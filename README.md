# Scalable pluvial flood risk assessment (H3 DGGS + ML)

Data-driven framework aligned with:

> *Scalable pluvial flood risk assessment: A data-driven framework integrating machine learning (ML) and discrete global grid systems (DGGS H3)*  
> NTNU, 7Analytics AS, Østfold University College (Norway).

This repository implements an H3-indexed pluvial workflow: per-cell features, ML (classification + continuous risk), Parquet/GeoJSON exports, and **spatially honest** H3-block cross-validation.

## Academic manuscript (paper path)

Working methods manuscript (IJDRR-shaped; open labels ≠ PFIb): [`docs/paper/manuscript.md`](docs/paper/manuscript.md) · HTML [`docs/paper/manuscript.html`](docs/paper/manuscript.html).

**Abstract (pilot evidence only).** We present an open-label H3 learning protocol for two Manhattan pilots: a Lower Manhattan table (`n=141`) and an expanded extent (`manhattan_expanded`, `n=956`). Lower Manhattan spatial CV accuracy **0.784 ± 0.069** / F1 **0.866** sits **below** an always-positive majority baseline (**0.808** / **0.893**), so it is not reported as classification skill. The expanded pilot is near-even (47.9% positive, 28 blocks): accuracy **0.642 ± 0.148** **exceeds** both the always-positive baseline (**0.479**) and the constant majority-class (always-negative) baseline (**0.521**), and continuous-risk R² is **0.525 ± 0.112**, but F1 (**0.608**) remains below the always-positive F1 (**0.641**, fold-mean). Out-of-fold discrimination is moderate in both pilots: pooled ROC-AUC **0.68** (LM) and **0.70** (expanded), pooled average precision **0.86** (LM) and **0.72** (expanded); the expanded PR-AUC of **0.72** sits clearly above its **0.479** prevalence baseline. Positive-class F1 remains below the always-positive comparator, so classification skill is not claimed. Open-label scale-loss Jaccard (mean aggregation R10→R8 **0.167**), adaptive cell-count screening (adaptive/uniform ≈ **0.569**), and a binding rainfall-conditioned `PFI_h(c,r)` definition complete the protocol. We do **not** claim citywide skill, PFIb reproduction, radar rainfall, or rainfall discrimination (current within-cell scenario range = **0**; 待补充). Process detail: [`docs/paper/report.md`](docs/paper/report.md).

## Paper path vs demo path

**Main paper positioning** (do not drift): vs Svellingen et al. 2026 IJDRR (PFIb→H3 aggregation, Jaccard ~0.14 at R13 vs R10, NYC, proprietary insurance labels):

1. Spatially honest H3-block CV as first-class evaluation  
2. Open multi-source labels (DEP stormwater, 311, USGS Ida HWM) — **not** PFIb  
3. Adaptive H3 refinement against scale / hotspot loss  
4. Event-conditioned rainfall `PFI_h(c, r)`

**Oslo is transfer/appendix**, not the main claim. **Synthetic and fixture accuracy is never science.**

| Path | Config | What it is | What you may claim |
|------|--------|------------|--------------------|
| Demo | `configs/demo_oslo.yaml` | Hash features + synthetic labels | Pipeline QA |
| NYC fixture | `configs/nyc.yaml` + missing `data/raw/nyc/` | Same join/zonal/adaptive **code** on tiny invented layers (`assembly_mode=fixture`) | Code works; **not** NYC skill |
| NYC open data | same config with live GeoTIFF/GeoJSON | Production table | Spatial-CV results on documented public layers only |
| 7Analytics PFIb | — | **Not implemented, not reproduced** | Do not claim |

## Quick start (demo path)

```powershell
cd /path/to/pluvial-flood-risk-DGGS-H3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Oslo synthetic demo (data → train → eval → predict)
python scripts\run_demo.py
pluvial-smoke
```

Step-by-step:

```powershell
pluvial-demo-data --config configs\demo_oslo.yaml
pluvial-train
pluvial-evaluate
pluvial-predict --rainfall 40
pluvial-predict --config configs\demo_oslo.yaml --scenarios
pluvial-diagnostics --fine-resolution 10 --resolutions 8,9,10
```

## NYC / Manhattan smoke (paper path)

Fetch a **Lower Manhattan** Open Data / USGS subset (not citywide 1 ft DEM):

```powershell
python scripts\download_nyc_data.py
# or .\scripts\download_nyc_data_stub.ps1
python scripts\build_nyc_h3.py --no-fixtures
pluvial-nyc-smoke
```

If the network blocks Socrata or mirrors fail, fixtures still work:

```powershell
python scripts\build_nyc_h3.py --fixtures
pluvial-nyc-smoke
```

See `data/raw/nyc/DOWNLOAD_MANIFEST.json` and `data/raw/DATA_SOURCES.md` for what is live vs synthetic. Typical live stack: DEM, DEP, buildings, Ida HWM, 311 (ArcGIS mirror), Sandy (negative control), NLCD impervious, and NHDPlus HR hydro (`dist_stream_m` from vector → `feature_source=observed` when all static layers are live). Hydro in Lower Manhattan is mostly tidal river/waterbody — a **distance-to-water** proxy, not dense inland streams. `event_rainfall.tif` is a constant Ida-like hook, not radar. **Do not claim PFIb reproduction.**

Outputs of interest:

