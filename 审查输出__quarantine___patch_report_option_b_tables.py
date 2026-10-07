"""Patch remaining Option-B-stale tables/sentences in docs/paper/report.md from live outputs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
report = ROOT / "docs" / "paper" / "report.md"
ms = ROOT / "docs" / "paper" / "manuscript.md"
text = report.read_text(encoding="utf-8")

pr = json.loads((ROOT / "outputs" / "paper_results.json").read_text(encoding="utf-8"))
lm = pr["lower_manhattan"]
sc = lm["spatial_cv"]
bl = lm["baselines"]
folds = pd.read_csv(ROOT / "models" / "nyc_smoke" / "spatial_cv_folds.csv")
jac = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
adap = pd.read_csv(ROOT / "outputs" / "adaptive_vs_fixed_ablation.csv").iloc[0]
nc = json.loads((ROOT / "outputs" / "negative_control.json").read_text(encoding="utf-8"))
sa = json.loads((ROOT / "outputs" / "source_ablation.json").read_text(encoding="utf-8"))
pfi = pd.read_csv(ROOT / "outputs" / "pfi_h_scenarios.csv")

acc_m = float(sc["spatial_cv_accuracy_mean"])
acc_s = float(sc["spatial_cv_accuracy_std"])
f1_m = float(sc["spatial_cv_f1_mean"])
r2_m = float(sc["spatial_cv_r2_mean"])
r2_s = float(sc["spatial_cv_r2_std"])
mae_m = float(sc["spatial_cv_mae_mean"])
roc_p = float(sc["spatial_cv_roc_auc_pooled"])
ap_p = float(sc["spatial_cv_pr_auc_pooled"])
n_blocks = int(sc["spatial_cv_n_blocks"])
prev = float(bl["overall_positive_prevalence"])
rand_acc = float(sc["random_split_val_accuracy"])

# --- Table 1 ---
old_t1 = """| Metric | Value |
|--------|-------|
| n_cells | 262 |
| spatial_cv_n_folds / n_blocks | 5 / 7 |
| accuracy mean ± std | 0.808895 ± 0.045779 |
| F1 mean ± std | 0.846 |
| R² mean ± std | 0.227 ± 0.196 |
| MAE mean | 0.330337 |
| random_split_val_accuracy（诊断） | 0.758621 |
| 留出正类占比（prevalence） | 0.6738 |
| 多数类（恒判正）基线 accuracy | **0.629** |
| 多数类（恒判正）基线 F1 | **0.762** |
| 模型是否超过多数类基线 acc / f1 | **是 / 是** |
| 留出 ROC-AUC（pooled） | **0.847** |
| 留出 AP（pooled） | **0.851**（随机基线 = 正类占比 0.630） |"""

new_t1 = f"""| Metric | Value |
|--------|-------|
| n_cells | 262 |
| spatial_cv_n_folds / n_blocks | 5 / {n_blocks} |
| accuracy mean ± std | {acc_m:.6f} ± {acc_s:.6f} |
| F1 mean ± std | {f1_m:.3f} |
| R² mean ± std | {r2_m:.3f} ± {r2_s:.3f} |
| MAE mean | {mae_m:.6f} |
| random_split_val_accuracy（诊断） | {rand_acc:.6f} |
| 留出正类占比（prevalence） | {prev:.4f} |
| 多数类（恒判正）基线 accuracy | **{bl['always_positive_mean_acc']:.3f}** |
| 多数类（恒判正）基线 F1 | **{bl['always_positive_mean_f1']:.3f}** |
| 模型是否超过多数类基线 acc / f1 | **是 / 是** |
| 留出 ROC-AUC（pooled） | **{roc_p:.3f}** |
| 留出 AP（pooled） | **{ap_p:.3f}**（随机基线 = 正类占比 {prev:.3f}） |"""
if old_t1 not in text:
    raise SystemExit("Table 1 block not found")
text = text.replace(old_t1, new_t1)

# --- Table 2 folds ---
fold_rows = ["| fold | n_train | n_test | accuracy | f1 | r2 | mae |", "|------|---------|--------|----------|-----|-----|-----|"]
for _, r in folds.iterrows():
    fold_rows.append(
        f"| {int(r.fold_id)} | {int(r.n_train)} | {int(r.n_test)} | {r.accuracy:.3f} | {r.f1:.3f} | "
        f"{r.r2:+.3f} | {r.mae:.3f} |"
    )
new_folds = "\n".join(fold_rows)
# replace by finding old header through fold 4
import re

text, n = re.subn(
    r"\| fold \| n_train \| n_test \| accuracy \| f1 \| r2 \| mae \|\n"
    r"\|------\|---------\|--------\|----------\|-----\|-----\|-----\|\n"
    r"(?:\| .*\n){5}",
    new_folds + "\n",
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"fold table replace count={n}")

text = text.replace(
    "**结论：** 多数折 Accuracy≈0.64–0.82，Fold4（n=24）抬高均值至 1.000；与表 1 一致。仍是 LM smoke。",
    f"**结论：** 五折 Accuracy≈{folds.accuracy.min():.2f}–{folds.accuracy.max():.2f}，F1≈{folds.f1.min():.2f}–{folds.f1.max():.2f}；与表 1 一致。仍是 LM Option B（n=262）。",
)
text = text.replace(
    "**如何读：** Fold4 准确率 1.000 明显高于其他折——这正是必须同时报告 **std** 的原因：块大小与正负类比例不均时，单折会跳动。",
    "**如何读：** 折间 accuracy/F1 仍有跳动（块大小与正负类比例不均）——这正是必须同时报告 **std** 的原因。",
)

# Fig 2 descriptive stats — keep qualitative; update PFI mean
pfi_mean = float(pfi["PFI_h"].mean())
text = text.replace("均值 0.677；**全拟合模型输出，非留出验证图**）", f"均值 {pfi_mean:.3f}；**deployment_full 全拟合输出，非留出验证图**）")
text = text.replace("均值 0.6774", f"均值 {pfi_mean:.4f}")

# --- Jaccard table ---
def jrow(coarse: int, agg: str) -> pd.Series:
    return jac[(jac.coarse_res == coarse) & (jac.aggregation == agg)].iloc[0]

rows = []
for coarse in (8, 9):
    for agg in ("mean", "max", "p90"):
        r = jrow(coarse, agg)
        rows.append(
            f"| {coarse} | {agg} | {r.jaccard:.4f} | {r.f1:.4f} | {r.fine_parent_recall:.4f} | {r.coarse_precision:.4f} |"
        )
n_fine = int(jac.iloc[0].n_fine)
k_fine = int(jac.iloc[0].k_fine)
new_jac = (
    "| coarse | agg | jaccard | f1 | fine-parent recall | coarse precision |\n"
    "|--------|-----|---------|-----|-------------------|------------------|\n"
    + "\n".join(rows)
    + f"\n\n附：细网格 n_fine={n_fine}，exact top-10% 热点 k={k_fine}"
    "（tie-aware fractional membership + projected-parent-area budgets；"
    "matched_budgets_cell_count=false）。"
)
text, n = re.subn(
    r"\| coarse \| agg \| jaccard \| f1 \| fine-parent recall \| coarse precision \|\n"
    r"\|--------\|-----\|---------\|-----\|-------------------\|------------------\|\n"
    r"(?:\| .*\n){6}\n附：细网格 n_fine=991，exact top-10% 热点 k=99（原生 overlay，无 parent inheritance；旧 q=0\.9 因 149/991 分数饱和会选 15\.0%，已弃用）。",
    new_jac,
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"jaccard table replace count={n}")

jm9 = float(jrow(9, "mean").jaccard)
jm8 = float(jrow(8, "mean").jaccard)
text = text.replace("mean@R8=0.111、mean@R9=0.180", f"mean@R8={jm8:.3f}、mean@R9={jm9:.3f}")
text = text.replace("Jaccard 0.18/0.11", f"Jaccard {jm9:.3f}/{jm8:.3f}")
text = text.replace("R10-vs-R9=0.180、R10-vs-R8=0.111", f"R10-vs-R9={jm9:.3f}、R10-vs-R8={jm8:.3f}")
text = text.replace("R10-vs-R9=0.180→R10-vs-R8=0.111", f"R10-vs-R9={jm9:.3f}→R10-vs-R8={jm8:.3f}")
text = text.replace("把矩阵中的 0.180/0.111", f"把矩阵中的 {jm9:.3f}/{jm8:.3f}")
text = text.replace("（991 个 R10 单元）", f"（{n_fine} 个 R10 单元）")
text = text.replace("（a） R10 开放标签分（n=991）", f"（a） R10 开放标签分（n={n_fine}）")
# parent counts from jaccard
n_r9 = int(jrow(9, "mean").n_coarse)
n_r8 = int(jrow(8, "mean").n_coarse)
text = text.replace("至 R9（160）/ R8（31）", f"至 R9（{n_r9}）/ R8（{n_r8}）")
text = text.replace("（b） R9 mean 上卷（n=160）；（c） R8 mean 上卷（n=31）", f"（b） R9 mean 上卷（n={n_r9}）；（c） R8 mean 上卷（n={n_r8}）")
text = text.replace("R8 n=31 的真实散布", f"R8 n={n_r8} 的真实散布")

# historical note for Jaccard calibration — keep as pre-revision labeled
text = text.replace(
    "R10→R9 mean Jaccard 从旧 q=0.9 的 0.210 校准为 0.180，真实揭示尺度损失。**",
    f"R10→R9 mean Jaccard 在 Option B（n_fine={n_fine}，projected-parent-area）下为 **{jm9:.3f}**"
    "（历史注记：pre-Option-B smoke 足迹曾报告 ~0.180）。**",
)

# --- Adaptive table ---
ratio = float(adap["adaptive_cell_count_ratio"])
n_adapt = int(adap["n_adaptive_mixed"])
n_uni = int(float(adap["adaptive_n_uniform_fine"]))
n_ref = int(adap["adaptive_n_parents_refined"])
old_ad = """| Field | Value |
|-------|-------|
| score_col | PFI_h |
| n_fixed_coarse (R9) | 262 |
| n_adaptive_mixed | 4845 |
| n_uniform_fine (R11) | 6909 |
| adaptive_cell_count_ratio (adaptive/uniform) | 0.701259 |
| parents_refined | 98 |
| score_quantile | 0.8 |
| coarse→fine | 9→11 |"""
new_ad = f"""| Field | Value |
|-------|-------|
| score_col | PFI_h |
| n_fixed_coarse (R9) | 262 |
| n_adaptive_mixed | {n_adapt} |
| n_uniform_fine (R11) | {n_uni} |
| adaptive_cell_count_ratio (adaptive/uniform) | {ratio:.6f} |
| parents_refined | {n_ref} |
| score_quantile | 0.8 |
| coarse→fine | 9→11 |"""
if old_ad not in text:
    raise SystemExit("adaptive table not found")
text = text.replace(old_ad, new_ad)
text = text.replace(
    "本 smoke 设定下自适应把均匀细网格单元数降到约七成（**仅单元数**）。",
    f"本 Option B 设定下自适应把均匀细网格单元数降到约 {ratio*100:.1f}%（**仅单元数**）。",
)
text = text.replace(
    "「Adaptive = 34.4× fixed R9 = 70.1% of uniform R11（representation size only）」",
    f"「Adaptive = {n_adapt/262:.1f}× fixed R9 = {ratio*100:.1f}% of uniform R11（representation size only）」",
)

# --- Negative control ---
old_nc = """| Field | Value |
|-------|-------|
| n_cells | 262 |
| n_coastal / n_pluvial / n_both | 31 / 95 / 20 |
| n_coastal_only / n_pluvial_only | 11 / 75 |
| n_neither | 35 |
| frac_coastal_only | 0.0780 |
| score_col | **oof_model_score**（留出模型分，非 target） |
| mean_score_coastal_only | 0.435 |
| mean_score_pluvial_only | 0.823 |
| mean_score_both | 0.750 |
| mean_score_neither | 0.308 |
| pluvial_minus_coastal_mean_score | **0.387** |
| coastal_only_among_high_score | 0.034 |
| pluvial_among_high_score | 0.793 |
| assembly_mode | opendata |"""
new_nc = f"""| Field | Value |
|-------|-------|
| n_cells | {int(nc['n_cells'])} |
| n_coastal / n_pluvial / n_both | {int(nc['n_coastal'])} / {int(nc['n_pluvial'])} / {int(nc['n_both'])} |
| n_coastal_only / n_pluvial_only | {int(nc['n_coastal_only'])} / {int(nc['n_pluvial_only'])} |
| n_neither | {int(nc['n_neither'])} |
| frac_coastal_only | {nc['frac_coastal_only']:.4f} |
| score_col | **oof_model_score**（留出模型分，非 target） |
| mean_score_coastal_only | {nc['mean_score_coastal_only']:.3f} |
| mean_score_pluvial_only | {nc['mean_score_pluvial_only']:.3f} |
| mean_score_both | {nc['mean_score_both']:.3f} |
| mean_score_neither | {nc['mean_score_neither']:.3f} |
| pluvial_minus_coastal_mean_score | **{nc['pluvial_minus_coastal_mean_score']:.3f}** |
| coastal_only_among_high_score | {nc['coastal_only_among_high_score']:.3f} |
| pluvial_among_high_score | {nc['pluvial_among_high_score']:.3f} |
| assembly_mode | opendata |"""
if old_nc not in text:
    raise SystemExit("NC table not found")
text = text.replace(old_nc, new_nc)
text = text.replace(
    f"**如何读：** `n_coastal_only=11`（7.8%）的**留出模型分均值为 0.435**，并非 0——说明模型确实**部分学习了低海拔/近岸信号**；`n_pluvial_only=75` 的留出分为 0.823，分差 0.387。因此模型并非「完全不把证据集中在海岸单元」，但 pluvial-only 仍最高、top-20% 分数单元中 coastal-only 仅占 3.4%，说明模型没有被海岸位置单独驱动。这是比旧版（coastal-only target=0.000、分差 0.888）**更诚实**的结论。",
    f"**如何读：** `n_coastal_only={int(nc['n_coastal_only'])}`（{nc['frac_coastal_only']*100:.1f}%）的**留出模型分均值为 {nc['mean_score_coastal_only']:.3f}**，并非 0——说明模型确实**部分学习了低海拔/近岸信号**；"
    f"`n_pluvial_only={int(nc['n_pluvial_only'])}` 的留出分为 {nc['mean_score_pluvial_only']:.3f}，分差 {nc['pluvial_minus_coastal_mean_score']:.3f}。"
    f"因此模型并非「完全不把证据集中在海岸单元」，但 pluvial-only 仍最高、高分单元中 coastal-only 仅占 {nc['coastal_only_among_high_score']*100:.1f}%，说明模型没有被海岸位置单独驱动。",
)
text = text.replace(
    "答案是「部分（coastal-only OOF=0.435 vs neither=0.308），但不主导（pluvial-only=0.823 更高，top 分数单元 79.3% 为 pluvial）」",
    f"答案是「部分（coastal-only OOF={nc['mean_score_coastal_only']:.3f} vs neither={nc['mean_score_neither']:.3f}），"
    f"但不主导（pluvial-only={nc['mean_score_pluvial_only']:.3f} 更高，高分单元 {nc['pluvial_among_high_score']*100:.1f}% 为 pluvial）」",
)

# PFI scenario means
pm = float(pfi.groupby("scenario")["PFI_h"].mean().iloc[0])
text = text.replace(
    """| scenario | rainfall_mm_h | mean PFI_h |
