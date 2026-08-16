# Literature + architecture conclusions (independent + advisor brief)

**Date:** 2026-08-16 (continued)  
**ChatGPT URL (intended):** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Browser MCP status:** **UNAVAILABLE** — session MCP catalog only exposes `cursor-app-control` (no `cursor-ide-browser`). Cannot list tabs, paste brief, enable web search in ChatGPT, or confirm GitHub-read. Brief ready: `artifacts/chatgpt_literature_brief.md`.  
**Web-search advisor reply captured from ChatGPT:** **No**  
**Independent WebSearch (executor, this round):** Yes — Svellingen DOI / 7Analytics summary; GeoAI handbook spatial CV PDF; GeoML GroupKFold practice pages.

## Architecture verdict (executor judgment)

Adopt an **IJDRR-compatible section order** with **Nature-skills claim discipline** (evidence → boundary; no fabricated novelty). Primary venue shape = applied disaster-risk / methods paper, not flagship Nature.

**Axes (nature-writing):** `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (IJDRR-compatible + Nature claim verbs).

## Related work clusters (web-verified anchors)

1. **H3 + pluvial ML (contrast paper):** Svellingen, Torgersen, Bruland, Muthanna — *Int. J. Disaster Risk Reduction* (2026), Vol. 137 — ML building-level **PFIb** aggregated to H3; ~98% spatial-query efficiency; Jaccard ≈ 0.14 between fine (R13) and coarser (R10) hotspots. DOI: https://doi.org/10.1016/j.ijdrr.2026.106091 · SSRN preprint related: https://doi.org/10.2139/ssrn.5875380  
2. **Spatial CV / GeoAI:** Hu et al. GeoAI Handbook chapter on spatial CV (clustering / grid / geo-attribute / spatial LOO); practice guides using **GroupKFold** spatial blocks to reduce leakage vs random k-fold. PDF: https://www.acsu.buffalo.edu/~yhu42/papers/2023_GeoAIHandbook_SpatialCV.pdf  
3. **Urban pluvial susceptibility ML:** city studies with conditioning factors + classical ML (often random CV historically; newer work increasingly cites spatial blocking) — related but usually single-resolution / non-adaptive / no non-PFIb `PFI_h(c,r)` honesty.  
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

Figures: F2 Jaccard, F3 adaptive counts, F4 spatial CV bars (live). F1 workflow schematic **待补充**. Scenario curves flat → honesty note, not “response verified”.

## Claimable novelty (honest one-paragraph)

We contribute a reproducible **open-label** H3 learning protocol with **spatially blocked GroupKFold CV**, an open-label **scale-loss Jaccard ladder**, **adaptive refinement screened by trained cell scores**, and an explicit definition of `PFI_h(c,r)` as a rainfall-conditioned hex flood probability/index (**not** feature importance and **not** PFIb), demonstrated on a Lower Manhattan public-data smoke (`n=141`, `assembly_mode=opendata`) — **not** as a PFIb replication, citywide validated product, or radar-conditioned event system.

## Claim matrix

| Allowed | Forbidden |
|---------|-----------|
| Open-label H3+ML + spatial CV on stated bbox | PFIb reproduction / insurance skill |
| Open-label Jaccard / scale-loss at stated res | Equality to Svellingen Jaccard 0.14 |
| Adaptive cell-count ratio vs uniform fine | Citywide compute savings from smoke |
| `PFI_h` = model flood probability under rainfall condition (definition) | Calling it importance or PFIb; claiming rainfall discrimination from **flat** scenario CSV |
| Sandy as negative control only | Training on Sandy; fixture/Oslo as science |

## Gaps marked 待补充

- ChatGPT **web-search** reply + any GitHub-read confirmation (needs browser MCP or manual paste).  
- I2 observed event rainfall ingest.  
- Non-degenerate `PFI_h` response across rainfall scenarios (within-cell range currently **0**).  
- Citywide / expanded bbox primary table.  
- FloodNet held-out validation.  
- Workflow schematic figure.
