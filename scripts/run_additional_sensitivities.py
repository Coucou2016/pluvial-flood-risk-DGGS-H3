#!/usr/bin/env python
"""Additional Major-Revision sensitivities (land-mask, polygon thresholds, OOF metrics).

Writes:
- outputs/land_mask_sensitivity.json
- outputs/polygon_area_threshold_sensitivity.json
- outputs/oof_extended_metrics.json
- outputs/hwm_quality_oof_validation.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import FEATURE_COLUMNS, OUTPUTS_DIR, PROCESSED_DIR  # noqa: E402
from pluvial_flood_risk.features import feature_matrix  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

TABLE_LM = PROCESSED_DIR / "nyc_h3_cells.parquet"
TABLE_EXP = PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"
OOF_LM = ROOT / "models" / "nyc_smoke" / "spatial_cv_oof_predictions.csv"
OOF_EXP = ROOT / "models" / "nyc_expanded" / "spatial_cv_oof_predictions.csv"
HYDRO = ROOT / "data" / "raw" / "nyc" / "hydro_streams.geojson"


def _specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    return float(tn / (tn + fp)) if (tn + fp) else float("nan")


def oof_metrics(oof_path: Path, threshold: float = 0.5) -> dict:
    oof = pd.read_csv(oof_path)
    y = oof["y_true"].to_numpy(dtype=int)
    p = oof["y_proba"].to_numpy(dtype=float)
    pred = (p >= threshold).astype(int)
    fold_rows = []
    for fid, g in oof.groupby("fold_id"):
        yt = g["y_true"].to_numpy(dtype=int)
        yp = g["y_proba"].to_numpy(dtype=float)
        yhat = (yp >= threshold).astype(int)
        fold_rows.append(
            {
                "fold_id": int(fid),
                "n": int(len(g)),
                "accuracy": float(accuracy_score(yt, yhat)),
                "balanced_accuracy": float(balanced_accuracy_score(yt, yhat)),
                "f1": float(f1_score(yt, yhat, zero_division=0)),
                "precision": float(precision_score(yt, yhat, zero_division=0)),
                "recall": float(recall_score(yt, yhat, zero_division=0)),
                "specificity": _specificity(yt, yhat),
                "mcc": float(matthews_corrcoef(yt, yhat)) if len(np.unique(yt)) > 1 else float("nan"),
                "roc_auc": float(roc_auc_score(yt, yp)) if len(np.unique(yt)) > 1 else float("nan"),
            }
        )
    return {
        "threshold": threshold,
        "threshold_note": "prespecified operating threshold for comparability (0.5)",
        "pooled": {
            "n": int(len(oof)),
            "roc_auc": float(roc_auc_score(y, p)),
            "average_precision": float(average_precision_score(y, p)),
            "accuracy": float(accuracy_score(y, pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "specificity": _specificity(y, pred),
            "mcc": float(matthews_corrcoef(y, pred)),
        },
        "spatial_fold_variability": {
            "accuracy_mean": float(np.mean([r["accuracy"] for r in fold_rows])),
            "accuracy_std": float(np.std([r["accuracy"] for r in fold_rows])),
            "balanced_accuracy_mean": float(np.mean([r["balanced_accuracy"] for r in fold_rows])),
            "balanced_accuracy_std": float(np.std([r["balanced_accuracy"] for r in fold_rows])),
            "f1_mean": float(np.mean([r["f1"] for r in fold_rows])),
            "f1_std": float(np.std([r["f1"] for r in fold_rows])),
            "mcc_mean": float(np.nanmean([r["mcc"] for r in fold_rows])),
            "mcc_std": float(np.nanstd([r["mcc"] for r in fold_rows])),
            "folds": fold_rows,
        },
    }


def land_mask_sensitivity() -> dict:
    """Centroid-on-land proxy: exclude cells with very low impervious + near-zero elev
    that sit over water (no polygon land mask available); also report elev>0 filter.
    """
    df = pd.read_parquet(TABLE_LM)
    cells = df["h3_index"].astype(str).tolist()
    # Prefer hydro overlay if present: cell centroid not inside a water polygon is expensive;
    # use elev_m > 0 OR impervious_frac >= 0.05 as a land-ish filter, plus strict elev>0.
    masks = {
        "all_cells": np.ones(len(df), dtype=bool),
        "elevation_gt_0": df["elevation_m"].to_numpy(dtype=float) > 0.0,
        "impervious_ge_0.05_or_elev_gt_0": (
            (df["impervious_frac"].to_numpy(dtype=float) >= 0.05)
            | (df["elevation_m"].to_numpy(dtype=float) > 0.0)
        ),
    }
    rows = []
    for name, mask in masks.items():
        sub = df.loc[mask].copy()
        if len(sub) < 20 or sub["flood_class"].nunique() < 2:
            rows.append({"mask": name, "n_cells": int(len(sub)), "note": "skipped"})
            continue
        X = feature_matrix(sub)
        y_class = sub["flood_class"].to_numpy(dtype=int)
        y_risk = sub["flood_risk"].to_numpy(dtype=float)
        groups = block_ids_for_cells(sub["h3_index"].astype(str).tolist(), 2)
        m = spatial_block_cv_metrics(
            X, y_class, y_risk, groups, n_splits=5, metric_prefix="land", cells=sub["h3_index"].astype(str).tolist()
        )
        rows.append(
            {
                "mask": name,
                "n_cells": int(len(sub)),
                "n_positive": int(y_class.sum()),
                "prevalence": float(y_class.mean()),
                "roc_auc_pooled": m["land_roc_auc_pooled"],
                "accuracy_mean": m["land_accuracy_mean"],
                "f1_mean": m["land_f1_mean"],
                "note": "",
            }
        )
    return {
        "note": (
            "Land-mask proxies on Option B LM (true land-fraction polygon not assembled). "
            "Primary metrics recomputed under elevation/impervious filters."
        ),
        "rows": rows,
    }


def polygon_area_thresholds() -> dict:
    df = pd.read_parquet(TABLE_LM)
    cells = df["h3_index"].astype(str).tolist()
    X = feature_matrix(df)
    groups = block_ids_for_cells(cells, 2)
    dep = df["dep_area_frac"].to_numpy(dtype=float)
    complaint = df["complaint_presence"].to_numpy(dtype=int)
    hwm = df["ida_hwm_presence"].to_numpy(dtype=int)
    rows = []
    for thr in (0.0, 0.01, 0.05, 0.10):
        dep_pos = (dep > thr).astype(int) if thr > 0 else (dep > 1e-9).astype(int)
        # Composite rebuilt: DEP thresholded area, plus point presence unchanged
        flood_risk = np.maximum.reduce(
            [np.where(dep > thr, dep, 0.0) if thr > 0 else dep, complaint.astype(float), hwm.astype(float)]
        )
        flood_class = (flood_risk > 1e-9).astype(int)
        if len(np.unique(flood_class)) < 2:
            rows.append({"threshold": thr, "note": "single-class", "n_positive": int(flood_class.sum())})
            continue
        m = spatial_block_cv_metrics(
            X, flood_class, flood_risk, groups, n_splits=5, metric_prefix="athr", cells=cells
        )
        rows.append(
            {
                "threshold": thr,
                "n_positive": int(flood_class.sum()),
                "n_dep_positive": int(dep_pos.sum()),
                "prevalence": float(flood_class.mean()),
                "roc_auc_pooled": m["athr_roc_auc_pooled"],
                "accuracy_mean": m["athr_accuracy_mean"],
                "f1_mean": m["athr_f1_mean"],
                "note": "",
            }
        )
    return {
        "note": "Composite rebuilt with DEP area-fraction thresholds 0 / 1% / 5% / 10%.",
        "rows": rows,
    }


def hwm_quality_oof() -> dict:
    if not TABLE_EXP.exists() or not OOF_EXP.exists():
        return {"note": "expanded artifacts missing", "n_hwm_cells": 0}
    df = pd.read_parquet(TABLE_EXP)
    oof = pd.read_csv(OOF_EXP)
    merged = df.merge(oof[["h3_index", "y_proba", "y_true"]], on="h3_index", how="inner")
    hwm = merged.loc[merged["ida_hwm_presence"] == 1].copy()
    # Quality filter: keep cells whose quality string mentions Excellent or Good
    q = hwm["ida_hwm_quality"].astype(str)
    keep = q.str.contains("Excellent|Good", case=False, regex=True)
    filt = hwm.loc[keep]
    return {
        "note": (
            "Quality-filtered OOF score validation on expanded-pilot HWM cells "
            "(Excellent/Good in ida_hwm_quality). Not a full CV refit."
        ),
        "n_hwm_cells": int(len(hwm)),
        "n_quality_filtered": int(len(filt)),
        "mean_oof_score_all_hwm": float(hwm["y_proba"].mean()) if len(hwm) else None,
        "mean_oof_score_quality_filtered": float(filt["y_proba"].mean()) if len(filt) else None,
        "fraction_oof_ge_0.5_quality_filtered": float((filt["y_proba"] >= 0.5).mean())
        if len(filt)
        else None,
        "quality_values": hwm["ida_hwm_quality"].value_counts().to_dict(),
    }


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    oof_payload = {
        "lower_manhattan": oof_metrics(OOF_LM),
        "manhattan_expanded": oof_metrics(OOF_EXP) if OOF_EXP.exists() else None,
        "hyperparameter_provenance": (
            "GBM hyperparameters (n_estimators=80, max_depth=4, learning_rate=0.08, "
            "seed=42) were pre-specified without nested cross-validation tuning."
        ),
        "urban_flag_note": (
            "land_cover_urban remains in FEATURE_COLUMNS as a deterministic transform "
            "of impervious_frac (>0.45) retained for interpretability; it adds no "
            "independent information."
        ),
        "feature_columns": list(FEATURE_COLUMNS),
    }
    (OUTPUTS_DIR / "oof_extended_metrics.json").write_text(
        json.dumps(oof_payload, indent=2), encoding="utf-8"
    )
    land = land_mask_sensitivity()
    (OUTPUTS_DIR / "land_mask_sensitivity.json").write_text(
        json.dumps(land, indent=2), encoding="utf-8"
    )
    poly = polygon_area_thresholds()
    (OUTPUTS_DIR / "polygon_area_threshold_sensitivity.json").write_text(
        json.dumps(poly, indent=2), encoding="utf-8"
    )
    hwm = hwm_quality_oof()
    (OUTPUTS_DIR / "hwm_quality_oof_validation.json").write_text(
        json.dumps(hwm, indent=2), encoding="utf-8"
    )
    print(json.dumps({"oof": oof_payload, "land": land, "poly": poly, "hwm": hwm}, indent=2))


if __name__ == "__main__":
    main()
