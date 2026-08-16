# Prioritized fix plan — pluvial H3+ML paper path

**Date:** 2026-08-15  
**Owner notes:** Cursor lead executes patches; ChatGPT (when browser MCP works) reviews/extends.  
**Git HEAD:** N/A (no `.git`)

## P0 — honesty / claim safety

| ID | Item | Status | Acceptance |
|----|------|--------|------------|
| H1 | Rainfall not in `observed_feature_cols`; `rainfall_source` present | **Done** | Assemble tests green |
| H2 | Docs: cite `models/nyc_smoke/run_metadata.json` not root demo | **Done** (README) | No mis-cite in manuscript draft |
| H3 | Claim matrix frozen in work plan | **Done** | See `paper_path_work_plan.md` |

## P1 — evaluation design (paper-facing)

| ID | Item | Status | Acceptance |
|----|------|--------|------------|
| E1 | Adaptive smoke uses trained `PFI_h` | **Done** | `score_source=trained_PFI_h` |
| E2 | Jaccard ladder including fine-res ≥R10 | **Done** | CSV/PNG under `outputs/` |
| E3 | Expand study bbox profile (optional config) | **Done** | `bbox_profiles` + `--bbox-profile`; smoke stays `smoke` |
| E4 | Negative-control note live vs fixture | **Done** | `negative_control.json` |
| E5 | Spatial CV per-fold CSV | **Done** | `models/nyc_smoke/spatial_cv_folds.csv` |
| E6 | Adaptive vs fixed ablation | **Done** | `outputs/adaptive_vs_fixed_ablation.csv` |

## P2 — blocked / optional

| ID | Item | Status | Acceptance |
|----|------|--------|------------|
| I1 | FloodNet optional GeoJSON join | **Done** | Config flag; empty/absent → no-op |
| I2 | Observed event rainfall ingest | **Blocked** | Non-synthetic manifest; synthetic `event_raster` only |
| I3 | Citywide download profile | **Blocked** | Separate config |
| I4 | Manuscript skeleton | **Done** | `docs/paper/manuscript_skeleton.md` (Methods prose filled) |
| I5 | Paper + report package from live outputs | **Done (2026-08-16)** | `docs/paper/manuscript.md`, `report.html`, figures SciencePlots |
| I6 | Non-degenerate `PFI_h` across rainfall scenarios | **Open** | Current CSV within-cell range = 0 |

## Suggested next coding pass

1. **I2 Observed event rainfall ingest** remains scientific priority (still blocked — no gauge/radar grid).
2. Investigate why scenario `PFI_h` is flat across rainfall (I6) before claiming event conditioning empirically.
3. I3 citywide profile after rainfall honesty is stable.
4. Do **not** regress H1 / E1–E6 / I1 (FloodNet remains opt-in).
5. Paper writing path advanced: fill Results from live metadata (done); polish figures with SciencePlots (done).

## Gates (must stay green)

```text
pytest -q
pluvial-smoke
pluvial-nyc-smoke
```
