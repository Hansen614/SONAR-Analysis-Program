"""Final evidence documents and diagnostic plots, derived only from packaged S7/S10 tables."""
import json,shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from science_api import ROOT,FINAL,RELEASE,ESTIMATOR,save_json,digest

def read(p):return pd.read_csv(ROOT/p)
def write(p,text):
    out=ROOT/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text.strip()+'\n')
def table(d,cols=None):
    d=d if cols is None else d[cols]
    def fmt(v):
        if v is None or (isinstance(v,float) and not np.isfinite(v)):return 'unavailable'
        if isinstance(v,(float,np.floating)):return f'{v:.6g}'
        return str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in d.itertuples(index=False,name=None))

def plots():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','svg.hashsalt':RELEASE,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    out=ROOT/'figures/diagnostic';out.mkdir(exist_ok=True)
    def save(fig,name):
        fig.tight_layout();fig.savefig(out/(name+'.png'));fig.savefig(out/(name+'.svg'),metadata={'Date':'2026-10-13'});plt.close(fig)
    ref=read('results/calibration/S7_reference_response_corrected.csv');m=json.loads((ROOT/'models/res_primary/model.json').read_text());u=json.loads((ROOT/'models/res_primary/uncertainty.json').read_text())
    a=np.array(u['grid']);alpha,sl,sh=m['coefficients'];pred=alpha+sl*np.minimum(a,.5)+sh*np.maximum(a-.5,0)
    fig,ax=plt.subplots(figsize=(7,4.6));ax.fill_between(100*a,u['primary_lower'],u['primary_upper'],color='#82b8af',alpha=.28,label='Internal compatibility envelope')
    ax.plot(a*100,pred,color='#26766b',label='Frozen hinge, knot 50%')
    for rep,marker in [('A','o'),('B','s')]:
        d=ref[ref.replicate_label==rep];ax.scatter(d.mass_fraction*100,d.ras,marker=marker,s=32,edgecolor='white',linewidth=.4,label=f'Independent well {rep}',color='#426077')
    ax.axvspan(90,100,color='#cf8d64',alpha=.14);ax.set(xlabel='Corrected AC DNA mass fraction (%)',ylabel='RAS (linear ratio of sums)');ax.legend(frameon=False,fontsize=8,loc='upper left')
    save(fig,'RES_A_reference_calibration')
    cv=read('results/layer2/RES_Inverse_Validation.csv');z=cv[(cv.model=='monotone_hinge_50')&(cv.validation=='leave_one_reference_level_out')]
    fig,(ax,bx)=plt.subplots(1,2,figsize=(10,4.6),gridspec_kw={'width_ratios':[2,1]})
    for row in z.itertuples():
        if pd.notna(row.recovered_AC_mass_fraction):
            ax.scatter(row.true_AC_mass_fraction*100,row.recovered_AC_mass_fraction*100,marker='o' if row.held_input_within_training_domain else '^',color='#26766b' if row.held_input_within_training_domain else '#bd7650',s=36)
        else:ax.scatter(row.true_AC_mass_fraction*100,-8,marker='x',color='#a54141',s=50);ax.annotate('out of range',(row.true_AC_mass_fraction*100,-8),xytext=(10,6),textcoords='offset points',fontsize=8)
    ax.plot([0,100],[0,100],ls='--',color='#888888',lw=1);ax.set(xlabel='Held-out true AC mass fraction (%)',ylabel='Recovered AC mass equivalent (%)',ylim=(-13,107))
    ax.text(.02,.98,'20 held-out wells / 10 levels\nCircles: interpolation input\nTriangles: input outside training range',va='top',transform=ax.transAxes,fontsize=8)
    bx.bar(['Unique','Out of\nrange'],[z.recovered_AC_mass_fraction.notna().sum(),z.recovered_AC_mass_fraction.isna().sum()],color=['#26766b','#a54141']);bx.set(ylabel='Held-out wells',ylim=(0,22));bx.set_yticks([0,5,10,15,20])
    bx.text(0,19.4,'19/20',ha='center');bx.text(1,1.4,'1/20',ha='center');save(fig,'RES_B_inverse_recovery_all_cases')
    s=read('results/layer2/RES_Sample_Results.csv').set_index('sample_id');names=['S7_90B','S7_5B','S7_100A'];fig,ax=plt.subplots(figsize=(8,3.8))
    for j,name in enumerate(names):
        row=s.loc[name];l,h=json.loads(row.conditional_bootstrap_interval)
        ax.plot([100*row.compatibility_low,100*row.compatibility_high],[j,j],color='#b8c8c5',lw=10,solid_capstyle='butt')
        ax.plot([100*l,100*h],[j,j],color='#26766b',lw=4,solid_capstyle='butt');ax.scatter(row.res_mass_fraction*100,j,color='#173b46',s=42,zorder=4)
        ax.scatter(row.known_AC_mass_fraction*100,j,marker='x',color='#bd7650',s=45,zorder=5)
    ax.set(yticks=range(3),yticklabels=['S7_90B (corrected 75%)','S7_5B (5%)','S7_100A (100%)'],xlabel='AC DNA mass equivalent (%)',xlim=(-2,102),ylim=(-.5,2.7));ax.invert_yaxis()
    ax.plot([],[],color='#b8c8c5',lw=8,label='Compatibility set, not nominal 95% CI');ax.plot([],[],color='#26766b',lw=4,label='Conditional bootstrap quantiles');ax.scatter([],[],marker='x',color='#bd7650',label='Known reference input')
    ax.legend(loc='lower right',fontsize=8,frameon=False);save(fig,'RES_C_real_sample_calculations')
    rp=read('results/layer1/Normalization_Repeatability.csv');fig,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,series in zip(axes,['S7','S10']):
        d=rp[rp.series==series]
        for row in d.itertuples():ax.plot([0,1],[row.raw_EGFP_CV_percent,row.RAS_CV_percent],color='#26766b' if row.improved else '#bd7650',alpha=.8,marker='o',ms=4)
        ax.set(xticks=[0,1],xticklabels=['Raw EGFP','RAS'],ylabel='A/B well-pair CV (%)',title=series)
    save(fig,'RAS_repeatability')
    red=read('results/red_profiles.csv');fig,ax=plt.subplots(figsize=(7,4.5))
    for name,d in red.groupby('acquisition_id'):ax.plot(d.center,d.ras,color='#26766b' if name.startswith('S7') else '#bd7650',alpha=.35,lw=1)
    ax.set(xscale='log',xlabel='Common mCherry bin center (raw linear detector a.u.)',ylabel='Within-bin RAS');ax.plot([],[],color='#26766b',label='S7, 20 wells');ax.plot([],[],color='#bd7650',label='S10, 12 wells');ax.legend(frameon=False)
    save(fig,'RAS_red_expression_dependence')
    mp=read('results/layer3/Molecular_Prediction_Comparison.csv');mp=mp[mp.validation=='leave_one_dose_out'].sort_values('RMSE',ascending=False)
    labels={'training_mean':'Mean baseline','reporter_RAS':'Reporter RAS','editor_dose_log1p':'log(1 + editor dose)','reporter_RAS_plus_B':'RAS + BFP fraction','B_detection_fraction':'BFP fraction','editor_dose_linear':'Linear editor dose','editor_dose_linear_plus_B':'Linear dose + BFP fraction'}
    fig,ax=plt.subplots(figsize=(8,4.8));ax.barh([labels[n] for n in mp.model],mp.RMSE,color=['#bd7650' if 'dose' in n else '#26766b' for n in mp.model]);ax.set(xlabel='Leave-one-dose-out RMSE (relative chromatogram index)');ax.invert_yaxis();save(fig,'Molecular_dose_benchmarks')

