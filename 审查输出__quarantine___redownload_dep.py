"""Temporary helper: re-download DEP stormwater layers (M4 sea-level fix).

Downloads Layer 1 (Current Sea Levels) as the primary target and Layer 2
(2050 SLR) as a sensitivity file, for both the lower_manhattan and
manhattan_expanded bboxes. Overwrites the existing primary files.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.download_nyc import (  # noqa: E402
    _DEP_STORMWATER_2050SLR,
    _DEP_STORMWATER_CURRENT,
    _DEP_WHERE,
    _download_arcgis_geojson,
)

TARGETS = [
    ("lower_manhattan", [-74.02, 40.70, -73.97, 40.76], ROOT / "data" / "raw" / "nyc"),
    ("manhattan_expanded", [-74.03, 40.68, -73.94, 40.80], ROOT / "data" / "raw" / "nyc_expanded"),
]


def main() -> None:
    for name, bbox, out_dir in TARGETS:
        out_dir.mkdir(parents=True, exist_ok=True)
        primary = out_dir / "dep_stormwater_flood.geojson"
        slr = out_dir / "dep_stormwater_flood_2050slr.geojson"
        n = _download_arcgis_geojson(
            _DEP_STORMWATER_CURRENT, bbox, primary, page_size=2000, where=_DEP_WHERE
        )
        print(f"[{name}] current-sea-level (layer 1) -> {primary.name}: {n} features")
        n2 = _download_arcgis_geojson(
            _DEP_STORMWATER_2050SLR, bbox, slr, page_size=2000, where=_DEP_WHERE
        )
        print(f"[{name}] 2050-SLR (layer 2) -> {slr.name}: {n2} features")


if __name__ == "__main__":
    main()
