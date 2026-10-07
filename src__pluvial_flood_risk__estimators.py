"""Shared sklearn pipelines for classifier and regressor."""

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


def build_classifier(random_state: int = RANDOM_SEED) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=GBM_N_ESTIMATORS,
                    max_depth=GBM_MAX_DEPTH,
                    learning_rate=GBM_LEARNING_RATE,
                    random_state=random_state,
                ),
            ),
        ]
    )


def build_regressor(random_state: int = RANDOM_SEED) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingRegressor(
                    n_estimators=GBM_N_ESTIMATORS,
                    max_depth=GBM_MAX_DEPTH,
                    learning_rate=GBM_LEARNING_RATE,
                    random_state=random_state,
                ),
            ),
        ]
    )


def build_logistic_classifier(random_state: int = RANDOM_SEED) -> Pipeline:
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
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )
