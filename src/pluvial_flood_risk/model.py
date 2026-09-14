"""ML models for pluvial flood risk (classification + regression)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
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


ROLE_EVALUATION = "evaluation_split"
ROLE_DEPLOYMENT = "deployment_full"


@dataclass
class TrainResult:
    """Evaluation-split models (diagnostics only — not for maps)."""

    classifier: Pipeline
    regressor: Pipeline
    metrics: dict
    random_seed: int = RANDOM_SEED
    fit_rows: int = 0
    role: str = ROLE_EVALUATION


@dataclass
class DeploymentResult:
    """All-cell refit used only for descriptive maps / adaptive screening."""

    classifier: Pipeline
    regressor: Pipeline
    fit_rows: int
    training_h3_sha256: str
    random_seed: int
    role: str = ROLE_DEPLOYMENT
    feature_columns: list[str] = field(default_factory=lambda: list(FEATURE_COLUMNS))


def training_h3_sha256(cells: list[str]) -> str:
    payload = "\n".join(sorted(str(c) for c in cells)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def train_models(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    test_size: float = 0.2,
    cells: list[str] | None = None,
    spatial_cv_k: int = DEFAULT_SPATIAL_CV_K,
    spatial_cv_folds: int = DEFAULT_SPATIAL_CV_FOLDS,
    random_seed: int = RANDOM_SEED,
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
        random_state=random_seed,
        stratify=y_class,
    )

    clf = build_classifier(random_state=random_seed)
    reg = build_regressor(random_state=random_seed)
    clf.fit(X_tr, yc_tr)
    reg.fit(X_tr, yr_tr)

    metrics: dict = {
        "random_split_val_accuracy": float(clf.score(X_te, yc_te)),
        "random_split_val_r2": float(reg.score(X_te, yr_te)),
        "val_accuracy": float(clf.score(X_te, yc_te)),
        "val_r2": float(reg.score(X_te, yr_te)),
        "evaluation_fit_rows": int(len(X_tr)),
        "random_seed": int(random_seed),
    }

    if cells is not None and len(cells) == len(X):
        groups = block_ids_for_cells(cells, spatial_cv_k)

        def _clf():
            return build_classifier(random_state=random_seed)

        def _reg():
            return build_regressor(random_state=random_seed)

        metrics.update(
            spatial_block_cv_metrics(
                X,
                y_class,
                y_risk,
                groups,
                n_splits=spatial_cv_folds,
                cells=cells,
                clf_builder=_clf,
                reg_builder=_reg,
            )
        )

    return TrainResult(
        classifier=clf,
        regressor=reg,
        metrics=metrics,
        random_seed=random_seed,
        fit_rows=int(len(X_tr)),
        role=ROLE_EVALUATION,
    )


def fit_deployment_models(
    X: np.ndarray,
    y_class: np.ndarray,
    y_risk: np.ndarray,
    cells: list[str],
    random_seed: int = RANDOM_SEED,
) -> DeploymentResult:
    """Refit classifier/regressor on ALL cells after evaluation is complete."""
    if len(cells) != len(X):
        raise ValueError("cells length must match X rows for deployment fit.")
    clf = build_classifier(random_state=random_seed)
    reg = build_regressor(random_state=random_seed)
    clf.fit(X, y_class)
    reg.fit(X, y_risk)
    return DeploymentResult(
        classifier=clf,
        regressor=reg,
        fit_rows=int(len(X)),
        training_h3_sha256=training_h3_sha256(cells),
        random_seed=int(random_seed),
        role=ROLE_DEPLOYMENT,
        feature_columns=list(FEATURE_COLUMNS),
    )


def save_models(result: TrainResult, model_dir: Path) -> None:
    """Backward-compatible save of evaluation-split models at model_dir root."""
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.classifier, model_dir / "classifier.joblib")
    joblib.dump(result.regressor, model_dir / "regressor.joblib")
    joblib.dump(result.metrics, model_dir / "train_metrics.joblib")
    joblib.dump(FEATURE_COLUMNS, model_dir / "feature_columns.joblib")


def save_evaluation_artifacts(result: TrainResult, model_dir: Path) -> Path:
    eval_dir = Path(model_dir) / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.classifier, eval_dir / "split_diagnostic_classifier.joblib")
    joblib.dump(result.regressor, eval_dir / "split_diagnostic_regressor.joblib")
    joblib.dump(result.metrics, eval_dir / "train_metrics.joblib")
    joblib.dump(FEATURE_COLUMNS, eval_dir / "feature_columns.joblib")
    (eval_dir / "role.json").write_text(
        json.dumps(
            {
                "role": ROLE_EVALUATION,
                "fit_rows": result.fit_rows,
                "random_seed": result.random_seed,
                "note": "Random-split diagnostic only; never use for maps or adaptive.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Keep root copies for backward-compatible loaders during transition.
    save_models(result, model_dir)
    return eval_dir


def save_deployment_artifacts(deployment: DeploymentResult, model_dir: Path) -> Path:
    dep_dir = Path(model_dir) / "deployment"
    dep_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(deployment.classifier, dep_dir / "classifier_full.joblib")
    joblib.dump(deployment.regressor, dep_dir / "regressor_full.joblib")
    (dep_dir / "feature_columns.json").write_text(
        json.dumps(deployment.feature_columns, indent=2),
        encoding="utf-8",
    )
    joblib.dump(deployment.feature_columns, dep_dir / "feature_columns.joblib")
    manifest = {
        "role": ROLE_DEPLOYMENT,
        "fit_rows": deployment.fit_rows,
        "training_h3_sha256": deployment.training_h3_sha256,
        "random_seed": deployment.random_seed,
        "n_feature_columns": len(deployment.feature_columns),
    }
    (dep_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Also mirror as canonical root names so existing map code can prefer deployment.
    joblib.dump(deployment.classifier, model_dir / "classifier_full.joblib")
    joblib.dump(deployment.regressor, model_dir / "regressor_full.joblib")
    return dep_dir


def require_model_artifacts(model_dir: Path, *, prefer_deployment: bool = False) -> None:
    model_dir = Path(model_dir)
    if prefer_deployment:
        dep = model_dir / "deployment"
        candidates = [
            dep / "classifier_full.joblib",
            dep / "regressor_full.joblib",
        ]
        if all(p.exists() for p in candidates):
            return
        # Fall through to root full artifacts
        if (model_dir / "classifier_full.joblib").exists() and (
            model_dir / "regressor_full.joblib"
        ).exists():
            return
    missing = [
        model_dir / name
        for name in ("classifier.joblib", "regressor.joblib", "feature_columns.joblib")
        if not (model_dir / name).exists()
    ]
    if missing and not prefer_deployment:
        paths = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing model artifact(s): {paths}. Run 'pluvial-train' (or pluvial-demo-data then train) first."
        )
    if prefer_deployment and missing:
        # Allow evaluation-only dirs to fail clearly when maps request deployment.
        raise FileNotFoundError(
            f"Missing deployment_full artifacts under {model_dir / 'deployment'}. "
            "Re-run training so classifier_full / regressor_full are fitted on all cells."
        )


def load_models(
    model_dir: Path,
    *,
    expected_role: str | None = None,
) -> tuple[Pipeline, Pipeline, list[str]]:
    """
    Load models.

    ``expected_role='deployment_full'`` requires the all-cell refit (maps/adaptive).
    ``expected_role='evaluation_split'`` or None loads the evaluation/split diagnostic
    (backward compatible with root classifier.joblib).
    """
    model_dir = Path(model_dir)
    if expected_role == ROLE_DEPLOYMENT:
        require_model_artifacts(model_dir, prefer_deployment=True)
        dep = model_dir / "deployment"
        clf_path = dep / "classifier_full.joblib"
        reg_path = dep / "regressor_full.joblib"
        if not clf_path.exists():
            clf_path = model_dir / "classifier_full.joblib"
            reg_path = model_dir / "regressor_full.joblib"
        clf = joblib.load(clf_path)
        reg = joblib.load(reg_path)
        feat_json = dep / "feature_columns.json"
        if feat_json.exists():
            features = json.loads(feat_json.read_text(encoding="utf-8"))
        elif (dep / "feature_columns.joblib").exists():
            features = joblib.load(dep / "feature_columns.joblib")
        else:
            features = joblib.load(model_dir / "feature_columns.joblib")
        manifest_path = dep / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("role") != ROLE_DEPLOYMENT:
                raise ValueError(
                    f"Expected role={ROLE_DEPLOYMENT}, got {manifest.get('role')}"
                )
        return clf, reg, features

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
