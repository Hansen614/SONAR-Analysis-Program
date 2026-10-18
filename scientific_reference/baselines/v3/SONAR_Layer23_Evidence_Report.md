Version: `sonar-s7-s10-layer23-20261013-v3`. Reviewed 2026-10-13. Upstream Flow Quantification: `sonar-fresh-s7-s10-20261012-v2`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.

# SONAR Layer 2–3 Scientific Evidence Report

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
| dose_ratio | well_n | F_raw_mean | R_raw_mean | signal_mean | signal_SD |
| --- | --- | --- | --- | --- | --- |
| 0 | 2 | 0.044926 | 0.01584 | 3.4694e-18 | 0.017497 |
| 0.5 | 2 | 0.045129 | 0.048948 | 0.016656 | 0.0087025 |
| 1 | 2 | 0.048062 | 0.058814 | 0.023055 | 0.01062 |
| 2 | 2 | 0.073729 | 0.14543 | 0.079199 | 0.033776 |
| 4 | 2 | 0.10652 | 0.1638 | 0.10477 | 0.012807 |
| 8 | 2 | 0.16354 | 0.28745 | 0.20174 | 0.010482 |

The raw chromatogram composition depends on direction, channel response and sequence context. Local baseline, nearby maxima and peak-area choices preserve the broad response, but cannot calibrate absolute accuracy. Nested-label uncertainty is estimated only when two complete labels are available. All folds keep the well's molecular reads together. Other cytidines also show dose-associated peaks; the screen is descriptive, and C280 is prioritized by sequence/codon context rather than response ranking.

No DNase/no-RT or sampled-population evidence was found in the searched supplied records. User-confirmed RNA extraction is retained; it is not silently downgraded to unknown. What remains unknown is whether the sequenced PCR mixture excludes residual DNA and corresponds to the selected flow population.

## Reporter fit and inverse evidence
| model | validation | RAS_prediction_n | RAS_RMSE | inverse_recovery_n | inverse_MAE_mass_fraction |
| --- | --- | --- | --- | --- | --- |
| affine | in_sample_descriptive | 20 | 0.070104 | 0 | unavailable |
| affine | leave_one_well_out | 20 | 0.078044 | 17 | 0.066914 |
| affine | leave_one_reference_level_out | 16 | 0.09339 | 16 | 0.076864 |
| isotonic | in_sample_descriptive | 20 | 0.037011 | 0 | unavailable |
| isotonic | leave_one_well_out | 20 | 0.050725 | 15 | 0.095736 |
| isotonic | leave_one_reference_level_out | 16 | 0.1071 | 15 | 0.10712 |
| monotone_hinge_50 | in_sample_descriptive | 20 | 0.068523 | 0 | unavailable |
| monotone_hinge_50 | leave_one_well_out | 20 | 0.07833 | 17 | 0.066322 |
| monotone_hinge_50 | leave_one_reference_level_out | 16 | 0.097955 | 16 | 0.078095 |

The 75/90 discrepancy exceeds ordinary within-level dispersion and persists after computational perturbation. Increased mCherry relative to green explains the lower ratio but not its biological/preparation origin. Model-specific smooth inverse values can still be computed, but they are conditional on assumptions not validated by the reference ladder. Isotonic models expose literal plateaus; discrepancy-aware sets are broad even for affine/hinge fits. The 20-percentage-point width screen identifies no narrow domain and is explicitly a diagnostic, not a retrospective success criterion.

## Direct prediction evidence
| model | well_n | RMSE | MAE | bias | prediction_interval_coverage |
| --- | --- | --- | --- | --- | --- |
| training_mean | 12 | 0.083797 | 0.071523 | -9.2519e-18 | 0.83333 |
| reporter_RAS | 12 | 0.090155 | 0.079761 | 0.004185 | 0.83333 |
| B_detection_fraction | 12 | 0.019219 | 0.016816 | -0.0030498 | 0.91667 |
| editor_dose_log1p | 12 | 0.034325 | 0.029796 | -0.0064514 | 0.91667 |
| reporter_RAS_plus_B | 12 | 0.019814 | 0.017507 | -0.0017524 | 0.91667 |

The endpoint is raw chromatogram signal index. These errors cannot be reported as RNA-editing percentage errors. Model-based prediction intervals and fixed-error bootstrap summaries characterize internal behavior, not independent assay or external validation. BFP may primarily encode the editor-dose titration; this experiment alone does not show generalization to another editor, reporter, treatment, batch or population. Adding RAS to B provides no observed improvement. A valid four-layer framework must expose this discordance, not force positive calibration.

## Generalizable measurement contribution
The transferable contribution is methodological: maintain linear paired-channel estimators, preserve negative background-corrected signals, verify channel identity, retain explicit population definitions, preserve nested experimental units, invert calibrations as sets where needed, separate fit from validation, and qualify the molecular endpoint independently. The particular gates, gain scales, S7 curves, C280 trace responses and index predictors are reporter/session specific and have no demonstrated universal transfer.

## Source map and reproduction
Molecular reconstruction and exact methods: `reports/OpenA_Amplicon_Reconstruction.md` and `reports/S10_Sanger_Quantification.md`. Reporter models/inverses: `reports/Layer2_RES_Calibration.md`. Prediction: `reports/Layer3_PER_Calibration.md`. Blockers: `SONAR_Layer23_Blocker_Resolution.md`. The twelve diagnostic figures and captions are indexed by `SONAR_Layer23_Figure_Evidence_Inventory.md`; each reads real exported tables. All model parameters, fold memberships and unavailable states are saved under `models/layer23/` and `results/`.

The previous release is preserved in `baselines/v2/`. Its source/configuration/RAS matches the supplied archive; 58 saved context/mask/result artifacts reproduced exactly before extension. The current `python reproduce.py --verify` includes the extension, tests, all nested numeric tables, fitted-model JSON and all PNGs. The executed result—not this instruction—is recorded in `reports/reproducibility_record.json`. The upstream RAS file and kernel hashes are pinned; a change invalidates calibration execution. No upstream estimator, gate or background was altered to improve downstream results.
## Method references

The original [Applied Biosystems ABIF specification, July 2006](https://archive.gfjc.fiu.edu/workshops/resources/literature/ABIF_File_Format.pdf), pp. 52–53, defines analyzed DATA9–12, PBAS2, PCON2 and PLOC2; per-file FWO_1 records channel order. [EditR primary paper](https://pubmed.ncbi.nlm.nih.gov/31021262/) and [author repository](https://github.com/MoriarityLab/EditR) establish a published Sanger-quantification approach. This release implements transparent peak metrics and processing sensitivities, not the EditR algorithm or a claim of EditR validation for this reporter. [scikit-learn isotonic documentation](https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html) describes the shape-constrained model and unavailable out-of-domain predictions; the installed version is pinned in `requirements.txt`. Sources accessed 2026-10-13. No external experimental observations enter fitting.
