"""Independent, read-only evidence checks for the manuscript audit.

This script never overwrites project data, models, figures, or paper files.  It
reads the current working tree and writes audit-only JSON/CSV evidence under
``审查输出/evidence``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import h3
import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, r2_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "审查输出" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.config import FEATURE_COLUMNS  # noqa: E402
from pluvial_flood_risk.estimators import build_classifier, build_regressor  # noqa: E402
from pluvial_flood_risk.spatial_cv import block_ids_for_cells, spatial_block_cv_metrics  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()


def clean_value(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, np.ndarray):
        return [clean_value(v) for v in value.tolist()]
    if isinstance(value, dict):
        return {str(k): clean_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_value(v) for v in value]
    return value


def file_inventory() -> list[dict]:
    patterns = [
        "data/raw/nyc/*",
        "data/raw/nyc_expanded/*",
        "data/processed/*.parquet",
        "models/nyc_smoke/*",
        "models/nyc_expanded/*",
        "outputs/*",
        "docs/paper/figures/*.png",
        "docs/paper/figures/supplementary/*.png",
        "docs/paper/manuscript.*",
        "docs/paper/report.*",
        "src/pluvial_flood_risk/*.py",
        "scripts/*.py",
        "configs/*.yaml",
    ]
    paths: set[Path] = set()
    for pat in patterns:
        paths.update(p for p in ROOT.glob(pat) if p.is_file())
    rows = []
    for path in sorted(paths):
        stat = path.stat()
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256(path),
            }
        )
    return rows


def git_evidence() -> dict:
    status = run("git", "status", "--porcelain=v1")
    return {
        "head": run("git", "rev-parse", "HEAD"),
        "branch": run("git", "branch", "--show-current"),
        "submission_v2_commit": run("git", "rev-list", "-n", "1", "submission-v2"),
        "submission_v2_object": run("git", "rev-parse", "submission-v2"),
        "dirty": bool(status),
        "dirty_entry_count": len(status.splitlines()) if status else 0,
        "status_porcelain": status.splitlines(),
    }


def manifest_evidence() -> dict:
    result: dict[str, dict] = {}
    for rel in ["data/raw/nyc/DOWNLOAD_MANIFEST.json", "data/raw/nyc_expanded/DOWNLOAD_MANIFEST.json"]:
        path = ROOT / rel
        manifest = json.loads(path.read_text(encoding="utf-8"))
        layer_rows = []
        for layer in manifest.get("layers", []):
            local_value = layer.get("path")
            local = Path(str(local_value)) if local_value else None
            if local is not None and not local.is_absolute():
                local = ROOT / local
            layer_rows.append(
                {
                    "name": layer.get("name"),
                    "status": layer.get("status"),
                    "source": layer.get("source"),
                    "path": str(local) if local is not None else None,
                    "exists": bool(local is not None and local.exists()),
                    "actual_size_bytes": local.stat().st_size if local is not None and local.exists() and local.is_file() else None,
                    "actual_sha256": sha256(local) if local is not None and local.exists() and local.is_file() else None,
                    "has_exact_url_field": any(k in layer for k in ("url", "source_url", "download_url")),
                    "has_license_field": any(k in layer for k in ("license", "licence")),
                    "has_checksum_field": any(k in layer for k in ("sha256", "checksum")),
                    "manifest_detail": layer.get("detail"),
                }
            )
        result[rel] = {
            "started_utc": manifest.get("started_utc"),
            "finished_utc": manifest.get("finished_utc"),
            "bbox": manifest.get("bbox"),
            "assembly_ready": manifest.get("assembly_ready"),
            "layers": layer_rows,
            "all_layers_have_exact_url": all(r["has_exact_url_field"] for r in layer_rows),
            "all_layers_have_license": all(r["has_license_field"] for r in layer_rows),
            "all_layers_have_checksum": all(r["has_checksum_field"] for r in layer_rows),
        }
    return result


def raster_evidence() -> dict:
    import rasterio

    result = {}
    for rel in [
        "data/raw/nyc/dem.tif",
        "data/raw/nyc/impervious.tif",
        "data/raw/nyc/event_rainfall.tif",
        "data/raw/nyc_expanded/dem.tif",
        "data/raw/nyc_expanded/impervious.tif",
        "data/raw/nyc_expanded/event_rainfall.tif",
    ]:
        path = ROOT / rel
        with rasterio.open(path) as ds:
            a = ds.read(1, masked=True)
            vals = a.compressed().astype(float)
            result[rel] = {
                "shape": [ds.height, ds.width],
                "crs": str(ds.crs),
                "bounds": list(ds.bounds),
                "nodata": ds.nodata,
                "valid_count": int(vals.size),
                "min": float(vals.min()) if vals.size else None,
                "max": float(vals.max()) if vals.size else None,
                "mean": float(vals.mean()) if vals.size else None,
                "std": float(vals.std()) if vals.size else None,
                "unique_count": int(np.unique(vals).size) if vals.size else 0,
                "sha256": sha256(path),
            }
    return result


def frame_profile(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(path)
    profile: dict = {
        "rows": len(df),
        "columns": list(df.columns),
        "duplicate_h3": int(df["h3_index"].duplicated().sum()) if "h3_index" in df else None,
        "h3_resolutions": sorted({int(h3.get_resolution(str(c))) for c in df["h3_index"]}) if "h3_index" in df else [],
        "null_counts": {c: int(v) for c, v in df.isna().sum().items() if int(v) > 0},
    }
    for col in ["assembly_mode", "feature_source", "label_source", "rainfall_source", "observed_feature_cols"]:
        if col in df:
            profile[f"unique_{col}"] = sorted(map(str, df[col].dropna().unique().tolist()))
    numeric = df.select_dtypes(include=[np.number])
    profile["numeric_min_max"] = {
        c: {"min": float(numeric[c].min()), "max": float(numeric[c].max()), "std": float(numeric[c].std(ddof=0))}
        for c in numeric.columns
        if len(numeric)
    }
    if {"dep_area_frac", "complaint_count", "ida_hwm_count", "flood_risk"}.issubset(df.columns):
        dep = df["dep_area_frac"].astype(float).clip(0, 1)
        complaint_presence = (df["complaint_count"].astype(float) > 0).astype(float)
        hwm_presence = (df["ida_hwm_count"].astype(float) > 0).astype(float)
        expected = pd.concat([dep, complaint_presence, hwm_presence], axis=1).max(axis=1)
        profile["target_max_rule_mismatch_count"] = int((~np.isclose(expected, df["flood_risk"].astype(float))).sum())
        profile["source_positive_counts"] = {
            "dep_positive": int((dep > 0).sum()),
            "complaint_positive": int((complaint_presence > 0).sum()),
            "hwm_positive": int((hwm_presence > 0).sum()),
            "composite_positive_at_1e_9": int((df["flood_risk"].astype(float) >= 1e-9).sum()),
        }
    if {"flood_risk", "flood_class"}.issubset(df.columns):
        expected_class = (df["flood_risk"].astype(float) >= 1e-9).astype(int)
        profile["class_threshold_mismatch_count"] = int((expected_class != df["flood_class"].astype(int)).sum())
        profile["class_prevalence"] = float(df["flood_class"].mean())
    return df, profile


def oof_profile(df: pd.DataFrame, oof_path: Path, folds_path: Path, k: int = 2) -> dict:
    oof = pd.read_csv(oof_path)
    folds = pd.read_csv(folds_path)
    merged = df[["h3_index", "flood_class", "flood_risk"]].merge(oof, on="h3_index", how="outer", indicator=True)
    group_expected = dict(zip(df["h3_index"].astype(str), block_ids_for_cells(df["h3_index"].astype(str).tolist(), k)))
    fold_rows = []
    for fold_id, sub in oof.groupby("fold_id", sort=True):
        fold_rows.append(
            {
                "fold_id": int(fold_id),
                "n": len(sub),
                "accuracy_recomputed": float(accuracy_score(sub["y_true"], sub["y_pred"])),
                "f1_recomputed": float(f1_score(sub["y_true"], sub["y_pred"], zero_division=0)),
                "blocks": sorted(sub["h3_index"].map(group_expected).unique().tolist()),
            }
        )
    return {
        "rows": len(oof),
        "duplicate_h3": int(oof["h3_index"].duplicated().sum()),
        "merge_status": merged["_merge"].value_counts().to_dict(),
        "y_true_mismatch_count": int((merged.loc[merged["_merge"] == "both", "flood_class"].astype(int) != merged.loc[merged["_merge"] == "both", "y_true"].astype(int)).sum()),
        "oof_contains_regression_predictions": bool({"y_risk_true", "y_risk_pred"}.issubset(oof.columns)),
        "pooled_roc_auc_recomputed": float(roc_auc_score(oof["y_true"], oof["y_proba"])),
        "pooled_average_precision_recomputed": float(average_precision_score(oof["y_true"], oof["y_proba"])),
        "fold_accuracy_mean_recomputed": float(folds["accuracy"].mean()),
        "fold_accuracy_sd0_recomputed": float(folds["accuracy"].std(ddof=0)),
        "fold_f1_mean_recomputed": float(folds["f1"].mean()),
        "fold_f1_sd0_recomputed": float(folds["f1"].std(ddof=0)),
        "fold_r2_mean_recomputed": float(folds["r2"].mean()),
        "fold_r2_sd0_recomputed": float(folds["r2"].std(ddof=0)),
        "folds": fold_rows,
    }


def recompute_spatial_cv(df: pd.DataFrame, k: int = 2, n_splits: int = 5) -> dict:
    x = df[FEATURE_COLUMNS].to_numpy(float)
    y_class = df["flood_class"].to_numpy(int)
    y_risk = df["flood_risk"].to_numpy(float)
    cells = df["h3_index"].astype(str).tolist()
    groups = block_ids_for_cells(cells, k)
    result = spatial_block_cv_metrics(x, y_class, y_risk, groups, n_splits=n_splits, cells=cells)
    result.pop("spatial_cv_oof_table", None)
    result.pop("spatial_cv_fold_table", None)
    return clean_value(result)


def model_profile(model_dir: Path, df: pd.DataFrame) -> dict:
    clf = joblib.load(model_dir / "classifier.joblib")
    reg = joblib.load(model_dir / "regressor.joblib")
    features = joblib.load(model_dir / "feature_columns.joblib")
    gb_clf = clf.named_steps.get("model") or clf.steps[-1][1]
    gb_reg = reg.named_steps.get("model") or reg.steps[-1][1]
    trained_rows_classifier = int(getattr(gb_clf, "n_trees_per_iteration_", 0) or 0)
    # sklearn does not persist n_samples_fit for GradientBoosting; infer the
    # implementation path from train_models and compare stored full-table scores
    # against independently fitted 80% and 100% models.
    x = df[features].to_numpy(float)
    saved_p = clf.predict_proba(x)[:, list(clf.classes_).index(1)]
    saved_r = reg.predict(x)
    from sklearn.model_selection import train_test_split
    from pluvial_flood_risk.config import RANDOM_SEED

    indices = np.arange(len(df))
    tr, _ = train_test_split(indices, test_size=0.2, random_state=RANDOM_SEED, stratify=df["flood_class"].to_numpy(int))
    clf_80 = build_classifier().fit(x[tr], df["flood_class"].to_numpy(int)[tr])
    reg_80 = build_regressor().fit(x[tr], df["flood_risk"].to_numpy(float)[tr])
    clf_100 = build_classifier().fit(x, df["flood_class"].to_numpy(int))
    reg_100 = build_regressor().fit(x, df["flood_risk"].to_numpy(float))
    p80 = clf_80.predict_proba(x)[:, list(clf_80.classes_).index(1)]
    p100 = clf_100.predict_proba(x)[:, list(clf_100.classes_).index(1)]
    r80 = reg_80.predict(x)
    r100 = reg_100.predict(x)
    return {
        "feature_columns": list(features),
        "stored_classifier_classes": list(map(int, clf.classes_)),
        "stored_vs_refit80_max_abs_probability_diff": float(np.max(np.abs(saved_p - p80))),
        "stored_vs_refit100_max_abs_probability_diff": float(np.max(np.abs(saved_p - p100))),
        "stored_vs_refit80_max_abs_regression_diff": float(np.max(np.abs(saved_r - r80))),
        "stored_vs_refit100_max_abs_regression_diff": float(np.max(np.abs(saved_r - r100))),
        "independent_train_rows_80": int(len(tr)),
        "independent_train_rows_100": int(len(df)),
        "rainfall_feature_importance_classifier": float(gb_clf.feature_importances_[list(features).index("rainfall_mm_h")]),
        "rainfall_feature_importance_regressor": float(gb_reg.feature_importances_[list(features).index("rainfall_mm_h")]),
        "sklearn_n_trees_per_iteration": trained_rows_classifier,
    }


def scenario_profile() -> dict:
    path = ROOT / "outputs/pfi_h_scenarios.csv"
    df = pd.read_csv(path)
    per_cell_range = df.groupby("h3_index")["PFI_h"].agg(lambda s: float(s.max() - s.min()))
    return {
        "rows": len(df),
        "unique_cells": int(df["h3_index"].nunique()),
        "scenarios": df.groupby("scenario").agg(rows=("h3_index", "size"), rainfall_mm_h=("rainfall_mm_h", "first"), mean_PFI_h=("PFI_h", "mean")).reset_index().to_dict("records"),
        "max_within_cell_range": float(per_cell_range.max()),
        "nonzero_range_cells": int((per_cell_range > 1e-12).sum()),
        "pfi_min": float(df["PFI_h"].min()),
        "pfi_max": float(df["PFI_h"].max()),
    }


def jaccard_profile() -> dict:
    df = pd.read_csv(ROOT / "outputs/jaccard_by_resolution.csv")
    rows = df.to_dict("records")
    for row in rows:
        row["projected_fine_to_coarse_count_ratio"] = row["n_hotspot_fine_parents"] / row["n_hotspot_coarse"]
    labels = pd.read_parquet(ROOT / "data/processed/nyc_h3_cells_r10_labels.parquet")
    scores = labels["flood_risk"].astype(float)
    k = int(round(0.10 * len(scores)))
    threshold = float(scores.sort_values(ascending=False).iloc[k - 1])
    return {
        "rows": rows,
        "r10_k": k,
        "r10_threshold": threshold,
        "r10_cells_at_or_above_threshold": int((scores >= threshold).sum()),
        "r10_cells_strictly_above_threshold": int((scores > threshold).sum()),
        "r10_ties_at_threshold": int((scores == threshold).sum()),
    }


def png_profile() -> list[dict]:
    rows = []
    for path in sorted((ROOT / "docs/paper/figures").rglob("*.png")):
        with Image.open(path) as im:
            rows.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "width_px": im.width,
                    "height_px": im.height,
                    "mode": im.mode,
                    "sha256": sha256(path),
                }
            )
    return rows


def normalize_words(text: str) -> list[str]:
    text = re.sub(r"https?://\S+", " ", text.lower())
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text)


def body_before_references(text: str) -> str:
    return re.split(r"^##\s+References\s*$", text, maxsplit=1, flags=re.I | re.M)[0]


def similarity_profile() -> dict:
    manuscript = body_before_references((ROOT / "docs/paper/manuscript.md").read_text(encoding="utf-8"))
    reference = (ROOT / "1-s2.0-S2212420926001032-main.md").read_text(encoding="utf-8", errors="replace")
    mw = normalize_words(manuscript)
    rw = normalize_words(reference)
    n = 10
    mgrams = {tuple(mw[i : i + n]) for i in range(len(mw) - n + 1)}
    rgrams = {tuple(rw[i : i + n]) for i in range(len(rw) - n + 1)}
    overlaps = sorted(mgrams & rgrams)

    def paragraphs(t: str) -> list[str]:
        return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", t) if len(normalize_words(p)) >= 30]

    mp, rp = paragraphs(manuscript), paragraphs(reference)
    best = []
    for i, a in enumerate(mp):
        aw = " ".join(normalize_words(a))
        scores = []
        for j, b in enumerate(rp):
            bw = " ".join(normalize_words(b))
            scores.append((SequenceMatcher(None, aw, bw).ratio(), j, b))
        score, j, b = max(scores, default=(0.0, -1, ""))
        best.append({"manuscript_paragraph": i, "reference_paragraph": j, "similarity": score, "manuscript_excerpt": a[:240], "reference_excerpt": b[:240]})
    best.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "method": "case-folded alphanumeric tokens; manuscript body excludes reference list",
        "exact_10_word_overlap_count": len(overlaps),
        "exact_10_word_overlaps": [" ".join(x) for x in overlaps[:50]],
        "top_paragraph_matches": best[:15],
        "caveat": "This checks only the supplied reference PDF/Markdown and cannot prove originality against all external literature.",
    }


def metadata_profile() -> dict:
    out = {}
    for rel in ["models/nyc_smoke/run_metadata.json", "models/nyc_expanded/run_metadata.json"]:
        p = ROOT / rel
        data = json.loads(p.read_text(encoding="utf-8"))
        out[rel] = data
    out["current_environment"] = {
        "python": sys.version,
        "h3": getattr(h3, "__version__", "unknown"),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sklearn": __import__("sklearn").__version__,
    }
    return out


def main() -> None:
    inv = file_inventory()
    pd.DataFrame(inv).to_csv(OUT / "file_sha256_inventory.csv", index=False, encoding="utf-8-sig")

    frames = {}
    dfs = {}
    for name, rel in {
        "lower_manhattan": "data/processed/nyc_h3_cells.parquet",
        "expanded": "data/processed/nyc_h3_cells_expanded.parquet",
        "r10_labels": "data/processed/nyc_h3_cells_r10_labels.parquet",
    }.items():
        dfs[name], frames[name] = frame_profile(ROOT / rel)

    checks = {
        "generated_utc": pd.Timestamp.now("UTC").isoformat(),
        "git": git_evidence(),
        "metadata": metadata_profile(),
        "manifests": manifest_evidence(),
        "rasters": raster_evidence(),
        "processed_tables": frames,
        "oof": {
            "lower_manhattan": oof_profile(dfs["lower_manhattan"], ROOT / "models/nyc_smoke/spatial_cv_oof_predictions.csv", ROOT / "models/nyc_smoke/spatial_cv_folds.csv"),
            "expanded": oof_profile(dfs["expanded"], ROOT / "models/nyc_expanded/spatial_cv_oof_predictions.csv", ROOT / "models/nyc_expanded/spatial_cv_folds.csv"),
        },
        "spatial_cv_independent_recompute": {
            "lower_manhattan": recompute_spatial_cv(dfs["lower_manhattan"]),
            "expanded": recompute_spatial_cv(dfs["expanded"]),
        },
        "saved_model_identity": {
            "lower_manhattan": model_profile(ROOT / "models/nyc_smoke", dfs["lower_manhattan"]),
            "expanded": model_profile(ROOT / "models/nyc_expanded", dfs["expanded"]),
        },
        "rainfall_scenarios": scenario_profile(),
        "scale_diagnostic": jaccard_profile(),
        "figure_files": png_profile(),
        "manuscript_reference_similarity": similarity_profile(),
        "file_inventory_count": len(inv),
    }
    (OUT / "audit_evidence.json").write_text(json.dumps(clean_value(checks), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "evidence": str(OUT / "audit_evidence.json"),
        "inventory": str(OUT / "file_sha256_inventory.csv"),
        "lm_cv": checks["spatial_cv_independent_recompute"]["lower_manhattan"],
        "expanded_cv": checks["spatial_cv_independent_recompute"]["expanded"],
        "model_identity": checks["saved_model_identity"],
        "similarity": checks["manuscript_reference_similarity"],
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
