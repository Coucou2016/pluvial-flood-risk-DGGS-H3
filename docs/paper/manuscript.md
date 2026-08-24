# Spatially blocked pluvial-flood susceptibility learning on the H3 grid using heterogeneous open public data

## Highlights

- An H3-native framework links evidence assembly, spatially blocked validation, and resolution control on one hierarchical grid
- Heterogeneous open sources are kept distinct as evidence (model-derived DEP, crowd-reported 311, observed Ida high-water marks) rather than merged into a single ground truth
- Prevalence-aware baselines change the reading of classification skill; the Lower Manhattan model exceeds always-positive on accuracy (0.808 vs 0.687) and F1 (0.864 vs 0.813)
- Native fine-resolution label overlay reveals substantial scale loss (mean hotspot Jaccard 0.21 to R9, 0.17 to R8)
- Constant synthetic rainfall produces a flat condition response, so rainfall conditioning is deferred to event-based data

---

## Abstract

Urban pluvial flooding develops rapidly when intense rainfall overwhelms drainage before water reaches a watercourse, and screening it at city scale requires representations that are computationally scalable, updateable as new evidence arrives, and evaluated with explicit control of spatial dependence. Many data-driven approaches rely on proprietary damage or insurance labels, and random train-test splits can inflate skill when spatially proximate observations appear in both training and test sets. This study evaluates an H3-native framework in which the hexagonal discrete global grid provides the common spatial support for evidence assembly, spatially blocked validation, and resolution control, using only heterogeneous open public data. Flood evidence is assembled on H3 cells from three sources that are kept distinct: model-derived stormwater polygons (New York City DEP, categories 1–2), crowd-reported street-flooding complaints (NYC 311), and observed high-water marks (USGS Hurricane Ida). Gradient-boosting classifiers and an evidence-score regressor are fitted and evaluated under H3-block spatial cross-validation in which entire parent cells are withheld. In the Lower Manhattan pilot (n = 141 cells, 69.5% positive), the model attains spatial cross-validation accuracy 0.808 ± 0.085 and F1 0.864 ± 0.061, above the always-positive baseline (0.687 and 0.813), with pooled out-of-fold ROC-AUC 0.741 and average precision 0.803. In the larger pilot (n = 956 cells, 49.7% positive), accuracy is 0.824 ± 0.013 and F1 is 0.832 ± 0.019, both above the fold-mean constant-class baselines, with pooled out-of-fold ROC-AUC 0.875. A native fine-resolution label overlay shows that hotspot membership degrades markedly under coarsening (mean Jaccard 0.21 to R9 and 0.17 to R8), and adaptive refinement concentrates representation into 60% as many cells as a uniform fine grid. Because the training rainfall is constant, the fitted score is invariant across rainfall scenarios; rainfall-conditioned screening therefore remains unevaluated and is deferred to event-based data. The results illustrate a reproducible, prevalence-aware spatial-evaluation architecture for screening pluvial-flood susceptibility from open data, while citywide skill and rainfall-conditioned discrimination remain open questions.

**Keywords:** pluvial flood susceptibility; H3; discrete global grid; spatial cross-validation; machine learning; open data.

---

## 1. Introduction

Urban flooding occurs predominantly during intense rainfall in densely built areas with limited drainage, and its pluvial form—flooding that develops when rainfall overwhelms drainage before entering watercourses—can appear rapidly and with little warning [1]. Assessing this hazard at city scale requires representations that are computationally scalable, updateable as new observations arrive, and evaluated in a way that does not inflate performance. Two limitations recur in data-driven pluvial-flood screening. The first is that some published indices rely on proprietary damage or insurance records, so the underlying labels are neither public nor transferable to jurisdictions without comparable records. The second is evaluation: random train-test splits can overestimate generalisation when spatially proximate observations occur in both the training and test sets because of spatial autocorrelation. For city-scale screening these constraints create a spatial-representation problem as well as a modelling problem: observations, predictions, and evaluation need a spatial support that remains coherent as scale changes.

Discrete Global Grid Systems, and the hexagonal H3 system in particular [2], provide a scalable spatial substrate for integrating observations, predictions, and multi-resolution analysis. H3 is a hierarchical, predominantly hexagonal spatial index with neighbourhood operations and parent–child relationships across resolutions [3]. Hexagonal grids have been applied to multi-scale flood mapping under climate scenarios [4], and a closely related line of work aggregates a pre-existing machine-learning building-level pluvial susceptibility index into H3 cells to reduce query cost and expose resolution-dependent hotspot loss [5,6]. In that formulation H3 serves primarily as a multi-resolution aggregation and communication layer for an inherited index, leaving open the question of how the same hierarchy might support model fitting and evaluation across unseen spatial blocks.

