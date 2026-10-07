# Spatially blocked pluvial-flood susceptibility learning on the H3 grid using heterogeneous open public data

## Highlights

- An H3-native protocol joins open-evidence assembly, spatially blocked validation, and resolution diagnostics on one hierarchical grid
- Binary labels are kept as **evidence-positive / evidence-unrecorded** (model-derived DEP, crowd-reported 311, observed Ida high-water marks), not verified flood / non-flood ground truth
- Prevalence-aware baselines change how classification skill is read: Lower Manhattan Option B (n = 262) exceeds always-positive on accuracy (0.824 vs 0.637) and F1 (0.861 vs 0.769)
- Domain-masked native R10 overlay with a strict 10% area budget shows substantial scale loss (mean hotspot soft Jaccard 0.136 to R8; R10→R9 support unified at n = 262)
- The fitted quantity is the cell susceptibility score S_h(c)=f_θ(X_c); rainfall-conditioned S_h(c,r) is deferred until observed event rainfall is available

---

## Abstract

Urban pluvial flooding develops when intense rainfall overwhelms drainage before water reaches a watercourse. City-scale screening needs a spatial support that can be updated as new evidence arrives and that can be evaluated without inflating skill through spatial leakage. Many published indices draw on proprietary damage or insurance labels, and random train–test splits can overstate performance when nearby cells appear in both partitions. This study evaluates an H3-native protocol in which the hexagonal discrete global grid is the common support for evidence assembly, spatially blocked validation, and resolution control, using only heterogeneous open public data.

Flood evidence is assembled on H3 cells from three sources kept distinct in the training table: model-derived New York City DEP stormwater polygons (categories 1–2), crowd-reported NYC 311 street-flooding complaints, and observed USGS Hurricane Ida high-water marks. Binary labels are framed as evidence-positive versus evidence-unrecorded. Gradient-boosting classifiers and an evidence-score regressor are fitted under H3-block spatial cross-validation that withholds entire parent cells. After evaluation, separate deployment models are refitted on all cells for descriptive maps and adaptive screening only.

In the Lower Manhattan pilot (Option B; n = 262 R9 cells; 63.7% evidence-positive), spatial cross-validation accuracy is 0.824 ± 0.055 and F1 is 0.861, above the always-positive baseline (0.637 and 0.769), with pooled out-of-fold ROC-AUC 0.850 and average precision 0.851. In the expanded pilot (n = 956; 48.2% evidence-positive), accuracy is 0.819 ± 0.024 and F1 is 0.822, both above the fold-mean constant-class baselines, with pooled ROC-AUC 0.880 and average precision 0.815. A domain-masked native R10 label overlay with tie-aware fractional hotspot membership under a strict 10% area budget shows hotspot membership degrading under coarsening (mean soft Jaccard 0.136 to R8; 0.220 to R9). Adaptive refinement uses about 57% as many cells as a uniform fine grid. The primary screening quantity is S_h(c)=f_θ(X_c); because training rainfall is constant, rainfall-conditioned S_h(c,r) is not claimed. Production assembly is fail-closed: missing layers or NaNs abort rather than silently filling synthetic features. Citywide skill and rainfall-conditioned discrimination remain open.

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

The cell-level flood-evidence score combines the available open sources. Polygon sources contribute an intersection area fraction (0–1); point sources contribute a per-cell presence indicator. The score is the maximum of the area fraction and the point-presence indicator, clipped to [0,1]. The binary label is then defined as flood_class = 1[flood_evidence_score ≥ 1e−9], so any cell with positive evidence is **evidence-positive** and all other cells are **evidence-unrecorded**—not verified flood versus verified non-flood.

Three properties of this target matter for interpretation. First, the three sources are not interchangeable measurements of one latent variable: the DEP polygons are hydrologic–hydraulic model outputs of moderate stormwater flooding at current sea levels (category 1, nuisance flooding with ponding depth ≥4 in to <1 ft; category 2, deep-and-contiguous flooding ≥1 ft; the coastal “future high tides” class is excluded); the 311 complaints are crowd-reported and unverified; only the high-water marks are direct observations of an actual event (Ida, 2021). Second, the sources span different times and forcings and are therefore collapsed into a static “has there ever been any evidence here” score rather than a per-event inundation label. Third, the score is not a severity measure: a cell with one complaint receives the same score as a cell with a verified high-water mark, because any point presence saturates the score at 1. The score is consequently treated as a flood-evidence screening target, not as flood risk, flood depth, or a calibrated probability.

Each source is retained separately in the assembled table for auditability: DEP contributes an area-fraction column (further split into nuisance and deep categories), 311 contributes count and presence fields, and high-water marks contribute count, presence, and quality fields, with an evidence-source string recording which sources are present per cell. The composite score is built from these source-specific columns rather than from an undifferentiated merge. NYC 311 records in particular reflect reporting and mapping processes, and their biases have been documented previously [7,8].

