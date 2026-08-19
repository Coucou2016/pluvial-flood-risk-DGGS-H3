# W8 文本上下文包 · GitHub 直读 + 投稿体例收尾（2026-08-19）

> 用途：粘贴给 ChatGPT（OpenAI）的第 8 轮协作文本包。本轮按用户最新指令，把**最新 GitHub 链接**交给 ChatGPT 读取全部相关内容并反馈；同时注入关键文件（文本经 PNG 编码、图片直接注入）以防浏览端抓取限制。
> 本轮聚焦 ChatGPT W7 回复 §6 自提的三个 W8 方向：**① 全文 defensive prose 最后一次 sweep；② 最终 PDF 版面审阅；③ submission-package 一致性**。

---

## 0. 上一轮（W7）结论与落实

ChatGPT W7 对 W6 修复做了独立复核（直接解码 OOF CSV 与两个 parquet 重算 §4.1 统计量，全部与 manuscript 一致），并给出 4 项 MUST-FIX + 6 项 optional。**全部已落实并推送到 GitHub**：

| 项 | 内容 | 状态 |
|---|---|---|
| M1 | §3.5 删除对 Fig. 5 的提前编号引用，恢复 Fig 1→6 首现顺序 | 已改 |
| M2 | §4.1 "These correlations"→"This correlation" | 已改 |
| M3 | §4.1 改写 "any positive evidence…lifts the score" → 精确描述 fractional polygon-overlap / point-presence | 已改 |
| M4 | Fig. 5(b) 面板标签 (b) 改白色 | 已改 |
| O1–O6 | Fig.1/2/5 caption 人类化、synthetic Ida-like、Fig.5(a) 内部 mean/extrema 说明、PFI_h mathtext、Table 3 ddof 去重 | 已改 |

当前 master = `bb5f6af`，paper-v1 tag 已存在。

## 1. 本轮 GitHub 链接（请读取全部相关内容）

**仓库主页：** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3

**关键文件 raw 直链（若浏览端可抓取）：**
- 手稿：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/manuscript.md
- 审查文档：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/audit.md
- 出图代码：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/src/pluvial_flood_risk/figures.py
- 图 1（工作流）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/workflow_schematic.png
- 图 2（空间结果）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/spatial_maps.png
- 图 3（空间 CV）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/spatial_cv_folds.png
- 图 4（Jaccard 阶梯）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/jaccard_by_resolution.png
- 图 5（分辨率效应）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/resolution_effects.png
- 图 6（自适应 vs 均匀）：https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/figures/adaptive_ablation.png

> 若以上直链抓取受限（历史上曾 0/13 失败），请直接使用**注入到本会话的文件**（manuscript.md / audit.md / figures.py / 参考论文 md / 两张 PNG）。

## 2. 本轮注入文件（8 个）

1. `manuscript.md`（W7 修复后最新版，6 图 6 表）
2. `audit.md`（含 §8.5 W6 修复记录、§8.6 W7 复核与修复记录）
3. `figures.py`（完整源码，全部 6 图函数）
4. `1-s2.0-S2212420926001032-main.md`（参考论文：Svellingen et al. 2026 IJDRR 全文文本，用于写法/篇幅/逻辑对照）
5. `spatial_maps.png`（图 2，W7 修复后）
6. `resolution_effects.png`（图 5，W7 修复后）
7. `report.md`（研究报告中英文版）
8. `chatgpt_context_W7.md`（上一轮上下文包，供对照）

## 3. 请 ChatGPT 复核的问题（W8）

### A. Defensive prose 最后一次 sweep（W7 自提方向 1）
1. 逐节找出仍带「研究工作总结 / 审稿答辩 / AI 辅助整理稿」气质的句子，尤其是含 `not / do not / does not / are not / cannot / never / must not / without` 密集的段落（Abstract、§4.1、§4.4、§5.1、§5.3、§5.4、Fig. 5 caption）。
2. 对每一处给出**句子级替换建议**：把「防御式否定」改写为「正向 factual 陈述」，但**不改科学内容、结果、核心结论、数字**。
3. 特别检查：哪些 `not` 是**必须保留的科学诚实声明**（如 not a reproduction、never used as training label），哪些是**可转正的技术说明**（如 Random splits are not primary）。
4. 给出最终「保留 vs 改写」清单，按高/中/低优先级排序，最多 20 条。

### B. 最终 PDF 版面审阅（W7 自提方向 2）
5. 参考论文的图表排版规范（图幅、字体、caption 位置、表格样式），对照本稿 6 图 6 表逐一检查：
   - 图：物理尺寸是否适合单栏/双栏；字号在图内是否可读；三面板 Fig.2 与双面板 Fig.5 的实际渲染尺寸。
   - 表：Table 1–6 是否会在投稿页宽内换行/溢出；caption 是否完整落在表前。
   - 给每个图/表一条「版面建议」（若已达标则明说达标）。
6. 检查图号/caption 与正文引用是否一一对应（Fig 1–6、Table 1–6），以及 figure PDF 文件名与 manuscript 编号的对应关系。

### C. submission-package 一致性（W7 自提方向 3）
7. 对照 IJDRR 投稿体例检查：Abstract、Keywords、Highlights（当前**缺失**）、CRediT（当前为显式 placeholder「待补充」）、Funding、Declaration of competing interest、Data availability、Declaration of Generative AI、References 编号与格式。
8. 若 Highlihts 必要，请给 3–5 条候选（每条 ≤85 字符，符合 IJDRR 要求），基于现有科学内容提炼，不得新增未做的工作。
9. 检查数据/代码可用性声明与仓库实际内容是否一致（如 paper-v1 tag、download manifest、版本号）。

### D. 回归确认
10. 最后确认：W7 的 4 MUST-FIX + 6 optional 在注入的最新 manuscript.md / figures.py / PNG 中是否都已正确落地、无新回归。

## 4. 约束（与历史各轮一致）

- **不改变**科学内容、结果、核心结论与全部数字；只做写法、逻辑、排版、投稿体例。
- 不要建议新增实验或修改方法；只审现有 6 图 6 表与文字。
- 每条建议给出精确句子/段落级 diff，便于本地直接落地。
- 输出用中文，结构化为「A/B/C/D 四部分」。
