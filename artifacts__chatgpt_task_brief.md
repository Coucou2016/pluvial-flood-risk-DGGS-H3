# Engineering task: Pluvial flood H3+ML — problem audit + paper-path work plan

**From:** Cursor lead (local workspace)  
**To:** ChatGPT Pro/Plus (browser collaborator)  
**Date:** 2026-08-15  
**Source ZIP:** `artifacts/pluvial_h3_paper_audit_src_20260815_234637.zip`  
**SHA-256:** `1D7B67BCAAF95DC935E7987482F42E4B94D7E47DCBD4F374BE1F333E56818C7B`  
**Also see:** `artifacts/source_zip_baseline.json`  
**You cannot access the user’s disk.** Use only this brief + the uploaded ZIP.

---

## 1. Background & goals

Repository implements a scalable pluvial flood risk framework: H3 DGGS + ML, spatially honest H3-block CV, open multi-source labels, adaptive H3 refinement, and event-conditioned `PFI_h(c, r)`.

**Paper positioning vs Svellingen et al. 2026 IJDRR:**

| Their work | Our paper path |
|------------|----------------|
| PFIb → H3 aggregation | **No PFIb** — open labels (DEP, 311, USGS Ida HWM) |
| Jaccard ~0.14 at R13 vs R10 (NYC, proprietary) | Open-label Jaccard / scale-loss diagnostics |
| Fixed fine grid | Adaptive H3 refinement metrics |
| — | Spatial block CV as first-class evaluation |
| — | `PFI_h(c, r)` rainfall scenarios |

**User need:** Continue checking what problems remain and **advance the earlier paper/framework work plan** (methods outline, experiment checklist, code gaps vs claims, prioritized patches).

**Known soft gaps (starting point, not exhaustive):** FloodNet stub; synthetic `event_rainfall` (not radar); Lower Manhattan subset ≠ citywide; paper manuscript not written; root `models/run_metadata.json` may be Oslo demo while `models/nyc_smoke/` holds observed NYC smoke train.

**Cursor-side already landed (verify, do not regress):** (1) rainfall honesty — `rainfall_mm_h` not in `observed_feature_cols`; `rainfall_source` column. (2) **P7** — adaptive smoke uses trained `PFI_h` (`score_source=trained_PFI_h`). (3) **E2 Jaccard fine ladder** — `diagnostics.fine_res=10`; R10 table = points + parent-inherited polygon scores (`label_scale_mode=points_plus_parent_inherit`); CSV has R10→R9/R8; figure updated. (4) Negative-control note branches on `assembly_mode`. (5) `artifacts/paper_methods_outline.md` methods/experiment claim matrix.

**Ask ChatGPT for next priorities:** manuscript Methods/Experiments prose from outline; optional offline direct DEP@R10 vs inherited-mode wording; FloodNet optional GeoJSON; expand bbox profile; observed rainfall ingest. Do **not** regress H1/P7/E2/E4.

---

## 2. Non-negotiable boundaries

1. **No PFIb claims** — do not reproduce or claim 7Analytics insurance labels.
2. **Fixture ≠ science** — `assembly_mode=fixture` / synthetic demo metrics are QA only.
3. **No unauthorized git commit / push / PR / deploy.**
4. Do not invent live data results you cannot verify from ZIP contents + manifests.
5. Oslo (`configs/demo_oslo.yaml`) is transfer/appendix, not the main claim.
6. Hydro in Lower Manhattan is largely tidal/shoreline — `dist_stream_m` is distance-to-water, not classic inland stream proximity.

---

## 3. Current architecture (ZIP)

```
src/pluvial_flood_risk/   # core library
configs/demo_oslo.yaml, configs/nyc.yaml
scripts/download_nyc_data.py, build_nyc_h3.py, run_demo.py, run_nyc_smoke.py
tests/                    # pytest suite
data/raw/DATA_SOURCES.md, data/raw/nyc/DOWNLOAD_MANIFEST.json
LIVE_DATA_PATHS.md        # large layers not in ZIP
outputs_samples/          # sample Jaccard / negative_control / run_metadata
```

