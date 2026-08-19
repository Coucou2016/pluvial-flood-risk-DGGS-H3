# W10 复核请求（2026-08-20）：确认 W9 图体系对齐落地正确、无回归

## 背景
你上一轮（W9）判定：唯一值得进正文的缺失图型是"多分辨率空间并排图"，并建议"用真实 R10 labels 替换现主文 Fig.4，当前 Jaccard/F1 图移到 Supplementary"。我方已按你的 A/B/C 全部落实并推送到 GitHub（commit `036b520`）。本轮请复核落地是否正确，做回归确认。

## W9 已落实清单（请逐项核对）
1. **新增主文 Fig.4** `multi_resolution_spatial.png`：R10（n=991）/ R9 mean rollup（n=160）/ R8 mean rollup（n=31）三面板，共享 0–1 viridis 色标；数据 `nyc_h3_cells_r10_labels.parquet`，与 Fig.5 完全同源。
2. **旧 Fig.4** `jaccard_by_resolution.png` 移到 `supplementary/`，降级为补充图 S1；数值仍完整列于 Table 4。
3. **Fig.1**：`Learning & validation` / `Diagnostics & outputs` header 改两行；删除底部 y=0.30 悬空灰色箭头。
4. **Fig.2**：colorbar `Observed risk (0–1)` → `Open-label risk (0–1)`。
5. **Fig.6**：顶部 annotation 下移（ylim 1.22→1.30、annotation y 1.10→1.02）。
6. **文字同步**：manuscript Fig.4 caption 重写；§4.3 `(Fig. 4)`→`(Table 4)`；新增 Fig.4 空间图描述句；Fig.5 caption `in Fig. 4`→`in Table 4`；Table 4 note 加 `Supplementary Fig. S1`；新增 `Supplementary Figure S1` caption（置于 Figure 6 caption 后）。正文图号 first-mention 顺序仍 1→6。

## 本轮注入文件（9 个）
- `chatgpt_context_W10.md`（本文件）
- `manuscript.md`（W9 更新后）
- `audit.md`（含 §8.9 W9 记录）
- `multi_resolution_spatial.png`（新 Fig.4）
- `workflow_schematic.png`（Fig.1 修复后）
- `spatial_maps.png`（Fig.2 修复后）
- `adaptive_ablation.png`（Fig.6 修复后）
- `resolution_effects.png`（Fig.5 未改，供对照）
- `spatial_cv_folds.png`（Fig.3 未改，供对照）

## 请回答（中文，结构化）
1. **图 4 复核**：新 `multi_resolution_spatial.png` 三面板是否正确呈现 R10→R9→R8 的空间平滑？共享 colorbar 是否正常、无重叠/裁切？三面板 footprint 是否一致？(a)(b)(c) 标注是否醒目？
2. **Fig.1/2/6 修复复核**：header 两行、删除底部箭头、colorbar 术语、Fig.6 margin 是否都正确落地？有无新引入的视觉问题？
3. **文字一致性复核**：manuscript 的 Fig.4 caption、§4.3 正文、Table 4 note、Fig.5 caption、Supplementary S1 caption 是否互相一致、无"旧 Fig.4=Jaccard ladder"的残留引用？
4. **回归确认**：确认科学内容/结果/核心结论/全部数字未变（R10=991 / R9=160 / R8=31、Jaccard ladder 数值、Table 1–5 全部数字）。
5. **最终判定**：W9 图体系对齐是否达标？给 MUST-FIX / 建议 / sign-off 分级。若 sign-off，请明确说明"图体系对齐完成"。

## 约束
- 不改变科学内容、结果、核心结论与全部数字。
- 只复核图体系对齐、图质量、排版体例。
