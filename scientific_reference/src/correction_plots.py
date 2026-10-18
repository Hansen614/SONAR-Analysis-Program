"""Regenerate corrected-axis figures only; retain all unaffected figure bytes."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from layer23_common import *
from layer23_plots import run as update_calibration_plots,COL

def run():
    out=ROOT/'figures/correction';out.mkdir(exist_ok=True)
    update_calibration_plots(only=['L23_07_S7_models','L23_08_S7_residuals','L23_09_inverse_uncertainty','L23_10_reference_anomaly'])
    records=[]
    def save(fig,name,sources,caption,folder=out):
        fig.tight_layout();fig.savefig(folder/f'{name}.png');fig.savefig(folder/f'{name}.svg');plt.close(fig)
        records.append(dict(figure_id=name,source_tables=';'.join(sources),source_sha256=';'.join(sha(ROOT/p) for p in sources),caption=caption,status='CORRECTED_PRIMARY_EXPLORATORY_RETROSPECTIVE_LABELS',folder=str(folder.relative_to(ROOT))))
    s=pd.read_csv(ROOT/'results/calibration/S7_reference_response_corrected.csv')
    fig,ax=plt.subplots(1,3,figsize=(13,3.6))
    for a,metric,label in zip(ax,['mean_G_raw','mean_G_corrected','ras'],['Mean raw EGFP (a.u.)','Mean corrected EGFP (a.u.)','Exploratory RAS (G/R)']):
        for rep,marker in [('A','o'),('B','s')]:
            z=s[s.replicate_label==rep].sort_values('corrected_ac_mass_fraction');a.plot(100*z.corrected_ac_mass_fraction,z[metric],marker=marker,color='#236B8E',ls='-' if rep=='A' else '--',label=rep,alpha=.8)
        a.set(xlabel='Corrected AC DNA mass (%)',ylabel=label,xticks=[0,5,15,20,30,40,50,75,90,100]);a.tick_params(axis='x',rotation=45,labelsize=8)
    ax[0].legend(title='Independent well');save(fig,'F04_S7_normalization',['results/calibration/S7_reference_response_corrected.csv'],'Original event means and RAS under team-corrected 75/90 identities; prior 10-to-15 correction retained. n=2 wells/level. Lines are descriptive, not fits.',ROOT/'figures')
    idx=pd.read_csv(ROOT/'figures/figure_index.csv');idx.loc[idx.figure_id=='F04_S7_normalization',['source_tables','caption','hashes']]=[records[0]['source_tables'],records[0]['caption'],records[0]['source_sha256']];table('figures/figure_index.csv',idx)
    fig,ax=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for a,col,title in zip(ax,['pre_correction_ac_mass_fraction','corrected_ac_mass_fraction'],['Original v3 interpretation','Team-corrected primary interpretation']):
        for rep,mark in [('A','o'),('B','s')]:
            z=s[s.replicate_label==rep].sort_values(col);a.errorbar(100*z[col],z.ras,yerr=np.vstack([z.ras-z.event_control_ci_low,z.event_control_ci_high-z.ras]),fmt=mark+'-',ms=5,lw=1,label=rep)
        a.set(xlabel='AC DNA mass (%)',ylabel='Unchanged reporter RAS',title=title);a.axvspan(75,90,color='#d9c8e8',alpha=.2)
    ax[0].legend(title='Independent well');save(fig,'C01_original_corrected_response',['results/calibration/S7_reference_response_corrected.csv'],'Identical 20 RAS values and event/control intervals before and after four label assignments. The remaining variation between independent wells is not represented by the narrow event-only intervals. Correction is retrospective and not independently proven.')
    comp=pd.read_csv(ROOT/'results/calibration/S7_before_after_model_comparison.csv');z=comp[comp.validation=='leave_one_reference_level_out'];fig,ax=plt.subplots(1,2,figsize=(11,4));pos=np.arange(len(z))
    for i,(col,label) in enumerate([('RAS_RMSE','Leave-level RMSE (RAS units)'),('training_R2','Training R²')]):
        ax[i].bar(pos-.18,z[col+'_original'],.36,label='Original',color='#a8b2bd');ax[i].bar(pos+.18,z[col+'_corrected'],.36,label='Corrected',color='#327c9e');ax[i].set(xticks=pos,xticklabels=['Affine','Isotonic','50% hinge'],ylabel=label)
    ax[0].legend();save(fig,'C02_model_comparison',['results/calibration/S7_before_after_model_comparison.csv'],'All three models use identical fitting policies and 20 independent wells. Leave-level forward errors score the same 16 in-range held-out wells; omitted endpoints are unavailable. Improvement describes model agreement, not proof of transposition.')
    q=pd.read_csv(ROOT/'results/calibration/S7_cross_model_inverse_support.csv');local=pd.read_csv(ROOT/'results/calibration/S7_local_inverse_resolution.csv');fig,ax=plt.subplots(1,2,figsize=(12,4))
    for name in ['isotonic','monotone_hinge_50']:
        z=local[local.model==name];ax[0].plot(100*z.nominal_AC_mass_fraction,z.local_slope_RAS_per_mass_fraction,label=name.replace('_',' '),color=COL[name])
    ax[0].set(xlabel='Corrected AC DNA mass (%)',ylabel='Local slope: RAS per unit mass fraction');ax[0].legend(fontsize=8)
    ax[1].fill_between(q.RAS,100*q.union_compatible_low,100*q.union_compatible_high,color='#a4bbc6',alpha=.5,label='Union of two model envelopes')
    for col,name in [('isotonic_point','isotonic'),('hinge_point','monotone_hinge_50')]:ax[1].plot(q.RAS,100*q[col],color=COL[name],label=name.replace('_',' '))
    ranges=pd.read_csv(ROOT/'results/calibration/S7_cross_model_supported_ranges.csv')
    if len(ranges):
        largest=ranges.iloc[np.argmax(ranges.RAS_high-ranges.RAS_low)];ax[1].axvspan(largest.RAS_low,largest.RAS_high,color='#70a483',alpha=.22,label='Largest contiguous narrow diagnostic')
    ax[1].set(xlabel='RAS',ylabel='Conditional AC mass equivalent (%)',ylim=(-2,102));ax[1].legend(fontsize=7)
    save(fig,'C03_cross_model_inverse_support',['results/calibration/S7_cross_model_inverse_support.csv','results/calibration/S7_local_inverse_resolution.csv','results/calibration/S7_cross_model_supported_ranges.csv'],'Zero isotonic slopes reveal nonunique regions. The union of isotonic/hinge discrepancy envelopes must be <=20 AC percentage points and untruncated by boundaries. Green marks the largest contiguous supported grid segment; isolated boundary-grid points do not expand it. It is not a validated confidence interval or external accuracy claim.')
    m=pd.read_csv(ROOT/'results/calibration/S10_hypothetical_S7_mapping.csv');fig,ax=plt.subplots(1,3,figsize=(12,4),sharey=True)
    for a,name in zip(ax,['affine','isotonic','monotone_hinge_50']):
        z=m[m.model==name].sort_values('RAS');a.vlines(z.RAS,100*z.diagnostic_compatible_mass_low,100*z.diagnostic_compatible_mass_high,color=COL[name],alpha=.6);a.scatter(z.RAS,100*z.hypothetical_S7_mass_equivalent,color=COL[name],s=20);a.set(xlabel='S10 reporter-population RAS',ylabel='Hypothetical S7 mass equivalent (%)',title=name.replace('_',' '))
    save(fig,'C04_S10_unqualified_mapping',['results/calibration/S10_hypothetical_S7_mapping.csv'],'Conditional arithmetic sensitivity only. S7/S10 transfer remains unsupported; molecular population is unknown. These values are not validated S10 RES or RNA fractions. Vertical spans are exploratory compatibility envelopes.')
    table('figures/correction/figure_index.csv',records)
    print('Updated 5 affected figures and created 4 correction diagnostics',flush=True)

if __name__=='__main__':run()
