"""Before/after calibration evidence and conditional inverse-domain assessment."""
from scipy.stats import t
from layer23_common import *
from s7_correction import BASE,CORR
from reporter_calibration import fit_model,predict,MODELS
from inverse_calibration import inverse,set_ranges
from biological_calibration import ols_fit,ols_predict

def run():
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv')
    x=s.corrected_ac_mass_fraction.to_numpy();y=s.ras.to_numpy()
    old=pd.read_csv(BASE/'results/calibration/S7_model_comparison.csv');new=pd.read_csv(ROOT/'results/calibration/S7_model_comparison.csv')
    oldp=pd.read_csv(BASE/'results/calibration/S7_calibration_predictions.csv');old['training_R2']=old.model.map({n:1-np.sum(z.residual**2)/np.sum((z.observed_RAS-z.observed_RAS.mean())**2) for n,z in oldp.groupby('model')})
    metrics=['training_R2','RAS_RMSE','RAS_MAE','RAS_bias','RAS_prediction_n','inverse_recovery_n','inverse_MAE_mass_fraction','inverse_RMSE_mass_fraction','inverse_bias_mass_fraction']
    cmp=old[['model','validation']+metrics].merge(new[['model','validation']+metrics],on=['model','validation'],suffixes=('_original','_corrected'))
    for m in metrics:cmp[m+'_change']=cmp[m+'_corrected']-cmp[m+'_original']
    table('results/calibration/S7_before_after_model_comparison.csv',cmp)
    oldr=pd.read_csv(BASE/'results/ras_results.csv');oldr=oldr[(oldr.series=='S7')&(oldr.population_mode=='reporter')]
    both=[]
    for label,d,axis in [('original_recorded_v3',oldr,'condition_label'),('team_corrected_v4',s,'condition_label')]:
        for a,z in d.groupby(axis):both.append(dict(label_basis=label,AC_mass_fraction=a/100,mean_RAS=z.ras.mean(),SD_RAS=z.ras.std(ddof=1),well_n=len(z),original_ids=';'.join(z.acquisition_id)))
    table('results/calibration/S7_before_after_response.csv',both)
    # Empirical adjacent differences keep n=2 well uncertainty separate from event precision.
    contrasts=[]
    for a,b in zip(sorted(set(x))[:-1],sorted(set(x))[1:]):
        u=y[x==a];v=y[x==b];va=u.var(ddof=1)/len(u);vb=v.var(ddof=1)/len(v);se=np.sqrt(va+vb);df=(va+vb)**2/(va**2/(len(u)-1)+vb**2/(len(v)-1));delta=v.mean()-u.mean();half=t.ppf(.975,df)*se
        contrasts.append(dict(lower_mass_fraction=a,upper_mass_fraction=b,delta_RAS=delta,well_SE=se,Welch_df=df,difference_low=delta-half,difference_high=delta+half,zero_in_interval=bool(delta-half<=0<=delta+half),interpretation='DESCRIPTIVE_WELCH_95_INTERVAL_N2_ASSUMPTIONS_NOT_EQUIVALENCE_TEST'))
    table('results/calibration/S7_adjacent_level_distinguishability.csv',contrasts)
    models=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text());curves=pd.read_csv(ROOT/'results/calibration/S7_calibration_curves.csv')
    resolution=[];domains=[]
    for name,model in models.items():
        c=curves[curves.model==name];grid=c.AC_mass_fraction.to_numpy();values=c.predicted_RAS.to_numpy();low=c.diagnostic_prediction_low.to_numpy();high=c.diagnostic_prediction_high.to_numpy();kn=np.array(model['knots']);vv=np.array(model['values']);slopes=np.diff(vv)/np.diff(kn);rows=[]
        for a,ras in zip(grid,values):
            j=min(max(0,np.searchsorted(kn,a,side='right')-1),len(slopes)-1);slope=slopes[j];ii=inverse(model,ras);ranges,lo,hi=set_ranges(grid,(low<=ras)&(high>=ras));width=hi-lo if lo is not None else np.nan
            interior=lo is not None and lo>0 and hi<1
            narrow=bool(ii['point'] is not None and slope>1e-12 and interior and width<=CFG['S7_resolution_width_diagnostic']+1e-12)
            row=dict(model=name,nominal_AC_mass_fraction=a,model_RAS=ras,local_slope_RAS_per_mass_fraction=slope,mass_change_per_0p01_RAS=.01/slope if slope>1e-12 else None,inverse_point=ii['point'],inverse_status=ii['status'],compatible_low=lo,compatible_high=hi,compatible_width=width,interior_without_boundary_truncation=interior,narrow_exploratory_screen=narrow,qualification='EXPLORATORY_NOT_VALIDATED',reference_basis_id=CORR['reference_basis_id']);rows.append(row)
        resolution.extend(rows);d=pd.DataFrame(rows);ranges,_,_=set_ranges(grid,d.narrow_exploratory_screen.to_numpy())
        for n,(lo,hi) in enumerate(ranges):
            z=d[(d.nominal_AC_mass_fraction>=lo)&(d.nominal_AC_mass_fraction<=hi)]
            domains.append(dict(model=name,segment=n+1,model_mass_low=lo,model_mass_high=hi,RAS_low=z.model_RAS.min(),RAS_high=z.model_RAS.max(),maximum_compatibility_width=z.compatible_width.max(),status='EXPLORATORY',qualification='Configuration-fixed <=0.20 width; unique inverse; positive local slope; neither reference boundary truncates set; internal diagnostic only'))
        if not ranges:domains.append(dict(model=name,segment=0,model_mass_low=None,model_mass_high=None,RAS_low=None,RAS_high=None,maximum_compatibility_width=None,status='NO_NARROW_INTERIOR_DOMAIN',qualification='No model grid segment meets exploratory screen; not an absolute assay validity test'))
    table('results/calibration/S7_local_inverse_resolution.csv',resolution);table('results/calibration/S7_exploratory_domains.csv',domains)
    # Compare inverse error on identical estimable held-out wells; availability is itself evidence.
    cv=pd.read_csv(ROOT/'results/calibration/S7_internal_validation.csv');matched=[]
    for scheme,z in cv.groupby('validation'):
        common=set.intersection(*(set(q.loc[q.mass_recovery_error.notna(),'test_well']) for _,q in z.groupby('model')))
        for name,q in z.groupby('model'):
            q=q[q.test_well.isin(common)];e=q.mass_recovery_error
            matched.append(dict(model=name,validation=scheme,common_well_n=len(q),common_wells=';'.join(sorted(common)),MAE_mass_fraction=e.abs().mean(),RMSE_mass_fraction=np.sqrt(np.mean(e**2)),bias_mass_fraction=e.mean()))
    table('results/calibration/S7_matched_inverse_validation.csv',matched)
    # Model-robust screen: require both better-performing shape models and their union envelope.
    joint=[]
    for val in np.linspace(.45,1.2,1501):
        results=[]
        for name in ['isotonic','monotone_hinge_50']:
            c=curves[curves.model==name];ii=inverse(models[name],val);_,lo,hi=set_ranges(c.AC_mass_fraction.to_numpy(),((c.diagnostic_prediction_low<=val)&(c.diagnostic_prediction_high>=val)).to_numpy());results.append((ii,lo,hi))
        available=all(ii['point'] is not None and lo is not None for ii,lo,hi in results)
        lo=min(a[1] for a in results) if all(a[1] is not None for a in results) else None;hi=max(a[2] for a in results) if all(a[2] is not None for a in results) else None
        width=hi-lo if lo is not None else None;passes=available and lo>0 and hi<1 and width<=CFG['S7_resolution_width_diagnostic']+1e-12
        joint.append(dict(RAS=val,isotonic_point=results[0][0]['point'],hinge_point=results[1][0]['point'],union_compatible_low=lo,union_compatible_high=hi,union_width=width,joint_narrow_interior=passes,status='EXPLORATORY' if passes else 'NO_JOINT_NARROW_SUPPORT',not_a_validated_confidence_interval=True))
    joint=pd.DataFrame(joint);table('results/calibration/S7_cross_model_inverse_support.csv',joint)
    ranges,_,_=set_ranges(joint.RAS.to_numpy(),joint.joint_narrow_interior.to_numpy());table('results/calibration/S7_cross_model_supported_ranges.csv',[dict(RAS_low=a,RAS_high=b,qualification='EXPLORATORY_ONLY_UNION_OF_ISOTONIC_AND_HINGE_ENVELOPES',resolution_width_threshold=CFG['S7_resolution_width_diagnostic']) for a,b in ranges])
    # Every reported reference-equivalent value identifies its basis, model, population and limits.
    res=pd.read_csv(ROOT/'results/calibration/S7_RES_results.csv')
    res['population_mode']='reporter';res['calibration_model_id']=VERSION+'::'+res.model;res['reference_basis_id']=CORR['reference_basis_id'];res['applicable_domain']='S7 same-session reporter population under team-corrected AC DNA mass labels; not qualified for S10';res['correction_evidence_status']=CORR['correction_status']
    res['RES_status']=res.inverse_status.map({'EXPLORATORY_UNIQUE_MODEL_INVERSE':'EXPLORATORY','NON_IDENTIFIABLE_PLATEAU':'NONIDENTIFIABLE','OUT_OF_CALIBRATION_RANGE':'OUT_OF_CALIBRATION_RANGE'}).fillna('NOT_CALIBRATED')
    res['diagnostic_compatibility_width']=res.diagnostic_compatible_mass_high-res.diagnostic_compatible_mass_low
    res['narrow_interior_compatibility']=res.RES_exploratory_mass_fraction.notna()&(res.diagnostic_compatibility_width<=CFG['S7_resolution_width_diagnostic']+1e-12)&(res.diagnostic_compatible_mass_low>0)&(res.diagnostic_compatible_mass_high<1)
    table('results/calibration/S7_RES_results.csv',res)
    inv=pd.read_csv(ROOT/'results/calibration/S7_inverse_identifiability.csv');inv['reference_basis_id']=CORR['reference_basis_id'];inv['calibration_model_id']=VERSION+'::'+inv.model;table('results/calibration/S7_inverse_identifiability.csv',inv)
    sensitivities=[];sensitivity_inverse=[]
    for scenario in CORR['sensitivity_scenarios']:
        if scenario.endswith('_wells_only'):keep=s.replicate_label.eq(scenario[0]).to_numpy()
        else:keep=~np.isin(x,{'omit_75':[.75],'omit_90':[.9],'omit_100':[1.],'omit_90_and_100':[.9,1.]}[scenario])
        for name in MODELS:
            m=fit_model(name,x[keep],y[keep]);grid=np.linspace(m['x_min'],m['x_max'],201);change=predict(m,grid)-predict(models[name],grid)
            sensitivities.append(dict(model=name,scenario=scenario,reference_wells=int(keep.sum()),input_min=m['x_min'],input_max=m['x_max'],maximum_abs_RAS_change_on_common_input=float(np.max(abs(change))),RMS_change_on_common_input=float(np.sqrt(np.mean(change**2))),coefficients=json.dumps(m['coefficients']),knots=json.dumps(m['knots']),values=json.dumps(m['values']),interpretation='DIAGNOSTIC_REFITS_ONLY_ALL_20_WELLS_REMAIN_PRIMARY'))
            for val in [.55,.65,.8,1.,1.1]:
                ii=inverse(m,val);full=inverse(models[name],val)
                sensitivity_inverse.append(dict(model=name,scenario=scenario,RAS=val,point=ii['point'],low=ii['low'],high=ii['high'],status=ii['status'],full_point=full['point'],change=None if ii['point'] is None or full['point'] is None else ii['point']-full['point']))
    table('results/calibration/S7_reference_sensitivity.csv',sensitivities);table('results/calibration/S7_inverse_sensitivity.csv',sensitivity_inverse)
    # Same-mode hypothetical mapping only; carry the corrected inverse envelope along.
    mapping=pd.read_csv(ROOT/'results/calibration/S10_hypothetical_S7_mapping.csv')
    for i,row in mapping.iterrows():
        c=curves[curves.model==row.model];_,lo,hi=set_ranges(c.AC_mass_fraction.to_numpy(),((c.diagnostic_prediction_low<=row.RAS)&(c.diagnostic_prediction_high>=row.RAS)).to_numpy())
        mapping.loc[i,'diagnostic_compatible_mass_low']=lo;mapping.loc[i,'diagnostic_compatible_mass_high']=hi
    mapping['reference_basis_id']=CORR['reference_basis_id'];mapping['calibration_model_id']=VERSION+'::'+mapping.model;mapping['RES_status']='NOT_CALIBRATED';mapping['sensitivity_status']='HYPOTHETICAL_UNQUALIFIED_TRANSFER';table('results/calibration/S10_hypothetical_S7_mapping.csv',mapping)
    compat=pd.read_csv(BASE/'results/calibration/S7_S10_compatibility.csv');compat['reference_basis_id']=CORR['reference_basis_id'];compat.loc[compat.dimension=='reference_axis','S7']='Corrected AC DNA mass mixture; probable label transposition authorized retrospectively'
    extra=[('total_DNA_loading','not documented per S7 well','1000 ng/well user-confirmed','UNRESOLVED'),('sampling_time','exact elapsed culture/treatment timing not documented','RNA after flow at same experimental timepoint; elapsed minutes unknown','UNRESOLVED'),('BFP_linkage','S7 linkage unverified','ORCA-P2A-BFP confirmed','DIFFERENT_OR_UNRESOLVED')]
    compat=pd.concat([compat,pd.DataFrame([dict(dimension=a,S7=b,S10=c,status=d,calibration_transfer_qualified=False,reference_basis_id=CORR['reference_basis_id']) for a,b,c,d in extra])],ignore_index=True);table('results/calibration/S7_S10_compatibility.csv',compat)
    # Recalculate the only v3 calibration-dependent prediction: explicit affine information check.
    pairs=pd.read_csv(ROOT/'results/prediction/S10_flow_molecular_pairs.csv');validation=pd.read_csv(ROOT/'results/prediction/S10_prediction_validation.csv');trans=np.array([inverse(models['affine'],v)['point'] for v in pairs.RAS_reporter],float);algebra=[]
    for row in validation[validation.model=='reporter_RAS'].itertuples():
        train=pairs.well_id.isin(row.train_wells.split(';')).to_numpy();test=(pairs.well_id==row.test_well).to_numpy();ok=np.isfinite(trans[train]).all() and np.isfinite(trans[test]).all();pred=np.nan
        if ok:pred=float(ols_predict(ols_fit(trans[train,None],pairs.raw_signal_index.to_numpy()[train]),trans[test,None])[0][0])
        algebra.append(dict(validation=row.validation,test_well=row.test_well,direct_prediction=row.predicted_signal,hypothetical_affine_staged_prediction=pred,difference=pred-row.predicted_signal,status='MATHEMATICAL_SENSITIVITY_ONLY_TRANSFER_UNQUALIFIED' if ok else 'OUT_OF_CALIBRATION_RANGE',reference_basis_id=CORR['reference_basis_id']))
    table('results/prediction/S10_affine_transform_sensitivity.csv',algebra)
    predsummary=json.loads((BASE/'results/prediction/S10_prediction_summary.json').read_text());predsummary['maximum_affine_transform_difference']=max(abs(r['difference']) for r in algebra);predsummary['calibration_sensitivity_version']=VERSION;predsummary['direct_models_version']=predsummary['version'];jsonout('results/prediction/S10_prediction_summary.json',predsummary)
    table('results/prediction/S10_staged_model_results.csv',[dict(model='RAS_to_corrected_S7_RES_to_RNA_fraction',status='NOT_CALIBRATED',fitted=False,PER=None,reasons='S7 inverse improved conditionally; S7/S10 construct/loading/treatment/population transfer still unqualified; molecular endpoint remains uncalibrated chromatogram index',reference_basis_id=CORR['reference_basis_id'],maximum_affine_prediction_difference=max(abs(r['difference']) for r in algebra))])
    status=pd.read_csv(BASE/'results/prediction/SONAR_layer_status.csv');status.loc[status.layer==2,['highest_output','limit']]=['improved_corrected_reference_specific_exploratory_RES','low_and_high_plateaus_retrospective_labels_internal_validation_only'];table('results/prediction/SONAR_layer_status.csv',status)
    best_old=old[old.validation=='leave_one_reference_level_out'].sort_values('RAS_RMSE').iloc[0];best_new=new[new.validation=='leave_one_reference_level_out'].sort_values('RAS_RMSE').iloc[0]
    jsonout('results/calibration/S7_correction_summary.json',dict(version=VERSION,reference_basis_id=CORR['reference_basis_id'],correction_independently_verified=False,best_forward_model_original=best_old.model,best_forward_model_corrected=best_new.model,original_leave_level_RMSE=best_old.RAS_RMSE,corrected_leave_level_RMSE=best_new.RAS_RMSE,narrow_interior_domains=domains,validated_RES_count=0,exploratory_inverse_points=int(res.RES_exploratory_mass_fraction.notna().sum()),S10_transfer_qualified=False,direct_molecular_results_preserved=True,maximum_affine_prediction_difference=max(abs(r['difference']) for r in algebra)))
    print('Corrected calibration compared with v3; inverse domains, sensitivities and transfer evaluated',flush=True)

if __name__=='__main__':run()