These limitations motivate an H3-native learning and evaluation architecture in which the grid acts as the common spatial support rather than only as an aggregation layer. Heterogeneous public evidence is assembled directly on H3 cells, coarse H3 parents define the spatial holdouts, and the same hierarchy is subsequently used to examine scale effects and guide selective refinement. The contribution therefore lies in linking evidence construction, spatial validation, and resolution control within one hierarchical spatial reference; each of these components is established separately in prior work [4,7,8,9,10]. Throughout, the fitted positive-class model output is treated as a susceptibility score and is kept distinct from both feature-importance measures and the H3-aggregated building index of Svellingen et al. [5].

Accordingly, the analysis asks whether predictive performance persists when entire H3 parent blocks are withheld, relative to class-prevalence baselines; how hotspot membership changes as fine-scale evidence is aggregated, and whether trained cell scores can concentrate fine-resolution representation. These questions are examined on two Manhattan pilot extents, one smaller and one expanded, rather than at citywide scale.

## 2. Study area and data

The analysis uses two Manhattan pilot extents. The smaller is a Lower Manhattan bounding box (approximately 74.02–73.97°W, 40.70–40.76°N); the larger expanded-Manhattan box spans approximately 74.03–73.94°W, 40.68–40.80°N. Both lie within New York City and are described as pilot extents throughout. The H3 support follows these bounding boxes; the implications of using a rectangular support rather than a strict Manhattan land footprint are discussed in Section 5.4.

The predictor and evidence layers are drawn from public datasets downloaded in August 2026. Elevation is from the USGS 3D Elevation Program [11]; impervious fraction from the National Land Cover Database annual fractional impervious surface [12]; hydrography from NHDPlus High Resolution [13]; flood evidence from the New York City Department of Environmental Protection stormwater flood polygons [14], NYC 311 street-flooding complaints [15], and USGS Hurricane Ida high-water marks [16]; and a negative control from FEMA Sandy storm-surge inundation [17]. Version and download dates are recorded in a repository download manifest. Building footprints are used to compute building density. A distance-to-water proxy is derived from NHDPlus hydrography; because the Lower Manhattan hydrography is dominated by tidal rivers and shoreline features, this predictor is interpreted as shoreline/tidal-water distance rather than as inland drainage density. Table 1 lists the layers and their roles.

**Table 1. Open data layers and their roles in the framework.**

| Layer | Source | Form | Role |
|---|---|---|---|
| Elevation | USGS 3DEP | Raster | Elevation, slope, flow-accumulation proxy |
| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction, urban land-cover flag |
| Hydrography | USGS NHDPlus HR | Vector | Shoreline/tidal-water distance proxy |
| Building footprints | NYC MapHub | Vector | Building density |
| Flood evidence — stormwater | NYC DEP stormwater polygons (Flooding_Category 1–2) | Vector | Model-derived flood-evidence target (continuous and binary) |
| Flood evidence — complaints | NYC 311 street-flooding complaints (ArcGIS "streetfloodtime", 2010–2014) | Vector | Crowd-reported flood-evidence target (continuous and binary) |
| Flood evidence — observations | USGS Hurricane Ida high-water marks | Vector | Observed flood-evidence target (continuous and binary) |
| Negative control | FEMA Sandy surge inundation | Vector | Coastal-overlap diagnostic; never a training label |
| Rainfall condition r | Synthetic constant grid (75 mm/h) | Raster | Condition r; constant in the present pilots |

The cell-level flood-evidence score combines the available open sources. Polygon sources contribute an intersection area fraction (0–1); point sources contribute a per-cell presence indicator. The score is the maximum of the area fraction and the point-presence indicator, clipped to [0,1]. The binary flood-class target is then defined deterministically as flood_class = 1[flood_evidence_score ≥ 1e−9], so any cell with positive evidence is positive. Three properties of this target warrant emphasis. First, the three sources are not interchangeable measurements of one latent variable: the DEP polygons are hydrologic–hydraulic model outputs for two design rainfall classes, the 311 complaints are crowd-reported and unverified, and only the high-water marks are direct observations of an actual event (Ida, 2021). Second, the sources span different times and forcings and are therefore collapsed into a static, "has there ever been any evidence here" score rather than a per-event inundation label. Third, the score is not a severity measure: a cell with one complaint receives the same score as a cell with a verified high-water mark, because any point presence saturates the score at 1. The score is consequently treated as a flood-evidence screening target, not as flood risk, flood depth, or a calibrated probability. Each source is retained separately in the assembled table for auditability: the DEP polygons contribute `dep_area_frac` (split further into `dep_nuisance_frac` for category 1 and `dep_deep_frac` for category 2), the 311 complaints contribute `complaint_count`/`complaint_presence`, and the high-water marks contribute `ida_hwm_count`/`ida_hwm_presence`/`ida_hwm_quality`, with an `evidence_sources` string recording which sources are present per cell. The composite score is then constructed from these source-specific columns rather than from an undifferentiated merge, so the claim that the sources are kept distinct is true of the assembled table, not only of the documentation. NYC 311 records in particular reflect reporting and mapping processes, and their biases have been documented previously [7,8]. FloodNet is supported as an optional label source, but no usable FloodNet observations are included in the present analyses.

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

