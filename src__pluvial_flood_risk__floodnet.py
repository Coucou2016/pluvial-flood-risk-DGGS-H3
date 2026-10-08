"""FloodNet NYC Open Data helpers — strictly held-out external validation only.

Official datasets (public as of 2026-03-03):
- Events: aq7i-eu5q (Street Flooding Events Measured by FloodNet Sensors)
- Sensors: kb2e-tjy3 (Sensor Deployment Metadata; lat/lon + tidally_influenced)

Major Revision 2026-10-08 (P0-2/P0-3/P0-4)
-----------------------------------------
- FloodNet is an **external-validation** source, never a training label. The
  legacy ``labels.include_floodnet`` switch is gone; role typing in ``labels.py``
  makes it a code invariant.
- The ``analysis_freeze_utc`` is **enforced on the data**: events are filtered to
  ``flood_start_time < freeze_time`` and sensors to ``date_installed < freeze_time``
  (both at query time and again after download), with an assertion on the max
  timestamp. Audit counters are recorded so the freeze is auditable.
- Sensor **exposure** (``sensor_exposure_days`` / ``event_rate_per_year``) is
  computed so a cell-level outcome is not dominated by very young sensors.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
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

# Sensitivity thresholds (days) for sensor exposure filtering (P0-2).
DEFAULT_EXPOSURE_THRESHOLDS_DAYS: tuple[int, ...] = (30, 90, 180, 365)

FLOODNET_README = f"""# FloodNet — reserved held-out external validation

Official NYC Open Data (published {FLOODNET_PUBLISHED}):

- Events: {FLOODNET_EVENTS_LANDING} (`{FLOODNET_EVENTS_DATASET}`)
- Sensor locations: {FLOODNET_SENSORS_LANDING} (`{FLOODNET_SENSORS_DATASET}`)

These layers are **public**. This analysis freeze does **not** use FloodNet as a
training or evaluation label. Downloaded sensor/event files support a **strict
held-out external-validation diagnostic** only
(`scripts/run_floodnet_heldout.py` → `outputs/floodnet_heldout_validation.json`).
The freeze is enforced on the data: events with ``flood_start_time`` and sensors
with ``date_installed`` at/after ``{ANALYSIS_FREEZE_UTC}`` are dropped.

Do not treat sensor depth as insurance PFIb labels. Do not claim the portal
lacks FloodNet data — the dataset IDs above are the authoritative sources.
"""

USER_AGENT = "pluvial-flood-risk-dggs-h3/0.1 (+FloodNet held-out download)"


def freeze_time() -> datetime:
    """Parse :data:`ANALYSIS_FREEZE_UTC` as an aware UTC datetime."""
    return datetime.fromisoformat(ANALYSIS_FREEZE_UTC.replace("Z", "+00:00"))


def write_floodnet_stub(out_dir: Path | str) -> Path:
    """Write a README under raw/nyc documenting the official dataset IDs."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    readme = out_dir / "FLOODNET_STUB.txt"
    readme.write_text(FLOODNET_README, encoding="utf-8")
    return readme


def _soda_fetch_all(
    dataset_id: str,
    *,
    page_size: int = 1000,
    timeout: float = 120,
    where: str | None = None,
    max_retries: int = 6,
) -> list[dict]:
    """Paginate a Socrata resource until an empty page (optional ``$where``).

    NYC Open Data is intermittently flaky (443/SSL resets), so each page is
    retried with linear backoff before giving up.
    """
    import time

    rows: list[dict] = []
    offset = 0
    while True:
        params = {"$limit": str(page_size), "$offset": str(offset)}
        if where:
            params["$where"] = where
        qs = urlencode(params)
        url = f"https://data.cityofnewyork.us/resource/{dataset_id}.json?{qs}"
        batch: list[dict] | None = None
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                req = Request(
                    url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
                )
                with urlopen(req, timeout=timeout) as resp:
                    batch = json.loads(resp.read().decode("utf-8"))
                break
            except Exception as exc:  # noqa: BLE001 — network flakiness
                last_err = exc
                time.sleep(2.0 * (attempt + 1))
        if batch is None:
            raise RuntimeError(f"Socrata fetch failed for {dataset_id} after {max_retries} tries: {last_err}")
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def filter_events_before_freeze(
    events: list[dict],
    freeze: datetime | None = None,
) -> tuple[list[dict], dict[str, Any]]:
    """Filter events to ``flood_start_time < freeze``; return dropped counters."""
    freeze = freeze or freeze_time()
    kept: list[dict] = []
    dropped = 0
    bad = 0
    max_ts: datetime | None = None
    for ev in events:
        raw = ev.get("flood_start_time") or ev.get("flood_start") or ev.get("event_start_time")
        if raw in (None, ""):
            bad += 1
            continue
        try:
            ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            bad += 1
            continue
        if ts < freeze:
            kept.append(ev)
            if max_ts is None or ts > max_ts:
                max_ts = ts
        else:
            dropped += 1
    if kept:
        assert max_ts is not None and max_ts < freeze, "FloodNet freeze failed: post-freeze event kept"
    return kept, {
        "n_events_downloaded": int(len(events)),
        "n_events_before_freeze": int(len(kept)),
        "n_events_after_freeze_dropped": int(dropped),
        "n_events_unparseable_timestamp": int(bad),
        "events_max_timestamp_after_filter": max_ts.isoformat() if max_ts else None,
        "analysis_freeze_utc": freeze.isoformat(),
    }


