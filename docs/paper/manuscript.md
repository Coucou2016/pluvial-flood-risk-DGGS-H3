# Spatially blocked pluvial-flood susceptibility learning on the H3 grid using heterogeneous open public data

## Highlights

- An H3-native framework links evidence assembly, spatially blocked validation, and resolution control on one hierarchical grid
- Heterogeneous open sources are kept distinct as evidence (model-derived DEP, crowd-reported 311, observed Ida high-water marks) rather than merged into a single ground truth
- Prevalence-aware baselines change the reading of classification skill; the Lower Manhattan model (Option B, n = 262) exceeds always-positive on accuracy (0.820 vs 0.637) and F1 (0.858 vs 0.769)
- Native fine-resolution label overlay with area-budget fractional hotspots shows substantial scale loss (mean hotspot Jaccard 0.136 to R8 at a 10% area budget)
- Constant synthetic rainfall produces a flat condition response, so rainfall conditioning is deferred to event-based data

---

## Abstract

Urban pluvial flooding develops rapidly when intense rainfall overwhelms drainage before water reaches a watercourse, and screening it at city scale requires representations that are computationally scalable, updateable as new evidence arrives, and evaluated with explicit control of spatial dependence. Many data-driven approaches rely on proprietary damage or insurance labels, and random train-test splits can inflate skill when spatially proximate observations appear in both training and test sets. This study evaluates an H3-native framework in which the hexagonal discrete global grid provides the common spatial support for evidence assembly, spatially blocked validation, and resolution control, using only heterogeneous open public data. Flood evidence is assembled on H3 cells from three sources that are kept distinct: model-derived stormwater polygons (New York City DEP, categories 1–2), crowd-reported street-flooding complaints (NYC 311), and observed high-water marks (USGS Hurricane Ida). Gradient-boosting classifiers and an evidence-score regressor are fitted and evaluated under H3-block spatial cross-validation in which entire parent cells are withheld; after evaluation, separate deployment models are refitted on all cells for descriptive maps and adaptive screening only. In the Lower Manhattan pilot (manuscript bbox, n = 262 R9 cells, 63.7% positive; Major Revision Option B), the model attains spatial cross-validation accuracy 0.820 ± 0.057 and F1 0.858, above the always-positive baseline (0.637 and 0.769), with pooled out-of-fold ROC-AUC 0.848 and average precision 0.855. In the larger pilot (n = 956 cells, 47.9% positive), accuracy is 0.823 ± 0.028 and F1 is 0.826, both above the fold-mean constant-class baselines, with pooled out-of-fold ROC-AUC 0.882 and average precision 0.823.A native fine-resolution label overlay with tie-aware fractional hotspot membership and a strict 10% area budget shows that hotspot membership degrades under coarsening (mean Jaccard 0.136 to R8 at a 10% area budget), and adaptive refinement concentrates representation into about 56% as many cells as a uniform fine grid. Because the training rainfall is constant, the fitted score is invariant across rainfall scenarios; rainfall-conditioned screening therefore remains unevaluated and is deferred to event-based data. The results illustrate a reproducible, prevalence-aware spatial-evaluation architecture for screening pluvial-flood susceptibility from open data, while citywide skill and rainfall-conditioned discrimination remain open questions. Production assembly is fail-closed: missing layers or NaNs abort rather than silently filling synthetic features.

**Keywords:** pluvial flood susceptibility; H3; discrete global grid; spatial cross-validation; machine learning; open data.

---

## 1. Introduction

Urban flooding occurs predominantly during intense rainfall in densely built areas with limited drainage, and its pluvial form—flooding that develops when rainfall overwhelms drainage before entering watercourses—can appear rapidly and with little warning [1]. Assessing this hazard at city scale requires representations that are computationally scalable, updateable as new observations arrive, and evaluated in a way that does not inflate performance. Two limitations recur in data-driven pluvial-flood screening. The first is that some published indices rely on proprietary damage or insurance records, so the underlying labels are neither public nor transferable to jurisdictions without comparable records. The second is evaluation: random train-test splits can overestimate generalisation when spatially proximate observations occur in both the training and test sets because of spatial autocorrelation. For city-scale screening these constraints create a spatial-representation problem as well as a modelling problem: observations, predictions, and evaluation need a spatial support that remains coherent as scale changes.

Discrete Global Grid Systems, and the hexagonal H3 system in particular [2], provide a scalable spatial substrate for integrating observations, predictions, and multi-resolution analysis. H3 is a hierarchical, predominantly hexagonal spatial index with neighbourhood operations and parent–child relationships across resolutions [3]. Hexagonal grids have been applied to multi-scale flood mapping under climate scenarios [4], and a closely related line of work aggregates a pre-existing machine-learning building-level pluvial susceptibility index into H3 cells to reduce query cost and expose resolution-dependent hotspot loss [5,6]. In that formulation H3 serves primarily as a multi-resolution aggregation and communication layer for an inherited index, leaving open the question of how the same hierarchy might support model fitting and evaluation across unseen spatial blocks.

These limitations motivate an H3-native learning and evaluation architecture in which the grid acts as the common spatial support rather than only as an aggregation layer. Heterogeneous public evidence is assembled directly on H3 cells, coarse H3 parents define the spatial holdouts, and the same hierarchy is subsequently used to examine scale effects and guide selective refinement. The contribution therefore lies in linking evidence construction, spatial validation, and resolution control within one hierarchical spatial reference; each of these components is established separately in prior work [4,7,8,9,10]. Throughout, the fitted positive-class model output is treated as a susceptibility score and is kept distinct from both feature-importance measures and the H3-aggregated building index of Svellingen et al. [5].

Accordingly, the analysis asks whether predictive performance persists when entire H3 parent blocks are withheld, relative to class-prevalence baselines; how hotspot membership changes as fine-scale evidence is aggregated, and whether trained cell scores can concentrate fine-resolution representation. These questions are examined on two Manhattan pilot extents, one smaller and one expanded, rather than at citywide scale.

## 2. Study area and data

