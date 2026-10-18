# Stable analytical API v1
All functions are in `src/science_api.py`. From the package root, use `sys.path.insert(0,"src")` before import, or set PYTHONPATH=src. The next application may install/package this module while preserving behavior. Fractions use0–1; display percentages multiply by100 and keep the mass-equivalent label. No GUI/framework state is used.

| Function | Actual inputs | Actual output / restriction |
| --- | --- | --- |
| load_experiment(root=ROOT, verify_hashes=True) | Packaged root with inventory, inputs, reference | pandas corrected acquisition manifest; checks required well IDs, current corrections and packaged hashes; original_path is unused |
| validate_metadata(manifest) | Corrected metadata DataFrame | PASS counts or ValueError; current S7/S10 schema, not a general arbitrary-assay importer |
| build_context(root=ROOT) | Registered raw controls/config | Full context dict rebuilt with frozen method; no outcome-driven gate fitting |
| load_context(path=None) | Context JSON | Validated context/kernel identity |
| process_fcs(path, context=None, metadata=None) | Compatible 12-channel FCS, context and sample metadata | Internal array/masks, optical audit, counts, input hash; rejects profile/channel changes |
| calculate_ras(processed, population_mode="reporter", uncertainty=None, bootstrap_repeats=0) | Processed data; reporter/blue_positive_reporter/blue_negative_reporter | Signed ratio-of-sums contract; optional audited uncertainty or explicit deterministic paired bootstrap; default supplies deltaSE and no invented CI |
| fit_reporter_calibration(fractions,ras,model="monotone_hinge_50",fraction_basis="AC_DNA_mass_fraction") | Well-level reference arrays | New unqualified research model, never replaces the frozen model; caller must supply independent-well metadata and its own validation |
| load_res_model(path=None) | Saved model JSON | Hash-checked primary model; invalidated dependency=>ValueError |
| forward_res(fraction,model=None) | Mass fraction and loaded model | RAS inside numerical domain, otherwiseNone |
| calculate_res(ras,*,context_id,population_mode,calibration_domain_id,mode="research",sample_id=None,ras_interval=None,model=None,uncertainty_bundle=None) | Declared context/estimator domain, input RAS and optional measurement interval | Research point/identified interval, statuses, conditional bootstrap, compatible set, routine permission and separately named incompatible mapping; never clips/extrapolates |
| analyze_molecular_reference(root=ROOT) | Packaged molecular tables | Relative endpoint status and real well rows or missing status; does not rerun trace processing itself |
| fit_biological_calibration(x,y,endpoint="relative_chromatogram_index") | Finite independent-well features/relative endpoint | OLS research model; absolute endpoint rejected inv1 |
| predict_per(res_result,biological_model=None) | RES output and optional relative model | PER=None with precise qualification reason; no absolute-model adapter inv1 |
| generate_measurement_report(path,samples) | JSON-safe scientific results | Versioned JSON report with explicit nulls |

`process_fcs` metadata supplies acquisition_id, well_id, condition_label, and linked_editor_present. Absence of confirmed linkage makes blue-positive co-expression inapplicable; reporter RAS can remain available. A file with a missing BFP channel does not match this frozen 12-channel context and is rejected; support for other panels needs a separately versioned context rather than silently changing indices.

For registered sample IDs, frozen observation uncertainty may be reused only for matching RAS. For arbitrary compatible research inputs without synchronized sample draws, conditional bootstrap describes model uncertainty at fixed RAS; a supplied RAS interval expands the compatibility set. The output explicitly says no observation bootstrap. Do not imply this is identical to full synchronized uncertainty in the original S7 wells.

Original raw molecular execution remains in `amplicon_reconstruction.run`, `sanger_quantification.run`, and `prediction_validation.run`; the tested `science.py reproduce` coordinates these in an isolated directory. See REPRODUCTION_GUIDE for entry points and historical-module status.
