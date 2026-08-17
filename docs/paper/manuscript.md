# Spatially blocked pluvial flood learning on the H3 grid: open labels, adaptive refinement, and a rainfall-conditioned cell index

---

## Abstract

Intense short-duration rainfall can overwhelm urban drainage and produce pluvial flooding with limited warning, and city-scale screening increasingly relies on machine learning and multi-resolution grids. Many operational indices, however, are tied to proprietary insurance labels and to evaluation protocols that ignore spatial leakage. This study presents an open-label machine-learning framework for hexagonal pluvial flood screening on the H3 discrete global grid. Multi-source public flood indicators are joined to H3 cells; gradient-boosting classification and continuous-risk regression are fitted; and performance is assessed with H3-block spatial cross-validation that withholds entire parent cells. The framework quantifies scale loss through a Jaccard/F1 hotspot ladder, screens parents for adaptive refinement using trained scores, and defines a rainfall-conditioned cell index `PFI_h(c,r)` as a model output distinct from feature importance and from the proprietary PFIb. On a small Manhattan pilot (n = 141, 80% positive), accuracy is 0.784 ± 0.069 with F1 0.866, below the always-positive baseline (0.808 / 0.893); out-of-fold ROC-AUC is 0.68 and average precision 0.86. On a larger pilot (n = 956, 47.9% positive), accuracy is 0.642 ± 0.148, exceeding both the always-positive (0.479) and constant majority-class (0.521) baselines, with continuous-risk R² of 0.525 ± 0.112 and moderate out-of-fold discrimination (ROC-AUC 0.70, average precision 0.72). Adaptive refinement uses about 57% as many cells as a uniform fine grid. The results demonstrate the framework end-to-end on the stated pilot extents but do not establish citywide skill or rainfall-conditioned discrimination, because event rainfall remains a constant synthetic input.

**Keywords:** pluvial flood; H3; discrete global grid; spatial cross-validation; machine learning; flood susceptibility.

---

## 1 Introduction

Extreme rainfall events are increasing in frequency and intensity, and pluvial flooding—the flooding that occurs when intense rain overwhelms urban drainage before it can enter watercourses—can develop rapidly and with limited warning (Rosenzweig et al., 2021). Assessing this risk at city scale requires representations that are computationally scalable, updateable as new observations arrive, and evaluable without silent spatial leakage.

Discrete Global Grid Systems (DGGS), and the hexagonal H3 system in particular (Uber Technologies, 2026), provide nested cells that support multi-resolution aggregation and neighbourhood queries. Svellingen et al. (2026) showed that a machine-learning building-level pluvial susceptibility index can be aggregated into H3 cells, reducing spatial query cost by roughly two orders of magnitude, and that hotspot sets can diverge sharply across resolutions (Jaccard similarity of about 0.14 between street-level and neighbourhood hotspots on their proprietary stack). That work establishes H3 as a communication and screening fabric, but it focuses on aggregating and communicating a proprietary index rather than on an open, spatially honest learning protocol for jurisdictions without access to insurance claims.

This study develops an open-label H3 framework for pluvial-flood susceptibility modelling that combines spatially blocked evaluation, multi-resolution scale diagnostics, adaptive refinement, and an explicitly defined rainfall-conditioned cell index. Unlike Svellingen et al. (2026), who aggregate a pre-existing building-level, insurance-derived index to H3 cells for scalable representation, the present approach learns directly from open flood observations on the H3 support, evaluates transfer across held-out H3 spatial blocks, and selectively refines the spatial representation using trained cell scores. The framework retains explicit provenance for feature, label, rainfall, and assembly sources; treats H3-block cross-validation as the primary evaluation while retaining random splits as diagnostic comparisons and reporting class-prevalence baselines alongside accuracy and F1; and quantifies resolution-dependent scale loss using Jaccard and F1 before adaptive refinement. `PFI_h(c,r)` is defined as a rainfall-conditioned model output and is distinct from both feature-importance measures and PFIb. The analysis is methodological and limited to the evaluated pilot extents rather than constituting a citywide operational flood map.

