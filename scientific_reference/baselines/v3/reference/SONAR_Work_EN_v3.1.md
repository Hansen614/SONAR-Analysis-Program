# SONAR — Complete Pipeline Design and Work Handoff

**Independent English specification**

| Field | Value |
| --- | --- |
| Documentation version | `SONAR-docs-v3.1 · work-edition` |
| Scientific design | `SONAR-v3-design`; estimator and D01–D12 unchanged |
| Date | 2026-09-19 |
| Status | Proposed implementation contract; empirical choices and validation remain open. |
| Normative language | English is authoritative. The separate Chinese translation preserves all equations, schema keys and IDs. |
| Companion | `SONAR_Measurement_EN_v3.1.md` |
| Primary source | `reporter_four_layer_framework_v2.md`, followed by the user's subsequent estimator and BFP design discussions. |
| Data-analysis status | No new FCS, construct-sequence or sequencing analysis is reported here. |

> **Implementation mandate.** Build an auditable four-layer pipeline from all supplied data, preserving the distinction between measurement, reporter calibration and molecular prediction. Complete every supported layer, but do not fabricate absent controls, calibration curves, validation metrics or sequence facts. “Complete software” may legitimately return “not calibrated” for an unsupported biological output.

> **v3.1 documentation change.** This is the standalone English edition of the existing v3 implementation specification. Sections 0–23 retain its scientific design; file names, language packaging and Measurement publication links are updated. Section 24 adds the evidence-export interface for the revised Measurement page, based on the public official award aspects checked on 2026-09-19. This is not a new empirical freeze or a change to the estimator. The corresponding Chinese file is `SONAR_Work_ZH_v3.1.md`.

## Reading map

| Sections | Purpose |
| --- | --- |
| 0–3 | Revision history, scientific target, notation, inputs |
| 4–5 | Preprocessing and Layer −1 |
| 6–8 | Layer 1, population aggregation and BFP |
| 9–12 | AC/INAC calibration and molecular prediction |
| 13–15 | Uncertainty, QC and validation design |
| 16–20 | Interfaces, execution, tests, outputs, decisions |
| 21–23 | Handoff prompt, configuration template, references |
| 24 | Measurement-page evidence exports and publication checks |

---

## 0. Revision contract: what this version preserves and replaces

The four-layer architecture and names remain unchanged: **Context Calibration → Flow Quantification → Reporter Calibration → Biological Calibration**, with outputs **context parameters → RAS → RES → PER**. The original separation of stronger versus weaker claims remains fundamental.

The discussions after v2 changed the measurement target. Therefore, this document is a declared reconstruction, not a silent extension of every earlier formula. Its primary proposed RAS is the **ratio of background-corrected linear green and red sums in a declared population**. It is no longer AF, mean green excess, or a capped green-only mean. Validation must establish the usable domain of this estimator; it must not merely select whichever formula produces the desired PUF ranking.

| Earlier proposal | v3 resolution |
| --- | --- |
| mCherry is mainly a positivity gate | Gate **and continuous internal reference** |
| RAS = GFP-positive fraction | AF is retained as supporting information |
| Mean/capped GFP excess is the main score | Replaced by linear corrected ratio of sums |
| All calculations should use transformed values | Gates/plots may use transforms; sums and ratios use linear signal |
| Mock quantiles alone establish all three positive gates | Quantiles are candidates; validate optical panel and negative spreading |
| All samples must pass BFP+ | Explicit reporter-population and co-expression modes |
| Add active ORCA to AC/INAC without further checks | First establish reference-state integrity and transferability |
| AC DNA fraction equals true edited RNA fraction | Distinguish nominal DNA, cell-mixture and measured RNA axes |
| Sanger is error-free ground truth | Independently estimated reference with assay uncertainty |
| One biological curve predicts all targets | Target-, population- and domain-specific validation |

Statements below are either **design decisions**, **mathematical consequences under stated assumptions**, or **pending empirical decisions**. The IDs `D01`–`D12` identify the latter. Nothing in the document establishes that a specific old batch passed QC or that one reporter is better than another.

---

## 1. Define the scientific quantity before implementing an estimator

### 1.1 Three channels with non-interchangeable roles

Let $R$, $G$ and $B$ denote mCherry, EGFP and BFP fluorescence. mCherry marks reporter expression and provides a continuous internal reference. EGFP is the editing-associated output. In a verified ORCA–P2A–BFP construct, BFP marks detectable editor-linked expression and provides an expression covariate. It is not a second reference to divide out automatically.

The intended ecDHFR-DD switch is a low-to-high readout. Establish the exact edited/unedited linkage from the final sequences before drawing a codon-level mechanism or assuming which translation product carries DD. TMP-dependent DD stabilization is not itself evidence of RNA editing. The DD literature supports the general stability mechanism, not this team's exact sequence.[^R1]

### 1.2 Same transcript is an advantage, not a complete calibration

A shared reporter transcript motivates red normalization because a common expression component may affect both channels. It does not establish identical maturation, degradation or steady-state protein abundance. Similarly, 2A-mediated protein separation does not establish that BFP is an exact concentration meter for active ORCA.[^R2] These are testable approximation limits, not reasons to discard the internal reference.

Reporter abundance can also affect the biology, for example by changing the editor-to-substrate relationship. The pipeline should remove a common optical/expression scale where justified, not force reporter-dose invariance if changing reporter dose actually changes activation. Separate normalization checks on locked reference states from mechanistic tests on genuinely edited reporters. **[D01, D12]**

### 1.3 Declare the estimand

| Output | Intended quantity | Not equivalent to |
| --- | --- | --- |
| Context package | Measurement definitions and background estimates | A reporter score |
| RAS | Green output per unit red reference in a declared population | Edited-cell fraction or directly counted edited RNA |
| RES | Input-equivalent active-reference fraction under a validated reporter calibration | Universal editing percentage |
| PER | Predicted RNA-editing fraction for a named endpoint and population | A direct sequencing measurement or a universal property of an editor |

“Rate” in PER means fraction at the sampling time, not a kinetic rate. The central intended benefit is interpretable reporter-based comparison; predicting endogenous editing is a separately validated extension. Higher RAS in an observed population and higher response at matched BFP expression are different findings. Preserve both without relabeling either as universally superior editing.

---

## 2. Notation, population identities and context objects

| Symbol | Definition |
| --- | --- |
| $s,i$ | Sample and event index |
| $c\in\{G,R,B\}$ | Green, red and blue channels |
| $X_{c,i}$ | Linear, compensated channel intensity |
| $x^t_{c,i}=\psi_c(X_{c,i})$ | Display/gating transform |
| $\widehat b_{c,i}$ | Estimated expected additive background in linear units |
| $g_i,r_i,b_i$ | Corrected linear EGFP, mCherry and BFP |
| $T_c$ | Validated fluorescence-positivity boundary in a declared space |
| $\mathcal V_s$ | Quality-screened reference-gated cells |
| $R_{\rm det}^+$ | Detectably red-positive events |
| $R_{\rm q}^+$ | Red-positive events also meeting reference-quantification requirements |
| $\mathcal P_R,\mathcal P_{RB}$ | Reporter-population and co-expression analysis populations |
| $m$ | Population/standardization mode, not an experimental treatment |
| $d$ | Calibration domain identity |
| $t,\tau$ | Molecular target identity and sampling time, respectively |
| $A$ | Calibration reference-mixture input with explicit basis |
| $g_{m,d}(A),h_{t,m,d}$ | Reporter response curve and biological prediction function |

To avoid confusing BFP with “background,” use $\widehat b_c$ for linear backgrounds and $m_c^t,s_c^t$ for transformed Mock center/scale. Do not reuse the old symbol $B_G$ for both a transformed median and a linear subtraction constant.

The strict Mock-derived object remains $\Theta_{\mathrm{mock}}$. Panel-specific controls and preprocessing provenance enter separately as $\Theta_{\mathrm{panel}}$ and the profile record. Their combined Layer −1 output is:

$$
\Omega_{\mathrm{context}}=
\{\Theta_{\mathrm{mock}},\Theta_{\mathrm{panel}},\mathrm{preprocessing\ profile},
\mathrm{compatibility\ rules},\mathrm{QC},\mathrm{versions}\}.
$$

This is an explicit interface extension, not a claim that Mock alone supplies compensation or all multicolor thresholds. It preserves four layers; preprocessing is a prerequisite, not an invented fifth scientific score.

---

## 3. Required input data and provenance

### 3.1 Inventory before analysis

Read all supplied manifests, raw files, construct records and laboratory notes before assigning analysis roles. Preserve raw data unchanged and hash every input. Resolve duplicate exports, multiple acquisitions of the same well, corrected sample labels and changed instrument settings. Do not infer biological replication from a filename suffix or infer compensation merely from the word “compensated.” Conflicts become entries in a reconciliation report. **[D11]**

No numeric conclusion from an earlier chat summary substitutes for the underlying FCS/log. Historical doses, dilution corrections and preferred reporter designs are hypotheses or provenance leads until verified against the supplied records.

### 3.2 Sample manifest

Use one row per acquisition, with a separate biological sample ID. Fields may be null when genuinely unavailable, but missingness must remain explicit. Units are mandatory for numeric laboratory quantities.

| Field group | Required schema keys |
| --- | --- |
| Identity | `sample_id`, `acquisition_id`, `file_path`, `sha256`, `source_record` |
| Replication | `biological_batch_id`, `culture_id`, `plate_id`, `well_id`, `biological_replicate_id`, `technical_parent_id` |
| Role | `sample_role`, `reporter_id`, `editor_id`, `editor_bfp_linked`, `target_id` |
| Context | `cell_type`, `culture_condition_id`, `panel_id`, `instrument_id`, `acquisition_session_id`, `instrument_profile_id` |
| Controls | `mock_id`, `compensation_control_set_id`, `channel_negative_control_set_id`, `reference_bead_id` |
| Treatment | `reporter_dna_amount`, `editor_dna_amount`, `total_dna_amount`, their units; `transfection_condition_id`, `tmp_condition_id`, `sampling_time`, `acquisition_time` |
| Analysis | `requested_population_modes`, `domain_id`, `calibration_set_id`, `pair_id`, `split_id`, `exclusion_reason` |