NYC Open Data FloodNet street-flooding events (dataset aq7i-eu5q; published 2026-03-03) and sensor deployment metadata (kb2e-tjy3) are retained for a strict held-out diagnostic and are never joined into the composite training or evaluation target. Among study cells that contain at least one FloodNet sensor, out-of-fold scores show weak discrimination of cells with one or more quality-controlled sensor flood events (Lower Manhattan ROC-AUC 0.314 on 23 sensor cells; expanded 0.463 on 57 sensor cells), so sensor-event agreement is not claimed as external skill.

The DEP service provides the moderate-flood polygon layer under both current sea levels and a projected 2050 sea-level-rise scenario. The current-sea-level layer is the primary evidence; the 2050 variant is retained as a sensitivity. Under the sea-level sensitivity protocol, re-running the target with the 2050 layer shifts Option B (n = 262) positive prevalence from 63.7% to 67.6% and pooled ROC-AUC from 0.848 to 0.836; in the expanded pilot the shifts are 47.9% to 50.0% and 0.882 to 0.872. These changes do not alter any substantive conclusion.

Rainfall enters the framework only as a deferred conditioning variable. The present pilots define the primary susceptibility score as S_h(c)=f_θ(X_c) from static predictors alone. A constant synthetic rainfall input (Ida-like 75 mm/h) is retained for scenario bookkeeping in the Supplement but produces a flat within-cell response and is not a main claim. Event-conditioned S_h(c,r) is left for future work.

## 3. Methods

The method uses the H3 hierarchy as a common spatial reference while assigning distinct roles to the resolutions used for model fitting, spatial blocking, scale diagnostics, and adaptive refinement (Fig. 1). Production feature assembly is fail-closed: if a required static layer is missing or yields NaN after zonal aggregation, the run aborts rather than substituting synthetic hash features.

### 3.1 Evidence assembly on H3

For a chosen bounding box and modelling resolution R9, every intersecting H3 cell is listed and retained as a row. Raster predictors are summarised as zonal means over each cell; vector predictors and evidence layers are summarised by intersection area fraction (polygons) or presence/count (points). All H3 indexing and spatial joins use longitude–latitude coordinates (EPSG:4326). Cell areas use H3 native cell-area calculations; distance-to-water uses a great-circle (haversine) distance from the cell centre to the nearest NHDPlus hydrographic feature; terrain derivatives are computed on the raster grid and averaged zonally over each cell. Polygon intersections use EPSG:2263. The continuous flood-evidence score and the binary flood_class label are then formed as in Section 2, with source-specific columns retained alongside the composite. Fail-closed assembly means that incomplete downloads or NaN zonal statistics abort the run; fixture or synthetic feature fill is disabled for production paper artefacts.

### 3.2 H3 representation roles

Supervised modelling uses H3 resolution 9 (R9) as the training and evaluation support (edge length on the order of a city block in mid-latitudes). Resolution 10 (R10) provides the fine-evidence support for the scale-loss diagnostic, with hotspots subsequently rolled to R9 and R8; model fitting remains at R9 throughout. Adaptive refinement is a post-training step that replaces selected R9 cells with their resolution-11 (R11) descendants. The workflow is summarised in Fig. 1.

### 3.3 Features

Static predictors are elevation, slope, a flow-accumulation proxy (D8-derived from the digital elevation model), impervious fraction (NLCD), building density, and shoreline/tidal-water distance. Elevation, slope, and the flow-accumulation proxy are zonal means over each cell; impervious fraction is a zonal mean of the NLCD fractional-impervious surface; building density is the building-centroid count divided by cell area; shoreline/tidal-water distance is the great-circle distance from the cell centre to the nearest NHDPlus hydrographic feature. The previously considered urban land-cover flag (impervious fraction > 0.45) is excluded from the estimator feature set because it is a deterministic copy of impervious fraction and carries no independent information. Rainfall is handled separately as the condition r rather than as a static feature.

### 3.4 Models and baselines

The primary learner is a gradient-boosting classifier and an evidence-score gradient-boosting regressor, each with 80 estimators, maximum depth 4, and learning rate 0.08, fitted on features standardised within each training fold, with a fixed random seed (42); all other estimator parameters retain the scikit-learn 1.8 defaults. These hyperparameters were **pre-specified without nested cross-validation retuning**, to avoid an additional tuning loop on the small pilot samples and to keep evaluation comparable across ablations. Classification uses a **prespecified operating threshold of 0.5** for comparability across folds and pilots; a train-fold max-F1 threshold sensitivity is reported in the registry only.

Two constant classifiers—always-positive and always-negative—are computed on each held-out fold, and accuracy and F1 are reported alongside these constant classifiers to provide a class-prevalence reference. The majority-class identity is determined from pooled target counts, and the constant-baseline accuracy and F1 use the same fold-wise aggregation as the model metrics. Two further baselines are included for diagnostic comparison: an L2-regularised logistic classifier and a ponding rule defined by the weighted combination

