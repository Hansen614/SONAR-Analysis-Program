"""Scientific diagnostics from saved result tables only."""
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/sonar_layer23_mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np,pandas as pd
from layer23_common import *
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','savefig.dpi':160})
COL={'affine':'#237A9F','isotonic':'#BA6338','monotone_hinge_50':'#8063AE','F':'#237A9F','R':'#BA6338','C':'#237A9F','T':'#B96A36','A':'#3B8E60','G':'#7B62A5'}
def read(path):return pd.read_csv(ROOT/'results'/path)
def run(only=None):
    records=[]
    def save(fig,name,sources,caption):
        if only is not None and name not in only:
            plt.close(fig);return
        fig.tight_layout();fig.savefig(ROOT/'figures/layer23'/f'{name}.png');fig.savefig(ROOT/'figures/layer23'/f'{name}.svg');plt.close(fig)
        records.append(dict(figure_id=name,source_tables=';'.join(sources),source_sha256=';'.join(sha(ROOT/p) for p in sources),caption=caption,status='diagnostic_not_publication_or_assay_validation'))
    d=read('molecular/OpenA_reference_alignment.csv');summary=json.loads((ROOT/'results/molecular/OpenA_reconstruction_summary.json').read_text())
    fig,ax=plt.subplots(2,1,figsize=(11,5.5),gridspec_kw={'height_ratios':[2,1]})
    ax[0].step(d.position_1based,d.Q20_F_n,where='mid',label='Forward Q20',color=COL['F']);ax[0].step(d.position_1based,d.Q20_R_n,where='mid',label='Reverse Q20',color=COL['R']);ax[0].axvline(280,color='#674B8B',ls='--');ax[0].set(xlabel='Forward amplicon position (1-based)',ylabel='Supporting control reads',ylim=(-.1,4.5));ax[0].legend(loc='lower center',ncol=2)
    for lo,hi in [(1,14),(509,523)]:ax[0].axvspan(lo,hi,color='#999999',alpha=.2)
    a=summary['EGFP_segment_end_1based'];b=summary['DHFR_mapped_start_1based'];ax[1].broken_barh([(1,a-1)],(1,1),facecolors='#65A68D');ax[1].broken_barh([(a+1,b-a-1)],(1,1),facecolors='#DBC489');ax[1].broken_barh([(b,523-b)],(1,1),facecolors='#B2A3CE');ax[1].axvline(280,color='#674B8B',ls='--');ax[1].text(120,1.5,'EGFP segment',ha='center',va='center');ax[1].text(410,1.5,'DHFR segment',ha='center',va='center');ax[1].annotate('C280: CGA → TGA',(280,2),(280,3.1),ha='center',arrowprops={'arrowstyle':'->'});ax[1].set(xlim=(0,524),ylim=(0,3.7),yticks=[],xlabel='Reconstructed architecture; intended target remains provisional')
    save(fig,'L23_01_reference_support',['results/molecular/OpenA_reference_alignment.csv','results/molecular/OpenA_reconstruction_summary.json'],'Four independent molecular-label assemblies across two wells agree at 523 bp. Q20-trimmed evidence supports 494 bases, of which 393 have both directions. Grey terminals lack accepted Q20 support and use recorded primers. C280 is the unique linker stop-gain candidate.')
    trace=read('molecular/S10_chromatogram_plot_points.csv');metrics=read('molecular/S10_read_level_peak_metrics.csv')
    for name,labels,caption in [('L23_02_bidirectional_traces',['1-0-1','1-8-1'],'Raw processed ABI traces at aligned candidate C280 in no-editor and 1:8 samples. F uses C/T and R uses G/A. Signal amplitudes remain direction-specific; no editing percentage is inferred.'),('L23_03_flagged_read',['1-8-1','1-8-2'],'The flagged 1-8-2.F trace has only 60% matching flanking positions at the putative target. Its site statistic is excluded by the declared flank-identity screen, while its original trace and reverse read remain available.')]:
        fig,ax=plt.subplots(2,2,figsize=(12,6.8))
        for col,label in enumerate(labels):
            for row,dire in enumerate(['F','R']):
                z=trace[(trace.sample_label==label)&(trace.direction==dire)].sort_values('relative_forward_base_distance');a=ax[row,col]
                for base in 'ACGT':a.plot(z.relative_forward_base_distance,z[base],label=base,color=COL[base],lw=1.2)
                a.axvline(0,color='black',ls='--',lw=.8);a.set(xlim=(-6,6),xlabel='Distance from mapped C280 (forward-base units)',ylabel='Processed signal (a.u.)',title=f'{label} {dire}')
                m=metrics[(metrics.sample_label==label)&(metrics.direction==dire)].iloc[0]
                a.text(.02,.93,'Eligible' if m.eligible else 'Failed local alignment QC',transform=a.transAxes,va='top',fontsize=9)
        ax[0,1].legend(ncol=4,loc='upper right',fontsize=8)
        save(fig,name,['results/molecular/S10_chromatogram_plot_points.csv','results/molecular/S10_read_level_peak_metrics.csv'],caption)
    w=read('molecular/S10_well_level_molecular_results.csv');fig,ax=plt.subplots(1,3,figsize=(13,4))
    for a,field,ylabel in zip(ax,['F_raw_mean','R_raw_mean','signal_index'],['Forward T / (C + T)','Reverse A / (G + A)','Background-corrected signal index']):
        for lab,marker in [('A','o'),('B','s')]:
            z=w[w.well_id.str.endswith('_'+lab+'_well')].sort_values('dose_ratio');a.plot(z.dose_ratio,z[field],marker=marker,label=lab,ls='-' if lab=='A' else '--')
        a.set(xlabel='Editor:reporter DNA mass ratio',ylabel=ylabel)
    ax[0].legend(title='Independent well');save(fig,'L23_04_molecular_response',['results/molecular/S10_well_level_molecular_results.csv'],'Twelve wells, n=2 per dose. Directional summaries retain eligible reads; the combined index uses only complete F/R molecular-label pairs. The index is not an edited-RNA fraction. One high-dose well has only one complete pair.')
    p=read('molecular/S10_bidirectional_concordance.csv');p=p[p.complete_pair];fig,ax=plt.subplots(1,2,figsize=(10,4))
    sc=ax[0].scatter(p.F_raw,p.R_raw,c=p.dose_ratio,cmap='viridis',s=42);mx=max(p.F_raw.max(),p.R_raw.max());ax[0].plot([0,mx],[0,mx],ls='--',color='gray');ax[0].set(xlabel='Forward alternative peak ratio',ylabel='Reverse alternative peak ratio')
    ax[1].scatter((p.F_raw+p.R_raw)/2,p.raw_R_minus_F,c=p.dose_ratio,cmap='viridis',s=42);ax[1].axhline(0,color='gray',ls='--');ax[1].set(xlabel='Mean of direction ratios',ylabel='Reverse minus forward');fig.colorbar(sc,ax=ax[1],label='Editor:reporter ratio')
    save(fig,'L23_05_direction_agreement',['results/molecular/S10_bidirectional_concordance.csv'],'Twenty-three complete technical F/R pairs are grouped within 12 independent wells. Direction bias grows with signal; correlation alone does not establish quantitative agreement.')
    b=read('molecular/S10_bystander_site_analysis.csv');fig,ax=plt.subplots(figsize=(7,5));ax.scatter(b.F_high_minus_control,b.R_high_minus_control,s=20,color='#999999',alpha=.7)
    for pos in [280,224,305,187]:
        z=b[b.position_1based==pos].iloc[0];ax.scatter(z.F_high_minus_control,z.R_high_minus_control,color='#B96A36' if pos==280 else '#237A9F',s=45);ax.annotate(f'C{pos}',(z.F_high_minus_control,z.R_high_minus_control),(6,6),textcoords='offset points')
    ax.axhline(0,color='gray',lw=.6);ax.axvline(0,color='gray',lw=.6);ax.set(xlabel='Forward: 1:8 minus 1:0 peak ratio',ylabel='Reverse: 1:8 minus 1:0 peak ratio')
    save(fig,'L23_06_cytidine_screen',['results/molecular/S10_bystander_site_analysis.csv'],'All covered cytidines are screened descriptively. Other dose-associated secondary peaks exist; these are candidate bystander/technical signatures, not validated edits or multiplicity-controlled discoveries. C280 was selected by linker/codon evidence, not this ranking.')
    points=read('calibration/S7_calibration_predictions.csv');curves=read('calibration/S7_calibration_curves.csv');fig,ax=plt.subplots(1,3,figsize=(13,4),sharey=True)
    for a,name in zip(ax,['affine','isotonic','monotone_hinge_50']):
        z=points[points.model==name];c=curves[curves.model==name];a.scatter(z.AC_mass_fraction*100,z.observed_RAS,color='#333333',s=24);a.plot(c.AC_mass_fraction*100,c.predicted_RAS,color=COL[name]);a.fill_between(c.AC_mass_fraction*100,c.bootstrap_mean_low,c.bootstrap_mean_high,color=COL[name],alpha=.2);a.set(xlabel='AC DNA mass (%)',ylabel='RAS',title=name.replace('_',' '))
    save(fig,'L23_07_S7_models',['results/calibration/S7_calibration_predictions.csv','results/calibration/S7_calibration_curves.csv'],'Twenty independent S7 transfection wells, two per mass fraction. Three prespecified low-complexity fits; shaded bands show within-level well/event bootstrap mean uncertainty, not external calibration accuracy.')
    fig,ax=plt.subplots(1,3,figsize=(13,3.8),sharey=True)
    for a,name in zip(ax,['affine','isotonic','monotone_hinge_50']):
        z=points[points.model==name];a.scatter(z.AC_mass_fraction*100,z.residual,color=COL[name]);a.axhline(0,color='gray',ls='--');a.set(xlabel='AC DNA mass (%)',ylabel='Observed − fitted RAS',title=name.replace('_',' '))
    save(fig,'L23_08_S7_residuals',['results/calibration/S7_calibration_predictions.csv'],'Original 75%, 90% and 100% references remain in all fits. Residual structure is not removed by relabeling, gate tuning or deleting inconvenient levels.')
    inv=read('calibration/S7_inverse_identifiability.csv');fig,ax=plt.subplots(1,3,figsize=(13,4),sharey=True)
    for a,name in zip(ax,['affine','isotonic','monotone_hinge_50']):
        z=inv[inv.model==name].sort_values('RAS');a.fill_between(z.RAS,z.diagnostic_compatible_mass_low*100,z.diagnostic_compatible_mass_high*100,color=COL[name],alpha=.2);a.plot(z.RAS,z.exact_inverse_point*100,color=COL[name]);p=z[z.exact_inverse_status=='NON_IDENTIFIABLE_PLATEAU'];a.vlines(p.RAS,p.exact_inverse_low*100,p.exact_inverse_high*100,color='black',lw=3);a.set(xlabel='RAS',ylabel='Compatible AC DNA mass (%)',title=name.replace('_',' '),ylim=(-3,103))
    save(fig,'L23_09_inverse_uncertainty',['results/calibration/S7_inverse_identifiability.csv'],'Curves are model-specific inverses; black segments are nonunique isotonic plateaus. Shading adds internally observed discrepancy to bootstrap mean bands. It is an exploratory compatibility set, not a validated 95% RES interval. Values beyond fitted response range are not clipped.')
    a=read('calibration/S7_anomaly_well_diagnostics.csv');fig,ax=plt.subplots(2,3,figsize=(12,7.4))
    for panel,col,ylabel in zip(ax[0],['mean_G_corrected','mean_R_corrected','ras'],['Corrected EGFP mean (a.u.)','Corrected mCherry mean (a.u.)','RAS']):
        for lab,m in [('A','o'),('B','s')]:
            z=a[a.replicate_label==lab].sort_values('condition_label');panel.plot(z.condition_label,z[col],marker=m,label=lab)
        panel.set(xlabel='AC DNA mass (%)',ylabel=ylabel)
    ax[0,0].legend(title='Well');hist=read('calibration/S7_anomaly_distributions.csv');colors={75:'#237A9F',90:'#A85559',100:'#58856F'}
    for panel,ch in zip(ax[1,:2],['EGFP','mCherry']):
        for (dose,rep),z in hist[hist.channel==ch].groupby(['condition_label','replicate_label']):
            z=z.dropna(subset=['log10_left','log10_right']);panel.step((z.log10_left+z.log10_right)/2,z.fraction,where='mid',color=colors[dose],ls='-' if rep=='A' else '--',label=f'{int(dose)}% {rep}',lw=1.2)
        panel.set(xlabel=f'log10 raw {ch} (a.u.)',ylabel='Selected events / total',xlim=(2,6.5))
    ax[1,0].legend(fontsize=7,ncol=2)
    for rep,m in [('A','o'),('B','s')]:
        z=a[a.replicate_label==rep].sort_values('condition_label');ax[1,2].plot(z.condition_label,z.n_selected,marker=m,label=rep)
    ax[1,2].set(xlabel='AC DNA mass (%)',ylabel='Reporter-selected events')
    save(fig,'L23_10_reference_anomaly',['results/calibration/S7_anomaly_well_diagnostics.csv','results/calibration/S7_anomaly_distributions.csv'],'Team-corrected 75%/90% labels are used. The former reversal disappears, while 90% and 100% RAS remain close. Lower panels show unchanged original reporter-gated event distributions assigned to corrected AC levels. Improved model agreement does not independently verify retrospective labels.')
    p=read('prediction/S10_flow_molecular_pairs.csv');fig,ax=plt.subplots(1,3,figsize=(13,4))
    for a,col,xlabel in zip(ax,['RAS_reporter','blue_positive_fraction_reporters','RAS_editor_coexpression'],['Reporter-population RAS','B+ fraction among reporter events','Co-expression RAS']):
        z=p[[col,'raw_signal_index','condition_label']].dropna();sc=a.scatter(z[col],z.raw_signal_index,c=z.condition_label,cmap='viridis',s=42);a.set(xlabel=xlabel,ylabel='Raw chromatogram signal index')
    fig.colorbar(sc,ax=ax[-1],label='Editor:reporter ratio');save(fig,'L23_11_flow_molecular_association',['results/prediction/S10_flow_molecular_pairs.csv'],'Each point is one independent well; 12 reporter/B-fraction pairs and 10 defined co-expression pairs. Molecular population is undocumented. Index association is not RNA-editing accuracy or causality.')
    v=read('prediction/S10_prediction_validation.csv');fig,ax=plt.subplots(1,3,figsize=(13,4),sharex=True,sharey=True)
    for a,name in zip(ax,['training_mean','reporter_RAS','B_detection_fraction']):
        z=v[(v.model==name)&(v.validation=='leave_one_dose_out')];a.errorbar(z.observed_signal,z.predicted_signal,yerr=np.vstack([z.predicted_signal-z.prediction_low,z.prediction_high-z.predicted_signal]),fmt='o',ms=4,capsize=2,color='#237A9F',alpha=.8);a.plot([0,.3],[0,.3],color='gray',ls='--');a.set(xlabel='Held-out measured signal index',ylabel='Predicted signal index',title=name.replace('_',' '))
    save(fig,'L23_12_internal_prediction',['results/prediction/S10_prediction_validation.csv'],'Leave-one-dose-out predictions keep all reads from each well together. Error bars are model-based OLS t prediction intervals. Response is raw peak-composition index, not RNA editing; staged biological PER is unavailable. Direct RAS does not beat the training-mean baseline.')
    if only is not None:
        prior=pd.read_csv(ROOT/'figures/layer23/figure_index.csv');prior=prior[~prior.figure_id.isin(only)];records=pd.concat([prior,pd.DataFrame(records)],ignore_index=True).sort_values('figure_id')
    table('figures/layer23/figure_index.csv',records)
    print('Layer23 diagnostics:',len(records),flush=True)

if __name__=='__main__':run()
