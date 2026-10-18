# Portable model and output contracts
Primary model: `models/res_primary/model.json`; context: `models/context_profiles/context_v1.json`; resampling/curve values: `models/res_primary/uncertainty.json`; benchmarks: `models/res_alternative/`; molecular-only models and qualification flags: `models/molecular/`. No pickle/notebook state is used.

The primary object contains modelID/version/family, equations and both coefficient bases, knot policy/constraints/fitting method, independent-well sampleIDs, input/outputunits, massbasis/population/context, fourdomain classes, validation denominators/errors/coverage, inverse and output permission policies, uncertaintyartifact, and code/config/input hashes. `load_res_model` rejects changed scientific dependencies. Changing display layout does not authorize scientific changes.

`schemas.json` supplies minimal JSONSchema contracts for application integration. They describe required core fields and nullability; additional documented fields carry evidence/provenance. Scientific validation remains in the tests and APIs; passing JSON shape validation is not assay qualification.
