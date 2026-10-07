"""Jaccard paper figure."""

from __future__ import annotations

from pathlib import Path

import pytest

from pluvial_flood_risk.figures import plot_jaccard_ladder, plot_resolution_effects, plot_workflow_schematic
from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics, write_jaccard_diagnostics
from pluvial_flood_risk.synthetic import build_demo_dataset


def test_plot_jaccard_ladder(tmp_path: Path):
    pytest.importorskip("matplotlib")
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    csv_path = tmp_path / "jaccard_by_resolution.csv"
    table = write_jaccard_diagnostics(df, csv_path, value_col="flood_risk", resolutions=[8, 9, 10])
    png = tmp_path / "jaccard_by_resolution.png"
    # write_jaccard_diagnostics also attempts the PNG next to the CSV
    sidecar = csv_path.with_suffix(".png")
    if sidecar.exists():
        assert sidecar.stat().st_size > 0
    out = plot_jaccard_ladder(table, png)
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_resolution_effects_requires_canonical_table(tmp_path: Path):
    pytest.importorskip("matplotlib")
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    with pytest.raises(ValueError, match="ladder_table"):
        plot_resolution_effects(df, tmp_path / "effects.png")


def test_plot_resolution_effects_reads_canonical_jaccard(tmp_path: Path):
    pytest.importorskip("matplotlib")
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    ladder = resolution_ladder_topk_diagnostics(
        df, "flood_risk", resolutions=[8, 9, 10], hotspot_budget=0.10, n_hard_boot=4
    )
    csv_path = tmp_path / "jaccard_by_resolution.csv"
    ladder.to_csv(csv_path, index=False)
    out = plot_resolution_effects(df, tmp_path / "effects.png", ladder_table=csv_path)
    assert out.exists()
    # Figure must not invent a second Jaccard: heatmap values are the CSV values.
    from pluvial_flood_risk.rollups import canonical_ladder_heatmap

    heat = canonical_ladder_heatmap(ladder)
    assert heat.loc["mean", 9] == pytest.approx(
        float(ladder.loc[(ladder["aggregation"] == "mean") & (ladder["coarse_res"] == 9), "jaccard"].iloc[0])
    )


def test_plot_workflow_schematic(tmp_path: Path):
    pytest.importorskip("matplotlib")
    png = tmp_path / "workflow_schematic.png"
    out = plot_workflow_schematic(png)
    assert out.exists()
    assert out.stat().st_size > 0
