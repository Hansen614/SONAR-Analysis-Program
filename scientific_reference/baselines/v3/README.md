# SONAR S7/S10 integrated analysis — v3

Start with [中文科学摘要](SONAR_Layer23_Scientific_Summary_ZH.md), [English scientific evidence](SONAR_Layer23_Evidence_Report.md), and [integrated four-layer report](SONAR_Measurement_Evidence_Report.md).

Release `sonar-s7-s10-layer23-20261013-v3` extends the existing project. The upstream Layer 0–1 version stays `sonar-fresh-s7-s10-20261012-v2` with identical RAS bytes, estimator, gates and background. The prior complete release and verification records are preserved under `baselines/v2/`; no other experimental series was added. User-confirmed HEK293T metadata is applied to experimental sample manifests.

The extension contains independently reconstructed OpenA523 reference/alignment evidence; 48-read Sanger processing and 12-well relative molecular results; three fitted S7 mass-calibration models, internal validation and explicit inverse sets; and grouped S10 relative-index prediction models. Validated RES and RNA-editing PER remain unavailable. Model and assay qualification are explicit in every relevant table/report.

## Main outputs
- `results/molecular/`: consensus FASTA/annotated GenBank/alignment, per-base support, read metrics, 24-label and 12-well summaries, source audit.
- `results/calibration/`: fits, residuals, grouped recovery, bootstrap uncertainty, inverses, anomaly and S7/S10 compatibility.
- `results/prediction/`: paired wells, actual exploratory models and held-out predictions, explicit unavailable staged biological model.
- `models/layer23/`, `config/layer23.json`: serialized model coefficients/thresholds and frozen choices; upstream hashes prevent silent incompatibility.
- `figures/layer23/`: 12 new data-driven diagnostics in PNG/SVG with source hashes. Existing 13 Layer 0–1 diagnostics remain.
- `reports/`: detailed scientific methods and executed tests/reproduction records. `SONAR_Layer23_Blocker_Resolution.md` documents actual resolution attempts.
- `reference/layer23/`: supplied request, provisional files and permitted generic construct records, preserved as sources.
- `baselines/v2/`: preserved prior release and exact-output baseline verification. `_work/` is disposable working material.

## Reproduce
Use Python 3.13 with the pinned packages in `requirements.txt`:

```text
python reproduce.py --verify
```

The complete command regenerates Layers 0–3, runs the scientific tests, performs an isolated second run, and compares all nested numerical result tables, event masks, model JSON and PNG pixels. For only the extension after a verified unchanged upstream run: `python reproduce.py --layer23-only`. On this host the prepared interpreter is `_work/venv/bin/python`. No internet or external project paths are needed after installation; packaged input hashes are verified. The current run's actual checks appear in `reports/reproducibility_record.json` and `reports/test_results.txt`.

All peak fractions are chromatogram metrics until separately qualified; AC DNA mass fractions are reference inputs, not RNA edits. No final Wiki page, publication figure or synthetic validation dataset is included.
