# Spatially blocked pluvial flood learning on the H3 grid: open labels, adaptive refinement, and a rainfall-conditioned cell index

## Highlights

- A hierarchical hexagonal grid unifies learning, validation and refinement
- Public flood observations support reproducible pluvial-flood screening
- Class-prevalence baselines change interpretation of classification performance
- Adaptive refinement uses 57% as many cells as uniform fine-grid refinement
- Constant synthetic rainfall yields no rainfall-conditioned discrimination

---

## Abstract

Extreme rainfall increasingly overwhelms urban drainage and produces pluvial flooding with limited warning, and city-scale screening depends on representations that are computationally scalable, updateable, and evaluated with explicit control for spatial dependence. Many data-driven susceptibility methods rely on proprietary damage or insurance labels, and random train-test splits can inflate skill when spatial dependence is ignored. This study demonstrates an open-label machine-learning framework in which the H3 discrete global grid provides a common spatial support for label assembly, supervised learning, geographically blocked evaluation, scale diagnostics, and selective refinement. Multi-source public flood observations are joined to H3 cells, a gradient-boosting classifier and a continuous-risk regressor are fitted, and performance is assessed with H3-block spatial cross-validation that withholds entire parent cells. On a small Manhattan pilot (n = 141, 80% positive), spatial cross-validation accuracy is 0.784 ± 0.069 and F1 is 0.866, below the always-positive baseline (0.808 and 0.893); pooled out-of-fold ROC-AUC is 0.68 and average precision is 0.86. On a larger pilot (n = 956, 47.9% positive), accuracy is 0.642 ± 0.148, exceeding the constant majority-class baseline (0.521), with continuous-risk R² of 0.525 ± 0.112 and out-of-fold ROC-AUC of 0.70. Selective refinement uses about 57% as many cells as uniform R11 refinement. The framework formalizes the model output as a rainfall-conditioned cell index PFI_h(c,r); because the pilots use a constant synthetic rainfall input, the results establish the learning and evaluation architecture but not citywide skill or rainfall-conditioned discrimination.

**Keywords:** pluvial flood; H3; discrete global grid; spatial cross-validation; machine learning; flood susceptibility.

---

## 1. Introduction

Urban flooding occurs predominantly during intense rainfall in densely built areas with limited drainage, and the pluvial form—flooding that develops when rainfall overwhelms drainage before entering watercourses—can appear rapidly and with little warning [1]. Assessing this hazard at city scale requires representations that are computationally scalable, updateable as new observations arrive, and evaluated in a way that does not inflate performance. Two limitations recur in data-driven pluvial-flood screening. The first is that some data-driven pluvial-flood indices rely on proprietary damage or insurance records, so the underlying labels are neither public nor transferable to jurisdictions without comparable records. The second is evaluation: random train-test splits can overestimate generalisation when spatially proximate observations occur in both the training and test sets because of spatial autocorrelation.

Discrete Global Grid Systems, and the hexagonal H3 system in particular [2], provide a scalable spatial substrate for integrating observations, predictions, and multi-resolution analysis. H3 is a hierarchical, predominantly hexagonal spatial index with neighbourhood operations and parent–child relationships across resolutions [3]. Hexagonal DGGS have been applied to multi-scale flood mapping under climate scenarios [4], and a closely related line of work aggregates a pre-existing machine-learning building-level pluvial susceptibility index into H3 cells to reduce query cost and expose resolution-dependent hotspot loss [5,6]. That work uses H3 chiefly as a multi-resolution aggregation and communication substrate for an inherited index; it does not learn directly on the grid, nor does it evaluate how well predictions transfer to unseen spatial blocks.

The present study addresses these two issues by combining public flood observations with spatially blocked evaluation on a common H3 support. Public flood observations are assembled onto H3 cells and used as labels; a model is fitted on those cells; evaluation is performed by spatial cross-validation that withholds entire coarse H3 parent blocks; and the trained scores are then used to select which cells to refine. The contribution is therefore not the individual use of H3, machine learning, open flood observations, or spatial cross-validation—each is established separately in prior work [4,7,8,9,10]—but their integration into a single H3-native framework in which the same hierarchical grid supports label assembly, geographically blocked evaluation, scale diagnostics, and selective refinement. Throughout, PFI_h(c,r) denotes the fitted model's rainfall-conditioned flood-probability output for a cell; it is a model output, not a feature-importance measure, and it is distinct from the H3-aggregated building index of Svellingen et al. [5].

