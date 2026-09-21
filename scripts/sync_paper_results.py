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


def main() -> None:
    if not REGISTRY.exists():
        raise SystemExit("paper_results.json missing")
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload["generated_utc"] = datetime.now(timezone.utc).isoformat()
    payload["git_commit"] = _git("rev-parse", "HEAD")
    payload["run_id"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload["config_hash"] = _config_hash()

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

    hwm = _load(OUT / "hwm_quality_oof_validation.json")
    if hwm:
        payload["hwm_quality_oof_validation"] = hwm

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
