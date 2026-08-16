"""Per-H3-cell feature engineering (terrain, hydrology proxies, exposure)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import FEATURE_COLUMNS


def _hash_seed(cell_id: str) -> int:
    return sum(ord(c) for c in cell_id) % (2**31 - 1)


def _seeded_uniform(seeds: np.ndarray, stream: int) -> np.ndarray:
    """Deterministic [0, 1) uniforms from integer seeds (reproducible demo features)."""
    x = (seeds.astype(np.uint64) * 1103515245 + stream) % (2**31 - 1)
    return x.astype(np.float64) / float(2**31 - 1)


def engineer_features_for_cells(
    cells: list[str],
    rainfall_mm_h: float = 25.0,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """
    Build feature matrix for H3 cells.

    Demo mode: deterministic pseudo-random features from cell ID so runs are reproducible.
    Replace with raster zonal stats (DEM, land use, buildings) in production.
    """
    if not cells:
        return pd.DataFrame(columns=["h3_index", *FEATURE_COLUMNS])

    seeds = np.fromiter((_hash_seed(c) for c in cells), dtype=np.int64, count=len(cells))
    if rng is not None:
        seeds = seeds ^ rng.integers(0, 2**31, size=len(cells), dtype=np.int64)

    u0 = _seeded_uniform(seeds, 1)
    u1 = _seeded_uniform(seeds, 2)
    u2 = _seeded_uniform(seeds, 3)
    lat_factor = (seeds % 1000) / 1000.0

    elevation = 5.0 + 80.0 * u0 + 20.0 * lat_factor
    slope = 0.5 + 12.0 * u1
    flow_accum = -np.log1p(-np.clip(u2, 1e-9, 1 - 1e-9)) * 2.0  # exponential-like
    impervious = np.clip(0.1 + 0.7 * _seeded_uniform(seeds, 4), 0, 1)
    building_density = impervious * (50 + 200 * _seeded_uniform(seeds, 5))
    dist_stream = 20.0 + 800.0 * _seeded_uniform(seeds, 6)
    land_cover_urban = (impervious > 0.45).astype(np.float64)

    return pd.DataFrame(
        {
            "h3_index": cells,
            "elevation_m": elevation,
            "slope_deg": slope,
            "flow_accum_proxy": flow_accum,
            "impervious_frac": impervious,
            "building_density": building_density,
            "dist_stream_m": dist_stream,
            "rainfall_mm_h": rainfall_mm_h,
            "land_cover_urban": land_cover_urban,
        }
    )


def aggregate_point_features_to_h3(
    points: pd.DataFrame,
    lon_col: str = "lon",
    lat_col: str = "lat",
    value_cols: list[str] | None = None,
    resolution: int = 9,
) -> pd.DataFrame:
    """Aggregate point samples to H3 cells (mean). Used when vector inputs exist."""
    import h3

    if value_cols is None:
        value_cols = [c for c in points.columns if c not in (lon_col, lat_col, "h3_index")]

    points = points.copy()
    lats = points[lat_col].to_numpy(dtype=np.float64)
    lons = points[lon_col].to_numpy(dtype=np.float64)
    points["h3_index"] = [
        h3.latlng_to_cell(float(lat), float(lon), resolution)
        for lat, lon in zip(lats, lons, strict=True)
    ]
    if not value_cols:
        return points.groupby("h3_index", as_index=False).size().rename(columns={"size": "point_count"})
    grouped = points.groupby("h3_index", as_index=False)[value_cols].mean()
    return grouped


def count_points_to_h3(
    points: pd.DataFrame,
    lon_col: str = "lon",
    lat_col: str = "lat",
    resolution: int = 9,
) -> pd.DataFrame:
    """Count points per H3 cell (building centroids, 311, high-water marks)."""
    import h3

    if points.empty:
        return pd.DataFrame(columns=["h3_index", "point_count"])
    out = points.copy()
    out["h3_index"] = [
        h3.latlng_to_cell(float(lat), float(lon), resolution)
        for lat, lon in zip(out[lat_col].to_numpy(), out[lon_col].to_numpy(), strict=True)
    ]
    return out.groupby("h3_index", as_index=False).size().rename(columns={"size": "point_count"})


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in metres (WGS84 sphere)."""
    r = 6_371_000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2.0) ** 2
    return float(2.0 * r * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0))))


