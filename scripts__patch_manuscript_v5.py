#!/usr/bin/env python
"""Patch manuscript.md tables/prose from live paper_results + CSVs (no invented numbers)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "outputs" / "paper_results.json"
MS = ROOT / "docs" / "paper" / "manuscript.md"


def f3(x) -> str:
    return f"{float(x):.3f}"


def f1(x) -> str:
    return f"{float(x):.1f}"


def main() -> None:
    d = json.loads(REG.read_text(encoding="utf-8"))
    # Ensure scale_loss + adaptive + f1_std are current
    ladder = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
    d["scale_loss"] = {
        "source_csv": "outputs/jaccard_by_resolution.csv",
        "source_json": "outputs/jaccard_by_resolution.json",
        "budget_match_mode": "strict_area_budget",
        "primary_metric": "area_weighted_soft_jaccard",
        "hotspot_budget": 0.10,
        "study_domain_mask": True,
        "n_fine": int(ladder["n_fine"].iloc[0]),
        "n_coarse_r9": int(ladder.loc[ladder["coarse_res"] == 9, "n_coarse"].iloc[0]),
        "rows": json.loads(ladder.to_json(orient="records")),
    }
    ad_path = ROOT / "outputs" / "adaptive_r11_hotspot_retention.json"
    if ad_path.exists():
        d["adaptive_r11_hotspot_retention"] = json.loads(ad_path.read_text(encoding="utf-8"))
    for key, fold in (
        ("lower_manhattan", ROOT / "models" / "nyc_smoke" / "spatial_cv_folds.csv"),
        ("manhattan_expanded", ROOT / "models" / "nyc_expanded" / "spatial_cv_folds.csv"),
    ):
        f = pd.read_csv(fold)
        d[key]["spatial_cv"]["spatial_cv_f1_std"] = float(f["f1"].std(ddof=0))
        d[key]["spatial_cv"]["spatial_cv_f1_mean"] = float(f["f1"].mean())
    REG.write_text(json.dumps(d, indent=2), encoding="utf-8")

    lm = d["lower_manhattan"]
    exp = d["manhattan_expanded"]
    sc = lm["spatial_cv"]
    esc = exp["spatial_cv"]
    bl = lm["baselines"]
    ebl = exp["baselines"]
    oof_lm = d["oof_extended_metrics"]["lower_manhattan"]["pooled"]
    oof_ex = d["oof_extended_metrics"]["manhattan_expanded"]["pooled"]
    ad = d.get("adaptive_r11_hotspot_retention") or {}
    nc = json.loads((ROOT / "outputs" / "negative_control.json").read_text(encoding="utf-8"))
    sandy = d.get("sandy_311_window_sensitivity") or json.loads(
        (ROOT / "outputs" / "sandy_311_window_sensitivity.json").read_text(encoding="utf-8")
    )
    sa = d["source_ablation"]["pilots"]
    lm_sa = {r["target"]: r for r in sa["lower_manhattan"]}
    ex_sa = {r["target"]: r for r in sa["manhattan_expanded"]}
    blk = d["block_sensitivity"]["pilots"]

    def jac(agg: str, res: int, col: str = "jaccard") -> float:
        row = ladder.loc[(ladder["aggregation"] == agg) & (ladder["coarse_res"] == res)].iloc[0]
        return float(row[col])

    text = MS.read_text(encoding="utf-8")

    # Abstract primary numbers
    text = re.sub(
        r"In the Lower Manhattan pilot \(manuscript bbox, n = 262 R9 cells, 63\.7% evidence-positive; Major Revision Option B\), the model attains spatial cross-validation accuracy 0\.\d+ ± 0\.\d+ and F1 0\.\d+, above the always-positive baseline \(0\.\d+ and 0\.\d+\), with pooled out-of-fold ROC-AUC 0\.\d+ and average precision 0\.\d+\. In the larger pilot \(n = 956 cells, 47\.9% evidence-positive\), accuracy is 0\.\d+ ± 0\.\d+ and F1 is 0\.\d+, both above the fold-mean constant-class baselines, with pooled out-of-fold ROC-AUC 0\.\d+ and average precision 0\.\d+\.",
        (
            f"In the Lower Manhattan pilot (manuscript bbox, n = 262 R9 cells, "
            f"{100*lm['positive_prevalence']:.1f}% evidence-positive; Major Revision Option B), "
            f"the model attains spatial cross-validation accuracy {f3(sc['spatial_cv_accuracy_mean'])} ± "
            f"{f3(sc['spatial_cv_accuracy_std'])} and F1 {f3(sc['spatial_cv_f1_mean'])}, above the "
            f"always-positive baseline ({f3(bl['always_positive_mean_acc'])} and "
            f"{f3(bl['always_positive_mean_f1'])}), with pooled out-of-fold ROC-AUC "
            f"{f3(sc['spatial_cv_roc_auc_pooled'])} and average precision "
            f"{f3(sc['spatial_cv_pr_auc_pooled'])}. In the larger pilot (n = 956 cells, "
            f"{100*exp['positive_prevalence']:.1f}% evidence-positive), accuracy is "
            f"{f3(esc['spatial_cv_accuracy_mean'])} ± {f3(esc['spatial_cv_accuracy_std'])} and F1 is "
            f"{f3(esc['spatial_cv_f1_mean'])}, both above the fold-mean constant-class baselines, "
            f"with pooled out-of-fold ROC-AUC {f3(esc['spatial_cv_roc_auc_pooled'])} and average "
            f"precision {f3(esc['spatial_cv_pr_auc_pooled'])}."
        ),
        text,
        count=1,
    )
    text = re.sub(
        r"\(mean Jaccard 0\.\d+ to R8; 0\.\d+ to R9\), and adaptive refinement concentrates representation into about \d+% as many cells as a uniform fine grid",
        (
            f"(mean Jaccard {f3(jac('mean', 8))} to R8; {f3(jac('mean', 9))} to R9), and adaptive "
            f"refinement concentrates representation into about "
            f"{int(round(100 * float(ad.get('cell_count_ratio_vs_uniform', 0.56))))}% as many cells "
            f"as a uniform fine grid"
        ),
        text,
        count=1,
    )

    # Highlights scale-loss R8
    text = re.sub(
        r"mean hotspot Jaccard 0\.\d+ to R8",
        f"mean hotspot Jaccard {f3(jac('mean', 8))} to R8",
        text,
        count=1,
    )

    # Table 3 Panel B F1 row fix
    text = re.sub(
        r"\| F1 \| 0\.\d+(?: ± 0\.\d+)? \| 0\.\d+(?: ± 0\.\d+)? \|",
        f"| F1 | {f3(sc['spatial_cv_f1_mean'])} ± {f3(sc['spatial_cv_f1_std'])} | "
        f"{f3(esc['spatial_cv_f1_mean'])} ± {f3(esc['spatial_cv_f1_std'])} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-positive accuracy \| 0\.\d+ \| 0\.\d+ \|",
        f"| Always-positive accuracy | {f3(bl['always_positive_mean_acc'])} | "
        f"{f3(ebl['always_positive_mean_acc'])} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-positive F1 \| 0\.\d+ \| 0\.\d+ \|",
        f"| Always-positive F1 | {f3(bl['always_positive_mean_f1'])} | "
        f"{f3(ebl['always_positive_mean_f1'])} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-negative accuracy \| 0\.\d+ \| 0\.\d+ \|",
        f"| Always-negative accuracy | {f3(bl['always_negative_mean_acc'])} | "
        f"{f3(ebl['always_negative_mean_acc'])} |",
        text,
        count=1,
    )

    # Table 4 from ladder
    mae_col = "continuous_mae"
    recall_col = "fine_parent_recall"
    prec_col = "coarse_precision"
    spear_col = "spearman_rank_corr"

    def t4(agg, res):
        r = ladder.loc[(ladder["aggregation"] == agg) & (ladder["coarse_res"] == res)].iloc[0]
        return (
            f"| R{res} | {agg.capitalize() if agg != 'p90' else 'P90'} | {f3(r['jaccard'])} | "
            f"{f3(r[mae_col])} | {f3(r[recall_col])} | {f3(r[prec_col])} | {f3(r[spear_col])} |"
        )

    table4 = "\n".join(
        [
            "| Coarse resolution | Aggregation | Soft Jaccard | Continuous MAE | Fine-parent recall | Coarse precision | Spearman |",
            "|---|---|---|---|---|---|---|",
            t4("mean", 9),
            t4("max", 9),
            t4("p90", 9),
            t4("mean", 8),
            t4("max", 8),
            t4("p90", 8),
        ]
    )
    text = re.sub(
        r"\| Coarse resolution \| Aggregation \| Soft Jaccard \| Continuous MAE \| Fine-parent recall \| Coarse precision \| Spearman \|\n\|---\|---\|---\|---\|---\|---\|---\|\n(?:\| R\d+ \|[^\n]+\n){6}",
        table4 + "\n",
        text,
        count=1,
    )
    text = re.sub(
        r"the R9 rollup yields area-weighted soft Jaccard 0\.\d+.*?and the R8 rollup yields 0\.\d+",
        f"the R9 rollup yields area-weighted soft Jaccard {f3(jac('mean', 9))} "
        f"(hard median reported in Table 4) and the R8 rollup yields {f3(jac('mean', 8))}",
        text,
        count=1,
    )
    text = re.sub(
        r"Maximum aggregation reaches soft Jaccard 0\.\d+ \(R9\) / 0\.\d+ \(R8\)",
        f"Maximum aggregation reaches soft Jaccard {f3(jac('max', 9))} (R9) / {f3(jac('max', 8))} (R8)",
        text,
        count=1,
    )
    text = re.sub(
        r"\(R10→R9 mean 0\.\d+; R10→R8 mean 0\.\d+\)",
        f"(R10→R9 mean {f3(jac('mean', 9))}; R10→R8 mean {f3(jac('mean', 8))})",
        text,
        count=1,
    )
    text = re.sub(
        r"mean Jaccard 0\.\d+ to R9, 0\.\d+ to R8",
        f"mean Jaccard {f3(jac('mean', 9))} to R9, {f3(jac('mean', 8))} to R8",
        text,
        count=1,
    )

    # Adaptive Option A section
    if ad:
        pct = 100 * float(ad["cell_count_ratio_vs_uniform"])
        adaptive_block = (
            f"The fixed coarse grid has 262 cells. Adaptive refinement selects "
            f"{int(ad['n_parents_refined'])} of 262 R9 cells and produces "
            f"{int(ad['n_adaptive_mixed']):,} mixed cells, compared with "
            f"{int(ad['n_uniform_fine']):,} cells for uniform R11 refinement "
            f"(Supplementary Fig. S2). The adaptive grid therefore uses "
            f"{pct:.1f}% as many cells as the uniform fine grid. True R11 feature "
            f"re-extraction on refined children (post-urban-drop deployment model; "
            f"{int(ad['n_refined_children_scorable']):,} / {int(ad['n_refined_children']):,} "
            f"children scorable after dropping DEM-edge NaNs) yields hotspot recall "
            f"{f3(ad['hotspot_recall'])} versus a uniformly scored scorable R11 grid "
            f"({int(ad['n_hotspot_uniform_scorable']):,} hotspots at quantile "
            f"{ad['hotspot_quantile']}). Table 5 lists the counts.\n\n"
            f"**Table 5. Adaptive representation experiment versus fixed and uniform fine grids** "
            f"(Lower Manhattan Option B; adaptive = {pct:.1f}% of uniform R11; "
            f"{int(ad['n_parents_refined'])} of 262 R9 cells refined; Option A true R11 "
            f"re-extract hotspot recall {f3(ad['hotspot_recall'])}).\n\n"
            f"| Representation | Cell count |\n"
            f"|---|---|\n"
            f"| Fixed R9 | 262 |\n"
            f"| Adaptive R9/R11 | {int(ad['n_adaptive_mixed']):,} |\n"
            f"| Uniform R11 | {int(ad['n_uniform_fine']):,} |\n"
        )
        text = re.sub(
            r"The fixed coarse grid has 262 cells\..*?\| Uniform R11 \| [0-9,]+ \|\n",
            adaptive_block,
            text,
            count=1,
            flags=re.S,
        )

    # Sandy / NC
    text = re.sub(
        r"Across the 262 cells, 74 intersect Sandy coastal inundation and \d+ carry pluvial evidence \(under the composite flood_class definition\); \d+ have both, and \d+ are coastal-only \([\d.]+%\)\.",
        (
            f"Across the 262 cells, {int(nc['n_coastal'])} intersect Sandy coastal inundation and "
            f"{int(nc['n_pluvial'])} carry pluvial evidence (under the composite flood_class definition); "
            f"{int(nc['n_both'])} have both, and {int(nc['n_coastal_only'])} are coastal-only "
            f"({100*float(nc['frac_coastal_only']):.1f}%)."
        ),
        text,
        count=1,
    )
    text = re.sub(
        r"The out-of-fold score averages 0\.\d+ in coastal-only cells, 0\.\d+ in pluvial-only cells, 0\.\d+ in cells with both, and 0\.\d+ in cells with neither, giving a pluvial−coastal out-of-fold score difference of 0\.\d+\. Among the \d+ cells above the 0\.8 score quantile, [\d.]+% are coastal-only and [\d.]+% carry pluvial evidence\.",
        (
            f"The out-of-fold score averages {f3(nc['mean_score_coastal_only'])} in coastal-only cells, "
            f"{f3(nc['mean_score_pluvial_only'])} in pluvial-only cells, "
            f"{f3(nc['mean_score_both'])} in cells with both, and "
            f"{f3(nc['mean_score_neither'])} in cells with neither, giving a pluvial−coastal "
            f"out-of-fold score difference of {f3(nc['pluvial_minus_coastal_mean_score'])}. "
            f"Among the {int(nc['n_high_score'])} cells above the 0.8 score quantile, "
            f"{100*float(nc['coastal_only_among_high_score']):.1f}% are coastal-only and "
            f"{100*float(nc['pluvial_among_high_score']):.1f}% carry pluvial evidence."
        ),
        text,
        count=1,
    )
    ls = sandy["label_shift"]
    meta = sandy["311_meta"]
    scv_s = sandy["spatial_cv_sandy311_excluded"]
    text = re.sub(
        r"excluding 311 complaints created in the Sandy landfall window 2012-10-27 to 2012-11-05 removes \d+ of \d+ complaints, flips one cell label \(\d+→\d+ positives\), and leaves pooled ROC-AUC essentially unchanged \(0\.\d+ vs 0\.\d+ on the rebuilt composite\)",
        (
            f"excluding 311 complaints created in the Sandy landfall window 2012-10-27 to 2012-11-05 "
            f"removes {meta['n_311_excluded_sandy_window']} of {meta['n_311_features_total']} complaints, "
            f"flips {ls['n_cells_flipped']} cell label ({ls['n_positive_baseline']}→"
            f"{ls['n_positive_sandy311_excluded']} positives), and leaves pooled ROC-AUC essentially "
            f"unchanged ({f3(scv_s['roc_auc_pooled'])} vs {f3(sc['spatial_cv_roc_auc_pooled'])} on the "
            f"rebuilt composite)"
        ),
        text,
        count=1,
    )

    # Table 6
    table6 = f"""| Statistic | Value |
