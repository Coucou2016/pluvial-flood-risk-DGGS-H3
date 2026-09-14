"""FloodNet NYC Open Data helpers — held-out only; never a default training label.

Official datasets (public as of 2026-03-03):
- Events: aq7i-eu5q (Street Flooding Events Measured by FloodNet Sensors)
- Sensors: kb2e-tjy3 (Sensor Deployment Metadata; lat/lon + tidally_influenced)

Training/evaluation assembly keeps ``labels.include_floodnet: false`` by default.
Downloaded files support a separate held-out diagnostic only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from shapely.geometry import Point

FLOODNET_EVENTS_DATASET = "aq7i-eu5q"
FLOODNET_SENSORS_DATASET = "kb2e-tjy3"
FLOODNET_EVENTS_LANDING = (
    "https://data.cityofnewyork.us/Environment/"
    "FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q"
)
FLOODNET_SENSORS_LANDING = (
    "https://data.cityofnewyork.us/Environment/"
    "FloodNet-Sensor-Deployment-Metadata/kb2e-tjy3"
)
FLOODNET_PUBLISHED = "2026-03-03"
ANALYSIS_FREEZE_UTC = "2026-08-30T00:00:00+00:00"

FLOODNET_README = f"""# FloodNet — reserved held-out external validation

Official NYC Open Data (published {FLOODNET_PUBLISHED}):

- Events: {FLOODNET_EVENTS_LANDING} (`{FLOODNET_EVENTS_DATASET}`)
- Sensor locations: {FLOODNET_SENSORS_LANDING} (`{FLOODNET_SENSORS_DATASET}`)

These layers are **public**. This analysis freeze does **not** use FloodNet as a
training or evaluation label (`labels.include_floodnet: false`). Downloaded
sensor/event files support a **strict held-out diagnostic** only
(`scripts/run_floodnet_heldout.py` → `outputs/floodnet_heldout_validation.json`).

Do not treat sensor depth as insurance PFIb labels. Do not claim the portal
lacks FloodNet data — the dataset IDs above are the authoritative sources.
"""

USER_AGENT = "pluvial-flood-risk-dggs-h3/0.1 (+FloodNet held-out download)"


def write_floodnet_stub(out_dir: Path | str) -> Path:
    """Write a README under raw/nyc documenting the official dataset IDs."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    readme = out_dir / "FLOODNET_STUB.txt"
    readme.write_text(FLOODNET_README, encoding="utf-8")
    return readme


def _soda_fetch_all(dataset_id: str, *, page_size: int = 1000, timeout: float = 120) -> list[dict]:
    """Paginate a Socrata resource until an empty page."""
    rows: list[dict] = []
    offset = 0
    while True:
        qs = urlencode({"$limit": str(page_size), "$offset": str(offset)})
        url = f"https://data.cityofnewyork.us/resource/{dataset_id}.json?{qs}"
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            batch = json.loads(resp.read().decode("utf-8"))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def download_floodnet_heldout(
    out_dir: Path | str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    """Download FloodNet sensors + events; write GeoJSON and query sidecars.

    Never joins into training labels. Returns a manifest dict for DOWNLOAD_MANIFEST.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()

    sensors = _soda_fetch_all(FLOODNET_SENSORS_DATASET)
    events = _soda_fetch_all(FLOODNET_EVENTS_DATASET)

    sensor_by_id = {str(s.get("sensor_id")): s for s in sensors if s.get("sensor_id")}
    event_counts: dict[str, int] = {}
    max_depth: dict[str, float] = {}
    for ev in events:
        sid = str(ev.get("sensor_id") or "")
        if not sid:
            continue
        event_counts[sid] = event_counts.get(sid, 0) + 1
        try:
            d = float(ev.get("max_depth_inches"))
        except (TypeError, ValueError):
            continue
        max_depth[sid] = max(max_depth.get(sid, 0.0), d)

    records: list[tuple[Point, dict]] = []
    for sid, s in sensor_by_id.items():
        try:
            lon = float(s["longitude"])
            lat = float(s["latitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if bbox is not None:
            minx, miny, maxx, maxy = bbox
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                continue
        props = {
            "source": "floodnet",
            "held_out_only": True,
            "sensor_id": sid,
            "sensor_name": s.get("sensor_name"),
            "tidally_influenced": s.get("tidally_influenced"),
            "borough": s.get("borough"),
            "date_installed": s.get("date_installed"),
            "n_flood_events": int(event_counts.get(sid, 0)),
            "max_depth_inches": max_depth.get(sid),
            "dataset_events": FLOODNET_EVENTS_DATASET,
            "dataset_sensors": FLOODNET_SENSORS_DATASET,
        }
        records.append((Point(lon, lat), props))

    from pluvial_flood_risk.vector_io import write_geojson_features

    geo_path = out_dir / "floodnet_sensors.geojson"
    write_geojson_features(geo_path, records)

    events_path = out_dir / "floodnet_events.json"
    events_path.write_text(
        json.dumps(
            {
                "dataset_id": FLOODNET_EVENTS_DATASET,
                "landing_page": FLOODNET_EVENTS_LANDING,
                "retrieved_utc": retrieved,
                "n_events_citywide": len(events),
                "n_sensors_citywide": len(sensors),
                "n_sensors_written": len(records),
                "bbox": list(bbox) if bbox else None,
                "events": events,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    query_path = out_dir / "floodnet_query.json"
    meta = {
        "role": "held_out_external_validation_only",
        "include_in_training_labels": False,
        "analysis_freeze_utc": ANALYSIS_FREEZE_UTC,
        "published": FLOODNET_PUBLISHED,
        "events_dataset_id": FLOODNET_EVENTS_DATASET,
        "events_landing_page": FLOODNET_EVENTS_LANDING,
        "sensors_dataset_id": FLOODNET_SENSORS_DATASET,
        "sensors_landing_page": FLOODNET_SENSORS_LANDING,
        "retrieved_utc": retrieved,
        "n_events_citywide": len(events),
        "n_sensors_citywide": len(sensors),
        "n_sensors_in_bbox": len(records),
        "bbox": list(bbox) if bbox else None,
        "geojson": str(geo_path.as_posix()),
        "events_json": str(events_path.as_posix()),
        "official_identity_verified": True,
        "mirror_status": "official",
    }
    query_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_floodnet_stub(out_dir)
    return meta


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