The study is organised around three questions. (i) Does performance persist when entire H3 parent blocks are withheld, relative to the trivial baselines implied by class prevalence? (ii) How much hotspot membership is lost when fine-scale labels are aggregated to coarser H3 resolutions, and can trained cell scores be used to concentrate fine-resolution representation where it matters most? (iii) Can the fitted cell-level output be formalised to accommodate rainfall conditioning in future runs with observed rainfall variation? Two Manhattan pilots—one small and one expanded—are used to demonstrate the framework; both are pilot extents, not a citywide analysis.

## 2. Study area and data

**Extent.** Two Manhattan pilot extents are used. The smaller is a Lower Manhattan bounding box (approximately 74.02–73.97°W, 40.70–40.76°N); the larger expanded-Manhattan box spans approximately 74.03–73.94°W, 40.68–40.80°N. Both lie within New York City and are described as pilot extents throughout.

**Data sources.** All layers are open and were downloaded in August 2026. Elevation is from the USGS 3D Elevation Program [11]; impervious fraction from the National Land Cover Database [12]; hydrography from NHDPlus High Resolution [13]; flood labels from the New York City Department of Environmental Protection stormwater flood polygons [14], NYC 311 flooding service requests [15], and USGS Hurricane Ida high-water marks [16]; and a negative control from FEMA Sandy storm-surge inundation [17]. Version and download dates are recorded in a repository download manifest. Building footprints are used to compute building density. A distance-to-water proxy is derived from NHDPlus hydrography in a tidal and shoreline setting. Table 1 lists the layers and their roles.

**Table 1. Open data layers and their roles in the framework.**

| Layer | Source | Form | Role |
|---|---|---|---|
| Elevation | USGS 3DEP | Raster | Elevation, slope, flow-accumulation proxy |
| Impervious surface | NLCD fractional impervious | Raster | Impervious fraction, urban land-cover flag |
| Hydrography | USGS NHDPlus HR | Vector | Distance-to-water proxy |
| Building footprints | NYC MapHub | Vector | Building density |
| Flood observations | NYC DEP stormwater, NYC 311, USGS Ida HWM | Vector | Flood-risk target (continuous and binary) |
| Negative control | FEMA Sandy surge inundation | Vector | Coastal-overlap diagnostic; never a training label |
| Rainfall condition r | Synthetic constant grid (75 mm/h) | Raster | Condition r; constant in the present pilots |

**What the labels mean.** The continuous flood-risk target is assembled per cell from open observations. Polygon sources contribute an intersection area fraction (0–1); point sources contribute a per-cell count. The risk score is the maximum of the area fraction and the point-presence indicator, clipped to [0,1]. The binary flood-class target is then defined deterministically as flood_class = 1[flood_risk ≥ 1e−9], so any cell with positive flood evidence is positive. These are observed flood labels, not verified inundation ground truth: NYC 311 records in particular reflect reporting and mapping processes, and their biases have been documented previously [7,8]. FloodNet is supported as an optional label source, but no usable FloodNet observations are included in the present analyses.

**Rainfall.** Rainfall is represented as a separate condition r (rainfall intensity). The pilot rainfall is a constant synthetic input representing an Ida-like scenario (75 mm/h), not radar or gauge data; this choice is deliberate and is reported as a limitation in Section 5.

## 3. Methods

### 3.1 H3 representation

Supervised modelling uses H3 resolution 9 (R9) as the training and evaluation support. Resolution 10 (R10) is used only to assemble fine labels for the scale-loss diagnostic, which rolls hotspots to parent resolutions R9 and R8; R10 and R8 never participate in training. Adaptive refinement is a post-training step that replaces selected R9 cells with their resolution-11 (R11) descendants. All H3 indexing and spatial joins use longitude–latitude coordinates (EPSG:4326). Metric quantities are computed on this support: cell areas use H3 native cell-area calculations, distance-to-water uses a great-circle (haversine) distance, and the terrain derivatives are computed on the raster grid and averaged zonally over each cell. The workflow is summarised in Fig. 1.

### 3.2 Features

