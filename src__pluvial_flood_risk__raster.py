"""Raster → H3 zonal statistics (optional rasterio)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.h3_grid import cell_boundary_polygon


def require_rasterio():
    try:
        import rasterio  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Raster support requires rasterio. Install with: pip install -e '.[raster]'"
        ) from exc


def zonal_mean_raster_to_h3(
    cells: list[str],
    raster_path: Path | str,
    band: int = 1,
    nodata: float | None = None,
) -> pd.DataFrame:
    """
    Mean raster value per H3 cell (mask by cell polygon).

    Production pipelines should use aligned CRS rasters; this helper assumes
    the raster CRS matches cell boundary coordinates (EPSG:4326 for demo fixtures).
    """
    require_rasterio()
    import rasterio

    raster_path = Path(raster_path)
    with rasterio.open(raster_path) as src:
        return _zonal_mean_from_src(cells, src, band=band, nodata=nodata)


def _zonal_mean_from_src(
    cells: list[str],
    src,
    band: int = 1,
    nodata: float | None = None,
) -> pd.DataFrame:
    from rasterio.mask import mask

    if nodata is None:
        nodata = src.nodata
    fill = nodata if nodata is not None else -9999.0
    rows: list[dict] = []
    for cell in cells:
        geom = cell_boundary_polygon(cell)
        try:
            data, _ = mask(
                src,
                [geom.__geo_interface__],
                crop=True,
                filled=True,
                nodata=fill,
            )
        except ValueError:
            rows.append({"h3_index": cell, "zonal_mean": np.nan})
            continue

        band_data = data[band - 1].astype(np.float64)
        # Always drop the mask fill value (even when src.nodata was None)
        valid = band_data[band_data != fill]
        valid = valid[np.isfinite(valid)]
        mean_val = float(np.nanmean(valid)) if valid.size else np.nan
        rows.append({"h3_index": cell, "zonal_mean": mean_val})
    return pd.DataFrame(rows)


def zonal_mean_array_to_h3(
    cells: list[str],
    array: np.ndarray,
    transform,
    crs,
    nodata: float = -9999.0,
) -> pd.DataFrame:
    """Zonal mean from an in-memory 2-D array (same CRS as H3 cell boundaries)."""
    require_rasterio()
    import rasterio
    from rasterio.io import MemoryFile

    arr = np.asarray(array, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError("array must be 2-D")
    height, width = arr.shape
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
    }
    with MemoryFile() as mem:
        with mem.open(**profile) as dataset:
            dataset.write(arr, 1)
            return _zonal_mean_from_src(cells, dataset, nodata=nodata)


def slope_degrees_from_dem_array(dem: np.ndarray, transform, center_lat: float) -> np.ndarray:
    """Approximate slope in degrees from a DEM (EPSG:4326 pixel sizes → metres)."""
    px_w = float(transform.a)
    px_h = abs(float(transform.e))
    dx_m = max(abs(px_w) * 111_320.0 * np.cos(np.radians(center_lat)), 1e-6)
    dy_m = max(px_h * 110_540.0, 1e-6)
    gy, gx = np.gradient(np.asarray(dem, dtype=np.float64))
    slope_rad = np.arctan(np.sqrt((gx / dx_m) ** 2 + (gy / dy_m) ** 2))
    return np.degrees(slope_rad)


def d8_flow_accumulation(dem: np.ndarray) -> np.ndarray:
    """
    Single-flow D8 accumulation: each cell starts at 1 and drains to the lowest
    of its 8 neighbours. A cheap HAND/TWI-like proxy when a hydro raster is absent.
    """
    z = np.asarray(dem, dtype=np.float64)
    height, width = z.shape
    filled = np.nan_to_num(z, nan=np.nanmax(z) if np.isfinite(z).any() else 0.0)
    offsets = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    receiver_i = np.full((height, width), -1, dtype=np.int32)
    receiver_j = np.full((height, width), -1, dtype=np.int32)
    for i in range(height):
        for j in range(width):
            best = filled[i, j]
            bi, bj = -1, -1
            for di, dj in offsets:
                ni, nj = i + di, j + dj
                if 0 <= ni < height and 0 <= nj < width and filled[ni, nj] < best:
                    best = filled[ni, nj]
                    bi, bj = ni, nj
            receiver_i[i, j] = bi
            receiver_j[i, j] = bj

    accum = np.ones((height, width), dtype=np.float64)
    order = np.argsort(-filled.ravel(), kind="stable")
    for idx in order:
        i, j = divmod(int(idx), width)
        ri, rj = int(receiver_i[i, j]), int(receiver_j[i, j])
        if ri >= 0:
            accum[ri, rj] += accum[i, j]
    accum = np.where(np.isfinite(z), accum, np.nan)
    return accum


def zonal_flow_accum_from_dem(
    cells: list[str],
    dem_path: Path | str,
    band: int = 1,
) -> pd.DataFrame:
    """Mean D8 flow-accumulation proxy per H3 cell from a DEM GeoTIFF."""
    require_rasterio()
    import rasterio

    dem_path = Path(dem_path)
    with rasterio.open(dem_path) as src:
        dem = src.read(band).astype(np.float64)
        nodata = src.nodata
        if nodata is not None:
            dem = np.where(dem == nodata, np.nan, dem)
        accum = d8_flow_accumulation(dem)
        accum = np.where(np.isfinite(accum), accum, -9999.0)
        zonal = zonal_mean_array_to_h3(
            cells,
            accum.astype(np.float32),
            src.transform,
            src.crs,
            nodata=-9999.0,
        )
    return zonal.rename(columns={"zonal_mean": "flow_accum_proxy"})


def zonal_slope_deg_from_dem(
    cells: list[str],
    dem_path: Path | str,
    band: int = 1,
) -> pd.DataFrame:
    """Mean slope (degrees) per H3 cell, derived from a DEM GeoTIFF."""
    require_rasterio()
    import rasterio

    dem_path = Path(dem_path)
    with rasterio.open(dem_path) as src:
        dem = src.read(band).astype(np.float64)
        nodata = src.nodata
        if nodata is not None:
            dem = np.where(dem == nodata, np.nan, dem)
        center_lat = (src.bounds.top + src.bounds.bottom) / 2.0
        slope = slope_degrees_from_dem_array(np.nan_to_num(dem, nan=0.0), src.transform, center_lat)
        if nodata is not None:
            slope = np.where(np.isnan(dem), -9999.0, slope)
        zonal = zonal_mean_array_to_h3(
            cells,
            slope.astype(np.float32),
            src.transform,
            src.crs,
            nodata=-9999.0,
        )
    zonal = zonal.rename(columns={"zonal_mean": "slope_deg"})
    return zonal


def merge_raster_feature(
    features: pd.DataFrame,
    zonal: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:
    """Attach zonal raster column to an H3 feature table."""
    merged = features.merge(zonal, on="h3_index", how="left")
    merged[column_name] = merged["zonal_mean"]
    merged = merged.drop(columns=["zonal_mean"])
    return merged
