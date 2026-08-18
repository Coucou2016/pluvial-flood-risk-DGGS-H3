"""Regenerate all four paper figures from their locked data tables in one step.

Usage: .venv\\Scripts\\python.exe scripts\\make_figures.py
Writes PNG + PDF into docs/paper/figures/.
"""
from pathlib import Path

from pluvial_flood_risk.figures import (
    plot_adaptive_ablation,
    plot_jaccard_ladder,
    plot_spatial_cv_bars,
    plot_workflow_schematic,
)

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "paper" / "figures"


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Fig 1 — conceptual workflow (no data dependency)
    plot_workflow_schematic(FIG_DIR / "workflow_schematic.png")

    # Fig 2 — spatial CV folds (live fold CSV)
    plot_spatial_cv_bars(
        ROOT / "models" / "nyc_smoke" / "spatial_cv_folds.csv",
        FIG_DIR / "spatial_cv_folds.png",
    )

    # Fig 3 — Jaccard/F1 scale-loss ladder (live diagnostic CSV)
    plot_jaccard_ladder(
        ROOT / "outputs" / "jaccard_by_resolution.csv",
        FIG_DIR / "jaccard_by_resolution.png",
    )

    # Fig 4 — adaptive vs fixed/uniform cell counts (live ablation CSV)
    plot_adaptive_ablation(
        ROOT / "outputs" / "adaptive_vs_fixed_ablation.csv",
        FIG_DIR / "adaptive_ablation.png",
    )

    print("Wrote figures to", FIG_DIR)


if __name__ == "__main__":
    main()