`0.40·(1 − elev_norm) + 0.35·imperv + 0.15·(1 − min(slope, 15°)/15°) + 0.10·TWI_norm`,

where elev_norm and TWI_norm are min–max normalised elevation and a topographic-wetness proxy, and a cell is classified positive when the score is at least 0.5. In spatial cross-validation the min–max bounds for the ponding rule are computed from the training fold only and applied to the held-out fold, so the baseline does not use test-set distribution information. In-sample metrics are treated as optimistic references only. Table 2 summarises the models and baselines.

**Table 2. Model and baseline specifications.**

| Model / baseline | Configuration | Role |
|---|---|---|
| Gradient-boosting classifier | 80 estimators, max depth 4, learning rate 0.08, features standardised within each training fold, random seed 42 | Primary binary learner |
| Gradient-boosting regressor | Same configuration | Evidence-score regressor |
| L2-regularised logistic classifier | scikit-learn 1.8 defaults | Diagnostic baseline |
| Ponding rule | Weighted combination of normalised elevation, impervious fraction, slope, and TWI; positive when score ≥ 0.5; bounds from training fold only | Diagnostic baseline |
| Always-positive / always-negative | Constant class prediction | Prevalence-aware baselines on each held-out fold |

### 3.5 Spatial H3-block cross-validation and deployment models

Each R9 cell is assigned to its R7 parent (two H3 resolution levels coarser). Up to five-fold GroupKFold partitions these R7 groups so that no R7 block appears in both the training and the held-out portion of a fold; when fewer than five blocks are available, the number of folds equals the number of blocks. This changes the generalisation target from “new randomly drawn cells” to “new spatial blocks”, which is closer to the transfer a screening product would face. For each held-out cell the predicted class probability is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]—are computed from pooled out-of-fold (OOF) predictions. H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons only.

After evaluation is complete, separate deployment classifiers and regressors are refitted on all cells (fit_rows equals the pilot cell count: 262 or 956). These all-cell models are used only for descriptive maps (Fig. 2c) and adaptive-grid screening and are never used to calculate held-out performance metrics. Model manifests record the model role (evaluation versus deployment), the number and hash of training cells, configuration, software versions, and random seed.

The R7 block size is fixed a priori; block-size sensitivity, leave-one-R7-block-out (LOBO), and Moran’s I of the evidence score and of OOF residuals are reported in Section 4.9 and Table 8.

### 3.6 Domain-masked scale-loss diagnostics

Fine-resolution hotspot membership is defined on native R10 evidence scores using a fixed 10% area budget with fractional allocation within boundary ties (no lexicographic H3-index tie-break and no cell-count top-k). Fine cells are restricted by a study_domain_mask so that R10 parents at modelling resolution R9 equal the modelling R9 set (Option B: n_coarse = 262), removing the bbox-induced parent surplus that previously inflated the coarse support (296 versus 262). For each coarse parent p the reference membership is the area-weighted fraction w_ref(p)=Σ_i∈p a_i w_i / Σ_i∈p a_i. Coarse hotspots are selected under the same area budget on area-weighted mean, maximum, or p90 parent scores, allowing fractional membership of the final tied group so that selected coarse area equals the fine budget within floating-point tolerance.

The primary overlap metric is the area-weighted soft Jaccard; hard-set Jaccard is reported only as a seeded tie-resolution sensitivity (1000 draws; median and 95% interval). Continuous distortion is reported as mean absolute error between fine-parent mean scores and the coarse aggregation. Maximum aggregation can approach high Jaccard for structural reasons (parent collapse under max) and is not interpreted as a preferred strategy. Table 4 and Fig. 6b are read from the same archived diagnostics table; figures never recompute Jaccard independently. The fine R10 reference is assembled by overlaying the raw polygon and point geometries directly onto R10 cells, not by inheriting scores from R9 parents. These diagnostics use different labels, resolutions, and hotspot definitions from the Jaccard value reported by Svellingen et al. [5] and are not a reproduction of that result.

### 3.7 Source ablation and coastal diagnostic

Because the composite target is the maximum of three heterogeneous sources, construct validity depends on whether ranking discrimination is driven by one source alone—in particular, whether the model merely re-derives the DEP hydrologic–hydraulic map from terrain and imperviousness predictors that share its drivers. The same spatial block cross-validation is therefore refit to DEP-only, 311-only, HWM-only, 311+HWM, and the composite; to the composite with shoreline distance removed; and to 311-only with building density removed (Section 4.8; Table 7).

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a coastal-confounding diagnostic. Because the flood-evidence score combines polygon overlap and point presence, the pluvial grouping in the diagnostic is derived from the same composite flood_class definition used elsewhere, so that a cell carrying only a point label is counted as pluvial rather than misassigned to the “neither” group. The control reports the overlap between pluvial evidence and coastal inundation and the difference in the **out-of-fold model score** between pluvial-only and coastal-only cells. The score compared is the held-out gradient-boosting score, never the target flood-evidence score, because a coastal-only cell has flood_class = 0 by construction and therefore a target score of 0 by definition; comparing target scores would be circular. Sandy labels are never used as training labels. As a sensitivity, 311 complaints created in the Sandy landfall window 2012-10-27 to 2012-11-05 are excluded before rebuilding the composite target, while coastal diagnostics still use OOF scores from the primary (unmodified) CV.

