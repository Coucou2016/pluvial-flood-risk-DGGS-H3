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
    assert cfg["default_smoke_profile"] == "smoke"
    assert resolve_bbox(cfg, default=cfg["default_smoke_profile"]) == smoke


def test_floodnet_absent_is_noop(tmp_path: Path):
    missing = tmp_path / "floodnet_sensors.geojson"
    assert usable_floodnet_path(missing) is None
    assert floodnet_join_status(missing, include=True) == "absent"
    assert floodnet_join_status(missing, include=False) == "disabled_by_config"

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg["paths"])
    cfg["paths"]["floodnet"] = missing
    cfg["labels"] = {"include_floodnet": True}
    src = sources_from_config(cfg)
    assert all(Path(p).name != "floodnet_sensors.geojson" or not Path(p).exists() for p in src.flood_points_paths)


def test_floodnet_disabled_by_default_config():
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    assert cfg.get("labels", {}).get("include_floodnet") is False


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
