from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, linregress
from core import *
from inventory import ROOT,write_csv,dump,sha

def run():
    cfg=json.loads((ROOT/'config/analysis.json').read_text()); rng=np.random.default_rng(cfg['seed'])
    df=pd.read_csv(ROOT/'inventory/acquisition_manifest.csv').fillna('')
    if df.profile_id.nunique()!=1:raise ValueError('Multiple optical profiles require separately qualified contexts')
    data={row.acquisition_id:read_fcs(ROOT/row.file_path)[0] for row in df.itertuples()}
    metadata={row.acquisition_id:read_fcs(ROOT/row.file_path)[1] for row in df.itertuples()}
    context=fit_gates(data[cfg['context_training_control']],cfg)
    controls=[cfg['context_training_control'],cfg['transfer_control']]
    ca=[data[k][gate(data[k],context,cfg)[2]] for k in controls]
    bg,bg_se,threshold,rq=background(ca,cfg)
    control_cov=sum(np.cov(a[:,[G,R]],rowvar=False,ddof=1)/len(a) for a in ca)/len(ca)**2
    control_noise=rng.multivariate_normal([0,0],control_cov,size=cfg['bootstrap_repeats'])
    bgrows=[]; transfer=[]
    for k,a in zip(controls,ca):
        for ch,idx in [('EGFP',G),('mCherry',R),('BFP',B)]:
            bgrows.append(dict(control_id=k,channel=ch,n=len(a),mean_linear=float(a[:,idx].mean()),median_linear=float(np.median(a[:,idx])),sd_linear=float(a[:,idx].std(ddof=1)),se_mean=float(a[:,idx].std(ddof=1)/np.sqrt(len(a))),quantile_995=float(np.quantile(a[:,idx],cfg['positivity_quantile'])),used_background=bg[idx],used_threshold=threshold[idx],quantitative_red_boundary=rq if ch=='mCherry' else None,units='linear_detector_au'))
    for train,other in [(0,1),(1,0)]:
        for ch,idx in [('EGFP',G),('mCherry',R),('BFP',B)]:
            boundary=float(np.quantile(ca[train][:,idx],cfg['positivity_quantile']))
            transfer.append(dict(training_control=controls[train],test_control=controls[other],channel=ch,threshold=boundary,test_positive_fraction=float(np.mean(ca[other][:,idx]>boundary)),interpretation='held_out_acquisition_not_confirmed_independent_well_or_multicolor_FMO'))
    context.update(background=bg.tolist(),background_event_se=bg_se.tolist(),positivity_thresholds=threshold.tolist(),red_quantitative_boundary=rq,profile_id=df.iloc[0].profile_id,version=cfg['analysis_version'],optical_status=cfg['status'],config_sha256=sha(ROOT/'config/analysis.json'))
    dump(ROOT/'contexts/context.json',context)
    write_csv(ROOT/'results/background_thresholds.csv',bgrows);write_csv(ROOT/'results/negative_transfer.csv',transfer)
    rows=[];retention=[];time=[];sens=[];sampling=[];influence=[];joint=[];display=[];popcache={};binrows=[];redrows=[];bootrows=[]
    for row in df.itertuples():
        aid=row.acquisition_id;x=data[aid];mock=row.sample_role=='Mock'
        q,cell,s,t,flags=gate(x,context,cfg)
        pr=s&(x[:,R]>rq); pb=pr&(x[:,B]>threshold[B]); pn=pr&~(x[:,B]>threshold[B])
        masks=dict(quality=q,cell=cell,singlet=s,reporter=pr,blue_positive_reporter=pb,blue_negative_reporter=pn)
        np.savez_compressed(ROOT/'masks'/f'{aid}.npz',**masks)
        retention.append(dict(acquisition_id=aid,series=row.series,condition_label=row.condition_label,original=len(x),after_quality=int(q.sum()),after_cell=int(cell.sum()),after_singlet=int(s.sum()),reporter_selected=int(pr.sum()),blue_positive_reporter=int(pb.sum()),retained_fraction=float(s.mean()),**flags))
        time.extend(dict(acquisition_id=aid,**v) for v in t)
        ds=np.sort(rng.choice(len(x),min(1800,len(x)),replace=False))
        display.extend(dict(acquisition_id=aid,event_index_0based=int(i),FSC_A=x[i,1],FSC_H=x[i,0],SSC_A=x[i,3],G=x[i,G],R=x[i,R],B=x[i,B],singlet=bool(s[i]),reporter=bool(pr[i])) for i in ds)
        for pattern in range(8):
            zz=s.copy()
            for bit,idx in enumerate([R,G,B]): zz&=(x[:,idx]>threshold[idx])==bool(pattern&(1<<bit))
            joint.append(dict(acquisition_id=aid,R_positive=bool(pattern&1),G_positive=bool(pattern&2),B_positive=bool(pattern&4),events=int(zz.sum()),denominator_singlets=int(s.sum()),fraction=float(zz.sum()/s.sum())))
        if mock: continue
        for mode,mask in [('reporter',pr),('blue_positive_reporter',pb),('blue_negative_reporter',pn)]:
            if row.series=='S7' and mode!='reporter': continue
            v=x[mask];g=v[:,G]-bg[G];r=v[:,R]-bg[R];res=score(g,r,cfg)
            popcache[(aid,mode)]=(v,g,r)
            linked_editor_present=row.series=='S10' and float(row.condition_label)>0
            coexpression_status=('LINKAGE_USER_CONFIRMED_OPTICAL_BOUNDARY_PROVISIONAL' if linked_editor_present else 'NOT_APPLICABLE_NO_EDITOR') if row.series=='S10' else 'NOT_APPLICABLE_S7_LINKAGE_UNKNOWN'
            interpretation='reporter_editor_coexpression_exploratory' if mode=='blue_positive_reporter' and linked_editor_present else 'blue_negative_diagnostic' if mode=='blue_negative_reporter' else 'no_editor_blue_tail_diagnostic' if mode=='blue_positive_reporter' else 'reporter'
            base=dict(acquisition_id=aid,series=row.series,condition_label=row.condition_label,source_condition_label=row.source_condition_label,replicate_label=row.replicate_label,well_id=row.well_id,population_mode=mode,population_interpretation=interpretation,independent_well_n_verified=1,independent_wells_per_condition=2,reporter_dna_ng=row.reporter_dna_ng,editor_dna_ng=row.editor_dna_ng,total_dna_ng=row.total_dna_ng,analysis_version=cfg['analysis_version'],optical_status=cfg['status'],coexpression_claim_status=coexpression_status,**res)
            base.update(mean_G_raw=float(v[:,G].mean()) if len(v) else None,median_G_raw=float(np.median(v[:,G])) if len(v) else None,mean_R_raw=float(v[:,R].mean()) if len(v) else None,mean_B_raw=float(v[:,B].mean()) if len(v) else None,median_B_raw=float(np.median(v[:,B])) if len(v) else None,EGFP_positive_fraction=float(np.mean(v[:,G]>threshold[G])) if len(v) else None,reporter_detection_fraction=float(np.mean(x[s,R]>threshold[R])),reporter_quant_fraction=float(pr.sum()/s.sum()),B_positive_fraction_singlets=float(np.mean(x[s,B]>threshold[B])),blue_positive_fraction_reporters=float(pb.sum()/pr.sum()) if pr.any() else None,CEF_editor_verified=None,RES=None,RES_status='NOT_CALIBRATED',PER=None,PER_status='NOT_CALIBRATED')
            base.update(mean_G_all_singlets=float(x[s,G].mean()),validated_RAS=None,validated_RAS_status='OPTICAL_AND_LOQ_VALIDATION_UNAVAILABLE')
            base.update(CEF_editor_exploratory=float(pb.sum()/pr.sum()) if linked_editor_present and pr.any() else None,CEF_status='USER_CONFIRMED_LINKAGE_PROVISIONAL_B_BOUNDARY' if linked_editor_present else 'NOT_APPLICABLE_NO_CONFIRMED_EDITOR_PRESENT',metadata_confirmation_source=row.metadata_confirmation_source)
            if res['ras'] is not None:
                boot,eventdraws,controldraws=bootstrap(g,r,control_noise,cfg,rng);base.update(boot)
                bootrows.extend(dict(acquisition_id=aid,population_mode=mode,draw_id=j,event_ras=ee,event_control_ras=cc,shared_background_draw_id=j) for j,(ee,cc) in enumerate(zip(eventdraws,controldraws)))
                n=len(v);sr=r.sum();sg=g.sum();rat=sg/sr;k=max(1,int(np.ceil(n*.01)));top=np.argsort(r)[-k:]
                leave=(sg-g)/(sr-r);infl=float(np.max(np.abs(leave-rat)))
                tail_ratio=float((sg-g[top].sum())/(sr-r[top].sum()))
                influence.append(dict(acquisition_id=aid,population_mode=mode,ras=rat,n=n,top_one_percent_red_share=float(r[top].sum()/sr),top_one_percent_green_share=float(g[top].sum()/sg) if sg else None,ras_without_top_one_percent_red=tail_ratio,relative_change_without_top_one_percent=float((tail_ratio-rat)/abs(rat)) if rat else None,max_leave_one_out_change=infl,effective_red_events=res['effective_red_events'],max_red_weight=res['max_red_weight'],bright_events_removed_from_primary=False))
                for ns in cfg['subsample_sizes']:
                    if ns>n: continue
                    vals=[]
                    for _ in range(cfg['subsample_repeats']):
                        ix=rng.choice(n,ns,replace=False); vals.append(float(g[ix].sum()/r[ix].sum()))
                    sampling.append(dict(acquisition_id=aid,population_mode=mode,selected_total=n,sample_n=ns,repeats=len(vals),full_ras=rat,subsample_mean=float(np.mean(vals)),subsample_sd=float(np.std(vals,ddof=1)),q025=float(np.quantile(vals,.025)),q975=float(np.quantile(vals,.975)),sampling='without_replacement_conditional_finite_acquisition'))
            base['qc_state']='WARN_OPTICAL_UNVALIDATED' if base['ras'] is not None else 'FAIL_QUANTIFICATION'
            if base.get('max_red_weight',0)>cfg['max_red_weight_warning']:base['qc_state']+=';HIGH_INFLUENCE'
            if flags['rate_removed']:base['qc_state']+=';TIME_FILTERED'
            rows.append(base)
        # All alternative gates are predeclared and preserve signed paired fluorescence.
        alternatives=[('scatter_0.975',.975,None,False),('scatter_0.995',.995,None,False),('singlet_2.5MAD',None,2.5,False),('singlet_3.5MAD',None,3.5,False),('without_time_filter',None,None,True)]
        for name,prob,sm,nt in alternatives:
            altca=[data[k][gate(data[k],context,cfg,prob,sm,nt)[2]] for k in controls]
            ab,ase,ath,arq=background(altca,cfg); ss=gate(x,context,cfg,prob,sm,nt)[2]
            pp=ss&(x[:,R]>arq)
            for mode,mm in [('reporter',pp),('blue_positive_reporter',pp&(x[:,B]>ath[B]))]:
                if row.series=='S7' and mode!='reporter':continue
                rr=score(x[mm,G]-ab[G],x[mm,R]-ab[R],cfg)
                sens.append(dict(acquisition_id=aid,population_mode=mode,scenario=name,type='gate_context_refit',ras=rr['ras'],n=rr['n_selected']))
        bgs=[('Mock1_mean',ca[0].mean(axis=0)),('Mock2_mean',ca[1].mean(axis=0)),('control_median_NOT_expected_additive',np.mean([np.median(a,axis=0) for a in ca],axis=0)),('no_subtraction',np.zeros(12))]
        for name,ab in bgs:
            for mode,mm in [('reporter',pr),('blue_positive_reporter',pb)]:
                if row.series=='S7' and mode!='reporter':continue
                rr=score(x[mm,G]-ab[G],x[mm,R]-ab[R],cfg)
                sens.append(dict(acquisition_id=aid,population_mode=mode,scenario=name,type='background_fixed_events',ras=rr['ras'],n=rr['n_selected']))
        for quant in [.99,.999]:
            ath=np.max([np.quantile(a,quant,axis=0) for a in ca],axis=0);arq=max(ath[R],bg[R]+cfg['red_min_background_sd_multiplier']*np.sqrt(np.mean([a[:,R].var(ddof=1) for a in ca])))
            for mode,mm in [('reporter',s&(x[:,R]>arq)),('blue_positive_reporter',s&(x[:,R]>arq)&(x[:,B]>ath[B]))]:
                if row.series=='S7' and mode!='reporter':continue
                rr=score(x[mm,G]-bg[G],x[mm,R]-bg[R],cfg);sens.append(dict(acquisition_id=aid,population_mode=mode,scenario=f'negative_quantile_{quant}',type='threshold',ras=rr['ras'],n=rr['n_selected']))
        print(aid,'singlets',s.sum(),'reporter',pr.sum(),flush=True)
    result=pd.DataFrame(rows)
    # Equal-width bins on log10 raw signal, with common endpoints from every eligible acquisition.
    # These profiles are descriptive, never used to select the primary score.
    for channel,idx,target in [('red',R,redrows),('blue',B,binrows)]:
        ids=[r.acquisition_id for r in df.itertuples() if r.sample_role!='Mock' and (channel=='red' or (r.series=='S10' and float(r.condition_label)>0))]
        profile_mode='reporter' if channel=='red' else 'blue_positive_reporter'
        lo=max(np.quantile(popcache[(aid,profile_mode)][0][:,idx],.05) for aid in ids)
        hi=min(np.quantile(popcache[(aid,profile_mode)][0][:,idx],.95) for aid in ids)
        if hi<=lo:continue
        bounds=np.geomspace(max(lo,1e-8),hi,5)
        for aid in ids:
            v,g,r=popcache[(aid,profile_mode)]
            for j,(l,h) in enumerate(zip(bounds[:-1],bounds[1:])):
                m=(v[:,idx]>=l)&(v[:,idx]<(h if j<3 else np.nextafter(h,np.inf)))
                rr=score(g[m],r[m],cfg);target.append(dict(acquisition_id=aid,population_mode=profile_mode,channel=channel,bin=j,lower=l,upper=h,center=np.sqrt(l*h),coverage_fraction=float(m.mean()),units='raw_linear_detector_au',**rr))
    # No-editor-labelled reporter controls give a relevant negative-spread diagnostic, not a single-color compensation estimate.
    blueaudit=[]
    zeroids=[r.acquisition_id for r in df.itertuples() if r.series=='S10' and r.sample_role!='Mock' and float(r.condition_label)==0]
    blue_boundary=max(np.quantile(popcache[(aid,'reporter')][0][:,B],.995) for aid in zeroids)
    for aid in [r.acquisition_id for r in df.itertuples() if r.series=='S10']:
        v,g,r=popcache[(aid,'reporter')];m=v[:,B]>blue_boundary
        rr=score(g[m],r[m],cfg)
        blueaudit.append(dict(acquisition_id=aid,alternative_B_boundary=blue_boundary,mock_B_boundary=threshold[B],B_positive_fraction_reporter=float(m.mean()),ras_blue_selected=rr['ras'],n=rr['n_selected'],status='no_editor_control_negative_transfer_linkage_user_confirmed_optics_provisional'))
    repeat=[]
    for (series,condition,mode),grp in result.groupby(['series','condition_label','population_mode']):
        for metric in ['mean_G_raw','mean_G_corrected','ras']:
            z=grp[metric].dropna().to_numpy(float);mean=z.mean() if len(z) else np.nan;sd=z.std(ddof=1) if len(z)>1 else np.nan
            repeat.append(dict(series=series,condition_label=condition,population_mode=mode,metric=metric,acquisition_n=len(z),verified_independent_well_n=int(grp.loc[grp[metric].notna(),'well_id'].nunique()),planned_independent_well_n=2,labels=';'.join(grp.acquisition_id),mean=mean,sd=sd,cv_percent=100*sd/abs(mean) if mean!=0 else None,definition='sample_SD_ddof1_divided_by_absolute_mean_times100',status='independent_transfection_well_repeatability_within_experiment_n2_user_confirmed'))
    rep=pd.DataFrame(repeat);write_csv(ROOT/'results/repeatability.csv',repeat)
    response=[];adj=[]
    for (series,mode),grp in result.groupby(['series','population_mode']):
        cond=grp.groupby('condition_label').agg(ras_mean=('ras','mean'),ras_sd=('ras','std'),acquisition_n=('ras','count')).reset_index().sort_values('condition_label')
        cond['verified_independent_well_n']=cond.acquisition_n
        for rr in cond.to_dict('records'):response.append(dict(series=series,population_mode=mode,**rr))
        for j in range(1,len(cond)):
            a,b=cond.iloc[j-1],cond.iloc[j];adj.append(dict(series=series,population_mode=mode,from_condition=a.condition_label,to_condition=b.condition_label,delta_mean_ras=b.ras_mean-a.ras_mean,positive_slope=bool(b.ras_mean>a.ras_mean)))
    tables={'ras_results':rows,'event_retention':retention,'time_qc':time,'sensitivity':sens,'event_count_sensitivity':sampling,'high_expression_influence':influence,'binary_populations':joint,'blue_profiles':binrows,'red_profiles':redrows,'B_negative_transfer':blueaudit,'response_summary':response,'adjacent_response':adj,'bootstrap_draws':bootrows}
    for name,table in tables.items():write_csv(ROOT/'results'/f'{name}.csv',table)
    write_csv(ROOT/'figures/source_tables/event_display_subset.csv',display)
    associations=[]
    for series in ['S7','S10']:
        for mode,grp in result[result.series==series].groupby('population_mode'):
            for metric in ['ras','mean_G_raw','mean_R_raw','median_B_raw','blue_positive_fraction_reporters']:
                z=grp.groupby('condition_label')[metric].mean().dropna();r,p=spearmanr(z.index.astype(float),z.values)
                associations.append(dict(series=series,population_mode=mode,metric=metric,condition_n=len(z),spearman_rho=float(r),p_descriptive_only=float(p),status='condition_mean_association_not_independent_dose_validation'))
    write_csv(ROOT/'results/associations.csv',associations)
    # Algebraic identity must hold for the partition of the same reporter population.
    identity=[]
    for aid in zeroids+ [r.acquisition_id for r in df.itertuples() if r.series=='S10' and r.sample_role!='Mock' and float(r.condition_label)>0]:
        vals={m:popcache[(aid,m)] for m in ['reporter','blue_positive_reporter','blue_negative_reporter']}
        sr=vals['reporter'][2].sum();w=vals['blue_positive_reporter'][2].sum()/sr
        ratios={m:v[1].sum()/v[2].sum() for m,v in vals.items()}
        error=ratios['reporter']-(w*ratios['blue_positive_reporter']+(1-w)*ratios['blue_negative_reporter'])
        identity.append(dict(acquisition_id=aid,red_weight_B_positive=w,reconstruction_error=error))
    write_csv(ROOT/'results/partition_identity.csv',identity)
    print('Completed fresh flow analysis',len(result),'outputs',flush=True)

if __name__=='__main__':run()
