"""Multi-resolution rollups and hotspot Jaccard."""

from __future__ import annotations

from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.rollups import (
    jaccard_index,
    resolution_ladder_diagnostics,
    rollup_to_parent,
    write_jaccard_diagnostics,
)
from pluvial_flood_risk.synthetic import build_demo_dataset


def test_jaccard_identical_sets():
    s = {"a", "b"}
    assert jaccard_index(s, s) == 1.0
    assert jaccard_index(set(), set()) == 1.0
    assert jaccard_index({"a"}, {"b"}) == 0.0


def test_rollup_mean_max_p90():
    cells = bbox_to_cells(10.70, 59.90, 10.73, 59.93, 10)
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.73, 59.93), resolution=10)
    df = df.loc[df["h3_index"].isin(cells)].copy()
    rolled = rollup_to_parent(df, "flood_risk", parent_res=9)
    assert len(rolled) > 0
    assert {"flood_risk_mean", "flood_risk_max", "flood_risk_p90"}.issubset(rolled.columns)
    assert (rolled["flood_risk_max"] + 1e-9 >= rolled["flood_risk_mean"]).all()


def test_ladder_jaccard_bounds(tmp_path):
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    table = resolution_ladder_diagnostics(df, "flood_risk", resolutions=[8, 9, 10], hotspot_quantile=0.8)
    assert len(table) >= 2
    assert table["jaccard"].between(0.0, 1.0).all()
    assert table["f1"].between(0.0, 1.0).all()
    assert set(table["aggregation"]) <= {"mean", "max", "p90"}
    csv_path = tmp_path / "jaccard_by_resolution.csv"
    written = write_jaccard_diagnostics(df, csv_path, value_col="flood_risk", resolutions=[8, 9, 10])
    assert csv_path.exists()
    assert len(written) == len(table)


def test_jaccard_fine_ladder_includes_r10_pairs(tmp_path):
    """Paper E2: fine_res>=10 with coarse parents (not only R9→R8)."""
    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    table = resolution_ladder_diagnostics(
        df, "flood_risk", resolutions=[8, 9, 10], hotspot_quantile=0.8
    )
    assert not table.empty
    assert int(table["fine_res"].max()) >= 10
    coarse = set(int(x) for x in table["coarse_res"].unique())
    assert 9 in coarse
    assert 8 in coarse
    assert (table["fine_res"] > table["coarse_res"]).all()
    csv_path = tmp_path / "jaccard_fine_ladder.csv"
    written = write_jaccard_diagnostics(
        df, csv_path, value_col="flood_risk", resolutions=[8, 9, 10]
    )
    assert csv_path.exists()
    assert len(written) >= 6  # two coarse × three aggregations
