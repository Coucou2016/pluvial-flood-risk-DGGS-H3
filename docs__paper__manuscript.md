# Spatially blocked pluvial-flood susceptibility learning on the H3 grid using heterogeneous open public data

## Highlights

- An H3-native protocol joins open-evidence assembly, spatially blocked validation with a physical guard band, and resolution diagnostics on one hierarchical grid
- The main target is the **binary union** `evidence_positive = (DEP area > 0) | (311 count > 0) | (Ida HWM count > 0)`, kept as **evidence-positive / evidence-unrecorded** (model-derived DEP, crowd-reported 311, observed Ida high-water marks) — not verified flood / non-flood ground truth and not a cross-source continuous composite
- Prevalence-aware baselines change how classification skill is read: Lower Manhattan Option B (n = 262) exceeds always-positive on accuracy (0.828 vs 0.637) and fold-mean F1 (0.868 ± 0.043 vs 0.769); expanded pilot (n = 956) fold-mean F1 0.824 ± 0.039 vs 0.646
- **Independent FloodNet event-level validation was NOT established**: strict held-out ROC-AUC is 0.451 (LM) / 0.479 (expanded), with no-event sensor cells scoring at least as high as event cells. This negative result is a core finding, not a footnote.
- Domain-masked native R10 overlay with a strict 10% area budget shows substantial scale loss (mean reconstruction MAE 0.238 / RMSE 0.345 to R9; soft Jaccard 0.193 to R9, 0.114 to R8); adaptive refinement recalls 0.882 of uniform-R11 hotspots at 57.4% of the uniform cell count

---

## Abstract

Urban pluvial flooding develops when intense rainfall overwhelms drainage before water reaches a watercourse. City-scale screening needs a spatial support that can be updated as new evidence arrives and that can be evaluated without inflating skill through spatial leakage. Many published indices draw on proprietary damage or insurance labels, and random train–test splits can overstate performance when nearby cells appear in both partitions. This study evaluates an H3-native protocol in which the hexagonal discrete global grid is the common support for evidence assembly, spatially blocked validation, and resolution control, using only heterogeneous open public data.

Flood evidence is assembled on H3 cells from three sources kept distinct in the training table: model-derived New York City DEP stormwater polygons (categories 1–2), crowd-reported NYC 311 street-flooding complaints, and observed USGS Hurricane Ida high-water marks. Binary labels are framed as evidence-positive versus evidence-unrecorded. A gradient-boosting classifier is fitted under H3-block spatial cross-validation that withholds entire parent cells, with a physical guard band around every held-out block and a spatial-block bootstrap for confidence intervals. After evaluation, separate deployment models are refitted on all cells for descriptive maps and adaptive screening only.

In the Lower Manhattan pilot (Option B; n = 262 R9 cells; 63.7% evidence-positive), spatial cross-validation accuracy is 0.828 ± 0.053 and fold-mean F1 is 0.868 ± 0.043, above the always-positive baseline (0.637 and 0.769), with pooled out-of-fold ROC-AUC 0.849 (95% spatial-block bootstrap CI 0.728–0.951) and average precision 0.850 (CI 0.778–0.965). In the expanded pilot (n = 956; 47.9% evidence-positive), accuracy is 0.824 ± 0.036 and F1 is 0.824 ± 0.039, both above the fold-mean constant-class baselines, with pooled ROC-AUC 0.887 (CI 0.831–0.929) and average precision 0.827 (CI 0.774–0.883). A domain-masked native R10 label overlay with tie-aware fractional hotspot membership under a strict 10% area budget shows hotspot membership degrading under coarsening (mean soft Jaccard 0.114 to R8; 0.193 to R9). Adaptive refinement uses about 57% as many cells as a uniform fine grid. The primary screening quantity is S_h(c)=f_θ(X_c); because training rainfall is constant, rainfall-conditioned S_h(c,r) is not claimed. Independent event-level validation with the FloodNet sensor network was **not** established (strict held-out ROC-AUC 0.451 LM / 0.479 expanded, with no-event sensor cells scoring at least as high as event cells), so the claim is limited to blocked-CV discrimination of a heterogeneous open-evidence target rather than external event-level skill. Production assembly is fail-closed: missing layers or NaNs abort rather than silently filling synthetic features. Citywide skill and rainfall-conditioned discrimination remain open.

**Keywords:** pluvial flood susceptibility; H3; discrete global grid; spatial cross-validation; machine learning; open data.

---

## 1. Introduction

Urban flooding occurs mainly during intense rainfall in densely built areas with limited drainage. Its pluvial form—flooding that develops when rainfall overwhelms drainage before entering watercourses—can appear rapidly and with little warning [1]. Assessing this hazard at city scale requires representations that are computationally scalable, updateable as new observations arrive, and evaluated without inflated performance. Two constraints recur in data-driven pluvial-flood screening. First, some published indices rely on proprietary damage or insurance records, so the labels are neither public nor transferable to jurisdictions without comparable archives. Second, random train–test splits can overestimate generalisation when spatially proximate observations fall into both the training and test sets because of spatial autocorrelation. For city-scale screening these constraints create a spatial-representation problem as well as a modelling problem: observations, predictions, and evaluation need a support that remains coherent as scale changes.

Discrete Global Grid Systems, and the hexagonal H3 system in particular [2], offer a scalable substrate for integrating observations, predictions, and multi-resolution analysis. H3 is a hierarchical, predominantly hexagonal spatial index with neighbourhood operations and parent–child relationships across resolutions [3]. Hexagonal grids have been used for multi-scale flood mapping under climate scenarios [4], and a closely related line of work aggregates a pre-existing machine-learning building-level pluvial susceptibility index into H3 cells to reduce query cost and expose resolution-dependent hotspot loss [5,6]. In that formulation H3 mainly serves as a multi-resolution aggregation and communication layer for an inherited index. What remains open is whether the same hierarchy can also support model fitting and evaluation across unseen spatial blocks when the labels themselves are assembled from open public evidence.

That gap motivates an H3-native learning and evaluation architecture: the grid is the common spatial support rather than only an aggregation layer. Heterogeneous public evidence is assembled directly on H3 cells, coarse H3 parents define spatial holdouts, and the same hierarchy is used to examine scale effects and guide selective refinement. The contribution is therefore the linkage of evidence construction, spatial validation, and resolution control within one hierarchical reference; each component has precedents when taken alone [4,7,8,9,10]. Throughout, the fitted positive-class model output is treated as a susceptibility score and is kept distinct from both feature-importance measures and the H3-aggregated building index of Svellingen et al. [5].

The analysis asks three questions. First, does predictive performance persist when entire H3 parent blocks are withheld, relative to class-prevalence baselines? Second, how does hotspot membership change as fine-scale evidence is aggregated? Third, can trained cell scores concentrate fine-resolution representation without a uniform fine grid? These questions are examined on two Manhattan pilot extents rather than at citywide scale.

## 2. Study area and data

The analysis uses two Manhattan pilot extents. The smaller is a Lower Manhattan bounding box (74.02–73.97°W, 40.70–40.76°N) that yields **262** H3 resolution-9 cells (Major Revision Option B: the manuscript bbox is the analysis extent; a legacy 141-cell smoke subset is retained only for fast QA). The larger expanded-Manhattan box spans approximately 74.03–73.94°W, 40.68–40.80°N (956 R9 cells). Both lie within New York City and are described as pilot extents throughout. The H3 support follows these bounding boxes; the implications of rectangular support versus a strict land footprint are discussed in Section 5.4.

