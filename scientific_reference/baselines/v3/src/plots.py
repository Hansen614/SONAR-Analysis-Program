"""All diagnostic plots read exported tables; no hidden event processing."""
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/sonar_mpl')
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inventory import ROOT,write_csv,sha

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160,'svg.fonttype':'none'})
COL={'S7':'#236B8E','S10':'#B96A36','reporter':'#236B8E','blue_positive_reporter':'#7459A8','blue_negative_reporter':'#888888'}
def table(name):return pd.read_csv(ROOT/'results'/f'{name}.csv')
INDEX=[]
def save(fig,name,sources,caption):
    fig.tight_layout();fig.savefig(ROOT/'figures'/f'{name}.png');fig.savefig(ROOT/'figures'/f'{name}.svg');plt.close(fig)
    INDEX.append(dict(figure_id=name,source_tables=';'.join(sources),caption=caption,stage='analytical_diagnostic_not_final_Wiki',hashes=';'.join(sha(ROOT/s) for s in sources)))
def run():
    r=table('ras_results');ret=table('event_retention');bg=table('background_thresholds'); ev=pd.read_csv(ROOT/'figures/source_tables/event_display_subset.csv')
    fig,ax=plt.subplots(2,2,figsize=(10,8))
    for row,aid in enumerate(['S7_MOCK1','S7_MOCK2']):
        z=ev[ev.acquisition_id==aid]
        for col,(x,y) in enumerate([('FSC_A','SSC_A'),('FSC_H','FSC_A')]):
            for keep,c in [(False,'#b8b8b8'),(True,'#236B8E')]:
                q=z[z.singlet==keep];ax[row,col].scatter(np.log10(q[x]),np.log10(q[y]),s=3,color=c,alpha=.5,label='retained' if keep else 'excluded')
            ax[row,col].set(xlabel=f'log10 {x}',ylabel=f'log10 {y}',title=aid)
    ax[0,0].legend(markerscale=3)
    save(fig,'F01_control_gates',['figures/source_tables/event_display_subset.csv'],'MOCK1 supplies scatter/pulse gates; MOCK2 is a transfer acquisition. Scatter-selected singlets are not verified viable cells. Display subsampling does not affect scores.')
    fig,ax=plt.subplots(1,3,figsize=(12,3.5))
    for a,ch,col in zip(ax,['EGFP','mCherry','BFP'],['G','R','B']):
        for aid,c in [('S7_MOCK1','#236B8E'),('S7_MOCK2','#B96A36')]:
            z=ev[(ev.acquisition_id==aid)&ev.singlet][col];a.hist(z,bins=45,density=True,histtype='step',color=c,label=aid)
        a.axvline(bg[bg.channel==ch].used_threshold.iloc[0],color='black',ls='--',lw=1);a.set(xlabel=f'{ch} linear detector a.u.',ylabel='Density');a.set_xlim(left=-1000 if ch=='BFP' else 0)
    ax[0].legend(fontsize=8)
    save(fig,'F02_control_background',['figures/source_tables/event_display_subset.csv','results/background_thresholds.csv'],'Control distributions and provisional positivity thresholds. These Mock-only boundaries do not validate multicolor negative spread.')
    fig,ax=plt.subplots(2,1,figsize=(12,7),sharex=True);z=ret[~ret.acquisition_id.str.contains('MOCK')];pos=np.arange(len(z))
    ax[0].bar(pos,z.after_singlet/z.original*100,color=[COL[s] for s in z.series]);ax[0].set(ylabel='Retained singlets (%)')
    ax[1].bar(pos,z.reporter_selected,color=[COL[s] for s in z.series]);ax[1].set(ylabel='Reporter-selected events',xticks=pos,xticklabels=z.acquisition_id);ax[1].tick_params(axis='x',rotation=90,labelsize=8)
    save(fig,'F03_event_retention',['results/event_retention.csv'],'Uniform control-derived rules across all 32 experimental acquisitions; event counts are not biological replicate counts.')
    for series in ['S7','S10']:
        z=r[(r.series==series)&(r.population_mode=='reporter')];fig,ax=plt.subplots(1,3,figsize=(13,3.6))
        for a,metric,ylabel in zip(ax,['mean_G_raw','mean_G_corrected','ras'],['Mean raw EGFP (a.u.)','Mean corrected EGFP (a.u.)','Exploratory RAS (G/R)']):
            for lab,marker in [('A','o'),('B','s')]:
                zz=z[z.replicate_label==lab].sort_values('condition_label');a.plot(zz.condition_label,zz[metric],marker=marker,color=COL[series],ls='-' if lab=='A' else '--',label=lab,alpha=.8)
            a.set(xlabel='AC DNA mass fraction (%)' if series=='S7' else 'Reporter:editor DNA ratio 1:x',ylabel=ylabel)
        if series=='S7':
            for a in ax:
                a.set_xticks([0,5,15,20,30,40,50,75,90,100]);a.tick_params(axis='x',rotation=45,labelsize=8)
        ax[0].legend(title='Independent well');save(fig,f'F04_{series}_normalization',['results/ras_results.csv'],'Same reporter-selected events for all three metrics. A/B are user-confirmed independent transfection wells (n=2 per condition). S7 source label 10 is analyzed as confirmed 15% AC by DNA mass; lines are not calibration fits.')
    rep=table('repeatability');z=rep[rep.population_mode=='reporter'].pivot(index=['series','condition_label'],columns='metric',values='cv_percent').reset_index()
    fig,ax=plt.subplots(figsize=(6,5));mx=max(z.mean_G_raw.max(),z.ras.max())*1.1;ax.plot([0,mx],[0,mx],ls='--',color='gray')
    for series in ['S7','S10']:
        q=z[z.series==series];ax.scatter(q.mean_G_raw,q.ras,label=series,color=COL[series],s=40)
        for t in q.itertuples():
            if t.ras>t.mean_G_raw:
                offset={('S7',40.0):(9,-12),('S7',100.0):(7,17),('S10',0.5):(16,3)}[(series,t.condition_label)]
                ax.annotate(f'{series}: {t.condition_label:g}',(t.mean_G_raw,t.ras),xytext=offset,textcoords='offset points',fontsize=8,color=COL[series],arrowprops=dict(arrowstyle='-',lw=.5,color=COL[series]))
    ax.set(xlabel='A/B raw EGFP CV (%)',ylabel='A/B RAS CV (%)');ax.legend();save(fig,'F05_pair_dispersion',['results/repeatability.csv'],'All matched-label pairs are shown; labels mark conditions with higher RAS CV. CV = sample SD (ddof=1) / absolute mean x 100. This is within-experiment independent-transfection-well repeatability (n=2 per condition); independent culture/day replication is not established.')
    fig,ax=plt.subplots(1,2,figsize=(10,4));z=r[(r.series=='S10')&(r.population_mode=='reporter')]
    for lab,m in [('A','o'),('B','s')]:
        q=z[z.replicate_label==lab].sort_values('condition_label');ax[0].plot(q.condition_label,100*q.blue_positive_fraction_reporters,marker=m,label=lab)
    ax[0].set(xlabel='Reporter:editor DNA ratio 1:x',ylabel='B+ among reporter-selected events (%)');ax[0].legend()
    for mode in ['reporter','blue_positive_reporter','blue_negative_reporter']:
        q=r[(r.series=='S10')&(r.population_mode==mode)].groupby('condition_label').ras.mean();ax[1].plot(q.index,q,marker='o',label={'reporter':'Reporter population','blue_positive_reporter':'Editor co-expression (R+B+)','blue_negative_reporter':'Blue-negative reporter'}[mode],color=COL[mode])
    ax[1].set(xlabel='Reporter:editor DNA ratio 1:x',ylabel='Mean exploratory RAS');ax[1].legend(fontsize=8)
    save(fig,'F06_blue_dimension',['results/ras_results.csv'],'ORCA-P2A-BFP linkage is user-confirmed. At positive editor doses, R+B+ is an exploratory reporter/editor co-expression population; the multicolor B boundary remains provisional. The 1:0 blue tail is a negative-control diagnostic, not editor co-expression.')
    s=table('sensitivity');s=s.merge(r[['acquisition_id','population_mode','ras']],on=['acquisition_id','population_mode'],suffixes=('_alt','_primary'));s=s[(s.population_mode=='reporter')&~s.scenario.isin(['no_subtraction','control_median_NOT_expected_additive'])];s['pct']=100*(s.ras_alt/s.ras_primary-1)
    fig,ax=plt.subplots(figsize=(9,5));names=list(s.scenario.unique());ax.boxplot([s[s.scenario==n].pct.dropna() for n in names],vert=False,tick_labels=names,showfliers=True);ax.axvline(0,color='gray',ls='--');ax.set(xlabel='Change from primary reporter RAS (%)')
    save(fig,'F07_sensitivity',['results/sensitivity.csv','results/ras_results.csv'],'Predeclared gate, background and threshold perturbations across experimental acquisitions. Boxes describe sensitivity across conditions, not replicate uncertainty.')
    s=table('event_count_sensitivity');fig,ax=plt.subplots(1,2,figsize=(11,4))
    for a,series in zip(ax,['S7','S10']):
        z=s[(s.population_mode=='reporter')&s.acquisition_id.str.startswith(series+'_')]
        for aid,q in z.groupby('acquisition_id'):a.plot(q.sample_n,100*(q.q975-q.q025)/abs(q.full_ras),color=COL[series],alpha=.25)
        a.set(xscale='log',xlabel='Events sampled without replacement',ylabel='95% interval width / full RAS (%)',title=series)
    save(fig,'F08_event_count',['results/event_count_sensitivity.csv'],'100 subsamples at each supported event count. Uncertainty is conditional on one acquisition and shrinks to zero at the full finite sample; it is not biological uncertainty.')
    inf=table('high_expression_influence');fig,ax=plt.subplots(1,2,figsize=(11,4));z=inf[inf.population_mode=='reporter']
    for series in ['S7','S10']:
        q=z[z.acquisition_id.str.startswith(series+'_')];ax[0].scatter(q.top_one_percent_red_share*100,q.relative_change_without_top_one_percent*100,label=series,color=COL[series])
    ax[0].set(xlabel='Red signal from top 1% of red events (%)',ylabel='RAS change if removed (%)');ax[0].legend()
    rp=table('red_profiles')
    for aid,q in rp.groupby('acquisition_id'):ax[1].plot(q.center,q.ras,alpha=.3,color=COL[aid.split('_')[0]])
    ax[1].set(xscale='log',xlabel='Shared red-intensity bin (raw a.u.)',ylabel='Within-bin exploratory RAS')
    save(fig,'F09_reference_influence',['results/high_expression_influence.csv','results/red_profiles.csv'],'Bright events remain in the primary score. Red-bin dependence limits any assumption of perfect reporter-expression invariance.')
    b=table('blue_profiles');fig,ax=plt.subplots(1,2,figsize=(11,4))
    for aid,q in b.groupby('acquisition_id'):
        ax[0].plot(q.center,q.ras,marker='.',alpha=.6,label=aid.replace('S10_1_',''));ax[1].plot(q.center,q.n_selected,marker='.',alpha=.6)
    ax[0].set(xscale='log',xlabel='Common B+ intensity bin (raw a.u.)',ylabel='Within-bin RAS');ax[0].legend(ncol=2,fontsize=7)
    ax[1].set(xscale='log',yscale='log',xlabel='Common B+ intensity bin (raw a.u.)',ylabel='Selected events in bin')
    save(fig,'F10_blue_common_support',['results/blue_profiles.csv'],'Common B+ range is the intersection of within-acquisition 5th–95th percentiles for positive editor-ratio labels. Low-count bins remain unavailable; profiles do not establish active-editor abundance.')
    q=pd.read_csv(ROOT/'inventory/molecular_reads.csv');fig,ax=plt.subplots(1,2,figsize=(10,4))
    for dire,c in [('F','#236B8E'),('R','#B96A36')]:
        zz=q[q.direction==dire];ax[0].scatter(zz.called_bases,zz.Q20_bases,label=dire,color=c);ax[1].scatter(zz.reference_alignment_paired_bases,zz.reference_aligned_identity,label=dire,color=c)
    ax[0].set(xlabel='Called bases',ylabel='Bases with Phred >= 20');ax[0].legend();ax[1].set(xlabel='Bases aligned to general reporter design',ylabel='Identity in paired aligned columns')
    save(fig,'F11_molecular_audit',['inventory/molecular_reads.csv'],'48 AB1 reads / 24 molecular labels / 12 user-confirmed S10 parent wells. Labels 1/2 map to A and 3/4 to B; RNA was extracted after flow. General-design alignment is an identity lead, not exact OpenA or quantitative RNA-editing validation.')
    p=table('plate_summary');fig,ax=plt.subplots(1,2,figsize=(10,4))
    for a,kind in zip(ax,['S10_single_point','S10_spatial_scan']):
        q=p[(p.kind==kind)&(p.channel=='mCherry')];a.scatter(np.arange(len(q)),q.mean_RFU);a.axhline(0,color='gray',ls='--');a.set(xticks=np.arange(len(q)),xticklabels=q.sample_label,ylabel='mCherry RFU',title=kind.replace('_',' '));a.tick_params(axis='x',rotation=90)
        if kind=='S10_spatial_scan':a.axhline(p[(p.kind=='PBS_spatial_scan')&(p.channel=='mCherry')].mean_RFU.iloc[0],color='#B96A36',label='documented PBS A01');a.legend(fontsize=8)
    save(fig,'F12_plate_reference_signal',['results/plate_summary.csv'],'Single-point red fluorescence includes negative values. Spatial points are technical positions within a well. No validated plate RAS or flow-to-plate conversion is produced.')
    write_csv(ROOT/'figures/figure_index.csv',INDEX)
    print('Generated',len(INDEX),'diagnostic figures')

if __name__=='__main__':run()
