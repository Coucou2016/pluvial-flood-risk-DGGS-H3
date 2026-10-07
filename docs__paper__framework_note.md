# Paper framework note (Option B freeze)

**Date:** 2026-09-15  
**Manuscript spine:** `docs/paper/manuscript.md` (user mainline; no separate `manuscript_new*` found)  
**Numeric registry:** `outputs/paper_results.json` (generated_utc 2026-09-14)  
**Writing architecture:** IJDRR / applied disaster-risk skeleton + Nature-skills claim discipline  
**Axes (nature-writing / polishing):** task=manuscript; paper_type=methods-leaning research; language=en; journal=generic (IJDRR-style)

## One-sentence argument

In urban pluvial screening without proprietary insurance labels, linking open multi-source evidence, H3-block spatial cross-validation, area-budget scale-loss diagnostics, and score-guided adaptive refinement on one hierarchical grid yields prevalence-aware blocked skill and documented hotspot loss on Manhattan pilots, without claiming citywide or rainfall-conditioned discrimination.

## Literature-informed architecture (survey snapshot)

| Anchor | Role for this paper |
|--------|---------------------|
| Svellingen et al. 2026 IJDRR (PFIb→H3 aggregation; Jaccard ~0.14 R13–R10) | **Contrast venue & skeleton**; do not reproduce PFIb, efficiency %, or their Jaccard as ours |
| Li et al. 2022 IJGI (multi-scale flood on hexagonal DGGS) | Supports DGGS as multi-resolution fabric, not as learning protocol alone |
| Bersabe & Jun 2025 IJGI (Seoul pluvial ML + drainage factors) | Related open-factor ML maps; typically lack H3-native CV + adaptive + honest rainfall conditioning |
| Spatial CV / GeoAI practice (block / GroupKFold; e.g. h3sdm_spatial_cv) | Justifies H3-parent blocking as primary evaluation |
| Agonafir et al. on NYC 311 street flooding | Documents reporting bias of crowd labels used as evidence |

**Imitate:** IJDRR section order; Methods→Results→Discussion claim–evidence–boundary; Phrasebank hedging.  
**Do not imitate:** “tool stack as novelty”; PFIb aggregation as our contribution; copying reference-paper numbers.

## Claimable contributions (not the software stack)

1. **Open heterogeneous labels kept distinct** on H3 (DEP model polygons / official 311 / Ida HWM), composite max for screening only.  
2. **Spatial H3-block CV as primary blocked evaluation**, with prevalence-aware constant baselines.  
3. **Area-budget soft Jaccard scale-loss ladder** on native R10 open evidence (strict_area_budget).  
4. **Adaptive H3 refinement** screened by deployment model score (cell-count representation only).  
5. **Explicit `PFI_h(c,r)`** as rainfall-conditioned model score (not feature importance; not PFIb); flat under constant synthetic rainfall → rainfall discrimination deferred.

## Frozen headline metrics (do not invent)

| Pilot | n | Prevalence | Acc (mean±SD) | F1 | Pooled ROC-AUC | Pooled AP |
|-------|---|------------|---------------|----|----------------|-----------|
| Lower Manhattan Option B | 262 | 63.7% | 0.820 ± 0.057 | 0.858 | 0.848 | 0.855 |
| Expanded Manhattan | 956 | 47.9% | 0.823 ± 0.028 | 0.826 | 0.882 | 0.823 |

Scale loss (primary soft Jaccard, 10% area budget): R10→R9 mean **0.227**; R10→R8 mean **0.136**.  
Adaptive: 145/262 parents refined → 7,222 mixed vs 12,838 uniform R11 (**56.3%**).  
FloodNet: held-out diagnostic only (LM ROC-AUC 0.343 on 23 sensor cells; Exp 0.468 on 57); never training labels.  
311: official SODA `76ig-c548`, `official_identity_verified=true`. Fail-closed assembly.

## Boundaries (always)

- LM / expanded pilots ≠ citywide  
- Synthetic constant rainfall ≠ observed event forcing  
- Soft Jaccard ≠ Svellingen 0.14  
- Deployment maps ≠ held-out skill  
- Author names / ORCID / CRediT remain **待补充**