All source datasets are third-party public inputs. Cell-level features, labels, fitted models, predictions, diagnostics, tables, and figures are author-derived outputs. Elevation is from the USGS 3D Elevation Program [11]; impervious fraction from the National Land Cover Database annual fractional impervious surface [12]; hydrography from NHDPlus High Resolution [13]; flood evidence from New York City Department of Environmental Protection stormwater flood polygons [14], NYC 311 street-flooding complaints [15], and USGS Hurricane Ida high-water marks [16]; and a coastal-confounding diagnostic from FEMA Sandy storm-surge inundation [17]. Machine-readable provenance is recorded in the repository download manifest (official landing pages, service URLs, SHA-256 hashes, and mirror status). DEP stormwater still resolves via a public ArcGIS FeatureServer mirror (identity not officially verified in the manifest). Street-flooding complaints are extracted from the official NYC Open Data historical dataset 76ig-c548 (2010–2014; descriptor Street Flooding (SJ); ordered pagination; unique_key deduplication; official identity verified). USGS Ida high-water marks are official (DOI 10.5066/P9OMBJPQ). Building footprints supply building density. A distance-to-mapped-water proxy is derived from NHDPlus hydrography; because Lower Manhattan hydrography is dominated by tidal rivers and shoreline features, this predictor is interpreted as shoreline/tidal-water distance rather than inland drainage density. Polygon intersection area fractions are computed after projecting geometries to EPSG:2263. Table 1 lists the layers and their roles.

**Table 1. Open data layers and their roles in the framework.**

| Layer | Source | Form | Role |
|---|---|---|---|
| Elevation | USGS 3DEP | Raster | Elevation, slope, flow-accumulation proxy |
| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction |
| Hydrography | USGS NHDPlus HR | Vector | Shoreline/tidal-water distance proxy; NHD water polygons for land-mask sensitivity |
| Building footprints | NYC MapHub | Vector | Building density |
| Flood evidence — stormwater | NYC DEP moderate-flood stormwater polygons, current sea levels (Flooding_Category 1–2) | Vector | Model-derived flood-evidence target (continuous and binary) |
| Flood evidence — complaints | NYC 311 street-flooding complaints (official dataset 76ig-c548, 2010–2014 Street Flooding (SJ)) | Vector | Crowd-reported flood-evidence target (continuous and binary) |
| Flood evidence — observations | USGS Hurricane Ida high-water marks | Vector | Observed flood-evidence target (continuous and binary) |
| Negative control | FEMA Sandy surge inundation | Vector | Coastal-overlap diagnostic; never a training label |
| Held-out sensor events | NYC FloodNet events (aq7i-eu5q) + sensor metadata (kb2e-tjy3) | Vector | Strict held-out diagnostic only; never a training label |
| Rainfall condition r | Synthetic constant grid (75 mm/h; Supplement only) | Raster | Not used as a main claim; S_h(c) is rainfall-invariant here |

The main cell-level target is a **binary union of the available open evidence sources**:

`evidence_positive = (dep_area_frac > 0) | (complaint_count > 0) | (ida_hwm_count > 0)`.

The three sources are retained **separately** in the training table (`dep_area_frac`, split into nuisance/deep fractions; `complaint_count`/`complaint_presence`; `ida_hwm_count`/`ida_hwm_presence`/`ida_hwm_quality`) together with an `evidence_sources` string recording which sources are present per cell. The earlier cross-source continuous `max(area_frac, point_presence)` composite is **removed from the main result**: a single regressor on that composite is no longer a paper headline. Where a continuous quantity is retained it is DEP-only and named `evidence_coverage_proxy` (the DEP polygon intersection area fraction), never a cross-source maximum. Cells with any positive evidence are **evidence-positive**; all others are **evidence-unrecorded**—not verified flood versus verified non-flood.

**Table 1b. Evidence semantics.**

| Source | Observation vs model | Time | Geometry | Dominant bias | Training role |
|---|---|---|---|---|---|
| DEP stormwater polygons (cat. 1–2) | Hydrologic–hydraulic **model output** | Current sea level (2050 SLR as sensitivity) | Polygon area fraction | Model structure/parameters; coastal “future high tides” class excluded | `training_label` |
| NYC 311 street-flooding complaints | Crowd-**reported**, unverified | 2010–2014 | Point count/presence | Reporting and mapping bias [7,8] | `training_label` |
| USGS Hurricane Ida high-water marks | **Observed** (single event) | Hurricane Ida, 2021 | Point count/presence/quality | Sparse (n = 6 cells in the expanded pilot) | `training_label` |
| FEMA Sandy surge inundation | Model/mapped coastal | Hurricane Sandy, 2012 | Polygon overlap | Coastal, not pluvial | `negative_control` (never a training label) |
| NYC FloodNet sensor events | Sensor-**observed** events | Pre-freeze, enforced | Point/sensor cells | Sparse sensor footprint; sensor exposure | `external_validation` (never a training label) |

Three properties of this target matter for interpretation. First, the three sources are not interchangeable measurements of one latent variable: the DEP polygons are hydrologic–hydraulic model outputs of moderate stormwater flooding at current sea levels (category 1, nuisance flooding with ponding depth ≥4 in to <1 ft; category 2, deep-and-contiguous flooding ≥1 ft; the coastal “future high tides” class is excluded); the 311 complaints are crowd-reported and unverified; only the high-water marks are direct observations of an actual event (Ida, 2021). Second, the sources span different times and forcings and are therefore collapsed into a static “has there ever been any evidence here” label rather than a per-event inundation label. Third, the target is not a severity measure: any single source saturates the binary indicator, so the model learns to rank the co-occurrence of heterogeneous evidence rather than flood depth or a calibrated probability.

Each source is retained separately in the assembled table for auditability: DEP contributes an area-fraction column (further split into nuisance and deep categories), 311 contributes count and presence fields, and high-water marks contribute count, presence, and quality fields, with an evidence-source string recording which sources are present per cell. The binary target is the union of these source-specific columns rather than an undifferentiated merge. NYC 311 records in particular reflect reporting and mapping processes, and their biases have been documented previously [7,8].

NYC Open Data FloodNet street-flooding events (dataset aq7i-eu5q; published 2026-03-03) and sensor deployment metadata (kb2e-tjy3) are retained for an **enforced held-out diagnostic** and are never joined into the training or evaluation target. The analysis freeze is enforced on the data: events are filtered at query time and again after download to `flood_start_time < 2026-08-30`, with an assertion on the maximum retained timestamp, and sensors are filtered on `date_installed`. Among study cells that contain at least one FloodNet sensor, out-of-fold scores show weak and, for the pooled footprint, inverted discrimination of cells with one or more quality-controlled sensor flood events (Lower Manhattan ROC-AUC 0.451 on 23 sensor cells; expanded 0.479 on 57 sensor cells; no-event sensor cells score at least as high as event cells), so sensor-event agreement is **not** claimed as external skill. Filtering cells by sensor exposure does not remove the negative result (LM ROC-AUC 0.467 at ≥90 d, 0.333 at ≥180 d; expanded 0.521 at ≥90 d, 0.617 at ≥365 d), and the result is reported in full whether or not it is above 0.5.

The DEP service provides the moderate-flood polygon layer under both current sea levels and a projected 2050 sea-level-rise scenario. The current-sea-level layer is the primary evidence; the 2050 variant is retained as a sensitivity. Under the sea-level sensitivity protocol, re-running the target with the 2050 layer shifts Option B (n = 262) positive prevalence from 63.7% to 67.6% and pooled ROC-AUC from 0.848 to 0.836; in the expanded pilot the shifts are 47.9% to 50.0% and 0.882 to 0.872. These changes do not alter any substantive conclusion.

Rainfall enters the framework only as a deferred conditioning variable. The present pilots define the primary susceptibility score as S_h(c)=f_θ(X_c) from static predictors alone. A constant synthetic rainfall input (Ida-like 75 mm/h) is retained for scenario bookkeeping in the Supplement but produces a flat within-cell response and is not a main claim. Event-conditioned S_h(c,r) is left for future work.

## 3. Methods

The method uses the H3 hierarchy as a common spatial reference while assigning distinct roles to the resolutions used for model fitting, spatial blocking, scale diagnostics, and adaptive refinement (Fig. 1). Production feature assembly is fail-closed: if a required static layer is missing or yields NaN after zonal aggregation, the run aborts rather than substituting synthetic hash features.

### 3.1 Evidence assembly on H3

