# ChatGPT W7 评审回复（2026-08-19，自动注入与抓取）

> 来源：https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2
> 方式：注入 8 个文件（manuscript.md / audit.md / figures.py / spatial_cv_oof_predictions.csv / nyc_h3_cells.parquet / pfi_h_scenarios.parquet / spatial_maps.png / resolution_effects.png）并发送 W7 复核请求。

---

## 一、总体结论

> 本轮可以做实质复核了：manuscript.md、audit.md、figures.py 都已读到，两张新 PNG 也逐张检查；另外直接读取了 OOF CSV，并对两个 Parquet 的实际列值做了独立解码/recompute。**结论：W6 的修复本身全部落地，但发现 3 个很小的新回归/表述问题（§4.1 两处文字 + Fig5(b) 标签对比度），处理后即可 sign-off。**

## 二、W6 MUST-FIX/optional 逐条复核

**W6 的 8 个 MUST-FIX 和 8 个 optional 均已正确落实。** 具体确认：
- Fig. 2(a) 实际读取 flood_risk（非 flood_class），连续 0–1 色标正确；
- deployed 已全部改为 full-fit（panel (c) 代码和 caption 均如此）；
- Fig. 2 caption 明确 r=75 mm/h，并说明 panel (c) 不是 OOF validation map；
- Fig. 2 与 Fig. 5 均已有 (a)/(b)/(c) panel tags，实际 PNG 吻合；
- Fig. 5(b) 深色格动态白字（阈值 val>=0.6）；
- Fig. 5 caption 解释 991→160→31 diagnostic footprint 与 141-cell supervised table 不同；
- Table 3 明确 ddof=0 并有表下注释；
- §4.1 明确 spatial correlations 是 descriptive concordance 非 validation；
- Fig. 5(a) raw points、colorbar label、不加 R6/R7、标题 cross-resolution similarity、Fig. 4/5 分工句均已落实。

## 三、§4.1 独立重算结果（ChatGPT 从注入数据文件独立读取）

| Quantity | Recomputed |
|---|---|
| n | 141 |
| observed min | 0 |
| observed median | 1.000 |
| observed mean | 0.605075 |
| observed ≥ 0.8 | 84 / 141 |
| observed exactly 0 | 28 |
| observed exactly 1 | 84 |
| OOF probability mean | 0.798305 |
| Ida-like full-fit PFI mean | 0.802888 |
| Pearson observed ~ OOF | 0.244801 |
| Pearson observed ~ full-fit PFI | 0.467873 |
| Pearson OOF ~ full-fit PFI | 0.508675 |

与 audit §8.5 独立汇总完全一致；manuscript §4.1 打印值全部匹配。

## 四、新 MUST-FIX（4 项）

1. **§3.5 删除对 Fig. 5 的提前编号引用**：当前全文首次出现顺序为 Fig.1→5→2→3→4→6 而非 1→6。最小处理：§3.5 删掉 figure number，改为 "The same diagnostics are additionally summarised through score distributions across resolutions and a pairwise hotspot-similarity matrix."，让 Fig. 5 首次正式出现于 §4.3。
2. **§4.1 These correlations → This correlation**：正文只报告了一个 Pearson（r=0.51），应为单数 "This correlation is a descriptive measure of spatial concordance…"。不把 0.245/0.468 也加入正文（保持 Results 简洁）。
3. **§4.1 改写 "any positive evidence … lifts the score to a high value"**：真实 flood_risk 含 29 个 0–1 之间 fractional values，表述过强。改为 "cells with no positive flood evidence score 0, whereas positive evidence produces either a fractional polygon-overlap score or a point-presence score of 1"。
4. **Fig. 5(b) (b) 标签改白色**（现黑色落在左上角深蓝 1.000 cell 内，对比度不足）。

## 五、Optional（6 项）

1. **Fig. 1 caption**：拆开超长首句，passed to diagnostics → diagnostics include；"…at R9 with provenance tags." 后断句。
2. **Fig. 2 caption**：将 "not an OOF validation map" 压入 panel (c) 定义；"Ida-like" → "synthetic Ida-like rainfall condition"。
3. **Fig. 5 caption**：两句 defensive wording 改正向 factual：→ "The R10 label-assembly footprint contains 991 cells and aggregates to 160 R9 and 31 R8 parents, distinct from the 141-cell R9 supervised modelling table in Sections 4.1–4.2."；"For the realised hotspot sets, both comparisons involving R8 yield Jaccard similarity 0.167."
4. **Fig. 5(a) caption**：说明 violin 内部 mean/extrema lines（"Internal bars indicate the mean and extrema."），或删除内部 summary lines。
5. **Fig. 2 PFI_h 用 mathtext**：与 Fig. 1 数学排版统一（当前 literal PFI_h 显示下划线）。
6. **Table 3 caption 与 Note 的 ddof=0 去重**：只保留表注作为正式 statistical convention。

## 六、W8+ 最值得做的 3 项（ChatGPT 建议下一轮转向 submission polish）

1. **全文 defensive prose 最后一次 sweep**：找 not / do not / are not / does not 密集段落，改成正向 factual statement（尤其 Fig. 5 caption 与 Discussion）；不动贡献结构。
2. **最终 PDF 版面审阅**：按真实投稿页宽检查 6 图 6 表（figure typography、跨栏宽度、表格换行、caption 与图距离、Fig. 5 双 panel 物理尺寸可读性）。
3. **submission-package consistency**：检查 CRediT、Highlights、AI declaration、data/code availability、paper-v1 tag/commit、figure PDF 文件名与 manuscript 编号一一对应（当前 CRediT 仍是显式 placeholder）。

> 总结句：除 4 个小 MUST-FIX 外，W6 新增的两张图及其数据链已通过本轮独立复核，**没有发现新的数值错误**。
