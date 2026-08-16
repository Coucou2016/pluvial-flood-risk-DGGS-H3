"""Shared sklearn pipelines for classifier and regressor."""

from __future__ import annotations

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pluvial_flood_risk.config import RANDOM_SEED


def build_classifier() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=80,
                    max_depth=4,
                    learning_rate=0.08,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def build_regressor() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingRegressor(
                    n_estimators=80,
                    max_depth=4,
                    learning_rate=0.08,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def build_logistic_classifier() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=500,
                    random_state=RANDOM_SEED,
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