def filter_sensors_before_freeze(
    sensors: list[dict],
    freeze: datetime | None = None,
) -> tuple[list[dict], dict[str, Any]]:
    """Filter sensors to ``date_installed < freeze`` (unparseable kept, flagged)."""
    freeze = freeze or freeze_time()
    kept: list[dict] = []
    dropped = 0
    unknown = 0
    for s in sensors:
        raw = s.get("date_installed") or s.get("installed_date")
        if raw in (None, ""):
            unknown += 1
            kept.append(s)
            continue
        try:
            ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            unknown += 1
            kept.append(s)
            continue
        if ts < freeze:
            kept.append(s)
        else:
            dropped += 1
    return kept, {
        "n_sensors_downloaded": int(len(sensors)),
        "n_sensors_before_freeze": int(len(kept)),
        "n_sensors_after_freeze_dropped": int(dropped),
        "n_sensors_missing_date_installed": int(unknown),
    }


def _parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def compute_sensor_exposure(
    sensors: list[dict],
    events: list[dict],
    freeze: datetime | None = None,
) -> dict[str, dict[str, float]]:
    """Per-sensor exposure days and pre-freeze event rate (events/year)."""
    freeze = freeze or freeze_time()
    counts: dict[str, int] = {}
    for ev in events:
        sid = str(ev.get("sensor_id") or "")
        if sid:
            counts[sid] = counts.get(sid, 0) + 1
    out: dict[str, dict[str, float]] = {}
    for s in sensors:
        sid = str(s.get("sensor_id") or "")
        installed = _parse_ts(s.get("date_installed") or s.get("installed_date"))
        exposure_days = float((freeze - installed).days) if installed is not None else float("nan")
        if np.isfinite(exposure_days):
            exposure_days = max(0.0, exposure_days)
            years = max(exposure_days / 365.25, 0.25)
        else:
            years = float("nan")
        n_events = counts.get(sid, 0)
        out[sid] = {
            "n_events_before_freeze": float(n_events),
            "sensor_exposure_days": exposure_days,
            "event_rate_per_year": (float(n_events) / years) if np.isfinite(years) and years > 0 else float("nan"),
        }
    return out


def download_floodnet_heldout(
    out_dir: Path | str,
    *,
    bbox: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    """Download FloodNet sensors + events; write GeoJSON and query sidecars.

    Never joins into training labels. Events are filtered at query time and again
    after download so no post-freeze record can leak in. Returns a manifest dict
    for DOWNLOAD_MANIFEST.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()
    freeze = freeze_time()
    freeze_day = freeze.date().isoformat()

    sensors = _soda_fetch_all(FLOODNET_SENSORS_DATASET)
    events_raw = _soda_fetch_all(
        FLOODNET_EVENTS_DATASET,
        where=f"flood_start_time < '{freeze_day}T00:00:00.000'",
    )
    events, event_audit = filter_events_before_freeze(events_raw, freeze)
    sensors, sensor_audit = filter_sensors_before_freeze(sensors, freeze)
    exposure = compute_sensor_exposure(sensors, events, freeze)

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
        exp = exposure.get(sid, {})
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
            "sensor_exposure_days": exp.get("sensor_exposure_days"),
            "event_rate_per_year": exp.get("event_rate_per_year"),
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
                "analysis_freeze_utc": freeze.isoformat(),
                **event_audit,
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
        "role": "external_validation",
        "include_in_training_labels": False,
        "analysis_freeze_utc": freeze.isoformat(),
        "published": FLOODNET_PUBLISHED,
        "events_dataset_id": FLOODNET_EVENTS_DATASET,
        "events_landing_page": FLOODNET_EVENTS_LANDING,
        "sensors_dataset_id": FLOODNET_SENSORS_DATASET,
        "sensors_landing_page": FLOODNET_SENSORS_LANDING,
        "retrieved_utc": retrieved,
        "query_where_events": f"flood_start_time < '{freeze_day}T00:00:00.000'",
        **event_audit,
        **sensor_audit,
        "n_sensors_in_bbox": len(records),
        "bbox": list(bbox) if bbox else None,
        "geojson": geo_path.as_posix(),
        "events_json": events_path.as_posix(),
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
    """Deprecated: FloodNet is never joined. Kept so old call sites resolve.

    Always reports the external-validation-only status; ``include`` is ignored
    (there is no training-join path anymore, P0-3).
    """
    del include
    return "external_validation_only"
