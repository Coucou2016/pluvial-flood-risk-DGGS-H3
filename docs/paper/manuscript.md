# Beyond aggregating a building index: spatially honest, event-conditioned pluvial flood learning on adaptive H3 grids

**Working manuscript (methods / IJDRR-shaped)**  
**Status:** Matured draft constrained to live Lower Manhattan open-data pilot metrics. Incomplete items marked 待补充.  
**Public code and documentation:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3

**Terminology ledger**

| Term | Canonical meaning |
|------|-------------------|
| H3 | Uber hexagonal Discrete Global Grid System |
| Open labels | DEP stormwater polygons, 311 flooding points, USGS Ida HWM — not PFIb |
| Spatial H3-block CV | GroupKFold holding out coarse H3 parent blocks |
| `PFI_h(c,r)` | Model rainfall-conditioned flood probability/index for cell `c` under rainfall condition `r` |
| PFIb | 7Analytics / Svellingen building-level pluvial flood index — **not used here** |
| LM pilot | Lower Manhattan open-data pilot (`n_cells=141`) |

---

## Abstract

Urban pluvial flood screening increasingly relies on machine learning and multi-resolution grids, yet many operational indices remain tied to proprietary insurance labels and evaluation protocols that ignore spatial leakage. Building on the H3 DGGS framing popularised for scalable pluvial mapping, we develop an **open-label** hexagonal learning protocol for a Lower Manhattan pilot: multi-source public flood indicators are joined to H3 cells, gradient-boosting models are assessed with **H3-block spatial cross-validation**, scale-loss is quantified with a Jaccard/F1 hotspot ladder, and an **adaptive** refinement stage screens parents using trained cell scores. We define `PFI_h(c,r)` explicitly as a rainfall-conditioned hex flood probability/index — a model output, not feature importance and not the proprietary PFIb product. On the live open-data pilot table (`n=141` cells; open-data assembly), spatial CV accuracy was **0.784 ± 0.069** (5 folds) with mean F1 **0.866**. Adaptive refinement retained about **57%** of uniform-fine cell count relative to an R11 reference while expanding high-score parents. We do **not** claim citywide skill, PFIb reproduction, or radar rainfall: event rainfall remains a synthetic constant hook, and current scenario tables show **no within-cell `PFI_h` change across rainfall intensities** (待补充). Oslo synthetic runs remain appendix-only pipeline QA.

---

## 1 Introduction

Intense short-duration rainfall can overwhelm urban drainage and generate pluvial flooding with limited warning. City-scale assessment needs representations that are (i) computationally scalable, (ii) updateable when new observations arrive, and (iii) evaluable without silent spatial leakage. Discrete Global Grid Systems (DGGS), and in particular Uber H3, provide nested hexagonal cells that support multi-resolution aggregation and neighbour queries.

Svellingen et al. (2026) demonstrated that machine-learning-derived building-level pluvial susceptibility (PFIb) can be aggregated into H3 cells to reduce spatial query cost by roughly two orders of magnitude, while also showing that hotspot sets can diverge sharply across resolutions (Jaccard similarity ≈ 0.14 between fine street-level and coarser neighbourhood hotspots on their proprietary stack). That work motivates H3 as a communication and screening fabric, but it does not provide an open, spatially honest learning protocol for jurisdictions that cannot access insurance claims.

This manuscript therefore asks: **can an open multi-source label stack on H3 support spatially blocked evaluation, diagnose scale-loss, and drive adaptive refinement with an explicit rainfall-conditioned cell index — without claiming PFIb reproduction?** Our contributions are:

1. An open-label H3 feature/label assembly protocol with explicit provenance fields for assembly mode, feature source, label source, and rainfall source.
2. Primary skill reporting via spatial H3-block CV, with random splits demoted to diagnostics.
3. A scale-loss Jaccard/F1 ladder and an adaptive H3 ablation screened by trained `PFI_h`, plus a binding definition of `PFI_h(c,r)`.

---

## 2 Related work

**Insurance / claims-driven pluvial indices.** Svellingen et al. (2026, IJDRR) operationalise PFIb through H3 aggregation and document multi-resolution hotspot loss. We cite this as the closest H3+pluvial precedent and as the claim boundary we refuse to cross (no PFIb). A related SSRN preprint frames the same H3 indexing narrative (Svellingen et al., SSRN).

