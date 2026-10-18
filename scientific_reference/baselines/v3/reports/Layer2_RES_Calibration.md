Version: `sonar-s7-s10-layer23-20261013-v3`. Reviewed 2026-10-13. Upstream Flow Quantification: `sonar-fresh-s7-s10-20261012-v2`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.

# Layer 2 — Reporter Calibration and RES

## Actual fitted models
The 20 independent S7 transfection wells are fit on confirmed **AC DNA mass fraction A∈[0,1]**, with source label 10 corrected to 0.15. No exact AC/INAC plasmid identities/lengths were established in the permitted construct records; no molar conversion is made. Generic 7,498-bp design length is not substituted for both reference plasmids. AC mass fraction is never treated as edited-RNA fraction.

Three models were specified and executed: affine OLS, increasing isotonic regression with linear interpolation between fitted thresholds, and a continuous monotonic piecewise-linear model with a fixed 50% knot and nonnegative segment slopes. The hinge has three parameters, affine two; no high-degree polynomial or fitted knot search is used. Wells receive equal weight. All 75%, 90% and 100% observations remain in the fit.

Affine parameters: intercept **0.474000**, slope **0.651806 RAS per unit AC mass fraction**. Hinge parameters and isotonic thresholds are serialized with version and upstream hashes in `models/layer23/S7_calibration_models.json`; parameter bootstrap draws are exported. A fitted function is not a validated measurement calibration.

## Internal validation results
| model | validation | RAS_prediction_n | RAS_RMSE | inverse_recovery_n | inverse_MAE_mass_fraction | inverse_RMSE_mass_fraction |
| --- | --- | --- | --- | --- | --- | --- |
| affine | in_sample_descriptive | 20 | 0.070104 | 0 | unavailable | unavailable |
| affine | leave_one_well_out | 20 | 0.078044 | 17 | 0.066914 | 0.082496 |
| affine | leave_one_reference_level_out | 16 | 0.09339 | 16 | 0.076864 | 0.09392 |
| isotonic | in_sample_descriptive | 20 | 0.037011 | 0 | unavailable | unavailable |
| isotonic | leave_one_well_out | 20 | 0.050725 | 15 | 0.095736 | 0.12316 |
| isotonic | leave_one_reference_level_out | 16 | 0.1071 | 15 | 0.10712 | 0.13146 |
| monotone_hinge_50 | in_sample_descriptive | 20 | 0.068523 | 0 | unavailable | unavailable |
| monotone_hinge_50 | leave_one_well_out | 20 | 0.07833 | 17 | 0.066322 | 0.078275 |
| monotone_hinge_50 | leave_one_reference_level_out | 16 | 0.097955 | 16 | 0.078095 | 0.091402 |

Leave-one-well-out predicts a new well at an already represented reference level; leave-one-reference-level-out tests interpolation across an omitted concentration. All technical/event resampling remains within its parent well. Neither is external validation with independently prepared blinded mixtures. The four 0%/100% endpoint wells cannot receive forward interpolation predictions when their whole level is held out; they are explicitly unavailable, giving 16 in-domain forward predictions. Inverse recovery has its own availability counts and is never scored after clipping.

Isotonic forward RMSE is 0.05073 in leave-one-well-out but 0.10710 in leave-one-level-out, versus affine 0.07804 and 0.09339. Thus fitting away within-level noise is not evidence of a reliable inverse. The affine leave-level inverse MAE is 0.07686 mass fraction (7.69 AC percentage points), among the 16 available recoveries; this excludes non-estimable cases and is not a universal accuracy specification. Formal affine lack-of-fit relative to within-level pure error is F(8,10)=35.08, p=2.47e-06; its same-session independent-error assumptions and n=2 replication limit interpretation.

## The 75%/90% anomaly was retained and investigated
Source FCS tube labels, the original photograph and team-confirmed mass axis still identify 75/90/100; no independent record justifies relabeling 90. Both 90% well RAS values are below both 75% values. Mean green rises from about 80,000 to 181,000 a.u. and red rises from about 70,600 to 184,800 a.u.; the larger proportional red rise explains the ratio reversal arithmetically. It does not identify its preparation or biological cause. Counts, denominator precision, bright-event influence and time QC were examined. The reversal persists in **all 11** background/gate/threshold sensitivity scenarios. No S7 plate-reader workbook was present for an independent same-series check. S8 data were not imported to fill that gap.

## Inverse sets and uncertainty
Inversion is restricted to each model's fitted response range. Outside values remain unavailable rather than extrapolated or clipped. Isotonic exact plateaus have a set-valued inverse:

| RAS | exact_inverse_low | exact_inverse_high |
| --- | --- | --- |
| 0.52316 | 0 | 0.05 |
| 0.56099 | 0.15 | 0.2 |
| 0.67807 | 0.3 | 0.4 |
| 1.0555 | 0.75 | 0.9 |

Thus low intervals 0–5%, 15–20%, 30–40%, and high 75–90% can be identical under this fitted monotonic model. Original well variability and model mismatch broaden ambiguity further. The endpoint values near 75% and 100% are also close empirically; a single model-assumed point can conceal that conflict.

One thousand stratified bootstraps resample the two wells within each level and propagate the stored paired-event/shared-control draws. The same control draw is preserved between reference and inverse observation within a replicate. This estimates uncertainty conditional on this small, fixed reference design; it omits mixture-preparation and batch uncertainty. In-range inverse draws receive conditional percentile intervals with the in-range fraction reported. Failed draws are not clipped or converted to zero; conditional intervals are not unconditional coverage guarantees.

A second, deliberately conservative diagnostic adds the empirical 95th percentile of absolute leave-level residuals to bootstrap mean-response bands and inverts the resulting response envelope. These **compatibility sets are not calibrated 95% confidence intervals**. Across the evaluated response grid, the narrowest set spans over 0.21 mass fraction for every model; none meets the prespecified exploratory width screen of ≤0.20. The numeric screen is not a validated assay specification. The present evidence therefore establishes **no validated RES domain**. `S7_RES_results.csv` retains model-specific exploratory inverses, plateaus, out-of-range states and uncertainty separately from blank `RES_validated`.

## S7-to-S10 transfer
HEK293T and the detector profile match. Reporter loading in S7, precise AC/INAC states/constructs, treatment/TMP, linked editor effects, and the reference-to-OpenA biological bridge remain unresolved. S7 reporter-population calibration is not qualified for R+B+-selected S10. Same-mode S10 reporter values are mapped only in a distinctly labelled hypothetical sensitivity table. No S10 co-expression score receives S7 RES, and no mapped value is promoted into biological PER.

Sources: `results/calibration/S7_model_comparison.csv`, `S7_calibration_predictions.csv`, `S7_internal_validation.csv`, `S7_parameter_bootstrap.csv`, `S7_inverse_identifiability.csv`, `S7_RES_results.csv`, anomaly tables and `S7_S10_compatibility.csv`. L23_07–10 show fits, residuals, ambiguity and the actual anomaly.
