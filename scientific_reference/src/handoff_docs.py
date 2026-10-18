"""Maintain the standalone software handoff documentation for this actual release."""
import json,importlib.metadata,platform,shutil
from science_api import ROOT,RELEASE,FINAL,save_json
from final_reports import write

def run():
    write('START_HERE.md',f'''# Start here — SONAR scientific release and Codex handoff
Release `{RELEASE}`. The package includes the complete S7/S10 data and executable analytical foundation. It does not include a graphical application.

1. Read `reports/SONAR_Integrated_Evidence_Report.md` and `science/SONAR_Scientific_Freeze.md`.
2. Use `documentation/REPRODUCTION_GUIDE.md` to run verification, a real FCS-to-RES example, and a full raw-data rebuild.
3. Read `CODEX_IMPLEMENTATION_PROMPT.md`. It is the complete English prompt to copy into a new Codex conversation together with this ZIP.
4. Treat `models/res_primary/model.json`, `models/context_profiles/context_v1.json`, `results/layer0`–`results/layer3`, and `tests/golden_reference/` as the frozen current scientific contract.

The old root reports, `results/calibration`, `results/prediction`, and `baselines/` preserve historical v4/v3 evidence. Their old names/statuses do not override the current final reports. Original `results/ras_results.csv` has historical label columns: join the corrected `inventory/acquisition_manifest.csv` by acquisition ID, or use `results/layer1/RAS_Results.csv`. Do not infer current conditions from filenames.

Current command entry point: `science.py`. Root `reproduce.py` is retained historical v4 source, not the final-release entry point. All required inputs are under `inputs/` and `reference/`; any original absolute paths in provenance are historical annotations, never required runtime files.

Internal authorized research handoff. Public redistribution permissions are not established. Read `documentation/DATA_SHARING.md` before public release.
''')
    write('README.md',f'''# SONAR — RNA Editing Reporter Measurement Toolkit
Scientific reference release `{RELEASE}`. Start at [START_HERE.md](START_HERE.md).

SONAR separates Context Calibration, RAS fluorescence quantification, reference-equivalent RES calibration, and molecular/PER qualification. The fixed 50% monotone hinge is an operational research calibration for corrected S7 AC DNA mass mixtures. All 20 S7 samples have point inverses with uncertainty/status; no validated S10 transfer or absolute PER is emitted.

```sh
python science.py verify
python science.py example --sample S7_90B --output _work/example.json
python science.py reproduce
```

Use Python 3.13 and the exact dependencies in `environment/requirements.lock.txt`; see [reproduction guide](documentation/REPRODUCTION_GUIDE.md) for setup and tested scope. Normal model use loads JSON artifacts; the explicit `finalize`/`reproduce` science-maintenance paths may refit only for audit. No notebook, service, GUI or external data path is required.

The raw input directory layout from v4 is preserved to keep hashes and relative paths stable rather than duplicate it under a new `data/raw/` tree. `inventory/` holds metadata; `reference/` holds construct evidence and user instructions; `models/` holds portable contracts; `src/` contains original kernels and thin final interfaces; `science/` and final `reports/` provide evidence; `results/layer*/` and `results/integrated/` are current outputs; `tests/` includes legacy, edge and real-data golden tests.

The complete [Codex prompt](CODEX_IMPLEMENTATION_PROMPT.md) defines the next application's scope. No final Wiki narrative or publication figure design is included.
''')
    write('science/SONAR_Four_Layer_Definitions.md','''# Frozen four-layer definitions
| Layer | Name | Function | Output and unit |
| --- | --- | --- | --- |
| 0 | Context Calibration | Decode linear channels; apply acquisition, scatter/singlet selection; estimate background and distinct fluorescence thresholds; declare QC and compatibility | Versioned Context Profile; detector a.u. and event counts |
| 1 | Flow Quantification | Ratio of paired corrected sums in a declared population | RAS, dimensionless channel ratio |
| 2 | Reporter Calibration | Invert an empirical reference response g(A) | RES — Relative Editing Score; operational label AC Reference-Equivalent Score; AC DNA mass-equivalent fraction |
| 3 | Biological Calibration | Evaluate independent molecular evidence and qualify any future h(RES) | Relative molecular index now; PER=100*h(RES) percent only after qualified absolute RNA calibration |

RAS_P=sum(g_i)/sum(r_i); P_R=V∩R_q+; P_RB=V∩R_q+∩B+ only with linked editor present. V is acquisition-QC/scatter/singlet-selected events, not a viability-marker-defined live population. Display transformations do not enter sums. Distinguish repeatability, reference recovery, molecular accuracy, computational reproducibility and external transfer.
''')
    write('science/RAS_Mathematical_Definition.md',f'''# RAS mathematical definition
Estimator identity: `{FINAL['ras_estimator_id']}`; implementation `src/core.py::score`.

For selected paired events, g_i=raw_G_i-background_G and r_i=raw_R_i-background_R. RAS=sum(g_i)/sum(r_i). Do not average per-cell g/r, log-transform sums, rectify negative green, add pseudocounts, remove bright cells for primary output, or tune gates to increase calibration fit.

Event count must be at least100, corrected red sum positive, and relative SE of mean corrected red at most0.10. Invalid/insufficient results are null, not zero. Event delta SE uses paired residuals g_i−RAS*r_i; effective red support is sum(r)^2/sum(r²). Shared-control and paired-event bootstrap uncertainty, gate/background sensitivities, between-well SD and condition differences are distinct.

See `reports/Layer1_RAS_Final_Report.md` and `models/context_profiles/context_v1.json` for actual populations and uncertainty. The final API hides no-editor BFP tails from co-expression outputs but preserves them in historical diagnostic tables.
''')
    write('science/SONAR_Scientific_Freeze.md',f'''# Scientific freeze
Release identifier: `{RELEASE}`. This identifies a frozen implementation, not external biological validation.

- Context: `{FINAL['context_id']}`; gates/background rederived from the two packaged Mock acquisitions and stored explicitly.
- RAS: `{FINAL['ras_estimator_id']}`; original ratio-of-sums core and v4 measurements preserved.
- Primary RES: `{FINAL['model_id']}`; three-parameter monotone hinge, fixed k=0.5, DNA mass basis, reporter population only.
- Uncertainty: retained paired-event/shared-control RAS draws; 1,000 reference-level-stratified well bootstrap draws; conditional inverse quantiles plus discrepancy compatibility sets; honest 500-draw/fold held-out uncertainty evaluation.
- Internal domain screen: largest contiguous primary/isotonic interior union set ≤0.20 mass-fraction width; RAS 0.7845–1.0065. This is explicitly exploratory.
- No silent extrapolation, clipping, pseudo-counts, artificial controls, unique points for plateaus, S7-to-S10 transfer, or relative-index-as-PER.
- Public outputs distinguish technical QC, numerical availability, interpretation permission, reference-domain identity and evidence strength. Missing values are null/blank, never zero.
- Absolute PER adapter is intentionally unavailable; the relative molecular module remains operational.

Application engineering may improve organization, import/export and interface presentation but must not change scientific semantics or automatically refit this model. A kernel/context/model/source change invalidates downstream identities and requires explicit scientific versioning/review. Old provenance versions are retained and should not be silently migrated.

The exact source/config/model/input hashes are in `RELEASE_MANIFEST.json`; model dependency hashes are embedded in the model itself. `provenance/v4_extracted_manifest.json` records the unmodified starting archive before work. `provenance/v4_reverification.json` records its successful full v4 reproduction.
''')
    write('science/Calibration_Domains.md','''# Calibration domains
Numerical domain: A in[0,1], RAS in[0.5000914764582751,1.1744788068801943] for the frozen hinge. A mathematical formula outside this interval does not authorize extrapolation.

Observed domain: 20 wells at ten corrected mass levels. Actual RAS 0.508171–1.144856. Intervals between levels are fitted interpolation, not continuously measured standards.

Internal exploratory screen: RAS 0.7845–1.0065, primary-model equivalent54.5164–80.4085% AC mass. Determined from model/uncertainty criteria with explicit grid resolution, not chosen by downstream PUF rankings. Only the75% level's two wells occupy the screen; the bounds do not establish assay accuracy. Sample-specific RAS uncertainty expands both model sets. The two wells inside the reference-response screen have joint widths20.8 and21.8pp, so neither passes the strict 20 pp sample screen; all 20 research point estimates remain available.

Transfer domain: only the same S7 reference experiment/population is identified. No supported S10, R+B+, other reporter, treatment, instrument, culture, batch or laboratory transfer. HEK293T and instrument matches alone are insufficient. Routine quantitative use is unqualified in v1. Research numerical outputs remain available with limitations.

Machine-readable source: `results/layer2/RES_Calibration_Domain.json` and the same object embedded in the primary model.
''')
    write('science/Scientific_Limitations.md','''# Unresolved scientific limits
The75/90 correction is retrospective probable team recollection, not independently verified preparation evidence. S7 AC/INAC exact plasmid identities/lengths, loading/totalDNA and treatment metadata remain incomplete. DNA mass fractions cannot be promoted to molar fractions. A/B are wells, not independent cultures/days.

Identity compensation and missing single-color/FMO controls leave optics unvalidated. No viability marker or empirical LOQ/upper detector validation exists. RAS improves repeatability but remains red-expression dependent; effective support is much smaller than event count. n=2 reference wells and same-dataset model selection limit uncertainty/accuracy claims. Conditional inverse bootstrap intervals under-cover; broad compatibility sets have no nominal probability guarantee. High-end90–100% response is poorly separated; a fitted positive slope is not empirical resolution.

The internal screen has actual observations at only one reference level. There is no S7/S10 construct/population/condition bridge. S10 chromatogram signal is uncalibrated, direction-biased and based on a candidate target; no documented DNase/no-RT or known RNA standards qualify an absolute fraction. BFP and molecular signal both track dose; independent incremental information is unproven. No externally validated PER, interlaboratory reproducibility or public redistribution authorization is claimed.
''')
    write('science/Scientific_Decision_Log.md','''# Changes from verified v4
| Change | Reason | Affected evidence | Recalculated downstream | Conclusion |
| --- | --- | --- | --- | --- |
| Add explicit versioned context and per-sample QC/range audit | Make gates, background and limitations loadable | Same34 acquisitions | Raw-to-RAS regression and range-only sensitivity | RAS preserved; rare metadata range exceedances do not prove saturation |
| Standardize RAS contract; no-editor co-expression NOT_APPLICABLE | Separate population meaning from numerical tails | Two no-editor S10 blue-tail rows | New API table only; legacy56 rows preserved |32 reporter and10 positive-dose co-expression scores available |
| Recompute corrected-label CV, red threshold/support summaries | Verify actual repeatability and expression limits |32 wells | Final reports/diagnostics | Improvement persists; red-expression dependence explicit |
| Freeze existing fixed50% hinge | Operational, inspectable RES |20 corrected S7 wells | Portable model, forward/inverse API,20 sample outputs | Leading primary retained; no retuned knot |
| Add complete-denominator inverse validation and training-only nested discrepancy intervals | Prevent success-only accuracy or overconfident bootstrap claims |20 wells, twoCV schemes, three models |120 held-out rows plus summaries |19/20 level inverses;6.153pp conditionalMAE;5.848pp only matched14 |
| Reassess domain from primary/isotonic uncertainty screen | Distinguish mathematical from empirical support |Same reference data |DomainJSON/statuses |0.7845–1.0065 reproduced; exploratory, sparsely sampled |
| Add linear dose/dose+B and within-dose molecular benchmarks | Assess shared dose dependence |12 S10 wells/6doses |New molecular comparisons; original predictions reproduce |BFP-only and dose-only similar; incremental contribution not established |
| Package relative-only PER interface, tests, examples and English prompt | Software readiness without changing science |No new experimental measurements |Current contracts and clean raw rebuild |PER remainsnull; molecular evidence retained |

No source FCS/AB1, signed sum, original RAS estimator, molecular reconstruction, target QC criterion or established correction was changed. Original reports and models are retained as historical evidence; current final reports supersede their feasibility-only wording.
''')
    write('science/SONAR_Scientific_Overview.md','''# Scientific overview
SONAR (System for Optical Normalization and Analysis of RNA Editing), developed for SUSTech-China iGEM2026, separates measurement context from optical reporter response, empirical reference equivalence and molecular qualification. Its finished scientific contributions here are reproducible detector-scale RAS, an operational fixed-hinge RES model with error/failure/uncertainty accounting, and independent relative molecular evidence with a dose-aware interpretation.

Read `reports/SONAR_Integrated_Evidence_Report.md` for numerical findings and `science/SONAR_Evidence_Matrix.md` for claim-level boundaries. The release contains all original authorized S7/S10 inputs needed for the documented computational reconstruction; no additional SONAR series is used.
''')
    write('documentation/API_CONTRACT.md','''# Stable analytical API v1
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
''')
    write('documentation/QC_AND_STATUS_DEFINITIONS.md','''# QC, numerical availability and interpretation
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
''')
    write('documentation/DATA_DICTIONARY.md','''# Data and result dictionary
`inputs/S7/` and `inputs/S10/`: immutable authorized records, original FCS, AB1, spreadsheets, sequencing files and images. `inputs/construct_reference/` and `reference/layer23/`: associated design/reference information. `inventory/input_files.csv` records170 source-file copies and original/provided hashes. `reference/layer23/source_manifest.json` records13 associated references. The source path string is historical, never an execution dependency.

`inventory/acquisition_manifest.csv`:34 deduplicated acquisitions, original labels, corrected mass fraction, independent-well identity, input hashes, channels/profile and correction provenance. The36 original FCS files include two identical duplicated Mocks; do not count these as two extra controls. No correction renames files.

`results/layer0/Sample_QC.csv`: recorded/acquisitionQC/cell/singlet/reporter/BFP/co-expression counts, context/provenance, range and optical warnings. `Detector_Range_Audit.csv`: per channel metadata range, extrema and counts; channel-count sums may double-count events. `Range_Exclusion_Sensitivity.csv`: unique selected events outside green/red range, primary versus diagnostic-excludedRAS.

`results/layer1/RAS_Results.csv`: current condition labels, population/estimator/context, corrected sums, selected and effectiveN, RAS and intervals. Original `results/ras_results.csv` is immutable with historical label columns; join IDs to corrected metadata. `Normalization_Repeatability.csv`: per condition n=2 sample CV percent. Red profiles/support and threshold sensitivity describe expression dependence.

`results/layer2/RES_Sample_Results.csv`:20 actualS7 rows. RAS input; known corrected mass; `res_mass_fraction` (research ordinary field), `research_res_mass_fraction`, identified/conditional/compatibleintervals, model and domain IDs, success counts, scientific/numerical statuses. List/object cells are validJSON strings. `routine_res_mass_fraction` and `validated_RNA_editing_fraction` are blank. `RES_Inverse_Validation.csv`:120 held-out records (3 models×2 schemes×20 wells), truefraction, train IDs/domain, prediction/errors, inversionfailures and honestintervals. Error_pp means100×(recovered−true). Full-set point MAE is undefined when an inverse is missing. `RES_Model_Comparison.csv` separates allheldout/interior/common unique subsets and their denominators. `S10_Transfer_Restricted_Results.csv` has no ordinary RES; a hypotheticalmapping is separately named.

`results/molecular/`:original read/label/well/site/reconstruction evidence. `signal_index` is direction-specific no-editor-subtracted relative index; `raw_signal_index` adds back the shared offset for prediction. Neither is absolute edited RNA. TechnicalF/R labels are nested within12 wells. `results/layer3/`:dose-aware molecular comparisons, all prediction rows, extrapolationflags and sixwithin-dose paired differences. Error units are chromatogramindex, neverpercentage points.

`results/integrated/SONAR_Sample_Reports.json`:32 complete sample objects withQC,RAS,RES,PER,provenance. `SONAR_Evidence_Matrix.csv`:claim-level evidence forWiki. Historical `results/calibration`, `results/prediction` and oldreports remain audit material. MissingCSV is blank and missingJSON isnull, neverimplicitzero.
''')
    write('documentation/MODEL_IO_SCHEMAS.md','''# Portable model and output contracts
Primary model: `models/res_primary/model.json`; context: `models/context_profiles/context_v1.json`; resampling/curve values: `models/res_primary/uncertainty.json`; benchmarks: `models/res_alternative/`; molecular-only models and qualification flags: `models/molecular/`. No pickle/notebook state is used.

The primary object contains modelID/version/family, equations and both coefficient bases, knot policy/constraints/fitting method, independent-well sampleIDs, input/outputunits, massbasis/population/context, fourdomain classes, validation denominators/errors/coverage, inverse and output permission policies, uncertaintyartifact, and code/config/input hashes. `load_res_model` rejects changed scientific dependencies. Changing display layout does not authorize scientific changes.

`schemas.json` supplies minimal JSONSchema contracts for application integration. They describe required core fields and nullability; additional documented fields carry evidence/provenance. Scientific validation remains in the tests and APIs; passing JSON shape validation is not assay qualification.
''')
    schemas={'schema_version':'1.0','release_id':RELEASE,'contracts':{
      'context':{'type':'object','required':['context_id','ras_estimator_id','instrument_fingerprint','gate_parameters','support_requirements','limitations']},
      'RAS':{'type':'object','required':['sample_id','population_mode','context_profile_id','estimator_version','ras','score_status','qc_state'], 'properties':{'ras':{'type':['number','null']},'n_selected':{'type':'integer','minimum':0},'sum_G_corrected':{'type':'number'},'sum_R_corrected':{'type':'number'}}},
      'RES':{'type':'object','required':['RAS','model_id','input_basis','output_unit','res_mass_fraction','numerical_status','scientific_status','calibration_region','routine_status'], 'properties':{'res_mass_fraction':{'type':['number','null'],'minimum':0,'maximum':1},'research_res_mass_fraction':{'type':['number','null']},'hypothetical_incompatible_mapping':{'type':['number','null']},'exact_inverse_interval':{'type':['array','null']},'compatibility_intervals':{'type':'array'}}},
      'PER':{'type':'object','required':['PER','unit','PER_status'], 'properties':{'PER':{'type':'null'},'unit':{'const':'percent_edited_RNA'}}}}}
    save_json(ROOT/'documentation/schemas.json',schemas)
    write('documentation/REPRODUCTION_GUIDE.md','''# Reproduce the scientific release
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
''')
    write('documentation/SCIENTIFIC_ACCEPTANCE_TESTS.md','''# Scientific acceptance tests
`tests/test_science.py`, `tests/test_layer23.py` and `tests/test_s7_correction.py` retain44 v4 tests. `tests/test_final_science.py` adds 18 counted cases for actual raw-to-score golden cases and mathematical/interface edges. `tests/golden_reference/real_samples.json` contains realS7_90B,S7_5B,S7_100A,S10_1_8_A measurements, not fabricated examples. Synthetic tests are explicitly named and test only edge behavior.

Acceptance includes corrected labels/raw hashes; channel identity; separate background/threshold; paired signed ratio and positive denominator; reporter/co-expression/missing editor semantics; missing channel rejection; load-only frozen model; forward/inverse roundtrip; plateau interval; out-of-domain null; uncertainty denominators and registered-sample mismatch refusal; research/routine/transfer separation; missingmolecular reference andPER refusal; model/core/context versionrejection; deterministicresults; independent-fold membership; all-held-out denominators; researchfits leave frozen model unchanged.

Full integration additionally executes `python science.py reproduce`. No v4 or final numbers may be “updated” in goldens merely to pass a refactor. A discrepancy requires investigation and explicit scientific versioning. Test success verifies implementation, not optical assay accuracy, external transfer or RNAediting qualification.
''')
    write('documentation/SOFTWARE_REQUIREMENTS.md','''# Next application requirements
Product: SONAR — RNA Editing Reporter Measurement Toolkit. Scientificbackend must remain GUI-independent. A lightweight Streamlit UI is an acceptable first application; no GUI has been built here.

Priority 1 reproduce the frozen engine; priority2 installablePythonpackage without changingmath; priority3 CLI/import/reporting; priority4 accessibleGUI; priority5 versionedmodel loading and user-referencefitting; priority6 validation/errors/export; priority7 docs/examples/releasepackaging. The fuller instructions are in CODEX_IMPLEMENTATION_PROMPT.md.

Workflow: import FCS+controls+requiredwell metadata; inspectContext/QC; calculateRASwith declaredpopulation; loadcompatiblemodel or fit reviewable user reference; inspectRESforward/inverse/uncertainty/domains; evaluate qualifiedmolecular data; export table+report+provenance bundle. RESmust be prominent and understandable. Show source and correctedlabels together. KeepQC,numericalavailability andinterpretationpermissions separate. Never substitute a percentage editing label for RESorrelative chromatogram index. Missing data are notzero; error states must be informative.

New panel/instrument support is a versionedcontext extension; no silent channel guess, automatic unverified compensation or arbitrary reuse ofS7 calibration. A supplied absolutemolecular model requires a reviewed qualification adapter; v1 always returns PER null. Preserve all frozen tests and add meaningful import/export/error-flow integrationtests.
''')
    write('documentation/KNOWN_ISSUES.md','''# Known issues and intentional boundaries
Scientific limits are fully enumerated in `science/Scientific_Limitations.md`. Runtime currently supports this fixed 12-channel CytoFLEXScontext; arbitrary FCS channel panels need explicit adapters. The CLIexample targets registeredS7/S10 acquisitions. The fittingprimitive does not perform a complete user data model qualification workflow. AbsolutePERadapter is intentionally absent.

Legacy modules use a package-relative ROOT and are coordinated by the final entry point; packaging/refactoring is future engineering. Historical original paths remain in source provenance but are never required by testedfinalcommands. Old v4 reproduce.py is retained as historicalcode and is not the final entry point. Historical RAS columns have oldlabels; new exports join corrected metadata byID. The redundant nested v2 ZIP was omitted to avoid duplicating raw data. Its hash is preserved in provenance/redundant_nested_archive_omission.json; baseline tables, configurations, audit records and all runtime inputs remain. The original v4 archive was preserved unchanged.

Compatibilitysets use a finitegrid and are not confidencebounds. Bootstraps cannot resolve between-day variance with n=2. Marginal predictor-range flags do not prove multivariate in-domainstatus. All dependencies are version-pinned; only the recorded Python/macOS environment was executed, not every supported futureplatform.
''')
    write('documentation/DATA_SHARING.md','''# Data sharing
This package contains original experimental data and associated source records authorized for internal S7/S10 analysis and Codex handoff. Inclusion is not permission for unrestricted public redistribution. Confirm experimental-team and institution permissions before publishing raw files or the full archive. Wiki may use evidence-bounded derivedresults subject to the team's review. Do not upload source data to thirdparty services merely to implement a localinterface.
''')
    # Exact runtime dependency closure, avoiding unrelated packages in the host environment.
    packages=['numpy','scipy','pandas','matplotlib','scikit-learn','flowio','biopython','openpyxl','pillow','pillow-heif','pytest',
      'joblib','threadpoolctl','contourpy','cycler','fonttools','kiwisolver','packaging','pyparsing','python-dateutil','six','pytz','tzdata','et-xmlfile','iniconfig','pluggy','pygments']
    versions={p:importlib.metadata.version(p) for p in packages}
    write('environment/requirements.lock.txt','\n'.join(f'{p}=={v}' for p,v in versions.items()))
    save_json(ROOT/'environment/runtime.json',{'python':platform.python_version(),'platform':platform.platform(),'packages':versions,'tested_platform_only':True})
    write('environment/README.md','Use Python 3.13.7 and requirements.lock.txt. This directory records the tested dependency environment; Python and binary wheels are not embedded. Allscientific data and executable source are embedded. Installation may require networkaccess; analysis does not.')
    write('CODEX_IMPLEMENTATION_PROMPT.md',PROMPT)
    print('Scientific freeze, API/data/status contracts and complete Codex prompt saved',flush=True)