**Gates (must remain green after patches):**

```text
pytest -q
pluvial-smoke
pluvial-nyc-smoke
```

CI: `.github/workflows/ci.yml` runs the same three.

---

## 4. Scope — research / modify

### A. Problem audit (primary)

Audit remaining scientific honesty, engineering, and paper-readiness problems. Cover at least:

1. Provenance honesty (`assembly_mode`, `feature_source`, `label_source`, `rainfall_source` / event rainfall synthetic hook)
2. FloodNet stub vs paper claims
3. Scale: smoke_bbox / Lower Manhattan vs citywide
4. Jaccard ladder vs Svellingen comparison design (resolution pairs, aggregation)
5. Adaptive refinement evaluation vs uniform fine grid
6. Model artifact confusion (demo vs nyc_smoke metadata)
7. Label construction (DEP polygon area-frac + point counts; class imbalance; leakage)
8. Spatial CV block design adequacy for n≈141 cells
9. Negative control (Sandy) interpretation
10. Missing manuscript / methods text

### B. Advance paper work plan

Deliver a concrete plan:

1. Methods draft outline (sections + what each code module supports)
2. Experiment checklist (tables/figures; what is runnable now vs blocked)
3. Code gaps vs allowable paper claims
4. Prioritized patch list (P0/P1/P2) with acceptance tests

### C. Optional high-value patches (if time)

Prefer small, honest, test-backed patches over large refactors. Examples of good targets:

- Stop treating synthetic event rainfall as “observed” feature (if still present)
- Document / tag rainfall provenance in assembled tables
- Jaccard diagnostics that can include parent→child comparisons needed for paper figs
- FloodNet optional join hook behind explicit config (no fake sensors)
- Paper-facing `docs/` or `artifacts/` methods skeleton (markdown only)

---

## 5. Deliverables

1. **`problem_audit_report.md`** — findings with severity, evidence (file/symbol), claim risk
2. **`paper_path_work_plan.md`** — methods outline + experiment checklist + claim matrix
3. **`prioritized_fix_plan.md`** — P0/P1/P2 with owner notes
4. **Patches** — unified diffs or full files ready to apply; list every touched path
5. **Test notes** — commands you expect Cursor lead to run; any tests you added

---

## 6. Forbidden claims / ops

- Do not claim PFIb reproduction or Svellingen Jaccard 0.14 reproduced
- Do not claim citywide NYC skill from Lower Manhattan smoke bbox
- Do not claim radar/gauge rainfall when `event_rainfall` is synthetic constant
- Do not ask Cursor to `git push`, commit, or deploy
- Do not include secrets, API keys, or `.env` content in outputs

---

## 7. Acceptance criteria

Cursor lead will independently:

1. Verify findings against source (not trust ChatGPT alone)
2. Apply patches in isolation if provided
3. Run `pytest -q`, `pluvial-smoke`, `pluvial-nyc-smoke`
4. Security / claim-boundary review
5. Feed concrete defects back until pass or external blocker

A delivery **passes** when:

- Audit + work plan are complete and evidence-based
- Any code patches leave all three gates green
- No PFIb / fixture-as-science / unauthorized git ops
- Residual risks explicitly listed as unverified

---

## 8. ZIP contents note

Large live layers (buildings ~18 MB, DEP ~41 MB, Sandy ~5.5 MB, DEM/impervious) are **path-documented** in `LIVE_DATA_PATHS.md`, not shipped. Manifest + small vectors + full source/tests/configs are included.

**Git baseline:** workspace currently has **no `.git` directory** (not a git repo). Do not assume a commit SHA.

---

## 9. Response format

Please structure your reply as:

1. Executive summary (≤10 lines)
2. Problem audit table
3. Paper work plan (methods + experiments + claim matrix)
4. Prioritized fixes
5. Patches (if any)
6. Residual risks / what you could not verify without live GB data
