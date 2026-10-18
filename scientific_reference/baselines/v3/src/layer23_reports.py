"""Integrated scientific handoff generated from the actual extension outputs."""
import json
import numpy as np,pandas as pd
from layer23_common import *

def read(p):return pd.read_csv(ROOT/'results'/p)
def load(p):return json.loads((ROOT/p).read_text())
def run():
    rec=load('results/molecular/OpenA_reconstruction_summary.json');ms=load('results/molecular/S10_molecular_summary.json');cal=load('results/calibration/S7_calibration_summary.json');ps=load('results/prediction/S10_prediction_summary.json');audit=load('results/molecular/source_audit_summary.json')
    well=read('molecular/S10_well_level_molecular_results.csv');condition=read('molecular/S10_condition_molecular_summary.csv');mc=read('calibration/S7_model_comparison.csv');pv=read('prediction/S10_direct_model_results.csv');ass=read('prediction/S10_flow_molecular_associations.csv');inv=read('calibration/S7_inverse_identifiability.csv');an=read('calibration/S7_anomaly_well_diagnostics.csv');bs=read('molecular/S10_bystander_site_analysis.csv');processing=read('molecular/S10_processing_sensitivity.csv');fig=pd.read_csv(ROOT/'figures/layer23/figure_index.csv')
    header=f'Version: `{VERSION}`. Reviewed {CFG["review_date"]}. Upstream Flow Quantification: `{CFG["upstream_analysis_version"]}`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.\n\n'
    references='''## Method references

The original [Applied Biosystems ABIF specification, July 2006](https://archive.gfjc.fiu.edu/workshops/resources/literature/ABIF_File_Format.pdf), pp. 52–53, defines analyzed DATA9–12, PBAS2, PCON2 and PLOC2; per-file FWO_1 records channel order. [EditR primary paper](https://pubmed.ncbi.nlm.nih.gov/31021262/) and [author repository](https://github.com/MoriarityLab/EditR) establish a published Sanger-quantification approach. This release implements transparent peak metrics and processing sensitivities, not the EditR algorithm or a claim of EditR validation for this reporter. [scikit-learn isotonic documentation](https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html) describes the shape-constrained model and unavailable out-of-domain predictions; the installed version is pinned in `requirements.txt`. Sources accessed 2026-10-13. No external experimental observations enter fitting.
'''
    recon=header+f'''# OpenA amplicon reconstruction

## Result and evidence level
Four independently assembled no-editor F/R molecular-label pairs produce the **same 523 bp sequence**, exactly matching the newly supplied candidate FASTA. They represent **two independent transfection wells**, not four independent cultures. C280 is supported by four forward and four reverse Q20 reads and is the unique linker cytidine whose C→T substitution produces an in-frame stop in the reconstructed architecture. This supports a sequence/mechanism-based candidate. No independent construction record confirms that it was the intended target; no full plasmid sequence or accurate editing fraction is inferred.

## Method actually executed
The assembly does not use the supplied candidate or generic sequence as a template. For each of `1-0-1` through `1-0-4`, the raw PBAS2 forward call and reverse-complemented reverse call are locally aligned (match +2, mismatch −3, gap-open −8, extension −0.5). A seam at the midpoint of exact Q30-matched overlap joins the reverse read's upstream region to the forward read's downstream region. Recorded forward-primer suffix and reverse-primer reverse-complement prefix anchor the ends, requiring at least eight exact bases. The four complete assemblies agree before comparison with the provisional FASTA.

A separate evidence pass aligns all eight raw control reads back to the reconstruction. End trimming retains the interval bounded by 15-base windows with at least 12 Q20 calls; individual votes also require Q20. This avoids counting isolated high-quality calls in otherwise unreliable termini. Raw calls, trim status, qualities and base mappings are exported, so sequence inference is distinct from quality-qualified support.

{md(pd.DataFrame(rec['coverage_counts'].items(),columns=['evidence_class','positions']))}

**494 positions have accepted Q20 support from at least one direction; 393 have both directions.** The 29 positions without accepted Q20 support are 1–14 and 509–523. They are supplied by the recorded primers. The preliminary description of approximately 500 central positions is broadly consistent with raw-read coverage, but **500 independently bidirectionally quality-supported bases is not supported by this stricter audit**. No Q20 disagreement remains among accepted control calls. Sequenced PCR-primer bases do not independently verify the original plasmid-template termini.

## Relationship to the generic reporter
The generic primer interval is 544 bp. A declared global alignment gives 502 matches, 16 substitutions, 26 positions deleted in OpenA and five inserted positions: **net −21 bp**, rather than proof of one simple 21-bp deletion. Gap placement within divergent sequence is alignment-model dependent; the full alignment is exported. The independently reconstructed sequence, net length and candidate coordinate do not depend on selecting that gap representation.

The generic EGFP annotation establishes frame zero relative to this primer-anchored fragment. Its mapped EGFP segment ends at amplicon position 258; the mapped DHFR region begins at 289. The reconstructed intervening linker contains `CGA` at 280–282. C280→T produces `TGA` in cDNA (RNA `UGA`), after the EGFP segment and before DHFR. Among all {len(bs)} cytidines screened, C280 is the only stop-gain cytidine in this linker. Other stop-gain possibilities within EGFP or DHFR have different consequences. This prioritization uses sequence and architecture, not editor-dose correlation or the largest secondary peak.

## Source evidence
`results/molecular/OpenA_amplicon_consensus.fasta`, `OpenA_amplicon_annotated.gb`, `OpenA_independent_control_assemblies.csv`, `OpenA_reference_alignment.csv`, `OpenA_control_base_calls.csv`, `OpenA_generic_comparison.csv`, `OpenA_candidate_editing_sites.csv`, and `OpenA_vs_generic.aligned.fasta`. L23_01 visualizes Q20 support and architecture. The aligned FASTA preserves both ungapped source sequences. Original AB1, primers and provisional files are preserved unchanged.
'''
    report('reports/OpenA_Amplicon_Reconstruction.md',recon)
    sanger=header+f'''# S10 bidirectional chromatogram quantification

## Main result
All **48 AB1 reads** were processed and independently byte-cross-checked. **47 pass site-local QC**; 24 molecular labels yield **23 complete F/R pairs**, grouped into **12 independent transfection wells**. Increasing editor dose accompanies an increasing C280 alternative-peak signal in both directions, but direction-specific scale differences prevent interpreting the ratios as calibrated RNA-editing percentages.

{md(condition[['dose_ratio','well_n','F_raw_mean','R_raw_mean','signal_mean','signal_SD']])}

F is T/(C+T); R is A/(G+A). Direction means first average eligible labels within each well, then weight the two wells equally. At 1:8 they are **{condition.iloc[-1].F_raw_mean:.5f}** and **{condition.iloc[-1].R_raw_mean:.5f}**. The supplied preliminary F mean near 0.145 is recovered only by including the flagged misaligned forward read and equally weighting four raw traces. Excluding that read by a sequence-based rule and preserving well weighting changes the forward result; the difference is documented, not tuned toward the preliminary value.

## Read processing and QC
For each file, the ABIF directory is decoded directly and checked against Biopython for PBAS2, PCON2, PLOC2 and DATA9–12. FWO_1 is read per file (all observed orders happen to be GATC); no universal order is assumed. RevC is checked. High-quality called-base versus dominant processed channel agreement is exported in `S10_read_metadata_audit.csv`. Reverse reads are reverse-complemented for sequence alignment, while original trace coordinates and fluorescence identities are preserved. Reverse C280 therefore uses **G/A**, not C/T. The reference base and index are tested directly against the raw arrays.

Site eligibility requires stable mapping across gap-open penalties −6, −8 and −12, at least 90% matching flanking reference positions in ±10 bases (target omitted), median flank Phred ≥20, and ≤20% signal from the two irrelevant nucleotide channels at the target. The target's own Phred is reported but is not a selection gate: genuine mixed peaks can lower that base's quality. The thresholds are engineering screens, not validated molecular assay limits.

`1-8-2.F` has only **60% flank sequence identity** at the putative C280 location and fails the fixed identity rule. Its target Phred alone is 24, illustrating why read quality or a vendor warning alone is insufficient. The original trace, raw diagnostic ratio and failure reason remain in the read table. `1-8-2.R` is retained as eligible directional evidence; label 2 does not enter the primary equal-direction paired index because its F partner is unavailable. Thus the 1:8 A well has only one complete molecular label and no estimable nested-label SD/SE. It remains one independent well; no missing direction is imputed.

## Background and processing sensitivity
Primary metrics use processed-channel values at PLOC2. Sensitivity variants use (i) subtraction of each dye's local 10th-percentile processed baseline over ±4 called-base intervals, floored at zero for the peak-intensity model; (ii) maximum signal within ±2 scans of the mapped peak, restricted to the base cell; and (iii) integrated signal between neighboring peak midpoints. These variant assumptions are explicit and do not alter upstream signed-green RAS handling. No unknown spectral matrix or dye-response factor is estimated from a dose trend.

No-editor background is the equal-well mean within each sequencing direction. It is subtracted **without clipping negative corrected ratios**. The combined signal index is the mean of corrected F and R within each complete label, then the equal-label mean within each well. This supplies a reproducible relative index with arbitrary direction weighting; it is not a biophysical fraction. Model fitting uses the corresponding raw index so a held-out control does not define a training endpoint's background.

{md(processing[processing.dose_ratio==8][['processing','mean_index','sd_index']])}

At the highest dose, the four defensible processing choices yield mean indices about 0.197–0.202. This local robustness does not resolve the approximately twofold direction-dependent signal scale. Across complete pairs, raw R−F bias is {ms['raw_direction_bias']:.5f} and direction RMSE is {ms['raw_direction_RMSE']:.5f}; correlation {ms['direction_correlation']:.3f} is not agreement. Baseline subtraction barely changes the high-dose index, so local background alone does not explain the strand discrepancy. Sequence context, processed-dye response, overlapping peaks and different read positions remain plausible contributors; known-mixture standards are absent, so their separate effects cannot be identified.

## Other cytidines
All {len(bs)} cytidines are screened with the same mapping and local-QC logic. At {int(bs.both_direction_high_above_control.sum())} sites, both high-dose wells exceed the observed no-editor well maximum in both directions. This is a descriptive screening criterion, not a significance test, FDR-controlled discovery or proof of bystander editing. C224 and C305 are examples with appreciable direction-consistent increases. C280 remains prioritized by its independently evaluated linker stop consequence; secondary-peak ranking did not determine its identity.

## RNA provenance and assay status
The team confirms RNA extraction after flow at the same experimental time point and mapping 1/2→A, 3/4→B. A fresh search of {audit['files_inspected']} permitted source files and seven parseable annotated construct documents found no DNase/no-RT or sampled-population records. The search manifest and all text hits are saved; an Excel lock file was excluded as a non-data artifact. This means controls were **not found in supplied records**, not that they were necessarily absent from laboratory practice. The PCR submission and alternative peaks alone cannot exclude residual DNA, sequence mixtures or other technical origins. Full absolute RNA fractions remain unavailable.

## Well-level results
{md(well[['well_id','complete_molecular_pairs','F_raw_mean','R_raw_mean','signal_index','technical_mean_SE','molecular_fraction_status']])}

Nested-label SD and SE are descriptive with at most two labels. They exclude calibration bias, inter-direction bias, RNA sampling and between-well uncertainty; one-label values are unavailable. They are not 95% RNA-editing confidence intervals.

## Status vocabulary
- `CANDIDATE_SITE_SUPPORTED`: base, frame and architecture supported, intended-target record still missing.
- `EXPLORATORY_PEAK_COMPOSITION`: numerical site metric passes declared trace/mapping QC.
- `EDITING_ASSOCIATED_SIGNAL_EXPLORATORY`: candidate-site signal changes with conditions; does not establish RNA editing as the exclusive cause.
- `UNAVAILABLE_SITE_QC`: mapped raw diagnostic retained, but not accepted for site quantification.
- `ASSAY_VALIDATION_INSUFFICIENT`: no accurate absolute RNA fraction; never substitute zero.

Sources: all files under `results/molecular/`, particularly `S10_read_level_peak_metrics.csv`, `S10_bidirectional_concordance.csv`, `S10_well_level_molecular_results.csv`, `S10_bystander_site_analysis.csv`, and processing/background tables. L23_02–06 show actual traces, the failed read, well responses, direction disagreement and multisite screening.
'''+references
    report('reports/S10_Sanger_Quantification.md',sanger)
    models=load('models/layer23/S7_calibration_models.json');iso=inv[inv.exact_inverse_status=='NON_IDENTIFIABLE_PLATEAU']
    layer2=header+f'''# Layer 2 — Reporter Calibration and RES

## Actual fitted models
The 20 independent S7 transfection wells are fit on confirmed **AC DNA mass fraction A∈[0,1]**, with source label 10 corrected to 0.15. No exact AC/INAC plasmid identities/lengths were established in the permitted construct records; no molar conversion is made. Generic 7,498-bp design length is not substituted for both reference plasmids. AC mass fraction is never treated as edited-RNA fraction.

Three models were specified and executed: affine OLS, increasing isotonic regression with linear interpolation between fitted thresholds, and a continuous monotonic piecewise-linear model with a fixed 50% knot and nonnegative segment slopes. The hinge has three parameters, affine two; no high-degree polynomial or fitted knot search is used. Wells receive equal weight. All 75%, 90% and 100% observations remain in the fit.

Affine parameters: intercept **{models['affine']['coefficients'][0]:.6f}**, slope **{models['affine']['coefficients'][1]:.6f} RAS per unit AC mass fraction**. Hinge parameters and isotonic thresholds are serialized with version and upstream hashes in `models/layer23/S7_calibration_models.json`; parameter bootstrap draws are exported. A fitted function is not a validated measurement calibration.

## Internal validation results
{md(mc[['model','validation','RAS_prediction_n','RAS_RMSE','inverse_recovery_n','inverse_MAE_mass_fraction','inverse_RMSE_mass_fraction']])}

Leave-one-well-out predicts a new well at an already represented reference level; leave-one-reference-level-out tests interpolation across an omitted concentration. All technical/event resampling remains within its parent well. Neither is external validation with independently prepared blinded mixtures. The four 0%/100% endpoint wells cannot receive forward interpolation predictions when their whole level is held out; they are explicitly unavailable, giving 16 in-domain forward predictions. Inverse recovery has its own availability counts and is never scored after clipping.

Isotonic forward RMSE is 0.05073 in leave-one-well-out but 0.10710 in leave-one-level-out, versus affine 0.07804 and 0.09339. Thus fitting away within-level noise is not evidence of a reliable inverse. The affine leave-level inverse MAE is 0.07686 mass fraction (7.69 AC percentage points), among the 16 available recoveries; this excludes non-estimable cases and is not a universal accuracy specification. Formal affine lack-of-fit relative to within-level pure error is F(8,10)={cal['affine_lack_of_fit_F']:.2f}, p={cal['affine_lack_of_fit_p']:.3g}; its same-session independent-error assumptions and n=2 replication limit interpretation.

## The 75%/90% anomaly was retained and investigated
Source FCS tube labels, the original photograph and team-confirmed mass axis still identify 75/90/100; no independent record justifies relabeling 90. Both 90% well RAS values are below both 75% values. Mean green rises from about 80,000 to 181,000 a.u. and red rises from about 70,600 to 184,800 a.u.; the larger proportional red rise explains the ratio reversal arithmetically. It does not identify its preparation or biological cause. Counts, denominator precision, bright-event influence and time QC were examined. The reversal persists in **all 11** background/gate/threshold sensitivity scenarios. No S7 plate-reader workbook was present for an independent same-series check. S8 data were not imported to fill that gap.

## Inverse sets and uncertainty
Inversion is restricted to each model's fitted response range. Outside values remain unavailable rather than extrapolated or clipped. Isotonic exact plateaus have a set-valued inverse:

{md(iso[['RAS','exact_inverse_low','exact_inverse_high']])}

Thus low intervals 0–5%, 15–20%, 30–40%, and high 75–90% can be identical under this fitted monotonic model. Original well variability and model mismatch broaden ambiguity further. The endpoint values near 75% and 100% are also close empirically; a single model-assumed point can conceal that conflict.

One thousand stratified bootstraps resample the two wells within each level and propagate the stored paired-event/shared-control draws. The same control draw is preserved between reference and inverse observation within a replicate. This estimates uncertainty conditional on this small, fixed reference design; it omits mixture-preparation and batch uncertainty. In-range inverse draws receive conditional percentile intervals with the in-range fraction reported. Failed draws are not clipped or converted to zero; conditional intervals are not unconditional coverage guarantees.

A second, deliberately conservative diagnostic adds the empirical 95th percentile of absolute leave-level residuals to bootstrap mean-response bands and inverts the resulting response envelope. These **compatibility sets are not calibrated 95% confidence intervals**. Across the evaluated response grid, the narrowest set spans over 0.21 mass fraction for every model; none meets the prespecified exploratory width screen of ≤0.20. The numeric screen is not a validated assay specification. The present evidence therefore establishes **no validated RES domain**. `S7_RES_results.csv` retains model-specific exploratory inverses, plateaus, out-of-range states and uncertainty separately from blank `RES_validated`.

## S7-to-S10 transfer
HEK293T and the detector profile match. Reporter loading in S7, precise AC/INAC states/constructs, treatment/TMP, linked editor effects, and the reference-to-OpenA biological bridge remain unresolved. S7 reporter-population calibration is not qualified for R+B+-selected S10. Same-mode S10 reporter values are mapped only in a distinctly labelled hypothetical sensitivity table. No S10 co-expression score receives S7 RES, and no mapped value is promoted into biological PER.

Sources: `results/calibration/S7_model_comparison.csv`, `S7_calibration_predictions.csv`, `S7_internal_validation.csv`, `S7_parameter_bootstrap.csv`, `S7_inverse_identifiability.csv`, `S7_RES_results.csv`, anomaly tables and `S7_S10_compatibility.csv`. L23_07–10 show fits, residuals, ambiguity and the actual anomaly.
'''
    report('reports/Layer2_RES_Calibration.md',layer2)
    primary=pv[pv.model.isin(['training_mean','reporter_RAS','B_detection_fraction','editor_dose_log1p','reporter_RAS_plus_B'])]
    assoc=ass[(ass.unit=='well')&(ass.endpoint=='raw_signal_index')]
    layer3=header+f'''# Layer 3 — Biological Calibration and PER

## Qualified endpoint versus available endpoint
The intended endpoint is C280 edited fraction in OpenA reporter RNA at sampling, with C→U in the forward transcript. Sequence/codon support and parent-well mapping are now available. Quantitative RNA fractions are not: the actual measured cell population, DNA-exclusion controls, known-mixture assay response and absolute uncertainty remain unresolved. No endogenous or introduced APOE result is substituted.

The available numerical endpoint is a **raw direction-averaged C280 chromatogram composition index**, calculated within complete molecular-label pairs and then averaged within each well. It is neither a cell fraction nor a calibrated RNA fraction. The raw index avoids defining a held-out endpoint using all control wells' background; fitting an intercept makes its constant background shift irrelevant to the within-release association. The corrected index remains available for descriptive plots.

The final pairing table has 12 independent wells, each linked to 2 molecular labels and 4 original reads, reporter RAS, co-expression RAS where estimable, B-positive fraction, doses, technical uncertainty and assay status. There are only 10 defined editor co-expression RAS values, because no-editor R+B+ tails are not editor-expressing populations and fail the denominator screen. RNA population remains undocumented and is not assumed to be sorted R+B+.

## Observed relationship
{md(assoc[['predictor','n','pearson','spearman']])}

The index tracks editor dose and B-positive prevalence strongly within this dataset. It has weak negative association with reporter RAS and a negative association with co-expression RAS. These associations cannot establish causality, absolute RNA editing or a transferable model; they reveal that the present optical activity metric does not track the candidate-site chromatogram response as expected.

## Actual prediction attempts
Simple OLS models were fitted to the relative index: training mean only; reporter RAS alone; B-positive detection fraction alone; log(1+editor ratio); reporter RAS plus B fraction; and, on the same positive-dose subset, co-expression RAS and matched mean/B baselines. Models and bootstrap coefficients are saved. There is no hyperparameter tuning or hidden search over covariates. Additional B information is named explicitly; it does not redefine RAS or RES.

All technical labels/directions from each well stay together. Leave-one-well-out uses 11 wells (or 9 for the positive-dose subset). Leave-one-dose-out withholds both wells at that condition. Predictors outside training ranges are flagged; unconstrained signal-model predictions and model-based intervals are not clipped into a biological percentage. Ordinary t prediction intervals assume the fitted linear model and residual structure; their reported internal coverage is not assay accuracy or externally verified coverage.

{md(primary[['model','validation','well_n','RMSE','MAE','bias','prediction_interval_coverage']])}

For leave-one-dose-out, RAS-only RMSE **0.09015** is worse than the training-mean baseline **0.08380**. B-fraction-only RMSE is **0.01922**. Reporter RAS plus B gives **0.01981**, with no numerical advantage here over B alone. On the 10 positive-dose wells, co-expression-RAS RMSE is **0.09022**, versus its matched mean baseline **0.08492**. These are units of the relative chromatogram index, never percentage-point RNA editing errors. The small six-dose design, shared processing context and unqualified endpoint make all predictive results exploratory. Good dose-linked performance may largely encode the experimental titration rather than transferable mechanistic prediction.

## Direct versus staged interpretation
A staged `RAS→RES→RNA` model is **not fitted**: there is no validated S7-to-S10 calibration bridge or quantitatively qualified molecular fraction. Its result table states the exact reasons. A separate mathematical sensitivity maps reporter RAS through the fitted affine S7 inverse only where in range, then repeats the same linear-index prediction on identical held-out wells. Maximum direct/staged prediction difference is {ps['maximum_affine_transform_difference']:.3g}. An invertible affine rescaling supplies no new sample information; this algebraic comparison is not evidence of biological transfer and is not PER.

## Explaining the discordance without claiming a cause
The sequence signal, RAS and BFP answer different questions. RAS is red-expression-weighted within selected reporter events; RT-PCR/Sanger samples molecules from an undocumented population; B detection measures expression prevalence under a provisional threshold. Those differences can change weighting and dilute or enrich a signal. Reporter maturation, DD stability/TMP conditions, differences between locked AC/INAC references and edited OpenA, and optical spillover are additional hypotheses. The present experiment does not isolate them. The observed molecular/optical mismatch should be reported, not removed by tuning gates, replacing the RAS formula, or fitting a forced increasing predictor.

## Status and sources
**PER remains unavailable**, while site reconstruction, actual Sanger quantification and grouped relative-signal model evaluation are complete. `results/prediction/S10_flow_molecular_pairs.csv`, `S10_direct_model_results.csv`, `S10_prediction_validation.csv`, `S10_staged_model_results.csv`, `S10_affine_transform_sensitivity.csv`, and `S10_flow_molecular_associations.csv` provide the evidence. L23_11–12 show actual paired relationships and held-out predictions. No plot presents simulated RNA truth or a validated PER.
'''
    report('reports/Layer3_PER_Calibration.md',layer3)
    blockers=[
    ('Missing complete OpenA GenBank','Eight raw no-editor AB1, recorded primers, provisional FASTA','Assembled each of four F/R pairs without candidate template; compared only afterward','523 bp and all four assemblies agree; annotated amplicon exported','RESOLVED_FOR_CENTRAL_AMPLICON','Termini partly primer-derived; full clone not verified','Full plasmid no longer blocks site analysis'),
    ('Generic 544 versus 523 bp','Generic annotated design and independent consensus','Global alignment and base-level mapping','Net −21 bp with substitutions and complex indel representation','RESOLVED_LENGTH_AND_DIFFERENCE','Not proof of one simple deletion or exact full-clone identity','Use reconstructed amplicon for site analysis'),
    ('Candidate C280','Control base support, generic coding frame and reconstructed linker','Enumerated all cytidines and C→T codon consequences','C280 CGA→TGA is unique stop-gain candidate within linker; four F and four R support C','PARTIALLY_RESOLVED','Intended-target construction record not supplied','Site-specific exploratory signals supported'),
    ('F/R disagreement','48 traces; no-editor and positive doses','Per-file dye checks, baseline/max/area sensitivity, paired comparison','Signal rises in both directions; large scale discrepancy persists','INVESTIGATED_UNRESOLVED_BIAS','No known-mixture response calibration','No absolute RNA fraction'),
    ('Mixed 1-8-2.F','Original trace, mapped local sequence and vendor flag','Declared mapping/flank/quality screens','60% flank identity; retained in audit, excluded from site endpoint','RESOLVED_QC_ROUTING','One high-dose well has one complete molecular pair','Uncertainty unavailable at nested-label level for that well'),
    ('Secondary peaks versus RNA fraction','C280 and 139 other cytidines, controls, 12 wells','Computed raw/corrected peak composition and actual model fits','Editing-associated relative response quantified','PARTIALLY_RESOLVED','Dye/context bias and RNA/DNA origin of product unqualified','PER unavailable; relative index supported'),
    ('RNA sampling population','S10 text records, workbooks, photo and confirmed timing','Searched all available records and preserved pairing','Same-timepoint flow then RNA confirmed; cell selection not found','EXPERIMENTAL_EVIDENCE_MISSING','No bulk-versus-sorted population assignment','Cannot claim R+B+-conditioned RNA endpoint'),
    ('DNase/no-RT controls','All supplied S10 text/workbook material','Searched named terms and audited source files','No documentary hits found','EXPERIMENTAL_EVIDENCE_MISSING','Absence from records is not proof controls were not performed','Alternative peaks not uniquely attributable to RNA editing'),
    ('S7 75/90 reversal','Photos, FCS labels, both wells, raw means, counts and sensitivity','Retained identities; compared red/green weights and all 11 perturbations','Both wells reproduce reversal; red rises proportionally more; all sensitivities retain it','NUMERICALLY_EXPLAINED_CAUSE_UNRESOLVED','No S7 plate or independent preparation/batch evidence','Inverse sets broad; no validated RES domain'),
    ('AC/INAC plasmid lengths','Permitted general construct files','Read sequence lengths and annotations; checked exact identity links','No verified pair of exact S7 AC/INAC constructs','EXPERIMENTAL_EVIDENCE_MISSING','Generic lengths cannot establish reference molarity','Use confirmed mass axis only'),
    ('S7/S10 population transfer','Cell, dose, treatment, architecture and detector evidence','Explicit compatibility table','HEK293T/profile match; other required bridges unresolved','UNQUALIFIED_TRANSFER','Editor and R+B+ selection differ; S7 dose/treatment unknown','No staged biological PER; hypothetical reporter mapping separate'),
    ('Single-color compensation','36 original FCS, XML/config/XIT and labels','Audited all available controls and retained identity matrix','No matched single-color control acquisitions found','EXPERIMENTAL_EVIDENCE_MISSING','Do not infer coefficients from G/B associations','RAS and downstream fits stay detector-scale exploratory'),
    ('Independent batches','Manifest, FCS dates, team confirmation','Separated midnight acquisition dates from independent experiments','n=2 transfection wells/condition; one acquisition context','EXPERIMENTAL_EVIDENCE_MISSING','No external batch or laboratory validation','Internal validation only')]
    br=pd.DataFrame(blockers,columns=['blocker','evidence_examined','action','result','resolution','remaining_limit','consequence']);table('reports/layer23/blocker_resolution.csv',br)
    report('SONAR_Layer23_Blocker_Resolution.md',header+'# Blocker-resolution register\n\n'+md(br)+'\n\nThe record distinguishes a completed computational investigation from missing experimental evidence. None of the established sample metadata was requested again.')
    evidence=header+f'''# SONAR Layer 2–3 Scientific Evidence Report

## Findings to carry into scientific writing
The extension resolves the central OpenA-reference problem and performs the molecular and calibration analyses that were previously only feasibility audits. It supports a **523-bp candidate amplicon, a sequence-supported C280 stop-switch candidate, actual bidirectional chromatogram response, fitted S7 mass-reference models, and grouped optical-to-relative-molecular prediction tests**. It does not establish calibrated RNA-editing fractions, a validated RES domain or PER.

1. Four no-editor F/R reconstructions from two independent wells agree exactly at 523 bp. Accepted Q20 support covers 494 positions; 393 are supported in both directions. Terminal positions 1–14 and 509–523 are primer-derived at the declared quality level. C280 has eight accepted control calls and uniquely introduces a stop within the reconstructed EGFP–DHFR linker. Intended target identity remains provisional.
2. Of 48 Sanger reads, 47 pass site QC. The flagged `1-8-2.F` fails local sequence identity, not merely a vendor warning. Twenty-three complete technical pairs remain within 12 wells. C280 signal increases with dose; eligible equal-well F peak ratios rise from 0.04493 to 0.16354, and R ratios from 0.01584 to 0.28745. These are peak compositions, **not RNA editing percentages**.
3. Affine, isotonic and fixed-knot monotonic S7 fits were actually estimated and internally tested. Isotonic leave-well RMSE is 0.05073, but leave-level RMSE is 0.10710; affine values are 0.07804 and 0.09339. Isotonic plateaus and large discrepancy-aware inverse sets prevent a validated domain. Both 90% wells remain below both 75% wells under all 11 context sensitivities.
4. The paired molecular index follows B detection much more closely than RAS. At the well level, reporter RAS versus index has Pearson r=−0.288; B-positive fraction r=0.976. Leave-dose-out RAS-only RMSE 0.09015 is worse than the mean-only baseline 0.08380; B-only RMSE is 0.01922. This is a meaningful failure of the current RAS-only predictive relationship for the measured relative endpoint.
5. A staged biological model is not qualified because accurate RNA fractions and S7-to-S10 transfer are absent. An explicitly hypothetical affine-rescaling sensitivity reproduces direct predictions to numerical precision, illustrating that a deterministic invertible intermediate adds no data by itself.

## Dataset and experimental units
S7: 20 independent transfection wells, 10 confirmed AC mass levels, two wells per level. S10: 12 independent transfection wells, six editor doses, two wells per dose; 24 nested molecular labels and 48 F/R reads. Both experiments use user-confirmed HEK293T. Two shared Mock acquisitions are counted once. No independent culture-day or external batch replication is inferred. Established DNA doses, P2A linkage, 15% correction and 1/2→A, 3/4→B mapping remain intact. RNA was extracted after flow; elapsed minutes and sampled population are undocumented.

## What each layer now contributes
| Layer | Implemented contribution | Highest supported output |
| --- | --- | --- |
| 0 Context Calibration | Frozen FCS decoding, common gates/background, time QC, auditable masks | Reproducible same-session detector context; optical validation incomplete |
| 1 Flow Quantification | Unchanged signed linear paired ratio of sums; red-normalization repeatability; B dimension | Exploratory RAS; n=2 well repeatability; provisional co-expression interpretation |
| 2 Reporter Calibration | Three actual fits; grouped recovery; set-valued inverse; bootstrap and discrepancy analysis | Internally evaluated S7-specific exploratory mass equivalents; no validated RES domain |
| 3 Biological Calibration | Reconstructed candidate site; 48 trace analyses; 12-well molecular registry; grouped relative-index prediction | Editing-associated chromatogram response and exploratory associations; no calibrated RNA fraction or PER |

## Molecular evidence and uncertainty
{md(condition[['dose_ratio','well_n','F_raw_mean','R_raw_mean','signal_mean','signal_SD']])}

The raw chromatogram composition depends on direction, channel response and sequence context. Local baseline, nearby maxima and peak-area choices preserve the broad response, but cannot calibrate absolute accuracy. Nested-label uncertainty is estimated only when two complete labels are available. All folds keep the well's molecular reads together. Other cytidines also show dose-associated peaks; the screen is descriptive, and C280 is prioritized by sequence/codon context rather than response ranking.

No DNase/no-RT or sampled-population evidence was found in the searched supplied records. User-confirmed RNA extraction is retained; it is not silently downgraded to unknown. What remains unknown is whether the sequenced PCR mixture excludes residual DNA and corresponds to the selected flow population.

## Reporter fit and inverse evidence
{md(mc[['model','validation','RAS_prediction_n','RAS_RMSE','inverse_recovery_n','inverse_MAE_mass_fraction']])}

The 75/90 discrepancy exceeds ordinary within-level dispersion and persists after computational perturbation. Increased mCherry relative to green explains the lower ratio but not its biological/preparation origin. Model-specific smooth inverse values can still be computed, but they are conditional on assumptions not validated by the reference ladder. Isotonic models expose literal plateaus; discrepancy-aware sets are broad even for affine/hinge fits. The 20-percentage-point width screen identifies no narrow domain and is explicitly a diagnostic, not a retrospective success criterion.

## Direct prediction evidence
{md(primary[primary.validation=='leave_one_dose_out'][['model','well_n','RMSE','MAE','bias','prediction_interval_coverage']])}

The endpoint is raw chromatogram signal index. These errors cannot be reported as RNA-editing percentage errors. Model-based prediction intervals and fixed-error bootstrap summaries characterize internal behavior, not independent assay or external validation. BFP may primarily encode the editor-dose titration; this experiment alone does not show generalization to another editor, reporter, treatment, batch or population. Adding RAS to B provides no observed improvement. A valid four-layer framework must expose this discordance, not force positive calibration.

## Generalizable measurement contribution
The transferable contribution is methodological: maintain linear paired-channel estimators, preserve negative background-corrected signals, verify channel identity, retain explicit population definitions, preserve nested experimental units, invert calibrations as sets where needed, separate fit from validation, and qualify the molecular endpoint independently. The particular gates, gain scales, S7 curves, C280 trace responses and index predictors are reporter/session specific and have no demonstrated universal transfer.

## Source map and reproduction
Molecular reconstruction and exact methods: `reports/OpenA_Amplicon_Reconstruction.md` and `reports/S10_Sanger_Quantification.md`. Reporter models/inverses: `reports/Layer2_RES_Calibration.md`. Prediction: `reports/Layer3_PER_Calibration.md`. Blockers: `SONAR_Layer23_Blocker_Resolution.md`. The twelve diagnostic figures and captions are indexed by `SONAR_Layer23_Figure_Evidence_Inventory.md`; each reads real exported tables. All model parameters, fold memberships and unavailable states are saved under `models/layer23/` and `results/`.

The previous release is preserved in `baselines/v2/`. Its source/configuration/RAS matches the supplied archive; 58 saved context/mask/result artifacts reproduced exactly before extension. The current `python reproduce.py --verify` includes the extension, tests, all nested numeric tables, fitted-model JSON and all PNGs. The executed result—not this instruction—is recorded in `reports/reproducibility_record.json`. The upstream RAS file and kernel hashes are pinned; a change invalidates calibration execution. No upstream estimator, gate or background was altered to improve downstream results.
'''+references
    report('SONAR_Layer23_Evidence_Report.md',evidence)
    zh=header+'''# SONAR Layer 2–3：中文科学摘要

本轮已完成实际序列重建、48 条峰图定量、S7 三种校准模型拟合与内部验证，以及 S10 按独立孔分组的预测检验。v2 已归档；Layer 0–1 的门控、背景和 RAS 数值保持不变。

**OpenA 的核心序列障碍已解决。** 四组无 editor 的双向读段分别拼接，均得到同一条 523 bp 序列，与候选 FASTA 一致。严格质量筛选后，494 个碱基有 Q20 支持，其中 393 个同时有正反向支持；两端 29 个位置由引物补足。C280 是连接区内唯一可由 C→T 产生终止密码子（CGA→TGA）的胞嘧啶位点，具有明确序列与机制支持；“原设计指定靶点”仍缺独立构建记录。

**测到了剂量相关的 C280 峰图响应，但尚不是准确 RNA 编辑率。** 48 条读段中 47 条通过位点质控。`1-8-2.F` 的目标邻域序列一致性只有 60%，因此保留原图、排除其位点定量；不能只依据其混峰备注，也不能将错配位置的比例纳入平均。24 个分子标签得到 23 组完整 F/R 配对，仍仅代表 12 个独立转染孔。正向峰比例由无 editor 的 0.0449 升至最高剂量的 0.1635，反向由 0.0158 升至 0.2874。方向差异没有被局部背景校正消除，缺少已知混合标准和 DNA 残留排除记录，不能把这些值乘 100 后称为编辑率。

**S7 已真正拟合，但不能宣称 RES 校准成功。** 采用仿射、单调等距回归及固定 50% 折点的单调分段线性模型。等距模型“留一孔”RMSE 为 0.0507，“留一浓度”升到 0.1071；仿射为 0.0780、0.0934。单调模型在 0–5%、15–20%、30–40%、75–90% AC 质量区间产生平台。纳入模型偏差后逆推范围很宽，没有建立可靠的 RES 适用区间。每个模型的探索性逆值、区间、越界和不可识别状态已输出，均未冒充已验证 RES。

**75%→90% 反转不是此次门控造成的。** 两个 90% 孔都低于两个 75% 孔；11 种门控/背景/阈值敏感性方案均保留反转。90% 绿色增强，但红色增幅更大，因此 G/R 降低。这解释了数值来源，尚不能确定配制或生物原因；没有擅自改标签或删除 90%。

**最关键的新结论：当前 RAS 未能预测这个分子信号。** 12 孔中，RAS 与峰图指数 Pearson r=−0.288，B+ 比例与指数 r=0.976。留出整个剂量条件时，RAS 单变量预测 RMSE 为 0.0902，比仅使用训练集均值的 0.0838 更差；B+ 单变量为 0.0192。加入 RAS 后没有改善。这些是相对峰图指数单位的误差，不是编辑率误差；BFP 的表现也可能主要反映本次 editor 剂量梯度。

**PER 仍不可报告，但原因已经具体化。** 同孔配对和流式后提 RNA 已确认；尚缺准确分子比例、RNA 所取细胞群体及 S7→S10 的有效校准桥接。因此未强行拟合生物学分阶段 PER。另行检验了仿射 RES 变换的数学影响：与直接线性模型预测相同，说明可逆重标度本身不会增加样本信息。

主要交付：英文证据报告 `SONAR_Layer23_Evidence_Report.md`；阻塞项处理登记 `SONAR_Layer23_Blocker_Resolution.md`；逐层方法在 `reports/`；实际模型和分组验证表在 `models/layer23/`、`results/`；12 张新的诊断图及证据清单在 `figures/layer23/`。本轮未制作最终 Wiki 页面或发表级配图。
'''
    report('SONAR_Layer23_Scientific_Summary_ZH.md',zh)
    figure_numbers={
        'L23_01_reference_support':'523 bp; 494 Q20-supported positions; 393 bidirectional; 29 primer-inferred terminal bases; C280',
        'L23_02_bidirectional_traces':'Four illustrated original traces: 1-0-1 F/R and 1-8-1 F/R; target at forward coordinate 280',
        'L23_03_flagged_read':'1-8-2.F flank identity 0.60 versus declared 0.90 gate; 47/48 total reads eligible',
        'L23_04_molecular_response':f'12 wells; high-dose corrected index {condition.iloc[-1].signal_mean:.6f}; F raw {condition.iloc[-1].F_raw_mean:.6f}; R raw {condition.iloc[-1].R_raw_mean:.6f}',
        'L23_05_direction_agreement':'23 complete F/R label pairs nested within 12 wells; 1 incomplete pair retained as unavailable',
        'L23_06_cytidine_screen':'140 cytidines screened; 15 pass the descriptive both-wells/both-directions high-dose-versus-control screen; not multiplicity-adjusted',
        'L23_07_S7_models':'20 wells, 10 AC mass levels; affine leave-level RMSE 0.093390; isotonic 0.107098; hinge 0.097955',
        'L23_08_S7_residuals':f'Affine pure-error lack-of-fit F(8,10)={cal["affine_lack_of_fit_F"]:.5f}; p={cal["affine_lack_of_fit_p"]:.4g}',
        'L23_09_inverse_uncertainty':'Isotonic plateaus: 0–5%, 15–20%, 30–40%, 75–90% AC mass; narrowest discrepancy-aware set exceeds 21 percentage points in each model',
        'L23_10_reference_anomaly':'Both 90% RAS values below both 75% values; reversal preserved in all 11 tested context sensitivities; histograms contain 6 original gated wells',
        'L23_11_flow_molecular_association':'Well-level Pearson r: RAS −0.288178, B-positive fraction 0.976424; co-expression RAS −0.528642 (n=10)',
        'L23_12_internal_prediction':'Leave-dose RMSE: mean 0.083797, RAS 0.090155, B fraction 0.019219; index units, not RNA fraction units'}
    fig['supporting_dataset']=np.where(fig.figure_id.str.contains('L23_0[789]|L23_10'),'S7 AC/INAC independent transfection wells','S10 OpenA independent wells with nested molecular labels')
    fig['numerical_findings']=fig.figure_id.map(figure_numbers)
    table('reports/layer23/figure_evidence_inventory.csv',fig)
    finv=header+'# Layer 2–3 figure evidence inventory\n\nAll figures are analytical diagnostics, exported as PNG and editable SVG. No simulated or external observations are shown. The caption states the scientific message and limitations; the numerical column identifies the observed evidence.\n\n'+md(fig[['figure_id','supporting_dataset','source_tables','numerical_findings','caption','status']])
    report('SONAR_Layer23_Figure_Evidence_Inventory.md',finv)
    # Preserve the prior Layer 0/1 narrative verbatim, replace superseded feasibility-only layers.
    existing=(ROOT/'SONAR_Measurement_Evidence_Report.md').read_text();start=existing.find('## Layer 0: context calibration');end=existing.find('## Layer 2:',start)
    earlier=existing[start:end] if start>=0 and end>start else 'Layer 0–1 methods and unchanged results remain in their detailed reports.\n'
    report('SONAR_Measurement_Evidence_Report.md',header+'# SONAR Integrated Measurement Evidence Report\n\n'+evidence.split('## Dataset and experimental units')[0].split('# SONAR Layer 2–3 Scientific Evidence Report\n\n')[1]+'\n'+earlier+'\n## Layer 2: Reporter Calibration\n\nThree actual S7 mass-axis models, grouped validation and inverse uncertainty are complete. Internally evaluated exploratory mass-equivalent values are available; no validated RES domain is established. See [Layer 2 report](reports/Layer2_RES_Calibration.md).\n\n## Layer 3: Biological Calibration\n\nOpenA523/C280 reconstruction, bidirectional peak analysis and 12-well signal prediction are complete. RAS does not outperform a mean-only predictor for the available relative endpoint. Accurate RNA fractions, cross-population transfer and PER remain unqualified. See [Layer 3 report](reports/Layer3_PER_Calibration.md).\n\n## Full scientific handoff\n\n[Layer 2–3 evidence report](SONAR_Layer23_Evidence_Report.md), [Chinese summary](SONAR_Layer23_Scientific_Summary_ZH.md), [blocker resolution](SONAR_Layer23_Blocker_Resolution.md), and [figure evidence inventory](SONAR_Layer23_Figure_Evidence_Inventory.md). Earlier feasibility-only reports are retained as v2 historical context; the new actual analysis supersedes their statements that models were not fitted.')
    # Clearly mark retained v2 documents so their earlier blockers cannot be mistaken for current findings.
    for name in ['Layer2_Reporter_Calibration_Feasibility.md','Layer3_Biological_Calibration_Audit.md','Executive_Summary.md','Data_Inventory_and_Reconciliation.md']:
        p=ROOT/'reports'/name;text=p.read_text();banner='> Historical v2 record, preserved for provenance. Superseded by the actual v3 analyses in `Layer2_RES_Calibration.md`, `Layer3_PER_Calibration.md` and the root Layer23 evidence report. HEK293T is now user-confirmed; OpenA reconstruction and exploratory fitting have been completed.\n\n'
        if not text.startswith('> Historical v2'):p.write_text(banner+text)
    report('README.md',f'''# SONAR S7/S10 integrated analysis — v3

Start with [中文科学摘要](SONAR_Layer23_Scientific_Summary_ZH.md), [English scientific evidence](SONAR_Layer23_Evidence_Report.md), and [integrated four-layer report](SONAR_Measurement_Evidence_Report.md).

Release `{VERSION}` extends the existing project. The upstream Layer 0–1 version stays `{CFG['upstream_analysis_version']}` with identical RAS bytes, estimator, gates and background. The prior complete release and verification records are preserved under `baselines/v2/`; no other experimental series was added. User-confirmed HEK293T metadata is applied to experimental sample manifests.

The extension contains independently reconstructed OpenA523 reference/alignment evidence; 48-read Sanger processing and 12-well relative molecular results; three fitted S7 mass-calibration models, internal validation and explicit inverse sets; and grouped S10 relative-index prediction models. Validated RES and RNA-editing PER remain unavailable. Model and assay qualification are explicit in every relevant table/report.

## Main outputs
- `results/molecular/`: consensus FASTA/annotated GenBank/alignment, per-base support, read metrics, 24-label and 12-well summaries, source audit.
- `results/calibration/`: fits, residuals, grouped recovery, bootstrap uncertainty, inverses, anomaly and S7/S10 compatibility.
- `results/prediction/`: paired wells, actual exploratory models and held-out predictions, explicit unavailable staged biological model.
- `models/layer23/`, `config/layer23.json`: serialized model coefficients/thresholds and frozen choices; upstream hashes prevent silent incompatibility.
- `figures/layer23/`: 12 new data-driven diagnostics in PNG/SVG with source hashes. Existing 13 Layer 0–1 diagnostics remain.
- `reports/`: detailed scientific methods and executed tests/reproduction records. `SONAR_Layer23_Blocker_Resolution.md` documents actual resolution attempts.
- `reference/layer23/`: supplied request, provisional files and permitted generic construct records, preserved as sources.
- `baselines/v2/`: preserved prior release and exact-output baseline verification. `_work/` is disposable working material.

## Reproduce
Use Python 3.13 with the pinned packages in `requirements.txt`:

```text
python reproduce.py --verify
```

The complete command regenerates Layers 0–3, runs the scientific tests, performs an isolated second run, and compares all nested numerical result tables, event masks, model JSON and PNG pixels. For only the extension after a verified unchanged upstream run: `python reproduce.py --layer23-only`. On this host the prepared interpreter is `_work/venv/bin/python`. No internet or external project paths are needed after installation; packaged input hashes are verified. The current run's actual checks appear in `reports/reproducibility_record.json` and `reports/test_results.txt`.

All peak fractions are chromatogram metrics until separately qualified; AC DNA mass fractions are reference inputs, not RNA edits. No final Wiki page, publication figure or synthetic validation dataset is included.
''')
    # Publish a concise machine-readable layer status and source inventory.
    table('results/prediction/SONAR_layer_status.csv',[dict(layer=0,name='Context Calibration',highest_output='same_session_context',qualified=False,limit='optical_controls_missing'),dict(layer=1,name='Flow Quantification',highest_output='exploratory_RAS',qualified=False,limit='optics_and_LOQ_unvalidated'),dict(layer=2,name='Reporter Calibration',highest_output='internally_evaluated_exploratory_mass_equivalent',qualified=False,limit='broad_inverse_nonidentifiability_no_external_reference_validation'),dict(layer=3,name='Biological Calibration',highest_output='candidate_site_signal_and_grouped_relative_index_models',qualified=False,limit='RNA_fraction_assay_and_population_transfer_unqualified')])
    decisions=pd.read_csv(ROOT/'reports/decision_registry.csv');decisions['analysis_version']=VERSION
    updates={'D01':('partially_resolved','OpenA523 reconstructed independently; full AC/INAC/OpenA/editor construct identities remain unverified'),'D07':('exploratory_models_fitted','Three actual S7 models and grouped validation completed; model-specific inverse sets exported; no validated RES domain'),'D09':('partially_resolved','OpenA523 candidate C280 reconstructed; 48 reads processed, 47 site-eligible, 23 complete pairs within 12 wells; absolute RNA assay and sampled population unqualified'),'D10':('relative_models_evaluated_PER_unavailable','Grouped relative-index prediction evaluated; RAS does not beat mean baseline; B covariate is exploratory; staged RNA PER unavailable')}
    for key,(status,limit) in updates.items():decisions.loc[decisions.decision_id==key,['status','evidence_or_limit']]=[status,limit]
    table('reports/decision_registry.csv',decisions)
    register=pd.read_csv(ROOT/'reports/evidence_register.csv');register=register[~register.evidence_id.astype(str).str.startswith('L23_')].copy()
    register.loc[register.evidence_id=='E04',['result_table','limitations']]=['results/calibration/S7_inverse_identifiability.csv','Three models fitted and internally evaluated; wide/nonunique inverse and no qualified external reference calibration']
    register.loc[register.evidence_id=='E05',['result_table','limitations']]=['results/molecular/S10_well_level_molecular_results.csv','Candidate C280 reconstructed; RNA origin and well pairing confirmed; residual DNA controls, sampled population and quantitative assay validation unresolved']
    additions=[]
    for eid,claim,tab,figid,n,limit in [('L23_01','OpenA523 independently reconstructed from four no-editor pairs; C280 candidate in linker','molecular/OpenA_reference_alignment.csv','L23_01_reference_support',2,'29 primer-terminal positions lack Q20 support; intended target provisional'),('L23_02','Dose-associated relative C280 signal; 47 eligible reads and 23 complete technical pairs','molecular/S10_well_level_molecular_results.csv','L23_04_molecular_response',12,'Peak composition is not calibrated RNA fraction; direction bias persists'),('L23_03','Three fitted S7 mass-axis models; no validated inverse domain','calibration/S7_model_comparison.csv','L23_07_S7_models',20,'Internal n=2 wells per level; no independent batch validation'),('L23_04','RAS fails to beat mean baseline in grouped prediction of available molecular index','prediction/S10_direct_model_results.csv','L23_12_internal_prediction',12,'Relative chromatogram endpoint; B-dose confounding; no PER')]:
        additions.append(dict(evidence_id=eid,status='supported_exploratory',claim=claim,source_files='inputs/S7;inputs/S10;reference/layer23',input_hashes='inventory/input_files.csv;reference/layer23/source_manifest.json',sample_ids='results/prediction/S10_flow_molecular_pairs.csv' if 'molecular' in tab or 'prediction' in tab else 'inventory/acquisition_manifest.csv',population_mode='explicit_flow_population_molecular_population_unknown',independent_n=n,context_id='contexts/context.json',estimator_id=CFG['upstream_analysis_version'],calibration_id=VERSION,result_table='results/'+tab,figure_id=figid,uncertainty_definition='See layer-specific methods; internal and conditional only',limitations=limit,review_date='2026-10-13'))
    table('reports/evidence_register.csv',pd.concat([register,pd.DataFrame(additions)],ignore_index=True))
    for filename in ['SONAR_中文科学摘要.md']:
        p=ROOT/filename
        if p.exists() and not p.read_text().startswith('> Historical v2'):
            p.write_text('> Historical v2 summary. Current integrated findings: [v3 中文科学摘要](SONAR_Layer23_Scientific_Summary_ZH.md).\n\n'+p.read_text())
    print('Integrated Layer23 scientific reports generated',flush=True)

if __name__=='__main__':run()
