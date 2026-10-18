> Historical v2 record, preserved for provenance. Superseded by the actual v3 analyses in `Layer2_RES_Calibration.md`, `Layer3_PER_Calibration.md` and the root Layer23 evidence report. HEK293T is now user-confirmed; OpenA reconstruction and exploratory fitting have been completed.

Analysis version: `sonar-fresh-s7-s10-20261012-v2`. Review date: 2026-10-13. Authorized experimental series: S7 and S10 only. All numerical results below were regenerated from copied original inputs.

## Scientific question
Does the S7 active/inactive reference response admit a reliable inverse mapping from RAS to reference-equivalent input (RES)?

## Reference verification and implemented analysis
FCS tube metadata preserves the 20 S7 source labels. The user confirms the handwritten 10-to-15 correction and a mass-based AC/INAC mixture. The analysis axis is now **AC DNA mass fraction (%)**: 0, 5, 15, 20, 30, 40, 50, 75, 90 and 100. Source filenames and acquisition IDs such as S7_10A remain unchanged; `source_condition_label=10` and `condition_label=15` preserve the reconciliation. These are input DNA mass fractions, not measured intracellular RNA fractions or molar fractions. Exact AC/INAC sequence states, locked-state integrity, plasmid lengths, total reporter loading, per-well amounts and preparation uncertainty remain unresolved.

The implemented characterization uses the independently regenerated reporter-population RAS values, retaining A and B separately. It computes equal-acquisition condition means, sample SD, adjacent differences and descriptive rank association. No calibration model is selected or fitted; no inverse is exported. S7 observations are not reused as a held-out validation set.

## Actual response
| condition_label | ras_mean | ras_sd | acquisition_n |
| --- | --- | --- | --- |
| 0 | 0.53369 | 0.023324 | 2 |
| 5 | 0.51263 | 0.006303 | 2 |
| 15 | 0.56103 | 0.028405 | 2 |
| 20 | 0.56095 | 0.009664 | 2 |
| 30 | 0.67859 | 0.00046491 | 2 |
| 40 | 0.67754 | 0.010654 | 2 |
| 50 | 0.7444 | 0.017944 | 2 |
| 75 | 1.1322 | 0.0057949 | 2 |
| 90 | 0.97872 | 0.031766 | 2 |
| 100 | 1.1304 | 0.020481 | 2 |

Endpoint means rise from 0.533694 at label 0 to 1.130373 at 100: a 2.118-fold difference. This establishes a detector-scale reference response under the selected context. The low endpoint is not zero; it cannot be interpreted as a zero-edited-RNA measurement. The label-5 mean (0.512628) is below label 0. The 75 mean (1.132248) exceeds the 90 mean (0.978722); the 75 and 100 means differ by only 0.001875. Small reversals also occur around 15/20 and 30/40. A strong overall rank association does not establish an identifiable local inverse.

## Identifiability and compatibility
The empirical means are not one-to-one and low-end changes are not consistently resolved relative to A/B dispersion. Unverified reference states, preparation uncertainty and lack of independent calibration validation prevent RES qualification even though mass fractions and A/B well identity are now confirmed. A high-order or forced monotonic fit would hide this evidence. The appropriate output is `NOT_CALIBRATED`, with empirical response tables retained. No RES is assigned to S7 or S10.

S7 reporter-population references are not a validated bridge to blue-selected S10 populations. The exact reporter and treatment compatibility and editor/BFP influence on reference integrity are unresolved. A shared detector profile alone is insufficient.

## Required evidence before RES
Verify full AC/INAC sequences and locked responses, final preparation amounts and mixing process, lengths and explicitly defined input fractions. Demonstrate compatible context and population mode, or validate a bridge. Extend the current two-well-per-condition response to additional independently prepared wells and sessions, with emphasis on low-end discrimination and the 75/90/100 anomaly. Use independently prepared blinded mixtures to evaluate bias, precision, local inverse uncertainty and recovery; declare the accepted domain before reporting RES. Separately test whether the DNA-mixture surrogate transfers to genuinely edited reporters. None of these future checks is claimed completed.

## Sources and figure opportunities
`inventory/record_transcription.md`, `inputs/S7/IMG_1694.HEIC`, `results/ras_results.csv`, `response_summary.csv`, `adjacent_response.csv`, and `associations.csv`. F04_S7 can show the real ladder with every acquisition; it must not be labelled a validated calibration curve.
