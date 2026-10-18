Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# Layer 2 — corrected reporter calibration and RES

## Reference inputs and actual fits
Twenty independent transfection wells, two per AC DNA mass level, retain identical RAS measurements and uncertainties. The 75/90 interpretation follows the team's probable retrospective transposition; 10→15 remains confirmed. Exact AC/INAC construct lengths remain unverified, so no molar conversion is introduced.

| corrected_ac_mass_fraction | mean_RAS | SD_RAS | independent_wells | original_acquisition_ids |
| --- | --- | --- | --- | --- |
| 0 | 0.53369 | 0.023324 | 2 | S7_0A;S7_0B |
| 0.05 | 0.51263 | 0.006303 | 2 | S7_5A;S7_5B |
| 0.15 | 0.56103 | 0.028405 | 2 | S7_10A;S7_10B |
| 0.2 | 0.56095 | 0.009664 | 2 | S7_20A;S7_20B |
| 0.3 | 0.67859 | 0.00046491 | 2 | S7_30A;S7_30B |
| 0.4 | 0.67754 | 0.010654 | 2 | S7_40A;S7_40B |
| 0.5 | 0.7444 | 0.017944 | 2 | S7_50A;S7_50B |
| 0.75 | 0.97872 | 0.031766 | 2 | S7_90A;S7_90B |
| 0.9 | 1.1322 | 0.0057949 | 2 | S7_75A;S7_75B |
| 1 | 1.1304 | 0.020481 | 2 | S7_100A;S7_100B |

The same v3 methods are refit: unweighted affine OLS; increasing isotonic regression with interpolation between fitted thresholds; continuous monotone piecewise-linear calibration with fixed knot A=0.5 and nonnegative segment slopes. All 20 wells remain in every primary fit. The hinge knot, random seed, 1,000 stratified bootstraps and model-comparison rules are documented in configuration. No high-level deletion or knot search selects the primary fit.

Affine intercept/slope: 0.465348, 0.672163. Hinge intercept, low slope and high slope: 0.500091, 0.491369, 0.857406. Parameters, isotonic thresholds, version, corrected reference basis, input hashes and correction hash are serialized in `models/layer23/S7_calibration_models.json`.

## Validation and model preference
| model | validation | training_R2 | RAS_prediction_n | RAS_RMSE | RAS_MAE | RAS_bias | inverse_recovery_n | inverse_MAE_mass_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| affine | in_sample_descriptive | 0.96478 | 20 | 0.043194 | 0.036513 | -2.1094e-16 | 0 | unavailable |
| affine | leave_one_well_out | 0.96478 | 20 | 0.048109 | 0.040562 | -0.0013125 | 17 | 0.057145 |
| affine | leave_one_reference_level_out | 0.96478 | 16 | 0.049716 | 0.041728 | 0.0059617 | 16 | 0.062021 |
| isotonic | in_sample_descriptive | 0.99638 | 20 | 0.013839 | 0.011573 | 1.6653e-17 | 0 | unavailable |
| isotonic | leave_one_well_out | 0.99638 | 20 | 0.023784 | 0.019377 | 0.00012053 | 15 | 0.06088 |
| isotonic | leave_one_reference_level_out | 0.99638 | 16 | 0.040048 | 0.035899 | -0.00053271 | 16 | 0.068027 |
| monotone_hinge_50 | in_sample_descriptive | 0.98104 | 20 | 0.031695 | 0.027609 | 5.0515e-16 | 0 | unavailable |
| monotone_hinge_50 | leave_one_well_out | 0.98104 | 20 | 0.038317 | 0.032906 | 0.00043197 | 20 | 0.053752 |
| monotone_hinge_50 | leave_one_reference_level_out | 0.98104 | 16 | 0.036368 | 0.030726 | -0.0026405 | 19 | 0.061531 |

Leave-one-well-out asks about a new well at a represented input; leave-one-level-out asks about interpolation across an omitted AC level. Technical events never become independent calibration samples. The endpoint exclusion and inverse availability are explicit in the fold table. The fixed-50% hinge is the preferred exploratory forward/inverse model under leave-level evaluation, with isotonic retained to expose plateaus. Hinge matched-case inverse MAE is **5.85 AC percentage points**, among 14 common estimable wells; this is internal recovery error, not an external accuracy guarantee. Affine lack-of-fit remains F(8,10)=12.542, p=0.0002707 under the limited pure-error assumptions.

## Inverse uncertainty and ranges
Model-specific diagnostic ranges:

| model | model_mass_low | model_mass_high | RAS_low | RAS_high | status |
| --- | --- | --- | --- | --- | --- |
| affine | unavailable | unavailable | unavailable | unavailable | NO_NARROW_INTERIOR_DOMAIN |
| isotonic | 0.507 | 0.828 | 0.75096 | 1.0581 | EXPLORATORY |
| monotone_hinge_50 | 0.545 | 0.908 | 0.78436 | 1.0956 | EXPLORATORY |

