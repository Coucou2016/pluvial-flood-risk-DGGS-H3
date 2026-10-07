# Manuscript skeleton — Scalable pluvial flood risk on H3 (open labels)

Working title: *Beyond aggregating a building index: spatially honest pluvial flood learning and adaptive H3 screening with an explicit rainfall-conditioned cell index*

**Status:** Expanded manuscript in `docs/paper/manuscript.md` (Results filled from live `models/nyc_smoke/` / `outputs/` only). Skeleton retained as outline reference.  
**Conversation:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2 (browser MCP blocked 2026-08-16; paste `artifacts/chatgpt_literature_brief.md` manually)  
**Boundaries:** No PFIb; fixture ≠ science; Lower Manhattan smoke ≠ citywide; `PFI_h(c,r)` = rainfall-conditioned hex flood probability/index (not feature importance).

---

## Abstract (draft bullets)

- Motivation: scalable pluvial assessment without proprietary insurance labels.
- Method: open multi-source labels → H3 features → GBM + spatial block CV; adaptive refinement; `PFI_h(c,r)`.
- Result slots: spatial_cv metrics; Jaccard ladder; adaptive cell_count_ratio / hotspot_recall; Sandy negative control.
- Limitation slot: study extent, rainfall provenance, label bias.

## 1 Introduction

- Urban pluvial risk; limits of hydrodynamic-only workflows at city scale.
- Svellingen et al. 2026: PFIb → H3, efficiency, Jaccard scale-loss (cite; do not claim reproduction).
- Gap: open, spatially honest evaluation + adaptive response to scale-loss + event-conditioned index.
- Contributions (3): (i) open-label H3-ML protocol with spatial CV; (ii) scale-loss diagnostics; (iii) adaptive H3 + `PFI_h(c,r)`.

## 2 Related work

- Insurance / claims ML; DGGS flood (ISEA3H, H3H); MAUP / adaptive partitions.
- Table: openness of labels, grid, evaluation honesty, event conditioning.

## 3 Study area and data

- Lower Manhattan bbox (`configs/nyc.yaml`); citywide deferred.
- Layers + CRS + license: copy from `data/raw/DATA_SOURCES.md` / `DOWNLOAD_MANIFEST.json`.
- Provenance columns: `assembly_mode`, `feature_source`, `label_source`, `rainfall_source`.
- Sandy as **negative control only**.

## 4 Methods

### 4.1 H3 representation

We index the study extent with Uber H3 hexagonal cells. The training table uses resolution **R9** (configurable). Scale-loss diagnostics assemble labels at a finer resolution (**≥ R10**) and roll hotspots to coarser parents (R9, R8). Adaptive refinement screens high-score parents and expands selected children to **R11**. Cell geometry and parent–child relations follow the H3 hierarchy; all joins are performed in EPSG:4326.

### 4.2 Features and open labels

Static predictors include DEM-derived elevation and slope, a flow-accumulation proxy, NLCD impervious fraction, building density, and distance to hydro features (NHDPlus HR / waterbodies as a **distance-to-water** proxy in Lower Manhattan, not dense inland streams). Rainfall enters as a scenario intensity `rainfall_mm_h` (or optional event GeoTIFF hook). Observed static feature columns are tracked separately from rainfall so a constant synthetic event grid is never marketed as radar.

Labels are **open multi-source** layers: DEP stormwater flood polygons (area fraction), 311 flooding complaints and USGS Ida high-water marks (point counts). These define `flood_risk` / `flood_class` as **observed flood labels** (not “ground truth”). We do **not** use or reproduce 7Analytics PFIb. Optional FloodNet sensor points may join the same binary target only when `labels.include_floodnet: true` **and** a non-empty `floodnet_sensors.geojson` is present; default is **off** (opt-in). Prefer a later held-out FloodNet validation experiment when coverage is sufficient. Absence/empty remains a documented no-op.