### 3.8 Adaptive representation experiment (Supplement)

After training, the full-fit positive-class model score screens R9 cells for refinement as an **adaptive representation experiment** reported by cell count (Supplementary Fig. S2; Table 5). A cell is selected when its score is at or above the 0.8 quantile of all cell scores, or when its predicted probability is uncertain (uncertainty 1 − 2|p − 0.5| of at least 0.7, i.e. p between 0.35 and 0.65); the selection is then expanded to include the one-ring H3 neighbourhood among the R9 cells. Each selected cell is replaced by its R11 descendants while unselected cells remain at R9. A separate Option A diagnostic re-extracts R11 features on refined children and scores them with the post-urban-drop deployment model; cells with NaN static features at DEM edges are dropped before scoring. The primary claim for adaptive refinement remains cell-count concentration relative to a uniform fine grid; runtime and memory are not claimed as efficiency gains.

### 3.9 Susceptibility score (rainfall deferred)

The primary cell index is

`S_h(c) = f_θ(X_c)`,

the classifier’s positive-class score from static predictors X_c (not a calibrated probability; not PFIb). Rainfall-conditioned S_h(c,r) is defined for future event-based analyses but is not claimed here: the pilot’s constant synthetic rainfall has zero training variance, so flat scenario loops are retained only as a limitation and Supplement note.

## 4. Results

### 4.1 Spatial pattern of evidence, predictions, and the full-fit score

On the 262-cell Lower Manhattan R9 support (Option B), the open-evidence scores, out-of-fold scores, and full-fit model score show related but distinct spatial patterns (Fig. 2). The evidence scores are bimodal by construction: cells with no positive evidence score 0, whereas positive evidence yields either a fractional polygon-overlap score or a point-presence score of 1 (median 1.0, mean 0.598). Fig. 3 shows how this composite surface decomposes into its source components: the DEP stormwater polygons and the 311 crowd reports occupy overlapping but not identical cell sets, and the composite score is the maximum over the source-specific layers. The Ida high-water marks contribute no cells within the Lower Manhattan extent—the USGS Ida points lie outside this narrow bounding box—so the Lower Manhattan composite is driven by the DEP and 311 sources alone (the expanded pilot includes high-water-mark points across six cells). The out-of-fold scores are on average moderate (mean 0.663) and less dispersed, consistent with the modest pooled discrimination reported in Section 4.2 (ROC-AUC 0.850 and average precision 0.851 at 63.7% positive prevalence). The full-fit score has a mean of about 0.68 and shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.63), as expected when the same cells, features, and labels are refitted without the five-fold holdout structure. The full-fit surface is an in-sample fit and is not a validation result; predictive performance is assessed from the out-of-fold metrics in Section 4.2.

### 4.2 Spatial H3-block cross-validation

The smaller pilot contains 262 R9 cells distributed over 12 R7 blocks. Five-fold spatial cross-validation yields accuracy 0.824 ± 0.055 and F1 0.861 (Fig. 4). Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). The held-out labels are evidence-positive in 63.7% of cells, and the model exceeds the always-positive baseline on both accuracy (0.824 vs 0.637) and F1 (0.861 vs 0.769); the always-negative baseline accuracy is 0.363. Pooled out-of-fold ROC-AUC is 0.850 and pooled average precision is 0.851, above the 0.637 prevalence reference. At the prespecified 0.5 threshold, pooled OOF balanced accuracy is 0.790, precision 0.827, recall 0.916, specificity 0.663, and MCC 0.611. Evidence-score R² (0.167 ± 0.319) is demoted to a Supplement completeness metric; it quantifies fit to the constructed flood-evidence score rather than to any physical severity variable. Table 3 separates pooled OOF ranking/threshold metrics from spatial-fold variability.

**Table 3. Spatial H3-block cross-validation summary for the two pilots.** Panel A: pooled out-of-fold ranking and threshold metrics (operating threshold 0.5). Panel B: fold-mean ± population SD across five held-out folds. For the smaller pilot the evidence-positive class is the majority (63.7%).

**Panel A — Pooled OOF**

| Metric | Lower Manhattan (n = 262) | Expanded (n = 956) |
|---|---|---|
| ROC-AUC | 0.850 | 0.880 |
| Average precision | 0.851 | 0.815 |
| Accuracy | 0.824 | 0.819 |
| Balanced accuracy | 0.790 | 0.821 |
| Precision | 0.827 | 0.777 |
| Recall | 0.916 | 0.876 |
| Specificity | 0.663 | 0.766 |
| MCC | 0.611 | 0.644 |