A blank `editor_bfp_linked` is unknown, not false. BFP detected in a sample does not prove it is ORCA-linked without construct metadata. `sample_role` distinguishes Mock, single-color, channel-negative, AC, INAC, mixture, reporter-only WT, tagged-editor sample, untagged-editor sample and RNA-paired sample; roles may overlap when explicitly valid.

### 3.3 Supporting registries

| Registry | Required information |
| --- | --- |
| Construct registry | Exact sequences/maps, sequence hashes, transcript organization, fluorophore identities, editor linkage, editable site, AC/INAC state definitions and evidence of locked behavior |
| Panel registry | Verified channel names and aliases, area/height identity, detector ranges, optical settings, compensation matrix orientation/state, transform definitions |
| Mixture table | `mixture_id`, masses, lengths, amounts/units, nominal fraction, `fraction_basis`, `mixture_process`, uncertainty, total reporter amount |
| RNA-reference table | Raw AB1/reads, reference sequence, target type/locus/strand, edited base, method/version, estimate and uncertainty, assay QC, sampling population, paired sample IDs |
| Split registry | Development/calibration/validation roles and grouping keys fixed before outcome-driven tuning |

### 3.4 Controls answer different questions

| Control | Purpose | Must not be used to claim |
| --- | --- | --- |
| Matched nonfluorescent Mock | Cell/instrument background and population reference | Reporter leak is zero |
| Single-color controls | Optical spillover correction | Full multicolor negative spread is absent |
| Channel-negative/FMO-style controls | Negative distribution in the presence of other fluorophores | Molecularly unedited reporter behavior |
| INAC and AC | Reporter response endpoints and mixture calibration | Intracellular RNA proportions without measurement |
| Reporter-only/no active editor | Biological leak/context comparison | A universally transferable calibration |
| Independent RNA reference | Molecular endpoint calibration | Error-free truth |

In this fluorescent-protein system, a channel-negative control must be designed and documented; it is not literally an omitted antibody stain. The use of FMO-style logic is a proposed adaptation of established multicolor-control practice.[^R3] A no-green-expression optical control and an INAC reporter with possible green leak are not automatically interchangeable.

---

## 4. Preprocessing: preserve the meaning of fluorescence units

### 4.1 Validate FCS semantics before touching the gates

Inspect the actual FCS parameter names/descriptions, data type, acquisition range, gain/log encoding, compensation keywords and acquisition metadata. Map EGFP, mCherry and BFP by verified detector identity rather than color-name guessing. Use a validated area measurement for quantitative fluorescence. A height or width channel is not an interchangeable substitute. Check the instrument's meaning of BSC/SSC before mapping the scatter variable.

Decode the file's native numerical representation into the intended linear measurement scale before compensation and quantitative aggregation. Native decoding/linearization is distinct from a later visualization transform. Record what the reader library has already done. If FlowKit is selected, its documented event sources and defaults must be handled explicitly: transformed events are not the quantitative default intended by this specification.[^R6] Verify the installed API rather than assuming a historical call signature. **[D02]**

### 4.2 Compensate exactly once

Maintain a state machine: `uncompensated → compensated_linear → display_transformed`. An already compensated export enters at the second state, provided its provenance is verified. A stored spillover matrix does not by itself establish whether compensation has already been applied. Validate matrix labels, orientation and channel ordering using controls and recorded software behavior.[^R4]

Do not estimate a compensation matrix from Mock covariance, from an experimental green–blue trend, or from the desired separation between groups. Preserve signed compensated values. If a spectral instrument is used, an independently validated unmixing workflow replaces the corresponding optical step; do not invent an unmixing model from these three channels alone.

### 4.3 Preserve three representations

| Representation | Purpose |
| --- | --- |
| Immutable original | Provenance and reprocessing |
| Linear compensated | Background correction, sums, ratios and quantitative diagnostics |
| Display/gating transformed | Logicle/arcsinh plots and validated gate construction |

Never compute the primary RAS from $\sum\psi(G)/\sum\psi(R)$, $G^*/R^*$, median-channel ratios, or the plotted subset. A positive rescaling applied separately to red and green changes RAS unless the corresponding calibration is updated. Mock subtraction alone cannot harmonize different detector gains.

### 4.4 Acquisition-quality checks

Detect malformed events, nonfinite values, acquisition discontinuities and obvious flow instability using a frozen rule. Time-quality filtering is applied **per file**: do not copy the Mock's absolute acquisition-time intervals into every sample. Record masks and exclusion reasons. If time is unavailable, report that limitation.

Inspect raw-range clipping and transformed plateaus separately. `$PnR` or the observed maximum is not automatically the true saturation boundary after preprocessing. Establish the usable range from file semantics and control evidence. A sample with substantial clipped signal is censored; deleting its brightest cells does not reconstruct the missing fluorescence. **[D03, D05]**

---

## 5. Layer −1 — Context Calibration

### 5.1 Match context, not merely the experiment date

A context profile identifies the cell type/state, culture/transfection handling, treatment and sampling timeline, instrument settings, fluorescence panel and control set. One acquisition day can contain multiple incompatible contexts. Conversely, several sessions may share a validated profile only when optical and biological transfer has been demonstrated.

The control package may contain more than one Mock or channel-negative replicate. Do not pool incompatible backgrounds merely to increase event counts. Specify which negative population models each sample. Use blinded control-only selection for gates; experimental labels and desired outcomes must not influence it.

### 5.2 Reference population gates

Build an intact-cell gate from a validated scatter population and a singlet gate from suitable pulse geometry. Compare a small preregistered candidate set on development controls: a reviewed density contour, robust covariance contour, or validated clustering model for cells; a robust pulse-geometry residual or density contour for singlets. The highest-density or largest cluster is not automatically intact cells—debris can dominate a poor preparation.

A control-derived gate may require a blinded human review before acceptance. Once accepted, apply the same reference gate within its context; store its coordinates, transform, algorithm parameters and approval history. A low experimental retention rate triggers review/QC, not a favorable sample-specific redraw. A legitimately revised gate creates a new version and requires reprocessing all affected controls and samples. **[D03]**

$$
\mathcal V_s=
\mathcal Q_{\mathrm{time},s}\cap\mathcal G_{\mathrm{cell},d}
\cap\mathcal G_{\mathrm{singlet},d}
\cap\mathcal G_{\mathrm{viability},d}\quad\text{when viability is measured}.
$$

Without a viability marker, omit the viability term and describe the result as scatter-selected singlets, not confirmed live cells. Without pulse geometry, report `singlet_exclusion_unavailable`; this may permit a limited analysis mode but cannot be silently equivalent to a validated singlet pipeline. Do not hardcode 98–99% coverage as a universally correct biological gate.

### 5.3 Descriptive background versus additive correction

For each channel

$$
m_c^t=\operatorname{median}\{\psi_c(X_{c,i}):i\in\mathcal V_{\rm mock}\},
\qquad
s_c^t=1.4826\operatorname{MAD}\{\psi_c(X_{c,i})\}.
$$

These transformed center/scale quantities describe negative distributions and support plots, threshold diagnostics and drift checks. The factor 1.4826 is a conventional normal-consistency scaling of MAD, not evidence that the distribution is Gaussian. A zero/tiny MAD is flagged; do not create enormous z-scores by dividing by it.

The additive baseline used in RAS is a **separate linear-space estimate of expected background**:

$$
\widehat b_{c,i}=\widehat{\mathbb E}\!
\left[X_c\mid U_i,\ \text{matched negative context}\right].
$$

Start with a constant mean from quality-screened matched negative cells when its validity is supported. Evaluate a low-complexity conditional mean using scatter or other non-response covariates only if there is enough negative-control support. Compare residual mean, variance, stability and out-of-support behavior on independent negative replicates. A robust median remains useful descriptively, but subtracting it does not guarantee that a summed negative population has mean zero. **[D04]**

Do not regress experimental EGFP against BFP and call the residual “background”: that can remove the biological response being studied. Likewise, do not extrapolate a Mock-derived EGFP-versus-red background relation into the bright reporter region unsupported by Mock. Optical mean spillover belongs to compensation; fluorescence-dependent negative spreading still needs panel validation.

### 5.4 Positivity and quantifiability are different decisions

A candidate Mock rule is

$$
T_c^{\rm mock}=Q_{p_c}(X_{c,\rm mock}),\qquad
p_c\in\{0.99,0.995,0.999\}\ \text{as development candidates only}.
$$

The listed quantiles are candidates, not selected defaults. Fix the quantile convention and the space where it is estimated. Monotonic transforms preserve ordering, but interpolation conventions can produce slightly different numeric quantiles; store the implemented threshold explicitly.

Use matched channel-negative controls to determine whether a constant boundary is adequate or an expression-dependent negative envelope is required. Any conditional boundary must be learned from controls with relevant expression support, declared in the panel profile, and used identically for calibration and tests. Do not adjust it after viewing candidate performance. FMO-style control use is distinct from subtracting an INAC biological baseline.[^R3]

$$
R_{\rm det}^+=\{R>T_R\},\qquad
R_{\rm q}^+=R_{\rm det}^+\cap\{r>r_{\min},\ \text{reference in quantifiable range}\}.
$$

The extra quantification margin $r_{\min}$ is a versioned, data-validated requirement, not an arbitrary ratio-stabilizing constant added to every denominator. It ensures that retained red weights are positive and sufficiently informative. Positivity alone may admit a population whose summed reference is too uncertain for a useful ratio. Report detection and quantitative-selection losses separately. **[D04–D05]**

### 5.5 Independent QC and uncertainty

A sample's fraction above its own fitted quantile will be approximately $1-p$ by construction. This checks software consistency; it does not independently validate a false-positive rate. Use separately acquired or held-out negative controls, with enough tail events, to evaluate transfer. Bootstrap or repeat negative controls to quantify uncertainty in thresholds and background estimates.

Record three-channel covariance/correlation as descriptive diagnostics, never as compensation coefficients. Track gain/profile compatibility, negative residual distributions, tail behavior, gate retention, event counts and control outliers. A Mock cannot provide a meaningful reporter ratio merely because its red upper tail contains a few “positive” events.

### 5.6 Layer −1 output