| Path | Description |
|------|-------------|
| `data/processed/nyc_h3_cells.parquet` | Assembled H3 table (`assembly_mode`, `label_source`, `feature_source`) |
| `outputs/jaccard_by_resolution.csv` | Hotspot Jaccard / F1 vs parent res |
| `outputs/jaccard_by_resolution.png` | Paper-style scale-loss figure (needs matplotlib) |
| `outputs/negative_control.json` | Sandy/coastal vs pluvial overlap (not a training label) |
| `outputs/pfi_h_scenarios.csv` | `PFI_h` per cell and rainfall scenario |
| `outputs/adaptive_vs_fixed_ablation.csv` | Adaptive vs fixed coarse ablation |
| `models/nyc_smoke/spatial_cv_folds.csv` | Per-fold spatial CV (NYC; prefer over demo `outputs/spatial_cv_folds.csv`) |
| `models/run_metadata.json` | **Oslo/demo** train metadata — not NYC skill |
| `models/nyc_smoke/run_metadata.json` | **Citable** NYC smoke metrics when live stack present |

**Bbox profiles** (`configs/nyc.yaml`): `smoke` (default for `pluvial-nyc-smoke`), `lower_manhattan` (default build/download), `manhattan_expanded` (optional larger fetch — not for smoke).

```powershell
python scripts\download_nyc_data.py --bbox-profile lower_manhattan
python scripts\build_nyc_h3.py --bbox-profile lower_manhattan --no-fixtures
# Expanded extent (separate DEM pull; do not use for default smoke):
# python scripts\download_nyc_data.py --bbox-profile manhattan_expanded --dem-size 800,900
```

**FloodNet:** opt-in (`labels.include_floodnet: false` by default). Place non-empty `data/raw/nyc/floodnet_sensors.geojson` and set the flag true to augment training points; prefer held-out sensor validation for paper claims. Absent/empty → no-op (`floodnet_join` in smoke JSON).

## Event-conditioned inference

`PFI_h(c, r)` is the classifier flood probability at cell `c` under rainfall intensity `r` (mm/h). Static terrain/exposure features are built once; only `rainfall_mm_h` changes.

```powershell
pluvial-predict-scenarios --config configs\nyc.yaml
# columns: h3_index, scenario, rainfall_mm_h, PFI_h, predicted_risk, ...
```

This is **not** the 7Analytics PFIb insurance product.

## Adaptive H3 refinement

Coarse screen (e.g. R9) → children only for high-risk and/or high-uncertainty parents, optional k-ring expansion:

```powershell
pluvial-adaptive --bbox 10.70,59.90,10.80,59.96 --coarse-res 9 --fine-res 11 --quantile 0.8
```

Metrics: `hotspot_recall` vs a uniform fine grid, `cell_count_ratio` (adaptive / uniform).

## Baselines

`pluvial-evaluate` reports GBM in-sample + spatial CV **and**:

- `baseline_logistic_*` — L2 logistic + linear regressor  
- `baseline_rule_*` — elevation + impervious + slope + TWI-like ponding rule  

## Credibility: demo vs production

| Aspect | Demo (default) | Production (your data) |
|--------|----------------|------------------------|
| Features | Hash from H3 ID | DEM / land cover / buildings / hydro → H3 |
| Labels | `synthetic` formula | `observed` polygon area-fraction / point counts |
| Random split | Diagnostic only | Diagnostic only |
| Spatial block CV | `spatial_cv_*` | **Required** |
| Accuracy claims | QA only | Observed labels + spatial CV + `assembly_mode=opendata` |

## Project layout

```
src/pluvial_flood_risk/
  h3_grid.py          # H3 indexing, parents/children, geometry candidates
  features.py         # Hash features + point/polygon/hydro aggregation
  labels.py           # Synthetic labels + attach_observed_labels
  raster.py           # GeoTIFF zonal mean + DEM slope / D8 proxy
  crs_warp.py         # 2263→4326 raster/vector warp
  download_nyc.py     # Lower Manhattan Open Data / USGS fetch
  assemble.py         # Wire rasters/vectors into an H3 table
  rollups.py          # Parent mean/max/p90 + Jaccard ladder
  figures.py          # Jaccard vs resolution PNG
  negative_control.py # Sandy/FEMA overlay (not a pluvial label)
  event_rainfall.py   # Optional event rainfall GeoTIFF → rainfall_mm_h
  floodnet.py         # FloodNet sensor stub path
  adaptive.py         # Coarse→fine refinement
  baselines.py        # Logistic + ponding rule
  spatial_cv.py       # H3 block GroupKFold
  pipeline.py         # train / predict / scenarios / evaluate / smokes
configs/demo_oslo.yaml
configs/nyc.yaml
data/raw/DATA_SOURCES.md
scripts/download_nyc_data.py
scripts/build_nyc_h3.py
```

## H3 resolution

| Res | ~hex edge | Typical use |
|-----|-----------|-------------|
| 8 | ~460 m | Regional screening |
| 9 | ~174 m | City / catchment (default) |
| 10 | ~66 m | Neighborhood |
| 11 | ~25 m | Adaptive refinement target |

## Tests

```powershell
pytest -q
pluvial-smoke
```

## License

MIT (scaffold). Upstream Open Data licenses remain those of NYC, USGS, FEMA, Kartverket, etc.
