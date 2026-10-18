Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# SONAR Integrated Measurement Evidence — corrected S7 reference

Layer 0–1 measurements remain unchanged. Layer 2 now supports more precise, conditional reference-specific middle-range RES. Layer 3 retains a measured relative molecular signal but no validated PER. The label correction is retrospective and not independently verified.

## Layer 0: context calibration
**Question.** Can the fluorescence measurements be processed in one reproducible context? **Method.** Native FCS interpretation is cross-checked independently; fixed Mock-trained scatter/pulse gates, per-file rate QC, linear mean subtraction and provisional positivity boundaries are applied. **Evidence.** Twenty S7 acquisitions, twelve S10 acquisitions and two shared unique Mocks on one detector profile. **Key findings.** Mock singlet retention is about 78.4–78.5%; cross-control positivity rates are 0.424–0.602%; one S10 acquisition loses 4.32% of events to the rate rule. **Interpretation.** Geometry and approximate negative-background transfer are consistent within the supplied session. **Limits.** Mock transfer does not prove optical spillover correction, multicolor negative classification, viable-cell selection or interday transfer. **Figure opportunity.** F01–F03 provide actual gates, backgrounds and counts. **Sources.** `inventory/acquisition_manifest.csv`, `reader_crosscheck.csv`, `channel_metadata.csv`; `results/event_retention.csv`, `background_thresholds.csv`, `negative_transfer.csv`; `contexts/context.json`; detailed methods in `reports/Layer0_Context_Calibration.md`.

## Layer 1: flow quantification
**Question.** Can green reporter output be interpreted relative to a continuous red reference, and what does blue add? **Method.** RAS=sum(corrected green)/sum(corrected red) on identical red-eligible events, preserving negative green values. Blue-stratified results, paired-event bootstrap intervals, shared control-mean uncertainty, gate/background perturbations, finite-event subsampling and bright-event influence are assessed separately. **Evidence.** All 32 reporter populations meet the provisional numerical screen; 10 positive-ratio S10 blue-selected populations are estimable. Two no-editor-labelled blue-selected populations fail denominator precision. **Key findings.** RAS lowers CV in 8/10 S7 and 5/6 S10 pairs. Gate perturbations change main scores by at most about 1.64%, alternative Mock means by about 0.12%. The top 1% of red events carry 16.78–30.78% of red signal; deleting them would change RAS by -1.18% to +6.29%. S10 B-positive fractions rise from 1.22% to 40.21% at endpoint labels. **Interpretation.** Normalization often reduces observed scale-related dispersion but retains expression weighting and does not make the reporter a molecular counter. BFP adds a detectable-expression covariate, not an editing-rate readout. **Limits.** A/B independent transfection wells and S10 ORCA–P2A–BFP linkage are user-confirmed; no optical/LOQ validation; 14/40 common B-bin scores are unavailable, preventing a complete standardized comparison. **Figure opportunities.** F04–F10 support normalization, heterogeneous improvement, blue prevalence, robustness and influence. **Sources.** `results/ras_results.csv`, `repeatability.csv`, `sensitivity.csv`, `high_expression_influence.csv`, `blue_profiles.csv`, `B_negative_transfer.csv`, `event_count_sensitivity.csv`, `bootstrap_draws.csv`; detailed report `reports/Layer1_Flow_Quantification.md`.





## Layer 2: corrected reporter calibration

The correction materially improves reference-model agreement, but leaves low-input overlap and high-end compression. The measured RAS values are identical. Affine training R² changes from **0.907229 to 0.964782**.

| model | RAS_RMSE_original | RAS_RMSE_corrected | RAS_MAE_original | RAS_MAE_corrected | inverse_recovery_n_original | inverse_recovery_n_corrected | inverse_MAE_mass_fraction_original | inverse_MAE_mass_fraction_corrected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| affine | 0.09339 | 0.049716 | 0.067668 | 0.041728 | 16 | 16 | 0.076864 | 0.062021 |
| isotonic | 0.1071 | 0.040048 | 0.077264 | 0.035899 | 15 | 16 | 0.10712 | 0.068027 |
| monotone_hinge_50 | 0.097955 | 0.036368 | 0.070266 | 0.030726 | 16 | 19 | 0.078095 | 0.061531 |

Forward leave-level metrics evaluate the same 16 interpolable held-out wells; the four endpoint wells cannot receive forward interpolation when their whole reference level is removed. Inverse availability is a separate criterion and can differ from forward availability. Do not compare inverse errors without also reporting available sample counts.

On the **same 14** held-out wells with estimable inverses in every corrected model:

| model | common_well_n | MAE_mass_fraction | RMSE_mass_fraction | bias_mass_fraction |
| --- | --- | --- | --- | --- |
| affine | 14 | 0.067168 | 0.078698 | -0.014091 |
| isotonic | 14 | 0.06258 | 0.072138 | 0.004986 |
| monotone_hinge_50 | 14 | 0.058475 | 0.06858 | 0.0032564 |

The lowest leave-level forward RMSE changes from affine in v3 to **the fixed-50% monotone hinge in v4** (0.036368). It also has the lowest inverse error in the matched subset. Isotonic remains best for leave-one-well prediction at already represented levels and is retained as the shape diagnostic. This is descriptive model preference within a small dataset, not an independently tested winner; model comparison itself uses these folds and no nested external model-selection validation exists.


The largest contiguous cross-model diagnostic range is **RAS 0.7845–1.0065**, corresponding to model point estimates spanning approximately **54.3–80.4% AC DNA mass**. This is an outcome of the stated grid/width screen, not an externally validated interval of assay accuracy. No RES is classified VALIDATED_WITHIN_DOMAIN. See [Layer 2 methods](reports/Layer2_RES_Calibration.md) and [before/after evidence](reports/S7_Calibration_Before_After_Comparison.md).

## Layer 3: unchanged molecular evidence and updated transfer assessment

Direct RAS-to-chromatogram-index prediction and BFP comparisons remain numerically unchanged. The recalculated hypothetical affine staged predictions equal direct predictions to numerical precision, and actual S7-to-S10 transfer remains unqualified. No absolute RNA fraction or PER is established. See [Layer 3 report](reports/Layer3_PER_Calibration.md).

## Scientific handoff

[Chinese summary](SONAR_S7_Correction_Scientific_Summary_ZH.md), [full corrected evidence](SONAR_Layer23_Evidence_Report.md), [correction provenance](reports/S7_Label_Correction_Record.md), and [figure inventory](SONAR_Layer23_Figure_Evidence_Inventory.md). Reproduction status is recorded in `reports/reproducibility_record.json`; it is computational reproducibility, not independent experimental validation.