Static predictors are elevation, slope, a flow-accumulation proxy (D8-derived from the digital elevation model), impervious fraction (NLCD), an urban land-cover flag, building density, and distance-to-water (a shoreline/tidal-water proxy). Elevation, slope, and the flow-accumulation proxy are zonal means over each cell derived from the digital elevation model; impervious fraction is a zonal mean of the NLCD fractional-impervious surface; building density is the building-centroid count divided by cell area; distance-to-water is the great-circle distance from the cell centre to the nearest NHDPlus hydrographic feature; the urban land-cover flag marks cells whose impervious fraction exceeds 0.45. Rainfall is handled separately as the condition r rather than as a static feature.

### 3.3 Models and baselines

The primary learner is a gradient-boosting classifier and a continuous-risk gradient-boosting regressor, each with 80 estimators, maximum depth 4, and learning rate 0.08, fitted on features standardised within each training fold, with a fixed random seed (42); all other estimator parameters retain the scikit-learn 1.8 defaults. Two constant classifiers—always-positive and always-negative—are computed on each held-out fold, and accuracy and F1 are reported alongside these constant classifiers to provide a class-prevalence reference. The majority-class identity is determined from pooled target counts, and the constant-baseline accuracy and F1 use the same fold-wise aggregation as the model metrics. Two further baselines are included for diagnostic comparison: an L2-regularised logistic classifier and a ponding rule defined by the weighted combination

\[
0.40\cdot(1-\mathrm{elev}_{\mathrm{norm}}) + 0.35\cdot\mathrm{imperv} + 0.15\cdot(1-\min(\mathrm{slope},15^\circ)/15^\circ) + 0.10\cdot\mathrm{TWI}_{\mathrm{norm}},
\]

where elev_norm and TWI_norm are min–max normalised elevation and a topographic-wetness proxy, and a cell is classified positive when the score is at least 0.5. In-sample metrics are treated as optimistic references only. Table 2 summarises the models and baselines.

**Table 2. Model and baseline specifications.**

| Model / baseline | Configuration | Role |
|---|---|---|
| Gradient-boosting classifier | 80 estimators, max depth 4, learning rate 0.08, features standardised within each training fold, random seed 42 | Primary binary learner |
| Gradient-boosting regressor | Same configuration | Continuous-risk learner |
| L2-regularised logistic classifier | scikit-learn 1.8 defaults | Diagnostic baseline |
| Ponding rule | Weighted combination of normalised elevation, impervious fraction, slope, and TWI; positive when score ≥ 0.5 | Diagnostic baseline |
| Always-positive / always-negative | Constant class prediction | Prevalence-aware baselines on each held-out fold |

### 3.4 Spatial H3-block cross-validation

Each R9 cell is assigned to its R7 parent, two H3 resolution levels coarser, and five-fold GroupKFold partitions these R7 groups so that no R7 block appears in both the training and the held-out portion of a fold. This changes the generalisation target from "new randomly drawn cells" to "new spatial blocks", which is closer to the transfer a screening product would face. For each held-out cell the predicted class probability is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP), computed as the recall-weighted mean of precision across score thresholds [18]—are computed from pooled out-of-fold predictions. H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons.

### 3.5 Scale-loss diagnostics

Fine-resolution (R10) hotspot sets are defined by thresholding the open-label score at its 0.9 quantile and projected onto a coarser parent support; parent-aggregated (R9 and R8) hotspots are thresholded at the 0.9 quantile of the mean, maximum, and p90 rollups of the fine scores; the two sets are compared on that common parent support using Jaccard similarity and F1. The same diagnostics are additionally summarised through score distributions across resolutions and a pairwise hotspot-similarity matrix. Because many R10 open-label scores are tied at the maximum value, the 0.9-quantile threshold coincides with that maximum and the fine hotspot comprises every cell attaining it; the resulting counts are reported in Section 4.3. These diagnostics use different labels, resolutions, and hotspot definitions from the Jaccard value reported by Svellingen et al. [5] and are not a reproduction of that result.

### 3.6 Adaptive refinement

