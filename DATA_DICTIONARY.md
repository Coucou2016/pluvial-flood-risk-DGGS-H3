# Data dictionary

Column-level description of the modelling tables and core result files. CSV
mirrors (`*.csv`) share the exact columns of their `*.parquet` twins.

> **Major Revision 2026-10-08 (schema v2).** The main target is now the binary
> union `evidence_positive`; the cross-source continuous composite is no longer a
> main result, and the uncalibrated model score is `susceptibility_score`
> (`S_h(c)`), never a "probability". Legacy `PFI_h` / `flood_probability` column
> names are retired. Some legacy columns are still **present in the tables for
> provenance/QA** and are marked as such below.

---

## 1. `data__processed__nyc_h3_cells.{parquet,csv}`
Lower Manhattan pilot, H3 resolution 9, **n = 262**.

| Column | Type | Meaning |
|---|---|---|
| `h3_index` | str | H3 R9 cell id |
| `elevation_m` | float | Mean elevation (USGS 3DEP) |
| `impervious_frac` | float | Impervious fraction 0–1 (Annual NLCD) |
| `slope_deg` | float | Terrain slope (nodata-safe: edge cells are never silently zeroed) |
| `dem_d8_accum_proxy` | float | DEM-derived D8 flow-accumulation proxy (renamed from `flow_accum_proxy`) |
| `land_cover_urban` | float | Urban land-cover indicator (kept for provenance; **excluded from the model**) |
| `building_density` | float | Building-centroid count / **land** area (NYC MapHub) |
| `building_area_fraction` | float | Building footprint area / cell area (exposure, distinct from the count) |
| `dist_mapped_water_m` | float | Nearest mapped-water distance in **EPSG:2263 metres** (renamed from `dist_stream_m`; alias kept) |
| `rainfall_mm_h` | float | Rainfall input; **constant synthetic hook (75 mm/h)**, not radar. **Removed from `FEATURE_COLUMNS`** (zero variance); see `EVENT_FEATURE_COLUMNS` |
| `lon`, `lat` | float | Cell centroid |
| `h3_resolution` | int | 9 |
| `feature_source` | str | `observed` (live layers) / `fixture` / `synthetic` |
| `assembly_mode` | str | `opendata` / `fixture` / `demo` |
| `observed_feature_cols` | str | Which features came from live data |
| `rainfall_source` | str | `event_raster` (the synthetic constant grid) |
| `data_mode` | str | `production` / `demo` |
| `synthetic_value_count`, `null_value_count` | int | Filled / missing counts (0 under fail-closed) |
| `dep_area_frac` | float | DEP stormwater flood area fraction |
| `dep_nuisance_frac`, `dep_deep_frac` | float | DEP category breakdown |
| `complaint_count`, `complaint_presence` | int | NYC 311 street-flood complaints |
| `ida_hwm_count`, `ida_hwm_presence` | int | USGS Ida high-water marks |
| `ida_hwm_quality` | str | HWM quality flag (Excellent/Good/Fair/Poor); n = 6 diagnostic-only |
| `evidence_sources` | str | Comma list, e.g. `dep`, `complaint`, `hwm` |
| `evidence_positive` | int | **Main binary target**: `(dep_area_frac>0) | (complaint_count>0) | (ida_hwm_count>0)`; 1 = evidence-positive, 0 = evidence-unrecorded |
| `evidence_score` | float | Per-cell open-evidence score (target-side quantity; renamed from `flood_risk`) |
| `evidence_coverage_proxy` | float | Continuous target proxy: **DEP-only** polygon area fraction (replaces the old cross-source composite) |
| `susceptibility_score` | float | Model score `S_h(c)=f_θ(X_c)` (**uncalibrated**) |
| `flood_class` | int | Legacy alias of `evidence_positive` (kept for backward compatibility) |
| `flood_risk` | float | Legacy alias of `evidence_score` (kept for backward compatibility) |
| `label_source` | str | `open_public_evidence` |
| `sandy_area_frac`, `sandy_class` | float/int | **Negative control only** (FEMA Sandy), never a training label |

`FEATURE_COLUMNS` (the estimator inputs) are: `elevation_m`, `slope_deg`,
`dem_d8_accum_proxy`, `impervious_frac`, `building_density`,
`building_area_fraction`, `dist_mapped_water_m`. Rainfall is **not** among them
(zero-variance in training); a future event interface is documented separately as
`EVENT_FEATURE_COLUMNS`.

## 2. `data__processed__nyc_h3_cells_expanded.{parquet,csv}`
Manhattan Expanded pilot, **n = 956**. Identical schema to §1.

## 3. `data__processed__nyc_h3_cells_r10_labels.{parquet,csv}`
R10 label-support table for scale diagnostics. Same evidence columns as §1, plus
`label_scale_mode` (`native_overlay`). **Labels only — no modelling features**.