For a chosen bounding box and modelling resolution R9, every intersecting H3 cell is listed and retained as a row. Raster predictors are summarised as zonal means over each cell; vector predictors and evidence layers are summarised by intersection area fraction (polygons) or presence/count (points). All H3 indexing and spatial joins use longitude–latitude coordinates (EPSG:4326). Cell areas use H3 native cell-area calculations; distance-to-water is computed as the nearest distance from the cell centroid to mapped NHD water features after projecting both to EPSG:2263 (metres), not as a WGS84 haversine distance; terrain derivatives are computed on the raster grid and averaged zonally over each cell. Polygon intersections use EPSG:2263. The binary `evidence_positive` target is formed as in Section 2, with source-specific columns retained alongside it. Fail-closed assembly means that incomplete downloads or NaN zonal statistics abort the run; fixture or synthetic feature fill is disabled for production paper artefacts.

### 3.2 H3 representation roles

Supervised modelling uses H3 resolution 9 (R9) as the training and evaluation support (edge length on the order of a city block in mid-latitudes). Resolution 10 (R10) provides the fine-evidence support for the scale-loss diagnostic, with hotspots subsequently rolled to R9 and R8; model fitting remains at R9 throughout. Adaptive refinement is a post-training step that replaces selected R9 cells with their resolution-11 (R11) descendants. The workflow is summarised in Fig. 1.

### 3.3 Features

Static predictors are elevation, slope, a DEM-derived D8 accumulation proxy (`dem_d8_accum_proxy`), impervious fraction (NLCD), building density, building footprint area fraction (`building_area_fraction`), and distance to mapped water (`dist_mapped_water_m`). Elevation, slope, and the accumulation proxy are zonal means over each cell; impervious fraction is a zonal mean of the NLCD fractional-impervious surface; building density is the building-centroid count divided by the **land** area of the cell (with the footprint area fraction carried separately so exposure is not encoded only by a count); distance to mapped water is the projected nearest-water distance (EPSG:2263 metres). Slope is computed nodata-safely: invalid DEM cells are nearest-filled only for the gradient convolution and then restored to nodata and dilated one ring, so edge cells are not silently assigned a zero slope. Trees are fitted on raw features; a `StandardScaler` is used only inside the logistic-regression baseline pipeline, never before the gradient-boosting model (tree splits are invariant to monotone rescaling, so a scaler would only add an invariance-fragile preprocessing step). The previously considered urban land-cover flag (impervious fraction > 0.45) and the constant `rainfall_mm_h` column are excluded from the estimator feature set — the former is a deterministic copy of impervious fraction and the latter is zero-variance in training. Rainfall is handled separately as the condition r rather than as a static feature; a future event interface is documented as `EVENT_FEATURE_COLUMNS` and any scenario hook must pass a `min_unique` uniqueness guard before a constant feature can be presented as a learned driver.

### 3.4 Models and baselines

The primary learner is a gradient-boosting classifier with 80 estimators, maximum depth 4, and learning rate 0.08, fitted on raw features with a fixed random seed (42); all other estimator parameters retain the scikit-learn 1.8 defaults. These hyperparameters were **pre-specified without nested cross-validation retuning**, to avoid an additional tuning loop on the small pilot samples and to keep evaluation comparable across ablations. Classification uses a **prespecified operating threshold of 0.5** for comparability across folds and pilots; a train-fold max-F1 threshold sensitivity is reported in the registry only. An evidence-score regressor is retained only as a supplement diagnostic and is not a paper headline, because the main target is now binary. Three nested feature-set models are reported for construct validity: a **physics-only** model (terrain, imperviousness, accumulation proxy, water distance), a **reporting/exposure-only** model (building density and building area fraction), and the **full** model (all features), so that ranking discrimination can be attributed to physical drivers versus exposure/reporting proxies. (The 311 target is itself partly a reporting-opportunity signal, which is why the reporting-only model is reported rather than treated as construct truth.)

Two constant classifiers—always-positive and always-negative—are computed on each held-out fold, and accuracy and F1 are reported alongside these constant classifiers to provide a class-prevalence reference. The majority-class identity is determined from pooled target counts, and the constant-baseline accuracy and F1 use the same fold-wise aggregation as the model metrics. Two further baselines are included for diagnostic comparison: an L2-regularised logistic classifier and a ponding rule defined by the weighted combination

`0.40·(1 − elev_norm) + 0.35·imperv + 0.15·(1 − min(slope, 15°)/15°) + 0.10·TWI_norm`,

where elev_norm and TWI_norm are min–max normalised elevation and a topographic-wetness proxy, and a cell is classified positive when the score is at least 0.5. In spatial cross-validation the min–max bounds for the ponding rule are computed from the training fold only and applied to the held-out fold, so the baseline does not use test-set distribution information. In-sample metrics are treated as optimistic references only. Table 2 summarises the models and baselines.

**Table 2. Model and baseline specifications.**

| Model / baseline | Configuration | Role |
|---|---|---|
| Gradient-boosting classifier | 80 estimators, max depth 4, learning rate 0.08, raw features (no scaler), random seed 42 | Primary binary learner |
| Physics-only / reporting-only / full GBM | Same configuration on nested feature subsets | Construct-validity models (AUC_physics / AUC_reporting / AUC_full) |
| Gradient-boosting regressor | Same configuration | Evidence-coverage regressor (supplement diagnostic only) |
| L2-regularised logistic classifier | scikit-learn 1.8 defaults, `StandardScaler` inside the pipeline | Diagnostic baseline |
| Ponding rule | Weighted combination of normalised elevation, impervious fraction, slope, and TWI; positive when score ≥ 0.5; bounds from training fold only | Diagnostic baseline |
| Always-positive / always-negative | Constant class prediction | Prevalence-aware baselines on each held-out fold |

### 3.5 Spatial H3-block cross-validation and deployment models

Each R9 cell is assigned to the H3 parent two resolutions coarser (**parent-resolution offset = 2, giving R7 blocks**). Up to five-fold GroupKFold partitions these R7 groups so that no R7 block appears in both the training and the held-out portion of a fold; when fewer than five blocks are available, the number of folds equals the number of blocks. This changes the generalisation target from “new randomly drawn cells” to “new spatial blocks”, which is closer to the transfer a screening product would face. Because adjacent blocks can still leak across a shared boundary, a **physical guard band** is added: after the parent-block split, training cells within a metre buffer (projected to EPSG:2263) of any held-out cell are purged, and an equivalent H3 `grid_disk` purge is also available. Buffer sensitivity is reported at 0/250/500/1000 m together with the retained-training fraction (Table 3b); a fold that becomes single-class aborts rather than being silently dropped. For each held-out cell the predicted class score is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]—are computed from pooled out-of-fold (OOF) predictions. Because OOF cells are spatially correlated, pooled ROC-AUC and AP confidence intervals are computed with a **spatial-block bootstrap** that resamples H3 parent blocks (1000 draws), not cells. H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons only.

After evaluation is complete, separate deployment classifiers and regressors are refitted on all cells (fit_rows equals the pilot cell count: 262 or 956). These all-cell models are used only for descriptive maps (Fig. 2c) and adaptive-grid screening and are never used to calculate held-out performance metrics. Model manifests record the model role (evaluation versus deployment), the number and hash of training cells, configuration, software versions, and random seed.

The R7 block size is fixed a priori; block-size sensitivity, leave-one-R7-block-out (LOBO), and Moran’s I of the evidence target and of OOF residuals are reported in Section 4.8 and Table 8.

### 3.6 Domain-masked scale-loss diagnostics

Fine-resolution hotspot membership is defined on native R10 evidence scores using a fixed 10% area budget with fractional allocation within boundary ties (no lexicographic H3-index tie-break and no cell-count top-k). Fine cells are restricted by a study_domain_mask so that R10 parents at modelling resolution R9 equal the modelling R9 set (Option B: n_coarse = 262), removing the bbox-induced parent surplus that previously inflated the coarse support. For each coarse parent p the reference membership is the area-weighted fraction w_ref(p)=Σ_i∈p a_i w_i / Σ_i∈p a_i. Coarse hotspots are selected under the same area budget on area-weighted mean, maximum, or p90 parent scores, allowing fractional membership of the final tied group so that selected coarse area equals the fine budget within floating-point tolerance.

