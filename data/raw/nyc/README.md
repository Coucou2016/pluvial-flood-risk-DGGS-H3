# NYC / Manhattan raw layers

Place live Open Data here (EPSG:4326), or run:

```powershell
.\.venv\Scripts\python.exe scripts\download_nyc_data.py
```

That pulls a **Lower Manhattan bbox subset** (see `configs/nyc.yaml`), not citywide 1 ft DEM. Manifest: `DOWNLOAD_MANIFEST.json`.

Socrata (`data.cityofnewyork.us`) often returns HTTP 403; the downloader prefers ArcGIS FeatureServer / USGS / CDN mirrors for 311 and Sandy.

If downloads fail, `python scripts\build_nyc_h3.py --fixtures` writes **schema fixtures** (same filenames, invented geometries) and `SCHEMA_FIXTURE.txt`. Fixture scores are pipeline QA only — not NYC flood skill, not 7Analytics PFIb.

See `../DATA_SOURCES.md` for live vs synthetic honesty. With NHDPlus HR hydro present, `dist_stream_m` is vector-derived (tidal/shoreline-heavy in LM) and assemble can reach `feature_source=observed`.
