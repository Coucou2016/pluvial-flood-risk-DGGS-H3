"""Jaccard paper figure."""

from __future__ import annotations

from pathlib import Path

import pytest

from pluvial_flood_risk.figures import plot_jaccard_ladder
from pluvial_flood_risk.rollups import write_jaccard_diagnostics
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