Throughout, `PFI_h(c,r)` denotes a rainfall-conditioned hexagon flood probability produced by the trained model on the H3 support. The symbol is deliberately reused from Svellingen et al. (2026), where `PFI_h` instead denotes an H3-aggregated building-level index; the two quantities differ in training data (open flood observations versus insurance-derived building scores), in construction (direct H3-native learning versus post-hoc aggregation), and in meaning, and are therefore not equivalent. Claims of citywide skill, radar-based rainfall, parity with PFIb, or rainfall-conditioned discrimination are outside the scope of the present evidence.

## 2 Related work

The closest methodological comparator is the H3-based pluvial flood framework of Svellingen et al. (2026). They aggregate a machine-learning building-level pluvial susceptibility index (PFIb) into H3 cells, reducing geometry-heavy spatial query cost by roughly two orders of magnitude while exposing a resolution trade-off: fine street-level hotspots are largely invisible at coarser neighbourhood grids (Jaccard about 0.14 between their fine and intermediate hotspot sets). A related preprint develops the same H3 indexing narrative (Svellingen et al., 2025). This line of work treats H3 as a scalable communication fabric for proprietary indices; its focus is aggregation and communication rather than open-label learning or spatially blocked evaluation. It is therefore the closest precedent and an explicit boundary for the present study, which does not reproduce PFIb and does not equate its own Jaccard values to theirs.

Hexagonal DGGS have also been investigated as general substrates for multi-source and multi-resolution flood analysis. Li et al. (2022) use an ISEA3H hexagonal DGGS for multi-scale flood mapping under climate scenarios, emphasising resolution-consistent predictors. Their contribution supports DGGS nesting as a scientific substrate, whereas the present study uses H3 nesting for a learning and evaluation framework over open urban flood indicators rather than for climate-scenario inundation mapping. Adaptive and non-uniform spatial resolution has separate antecedents in process-based flood simulation; here the grid is refined selectively from trained scores rather than prescribed by an inundation solver.

A separate methodological issue concerns spatial dependence in model evaluation. Random train/test splits routinely inflate skill under spatial autocorrelation. Sun et al. (2023) establish the rationale for spatially separated validation in geospatial machine learning. This study operationalises that rationale with `GroupKFold` over coarse H3 parent identifiers, so that entire parent blocks are withheld and primary reporting aligns with leakage-aware practice rather than treating random accuracy as the headline metric.

Open urban flood observations provide an alternative to proprietary damage or insurance labels, although their observation processes introduce reporting biases. New York City 311 flooding complaints have previously supported statistical and machine-learning analyses of street flooding, and their reporting biases—who reports, and which flooded roads are driven—are explicitly documented (Agonafir et al., 2022a; Agonafir et al., 2022b). The present contribution is therefore not the use of open flood reports itself, but their assembly onto H3-native cells together with blocked spatial evaluation.

A parallel literature applies machine-learning methods to urban pluvial-flood susceptibility using topographic, land-cover, hydrological, and drainage-related predictors. City-scale studies map susceptibility from digital elevation models, land cover, and drainage proxies with classical machine learning (e.g., Bersabe & Jun, 2025, Seoul). The present study combines these strands—open multi-source labels, H3 nesting, adaptive refinement screened by trained scores, and an explicitly defined rainfall-conditioned cell index—in a single reproducible pipeline with blocked cross-validation as the primary evaluation.

Relative to the PFIb-to-H3 aggregation papers, this work does not improve or reproduce a proprietary building index; it asks whether public flood indicators can support spatially blocked learning on H3. Relative to hexagonal DGGS flood mapping, it emphasises evaluation and adaptive screening rather than scenario inundation alone. Relative to urban pluvial susceptibility maps, it adds H3-block cross-validation as the primary evaluation, an open-label scale-loss ladder, adaptive cell-count diagnostics, and a formal non-PFIb definition of `PFI_h(c,r)`, while the present evidence does not yet establish citywide, radar, or rainfall-discrimination claims.

## 3 Study area and data

**Extent.** Two Manhattan pilot extents are used. The smaller is a Lower Manhattan bounding box (approximately 74.02–73.97°W, 40.70–40.76°N); the larger (`manhattan_expanded`) extends northward to approximately 74.03–73.94°W, 40.68–40.80°N. Both are pilot extents within New York City, not a citywide extent.

