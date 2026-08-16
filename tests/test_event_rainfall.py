"""Event rainfall raster hook."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pluvial_flood_risk.event_rainfall import attach_event_rainfall_raster
from pluvial_flood_risk.h3_grid import bbox_to_cells


def test_attach_event_rainfall_raster(tmp_path: Path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_bounds

    bbox = (-74.015, 40.705, -74.005, 40.712)
    cells = bbox_to_cells(*bbox, 10)
    df = pd.DataFrame({"h3_index": cells, "rainfall_mm_h": 25.0})
    path = tmp_path / "event_rainfall.tif"
    width, height = 8, 8
    arr = np.full((height, width), 55.0, dtype=np.float32)
    transform = from_bounds(*bbox, width, height)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999.0,
    ) as ds:
        ds.write(arr, 1)

    out = attach_event_rainfall_raster(df, path)
    assert out["rainfall_mm_h"].notna().any()
    assert float(out["rainfall_mm_h"].dropna().mean()) == pytest.approx(55.0, abs=1.0)


def test_attach_event_rainfall_missing_path_noop():
    df = pd.DataFrame({"h3_index": ["abc"], "rainfall_mm_h": [40.0]})
    out = attach_event_rainfall_raster(df, "does_not_exist.tif")
    assert float(out["rainfall_mm_h"].iloc[0]) == 40.0
