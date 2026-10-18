Analysis version: `sonar-fresh-s7-s10-20261012-v2`. Review date: 2026-10-13. Authorized experimental series: S7 and S10 only. All numerical results below were regenerated from copied original inputs.

## Scientific question
Can one declared measurement context support consistent processing of the supplied flow acquisitions?

## Implemented method and experimental evidence
There are 36 FCS files, 34 unique event acquisitions and 3,400,000 unique events. S7 contributes 20 experimental acquisitions; S10 contributes 12; two Mock acquisitions are shared byte-identical files across directories. They are counted once. No additional biological replicates are inferred. All files have 100,000 events and the same CytoFLEX S serial AS52073 optical profile, with GFP/PB450/mCherry gains 50/1/400. Acquisition crossed midnight on 2026-09-23/24; this is one contiguous session, not independent day replication.

FlowIO 1.4.0 reads native FCS3.0 list-mode 32-bit little-endian floating-point data. Area channels FL1-A, FL6-A and FL11-A map through FCS descriptions to GFP-A, PB450-A and mCherry-A. PnE=0,0 and PnG=1 for all parameters. Preprocessing changes only Time by TIMESTEP=0.00002 seconds per unit. An independent NumPy byte decoder agrees exactly on every event in all 36 file copies. Hardware gain is not divided out; these remain instrument-specific a.u. The identity matrix is verified and preserved as a no-op, without claiming optical compensation has been validated. Original data, linear values and display-transformed coordinates are distinct. Display data are sampled only for plots.

MOCK1 alone trains a robust MCD ellipse on log10(FSC-A, SSC-A), using support fraction 0.8 and a fixed random subset of 8,000 events. The accepted squared distance is chi-square(2) 0.99 = 9.21034. This is a transparent geometric choice, not a statistical proof that 99% of cells are retained. The singlet gate uses log10(FSC-A/FSC-H) within three normalized MADs of the MOCK1 center. Exact fitted values are in `contexts/context.json`. MOCK2 tests transfer of that geometry. The bright response groups never choose the gates. No viability dye is present; populations are described as scatter-selected, singlet-like events.

Per acquisition, finite positive scatter and finite nonnegative time are required. Complete one-second bins are flagged if their rate differs from the median by more than six times max(normalized MAD, sqrt(median rate), 0.1 x median rate). The last partial bin is not rate-tested. Time reversals are flagged. Only rate-outlier bins are removed. This cannot diagnose all clogs or population drift; time-bin scatter and fluorescence summaries remain auditable.

## Actual results
The Mock singlet retentions are 78.424% and 78.543%. Experimental singlet retention spans 66.48–77.08%. The rate rule removes 4,320 events from `S10_1_1_B`; other acquisitions retain all events at that step. No time reversals or malformed/nonfinite events are observed.

| control_id | channel | mean_linear | sd_linear | quantile_995 | used_background | used_threshold |
| --- | --- | --- | --- | --- | --- | --- |
| S7_MOCK1 | EGFP | 2929.9 | 1417.9 | 9101.2 | 2999.9 | 9295 |
| S7_MOCK1 | mCherry | 1165.6 | 644.78 | 3395.7 | 1149.5 | 3395.7 |
| S7_MOCK1 | BFP | 200.82 | 299.22 | 985.89 | 196.5 | 985.89 |
| S7_MOCK2 | EGFP | 3069.9 | 1474.2 | 9295 | 2999.9 | 9295 |
| S7_MOCK2 | mCherry | 1133.4 | 674.77 | 3236.3 | 1149.5 | 3395.7 |
| S7_MOCK2 | BFP | 192.18 | 298.15 | 974.59 | 196.5 | 985.89 |

Background subtraction uses the equally weighted arithmetic means of the two control acquisitions in linear units. Positivity uses the larger of the two within-control 99.5th percentiles. These are separate operations. The candidate red quantification boundary is max(red positivity threshold, mean background + 3 background SD); here it equals 3395.724 a.u. This is a provisional screen, not a measured limit of quantification.

| training_control | test_control | channel | test_positive_fraction |
| --- | --- | --- | --- |
| S7_MOCK1 | S7_MOCK2 | EGFP | 0.0054492 |
| S7_MOCK1 | S7_MOCK2 | mCherry | 0.0042397 |
| S7_MOCK1 | S7_MOCK2 | BFP | 0.0043925 |
| S7_MOCK2 | S7_MOCK1 | EGFP | 0.0046159 |
| S7_MOCK2 | S7_MOCK1 | mCherry | 0.0060186 |
| S7_MOCK2 | S7_MOCK1 | BFP | 0.0055723 |

The cross-control positivity rates span 0.424–0.602%. Each transfer calculation derives a threshold from the other acquisition. The final maximum-of-two threshold uses both controls and therefore has no third held-out negative validation sample. Differences in mean EGFP background are about 4.7% relative to their equal-weight mean. This is small control drift in this session, not between-day reproducibility.

Native fluorescence ranges and maxima are exported for every channel. Area values occasionally exceed PnR (maximum observed fractions: EGFP 0.004%, red 0.005%); no repeated-maximum pileup is observed in fluorescence area channels (each maximum occurs once). PnR is not independently established as the analog clipping boundary, so these excursions are flagged rather than deleting bright cells or declaring saturation absent. No optical standard or absolute molecule-unit conversion is documented.

## Interpretation and limits
All fluorescence scores in this release are **exploratory detector-scale RAS**. The stored compensation matrix is identity and `USCOMP=False`; no matched single-color controls establish negligible spillover. Mock-derived boundaries have only acquisition-level negative-transfer checks. User metadata confirms independent A/B transfection wells, S7 AC mass fractions (source label 10 means 15%), S10 doses and ORCA–P2A–BFP linkage, and molecular labels 1/2→A and 3/4→B with RNA extracted after flow at the same experimental time point. Exact AC/INAC states, sequence-level construct identity, sampled RNA population and molecular assay qualification remain unresolved. These restrictions are separate from successful numerical computation. Validated RAS, RES and PER fields remain unavailable; unavailable never means zero.

The data support computationally reproducible, consistent geometry and approximate negative-background transfer within the recorded session. They do not establish viable-cell specificity, multicolor optical validity, an empirical red LOQ, independent control-well repeatability or cross-instrument transfer.

## Source tables and figure opportunities
`inventory/acquisition_manifest.csv`, `inventory/channel_metadata.csv`, `inventory/reader_crosscheck.csv`, `results/event_retention.csv`, `results/background_thresholds.csv`, `results/negative_transfer.csv`, `results/time_qc.csv`, and `masks/*.npz`. Diagnostics F01–F03 show control gates, background and retention. F07 shows perturbation sensitivity. Source-table links and captions are in `figures/figure_index.csv`.
