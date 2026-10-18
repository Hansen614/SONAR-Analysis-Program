Version: `sonar-s7-s10-layer23-20261013-v3`. Reviewed 2026-10-13. Upstream Flow Quantification: `sonar-fresh-s7-s10-20261012-v2`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.

# Layer 3 — Biological Calibration and PER

## Qualified endpoint versus available endpoint
The intended endpoint is C280 edited fraction in OpenA reporter RNA at sampling, with C→U in the forward transcript. Sequence/codon support and parent-well mapping are now available. Quantitative RNA fractions are not: the actual measured cell population, DNA-exclusion controls, known-mixture assay response and absolute uncertainty remain unresolved. No endogenous or introduced APOE result is substituted.

The available numerical endpoint is a **raw direction-averaged C280 chromatogram composition index**, calculated within complete molecular-label pairs and then averaged within each well. It is neither a cell fraction nor a calibrated RNA fraction. The raw index avoids defining a held-out endpoint using all control wells' background; fitting an intercept makes its constant background shift irrelevant to the within-release association. The corrected index remains available for descriptive plots.

The final pairing table has 12 independent wells, each linked to 2 molecular labels and 4 original reads, reporter RAS, co-expression RAS where estimable, B-positive fraction, doses, technical uncertainty and assay status. There are only 10 defined editor co-expression RAS values, because no-editor R+B+ tails are not editor-expressing populations and fail the denominator screen. RNA population remains undocumented and is not assumed to be sorted R+B+.

## Observed relationship
| predictor | n | pearson | spearman |
| --- | --- | --- | --- |
| editor_dna_ng | 12 | 0.97232 | 0.94705 |
| blue_positive_fraction_reporters | 12 | 0.97642 | 0.96503 |
| RAS_reporter | 12 | -0.28818 | -0.3007 |
| RAS_editor_coexpression | 10 | -0.52864 | -0.41818 |
| median_B_raw | 12 | 0.97684 | 0.94406 |
| mean_R_corrected | 12 | 0.39221 | 0.35664 |

The index tracks editor dose and B-positive prevalence strongly within this dataset. It has weak negative association with reporter RAS and a negative association with co-expression RAS. These associations cannot establish causality, absolute RNA editing or a transferable model; they reveal that the present optical activity metric does not track the candidate-site chromatogram response as expected.

## Actual prediction attempts
Simple OLS models were fitted to the relative index: training mean only; reporter RAS alone; B-positive detection fraction alone; log(1+editor ratio); reporter RAS plus B fraction; and, on the same positive-dose subset, co-expression RAS and matched mean/B baselines. Models and bootstrap coefficients are saved. There is no hyperparameter tuning or hidden search over covariates. Additional B information is named explicitly; it does not redefine RAS or RES.

All technical labels/directions from each well stay together. Leave-one-well-out uses 11 wells (or 9 for the positive-dose subset). Leave-one-dose-out withholds both wells at that condition. Predictors outside training ranges are flagged; unconstrained signal-model predictions and model-based intervals are not clipped into a biological percentage. Ordinary t prediction intervals assume the fitted linear model and residual structure; their reported internal coverage is not assay accuracy or externally verified coverage.

| model | validation | well_n | RMSE | MAE | bias | prediction_interval_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| training_mean | leave_one_well_out | 12 | 0.076558 | 0.065745 | -1.8504e-17 | 0.91667 |
| training_mean | leave_one_dose_out | 12 | 0.083797 | 0.071523 | -9.2519e-18 | 0.83333 |
| reporter_RAS | leave_one_well_out | 12 | 0.080562 | 0.072251 | 0.0033187 | 1 |
| reporter_RAS | leave_one_dose_out | 12 | 0.090155 | 0.079761 | 0.004185 | 0.83333 |
| B_detection_fraction | leave_one_well_out | 12 | 0.017411 | 0.014241 | -0.00067659 | 0.91667 |
| B_detection_fraction | leave_one_dose_out | 12 | 0.019219 | 0.016816 | -0.0030498 | 0.91667 |
| editor_dose_log1p | leave_one_well_out | 12 | 0.026123 | 0.023032 | -0.0016841 | 1 |
| editor_dose_log1p | leave_one_dose_out | 12 | 0.034325 | 0.029796 | -0.0064514 | 0.91667 |
| reporter_RAS_plus_B | leave_one_well_out | 12 | 0.019401 | 0.016356 | 0.00094962 | 0.91667 |
| reporter_RAS_plus_B | leave_one_dose_out | 12 | 0.019814 | 0.017507 | -0.0017524 | 0.91667 |

For leave-one-dose-out, RAS-only RMSE **0.09015** is worse than the training-mean baseline **0.08380**. B-fraction-only RMSE is **0.01922**. Reporter RAS plus B gives **0.01981**, with no numerical advantage here over B alone. On the 10 positive-dose wells, co-expression-RAS RMSE is **0.09022**, versus its matched mean baseline **0.08492**. These are units of the relative chromatogram index, never percentage-point RNA editing errors. The small six-dose design, shared processing context and unqualified endpoint make all predictive results exploratory. Good dose-linked performance may largely encode the experimental titration rather than transferable mechanistic prediction.

## Direct versus staged interpretation
A staged `RAS→RES→RNA` model is **not fitted**: there is no validated S7-to-S10 calibration bridge or quantitatively qualified molecular fraction. Its result table states the exact reasons. A separate mathematical sensitivity maps reporter RAS through the fitted affine S7 inverse only where in range, then repeats the same linear-index prediction on identical held-out wells. Maximum direct/staged prediction difference is 2.91e-16. An invertible affine rescaling supplies no new sample information; this algebraic comparison is not evidence of biological transfer and is not PER.

## Explaining the discordance without claiming a cause
The sequence signal, RAS and BFP answer different questions. RAS is red-expression-weighted within selected reporter events; RT-PCR/Sanger samples molecules from an undocumented population; B detection measures expression prevalence under a provisional threshold. Those differences can change weighting and dilute or enrich a signal. Reporter maturation, DD stability/TMP conditions, differences between locked AC/INAC references and edited OpenA, and optical spillover are additional hypotheses. The present experiment does not isolate them. The observed molecular/optical mismatch should be reported, not removed by tuning gates, replacing the RAS formula, or fitting a forced increasing predictor.

## Status and sources
**PER remains unavailable**, while site reconstruction, actual Sanger quantification and grouped relative-signal model evaluation are complete. `results/prediction/S10_flow_molecular_pairs.csv`, `S10_direct_model_results.csv`, `S10_prediction_validation.csv`, `S10_staged_model_results.csv`, `S10_affine_transform_sensitivity.csv`, and `S10_flow_molecular_associations.csv` provide the evidence. L23_11–12 show actual paired relationships and held-out predictions. No plot presents simulated RNA truth or a validated PER.
