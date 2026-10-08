"""Adaptive H3 refinement: coarse screen, then children only where needed.

Major Revision 2026-10-08 (P0-7/P0-8)
-------------------------------------
``hotspot_recall`` used to be a coverage tautology: a complete mixed-resolution
partition *always* covers every fine hotspot because the coarse parent covers it.
The paper metric is now ``hotspot_refinement_recall`` — a hotspot is only recalled
if it is **actually refined** to the fine resolution (present as a fine child of a
refined parent), not merely covered by a coarse parent. Coverage is reported
separately as ``hotspot_coverage_recall``.

Completeness (P0-8) is reported explicitly: ``refined_children_total``,
``refined_children_scorable``, ``refined_children_missing`` and
``missing_fraction``, plus best/worst-case recall bounds (missing children are
counted as hits in the best case and misses in the worst case).
"""

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
    Parents exceeding a susceptibility quantile and/or probability uncertainty.

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
    *,
    refined_fine_cells: list[str] | None = None,
    uniform_scorable_cells: list[str] | None = None,
) -> dict[str, float]:
    """
    Refinement(not coverage) recall/precision/enrichment of an adaptive mixed
    index vs a uniform fine grid, plus completeness diagnostics.

    ``refined_fine_cells`` is the set of fine cells that are **actually present**
    (children of refined parents). If omitted it defaults to the fine-resolution
    members of ``mixed_cells``. ``hotspot_refinement_recall`` counts a uniform
    hotspot as recalled only when it is in ``refined_fine_cells`` — this exposes
    the old coverage tautology (an un-refined hotspot scores 0).

    ``uniform_scorable_cells`` (if given) is the subdomain for which fine scores
    exist; used to report best/worst-case recall bounds when fine data is missing
    at DEM edges (P0-8).
    """
    from pluvial_flood_risk.rollups import hotspot_ids

    uniform_scores = np.asarray(uniform_scores, dtype=np.float64)
    uniform_fine_cells = [str(c) for c in uniform_fine_cells]
    hot, _ = hotspot_ids(uniform_fine_cells, uniform_scores, quantile=hotspot_quantile)
    mixed_set = set(str(c) for c in mixed_cells)
    fine_res = max((cell_resolution(c) for c in uniform_fine_cells), default=0)
    if refined_fine_cells is None:
        refined_fine_set = {str(c) for c in mixed_cells if cell_resolution(str(c)) == fine_res}
    else:
        refined_fine_set = {str(c) for c in refined_fine_cells}
    refined_fine_set &= set(uniform_fine_cells)

    n_hot = max(len(hot), 1)
    n_uniform = max(len(uniform_fine_cells), 1)
    n_refined_fine = max(len(refined_fine_set), 1)

    refined_hot = hot & refined_fine_set
    coverage_hot = {c for c in hot if cell_covered_by_index(c, mixed_set)}

    # Completeness: DEM-edge NaN dropped some fine cells entirely.
    refined_children_total = len(refined_fine_set | (hot & mixed_set))
    if uniform_scorable_cells is not None:
        scorable = set(str(c) for c in uniform_scorable_cells)
        refined_scorable = refined_fine_set & scorable
        missing = refined_fine_set - scorable
    else:
        refined_scorable = refined_fine_set
        missing = set()
    missing_fraction = (
        float(len(missing)) / float(max(len(refined_fine_set), 1)) if refined_fine_set else 0.0
    )
    hot_in_scorable = hot & (set(str(c) for c in uniform_scorable_cells) if uniform_scorable_cells is not None else hot)

    frac_hot_inside_refined = float(len(refined_hot)) / n_hot
    frac_hot_in_domain = float(len(hot)) / n_uniform
    enrichment = (
        frac_hot_inside_refined / frac_hot_in_domain if frac_hot_in_domain > 0 else float("nan")
    )

    # Best/worst-case recall bounds when refined children are missing (NaN) at edges.
    n_missing_hot = len(hot) - len(hot & refined_scorable)
    best_case = float(len(hot & refined_scorable) + n_missing_hot) / n_hot
    worst_case = float(len(hot & refined_scorable)) / n_hot

    return {
        "n_adaptive": float(len(mixed_cells)),
        "n_uniform_fine": float(len(uniform_fine_cells)),
        "cell_count_ratio": float(len(mixed_cells) / n_uniform),
        "n_hotspot_uniform": float(len(hot)),
        "hotspot_refinement_recall": float(len(refined_hot)) / n_hot,
        "hotspot_refinement_precision": float(len(refined_hot)) / n_refined_fine,
        "hotspot_enrichment": enrichment,
        "hotspot_coverage_recall": float(len(coverage_hot)) / n_hot,
        "hotspot_quantile": float(hotspot_quantile),
        "refined_children_total": int(refined_children_total),
        "refined_children_scorable": int(len(refined_scorable)),
        "refined_children_missing": int(len(missing)),
        "missing_fraction": missing_fraction,
        "n_hotspot_scorable": int(len(hot_in_scorable)),
        "hotspot_refinement_recall_best_case": best_case,
        "hotspot_refinement_recall_worst_case": worst_case,
    }


