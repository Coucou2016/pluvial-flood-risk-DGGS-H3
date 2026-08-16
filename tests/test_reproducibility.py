import numpy as np

from pluvial_flood_risk.config import RANDOM_SEED
from pluvial_flood_risk.features import engineer_features_for_cells
from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.labels import attach_labels, synthetic_risk_score
from pluvial_flood_risk.model import train_models


def test_feature_engineering_is_deterministic():
    cells = bbox_to_cells(10.70, 59.90, 10.75, 59.95, 9)[:20]
    a = engineer_features_for_cells(cells, rainfall_mm_h=30.0)
    b = engineer_features_for_cells(cells, rainfall_mm_h=30.0)
    np.testing.assert_array_equal(a["elevation_m"].to_numpy(), b["elevation_m"].to_numpy())


def test_train_metrics_reproducible_with_seed():
    cells = bbox_to_cells(10.70, 59.90, 10.80, 59.96, 9)
    df = engineer_features_for_cells(cells, rainfall_mm_h=25.0)
    df = attach_labels(df)
    X = df[
        [
            "elevation_m",
            "slope_deg",
            "flow_accum_proxy",
            "impervious_frac",
            "building_density",
            "dist_stream_m",
            "rainfall_mm_h",
            "land_cover_urban",
        ]
    ].to_numpy()
    y_class = df["flood_class"].to_numpy()
    y_risk = df["flood_risk"].to_numpy()

    m1 = train_models(X, y_class, y_risk, cells=cells).metrics
    m2 = train_models(X, y_class, y_risk, cells=cells).metrics
    assert m1["random_split_val_accuracy"] == m2["random_split_val_accuracy"]
    assert m1["spatial_cv_accuracy_mean"] == m2["spatial_cv_accuracy_mean"]
    assert RANDOM_SEED == 42


def test_label_noise_uses_global_seed():
    cells = bbox_to_cells(10.70, 59.90, 10.72, 59.92, 9)[:10]
    df = engineer_features_for_cells(cells)
    s1 = synthetic_risk_score(df)
    s2 = synthetic_risk_score(df)
    np.testing.assert_allclose(s1, s2)
