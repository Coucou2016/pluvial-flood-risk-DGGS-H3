from pathlib import Path

from pluvial_flood_risk.config_loader import load_study_config


def test_load_demo_oslo_config():
    path = Path(__file__).resolve().parents[1] / "configs" / "demo_oslo.yaml"
    cfg = load_study_config(path)
    assert cfg["name"] == "demo_oslo"
    assert cfg["data_provenance"] == "synthetic"
    assert len(cfg["bbox"]) == 4
    assert cfg["spatial_cv"]["k_ring"] == 2


def test_load_nyc_config():
    path = Path(__file__).resolve().parents[1] / "configs" / "nyc.yaml"
    cfg = load_study_config(path)
    assert cfg["name"] == "nyc_manhattan"
    assert cfg["study_role"] == "main"
    assert len(cfg["bbox"]) == 4
    assert cfg["bbox"][0] < -73.0
    assert "ida_like" in {s["name"] for s in cfg["rainfall_scenarios"]}
    assert cfg["paths"]["dem"].name == "dem.tif"
    assert cfg["adaptive"]["fine_res"] >= cfg["resolution"]