After training, the full-fit PFI_h probability screens R9 cells for refinement. A cell is selected when its PFI_h is at or above the 0.8 quantile of all cell scores, or when its predicted probability is uncertain (uncertainty 1 − 2|p − 0.5| of at least 0.7, i.e. p between 0.35 and 0.65); the selection is then expanded to include the one-ring H3 neighbourhood among the R9 cells. Each selected cell is replaced by its R11 descendants while unselected cells remain at R9. Refinement changes only the spatial representation; no R11 model is retrained. The primary metric is the resulting mixed-resolution cell count relative to a uniform R11 grid.

### 3.7 Rainfall-conditioned index

The cell index is defined as

\[
\mathrm{PFI}_h(c,r)=\widehat{P}(Y_c=1\mid X_c,r),
\]

where Y_c is the binary flood label, X_c are the static predictors, and r is the rainfall condition, and \(\widehat{P}(\cdot)\) is the classifier's positive-class probability output. No probability-calibration claim is made unless calibration is evaluated separately. The index is a model output, not a SHAP or permutation importance, and not PFIb. Because the pilot uses a constant synthetic rainfall input, rainfall has zero training variance and the fitted PFI_h(c,r) is invariant across the evaluated rainfall scenarios; the definition is retained for subsequent analyses with observed rainfall variation.

### 3.8 Negative control

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection. It is attached only after label assembly and used as a negative control that reports the overlap between pluvial evidence and coastal inundation (the coastal-only fraction) and the difference in mean observed flood-risk score between pluvial-only and coastal-only cells; Sandy labels are never used as training labels.

## 4. Results

### 4.1 Spatial pattern of labels, predictions, and the full-fit index

Fig. 2 maps the three quantities the framework produces on the 141-cell Lower Manhattan support at R9: the observed open-label score, the pooled out-of-fold probability of the gradient-boosting classifier, and the full-fit index PFI_h(c, r). The observed scores are bimodal by construction: cells with no positive flood evidence score 0, whereas positive evidence yields either a fractional polygon-overlap score or a point-presence score of 1 (median 1.0, mean 0.605; 84 of 141 cells at or above 0.8). The out-of-fold probabilities are on average high (mean 0.798) and less dispersed, consistent with the modest pooled discrimination reported in Section 4.2 (ROC-AUC 0.68 and average precision 0.86 at 80% positive prevalence). The full-fit index has a mean of 0.803 and shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.51), as expected when the same cells, features, and labels are refitted without the five-fold holdout structure. This correlation is a descriptive measure of spatial concordance between the assembled surfaces; predictive performance is evaluated from the out-of-fold metrics reported in Section 4.2. The maps provide a qualitative comparison of the assembled surfaces; quantitative predictive performance is reported in Section 4.2.

### 4.2 Spatial H3-block cross-validation

The smaller pilot contains 141 R9 cells distributed over seven R7 blocks. Five-fold spatial cross-validation yields accuracy 0.784 ± 0.069 and F1 0.866 ± 0.044 (Fig. 3); per-fold accuracy/F1 are Fold0 0.755 / 0.850, Fold1 0.760 / 0.850, Fold2 0.773 / 0.872, Fold3 0.714 / 0.813, and Fold4 0.917 / 0.944. Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). The held-out labels are highly imbalanced (80.1% positive), and a trivial always-positive classifier reaches mean accuracy 0.808 and mean F1 0.893 across the same folds—above the model's 0.784 and 0.866. The always-negative baseline accuracy is 0.192. Pooled out-of-fold ROC-AUC is 0.683, indicating modest ranking discrimination, and pooled average precision is 0.861, only slightly above the 0.801 positive-prevalence baseline. Continuous-risk R² is 0.030 ± 0.343 and is reported for completeness. Fold4 accuracy (0.917) coincides with a small test set (n = 24, two blocks) and is not interpreted in isolation. Table 3 summarises these numbers together with the expanded-pilot results.

**Table 3. Spatial H3-block cross-validation summary for the two pilots.** Accuracy, F1, R², and MAE are fold means ± population SD across five held-out folds; ROC-AUC and average precision are pooled out-of-fold values. For the smaller pilot the positive class is the majority class (80.1%), so the always-positive classifier is also the majority baseline; for the expanded pilot the majority class is negative.