The primary overlap metric is the area-weighted soft Jaccard; hard-set Jaccard is reported only as a seeded tie-resolution sensitivity (1000 draws; median and 95% interval). Scale loss is quantified by a **true reconstruction error**: each coarse parent score is expanded back onto its fine children and compared with the fine truth, area-weighted, giving `reconstruction_mae` and `reconstruction_rmse` (and a rank correlation on the reconstruction). The previous parent-mean-versus-itself comparison is an algebraic identity (MAE = RMSE = 0, Spearman = 1) and is retained only as an implementation identity check in the registry (`continuous_mae` / `spearman_rank_corr`), never as a headline scale-loss number. Maximum aggregation can approach high Jaccard for structural reasons (parent collapse under max) and is not interpreted as a preferred strategy. Table 4 and Fig. 6b are read from the same archived diagnostics table; figures never recompute Jaccard independently. The fine R10 reference is assembled by overlaying the raw polygon and point geometries directly onto R10 cells, not by inheriting scores from R9 parents. These diagnostics use different labels, resolutions, and hotspot definitions from the Jaccard value reported by Svellingen et al. [5] and are not a reproduction of that result.

### 3.7 Source ablation and coastal diagnostic

Because the target is the union of three heterogeneous sources, construct validity depends on whether ranking discrimination is driven by one source alone—in particular, whether the model merely re-derives the DEP hydrologic–hydraulic map from terrain and imperviousness predictors that share its drivers. The same spatial block cross-validation is therefore refit to DEP-only, 311-only, HWM-only, 311+HWM, and the full evidence union; to the union with mapped-water distance removed; and to 311-only with building density removed. In addition, three nested feature-set models are fitted on the union target—**physics-only** (terrain, imperviousness, accumulation proxy, mapped-water distance), **reporting/exposure-only** (building density and building area fraction), and **full**—to separate physical drivers from reporting/exposure proxies (Section 4.8; Table 7).

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a coastal-confounding diagnostic (a `negative_control` source). Because the evidence label is a union of polygon overlap and point presence, the pluvial grouping in the diagnostic is derived from the same evidence-positive definition used elsewhere, so that a cell carrying only a point label is counted as pluvial rather than misassigned to the “neither” group. The control reports the overlap between pluvial evidence and coastal inundation and the difference in the **out-of-fold model score** between pluvial-only and coastal-only cells. The score compared is the held-out gradient-boosting score, never the evidence label, because a coastal-only cell has `evidence_positive = 0` by construction; comparing label scores would be circular. Sandy labels are never used as training labels. As a sensitivity, 311 complaints created in the Sandy landfall window 2012-10-27 to 2012-11-05 are excluded before rebuilding the label, while coastal diagnostics still use OOF scores from the primary (unmodified) CV.

### 3.8 Adaptive representation experiment (Supplement)

After training, the deployment model score screens R9 cells for refinement as an **adaptive representation experiment** reported by cell count (Supplementary Fig. S2; Table 5). A cell is selected when its score is at or above the 0.8 quantile of all cell scores, or when its predicted score is uncertain (uncertainty 1 − 2|p − 0.5| of at least 0.7, i.e. p between 0.35 and 0.65); the selection is then expanded to include the one-ring H3 neighbourhood among the R9 cells. Each selected cell is replaced by its R11 descendants while unselected cells remain at R9. A separate Option A diagnostic re-extracts R11 features on refined children and scores them with the post-urban-drop deployment model; cells with NaN static features at DEM edges are dropped before scoring. The primary adaptive metric is the **hotspot refinement recall**: of the uniform-R11 hotspots (top 10% by score), the fraction whose own R11 cell was actually refined to R11 — the previous “hotspot recall” was a coverage tautology, because a complete mixed-resolution partition trivially covers every hotspot. Refinement precision and enrichment, plus a cost–recall curve over score quantiles {0.70, 0.75, 0.80, 0.85, 0.90, 0.95} and neighbour expansion {0, 1}, are reported, together with refined-child completeness counts (total / scorable / missing / missing fraction) and best/worst-case recall bounds that treat DEM-edge-missing hotspots as hits/misses. The primary claim remains cell-count concentration relative to a uniform fine grid; runtime and memory are not claimed as efficiency gains.

### 3.9 Susceptibility score (rainfall deferred)

The primary cell index is

`S_h(c) = f_θ(X_c)`,

the classifier’s positive-class score from static predictors X_c (not a calibrated probability; not PFIb). Rainfall-conditioned S_h(c,r) is defined for future event-based analyses but is not claimed here: the pilot’s constant synthetic rainfall has zero training variance, so flat scenario loops are retained only as a limitation and Supplement note.

## 4. Results

### 4.1 Spatial pattern of evidence, predictions, and the deployment score

On the 262-cell Lower Manhattan R9 support (Option B), the source-specific evidence, out-of-fold scores, and deployment model score show related but distinct spatial patterns (Fig. 2). The binary label is positive in 167 of 262 cells (63.7%). Fig. 3 shows how the evidence decomposes into its source components: the DEP stormwater polygons and the 311 crowd reports occupy overlapping but not identical cell sets, and the binary label is the union over the source-specific layers. The Ida high-water marks contribute no cells within the Lower Manhattan extent—the USGS Ida points lie outside this narrow bounding box—so the Lower Manhattan label is driven by the DEP and 311 sources alone (the expanded pilot includes high-water-mark points across six cells). The out-of-fold scores are on average moderate (mean 0.663) and less dispersed, consistent with the pooled discrimination reported in Section 4.2 (ROC-AUC 0.849 and average precision 0.850 at 63.7% positive prevalence). The deployment score has a mean of about 0.68 and shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.63), as expected when the same cells, features, and labels are refitted without the five-fold holdout structure. The deployment surface is an in-sample fit and is not a validation result; predictive performance is assessed from the out-of-fold metrics in Section 4.2.

### 4.2 Spatial H3-block cross-validation

The smaller pilot contains 262 R9 cells distributed over 12 R7 blocks. Five-fold spatial cross-validation yields accuracy 0.828 ± 0.053 and fold-mean F1 0.868 ± 0.043 (Fig. 4). Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). The held-out labels are evidence-positive in 63.7% of cells, and the model exceeds the always-positive baseline on both accuracy (0.828 vs 0.637) and F1 (0.868 vs 0.769); the always-negative baseline accuracy is 0.363. Pooled out-of-fold ROC-AUC is 0.849 (95% spatial-block bootstrap CI 0.728–0.951) and pooled average precision is 0.850 (CI 0.778–0.965), above the 0.637 prevalence reference. At the prespecified 0.5 threshold, pooled OOF balanced accuracy is 0.793, precision 0.828, recall 0.922, specificity 0.663, and MCC 0.620. The evidence-coverage regressor R² (0.258 ± 0.225) is demoted to a Supplement completeness metric; it quantifies fit to the DEP-only coverage proxy rather than to any physical severity variable, and the regressor is no longer a paper headline. Table 3 separates pooled OOF ranking/threshold metrics from spatial-fold variability.

**Table 3. Spatial H3-block cross-validation summary for the two pilots.** Panel A: pooled out-of-fold ranking and threshold metrics (operating threshold 0.5). Panel B: fold-mean ± population SD across five held-out folds. For the smaller pilot the evidence-positive class is the majority (63.7%).

**Panel A — Pooled OOF**

| Metric | Lower Manhattan (n = 262) | Expanded (n = 956) |
|---|---|---|
| ROC-AUC | 0.849 | 0.887 |
| Average precision (AP) | 0.850 | 0.827 |
| Accuracy | 0.828 | 0.824 |
| Balanced accuracy | 0.793 | 0.826 |
| Precision | 0.828 | 0.789 |
| Recall | 0.922 | 0.865 |
| Specificity | 0.663 | 0.787 |
| MCC | 0.620 | 0.652 |

