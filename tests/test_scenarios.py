"""Event-conditioned multi-scenario susceptibility interface (P0-11)."""

from pathlib import Path

import pytest

from pluvial_flood_risk.pipeline import run_inference_scenarios, run_training
from pluvial_flood_risk.synthetic import write_demo_data


def test_scenarios_require_train_df_or_explicit_optin(tmp_path: Path):
    """P0-11: rainfall is NOT a trained input → refuse silent scenario claims."""
    data = write_demo_data(output_dir=tmp_path, bbox=(10.70, 59.90, 10.78, 59.95), resolution=9)
    model_dir = tmp_path / "models"
    run_training(data, model_dir=model_dir, allow_synthetic=True)
    bbox = (10.70, 59.90, 10.74, 59.93)
    scen = [{"name": "a", "mm_h": 20.0}, {"name": "b", "mm_h": 80.0}]
    with pytest.raises(ValueError, match="rainfall"):
        run_inference_scenarios(
            bbox, 9, scen, model_dir=model_dir, output_dir=tmp_path / "out", fallback_synthetic=True
        )


def test_scenarios_guarded_interface_runs_with_optin(tmp_path: Path):
    data = write_demo_data(output_dir=tmp_path, bbox=(10.70, 59.90, 10.78, 59.95), resolution=9)
    model_dir = tmp_path / "models"
    run_training(data, model_dir=model_dir, allow_synthetic=True)
    bbox = (10.70, 59.90, 10.74, 59.93)
    scen = [{"name": "a", "mm_h": 20.0}, {"name": "b", "mm_h": 80.0}]
    out = run_inference_scenarios(
        bbox,
        9,
        scen,
        model_dir=model_dir,
        output_dir=tmp_path / "out",
        fallback_synthetic=True,
        allow_unsupported=True,
    )
    assert {"susceptibility_score", "scenario", "rainfall_mm_h"}.issubset(out.columns)
    assert set(out["scenario"]) == {"a", "b"}
    n = out["h3_index"].nunique()
    assert len(out) == n * 2
    # rainfall is documented as NOT a model input → identical scores across scenarios.
    assert (out["rainfall_is_model_input"] == False).all()  # noqa: E712
    assert (tmp_path / "out" / "susceptibility_scenarios.csv").exists()
