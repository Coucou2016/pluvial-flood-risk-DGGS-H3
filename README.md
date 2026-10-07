# Scalable pluvial flood risk assessment (H3 DGGS + ML) — flat repository for review

> **Why is everything in one folder?** This repository is **intentionally flat**
> (no subdirectories) so that a human reviewer, ChatGPT, or any other agent can
> read the *entire* paper, report, audit trail, code, figures and core result
> data in a single listing, without traversing a directory tree. See
> [`FLAT_LAYOUT_EXPLAINED.md`](FLAT_LAYOUT_EXPLAINED.md). Mapping and restore
> tooling: [`FILE_INDEX.csv`](FILE_INDEX.csv) / [`RESTORE_STRUCTURE.ps1`](RESTORE_STRUCTURE.ps1) /
> [`RESTORE_STRUCTURE.py`](RESTORE_STRUCTURE.py).

This repository is an **open-label H3 learning protocol for urban pluvial flood
evidence screening**. It is *not* a calibrated depth or probability product, and
it is *not* a reproduction of any proprietary flood-risk index.

Third-party reference material kept here for review context:
`1-s2.0-S2212420926001032-main.md` / `.pdf` (Svellingen et al., IJDRR — used only
as a writing/positioning reference; **not redistributed as our own output**).

---

## 1. Start here

| If you want to… | Open |
|---|---|
| Read the paper | [`docs__paper__manuscript.md`](docs__paper__manuscript.md) · HTML [`docs__paper__manuscript.html`](docs__paper__manuscript.html) · PDF [`docs__paper__manuscript.pdf`](docs__paper__manuscript.pdf) |
| Read the Chinese research report (背景/方法/图表/结果/分析/结论) | [`docs__paper__report.md`](docs__paper__report.md) · HTML [`report.html`](report.html) · PDF [`report.pdf`](report.pdf) |
| Read the technical audit trail (data provenance, calculation chain, P0 review resolutions) | [`docs__paper__audit.md`](docs__paper__audit.md) |
| Check the *authoritative* numbers | [`outputs__paper_results.json`](outputs__paper_results.json) + [`RESULTS_QUICK_TABLE.csv`](RESULTS_QUICK_TABLE.csv) |
| Get the 5-minute orientation | [`AI_REVIEW_READING_GUIDE.md`](AI_REVIEW_READING_GUIDE.md) |
| Understand every column | [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) |
| See all files by role | [`FILE_INDEX.csv`](FILE_INDEX.csv) |

**Single source of truth for numbers:** `outputs__paper_results.json`. Every
figure, table and sentence in the manuscript/report/audit is checked against it
by `tests__test_major_revision_gates.py`.

---

## 2. Headline results (frozen, from `outputs__paper_results.json`)

Two Manhattan pilots. Evaluation is **spatial H3-block cross-validation**
(GroupKFold over R7 parent blocks) with pooled out-of-fold (OOF) metrics; a
separate `deployment_full` model is fitted on 100% of cells for mapping only.

| Quantity | Lower Manhattan (Option B) | Manhattan Expanded |
|---|---|---|
| Cells (R9) | **262** | **956** |
| Positive (`evidence-positive`) | 167 (63.7%) | 461 (48.2%) |
| Spatial-CV ROC-AUC (pooled OOF) | **0.850** | **0.880** |
| Spatial-CV PR-AUC / AP (pooled OOF) | **0.851** | **0.815** |
| Spatial-CV accuracy (fold mean ± SD) | 0.824 ± 0.055 | 0.819 ± 0.024 |
| Spatial-CV F1 (fold mean ± SD) | 0.861 ± 0.049 | 0.822 ± 0.028 |
| Always-positive baseline (acc / F1) | 0.637 / 0.769 | 0.482 / 0.649 |
| n folds / n spatial blocks | 5 / 12 | 5 / 28 |

**Scale loss (R10 → coarse, strict area budget, 10% hotspot budget, soft
Jaccard):** R10→R9 mean **0.220**, R10→R8 mean **0.136** (primary, area-weighted).
Max/p90 aggregations are reported as sensitivity only.

