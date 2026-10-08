#!/usr/bin/env python
"""Sync outputs/paper_results.json from live diagnostic JSONs + git provenance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REGISTRY = OUT / "paper_results.json"

_WIN_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return ""


def _rel(path: Path | str) -> str:
    """Project-relative POSIX path (never an absolute Windows path)."""
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except (ValueError, OSError):
        return p.name


def _rel(value):
    """Project-relative POSIX path; strip any absolute local prefix."""
    s = str(value).strip().replace("\\", "/")
    for marker in ("/outputs/", "/models/", "/data/", "/docs/"):
        idx = s.find(marker)
        if idx >= 0:
            return s[idx + 1 :]
    m = re.match(r"^[A-Za-z]:/", s)
    if m:
        return s[3:] if s.endswith("/") is False else s[3:]
    return s


def _relativise(value):
    """Recursively rewrite absolute local paths inside registry values."""
    if isinstance(value, dict):
        return {k: _relativise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_relativise(v) for v in value]
    if isinstance(value, str) and _WIN_ABS_RE.search(value) and not _URL_RE.search(value):
        return _rel(value)
    return value


def _load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _file_sha256(path: Path) -> str | None:
    return _sha256_file(path)


def _provenance_block() -> dict:
    """Split provenance: analysis source commit vs snapshot repo commit (P1-13)."""
    root = ROOT
    return {
        "analysis_source_commit": _git("rev-parse", "HEAD"),
        "analysis_source_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "snapshot_repository_commit": _git("rev-parse", "HEAD"),
        "config_sha256": _file_sha256(root / "configs" / "nyc.yaml"),
        "lockfile_sha256": _file_sha256(root / "requirements.lock.txt"),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "analysis_source_commit is the commit of this working analysis tree; "
            "snapshot_repository_commit is the commit of the flat review snapshot "
            "published to GitHub. They coincide until the flat snapshot is rebuilt."
        ),
    }


def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit("paper_results.json missing")
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["schema"] = 2
    payload["generated_utc"] = datetime.now(timezone.utc).isoformat()
    payload["git_commit"] = _git("rev-parse", "HEAD")
    payload["run_id"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload["config_hash"] = _config_hash()
    payload["provenance"] = _provenance_block()

    _sync_pilot_from_models(payload)

    # External validation (FloodNet) replaces the old top-level `floodnet` block.
    ext = _load(OUT / "floodnet_heldout_validation.json")
    if ext:
        payload["external_validation"] = ext
    payload.pop("floodnet", None)

    src = _load(OUT / "source_ablation.json")
    if src:
        payload["source_ablation"] = src

    blk = _load(OUT / "block_sensitivity.json")
    if blk:
        payload["block_sensitivity"] = blk
        # Top-level buffer-sensitivity table (P0-5) for the paper table.
        buffer_rows: list[dict] = []
        for pilot, res in (blk.get("pilots") or {}).items():
            for row in res.get("buffer_sensitivity") or []:
                buffer_rows.append({"pilot": pilot, **row})
        if buffer_rows:
            payload["buffer_sensitivity"] = {
                "note": (blk.get("pilots") or {}).get("lower_manhattan", {}).get("buffer_note", ""),
                "buffers_m": [0, 250, 500, 1000],
                "rows": buffer_rows,
            }

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

    hwm = _load(OUT / "hwm_quality_oof_validation.json") or _load(OUT / "hwm_validation.json")
    if hwm:
        payload["hwm_quality_oof_validation"] = hwm
        payload["hwm_validation"] = hwm

    thr = _load(OUT / "operating_threshold_sensitivity.json")
    if thr:
        payload["operating_threshold_sensitivity"] = thr

    adaptive = _load(OUT / "adaptive_r11_hotspot_retention.json")
    if adaptive:
        payload["adaptive_r11_hotspot_retention"] = adaptive

    # Adaptive representation cell-count accounting (rebuilt from the fresh CSV,
    # replacing the legacy PFI_h-keyed block).
    adaptive_csv = OUT / "adaptive_vs_fixed_ablation.csv"
    if adaptive_csv.exists():
        import pandas as pd

        adf = pd.read_csv(adaptive_csv)
        rows = json.loads(adf.to_json(orient="records"))
        # Enrich the first (primary) row with the refinement-completeness counts and
        # cost-recall curve from the Option A re-extraction JSON.
        if rows and adaptive:
            base = adaptive.get("base_adaptive_metrics") or {}
            rows[0].update(
                {
                    "adaptive_n_coarse": base.get("n_coarse"),
                    "adaptive_n_parents_refined": base.get("n_parents_refined"),
                    "adaptive_n_adaptive": base.get("n_adaptive"),
                    "adaptive_n_refined_children_total": adaptive.get(
                        "n_refined_children_total"
                    ),
                    "adaptive_n_refined_children_scorable": adaptive.get(
                        "n_refined_children_scorable"
                    ),
                    "adaptive_refined_children_missing": adaptive.get(
                        "refined_children_missing"
                    ),
                    "adaptive_missing_fraction": adaptive.get("missing_fraction"),
                    "adaptive_hotspot_refinement_precision": adaptive.get(
                        "hotspot_refinement_precision"
                    ),
                    "adaptive_hotspot_enrichment": adaptive.get("hotspot_enrichment"),
                    "adaptive_hotspot_refinement_recall_best_case": adaptive.get(
                        "hotspot_refinement_recall_best_case"
                    ),
                    "adaptive_hotspot_refinement_recall_worst_case": adaptive.get(
                        "hotspot_refinement_recall_worst_case"
                    ),
                    "adaptive_score_col": "susceptibility_score",
                }
            )
        payload["adaptive"] = {
            "source_csv": "outputs/adaptive_vs_fixed_ablation.csv",
            "source_json": "outputs/adaptive_r11_hotspot_retention.json",
            "note": (
                "Cell-count accounting only (deployment_full in-sample selection); "
                "not a runtime/efficiency claim. hotspot_refinement_recall counts a "
                "uniform-R11 hotspot as recalled only if that R11 cell was actually "
                "refined (the legacy coverage recall was a tautology)."
            ),
            "rows": rows,
        }

    # Spatial-block bootstrap 95% CI summary (P0-5), read from the live CV metrics.
    ci_rows: list[dict] = []
    for pilot_key, label in (
        ("lower_manhattan", "lower_manhattan"),
        ("manhattan_expanded", "manhattan_expanded"),
    ):
        sc = (payload.get(pilot_key) or {}).get("spatial_cv") or {}
        if not sc:
            continue
        ci_rows.append(
            {
                "pilot": label,
                "roc_auc_pooled": sc.get("spatial_cv_roc_auc_pooled"),
                "roc_auc_ci_low": sc.get("spatial_cv_roc_auc_ci_low"),
                "roc_auc_ci_high": sc.get("spatial_cv_roc_auc_ci_high"),
                "average_precision_pooled": sc.get("spatial_cv_average_precision_pooled"),
                "average_precision_ci_low": sc.get("spatial_cv_average_precision_ci_low"),
                "average_precision_ci_high": sc.get("spatial_cv_average_precision_ci_high"),
                "bootstrap_n": sc.get("spatial_cv_bootstrap_n"),
                "n_blocks": sc.get("spatial_cv_n_blocks"),
            }
        )
    if ci_rows:
        payload["block_bootstrap_ci"] = {
            "resampling_unit": "H3 parent block (R7) at parent-resolution offset 2",
            "note": "Spatial-block bootstrap 95% CI resamples blocks, not cells.",
            "rows": ci_rows,
        }

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
            "study_domain_mask": bool(ladder["study_domain_mask"].iloc[0])
            if "study_domain_mask" in ladder.columns
            else False,
            "n_fine": int(ladder["n_fine"].iloc[0]) if len(ladder) else None,
            "n_coarse_r9": int(ladder.loc[ladder["coarse_res"] == 9, "n_coarse"].iloc[0])
            if len(ladder)
            else None,
            "rows": json.loads(ladder.to_json(orient="records")),
        }

    payload = _relativise(payload)
    # Re-assert provenance after relativisation (they are already relative strings).
    payload["provenance"] = _provenance_block()
    payload["paths_note"] = "All paths are project-relative POSIX paths (no absolute local paths)."
    payload["freeze_tag"] = "major-revision-2026-10-08"
    REGISTRY.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated {REGISTRY} commit={payload['git_commit'][:12]} run_id={payload['run_id']}")


if __name__ == "__main__":
    main()
