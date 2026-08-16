"""Shared fixtures (tiny GeoTIFF for raster tests)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DEMO_DEM_PATH = FIXTURE_DIR / "demo_dem.tif"


@pytest.fixture(scope="session")
def demo_dem_path() -> Path:
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_bounds

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_DEM_PATH.exists():
        return DEMO_DEM_PATH

    # Small WGS84 grid over Oslo demo bbox subset
    west, south, east, north = 10.72, 59.91, 10.78, 59.96
    width, height = 24, 20
    data = np.linspace(10.0, 120.0, width * height, dtype=np.float32).reshape(height, width)
    transform = from_bounds(west, south, east, north, width, height)

    with rasterio.open(
        DEMO_DEM_PATH,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(data, 1)

    return DEMO_DEM_PATH
