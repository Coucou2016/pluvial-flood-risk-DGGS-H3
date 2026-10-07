#!/usr/bin/env python
"""Block-size sensitivity for spatial cross-validation (reviewer M1).

The primary evaluation uses H3 parent blocks at k=2 (R9 -> R7). To test whether
this coarsening is sufficient to break spatial dependence, the same spatial CV is
re-run at k=1 (R8 blocks), k=2 (R7, primary), and k=3 (R6) where enough blocks
exist, and Moran's I of the composite evidence score is computed at native R9
k-ring adjacency as a measure of the target's spatial-autocorrelation scale.

Also reports:
- leave-one-R7-block-out (LOBO) for pilots with enough blocks
- Moran's I on OOF residuals (y_true - y_proba) from the primary k=2 CV

Outputs:
- outputs/block_sensitivity.json  (nested by pilot)
- outputs/block_sensitivity.csv   (long format)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import OUTPUTS_DIR, PROCESSED_DIR  # noqa: E402
from pluvial_flood_risk.features import feature_matrix  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

SPATIAL_CV_FOLDS = 5
K_VALUES = [1, 2, 3]

PILOTS = [
    ("lower_manhattan", PROCESSED_DIR / "nyc_h3_cells.parquet"),
    ("manhattan_expanded", PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"),
]


def _clean(v: float | None) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if not np.isfinite(f) else f


def morans_i(cells: list[str], x: np.ndarray) -> dict[str, float | int]:
    """Moran's I of ``x`` under H3 k-ring(1) adjacency, restricted to in-set neighbours.

    Row-normalised weights; I = sum_ij w_ij z_i z_j / sum_i z_i^2 with z = x - mean(x).
    """
    import h3

    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    z = x - x.mean()
    denom = float(np.sum(z * z))
    if denom <= 0:
        return {"morans_i": None, "n_neighbors": 0, "n_isolated": n, "note": "zero-variance target"}

    num = 0.0
    n_edges = 0
    n_isolated = 0
    for i, c in enumerate(cells):
        try:
            neigh = [nb for nb in h3.grid_disk(c, 1) if nb != c]
        except Exception:
            neigh = []
        in_set = [idx[nb] for nb in neigh if nb in idx]
        if not in_set:
            n_isolated += 1
            continue
        w = 1.0 / len(in_set)
        for j in in_set:
            num += w * z[i] * z[j]
            n_edges += 1
    return {
        "morans_i": float(num / denom),
        "n_edges": n_edges,
        "n_isolated": n_isolated,
        "note": "",
    }


def leave_one_block_out(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    groups: np.ndarray,
    cells: list[str],
) -> dict:
    """Leave-one-R7-block-out: each unique parent block held out once."""
    from sklearn.metrics import average_precision_score, roc_auc_score

    from pluvial_flood_risk.estimators import build_classifier, build_regressor
    from pluvial_flood_risk.metrics import evaluate_predictions

    unique = np.unique(groups)
    fold_rows: list[dict] = []
    oof_y: list[np.ndarray] = []
    oof_p: list[np.ndarray] = []
    for block in unique:
        test_idx = np.where(groups == block)[0]
        train_idx = np.where(groups != block)[0]
        if len(test_idx) == 0 or len(train_idx) == 0:
            continue
        if len(np.unique(y_class[train_idx])) < 2:
            continue
        clf = build_classifier()
        reg = build_regressor()
        clf.fit(X[train_idx], y_class[train_idx])
        reg.fit(X[train_idx], y_risk[train_idx])
        pred_class = clf.predict(X[test_idx])
        risk = reg.predict(X[test_idx])
        proba_matrix = clf.predict_proba(X[test_idx])
        classes = list(clf.classes_)
        pos_idx = classes.index(1) if 1 in classes else 0
        proba = proba_matrix[:, pos_idx]
        fold = evaluate_predictions(
            y_risk[test_idx], risk, y_class[test_idx], pred_class, proba
        )
        fold_rows.append(
            {
                "held_out_block": str(block),
                "n_test": int(len(test_idx)),
                "n_positive_test": int(np.sum(y_class[test_idx] == 1)),
                "accuracy": float(fold["accuracy"]),
                "f1": float(fold["f1"]),
                "roc_auc": float(fold.get("roc_auc", float("nan"))),
                "pr_auc": float(fold.get("average_precision", float("nan"))),
            }
        )
        oof_y.append(y_class[test_idx].astype(int))
        oof_p.append(proba.astype(float))

    if not fold_rows:
        return {"n_blocks": int(len(unique)), "n_folds": 0, "note": "LOBO not fitted"}

    y_all = np.concatenate(oof_y)
    p_all = np.concatenate(oof_p)
    pooled_roc = float("nan")
    pooled_ap = float("nan")
    if len(np.unique(y_all)) > 1:
        try:
            pooled_roc = float(roc_auc_score(y_all, p_all))
        except ValueError:
            pooled_roc = float("nan")
        try:
            pooled_ap = float(average_precision_score(y_all, p_all))
        except ValueError:
            pooled_ap = float("nan")

    accs = [r["accuracy"] for r in fold_rows]
    f1s = [r["f1"] for r in fold_rows]
    rocs = [r["roc_auc"] for r in fold_rows if np.isfinite(r["roc_auc"])]
    return {
        "n_blocks": int(len(unique)),
        "n_folds": int(len(fold_rows)),
        "roc_auc_pooled": _clean(pooled_roc),
        "pr_auc_pooled": _clean(pooled_ap),
        "roc_auc_mean": _clean(float(np.nanmean(rocs))) if rocs else None,
        "roc_auc_std": _clean(float(np.nanstd(rocs))) if rocs else None,
        "accuracy_mean": _clean(float(np.mean(accs))),
        "accuracy_std": _clean(float(np.std(accs))),
        "f1_mean": _clean(float(np.mean(f1s))),
        "fold_rows": fold_rows,
        "note": "",
    }


def run_one_pilot(name: str, table_path: Path) -> dict:
    df = pd.read_parquet(table_path)
    cells = df["h3_index"].astype(str).tolist()
    X = feature_matrix(df)
    y_class = df["flood_class"].to_numpy(dtype=int)
    y_risk = df["flood_risk"].to_numpy(dtype=float)

    rows: list[dict] = []
    primary_oof: list[dict] | None = None
    for k in K_VALUES:
        groups = block_ids_for_cells(cells, k)
        n_blocks = int(len(np.unique(groups)))
        base = {
            "pilot": name,
            "k": k,
            "block_resolution": 9 - k,
            "n_blocks": n_blocks,
            "n_folds": min(SPATIAL_CV_FOLDS, n_blocks),
        }
        if n_blocks < 2:
            base.update(
                {
                    "roc_auc_pooled": None,
                    "roc_auc_mean": None,
                    "roc_auc_std": None,
                    "accuracy_mean": None,
                    "f1_mean": None,
                    "r2_mean": None,
                    "note": f"only {n_blocks} block(s); CV not fitted",
                }
            )
            rows.append(base)
            continue
        m = spatial_block_cv_metrics(
            X,
            y_class,
            y_risk,
            groups,
            n_splits=SPATIAL_CV_FOLDS,
            metric_prefix=f"block{k}",
            cells=cells,
        )
        base.update(
            {
                "roc_auc_pooled": _clean(m[f"block{k}_roc_auc_pooled"]),
                "roc_auc_mean": _clean(m[f"block{k}_roc_auc_mean"]),
                "roc_auc_std": _clean(m[f"block{k}_roc_auc_std"]),
                "accuracy_mean": _clean(m[f"block{k}_accuracy_mean"]),
                "accuracy_std": _clean(m[f"block{k}_accuracy_std"]),
                "f1_mean": _clean(m[f"block{k}_f1_mean"]),
                "r2_mean": _clean(m[f"block{k}_r2_mean"]),
                "note": "",
            }
        )
        rows.append(base)
        if k == 2:
            primary_oof = m.get(f"block{k}_oof_table")

    mi_target = morans_i(cells, y_risk)
    mi_residual = {"morans_i": None, "note": "no primary OOF"}
    if primary_oof:
        oof_df = pd.DataFrame(primary_oof)
        oof_df = oof_df.set_index("h3_index").reindex(cells)
        residual = oof_df["y_true"].to_numpy(dtype=float) - oof_df["y_proba"].to_numpy(
            dtype=float
        )
        mi_residual = morans_i(cells, residual)

    groups_r7 = block_ids_for_cells(cells, 2)
    lobo = leave_one_block_out(X, y_class, y_risk, groups_r7, cells)

    return {
        "rows": rows,
        "morans_i": mi_target,
        "morans_i_oof_residual": mi_residual,
        "lobo_r7": lobo,
    }


def main() -> None:
    payload: dict = {"spatial_cv_folds": SPATIAL_CV_FOLDS, "pilots": {}}
    all_rows: list[dict] = []
    for name, path in PILOTS:
        if not path.exists():
            print(f"SKIP {name}: {path} not found", file=sys.stderr)
            continue
        res = run_one_pilot(name, path)
        payload["pilots"][name] = {
            "block_sensitivity": res["rows"],
            "morans_i": res["morans_i"],
            "morans_i_oof_residual": res["morans_i_oof_residual"],
            "lobo_r7": {
                k: v
                for k, v in res["lobo_r7"].items()
                if k != "fold_rows"
            },
        }
        # Keep full LOBO fold table in a sidecar for audit, but also embed summary.
        lobo_folds = res["lobo_r7"].get("fold_rows") or []
        if lobo_folds:
            pd.DataFrame(lobo_folds).to_csv(
                OUTPUTS_DIR / f"lobo_r7_{name}.csv", index=False
            )
        all_rows.extend(res["rows"])

    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(outputs / "block_sensitivity.csv", index=False)
    (outputs / "block_sensitivity.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
