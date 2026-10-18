# Layer 2 — Final operational RES
Release: `sonar-science-v1.0-s7s10`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.

The fixed-knot monotone hinge is frozen as the primary operational reference model. Affine and isotonic remain benchmarks. This completes executable reference-equivalent calculation while retaining explicit research status.

## Calibration and selection
S7 has 20 independent transfection wells, two per corrected AC DNA mass input: 0, 5, 15, 20, 30, 40, 50, 75, 90 and 100%. Original source “10” means 15%; original 75A/B mean 90%; original 90A/B mean 75%. The last interchange is the experimental team's retrospective probable correction, not independently verified preparation evidence. Improved fit is not proof of the correction. Original filenames, event bytes and well RAS are unchanged.

The equation is `g(A) = 0.500091476458275 + 0.491368713316119 A + 0.366037234211599 max(0, A - 0.5)`. Lower and upper slopes are 0.491369 and 0.857406; inverse sensitivities are 2.035 and 1.166 fraction per RAS unit. Three parameters and the pre-existing fixed 50% knot provide a transparent continuous inverse. The model has the lowest leave-reference-level forward RMSE and the lowest matched-subset inverse MAE of the three candidates. Isotonic performs better in leave-one-well-out forward prediction, where the same reference level remains in training. Model selection and evaluation used the same small dataset, so selection optimism is not removed by external or nested model-family validation.

| model | forward_prediction_n | forward_RMSE_RAS | total_held_out | unique_inverse_n | out_of_range_n | inverse_MAE_pp | inverse_RMSE_pp | inverse_bias_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| affine | 16 | 0.0497156 | 20 | 16 | 4 | 6.20211 | 7.42233 | -0.908057 |
| isotonic | 16 | 0.0400479 | 20 | 16 | 4 | 6.80269 | 7.72928 | 0.313488 |
| monotone_hinge_50 | 16 | 0.0363679 | 20 | 19 | 1 | 6.15312 | 7.07775 | 0.119745 |

Forward RMSE uses 16 evaluable interior held-out wells: excluded 0%/100% levels lie outside each fold's training input range. Inverse columns use observed held-out RAS and their own successful-inversion denominators. They answer a different question.

## Inverse performance without hiding failures
| validation | total_held_out | unique_inverse_n | out_of_range_n | inverse_MAE_pp | inverse_RMSE_pp | inverse_bias_pp | compatible_set_coverage_all | conditional_bootstrap_coverage_given_interval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leave_one_reference_level_out | 20 | 19 | 1 | 6.15312 | 7.07775 | 0.119745 | 0.8 | 0.25 |
| leave_one_well_out | 20 | 20 | 0 | 5.37517 | 6.09906 | -0.250852 | 0.95 | 0.15 |

The primary model uniquely inverts 20/20 leave-one-well-out observations (MAE 5.375 pp; RMSE 6.099 pp) and 19/20 leave-one-reference-level-out observations (MAE 6.153 pp; RMSE 7.078 pp; bias +0.120 pp). The one failed level-held-out case is out of the fitted response range; its error is undefined, not zero. A full-20 point MAE is therefore not defined. Restricting to the 16 held-out wells whose true fractions are inside training range gives 16/16 unique inverses and MAE 5.327 pp, RMSE 6.115 pp. Endpoint observations must not be called validated interpolation merely because their observed signal has an inverse.

The previously quoted 5.85 pp is exactly 5.847525 pp for 14 wells uniquely inverted by all three models, not the full held-out set. That common subset includes two 0% observations outside their fold's input domain. Its purpose is like-for-like model comparison. Full denominators and per-level errors remain in the tables.

## Uncertainty findings
The new outer-held-out uncertainty evaluation resamples wells within training levels (500 draws/fold), synchronizes paired event/shared-control draws, and estimates discrepancy from inner held-out training levels only. No held-out outcome selects the interval width. Conditional bootstrap intervals cover only 3/20 true inputs under leave-one-well-out and 5/20 under leave-one-level-out. This demonstrates that narrow measurement/parameter intervals alone inadequately capture model discrepancy. They are not the headline uncertainty.

The broader nonnominal compatibility sets cover 19/20 and 16/20 respectively. Level-held-out interior coverage is 16/16, with wide sets; four endpoint truths cannot be covered by sets restricted to the fold's observed input domain. These are empirical internal coverages on few dependent folds, not validated nominal probabilities. Two reference wells per level cannot estimate preparation-batch or between-day variation. All unsuccessful inversions, conditional denominators, uncertainty sets and domain labels are exported.

## Four domains and real outputs
Numerical A domain: 0–1. Numerical response domain: 0.500091–1.174479 RAS. Observed well responses: 0.508171–1.144856; observations exist at ten discrete levels, not every continuous A.

The re-evaluated conservative internal screen is RAS 0.7845–1.0065, corresponding under the frozen hinge to 54.52–80.41% AC mass equivalent. Its reference-only grid criteria reproduce v4; adding actual sample measurement uncertainty must be evaluated separately for both models. Isolated passing grid points above 1.0065 are not joined across gaps. Only the actual 75% reference level (two wells) lies inside this screen; the smooth interval must not imply dense empirical validation. The width threshold is a declared engineering diagnostic. It is not a validated assay range.

All 20 S7 wells have model-defined point inverses, spanning 1.64%–96.55% AC DNA mass equivalent. Two fall inside the reference-response screen and have primary-model sample compatibility widths below 20 pp, but their measurement-expanded primary/isotonic union widths are 20.8 and 21.8 pp. They are classified PRIMARY_INFORMATIVE_CROSS_MODEL_SET_BROAD: neither passes the stricter 20 pp joint sample screen. Fourteen have weak/boundary support, and four are in the observed high-end flattening region. All numerical estimates remain available for research. The 90% versus 100% response means are 1.132248 and 1.130373; their difference −0.001875 is much smaller than its n=2 uncertainty. This supports poor separation, not equivalence or proven detector saturation. The primary positive upper slope does not remove that empirical limitation.

Research mode emits compatible point estimates and intervals with all limitations. Routine quantitative mode returns no qualified RES in this release; it retains the research result in its separate field. Transfer to S10 is unqualified: matching HEK293T and detector profile does not establish construct, loading, treatment, time, reference axis or RNA-population compatibility. S10 reporter values are below the internal screen; no ordinary S10 RES or R+B+ transfer is emitted. A separately named hypothetical mapping is retained for sensitivity only.

Sources: [model specification](../science/RES_Primary_Model_Specification.md), [full validation](../results/layer2/RES_Inverse_Validation.csv), [comparison](../results/layer2/RES_Model_Comparison.csv), [sample results](../results/layer2/RES_Sample_Results.csv), [domains](../results/layer2/RES_Calibration_Domain.json), [worked examples](../science/RES_Worked_Examples.md), [transfer audit](../results/calibration/S7_S10_compatibility.csv).
