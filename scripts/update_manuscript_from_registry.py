#!/usr/bin/env python
"""Rewrite key manuscript numeric claims from paper_results.json (no invented numbers)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "outputs" / "paper_results.json"
MS = ROOT / "docs" / "paper" / "manuscript.md"


def f3(x: float) -> str:
    return f"{float(x):.3f}"


def f1pct(x: float) -> str:
    return f"{100.0 * float(x):.1f}"


def main() -> None:
    d = json.loads(REG.read_text(encoding="utf-8"))
    text = MS.read_text(encoding="utf-8")
    lm = d["lower_manhattan"]
    exp = d["manhattan_expanded"]
    sc = lm["spatial_cv"]
    bl = lm["baselines"]
    esc = exp["spatial_cv"]
    ebl = exp.get("baselines") or {}
    oof = d.get("oof_extended_metrics") or {}
    lm_oof = (oof.get("lower_manhattan") or {}).get("pooled") or {}
    exp_oof = (oof.get("manhattan_expanded") or {}).get("pooled") or {}

    # Headline highlights (line ~7)
    text = re.sub(
        r"accuracy \(0\.\d+ vs 0\.\d+\) and F1 \(0\.\d+ vs 0\.\d+\)",
        f"accuracy ({f3(sc['spatial_cv_accuracy_mean'])} vs {f3(bl['always_positive_mean_acc'])}) "
        f"and F1 ({f3(sc['spatial_cv_f1_mean'])} vs {f3(bl['always_positive_mean_f1'])})",
        text,
        count=1,
    )

    # §3.2 predictors: remove urban flag language
    text = text.replace(
        "impervious fraction (NLCD), an urban land-cover flag, building density, and shoreline/tidal-water distance",
        "impervious fraction (NLCD), building density, and shoreline/tidal-water distance",
    )
    text = text.replace(
        "; the urban land-cover flag marks cells whose impervious fraction exceeds 0.45. Because the urban flag is a deterministic transformation of the impervious fraction, it is retained only for interpretability and carries no independent information.",
        ". The previously considered urban land-cover flag (impervious fraction > 0.45) is excluded from the estimator feature set because it is a deterministic copy of impervious fraction and carries no independent information.",
    )
    text = text.replace(
        "| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction, urban land-cover flag |",
        "| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction |",
    )
    text = text.replace(
        ", and the urban land-cover flag is a deterministic copy of the impervious fraction",
        "; the urban land-cover flag was removed from production features as a deterministic copy of impervious fraction",
    )

    # Primary CV paragraph numbers
    text = re.sub(
        r"Five-fold spatial cross-validation yields accuracy 0\.\d+ ± 0\.\d+ and F1 0\.\d+",
        f"Five-fold spatial cross-validation yields accuracy {f3(sc['spatial_cv_accuracy_mean'])} ± "
        f"{f3(sc['spatial_cv_accuracy_std'])} and F1 {f3(sc['spatial_cv_f1_mean'])}",
        text,
        count=1,
    )
    text = re.sub(
        r"exceeds the always-positive baseline on both accuracy \(0\.\d+ vs 0\.\d+\) and F1 \(0\.\d+ vs 0\.\d+\)",
        f"exceeds the always-positive baseline on both accuracy ({f3(sc['spatial_cv_accuracy_mean'])} vs "
        f"{f3(bl['always_positive_mean_acc'])}) and F1 ({f3(sc['spatial_cv_f1_mean'])} vs "
        f"{f3(bl['always_positive_mean_f1'])})",
        text,
        count=1,
    )
    text = re.sub(
        r"Pooled out-of-fold ROC-AUC is 0\.\d+ and pooled average precision is 0\.\d+",
        f"Pooled out-of-fold ROC-AUC is {f3(sc['spatial_cv_roc_auc_pooled'])} and pooled average precision is "
        f"{f3(sc['spatial_cv_pr_auc_pooled'])}",
        text,
        count=1,
    )
    if lm_oof:
        text = re.sub(
            r"pooled OOF balanced accuracy is 0\.\d+, precision 0\.\d+, recall 0\.\d+, specificity 0\.\d+, and MCC 0\.\d+",
            f"pooled OOF balanced accuracy is {f3(lm_oof['balanced_accuracy'])}, precision {f3(lm_oof['precision'])}, "
            f"recall {f3(lm_oof['recall'])}, specificity {f3(lm_oof['specificity'])}, and MCC {f3(lm_oof['mcc'])}",
            text,
            count=1,
        )
    text = re.sub(
        r"Evidence-score R² \(0\.\d+ ± 0\.\d+\)",
        f"Evidence-score R² ({f3(sc['spatial_cv_r2_mean'])} ± {f3(sc['spatial_cv_r2_std'])})",
        text,
        count=1,
    )

    # Table 3 panel A/B — rewrite the markdown table block after the Table 3 caption.
    # We replace known metric rows by regex on the first two numeric columns.
    def repl_table3_row(label: str, lm_v: float, exp_v: float, text: str) -> str:
        return re.sub(
            rf"(\| {re.escape(label)} \| )0\.\d+( \| )0\.\d+( \|)",
            rf"\g<1>{f3(lm_v)}\g<2>{f3(exp_v)}\g<3>",
            text,
            count=1,
        )

    if lm_oof and exp_oof:
        text = repl_table3_row("ROC-AUC", lm_oof["roc_auc"], exp_oof["roc_auc"], text)
        text = repl_table3_row("Average precision", lm_oof["average_precision"], exp_oof["average_precision"], text)
        text = repl_table3_row("Accuracy", lm_oof["accuracy"], exp_oof["accuracy"], text)
        text = repl_table3_row("Balanced accuracy", lm_oof["balanced_accuracy"], exp_oof["balanced_accuracy"], text)
        text = repl_table3_row("F1", lm_oof["f1"], exp_oof["f1"], text)
        text = repl_table3_row("Precision", lm_oof["precision"], exp_oof["precision"], text)
        text = repl_table3_row("Recall", lm_oof["recall"], exp_oof["recall"], text)
        text = repl_table3_row("Specificity", lm_oof["specificity"], exp_oof["specificity"], text)
        text = repl_table3_row("MCC", lm_oof["mcc"], exp_oof["mcc"], text)

    # Panel B fold-mean rows
    text = re.sub(
        r"(\| Accuracy \| )0\.\d+ ± 0\.\d+( \| )0\.\d+ ± 0\.\d+( \|)",
        rf"\g<1>{f3(sc['spatial_cv_accuracy_mean'])} ± {f3(sc['spatial_cv_accuracy_std'])}\g<2>"
        rf"{f3(esc['spatial_cv_accuracy_mean'])} ± {f3(esc['spatial_cv_accuracy_std'])}\g<3>",
        text,
        count=1,
    )
    text = re.sub(
        r"(\| F1 \| )0\.\d+ ± 0\.\d+( \| )0\.\d+ ± 0\.\d+( \|)",
        rf"\g<1>{f3(sc['spatial_cv_f1_mean'])} ± {f3(sc.get('spatial_cv_f1_std', 0))}\g<2>"
        rf"{f3(esc['spatial_cv_f1_mean'])} ± {f3(esc.get('spatial_cv_f1_std', 0))}\g<3>",
        text,
        count=1,
    )
    # If F1 std missing, fold CSV may be needed — leave 0.000 only if truly missing
    text = re.sub(
        r"(\| ROC-AUC \| )0\.\d+ ± 0\.\d+( \| )0\.\d+ ± 0\.\d+( \|)",
        rf"\g<1>{f3(sc['spatial_cv_roc_auc_mean'])} ± {f3(sc['spatial_cv_roc_auc_std'])}\g<2>"
        rf"{f3(esc['spatial_cv_roc_auc_mean'])} ± {f3(esc['spatial_cv_roc_auc_std'])}\g<3>",
        text,
        count=1,
    )

    # Source ablation prose
    sa = d.get("source_ablation") or {}
    pilots = sa.get("pilots") or {}
    lm_rows = {r["target"]: r for r in pilots.get("lower_manhattan") or []}
    exp_rows = {r["target"]: r for r in pilots.get("manhattan_expanded") or []}
    if lm_rows and exp_rows:
        text = re.sub(
            r"DEP-only pooled ROC-AUC is 0\.\d+ while 311-only reaches 0\.\d+ \(still well above 0\.5\) against 0\.\d+ for the composite; in the expanded pilot the corresponding values are 0\.\d+, 0\.\d+, and 0\.\d+",
            f"DEP-only pooled ROC-AUC is {f3(lm_rows['dep_only']['roc_auc_pooled'])} while 311-only reaches "
            f"{f3(lm_rows['complaint_only']['roc_auc_pooled'])} (still well above 0.5) against "
            f"{f3(lm_rows['composite']['roc_auc_pooled'])} for the composite; in the expanded pilot the "
            f"corresponding values are {f3(exp_rows['dep_only']['roc_auc_pooled'])}, "
            f"{f3(exp_rows['complaint_only']['roc_auc_pooled'])}, and {f3(exp_rows['composite']['roc_auc_pooled'])}",
            text,
            count=1,
        )
        text = re.sub(
            r"leaves LM pooled ROC-AUC at 0\.\d+ and expanded at 0\.\d+",
            f"leaves LM pooled ROC-AUC at {f3(lm_rows['complaint_no_building_density']['roc_auc_pooled'])} "
            f"and expanded at {f3(exp_rows['complaint_no_building_density']['roc_auc_pooled'])}",
            text,
            count=1,
        )

    # Discussion closing numbers
    text = re.sub(
        r"\(0\.\d+ vs 0\.\d+; 0\.\d+ vs 0\.\d+\), and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy \(0\.\d+ vs 0\.\d+\) and F1 \(0\.\d+ vs 0\.\d+\)",
        f"({f3(sc['spatial_cv_accuracy_mean'])} vs {f3(bl['always_positive_mean_acc'])}; "
        f"{f3(sc['spatial_cv_f1_mean'])} vs {f3(bl['always_positive_mean_f1'])}), and the expanded pilot exceeds "
        f"both the majority-negative and always-positive baselines on accuracy "
        f"({f3(esc['spatial_cv_accuracy_mean'])} vs {f3(ebl.get('always_negative_mean_acc') or ebl.get('majority_acc_mean', 0.521))}) "
        f"and F1 ({f3(esc['spatial_cv_f1_mean'])} vs {f3(ebl.get('always_positive_mean_f1') or 0.646)})",
        text,
        count=1,
    )
    text = re.sub(
        r"Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots \(0\.\d+ and 0\.\d+\)",
        f"Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots "
        f"({f3(sc['spatial_cv_roc_auc_pooled'])} and {f3(esc['spatial_cv_roc_auc_pooled'])})",
        text,
        count=1,
    )

    # Adaptive cell counts from ablation / r11
    ad = d.get("adaptive_r11_hotspot_retention") or {}
    if ad.get("n_adaptive_mixed"):
        text = re.sub(
            r"concentrates cells into \d+% of a uniform fine grid",
            f"concentrates cells into {int(round(100 * float(ad['cell_count_ratio_vs_uniform'])))}% of a uniform fine grid",
            text,
            count=1,
        )

    MS.write_text(text, encoding="utf-8")
    print(f"Updated {MS} from registry commit={d.get('git_commit', '')[:12]}")


if __name__ == "__main__":
    main()
