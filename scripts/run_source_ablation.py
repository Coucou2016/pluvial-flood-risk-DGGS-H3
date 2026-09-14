#!/usr/bin/env python
"""Source-ablation for the composite open-evidence target (reviewer M2).

The composite target ``flood_risk = max(dep_area_frac, complaint_presence,
ida_hwm_presence)`` mixes three heterogeneous sources. To test construct
validity we re-run the *same* spatial H3-block cross-validation (GBM, k=2 parent
blocks, 5 folds) against six target definitions and report discrimination
(ROC-AUC / average precision) and thresholded accuracy/F1 plus prevalence:

- ``dep_only``                 DEP stormwater polygon area fraction (categories 1-2)
- ``complaint_only``           311 crowd-report presence
- ``hwm_only``                 USGS Ida high-water-mark presence
- ``complaint_hwm``            311 OR HWM presence (observational evidence)
- ``composite``                the current max() target (baseline)
- ``composite_no_diststream``  composite target, with dist_stream_m dropped from X

The headline question is whether the observed ranking ability is dominated by a
single source (notably DEP, whose H&H model outputs share drivers with the
topographic/impervious predictors) or is reproduced across source definitions.
Single-class targets (e.g. HWM in the Lower Manhattan extent, where 0 HWM points
fall) are recorded with prevalence only and not fitted.

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

SPATIAL_CV_K = 2
SPATIAL_CV_FOLDS = 5

PILOTS = [
    ("lower_manhattan", PROCESSED_DIR / "nyc_h3_cells.parquet"),
    ("manhattan_expanded", PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"),
]


def _require_cols(df: pd.DataFrame, *cols: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"table missing source columns {missing}")


def target_variants(df: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray, str]]:
    """Return {name: (y_class, y_risk, feature_drop)} for each source definition.

    ``feature_drop`` is a column name to remove from the feature matrix ('' means
    keep all FEATURE_COLUMNS). The composite target is read from the assembled
    ``flood_class`` / ``flood_risk`` columns so it matches the primary pipeline
    exactly.
    """
    _require_cols(
        df,
        "dep_area_frac",
        "complaint_presence",
        "ida_hwm_presence",
        "flood_class",
        "flood_risk",
    )
    dep_pos = (df["dep_area_frac"].to_numpy(dtype=float) > 1e-9).astype(int)
    complaint_pos = df["complaint_presence"].to_numpy(dtype=int)
    hwm_pos = df["ida_hwm_presence"].to_numpy(dtype=int)
    complaint_hwm_pos = ((complaint_pos + hwm_pos) > 0).astype(int)

    return {
        "dep_only": (
            dep_pos,
            df["dep_area_frac"].to_numpy(dtype=float),
            "",
        ),
        "complaint_only": (
            complaint_pos,
            complaint_pos.astype(float),
            "",
        ),
        "hwm_only": (
            hwm_pos,
            hwm_pos.astype(float),
            "",
        ),
        "complaint_hwm": (
            complaint_hwm_pos,
            np.maximum(complaint_pos, hwm_pos).astype(float),
            "",
        ),
        "composite": (
            df["flood_class"].to_numpy(dtype=int),
            df["flood_risk"].to_numpy(dtype=float),
            "",
        ),
        "composite_no_diststream": (
            df["flood_class"].to_numpy(dtype=int),
            df["flood_risk"].to_numpy(dtype=float),
            "dist_stream_m",
        ),
    }


def _feature_matrix(df: pd.DataFrame, drop: str) -> np.ndarray:
    cols = [c for c in FEATURE_COLUMNS if c != drop]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"feature table missing columns {missing}")
    return df[cols].to_numpy(dtype=np.float64)


def run_one_pilot(name: str, table_path: Path) -> list[dict]:
    df = pd.read_parquet(table_path)
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, SPATIAL_CV_K)
    variants = target_variants(df)

    rows: list[dict] = []
    for target_name, (y_class, y_risk, drop) in variants.items():
        base = {
            "pilot": name,
            "target": target_name,
            "n_cells": int(len(df)),
            "n_blocks": int(len(np.unique(groups))),
            "feature_drop": drop or None,
        }
        if len(np.unique(y_class)) < 2:
            base.update(
                {
                    "n_positive": int(np.sum(y_class == 1)),
                    "prevalence": float(np.mean(y_class == 1)),
                    "roc_auc_pooled": None,
                    "roc_auc_mean": None,
                    "roc_auc_std": None,
                    "pr_auc_pooled": None,
                    "accuracy_mean": None,
                    "f1_mean": None,
                    "note": "single-class target (not fitted)",
                }
            )
            rows.append(base)
            continue

        X = _feature_matrix(df, drop)
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
                "pr_auc_pooled": _clean(m[f"ablation_{target_name}_pr_auc_pooled"]),
                "accuracy_mean": _clean(m[f"ablation_{target_name}_accuracy_mean"]),
                "accuracy_std": _clean(m[f"ablation_{target_name}_accuracy_std"]),
                "f1_mean": _clean(m[f"ablation_{target_name}_f1_mean"]),
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
            "Source-ablation (M2): same spatial H3-block CV (k=2 parent blocks, 5 folds, "
            "GBM) refit to six target definitions to test construct validity of the "
            "composite max(dep_area_frac, complaint_presence, ida_hwm_presence) target. "
            "ROC-AUC is the headline ranking-discrimination metric; accuracy/F1 are "
            "threshold-dependent. Single-class targets are not fitted."
        ),
        "spatial_cv_k": SPATIAL_CV_K,
        "spatial_cv_folds": SPATIAL_CV_FOLDS,
        "pilots": nested,
    }
    (outputs / "source_ablation.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
