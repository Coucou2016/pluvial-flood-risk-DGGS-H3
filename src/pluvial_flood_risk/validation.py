"""Training-table validation and interpretability warnings."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import (
    FEATURE_COLUMNS,
    PROVENANCE_SYNTHETIC,
    TARGET_CLASS_COLUMN,
)


FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "elevation_m": (-50.0, 3000.0),
    "slope_deg": (0.0, 90.0),
    "flow_accum_proxy": (0.0, 1e6),
    "impervious_frac": (0.0, 1.0),
    "building_density": (0.0, 1e5),
    "dist_stream_m": (0.0, 50_000.0),
    "rainfall_mm_h": (0.0, 500.0),
    "land_cover_urban": (0.0, 1.0),
}


def validate_training_table(
    df: pd.DataFrame,
    min_cells: int = 50,
    min_positive_fraction: float = 0.05,
    max_positive_fraction: float = 0.95,
) -> list[str]:
    """Return human-readable issues; empty list means checks passed."""
    issues: list[str] = []

    if len(df) < min_cells:
        issues.append(f"Only {len(df)} cells (minimum recommended: {min_cells}).")

    if TARGET_CLASS_COLUMN in df.columns:
        pos_frac = float(df[TARGET_CLASS_COLUMN].mean())
        if pos_frac < min_positive_fraction or pos_frac > max_positive_fraction:
            issues.append(
                f"Class imbalance: flood_class positive fraction {pos_frac:.3f} "
                f"(expected between {min_positive_fraction} and {max_positive_fraction})."
            )

    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            issues.append(f"Missing feature column: {col}")
            continue
        if df[col].isna().any():
            issues.append(f"NaN values in feature column '{col}'.")
        lo, hi = FEATURE_RANGES.get(col, (-np.inf, np.inf))
        below = (df[col] < lo).sum()
        above = (df[col] > hi).sum()
        if below or above:
            issues.append(
                f"Feature '{col}' has {int(below)} values below {lo} "
                f"and {int(above)} above {hi} (sanity range check)."
            )

    if "label_source" in df.columns and (df["label_source"] == PROVENANCE_SYNTHETIC).all():
        issues.append(
            "All labels are synthetic - metrics measure fit to a demo formula, "
            "not real flood observations."
        )

    if "assembly_mode" in df.columns and (df["assembly_mode"] == "fixture").all():
        issues.append(
            "assembly_mode=fixture: observed-join / zonal code paths ran on "
            "schema fixtures, not live NYC Open Data. Do not report accuracy as science."
        )

    return issues


def emit_validation_warnings(issues: list[str]) -> None:
    for msg in issues:
        warnings.warn(msg, stacklevel=2)