**Hexagonal DGGS flood analytics.** Li et al. (2022) use an ISEA3H hexagonal DGGS as a multi-scale fabric for flood mapping under climate scenarios, supporting resolution-consistent predictors without relying on insurance labels. That line of work motivates DGGS as an analysis substrate; our contribution is an open-label **learning and evaluation protocol** on Uber H3 rather than climate-scenario inundation mapping alone.

**Spatial cross-validation.** GeoAI practice emphasises block / GroupKFold CV because random folds inflate scores under spatial autocorrelation (Sun, Hu, Lakhanpal & Zhou, 2023, *Handbook of Geospatial Artificial Intelligence*, spatial CV chapter). Flood susceptibility studies increasingly adopt spatial holdouts for the same reason. We instantiate blocking with coarse H3 parent IDs (a grid-/geo-attribute-style block holdout on H3 parents).

**Urban pluvial ML susceptibility.** City studies map susceptibility from DEM, land cover, and drainage proxies with classical ML (e.g. Bersabe & Jun, 2025, Seoul). Fewer combine open labels, H3 nesting, adaptive refinement, and rainfall-conditioned index honesty in one reproducible pipeline with blocked CV as the primary metric.

---

## 3 Study area and data

**Extent.** Lower Manhattan bounding box (approx. −74.02–−73.97°E, 40.70–40.76°N), as documented in the public repository configuration and download manifest. This is a **pilot extent**, not citywide New York City.

**Live layers (open downloads, August 2026).** DEM (USGS 3DEP subset), DEP stormwater flood polygons, building footprints, USGS Ida high-water marks, 311 flooding points (ArcGIS/CDN mirrors), FEMA Sandy inundation (negative control only), NLCD impervious fraction, NHDPlus HR hydro vectors (`dist_stream_m` as a **distance-to-water** proxy in a tidal/shoreline setting). FloodNet is stub/opt-in. Event rainfall is a **synthetic constant** Ida-like hook, not radar.

**Provenance.** Training table assembly reports open-data assembly with observed static features; rainfall may still carry an event-raster provenance tag rather than gauge/radar observation.

---

## 4 Methods

### 4.1 H3 representation

Training uses H3 resolution **R9** (configurable). Scale-loss diagnostics assemble labels at fine resolution **R10** and roll hotspots to parents R9/R8. Adaptive refinement expands selected parents to **R11**. Joins use EPSG:4326.

### 4.2 Features and open labels

Static predictors: elevation, slope, flow-accumulation proxy, impervious fraction, urban land-cover flag, building density, distance-to-water. Rainfall enters as rainfall intensity for scenario conditioning; observed static columns are tracked separately from rainfall so a constant synthetic grid is not marketed as radar.

Labels combine DEP polygon area fractions with 311 / Ida point counts into flood-risk / flood-class targets as **observed flood labels** (not ground truth). We do not use PFIb. FloodNet joins only when explicitly enabled and a non-empty layer exists.

### 4.3 Models and baselines

Primary learner: gradient-boosting classifier + continuous risk regressor. Baselines: L2 logistic / linear, and an elevation–impervious–slope–TWI-like ponding rule. In-sample metrics are optimistic references only.

### 4.4 Spatial H3-block cross-validation

Cells are grouped by coarse H3 parents; GroupKFold holds out entire blocks. Per-fold metrics are archived with the pilot run. Random i.i.d. splits are not primary.

### 4.5 Scale-loss diagnostics

Fine-resolution hotspot sets (top quantile of risk) are compared to parent-aggregated hotspots via Jaccard and F1 for mean/max/p90 rollups. Numeric values are **not** equated to Svellingen et al.’s PFIb Jaccard ≈ 0.14.

### 4.6 Adaptive refinement

After training, cell scores (`PFI_h` / flood probability) screen parents for refinement. Metrics: mixed-resolution cell counts versus fixed coarse and versus uniform fine (adaptive/uniform cell-count ratio). The pilot uses trained `PFI_h` as the screening score.

### 4.7 Event-conditioned `PFI_h(c,r)`

\[
\mathrm{PFI}_h(c,r)=\widehat{P}(Y_c=1\mid X_c,r)
\]

Static features \(X_c\) are held fixed while rainfall condition \(r\) varies across named scenarios. This is a **model output**, not SHAP/permutation importance and not PFIb.

### 4.8 Negative control

FEMA Sandy coastal inundation overlaps are reported for separation checks only and are never training labels.

---

## 5 Experiments

