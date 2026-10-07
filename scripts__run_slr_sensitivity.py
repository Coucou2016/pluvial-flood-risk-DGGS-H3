#!/usr/bin/env python
"""Sea-level sensitivity for the DEP stormwater target (reviewer M4).

The primary target uses the DEP "Moderate Flood with Current Sea Levels" layer
(Layer 1). This script re-assembles the target with the "Moderate Flood with
2050 Sea Level Rise" layer (Layer 2, same Flooding_Category 1-2 filtering) and
reports the change in target prevalence and in spatial H3-block CV ranking
discrimination (ROC-AUC / AP) versus the current-sea-level primary.

Both DEP variants are hydrologic/hydraulic model outputs; the comparison is a
data-semantics sensitivity, not an observation-based validation.

Outputs:
- outputs/slr_sensitivity.json  (nested by pilot)
- outputs/slr_sensitivity.csv   (long format)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import FEATURE_COLUMNS, OUTPUTS_DIR  # noqa: E402
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox  # noqa: E402
from pluvial_flood_risk.assemble import assemble_h3_table, sources_from_config  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

SPATIAL_CV_K = 2
SPATIAL_CV_FOLDS = 5

# (pilot name, bbox profile, raw_dir)
PILOTS = [
    ("lower_manhattan", "lower_manhattan", ROOT / "data" / "raw" / "nyc"),
    ("manhattan_expanded", "manhattan_expanded", ROOT / "data" / "raw" / "nyc_expanded"),
]


def _feature_matrix(df: pd.DataFrame) -> np.ndarray:
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"feature table missing columns {missing}")
    return df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)


def _clean(v: float | None) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if not np.isfinite(f) else f


def _assemble_and_score(cfg: dict, bbox: list, resolution: int, rainfall: float, sources) -> dict:
    df = assemble_h3_table(
        bbox, resolution, rainfall_mm_h=rainfall, sources=sources, fallback_synthetic=False
    )
    y_class = df["flood_class"].to_numpy(dtype=int)
    y_risk = df["flood_risk"].to_numpy(dtype=float)
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, SPATIAL_CV_K)

    base = {
        "n_cells": int(len(df)),
        "n_positive": int(np.sum(y_class == 1)),
        "prevalence": float(np.mean(y_class == 1)),
        "dep_area_frac_sum": float(df["dep_area_frac"].sum()) if "dep_area_frac" in df else None,
        "n_dep_cells": int((df["dep_area_frac"] > 1e-9).sum()) if "dep_area_frac" in df else None,
    }
    if len(np.unique(y_class)) < 2:
        base.update({k: None for k in (
            "roc_auc_pooled", "roc_auc_mean", "pr_auc_pooled",
            "accuracy_mean", "f1_mean", "r2_mean",
        )})
        base["note"] = "single-class target (not fitted)"
        return base

    X = _feature_matrix(df)
    m = spatial_block_cv_metrics(
        X, y_class, y_risk, groups, n_splits=SPATIAL_CV_FOLDS,
        metric_prefix="slr", cells=cells,
    )
    base.update({
        "roc_auc_pooled": _clean(m.get("slr_roc_auc_pooled")),
        "roc_auc_mean": _clean(m.get("slr_roc_auc_mean")),
        "pr_auc_pooled": _clean(m.get("slr_pr_auc_pooled")),
        "accuracy_mean": _clean(m.get("slr_accuracy_mean")),
        "f1_mean": _clean(m.get("slr_f1_mean")),
        "r2_mean": _clean(m.get("slr_r2_mean")),
        "note": "",
    })
    return base


def main() -> None:
    config_path = ROOT / "configs" / "nyc.yaml"
    cfg = load_study_config(config_path)
    resolution = int(cfg.get("resolution", 9))
    rainfall = float(cfg.get("rainfall_mm_h", 40.0))

    all_rows: list[dict] = []
    for pilot_name, profile, raw_dir in PILOTS:
        bbox = resolve_bbox(cfg, profile)
        cfg["paths"] = dict(cfg.get("paths") or {})
        cfg["paths"]["raw_dir"] = str(raw_dir)
        # Drop Lower-Manhattan hardcoded paths so discover_sources resolves the
        # raw_dir's own conventional filenames (same as run_expanded_study.py).
        for key in ("dem", "slope", "impervious", "buildings", "hydro",
                    "flood_polygons", "flood_points", "coastal", "sandy",
                    "event_rainfall", "floodnet"):
            cfg["paths"].pop(key, None)
        cfg["assembly_mode"] = "opendata"

        primary_sources = sources_from_config(cfg)
        slr_sources = sources_from_config(cfg)
        slr_sources.flood_polygons_path = raw_dir / "dep_stormwater_flood_2050slr.geojson"

        for variant, sources in (("current_sea_level", primary_sources), ("2050_slr", slr_sources)):
            row = _assemble_and_score(cfg, bbox, resolution, rainfall, sources)
            row["pilot"] = pilot_name
            row["dep_variant"] = variant
            all_rows.append(row)
            print(f"[{pilot_name}/{variant}] n={row['n_cells']} "
                  f"prevalence={row['prevalence']:.4f} "
                  f"roc_auc_pooled={row.get('roc_auc_pooled')}", file=sys.stderr)

    tab = pd.DataFrame(all_rows)
    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    tab.to_csv(outputs / "slr_sensitivity.csv", index=False)

    nested: dict[str, list[dict]] = {}
    for pilot_name, _, _ in PILOTS:
        nested[pilot_name] = [
            {k: v for k, v in r.items() if k != "pilot"}
            for r in all_rows if r["pilot"] == pilot_name
        ]
    payload = {
        "note": (
            "Sea-level sensitivity (M4): the composite target is re-assembled with the "
            "DEP 'Moderate Flood with 2050 Sea Level Rise' layer (Layer 2, same "
            "Flooding_Category 1-2 filtering) and compared against the current-sea-level "
            "primary (Layer 1) under the same spatial H3-block CV (k=2 parent blocks, 5 "
            "folds, GBM). Both DEP variants are H&H model outputs."
        ),
        "spatial_cv_k": SPATIAL_CV_K,
        "spatial_cv_folds": SPATIAL_CV_FOLDS,
        "pilots": nested,
    }
    (outputs / "slr_sensitivity.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
