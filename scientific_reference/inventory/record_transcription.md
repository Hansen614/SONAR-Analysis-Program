# Primary-record transcription and user-confirmed identities

Photo transcription reviewed 2026-10-12; user metadata reconciled 2026-10-13. Statements below describe what each primary file alone shows; the dated confirmation section resolves selected gaps. This transcription was made from the supplied photographs and workbooks during the fresh reconstruction. It is not inherited from a previous SONAR analysis. Originals are copied byte-for-byte under `inputs/`.

## S7 photograph

Source: `inputs/S7/IMG_1694.HEIC` (readable rendering: `inventory/S7_record.png`).

- The AC row reads 0, 5, 10, 20, 30, 40, 50, 75, 90, 100. A blue 15 and arrow are written at the 10 position. The amount row contains a corresponding blue 3 beneath the original 2. These are evidence of a possible correction; they do not establish whether the FCS label or actual mixture was changed.
- The next row reads approximately 0, 1, 2 (blue 3), 4, 6, 8, 10, 15, 18, 20. The units and final amount per well are not sufficiently documented for a molar-fraction calculation.
- The bottom has preparation lines labelled A and B with Lipo 3000 / P3000 and a BFP-related entry. These A/B reagent-mixture labels must not automatically be equated with the A/B acquisition suffixes.
- The photograph alone does not establish exact AC/INAC clone sequences, lengths, mixing basis, per-well amounts, culture, treatment or harvest interval. User confirmation below establishes mass basis and the 15% correction.

## S10 photograph

Source: `inputs/S10/IMG_1693.HEIC` (readable rendering: `inventory/S10_record.png`).

- A blue `(x2)` annotation is visible above an E0–5 series.
- The reporter row shows 200 for the early columns and a continuation line. The BFP-labelled row reads 0, 100, 200, 400, 800, 1600; a balancing E row is consistent with 1800, 1700, 1600, 1400, 1000, 200 (some digits are less clear).
- A lower preparation entry refers to RepOpenA. The photograph is consistent with, but does not alone establish, a two-well preparation using 100 ng reporter per well and total 1,000 ng DNA per well. The user subsequently confirmed this per-well interpretation; editor doses are now derived from the recorded ratios (see below).
- Physical ORCA–P2A–BFP linkage and the exact editor construct are not demonstrated by the photograph. No sequence-verified linked editor record was found in the authorized S7/S10 directories.

## Workbooks

- `inputs/S10/酶标仪/孔图备注.xlsx`, Sheet1 B13:E15, documents the EDIT plate labels 1:0-a/b through 1:8-a/b. The workbook also contains S8 AC entries; those experimental measurements are outside the scope. Only the EDIT block is used.
- The same workbook B18 identifies PBS at A01. Other wells of the blank scan are not assumed to be PBS controls.
- `inputs/S10/523RepEdit.xlsx`, Sheet1 B13:C14, provides OpenA1-edit523 F/R primer names and exact sequences. The template date is not accepted as an experiment date.
- `inputs/S10/测序/s9 edit 编辑率测序.xlsx`, Sheet1 B11:B34, lists 24 labels, four at each ratio, and names unpurified PCR products. Its S9 filename and template date conflict with S10 placement. The primer footer lists unrelated PUF names, so it is not accepted as proof of the primers actually used.
- The vendor result workbook `26I2618422443_SZ8648.xlsx`, sheet1, links each molecular label to forward/reverse reads and records receipt on 2026-09-26. Raw AB1 run dates are independently audited. These dates do not establish RNA harvest time.
- `1-8-2.F` has a vendor double-peak note. It is retained in the audit; a mixed trace is not automatically a quantitative RNA-editing reference.

## Direct user confirmation, 2026-10-13

Exact replies: “123 都是，4 12 为 a，34 为 b”; after a focused clarification, “质量，是的，跑完流式提的 rna”. Question context is preserved in `config/user_confirmations.json`.

- S7 and S10 A/B are independent transfection wells under the same condition. Analysis IDs refer to these wells; physical plate positions and independent-culture relationships remain unknown.
- S7 source label 10 was actually 15% AC, mixed by DNA mass. Original IDs/files remain intact; the analysis coordinate is 15. No conversion to molar or intracellular RNA fraction is made.
- S10 reporter was 100 ng/well, total DNA 1,000 ng/well, and ORCA was linked to BFP through P2A. The recorded 1:x ratios imply editor amounts 0, 50, 100, 200, 400 and 800 ng/well. Remaining DNA amounts are arithmetic mass balances, not extra independent measurements of vector identity.
- Molecular labels 1/2 belong to A, 3/4 to B for each S10 condition. This direct confirmation resolves the S10 association despite the S9 form filename. Each parent well has two molecular labels; their extraction/RT/PCR/aliquot relationship remains unknown.
- RNA was extracted after flow at the same experimental time point. Exact elapsed minutes and the sampled cell population are unknown. RNA origin is reported by the user; absence of residual DNA in PCR products and quantitative molecular assay validity are not established by that statement.

The confirmation updates experiment metadata, not the visual transcription or raw source files. It does not establish exact clone sequence, single-color compensation, RNA target coordinates, DNase/no-RT outcomes or molecular editing fractions.