| Metric | Lower Manhattan (n = 141) | Expanded (n = 956) |
|---|---|---|
| Accuracy | 0.784 ± 0.069 | 0.642 ± 0.148 |
| F1 | 0.866 ± 0.044 | 0.608 ± 0.185 |
| Continuous-risk R² | 0.030 ± 0.343 | 0.525 ± 0.112 |
| MAE | 0.332 ± 0.074 | 0.112 ± 0.060 |
| Pooled ROC-AUC | 0.683 | 0.703 |
| Pooled average precision | 0.861 | 0.723 |
| Always-positive accuracy | 0.808 | 0.479 |
| Always-positive F1 | 0.893 | 0.641 |
| Always-negative accuracy | 0.192 | 0.521 |
| Majority-class F1 | 0.893 (positive) | 0 (negative) |

Note: SD denotes the population standard deviation across the five held-out folds (ddof = 0); the fold-mean values in the first four rows are arithmetic means of the per-fold metrics.

### 4.3 Scale-loss Jaccard ladder

Fine-resolution hotspots are defined at R10 by thresholding at the 0.9 quantile and rolled up to R9 and R8 under mean, maximum, and p90 aggregation (Fig. 4). The R10 hotspot comprises 571 of 991 fine cells because many fine open-label scores are tied at the maximum value, so the 0.9 quantile coincides with that maximum (Section 3.5). Under mean aggregation the R8 rollup yields Jaccard 0.167 and F1 0.286, whereas the R9 rollup yields 0.977 and 0.988. At R8, maximum and p90 aggregation both yield Jaccard/F1 of 1.000/1.000; at R9, maximum yields 1.000/1.000 whereas p90 yields 0.977/0.988. Maximum and p90 aggregation therefore retain more of the extreme signal than mean aggregation, but their higher overlap does not imply an absence of scale loss.

Fig. 5a shows the same scale dependence as score compression: the R10 distribution is wide and bimodal, while the mean rollups at R9 and R8 are progressively compressed, and Fig. 5b summarises the pairwise cross-resolution Jaccard similarity among the three resolutions, reproducing the R10-vs-R9 (0.977) and R10-vs-R8 (0.167) ladder values. Fig. 4 therefore examines sensitivity to the aggregation operator, whereas Fig. 5 holds mean aggregation fixed to isolate resolution-dependent changes in score distribution and hotspot membership. These values use different labels, resolutions, and hotspot definitions from the PFIb Jaccard of 0.14 reported by Svellingen et al. [5] and are not interpreted as a reproduction of that value. Table 4 lists the full ladder.

**Table 4. Scale-loss ladder: hotspot Jaccard similarity and F1 between the R10 reference support and coarser representations under three aggregation rules** (0.9-quantile thresholds; the fine R10 hotspot comprises 571 of 991 cells).

| Coarse resolution | Aggregation | Jaccard | F1 |
|---|---|---|---|
| R8 | Mean | 0.167 | 0.286 |
| R8 | Maximum | 1.000 | 1.000 |
| R8 | P90 | 1.000 | 1.000 |
| R9 | Mean | 0.977 | 0.988 |
| R9 | Maximum | 1.000 | 1.000 |
| R9 | P90 | 0.977 | 0.988 |

Note: hotspot thresholds are empirical 0.9 quantiles of the assembled R10 scores; because many fine scores are tied at the maximum, the fine threshold coincides with that maximum and the R10 hotspot comprises every cell attaining it (571 of 991).

### 4.4 Adaptive versus fixed and uniform fine grids

The fixed coarse grid has 141 cells. Adaptive refinement selects 79 of 141 R9 cells and produces 3,933 mixed cells, compared with 6,909 cells for uniform R11 refinement (Fig. 6). The adaptive grid therefore uses 56.9% as many cells as the uniform fine grid and 27.9 times as many cells as the fixed R9 baseline. This ablation measures representation size by cell count; runtime, memory use, and city-scale computational cost are outside the reported metrics. Table 5 lists the counts.

**Table 5. Adaptive refinement versus fixed and uniform fine grids by cell count** (Lower Manhattan pilot; adaptive = 27.9× fixed R9 = 56.9% of uniform R11; 79 of 141 R9 cells refined).

| Representation | Cell count |
|---|---|
| Fixed R9 | 141 |
| Adaptive R9/R11 | 3,933 |
| Uniform R11 | 6,909 |

### 4.5 Rainfall scenarios

