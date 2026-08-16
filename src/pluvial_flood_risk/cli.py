"""Command-line entry points."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import click

from pluvial_flood_risk.config import (
    DEFAULT_BBOX,
    DEFAULT_H3_RESOLUTION,
    DEFAULT_SPATIAL_CV_FOLDS,
    DEFAULT_SPATIAL_CV_K,
    MODELS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
)
from pluvial_flood_risk.config_loader import load_study_config, rainfall_scenarios_from_config
from pluvial_flood_risk.pipeline import (
    nyc_smoke_test,
    run_evaluation,
    run_inference,
    run_inference_scenarios,
    run_training,
    smoke_test,
)
from pluvial_flood_risk.synthetic import write_demo_data


def _parse_bbox(ctx, param, value):
    if value is None:
        return DEFAULT_BBOX
    parts = [float(x.strip()) for x in value.split(",")]
    if len(parts) != 4:
        raise click.BadParameter("bbox must be min_lon,min_lat,max_lon,max_lat")
    return tuple(parts)


def _parse_resolutions(value: str | None) -> list[int] | None:
    if not value:
        return None
    return [int(x.strip()) for x in value.split(",") if x.strip()]


@click.group()
def main():
    """Pluvial flood risk on H3 DGGS (ML + scalable outputs)."""
    pass


@main.command("generate-demo-data")
@click.option("--output-dir", type=click.Path(path_type=Path), default=PROCESSED_DIR)
@click.option("--resolution", default=None, type=int)
@click.option("--bbox", callback=_parse_bbox, default=None, help="min_lon,min_lat,max_lon,max_lat")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="YAML study config (e.g. configs/demo_oslo.yaml)",
)
def generate_demo_data(
    output_dir: Path,
    resolution: int | None,
    bbox: tuple[float, float, float, float],
    config_path: Path | None,
):
    """Create synthetic H3 training table (Parquet)."""
    if config_path:
        cfg = load_study_config(config_path)
        bbox = cfg["bbox"]
        resolution = cfg.get("resolution", DEFAULT_H3_RESOLUTION)
    resolution = resolution or DEFAULT_H3_RESOLUTION
    path = write_demo_data(output_dir=output_dir, bbox=bbox, resolution=resolution)
    click.echo(f"Wrote {path} ({path.stat().st_size} bytes) [synthetic provenance]")


@main.command()
@click.option("--data", "data_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--model-dir", type=click.Path(path_type=Path), default=MODELS_DIR)
@click.option("--spatial-cv-k", default=DEFAULT_SPATIAL_CV_K, show_default=True)
@click.option("--spatial-cv-folds", default=DEFAULT_SPATIAL_CV_FOLDS, show_default=True)
def train(
    data_path: Path | None,
    model_dir: Path,
    spatial_cv_k: int,
    spatial_cv_folds: int,
):
    """Train classifier + regressor; report random-split + spatial block CV."""
    metrics = run_training(
        data_path,
        model_dir,
        spatial_cv_k=spatial_cv_k,
        spatial_cv_folds=spatial_cv_folds,
    )
    click.echo(json.dumps(metrics, indent=2))


@main.command()
@click.option("--bbox", callback=_parse_bbox, default=None)
@click.option("--resolution", default=DEFAULT_H3_RESOLUTION, show_default=True)
@click.option("--rainfall", default=25.0, show_default=True, help="mm/h design storm")
@click.option("--model-dir", type=click.Path(path_type=Path), default=MODELS_DIR)
@click.option("--output-dir", type=click.Path(path_type=Path), default=OUTPUTS_DIR)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
)
@click.option(
    "--scenarios/--no-scenarios",
    default=False,
    help="Write PFI_h(c, r) table for every rainfall_scenarios entry in --config",
)
def predict(
    bbox: tuple[float, float, float, float],
    resolution: int,
    rainfall: float,
    model_dir: Path,
    output_dir: Path,
    config_path: Path | None,
    scenarios: bool,
):
    """Run inference; write Parquet + GeoJSON under outputs/."""
    cfg = None
    if config_path:
        cfg = load_study_config(config_path)
        bbox = cfg["bbox"]
        resolution = cfg.get("resolution", resolution)
        rainfall = cfg.get("rainfall_mm_h", rainfall)

    if scenarios:
        if cfg is None:
            raise click.UsageError("--scenarios requires --config with rainfall_scenarios")
        scen = rainfall_scenarios_from_config(cfg)
        df = run_inference_scenarios(bbox, resolution, scen, model_dir, output_dir)
        click.echo(f"PFI_h scenarios: {len(df)} rows ({len(scen)} rainfall rates) -> {output_dir}")
        return

    df = run_inference(bbox, resolution, model_dir, rainfall, output_dir)
    click.echo(f"Predicted {len(df)} H3 cells -> {output_dir}")


@main.command("predict-scenarios")
@click.option("--bbox", callback=_parse_bbox, default=None)
@click.option("--resolution", default=DEFAULT_H3_RESOLUTION, show_default=True)
@click.option("--model-dir", type=click.Path(path_type=Path), default=MODELS_DIR)
@click.option("--output-dir", type=click.Path(path_type=Path), default=OUTPUTS_DIR)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
)
def predict_scenarios(
    bbox: tuple[float, float, float, float],
    resolution: int,
    model_dir: Path,
    output_dir: Path,
    config_path: Path,
):
    """Event-conditioned PFI_h(c, r) for all rainfall scenarios in a YAML config."""
    cfg = load_study_config(config_path)
    bbox = cfg["bbox"]
    resolution = cfg.get("resolution", resolution)
    scen = rainfall_scenarios_from_config(cfg)
    df = run_inference_scenarios(bbox, resolution, scen, model_dir, output_dir)
    click.echo(f"Wrote {len(df)} PFI_h rows -> {output_dir / 'pfi_h_scenarios.csv'}")


@main.command()
@click.option("--data", "data_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--model-dir", type=click.Path(path_type=Path), default=MODELS_DIR)
@click.option("--spatial-cv-k", default=DEFAULT_SPATIAL_CV_K, show_default=True)
@click.option("--spatial-cv-folds", default=DEFAULT_SPATIAL_CV_FOLDS, show_default=True)
def evaluate(
    data_path: Path | None,
    model_dir: Path,
    spatial_cv_k: int,
    spatial_cv_folds: int,
):
    """Evaluate models; includes spatial block CV and simple baselines."""
    metrics = run_evaluation(
        data_path,
        model_dir,
        spatial_cv_k=spatial_cv_k,
        spatial_cv_folds=spatial_cv_folds,
    )
    for w in metrics.get("_warnings", []):
        warnings.warn(w)
    click.echo(json.dumps(metrics, indent=2, default=str))


@main.command()
@click.option(
    "--data",
    "data_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="H3 table with predicted_risk or flood_risk",
)
@click.option("--value-col", default="predicted_risk", show_default=True)
@click.option("--resolutions", default="8,9,10,11", show_default=True)
@click.option("--quantile", default=0.9, show_default=True)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=OUTPUTS_DIR / "jaccard_by_resolution.csv",
)
@click.option("--bbox", callback=_parse_bbox, default=None)
@click.option("--fine-resolution", default=None, type=int, help="Build a synthetic fine table if --data omitted")
def diagnostics(
    data_path: Path | None,
    value_col: str,
    resolutions: str,
    quantile: float,
    out: Path,
    bbox: tuple[float, float, float, float],
    fine_resolution: int | None,
):
    """Hotspot Jaccard / F1 vs parent resolution (paper Figure table)."""
    import pandas as pd

    from pluvial_flood_risk.rollups import write_jaccard_diagnostics
    from pluvial_flood_risk.synthetic import build_demo_dataset

    res_list = _parse_resolutions(resolutions) or [8, 9, 10, 11]
    if data_path:
        df = pd.read_parquet(data_path)
    else:
        fine = fine_resolution or max(res_list)
        df = build_demo_dataset(bbox=bbox, resolution=fine)
        value_col = "flood_risk"
    table = write_jaccard_diagnostics(
        df,
        out,
        value_col=value_col,
        resolutions=res_list,
        hotspot_quantile=quantile,
    )
    click.echo(f"Wrote {out} ({len(table)} rows)")
    if len(table):
        click.echo(table.to_string(index=False))
    png = out.with_suffix(".png")
    if png.exists():
        click.echo(f"Figure: {png}")


@main.command("adaptive")
@click.option("--bbox", callback=_parse_bbox, default=None)
@click.option("--coarse-res", default=9, show_default=True)
@click.option("--fine-res", default=11, show_default=True)
@click.option("--quantile", default=0.8, show_default=True, help="Risk quantile to refine")
@click.option("--expand-k", default=1, show_default=True)
@click.option("--data", "data_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=OUTPUTS_DIR / "adaptive_cells.txt",
)
def adaptive_refine(
    bbox: tuple[float, float, float, float],
    coarse_res: int,
    fine_res: int,
    quantile: float,
    expand_k: int,
    data_path: Path | None,
    out: Path,
):
    """Coarse screen then refine high-risk parents (innovation C)."""
    import pandas as pd

    from pluvial_flood_risk.adaptive import run_adaptive_refinement
    from pluvial_flood_risk.labels import synthetic_risk_score
    from pluvial_flood_risk.synthetic import build_demo_dataset

    if data_path:
        df = pd.read_parquet(data_path)
    else:
        df = build_demo_dataset(bbox=bbox, resolution=coarse_res)
    if "predicted_risk" not in df.columns:
        df = df.copy()
        df["predicted_risk"] = df["flood_risk"] if "flood_risk" in df.columns else synthetic_risk_score(df)
    mixed, metrics = run_adaptive_refinement(
        df,
        fine_res=fine_res,
        score_col="predicted_risk",
        score_quantile=quantile,
        expand_k=expand_k,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(mixed), encoding="utf-8")
    click.echo(json.dumps(metrics, indent=2, default=str))
    click.echo(f"Wrote {len(mixed)} mixed-resolution cell ids -> {out}")


@main.command()
def smoke():
    """End-to-end Oslo synthetic demo: data -> train -> eval -> predict."""
    result = smoke_test()
    click.echo(json.dumps(result, indent=2, default=str))


@main.command("nyc-smoke")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=PROJECT_ROOT / "configs" / "nyc.yaml",
)
@click.option("--no-fixtures", is_flag=True, help="Do not write schema fixtures if Open Data is missing")
def nyc_smoke(config_path: Path, no_fixtures: bool):
    """Manhattan paper-path smoke (fixtures if live Open Data is absent)."""
    result = nyc_smoke_test(config_path=config_path, use_fixtures=not no_fixtures)
    click.echo(json.dumps(result, indent=2, default=str))


@main.command("show-config")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=PROJECT_ROOT / "configs" / "demo_oslo.yaml",
)
def show_config(config_path: Path):
    """Print resolved demo/study YAML config."""
    cfg = load_study_config(config_path)
    click.echo(json.dumps(cfg, indent=2, default=str))


generate_demo_data = generate_demo_data
train = train
predict = predict
evaluate = evaluate
smoke = smoke
show_config = show_config
diagnostics = diagnostics
predict_scenarios = predict_scenarios
adaptive_refine = adaptive_refine
nyc_smoke = nyc_smoke
