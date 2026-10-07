#!/usr/bin/env python
"""Adaptive Option A: re-extract R11 features+scores on refined cells; hotspot retention.

Cells outside DEM/impervious coverage (NaN static features) are dropped and counted.
Writes:
- outputs/adaptive_r11_hotspot_retention.json
- updates outputs/adaptive_vs_fixed_ablation.csv with live post-retrain counts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.adaptive import (  # noqa: E402
    cell_covered_by_index,
    children_of_parents,
    run_adaptive_refinement,
    select_parents_to_refine,
    uncertainty_from_probability,
)
from pluvial_flood_risk.assemble import sources_from_config  # noqa: E402
from pluvial_flood_risk.config import (  # noqa: E402
    FEATURE_COLUMNS,
    MODELS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
)
from pluvial_flood_risk.config_loader import load_study_config  # noqa: E402
from pluvial_flood_risk.features import (  # noqa: E402
    building_density_from_vector,
    dist_stream_from_vector,
    feature_matrix,
)
from pluvial_flood_risk.model import ROLE_DEPLOYMENT, load_models, predict  # noqa: E402
from pluvial_flood_risk.raster import (  # noqa: E402
    merge_raster_feature,
    zonal_flow_accum_from_dem,
    zonal_mean_raster_to_h3,
    zonal_slope_deg_from_dem,
)
from pluvial_flood_risk.rollups import hotspot_ids  # noqa: E402

TABLE = PROCESSED_DIR / "nyc_h3_cells.parquet"
MODEL_DIR = MODELS_DIR / "nyc_smoke"
CFG = PROJECT_ROOT / "configs" / "nyc.yaml"


def assemble_features_drop_nan(cells: list[str], rainfall: float, sources) -> tuple[pd.DataFrame, int]:
    """Assemble observed features (mirrors production assemble); drop NaN static rows."""
    n = len(cells)
    data: dict[str, object] = {"h3_index": cells}
    for col in FEATURE_COLUMNS:
        if col == "rainfall_mm_h":
            data[col] = np.full(n, rainfall, dtype=np.float64)
        else:
            data[col] = np.full(n, np.nan, dtype=np.float64)
    df = pd.DataFrame(data)

    if sources.dem_path and Path(sources.dem_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.dem_path)
        df = merge_raster_feature(df, zonal, "elevation_m")
        if not (sources.slope_path and Path(sources.slope_path).exists()):
            try:
                slope = zonal_slope_deg_from_dem(cells, sources.dem_path)
                df = df.drop(columns=["slope_deg"], errors="ignore")
                df = df.merge(slope, on="h3_index", how="left")
            except Exception:
                pass
        try:
            flow = zonal_flow_accum_from_dem(cells, sources.dem_path)
            df = df.drop(columns=["flow_accum_proxy"], errors="ignore")
            df = df.merge(flow, on="h3_index", how="left")
        except Exception:
            pass

    if sources.slope_path and Path(sources.slope_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.slope_path)
        df = merge_raster_feature(df, zonal, "slope_deg")

    if sources.impervious_path and Path(sources.impervious_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.impervious_path)
        df = merge_raster_feature(df, zonal, "impervious_frac")

    if sources.buildings_path and Path(sources.buildings_path).exists():
        bldg = building_density_from_vector(cells, sources.buildings_path)
        df = df.drop(columns=["building_density"], errors="ignore")
        df = df.merge(bldg[["h3_index", "building_density"]], on="h3_index", how="left")
        # Building density of 0 is valid (no buildings); fill remaining NaN with 0
        df["building_density"] = df["building_density"].fillna(0.0)

    if sources.hydro_path and Path(sources.hydro_path).exists():
        dist = dist_stream_from_vector(cells, sources.hydro_path)
        df = df.drop(columns=["dist_stream_m"], errors="ignore")
        df = df.merge(dist, on="h3_index", how="left")

    static = [c for c in FEATURE_COLUMNS if c != "rainfall_mm_h"]
    ok = df[static].notna().all(axis=1)
    n_dropped = int((~ok).sum())
    return df.loc[ok].reset_index(drop=True), n_dropped


def main() -> None:
    cfg = load_study_config(CFG)
    adaptive_cfg = cfg.get("adaptive") or {}
    fine_res = int(adaptive_cfg.get("fine_res", 11))
    score_q = float(adaptive_cfg.get("risk_quantile", 0.8))
    u_min = float(adaptive_cfg.get("uncertainty_min", 0.7))
    expand_k = int(adaptive_cfg.get("expand_neighbors", 1))
    hotspot_q = float((cfg.get("diagnostics") or {}).get("hotspot_quantile", 0.9))
    rainfall = float(cfg.get("rainfall_mm_h", 40.0))

    coarse = pd.read_parquet(TABLE)
    clf, reg, _ = load_models(MODEL_DIR, expected_role=ROLE_DEPLOYMENT)
    Xc = feature_matrix(coarse)
    risk, proba, _ = predict(clf, reg, Xc)
    coarse = coarse.copy()
    coarse["predicted_risk"] = risk
    coarse["flood_probability"] = proba
    coarse["PFI_h"] = risk

    mixed, base_metrics = run_adaptive_refinement(
        coarse,
        fine_res=fine_res,
        score_col="PFI_h",
        proba_col="flood_probability",
        score_quantile=score_q,
        uncertainty_min=u_min,
        expand_k=expand_k,
    )

    parents = select_parents_to_refine(
        coarse["h3_index"].astype(str).tolist(),
        coarse["PFI_h"].to_numpy(dtype=float),
        score_quantile=score_q,
        uncertainty=uncertainty_from_probability(proba),
        uncertainty_min=u_min,
        expand_k=expand_k,
    )
    fine_children = children_of_parents(parents, fine_res)
    all_fine = children_of_parents(coarse["h3_index"].astype(str).tolist(), fine_res)
    sources = sources_from_config(cfg)

    print(f"Assembling refined R{fine_res} children: n={len(fine_children)} ...", flush=True)
    fine_df, n_drop_ref = assemble_features_drop_nan(fine_children, rainfall, sources)
    print(f"Refined scorable={len(fine_df)} dropped={n_drop_ref}", flush=True)
    Xf = feature_matrix(fine_df)
    fine_risk, fine_proba, _ = predict(clf, reg, Xf)
    fine_df["predicted_risk"] = fine_risk
    fine_df["flood_probability"] = fine_proba

    print(f"Assembling uniform R{fine_res} grid: n={len(all_fine)} ...", flush=True)
    uni_df, n_drop_uni = assemble_features_drop_nan(all_fine, rainfall, sources)
    print(f"Uniform scorable={len(uni_df)} dropped={n_drop_uni}", flush=True)
    Xu = feature_matrix(uni_df)
    uni_risk, _, _ = predict(clf, reg, Xu)
    uni_df["predicted_risk"] = uni_risk

    hot, _ = hotspot_ids(
        uni_df["h3_index"].astype(str).tolist(),
        uni_df["predicted_risk"].to_numpy(dtype=float),
        quantile=hotspot_q,
    )
    mixed_set = set(mixed)
    recalled = sum(1 for c in hot if cell_covered_by_index(c, mixed_set))
    n_hot = max(len(hot), 1)

    retention = {
        "mode": "option_A_true_r11_reextract",
        "fine_res": fine_res,
        "n_coarse": int(len(coarse)),
        "n_parents_refined": int(len(parents)),
        "n_adaptive_mixed": int(len(mixed)),
        "n_uniform_fine": int(len(all_fine)),
        "n_uniform_fine_scorable": int(len(uni_df)),
        "n_refined_children": int(len(fine_children)),
        "n_refined_children_scorable": int(len(fine_df)),
        "n_dropped_refined_nan": int(n_drop_ref),
        "n_dropped_uniform_nan": int(n_drop_uni),
        "cell_count_ratio_vs_uniform": float(len(mixed) / len(all_fine)) if all_fine else None,
        "n_hotspot_uniform_scorable": int(len(hot)),
        "hotspot_recall": float(recalled / n_hot),
        "hotspot_quantile": hotspot_q,
        "mean_score_refined_children": float(np.mean(fine_risk)) if len(fine_risk) else None,
        "mean_score_uniform_fine": float(np.mean(uni_risk)) if len(uni_risk) else None,
        "base_adaptive_metrics": base_metrics,
        "note": (
            "True R11 feature re-extraction on refined parents' children using the "
            "post-urban-drop deployment model; cells with NaN static features (DEM edge) "
            "are dropped before scoring. Hotspot recall vs uniformly scored scorable R11."
        ),
    }

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "adaptive_r11_hotspot_retention.json").write_text(
        json.dumps(retention, indent=2, default=str), encoding="utf-8"
    )

    ablation = pd.DataFrame(
        [
            {
                "ablation": "adaptive_vs_fixed_h3",
                "n_fixed_coarse": int(len(coarse)),
                "n_adaptive_mixed": int(len(mixed)),
                "cell_count_ratio_vs_fixed": float(len(mixed) / len(coarse)),
                "adaptive_n_uniform_fine": float(len(all_fine)),
                "adaptive_cell_count_ratio": float(len(mixed) / len(all_fine)) if all_fine else None,
                "adaptive_hotspot_recall": float(recalled / n_hot),
                "adaptive_n_hotspot_uniform": float(len(hot)),
                "note": retention["note"],
            }
        ]
    )
    ablation.to_csv(OUTPUTS_DIR / "adaptive_vs_fixed_ablation.csv", index=False)
    print(json.dumps(retention, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
