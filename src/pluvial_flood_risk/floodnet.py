"""FloodNet optional sensor points — join only when a usable GeoJSON exists."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import Point

FLOODNET_README = """# FloodNet stub

Place FloodNet sensor GeoJSON here as `floodnet_sensors.geojson` (EPSG:4326).

API / portal: https://www.floodnet.nyc/

This pipeline does **not** auto-ingest live FloodNet streams yet. When present
and non-empty, points join like other flood_points (optional label enrichment).
Do not treat sensor depth as insurance PFIb labels.
"""


def write_floodnet_stub(out_dir: Path | str) -> Path:
    """Write a README placeholder under raw/nyc (no empty GeoJSON)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    readme = out_dir / "FLOODNET_STUB.txt"
    readme.write_text(FLOODNET_README, encoding="utf-8")
    return readme


def load_floodnet_points(path: Path | str) -> list[tuple[Any, dict]]:
    """Load FloodNet GeoJSON Point features if present; else return []."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    feats = data.get("features") or []
    out = []
    for feat in feats:
        geom = feat.get("geometry")
        if not geom:
            continue
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        if gtype == "Point":
            lon, lat = float(coords[0]), float(coords[1])
        elif gtype == "MultiPoint" and coords:
            lon, lat = float(coords[0][0]), float(coords[0][1])
        else:
            continue
        props = dict(feat.get("properties") or {})
        props.setdefault("source", "floodnet")
        out.append((Point(lon, lat), props))
    return out


def usable_floodnet_path(path: Path | str | None) -> Path | None:
    """Return path only if the file exists and contains ≥1 Point feature."""
    if path is None or path == "":
        return None
    p = Path(path)
    if not p.exists():
        return None
    return p if load_floodnet_points(p) else None


def floodnet_join_status(path: Path | str | None, *, include: bool) -> str:
    """Human-readable join status for manifests / run metadata."""
    if not include:
        return "disabled_by_config"
    if path is None or path == "":
        return "no_path_configured"
    p = Path(path)
    if not p.exists():
        return "absent"
    if usable_floodnet_path(p) is None:
        return "empty_or_unreadable"
    return "joined"
