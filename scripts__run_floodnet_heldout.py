"""Strict held-out FloodNet external-validation diagnostic (never a training label).

Downloads (if needed) NYC Open Data aq7i-eu5q + kb2e-tjy3, applies the enforced
analysis freeze on data timestamps, maps sensors to H3 R9, and scores existing OOF
susceptibility ranks against sensor cells that recorded >=1 flood event.

Major Revision 2026-10-08 (P0-2/P0-4)
-------------------------------------
- The freeze is enforced: post-freeze events/sensors are dropped and audited.
- Sensor exposure (``sensor_exposure_days`` / ``event_rate_per_year``) is computed
  and the diagnostic is repeated at min-exposure thresholds 30/90/180/365 days.
- The result is reported **even when AUC < 0.5** — the FloodNet external result is
  a documented NEGATIVE result, surfacing in the abstract/conclusion.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.floodnet import (  # noqa: E402
    ANALYSIS_FREEZE_UTC,
    DEFAULT_EXPOSURE_THRESHOLDS_DAYS,
    FLOODNET_EVENTS_DATASET,
    FLOODNET_EVENTS_LANDING,
    FLOODNET_PUBLISHED,
    FLOODNET_SENSORS_DATASET,
    FLOODNET_SENSORS_LANDING,
    compute_sensor_exposure,
    download_floodnet_heldout,
    filter_events_before_freeze,
    filter_sensors_before_freeze,
    freeze_time,
    load_floodnet_points,
)


def _bbox_from_cfg(profile: str) -> tuple[float, float, float, float]:
    from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    return tuple(resolve_bbox(cfg, profile))  # type: ignore[return-value]


def _ensure_floodnet(raw_dir: Path, bbox: tuple[float, float, float, float]) -> Path:
    geo = raw_dir / "floodnet_sensors.geojson"
    if geo.exists() and load_floodnet_points(geo):
        return geo
    download_floodnet_heldout(raw_dir, bbox=bbox)
    return geo


def _load_raw_events(raw_dir: Path) -> tuple[list[dict], dict]:
    """Load downloaded events and enforce the freeze on their timestamps."""
    events_path = raw_dir / "floodnet_events.json"
    if not events_path.exists():
        return [], {}
    try:
        payload = json.loads(events_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], {}
    events = payload.get("events") or []
    kept, audit = filter_events_before_freeze(events, freeze_time())
    return kept, audit


def _load_raw_sensors(raw_dir: Path) -> tuple[list[dict], dict]:
    """Reconstruct sensor dicts from the GeoJSON properties; filter by install date."""
    geo = raw_dir / "floodnet_sensors.geojson"
    if not geo.exists():
        return [], {}
    sensors = [dict(props) for _pt, props in load_floodnet_points(geo)]
    kept, audit = filter_sensors_before_freeze(sensors, freeze_time())
    return kept, audit


def _score_variant(
    cell_agg: pd.DataFrame,
    oof: pd.DataFrame,
    score_col: str,
    exposure_min_days: float | None = None,
) -> dict:
    """Compute ROC-AUC / AP for a (possibly exposure-filtered) sensor-cell outcome."""
    agg = cell_agg
    if exposure_min_days is not None and "sensor_exposure_days" in agg.columns:
        agg = agg.loc[agg["sensor_exposure_days"] >= exposure_min_days].copy()
    merged = agg.merge(oof[["h3_index", score_col]], on="h3_index", how="left")
    y = merged["any_event"].astype(int).to_numpy()
    s = merged[score_col].astype(float).to_numpy()
    mask = np.isfinite(s)
    y, s = y[mask], s[mask]
    out: dict = {
        "exposure_min_days": exposure_min_days,
        "n_cells": int(len(y)),
        "n_positive": int((y == 1).sum()),
        "positive_prevalence": float(y.mean()) if len(y) else None,
        "roc_auc": None,
        "average_precision": None,
        "mean_score_event_cells": float(s[y == 1].mean()) if (y == 1).any() else None,
        "mean_score_no_event_cells": float(s[y == 0].mean()) if (y == 0).any() else None,
    }
    if len(y) >= 5 and len(np.unique(y)) == 2:
        out["roc_auc"] = float(roc_auc_score(y, s))
        out["average_precision"] = float(average_precision_score(y, s))
    elif len(y) < 5:
        out["note"] = "too few sensor-overlapping study cells for ROC/AP"
    else:
        out["note"] = "single-class sensor-cell outcome; ROC/AP undefined"
    return out


def _pilot_diag(
    *,
    name: str,
    bbox: tuple[float, float, float, float],
    raw_dir: Path,
    oof_csv: Path,
    table_parquet: Path,
    resolution: int = 9,
) -> dict:
    geo = _ensure_floodnet(raw_dir, bbox)
    pts = load_floodnet_points(geo)
    oof = pd.read_csv(oof_csv)
    table = pd.read_parquet(table_parquet)
    h3_col_table = "h3_index" if "h3_index" in table.columns else "h3"
    h3_set = set(table[h3_col_table].astype(str))

    # Freeze audit + exposure from the enforced raw dumps.
    events, event_audit = _load_raw_events(raw_dir)
    sensors_raw, sensor_audit = _load_raw_sensors(raw_dir)
    exposure = compute_sensor_exposure(sensors_raw, events, freeze_time())

    sensor_rows = []
    for pt, props in pts:
        lon, lat = float(pt.x), float(pt.y)
        if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        sid = str(props.get("sensor_id"))
        exp = exposure.get(sid, {})
        exposure_days = props.get("sensor_exposure_days")
        if exposure_days is None:
            exposure_days = exp.get("sensor_exposure_days")
        event_rate = props.get("event_rate_per_year")
        if event_rate is None:
            event_rate = exp.get("event_rate_per_year")
        cell = h3.latlng_to_cell(lat, lon, resolution)
        sensor_rows.append(
            {
                "sensor_id": sid,
                "sensor_name": props.get("sensor_name"),
                "tidally_influenced": props.get("tidally_influenced"),
                "n_flood_events": int(props.get("n_flood_events") or 0),
                "max_depth_inches": props.get("max_depth_inches"),
                "sensor_exposure_days": exposure_days,
                "event_rate_per_year": event_rate,
                "h3_index": cell,
                "in_study_table": cell in h3_set,
            }
        )
    sens = pd.DataFrame(sensor_rows)
    if sens.empty:
        return {
            "pilot": name,
            "n_sensors_in_bbox": 0,
            "n_sensors_in_study_table": 0,
            "note": "no FloodNet sensors in bbox after download",
        }

    # Cell-level held-out outcome: any sensor in cell with >=1 pre-freeze QC event.
    cell_agg = (
        sens.groupby("h3_index", as_index=False)
        .agg(
            n_sensors=("sensor_id", "count"),
            n_events=("n_flood_events", "sum"),
            max_depth_inches=("max_depth_inches", "max"),
            sensor_exposure_days=("sensor_exposure_days", "min"),
            event_rate_per_year=("event_rate_per_year", "max"),
            any_event=("n_flood_events", lambda s: int((s.fillna(0) > 0).any())),
        )
    )
    cell_agg = cell_agg[cell_agg["h3_index"].isin(h3_set)].copy()

    score_col = None
    for c in ("y_proba", "y_prob", "oof_proba", "proba", "y_score", "oof_model_score"):
        if c in oof.columns:
            score_col = c
            break
    if score_col is None:
        for c in oof.columns:
            if c.lower() in {"h3", "h3_index", "y_true", "y_pred", "fold", "fold_id", "block", "h3_parent_block"}:
                continue
            if pd.api.types.is_numeric_dtype(oof[c]):
                score_col = c
                break
    if score_col is None:
        raise RuntimeError(f"No score column in {oof_csv}")

    oof = oof.copy()
    h3_col_oof = "h3_index" if "h3_index" in oof.columns else "h3"
    oof["h3_index"] = oof[h3_col_oof].astype(str)

    baseline = _score_variant(cell_agg, oof, score_col)
    sensitivity = {
        "all_sensors": baseline,
        **{
            f"min_exposure_{d}d": _score_variant(cell_agg, oof, score_col, float(d))
            for d in DEFAULT_EXPOSURE_THRESHOLDS_DAYS
        },
    }

    return {
        "pilot": name,
        "bbox": list(bbox),
        "resolution": resolution,
        "score_column": score_col,
        "n_sensors_in_bbox": int(len(sens)),
        "n_sensors_with_events": int((sens["n_flood_events"] > 0).sum()),
        "n_sensors_in_study_table": int(sens["in_study_table"].sum()),
        "n_study_cells_with_sensor": int(len(cell_agg)),
        "n_study_cells_with_event": int(cell_agg["any_event"].sum()),
        "n_tidally_influenced_sensors": int(
            sens["tidally_influenced"].astype(str).str.lower().str.startswith("y").sum()
        ),
        "positive_prevalence_sensor_cells": baseline["positive_prevalence"],
        "roc_auc": baseline["roc_auc"],
        "average_precision": baseline["average_precision"],
        "mean_score_event_cells": baseline["mean_score_event_cells"],
        "mean_score_no_event_cells": baseline["mean_score_no_event_cells"],
        "exposure_sensitivity": sensitivity,
        "freeze_audit": {**event_audit, **sensor_audit},
        "held_out": True,
        "used_in_training_labels": False,
    }


def main() -> None:
    out_path = ROOT / "outputs" / "floodnet_heldout_validation.json"
    pilots = []
    for name, profile, raw_rel, oof_rel, table_rel in (
        (
            "lower_manhattan",
            "lower_manhattan",
            "data/raw/nyc",
            "models/nyc_smoke/spatial_cv_oof_predictions.csv",
            "data/processed/nyc_h3_cells.parquet",
        ),
        (
            "manhattan_expanded",
            "manhattan_expanded",
            "data/raw/nyc_expanded",
            "models/nyc_expanded/spatial_cv_oof_predictions.csv",
            "data/processed/nyc_h3_cells_expanded.parquet",
        ),
    ):
        bbox = _bbox_from_cfg(profile)
        raw_dir = ROOT / raw_rel
        raw_dir.mkdir(parents=True, exist_ok=True)
        pilots.append(
            _pilot_diag(
                name=name,
                bbox=bbox,
                raw_dir=raw_dir,
                oof_csv=ROOT / oof_rel,
                table_parquet=ROOT / table_rel,
            )
        )

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_freeze_utc": ANALYSIS_FREEZE_UTC,
        "role": "external_validation",
        "used_in_training_or_evaluation_labels": False,
        "events_dataset_id": FLOODNET_EVENTS_DATASET,
        "events_landing_page": FLOODNET_EVENTS_LANDING,
        "sensors_dataset_id": FLOODNET_SENSORS_DATASET,
        "sensors_landing_page": FLOODNET_SENSORS_LANDING,
        "published": FLOODNET_PUBLISHED,
        "outcome_definition": (
            "Study R9 cell is positive if it contains >=1 FloodNet sensor with "
            ">=1 pre-freeze QC street-flooding event in aq7i-eu5q; scores are "
            "spatial-CV OOF susceptibility ranks from the open-evidence model "
            "(FloodNet excluded from training)."
        ),
        "interpretation": (
            "NEGATIVE external result: independent FloodNet event-level discrimination "
            "was NOT established (AUC can be < 0.5). Reported honestly."
        ),
        "pilots": pilots,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    for p in pilots:
        print(
            p["pilot"],
            "sensors",
            p.get("n_sensors_in_bbox"),
            "event_cells",
            p.get("n_study_cells_with_event"),
            "ROC",
            p.get("roc_auc"),
            "AP",
            p.get("average_precision"),
        )


if __name__ == "__main__":
    main()