**Panel B — Spatial-fold variability (mean ± SD)**

| Metric | Lower Manhattan (n = 262) | Expanded (n = 956) |
|---|---|---|
| Accuracy | 0.824 ± 0.055 | 0.819 ± 0.024 |
| F1 | 0.861 ± 0.049 | 0.822 ± 0.028 |
| Always-positive accuracy | 0.637 | 0.482 |
| Always-positive F1 | 0.769 | 0.649 |
| Always-negative accuracy | 0.363 | 0.518 |

Note: SD denotes the population standard deviation across the five held-out folds (ddof = 0). Evidence-score R² is reported only in the Supplement.

### 4.3 Scale-loss Jaccard ladder

Fine-resolution hotspots are defined at R10 by a strict 10% area budget with fractional membership at tied boundary scores, after restricting fine cells to the modelling R9 study_domain_mask (n_fine = 1788; n_coarse R9 = 262). Parent reference membership is area-weighted (w_ref), and coarse hotspots use the same area budget on mean/max/p90 scores. Under mean aggregation the R9 rollup yields area-weighted soft Jaccard 0.220 and the R8 rollup yields 0.136. Maximum aggregation reaches soft Jaccard 0.648 (R9) / 0.579 (R8); high max-aggregation Jaccard can be structural under parent collapse and is not treated as a preferred strategy. Continuous MAE between fine-parent mean scores and the coarse aggregation is 0 for mean (by construction) and 0.388 / 0.656 for max at R9 / R8. Table 4 and Fig. 6b are read from the same CSV.

Fig. 5 maps the domain-masked R10 open-evidence score surface and its mean rollups to R9 and R8. Fig. 6a summarises the same scale dependence through ECDFs/histograms (better suited to 0/1-heavy scores than violins), and Fig. 6b displays the area-weighted soft Jaccard values from Table 4 (R10→R9 mean 0.220; R10→R8 mean 0.136).

**Table 4. Scale-loss ladder under a strict 10% area budget with fractional membership ties (study_domain_mask on).** Fine R10 support n = 1788 after restricting to modelling R9 parents (Option B n = 262). Primary metric is the area-weighted soft Jaccard; hard Jaccard is a 1000-draw seeded tie-resolution sensitivity. Continuous MAE is fine-parent mean versus coarse aggregation.

| Coarse resolution | Aggregation | Soft Jaccard | Continuous MAE | Fine-parent recall | Coarse precision | Spearman |
|---|---|---|---|---|---|---|
| R9 | Mean | 0.220 | 0.000 | 0.360 | 0.360 | 1.000 |
| R9 | Max | 0.648 | 0.388 | 0.786 | 0.786 | 0.916 |
| R9 | P90 | 0.573 | 0.251 | 0.729 | 0.729 | 0.983 |
| R8 | Mean | 0.136 | 0.000 | 0.240 | 0.240 | 1.000 |
| R8 | Max | 0.579 | 0.656 | 0.733 | 0.733 | 0.707 |
| R8 | P90 | 0.682 | 0.398 | 0.811 | 0.811 | 0.910 |

Note: cell-count budgets are not matched (area budgets are). Exact top-k budgets 5/10/15/20% remain in the archived hotspot-budget companion table. The full ladder is plotted in Supplementary Fig. S1.

### 4.4 Adaptive representation experiment (Supplement)

The fixed coarse grid has 262 cells. Adaptive refinement selects 148 of 262 R9 cells and produces 7,366 mixed cells, compared with 12,838 cells for uniform R11 refinement (Supplementary Fig. S2). The adaptive grid therefore uses 57.4% as many cells as the uniform fine grid. True R11 feature re-extraction on refined children (post-urban-drop deployment model; 7,222 of 7,252 children scorable after dropping DEM-edge NaNs) yields hotspot recall 1.000 versus a uniformly scored scorable R11 grid (1,258 hotspots at quantile 0.9). Table 5 lists the counts.

**Table 5. Adaptive representation experiment versus fixed and uniform fine grids** (Lower Manhattan Option B; adaptive = 57.4% of uniform R11; 148 of 262 R9 cells refined; Option A true R11 re-extract hotspot recall 1.000).

| Representation | Cell count |
|---|---|
| Fixed R9 | 262 |
| Adaptive R9/R11 | 7,366 |
| Uniform R11 | 12,838 |

### 4.5 Rainfall scenarios (limitation / Supplement)

Flat synthetic rainfall scenarios (25–100 mm/h) leave S_h(c) unchanged within each cell. Rainfall-conditioned discrimination is **not claimed**; validated event rainfall remains future work toward S_h(c,r).

### 4.6 Sandy coastal-confounding diagnostic

