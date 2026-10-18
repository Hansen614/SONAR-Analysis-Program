# Layer 0 — Final Context Calibration
Release: `sonar-science-v1.0-s7s10`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.

The context is computationally reproducible and supports exploratory detector-scale measurement. It is not a validated multicolor optical standard.

## Implemented measurement
34 unique acquisitions comprise 32 experimental wells and two Mock acquisitions; duplicated Mock files in S10 are not independent controls. Original FCS bytes decode as 12-channel little-endian floating point. FlowIO's raw arrays were independently checked against bytes; only the Time channel receives its stored time-step conversion. The channel order is fixed: EGFP = FL1-A, index 5; BFP = FL6-A, index 7; mCherry = FL11-A, index 9. Unit gains and linear PnE fields are required. Display transforms never enter fluorescence sums.

Acquisition QC rejects nonfinite/nonpositive scatter and 1-second rate bins beyond six robust scale units. A robust two-dimensional log-scatter ellipse is fit on Mock1 only (MCD support 0.8, at most 8,000 events, seed 20261012, chi-square cutoff 9.21034). Singlets use log10(FSC-A/FSC-H) within three Mock-trained robust SDs. These are morphological selections; no live/dead marker establishes viability.

The background is the equal-weight mean of the two gated Mock acquisition means. Raw positivity uses the maximum of their channel-specific 99.5th percentiles. mCherry quantification requires raw R > 3395.724011230456, equal here to the positivity threshold; this numerical equality does not equate the background and threshold. Additive backgrounds are EGFP 2999.921288652426, mCherry 1149.481510590721 and BFP 196.5028889499891 detector a.u. Signed corrected EGFP is retained. The red boundary is a provisional precision screen, not an empirical LOQ.

## Numerical QC evidence
All 204 saved masks were independently reproduced from the raw FCS and saved configuration by the final wrapper. Negative-acquisition transfer positivity ranges from 0.424% to 0.602%. The largest rate-QC exclusion is 4.32% in one acquisition. A/B remain independent transfection wells within this experiment, not independent cultures or experimental days.

The newly explicit range audit found 70 fluorescence events counted across channels at or above the declared PnR (16,777,216); cross-channel counts can describe the same event. 18 acquisitions are flagged. No fluorescence value is exactly equal to PnR; every observed channel maximum occurs once. Because integrated floating-point area signals can exceed this metadata range and no flat maximum accumulation is observed, these files do not establish physical clipping or absence of saturation. Among reporter-selected populations, 23 distinct events are flagged across 32 wells (0–4/well). Removing them only as a sensitivity analysis changes RAS by -2.760% to 0.114%. Primary values retain these events.

## Optical boundary and interface
The stored spillover matrix is identity and USCOMP is False. No matched single-color/FMO controls or verified compensation provenance were recovered. Experimental EGFP/BFP relationships are never used to infer spillover. No-editor S10 reporter populations show broader BFP tails than Mock; this is a negative-transfer diagnostic, not a new compensation standard. All samples retain `WARN_OPTICAL_UNVALIDATED`; numerical score availability is a separate field.

`models/context_profiles/context_v1.json` contains the instrument fingerprint, cell type, exact channels, control hashes, additive background, positivity and quantification thresholds, fitted gates, support requirements, uncertainty, QC rules and compatibility policy. `process_fcs` enforces the profile and returns counts plus range warnings. `build_context` rebuilds this profile from packaged controls. Missing/mismatched channels are rejected explicitly; a different panel requires its own context implementation. The final profile's unvalidated upper range is JSON null.

Sources: [sample QC](../results/layer0/Sample_QC.csv), [channel range audit](../results/layer0/Detector_Range_Audit.csv), [range sensitivity](../results/layer0/Range_Exclusion_Sensitivity.csv), [raw regression](../results/layer0/raw_flow_regression.json), [negative transfer](../results/negative_transfer.csv), [API](../documentation/API_CONTRACT.md).