### 3.4 Spatial H3-block cross-validation

Each R9 cell is assigned to its R7 parent, two H3 resolution levels coarser, and five-fold GroupKFold partitions these R7 groups so that no R7 block appears in both the training and the held-out portion of a fold. This changes the generalisation target from "new randomly drawn cells" to "new spatial blocks", which is closer to the transfer a screening product would face. For each held-out cell the predicted class probability is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]—are computed from pooled out-of-fold predictions. H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons. The R7 block size is fixed a priori, and its relation to the target's spatial dependence structure was not tuned; block-size sensitivity is flagged as a limitation in Section 5.4.

### 3.5 Scale-loss diagnostics

Fine-resolution (R10) hotspot sets are defined by thresholding the open-evidence score at its 0.9 quantile and projected onto a coarser parent support; parent-aggregated (R9 and R8) hotspots are thresholded at the 0.9 quantile of the mean, maximum, and p90 rollups of the fine scores; the two sets are compared on that common parent support using Jaccard similarity and F1. The fine R10 reference is assembled by overlaying the raw polygon and point geometries directly onto R10 cells—not by inheriting scores from R9 parents—so that the coarse rollups are compared against a fine support that is independent of the aggregation being tested. The same diagnostics are additionally summarised through score distributions across resolutions and a pairwise hotspot-similarity matrix. These diagnostics use different labels, resolutions, and hotspot definitions from the Jaccard value reported by Svellingen et al. [5] and are not a reproduction of that result.

### 3.6 Adaptive refinement

After training, the full-fit positive-class model score screens R9 cells for refinement. A cell is selected when its score is at or above the 0.8 quantile of all cell scores, or when its predicted probability is uncertain (uncertainty 1 − 2|p − 0.5| of at least 0.7, i.e. p between 0.35 and 0.65); the selection is then expanded to include the one-ring H3 neighbourhood among the R9 cells. Each selected cell is replaced by its R11 descendants while unselected cells remain at R9. Model fitting precedes the refinement stage, which changes the spatial representation without altering the fitted R9 model. The reported metric is the resulting mixed-resolution cell count relative to a uniform R11 grid. This comparison quantifies representation size only; it does not by itself demonstrate computational efficiency, hotspot retention, or prediction quality, because the selection uses in-sample full-fit scores and the uniform fine reference is estimated from child counts rather than scored directly. These limitations are noted in Section 4.4 and Section 5.4.

### 3.7 Rainfall conditioning

The cell index is defined as

`PFI_h(c,r) = P̂(Y_c = 1 | X_c, r)`,

where Y_c is the binary flood label, X_c are the static predictors, and r is the rainfall condition, and P̂(·) is the classifier's positive-class score output. The classifier output is used directly without a separate calibration analysis and is therefore referred to as a model score rather than a calibrated probability. PFI_h is the fitted cell-level model output and is distinct from both feature-importance measures and PFIb. Because the pilot uses a constant synthetic rainfall input, rainfall has zero training variance and the fitted PFI_h(c,r) is invariant across the evaluated rainfall scenarios; the definition is retained for subsequent analyses with observed rainfall variation, but rainfall-conditioned discrimination is not claimed in the present study.

### 3.8 Negative control

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after evidence assembly and used as a negative control. Because the flood-evidence score combines polygon overlap and point presence, the pluvial grouping in the negative control is derived from the same composite flood_class definition used elsewhere, so that a cell carrying only a point label is counted as pluvial rather than misassigned to the "neither" group. The control reports the overlap between pluvial evidence and coastal inundation (the coastal-only fraction) and the difference in the **out-of-fold model score** between pluvial-only and coastal-only cells. The score compared is the held-out gradient-boosting score, never the target flood-evidence score, because a coastal-only cell has flood_class = 0 by construction and therefore a target score of 0 by definition; comparing target scores would be circular. Sandy labels are never used as training labels.