def cost_recall_curve(
    coarse_df: pd.DataFrame,
    uniform_fine_df: pd.DataFrame,
    fine_res: int,
    *,
    score_col: str = "susceptibility_score",
    quantiles: tuple[float, ...] = (0.70, 0.75, 0.80, 0.85, 0.90, 0.95),
    neighbor_expansion: tuple[int, ...] = (0, 1),
    hotspot_quantile: float = 0.9,
) -> pd.DataFrame:
    """Cost–recall curve over risk quantiles × neighbour expansion widths."""
    rows: list[dict] = []
    fine_cells = uniform_fine_df["h3_index"].astype(str).tolist()
    fine_scores = uniform_fine_df[score_col].to_numpy(dtype=np.float64)
    n_uniform_fine = len(fine_cells)
    for quantile in quantiles:
        for expand_k in neighbor_expansion:
            parents = select_parents_to_refine(
                coarse_df["h3_index"].astype(str).tolist(),
                coarse_df[score_col].to_numpy(dtype=np.float64),
                score_quantile=quantile,
                expand_k=expand_k,
            )
            refined_fine = children_of_parents(parents, fine_res)
            mixed = mixed_resolution_cells(
                coarse_df["h3_index"].astype(str).tolist(), parents, fine_res
            )
            metrics = adaptive_vs_uniform_metrics(
                mixed,
                fine_cells,
                fine_scores,
                hotspot_quantile=hotspot_quantile,
                refined_fine_cells=refined_fine,
                uniform_scorable_cells=fine_cells,
            )
            rows.append(
                {
                    "score_quantile": float(quantile),
                    "neighbor_expansion": int(expand_k),
                    "n_parents_refined": int(len(parents)),
                    "n_refined_children": int(len(refined_fine)),
                    "n_adaptive_mixed": int(len(mixed)),
                    "cell_count_ratio": metrics["cell_count_ratio"],
                    "hotspot_refinement_recall": metrics["hotspot_refinement_recall"],
                    "hotspot_refinement_precision": metrics["hotspot_refinement_precision"],
                    "hotspot_enrichment": metrics["hotspot_enrichment"],
                }
            )
    return pd.DataFrame(rows)


def run_adaptive_refinement(
    coarse_df: pd.DataFrame,
    fine_res: int,
    score_col: str = "susceptibility_score",
    proba_col: str | None = "susceptibility_score",
    score_quantile: float = 0.8,
    uncertainty_min: float = 0.7,
    expand_k: int = 1,
    uniform_fine_df: pd.DataFrame | None = None,
    hotspot_quantile: float = 0.9,
) -> tuple[list[str], dict[str, Any]]:
    """
    Select high-susceptibility / high-uncertainty coarse cells and expand to ``fine_res``.

    Returns (mixed-resolution cell ids, metrics dict).
    """
    # Deprecated score-column alias (P0-10): accept the old name if given.
    if score_col not in coarse_df.columns:
        for legacy in ("PFI_h", "predicted_risk", "flood_risk"):
            if legacy in coarse_df.columns:
                score_col = legacy
                break

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
    refined_fine = children_of_parents(parents, fine_res)
    coarse_res = cell_resolution(cells[0]) if cells else -1
    metrics: dict[str, Any] = {
        "coarse_res": coarse_res,
        "fine_res": fine_res,
        "n_coarse": len(cells),
        "n_parents_refined": len(parents),
        "n_adaptive": len(mixed),
        "n_refined_children_total": len(refined_fine),
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
                refined_fine_cells=refined_fine,
            )
        )
    else:
        n_uniform_est = len(children_of_parents(cells, fine_res)) if cells else 0
        metrics["n_uniform_fine"] = float(n_uniform_est)
        metrics["cell_count_ratio"] = float(len(mixed) / n_uniform_est) if n_uniform_est else float("nan")
    return mixed, metrics
