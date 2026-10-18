"""Scientific v4 handoff, with retrospective-label provenance and unchanged endpoints explicit."""
from layer23_common import *
from s7_correction import BASE,CORR

def read(name):return pd.read_csv(ROOT/name)
def run():
    header=f"Version: `{VERSION}`. Correction date: 2026-10-13. Reference basis: `{CORR['reference_basis_id']}`.\n\n"
    cmp=read('results/calibration/S7_before_after_model_comparison.csv');cv=read('results/calibration/S7_model_comparison.csv');summary=read('results/calibration/S7_corrected_response_summary.csv');dom=read('results/calibration/S7_exploratory_domains.csv');joint=read('results/calibration/S7_cross_model_supported_ranges.csv');support=read('results/calibration/S7_cross_model_inverse_support.csv');adj=read('results/calibration/S7_adjacent_level_distinguishability.csv');matched=read('results/calibration/S7_matched_inverse_validation.csv');sens=read('results/calibration/S7_reference_sensitivity.csv');res=read('results/calibration/S7_RES_results.csv');inv=read('results/calibration/S7_inverse_identifiability.csv');compat=read('results/calibration/S7_S10_compatibility.csv');manifest=read('inventory/S7_corrected_manifest.csv');models=json.loads((ROOT/'models/layer23/S7_calibration_models.json').read_text());cal=json.loads((ROOT/'results/calibration/S7_calibration_summary.json').read_text());cs=json.loads((ROOT/'results/calibration/S7_correction_summary.json').read_text())
    main=cmp[cmp.validation=='leave_one_reference_level_out'];training=cmp[cmp.validation=='in_sample_descriptive'];high=adj.iloc[-1];aff=training[training.model=='affine'].iloc[0]
    common=matched[matched.validation=='leave_one_reference_level_out'];jr=joint.iloc[0];good=support[(support.RAS>=jr.RAS_low)&(support.RAS<=jr.RAS_high)];masslow=good[['isotonic_point','hinge_point']].min().min();masshigh=good[['isotonic_point','hinge_point']].max().max()
    boundary=f"The largest contiguous cross-model diagnostic range is **RAS {jr.RAS_low:.4f}–{jr.RAS_high:.4f}**, corresponding to model point estimates spanning approximately **{100*masslow:.1f}–{100*masshigh:.1f}% AC DNA mass**. This is an outcome of the stated grid/width screen, not an externally validated interval of assay accuracy."
    status_text='\n'.join(f'- `{k}`: {v}' for k,v in CORR['status_definitions'].items())
    correction=header+f'''# S7 label-correction record

The primary interpretation exchanges original 75% and 90% reference labels, exactly as authorized by the experimental team. Source: **{CORR['correction_source']}** The team described a probable transposition from retrospective recollection. No contemporaneous independent preparation record verifies it. Improved fit is conditional model agreement and **does not prove the labels were wrong**.

{md(manifest[manifest.acquisition_id.isin(CORR['swap_by_acquisition_id'])][['original_acquisition_id','original_filename','pre_correction_ac_mass_fraction','corrected_ac_mass_fraction','correction_status']])}

The original source label 10 remains corrected to 15% under the prior confirmation. `original_ac_mass_fraction` records the literal filename/source label (0.10 for those samples), `pre_correction_ac_mass_fraction` records v3 interpretation (0.15), and `corrected_ac_mass_fraction` records the current primary basis. Source sample IDs, acquisition IDs, well IDs, filenames, hashes, dates, status and correction source remain separate. A/B wells stay independent transfections; no well is reassigned to another replicate.

The original v3 release ZIP is retained unchanged. `baselines/v3/` preserves its scientific source/configuration/output snapshot and archive hash. A complete archived v3 rerun passed before correction; see `pre_correction_reverification.json`. `reports/S7_correction_unaffected_hashes.csv` verifies preserved evidence by file hash.

Affected: the primary sample interpretation, S7 reference table, three calibration fits, grouped validation, inverse estimates/uncertainty, S7-axis figures, conditional S10 mappings, affine-rescaling sensitivity, scientific registers and integrated reports. Preserved: original FCS/AB1, Layer 0–1 estimator and configuration, event masks, backgrounds, RAS values and uncertainties, BFP fractions, molecular reference and Sanger metrics, flow–molecular pairs, direct signal models and their validation. Historical `results/ras_results.csv` retains its v3 label column and bytes; current calibration always joins the corrected manifest by acquisition ID. It must not infer current AC input from the historical column.

The updated execution entry uses the verified v3 upstream artifacts and recalculates only affected dependencies. This is not another FCS gate fit or Sanger reanalysis. A changed upstream hash invalidates the correction run. No unrelated implementation defect was folded into this correction.
'''
    report('reports/S7_Label_Correction_Record.md',correction)
    comparison=header+f'''# Original versus corrected S7 calibration

## Quantitative result
The correction materially improves reference-model agreement, but leaves low-input overlap and high-end compression. The measured RAS values are identical. Affine training R² changes from **{aff.training_R2_original:.6f} to {aff.training_R2_corrected:.6f}**.

{md(main[['model','RAS_RMSE_original','RAS_RMSE_corrected','RAS_MAE_original','RAS_MAE_corrected','inverse_recovery_n_original','inverse_recovery_n_corrected','inverse_MAE_mass_fraction_original','inverse_MAE_mass_fraction_corrected']])}

Forward leave-level metrics evaluate the same 16 interpolable held-out wells; the four endpoint wells cannot receive forward interpolation when their whole reference level is removed. Inverse availability is a separate criterion and can differ from forward availability. Do not compare inverse errors without also reporting available sample counts.

On the **same {int(common.common_well_n.iloc[0])}** held-out wells with estimable inverses in every corrected model:

{md(common[['model','common_well_n','MAE_mass_fraction','RMSE_mass_fraction','bias_mass_fraction']])}

The lowest leave-level forward RMSE changes from affine in v3 to **the fixed-50% monotone hinge in v4** ({cs['corrected_leave_level_RMSE']:.6f}). It also has the lowest inverse error in the matched subset. Isotonic remains best for leave-one-well prediction at already represented levels and is retained as the shape diagnostic. This is descriptive model preference within a small dataset, not an independently tested winner; model comparison itself uses these folds and no nested external model-selection validation exists.

## What disappeared and what remains
The former 75→90% decrease becomes an increase from **0.978722 to 1.132248** under the authorized interpretation; all 11 saved gate/background/threshold sensitivities preserve that ordering. These are the same underlying acquisitions. Corrected 90% and 100% means are **1.132248 and 1.130373**, a difference of **{high.delta_RAS:.6f} RAS**. With only two wells per level, the descriptive Welch interval for the difference is [{high.difference_low:.4f}, {high.difference_high:.4f}]. It does not distinguish them and does not prove equivalence or a biological saturation mechanism.

Low-input reversals/overlap at 0–5%, 15–20% and 30–40% persist. Isotonic pooling retains those plateaus and adds a 90–100% plateau. The smooth hinge imposes an increasing high segment and cannot independently demonstrate separation of 90% from 100%.

## Did usable RES expand?
Yes, **model-conditional, reference-specific exploratory RES becomes more defensible in the middle range**. The earlier claim that every region is broadly unresolved no longer describes the corrected results. {boundary}

The diagnostic requires a unique model inverse, positive local slope, and the union of isotonic/hinge discrepancy envelopes no wider than 0.20 AC mass fraction, with neither reference boundary truncating the set. The 0.20 width threshold is retained from v3; the cross-model/interior criteria guard against model dependence and artificial narrowing near boundaries. It does not mean ±10 percentage-point validated accuracy, and the envelopes are not calibrated 95% confidence intervals. The numerical grids have 0.001 mass-fraction and 0.0005 RAS spacing. Tiny isolated pass points at the threshold boundary are retained in the exported table but do not extend the largest contiguous range; these grid endpoints do not imply four-decimal assay precision.

No `VALIDATED_WITHIN_DOMAIN` RES is assigned. The retrospective labels, two wells per level, unknown exact reference constructs, incomplete optical validation and absence of blinded independently prepared mixtures still prevent an externally validated quantitative claim. Additional reference calibration is required for such a claim. AC DNA mass equivalent is never RNA-editing percentage.

Sources: corrected well/mean tables, `S7_before_after_model_comparison.csv`, `S7_matched_inverse_validation.csv`, `S7_cross_model_inverse_support.csv`, `S7_adjacent_level_distinguishability.csv`, and all detailed calibration outputs under `results/calibration/`.
'''
    report('reports/S7_Calibration_Before_After_Comparison.md',comparison)
    layer2=header+f'''# Layer 2 — corrected reporter calibration and RES

## Reference inputs and actual fits
Twenty independent transfection wells, two per AC DNA mass level, retain identical RAS measurements and uncertainties. The 75/90 interpretation follows the team's probable retrospective transposition; 10→15 remains confirmed. Exact AC/INAC construct lengths remain unverified, so no molar conversion is introduced.

{md(summary)}

The same v3 methods are refit: unweighted affine OLS; increasing isotonic regression with interpolation between fitted thresholds; continuous monotone piecewise-linear calibration with fixed knot A=0.5 and nonnegative segment slopes. All 20 wells remain in every primary fit. The hinge knot, random seed, 1,000 stratified bootstraps and model-comparison rules are documented in configuration. No high-level deletion or knot search selects the primary fit.

Affine intercept/slope: {models['affine']['coefficients'][0]:.6f}, {models['affine']['coefficients'][1]:.6f}. Hinge intercept, low slope and high slope: {', '.join(f'{v:.6f}' for v in models['monotone_hinge_50']['coefficients'])}. Parameters, isotonic thresholds, version, corrected reference basis, input hashes and correction hash are serialized in `models/layer23/S7_calibration_models.json`.

## Validation and model preference
{md(cv[['model','validation','training_R2','RAS_prediction_n','RAS_RMSE','RAS_MAE','RAS_bias','inverse_recovery_n','inverse_MAE_mass_fraction']])}

Leave-one-well-out asks about a new well at a represented input; leave-one-level-out asks about interpolation across an omitted AC level. Technical events never become independent calibration samples. The endpoint exclusion and inverse availability are explicit in the fold table. The fixed-50% hinge is the preferred exploratory forward/inverse model under leave-level evaluation, with isotonic retained to expose plateaus. Hinge matched-case inverse MAE is **{100*common[common.model=='monotone_hinge_50'].MAE_mass_fraction.iloc[0]:.2f} AC percentage points**, among {int(common.common_well_n.iloc[0])} common estimable wells; this is internal recovery error, not an external accuracy guarantee. Affine lack-of-fit remains F(8,10)={cal['affine_lack_of_fit_F']:.3f}, p={cal['affine_lack_of_fit_p']:.4g} under the limited pure-error assumptions.

## Inverse uncertainty and ranges
Model-specific diagnostic ranges:

{md(dom[['model','model_mass_low','model_mass_high','RAS_low','RAS_high','status']])}

{boundary}

Isotonic exact plateau inverses remain intervals:

{md(inv[(inv.model=='isotonic')&(inv.exact_inverse_status=='NON_IDENTIFIABLE_PLATEAU')][['RAS','exact_inverse_low','exact_inverse_high']])}

Local slope and 0.01-RAS perturbation magnification are exported in `S7_local_inverse_resolution.csv`. Zero slope has no finite unique inverse; weak slope magnifies response error. A smooth model's point estimate does not resolve the empirical 90/100 overlap.

Uncertainty preserves the v3 policy: 1,000 within-level well bootstraps with paired-event and shared-control draws; the same control draw is shared with the inverse observation. Conditional quantiles report the fraction of bootstrap inverses available. No unavailable draw is clipped to 0 or 1. A separate envelope adds the 95th percentile of absolute leave-level response errors to bootstrap mean bands and is inverted as a set. These are exploratory compatibility sets, not calibrated coverage intervals. They omit preparation and independent batch uncertainty. The cross-model union is a further sensitivity bound, not a new probability statement.

## Independent-well and high-reference sensitivity
{md(sens[['model','scenario','reference_wells','input_min','input_max','maximum_abs_RAS_change_on_common_input']])}

These refits investigate dependence; they do not replace the primary 20-well fits. Removing corrected 90% can change isotonic predictions by about 0.062 RAS on the common domain, while the hinge changes by about 0.028. A/B-only fits provide a separate two-replicate sensitivity check. Omitting both high levels truncates support to 75%; a small within-range change does not demonstrate extrapolation beyond that range.

## RES status and domain
Every RES row includes original well/acquisition ID, input RAS, reporter population, model ID, corrected reference-basis ID, point or interval, bootstrap and compatibility uncertainty, label evidence status and applicable S7 domain. {int(res.RES_exploratory_mass_fraction.notna().sum())} of 60 model-by-well rows have unique model point inverses; this is not 60 independent samples and not 54 validated measurements.

{status_text}

No S10 population receives a qualified S7 RES. `S10_hypothetical_S7_mapping.csv` is an explicitly named arithmetic sensitivity with compatibility spans; its actual S10 RES status is `NOT_CALIBRATED`.
'''
    report('reports/Layer2_RES_Calibration.md',layer2)
    direct=read('results/prediction/S10_direct_model_results.csv');direct=direct[(direct.validation=='leave_one_dose_out')&direct.model.isin(['training_mean','reporter_RAS','B_detection_fraction','reporter_RAS_plus_B'])]
    l3=header+f'''# Layer 3 — biological calibration after S7 label correction

The S7 correction improves a reference-specific optical calibration. **It does not establish S7-to-S10 transfer, improve the observed direct RAS relationship, or validate PER.** No original S10 molecular measurements or direct predictive fits were recalculated.

The preserved S10 evidence remains: 523-bp independently reconstructed amplicon, provisional candidate C280 CGA→TGA, 47/48 site-eligible AB1 reads, 23 complete bidirectional molecular labels nested within 12 independent transfection wells, and dose-associated relative peak response. RNA extraction after flow and 1/2→A, 3/4→B are confirmed. The sampled cell population, DNA-residual exclusion and known-mixture molecular response calibration remain unqualified. The index is not an accurately measured RNA-edited fraction. Original methods/results remain in `OpenA_Amplicon_Reconstruction.md` and `S10_Sanger_Quantification.md`.

## Unchanged direct prediction
{md(direct[['model','well_n','RMSE','MAE','bias','prediction_interval_coverage']])}

These are leave-one-dose-out errors in raw chromatogram-index units, not RNA percentage errors. RAS-only remains worse than the training-mean baseline; B detection remains more predictive within this dose titration. Additional RAS does not improve B-only prediction. This pattern is not causal or externally validated. All same-well molecular reads remain grouped in the preserved folds.

## Transfer reassessment
{md(compat[['dimension','S7','S10','status']])}

Common HEK293T and detector profile do not resolve construct/reference identity, S7 reporter/total DNA loading, editor effects, treatment/timing or measured population. Reporter-selected S7, reporter-selected S10 and BFP-positive co-expression S10 are not assumed equivalent. The corrected-reference label uncertainty is an additional provenance condition, not a transfer bridge.

## Updated dependent computations
All 36 model-by-S10-reporter hypothetical mappings were recalculated with corrected calibration parameters and discrepancy envelopes; none is a validated S10 RES. Observed S10 reporter RAS lies in the less-resolved low S7 response region, below the common narrow interior screen. No S10 R+B+ score is assigned a transferred RES.

The affine-rescaling sensitivity was recomputed on the exact preserved direct-model folds. Its maximum prediction difference from direct affine RAS regression is {cs['maximum_affine_prediction_difference']:.3g}. A deterministic invertible affine rescaling adds no sample-level information. This is an algebraic check, not biological staged validation. A staged RNA/PER model remains unavailable because both transfer and absolute molecular-fraction qualification are missing. A better S7 fit cannot repair either issue.

Current limitation: **more defensible exploratory S7 mass-equivalent RES in a middle range; no additional validated RNA-editing prediction claim**. The preserved BFP comparison and the RAS–molecular discrepancy remain important integrated findings.
'''
    report('reports/Layer3_PER_Calibration.md',l3)
    zh=header+f'''# S7 标签更正后的科学结论

**结论：RES 的中间区间变得更有依据，但仍是依赖本次参考体系和标签解释的探索性估计；PER 尚未因此获得验证。**

实验人员回忆原标 75% 与 90% 的样本可能互换。依照你的明确授权，原 75A/B 现在按 90% 分析，原 90A/B 按 75% 分析；此前 10%→15% 的更正保留。所有原始文件、孔编号、荧光值、RAS、测序结果均未修改。这属于事后报告的可能标签颠倒，尚无同期独立记录证实。曲线变好只能说明更正后更符合模型，不能反过来证明标签一定错了。

**校准改善来自实际重算。** 仿射模型训练 R² 从 {aff.training_R2_original:.3f} 升至 {aff.training_R2_corrected:.3f}。留出整个 AC 水平时，仿射、单调和固定 50% 转折点分段模型的 RAS RMSE 分别为 0.0497、0.0400、0.0364；原先分别为 0.0934、0.1071、0.0980。分段模型现在最适合作为探索性的主要参考，单调模型用于揭示不可区分区间。在三模型共同能够反算的 {int(common.common_well_n.iloc[0])} 个留出孔中，分段模型的 AC 质量比例平均绝对误差约为 {100*common[common.model=='monotone_hinge_50'].MAE_mass_fraction.iloc[0]:.2f} 个百分点。这是同一次实验内的检验，不能写成跨批次准确度。

**可用区间有所扩大，但不是全范围可用。** 更正后 75%、90%、100% 的平均 RAS 为 0.9787、1.1322、1.1304。原来的 75%→90% 下降消失；90% 与 100% 仍无法由当前两孔重复可靠区分。低端 0–5%、15–20%、30–40% 也仍有重叠。不能因平滑模型能够反算一个数，就认为这些区间已经可辨。

保持上一版“兼容区间总宽度不超过 20 个 AC 百分点”的探索性标准，并要求单调/分段两模型都支持、区间不被 0/100% 边界截窄，得到主要连续 RAS 区间约 **{jr.RAS_low:.3f}–{jr.RAS_high:.3f}**。两模型的点估计大致覆盖 **{100*masslow:.0f}–{100*masshigh:.0f}% AC 质量输入当量**。这是可报告的、带不确定范围的参考等效量；20 个百分点是区间总宽度诊断阈值，不代表已验证的 ±10 个百分点准确度。不能称为已验证 RES，更不能当作 RNA 编辑百分比。

**S10 结论保持不变。** 已确认的 C280 相对峰图信号随 editor 剂量增加，但 RAS 预测该信号仍不优于均值基线；BFP 阳性比例的关联较强。更正 S7 标签没有改变这 12 孔的直接证据。S7 与 S10 的构建、DNA 负载、处理和细胞群体对应关系仍不充分，Sanger 峰比例也未完成绝对编辑率标定，因此不能将更正后的 S7 曲线直接转换为 S10 的已验证 RES 或 PER。

**Wiki 应突出三个结果：** 可追溯的标签更正使参考校准明显改善；逆校准明确揭示中间可估计、两端受限的范围；更好的光学校准并未自动带来分子编辑预测能力。Layer 0–1 的可复现测量与归一化证据保持原样，Layer 2 获得更强的局部探索性定量解释，Layer 3 的分子响应证据与预测局限均应保留。

更高等级的定量结论仍需要可追溯的独立混合参考、盲法验证和更多批次，以及相匹配的分子定量与细胞群体证据。此次已经完成当前数据能支持的重拟合、验证、逆估计与敏感性分析。
'''
    report('SONAR_S7_Correction_Scientific_Summary_ZH.md',zh)
    report('SONAR_Layer23_Scientific_Summary_ZH.md',header+'# 当前中文科学摘要\n\n请阅读 [S7 更正后的完整中文摘要](SONAR_S7_Correction_Scientific_Summary_ZH.md)。原 v3 摘要保存在 `baselines/v3/`。\n\n'+zh.split('# S7 标签更正后的科学结论\n\n')[1])
    evidence=header+'# SONAR corrected Layer 2–3 scientific evidence\n\n'+comparison.split('# Original versus corrected S7 calibration\n\n')[1]+'\n\n'+l3.split('# Layer 3 — biological calibration after S7 label correction\n\n')[1]+'''\n\n## Evidence and reproduction
The full incremental run restores only verified frozen upstream data, applies versioned metadata, refits all three reporter calibrations, reassesses inverses and transfer, updates dependent sensitivities and renders affected figures. The archived v3 analysis was independently rerun first. Current reproducibility results and preserved-file hashes are in `reports/reproducibility_record.json` and `reports/S7_correction_unaffected_hashes.csv`.

The corrected manifest, reference-response tables, models, fold memberships, inverse sets, sensitivity refits and source-linked diagnostic figures are included. No external experimental measurements or simulated validation samples were introduced. The previous v3 scientific outputs remain available under `baselines/v3/`; its original complete ZIP remains unchanged.
'''
    report('SONAR_Layer23_Evidence_Report.md',evidence)
    old=(BASE/'SONAR_Measurement_Evidence_Report.md').read_text();earlier=old[old.index('## Layer 0:'):old.index('## Layer 2:')]
    report('SONAR_Measurement_Evidence_Report.md',header+'# SONAR Integrated Measurement Evidence — corrected S7 reference\n\nLayer 0–1 measurements remain unchanged. Layer 2 now supports more precise, conditional reference-specific middle-range RES. Layer 3 retains a measured relative molecular signal but no validated PER. The label correction is retrospective and not independently verified.\n\n'+earlier+'\n## Layer 2: corrected reporter calibration\n\n'+comparison.split('## Quantitative result\n')[1].split('## What disappeared')[0]+'\n'+boundary+' No RES is classified VALIDATED_WITHIN_DOMAIN. See [Layer 2 methods](reports/Layer2_RES_Calibration.md) and [before/after evidence](reports/S7_Calibration_Before_After_Comparison.md).\n\n## Layer 3: unchanged molecular evidence and updated transfer assessment\n\nDirect RAS-to-chromatogram-index prediction and BFP comparisons remain numerically unchanged. The recalculated hypothetical affine staged predictions equal direct predictions to numerical precision, and actual S7-to-S10 transfer remains unqualified. No absolute RNA fraction or PER is established. See [Layer 3 report](reports/Layer3_PER_Calibration.md).\n\n## Scientific handoff\n\n[Chinese summary](SONAR_S7_Correction_Scientific_Summary_ZH.md), [full corrected evidence](SONAR_Layer23_Evidence_Report.md), [correction provenance](reports/S7_Label_Correction_Record.md), and [figure inventory](SONAR_Layer23_Figure_Evidence_Inventory.md). Reproduction status is recorded in `reports/reproducibility_record.json`; it is computational reproducibility, not independent experimental validation.')
    # Replace affected figure evidence; preserve captions/source hashes for unchanged measurements.
    fig=read('figures/layer23/figure_index.csv');extra=read('figures/correction/figure_index.csv');combined=pd.concat([fig,extra],ignore_index=True)
    findings={'L23_07_S7_models':'Corrected leave-level RMSE: affine 0.049716; isotonic 0.040048; hinge 0.036368','L23_08_S7_residuals':'All 20 unchanged measurements retained; high 90/100 overlap remains','L23_09_inverse_uncertainty':boundary,'L23_10_reference_anomaly':'Corrected means at 75/90/100%: 0.978722 / 1.132248 / 1.130373','C01_original_corrected_response':'Only four original AC assignments change; 20 RAS values identical','C02_model_comparison':f'Affine R² {aff.training_R2_original:.6f} to {aff.training_R2_corrected:.6f}; hinge now lowest leave-level RMSE','C03_cross_model_inverse_support':boundary,'C04_S10_unqualified_mapping':'36 arithmetic mappings recalculated; zero qualified S10 RES','F04_S7_normalization':'Same raw/corrected green means and RAS; corrected AC axis'}
    prior=read('baselines/v3/reports/layer23/figure_evidence_inventory.csv').set_index('figure_id')
    combined['numerical_findings']=combined.figure_id.map(lambda n:findings.get(n,prior.loc[n,'numerical_findings'] if n in prior.index else 'See source table'))
    table('reports/layer23/figure_evidence_inventory.csv',combined)
    report('SONAR_Layer23_Figure_Evidence_Inventory.md',header+'# Current figure evidence\n\nFive affected figures were regenerated; four new correction diagnostics were added. All other measurement plots retain original bytes. Figure captions state scientific limits.\n\n'+md(combined[['figure_id','source_tables','numerical_findings','caption']]))
    report('SONAR_Figure_Evidence_Inventory.md',header+'# Integrated figure routing\n\nLayer 0–1 figure F04_S7 uses corrected inputs; other original figures remain unchanged. The canonical acquisition IDs in F03 are raw identifiers, not current AC labels.\n\n'+md(read('figures/figure_index.csv')[['figure_id','source_tables','caption']])+'\n\nFor corrected calibration and molecular figures see [current Layer 2–3 figure inventory](SONAR_Layer23_Figure_Evidence_Inventory.md).')
    blockers=read('baselines/v3/reports/layer23/blocker_resolution.csv');sel=blockers.blocker=='S7 75/90 reversal';blockers.loc[sel,['action','result','resolution','remaining_limit','consequence']]=['Applied team-authorized retrospective label transposition; refit and revalidated all models','Major reversal disappears; internal prediction improves; 90/100 and low overlaps remain','CORRECTED_BY_USER_AUTHORIZATION_NOT_INDEPENDENTLY_VERIFIED','No contemporaneous independent preparation evidence or external validation','Middle-range exploratory RES becomes more defensible; no validated transfer or PER'];table('reports/layer23/blocker_resolution.csv',blockers)
    report('SONAR_Layer23_Blocker_Resolution.md',header+'# Current blocker-resolution register\n\nOnly the label-associated calibration evidence changes. Molecular and optical experimental evidence remains as audited in v3.\n\n'+md(blockers))
    decisions=read('baselines/v3/reports/decision_registry.csv');decisions.loc[decisions.decision_id=='D07',['status','evidence_or_limit']]=['corrected_exploratory_calibration','Retrospective 75/90 correction applied; hinge preferred by leave-level error; middle-range inverse support improved, no validated RES'];decisions['analysis_version']=VERSION;table('reports/decision_registry.csv',decisions)
    ev=read('baselines/v3/reports/evidence_register.csv');ev.loc[ev.evidence_id.isin(['E04','L23_03']),['status','claim','calibration_id','limitations']]=['exploratory','Corrected reference calibration improves middle-range conditional RES',VERSION,'Retrospective labels; low/high overlap; no externally validated accuracy'];table('reports/evidence_register.csv',ev)
    for name in ['SONAR_中文科学摘要.md']:
        p=BASE/name
        if p.exists():report(name,'> Historical summary. Current corrected findings: [中文摘要](SONAR_S7_Correction_Scientific_Summary_ZH.md).\n\n'+p.read_text())
    report('README.md',header+'''# SONAR S7/S10 — corrected v4 release

Start with [中文科学摘要](SONAR_S7_Correction_Scientific_Summary_ZH.md), [before/after calibration](reports/S7_Calibration_Before_After_Comparison.md), [full scientific evidence](SONAR_Layer23_Evidence_Report.md), and [integrated four-layer report](SONAR_Measurement_Evidence_Report.md).

The team-authorized probable 75/90 transposition is applied to primary S7 metadata. Original names/IDs and all event-level and molecular measurements remain intact. The earlier 10→15 correction is retained. Better agreement is not independent proof of transposition.

Run `python reproduce.py --verify` with Python 3.13 and the pinned packages in `requirements.txt`. On this host the prepared interpreter is `_work/venv/bin/python`; `_work` is not distributed. The v4 command uses the reproduced archived v3 upstream artifacts, applies the correction, refits all three S7 models, evaluates inverses/sensitivity/transfer, updates calibration-dependent S10 arithmetic, generates affected figures, and runs tests. `--verify` repeats the complete incremental analysis in an isolated directory, checks outputs and confirms preserved hashes. It does not rerun FCS gates, Sanger processing or direct molecular fits. The archived v3 code and its prior baseline verification permit those original analyses to be rerun separately.

Current manifests are `inventory/acquisition_manifest.csv` and `inventory/S7_corrected_manifest.csv`. The immutable `results/ras_results.csv` retains historical label columns; current calibration joins its acquisition IDs to `results/calibration/S7_reference_response_corrected.csv`. Do not infer current AC fraction from raw filenames or the frozen RAS label column.

Outputs: `results/calibration/` contains corrected response, fits, fold predictions, R²/errors, inverse uncertainty, local slopes, independent-well/high-level sensitivity and before/after comparisons. `models/layer23/S7_calibration_models.json` contains v4 model IDs and provenance. Unchanged S10 direct models intentionally retain v3 provenance. `results/prediction/` contains those preserved measurements/direct validations plus updated, explicitly hypothetical affine sensitivity. `figures/correction/` holds four new diagnostics; only five existing plots were affected. `reports/` contains methods, provenance and actual reproducibility records.

`baselines/v3/` preserves the prior scientific code, configuration and outputs extracted from the original complete v3 ZIP, whose path/hash are recorded in `archive_provenance.json`. Raw inputs are shared unchanged, avoiding a redundant copy. Earlier v2 is also retained. Absolute RNA fractions/PER remain unqualified; corrected S7 RES is exploratory and reference-specific. All source/configuration/output hashes accompany this release.
''')
    print('Corrected scientific reports, Chinese summary and integrated evidence generated',flush=True)

if __name__=='__main__':run()
