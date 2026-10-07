#!/usr/bin/env python
"""Hotspot budget sensitivity with exact-top-k ranking (reviewer M3).

The paper's scale-loss ladder previously used a 0.9 quantile threshold, which,
because many fine evidence scores are tied at their maximum, selected 15% of
cells instead of a nominal top 10%. A single Jaccard also conflates aggregation
smoothing, many-to-one parent collapse, and re-thresholding on the coarse grid.

This script re-derives the ladder with exact-top-k hotspots (k = round(budget *
n), tie-broken by H3 index) at 5/10/15/20% spatial budgets, on the natively
assembled R10 label table, and reports Jaccard, F1, fine-hotspot-parent recall,
and coarse-hotspot precision separately for the mean/max/p90 aggregation rules.

Outputs:
- outputs/hotspot_budget_sensitivity.csv
- outputs/hotspot_budget_sensitivity.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import OUTPUTS_DIR, PROCESSED_DIR  # noqa: E402
from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics  # noqa: E402

BUDGETS = [0.05, 0.10, 0.15, 0.20]
TABLE_PATH = PROCESSED_DIR / "nyc_h3_cells_r10_labels.parquet"
# Coarser ladder rungs to compare against the native R10 fine grid.
RESOLUTIONS = [8, 9]


def _resolve_value_col(df: pd.DataFrame) -> str:
    for c in ("flood_risk", "predicted_risk", "PFI_h"):
        if c in df.columns:
            return c
    raise KeyError("no value column (tried flood_risk, predicted_risk, PFI_h)")


def main() -> None:
    if not TABLE_PATH.exists():
        print(f"ERROR: {TABLE_PATH} not found; run the smoke pipeline first.", file=sys.stderr)
        raise SystemExit(2)

    df = pd.read_parquet(TABLE_PATH)
    value_col = _resolve_value_col(df)

    frames: list[pd.DataFrame] = []
    for budget in BUDGETS:
        tab = resolution_ladder_topk_diagnostics(
            df,
            value_col=value_col,
            resolutions=RESOLUTIONS,
            hotspot_budget=budget,
        )
        frames.append(tab)

    out = pd.concat(frames, ignore_index=True)
    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    out.to_csv(outputs / "hotspot_budget_sensitivity.csv", index=False)

    # Compact JSON summary for the manuscript/report.
    summary_rows = []
    for _, r in out.iterrows():
        summary_rows.append(
            {
                "budget": float(r["hotspot_budget"]),
                "coarse_res": int(r["coarse_res"]),
                "aggregation": r["aggregation"],
                "k_fine": int(r["k_fine"]),
                "k_coarse": int(r["k_coarse"]),
                "n_fine_parents": int(r["n_hotspot_fine_parents"]),
                "n_coarse_hot": int(r["n_hotspot_coarse"]),
                "jaccard": float(r["jaccard"]),
                "f1": float(r["f1"]),
                "fine_parent_recall": float(r["fine_parent_recall"]),
                "coarse_precision": float(r["coarse_precision"]),
            }
        )
    payload = {
        "note": (
            "Exact-top-k hotspot budget sensitivity on the natively assembled R10 label "
            "table. k = round(budget * n) with H3-index tie-break; matched budgets on the "
            "fine and coarse grids. Retention metrics (fine_parent_recall, coarse_precision) "
            "separate aggregation smoothing / parent collapse / re-thresholding."
        ),
        "value_col": value_col,
        "n_fine": int(out["n_fine"].iloc[0]) if len(out) else None,
        "budgets": BUDGETS,
        "rows": summary_rows,
    }
    (outputs / "hotspot_budget_sensitivity.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
