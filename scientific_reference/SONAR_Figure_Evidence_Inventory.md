Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# Integrated figure routing

Layer 0–1 figure F04_S7 uses corrected inputs; other original figures remain unchanged. The canonical acquisition IDs in F03 are raw identifiers, not current AC labels.

| figure_id | source_tables | caption |
| --- | --- | --- |
| F01_control_gates | figures/source_tables/event_display_subset.csv | MOCK1 supplies scatter/pulse gates; MOCK2 is a transfer acquisition. Scatter-selected singlets are not verified viable cells. Display subsampling does not affect scores. |
| F02_control_background | figures/source_tables/event_display_subset.csv;results/background_thresholds.csv | Control distributions and provisional positivity thresholds. These Mock-only boundaries do not validate multicolor negative spread. |
| F03_event_retention | results/event_retention.csv | Uniform control-derived rules across all 32 experimental acquisitions; event counts are not biological replicate counts. |
| F04_S7_normalization | results/calibration/S7_reference_response_corrected.csv | Original event means and RAS under team-corrected 75/90 identities; prior 10-to-15 correction retained. n=2 wells/level. Lines are descriptive, not fits. |
| F04_S10_normalization | results/ras_results.csv | Same reporter-selected events for all three metrics. A/B are user-confirmed independent transfection wells (n=2 per condition). S7 source label 10 is analyzed as confirmed 15% AC by DNA mass; lines are not calibration fits. |
| F05_pair_dispersion | results/repeatability.csv | All matched-label pairs are shown; labels mark conditions with higher RAS CV. CV = sample SD (ddof=1) / absolute mean x 100. This is within-experiment independent-transfection-well repeatability (n=2 per condition); independent culture/day replication is not established. |
| F06_blue_dimension | results/ras_results.csv | ORCA-P2A-BFP linkage is user-confirmed. At positive editor doses, R+B+ is an exploratory reporter/editor co-expression population; the multicolor B boundary remains provisional. The 1:0 blue tail is a negative-control diagnostic, not editor co-expression. |
| F07_sensitivity | results/sensitivity.csv;results/ras_results.csv | Predeclared gate, background and threshold perturbations across experimental acquisitions. Boxes describe sensitivity across conditions, not replicate uncertainty. |
| F08_event_count | results/event_count_sensitivity.csv | 100 subsamples at each supported event count. Uncertainty is conditional on one acquisition and shrinks to zero at the full finite sample; it is not biological uncertainty. |
| F09_reference_influence | results/high_expression_influence.csv;results/red_profiles.csv | Bright events remain in the primary score. Red-bin dependence limits any assumption of perfect reporter-expression invariance. |
| F10_blue_common_support | results/blue_profiles.csv | Common B+ range is the intersection of within-acquisition 5th–95th percentiles for positive editor-ratio labels. Low-count bins remain unavailable; profiles do not establish active-editor abundance. |
| F11_molecular_audit | inventory/molecular_reads.csv | 48 AB1 reads / 24 molecular labels / 12 user-confirmed S10 parent wells. Labels 1/2 map to A and 3/4 to B; RNA was extracted after flow. General-design alignment is an identity lead, not exact OpenA or quantitative RNA-editing validation. |
| F12_plate_reference_signal | results/plate_summary.csv | Single-point red fluorescence includes negative values. Spatial points are technical positions within a well. No validated plate RAS or flow-to-plate conversion is produced. |

For corrected calibration and molecular figures see [current Layer 2–3 figure inventory](SONAR_Layer23_Figure_Evidence_Inventory.md).