The scenario loop covers the 141 cells at four intensities—moderate (25), heavy (40), Ida-like (75), and extreme (100 mm/h). The mean PFI_h is about 0.803 for every scenario, and the within-cell range across scenarios is 0. The present pilot therefore does not demonstrate rainfall-conditioned discrimination. The flat response follows from constant training rainfall: every training cell carries the same synthetic value, so rainfall has zero training variance and contributes no learned variation to the fitted predictions. Evaluating rainfall responsiveness requires observed event rainfall with variation across intensities and model retraining.

### 4.6 Sandy negative control

Across the 141 cells, 31 intersect Sandy coastal inundation, 71 have pluvial evidence, and 23 have both; 8 cells are coastal-only (≈5.7%), and the mean observed flood-risk score is ≈0.120 higher in pluvial-only than in coastal-only cells. Coastal overlap is not a training label. Table 6 details the overlap and mean scores.

**Table 6. Sandy negative-control statistics on the 141-cell pilot.** The pluvial−coastal score difference is the mean observed flood-risk score of pluvial-only cells minus that of coastal-only cells.

| Statistic | Value |
|---|---|
| Cells intersecting Sandy inundation | 31 of 141 |
| Cells with pluvial evidence | 71 of 141 |
| Both pluvial and coastal | 23 |
| Coastal-only | 8 (5.7%) |
| Pluvial-only | 48 (34.0%) |
| Neither | 62 (44.0%) |
| Mean flood-risk score, coastal-only cells | 0.500 |
| Mean flood-risk score, pluvial-only cells | 0.620 |
| Mean flood-risk score, both | 0.590 |
| Mean flood-risk score, neither | 0.613 |
| Pluvial − coastal mean score difference | 0.120 |

### 4.7 Expanded open-data pilot

The expanded extent is a second, larger open-data pilot: 956 cells over 28 blocks, still not citywide, with near-even held-out labels (47.9% positive). Under the same H3-block protocol, spatial cross-validation accuracy is 0.642 ± 0.148, exceeding both the always-positive baseline (0.479) and the constant majority-class baseline (0.521, here the negative class); F1 is 0.608, below the fold-mean always-positive F1 of 0.641. Continuous-risk R² is 0.525 ± 0.112, MAE is 0.112, and pooled out-of-fold ROC-AUC is 0.703 with average precision 0.723, above the 0.479 prevalence baseline (Table 3). Per-fold accuracy/F1 are Fold0 0.801 / 0.832, Fold1 0.419 / 0.442, Fold2 0.759 / 0.736, Fold3 0.516 / 0.343, and Fold4 0.715 / 0.689. The per-fold spread coincides with heterogeneous held-out class composition—Fold1 and Fold3 are majority-negative, Fold0 and Fold4 majority-positive, and Fold2 nearly balanced (97/94)—and is not attributed to prevalence without further analysis. The expanded pilot provides a robustness check within Manhattan; citywide generalisation remains unevaluated.

## 5. Discussion

### 5.1 What the experiments establish

The two pilots show that the framework supports spatially blocked evaluation, reveals scale-dependent changes in hotspot membership under mean aggregation, and reduces fine-grid cell count through trained-score refinement. The spatial maps in Fig. 2 put these numbers in context: the observed labels are bimodal by construction, the model probabilities are high on average and less dispersed, and the full-fit index shows moderate spatial concordance with the cross-validated surface. Validation is based on the out-of-fold metrics. On classification the pilots differ: the smaller table does not beat its constant-class baselines on accuracy or F1, whereas the expanded table beats the constant majority-class baseline on accuracy (0.642 versus 0.521) but not on F1 against the always-positive comparator (0.608 versus 0.641). Pooled out-of-fold ROC-AUC indicates modest-to-moderate ranking discrimination in both pilots (0.68 and 0.70), and average precision is 0.86 and 0.72 respectively; because average precision is prevalence-dependent, the higher value in the smaller pilot is interpreted relative to its higher prevalence baseline. Accordingly, the results support measurable ranking discrimination but not strong thresholded classification, and no citywide classification skill is claimed.

### 5.2 Relation to prior work

The comparison with Svellingen et al. [5] is conceptual rather than numerical. They aggregate a proprietary building index into H3 for scalable communication; this study learns on public labels with spatial holdouts and defines an independent rainfall-conditioned H3 model output. Although the R8 mean-aggregation Jaccard value (0.167) is numerically close to the value they report (0.14), the two quantities arise from different labels, resolutions, and aggregation procedures and should not be equated. The present Jaccard ladder is a diagnostic of scale loss on open labels, not an estimate of the same quantity.

