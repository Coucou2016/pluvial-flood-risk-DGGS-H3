"""Parent/child H3 rollups and hotspot Jaccard / F1 diagnostics."""

from __future__ import annotations

from pathlib import Path

import h3
import numpy as np
import pandas as pd

from pluvial_flood_risk.h3_grid import cell_area_m2, cell_parent, cell_resolution


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


AREA_BUDGET_REL_TOL = 1e-6
HARD_TIE_BOOTSTRAP_DEFAULT = 200
HARD_TIE_BOOTSTRAP_PAPER = 1000


def weighted_jaccard(weights_a: dict[str, float], weights_b: dict[str, float]) -> float:
    """Soft Jaccard using fractional membership weights in [0, 1]."""
    keys = set(weights_a) | set(weights_b)
    if not keys:
        return 1.0
    inter = sum(min(weights_a.get(k, 0.0), weights_b.get(k, 0.0)) for k in keys)
    union = sum(max(weights_a.get(k, 0.0), weights_b.get(k, 0.0)) for k in keys)
    return float(inter / union) if union > 0 else 1.0


def area_weighted_soft_jaccard(
    weights_a: dict[str, float],
    weights_b: dict[str, float],
    areas: dict[str, float],
) -> float:
    """Area-weighted soft Jaccard: Σ a min(w_a,w_b) / Σ a max(w_a,w_b)."""
    keys = set(weights_a) | set(weights_b)
    if not keys:
        return 1.0
    inter = 0.0
    union = 0.0
    for k in keys:
        area = float(areas.get(k, 0.0))
        if area <= 0.0:
            continue
        wa = float(weights_a.get(k, 0.0))
        wb = float(weights_b.get(k, 0.0))
        inter += area * min(wa, wb)
        union += area * max(wa, wb)
    return float(inter / union) if union > 0 else 1.0


def membership_area(weights: dict[str, float], areas: dict[str, float]) -> float:
    """Σ a_i w_i for keys present in either mapping."""
    return float(sum(float(areas.get(k, 0.0)) * float(w) for k, w in weights.items()))


def area_weighted_overlap(
    ids_a: set[str],
    ids_b: set[str],
    area_lookup: dict[str, float] | None = None,
) -> float:
    """Intersection-over-union weighted by cell area (m²)."""

    def _area(cid: str) -> float:
        if area_lookup and cid in area_lookup:
            return float(area_lookup[cid])
        try:
            return float(cell_area_m2(cid))
        except Exception:
            return 1.0

    keys = ids_a | ids_b
    if not keys:
        return 1.0
    inter = sum(_area(k) for k in (ids_a & ids_b))
    union = sum(_area(k) for k in keys)
    return float(inter / union) if union > 0 else 1.0


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


def hotspot_ids_topk(
    cell_ids: list[str] | np.ndarray,
    values: np.ndarray,
    k: int,
) -> tuple[set[str], float]:
    """Select exactly ``k`` cells with the largest values (legacy hard cut).

    Prefer :func:`hotspot_weights_topk` for tie-aware diagnostics. This hard
    cut still breaks residual ties by H3 index only when a binary set is required.
    """
    weights, thresh = hotspot_weights_topk(cell_ids, values, k)
    hot = {cid for cid, w in weights.items() if w >= 1.0 - 1e-12}
    # If fractional ties leave fewer than k hard members, include all tied cells
    # with positive weight as a hard set (union of the tie group).
    if len(hot) < k:
        hot = {cid for cid, w in weights.items() if w > 0}
    return hot, thresh


def hotspot_weights_topk(
    cell_ids: list[str] | np.ndarray,
    values: np.ndarray,
    k: int,
) -> tuple[dict[str, float], float]:
    """Tie-aware top-k with fractional membership at the threshold.

    Cells strictly above the k-boundary receive weight 1. Cells tied at the
    boundary value share the remaining budget equally (fractional membership),
    so lexicographic H3 index is never used to invent a unique ranking among
    equal scores. Returned threshold is the boundary value.
    """
    values = np.asarray(values, dtype=np.float64)
    ids = [str(c) for c in cell_ids]
    finite = [(float(values[i]), ids[i]) for i in range(len(ids)) if np.isfinite(values[i])]
    finite.sort(key=lambda t: -t[0])
    if k <= 0 or not finite:
        return {}, float("nan")
    k = min(int(k), len(finite))
    boundary_value = finite[k - 1][0]
    weights: dict[str, float] = {}
    # Strict winners
    for val, cid in finite:
        if val > boundary_value + 1e-15:
            weights[cid] = 1.0
        else:
            break
    remaining = k - len(weights)
    tied = [cid for val, cid in finite if abs(val - boundary_value) <= 1e-15]
    if remaining <= 0:
        return weights, float(boundary_value)
    if not tied:
        return weights, float(boundary_value)
    frac = float(remaining) / float(len(tied))
    for cid in tied:
        weights[cid] = frac
    return weights, float(boundary_value)


