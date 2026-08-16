# ChatGPT paste — Round 1 (Literature + architecture)

**Paste into:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Or new chat title:** `R1 paper architecture literature`  
**Enable:** Web search ON  
**Rules:** TEXT only — no ZIP/uploads.  
**Public GitHub (read if possible):** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3

---

Please enable **web search** and help design a paper (not a coding plan).

## Locked positioning (do not drift)
- Open multi-source flood labels (DEP stormwater, 311, USGS Ida HWM) — **not** proprietary PFIb.
- Primary evaluation: **spatial H3-block GroupKFold CV** (not random split).
- **Adaptive H3** refinement screened by trained scores.
- `PFI_h(c,r)` = rainfall-conditioned hex **flood probability/index** from the model — **not** feature importance and **not** 7Analytics PFIb.
- Oslo = appendix only; fixture/synthetic ≠ science; Lower Manhattan smoke ≠ citywide.
- Do **not** recommend claiming PFIb reproduction or Svellingen Jaccard 0.14 equality.

## Live evidence (Lower Manhattan smoke only)
- `n_cells=141`, `assembly_mode=opendata`
- Spatial CV accuracy mean **0.783756 ± 0.069280**, F1 mean **0.865748** (`models/nyc_smoke/run_metadata.json`)
- Jaccard mean R10→R8 = **0.1667** (`outputs/jaccard_by_resolution.csv`) — conceptual dialogue with Svellingen, not equality claim
- Adaptive/uniform fine cell_count_ratio ≈ **0.569**
- Scenario within-cell `PFI_h` range = **0** (honest gap; synthetic rainfall hook)

## Ask
1. Survey: Svellingen 2026 IJDRR H3/PFIb; hexagonal DGGS flood; spatial CV for GeoML; adaptive grids / MAUP; urban pluvial ML.
2. Recommend writing architecture (IJDRR vs NatComms methods) and why.
3. Section framework + figure/table plan within our boundaries.
4. Claimable innovation vs Svellingen without overclaiming.
5. What we must **not** claim given LM smoke + synthetic rain + flat scenario PFI.

Return: structured outline, claim matrix (allowed/forbidden), 8–12 citations with DOI/URL, one-paragraph honest novelty.
