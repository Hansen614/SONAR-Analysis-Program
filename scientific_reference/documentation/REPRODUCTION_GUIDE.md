# Reproduce the scientific release
Extract the ZIP, enter its single top-level directory, and run all commands from there. No previous v4 ZIP or original Desktop files are required. Raw data and all scientific configuration are inside this package. Original absolute provenance strings are not required runtime paths.

## Environment
Tested: Python 3.13.7, macOS arm64, exact versions in `environment/requirements.lock.txt`. For a new environment:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r environment/requirements.lock.txt
```

The release was executed using these installed versions. Dependency download/installation itself was not re-tested in a new network-isolated environment. Other operating systems are untested; numerical tolerance is rtol=atol=1e-12 under the recorded environment. The raw-data analysis is offline once dependencies are installed. No GUI/service/account is required.

## Tested execution commands
Use your chosen Python interpreter (`python` below) with the pinned dependencies.

```sh
python science.py verify
python science.py example --sample S7_90B --output _work/example.json
python science.py example --sample S7_5B --output _work/weak_example.json
python science.py example --sample S7_100A --output _work/boundary_example.json
python science.py example --sample S10_1_8_A --output _work/S10_transfer_restricted.json
python science.py reproduce
```

`verify` checks packaged raw/references, frozen model dependency hashes, and unit/integration/golden tests. `example` decodes a real raw FCS, uses the stored context, computes signed RAS, loads the frozen inverse and writes a complete JSON report. Registered uncertainty records are used only with the matching raw sample/RAS. `--mode routine` keeps a separately named research value but leaves ordinary/routine RES null.

`reproduce` creates `_work/raw_rebuild/`, copies packaged inputs, and rebuilds the original complete flow pipeline including 2,000-draw bootstrap from raw FCS. It rebuilds provisional amplicon and 48 AB1 metrics, original molecular predictions, corrected S7 references, and all final scientific tables/models. Historical pre-correction metadata is used only to reproduce immutable RAS bytes; the documented correction is then reapplied by acquisition ID. It compares 32 sample reports, 204 mask arrays, molecular tables, final tables and model JSON against frozen outputs. Results and detailed stage logs go to `_work/`. It may take several minutes and needs roughly 1 GB spare disk space; it never edits raw inputs or replaces frozen results.

Explicit release-maintenance command `python science.py finalize` regenerates final science artifacts and final reports. This is a scientific refit/audit command, not the future application's routine path. Its model is pinned to existing v4 outputs and all new parameter comparisons must pass. Do not run historical root`reproduce.py` as the final release command.

Results expected: all tests PASS, golden RAS and RES within 1e-12, raw RAS bytes identical, final numeric max difference 0 in the tested run, masks equal, no S10 ordinary RES and no PER. `provenance/` records the actual release and clean-extraction checks. `_work/` can be discarded after inspection and is never packaged as a runtime dependency.