**Layers.** The following open layers were downloaded in August 2026: a digital elevation model (USGS 3DEP subset); DEP stormwater flood polygons; building footprints; USGS Hurricane Ida high-water marks; NYC 311 flooding points (ArcGIS/CDN mirrors); FEMA Sandy storm-surge inundation (negative control only); NLCD impervious fraction; and NHDPlus HR hydrography, from which `dist_stream_m` is derived as a distance-to-water proxy in a tidal and shoreline setting. FloodNet is supported as an optional label source, but no usable FloodNet observations are included in the present analyses. Event rainfall is a constant synthetic rainfall condition representing the Ida-like scenario, not radar or gauge data.

**Data sources.** Elevation is from the USGS 3D Elevation Program; impervious fraction from the National Land Cover Database; hydrography from NHDPlus High Resolution; flood labels from the New York City Department of Environmental Protection stormwater flood polygons, NYC 311 flooding service requests, and USGS Hurricane Ida high-water marks; and the negative control from FEMA Sandy storm-surge inundation. Version and download dates are recorded in the repository download manifest. The assembly is open-data; rainfall may carry an event-raster provenance tag rather than a gauge or radar observation.

## 4 Methods

### 4.1 H3 representation

Supervised modelling uses H3 resolution 9 (R9) as the training and evaluation support; models are fitted and blocked cross-validation metrics are computed on R9 cells. Resolution 10 (R10) is used only to assemble fine labels for the scale-loss diagnostic, which rolls hotspots to parent resolutions 9 and 8 (R8); R10 and R8 never participate in training. Adaptive refinement is a post-training representation step that replaces selected R9 cells with their resolution-11 (R11) descendants. All H3 indexing and spatial joins use longitude–latitude coordinates (EPSG:4326). The overall workflow is summarised in Figure 1.

### 4.2 Features and open labels

Static predictors are elevation, slope, a flow-accumulation proxy (D8-derived from the digital elevation model), impervious fraction (NLCD), an urban land-cover flag, building density, and distance-to-water (a shoreline/tidal-water proxy). Rainfall is represented as a separate scenario-conditioning feature (rainfall intensity); the current pilot rainfall is constant and synthetic and is not presented as observed radar rainfall.

The continuous flood-risk target is assembled per cell from open observations. Polygon sources contribute an intersection area fraction (0–1); point sources contribute a per-cell count. The risk score is the maximum of the area fraction and the point-presence indicator, clipped to [0,1]. The binary flood-class target is then defined deterministically as `flood_class = 1[flood_risk >= 1e-9]`, so any cell with positive flood evidence is positive. These are observed flood labels, not ground-truth inundation, and PFIb is not used. FloodNet joins only when explicitly enabled and a non-empty layer exists.

### 4.3 Models and baselines

The primary learner is a gradient-boosting classifier with a continuous-risk regressor, fitted with a fixed random seed (42). Baselines are an L2-regularised logistic classifier and an elevation–slope–imperviousness ponding rule. The ponding score is the weighted combination \(0.40\cdot(1-\mathrm{elev}_{\mathrm{norm}}) + 0.35\cdot\mathrm{imperv} + 0.15\cdot(1-\min(\mathrm{slope},15^\circ)/15^\circ) + 0.10\cdot\mathrm{TWI}_{\mathrm{norm}}\), where \(\mathrm{elev}_{\mathrm{norm}}\) and \(\mathrm{TWI}_{\mathrm{norm}}\) are min–max normalised elevation and a topographic-wetness proxy, and a cell is classified positive when the score is at least 0.5. In-sample metrics are treated as optimistic references only. Two constant classifiers—always-positive and always-negative—are computed on each held-out fold so that accuracy and F1 are never reported without a class-prevalence comparison. The majority-class identity is determined from pooled target counts, whereas reported constant-baseline accuracy and F1 use the same fold-wise aggregation as the model metrics.

### 4.4 Spatial H3-block cross-validation

