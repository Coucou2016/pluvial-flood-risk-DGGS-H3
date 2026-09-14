"""Multi-resolution rollups and hotspot Jaccard."""

from __future__ import annotations

import pytest

from pluvial_flood_risk.h3_grid import bbox_to_cells
from pluvial_flood_risk.rollups import (
    area_weighted_soft_jaccard,
    canonical_ladder_heatmap,
    hotspot_weights_area_budget,
    jaccard_index,
    parent_area_weighted_membership,
    resolution_ladder_diagnostics,
    resolution_ladder_topk_diagnostics,
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


def test_area_budget_tied_group_matches_target():
    ids = [f"c{i}" for i in range(5)]
    values = [1.0, 1.0, 1.0, 1.0, 1.0]
    areas = [10.0, 10.0, 10.0, 10.0, 10.0]
    target = 25.0
    weights, thresh = hotspot_weights_area_budget(ids, values, areas, target)
    assert abs(thresh - 1.0) < 1e-12
    selected = sum(a * weights[i] for i, a in zip(ids, areas))
    assert abs(selected - target) < 1e-9
    assert all(abs(w - 0.5) < 1e-9 for w in weights.values())


def test_area_budget_does_not_mix_cell_count_topk():
    ids = ["a", "b", "c"]
    values = [3.0, 2.0, 1.0]
    areas = [100.0, 1.0, 1.0]
    weights, _ = hotspot_weights_area_budget(ids, values, areas, target_area=50.0)
    # Half of the large top cell, not one "top-k" cell at weight 1.
    assert abs(weights["a"] - 0.5) < 1e-9
    assert "b" not in weights
    assert abs(sum(areas[i] * weights.get(cid, 0.0) for i, cid in enumerate(ids)) - 50.0) < 1e-9


def test_parent_membership_is_area_weighted_not_capped_sum():
    fine_ids = ["f1", "f2"]
    fine_weights = {"f1": 0.5, "f2": 0.5}
    fine_areas = {"f1": 10.0, "f2": 30.0}

    class _FakeH3:
        @staticmethod
        def cell_to_parent(cid, _res):
            return "P"

    import pluvial_flood_risk.rollups as rollups

    orig = rollups.h3.cell_to_parent
    rollups.h3.cell_to_parent = _FakeH3.cell_to_parent
    try:
        w_ref, support = parent_area_weighted_membership(fine_ids, fine_weights, fine_areas, 8)
    finally:
        rollups.h3.cell_to_parent = orig
    assert abs(support["P"] - 40.0) < 1e-12
    assert abs(w_ref["P"] - 0.5) < 1e-12


def test_area_weighted_soft_jaccard_identity():
    w = {"a": 0.2, "b": 1.0}
    areas = {"a": 10.0, "b": 5.0}
    assert area_weighted_soft_jaccard(w, w, areas) == pytest.approx(1.0)


def test_canonical_ladder_heatmap_reads_table_only():
    import pandas as pd

    table = pd.DataFrame(
        {
            "fine_res": [10, 10, 10, 10],
            "coarse_res": [9, 8, 9, 8],
            "aggregation": ["mean", "mean", "max", "max"],
            "jaccard": [0.31, 0.12, 0.40, 0.22],
        }
    )
    heat = canonical_ladder_heatmap(table)
    assert heat.loc["mean", 9] == pytest.approx(0.31)
    assert heat.loc["mean", 8] == pytest.approx(0.12)


def test_area_budget_ladder_invariants():
    import numpy as np

    df = build_demo_dataset(bbox=(10.70, 59.90, 10.74, 59.94), resolution=10)
    table = resolution_ladder_topk_diagnostics(
        df,
        "flood_risk",
        resolutions=[8, 9, 10],
        hotspot_budget=0.10,
        n_hard_boot=8,
        random_seed=42,
    )
    assert not table.empty
    assert (table["budget_match_mode"] == "strict_area_budget").all()
    assert (table["matched_budgets_cell_count"] == False).all()  # noqa: E712
    assert (table["area_budget_rel_err_fine"] < 1e-4).all()
    assert (table["area_budget_rel_err_coarse"] < 1e-4).all()
    assert table["jaccard"].between(0.0, 1.0).all()
    np.testing.assert_allclose(table["jaccard"], table["jaccard_soft"], atol=1e-12)