| ID | Description | Role |
|----|-------------|------|
| E1 | Assemble open LM table | Feature/label table for the pilot bbox |
| E2 | Spatial CV | Primary blocked accuracy / F1 |
| E3 | Baselines | Diagnostic comparison |
| E4 | Jaccard ladder | Scale-loss hotspot similarity |
| E5 | Adaptive + ablation | Cell-count efficiency vs uniform fine |
| E6 | Rainfall scenarios | Within-cell `PFI_h` response across intensities |
| E7 | Sandy negative control | Coastal overlap checks (not training) |

Reproducible tables and figures are released with the public repository; process detail lives in the companion research report.

---

## 6 Results

All numbers below are copied from the live Lower Manhattan open-data pilot (`n_cells=141`). They do **not** describe citywide performance.

### 6.1 Spatial H3-block CV (primary)

| Metric | Value |
|--------|-------|
| n_cells | 141 |
| spatial_cv_n_folds | 5 |
| spatial_cv_n_blocks | 7 |
| spatial_cv_accuracy_mean ± std | 0.784 ± 0.069 |
| spatial_cv_f1_mean | 0.866 |
| spatial_cv_r2_mean ± std | 0.030 ± 0.343 |
| spatial_cv_mae_mean | 0.332 |
| random_split_val_accuracy (diagnostic only) | 0.690 |

Per-fold accuracy/F1: Fold0 0.755 / 0.850; Fold1 0.760 / 0.850; Fold2 0.773 / 0.872; Fold3 0.714 / 0.813; Fold4 0.917 / 0.944.

**Reading.** Mean blocked accuracy near 0.78 indicates that an open-label H3 table can be trained under spatial holdout on this pilot bbox. Fold4’s high accuracy is a single-block outcome on small test counts and must not be generalised to citywide skill. Random-split accuracy (0.690) remains diagnostic only and is **not** the primary claim.

### 6.2 Scale-loss Jaccard ladder (open labels)

Fine resolution R10, hotspot quantile 0.9:

| coarse_res | aggregation | jaccard | f1 |
|------------|-------------|---------|-----|
| 8 | mean | 0.167 | 0.286 |
| 8 | max | 1.000 | 1.000 |
| 8 | p90 | 1.000 | 1.000 |
| 9 | mean | 0.977 | 0.988 |
| 9 | max | 1.000 | 1.000 |
| 9 | p90 | 0.977 | 0.988 |

**Reading.** Mean parent rollup at R8 loses most fine hotspots (Jaccard 0.167), illustrating scale smoothing; max/p90 retain extrema by construction. These values are open-label diagnostics on this bbox — **not** a reproduction of Svellingen et al. 0.14.

### 6.3 Adaptive vs fixed / uniform fine

| Field | Value |
|-------|-------|
| score used for screening | `PFI_h` |
| n_fixed_coarse (R9) | 141 |
| n_adaptive_mixed | 3933 |
| n_uniform_fine (R11) | 6909 |
| adaptive_cell_count_ratio (adaptive/uniform) | 0.569 |
| n_parents_refined | 79 |
| score_quantile | 0.8 |

Adaptive mixed grids use fewer cells than uniform R11 (~57%) while refining 79/141 coarse parents. This is a **cell-count** efficiency statement on the pilot table, not a verified compute-time saving at city scale.

### 6.4 Rainfall scenarios (`PFI_h`)

141 cells × scenarios {moderate 25, heavy 40, ida_like 75, extreme 100 mm/h}; rainfall provenance remains event-raster (synthetic constant hook); assembly is open-data.  
**Observed:** mean `PFI_h` ≈ **0.802888** for every scenario; **within-cell range across scenarios = 0**.  
**Interpretation:** the current pilot does **not** demonstrate rainfall-conditioned discrimination. Treat scenario maps as schema/QA until the predict path / feature set yields non-zero response (待补充). Definition of `PFI_h(c,r)` remains binding for future runs.

### 6.5 Sandy negative control

Open-data assembly: n_cells=141; n_coastal=31; n_pluvial=71; n_both=23; n_coastal_only=8; frac_coastal_only≈0.057; pluvial_minus_coastal_mean_score≈0.120. Coastal overlay is **not** a training label.

---

## 7 Discussion

The LM pilot shows that an open-label H3 table can be trained and evaluated with blocked CV, that mean rollups can erase fine hotspots (scale-loss), and that trained-score adaptive refinement reduces uniform-fine cell count. These results support **protocol credibility** under stated boundaries, not product-ready city maps.

