# Scientific freeze
Release identifier: `sonar-science-v1.0-s7s10`. This identifies a frozen implementation, not external biological validation.

- Context: `SONAR-CytoFLEXS-22cac3269aa6-v1`; gates/background rederived from the two packaged Mock acquisitions and stored explicitly.
- RAS: `ratio_of_paired_linear_sums-v2`; original ratio-of-sums core and v4 measurements preserved.
- Primary RES: `sonar-science-v1.0-s7s10::S7-hinge-k050`; three-parameter monotone hinge, fixed k=0.5, DNA mass basis, reporter population only.
- Uncertainty: retained paired-event/shared-control RAS draws; 1,000 reference-level-stratified well bootstrap draws; conditional inverse quantiles plus discrepancy compatibility sets; honest 500-draw/fold held-out uncertainty evaluation.
- Internal domain screen: largest contiguous primary/isotonic interior union set ≤0.20 mass-fraction width; RAS 0.7845–1.0065. This is explicitly exploratory.
- No silent extrapolation, clipping, pseudo-counts, artificial controls, unique points for plateaus, S7-to-S10 transfer, or relative-index-as-PER.
- Public outputs distinguish technical QC, numerical availability, interpretation permission, reference-domain identity and evidence strength. Missing values are null/blank, never zero.
- Absolute PER adapter is intentionally unavailable; the relative molecular module remains operational.

Application engineering may improve organization, import/export and interface presentation but must not change scientific semantics or automatically refit this model. A kernel/context/model/source change invalidates downstream identities and requires explicit scientific versioning/review. Old provenance versions are retained and should not be silently migrated.

The exact source/config/model/input hashes are in `RELEASE_MANIFEST.json`; model dependency hashes are embedded in the model itself. `provenance/v4_extracted_manifest.json` records the unmodified starting archive before work. `provenance/v4_reverification.json` records its successful full v4 reproduction.
