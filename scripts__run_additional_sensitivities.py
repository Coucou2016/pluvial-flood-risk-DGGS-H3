#!/usr/bin/env python
"""Additional Major-Revision sensitivities (true land-mask, polygon thresholds, OOF, HWM, threshold).

Writes:
- outputs/land_mask_sensitivity.json
- outputs/polygon_area_threshold_sensitivity.json
- outputs/oof_extended_metrics.json
- outputs/hwm_quality_oof_validation.json
- outputs/hwm_validation.json
- outputs/operating_threshold_sensitivity.json
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

from pluvial_flood_risk.config import (  # noqa: E402
    FEATURE_COLUMNS,
    GBM_LEARNING_RATE,
    GBM_MAX_DEPTH,
    GBM_N_ESTIMATORS,
    OPERATING_THRESHOLD_DEFAULT,
    OUTPUTS_DIR,
    PROCESSED_DIR,
)
from pluvial_flood_risk.estimators import build_classifier, build_regressor  # noqa: E402
from pluvial_flood_risk.features import feature_matrix  # noqa: E402
from pluvial_flood_risk.land_mask import apply_land_masks  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

TABLE_LM = PROCESSED_DIR / "nyc_h3_cells.parquet"
TABLE_EXP = PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"
OOF_LM = ROOT / "models" / "nyc_smoke" / "spatial_cv_oof_predictions.csv"
OOF_EXP = ROOT / "models" / "nyc_expanded" / "spatial_cv_oof_predictions.csv"
HYDRO_LM = ROOT / "data" / "raw" / "nyc" / "hydro_streams.geojson"
HYDRO_EXP = ROOT / "data" / "raw" / "nyc_expanded" / "hydro_streams.geojson"
HWM_RAW = ROOT / "data" / "raw" / "nyc" / "usgs_ida_hwm.geojson"


def _specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    return float(tn / (tn + fp)) if (tn + fp) else float("nan")


def oof_metrics(oof_path: Path, threshold: float = OPERATING_THRESHOLD_DEFAULT) -> dict:
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
        "threshold_note": (
            f"prespecified operating threshold for comparability ({threshold})"
        ),
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


def _best_f1_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Select threshold maximising F1 on the provided (train) fold only."""
    if len(np.unique(y_true)) < 2:
        return OPERATING_THRESHOLD_DEFAULT
    candidates = np.unique(np.concatenate([np.linspace(0.05, 0.95, 19), y_proba]))
    best_t, best_f1 = OPERATING_THRESHOLD_DEFAULT, -1.0
    for t in candidates:
        pred = (y_proba >= t).astype(int)
        f1 = float(f1_score(y_true, pred, zero_division=0))
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
    return best_t


def operating_threshold_sensitivity(table_path: Path, pilot: str) -> dict:
    """Train-fold-only max-F1 threshold vs fixed 0.5 (never tuned on test)."""
    from sklearn.model_selection import GroupKFold

    df = pd.read_parquet(table_path)
    X = feature_matrix(df)
    y = df["flood_class"].to_numpy(dtype=int)
    y_risk = df["flood_risk"].to_numpy(dtype=float)
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, 2)
    gkf = GroupKFold(n_splits=min(5, len(np.unique(groups))))

    fixed_rows = []
    tuned_rows = []
    oof_fixed = []
    oof_tuned = []
    for fold_id, (tr, te) in enumerate(gkf.split(X, y, groups)):
        clf = build_classifier()
        clf.fit(X[tr], y[tr])
        proba = clf.predict_proba(X[te])[:, list(clf.classes_).index(1) if 1 in clf.classes_ else 0]
        yt = y[te]
        # Fixed 0.5
        pred_f = (proba >= OPERATING_THRESHOLD_DEFAULT).astype(int)
        fixed_rows.append(
            {
                "fold_id": fold_id,
                "threshold": OPERATING_THRESHOLD_DEFAULT,
                "accuracy": float(accuracy_score(yt, pred_f)),
                "f1": float(f1_score(yt, pred_f, zero_division=0)),
            }
        )
        # Train-fold max-F1 threshold applied to held-out
        train_proba = clf.predict_proba(X[tr])[
            :, list(clf.classes_).index(1) if 1 in clf.classes_ else 0
        ]
        t_star = _best_f1_threshold(y[tr], train_proba)
        pred_t = (proba >= t_star).astype(int)
        tuned_rows.append(
            {
                "fold_id": fold_id,
                "threshold_selected_on_train": t_star,
                "accuracy": float(accuracy_score(yt, pred_t)),
                "f1": float(f1_score(yt, pred_t, zero_division=0)),
            }
        )
        for i, idx in enumerate(te):
            oof_fixed.append({"y_true": int(yt[i]), "y_proba": float(proba[i]), "y_pred": int(pred_f[i])})
            oof_tuned.append(
                {
                    "y_true": int(yt[i]),
                    "y_proba": float(proba[i]),
                    "y_pred": int(pred_t[i]),
                    "threshold": t_star,
                }
            )

    def _summ(rows, key_acc="accuracy", key_f1="f1"):
        return {
            "accuracy_mean": float(np.mean([r[key_acc] for r in rows])),
            "accuracy_std": float(np.std([r[key_acc] for r in rows])),
            "f1_mean": float(np.mean([r[key_f1] for r in rows])),
            "f1_std": float(np.std([r[key_f1] for r in rows])),
            "folds": rows,
        }

    yf = np.array([r["y_true"] for r in oof_fixed])
    pf = np.array([r["y_pred"] for r in oof_fixed])
    yt = np.array([r["y_true"] for r in oof_tuned])
    pt = np.array([r["y_pred"] for r in oof_tuned])
    return {
        "pilot": pilot,
        "note": (
            "Operating threshold selected by maximising F1 on the training fold only, "
            "then applied to the held-out fold. Never tuned on test."
        ),
        "fixed_0.5": {
            **_summ(fixed_rows),
            "pooled_accuracy": float(accuracy_score(yf, pf)),
            "pooled_f1": float(f1_score(yf, pf, zero_division=0)),
        },
        "train_fold_max_f1": {
            **_summ(tuned_rows),
            "pooled_accuracy": float(accuracy_score(yt, pt)),
            "pooled_f1": float(f1_score(yt, pt, zero_division=0)),
            "mean_selected_threshold": float(
                np.mean([r["threshold_selected_on_train"] for r in tuned_rows])
            ),
        },
    }


