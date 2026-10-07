# Scalable pluvial flood risk assessment (H3 DGGS + ML)

Open-label H3 learning protocol for urban pluvial flood **evidence screening**
(not a calibrated depth or probability product; not a reproduction of proprietary PFIb).

Authors and affiliations: **confirm before submission** (placeholders in `pyproject.toml`).
This repository is independent of NTNU / 7Analytics / Østfold reference-paper institutions.

## Academic manuscript (paper path)

Working methods manuscript (IJDRR-shaped; open labels ≠ PFIb): [`docs/paper/manuscript.md`](docs/paper/manuscript.md) · HTML [`docs/paper/manuscript.html`](docs/paper/manuscript.html).

**Abstract (pilot evidence only — Major Revision Option B).** We present an open-label H3 learning protocol for two Manhattan pilots: Lower Manhattan at the manuscript bbox (**n=262** R9 cells) and an expanded extent (`manhattan_expanded`, **n=956**). Lower Manhattan spatial CV accuracy **0.820 ± 0.057** / F1 **0.858** exceeds always-positive (**0.637** / **0.769**); pooled ROC-AUC **0.848**, AP **0.855**. Expanded: accuracy **0.823 ± 0.028** / F1 **0.826**, pooled ROC-AUC **0.882**, AP **0.823**. Spatial CV is the primary evaluation; a separate **deployment_full** model is fitted on all cells for maps/adaptive screening only. Scale-loss uses area-budget fractional hotspots (primary: area-weighted soft Jaccard; R10→R9 mean **0.227**, R10→R8 mean **0.136**). FloodNet (`aq7i-eu5q` + `kb2e-tjy3`) is downloaded for a **strict held-out** diagnostic only (not a training label). We do **not** claim citywide skill, PFIb reproduction, radar rainfall, or rainfall discrimination. Authoritative numbers: `outputs/paper_results.json`. Process detail: [`docs/paper/report.md`](docs/paper/report.md). Provenance: [`data/raw/data_manifest.json`](data/raw/data_manifest.json). Lockfile: `requirements.lock.txt`.

## Paper path vs demo path

**Main paper positioning** (do not drift): vs Svellingen et al. 2026 IJDRR (PFIb→H3 aggregation, Jaccard ~0.14 at R13 vs R10, NYC, proprietary insurance labels):

1. Spatially honest H3-block CV as first-class evaluation  
2. Open multi-source labels (DEP stormwater, 311, USGS Ida HWM) — **not** PFIb  
3. Adaptive H3 refinement against scale / hotspot loss  
4. Event-conditioned rainfall `PFI_h(c, r)` (hook; flat under constant rainfall)

**Oslo is transfer/appendix**, not the main claim. **Synthetic and fixture accuracy is never science.** Production assembly is **fail-closed** (`fallback_synthetic=False`); synthetic fills require explicit `--demo` / `--allow-synthetic`.

| Path | Config | What it is | What you may claim |
|------|--------|------------|--------------------|
| Demo | `configs/demo_oslo.yaml` | Hash features + synthetic labels | Pipeline QA |
| NYC fixture | `configs/nyc.yaml` + missing `data/raw/nyc/` | Same join/zonal/adaptive **code** on tiny invented layers (`assembly_mode=fixture`) | Code works; **not** NYC skill |
| NYC open data | same config with live GeoTIFF/GeoJSON | Production table | Spatial-CV results on documented public layers only |
| 7Analytics PFIb | — | **Not implemented, not reproduced** | Do not claim |

## Quick start (demo path)

```powershell
cd /path/to/pluvial-flood-risk-DGGS-H3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Oslo synthetic demo (data → train → eval → predict)
python scripts\run_demo.py
pluvial-smoke
```

## NYC / Manhattan paper path (Option B)

Study bbox = **Lower Manhattan** `[-74.02, 40.70, -73.97, 40.76]` (~262 R9 cells). Legacy `smoke` profile (~141) remains for fast QA only.

```powershell
python scripts\download_nyc_data.py --bbox-profile lower_manhattan
python scripts\build_nyc_h3.py --bbox-profile lower_manhattan --no-fixtures
pluvial-nyc-smoke
```

311 street-flooding uses official NYC Open Data **76ig-c548** (`official_identity_verified=true`). DEP stormwater uses an AdaptNYC/ArcGIS public mirror (`official_identity_verified=false`; official Open Data landing `9i7c-xyvv` — geospatial export not machine-reliable). USGS Ida HWM is official (DOI 10.5066/P9OMBJPQ). FloodNet events+sensors download via `scripts/run_floodnet_heldout.py` (held-out only).

Hydro `dist_stream_m` is a **distance-to-mapped-water** proxy (NHD/OSM), not dense inland streams. `event_rainfall.tif` is a constant synthetic rainfall input, not radar. **Do not claim PFIb reproduction.** Production assembly is fail-closed (no synthetic fills unless explicitly allowed).

Reproduce frozen metrics from `outputs/paper_results.json` after `pip install -r requirements.lock.txt` (or `pip install -e ".[dev]"` with `h3==4.4.2`).

Model layout after training:

```
models/<run>/
  evaluation/          # spatial CV folds + OOF + split diagnostic
  deployment/          # classifier_full / regressor_full (fit_rows == n_cells)
  run_metadata.json
```

Maps and adaptive screening load **deployment_full** only.

## Tests

```powershell
pytest -q
pluvial-smoke
```

Consistency gates (Major Revision): `tests/test_major_revision_gates.py`.

## License

MIT (scaffold). Upstream Open Data licenses remain those of NYC, USGS, FEMA, etc.