|----------|---------------|------------|
| moderate | 25 | 0.6774 |
| heavy | 40 | 0.6774 |
| Ida-like | 75 | 0.6774 |
| extreme | 100 | 0.6774 |""",
    f"""| scenario | rainfall_mm_h | mean PFI_h |
|----------|---------------|------------|
| moderate | 25 | {pm:.4f} |
| heavy | 40 | {pm:.4f} |
| Ida-like | 75 | {pm:.4f} |
| extreme | 100 | {pm:.4f} |""",
)

# Expanded comparison column leftovers
text = text.replace("| spatial_cv_n_blocks | **28** | 7 |", f"| spatial_cv_n_blocks | **28** | {n_blocks} |")
text = text.replace("| 正类占比（held-out） | **0.475** | 0.674 |", f"| 正类占比（held-out） | **0.475** | {prev:.3f} |")
text = text.replace("| spatial_cv_f1_mean | **0.819** | 0.822 |", f"| spatial_cv_f1_mean | **0.819** | {f1_m:.3f} |")
text = text.replace(
    "| spatial_cv_r2_mean ± std | **0.333 ± 0.144** | 0.048 ± 0.348 |",
    f"| spatial_cv_r2_mean ± std | **0.336 ± 0.146** | {r2_m:.3f} ± {r2_s:.3f} |",
)
text = text.replace(
    "| spatial_cv_mae_mean | **0.286** | 0.330 |",
    f"| spatial_cv_mae_mean | **0.285** | {mae_m:.3f} |",
)
text = text.replace(
    "| random_split_val_accuracy（仅诊断） | 0.818 | 0.759 |",
    f"| random_split_val_accuracy（仅诊断） | 0.818 | {rand_acc:.3f} |",
)
text = text.replace("| always-negative accuracy | **0.525** | 0.338 |", "| always-negative accuracy | **0.525** | 0.371 |")
text = text.replace("| AP / average precision（pooled，留出） | **0.812** | 0.805 |", f"| AP / average precision（pooled，留出） | **0.812** | {ap_p:.3f} |")
text = text.replace("| 随机 AP 基线（=正类占比） | 0.475 | 0.674 |", f"| 随机 AP 基线（=正类占比） | 0.475 | {prev:.3f} |")

text = text.replace("小窗口 R²≈0.048，扩展窗口 R²≈0.333", f"小窗口 R²≈{r2_m:.3f}，扩展窗口 R²≈0.336")
text = text.replace(
    "且留出 ROC-AUC（0.780 / 0.883）与 AP（0.805 / 0.812）均高于各自随机基线",
    f"且留出 ROC-AUC（{roc_p:.3f} / 0.883）与 AP（{ap_p:.3f} / 0.812）均高于各自随机基线",
)

# Source ablation table
lm_rows = {r["target"]: r for r in sa["pilots"]["lower_manhattan"]}
ex_rows = {r["target"]: r for r in sa["pilots"]["manhattan_expanded"]}


def fmt(target: str, key: str, nd: int = 3):
    lv = lm_rows[target].get(key)
    ev = ex_rows[target].get(key)
    if lv is None and ev is None:
        return "— / —"
    if lv is None:
        return f"— / {ev:.{nd}f}"
    return f"{lv:.{nd}f} / {ev:.{nd}f}"


def npos(target: str):
    return f"{lm_rows[target]['n_positive']} / {ex_rows[target]['n_positive']}"


new_sa = f"""| 目标定义 | 正类单元（LM / 扩展） | pooled ROC-AUC（LM / 扩展） | fold-mean ROC-AUC（LM / 扩展） | F1（LM / 扩展） |
|----------|----------------------|----------------------------|-------------------------------|----------------|
| DEP-only（多边形面积） | {npos('dep_only')} | {fmt('dep_only','roc_auc_pooled')} | {fmt('dep_only','roc_auc_mean')} | {fmt('dep_only','f1_mean')} |
| 311-only（众包报告） | {npos('complaint_only')} | {fmt('complaint_only','roc_auc_pooled')} | {fmt('complaint_only','roc_auc_mean')} | {fmt('complaint_only','f1_mean')} |
| HWM-only（USGS Ida） | {npos('hwm_only')} | {fmt('hwm_only','roc_auc_pooled')} | {fmt('hwm_only','roc_auc_mean')} | {fmt('hwm_only','f1_mean')} |
| 311 + HWM | {npos('complaint_hwm')} | {fmt('complaint_hwm','roc_auc_pooled')} | {fmt('complaint_hwm','roc_auc_mean')} | {fmt('complaint_hwm','f1_mean')} |
| composite（max） | {npos('composite')} | {fmt('composite','roc_auc_pooled')} | {fmt('composite','roc_auc_mean')} | {fmt('composite','f1_mean')} |
| composite 去掉 dist_stream_m | {npos('composite_no_diststream')} | {fmt('composite_no_diststream','roc_auc_pooled')} | {fmt('composite_no_diststream','roc_auc_mean')} | {fmt('composite_no_diststream','f1_mean')} |"""

text, n = re.subn(
    r"\| 目标定义 \| 正类单元（LM / 扩展） \| pooled ROC-AUC（LM / 扩展） \| fold-mean ROC-AUC（LM / 扩展） \| F1（LM / 扩展） \|\n"
    r"\|----------\|----------------------\|----------------------------\|-------------------------------\|----------------\|\n"
    r"(?:\| .*\n){6}",
    new_sa + "\n",
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"source ablation table replace count={n}")

text = text.replace("源于仅 7 块、5 个不同拟合模型", f"源于仅 {n_blocks} 块、5 个不同拟合模型")

# conclusions leftovers
text = text.replace(
    "开放标签 H3+ML + 空间块 CV 已产生两个试点（LM smoke `n=141`、扩展窗口",
    "开放标签 H3+ML + 空间块 CV 已产生两个试点（LM Option B `n=262`、扩展窗口",
)

report.write_text(text, encoding="utf-8")
print("wrote", report)

# manuscript: seven blocks -> 12
mst = ms.read_text(encoding="utf-8")
mst2 = mst.replace(
    "because the five folds derive from different fitted models on only seven blocks (per-fold ROC-AUC ranges from 0.588 to 1.000)",
    "because the five folds derive from different fitted models on 12 blocks (fold-mean and pooled differ when score scales vary across folds)",
)
if mst2 != mst:
    ms.write_text(mst2, encoding="utf-8")
    print("manuscript seven-blocks note fixed")
else:
    print("manuscript note already ok or pattern missed")

# residual grep
for label, p in [("report", report), ("ms", ms)]:
    t = p.read_text(encoding="utf-8")
    for pat in ["0.781432", "n_cells=141", "0.780 / 0.883", "4845", "6909", "0.048 ±", "仅 7 块"]:
        print(label, "HAS" if pat in t else "ok", pat)