The analysis uses two Manhattan pilot extents. The smaller is a Lower Manhattan bounding box (74.02–73.97°W, 40.70–40.76°N) that yields **262** H3 resolution-9 cells (Major Revision Option B: the manuscript bbox is the analysis extent; a legacy 141-cell smoke subset is retained only for fast QA). The larger expanded-Manhattan box spans approximately 74.03–73.94°W, 40.68–40.80°N (956 R9 cells). Both lie within New York City and are described as pilot extents throughout. The H3 support follows these bounding boxes; the implications of using a rectangular support rather than a strict Manhattan land footprint are discussed in Section 5.4.

All source datasets are third-party public inputs; cell-level features, labels, fitted models, predictions, diagnostics, tables, and figures are author-derived outputs. The predictor and evidence layers are drawn from public datasets. Elevation is from the USGS 3D Elevation Program [11]; impervious fraction from the National Land Cover Database annual fractional impervious surface [12]; hydrography from NHDPlus High Resolution [13]; flood evidence from New York City Department of Environmental Protection stormwater flood polygons [14], NYC 311 street-flooding complaints [15], and USGS Hurricane Ida high-water marks [16]; and a coastal-confounding diagnostic from FEMA Sandy storm-surge inundation [17]. Machine-readable provenance is recorded in `data/raw/data_manifest.json` (official landing pages, service URLs, SHA-256, mirror status). **DEP stormwater still resolves via a public ArcGIS FeatureServer mirror** (`official_identity_verified=false`). **311 street-flooding complaints are extracted from the official NYC Open Data historical dataset 76ig-c548** (2010–2014; descriptor Street Flooding (SJ); ordered pagination; unique_key dedup; `official_identity_verified=true`). USGS Ida HWM is official (DOI 10.5066/P9OMBJPQ). Building footprints are used to compute building density. A distance-to-mapped-water proxy (`dist_stream_m` in code) is derived from NHDPlus hydrography; because the Lower Manhattan hydrography is dominated by tidal rivers and shoreline features, this predictor is interpreted as shoreline/tidal-water distance rather than as inland drainage density. Polygon intersection area fractions are computed after projecting geometries to EPSG:2263. Table 1 lists the layers and their roles.

**Table 1. Open data layers and their roles in the framework.**

| Layer | Source | Form | Role |
|---|---|---|---|
| Elevation | USGS 3DEP | Raster | Elevation, slope, flow-accumulation proxy |
| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction, urban land-cover flag |
| Hydrography | USGS NHDPlus HR | Vector | Shoreline/tidal-water distance proxy |
| Building footprints | NYC MapHub | Vector | Building density |
| Flood evidence — stormwater | NYC DEP moderate-flood stormwater polygons, current sea levels (Flooding_Category 1–2) | Vector | Model-derived flood-evidence target (continuous and binary) |
| Flood evidence — complaints | NYC 311 street-flooding complaints (official dataset 76ig-c548, 2010–2014 Street Flooding (SJ)) | Vector | Crowd-reported flood-evidence target (continuous and binary) |
| Flood evidence — observations | USGS Hurricane Ida high-water marks | Vector | Observed flood-evidence target (continuous and binary) |
| Negative control | FEMA Sandy surge inundation | Vector | Coastal-overlap diagnostic; never a training label |
| Held-out sensor events | NYC FloodNet events (aq7i-eu5q) + sensor metadata (kb2e-tjy3) | Vector | Strict held-out diagnostic only; never a training label |
| Rainfall condition r | Synthetic constant grid (75 mm/h) | Raster | Condition r; constant in the present pilots |

The cell-level flood-evidence score combines the available open sources. Polygon sources contribute an intersection area fraction (0–1); point sources contribute a per-cell presence indicator. The score is the maximum of the area fraction and the point-presence indicator, clipped to [0,1]. The binary flood-class target is then defined deterministically as flood_class = 1[flood_evidence_score ≥ 1e−9], so any cell with positive evidence is positive. Three properties of this target warrant emphasis. First, the three sources are not interchangeable measurements of one latent variable: the DEP polygons are hydrologic–hydraulic model outputs of moderate stormwater flooding at current sea levels, encoded in two ponding-depth classes (category 1, nuisance flooding with ponding depth ≥4 in to <1 ft; category 2, deep-and-contiguous flooding ≥1 ft; the coastal "future high tides" class is excluded), the 311 complaints are crowd-reported and unverified, and only the high-water marks are direct observations of an actual event (Ida, 2021). Second, the sources span different times and forcings and are therefore collapsed into a static, "has there ever been any evidence here" score rather than a per-event inundation label. Third, the score is not a severity measure: a cell with one complaint receives the same score as a cell with a verified high-water mark, because any point presence saturates the score at 1. The score is consequently treated as a flood-evidence screening target, not as flood risk, flood depth, or a calibrated probability. Each source is retained separately in the assembled table for auditability: the DEP polygons contribute `dep_area_frac` (split further into `dep_nuisance_frac` for category 1 and `dep_deep_frac` for category 2), the 311 complaints contribute `complaint_count`/`complaint_presence`, and the high-water marks contribute `ida_hwm_count`/`ida_hwm_presence`/`ida_hwm_quality`, with an `evidence_sources` string recording which sources are present per cell. The composite score is then constructed from these source-specific columns rather than from an undifferentiated merge, so the claim that the sources are kept distinct is true of the assembled table, not only of the documentation. NYC 311 records in particular reflect reporting and mapping processes, and their biases have been documented previously [7,8]. NYC Open Data FloodNet street-flooding events (`aq7i-eu5q`; published 2026-03-03) and sensor deployment metadata (`kb2e-tjy3`) are public and are downloaded into the raw stack for a **strict held-out** diagnostic (`outputs/floodnet_heldout_validation.json`). They are never joined into the composite training/evaluation target (`labels.include_floodnet: false`). Among study cells that contain at least one FloodNet sensor, OOF scores show weak discrimination of cells with ≥1 QC sensor flood event (Lower Manhattan ROC-AUC 0.343 on 23 sensor cells; expanded 0.468 on 57 sensor cells), so sensor-event agreement is not claimed as external skill. The DEP service provides the moderate-flood polygon layer under both current sea levels and a projected 2050 sea-level-rise scenario; the current-sea-level layer is taken as the primary evidence because it represents present-day flooding, while the 2050 variant is retained as a sensitivity. Re-running the target with the 2050 layer is reported as a sensitivity (`outputs/slr_sensitivity.json`, post–official-311 rebuild): under Option B (n = 262) positive prevalence shifts from 63.7% to 67.6% and pooled ROC-AUC from 0.848 to 0.836; in the expanded pilot the shifts are 47.9%→50.0% and 0.882→0.872. These changes do not alter any substantive conclusion, so the results are not an artefact of the sea-level scenario selected for the stormwater layer. (Pre-revision n = 141 smoke figures are historical only.)

