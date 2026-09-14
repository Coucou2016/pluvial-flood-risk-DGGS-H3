"""Tests for bbox profiles and optional FloodNet join."""

from __future__ import annotations

import json
from pathlib import Path

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
    # Option B: paper smoke path uses lower_manhattan (~262 R9)
    assert cfg["default_smoke_profile"] == "lower_manhattan"
    assert cfg["default_build_profile"] == "lower_manhattan"
    assert resolve_bbox(cfg, default=cfg["default_smoke_profile"]) == study
    assert resolve_bbox(cfg, "smoke") == smoke


def test_floodnet_absent_is_noop(tmp_path: Path):
    missing = tmp_path / "floodnet_sensors.geojson"
    assert usable_floodnet_path(missing) is None
    assert floodnet_join_status(missing, include=True) == "absent"
    assert floodnet_join_status(missing, include=False) == "disabled_by_config"

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg["paths"])
    cfg["paths"]["floodnet"] = missing
    # Isolate from live data/raw/nyc/floodnet_sensors.geojson fallback.
    cfg["paths"]["raw_dir"] = tmp_path
    cfg["labels"] = {"include_floodnet": True}
    src = sources_from_config(cfg)
    assert all(Path(p).name != "floodnet_sensors.geojson" or not Path(p).exists() for p in src.flood_points_paths)
    assert missing not in src.flood_points_paths


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


def test_floodnet_disabled_by_default_config():
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    assert cfg.get("labels", {}).get("include_floodnet") is False


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


def test_floodnet_nonempty_appended_to_points(tmp_path: Path):
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
    assert usable_floodnet_path(geo) == geo
    assert floodnet_join_status(geo, include=True) == "joined"

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg["paths"])
    cfg["paths"]["flood_points"] = []
    cfg["paths"]["floodnet"] = geo
    cfg["labels"] = {"include_floodnet": True}
    src = sources_from_config(cfg)
    assert geo in src.flood_points_paths

    cfg["labels"] = {"include_floodnet": False}
    src_off = sources_from_config(cfg)
    assert geo not in src_off.flood_points_paths
    assert floodnet_join_status(geo, include=False) == "disabled_by_config"
