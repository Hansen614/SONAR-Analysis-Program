Version: `sonar-s7-s10-layer23-20261013-v3`. Reviewed 2026-10-13. Upstream Flow Quantification: `sonar-fresh-s7-s10-20261012-v2`. Experimental data: S7/S10 only; HEK293T confirmed in the current user request.

# OpenA amplicon reconstruction

## Result and evidence level
Four independently assembled no-editor F/R molecular-label pairs produce the **same 523 bp sequence**, exactly matching the newly supplied candidate FASTA. They represent **two independent transfection wells**, not four independent cultures. C280 is supported by four forward and four reverse Q20 reads and is the unique linker cytidine whose C→T substitution produces an in-frame stop in the reconstructed architecture. This supports a sequence/mechanism-based candidate. No independent construction record confirms that it was the intended target; no full plasmid sequence or accurate editing fraction is inferred.

## Method actually executed
The assembly does not use the supplied candidate or generic sequence as a template. For each of `1-0-1` through `1-0-4`, the raw PBAS2 forward call and reverse-complemented reverse call are locally aligned (match +2, mismatch −3, gap-open −8, extension −0.5). A seam at the midpoint of exact Q30-matched overlap joins the reverse read's upstream region to the forward read's downstream region. Recorded forward-primer suffix and reverse-primer reverse-complement prefix anchor the ends, requiring at least eight exact bases. The four complete assemblies agree before comparison with the provisional FASTA.

A separate evidence pass aligns all eight raw control reads back to the reconstruction. End trimming retains the interval bounded by 15-base windows with at least 12 Q20 calls; individual votes also require Q20. This avoids counting isolated high-quality calls in otherwise unreliable termini. Raw calls, trim status, qualities and base mappings are exported, so sequence inference is distinct from quality-qualified support.

| evidence_class | positions |
| --- | --- |
| PRIMER_INFERRED_NO_Q20 | 29 |
| UNIDIRECTIONAL_Q20 | 101 |
| BIDIRECTIONAL_Q20 | 393 |

**494 positions have accepted Q20 support from at least one direction; 393 have both directions.** The 29 positions without accepted Q20 support are 1–14 and 509–523. They are supplied by the recorded primers. The preliminary description of approximately 500 central positions is broadly consistent with raw-read coverage, but **500 independently bidirectionally quality-supported bases is not supported by this stricter audit**. No Q20 disagreement remains among accepted control calls. Sequenced PCR-primer bases do not independently verify the original plasmid-template termini.

## Relationship to the generic reporter
The generic primer interval is 544 bp. A declared global alignment gives 502 matches, 16 substitutions, 26 positions deleted in OpenA and five inserted positions: **net −21 bp**, rather than proof of one simple 21-bp deletion. Gap placement within divergent sequence is alignment-model dependent; the full alignment is exported. The independently reconstructed sequence, net length and candidate coordinate do not depend on selecting that gap representation.

The generic EGFP annotation establishes frame zero relative to this primer-anchored fragment. Its mapped EGFP segment ends at amplicon position 258; the mapped DHFR region begins at 289. The reconstructed intervening linker contains `CGA` at 280–282. C280→T produces `TGA` in cDNA (RNA `UGA`), after the EGFP segment and before DHFR. Among all 140 cytidines screened, C280 is the only stop-gain cytidine in this linker. Other stop-gain possibilities within EGFP or DHFR have different consequences. This prioritization uses sequence and architecture, not editor-dose correlation or the largest secondary peak.

## Source evidence
`results/molecular/OpenA_amplicon_consensus.fasta`, `OpenA_amplicon_annotated.gb`, `OpenA_independent_control_assemblies.csv`, `OpenA_reference_alignment.csv`, `OpenA_control_base_calls.csv`, `OpenA_generic_comparison.csv`, `OpenA_candidate_editing_sites.csv`, and `OpenA_vs_generic.aligned.fasta`. L23_01 visualizes Q20 support and architecture. The aligned FASTA preserves both ungapped source sequences. Original AB1, primers and provisional files are preserved unchanged.