## 4. `outputs__susceptibility_scenarios.{parquet,csv}`
Event-conditioned scenario scoring (deferred hook). Feature block plus `scenario`,
`predicted_evidence_susceptibility`, `susceptibility_score`, `predicted_class`.
Under constant rainfall the scenarios coincide — this is the illustrative hook,
not a rainfall-skill result. Any scenario interface must pass a `min_unique`
uniqueness guard before a constant feature can be treated as learned.

## 5. Result registries (`outputs__*.json`)

| File | Contents |
|---|---|
| `outputs__paper_results.json` | **Authoritative** registry (schema v2): pilots, CV metrics + bootstrap CIs, baselines, evidence semantics, source ablation (incl. physics/reporting/full), block sensitivity, **buffer sensitivity**, scale-loss (soft Jaccard + true reconstruction MAE/RMSE), SLR sensitivity, negative control, **external_validation** (FloodNet), adaptive refinement, sensitivities, feature columns, software environment, split provenance |
| `outputs__oof_extended_metrics.json` | Extended pooled OOF metrics + per-fold table (accuracy, balanced acc, F1, precision, recall, specificity, MCC, ROC-AUC) |
| `outputs__source_ablation.{json,csv}` | Target-definition and feature-subset ablations per pilot |
| `outputs__block_sensitivity.{json,csv}` | Parent-resolution-offset 1/2/3 (R8/R7/R6) sensitivity + LOBO + Moran's I |
| `outputs__buffer_sensitivity.csv` | 0/250/500/1000 m metre guard bands (EPSG:2263) + `h3_grid_disk_k1/k2` purge, with retained-train fraction |
| `outputs__lobo_r7_*.csv` | Leave-one-block-out (R7) results |
| `outputs__jaccard_by_resolution.{json,csv}` | Scale-loss soft/hard Jaccard + `reconstruction_mae`/`reconstruction_rmse` (identity `continuous_mae` is QA-only) |
| `outputs__hotspot_budget_sensitivity.{json,csv}` | Hotspot budget sweep (5/10/15/20%) |
| `outputs__slr_sensitivity.{json,csv}` | 2050-SLR DEP-layer sensitivity |
| `outputs__negative_control.json` | Coastal-vs-pluvial OOF-score separation (Sandy, never a label) |
| `outputs__floodnet_heldout_validation.json` | FloodNet strict held-out **external validation** (core negative result) + freeze audit counters + exposure sensitivity |
| `outputs__land_mask_sensitivity.json` | Water-mask sensitivity (NHDPlus) |
| `outputs__polygon_area_threshold_sensitivity.json` | DEP area-fraction threshold sweep |
| `outputs__operating_threshold_sensitivity.json` | 0.5 vs train-fold-max-F1 threshold |
| `outputs__sandy_311_window_sensitivity.json` | Excluding Sandy-window 311 reports |
| `outputs__hwm_quality_oof_validation.json` | HWM quality-filtered OOF validation |
| `outputs__adaptive_vs_fixed_ablation.csv` | Adaptive vs fixed cell-count accounting |
| `outputs__adaptive_r11_hotspot_retention.json` | True R11 re-extraction: `hotspot_refinement_recall`/precision/enrichment + cost-recall curve |
| `outputs__adaptive_cost_recall.csv` | Cost-recall curve rows for the adaptive experiment |
| `outputs__classification_baselines*.json` | Trivial baselines per pilot |

## 6. Provenance columns / keys

- `outputs__paper_results.json` → `git_commit`, `run_id`, `config_hash`,
  `freeze_tag` (`major-revision-2026-10-08`), `schema` (2), `fail_closed`,
  `paths_note`.
- `provenance` block → `analysis_source_commit` (this analysis tree) vs
  `snapshot_repository_commit` (flat review snapshot), plus `config_sha256` and
  `lockfile_sha256`. **No absolute local paths** anywhere in the registry.
- `审查输出__evidence__file_sha256_inventory.csv` — SHA-256 of every input.
- `data__raw__nyc__DOWNLOAD_MANIFEST.json` — per-layer source URL, dataset id,
  sha256, byte/row count, retrieval date (schema `raw_download_manifest/v2`).

## 7. Units & conventions

- Areas are square metres; `*_area_frac` are fractions of cell area (0–1).
- Distances are EPSG:2263 metres (nearest mapped water).
- `susceptibility_score` = `S_h(c)`, the uncalibrated positive-class score of the
  gradient-boosting classifier; **not** a depth, probability, or return-period.
- Reported CV metrics are **pooled out-of-fold** unless suffixed `_mean`
  (fold mean), which is followed by `_std`.
- `hotspot_refinement_recall` counts a uniform-fine hotspot as recalled only if
  that fine cell was *actually refined* (the legacy coverage recall is a
  tautology and is retained only as a QA counter).
