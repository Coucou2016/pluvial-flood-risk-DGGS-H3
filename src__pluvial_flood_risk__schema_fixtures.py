"""Tiny public-schema fixtures (NYC layer names, not live Open Data)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, box

from pluvial_flood_risk.vector_io import write_geojson_features


NYC_SCHEMA_FILES = (
    "dem.tif",
    "impervious.tif",
    "building_footprints.geojson",
    "dep_stormwater_flood.geojson",
    "flooding_311.geojson",
    "usgs_ida_hwm.geojson",
    "hydro_streams.geojson",
    "fema_sandy.geojson",
)
FIXTURE_MARKER = "SCHEMA_FIXTURE.txt"


def write_public_schema_fixtures(
    out_dir: Path | str,
    bbox: tuple[float, float, float, float],
    seed: int = 42,
) -> dict[str, Path]:
    """
    Write a miniature DEM + GeoJSON stack using NYC *public layer names*.

    Geometries are invented inside ``bbox`` so the production join/zonal code
    can be tested without downloading Open Data. Tag outputs as assembly_mode=fixture.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FIXTURE_MARKER).write_text(
        "Invented public-schema geometries for pipeline tests. Not live NYC Open Data.\n"
        "Delete this file if you replace layers with real downloads.\n",
        encoding="utf-8",
    )
    min_lon, min_lat, max_lon, max_lat = bbox
    mid_lon = (min_lon + max_lon) / 2.0
    mid_lat = (min_lat + max_lat) / 2.0
    west_lon = min_lon + 0.35 * (max_lon - min_lon)
    south_lat = min_lat + 0.40 * (max_lat - min_lat)

    paths: dict[str, Path] = {}
    paths.update(_write_rasters(out_dir, bbox, seed))

    flood = box(min_lon, min_lat, west_lon, south_lat)
    paths["flood_polygons"] = write_geojson_features(
        out_dir / "dep_stormwater_flood.geojson",
        [
            (
                flood,
                {"Flooding_Category": 2, "source": "fixture", "layer": "DEP_Stormwater"},
            )
        ],
    )

    bldg_w = 0.15 * (max_lon - min_lon)
    bldg_h = 0.15 * (max_lat - min_lat)
    buildings = [
        (box(min_lon + 0.05 * (max_lon - min_lon), min_lat + 0.05 * (max_lat - min_lat),
             min_lon + 0.05 * (max_lon - min_lon) + bldg_w,
             min_lat + 0.05 * (max_lat - min_lat) + bldg_h),
         {"BIN": 1, "HEIGHTROOF": 18.0, "source": "fixture"}),
        (box(mid_lon, mid_lat, mid_lon + bldg_w, mid_lat + bldg_h),
         {"BIN": 2, "HEIGHTROOF": 32.0, "source": "fixture"}),
        (box(max_lon - 2 * bldg_w, max_lat - 2 * bldg_h, max_lon - bldg_w, max_lat - bldg_h),
         {"BIN": 3, "HEIGHTROOF": 12.0, "source": "fixture"}),
    ]
    paths["buildings"] = write_geojson_features(out_dir / "building_footprints.geojson", buildings)

    stream = LineString(
        [
            (min_lon, mid_lat),
            (mid_lon, mid_lat - 0.1 * (max_lat - min_lat)),
            (max_lon, mid_lat),
        ]
    )
    paths["hydro"] = write_geojson_features(
        out_dir / "hydro_streams.geojson",
        [(stream, {"name": "fixture_stream", "source": "fixture"})],
    )

    p1 = Point(min_lon + 0.1 * (max_lon - min_lon), min_lat + 0.1 * (max_lat - min_lat))
    p2 = Point(min_lon + 0.2 * (max_lon - min_lon), min_lat + 0.15 * (max_lat - min_lat))
    p3 = Point(mid_lon, mid_lat)
    paths["flood_311"] = write_geojson_features(
        out_dir / "flooding_311.geojson",
        [
            (p1, {"complaint_type": "Street Flooding", "source": "fixture"}),
            (p2, {"complaint_type": "Sewer", "source": "fixture"}),
            (p3, {"complaint_type": "Street Flooding", "source": "fixture"}),
        ],
    )
    paths["ida_hwm"] = write_geojson_features(
        out_dir / "usgs_ida_hwm.geojson",
        [
            (p1, {"hwm_id": "FIX-1", "event": "Ida", "height_above_gnd": 0.4, "source": "fixture"}),
            (Point(west_lon, south_lat), {"hwm_id": "FIX-2", "event": "Ida", "height_above_gnd": 0.7, "source": "fixture"}),
        ],
    )
    # Coastal surge (Sandy) — negative control, not used as pluvial labels
    sandy = box(min_lon, min_lat, max_lon, min_lat + 0.12 * (max_lat - min_lat))
    paths["fema_sandy"] = write_geojson_features(
        out_dir / "fema_sandy.geojson",
        [(sandy, {"event": "Sandy", "hazard": "coastal_surge", "source": "fixture"})],
    )
    return paths


def _write_rasters(
    out_dir: Path,
    bbox: tuple[float, float, float, float],
    seed: int,
) -> dict[str, Path]:
    min_lon, min_lat, max_lon, max_lat = bbox
    width, height = 24, 20
    xs = np.linspace(0.0, 1.0, width)
    ys = np.linspace(0.0, 1.0, height)
    xx, yy = np.meshgrid(xs, ys)
    # Row 0 is north: low elevation in SW (ponding), higher to the NE
    elev = (8.0 + 35.0 * xx + 25.0 * (1.0 - yy)).astype(np.float32)
    rng = np.random.default_rng(seed)
    elev += rng.normal(0, 0.4, size=elev.shape).astype(np.float32)
    imperv = np.clip(0.75 - 0.55 * xx - 0.15 * yy, 0.05, 0.95).astype(np.float32)

    paths: dict[str, Path] = {}
    try:
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        return paths

    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
    dem_path = out_dir / "dem.tif"
    imp_path = out_dir / "impervious.tif"
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -9999.0,
    }
    with rasterio.open(dem_path, "w", **profile) as dst:
        dst.write(elev, 1)
    with rasterio.open(imp_path, "w", **profile) as dst:
        dst.write(imperv, 1)
    paths["dem"] = dem_path
    paths["impervious"] = imp_path
    return paths