def building_density_from_vector(
    cells: list[str],
    buildings_path,
) -> pd.DataFrame:
    """
    Buildings per km² from footprints (centroids) or points.

    Uses ``count_points_to_h3`` / ``aggregate_point_features_to_h3`` so the
    production path shares the same H3 point join as other layers.
    """
    from pluvial_flood_risk.h3_grid import cell_area_km2, cell_resolution
    from pluvial_flood_risk.vector_io import load_vector_records

    if not cells:
        return pd.DataFrame(columns=["h3_index", "building_density", "building_area_frac"])

    records = load_vector_records(buildings_path)
    res = cell_resolution(cells[0])
    rows = []
    for geom, _props in records:
        if geom is None or geom.is_empty:
            continue
        c = geom.centroid
        rows.append({"lon": float(c.x), "lat": float(c.y), "n": 1.0})
    points = pd.DataFrame(rows)
    counts = (
        count_points_to_h3(points, resolution=res)
        if not points.empty
        else pd.DataFrame(columns=["h3_index", "point_count"])
    )
    count_map = dict(zip(counts["h3_index"], counts["point_count"])) if len(counts) else {}

    from pluvial_flood_risk.h3_grid import cell_boundary_polygon, geometry_to_candidate_cells
    import shapely

    polys = [g for g, _ in records if g.geom_type in ("Polygon", "MultiPolygon")]
    area_frac = {c: 0.0 for c in cells}
    if polys:
        union = shapely.union_all(polys) if len(polys) > 1 else polys[0]
        candidates = set(geometry_to_candidate_cells(union, res, k_buffer=1))
        cell_set = set(cells)
        for cell in candidates & cell_set:
            poly = cell_boundary_polygon(cell)
            ca = poly.area
            if ca <= 0:
                continue
            try:
                inter = poly.intersection(union)
                area_frac[cell] = float(min(1.0, inter.area / ca)) if not inter.is_empty else 0.0
            except Exception:
                area_frac[cell] = 0.0

    density = []
    fracs = []
    for cell in cells:
        km2 = max(cell_area_km2(cell), 1e-12)
        density.append(float(count_map.get(cell, 0)) / km2)
        fracs.append(area_frac[cell])
    return pd.DataFrame(
        {
            "h3_index": cells,
            "building_density": density,
            "building_area_frac": fracs,
        }
    )


def dist_stream_from_vector(cells: list[str], hydro_path) -> pd.DataFrame:
    """Distance (m) from each cell centre to the nearest hydro geometry."""
    from shapely.geometry import Point
    from shapely.ops import nearest_points

    from pluvial_flood_risk.h3_grid import cell_centers
    from pluvial_flood_risk.vector_io import load_vector_records

    records = load_vector_records(hydro_path)
    geoms = [g for g, _ in records if g is not None and not g.is_empty]
    if not cells:
        return pd.DataFrame(columns=["h3_index", "dist_stream_m"])
    if not geoms:
        return pd.DataFrame({"h3_index": cells, "dist_stream_m": [np.nan] * len(cells)})

    import shapely

    hydro = shapely.union_all(geoms) if len(geoms) > 1 else geoms[0]
    lons, lats = cell_centers(cells)
    dists = []
    for lon, lat in zip(lons, lats, strict=True):
        pt = Point(float(lon), float(lat))
        try:
            nearest = nearest_points(pt, hydro)[1]
            dists.append(haversine_m(float(lon), float(lat), float(nearest.x), float(nearest.y)))
        except Exception:
            dists.append(np.nan)
    return pd.DataFrame({"h3_index": cells, "dist_stream_m": dists})


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Feature table missing columns: {missing}")
    return df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
