Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# Original versus corrected S7 calibration

## Quantitative result
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

## What disappeared and what remains
The former 75→90% decrease becomes an increase from **0.978722 to 1.132248** under the authorized interpretation; all 11 saved gate/background/threshold sensitivities preserve that ordering. These are the same underlying acquisitions. Corrected 90% and 100% means are **1.132248 and 1.130373**, a difference of **-0.001875 RAS**. With only two wells per level, the descriptive Welch interval for the difference is [-0.1410, 0.1372]. It does not distinguish them and does not prove equivalence or a biological saturation mechanism.

Low-input reversals/overlap at 0–5%, 15–20% and 30–40% persist. Isotonic pooling retains those plateaus and adds a 90–100% plateau. The smooth hinge imposes an increasing high segment and cannot independently demonstrate separation of 90% from 100%.

## Did usable RES expand?
Yes, **model-conditional, reference-specific exploratory RES becomes more defensible in the middle range**. The earlier claim that every region is broadly unresolved no longer describes the corrected results. The largest contiguous cross-model diagnostic range is **RAS 0.7845–1.0065**, corresponding to model point estimates spanning approximately **54.3–80.4% AC DNA mass**. This is an outcome of the stated grid/width screen, not an externally validated interval of assay accuracy.

The diagnostic requires a unique model inverse, positive local slope, and the union of isotonic/hinge discrepancy envelopes no wider than 0.20 AC mass fraction, with neither reference boundary truncating the set. The 0.20 width threshold is retained from v3; the cross-model/interior criteria guard against model dependence and artificial narrowing near boundaries. It does not mean ±10 percentage-point validated accuracy, and the envelopes are not calibrated 95% confidence intervals. The numerical grids have 0.001 mass-fraction and 0.0005 RAS spacing. Tiny isolated pass points at the threshold boundary are retained in the exported table but do not extend the largest contiguous range; these grid endpoints do not imply four-decimal assay precision.

No `VALIDATED_WITHIN_DOMAIN` RES is assigned. The retrospective labels, two wells per level, unknown exact reference constructs, incomplete optical validation and absence of blinded independently prepared mixtures still prevent an externally validated quantitative claim. Additional reference calibration is required for such a claim. AC DNA mass equivalent is never RNA-editing percentage.

Sources: corrected well/mean tables, `S7_before_after_model_comparison.csv`, `S7_matched_inverse_validation.csv`, `S7_cross_model_inverse_support.csv`, `S7_adjacent_level_distinguishability.csv`, and all detailed calibration outputs under `results/calibration/`.