The largest contiguous cross-model diagnostic range is **RAS 0.7845–1.0065**, corresponding to model point estimates spanning approximately **54.3–80.4% AC DNA mass**. This is an outcome of the stated grid/width screen, not an externally validated interval of assay accuracy.

Isotonic exact plateau inverses remain intervals:

| RAS | exact_inverse_low | exact_inverse_high |
| --- | --- | --- |
| 0.52316 | 0 | 0.05 |
| 0.56099 | 0.15 | 0.2 |
| 0.67807 | 0.3 | 0.4 |
| 1.1313 | 0.9 | 1 |

Local slope and 0.01-RAS perturbation magnification are exported in `S7_local_inverse_resolution.csv`. Zero slope has no finite unique inverse; weak slope magnifies response error. A smooth model's point estimate does not resolve the empirical 90/100 overlap.

Uncertainty preserves the v3 policy: 1,000 within-level well bootstraps with paired-event and shared-control draws; the same control draw is shared with the inverse observation. Conditional quantiles report the fraction of bootstrap inverses available. No unavailable draw is clipped to 0 or 1. A separate envelope adds the 95th percentile of absolute leave-level response errors to bootstrap mean bands and is inverted as a set. These are exploratory compatibility sets, not calibrated coverage intervals. They omit preparation and independent batch uncertainty. The cross-model union is a further sensitivity bound, not a new probability statement.

## Independent-well and high-reference sensitivity
| model | scenario | reference_wells | input_min | input_max | maximum_abs_RAS_change_on_common_input |
| --- | --- | --- | --- | --- | --- |
| affine | A_wells_only | 10 | 0 | 1 | 0.012244 |
| isotonic | A_wells_only | 10 | 0 | 1 | 0.022462 |
| monotone_hinge_50 | A_wells_only | 10 | 0 | 1 | 0.01326 |
| affine | B_wells_only | 10 | 0 | 1 | 0.012244 |
| isotonic | B_wells_only | 10 | 0 | 1 | 0.022462 |
| monotone_hinge_50 | B_wells_only | 10 | 0 | 1 | 0.01326 |
| affine | omit_75 | 18 | 0 | 1 | 0.0030417 |
| isotonic | omit_75 | 18 | 0 | 1 | 0.0074971 |
| monotone_hinge_50 | omit_75 | 18 | 0 | 1 | 0.0052548 |
| affine | omit_90 | 18 | 0 | 1 | 0.030195 |
| isotonic | omit_90 | 18 | 0 | 1 | 0.061598 |
| monotone_hinge_50 | omit_90 | 18 | 0 | 1 | 0.027685 |
| affine | omit_100 | 18 | 0 | 0.9 | 0.0040101 |
| isotonic | omit_100 | 18 | 0 | 0.9 | 0.00093743 |
| monotone_hinge_50 | omit_100 | 18 | 0 | 0.9 | 0.041314 |
| affine | omit_90_and_100 | 16 | 0 | 0.75 | 0.040788 |
| isotonic | omit_90_and_100 | 16 | 0 | 0.75 | 0 |
| monotone_hinge_50 | omit_90_and_100 | 16 | 0 | 0.75 | 0.018595 |

These refits investigate dependence; they do not replace the primary 20-well fits. Removing corrected 90% can change isotonic predictions by about 0.062 RAS on the common domain, while the hinge changes by about 0.028. A/B-only fits provide a separate two-replicate sensitivity check. Omitting both high levels truncates support to 75%; a small within-range change does not demonstrate extrapolation beyond that range.

## RES status and domain
Every RES row includes original well/acquisition ID, input RAS, reporter population, model ID, corrected reference-basis ID, point or interval, bootstrap and compatibility uncertainty, label evidence status and applicable S7 domain. 54 of 60 model-by-well rows have unique model point inverses; this is not 60 independent samples and not 54 validated measurements.

- `VALIDATED_WITHIN_DOMAIN`: Requires qualified reference/optical assay, supported uncertainty and independent external validation; no v4 sample assigned.
- `EXPLORATORY`: An in-domain model-conditional estimate under retrospectively corrected S7 metadata; not validated RNA or AC accuracy.
- `NONIDENTIFIABLE`: Exact plateau has an interval inverse; no arbitrary point.
- `OUT_OF_CALIBRATION_RANGE`: Response outside fitted range; unavailable, not clipped or extrapolated.
- `NOT_CALIBRATED`: Missing or incompatible calibration population/domain.

No S10 population receives a qualified S7 RES. `S10_hypothetical_S7_mapping.csv` is an explicitly named arithmetic sensitivity with compatibility spans; its actual S10 RES status is `NOT_CALIBRATED`.