Across the 262 cells, 74 intersect Sandy coastal inundation and 165 carry pluvial evidence under the coastal-diagnostic grouping; 44 have both, and 30 are coastal-only (11.5%). The control compares the **out-of-fold model score** across these groups rather than the target, because a coastal-only cell has flood_class = 0 and therefore a target score of 0 by definition; comparing target scores would be circular. The out-of-fold score averages 0.406 in coastal-only cells, 0.886 in pluvial-only cells, 0.760 in cells with both, and 0.280 in cells with neither, giving a pluvial−coastal out-of-fold score difference of 0.480. Among the 53 cells above the 0.8 score quantile, 3.8% are coastal-only and 83.0% carry pluvial evidence. As a sensitivity, excluding 311 complaints created in the Sandy landfall window 2012-10-27 to 2012-11-05 removes 9 of 510 complaints, flips 1 cell label (167→166 positives), and leaves pooled ROC-AUC essentially unchanged (0.861 vs 0.850 on the rebuilt composite); the OOF pluvial−coastal score gap remains positive (0.464). Coastal overlap is never a training label. Table 6 details the primary overlap and mean out-of-fold scores.

**Table 6. Sandy coastal-confounding diagnostic statistics on the 262-cell Option B pilot.** The score comparison uses the out-of-fold model score (never the target flood-evidence score, which is 0 in coastal-only cells by construction). The pluvial−coastal difference is the mean out-of-fold score of pluvial-only cells minus that of coastal-only cells.

| Statistic | Value |
|---|---|
| Cells intersecting Sandy inundation | 74 of 262 |
| Cells with pluvial evidence (diagnostic grouping) | 165 of 262 |
| Both pluvial and coastal | 44 |
| Coastal-only | 30 (11.5%) |
| Pluvial-only | 121 (46.2%) |
| Neither | 67 (25.6%) |
| Mean out-of-fold model score, coastal-only cells | 0.406 |
| Mean out-of-fold model score, pluvial-only cells | 0.886 |
| Mean out-of-fold model score, both | 0.760 |
| Mean out-of-fold model score, neither | 0.280 |
| Pluvial − coastal out-of-fold score difference | 0.480 |
| Coastal-only among cells above 0.8 score quantile | 3.8% |
| Pluvial among cells above 0.8 score quantile | 83.0% |

### 4.7 Expanded open-data pilot

The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in 48.2% of cells (461 of 956). Under the same H3-block protocol, spatial cross-validation accuracy is 0.819 ± 0.024 and F1 is 0.822, both exceeding the fold-mean constant-class baselines (majority-negative accuracy 0.518; always-positive accuracy 0.482 and F1 0.649). Pooled out-of-fold ROC-AUC is 0.880 (fold-mean 0.880 ± 0.032) with average precision 0.815, well above the 0.482 prevalence reference; evidence-score R² is 0.379 ± 0.090 and MAE is 0.279. Per-fold accuracy/F1 are Fold0 0.832 / 0.848, Fold1 0.832 / 0.840, Fold2 0.827 / 0.844, Fold3 0.832 / 0.805, Fold4 0.772 / 0.776; the near-balanced per-fold class composition yields a much tighter fold spread than the smaller pilot. The expanded pilot provides a within-Manhattan scale-up check rather than an independent external validation; citywide generalisation remains unevaluated.

### 4.8 Source-ablation of the composite target

Because the composite target is the maximum of three heterogeneous sources, its construct validity depends on whether ranking discrimination is driven by one source alone. To test this, the same spatial block cross-validation was refit to DEP-only, 311-only, HWM-only, 311+HWM, and the composite; to the composite with shoreline distance removed; and to 311-only with building density removed (Table 7).

Discrimination is reproduced across source definitions rather than concentrated in DEP. In Lower Manhattan, DEP-only pooled ROC-AUC is 0.801 while 311-only reaches 0.853 (still well above 0.5) against 0.850 for the composite; in the expanded pilot the corresponding values are 0.811, 0.843, and 0.880. Dropping building density from the 311-only feature set leaves LM pooled ROC-AUC at 0.839 and expanded at 0.816—still above 0.5—so 311 skill is not an artefact of building density alone. Removing shoreline distance leaves composite discrimination essentially unchanged. The HWM-only target has no usable discrimination in these pilots.

**Table 7. Source-ablation: spatial block-CV ranking discrimination for each target definition.** Same protocol as the primary evaluation (H3 k=2 parent blocks, up to five folds, GBM). LM = Lower Manhattan (n = 262); Exp = expanded pilot (n = 956). These ablations reduce concern that the composite target is an artefact of a single source; they do not prove construct validity.

