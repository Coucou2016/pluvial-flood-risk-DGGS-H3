# Data inputs (production vs demo)

## Demo (this repository)

| Item | Location | Provenance |
|------|----------|------------|
| H3 cell features | `data/processed/demo_h3_cells.parquet` | `feature_source=synthetic` (hash) |
| Labels | same table | `label_source=synthetic` (physics-inspired score, not observations) |

**Do not** report demo accuracy as operational flood forecasting performance.

Config: `configs/demo_oslo.yaml` (bbox, resolution, rainfall scenarios, spatial CV settings). Oslo is **transfer / appendix**, not the paper’s main claim.

## Paper study: NYC / Manhattan (open labels)

Main contribution vs Svellingen et al. 2026 IJDRR (PFIb→H3, Jaccard 0.14 R13 vs R10, proprietary insurance labels):

- Spatially honest H3-block CV
- **Open multi-source labels** (not PFIb)
- Adaptive H3 refinement
- Event-conditioned `PFI_h(c, r)`

**This repository does not reproduce 7Analytics PFIb** and does not ship insurance claims.

Config: `configs/nyc.yaml`. Assemble: `python scripts\build_nyc_h3.py`.

### Automated download (Lower Manhattan bbox)

Default study bbox is **Lower Manhattan** (`configs/nyc.yaml`), not citywide — a full NYC 1 ft DEM is too large for the default smoke path. The downloader pulls a **USGS 3DEP subset** for that bbox plus public vector mirrors:

```powershell
python scripts\download_nyc_data.py
# or
.\scripts\download_nyc_data_stub.ps1
```

Writes `data/raw/nyc/DOWNLOAD_MANIFEST.json` with per-layer status. On success (DEM + DEP present) it removes `SCHEMA_FIXTURE.txt` so assemble uses `assembly_mode=opendata`.

**Socrata note:** `data.cityofnewyork.us` often returns HTTP 403 from automated clients. The downloader therefore prefers **ArcGIS FeatureServer**, **USGS**, and (for Street Flooding CSV) a **jsDelivr CDN** mirror of the public 311 Street Flooding (SJ) extract (`cdn.jsdelivr.net/gh/mebauer/nyc-311-street-flooding@main/...`) as an optional fallback when ArcGIS is unavailable. Fixture fallback remains if network fails:

```powershell
python scripts\build_nyc_h3.py --fixtures
```

### What was downloaded in this workspace (2026-08-15)

