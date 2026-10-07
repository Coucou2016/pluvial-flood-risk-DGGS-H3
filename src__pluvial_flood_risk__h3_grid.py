"""H3 DGGS indexing and polygon boundaries."""

from __future__ import annotations

import warnings

import h3
import numpy as np
from h3 import LatLngPoly
from shapely.geometry import Polygon


def bbox_to_cells(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    resolution: int,
) -> list[str]:
    """Cover a bounding box with H3 cells (compact unique set)."""
    ring = [
        (min_lat, min_lon),
        (min_lat, max_lon),
        (max_lat, max_lon),
        (max_lat, min_lon),
        (min_lat, min_lon),
    ]
    try:
        poly = LatLngPoly(ring)
        return sorted(h3.geo_to_cells(poly, resolution))
    except Exception as exc:
        warnings.warn(
            f"H3 polygon fill failed ({exc}); using lat/lon grid sampling.",
            stacklevel=2,
        )
        return _bbox_grid_sample(min_lon, min_lat, max_lon, max_lat, resolution)


def _bbox_grid_sample(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    resolution: int,
) -> list[str]:
    lats = np.linspace(min_lat, max_lat, 40)
    lons = np.linspace(min_lon, max_lon, 40)
    cells: set[str] = set()
    for lat in lats:
        for lon in lons:
            cells.add(h3.latlng_to_cell(float(lat), float(lon), resolution))
    return sorted(cells)


def cell_center(cell: str) -> tuple[float, float]:
    lat, lon = h3.cell_to_latlng(cell)
    return lon, lat


def cell_centers(cells: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Batch cell centers as (lon, lat) arrays."""
    if not cells:
        return np.array([]), np.array([])
    lats = np.empty(len(cells), dtype=np.float64)
    lons = np.empty(len(cells), dtype=np.float64)
    for i, cell in enumerate(cells):
        lat, lon = h3.cell_to_latlng(cell)
        lats[i] = lat
        lons[i] = lon
    return lons, lats


def cell_boundary_polygon(cell: str) -> Polygon:
    boundary = h3.cell_to_boundary(cell)
    # h3 returns (lat, lon); shapely wants (lon, lat)
    coords = [(lon, lat) for lat, lon in boundary]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return Polygon(coords)


def cell_parent(cell: str, parent_res: int) -> str:
    return h3.cell_to_parent(cell, parent_res)


def cell_children(cell: str, child_res: int) -> list[str]:
    return sorted(h3.cell_to_children(cell, child_res))


def cell_area_m2(cell: str) -> float:
    return float(h3.cell_area(cell, unit="m^2"))


def cell_area_km2(cell: str) -> float:
    return float(h3.cell_area(cell, unit="km^2"))


def grid_disk(cell: str, k: int) -> list[str]:
    return sorted(h3.grid_disk(cell, k))


def cell_resolution(cell: str) -> int:
    return int(h3.get_resolution(cell))


def _ring_latlng(coords_lonlat: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Shapely (lon, lat) ring → h3 (lat, lon) ring."""
    ring = [(float(lat), float(lon)) for lon, lat in coords_lonlat]
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]
    return ring


def geometry_to_candidate_cells(geom, resolution: int, k_buffer: int = 1) -> list[str]:
    """
    H3 cells that may intersect a shapely geometry, plus an optional k-ring buffer.

    Partial-edge overlaps can be missed by polygon fill; callers should compute
    exact intersection on this candidate set.
    """
    from shapely.geometry import Polygon, mapping

    if geom is None or geom.is_empty:
        return []

    cells: set[str] = set()
    gt = geom.geom_type

    if gt == "Point":
        cells.add(h3.latlng_to_cell(float(geom.y), float(geom.x), resolution))
    elif gt == "MultiPoint":
        for pt in geom.geoms:
            cells.add(h3.latlng_to_cell(float(pt.y), float(pt.x), resolution))
    elif gt in ("LineString", "LinearRing"):
        n = max(2, int(geom.length / 0.00015) + 1)
        for i in range(n):
            pt = geom.interpolate(i / (n - 1), normalized=True)
            cells.add(h3.latlng_to_cell(float(pt.y), float(pt.x), resolution))
    elif gt == "MultiLineString":
        for part in geom.geoms:
            cells.update(geometry_to_candidate_cells(part, resolution, k_buffer=0))
    elif gt == "Polygon":
        try:
            exterior = _ring_latlng(list(geom.exterior.coords))
            holes = [_ring_latlng(list(r.coords)) for r in geom.interiors]
            poly = LatLngPoly(exterior, holes) if holes else LatLngPoly(exterior)
            cells.update(h3.geo_to_cells(poly, resolution))
        except Exception:
            cells.update(_geom_bounds_sample(geom, resolution))
        if not cells:
            c = geom.centroid
            cells.add(h3.latlng_to_cell(float(c.y), float(c.x), resolution))
            cells.update(_geom_bounds_sample(geom, resolution))
    elif gt == "MultiPolygon":
        for part in geom.geoms:
            cells.update(geometry_to_candidate_cells(part, resolution, k_buffer=0))
    elif gt == "GeometryCollection":
        for part in geom.geoms:
            cells.update(geometry_to_candidate_cells(part, resolution, k_buffer=0))
    else:
        mapped = mapping(geom)
        if mapped and mapped.get("type") == "Polygon":
            cells.update(
                geometry_to_candidate_cells(Polygon(mapped["coordinates"][0]), resolution, k_buffer=0)
            )
        else:
            cells.update(_geom_bounds_sample(geom, resolution))

    if k_buffer:
        buffered: set[str] = set(cells)
        for c in cells:
            buffered.update(h3.grid_disk(c, k_buffer))
        cells = buffered
    return sorted(cells)


def _geom_bounds_sample(geom, resolution: int, n: int = 12) -> set[str]:
    minx, miny, maxx, maxy = geom.bounds
    if not np.isfinite([minx, miny, maxx, maxy]).all():
        return set()
    lons = np.linspace(minx, maxx, n)
    lats = np.linspace(miny, maxy, n)
    cells: set[str] = set()
    from shapely.geometry import Point

    for lat in lats:
        for lon in lons:
            pt = Point(float(lon), float(lat))
            if geom.intersects(pt) or geom.contains(pt):
                cells.add(h3.latlng_to_cell(float(lat), float(lon), resolution))
    c = geom.centroid
    cells.add(h3.latlng_to_cell(float(c.y), float(c.x), resolution))
    return cells


def parent_of_cell(cell: str, parent_res: int) -> str:
    """Parent at parent_res; if cell is already coarser/equal, return cell."""
    res = h3.get_resolution(cell)
    if parent_res >= res:
        return cell
    return h3.cell_to_parent(cell, parent_res)
