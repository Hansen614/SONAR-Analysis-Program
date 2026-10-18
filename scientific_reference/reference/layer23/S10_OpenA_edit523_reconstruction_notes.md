# S10 OpenA-edit523: provisional amplicon reconstruction

**Status: candidate sequence, NOT verified reference or validated RNA-editing measurement.** Created from the user-provided S7/S10 SONAR reconstruction ZIP, using S10 raw AB1 chromatograms, the recorded forward/reverse primers, and the generic annotated reporter only as a flanking/architecture aid. No original source files were modified.

## Inputs and workflow

- Recorded forward primer: `ATGGCCGATAAGCAGAAGAACG` (22 nt).
- Recorded reverse primer: `CCACACTTTTCACCCAGGTCAC` (22 nt).
- Generic reporter design predicts 544 bp between the primers, whereas S10 contains an approximately 21 bp shorter internal region; candidate OpenA amplicon is 523 bp, consistent with the name `OpenA1-edit523`.
- Reconstructed 500 central base positions from aligned forward and reverse AB1 base calls from four independent S10 1:0 molecular labels (two transfection wells, two labels per well); recovered terminal 11 and 12 positions from the primer-anchored generic design. The four 1:0 F/R pairs show high agreement across the overlapping central region, with read-end discrepancies noted during reconstruction.
- Reconstructed S10 523-bp candidate sequence is provided in the companion FASTA; it matches both provided primers at the two ends. This is NOT an experimentally verified full plasmid construct or a separately validated clone.

## Candidate edited base

- The reconstructed protein-coding frame supports a candidate target at **position 280 (1-based, forward amplicon orientation)**.
- The local codon is **`CGA`**, which would become **`TGA`** after C→U editing of the corresponding RNA (recorded as C→T in RT-derived cDNA). This is consistent with an editing-triggered stop switch in the reporter.
- This is a strong sequence-based **candidate**, not a substitute for independent confirmation that this is the intended editing site and that the specific PCR product derives from RNA rather than residual DNA.

## Exploratory chromatogram observations

Raw ABI processed-peak channels (`DATA9–DATA12`) were mapped by each read's `FWO_1` dye-order metadata. An alternate-base ratio `alt_peak/(reference_peak + alt_peak)` was assessed at the same called-base peak position (`PLOC2`) in each read, mapping F C→T and R G→A at candidate position 280. These ratios are **not editing fractions** and are not yet corrected for dye/channel or sequence-context biases.

| Editor:reporter DNA ratio | Forward T/(C+T) (mean) | Reverse A/(G+A) (mean) |
|---|---:|---:|
| 0 | 0.045 | 0.016 |
| 0.5 | 0.045 | 0.049 |
| 1 | 0.048 | 0.059 |
| 2 | 0.074 | 0.145 |
| 4 | 0.107 | 0.164 |
| 8 | 0.145 | 0.287 |

- Four forward and four reverse reads per ratio are from two parent transfection wells (they are not eight independent biological replicates).
- Both directions show a generally increasing alternate peak with editor dose. This supports further investigation of C280 but **does not justify reporting RNA editing percentages**.
- Several other cytidine positions also show alternate-peak changes; check bystander editing, read alignment, dye spectral behavior, and background. One 1:8 forward chromatogram was vendor-flagged for mixed peaks. The F/R ratios differ substantially, emphasizing the need for quantitative assay calibration and uncertainty analysis.

## Recommended requirements before PER calibration

1. Independently verify the provisional edited position and reporter coding context (e.g., using construction records or confirmation sequencing), and preserve versioned reference sequence.
2. Confirm the S10 PCR products are RNA-derived; audit DNase/no-RT controls if available. Check technical-read, molecular-label and parent-well relations.
3. At C280, quantify the C/T (and reverse G/A) chromatogram components with a validated baseline/cross-talk strategy; ideally use known-mixture standards or orthogonal amplicon sequencing. Include both strand concordance and uncertainty.
4. Investigate background and other changing cytidine positions as potential bystander signals, rather than assuming a single editing event.
5. Aggregate results at independent-well level (two wells per condition), then validate the relationship to RAS/RES using appropriate independent data.

**Main conclusion:** missing full-plasmid GenBank is not an absolute barrier to locating a plausible S10 RNA-editing reporter target; the lack of a validated site-specific editing-fraction assay is still a barrier to claiming a calibrated PER.
