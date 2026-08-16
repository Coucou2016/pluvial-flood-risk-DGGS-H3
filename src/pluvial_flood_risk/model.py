"""ML models for pluvial flood risk (classification + regression)."""



from __future__ import annotations



from dataclasses import dataclass

from pathlib import Path



import joblib

import numpy as np

from sklearn.model_selection import train_test_split

from sklearn.pipeline import Pipeline



from pluvial_flood_risk.config import (

    DEFAULT_SPATIAL_CV_FOLDS,

    DEFAULT_SPATIAL_CV_K,

    FEATURE_COLUMNS,

    RANDOM_SEED,

)

from pluvial_flood_risk.estimators import build_classifier, build_regressor

from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics





@dataclass
class TrainResult:
    classifier: Pipeline
    regressor: Pipeline
    metrics: dict


def train_models(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    test_size: float = 0.2,
    cells: list[str] | None = None,
    spatial_cv_k: int = DEFAULT_SPATIAL_CV_K,
    spatial_cv_folds: int = DEFAULT_SPATIAL_CV_FOLDS,
) -> TrainResult:
    if len(np.unique(y_class)) < 2:
        raise ValueError(
            "Training labels need both flood and non-flood classes; "
            "check label threshold or input data."
        )

    X_tr, X_te, yc_tr, yc_te, yr_tr, yr_te = train_test_split(
        X,
        y_class,
        y_risk,
        test_size=test_size,
        random_state=RANDOM_SEED,
        stratify=y_class,
    )

    clf = build_classifier()
    reg = build_regressor()
    clf.fit(X_tr, yc_tr)
    reg.fit(X_tr, yr_tr)

    metrics: dict = {
        "random_split_val_accuracy": float(clf.score(X_te, yc_te)),
        "random_split_val_r2": float(reg.score(X_te, yr_te)),
        "val_accuracy": float(clf.score(X_te, yc_te)),
        "val_r2": float(reg.score(X_te, yr_te)),
    }

    if cells is not None and len(cells) == len(X):
        groups = block_ids_for_cells(cells, spatial_cv_k)
        metrics.update(
            spatial_block_cv_metrics(
                X,
                y_class,
                y_risk,
                groups,
                n_splits=spatial_cv_folds,
            )
        )

    return TrainResult(classifier=clf, regressor=reg, metrics=metrics)





def save_models(result: TrainResult, model_dir: Path) -> None:

    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(result.classifier, model_dir / "classifier.joblib")

    joblib.dump(result.regressor, model_dir / "regressor.joblib")

    joblib.dump(result.metrics, model_dir / "train_metrics.joblib")

    joblib.dump(FEATURE_COLUMNS, model_dir / "feature_columns.joblib")





def require_model_artifacts(model_dir: Path) -> None:

    missing = [

        model_dir / name

        for name in ("classifier.joblib", "regressor.joblib", "feature_columns.joblib")

        if not (model_dir / name).exists()

    ]

    if missing:

        paths = ", ".join(str(p) for p in missing)

        raise FileNotFoundError(

            f"Missing model artifact(s): {paths}. Run 'pluvial-train' (or pluvial-demo-data then train) first."

        )





def load_models(model_dir: Path) -> tuple[Pipeline, Pipeline, list[str]]:

    require_model_artifacts(model_dir)

    clf = joblib.load(model_dir / "classifier.joblib")

    reg = joblib.load(model_dir / "regressor.joblib")

    features = joblib.load(model_dir / "feature_columns.joblib")

    return clf, reg, features





def predict(

    clf: Pipeline,

    reg: Pipeline,

    X: np.ndarray,

) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

    risk = reg.predict(X)

    proba_matrix = clf.predict_proba(X)

    classes = list(clf.classes_)

    if 1 in classes:

        pos_idx = classes.index(1)

    else:

        pos_idx = 0

    proba = proba_matrix[:, pos_idx]

    pred_class = clf.predict(X)

    return risk, proba, pred_class


