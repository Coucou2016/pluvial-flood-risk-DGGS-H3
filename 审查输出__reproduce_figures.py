"""Regenerate paper figures into an audit-only folder and compare pixels."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.figures import (  # noqa: E402
    plot_adaptive_ablation,
    plot_jaccard_ladder,
    plot_multi_resolution_spatial,
    plot_resolution_effects,
    plot_source_evidence_maps,
    plot_spatial_cv_bars,
    plot_spatial_maps,
    plot_workflow_schematic,
)
from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics  # noqa: E402


OUT = ROOT / "审查输出" / "figure_reproduction"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "supplementary").mkdir(parents=True, exist_ok=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(original: Path, reproduced: Path) -> dict:
    with Image.open(original) as a_im, Image.open(reproduced) as b_im:
        a = np.asarray(a_im.convert("RGB"), dtype=np.float32)
        b = np.asarray(b_im.convert("RGB"), dtype=np.float32)
    same_shape = a.shape == b.shape
    if same_shape:
        diff = np.abs(a - b)
        rmse = float(np.sqrt(np.mean((a - b) ** 2)))
        max_abs = float(diff.max())
        exact_fraction = float(np.mean(np.all(a == b, axis=2)))
    else:
        rmse = max_abs = exact_fraction = None
    return {
        "original": original.relative_to(ROOT).as_posix(),
        "reproduced": reproduced.relative_to(ROOT).as_posix(),
        "same_shape": same_shape,
        "original_shape": list(a.shape),
        "reproduced_shape": list(b.shape),
        "same_sha256": digest(original) == digest(reproduced),
        "original_sha256": digest(original),
        "reproduced_sha256": digest(reproduced),
        "pixel_rmse_0_255": rmse,
        "pixel_max_abs": max_abs,
        "exact_pixel_fraction": exact_fraction,
    }


def main() -> None:
    data = ROOT / "data"
    raw = data / "raw" / "nyc"
    models = ROOT / "models"
    outputs = ROOT / "outputs"
    originals = ROOT / "docs" / "paper" / "figures"

    plot_workflow_schematic(OUT / "workflow_schematic.png")
    plot_spatial_maps(
        data / "processed" / "nyc_h3_cells.parquet",
        models / "nyc_smoke" / "spatial_cv_oof_predictions.csv",
        outputs / "pfi_h_scenarios.parquet",
        raw / "dem.tif",
        raw / "hydro_streams.geojson",
        OUT / "spatial_maps.png",
    )
    plot_spatial_cv_bars(models / "nyc_smoke" / "spatial_cv_folds.csv", OUT / "spatial_cv_folds.png")
    plot_source_evidence_maps(
        data / "processed" / "nyc_h3_cells.parquet",
        raw / "dem.tif",
        raw / "hydro_streams.geojson",
        OUT / "source_evidence_maps.png",
    )
    plot_multi_resolution_spatial(
        data / "processed" / "nyc_h3_cells_r10_labels.parquet",
        raw / "dem.tif",
        raw / "hydro_streams.geojson",
        OUT / "multi_resolution_spatial.png",
    )
    r10 = pd.read_parquet(data / "processed" / "nyc_h3_cells_r10_labels.parquet")
    ladder = resolution_ladder_topk_diagnostics(
        r10, value_col="flood_risk", resolutions=[8, 9], hotspot_budget=0.10
    )
    ladder.to_csv(OUT / "jaccard_by_resolution_recomputed.csv", index=False)
    plot_jaccard_ladder(ladder, OUT / "supplementary" / "jaccard_by_resolution.png")
    plot_resolution_effects(
        data / "processed" / "nyc_h3_cells_r10_labels.parquet",
        OUT / "resolution_effects.png",
        budget=0.10,
    )
    plot_adaptive_ablation(
        outputs / "adaptive_vs_fixed_ablation.csv",
        OUT / "supplementary" / "adaptive_ablation.png",
    )

    pairs = [
        (originals / "workflow_schematic.png", OUT / "workflow_schematic.png"),
        (originals / "spatial_maps.png", OUT / "spatial_maps.png"),
        (originals / "spatial_cv_folds.png", OUT / "spatial_cv_folds.png"),
        (originals / "source_evidence_maps.png", OUT / "source_evidence_maps.png"),
        (originals / "multi_resolution_spatial.png", OUT / "multi_resolution_spatial.png"),
        (originals / "resolution_effects.png", OUT / "resolution_effects.png"),
        (originals / "supplementary" / "jaccard_by_resolution.png", OUT / "supplementary" / "jaccard_by_resolution.png"),
        (originals / "supplementary" / "adaptive_ablation.png", OUT / "supplementary" / "adaptive_ablation.png"),
    ]
    comparisons = [compare(a, b) for a, b in pairs]
    saved_ladder = pd.read_csv(outputs / "jaccard_by_resolution.csv")
    common = list(ladder.columns)
    delta = (saved_ladder.select_dtypes(include=[np.number]) - ladder.select_dtypes(include=[np.number])).abs()
    ladder_equal = bool(
        saved_ladder["aggregation"].equals(ladder["aggregation"])
        and (delta.fillna(0).to_numpy() <= 1e-15).all()
    )
    evidence = {
        "figure_comparisons": comparisons,
        "all_exact_sha256": all(x["same_sha256"] for x in comparisons),
        "jaccard_csv_exact_dataframe_match": ladder_equal,
    }
    (OUT / "figure_reproduction_evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
