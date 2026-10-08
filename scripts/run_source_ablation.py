#!/usr/bin/env python
"""Source-ablation and physics/reporting/full models for the open-evidence target.

Major Revision 2026-10-08
-------------------------
The MAIN target is now the binary union
``evidence_positive = (dep_area_frac>0) | (complaint_count>0) | (ida_hwm_count>0)``.
This script tests construct validity by re-running the *same* spatial H3-block
cross-validation (GBM, parent-resolution offset = 2 → R7 blocks, 5 folds) against
several target definitions and feature subsets:

Target definitions
- ``dep_only``        DEP stormwater polygon presence (categories 1-2)
- ``complaint_only``  311 crowd-report presence
- ``hwm_only``        USGS Ida high-water-mark presence
- ``complaint_hwm``   311 OR HWM presence (observational evidence)
- ``evidence_union``  the main binary union target (baseline)
- ``evidence_union_no_distwater``  union, with dist_mapped_water_m dropped
- ``complaint_no_building_density``  311-only, building_density dropped

Feature-subset models (P1-1), all on the main union target
- ``union_physics_only``    terrain / hydrology predictors only
- ``union_reporting_only``  exposure / reporting-opportunity predictors only
- ``union_full``            all physics + reporting predictors

The headline question is whether observed ranking ability is dominated by a
single source (notably DEP, whose H&H model outputs share drivers with the
topographic/impervious predictors) or is reproduced across source definitions.
Single-class targets are recorded with prevalence only and not fitted.

Outputs:
- outputs/source_ablation.json  (nested by pilot)
- outputs/source_ablation.csv   (long format)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import FEATURE_COLUMNS, OUTPUTS_DIR, PROCESSED_DIR  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

PARENT_RESOLUTION_OFFSET = 2
SPATIAL_CV_FOLDS = 5

# P1-1: split the production feature set into physics vs reporting/exposure.
PHYSICS_FEATURES = ["elevation_m", "slope_deg", "dem_d8_accum_proxy", "dist_mapped_water_m"]
REPORTING_FEATURES = ["impervious_frac", "building_density", "building_area_fraction"]

PILOTS = [
    ("lower_manhattan", PROCESSED_DIR / "nyc_h3_cells.parquet"),
    ("manhattan_expanded", PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"),
]


def _require_cols(df: pd.DataFrame, *cols: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"table missing source columns {missing}")


def target_variants(
    df: pd.DataFrame,
) -> dict[str, tuple[np.ndarray, np.ndarray, list[str] | None]]:
    """Return {name: (y_class, y_risk, feature_columns_or_None)}.

    ``feature_columns_or_None`` is a subset of ``FEATURE_COLUMNS`` (``None`` keeps
    all). The union target is read from the assembled ``evidence_positive`` /
    ``evidence_score`` columns so it matches the primary pipeline exactly.
    """
    _require_cols(
        df,
        "dep_area_frac",
        "complaint_presence",
        "ida_hwm_presence",
        "evidence_positive",
        "evidence_score",
    )
    dep_pos = (df["dep_area_frac"].to_numpy(dtype=float) > 1e-9).astype(int)
    complaint_pos = df["complaint_count"].to_numpy(dtype=int)
    complaint_pos = (complaint_pos > 0).astype(int) if "complaint_count" in df.columns else df[
        "complaint_presence"
    ].to_numpy(dtype=int)
    hwm_pos = df["ida_hwm_presence"].to_numpy(dtype=int)
    complaint_hwm_pos = ((complaint_pos + hwm_pos) > 0).astype(int)
    union_class = df["evidence_positive"].to_numpy(dtype=int)
    union_score = df["evidence_score"].to_numpy(dtype=float)

    physics = [c for c in PHYSICS_FEATURES if c in FEATURE_COLUMNS]
    reporting = [c for c in REPORTING_FEATURES if c in FEATURE_COLUMNS]

    return {
        "dep_only": (dep_pos, df["dep_area_frac"].to_numpy(dtype=float), None),
        "complaint_only": (complaint_pos, complaint_pos.astype(float), None),
        "hwm_only": (hwm_pos, hwm_pos.astype(float), None),
        "complaint_hwm": (complaint_hwm_pos, np.maximum(complaint_pos, hwm_pos).astype(float), None),
        "evidence_union": (union_class, union_score, None),
        "evidence_union_no_distwater": (
            union_class,
            union_score,
            [c for c in FEATURE_COLUMNS if c != "dist_mapped_water_m"],
        ),
        "complaint_no_building_density": (
            complaint_pos,
            complaint_pos.astype(float),
            [c for c in FEATURE_COLUMNS if c != "building_density"],
        ),
        # P1-1 physics / reporting / full feature-subset models on the union target.
        "union_physics_only": (union_class, union_score, physics),
        "union_reporting_only": (union_class, union_score, reporting),
        "union_full": (union_class, union_score, list(FEATURE_COLUMNS)),
    }


def _feature_matrix(df: pd.DataFrame, cols: list[str] | None) -> np.ndarray:
    use = list(FEATURE_COLUMNS) if cols is None else list(cols)
    missing = [c for c in use if c not in df.columns]
    if missing:
        raise KeyError(f"feature table missing columns {missing}")
    return df[use].to_numpy(dtype=np.float64)


def run_one_pilot(name: str, table_path: Path) -> list[dict]:
    df = pd.read_parquet(table_path)
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, PARENT_RESOLUTION_OFFSET)
    variants = target_variants(df)

    rows: list[dict] = []
    for target_name, (y_class, y_risk, cols) in variants.items():
        base = {
            "pilot": name,
            "target": target_name,
            "n_cells": int(len(df)),
            "n_blocks": int(len(np.unique(groups))),
            "feature_subset": ",".join(cols) if cols is not None else "all",
        }
        if len(np.unique(y_class)) < 2:
            base.update(
                {
                    "n_positive": int(np.sum(y_class == 1)),
                    "prevalence": float(np.mean(y_class == 1)),
                    "roc_auc_pooled": None,
                    "roc_auc_mean": None,
                    "roc_auc_std": None,
                    "average_precision_pooled": None,
                    "accuracy_mean": None,
                    "f1_mean": None,
                    "note": "single-class target (not fitted)",
                }
            )
            rows.append(base)
            continue

        X = _feature_matrix(df, cols)
        m = spatial_block_cv_metrics(
            X,
            y_class,
            y_risk,
            groups,
            n_splits=SPATIAL_CV_FOLDS,
            metric_prefix=f"ablation_{target_name}",
            cells=cells,
        )
        base.update(
            {
                "n_positive": int(np.sum(y_class == 1)),
                "prevalence": float(np.mean(y_class == 1)),
                "roc_auc_pooled": _clean(m[f"ablation_{target_name}_roc_auc_pooled"]),
                "roc_auc_mean": _clean(m[f"ablation_{target_name}_roc_auc_mean"]),
                "roc_auc_std": _clean(m[f"ablation_{target_name}_roc_auc_std"]),
                "average_precision_pooled": _clean(
                    m[f"ablation_{target_name}_average_precision_pooled"]
                ),
                "pr_auc_pooled": _clean(m[f"ablation_{target_name}_pr_auc_pooled"]),
                "accuracy_mean": _clean(m[f"ablation_{target_name}_accuracy_mean"]),
                "accuracy_std": _clean(m[f"ablation_{target_name}_accuracy_std"]),
                "f1_mean": _clean(m[f"ablation_{target_name}_f1_mean"]),
                "roc_auc_ci_low": _clean(m[f"ablation_{target_name}_roc_auc_ci_low"]),
                "roc_auc_ci_high": _clean(m[f"ablation_{target_name}_roc_auc_ci_high"]),
                "note": "",
            }
        )
        rows.append(base)
    return rows


def _clean(v: float | None) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if not np.isfinite(f) else f


def main() -> None:
    all_rows: list[dict] = []
    for name, path in PILOTS:
        if not path.exists():
            print(f"SKIP {name}: {path} not found", file=sys.stderr)
            continue
        all_rows.extend(run_one_pilot(name, path))

    tab = pd.DataFrame(all_rows)
    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    tab.to_csv(outputs / "source_ablation.csv", index=False)

    nested: dict[str, list[dict]] = {}
    for name, _ in PILOTS:
        nested[name] = [
            {k: v for k, v in r.items() if k != "pilot"} for r in all_rows if r["pilot"] == name
        ]
    payload = {
        "note": (
            "Source-ablation (M2): same spatial H3-block CV (parent-resolution offset = 2 "
            "→ R7 blocks, 5 folds, GBM) refit to multiple target definitions and feature "
            "subsets to test construct validity of the binary union evidence target "
            "((dep_area_frac>0)|(complaint>0)|(hwm>0)); includes physics-only vs "
            "reporting-only vs full models (P1-1). ROC-AUC is the headline "
            "ranking-discrimination metric; accuracy/F1 are threshold-dependent. "
            "Single-class targets are not fitted."
        ),
        "parent_resolution_offset": PARENT_RESOLUTION_OFFSET,
        "spatial_cv_k": PARENT_RESOLUTION_OFFSET,
        "spatial_cv_folds": SPATIAL_CV_FOLDS,
        "physics_features": [c for c in PHYSICS_FEATURES if c in FEATURE_COLUMNS],
        "reporting_features": [c for c in REPORTING_FEATURES if c in FEATURE_COLUMNS],
        "pilots": nested,
    }
    (outputs / "source_ablation.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
