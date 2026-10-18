Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# Layer 3 — biological calibration after S7 label correction

The S7 correction improves a reference-specific optical calibration. **It does not establish S7-to-S10 transfer, improve the observed direct RAS relationship, or validate PER.** No original S10 molecular measurements or direct predictive fits were recalculated.

The preserved S10 evidence remains: 523-bp independently reconstructed amplicon, provisional candidate C280 CGA→TGA, 47/48 site-eligible AB1 reads, 23 complete bidirectional molecular labels nested within 12 independent transfection wells, and dose-associated relative peak response. RNA extraction after flow and 1/2→A, 3/4→B are confirmed. The sampled cell population, DNA-residual exclusion and known-mixture molecular response calibration remain unqualified. The index is not an accurately measured RNA-edited fraction. Original methods/results remain in `OpenA_Amplicon_Reconstruction.md` and `S10_Sanger_Quantification.md`.

## Unchanged direct prediction
| model | well_n | RMSE | MAE | bias | prediction_interval_coverage |
| --- | --- | --- | --- | --- | --- |
| training_mean | 12 | 0.083797 | 0.071523 | -9.2519e-18 | 0.83333 |
| reporter_RAS | 12 | 0.090155 | 0.079761 | 0.004185 | 0.83333 |
| B_detection_fraction | 12 | 0.019219 | 0.016816 | -0.0030498 | 0.91667 |
| reporter_RAS_plus_B | 12 | 0.019814 | 0.017507 | -0.0017524 | 0.91667 |

These are leave-one-dose-out errors in raw chromatogram-index units, not RNA percentage errors. RAS-only remains worse than the training-mean baseline; B detection remains more predictive within this dose titration. Additional RAS does not improve B-only prediction. This pattern is not causal or externally validated. All same-well molecular reads remain grouped in the preserved folds.

## Transfer reassessment
| dimension | S7 | S10 | status |
| --- | --- | --- | --- |
| cell_type | HEK293T_user_confirmed | HEK293T_user_confirmed | MATCH |
| detector_profile | same recorded CytoFLEX S profile | same profile | MATCH_NOT_SUFFICIENT |
| population | reporter eligible | reporter eligible or R+B+ | REPORTER_MATCH_BPOS_MISMATCH |
| reporter_architecture | AC/INAC exact sequences and lengths unverified | OpenA reconstructed amplicon; full construct unknown | UNRESOLVED |
| reporter_loading | per-well amount unresolved | 100 ng/well | UNRESOLVED |
| treatment_TMP | unresolved | unresolved | UNRESOLVED |
| editor_presence | BFP label does not verify linked editor | ORCA-P2A-BFP at variable doses | UNRESOLVED_REFERENCE_BRIDGE |
| reference_axis | Corrected AC DNA mass mixture; probable label transposition authorized retrospectively | editor DNA dose; unknown actual RNA state | DIFFERENT_EXPERIMENTAL_AXIS |
| molecular_population | not applicable | RNA cell population undocumented | UNRESOLVED |
| total_DNA_loading | not documented per S7 well | 1000 ng/well user-confirmed | UNRESOLVED |
| sampling_time | exact elapsed culture/treatment timing not documented | RNA after flow at same experimental timepoint; elapsed minutes unknown | UNRESOLVED |
| BFP_linkage | S7 linkage unverified | ORCA-P2A-BFP confirmed | DIFFERENT_OR_UNRESOLVED |

Common HEK293T and detector profile do not resolve construct/reference identity, S7 reporter/total DNA loading, editor effects, treatment/timing or measured population. Reporter-selected S7, reporter-selected S10 and BFP-positive co-expression S10 are not assumed equivalent. The corrected-reference label uncertainty is an additional provenance condition, not a transfer bridge.

## Updated dependent computations
All 36 model-by-S10-reporter hypothetical mappings were recalculated with corrected calibration parameters and discrepancy envelopes; none is a validated S10 RES. Observed S10 reporter RAS lies in the less-resolved low S7 response region, below the common narrow interior screen. No S10 R+B+ score is assigned a transferred RES.

The affine-rescaling sensitivity was recomputed on the exact preserved direct-model folds. Its maximum prediction difference from direct affine RAS regression is 3.47e-16. A deterministic invertible affine rescaling adds no sample-level information. This is an algebraic check, not biological staged validation. A staged RNA/PER model remains unavailable because both transfer and absolute molecular-fraction qualification are missing. A better S7 fit cannot repair either issue.

Current limitation: **more defensible exploratory S7 mass-equivalent RES in a middle range; no additional validated RNA-editing prediction claim**. The preserved BFP comparison and the RAS–molecular discrepancy remain important integrated findings.