Each R9 modelling cell is assigned to its R7 parent by two-level coarsening (\(k=2\)), and five-fold `GroupKFold` partitions these R7 groups so that no R7 block occurs in both the training and held-out portions of a fold. Per-fold metrics are archived with each pilot run. For each held-out cell the predicted class probability is retained, so that threshold-independent discrimination metrics—ROC-AUC and average precision (AP, the area under the precision–recall curve; Saito & Rehmsmeier, 2015)—are computed from pooled out-of-fold predictions. Random independent splits are computed but are not primary.

### 4.5 Scale-loss diagnostics

Fine-resolution (R10) hotspot sets, defined as the top decile (quantile 0.9) of risk, are compared with parent-aggregated (R9 and R8) hotspots using Jaccard similarity and F1 under mean, maximum, and p90 rollups, after both sets are projected onto a common support. These diagnostics are methodologically distinct from the Jaccard value reported by Svellingen et al. (2026) and are not treated as a reproduction of that result.

### 4.6 Adaptive refinement

After training, cell scores screen parents for refinement: parents whose score is at or above the 0.8 quantile of all cell scores are selected. Each selected R9 cell is replaced by its R11 descendants, while unselected cells remain at R9. The primary metric is the resulting mixed-resolution cell count relative to a uniform fine grid, expressed as an adaptive-to-uniform cell-count ratio; hotspot recall of the adaptive grid against a uniform R11 grid is also reported. The pilot uses the trained `PFI_h` as the screening score.

### 4.7 Rainfall-conditioned index

The cell index is defined as

\[
\mathrm{PFI}_h(c,r)=\widehat{P}(Y_c=1\mid X_c,r),
\]

where \(Y_c\) is the binary flood label, \(X_c\) are the static predictors, and \(r\) is the rainfall condition. Here \(\widehat{P}(\cdot)\) is the classifier's positive-class probability output; no probability-calibration claim is made unless calibration is evaluated separately. The index is a model output, not a SHAP or permutation importance, and not PFIb. The present pilot uses a constant synthetic rainfall input; because rainfall does not vary in the training data, the fitted `PFI_h(c,r)` is invariant across the evaluated rainfall scenarios. This definition is retained for subsequent analyses using observed rainfall variation.

### 4.8 Negative control

FEMA Sandy coastal inundation is excluded from feature construction, target construction, model fitting, and model selection, and is compared with predictions only after fitting as a coastal-inundation separation check. The overlap statistics are the fraction of cells that are coastal-only (Sandy overlap without pluvial evidence) and the difference between mean scores of pluvial-only and coastal-only cells; Sandy labels are never used as training labels.

## 5 Experimental design

| ID | Description | Role |
|----|-------------|------|
| E1 | Assemble the open Lower Manhattan table | Feature/label table for the pilot bbox |
| E2 | Spatial cross-validation | Primary blocked accuracy / F1 and out-of-fold discrimination |
| E3 | Baselines | Diagnostic comparison against constant and parametric classifiers |
| E4 | Jaccard ladder | Scale-loss hotspot similarity |
| E5 | Adaptive refinement and ablation | Cell-count comparison against uniform fine |
| E6 | Rainfall scenarios | Within-cell `PFI_h` response across intensities |
| E7 | Sandy negative control | Coastal overlap checks (not training) |

Reproducible tables and figures are released with the public repository; process detail is documented in the accompanying research report.

## 6 Results

All figures are computed from the two Manhattan pilots and do not describe citywide performance.

### 6.1 Spatial H3-block cross-validation

| Metric | Value |
|--------|-------|
| Cells | 141 |
| Spatial-CV folds | 5 |
| Spatial-CV blocks | 7 |
| Spatial-CV accuracy, mean ± SD | 0.784 ± 0.069 |
| Spatial-CV F1, mean | 0.866 |
| Spatial-CV R², mean ± SD | 0.030 ± 0.343 |
| Spatial-CV MAE, mean | 0.332 |
| Random-split accuracy (diagnostic only) | 0.690 |
| Positive-class prevalence (held-out) | 0.801 |
| Always-positive baseline accuracy | 0.808 |
| Always-positive baseline F1 (fold-mean) | 0.893 |
| Always-negative baseline accuracy | 0.192 |
| ROC-AUC, pooled out-of-fold | 0.683 |
| Average precision (AP), pooled out-of-fold | 0.861 |