**Panel B — Spatial-fold variability (mean ± SD)**

| Metric | Lower Manhattan (n = 262) | Expanded (n = 956) |
|---|---|---|
| Accuracy | 0.828 ± 0.053 | 0.824 ± 0.036 |
| F1 | 0.868 ± 0.043 | 0.824 ± 0.039 |
| Always-positive accuracy | 0.637 | 0.479 |
| Always-positive F1 | 0.769 | 0.646 |
| Always-negative accuracy | 0.363 | 0.521 |

Note: SD denotes the population standard deviation across the five held-out folds (ddof = 0). Pooled ROC-AUC/AP 95% CIs are from a spatial-block bootstrap (resampling R7 blocks, 1000 draws), not a cell bootstrap. The evidence-coverage regressor R² is reported only in the Supplement.

### 4.3 Buffer sensitivity

Because adjacent R7 blocks share boundaries, the parent-block split alone can leave near-boundary train–test pairs. Purging training cells within a metre buffer of any held-out cell (projected to EPSG:2263) does not change discrimination at 0/250/500/1000 m in the Lower Manhattan pilot, because the minimum train–test distance between the 12 R7 blocks is already ≈1127 m: retained training fraction is 1.000 at every buffer and pooled ROC-AUC/AP stay at 0.849/0.850 (expanded 0.887/0.827; min distance ≈1127 m). An H3 `grid_disk` purge is more aggressive and does remove cells: purging the one-ring R7 neighbourhood retains 0.876 of training rows (ROC-AUC 0.842, AP 0.837; expanded 0.885/0.829) and a two-ring purge retains 0.733 (ROC-AUC 0.817, AP 0.826; expanded 0.876/0.816). Buffer sensitivity with retained-train fraction is in Table 3b; the spatial-block bootstrap CIs in Section 4.2 already use the block as the resampling unit.

**Table 3b. Buffered spatial-CV sensitivity (Lower Manhattan Option B; five folds).** Buffers are metre guard bands around held-out cells; `grid_disk` rows purge the H3 parent-neighbourhood instead.

| Guard band | Retained train fraction | Pooled ROC-AUC | Pooled AP |
|---|---|---|---|
| 0 m buffer | 1.000 | 0.849 | 0.850 |
| 250 m buffer | 1.000 | 0.849 | 0.850 |
| 500 m buffer | 1.000 | 0.849 | 0.850 |
| 1000 m buffer | 1.000 | 0.849 | 0.850 |
| grid_disk k = 1 | 0.876 | 0.842 | 0.837 |
| grid_disk k = 2 | 0.733 | 0.817 | 0.826 |

### 4.4 Source-ablation of the evidence-union target

Because the target is the union of three heterogeneous sources, its construct validity depends on whether ranking discrimination is driven by one source alone. To test this, the same spatial block cross-validation was refit to DEP-only, 311-only, HWM-only, 311+HWM, and the full evidence union; to the union with mapped-water distance removed; and to 311-only with building density removed. Three nested feature-set models were also fitted on the union target: physics-only, reporting/exposure-only, and full (Table 7).

Discrimination is reproduced across source definitions rather than concentrated in DEP. In Lower Manhattan, DEP-only pooled ROC-AUC is 0.800 while 311-only reaches 0.837 (still well above 0.5) against 0.849 for the union; in the expanded pilot the corresponding values are 0.801, 0.850, and 0.887. Dropping building density from the 311-only feature set leaves LM pooled ROC-AUC at 0.843 and expanded at 0.848—still above 0.5—so 311 skill is not an artefact of building density alone. Removing mapped-water distance leaves union discrimination essentially unchanged (LM 0.849, expanded 0.885). The HWM-only target has no usable discrimination in these pilots (LM single-class; expanded pooled ROC-AUC 0.234, i.e. below chance, on 6 positive cells). Feature-set ablation attributes most discrimination to the physics-only model (LM 0.851, expanded 0.862), with the reporting/exposure-only model lower (LM 0.805, expanded 0.873) and the full model at 0.849/0.887; the union gains only a small margin over the physics-only feature set, which is consistent with the collinearity between terrain/imperviousness and the DEP model output and is reported as a limitation rather than as construct validity.

**Table 7. Source-ablation: spatial block-CV ranking discrimination for each target definition.** Same protocol as the primary evaluation (H3 parent-resolution offset = 2 ⇒ R7 blocks, up to five folds, GBM). LM = Lower Manhattan (n = 262); Exp = expanded pilot (n = 956). These ablations reduce concern that the union target is an artefact of a single source; they do not prove construct validity.

| Target definition | Positive cells (LM / Exp) | Pooled ROC-AUC (LM / Exp) | Fold-mean ROC-AUC (LM / Exp) | F1 (LM / Exp) |
|---|---|---|---|---|
| DEP-only (polygon area) | 74 / 231 | 0.800 / 0.801 | 0.785 / 0.809 | 0.422 / 0.473 |
| 311-only (crowd reports) | 144 / 373 | 0.837 / 0.850 | 0.804 / 0.846 | 0.785 / 0.695 |
| HWM-only (USGS Ida) | 0 / 6 | — / 0.234 | — / 0.486 | — / 0.000 |
| 311 + HWM | 144 / 375 | 0.837 / 0.853 | 0.804 / 0.850 | 0.785 / 0.702 |
| Evidence union (binary) | 167 / 458 | 0.849 / 0.887 | 0.830 / 0.886 | 0.868 / 0.824 |
| Union without dist_mapped_water_m | 167 / 458 | 0.849 / 0.885 | 0.806 / 0.885 | 0.871 / 0.816 |
| 311-only without building_density | 144 / 373 | 0.843 / 0.848 | 0.812 / 0.844 | 0.786 / 0.714 |
| Union, physics-only features | 167 / 458 | 0.851 / 0.862 | 0.858 / 0.860 | 0.871 / 0.786 |
| Union, reporting/exposure-only features | 167 / 458 | 0.805 / 0.873 | 0.764 / 0.873 | 0.875 / 0.809 |
| Union, full features | 167 / 458 | 0.849 / 0.887 | 0.830 / 0.886 | 0.868 / 0.824 |

Note: “—” marks a single-class target that was not fitted. The final three rows are the nested feature-set models (physics / reporting-exposure / full).

### 4.5 FloodNet external validation (a core negative result)

The FloodNet sensor network provides a strict, never-trained external check on whether the open-evidence susceptibility score tracks independently observed street-flooding events. Counting a study R9 cell as a sensor-event cell if it contains at least one sensor with at least one quality-controlled pre-freeze event, out-of-fold scores **fail to discriminate** event from no-event cells: pooled ROC-AUC is 0.451 in Lower Manhattan (23 sensor cells; no-event cells mean score 0.808 vs event cells 0.891) and 0.479 in the expanded pilot (57 cells; 0.748 vs 0.728), i.e. no-event sensor cells score **at least as high** as event cells. Average precision (0.726 / 0.754) is below the sensor-cell prevalence reference (0.739 / 0.702) in the smaller pilot, so it does not indicate positive skill either. The result is not an artefact of very young sensors: filtering to a minimum exposure of 90/180/365 days leaves ROC-AUC below 0.5 or only marginally above it (LM 0.467 / 0.333 / 0.444; expanded 0.521 / 0.514 / 0.617) at the cost of shrinking the already small positive sample (Table 9). The freeze is enforced on the data (events and sensors filtered to `flood_start_time`/`date_installed` < 2026-08-30, max retained event timestamp 2026-08-29, assertion on the max). This negative result is a core finding: independent FloodNet event-level discrimination was **not** established, and it constrains the study claim to blocked-CV discrimination of a heterogeneous open-evidence target rather than external event-level skill. The sparse sensor footprint (26 and 69 sensors in the two extents) also limits power.

