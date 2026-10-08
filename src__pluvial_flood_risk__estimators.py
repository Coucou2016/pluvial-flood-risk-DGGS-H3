"""Shared sklearn estimators for classifier and regressor baselines.

Major Revision 2026-10-08 (P1-7): **no ``StandardScaler`` before the gradient
boosting models.** Tree ensembles are invariant to monotone feature scaling, so
the scaler was a no-op that only obscured the pipeline; raw features are used
for the GBM. The scaler is retained *only* for the linear/logistic baselines,
where it is genuinely required.
"""

from __future__ import annotations

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pluvial_flood_risk.config import (
    GBM_LEARNING_RATE,
    GBM_MAX_DEPTH,
    GBM_N_ESTIMATORS,
    RANDOM_SEED,
)


def build_classifier(random_state: int = RANDOM_SEED) -> GradientBoostingClassifier:
    """GBM classifier on **raw** features (no scaler)."""
    return GradientBoostingClassifier(
        n_estimators=GBM_N_ESTIMATORS,
        max_depth=GBM_MAX_DEPTH,
        learning_rate=GBM_LEARNING_RATE,
        random_state=random_state,
    )


def build_regressor(random_state: int = RANDOM_SEED) -> GradientBoostingRegressor:
    """GBM regressor on **raw** features (no scaler)."""
    return GradientBoostingRegressor(
        n_estimators=GBM_N_ESTIMATORS,
        max_depth=GBM_MAX_DEPTH,
        learning_rate=GBM_LEARNING_RATE,
        random_state=random_state,
    )


def build_logistic_classifier(random_state: int = RANDOM_SEED) -> Pipeline:
    """L2 logistic baseline — scaler required (linear model)."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=500,
                    random_state=random_state,
                ),
            ),
        ]
    )


def build_linear_regressor() -> Pipeline:
    """Linear-regression baseline — scaler required (linear model)."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )
