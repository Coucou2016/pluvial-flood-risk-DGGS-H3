"""Regenerate all paper figures from their locked data tables in one step.

Usage: .venv\\Scripts\\python.exe scripts\\make_figures.py
Writes PNG + PDF into docs/paper/figures/.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from pluvial_flood_risk.figures import (
    plot_adaptive_ablation,
    plot_jaccard_ladder,
    plot_multi_resolution_spatial,
    plot_resolution_effects,
    plot_source_evidence_maps,
    plot_spatial_cv_bars,
    plot_spatial_maps,
    plot_workflow_schematic,
)
from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "paper" / "figures"
STAGING = ROOT / "outputs" / "_figure_staging"
DATA = ROOT / "data"
OUT = ROOT / "outputs"
MODELS = ROOT / "models"
RAW = DATA / "raw" / "nyc"


def _publish(staged: Path, dest: Path) -> None:
    """Write via staging then copy; retries around Windows file locks (Errno 22)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: OSError | None = None
    for attempt in range(8):
        try:
            shutil.copy2(staged, dest)
            pdf = staged.with_suffix(".pdf")
            if pdf.exists():
                shutil.copy2(pdf, dest.with_suffix(".pdf"))
            return
        except OSError as exc:
            last_err = exc
            time.sleep(0.4 * (attempt + 1))
    raise OSError(f"Failed to publish {staged} -> {dest}: {last_err}")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)

    # Fig 1 — conceptual workflow (no data dependency)
    plot_workflow_schematic(STAGING / "workflow_schematic.png")
    _publish(STAGING / "workflow_schematic.png", FIG_DIR / "workflow_schematic.png")

    # Fig 2 — spatial result maps (observed / OOF probability / PFI_h)
    plot_spatial_maps(
        DATA / "processed" / "nyc_h3_cells.parquet",
        MODELS / "nyc_smoke" / "spatial_cv_oof_predictions.csv",
        OUT / "pfi_h_scenarios.parquet",
        RAW / "dem.tif",
        RAW / "hydro_streams.geojson",
        STAGING / "spatial_maps.png",
    )
    _publish(STAGING / "spatial_maps.png", FIG_DIR / "spatial_maps.png")

    # Fig 3 — spatial CV folds (live fold CSV)
    plot_spatial_cv_bars(
        MODELS / "nyc_smoke" / "spatial_cv_folds.csv",
        STAGING / "spatial_cv_folds.png",
    )
    _publish(STAGING / "spatial_cv_folds.png", FIG_DIR / "spatial_cv_folds.png")

    # Fig 4 — source-specific open-evidence maps (DEP / 311 / HWM / composite)
    plot_source_evidence_maps(
        DATA / "processed" / "nyc_h3_cells.parquet",
        RAW / "dem.tif",
        RAW / "hydro_streams.geojson",
        STAGING / "source_evidence_maps.png",
    )
    _publish(STAGING / "source_evidence_maps.png", FIG_DIR / "source_evidence_maps.png")

    # Fig 5 — multi-resolution open-label score surface (R10 / R9 mean / R8 mean)
    plot_multi_resolution_spatial(
        DATA / "processed" / "nyc_h3_cells_r10_labels.parquet",
        RAW / "dem.tif",
        RAW / "hydro_streams.geojson",
        STAGING / "multi_resolution_spatial.png",
    )
    _publish(STAGING / "multi_resolution_spatial.png", FIG_DIR / "multi_resolution_spatial.png")

    # Supplementary Fig S1 + Fig 6 — both read the canonical area-budget ladder.
    sup_dir = FIG_DIR / "supplementary"
    sup_dir.mkdir(parents=True, exist_ok=True)
    import json
    import pandas as pd
    from datetime import datetime, timezone
    from pluvial_flood_risk.rollups import HARD_TIE_BOOTSTRAP_PAPER

    r10_labels = pd.read_parquet(DATA / "processed" / "nyc_h3_cells_r10_labels.parquet")
    ladder = resolution_ladder_topk_diagnostics(
        r10_labels,
        value_col="flood_risk",
        resolutions=[8, 9],
        hotspot_budget=0.10,
        n_hard_boot=HARD_TIE_BOOTSTRAP_PAPER,
        random_seed=42,
    )
    csv_path = OUT / "jaccard_by_resolution.csv"
    json_path = OUT / "jaccard_by_resolution.json"
    ladder.to_csv(csv_path, index=False)
    json_path.write_text(
        json.dumps(ladder.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    registry = ROOT / "outputs" / "paper_results.json"
    if registry.exists():
        payload = json.loads(registry.read_text(encoding="utf-8"))
        payload["scale_loss"] = {
            "source_csv": "outputs/jaccard_by_resolution.csv",
            "source_json": "outputs/jaccard_by_resolution.json",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "budget_match_mode": "strict_area_budget",
            "primary_metric": "area_weighted_soft_jaccard",
            "hotspot_budget": 0.10,
            "n_fine": int(ladder["n_fine"].iloc[0]) if len(ladder) else None,
            "rows": json.loads(ladder.to_json(orient="records")),
        }
        registry.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    plot_jaccard_ladder(
        csv_path,
        STAGING / "jaccard_by_resolution.png",
    )
    _publish(STAGING / "jaccard_by_resolution.png", sup_dir / "jaccard_by_resolution.png")

    # Fig 6 — violins from R10 labels; Jaccard heatmap from the same CSV as Table 4
    plot_resolution_effects(
        DATA / "processed" / "nyc_h3_cells_r10_labels.parquet",
        STAGING / "resolution_effects.png",
        ladder_table=csv_path,
    )
    _publish(STAGING / "resolution_effects.png", FIG_DIR / "resolution_effects.png")

    # Supplementary Fig S2 — adaptive vs fixed/uniform cell counts (live ablation CSV).
    # Demoted from a main figure: this is a representation-size count, reported as a
    # table in the manuscript, so only a compact supplementary figure is rendered.
    plot_adaptive_ablation(
        OUT / "adaptive_vs_fixed_ablation.csv",
        STAGING / "adaptive_ablation.png",
    )
    _publish(STAGING / "adaptive_ablation.png", sup_dir / "adaptive_ablation.png")

    print("Wrote figures to", FIG_DIR)


if __name__ == "__main__":
    main()