## 4. Results

### 4.1 Spatial pattern of evidence, predictions, and the full-fit score

On the 141-cell Lower Manhattan R9 support, the open-evidence scores, out-of-fold scores, and full-fit model score show related but distinct spatial patterns (Fig. 2). The evidence scores are bimodal by construction: cells with no positive evidence score 0, whereas positive evidence yields either a fractional polygon-overlap score or a point-presence score of 1 (median 1.0, mean 0.600). Fig. 3 shows how this composite surface decomposes into its source components: the DEP stormwater polygons and the 311 crowd reports occupy overlapping but not identical cell sets, and the composite score is the maximum over the source-specific layers. The Ida high-water marks contribute no cells within the Lower Manhattan extent—the USGS Ida points lie outside this narrow bounding box—so the Lower Manhattan composite is driven by the DEP and 311 sources alone (the expanded pilot includes 14 high-water-mark points across six cells). The out-of-fold scores are on average moderate (mean 0.69) and less dispersed, consistent with the modest pooled discrimination reported in Section 4.2 (ROC-AUC 0.741 and average precision 0.803 at 69.5% positive prevalence). The full-fit score has a mean of about 0.69 and shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.62), as expected when the same cells, features, and labels are refitted without the five-fold holdout structure. The full-fit surface is an in-sample fit and is not a validation result; predictive performance is assessed separately from the out-of-fold metrics reported in Section 4.2.

### 4.2 Spatial H3-block cross-validation

The smaller pilot contains 141 R9 cells distributed over seven R7 blocks. Five-fold spatial cross-validation yields accuracy 0.808 ± 0.085 and F1 0.864 ± 0.061 (Fig. 4); per-fold accuracy/F1 are Fold0 0.755 / 0.842, Fold1 0.840 / 0.882, Fold2 0.773 / 0.839, Fold3 0.714 / 0.786, and Fold4 0.958 / 0.970. Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). The held-out labels are positive in 69.5% of cells, and the model exceeds the always-positive baseline on both accuracy (0.808 vs 0.687) and F1 (0.864 vs 0.813); the always-negative baseline accuracy is 0.313. Pooled out-of-fold ROC-AUC is 0.741 and pooled average precision is 0.803, above the 0.695 positive-prevalence reference. The evidence-score R² is 0.079 ± 0.338 and is reported for completeness; it quantifies fit to the constructed evidence score rather than to any physical severity variable. Fold4 accuracy (0.958) coincides with a small test set (n = 24, two blocks) and is not interpreted in isolation. Table 3 summarises these numbers together with the expanded-pilot results.

**Table 3. Spatial H3-block cross-validation summary for the two pilots.** Accuracy, F1, evidence-score R², and MAE are fold means ± population SD across five held-out folds; ROC-AUC and average precision are pooled out-of-fold values. For the smaller pilot the positive class is the majority class (69.5%), so the always-positive classifier is also the majority baseline; for the expanded pilot the majority class is negative.

| Metric | Lower Manhattan (n = 141) | Expanded (n = 956) |
|---|---|---|
| Accuracy | 0.808 ± 0.085 | 0.824 ± 0.013 |
| F1 | 0.864 ± 0.061 | 0.832 ± 0.019 |
| Evidence-score R² | 0.079 ± 0.338 | 0.346 ± 0.138 |
| MAE | 0.326 ± 0.074 | 0.284 ± 0.033 |
| Pooled ROC-AUC | 0.741 | 0.875 |
| Pooled average precision | 0.803 | 0.822 |
| Always-positive accuracy | 0.687 | 0.497 |
| Always-positive F1 | 0.813 | 0.663 |
| Always-negative accuracy | 0.313 | 0.503 |
| Majority-class F1 | 0.813 (positive) | 0 (negative) |

Note: SD denotes the population standard deviation across the five held-out folds (ddof = 0); the fold-mean values in the first four rows are arithmetic means of the per-fold metrics.

### 4.3 Scale-loss Jaccard ladder