Relative to Svellingen et al. (2026), the dialogue is conceptual: they aggregate a proprietary building index (PFIb) into H3 for scalable communication; we learn on public labels with spatial holdouts and an explicit non-PFIb `PFI_h(c,r)`. Our open-label Jaccard mean R10→R8 (0.167) should **not** be narrated as matching their PFIb Jaccard ≈ 0.14 — different labels, resolutions, and hotspot definitions.

Limitations dominate external validity: small extent (`n=141`), label bias (311 reporting), tidal hydro proxy, synthetic rainfall, flat scenario `PFI_h`, no FloodNet holdout, and no workflow schematic figure (Figure 1 待补充). Random-split accuracy must not displace spatial CV in claims. Fold-level variance (including Fold4) further warns against over-interpreting a single pilot run.

**What would close key gaps (completion criteria):** (i) ingest observed event rainfall with non-synthetic provenance; (ii) non-flat scenarios — within-cell `PFI_h` range > 0 across rainfall intensities on the same static \(X_c\); (iii) expanded bbox / citywide profile with the same spatial CV protocol; (iv) FloodNet held-out validation when a non-empty layer exists.

---

## 8 Conclusions

We present a reproducible open-label H3+ML protocol with spatial block CV, scale-loss diagnostics, adaptive refinement, and an explicit non-PFIb `PFI_h(c,r)` definition. Live Lower Manhattan pilot metrics support pipeline credibility under stated boundaries. Next: observed event rainfall, non-degenerate rainfall response, expanded bbox / citywide profile, and FloodNet validation — all 待补充.

---

## Figure captions

**Figure 2. Scale-loss Jaccard ladder (open labels).** Jaccard and F1 between fine R10 hotspot parents and coarse R8/R9 hotspots under mean/max/p90 aggregation. Mean R8 Jaccard ≈ 0.167 illustrates smoothing; do **not** equate to Svellingen et al. PFIb Jaccard ≈ 0.14.

**Figure 3. Adaptive vs uniform fine cell counts.** Fixed coarse (R9), adaptive mixed, and uniform fine (R11) cell counts (adaptive/uniform ≈ 0.569). Cell-count efficiency only; not citywide runtime proof.

**Figure 4. Spatial H3-block CV fold metrics.** Per-fold accuracy and F1 on the LM pilot table (`n=141`). Primary claim uses mean ± std across folds; individual high folds are not citywide skill.

**Figure 1 (workflow schematic).** 待补充.

---

## Data and code availability

Public repository (code, configs, tests, paper docs, and small summary tables; large rasters/geojson, trained model binaries, and large parquet files excluded): https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 (`pluvial-flood-risk-dggs-h3` v0.1.0). Layer provenance and download manifests are released with the repository. Demo/Oslo paths are QA only. A deep process-oriented research report accompanies the manuscript in the same documentation folder.

## References (selected)

1. Svellingen, W., Torgersen, G., Bruland, O. & Muthanna, T. Scalable pluvial flood risk assessment: A data-driven framework integrating machine learning (ML) and discrete global grid systems (DGGS H3). *Int. J. Disaster Risk Reduction* **137** (2026). https://doi.org/10.1016/j.ijdrr.2026.106091  
2. Svellingen, W. et al. Indexing areas vulnerable to pluvial floods—Using Machine Learning and H3 Hexagonal Grid System. *SSRN* (preprint). https://doi.org/10.2139/ssrn.5875380  
3. Li, M., McGrath, H. & Stefanakis, E. Multi-Scale Flood Mapping under Climate Change Scenarios in Hexagonal Discrete Global Grids. *ISPRS Int. J. Geo-Inf.* **11**, 627 (2022). https://doi.org/10.3390/ijgi11120627  
4. Sun, K., Hu, Y., Lakhanpal, G. & Zhou, R. Z. Spatial cross-validation for GeoAI. In Gao, S., Hu, Y. & Li, W. (eds) *Handbook of Geospatial Artificial Intelligence* (Taylor & Francis, 2023). Chapter PDF: https://www.acsu.buffalo.edu/~yhu42/papers/2023_GeoAIHandbook_SpatialCV.pdf  
5. Bersabe, J. T. & Jun, B.-W. The Machine Learning-Based Mapping of Urban Pluvial Flood Susceptibility in Seoul Integrating Flood Conditioning Factors and Drainage-Related Data. *ISPRS Int. J. Geo-Inf.* **14**, 57 (2025). https://doi.org/10.3390/ijgi14020057  

Additional venue-specific references 待补充.
