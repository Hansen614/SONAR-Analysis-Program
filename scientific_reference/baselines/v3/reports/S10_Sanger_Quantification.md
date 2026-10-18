Version: `sonar-s7-s10-layer23-20261013-v3`. Reviewed 2026-10-13. Upstream Flow Quantification: `sonar-fresh-s7-s10-20261012-v2`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.

# S10 bidirectional chromatogram quantification

## Main result
All **48 AB1 reads** were processed and independently byte-cross-checked. **47 pass site-local QC**; 24 molecular labels yield **23 complete F/R pairs**, grouped into **12 independent transfection wells**. Increasing editor dose accompanies an increasing C280 alternative-peak signal in both directions, but direction-specific scale differences prevent interpreting the ratios as calibrated RNA-editing percentages.

| dose_ratio | well_n | F_raw_mean | R_raw_mean | signal_mean | signal_SD |
| --- | --- | --- | --- | --- | --- |
| 0 | 2 | 0.044926 | 0.01584 | 3.4694e-18 | 0.017497 |
| 0.5 | 2 | 0.045129 | 0.048948 | 0.016656 | 0.0087025 |
| 1 | 2 | 0.048062 | 0.058814 | 0.023055 | 0.01062 |
| 2 | 2 | 0.073729 | 0.14543 | 0.079199 | 0.033776 |
| 4 | 2 | 0.10652 | 0.1638 | 0.10477 | 0.012807 |
| 8 | 2 | 0.16354 | 0.28745 | 0.20174 | 0.010482 |

F is T/(C+T); R is A/(G+A). Direction means first average eligible labels within each well, then weight the two wells equally. At 1:8 they are **0.16354** and **0.28745**. The supplied preliminary F mean near 0.145 is recovered only by including the flagged misaligned forward read and equally weighting four raw traces. Excluding that read by a sequence-based rule and preserving well weighting changes the forward result; the difference is documented, not tuned toward the preliminary value.

## Read processing and QC
For each file, the ABIF directory is decoded directly and checked against Biopython for PBAS2, PCON2, PLOC2 and DATA9–12. FWO_1 is read per file (all observed orders happen to be GATC); no universal order is assumed. RevC is checked. High-quality called-base versus dominant processed channel agreement is exported in `S10_read_metadata_audit.csv`. Reverse reads are reverse-complemented for sequence alignment, while original trace coordinates and fluorescence identities are preserved. Reverse C280 therefore uses **G/A**, not C/T. The reference base and index are tested directly against the raw arrays.

Site eligibility requires stable mapping across gap-open penalties −6, −8 and −12, at least 90% matching flanking reference positions in ±10 bases (target omitted), median flank Phred ≥20, and ≤20% signal from the two irrelevant nucleotide channels at the target. The target's own Phred is reported but is not a selection gate: genuine mixed peaks can lower that base's quality. The thresholds are engineering screens, not validated molecular assay limits.

`1-8-2.F` has only **60% flank sequence identity** at the putative C280 location and fails the fixed identity rule. Its target Phred alone is 24, illustrating why read quality or a vendor warning alone is insufficient. The original trace, raw diagnostic ratio and failure reason remain in the read table. `1-8-2.R` is retained as eligible directional evidence; label 2 does not enter the primary equal-direction paired index because its F partner is unavailable. Thus the 1:8 A well has only one complete molecular label and no estimable nested-label SD/SE. It remains one independent well; no missing direction is imputed.

## Background and processing sensitivity
Primary metrics use processed-channel values at PLOC2. Sensitivity variants use (i) subtraction of each dye's local 10th-percentile processed baseline over ±4 called-base intervals, floored at zero for the peak-intensity model; (ii) maximum signal within ±2 scans of the mapped peak, restricted to the base cell; and (iii) integrated signal between neighboring peak midpoints. These variant assumptions are explicit and do not alter upstream signed-green RAS handling. No unknown spectral matrix or dye-response factor is estimated from a dose trend.

No-editor background is the equal-well mean within each sequencing direction. It is subtracted **without clipping negative corrected ratios**. The combined signal index is the mean of corrected F and R within each complete label, then the equal-label mean within each well. This supplies a reproducible relative index with arbitrary direction weighting; it is not a biophysical fraction. Model fitting uses the corresponding raw index so a held-out control does not define a training endpoint's background.

| processing | mean_index | sd_index |
| --- | --- | --- |
| raw_peak_ratio | 0.20174 | 0.010482 |
| baseline_peak_ratio | 0.20194 | 0.010575 |
| nearby_max_ratio | 0.19869 | 0.01119 |
| peak_area_ratio | 0.197 | 0.012949 |
| UNFILTERED_DIAGNOSTIC_RAW_NOT_SITE_VALID | 0.18601 | unavailable |

