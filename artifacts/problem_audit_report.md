# Problem audit — pluvial flood H3+ML (Cursor lead, independent)

**Date:** 2026-08-15  
**Workspace:** `E:\Projects\20260522-pluvial-flood-risk-DGGS-H3`  
**Git:** not a repository (no `.git`; no HEAD SHA)

## Summary

Pipeline scaffolding for the paper path is largely in place (open labels, spatial CV, adaptive H3, `PFI_h` scenarios, NYC open-data download/assemble). Remaining issues are mainly **scientific honesty / scale / manuscript**, plus a few engineering provenance gaps. Honesty bugs patched this session: (1) synthetic event rainfall listed in `observed_feature_cols`; (2) **P7** adaptive smoke now uses trained `PFI_h` post-train.

## Findings

| ID | Severity | Issue | Evidence | Claim risk |
|----|----------|-------|----------|------------|
| P1 | **High** | No paper manuscript / methods draft in repo | Only `README.md` + `DATA_SOURCES.md`; no `docs/paper*` | Cannot submit / review methods without writing |
| P2 | **High** | Event rainfall is synthetic constant (75 mm/h), not radar/gauge | `DOWNLOAD_MANIFEST.json` layer `event_rainfall` source=`synthetic_constant_grid`; `FLOODNET` skipped | Must not claim event-conditioned skill from observed rain |
| P3 | **High** | FloodNet not wired | `FLOODNET_STUB.txt`; API 404 in manifest; `floodnet.py` stub only | Optional sensor validation section blocked |
| P4 | **Med** | Study extent = Lower Manhattan smoke subset, not citywide | `configs/nyc.yaml` bbox; README notes 1 ft citywide DEM too large | Citywide generalization claims forbidden |
| P5 | **Med→Fixed** | Jaccard ladder was R9→R8 only | Was: `nyc_smoke` filtered `resolutions <= resolution`; **patched**: `diagnostics.fine_res=10` assembles fine table for ladder | Weak vs Svellingen narrative; **now** open-label R10→R9/R8 (still not PFIb 0.14) |
| P6 | **Med** | Root `models/run_metadata.json` is Oslo **synthetic** (n=988) while NYC observed smoke lives under `models/nyc_smoke/` (n=141, `data_provenance=observed`) | Compare both JSON files | Easy to mis-cite demo metrics as NYC skill |
| P7 | **Med→Fixed** | Adaptive path in `nyc_smoke_test` used pre-train synthetic/label scores | Was `pipeline.py` pre-train block; **patched 2026-08-15**: train → scenarios → `run_inference` → adaptive on `PFI_h` / `flood_probability`, `score_source=trained_PFI_h` | Was: smoke adaptive not ML; **now** adaptive metrics reflect trained classifier |
| P8 | **Med** | Spatial CV on n=141 / ~7 blocks is thin for paper primary results | `models/nyc_smoke/run_metadata.json` `spatial_cv_n_blocks=7` | Report uncertainty; expand bbox or fine-res before strong claims |
| P9 | **Med** | Synthetic rainfall was previously tagged inside `observed_feature_cols` | `assemble.py` (pre-fix); parquet showed `rainfall_mm_h` in observed cols | Misleading provenance; **patched** this session (`rainfall_source` column; rainfall not added to `observed`) |
| P10 | **Low** | Hydro = NHD tidal/waterbody proxy | Manifest detail + DATA_SOURCES | Methods must say distance-to-water |
| P11 | **Low→Fixed** | Negative-control JSON note fixture-only phrasing | `negative_control.py` now branches on `assembly_mode` | Live vs fixture wording |
| P12 | **Low** | No git → no reproducible commit pin for ZIP/paper | `Test-Path .git` → False | Init git later (user-authorized) for archival |
| P13 | **Info** | Random-split metrics still written alongside spatial CV | train metadata | Paper must foreground spatial CV only |

## What looks solid

- Open-data assemble path produces `assembly_mode=opendata`, `feature_source=observed`, `label_source=observed` for current NYC table (141 cells).
- Multi-source labels (DEP + 311 + Ida HWM), Sandy negative control, NLCD impervious, buildings, DEM, NHD hydro present per manifest.
- CLI + CI gates: pytest, `pluvial-smoke`, `pluvial-nyc-smoke`.
- Explicit anti-PFIb language in README, configs, figures captions, smoke return payload.

## Prioritized fix themes

1. **P0 — Honesty:** rainfall provenance (done locally); separate demo vs NYC model dirs in docs; never cite fixture/demo as skill.
2. **P0 — Paper skeleton:** methods outline + claim matrix + experiment checklist (see `paper_path_work_plan.md`).
3. **P1 — Evaluation design:** finer Jaccard ladder / adaptive using trained `PFI_h`; expand study area when feasible.
4. **P2 — FloodNet / real event rain:** optional integrations behind config; do not block manuscript draft.
