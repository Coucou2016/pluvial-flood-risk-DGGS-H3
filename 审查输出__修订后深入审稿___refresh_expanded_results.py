"""Refresh paper_results.json expanded block and patch manuscript expanded metrics."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "docs" / "paper" / "manuscript.md"
REPORT = ROOT / "docs" / "paper" / "report.md"


def _fmt3(x: float) -> str:
    return f"{float(x):.3f}"


def _fmt1(x: float) -> str:
    return f"{float(x):.1f}"


def main() -> None:
    pr_path = ROOT / "outputs" / "paper_results.json"
    pr = json.loads(pr_path.read_text(encoding="utf-8"))
    exp_meta = json.loads((ROOT / "models" / "nyc_expanded" / "run_metadata.json").read_text(encoding="utf-8"))
    edf = pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells_expanded.parquet")
    bas = json.loads((ROOT / "outputs" / "classification_baselines_expanded.json").read_text(encoding="utf-8"))
    pr["generated_utc"] = datetime.now(timezone.utc).isoformat()
    pr["manhattan_expanded"] = {
        "n_cells": int(len(edf)),
        "n_positive": int(edf["flood_class"].sum()),
        "positive_prevalence": float(edf["flood_class"].mean()),
        "bbox": [-74.03, 40.68, -73.94, 40.8],
        "spatial_cv": exp_meta.get("metrics", {}),
        "deployment": exp_meta.get("deployment", {}),
        "evaluation": exp_meta.get("evaluation", {}),
        "baselines": bas,
    }
    pr_path.write_text(json.dumps(pr, indent=2), encoding="utf-8")

    m = exp_meta["metrics"]
    acc = _fmt3(m["spatial_cv_accuracy_mean"])
    acc_sd = _fmt3(m["spatial_cv_accuracy_std"])
    f1 = _fmt3(m["spatial_cv_f1_mean"])
    roc = _fmt3(m["spatial_cv_roc_auc_pooled"])
    ap = _fmt3(m["spatial_cv_pr_auc_pooled"])
    r2 = _fmt3(m["spatial_cv_r2_mean"])
    r2_sd = _fmt3(m["spatial_cv_r2_std"])
    mae = _fmt3(m["spatial_cv_mae_mean"])
    prev = _fmt1(100 * float(edf["flood_class"].mean()))
    n_pos = int(edf["flood_class"].sum())
    ap_acc = _fmt3(bas["always_positive_acc_mean"])
    ap_f1 = _fmt3(bas["always_positive_f1_mean"])
    an_acc = _fmt3(bas["always_negative_acc_mean"])
    fold_roc = _fmt3(m["spatial_cv_roc_auc_mean"])
    fold_roc_sd = _fmt3(m["spatial_cv_roc_auc_std"])

    text = PAPER.read_text(encoding="utf-8")

    # Abstract expanded sentence
    text = re.sub(
        r"In the larger pilot \(n = 956 cells, [0-9.]+% positive\), accuracy is [0-9.]+ ± [0-9.]+ and F1 is [0-9.]+, both above the fold-mean constant-class baselines, with pooled out-of-fold ROC-AUC [0-9.]+ and average precision [0-9.]+.",
        f"In the larger pilot (n = 956 cells, {prev}% positive), accuracy is {acc} ± {acc_sd} and F1 is {f1}, both above the fold-mean constant-class baselines, with pooled out-of-fold ROC-AUC {roc} and average precision {ap}.",
        text,
        count=1,
    )

    # Table 3 expanded column
    text = re.sub(
        r"\| Accuracy \| 0\.820 ± 0\.057 \| [0-9.]+ ± [0-9.]+ \|",
        f"| Accuracy | 0.820 ± 0.057 | {acc} ± {acc_sd} |",
        text,
        count=1,
    )
    text = re.sub(r"\| F1 \| 0\.858 \| [0-9.]+ \|", f"| F1 | 0.858 | {f1} |", text, count=1)
    text = re.sub(
        r"\| Evidence-score R² \| 0\.191 ± 0\.287 \| [0-9.]+ ± [0-9.]+ \|",
        f"| Evidence-score R² | 0.191 ± 0.287 | {r2} ± {r2_sd} |",
        text,
        count=1,
    )
    text = re.sub(r"\| MAE \| 0\.279 \| [0-9.]+ \|", f"| MAE | 0.279 | {mae} |", text, count=1)
    text = re.sub(r"\| Pooled ROC-AUC \| 0\.848 \| [0-9.]+ \|", f"| Pooled ROC-AUC | 0.848 | {roc} |", text, count=1)
    text = re.sub(
        r"\| Pooled average precision \| 0\.855 \| [0-9.]+ \|",
        f"| Pooled average precision | 0.855 | {ap} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-positive accuracy \| 0\.637 \| [0-9.]+ \|",
        f"| Always-positive accuracy | 0.637 | {ap_acc} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-positive F1 \| 0\.769 \| [0-9.]+ \|",
        f"| Always-positive F1 | 0.769 | {ap_f1} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| Always-negative accuracy \| 0\.363 \| [0-9.]+ \|",
        f"| Always-negative accuracy | 0.363 | {an_acc} |",
        text,
        count=1,
    )

    # Expanded results paragraph (replace opening metrics; leave per-fold if stale with note)
    text = re.sub(
        r"The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in [0-9.]+% of cells \(\d+ of 956\)\. Under the same H3-block protocol, spatial cross-validation accuracy is [0-9.]+ ± [0-9.]+ and F1 is [0-9.]+ ± [0-9.]+, both exceeding the fold-mean constant-class baselines \(majority-negative accuracy [0-9.]+; always-positive accuracy [0-9.]+ and F1 [0-9.]+\)\. Pooled out-of-fold ROC-AUC is [0-9.]+ \(fold-mean [0-9.]+ ± [0-9.]+\) with average precision [0-9.]+, well above the [0-9.]+ prevalence reference; evidence-score R² is [0-9.]+ ± [0-9.]+ and MAE is [0-9.]+ ± [0-9.]+\.",
        f"The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in {prev}% of cells ({n_pos} of 956). Under the same H3-block protocol, spatial cross-validation accuracy is {acc} ± {acc_sd} and F1 is {f1}, both exceeding the fold-mean constant-class baselines (majority-negative accuracy {an_acc}; always-positive accuracy {ap_acc} and F1 {ap_f1}). Pooled out-of-fold ROC-AUC is {roc} (fold-mean {fold_roc} ± {fold_roc_sd}) with average precision {ap}, well above the {ap_acc} prevalence reference; evidence-score R² is {r2} ± {r2_sd} and MAE is {mae}.",
        text,
        count=1,
    )

    # Discussion / synthesis expanded numbers
    text = text.replace(
        "and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy (0.821 vs 0.525) and F1 (0.819 vs 0.643)",
        f"and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy ({acc} vs {an_acc}) and F1 ({f1} vs {ap_f1})",
    )
    text = text.replace(
        "Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.848 and 0.883), with average precision 0.855 and 0.812",
        f"Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.848 and {roc}), with average precision 0.855 and {ap}",
    )
    text = text.replace(
        "The evidence-score R² is 0.191 in the smaller pilot and 0.336 in the expanded pilot",
        f"The evidence-score R² is 0.191 in the smaller pilot and {r2} in the expanded pilot",
    )

    # Table 8 Exp R7 primary row
    text = re.sub(
        r"\| Exp \| 2 \(R7\) \| 28 \| [0-9.]+ \| [0-9.]+ \| [0-9.]+ \| [0-9.]+ \| [0-9.]+ \|",
        f"| Exp | 2 (R7) | 28 | {roc} | {fold_roc} | {acc} | {f1} | {r2} |",
        text,
        count=1,
    )

    # Table 7 composite positive counts; leave ablation ROC as pending re-run
    lm_df = pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells.parquet")
    lm_comp = int(lm_df["flood_class"].sum())
    lm_311 = int(((lm_df["complaint_presence"] > 0) | (lm_df["ida_hwm_presence"] > 0)).sum())
    exp_311 = int(((edf["complaint_presence"] > 0) | (edf["ida_hwm_presence"] > 0)).sum())
    text = re.sub(
        r"\| Composite \(max\) \| \d+ / \d+ \|",
        f"| Composite (max) | {lm_comp} / {n_pos} |",
        text,
        count=1,
    )
    text = re.sub(
        r"\| 311 \+ HWM \| \d+ / \d+ \|",
        f"| 311 + HWM | {lm_311} / {exp_311} |",
        text,
        count=1,
    )

    PAPER.write_text(text, encoding="utf-8")

    # Light report.md current-truth note
    if REPORT.exists():
        rtxt = REPORT.read_text(encoding="utf-8")
        rtxt = rtxt.replace(
            "当前真相是 Option B n=262（正类 63.0%，acc 0.809，F1 0.846，ROC-AUC 0.847）",
            "当前真相是 Option B n=262（正类 63.7%，acc 0.820，F1 0.858，ROC-AUC 0.848；扩展 n=956 正类 "
            f"{prev}%，acc {acc}，F1 {f1}，ROC-AUC {roc}；见 outputs/paper_results.json）",
        )
        REPORT.write_text(rtxt, encoding="utf-8")

    print(
        "expanded",
        n_pos,
        prev,
        acc,
        f1,
        roc,
        ap,
        r2,
        mae,
        "ap_acc",
        ap_acc,
        "an_acc",
        an_acc,
    )


if __name__ == "__main__":
    main()
