"""Grouped prediction of a chromatogram index; never relabelled as RNA editing PER."""
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from layer23_common import *
from inverse_calibration import inverse
from biological_calibration import ols_fit,ols_predict,build_flow_molecular_pairs

def run():
    pairs,constant=build_flow_molecular_pairs()
    specs={'training_mean':[],'reporter_RAS':['RAS_reporter'],'B_detection_fraction':['blue_positive_fraction_reporters'],'editor_dose_log1p':['log1p_editor_ratio'],'reporter_RAS_plus_B':['RAS_reporter','blue_positive_fraction_reporters'],'coexpression_RAS':['RAS_editor_coexpression'],'positive_dose_training_mean':[],'positive_dose_B_fraction':['blue_positive_fraction_reporters']}
    models={};validation=[];summary=[];params=[]
    rng=np.random.default_rng(CFG['seed']+31)
    for name,features in specs.items():
        positive=name in ['coexpression_RAS','positive_dose_training_mean','positive_dose_B_fraction'];d=pairs[pairs.condition_label>0].copy() if positive else pairs.copy();d=d.dropna(subset=features+['raw_signal_index'])
        x=d[features].to_numpy(float);y=d.raw_signal_index.to_numpy();ids=d.well_id.to_numpy();doses=d.condition_label.to_numpy();full=ols_fit(x,y)
        models[name]=dict(**full,features=features,endpoint='raw_direction_averaged_C280_chromatogram_index',qualification='EXPLORATORY_ASSOCIATION_NOT_PER',training_wells=list(ids),upstream_RAS_sha256=CFG['upstream_ras_sha256'],version=VERSION,provenance=model_provenance(molecular=True))
        for bi in range(CFG['prediction_bootstrap_repeats']):
            ix=np.concatenate([rng.choice(np.flatnonzero(doses==a),sum(doses==a),replace=True) for a in np.unique(doses)])
            if np.linalg.matrix_rank(np.column_stack([np.ones(len(ix)),x[ix]]))<x.shape[1]+1:continue
            fit=ols_fit(x[ix],y[ix]);params.extend(dict(model=name,bootstrap_id=bi,parameter='intercept' if j==0 else features[j-1],value=v) for j,v in enumerate(fit['coefficients']))
        for scheme,groups in [('leave_one_well_out',ids),('leave_one_dose_out',np.unique(doses))]:
            for group in groups:
                test=ids==group if scheme=='leave_one_well_out' else doses==group;train=~test;fitted=ols_fit(x[train],y[train]);pred,low,high=ols_predict(fitted,x[test]);outside=np.any((x[test]<x[train].min(axis=0))|(x[test]>x[train].max(axis=0)),axis=1) if features else np.zeros(sum(test),bool)
                for i,p,l,h,o in zip(np.flatnonzero(test),pred,low,high,outside):
                    validation.append(dict(model=name,validation=scheme,fold=str(group),test_well=ids[i],test_dose=doses[i],train_wells=';'.join(ids[train]),train_well_n=int(train.sum()),observed_signal=y[i],predicted_signal=p,error=p-y[i],prediction_low=l,prediction_high=h,interval_covers=bool(l<=y[i]<=h),outside_training_predictor_range=bool(o),endpoint='RAW_CHROMATOGRAM_INDEX_NOT_RNA_EDITING_FRACTION',interval_status='OLS_T_PREDICTION_INTERVAL_MODEL_ASSUMPTIONS_NOT_ASSAY_ACCURACY',PER=None,PER_status='NOT_QUALIFIED'))
        v=pd.DataFrame(validation)
        for scheme in ['leave_one_well_out','leave_one_dose_out']:
            z=v[(v.model==name)&(v.validation==scheme)];e=z.error.to_numpy();boot=[]
            # Descriptive uncertainty of the fixed held-out errors; not a new independent validation.
            for bi in range(1000):
                ix=rng.integers(0,len(e),len(e));boot.append([np.mean(abs(e[ix])),np.sqrt(np.mean(e[ix]**2))])
            ci=np.quantile(boot,[.025,.975],axis=0)
            summary.append(dict(model=name,features=';'.join(features),validation=scheme,well_n=len(z),endpoint='RAW_C280_CHROMATOGRAM_COMPOSITION_INDEX',MAE=np.mean(abs(e)),RMSE=np.sqrt(np.mean(e**2)),bias=e.mean(),MAE_descriptive_low=ci[0,0],MAE_descriptive_high=ci[1,0],RMSE_descriptive_low=ci[0,1],RMSE_descriptive_high=ci[1,1],prediction_interval_coverage=z.interval_covers.mean(),outside_predictor_range_n=z.outside_training_predictor_range.sum(),qualification='EXPLORATORY_INTERNAL_VALIDATION_NOT_PER'))
    table('results/prediction/S10_prediction_validation.csv',validation);table('results/prediction/S10_direct_model_results.csv',summary);table('results/prediction/S10_model_parameter_bootstrap.csv',params);jsonout('models/layer23/S10_exploratory_signal_models.json',models)
    association=[]
    for scale in ['well','dose_mean']:
        d=pairs if scale=='well' else pairs.groupby('condition_label').mean(numeric_only=True).reset_index()
        for predictor in ['editor_dna_ng','blue_positive_fraction_reporters','RAS_reporter','RAS_editor_coexpression','median_B_raw','mean_R_corrected']:
            for endpoint in ['raw_signal_index','F_raw_mean','R_raw_mean']:
                z=d[[predictor,endpoint]].dropna()
                association.append(dict(unit=scale,predictor=predictor,endpoint=endpoint,n=len(z),pearson=z[predictor].corr(z[endpoint]),spearman=spearmanr(z[predictor],z[endpoint]).statistic,interpretation='DESCRIPTIVE_ASSOCIATION_NO_CAUSAL_OR_MOLECULAR_FRACTION_CLAIM'))
    table('results/prediction/S10_flow_molecular_associations.csv',association)
    # No biological staged fit is permitted. A separate algebraic sensitivity checks the affine-information claim.
    cal=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text())['affine'];mapped=np.array([inverse(cal,v)['point'] for v in pairs.RAS_reporter],float)
    algebra=[];v=pd.DataFrame(validation)
    if np.isfinite(mapped).all():
        for row in v[v.model=='reporter_RAS'].itertuples():
            train=pairs.well_id.isin(row.train_wells.split(';')).to_numpy();test=pairs.well_id==row.test_well
            fit=ols_fit(mapped[train,None],pairs.raw_signal_index.to_numpy()[train]);pred,_,_=ols_predict(fit,mapped[test,None])
            algebra.append(dict(validation=row.validation,test_well=row.test_well,direct_prediction=row.predicted_signal,hypothetical_affine_staged_prediction=float(pred[0]),difference=float(pred[0]-row.predicted_signal),status='MATHEMATICAL_SENSITIVITY_ONLY_TRANSFER_UNQUALIFIED'))
    table('results/prediction/S10_affine_transform_sensitivity.csv',algebra)
    table('results/prediction/S10_staged_model_results.csv',[dict(model='RAS_to_S7_RES_to_RNA_fraction',status='UNAVAILABLE',fitted=False,PER=None,reasons='No calibrated molecular editing fractions; S7/S10 reference and population transfer unqualified; no supported RES domain validated',mathematical_sensitivity='Affine transform only evaluated separately; no added sample information',maximum_affine_prediction_difference=max(abs(r['difference']) for r in algebra) if algebra else None)])
    jsonout('results/prediction/S10_prediction_summary.json',dict(version=VERSION,independent_wells=12,primary_signal_index='equal directions within complete molecular labels; equal labels within well; not editing percentage',raw_signal_offset=constant,PER_available=False,staged_biological_fit=False,direct_relative_signal_fit=True,validation_schemes=['leave_one_well_out','leave_one_dose_out'],models=summary,maximum_affine_transform_difference=max(abs(r['difference']) for r in algebra) if algebra else None))
    print('S10 grouped exploratory signal models fitted; PER unavailable',flush=True)

if __name__=='__main__':run()