Fine-resolution hotspots are defined at R10 by thresholding at the 0.9 quantile and rolled up to R9 and R8 under mean, maximum, and p90 aggregation (Table 4). The R10 hotspot comprises 149 of 991 fine cells (15.0%), because the fine evidence score is tied at its maximum value in many cells and the 0.9 quantile coincides with that maximum (Section 3.5). Under mean aggregation the R9 rollup yields Jaccard 0.210 and F1 0.347, and the R8 rollup yields 0.167 and 0.286. Maximum and p90 aggregation retain more of the extreme signal (at R9, maximum yields 1.000/1.000 and p90 yields 0.543/0.704; at R8, maximum yields 1.000/1.000 and p90 yields 0.500/0.667), but their higher overlap does not imply an absence of scale loss. The mean-aggregation values show that the majority of the fine hotspot signal is not preserved when evidence is re-expressed on coarser supports.

Fig. 5 maps the R10 open-evidence score surface and its mean rollups to R9 and R8 on the same label-assembly footprint, providing a spatial view of the smoothing that accompanies coarsening. Fig. 6a summarises the same scale dependence through the score distributions: the R10 distribution is wide and bimodal, while the mean rollups at R9 and R8 are progressively compressed, and Fig. 6b summarises the pairwise cross-resolution Jaccard similarity among the three resolutions, reproducing the R10-vs-R9 (0.210) and R10-vs-R8 (0.167) ladder values. Table 4 quantifies sensitivity to the aggregation operator. Figures 5 and 6 hold mean aggregation fixed: Fig. 5 shows the spatial effect of coarsening, whereas Fig. 6 summarises the corresponding changes in score distribution and hotspot membership. These values use different labels, resolutions, and hotspot definitions from the PFIb Jaccard of 0.14 reported by Svellingen et al. [5] and are not interpreted as a reproduction of that value. Table 4 lists the full ladder.

**Table 4. Scale-loss ladder: hotspot Jaccard similarity and F1 between the R10 reference support and coarser representations under three aggregation rules** (0.9-quantile thresholds; the fine R10 hotspot comprises 149 of 991 cells).

| Coarse resolution | Aggregation | Jaccard | F1 |
|---|---|---|---|
| R8 | Mean | 0.167 | 0.286 |
| R8 | Maximum | 1.000 | 1.000 |
| R8 | P90 | 0.500 | 0.667 |
| R9 | Mean | 0.210 | 0.347 |
| R9 | Maximum | 1.000 | 1.000 |
| R9 | P90 | 0.543 | 0.704 |

Note: hotspot thresholds are empirical 0.9 quantiles of the natively assembled R10 scores; because many fine scores are tied at the maximum, the fine threshold coincides with that maximum and the R10 hotspot comprises every cell attaining it (149 of 991). The full ladder is plotted in Supplementary Fig. S1.

### 4.4 Adaptive versus fixed and uniform fine grids

The fixed coarse grid has 141 cells. Adaptive refinement selects 84 of 141 R9 cells and produces 4,173 mixed cells, compared with 6,909 cells for uniform R11 refinement (Supplementary Fig. S2). The adaptive grid therefore uses 60.4% as many cells as the uniform fine grid and 29.6 times as many cells as the fixed R9 baseline. This comparison quantifies representation size by cell count; runtime, memory use, hotspot retention, and city-scale computational cost were not evaluated, and the selection is based on in-sample full-fit scores. Table 5 lists the counts.

**Table 5. Adaptive refinement versus fixed and uniform fine grids by cell count** (Lower Manhattan pilot; adaptive = 29.6× fixed R9 = 60.4% of uniform R11; 84 of 141 R9 cells refined).

| Representation | Cell count |
|---|---|
| Fixed R9 | 141 |
| Adaptive R9/R11 | 4,173 |
| Uniform R11 | 6,909 |

### 4.5 Rainfall scenarios

The scenario loop covers the 141 cells at four intensities—moderate (25), heavy (40), Ida-like (75), and extreme (100 mm/h). The mean model score is about 0.69 for every scenario, and the within-cell range across scenarios is 0. Consequently, the fitted scenarios provide no rainfall-conditioned discrimination under the present training data. The flat response follows from constant training rainfall: every training cell carries the same synthetic value, so rainfall has zero training variance and contributes no learned variation to the fitted predictions. Evaluating rainfall responsiveness requires observed event rainfall with variation across intensities and model retraining.

### 4.6 Sandy negative control

Across the 141 cells, 31 intersect Sandy coastal inundation and 98 carry pluvial evidence (under the composite flood_class definition); 22 have both, and nine are coastal-only (6.4%). The control compares the out-of-fold model score across these groups rather than the target, because a coastal-only cell has flood_class = 0 and therefore a target score of 0 by definition; comparing target scores would be circular. The out-of-fold score averages 0.644 in coastal-only cells, 0.840 in pluvial-only cells, 0.771 in cells with both, and 0.323 in cells with neither, giving a pluvial−coastal out-of-fold score difference of 0.195. Among the 29 cells above the 0.8 score quantile, 3.4% are coastal-only and 75.9% carry pluvial evidence. The coastal-only cells therefore receive non-trivial out-of-fold scores, consistent with the model partially learning low-elevation, shoreline-proximal signal, but pluvial-only cells still score highest, so the model is not driven solely by coastal position. Coastal overlap is not a training label. Table 6 details the overlap and mean out-of-fold scores.