**Negative control (coastal vs pluvial, OOF score):** mean OOF score is
**0.886** for pluvial-only cells vs **0.406** for coastal-only cells — the model
separates pluvial from coastal flooding evidence rather than merely detecting
"wet near the coast".

**Labels.** The binary target is `evidence-positive` vs `evidence-unrecorded`,
assembled from open sources: DEP stormwater flood polygons (H&H model output),
NYC 311 street-flood complaints (official SODA dataset `76ig-c548`), and USGS
Ida high-water marks. **FloodNet** (`aq7i-eu5q` + `kb2e-tjy3`) is a **strict
held-out** diagnostic only — never a training label.

**Honest boundaries.** No claim of citywide skill, PFIb reproduction, radar
rainfall, or rainfall discrimination. `event_rainfall.tif` is a constant
synthetic rainfall hook, not observed radar. Production data assembly is
**fail-closed** (no synthetic fills unless explicitly requested).

---

## 3. Repository layout (flat — every file is at the root)

File names encode their original path with `__` as the separator, e.g.

- `src/pluvial_flood_risk/model.py`  → `src__pluvial_flood_risk__model.py`
- `docs/paper/manuscript.md`        → `docs__paper__manuscript.md`
- `outputs/paper_results.json`      → `outputs__paper_results.json`
- `data/processed/nyc_h3_cells.parquet` → `data__processed__nyc_h3_cells.parquet`

| Prefix | Contents |
|---|---|
| `docs__paper__*` | manuscript, report, audit, highlights, framework notes |
| `report.{md,html,pdf}` | top-level report copies (same as `docs__paper__report.*`) |
| `outputs__*` | result tables & JSON registries (metrics, ablations, sensitivities) |
| `data__processed__*` | per-cell modelling tables (parquet + CSV mirror) |
| `data__raw__*` | small raw provenance layers (311, USGS HWM, hydro) |
| `models__*` | fitted joblib artefacts for evaluation/deployment |
| `src__*`, `scripts__*`, `tests__*` | pipeline code, entry-point scripts, gates |
| `artifacts__*` | review history (acceptance reports, round logs) + figure renders |
| `审查输出__*` | Chinese audit pack (evidence JSON, sha256 inventory, QA reports) |
| `*__figures__*` | publication figures (PDF vector + PNG raster) |

**CSV mirrors.** Every `.parquet` has a `.csv` twin with identical columns, so a
text-only reader or LLM can open the data directly. Parquet remains the exact
artefact; the CSV is a reading convenience.

**Heavy raw geometry & QA bundles** (216 MB of GeoJSON/GeoTIFF + 82 MB QA pack)
are attached to the repository's **GitHub Release**, not committed here. See
[`AI_REVIEW_READING_GUIDE.md`](AI_REVIEW_READING_GUIDE.md) §"Heavy assets".

---

## 4. Reproduce (optional)

This flat folder is a *review snapshot*, not a runnable dev environment. To run
the pipeline, restore the tree and install the lockfile:

```powershell
# Recreate the original directory tree (copies, does not touch this folder)
python RESTORE_STRUCTURE.py --into ./_restored
cd ./_restored
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
pytest -q
```

Reference environment (from `outputs__paper_results.json`): Python 3.13.12,
`h3==4.4.2`, scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.6, shapely 2.1.2.

---

## 5. Data & licensing

Upstream Open Data licences remain those of NYC (311 `76ig-c548`, DEP stormwater
mirror), USGS (`P9OMBJPQ` Ida HWM; NHDPlus HR hydro; 3DEP DEM), FEMA (Sandy),
and Esri/Annual NLCD (impervious). See `data__raw__nyc__DOWNLOAD_MANIFEST.json`
for per-layer provenance and `data__raw__nyc__README.md` for honesty caveats.

Repository code is MIT. The third-party reference article retained at the root
remains under its publisher's copyright and is included **only** as review
context — it is not part of this project's output.

Authoritative provenance: `outputs__paper_results.json` (`git_commit`,
`run_id`, `freeze_tag`) and `审查输出__evidence__file_sha256_inventory.csv`.
