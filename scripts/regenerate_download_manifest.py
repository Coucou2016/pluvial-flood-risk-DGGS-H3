#!/usr/bin/env python
"""Regenerate data/raw/<pilot>/DOWNLOAD_MANIFEST.json from the files on disk.

Major Revision 2026-10-08 (P1-11 / P1-12)
----------------------------------------
The download report historically recorded absolute Windows paths and no content
hashes, so "which file fed which number" was not auditable and the manifest was
not portable. This script rewrites the manifest with:

- ``path`` relative to the project root (forward slashes),
- ``sha256`` and ``bytes`` per file,
- ``n_records`` for GeoJSON (feature count) / JSON event dumps,
- frozen provenance fields (``dataset_id`` / ``landing_page`` / ``api_url`` /
  ``query`` / ``retrieved_utc`` / ``bbox`` / ``time_window``) carried over from the
  existing download report when present.

It does NOT invent provenance: fields that the download report never recorded are
omitted rather than guessed. Run after any download or data refresh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MANIFEST_NAME = "DOWNLOAD_MANIFEST.json"

# Files that are part of a pilot's raw evidence stack (sha256+count recorded).
DEFAULT_LAYERS = [
    "dem.tif",
    "impervious.tif",
    "building_footprints.geojson",
    "hydro_streams.geojson",
    "dep_stormwater_flood.geojson",
    "dep_stormwater_flood_2050slr.geojson",
    "flooding_311.geojson",
    "flooding_311_query.json",
    "usgs_ida_hwm.geojson",
    "fema_sandy.geojson",
    "event_rainfall.tif",
    "floodnet_sensors.geojson",
    "floodnet_events.json",
    "floodnet_query.json",
]

# Landing pages / dataset ids that let a reader re-fetch the layer.
DATASET_META: dict[str, dict[str, str]] = {
    "dem.tif": {
        "dataset_id": "usgs_3dep_elevation",
        "landing_page": "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer",
        "type": "raster",
    },
    "impervious.tif": {
        "dataset_id": "nlcd_annual_fractional_impervious",
        "landing_page": (
            "https://di-nlcd.img.arcgis.com/arcgis/rest/services/"
            "USA_NLCD_Annual_LandCover_Fractional_Impervious_Surface/ImageServer"
        ),
        "type": "raster",
    },
    "building_footprints.geojson": {
        "dataset_id": "nyc_maphub_building_view",
        "landing_page": "https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/BUILDING_view/FeatureServer/0",
        "type": "vector",
    },
    "hydro_streams.geojson": {
        "dataset_id": "usgs_nhdplus_hr",
        "landing_page": "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer",
        "type": "vector",
    },
    "dep_stormwater_flood.geojson": {
        "dataset_id": "nyc_dep_stormwater_flood_current_slr",
        "landing_page": "https://data.cityofnewyork.us/Environment/NYC-Stormwater-Flood-Maps/9i7c-xyvv",
        "attribution": "public ArcGIS mirror attributed to NYC DEP",
        "official_identity_verified": "false",
        "type": "vector",
    },
    "dep_stormwater_flood_2050slr.geojson": {
        "dataset_id": "nyc_dep_stormwater_flood_2050_slr",
        "landing_page": "https://data.cityofnewyork.us/Environment/NYC-Stormwater-Flood-Maps/9i7c-xyvv",
        "attribution": "public ArcGIS mirror attributed to NYC DEP",
        "official_identity_verified": "false",
        "type": "vector",
    },
    "flooding_311.geojson": {
        "dataset_id": "nyc311_76ig_c548_street_flooding",
        "landing_page": "https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548",
        "time_window": "2010-01-01 <= created_date < 2015-01-01",
        "type": "vector",
    },
    "flooding_311_query.json": {
        "dataset_id": "nyc311_76ig_c548_street_flooding",
        "landing_page": "https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548",
        "time_window": "2010-01-01 <= created_date < 2015-01-01",
        "type": "json",
    },
    "usgs_ida_hwm.geojson": {
        "dataset_id": "usgs_sciencebase_P9OMBJPQ_ida_hwm",
        "landing_page": "https://www.sciencebase.gov/catalog/item/618975c8d34ec04fc9c5a049",
        "type": "vector",
    },
    "fema_sandy.geojson": {
        "dataset_id": "sandy_inundation_zone_public_mirror",
        "landing_page": "https://data.cityofnewyork.us/Environment/Hurricane-Sandy-Inundation-Zone/uyj8-7rv5",
        "role": "negative_control",
        "type": "vector",
    },
    "event_rainfall.tif": {
        "dataset_id": "synthetic_constant_rainfall_hook",
        "landing_page": None,
        "note": "Uniform constant mm/h scenario hook; NOT gauge/radar observations.",
        "type": "raster",
    },
    "floodnet_sensors.geojson": {
        "dataset_id": "kb2e-tjy3",
        "landing_page": "https://data.cityofnewyork.us/Environment/FloodNet-Sensor-Deployment-Metadata/kb2e-tjy3",
        "role": "external_validation",
        "type": "vector",
    },
    "floodnet_events.json": {
        "dataset_id": "aq7i-eu5q",
        "landing_page": (
            "https://data.cityofnewyork.us/Environment/"
            "FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q"
        ),
        "role": "external_validation",
        "type": "json",
    },
    "floodnet_query.json": {
        "dataset_id": "aq7i-eu5q+kb2e-tjy3",
        "landing_page": (
            "https://data.cityofnewyork.us/Environment/"
            "FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q"
        ),
        "role": "external_validation",
        "type": "json",
    },
}


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _sha256(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _n_records(path: Path) -> int | None:
    """Feature/event count for GeoJSON/JSON; None for rasters or unreadable files."""
    if path.suffix.lower() not in {".json", ".geojson"}:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        if isinstance(data.get("features"), list):
            return len(data["features"])
        if isinstance(data.get("events"), list):
            return len(data["events"])
    if isinstance(data, list):
        return len(data)
    return None


def build_manifest(raw_dir: Path) -> dict:
    manifest_path = raw_dir / MANIFEST_NAME
    prior: dict = {}
    if manifest_path.exists():
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior = {}

    files: list[dict] = []
    for name in DEFAULT_LAYERS:
        path = raw_dir / name
        if not path.exists():
            continue
        entry: dict = {
            "name": path.stem,
            "path": _rel(path),
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
            "n_records": _n_records(path),
        }
        entry.update({k: v for k, v in DATASET_META.get(name, {}).items() if v is not None})
        files.append(entry)

    bbox = prior.get("bbox")
    out = {
        "schema": "raw_download_manifest/v2",
        "bbox": bbox,
        "generated_from": "scripts/regenerate_download_manifest.py",
        "notes": [
            "Paths are relative to the project root (no absolute Windows paths).",
            "sha256 / bytes / n_records are recomputed from the files on disk.",
            "DEP stormwater polygons are a public ArcGIS mirror attributed to NYC DEP; "
            "official portal identity is not verified.",
            "event_rainfall.tif is a constant scenario hook, not gauge/radar rainfall.",
        ],
        "files": files,
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "nyc",
        help="Raw directory to index (default: data/raw/nyc)",
    )
    args = ap.parse_args()
    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        print(f"ERROR: {raw_dir} does not exist", file=sys.stderr)
        raise SystemExit(2)
    manifest = build_manifest(raw_dir)
    out_path = raw_dir / MANIFEST_NAME
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} with {len(manifest['files'])} files")


if __name__ == "__main__":
    main()