**Table 6. Sandy negative-control statistics on the 141-cell pilot.** The score comparison uses the out-of-fold model score (never the target flood-evidence score, which is 0 in coastal-only cells by construction). The pluvial−coastal difference is the mean out-of-fold score of pluvial-only cells minus that of coastal-only cells.

| Statistic | Value |
|---|---|
| Cells intersecting Sandy inundation | 31 of 141 |
| Cells with pluvial evidence | 98 of 141 |
| Both pluvial and coastal | 22 |
| Coastal-only | 9 (6.4%) |
| Pluvial-only | 76 (53.9%) |
| Neither | 34 (24.1%) |
| Mean out-of-fold model score, coastal-only cells | 0.644 |
| Mean out-of-fold model score, pluvial-only cells | 0.840 |
| Mean out-of-fold model score, both | 0.771 |
| Mean out-of-fold model score, neither | 0.323 |
| Pluvial − coastal out-of-fold score difference | 0.195 |
| Coastal-only among cells above 0.8 score quantile | 3.4% |
| Pluvial among cells above 0.8 score quantile | 75.9% |

### 4.7 Expanded open-data pilot

The expanded open-data pilot contains 956 cells over 28 blocks, with positive held-out labels in 49.7% of cells (475 of 956). Under the same H3-block protocol, spatial cross-validation accuracy is 0.824 ± 0.013 and F1 is 0.832 ± 0.019, both exceeding the fold-mean constant-class baselines (majority-negative accuracy 0.503; always-positive accuracy 0.497 and F1 0.663). Pooled out-of-fold ROC-AUC is 0.875 (fold-mean 0.878 ± 0.027) with average precision 0.822, well above the 0.497 prevalence reference; evidence-score R² is 0.346 ± 0.138 and MAE is 0.284 ± 0.033. Per-fold accuracy/F1 are Fold0 0.827 / 0.845, Fold1 0.848 / 0.857, Fold2 0.817 / 0.837, Fold3 0.821 / 0.805, and Fold4 0.808 / 0.816; the near-balanced per-fold class composition (positive test counts 82–108) yields a much tighter fold spread than the smaller pilot. The expanded pilot provides a within-Manhattan scale-up check rather than an independent external validation; citywide generalisation remains unevaluated.

## 5. Discussion

### 5.1 What the experiments establish

Taken together, the two pilots show two distinct roles of the H3 hierarchy. Spatial blocking changes the interpretation of predictive performance: the Lower Manhattan model exceeds the always-positive baseline on both accuracy and F1 (0.808 vs 0.687; 0.864 vs 0.813), and the expanded pilot exceeds both the majority-negative and always-positive baselines on accuracy (0.824 vs 0.503) and F1 (0.832 vs 0.663). Coarsening and selective refinement expose a separate trade-off in spatial representation: mean aggregation of the fine hotspot produces substantial hotspot-set disagreement under the specified projection-and-rethresholding protocol (Jaccard 0.210 to R9, 0.167 to R8), while adaptive refinement concentrates representation into 60% of a uniform fine grid without any claimed efficiency gain. Pooled out-of-fold ROC-AUC indicates moderate ranking discrimination in both pilots (0.741 and 0.875), with average precision 0.803 and 0.822; average precision is prevalence-dependent, so the two values are interpreted relative to their respective prevalence references (0.695 and 0.497) rather than compared to one another. Accordingly, the results support measurable ranking discrimination within the evaluated extents, but no citywide classification skill is claimed.

### 5.2 Relation to prior work

Svellingen et al. [5] use H3 to aggregate a proprietary building-level index for scalable communication, whereas the present framework learns from heterogeneous open evidence and evaluates predictions across held-out H3 spatial blocks. The R8 mean-aggregation Jaccard value of 0.167 is numerically close to their reported value of 0.14, but the two measures use different labels, resolutions, and aggregation procedures. The present ladder therefore characterises scale loss in the open-evidence analysis rather than reproducing their metric.

### 5.3 Methodological implications

