# AI / reviewer reading guide (5 minutes)

This guide tells a human reviewer or an AI agent **exactly which files to open,
in which order**, and how each claim maps to evidence. Everything referenced
here is in the flat root directory.

## 0. The one authoritative artefact

`outputs__paper_results.json` is the **single source of truth** for every number.
If a sentence in the manuscript, report or audit disagrees with it, the JSON is
right and the prose is a bug. `RESULTS_QUICK_TABLE.csv` is a flat projection of
the same JSON for quick scanning.

## 1. Read in this order

1. **`README.md`** — what the project is, headline numbers, honest boundaries.
2. **`docs__paper__manuscript.md`** — the paper (abstract → methods → results).
   - HTML: `docs__paper__manuscript.html` · PDF: `docs__paper__manuscript.pdf`
3. **`docs__paper__report.md`** — the long-form research report (Chinese): for
   every figure and table it explains *how it was produced and what it means*.
   - HTML: `report.html` · PDF: `report.pdf`
4. **`docs__paper__audit.md`** — the technical audit trail: data provenance,
   the calculation chain, and how each formal review item (P0) was resolved.
5. **`RESULTS_QUICK_TABLE.csv`** — the frozen numbers, one row per metric.
6. **`FILE_INDEX.csv`** — every file with its original path and category.

## 2. Claim → evidence map

| Claim in the paper | Evidence file(s) |
|---|---|
| Lower Manhattan n=262, 63.7% positive | `data__processed__nyc_h3_cells.csv`, `outputs__paper_results.json` |
| Expanded n=956, 47.9% positive | `data__processed__nyc_h3_cells_expanded.csv` |
| Spatial-CV ROC-AUC/AP + spatial-block bootstrap CI, accuracy/F1 | `outputs__paper_results.json` → `*.spatial_cv`, `block_bootstrap_ci`, `outputs__oof_extended_metrics.json` |
| Per-fold OOF predictions & folds | `models__nyc_smoke__evaluation__spatial_cv_oof_predictions.csv`, `..._folds.csv`, and the `models__nyc_expanded__evaluation__*` twins |
| Construct validity of the union target (+ physics/reporting/full) | `outputs__source_ablation.csv` / `.json` |
| Buffer sensitivity (0/250/500/1000 m + grid_disk) | `outputs__buffer_sensitivity.csv`, `outputs__paper_results.json` → `buffer_sensitivity` |
| Scale loss (soft Jaccard + true reconstruction MAE/RMSE) | `outputs__jaccard_by_resolution.csv` / `.json` |
| Block-size sensitivity (offset 1/2/3) + LOBO | `outputs__block_sensitivity.csv`, `outputs__lobo_r7_*.csv` |
| Moran's I (target + OOF residual) | `outputs__block_sensitivity.json` |
| Sea-level-rise sensitivity | `outputs__slr_sensitivity.csv` / `.json` |
| Coastal vs pluvial negative control | `outputs__negative_control.json` |
| FloodNet strict held-out **external validation** (negative result) + freeze audit | `outputs__floodnet_heldout_validation.json` |
| Land-mask / DEP-threshold / threshold sensitivities | `outputs__land_mask_sensitivity.json`, `outputs__polygon_area_threshold_sensitivity.json`, `outputs__operating_threshold_sensitivity.json` |
| Adaptive refinement recall/precision/enrichment/cost-recall | `outputs__adaptive_vs_fixed_ablation.csv`, `outputs__adaptive_r11_hotspot_retention.json`, `outputs__adaptive_cost_recall.csv` |
| Figures | `docs__paper__figures__*.pdf` (vector) / `.png` (raster) |
| Figure generation code | `src__pluvial_flood_risk__figures.py`, `scripts__make_figures.py` |
| Data provenance / integrity | `data__raw__nyc__DOWNLOAD_MANIFEST.json`, `审查输出__evidence__file_sha256_inventory.csv` |
| Submission hard gates (8) | `tests__test_submission_hard_gates.py` (run with `PAPER_RELEASE_STRICT=1`) |

## 3. Method in one paragraph (for orientation)

