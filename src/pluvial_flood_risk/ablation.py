"""Ablation: fixed-resolution H3 vs adaptive refinement (paper P1.3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from pluvial_flood_risk.adaptive import run_adaptive_refinement


def adaptive_vs_fixed_ablation(
    coarse_df: pd.DataFrame,
    fine_res: int,
    score_col: str = "PFI_h",
    proba_col: str | None = "flood_probability",
    score_quantile: float = 0.8,
    expand_k: int = 1,
    hotspot_quantile: float = 0.9,
) -> dict[str, Any]:
    """
    Compare adaptive mixed-resolution index against keeping the full coarse grid
    and against a uniform fine grid (cell count + hotspot recall).

    ``coarse_df`` must already carry trained scores (``PFI_h`` / predicted_risk).
    """
    if score_col not in coarse_df.columns:
        raise KeyError(f"ablation requires score column '{score_col}'")

    mixed, adaptive_metrics = run_adaptive_refinement(
        coarse_df,
        fine_res=fine_res,
        score_col=score_col,
        proba_col=proba_col if proba_col and proba_col in coarse_df.columns else None,
        score_quantile=score_quantile,
        expand_k=expand_k,
        hotspot_quantile=hotspot_quantile,
    )

    n_fixed = int(len(coarse_df))
    n_adaptive = int(len(mixed))
    out: dict[str, Any] = {
        "ablation": "adaptive_vs_fixed_h3",
        "score_col": score_col,
        "n_fixed_coarse": n_fixed,
        "n_adaptive_mixed": n_adaptive,
        "cell_count_ratio_vs_fixed": float(n_adaptive / n_fixed) if n_fixed else float("nan"),
        "note": (
            "Fixed = keep all coarse cells; adaptive = refine high-score parents to fine_res. "
            "Hotspot recall vs uniform fine is under adaptive_* keys when estimated."
        ),
    }
    for k, v in adaptive_metrics.items():
        out[f"adaptive_{k}"] = v
    return out


def write_ablation_report(metrics: dict[str, Any], out_path: Path | str) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(out_path, index=False)
    return out_path