def hotspot_weights_area_budget(
    cell_ids: list[str] | np.ndarray,
    values: np.ndarray,
    areas: np.ndarray | list[float],
    target_area: float,
) -> tuple[dict[str, float], float]:
    """Strict area-budget hotspot membership with fractional tied groups.

    Cells are grouped by descending score. Each whole group whose total area is
    at most the remaining budget receives weight 1. The first group that would
    exceed the remaining budget receives a uniform fractional weight
    ``remaining / group_area`` so that ``Σ a_i w_i`` equals ``target_area``
    (within floating-point tolerance). H3 index is never used to break ties.
    Cell-count top-k is not applied.
    """
    values = np.asarray(values, dtype=np.float64)
    areas_arr = np.asarray(areas, dtype=np.float64)
    ids = [str(c) for c in cell_ids]
    if len(ids) != len(values) or len(ids) != len(areas_arr):
        raise ValueError("cell_ids, values, and areas must have the same length")
    if target_area <= 0.0 or not ids:
        return {}, float("nan")

    finite: list[tuple[float, float, str]] = []
    for i, cid in enumerate(ids):
        if not np.isfinite(values[i]) or not np.isfinite(areas_arr[i]) or areas_arr[i] <= 0.0:
            continue
        finite.append((float(values[i]), float(areas_arr[i]), cid))
    if not finite:
        return {}, float("nan")

    total_area = float(sum(a for _, a, _ in finite))
    target = min(float(target_area), total_area)
    finite.sort(key=lambda t: -t[0])

    weights: dict[str, float] = {}
    remaining = target
    i = 0
    boundary = float("nan")
    while i < len(finite) and remaining > AREA_BUDGET_REL_TOL * max(target, 1.0):
        score = finite[i][0]
        group: list[tuple[float, str]] = []
        while i < len(finite) and abs(finite[i][0] - score) <= 1e-15:
            group.append((finite[i][1], finite[i][2]))
            i += 1
        group_area = float(sum(a for a, _ in group))
        if group_area <= 0.0:
            continue
        boundary = score
        if group_area <= remaining + AREA_BUDGET_REL_TOL * max(target, 1.0):
            for _, cid in group:
                weights[cid] = 1.0
            remaining -= group_area
        else:
            frac = float(remaining / group_area)
            for _, cid in group:
                weights[cid] = frac
            remaining = 0.0
            break
    return weights, float(boundary)


