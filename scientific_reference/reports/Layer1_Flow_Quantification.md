Analysis version: `sonar-fresh-s7-s10-20261012-v2`. Review date: 2026-10-13. Authorized experimental series: S7 and S10 only. All numerical results below were regenerated from copied original inputs.

## Scientific question
What can paired red and green fluorescence quantify, and does continuous red normalization reduce observed variation?

## Implemented quantity
For exactly the same selected events, `g = GFP-A - mean Mock GFP-A` and `r = mCherry-A - mean Mock mCherry-A`; **RAS = sum(g) / sum(r)**. Accumulation is float64 on linear values. It is also a red-weighted mean of per-event g/r when r>0. It is not the arithmetic mean of cell ratios, a percentage of edited cells, or the fraction of edited RNA. mCherry normalization can remove a shared expression scale under proportionality assumptions; it does not remove differential maturation, stability, detector effects, or substrate-loading biology.

The primary population is the common quality/scatter/singlet population with red above the candidate quantification boundary. There is no EGFP-positive gate. Signed corrected green values are retained; 0.33–6.25% of selected events have negative corrected green in these acquisitions. No epsilon, winsorization, independent channel clipping or sample-specific fluorescence gate is used.

A numerical score requires at least 100 selected events and a positive red denominator whose conditional event-sampling relative standard error is at most 10%. Those are declared provisional engineering screens, not empirically validated assay specifications. They do not resolve optical uncertainty. All 32 reporter populations meet this numerical screen: selected counts 15,249–33,225, red effective counts 1225–4553, and maximum relative denominator SE 2.77%. Effective events are weight-concentration diagnostics, never biological n.

## Per-acquisition primary results
Raw and corrected means refer to the same reporter-selected population. An all-singlet raw-green mean is exported separately. Fluorescence units are linear detector a.u.; RAS is a green/red detector-channel ratio.

| acquisition_id | n_selected | mean_G_raw | mean_G_corrected | mean_R_corrected | ras | event_ci_low | event_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S7_0A | 28305 | 86137 | 83137 | 1.5111e+05 | 0.55019 | 0.5425 | 0.55803 |
| S7_0B | 27640 | 79609 | 76609 | 1.4812e+05 | 0.5172 | 0.50988 | 0.52457 |
| S7_100A | 29732 | 1.7311e+05 | 1.7011e+05 | 1.4859e+05 | 1.1449 | 1.1345 | 1.1551 |
| S7_100B | 29421 | 1.734e+05 | 1.704e+05 | 1.527e+05 | 1.1159 | 1.1052 | 1.127 |
| S7_10A | 29027 | 84258 | 81258 | 1.3983e+05 | 0.58111 | 0.57351 | 0.58888 |
| S7_10B | 23047 | 70406 | 67406 | 1.2461e+05 | 0.54094 | 0.53386 | 0.54794 |
| S7_20A | 25354 | 76669 | 73669 | 1.2975e+05 | 0.56778 | 0.56099 | 0.57451 |
| S7_20B | 28054 | 85253 | 82253 | 1.4844e+05 | 0.55411 | 0.54792 | 0.56031 |
| S7_30A | 25975 | 94374 | 91374 | 1.3459e+05 | 0.67892 | 0.67084 | 0.68664 |
| S7_30B | 26524 | 96125 | 93125 | 1.373e+05 | 0.67827 | 0.67081 | 0.68585 |
| S7_40A | 27371 | 92794 | 89794 | 1.3107e+05 | 0.68508 | 0.67766 | 0.69242 |
| S7_40B | 25574 | 93256 | 90256 | 1.3471e+05 | 0.67001 | 0.66236 | 0.67801 |
| S7_50A | 22180 | 95309 | 92309 | 1.2193e+05 | 0.75709 | 0.74927 | 0.76548 |
| S7_50B | 23163 | 88026 | 85026 | 1.162e+05 | 0.73171 | 0.72394 | 0.73947 |
| S7_5A | 28938 | 80518 | 77518 | 1.4991e+05 | 0.51709 | 0.51006 | 0.52436 |
| S7_5B | 25884 | 76143 | 73143 | 1.4393e+05 | 0.50817 | 0.50046 | 0.51544 |
| S7_75A | 15249 | 81746 | 78746 | 69298 | 1.1363 | 1.1232 | 1.1495 |
| S7_75B | 16239 | 84213 | 81213 | 71988 | 1.1282 | 1.1146 | 1.1411 |
| S7_90A | 33225 | 1.9102e+05 | 1.8802e+05 | 1.8779e+05 | 1.0012 | 0.99241 | 1.0093 |
| S7_90B | 32207 | 1.7685e+05 | 1.7385e+05 | 1.8181e+05 | 0.95626 | 0.94875 | 0.96417 |
| S10_1_0_A | 22106 | 96056 | 93056 | 1.4048e+05 | 0.6624 | 0.64577 | 0.67915 |
| S10_1_0_B | 19124 | 86284 | 83284 | 1.3691e+05 | 0.60832 | 0.58708 | 0.63168 |
| S10_1_0.5_A | 20151 | 86275 | 83275 | 1.3893e+05 | 0.5994 | 0.5826 | 0.61821 |
| S10_1_0.5_B | 19205 | 85051 | 82051 | 1.4067e+05 | 0.5833 | 0.56431 | 0.60433 |
| S10_1_1_A | 23263 | 92800 | 89800 | 1.4616e+05 | 0.61439 | 0.60134 | 0.62727 |
| S10_1_1_B | 18290 | 73894 | 70895 | 1.2727e+05 | 0.55706 | 0.53503 | 0.58805 |
| S10_1_2_A | 20719 | 75281 | 72281 | 1.3804e+05 | 0.52363 | 0.51075 | 0.5366 |
| S10_1_2_B | 20011 | 83697 | 80697 | 1.4181e+05 | 0.56905 | 0.55266 | 0.58673 |
| S10_1_4_A | 21946 | 92875 | 89875 | 1.4058e+05 | 0.63933 | 0.62146 | 0.65928 |
| S10_1_4_B | 19923 | 85394 | 82394 | 1.3716e+05 | 0.6007 | 0.58289 | 0.61906 |
| S10_1_8_A | 21818 | 87328 | 84329 | 1.4737e+05 | 0.57223 | 0.55858 | 0.58632 |
| S10_1_8_B | 20861 | 82167 | 79167 | 1.3938e+05 | 0.56799 | 0.5534 | 0.58413 |