**Table 9. FloodNet strict held-out external validation.** Sensor-cell outcome = ≥1 sensor with ≥1 pre-freeze event. `min exposure` filters cells by the minimum installed-sensor exposure before the freeze; all values are reported whether or not they exceed 0.5.

| Pilot | Setting | Sensor cells | ROC-AUC | Average precision |
|---|---|---|---|---|
| LM | all sensors | 23 | 0.451 | 0.726 |
| LM | ≥ 90 d exposure | 20 | 0.467 | 0.740 |
| LM | ≥ 180 d exposure | 19 | 0.333 | 0.740 |
| LM | ≥ 365 d exposure | 9 | 0.444 | 0.705 |
| Expanded | all sensors | 57 | 0.479 | 0.754 |
| Expanded | ≥ 90 d exposure | 48 | 0.521 | 0.807 |
| Expanded | ≥ 180 d exposure | 46 | 0.514 | 0.836 |
| Expanded | ≥ 365 d exposure | 32 | 0.617 | 0.882 |

### 4.6 Scale-loss reconstruction

Fine-resolution hotspots are defined at R10 by a strict 10% area budget with fractional membership at tied boundary scores, after restricting fine cells to the modelling R9 study_domain_mask (n_fine = 1788; n_coarse R9 = 262). Parent reference membership is area-weighted (w_ref), and coarse hotspots use the same area budget on mean/max/p90 scores. Under mean aggregation the R9 rollup yields area-weighted soft Jaccard 0.193 and the R8 rollup yields 0.114. The true reconstruction error — expanding each coarse parent score back onto its fine children and comparing with the fine truth, area-weighted — is reconstruction MAE 0.238 / RMSE 0.345 to R9 and 0.323 / 0.402 to R8 under mean aggregation, with a reconstruction rank correlation of 0.557 (R9) / 0.319 (R8). The earlier parent-mean-versus-itself comparison is an algebraic identity (MAE = RMSE = 0, Spearman = 1) and is retained only as an implementation check. Maximum aggregation reaches soft Jaccard 0.609 (R9) / 0.682 (R8); high max-aggregation Jaccard can be structural under parent collapse and is not treated as a preferred strategy. Table 4 and Fig. 6b are read from the same CSV.

Fig. 5 maps the domain-masked R10 evidence surface and its mean rollups to R9 and R8. Fig. 6a summarises the same scale dependence through ECDFs/histograms (better suited to 0/1-heavy labels than violins), and Fig. 6b displays the area-weighted soft Jaccard values from Table 4 (R10→R9 mean 0.193; R10→R8 mean 0.114).

**Table 4. Scale-loss ladder under a strict 10% area budget with fractional membership ties (study_domain_mask on).** Fine R10 support n = 1788 after restricting to modelling R9 parents (Option B n = 262). Primary metric is the area-weighted soft Jaccard; hard Jaccard is a 1000-draw seeded tie-resolution sensitivity. Reconstruction MAE/RMSE is the area-weighted fine-versus-coarse-reconstruction error (primary scale-loss statistic); `continuous_mae` is the deleted parent-mean identity, retained only as a QA check.

| Coarse resolution | Aggregation | Soft Jaccard | Reconstruction MAE | Reconstruction RMSE | Reconstruction rank corr. | (QA) identity MAE |
|---|---|---|---|---|---|---|
| R9 | Mean | 0.193 | 0.238 | 0.345 | 0.557 | 0.000 |
| R9 | Max | 0.609 | 0.403 | 0.635 | 0.418 | 0.394 |
| R9 | P90 | 0.633 | 0.321 | 0.525 | 0.498 | 0.282 |
| R8 | Mean | 0.114 | 0.323 | 0.402 | 0.319 | 0.000 |
| R8 | Max | 0.682 | 0.669 | 0.818 | 0.179 | 0.596 |
| R8 | P90 | 0.734 | 0.583 | 0.757 | 0.240 | 0.477 |

Note: cell-count budgets are not matched (area budgets are). Exact top-k budgets 5/10/15/20% remain in the archived hotspot-budget companion table. The full ladder is plotted in Supplementary Fig. S1.

### 4.7 Adaptive representation experiment (Supplement)

The fixed coarse grid has 262 cells. Adaptive refinement selects 148 of 262 R9 cells and produces 7,366 mixed cells, compared with 12,838 cells for uniform R11 refinement (Supplementary Fig. S2). The adaptive grid therefore uses 57.4% as many cells as the uniform fine grid. True R11 feature re-extraction on refined children (deployment model; 7,191 of 7,252 children scorable after dropping 61 DEM-edge NaN cells, missing fraction 0.008) yields a **hotspot refinement recall of 0.882**: of the 1,258 uniform-R11 hotspots (top 10% by score), 88.2% had their own R11 cell actually refined (vs the legacy coverage recall of 1.000, which is a tautology). Refinement precision is 0.154 and enrichment (fraction of hotspots inside refined cells divided by the uniform-domain hotspot fraction) is 8.8. The cost–recall curve over score quantiles {0.70–0.95} and neighbour expansion {0, 1} (Fig. S2b) shows the trade-off: at quantile 0.80 with no neighbour expansion, refining 53 parents (22.3% of the uniform cell count) recalls 60.0% of hotspots; at quantile 0.70 with one-ring expansion, refining 181 parents (71.2% of uniform) recalls 94.9%. Best/worst-case recall bounds (treating DEM-edge-missing hotspots as hits/misses) coincide at 0.882 because the recalled hotspots are all scorable. Table 5 lists the counts.

**Table 5. Adaptive representation experiment versus fixed and uniform fine grids** (Lower Manhattan Option B; adaptive = 57.4% of uniform R11; 148 of 262 R9 cells refined; hotspot refinement recall 0.882, legacy coverage recall 1.000).

| Representation | Cell count |
|---|---|
| Fixed R9 | 262 |
| Adaptive R9/R11 | 7,366 |
| Uniform R11 | 12,838 |

### 4.8 Block-size sensitivity and spatial autocorrelation

The R7 block size (parent-resolution offset = 2) was fixed a priori, so its adequacy was tested by repeating the spatial cross-validation with R8 (offset = 1) and R6 (offset = 3) parent blocks, by leave-one-R7-block-out (LOBO) for both pilots, and by computing Moran’s I of the binary evidence target and of OOF residuals under native R9 grid-disk adjacency (Table 8). The evidence target is positively spatially autocorrelated (Moran’s I 0.399 in Lower Manhattan, 0.501 in the expanded pilot), confirming that spatially blocked rather than i.i.d. splitting is required. OOF residual Moran’s I is much weaker (0.064 LM; 0.099 Exp), so blocking reduces but does **not fully eliminate** residual spatial structure. Ranking discrimination is moderately stable across block sizes, yet fixed-threshold accuracy/F1 show more spatial heterogeneity—especially in the smaller pilot. LOBO on Lower Manhattan (12 folds) yields pooled ROC-AUC 0.858 (fold-mean 0.840 ± 0.144), consistent with the primary five-fold result but with wider fold dispersion when each block is held out alone; expanded LOBO (28 folds) gives pooled ROC-AUC 0.892.

**Table 8. Block-size sensitivity of the spatial cross-validation.** The same GBM protocol is repeated at parent-resolution offsets 1 (R8), 2 (R7, primary), and 3 (R6), using **up to five folds** (when fewer blocks exist, n_folds = n_blocks). Moran’s I is computed on the binary evidence target and on OOF residuals (y_true − y_proba). LM = Lower Manhattan Option B (n = 262); Exp = expanded pilot (n = 956).

