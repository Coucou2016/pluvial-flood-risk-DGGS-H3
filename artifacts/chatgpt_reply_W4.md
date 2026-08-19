# ChatGPT W4 回复归档（第 4 轮：全文一致性 + humanize 终审）

> 对话：Pluvial Flood Audit Plan
> 时间：2026-08-19（第 4 轮）
> 性质：外部顾问评审回复，仅作建议；是否采纳由 Cursor 依本地源码独立判定。

---

## 一致性问题清单（2 处需再确认/小修）

1. **§3.5 / §4.2 / Fig. 3 caption — 需同步去掉 "top decile" 概念。** 既然已确认 empirical 0.9 quantile = 1.0 且因大量 ties 使 R10 hotspot = 571/991 cells，它就不是实际意义的 "top 10%"。若 Fig. 3 caption 或 §4.2 仍写 "top decile (quantile 0.9)"，与新 Methods 不一致。最小改法：改为 "hotspots thresholded at the empirical 0.9 quantile"，并补 "Because many R10 scores are tied at the maximum value, this threshold equals 1.0 and selects 571 of 991 cells." 不要再称 fixed decile。

2. **§3.8 Sandy — 检查 "compared with predictions" 是否还在。** 源码已核实 `score_col=flood_risk`（观测标签分），非 model prediction。建议改为 "FEMA Sandy inundation is excluded from all model development and used only as a post hoc coastal-inundation separation diagnostic."，随后写 overlap 和 mean observed flood-risk score difference；§4.5/§5 若有 "model score"/"prediction difference" 也应同步改。

## 可复现性补充点（非矛盾，需确认）
- "fitted on standardised features" 需明确 scaler 是否只在每个 training fold 上拟合（否则是潜在 leakage）。
- "uncertainty ≥ 0.7" 若正文没有定义 uncertainty 公式，仍不可完全复现；需加入源码真实公式。

## Humanize 微调建议（可选，不涉及科学内容）
- §3.3 "unspecified estimator settings use scikit-learn 1.8 defaults" → "All other estimator parameters retain the scikit-learn 1.8 defaults."
- §3.4 "average precision (AP), where AP is the recall-weighted mean…" → "average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]."
- §3.6 "predicted probability uncertain" → "cells with uncertain predicted probabilities"；"selected set closed under a one-ring H3 neighbourhood" → "The selection is then expanded to include the one-ring H3 neighbourhood."
- §3.5 "fine open-label scores saturate at their maximum" → "Many R10 open-label scores are tied at the maximum value…"
- §3.1 "H3 native hex areas" → "H3 native cell-area calculations"
- §4.5 "mean observed label score" → "mean observed flood-risk score"

## Sign-off
**Conditional sign-off。** 只要确认并处理：(1) 所有 "top decile" 残留改为 "empirical 0.9-quantile threshold with ties"；(2) Sandy 全文不再把 flood_risk 差异称为 model prediction/model score；(3) 确认 standardisation 的 fold scope 与 uncertainty 定义已在 Methods 明示——即可正式 sign-off。其余新增 Methods 细节未引入新的明显 AI 痕迹，也未看到新的数字或分辨率角色冲突。
