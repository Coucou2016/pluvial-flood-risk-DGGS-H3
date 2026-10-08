"""Spatial block cross-validation with a physical guard band and block bootstrap.

Major Revision 2026-10-08
-------------------------
P0-5/P0-6: The coarse spatial block is the H3 **parent** ``parent_resolution_offset``
levels above the modelling resolution (e.g. R9 − 2 = R7). This was historically
misnamed ``k_ring`` — it is a parent-resolution offset, not a k-ring.

``GroupKFold`` only prevents the *same* block appearing in train and test;
neighbouring blocks still leak across the block boundary. We therefore purge
training cells within a physical metre buffer of any held-out cell (centroids
projected to EPSG:2263). A buffer of 0 m reproduces the classic GroupKFold.
A pooled AUC/AP 95% CI is computed with a **spatial-block bootstrap** (blocks,
not cells, are the resampling unit).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from pluvial_flood_risk.config import (
    DEFAULT_CV_BUFFER_METERS,
    SPATIAL_BLOCK_BOOTSTRAP_N,
)
from pluvial_flood_risk.estimators import build_classifier, build_regressor
from pluvial_flood_risk.metrics import evaluate_predictions


def h3_parent_block_id(cell: str, parent_resolution_offset: int) -> str:
    """Coarser H3 parent used as spatial block ID (offset levels up)."""
    res = h3.get_resolution(cell)
    parent_res = max(0, res - int(parent_resolution_offset))
    return h3.cell_to_parent(cell, parent_res)


def block_ids_for_cells(cells: list[str], parent_resolution_offset: int) -> np.ndarray:
    return np.array(
        [h3_parent_block_id(c, parent_resolution_offset) for c in cells], dtype=object
    )


# Deprecated aliases (kept so older call sites keep resolving).
def h3_block_id(cell: str, k: int) -> str:
    """Deprecated: use :func:`h3_parent_block_id` (``k`` was a parent-res offset)."""
    return h3_parent_block_id(cell, k)


def _project_centroids_to_2263(cells: list[str]) -> np.ndarray | None:
    """Project cell centroids to EPSG:2263 metres; None if pyproj unavailable."""
    try:
        from pyproj import Transformer
    except ImportError:
        return None
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2263", always_xy=True)
    lons = np.empty(len(cells), dtype=np.float64)
    lats = np.empty(len(cells), dtype=np.float64)
    for i, cell in enumerate(cells):
        lat, lon = h3.cell_to_latlng(cell)
        lats[i] = lat
        lons[i] = lon
    xs, ys = transformer.transform(lons, lats)
    return np.column_stack([np.asarray(xs), np.asarray(ys)])


def purge_train_neighbors(
    train_cells: list[str],
    test_cells: list[str],
    buffer_m: float,
    *,
    mode: str = "meters",
    k_ring: int = 1,
) -> list[str]:
    """
    Return the subset of ``train_cells`` that are further than ``buffer_m`` from
    every ``test_cells`` centroid.

    ``mode='meters'`` projects centroids to EPSG:2263 and uses true metres.
    ``mode='k_ring'`` falls back to an H3 grid-disk purge (``k_ring`` neighbours
    of every test cell are removed from train) when pyproj is unavailable.
    """
    if buffer_m <= 0 and mode != "k_ring":
        return list(train_cells)
    if mode == "k_ring":
        banned: set[str] = set()
        for cell in test_cells:
            for offset in range(0, k_ring + 1):
                banned.update(h3.grid_disk(cell, offset))
        return [c for c in train_cells if c not in banned]

    coords = _project_centroids_to_2263(list(train_cells) + list(test_cells))
    if coords is None:
        warnings.warn(
            "pyproj unavailable; falling back to H3 k-ring buffer purge.",
            stacklevel=2,
        )
        return purge_train_neighbors(train_cells, test_cells, buffer_m, mode="k_ring")

    n_train = len(train_cells)
    train_xy = coords[:n_train]
    test_xy = coords[n_train:]
    if len(test_xy) == 0:
        return list(train_cells)
    if buffer_m <= 0:
        # Still purge exact-neighbour duplicates at 0 m (identical centroids).
        keep = np.ones(n_train, dtype=bool)
        for i in range(n_train):
            d = np.hypot(test_xy[:, 0] - train_xy[i, 0], test_xy[:, 1] - train_xy[i, 1])
            if np.any(d <= 1e-9):
                keep[i] = False
        return [c for c, k in zip(train_cells, keep, strict=True) if k]

    keep = np.ones(n_train, dtype=bool)
    for i in range(n_train):
        d = np.hypot(test_xy[:, 0] - train_xy[i, 0], test_xy[:, 1] - train_xy[i, 1])
        if np.any(d < buffer_m):
            keep[i] = False
    return [c for c, k in zip(train_cells, keep, strict=True) if k]


def min_train_test_distance_m(
    train_cells: list[str],
    test_cells: list[str],
) -> float:
    """Minimum train↔test centroid distance (m, EPSG:2263); NaN if unavailable.

    Reported alongside the buffer sensitivity table so a retained-train fraction
    of 1.0 is auditable: block-level separation can already exceed the guard band.
    """
    if not train_cells or not test_cells:
        return float("nan")
    coords = _project_centroids_to_2263(list(train_cells) + list(test_cells))
    if coords is None:
        return float("nan")
    n_train = len(train_cells)
    train_xy = coords[:n_train]
    test_xy = coords[n_train:]
    if len(test_xy) == 0:
        return float("nan")
    # Chunked to bound memory on large tables.
    best = float("inf")
    step = 512
    for start in range(0, n_train, step):
        block = train_xy[start : start + step]
        d = np.hypot(
            block[:, None, 0] - test_xy[None, :, 0],
            block[:, None, 1] - test_xy[None, :, 1],
        )
        best = min(best, float(np.min(d)))
    return best if np.isfinite(best) else float("nan")


def spatial_block_bootstrap_ci(
    y_true: np.ndarray,
    y_score: np.ndarray,
    blocks: np.ndarray,
    *,
    n_boot: int = SPATIAL_BLOCK_BOOTSTRAP_N,
    random_seed: int = 42,
) -> dict[str, float]:
    """Bootstrap 95% CI for pooled AUC/AP, resampling spatial *blocks*."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=np.float64)
    blocks = np.asarray(blocks, dtype=object)
    unique_blocks = np.unique(blocks)
    out = {
        "roc_auc_ci_low": float("nan"),
        "roc_auc_ci_high": float("nan"),
        "average_precision_ci_low": float("nan"),
        "average_precision_ci_high": float("nan"),
        "bootstrap_n": int(n_boot),
        "n_blocks_bootstrap": int(len(unique_blocks)),
    }
    if n_boot <= 0 or len(unique_blocks) < 2 or len(np.unique(y_true)) < 2:
        return out
    block_index = {b: np.where(blocks == b)[0] for b in unique_blocks}
    rng = np.random.default_rng(random_seed)
    aucs: list[float] = []
    aps: list[float] = []
    for _ in range(int(n_boot)):
        sampled = rng.choice(unique_blocks, size=len(unique_blocks), replace=True)
        idx = np.concatenate([block_index[b] for b in sampled])
        yt = y_true[idx]
        ys = y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        try:
            aucs.append(float(roc_auc_score(yt, ys)))
            aps.append(float(average_precision_score(yt, ys)))
        except ValueError:
            continue
    if aucs:
        out["roc_auc_ci_low"] = float(np.quantile(aucs, 0.025))
        out["roc_auc_ci_high"] = float(np.quantile(aucs, 0.975))
        out["average_precision_ci_low"] = float(np.quantile(aps, 0.025))
        out["average_precision_ci_high"] = float(np.quantile(aps, 0.975))
    return out


