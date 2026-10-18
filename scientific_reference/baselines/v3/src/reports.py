"""Scientific handoff documents generated from this reconstruction's tables."""
from pathlib import Path
import json,shutil
import numpy as np,pandas as pd
from inventory import ROOT,write_csv,sha

def read(n):return pd.read_csv(ROOT/'results'/f'{n}.csv')
def md(d):
    def f(v):
        if pd.isna(v):return 'unavailable'
        if isinstance(v,(float,np.floating)):return f'{v:.5g}'
        return str(v).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(f(v) for v in row)+' |' for row in d.itertuples(index=False,name=None)])
def write(name,text):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')

def run():
    cfg=json.loads((ROOT/'config/analysis.json').read_text());ver=cfg['analysis_version']
    r=read('ras_results');pr=r[r.population_mode=='reporter'];s7=pr[pr.series=='S7'];s10=pr[pr.series=='S10'];ret=read('event_retention');bg=read('background_thresholds');transfer=read('negative_transfer');resp=read('response_summary');influence=read('high_expression_influence');ip=influence[influence.population_mode=='reporter'];sens=read('sensitivity');rep=read('repeatability');mol=pd.read_csv(ROOT/'inventory/molecular_reads.csv');blue=read('blue_profiles')
    cv=rep[rep.population_mode=='reporter'].pivot(index=['series','condition_label'],columns='metric',values='cv_percent');cvtable=cv.groupby(level=0).median().reset_index();cvtable['pairs_improved']=[int((cv.loc[s].ras<cv.loc[s].mean_G_raw).sum()) for s in cvtable.series];cvtable['pair_n']=[len(cv.loc[s]) for s in cvtable.series]
    sr=s7.groupby('condition_label').ras.mean();tr=s10.groupby('condition_label').ras.mean();bf=s10.groupby('condition_label').blue_positive_fraction_reporters.mean()
    sens=sens.merge(pr[['acquisition_id','ras']],on='acquisition_id',suffixes=('_alternative','_primary'));sens=sens[sens.population_mode=='reporter'];sens['relative_percent']=100*(sens.ras_alternative/sens.ras_primary-1);st=sens.groupby('scenario').relative_percent.agg(['min','max']).reset_index()
    bootstrap_convergence=max(((pr.bootstrap_half_low-pr.event_ci_low).abs()/(pr.event_ci_high-pr.event_ci_low)).max(),((pr.bootstrap_half_high-pr.event_ci_high).abs()/(pr.event_ci_high-pr.event_ci_low)).max())
    header=f'Analysis version: `{ver}`. Review date: {cfg["review_date"]}. Authorized experimental series: S7 and S10 only. All numerical results below were regenerated from copied original inputs.\n\n'
    limits='''All fluorescence scores in this release are **exploratory detector-scale RAS**. The stored compensation matrix is identity and `USCOMP=False`; no matched single-color controls establish negligible spillover. Mock-derived boundaries have only acquisition-level negative-transfer checks. User metadata confirms independent A/B transfection wells, S7 AC mass fractions (source label 10 means 15%), S10 doses and ORCA–P2A–BFP linkage, and molecular labels 1/2→A and 3/4→B with RNA extracted after flow at the same experimental time point. Exact AC/INAC states, sequence-level construct identity, sampled RNA population and molecular assay qualification remain unresolved. These restrictions are separate from successful numerical computation. Validated RAS, RES and PER fields remain unavailable; unavailable never means zero.'''
    layer0=header+f'''## Scientific question
Can one declared measurement context support consistent processing of the supplied flow acquisitions?

## Implemented method and experimental evidence
There are 36 FCS files, 34 unique event acquisitions and 3,400,000 unique events. S7 contributes 20 experimental acquisitions; S10 contributes 12; two Mock acquisitions are shared byte-identical files across directories. They are counted once. No additional biological replicates are inferred. All files have 100,000 events and the same CytoFLEX S serial AS52073 optical profile, with GFP/PB450/mCherry gains 50/1/400. Acquisition crossed midnight on 2026-09-23/24; this is one contiguous session, not independent day replication.

FlowIO 1.4.0 reads native FCS3.0 list-mode 32-bit little-endian floating-point data. Area channels FL1-A, FL6-A and FL11-A map through FCS descriptions to GFP-A, PB450-A and mCherry-A. PnE=0,0 and PnG=1 for all parameters. Preprocessing changes only Time by TIMESTEP=0.00002 seconds per unit. An independent NumPy byte decoder agrees exactly on every event in all 36 file copies. Hardware gain is not divided out; these remain instrument-specific a.u. The identity matrix is verified and preserved as a no-op, without claiming optical compensation has been validated. Original data, linear values and display-transformed coordinates are distinct. Display data are sampled only for plots.

MOCK1 alone trains a robust MCD ellipse on log10(FSC-A, SSC-A), using support fraction 0.8 and a fixed random subset of 8,000 events. The accepted squared distance is chi-square(2) 0.99 = 9.21034. This is a transparent geometric choice, not a statistical proof that 99% of cells are retained. The singlet gate uses log10(FSC-A/FSC-H) within three normalized MADs of the MOCK1 center. Exact fitted values are in `contexts/context.json`. MOCK2 tests transfer of that geometry. The bright response groups never choose the gates. No viability dye is present; populations are described as scatter-selected, singlet-like events.

Per acquisition, finite positive scatter and finite nonnegative time are required. Complete one-second bins are flagged if their rate differs from the median by more than six times max(normalized MAD, sqrt(median rate), 0.1 x median rate). The last partial bin is not rate-tested. Time reversals are flagged. Only rate-outlier bins are removed. This cannot diagnose all clogs or population drift; time-bin scatter and fluorescence summaries remain auditable.

## Actual results
The Mock singlet retentions are {ret[ret.acquisition_id.str.contains('MOCK')].retained_fraction.min()*100:.3f}% and {ret[ret.acquisition_id.str.contains('MOCK')].retained_fraction.max()*100:.3f}%. Experimental singlet retention spans {ret[~ret.acquisition_id.str.contains('MOCK')].retained_fraction.min()*100:.2f}–{ret[~ret.acquisition_id.str.contains('MOCK')].retained_fraction.max()*100:.2f}%. The rate rule removes 4,320 events from `S10_1_1_B`; other acquisitions retain all events at that step. No time reversals or malformed/nonfinite events are observed.

{md(bg[['control_id','channel','mean_linear','sd_linear','quantile_995','used_background','used_threshold']])}

Background subtraction uses the equally weighted arithmetic means of the two control acquisitions in linear units. Positivity uses the larger of the two within-control 99.5th percentiles. These are separate operations. The candidate red quantification boundary is max(red positivity threshold, mean background + 3 background SD); here it equals {bg[bg.channel=='mCherry'].used_threshold.iloc[0]:.3f} a.u. This is a provisional screen, not a measured limit of quantification.

{md(transfer[['training_control','test_control','channel','test_positive_fraction']])}

The cross-control positivity rates span {transfer.test_positive_fraction.min()*100:.3f}–{transfer.test_positive_fraction.max()*100:.3f}%. Each transfer calculation derives a threshold from the other acquisition. The final maximum-of-two threshold uses both controls and therefore has no third held-out negative validation sample. Differences in mean EGFP background are about 4.7% relative to their equal-weight mean. This is small control drift in this session, not between-day reproducibility.

Native fluorescence ranges and maxima are exported for every channel. Area values occasionally exceed PnR (maximum observed fractions: EGFP 0.004%, red 0.005%); no repeated-maximum pileup is observed in fluorescence area channels (each maximum occurs once). PnR is not independently established as the analog clipping boundary, so these excursions are flagged rather than deleting bright cells or declaring saturation absent. No optical standard or absolute molecule-unit conversion is documented.

## Interpretation and limits
{limits}

The data support computationally reproducible, consistent geometry and approximate negative-background transfer within the recorded session. They do not establish viable-cell specificity, multicolor optical validity, an empirical red LOQ, independent control-well repeatability or cross-instrument transfer.

## Source tables and figure opportunities
`inventory/acquisition_manifest.csv`, `inventory/channel_metadata.csv`, `inventory/reader_crosscheck.csv`, `results/event_retention.csv`, `results/background_thresholds.csv`, `results/negative_transfer.csv`, `results/time_qc.csv`, and `masks/*.npz`. Diagnostics F01–F03 show control gates, background and retention. F07 shows perturbation sensitivity. Source-table links and captions are in `figures/figure_index.csv`.
'''
    write('reports/Layer0_Context_Calibration.md',layer0)
    layer1=header+f'''## Scientific question
What can paired red and green fluorescence quantify, and does continuous red normalization reduce observed variation?

## Implemented quantity
For exactly the same selected events, `g = GFP-A - mean Mock GFP-A` and `r = mCherry-A - mean Mock mCherry-A`; **RAS = sum(g) / sum(r)**. Accumulation is float64 on linear values. It is also a red-weighted mean of per-event g/r when r>0. It is not the arithmetic mean of cell ratios, a percentage of edited cells, or the fraction of edited RNA. mCherry normalization can remove a shared expression scale under proportionality assumptions; it does not remove differential maturation, stability, detector effects, or substrate-loading biology.

The primary population is the common quality/scatter/singlet population with red above the candidate quantification boundary. There is no EGFP-positive gate. Signed corrected green values are retained; {pr.signed_green_negative_fraction.min()*100:.2f}–{pr.signed_green_negative_fraction.max()*100:.2f}% of selected events have negative corrected green in these acquisitions. No epsilon, winsorization, independent channel clipping or sample-specific fluorescence gate is used.

A numerical score requires at least 100 selected events and a positive red denominator whose conditional event-sampling relative standard error is at most 10%. Those are declared provisional engineering screens, not empirically validated assay specifications. They do not resolve optical uncertainty. All 32 reporter populations meet this numerical screen: selected counts {int(pr.n_selected.min()):,}–{int(pr.n_selected.max()):,}, red effective counts {pr.effective_red_events.min():.0f}–{pr.effective_red_events.max():.0f}, and maximum relative denominator SE {100*pr.denominator_relative_se.max():.2f}%. Effective events are weight-concentration diagnostics, never biological n.

## Per-acquisition primary results
Raw and corrected means refer to the same reporter-selected population. An all-singlet raw-green mean is exported separately. Fluorescence units are linear detector a.u.; RAS is a green/red detector-channel ratio.

{md(pr[['acquisition_id','n_selected','mean_G_raw','mean_G_corrected','mean_R_corrected','ras','event_ci_low','event_ci_high']])}

## Does mCherry normalization improve repeatability?
The user confirms A/B are two independent transfection wells under each condition. The following calculation is **within-experiment independent-transfection-well repeatability (n=2 per condition)**. Independent cultures, days and batches have not been established. Each CV uses only the two wells at the same condition: sample SD with ddof=1 divided by absolute mean, times 100. Different AC fractions or editor ratios are never treated as replicates. Each condition contributes equally to the median across conditions. Raw-green and RAS CVs use the same selected events.

{md(cvtable)}

S7 improves in 8/10 pairs; S10 improves in 5/6. S7 labels 40 and 100 and S10 label 0.5 have higher RAS CV than raw-green CV. Normalization reduces between-well dispersion in most conditions but does not establish biological accuracy, a universal advantage or removal of all expression dependence. Exact pair values, including unfavorable cases, are in `results/repeatability.csv`.

Within common red-intensity bins, RAS changes across the reporter-expression range. Those strata confound expression, cell state, noise and possible substrate effects; they are not randomized reporter-load experiments. S7/S10 contain no verified locked-state reporter-dose series that isolates these mechanisms. Do not claim perfect dose invariance.

## What BFP adds
S10 B-positive fractions among reporter-selected events increase from {100*bf.loc[0]:.2f}% at label 1:0 to {100*bf.loc[8]:.2f}% at 1:8 using the Mock boundary. This is an observable detection dimension. The no-editor-labelled reporter acquisitions themselves have about 1.2% B-positive events, exceeding the nominal 0.5% Mock tail. A reporter-only-derived alternative B threshold of 1,109.878 a.u. changes these fractions; at 1:8 the average is about 37.32%. This demonstrates why Mock alone does not validate the multicolor B boundary.

The program separately calculates reporter, blue-positive reporter and blue-negative reporter populations for S10. The user confirms ORCA–P2A–BFP linkage for this S10 experiment. For editor-present conditions, blue-positive reporter populations are therefore routed as exploratory reporter/editor co-expression populations. This is experimental metadata confirmation, not sequence verification or validation of the B-positive optical boundary. `CEF_editor_exploratory` reports the B+ fraction among reporter-eligible events; `CEF_editor_verified` remains unavailable because the boundary is not validated. The zero-editor B+ tail is a negative-control diagnostic and is not an editor co-expression fraction. S7's BFP-related preparation annotation does not establish editor linkage, so it is not routed into editor co-expression mode. In the 1:0 group, blue-positive scores are unavailable because denominator relative SEs are approximately 15.9% and 21.0%, despite 262 and 241 events. They are not replaced by zero.

For positive ratio labels, the blue-selected RAS means are:

{md(resp[(resp.series=='S10')&(resp.population_mode=='blue_positive_reporter')][['condition_label','ras_mean','ras_sd','acquisition_n']])}

Neither the overall reporter score nor the blue-selected score increases monotonically with editor-ratio label. BFP cannot be read as exact active-editor abundance or increasing editing efficiency. The red-share-weighted decomposition of blue-positive/negative populations reconstructs reporter RAS to floating-point precision; the weight is red signal, not the cell-count fraction.

Common B+ bins were built from the intersection of 5th–95th percentile supports across all ten positive-ratio acquisitions. They retain {int(blue.n_selected.min())}–{int(blue.n_selected.max())} events per bin, but {int(blue.ras.isna().sum())}/{len(blue)} bins fail the denominator/count screen. There is no complete quantitatively accepted common-bin grid, so no standardized BFP-matched aggregate is reported. The incomplete profiles are useful diagnostics only.

## Uncertainty, robustness and bright-cell influence
There are 2,000 paired-event bootstrap draws per available population. Pointwise 95% intervals condition on the acquisition, fixed gate and background policy. A second interval includes Gaussian uncertainty of the control means with their paired green/red covariance; the same control perturbation draw is shared across acquisitions. This does not include biological variability, control-well/batch uncertainty, gate estimation, optical spillover or molecular calibration. The maximum reporter-population endpoint shift between the first 1,000 and all 2,000 draws is {100*bootstrap_convergence:.2f}% of the full interval width, documenting Monte Carlo stability at the precision reported. Full draws are exported. Independent biological confidence intervals are unavailable.

Event-count sensitivity uses 100 subsamples without replacement at supported sizes 100, 500, 1,000, 5,000, 10,000 and 20,000. It estimates finite-acquisition sampling sensitivity; an interval at the full event count would collapse and must not be called biological precision.

{md(st)}

These relative changes are percentages. Gate variants refit the corresponding control background and thresholds but preserve the same fixed scatter geometry; this tests the full perturbed context. Background variants keep events fixed. Median background and no subtraction are explicitly alternative estimands/sensitivity references, not selected policies. Switching between the two control means changes primary RAS by no more than about 0.12%; the largest tested geometric perturbation changes it by about 1.64%. A small perturbation effect does not validate unknown spillover.

The top 1% of red-expressing events contribute {100*ip.top_one_percent_red_share.min():.2f}–{100*ip.top_one_percent_red_share.max():.2f}% of total red signal. Removing them would change RAS by {100*ip.relative_change_without_top_one_percent.min():.2f}–{100*ip.relative_change_without_top_one_percent.max():.2f}%; they remain in the primary estimator. The largest one-event leave-out change is {ip.max_leave_one_out_change.max():.5f} RAS units. This concentration is scientifically relevant even though no single event dominates the main reporter populations.

## Interpretation domain and remaining limits
{limits}

RAS is useful here as a declared population-level reporter response in one instrument context. Claim conditional robustness and within-experiment independent-transfection-well repeatability improvement in most conditions. No evidence establishes RNA-editing accuracy, independent-culture or cross-day reproducibility, or a universal editor ranking.

## Source tables and figure opportunities
`ras_results.csv`, `repeatability.csv`, `bootstrap_draws.csv`, `event_count_sensitivity.csv`, `sensitivity.csv`, `high_expression_influence.csv`, `red_profiles.csv`, `blue_profiles.csv`, `B_negative_transfer.csv`, `binary_populations.csv` and `partition_identity.csv` under `results/`. F04–F10 address normalization, pair dispersion, BFP, robustness, event support and reference weighting.
'''
    write('reports/Layer1_Flow_Quantification.md',layer1)
    layer2=header+f'''## Scientific question
Does the S7 active/inactive reference response admit a reliable inverse mapping from RAS to reference-equivalent input (RES)?

## Reference verification and implemented analysis
FCS tube metadata preserves the 20 S7 source labels. The user confirms the handwritten 10-to-15 correction and a mass-based AC/INAC mixture. The analysis axis is now **AC DNA mass fraction (%)**: 0, 5, 15, 20, 30, 40, 50, 75, 90 and 100. Source filenames and acquisition IDs such as S7_10A remain unchanged; `source_condition_label=10` and `condition_label=15` preserve the reconciliation. These are input DNA mass fractions, not measured intracellular RNA fractions or molar fractions. Exact AC/INAC sequence states, locked-state integrity, plasmid lengths, total reporter loading, per-well amounts and preparation uncertainty remain unresolved.

The implemented characterization uses the independently regenerated reporter-population RAS values, retaining A and B separately. It computes equal-acquisition condition means, sample SD, adjacent differences and descriptive rank association. No calibration model is selected or fitted; no inverse is exported. S7 observations are not reused as a held-out validation set.

## Actual response
{md(resp[(resp.series=='S7')&(resp.population_mode=='reporter')][['condition_label','ras_mean','ras_sd','acquisition_n']])}

Endpoint means rise from {sr.loc[0]:.6f} at label 0 to {sr.loc[100]:.6f} at 100: a {sr.loc[100]/sr.loc[0]:.3f}-fold difference. This establishes a detector-scale reference response under the selected context. The low endpoint is not zero; it cannot be interpreted as a zero-edited-RNA measurement. The label-5 mean ({sr.loc[5]:.6f}) is below label 0. The 75 mean ({sr.loc[75]:.6f}) exceeds the 90 mean ({sr.loc[90]:.6f}); the 75 and 100 means differ by only {abs(sr.loc[75]-sr.loc[100]):.6f}. Small reversals also occur around 15/20 and 30/40. A strong overall rank association does not establish an identifiable local inverse.

## Identifiability and compatibility
The empirical means are not one-to-one and low-end changes are not consistently resolved relative to A/B dispersion. Unverified reference states, preparation uncertainty and lack of independent calibration validation prevent RES qualification even though mass fractions and A/B well identity are now confirmed. A high-order or forced monotonic fit would hide this evidence. The appropriate output is `NOT_CALIBRATED`, with empirical response tables retained. No RES is assigned to S7 or S10.

S7 reporter-population references are not a validated bridge to blue-selected S10 populations. The exact reporter and treatment compatibility and editor/BFP influence on reference integrity are unresolved. A shared detector profile alone is insufficient.

## Required evidence before RES
Verify full AC/INAC sequences and locked responses, final preparation amounts and mixing process, lengths and explicitly defined input fractions. Demonstrate compatible context and population mode, or validate a bridge. Extend the current two-well-per-condition response to additional independently prepared wells and sessions, with emphasis on low-end discrimination and the 75/90/100 anomaly. Use independently prepared blinded mixtures to evaluate bias, precision, local inverse uncertainty and recovery; declare the accepted domain before reporting RES. Separately test whether the DNA-mixture surrogate transfers to genuinely edited reporters. None of these future checks is claimed completed.

## Sources and figure opportunities
`inventory/record_transcription.md`, `inputs/S7/IMG_1694.HEIC`, `results/ras_results.csv`, `response_summary.csv`, `adjacent_response.csv`, and `associations.csv`. F04_S7 can show the real ladder with every acquisition; it must not be labelled a validated calibration curve.
'''
    write('reports/Layer2_Reporter_Calibration_Feasibility.md',layer2)
    layer3=header+f'''## Scientific question
Are independent, quantitatively qualified RNA-editing fractions paired with the flow samples available to train and validate PER?

## Audit method and actual materials
The S10 directory contains {len(mol)} AB1 reads: forward and reverse reads for 24 molecular sample labels, four per ratio. User-confirmed mapping assigns labels 1/2 to A and 3/4 to B, giving 12 independent transfection wells across six conditions, two wells per condition. Each well has two molecular labels and four technical F/R reads; the two labels are not extra independent wells. Their extraction/RT/PCR/aliquot relationship is not yet documented. The vendor workbook links labels, reads and submission receipt; AB1 records provide instrument run metadata. Called lengths range {int(mol.called_bases.min())}–{int(mol.called_bases.max())} bases; Phred>=20 counts range {int(mol.Q20_bases.min())}–{int(mol.Q20_bases.max())}. Raw trace signals and per-base quality were parsed anew with Biopython. The `.seq` exports differ from the AB1 base calls for {int((~mol.seq_export_matches_AB1).sum())}/{len(mol)} reads, including lowercase insertions/edits; they are not silently treated as identical raw calls. Raw AB1 is retained as the chromatogram authority. The vendor flags `1-8-2.F` for double peaks; it remains in the audit.

The `523RepEdit.xlsx` workbook supplies the exact F/R primer sequences. They delimit a 544-bp region in the available general reporter design; their names specify 523 and the sample record says RepOpenA. This is evidence that the generic design is not the verified exact S10 reference. Local alignment to that generic reporter interval gives paired-column identities {100*mol.reference_aligned_identity.min():.2f}–{100*mol.reference_aligned_identity.max():.2f}%, supporting a reporter-region lead. It does not establish the exact edited coordinate or molecular endpoint. This reconstruction does not import a patched reference or any S5 measurements to close that gap.

The request sheet is named `s9 edit 编辑率测序.xlsx` despite its location under S10 and contains an older template date and unrelated primer-footer names. The vendor receipt dates and AB1 run dates are later than flow acquisition, but sequencing dates alone do not determine RNA harvest time. The user confirms their mapping to S10 wells, resolving the series/sample association despite the S9 form filename. The old filename is retained as source metadata; the confirmation does not qualify the traces as quantitative RNA-editing endpoints.

## Pairing, endpoint and assay qualification
The dated user confirmation establishes a many-to-one molecular-to-flow map: 1/2→A and 3/4→B for every ratio. The user reports RNA extraction after completion of flow at the same experimental time point. RNA origin is therefore user-confirmed, while exact clock time, elapsed minutes, retained-versus-sorted population, extraction/RT details and no-RT/DNase controls remain undocumented. Sequential flow then RNA extraction is not an assertion of simultaneous collection or identity with the analyzed R+B+ event population. User-reported RNA origin does not by itself exclude residual plasmid DNA from downstream PCR products. Exact reporter target versus introduced/endogenous target, edited strand/base, reference sequence, assay response calibration, quantitative limits and per-sample molecular uncertainty remain unverified. No nominal DNA fractions, fluorescence values or raw secondary-peak shares are substituted for independently measured RNA-editing fractions.

Therefore **PER is not fitted or estimated**. The 24-row molecular pairing registry now contains all confirmed parent-well mappings. `results/flow_RNA_well_registry.csv` joins the 12 independent wells to their two molecular labels, four reads, doses and flow RAS. RNA editing fractions remain empty because the exact endpoint and assay are unqualified; two labels from the same well must stay together in any future validation split. The base-level secondary-peak-share statistic is only a chromatogram-complexity diagnostic and has no editing-rate interpretation. Sanger quality, double peaks or alignment alone do not establish an RNA-derived editing percentage.

## Exact future validation requirements
1. Define one endpoint: e.g. the edited fraction at a named site of reporter RNA, with exact strand and sequence. Endogenous APOE requires its own locus-specific evidence and domain.
2. Assign persistent identifiers linking culture/batch, physical well, reporter/editor construct, flow acquisition, RNA extraction, RT/PCR product and molecular read. The 1/2→A, 3/4→B relation is now supplied by the user; add extraction, RT/PCR and physical plate identifiers without counting the two labels per well as independent units.
3. Record the exact elapsed interval and sampled material for the confirmed flow-then-RNA sequence at the same experimental time point. For bulk RNA, define a bulk-response model and characterize which cells contributed. For a conditional R+B+ claim, molecular sampling must match that population (or a validated population bridge is required). Multiplying a conditional prediction by a cell-count co-expression fraction is insufficient.
4. Verify RNA origin and exclude residual DNA with suitable controls. Establish the molecular assay's bias, precision, background, response range and uncertainty with known mixtures and an appropriate independent reference where possible. Bidirectional Sanger reads are technical evidence, not independent biological n.
5. Separate development and validation by independent well/culture/session, keeping all paired reads and technical acquisitions together. Test the intended target/editor/batch domain on genuinely held-out material. Define acceptable errors and prediction-interval coverage before judging performance.
6. On the same held-out endpoints compare direct `RAS -> E_RNA` against staged `RAS -> RES -> E_RNA`, with the same allowed covariates and uncertainty treatment. Fit all reporter calibration and model choices within training folds or on separate reference data; prevent held-out leakage. Compare MAE/RMSE, calibration bias, uncertainty coverage and domain failures, not correlation alone. Keep the intermediate RES only if its interpretability or predictive/transfer benefit is supported.

## Plate-reader evidence is not a molecular reference
The S10 EDIT plate block is separately extracted. The S8 blocks in the shared map are excluded. Three channels are recorded by Varioskan LUX; only PBS A01 is explicitly documented as blank. A spatial scan supplies 81 positions per well; these are technical spatial measurements. Single-point red values include negatives and lack a matched single-point blank. Spatial scan red is weak and lacks a cell-matched background and quantitative precision study. No plate-based RAS, flow-to-plate calibration, or RNA-editing truth is inferred. Exact raw values and settings are retained in `plate_raw_points.csv`, `plate_summary.csv`, and `inventory/plate_settings.csv`.

## Sources and figure opportunities
`inventory/molecular_reads.csv`, `molecular_pairing_registry.csv`, `primer_reference_audit.json`, `construct_features.csv`, `results/sanger_base_quality.csv`, original AB1 and workbooks. F11 supports a molecular-evidence audit; F12 supports the plate-readout limitation. Neither is a PER validation figure.
'''
    write('reports/Layer3_Biological_Calibration_Audit.md',layer3)
    write('reports/Data_Inventory_and_Reconciliation.md',header+'''## Input accounting and independence
The full file manifest lists original paths, copied paths, sizes and SHA-256 hashes. `acquisition_file_manifest.csv` has one row for each of the 36 FCS files; `acquisition_manifest.csv` has one row for each of the 34 unique acquisitions. File hashes, DATA-segment hashes and instrument tube UUIDs are retained to audit duplicate copies versus acquisitions. Two shared Mocks are deduplicated. There are 32 user-confirmed independent transfection wells, two per condition; independent culture or batch replication is not established. No non-identical FCS re-export of the same event data was identified. Generated well IDs identify the confirmed experimental units but are not physical plate coordinates. Culture IDs and the molecular preparation subtype remain unknown.

## Reconciliation decisions
| Issue | Observed evidence | Decision |
| --- | --- | --- |
| Shared Mock files | Identical full-file and event-data hashes in S7/S10 | Count each acquisition once |
| Midnight crossing | FCS dates 23/24 September; same optical settings | One contiguous acquisition session; no independent-day claim |
| A/B identity | User confirms two independent transfection wells per condition | Within-experiment well repeatability, n=2; no independent-culture/day claim |
| S7 10/15 | User confirms handwritten 15 correction | Retain source IDs/label 10; analyze at 15% AC mass fraction |
| S7 AC/INAC | User confirms mass-based mixing | AC mass-fraction axis; not molar or RNA fraction; exact states remain unverified |
| S10 DNA | User confirms reporter 100 ng and total DNA 1,000 ng per well | Editor amounts derived from recorded 1:x ratios: 0, 50, 100, 200, 400, 800 ng |
| BFP | User confirms ORCA–P2A–BFP in S10 | Positive-dose B+ reporter mode is exploratory editor co-expression; optical boundary still provisional |
| Compensation | Identity matrices and USCOMP=False in all FCS files | Preserve native linear values; no invented spillover estimate |
| Matched optical controls | Two Mock acquisitions; no single-color panel | Optical-validity warning applies to all scores |
| S10 1:1 B rate anomaly | One-second rate outlier bins | Apply fixed time rule; retain no-time-filter sensitivity |
| Fluorescence above PnR | Tiny area-channel excursions, no repeated-max pileup | Diagnose; do not equate metadata range with proven clipping |
| S9-named sequencing form in S10 | User confirms these molecular samples map to S10 A/B | Series association resolved by user; preserve source filename |
| Flow A/B versus molecular 1–4 | User: 1/2→A, 3/4→B; RNA extracted after flow | 24 labels grouped into 12 wells; exact sampled population and assay still unqualified |
| SEQ versus AB1 | 19 of 48 text exports differ from AB1 calls | Preserve both; AB1 is trace authority |
| General reporter versus OpenA | Generic primer interval 544 bp versus 523 name | Generic design supports architecture only; exact target unresolved |
| Shared S8/S10 plate map | Separate EDIT block identified | Use EDIT values only; exclude S8 experimental values |
| PBS blank | Only A01 explicitly labelled PBS | Do not pool other blank-file wells as known controls |

## Construct-role registry
The general sequence design explicitly annotates mCherry, GSG-P2A, EGFP and ecDHFR-DD. This supports the intended continuous red-reference / green-response architecture at design level. It is not full-clone sequence confirmation for S7 AC, S7 INAC or S10 OpenA. AC/INAC molecular locked states remain unresolved. S10 ORCA–P2A–BFP linkage is user-confirmed but not sequence-verified. No construct length from the generic plasmid is substituted for missing AC/INAC plasmid lengths.

## Unknown fields
Unresolved fields are S7 absolute DNA amounts, culture identity, cell type, treatment/TMP conditions, exact flow-to-RNA elapsed interval, RNA population selection, viability, exact construct sequences, physical plate coordinates, independent culture/day replication and molecular assay controls. S10 absolute doses, S7 mass basis/corrected percentage, transfection-well independence, and flow/RNA label grouping are resolved from user confirmation. The inventory is complete in its accounting of supplied materials; the experimental history is not fully resolved. See `record_transcription.md` and each source workbook/photo for the evidence boundary.
''')
    pairing=read('flow_RNA_well_registry')
    write('reports/Metadata_Confirmation_Update.md',header+'''# User-confirmed metadata update

Direct replies: “123 都是，4 12 为 a，34 为 b”; “质量，是的，跑完流式提的 rna”. Complete question context and exact interpretation are retained in `config/user_confirmations.json`.

A/B are independent transfection wells within each condition. S7 label 10 means 15% AC by DNA mass. S10 has 100 ng reporter and 1,000 ng total DNA per well, with user-confirmed ORCA–P2A–BFP. Editor mass follows the recorded 1:x ratio; remaining DNA is derived by subtraction. Molecular labels 1/2 map to A, 3/4 to B. RNA was extracted after flow at the same experimental time point; exact elapsed minutes and cell-population selection are unknown.

No fluorescence gate, background rule or estimator was changed in response to these confirmations. Corrected coordinates, biological interpretation, n definitions and pairing tables change; the per-acquisition numerical fluorescence measurements do not. Source IDs preserve raw labels. Each well's two molecular labels and four F/R reads share one validation group. No molecular editing fraction is imputed.

## Twelve-well flow/RNA registry

'''+md(pairing[['flow_acquisition_id','condition_label','replicate_label','editor_dna_ng','molecular_labels','read_n','RAS_reporter','RAS_editor_coexpression','molecular_endpoint_status']]))
    # Scientific writer's report: eight required elements for each layer.
    evidence=header+f'''# SONAR Measurement Evidence Report

## Findings to prioritize
1. A fresh, auditable reconstruction processes all 34 unique flow acquisitions and preserves the exact linear paired-channel estimator. This is the strongest computational claim.
2. Red normalization reduces matched-label A/B dispersion in most tested conditions: S7 median raw-green CV {cvtable[cvtable.series=='S7'].mean_G_raw.iloc[0]:.2f}% to RAS CV {cvtable[cvtable.series=='S7'].ras.iloc[0]:.2f}%; S10 {cvtable[cvtable.series=='S10'].mean_G_raw.iloc[0]:.2f}% to {cvtable[cvtable.series=='S10'].ras.iloc[0]:.2f}%. These are within-experiment independent-transfection-well CVs (n=2 per condition); culture/day reproducibility is untested.
3. S7 has a {sr.loc[100]/sr.loc[0]:.2f}-fold endpoint reporter response, with unresolved low-end separation and a marked 75-to-90 reversal. This supports reference-response characterization but not reliable RES.
4. S10 B-positive prevalence increases with the ratio labels while RAS remains nonmonotonic. Detectable blue expression and normalized reporter response answer different questions.
5. There is no validated PER: 48 Sanger reads map to 12 S10 wells with user-confirmed RNA extraction after flow. Exact reference/site, RNA population selection, DNA-exclusion controls and assay uncertainty remain unresolved.

{limits}

## Layer 0: context calibration
**Question.** Can the fluorescence measurements be processed in one reproducible context? **Method.** Native FCS interpretation is cross-checked independently; fixed Mock-trained scatter/pulse gates, per-file rate QC, linear mean subtraction and provisional positivity boundaries are applied. **Evidence.** Twenty S7 acquisitions, twelve S10 acquisitions and two shared unique Mocks on one detector profile. **Key findings.** Mock singlet retention is about 78.4–78.5%; cross-control positivity rates are 0.424–0.602%; one S10 acquisition loses 4.32% of events to the rate rule. **Interpretation.** Geometry and approximate negative-background transfer are consistent within the supplied session. **Limits.** Mock transfer does not prove optical spillover correction, multicolor negative classification, viable-cell selection or interday transfer. **Figure opportunity.** F01–F03 provide actual gates, backgrounds and counts. **Sources.** `inventory/acquisition_manifest.csv`, `reader_crosscheck.csv`, `channel_metadata.csv`; `results/event_retention.csv`, `background_thresholds.csv`, `negative_transfer.csv`; `contexts/context.json`; detailed methods in `reports/Layer0_Context_Calibration.md`.

## Layer 1: flow quantification
**Question.** Can green reporter output be interpreted relative to a continuous red reference, and what does blue add? **Method.** RAS=sum(corrected green)/sum(corrected red) on identical red-eligible events, preserving negative green values. Blue-stratified results, paired-event bootstrap intervals, shared control-mean uncertainty, gate/background perturbations, finite-event subsampling and bright-event influence are assessed separately. **Evidence.** All 32 reporter populations meet the provisional numerical screen; 10 positive-ratio S10 blue-selected populations are estimable. Two no-editor-labelled blue-selected populations fail denominator precision. **Key findings.** RAS lowers CV in 8/10 S7 and 5/6 S10 pairs. Gate perturbations change main scores by at most about 1.64%, alternative Mock means by about 0.12%. The top 1% of red events carry 16.78–30.78% of red signal; deleting them would change RAS by -1.18% to +6.29%. S10 B-positive fractions rise from {100*bf.loc[0]:.2f}% to {100*bf.loc[8]:.2f}% at endpoint labels. **Interpretation.** Normalization often reduces observed scale-related dispersion but retains expression weighting and does not make the reporter a molecular counter. BFP adds a detectable-expression covariate, not an editing-rate readout. **Limits.** A/B independent transfection wells and S10 ORCA–P2A–BFP linkage are user-confirmed; no optical/LOQ validation; 14/40 common B-bin scores are unavailable, preventing a complete standardized comparison. **Figure opportunities.** F04–F10 support normalization, heterogeneous improvement, blue prevalence, robustness and influence. **Sources.** `results/ras_results.csv`, `repeatability.csv`, `sensitivity.csv`, `high_expression_influence.csv`, `blue_profiles.csv`, `B_negative_transfer.csv`, `event_count_sensitivity.csv`, `bootstrap_draws.csv`; detailed report `reports/Layer1_Flow_Quantification.md`.

## Layer 2: reporter calibration feasibility
**Question.** Can the response be inverted to an active-reference-equivalent input? **Method.** Plot and summarize independently recalculated S7 acquisition points; inspect local reversals, dispersion and identity/mixture requirements without forcing a fit. **Evidence.** Ten user-confirmed AC mass fractions with two independent transfection wells each. **Key findings.** Mean RAS is {sr.loc[0]:.4f} at 0 and {sr.loc[100]:.4f} at 100, but {sr.loc[75]:.4f} at 75 and {sr.loc[90]:.4f} at 90. **Interpretation.** A broad response exists; local inversion is not qualified. **Limits.** Mass input fractions are not molar fractions or RNA editing; exact reference states remain unverified; no independent calibration validation or population bridge. **Figure opportunity.** F04_S7 with every observation, no fitted monotonic curve. **Sources.** Original S7 photograph, `inventory/record_transcription.md`, `results/response_summary.csv`, `adjacent_response.csv`; detailed report `reports/Layer2_Reporter_Calibration_Feasibility.md`. RES status is `NOT_CALIBRATED`.

## Layer 3: biological calibration requirements
**Question.** Can SONAR predict an independently measured RNA endpoint? **Method.** Audit AB1 metadata, quality, sequence/export discrepancies, primers, generic-reporter alignment and sampling provenance. **Evidence.** Forty-eight traces for 24 molecular labels, plus submission/primer records. **Key findings.** Q20 support spans {int(mol.Q20_bases.min())}–{int(mol.Q20_bases.max())} bases per trace; 19 text exports differ from AB1 calls; the generic design primer interval is 544 bp despite a 523 label. **Interpretation.** Molecular material exists but is not a qualified paired RNA calibration dataset. **Limits.** S10 assignment, parent-well mapping and RNA extraction after flow are user-confirmed; exact site/reference, sampled population, residual-DNA exclusion and quantitative assay uncertainty remain unresolved. **Figure opportunity.** F11 can document evidence readiness; a PER prediction-versus-truth figure is unsupported. **Sources.** `inventory/molecular_reads.csv`, `molecular_pairing_registry.csv`, `primer_reference_audit.json`, raw AB1/workbooks; detailed report `reports/Layer3_Biological_Calibration_Audit.md`. PER is not fitted.

## Claim language for subsequent scientific writing
Supported: “A uniform reconstruction generated explicitly defined, background-corrected population fluorescence ratios from S7/S10 and exposed uncertainty and calibration limits.” Supported with a narrow qualifier: “RAS reduced between-well dispersion in most conditions across two independently transfected wells per condition in the same experiment.” Preliminary: “The S7 AC DNA mass-fraction ladder produced a broad reporter response.” Unsupported: “SONAR accurately measured RNA editing,” “BFP measured active-editor concentration,” “RES recovered edited-RNA fractions,” “PER predicted endogenous editing,” or “the assay reproduced across laboratories.”

## Reproducibility at the tested level
Computational re-execution is checked against deterministic result tables and event masks; the executed check is recorded in `reports/reproducibility_record.json`. Within-experiment repeatability is characterized by two user-confirmed independent transfection wells per condition; independent cultures are not documented. Between-experiment, cross-instrument and cross-laboratory transfer have not been demonstrated. Shared Mocks and midnight dates do not supply those independent levels.

## Suggested next scientific decisions
The user has resolved parent-well identities, mass basis, S10 doses/linkage and flow-then-RNA timing. Next verify exact construct/target provenance, validate panel-specific optical controls and red precision, investigate the S7 75/90 anomaly and low-end response, and qualify the already paired RNA material as a quantitative endpoint. Evaluate direct RAS-to-RNA prediction against the staged model on the same independent holdout data before promoting RES as a necessary predictive step.

## External methodological references
The [FlowIO documentation](https://flowio.readthedocs.io/en/latest/notebooks/flowio_tutorial.html) explains raw versus preprocessed FCS representations. The [UTHealth FMO guidance](https://med.uth.edu/imm/flow-cytometry-services/protocols-and-guidelines/fmo-controls/) motivates multicolor negative-control checks; its antibody-panel practice is not direct validation of this fluorescent-protein panel. [EditR](https://github.com/MoriarityLab/EditR) is a possible Sanger assay method; EditR was not run here, and citing it does not establish RNA origin, assay calibration or pairing. Accessed 2026-10-12. Project-specific numerical claims come only from this release's tables.
'''
    write('SONAR_Measurement_Evidence_Report.md',evidence)
    zh=f'''# SONAR S7/S10 重建：中文科学摘要

版本：`{ver}`；审阅日期：{cfg['review_date']}。

本版已纳入用户对实验记录的确认，并重新生成样本表、孔级配对、分析结果及 13 张诊断图。原始文件和文件名保持原样；S7 图表与汇总使用纠正后的 15% 坐标。

## 已确认的实验信息

- S7、S10 的 A/B 是同条件的两个独立转染孔，每个条件 n=2。S7 共 20 个实验孔，S10 共 12 个；未据此推断独立培养批次或跨日重复。
- S7 按 **AC/INAC DNA 质量比例**混合，源文件“10”实际为 **15% AC**。保留源标签 10，并将分析条件记为 15%；该百分比不代表摩尔比例或 RNA 编辑率。
- S10 每孔 reporter **100 ng**、总 DNA **1,000 ng**，ORCA 与 BFP 通过 **P2A** 相连。由记录的 1:0、1:0.5、1:1、1:2、1:4、1:8 推导 editor 分别为 **0、50、100、200、400、800 ng/孔**。这是剂量换算；精确构建序列仍待核实。
- 每个 S10 条件的测序标签 **1、2→A 孔，3、4→B 孔**。用户确认同一实验时间点在**完成流式后提 RNA**；精确间隔及提取的细胞群体尚无记录。24 个分子标签归入 12 个独立孔，每孔两个标签、四条 F/R 读段；不能按 24 个独立重复计算。

确认原文与适用范围保存在 `config/user_confirmations.json`。测序标签在同一孔内属于何种提取、RT、PCR 或分装重复，仍保留为未知。

## 主要结果与解释

**归一化通常改善同次实验内的孔间重复性。** S7 原始 EGFP 的条件内 CV 中位数为 **4.70%**，RAS 为 **1.77%**，10 个条件中 8 个改善；S10 为 **6.71%→5.14%**，6 个条件中 5 个改善。CV 以两个独立转染孔的样本标准差（ddof=1）除以均值绝对值计算。S7 40%、100% 及 S10 1:0.5 未改善。n=2 仅支持有限的同次实验比较，不能证明编辑率准确或跨批次可重复。

**S7 存在整体参考响应，但 RES 仍未校准。** 0% 与 100% AC 的平均 RAS 为 {sr.loc[0]:.4f}、{sr.loc[100]:.4f}，相差 {sr.loc[100]/sr.loc[0]:.2f} 倍；75% 为 {sr.loc[75]:.4f}，90% 降到 {sr.loc[90]:.4f}。15% 坐标和质量基准确认后，非单调性仍存在。精确 AC/INAC 状态、配制不确定度和独立校准验证尚缺，不能强行反演。

**S10 现可解释为探索性的 reporter/editor 共表达分析。** 已确认 ORCA–P2A–BFP，因此有 editor 的 B+ reporter 子群有明确的共表达含义；单色/多色对照仍不足，B+ 边界和 CEF 仍属暂定。reporter 群体的 B+ 比例从无 editor 的 {100*bf.loc[0]:.2f}% 增至 1:8 的 {100*bf.loc[8]:.2f}%，但 RAS 没有同步单调增加。无 editor 的 B+ 尾部是阴性对照诊断，不能称为 editor 共表达。其两个蓝色子群还因红色分母精度不足而不输出 RAS。

**流式—RNA 配对已建立，PER 尚不能拟合。** `results/flow_RNA_well_registry.csv` 按 12 个孔汇总剂量、RAS、分子标签与提取顺序。用户已确认 RNA 来源，但残留 DNA 排除、准确编辑位点、参考序列和定量误差仍缺。19/48 个 `.seq` 与 AB1 调用不同；一般 reporter 设计的引物区间为 544 bp，与 OpenA 523 标签不一致。未将混峰、质量比例或荧光值充当 RNA 编辑真值。后续划分训练/验证时，同一孔的全部标签和读段必须归在同一组。

## 四层完成状态

| 层 | 已完成 | 保留的边界 |
| --- | --- | --- |
| Layer 0 | 36 个 FCS 文件审计、去重为 34 次采集，线性解码核对、统一门控、背景与时间质控 | 两份共享 Mock 不增加独立 n；补偿及多色边界未验证，无活性染料 |
| Layer 1 | 32 个 reporter 群体的探索性 RAS、n=2 孔间重复性、S10 共表达分层、事件不确定度和稳健性 | 仪器尺度比值；门限暂定；构建连接由用户确认，未做序列验证；14/40 共用 BFP 区间定量失败 |
| Layer 2 | 按已确认质量百分比和 15% 修正分析 S7 参考响应 | 不可认定已校准，RES 留空 |
| Layer 3 | 48 条 AB1 的审计；24 标签→12 孔的配对及流式后提 RNA 的记录 | RNA 报告来源已确认；精确分子终点和检测有效性未合格，PER 留空 |

RAS 使用同一批事件的 `Σ(G−背景)/Σ(R−背景)`，保留负绿色值，不以绿色阳性筛选，不加分母伪计数。2000 次事件自助抽样只描述条件于采集的技术不确定度，不替代独立孔重复。更换 Mock 均值使主 RAS 最大变化约 0.12%，测试门控扰动约 1.64%；最亮 1% 红色事件贡献 16.78–30.78% 红色总信号，已保留并报告影响。

英文报告：`SONAR_Measurement_Evidence_Report.md`；图证据清单：`SONAR_Figure_Evidence_Inventory.md`；逐层方法与局限：`reports/`。诊断图为科学审阅材料。下一步应集中补准确构建/靶位点、RNA 检测质控、所取细胞群体及光学验证，随后在独立留出孔或批次上评价 RNA 编辑率预测。
'''
    write('SONAR_中文科学摘要.md',zh)
    fig=pd.read_csv(ROOT/'figures/figure_index.csv');inventory='''# SONAR Figure Evidence Inventory

These are scientific messages and available evidence, not final illustration prompts. All diagnostics have PNG and editable SVG exports; source tables are enumerated in `figures/figure_index.csv`. Every A/B condition has two user-confirmed independent transfection wells; independence of culture/day is not established.

| Candidate | Scientific message | Data and recommended plot | Replicate support | Status and limitation |
| --- | --- | --- | --- | --- |
| Context and gates | One declared context processes the session consistently | F01–F03; control scatter, background distributions, retention bars | 2 unique Mock acquisitions; 32 experimental acquisitions | Partially supported: same-session processing; no viable-cell or optical validation |
| Normalization | Red normalization reduces dispersion in most conditions, with exceptions | F04_S7/F04_S10 and F05; paired raw/corrected/RAS points and CV comparison | 10 S7 and 6 S10 conditions; n=2 independent transfection wells per condition | Partially supported: show every exception; no accuracy claim |
| BFP dimension | Blue detection and reporter activity change differently | F06; B+ fractions and mode-specific RAS | 12 S10 transfection wells; n=2 per condition | Partially supported: linkage user-confirmed; multicolor boundary unvalidated |
| Robustness | Scores are insensitive to tested small background/gate changes | F07/F08; sensitivity distributions and event-subsampling widths | Within-acquisition resampling, not biological replication | Supported within the declared computational domain; not optical validity |
| Reference weighting | Bright red cells contribute disproportionate signal | F09; red-share versus perturbation and red-bin response | 32 acquisitions, technical event support | Supported descriptive finding; removal is a sensitivity analysis only |
| Matched blue profiles | Some common-intensity bins lack sufficient denominator precision | F10; profiles plus counts and explicit gaps | 10 positive-ratio S10 acquisitions, 40 bins | Partially supported: 14 bins unavailable, no standardized aggregate |
| Reporter reference ladder | Broad response with low-end reversals and high-end ambiguity | F04_S7; all observations and confirmed AC mass fractions, no forced fit | Two independent transfection wells per mass fraction | Partially supported: not a validated inverse calibration |
| Molecular readiness | Traces exist but paired RNA truth is unqualified | F11; read-quality / alignment audit and a pairing-status table | 48 reads / 24 labels / 12 parent wells; F/R technical reads | Supported audit; PER validation plot unsupported |
| Plate-readout limitation | Weak red signal prevents a qualified plate normalization | F12; raw red values and documented PBS scan mean | 12 labelled EDIT wells; 81 spatial positions per scan well | Partially supported: no matched single-point blank; no molecular endpoint |
| Four-layer future prediction | How qualified references could connect RAS, RES and PER | A later conceptual diagram tied to layer-status table | No prediction-validation sample set | Conceptual only for RES/PER; never draw synthetic prediction observations |

The strongest eventual Measurement figures would combine normalization with its exceptions, the actual S7 reference response, and BFP detection versus RAS. Preserve the exploratory instrument-scale qualifier and n=2 within-experiment transfection-well scope. Do not label a positive rank trend as calibration validity or a repeated software run as biological reproduction.
'''
    write('SONAR_Figure_Evidence_Inventory.md',inventory)
    decisions=[('D01','Construct/reference identity','unresolved','Generic reporter architecture verified only; exact AC/INAC/OpenA/editor clones unknown'),('D02','FCS and optics','partially_resolved','Byte decoding and channels verified; identity matrix optically unvalidated'),('D03','Population gates','frozen_exploratory','Mock1 MCD geometry, pulse ratio and per-file time rule; no viability claim'),('D04','Background and thresholds','frozen_exploratory','Equal-control linear means; Mock Q99.5 boundaries; transfer check only'),('D05','Quantification QC','provisional','N>=100 and denominator RSE<=0.1 are declared numerical screens, not validated LOQ'),('D06','Population bridge','unresolved','S7 to S10 blue-selected bridge not demonstrated'),('D07','Reporter inverse','not_calibrated','Mass basis confirmed; reference states unverified and response nonmonotonic; no inverse fitted'),('D08','BFP covariate','partially_resolved','ORCA-P2A-BFP linkage user-confirmed; coexpression exploratory; 14/40 blue bins unavailable'),('D09','Molecular reference','unresolved','RNA origin and S10 well pairing user-confirmed; exact site, sampled population and assay validation unresolved'),('D10','Prediction domain','not_calibrated','No PER fitted'),('D11','Fresh reconciliation','completed_with_unknowns','All raw files inventoried; two duplicate controls removed; conflicts explicit'),('D12','Reference validity','partially_resolved','Most A/B dispersion lower; red dependence and bright-event influence remain')]
    write_csv(ROOT/'reports/decision_registry.csv',[dict(decision_id=a,question=b,status=c,evidence_or_limit=d,analysis_version=ver) for a,b,c,d in decisions])
    er=[]
    entries=[('E01','not_supported','Exact sample-specific reporter/editor identity is not verified','inventory/construct_features.csv','F11_molecular_audit','No exact clone registry'),('E02','supported_within_domain','One session has consistent geometry and approximate Mock negative transfer','results/negative_transfer.csv','F01_control_gates','Optical compensation and viability unvalidated'),('E03','supported_within_domain','RAS uses a continuous paired red reference and exposes influence','results/high_expression_influence.csv','F09_reference_influence','Not proof of molecular accuracy or expression invariance'),('E04','not_supported','Reliable inverse reporter calibration is not established','results/response_summary.csv','F04_S7_normalization','Reference states, nonmonotonicity and calibration holdout unresolved; mass basis confirmed'),('E05','not_supported','No qualified paired RNA reference or PER prediction','inventory/molecular_pairing_registry.csv','F11_molecular_audit','RNA origin and pairing user-confirmed; exact site, residual DNA controls, sampled population and assay uncertainty unresolved'),('E06','supported_within_domain','Within-experiment independent-transfection-well repeatability characterized at n=2 per condition','results/repeatability.csv','F05_pair_dispersion','Two wells per condition; independent culture/day/batch reproducibility not established'),('E07','supported_within_domain','Fresh source, hashed inputs, tests and deterministic re-execution','reports/reproducibility_record.json','F03_event_retention','Computational only; see actual check result'),('E08','supported_within_domain','S7 response is nonmonotonic and S10 B detection does not imply increasing RAS','results/response_summary.csv','F06_blue_dimension','Exploratory same-session interpretation only')]
    input_hashes='inventory/input_files.csv'
    for eid,status,claim,tab,fid,lim in entries:
        er.append(dict(evidence_id=eid,status=status,claim=claim,source_files='inputs/S7;inputs/S10',input_hashes=input_hashes,sample_ids='inventory/acquisition_manifest.csv',population_mode='reporter_or_explicit_blue_stratum',independent_n='32 transfection wells across 16 conditions; n=2 per condition; 12 S10 wells for molecular grouping; Mock independence unknown',context_id='contexts/context.json',estimator_id=ver,calibration_id='none',result_table=tab,figure_id=fid,uncertainty_definition='conditional_event_sampling_and_control_mean; not biological',limitations=lim,review_date=cfg['review_date']))
    write_csv(ROOT/'reports/evidence_register.csv',er)
    highest=pr[['acquisition_id','series','condition_label','ras','score_status','qc_state','validated_RAS_status','RES_status','PER_status']].copy();highest['highest_supported_output']='Layer1_exploratory_detector_scale_RAS';highest['coexpression_status']=pr.coexpression_claim_status.to_numpy();write_csv(ROOT/'results/sample_highest_supported_output.csv',highest.to_dict('records'))
    write('reports/units_and_uncertainty.md','''# Units and uncertainty

Native and corrected fluorescence: linear detector arbitrary units in one CytoFLEX S gain/profile. Hardware detector gains are not a molecule calibration. Time: seconds after FCS TIMESTEP conversion. RAS: ratio of corrected green to red channel sums, dependent on relative detector scaling. It is not a percent or a molar fluorescence ratio. S7 AC input coordinates are confirmed DNA mass percentages, with source label 10 corrected to 15; they are not RNA or molar fractions. S10 per-well reporter and total DNA are confirmed as 100 ng and 1,000 ng; editor ng is derived from the recorded 1:x ratio. The remaining DNA amount is a mass-balance derivation, not independent vector identity evidence. Plate data retain instrument RFU and are not merged with flow a.u.

Event bootstrap intervals: conditional technical uncertainty in one acquisition, with fixed gates and selected events. Event-plus-control intervals also propagate covariance of the two control means using a shared Gaussian draw across acquisitions. Neither includes optical, gate-estimation, biological-well, batch or molecular calibration uncertainty. A/B CV uses ddof=1 sample SD divided by absolute mean at one condition, n=2 user-confirmed independent transfection wells within one experiment; independent cultures or batches are not established. Spatial plate points and Sanger F/R reads are technical measurements, never biological n.

Empty CSV cells represent unavailable or unverified values when paired with an explicit status column. In particular, validated_RAS, RES and PER are empty, never zero. The measured signed green distribution is preserved, so negative corrected events are valid retained numerical values.
''')
    write('reports/Executive_Summary.md',f'''# Executive summary

{header}
The fresh pipeline and complete evidence package have been reconstructed from S7/S10 originals, preserving hashes, acquisition identity, event masks, linear paired-channel RAS, uncertainty and diagnostic plots. There are 34 unique acquisitions, including two shared Mocks. All 32 experimental reporter populations produce exploratory detector-scale RAS. Exact experimental metadata remains incomplete.

The strongest numerical findings are lower A/B dispersion after red normalization in 8/10 S7 and 5/6 S10 pairs, a {sr.loc[100]/sr.loc[0]:.2f}-fold S7 endpoint response with important reversals, and increasing S10 B-positive prevalence without monotonic RAS. These observations support a transparent reporter measurement workflow with bounded claims. They do not establish RNA-editing accuracy.

RES is not calibrated: reference states, local inversion and independent validation are unresolved despite confirmed mass fractions. PER is unsupported: parent-well mapping and RNA extraction after flow are confirmed, but the traces lack an exact verified endpoint, sampled-population definition and quantitative assay qualification. There is no forced calibration or synthetic prediction curve.

User confirmation resolves A/B independence, S7 15% correction/mass basis, S10 doses/linkage and 1/2-A, 3/4-B RNA pairing. The sampling sequence is flow followed by RNA extraction at the same experimental time point; elapsed minutes and population identity are unknown. Validate optics and red precision, repeat informative reference conditions, and compare direct versus staged molecular prediction on held-out paired data. Final Wiki prose and publication figures are intentionally outside this stage.
''')
    write('README.md',f'''# SONAR fresh reconstruction: S7 and S10

Start with [中文科学摘要](SONAR_中文科学摘要.md), [Measurement evidence report](SONAR_Measurement_Evidence_Report.md), and [figure evidence inventory](SONAR_Figure_Evidence_Inventory.md).

Version `{ver}`. This directory is isolated from all earlier SONAR implementations. Original experimental input copies are included under `inputs/`, with SHA-256 comparison to the originals. No S1–S6/S8/S9 experimental measurements or old SONAR code/results enter calculations. The S9-named submission form inside S10 retains its original filename; user-confirmed pairing resolves its S10 sample association, while molecular editing truth remains unqualified. Shared map S8 entries are excluded from measured plate analysis. A generic reporter construct is used only for architecture/primer auditing, never as the exact verified S10 reference.

## Contents
- `src/`, `config/`, `tests/`, `reproduce.py`: new analysis, frozen choices and meaningful mathematical/raw-data checks.
- `inventory/`: all files, unique acquisitions, original FCS metadata, channels, record transcription, molecular audit and user-confirmed parent-well mappings with remaining assay gaps.
- `contexts/`, `masks/`: trained context object and per-acquisition event masks (indices refer to original event order).
- `results/`: numerical tables, conditional uncertainty draws, population metrics, sensitivity, reference response, plate and molecular diagnostics.
- `figures/`: 13 real-data diagnostics in PNG/SVG; every plot reads an exported source table listed in `figure_index.csv`.
- `reports/`: separate Layer 0–3 reports, reconciliation, decisions, evidence register, data dictionary, units and actual re-execution record.
- `_work/`: temporary environment/rendering and verification output, not required as scientific source.

## Reproduce
Use Python 3.13 and the pinned packages in `requirements.txt`. Create a virtual environment and install those packages; then from this directory run:

```text
python reproduce.py --verify
```

The command verifies input hashes, regenerates all supported analyses and plots, runs tests, and performs a second independent output-directory execution to compare deterministic tables and masks. For a normal single run use `python reproduce.py`. The report-generation step creates documentation from result tables. Provided hand-record transcription remains a human-audited source annotation; it is not inferred anew by software.

Inputs are included so analysis can run without previous project folders. Source originals are verified if present; no original is modified. The current host's already prepared environment can also run `_work/venv/bin/python reproduce.py --verify`.

## Interpretation boundary
{limits}

No final Wiki narrative or final illustration prompt is delivered in this stage. The evidence reports are intended for scientific review before subsequent writing.
''')
    # Field-level dictionary for every emitted CSV; specialized meanings override naming heuristics.
    dictionary=[]
    for p in sorted((ROOT/'results').glob('*.csv')):
        d=pd.read_csv(p,nrows=2)
        for col in d.columns:
            units='dimensionless_or_identifier'
            if ('G_' in col or 'R_' in col or 'B_' in col) and not any(k in col for k in ['fraction','share','positive','weight','status']):units='linear_detector_au'
            if 'RFU' in col or col in ['minimum','maximum','sd_spatial']:units='instrument_RFU'
            if col.endswith('_s'):units='seconds'
            if col.endswith('_ng'):units='ng_DNA_per_well'
            if col in ['verified_independent_well_n','independent_well_n_verified','independent_wells_per_condition','planned_independent_well_n','independent_transfection_well_n']:units='independent_transfection_wells_within_experiment'
            if 'percent' in col or col=='pct':units='percent'
            if 'fraction' in col or 'share' in col or 'weight' in col:units='fraction_0_to_1_unless_explicit_signed_change'
            if 'ras' in col.lower():units='green_red_detector_ratio'
            if col in ['event_ci_low','event_ci_high','event_control_ci_low','event_control_ci_high','bootstrap_half_low','bootstrap_half_high','q025','q975','subsample_mean','subsample_sd','max_leave_one_out_change','reconstruction_error']:units='green_red_detector_ratio'
            if col in ['FSC_A_median','G_median','R_median','B_median','lower','upper','center','alternative_B_boundary','mock_B_boundary']:units='linear_detector_au'
            if col=='rate_per_s':units='events_per_second'
            if col=='phred':units='Phred_quality_score'
            if col in ['secondary_peak_share','coverage_fraction','p_descriptive_only']:units='fraction_or_probability'
            if col in ['point_n','base_index_1based','draw_id','shared_background_draw_id','bin']:units='count_or_index_at_named_level'
            if col in ['n','n_selected','sample_n','original','after_quality','after_cell','after_singlet','events','point_n','acquisition_n']:units='count_at_named_unit_not_biological_n'
            meaning={'condition_label':'S7 confirmed AC DNA mass percent (source 10 corrected to 15); S10 recorded reporter:editor 1:x, reporter 100 ng/well and total 1000 ng/well confirmed','ras':'sum signed background-corrected linear green / sum corrected linear red on same selected events; exploratory optical status','validated_RAS':'unavailable because optical/LOQ validation not established','RES':'unavailable: reporter inverse calibration not qualified','PER':'unavailable: biological prediction not qualified','event_ci_low':'2.5th percentile of paired-event bootstrap conditional on fixed context','event_ci_high':'97.5th percentile of paired-event bootstrap conditional on fixed context','event_control_ci_low':'2.5th percentile including shared paired control-mean Gaussian uncertainty','event_control_ci_high':'97.5th percentile including shared paired control-mean Gaussian uncertainty','cv_percent':'100 * sample SD (ddof=1) / absolute mean of two independent transfection wells within each condition','secondary_peak_share':'second-largest processed ABIF signal / sum ACGT at called-base position; diagnostic only, not editing fraction','population_mode':'computational event mask name; S10 positive-dose blue_positive_reporter means exploratory editor coexpression with user-confirmed ORCA-P2A-BFP linkage','independent_well_n_verified':'one independent transfection well per score row; per-condition replicate count is two, not event count','CEF_editor_exploratory':'B-positive fraction among reporter-eligible events in S10 positive-dose conditions; linkage user-confirmed, B boundary provisional; no-editor rows unavailable','CEF_editor_verified':'unavailable because the multicolor B boundary is not validated, despite user-confirmed editor linkage','source_condition_label':'unchanged FCS condition label; S7 source 10 maps to actual mass-percent 15','population_interpretation':'biological meaning of computational event mask after applying user-confirmed linkage and editor dose','score_status':'numerical availability, distinct from optical QC and calibration status','qc_state':'optical, quantification and influence warning status','mean_G_raw':'mean native linear GFP-A among the row selected population','mean_G_corrected':'mean signed GFP-A minus common linear control mean','mean_R_corrected':'mean mCherry-A minus common linear control mean','mean_G_all_singlets':'raw green mean over all retained singlet-like events','EGFP_positive_fraction':'fraction above provisional green threshold within row selected population','reporter_detection_fraction':'fraction red-positive among singlet-like events','reporter_quant_fraction':'fraction reporter-eligible among singlet-like events','blue_positive_fraction_reporters':'B-positive reporter events / all reporter-selected events','effective_red_events':'squared red sum / sum squared red; weight concentration, not independent n','denominator_relative_se':'event-sampling SE of mean red divided by mean corrected red','relative_change_without_top_one_percent':'(tail-removed RAS - primary RAS)/abs(primary RAS); sensitivity only','shared_background_draw_id':'same draw reused across acquisitions to preserve shared-control covariance'}.get(col,col.replace('_',' ')+'; see owning layer method and source code for exact aggregation')
            dictionary.append(dict(table=str(p.relative_to(ROOT)),field=col,units=units,meaning=meaning,missing_policy='blank is unavailable/unverified, never imputed zero',analysis_version=ver))
    write_csv(ROOT/'reports/data_dictionary.csv',dictionary)
    print('Scientific reports and evidence registries generated')

if __name__=='__main__':run()
