"""S7 mass-axis fits, grouped internal validation, explicit set-valued inverses."""
import numpy as np,pandas as pd
from scipy.optimize import lsq_linear
from scipy.stats import f as fdist
from sklearn.isotonic import IsotonicRegression
from layer23_common import *
from inverse_calibration import inverse,set_ranges

MODELS=CFG['S7_models']
def fit_model(name,x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    if name=='affine':
        design=np.column_stack([np.ones(len(x)),x]);coef=np.linalg.lstsq(design,y,rcond=None)[0]
        knots=np.array([x.min(),x.max()]);values=coef[0]+coef[1]*knots
    elif name=='monotone_hinge_50':
        knot=CFG['S7_hinge_knot'];design=np.column_stack([np.ones(len(x)),np.minimum(x,knot),np.maximum(x-knot,0)])
        coef=lsq_linear(design,y,bounds=([-np.inf,0,0],[np.inf,np.inf,np.inf]),tol=1e-12).x
        knots=np.unique([x.min(),max(x.min(),min(x.max(),knot)),x.max()]);values=coef[0]+coef[1]*np.minimum(knots,knot)+coef[2]*np.maximum(knots-knot,0)
    elif name=='isotonic':
        model=IsotonicRegression(increasing=True,out_of_bounds='nan').fit(x,y);knots=model.X_thresholds_;values=model.y_thresholds_;coef=None
    else:raise ValueError(name)
    return dict(model=name,knots=knots.tolist(),values=values.tolist(),coefficients=None if coef is None else coef.tolist(),x_min=float(x.min()),x_max=float(x.max()),fraction_basis='AC_DNA_mass_fraction',fitting_unit='independent_transfection_well',qualification='EXPLORATORY_INTERNALLY_EVALUATED')
def predict(model,x):
    x=np.asarray(x,float);out=np.interp(x,model['knots'],model['values'],left=np.nan,right=np.nan)
    return out

def run():
    assert_upstream();rng=np.random.default_rng(CFG['seed'])
    r=pd.read_csv(ROOT/'results/ras_results.csv');s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv').sort_values(['condition_label','replicate_label']).copy()
    x=s.mass_fraction.to_numpy();y=s.ras.to_numpy();ids=s.acquisition_id.to_numpy();levels=np.unique(x)
    fitted={name:fit_model(name,x,y) for name in MODELS};validation=[];predictions=[];comparisons=[]
    for name,model in fitted.items():
        pred=predict(model,x)
        for row,p in zip(s.itertuples(),pred):predictions.append(dict(model=name,acquisition_id=row.acquisition_id,well_id=row.well_id,AC_mass_fraction=row.mass_fraction,observed_RAS=row.ras,fitted_RAS=p,residual=row.ras-p,split='in_sample_descriptive'))
        for scheme,groups in [('leave_one_well_out',ids),('leave_one_reference_level_out',levels)]:
            for group in groups:
                test=ids==group if scheme=='leave_one_well_out' else x==group;train=~test;fm=fit_model(name,x[train],y[train]);pr=predict(fm,x[test])
                for index,p in zip(np.flatnonzero(test),pr):
                    inv=inverse(fm,y[index]);validation.append(dict(model=name,validation=scheme,fold=str(group),test_well=ids[index],train_wells=';'.join(ids[train]),true_AC_mass_fraction=x[index],observed_RAS=y[index],predicted_RAS=p,RAS_error=p-y[index],recovered_AC_mass_fraction=inv['point'],inverse_low=inv['low'],inverse_high=inv['high'],inverse_status=inv['status'],mass_recovery_error=inv['point']-x[index] if inv['point'] is not None else None,forward_status='IN_TRAINING_INPUT_DOMAIN' if np.isfinite(p) else 'HELD_INPUT_OUTSIDE_TRAINING_RANGE',validation_level='internal_same_session_not_external_mixtures'))
        for scheme in ['in_sample_descriptive','leave_one_well_out','leave_one_reference_level_out']:
            z=pd.DataFrame(validation);z=z[(z.model==name)&(z.validation==scheme)] if scheme!='in_sample_descriptive' else None
            err=pred-y if z is None else z.RAS_error.dropna().to_numpy();inv_err=np.array([]) if z is None else z.mass_recovery_error.dropna().to_numpy()
            comparisons.append(dict(model=name,validation=scheme,well_n=20,RAS_prediction_n=len(err),RAS_RMSE=float(np.sqrt(np.mean(err**2))),RAS_MAE=float(np.mean(abs(err))),RAS_bias=float(np.mean(err)),inverse_recovery_n=len(inv_err),inverse_MAE_mass_fraction=float(np.mean(abs(inv_err))) if len(inv_err) else None,inverse_RMSE_mass_fraction=float(np.sqrt(np.mean(inv_err**2))) if len(inv_err) else None,inverse_bias_mass_fraction=float(np.mean(inv_err)) if len(inv_err) else None,qualified_RES=False))
    cv=pd.DataFrame(validation);table('results/calibration/S7_internal_validation.csv',cv)
    for row in comparisons:
        row['training_R2']=1-np.sum((y-predict(fitted[row['model']],x))**2)/np.sum((y-y.mean())**2)
        row['reference_basis_id']=CFG['reference_basis_id']
    table('results/calibration/S7_model_comparison.csv',comparisons);table('results/calibration/S7_calibration_predictions.csv',predictions)
    grid=np.linspace(0,1,CFG['S7_inverse_grid_points']);boots={n:[] for n in MODELS};coefs=[];bootstrap_draw_ids=[]
    draws=pd.read_csv(ROOT/'results/bootstrap_draws.csv');draws=draws[(draws.population_mode=='reporter')&draws.acquisition_id.isin(ids)]
    dm=draws.pivot(index='draw_id',columns='acquisition_id',values='event_control_ras')[ids].to_numpy()
    for b in range(CFG['S7_bootstrap_repeats']):
        indices=np.concatenate([rng.choice(np.flatnonzero(x==l),2,replace=True) for l in levels]);shared=int(rng.integers(len(dm)));bootstrap_draw_ids.append(shared);yy=dm[shared,indices]
        for name in MODELS:
            fm=fit_model(name,x[indices],yy);boots[name].append(fm)
            if fm['coefficients'] is not None:
                for j,v in enumerate(fm['coefficients']):coefs.append(dict(bootstrap_id=b,model=name,parameter_index=j,value=v))
    table('results/calibration/S7_parameter_bootstrap.csv',coefs)
    curves=[];inverse_grid=[];res=[];bands={}
    for name,model in fitted.items():
        mat=np.stack([predict(fm,grid) for fm in boots[name]]);low,high=np.quantile(mat,[.025,.975],axis=0);full=predict(model,grid)
        errors=cv[(cv.model==name)&(cv.validation=='leave_one_reference_level_out')].RAS_error.dropna().to_numpy()
        discrepancy=float(np.quantile(abs(errors),.95));bands[name]=(low-discrepancy,high+discrepancy)
        for a,p,l,h in zip(grid,full,low,high):curves.append(dict(model=name,AC_mass_fraction=a,predicted_RAS=p,bootstrap_mean_low=l,bootstrap_mean_high=h,diagnostic_prediction_low=l-discrepancy,diagnostic_prediction_high=h+discrepancy,internal_absolute_residual_q95=discrepancy,interval_status='BOOTSTRAP_MEAN_PLUS_INTERNAL_DISCREPANCY_NOT_VALIDATED_95PI'))
        ys=np.unique(np.r_[np.linspace(min(y)-.06,max(y)+.06,150),model['values']])
        for val in ys:
            inv=inverse(model,val);ranges,lo,hi=set_ranges(grid,(bands[name][0]<=val)&(bands[name][1]>=val))
            inverse_grid.append(dict(model=name,RAS=val,exact_inverse_low=inv['low'],exact_inverse_high=inv['high'],exact_inverse_point=inv['point'],exact_inverse_status=inv['status'],diagnostic_compatible_mass_low=lo,diagnostic_compatible_mass_high=hi,compatible_intervals=json.dumps(ranges),compatible_interval_n=len(ranges),compatible_width=None if lo is None else hi-lo,resolution_status='NO_COMPATIBLE_INPUT' if lo is None else 'BROAD_NONRESOLVED' if hi-lo>CFG['S7_resolution_width_diagnostic'] else 'NARROW_EXPLORATORY_ONLY',validated_RES=None))
        for i,row in enumerate(s.itertuples()):
            inv=inverse(model,row.ras);lows=[];highs=[]
            for b,fm in enumerate(boots[name]):
                # Event/control uncertainty is propagated separately from reference-well resampling.
                obs=float(dm[bootstrap_draw_ids[b],i]);ii=inverse(fm,obs)
                if ii['low'] is not None:lows.append(ii['low']);highs.append(ii['high'])
            margin=max(row.ras-row.event_control_ci_low,row.event_control_ci_high-row.ras)
            ranges,lo,hi=set_ranges(grid,(bands[name][0]-margin<=row.ras)&(bands[name][1]+margin>=row.ras))
            res.append(dict(acquisition_id=row.acquisition_id,well_id=row.well_id,model=name,known_AC_mass_fraction=row.mass_fraction,RAS=row.ras,RES_exploratory_mass_fraction=inv['point'],inverse_low=inv['low'],inverse_high=inv['high'],inverse_status=inv['status'],bootstrap_conditional_low=float(np.quantile(lows,.025)) if lows else None,bootstrap_conditional_high=float(np.quantile(highs,.975)) if highs else None,bootstrap_in_range_fraction=len(lows)/len(boots[name]),bootstrap_interval_status='CONDITIONAL_ON_ESTIMABLE_DRAW_NOT_UNCONDITIONAL_COVERAGE',diagnostic_compatible_mass_low=lo,diagnostic_compatible_mass_high=hi,diagnostic_compatible_intervals=json.dumps(ranges),RES_validated=None,RES_status='EXPLORATORY_WITHIN_S7_REFERENCE_ONLY' if inv['point'] is not None else inv['status'],cross_S10_transfer_qualified=False))
        model.update(version=VERSION,calibration_model_id=VERSION+'::'+name,reference_basis_id=CFG['reference_basis_id'],corrected_reference_sha256=sha(ROOT/'results/calibration/S7_reference_response_corrected.csv'),label_correction_sha256=sha(ROOT/'config/s7_label_correction.json'),upstream_RAS_sha256=CFG['upstream_ras_sha256'],internal_discrepancy_q95=discrepancy,bootstrap='stratified two wells per level with replacement plus shared-control event draws; n2 limitation',bootstrap_repeats=len(boots[name]),provenance=model_provenance())
    table('results/calibration/S7_calibration_curves.csv',curves);table('results/calibration/S7_inverse_identifiability.csv',inverse_grid);table('results/calibration/S7_RES_results.csv',res)
    jsonout('models/layer23/S7_calibration_models.json',fitted)
    # Explicitly retain adjacent reversals and compare them with within-level dispersion.
    adj=[];means=s.groupby('mass_fraction').ras.mean();sd=s.groupby('mass_fraction').ras.std()
    for a,b in zip(levels[:-1],levels[1:]):
        se=float(np.sqrt(sd[a]**2/2+sd[b]**2/2));adj.append(dict(from_AC_mass_fraction=a,to_AC_mass_fraction=b,delta_mean_RAS=means[b]-means[a],within_level_SE_difference=se,delta_divided_by_within_level_SE=(means[b]-means[a])/se,interpretation='descriptive_n2_not_batch_uncertainty'))
    table('results/calibration/S7_local_response_resolution.csv',adj)
    model=fitted['affine'];residual=y-predict(model,x);pure=sum(np.sum((y[x==l]-y[x==l].mean())**2) for l in levels);lack=max(0,float(np.sum(residual**2)-pure));Fstat=(lack/8)/(pure/10)
    # Inputs outside compatible population remain mappings only, never assigned RES.
    exploratory=[]
    for row in r[(r.series=='S10')&(r.population_mode=='reporter')].itertuples():
        for name,model in fitted.items():
            ii=inverse(model,row.ras);exploratory.append(dict(acquisition_id=row.acquisition_id,population_mode='reporter',model=name,RAS=row.ras,hypothetical_S7_mass_equivalent=ii['point'],inverse_status=ii['status'],transfer_status='UNQUALIFIED_S7_TO_S10_EXPLORATORY_MAPPING_ONLY',RES_validated=None))
    table('results/calibration/S10_hypothetical_S7_mapping.csv',exploratory)
    jsonout('results/calibration/S7_calibration_summary.json',dict(version=VERSION,models=list(fitted),mass_axis_verified=True,molar_axis_available=False,external_validation=False,affine_lack_of_fit_F=Fstat,affine_lack_of_fit_df=[8,10],affine_lack_of_fit_p=float(fdist.sf(Fstat,8,10)),affine_pure_error_SS=pure,model_comparison=comparisons,qualified_RES_n=0,interval_policy='Exploratory conditional bootstrap and empirical residual compatibility, not calibrated confidence coverage'))
    print('S7 fitted and internally evaluated',MODELS,flush=True)

if __name__=='__main__':run()
