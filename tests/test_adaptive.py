"""Adaptive H3 refinement."""

from __future__ import annotations

import numpy as np

from pluvial_flood_risk.adaptive import (
    adaptive_vs_uniform_metrics,
    run_adaptive_refinement,
    select_parents_to_refine,
)
from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_children
from pluvial_flood_risk.synthetic import build_demo_dataset


TINY = (10.70, 59.90, 10.73, 59.93)


def test_select_quantile_and_neighbor_expand():
    cells = bbox_to_cells(*TINY, 8)
    scores = np.linspace(0, 1, len(cells))
    selected = select_parents_to_refine(cells, scores, score_quantile=0.9, expand_k=0)
    assert 1 <= len(selected) <= max(3, len(cells) // 5)
    expanded = select_parents_to_refine(cells, scores, score_quantile=0.9, expand_k=1)
    assert len(expanded) >= len(selected)


def test_adaptive_fewer_cells_than_uniform_fine():
    df = build_demo_dataset(bbox=TINY, resolution=8)
    df = df.copy()
    df["predicted_risk"] = df["flood_risk"]
    mixed, metrics = run_adaptive_refinement(
        df,
        fine_res=10,
        score_col="predicted_risk",
        proba_col=None,
        score_quantile=0.8,
        expand_k=0,
    )
    n_uniform = sum(len(cell_children(c, 10)) for c in df["h3_index"].astype(str))
    assert metrics["n_adaptive"] < n_uniform
    assert metrics["cell_count_ratio"] < 1.0
    assert len(mixed) == metrics["n_adaptive"]


def test_hotspot_recall_vs_uniform():
    coarse = bbox_to_cells(*TINY, 8)
    fine = []
    for c in coarse:
        fine.extend(cell_children(c, 10))
    rng = np.random.default_rng(0)
    scores = rng.random(len(fine))
    # Refine every coarse parent → recall should be 1
    mixed = fine
    m = adaptive_vs_uniform_metrics(mixed, fine, scores, hotspot_quantile=0.8)
    assert m["hotspot_recall"] == 1.0
    assert m["cell_count_ratio"] == 1.0
