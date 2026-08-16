# Paper-path work plan — H3 + ML pluvial flood risk

**Positioning:** vs Svellingen et al. 2026 IJDRR — open labels, spatial CV, adaptive H3, `PFI_h(c,r)`; **not** PFIb.

## Methods draft outline (manuscript skeleton)

1. **Introduction** — urban pluvial risk; scale loss under H3 aggregation; need for open, reproducible alternatives to proprietary insurance labels.
2. **Related work** — Svellingen et al. 2026; DGGS/H3; spatial CV; ML flood susceptibility.
3. **Study area & data** — Lower Manhattan bbox (state limits); DEM (3DEP subset), NLCD impervious, buildings, DEP stormwater, 311, USGS Ida HWM, NHDPlus HR (distance-to-water), Sandy negative control; FloodNet (future); rainfall scenarios / synthetic event hook honesty.
4. **H3 representation** — resolutions 8–11; cell features; observed vs synthetic provenance fields.
5. **Labels** — multi-source open labels → `flood_area_frac` / `flood_point_count` / `flood_class`; **not** PFIb.
6. **Models** — GBM (+ logistic / rule baselines); features list; `PFI_h(c,r)` definition.
7. **Evaluation** — H3-block GroupKFold; forbid random-split as primary; Jaccard/F1 hotspot ladder; adaptive refinement metrics (`hotspot_recall`, `cell_count_ratio`); negative control.
8. **Results** — tables/figures checklist below.
9. **Discussion** — scale, label bias, hydro proxy, rainfall honesty, transfer to Oslo appendix.
10. **Limitations & reproducibility** — manifest, seeds, software versions, no PFIb.

## Experiment checklist

| Exp | Status | Runnable now? | Notes |
|-----|--------|---------------|-------|
| E1 Assemble NYC open table | Done (local) | Yes | `build_nyc_h3.py --no-fixtures` |
| E2 Spatial CV metrics | Smoke done (n=141) | Yes | Expand bbox before paper primary |
| E3 Baselines (logistic, rule) | Implemented | Yes | `pluvial-evaluate` |
| E4 Jaccard scale-loss ladder | Done (R10 fine) | Yes | `diagnostics.fine_res=10`; R10→R9/R8 CSV + PNG |
| E5 Adaptive vs uniform fine | Smoke uses trained PFI_h | Yes | Post-train adaptive; still expand bbox for paper |
| E6 `PFI_h` scenarios | Done | Yes | moderate/heavy/ida_like/extreme |
| E7 Sandy negative control | Done | Yes | Interpret carefully |
| E8 FloodNet validation | Blocked | Stub | API/export wiring |
| E9 Observed event rainfall | Blocked | Synthetic hook | Need radar/gauge grid |
| E10 Citywide / borough scale | Blocked | Cost/size | Separate download profile |
| E11 Oslo transfer appendix | Demo path | Yes | Synthetic labels — appendix only |
| E12 Manuscript figures | Partial | Jaccard PNG exists | Caption already anti-PFIb |

## Claim matrix (allowed vs forbidden)

| Claim | Allowed when |
|-------|----------------|
| Open-label H3+ML pipeline with spatial CV | `assembly_mode=opendata` + documented layers + spatial CV |
| Scale-loss / Jaccard on open labels | Document resolutions & aggregation; do not equal Svellingen 0.14 |
| Adaptive reduces cell count with recall tradeoff | Report metrics on stated score source |
| `PFI_h` responds to rainfall scenarios | Scenario table; rainfall not claimed as radar if synthetic |
| PFIb reproduced / insurance skill | **Never** |
| Fixture/demo accuracy = NYC skill | **Never** |
| Citywide performance from LM smoke | **Never** |

## Prioritized patches (for ChatGPT / next coding pass)

| Priority | Item | Acceptance |
|----------|------|------------|
| P0 | Rainfall provenance honesty | `rainfall_mm_h` not in `observed_feature_cols`; `rainfall_source` present — **landed Cursor-side** |
| P0 | Docs: which `run_metadata` is citable | README note demo vs `models/nyc_smoke` |
| P0 | Methods markdown skeleton under `artifacts/` or `docs/` | This file + audit |
| P1 | Jaccard ladder at fine_res≥10 for paper fig | CSV rows covering R10→R9/R8 — **landed Cursor-side** |
| P1 | Adaptive smoke uses trained probabilities | Metrics from `PFI_h` / classifier — **landed Cursor-side** (`score_source=trained_PFI_h`) |
| P1 | Expand study bbox profile (optional config) | Documented; smoke still fast |
| P2 | FloodNet optional GeoJSON join | Config flag; empty if absent |
| P2 | Real event rainfall ingest | Manifest source ≠ synthetic |

## Next writing sprint (concrete)

1. Freeze claim matrix in manuscript Methods.
2. Produce Table 1 (data layers + provenance from `DOWNLOAD_MANIFEST.json`).
3. Produce Figure 1 (workflow), Figure 2 (Jaccard ladder), Figure 3 (adaptive recall vs cost), Figure 4 (`PFI_h` maps/scenarios — qualitative).
4. Report spatial CV mean±std only as primary skill; put random split in SI.
5. Explicit limitations paragraph: synthetic rain, FloodNet, LM subset, hydro proxy.
