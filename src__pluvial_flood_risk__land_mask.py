"""True land / water masks for H3 cells from NHDPlus water polygons."""

from __future__ import annotations

import json
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union
from shapely.prepared import prep


def _h3_polygon(cell: str) -> Polygon:
    """H3 cell boundary as a Shapely polygon (lon/lat WGS84)."""
    boundary = h3.cell_to_boundary(cell)
    # h3 returns (lat, lon); Shapely wants (lon, lat)
    coords = [(lon, lat) for lat, lon in boundary]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return Polygon(coords)


def load_water_polygons(hydro_geojson: Path) -> list:
    """Load NHDArea / NHDWaterbody (and any Polygon) features as Shapely geometries."""
    payload = json.loads(Path(hydro_geojson).read_text(encoding="utf-8"))
    polys = []
    for feat in payload.get("features", []):
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        if gtype not in {"Polygon", "MultiPolygon"}:
            continue
        props = feat.get("properties") or {}
        layer = str(props.get("nhd_layer") or props.get("hydro_role") or "")
        # Prefer water-area / waterbody layers; still accept unnamed polygons.
        if layer and not any(
            key in layer.lower()
            for key in ("nhdarea", "nhdwaterbody", "water_area", "waterbody", "water")
        ):
            # Keep polygons even if layer string is unexpected (bbox hydro dumps).
            pass
        try:
            g = shape(geom)
        except Exception:
            continue
        if g.is_empty:
            continue
        polys.append(g)
    return polys


def cell_land_metrics(
    cells: list[str],
    hydro_geojson: Path,
) -> pd.DataFrame:
    """Per-cell land fraction and centroid-on-land flags from NHD water polygons.

    ``land_frac = 1 - (cell ∩ water) / cell_area`` (planar lon/lat area ratio;
    acceptable for relative filtering within a small Manhattan bbox).
    ``centroid_on_land`` is True when the cell centre is not inside any water polygon.
    """
    water = load_water_polygons(hydro_geojson)
    if not water:
        return pd.DataFrame(
            {
                "h3_index": cells,
                "land_frac": np.ones(len(cells), dtype=float),
                "water_frac": np.zeros(len(cells), dtype=float),
                "centroid_on_land": np.ones(len(cells), dtype=bool),
                "note": ["no_water_polygons"] * len(cells),
            }
        )

    water_union = unary_union(water)
    prepared = prep(water_union)
    rows = []
    for cell in cells:
        poly = _h3_polygon(cell)
        cell_area = float(poly.area)
        if cell_area <= 0:
            rows.append(
                {
                    "h3_index": cell,
                    "land_frac": float("nan"),
                    "water_frac": float("nan"),
                    "centroid_on_land": False,
                    "note": "zero_area",
                }
            )
            continue
        inter = poly.intersection(water_union)
        water_frac = float(inter.area / cell_area) if not inter.is_empty else 0.0
        water_frac = float(np.clip(water_frac, 0.0, 1.0))
        lat, lon = h3.cell_to_latlng(cell)
        on_land = not prepared.contains(Point(lon, lat))
        rows.append(
            {
                "h3_index": cell,
                "land_frac": 1.0 - water_frac,
                "water_frac": water_frac,
                "centroid_on_land": bool(on_land),
                "note": "",
            }
        )
    return pd.DataFrame(rows)


def apply_land_masks(
    df: pd.DataFrame,
    hydro_geojson: Path,
    land_frac_min: float = 0.5,
) -> dict[str, np.ndarray]:
    """Return named boolean masks aligned to ``df`` row order."""
    cells = df["h3_index"].astype(str).tolist()
    metrics = cell_land_metrics(cells, hydro_geojson)
    metrics = metrics.set_index("h3_index").reindex(cells)
    land_frac = metrics["land_frac"].to_numpy(dtype=float)
    centroid = metrics["centroid_on_land"].to_numpy(dtype=bool)
    return {
        "all_cells": np.ones(len(df), dtype=bool),
        "land_frac_ge_0.5": land_frac >= land_frac_min,
        "centroid_on_land": centroid,
        "land_frac_ge_0.5_and_centroid_on_land": (land_frac >= land_frac_min) & centroid,
        "_land_frac": land_frac,
        "_centroid_on_land": centroid,
    }
