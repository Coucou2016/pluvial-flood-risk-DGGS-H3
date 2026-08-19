# W6 文本上下文包 · 图码对应清单 + 评审问题（2026-08-19）

> 用途：粘贴给 ChatGPT（OpenAI）的第 6 轮协作文本包。图与 `manuscript.md` 由用户手动上传；本包提供图↔码↔数据的三方对应，以及本轮评审问题。
> 注意：为符合 ChatGPT 阅读能力，本包**仅含文本**。图片本体请用户手动上传（GitHub 直链曾被 ChatGPT 端限制，见 R22 记录）。

---

## 0. 上一轮状态（W5，已签收）

W5 已正式 sign-off：W4 的全部条件项闭环（0.9-quantile ties、Sandy observed flood-risk score、fold-local standardisation、uncertainty 公式、AP 定义、H3 层级术语）。W6 起新增工作完全来自用户新要求：**对照参考论文（Svellingen et al. 2026 IJDRR）补齐图/表类型与数量**。

## 1. 本轮变更摘要（W6，仅新增图表，未改科学结论）

- 图从 4 张扩展到 **6 张**：新增 **Fig 2 空间结果图**、**Fig 5 分辨率效应图**。
- 表格从 0 张扩展到 **6 张**：数据层（表1）、模型规格（表2）、空间 CV 汇总（表3）、尺度损失阶梯（表4）、自适应单元数（表5）、Sandy 负对照（表6）。
- 结果小节重排为 §4.1 空间模式（新）→ §4.2 空间 CV → §4.3 尺度损失 → §4.4 自适应 → §4.5 降雨情景 → §4.6 Sandy → §4.7 扩展试点。
- 方法与结论、全部数值未变。

## 2. 六张图 ↔ 生成代码 ↔ 数据文件 三方对应

| 图 | 内容 | 生成函数（`src/pluvial_flood_risk/figures.py`） | 数据文件（live，非拷贝） |
|----|------|------------------------------------------------|--------------------------|
| Fig 1 | 概念工作流（4 列：开放输入→H3 组装→学习与分块评价→诊断输出；Sandy 虚线旁路） | `plot_workflow_schematic` | 无（概念图，非数据图） |
| Fig 2 | 空间结果图（Lower Manhattan，n=141，三面板同支撑：(a) 观测开放标签分；(b) 空间 CV 留出概率；(c) PFI_h(c,r) ida_like；DEM 灰底 + NHDPlus 水系） | `plot_spatial_maps`（新增） | `data/processed/nyc_h3_cells.parquet`（观测）；`models/nyc_smoke/spatial_cv_oof_predictions.csv`（留出）；`outputs/pfi_h_scenarios.parquet`（PFI_h，scenario=ida_like）；`data/raw/nyc/dem.tif`；`data/raw/nyc/hydro_streams.geojson` |
| Fig 3 | 空间 H3 块 CV 各折 Accuracy/F1（配对标记 + Mean±SD） | `plot_spatial_cv_bars` | `models/nyc_smoke/spatial_cv_folds.csv`；`models/nyc_smoke/spatial_cv_oof_predictions.csv` |
| Fig 4 | Jaccard/F1 尺度损失阶梯（R10→R9/R8，mean/max/p90 上卷） | `plot_jaccard_ladder` | `outputs/jaccard_by_resolution.csv` |
| Fig 5 | 分辨率效应：(a) 开放标签分 R10(n=991)/R9(n=160)/R8(n=31) 小提琴；(b) Jaccard 热点持久性矩阵（q=0.9） | `plot_resolution_effects`（新增） | `data/processed/nyc_h3_cells_r10_labels.parquet`（991 R10），R9/R8 由 `h3.cell_to_parent` mean 上卷 |
| Fig 6 | 自适应消融：Fixed R9(141) / Adaptive(3933) / Uniform R11(6909)；27.9× / 56.9% | `plot_adaptive_ablation` | `outputs/adaptive_vs_fixed_ablation.csv` |

## 3. 本轮数值复核（全部从 live 文件重算）

- Fig 5b：J(R10,R9)=0.977、J(R10,R8)=0.167、J(R9,R8)=0.167；单元数 991/160/31。与 `jaccard_by_resolution.csv` 的 mean 行完全一致。
- Fig 2：三面板共享支撑 n=141；两两 Pearson：obs~oof=0.245、obs~pfi=0.468、oof~pfi=0.509。
- Fig 6：3933/141=27.9×、3933/6909=56.9%。

## 4. 对照参考论文图类型检查

| 参考论文图 | 类型 | 本项目 | 状态 |
|-----------|------|--------|------|
| Fig 1 概念工作流 | 流程图 | Fig 1 | 已覆盖 |
| Fig 2 H3 分辨率色标 | 概念图 | 以 Fig 1+Fig 5 覆盖 | 不复制其 5 级 PFIb 校准色标（避免等同声明） |
| Fig 3 PFI_b→PFI_h 转换 | 空间图 | Fig 2 三面板 | 已覆盖 |
| Fig 4 多分辨率空间图 | 空间图 | Fig 2（R9 单一支撑） | 已覆盖（不伪造 R6/R8/R10/R13 多分辨率） |
| Fig 5a 分辨率分布 | 统计 violin | Fig 5a | 已覆盖 |
| Fig 5b Jaccard 矩阵 | 统计 heatmap | Fig 5b | 已覆盖 |
| Fig 6 流域 vs H3 | 空间对比图 | **未做**（无 HUC-12 数据） | 待补充/如实缺项 |

## 5. 请 ChatGPT 评审的问题（W6）

1. **Fig 2 空间结果图**：三面板同支撑是否合理？观测面板是二元化的 0/1（证据有无），与 (b)(c) 连续色标共用 0–1 色标是否会引起误导？DEM 灰底 + 水系浅蓝是否影响六边形辨识度？颜色映射 viridis 是否适合 0/1 高度偏态数据？
2. **Fig 5 分辨率效应图**：(a) 小提琴在 n=31 的 R8 上是否稳健；(b) 对称矩阵的 J(R9,R8)=J(R10,R8)=0.167 是否为巧合、是否需要在 caption 说明；是否应加 R6/R7 行（会退化为全 1）？
3. **表体系**：6 张表是否足够/是否有一张多余或缺失？表 3 的 SD（ddof=0）是否需要 footnote？
4. **图号与正文引用**：Fig 1–6 引用顺序是否自然（正文首次出现顺序 1,2,3,4,5,6）？
5. **写法残留检查**：图注是否有"研究总结/AI 辅助整理稿"气质的句子需要 humanize？（具体到句子）
6. **创造性定位**：新增"空间结果图 + 分辨率效应统计图"是否强化了"H3 作为共同空间支撑"的主叙事，还是只增加图表数量？有无更聚焦的呈现方式？

## 6. 上传清单（用户手动上传到 ChatGPT）

1. `docs/paper/figures/spatial_maps.png`
2. `docs/paper/figures/resolution_effects.png`
3. `docs/paper/manuscript.md`（最新版，含 6 图 6 表）
4. （可选）`src/pluvial_flood_risk/figures.py` 中 `plot_spatial_maps` 与 `plot_resolution_effects` 两段源码

GitHub 仓库（已推最新代码与文档，供 ChatGPT 读取）：https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3
