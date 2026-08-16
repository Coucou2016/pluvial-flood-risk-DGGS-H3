"""Coastal / surge overlay as a negative control (not a pluvial label)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.labels import attach_observed_labels


def attach_coastal_overlay(
    df: pd.DataFrame,
    coastal_path: Path | str,
    prefix: str = "sandy",
) -> pd.DataFrame:
    """
    Join a coastal-surge polygon (e.g. FEMA / Sandy inundation) onto H3 cells.

    Writes ``{prefix}_area_frac`` and ``{prefix}_class``. Does **not** change
    ``flood_risk`` / ``flood_class`` / ``label_source``.
    """
    path = Path(coastal_path)
    if not path.exists():
        raise FileNotFoundError(path)

    overlay = attach_observed_labels(df[["h3_index"]].copy(), path, risk_column=f"{prefix}_risk")
    out = df.copy()
    out[f"{prefix}_area_frac"] = overlay["flood_area_frac"].to_numpy()
    out[f"{prefix}_class"] = overlay["flood_class"].to_numpy()
    return out


def negative_control_metrics(
    df: pd.DataFrame,
    score_col: str | None = None,
    coastal_frac_col: str = "sandy_area_frac",
    pluvial_frac_col: str = "flood_area_frac",
    pluvial_class_col: str = "flood_class",
    score_quantile: float = 0.8,
) -> dict[str, float | str]:
    """
    Quantify whether high scores concentrate in coastal-only cells.

    A pluvial model should score **pluvial-only** cells higher than **coastal-only**
    cells. High ``coastal_only_among_high_score`` is a leakage warning (learning
    surge / low elevation near the water rather than rainfall ponding).
    """
    if coastal_frac_col not in df.columns:
        raise KeyError(f"Missing {coastal_frac_col}; call attach_coastal_overlay first.")

    n = int(len(df))
    coastal = df[coastal_frac_col].to_numpy(dtype=np.float64) > 0
    if pluvial_frac_col in df.columns:
        pluvial = df[pluvial_frac_col].to_numpy(dtype=np.float64) > 0
    elif pluvial_class_col in df.columns:
        pluvial = df[pluvial_class_col].to_numpy() == 1
    else:
        raise KeyError("Need flood_area_frac or flood_class for the pluvial mask.")

    coastal_only = coastal & ~pluvial
    pluvial_only = pluvial & ~coastal
    both = coastal & pluvial
    neither = ~coastal & ~pluvial

    assembly_mode = "unknown"
    if "assembly_mode" in df.columns and len(df):
        assembly_mode = str(df["assembly_mode"].iloc[0])
    if assembly_mode == "fixture":
        note = (
            "coastal overlay is a negative control, not a training label; "
            "fixture/synthetic numbers are pipeline QA only — not scientific skill"
        )
    elif assembly_mode == "opendata":
        note = (
            "coastal overlay is a negative control, not a training label; "
            "metrics are on the live open-data stack (still Lower Manhattan / stated bbox, "
            "not citywide; not PFIb)"
        )
    else:
        note = (
            "coastal overlay is a negative control, not a training label; "
            f"interpret with assembly_mode={assembly_mode}"
        )

    metrics: dict[str, float | str] = {
        "n_cells": float(n),
        "n_coastal": float(coastal.sum()),
        "n_pluvial": float(pluvial.sum()),
        "n_coastal_only": float(coastal_only.sum()),
        "n_pluvial_only": float(pluvial_only.sum()),
        "n_both": float(both.sum()),
        "n_neither": float(neither.sum()),
        "frac_coastal_only": float(coastal_only.mean()) if n else 0.0,
        "frac_pluvial_only": float(pluvial_only.mean()) if n else 0.0,
        "assembly_mode": assembly_mode,
        "note": note,
    }

    if score_col is None:
        for cand in ("predicted_risk", "PFI_h", "flood_risk"):
            if cand in df.columns:
                score_col = cand
                break
    if score_col is None or score_col not in df.columns:
        return metrics

    scores = df[score_col].to_numpy(dtype=np.float64)
    metrics["score_col"] = score_col

    def _mean(mask: np.ndarray) -> float:
        if not mask.any():
            return float("nan")
        return float(np.nanmean(scores[mask]))

    metrics["mean_score_coastal_only"] = _mean(coastal_only)
    metrics["mean_score_pluvial_only"] = _mean(pluvial_only)
    metrics["mean_score_both"] = _mean(both)
    metrics["mean_score_neither"] = _mean(neither)

    finite = np.isfinite(scores)
    if finite.any():
        thresh = float(np.nanquantile(scores[finite], score_quantile))
        high = finite & (scores >= thresh)
        metrics["high_score_quantile"] = score_quantile
        metrics["high_score_threshold"] = thresh
        metrics["n_high_score"] = float(high.sum())
        if high.any():
            metrics["coastal_only_among_high_score"] = float(coastal_only[high].mean())
            metrics["pluvial_among_high_score"] = float(pluvial[high].mean())
        else:
            metrics["coastal_only_among_high_score"] = float("nan")
            metrics["pluvial_among_high_score"] = float("nan")

        pluvial_mean = metrics["mean_score_pluvial_only"]
        coastal_mean = metrics["mean_score_coastal_only"]
        if np.isfinite(pluvial_mean) and np.isfinite(coastal_mean):
            metrics["pluvial_minus_coastal_mean_score"] = float(pluvial_mean - coastal_mean)
    return metrics
