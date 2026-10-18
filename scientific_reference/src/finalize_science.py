"""Derive the final contracts and new diagnostics from verified v4 observations.
Run once to freeze; normal application use loads artifacts. Never edits v4 source tables.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from science_api import *
from reporter_calibration import fit_model,predict
from inverse_calibration import inverse,set_ranges
from biological_calibration import ols_fit,ols_predict

def csv(path,rows):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    (rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)).to_csv(p,index=False,float_format='%.17g')

def layer01():
    manifest=load_experiment();ctx=build_context();old=json.loads((ROOT/'contexts/context.json').read_text())
    for k in ctx['gate_parameters']:
        np.testing.assert_allclose(ctx['gate_parameters'][k],old[k],rtol=1e-12,atol=1e-12) if k!='training_control' else None
    save_json(ROOT/'models/context_profiles/context_v1.json',ctx)
    original=pd.read_csv(ROOT/'results/ras_results.csv');rasrows=[];qc=[];optical=[];influence=[];threshold=[];profiles=[]
    outputs=[];mask_count=0
    for row in manifest.itertuples():
        md=row._asdict();md['linked_editor_present']=row.series=='S10' and row.sample_role!='Mock' and row.condition_label>0
        pr=process_fcs(ROOT/row.file_path,ctx,md);q={**md,**pr['qc']}
        qc.append({k:q[k] for k in ['acquisition_id','series','condition_label','sample_role',*pr['qc'].keys()]})
        optical.extend({'acquisition_id':row.acquisition_id,**o} for o in pr['optical'])
        masks=np.load(ROOT/'masks'/f'{row.acquisition_id}.npz')
        for k in masks.files: np.testing.assert_array_equal(masks[k],pr['masks'][k]);mask_count+=1
        if row.sample_role=='Mock':continue
        sample={'sample_id':row.acquisition_id,'well_id':row.well_id,'series':row.series,'condition_label':row.condition_label,
          'original_source_condition_label':row.source_condition_label,'qc':pr['qc'],'input_sha256':row.sha256,'RAS':[]}
        for mode in ['reporter']+(['blue_positive_reporter','blue_negative_reporter'] if row.series=='S10' else []):
            o=original[(original.acquisition_id==row.acquisition_id)&(original.population_mode==mode)].iloc[0]
            uncertainty={k:o[k] for k in ['event_ci_low','event_ci_high','event_control_ci_low','event_control_ci_high','bootstrap_denominator_failure_fraction']}
            result=calculate_ras(pr,mode,uncertainty=uncertainty)
            if result['score_status']!='NOT_APPLICABLE_NO_LINKED_EDITOR':
                for k in ['ras','sum_G_corrected','sum_R_corrected','n_selected','effective_red_events']:
                    if result.get(k) is not None:np.testing.assert_allclose(result[k],o[k],rtol=1e-12,atol=1e-12)
            sample['RAS'].append(result)
            rasrows.append({**{k:v for k,v in result.items() if k!='uncertainty'},**uncertainty,
              'series':row.series,'original_condition_label':row.source_condition_label,'condition_label':row.condition_label})
        outputs.append(sample)
        x=pr['array'];c=ctx['gate_parameters'];sel=pr['masks']['reporter'];v=x[sel];r=v[:,R]-c['background'][R];g=v[:,G]-c['background'][G];base=score(g,r,ctx['config'])['ras']
        bad=(v[:,G]>=pr['optical'][0]['declared_PnR'])|(v[:,R]>=pr['optical'][1]['declared_PnR'])
        reduced=score(g[~bad],r[~bad],ctx['config'])['ras']
        influence.append(dict(acquisition_id=row.acquisition_id,range_flagged_reporter_events=int(bad.sum()),RAS=base,RAS_excluding_range_flagged=reduced,
          relative_change=None if reduced is None else reduced/base-1,policy='sensitivity_only_no_primary_event_removal'))
        for factor in [.8,1,1.2,1.5]:
            raw_boundary=c['background'][R]+factor*(c['red_quantitative_boundary']-c['background'][R]);sm=pr['masks']['singlet']&(x[:,R]>raw_boundary)
            z=score(x[sm,G]-c['background'][G],x[sm,R]-c['background'][R],ctx['config'])
            threshold.append(dict(acquisition_id=row.acquisition_id,threshold_excess_factor=factor,raw_red_threshold=raw_boundary,n_selected=z['n_selected'],RAS=z['ras'],relative_change=z['ras']/base-1 if z['ras'] is not None else None,interpretation='diagnostic_only_primary_boundary_unchanged'))
        bins=pd.read_csv(ROOT/'results/red_profiles.csv');bins=bins[bins.acquisition_id==row.acquisition_id].sort_values('bin').dropna(subset=['ras'])
        profiles.append(dict(acquisition_id=row.acquisition_id,series=row.series,corrected_condition=row.condition_label,
          reporter_fraction=float(sel.sum()/pr['masks']['singlet'].sum()),red_q10=float(np.quantile(r,.1)),red_median=float(np.median(r)),red_q90=float(np.quantile(r,.9)),
          effective_red_events=base and score(g,r,ctx['config'])['effective_red_events'],selected_events=len(r),red_weighted_support_fraction=score(g,r,ctx['config'])['effective_red_events']/len(r),
          red_bin_n=len(bins),lowest_bin_RAS=float(bins.ras.iloc[0]),highest_bin_RAS=float(bins.ras.iloc[-1]),
          high_minus_low_bin_RAS=float(bins.ras.iloc[-1]-bins.ras.iloc[0]),bin_spearman=float(spearmanr(bins.center,bins.ras).statistic),
          interpretation='within_sample_expression_dependence_not_causal_or_independent_cell_replicates'))
    csv('results/layer0/Sample_QC.csv',qc);csv('results/layer0/Detector_Range_Audit.csv',optical);csv('results/layer0/Range_Exclusion_Sensitivity.csv',influence)
    csv('results/layer1/RAS_Results.csv',rasrows);csv('results/layer1/Red_Threshold_Sensitivity.csv',threshold);csv('results/layer1/Reporter_Expression_Dependence.csv',profiles)
    # Recompute matched well CV from preserved values with the current labels joined by acquisition ID.
    z=original[original.population_mode=='reporter'].drop(columns=['condition_label']).merge(manifest[['acquisition_id','condition_label']],on='acquisition_id',validate='one_to_one')
    rows=[]
    for (series,cond),d in z.groupby(['series','condition_label']):
        cv=lambda a:float(a.std(ddof=1)/abs(a.mean())*100)
        raw=cv(d.mean_G_raw);norm=cv(d.ras)
        rows.append(dict(series=series,condition_label=cond,well_n=len(d),well_ids=';'.join(d.well_id),raw_EGFP_CV_percent=raw,RAS_CV_percent=norm,
          reduction_percentage_points=raw-norm,improved=norm<raw,definition='sample_SD_ddof1/abs_mean*100; same reporter events'))
    csv('results/layer1/Normalization_Repeatability.csv',rows)
    summary=pd.DataFrame(rows).groupby('series').agg(conditions=('well_n','size'),raw_CV_median=('raw_EGFP_CV_percent','median'),RAS_CV_median=('RAS_CV_percent','median'),improved_conditions=('improved','sum')).reset_index()
    csv('results/layer1/Normalization_Summary.csv',summary)
    save_json(ROOT/'results/integrated/sample_measurements_base.json',outputs)
    save_json(ROOT/'results/layer0/raw_flow_regression.json',{'status':'PASS','context_rebuilt_from_controls':True,'event_masks_equal':mask_count,'RAS_rows_compared':54,'no_editor_blue_tail_rows_reclassified_not_removed_from_legacy':2})
    print('Layer 0/1: raw gates, sums, RAS and QC verified',flush=True)

def bootstrap_release_bundle(s):
    """Exactly replay v4 well resampling and shared observation draw IDs; freeze all artifacts."""
    rng=np.random.default_rng(FINAL['seed']);ids=s.acquisition_id.to_numpy();x=s.mass_fraction.to_numpy()
    draws=pd.read_csv(ROOT/'results/bootstrap_draws.csv');draws=draws[(draws.population_mode=='reporter')&draws.acquisition_id.isin(ids)]
    dm=draws.pivot(index='draw_id',columns='acquisition_id',values='event_control_ras')[ids].to_numpy()
    coefficients=[];obs={k:[] for k in ids};drawids=[]
    for b in range(1000):
        ii=np.concatenate([rng.choice(np.flatnonzero(x==a),2,replace=True) for a in np.unique(x)])
        shared=int(rng.integers(len(dm)));drawids.append(shared)
        fm=fit_model('monotone_hinge_50',x[ii],dm[shared,ii]);coefficients.append(fm['coefficients'])
        for i,k in enumerate(ids):obs[k].append(float(dm[shared,i]))
    v4=pd.read_csv(ROOT/'results/calibration/S7_parameter_bootstrap.csv');v4=v4[v4.model=='monotone_hinge_50'].pivot(index='bootstrap_id',columns='parameter_index',values='value').to_numpy()
    np.testing.assert_allclose(coefficients,v4,rtol=1e-12,atol=1e-12)
    curves=pd.read_csv(ROOT/'results/calibration/S7_calibration_curves.csv');h=curves[curves.model=='monotone_hinge_50'];iso=curves[curves.model=='isotonic']
    return dict(version=RELEASE,grid=h.AC_mass_fraction.tolist(),primary_lower=h.diagnostic_prediction_low.tolist(),primary_upper=h.diagnostic_prediction_high.tolist(),
      isotonic_lower=iso.diagnostic_prediction_low.tolist(),isotonic_upper=iso.diagnostic_prediction_high.tolist(),
      hinge_coefficients=coefficients,sample_observation_draws=obs,sample_RAS=dict(zip(ids,s.ras)),shared_control_draw_ids=drawids,
      procedure='1000 stratified well-resamples (2/level), one shared paired event/control draw ID across all samples per replicate; coefficient and observation uncertainties coupled',
      limitations=['n2 cannot estimate between-day variance','conditional successful-inverse quantiles are not unconditional coverage','in-sample training wells reused; CV evaluated separately'])

def inverse_validation(s):
    names=['affine','isotonic','monotone_hinge_50'];x=s.mass_fraction.to_numpy();y=s.ras.to_numpy();ids=s.acquisition_id.to_numpy()
    draws=pd.read_csv(ROOT/'results/bootstrap_draws.csv');draws=draws[(draws.population_mode=='reporter')&draws.acquisition_id.isin(ids)]
    dm=draws.pivot(index='draw_id',columns='acquisition_id',values='event_control_ras')[ids].to_numpy()
    rng=np.random.default_rng(FINAL['seed']+507);rows=[]
    for scheme,groups in [('leave_one_well_out',ids),('leave_one_reference_level_out',np.unique(x))]:
        for group in groups:
            test=ids==group if scheme=='leave_one_well_out' else x==group;ti=np.flatnonzero(test);tr=np.flatnonzero(~test)
            grid=np.linspace(x[tr].min(),x[tr].max(),1001)
            models={n:fit_model(n,x[tr],y[tr]) for n in names};curves={n:[] for n in names};boot={n:{i:[] for i in ti} for n in names}
            discrepancy={}
            # Inner grouped forward residuals use training levels only; outer held-out outcome never sets interval width.
            for name in names:
                errors=[]
                for a in np.unique(x[tr]):
                    use=tr[x[tr]!=a];held=tr[x[tr]==a]
                    fm=fit_model(name,x[use],y[use]);pr=predict(fm,x[held]);errors.extend((pr-y[held])[np.isfinite(pr)])
                discrepancy[name]=float(np.quantile(abs(np.array(errors)),.95))
            for b in range(FINAL['cv_bootstrap_repeats']):
                ii=np.concatenate([rng.choice(tr[x[tr]==a],sum(x[tr]==a),replace=True) for a in np.unique(x[tr])]);shared=int(rng.integers(len(dm)))
                for name in names:
                    fm=fit_model(name,x[ii],dm[shared,ii]);curves[name].append(predict(fm,grid))
                    for i in ti:
                        z=inverse(fm,float(dm[shared,i]))
                        if z['low'] is not None:boot[name][i].append([z['low'],z['high']])
            for name,fm in models.items():
                low,high=np.quantile(curves[name],[.025,.975],axis=0);low-=discrepancy[name];high+=discrepancy[name]
                for i in ti:
                    inv=inverse(fm,y[i]);p=float(predict(fm,[x[i]])[0]);bt=boot[name][i]
                    bl,bh=(float(np.quantile(np.array(bt)[:,0],.025)),float(np.quantile(np.array(bt)[:,1],.975))) if bt else (None,None)
                    margin=max(y[i]-s.iloc[i].event_control_ci_low,s.iloc[i].event_control_ci_high-y[i])
                    ranges,lo,hi=set_ranges(grid,(low-margin<=y[i])&(high+margin>=y[i]))
                    rows.append(dict(model=name,validation=scheme,fold=str(group),test_well=ids[i],train_wells=';'.join(ids[tr]),train_well_n=len(tr),true_AC_mass_fraction=x[i],observed_RAS=y[i],
                      training_AC_low=x[tr].min(),training_AC_high=x[tr].max(),held_input_within_training_domain=bool(x[tr].min()<=x[i]<=x[tr].max()),
                      predicted_RAS=p,RAS_error=p-y[i],recovered_AC_mass_fraction=inv['point'],inverse_status=inv['status'],
                      inverse_error_pp=None if inv['point'] is None else 100*(inv['point']-x[i]),
                      conditional_bootstrap_low=bl,conditional_bootstrap_high=bh,bootstrap_success_n=len(bt),bootstrap_total_n=FINAL['cv_bootstrap_repeats'],
                      conditional_interval_covers=None if bl is None else bool(bl<=x[i]<=bh),
                      compatibility_low=lo,compatibility_high=hi,compatibility_intervals=json.dumps(ranges),compatibility_nonempty=lo is not None,
                      compatibility_covers=any(l-1e-12<=x[i]<=h+1e-12 for l,h in ranges),nested_training_residual_q95=discrepancy[name],
                      interval_status='OUTER_HELD_OUT_EVALUATION_OF_NONNOMINAL_COMPATIBILITY_SET; BOOTSTRAP_CONDITIONAL_ON_SUCCESS',
                      external_validation=False))
    v=pd.DataFrame(rows);csv('results/layer2/RES_Inverse_Validation.csv',v)
    old=pd.read_csv(ROOT/'results/calibration/S7_internal_validation.csv')
    for key,col in [('RAS_error','RAS_error'),('recovered_AC_mass_fraction','recovered_AC_mass_fraction')]:
        merged=v.merge(old,on=['model','validation','test_well'],suffixes=('_new','_v4'),validate='one_to_one')
        np.testing.assert_allclose(merged[col+'_new'],merged[col+'_v4'],rtol=1e-12,atol=1e-12,equal_nan=True)
    summaries=[]
    for (name,scheme),d in v.groupby(['model','validation']):
        common=set(v[(v.validation==scheme)&v.recovered_AC_mass_fraction.notna()].groupby('test_well').filter(lambda a:len(a)==3).test_well)
        for subset,z in [('all_held_out',d),('held_input_in_training_domain',d[d.held_input_within_training_domain]),('matched_unique_all_three_models',d[d.test_well.isin(common)])]:
            e=z.inverse_error_pp.dropna();fe=z.RAS_error.dropna();unique=len(e);n=len(z)
            summaries.append(dict(model=name,validation=scheme,subset=subset,total_held_out=n,unique_inverse_n=unique,unique_fraction=unique/n if n else None,
              out_of_range_n=int(z.inverse_status.eq('OUT_OF_CALIBRATION_RANGE').sum()),non_identifiable_n=int(z.inverse_status.eq('NON_IDENTIFIABLE_PLATEAU').sum()),
              inverse_MAE_pp=float(abs(e).mean()),inverse_RMSE_pp=float(np.sqrt(np.mean(e**2))),inverse_bias_pp=float(e.mean()),
              point_error_denominator=unique,full_set_point_MAE=None if unique<n else float(abs(e).mean()),failure_policy='undefined errors not replaced with zero; successes and failures jointly reported',
              forward_prediction_n=len(fe),forward_RMSE_RAS=float(np.sqrt(np.mean(fe**2))),forward_MAE_RAS=float(abs(fe).mean()),
              compatible_set_coverage_all=float(z.compatibility_covers.mean()),compatible_set_n=int(z.compatibility_nonempty.sum()),
              conditional_bootstrap_coverage_given_interval=float(z.conditional_interval_covers.dropna().astype(float).mean()),
              conditional_interval_n=int(z.conditional_interval_covers.notna().sum()),coverage_status='EMPIRICAL_INTERNAL_NOT_NOMINAL_95_PERCENT_VALIDATION'))
    csv('results/layer2/RES_Model_Comparison.csv',summaries)
    bylevel=[]
    for keys,d in v.groupby(['model','validation','true_AC_mass_fraction']):
        e=d.inverse_error_pp.dropna()
        bylevel.append(dict(model=keys[0],validation=keys[1],AC_mass_fraction=keys[2],well_n=len(d),unique_n=len(e),MAE_pp=abs(e).mean(),RMSE_pp=np.sqrt(np.mean(e**2)),bias_pp=e.mean(),compatibility_coverage=d.compatibility_covers.mean()))
    csv('results/layer2/RES_Inverse_Per_Level.csv',bylevel)
    print('RES full-denominator and nested uncertainty validation complete',flush=True)

def freeze_res():
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv').sort_values(['condition_label','replicate_label']).reset_index(drop=True)
    old=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text())
    bundle=bootstrap_release_bundle(s);save_json(ROOT/'models/res_primary/uncertainty.json',bundle)
    inverse_validation(s)
    h=old['monotone_hinge_50'];refit=fit_model('monotone_hinge_50',s.mass_fraction,s.ras)
    np.testing.assert_allclose(h['coefficients'],refit['coefficients'],rtol=1e-12,atol=1e-12)
    domainrows=[];grid=np.asarray(bundle['grid']);lo=np.asarray(bundle['primary_lower']);hi=np.asarray(bundle['primary_upper']);ilo=np.asarray(bundle['isotonic_lower']);ihi=np.asarray(bundle['isotonic_upper'])
    response_grid=np.arange(np.floor(h['values'][0]*2000),np.ceil(h['values'][-1]*2000)+1)/2000
    for y in response_grid:
        _,hl,hh=set_ranges(grid,(lo<=y)&(hi>=y));_,il,ih=set_ranges(grid,(ilo<=y)&(ihi>=y));inv=inverse(h,y);ii=inverse(old['isotonic'],y)
        good=all(v is not None for v in [hl,hh,il,ih,inv['point'],ii['point']])
        width=max(hh,ih)-min(hl,il) if good else None
        passed=good and min(hl,il)>0 and max(hh,ih)<1 and width<=FINAL['compatibility_width_limit']
        domainrows.append(dict(RAS=y,hinge_point=inv['point'],isotonic_point=ii['point'],union_low=min(hl,il) if good else None,union_high=max(hh,ih) if good else None,union_width=width,passes_internal_screen=passed))
    dg=pd.DataFrame(domainrows);ranges,_,_=set_ranges(response_grid,dg.passes_internal_screen.to_numpy());largest=max(ranges,key=lambda q:q[1]-q[0]) if ranges else None
    domain=dict(numerical={'AC_mass_fraction':[0,1],'RAS_response':h['values'][::2]},observed={'reference_levels':sorted(s.mass_fraction.unique()),'observed_RAS_range':[s.ras.min(),s.ras.max()],
      'independent_wells':20,'wells_per_level':2,'not_continuous_observation':True},
      internal_screen={'RAS_largest_contiguous':largest,'hinge_mass_equivalent':[inverse(h,v)['point'] for v in largest] if largest else None,
        'all_grid_pass_ranges':ranges,'policy':FINAL['res_region_policy'],'max_total_width':.20,'RAS_grid_step':.0005,'mass_grid_step':.001,
        'measurement_uncertainty':'per-sample RAS margin added afterwards; may narrow eligibility','qualification':'ENGINEERING_EXPLORATORY_COMPATIBILITY_SCREEN_NOT_VALIDATED_ACCURACY_RANGE',
        'observed_reference_levels_inside':[float(v) for v in sorted(s.mass_fraction.unique()) if largest and largest[0]<=float(predict(h,[v])[0])<=largest[1]]},
      transfer={'supported':'same S7 reference experiment, reporter population','external_supported':False,'S10_qualified':False,'routine_quantitative_qualified':False})
    save_json(ROOT/'results/layer2/RES_Calibration_Domain.json',domain);csv('results/layer2/RES_Domain_Screen.csv',dg)
    cv=pd.read_csv(ROOT/'results/layer2/RES_Model_Comparison.csv')
    deps=['src/core.py','src/science_api.py','config/analysis.json','config/science_final.json','config/s7_label_correction.json','results/ras_results.csv',
      'results/calibration/S7_reference_response_corrected.csv','models/res_primary/uncertainty.json']
    model={**h,'model_id':FINAL['model_id'],'calibration_model_id':FINAL['model_id'],
      'source_calibration_model_id':h['calibration_model_id'],'version':RELEASE,'ras_estimator_id':ESTIMATOR,'kernel_sha256':digest(ROOT/'src/core.py'),
      'context_id':FINAL['context_id'],'context_profile_sha256':digest(ROOT/'models/context_profiles/context_v1.json'),'calibration_domain_id':FINAL['calibration_domain_id'],
      'model_family':'continuous_monotone_hinge_fixed_knot','mathematical_definition':'g(A)=alpha+beta*A+gamma*max(0,A-0.5)',
      'parameters':{'alpha':h['coefficients'][0],'beta':h['coefficients'][1],'gamma':h['coefficients'][2]-h['coefficients'][1],'k':.5,'lower_slope':h['coefficients'][1],'upper_slope':h['coefficients'][2]},
      'knot_policy':'fixed at 0.5 in v3/v4; not searched in this release','constraints':'lower_slope>=0; upper_slope>=0; intercept unconstrained',
      'fitting_method':'bounded least squares with equal weight per independent well; 20 wells, 10 levels',
      'input_unit':'AC_DNA_mass_fraction_0_to_1','output_unit':'RAS_dimensionless_detector_channel_ratio','population_mode':'reporter',
      'training_sample_ids':s.acquisition_id.tolist(),'domains':domain,
      'inverse_policy':'unique piecewise-linear inverse; plateau=>identified interval; outside=>null, never clip/extrapolate',
      'uncertainty_artifact':'models/res_primary/uncertainty.json','validation':clean(cv[cv.model=='monotone_hinge_50'].to_dict('records')),
      'output_policy':{'research':'emit compatible numeric point with conditional interval and compatibility set','routine':'no qualified result for this release','incompatible':'ordinary RES null; separately labeled hypothetical mapping allowed'},
      'known_limits':['retrospective label correction not independently verified','n2/level one experimental series','local empirical 90-100% response flattening not represented by positive fitted upper slope','no external calibration or S10 transfer','not RNA editing fraction'],
      'source_hashes':{p:digest(ROOT/p) for p in deps}}
    save_json(ROOT/'models/res_primary/model.json',model)
    for name in ['affine','isotonic']:save_json(ROOT/'models/res_alternative'/f'{name}.json',{**old[name],'benchmark_only':True,'release_id':RELEASE})
    rows=[];samples=json.loads((ROOT/'results/integrated/sample_measurements_base.json').read_text())
    for sample in samples:
        r=next(x for x in sample['RAS'] if x['population_mode']=='reporter');sid=sample['sample_id'];u=r['uncertainty']
        z=calculate_res(r['ras'],context_id=FINAL['context_id'],population_mode='reporter',calibration_domain_id=FINAL['calibration_domain_id'] if sample['series']=='S7' else 'S10_NO_QUALIFIED_TRANSFER',
          sample_id=sid,ras_interval=[u['event_control_ci_low'],u['event_control_ci_high']],model=model,uncertainty_bundle=bundle)
        sample['RES']=z;sample['PER']=predict_per(z);sample['release_id']=RELEASE
        if sample['series']=='S7':
            row={k:(json.dumps(v) if isinstance(v,(list,dict)) else v) for k,v in z.items()};row['known_AC_mass_fraction']=sample['condition_label']/100;rows.append(row)
    csv('results/layer2/RES_Sample_Results.csv',rows)
    csv('results/layer2/S10_Transfer_Restricted_Results.csv',[{k:v for k,v in s['RES'].items() if not isinstance(v,(dict,list))} for s in samples if s['series']=='S10'])
    generate_measurement_report(ROOT/'results/integrated/SONAR_Sample_Reports.json',samples)
    print('Primary RES frozen; 20 S7 and 12 transfer-restricted S10 results emitted',flush=True)

def layer3():
    p=pd.read_csv(ROOT/'results/prediction/S10_flow_molecular_pairs.csv').sort_values(['condition_label','well_id']).reset_index(drop=True)
    p['editor_ratio']=p.condition_label
    specs={'training_mean':[],'reporter_RAS':['RAS_reporter'],'B_detection_fraction':['blue_positive_fraction_reporters'],
      'editor_dose_log1p':['log1p_editor_ratio'],'reporter_RAS_plus_B':['RAS_reporter','blue_positive_fraction_reporters'],
      'editor_dose_linear':['editor_ratio'],'editor_dose_linear_plus_B':['editor_ratio','blue_positive_fraction_reporters']}
    records=[];models={}
    for name,features in specs.items():
        x=p[features].to_numpy(float);y=p.raw_signal_index.to_numpy();dose=p.condition_label.to_numpy();ids=p.well_id.to_numpy()
        models[name]={**ols_fit(x,y),'features':features,'endpoint':'RAW_C280_CHROMATOGRAM_COMPOSITION_INDEX','absolute_fraction_qualified':False,'training_wells':ids.tolist(),'version':RELEASE}
        for scheme,groups in [('leave_one_well_out',ids),('leave_one_dose_out',np.unique(dose))]:
            for group in groups:
                test=ids==group if scheme=='leave_one_well_out' else dose==group;train=~test;fm=ols_fit(x[train],y[train]);pred,lo,hi=ols_predict(fm,x[test])
                outside=np.any((x[test]<x[train].min(axis=0))|(x[test]>x[train].max(axis=0)),axis=1) if features else np.zeros(test.sum(),bool)
                for i,pr,l,h,o in zip(np.flatnonzero(test),pred,lo,hi,outside):
                    records.append(dict(model=name,validation=scheme,test_well=ids[i],dose=dose[i],train_wells=';'.join(ids[train]),observed=y[i],predicted=pr,error=pr-y[i],prediction_low=l,prediction_high=h,covered=l<=y[i]<=h,
                      outside_training_predictor_range=o,extrapolation_rule='outside any marginal feature range; does not establish multivariate convex-hull support',PER=None,endpoint='RELATIVE_RAW_CHROMATOGRAM_INDEX_NOT_RNA_FRACTION'))
    d=pd.DataFrame(records);csv('results/layer3/Molecular_Prediction_Validation.csv',d)
    old=pd.read_csv(ROOT/'results/prediction/S10_prediction_validation.csv');merged=d.merge(old,on=['model','validation','test_well'],validate='one_to_one')
    np.testing.assert_allclose(merged.predicted,merged.predicted_signal,rtol=1e-12,atol=1e-12)
    rng=np.random.default_rng(FINAL['seed']+308);rows=[]
    for (name,scheme),z in d.groupby(['model','validation']):
        e=z.error.to_numpy();groups=sorted(z.dose.unique());b=[]
        for i in range(2000):
            sample=pd.concat([z[z.dose==g] for g in rng.choice(groups,len(groups),replace=True)]);ee=sample.error.to_numpy();b.append([np.mean(abs(ee)),np.sqrt(np.mean(ee**2))])
        lo,hi=np.quantile(b,[.025,.975],axis=0)
        rows.append(dict(model=name,validation=scheme,well_n=len(z),dose_condition_n=z.dose.nunique(),MAE=np.mean(abs(e)),RMSE=np.sqrt(np.mean(e**2)),bias=e.mean(),
          MAE_cluster_resample_low=lo[0],MAE_cluster_resample_high=hi[0],RMSE_cluster_resample_low=lo[1],RMSE_cluster_resample_high=hi[1],
          uncertainty='resampling six dose clusters of fixed held-out errors; descriptive, not independent retraining validation',
          OLS_t_interval_empirical_coverage=z.covered.mean(),outside_predictor_range_n=z.outside_training_predictor_range.sum(),endpoint='RAW_C280_RELATIVE_CHROMATOGRAM_INDEX',PER_qualified=False))
    csv('results/layer3/Molecular_Prediction_Comparison.csv',rows)
    dif=[]
    for dose,z in p.groupby('condition_label'):
        a=z[z.replicate_label=='A'].iloc[0];b=z[z.replicate_label=='B'].iloc[0]
        dif.append(dict(dose=dose,B_fraction_A_minus_B=a.blue_positive_fraction_reporters-b.blue_positive_fraction_reporters,index_A_minus_B=a.raw_signal_index-b.raw_signal_index,RAS_A_minus_B=a.RAS_reporter-b.RAS_reporter))
    dif=pd.DataFrame(dif);csv('results/layer3/Within_Dose_Well_Differences.csv',dif)
    x=dif.B_fraction_A_minus_B.to_numpy();y=dif.index_A_minus_B.to_numpy();slope=float(x@y/(x@x))
    save_json(ROOT/'results/layer3/Dose_Confounding_Assessment.json',dict(B_fraction_vs_linear_dose_pearson=p.blue_positive_fraction_reporters.corr(p.editor_ratio),
      within_dose_difference_pairs=len(dif),within_dose_difference_pearson=float(np.corrcoef(x,y)[0,1]),within_dose_difference_slope_through_origin=slope,
      interpretation='six A/B difference pairs remove dose mean; low support and shared assay limits preclude independent causal BFP contribution',
      regression_existing_model_predictions_equal=True,unchanged_comparisons=len(merged)))
    save_json(ROOT/'models/molecular/relative_models.json',models)
    save_json(ROOT/'models/molecular/PER_interface.json',{'version':RELEASE,'formula':'PER=100*h(RES)','qualified_absolute_models':[],
      'endpoint':'fraction_of_edited_RNA_molecules','current_endpoint':'relative_C280_chromatogram_composition',
      'stages':{'molecular_reference_available':True,'candidate_signal_detected':True,'relative_index_available':True,'absolute_fraction_qualified':False,
        'relative_prediction_fitted':True,'relative_prediction_internally_evaluated':True,'absolute_prediction_validated':False},
      'PER':None,'status':'ASSAY_VALIDATION_INSUFFICIENT_AND_S7_S10_TRANSFER_UNQUALIFIED',
      'future_adapter_requires':['known RNA mixture response calibration','DNase/noRT evidence','validated target/construct identity','matched population and conditions','independent held-out wells/batches','registered versioned h and transfer domain']})
    print('Molecular comparisons reproduced; linear dose and dose-plus-B sensitivity evaluated',flush=True)

def run():
    layer01();freeze_res();layer3()

if __name__=='__main__':run()
