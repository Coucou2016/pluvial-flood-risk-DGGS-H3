import numpy as np

from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, h3_block_id, spatial_block_cv_metrics


def test_h3_block_id_coarsens():
    cells = bbox_to_cells(10.70, 59.90, 10.72, 59.92, 9)
    parent = h3_block_id(cells[0], k=2)
    assert parent != cells[0]


def test_block_ids_no_leakage_between_folds():
    cells = bbox_to_cells(10.70, 59.90, 10.85, 59.98, 9)
    groups = block_ids_for_cells(cells, k=2)
    unique = np.unique(groups)
    assert len(unique) >= 5


def test_spatial_cv_metrics_finite():
    cells = bbox_to_cells(10.70, 59.90, 10.80, 59.96, 9)
    n = len(cells)
    rng = np.random.default_rng(42)
    X = rng.normal(size=(n, 4))
    y_class = (rng.random(n) > 0.5).astype(int)
    y_risk = rng.random(n)
    groups = block_ids_for_cells(cells, k=2)
    metrics = spatial_block_cv_metrics(X, y_class, y_risk, groups, n_splits=5)
    assert metrics["spatial_cv_n_folds"] >= 2
    assert np.isfinite(metrics["spatial_cv_accuracy_mean"])
