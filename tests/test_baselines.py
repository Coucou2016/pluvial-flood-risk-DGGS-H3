"""Logistic and ponding-rule baselines."""

from pluvial_flood_risk.baselines import compare_baselines, rule_ponding_score
from pluvial_flood_risk.synthetic import build_demo_dataset


def test_rule_score_in_unit_interval():
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.75, 59.95), resolution=9)
    scores = rule_ponding_score(df)
    assert scores.min() >= 0.0
    assert scores.max() <= 1.0


def test_compare_baselines_keys():
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.80, 59.96), resolution=9)
    metrics = compare_baselines(df, spatial_cv_k=2, spatial_cv_folds=3)
    assert 0.0 <= metrics["baseline_rule_accuracy"] <= 1.0
    assert 0.0 <= metrics["baseline_logistic_accuracy"] <= 1.0
    assert "baseline_logistic_spatial_cv_accuracy_mean" in metrics
    assert "baseline_rule_spatial_cv_accuracy_mean" in metrics
