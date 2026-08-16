#!/usr/bin/env python
"""Assemble NYC/Manhattan H3 cells from local Open Data or public-schema fixtures.

Uses the same join/zonal/label code as production. Does not download 7Analytics PFIb
and does not claim to reproduce Svellingen et al. insurance labels.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.assemble import assemble_h3_table, sources_from_config  # noqa: E402
from pluvial_flood_risk.config import PROCESSED_DIR, PROJECT_ROOT  # noqa: E402
from pluvial_flood_risk.config_loader import load_study_config  # noqa: E402
from pluvial_flood_risk.schema_fixtures import FIXTURE_MARKER, write_public_schema_fixtures  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "nyc.yaml")
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR / "nyc_h3_cells.parquet")
    parser.add_argument("--fixtures", action="store_true", help="Force public-schema fixtures even if data/raw/nyc/dem.tif exists")
    parser.add_argument("--no-fixtures", action="store_true", help="Fail if live rasters/vectors are missing")
    parser.add_argument(
        "--bbox-profile",
        default=None,
        help="Extent profile from configs/nyc.yaml bbox_profiles (default: default_build_profile)",
    )
    args = parser.parse_args()

    cfg = load_study_config(args.config)
    from pluvial_flood_risk.config_loader import resolve_bbox

    profile = args.bbox_profile or str(cfg.get("default_build_profile") or "lower_manhattan")
    bbox = resolve_bbox(cfg, profile)
    resolution = int(cfg.get("resolution", 9))
    rainfall = float(cfg.get("rainfall_mm_h", 40.0))
    raw_dir = Path(cfg.get("paths", {}).get("raw_dir") or (PROJECT_ROOT / "data" / "raw" / "nyc"))
    raw_dir.mkdir(parents=True, exist_ok=True)

    live = (
        (raw_dir / "dem.tif").exists()
        and (raw_dir / "dep_stormwater_flood.geojson").exists()
        and not (raw_dir / FIXTURE_MARKER).exists()
    )
    used_fixtures = False
    if args.fixtures or (not live and not args.no_fixtures):
        write_public_schema_fixtures(raw_dir, bbox)
        used_fixtures = True
        cfg["assembly_mode"] = "fixture"
        print(
            "Using public-schema fixtures (not live NYC Open Data). "
            "Fetch live subset: python scripts\\download_nyc_data.py"
        )
    elif live:
        cfg["assembly_mode"] = "opendata"
        print("Using live layers under data/raw/nyc/ (see DOWNLOAD_MANIFEST.json).")
    elif not live and args.no_fixtures:
        raise SystemExit(
            f"No live NYC layers under {raw_dir}. "
            "Run: python scripts\\download_nyc_data.py  (or omit --no-fixtures)."
        )

    sources = sources_from_config(cfg)
    if used_fixtures:
        sources.assembly_mode = "fixture"
    df = assemble_h3_table(bbox, resolution, rainfall_mm_h=rainfall, sources=sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output, index=False)
    summary = {
        "n_cells": int(len(df)),
        "path": str(args.output),
        "assembly_mode": str(df["assembly_mode"].iloc[0]) if len(df) else None,
        "label_source": str(df["label_source"].iloc[0]) if len(df) else None,
        "feature_source": str(df["feature_source"].iloc[0]) if len(df) else None,
        "used_schema_fixtures": used_fixtures,
        "bbox_profile": profile,
        "bbox": list(bbox),
        "flood_class_positive_frac": float(df["flood_class"].mean()) if "flood_class" in df.columns else None,
        "note": (
            "fixture QA table — not a scientific NYC accuracy result"
            if used_fixtures
            else "assembled from local files; still not 7Analytics PFIb"
        ),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