Features per H3 R9 cell: elevation, slope, DEM D8 accumulation proxy, impervious
fraction, building density (land-area denominator), building footprint area
fraction, and EPSG:2263 nearest mapped-water distance. Target: the binary union
`evidence_positive = (dep_area_frac>0) | (complaint_count>0) | (ida_hwm_count>0)`
from open sources. Evaluation is 5-fold **spatial** CV grouping cells by H3 R7
parent block (`GroupKFold`, parent-resolution offset = 2), reporting **pooled
OOF** ROC-AUC/AP with spatial-block bootstrap 95% CIs and fold-mean accuracy/F1;
0/250/500/1000 m metre guard bands plus an H3 `grid_disk` purge test the block
separation. A separate `deployment_full` model is then fitted on all cells purely
for mapping and adaptive-screening illustration. The `urban` flag is removed
(`urban_flag_removed: true`) because it duplicates impervious fraction, and
`rainfall_mm_h` is removed from the estimator features as zero-variance.

## 4. Data semantics you must not miss

- **Pseudo-labels vs observations.** DEP stormwater polygons are **H&H model
  outputs**, not observed floods. 311 records are **crowd reports**. USGS HWM
  points are **observed** water marks. The target mixes these *evidence types*
  on purpose; the paper therefore says `evidence-positive`, **not** "verified
  flood".
- **`sandy_*` columns are a `negative_control`**, never a training label; FloodNet
  is `external_validation`, also never a training label (gate-enforced).
- **`rainfall_mm_h` is a constant synthetic hook** (75 mm/h), not radar; it is
  excluded from the estimator features as zero-variance, and the paper makes no
  rainfall-discrimination claim.
- **`dist_mapped_water_m`** is an EPSG:2263 distance-to-mapped-water proxy
  (NHDPlus HR; legacy alias `dist_stream_m`), tidal / shoreline-heavy in Lower
  Manhattan — *not* classic inland stream proximity.
- **FloodNet result is a core negative finding.** The strict held-out ROC-AUC is
  0.451 (LM) / 0.479 (Expanded) — no event-level external skill is claimed.
- **Fail-closed assembly.** Production rejects missing files/columns; synthetic
  fallbacks require an explicit flag. `outputs__paper_results.json` records
  `fail_closed: true`.

## 5. Heavy assets (GitHub Release, not committed)

| Bundle | Approx. size | Contents |
|---|---|---|
| `raw_geospatial_bundle.zip` | ~216 MB | Full raw GeoJSON/GeoTIFF (building footprints, DEP polygons, DEM, impervious, Sandy) |
| `audit_qa_bundle.zip` | ~82 MB | QA page renders, Word/PDF audit snapshots |
| `processed_parquet_bundle.zip` | small | The exact `.parquet` tables (CSV mirrors are in the root) |

Small, text-readable provenance layers **are** in the root
(`data__raw__nyc__flooding_311.geojson`, `..._usgs_ida_hwm.geojson`,
`..._hydro_streams.geojson`) so the evidence can be inspected without a download.

## 6. Suggested cross-review checks

1. **Number drift.** Pick any metric in the manuscript and confirm it matches
   `outputs__paper_results.json`. (Automated in
   `tests__test_major_revision_gates.py`.)
2. **Label honesty.** Confirm the prose never says "verified flood"; search for
   `evidence-positive` / `evidence-unrecorded`.
3. **Evaluation integrity.** Verify spatial CV groups on R7 parents
   (`models__nyc_smoke__evaluation__spatial_cv_folds.csv`) and that the
   `deployment_full` model is *not* the one used for reported CV metrics.
4. **Baseline sanity.** Model accuracy/F1 must beat always-positive; check
   `outputs__paper_results.json` → `*.baselines`.
5. **Negative-result honesty.** Confirm the FloodNet failure (ROC-AUC < 0.5) is
   present in the abstract/conclusion and the claim is limited to blocked-CV
   open-evidence discrimination.
6. **Claim discipline.** Grep the manuscript for `citywide`, `radar`, `PFIb` to
   confirm all such mentions are explicit *dis*claimers.
7. **Hard gates.** Run `PAPER_RELEASE_STRICT=1 pytest tests/test_submission_hard_gates.py`
   — a missing critical artifact must FAIL, not skip.
