# Innovation framework and paper architecture

**Date:** 2026-08-16  
**Baseline:** NO_GIT (no `.git` in workspace)  
**Advisor chat (target):** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Positioning:** Methods / IJDRR-style applied paper with Nature-style claim discipline (evidence → boundary → no fabricated novelty).

## 1. Recommended writing architecture

| Option | Fit | Verdict |
|--------|-----|---------|
| **IJDRR / applied risk journal** (Intro → Related → Study area/Data → Methods → Results → Discussion → Conclusions) | Matches Svellingen venue; reviewers expect flood-risk framing | **Primary target structure** |
| Nature Communications methods-leaning | Stronger on protocol honesty + reproducibility; shorter conceptual opening | Use Nature-skills claim discipline; not flagship Nature |
| Pure Nature flagship | Overclaims risk; LM smoke not citywide | **Do not target** |

**Imitate:** IJDRR section skeleton + Nature-style claim verbs (`show` / `suggest` / `indicate`) and explicit boundaries.  
**Do not imitate:** Svellingen’s PFIb→aggregate narrative as our claim.

## 2. Paper framework (claimable spine)

```text
Problem: urban pluvial screening needs scalable grids without proprietary insurance labels
Gap: prior H3 work aggregates PFIb; open labels + spatial CV + adaptive response understudied
Method: open multi-source labels → H3 features → GBM + H3-block GroupKFold; Jaccard ladder; adaptive PFI_h screen; rainfall-conditioned PFI_h(c,r)
Evidence (LM smoke, n=141, assembly_mode=opendata): spatial CV metrics; Jaccard CSV/PNG; adaptive ablation; Sandy negative control
Boundary: Lower Manhattan smoke ≠ citywide; synthetic event rainfall ≠ radar; PFI_h flat across scenarios in current artifact → rainfall response 待补充; Oslo appendix only
```

## 3. Honest innovations vs Svellingen et al. 2026 (IJDRR)

| # | Claimable innovation | Evidence now | Not claimable |
|---|----------------------|--------------|---------------|
| I1 | **Open multi-source labels** on H3 (DEP / 311 / Ida HWM) instead of proprietary PFIb | `assembly_mode=opendata`, DATA_SOURCES | “Better than PFIb”; insurance skill |
| I2 | **Spatial H3-block CV as primary blocked evaluation** | `models/nyc_smoke/spatial_cv_folds.csv`, run_metadata, `outputs/classification_baselines.json` | Random-split accuracy as primary; classification "skill" (model does not beat majority baseline) |
| I3 | **Scale-loss Jaccard ladder on open labels** (mean/max/p90 rollups) | `outputs/jaccard_by_resolution.csv` | Equality to Svellingen Jaccard 0.14 |
| I4 | **Adaptive H3 refinement** screened by trained `PFI_h` | `adaptive_vs_fixed_ablation.csv`, `score_source=trained_PFI_h` | Citywide compute savings |
| I5 | **Explicit `PFI_h(c,r)` definition** as rainfall-conditioned flood probability/index (not PFIb, not feature importance) | Definition + scenario table schema | Event-conditioned discrimination (current CSV: **zero within-cell PFI range across scenarios** — report as gap) |

## 4. Claim matrix (freeze)

| Claim | Allowed when | Forbidden always |
|-------|--------------|------------------|
| Open-label H3+ML with spatial CV | Live opendata + documented layers + spatial CV | Fixture accuracy as NYC skill |
| Open-label scale-loss / Jaccard | Stated resolutions & aggregation | “Reproduced 0.14” |
| Adaptive reduces cell count vs uniform fine | Report `adaptive_cell_count_ratio` + score source | Citywide cost claim from smoke |
| `PFI_h` is model flood probability under rainfall condition | Definition + provenance | Feature importance / PFIb |
| Rainfall scenarios change `PFI_h` | Non-zero scenario response in artifact | Claim from flat scenario CSV |
| PFIb / insurance reproduction | — | Always |
| Citywide from LM smoke | — | Always |

## 5. Figure / table plan

| ID | Content | Source | Status |
|----|---------|--------|--------|
| T1 | Data layers + provenance | DOWNLOAD_MANIFEST / DATA_SOURCES | Fillable |
| T2 | Spatial CV mean±std + per-fold | run_metadata + spatial_cv_folds.csv | Live |
| F1 | Workflow schematic | Draw / describe | 待补充 graphic |
| F2 | Jaccard ladder SciencePlots | jaccard_by_resolution.png | Regenerated |
| F3 | Adaptive cell counts | adaptive_ablation.png | Regenerated |
| F4 | Spatial CV bars | spatial_cv_folds.png | Regenerated |
| F5 | `PFI_h` maps / scenario curves | pfi_h_scenarios.csv | Curves flat → qualitative map optional; honesty note required |
| A1 | Claim matrix | this file | Done |

## 6. Literature anchors (independent survey; not PFIb reproduction)

1. **Svellingen et al. 2026** IJDRR — PFIb→H3 aggregation, ~98% query efficiency, Jaccard ~0.14 R13 vs R10 (NYC, proprietary). Cite as contrast, not replication target. DOI: [10.1016/j.ijdrr.2026.106091](https://doi.org/10.1016/j.ijdrr.2026.106091).
2. **DGGS flood / multi-scale hex** — e.g. multi-scale flood mapping in ISEA3H under climate scenarios (IJGI 2022) — supports DGGS as multi-resolution fabric.
3. **Spatial CV / GeoAI** — block / GroupKFold spatial CV to reduce leakage (handbook + GeoML practice) — justifies H3-block CV as primary.
4. **Urban pluvial ML susceptibility** — open-factor ML maps (e.g. Seoul-style conditioning factors) — related but often lack DGGS + adaptive + rainfall-conditioned index honesty.

## 7. ChatGPT advisor brief (paste TEXT ONLY; enable web search)

See `artifacts/chatgpt_literature_brief.md`. Browser MCP may be blocked by empty tab / login; if so, parent pastes brief manually.

## 8. I2 rainfall status

**Blocked.** `event_rainfall.tif` remains synthetic constant hook (`rainfall_source=event_raster`). Observed gauge/radar ingest not present. Proceed with paper/report from live LM smoke artifacts; mark observed event rainfall as 待补充.
