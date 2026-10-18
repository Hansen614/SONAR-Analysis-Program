# Start here — SONAR scientific release and Codex handoff
Release `sonar-science-v1.0-s7s10`. The package includes the complete S7/S10 data and executable analytical foundation. It does not include a graphical application.

1. Read `reports/SONAR_Integrated_Evidence_Report.md` and `science/SONAR_Scientific_Freeze.md`.
2. Use `documentation/REPRODUCTION_GUIDE.md` to run verification, a real FCS-to-RES example, and a full raw-data rebuild.
3. Read `CODEX_IMPLEMENTATION_PROMPT.md`. It is the complete English prompt to copy into a new Codex conversation together with this ZIP.
4. Treat `models/res_primary/model.json`, `models/context_profiles/context_v1.json`, `results/layer0`–`results/layer3`, and `tests/golden_reference/` as the frozen current scientific contract.

The old root reports, `results/calibration`, `results/prediction`, and `baselines/` preserve historical v4/v3 evidence. Their old names/statuses do not override the current final reports. Original `results/ras_results.csv` has historical label columns: join the corrected `inventory/acquisition_manifest.csv` by acquisition ID, or use `results/layer1/RAS_Results.csv`. Do not infer current conditions from filenames.

Current command entry point: `science.py`. Root `reproduce.py` is retained historical v4 source, not the final-release entry point. All required inputs are under `inputs/` and `reference/`; any original absolute paths in provenance are historical annotations, never required runtime files.

Internal authorized research handoff. Public redistribution permissions are not established. Read `documentation/DATA_SHARING.md` before public release.
