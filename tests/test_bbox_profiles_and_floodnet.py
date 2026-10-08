"""Tests for bbox profiles and FloodNet external-validation isolation (P0-3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pluvial_flood_risk.assemble import sources_from_config
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox
from pluvial_flood_risk.floodnet import floodnet_join_status, usable_floodnet_path


ROOT = Path(__file__).resolve().parents[1]


def test_nyc_bbox_profiles_resolve():
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    assert "smoke" in cfg["bbox_profiles"]
    assert "manhattan_expanded" in cfg["bbox_profiles"]
    smoke = resolve_bbox(cfg, "smoke")
    study = resolve_bbox(cfg, "lower_manhattan")
    expanded = resolve_bbox(cfg, "manhattan_expanded")
    assert smoke == cfg["smoke_bbox"]
    assert study == cfg["bbox"]
    assert expanded[2] - expanded[0] > study[2] - study[0]
    assert cfg["default_smoke_profile"] == "lower_manhattan"
    assert cfg["default_build_profile"] == "lower_manhattan"
    assert resolve_bbox(cfg, default=cfg["default_smoke_profile"]) == study
    assert resolve_bbox(cfg, "smoke") == smoke


def test_floodnet_absent_is_noop(tmp_path: Path):
    missing = tmp_path / "floodnet_sensors.geojson"
    assert usable_floodnet_path(missing) is None
    # FloodNet is external validation only — the status is never a training join.
    assert floodnet_join_status(missing, include=True) == "external_validation_only"
    assert floodnet_join_status(missing, include=False) == "external_validation_only"


def test_floodnet_never_enters_training_points(tmp_path: Path):
    """P0-3: even a non-empty FloodNet file must NOT be appended to training points."""
    geo = tmp_path / "floodnet_sensors.geojson"
    geo.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-74.01, 40.71]},
                        "properties": {"sensor_id": "demo"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg["paths"])
    cfg["paths"]["raw_dir"] = tmp_path
    cfg["paths"]["flood_points"] = []
    cfg["paths"]["floodnet"] = geo
    src = sources_from_config(cfg)
    assert geo not in src.flood_points_paths


def test_include_floodnet_config_key_removed():
    """The legacy labels.include_floodnet switch must raise (P0-3)."""
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg["paths"])
    cfg["labels"] = {"include_floodnet": True}
    with pytest.raises(ValueError, match="include_floodnet"):
        sources_from_config(cfg)


def test_floodnet_official_dataset_ids():
    from pluvial_flood_risk.floodnet import (
        FLOODNET_EVENTS_DATASET,
        FLOODNET_SENSORS_DATASET,
        FLOODNET_PUBLISHED,
    )
    from pluvial_flood_risk import download_nyc as dn

    assert FLOODNET_EVENTS_DATASET == "aq7i-eu5q"
    assert FLOODNET_SENSORS_DATASET == "kb2e-tjy3"
    assert FLOODNET_PUBLISHED == "2026-03-03"
    assert dn._FLOODNET_EVENTS_DATASET == "aq7i-eu5q"
    assert dn._FLOODNET_SENSORS_DATASET == "kb2e-tjy3"


def test_config_uses_role_typed_blocks():
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    assert "external_validation" in cfg
    assert cfg["external_validation"]["floodnet"]["role"] == "external_validation"
    assert cfg["negative_control"]["sandy"]["role"] == "negative_control"
    assert "include_floodnet" not in (cfg.get("labels") or {})


def test_floodnet_freeze_filters_events_and_sensors():
    from datetime import datetime, timezone

    from pluvial_flood_risk.floodnet import (
        filter_events_before_freeze,
        filter_sensors_before_freeze,
    )

    freeze = datetime(2026, 8, 30, tzinfo=timezone.utc)
    events = [
        {"flood_start_time": "2026-01-01T00:00:00Z"},
        {"flood_start_time": "2026-09-15T00:00:00Z"},  # after freeze → dropped
    ]
    kept, audit = filter_events_before_freeze(events, freeze)
    assert len(kept) == 1
    assert audit["n_events_after_freeze_dropped"] == 1
    assert audit["events_max_timestamp_after_filter"].startswith("2026-01-01")

    sensors = [{"date_installed": "2026-05-01T00:00:00Z"}, {"date_installed": "2026-12-01T00:00:00Z"}]
    s_kept, s_audit = filter_sensors_before_freeze(sensors, freeze)
    assert len(s_kept) == 1
    assert s_audit["n_sensors_after_freeze_dropped"] == 1


def test_floodnet_heldout_artifact_if_present():
    path = ROOT / "outputs" / "floodnet_heldout_validation.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("used_in_training_or_evaluation_labels") is False
    assert payload.get("events_dataset_id") == "aq7i-eu5q"
    assert payload.get("sensors_dataset_id") == "kb2e-tjy3"
    assert len(payload.get("pilots") or []) >= 1


def test_311_official_query_freeze():
    from pluvial_flood_risk.download_nyc import (
        _311_CANDIDATES,
        _311_DESCRIPTOR,
        _311_OFFICIAL_DATASET,
        _311_where_clause,
    )

    assert _311_OFFICIAL_DATASET == "76ig-c548"
    assert _311_CANDIDATES[0][0] == "soda_76ig_c548_official"
    where = _311_where_clause((-74.02, 40.70, -73.97, 40.76), include_date=True)
    assert _311_DESCRIPTOR in where
    assert "2010-01-01" in where
    assert "2015-01-01" in where
    assert "Sewer" not in where
    assert "$limit" not in where