| Target definition | Positive cells (LM / Exp) | Pooled ROC-AUC (LM / Exp) | Fold-mean ROC-AUC (LM / Exp) | F1 (LM / Exp) |
|---|---|---|---|---|
| DEP-only (polygon area) | 74 / 231 | 0.801 / 0.811 | 0.788 / 0.814 | 0.507 / 0.466 |
| 311-only (crowd reports) | 144 / 373 | 0.853 / 0.843 | 0.824 / 0.845 | 0.773 / 0.707 |
| HWM-only (USGS Ida) | 0 / 6 | — / 0.233 | — / 0.484 | — / 0.000 |
| 311 + HWM | 144 / 375 | 0.853 / 0.836 | 0.824 / 0.836 | 0.773 / 0.706 |
| Composite (max) | 167 / 461 | 0.850 / 0.880 | 0.834 / 0.880 | 0.861 / 0.822 |
| Composite without dist_stream_m | 167 / 461 | 0.851 / 0.887 | 0.825 / 0.887 | 0.865 / 0.831 |
| 311-only without building_density | 144 / 373 | 0.839 / 0.816 | 0.821 / 0.820 | 0.736 / 0.667 |

Note: “—” marks a single-class target that was not fitted.

### 4.9 Block-size sensitivity and spatial autocorrelation

The R7 block size (k = 2) was fixed a priori, so its adequacy was tested by repeating the spatial cross-validation with R8 (k = 1) and R6 (k = 3) parent blocks, by leave-one-R7-block-out (LOBO) for Option B (12 blocks), and by computing Moran’s I of the composite evidence score and of OOF residuals under native R9 k-ring adjacency (Table 8). The composite target is positively spatially autocorrelated (Moran’s I 0.388 in Lower Manhattan, 0.421 in the expanded pilot), confirming that spatially blocked rather than i.i.d. splitting is required. OOF residual Moran’s I is much weaker (0.048 LM; 0.108 Exp), so blocking reduces but does **not fully eliminate** residual spatial structure. Ranking discrimination is moderately stable across block sizes, yet fixed-threshold accuracy/F1 show more spatial heterogeneity—especially in the smaller pilot. LOBO on Lower Manhattan (12 folds) yields pooled ROC-AUC 0.860 (fold-mean 0.860 ± 0.137), consistent with the primary five-fold result but with wider fold dispersion when each block is held out alone.

**Table 8. Block-size sensitivity of the spatial cross-validation.** The same GBM protocol is repeated at parent block sizes k = 1 (R8), k = 2 (R7, primary), and k = 3 (R6), using **up to five folds** (when fewer blocks exist, n_folds = n_blocks). Moran’s I is computed on the composite evidence score and on OOF residuals (y_true − y_proba). LM = Lower Manhattan Option B (n = 262); Exp = expanded pilot (n = 956).

| Pilot | k (block resolution) | Blocks | Pooled ROC-AUC | Fold-mean ROC-AUC | Accuracy | F1 |
|---|---|---|---|---|---|---|
| LM | 1 (R8) | 48 | 0.841 | 0.847 | 0.832 | 0.866 |
| LM | 2 (R7) | 12 | 0.850 | 0.834 | 0.824 | 0.861 |
| LM | 3 (R6) | 4 | 0.794 | 0.833 | 0.850 | 0.619 |
| LM LOBO (R7) | 2 | 12 | 0.860 | 0.860 ± 0.137 | 0.873 | 0.633 |
| Exp | 1 (R8) | 157 | 0.891 | 0.893 | 0.821 | 0.831 |
| Exp | 2 (R7) | 28 | 0.880 | 0.880 | 0.819 | 0.822 |
| Exp | 3 (R6) | 7 | 0.872 | 0.851 | 0.799 | 0.780 |

Moran’s I (composite evidence score): 0.388 (LM), 0.421 (Exp). Moran’s I (OOF residual): 0.048 (LM), 0.108 (Exp). Ranking is more stable than fixed-threshold metrics; residual spatial autocorrelation is reduced but not eliminated.

## 5. Discussion

### 5.1 What the experiments establish

Taken together, the two pilots show two distinct roles of the H3 hierarchy. Spatial blocking changes the interpretation of predictive performance on evidence-positive / evidence-unrecorded labels: the Lower Manhattan model exceeds the always-positive baseline on both accuracy and F1 (0.824 vs 0.637; 0.861 vs 0.769), and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy (0.819 vs 0.518) and F1 (0.822 vs 0.649). Coarsening under a unified study_domain_mask exposes substantial hotspot-set disagreement (mean Jaccard 0.220 to R9, 0.136 to R8 under a strict 10% area budget), while the adaptive representation experiment concentrates cells into 57% of a uniform fine grid without any claimed efficiency gain. Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.850 and 0.880). Source ablation shows that this ranking ability is not DEP-dominated: 311-only still exceeds 0.5 AUC, and 311-only without building density remains discriminative. Block-size and LOBO results show ranking is more stable than fixed-threshold metrics, and residual Moran’s I remains non-zero—so spatial leakage is mitigated, not eliminated. The results therefore support measurable ranking discrimination within the evaluated extents, but no citywide classification skill is claimed.

### 5.2 Relation to prior work