### 5.3 Methodological implications

The main methodological point is that a single hierarchical grid can serve four roles at once: the support on which labels are assembled, the grouping hierarchy for blocked cross-validation, the scale hierarchy for scale-loss diagnostics, and the refinement hierarchy for selective re-discretisation. Using the same hierarchy for these four operations extends H3 from a post-prediction visualisation layer to the learning and evaluation architecture. The spatial cross-validation design is deliberately conservative, but one caveat applies: the R7 block size is fixed a priori; its relation to the target's spatial autocorrelation range was not evaluated, so block-size sensitivity remains a limitation.

### 5.4 Limitations

1. **Spatial extent.** Results use two Manhattan pilots—Lower Manhattan (n = 141) and an expanded extent (n = 956)—both of which are sub-city Manhattan extents.
2. **Label bias.** 311 and related open indicators reflect reporting and mapping processes, not complete ground-truth inundation [7,8].
3. **Hydrographic proxy.** Distance-to-water from NHDPlus in a tidal and shoreline setting is a proxy, not inland drainage density.
4. **Rainfall provenance.** The present analysis uses constant synthetic rainfall rather than event-specific gauge or radar rainfall.
5. **Flat rainfall response.** The within-cell range of PFI_h across rainfall scenarios is currently 0; rainfall-conditioned discrimination is not demonstrated.
6. **Class imbalance and discrimination.** The smaller pilot is highly imbalanced (80% positive) and falls below the always-positive baseline; the expanded pilot beats the majority-class baseline on accuracy but not on F1 against the always-positive comparator.
7. **Small blocked design.** The smaller pilot distributes seven H3 blocks over five folds (per-fold test 21–49, some folds a single block); the expanded pilot uses 28 blocks (per-fold test 190–193), which is more defensible but still limited and non-citywide.
8. **Continuous skill.** Spatial cross-validation R² is near zero in the smaller pilot (0.030) and moderate in the expanded pilot (0.525); the R² values are interpreted within their respective pilot extents.
9. **Held-out sensors.** FloodNet validation is unavailable because no usable FloodNet observations are included.

Primary performance claims are based on spatial cross-validation; random-split accuracy is retained as a diagnostic comparison. Fold-level variance (including Fold4 on n = 24 in the smaller pilot) further cautions against over-interpreting a single pilot run.

### 5.5 Outstanding steps

Future work should (i) ingest observed event rainfall with documented provenance; (ii) evaluate whether PFI_h(c,r) varies across observed rainfall intensities for fixed static features; (iii) extend evaluation to broader spatial extents, including citywide coverage, under the same spatial cross-validation protocol; and (iv) perform held-out FloodNet validation when a suitable sensor layer is available.

## 6. Conclusions

This study shows that H3 can serve not only as an aggregation grid but as a common spatial support for open-label learning, spatially blocked validation, scale diagnostics, and selective refinement in pluvial-flood screening. The experiments demonstrate implementation and evaluation of the framework on two Manhattan pilots and show that blocked evaluation and prevalence-aware baselines materially change how classification performance should be interpreted; the evidence is limited to the two Manhattan pilot extents. The results indicate that a single hierarchical grid can link model evaluation and resolution control without requiring uniform fine-grid representation. Observed event rainfall, a non-degenerate rainfall response, a full citywide extent, and FloodNet validation remain to be addressed.

---

## CRediT authorship contribution statement

**[待补充 — to be completed before submission: list each author with their CRediT roles.]**

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Figure captions

**Figure 1. Open-label H3 pluvial-flood learning workflow.** Open flood observations (DEP stormwater polygons, 311 flooding reports, and USGS Ida high-water marks), static predictors (elevation, slope, a flow-accumulation proxy, land cover, buildings, hydrologic proximity), and a rainfall condition r (a constant synthetic rainfall condition in the present pilot, not observed radar rainfall) are assembled into H3 cells at R9 with provenance tags. Gradient-boosting classification and continuous-risk regression are then evaluated under H3-block GroupKFold cross-validation against constant-class and logistic/ponding-rule baselines; diagnostics include the rainfall-conditioned PFI_h(c,r) index (currently flat scenario response), a scale-loss Jaccard ladder (R10 to R9/R8), adaptive refinement to R11, and a Sandy coastal-overlap diagnostic. The FEMA Sandy layer is a dashed side-channel that bypasses learning and enters only the Sandy diagnostic; it is never a training label.

