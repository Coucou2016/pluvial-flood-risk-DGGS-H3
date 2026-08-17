"""End-to-end train, predict, and evaluate pipeline."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from pluvial_flood_risk.config import (
    DEFAULT_SPATIAL_CV_FOLDS,
    DEFAULT_SPATIAL_CV_K,
    MODELS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    PROVENANCE_SYNTHETIC,
    TARGET_CLASS_COLUMN,
    TARGET_COLUMN,
)
from pluvial_flood_risk.features import engineer_features_for_cells, feature_matrix
from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_centers, cell_resolution
from pluvial_flood_risk.io_export import to_geojson, to_parquet
from pluvial_flood_risk.metadata import build_run_metadata, write_run_metadata
from pluvial_flood_risk.metrics import evaluate_predictions
from pluvial_flood_risk.model import load_models, predict, save_models, train_models
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics
from pluvial_flood_risk.validation import emit_validation_warnings, validate_training_table


def load_training_table(path: Path | None = None) -> pd.DataFrame:
    path = path or (PROCESSED_DIR / "demo_h3_cells.parquet")
    if not path.exists():
        from pluvial_flood_risk.synthetic import write_demo_data

        write_demo_data()
    return pd.read_parquet(path)


def _data_provenance(df: pd.DataFrame) -> str:
    if "assembly_mode" in df.columns:
        modes = [str(m) for m in df["assembly_mode"].dropna().unique().tolist()]
        if len(modes) == 1 and modes[0] == "fixture":
            return "fixture"
        if "fixture" in modes:
            return "mixed"
    if "label_source" in df.columns:
        sources = df["label_source"].dropna().unique().tolist()
        if len(sources) == 1:
            return str(sources[0])
        return "mixed"
    return PROVENANCE_SYNTHETIC


def run_training(
    data_path: Path | None = None,
    model_dir: Path | None = None,
    spatial_cv_k: int = DEFAULT_SPATIAL_CV_K,
    spatial_cv_folds: int = DEFAULT_SPATIAL_CV_FOLDS,
) -> dict:
    df = load_training_table(data_path)
    issues = validate_training_table(df)
    emit_validation_warnings(issues)

    X = feature_matrix(df)
    y_class = df[TARGET_CLASS_COLUMN].to_numpy()
    y_risk = df[TARGET_COLUMN].to_numpy()
    cells = df["h3_index"].astype(str).tolist()

    result = train_models(
        X,
        y_class,
        y_risk,
        cells=cells,
        spatial_cv_k=spatial_cv_k,
        spatial_cv_folds=spatial_cv_folds,
    )
    model_dir = model_dir or MODELS_DIR
    metrics = dict(result.metrics)
    fold_rows = metrics.pop("spatial_cv_fold_table", None)
    if fold_rows:
        from pluvial_flood_risk.spatial_cv import write_spatial_cv_fold_table

        # Demo/default models/ → outputs/spatial_cv_folds.csv
        # Named model dirs (e.g. nyc_smoke) → models/<name>/ + outputs/spatial_cv_folds_<name>.csv
        if model_dir == MODELS_DIR:
            out_fold = OUTPUTS_DIR / "spatial_cv_folds.csv"
        else:
            out_fold = model_dir / "spatial_cv_folds.csv"
            write_spatial_cv_fold_table(fold_rows, OUTPUTS_DIR / f"spatial_cv_folds_{model_dir.name}.csv")
        write_spatial_cv_fold_table(fold_rows, out_fold)
        metrics["spatial_cv_fold_csv"] = str(out_fold)

    oof_rows = metrics.pop("spatial_cv_oof_table", None)
    if oof_rows:
        from pluvial_flood_risk.spatial_cv import write_spatial_cv_oof_table

        if model_dir == MODELS_DIR:
            out_oof = OUTPUTS_DIR / "spatial_cv_oof_predictions.csv"
        else:
            out_oof = model_dir / "spatial_cv_oof_predictions.csv"
        write_spatial_cv_oof_table(oof_rows, out_oof)
        metrics["spatial_cv_oof_csv"] = str(out_oof)

    result.metrics = metrics
    save_models(result, model_dir)

    meta = build_run_metadata(
        data_provenance=_data_provenance(df),
        extra={
            "n_cells": int(len(df)),
            "metrics": metrics,
            "spatial_cv_k": spatial_cv_k,
            "spatial_cv_folds": spatial_cv_folds,
        },
    )
    write_run_metadata(model_dir / "run_metadata.json", meta)
    return metrics


def _features_for_inference(
    cells: list[str],
    rainfall_mm_h: float,
    sources=None,
    fallback_synthetic: bool = True,
) -> pd.DataFrame:
    if sources is not None:
        from pluvial_flood_risk.assemble import assemble_feature_table

        return assemble_feature_table(
            cells,
            rainfall_mm_h=rainfall_mm_h,
            sources=sources,
            fallback_synthetic=fallback_synthetic,
        )
    df = engineer_features_for_cells(cells, rainfall_mm_h=rainfall_mm_h)
    if cells:
        lons, lats = cell_centers(cells)
        df["lon"] = lons
        df["lat"] = lats
        df["h3_resolution"] = cell_resolution(cells[0])
    df["feature_source"] = PROVENANCE_SYNTHETIC
    return df


def run_inference(
    bbox: tuple[float, float, float, float],
    resolution: int,
    model_dir: Path | None = None,
    rainfall_mm_h: float = 25.0,
    output_dir: Path | None = None,
    sources=None,
    fallback_synthetic: bool = True,
) -> pd.DataFrame:
    model_dir = model_dir or MODELS_DIR
    clf, reg, feature_cols = load_models(model_dir)

    min_lon, min_lat, max_lon, max_lat = bbox
    cells = bbox_to_cells(min_lon, min_lat, max_lon, max_lat, resolution)
    df = _features_for_inference(
        cells,
        rainfall_mm_h=rainfall_mm_h,
        sources=sources,
        fallback_synthetic=fallback_synthetic,
    )
    X = df[feature_cols].to_numpy(dtype=float)

    risk, proba, pred_class = predict(clf, reg, X)
    df["predicted_risk"] = risk
    df["flood_probability"] = proba
    df["PFI_h"] = proba
    df["predicted_class"] = pred_class
    df["rainfall_mm_h"] = rainfall_mm_h

    output_dir = output_dir or OUTPUTS_DIR
    to_parquet(df, output_dir / "risk_cells.parquet")
    to_geojson(df, output_dir / "risk_cells.geojson")
    return df


def run_inference_scenarios(
    bbox: tuple[float, float, float, float],
    resolution: int,
    scenarios: list[dict],
    model_dir: Path | None = None,
    output_dir: Path | None = None,
    sources=None,
    fallback_synthetic: bool = True,
) -> pd.DataFrame:
    """
    Event-conditioned PFI_h(c, r): static features once, rainfall r varies.

    Writes ``pfi_h_scenarios.parquet`` and ``.csv`` under ``output_dir``.
    """
    model_dir = model_dir or MODELS_DIR
    output_dir = output_dir or OUTPUTS_DIR
    clf, reg, feature_cols = load_models(model_dir)

    min_lon, min_lat, max_lon, max_lat = bbox
    cells = bbox_to_cells(min_lon, min_lat, max_lon, max_lat, resolution)
    base_rain = float(scenarios[0]["mm_h"]) if scenarios else 25.0
    base = _features_for_inference(
        cells,
        rainfall_mm_h=base_rain,
        sources=sources,
        fallback_synthetic=fallback_synthetic,
    )

    frames: list[pd.DataFrame] = []
    for scen in scenarios:
        mm_h = float(scen["mm_h"])
        name = str(scen.get("name", f"r{mm_h}"))
        df = base.copy()
        df["rainfall_mm_h"] = mm_h
        df["scenario"] = name
        X = df[feature_cols].to_numpy(dtype=float)
        risk, proba, pred_class = predict(clf, reg, X)
        df["predicted_risk"] = risk
        df["flood_probability"] = proba
        df["PFI_h"] = proba
        df["predicted_class"] = pred_class
        frames.append(df)

    out = pd.concat(frames, ignore_index=True) if frames else base
    output_dir.mkdir(parents=True, exist_ok=True)
    to_parquet(out, output_dir / "pfi_h_scenarios.parquet")
    out.to_csv(output_dir / "pfi_h_scenarios.csv", index=False)
    return out


def run_evaluation(
    data_path: Path | None = None,
    model_dir: Path | None = None,
    spatial_cv_k: int = DEFAULT_SPATIAL_CV_K,
    spatial_cv_folds: int = DEFAULT_SPATIAL_CV_FOLDS,
) -> dict:
    df = load_training_table(data_path)
    model_dir = model_dir or MODELS_DIR
    clf, reg, feature_cols = load_models(model_dir)
    X = df[feature_cols].to_numpy(dtype=float)
    risk, proba, pred_class = predict(clf, reg, X)

    metrics = evaluate_predictions(
        df[TARGET_COLUMN].to_numpy(),
        risk,
        df[TARGET_CLASS_COLUMN].to_numpy(),
        pred_class,
        proba,
    )
    metrics["eval_mode"] = "in_sample_full_table"
    metrics["data_provenance"] = _data_provenance(df)
    metrics["gbm_in_sample_accuracy"] = metrics["accuracy"]
    metrics["gbm_in_sample_f1"] = metrics["f1"]

    if "h3_index" in df.columns:
        cell_list = df["h3_index"].astype(str).tolist()
        groups = block_ids_for_cells(cell_list, spatial_cv_k)
        metrics.update(
            spatial_block_cv_metrics(
                X,
                df[TARGET_CLASS_COLUMN].to_numpy(),
                df[TARGET_COLUMN].to_numpy(),
                groups,
                n_splits=spatial_cv_folds,
                cells=cell_list,
            )
        )
        fold_rows = metrics.pop("spatial_cv_fold_table", None)
        if fold_rows:
            from pluvial_flood_risk.spatial_cv import write_spatial_cv_fold_table

            fold_csv = OUTPUTS_DIR / "spatial_cv_folds_eval.csv"
            write_spatial_cv_fold_table(fold_rows, fold_csv)
            metrics["spatial_cv_fold_csv"] = str(fold_csv)
        oof_rows = metrics.pop("spatial_cv_oof_table", None)
        if oof_rows:
            from pluvial_flood_risk.spatial_cv import write_spatial_cv_oof_table

            oof_csv = OUTPUTS_DIR / "spatial_cv_oof_predictions_eval.csv"
            write_spatial_cv_oof_table(oof_rows, oof_csv)
            metrics["spatial_cv_oof_csv"] = str(oof_csv)
        metrics["note"] = (
            "in_sample metrics are optimistic on training cells; "
            "spatial_cv_* are spatially blocked hold-out folds. "
            "baseline_* are logistic / ponding-rule comparisons."
        )

    from pluvial_flood_risk.baselines import compare_baselines

    try:
        metrics.update(
            compare_baselines(
                df,
                spatial_cv_k=spatial_cv_k,
                spatial_cv_folds=spatial_cv_folds,
                feature_cols=feature_cols,
            )
        )
    except Exception as exc:
        metrics["baseline_error"] = str(exc)

    return metrics


def smoke_test() -> dict:
    """Minimal end-to-end check (Oslo synthetic demo — not science)."""
    from pluvial_flood_risk.synthetic import write_demo_data

    path = write_demo_data()
    metrics_train = run_training(path)
    metrics_eval = run_evaluation(path)
    pred_df = run_inference(
        bbox=(10.70, 59.90, 10.85, 59.98),
        resolution=9,
        rainfall_mm_h=35.0,
    )
    return {
        "n_cells_trained": int(pd.read_parquet(path).shape[0]),
        "n_cells_predicted": int(pred_df.shape[0]),
        "data_provenance": PROVENANCE_SYNTHETIC,
        "train_metrics": metrics_train,
        "eval_metrics": metrics_eval,
    }


def nyc_smoke_test(
    config_path: Path | None = None,
    use_fixtures: bool = True,
) -> dict:
    """
    Manhattan/NYC paper-path smoke: assemble (fixtures if no Open Data),
    Jaccard diagnostics, train, multi-scenario PFI_h, then adaptive refinement
    driven by trained ``PFI_h`` / ``flood_probability``.

    Fixture metrics are pipeline QA, not scientific claims.
    """
    from pluvial_flood_risk.adaptive import run_adaptive_refinement
    from pluvial_flood_risk.assemble import (
        assemble_h3_table,
        assemble_label_scale_table,
        sources_from_config,
    )
    from pluvial_flood_risk.config_loader import load_study_config, rainfall_scenarios_from_config, resolve_bbox
    from pluvial_flood_risk.floodnet import floodnet_join_status
    from pluvial_flood_risk.rollups import write_jaccard_diagnostics
    from pluvial_flood_risk.schema_fixtures import FIXTURE_MARKER, write_public_schema_fixtures

    config_path = config_path or (PROJECT_ROOT / "configs" / "nyc.yaml")
    cfg = load_study_config(config_path)
    bbox_profile = str(cfg.get("default_smoke_profile") or "smoke")
    bbox = resolve_bbox(cfg, bbox_profile)
    resolution = int(cfg.get("resolution", 9))
    rainfall = float(cfg.get("rainfall_mm_h", 30.0))
    raw_dir = Path(cfg.get("paths", {}).get("raw_dir") or (PROJECT_ROOT / "data" / "raw" / "nyc"))

    live_dem = raw_dir / "dem.tif"
    marker = raw_dir / FIXTURE_MARKER
    looks_live = (
        live_dem.exists()
        and (raw_dir / "dep_stormwater_flood.geojson").exists()
        and not marker.exists()
    )
    used_fixtures = False
    if looks_live:
        cfg["assembly_mode"] = "opendata"
    elif use_fixtures:
        if not (marker.exists() and live_dem.exists()):
            write_public_schema_fixtures(raw_dir, bbox)
        used_fixtures = True
        cfg.setdefault("paths", {})
        cfg["assembly_mode"] = "fixture"

    sources = sources_from_config(cfg)
    if used_fixtures:
        sources.assembly_mode = "fixture"
        sources.dem_path = raw_dir / "dem.tif" if (raw_dir / "dem.tif").exists() else sources.dem_path
        sources.impervious_path = (
            raw_dir / "impervious.tif" if (raw_dir / "impervious.tif").exists() else sources.impervious_path
        )
        sources.buildings_path = raw_dir / "building_footprints.geojson"
        sources.hydro_path = raw_dir / "hydro_streams.geojson"
        sources.flood_polygons_path = raw_dir / "dep_stormwater_flood.geojson"
        sources.flood_points_paths = [
            raw_dir / "flooding_311.geojson",
            raw_dir / "usgs_ida_hwm.geojson",
        ]
        # Optional FloodNet stays config-driven (absent → no-op).
        from pluvial_flood_risk.floodnet import usable_floodnet_path

        fn = usable_floodnet_path((cfg.get("paths") or {}).get("floodnet"))
        if fn is not None:
            sources.flood_points_paths = list(sources.flood_points_paths) + [fn]
        sandy = raw_dir / "fema_sandy.geojson"
        if sandy.exists():
            sources.coastal_path = sandy

    labels_cfg = cfg.get("labels") or {}
    include_floodnet = bool(labels_cfg.get("include_floodnet", False))
    floodnet_status = floodnet_join_status(
        (cfg.get("paths") or {}).get("floodnet"),
        include=include_floodnet,
    )

    df = assemble_h3_table(bbox, resolution, rainfall_mm_h=rainfall, sources=sources)
    processed = PROCESSED_DIR
    processed.mkdir(parents=True, exist_ok=True)
    table_path = processed / "nyc_h3_cells.parquet"
    df.to_parquet(table_path, index=False)

    value_col = "flood_risk" if "flood_risk" in df.columns else "predicted_risk"
    diag_cfg = cfg.get("diagnostics") or {}
    diag_res = [int(r) for r in (diag_cfg.get("resolutions") or [8, 9, 10])]
    # Paper-facing ladder needs fine_res >= 10 (Svellingen-style design, open labels).
    # Training table may stay coarser (smoke resolution); assemble a fine diagnostic table.
    jaccard_fine = int(diag_cfg.get("fine_res") or max([resolution, *diag_res]))
    jaccard_source = df
    if jaccard_fine > resolution:
        # Fast fine ladder: point labels @ fine_res + inherit polygon scores from train table.
        # (Direct DEP polygon overlay at R10 is ~minutes; not suitable for smoke.)
        jaccard_source = assemble_label_scale_table(
            bbox, jaccard_fine, sources=sources, parent_label_df=df
        )
        fine_table_path = processed / f"nyc_h3_cells_r{jaccard_fine}_labels.parquet"
        jaccard_source.to_parquet(fine_table_path, index=False)
    diag_res_use = sorted({r for r in diag_res if r <= jaccard_fine})
    outputs = OUTPUTS_DIR
    outputs.mkdir(parents=True, exist_ok=True)
    jaccard_path = outputs / "jaccard_by_resolution.csv"
    jaccard_df = write_jaccard_diagnostics(
        jaccard_source,
        jaccard_path,
        value_col=value_col if value_col in jaccard_source.columns else "flood_risk",
        resolutions=diag_res_use,
        hotspot_quantile=float(diag_cfg.get("hotspot_quantile", 0.9)),
    )
    jaccard_png = outputs / "jaccard_by_resolution.png"
    jaccard_figure = None
    try:
        from pluvial_flood_risk.figures import plot_jaccard_ladder

        plot_jaccard_ladder(
            jaccard_df,
            jaccard_png,
            caption=(
                "Open-label / live-layer scale-loss diagnostic — not a reproduction of "
                "Svellingen et al. Jaccard 0.14 (R13 vs R10, proprietary PFIb)."
                if not used_fixtures
                else (
                    "Fixture/synthetic QA figure — not a reproduction of Svellingen et al. "
                    "Jaccard 0.14 (R13 vs R10, proprietary PFIb)."
                )
            ),
        )
        jaccard_figure = str(jaccard_png)
    except Exception:
        jaccard_figure = None

    nc_metrics = {}
    nc_path = outputs / "negative_control.json"
    if "sandy_area_frac" in df.columns:
        from pluvial_flood_risk.negative_control import negative_control_metrics

        nc_metrics = negative_control_metrics(df, score_col=value_col)
        cleaned = {
            k: (None if isinstance(v, float) and not math.isfinite(v) else v)
            for k, v in nc_metrics.items()
        }
        nc_path.write_text(json.dumps(cleaned, indent=2, default=str), encoding="utf-8")
        nc_metrics = cleaned

    model_dir = MODELS_DIR / "nyc_smoke"
    train_metrics = run_training(table_path, model_dir=model_dir)
    eval_metrics = run_evaluation(table_path, model_dir=model_dir)
    scenarios = rainfall_scenarios_from_config(cfg)
    scen_df = run_inference_scenarios(
        bbox,
        resolution,
        scenarios,
        model_dir=model_dir,
        output_dir=outputs,
        sources=sources,
    )

    # Adaptive screen after training: use ML PFI_h / flood_probability (not pre-train synthetic scores).
    adaptive_cfg = cfg.get("adaptive") or {}
    adaptive_rain = float(cfg.get("rainfall_mm_h", rainfall))
    if scenarios:
        ida = next((s for s in scenarios if str(s.get("name", "")).lower() in {"ida_like", "ida"}), None)
        adaptive_rain = float((ida or scenarios[-1])["mm_h"])
    coarse_pred = run_inference(
        bbox,
        resolution,
        model_dir=model_dir,
        rainfall_mm_h=adaptive_rain,
        output_dir=outputs / "adaptive_screen",
        sources=sources,
        fallback_synthetic=used_fixtures,
    )
    mixed_cells, adaptive_metrics = run_adaptive_refinement(
        coarse_pred,
        fine_res=int(adaptive_cfg.get("fine_res", resolution + 1)),
        score_col="PFI_h",
        proba_col="flood_probability",
        score_quantile=float(adaptive_cfg.get("risk_quantile", 0.8)),
        uncertainty_min=float(adaptive_cfg.get("uncertainty_min", 0.7)),
        expand_k=int(adaptive_cfg.get("expand_neighbors", 1)),
    )
    adaptive_metrics = {
        **adaptive_metrics,
        "score_source": "trained_PFI_h",
        "adaptive_rainfall_mm_h": adaptive_rain,
    }

    from pluvial_flood_risk.ablation import adaptive_vs_fixed_ablation, write_ablation_report

    ablation = adaptive_vs_fixed_ablation(
        coarse_pred,
        fine_res=int(adaptive_cfg.get("fine_res", resolution + 1)),
        score_col="PFI_h",
        proba_col="flood_probability",
        score_quantile=float(adaptive_cfg.get("risk_quantile", 0.8)),
        expand_k=int(adaptive_cfg.get("expand_neighbors", 1)),
    )
    ablation_path = outputs / "adaptive_vs_fixed_ablation.csv"
    write_ablation_report(ablation, ablation_path)

    return {
        "n_cells": int(len(df)),
        "bbox_profile": bbox_profile,
        "bbox": list(bbox),
        "floodnet_join": floodnet_status,
        "data_provenance": _data_provenance(df),
        "assembly_mode": str(df["assembly_mode"].iloc[0]) if "assembly_mode" in df.columns else "unknown",
        "used_schema_fixtures": used_fixtures,
        "label_source": str(df["label_source"].iloc[0]) if "label_source" in df.columns else "unknown",
        "feature_source": str(df["feature_source"].iloc[0]) if "feature_source" in df.columns else "unknown",
        "jaccard_rows": int(len(jaccard_df)),
        "jaccard_fine_res": int(jaccard_df["fine_res"].iloc[0]) if len(jaccard_df) else None,
        "jaccard_table_mode": (
            "labels_only_fine"
            if jaccard_fine > resolution
            else "train_table"
        ),
        "jaccard_csv": str(jaccard_path),
        "jaccard_png": jaccard_figure,
        "negative_control": nc_metrics,
        "negative_control_json": str(nc_path) if nc_metrics else None,
        "adaptive": adaptive_metrics,
        "ablation": ablation,
        "ablation_csv": str(ablation_path),
        "n_adaptive_cells": len(mixed_cells),
        "n_scenario_rows": int(len(scen_df)),
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "science_claim": (
            "fixture pipeline QA only — not NYC flood skill, not 7Analytics PFIb"
            if used_fixtures
            else "opendata table assembled; still requires spatial CV + documented labels"
        ),
    }