Per-fold accuracy/F1: Fold0 0.755 / 0.850; Fold1 0.760 / 0.850; Fold2 0.773 / 0.872; Fold3 0.714 / 0.813; Fold4 0.917 / 0.944 (Figure 2).

The held-out labels are highly imbalanced (80.1% positive). A trivial always-positive classifier would reach mean accuracy 0.808 and mean F1 0.893 across the same folds, which exceeds the model's 0.784 accuracy and 0.866 F1. Spatial blocking makes the evaluation design more defensible but does not by itself establish discrimination. The threshold-independent out-of-fold metrics are moderate: pooled ROC-AUC is 0.683 and pooled average precision is 0.861, the latter only slightly above the 0.801 prevalence baseline for a random ranker. Fold4 accuracy (0.917) coincides with a small test set (n = 24, two blocks) and is not interpreted in isolation. Continuous-risk R² (0.030 ± 0.343) is weak and reported for completeness. Random-split accuracy (0.690) remains diagnostic only.

### 6.2 Scale-loss Jaccard ladder (open labels)

Fine resolution R10, hotspot quantile 0.9 (Figure 3):

| Coarse resolution | Aggregation | Jaccard | F1 |
|-------------------|-------------|---------|-----|
| 8 | mean | 0.167 | 0.286 |
| 8 | max | 1.000 | 1.000 |
| 8 | p90 | 1.000 | 1.000 |
| 9 | mean | 0.977 | 0.988 |
| 9 | max | 1.000 | 1.000 |
| 9 | p90 | 0.977 | 0.988 |

Under mean aggregation, parent rollup at R8 yields Jaccard 0.167 with fine R10 hotspot parents, consistent with strong scale smoothing on this open-label stack. Maximum and p90 aggregation preserve extreme values by construction; their higher similarity therefore does not imply an absence of scale loss. These diagnostics use different labels, resolutions, and hotspot definitions from the PFIb Jaccard of 0.14 reported by Svellingen et al. (2026) and are not interpreted as a reproduction of that value.

### 6.3 Adaptive versus fixed and uniform fine grids

| Field | Value |
|-------|-------|
| score used for screening | `PFI_h` |
| Fixed coarse cells (R9) | 141 |
| Adaptive mixed cells | 3933 |
| Uniform fine cells (R11) | 6909 |
| Adaptive/uniform cell-count ratio | 0.569 |
| Parents refined | 79 |
| Screening quantile | 0.8 |

Adaptive mixed grids use about 57% as many cells as a uniform R11 grid (3933 versus 6909) while refining 79 of 141 coarse parents (Figure 4). Relative to the fixed R9 baseline the mixed grid uses about 27.9 times more cells (3933 versus 141). This statement concerns cell counts only; wall-clock runtime, memory, and city-scale cost are not reported.

### 6.4 Rainfall scenarios

The scenario loop covers 141 cells across four intensities—moderate (25), heavy (40), Ida-like (75), and extreme (100 mm/h). The mean `PFI_h` is about 0.803 for every scenario, and the within-cell range across scenarios is 0. The present pilot therefore does not demonstrate rainfall-conditioned discrimination. The flat response follows from constant training rainfall: every training cell carries the same synthetic rainfall value (75 mm/h), so rainfall has zero training variance and a feature importance of 0. A non-zero response requires ingested observed event rainfall with multi-intensity, non-synthetic provenance and retraining.

### 6.5 Sandy negative control

Across the 141 cells, 31 intersect Sandy coastal inundation, 71 have pluvial evidence, and 23 have both; 8 cells are coastal-only (≈5.7%), and the mean pluvial-minus-coastal score difference is ≈0.120. Coastal overlap is not a training label.

### 6.6 Expanded open-data pilot

| Metric | Value |
|--------|-------|
| Cells | 956 |
| Spatial-CV folds | 5 |
| Spatial-CV blocks | 28 |
| Spatial-CV accuracy, mean ± SD | 0.642 ± 0.148 |
| Spatial-CV F1, mean | 0.608 |
| Spatial-CV R², mean ± SD | 0.525 ± 0.112 |
| Spatial-CV MAE, mean | 0.112 |
| Random-split accuracy (diagnostic only) | 0.667 |
| Positive-class prevalence (held-out) | 0.479 |
| Always-positive baseline accuracy | 0.479 |
| Always-positive baseline F1 (fold-mean) | 0.641 |
| Constant majority-class (always-negative) accuracy | 0.521 |
| Constant majority-class (always-negative) F1 | 0.000 |
| ROC-AUC, pooled out-of-fold | 0.703 |
| Average precision (AP), pooled out-of-fold | 0.723 |