Rainfall enters the framework separately as the condition r (rainfall intensity). The pilot rainfall is a constant synthetic input representing an Ida-like scenario (75 mm/h), not radar or gauge data; this choice is deliberate and its consequence—a flat condition response—is reported in Section 4.5.

## 3. Methods

The method uses the H3 hierarchy as a common spatial reference while assigning distinct roles to the resolutions used for model fitting, spatial blocking, scale diagnostics, and adaptive refinement (Fig. 1).

### 3.1 H3 representation

Supervised modelling uses H3 resolution 9 (R9) as the training and evaluation support. Resolution 10 (R10) provides the fine-evidence support for the scale-loss diagnostic, with hotspots subsequently rolled to R9 and R8; model fitting remains at R9 throughout. Adaptive refinement is a post-training step that replaces selected R9 cells with their resolution-11 (R11) descendants. All H3 indexing and spatial joins use longitude–latitude coordinates (EPSG:4326). Cell areas use H3 native cell-area calculations, distance-to-water uses a great-circle (haversine) distance, and the terrain derivatives are computed on the raster grid and averaged zonally over each cell. The workflow is summarised in Fig. 1.

### 3.2 Features

Static predictors are elevation, slope, a flow-accumulation proxy (D8-derived from the digital elevation model), impervious fraction (NLCD), an urban land-cover flag, building density, and shoreline/tidal-water distance. Elevation, slope, and the flow-accumulation proxy are zonal means over each cell derived from the digital elevation model; impervious fraction is a zonal mean of the NLCD fractional-impervious surface; building density is the building-centroid count divided by cell area; shoreline/tidal-water distance is the great-circle distance from the cell centre to the nearest NHDPlus hydrographic feature; the urban land-cover flag marks cells whose impervious fraction exceeds 0.45. Because the urban flag is a deterministic transformation of the impervious fraction, it is retained only for interpretability and carries no independent information. Rainfall is handled separately as the condition r rather than as a static feature.

### 3.3 Models and baselines

The primary learner is a gradient-boosting classifier and an evidence-score gradient-boosting regressor, each with 80 estimators, maximum depth 4, and learning rate 0.08, fitted on features standardised within each training fold, with a fixed random seed (42); all other estimator parameters retain the scikit-learn 1.8 defaults. Two constant classifiers—always-positive and always-negative—are computed on each held-out fold, and accuracy and F1 are reported alongside these constant classifiers to provide a class-prevalence reference. The majority-class identity is determined from pooled target counts, and the constant-baseline accuracy and F1 use the same fold-wise aggregation as the model metrics. Two further baselines are included for diagnostic comparison: an L2-regularised logistic classifier and a ponding rule defined by the weighted combination

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

### 3.4 Spatial H3-block cross-validation and deployment models

Each R9 cell is assigned to its R7 parent, two H3 resolution levels coarser, and up to five-fold GroupKFold partitions these R7 groups so that no R7 block appears in both the training and the held-out portion of a fold (when fewer than five blocks are available, the number of folds equals the number of blocks). This changes the generalisation target from "new randomly drawn cells" to "new spatial blocks", which is closer to the transfer a screening product would face. For each held-out cell the predicted class probability is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]—are computed from pooled out-of-fold predictions. H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons only.

After evaluation is complete, separate **deployment** classifiers and regressors are refitted on all cells (`fit_rows = n_cells`). These all-cell models are used only for descriptive maps (Fig. 2c) and adaptive-grid screening and are never used to calculate held-out performance metrics. Model manifests record the model role (`evaluation_split` vs `deployment_full`), number and hash of training cells, configuration, software versions, and random seed. Production feature assembly is fail-closed: missing static layers or NaNs abort rather than filling synthetic hash features.

The R7 block size is fixed a priori; block-size sensitivity is reported in Section 4.9 / Table 8.

### 3.5 Scale-loss diagnostics

Fine-resolution hotspot membership is defined on native R10 evidence scores using a fixed 10% area budget with fractional allocation within boundary ties (no lexicographic H3-index tie-break and no cell-count top-k). For each coarse parent p the reference membership is the area-weighted fraction w_ref(p)=Σ_i∈p a_i w_i / Σ_i∈p a_i. Coarse hotspots are selected under the same area budget on area-weighted mean, maximum, or p90 parent scores, allowing fractional membership of the final tied group so that selected coarse area equals the fine budget within floating-point tolerance. The primary overlap metric is the area-weighted soft Jaccard; hard-set Jaccard is reported only as a seeded tie-resolution sensitivity (1000 draws; median and 95% interval). Table 4 and Fig. 6b are read from the same archived diagnostics table (`outputs/jaccard_by_resolution.csv`); figures never recompute Jaccard independently. The fine R10 reference is assembled by overlaying the raw polygon and point geometries directly onto R10 cells—not by inheriting scores from R9 parents. These diagnostics use different labels, resolutions, and hotspot definitions from the Jaccard value reported by Svellingen et al. [5] and are not a reproduction of that result.


### 3.6 Adaptive refinement

