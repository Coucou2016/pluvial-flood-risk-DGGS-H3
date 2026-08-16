# Literature + architecture conclusions (independent + advisor brief)

**Date:** 2026-08-16 (GitHub push round)  
**ChatGPT URL (intended):** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Public GitHub (verified):** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**Browser MCP status:** `cursor-ide-browser` is listed, but **automation failed** — new tabs get `viewId` then immediately vanish (`Tab 0 not found` / `Browser view not found` / `No browser tab available`). Could not paste brief, enable web search, or confirm ChatGPT GitHub-read.  
**Web-search advisor reply captured from ChatGPT:** **No**  
**Independent WebSearch (executor, this round):** **Yes** — Svellingen IJDRR DOI + 7Analytics summary; GeoML GroupKFold / spatial leakage pages; R `blockCV` vignette.

## Architecture verdict (executor judgment)

Adopt an **IJDRR-compatible section order** with **Nature-skills claim discipline** (evidence → boundary; no fabricated novelty). Primary venue shape = applied disaster-risk / methods paper, not flagship Nature.

**Axes (nature-writing):** `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (IJDRR-compatible + Nature claim verbs).

## Related work clusters (web-verified anchors)

1. **H3 + pluvial ML (contrast paper):** Svellingen, Torgersen, Bruland, Muthanna — *Int. J. Disaster Risk Reduction* (2026), Vol. 137 — ML building-level **PFIb** aggregated to H3 as hex-level index (**their** PFI_h aggregation narrative); ~98% spatial-query efficiency; fine (street-level ~R13) vs coarser (~R10) hotspot trade-off / Jaccard-scale loss reported in that paper. DOI: https://doi.org/10.1016/j.ijdrr.2026.106091 · related SSRN: https://doi.org/10.2139/ssrn.5875380 · 7Analytics note: https://7analytics.ai/internationaljournal-of-disaster-risk-reduction/  
   **Independent reject:** we do **not** claim PFIb reproduction, equality to their Jaccard ≈0.14, or that our open-label `PFI_h(c,r)` is their aggregated PFIb.
2. **Spatial CV / GeoML:** GroupKFold with geographic block IDs to reduce spatial leakage vs random k-fold; buffer / blockCV practice. Anchors: https://www.geospatialmachinelearning.com/training-geospatial-predictive-models-in-python/spatial-cross-validation-strategies/ · https://cran.r-project.org/package=blockCV/vignettes/tutorial_1.html · Hu et al. GeoAI Handbook spatial CV PDF: https://www.acsu.buffalo.edu/~yhu42/papers/2023_GeoAIHandbook_SpatialCV.pdf  
3. **Urban pluvial susceptibility ML:** conditioning-factor + classical ML studies (often historically random CV; newer work cites spatial blocking) — usually single-resolution / non-adaptive / no explicit non-PFIb rainfall-conditioned `PFI_h(c,r)`.  
4. **DGGS multi-scale flood:** hexagonal DGGS flood mapping under climate scenarios (IJGI-class literature) — multi-resolution fabric precedent without PFIb.

## Recommended writing architecture to imitate

| Layer | Imitate | Why |
|-------|---------|-----|
| Section skeleton | IJDRR applied risk paper | Same venue family as contrast paper; reviewers expect Data→Methods→Results |
| Claim language | Nature-skills / NatComms methods discipline | Prevent overclaim from LM smoke |
| Do **not** imitate | Svellingen PFIb→aggregate as *our* claim | We learn on open labels; we do not reproduce PFIb |

## Paper section + figure plan (honest)

1. Intro — problem + gap vs PFIb-H3 aggregation  
2. Related work — four clusters above  
3. Study area / data — LM bbox + provenance table  
4. Methods — H3; open labels; GBM; **spatial H3-block CV**; Jaccard ladder; adaptive; `PFI_h(c,r)` definition; Sandy negative control  
5. Experiments E1–E7  
6. Results — only live numbers  
7. Discussion — concept dialogue, not Jaccard matching  
8. Conclusions + 待补充  

Figures: F2 Jaccard, F3 adaptive counts, F4 spatial CV bars (live SciencePlots/TNR). F1 workflow schematic **待补充**. Scenario curves flat → honesty note, not “response verified”.

## Claimable novelty (honest one-paragraph)

We contribute a reproducible **open-label** H3 learning protocol with **spatially blocked GroupKFold CV**, an open-label **scale-loss Jaccard ladder**, **adaptive refinement screened by trained cell scores**, and an explicit definition of `PFI_h(c,r)` as a rainfall-conditioned hex flood probability/index (**not** feature importance and **not** PFIb), demonstrated on a Lower Manhattan public-data smoke (`n=141`, `assembly_mode=opendata`) — **not** as a PFIb replication, citywide validated product, or radar-conditioned event system.

## Claim matrix

| Allowed | Forbidden |
|---------|-----------|
| Open-label H3+ML + spatial CV on stated bbox | PFIb reproduction / insurance skill |
| Open-label Jaccard / scale-loss at stated res | Equality to Svellingen Jaccard 0.14 |
| Adaptive cell-count ratio vs uniform fine | Citywide compute savings from smoke |
| `PFI_h` = model flood probability under rainfall condition (definition) | Calling it importance or PFIb; claiming rainfall discrimination from **flat** scenario CSV |
| Sandy as negative control only | Training on Sandy; fixture/Oslo as science; citywide claims from LM |

## Gaps marked 待补充

- ChatGPT **web-search** reply + GitHub-read confirmation (browser MCP automation broken this round; manual paste required).  
- I2 observed event rainfall ingest.  
- Non-flat within-cell `PFI_h` across rainfall scenarios.  
- Citywide / expanded bbox primary results.  
- FloodNet held-out validation.  
- Workflow schematic figure (F1).

## Live numbers (not fabricated; LM smoke)

- Spatial CV accuracy **0.783756 ± 0.069280**, F1 **0.865748**, `n_cells=141`  
- Jaccard mean R10→R8 = **0.1667** (do **not** equate to 0.14)  
- Adaptive/uniform ratio ≈ **0.569**  
- Scenario within-cell `PFI_h` range = **0** (honest gap)