Per-fold accuracy/F1: Fold0 0.801 / 0.832; Fold1 0.419 / 0.442; Fold2 0.759 / 0.736; Fold3 0.516 / 0.343; Fold4 0.715 / 0.689.

The expanded extent is a second, larger open-data pilot (956 cells over 28 blocks), still not citywide. Its held-out labels are near-even (47.9% positive), in contrast to the 80% prevalence of the smaller table. Under the same H3-block protocol, spatial cross-validation accuracy is 0.642 ± 0.148, exceeding both the always-positive baseline (0.479) and the constant majority-class baseline (0.521). Out-of-fold discrimination is moderate: pooled ROC-AUC is 0.703 and pooled average precision is 0.723, the latter clearly above the 0.479 prevalence baseline. Mean F1 (0.608) nevertheless remains below the fold-mean always-positive F1 (0.641). The per-fold spread (accuracy 0.419–0.801; F1 0.343–0.832) coincides with heterogeneous held-out class composition—Fold1 and Fold3 are majority-negative, Fold0 and Fold4 are majority-positive, and Fold2 is nearly balanced (97/94)—and is not attributed to prevalence without further analysis. Continuous-risk R² (0.525 ± 0.112) is a positive blocked signal at this scale. This is reported as a robustness check on the framework, not as citywide skill.

## 7 Discussion

### 7.1 Interpretation under the stated boundaries

The two pilots indicate that an open-label H3 table can be assembled, trained, and evaluated with blocked cross-validation; that mean rollups substantially alter fine-hotspot membership; and that trained-score adaptive refinement reduces uniform-fine cell count. These results demonstrate the framework end-to-end under the stated pilot design; they do not establish product-ready city maps or rainfall-responsive screening under the present constant synthetic rainfall input. On classification, the two pilots differ. The smaller table does not beat its constant-class baselines on accuracy or F1, whereas the expanded table beats the constant majority-class baseline on accuracy (0.642 versus 0.521) but not on F1 against the always-positive comparator (0.608 versus 0.641). Out-of-fold ROC-AUC and average precision are moderate in both pilots (pooled ROC-AUC 0.68 and 0.70; pooled average precision 0.86 and 0.72), indicating some threshold-independent ranking discrimination that is stronger, relative to its prevalence baseline, in the more balanced expanded extent. Positive-class F1 nevertheless remains below the always-positive comparator in both pilots, so the discrimination evidence is treated as moderate rather than strong, and no citywide classification skill is claimed.

Relative to Svellingen et al. (2026), the comparison is conceptual: they aggregate a proprietary building index into H3 for scalable communication, whereas this study learns on public labels with spatial holdouts and an explicit non-PFIb `PFI_h(c,r)`. Although the R8 mean-aggregation Jaccard value (0.167) is numerically close to the value reported by Svellingen et al. (2026, 0.14), the two quantities arise from different labels, resolutions, and aggregation procedures and therefore do not constitute a reproduction comparison.

### 7.2 Limitations