After training, the full-fit positive-class model score screens R9 cells for refinement. A cell is selected when its score is at or above the 0.8 quantile of all cell scores, or when its predicted probability is uncertain (uncertainty 1 − 2|p − 0.5| of at least 0.7, i.e. p between 0.35 and 0.65); the selection is then expanded to include the one-ring H3 neighbourhood among the R9 cells. Each selected cell is replaced by its R11 descendants while unselected cells remain at R9. Model fitting precedes the refinement stage, which changes the spatial representation without altering the fitted R9 model. The reported metric is the resulting mixed-resolution cell count relative to a uniform R11 grid. This comparison quantifies representation size only; it does not by itself demonstrate computational efficiency, hotspot retention, or prediction quality, because the selection uses in-sample full-fit scores and the uniform fine reference is estimated from child counts rather than scored directly. These limitations are noted in Section 4.4 and Section 5.4.

### 3.7 Rainfall conditioning

The cell index is defined as

`PFI_h(c,r) = P̂(Y_c = 1 | X_c, r)`,

where Y_c is the binary flood label, X_c are the static predictors, and r is the rainfall condition, and P̂(·) is the classifier's positive-class score output. The classifier output is used directly without a separate calibration analysis and is therefore referred to as a model score rather than a calibrated probability. PFI_h is the fitted cell-level model output and is distinct from both feature-importance measures and PFIb. Because the pilot uses a constant synthetic rainfall input, rainfall has zero training variance and the fitted PFI_h(c,r) is invariant across the evaluated rainfall scenarios; the definition is retained for subsequent analyses with observed rainfall variation, but rainfall-conditioned discrimination is not claimed in the present study.

### 3.8 Coastal-confounding diagnostic

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a coastal-confounding diagnostic rather than a strict negative control. Because the flood-evidence score combines polygon overlap and point presence, the pluvial grouping in the negative control is derived from the same composite flood_class definition used elsewhere, so that a cell carrying only a point label is counted as pluvial rather than misassigned to the "neither" group. The control reports the overlap between pluvial evidence and coastal inundation (the coastal-only fraction) and the difference in the **out-of-fold model score** between pluvial-only and coastal-only cells. The score compared is the held-out gradient-boosting score, never the target flood-evidence score, because a coastal-only cell has flood_class = 0 by construction and therefore a target score of 0 by definition; comparing target scores would be circular. Sandy labels are never used as training labels.

## 4. Results

### 4.1 Spatial pattern of evidence, predictions, and the full-fit score

On the 262-cell Lower Manhattan R9 support (Option B), the open-evidence scores, out-of-fold scores, and full-fit model score show related but distinct spatial patterns (Fig. 2). The evidence scores are bimodal by construction: cells with no positive evidence score 0, whereas positive evidence yields either a fractional polygon-overlap score or a point-presence score of 1 (median 1.0, mean 0.598). Fig. 3 shows how this composite surface decomposes into its source components: the DEP stormwater polygons and the 311 crowd reports occupy overlapping but not identical cell sets, and the composite score is the maximum over the source-specific layers. The Ida high-water marks contribute no cells within the Lower Manhattan extent—the USGS Ida points lie outside this narrow bounding box—so the Lower Manhattan composite is driven by the DEP and 311 sources alone (the expanded pilot includes 14 high-water-mark points across six cells). The out-of-fold scores are on average moderate (mean 0.655) and less dispersed, consistent with the modest pooled discrimination reported in Section 4.2 (ROC-AUC 0.847 and average precision 0.851 at 63.7% positive prevalence). The full-fit score has a mean of about 0.68 and shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.63), as expected when the same cells, features, and labels are refitted without the five-fold holdout structure. The full-fit surface is an in-sample fit and is not a validation result; predictive performance is assessed separately from the out-of-fold metrics reported in Section 4.2.

### 4.2 Spatial H3-block cross-validation

The smaller pilot contains 262 R9 cells distributed over 12 R7 blocks. Five-fold spatial cross-validation yields accuracy 0.820 ± 0.057 and F1 0.858 (Fig. 4). Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). The held-out labels are positive in 63.7% of cells, and the model exceeds the always-positive baseline on both accuracy (0.820 vs 0.637) and F1 (0.858 vs 0.769); the always-negative baseline accuracy is 0.363. Pooled out-of-fold ROC-AUC is 0.848 and pooled average precision is 0.855, above the 0.637 positive-prevalence reference. The evidence-score R² is 0.191 ± 0.287 and is reported for completeness; it quantifies fit to the constructed flood-evidence score rather than to any physical severity variable. Table 3 summarises these numbers together with the expanded-pilot results.

**Table 3. Spatial H3-block cross-validation summary for the two pilots.** Accuracy, F1, evidence-score R², and MAE are fold means ± population SD across five held-out folds; ROC-AUC and average precision are pooled out-of-fold values. For the smaller pilot the positive class is the majority class (63.7%), so the always-positive classifier is also the majority baseline; for the expanded pilot the majority class is negative.

| Metric | Lower Manhattan (n = 262) | Expanded (n = 956) |
|---|---|---|
| Accuracy | 0.820 ± 0.057 | 0.823 ± 0.028 |
| F1 | 0.858 | 0.826 |
| Evidence-score R² | 0.191 ± 0.287 | 0.348 ± 0.110 |
| MAE | 0.279 | 0.283 |
| Pooled ROC-AUC | 0.848 | 0.882 |
| Pooled average precision | 0.855 | 0.823 |
| Always-positive accuracy | 0.637 | 0.479 |
| Always-positive F1 | 0.769 | 0.646 |
| Always-negative accuracy | 0.363 | 0.521 |
| Majority-class F1 | 0.769 (positive) | 0 (negative) |

Note: SD denotes the population standard deviation across the five held-out folds (ddof = 0); the fold-mean values in the first four rows are arithmetic means of the per-fold metrics.

### 4.3 Scale-loss Jaccard ladder

