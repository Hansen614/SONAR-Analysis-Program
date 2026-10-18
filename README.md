## Desktop candidate (1.4.0rc1)

SAP has self-contained desktop candidates for Apple Silicon macOS and Windows x64. No separate Python installation is required. See [installation notes](packaging/INSTALL.md) and [build instructions](packaging/README.md). Windows candidates are available from the [successful GitHub Actions run](https://github.com/Hansen614/SONAR-Analysis-Program/actions/runs/39100443668) under **SAP-windows-x64-candidate** (repository access required). Extract the downloaded artifact and then fully extract `SAP-1.4.0rc1-windows-x64-portable.zip`; open `SAP/SAP.exe` and keep the entire SAP folder together. These are unsigned/ad-hoc-signed candidates, not a public signed release. Intel Mac remains unbuilt.

# SONAR Platform 1.3.1

本地流式测量平台：**Layer 0 Θ → Layer 1 RAS → Layer 2 RES**。

## 启动

双击上层 `启动 SONAR.command`，或本目录 `start.command`，打开 http://127.0.0.1:8765/#home 。保持启动终端运行；Ctrl+C 停止服务。

```sh
.venv/bin/python -m sonar_app serve --open
```

当前电脑已配置 Python 3.13.7 和锁定依赖。新电脑在本目录运行 `bash install.sh`；安装可能需要网络，之后计算和界面可离线运行。其他操作系统/架构未验证。

## 界面

- **分析工作台**：新建实验、分步计算与实验记录。
- **数据源**：参考样本、背景与门控、参考标尺，使用独立导航。

表单统一尺寸与对齐；上传文件通过选择按钮或拖放添加。保存路径、通道映射、计算设置和技术参数按需展开。数据源与工作台之间切换会保留当前实验草稿。窄窗口自动切换为横向导航。

## 实验流程

1. **开始一次实验**：填写名称并选择保存文件夹。平台创建唯一实验子目录，不覆盖已有实验。
2. **Mock 环节**：上传至少一个同批次 Mock FCS。需要时展开“高级选项”，填写细胞类型、实验备注或修改自动匹配的通道。此时不需要实验组文件。
3. **Layer 0 结果**：查看门控、背景与阈值，点击“确认并继续”。
4. **实验组计算**：上传实验组文件，直接复用已确认的 Θ，计算 RAS / RES。“高级选项”中可填写 Reporter 和样本条件，修改计算群体、RES 标尺与重采样次数；默认 reporter 群体、内置参考标尺、200 次 Bootstrap。
5. **总结果**：查看逐样本结果和诊断。原始输入、Θ、CSV、HTML、报告 ZIP 自动保存，也可从界面下载。

高级选项默认收起。细胞类型和 Reporter 默认“未填写”，均为可选信息；实验备注默认留空，随实验、总结果及报告保存，不参与数值计算。同一浏览器会话中的未提交字段保留草稿。实验记录可恢复已保存阶段；修改 Mock、通道或细胞身份后需要重新分析和确认 Θ。缺少输入会明确说明原因。

## 测量定义与支持范围

- Θ 是参数集合。首个 Mock 拟合门控，全部 Mock 估计背景和阈值。一个 Mock 可建立研究 Θ，但缺少独立控制；参与拟合的多个 Mock 也不能同时视作独立阈值验证。
- RAS 是同一选中群体的配对线性校正 EGFP / mCherry 求和比 `ΣG / ΣR`，保留负校正值。事件支持不足或分母不可靠时保留不可估计状态。缺失 BFP 不补零。
- RES 是 AC DNA 质量参考等效分数，存储为 0–1，界面显示百分数。内置标尺用于新 Θ 时为跨批次未验证模型估计；模型域外不外推、不截断。独立参考拟合至少需要 3 个质量比例水平，每水平至少 2 个独立孔，并保留失败的验证结果。研究区间未经名义 95% 覆盖率验证。
- FCS 支持线性、gain=1、未补偿、无 spillover 或 identity spillover 的导出。非 identity 补偿和不一致的采集设置会拒绝；不同仪器或面板不会自动取得适用资格。
- 每文件最多 128 MiB，每实验最多 128 文件、总计 600 MiB。必需 FSC-H/A、SSC-H/A、Time、EGFP、mCherry；BFP 可选。默认文件名作为孔标识不证明生物独立性，需按实验实际核对。
- 服务仅监听本机 loopback，供单用户使用。

## 保存与复现

默认实验位置为 `workspace/experiments/`，也可选择其他本机文件夹。每个实验目录包含：

- `experiment.json`：阶段、文件清单、身份与已确认的 Θ 哈希。
- `inputs/mock/`、`inputs/sample/`：原始 FCS 副本。
- `layer0/`：Θ、Mock 掩码及文件哈希。
- `analyses/analysis-*/`：每次完整计算的原始输入、掩码、Θ、模型、结果与配置。
- `measurements.csv`、`report.html`、`SONAR_report.zip`：最近一次成功计算的汇总与报告。

从界面移除的原始文件和既有计算记录保留在磁盘。上游变化会清除当前阶段的结果资格；根目录汇总代表最近一次成功计算，当前进度以 `experiment.json` 为准。`workspace/experiments_index.json` 登记各实验保存位置。

解压报告包后，在同版本和锁定依赖环境中重算：

```sh
.venv/bin/python -m sonar_app pipeline-rerun /absolute/path/to/report --output rerun.json
.venv/bin/python -m sonar_app verify
```

新版读取旧分析时按当前测量范围呈现，旧分析原件不被改写；重新导出的结果和清单哈希保持一致。已确认的 Θ 继续有效。

## 实现与发布

`experiments.py` 管理实验阶段；`measurement.py` 管理面向用户的测量输出；`pipeline.py` 和原始 `scientific_reference/` 保留数值算法与既有身份。界面文件位于 `sonar_app/static/`。

`build_backend.py` 构建 `dist/sonar_platform-1.3.1-py3-none-any.whl`；`package_app.py` 构建上层 `SONAR_Platform_1.3.1.zip`，排除环境、工作区与实验目录。产品范围见 `PRODUCT_SCOPE.md`，实际验证见 `verification/QA_REPORT.md`。


## Reporter 设计模块

在顶部选择“设计”。上传单条 FASTA / TXT 或粘贴 DNA / RNA，输入目标 C 的 1-based 坐标；序列须按转录本 5′→3′ 方向提供。默认识别区 12 nt、间隔 2 nt，均可在高级选项修改。定位依赖这些设置，不是对编辑器结合范围的预测。

确认页显示原始截取与建议插入序列。靶 C 固定为 reporter 目标密码子的第 1 位，保留后方 2 nt；必要时从识别区前方再取 0–2 个真实碱基补齐读框（默认取 1 nt）。靶密码子的改造必须经用户确认。未指定原转录本 CDS 读框，不把 reporter 适配称作原蛋白的同义改造。

两条 WT oligo 使用 RP01 的 CAGC / TGCC 接口，均按 5′→3′ 输出。支持复制、订单 CSV、完整拼接质粒 FASTA 和含输入/设置/改动/来源的 JSON。检查完整拼接载体及模拟编辑后的读框、终止与 BsaI 位点；参考载体为用户提供的 `Reporter/序列/Universal_Reporter_Package.zip` 中的 `Universal_Reporter_EV.gb`（7,498 bp），不能替代实体克隆的序列确认。程序不改写识别区，也不生成未经用户确认的适配结果。

所有设计计算在本机浏览器完成。输入在当前页面会话的模块切换间保留；刷新会清空设计，请使用 JSON 保存结果。模块未更改流式计算引擎。实现：`reporter-engine.js`、`reporter-vector.js`、`reporter-designer.js/css`。运行 `node tests/reporter_design.cjs` 可复核序列测试；无需额外依赖。


## Reporter 构建页面

“设计 → Reporter 构建”提供用户整理的 Universal Reporter CDS（2,022 bp 线性编码序列）与 Plasmid（7,498 bp 环状 reporter 质粒），均有 GenBank / SnapGene 下载。下载名使用 `Universal_Reporter_Plasmid`；包内原名 `Universal_Reporter_EV` 仅保留在来源记录中，文件内容不变。CDS 与质粒的 1119–3140 位完全一致；已核对包内三种序列格式、注释坐标、完整载体仅保留 2617 / 2648 两个 BsaI 位点及 CAGC / GGCA 接口。文件属于计算设计，内含子调整的剪接或表达功能未验证。原 2,027 / 4,669 bp 文件已移出应用下载区；项目源文件保留。

网页插入步骤转写自维护中的 `Protocols/RP02`（v1.0，2026-10-13），保留短双链适配起始方案的边界，附原 PDF 下载。下载副本与源文件的哈希保存在 `sonar_app/static/downloads/construction_manifest.json`。正式 protocol 仍只在 `Protocols/` 维护；源包更新后运行 `.venv/bin/python tools/refresh_construction_assets.py` 同步下载镜像与设计参考，并核对网页转写内容。原 RP02 PDF 的 4,669 bp 示例保持原文；网页按 7,498 bp 质粒 将 75 ng 换算为约 15.2 fmol，沿用约 114 fmol 插入起始量时比例约 7.5∶1，不代表条件已优化。五个下载路径通过明确白名单提供，不开放任意本地文件路径。

卡片使用包内 SVG 图谱，点击可放大，支持缩放、适合窗口、Esc / 关闭按钮 / 遮罩关闭；质粒图仅将 EV 标签同步为 Plasmid，其余图谱内容不变。图谱来源与修改记录纳入 `construction_manifest.json`，并由刷新工具同步。
