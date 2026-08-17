"""Materialize trivial/majority classification baselines for the smoke fold table.

Reads ``models/nyc_smoke/spatial_cv_folds.csv`` and computes per-fold and mean
always-positive and always-negative baselines, so that accuracy/F1 are not
reported as "classification skill" without a class-prevalence comparison.

Outputs:
- ``outputs/classification_baselines.csv`` (per-fold)
- ``outputs/classification_baselines.json`` (summary)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FOLD_CSV = ROOT / "models" / "nyc_smoke" / "spatial_cv_folds.csv"
OUT_JSON = ROOT / "outputs" / "classification_baselines.json"
OUT_CSV = ROOT / "outputs" / "classification_baselines.csv"


def always_positive_metrics(pos: int, neg: int) -> tuple[float, float]:
    """Accuracy and positive-class F1 of predicting every cell as positive."""
    n = pos + neg
    acc = pos / n
    # recall = 1, precision = pos/n  =>  F1 = 2*acc/(acc + 1)
    f1 = 2.0 * acc / (acc + 1.0)
    return acc, f1


def main() -> None:
    df = pd.read_csv(FOLD_CSV)
    rows: list[dict] = []
    for _, r in df.iterrows():
        pos = int(r["n_positive_test"])
        neg = int(r["n_negative_test"])
        n = pos + neg
        ap_acc, ap_f1 = always_positive_metrics(pos, neg)
        rows.append(
            {
                "fold_id": int(r["fold_id"]),
                "n_test": n,
                "n_positive": pos,
                "n_negative": neg,
                "positive_prevalence": pos / n,
                "always_positive_acc": ap_acc,
                "always_positive_f1": ap_f1,
                "always_negative_acc": neg / n,
                "always_negative_f1": 0.0,
                "model_acc": float(r["accuracy"]),
                "model_f1": float(r["f1"]),
            }
        )

    tab = pd.DataFrame(rows)
    model_acc = float(df["accuracy"].mean())
    model_f1 = float(df["f1"].mean())
    ap_acc = float(tab["always_positive_acc"].mean())
    ap_f1 = float(tab["always_positive_f1"].mean())

    summary = {
        "source_fold_csv": str(FOLD_CSV),
        "note": (
            "Trivial baselines for the n=141 smoke fold table. Positive class "
            "dominates (overall prevalence %.4f), so always-positive is the "
            "majority-class baseline." % (df["n_positive_test"].sum() / df["n_test"].sum())
        ),
        "overall_positive_prevalence": float(df["n_positive_test"].sum() / df["n_test"].sum()),
        "model_mean_acc": model_acc,
        "model_mean_f1": model_f1,
        "always_positive_mean_acc": ap_acc,
        "always_positive_mean_f1": ap_f1,
        "always_negative_mean_acc": float(tab["always_negative_acc"].mean()),
        "always_negative_mean_f1": 0.0,
        "model_beats_majority_acc": bool(model_acc > ap_acc),
        "model_beats_majority_f1": bool(model_f1 > ap_f1),
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    tab.to_csv(OUT_CSV, index=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