| Pilot | Offset (block resolution) | Blocks | Pooled ROC-AUC | Fold-mean ROC-AUC | Accuracy | F1 |
|---|---|---|---|---|---|---|
| LM | 1 (R8) | 48 | 0.818 | 0.825 | 0.817 | 0.857 |
| LM | 2 (R7) | 12 | 0.849 | 0.830 | 0.828 | 0.868 |
| LM | 3 (R6) | 4 | 0.794 | 0.839 | 0.867 | 0.638 |
| LM LOBO (R7) | 2 | 12 | 0.858 | 0.840 ± 0.144 | 0.883 | 0.656 |
| Exp | 1 (R8) | 157 | 0.892 | 0.894 | 0.807 | 0.811 |
| Exp | 2 (R7) | 28 | 0.887 | 0.886 | 0.824 | 0.824 |
| Exp | 3 (R6) | 7 | 0.879 | 0.853 | 0.799 | 0.772 |
| Exp LOBO (R7) | 2 | 28 | 0.892 | 0.804 ± 0.129 | 0.854 | 0.661 |

Moran’s I (binary evidence target): 0.399 (LM), 0.501 (Exp). Moran’s I (OOF residual): 0.064 (LM), 0.099 (Exp). Ranking is more stable than fixed-threshold metrics; residual spatial autocorrelation is reduced but not eliminated.

## 5. Discussion

### 5.1 What the experiments establish

Taken together, the two pilots show two distinct roles of the H3 hierarchy. Spatial blocking changes the interpretation of predictive performance on evidence-positive / evidence-unrecorded labels: the Lower Manhattan model exceeds the always-positive baseline on both accuracy and F1 (0.828 vs 0.637; 0.868 vs 0.769), and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy (0.824 vs 0.479) and F1 (0.824 vs 0.646). Coarsening under a unified study_domain_mask exposes substantial hotspot-set disagreement (mean soft Jaccard 0.193 to R9, 0.114 to R8 under a strict 10% area budget; mean reconstruction MAE 0.238/RMSE 0.345 to R9), while the adaptive representation experiment concentrates cells into 57% of a uniform fine grid without any claimed efficiency gain. Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.849 and 0.887). Source ablation shows that this ranking ability is not DEP-dominated: 311-only still exceeds 0.5 AUC, and 311-only without building density remains discriminative. Block-size and LOBO results show ranking is more stable than fixed-threshold metrics, and residual Moran’s I remains non-zero—so spatial leakage is mitigated, not eliminated. Critically, the strict never-trained FloodNet external check does **not** establish event-level skill (ROC-AUC 0.451 LM / 0.479 expanded, with no-event cells scoring at least as high), so the study claim is limited to blocked-CV discrimination of a heterogeneous open-evidence target rather than external event-level skill. The results therefore support measurable ranking discrimination within the evaluated extents, but no citywide classification skill is claimed.

### 5.2 Relation to prior work

Svellingen et al. [5] use H3 to aggregate a proprietary building-level index for scalable communication, whereas the present framework learns from heterogeneous open evidence and evaluates predictions across held-out H3 spatial blocks. The R8 mean-aggregation soft Jaccard value of 0.114 (10% area budget; domain-masked) is numerically comparable in magnitude to their reported value of 0.14, but the two measures use different labels, resolutions, and aggregation procedures. The present ladder therefore characterises scale loss in the open-evidence analysis rather than reproducing their metric.

### 5.3 Methodological implications

Methodologically, the same H3 hierarchy links the spatial unit used for evidence assembly to the units used for cross-validation, scale analysis, and subsequent refinement, extending H3 from a post-prediction visualisation layer to the learning and evaluation architecture. The framework is reproducible in the sense that every reported number traces to public code and public data; reproducibility of the pipeline is not the same as validity of the label semantics, and the two are kept distinct in the accompanying audit document. The source-ablation also bears on a specific validity concern: the DEP stormwater layer is a hydrologic–hydraulic model output whose drivers (terrain, imperviousness) overlap with the predictors, so part of the composite’s discrimination could in principle be model-output emulation rather than evidence fusion. That the 311-only target—an observational, crowd-reported source—still reaches pooled ROC-AUC 0.850 in the expanded pilot indicates the framework is not merely re-deriving the DEP map, even though the union gains only a small margin over the better single source.

### 5.4 Limitations

Several limitations constrain interpretation. The evidence is restricted to two sub-city Manhattan extents: Lower Manhattan Option B (n = 262) and the expanded pilot (n = 956). The open evidence, particularly the 311 complaints, reflects reporting and mapping processes rather than complete ground-truth inundation [7,8], and the DEP stormwater layer is itself a hydrologic–hydraulic model output rather than an observation; only the high-water marks are direct observations. The H3 support follows rectangular bounding boxes rather than a strict Manhattan land footprint, so shoreline and water cells can shift prevalence and predictor distributions. A land-mask sensitivity using NHDPlus water polygons (NHDArea/NHDWaterbody) from the local hydrography extract was computed: requiring land_frac ≥ 0.5 removes only one cell (n = 261; pooled ROC-AUC 0.847), and requiring the cell centroid on land removes two cells (n = 260; ROC-AUC 0.832). The NHD extract in this pilot is shoreline-dominated and does not constitute a full cadastral land polygon; a stronger administrative land mask was not assembled. The shoreline/tidal-water distance predictor remains a tidal-water proxy rather than an inland drainage-density measure. The urban land-cover flag was removed from production features as a deterministic copy of impervious fraction. The terrain and D8 flow-accumulation predictors are heuristic proxies computed on a georeferenced raster without hydrological conditioning, and the DEM interpolation and resolution are those of the underlying export service. Critically, the strict never-trained FloodNet external check does not establish event-level skill (ROC-AUC 0.451 LM / 0.479 expanded), which bounds the claim to blocked-CV discrimination of the open-evidence target rather than external event-level skill.

Evaluation is further constrained by class composition and the number of spatial blocks. The smaller Option B pilot is 63.7% evidence-positive and distributes 12 H3 blocks across five folds; the expanded pilot uses 28 blocks. Block-size sensitivity and LOBO (Section 4.8) show ranking discrimination is moderately stable across R8/R7/R6 blocking, while fixed-threshold accuracy/F1 are more heterogeneous; residual Moran’s I (0.064–0.099) shows spatial leakage is reduced but not eliminated. Nested hyperparameter search was not run; GBM settings remain pre-specified. The evidence-coverage regressor R² is demoted to the Supplement. Adaptive refinement is primarily a cell-count representation experiment. The classifier output is not calibrated.

Rainfall conditioning remains unevaluated under observed forcing (S_h(c) only). DEP area-fraction thresholds (0/1%/5%/10%) are reported as sensitivities in the registry. The FloodNet held-out diagnostic covers only the sparse sensor footprint and does not support citywide event skill claims; it is reported as a core negative result, not a footnote.

### 5.5 Outstanding steps

Future work should first replace the constant rainfall placeholder with documented event observations and test S_h(c,r) for fixed static features. The same spatial cross-validation protocol can then be applied over broader extents, with denser FloodNet coverage and calibrated probabilities. Spatial buffering around held-out blocks remains a priority because residual Moran’s I shows leakage is not fully eliminated. Where a high-quality administrative land polygon is available, replacing the NHD water-based proxy with a true land footprint would tighten the spatial support.

## 6. Conclusions

Using H3 as a common spatial support links open-evidence learning to spatially blocked validation, scale diagnostics, and selective refinement rather than treating the grid only as a post-processing layer. Across the two Manhattan pilots, the blocked evaluation and prevalence-aware baselines change how classification performance is read, and selective refinement links resolution control to the fitted cell scores without requiring uniform fine-grid representation. The strict, never-trained FloodNet external check did **not** establish independent event-level skill (ROC-AUC 0.451 in Lower Manhattan; 0.479 expanded, with no-event sensor cells scoring at least as high as event cells), so the contribution is a blocked-CV protocol for discriminating a heterogeneous open-evidence target—not a validated citywide flood-event predictor. The evidence remains limited to the evaluated pilot extents; observed event rainfall, rainfall-responsive predictions, citywide evaluation, and denser FloodNet event validation remain priorities for further assessment.

---

## CRediT authorship contribution statement

**[待补充 — to be completed before submission: list each author with their CRediT roles.]**

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Figure captions

