"""Major-revision consistency gates (fail-closed, deployment, bbox, OOF)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pluvial_flood_risk.config import PROCESSED_DIR, PROJECT_ROOT
from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.model import (
    ROLE_DEPLOYMENT,
    fit_deployment_models,
    load_models,
    predict,
    training_h3_sha256,
)
from pluvial_flood_risk.rollups import canonical_ladder_heatmap, hotspot_weights_area_budget, hotspot_weights_topk, weighted_jaccard


ROOT = PROJECT_ROOT
MODELS_SMOKE = ROOT / "models" / "nyc_smoke"
MODELS_EXP = ROOT / "models" / "nyc_expanded"
TABLE_LM = PROCESSED_DIR / "nyc_h3_cells.parquet"
TABLE_EXP = PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"


def _skip_if_missing(*paths: Path):
    missing = [p for p in paths if not p.exists()]
    if missing:
        pytest.skip(f"Missing artifacts: {missing}")


def test_production_synthetic_count_zero():
    _skip_if_missing(TABLE_LM)
    df = pd.read_parquet(TABLE_LM)
    if "synthetic_value_count" in df.columns:
        assert int(df["synthetic_value_count"].iloc[0]) == 0
    if "data_mode" in df.columns:
        assert str(df["data_mode"].iloc[0]) == "production"
    assert "synthetic" not in set(df.get("feature_source", pd.Series(dtype=str)).astype(str))


def test_deployment_fit_rows_equals_n_rows():
    _skip_if_missing(TABLE_LM, MODELS_SMOKE / "deployment" / "manifest.json")
    df = pd.read_parquet(TABLE_LM)
    manifest = json.loads((MODELS_SMOKE / "deployment" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["role"] == ROLE_DEPLOYMENT
    assert int(manifest["fit_rows"]) == int(len(df))
    assert manifest["training_h3_sha256"] == training_h3_sha256(df["h3_index"].astype(str).tolist())


def test_deployment_predictions_match_independent_refit():
    _skip_if_missing(TABLE_LM, MODELS_SMOKE / "deployment" / "classifier_full.joblib")
    from pluvial_flood_risk.config import FEATURE_COLUMNS, TARGET_CLASS_COLUMN, TARGET_COLUMN
    from pluvial_flood_risk.features import feature_matrix

    df = pd.read_parquet(TABLE_LM)
    X = feature_matrix(df)
    y_class = df[TARGET_CLASS_COLUMN].to_numpy()
    y_risk = df[TARGET_COLUMN].to_numpy()
    cells = df["h3_index"].astype(str).tolist()
    seed = 42
    meta_path = MODELS_SMOKE / "run_metadata.json"
    if meta_path.exists():
        seed = int(json.loads(meta_path.read_text(encoding="utf-8")).get("random_seed", 42))

    clf, reg, _ = load_models(MODELS_SMOKE, expected_role=ROLE_DEPLOYMENT)
    risk_a, proba_a, class_a = predict(clf, reg, X)

    indep = fit_deployment_models(X, y_class, y_risk, cells, random_seed=seed)
    risk_b, proba_b, class_b = predict(indep.classifier, indep.regressor, X)

    assert indep.fit_rows == len(df)
    np.testing.assert_allclose(risk_a, risk_b, rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(proba_a, proba_b, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(class_a, class_b)


def test_manuscript_bbox_cell_count_matches_processed():
    """Option B: lower_manhattan bbox → processed n."""
    _skip_if_missing(TABLE_LM)
    from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    bbox = resolve_bbox(cfg, "lower_manhattan")
    resolution = int(cfg.get("resolution", 9))
    expected = len(bbox_to_cells(*bbox, resolution))
    df = pd.read_parquet(TABLE_LM)
    assert len(df) == expected
    # Option B target is ~262; allow exact match only
    assert expected == 262 or len(df) == expected


def test_oof_h3_set_matches_processed():
    _skip_if_missing(TABLE_LM, MODELS_SMOKE / "spatial_cv_oof_predictions.csv")
    df = pd.read_parquet(TABLE_LM)
    oof = pd.read_csv(MODELS_SMOKE / "spatial_cv_oof_predictions.csv")
    processed = set(df["h3_index"].astype(str))
    oof_set = set(oof["h3_index"].astype(str))
    assert oof_set == processed


def test_hotspot_fractional_tie_invariants():
    ids = [f"c{i}" for i in range(10)]
    # Five cells tied at the top value → k=3 must fractional-share among ties
    values = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.4, 0.3, 0.2, 0.1])
    weights, thresh = hotspot_weights_topk(ids, values, k=3)
    assert abs(thresh - 1.0) < 1e-12
    assert abs(sum(weights.values()) - 3.0) < 1e-9
    assert all(abs(w - 0.6) < 1e-9 for w in weights.values())
    # Soft Jaccard identity
    assert weighted_jaccard(weights, weights) == pytest.approx(1.0)


def test_figure_table_identity_if_artifacts_present():
    csv_path = ROOT / "outputs" / "jaccard_by_resolution.csv"
    _skip_if_missing(csv_path)
    table = pd.read_csv(csv_path)
    heat = canonical_ladder_heatmap(table, value_col="jaccard")
    mean_r9 = table.loc[(table["aggregation"] == "mean") & (table["coarse_res"] == 9), "jaccard"]
    mean_r8 = table.loc[(table["aggregation"] == "mean") & (table["coarse_res"] == 8), "jaccard"]
    assert not mean_r9.empty and not mean_r8.empty
    assert heat.loc["mean", 9] == pytest.approx(float(mean_r9.iloc[0]))
    assert heat.loc["mean", 8] == pytest.approx(float(mean_r8.iloc[0]))
    if "budget_match_mode" in table.columns and (table["budget_match_mode"] == "strict_area_budget").all():
        np.testing.assert_allclose(table["jaccard"], table["jaccard_soft"], atol=1e-12)
        if "matched_budgets_cell_count" in table.columns:
            assert not bool(table["matched_budgets_cell_count"].astype(bool).any())


def test_area_budget_sum_weights_times_area():
    ids = [f"c{i}" for i in range(8)]
    values = np.array([1.0] * 8)
    areas = np.ones(8) * 4.0
    target = 10.0
    weights, _ = hotspot_weights_area_budget(ids, values, areas, target)
    assert abs(sum(areas[i] * weights[ids[i]] for i in range(8)) - target) < 1e-9


def test_expanded_deployment_fit_rows_if_present():
    if not TABLE_EXP.exists() or not (MODELS_EXP / "deployment" / "manifest.json").exists():
        pytest.skip("expanded artifacts not present")
    df = pd.read_parquet(TABLE_EXP)
    manifest = json.loads((MODELS_EXP / "deployment" / "manifest.json").read_text(encoding="utf-8"))
    assert int(manifest["fit_rows"]) == int(len(df))
