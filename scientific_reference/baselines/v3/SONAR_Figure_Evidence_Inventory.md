# SONAR Figure Evidence Inventory

These are scientific messages and available evidence, not final illustration prompts. All diagnostics have PNG and editable SVG exports; source tables are enumerated in `figures/figure_index.csv`. Every A/B condition has two user-confirmed independent transfection wells; independence of culture/day is not established.

| Candidate | Scientific message | Data and recommended plot | Replicate support | Status and limitation |
| --- | --- | --- | --- | --- |
| Context and gates | One declared context processes the session consistently | F01–F03; control scatter, background distributions, retention bars | 2 unique Mock acquisitions; 32 experimental acquisitions | Partially supported: same-session processing; no viable-cell or optical validation |
| Normalization | Red normalization reduces dispersion in most conditions, with exceptions | F04_S7/F04_S10 and F05; paired raw/corrected/RAS points and CV comparison | 10 S7 and 6 S10 conditions; n=2 independent transfection wells per condition | Partially supported: show every exception; no accuracy claim |
| BFP dimension | Blue detection and reporter activity change differently | F06; B+ fractions and mode-specific RAS | 12 S10 transfection wells; n=2 per condition | Partially supported: linkage user-confirmed; multicolor boundary unvalidated |
| Robustness | Scores are insensitive to tested small background/gate changes | F07/F08; sensitivity distributions and event-subsampling widths | Within-acquisition resampling, not biological replication | Supported within the declared computational domain; not optical validity |
| Reference weighting | Bright red cells contribute disproportionate signal | F09; red-share versus perturbation and red-bin response | 32 acquisitions, technical event support | Supported descriptive finding; removal is a sensitivity analysis only |
| Matched blue profiles | Some common-intensity bins lack sufficient denominator precision | F10; profiles plus counts and explicit gaps | 10 positive-ratio S10 acquisitions, 40 bins | Partially supported: 14 bins unavailable, no standardized aggregate |
| Reporter reference ladder | Broad response with low-end reversals and high-end ambiguity | F04_S7; all observations and confirmed AC mass fractions, no forced fit | Two independent transfection wells per mass fraction | Partially supported: not a validated inverse calibration |
| Molecular readiness | Traces exist but paired RNA truth is unqualified | F11; read-quality / alignment audit and a pairing-status table | 48 reads / 24 labels / 12 parent wells; F/R technical reads | Supported audit; PER validation plot unsupported |
| Plate-readout limitation | Weak red signal prevents a qualified plate normalization | F12; raw red values and documented PBS scan mean | 12 labelled EDIT wells; 81 spatial positions per scan well | Partially supported: no matched single-point blank; no molecular endpoint |
| Four-layer future prediction | How qualified references could connect RAS, RES and PER | A later conceptual diagram tied to layer-status table | No prediction-validation sample set | Conceptual only for RES/PER; never draw synthetic prediction observations |

The strongest eventual Measurement figures would combine normalization with its exceptions, the actual S7 reference response, and BFP detection versus RAS. Preserve the exploratory instrument-scale qualifier and n=2 within-experiment transfection-well scope. Do not label a positive rank trend as calibration validity or a repeated software run as biological reproduction.