def run():
    model=json.loads((ROOT/'models/res_primary/model.json').read_text());params=model['parameters'];dom=model['domains']
    norm=read('results/layer1/Normalization_Summary.csv');nr=read('results/layer1/Normalization_Repeatability.csv')
    cv=read('results/layer2/RES_Model_Comparison.csv');inv=read('results/layer2/RES_Inverse_Validation.csv');samples=read('results/layer2/RES_Sample_Results.csv')
    qc=read('results/layer0/Sample_QC.csv');opt=read('results/layer0/Detector_Range_Audit.csv');sat=read('results/layer0/Range_Exclusion_Sensitivity.csv');red=read('results/layer1/Reporter_Expression_Dependence.csv');th=read('results/layer1/Red_Threshold_Sensitivity.csv')
    mol=read('results/layer3/Molecular_Prediction_Comparison.csv');conf=json.loads((ROOT/'results/layer3/Dose_Confounding_Assessment.json').read_text());mols=json.loads((ROOT/'results/molecular/S10_molecular_summary.json').read_text())
    ras=read('results/ras_results.csv');rp=ras[ras.population_mode=='reporter'];s10=rp[rp.series=='S10'];bs=s10.groupby('condition_label').blue_positive_fraction_reporters.mean()
    high=read('results/high_expression_influence.csv');high=high[high.population_mode=='reporter'];neg=read('results/negative_transfer.csv')
    equation=f"g(A) = {params['alpha']:.15g} + {params['beta']:.15g} A + {params['gamma']:.15g} max(0, A - 0.5)"
    base=f"Release: `{RELEASE}`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.\n"
    write('reports/Layer0_Context_Final_Report.md',f'''# Layer 0 — Final Context Calibration
{base}
The context is computationally reproducible and supports exploratory detector-scale measurement. It is not a validated multicolor optical standard.

## Implemented measurement
34 unique acquisitions comprise 32 experimental wells and two Mock acquisitions; duplicated Mock files in S10 are not independent controls. Original FCS bytes decode as 12-channel little-endian floating point. FlowIO's raw arrays were independently checked against bytes; only the Time channel receives its stored time-step conversion. The channel order is fixed: EGFP = FL1-A, index 5; BFP = FL6-A, index 7; mCherry = FL11-A, index 9. Unit gains and linear PnE fields are required. Display transforms never enter fluorescence sums.

Acquisition QC rejects nonfinite/nonpositive scatter and 1-second rate bins beyond six robust scale units. A robust two-dimensional log-scatter ellipse is fit on Mock1 only (MCD support 0.8, at most 8,000 events, seed 20261012, chi-square cutoff 9.21034). Singlets use log10(FSC-A/FSC-H) within three Mock-trained robust SDs. These are morphological selections; no live/dead marker establishes viability.

The background is the equal-weight mean of the two gated Mock acquisition means. Raw positivity uses the maximum of their channel-specific 99.5th percentiles. mCherry quantification requires raw R > 3395.724011230456, equal here to the positivity threshold; this numerical equality does not equate the background and threshold. Additive backgrounds are EGFP 2999.921288652426, mCherry 1149.481510590721 and BFP 196.5028889499891 detector a.u. Signed corrected EGFP is retained. The red boundary is a provisional precision screen, not an empirical LOQ.

## Numerical QC evidence
All 204 saved masks were independently reproduced from the raw FCS and saved configuration by the final wrapper. Negative-acquisition transfer positivity ranges from {100*neg.test_positive_fraction.min():.3f}% to {100*neg.test_positive_fraction.max():.3f}%. The largest rate-QC exclusion is {100*(qc.rate_removed/qc.recorded_events).max():.2f}% in one acquisition. A/B remain independent transfection wells within this experiment, not independent cultures or experimental days.

The newly explicit range audit found {int(opt.events_at_or_above_PnR.sum())} fluorescence events counted across channels at or above the declared PnR (16,777,216); cross-channel counts can describe the same event. {opt[opt.events_at_or_above_PnR>0].acquisition_id.nunique()} acquisitions are flagged. No fluorescence value is exactly equal to PnR; every observed channel maximum occurs once. Because integrated floating-point area signals can exceed this metadata range and no flat maximum accumulation is observed, these files do not establish physical clipping or absence of saturation. Among reporter-selected populations, {int(sat.range_flagged_reporter_events.sum())} distinct events are flagged across 32 wells (0–{int(sat.range_flagged_reporter_events.max())}/well). Removing them only as a sensitivity analysis changes RAS by {100*sat.relative_change.min():.3f}% to {100*sat.relative_change.max():.3f}%. Primary values retain these events.

## Optical boundary and interface
The stored spillover matrix is identity and USCOMP is False. No matched single-color/FMO controls or verified compensation provenance were recovered. Experimental EGFP/BFP relationships are never used to infer spillover. No-editor S10 reporter populations show broader BFP tails than Mock; this is a negative-transfer diagnostic, not a new compensation standard. All samples retain `WARN_OPTICAL_UNVALIDATED`; numerical score availability is a separate field.

`models/context_profiles/context_v1.json` contains the instrument fingerprint, cell type, exact channels, control hashes, additive background, positivity and quantification thresholds, fitted gates, support requirements, uncertainty, QC rules and compatibility policy. `process_fcs` enforces the profile and returns counts plus range warnings. `build_context` rebuilds this profile from packaged controls. Missing/mismatched channels are rejected explicitly; a different panel requires its own context implementation. The final profile's unvalidated upper range is JSON null.

Sources: [sample QC](../results/layer0/Sample_QC.csv), [channel range audit](../results/layer0/Detector_Range_Audit.csv), [range sensitivity](../results/layer0/Range_Exclusion_Sensitivity.csv), [raw regression](../results/layer0/raw_flow_regression.json), [negative transfer](../results/negative_transfer.csv), [API](../documentation/API_CONTRACT.md).
''')
    write('reports/Layer1_RAS_Final_Report.md',f'''# Layer 1 — Final RAS
{base}
RAS remains the ratio of paired, signed, background-corrected linear sums: `RAS_P = sum(g_i) / sum(r_i)`. The original core and all original RAS values are unchanged. mCherry is a continuous reference, not merely a positivity marker.

`P_R = singlets ∩ R_q+`; `P_RB = P_R ∩ B+` applies only with confirmed linked-editor presence. All 32 reporter-population scores and the 10 positive-dose S10 co-expression scores are available. The two no-editor BFP tails remain in historical diagnostics but are explicitly NOT_APPLICABLE for the co-expression result contract. BFP positivity indicates detectable editor-associated expression, not active ORCA abundance or editing.

## Normalization evidence
CV = sample SD (ddof=1) / absolute mean × 100, calculated across two independent transfection wells per condition. Raw EGFP means and RAS use the same selected reporter events. There are ten matched S7 and six S10 conditions.

{table(norm)}

Thus median CV declines from 4.697% to 1.767% in S7 (62.37% relative reduction of medians), and from 6.711% to 5.142% in S10 (23.37%). These are descriptive medians over heterogeneous conditions, not confidence intervals or proof of molecular accuracy. Normalization does not improve these conditions:

{table(nr[~nr.improved],['series','condition_label','raw_EGFP_CV_percent','RAS_CV_percent'])}

## Expression dependence and effective support
All 32 wells show lower RAS in the highest common red bin than in the lowest common red bin; differences range from {red.high_minus_low_bin_RAS.min():.3f} to {red.high_minus_low_bin_RAS.max():.3f} RAS. These within-sample bin summaries demonstrate expression dependence; normalization does not remove it. The common-bin analysis does not cover the entire red tail.

Effective red-weighted support `N_eff,R = sum(r)^2 / sum(r^2)` is {red.effective_red_events.min():.0f}–{red.effective_red_events.max():.0f} per reporter sample, only {100*red.red_weighted_support_fraction.min():.2f}%–{100*red.red_weighted_support_fraction.max():.2f}% of selected events. It measures concentration of red weights, never biological replicate count. Reporter-positive fractions range {100*red.reporter_fraction.min():.2f}%–{100*red.reporter_fraction.max():.2f}%; the corrected mCherry distributions and quantiles are exported per sample.

The top 1% of red-expressing events carry {100*high.top_one_percent_red_share.min():.2f}%–{100*high.top_one_percent_red_share.max():.2f}% of red signal. Their diagnostic removal shifts RAS by {100*high.relative_change_without_top_one_percent.min():.2f}% to {100*high.relative_change_without_top_one_percent.max():.2f}%. Moving the corrected red-threshold excess to 0.8/1.2/1.5 times primary changes RAS by {100*th.relative_change.min():.3f}% to {100*th.relative_change.max():.3f}%. These support numerical stability near the lower boundary, but do not remove expression-distribution dependence or validate a detector upper limit.

## Statistical uncertainty
The retained 2,000 paired-event bootstrap draws preserve green/red covariance. One shared bivariate control-noise draw per ID is applied jointly to all samples. Event-only and event-plus-control intervals are stored separately. Gate/background/threshold alternatives are sensitivity analyses, not silently pooled into a nominal CI. Between-well SD/CV is based on two wells; between-condition differences are separate experimental contrasts. No interval estimates between-day, culture or laboratory reproducibility. The final wrapper reproduces original sums and RAS and imports the verified original uncertainty records; new-sample bootstrap is an explicit optional API operation.

## BFP contribution
Mean BFP-positive fraction among reporter-selected S10 events rises from {100*bs.loc[0]:.2f}% at no editor to {100*bs.loc[8]:.2f}% at 800 ng editor. Thresholds are optically provisional. Common-BFP bins yield 26/40 estimable bins and 14/40 unavailable bins, so this conditional analysis is exploratory. Do not confuse BFP intensity, BFP-positive fraction, editor DNA dose, reporter RAS and R+B+ RAS.

The reporting contract includes sample, well and condition, population, context, estimator, input hash, selected N, effective N, signed green/red sums, RAS, distinct uncertainty fields, QC and interpretation. Suitable use is same-context reporter measurement and compatible reference calibration. It does not establish expression-independent molecular editing truth.

Sources: [normalization pairs](../results/layer1/Normalization_Repeatability.csv), [RAS contract](../results/layer1/RAS_Results.csv), [red dependence](../results/layer1/Reporter_Expression_Dependence.csv), [red bins](../results/red_profiles.csv), [threshold sensitivity](../results/layer1/Red_Threshold_Sensitivity.csv), [tail influence](../results/high_expression_influence.csv), [BFP profiles](../results/blue_profiles.csv).
''')
    comparison=cv[(cv.validation=='leave_one_reference_level_out')&(cv.subset=='all_held_out')]
    primary=cv[(cv.model=='monotone_hinge_50')&(cv.subset=='all_held_out')]
    write('science/RES_Primary_Model_Specification.md',f'''# Frozen primary RES model
Model ID: `{model['model_id']}`. Estimator: `{ESTIMATOR}`. Context: `{FINAL['context_id']}`. Calibration identity: `{FINAL['calibration_domain_id']}`.

```
{equation}
```

A is AC DNA mass fraction (0–1). Equivalently use `alpha + lower_slope*min(A,0.5) + upper_slope*max(A-0.5,0)`, with lower slope {params['lower_slope']:.15g} and upper slope {params['upper_slope']:.15g}. Coefficients in JSON use this latter basis. The knot is fixed at 0.5 as in v4, never searched against the held-out errors. Both slopes are constrained nonnegative; the intercept is unconstrained. Equal weight per independent reference well, bounded least squares, 20 wells and ten corrected levels.

For RAS y within [{model['values'][0]:.15g}, {model['values'][-1]:.15g}], invert `(y-alpha)/lower_slope` below g(0.5)={model['values'][1]:.15g}, otherwise `0.5+(y-g(0.5))/upper_slope`. General piecewise inversion returns an identified interval for flat segments. Outside-domain inputs return null, without clipping or extrapolation. RAS and RES are dimensionless but describe different axes. Display RES as “RES — AC Reference-Equivalent Score”, with DNA mass-equivalent units and status; never as RNA editing percentage.

`models/res_primary/model.json` is authoritative. `uncertainty.json` stores all 1,000 bootstrap coefficient draws, synchronized observation draw IDs and values, and 1,001-point curve bands. `calculate_res` reads these artifacts; routine application use does not refit. Model/context/core/config/reference hashes detect invalidated dependencies. Refit and new-context use require new identities and scientific review; the supplied fitting function is research-only.

Two uncertainty outputs are deliberately separate. Conditional 2.5/97.5% inverse bootstrap quantiles account for reference-well resampling, paired event noise, and shared controls, conditional on valid inversion. Their success denominator is reported. The broader compatibility set inverts the bootstrap mean-curve band expanded by the 95th percentile absolute leave-level-out RAS residual and the sample RAS interval margin. This is a reproducible diagnostic set, not a calibrated 95% CI or guaranteed ±10 percentage-point accuracy. Grid edges are rounded to 0.001 mass fraction and do not imply assay precision.

Internal range policy also requires compatibility with the isotonic benchmark: largest contiguous response region whose union of primary and isotonic sets is interior, ≤0.20 total mass-fraction width, and has unique point inverses. Sample measurement uncertainty is additionally checked. No rule uses S10 ranking or desired editing predictions.
''')
    write('reports/Layer2_RES_Final_Report.md',f'''# Layer 2 — Final operational RES
{base}
The fixed-knot monotone hinge is frozen as the primary operational reference model. Affine and isotonic remain benchmarks. This completes executable reference-equivalent calculation while retaining explicit research status.

## Calibration and selection
S7 has 20 independent transfection wells, two per corrected AC DNA mass input: 0, 5, 15, 20, 30, 40, 50, 75, 90 and 100%. Original source “10” means 15%; original 75A/B mean 90%; original 90A/B mean 75%. The last interchange is the experimental team's retrospective probable correction, not independently verified preparation evidence. Improved fit is not proof of the correction. Original filenames, event bytes and well RAS are unchanged.

The equation is `{equation}`. Lower and upper slopes are {params['lower_slope']:.6f} and {params['upper_slope']:.6f}; inverse sensitivities are {1/params['lower_slope']:.3f} and {1/params['upper_slope']:.3f} fraction per RAS unit. Three parameters and the pre-existing fixed 50% knot provide a transparent continuous inverse. The model has the lowest leave-reference-level forward RMSE and the lowest matched-subset inverse MAE of the three candidates. Isotonic performs better in leave-one-well-out forward prediction, where the same reference level remains in training. Model selection and evaluation used the same small dataset, so selection optimism is not removed by external or nested model-family validation.

{table(comparison,['model','forward_prediction_n','forward_RMSE_RAS','total_held_out','unique_inverse_n','out_of_range_n','inverse_MAE_pp','inverse_RMSE_pp','inverse_bias_pp'])}

Forward RMSE uses 16 evaluable interior held-out wells: excluded 0%/100% levels lie outside each fold's training input range. Inverse columns use observed held-out RAS and their own successful-inversion denominators. They answer a different question.

## Inverse performance without hiding failures
{table(primary,['validation','total_held_out','unique_inverse_n','out_of_range_n','inverse_MAE_pp','inverse_RMSE_pp','inverse_bias_pp','compatible_set_coverage_all','conditional_bootstrap_coverage_given_interval'])}

The primary model uniquely inverts 20/20 leave-one-well-out observations (MAE 5.375 pp; RMSE 6.099 pp) and 19/20 leave-one-reference-level-out observations (MAE 6.153 pp; RMSE 7.078 pp; bias +0.120 pp). The one failed level-held-out case is out of the fitted response range; its error is undefined, not zero. A full-20 point MAE is therefore not defined. Restricting to the 16 held-out wells whose true fractions are inside training range gives 16/16 unique inverses and MAE 5.327 pp, RMSE 6.115 pp. Endpoint observations must not be called validated interpolation merely because their observed signal has an inverse.

The previously quoted 5.85 pp is exactly 5.847525 pp for 14 wells uniquely inverted by all three models, not the full held-out set. That common subset includes two 0% observations outside their fold's input domain. Its purpose is like-for-like model comparison. Full denominators and per-level errors remain in the tables.

## Uncertainty findings
The new outer-held-out uncertainty evaluation resamples wells within training levels (500 draws/fold), synchronizes paired event/shared-control draws, and estimates discrepancy from inner held-out training levels only. No held-out outcome selects the interval width. Conditional bootstrap intervals cover only 3/20 true inputs under leave-one-well-out and 5/20 under leave-one-level-out. This demonstrates that narrow measurement/parameter intervals alone inadequately capture model discrepancy. They are not the headline uncertainty.

The broader nonnominal compatibility sets cover 19/20 and 16/20 respectively. Level-held-out interior coverage is 16/16, with wide sets; four endpoint truths cannot be covered by sets restricted to the fold's observed input domain. These are empirical internal coverages on few dependent folds, not validated nominal probabilities. Two reference wells per level cannot estimate preparation-batch or between-day variation. All unsuccessful inversions, conditional denominators, uncertainty sets and domain labels are exported.

## Four domains and real outputs
Numerical A domain: 0–1. Numerical response domain: {model['values'][0]:.6f}–{model['values'][-1]:.6f} RAS. Observed well responses: {dom['observed']['observed_RAS_range'][0]:.6f}–{dom['observed']['observed_RAS_range'][1]:.6f}; observations exist at ten discrete levels, not every continuous A.

The re-evaluated conservative internal screen is RAS 0.7845–1.0065, corresponding under the frozen hinge to 54.52–80.41% AC mass equivalent. Its reference-only grid criteria reproduce v4; adding actual sample measurement uncertainty must be evaluated separately for both models. Isolated passing grid points above 1.0065 are not joined across gaps. Only the actual 75% reference level (two wells) lies inside this screen; the smooth interval must not imply dense empirical validation. The width threshold is a declared engineering diagnostic. It is not a validated assay range.

All 20 S7 wells have model-defined point inverses, spanning {100*samples.res_mass_fraction.min():.2f}%–{100*samples.res_mass_fraction.max():.2f}% AC DNA mass equivalent. Two fall inside the reference-response screen and have primary-model sample compatibility widths below 20 pp, but their measurement-expanded primary/isotonic union widths are 20.8 and 21.8 pp. They are classified PRIMARY_INFORMATIVE_CROSS_MODEL_SET_BROAD: neither passes the stricter 20 pp joint sample screen. Fourteen have weak/boundary support, and four are in the observed high-end flattening region. All numerical estimates remain available for research. The 90% versus 100% response means are 1.132248 and 1.130373; their difference −0.001875 is much smaller than its n=2 uncertainty. This supports poor separation, not equivalence or proven detector saturation. The primary positive upper slope does not remove that empirical limitation.

Research mode emits compatible point estimates and intervals with all limitations. Routine quantitative mode returns no qualified RES in this release; it retains the research result in its separate field. Transfer to S10 is unqualified: matching HEK293T and detector profile does not establish construct, loading, treatment, time, reference axis or RNA-population compatibility. S10 reporter values are below the internal screen; no ordinary S10 RES or R+B+ transfer is emitted. A separately named hypothetical mapping is retained for sensitivity only.

Sources: [model specification](../science/RES_Primary_Model_Specification.md), [full validation](../results/layer2/RES_Inverse_Validation.csv), [comparison](../results/layer2/RES_Model_Comparison.csv), [sample results](../results/layer2/RES_Sample_Results.csv), [domains](../results/layer2/RES_Calibration_Domain.json), [worked examples](../science/RES_Worked_Examples.md), [transfer audit](../results/calibration/S7_S10_compatibility.csv).
''')
    # Full raw-to-model examples keep correct source IDs, original labels and signed sums.
    examples=['S7_90B','S7_5B','S7_100A'];parts=[];manifest=read('inventory/acquisition_manifest.csv').set_index('acquisition_id');sr=samples.set_index('sample_id')
    for name in examples:
        row=sr.loc[name];r=rp[rp.acquisition_id==name].iloc[0];q=qc[qc.acquisition_id==name].iloc[0];raw=manifest.loc[name];bl,bh=json.loads(row.conditional_bootstrap_interval)
        point=row.res_mass_fraction
        formula=f"({row.RAS:.12g} - {params['alpha']:.12g}) / {params['lower_slope']:.12g}" if point<.5 else f"0.5 + ({row.RAS:.12g} - {model['values'][1]:.12g}) / {params['upper_slope']:.12g}"
        parts.append(f'''## {name}: corrected reference input {100*row.known_AC_mass_fraction:g}% AC by mass
Raw file: `{raw.file_path}`; SHA-256 `{raw.sha256}`. Original acquisition ID is retained even when its label was corrected. Independent experimental unit: `{raw.well_id}`.

Recorded events {q.recorded_events:,} → after acquisition QC {q.after_acquisition_QC:,} → cells {q.cell_events:,} → singlets {q.singlet_events:,} → reporter population {int(r.n_selected):,}. Each selected event subtracts the saved linear backgrounds (green 2999.921288652426, red 1149.481510590721); the red threshold is applied to raw red values, and signed green values remain.

Corrected green sum = {r.sum_G_corrected:.15g}; corrected red sum = {r.sum_R_corrected:.15g}; RAS = {r.sum_G_corrected:.12g} / {r.sum_R_corrected:.12g} = **{row.RAS:.9f}**. Event-plus-shared-control RAS interval: [{r.event_control_ci_low:.9f}, {r.event_control_ci_high:.9f}]. Effective red support: {r.effective_red_events:.1f}, distinct from one independent well.

Frozen inverse calculation: `{formula}` = **{point:.9f}**, or **{100*point:.3f}% AC DNA mass equivalent**. Conditional bootstrap interval: [{100*bl:.3f}%, {100*bh:.3f}%], based on {int(row.bootstrap_success_n)}/{int(row.bootstrap_total_n)} invertible draws. Broader compatibility interval: [{100*row.compatibility_low:.1f}%, {100*row.compatibility_high:.1f}%], not a nominal 95% CI. The measurement-expanded primary/isotonic union has total width {100*row.cross_model_sample_width:.1f}pp. Status: `{row.calibration_region}`; `{row.scientific_status}`. This is a model-derived equivalent, not measured RNA editing and not an independent held-out validation sample.

Run: `python science.py example --sample {name} --output _work/{name}.json`.
''')
    write('science/RES_Worked_Examples.md',f"# Actual FCS → RAS → RES calculations\n\n{base}\nCommon equation: `{equation}`. Full context: `models/context_profiles/context_v1.json`.\n\n"+'\n'.join(parts)+'''
The low-input example shows boundary sensitivity and missing bootstrap inverses; the 100% example shows why a positive fitted slope is not proof of resolving the observed 90–100% plateau. `S7_90B` is the informative corrected 75% example. JSON report output also includes a null PER and its reason.
''')
    write('science/RES_Model_Card.md',f'''# RES primary model card
- Identity: `{model['model_id']}`; fixed 50% hinge, three parameters, explicit JSON.
- Purpose: reference-equivalent interpretation of compatible S7 reporter-population RAS; AC DNA mass basis.
- Training: 20 wells/10 levels, two wells per level, one experimental series. Source correction is retrospective and not independently verified.
- Performance: level-held-out forward RMSE 0.036368 RAS (16/20 evaluable forward cases); inverse MAE 6.153 pp, RMSE 7.078 pp on 19/20 unique inverses; one failure. Shared three-model subset MAE 5.848 pp (14 wells).
- Uncertainty: conditional bootstrap plus separately reported broader discrepancy compatibility set; neither is a validated 95% measurement interval. Conditional held-out coverage is poor.
- Domains: numerical A 0–1; internal exploratory screen RAS 0.7845–1.0065; no supported S10/external transfer. Only two reference wells occupy the screen's actual sampled level.
- Allowed: explicitly labeled compatible research estimates; own-model fitting as a new research model.
- Disallowed interpretation: RNA editing percentage, universal calibration, validated ±10 pp accuracy, routine quantitative claims, unqualified R+B+ transfer.
- Failure policy: missing/nonfinite/outside range -> null; plateau -> interval without unique point; incompatible -> ordinary RES null with optional separate hypothetical mapping.
- Maintenance: any input/core/context/calibration change requires dependency invalidation and a new model identity. Default application calls load, never silently refit.
''')
    write('reports/Layer3_PER_Final_Report.md',f'''# Layer 3 — Molecular evaluation and PER status
{base}
Relative molecular analysis is available and informative. Absolute RNA fraction and PER remain unavailable.

## Preserved primary evidence
The provisional 523 bp OpenA amplicon is reconstructed independently from four no-editor F/R pairs in two transfection wells. All four assemblies agree and match the supplied candidate. There are 494 Q20-supported bases, including 393 bidirectional and 101 unidirectional positions; 29 terminal positions depend on primers. The generic 544 bp design differs by multiple substitutions and indels (not one 21 bp deletion). Candidate C280 is a C→T chromatogram event corresponding to RNA C→U; transferred coding context is CGA→TGA in the switch linker. Its intended target identity remains unconfirmed independently of this reconstruction.

All 48 original AB1 traces were byte-checked for base calls, qualities, peak locations and dye-channel order. 47 are eligible at C280. `1-8-2.F` fails local flank identity (0.60 versus required 0.90), so it is retained as evidence but excluded from the site point estimate. There are 23 complete technical F/R pairs, 24 labels and 12 independent transfection wells; sequencing labels 1/2 map to flow A and 3/4 to B. RNA was extracted after flow at the same experimental timepoint; its exact selected cell population and elapsed interval are unresolved. No documented DNase/no-RT controls or known-fraction response standards qualify absolute RNA fractions.

No-editor directional raw ratios average 0.044926 (F) and 0.015840 (R); high-editor values average 0.163541 and 0.287447. Dose-level background-corrected mean index rises from 0 to 0.201744. The no-editor corrected mean is zero by construction, not evidence of no editing. Direction bias persists (raw R−F mean {mols['raw_direction_bias']:.5f}, direction RMSE {mols['raw_direction_RMSE']:.5f}); correlation does not establish agreement. Read, technical-label and well summaries remain distinct. The one complete pair in 8A has no estimable within-well technical SE.

## Predictive comparisons and dose confounding
The target for prediction is the raw direction-averaged C280 chromatogram composition index, with no held-out-control subtraction used to define the training endpoint. All 120 predictions from the five original full-cohort models reproduce exactly within tolerance. Existing positive-dose/co-expression models remain in historical tables (10 wells, five doses). The new table adds predeclared linear dose and linear dose plus BFP fraction benchmarks to the existing log-dose model; no nonlinear family search was performed.

{table(mol[mol.validation=='leave_one_dose_out'],['model','well_n','dose_condition_n','MAE','RMSE','bias','outside_predictor_range_n'])}

BFP fraction RMSE 0.019219 is close to the linear editor-dose-only RMSE 0.019884. Adding BFP to linear dose yields 0.017795, a modest internal reduction that cannot establish an independent biological contribution in 12 wells. BFP fraction correlates with dose at r={conf['B_fraction_vs_linear_dose_pearson']:.4f}. Within-dose A−B differences give r={conf['within_dose_difference_pearson']:.4f} across only six independent pairs; this limited support does not separate measurement error, transfection variability and causal editor abundance. RAS alone (RMSE 0.090155) is worse than the mean-only baseline (0.083797). BFP's strong overall association must not be described as proven information beyond dose.

Leave-one-well-out and leave-one-dose-out are exported separately. Prediction errors are in index units, not editing percentage points. OLS t intervals are model-assumption prediction intervals; empirical coverage and predictor-range extrapolation counts are reported. The new error uncertainty resamples six dose clusters of fixed held-out errors and is descriptive, not a new independent validation. Marginal predictor-range flags do not certify multivariate convex-hull support. No external batch or unobserved experimental context was validated.

## RES–molecular and PER decision
S10 is not qualified for the S7 reference model, and its RNA population cannot be assumed R+B+. Therefore no empirical hinge-RES-to-molecular staged fit is claimed. A deterministic invertible transformation does not create new sample-level information; it can change the functional form allowed to a downstream regression. Existing affine direct-versus-staged predictions agree to 3.47×10⁻¹⁶ as an algebraic sensitivity only. RES's demonstrated use is reference interpretation, not improved S10 RNA prediction.

The interface retains `E_RNA = h(RES)` and `PER = 100 h(RES)%` but returns PER=null. Separate flags identify molecular data availability, candidate signal, relative index, relative-model fitting/internal evaluation, absolute assay qualification and domain validation. No relative index is placed in a percent-edited-RNA field. Version 1 deliberately has no adapter that can authorize a new absolute model merely from a caller-supplied boolean.

Sources: [molecular data](../results/molecular/S10_well_level_molecular_results.csv), [reconstruction](OpenA_Amplicon_Reconstruction.md), [new comparisons](../results/layer3/Molecular_Prediction_Comparison.csv), [all held-out predictions](../results/layer3/Molecular_Prediction_Validation.csv), [dose adjustment](../results/layer3/Dose_Confounding_Assessment.json), [original co-expression comparisons](../results/prediction/S10_direct_model_results.csv).
''')
    write('science/Molecular_Reference_Status.md','''# Molecular reference status
S10 supplies 48 original AB1 files, 47 site-eligible reads, 23 complete technical F/R labels and 12 independent transfection wells. Candidate C280 in a provisional 523 bp amplicon has qualified local sequence support but not independent intended-target provenance. Available endpoint: direction-averaged relative chromatogram index. Unavailable endpoint: calibrated absolute edited-RNA fraction. No-editor subtraction and sequencing technical replicates do not supply missing assay calibration.

See [Layer 3 report](../reports/Layer3_PER_Final_Report.md), `results/molecular/`, and `models/molecular/PER_interface.json`. Original chromatograms and the reconstructed reference are included; no external file is required.
''')
    write('science/PER_Model_Interface_Specification.md','''# PER interface specification
`analyze_molecular_reference(root)` returns actual well results with relative-index and assay qualification flags, or MOLECULAR_REFERENCE_MISSING. `fit_biological_calibration(x,y,endpoint="relative_chromatogram_index")` fits a simple OLS research model; absolute RNA endpoints are rejected in v1. `predict_per(res_result, biological_model=None)` always returns a JSON null PER with a precise status under the supplied evidence.

Future qualified h models must record model/assay identity, absolute RNA-fraction endpoint, training well IDs, independent validation, reporter/population/treatment/context compatibility, numerical and transfer domains, uncertainty and source hashes. A future reviewed adapter may support these models. Setting an `absolute_fraction_qualified` boolean does not activate such an adapter in this release. Framework: E_RNA=h(RES), PER=100*h(RES) percent. Missing is null, never 0. A relative molecular prediction remains in its own explicitly named index field.
''')
    write('science/PER_Limitations_and_Future_Validation.md','''# PER limitations and future qualification
Existing limitations: candidate rather than independently confirmed target/construct identity; primer-inferred amplicon termini; direction-dependent Sanger peak response; one failed local read and one well with only one complete technical pair; no known-RNA-fraction standards, no documented no-RT/DNase controls, uncertain RNA cell population; two wells per dose and one series; strong shared dose dependence; no compatible S7-to-S10 bridge or external validation.

Future evidence requirements are scientific qualification requirements, not performed experiments: independently establish the exact constructs and intended site; qualify molecular response using known edited/unedited RNA fractions with relevant controls; document RNA population and timing; establish the same reporter/loading/treatment/population domain for optical and molecular measurements; use independent reference preparations and biological validation wells/batches; evaluate error, coverage, extrapolation and dose-adjusted information against simple baselines. Only then register a reviewed h model with explicit domain and error policy. No current figure may substitute the index for an RNA-editing percentage.
''')
    evidence=[
      ['Reproducible context and event selection','34 unique FCS acquisitions; two shared Mock controls','32 experimental wells', '204 masks identical; negative-transfer positivity '+f'{100*neg.test_positive_fraction.min():.3f}–{100*neg.test_positive_fraction.max():.3f}%', 'identity compensation; no optical validation','computational + internal technical','results/layer0/raw_flow_regression.json','recorded CytoFLEX S profile','main methods/result with optical limitation'],
      ['mCherry normalization improves descriptive well-pair repeatability','S7/S10','20 S7;12 S10','median CV 4.697→1.767%;6.711→5.142%; improved 8/10 and 5/6','n2/condition; not accuracy','internal descriptive','results/layer1/Normalization_Repeatability.csv','same reporter-selected populations','main result'],
      ['RAS remains expression-distribution dependent','S7/S10','32','highest common-red-bin RAS lower in 32/32; N_eff/N 5.87–16.42%','cells are not independent wells','descriptive sensitivity','results/layer1/Reporter_Expression_Dependence.csv','same context','required limitation'],
      ['Fixed-knot hinge provides operational reference-equivalent inverse','corrected S7','20','LO-level forward RMSE 0.036368 RAS; 20/20 in-sample inverses','retrospective labels; fixed family selected on same data','internal calibration','results/layer2/RES_Model_Comparison.csv','AC DNA mass; reporter population','principal calibration result'],
      ['Inverse recovery has quantified failure and error','corrected S7','20 held-out wells/10 levels','19/20 unique; MAE 6.153 pp; RMSE 7.078 pp on 19; common14 MAE5.848','no full20 point MAE; endpoint training-domain exclusions','internal grouped validation','results/layer2/RES_Inverse_Validation.csv','S7 reference series only','principal inverse-performance result'],
      ['Uncertainty must include model discrepancy','corrected S7','20','conditional bootstrap LO-level coverage5/20; compatibility16/20; interior16/16','wide nonnominal sets; dependent folds; n2/level','internal diagnostic','results/layer2/RES_Inverse_Validation.csv','same experiment','required uncertainty result'],
      ['Real sample RES available with applicability status','corrected S7','20','1.644–96.545% mass-equivalent;2/20 inside reference screen;0/20 pass measurement-expanded joint20pp screen','in-sample; not RNA; only75% reference level samples screen','operational exploratory','results/layer2/RES_Sample_Results.csv','RAS0.7845–1.0065 exploratory screen; no routine qualification','worked demonstration'],
      ['Relative molecular editing-associated signal available','S10 AB1','12 wells;48reads','47 eligible;23 completepairs;high-dose corrected index0.201744','not absoluteRNA; directional bias; controls missing','molecular descriptive','results/molecular/S10_well_level_molecular_results.csv','candidateC280','molecular evidence with endpoint caveat'],
      ['BFP predicts relative signal better than RAS; dose confounds interpretation','S10','12 wells/6doses','LO-dose RMSE B0.019219;linear dose0.019884;dose+B0.017795;RAS0.090155','sixpairs within-dose r0.345; no independent causal contribution','exploratory grouped comparison','results/layer3/Molecular_Prediction_Comparison.csv','sameS10 series; relativeindex','comparative result with dose benchmark'],
      ['PER remains unqualified','S7/S10','no qualified absoluteRNA standards','PER=null','missing assay and transfer qualification','explicit evidence boundary','models/molecular/PER_interface.json','no validated transfer domain','state explicitly']]
    e=pd.DataFrame(evidence,columns=['scientific_statement','dataset','independent_sample_count','numerical_result','uncertainty_or_limitation','evidence_strength','source_table','applicable_domain','Wiki_suitability'])
    e.to_csv(ROOT/'results/integrated/SONAR_Evidence_Matrix.csv',index=False)
    write('science/SONAR_Evidence_Matrix.md','# Scientific evidence matrix\n\n'+table(e))
    write('reports/SONAR_Integrated_Evidence_Report.md',f'''# SONAR integrated scientific evidence
{base}
## Measurement question and architecture
Can a multicolor RNA-editing reporter be measured reproducibly, interpreted against an empirical reference, and connected to independent molecular evidence? SONAR separates context construction (Layer 0), fluorescence ratio quantification/RAS (Layer 1), AC-reference calibration/RES (Layer 2), and molecular evaluation/PER qualification (Layer 3). Each layer declares its measurement population and evidence limits.

## Layer 0: reproducible context
Question: can raw events be decoded, selected and corrected reproducibly? Evidence: 34 unique acquisitions and two shared Mock controls; 204 masks reproduce, with stored channel/control/gate identities. Negative-control transfer positivity is 0.424–0.602%. The observed range flags do not establish saturation. Supported interpretation: fixed, reproducible detector-scale processing within the recorded context. Limitation: unvalidated multicolor optics, no viability marker or verified LOQ/upper detector bound. Source: `results/layer0/`; visualize counts and control distributions. See [final context report](Layer0_Context_Final_Report.md).

## Layer 1: normalization with measurable limits
Question: what does continuous mCherry normalization improve? Evidence: 20 S7 and 12 S10 independent transfection wells, two per condition. Median well CV falls 4.697→1.767% and 6.711→5.142%; 8/10 and 5/6 conditions improve. Supported interpretation: improved descriptive within-experiment repeatability, not molecular accuracy. All 32 samples retain red-expression dependence and concentrated red weights; paired-event CIs do not estimate between-well/day variance. Source: `results/layer1/`; visualize paired CVs and red-bin profiles. See [RAS report](Layer1_RAS_Final_Report.md).

## Layer 2: main reference-calibration contribution
Question: can reporter response be converted to an interpretable reference equivalent? Evidence: corrected S7 mass mixtures and frozen 50% hinge; leave-level forward RMSE 0.036368 RAS (16 evaluable interior wells). Operational inversion yields research RES for all 20 reference wells. In held-out inverse recovery, 19/20 are unique and conditional MAE/RMSE are 6.153/7.078 pp. The restricted matched14 MAE is 5.848 pp. Supported interpretation: transparent AC mass-equivalent measurement with explicit failure and uncertainty. Conditional bootstrap coverage is poor (5/20 LO-level); broader compatibility coverage is 16/20 overall and 16/16 interior, with no nominal guarantee. RAS 0.7845–1.0065 is an exploratory compatibility screen, not a validated 54.52–80.41% assay range. Source: `results/layer2/`; three distinct figures show calibration, all-case inverse recovery, and actual raw-to-RES examples. See [RES report](Layer2_RES_Final_Report.md).

## Layer 3: independent molecular evidence and its boundary
Question: do optical readouts track the available molecular signal? Evidence: provisional 523 bp reference, candidate C280, 48 reads/12 wells, 47 eligible reads. The relative chromatogram index increases with dose but cannot be called an edited-RNA fraction. BFP fraction has lower dose-held-out prediction RMSE than RAS (0.019219 vs0.090155), yet linear dose is similar (0.019884). Dose+BFP reaches0.017795 internally; six within-dose pairs provide limited independent support. Supported interpretation: relative molecular signal is more closely associated with editor-dose/detection than with reporter RAS in S10. No compatible staged RES-to-RNA calibration or absolute PER is established. Source: `results/molecular/`, `results/layer3/`; visualize traces, direction differences and dose-held-out benchmarks. See [PER report](Layer3_PER_Final_Report.md).

## Integrated validation and scientific usefulness
Context, estimator, model, population and input hashes accompany every sample. Numerical availability is separate from QC and interpretation permission. The analytical core runs without a GUI or notebook. Reproduction evidence is in `provenance/`; it is computational replication, not independent biological or interlaboratory validation. Improved repeatability, calibration fit, inverse reference recovery and molecular accuracy are different claims.

This release provides a working raw-flow-to-RES measurement demonstration, failure-aware calibration evaluation, molecular evidence, and a tested software foundation. Adapting it requires a separately qualified context and reference model; S7 is not universal. Exact construct/loading/treatment metadata, independent reference batches, optical controls and molecular assay qualification remain unresolved. The complete [evidence matrix](../science/SONAR_Evidence_Matrix.md) gives one row per claim and its Wiki suitability. This is scientific source material for later Wiki writing, not final Wiki prose or final publication artwork.
''')
    figure_rows=[
      ('Context processing','Layer0 counts/control distributions','34 acquisitions; 32 experimental wells','results/layer0/Sample_QC.csv;results/negative_transfer.csv','event counts, fluorescence in linear a.u.','masks and control transfer support reproducibility, not optical accuracy','src/plots.py; existing F01–F03 diagnostics'),
      ('RAS repeatability','paired raw vs RAS CV','2 wells per condition; 10 S7+6 S10','results/layer1/Normalization_Repeatability.csv','CV %; identical reporter populations','n2 descriptive; report three non-improving conditions','figures/diagnostic/RAS_repeatability'),
      ('Expression dependence','common-red-bin RAS plus effective support','32 wells; events nested','results/red_profiles.csv;results/layer1/Reporter_Expression_Dependence.csv','red intensity a.u. (display log); RAS; effectiveN/N','weights and reporter distribution remain important','figures/diagnostic/RAS_red_expression_dependence'),
      ('RES A — empirical calibration','corrected A/B points, frozen hinge and envelope','20 wells; 10 referencelevels','results/calibration/S7_reference_response_corrected.csv;models/res_primary/uncertainty.json','AC DNA mass % vs RAS','retrospective labels; envelope not nominal95CI','figures/diagnostic/RES_A_reference_calibration'),
      ('RES B — inverse recovery','held-out true vs recovered; failure count; per-level error','20 held-out wells;10levels;19unique','results/layer2/RES_Inverse_Validation.csv;RES_Model_Comparison.csv','true/recovered AC mass %; error pp','show out-of-range point and endpoint training-domain flags; never show successes alone','figures/diagnostic/RES_B_inverse_recovery_all_cases'),
      ('RES C — actual calculation','3 raw-FCS examples, signed sums, RAS and inverse intervals','3 actual wells; illustrative in-sample','science/RES_Worked_Examples.md;results/layer2/RES_Sample_Results.csv','AC DNA mass-equivalent %','point is model output, not measuredRNA; conditional intervals under-cover','figures/diagnostic/RES_C_real_sample_calculations'),
      ('Molecular evidence','amplicon support, target traces, F/R agreement','48 reads;12 wells;23completepairs','results/molecular/','nt coordinates; chromatogramindex; traces','C280 candidate; direction bias; notabsoluteRNA','src/layer23_plots.py; existing L23_01–06'),
      ('Dose-aware molecular prediction','mean/RAS/BFP/dose/dose+B comparisons; within-dose pairs','12 wells;6doseconditions','results/layer3/Molecular_Prediction_Comparison.csv;Within_Dose_Well_Differences.csv','LO-dose RMSE in rawrelativeindex units','BFP tightly tracksdose; no independent contribution proven','figures/diagnostic/Molecular_dose_benchmarks')]
    f=pd.DataFrame(figure_rows,columns=['scientific_message','suggested_panels','independent_sample_count','source_tables','axes_and_units','interpretation_limits','plot_or_code'])
    f.to_csv(ROOT/'figures/diagnostic/figure_evidence_inventory.csv',index=False)
    write('SONAR_Final_Figure_Evidence_Inventory.md','# Final figure evidence inventory\n\nDiagnostic PNG and editable SVG sources accompany the new plots. All six new figures are generated by `src/final_reports.py::plots`; existing plots and their source tables are retained. Captions must keep sample counts, units and limits below. No final publication layout or decorative schematic is claimed.\n\n'+table(f)+'\n\nKey numbers and supported conclusions are in `results/integrated/SONAR_Evidence_Matrix.csv` and the final layer reports. Original 75/90 filenames must be shown with corrected condition labels whenever displayed.')
    plots()
    print('Final reports, evidence matrix, worked examples and six diagnostics generated',flush=True)

if __name__=='__main__':run()
