"""Simple baselines vs GBM (logistic regression and elevation+impervious rule)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from pluvial_flood_risk.config import FEATURE_COLUMNS, TARGET_CLASS_COLUMN, TARGET_COLUMN
from pluvial_flood_risk.estimators import build_linear_regressor, build_logistic_classifier
from pluvial_flood_risk.metrics import evaluate_predictions
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics


def rule_ponding_score(df: pd.DataFrame) -> np.ndarray:
    """
    HAND / TWI-like ponding proxy: low elevation, low slope, high impervious.

    Not a hydrodynamic model — a transparent baseline for evaluate tables.
    """
    elev = df["elevation_m"].to_numpy(dtype=np.float64)
    slope = df["slope_deg"].to_numpy(dtype=np.float64)
    imperv = df["impervious_frac"].to_numpy(dtype=np.float64)
    elev_span = np.nanmax(elev) - np.nanmin(elev)
    elev_norm = (elev - np.nanmin(elev)) / (elev_span + 1e-9)
    flow = df["flow_accum_proxy"].to_numpy(dtype=np.float64) if "flow_accum_proxy" in df.columns else 1.0
    tan_s = np.tan(np.radians(np.clip(slope, 0.05, 89.0)))
    twi = np.log1p(np.clip(flow, 0, None) / (tan_s + 1e-6))
    twi_span = np.nanmax(twi) - np.nanmin(twi)
    twi_n = (twi - np.nanmin(twi)) / (twi_span + 1e-9)
    score = (
        0.40 * (1.0 - np.clip(elev_norm, 0, 1))
        + 0.35 * np.clip(imperv, 0, 1)
        + 0.15 * (1.0 - np.clip(slope, 0, 15) / 15.0)
        + 0.10 * np.clip(twi_n, 0, 1)
    )
    return np.clip(score, 0.0, 1.0)


def rule_predict_class(df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
    return (rule_ponding_score(df) >= threshold).astype(int)


def _safe_metrics(y_risk, pred_risk, y_class, pred_class, proba=None) -> dict[str, float]:
    return evaluate_predictions(y_risk, pred_risk, y_class, pred_class, proba)


def compare_baselines(
    df: pd.DataFrame,
    spatial_cv_k: int = 2,
    spatial_cv_folds: int = 5,
    feature_cols: list[str] | None = None,
) -> dict[str, float]:
    """
    In-sample + spatial-block metrics for logistic regression and the ponding rule.

    GBM metrics are produced separately by the trained model in ``run_evaluation``.
    """
    feature_cols = feature_cols or list(FEATURE_COLUMNS)
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Baseline features missing: {missing}")

    y_class = df[TARGET_CLASS_COLUMN].to_numpy()
    y_risk = df[TARGET_COLUMN].to_numpy(dtype=np.float64)
    X = df[feature_cols].to_numpy(dtype=np.float64)

    out: dict[str, float] = {}

    rule_score = rule_ponding_score(df)
    rule_class = (rule_score >= 0.5).astype(int)
    rule_m = _safe_metrics(y_risk, rule_score, y_class, rule_class, rule_score)
    out["baseline_rule_accuracy"] = rule_m["accuracy"]
    out["baseline_rule_f1"] = rule_m["f1"]
    out["baseline_rule_mae"] = rule_m["mae"]
    if "roc_auc" in rule_m:
        out["baseline_rule_roc_auc"] = rule_m["roc_auc"]

    clf = build_logistic_classifier()
    reg = build_linear_regressor()
    clf.fit(X, y_class)
    reg.fit(X, y_risk)
    proba_matrix = clf.predict_proba(X)
    classes = list(clf.classes_)
    pos_idx = classes.index(1) if 1 in classes else 0
    log_proba = proba_matrix[:, pos_idx]
    log_class = clf.predict(X)
    log_risk = reg.predict(X)
    log_m = _safe_metrics(y_risk, log_risk, y_class, log_class, log_proba)
    out["baseline_logistic_accuracy"] = log_m["accuracy"]
    out["baseline_logistic_f1"] = log_m["f1"]
    out["baseline_logistic_mae"] = log_m["mae"]
    if "roc_auc" in log_m:
        out["baseline_logistic_roc_auc"] = log_m["roc_auc"]

    if "h3_index" in df.columns and len(df) >= 10:
        groups = block_ids_for_cells(df["h3_index"].astype(str).tolist(), spatial_cv_k)
        try:
            cv = spatial_block_cv_metrics(
                X,
                y_class,
                y_risk,
                groups,
                n_splits=spatial_cv_folds,
                clf_builder=build_logistic_classifier,
                reg_builder=build_linear_regressor,
                metric_prefix="baseline_logistic_spatial_cv",
            )
            cv.pop("baseline_logistic_spatial_cv_fold_table", None)
            out.update({k: float(v) for k, v in cv.items() if isinstance(v, (int, float, np.floating))})
        except Exception:
            out["baseline_logistic_spatial_cv_accuracy_mean"] = float("nan")

        unique = np.unique(groups)
        n_splits = min(spatial_cv_folds, len(unique))
        if n_splits >= 2:
            gkf = GroupKFold(n_splits=n_splits)
            accs: list[float] = []
            f1s: list[float] = []
            for _, test_idx in gkf.split(X, y_class, groups):
                fold_df = df.iloc[test_idx]
                pred = rule_predict_class(fold_df)
                fold_m = _safe_metrics(
                    y_risk[test_idx],
                    rule_ponding_score(fold_df),
                    y_class[test_idx],
                    pred,
                    rule_ponding_score(fold_df),
                )
                accs.append(fold_m["accuracy"])
                f1s.append(fold_m["f1"])
            out["baseline_rule_spatial_cv_accuracy_mean"] = float(np.mean(accs))
            out["baseline_rule_spatial_cv_f1_mean"] = float(np.mean(f1s))

    out["baseline_note"] = (
        "rule = elevation+impervious+slope+TWI-like; logistic = L2 logistic + linear "
        "regressor; compare to GBM in_sample / spatial_cv_* . In-sample is optimistic."
    )
    return out