## Does mCherry normalization improve repeatability?
The user confirms A/B are two independent transfection wells under each condition. The following calculation is **within-experiment independent-transfection-well repeatability (n=2 per condition)**. Independent cultures, days and batches have not been established. Each CV uses only the two wells at the same condition: sample SD with ddof=1 divided by absolute mean, times 100. Different AC fractions or editor ratios are never treated as replicates. Each condition contributes equally to the median across conditions. Raw-green and RAS CVs use the same selected events.

| series | mean_G_corrected | mean_G_raw | ras | pairs_improved | pair_n |
| --- | --- | --- | --- | --- | --- |
| S10 | 6.9611 | 6.7109 | 5.1424 | 5 | 6 |
| S7 | 4.8208 | 4.697 | 1.7673 | 8 | 10 |

S7 improves in 8/10 pairs; S10 improves in 5/6. S7 labels 40 and 100 and S10 label 0.5 have higher RAS CV than raw-green CV. Normalization reduces between-well dispersion in most conditions but does not establish biological accuracy, a universal advantage or removal of all expression dependence. Exact pair values, including unfavorable cases, are in `results/repeatability.csv`.

Within common red-intensity bins, RAS changes across the reporter-expression range. Those strata confound expression, cell state, noise and possible substrate effects; they are not randomized reporter-load experiments. S7/S10 contain no verified locked-state reporter-dose series that isolates these mechanisms. Do not claim perfect dose invariance.

## What BFP adds
S10 B-positive fractions among reporter-selected events increase from 1.22% at label 1:0 to 40.21% at 1:8 using the Mock boundary. This is an observable detection dimension. The no-editor-labelled reporter acquisitions themselves have about 1.2% B-positive events, exceeding the nominal 0.5% Mock tail. A reporter-only-derived alternative B threshold of 1,109.878 a.u. changes these fractions; at 1:8 the average is about 37.32%. This demonstrates why Mock alone does not validate the multicolor B boundary.

The program separately calculates reporter, blue-positive reporter and blue-negative reporter populations for S10. The user confirms ORCA–P2A–BFP linkage for this S10 experiment. For editor-present conditions, blue-positive reporter populations are therefore routed as exploratory reporter/editor co-expression populations. This is experimental metadata confirmation, not sequence verification or validation of the B-positive optical boundary. `CEF_editor_exploratory` reports the B+ fraction among reporter-eligible events; `CEF_editor_verified` remains unavailable because the boundary is not validated. The zero-editor B+ tail is a negative-control diagnostic and is not an editor co-expression fraction. S7's BFP-related preparation annotation does not establish editor linkage, so it is not routed into editor co-expression mode. In the 1:0 group, blue-positive scores are unavailable because denominator relative SEs are approximately 15.9% and 21.0%, despite 262 and 241 events. They are not replaced by zero.

For positive ratio labels, the blue-selected RAS means are:

| condition_label | ras_mean | ras_sd | acquisition_n |
| --- | --- | --- | --- |
| 0 | unavailable | unavailable | 0 |
| 0.5 | 0.66756 | 0.038022 | 2 |
| 1 | 0.63601 | 0.020091 | 2 |
| 2 | 0.57379 | 0.039969 | 2 |
| 4 | 0.63879 | 0.023995 | 2 |
| 8 | 0.57553 | 0.0054922 | 2 |

Neither the overall reporter score nor the blue-selected score increases monotonically with editor-ratio label. BFP cannot be read as exact active-editor abundance or increasing editing efficiency. The red-share-weighted decomposition of blue-positive/negative populations reconstructs reporter RAS to floating-point precision; the weight is red signal, not the cell-count fraction.

Common B+ bins were built from the intersection of 5th–95th percentile supports across all ten positive-ratio acquisitions. They retain 113–2146 events per bin, but 14/40 bins fail the denominator/count screen. There is no complete quantitatively accepted common-bin grid, so no standardized BFP-matched aggregate is reported. The incomplete profiles are useful diagnostics only.

## Uncertainty, robustness and bright-cell influence
There are 2,000 paired-event bootstrap draws per available population. Pointwise 95% intervals condition on the acquisition, fixed gate and background policy. A second interval includes Gaussian uncertainty of the control means with their paired green/red covariance; the same control perturbation draw is shared across acquisitions. This does not include biological variability, control-well/batch uncertainty, gate estimation, optical spillover or molecular calibration. The maximum reporter-population endpoint shift between the first 1,000 and all 2,000 draws is 4.44% of the full interval width, documenting Monte Carlo stability at the precision reported. Full draws are exported. Independent biological confidence intervals are unavailable.

Event-count sensitivity uses 100 subsamples without replacement at supported sizes 100, 500, 1,000, 5,000, 10,000 and 20,000. It estimates finite-acquisition sampling sensitivity; an interval at the full event count would collapse and must not be called biological precision.

| scenario | min | max |
| --- | --- | --- |
| Mock1_mean | 0.045805 | 0.11679 |
| Mock2_mean | -0.11676 | -0.045797 |
| control_median_NOT_expected_additive | 0.10423 | 0.34323 |
| negative_quantile_0.99 | 0.015954 | 0.064218 |
| negative_quantile_0.999 | -0.40197 | -0.091807 |
| no_subtraction | 0.97748 | 3.4958 |
| scatter_0.975 | -1.6435 | 0.8107 |
| scatter_0.995 | -0.24504 | 0.26487 |
| singlet_2.5MAD | -0.57521 | 0.32975 |
| singlet_3.5MAD | -0.33863 | 0.33157 |
| without_time_filter | 0 | 0.36222 |

These relative changes are percentages. Gate variants refit the corresponding control background and thresholds but preserve the same fixed scatter geometry; this tests the full perturbed context. Background variants keep events fixed. Median background and no subtraction are explicitly alternative estimands/sensitivity references, not selected policies. Switching between the two control means changes primary RAS by no more than about 0.12%; the largest tested geometric perturbation changes it by about 1.64%. A small perturbation effect does not validate unknown spillover.

The top 1% of red-expressing events contribute 16.78–30.78% of total red signal. Removing them would change RAS by -1.18–6.29%; they remain in the primary estimator. The largest one-event leave-out change is 0.01133 RAS units. This concentration is scientifically relevant even though no single event dominates the main reporter populations.

## Interpretation domain and remaining limits
All fluorescence scores in this release are **exploratory detector-scale RAS**. The stored compensation matrix is identity and `USCOMP=False`; no matched single-color controls establish negligible spillover. Mock-derived boundaries have only acquisition-level negative-transfer checks. User metadata confirms independent A/B transfection wells, S7 AC mass fractions (source label 10 means 15%), S10 doses and ORCA–P2A–BFP linkage, and molecular labels 1/2→A and 3/4→B with RNA extracted after flow at the same experimental time point. Exact AC/INAC states, sequence-level construct identity, sampled RNA population and molecular assay qualification remain unresolved. These restrictions are separate from successful numerical computation. Validated RAS, RES and PER fields remain unavailable; unavailable never means zero.

RAS is useful here as a declared population-level reporter response in one instrument context. Claim conditional robustness and within-experiment independent-transfection-well repeatability improvement in most conditions. No evidence establishes RNA-editing accuracy, independent-culture or cross-day reproducibility, or a universal editor ranking.

## Source tables and figure opportunities
`ras_results.csv`, `repeatability.csv`, `bootstrap_draws.csv`, `event_count_sensitivity.csv`, `sensitivity.csv`, `high_expression_influence.csv`, `red_profiles.csv`, `blue_profiles.csv`, `B_negative_transfer.csv`, `binary_populations.csv` and `partition_identity.csv` under `results/`. F04–F10 address normalization, pair dispersion, BFP, robustness, event support and reference weighting.
