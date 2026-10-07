"""One-off: install official 76ig-c548 311 extracts and fail-closed reassemble."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.assemble import assemble_h3_table, assemble_label_scale_table, sources_from_config
from pluvial_flood_risk.config import PROCESSED_DIR
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox
from pluvial_flood_risk.download_nyc import (
    _311_OFFICIAL_LANDING,
    _311_SODA_JSON,
    _download_311_soda_official,
)
from pluvial_flood_risk.pipeline import run_training

NOW = datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def install_official_311(out_path: Path, bbox: tuple[float, float, float, float]) -> dict:
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            n, meta = _download_311_soda_official(_311_SODA_JSON, out_path, bbox=bbox)
            sidecar = out_path.with_name(out_path.stem + "_query.json")
            sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            meta["path"] = str(out_path)
            meta["n_features"] = n
            meta["sha256"] = sha256(out_path)
            meta["size_bytes"] = out_path.stat().st_size
            return meta
        except Exception as exc:
            last_err = exc
            print(f"311 download attempt {attempt} failed: {exc}")
    raise RuntimeError(f"official 311 download failed: {last_err}")


def patch_manifest(lm_meta: dict) -> None:
    man_path = ROOT / "data" / "raw" / "data_manifest.json"
    data = json.loads(man_path.read_text(encoding="utf-8"))
    data["generated_utc"] = NOW
    data["manifest_generated_utc"] = NOW
    for layer in data.get("layers") or []:
        if layer.get("layer") != "flooding_311":
            continue
        layer["official_landing_page"] = _311_OFFICIAL_LANDING
        layer["exact_download_url_or_service_layer"] = _311_SODA_JSON
        layer["item_owner"] = "City of New York"
        layer["item_org"] = "NYC Open Data"
        layer["official_identity_verified"] = True
        layer["mirror_status"] = "official"
        layer["query"] = lm_meta.get("where")
        layer["vintage"] = "311 Service Requests 2010-2019 (76ig-c548); filtered 2010-2014 Street Flooding (SJ)"
        layer["source_retrieved_utc"] = lm_meta.get("retrieved_utc")
        layer["retrieved_utc"] = lm_meta.get("retrieved_utc")
        layer["manifest_generated_utc"] = NOW
        layer["feature_count"] = lm_meta["n_features"]
        layer["size_bytes"] = lm_meta["size_bytes"]
        layer["sha256"] = lm_meta["sha256"]
        layer["license"] = "NYC Open Data Terms of Use"
        layer["query_sidecar"] = "data/raw/nyc/flooding_311_query.json"
    man_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    csv_path = ROOT / "data" / "raw" / "data_manifest.csv"
    if csv_path.exists():
        rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
        fieldnames = list(rows[0].keys()) if rows else []
        for row in rows:
            if row.get("layer") != "flooding_311":
                continue
            row["official_landing_page"] = _311_OFFICIAL_LANDING
            row["exact_download_url_or_service_layer"] = _311_SODA_JSON
            row["item_owner"] = "City of New York"
            row["item_org"] = "NYC Open Data"
            row["official_identity_verified"] = "True"
            row["mirror_status"] = "official"
            row["query"] = lm_meta.get("where", "")
            row["vintage"] = "76ig-c548 2010-2014 Street Flooding (SJ)"
            row["retrieved_utc"] = lm_meta.get("retrieved_utc", "")
            row["feature_count"] = str(lm_meta["n_features"])
            row["size_bytes"] = str(lm_meta["size_bytes"])
            row["sha256"] = lm_meta["sha256"]
            row["license"] = "NYC Open Data Terms of Use"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)


def main() -> None:
    probe = ROOT / "data" / "raw" / "nyc" / "_flooding_311_official_probe.geojson"
    if probe.exists():
        probe.unlink()

    lm_path = ROOT / "data" / "raw" / "nyc" / "flooding_311.geojson"
    lm_query = ROOT / "data" / "raw" / "nyc" / "flooding_311_query.json"
    if lm_path.exists() and lm_query.exists() and json.loads(lm_path.read_text(encoding="utf-8")).get("features"):
        n_existing = len(json.loads(lm_path.read_text(encoding="utf-8"))["features"])
        if n_existing >= 500:
            lm_meta = json.loads(lm_query.read_text(encoding="utf-8"))
            lm_meta["n_features"] = n_existing
            lm_meta["sha256"] = sha256(lm_path)
            lm_meta["size_bytes"] = lm_path.stat().st_size
            print("LM 311 already official", n_existing)
        else:
            lm_meta = install_official_311(lm_path, (-74.02, 40.70, -73.97, 40.76))
    else:
        lm_meta = install_official_311(lm_path, (-74.02, 40.70, -73.97, 40.76))
    print("LM 311 features", lm_meta["n_features"], lm_meta["sha256"][:12])
    patch_manifest(lm_meta)

    exp_path = ROOT / "data" / "raw" / "nyc_expanded" / "flooding_311.geojson"
    exp_bbox = (-74.03, 40.68, -73.94, 40.8)
    exp_meta = install_official_311(exp_path, exp_bbox)
    print("Expanded 311 features", exp_meta["n_features"], exp_meta["sha256"][:12])
    (ROOT / "data" / "raw" / "nyc_expanded" / "flooding_311_query.json").write_text(
        json.dumps(exp_meta, indent=2), encoding="utf-8"
    )

    cfg = load_study_config(ROOT / "configs" / "nyc.yaml")
    cfg["assembly_mode"] = "opendata"

    # Lower Manhattan processed + R10 labels
    sources = sources_from_config(cfg)
    bbox = resolve_bbox(cfg, "lower_manhattan")
    df = assemble_h3_table(
        bbox,
        int(cfg["resolution"]),
        rainfall_mm_h=float(cfg["rainfall_mm_h"]),
        sources=sources,
        fallback_synthetic=False,
    )
    lm_out = PROCESSED_DIR / "nyc_h3_cells.parquet"
    df.to_parquet(lm_out, index=False)
    print("LM table", len(df), "pos", int(df["flood_class"].sum()), lm_out)

    r10 = assemble_label_scale_table(bbox, 10, sources=sources)
    r10_out = PROCESSED_DIR / "nyc_h3_cells_r10_labels.parquet"
    r10.to_parquet(r10_out, index=False)
    print("R10 labels", len(r10), r10_out)

    print("Training nyc_smoke…")
    run_training(
        lm_out,
        model_dir=ROOT / "models" / "nyc_smoke",
        random_seed=int(cfg.get("random_seed", 42)),
        allow_synthetic=False,
        refuse_synthetic=True,
    )
    print("LM training done")


if __name__ == "__main__":
    main()