Svellingen et al. [5] use H3 to aggregate a proprietary building-level index for scalable communication, whereas the present framework learns from heterogeneous open evidence and evaluates predictions across held-out H3 spatial blocks. The R8 mean-aggregation Jaccard value of 0.136 (10% area budget; domain-masked) is numerically comparable in magnitude to their reported value of 0.14, but the two measures use different labels, resolutions, and aggregation procedures. The present ladder therefore characterises scale loss in the open-evidence analysis rather than reproducing their metric.

### 5.3 Methodological implications

Methodologically, the same H3 hierarchy links the spatial unit used for evidence assembly to the units used for cross-validation, scale analysis, and subsequent refinement, extending H3 from a post-prediction visualisation layer to the learning and evaluation architecture. The framework is reproducible in the sense that every reported number traces to public code and public data; reproducibility of the pipeline is not the same as validity of the label semantics, and the two are kept distinct in the accompanying audit document. The source-ablation also bears on a specific validity concern: the DEP stormwater layer is a hydrologic–hydraulic model output whose drivers (terrain, imperviousness) overlap with the predictors, so part of the composite’s discrimination could in principle be model-output emulation rather than evidence fusion. That the 311-only target—an observational, crowd-reported source—still reaches pooled ROC-AUC 0.843 in the expanded pilot indicates the framework is not merely re-deriving the DEP map, even though the composite gains only a small margin over the better single source.

### 5.4 Limitations

Several limitations constrain interpretation. The evidence is restricted to two sub-city Manhattan extents: Lower Manhattan Option B (n = 262) and the expanded pilot (n = 956). The open evidence, particularly the 311 complaints, reflects reporting and mapping processes rather than complete ground-truth inundation [7,8], and the DEP stormwater layer is itself a hydrologic–hydraulic model output rather than an observation; only the high-water marks are direct observations. The H3 support follows rectangular bounding boxes rather than a strict Manhattan land footprint, so shoreline and water cells can shift prevalence and predictor distributions. A land-mask sensitivity using NHDPlus water polygons (NHDArea/NHDWaterbody) from the local hydrography extract was computed: requiring land_frac ≥ 0.5 removes only one cell (n = 261; pooled ROC-AUC 0.844), and requiring the cell centroid on land removes two cells (n = 260; ROC-AUC 0.845). The NHD extract in this pilot is shoreline-dominated and does not constitute a full cadastral land polygon; a stronger administrative land mask was not assembled. The shoreline/tidal-water distance predictor remains a tidal-water proxy rather than an inland drainage-density measure. The urban land-cover flag was removed from production features as a deterministic copy of impervious fraction. The terrain and flow-accumulation predictors are heuristic proxies computed on a georeferenced raster without hydrological conditioning, and the DEM interpolation and resolution are those of the underlying export service.

Evaluation is further constrained by class composition and the number of spatial blocks. The smaller Option B pilot is 63.7% evidence-positive and distributes 12 H3 blocks across five folds; the expanded pilot uses 28 blocks. Block-size sensitivity and LOBO (Section 4.9) show ranking discrimination is moderately stable across R8/R7/R6 blocking, while fixed-threshold accuracy/F1 are more heterogeneous; residual Moran’s I (0.048–0.108) shows spatial leakage is reduced but not eliminated. Nested hyperparameter search was not run; GBM settings remain pre-specified. Evidence-score R² is demoted to the Supplement. Adaptive refinement is primarily a cell-count representation experiment. The classifier output is not calibrated.

Rainfall conditioning remains unevaluated under observed forcing (S_h(c) only). DEP area-fraction thresholds (0/1%/5%/10%) are reported as sensitivities in the registry. The FloodNet held-out diagnostic covers only the sparse sensor footprint and does not support citywide event skill claims.

### 5.5 Outstanding steps

Future work should first replace the constant rainfall placeholder with documented event observations and test S_h(c,r) for fixed static features. The same spatial cross-validation protocol can then be applied over broader extents, with denser FloodNet coverage and calibrated probabilities. Spatial buffering around held-out blocks remains a priority because residual Moran’s I shows leakage is not fully eliminated. Where a high-quality administrative land polygon is available, replacing the NHD water-based proxy with a true land footprint would tighten the spatial support.

## 6. Conclusions

Using H3 as a common spatial support links open-evidence learning to spatially blocked validation, scale diagnostics, and selective refinement rather than treating the grid only as a post-processing layer. Across the two Manhattan pilots, the blocked evaluation and prevalence-aware baselines change how classification performance is read, and selective refinement links resolution control to the fitted cell scores without requiring uniform fine-grid representation. The evidence remains limited to the evaluated pilot extents; observed event rainfall, rainfall-responsive predictions, citywide evaluation, and denser FloodNet event validation remain priorities for further assessment.

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

**Figure 6. Resolution effects on the open-evidence score surface (Option B).** (a) ECDF with light histograms of the score at R10 (n = 1788), R9 (n = 262), and R8 (n = 48); (b) area-weighted soft Jaccard from the canonical scale-results table (Table 4). For mean aggregation, R10→R9 = 0.220 and R10→R8 = 0.136.

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
