# Why this repository is flat (no folders)

## Intent

This repository is published **as a review surface**, not as a development
environment. It is deliberately flattened so that **the entire project —
manuscript, report, audit trail, code, figures and core result data — is visible
in one directory listing**. A reviewer (human or AI agent) can `ls` / list the
root once and immediately see everything, instead of walking a directory tree
and guessing which subfolder holds the numbers behind a claim.

This is a common pain point when an agent is asked to cross-check a paper: it
must resolve `docs/paper/manuscript.md`, find that it cites
`outputs/paper_results.json`, then locate `src/pluvial_flood_risk/model.py`, and
so on. Flattening collapses that traversal into a single listing, and the
`__` naming convention keeps the original path legible.

**There is no hidden significance to the flatness.** It is a deliberate
accessibility trade-off, and it is fine that the folder cannot be run or built
in place.

## Naming convention

A file's flat name is its original repository-relative path with every `/`
replaced by `__` (double underscore). Examples:

| Original path | Flat name |
|---|---|
| `docs/paper/manuscript.md` | `docs__paper__manuscript.md` |
| `src/pluvial_flood_risk/model.py` | `src__pluvial_flood_risk__model.py` |
| `outputs/paper_results.json` | `outputs__paper_results.json` |
| `data/processed/nyc_h3_cells.parquet` | `data__processed__nyc_h3_cells.parquet` |
| `artifacts/figures/spatial_cv_folds.png` | `artifacts__figures__spatial_cv_folds.png` |
| `docs/paper/figures/supplementary/adaptive_ablation.pdf` | `docs__paper__figures__supplementary__adaptive_ablation.pdf` |

Files that already lived at the root keep their names, except the project README
which is renamed to **`README_PROJECT_ORIGINAL.md`** (so that the flat-review
README can occupy `README.md`).

## What was deliberately left out of the flat root

| Excluded | Reason | Where it lives |
|---|---|---|
| Heavy raw geometry/raster (~216 MB: GeoJSON, GeoTIFF) | Size; not text-readable | GitHub **Release** bundle `raw_geospatial_bundle.zip` |
| QA render pack (~82 MB: page PNGs, zip snapshots) | Redundant renders of the audit reports | GitHub **Release** bundle `audit_qa_bundle.zip` |
| Processed parquet **is** included, and each has a CSV mirror | So an LLM can read the data as text | `data__processed__*.csv`, `outputs__*.csv` |
| ChatGPT paste/reply plumbing (`chatgpt_paste_*`, `chatgpt_reply_*`, `chatgpt_context_*`, `.js`, `.json` payloads) | Raw pipeline scratch, no review value | Original repo only |

Small raw provenance layers that *are* text-readable are kept so a reviewer can
inspect the actual evidence inputs: `data__raw__nyc__flooding_311.geojson`,
`data__raw__nyc__usgs_ida_hwm.geojson`, `data__raw__nyc__hydro_streams.geojson`
(and the `nyc_expanded` equivalents).

Third-party reference material (`1-s2.0-S2212420926001032-main.*`) is retained at
the root **as review context only**; it is a positioning reference, not this
project's output, and remains under the publisher's copyright.

## Reconstructing the original tree

Two helpers are provided so the flat layout can be reversed exactly:

```powershell
# PowerShell
./RESTORE_STRUCTURE.ps1 -Destination ./_restored

# or Python (cross-platform)
python RESTORE_STRUCTURE.py --into ./_restored
```

Both read `FILE_INDEX.csv` (the authoritative `flat_name → original_path` map,
also available as `FILE_INDEX.json`) and copy each file back into its original
directory structure. They **copy**, never move, so the flat folder is untouched.

## Keeping it honest

Because a flat listing hides structure, two machine-readable aids are included:

- **`FILE_INDEX.csv`** — every file with `flat_name`, `category`,
  `size_bytes`, `original_path`.
- **`RESULTS_QUICK_TABLE.csv`** — the headline frozen numbers with their exact
  registry keys, so a claim in the manuscript can be traced to a value in one
  hop.