Provenance fields on every assembled table: `assembly_mode` (opendata|fixture|hash), `feature_source`, `label_source`, `rainfall_source`.

### 4.3 Models and baselines

Primary learner: gradient-boosting classifier + continuous risk regressor on the H3 feature matrix. Baselines: L2 logistic + linear regressor, and a simple elevation/impervious/slope/TWI-like ponding rule. In-sample metrics are reported only as optimistic references; primary blocked-evaluation claims use spatial CV, with class-prevalence and majority-class baselines disclosed (accuracy/F1 do not beat the majority baseline on this pilot).

### 4.4 Spatial H3-block cross-validation

Training cells are blocked by coarse H3 parents (k-ring grouping). GroupKFold holds out entire blocks so neighboring cells do not leak across folds. Per-fold counts and metrics are written to `spatial_cv_folds*.csv`. Random i.i.d. splits are not the primary protocol.

### 4.5 Scale-loss diagnostics

Hotspot sets at fine resolution (top quantile of risk) are compared to parent-aggregated hotspots via Jaccard and F1 across resolution pairs. Figures must state open-label provenance and must not claim equality to Svellingen et al.’s PFIb Jaccard (~0.14).

### 4.6 Adaptive refinement and ablation

After training, cell scores `PFI_h` / `flood_probability` screen parents for refinement. Metrics include mixed-resolution cell count vs fixed coarse and vs uniform fine (`cell_count_ratio`), plus hotspot recall when estimated. Ablation artifact: `adaptive_vs_fixed_ablation.csv`. Adaptive smoke must use **trained** scores (`score_source=trained_PFI_h`), never label-only screens for the paper path.

### 4.7 Event-conditioned `PFI_h(c,r)`

Definition (binding):  
`PFI_h(c,r) = ˆP(Y_c = 1 | X_c, r)` — the trained model’s rainfall-conditioned flood probability/index for cell `c` under rainfall condition `r`.

It is a **model output**, not feature importance, SHAP, permutation importance, or causal attribution. Static features `X_c` are held fixed while `r` varies across named scenarios (e.g. moderate / heavy / ida_like / extreme). Scenario tables (`pfi_h_scenarios.csv`) support response curves; maps under synthetic rainfall must be labeled as scenario-conditioned, not observed inundation.

### 4.8 Negative control

FEMA Sandy coastal inundation is joined for overlap diagnostics only and is **not** a training label. Results are interpreted as coastal vs pluvial separation checks under the stated assembly mode.

## 5 Experiments

| ID | Description | Primary output |
|----|-------------|----------------|
| E1 | Assemble open LM table | `nyc_h3_cells.parquet` |
| E2 | Spatial CV | `spatial_cv_*`, fold CSV |
| E3 | Baselines | evaluate JSON |
| E4 | Jaccard ladder | `jaccard_by_resolution.csv/.png` |
| E5 | Adaptive + ablation | adaptive metrics + ablation CSV |
| E6 | Rainfall scenarios | `pfi_h_scenarios.csv` |
| E7 | Sandy negative control | `negative_control.json` |

## 6 Results

*(Leave blank until filled from live metadata — do not paste fixture accuracy as skill.)*

## 7 Discussion

- Decision scale matching; 311 reporting bias; tidal hydro as distance-to-water.
- What LM smoke can and cannot claim.

## 8 Conclusions

- Restate three contributions; open code + public layers; future: citywide, observed event rain, FloodNet.

## Figures / tables checklist

1. Data provenance table  
2. Multi-resolution risk / hotspot maps  
3. Jaccard vs coarse resolution  
4. Adaptive vs fixed / uniform fine  
5. Spatial CV vs random split  
6. Claim matrix (appendix)

## Forbidden wording checklist

- [ ] No “reproduced Svellingen Jaccard 0.14”
- [ ] No “citywide validated” from LM smoke  
- [ ] No “radar rainfall” unless ingest is non-synthetic  
- [ ] No PFIb / insurance skill claims  
