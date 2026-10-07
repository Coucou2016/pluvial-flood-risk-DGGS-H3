#!/usr/bin/env python
"""Fetch Lower Manhattan public layers into data/raw/nyc/ (EPSG:4326).

Falls back gracefully when Socrata is blocked; uses ArcGIS/USGS/CDN mirrors.
Does not download 7Analytics PFIb. See data/raw/DATA_SOURCES.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import NYC_MANHATTAN_BBOX, PROJECT_ROOT  # noqa: E402
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox  # noqa: E402
from pluvial_flood_risk.download_nyc import download_nyc_layers  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "nyc.yaml",
        help="Study YAML (bbox / raw_dir)",
    )
    parser.add_argument("--out", type=Path, default=None, help="Override output directory")
    parser.add_argument("--smoke-bbox", action="store_true", help="Use smoke profile instead of study bbox")
    parser.add_argument(
        "--bbox-profile",
        default=None,
        help="Named profile from bbox_profiles (overrides --smoke-bbox when set)",
    )
    parser.add_argument("--no-311", action="store_true")
    parser.add_argument("--no-sandy", action="store_true")
    parser.add_argument("--no-impervious", action="store_true")
    parser.add_argument("--no-event-rainfall", action="store_true")
    parser.add_argument(
        "--no-hydro",
        action="store_true",
        help="Skip NHDPlus HR / OSM hydro (dist_stream_m would stay synthetic)",
    )
    parser.add_argument(
        "--event-rainfall-mm-h",
        type=float,
        default=75.0,
        help="Constant mm/h for optional event_rainfall.tif (Ida-like hook)",
    )
    parser.add_argument(
        "--dem-size",
        default="500,600",
        help="3DEP/NLCD export width,height pixels (Lower Manhattan subset)",
    )
    args = parser.parse_args()

    cfg = load_study_config(args.config)
    if args.bbox_profile:
        profile_used = args.bbox_profile
        bbox = resolve_bbox(cfg, profile_used)
    elif args.smoke_bbox:
        profile_used = "smoke"
        bbox = resolve_bbox(cfg, "smoke")
    else:
        profile_used = str(cfg.get("default_build_profile") or "lower_manhattan")
        bbox = resolve_bbox(cfg, profile_used)
    if len(bbox) != 4:
        bbox = NYC_MANHATTAN_BBOX
    out = args.out or Path(cfg.get("paths", {}).get("raw_dir") or (PROJECT_ROOT / "data" / "raw" / "nyc"))
    w, h = [int(x.strip()) for x in args.dem_size.split(",")]

    def _progress(msg: str) -> None:
        print(msg, flush=True)

    report = download_nyc_layers(
        out_dir=out,
        bbox=bbox,
        dem_size=(w, h),
        include_311=not args.no_311,
        include_sandy=not args.no_sandy,
        include_impervious=not args.no_impervious,
        include_event_rainfall=not args.no_event_rainfall,
        event_rainfall_mm_h=args.event_rainfall_mm_h,
        include_hydro=not args.no_hydro,
        progress=_progress,
    )
    payload = report.to_dict()
    payload["bbox_profile"] = profile_used
    payload["bbox"] = list(bbox)
    print(json.dumps(payload, indent=2))
    if not report.assembly_ready:
        print(
            "WARNING: assembly not ready — dem.tif and/or dep_stormwater_flood.geojson missing. "
            "Fixture fallback: python scripts\\build_nyc_h3.py --fixtures",
            file=sys.stderr,
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()
