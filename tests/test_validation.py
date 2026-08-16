import pandas as pd

from pluvial_flood_risk.config import FEATURE_COLUMNS, PROVENANCE_SYNTHETIC
from pluvial_flood_risk.synthetic import build_demo_dataset
from pluvial_flood_risk.validation import validate_training_table


def test_demo_dataset_passes_core_checks():
    df = build_demo_dataset()
    issues = validate_training_table(df)
    assert not any("Missing feature" in i for i in issues)
    assert any("synthetic" in i.lower() for i in issues)


def test_nan_feature_detected():
    df = build_demo_dataset()
    df.loc[0, "elevation_m"] = float("nan")
    issues = validate_training_table(df)
    assert any("NaN" in i for i in issues)


def test_provenance_columns_present():
    df = build_demo_dataset()
    assert (df["feature_source"] == PROVENANCE_SYNTHETIC).all()
    assert (df["label_source"] == PROVENANCE_SYNTHETIC).all()
    assert set(FEATURE_COLUMNS).issubset(df.columns)
