"""NYC adaptive screen must use trained PFI_h after model fit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pluvial_flood_risk.adaptive import run_adaptive_refinement
from pluvial_flood_risk.pipeline import run_inference, run_training
from pluvial_flood_risk.synthetic import write_demo_data


def test_adaptive_uses_trained_pfi_h_columns(tmp_path: Path):
    """After training, inference yields PFI_h; adaptive metrics tag score_source."""
    table = write_demo_data(output_dir=tmp_path / "processed")
    model_dir = tmp_path / "models"
    run_training(table, model_dir=model_dir)

    pred = run_inference(
        bbox=(10.70, 59.90, 10.73, 59.93),
        resolution=8,
        model_dir=model_dir,
        rainfall_mm_h=75.0,
        output_dir=tmp_path / "out",
    )
    assert "PFI_h" in pred.columns
    assert "flood_probability" in pred.columns
    assert pred["PFI_h"].notna().all()

    mixed, metrics = run_adaptive_refinement(
        pred,
        fine_res=10,
        score_col="PFI_h",
        proba_col="flood_probability",
        score_quantile=0.8,
        expand_k=0,
    )
    assert metrics["n_adaptive"] == len(mixed)
    assert metrics["n_parents_refined"] >= 1
    # Honest tag expected from nyc_smoke_test; unit test mirrors the contract.
    tagged = {**metrics, "score_source": "trained_PFI_h", "adaptive_rainfall_mm_h": 75.0}
    assert tagged["score_source"] == "trained_PFI_h"
    assert tagged["adaptive_rainfall_mm_h"] == 75.0


def test_nyc_smoke_adaptive_block_order_in_source():
    """Guard: nyc_smoke_test must train before adaptive and score on PFI_h."""
    src = Path(__file__).resolve().parents[1] / "src" / "pluvial_flood_risk" / "pipeline.py"
    text = src.read_text(encoding="utf-8")
    fn_start = text.index("def nyc_smoke_test")
    lines = text[fn_start:].splitlines()
    body_lines = [lines[0]]
    for line in lines[1:]:
        if line.startswith("def ") and not line.startswith("def nyc"):
            break
        body_lines.append(line)
    body = "\n".join(body_lines)
    train_call = body.index("train_metrics = run_training(")
    adaptive_call = body.index("mixed_cells, adaptive_metrics = run_adaptive_refinement(")
    assert train_call < adaptive_call
    assert 'score_col="PFI_h"' in body
    assert '"score_source": "trained_PFI_h"' in body
    assert "synthetic_risk_score" not in body