**Figure 2. Spatial results for the Lower Manhattan pilot (n = 141 R9 cells).** (a) Observed open-label flood-risk score; (b) pooled out-of-fold gradient-boosting probability under H3-block spatial cross-validation; (c) full-fit rainfall-conditioned index PFI_h(c, r), shown at a synthetic Ida-like rainfall condition r = 75 mm/h and not an out-of-fold prediction (the surface is invariant across the evaluated scenarios because the training rainfall is constant; Section 4.5). Hexagons are coloured by value on a common 0–1 scale; grey shading is the DEM relief and light-blue lines/polygons are NHDPlus shoreline and water features.

**Figure 3. Spatial H3-block cross-validation performance for the Lower Manhattan pilot.** Classification accuracy and F1 are shown as paired markers for each of five held-out folds formed from seven R7 H3 blocks (n = 141 cells); a final x-position shows the fold mean ± SD with error bars.

**Figure 4. Open-label hotspot scale-loss diagnostics across H3 resolutions.** Jaccard similarity and F1 compare hotspot sets defined on the reference fine support, H3 R10 (0.9-quantile threshold), with R9 and R8 representations under mean, maximum, and p90 aggregation.

**Figure 5. Resolution effects on the open-label score surface.** (a) Violin plots with overlaid cell scores of the distribution at R10 (n = 991), R9 (n = 160, mean rollup), and R8 (n = 31, mean rollup), showing variance compression as the grid coarsens; internal bars mark the mean and extrema, and the distributions are descriptive summaries of the assembled scores. (b) Cross-resolution hotspot Jaccard similarity matrix (0.9-quantile thresholds) between hotspot sets at R10, R9, and R8, computed on the coarser support of each pair so the R10-vs-R9 and R10-vs-R8 entries reproduce the ladder in Fig. 4. The R10 label-assembly footprint contains 991 cells and aggregates to 160 R9 and 31 R8 parents, distinct from the 141-cell R9 supervised modelling table in Sections 4.1–4.2. For the realised hotspot sets, both comparisons involving R8 yield Jaccard similarity 0.167.

**Figure 6. Adaptive refinement versus uniform fine grids by cell count.** Fixed R9 (141), adaptive mixed R9/R11 (3,933), and uniform R11 (6,909) representations are compared for the Lower Manhattan pilot (adaptive = 27.9× fixed R9 = 56.9% of uniform R11; 79 of 141 R9 cells refined).

---

## Data and code availability

The public repository (code, configs, tests, paper documentation, and small summary tables; large rasters, geojson, trained model binaries, and large parquet files are excluded) is available at https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3. The submission version is archived under the immutable tag `submission-v1`; the corresponding commit and provenance of all reported outputs are recorded in the accompanying audit document. Each raw layer is mapped in the repository download manifest to its source URL, retrieval date, and license. Analyses used scikit-learn 1.8.0 and H3 4.4.2 (exact versions are recorded in the run metadata). Synthetic demonstrations are excluded from scientific evidence. A process-oriented research report and a data-authenticity audit document accompany the manuscript in the same documentation folder.

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

[14] New York City Department of Environmental Protection, Stormwater flood map (ArcGIS Hub), accessed August 2026. https://data.cityofnewyork.us

[15] New York City Open Data, 311 service requests from 2010 to present (flooding subset), accessed August 2026. https://data.cityofnewyork.us/resource/erm2-nwe9

[16] U.S. Geological Survey, Hurricane Ida high-water marks, data release, accessed August 2026. https://doi.org/10.5066/P9OMBJPQ

[17] Federal Emergency Management Agency / New York City Open Data, Hurricane Sandy storm surge inundation (uyj8-7rv5), accessed August 2026. https://data.cityofnewyork.us/api/geospatial/uyj8-7rv5

[18] T. Saito, M. Rehmsmeier, The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets, PLOS ONE 10 (2015) e0118432. https://doi.org/10.1371/journal.pone.0118432