Fine-resolution hotspots are defined at R10 by a strict 10% area budget with fractional membership at tied boundary scores. Parent reference membership is area-weighted (w_ref), and coarse hotspots use the same area budget on mean/max/p90 scores. Under mean aggregation the R9 rollup yields area-weighted soft Jaccard 0.227 (hard median 0.148) and the R8 rollup yields 0.136 (hard median 0.000). Maximum aggregation no longer saturates at 1.0 under this protocol. Hard Jaccard is a sensitivity only. Table 4 and Fig. 6b are read from the same CSV. 
Fig. 5 maps the R10 open-evidence score surface and its mean rollups to R9 and R8 on the same label-assembly footprint, providing a spatial view of the smoothing that accompanies coarsening. Fig. 6a summarises the same scale dependence through the score distributions: the R10 distribution is wide and bimodal, while the mean rollups at R9 and R8 are progressively compressed, and Fig. 6b displays the area-weighted soft Jaccard values from Table 4 by aggregation and coarse resolution (R10→R9 mean 0.227; R10→R8 mean 0.136). Table 4 quantifies sensitivity to the aggregation operator. Figures 5 and 6 hold mean aggregation fixed: Fig. 5 shows the spatial effect of coarsening, whereas Fig. 6 summarises the corresponding changes in score distribution and hotspot membership. These values use different labels, resolutions, and hotspot definitions from the PFIb Jaccard of 0.14 reported by Svellingen et al. [5] and are not interpreted as a reproduction of that value. Table 4 lists the full ladder.

**Table 4. Scale-loss ladder under a strict 10% area budget with fractional membership ties.** Fine R10 support n = 1857 (Option B). Primary metric is the area-weighted soft Jaccard; hard Jaccard is a 1000-draw seeded tie-resolution sensitivity. All values are from `outputs/jaccard_by_resolution.csv`.

| Coarse resolution | Aggregation | Soft Jaccard | Hard median [95% CI] | Fine-parent recall | Coarse precision |
|---|---|---|---|---|---|
| R9 | Mean | 0.227 | 0.148 [0.074, 0.259] | 0.370 | 0.370 |
| R9 | Maximum | 0.649 | 0.031 [0.000, 0.100] | 0.787 | 0.787 |
| R9 | P90 | 0.571 | 0.034 [0.000, 0.138] | 0.727 | 0.727 |
| R8 | Mean | 0.136 | 0.000 [0.000, 0.000] | 0.239 | 0.239 |
| R8 | Maximum | 0.570 | 0.000 [0.000, 0.000] | 0.726 | 0.726 |
| R8 | P90 | 0.682 | 0.000 [0.000, 0.000] | 0.811 | 0.811 |

Note: `matched_budgets_cell_count=false`; `budget_match_mode=strict_area_budget`. The full ladder is plotted in Supplementary Fig. S1.

### 4.4 Adaptive versus fixed and uniform fine grids

The fixed coarse grid has 262 cells. Adaptive refinement selects 145 of 262 R9 cells and produces 7,222 mixed cells, compared with 12,838 cells for uniform R11 refinement (Supplementary Fig. S2). The adaptive grid therefore uses 56.3% as many cells as the uniform fine grid. This comparison quantifies representation size by cell count; runtime, memory use, hotspot retention, and city-scale computational cost were not evaluated, and the selection is based on in-sample **deployment_full** scores. Table 5 lists the counts.

**Table 5. Adaptive refinement versus fixed and uniform fine grids by cell count** (Lower Manhattan Option B; adaptive = 56.3% of uniform R11; 145 of 262 R9 cells refined).

| Representation | Cell count |
|---|---|
| Fixed R9 | 262 |
| Adaptive R9/R11 | 7,222 |
| Uniform R11 | 12,838 |

### 4.5 Rainfall scenarios

The scenario loop covers the 262 cells at four intensities—moderate (25), heavy (40), Ida-like (75), and extreme (100 mm/h). Because every training cell carries the same synthetic rainfall value, rainfall has zero training variance and the fitted within-cell score range across scenarios is 0. Rainfall-conditioned discrimination is therefore not claimed; validated event rainfall remains a placeholder for future work.

### 4.6 Sandy coastal-confounding diagnostic

Across the 262 cells, 74 intersect Sandy coastal inundation and 165 carry pluvial evidence (under the composite flood_class definition); 44 have both, and 30 are coastal-only (11.5%). The control compares the out-of-fold model score across these groups rather than the target, because a coastal-only cell has flood_class = 0 and therefore a target score of 0 by definition; comparing target scores would be circular. The out-of-fold score averages 0.406 in coastal-only cells, 0.886 in pluvial-only cells, 0.760 in cells with both, and 0.280 in cells with neither, giving a pluvial−coastal out-of-fold score difference of 0.480. Among the 53 cells above the 0.8 score quantile, 3.8% are coastal-only and 83.0% carry pluvial evidence. The coastal-only cells therefore receive non-trivial out-of-fold scores, consistent with the model partially learning low-elevation, shoreline-proximal signal, but pluvial-only cells still score highest, so the model is not driven solely by coastal position. Coastal overlap is not a training label. Table 6 details the overlap and mean out-of-fold scores.

**Table 6. Sandy coastal-confounding diagnostic statistics on the 262-cell Option B pilot.** The score comparison uses the out-of-fold model score (never the target flood-evidence score, which is 0 in coastal-only cells by construction). The pluvial−coastal difference is the mean out-of-fold score of pluvial-only cells minus that of coastal-only cells.

| Statistic | Value |
|---|---|
| Cells intersecting Sandy inundation | 74 of 262 |
| Cells with pluvial evidence | 165 of 262 |
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

The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in 47.9% of cells (458 of 956). Under the same H3-block protocol, spatial cross-validation accuracy is 0.823 ± 0.028 and F1 is 0.826, both exceeding the fold-mean constant-class baselines (majority-negative accuracy 0.521; always-positive accuracy 0.479 and F1 0.646). Pooled out-of-fold ROC-AUC is 0.882 (fold-mean 0.881 ± 0.034) with average precision 0.823, well above the 0.479 prevalence reference; evidence-score R² is 0.348 ± 0.110 and MAE is 0.283. Per-fold accuracy/F1 are Fold0 0.843 / 0.856, Fold1 0.838 / 0.841, Fold2 0.817 / 0.834, Fold3 0.847 / 0.822, and Fold4 0.772 / 0.776; the near-balanced per-fold class composition (positive test counts 76–102) yields a much tighter fold spread than the smaller pilot. The expanded pilot provides a within-Manhattan scale-up check rather than an independent external validation; citywide generalisation remains unevaluated.

### 4.8 Source-ablation of the composite target