| Layer | File | Status | Source / notes |
|-------|------|--------|----------------|
| DEM | `dem.tif` | **Live** | USGS 3DEP ImageServer export, EPSG:4326, 500×600 for bbox |
| DEP stormwater | `dep_stormwater_flood.geojson` | **Live** | ArcGIS Hub moderate+2050 SLR (Flooding_Category) |
| Buildings | `building_footprints.geojson` | **Live** | NYC MapHub `BUILDING_view` (~18k footprints in bbox) |
| USGS Ida HWM | `usgs_ida_hwm.geojson` | **Live** | ScienceBase DOI [10.5066/P9OMBJPQ](https://doi.org/10.5066/P9OMBJPQ) (~159 pts; retry if 502) |
| 311 flooding | `flooding_311.geojson` | **Live (mirror)** | ArcGIS `streetfloodtime` FeatureServer (~488 pts in bbox). SODA `erm2-nwe9` still 403; CDN Street Flooding (SJ) CSV is fallback |
| Sandy inundation | `fema_sandy.geojson` | **Live (mirror)** | ArcGIS Online `Sandy_Inundation_Zone` (~9 polys in bbox). Negative control only — not a training label |
| Impervious / NLCD | `impervious.tif` | **Live** | Esri Annual NLCD Fractional Impervious ImageServer; values scaled to 0–1 fraction |
| Hydro / NHD | `hydro_streams.geojson` | **Live** | USGS NHDPlus HR MapServer (flowlines + NHDArea + NHDWaterbody), bbox-clipped (~13 features). Lower Manhattan is tidal-river / shoreline-heavy — `dist_stream_m` is a **distance-to-water** proxy, not classic inland stream proximity. OSM Overpass waterways are a downloader fallback |
| FloodNet | `FLOODNET_STUB.txt` | Stub only | Sensor GeoJSON not wired |
| Event rainfall | `event_rainfall.tif` | **Synthetic hook** | Uniform 75 mm/h grid over bbox (Ida-like scenario); **not** gauge/radar |

`SCHEMA_FIXTURE.txt` is **absent** when the live DEM+DEP stack is present. With hydro present, assemble tags **`feature_source=observed`** for static terrain/exposure columns (rainfall may still come from the scenario/`event_rainfall` hook — see `assemble.py` provenance rules). Do not claim PFIb reproduction; Jaccard on this stack is open-label scale-loss QA, not Svellingen et al. 0.14.

### NYC public layers (manual / alternate portals)

All layers should be reprojected to **EPSG:4326** before H3 zonal stats / polygon join (`pluvial_flood_risk.crs_warp`). Native NYC DEM is often **EPSG:2263**.

| Dataset | Provider | URL / portal | Format | Typical CRS | License (check source) | Use in pipeline |
|---------|----------|--------------|--------|-------------|------------------------|-----------------|
| Building Footprints | NYC Open Data / MapHub | https://data.cityofnewyork.us/Housing-Development/Building-Footprints/nqwf-w8eh | GeoJSON | EPSG:2263 or 4326 | NYC Open Data Terms | `building_density` |
| 1 ft DEM (NYC) | NYC / DoITT | NYC Open Data / GIS | GeoTIFF | EPSG:2263 | City of NY | Prefer over 3DEP when available; warp with `crs_warp` |
| 3DEP DEM | USGS | National Map ImageServer | GeoTIFF | 4326 export | USGS public domain | Default automated DEM |
| DEP Stormwater Flood Maps | NYC DEP | Open Data + ArcGIS Hub | polygons | 2263 / 4326 | NYC Open Data Terms | Pluvial labels |
| 311 flooding subset | NYC 311 | https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9 | CSV / GeoJSON | WGS84 | NYC Open Data Terms | Point labels |
| FloodNet | FloodNet-NYC | https://www.floodnet.nyc/ | sensor points | WGS84 | see FloodNet terms | Optional stub |
| USGS Ida HWM | USGS | https://doi.org/10.5066/P9OMBJPQ | CSV → GeoJSON | NAD83 / WGS84 | USGS public domain | Independent HWM points |
| NHDPlus HR hydro | USGS | https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer | flowlines / waterbodies | 4326 export | USGS public domain | `dist_stream_m` (water-proximity proxy) |
| FEMA / Sandy surge | FEMA / NYC | Open Data `uyj8-7rv5` | polygons | varies | FEMA / NYC | Negative control only |

Suggested `data/raw/nyc/` layout:

```
data/raw/nyc/
  dem.tif                         # warped EPSG:4326 (3DEP subset or NYC 1ft)
  impervious.tif                  # optional
  building_footprints.geojson
  dep_stormwater_flood.geojson
  flooding_311.geojson            # optional if SODA reachable
  usgs_ida_hwm.geojson
  hydro_streams.geojson           # optional
  fema_sandy.geojson              # negative control only
  event_rainfall.tif              # optional event mm/h grid
  DOWNLOAD_MANIFEST.json
```

## Observed vs synthetic vs fixture

| Mode | `assembly_mode` | Feature builder | Label builder | Metrics meaning |
|------|-----------------|-----------------|---------------|-----------------|
| Hash demo | `hash_demo` | `engineer_features_for_cells` | `attach_labels` | Pipeline QA only |
| Schema fixture | `fixture` | same zonal/join as production on tiny invented layers | `attach_observed_labels` | Proves the **code path**; not NYC skill |
| Open data | `opendata` | DEM/buildings/… on disk (may be **mixed** with synthetic gaps) | DEP / 311 / HWM join | Valid **only** with spatial CV + documented layers |

`label_source=observed` means the **polygon/point join** ran, not that every feature column is live. Always read `assembly_mode`, `feature_source`, `DOWNLOAD_MANIFEST.json`, and `models/run_metadata.json` → `data_provenance`.

## CRS warp (implemented)

```python
from pluvial_flood_risk.crs_warp import warp_raster_to_4326, reproject_geojson_to_4326, ensure_raster_4326
warp_raster_to_4326("dem_2263.tif", "data/raw/nyc/dem.tif")
ensure_raster_4326("data/raw/nyc/dem.tif")  # in-place if needed
```

Requires: `pip install -e ".[raster]"` (`rasterio`, `pyproj`).

## Raster → H3 (implemented)

```python
from pluvial_flood_risk.raster import zonal_mean_raster_to_h3, merge_raster_feature, zonal_slope_deg_from_dem
zonal = zonal_mean_raster_to_h3(cells, "data/raw/nyc/dem.tif")
features = merge_raster_feature(features, zonal, "elevation_m")
slope = zonal_slope_deg_from_dem(cells, "data/raw/nyc/dem.tif")
```

## Credibility checklist

| Check | Demo | Fixture NYC | Live NYC Open Data |
|-------|------|-------------|-------------------|
| Spatial block CV | Yes | Yes | Required |
| Random split metrics | Optimistic | Optimistic | Supplement only |
| Open labels (not PFIb) | No (synthetic) | Schema only | DEP / 311 / HWM |
| Adaptive H3 | CLI/tests | Smoke | Paper analysis |
| `PFI_h(c, r)` scenarios | Yes | Yes | Yes |
| Hydrodynamic simulation | No | No | Optional external |