At the highest dose, the four defensible processing choices yield mean indices about 0.197–0.202. This local robustness does not resolve the approximately twofold direction-dependent signal scale. Across complete pairs, raw R−F bias is 0.03656 and direction RMSE is 0.06773; correlation 0.928 is not agreement. Baseline subtraction barely changes the high-dose index, so local background alone does not explain the strand discrepancy. Sequence context, processed-dye response, overlapping peaks and different read positions remain plausible contributors; known-mixture standards are absent, so their separate effects cannot be identified.

## Other cytidines
All 140 cytidines are screened with the same mapping and local-QC logic. At 15 sites, both high-dose wells exceed the observed no-editor well maximum in both directions. This is a descriptive screening criterion, not a significance test, FDR-controlled discovery or proof of bystander editing. C224 and C305 are examples with appreciable direction-consistent increases. C280 remains prioritized by its independently evaluated linker stop consequence; secondary-peak ranking did not determine its identity.

## RNA provenance and assay status
The team confirms RNA extraction after flow at the same experimental time point and mapping 1/2→A, 3/4→B. A fresh search of 180 permitted source files and seven parseable annotated construct documents found no DNase/no-RT or sampled-population records. The search manifest and all text hits are saved; an Excel lock file was excluded as a non-data artifact. This means controls were **not found in supplied records**, not that they were necessarily absent from laboratory practice. The PCR submission and alternative peaks alone cannot exclude residual DNA, sequence mixtures or other technical origins. Full absolute RNA fractions remain unavailable.

## Well-level results
| well_id | complete_molecular_pairs | F_raw_mean | R_raw_mean | signal_index | technical_mean_SE | molecular_fraction_status |
| --- | --- | --- | --- | --- | --- | --- |
| S10_1_0_A_well | 2 | 0.033951 | 0.0020704 | -0.012372 | 0.0027524 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_0_B_well | 2 | 0.0559 | 0.029609 | 0.012372 | 0.0080806 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_0.5_A_well | 2 | 0.050003 | 0.056382 | 0.02281 | 0.016558 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_0.5_B_well | 2 | 0.040255 | 0.041515 | 0.010502 | 0.0021249 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_1_A_well | 2 | 0.043219 | 0.078676 | 0.030565 | 0.007531 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_1_B_well | 2 | 0.052905 | 0.038953 | 0.015546 | 0.0030246 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_2_A_well | 2 | 0.070118 | 0.10128 | 0.055316 | 0.0032417 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_2_B_well | 2 | 0.077341 | 0.18959 | 0.10308 | 0.046 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_4_A_well | 2 | 0.11285 | 0.17558 | 0.11383 | 0.0026066 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_4_B_well | 2 | 0.10019 | 0.15202 | 0.095718 | 0.0011259 | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_8_A_well | 1 | 0.15665 | 0.29589 | 0.20916 | unavailable | ASSAY_VALIDATION_INSUFFICIENT |
| S10_1_8_B_well | 2 | 0.17043 | 0.279 | 0.19433 | 0.0049945 | ASSAY_VALIDATION_INSUFFICIENT |

Nested-label SD and SE are descriptive with at most two labels. They exclude calibration bias, inter-direction bias, RNA sampling and between-well uncertainty; one-label values are unavailable. They are not 95% RNA-editing confidence intervals.

## Status vocabulary
- `CANDIDATE_SITE_SUPPORTED`: base, frame and architecture supported, intended-target record still missing.
- `EXPLORATORY_PEAK_COMPOSITION`: numerical site metric passes declared trace/mapping QC.
- `EDITING_ASSOCIATED_SIGNAL_EXPLORATORY`: candidate-site signal changes with conditions; does not establish RNA editing as the exclusive cause.
- `UNAVAILABLE_SITE_QC`: mapped raw diagnostic retained, but not accepted for site quantification.
- `ASSAY_VALIDATION_INSUFFICIENT`: no accurate absolute RNA fraction; never substitute zero.

Sources: all files under `results/molecular/`, particularly `S10_read_level_peak_metrics.csv`, `S10_bidirectional_concordance.csv`, `S10_well_level_molecular_results.csv`, `S10_bystander_site_analysis.csv`, and processing/background tables. L23_02–06 show actual traces, the failed read, well responses, direction disagreement and multisite screening.
## Method references

The original [Applied Biosystems ABIF specification, July 2006](https://archive.gfjc.fiu.edu/workshops/resources/literature/ABIF_File_Format.pdf), pp. 52–53, defines analyzed DATA9–12, PBAS2, PCON2 and PLOC2; per-file FWO_1 records channel order. [EditR primary paper](https://pubmed.ncbi.nlm.nih.gov/31021262/) and [author repository](https://github.com/MoriarityLab/EditR) establish a published Sanger-quantification approach. This release implements transparent peak metrics and processing sensitivities, not the EditR algorithm or a claim of EditR validation for this reporter. [scikit-learn isotonic documentation](https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html) describes the shape-constrained model and unavailable out-of-domain predictions; the installed version is pinned in `requirements.txt`. Sources accessed 2026-10-13. No external experimental observations enter fitting.
