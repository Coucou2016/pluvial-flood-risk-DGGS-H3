#!/usr/bin/env python
"""Sandy-window 311 exclusion sensitivity (negative-control companion).

Re-aggregates NYC 311 street-flooding complaints after excluding records with
``created_date`` in [2012-10-27, 2012-11-05] (Sandy landfall window), rebuilds
the composite open-evidence target on the Lower Manhattan Option B table, and
reports:
  1. label-shift counts (how many cells flip)
  2. spatial-block CV metrics on the Sandy-excluded composite
  3. coastal-confounding diagnostic using existing OOF model scores vs the
     Sandy-excluded pluvial grouping (score column remains OOF, never target)

Outputs: outputs/sandy_311_window_sensitivity.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import OUTPUTS_DIR, PROCESSED_DIR  # noqa: E402
from pluvial_flood_risk.features import feature_matrix  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402

WINDOW_START = datetime(2012, 10, 27)
WINDOW_END = datetime(2012, 11, 5, 23, 59, 59)
GEOJSON = ROOT / "data" / "raw" / "nyc" / "flooding_311.geojson"
TABLE = PROCESSED_DIR / "nyc_h3_cells.parquet"
OOF = ROOT / "models" / "nyc_smoke" / "spatial_cv_oof_predictions.csv"
SPATIAL_CV_K = 2
SPATIAL_CV_FOLDS = 5


def _parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    text = str(raw).replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            continue
    return None


def complaint_presence_excluding_window(
    geojson_path: Path,
    cells: list[str],
    resolution: int = 9,
) -> tuple[np.ndarray, dict]:
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    cell_set = set(cells)
    counts = {c: 0 for c in cells}
    n_total = 0
    n_excluded = 0
    n_kept = 0
    for feat in payload.get("features", []):
        n_total += 1
        props = feat.get("properties") or {}
        created = _parse_date(props.get("created_date", ""))
        if created is not None and WINDOW_START <= created <= WINDOW_END:
            n_excluded += 1
            continue
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        try:
            cell = h3.latlng_to_cell(lat, lon, resolution)
        except Exception:
            continue
        if cell in cell_set:
            counts[cell] += 1
            n_kept += 1
    presence = np.array([1 if counts[c] > 0 else 0 for c in cells], dtype=int)
    meta = {
        "n_311_features_total": n_total,
        "n_311_excluded_sandy_window": n_excluded,
        "n_311_kept_in_study_cells": n_kept,
        "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
    }
    return presence, meta


def coastal_groups(df: pd.DataFrame, flood_class: np.ndarray) -> pd.DataFrame:
    sandy = (df["sandy_area_frac"].to_numpy(dtype=float) > 1e-9).astype(int)
    pluvial = flood_class.astype(int)
    return pd.DataFrame(
        {
            "h3_index": df["h3_index"].astype(str),
            "coastal": sandy,
            "pluvial": pluvial,
            "group": np.where(
                (sandy == 1) & (pluvial == 1),
                "both",
                np.where(
                    (sandy == 1) & (pluvial == 0),
                    "coastal_only",
                    np.where((sandy == 0) & (pluvial == 1), "pluvial_only", "neither"),
                ),
            ),
        }
    )


def main() -> None:
    if not TABLE.exists() or not GEOJSON.exists():
        raise SystemExit(f"missing inputs: {TABLE.exists()=} {GEOJSON.exists()=}")

    df = pd.read_parquet(TABLE)
    cells = df["h3_index"].astype(str).tolist()
    complaint_excl, meta311 = complaint_presence_excluding_window(GEOJSON, cells)

    dep = df["dep_area_frac"].to_numpy(dtype=float)
    hwm = df["ida_hwm_presence"].to_numpy(dtype=int)
    flood_risk = np.maximum.reduce(
        [dep, complaint_excl.astype(float), hwm.astype(float)]
    )
    flood_class = (flood_risk > 1e-9).astype(int)

    baseline_class = df["flood_class"].to_numpy(dtype=int)
    flipped = int(np.sum(baseline_class != flood_class))
    n_pos_base = int(baseline_class.sum())
    n_pos_excl = int(flood_class.sum())

    X = feature_matrix(df)
    groups = block_ids_for_cells(cells, SPATIAL_CV_K)
    m = spatial_block_cv_metrics(
        X,
        flood_class,
        flood_risk,
        groups,
        n_splits=SPATIAL_CV_FOLDS,
        metric_prefix="sandy311excl",
        cells=cells,
    )

    # Coastal diagnostic with *existing* OOF scores (never target score).
    oof = pd.read_csv(OOF)
    groups_df = coastal_groups(df, flood_class).merge(
        oof[["h3_index", "y_proba"]], on="h3_index", how="left"
    )
    means = groups_df.groupby("group")["y_proba"].mean().to_dict()
    pluvial_minus_coastal = float(
        means.get("pluvial_only", float("nan")) - means.get("coastal_only", float("nan"))
    )

    payload = {
        "note": (
            "311 complaints with created_date in the Sandy landfall window "
            "[2012-10-27, 2012-11-05] are excluded before rebuilding the composite "
            "max(dep, complaint, hwm) target. Coastal diagnostic still uses OOF "
            "model scores from the primary (unmodified) CV, never the target score."
        ),
        "pilot": "lower_manhattan",
        "n_cells": int(len(df)),
        "311_meta": meta311,
        "label_shift": {
            "n_positive_baseline": n_pos_base,
            "n_positive_sandy311_excluded": n_pos_excl,
            "n_cells_flipped": flipped,
            "prevalence_baseline": float(n_pos_base / len(df)),
            "prevalence_sandy311_excluded": float(n_pos_excl / len(df)),
        },
        "spatial_cv_sandy311_excluded": {
            "roc_auc_pooled": m["sandy311excl_roc_auc_pooled"],
            "roc_auc_mean": m["sandy311excl_roc_auc_mean"],
            "pr_auc_pooled": m["sandy311excl_pr_auc_pooled"],
            "accuracy_mean": m["sandy311excl_accuracy_mean"],
            "f1_mean": m["sandy311excl_f1_mean"],
        },
        "coastal_diagnostic_oof_vs_excluded_labels": {
            "score_col": "oof_model_score",
            "mean_score_by_group": {k: float(v) for k, v in means.items()},
            "pluvial_minus_coastal_mean_score": pluvial_minus_coastal,
            "n_by_group": groups_df["group"].value_counts().to_dict(),
        },
    }

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / "sandy_311_window_sensitivity.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
