# SONAR — RNA Editing Reporter Measurement Toolkit
Scientific reference release `sonar-science-v1.0-s7s10`. Start at [START_HERE.md](START_HERE.md).

SONAR separates Context Calibration, RAS fluorescence quantification, reference-equivalent RES calibration, and molecular/PER qualification. The fixed 50% monotone hinge is an operational research calibration for corrected S7 AC DNA mass mixtures. All 20 S7 samples have point inverses with uncertainty/status; no validated S10 transfer or absolute PER is emitted.

```sh
python science.py verify
python science.py example --sample S7_90B --output _work/example.json
python science.py reproduce
```

Use Python 3.13 and the exact dependencies in `environment/requirements.lock.txt`; see [reproduction guide](documentation/REPRODUCTION_GUIDE.md) for setup and tested scope. Normal model use loads JSON artifacts; the explicit `finalize`/`reproduce` science-maintenance paths may refit only for audit. No notebook, service, GUI or external data path is required.

The raw input directory layout from v4 is preserved to keep hashes and relative paths stable rather than duplicate it under a new `data/raw/` tree. `inventory/` holds metadata; `reference/` holds construct evidence and user instructions; `models/` holds portable contracts; `src/` contains original kernels and thin final interfaces; `science/` and final `reports/` provide evidence; `results/layer*/` and `results/integrated/` are current outputs; `tests/` includes legacy, edge and real-data golden tests.

The complete [Codex prompt](CODEX_IMPLEMENTATION_PROMPT.md) defines the next application's scope. No final Wiki narrative or publication figure design is included.