Because the composite target is the maximum of three heterogeneous sources, its construct validity depends on whether ranking discrimination is driven by one source alone—in particular, whether the model merely re-derives the DEP hydrologic–hydraulic map from the terrain and imperviousness predictors that share its drivers. To test this, the same spatial block cross-validation was refit to five target definitions (DEP-only, 311-only, HWM-only, 311+HWM, and the composite) and to the composite with the shoreline/tidal-water distance predictor removed (Table 7).

Discrimination is reproduced across source definitions rather than concentrated in one. In the expanded pilot, DEP-only and 311-only reach pooled ROC-AUC of 0.811 and 0.844, respectively, against 0.882 for the composite; in the smaller pilot the corresponding values are 0.802 and 0.846 against 0.848. The 311-only result is the more informative of the two, because 311 complaints are observational rather than model-derived, so their discrimination cannot be explained as reconstruction of the DEP model output. The composite exceeds either single source in the expanded pilot, consistent with a modest fusion benefit, but the gain over the better single source is small (0.882 versus 0.844). The HWM-only target has no discrimination: no Ida high-water marks fall in the smaller pilot, and in the expanded pilot the six marked cells yield pooled ROC-AUC 0.233 and zero F1, so the high-water marks contribute presence to the composite without independent ranking ability. Removing the shoreline/tidal-water distance predictor leaves discrimination essentially unchanged (pooled ROC-AUC 0.882 versus 0.882, accuracy 0.817 versus 0.823), indicating that the ranking ability is not carried by the coastal-position proxy.

**Table 7. Source-ablation: spatial block-CV ranking discrimination for each target definition.** Same protocol as the primary evaluation (H3 k=2 parent blocks, up to five folds, GBM). LM = Lower Manhattan (n = 262); Exp = expanded pilot (n = 956). Pooled and fold-mean ROC-AUC are reported; HWM-only is not fitted in LM because no high-water marks fall there. These ablations reduce concern that the composite target is an artefact of a single source; they do not prove construct validity.

| Target definition | Positive cells (LM / Exp) | Pooled ROC-AUC (LM / Exp) | Fold-mean ROC-AUC (LM / Exp) | F1 (LM / Exp) |
|---|---|---|---|---|
| DEP-only (polygon area) | 74 / 231 | 0.802 / 0.811 | 0.789 / 0.815 | 0.496 / 0.455 |
| 311-only (crowd reports) | 144 / 373 | 0.846 / 0.844 | 0.814 / 0.845 | 0.770 / 0.718 |
| HWM-only (USGS Ida) | 0 / 6 | — / 0.233 | — / 0.484 | — / 0.000 |
| 311 + HWM | 144 / 375 | 0.846 / 0.838 | 0.814 / 0.839 | 0.770 / 0.718 |
| Composite (max) | 167 / 458 | 0.848 / 0.882 | 0.821 / 0.881 | 0.858 / 0.826 |
| Composite without dist_stream_m | 167 / 458 | 0.852 / 0.882 | 0.830 / 0.880 | 0.855 / 0.820 |

Note: "—" marks a single-class target that was not fitted. Pooled ROC-AUC in the smaller pilot differs from the fold-mean because the five folds derive from different fitted models on 12 blocks (fold-mean and pooled differ when score scales vary across folds); fold-mean and pooled values are both reported rather than privileging one.

### 4.9 Block-size sensitivity and spatial autocorrelation

The R7 block size (k = 2) was fixed a priori, so its adequacy was tested by repeating the spatial cross-validation with R8 (k = 1) and R6 (k = 3) parent blocks and by computing Moran's I of the composite evidence score under native R9 k-ring adjacency (Table 8). The composite target is positively spatially autocorrelated (Moran's I 0.388 in Lower Manhattan, 0.433 in the expanded pilot), confirming that spatially blocked rather than i.i.d. splitting is required. In the expanded pilot, ranking discrimination is stable across block sizes (pooled ROC-AUC 0.890, 0.882, and 0.872 at R8, R7, and R6). The Lower Manhattan Option B pilot (12 R7 blocks) yields pooled ROC-AUC 0.843 (R8), 0.848 (R7), and 0.795 (R6; 4 blocks → 4 folds). Block-size sensitivity is therefore reported rather than deferred as future work.

**Table 8. Block-size sensitivity of the spatial cross-validation.** The same GBM protocol is repeated at parent block sizes k = 1 (R8), k = 2 (R7, primary), and k = 3 (R6), using **up to five folds** (when fewer blocks exist, n_folds = n_blocks; e.g. LM R6 uses 4 folds). Moran's I is computed on the composite evidence score under native R9 k-ring adjacency. LM = Lower Manhattan Option B (n = 262); Exp = expanded pilot (n = 956).

| Pilot | k (block resolution) | Blocks | Pooled ROC-AUC | Fold-mean ROC-AUC | Accuracy | F1 | Evidence-score R² |
|---|---|---|---|---|---|---|---|
| LM | 1 (R8) | 48 | 0.843 | 0.848 | 0.836 | 0.868 | 0.351 |
| LM | 2 (R7) | 12 | 0.848 | 0.821 | 0.820 | 0.858 | 0.191 |
| LM | 3 (R6) | 4 | 0.795 | 0.846 | 0.859 | 0.630 | — |
| Exp | 1 (R8) | 157 | 0.890 | 0.893 | 0.818 | 0.825 | 0.380 |
| Exp | 2 (R7) | 28 | 0.882 | 0.881 | 0.823 | 0.826 | 0.348 |
| Exp | 3 (R6) | 7 | 0.872 | 0.848 | 0.808 | 0.786 | 0.272 |

Moran's I (composite evidence score): 0.388 (LM), 0.433 (Exp). Fold-mean and pooled ROC-AUC differ in the smaller pilot because the folds derive from different fitted models on few blocks.

## 5. Discussion

### 5.1 What the experiments establish