def land_mask_sensitivity() -> dict:
    """True NHD water-polygon land fraction / centroid-on-land sensitivity."""
    df = pd.read_parquet(TABLE_LM)
    if not HYDRO_LM.exists():
        return {"note": "hydro_streams.geojson missing", "rows": []}
    masks = apply_land_masks(df, HYDRO_LM, land_frac_min=0.5)
    land_frac = masks.pop("_land_frac")
    centroid = masks.pop("_centroid_on_land")
    rows = []
    for name, mask in masks.items():
        sub = df.loc[mask].copy()
        if len(sub) < 20 or sub["flood_class"].nunique() < 2:
            rows.append(
                {
                    "mask": name,
                    "n_cells": int(len(sub)),
                    "note": "skipped (too few cells or single-class)",
                }
            )
            continue
        X = feature_matrix(sub)
        y_class = sub["flood_class"].to_numpy(dtype=int)
        y_risk = sub["flood_risk"].to_numpy(dtype=float)
        m = spatial_block_cv_metrics(
            X,
            y_class,
            y_risk,
            block_ids_for_cells(sub["h3_index"].astype(str).tolist(), 2),
            n_splits=5,
            metric_prefix="land",
            cells=sub["h3_index"].astype(str).tolist(),
        )
        rows.append(
            {
                "mask": name,
                "n_cells": int(len(sub)),
                "n_positive": int(y_class.sum()),
                "prevalence": float(y_class.mean()),
                "mean_land_frac": float(land_frac[mask].mean()),
                "roc_auc_pooled": m["land_roc_auc_pooled"],
                "accuracy_mean": m["land_accuracy_mean"],
                "f1_mean": m["land_f1_mean"],
                "note": "",
            }
        )
    return {
        "note": (
            "True land-mask sensitivity on Option B LM using NHDPlus water polygons "
            "(NHDArea/NHDWaterbody) from hydro_streams.geojson. "
            "land_frac = 1 - (cell ∩ water)/cell_area; centroid_on_land excludes "
            "cell centres inside water polygons. Primary spatial CV recomputed per mask."
        ),
        "hydro_source": str(HYDRO_LM.relative_to(ROOT)),
        "n_water_frac_gt_0": int((land_frac < 1.0 - 1e-12).sum()),
        "n_centroid_in_water": int((~centroid).sum()),
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
        flood_risk = np.maximum.reduce(
            [
                np.where(dep > thr, dep, 0.0) if thr > 0 else dep,
                complaint.astype(float),
                hwm.astype(float),
            ]
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
        "note": "Composite rebuilt with DEP area-fraction thresholds 0 / 1% / 5% / 10% (post-urban-drop features).",
        "feature_columns": list(FEATURE_COLUMNS),
        "rows": rows,
    }


def hwm_validation() -> dict:
    """Quality-filtered HWM cell OOF validation + height_above_gnd diagnostic."""
    if not TABLE_EXP.exists() or not OOF_EXP.exists():
        return {"note": "expanded artifacts missing", "n_hwm_cells": 0}

    df = pd.read_parquet(TABLE_EXP)
    oof = pd.read_csv(OOF_EXP)
    merged = df.merge(oof[["h3_index", "y_proba", "y_true"]], on="h3_index", how="inner")
    hwm = merged.loc[merged["ida_hwm_presence"] == 1].copy()
    q = hwm["ida_hwm_quality"].astype(str) if "ida_hwm_quality" in hwm.columns else pd.Series([""] * len(hwm))
    keep = q.str.contains("Excellent|Good", case=False, regex=True)
    filt = hwm.loc[keep]

    # Raw USGS height_above_gnd diagnostic (if present)
    depth_diag: dict = {"available": False}
    if HWM_RAW.exists():
        payload = json.loads(HWM_RAW.read_text(encoding="utf-8"))
        heights = []
        qualities = []
        cell_heights: dict[str, list[float]] = {}
        for feat in payload.get("features", []):
            props = feat.get("properties") or {}
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates")
            if not coords or len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            try:
                cell = h3.latlng_to_cell(lat, lon, 9)
            except Exception:
                continue
            hag = props.get("height_above_gnd")
            if hag is None:
                continue
            try:
                hag_f = float(hag)
            except (TypeError, ValueError):
                continue
            heights.append(hag_f)
            qualities.append(str(props.get("hwm_quality", "")))
            cell_heights.setdefault(cell, []).append(hag_f)
        if heights:
            cell_mean = {c: float(np.mean(v)) for c, v in cell_heights.items()}
            hwm_cells = set(hwm["h3_index"].astype(str))
            scored = []
            for c, mean_h in cell_mean.items():
                if c not in hwm_cells:
                    continue
                row = hwm.loc[hwm["h3_index"].astype(str) == c].iloc[0]
                scored.append(
                    {
                        "h3_index": c,
                        "mean_height_above_gnd_ft": mean_h,
                        "oof_score": float(row["y_proba"]),
                    }
                )
            scores = [r["oof_score"] for r in scored]
            depths = [r["mean_height_above_gnd_ft"] for r in scored]
            spearman = None
            if len(scored) >= 3:
                from scipy.stats import spearmanr

                spearman = float(spearmanr(depths, scores).correlation)
            depth_diag = {
                "available": True,
                "field": "height_above_gnd",
                "units": "ft",
                "n_raw_points_with_height": int(len(heights)),
                "n_hwm_cells_with_height": int(len(scored)),
                "mean_height_above_gnd_ft": float(np.mean(heights)),
                "spearman_height_vs_oof": spearman,
                "note": (
                    "Diagnostic only: USGS HWM height_above_gnd vs expanded-pilot OOF "
                    "probability; not used as a training target."
                ),
            }

    out = {
        "note": (
            "Quality-filtered OOF score validation on expanded-pilot HWM cells "
            "(Excellent/Good in ida_hwm_quality), plus USGS height_above_gnd diagnostic."
        ),
        "n_hwm_cells": int(len(hwm)),
        "n_quality_filtered": int(len(filt)),
        "mean_oof_score_all_hwm": float(hwm["y_proba"].mean()) if len(hwm) else None,
        "mean_oof_score_quality_filtered": float(filt["y_proba"].mean()) if len(filt) else None,
        "fraction_oof_ge_0.5_quality_filtered": float((filt["y_proba"] >= 0.5).mean())
        if len(filt)
        else None,
        "quality_values": hwm["ida_hwm_quality"].value_counts().to_dict()
        if "ida_hwm_quality" in hwm.columns
        else {},
        "height_above_gnd_diagnostic": depth_diag,
        "feature_columns_used_in_model": list(FEATURE_COLUMNS),
    }
    return out


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    assert "land_cover_urban" not in FEATURE_COLUMNS, "urban flag must be dropped from FEATURE_COLUMNS"

    oof_payload = {
        "lower_manhattan": oof_metrics(OOF_LM),
        "manhattan_expanded": oof_metrics(OOF_EXP) if OOF_EXP.exists() else None,
        "hyperparameter_provenance": (
            f"GBM hyperparameters (n_estimators={GBM_N_ESTIMATORS}, max_depth={GBM_MAX_DEPTH}, "
            f"learning_rate={GBM_LEARNING_RATE}, seed=42) are pre-specified in "
            "src/pluvial_flood_risk/config.py and estimators.py with no nested CV retuning."
        ),
        "urban_flag_note": (
            "land_cover_urban removed from FEATURE_COLUMNS / estimator inputs "
            "(deterministic copy of impervious_frac; no independent information)."
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

    hwm = hwm_validation()
    (OUTPUTS_DIR / "hwm_quality_oof_validation.json").write_text(
        json.dumps(hwm, indent=2), encoding="utf-8"
    )
    (OUTPUTS_DIR / "hwm_validation.json").write_text(
        json.dumps(hwm, indent=2), encoding="utf-8"
    )

    thr = {
        "lower_manhattan": operating_threshold_sensitivity(TABLE_LM, "lower_manhattan"),
        "manhattan_expanded": (
            operating_threshold_sensitivity(TABLE_EXP, "manhattan_expanded")
            if TABLE_EXP.exists()
            else None
        ),
    }
    (OUTPUTS_DIR / "operating_threshold_sensitivity.json").write_text(
        json.dumps(thr, indent=2), encoding="utf-8"
    )

    print(
        json.dumps(
            {"oof": oof_payload, "land": land, "poly": poly, "hwm": hwm, "threshold": thr},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
