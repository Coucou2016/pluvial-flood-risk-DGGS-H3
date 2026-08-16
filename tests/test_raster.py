import pytest

from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.raster import merge_raster_feature, zonal_mean_raster_to_h3


def test_zonal_mean_raster_to_h3(demo_dem_path):
    cells = bbox_to_cells(10.72, 59.91, 10.78, 59.96, 9)[:12]
    zonal = zonal_mean_raster_to_h3(cells, demo_dem_path)
    assert len(zonal) == len(cells)
    assert zonal["zonal_mean"].notna().all()
    assert zonal["zonal_mean"].between(10, 120).all()


def test_merge_raster_feature(demo_dem_path):
    cells = bbox_to_cells(10.72, 59.91, 10.76, 59.94, 9)[:8]
    import pandas as pd

    features = pd.DataFrame({"h3_index": cells})
    zonal = zonal_mean_raster_to_h3(cells, demo_dem_path)
    merged = merge_raster_feature(features, zonal, "elevation_m")
    assert "elevation_m" in merged.columns
    assert merged["elevation_m"].notna().all()


def test_zonal_mean_excludes_mask_fill_when_src_nodata_none(tmp_path):
    """Regression: 3DEP exports often lack nodata; mask fill must not enter the mean."""
    rasterio = pytest.importorskip("rasterio")
    import numpy as np
    from rasterio.transform import from_bounds

    bbox = (-74.015, 40.705, -74.005, 40.712)
    path = tmp_path / "dem_nonodata.tif"
    width, height = 10, 10
    arr = np.full((height, width), 12.0, dtype=np.float32)
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
        nodata=None,
    ) as ds:
        ds.write(arr, 1)

    cells = bbox_to_cells(*bbox, 10)[:6]
    zonal = zonal_mean_raster_to_h3(cells, path)
    assert zonal["zonal_mean"].notna().all()
    assert zonal["zonal_mean"].between(10, 14).all()


def test_zonal_slope_deg_from_dem(demo_dem_path):
    from pluvial_flood_risk.raster import zonal_slope_deg_from_dem

    cells = bbox_to_cells(10.72, 59.91, 10.78, 59.96, 9)[:8]
    slope = zonal_slope_deg_from_dem(cells, demo_dem_path)
    assert len(slope) == len(cells)
    assert slope["slope_deg"].notna().all()
    assert (slope["slope_deg"] >= 0).all()


def test_d8_flow_accumulation_drains_to_pit():
    import numpy as np

    from pluvial_flood_risk.raster import d8_flow_accumulation

    dem = np.array(
        [
            [3.0, 3.0, 3.0],
            [3.0, 1.0, 3.0],
            [3.0, 3.0, 3.0],
        ]
    )
    accum = d8_flow_accumulation(dem)
    assert accum[1, 1] == pytest.approx(9.0)
    assert accum[1, 1] == accum.max()


def test_zonal_flow_accum_from_dem(demo_dem_path):
    from pluvial_flood_risk.raster import zonal_flow_accum_from_dem

    cells = bbox_to_cells(10.72, 59.91, 10.78, 59.96, 9)[:8]
    flow = zonal_flow_accum_from_dem(cells, demo_dem_path)
    assert len(flow) == len(cells)
    assert flow["flow_accum_proxy"].notna().all()
    assert (flow["flow_accum_proxy"] > 0).all()
