"""Site-specific chromatogram composition, grouped by molecule and transfection well."""
import numpy as np,pandas as pd
from Bio import SeqIO
from scipy.stats import spearmanr
from ab1_processing import read_ab1,site_metrics
from layer23_common import *
from sample_metadata import molecular_metadata

def run():
    reference=str(SeqIO.read(ROOT/'results/molecular/OpenA_amplicon_consensus.fasta','fasta').seq)
    sites=pd.read_csv(ROOT/'results/molecular/OpenA_candidate_editing_sites.csv')
    reads=[read_ab1(p) for p in sorted((ROOT/'inputs/S10/测序').rglob('*.ab1'))]
    metrics=[];trace=[];read_audit=[]
    for read in reads:
        pair=molecular_metadata(read['label']);base=dict(flow_acquisition_id=pair['flow_acquisition_pair'],well_id=pair['well_id'],dose_ratio=pair['editor_ratio'],vendor_mixed_peak_flag=read['label']=='1-8-2' and read['direction']=='F')
        for pos in sites.position_1based:
            v=site_metrics(reference,read,int(pos));v['source_AB1']=str(read['path'].relative_to(ROOT));v.update(base);metrics.append(v)
        t=next(v for v in metrics if v['read_id']==read['read_id'] and v['position_1based']==280)
        loc=t.get('scan_index_0based');idx=t.get('AB1_base_index_1based',1)-1
        signal=np.stack([read['traces'][b][read['loc']] for b in 'ACGT'],axis=1)
        high=np.flatnonzero(read['q']>=30);called=np.array(list(read['seq']))
        empirical=np.array(list('ACGT'))[signal.argmax(axis=1)]
        read_audit.append(dict(read_id=read['read_id'],sample_label=read['label'],direction=read['direction'],**base,source=str(read['path'].relative_to(ROOT)),sha256=sha(read['path']),abif_version=read['version'],dye_order=read['order'],byte_decoder_agrees=True,RevC=read['raw'].get('RevC1',0),Q30_calls=len(high),Q30_called_dominant_channel_agreement=float(np.mean(called[high]==empirical[high])),Q20_bases=int((read['q']>=20).sum()),called_bases=len(read['seq']),trim_start_oriented_1based=read['trim'][0]+1,trim_end_oriented_1based=read['trim'][1],target_eligible=t.get('eligible',False),target_failure_reasons=t.get('failure_reasons','UNMAPPED')))
        if read['label'] in ['1-0-1','1-8-1','1-8-2'] and loc is not None:
            spacing=float(np.median(np.diff(read['loc'][max(0,idx-10):idx+11])))
            for scan in range(max(0,int(loc-10*spacing)),min(len(read['traces']['A']),int(loc+10*spacing)+1)):
                trace.append(dict(read_id=read['read_id'],sample_label=read['label'],direction=read['direction'],scan_index_0based=scan,relative_scan=scan-loc,relative_forward_base_distance=(scan-loc)/spacing*(1 if read['direction']=='F' else -1),target_eligible=t.get('eligible',False),**{b:read['traces'][b][scan] for b in 'ACGT'}))
        print('AB1',read['label'],read['direction'],'target',t.get('signal_status'),flush=True)
    allm=pd.DataFrame(metrics);allm['eligible']=allm.eligible.eq(True);target=allm[allm.position_1based==280].copy()
    table('results/molecular/S10_read_metadata_audit.csv',read_audit)
    table('results/molecular/S10_all_cytidine_peak_metrics.csv',allm)
    table('results/molecular/S10_read_level_peak_metrics.csv',target)
    table('results/molecular/S10_chromatogram_plot_points.csv',trace)
    valid=target[target.eligible.fillna(False)].copy()
    # Direction-specific no-editor background from equal-weight well means.
    bg={}
    methods=['raw_peak_ratio','baseline_peak_ratio','nearby_max_ratio','peak_area_ratio']
    bgrows=[]
    for dire in ['F','R']:
        for method in methods:
            control=valid[(valid.dose_ratio==0)&(valid.direction==dire)].groupby('well_id')[method].mean()
            value=float(control.mean());bg[(dire,method)]=value
            bgrows.append(dict(direction=dire,processing=method,background=value,well_n=len(control),sd_between_wells=control.std(ddof=1),calibrated_to_editing_fraction=False))
    table('results/molecular/S10_no_editor_background.csv',bgrows)
    for method in methods:
        target[method+'_minus_control']=[v-bg[(d,method)] if e else np.nan for v,d,e in zip(target[method],target.direction,target.eligible)]
    table('results/molecular/S10_read_level_peak_metrics.csv',target)
    pairs=[]
    for label,z in target.groupby('sample_label'):
        f=z[z.direction=='F'].iloc[0];r=z[z.direction=='R'].iloc[0];ok=bool(f.eligible and r.eligible)
        row=dict(sample_label=label,flow_acquisition_id=f.flow_acquisition_id,well_id=f.well_id,dose_ratio=f.dose_ratio,F_eligible=f.eligible,R_eligible=r.eligible,complete_pair=ok,F_raw=f.raw_peak_ratio if f.eligible else None,R_raw=r.raw_peak_ratio if r.eligible else None,F_minus_control=f.raw_peak_ratio_minus_control if f.eligible else None,R_minus_control=r.raw_peak_ratio_minus_control if r.eligible else None,raw_R_minus_F=r.raw_peak_ratio-f.raw_peak_ratio if ok else None,corrected_R_minus_F=r.raw_peak_ratio_minus_control-f.raw_peak_ratio_minus_control if ok else None,paired_signal_index=(f.raw_peak_ratio_minus_control+r.raw_peak_ratio_minus_control)/2 if ok else None,status='EXPLORATORY_DIRECTION_AVERAGED_SIGNAL_INDEX' if ok else 'INCOMPLETE_TECHNICAL_PAIR',missing_policy='No single-direction imputation')
        for method in methods:row['index_'+method]=(f[method+'_minus_control']+r[method+'_minus_control'])/2 if ok else None
        pairs.append(row)
    pairdf=pd.DataFrame(pairs);table('results/molecular/S10_bidirectional_concordance.csv',pairdf)
    well=[]
    for wid,z in pairdf.groupby('well_id'):
        tr=target[target.well_id==wid];complete=z[z.complete_pair];signals=complete.paired_signal_index.to_numpy();n=len(signals)
        row=dict(well_id=wid,flow_acquisition_id=z.flow_acquisition_id.iloc[0],dose_ratio=z.dose_ratio.iloc[0],independent_well_n=1,molecular_labels=';'.join(z.sample_label),molecular_label_n=len(z),read_n=len(tr),eligible_read_n=int(tr.eligible.sum()),complete_molecular_pairs=n,signal_index=float(signals.mean()) if n else None,technical_pair_SD=float(signals.std(ddof=1)) if n>1 else None,technical_mean_SE=float(signals.std(ddof=1)/np.sqrt(n)) if n>1 else None,technical_uncertainty_status='DESCRIPTIVE_TWO_NESTED_LABELS_NOT_BIOLOGICAL_CI' if n>1 else 'UNAVAILABLE_ONLY_ONE_COMPLETE_LABEL',RNA_editing_fraction=None,molecular_fraction_status='ASSAY_VALIDATION_INSUFFICIENT',site_status='CANDIDATE_SITE_SUPPORTED',signal_status='EDITING_ASSOCIATED_SIGNAL_EXPLORATORY' if n else 'UNAVAILABLE',RNA_origin='user_confirmed_flow_then_RNA',RNA_population='undocumented_not_assumed_RplusBplus',DNase_noRT_documented=False)
        for dire in ['F','R']:
            zz=tr[(tr.direction==dire)&tr.eligible];row[dire+'_raw_mean']=zz.raw_peak_ratio.mean();row[dire+'_minus_control_mean']=zz.raw_peak_ratio_minus_control.mean();row[dire+'_eligible_n']=len(zz)
        for method in methods:row['index_'+method]=complete['index_'+method].mean()
        well.append(row)
    w=pd.DataFrame(well).sort_values(['dose_ratio','well_id']);table('results/molecular/S10_well_level_molecular_results.csv',w)
    condition=w.groupby('dose_ratio').agg(well_n=('well_id','nunique'),signal_mean=('signal_index','mean'),signal_SD=('signal_index','std'),F_raw_mean=('F_raw_mean','mean'),R_raw_mean=('R_raw_mean','mean'),F_minus_control=('F_minus_control_mean','mean'),R_minus_control=('R_minus_control_mean','mean')).reset_index()
    table('results/molecular/S10_condition_molecular_summary.csv',condition)
    # Every cytidine is screened; no dose-based target selection or significance claims.
    bystanders=[]
    for pos,z in allm.groupby('position_1based'):
        z=z[z.eligible.fillna(False)]
        rec=dict(position_1based=pos,screen_status='DESCRIPTIVE_MULTISITE_NO_MULTIPLICITY_ADJUSTED_INFERENCE')
        for dire in ['F','R']:
            d=z[z.direction==dire].groupby(['dose_ratio','well_id']).raw_peak_ratio.mean().reset_index();lo=d[d.dose_ratio==0];hi=d[d.dose_ratio==8]
            rec[dire+'_well_n']=len(d);rec[dire+'_no_editor_mean']=lo.raw_peak_ratio.mean();rec[dire+'_high_editor_mean']=hi.raw_peak_ratio.mean();rec[dire+'_high_minus_control']=hi.raw_peak_ratio.mean()-lo.raw_peak_ratio.mean();rec[dire+'_all_high_wells_above_control_max']=len(hi)==2 and len(lo)==2 and bool(hi.raw_peak_ratio.min()>lo.raw_peak_ratio.max())
            rec[dire+'_dose_spearman']=float(spearmanr(d.dose_ratio,d.raw_peak_ratio).statistic) if len(d)>2 else None
        rec['both_direction_high_above_control']=rec['F_all_high_wells_above_control_max'] and rec['R_all_high_wells_above_control_max']
        bystanders.append(rec)
    bs=pd.DataFrame(bystanders).merge(sites[['position_1based','reference_codon','alternative_codon','stop_gain','architecture_region','mechanistic_priority']],on='position_1based')
    table('results/molecular/S10_bystander_site_analysis.csv',bs)
    processing=[]
    for method in methods:
        for d,z in w.groupby('dose_ratio'):processing.append(dict(processing=method,dose_ratio=d,well_n=len(z),mean_index=z['index_'+method].mean(),sd_index=z['index_'+method].std(ddof=1)))
    # Explicit sensitivity: unfiltered metrics include the vendor-flagged, misaligned trace only as a diagnostic.
    for d,z in target.groupby('dose_ratio'):
        processing.append(dict(processing='UNFILTERED_DIAGNOSTIC_RAW_NOT_SITE_VALID',dose_ratio=d,well_n=z.well_id.nunique(),mean_index=np.mean([z[z.direction==dire].raw_peak_ratio.mean()-bg[(dire,'raw_peak_ratio')] for dire in ['F','R']]),sd_index=None))
    table('results/molecular/S10_processing_sensitivity.csv',processing)
    complete=pairdf[pairdf.complete_pair]
    jsonout('results/molecular/S10_molecular_summary.json',dict(version=VERSION,read_n=len(target),eligible_reads=int(target.eligible.sum()),failed_reads=target.loc[~target.eligible,['read_id','failure_reasons']].to_dict('records'),complete_pairs=len(complete),independent_wells=len(w),raw_direction_bias=float(complete.raw_R_minus_F.mean()),raw_direction_RMSE=float(np.sqrt(np.mean(complete.raw_R_minus_F**2))),background_corrected_direction_bias=float(complete.corrected_R_minus_F.mean()),direction_correlation=float(complete.F_raw.corr(complete.R_raw)),backgrounds=bgrows,condition_summary=condition.to_dict('records'),validated_RNA_fractions=0,all_reads_byte_crosschecked=True))
    print('Sanger metrics:',len(target),'reads',int(target.eligible.sum()),'eligible;',len(w),'wells',flush=True)

if __name__=='__main__':run()