```text
ContextResult
  context_id; domain/profile compatibility; status; reasons
  theta_mock
    control_ids; control_hashes; event masks; counts
    cell_gate; singlet_gate; viability availability
    transformed median/MAD and 3-channel descriptive covariance
    linear background model; support; uncertainty
    candidate/final Mock thresholds; estimation convention
  theta_panel
    channel map; compensation provenance/state
    single-color diagnostics; channel-negative validation
    final positivity policies; support and uncertainty
  preprocessing_profile; transforms; quantifiable ranges
  locked algorithm/config/version hashes; review record
```

The pure function estimating $\Theta_{\rm mock}$ takes Mock data and configuration only. The context assembler can additionally read declared optical controls and metadata. Neither uses held-out biological outcomes to select gates. **[D02–D05]**

---

## 6. Layer 1 — declare and preserve the analysis population

### 6.1 Two supported modes, not one compulsory blue gate

$$
\mathcal P_{R,s}=\mathcal V_s\cap R_{\rm q}^+,
\qquad
\mathcal P_{RB,s}=\mathcal V_s\cap R_{\rm q}^+\cap B^+.
$$

| Mode ID | Population | Intended question |
| --- | --- | --- |
| `reporter_population` | $\mathcal P_R$ | Reporter-normalized response across quantifiable reporter-expressing cells |
| `coexpression` | $\mathcal P_{RB}$ | Response conditional on detectable reporter and editor-linked expression |

In concise Wiki notation, $R^+$ means the validated reporter-positive analysis region; Work must retain the distinction between $R_{\rm det}^+$ and $R_{\rm q}^+$. For verified BFP-linked editor samples, output both modes when possible. `coexpression` is the primary conditional activity view; `reporter_population` preserves the effect of incomplete co-expression and supports legacy reporter-only analyses.

No-BFP AC/INAC data are processed in reporter-population mode. A missing BFP channel is not a BFP-negative measurement. A detected BFP signal from an unlinked plasmid is not automatically an ORCA-linked co-expression measurement. Absent or unverified linkage yields an explicit mode restriction. **[D06]**

### 6.2 Same numerical kernel, metadata-aware routing

The RAS kernel is outcome-blind, but it legitimately accepts a declared population policy and verified context. Sample type, marker presence and acquisition profile cannot be ignored merely to keep the interface artificially limited to two file arguments. The router determines which policies are valid; the kernel applies the same formula to every eligible sample under that policy.

Do not force AC/INAC through a nonexistent blue-positive gate. Do not silently switch an unknown sample from co-expression to reporter-population mode and reuse the same calibration ID. The two modes can share an estimator implementation while requiring different calibration identities.

### 6.3 Preserve the below-BFP-threshold population

$\mathcal P_{RB^-}=\mathcal P_R\cap B^-$ can be reported as an internal descriptive comparison. It is **below the BFP detection boundary**, not proven devoid of ORCA. BFP/ORCA differences in kinetics and detection limit prevent it from replacing an explicit editor-negative control. Neither $G^+$ nor $B^+$ establishes molecular editing by itself.

The order of red and blue gates does not change the final intersection when the boundaries are fixed. Their displayed order may follow reporter → editor → response for readability. EGFP positivity is not an eligibility requirement for the main score.

---

## 7. Layer 1 — from paired single-cell fluorescence to population RAS

### 7.1 Primary proposed estimator

For every event in the declared population

$$
g_i=G_i-\widehat b_{G,i},\qquad
r_i=R_i-\widehat b_{R,i},\qquad
b_i=B_i-\widehat b_{B,i}.
$$

For sample $s$ and mode $m$

$$
\boxed{
\operatorname{RAS}_{s,m}
=\frac{\sum_{i\in\mathcal P_{s,m}}g_i}{\sum_{i\in\mathcal P_{s,m}}r_i}
=\frac{\overline g_{s,m}}{\overline r_{s,m}}.
}
$$

**Estimator ID** `ras-linear-ratio-of-sums-v3-design`.

Both sums use exactly the same events. Use all retained events and double-precision accumulation, not the plot subsample. Preserve signed corrected green values; do not subtract a green positivity threshold, discard GFP-negative events, rectify each event at zero, or cap green intensity alone. Those operations create different estimands and can bias a low-signal average upward.

Require a positive, sufficiently precise red denominator. If it fails, return `NOT_ESTIMABLE`, with sums and uncertainty retained; do not add an arbitrary epsilon or report zero. A slightly negative RAS near background is possible as a noisy measurement. Its biological interpretation depends on uncertainty and the INAC calibration, not automatic clipping.

### 7.2 Why ratio of sums is not mean of ratios

When retained $r_i>0$

$$
w_i=\frac{r_i}{\sum_j r_j},\qquad
\operatorname{RAS}=\sum_i w_i\frac{g_i}{r_i}.
$$

RAS is a red-reference-weighted mean of per-cell ratios. A very weak-red cell does not receive the same weight as a strong-red cell, avoiding the particular instability of giving all low-denominator ratios equal weight. This is not proof that all outliers are harmless; high-red events may dominate.

Under the idealized assumptions $r_i=k_R n_i$ and $g_i=k_Gn_i a_i$:

$$
\operatorname{RAS}=\frac{k_G}{k_R}
\frac{\sum_i n_i a_i}{\sum_i n_i}.
$$

This motivates a reporter-abundance-weighted activation interpretation. In real data, $n_i$ is not directly counted, $a_i$ need not be an RNA-editing fraction, and accumulated protein signal integrates expression history. The approximation must be evaluated, not promoted to a literal molecular counting equation. **[D12]**

### 7.3 Invariance and limits

Duplicating every event leaves RAS unchanged. Multiplying corrected red and green by the same positive factor also leaves it unchanged. Multiplying only green by a gain factor does not. Thus the formula removes acquisition-count dependence and a common proportional scale under stated conditions; it does not automatically remove independent detector changes, differential fluorophore kinetics, heterogeneous substrate loading or selection bias.

Report a same-condition replicate's RAS at the well level. Do not pool all events from replicate wells and use their event count as biological $n$. Pooling weights wells by total reference output and changes the comparison. Technical reacquisitions may be merged only under an explicit same-sample rule, retaining their acquisition QC.

### 7.4 Influence, effective support and denominator precision

$$
N_{\rm eff,R}=\frac{1}{\sum_i w_i^2}
=\frac{(\sum_i r_i)^2}{\sum_i r_i^2},
\qquad
\operatorname{RAS}_{-i}=\frac{\sum_j g_j-g_i}{\sum_j r_j-r_i}.
$$

Report selected $N$, $N_{\rm eff,R}$, maximum red weight, the red contribution of a prespecified upper-tail subset, and a leave-one-out or influence approximation. These diagnose concentration of information; $N_{\rm eff,R}$ is not a replacement for independent biological replication. Determine count, denominator and influence limits using precision goals and empirical controls. **[D05]**

Do not remove genuine bright cells just because they change the score. Distinguish acquisition artifacts from biologically high expression. Use robust alternatives as sensitivity analyses. If a revised robust estimator is needed, specify a joint weighting/selection rule, acknowledge the altered estimand, assign a new estimator version, and refit dependent calibration models. Do not silently winsorize each sample at its own outcome-dependent quantile.

### 7.5 Supporting metrics