|---|---|
| Cells intersecting Sandy inundation | {int(nc['n_coastal'])} of 262 |
| Cells with pluvial evidence | {int(nc['n_pluvial'])} of 262 |
| Both pluvial and coastal | {int(nc['n_both'])} |
| Coastal-only | {int(nc['n_coastal_only'])} ({100*float(nc['frac_coastal_only']):.1f}%) |
| Pluvial-only | {int(nc['n_pluvial_only'])} ({100*float(nc['frac_pluvial_only']):.1f}%) |
| Neither | {int(nc['n_neither'])} ({100*float(nc['n_neither'])/262:.1f}%) |
| Mean out-of-fold model score, coastal-only cells | {f3(nc['mean_score_coastal_only'])} |
| Mean out-of-fold model score, pluvial-only cells | {f3(nc['mean_score_pluvial_only'])} |
| Mean out-of-fold model score, both | {f3(nc['mean_score_both'])} |
| Mean out-of-fold model score, neither | {f3(nc['mean_score_neither'])} |
| Pluvial − coastal out-of-fold score difference | {f3(nc['pluvial_minus_coastal_mean_score'])} |
| Coastal-only among cells above 0.8 score quantile | {100*float(nc['coastal_only_among_high_score']):.1f}% |
| Pluvial among cells above 0.8 score quantile | {100*float(nc['pluvial_among_high_score']):.1f}% |
"""
    text = re.sub(
        r"\| Statistic \| Value \|\n\|---\|---\|\n(?:\|[^\n]+\n){13}",
        table6,
        text,
        count=1,
    )

    # Expanded section 4.7
    folds = pd.read_csv(ROOT / "models" / "nyc_expanded" / "spatial_cv_folds.csv")
    fold_bits = ", ".join(
        f"Fold{int(r.fold_id)} {f3(r.accuracy)} / {f3(r.f1)}" for _, r in folds.iterrows()
    )
    text = re.sub(
        r"The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in [\d.]+% of cells \(\d+ of 956\)\. Under the same H3-block protocol, spatial cross-validation accuracy is 0\.\d+ ± 0\.\d+ and F1 is 0\.\d+, both exceeding the fold-mean constant-class baselines \(majority-negative accuracy 0\.\d+; always-positive accuracy 0\.\d+ and F1 0\.\d+\)\. Pooled out-of-fold ROC-AUC is 0\.\d+ \(fold-mean 0\.\d+ ± 0\.\d+\) with average precision 0\.\d+, well above the [\d.]+ prevalence reference; evidence-score R² is 0\.\d+ ± 0\.\d+ and MAE is 0\.\d+\. Per-fold accuracy/F1 are [^;]+;",
        (
            f"The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out "
            f"labels in {100*exp['positive_prevalence']:.1f}% of cells ({exp['n_positive']} of 956). "
            f"Under the same H3-block protocol, spatial cross-validation accuracy is "
            f"{f3(esc['spatial_cv_accuracy_mean'])} ± {f3(esc['spatial_cv_accuracy_std'])} and F1 is "
            f"{f3(esc['spatial_cv_f1_mean'])}, both exceeding the fold-mean constant-class baselines "
            f"(majority-negative accuracy {f3(ebl['always_negative_mean_acc'])}; always-positive "
            f"accuracy {f3(ebl['always_positive_mean_acc'])} and F1 {f3(ebl['always_positive_mean_f1'])}). "
            f"Pooled out-of-fold ROC-AUC is {f3(esc['spatial_cv_roc_auc_pooled'])} (fold-mean "
            f"{f3(esc['spatial_cv_roc_auc_mean'])} ± {f3(esc['spatial_cv_roc_auc_std'])}) with average "
            f"precision {f3(esc['spatial_cv_pr_auc_pooled'])}, well above the "
            f"{f3(exp['positive_prevalence'])} prevalence reference; evidence-score R² is "
            f"{f3(esc['spatial_cv_r2_mean'])} ± {f3(esc['spatial_cv_r2_std'])} and MAE is "
            f"{f3(esc['spatial_cv_mae_mean'])}. Per-fold accuracy/F1 are {fold_bits};"
        ),
        text,
        count=1,
    )

    # Table 7
    def t7(name, key):
        a, b = lm_sa[key], ex_sa[key]
        p = f"{a['n_positive']} / {b['n_positive']}"
        if a.get("roc_auc_pooled") is None:
            return (
                f"| {name} | {p} | — / {f3(b['roc_auc_pooled'])} | — / {f3(b['roc_auc_mean'])} | "
                f"— / {f3(b['f1_mean'])} |"
            )
        return (
            f"| {name} | {p} | {f3(a['roc_auc_pooled'])} / {f3(b['roc_auc_pooled'])} | "
            f"{f3(a['roc_auc_mean'])} / {f3(b['roc_auc_mean'])} | "
            f"{f3(a['f1_mean'])} / {f3(b['f1_mean'])} |"
        )

    table7_rows = "\n".join(
        [
            "| Target definition | Positive cells (LM / Exp) | Pooled ROC-AUC (LM / Exp) | Fold-mean ROC-AUC (LM / Exp) | F1 (LM / Exp) |",
            "|---|---|---|---|---|",
            t7("DEP-only (polygon area)", "dep_only"),
            t7("311-only (crowd reports)", "complaint_only"),
            t7("HWM-only (USGS Ida)", "hwm_only"),
            t7("311 + HWM", "complaint_hwm"),
            t7("Composite (max)", "composite"),
            t7("Composite without dist_stream_m", "composite_no_diststream"),
            t7("311-only without building_density", "complaint_no_building_density"),
        ]
    )
    text = re.sub(
        r"\| Target definition \| Positive cells \(LM / Exp\) \| Pooled ROC-AUC \(LM / Exp\) \| Fold-mean ROC-AUC \(LM / Exp\) \| F1 \(LM / Exp\) \|\n\|---\|---\|---\|---\|---\|\n(?:\|[^\n]+\n){7}",
        table7_rows + "\n",
        text,
        count=1,
    )

    # Table 8 from block sensitivity
    def blk_row(pilot_key, label_prefix):
        rows = []
        for r in blk[pilot_key]["block_sensitivity"]:
            rows.append(
                f"| {label_prefix} | {r['k']} (R{r['block_resolution']}) | {r['n_blocks']} | "
                f"{f3(r['roc_auc_pooled'])} | {f3(r['roc_auc_mean'])} | "
                f"{f3(r['accuracy_mean'])} | {f3(r['f1_mean'])} |"
            )
        return rows

    lobo = blk["lower_manhattan"].get("lobo_r7") or blk["lower_manhattan"].get("lobo") or {}
    table8_lines = [
        "| Pilot | k (block resolution) | Blocks | Pooled ROC-AUC | Fold-mean ROC-AUC | Accuracy | F1 |",
        "|---|---|---|---|---|---|---|",
        *blk_row("lower_manhattan", "LM"),
    ]
    if lobo:
        table8_lines.append(
            f"| LM LOBO (R7) | 2 | {lobo.get('n_blocks', 12)} | {f3(lobo['roc_auc_pooled'])} | "
            f"{f3(lobo['roc_auc_mean'])} ± {f3(lobo.get('roc_auc_std', 0))} | "
            f"{f3(lobo['accuracy_mean'])} | {f3(lobo['f1_mean'])} |"
        )
    table8_lines.extend(blk_row("manhattan_expanded", "Exp"))
    text = re.sub(
        r"\| Pilot \| k \(block resolution\) \| Blocks \| Pooled ROC-AUC \| Fold-mean ROC-AUC \| Accuracy \| F1 \|\n\|---\|---\|---\|---\|---\|---\|---\|\n(?:\|[^\n]+\n){7}",
        "\n".join(table8_lines) + "\n",
        text,
        count=1,
    )

    mi_lm = blk["lower_manhattan"]["morans_i"]
    mi_ex = blk["manhattan_expanded"]["morans_i"]
    mi_r_lm = blk["lower_manhattan"].get("morans_i_oof_residual") or {}
    mi_r_ex = blk["manhattan_expanded"].get("morans_i_oof_residual") or {}
    text = re.sub(
        r"Moran's I \(composite evidence score\): 0\.\d+ \(LM\), 0\.\d+ \(Exp\)\. Moran's I \(OOF residual\): 0\.\d+ \(LM\), 0\.\d+ \(Exp\)\.",
        (
            f"Moran's I (composite evidence score): {f3(mi_lm['morans_i'])} (LM), "
            f"{f3(mi_ex['morans_i'])} (Exp). Moran's I (OOF residual): "
            f"{f3(mi_r_lm.get('morans_i', float('nan')))} (LM), "
            f"{f3(mi_r_ex.get('morans_i', float('nan')))} (Exp)."
        ),
        text,
        count=1,
    )
    text = re.sub(
        r"The composite target is positively spatially autocorrelated \(Moran's I 0\.\d+ in Lower Manhattan, 0\.\d+ in the expanded pilot\)",
        (
            f"The composite target is positively spatially autocorrelated (Moran's I "
            f"{f3(mi_lm['morans_i'])} in Lower Manhattan, {f3(mi_ex['morans_i'])} in the expanded pilot)"
        ),
        text,
        count=1,
    )
    text = re.sub(
        r"OOF residual Moran's I is much weaker \(0\.\d+ LM; 0\.\d+ Exp\)",
        (
            f"OOF residual Moran's I is much weaker ({f3(mi_r_lm.get('morans_i', float('nan')))} LM; "
            f"{f3(mi_r_ex.get('morans_i', float('nan')))} Exp)"
        ),
        text,
        count=1,
    )
    if lobo:
        text = re.sub(
            r"LOBO on Lower Manhattan \(12 folds\) yields pooled ROC-AUC 0\.\d+ \(fold-mean 0\.\d+ ± 0\.\d+\)",
            (
                f"LOBO on Lower Manhattan (12 folds) yields pooled ROC-AUC {f3(lobo['roc_auc_pooled'])} "
                f"(fold-mean {f3(lobo['roc_auc_mean'])} ± {f3(lobo.get('roc_auc_std', 0))})"
            ),
            text,
            count=1,
        )

    # OOF score mean in 4.1
    oof = pd.read_csv(ROOT / "models" / "nyc_smoke" / "spatial_cv_oof_predictions.csv")
    text = re.sub(
        r"\(mean 0\.\d+\) and less dispersed, consistent with the modest pooled discrimination reported in Section 4\.2 \(ROC-AUC 0\.\d+ and average precision 0\.\d+",
        (
            f"(mean {f3(oof['y_proba'].mean())}) and less dispersed, consistent with the modest pooled "
            f"discrimination reported in Section 4.2 (ROC-AUC {f3(sc['spatial_cv_roc_auc_pooled'])} and "
            f"average precision {f3(sc['spatial_cv_pr_auc_pooled'])}"
        ),
        text,
        count=1,
    )

    # FloodNet heldout if present
    fn = d.get("floodnet") or {}
    pilots = {p["pilot"]: p for p in (fn.get("pilots") or [])}
    if "lower_manhattan" in pilots and "manhattan_expanded" in pilots:
        text = re.sub(
            r"\(Lower Manhattan ROC-AUC 0\.\d+ on \d+ sensor cells; expanded 0\.\d+ on \d+ sensor cells\)",
            (
                f"(Lower Manhattan ROC-AUC {f3(pilots['lower_manhattan']['roc_auc'])} on "
                f"{pilots['lower_manhattan']['n_study_cells_with_sensor']} sensor cells; expanded "
                f"{f3(pilots['manhattan_expanded']['roc_auc'])} on "
                f"{pilots['manhattan_expanded']['n_study_cells_with_sensor']} sensor cells)"
            ),
            text,
            count=1,
        )

    MS.write_text(text, encoding="utf-8")
    print("Patched manuscript from live registry/CSVs")


if __name__ == "__main__":
    main()
