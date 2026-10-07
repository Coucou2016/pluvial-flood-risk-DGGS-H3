#!/usr/bin/env python
"""Sync outputs/paper_results.json from live diagnostic JSONs + git provenance."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REGISTRY = OUT / "paper_results.json"


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return ""


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _config_hash() -> str:
    cfg = ROOT / "configs" / "nyc.yaml"
    if not cfg.exists():
        return ""
    return hashlib.sha256(cfg.read_bytes()).hexdigest()[:16]


def _sync_pilot_from_models(payload: dict) -> None:
    """Refresh primary LM / expanded metrics from live model + baseline artifacts."""
    import pandas as pd

    from pluvial_flood_risk.config import FEATURE_COLUMNS, PROCESSED_DIR

    smoke_meta = _load(ROOT / "models" / "nyc_smoke" / "run_metadata.json")
    if smoke_meta and "lower_manhattan" in payload:
        metrics = smoke_meta.get("metrics") or {}
        lm = payload["lower_manhattan"]
        table = PROCESSED_DIR / "nyc_h3_cells.parquet"
        if table.exists():
            df = pd.read_parquet(table)
            lm["n_cells"] = int(len(df))
            if "flood_class" in df.columns:
                lm["n_positive"] = int(df["flood_class"].sum())
                lm["positive_prevalence"] = float(df["flood_class"].mean())
        sc = dict(lm.get("spatial_cv") or {})
        for k, v in metrics.items():
            if isinstance(v, (int, float, str)) or v is None:
                sc[k] = v
        lm["spatial_cv"] = sc
        if smoke_meta.get("deployment"):
            lm["deployment"] = smoke_meta["deployment"]
        if smoke_meta.get("evaluation"):
            lm["evaluation"] = smoke_meta["evaluation"]
        bl = _load(OUT / "classification_baselines.json")
        if bl:
            lm["baselines"] = bl
        payload["lower_manhattan"] = lm

    exp_meta = _load(ROOT / "models" / "nyc_expanded" / "run_metadata.json")
    exp_summary = _load(OUT / "expanded_primary_table.json")
    if "manhattan_expanded" in payload and (exp_meta or exp_summary):
        exp = payload["manhattan_expanded"]
        table_exp = PROCESSED_DIR / "nyc_h3_cells_expanded.parquet"
        if table_exp.exists():
            df = pd.read_parquet(table_exp)
            exp["n_cells"] = int(len(df))
            if "flood_class" in df.columns:
                exp["n_positive"] = int(df["flood_class"].sum())
                exp["positive_prevalence"] = float(df["flood_class"].mean())
        metrics = (exp_meta or {}).get("metrics") or (exp_summary or {}).get("spatial_cv") or {}
        sc = dict(exp.get("spatial_cv") or {})
        for k, v in metrics.items():
            if isinstance(v, (int, float, str)) or v is None:
                sc[k] = v
        exp["spatial_cv"] = sc
        if exp_meta and exp_meta.get("deployment"):
            exp["deployment"] = exp_meta["deployment"]
        bl = _load(OUT / "classification_baselines_expanded.json") or (
            (exp_summary or {}).get("constant_baselines")
        )
        if bl:
            # Normalise expanded baseline keys to the LM naming
            exp["baselines"] = {
                "overall_positive_prevalence": bl.get("overall_positive_prevalence")
                or exp.get("positive_prevalence"),
                "model_mean_acc": bl.get("model_mean_acc"),
                "model_mean_f1": bl.get("model_mean_f1"),
                "always_positive_mean_acc": bl.get("always_positive_mean_acc")
                or bl.get("always_positive_acc_mean"),
                "always_positive_mean_f1": bl.get("always_positive_mean_f1")
                or bl.get("always_positive_f1_mean"),
                "always_negative_mean_acc": bl.get("always_negative_mean_acc")
                or bl.get("always_negative_acc_mean"),
                "always_negative_mean_f1": bl.get("always_negative_mean_f1")
                or bl.get("always_negative_f1_mean", 0.0),
                "model_beats_majority_acc": bl.get("model_beats_majority_acc"),
                "model_beats_majority_f1": bl.get("model_beats_majority_f1"),
            }
        payload["manhattan_expanded"] = exp

    payload["feature_columns"] = list(FEATURE_COLUMNS)
    payload["urban_flag_removed"] = "land_cover_urban" not in FEATURE_COLUMNS


def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit("paper_results.json missing")
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["generated_utc"] = datetime.now(timezone.utc).isoformat()
    payload["git_commit"] = _git("rev-parse", "HEAD")
    payload["run_id"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload["config_hash"] = _config_hash()

    _sync_pilot_from_models(payload)

    src = _load(OUT / "source_ablation.json")
    if src:
        payload["source_ablation"] = src

    blk = _load(OUT / "block_sensitivity.json")
    if blk:
        payload["block_sensitivity"] = blk

    sandy = _load(OUT / "sandy_311_window_sensitivity.json")
    if sandy:
        payload["sandy_311_window_sensitivity"] = sandy

    oof = _load(OUT / "oof_extended_metrics.json")
    if oof:
        payload["oof_extended_metrics"] = oof

    land = _load(OUT / "land_mask_sensitivity.json")
    if land:
        payload["land_mask_sensitivity"] = land

    poly = _load(OUT / "polygon_area_threshold_sensitivity.json")
    if poly:
        payload["polygon_area_threshold_sensitivity"] = poly

    hwm = _load(OUT / "hwm_validation.json") or _load(OUT / "hwm_quality_oof_validation.json")
    if hwm:
        payload["hwm_quality_oof_validation"] = hwm
        payload["hwm_validation"] = hwm

    thr = _load(OUT / "operating_threshold_sensitivity.json")
    if thr:
        payload["operating_threshold_sensitivity"] = thr

    adaptive = _load(OUT / "adaptive_r11_hotspot_retention.json")
    if adaptive:
        payload["adaptive_r11_hotspot_retention"] = adaptive

    # Keep scale_loss if make_figures already wrote it; else leave existing.
    jac = OUT / "jaccard_by_resolution.csv"
    if jac.exists():
        import pandas as pd

        ladder = pd.read_csv(jac)
        payload["scale_loss"] = {
            "source_csv": "outputs/jaccard_by_resolution.csv",
            "source_json": "outputs/jaccard_by_resolution.json",
            "generated_utc": payload["generated_utc"],
            "budget_match_mode": "strict_area_budget",
            "primary_metric": "area_weighted_soft_jaccard",
            "hotspot_budget": 0.10,
            "study_domain_mask": bool(
                ladder["study_domain_mask"].iloc[0]
            )
            if "study_domain_mask" in ladder.columns
            else False,
            "n_fine": int(ladder["n_fine"].iloc[0]) if len(ladder) else None,
            "n_coarse_r9": int(ladder.loc[ladder["coarse_res"] == 9, "n_coarse"].iloc[0])
            if len(ladder)
            else None,
            "rows": json.loads(ladder.to_json(orient="records")),
        }

    REGISTRY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated {REGISTRY} commit={payload['git_commit'][:12]} run_id={payload['run_id']}")


if __name__ == "__main__":
    main()
