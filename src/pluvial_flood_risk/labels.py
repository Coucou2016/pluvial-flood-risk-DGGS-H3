"""Synthetic and observed pluvial flood risk labels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import (
    PROVENANCE_OBSERVED,
    PROVENANCE_SYNTHETIC,
    TARGET_CLASS_COLUMN,
    TARGET_COLUMN,
)


def synthetic_risk_score(df: pd.DataFrame) -> np.ndarray:
    """
    Physics-inspired pluvial susceptibility proxy for demo training.

    Higher risk when: low elevation, low slope (ponding), high imperviousness,
    high rainfall, high building exposure, close to streams (ponding zones).
    """
    elev = df["elevation_m"].to_numpy()
    slope = df["slope_deg"].to_numpy()
    imperv = df["impervious_frac"].to_numpy()
    rain = df["rainfall_mm_h"].to_numpy()
    buildings = df["building_density"].to_numpy()
    dist = df["dist_stream_m"].to_numpy()

    score = (
        0.25 * (100.0 - np.clip(elev, 0, 100)) / 100.0
        + 0.15 * (1.0 - np.clip(slope, 0, 15) / 15.0)
        + 0.25 * imperv
        + 0.15 * (rain / 50.0)
        + 0.10 * (buildings / 250.0)
        + 0.10 * (1.0 - np.clip(dist, 0, 500) / 500.0)
    )
    from pluvial_flood_risk.config import RANDOM_SEED

    noise = np.random.default_rng(RANDOM_SEED).normal(0, 0.05, size=len(score))
    return np.clip(score + noise, 0.0, 1.0)


def attach_labels(
    df: pd.DataFrame,
    threshold: float = 0.55,
    label_source: str | None = None,
) -> pd.DataFrame:
    from pluvial_flood_risk.config import PROVENANCE_SYNTHETIC as synth

    out = df.copy()
    out[TARGET_COLUMN] = synthetic_risk_score(out)
    out[TARGET_CLASS_COLUMN] = (out[TARGET_COLUMN] >= threshold).astype(int)
    out["label_source"] = label_source or synth
    return out


def attach_observed_labels(
    df: pd.DataFrame,
    flood_polygons_path: Path | str | list[Path | str],
    risk_column: str = "observed_risk",
    class_threshold: float = 1e-9,
) -> pd.DataFrame:
    """
    Join historical pluvial flood polygons/points to H3 cells.

    Polygons contribute intersection *area fraction* (0–1). Points contribute
    per-cell counts via H3 indexing. ``flood_risk`` is the area fraction, or 1
    when only points are present and count > 0. Sets ``label_source=observed``.

    Parameters
    ----------
    flood_polygons_path
        GeoJSON or GPKG path, or a list of paths (multi-source open labels).
    risk_column
        Copy of the continuous observed score (defaults to ``observed_risk``).
    class_threshold
        Minimum score for ``flood_class=1`` (any intersection by default).
    """
    from pluvial_flood_risk.h3_grid import (
        cell_boundary_polygon,
        cell_resolution,
        geometry_to_candidate_cells,
    )
    from pluvial_flood_risk.vector_io import load_vector_records_many

    if "h3_index" not in df.columns:
        raise KeyError("attach_observed_labels requires an 'h3_index' column.")

    records = load_vector_records_many(flood_polygons_path)
    polygons: list = []
    points: list = []
    for geom, _props in records:
        gt = geom.geom_type
        if gt in ("Polygon", "MultiPolygon"):
            cleaned = _valid_polygon(geom)
            if cleaned is not None:
                polygons.append(cleaned)
        elif gt in ("Point", "MultiPoint"):
            points.append(geom)
        elif gt in ("LineString", "MultiLineString"):
            cleaned = _valid_polygon(geom.buffer(1e-5))
            if cleaned is not None:
                polygons.append(cleaned)
        elif gt == "GeometryCollection":
            for part in geom.geoms:
                if part.geom_type in ("Polygon", "MultiPolygon"):
                    cleaned = _valid_polygon(part)
                    if cleaned is not None:
                        polygons.append(cleaned)
                elif part.geom_type in ("Point", "MultiPoint"):
                    points.append(part)

    cells = df["h3_index"].astype(str).tolist()
    n = len(cells)
    frac = np.zeros(n, dtype=np.float64)
    counts = np.zeros(n, dtype=np.int64)
    if n == 0:
        out = df.copy()
        out["flood_area_frac"] = frac
        out["flood_point_count"] = counts
        out[risk_column] = frac
        out[TARGET_COLUMN] = frac
        out[TARGET_CLASS_COLUMN] = np.zeros(n, dtype=int)
        out["label_source"] = PROVENANCE_OBSERVED
        return out

    res = cell_resolution(cells[0])
    cell_to_idx = {c: i for i, c in enumerate(cells)}

    if polygons:
        flood_union = _union_polygons(polygons)

        candidates = geometry_to_candidate_cells(flood_union, res, k_buffer=1)
        for cell in candidates:
            idx = cell_to_idx.get(cell)
            if idx is None:
                continue
            frac[idx] = _cell_intersection_fraction(cell, flood_union)

    if points:
        import h3

        for geom in points:
            pts = list(geom.geoms) if geom.geom_type == "MultiPoint" else [geom]
            for pt in pts:
                cell = h3.latlng_to_cell(float(pt.y), float(pt.x), res)
                idx = cell_to_idx.get(cell)
                if idx is not None:
                    counts[idx] += 1

    has_poly = len(polygons) > 0
    if has_poly:
        risk = np.clip(np.maximum(frac, (counts > 0).astype(np.float64)), 0.0, 1.0)
    else:
        risk = (counts > 0).astype(np.float64)

    out = df.copy()
    out["flood_area_frac"] = frac
    out["flood_point_count"] = counts
    out[risk_column] = risk
    out[TARGET_COLUMN] = risk
    out[TARGET_CLASS_COLUMN] = (risk >= class_threshold).astype(int)
    out["label_source"] = PROVENANCE_OBSERVED
    return out


def _valid_polygon(geom):
    """Repair invalid flood polygons (common in Open Data / ArcGIS mirrors)."""
    if geom is None or geom.is_empty:
        return None
    try:
        from shapely import make_valid

        g = make_valid(geom)
    except Exception:
        try:
            g = geom.buffer(0)
        except Exception:
            return None
    if g is None or g.is_empty:
        return None
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    if g.geom_type == "GeometryCollection":
        parts = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty]
        if not parts:
            return None
        return _union_polygons(parts)
    return None


def _union_polygons(polygons: list):
    """Unary union with progressive fallback for TopologyException-prone layers."""
    import shapely

    if not polygons:
        raise ValueError("no polygons to union")
    if len(polygons) == 1:
        return polygons[0]
    try:
        return shapely.union_all(polygons)
    except Exception:
        pass
    try:
        return shapely.unary_union([p.buffer(0) for p in polygons])
    except Exception:
        pass
    flood_union = polygons[0]
    for g in polygons[1:]:
        try:
            flood_union = flood_union.union(g)
        except Exception:
            try:
                flood_union = flood_union.buffer(0).union(g.buffer(0))
            except Exception:
                continue
    return flood_union


def _cell_intersection_fraction(cell: str, flood_geom) -> float:
    from pluvial_flood_risk.h3_grid import cell_boundary_polygon

    cell_poly = cell_boundary_polygon(cell)
    cell_area = cell_poly.area
    if cell_area <= 0 or flood_geom is None or flood_geom.is_empty:
        return 0.0
    try:
        inter = cell_poly.intersection(flood_geom)
    except Exception:
        try:
            inter = cell_poly.buffer(0).intersection(flood_geom.buffer(0))
        except Exception:
            return 0.0
    if inter.is_empty:
        return 0.0
    return float(min(1.0, inter.area / cell_area))
