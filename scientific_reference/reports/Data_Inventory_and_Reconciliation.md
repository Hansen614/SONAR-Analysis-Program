> Historical v2 record, preserved for provenance. Superseded by the actual v3 analyses in `Layer2_RES_Calibration.md`, `Layer3_PER_Calibration.md` and the root Layer23 evidence report. HEK293T is now user-confirmed; OpenA reconstruction and exploratory fitting have been completed.

Analysis version: `sonar-fresh-s7-s10-20261012-v2`. Review date: 2026-10-13. Authorized experimental series: S7 and S10 only. All numerical results below were regenerated from copied original inputs.

## Input accounting and independence
The full file manifest lists original paths, copied paths, sizes and SHA-256 hashes. `acquisition_file_manifest.csv` has one row for each of the 36 FCS files; `acquisition_manifest.csv` has one row for each of the 34 unique acquisitions. File hashes, DATA-segment hashes and instrument tube UUIDs are retained to audit duplicate copies versus acquisitions. Two shared Mocks are deduplicated. There are 32 user-confirmed independent transfection wells, two per condition; independent culture or batch replication is not established. No non-identical FCS re-export of the same event data was identified. Generated well IDs identify the confirmed experimental units but are not physical plate coordinates. Culture IDs and the molecular preparation subtype remain unknown.

## Reconciliation decisions
| Issue | Observed evidence | Decision |
| --- | --- | --- |
| Shared Mock files | Identical full-file and event-data hashes in S7/S10 | Count each acquisition once |
| Midnight crossing | FCS dates 23/24 September; same optical settings | One contiguous acquisition session; no independent-day claim |
| A/B identity | User confirms two independent transfection wells per condition | Within-experiment well repeatability, n=2; no independent-culture/day claim |
| S7 10/15 | User confirms handwritten 15 correction | Retain source IDs/label 10; analyze at 15% AC mass fraction |
| S7 AC/INAC | User confirms mass-based mixing | AC mass-fraction axis; not molar or RNA fraction; exact states remain unverified |
| S10 DNA | User confirms reporter 100 ng and total DNA 1,000 ng per well | Editor amounts derived from recorded 1:x ratios: 0, 50, 100, 200, 400, 800 ng |
| BFP | User confirms ORCA–P2A–BFP in S10 | Positive-dose B+ reporter mode is exploratory editor co-expression; optical boundary still provisional |
| Compensation | Identity matrices and USCOMP=False in all FCS files | Preserve native linear values; no invented spillover estimate |
| Matched optical controls | Two Mock acquisitions; no single-color panel | Optical-validity warning applies to all scores |
| S10 1:1 B rate anomaly | One-second rate outlier bins | Apply fixed time rule; retain no-time-filter sensitivity |
| Fluorescence above PnR | Tiny area-channel excursions, no repeated-max pileup | Diagnose; do not equate metadata range with proven clipping |
| S9-named sequencing form in S10 | User confirms these molecular samples map to S10 A/B | Series association resolved by user; preserve source filename |
| Flow A/B versus molecular 1–4 | User: 1/2→A, 3/4→B; RNA extracted after flow | 24 labels grouped into 12 wells; exact sampled population and assay still unqualified |
| SEQ versus AB1 | 19 of 48 text exports differ from AB1 calls | Preserve both; AB1 is trace authority |
| General reporter versus OpenA | Generic primer interval 544 bp versus 523 name | Generic design supports architecture only; exact target unresolved |
| Shared S8/S10 plate map | Separate EDIT block identified | Use EDIT values only; exclude S8 experimental values |
| PBS blank | Only A01 explicitly labelled PBS | Do not pool other blank-file wells as known controls |

## Construct-role registry
The general sequence design explicitly annotates mCherry, GSG-P2A, EGFP and ecDHFR-DD. This supports the intended continuous red-reference / green-response architecture at design level. It is not full-clone sequence confirmation for S7 AC, S7 INAC or S10 OpenA. AC/INAC molecular locked states remain unresolved. S10 ORCA–P2A–BFP linkage is user-confirmed but not sequence-verified. No construct length from the generic plasmid is substituted for missing AC/INAC plasmid lengths.

## Unknown fields
Unresolved fields are S7 absolute DNA amounts, culture identity, cell type, treatment/TMP conditions, exact flow-to-RNA elapsed interval, RNA population selection, viability, exact construct sequences, physical plate coordinates, independent culture/day replication and molecular assay controls. S10 absolute doses, S7 mass basis/corrected percentage, transfection-well independence, and flow/RNA label grouping are resolved from user confirmation. The inventory is complete in its accounting of supplied materials; the experimental history is not fully resolved. See `record_transcription.md` and each source workbook/photo for the evidence boundary.
