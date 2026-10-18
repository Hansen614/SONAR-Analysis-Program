# Frozen primary RES model
Model ID: `sonar-science-v1.0-s7s10::S7-hinge-k050`. Estimator: `ratio_of_paired_linear_sums-v2`. Context: `SONAR-CytoFLEXS-22cac3269aa6-v1`. Calibration identity: `S7_AC_DNA_mass_team_corrected_20261013`.

```
g(A) = 0.500091476458275 + 0.491368713316119 A + 0.366037234211599 max(0, A - 0.5)
```

A is AC DNA mass fraction (0–1). Equivalently use `alpha + lower_slope*min(A,0.5) + upper_slope*max(A-0.5,0)`, with lower slope 0.491368713316119 and upper slope 0.857405947527719. Coefficients in JSON use this latter basis. The knot is fixed at 0.5 as in v4, never searched against the held-out errors. Both slopes are constrained nonnegative; the intercept is unconstrained. Equal weight per independent reference well, bounded least squares, 20 wells and ten corrected levels.

For RAS y within [0.500091476458275, 1.17447880688019], invert `(y-alpha)/lower_slope` below g(0.5)=0.745775833116335, otherwise `0.5+(y-g(0.5))/upper_slope`. General piecewise inversion returns an identified interval for flat segments. Outside-domain inputs return null, without clipping or extrapolation. RAS and RES are dimensionless but describe different axes. Display RES as “RES — AC Reference-Equivalent Score”, with DNA mass-equivalent units and status; never as RNA editing percentage.

`models/res_primary/model.json` is authoritative. `uncertainty.json` stores all 1,000 bootstrap coefficient draws, synchronized observation draw IDs and values, and 1,001-point curve bands. `calculate_res` reads these artifacts; routine application use does not refit. Model/context/core/config/reference hashes detect invalidated dependencies. Refit and new-context use require new identities and scientific review; the supplied fitting function is research-only.

Two uncertainty outputs are deliberately separate. Conditional 2.5/97.5% inverse bootstrap quantiles account for reference-well resampling, paired event noise, and shared controls, conditional on valid inversion. Their success denominator is reported. The broader compatibility set inverts the bootstrap mean-curve band expanded by the 95th percentile absolute leave-level-out RAS residual and the sample RAS interval margin. This is a reproducible diagnostic set, not a calibrated 95% CI or guaranteed ±10 percentage-point accuracy. Grid edges are rounded to 0.001 mass fraction and do not imply assay precision.

Internal range policy also requires compatibility with the isotonic benchmark: largest contiguous response region whose union of primary and isotonic sets is interior, ≤0.20 total mass-fraction width, and has unique point inverses. Sample measurement uncertainty is additionally checked. No rule uses S10 ranking or desired editing predictions.
