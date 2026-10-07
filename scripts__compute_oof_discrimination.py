#!/usr/bin/env python
"""Compute out-of-fold ROC-AUC / PR-AUC for an H3 table without retraining models.

Reads a processed H3 parquet table, rebuilds the feature matrix, and re-runs the
spatial H3-block CV with per-cell out-of-fold probability collection, archiving
pooled and fold-mean ROC-AUC and average precision (PR-AUC). The fold assignment
is deterministic (GroupKFold over H3 parent blocks), so results reproduce the
archived fold tables.

Usage:
  python scripts/compute_oof_discrimination.py \
      --table data/processed/nyc_h3_cells.parquet \
      --model-dir models/nyc_smoke --k 2 --folds 5 \
      --out-json outputs/smoke_discrimination.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from pluvial_flood_risk.config import (  # noqa: E402
    DEFAULT_SPATIAL_CV_FOLDS,
    DEFAULT_SPATIAL_CV_K,
    TARGET_CLASS_COLUMN,
    TARGET_COLUMN,
)
from pluvial_flood_risk.features import feature_matrix  # noqa: E402
from pluvial_flood_risk.spatial_cv import (  # noqa: E402
    block_ids_for_cells,
    spatial_block_cv_metrics,
    write_spatial_cv_oof_table,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--model-dir", type=Path, default=None)
    ap.add_argument("--k", type=int, default=DEFAULT_SPATIAL_CV_K)
    ap.add_argument("--folds", type=int, default=DEFAULT_SPATIAL_CV_FOLDS)
    ap.add_argument("--out-json", type=Path, required=True)
    args = ap.parse_args()

    df = pd.read_parquet(args.table)
    X = feature_matrix(df)
    y_class = df[TARGET_CLASS_COLUMN].to_numpy()
    y_risk = df[TARGET_COLUMN].to_numpy()
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, args.k)

    metrics = spatial_block_cv_metrics(
        X, y_class, y_risk, groups, n_splits=args.folds, cells=cells
    )
    oof_rows = metrics.pop("spatial_cv_oof_table", None)
    metrics.pop("spatial_cv_fold_table", None)

    out = {
        "source_table": str(args.table),
        "k": args.k,
        "folds": args.folds,
        "n_cells": int(len(df)),
        "spatial_cv_n_blocks": metrics.get("spatial_cv_n_blocks"),
        "accuracy_mean": metrics.get("spatial_cv_accuracy_mean"),
        "f1_mean": metrics.get("spatial_cv_f1_mean"),
        "roc_auc_mean": metrics.get("spatial_cv_roc_auc_mean"),
        "roc_auc_std": metrics.get("spatial_cv_roc_auc_std"),
        "pr_auc_mean": metrics.get("spatial_cv_pr_auc_mean"),
        "pr_auc_std": metrics.get("spatial_cv_pr_auc_std"),
        "roc_auc_pooled": metrics.get("spatial_cv_roc_auc_pooled"),
        "pr_auc_pooled": metrics.get("spatial_cv_pr_auc_pooled"),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )

    if oof_rows and args.model_dir:
        args.model_dir.mkdir(parents=True, exist_ok=True)
        write_spatial_cv_oof_table(oof_rows, args.model_dir / "spatial_cv_oof_predictions.csv")

    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
