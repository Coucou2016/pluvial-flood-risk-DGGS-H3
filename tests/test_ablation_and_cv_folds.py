"""Spatial CV fold reporting and adaptive ablation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.ablation import adaptive_vs_fixed_ablation, write_ablation_report
from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.spatial_cv import (
    block_ids_for_cells,
    spatial_block_cv_metrics,
    write_spatial_cv_fold_table,
)
from pluvial_flood_risk.synthetic import build_demo_dataset


def test_spatial_cv_fold_table(tmp_path: Path):
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.78, 59.96), resolution=9)
    X = np.column_stack(
        [
            df["elevation_m"],
            df["impervious_frac"],
            df["rainfall_mm_h"],
        ]
    )
    y_class = df["flood_class"].to_numpy()
    y_risk = df["flood_risk"].to_numpy()
    groups = block_ids_for_cells(df["h3_index"].astype(str).tolist(), k=2)
    metrics = spatial_block_cv_metrics(X, y_class, y_risk, groups, n_splits=3)
    folds = metrics["spatial_cv_fold_table"]
    assert len(folds) >= 2
    assert {"fold_id", "n_test", "n_positive_test", "test_block_ids"} <= set(folds[0])
    path = tmp_path / "spatial_cv_folds.csv"
    table = write_spatial_cv_fold_table(folds, path)
    assert path.exists()
    assert len(table) == len(folds)


def test_adaptive_vs_fixed_ablation():
    cells = bbox_to_cells(-74.02, 40.70, -73.99, 40.73, 9)[:40]
    df = pd.DataFrame(
        {
            "h3_index": cells,
            "PFI_h": np.linspace(0.1, 0.9, len(cells)),
            "flood_probability": np.linspace(0.1, 0.9, len(cells)),
        }
    )
    metrics = adaptive_vs_fixed_ablation(df, fine_res=10, score_quantile=0.8)
    assert metrics["n_fixed_coarse"] == len(cells)
    assert metrics["n_adaptive_mixed"] >= 1
    assert "cell_count_ratio_vs_fixed" in metrics
