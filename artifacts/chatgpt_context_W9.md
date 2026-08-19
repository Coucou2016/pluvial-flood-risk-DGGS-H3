# W9 评审请求（2026-08-20）：参考论文图类型对照 + 图质量终审

## 背景
你上一轮（W8）已对科学内容与图表一致性 sign-off，并给出 3 个投稿前 blocking 项。本轮按用户最新指令聚焦一个此前未充分覆盖的维度：**把参考论文 PDF 中的 6 张图逐一看清，并与我方 6 张图做"图类型 / 图数量 / 图质量"三方面对照**，判断我方是否已对齐参考论文的图体系（用户明确要求"参考论文画了哪几张图、什么类型，我也要画什么类型"）。

## 本轮注入文件（共 16 个）

### A. 参考论文 6 张图（从 1-s2.0-S2212420926001032-main.pdf 提取的原始嵌入图，命名 img_pXX_XX.png）
| 文件 | 对应参考论文图 | 内容 |
|---|---|---|
| img_p04_00.png | Fig. 1 | 方法工作流：PFIb 三层特征提取 + Random Forest 训练示意 |
| img_p05_00.png | Fig. 2 | H3 概念：a) 父子七分 b) 分辨率 Micro/Meso/Macro c) 5 级配色 Very Low→Very High |
| img_p06_00.png | Fig. 3 | PFIb→PFIh 转换：a) 建筑级点 b) 六边形聚合 |
| img_p07_00.png | Fig. 4 | 多分辨率空间图：R6/R8/R10/R13 纽约四面板 |
| img_p07_01.png | Fig. 5 | 高阶统计：a) R6-R13 violin 分布 b) Jaccard 热点持续热力图 |
| img_p09_00.png | Fig. 6 | 流域 vs H3 空间对比：a) HUC-12 子流域 b) H3 R9 c) H3 R11 |

### B. 我方 6 张图（docs/paper/figures/，已按 190/140 mm 重渲染）
1. workflow_schematic.png（Fig.1 方法工作流）
2. spatial_maps.png（Fig.2 空间结果：observed / OOF / PFI_h 三面板）
3. spatial_cv_folds.png（Fig.3 空间 H3-block CV 折线）
4. jaccard_by_resolution.png（Fig.4 Jaccard/F1 阶梯）
5. resolution_effects.png（Fig.5 a) violin b) Jaccard 热力图）
6. adaptive_ablation.png（Fig.6 自适应细化 cell count）

### C. 文本文件
- manuscript.md（W8 修复后最新，6 图 6 表）
- audit.md（含 §8.7 W8、§8.8 tag 记录）

## 请按 A/B/C 三部分回答（中文，结构化，给出可落地 diff）

### A. 图类型 / 图数量对照
1. 逐张对照：参考论文 6 张图各自属于什么"图类型"（示意/概念/空间结果/空间对比/高阶统计），我方是否有对应类型？逐一给"已对齐 / 部分对齐 / 缺失"判定。
2. 我初步判断的差异点，请你验证或推翻：
   - 参考 Fig.2（H3 父子/分辨率/配色概念图）在我方无独立图，只融入 Fig.1 和文字 —— 是否需要补一张独立 H3 概念图？
   - 参考 Fig.4（R6/R8/R10/R13 多分辨率空间并排图）在我方缺 —— 但我方 Fig.5 用 violin+Jaccard 覆盖了"分辨率效应"，且我方科学贡献不同（有空间CV、有自适应细化）。是否仍需补一张"多分辨率 open-label 空间并排图"以对齐图体系？
   - 参考 Fig.6（流域 vs H3 空间对比）在我方缺 —— 我方 Fig.6 是自适应细化 cell count。是否需补"流域/行政区 vs H3 空间对比图"？
3. 关键约束：**只能使用我方现有真实产出数据**（`data/processed/nyc_h3_cells.parquet`、`nyc_h3_cells_r10_labels.parquet`、`models/nyc_smoke/spatial_cv_oof_predictions.csv`、`outputs/pfi_h_scenarios.parquet`、`outputs/jaccard_by_resolution.csv`、`outputs/adaptive_vs_fixed_ablation.csv`），**不得臆造数据**。请判断：哪些"缺失图"能用现有数据真实补出？哪些不能（需诚实说明为何缺、是否用文字表述替代）？
4. 若某图能补且值得补，给出该图的最小可行设计（面板数、每面板变量、数据来源文件、视觉编码），并说明它会放在 manuscript 哪一节、引用编号如何排。

### B. 图质量终审（我方 6 张图）
5. 逐一检查我方 6 张图在 190/140 mm 目标宽度下的可读性、配色、图注（legend/colorbar）一致性、panel 标注 (a)(b)(c)、字体（Times New Roman、≥7pt）。
6. 特别关注 Fig.2（三面板空间图）与 Fig.5（双面板统计图）在双栏 190 mm 下的实际观感；Fig.1（工作流）紧凑重排后是否有文字溢出/拥挤。

### C. 结论
7. 给一个明确的"图体系是否达标"判定：我方 6 图 + 6 表是否已充分对齐参考论文的图类型体系？还缺什么？按 MUST-FIX / 建议 / 可选 分级输出。

## 约束
- 不改变科学内容、结果、核心结论与全部数字。
- 只做图体系对齐、图质量、写作/排版/投稿体例。
- 每条建议给出精确可落地内容（图设计、代码改动点、或 manuscript 文字位置）。