Taken together, the two pilots show two distinct roles of the H3 hierarchy. Spatial blocking changes the interpretation of predictive performance: the Lower Manhattan model exceeds the always-positive baseline on both accuracy and F1 (0.820 vs 0.637; 0.858 vs 0.769), and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy (0.823 vs 0.521) and F1 (0.826 vs 0.646). Coarsening and selective refinement expose a separate trade-off in spatial representation: mean aggregation of the fine hotspot produces substantial hotspot-set disagreement under the specified projection-and-rethresholding protocol (Jaccard 0.227 to R9, 0.136 to R8 under a strict 10% area budget), while adaptive refinement concentrates representation into 56% of a uniform fine grid without any claimed efficiency gain. Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.848 and 0.882), with average precision 0.855 and 0.823; average precision is prevalence-dependent, so the two values are interpreted relative to their respective prevalence references (0.637 and 0.479) rather than compared to one another. A source-level ablation shows that this ranking ability is reproduced for the DEP-only and 311-only targets rather than concentrated in a single source, and that it persists when the shoreline/tidal-water distance predictor is removed, so source ablation reduces, but does not eliminate, concern that shared spatial structure or reporting processes drive discrimination. Accordingly, the results support measurable ranking discrimination within the evaluated extents, but no citywide classification skill is claimed.

### 5.2 Relation to prior work

Svellingen et al. [5] use H3 to aggregate a proprietary building-level index for scalable communication, whereas the present framework learns from heterogeneous open evidence and evaluates predictions across held-out H3 spatial blocks. The R8 mean-aggregation Jaccard value of 0.136 (10% area budget) is numerically comparable in scale to their reported value of 0.14, but the two measures use different labels, resolutions, and aggregation procedures. The present ladder therefore characterises scale loss in the open-evidence analysis rather than reproducing their metric.

### 5.3 Methodological implications

Methodologically, the same H3 hierarchy links the spatial unit used for evidence assembly to the units used for cross-validation, scale analysis, and subsequent refinement, extending H3 from a post-prediction visualisation layer to the learning and evaluation architecture. The framework is reproducible in the sense that every number traces to public code and public data; but reproducibility of the pipeline is not the same as validity of the label semantics, and the two are kept distinct in the accompanying audit document. The source-ablation also bears on a specific validity concern: the DEP stormwater layer is a hydrologic–hydraulic model output whose drivers (terrain, imperviousness) overlap with the predictors, so part of the composite's discrimination could in principle be model-output emulation rather than evidence fusion. That the 311-only target—an observational, crowd-reported source—still reaches pooled ROC-AUC 0.844 in the expanded pilot indicates the framework is not merely re-deriving the DEP map, even though the composite gains only a small margin over the better single source.

### 5.4 Limitations

Several limitations constrain the interpretation of the results. The evidence is restricted to two sub-city Manhattan extents: Lower Manhattan Option B (n = 262) and the expanded pilot (n = 956). The open evidence, particularly the 311 complaints, reflects reporting and mapping processes rather than complete ground-truth inundation [7,8], and the DEP stormwater layer is itself a hydrologic–hydraulic model output rather than an observation; only the high-water marks are direct observations. The H3 support follows rectangular bounding boxes rather than a strict Manhattan land footprint, so shoreline and water cells can shift prevalence and predictor distributions; the shoreline/tidal-water distance predictor is a tidal-water proxy rather than an inland drainage-density measure, and the urban land-cover flag is a deterministic copy of the impervious fraction. The terrain and flow-accumulation predictors are heuristic proxies computed on a georeferenced raster without hydrological conditioning, and the DEM interpolation and resolution are those of the underlying export service.

Evaluation is further constrained by class composition and the number of spatial blocks. The smaller Option B pilot is 63.7% positive and distributes 12 H3 blocks across five folds; the expanded pilot uses 28 blocks with larger per-fold test sets. Block-size sensitivity (Section 4.9) shows the expanded pilot's ranking discrimination is stable across R8/R7/R6 blocking (pooled ROC-AUC 0.890/0.882/0.872), and the Option B Lower Manhattan pooled ROC-AUC is 0.843/0.848/0.795; the composite target is positively spatially autocorrelated (Moran's I 0.388–0.433). The evidence-score R² is 0.191 in the smaller pilot and 0.348 in the expanded pilot, and both values quantify fit to the constructed evidence score rather than to a physical severity variable. Adaptive refinement was selected with in-sample deployment_full scores and compared only by cell count, so it demonstrates representation-size reduction but not computational efficiency or hotspot retention. The classifier output is not calibrated, and the model score is therefore not presented as a probability.

Rainfall conditioning remains unevaluated under observed forcing. The current input is a constant synthetic rainfall value rather than event-specific gauge or radar rainfall, giving a within-cell score range of 0 across scenarios. Primary performance interpretation therefore rests on spatial cross-validation, with random-split accuracy retained as a diagnostic comparison. The fold-level variation, including Fold4 on n = 24 in the smaller pilot, further limits inference from any single fold. The FloodNet held-out diagnostic covers only the sparse sensor footprint (26 sensors / 23 R9 cells in Lower Manhattan; 69 / 57 in the expanded pilot) and does not support citywide event skill claims.

### 5.5 Outstanding steps

Future work should first replace the synthetic rainfall condition with documented event observations and test whether the fitted score varies across rainfall intensities for fixed static features. The same spatial cross-validation protocol can then be applied over broader, including citywide, extents, with denser FloodNet coverage, sensor-cluster uncertainty, and depth/duration thresholds beyond the binary cell-level event indicator used here. Probability calibration, spatial buffering around held-out blocks, and leave-one-block-out evaluation for the smaller pilot remain priorities for further assessment.

## 6. Conclusions

Using H3 as a common spatial support links open-evidence learning to spatially blocked validation, scale diagnostics, and selective refinement rather than treating the grid only as a post-processing layer. Across the two Manhattan pilots, the blocked evaluation and prevalence-aware baselines change the interpretation of classification performance, and selective refinement links resolution control to the fitted cell scores without requiring uniform fine-grid representation. The evidence remains limited to the evaluated pilot extents; observed event rainfall, rainfall-responsive predictions, citywide evaluation, and denser FloodNet event validation remain priorities for further assessment.

---

## CRediT authorship contribution statement

**[待补充 — to be completed before submission: list each author with their CRediT roles.]**

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Figure captions