$$
AF_m=\frac{\#\{i\in\mathcal P_m:G_i>T_G\}}{|\mathcal P_m|},
\qquad
AM_m=\operatorname{median}\{g_i:i\in\mathcal P_m\}.
$$

Store an optional $AM_{G^+}$ separately with its own denominator. AF describes threshold-positive prevalence; AM describes fluorescence magnitude. Neither is itself an editing fraction. The previous identity “RAS = AF × AM” does **not** apply to this final ratio-of-sums RAS and this median-based AM.

Also report pure detection fractions $P(R_{\rm det}^+\mid\mathcal V)$ and $P(B^+\mid\mathcal V)$; co-expression $CEF_{\rm det}=P(B^+\mid R_{\rm det}^+,\mathcal V)$; quantitative co-expression $CEF_{\rm q}=|\mathcal P_{RB}|/|\mathcal P_R|$; per-gate counts; all eight binary fluorescence combinations; channel distributions; saturation and compensation diagnostics. Keep denominator labels on every percentage.

### 7.6 Relation between the two population modes

For disjoint B-positive and B-negative parts of the same $\mathcal P_R$

$$
W_B^R=\frac{\sum_{i\in\mathcal P_{RB}}r_i}{\sum_{i\in\mathcal P_R}r_i},
\qquad
\operatorname{RAS}_R=W_B^R\operatorname{RAS}_{RB}
+(1-W_B^R)\operatorname{RAS}_{RB^-}.
$$

This is an exact aggregation identity when the two component ratios are defined. The weight is the **red-reference share**, not the cell-count co-expression fraction. It explains why incomplete co-expression can affect the reporter-population score without proving that this score is “wrong.” It also shows why multiplying a gated editing prediction by CEF is not a valid generic conversion to bulk RNA editing.

---

## 8. BFP as a continuous covariate and comparison tool

### 8.1 Preserve both experimental performance and expression-matched comparison

The observed co-expression RAS describes the selected population as acquired. Differences in BFP distributions may be part of construct expression performance. A separate expression-matched analysis asks whether response differs at comparable editor-linked expression. Do not discard the first result or call the second an intrinsic catalytic constant.

BFP maturation/stability, the P2A architecture, ORCA integrity and sampling time can affect the proxy. Compare tagged and untagged editor function where data exist, and check that blue intensity is informative over the intended range. Optical blue-to-green artifacts must be ruled out with independent controls before interpreting a blue–response trend. **[D01, D02, D08]**

### 8.2 Shared-bin profiles

Define shared BFP intensity bins within a compatible calibrated/profile scale; optionally use joint red–blue bins to control reporter-expression differences too. Boundaries come from prespecified reference/development data, not each test sample's own quantiles. “Low” in two groups must refer to the same range. Report counts, sums, RAS and intervals in each bin, and mark bins without sufficient support.

A within-well BFP association is observational. Co-transfection, cell state and expression history may vary along the same axis. A stronger causal dose claim requires an independently controlled dose design; the pipeline must not manufacture it from bin labels.

### 8.3 Optional reference-population standardization

Let $\pi_k^*$ be a fixed reference **cell-population** proportion in shared bins

$$
\pi_k^*\ge0,\quad\sum_k\pi_k^*=1,
\qquad
\boxed{
\operatorname{RAS}_{\rm std,s}
=\frac{\sum_k\pi_k^*\,\overline g_{s,k}}
{\sum_k\pi_k^*\,\overline r_{s,k}}.
}
$$

This computes the ratio of expected green and red signals under a common reference cell distribution. It is generally **not** $\sum_k\pi_k^*RAS_{s,k}$. The latter instead requires a declared reference-red-mass weighting interpretation. Preserve `standardization_id`, bin definitions, reference weights and support requirements. Do not silently renormalize weights differently for each group when a bin is missing; restrict a prespecified common support or return `INSUFFICIENT_SUPPORT`.

A standardized RAS needs a calibration fitted or validated under that same standardization. Applying a nonlinear inverse before averaging is not generally equivalent to averaging first and then inverting. Keep observed-population and standardized outputs separately named. **[D08]**

---

## 9. Layer 2 — define a valid AC/INAC calibration experiment

### 9.1 Verify what AC and INAC actually encode

Read the final sequences and define the active and inactive reference states operationally and molecularly. Establish whether INAC is uneditable by the experimental editor and whether AC remains an active reference under that treatment. A WT-like editable negative is not a locked INAC merely because it was called “inactive” in a filename. Reference integrity is particularly important before adding active ORCA–P2A–BFP to a calibration. **[D01, D06]**

### 9.2 The calibration axis must name its basis

For co-transfected DNA mixtures

$$
A_{\rm DNA}=
\frac{m_{AC}/L_{AC}}{m_{AC}/L_{AC}+m_{INAC}/L_{INAC}}.
$$

$m$ is DNA mass and $L$ is plasmid length. This is the nominal molar input fraction; equal mass is equal molar input only for equal lengths. Store actual quantities, uncertainty and dilution provenance. Use a measured RNA-state fraction as a different calibration axis only when available and validated.

DNA input fraction does not automatically equal intracellular transcript fraction. Differential uptake, transcription, RNA stability and population selection may change it. Mixtures made by co-transfecting plasmids, by mixing separately transfected cells, and by measuring RNA fractions are different calibration designs. Store both `fraction_basis` and `mixture_process`; do not pool them under an unlabeled “% editing” axis. **[D07]**

### 9.3 Domain and mode matching

A calibration domain records reporter architecture, reference-state identities, cell type, reporter/total DNA loading, editor background, treatment including TMP, sampling timeline, optical profile, population mode and standardization. Not every field must be fixed forever, but any permitted variation must be supported by data and encoded as a validated domain or covariate.

Changing WT/OpenA/OpenB architecture, reporter dose, or marker status is not automatically absorbed by a single AC/INAC curve. First fit domain-specific curves or establish an explicit bridge. Similar endpoint values alone do not prove identical interior response. **[D06–D07, D12]**

### 9.4 Retain legacy data without claiming an untested bridge

| Available calibration | Supported path |
| --- | --- |
| AC/INAC without BFP | Directly develop `reporter_population` calibration |
| Locked AC/INAC with same tagged editor context | Co-expression calibration if state integrity and context match are verified |
| AC/INAC plus inactive ORCA–BFP or BFP alone | Optical/selection matching candidate; biological transfer still requires a bridge |
| Demonstrated mode/context invariance | Share or transfer a model only over the validated range |

Legacy no-editor AC/INAC data are not automatically worthless and are not automatically the final co-expression calibration. Keep them, process them with the corrected RAS, and determine their supported use. The user's actual mixture records must control the analysis, not prior verbal assumptions about how those mixtures were made.

---

## 10. Layer 2 — fit, invert and validate the reporter response

### 10.1 Fit on independent sample summaries

$$
RAS_{j,m}=g_{m,d}(A_j)+\varepsilon_j,
\qquad
RES_{s,m}=g_{m,d}^{-1}(RAS_{s,m})\ \text{where identifiable}.
$$

Each calibration well/biological sample contributes its RAS and uncertainty. Multiple cytometry events do not create independent mixture levels or biological replicates. Preserve between-well and between-batch variation, and uncertainty in $A$ when meaningful.

Use a prespecified simple model hierarchy: an affine response with positive slope where supported; otherwise a monotone piecewise/shape-constrained response; a more parameterized saturation model only if the number and distribution of calibration points justify it. Compare out-of-sample prediction, residuals, stability and inverse precision, not fit $R^2$ alone. Do not force monotonicity over a genuine reproducible decline merely to obtain an inverse. **[D07]**

### 10.2 Meaning of RES

RES is the input-equivalent reference activity under the stored calibration axis. With a DNA-based curve, RES = 0.70 means that the sample's response corresponds to a nominal AC molar input fraction of approximately 0.70 under those conditions. It is not automatically 70% of the green/red response range, 70% activated cells, 70% edited reporter RNA, or 70% endogenous editing.

Only for an affine two-endpoint model does ordinary endpoint normalization have the same meaning:

$$
RES=\frac{RAS-g(0)}{g(1)-g(0)}\qquad\text{only if }g\text{ is affine}.
$$

### 10.3 Identifiability and reporting rules

Define the supported input range, output range and local inverse precision. On a plateau, several $A$ values may produce indistinguishable RAS. Return an identified interval/set or `NONIDENTIFIABLE`; do not choose an arbitrary single value. Report out-of-range measurements as `OUT_OF_CALIBRATION_RANGE` with their original RAS. Do not silently extrapolate, clip to endpoints, or label values above one as “over 100% editing.”

For a smooth local model, $SE(RES)\approx SE(RAS)/|g'(RES)|$ illustrates why inverse uncertainty expands near a flat response. Use resampling/model uncertainty for final intervals rather than relying on this approximation alone.

### 10.4 Validate the reference-mixture surrogate

A synthetic AC/INAC ladder may differ from a genuinely edited WT reporter in intracellular state distribution, transcript stability and expression history. Test surrogate transfer using genuine edited reporter samples with independent reporter-RNA measurements when available. Fit quality on the ladder does not itself establish that transfer.

Layer 2 estimates a composite response. It does not separately identify and remove each DD, P2A or maturation mechanism, and it cannot reconstruct information lost to clipping or a flat curve. Applying one strictly increasing $g^{-1}$ preserves the original RAS order; that ranking preservation is mathematics, not independent proof that the order reflects RNA editing. Comparisons across different calibrated domains require additional commensurability evidence. **[D07, D12]**

### 10.5 Calibration object

```text
ReporterCalibrationModel
  calibration_id; estimator_id; population_mode; standardization_id
  domain_id; allowed_contexts; reference_state_ids; sequence_hashes
  fraction_basis; mixture_process; input_units
  training_sample_ids; split_id; model_family; parameters
  input_support; output_support; inverse_policy; identifiable_intervals
  uncertainty_model; bootstrap/version record
  held-out diagnostics; surrogate-transfer evidence; limitations
  status; model_hash; upstream_context/estimator fingerprints
```

---

## 11. Layer 3 — establish an independent, correctly paired RNA reference

### 11.1 Name the molecular endpoint

Each RNA reference must identify `target_type` as `reporter_rna`, `introduced_target_rna`, or `endogenous_target_rna`, with the actual transcript, locus, strand and edited position. A validated prediction of reporter-RNA editing is useful but must not be called endogenous APOE editing. Endogenous and introduced APOE may require an assay that distinguishes their sources.

Use $\widehat E_{\rm ref}$ for the independent estimated edited fraction. Reserve an unobserved “true fraction” for a latent scientific quantity, not the raw Sanger estimate. Keep values internally as fractions in $[0,1]$ when valid; attach an explicit unit to every imported percentage. **[D09]**

### 11.2 Sanger and sequencing input contract

Where Sanger is the reference, retain the raw AB1 traces, reference sequence, local alignment, trace direction, target base position, quality metrics, negative controls, analysis method/version and uncertainty. For C-to-U editing, interpret the corresponding cDNA base change in the correct orientation; do not read a reverse trace as though it were forward. Validate low-fraction detectability and quantification using appropriate known-reference mixtures. A simple peak-height ratio is a candidate assay calculation, not an automatically accurate universal percentage.

EditR is one available trace-quantification implementation; applicability to the supplied RNA-derived amplicons, chemistry and locus still needs validation.[^R5] Check that the assay reflects RNA rather than residual plasmid DNA, using the actual RNA preparation and relevant no-RT/control records. Reject or flag ambiguous alignment, poor trace quality, background polymorphism and source ambiguity. For amplicon sequencing, retain read counts and assay QC while distinguishing sequencing/PCR sampling from independent biological replication. **[D09]**

### 11.3 Pair population, time and biological replicate

Prefer a paired flow/RNA measurement from the same biological sample or explicitly matched aliquots, with a shared `pair_id`. Sister wells are an alternative design but contribute biological matching uncertainty and must be labeled accordingly. Record collection and processing times rather than assuming equal nominal post-transfection labels guarantee equivalence.

A conditional $R^+B^+$ score should preferably be paired with an RNA sample representing that same population, such as a documented population-matched collection. Account for the sampling procedure and delay when relevant. Whole-well RNA instead measures a bulk endpoint. It may be modeled from reporter-population/co-expression features only in a separately validated bulk prediction model, not silently relabeled as the gated fraction. **[D09]**

### 11.4 Why matched cells still need biological calibration

RAS weights cells by reporter-associated red output. An RNA assay weights them by the number of assayed target transcripts. Even for the same cells, these weights need not match. A bulk target also includes cells outside the reporter/editor gate. Consequently, neither red normalization nor multiplying a conditional prediction by a cell-count co-expression fraction establishes an exact endogenous editing fraction.

Layer 3 exists to learn the empirical relationship for a defined target and sampling scheme, and to quantify its limitations. Reporter expression, editor expression and reporter burden may affect that relationship; check rather than assume their effects vanish after Layer 2.

---

## 12. Layer 3 — fit and validate PER

### 12.1 Core prediction model

For paired sample $j$

$$
\widehat E_{{\rm ref},j}=h_{t,m,d}(RES_j)+\epsilon_j,
\qquad
\boxed{PER_{s,t,m}=100\,\widehat h_{t,m,d}(RES_{s,m})\%.}
$$

$h$ predicts a fraction, not a time derivative. Model identity includes target, population, sampling scheme, reporter/editor domain, assay and permitted expression range. A simple univariate RES model is the baseline hypothesis. If BFP, co-expression or other covariates are required, name it explicitly as a multivariable biological model, for example $h_{\rm bulk}(RES,CEF,\text{expression features})$. Do not secretly redefine RAS or RES to conceal the extra predictors.

Choose an interpretable bounded or domain-limited model whose complexity is supported by independent samples. A local affine relation can be adequate on a restricted range; a monotone or bounded nonlinear model requires evidence and validation. Do not force a rising curve if the actual measured endpoint shows reproducible nonmonotonicity. Reference measurement error belongs in the uncertainty model. **[D10]**

### 12.2 Validation must match the intended claim

| Claim | Relevant holdout |
| --- | --- |
| Interpolation within a dose ladder | Independent wells, with training/test separation |
| Transfer to another run | Held-out biological/acquisition batch |
| Compare new PUF/editor candidates | Held-out candidate/editor identity, not just more doses of the same editor |
| Predict another target | Held-out target/locus |
| Predict another cell type or reporter | Explicit independent domain-transfer validation |

A model trained on doses of one editor has not demonstrated generalization to altered PUF recognition or catalytic behavior. A leave-one-dose-out result does not establish new-editor generalization. Use independent wells/batches as evaluation units; do not randomly split events from the same well into training and test sets.

Report MAE, RMSE, signed bias, calibration slope/intercept where estimable, and prediction-interval coverage, together with independent sample count and target range. Rank correlation is supplementary. State whether intervals predict a new biological sample or only uncertainty in a fitted mean. Set scientifically useful error tolerances before examining the locked test results. **[D10]**

### 12.3 Prediction authorization

PER is emitted only when the sample's target, population mode, context, estimator/model versions and covariate support match a validated biological model, and upstream RAS/RES are usable. Otherwise return a reasoned status and the highest supported upstream output.

A numerical function that returns a value outside its validated domain is not an authorized prediction. A bounded model does not cure out-of-domain input. Do not silently clip a raw prediction below zero or above one and present it as valid. Log any exploratory extrapolation separately, excluded from routine reports and claimed performance.

### 12.4 Biological model object

```text
BiologicalCalibrationModel
  model_id; target_type; target_id; transcript/locus/strand
  sampling_population; sampling_scheme; reference_assay_id
  estimator_id; population_mode; standardization_id; reporter_calibration_id
  domain_id; permitted_covariates; support
  training_pair_ids; independent_replicate_count; split_id
  model_family; parameters; reference_error_model
  held-out metrics; interval_definition; out-of-domain policy
  validated_claims; excluded_claims; limitations; model_hash
```

---

## 13. Uncertainty from events to models

### 13.1 Distinguish four sources

| Source | Example | Treatment |
| --- | --- | --- |
| Event sampling | Finite selected cells and within-run correlation | Paired-event or justified time-block resampling |
| Controls | Mock mean/threshold, panel parameters | Resample appropriate control units and propagate shared draws |
| Biological replication | Between-well and between-batch variation | Hierarchical summaries/models and grouped resampling |
| Calibration/reference | $g$, $h$, mixture inputs, RNA assay | Model/reference uncertainty and independent validation |

A large event count does not shrink biological or shared-control uncertainty to zero. A narrow event-only interval must be labeled conditional on that well and fixed controls. Avoid presenting it as confidence in an editor's reproducibility.

### 13.2 Event-level ratio uncertainty

Resample paired $(G,R,B,\text{scatter},\text{time})$ observations, not independent channel arrays. Respect temporal dependence when it is material. Reapply the relevant selection if the resampling procedure includes control-threshold uncertainty. A local diagnostic, conditional on fixed controls and selection, is:

$$
\widehat{SE}(\widehat\theta)^2\approx
\frac{\widehat{\operatorname{Var}}(g_i-\widehat\theta r_i)}
{N\,\overline r^{\,2}},\qquad \widehat\theta=RAS.
$$

This approximation is not a full-pipeline interval and can fail with weak denominators, concentrated weights or dependence. Near the reference-detection boundary, selection and background noise can bias a ratio; establish a quantitative range rather than relying on this standard error to certify weak-red data. **[D05]**

### 13.3 End-to-end propagation

A practical resampling design draws independent batches/wells at their proper levels; draws each shared Mock/control set once per bootstrap replicate; reuses that control draw for every linked sample; recomputes RAS; refits the fixed model family for $g$ and $h$ using calibration/training data; and evaluates predictions. Do not independently jitter the same shared Mock for every sample, which would erase genuine covariance.

Keep model-family selection separate from routine uncertainty estimation unless a explicitly specified nested selection procedure is used. In every cross-validation fold, fit training-dependent preprocessing, calibration and biological models using only permitted training/reference data. An independently supplied routine calibration may be used only if that is part of the deployment protocol being evaluated.

Use a deterministic seed and enough resamples to stabilize reported intervals; benchmark and record the chosen number. Missing biological replicates or unknown reference error must appear as limitations, not be replaced by invented variances.

### 13.4 Detection and quantification claims

The relevant negative distribution for the RAS assay is a matched inactive reporter population with a valid red denominator—not the Mock's accidental red-positive tail. Estimate a reporter-assay blank distribution from appropriate INAC/negative references and assess low-activity mixtures against a prespecified false-positive/detection criterion. A limit of quantification additionally requires useful precision and bias, preferably expressed in the calibrated reference-input scale.

Do not translate an AC-DNA detection limit directly into an endogenous-editing detection limit. A near-zero coefficient of variation is not meaningful when the mean is near zero; use absolute error or interval width. Off-to-on fluorescence is a design advantage to test, not a sufficient proof of low-end sensitivity. **[D05, D07, D09–D10]**

---

## 14. QC and explicit failure behavior

### 14.1 Separate data quality from score availability

Keep `qc_state = PASS | WARNING | FAIL` separate from `score_status`. A sample can have good flow data but no applicable biological calibration. Conversely, a model may exist but the sample's denominator may be unusable. Null is not zero, and a missing score must have a reason.

| Condition | Required behavior |
| --- | --- |
| Essential channel identity unknown | Block affected measurement; do not guess aliases |
| Compensation status unresolved | Block definitive quantitative RAS; preserve audit |
| Singlet/viability unavailable | Restrict population claims; follow profile-specific warning/failure policy |
| Major reference-gate mismatch | Flag/review; no outcome-driven redraw |
| Insufficient red denominator/events/effective support | `NOT_ESTIMABLE`; retain diagnostics |
| BFP absent or linkage unverified | `coexpression` unavailable; separately assess reporter mode |
| Severe clipping or optical artifact | Fail quantitative use over affected range |
| No compatible AC/INAC model | RAS available if valid; RES `NOT_CALIBRATED` |
| Plateau/nonunique inverse | Interval/set or `NONIDENTIFIABLE` |
| Outside reporter model support | `OUT_OF_CALIBRATION_RANGE`, retain RAS |
| RNA pairing/target incompatible | PER `NOT_CALIBRATED` or `OUT_OF_DOMAIN` |
| Missing shared-bin support | Standardized score `INSUFFICIENT_SUPPORT` |
| Mock has no genuine reporter population | RAS `NOT_APPLICABLE`, not “zero activity” |

### 14.2 Threshold registry rather than invented acceptance numbers

Record every cutoff with its unit, rationale, development evidence, intended consequence and version. Include minimum selected/effective events, denominator precision, gate retention, clipping, time instability, optical negative contamination and calibration error. No universal minimum event count, 99.5% gate, or acceptable saturation fraction is declared validated here.

A warning can allow a restricted exploratory output, but the restriction must propagate downstream. Critical upstream failures cannot become an apparently valid PER simply because a fitted function can produce a number.

---

## 15. Use all data without leaking validation information

### 15.1 Declare roles before tuning

Inventory every file, then assign development, calibration, validation and exploratory roles with grouping keys. All data should be read and accounted for; not all may be used to choose parameters before testing. Keep biological batch, well, acquisition parent, editor identity and target identity visible so related observations are not split improperly.

Use historical Mock and representative controls to develop population/optical rules. Use reference ladders to fit reporter calibration. Use paired RNA data to fit biological calibration. Reserve independent data for the claim being evaluated. A separate matched control for a held-out batch is allowed when it is part of the intended deployment procedure; its biological outcomes are not allowed to tune the scoring rule.

### 15.2 Freeze scientific meaning before final evaluation

Freeze the primary estimator identity, population mode, control logic, preprocessing, model family and performance criteria before the final evaluation. Development comparisons may reveal that the proposed ratio-of-sums is unusable in some range; report that and restrict the domain or issue a documented new design version. Do not replace the estimator merely because AF, a regression slope or a clipped green score yields a more attractive conclusion.

When data are too sparse for a defensible independent test, produce software, diagnostics and provisional fits, label them `development_only`, and state the missing validation. A single well with many events is not a substitute. After honest performance assessment, an optional all-eligible-data refit may be released for deployment, but its model ID must differ and the historical held-out performance record must remain intact.

---

## 16. Software architecture and interfaces

### 16.1 Separate numerical kernels, routing and model authorization

The architecture should have independent layers for file interpretation, context estimation, population selection, aggregation, calibration, prediction and reporting. The RAS kernel must not depend on whether the group is expected to be strong or weak. Metadata routing may determine available modes and eligible models; it must never tune gates to the sample's desired biological label.

The following interfaces are specification-level pseudocode, not a claim that a package with these functions already exists:

```python
inventory = validate_inventory(raw_paths, manifests, construct_registry)
splits = define_or_load_grouped_splits(inventory, validation_plan)

panel = validate_panel(optical_controls, panel_profile)
theta_mock = fit_mock_context(mock_samples, context_config)
context = assemble_context(theta_mock, panel, metadata, frozen_profile)

sample = load_linear_sample(fcs_path, panel, preprocessing_profile)
eligible_modes = route_population_modes(sample_metadata, context)

for policy in eligible_modes:
    result_l1 = calculate_ras(sample, context, population_policy=policy)
    # No AC/INAC endpoint rescaling inside calculate_ras.
    result_l2 = apply_reporter_calibration(
        result_l1, compatible_reporter_model, authorization_policy
    )
    result_l3 = predict_editing_fraction(
        result_l2, compatible_biological_model, target_metadata,
        authorized_covariates, authorization_policy
    )
    save_result_bundle(result_l1, result_l2, result_l3)

# Fit only from the designated training/calibration partitions.
g_model = fit_reporter_calibration(l1_calibration_results, mixture_table, fit_plan)
h_model = fit_biological_calibration(l2_training_results, rna_pairs, fit_plan)
```

Numeric outputs contain their own availability status. A missing calibration must not crash the entire run or prevent valid Layer-1 outputs. A critical preprocessing inconsistency must not be swallowed by a generic exception handler that returns a plausible number.

### 16.2 Recommended repository layout

```text
sonar/
  README.md
  raw/                         # immutable inputs
  metadata/
    samples.csv
    constructs.csv
    panels.yaml
    controls.csv
    mixtures.csv
    rna_references.csv
    pairings.csv
    splits.csv
  config/
    context_profiles.yaml
    population_policies.yaml
    qc_limits.yaml
    calibration_plan.yaml
  src/
    io/  preprocessing/  context/  populations/
    scoring/  calibration/  prediction/  uncertainty/  reporting/
  contexts/                    # fitted control packages
  models/                      # versioned g and h
  results/
    inventory/  sample_metrics/  event_masks/  calibration/  validation/
  figures/
    diagnostic/  wiki/  source_tables/
  reports/
    reconciliation/  decisions/  limitations/  sample_reports/
  docs/
    SONAR_Measurement_EN_v3.1.md
    SONAR_Measurement_ZH_v3.1.md
    SONAR_Work_EN_v3.1.md
    SONAR_Work_ZH_v3.1.md
    methods_en.md
    methods_zh.md
    changelog.md
  tests/
  environment/                 # resolved package versions
```

### 16.3 Quantitative output schema

Use one result row per acquisition/biological-sample summary and population mode, never unlabeled score columns that mix modes. Long-form tables should store at least:

```text
sample_id, acquisition_id, biological_sample_id, batch_id
population_mode, standardization_id, context_id, estimator_id
N_total, N_time_pass, N_cell, N_singlet, N_viable_if_measured
N_R_detected, N_R_quantifiable, N_RB, N_selected, N_G_positive
sum_G_corrected, sum_R_corrected, mean_G_corrected, mean_R_corrected
RAS, RAS_status, RAS_interval_low, RAS_interval_high, interval_type
AF, AM, AM_positive_optional, CEF_detected, CEF_quantitative
N_eff_red, max_red_weight, upper_tail_red_share, influence_summary
G_saturation_fraction, R_saturation_fraction, B_saturation_fraction
BFP_distribution_summary, red_distribution_summary, support_summary
RES, RES_status, RES_interval_low, RES_interval_high, calibration_id
PER, PER_status, PER_interval_low, PER_interval_high, biological_model_id
target_type, target_id, sampling_population, reference_assay_id
qc_state, qc_codes, limitations, software_version, config_hash, input_hash
```

Calibration tables additionally preserve mixture inputs and reference uncertainty. RNA-pair tables preserve measured values separately from predictions. For every percentage, store its denominator. For every interval, state whether it is event-conditional, calibration-inclusive, or a new-sample prediction interval.

### 16.4 Event-level audit trail and efficient execution

Retain masks or an indexed event table showing which step excluded each event. Large datasets may be processed in chunks with cached linear representations and stable sums. Plot subsampling is deterministic and display-only. Ensure parallel/chunked calculations agree with full-file calculations within a documented floating-point tolerance.

Export a lightweight full-results table and optional event-level Parquet/Arrow data. Record the package/environment lockfile after verifying installed versions. Save exact transforms, gates, background-model coefficients and calibration parameters; screenshots alone are not an executable analysis definition.

### 16.5 Version dependencies

Each model fingerprint includes upstream preprocessing profile, channel mapping, background correction, population policy, RAS estimator and standardization. Changes that alter numerical scores invalidate the identity of dependent $g$ and $h$ models until reprocessing/refitting or a validated bridge is completed. An editorial translation correction does not necessarily invalidate models; a gate or formula change does.

Preserve previous results with their original IDs. Reanalysis should produce a side-by-side comparison and an explicit change log, not overwrite historical numbers as if they had always been calculated by the new method.

---

## 17. End-to-end execution plan for Work

### Phase A — inventory and scientific reconciliation

Read every supplied data source. Hash files, resolve sample/replicate identities, verify construct and channel mappings, establish the actual AC/INAC mixture basis, and map RNA pairings. Produce a missing/conflicting-information report. Resolve from existing records before asking the user to repeat information. Separate missing essential facts from optional refinements.

### Phase B — establish profiles and validation partitions

Before tuning, lock the grouping/split plan and scientific comparison targets. Identify compatible optical/biological domains. Fit and compare a small control-based candidate set for gates, background models and thresholds. Evaluate retention, independent-negative transfer, residual behavior, stability and support—not experimental rank. Fill D02–D05 decisions with evidence, then freeze accepted context profiles.

### Phase C — implement and test Layer 1

Implement the declared linear ratio-of-sums kernel with both population modes, signed green values, denominator/influence QC and supporting metrics. Run the unit tests below. Reprocess all eligible historical samples under consistent profiles and output per-sample audits. Compare expression dependence and alternative estimands as diagnostics. Report where the primary score is unsupported rather than tuning it to flatten real biology.

### Phase D — fit reporter calibration

Verify locked reference integrity and mode compatibility. Fit $g$ using the proper mixture basis and independent replicate summaries. Test model complexity, inverse support, low-end precision, context transfer and genuine-edited-reporter equivalence where data permit. Keep distinct model IDs for unbridged reporter/population domains. Produce RAS even when no defensible RES mapping exists.

### Phase E — fit biological calibration

Independently QC RNA measurements and pairing. Fit target/population-specific $h$ and propagate upstream uncertainty. Evaluate only the declared claims using the appropriate held-out units. Compare a RES-only baseline with prespecified additional-covariate models if needed; justify complexity by validation, not training fit. Restrict PER to validated domains.

### Phase F — release results, software and maintained documentation

Export the reproducible code/configuration, result tables, event masks, calibration objects, diagnostics, sample reports, validation report and limitations register. Generate real-data figures from exported tables, then replace Wiki placeholders only where evidence is sufficient. Update the English specification first, mirror the Chinese translation, and record every resolved D-item plus any remaining blocker. The final run summary must state the highest authorized output for each sample/mode.

---

## 18. Required test suite

### 18.1 Numerical unit tests

The numeric examples below are synthetic test fixtures only. They are not SONAR experimental results and must never appear in a validation-results figure as measured data.

| ID | Fixture | Expected result |
| --- | --- | --- |
| T01 | $r=(10,90)$, $g=(5,9)$ | RAS = 0.14; not the mean-of-ratios 0.30 |
| T02 | Duplicate all paired events | RAS unchanged; event count doubles |
| T03 | Multiply corrected $g,r$ by 7 | RAS unchanged |
| T04 | Multiply only corrected $g$ by 2 | RAS doubles; gain invariance must not be falsely asserted |
| T05 | $r=(10,10)$, $g=(-2,2)$ | RAS = 0; rectification would incorrectly give 0.1 |
| T06 | No selected cells or unsafe red sum | `NOT_ESTIMABLE`, not 0 or epsilon-stabilized output |
| T07 | Change green positivity threshold only | AF may change; main RAS does not |
| T08 | Reverse order of fixed red/blue gates | Identical final intersection |
| T09 | T01 with only first event B+ | RAS_RB=0.5; RAS_RB−=0.1; red weight 0.1; mixture RAS=0.14 |
| T10 | Equal positive red weights | $N_{\rm eff,R}=N$; concentrated weights reduce it |
| T11 | Fixed-cell-weight standardization with unequal bin red means | Ratio of weighted means, not unweighted/naive mean of bin ratios |
| T12 | Linear calibration $g(A)=0.1+0.8A$, RAS=0.5 | RES=0.5; nonlinear models are not forced into endpoint normalization |
| T13 | Flat calibration interval | Interval/set or `NONIDENTIFIABLE` |
| T14 | RAS outside supported calibration range | Explicit out-of-range status, no silent clipping |

### 18.2 File, routing and provenance tests

| ID | Requirement |
| --- | --- |
| T15 | Verified channel permutation changes neither selection nor score; unknown mapping fails. |
| T16 | Already compensated exports are not compensated twice; unresolved state is blocked. |
| T17 | Passing display-transformed values into the linear aggregation kernel raises a typed error. |
| T18 | Plot subsampling does not change numerical results; chunked/full calculations agree. |
| T19 | Missing BFP and measured BFP negativity produce different statuses; legacy mode remains explicit. |
| T20 | Randomizing biological group labels does not alter fixed-context gate application or RAS. |
| T21 | Bulk RNA and gated conditional targets cannot be paired silently under one model identity. |
| T22 | Out-of-domain target/editor/context prevents unauthorized PER. |
| T23 | Changed estimator/gate/context fingerprints invalidate dependent calibration identities. |
| T24 | Technical acquisitions from one well are never counted as independent biological replicates. |
| T25 | Validation-group IDs never enter fitting or parameter-selection logs improperly. |
| T26 | Null scores retain reason codes and cannot be serialized/displayed as numerical zero. |
| T27 | Shared-control bootstrap draws are shared across linked samples, not independently regenerated. |
| T28 | Saturated values trigger censoring/QC policy, not automatic deletion of inconvenient bright cells. |

### 18.3 Empirical acceptance tests

Unit tests establish correct implementation, not biological validity. Empirical acceptance requires independent negative-control behavior, stable population selection, adequate red support, acceptable optical residuals, reference integrity, usable AC/INAC dynamic range, replicate precision, calibrated inverse uncertainty and independent molecular prediction within the claimed domain. Add explicit tests of red normalization and BFP proxy comparability. Numeric acceptance limits belong in the decision registry with their evidence.

---

## 19. Deliverables, figure generation and Wiki synchronization

### 19.1 Required run deliverables

Deliver a single reproducible entry point plus all resolved metadata/configuration, fitted contexts, model objects, tables, masks, tests and logs. The user should be able to rerun the analysis without recovering hidden manual gates from a screenshot. Include a one-page run summary that names the data coverage, unresolved blockers and score availability by layer.

| Output | Content |
| --- | --- |
| Inventory/reconciliation | Included, duplicate, missing, conflicting and excluded files |
| Context report | Control distributions, gate geometry, optical tests, linear baselines, thresholds, QC |
| Layer-1 table | Both modes, RAS and components, all denominators, uncertainty, support |
| Calibration report | $g$ by domain/mode, mixture basis, residuals, inverse range, bridges |
| Biological report | RNA assay QC, pairings, target-specific $h$, held-out metrics |
| Sample reports | Scores, statuses, intervals, population, model IDs and limitations |
| Reanalysis comparison | Old estimator versus new estimator, explicitly labeled |
| Documentation | Updated English base, aligned Chinese, decision log and changelog |

### 19.2 Figure specification

The companion Measurement document provides six English figure prompts and placements; the separate Chinese edition supplies their translations. Use illustration tools only for explanatory schematics. Actual FCS plots, calibration curves, sequencing traces and validation panels must be rendered from real data by reproducible code. A schematic example may contain invented values only if prominently labeled illustrative and kept separate from evidence figures.

Each plotted panel must be reconstructible from a source table, analysis version and population definition. Show biological replicate points where possible, state independent $n$, keep consistent axes and shared-bin definitions, and distinguish training from held-out observations. A smooth fitted curve is not evidence of dense measurements between calibration points.

| Figure ID | Data or design source |
| --- | --- |
| W-F1 | Verified construct roles plus four-layer schematic |
| W-F2 | Actual Mock/panel controls and gate masks |
| W-F3 | Ratio-of-sums schematic (clearly illustrative); actual internal-reference/load tests and shared-BFP-range comparisons |
| W-F4 | AC/INAC metadata, well-level RAS, fitted curve and inverse uncertainty |
| W-F5 | RNA pairings, held-out predictions, residuals and intervals |
| W-F6 | Actual well/batch precision or transfer evidence; traceable sample report and documented re-execution; optional shared-BFP profiles |

### 19.3 Page ownership and maintenance

Measurement contains the measurement objective, local method/control summary, units, calculations, calibration, supported validation results and a practical reproduction entry point. Engineering owns the iterations and failures that motivated the method; Protocol provides the full stepwise procedures; Contribution presents the broader reusable release. Cross-link detailed resources without moving essential Measurement evidence off the Measurement page. This publication clarification is part of the v3.1 documentation revision; it does not change the numerical pipeline.

Update English first, then its Chinese counterpart. Keep equation/estimator IDs, population names, uncertainty definitions and model scopes identical. Replace “designed to” with “demonstrated” only after linking a qualifying dataset and validation result. Keep unvalidated future extensions visibly separate from current capabilities.

---

## 20. Decision register: what data must resolve

The table is the shared maintenance contract for both documents. For each item, Work must record `status`, `evidence_files`, `candidate_choices`, `selected_value_or_policy`, `rationale`, `validation_scope`, `version` and `remaining_limitations`. Status values are `OPEN`, `PROVISIONAL`, `FROZEN_FOR_DOMAIN`, or `UNSUPPORTED`. Freezing a rule for one domain does not make it universal.

### D01 — Construct identity and reference-state integrity

Obtain final reporter/editor sequences and maps, exact editable site, edited/unedited DD linkage, AC/INAC locked-state evidence, fluorophore identities, ORCA–P2A–BFP linkage and available tagged-versus-untagged characterization. Decide which mechanisms and marker interpretations are supported. Without sequence support, retain only the operational low-to-high description; do not draw an exact codon switch or assume active ORCA leaves INAC unchanged.

### D02 — Optical profile and linear units

Resolve channel identities, native scaling, compensation state/matrix, single-color controls, multicolor negative behavior, detector range and cross-session compatibility. Decide whether each profile supports quantitative RAS and BFP gating. If critical optical provenance is missing, preserve exploratory diagnostics but block definitive quantitative conclusions; do not infer a matrix from the biological response.

### D03 — Population/time gates and display transform

Compare the small prespecified gate/transform candidate set against reviewed development controls. Select supported intact-cell and singlet definitions, time-QC logic and visibility/viability limitations. Record parameters and review decisions. Poorly resolved cell identity or missing pulse geometry limits the accepted mode; it is not repaired by a decorative polygon or universal retention percentage.

### D04 — Background estimators and positivity rules

Evaluate linear expected-background models, descriptive transformed summaries, quantile conventions, constant/conditional panel boundaries and independent-negative transfer. Freeze only supported models and ranges. An own-Mock quantile check is not validation; a conditional model outside its negative-control support is not authorized.

### D05 — Quantification limits and sample QC

Use actual distribution, replicate and precision data to set red quantification margins, denominator/count/effective-count requirements, influence limits, time/retention flags and saturation policies. Separate detection from quantitative precision. A low-expression sample may yield descriptive plots but no defensible ratio; retain that distinction rather than converting it to a weak-editing result.

### D06 — Population-mode compatibility and BFP calibration bridge

Determine which AC/INAC datasets support reporter-population mode, which support co-expression mode, and whether any bridge is demonstrated. Evaluate reference integrity under active editor and equivalence of inactive-editor/BFP-only alternatives. If untested, keep mode-specific models and leave unsupported RES unavailable; do not discard valid legacy RAS.

### D07 — Reporter response model and surrogate transfer

Resolve mixture basis/process, dilution uncertainty, model family, dynamic range, local inverse precision and real-edited-reporter transfer. Require independent replicate support and inspect nonlinearity/plateaus. If the ladder is noninformative, report no unique RES rather than fitting a high-order curve through every point.

### D08 — BFP covariates and optional standardization

Validate the editor-expression proxy, common BFP or joint red–blue bins, reference weights and common-support criteria. Decide whether observed-population and standardized results answer distinct useful questions. Without overlap, do not invent matched-expression comparisons or replace missing bins with model extrapolation disguised as observations.

### D09 — Molecular reference and sampling alignment

Verify target type, locus/strand, trace/read quality, RNA origin, assay calibration, reference uncertainty, sampling population/time and flow–RNA pairs. Separate reporter, introduced and endogenous endpoints. If only bulk RNA exists, develop an explicitly bulk model or limit the claim; do not label it conditional $R^+B^+$ editing.

### D10 — Biological model and validated prediction domain

Select $h$ complexity, covariates, uncertainty and performance criteria on permitted development data; then evaluate held-out claims. Record candidate/target/batch scope, not just a global correlation. With inadequate independent evidence, keep PER developmental or unavailable while preserving supported RAS/RES.

### D11 — Historical-data reconciliation

Resolve corrected sample labels, plasmid concentrations, actual doses, compensation exports, instrument changes, technical duplicates and prior analysis versions from supplied records. Mark unresolved values unknown; do not fill them from confident earlier assistant statements. Produce a versioned historical-versus-v3 comparison for all samples that can be reprocessed.

### D12 — Internal-reference validity and estimator sensitivity

Test whether red normalization removes a common expression component over the intended domain, without erasing real substrate-dose biology. Examine red dependence, genuine high-expression influence, raw versus alternative estimands, reporter architecture and treatment effects. Restrict the domain or revise the estimator transparently if necessary; no candidate is accepted merely because it improves a desired rank or calibration correlation.

---

## 21. Ready-to-use Work handoff prompt

### Implementation instruction

> Build the complete SONAR analysis pipeline using this specification, its companion Wiki document, and every supplied FCS, construct record, experimental manifest, control file, AC/INAC mixture record and independent RNA-reference dataset. Treat this document as `SONAR-v3-design`, not as a claim that the algorithms or calibration have already been validated.
>
> First inventory and reconcile all inputs, verify channel/construct identities and compensation state, establish the actual mixture basis and RNA pairings, and define grouped development/calibration/validation splits. Do not substitute earlier chat estimates for raw records. Resolve available information from the supplied files before asking for missing essentials.
>
> Implement Layers −1, 1, 2 and 3 as separate auditable modules. Preserve linear compensated intensities for the primary ratio-of-sums RAS, use mCherry as both selection marker and continuous internal reference, preserve BFP as a co-expression marker/covariate, retain both reporter-population and co-expression modes, and do not gate on EGFP positivity for the main score. Keep signed corrected green values and explicit denominator/influence QC. The RAS kernel must be blind to desired group outcomes.
>
> Fit reporter calibration only from compatible AC/INAC references with a declared mixture axis. Verify locked-state integrity and population/context compatibility before transferring a calibration. Model flat or out-of-range regions honestly. Fit biological calibration only to correctly identified, population/time-matched or explicitly bulk RNA endpoints; carry assay uncertainty and validate the intended target/editor/batch claim on independent data. Do not equate RES with endogenous editing or BFP intensity with exact active-editor abundance.
>
> Resolve D01–D12 with evidence, selected policies, versioned configuration and remaining limitations. Complete every layer supported by the data; return typed unavailable/not-calibrated/out-of-domain statuses for unsupported outputs rather than invented values. Do not silently change the primary scientific estimand to improve rankings or correlation. Any numerical definition change requires a declared version update and downstream recalibration.
>
> Deliver reproducible source code, environment/configuration, tests, full result tables, event masks, context/model objects, QC and validation reports, documented uncertainty, actual-data figure exports and an explicit limitations report. Use the Wiki figure prompts only as layout instructions, never as permission to fabricate data. Update the English base first and the Chinese translation correspondingly. Keep raw files immutable and retain all provenance/model hashes. The final summary must identify each sample's highest supported output and every unresolved blocker.

---

## 22. Configuration skeleton

This is valid YAML intended as a starting template, not a runnable frozen configuration. `null` entries deliberately prevent unsupported assumptions. Work should populate them from the decision registry and refuse production-mode execution when a required policy remains unresolved. A diagnostic/development run may still emit partial outputs.

```yaml
schema_version: sonar-config-v3-design
release_status: design
language_source_of_truth: en

provenance:
  raw_inputs_immutable: true
  hash_algorithm: sha256
  require_sample_manifest: true
  require_split_registry: true

preprocessing:
  channel_map: null                    # D02
  native_scaling_profile: null         # D02
  compensation_policy: exactly_once
  compensation_state_evidence: null    # D02
  quantitative_representation: linear_compensated
  preserve_signed_values: true
  display_transform: null              # D03
  plot_subsampling_affects_scores: false

context:
  mock_control_ids: null
  optical_control_set_ids: null
  cell_gate_policy: null               # D03
  singlet_gate_policy: null            # D03
  time_qc_policy: null                 # D03
  viability_policy: report_actual_availability
  linear_background_model: null       # D04
  positive_threshold_policy: null      # D04
  red_quantification_policy: null      # D05
  panel_negative_validation: null      # D02/D04

scoring:
  estimator_id: ras-linear-ratio-of-sums-v3-design
  available_modes:
    - reporter_population
    - coexpression
  gate_on_green_for_primary_score: false
  green_rectification: false
  arbitrary_denominator_epsilon: false
  bfp_denominator_normalization: false
  primary_sum_population_must_match: true
  standardization_policy: null         # D08, optional

reporter_calibration:
  fraction_basis: null                 # D07
  mixture_process: null                # D07
  reference_integrity_evidence: null   # D01/D06
  mode_bridge_evidence: null           # D06
  domain_registry: null
  model_family: null                   # D07
  inverse_policy: identifiable_only
  extrapolation_for_routine_reports: false

biological_calibration:
  target_type: null                    # D09
  target_id: null
  population_pairing_policy: null      # D09
  reference_assay_id: null
  model_family: null                   # D10
  additional_covariates: null
  authorized_domains: null
  extrapolation_for_routine_reports: false

qc:
  numerical_limits_registry: null      # D05
  score_status_is_separate_from_qc: true
  missing_score_is_zero: false

validation:
  split_registry_path: null
  grouping_keys: null
  prespecified_performance_targets: null
  random_seed: 20260918                # computational reproducibility only
  bootstrap_replicates: null           # choose after convergence checks
  shared_control_resampling: true
  event_count_is_biological_n: false
```

---

## 23. Source provenance, references and claim boundaries

### 23.1 Project-derived content

The source v2 document supplies the four-layer names, modular dependency structure, AC/INAC concept and RNA-reference prediction goal. Subsequent user discussions supply the preference for continuous mCherry normalization, the importance of low-to-high reporter output, and the reported ORCA–P2A–BFP construction. This reconstruction declares corrections to the former AF-primary and transformed-statistics-only proposals; it does not pretend those corrections were already in v2.

The exact construct mechanism, usable gates, mixture response, quantitative BFP relationship and successful PER performance remain data-dependent. The primary estimator and QC/model architecture here are proposed analytical design, with their derivations shown; external references are not represented as having validated SONAR itself.

### 23.2 External methodological references

[^R1]: Iwamoto M et al. *A General Chemical Method to Regulate Protein Stability in the Mammalian Central Nervous System.* Chemistry & Biology 17 (2010): 981–988. DOI: `10.1016/j.chembiol.2010.07.009`. General ecDHFR-DD/TMP mechanism; not SONAR sequence validation.
[^R2]: Kim JH et al. *High Cleavage Efficiency of a 2A Peptide Derived from Porcine Teschovirus-1 in Human Cell Lines, Zebrafish and Mice.* PLOS ONE 6 (2011): e18556. DOI: `10.1371/journal.pone.0018556`. General 2A context; not a quantitative ORCA–BFP conversion.
[^R3]: UTHealth Houston, IMM Flow Cytometry Service Center. *FMO Controls.* Official facility guidance, accessed 2026-09-18: `https://med.uth.edu/imm/flow-cytometry-services/protocols-and-guidelines/fmo-controls/`. The genetically encoded panel adaptation in this specification requires its own controls.
[^R4]: UTHealth Houston, IMM Flow Cytometry Service Center. *Compensation Controls.* Official facility guidance, accessed 2026-09-18: `https://med.uth.edu/imm/flow-cytometry-services/protocols-and-guidelines/compensation-controls/`.
[^R5]: MoriarityLab. *EditR.* Official source repository, accessed 2026-09-18: `https://github.com/MoriarityLab/EditR`. An available Sanger-trace quantification implementation; RNA-reference applicability is not assumed.
[^R6]: FlowKit. *Sample Class — API Documentation.* Official documentation, accessed 2026-09-18: `https://flowkit.readthedocs.io/en/latest/sample.html`. Verify reader preprocessing and explicitly select the correct event representation.

---

**Final design summary.** Controls establish a defensible context; mCherry supplies the continuous reporter reference; BFP identifies and stratifies editor-linked expression; EGFP supplies the response. Layer 1 aggregates paired linear fluorescence within a declared population. Layer 2 maps that score to a validated reference-equivalent input. Layer 3 predicts only a named molecular endpoint supported by independent evidence. When a layer lacks that evidence, the pipeline stops the claim—not the useful upstream analysis.

---

## 24. Measurement-page evidence export and publication interface

### 24.1 Evidence is not an extra analysis layer

This documentation-only addition aligns the four-layer implementation with the companion Measurement page. The public Best Measurement entry emphasizes reproducibility, method clarity, usefulness elsewhere and approach-appropriate validation/calibration.[^IGEM] These are paraphrased judging aspects, not new scientific outputs or a points scheme. Preserve every estimator, population, domain and uncertainty definition established in §§0–23.

`D01`–`D12` remain implementation decisions. `E01`–`E08` index evidence shown on the page. Do not confuse resolving a software decision with demonstrating the corresponding experimental claim. This interface is a SONAR-specific reporting plan, not a statement that iGEM requires each individual test, a particular reference bead, absolute molecule units, successful PER, or external-laboratory replication in every project.

### 24.2 Required evidence exports

| Evidence ID | Export from the actual supported analysis | Main source decisions | Measurement destination |
|---|---|---|---|
| E01 | Verified construct/reference-state registry and permitted mechanism diagram | D01 | W2; W-F1 |
| E02 | Optical/control QC, accepted gates, independent negative transfer, sample/settings/SOP summary | D02–D05 | W3; W-F2 |
| E03 | Internal-reference range, denominator/influence checks, reference-load tests and supported shared-BFP comparisons | D05, D08, D12 | W4; W-F3 |
| E04 | Actual mixture basis, model/bridge identity, identifiable range, held-out recovery, low-end precision and bias | D06–D07 | W5; W-F4 |
| E05 | RNA identity/assay QC, actual pairing, independent held-out predictions and authorized scope | D09–D10 | W6; W-F5 |
| E06 | Independent well/batch repeatability or transfer estimates with uncertainty and tested scope | D05, D07, D10–D12 as applicable | W7; W-F6 |
| E07 | Versioned example dataset/config/environment, actual tested command, reference outputs and re-execution agreement | D11; §§16–19 | W8; W-F6 |
| E08 | A project comparison/decision supported by the released analysis, with effect, uncertainty and limitations | Relevant frozen decisions | W1, W7, W9 |

If an item lacks data, export its status and the missing evidence, not an invented result. A sample-level warning is not automatically a failure of the entire method, and an attractive group separation is not automatically validation.

Suggested additional files (reporting outputs, not new required raw inputs):

```text
reports/measurement/
  evidence_register.csv
  unit_and_calibration_statement.md
  methods_at_a_glance.md
  reproducibility_record.md
  claims_and_limitations.md
figures/wiki/source_tables/
  E02_context.*
  E03_reference.*
  E04_calibration.*
  E05_molecular_validation.*
  E06_repeatability.*
  E08_project_comparison.*
```

### 24.3 Evidence-register contract

Keep `evidence_id`, `status`, `claim`, `source_files`, `input_hashes`, `sample_ids`, `population_mode`, `independent_n`, `context_id`, `estimator_id`, `calibration_id`, `result_table`, `figure_id`, `uncertainty_definition`, `limitations` and `review_date`. Status values are `planned`, `in_progress`, `supported_within_domain`, `not_evaluated` or `not_supported`. All affirmative claims must resolve to real tables/records and the stated domain.

This evidence status is distinct from sample `qc_state`, score availability and D-item freeze status. Keep all four concepts separate. Render a missing result as “not evaluated” or “not calibrated” as appropriate; never serialize it as a measured zero.

### 24.4 Unit and calibration statement

Export a readable statement of the actual fluorescence scale and its traceability. When no optical-standard conversion is documented, retain linear detector a.u. and the verified optical profile. Compensation and Mock subtraction are not an absolute calibration. RAS is an operational channel ratio, not a universal molecular ratio; RES uses the explicit reference-input basis; PER has an actual target, population, time and prediction domain.

If optical reference standards were used, report their identity, assigned values, mapping, compatible channels/range and uncertainty from the records. Do not retrospectively infer standards or molecule units to make the award narrative stronger. An optical calibration, a reporter-response calibration and a biological endpoint calibration solve different problems.

### 24.5 Reproduction evidence at its actual level

A re-execution record names the release/configuration/environment, input hashes, tested command, expected tables/figures, comparison tolerance and result. This demonstrates computational reconstruction only. Independent wells/batches support assay repeatability or transfer at the tested level. Another operator or laboratory may provide stronger transfer evidence when actually available; record that separately rather than labeling software availability as external experimental reproduction.

Document complete methods and a worked example even without an external replication dataset. Do not invent a universal replicate count or acceptance threshold; use the existing prespecified, domain-supported precision/QC framework. Carry both independent sample counts and event support into the public tables.

### 24.6 Publication and language synchronization

Maintain these four standalone documents:

```text
SONAR_Measurement_EN_v3.1.md
SONAR_Measurement_ZH_v3.1.md
SONAR_Work_EN_v3.1.md
SONAR_Work_ZH_v3.1.md
```

Use the English Measurement page as the narrative source and translate its verified updates into Chinese. Update the Work English specification first for technical changes. Keep W-F1–W-F6, E01–E08, D01–D12, equations and scientific identifiers consistent. The revised W-F6 includes repeatability/re-execution evidence in addition to its example report.

Before replacing a placeholder, verify its source table and claim status. Keep editor instructions and rubric mapping in appendices rather than copying them into the public body. Measurement must retain its methods, units, essential validation and reuse summary locally; links to Engineering/Protocol/Contribution supplement rather than replace them. Verify the actual team `/measurement` route and final form-specific requirements before submission.

**Source boundary:** the current official public page was checked through indexed official excerpts because direct text access returned a JavaScript-only shell. No authenticated team Judging Form or full 2026 handbook was reviewed. This addition maps the public aspects to a practical evidence package; it is not a claim of eligibility, award success or completed measurement validation.

[^IGEM]: iGEM Competition. *Special Awards*, Best Measurement entry, `https://competition.igem.org/judging/awards/special`. Public 2026 route and ballot aspects checked 2026-09-19 via official-page indexed excerpts. Detailed access and paraphrase notes are in Appendix A of the companion Measurement document.

