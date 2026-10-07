"""Spatial block cross-validation using H3 parent blocks (k-ring coarsening)."""

from __future__ import annotations

import warnings
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
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
    cells: list[str] | None = None,
) -> dict[str, float]:
    """
    GroupKFold by spatial block: train/test never share the same parent block.

    Returns mean fold metrics (accuracy, r2, f1, mae) — typically lower than
    a random i.i.d. split when labels are spatially structured — plus
    threshold-independent out-of-fold discrimination metrics (ROC-AUC and
    average precision / PR-AUC), reported both pooled and as fold means, and a
    per-cell out-of-fold prediction table.
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
            f"{metric_prefix}_roc_auc_mean": float("nan"),
            f"{metric_prefix}_roc_auc_pooled": float("nan"),
            f"{metric_prefix}_pr_auc_mean": float("nan"),
            f"{metric_prefix}_pr_auc_pooled": float("nan"),
            f"{metric_prefix}_fold_table": [],
            f"{metric_prefix}_oof_table": [],
        }

    gkf = GroupKFold(n_splits=n_splits)
    accs: list[float] = []
    r2s: list[float] = []
    f1s: list[float] = []
    maes: list[float] = []
    rocs: list[float] = []
    aps: list[float] = []
    fold_rows: list[dict] = []
    oof_rows: list[dict] = []
    oof_y_true: list[np.ndarray] = []
    oof_proba: list[np.ndarray] = []

    cell_labels = np.asarray(cells, dtype=object) if cells is not None else None

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
        rocs.append(float(fold.get("roc_auc", float("nan"))))
        aps.append(float(fold.get("average_precision", float("nan"))))

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
                "roc_auc": rocs[-1],
                "pr_auc": aps[-1],
            }
        )

        oof_y_true.append(y_class[test_idx].astype(int))
        oof_proba.append(proba.astype(float))
        for k, idx in enumerate(test_idx):
            oof_rows.append(
                {
                    "fold_id": int(fold_id),
                    "h3_index": str(cell_labels[idx]) if cell_labels is not None else str(int(idx)),
                    "h3_block": str(test_groups[k]),
                    "y_true": int(y_class[idx]),
                    "y_proba": float(proba[k]),
                    "y_pred": int(pred_class[k]),
                }
            )

    y_true_all = np.concatenate(oof_y_true)
    proba_all = np.concatenate(oof_proba)
    if len(np.unique(y_true_all)) > 1:
        try:
            pooled_roc = float(roc_auc_score(y_true_all, proba_all))
        except ValueError:
            pooled_roc = float("nan")
        try:
            pooled_ap = float(average_precision_score(y_true_all, proba_all))
        except ValueError:
            pooled_ap = float("nan")
    else:
        pooled_roc = float("nan")
        pooled_ap = float("nan")

    out = {
        f"{metric_prefix}_n_folds": float(n_splits),
        f"{metric_prefix}_n_blocks": float(len(unique)),
        f"{metric_prefix}_accuracy_mean": float(np.mean(accs)),
        f"{metric_prefix}_accuracy_std": float(np.std(accs)),
        f"{metric_prefix}_r2_mean": float(np.mean(r2s)),
        f"{metric_prefix}_r2_std": float(np.std(r2s)),
        f"{metric_prefix}_f1_mean": float(np.mean(f1s)),
        f"{metric_prefix}_mae_mean": float(np.mean(maes)),
        f"{metric_prefix}_roc_auc_mean": float(np.nanmean(rocs)),
        f"{metric_prefix}_roc_auc_std": float(np.nanstd(rocs)),
        f"{metric_prefix}_pr_auc_mean": float(np.nanmean(aps)),
        f"{metric_prefix}_pr_auc_std": float(np.nanstd(aps)),
        f"{metric_prefix}_roc_auc_pooled": pooled_roc,
        f"{metric_prefix}_pr_auc_pooled": pooled_ap,
        f"{metric_prefix}_fold_table": fold_rows,
        f"{metric_prefix}_oof_table": oof_rows,
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


def write_spatial_cv_oof_table(
    oof_rows: list[dict],
    out_path: Path | str,
) -> pd.DataFrame:
    """Persist per-cell out-of-fold predictions (y_true, proba, fold, block)."""
    table = pd.DataFrame(oof_rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    return table

