# ChatGPT paste — Round 2 (Methods claim-safety review)

**Paste into:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Or new chat:** `R2 methods claim safety`  
**Public GitHub:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**Also open:** `docs/paper/manuscript.md` §4 Methods on GitHub

---

Review the Methods text below for **claim safety**. Flag any sentence that overclaims given: LM smoke n=141, synthetic event rainfall, flat scenario PFI_h, Oslo=appendix, open labels ≠ PFIb.

## Methods excerpt (from live manuscript)

### H3 representation
Training uses H3 resolution R9. Scale-loss diagnostics assemble labels at fine R10 and roll hotspots to parents R9/R8. Adaptive refinement expands selected parents to R11. Joins use EPSG:4326.

### Features and open labels
Static predictors: elevation, slope, flow-accumulation proxy, impervious fraction, urban land-cover flag, building density, distance-to-water. Rainfall enters as `rainfall_mm_h` for scenario conditioning; observed static columns are tracked separately from rainfall so a constant synthetic grid is not marketed as radar. Labels combine DEP polygon area fractions with 311 / Ida point counts into flood_risk / flood_class as **observed flood labels** (not ground truth). We do not use PFIb.

### Models
Primary: gradient-boosting classifier + continuous risk regressor. Baselines: L2 logistic/linear and elevation–impervious–slope–TWI-like ponding rule. In-sample metrics are optimistic references only.

### Spatial H3-block CV
Cells grouped by coarse H3 parents; GroupKFold holds out entire blocks. Random i.i.d. splits are not primary.

### Scale-loss
Fine hotspot sets vs parent-aggregated hotspots via Jaccard/F1. Values are **not** equated to Svellingen et al. Jaccard ≈ 0.14.

### Adaptive refinement
Trained cell scores (`PFI_h` / flood probability) screen parents. Metric: adaptive/uniform fine `cell_count_ratio`.

### Event-conditioned PFI_h(c,r)
PFI_h(c,r) = P̂(Y_c=1 | X_c, r). Model output, not SHAP/importance, not PFIb.

### Negative control
FEMA Sandy coastal inundation overlaps for separation checks only; never training labels.

## Ask
1. Line-by-line claim hazards (ACCEPT / REVISE / REJECT wording).
2. Missing methods disclosures reviewers will demand.
3. Safe verbs for Results when citing n=141 smoke.
4. Proposed Methods subsection order if you would restructure.

Return a claim-safety table + revised phrasing only where needed (short).
