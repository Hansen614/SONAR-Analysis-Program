# RAS mathematical definition
Estimator identity: `ratio_of_paired_linear_sums-v2`; implementation `src/core.py::score`.

For selected paired events, g_i=raw_G_i-background_G and r_i=raw_R_i-background_R. RAS=sum(g_i)/sum(r_i). Do not average per-cell g/r, log-transform sums, rectify negative green, add pseudocounts, remove bright cells for primary output, or tune gates to increase calibration fit.

Event count must be at least100, corrected red sum positive, and relative SE of mean corrected red at most0.10. Invalid/insufficient results are null, not zero. Event delta SE uses paired residuals g_i−RAS*r_i; effective red support is sum(r)^2/sum(r²). Shared-control and paired-event bootstrap uncertainty, gate/background sensitivities, between-well SD and condition differences are distinct.

See `reports/Layer1_RAS_Final_Report.md` and `models/context_profiles/context_v1.json` for actual populations and uncertainty. The final API hides no-editor BFP tails from co-expression outputs but preserves them in historical diagnostic tables.
