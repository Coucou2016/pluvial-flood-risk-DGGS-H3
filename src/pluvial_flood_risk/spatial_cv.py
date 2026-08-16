"""Spatial block cross-validation using H3 parent blocks (k-ring coarsening)."""

from __future__ import annotations

import warnings
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from pluvial_flood_risk.estimators import build_classifier, build_regressor
from pluvial_flood_risk.metrics import evaluate_predictions


def h3_block_id(cell: str, k: int) -> str:
    """Coarser H3 parent used as spatial block ID (k levels up)."""
    res = h3.get_resolution(cell)
    parent_res = max(0, res - k)
    return h3.cell_to_parent(cell, parent_res)


def block_ids_for_cells(cells: list[str], k: int) -> np.ndarray:
    return np.array([h3_block_id(c, k) for c in cells], dtype=object)


def spatial_block_cv_metrics(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
    clf_builder=None,
    reg_builder=None,
    metric_prefix: str = "spatial_cv",
) -> dict[str, float]:
    """
    GroupKFold by spatial block: train/test never share the same parent block.

    Returns mean fold metrics (accuracy, r2, f1, mae) — typically lower than
    a random i.i.d. split when labels are spatially structured.
    """
    if clf_builder is None:
        clf_builder = build_classifier
    if reg_builder is None:
        reg_builder = build_regressor

    unique = np.unique(groups)
    n_splits = min(n_splits, len(unique))
    if n_splits < 2:
        warnings.warn(
            f"Only {len(unique)} spatial block(s); need >=2 for spatial CV.",
            stacklevel=2,
        )
        return {
            f"{metric_prefix}_n_folds": float(n_splits),
            f"{metric_prefix}_n_blocks": float(len(unique)),
            f"{metric_prefix}_accuracy_mean": float("nan"),
            f"{metric_prefix}_r2_mean": float("nan"),
            f"{metric_prefix}_f1_mean": float("nan"),
            f"{metric_prefix}_mae_mean": float("nan"),
            f"{metric_prefix}_fold_table": [],
        }

    gkf = GroupKFold(n_splits=n_splits)
    accs: list[float] = []
    r2s: list[float] = []
    f1s: list[float] = []
    maes: list[float] = []
    fold_rows: list[dict] = []

    for fold_id, (train_idx, test_idx) in enumerate(gkf.split(X, y_class, groups)):
        clf = clf_builder()
        reg = reg_builder()
        clf.fit(X[train_idx], y_class[train_idx])
        reg.fit(X[train_idx], y_risk[train_idx])

        pred_class = clf.predict(X[test_idx])
        risk = reg.predict(X[test_idx])
        proba_matrix = clf.predict_proba(X[test_idx])
        classes = list(clf.classes_)
        pos_idx = classes.index(1) if 1 in classes else 0
        proba = proba_matrix[:, pos_idx]

        fold = evaluate_predictions(
            y_risk[test_idx],
            risk,
            y_class[test_idx],
            pred_class,
            proba,
        )
        r2 = float(reg.score(X[test_idx], y_risk[test_idx]))
        accs.append(fold["accuracy"])
        r2s.append(r2)
        f1s.append(fold["f1"])
        maes.append(fold["mae"])

        test_groups = groups[test_idx]
        fold_rows.append(
            {
                "fold_id": fold_id,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "n_test_blocks": int(len(np.unique(test_groups))),
                "n_positive_test": int(np.sum(y_class[test_idx] == 1)),
                "n_negative_test": int(np.sum(y_class[test_idx] != 1)),
                "test_block_ids": ",".join(sorted(str(g) for g in np.unique(test_groups))),
                "accuracy": fold["accuracy"],
                "f1": fold["f1"],
                "r2": r2,
                "mae": fold["mae"],
            }
        )

    out = {
        f"{metric_prefix}_n_folds": float(n_splits),
        f"{metric_prefix}_n_blocks": float(len(unique)),
        f"{metric_prefix}_accuracy_mean": float(np.mean(accs)),
        f"{metric_prefix}_accuracy_std": float(np.std(accs)),
        f"{metric_prefix}_r2_mean": float(np.mean(r2s)),
        f"{metric_prefix}_r2_std": float(np.std(r2s)),
        f"{metric_prefix}_f1_mean": float(np.mean(f1s)),
        f"{metric_prefix}_mae_mean": float(np.mean(maes)),
        f"{metric_prefix}_fold_table": fold_rows,
    }
    return out


def write_spatial_cv_fold_table(
    fold_rows: list[dict],
    out_path: Path | str,
) -> pd.DataFrame:
    """Persist per-fold spatial CV diagnostics (paper Table / appendix)."""
    table = pd.DataFrame(fold_rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    return table