**Figure 1. Open-evidence H3 pluvial-flood susceptibility workflow.** Heterogeneous open evidence—model-derived DEP stormwater polygons (categories 1–2), 311 street-flooding complaints, and USGS Ida high-water marks—together with static predictors (elevation, slope, a flow-accumulation proxy, land cover, buildings, shoreline/tidal-water distance) and a rainfall condition r (a constant synthetic rainfall condition in the present pilot, not observed radar rainfall) are assembled into H3 cells at R9 with provenance tags. Gradient-boosting classification and evidence-score regression are then evaluated under H3-block GroupKFold cross-validation against constant-class and logistic/ponding-rule baselines; diagnostics include the model score PFI_h(c,r) (currently flat across scenarios), a scale-loss Jaccard ladder (R10 to R9/R8), adaptive refinement to R11, and a Sandy coastal-overlap diagnostic. The dashed FEMA Sandy side-channel represents the post-fit coastal-overlap diagnostic and has no role in model training.

**Figure 2. Spatial results for the Lower Manhattan pilot (n = 262 R9 cells; Option B).** (a) Open-evidence flood-evidence score; (b) pooled out-of-fold gradient-boosting score under H3-block spatial cross-validation; (c) **deployment_full** model score at the synthetic Ida-like condition r = 75 mm/h, fitted using all 262 cells after evaluation. The surface is invariant across the evaluated scenarios because the training rainfall is constant (Section 4.5). Panel (c) is an in-sample deployment fit, not a validation result. Hexagons are coloured by value on a common 0–1 scale; grey shading is the DEM relief and light-blue lines/polygons are NHDPlus shoreline and water features.

**Figure 3. Source-specific open-evidence maps for the Lower Manhattan pilot (n = 262 R9 cells).** The composite flood-evidence score (d) is the maximum over the source-specific layers retained as separate columns in the assembled table: (a) DEP stormwater polygon area fraction (categories 1–2), (b) 311 crowd-report count, and (c) USGS Ida high-water-mark count. Panel (a) and (d) share a 0–1 continuous scale; (b) and (c) use count scales. No Ida high-water marks fall within this extent, so panel (c) is empty by data availability rather than by processing choice. Hexagons are coloured by value; grey shading is the DEM relief and light-blue lines/polygons are NHDPlus shoreline and water features.

**Figure 4. Spatial H3-block cross-validation performance for the Lower Manhattan pilot.** Classification accuracy and F1 are shown as paired markers for each of five held-out folds formed from 12 R7 H3 blocks (n = 262 cells); a final x-position shows the fold mean ± SD with error bars. Three horizontal reference lines mark the constant-class baselines: the blue dashed line is the always-positive accuracy, the red dashed line is the always-positive F1, and the grey dotted line is the always-negative accuracy. Per-fold test size and positive prevalence are annotated inside the axes.

**Figure 5. Multi-resolution open-evidence score surface on the label-assembly footprint (Option B).** (a) R10 open-evidence flood score (n = 1857); (b) mean rollup to R9 (n = 296); and (c) mean rollup to R8 (n = 52). All panels use the same map extent and derive from the same natively assembled R10 label-assembly footprint, with a common 0–1 colour scale that makes the smoothing accompanying coarsening visible directly. Figure 6 summarises cross-resolution hotspot similarity, while Table 4 quantifies sensitivity to the aggregation rule.

**Figure 6. Resolution effects on the open-evidence score surface (Option B).** (a) Violin plots with overlaid cell scores of the distribution at R10 (n = 1857), R9 (n = 296, mean rollup), and R8 (n = 52, mean rollup), showing variance compression as the grid coarsens. (b) Area-weighted soft Jaccard from the canonical scale-results table (Table 4 / `outputs/jaccard_by_resolution.csv`) for mean, maximum, and p90 aggregations at R9 and R8; the figure does not recompute Jaccard. For mean aggregation, R10→R9 = 0.227 and R10→R8 = 0.136.

**Supplementary Figure S1. Open-evidence hotspot scale-loss diagnostics across H3 resolutions.** Area-weighted soft Jaccard and F1 compare hotspot membership defined on the reference fine support (H3 R10; 10% area budget with fractional ties) with R9 and R8 representations under mean, maximum, and p90 aggregation. This figure reads the same CSV as Table 4.

**Supplementary Figure S2. Adaptive refinement versus uniform fine grids by cell count.** Fixed R9 (262), adaptive mixed R9/R11 (7,222), and uniform R11 (12,838) representations are compared for the Lower Manhattan Option B pilot (adaptive = 56.3% of uniform R11; 145 of 262 R9 cells refined). The comparison is of representation size only; it does not measure runtime, memory, or hotspot retention, and is reported as a table (Table 5) in the main text.

---

## Data and code availability

The public repository (code, configs, tests, paper documentation, and small summary tables; large rasters, geojson, trained model binaries, and large parquet files are excluded) is available at https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3. The working tree is currently dirty under Major Revision; an immutable submission tag will be created only after author confirmation. Provenance of reported outputs is recorded in `outputs/paper_results.json` and the accompanying audit document. Each raw layer is mapped in the repository download manifest to its source URL, retrieval date, and license. Analyses that produced the frozen paper artifacts used scikit-learn 1.8.0 and H3 4.4.2 as recorded in the run metadata (`models/nyc_smoke/run_metadata.json`, `created_utc=2026-08-30`); the repository pins `h3==4.4.2` for reproducibility. A live working environment may temporarily report a newer H3 build (observed 4.5.0) until that pin is reinstalled—do not rewrite frozen metadata without a full re-run. Synthetic demonstrations are excluded from scientific evidence. A process-oriented research report and a data-authenticity audit document accompany the manuscript in the same documentation folder.

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During preparation of this work, generative AI tools (including Cursor/Composer agents) assisted with language editing, code review and debugging, test design, figure consistency checks, and drafting of the technical audit. Authors executed the scientific code, verified numerical outputs against regenerated artifacts, and take full responsibility for the content. Author names, affiliations, ORCID, and CRediT statements remain human placeholders pending confirmation.

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
