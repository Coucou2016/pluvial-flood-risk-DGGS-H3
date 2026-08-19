# W8 评审请求（2026-08-19）

## 背景
你上一轮（W7）已完成独立复核并 sign-off。本轮按你 W7 回复 §6 自提的三个 W8 方向继续收尾：**A. defensive prose 最后一次 sweep；B. 最终 PDF 版面审阅；C. submission-package 一致性**。同时按用户最新指令，已把最新 GitHub 链接给你直读（若抓取受限则以本轮注入的 8 个文件为准）。

**GitHub 仓库：** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 （当前 master = bb5f6af，paper-v1 tag 已存在）
**关键 raw 直链：** manuscript.md / audit.md / figures.py / 6 张 PNG 均在 `docs/paper/` 与 `docs/paper/figures/` 下（见上下文包）。

## 本轮注入文件（8 个）
1. `manuscript.md`（W7 修复后最新，6 图 6 表）
2. `audit.md`（含 §8.5 W6、§8.6 W7 记录）
3. `figures.py`（完整出图代码）
4. `reference_paper.md`（Svellingen et al. 2026 IJDRR 全文，写法/篇幅/逻辑对照）
5. `report.md`（研究报告中英文）
6. `chatgpt_context_W7.md`（上一轮上下文包）
7. `spatial_maps.png`（图 2）
8. `resolution_effects.png`（图 5）

## 请按 A/B/C/D 四部分回答

### A. Defensive prose 最后一次 sweep
1. 逐节找出仍带「研究工作总结 / 审稿答辩 / AI 辅助整理稿」气质的句子，尤其含 not / do not / does not / are not / cannot / never / must not / without 密集的段落（Abstract、§4.1、§4.4、§5.1、§5.3、§5.4、Fig.5 caption）。
2. 每处给句子级替换建议：防御式否定 → 正向 factual 陈述，**不改科学内容、结果、核心结论、数字**。
3. 区分「必须保留的科学诚实声明」（not a reproduction / never used as training label 等）与「可转正的技术说明」（Random splits are not primary 等）。
4. 输出「保留 vs 改写」清单，按高/中/低优先级，最多 20 条。

### B. 最终 PDF 版面审阅
5. 对照参考论文图表排版规范（图幅、字体、caption 位置、表格样式），逐一检查本稿 6 图 6 表：
   - 图：物理尺寸是否适合单栏/双栏；字号可读性；Fig.2 三面板与 Fig.5 双面板实际渲染尺寸。
   - 表：Table 1–6 是否会在投稿页宽内溢出/换行；caption 是否完整。
   - 每图每表给一条版面建议（达标则明说达标）。
6. 检查图号/caption 与正文引用一一对应（Fig 1–6、Table 1–6），figure PDF 文件名与 manuscript 编号对应关系。

### C. submission-package 一致性
7. 对照 IJDRR 投稿体例检查：Abstract、Keywords、**Highlights（当前缺失）**、CRediT（当前为显式 placeholder「待补充」）、Funding、Declaration of competing interest、Data availability、Declaration of Generative AI、References。
8. 若 Highlights 必要，请给 3–5 条候选（每条 ≤85 字符），基于现有科学内容提炼，不得新增未做的工作。
9. 检查数据/代码可用性声明与仓库实际内容一致性（paper-v1 tag、download manifest、版本号）。

### D. 回归确认
10. 确认 W7 的 4 MUST-FIX + 6 optional 在注入的最新文件/PNG 中是否正确落地、无新回归。

## 约束
- **不改变**科学内容、结果、核心结论与全部数字；只做写法、逻辑、排版、投稿体例。
- 不要建议新增实验或修改方法。
- 每条建议给出精确句子/段落级 diff，便于本地直接落地。
- 中文输出，结构化 A/B/C/D。
