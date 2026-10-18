# QC, numerical availability and interpretation
| Field/status | Meaning | Handling |
| --- | --- | --- |
| qc_state=WARN_OPTICAL_UNVALIDATED | Technical data processed, multicolor optics unqualified | Keep usable RAS and warnings |
| range_warning | At least one recorded fluorescence value ≥declaredPnR | Inspect counts/maximum and sensitivity; not automatic saturation or clipping |
| ESTIMABLE_EXPLORATORY | RAS meets event/denominator support | Display RAS and scientific limits |
| NOT_ESTIMABLE | Failed numerical/support condition | Null RAS; retain counts/reason |
| NOT_APPLICABLE_NO_LINKED_EDITOR | BFP tail lacks editor meaning | Null co-expression; keep reporter output |
| EXPLORATORY_UNIQUE_MODEL_INVERSE | One mathematical inverse exists | Scientific domain independently determines ordinary RES availability |
| NON_IDENTIFIABLE_PLATEAU | Multiple mass inputs share response | Identified interval, no unique point |
| OUT_OF_CALIBRATION_RANGE / UNAVAILABLE_INPUT | Invalid inverse input | Null point, no clipping/extrapolation |
| INTERNAL_EXPLORATORY_SCREEN | Passes reference region plus primary and joint per-sample width checks | Research estimate; never routine validated accuracy |
| PRIMARY_INFORMATIVE_CROSS_MODEL_SET_BROAD | Inside reference screen and primary set narrow, but measurement-expanded joint set exceeds20 pp | Keep research estimate and both uncertainty widths |
| NUMERICALLY_AVAILABLE_WEAK_OR_BOUNDARY_SUPPORT | Inverse exists outside narrow screen or with broad/truncated set | Keep research result with uncertainty |
| OBSERVED_HIGH_END_FLATTENING_PRIMARY_SLOPE_MODEL_DEPENDENT | Near high-end response region | Positive fitted slope does not establish observed resolution |
| CALIBRATION_TRANSFER_NOT_ESTABLISHED | Context/population/reference-domain mismatch | Ordinary RES null; explicit hypothetical field only |
| NOT_QUALIFIED_INTERNAL_CALIBRATION_ONLY | No routine quantitative permission | Routine RES null; retain research output separately |
| PER unavailable reasons | No qualified absolute assay/domain/model | Null PER; retain relative molecular evidence |

Percent display must say AC DNA mass equivalent for RES. Null/CSV blank means unavailable; zero is an actual numeric value only. Conditional bootstrap coverage and success probability are distinct from compatibility-set width and interpretation permission. All eligible/ineligible rows remain in exports.
