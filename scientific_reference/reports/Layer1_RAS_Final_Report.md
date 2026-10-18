# Layer 1 — Final RAS
Release: `sonar-science-v1.0-s7s10`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.

RAS remains the ratio of paired, signed, background-corrected linear sums: `RAS_P = sum(g_i) / sum(r_i)`. The original core and all original RAS values are unchanged. mCherry is a continuous reference, not merely a positivity marker.

`P_R = singlets ∩ R_q+`; `P_RB = P_R ∩ B+` applies only with confirmed linked-editor presence. All 32 reporter-population scores and the 10 positive-dose S10 co-expression scores are available. The two no-editor BFP tails remain in historical diagnostics but are explicitly NOT_APPLICABLE for the co-expression result contract. BFP positivity indicates detectable editor-associated expression, not active ORCA abundance or editing.

## Normalization evidence
CV = sample SD (ddof=1) / absolute mean × 100, calculated across two independent transfection wells per condition. Raw EGFP means and RAS use the same selected reporter events. There are ten matched S7 and six S10 conditions.

| series | conditions | raw_CV_median | RAS_CV_median | improved_conditions |
| --- | --- | --- | --- | --- |
| S10 | 6 | 6.71093 | 5.14238 | 5 |
| S7 | 10 | 4.69699 | 1.76734 | 8 |

Thus median CV declines from 4.697% to 1.767% in S7 (62.37% relative reduction of medians), and from 6.711% to 5.142% in S10 (23.37%). These are descriptive medians over heterogeneous conditions, not confidence intervals or proof of molecular accuracy. Normalization does not improve these conditions:

| series | condition_label | raw_EGFP_CV_percent | RAS_CV_percent |
| --- | --- | --- | --- |
| S10 | 0.5 | 1.0109 | 1.92482 |
| S7 | 40 | 0.351555 | 1.57245 |
| S7 | 100 | 0.116359 | 1.81188 |

## Expression dependence and effective support
All 32 wells show lower RAS in the highest common red bin than in the lowest common red bin; differences range from -0.262 to -0.042 RAS. These within-sample bin summaries demonstrate expression dependence; normalization does not remove it. The common-bin analysis does not cover the entire red tail.

Effective red-weighted support `N_eff,R = sum(r)^2 / sum(r^2)` is 1225–4553 per reporter sample, only 5.87%–16.42% of selected events. It measures concentration of red weights, never biological replicate count. Reporter-positive fractions range 22.07%–48.45%; the corrected mCherry distributions and quantiles are exported per sample.

The top 1% of red-expressing events carry 16.78%–30.78% of red signal. Their diagnostic removal shifts RAS by -1.18% to 6.29%. Moving the corrected red-threshold excess to 0.8/1.2/1.5 times primary changes RAS by -0.173% to 0.123%. These support numerical stability near the lower boundary, but do not remove expression-distribution dependence or validate a detector upper limit.

## Statistical uncertainty
The retained 2,000 paired-event bootstrap draws preserve green/red covariance. One shared bivariate control-noise draw per ID is applied jointly to all samples. Event-only and event-plus-control intervals are stored separately. Gate/background/threshold alternatives are sensitivity analyses, not silently pooled into a nominal CI. Between-well SD/CV is based on two wells; between-condition differences are separate experimental contrasts. No interval estimates between-day, culture or laboratory reproducibility. The final wrapper reproduces original sums and RAS and imports the verified original uncertainty records; new-sample bootstrap is an explicit optional API operation.

## BFP contribution
Mean BFP-positive fraction among reporter-selected S10 events rises from 1.22% at no editor to 40.21% at 800 ng editor. Thresholds are optically provisional. Common-BFP bins yield 26/40 estimable bins and 14/40 unavailable bins, so this conditional analysis is exploratory. Do not confuse BFP intensity, BFP-positive fraction, editor DNA dose, reporter RAS and R+B+ RAS.

The reporting contract includes sample, well and condition, population, context, estimator, input hash, selected N, effective N, signed green/red sums, RAS, distinct uncertainty fields, QC and interpretation. Suitable use is same-context reporter measurement and compatible reference calibration. It does not establish expression-independent molecular editing truth.

Sources: [normalization pairs](../results/layer1/Normalization_Repeatability.csv), [RAS contract](../results/layer1/RAS_Results.csv), [red dependence](../results/layer1/Reporter_Expression_Dependence.csv), [red bins](../results/red_profiles.csv), [threshold sensitivity](../results/layer1/Red_Threshold_Sensitivity.csv), [tail influence](../results/high_expression_influence.csv), [BFP profiles](../results/blue_profiles.csv).