Methodologically, the same H3 hierarchy links the spatial unit used for evidence assembly to the units used for cross-validation, scale analysis, and subsequent refinement, extending H3 from a post-prediction visualisation layer to the learning and evaluation architecture. The framework is reproducible in the sense that every number traces to public code and public data; but reproducibility of the pipeline is not the same as validity of the label semantics, and the two are kept distinct in the accompanying audit document.

### 5.4 Limitations

Several limitations constrain the interpretation of the results. The evidence is restricted to two sub-city Manhattan extents: Lower Manhattan (n = 141) and the expanded pilot (n = 956). The open evidence, particularly the 311 complaints, reflects reporting and mapping processes rather than complete ground-truth inundation [7,8], and the DEP stormwater layer is itself a hydrologic–hydraulic model output rather than an observation; only the high-water marks are direct observations. The H3 support follows rectangular bounding boxes rather than a strict Manhattan land footprint, so shoreline and water cells can shift prevalence and predictor distributions; the shoreline/tidal-water distance predictor is a tidal-water proxy rather than an inland drainage-density measure, and the urban land-cover flag is a deterministic copy of the impervious fraction. The terrain and flow-accumulation predictors are heuristic proxies computed on a georeferenced raster without hydrological conditioning, and the DEM interpolation and resolution are those of the underlying export service.

Evaluation is further constrained by class composition and the number of spatial blocks. The smaller pilot is 69.5% positive and distributes seven H3 blocks across five folds (per-fold test size 21–49, with some folds containing a single block); the expanded pilot uses 28 blocks with larger per-fold test sets. The R7 block size was fixed a priori without testing against the target's spatial dependence structure, so the results do not establish that blocking has fully controlled spatial autocorrelation. The evidence-score R² is 0.079 in the smaller pilot and 0.346 in the expanded pilot, and both values quantify fit to the constructed evidence score rather than to a physical severity variable. Adaptive refinement was selected with in-sample full-fit scores and compared only by cell count, so it demonstrates representation-size reduction but not computational efficiency or hotspot retention. The classifier output is not calibrated, and the model score is therefore not presented as a probability.

Rainfall conditioning remains unevaluated under observed forcing. The current input is a constant synthetic rainfall value rather than event-specific gauge or radar rainfall, giving a within-cell score range of 0 across scenarios. Primary performance interpretation therefore rests on spatial cross-validation, with random-split accuracy retained as a diagnostic comparison. The fold-level variation, including Fold4 on n = 24 in the smaller pilot, further limits inference from any single fold.

### 5.5 Outstanding steps

Future work should first replace the synthetic rainfall condition with documented event observations and test whether the fitted score varies across rainfall intensities for fixed static features. The same spatial cross-validation protocol can then be applied over broader, including citywide, extents and complemented by held-out FloodNet validation when a suitable sensor layer becomes available. Block-size sensitivity, calibration, and a source-level label sensitivity analysis (fitting separately to polygon-derived, complaint-derived, and observation-derived evidence) would further strengthen the construct validity of the target.

## 6. Conclusions

Using H3 as a common spatial support links open-evidence learning to spatially blocked validation, scale diagnostics, and selective refinement rather than treating the grid only as a post-processing layer. Across the two Manhattan pilots, the blocked evaluation and prevalence-aware baselines change the interpretation of classification performance, and selective refinement links resolution control to the fitted cell scores without requiring uniform fine-grid representation. The evidence remains limited to the evaluated pilot extents; observed event rainfall, rainfall-responsive predictions, citywide evaluation, block-size sensitivity, and FloodNet validation remain priorities for further assessment.

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

**Figure 2. Spatial results for the Lower Manhattan pilot (n = 141 R9 cells).** (a) Open-evidence flood score; (b) pooled out-of-fold gradient-boosting score under H3-block spatial cross-validation; (c) full-fit model score at the synthetic Ida-like condition r = 75 mm/h, fitted using all 141 cells. The surface is invariant across the evaluated scenarios because the training rainfall is constant (Section 4.5). Panel (c) is an in-sample fit, not a validation result. Hexagons are coloured by value on a common 0–1 scale; grey shading is the DEM relief and light-blue lines/polygons are NHDPlus shoreline and water features.

**Figure 3. Source-specific open-evidence maps for the Lower Manhattan pilot (n = 141 R9 cells).** The composite flood-evidence score (d) is the maximum over the source-specific layers retained as separate columns in the assembled table: (a) DEP stormwater polygon area fraction (categories 1–2), (b) 311 crowd-report count, and (c) USGS Ida high-water-mark count. Panel (a) and (d) share a 0–1 continuous scale; (b) and (c) use count scales. No Ida high-water marks fall within this extent, so panel (c) is empty by data availability rather than by processing choice. Hexagons are coloured by value; grey shading is the DEM relief and light-blue lines/polygons are NHDPlus shoreline and water features.

