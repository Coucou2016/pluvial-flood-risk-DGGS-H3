"""Synthetic and observed pluvial flood risk labels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import (
    PROVENANCE_OPEN_EVIDENCE,
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


def _source_kind(path: Path | str) -> str:
    """Classify a label path by conventional filename (multi-source provenance)."""
    name = str(path).lower()
    if "dep" in name or "stormwater" in name:
        return "dep"
    if "311" in name or "complaint" in name:
        return "complaint"
    if "hwm" in name or "ida" in name:
        return "hwm"
    if "floodnet" in name:
        return "floodnet"
    if "sandy" in name or "fema" in name:
        return "coastal"
    return "generic"


def _area_frac_for_polygons(
    cells: list[str],
    cell_to_idx: dict[str, int],
    res: int,
    polygons: list,
) -> np.ndarray:
    """Intersection area fraction per cell for a union of polygons."""
    from pluvial_flood_risk.h3_grid import geometry_to_candidate_cells

    frac = np.zeros(len(cells), dtype=np.float64)
    if not polygons:
        return frac
    flood_union = _union_polygons(polygons)
    for cell in geometry_to_candidate_cells(flood_union, res, k_buffer=1):
        idx = cell_to_idx.get(cell)
        if idx is None:
            continue
        frac[idx] = _cell_intersection_fraction(cell, flood_union)
    return frac


def _count_points(
    cells: list[str],
    cell_to_idx: dict[str, int],
    res: int,
    points: list,
) -> np.ndarray:
    """Per-cell count of point geometries via H3 indexing."""
    import h3

    counts = np.zeros(len(cells), dtype=np.int64)
    for geom in points:
        pts = list(geom.geoms) if geom.geom_type == "MultiPoint" else [geom]
        for pt in pts:
            cell = h3.latlng_to_cell(float(pt.y), float(pt.x), res)
            idx = cell_to_idx.get(cell)
            if idx is not None:
                counts[idx] += 1
    return counts


def attach_observed_labels(
    df: pd.DataFrame,
    flood_polygons_path: Path | str | list[Path | str],
    risk_column: str = "observed_risk",
    class_threshold: float = 1e-9,
) -> pd.DataFrame:
    """
    Join heterogeneous open flood-evidence polygons/points to H3 cells.

    The sources are retained **separately** as source-specific columns and then
    collapsed into a composite evidence score, so the claim "sources are kept
    distinct" is true of the assembled table, not only of the documentation:

    - ``dep_area_frac`` / ``dep_nuisance_frac`` / ``dep_deep_frac`` — DEP
      stormwater polygon coverage (all / category 1 / category 2).
    - ``complaint_count`` / ``complaint_presence`` — 311 crowd-reported points.
    - ``ida_hwm_count`` / ``ida_hwm_presence`` / ``ida_hwm_quality`` — USGS Ida HWM.
    - ``evidence_sources`` — string listing which sources are present per cell.

    The composite ``flood_risk`` (flood-evidence score) is ``max(dep_area_frac,
    complaint_presence, ida_hwm_presence)``, clipped to [0,1]; a cell carrying only
    a point label saturates at 1. ``flood_area_frac`` and ``flood_point_count`` are
    kept as aggregate columns for backward compatibility and for the coastal
    overlay (where a single coastal polygon path is passed in). Source identity is
    inferred from conventional filenames (``dep_stormwater_flood``, ``flooding_311``,
    ``usgs_ida_hwm``, ``fema_sandy``); unrecognised files fall back to ``generic``
    and still contribute to the composite via geometry type.

    Parameters
    ----------
    flood_polygons_path
        GeoJSON or GPKG path, or a list of paths (multi-source open labels).
    risk_column
        Copy of the continuous evidence score (defaults to ``observed_risk``).
    class_threshold
        Minimum score for ``flood_class=1`` (any intersection by default).
    """
    from pluvial_flood_risk.h3_grid import cell_resolution
    from pluvial_flood_risk.vector_io import load_vector_records

    if "h3_index" not in df.columns:
        raise KeyError("attach_observed_labels requires an 'h3_index' column.")

    paths: list[Path | str] = (
        [flood_polygons_path]
        if isinstance(flood_polygons_path, (str, Path))
        else list(flood_polygons_path)
    )

    # --- partition records by source and geometry type ---
    dep_polygons: list = []          # (geom, category)
    other_polygons: list = []        # generic/coastal polygons
    complaint_points: list = []
    hwm_points: list = []            # (geom, quality)
    floodnet_points: list = []
    generic_points: list = []

    for path in paths:
        kind = _source_kind(path)
        for geom, props in load_vector_records(path):
            gt = geom.geom_type
            if gt in ("Polygon", "MultiPolygon"):
                cleaned = _valid_polygon(geom)
                if cleaned is None:
                    continue
                if kind == "dep":
                    dep_polygons.append((cleaned, props))
                else:
                    other_polygons.append(cleaned)
            elif gt in ("Point", "MultiPoint"):
                pts = list(geom.geoms) if gt == "MultiPoint" else [geom]
                if kind == "complaint":
                    complaint_points.extend(pts)
                elif kind == "hwm":
                    hwm_points.extend((pt, props) for pt in pts)
                elif kind == "floodnet":
                    floodnet_points.extend(pts)
                else:
                    generic_points.extend(pts)
            elif gt in ("LineString", "MultiLineString"):
                cleaned = _valid_polygon(geom.buffer(1e-5))
                if cleaned is not None:
                    other_polygons.append(cleaned)
            elif gt == "GeometryCollection":
                for part in geom.geoms:
                    if part.geom_type in ("Polygon", "MultiPolygon"):
                        cleaned = _valid_polygon(part)
                        if cleaned is not None:
                            if kind == "dep":
                                dep_polygons.append((cleaned, props))
                            else:
                                other_polygons.append(cleaned)
                    elif part.geom_type in ("Point", "MultiPoint"):
                        pts = list(part.geoms) if part.geom_type == "MultiPoint" else [part]
                        if kind == "complaint":
                            complaint_points.extend(pts)
                        elif kind == "hwm":
                            hwm_points.extend((pt, props) for pt in pts)
                        elif kind == "floodnet":
                            floodnet_points.extend(pts)
                        else:
                            generic_points.extend(pts)

    cells = df["h3_index"].astype(str).tolist()
    n = len(cells)
    res = cell_resolution(cells[0]) if n else 0
    cell_to_idx = {c: i for i, c in enumerate(cells)}

    # --- source-specific area fractions ---
    dep_geoms = [g for g, _ in dep_polygons]
    dep_area_frac = _area_frac_for_polygons(cells, cell_to_idx, res, dep_geoms)
    dep_nuisance_frac = _area_frac_for_polygons(
        cells, cell_to_idx, res,
        [g for g, p in dep_polygons if str(p.get("Flooding_Category")) in {"1", "1.0", "1.00"}],
    )
    dep_deep_frac = _area_frac_for_polygons(
        cells, cell_to_idx, res,
        [g for g, p in dep_polygons if str(p.get("Flooding_Category")) in {"2", "2.0", "2.00"}],
    )
    other_area_frac = _area_frac_for_polygons(cells, cell_to_idx, res, other_polygons)

    # --- source-specific point counts ---
    complaint_count = _count_points(cells, cell_to_idx, res, complaint_points)
    hwm_count = _count_points(cells, cell_to_idx, res, [g for g, _ in hwm_points])
    floodnet_count = _count_points(cells, cell_to_idx, res, floodnet_points)
    generic_count = _count_points(cells, cell_to_idx, res, generic_points)

    complaint_presence = (complaint_count > 0).astype(np.int64)
    ida_hwm_presence = (hwm_count > 0).astype(np.int64)

    # HWM quality summary per cell (sorted unique quality strings).
    ida_hwm_quality = [""] * n
    if hwm_points:
        for geom, props in hwm_points:
            q = props.get("hwm_quality")
            if q is None:
                continue
            import h3

            cell = h3.latlng_to_cell(float(geom.y), float(geom.x), res)
            idx = cell_to_idx.get(cell)
            if idx is not None:
                ida_hwm_quality[idx] = "; ".join(
                    sorted(set(filter(None, [ida_hwm_quality[idx], str(q)])))
                )

    # --- composite evidence score (same semantics as before) ---
    agg_area_frac = np.maximum(dep_area_frac, other_area_frac)
    agg_point_count = complaint_count + hwm_count + floodnet_count + generic_count
    has_poly = len(dep_geoms) > 0 or len(other_polygons) > 0
    if has_poly:
        risk = np.clip(
            np.maximum(agg_area_frac, (agg_point_count > 0).astype(np.float64)),
            0.0,
            1.0,
        )
    else:
        risk = (agg_point_count > 0).astype(np.float64)

    # evidence_sources bitmask string per cell
    evidence_sources = []
    for i in range(n):
        parts = []
        if dep_area_frac[i] > 0:
            parts.append("dep")
        if complaint_count[i] > 0:
            parts.append("complaint")
        if hwm_count[i] > 0:
            parts.append("hwm")
        if floodnet_count[i] > 0:
            parts.append("floodnet")
        if other_area_frac[i] > 0:
            parts.append("coastal_or_other")
        evidence_sources.append("+".join(parts) if parts else "none")

    out = df.copy()
    # aggregate columns (backward-compatible)
    out["flood_area_frac"] = agg_area_frac
    out["flood_point_count"] = agg_point_count
    # source-specific columns
    out["dep_area_frac"] = dep_area_frac
    out["dep_nuisance_frac"] = dep_nuisance_frac
    out["dep_deep_frac"] = dep_deep_frac
    out["complaint_count"] = complaint_count
    out["complaint_presence"] = complaint_presence
    out["ida_hwm_count"] = hwm_count
    out["ida_hwm_presence"] = ida_hwm_presence
    out["ida_hwm_quality"] = ida_hwm_quality
    out["evidence_sources"] = evidence_sources
    # composite target
    out[risk_column] = risk
    out[TARGET_COLUMN] = risk
    out[TARGET_CLASS_COLUMN] = (risk >= class_threshold).astype(int)
    out["label_source"] = PROVENANCE_OPEN_EVIDENCE
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
