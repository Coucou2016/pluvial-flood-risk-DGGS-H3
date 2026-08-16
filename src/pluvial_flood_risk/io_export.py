"""Export H3 cell-level risk to Parquet and GeoJSON."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pluvial_flood_risk.h3_grid import cell_boundary_polygon


def to_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _row_value(row, column: str, default: float = 0.0) -> float:
    val = getattr(row, column, default)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return float(val)


def to_geojson(df: pd.DataFrame, path: Path, value_column: str = "predicted_risk") -> None:
    if "h3_index" not in df.columns:
        raise KeyError("GeoJSON export requires an 'h3_index' column.")

    features = []
    for row in df.itertuples(index=False):
        cell = row.h3_index
        geom = cell_boundary_polygon(cell)
        if hasattr(row, value_column):
            risk_val = _row_value(row, value_column)
        else:
            risk_val = _row_value(row, "flood_risk")
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "h3_index": cell,
                    value_column: risk_val,
                    "predicted_class": int(_row_value(row, "predicted_class", 0)),
                    "flood_probability": _row_value(row, "flood_probability", 0.0),
                },
                "geometry": geom.__geo_interface__,
            }
        )
    collection = {"type": "FeatureCollection", "features": features}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(collection), encoding="utf-8")
