"""Regenerate all paper figures from their locked data tables in one step.

Usage: .venv\\Scripts\\python.exe scripts\\make_figures.py
Writes PNG + PDF into docs/paper/figures/.
"""
from pathlib import Path

from pluvial_flood_risk.figures import (
    plot_adaptive_ablation,
    plot_jaccard_ladder,
    plot_multi_resolution_spatial,
    plot_resolution_effects,
    plot_spatial_cv_bars,
    plot_spatial_maps,
    plot_workflow_schematic,
)

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "paper" / "figures"
DATA = ROOT / "data"
OUT = ROOT / "outputs"
MODELS = ROOT / "models"
RAW = DATA / "raw" / "nyc"


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Fig 1 — conceptual workflow (no data dependency)
    plot_workflow_schematic(FIG_DIR / "workflow_schematic.png")

    # Fig 2 — spatial result maps (observed / OOF probability / PFI_h)
    plot_spatial_maps(
        DATA / "processed" / "nyc_h3_cells.parquet",
        MODELS / "nyc_smoke" / "spatial_cv_oof_predictions.csv",
        OUT / "pfi_h_scenarios.parquet",
        RAW / "dem.tif",
        RAW / "hydro_streams.geojson",
        FIG_DIR / "spatial_maps.png",
    )

    # Fig 3 — spatial CV folds (live fold CSV)
    plot_spatial_cv_bars(
        MODELS / "nyc_smoke" / "spatial_cv_folds.csv",
        FIG_DIR / "spatial_cv_folds.png",
    )

    # Fig 4 — multi-resolution open-label score surface (R10 / R9 mean / R8 mean)
    plot_multi_resolution_spatial(
        DATA / "processed" / "nyc_h3_cells_r10_labels.parquet",
        RAW / "dem.tif",
        RAW / "hydro_streams.geojson",
        FIG_DIR / "multi_resolution_spatial.png",
    )

    # Supplementary Fig S1 — Jaccard/F1 scale-loss ladder (live diagnostic CSV)
    sup_dir = FIG_DIR / "supplementary"
    sup_dir.mkdir(parents=True, exist_ok=True)
    plot_jaccard_ladder(
        OUT / "jaccard_by_resolution.csv",
        sup_dir / "jaccard_by_resolution.png",
    )

    # Fig 5 — resolution effects: score distribution + hotspot-persistence matrix
    plot_resolution_effects(
        DATA / "processed" / "nyc_h3_cells_r10_labels.parquet",
        FIG_DIR / "resolution_effects.png",
    )

    # Fig 6 — adaptive vs fixed/uniform cell counts (live ablation CSV)
    plot_adaptive_ablation(
        OUT / "adaptive_vs_fixed_ablation.csv",
        FIG_DIR / "adaptive_ablation.png",
    )

    print("Wrote figures to", FIG_DIR)


if __name__ == "__main__":
    main()
