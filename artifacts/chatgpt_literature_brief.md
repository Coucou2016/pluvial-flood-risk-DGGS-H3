# ChatGPT brief — paper architecture literature (TEXT ONLY)

**Paste into:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Or new chat title:** `paper architecture literature`  
**Rules for advisor:** TEXT only — no ZIP/uploads. Please **enable web search**.

---

Please enable **web search** and help us design a paper (not a coding plan).

## Locked positioning (do not drift)
- Open multi-source flood labels (DEP stormwater, 311, USGS Ida HWM) — **not** proprietary PFIb.
- Primary evaluation: **spatial H3-block GroupKFold CV** (not random split).
- **Adaptive H3** refinement screened by trained scores.
- `PFI_h(c,r)` = rainfall-conditioned hex **flood probability/index** from the model — **not** feature importance and **not** 7Analytics PFIb.
- Oslo = appendix only; fixture/synthetic ≠ science; Lower Manhattan smoke ≠ citywide.
- Do **not** recommend claiming PFIb reproduction or Svellingen Jaccard 0.14 equality.

## What we already have (live Lower Manhattan smoke)
- `n_cells=141`, `assembly_mode=opendata`, spatial CV accuracy mean≈0.784±0.069, F1 mean≈0.866 (from `models/nyc_smoke/run_metadata.json`).
- Jaccard ladder fine R10→R8/R9 (mean/max/p90) in `outputs/jaccard_by_resolution.csv`.
- Adaptive vs fixed ablation: adaptive/uniform cell_count_ratio≈0.569; score_col=PFI_h.
- Sandy negative control JSON present.
- Observed event rainfall ingest **blocked** (synthetic constant event raster only).
- Current `pfi_h_scenarios.csv`: **zero** within-cell PFI change across moderate/heavy/ida_like/extreme — report honestly as gap.

## Ask you (with web search)
1. Survey related literature: Svellingen 2026 IJDRR H3/PFIb; DGGS flood; spatial CV for GeoML; adaptive grids / MAUP; urban pluvial ML.
2. Recommend a **writing architecture** to imitate (IJDRR vs Nature Communications methods vs other) and why.
3. Propose a **paper section framework** + figure/table plan compatible with our honest boundaries.
4. Brainstorm **claimable innovation points** vs Svellingen without overclaiming.
5. Flag what we must **not** claim given LM smoke + synthetic rain + flat scenario PFI.

Return: structured outline, claim matrix (allowed/forbidden), 8–12 key citations with DOI/URL if found, and a one-paragraph “honest novelty” statement.