1. **Spatial extent.** Results use two Manhattan pilots—Lower Manhattan (n = 141) and an expanded extent (n = 956)—neither of which is citywide New York City.
2. **Label bias.** 311 and related open indicators reflect reporting and mapping processes, not complete ground-truth inundation.
3. **Hydrographic proxy.** Distance-to-water from NHDPlus in a tidal and shoreline setting is a proxy, not inland drainage density.
4. **Rainfall provenance.** Event rainfall remains a constant synthetic rainfall input; gauge or radar event ingestion is not yet implemented.
5. **Flat rainfall response.** The within-cell range of `PFI_h` across rainfall scenarios is currently 0; rainfall-conditioned discrimination is not demonstrated.
6. **Class imbalance and discrimination.** The smaller pilot is highly imbalanced (80% positive), and its accuracy and positive-class F1 fall below the always-positive majority baseline (0.808 / 0.893 versus 0.784 / 0.866). The expanded pilot is near-even and beats the constant majority-class baseline on accuracy (0.642 versus 0.521) but not on F1 against the always-positive comparator (0.608 versus 0.641). Out-of-fold ROC-AUC and average precision are moderate in both pilots, so discrimination is supported at a modest level but is not claimed as strong skill.
7. **Small blocked design.** The smaller pilot distributes only seven H3 blocks over five folds (per-fold test 21–49, some folds a single block); the expanded pilot uses 28 blocks (per-fold test 190–193), which is more defensible but still a limited, non-citywide design.
8. **Continuous skill.** Spatial cross-validation R² is near zero in the smaller pilot (0.030) and moderate in the expanded pilot (0.525); the latter is reported as a scale-sensitive signal, not as citywide predictive skill.
9. **Held-out sensors.** FloodNet validation is unavailable because no usable FloodNet observations are included in the present analyses.

Random-split accuracy must not displace spatial cross-validation in claims. Fold-level variance (including Fold4 on n = 24 in the smaller pilot) further cautions against over-interpreting a single pilot run.

### 7.3 Outstanding steps

Future work should (i) ingest observed event rainfall with non-synthetic provenance; (ii) produce non-flat scenarios, that is, a within-cell `PFI_h` range greater than zero across rainfall intensities on the same static features; (iii) extend to a citywide or larger profile under the same spatial cross-validation protocol; and (iv) perform FloodNet held-out validation when a non-empty sensor layer is available.

## 8 Conclusions

This study presents a reproducible open-label H3 and machine-learning framework—spatial block cross-validation, scale-loss diagnostics, adaptive cell-count refinement, and an explicitly defined rainfall-conditioned cell index `PFI_h(c,r)` distinct from PFIb—evaluated on two Manhattan open-data pilots. The live metrics demonstrate the framework end-to-end on the stated pilot extents but do not establish citywide operational skill. Out-of-fold ROC-AUC and average precision indicate moderate ranking discrimination, stronger relative to chance in the more balanced expanded extent, while positive-class F1 remains below the always-positive comparator in both pilots. Observed event rainfall, a non-degenerate rainfall response, a full citywide extent, and FloodNet validation remain to be addressed.

---

## CRediT authorship contribution statement

**[待补充 — to be completed before submission: list each author with their CRediT roles.]**

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the authors used ChatGPT (OpenAI) as an editorial reviewer to identify and correct issues in scientific framing, language, and submission structure. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.

---

## Figure captions

**Figure 1. Open-label H3 pluvial-flood learning workflow.** Open flood observations (DEP stormwater polygons, 311 flooding reports, and USGS Ida high-water marks), static predictors (elevation, slope, impervious fraction, building density, distance-to-water), and a rainfall condition `r` (a constant synthetic rainfall condition in the present pilot, not observed radar rainfall) are assembled into H3 cells at R9 with provenance tags (`assembly_mode`, `feature_source`, `label_source`, `rainfall_source`), fitted with a gradient-boosting classifier and a continuous-risk regressor under H3-block `GroupKFold` cross-validation against constant-class (always-positive and always-negative) and logistic/ponding-rule baselines, and passed to diagnostics: the rainfall-conditioned `PFI_h(c,r)` index (currently flat scenario response), a scale-loss Jaccard ladder (R10 to R9/R8), adaptive refinement to R11, and a Sandy negative-control check. The FEMA Sandy layer is a dashed side-channel that bypasses learning and enters only the negative-control diagnostic; it is never a training label.

**Figure 2. Spatial H3-block cross-validation performance for the Lower Manhattan pilot.** Classification accuracy and F1 are shown for each of five held-out folds formed from seven R7 H3 blocks (n = 141 cells).

**Figure 3. Open-label hotspot scale-loss diagnostics across H3 resolutions.** Jaccard similarity and F1 compare R10-derived hotspot sets (top decile, quantile 0.9) with R9 and R8 representations under mean, maximum, and p90 aggregation.

