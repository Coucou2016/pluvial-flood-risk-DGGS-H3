"""Parent/child H3 rollups and hotspot Jaccard / F1 diagnostics."""

from __future__ import annotations

from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pluvial_flood_risk.h3_grid import cell_parent, cell_resolution


def jaccard_index(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return float(len(a & b) / len(union)) if union else 0.0


def f1_sets(pred: set, truth: set) -> float:
    if not pred and not truth:
        return 1.0
    tp = len(pred & truth)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(truth) if truth else 0.0
    if precision + recall == 0:
        return 0.0
    return float(2.0 * precision * recall / (precision + recall))


def hotspot_ids(
    cell_ids: list[str] | np.ndarray,
    values: np.ndarray,
    quantile: float = 0.9,
    absolute: float | None = None,
) -> tuple[set[str], float]:
    values = np.asarray(values, dtype=np.float64)
    if absolute is not None:
        thresh = float(absolute)
    elif len(values) == 0:
        return set(), float("nan")
    else:
        thresh = float(np.quantile(values, quantile))
    hot = {str(c) for c, v in zip(cell_ids, values, strict=True) if np.isfinite(v) and v >= thresh}
    return hot, thresh


def rollup_to_parent(
    df: pd.DataFrame,
    value_col: str,
    parent_res: int,
    cell_col: str = "h3_index",
) -> pd.DataFrame:
    """
    Aggregate a fine H3 table to parent cells (mean / max / p90 of ``value_col``).
    """
    if cell_col not in df.columns or value_col not in df.columns:
        raise KeyError(f"rollup requires '{cell_col}' and '{value_col}'")
    if df.empty:
        return pd.DataFrame(
            columns=[
                "h3_index",
                f"{value_col}_mean",
                f"{value_col}_max",
                f"{value_col}_p90",
                "n_children",
                "h3_resolution",
            ]
        )

    work = df[[cell_col, value_col]].copy()
    work[cell_col] = work[cell_col].astype(str)
    work["parent"] = [cell_parent(c, parent_res) for c in work[cell_col]]

    def _p90(s: pd.Series) -> float:
        return float(np.nanpercentile(s.to_numpy(dtype=np.float64), 90))

    grouped = work.groupby("parent", as_index=False).agg(
        **{
            f"{value_col}_mean": (value_col, "mean"),
            f"{value_col}_max": (value_col, "max"),
            f"{value_col}_p90": (value_col, _p90),
            "n_children": (value_col, "size"),
        }
    )
    grouped = grouped.rename(columns={"parent": "h3_index"})
    grouped["h3_resolution"] = parent_res
    return grouped


def resolution_ladder_diagnostics(
    df: pd.DataFrame,
    value_col: str,
    resolutions: list[int] | None = None,
    hotspot_quantile: float = 0.9,
    cell_col: str = "h3_index",
) -> pd.DataFrame:
    """
    Hotspot Jaccard / F1 and extrema-smoothing when rolling a fine grid to coarser parents.

    This is the DGGS scale-loss diagnostic (cf. Svellingen et al. 2026 Jaccard of
    R13 vs R10 hotspots). Mean aggregation smooths extrema; max / p90 preserve them.
    """
    if df.empty:
        return pd.DataFrame()

    work = df.copy()
    work[cell_col] = work[cell_col].astype(str)
    if "h3_resolution" in work.columns:
        native_res = int(work["h3_resolution"].max())
        work = work.loc[work["h3_resolution"] == native_res].copy()
    else:
        native_res = cell_resolution(str(work[cell_col].iloc[0]))

    if resolutions is None:
        lo = max(0, native_res - 3)
        resolutions = list(range(lo, native_res + 1))

    fine_hot, fine_thresh = hotspot_ids(
        work[cell_col].tolist(),
        work[value_col].to_numpy(dtype=np.float64),
        quantile=hotspot_quantile,
    )

    rows: list[dict] = []
    for coarse in sorted(set(int(r) for r in resolutions)):
        if coarse >= native_res:
            continue
        rolled = rollup_to_parent(work, value_col, coarse, cell_col=cell_col)
        fine_hot_parents = {h3.cell_to_parent(c, coarse) for c in fine_hot}

        jaccards: dict[str, float] = {}
        for agg in ("mean", "max", "p90"):
            col = f"{value_col}_{agg}"
            coarse_hot, thresh = hotspot_ids(
                rolled["h3_index"].tolist(),
                rolled[col].to_numpy(dtype=np.float64),
                quantile=hotspot_quantile,
            )
            jac = jaccard_index(fine_hot_parents, coarse_hot)
            f1 = f1_sets(coarse_hot, fine_hot_parents)
            jaccards[agg] = jac
            rows.append(
                {
                    "fine_res": native_res,
                    "coarse_res": coarse,
                    "aggregation": agg,
                    "hotspot_quantile": hotspot_quantile,
                    "n_fine": int(len(work)),
                    "n_coarse": int(len(rolled)),
                    "n_hotspot_fine": int(len(fine_hot)),
                    "n_hotspot_fine_parents": int(len(fine_hot_parents)),
                    "n_hotspot_coarse": int(len(coarse_hot)),
                    "fine_hotspot_threshold": fine_thresh,
                    "coarse_hotspot_threshold": thresh,
                    "jaccard": jac,
                    "f1": f1,
                    "extrema_smoothing": float("nan"),
                }
            )

        # Extrema smoothing: hotspot agreement lost by mean vs preserved by max
        smoothing = float(jaccards.get("max", 0.0) - jaccards.get("mean", 0.0))
        for row in rows:
            if row["coarse_res"] == coarse and row["fine_res"] == native_res:
                row["extrema_smoothing"] = smoothing

    return pd.DataFrame(rows)


def write_jaccard_diagnostics(
    df: pd.DataFrame,
    out_path: Path | str,
    value_col: str = "predicted_risk",
    resolutions: list[int] | None = None,
    hotspot_quantile: float = 0.9,
) -> pd.DataFrame:
    """Write the paper-style Jaccard-vs-resolution table as CSV."""
    if value_col not in df.columns:
        if "flood_risk" in df.columns:
            value_col = "flood_risk"
        elif "PFI_h" in df.columns:
            value_col = "PFI_h"
        else:
            raise KeyError("No value column for diagnostics (tried predicted_risk, flood_risk, PFI_h).")

    table = resolution_ladder_diagnostics(
        df,
        value_col=value_col,
        resolutions=resolutions,
        hotspot_quantile=hotspot_quantile,
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)
    png_path = out_path.with_suffix(".png")
    try:
        from pluvial_flood_risk.figures import plot_jaccard_ladder

        plot_jaccard_ladder(table, png_path)
    except Exception:
        pass
    return table