def parent_area_weighted_membership(
    fine_ids: list[str],
    fine_weights: dict[str, float],
    fine_areas: dict[str, float],
    parent_res: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Area-weighted parent membership w_ref(p)=Σ a_i w_i / Σ a_i over children."""
    hot_area: dict[str, float] = {}
    support: dict[str, float] = {}
    for cid in fine_ids:
        area = float(fine_areas.get(cid, 0.0))
        if area <= 0.0:
            continue
        parent = h3.cell_to_parent(cid, parent_res)
        support[parent] = support.get(parent, 0.0) + area
        hot_area[parent] = hot_area.get(parent, 0.0) + area * float(fine_weights.get(cid, 0.0))
    w_ref = {p: (hot_area.get(p, 0.0) / a) if a > 0.0 else 0.0 for p, a in support.items()}
    return w_ref, support


def _hard_mask_area_budget(
    scores: np.ndarray,
    areas: np.ndarray,
    target_area: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """0/1 membership: rank by score then random keys; greedy fill until area budget."""
    n = len(scores)
    chosen = np.zeros(n, dtype=bool)
    if n == 0 or target_area <= 0.0:
        return chosen
    rand = rng.random(n)
    order = np.lexsort((rand, -scores))
    cum = 0.0
    for i in order:
        if cum >= target_area - 1e-12:
            break
        chosen[i] = True
        cum += float(areas[i])
    return chosen


def hard_jaccard_area_budget_sensitivity(
    fine_ids: list[str],
    fine_scores: np.ndarray,
    fine_areas: np.ndarray,
    parent_ids: list[str],
    parent_scores: np.ndarray,
    parent_areas: np.ndarray,
    parent_of_fine: list[str],
    target_area: float,
    n_boot: int = HARD_TIE_BOOTSTRAP_DEFAULT,
    random_seed: int = 42,
) -> dict[str, float]:
    """Hard-set Jaccard over seeded random resolutions of tied ranks.

    Fine cells are allocated 0/1 under the area budget with random tie order.
    Parent reference membership is the area fraction of selected children;
    a parent is hard-hot when that fraction is ≥ 0.5. Coarse cells use the
    same area budget on aggregated scores. Reports median and 95% interval.
    """
    if n_boot <= 0 or target_area <= 0.0 or len(fine_ids) == 0 or len(parent_ids) == 0:
        return {
            "jaccard_hard_median": float("nan"),
            "jaccard_hard_ci_low": float("nan"),
            "jaccard_hard_ci_high": float("nan"),
            "n_boot": int(max(0, n_boot)),
        }

    rng = np.random.default_rng(random_seed)
    parent_index = {pid: i for i, pid in enumerate(parent_ids)}
    child_area = np.zeros(len(parent_ids), dtype=np.float64)
    for area, parent in zip(fine_areas, parent_of_fine, strict=True):
        j = parent_index.get(parent)
        if j is not None:
            child_area[j] += float(area)

    jaccards: list[float] = []
    for _ in range(int(n_boot)):
        fine_hard = _hard_mask_area_budget(fine_scores, fine_areas, target_area, rng)
        selected_child_area = np.zeros(len(parent_ids), dtype=np.float64)
        for i, parent in enumerate(parent_of_fine):
            if not fine_hard[i]:
                continue
            j = parent_index.get(parent)
            if j is not None:
                selected_child_area[j] += float(fine_areas[i])
        with np.errstate(divide="ignore", invalid="ignore"):
            frac = np.divide(
                selected_child_area,
                child_area,
                out=np.zeros_like(selected_child_area),
                where=child_area > 0,
            )
        ref_hard = {parent_ids[j] for j in range(len(parent_ids)) if frac[j] >= 0.5}
        coarse_hard_mask = _hard_mask_area_budget(parent_scores, parent_areas, target_area, rng)
        coarse_hard = {parent_ids[j] for j in range(len(parent_ids)) if coarse_hard_mask[j]}
        jaccards.append(jaccard_index(ref_hard, coarse_hard))

    arr = np.asarray(jaccards, dtype=np.float64)
    return {
        "jaccard_hard_median": float(np.median(arr)),
        "jaccard_hard_ci_low": float(np.quantile(arr, 0.025)),
        "jaccard_hard_ci_high": float(np.quantile(arr, 0.975)),
        "n_boot": int(n_boot),
    }


def canonical_ladder_heatmap(
    table: pd.DataFrame,
    value_col: str = "jaccard",
) -> pd.DataFrame:
    """Pivot the native-fine ladder to aggregation × coarse_res. No recomputation."""
    if table is None or table.empty:
        raise ValueError("canonical scale-results table is empty")
    if value_col not in table.columns:
        raise KeyError(f"canonical table missing '{value_col}'")
    work = table.copy()
    native = int(work["fine_res"].max())
    work = work.loc[work["fine_res"].astype(int) == native]
    if work.empty:
        raise ValueError("canonical table has no native-fine rows")
    pivot = work.pivot_table(
        index="aggregation",
        columns="coarse_res",
        values=value_col,
        aggfunc="first",
    )
    return pivot


def bootstrap_hotspot_topk(
    cell_ids: list[str] | np.ndarray,
    values: np.ndarray,
    k: int,
    n_boot: int = 200,
    random_seed: int = 42,
) -> dict[str, float]:
    """Bootstrap random tie-breaks; return median membership and 95% CI half-width.

    Returns dict with keys membership_median / membership_ci_low / membership_ci_high
    encoded as parallel lists via a DataFrame-friendly nested structure.
    """
    values = np.asarray(values, dtype=np.float64)
    ids = np.asarray([str(c) for c in cell_ids], dtype=object)
    rng = np.random.default_rng(random_seed)
    finite_mask = np.isfinite(values)
    ids_f = ids[finite_mask]
    vals_f = values[finite_mask]
    if k <= 0 or len(ids_f) == 0:
        return {
            "cell_ids": [],
            "membership_median": [],
            "membership_ci_low": [],
            "membership_ci_high": [],
        }
    k = min(int(k), len(ids_f))
    membership = np.zeros((n_boot, len(ids_f)), dtype=np.float64)
    # Pre-group by unique values for tie randomization
    for b in range(n_boot):
        # Rank by value desc; within ties, random permutation
        order = np.arange(len(ids_f))
        # Stable sort by value, then shuffle within ties via random keys
        rand_keys = rng.random(len(ids_f))
        # lexsort: last key is primary — we want -value primary, random secondary
        ranked = order[np.lexsort((rand_keys, -vals_f))]
        chosen = ranked[:k]
        membership[b, chosen] = 1.0
    med = np.median(membership, axis=0)
    lo = np.quantile(membership, 0.025, axis=0)
    hi = np.quantile(membership, 0.975, axis=0)
    return {
        "cell_ids": ids_f.tolist(),
        "membership_median": med.tolist(),
        "membership_ci_low": lo.tolist(),
        "membership_ci_high": hi.tolist(),
    }


def spearman_rank_corr(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation; returns NaN if undefined."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return float("nan")
    rx = pd.Series(x[mask]).rank().to_numpy()
    ry = pd.Series(y[mask]).rank().to_numpy()
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


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
                "area_m2",
            ]
        )

    work = df[[cell_col, value_col]].copy()
    work[cell_col] = work[cell_col].astype(str)
    work["parent"] = [cell_parent(c, parent_res) for c in work[cell_col]]
    work["area_m2"] = [cell_area_m2(c) for c in work[cell_col]]

    def _p90(s: pd.Series) -> float:
        return float(np.nanpercentile(s.to_numpy(dtype=np.float64), 90))

    grouped = work.groupby("parent", as_index=False).agg(
        **{
            f"{value_col}_mean": (value_col, "mean"),
            f"{value_col}_max": (value_col, "max"),
            f"{value_col}_p90": (value_col, _p90),
            "n_children": (value_col, "size"),
            "area_m2": ("area_m2", "sum"),
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


def filter_fine_to_study_domain(
    df: pd.DataFrame,
    study_domain_parents: set[str] | list[str],
    *,
    modelling_res: int = 9,
    cell_col: str = "h3_index",
) -> pd.DataFrame:
    """Keep fine cells whose H3 parent at ``modelling_res`` is in the modelling support.

    Unifies scale-loss parents(R10) with the modelling R9 set under one
    ``study_domain_mask``, removing the bbox-induced parent surplus (e.g. 296 vs 262).
    """
    parents = {str(p) for p in study_domain_parents}
    if not parents or df.empty:
        return df.copy()
    work = df.copy()
    cells = work[cell_col].astype(str)
    keep = [h3.cell_to_parent(c, modelling_res) in parents for c in cells]
    out = work.loc[keep].copy()
    out["study_domain_mask"] = True
    out["study_domain_modelling_res"] = int(modelling_res)
    return out


def resolution_ladder_topk_diagnostics(
    df: pd.DataFrame,
    value_col: str,
    resolutions: list[int] | None = None,
    hotspot_budget: float = 0.10,
    cell_col: str = "h3_index",
    n_hard_boot: int = HARD_TIE_BOOTSTRAP_DEFAULT,
    random_seed: int = 42,
    study_domain_parents: set[str] | list[str] | None = None,
    modelling_res: int = 9,
) -> pd.DataFrame:
    """
    Canonical scale-loss ladder: area-weighted parent scores, then a strict
    area budget with fractional membership at tied groups.

    Fine hotspot membership uses ``hotspot_budget * Σ a_i`` (not cell-count
    top-k). Parent reference membership is
    ``w_ref(p) = Σ_{i∈p} a_i w_i / Σ_{i∈p} a_i``. Coarse hotspots are selected
    under the same area budget on area-weighted (mean) or max/p90 parent scores.
    The primary metric ``jaccard`` is the area-weighted soft Jaccard.
    Hard-set Jaccard is a seeded tie-resolution sensitivity only.

    When ``study_domain_parents`` is provided, fine cells are restricted to those
    whose parent at ``modelling_res`` lies in that set so that the R9 coarse
    support matches the modelling table.
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

    domain_applied = False
    if study_domain_parents is not None:
        work = filter_fine_to_study_domain(
            work,
            study_domain_parents,
            modelling_res=modelling_res,
            cell_col=cell_col,
        )
        domain_applied = True
        if work.empty:
            return pd.DataFrame()

    if resolutions is None:
        lo = max(0, native_res - 3)
        resolutions = list(range(lo, native_res + 1))

    fine_ids = work[cell_col].astype(str).tolist()
    fine_scores = work[value_col].to_numpy(dtype=np.float64)
    fine_area_arr = np.asarray([cell_area_m2(c) for c in fine_ids], dtype=np.float64)
    fine_area_lookup = {cid: float(a) for cid, a in zip(fine_ids, fine_area_arr, strict=True)}
    total_fine_area = float(fine_area_arr.sum())
    target_area = float(hotspot_budget) * total_fine_area

    fine_weights, fine_thresh = hotspot_weights_area_budget(
        fine_ids, fine_scores, fine_area_arr, target_area
    )
    fine_selected_area = membership_area(fine_weights, fine_area_lookup)
    fine_area_err = (
        abs(fine_selected_area - target_area) / target_area if target_area > 0 else 0.0
    )
    if fine_area_err > 1e-4:
        raise RuntimeError(
            f"Fine area budget invariant failed: selected={fine_selected_area} "
            f"target={target_area} rel_err={fine_area_err}"
        )

    rows: list[dict] = []
    for coarse in sorted(set(int(r) for r in resolutions)):
        if coarse >= native_res:
            continue
        rolled = rollup_to_parent(work, value_col, coarse, cell_col=cell_col)
        w_ref, support_area = parent_area_weighted_membership(
            fine_ids, fine_weights, fine_area_lookup, coarse
        )
        # Area-weighted mean of fine scores (audit: parent scores first).
        tmp = pd.DataFrame(
            {
                "parent": [h3.cell_to_parent(c, coarse) for c in fine_ids],
                "score": fine_scores,
                "area": fine_area_arr,
            }
        )
        weighted = tmp["score"] * tmp["area"]
        aw_mean = weighted.groupby(tmp["parent"]).sum() / tmp.groupby("parent")["area"].sum()
        rolled = rolled.set_index("h3_index")
        rolled[f"{value_col}_mean"] = aw_mean.reindex(rolled.index)
        rolled = rolled.reset_index()

        parent_ids = rolled["h3_index"].astype(str).tolist()
        parent_areas = np.asarray(
            [float(support_area.get(p, float(a))) for p, a in zip(parent_ids, rolled["area_m2"], strict=True)],
            dtype=np.float64,
        )
        area_lookup = {p: float(a) for p, a in zip(parent_ids, parent_areas, strict=True)}
        parent_of_fine = [h3.cell_to_parent(c, coarse) for c in fine_ids]

        # Align w_ref onto every parent in the rolled support (zeros included).
        w_ref_full = {p: float(w_ref.get(p, 0.0)) for p in parent_ids}

        for agg in ("mean", "max", "p90"):
            col = f"{value_col}_{agg}"
            parent_scores = rolled[col].to_numpy(dtype=np.float64)
            coarse_weights, thresh = hotspot_weights_area_budget(
                parent_ids, parent_scores, parent_areas, target_area
            )
            coarse_selected_area = membership_area(coarse_weights, area_lookup)
            coarse_area_err = (
                abs(coarse_selected_area - target_area) / target_area if target_area > 0 else 0.0
            )
            if coarse_area_err > 1e-4:
                raise RuntimeError(
                    f"Coarse area budget invariant failed at R{coarse}/{agg}: "
                    f"selected={coarse_selected_area} target={target_area} "
                    f"rel_err={coarse_area_err}"
                )

            jac = area_weighted_soft_jaccard(w_ref_full, coarse_weights, area_lookup)
            inter = 0.0
            sum_ref = 0.0
            sum_c = 0.0
            for p, area in area_lookup.items():
                wr = float(w_ref_full.get(p, 0.0))
                wc = float(coarse_weights.get(p, 0.0))
                inter += area * min(wr, wc)
                sum_ref += area * wr
                sum_c += area * wc
            recall = float(inter / sum_ref) if sum_ref > 0 else float("nan")
            precision = float(inter / sum_c) if sum_c > 0 else float("nan")
            if np.isfinite(precision) and np.isfinite(recall) and (precision + recall) > 0:
                f1 = float(2.0 * precision * recall / (precision + recall))
            else:
                f1 = 0.0 if (sum_ref > 0 or sum_c > 0) else 1.0

            hard = hard_jaccard_area_budget_sensitivity(
                fine_ids,
                fine_scores,
                fine_area_arr,
                parent_ids,
                parent_scores,
                parent_areas,
                parent_of_fine,
                target_area,
                n_boot=n_hard_boot,
                random_seed=random_seed,
            )

            merged = rolled.set_index("h3_index")[col].to_frame().join(
                aw_mean.rename("fine_parent_mean"), how="inner"
            )
            fine_parent_vals = merged["fine_parent_mean"].to_numpy(dtype=np.float64)
            coarse_vals = merged[col].to_numpy(dtype=np.float64)
            rho = spearman_rank_corr(fine_parent_vals, coarse_vals)
            continuous_mae = float(np.mean(np.abs(fine_parent_vals - coarse_vals)))
            continuous_rmse = float(np.sqrt(np.mean((fine_parent_vals - coarse_vals) ** 2)))

            n_hot_fine = int(sum(1 for w in fine_weights.values() if w > 0))
            n_hot_ref = int(sum(1 for w in w_ref_full.values() if w > 0))
            n_hot_coarse = int(sum(1 for w in coarse_weights.values() if w > 0))

            rows.append(
                {
                    "fine_res": native_res,
                    "coarse_res": coarse,
                    "aggregation": agg,
                    "hotspot_budget": hotspot_budget,
                    "budget_match_mode": "strict_area_budget",
                    "tie_method": "fractional_membership_area",
                    "study_domain_mask": domain_applied,
                    "study_domain_modelling_res": int(modelling_res) if domain_applied else None,
                    "n_fine": int(len(work)),
                    "n_coarse": int(len(rolled)),
                    "nominal_cell_k": int(max(1, round(hotspot_budget * len(work)))),
                    "fine_hotspot_area_m2": fine_selected_area,
                    "coarse_hotspot_area_m2": coarse_selected_area,
                    "target_area_m2": target_area,
                    "area_budget_rel_err_fine": fine_area_err,
                    "area_budget_rel_err_coarse": coarse_area_err,
                    "n_hotspot_fine": n_hot_fine,
                    "n_hotspot_fine_parents": n_hot_ref,
                    "n_hotspot_coarse": n_hot_coarse,
                    "fine_hotspot_threshold": fine_thresh,
                    "coarse_hotspot_threshold": thresh,
                    "jaccard": jac,
                    "jaccard_soft": jac,
                    "jaccard_hard_median": hard["jaccard_hard_median"],
                    "jaccard_hard_ci_low": hard["jaccard_hard_ci_low"],
                    "jaccard_hard_ci_high": hard["jaccard_hard_ci_high"],
                    "jaccard_hard_n_boot": hard["n_boot"],
                    "area_weighted_overlap": jac,
                    "spearman_rank_corr": rho,
                    "continuous_mae": continuous_mae,
                    "continuous_rmse": continuous_rmse,
                    "f1": f1,
                    "fine_parent_recall": recall,
                    "coarse_precision": precision,
                    "matched_budgets_cell_count": False,
                    "primary_metric": "area_weighted_soft_jaccard",
                    "note": (
                        "max aggregation Jaccard near 1.0 can be structural "
                        "(parent collapse under max), not a preferred strategy"
                        if agg == "max"
                        else ""
                    ),
                }
            )

    return pd.DataFrame(rows)
