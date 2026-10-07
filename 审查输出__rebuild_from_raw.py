"""Rebuild audit tables from current raw files without touching project outputs."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.assemble import (  # noqa: E402
    assemble_h3_table,
    assemble_label_scale_table,
    sources_from_config,
)
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox  # noqa: E402
from pluvial_flood_risk.h3_grid import bbox_to_cells  # noqa: E402

OUT = ROOT / "审查输出" / "evidence" / "raw_rebuild_evidence.json"


def compare_frames(actual: pd.DataFrame, expected: pd.DataFrame) -> dict:
    a = actual.sort_values("h3_index").reset_index(drop=True)
    e = expected.sort_values("h3_index").reset_index(drop=True)
    common = sorted(set(a.columns) & set(e.columns))
    numeric = [c for c in common if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(e[c])]
    text = [c for c in common if c not in numeric]
    numeric_max_abs = {}
    numeric_mismatch = {}
    for c in numeric:
        av = a[c].to_numpy(float)
        ev = e[c].to_numpy(float)
        valid = np.isfinite(av) & np.isfinite(ev)
        diff = np.abs(av[valid] - ev[valid]) if valid.any() else np.array([], dtype=float)
        numeric_max_abs[c] = float(diff.max()) if diff.size else 0.0
        numeric_mismatch[c] = int((~np.isclose(av, ev, rtol=1e-12, atol=1e-12, equal_nan=True)).sum())
    text_mismatch = {
        c: int((a[c].fillna("<NA>").astype(str) != e[c].fillna("<NA>").astype(str)).sum())
        for c in text
    }
    return {
        "actual_rows": len(a),
        "expected_rows": len(e),
        "same_h3_set": set(a["h3_index"].astype(str)) == set(e["h3_index"].astype(str)),
        "actual_only_columns": sorted(set(a.columns) - set(e.columns)),
        "expected_only_columns": sorted(set(e.columns) - set(a.columns)),
        "numeric_max_abs_diff": numeric_max_abs,
        "numeric_mismatch_count_at_1e_12": numeric_mismatch,
        "text_mismatch_count": text_mismatch,
        "total_numeric_mismatches": int(sum(numeric_mismatch.values())),
        "total_text_mismatches": int(sum(text_mismatch.values())),
        "actual_null_counts": {c: int(v) for c, v in a.isna().sum().items() if int(v)},
        "all_values_match": bool(
            len(a) == len(e)
            and set(a["h3_index"].astype(str)) == set(e["h3_index"].astype(str))
            and not set(a.columns).symmetric_difference(e.columns)
            and sum(numeric_mismatch.values()) == 0
            and sum(text_mismatch.values()) == 0
        ),
    }


def expanded_sources(cfg: dict):
    raw_dir = ROOT / "data" / "raw" / "nyc_expanded"
    cfg = dict(cfg)
    cfg["paths"] = dict(cfg.get("paths") or {})
    cfg["paths"]["raw_dir"] = raw_dir
    for key in (
        "dem", "slope", "impervious", "buildings", "hydro",
        "flood_polygons", "flood_points", "coastal", "sandy",
        "event_rainfall", "floodnet",
    ):
        cfg["paths"].pop(key, None)
    cfg["assembly_mode"] = "opendata"
    return cfg, sources_from_config(cfg)


def main() -> None:
    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    resolution = int(cfg.get("resolution", 9))
    rainfall = float(cfg.get("rainfall_mm_h", 40.0))
    result = {
        "claimed_lower_manhattan_bbox_in_manuscript": [-74.02, 40.70, -73.97, 40.76],
        "configured_smoke_bbox_used_by_nyc_smoke_test": list(resolve_bbox(cfg, "smoke")),
        "configured_lower_manhattan_bbox": list(resolve_bbox(cfg, "lower_manhattan")),
        "h3_cell_counts": {
            "smoke_bbox_r9": len(bbox_to_cells(*resolve_bbox(cfg, "smoke"), resolution)),
            "lower_manhattan_bbox_r9": len(bbox_to_cells(*resolve_bbox(cfg, "lower_manhattan"), resolution)),
            "expanded_bbox_r9": len(bbox_to_cells(*resolve_bbox(cfg, "manhattan_expanded"), resolution)),
        },
    }

    t0 = time.perf_counter()
    lm = assemble_h3_table(
        resolve_bbox(cfg, "smoke"),
        resolution,
        rainfall_mm_h=rainfall,
        sources=sources_from_config(cfg),
        fallback_synthetic=False,
    )
    result["lower_manhattan_rebuild_seconds"] = time.perf_counter() - t0
    result["lower_manhattan"] = compare_frames(
        lm, pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells.parquet")
    )

    t1 = time.perf_counter()
    cfg_exp, src_exp = expanded_sources(cfg)
    expanded = assemble_h3_table(
        resolve_bbox(cfg_exp, "manhattan_expanded"),
        resolution,
        rainfall_mm_h=rainfall,
        sources=src_exp,
        fallback_synthetic=False,
    )
    result["expanded_rebuild_seconds"] = time.perf_counter() - t1
    result["expanded"] = compare_frames(
        expanded, pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells_expanded.parquet")
    )

    t2 = time.perf_counter()
    r10 = assemble_label_scale_table(
        resolve_bbox(cfg, "smoke"), 10, sources=sources_from_config(cfg)
    )
    result["r10_rebuild_seconds"] = time.perf_counter() - t2
    result["r10_labels"] = compare_frames(
        r10, pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells_r10_labels.parquet")
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