**Figure 4. Spatial H3-block cross-validation performance for the Lower Manhattan pilot.** Classification accuracy and F1 are shown as paired markers for each of five held-out folds formed from seven R7 H3 blocks (n = 141 cells); a final x-position shows the fold mean ± SD with error bars. Three horizontal reference lines mark the constant-class baselines: the blue dashed line is the always-positive accuracy, the red dashed line is the always-positive F1, and the grey dotted line is the always-negative accuracy. Per-fold test size and positive prevalence are annotated below each marker.

**Figure 5. Multi-resolution open-evidence score surface on the label-assembly footprint.** (a) R10 open-evidence flood score (n = 991); (b) mean rollup to R9 (n = 160); and (c) mean rollup to R8 (n = 31). All panels use the same map extent and derive from the same natively assembled R10 label-assembly footprint, with a common 0–1 colour scale that makes the smoothing accompanying coarsening visible directly. Figure 6 summarises cross-resolution hotspot similarity, while Table 4 quantifies sensitivity to the aggregation rule.

**Figure 6. Resolution effects on the open-evidence score surface.** (a) Violin plots with overlaid cell scores of the distribution at R10 (n = 991), R9 (n = 160, mean rollup), and R8 (n = 31, mean rollup), showing variance compression as the grid coarsens; internal bars mark the mean and extrema, and the distributions are descriptive summaries of the assembled scores. (b) Cross-resolution hotspot Jaccard similarity matrix (0.9-quantile thresholds) between hotspot sets at R10, R9, and R8, computed on the coarser support of each pair so the R10-vs-R9 and R10-vs-R8 entries reproduce the ladder in Table 4. The R10 label-assembly footprint contains 991 cells and aggregates to 160 R9 and 31 R8 parents, distinct from the 141-cell R9 supervised modelling table in Sections 4.1–4.2. For the realised hotspot sets, the R10-vs-R8 comparison yields Jaccard similarity 0.167.

**Supplementary Figure S1. Open-evidence hotspot scale-loss diagnostics across H3 resolutions.** Jaccard similarity and F1 compare hotspot sets defined on the reference fine support, H3 R10 (0.9-quantile threshold), with R9 and R8 representations under mean, maximum, and p90 aggregation. This figure reproduces the numeric ladder reported in Table 4.

**Supplementary Figure S2. Adaptive refinement versus uniform fine grids by cell count.** Fixed R9 (141), adaptive mixed R9/R11 (4,173), and uniform R11 (6,909) representations are compared for the Lower Manhattan pilot (adaptive = 29.6× fixed R9 = 60.4% of uniform R11; 84 of 141 R9 cells refined). The comparison is of representation size only; it does not measure runtime, memory, or hotspot retention, and is reported as a table (Table 5) in the main text.

---

## Data and code availability

The public repository (code, configs, tests, paper documentation, and small summary tables; large rasters, geojson, trained model binaries, and large parquet files are excluded) is available at https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3. The submission version is archived under the immutable tag `submission-v2`; the corresponding commit and provenance of all reported outputs are recorded in the accompanying audit document. Each raw layer is mapped in the repository download manifest to its source URL, retrieval date, and license. Analyses used scikit-learn 1.8.0 and H3 4.4.2 (exact versions are recorded in the run metadata). Synthetic demonstrations are excluded from scientific evidence. A process-oriented research report and a data-authenticity audit document accompany the manuscript in the same documentation folder.

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the authors used ChatGPT (OpenAI) as an editorial reviewer to review manuscript language, organization, and the presentation of scientific framing. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.

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

[15] New York City Department of Environmental Protection, 311 street-flooding complaint layer (ArcGIS "streetfloodtime"; records 2010–2014), accessed August 2026. https://www.arcgis.com/home/item.html?id=33c5b455415a41788a736155affcb31c

[16] U.S. Geological Survey, Hurricane Ida high-water marks, data release, accessed August 2026. https://doi.org/10.5066/P9OMBJPQ

[17] Federal Emergency Management Agency / New York City Open Data, Hurricane Sandy storm surge inundation (uyj8-7rv5), accessed August 2026. https://data.cityofnewyork.us/api/geospatial/uyj8-7rv5

[18] T. Saito, M. Rehmsmeier, The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets, PLOS ONE 10 (2015) e0118432. https://doi.org/10.1371/journal.pone.0118432