PROMPT='''# Build the SONAR application from this frozen scientific handoff

You are continuing SONAR — RNA Editing Reporter Measurement Toolkit for SUSTech-China iGEM 2026. This ZIP is a self-contained scientific handoff, release `sonar-science-v1.0-s7s10`. Develop the reusable software application around the supplied, tested scientific engine. Do not reconstruct the experiments from conversation memory or redesign the metrics. Work from actual files in this extracted package. Preserve raw inputs and the frozen reference outputs. Do not publish or upload these experimental data without the user's separate authorization.

## 1. Scientific purpose and existing implementation

SONAR means System for Optical Normalization and Analysis of RNA Editing. It separates four layers:
1. Context Calibration establishes channel decoding, acquisition/scatter/singlet selection, additive backgrounds, distinct positivity/quantification thresholds, support and optical limitations.
2. Flow Quantification computes RAS from the ratio of paired, signed, corrected linear green and red sums in a declared population.
3. Reporter Calibration converts RAS through an empirical AC/INAC reference model to RES — Relative Editing Score, operationally “AC Reference-Equivalent Score.” The current reference axis is DNA mass fraction, not molecular editing fraction.
4. Biological Calibration evaluates independent molecular data and would qualify PER=100*h(RES) only after a calibrated absolute RNA assay and compatible validated model exist. The present S10 evidence supports a relative chromatogram index, not absolute PER.

Read START_HERE.md, science/SONAR_Scientific_Freeze.md, science/SONAR_Four_Layer_Definitions.md and reports/SONAR_Integrated_Evidence_Report.md first. The final layer reports, evidence matrix, domain JSON, worked examples and scientific limitations are authoritative current interpretation. Old root reports/results and baselines retain provenance, not competing current definitions.

The complete actual scientific source is in src/. The original unchanged kernels include core.py, analyze.py, inverse_calibration.py, reporter_calibration.py, ab1_processing.py, amplicon_reconstruction.py, sanger_quantification.py and prediction_validation.py. s7_correction.py and correction_analysis.py implement the authorized metadata overlay and v4 recalibration. New final interfaces are science_api.py; final derivation/validation is finalize_science.py; reports/diagnostics are generated by final_reports.py; clean raw reconstruction is release_verify.py. The current tested entry point is science.py. Root reproduce.py is historical v4 code, not the final entry point.

Inputs are already packaged under inputs/S7/, inputs/S10/, inputs/construct_reference/ and reference/. Corrected metadata and original hashes are in inventory/. Original absolute source paths are provenance strings and must never become required runtime paths. Keep relative paths and do not duplicate large raw files merely to make a prettier folder tree.

## 2. Reproduce before changing anything

Use documentation/REPRODUCTION_GUIDE.md and environment/requirements.lock.txt. The actual commands, from the extracted package root, are:

```sh
python science.py verify
python science.py example --sample S7_90B --output _work/example.json
python science.py example --sample S7_5B --output _work/weak_example.json
python science.py example --sample S7_100A --output _work/boundary_example.json
python science.py example --sample S10_1_8_A --output _work/S10_transfer_restricted.json
python science.py reproduce
```

The first command verifies raw/model hashes and all regression tests. The examples are actual raw FCS-to-context-to-RAS-to-loaded-RES calculations. The full reproduction command rebuilds flow processing, paired bootstraps, molecular reconstruction/trace metrics, corrected reference calibration and final contracts in _work/raw_rebuild/, then compares frozen tables, masks, models and integrated reports. It must pass before refactoring. Treat differences as problems to investigate, not permission to rewrite golden values. Tolerance is rtol=atol=1e-12 in the recorded environment. Computational reproduction does not establish biological or external validation.

Inspect RELEASE_MANIFEST.json and provenance/ for the actual scientific freeze and prior clean-extraction evidence. Preserve tests/test_science.py, tests/test_layer23.py, tests/test_s7_correction.py, tests/test_final_science.py and tests/golden_reference/real_samples.json. Synthetic unit tests are mathematical edge cases only and must never appear as experimental data.

## 3. Scientific definitions that may not change

RAS must remain sum(g_i)/sum(r_i), using background-corrected linear EGFP and mCherry from the exact same paired events. Keep signed green values. Do not replace it with a mean of per-cell ratios, a logged ratio, clipped positives, an arbitrary offset or a bright-cell-trimmed statistic. P_R is selected singlets above the red quantification threshold. P_RB additionally exceeds the BFP threshold and requires confirmed editor linkage/presence. No-editor blue tails are not editor co-expression. BFP is not a direct measurement of active ORCA or RNA editing. N_eff,R=sum(r)^2/sum(r²) is red-weighted event support, not biological n.

Current context models/context_profiles/context_v1.json has explicit channels, control hashes, saved gates, additive backgrounds, positivity thresholds, acquisition fingerprint, numerical representation and limitations. Identity compensation in these files is not validated optical compensation. Do not infer missing spillover coefficients from experimental green/blue relationships. Display log/arcsinh transformations must never alter the sums. Missing channels or changed acquisition profiles require explicit separately qualified contexts; do not silently guess channel meaning. Separate technical QC from RAS availability and downstream calibration permission.

S7 corrected DNA mass inputs are 0, 5, 15, 20, 30, 40, 50, 75, 90 and 100%. Original 10 means 15%; original 75A/B mean 90%; original 90A/B mean 75%. The latter change is retrospective probable team recollection, not independently verified preparation. Preserve original names and correction provenance. Never infer current fractions from source filenames. All original RAS numerical values remain unchanged; historical results/ras_results.csv still has old label columns. Use the corrected inventory manifest by acquisition ID or current results/layer1 exports.

S10 has 100 ng reporter and 1,000 ng total DNA per well; reporter:editor ratios 1:0, 1:0.5, 1:1, 1:2, 1:4 and 1:8. A/B are independent transfection wells within this experiment. ORCA is linked to BFP by P2A. Sequencing labels 1–2 map to A and 3–4 to B, with RNA extracted after flow at the same experimental timepoint. Exact RNA cell selection and elapsed interval are unresolved. Events and sequencing technical observations are not independent biological replicates.

## 4. Primary RES model and allowed outputs

Load models/res_primary/model.json and uncertainty.json. The frozen model is `sonar-science-v1.0-s7s10::S7-hinge-k050`, a continuous monotone hinge with fixed k=0.5:

g(A)=0.5000914764582751 + 0.4913687133161195*A + 0.3660372342115992*max(0,A-0.5).

A is AC DNA mass fraction. Both segment slopes are nonnegative: 0.4913687133161195 and 0.8574059475277187. The serialized coefficients also express alpha+lower_slope*min(A,0.5)+upper_slope*max(A-0.5,0); do not confuse these bases. Exact stored parameters are authoritative. The knot was not searched during this release. Affine and isotonic in models/res_alternative/ are benchmarks, not interchangeable default models.

Numerical domain A = 0–1 corresponds to RAS 0.5000914764582751–1.1744788068801943. Out-of-range inputs return null without clipping/extrapolation. Flat inverse regions return identified intervals, not invented points. The largest conservative internal screen is RAS 0.7845–1.0065, hinge equivalents 54.52–80.41% AC mass. This is an engineering compatibility screen, not a validated assay range or ±10 pp accuracy claim; only the actual 75% reference level has observations inside it. Adding actual sample uncertainty expands the two in-screen wells' joint model sets to 20.8 and 21.8 pp; neither passes a strict 20 pp joint sample criterion, although useful research estimates remain. The observed 90–100% response is poorly separated despite the fitted positive upper slope.

All 20 S7 reference wells have model-defined research inverses. The model's leave-reference-level forward RMSE is 0.036368 RAS on 16 forward-evaluable interior cases. Inverse recovery succeeds in 19/20 cases with MAE 6.153 pp and RMSE 7.078 pp among those 19; one case fails. The 5.848 pp MAE is only the 14-well common-success subset across all three models. Never report that subset as full-set accuracy or discard failed rows.

Preserve both uncertainty outputs: conditional inverse bootstrap quantiles with success denominators, and the wider model-discrepancy compatibility set. The narrow conditional intervals under-cover true held-out inputs (5/20 level-held-out); neither type is a validated 95% measurement interval. Use the stored shared-control observation draw structure for registered samples. For arbitrary inputs without those draws, expose the narrower scope of uncertainty exactly as the API does.

Research mode can show compatible numerical RES with evidence status. Routine mode must require appropriate scientific qualification; no current S7 model is routine-qualified. Preserve separate research fields instead of suppressing every exploratory number. Scientifically incompatible samples must not populate ordinary quantitative RES; a separately named hypothetical mapping can be offered in an advanced sensitivity view. S7-to-S10 transfer is not established, especially not to BFP-gated co-expression. Always display mass-equivalent units, model identity, population, domain and research status beside RES.

A default application run must load the frozen model, never refit it for convenience. Fitting user references is a separate explicit workflow with its own independent-well metadata, context, fraction basis, model identity, uncertainty, grouped validation and scientific review. Do not silently promote the S7 model to arbitrary cell types/reporters.

## 5. Molecular analysis and PER restrictions

Preserve the provisional 523 bp OpenA reconstruction and candidate C280 annotation. There are 48 AB1 traces, 47 site-eligible reads, 23 complete technical F/R pairs and 12 independent wells. One forward read 1-8-2.F fails local flank identity and must remain excluded from the candidate point estimate while retained in audit. Direction-dependent signal and primer-inferred termini remain visible.

The endpoint is a relative chromatogram composition index. No known-RNA-mixture response calibration, independently verified intended target, documented DNase/no-RT controls or matched RNA-population bridge qualify an absolute edited RNA fraction. Do not put this index into a percent RNA editing field. The current predict_per function returns PER=null with a reason; preserve the framework and relative molecular analysis.

S10 BFP fraction predicts this relative index better than RAS, but linear editor dose is similar: dose-held-out RMSE 0.019219 for BFP, 0.019884 for linear dose, 0.017795 for dose+BFP, 0.090155 for RAS. Six within-dose A/B pairs give limited support for independent BFP information. No causal or external-generalization claim is justified. Preserve both leave-one-well and leave-one-dose validation, uncertainty, endpoint units and predictor extrapolation flags. A deterministic invertible RAS→RES transform does not add new sample information. Do not force a staged S10 RES→RNA model.

Absolute PER model support is future scientifically reviewed work. A boolean field saying “qualified” must not bypass the absence of a validated adapter, assay and domain. Explain unavailable PER informatively rather than fabricating zero or a percentage.

## 6. Actual API to package

Use documentation/API_CONTRACT.md and MODEL_IO_SCHEMAS.md. The functions already exist in src/science_api.py:
load_experiment, validate_metadata, build_context, load_context, process_fcs, calculate_ras, fit_reporter_calibration, load_res_model, forward_res, calculate_res, analyze_molecular_reference, fit_biological_calibration, predict_per, generate_measurement_report.

They run independently of an interface. The current CLI analyzes registered samples; a general import workflow is an engineering extension that must preserve scientific contracts. The low-level fitting functions produce research models, not automatic qualification. Raw molecular processing remains in the explicit original modules coordinated by science.py reproduce. Respect code/config/context/model dependency hashes and version compatibility. Read documentation/DATA_DICTIONARY.md for exact current columns and the distinction between legacy and corrected metadata.

## 7. Build in this order

Priority 1: verify the supplied engine, inspect actual files and reproduce all frozen results. Record any blockers precisely and complete unaffected work.
Priority 2: refactor into an installable Python package while retaining original numerical kernels, portable models and regression fixtures. Replace implicit path globals through explicit experiment-root plumbing as needed; keep all input/model/output paths portable. Do not change the scientific model or golden values.
Priority 3: implement a robust CLI for importing a compatible experiment, metadata validation, context selection, RAS/RES analysis and report export. Preserve the existing commands or supply documented tested equivalents.
Priority 4: implement an accessible graphical interface. A lightweight Streamlit UI is reasonable; a justified equivalent is acceptable. Keep the scientific backend independent. Users should import data, review Context/QC, inspect RAS populations, use RES reference calibration, evaluate molecular reference status and export results.
Priority 5: provide interactive frozen-model loading and a clearly separated user-reference fitting workflow. Make RES a prominent feature with the forward curve, actual reference points, inverse calculation, uncertainty, status and sample-level comparison. Do not expose incompatible models as compatible merely because JSON loads.
Priority 6: add clear errors, input/metadata validation, consistent null/status handling, safe filenames and reproducible exports. New datasets require their own well identities and original/corrected labels. Do not upload files to external services by default.
Priority 7: document installation/use/scientific limits, provide actual example data/goldens, test the packaged application after clean extraction, and deliver source, runnable app, dependency environment, user guide, test results and release archive.

## 8. Interface and export requirements

Use simple labels and progressive disclosure. Show the experimental unit and population clearly. Separate technical QC, whether a number can be computed, whether calibration applies, and what interpretation is permitted. Never hide available RAS because RES/PER is unavailable. Preserve ordinary research RES for compatible samples while marking it appropriately. Show original and corrected S7 labels together; do not relabel raw files.

Export per-sample identity, condition, well, input hash, software/config/context/model versions; all relevant gate counts and support; signed green/red sums and RAS with uncertainty; RES point/identified/compatibility intervals and conditional bootstrap denominator; numerical/scientific/domain statuses; PER or an explicit null reason; relevant relative molecular results; methods and limitations. Provide CSV/JSON plus a readable measurement report and diagnostic figures. Include machine-readable provenance and an exact reproduction command. Missing values must not be 0. Context/RES/PER version changes must invalidate incompatible downstream artifacts.

## 9. Testing and completion

Keep all supplied scientific tests and real-data goldens. Add meaningful integration tests for importing, validation, wrong channels, missing editor/molecular data, negative corrected green, denominator failures, model mismatch, plateau/out-of-range inverse, research/routine modes, export and GUI/backend separation. Verify correct failure behavior as well as success. Reproduce final results within declared tolerance after packaging. Inspect actual output reports and application flows, not just source code or launch logs.

Deliver the complete app source, runnable installation/entrypoints, exact environment, scientific model artifacts, documentation, examples/goldens, automated tests with actual results, and a self-contained release ZIP. State what was implemented and tested and any unsupported platforms or scientific limits. Do not claim absolute RNA editing prediction, external transfer or experimental validation that this dataset does not provide. Do not independently write final Wiki claims or produce a public data release as part of ordinary application engineering.
'''

if __name__=='__main__':run()
