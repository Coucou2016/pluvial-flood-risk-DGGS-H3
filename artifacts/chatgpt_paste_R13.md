# ChatGPT round R13 — Methods clarity & completeness (text only; methods text pasted inline)

**Public repo:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 (master is current; commit 5d24fb0)
**R12 outcome:** contribution contrast vs Svellingen sharpened; Agonafir et al. NYC 311 citations added; adaptive-resolution antecedent added. Landed + pushed.

## Current Methods section (verbatim, from manuscript.md — review this text directly)

### 4.1 H3 representation
"Training uses H3 resolution 9, configurable. Scale-loss diagnostics assemble labels at fine resolution 10 and roll hotspots to parent resolutions 9 and 8. Adaptive refinement expands selected parents to resolution 11. All joins use EPSG:4326."

### 4.2 Features and open labels
"Static predictors are elevation, slope, a flow-accumulation proxy, impervious fraction, an urban land-cover flag, building density, and distance-to-water. Rainfall enters as rainfall intensity for scenario conditioning; observed static columns are tracked separately from rainfall so that a constant synthetic grid is not presented as radar. Labels combine DEP polygon area fractions with 311 and Ida point counts into flood-risk and flood-class targets. These are observed flood labels, not ground-truth inundation, and PFIb is not used. FloodNet joins only when explicitly enabled and a non-empty layer exists."

### 4.3 Models and baselines
"The primary learner is a gradient-boosting classifier with a continuous-risk regressor. Baselines are an L2-regularised logistic (or linear) model and an elevation–impervious–slope ponding rule. In-sample metrics are treated as optimistic references only. In addition, two constant classifiers—always-positive and always-negative—are computed on each held-out fold so that accuracy and F1 are never reported without a class-prevalence comparison; the constant majority-class classifier is derived from the pooled class count."

### 4.4 Spatial H3-block cross-validation
"Cells are grouped by coarse H3 parents, and GroupKFold withholds entire blocks. Per-fold metrics are archived with each pilot run. For each held-out cell, the predicted class probability is retained, so that threshold-independent discrimination metrics (ROC-AUC and average precision, or PR-AUC) can be computed from out-of-fold predictions. Random independent splits are computed but are not primary."

### 4.5 Scale-loss diagnostics
"Fine-resolution hotspot sets (the top quantile of risk) are compared with parent-aggregated hotspots using Jaccard similarity and F1 under mean, maximum, and p90 rollups. These values are not equated to Svellingen et al.'s PFIb Jaccard of 0.14."

### 4.6 Adaptive refinement
"After training, cell scores screen parents for refinement. The metrics are mixed-resolution cell counts relative to a fixed coarse grid and a uniform fine grid, expressed as an adaptive-to-uniform cell-count ratio. The pilot uses the trained PFI_h as the screening score."

### 4.7 Rainfall-conditioned index
"The cell index is defined as PFI_h(c,r) = P̂(Y_c=1 | X_c, r), where static features X_c are held fixed while the rainfall condition r varies across named scenarios. This is a model output, not a SHAP or permutation importance, and not PFIb. Because the training rainfall is currently a constant, the model has not observed rainfall variation and PFI_h(c,r) cannot yet respond to it; the definition remains binding for future runs with observed rainfall."

### 4.8 Negative control
"FEMA Sandy coastal inundation overlaps are reported for separation checks only and are never used as training labels."

## Live facts you can cross-check (all from repo JSON/CSV)

- Resolution R9 (train), R10/R8 (Jaccard), R11 (adaptive), EPSG:4326.
- Features: elevation, slope, flow_accum_proxy (D8 from DEM), impervious_fraction (NLCD), urban_land_flag, building_density, dist_stream_m (NHDPlus-derived, tidal/shoreline proxy).
- Labels: flood_risk (continuous) and flood_class (binary) from DEP area fraction + 311 count + Ida HWM count.
- Spatial CV: GroupKFold over H3 parent blocks; k=2 parents (R7) → 7 blocks (n=141) / 28 blocks (n=956); 5 folds.
- Models: GradientBoosting (classifier) + regressor; baselines: logistic + ponding rule + always-positive/always-negative constants.
- Seed fixed (42); per-cell OOF probabilities archived → ROC-AUC/PR-AUC.

## R13 focus — make Methods clearer and more complete (do NOT change science/results)

For each subsection 4.1–4.8, tell me concretely:

1. **Where is the description too thin for a reviewer to reproduce or judge the method?** Name the specific subsection and the exact missing detail (e.g., "4.2 does not say how the three label sources are combined into one binary target", "4.4 does not state how the parent block is chosen / k value", "4.6 does not define the score quantile or how many parents are refined").
2. **Which single definition is most under-specified right now** — the label binarization, the spatial-CV grouping, or the adaptive-refinement screen — and what is the minimal precise sentence to fix it?
3. **Is the PFI_h(c,r) definition (4.7) mathematically and semantically watertight**, or does it need a clarifying clause (e.g., that r is a scalar rainfall intensity, that the trained model treats it as one input feature)?
4. **Are there any internal inconsistencies** between Methods and Results (e.g., a Method that promises something Results never shows, or a number only defined in Results)?
5. Give the next 3 highest-value Methods edits, each with subsection and the exact sentence to add/replace.

Rules: text only. Do not invent numbers. Where you cannot see a value (e.g. the exact binarization threshold or the k value), say "the manuscript does not state X" rather than guessing.
