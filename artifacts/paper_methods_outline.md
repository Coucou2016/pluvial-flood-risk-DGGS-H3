# Methods / Experiments outline — H3 + ML pluvial flood (open labels)

**Date:** 2026-08-15  
**Positioning:** vs Svellingen et al. 2026 IJDRR — **no PFIb**; open multi-source labels; spatial CV; adaptive H3; `PFI_h(c,r)`.  
**Study extent (current runnable):** Lower Manhattan `smoke_bbox` / `bbox` in `configs/nyc.yaml` — **not** citywide.

---

## 1. Methods section skeleton (claim-safe)

### 1.1 Study area and data
- **Area:** Lower Manhattan bbox (state limits in config); citywide deferred (DEM size).
- **Static layers:** USGS 3DEP DEM subset, NLCD impervious, building footprints, NHDPlus HR / hydro → `dist_stream_m` (tidal/waterbody proximity in LM — **distance-to-water**, not inland stream density).
- **Labels:** DEP stormwater polygons + 311 + USGS Ida HWM → `flood_area_frac` / `flood_point_count` / `flood_class`.
- **Negative control:** FEMA/Sandy coastal inundation overlay (`sandy_*`) — **not** a training label.
- **Rainfall:** scenario constants + synthetic `event_rainfall` hook; tag `rainfall_source`; **do not** list `rainfall_mm_h` as observed static feature.
- **Provenance fields:** `assembly_mode`, `feature_source`, `label_source`, `rainfall_source`.

**Code:** `assemble.py`, `download_nyc.py`, `configs/nyc.yaml`, `data/raw/nyc/DOWNLOAD_MANIFEST.json`.

### 1.2 H3 representation
- Train/smoke table: H3 **R9** (~141 cells in smoke bbox).
- Adaptive fine: **R11** (config `adaptive.fine_res`).
- Jaccard diagnostic fine grid: **R10** (`diagnostics.fine_res`) via points + parent-inherited polygon scores (direct DEP overlay at R10 is optional/offline).

**Code:** `h3_grid.py`, `adaptive.py`, `pipeline.nyc_smoke_test`.

### 1.3 Models
- GBM classifier/regressor (+ logistic / rule baselines via evaluate).
- Event-conditioned `PFI_h(c,r)` over rainfall scenarios (moderate / heavy / ida_like / extreme).
- Adaptive screen uses **trained** `PFI_h` / `flood_probability` (`score_source=trained_PFI_h`).

**Code:** `models.py` / train-eval path in `pipeline.py`, `adaptive.py`.

### 1.4 Evaluation design
- **Primary:** H3-block GroupKFold spatial CV (forbid random-split as paper primary).
- **Scale-loss:** hotspot Jaccard / F1 ladder (mean / max / p90 rollups); open labels — **not** Svellingen 0.14.
- **Adaptive:** recall vs cell-count vs uniform fine.
- **Negative control:** coastal-only vs pluvial-only score concentration.
- **Cite:** `models/nyc_smoke/run_metadata.json` for NYC observed smoke — **not** root Oslo demo metadata.

---

## 2. Experiment checklist

| Exp | Claimable now? | Runnable | Blocker / note |
|-----|-----------------|----------|----------------|
| E1 NYC open table | Yes (LM subset) | Yes | `assembly_mode=opendata`, `feature_source=observed` |
| E2 Spatial CV | Yes as **smoke** | Yes | n≈141 / few blocks — expand before strong skill claims |
| E3 Baselines | Yes | Yes | Document models |
| E4 Jaccard ladder fine≥R10 | Yes (open-label diagnostic) | Yes | R10→R9/R8; **not** PFIb 0.14 |
| E5 Adaptive vs uniform | Yes (smoke metrics) | Yes | Trained `PFI_h`; still LM |
| E6 `PFI_h` scenarios | Yes (response to mm/h) | Yes | Rain is scenario/synthetic, not radar |
| E7 Sandy negative control | Yes (diagnostic) | Yes | Live note when `opendata` |
| E8 FloodNet | **No** | Stub | API / GeoJSON |
| E9 Observed event rain | **No** | Synthetic hook | Need radar/gauge |
| E10 Citywide | **No** | Blocked | Separate download profile |
| E11 Oslo transfer | Appendix only | Demo | Synthetic labels |
| E12 Manuscript figures | Partial | Jaccard PNG | Caption anti-PFIb |

---

## 3. Claim matrix (allowed vs forbidden)

| Claim | Allowed? |
|-------|----------|
| Open-label H3+ML with spatial CV on documented LM open data | Yes |
| Scale-loss / Jaccard on open labels at stated resolutions | Yes (do not equal Svellingen 0.14) |
| Adaptive reduces cells with recall tradeoff on trained `PFI_h` | Yes (state score source) |
| `PFI_h` responds to rainfall scenarios | Yes (state rain provenance) |
| PFIb / insurance skill reproduced | **Never** |
| Fixture/demo = NYC skill | **Never** |
| Citywide skill from LM smoke | **Never** |
| Radar/gauge event rainfall skill | **Not until** non-synthetic ingest |

---

## 4. Figures / tables to produce (writing sprint)

1. **Table 1** — data layers + provenance from `DOWNLOAD_MANIFEST.json`.
2. **Figure 1** — workflow (assemble → spatial CV → `PFI_h` → adaptive).
3. **Figure 2** — Jaccard ladder (`outputs/jaccard_by_resolution.png`); caption: open labels, not PFIb.
4. **Figure 3** — adaptive recall vs cell-count ratio.
5. **Figure 4** — `PFI_h` scenario maps (qualitative).
6. **SI** — random-split metrics only; FloodNet stub status; rainfall honesty.

---

## 5. Residual honesty checklist (before any submission draft)

- [ ] Methods freeze claim matrix above.
- [ ] Cite only `models/nyc_smoke/` for NYC observed smoke.
- [ ] State LM ≠ citywide; hydro = distance-to-water.
- [ ] State rainfall scenario/synthetic vs observed.
- [ ] No numeric comparison to Svellingen Jaccard 0.14 as reproduction.
