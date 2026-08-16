"""Adaptive H3 refinement: coarse screen, then children only where needed."""

from __future__ import annotations

from typing import Any

import h3
import numpy as np
import pandas as pd

from pluvial_flood_risk.h3_grid import (
    cell_children,
    cell_resolution,
    grid_disk,
)


def uncertainty_from_probability(proba: np.ndarray) -> np.ndarray:
    """1 at p=0.5 (most uncertain), 0 at p in {0, 1}."""
    p = np.clip(np.asarray(proba, dtype=np.float64), 0.0, 1.0)
    return 1.0 - np.abs(p - 0.5) * 2.0


def select_parents_to_refine(
    cells: list[str],
    scores: np.ndarray,
    score_quantile: float = 0.8,
    uncertainty: np.ndarray | None = None,
    uncertainty_min: float = 0.7,
    expand_k: int = 0,
) -> list[str]:
    """
    Parents exceeding a risk quantile and/or probability uncertainty.

    ``expand_k`` adds k-ring neighbours that still lie in ``cells`` (contiguity).
    """
    scores = np.asarray(scores, dtype=np.float64)
    if len(cells) == 0:
        return []
    thresh = float(np.nanquantile(scores, score_quantile))
    mask = np.isfinite(scores) & (scores >= thresh)
    if uncertainty is not None:
        u = np.asarray(uncertainty, dtype=np.float64)
        mask = mask | (np.isfinite(u) & (u >= uncertainty_min))
    selected = [c for c, m in zip(cells, mask, strict=True) if m]
    if expand_k and selected:
        allowed = set(cells)
        extra: set[str] = set()
        for c in selected:
            extra.update(grid_disk(c, expand_k))
        selected = sorted(set(selected) | (extra & allowed))
    else:
        selected = sorted(set(selected))
    return selected


def children_of_parents(parent_cells: list[str], fine_res: int) -> list[str]:
    out: list[str] = []
    for p in parent_cells:
        pres = cell_resolution(p)
        if fine_res <= pres:
            out.append(p)
        else:
            out.extend(cell_children(p, fine_res))
    return sorted(set(out))


def mixed_resolution_cells(
    coarse_cells: list[str],
    refine_parents: list[str],
    fine_res: int,
) -> list[str]:
    """Keep unselected coarse cells; replace selected parents with fine children."""
    refine_set = set(refine_parents)
    kept = [c for c in coarse_cells if c not in refine_set]
    refined = children_of_parents(refine_parents, fine_res)
    return sorted(set(kept) | set(refined))


def cell_covered_by_index(fine_cell: str, mixed_set: set[str]) -> bool:
    """True if the fine cell itself or any coarser parent is in the mixed index."""
    if fine_cell in mixed_set:
        return True
    res = h3.get_resolution(fine_cell)
    for parent_res in range(res - 1, -1, -1):
        if h3.cell_to_parent(fine_cell, parent_res) in mixed_set:
            return True
    return False


def adaptive_vs_uniform_metrics(
    mixed_cells: list[str],
    uniform_fine_cells: list[str],
    uniform_scores: np.ndarray,
    hotspot_quantile: float = 0.9,
) -> dict[str, float]:
    """
    Hotspot recall of an adaptive mixed-resolution index vs a uniform fine grid,
    plus cell-count ratio (adaptive / uniform).
    """
    from pluvial_flood_risk.rollups import hotspot_ids

    uniform_scores = np.asarray(uniform_scores, dtype=np.float64)
    hot, _ = hotspot_ids(uniform_fine_cells, uniform_scores, quantile=hotspot_quantile)
    mixed_set = set(mixed_cells)
    recalled = sum(1 for c in hot if cell_covered_by_index(c, mixed_set))
    n_hot = max(len(hot), 1)
    n_uniform = max(len(uniform_fine_cells), 1)
    return {
        "n_adaptive": float(len(mixed_cells)),
        "n_uniform_fine": float(len(uniform_fine_cells)),
        "cell_count_ratio": float(len(mixed_cells) / n_uniform),
        "n_hotspot_uniform": float(len(hot)),
        "hotspot_recall": float(recalled / n_hot),
        "hotspot_quantile": float(hotspot_quantile),
    }


def run_adaptive_refinement(
    coarse_df: pd.DataFrame,
    fine_res: int,
    score_col: str = "predicted_risk",
    proba_col: str | None = "flood_probability",
    score_quantile: float = 0.8,
    uncertainty_min: float = 0.7,
    expand_k: int = 1,
    uniform_fine_df: pd.DataFrame | None = None,
    hotspot_quantile: float = 0.9,
) -> tuple[list[str], dict[str, Any]]:
    """
    Select high-risk / high-uncertainty coarse cells and expand to ``fine_res``.

    Returns (mixed-resolution cell ids, metrics dict).
    """
    cells = coarse_df["h3_index"].astype(str).tolist()
    scores = coarse_df[score_col].to_numpy(dtype=np.float64)
    uncertainty = None
    if proba_col and proba_col in coarse_df.columns:
        uncertainty = uncertainty_from_probability(coarse_df[proba_col].to_numpy(dtype=np.float64))

    parents = select_parents_to_refine(
        cells,
        scores,
        score_quantile=score_quantile,
        uncertainty=uncertainty,
        uncertainty_min=uncertainty_min,
        expand_k=expand_k,
    )
    mixed = mixed_resolution_cells(cells, parents, fine_res)
    coarse_res = cell_resolution(cells[0]) if cells else -1
    metrics: dict[str, Any] = {
        "coarse_res": coarse_res,
        "fine_res": fine_res,
        "n_coarse": len(cells),
        "n_parents_refined": len(parents),
        "n_adaptive": len(mixed),
        "score_quantile": score_quantile,
        "expand_k": expand_k,
        "uncertainty_min": uncertainty_min,
    }
    if uniform_fine_df is not None and len(uniform_fine_df) and score_col in uniform_fine_df.columns:
        metrics.update(
            adaptive_vs_uniform_metrics(
                mixed,
                uniform_fine_df["h3_index"].astype(str).tolist(),
                uniform_fine_df[score_col].to_numpy(dtype=np.float64),
                hotspot_quantile=hotspot_quantile,
            )
        )
    else:
        n_uniform_est = len(children_of_parents(cells, fine_res)) if cells else 0
        metrics["n_uniform_fine"] = float(n_uniform_est)
        metrics["cell_count_ratio"] = float(len(mixed) / n_uniform_est) if n_uniform_est else float("nan")
    return mixed, metrics
