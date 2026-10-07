"""CRS warp helpers for EPSG:4326 H3 joins."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import box

from pluvial_flood_risk.crs_warp import (
    reproject_geojson_to_4326,
    transform_bbox,
    warp_raster_to_4326,
)
from pluvial_flood_risk.vector_io import write_geojson_features


def test_transform_bbox_identity_4326():
    pytest.importorskip("pyproj")
    bbox = (-74.02, 40.70, -73.97, 40.76)
    out = transform_bbox(bbox, "EPSG:4326", "EPSG:4326")
    assert out[0] == pytest.approx(bbox[0], abs=1e-6)


def test_warp_raster_2263_to_4326(tmp_path: Path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    # Tiny synthetic grid tagged as EPSG:2263 (NY Long Island ft)
    # Origin roughly Lower Manhattan in State Plane feet
    arr = np.linspace(0, 10, 12, dtype=np.float32).reshape(3, 4)
    src = tmp_path / "dem_2263.tif"
    dst = tmp_path / "dem_4326.tif"
    transform = from_origin(980000.0, 200000.0, 50.0, 50.0)
    profile = {
        "driver": "GTiff",
        "height": 3,
        "width": 4,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:2263",
        "transform": transform,
        "nodata": -9999.0,
    }
    with rasterio.open(src, "w", **profile) as ds:
        ds.write(arr, 1)

    warp_raster_to_4326(src, dst)
    with rasterio.open(dst) as ds:
        assert ds.crs.to_epsg() == 4326
        assert ds.width >= 1 and ds.height >= 1
        data = ds.read(1)
        assert np.isfinite(data).any()


def test_reproject_geojson_already_4326(tmp_path: Path):
    path = tmp_path / "poly.geojson"
    write_geojson_features(path, [(box(-74.01, 40.70, -74.00, 40.71), {"id": 1})])
    out = reproject_geojson_to_4326(path, tmp_path / "out.geojson")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
