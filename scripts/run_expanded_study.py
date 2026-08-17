#!/usr/bin/env python
"""Run the expanded-bbox (manhattan_expanded) primary table end-to-end.

Keeps every output separate from the published Lower Manhattan smoke so that the
n=141 results are never overwritten:

- raw data      -> data/raw/nyc_expanded/      (download first, or reuse)
- H3 table      -> data/processed/nyc_h3_cells_expanded.parquet
- models        -> models/nyc_expanded/
- summary       -> outputs/expanded_primary_table.json
- baselines     -> outputs/classification_baselines_expanded.{json,csv}

The "primary table" is the spatial H3-block CV summary plus disclosed
constant-classifier baselines (always-positive and always-negative, with the
true constant-majority derived from the pooled class count), mirroring Table 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import MODELS_DIR, OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT  # noqa: E402
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox  # noqa: E402
from pluvial_flood_risk.assemble import assemble_h3_table, sources_from_config  # noqa: E402
from pluvial_flood_risk.pipeline import run_training  # noqa: E402


def _constant_baselines(fold_csv: Path) -> dict:
    """Constant-classifier baselines for a spatial-CV fold table.

    Reports always-positive and always-negative classifiers *separately* and
    derives the true constant-majority classifier from the pooled class count,
    so that "majority" is never conflated with "always-positive" when the
    positive class is below 50%.

    All baselines are computed fold-wise and then averaged, matching how the
    model's spatial-CV accuracy/F1 are reported (mean of per-fold metrics).
    Pooled values are also emitted for reference.
    """
    import pandas as pd

    df = pd.read_csv(fold_csv)
    per_fold = []
    for _, r in df.iterrows():
        pos = int(r["n_positive_test"])
        neg = int(r["n_negative_test"])
        n = pos + neg
        per_fold.append(
            {
                "n_test": n,
                "pos": pos,
                "neg": neg,
                # always-positive: predict 1 everywhere
                "ap_acc": pos / n,
                "ap_f1": (2.0 * pos / (n + pos)) if pos > 0 else 0.0,
                # always-negative: predict 0 everywhere (positive-class F1 = 0)
                "an_acc": neg / n,
                "an_f1": 0.0,
                "model_acc": float(r["accuracy"]),
                "model_f1": float(r["f1"]),
            }
        )

    total_pos = sum(f["pos"] for f in per_fold)
    total_neg = sum(f["neg"] for f in per_fold)
    n = total_pos + total_neg
    prevalence = total_pos / n if n else 0.0
    majority_class = "negative" if total_neg >= total_pos else "positive"

    def mean(key: str) -> float:
        return sum(f[key] for f in per_fold) / len(per_fold)

    model_acc = mean("model_acc")
    model_f1 = mean("model_f1")

    ap_acc_mean = mean("ap_acc")
    ap_f1_mean = mean("ap_f1")
    an_acc_mean = mean("an_acc")

    # Constant-majority classifier = always predict the pooled majority class.
    if majority_class == "negative":
        majority_acc_mean = an_acc_mean
        majority_f1_mean = 0.0
    else:
        majority_acc_mean = ap_acc_mean
        majority_f1_mean = ap_f1_mean

    return {
        "n_test": n,
        "n_positive": total_pos,
        "n_negative": total_neg,
        "positive_prevalence": prevalence,
        "majority_class": majority_class,
        "model_mean_acc": model_acc,
        "model_mean_f1": model_f1,
        # always-positive (fold-mean + pooled)
        "always_positive_acc_mean": ap_acc_mean,
        "always_positive_f1_mean": ap_f1_mean,
        "always_positive_acc_pooled": prevalence,
        "always_positive_f1_pooled": (2.0 * prevalence / (1.0 + prevalence)) if prevalence > 0 else 0.0,
        # always-negative (fold-mean + pooled)
        "always_negative_acc_mean": an_acc_mean,
        "always_negative_f1_mean": 0.0,
        "always_negative_acc_pooled": total_neg / n if n else 0.0,
        "always_negative_f1_pooled": 0.0,
        # constant-majority (fold-mean)
        "majority_acc_mean": majority_acc_mean,
        "majority_f1_mean": majority_f1_mean,
        # comparisons (fold-mean model vs fold-mean baseline)
        "model_beats_always_positive_acc": bool(model_acc > ap_acc_mean),
        "model_beats_always_positive_f1": bool(model_f1 > ap_f1_mean),
        "model_beats_always_negative_acc": bool(model_acc > an_acc_mean),
        "model_beats_majority_acc": bool(model_acc > majority_acc_mean),
        "model_beats_majority_f1": bool(model_f1 > majority_f1_mean),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "nyc.yaml")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "nyc_expanded",
        help="Expanded raw data dir (downloaded separately)",
    )
    args = parser.parse_args()

    cfg = load_study_config(args.config)
    bbox = resolve_bbox(cfg, "manhattan_expanded")
    resolution = int(cfg.get("resolution", 9))
    rainfall = float(cfg.get("rainfall_mm_h", 40.0))

    raw_dir = Path(args.raw_dir)
    cfg["paths"] = dict(cfg.get("paths") or {})
    cfg["paths"]["raw_dir"] = raw_dir  # absolute; discover_sources() picks up conventional names
    cfg["assembly_mode"] = "opendata"

    live = (raw_dir / "dem.tif").exists() and (raw_dir / "dep_stormwater_flood.geojson").exists()
    if not live:
        print(
            f"ERROR: expanded raw dir not ready ({raw_dir}). "
            "Run: python scripts\\download_nyc_data.py --bbox-profile manhattan_expanded "
            "--out data\\raw\\nyc_expanded --dem-size 900,1200",
            file=sys.stderr,
        )
        raise SystemExit(2)

    sources = sources_from_config(cfg)
    df = assemble_h3_table(bbox, resolution, rainfall_mm_h=rainfall, sources=sources)

    table_path = PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(table_path, index=False)

    model_dir = MODELS_DIR / "nyc_expanded"
    train_metrics = run_training(table_path, model_dir=model_dir)

    fold_csv = model_dir / "spatial_cv_folds.csv"
    baseline = _constant_baselines(fold_csv) if fold_csv.exists() else {}

    summary = {
        "bbox_profile": "manhattan_expanded",
        "bbox": list(bbox),
        "resolution": resolution,
        "raw_dir": str(raw_dir),
        "n_cells": int(len(df)),
        "assembly_mode": str(df["assembly_mode"].iloc[0]) if len(df) else "unknown",
        "data_provenance": (
            str(df["label_source"].iloc[0]) if "label_source" in df.columns else "unknown"
        ),
        "flood_class_positive_frac": float(df["flood_class"].mean()) if "flood_class" in df.columns else None,
        "spatial_cv": train_metrics,
        "constant_baselines": baseline,
        "fold_csv": str(fold_csv),
        "table_path": str(table_path),
        "note": (
            "Expanded-bbox primary table (manhattan_expanded). Separate from the n=141 "
            "Lower Manhattan smoke. accuracy/F1 are reported alongside always-positive "
            "and always-negative constant classifiers, with the true constant-majority "
            "derived from the pooled class count. Classification discrimination is not "
            "claimed from thresholded accuracy/F1 alone."
        ),
    }

    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "expanded_primary_table.json").write_text(
        json.dumps(summary, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    if baseline:
        import pandas as pd

        bdf = pd.DataFrame([baseline])
        bdf.to_csv(outputs / "classification_baselines_expanded.csv", index=False)
        (outputs / "classification_baselines_expanded.json").write_text(
            json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(json.dumps(summary, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