def _empty_metrics(metric_prefix: str, n_folds: int, n_blocks: int) -> dict:
    return {
        f"{metric_prefix}_n_folds": float(n_folds),
        f"{metric_prefix}_n_blocks": float(n_blocks),
        f"{metric_prefix}_accuracy_mean": float("nan"),
        f"{metric_prefix}_r2_mean": float("nan"),
        f"{metric_prefix}_f1_mean": float("nan"),
        f"{metric_prefix}_mae_mean": float("nan"),
        f"{metric_prefix}_roc_auc_mean": float("nan"),
        f"{metric_prefix}_roc_auc_pooled": float("nan"),
        f"{metric_prefix}_average_precision_mean": float("nan"),
        f"{metric_prefix}_average_precision_pooled": float("nan"),
        f"{metric_prefix}_fold_table": [],
        f"{metric_prefix}_oof_table": [],
    }


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
    buffer_m: float = 0.0,
    purge_mode: str = "meters",
    k_ring: int = 1,
    bootstrap_n: int = SPATIAL_BLOCK_BOOTSTRAP_N,
    random_seed: int = 42,
) -> dict[str, float]:
    """
    GroupKFold by H3 parent block, optionally with a physical guard-band buffer.

    Returns mean fold metrics (accuracy, r2, f1, mae) — typically lower than a
    random i.i.d. split when labels are spatially structured — plus
    threshold-independent out-of-fold discrimination metrics (ROC-AUC and
    Average Precision), reported both pooled and as fold means, with a
    spatial-block bootstrap 95% CI for the pooled values.

    ``buffer_m > 0`` purges training cells within that many metres (EPSG:2263)
    of any held-out cell, and the retained-train fraction is reported.
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
        return _empty_metrics(metric_prefix, n_splits, len(unique))

    gkf = GroupKFold(n_splits=n_splits)
    accs: list[float] = []
    r2s: list[float] = []
    f1s: list[float] = []
    maes: list[float] = []
    rocs: list[float] = []
    aps: list[float] = []
    retained_fracs: list[float] = []
    fold_rows: list[dict] = []
    oof_rows: list[dict] = []
    oof_y_true: list[np.ndarray] = []
    oof_proba: list[np.ndarray] = []
    oof_blocks: list[np.ndarray] = []

    has_cells = cells is not None
    cell_labels = np.asarray(cells, dtype=object) if has_cells else None
    if cell_labels is None:
        cell_labels = np.array([str(i) for i in range(len(X))], dtype=object)

    for fold_id, (train_idx, test_idx) in enumerate(gkf.split(X, y_class, groups)):
        if buffer_m > 0 or purge_mode == "k_ring":
            train_cells = cell_labels[train_idx].astype(str).tolist()
            test_cells = cell_labels[test_idx].astype(str).tolist()
            kept_cells = set(
                purge_train_neighbors(
                    train_cells, test_cells, buffer_m, mode=purge_mode, k_ring=k_ring
                )
            )
            keep_mask = np.array([c in kept_cells for c in train_cells])
            train_idx = train_idx[keep_mask]
            if len(train_idx) == 0:
                continue
        n_train_before = int(len(train_idx))
        retained = float(len(train_idx)) / max(len(cell_labels) - len(test_idx), 1)
        retained_fracs.append(retained)

        clf = clf_builder()
        reg = reg_builder()
        if len(np.unique(y_class[train_idx])) < 2:
            raise ValueError(
                f"Fold {fold_id} became single-class after buffering "
                f"(buffer_m={buffer_m}); cannot fit the classifier."
            )
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
        # Only meaningful when real H3 cell IDs were supplied (otherwise the
        # synthetic "0,1,2..." index labels are not valid H3 cells).
        min_dist = (
            min_train_test_distance_m(
                cell_labels[train_idx].astype(str).tolist(),
                cell_labels[test_idx].astype(str).tolist(),
            )
            if has_cells
            else float("nan")
        )
        fold_rows.append(
            {
                "fold_id": fold_id,
                "n_train": int(len(train_idx)),
                "n_train_before_purge": n_train_before,
                "retained_train_fraction": retained,
                "min_train_test_distance_m": min_dist,
                "n_test": int(len(test_idx)),
                "n_test_blocks": int(len(np.unique(test_groups))),
                "n_positive_test": int(np.sum(y_class[test_idx] == 1)),
                "n_negative_test": int(np.sum(y_class[test_idx] != 1)),
                "test_block_ids": ",".join(sorted(str(g) for g in np.unique(test_groups))),
                "buffer_m": float(buffer_m),
                "accuracy": fold["accuracy"],
                "f1": fold["f1"],
                "r2": r2,
                "mae": fold["mae"],
                "roc_auc": rocs[-1],
                "average_precision": aps[-1],
            }
        )

        oof_y_true.append(y_class[test_idx].astype(int))
        oof_proba.append(proba.astype(float))
        oof_blocks.append(test_groups.astype(object))
        for k, idx in enumerate(test_idx):
            oof_rows.append(
                {
                    "fold_id": int(fold_id),
                    "h3_index": str(cell_labels[idx]),
                    "h3_parent_block": str(test_groups[k]),
                    "y_true": int(y_class[idx]),
                    "y_proba": float(proba[k]),
                    "y_pred": int(pred_class[k]),
                }
            )

    if not oof_proba:
        return _empty_metrics(metric_prefix, n_splits, len(unique))

    min_dists = [
        float(r["min_train_test_distance_m"])
        for r in fold_rows
        if np.isfinite(r.get("min_train_test_distance_m", float("nan")))
    ]

    y_true_all = np.concatenate(oof_y_true)
    proba_all = np.concatenate(oof_proba)
    blocks_all = np.concatenate(oof_blocks)
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

    bootstrap = spatial_block_bootstrap_ci(
        y_true_all, proba_all, blocks_all, n_boot=bootstrap_n, random_seed=random_seed
    )

    out = {
        f"{metric_prefix}_n_folds": float(len(fold_rows)),
        f"{metric_prefix}_n_blocks": float(len(unique)),
        f"{metric_prefix}_accuracy_mean": float(np.mean(accs)),
        f"{metric_prefix}_accuracy_std": float(np.std(accs)),
        f"{metric_prefix}_r2_mean": float(np.mean(r2s)),
        f"{metric_prefix}_r2_std": float(np.std(r2s)),
        f"{metric_prefix}_f1_mean": float(np.mean(f1s)),
        f"{metric_prefix}_f1_std": float(np.std(f1s)),
        f"{metric_prefix}_mae_mean": float(np.mean(maes)),
        f"{metric_prefix}_roc_auc_mean": float(np.nanmean(rocs)),
        f"{metric_prefix}_roc_auc_std": float(np.nanstd(rocs)),
        f"{metric_prefix}_average_precision_mean": float(np.nanmean(aps)),
        f"{metric_prefix}_average_precision_std": float(np.nanstd(aps)),
        f"{metric_prefix}_roc_auc_pooled": pooled_roc,
        f"{metric_prefix}_average_precision_pooled": pooled_ap,
        # Deprecated aliases: sklearn Average Precision is not the trapezoid PR-AUC.
        # The paper uses "Average Precision (AP)"; these keys are kept only so older
        # scripts/registry consumers keep resolving.
        f"{metric_prefix}_pr_auc_mean": float(np.nanmean(aps)),
        f"{metric_prefix}_pr_auc_std": float(np.nanstd(aps)),
        f"{metric_prefix}_pr_auc_pooled": pooled_ap,
        f"{metric_prefix}_retained_train_fraction_mean": float(np.mean(retained_fracs)),
        f"{metric_prefix}_min_train_test_distance_m": (
            float(np.min(min_dists)) if min_dists else float("nan")
        ),
        f"{metric_prefix}_buffer_m": float(buffer_m),
        f"{metric_prefix}_roc_auc_ci_low": bootstrap["roc_auc_ci_low"],
        f"{metric_prefix}_roc_auc_ci_high": bootstrap["roc_auc_ci_high"],
        f"{metric_prefix}_average_precision_ci_low": bootstrap["average_precision_ci_low"],
        f"{metric_prefix}_average_precision_ci_high": bootstrap["average_precision_ci_high"],
        f"{metric_prefix}_bootstrap_n": bootstrap["bootstrap_n"],
        f"{metric_prefix}_fold_table": fold_rows,
        f"{metric_prefix}_oof_table": oof_rows,
    }
    return out


def buffer_sensitivity_table(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    groups: np.ndarray,
    cells: list[str],
    buffers: tuple[int, ...] = DEFAULT_CV_BUFFER_METERS,
    n_splits: int = 5,
    clf_builder=None,
    reg_builder=None,
    purge_mode: str = "meters",
    k_ring: int = 1,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Run spatial block CV at several guard-band widths; return one row each."""
    rows: list[dict] = []
    for buffer_m in buffers:
        try:
            metrics = spatial_block_cv_metrics(
                X,
                y_class,
                y_risk,
                groups,
                n_splits=n_splits,
                clf_builder=clf_builder,
                reg_builder=reg_builder,
                metric_prefix="buffer",
                cells=cells,
                buffer_m=float(buffer_m),
                purge_mode=purge_mode,
                k_ring=k_ring,
                random_seed=random_seed,
            )
        except ValueError as exc:
            rows.append(
                {
                    "buffer_m": float(buffer_m),
                    "error": str(exc),
                    "retained_train_fraction": float("nan"),
                    "roc_auc_pooled": float("nan"),
                    "average_precision_pooled": float("nan"),
                }
            )
            continue
        rows.append(
            {
                "buffer_m": float(buffer_m),
                "retained_train_fraction": metrics["buffer_retained_train_fraction_mean"],
                "min_train_test_distance_m": metrics[
                    "buffer_min_train_test_distance_m"
                ],
                "roc_auc_pooled": metrics["buffer_roc_auc_pooled"],
                "roc_auc_ci_low": metrics["buffer_roc_auc_ci_low"],
                "roc_auc_ci_high": metrics["buffer_roc_auc_ci_high"],
                "average_precision_pooled": metrics["buffer_average_precision_pooled"],
                "average_precision_ci_low": metrics["buffer_average_precision_ci_low"],
                "average_precision_ci_high": metrics["buffer_average_precision_ci_high"],
                "accuracy_mean": metrics["buffer_accuracy_mean"],
                "f1_mean": metrics["buffer_f1_mean"],
                "n_folds": metrics["buffer_n_folds"],
                "n_blocks": metrics["buffer_n_blocks"],
            }
        )
    return pd.DataFrame(rows)


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
