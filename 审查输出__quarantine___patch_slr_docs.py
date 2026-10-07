from pathlib import Path

ms = Path("docs/paper/manuscript.md")
t = ms.read_text(encoding="utf-8")
idx = t.find("Re-running the target with the 2050")
end = t.find("\n\nRainfall enters", idx)
old = t[idx:end]
new = (
    "Re-running the target with the 2050 layer is reported as a sensitivity "
    "(`outputs/slr_sensitivity.json`): under Option B (n = 262) positive prevalence "
    "shifts from 63.0% to 67.2% and pooled ROC-AUC from 0.847 to 0.833; in the "
    "expanded pilot the shifts are 47.5%→49.7% and 0.883→0.875. These changes do "
    "not alter any substantive conclusion, so the results are not an artefact of "
    "the sea-level scenario selected for the stormwater layer. "
    "(Pre-revision n = 141 smoke figures 67.4%→69.5% / 0.780→0.741 are historical only.)"
)
if not old.startswith("Re-running"):
    raise SystemExit("anchor miss")
ms.write_text(t[:idx] + new + t[end:], encoding="utf-8")
print("manuscript SLR updated")
print("OLD:", repr(old[:120]))

audit = Path("docs/paper/audit.md")
a = audit.read_text(encoding="utf-8")

old_table = """| pilot | DEP 变体 | n | 正类 | 占比 | DEP 单元 | pooled ROC-AUC | fold-mean ROC-AUC | accuracy | F1 | R² |
|-------|----------|---|------|------|----------|----------------|-------------------|----------|----|-----|
| LM | current | 141 | 95 | 67.4% | 40 | 0.780 | 0.798 | 0.781 | 0.822 | 0.048 |
| LM | 2050 SLR | 141 | 98 | 69.5% | 54 | 0.741 | 0.817 | 0.808 | 0.864 | 0.079 |
| 扩展 | current | 956 | 454 | 47.5% | 231 | 0.883 | 0.883 | 0.821 | 0.819 | 0.333 |
| 扩展 | 2050 SLR | 956 | 475 | 49.7% | 268 | 0.875 | 0.878 | 0.824 | 0.832 | 0.346 |

**关键事实**：
1. **2050 SLR 行精确复现上一版（pre-M4）主表数字**（正类 98/475、pooled ROC-AUC 0.741/0.875、accuracy 0.808/0.824），证明 M4 修复前的主表确实是用 2050 SLR 层得到的——语义错误被准确定位。
2. **current 行与修复后主表（§9.3）逐位一致**（0.780/0.883、0.781/0.821）。
3. **current 层的判别力不降反略升**：LM pooled ROC-AUC 0.780 > 0.741；扩展 0.883 > 0.875（虽然扩展差异 ~0.008 属噪声级，LM 差异 ~0.039 在小样本上也不应过度解读）。
4. 两变体下**所有实质结论不变**：模型超过 prevalence-aware 基线、ROC-AUC/AP 高于随机、扩展判别稳定、R² 近零/中等。"""

new_table = """| pilot | DEP 变体 | n | 正类 | 占比 | DEP 单元 | pooled ROC-AUC | fold-mean ROC-AUC | accuracy | F1 | R² |
|-------|----------|---|------|------|----------|----------------|-------------------|----------|----|-----|
| LM Option B | current | 262 | 165 | 63.0% | 74 | 0.847 | 0.831 | 0.809 | 0.846 | 0.227 |
| LM Option B | 2050 SLR | 262 | 176 | 67.2% | 98 | 0.833 | 0.838 | 0.839 | 0.882 | 0.234 |
| 扩展 | current | 956 | 454 | 47.5% | 231 | 0.883 | 0.883 | 0.821 | 0.819 | 0.336 |
| 扩展 | 2050 SLR | 956 | 475 | 49.7% | 268 | 0.875 | 0.878 | 0.824 | 0.832 | 0.341 |

> **历史注记（pre-Option-B，n=141）：** 修订前 SLR 表曾为 LM current 95/67.4%/ROC 0.780 vs 2050 98/69.5%/ROC 0.741。勿与现行 Option B 混用。

**关键事实（Option B 重跑后）**：
1. **current 行与 Option B 主表（§14.3 / `outputs/paper_results.json`）逐位一致**（LM 0.847 / 0.809；扩展 0.883 / 0.821）。
2. **current 层的判别力不降反略升**：LM pooled ROC-AUC 0.847 > 0.833；扩展 0.883 > 0.875（扩展差异 ~0.008 属噪声级）。
3. 两变体下**所有实质结论不变**：模型超过 prevalence-aware 基线、ROC-AUC/AP 高于随机、扩展判别稳定。
4. （审计轨迹）pre-M4 主表曾误用 2050 SLR 层；该语义错误定位见历史 n=141 注记与 §9.3。"""

if old_table not in a:
    raise SystemExit("audit SLR table block not found")
a = a.replace(old_table, new_table)
a = a.replace(
    "- Optional: re-run SLR sensitivity on Option B 262-cell table (script fixed to `lower_manhattan` profile)\n",
    "- SLR sensitivity re-run on Option B (**done**; LM n=262, prev 63.0%→67.2%, ROC-AUC 0.847→0.833)\n",
)
audit.write_text(a, encoding="utf-8")
print("audit SLR updated")
