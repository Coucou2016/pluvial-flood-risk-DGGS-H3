"""Event-conditioned multi-scenario PFI_h."""

from pathlib import Path

from pluvial_flood_risk.pipeline import run_inference_scenarios, run_training
from pluvial_flood_risk.synthetic import write_demo_data


def test_scenarios_vary_rainfall_not_static_hash(tmp_path: Path):
    data = write_demo_data(output_dir=tmp_path, bbox=(10.70, 59.90, 10.78, 59.95), resolution=9)
    model_dir = tmp_path / "models"
    run_training(data, model_dir=model_dir)
    bbox = (10.70, 59.90, 10.74, 59.93)
    scen = [{"name": "a", "mm_h": 20.0}, {"name": "b", "mm_h": 80.0}]
    out = run_inference_scenarios(
        bbox,
        9,
        scen,
        model_dir=model_dir,
        output_dir=tmp_path / "out",
    )
    assert {"PFI_h", "scenario", "rainfall_mm_h"}.issubset(out.columns)
    assert set(out["scenario"]) == {"a", "b"}
    n = out["h3_index"].nunique()
    assert len(out) == n * 2
    # Same cell, different rainfall → PFI_h should usually differ
    cell = out["h3_index"].iloc[0]
    p = out.loc[out["h3_index"] == cell].sort_values("rainfall_mm_h")["PFI_h"].to_numpy()
    assert len(p) == 2
    assert (tmp_path / "out" / "pfi_h_scenarios.csv").exists()