**Figure 4. Adaptive refinement versus uniform fine grids by cell count.** Fixed R9, adaptive mixed R9/R11, and uniform R11 representations are compared for the Lower Manhattan pilot (adaptive/uniform ≈ 0.569; 79 of 141 parents refined).

---

## Data and code availability

The public repository (code, configs, tests, paper documentation, and small summary tables; large rasters, geojson, trained model binaries, and large parquet files are excluded) is available at https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3. The immutable paper release is tagged `paper-v1` in the repository; the exact commit that generated all reported outputs is recorded in the accompanying audit document. Each raw layer is mapped in the repository download manifest to its source URL, retrieval date, and license. Synthetic demonstrations are excluded from scientific evidence. A process-oriented research report and a data-authenticity audit document accompany the manuscript in the same documentation folder.

## References

Agonafir, C., Lakhankar, T., Khanbilvardi, R., Krakauer, N. Y., Radell, D., & Devineni, N. (2022a). A machine learning approach to evaluate the spatial variability of New York City's 311 street flooding complaints. *Comput. Environ. Urban Syst.*, 97, 101854. https://doi.org/10.1016/j.compenvurbsys.2022.101854

Agonafir, C., Pabon, A. R., Lakhankar, T., Khanbilvardi, R., & Devineni, N. (2022b). Understanding New York City street flooding through 311 complaints. *J. Hydrol.*, 605, 127300. https://doi.org/10.1016/j.jhydrol.2021.127300

Bersabe, J. T., & Jun, B.-W. (2025). The machine learning-based mapping of urban pluvial flood susceptibility in Seoul integrating flood conditioning factors and drainage-related data. *ISPRS Int. J. Geo-Inf.*, 14(2), 57. https://doi.org/10.3390/ijgi14020057

Federal Emergency Management Agency. (n.d.). Hurricane Sandy storm surge inundation. https://www.fema.gov

Li, M., McGrath, H., & Stefanakis, E. (2022). Multi-scale flood mapping under climate change scenarios in hexagonal discrete global grids. *ISPRS Int. J. Geo-Inf.*, 11(12), 627. https://doi.org/10.3390/ijgi11120627

Multi-Resolution Land Characteristics Consortium. (n.d.). National Land Cover Database (NLCD). https://www.mrlc.gov

New York City Department of Environmental Protection. (n.d.). Stormwater flood map. https://www.nyc.gov/site/dep

New York City Open Data. (n.d.). 311 service requests (flooding). https://data.cityofnewyork.us

Rosenzweig, B. R., et al. (2021). The value of urban flood modeling. *Earth's Future*, 9(1), e2020EF001873. https://doi.org/10.1029/2020EF001873

Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLOS ONE*, 10(3), e0118432. https://doi.org/10.1371/journal.pone.0118432

Sun, K., Hu, Y., Lakhanpal, G., & Zhou, R. Z. (2023). Spatial cross-validation for GeoAI. In S. Gao, Y. Hu, & W. Li (Eds.), *Handbook of Geospatial Artificial Intelligence*. Taylor & Francis. https://www.acsu.buffalo.edu/~yhu42/papers/2023_GeoAIHandbook_SpatialCV.pdf

Svellingen, W., Torgersen, G., Bruland, O., & Muthanna, T. (2025). Indexing areas vulnerable to pluvial floods—using machine learning and H3 hexagonal grid system. SSRN preprint. https://doi.org/10.2139/ssrn.5875380

Svellingen, W., Torgersen, G., Bruland, O., & Muthanna, T. (2026). Scalable pluvial flood risk assessment: A data-driven framework integrating machine learning (ML) and discrete global grid systems (DGGS H3). *Int. J. Disaster Risk Reduction*, 137, 106091. https://doi.org/10.1016/j.ijdrr.2026.106091

Uber Technologies, Inc. (2026). H3: A hexagonal hierarchical geospatial indexing system. https://h3geo.org

U.S. Geological Survey. (n.d.). 3D Elevation Program (3DEP). https://www.usgs.gov/3d-elevation-program

U.S. Geological Survey. (n.d.). Hurricane Ida high-water marks. https://www.usgs.gov

U.S. Geological Survey. (n.d.). NHDPlus High Resolution. https://www.usgs.gov/national-hydrography/nhdplus-high-resolution