**Figure 1. Open-evidence H3 pluvial-flood susceptibility workflow.** Three evidence boxes—DEP stormwater polygons (categories 1–2), NYC 311 street-flooding complaints, and USGS Ida high-water marks—are assembled with static predictors into H3 R9 cells as evidence-positive / evidence-unrecorded labels. Learning yields the susceptibility score S_h(c)=f_θ(X_c) under H3-block spatial CV; diagnostics include source ablation, domain-masked scale-loss Jaccard, and a Sandy coastal OOF diagnostic. Rainfall conditioning is deferred. The dashed FEMA Sandy side-channel is never a training label.

**Figure 2. Spatial results for the Lower Manhattan pilot (n = 262 R9 cells; Option B).** (a) Open-evidence flood-evidence score; (b) pooled out-of-fold gradient-boosting score under H3-block spatial cross-validation; (c) **deployment_full** susceptibility score S_h(c), fitted using all 262 cells after evaluation. Panel (c) is an in-sample deployment fit, not a validation result.

**Figure 3. Source-specific open-evidence maps for the Lower Manhattan pilot (n = 262 R9 cells).** The composite flood-evidence score (d) is the maximum over: (a) DEP stormwater polygon area fraction (categories 1–2), (b) 311 crowd-report count, and (c) USGS Ida high-water-mark count. No Ida high-water marks fall within this extent.

**Figure 4. Spatial H3-block cross-validation performance for the Lower Manhattan pilot.** Classification accuracy and F1 per fold, plus ΔAccuracy/ΔF1 versus the fold-wise always-positive baseline; constant-class reference lines are shown. Per-fold test size and evidence-positive prevalence are annotated.

**Figure 5. Multi-resolution open-evidence score surface under study_domain_mask (Option B).** (a) R10 open-evidence flood score (n = 1788); (b) mean rollup to R9 (n = 262, matching modelling support); and (c) mean rollup to R8 (n = 48).

**Figure 6. Resolution effects on the open-evidence score surface (Option B).** (a) ECDF with light histograms of the score at R10 (n = 1788), R9 (n = 262), and R8 (n = 48); (b) area-weighted soft Jaccard from the canonical scale-results table (Table 4). For mean aggregation, R10→R9 = 0.193 and R10→R8 = 0.114.

**Supplementary Figure S1. Open-evidence hotspot scale-loss diagnostics across H3 resolutions.** Reads the same CSV as Table 4 (domain-masked).

**Supplementary Figure S2. Adaptive representation experiment versus uniform fine grids by cell count.** Fixed R9 (262), adaptive mixed R9/R11 (7,366), and uniform R11 (12,838) for Lower Manhattan Option B (cell-count only; Option A R11 re-extract reported separately).

---

## Data and code availability

The public repository (code, configs, tests, paper documentation, and small summary tables; large rasters, GeoJSON files, trained model binaries, and large parquet files are excluded) is available at https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3. Provenance of the reported numeric registry and diagnostics is archived with the paper materials; each raw layer is mapped in the repository download manifest to its source URL, retrieval date, and license. Analyses that produced the frozen paper artifacts used scikit-learn 1.8.0 and H3 4.4.2 as recorded in the run metadata; the repository pins these versions for reproducibility. Synthetic demonstrations are excluded from scientific evidence. A process-oriented research report and a data-authenticity audit accompany the manuscript.

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During preparation of this work, generative AI tools assisted with language editing, code review, test design, figure consistency checks, and drafting of the technical audit. The authors executed the scientific code, verified numerical outputs against regenerated artifacts, and take full responsibility for the content. Author names, affiliations, ORCID, and CRediT statements remain placeholders pending confirmation.

## References

[1] B.R. Rosenzweig, et al., The value of urban flood modeling, Earth's Future 9 (2021) e2020EF001873. https://doi.org/10.1029/2020EF001873

[2] Uber Technologies, Inc., H3: A hexagonal hierarchical geospatial indexing system, 2026. https://h3geo.org

[3] J. Burdziej, Using hexagonal grids and network analysis for spatial accessibility assessment in urban environments, Miscellanea Geographica 23 (2019) 99–110. https://doi.org/10.2478/mgrsd-2018-0037

[4] M. Li, H. McGrath, E. Stefanakis, Multi-scale flood mapping under climate change scenarios in hexagonal discrete global grids, ISPRS Int. J. Geo-Inf. 11 (2022) 627. https://doi.org/10.3390/ijgi11120627

[5] W. Svellingen, G. Torgersen, O. Bruland, T. Muthanna, Scalable pluvial flood risk assessment: a data-driven framework integrating machine learning (ML) and discrete global grid systems (DGGS H3), Int. J. Disaster Risk Reduction 137 (2026) 106091. https://doi.org/10.1016/j.ijdrr.2026.106091

[6] W. Svellingen, G. Torgersen, O. Bruland, T. Muthanna, Indexing areas vulnerable to pluvial floods—using machine learning and H3 hexagonal grid system, SSRN preprint (2025). https://doi.org/10.2139/ssrn.5875380

[7] C. Agonafir, A.R. Pabon, T. Lakhankar, R. Khanbilvardi, N. Devineni, Understanding New York City street flooding through 311 complaints, J. Hydrol. 605 (2022) 127300. https://doi.org/10.1016/j.jhydrol.2021.127300

[8] C. Agonafir, T. Lakhankar, R. Khanbilvardi, N.Y. Krakauer, D. Radell, N. Devineni, A machine learning approach to evaluate the spatial variability of New York City's 311 street flooding complaints, Comput. Environ. Urban Syst. 97 (2022) 101854. https://doi.org/10.1016/j.compenvurbsys.2022.101854

[9] J.T. Bersabe, B.-W. Jun, The machine learning-based mapping of urban pluvial flood susceptibility in Seoul integrating flood conditioning factors and drainage-related data, ISPRS Int. J. Geo-Inf. 14 (2025) 57. https://doi.org/10.3390/ijgi14020057

[10] K. Sun, Y. Hu, G. Lakhanpal, R.Z. Zhou, Spatial cross-validation for GeoAI, in: S. Gao, Y. Hu, W. Li (Eds.), Handbook of Geospatial Artificial Intelligence, Taylor & Francis, 2023.

[11] U.S. Geological Survey, 3D Elevation Program (3DEP) elevation services, accessed August 2026. https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer

[12] Esri, USA NLCD annual fractional impervious surface (ImageServer export), accessed August 2026. https://di-nlcd.img.arcgis.com/arcgis/rest/services/USA_NLCD_Annual_LandCover_Fractional_Impervious_Surface/ImageServer

[13] U.S. Geological Survey, NHDPlus High Resolution MapServer, accessed August 2026. https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer

[14] New York City Department of Environmental Protection, Stormwater flood map (ArcGIS Hub; Flooding_Category 1–2), accessed August 2026. https://data.cityofnewyork.us

[15] NYC Open Data, 311 Service Requests from 2010 to 2019 (dataset 76ig-c548); Street Flooding (SJ) subset for 2010–2014, accessed September 2026. https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-2019/76ig-c548

[16] U.S. Geological Survey, Hurricane Ida high-water marks, data release, accessed August 2026. https://doi.org/10.5066/P9OMBJPQ

[17] Federal Emergency Management Agency / New York City Open Data, Hurricane Sandy storm surge inundation (uyj8-7rv5), accessed August 2026. https://data.cityofnewyork.us/api/geospatial/uyj8-7rv5

[18] T. Saito, M. Rehmsmeier, The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets, PLOS ONE 10 (2015) e0118432. https://doi.org/10.1371/journal.pone.0118432

[19] NYC Open Data, FloodNet: Street Flooding Events Measured by FloodNet Sensors (aq7i-eu5q), published 2026-03-03, accessed September 2026. https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q

[20] NYC Open Data, FloodNet: Sensor Deployment Metadata (kb2e-tjy3), accessed September 2026. https://data.cityofnewyork.us/Environment/FloodNet-Sensor-Deployment-Metadata/kb2e-tjy3
