"""Synthetic and observed pluvial *evidence* labels.

Major Revision (2026-10-08) target ontology
-------------------------------------------
The MAIN supervised target is a **binary union of three heterogeneous open
sources**:

    evidence_positive = (dep_area_frac > 0) | (complaint_count > 0) | (ida_hwm_count > 0)

Each source is retained separately (``dep_area_frac`` / ``dep_nuisance_frac`` /
``dep_deep_frac`` / ``complaint_count`` / ``complaint_presence`` / ``ida_hwm_count``
/ ``ida_hwm_presence`` / ``ida_hwm_quality``). The previous cross-source continuous
``max(area_frac, point_presence)`` composite is **removed from the main result**;
if a continuous target is retained it is DEP-only and named
``evidence_coverage_proxy``. A single flood-evidence *regressor* is therefore no
longer a paper headline (see ``docs/paper/audit.md``).

FloodNet is never a training label: ``attach_training_labels`` raises if any
source whose :class:`EvidenceSource.role` is not ``"training_label"`` is passed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import (
    PROVENANCE_OPEN_EVIDENCE,
    PROVENANCE_SYNTHETIC,
    TARGET_CLASS_COLUMN,
    TARGET_COLUMN,
    TARGET_PROXY_COLUMN,
)

SourceRole = Literal["training_label", "external_validation", "negative_control"]


@dataclass(frozen=True)
class EvidenceSource:
    """A typed flood-evidence layer with an explicit training role.

    ``role`` makes the training/external/negative-control separation a code
    invariant rather than a YAML convention: only ``training_label`` sources may
    reach :func:`attach_training_labels`.
    """

    path: Path
    kind: str
    role: SourceRole


def synthetic_risk_score(df: pd.DataFrame) -> np.ndarray:
    """
    Physics-inspired pluvial susceptibility proxy for demo training.

    Higher susceptibility when: low elevation, low slope (ponding), high
    imperviousness, high rainfall, high building exposure, close to water.
    ``rainfall_mm_h`` is used only in this demo formula (it is not a trained
    model input; see ``config.FEATURE_COLUMNS``).
    """
    elev = df["elevation_m"].to_numpy()
    slope = df["slope_deg"].to_numpy()
    imperv = df["impervious_frac"].to_numpy()
    rain = df["rainfall_mm_h"].to_numpy() if "rainfall_mm_h" in df.columns else np.full(len(df), 25.0)
    buildings = df["building_density"].to_numpy()
    dist_col = "dist_mapped_water_m" if "dist_mapped_water_m" in df.columns else "dist_stream_m"
    dist = df[dist_col].to_numpy()

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
    score = synthetic_risk_score(out)
    out[TARGET_COLUMN] = score
    out[TARGET_CLASS_COLUMN] = (score >= threshold).astype(int)
    # Legacy aliases (documented, not the canonical target).
    out["flood_risk"] = score
    out["flood_class"] = out[TARGET_CLASS_COLUMN]
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
    from shapely.geometry import box

    from pluvial_flood_risk.crs_warp import project_geometry_for_area
    from pluvial_flood_risk.h3_grid import cell_centers, geometry_to_candidate_cells

    frac = np.zeros(len(cells), dtype=np.float64)
    if not polygons or not cells:
        return frac
    flood_union = _union_polygons(polygons)
    # Clip to a padded bbox of the study cells before projecting — DEP mirrors
    # are citywide MultiPolygons; projecting the full city is prohibitively slow.
    lons, lats = cell_centers(cells)
    pad = 0.02
    clip = box(float(lons.min()) - pad, float(lats.min()) - pad, float(lons.max()) + pad, float(lats.max()) + pad)
    try:
        flood_union = flood_union.intersection(clip)
    except Exception:
        try:
            flood_union = flood_union.buffer(0).intersection(clip)
        except Exception:
            pass
    if flood_union is None or flood_union.is_empty:
        return frac
    flood_proj = project_geometry_for_area(flood_union)
    for cell in geometry_to_candidate_cells(flood_union, res, k_buffer=1):
        idx = cell_to_idx.get(cell)
        if idx is None:
            continue
        frac[idx] = _cell_intersection_fraction(cell, flood_proj, flood_already_projected=True)
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


def _partition_records(
    paths: list[Path | str],
) -> tuple[list, list, list, list, list, list]:
    """Split vector records into (dep poly+cat, other poly, complaint, hwm, floodnet, generic) points."""
    from pluvial_flood_risk.vector_io import load_vector_records

    dep_polygons: list = []          # (geom, category props)
    other_polygons: list = []        # generic/coastal polygons
    complaint_points: list = []
    hwm_points: list = []            # (geom, props)
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
    return dep_polygons, other_polygons, complaint_points, hwm_points, floodnet_points, generic_points


def _build_evidence_columns(df: pd.DataFrame, paths: list[Path | str]) -> pd.DataFrame:
    """Join the typed source layers onto ``df`` and derive the target columns."""
    from pluvial_flood_risk.h3_grid import cell_resolution

    if "h3_index" not in df.columns:
        raise KeyError("attach_observed_labels requires an 'h3_index' column.")

    dep_polygons, other_polygons, complaint_points, hwm_points, _, generic_points = (
        _partition_records(paths)
    )

    cells = df["h3_index"].astype(str).tolist()
    n = len(cells)
    res = cell_resolution(cells[0]) if n else 0
    cell_to_idx = {c: i for i, c in enumerate(cells)}

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

    complaint_count = _count_points(cells, cell_to_idx, res, complaint_points)
    hwm_count = _count_points(cells, cell_to_idx, res, [g for g, _ in hwm_points])
    generic_count = _count_points(cells, cell_to_idx, res, generic_points)
    floodnet_count = _count_points(cells, cell_to_idx, res, _floodnet_points(paths))

    complaint_presence = (complaint_count > 0).astype(np.int64)
    ida_hwm_presence = (hwm_count > 0).astype(np.int64)

    # HWM quality summary per cell (sorted unique quality strings).
    ida_hwm_quality = [""] * n
    if hwm_points:
        import h3

        for geom, props in hwm_points:
            q = props.get("hwm_quality")
            if q is None:
                continue
            cell = h3.latlng_to_cell(float(geom.y), float(geom.x), res)
            idx = cell_to_idx.get(cell)
            if idx is not None:
                ida_hwm_quality[idx] = "; ".join(
                    sorted(set(filter(None, [ida_hwm_quality[idx], str(q)])))
                )

    # --- MAIN binary evidence target (P0-1) ---
    # Polygon evidence is the union of DEP (categories 1-2) and any other polygon
    # source (e.g. a directly-passed coastal overlay). In the NYC main table the
    # only polygon source is DEP, so this equals ``dep_area_frac > 0``.
    poly_present = (dep_area_frac > 0) | (other_area_frac > 0)
    point_present = (complaint_count > 0) | (hwm_count > 0) | (generic_count > 0)
    evidence_positive = (poly_present | point_present).astype(np.int64)

    # Legacy aggregate columns retained for backward-compatible diagnostics.
    agg_area_frac = np.maximum(dep_area_frac, other_area_frac)
    agg_point_count = complaint_count + hwm_count + generic_count + floodnet_count

    # DEP-only continuous coverage proxy (never a cross-source max).
    evidence_coverage_proxy = dep_area_frac.copy()

    evidence_sources = []
    for i in range(n):
        parts = []
        if dep_area_frac[i] > 0:
            parts.append("dep")
        if complaint_count[i] > 0:
            parts.append("complaint")
        if hwm_count[i] > 0:
            parts.append("hwm")
        if other_area_frac[i] > 0:
            parts.append("coastal_or_other")
        evidence_sources.append("+".join(parts) if parts else "none")

    out = df.copy()
    out["flood_area_frac"] = agg_area_frac
    out["flood_point_count"] = agg_point_count
    out["dep_area_frac"] = dep_area_frac
    out["dep_nuisance_frac"] = dep_nuisance_frac
    out["dep_deep_frac"] = dep_deep_frac
    out["complaint_count"] = complaint_count
    out["complaint_presence"] = complaint_presence
    out["ida_hwm_count"] = hwm_count
    out["ida_hwm_presence"] = ida_hwm_presence
    out["ida_hwm_quality"] = ida_hwm_quality
    out["evidence_sources"] = evidence_sources
    out[TARGET_PROXY_COLUMN] = evidence_coverage_proxy
    # Canonical main target (binary) + a float score column that is the binary
    # indicator, NOT a cross-source continuous composite.
    out[TARGET_CLASS_COLUMN] = evidence_positive
    out[TARGET_COLUMN] = evidence_positive.astype(np.float64)
    # Legacy aliases for older call sites / figures.
    out["flood_class"] = evidence_positive
    out["flood_risk"] = evidence_positive.astype(np.float64)
    out["label_source"] = PROVENANCE_OPEN_EVIDENCE
    return out


def _floodnet_points(paths: list[Path | str]) -> list:
    """FloodNet points are counted only for a diagnostic column, never the target."""
    from pluvial_flood_risk.vector_io import load_vector_records

    pts: list = []
    for path in paths:
        if _source_kind(path) != "floodnet":
            continue
        for geom, _props in load_vector_records(path):
            gt = geom.geom_type
            if gt in ("Point", "MultiPoint"):
                pts.extend(list(geom.geoms) if gt == "MultiPoint" else [geom])
    return pts


def attach_observed_labels(
    df: pd.DataFrame,
    flood_polygons_path: Path | str | list[Path | str],
    risk_column: str = "observed_risk",
    class_threshold: float = 1e-9,
) -> pd.DataFrame:
    """
    Join heterogeneous open flood-evidence polygons/points to H3 cells.

    The sources are retained **separately** as source-specific columns and then
    collapsed into the binary ``evidence_positive`` target (union of polygon and
    point evidence), so the claim "sources are kept distinct" is true of the
    assembled table:

    - ``dep_area_frac`` / ``dep_nuisance_frac`` / ``dep_deep_frac`` — DEP
      stormwater polygon coverage (all / category 1 / category 2).
    - ``complaint_count`` / ``complaint_presence`` — 311 crowd-reported points.
    - ``ida_hwm_count`` / ``ida_hwm_presence`` / ``ida_hwm_quality`` — USGS Ida HWM.
    - ``evidence_coverage_proxy`` — DEP-only continuous area fraction (not a
      cross-source max).
    - ``evidence_sources`` — string listing which sources are present per cell.

    ``flood_area_frac`` and ``flood_point_count`` are kept as legacy aggregate
    columns for backward compatibility and for the coastal overlay (where a single
    coastal polygon path is passed in). Source identity is inferred from
    conventional filenames (``dep_stormwater_flood``, ``flooding_311``,
    ``usgs_ida_hwm``, ``fema_sandy``); unrecognised files fall back to ``generic``.

    Parameters
    ----------
    flood_polygons_path
        GeoJSON or GPKG path, or a list of paths (multi-source open labels).
    risk_column
        Legacy alias column set to the binary evidence indicator as float.
    class_threshold
        Unused; retained for call-site compatibility. The target is a binary union.
    """
    del class_threshold
    paths: list[Path | str] = (
        [flood_polygons_path]
        if isinstance(flood_polygons_path, (str, Path))
        else list(flood_polygons_path)
    )
    out = _build_evidence_columns(df, paths)
    out[risk_column] = out[TARGET_COLUMN]
    return out


def training_label_paths(sources: list[EvidenceSource]) -> list[Path]:
    """Paths whose role is ``training_label`` (fails closed on misuse)."""
    return [Path(s.path) for s in sources if s.role == "training_label"]


def attach_training_labels(
    df: pd.DataFrame,
    sources: list[EvidenceSource],
) -> pd.DataFrame:
    """
    Attach the main evidence target from *training-label* sources only.

    Raises
    ------
    ValueError
        If any source is not ``role == "training_label"`` (e.g. FloodNet
        external validation or a Sandy negative control). FloodNet physically
        cannot enter training through this path.
    """
    illegal = [s for s in sources if s.role != "training_label"]
    if illegal:
        detail = ", ".join(f"{s.kind}:{s.path} (role={s.role})" for s in illegal)
        raise ValueError(f"Non-training source passed to attach_training_labels: {detail}")
    return attach_observed_labels(df, training_label_paths(sources))


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


def _cell_intersection_fraction(
    cell: str,
    flood_geom,
    *,
    flood_already_projected: bool = False,
) -> float:
    from pluvial_flood_risk.crs_warp import project_geometry_for_area
    from pluvial_flood_risk.h3_grid import cell_boundary_polygon

    cell_poly = cell_boundary_polygon(cell)
    # Project cell (and flood if needed) to EPSG:2263 so area ratios use
    # projected units, not geographic degrees.
    cell_proj = project_geometry_for_area(cell_poly)
    flood_proj = flood_geom if flood_already_projected else project_geometry_for_area(flood_geom)
    cell_area = cell_proj.area
    if cell_area <= 0 or flood_proj is None or flood_proj.is_empty:
        return 0.0
    try:
        inter = cell_proj.intersection(flood_proj)
    except Exception:
        try:
            inter = cell_proj.buffer(0).intersection(flood_proj.buffer(0))
        except Exception:
            return 0.0
    if inter.is_empty:
        return 0.0
    return float(min(1.0, inter.area / cell_area))
