Version: `sonar-s7-s10-layer23-v4-label-corrected`. Correction date: 2026-10-13. Reference basis: `S7_AC_DNA_mass_team_corrected_20261013`.

# S7 label-correction record

The primary interpretation exchanges original 75% and 90% reference labels, exactly as authorized by the experimental team. Source: **Experimental team-reported probable label transposition, 2026-10-13.** The team described a probable transposition from retrospective recollection. No contemporaneous independent preparation record verifies it. Improved fit is conditional model agreement and **does not prove the labels were wrong**.

| original_acquisition_id | original_filename | pre_correction_ac_mass_fraction | corrected_ac_mass_fraction | correction_status |
| --- | --- | --- | --- | --- |
| S7_75A | 75A.fcs | 0.75 | 0.9 | USER_AUTHORIZED_PRIMARY_RETROSPECTIVE_PROBABLE_NOT_INDEPENDENTLY_VERIFIED |
| S7_75B | 75B.fcs | 0.75 | 0.9 | USER_AUTHORIZED_PRIMARY_RETROSPECTIVE_PROBABLE_NOT_INDEPENDENTLY_VERIFIED |
| S7_90A | 90A.fcs | 0.9 | 0.75 | USER_AUTHORIZED_PRIMARY_RETROSPECTIVE_PROBABLE_NOT_INDEPENDENTLY_VERIFIED |
| S7_90B | 90B.fcs | 0.9 | 0.75 | USER_AUTHORIZED_PRIMARY_RETROSPECTIVE_PROBABLE_NOT_INDEPENDENTLY_VERIFIED |

The original source label 10 remains corrected to 15% under the prior confirmation. `original_ac_mass_fraction` records the literal filename/source label (0.10 for those samples), `pre_correction_ac_mass_fraction` records v3 interpretation (0.15), and `corrected_ac_mass_fraction` records the current primary basis. Source sample IDs, acquisition IDs, well IDs, filenames, hashes, dates, status and correction source remain separate. A/B wells stay independent transfections; no well is reassigned to another replicate.

The original v3 release ZIP is retained unchanged. `baselines/v3/` preserves its scientific source/configuration/output snapshot and archive hash. A complete archived v3 rerun passed before correction; see `pre_correction_reverification.json`. `reports/S7_correction_unaffected_hashes.csv` verifies preserved evidence by file hash.

Affected: the primary sample interpretation, S7 reference table, three calibration fits, grouped validation, inverse estimates/uncertainty, S7-axis figures, conditional S10 mappings, affine-rescaling sensitivity, scientific registers and integrated reports. Preserved: original FCS/AB1, Layer 0–1 estimator and configuration, event masks, backgrounds, RAS values and uncertainties, BFP fractions, molecular reference and Sanger metrics, flow–molecular pairs, direct signal models and their validation. Historical `results/ras_results.csv` retains its v3 label column and bytes; current calibration always joins the corrected manifest by acquisition ID. It must not infer current AC input from the historical column.

The updated execution entry uses the verified v3 upstream artifacts and recalculates only affected dependencies. This is not another FCS gate fit or Sanger reanalysis. A changed upstream hash invalidates the correction run. No unrelated implementation defect was folded into this correction.
