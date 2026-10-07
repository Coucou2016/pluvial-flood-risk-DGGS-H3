"""Optional event rainfall raster → per-cell rainfall_mm_h override."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def attach_event_rainfall_raster(
    features: pd.DataFrame,
    raster_path: Path | str,
    *,
    column: str = "rainfall_mm_h",
    band: int = 1,
) -> pd.DataFrame:
    """
    Replace ``rainfall_mm_h`` with zonal mean of an event rainfall GeoTIFF.

    Raster must be EPSG:4326 (warp with ``crs_warp.ensure_raster_4326`` first).
    Missing path / ImportError leaves the table unchanged.
    """
    raster_path = Path(raster_path)
    if not raster_path.exists():
        return features
    if "h3_index" not in features.columns:
        raise ValueError("features must include h3_index")

    from pluvial_flood_risk.raster import merge_raster_feature, zonal_mean_raster_to_h3

    cells = features["h3_index"].astype(str).tolist()
    zonal = zonal_mean_raster_to_h3(cells, raster_path, band=band)
    out = features.drop(columns=[column], errors="ignore")
    out = merge_raster_feature(out, zonal, column)
    out[column] = out[column].astype(np.float64)
    return out
