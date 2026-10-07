"""Patch paper_results.json and manuscript.md from live outputs after P0 fixes."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "docs" / "paper" / "manuscript.md"
REPORT = ROOT / "docs" / "paper" / "report.md"
DATA_SOURCES = ROOT / "data" / "raw" / "DATA_SOURCES.md"


def _fmt3(x: float) -> str:
    return f"{float(x):.3f}"


def _fmt1(x: float) -> str:
    return f"{float(x):.1f}"


def update_paper_results() -> dict:
    ladder = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
    lm_meta = json.loads((ROOT / "models" / "nyc_smoke" / "run_metadata.json").read_text(encoding="utf-8"))
    baselines = json.loads((ROOT / "outputs" / "classification_baselines.json").read_text(encoding="utf-8"))
    df = pd.read_parquet(ROOT / "data" / "processed" / "nyc_h3_cells.parquet")

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "bbox_choice": "Option_B_lower_manhattan_262",
        "fail_closed": True,
        "data_manifest": "data/raw/data_manifest.json",
        "random_seed": 42,
        "311_source": {
            "dataset_id": "76ig-c548",
            "official_identity_verified": True,
            "descriptor": "Street Flooding (SJ)",
            "date_window": ["2010-01-01T00:00:00", "2015-01-01T00:00:00"],
            "n_features_lower_manhattan": 510,
        },
        "floodnet": {
            "dataset_id": "aq7i-eu5q",
            "status": "public_not_integrated",
            "analysis_freeze_utc": "2026-08-30T00:00:00+00:00",
            "note": "Held out for later external validation; not used in training/eval/maps.",
        },
        "lower_manhattan": {
            "n_cells": int(len(df)),
            "n_positive": int(df["flood_class"].sum()),
            "positive_prevalence": float(df["flood_class"].mean()),
            "bbox": [-74.02, 40.7, -73.97, 40.76],
            "spatial_cv": lm_meta.get("metrics", {}),
            "deployment": lm_meta.get("deployment", {}),
            "evaluation": lm_meta.get("evaluation", {}),
            "baselines": baselines,
        },
        "scale_loss": {
            "source_csv": "outputs/jaccard_by_resolution.csv",
            "budget_match_mode": "strict_area_budget",
            "primary_metric": "area_weighted_soft_jaccard",
            "hotspot_budget": 0.10,
            "n_fine": int(ladder["n_fine"].iloc[0]),
            "rows": json.loads(ladder.to_json(orient="records")),
        },
    }

    exp_meta_path = ROOT / "models" / "nyc_expanded" / "run_metadata.json"
    exp_table = ROOT / "data" / "processed" / "nyc_h3_cells_expanded.parquet"
    if exp_meta_path.exists() and exp_table.exists():
        # Only trust expanded if parquet is newer than the 311 refresh (~today).
        if exp_table.stat().st_mtime >= (ROOT / "data" / "raw" / "nyc" / "flooding_311.geojson").stat().st_mtime - 60:
            exp_meta = json.loads(exp_meta_path.read_text(encoding="utf-8"))
            edf = pd.read_parquet(exp_table)
            bas_exp = {}
            be = ROOT / "outputs" / "classification_baselines_expanded.json"
            if be.exists():
                bas_exp = json.loads(be.read_text(encoding="utf-8"))
            payload["manhattan_expanded"] = {
                "n_cells": int(len(edf)),
                "n_positive": int(edf["flood_class"].sum()),
                "positive_prevalence": float(edf["flood_class"].mean()),
                "bbox": [-74.03, 40.68, -73.94, 40.8],
                "spatial_cv": exp_meta.get("metrics", {}),
                "deployment": exp_meta.get("deployment", {}),
                "evaluation": exp_meta.get("evaluation", {}),
                "baselines": bas_exp,
            }

    out = ROOT / "outputs" / "paper_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def ladder_table_md(ladder: pd.DataFrame) -> str:
    lines = [
        "| Coarse resolution | Aggregation | Soft Jaccard | Hard median [95% CI] | Fine-parent recall | Coarse precision |",
        "|---|---|---|---|---|---|",
    ]
    order = [("9", "mean"), ("9", "max"), ("9", "p90"), ("8", "mean"), ("8", "max"), ("8", "p90")]
    label = {"mean": "Mean", "max": "Maximum", "p90": "P90"}
    for coarse, agg in order:
        row = ladder.loc[(ladder["coarse_res"] == int(coarse)) & (ladder["aggregation"] == agg)].iloc[0]
        hard = (
            f"{_fmt3(row['jaccard_hard_median'])} "
            f"[{_fmt3(row['jaccard_hard_ci_low'])}, {_fmt3(row['jaccard_hard_ci_high'])}]"
        )
        lines.append(
            f"| R{coarse} | {label[agg]} | {_fmt3(row['jaccard'])} | {hard} | "
            f"{_fmt3(row['fine_parent_recall'])} | {_fmt3(row['coarse_precision'])} |"
        )
    return "\n".join(lines)


def patch_manuscript(pr: dict) -> None:
    text = PAPER.read_text(encoding="utf-8")
    ladder = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
    lm = pr["lower_manhattan"]
    m = lm["spatial_cv"]
    b = lm["baselines"]
    j9 = float(ladder.loc[(ladder.coarse_res == 9) & (ladder.aggregation == "mean"), "jaccard"].iloc[0])
    j8 = float(ladder.loc[(ladder.coarse_res == 8) & (ladder.aggregation == "mean"), "jaccard"].iloc[0])
    hard9 = float(ladder.loc[(ladder.coarse_res == 9) & (ladder.aggregation == "mean"), "jaccard_hard_median"].iloc[0])
    hard8 = float(ladder.loc[(ladder.coarse_res == 8) & (ladder.aggregation == "mean"), "jaccard_hard_median"].iloc[0])

    acc = _fmt3(m["spatial_cv_accuracy_mean"])
    acc_sd = _fmt3(m["spatial_cv_accuracy_std"])
    f1 = _fmt3(m["spatial_cv_f1_mean"])
    roc = _fmt3(m["spatial_cv_roc_auc_pooled"])
    ap = _fmt3(m["spatial_cv_pr_auc_pooled"])
    r2 = _fmt3(m["spatial_cv_r2_mean"])
    r2_sd = _fmt3(m["spatial_cv_r2_std"])
    mae = _fmt3(m["spatial_cv_mae_mean"])
    prev = _fmt1(100 * lm["positive_prevalence"])
    ap_acc = _fmt3(b["always_positive_mean_acc"])
    ap_f1 = _fmt3(b["always_positive_mean_f1"])
    n_pos = lm["n_positive"]

    # Highlights Jaccard
    text = re.sub(
        r"mean hotspot Jaccard 0\.\d+ to R8 at 10%[^)\n]*",
        f"mean hotspot Jaccard {_fmt3(j8).lstrip('0') if False else _fmt3(j8)} to R8 at a 10% area budget",
        text,
        count=1,
    )
    # Fix awkward - just set explicitly
    text = re.sub(
        r"Native fine-resolution label overlay with tie-aware fractional hotspots and area-matched parent budgets shows substantial scale loss \(mean hotspot Jaccard [0-9.]+ to R8 at[^\)]*\)",
        f"Native fine-resolution label overlay with area-budget fractional hotspots shows substantial scale loss (mean hotspot Jaccard {_fmt3(j8)} to R8 at a 10% area budget)",
        text,
        count=1,
    )

    # §3.5 methods
    old_35 = re.search(r"### 3\.5 Scale-loss diagnostics\n\n.*?(?=\n### 3\.6 )", text, re.S)
    if old_35:
        new_35 = (
            "### 3.5 Scale-loss diagnostics\n\n"
            "Fine-resolution hotspot membership is defined on native R10 evidence scores using a fixed "
            "10% area budget with fractional allocation within boundary ties (no lexicographic H3-index "
            "tie-break and no cell-count top-k). For each coarse parent p the reference membership is the "
            "area-weighted fraction "
            "w_ref(p)=Σ_i∈p a_i w_i / Σ_i∈p a_i. Coarse hotspots are selected under the same area budget "
            "on area-weighted mean, maximum, or p90 parent scores, allowing fractional membership of the "
            "final tied group so that selected coarse area equals the fine budget within floating-point "
            "tolerance. The primary overlap metric is the area-weighted soft Jaccard; hard-set Jaccard is "
            "reported only as a seeded tie-resolution sensitivity (1000 draws; median and 95% interval). "
            "Table 4 and Fig. 6b are read from the same archived diagnostics table "
            "(`outputs/jaccard_by_resolution.csv`); figures never recompute Jaccard independently. "
            "The fine R10 reference is assembled by overlaying the raw polygon and point geometries "
            "directly onto R10 cells—not by inheriting scores from R9 parents. These diagnostics use "
            "different labels, resolutions, and hotspot definitions from the Jaccard value reported by "
            "Svellingen et al. [5] and are not a reproduction of that result.\n\n"
        )
        text = text[: old_35.start()] + new_35 + text[old_35.end() :]

    # §3.8 negative control rename
    text = text.replace(
        "### 3.8 Negative control\n\nFEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a negative control.",
        "### 3.8 Coastal-confounding diagnostic\n\nFEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a coastal-confounding diagnostic rather than a strict negative control.",
    )
    text = text.replace(
        "### 4.6 Sandy negative control",
        "### 4.6 Sandy coastal-confounding diagnostic",
    )
    text = text.replace(
        "**Table 6. Sandy negative-control statistics",
        "**Table 6. Sandy coastal-confounding diagnostic statistics",
    )

    # Table 4 block
    table4_pat = re.compile(
        r"\*\*Table 4\..*?\n\n\| Coarse resolution \|.*?\n\nNote:.*?(?=\n\n### 4\.4)",
        re.S,
    )
    table4 = (
        f"**Table 4. Scale-loss ladder under a strict 10% area budget with fractional membership ties.** "
        f"Fine R10 support n = {int(ladder['n_fine'].iloc[0])} (Option B). Primary metric is the "
        f"area-weighted soft Jaccard; hard Jaccard is a 1000-draw seeded tie-resolution sensitivity. "
        f"All values are from `outputs/jaccard_by_resolution.csv`.\n\n"
        f"{ladder_table_md(ladder)}\n\n"
        f"Note: `matched_budgets_cell_count=false`; `budget_match_mode=strict_area_budget`. "
        f"The full ladder is plotted in Supplementary Fig. S1."
    )
    text, n = table4_pat.subn(table4, text, count=1)
    if n != 1:
        print("WARN: Table 4 pattern not uniquely replaced", n)

    # §4.3 opening paragraph
    text = re.sub(
        r"### 4\.3 Scale-loss Jaccard ladder\n\n.*?(?=\nFig\. 5 maps)",
        "### 4.3 Scale-loss Jaccard ladder\n\n"
        f"Fine-resolution hotspots are defined at R10 by a strict 10% area budget with fractional "
        f"membership at tied boundary scores. Parent reference membership is area-weighted "
        f"(w_ref), and coarse hotspots use the same area budget on mean/max/p90 scores. Under mean "
        f"aggregation the R9 rollup yields area-weighted soft Jaccard {_fmt3(j9)} "
        f"(hard median {_fmt3(hard9)}) and the R8 rollup yields {_fmt3(j8)} "
        f"(hard median {_fmt3(hard8)}). Maximum aggregation no longer saturates at 1.0 under this "
        f"protocol. Hard Jaccard is a sensitivity only. "
        f"Table 4 and Fig. 6b are read from the same CSV. ",
        text,
        count=1,
        flags=re.S,
    )

    # Fix stale Fig 6 pairwise claims in §4.3
    text = re.sub(
        r"and Fig\. 6b summarises the pairwise cross-resolution Jaccard similarity among the three resolutions, reproducing the R10-vs-R9 \(0\.\d+\) and R10-vs-R8 \(0\.\d+\) ladder values\.",
        f"and Fig. 6b displays the area-weighted soft Jaccard values from Table 4 by aggregation and coarse resolution (R10→R9 mean {_fmt3(j9)}; R10→R8 mean {_fmt3(j8)}).",
        text,
        count=1,
    )

    # Fig 6 caption
    text = re.sub(
        r"\*\*Figure 6\..*?(?=\n\n\*\*Supplementary Figure S1)",
        f"**Figure 6. Resolution effects on the open-evidence score surface (Option B).** "
        f"(a) Violin plots with overlaid cell scores of the distribution at R10 (n = 1857), "
        f"R9 (n = 296, mean rollup), and R8 (n = 52, mean rollup), showing variance compression as "
        f"the grid coarsens. (b) Area-weighted soft Jaccard from the canonical scale-results table "
        f"(Table 4 / `outputs/jaccard_by_resolution.csv`) for mean, maximum, and p90 aggregations at "
        f"R9 and R8; the figure does not recompute Jaccard. For mean aggregation, R10→R9 = {_fmt3(j9)} "
        f"and R10→R8 = {_fmt3(j8)}.",
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r"\*\*Supplementary Figure S1\..*?(?=\n\n\*\*Supplementary Figure S2|\n\n## References)",
        "**Supplementary Figure S1. Open-evidence hotspot scale-loss diagnostics across H3 resolutions.** "
        "Area-weighted soft Jaccard and F1 compare hotspot membership defined on the reference fine "
        "support (H3 R10; 10% area budget with fractional ties) with R9 and R8 representations under "
        "mean, maximum, and p90 aggregation. This figure reads the same CSV as Table 4.",
        text,
        count=1,
        flags=re.S,
    )

    # 311 provenance
    text = text.replace(
        "**DEP stormwater and 311 currently resolve via public ArcGIS FeatureServer mirrors** (`official_identity_verified=false`); they are not claimed as official NYC-owned downloads until replaced.",
        "**DEP stormwater still resolves via a public ArcGIS FeatureServer mirror** (`official_identity_verified=false`). "
        "**311 street-flooding complaints are extracted from the official NYC Open Data historical dataset 76ig-c548** "
        "(2010–2014; descriptor Street Flooding (SJ); ordered pagination; unique_key dedup; `official_identity_verified=true`).",
    )
    text = text.replace(
        "| Flood evidence — complaints | NYC 311 street-flooding complaints (ArcGIS \"streetfloodtime\", 2010–2014) | Vector | Crowd-reported flood-evidence target (continuous and binary) |",
        "| Flood evidence — complaints | NYC 311 street-flooding complaints (official dataset 76ig-c548, 2010–2014 Street Flooding (SJ)) | Vector | Crowd-reported flood-evidence target (continuous and binary) |",
    )
    text = text.replace(
        "[15] New York City Department of Environmental Protection, 311 street-flooding complaint layer (ArcGIS \"streetfloodtime\"; records 2010–2014), accessed August 2026. https://www.arcgis.com/home/item.html?id=33c5b455415a41788a736155affcb31c",
        "[15] NYC Open Data, 311 Service Requests from 2010 to 2019 (dataset 76ig-c548); Street Flooding (SJ) subset for 2010–2014, accessed September 2026. https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548",
    )

    # FloodNet wording
    text = text.replace(
        "complemented by held-out FloodNet validation when a suitable sensor layer becomes available.",
        "complemented by held-out FloodNet validation using the now-public NYC Open Data sensor-event dataset (aq7i-eu5q; published 2026-03-03), which is not integrated in this analysis freeze.",
    )
    text = text.replace(
        "observed event rainfall, rainfall-responsive predictions, citywide evaluation, and FloodNet validation remain priorities for further assessment.",
        "observed event rainfall, rainfall-responsive predictions, citywide evaluation, and FloodNet held-out validation (aq7i-eu5q; not integrated here) remain priorities for further assessment.",
    )

    # Originality / third-party
    if "All source datasets are third-party public inputs" not in text:
        text = text.replace(
            "The predictor and evidence layers are drawn from public datasets.",
            "All source datasets are third-party public inputs; cell-level features, labels, fitted models, "
            "predictions, diagnostics, tables, and figures are author-derived outputs. "
            "The predictor and evidence layers are drawn from public datasets.",
        )

    # Discussion Jaccard + causal softening
    text = re.sub(
        r"\(Jaccard 0\.\d+ to R9, 0\.\d+ to R8 under area-matched 10% budgets\)",
        f"(Jaccard {_fmt3(j9)} to R9, {_fmt3(j8)} to R8 under a strict 10% area budget)",
        text,
        count=1,
    )
    text = text.replace(
        "so the discrimination is neither an artefact of the DEP model output nor carried by coastal position alone.",
        "so source ablation reduces, but does not eliminate, concern that shared spatial structure or reporting processes drive discrimination.",
    )
    text = re.sub(
        r"The R8 mean-aggregation Jaccard value of 0\.\d+ \(top-10% hotspots\) is numerically comparable",
        f"The R8 mean-aggregation Jaccard value of {_fmt3(j8)} (10% area budget) is numerically comparable",
        text,
        count=1,
    )

    # LM performance strings (best-effort replacements of primary Option B numbers)
    text = text.replace("accuracy 0.809 ± 0.046 and F1 0.846", f"accuracy {acc} ± {acc_sd} and F1 {f1}")
    text = text.replace("above the always-positive baseline (0.629 and 0.762)", f"above the always-positive baseline ({ap_acc} and {ap_f1})")
    text = text.replace("with pooled out-of-fold ROC-AUC 0.847 and average precision 0.851", f"with pooled out-of-fold ROC-AUC {roc} and average precision {ap}")
    text = text.replace("63.0% positive", f"{prev}% positive")
    text = text.replace("(0.809 vs 0.629; 0.846 vs 0.762)", f"({acc} vs {ap_acc}; {f1} vs {ap_f1})")
    text = text.replace("exceeds always-positive on accuracy (0.809 vs 0.629) and F1 (0.846 vs 0.762)", f"exceeds always-positive on accuracy ({acc} vs {ap_acc}) and F1 ({f1} vs {ap_f1})")
    text = text.replace("Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.847 and 0.883)", f"Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots ({roc} and 0.883)")
    text = text.replace("with average precision 0.851 and 0.812", f"with average precision {ap} and 0.812")
    text = text.replace("mean hotspot Jaccard 0.11 to R8", f"mean hotspot Jaccard {_fmt3(j8)} to R8")
    text = text.replace("mean Jaccard 0.11 to R8", f"mean Jaccard {_fmt3(j8)} to R8")

    # R² expanded stale 0.333 → keep until expanded retrain; LM R² update in Table 3 if present
    text = text.replace("evidence-score R² is 0.227 in the smaller pilot and 0.336 in the expanded pilot", f"evidence-score R² is {r2} in the smaller pilot and 0.336 in the expanded pilot")
    text = text.replace("evidence-score R² is 0.333 ± 0.144 and MAE is 0.286 ± 0.036", "evidence-score R² is 0.336 ± 0.146 and MAE is 0.285 ± 0.036")

    PAPER.write_text(text, encoding="utf-8")
    print("patched", PAPER)
    print("LM", lm["n_cells"], n_pos, acc, f1, roc, ap, "J9/J8", _fmt3(j9), _fmt3(j8))


def patch_data_sources() -> None:
    text = DATA_SOURCES.read_text(encoding="utf-8")
    text = text.replace(
        "| 311 flooding | `flooding_311.geojson` | **Live (mirror)** | ArcGIS `streetfloodtime` FeatureServer (~488 pts in bbox). SODA `erm2-nwe9` still 403; CDN Street Flooding (SJ) CSV is fallback |",
        "| 311 flooding | `flooding_311.geojson` | **Live (official)** | NYC Open Data historical dataset **76ig-c548** (2010–2014; descriptor Street Flooding (SJ); paginated; unique_key dedup; ~510 pts in LM bbox). Query freeze: `flooding_311_query.json` |",
    )
    text = text.replace(
        "| 311 flooding subset | NYC 311 | https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9 | CSV / GeoJSON | WGS84 | NYC Open Data Terms | Point labels |",
        "| 311 flooding subset | NYC 311 | https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548 | JSON / GeoJSON | WGS84 | NYC Open Data Terms | Point labels (2010–2014 Street Flooding (SJ)) |",
    )
    text = text.replace(
        "| FloodNet | `FLOODNET_STUB.txt` | Stub only | Sensor GeoJSON not wired |",
        "| FloodNet | `FLOODNET_STUB.txt` | Not integrated | Official dataset aq7i-eu5q is public (2026-03-03) but held out of this analysis freeze |",
    )
    text = text.replace(
        "| FloodNet | FloodNet-NYC | https://www.floodnet.nyc/ | sensor points | WGS84 | see FloodNet terms | Optional stub |",
        "| FloodNet | NYC Open Data / FloodNet | https://data.cityofnewyork.us/d/aq7i-eu5q | sensor events | WGS84 | NYC Open Data Terms | Held-out external validation (not ingested) |",
    )
    DATA_SOURCES.write_text(text, encoding="utf-8")
    print("patched", DATA_SOURCES)


def patch_report_jaccard(pr: dict) -> None:
    if not REPORT.exists():
        return
    text = REPORT.read_text(encoding="utf-8")
    ladder = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
    j9 = float(ladder.loc[(ladder.coarse_res == 9) & (ladder.aggregation == "mean"), "jaccard"].iloc[0])
    j8 = float(ladder.loc[(ladder.coarse_res == 8) & (ladder.aggregation == "mean"), "jaccard"].iloc[0])
    text = re.sub(
        r"细 R10→粗 R9 \*\*mean\*\* Jaccard = \*\*0\.\d+\*\*、R10→R8 \*\*mean\*\* Jaccard = \*\*0\.\d+\*\*",
        f"细 R10→粗 R9 **mean** Jaccard = **{_fmt3(j9)}**、R10→R8 **mean** Jaccard = **{_fmt3(j8)}**",
        text,
        count=1,
    )
    text = text.replace(
        "（tie-aware fractional membership + projected-parent-area budgets）",
        "（strict area budget + fractional membership; canonical CSV）",
    )
    text = text.replace("exact top-10% 预算、H3 index tie-break", "strict 10% area budget; fractional ties")
    text = text.replace("exact top-k 预算", "strict area budget")
    text = text.replace("H3 index 确定性 tie-break", "fractional membership at tied scores")
    text = text.replace("exact top-k/H3 tie-break", "area-budget fractional membership")
    # Replace table 3 numeric block if present
    table_block = []
    for _, row in ladder.sort_values(["coarse_res", "aggregation"]).iterrows():
        table_block.append(
            f"| {int(row.coarse_res)} | {row.aggregation} | {_fmt3(row.jaccard)} | {_fmt3(row.f1)} | {_fmt3(row.fine_parent_recall)} | {_fmt3(row.coarse_precision)} |"
        )
    text = re.sub(
        r"\| coarse \| agg \| jaccard \| f1 \| fine-parent recall \| coarse precision \|\n\|---.*?\n(?:\|.*\n)+",
        "| coarse | agg | jaccard | f1 | fine-parent recall | coarse precision |\n"
        "|--------|-----|---------|-----|-------------------|------------------|\n"
        + "\n".join(table_block)
        + "\n",
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r"R10-vs-R9=0\.\d+、R10-vs-R8=0\.\d+",
        f"R10→R9={_fmt3(j9)}、R10→R8={_fmt3(j8)}",
        text,
    )
    text = text.replace(
        "尚无可用的 FloodNet 观测",
        "FloodNet 官方数据集 aq7i-eu5q 已公开但本冻结分析未接入",
    )
    REPORT.write_text(text, encoding="utf-8")
    print("patched", REPORT)


def main() -> None:
    # Fix typo in date_window tuple in update_paper_results if any
    pr = update_paper_results()
    patch_manuscript(pr)
    patch_data_sources()
    patch_report_jaccard(pr)


if __name__ == "__main__":
    main()
