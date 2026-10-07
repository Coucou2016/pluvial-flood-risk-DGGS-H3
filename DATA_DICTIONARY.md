# Data dictionary

Column-level description of the modelling tables and core result files. CSV
mirrors (`*.csv`) share the exact columns of their `*.parquet` twins.

---

## 1. `data__processed__nyc_h3_cells.{parquet,csv}`
Lower Manhattan pilot, H3 resolution 9, **n = 262**.

| Column | Type | Meaning |
|---|---|---|
| `h3_index` | str | H3 R9 cell id |
| `elevation_m` | float | Mean elevation (USGS 3DEP) |
| `impervious_frac` | float | Impervious fraction 0–1 (Annual NLCD) |
| `slope_deg` | float | Terrain slope |
| `flow_accum_proxy` | float | Flow-accumulation proxy |
| `land_cover_urban` | float | Urban land-cover indicator (kept for provenance; **excluded from the model**) |
| `building_density` | float | Footprints per area (NYC MapHub) |
| `dist_stream_m` | float | Distance to mapped water (NHDPlus HR; distance-to-water proxy) |
| `rainfall_mm_h` | float | Rainfall input; **constant synthetic hook (75 mm/h)**, not radar |
| `lon`, `lat` | float | Cell centroid |
| `h3_resolution` | int | 9 |
| `feature_source` | str | `observed` (live layers) / `fixture` / `synthetic` |
| `assembly_mode` | str | `opendata` / `fixture` / `demo` |
| `observed_feature_cols` | str | Which features came from live data |
| `rainfall_source` | str | `event_raster` (the synthetic constant grid) |
| `data_mode` | str | `production` / `demo` |
| `synthetic_value_count`, `null_value_count` | int | Filled / missing counts (0 under fail-closed) |
| `flood_area_frac`, `flood_point_count` | float/int | Composite flood evidence |
| `dep_area_frac` | float | DEP stormwater flood area fraction |
| `dep_nuisance_frac`, `dep_deep_frac` | float | DEP category breakdown |
| `complaint_count`, `complaint_presence` | int | NYC 311 street-flood complaints |
| `ida_hwm_count`, `ida_hwm_presence` | int | USGS Ida high-water marks |
| `ida_hwm_quality` | str | HWM quality flag (Excellent/Good/Fair/Poor) |
| `evidence_sources` | str | Comma list, e.g. `dep`, `complaint`, `hwm` |
| `observed_risk` | float | Composite continuous risk input |
| `flood_risk` | float | Continuous target proxy |
| `flood_class` | int | **Binary target**: 1 = `evidence-positive`, 0 = `evidence-unrecorded` |
| `label_source` | str | `open_public_evidence` |
| `sandy_area_frac`, `sandy_class` | float/int | **Negative control only** (FEMA Sandy), never a training label |

## 2. `data__processed__nyc_h3_cells_expanded.{parquet,csv}`
Manhattan Expanded pilot, **n = 956**. Identical schema to §1 (same 36 columns).

## 3. `data__processed__nyc_h3_cells_r10_labels.{parquet,csv}`
R10 label-support table for scale diagnostics, **n = 1857**, 22 columns:
`h3_index`, `lon`, `lat`, `h3_resolution`, `assembly_mode`, `feature_source`
(`labels_only_diagnostics`), the evidence columns of §1, `observed_risk`,
`flood_risk`, `flood_class`, `label_source`, and `label_scale_mode`
(`native_overlay`). **Labels only — no modelling features** (that is what the
R9+raster/vector feature extraction is for).

## 4. `outputs__pfi_h_scenarios.{parquet,csv}`
Event-conditioned scenario scoring, **n = 1048**, 24 columns: §1 feature block
plus `scenario` (`moderate`/…), `predicted_risk`, `flood_probability`,
`PFI_h`, `predicted_class`. Under constant rainfall the scenarios coincide —
this is the illustrative hook, not a rainfall-skill result.

## 5. `outputs__risk_cells.{parquet,csv}`
Citywide-style screening output, **n = 988**, 17 columns: `h3_index`,
`elevation_m`, `slope_deg`, `flow_accum_proxy`, `impervious_frac`,
`building_density`, `dist_stream_m`, `rainfall_mm_h`, `land_cover_urban`, `lon`,
`lat`, `h3_resolution`, `feature_source` (may be `synthetic`),
`predicted_risk`, `flood_probability`, `PFI_h`, `predicted_class`.
**Illustrative mapping output from `deployment_full`, not a validated product.**

---

## 6. Result registries (`outputs__*.json`)

| File | Contents |
|---|---|
| `outputs__paper_results.json` | **Authoritative** registry: pilots, CV metrics, baselines, source ablation, block sensitivity, scale-loss, SLR sensitivity, negative control, sensitivities, software environment, provenance |
| `outputs__oof_extended_metrics.json` | Extended pooled OOF metrics + per-fold table (accuracy, balanced acc, F1, precision, recall, specificity, MCC, ROC-AUC) |
| `outputs__source_ablation.{json,csv}` | Seven target definitions per pilot (construct-validity test) |
| `outputs__block_sensitivity.{json,csv}` | R6/R7/R8 block-size sensitivity |
| `outputs__lobo_r7_*.csv` | Leave-one-block-out (R7) results |
| `outputs__jaccard_by_resolution.{json,csv}` | Scale-loss soft/hard Jaccard, budget-matched |
| `outputs__hotspot_budget_sensitivity.{json,csv}` | Hotspot budget sweep (5/10/15/20%) |
| `outputs__slr_sensitivity.{json,csv}` | 2050-SLR DEP-layer sensitivity |
| `outputs__negative_control.json` | Coastal-vs-pluvial score separation |
| `outputs__floodnet_heldout_validation.json` | FloodNet strict held-out diagnostic |
| `outputs__land_mask_sensitivity.json` | Water-mask sensitivity (NHDPlus) |
| `outputs__polygon_area_threshold_sensitivity.json` | DEP area-fraction threshold sweep |
| `outputs__operating_threshold_sensitivity.json` | 0.5 vs train-fold-max-F1 threshold |
| `outputs__sandy_311_window_sensitivity.json` | Excluding Sandy-window 311 reports |
| `outputs__hwm_quality_oof_validation.json` | HWM quality-filtered OOF validation |
| `outputs__adaptive_vs_fixed_ablation.csv` | Adaptive vs fixed cell-count accounting |
| `outputs__adaptive_r11_hotspot_retention.json` | True R11 re-extraction hotspot recall |
| `outputs__classification_baselines*.json` | Trivial baselines per pilot |

## 7. Provenance columns / keys

- `outputs__paper_results.json` → `git_commit`, `run_id`, `config_hash`,
  `freeze_tag`, `stamp_commit`, `fail_closed`.
- `审查输出__evidence__file_sha256_inventory.csv` — SHA-256 of every input.
- `data__raw__nyc__DOWNLOAD_MANIFEST.json` — per-layer source URL/status/count.

## 8. Units & conventions

- Areas are square metres; `*_area_frac` are fractions of cell area (0–1).
- `PFI_h` = pluvial flood indicator, a monotone transform of the OOF
  probability under the stated rainfall hook; **not** a depth or return-period.
- Reported CV metrics are **pooled out-of-fold** unless suffixed `_mean`
  (fold mean), which is followed by `_std`.
