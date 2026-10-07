"""对当前修订版的数据、模型、OOF 评价与尺度图口径做只读核验。

该脚本不修改原数据、模型或论文，仅在当前目录写出 JSON 证据。
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import h3
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score

from pluvial_flood_risk.figures import _pairwise_hotspot_jaccard, _resolution_rollups
from pluvial_flood_risk.model import fit_deployment_models, training_h3_sha256
from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def frame_audit(path: Path) -> dict:
    df = pd.read_parquet(path)
    out: dict = {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "h3_unique": int(df["h3_index"].astype(str).nunique()),
        "h3_resolution_counts": {
            str(k): int(v)
            for k, v in pd.Series([h3.get_resolution(str(x)) for x in df["h3_index"]])
            .value_counts()
            .sort_index()
            .items()
        },
        "duplicate_h3": int(df["h3_index"].astype(str).duplicated().sum()),
        "null_counts": {k: int(v) for k, v in df.isna().sum().items() if int(v) > 0},
    }
    for col in ("assembly_mode", "data_mode", "feature_source", "rainfall_source"):
        if col in df:
            out[f"{col}_counts"] = {str(k): int(v) for k, v in df[col].value_counts(dropna=False).items()}
    if "synthetic_feature_count" in df:
        out["synthetic_feature_count_sum"] = int(df["synthetic_feature_count"].sum())
        out["synthetic_feature_count_max"] = int(df["synthetic_feature_count"].max())
    if "rainfall_mm_h" in df:
        out["rainfall_unique"] = sorted(float(x) for x in df["rainfall_mm_h"].dropna().unique())
        out["rainfall_variance"] = float(df["rainfall_mm_h"].var(ddof=0))
    if "flood_class" in df:
        out["positive_cells"] = int(df["flood_class"].sum())
        out["positive_prevalence"] = float(df["flood_class"].mean())
    if {"flood_risk", "dep_area_frac", "complaint_presence", "ida_hwm_presence"}.issubset(df.columns):
        expected = np.maximum.reduce(
            [
                df["dep_area_frac"].to_numpy(float),
                df["complaint_presence"].to_numpy(float),
                df["ida_hwm_presence"].to_numpy(float),
            ]
        )
        out["composite_formula_max_abs_error"] = float(
            np.max(np.abs(df["flood_risk"].to_numpy(float) - expected))
        )
        expected_class = (expected >= 1e-9).astype(int)
        out["class_formula_mismatch_count"] = int(
            np.sum(df["flood_class"].to_numpy(int) != expected_class)
        )
        out["source_positive_cells"] = {
            "dep": int((df["dep_area_frac"] > 0).sum()),
            "complaint": int((df["complaint_presence"] > 0).sum()),
            "ida_hwm": int((df["ida_hwm_presence"] > 0).sum()),
        }
    return out


def oof_audit(table_path: Path, oof_path: Path, folds_path: Path) -> dict:
    table = pd.read_parquet(table_path)
    oof = pd.read_csv(oof_path)
    folds = pd.read_csv(folds_path)
    y = oof["y_true"].to_numpy(int)
    score_col = "y_score" if "y_score" in oof.columns else "y_proba"
    score = oof[score_col].to_numpy(float)
    pred = oof["y_pred"].to_numpy(int)
    return {
        "table_path": str(table_path.relative_to(ROOT)),
        "oof_path": str(oof_path.relative_to(ROOT)),
        "oof_sha256": sha256(oof_path),
        "folds_sha256": sha256(folds_path),
        "rows": int(len(oof)),
        "h3_unique": int(oof["h3_index"].astype(str).nunique()),
        "h3_set_matches_table": set(oof["h3_index"].astype(str))
        == set(table["h3_index"].astype(str)),
        "accuracy_pooled": float(accuracy_score(y, pred)),
        "f1_pooled": float(f1_score(y, pred, zero_division=0)),
        "roc_auc_pooled": float(roc_auc_score(y, score)),
        "average_precision_pooled": float(average_precision_score(y, score)),
        "positive_prevalence": float(y.mean()),
        "fold_rows": int(len(folds)),
        "fold_accuracy_mean": float(folds["accuracy"].mean()),
        "fold_accuracy_std_ddof0": float(folds["accuracy"].std(ddof=0)),
        "fold_f1_mean": float(folds["f1"].mean()),
        "fold_r2_mean": float(folds["r2"].mean()),
        "fold_r2_std_ddof0": float(folds["r2"].std(ddof=0)),
        "fold_mae_mean": float(folds["mae"].mean()),
        "fold_mae_std_ddof0": float(folds["mae"].std(ddof=0)),
    }


def deployment_audit(table_path: Path, model_dir: Path) -> dict:
    df = pd.read_parquet(table_path)
    manifest_path = model_dir / "deployment" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feature_cols = json.loads(
        (model_dir / "deployment" / "feature_columns.json").read_text(encoding="utf-8")
    )
    saved = joblib.load(model_dir / "deployment" / "classifier_full.joblib")
    seed = int(manifest["random_seed"])
    independent = fit_deployment_models(
        df[feature_cols].to_numpy(),
        df["flood_class"].to_numpy(),
        df["flood_risk"].to_numpy(),
        df["h3_index"].astype(str).tolist(),
        random_seed=seed,
    )
    saved_score = saved.predict_proba(df[feature_cols].to_numpy())[:, 1]
    independent_score = independent.classifier.predict_proba(df[feature_cols].to_numpy())[:, 1]
    return {
        "manifest": manifest,
        "manifest_sha256": sha256(manifest_path),
        "classifier_sha256": sha256(model_dir / "deployment" / "classifier_full.joblib"),
        "fit_rows_matches": int(manifest["fit_rows"]) == len(df),
        "h3_hash_matches": manifest["training_h3_sha256"]
        == training_h3_sha256(df["h3_index"].astype(str).tolist()),
        "independent_refit_prediction_max_abs_error": float(
            np.max(np.abs(saved_score - independent_score))
        ),
        "manifest_has_config_hash": any("config" in str(k).lower() for k in manifest),
        "manifest_has_feature_value_hash": any(
            "feature" in str(k).lower() and "hash" in str(k).lower() for k in manifest
        ),
        "manifest_has_raw_input_hashes": any(
            "raw" in str(k).lower() and "hash" in str(k).lower() for k in manifest
        ),
    }


def hotspot_audit(path: Path) -> dict:
    df = pd.read_parquet(path)
    ladder = resolution_ladder_topk_diagnostics(
        df, value_col="flood_risk", resolutions=[8, 9, 10], hotspot_budget=0.10
    )
    s10 = df.set_index("h3_index")["flood_risk"]
    s9 = _resolution_rollups(s10, 9)
    s8 = _resolution_rollups(s10, 8)
    table_rows = ladder[
        [
            "coarse_res",
            "aggregation",
            "jaccard",
            "jaccard_soft",
            "k_fine",
            "k_coarse",
            "n_hotspot_fine",
            "n_hotspot_fine_parents",
            "n_hotspot_coarse",
            "fine_hotspot_area_m2",
            "target_parent_area_m2",
        ]
    ].to_dict(orient="records")
    support_area = {}
    for res in (8, 9):
        row = ladder[(ladder["coarse_res"] == res) & (ladder["aggregation"] == "mean")].iloc[0]
        # The positive-weight fine set is the hard support used by hard Jaccard.
        from pluvial_flood_risk.rollups import hotspot_weights_topk

        k = int(row["k_fine"])
        weights, _ = hotspot_weights_topk(s10.index.tolist(), s10.to_numpy(float), k)
        parents = {h3.cell_to_parent(c, res) for c, w in weights.items() if w > 0}
        area = float(sum(h3.cell_area(p, unit="m^2") for p in parents))
        support_area[str(res)] = {
            "hard_parent_support_cells": len(parents),
            "hard_parent_support_area_m2": area,
            "implemented_target_area_m2": float(row["target_parent_area_m2"]),
            "implemented_target_to_support_area_ratio": float(
                row["target_parent_area_m2"] / area
            ),
        }
    return {
        "r10_rows": int(len(df)),
        "r10_score_one_count": int(np.isclose(df["flood_risk"], 1.0).sum()),
        "r10_score_zero_count": int(np.isclose(df["flood_risk"], 0.0).sum()),
        "table_rows": table_rows,
        "figure_pairwise_hard_jaccard_current_code": {
            "R10_R9": float(_pairwise_hotspot_jaccard(s10, s9, budget=0.10)),
            "R10_R8": float(_pairwise_hotspot_jaccard(s10, s8, budget=0.10)),
            "R9_R8": float(_pairwise_hotspot_jaccard(s9, s8, budget=0.10)),
        },
        "parent_support_area_check": support_area,
    }


def main() -> None:
    manifest = json.loads((ROOT / "data/raw/data_manifest.json").read_text(encoding="utf-8"))
    raw_checks = []
    for layer in manifest["layers"]:
        path = ROOT / layer["path"]
        raw_checks.append(
            {
                "layer": layer["layer"],
                "path": layer["path"],
                "exists": path.exists(),
                "size_matches": path.stat().st_size == int(layer["size_bytes"]),
                "sha256_matches": sha256(path) == layer["sha256"],
                "official_identity_verified": layer["official_identity_verified"],
                "mirror_status": layer["mirror_status"],
                "manifest_retrieved_utc": layer["retrieved_utc"],
            }
        )

    status = git("status", "--porcelain").splitlines()
    evidence = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "root": str(ROOT),
            "head": git("rev-parse", "HEAD"),
            "head_commit_time": git("log", "-1", "--format=%cI"),
            "dirty": bool(status),
            "dirty_path_count": len(status),
            "status": status,
        },
        "raw_manifest": {
            "path": "data/raw/data_manifest.json",
            "sha256": sha256(ROOT / "data/raw/data_manifest.json"),
            "all_sizes_match": all(x["size_matches"] for x in raw_checks),
            "all_hashes_match": all(x["sha256_matches"] for x in raw_checks),
            "checks": raw_checks,
            "expanded_paths_covered": any("nyc_expanded" in x["path"] for x in raw_checks),
        },
        "processed": {
            "lower_manhattan": frame_audit(ROOT / "data/processed/nyc_h3_cells.parquet"),
            "expanded": frame_audit(ROOT / "data/processed/nyc_h3_cells_expanded.parquet"),
            "r10_labels": frame_audit(ROOT / "data/processed/nyc_h3_cells_r10_labels.parquet"),
        },
        "oof": {
            "lower_manhattan": oof_audit(
                ROOT / "data/processed/nyc_h3_cells.parquet",
                ROOT / "models/nyc_smoke/spatial_cv_oof_predictions.csv",
                ROOT / "models/nyc_smoke/spatial_cv_folds.csv",
            ),
            "expanded": oof_audit(
                ROOT / "data/processed/nyc_h3_cells_expanded.parquet",
                ROOT / "models/nyc_expanded/spatial_cv_oof_predictions.csv",
                ROOT / "models/nyc_expanded/spatial_cv_folds.csv",
            ),
        },
        "deployment": {
            "lower_manhattan": deployment_audit(
                ROOT / "data/processed/nyc_h3_cells.parquet", ROOT / "models/nyc_smoke"
            ),
            "expanded": deployment_audit(
                ROOT / "data/processed/nyc_h3_cells_expanded.parquet", ROOT / "models/nyc_expanded"
            ),
        },
        "hotspot": hotspot_audit(ROOT / "data/processed/nyc_h3_cells_r10_labels.parquet"),
    }
    out = HERE / "current_revision_evidence.json"
    out.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
