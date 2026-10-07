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
| Expanded n=956, 48.2% positive | `data__processed__nyc_h3_cells_expanded.csv` |
| Spatial-CV ROC/PR-AUC, accuracy/F1 | `outputs__paper_results.json` → `*.spatial_cv`, `outputs__oof_extended_metrics.json` |
| Per-fold OOF predictions & folds | `models__nyc_smoke__evaluation__spatial_cv_oof_predictions.csv`, `..._folds.csv`, and the `models__nyc_expanded__evaluation__*` twins |
| Construct validity of the composite target | `outputs__source_ablation.csv` / `.json` |
| Scale loss (soft Jaccard R10→R9/R8) | `outputs__jaccard_by_resolution.csv` / `.json` |
| Block-size sensitivity (R6/R7/R8) + LOBO | `outputs__block_sensitivity.csv`, `outputs__lobo_r7_*.csv` |
| Moran's I (target + OOF residual) | `outputs__block_sensitivity.json` |
| Sea-level-rise sensitivity | `outputs__slr_sensitivity.csv` / `.json` |
| Coastal vs pluvial negative control | `outputs__negative_control.json` |
| FloodNet strict held-out diagnostic | `outputs__floodnet_heldout_validation.json` |
| Land-mask / DEP-threshold / threshold sensitivities | `outputs__land_mask_sensitivity.json`, `outputs__polygon_area_threshold_sensitivity.json`, `outputs__operating_threshold_sensitivity.json` |
| Adaptive refinement cell-count accounting | `outputs__adaptive_vs_fixed_ablation.csv`, `outputs__adaptive_r11_hotspot_retention.json` |
| Figures | `docs__paper__figures__*.pdf` (vector) / `.png` (raster) |
| Figure generation code | `src__pluvial_flood_risk__figures.py`, `scripts__make_figures.py` |
| Data provenance / integrity | `data__raw__nyc__DOWNLOAD_MANIFEST.json`, `审查输出__evidence__file_sha256_inventory.csv` |

## 3. Method in one paragraph (for orientation)

Features per H3 R9 cell: elevation, slope, flow-accumulation proxy, impervious
fraction, building density, distance-to-mapped-water, rainfall. Target: a
binary `evidence-positive` / `evidence-unrecorded` label assembled as
`max(dep_area_frac, complaint_presence, ida_hwm_presence)` from open sources.
Evaluation is 5-fold **spatial** CV grouping cells by H3 R7 parent block
(`GroupKFold`), reporting **pooled OOF** ROC-AUC/AP and fold-mean accuracy/F1.
A separate `deployment_full` model is then fitted on all cells purely for
mapping and adaptive-screening illustration. The `urban` flag is removed
(`urban_flag_removed: true`) because it is near-constant and leaked.

## 4. Data semantics you must not miss

- **Pseudo-labels vs observations.** DEP stormwater polygons are **H&H model
  outputs**, not observed floods. 311 records are **crowd reports**. USGS HWM
  points are **observed** water marks. The target mixes these *evidence types*
  on purpose; the paper therefore says `evidence-positive`, **not** "verified
  flood".
- **`sandy_*` columns are a negative control**, never a training label.
- **`rainfall_mm_h` is a constant synthetic hook** (75 mm/h), not radar; the
  paper makes no rainfall-discrimination claim.
- **`dist_stream_m`** is a distance-to-mapped-water proxy (NHDPlus HR), tidal /
  shoreline-heavy in Lower Manhattan — *not* classic inland stream proximity.
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
5. **Claim discipline.** Grep the manuscript for `citywide`, `radar`, `PFIb` to
   confirm all such mentions are explicit *dis*claimers.
