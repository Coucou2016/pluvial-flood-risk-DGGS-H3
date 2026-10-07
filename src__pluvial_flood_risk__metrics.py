"""Evaluation metrics for cell-level pluvial risk."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)


def evaluate_predictions(
    y_true_risk: np.ndarray,
    y_pred_risk: np.ndarray,
    y_true_class: np.ndarray,
    y_pred_class: np.ndarray,
    y_proba: np.ndarray | None = None,
) -> dict[str, float]:
    metrics: dict[str, float] = {
        "mae": float(mean_absolute_error(y_true_risk, y_pred_risk)),
        "rmse": float(np.sqrt(mean_squared_error(y_true_risk, y_pred_risk))),
        "accuracy": float(accuracy_score(y_true_class, y_pred_class)),
        "f1": float(f1_score(y_true_class, y_pred_class, zero_division=0)),
    }
    if y_proba is not None and len(np.unique(y_true_class)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true_class, y_proba))
        except ValueError:
            metrics["roc_auc"] = float("nan")
        try:
            metrics["average_precision"] = float(average_precision_score(y_true_class, y_proba))
        except ValueError:
            metrics["average_precision"] = float("nan")
    return metrics
