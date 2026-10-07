"""Generate demo training dataset on H3 grid."""



from __future__ import annotations



from pathlib import Path



import pandas as pd



from pluvial_flood_risk.config import (

    DEFAULT_BBOX,

    DEFAULT_H3_RESOLUTION,

    PROCESSED_DIR,

    PROVENANCE_SYNTHETIC,

    RAW_DIR,

)

from pluvial_flood_risk.features import engineer_features_for_cells

from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_centers

from pluvial_flood_risk.labels import attach_labels





def build_demo_dataset(

    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,

    resolution: int = DEFAULT_H3_RESOLUTION,

    rainfall_mm_h: float = 30.0,

) -> pd.DataFrame:

    min_lon, min_lat, max_lon, max_lat = bbox

    cells = bbox_to_cells(min_lon, min_lat, max_lon, max_lat, resolution)

    features = engineer_features_for_cells(cells, rainfall_mm_h=rainfall_mm_h)

    lons, lats = cell_centers(cells)

    features["lon"] = lons

    features["lat"] = lats

    features["h3_resolution"] = resolution

    features["feature_source"] = PROVENANCE_SYNTHETIC

    return attach_labels(features)





def write_demo_data(

    output_dir: Path | None = None,

    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,

    resolution: int = DEFAULT_H3_RESOLUTION,

) -> Path:

    output_dir = output_dir or PROCESSED_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    RAW_DIR.mkdir(parents=True, exist_ok=True)



    df = build_demo_dataset(bbox=bbox, resolution=resolution)

    path = output_dir / "demo_h3_cells.parquet"

    df.to_parquet(path, index=False)

    return path


