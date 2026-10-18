# Layer 3 — Molecular evaluation and PER status
Release: `sonar-science-v1.0-s7s10`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.

Relative molecular analysis is available and informative. Absolute RNA fraction and PER remain unavailable.

## Preserved primary evidence
The provisional 523 bp OpenA amplicon is reconstructed independently from four no-editor F/R pairs in two transfection wells. All four assemblies agree and match the supplied candidate. There are 494 Q20-supported bases, including 393 bidirectional and 101 unidirectional positions; 29 terminal positions depend on primers. The generic 544 bp design differs by multiple substitutions and indels (not one 21 bp deletion). Candidate C280 is a C→T chromatogram event corresponding to RNA C→U; transferred coding context is CGA→TGA in the switch linker. Its intended target identity remains unconfirmed independently of this reconstruction.

All 48 original AB1 traces were byte-checked for base calls, qualities, peak locations and dye-channel order. 47 are eligible at C280. `1-8-2.F` fails local flank identity (0.60 versus required 0.90), so it is retained as evidence but excluded from the site point estimate. There are 23 complete technical F/R pairs, 24 labels and 12 independent transfection wells; sequencing labels 1/2 map to flow A and 3/4 to B. RNA was extracted after flow at the same experimental timepoint; its exact selected cell population and elapsed interval are unresolved. No documented DNase/no-RT controls or known-fraction response standards qualify absolute RNA fractions.

No-editor directional raw ratios average 0.044926 (F) and 0.015840 (R); high-editor values average 0.163541 and 0.287447. Dose-level background-corrected mean index rises from 0 to 0.201744. The no-editor corrected mean is zero by construction, not evidence of no editing. Direction bias persists (raw R−F mean 0.03656, direction RMSE 0.06773); correlation does not establish agreement. Read, technical-label and well summaries remain distinct. The one complete pair in 8A has no estimable within-well technical SE.

## Predictive comparisons and dose confounding
The target for prediction is the raw direction-averaged C280 chromatogram composition index, with no held-out-control subtraction used to define the training endpoint. All 120 predictions from the five original full-cohort models reproduce exactly within tolerance. Existing positive-dose/co-expression models remain in historical tables (10 wells, five doses). The new table adds predeclared linear dose and linear dose plus BFP fraction benchmarks to the existing log-dose model; no nonlinear family search was performed.

| model | well_n | dose_condition_n | MAE | RMSE | bias | outside_predictor_range_n |
| --- | --- | --- | --- | --- | --- | --- |
| B_detection_fraction | 12 | 6 | 0.0168159 | 0.0192193 | -0.00304983 | 4 |
| editor_dose_linear | 12 | 6 | 0.0144618 | 0.0198838 | 0.00312982 | 4 |
| editor_dose_linear_plus_B | 12 | 6 | 0.0134474 | 0.0177949 | -0.00405234 | 4 |
| editor_dose_log1p | 12 | 6 | 0.0297965 | 0.0343251 | -0.00645142 | 4 |
| reporter_RAS | 12 | 6 | 0.0797605 | 0.0901549 | 0.00418496 | 2 |
| reporter_RAS_plus_B | 12 | 6 | 0.0175069 | 0.0198141 | -0.00175237 | 5 |
| training_mean | 12 | 6 | 0.0715229 | 0.0837966 | -4.62593e-18 | 0 |

BFP fraction RMSE 0.019219 is close to the linear editor-dose-only RMSE 0.019884. Adding BFP to linear dose yields 0.017795, a modest internal reduction that cannot establish an independent biological contribution in 12 wells. BFP fraction correlates with dose at r=0.9833. Within-dose A−B differences give r=0.3450 across only six independent pairs; this limited support does not separate measurement error, transfection variability and causal editor abundance. RAS alone (RMSE 0.090155) is worse than the mean-only baseline (0.083797). BFP's strong overall association must not be described as proven information beyond dose.

Leave-one-well-out and leave-one-dose-out are exported separately. Prediction errors are in index units, not editing percentage points. OLS t intervals are model-assumption prediction intervals; empirical coverage and predictor-range extrapolation counts are reported. The new error uncertainty resamples six dose clusters of fixed held-out errors and is descriptive, not a new independent validation. Marginal predictor-range flags do not certify multivariate convex-hull support. No external batch or unobserved experimental context was validated.

## RES–molecular and PER decision
S10 is not qualified for the S7 reference model, and its RNA population cannot be assumed R+B+. Therefore no empirical hinge-RES-to-molecular staged fit is claimed. A deterministic invertible transformation does not create new sample-level information; it can change the functional form allowed to a downstream regression. Existing affine direct-versus-staged predictions agree to 3.47×10⁻¹⁶ as an algebraic sensitivity only. RES's demonstrated use is reference interpretation, not improved S10 RNA prediction.

The interface retains `E_RNA = h(RES)` and `PER = 100 h(RES)%` but returns PER=null. Separate flags identify molecular data availability, candidate signal, relative index, relative-model fitting/internal evaluation, absolute assay qualification and domain validation. No relative index is placed in a percent-edited-RNA field. Version 1 deliberately has no adapter that can authorize a new absolute model merely from a caller-supplied boolean.

Sources: [molecular data](../results/molecular/S10_well_level_molecular_results.csv), [reconstruction](OpenA_Amplicon_Reconstruction.md), [new comparisons](../results/layer3/Molecular_Prediction_Comparison.csv), [all held-out predictions](../results/layer3/Molecular_Prediction_Validation.csv), [dose adjustment](../results/layer3/Dose_Confounding_Assessment.json), [original co-expression comparisons](../results/prediction/S10_direct_model_results.csv).
