"""Download Lower Manhattan public layers into data/raw/nyc/ (EPSG:4326).

Socrata (data.cityofnewyork.us) may 403 from some networks; this module prefers
ArcGIS FeatureServer + USGS 3DEP / ScienceBase mirrors that stay public.

Does not download 7Analytics PFIb. Fixture fallback remains when fetch fails.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from shapely.geometry import Point, shape

from pluvial_flood_risk.config import NYC_MANHATTAN_BBOX, PROJECT_ROOT
from pluvial_flood_risk.schema_fixtures import FIXTURE_MARKER, NYC_SCHEMA_FILES
from pluvial_flood_risk.vector_io import write_geojson_features

USER_AGENT = "pluvial-flood-pipeline/0.1 (research; H3+ML paper scaffold)"
DEFAULT_OUT = PROJECT_ROOT / "data" / "raw" / "nyc"
MANIFEST_NAME = "DOWNLOAD_MANIFEST.json"

# USGS 3DEP ImageServer (meters elevation; request EPSG:4326)
_3DEP_EXPORT = (
    "https://elevation.nationalmap.gov/arcgis/rest/services/"
    "3DEPElevation/ImageServer/exportImage"
)

# NYC DEP stormwater via public ArcGIS Hub mirror. The service
# "New_York_City_Map_WFL1" holds three flood layers:
#   Layer 1 = "Moderate Flood with Current Sea Levels"  -> PRIMARY pluvial target
#   Layer 2 = "Moderate Flood with 2050 Sea Level Rise" -> sensitivity analysis
#   Layer 3 = "Extreme Flood with 2080 Sea Level Rise"  -> not used
# Layers 1-3 share the coded field Flooding_Category:
#   1 = Nuisance Flooding (>=4 in to <1 ft) and 2 = Deep and Contiguous Flooding
#   (>=1 ft), both hydrologic/hydraulic MODEL OUTPUTS from extreme-rainfall
#   simulations; 3 = Future High Tides (coastal tidal inundation).
# For the pluvial susceptibility target we therefore (a) use the CURRENT-sea-level
# layer 1 so the target reflects present-day rainfall flooding rather than a 2050
# climate scenario, (b) exclude category 3 (coastal, not pluvial), and (c) treat
# categories 1-2 as a model-derived pseudo-label, never as "observed" flooding.
_DEP_STORMWATER_CURRENT = (
    "https://services.arcgis.com/g8EzU2gNHvGpFUGY/ArcGIS/rest/services/"
    "New_York_City_Map_WFL1/FeatureServer/1/query"
)
_DEP_STORMWATER_2050SLR = (
    "https://services.arcgis.com/g8EzU2gNHvGpFUGY/ArcGIS/rest/services/"
    "New_York_City_Map_WFL1/FeatureServer/2/query"
)
# Only pluvial model classes; category 3 (Future High Tides) is dropped.
_DEP_WHERE = "Flooding_Category IN (1,2)"

# Official NYC MapHub building footprints view
_BUILDINGS = (
    "https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/"
    "BUILDING_view/FeatureServer/0/query"
)

# Sandy inundation — ArcGIS Online mirrors of NYC Open Data uyj8-7rv5 (Socrata often 403)
_SANDY_CANDIDATES = [
    (
        "arcgis_sandy_jzHs",
        "https://services9.arcgis.com/jzHsRPm3d1aMJuBp/arcgis/rest/services/"
        "Sandy_Inundation_Zone/FeatureServer/0/query",
    ),
    (
        "arcgis_sandy_RQcp",
        "https://services2.arcgis.com/RQcpPaCpMAXzUI5g/arcgis/rest/services/"
        "Sandy_Inundation_Zone/FeatureServer/0/query",
    ),
    (
        "arcgis_sandy_tutorials",
        "https://services2.arcgis.com/j80Jz20at6Bi0thr/arcgis/rest/services/"
        "Hurricane_Sandy_Inundation_Zone_(Tutorials)/FeatureServer/0/query",
    ),
    (
        "socrata_geojson",
        "https://data.cityofnewyork.us/api/geospatial/uyj8-7rv5?method=export&format=GeoJSON",
    ),
]

_IDA_ITEM = "https://www.sciencebase.gov/catalog/item/618975c8d34ec04fc9c5a049?format=json"

# 311 street flooding. Prefer the official NYC Open Data historical extract
# (2010–2019, dataset 76ig-c548) with a frozen 2010–2014 / Street Flooding (SJ)
# query, ordered pagination, and unique_key dedup. Derived ArcGIS/CDN layers are
# fallbacks only and must be labelled as unverified public mirrors.
_311_OFFICIAL_DATASET = "76ig-c548"
_311_OFFICIAL_LANDING = (
    "https://data.cityofnewyork.us/Social-Services/"
    "311-Service-Requests-from-2010-to-2019/76ig-c548"
)
_311_SODA_JSON = f"https://data.cityofnewyork.us/resource/{_311_OFFICIAL_DATASET}.json"
_311_SELECT_FIELDS = (
    "unique_key,created_date,agency,complaint_type,descriptor,"
    "latitude,longitude,incident_address,borough"
)
_311_DESCRIPTOR = "Street Flooding (SJ)"
_311_DATE_START = "2010-01-01T00:00:00"
_311_DATE_END_EXCLUSIVE = "2015-01-01T00:00:00"
_311_PAGE_SIZE = 1000
_311_CANDIDATES = [
    (
        "soda_76ig_c548_official",
        _311_SODA_JSON,
    ),
    (
        "arcgis_streetfloodtime_derived",
        "https://services.arcgis.com/ximI3fAlai1oq9BZ/arcgis/rest/services/"
        "streetfloodtime/FeatureServer/0/query",
    ),
    (
        "jsdelivr_street_flooding_csv_derived",
        "https://cdn.jsdelivr.net/gh/mebauer/nyc-311-street-flooding@main/data/"
        "street-flooding-complaints.csv",
    ),
    (
        "socrata_erm2_nwe9_wrong_vintage",
        "https://data.cityofnewyork.us/resource/erm2-nwe9.json",
    ),
]

# FloodNet: official NYC Open Data events (aq7i-eu5q) + sensor metadata (kb2e-tjy3).
# Downloaded for held-out external validation only; never a default training label.
# Do not treat the legacy api.floodnet.nyc/status probe as "no usable data".
_FLOODNET_EVENTS_DATASET = "aq7i-eu5q"
_FLOODNET_SENSORS_DATASET = "kb2e-tjy3"
_FLOODNET_OPEN_DATA = f"https://data.cityofnewyork.us/d/{_FLOODNET_EVENTS_DATASET}"
_FLOODNET_SENSORS_LANDING = f"https://data.cityofnewyork.us/d/{_FLOODNET_SENSORS_DATASET}"
_DEP_OPEN_DATA_LANDING = (
    "https://data.cityofnewyork.us/Environment/NYC-Stormwater-Flood-Maps/9i7c-xyvv"
)
_DEP_ADAPTNYC_LANDING = "https://www.nyc.gov/content/climate/pages/initiatives/adaptnyc"

# Annual NLCD fractional impervious (0–100%) via Esri ImageServer; scale to 0–1
_NLCD_IMPERVIOUS = (
    "https://di-nlcd.img.arcgis.com/arcgis/rest/services/"
    "USA_NLCD_Annual_LandCover_Fractional_Impervious_Surface/ImageServer/exportImage"
)

# USGS NHDPlus High Resolution (hydro.nationalmap.gov) — flowlines + waterbodies
# Lower Manhattan has few classic inland streams; expect tidal rivers / shoreline /
# artificial channels. Still valid as a distance-to-water proxy for dist_stream_m.
_NHDPLUS_HR = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer"
_NHD_HYDRO_LAYERS = [
    (3, "NetworkNHDFlowline", "flowline"),
    (4, "NonNetworkNHDFlowline", "flowline"),
    (8, "NHDArea", "water_area"),
    (9, "NHDWaterbody", "waterbody"),
]

_OVERPASS = "https://overpass-api.de/api/interpreter"


@dataclass
class LayerResult:
    name: str
    path: str | None
    status: str  # downloaded | skipped | failed | fixture_kept | kept_prior
    source: str | None = None
    n_features: int | None = None
    detail: str | None = None


@dataclass
class DownloadReport:
    bbox: list[float]
    out_dir: str
    started_at: str
    finished_at: str | None = None
    layers: list[LayerResult] = field(default_factory=list)
    assembly_ready: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bbox": self.bbox,
            "out_dir": self.out_dir,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "assembly_ready": self.assembly_ready,
            "notes": self.notes,
            "layers": [asdict(x) for x in self.layers],
        }


def download_nyc_layers(
    out_dir: Path | str | None = None,
    bbox: tuple[float, float, float, float] = NYC_MANHATTAN_BBOX,
    *,
    dem_size: tuple[int, int] = (500, 600),
    include_311: bool = True,
    include_sandy: bool = True,
    include_impervious: bool = True,
    include_event_rainfall: bool = True,
    event_rainfall_mm_h: float = 75.0,
    include_hydro: bool = True,
    keep_fixture_for_missing: bool = False,
    progress: Callable[[str], None] | None = None,
) -> DownloadReport:
    """
    Fetch public layers clipped to ``bbox`` into ``out_dir`` as EPSG:4326 files.

    On partial success: removes SCHEMA_FIXTURE.txt when DEM + DEP stormwater
    are live so ``build_nyc_h3.py`` can set ``assembly_mode=opendata``.
    Missing optional layers stay absent (synthetic fill) unless
    ``keep_fixture_for_missing`` is True.
    """
    out_dir = Path(out_dir or DEFAULT_OUT)
    out_dir.mkdir(parents=True, exist_ok=True)
    log = progress or (lambda _m: None)
    report = DownloadReport(
        bbox=list(bbox),
        out_dir=str(out_dir),
        started_at=_now(),
        notes=[
            "Lower Manhattan bbox subset (configs/nyc.yaml). Not citywide 1ft DEM.",
            "Socrata may be blocked; ArcGIS/USGS/CDN mirrors used when needed.",
            "Not 7Analytics PFIb.",
        ],
    )

    # --- DEM (3DEP) ---
    dem_path = out_dir / "dem.tif"
    try:
        log("Downloading USGS 3DEP DEM subset…")
        _download_3dep_dem(bbox, dem_path, size=dem_size)
        from pluvial_flood_risk.crs_warp import ensure_raster_4326

        ensure_raster_4326(dem_path)
        report.layers.append(
            LayerResult("dem", str(dem_path), "downloaded", "USGS 3DEP ImageServer", detail="EPSG:4326 GeoTIFF")
        )
    except Exception as exc:
        report.layers.append(_failed_or_kept("dem", dem_path, "USGS 3DEP", exc, min_bytes=1000))
        log(f"DEM failed: {exc}")

    # --- DEP stormwater (model-derived pluvial classes 1–2; category 3 excluded) ---
    # Official NYC Open Data landing: 9i7c-xyvv. Geospatial SODA export observed as
    # HTTP 400, so production uses the public AdaptNYC/ArcGIS FeatureServer mirror
    # with official_identity_verified=false. Layer 1 = primary; Layer 2 = SLR only.
    dep_path = out_dir / "dep_stormwater_flood.geojson"
    dep_slr_path = out_dir / "dep_stormwater_flood_2050slr.geojson"
    try:
        log("Downloading DEP stormwater flood polygons (categories 1–2, current sea levels)…")
        n = _download_arcgis_geojson(
            _DEP_STORMWATER_CURRENT, bbox, dep_path, page_size=2000, where=_DEP_WHERE
        )
        report.layers.append(
            LayerResult(
                "dep_stormwater_flood",
                str(dep_path),
                "downloaded",
                (
                    "public_mirror ArcGIS FeatureServer Layer 1 (Moderate Flood, Current Sea Levels; "
                    "category 3 excluded). "
                    f"Official landing {_DEP_OPEN_DATA_LANDING}; AdaptNYC {_DEP_ADAPTNYC_LANDING}; "
                    "official_identity_verified=false"
                ),
                n_features=n,
                detail=f"service={_DEP_STORMWATER_CURRENT}",
            )
        )
    except Exception as exc:
        report.layers.append(_failed_or_kept("dep_stormwater_flood", dep_path, "ArcGIS DEP", exc))
        log(f"DEP stormwater failed: {exc}")

    try:
        log("Downloading DEP stormwater 2050 SLR sensitivity polygons (categories 1–2)…")
        n_slr = _download_arcgis_geojson(
            _DEP_STORMWATER_2050SLR, bbox, dep_slr_path, page_size=2000, where=_DEP_WHERE
        )
        report.layers.append(
            LayerResult(
                "dep_stormwater_flood_2050slr",
                str(dep_slr_path),
                "downloaded",
                (
                    "public_mirror ArcGIS FeatureServer Layer 2 (2050 SLR; category 3 excluded). "
                    f"Official landing {_DEP_OPEN_DATA_LANDING}; official_identity_verified=false"
                ),
                n_features=n_slr,
            )
        )
    except Exception as exc:
        report.layers.append(_failed_or_kept("dep_stormwater_flood_2050slr", dep_slr_path, "ArcGIS DEP", exc))
        log(f"DEP stormwater 2050 SLR failed: {exc}")

    # --- Buildings ---
    bldg_path = out_dir / "building_footprints.geojson"
    try:
        log("Downloading building footprints…")
        n = _download_arcgis_geojson(
            _BUILDINGS,
            bbox,
            bldg_path,
            page_size=2000,
            out_fields="*",
        )
        report.layers.append(
            LayerResult(
                "building_footprints",
                str(bldg_path),
                "downloaded",
                "NYC MapHub BUILDING_view",
                n_features=n,
            )
        )
    except Exception as exc:
        report.layers.append(_failed_or_kept("building_footprints", bldg_path, "BUILDING_view", exc))
        log(f"Buildings failed: {exc}")

    # --- Ida HWM ---
    ida_path = out_dir / "usgs_ida_hwm.geojson"
    try:
        log("Downloading USGS Ida HWM points…")
        n = _download_ida_hwm(ida_path, bbox=bbox)
        report.layers.append(
            LayerResult(
                "usgs_ida_hwm",
                str(ida_path),
                "downloaded",
                "USGS ScienceBase P9OMBJPQ",
                n_features=n,
            )
        )
    except Exception as exc:
        report.layers.append(_failed_or_kept("usgs_ida_hwm", ida_path, "ScienceBase", exc))
        log(f"Ida HWM failed: {exc}")

    # --- 311 ---
    if include_311:
        path_311 = out_dir / "flooding_311.geojson"
        try:
            log("Downloading 311 flooding subset…")
            src, n = _download_311_flooding(path_311, bbox=bbox)
            report.layers.append(
                LayerResult("flooding_311", str(path_311), "downloaded", src, n_features=n)
            )
        except Exception as exc:
            kept = _failed_or_kept("flooding_311", path_311, "311 mirrors", exc)
            report.layers.append(kept)
            log(f"311 failed (SODA often blocked): {exc}")
            if keep_fixture_for_missing and kept.status == "failed":
                report.notes.append("311 left for fixture writer if build --fixtures")

    # --- Sandy negative control ---
    if include_sandy:
        sandy_path = out_dir / "fema_sandy.geojson"
        try:
            log("Downloading Sandy inundation (negative control)…")
            src, n = _download_sandy(sandy_path, bbox=bbox)
            report.layers.append(
                LayerResult("fema_sandy", str(sandy_path), "downloaded", src, n_features=n)
            )
        except Exception as exc:
            report.layers.append(_failed_or_kept("fema_sandy", sandy_path, "Sandy mirrors", exc))
            log(f"Sandy failed: {exc}")

    # --- Impervious / NLCD ---
    if include_impervious:
        imp_path = out_dir / "impervious.tif"
        try:
            log("Downloading NLCD fractional impervious subset…")
            _download_nlcd_impervious(bbox, imp_path, size=dem_size)
            from pluvial_flood_risk.crs_warp import ensure_raster_4326

            ensure_raster_4326(imp_path)
            report.layers.append(
                LayerResult(
                    "impervious",
                    str(imp_path),
                    "downloaded",
                    "Esri Annual NLCD Fractional Impervious ImageServer",
                    detail="EPSG:4326 GeoTIFF, values scaled to fraction 0–1",
                )
            )
        except Exception as exc:
            report.layers.append(
                _failed_or_kept("impervious", imp_path, "NLCD ImageServer", exc, min_bytes=500)
            )
            log(f"Impervious failed: {exc}")
    else:
        report.layers.append(
            LayerResult(
                "impervious",
                None,
                "skipped",
                None,
                detail="include_impervious=False",
            )
        )

    # --- Optional Ida-like event rainfall grid ---
    if include_event_rainfall:
        rain_path = out_dir / "event_rainfall.tif"
        try:
            log(f"Writing event_rainfall.tif ({event_rainfall_mm_h} mm/h constant)…")
            _write_constant_rainfall(bbox, rain_path, mm_h=event_rainfall_mm_h, size=dem_size)
            report.layers.append(
                LayerResult(
                    "event_rainfall",
                    str(rain_path),
                    "downloaded",
                    "synthetic_constant_grid",
                    detail=f"Uniform {event_rainfall_mm_h} mm/h over bbox (Ida-like scenario hook; not gauge radar)",
                )
            )
        except Exception as exc:
            report.layers.append(
                LayerResult("event_rainfall", None, "failed", "event_rainfall", detail=str(exc))
            )
            log(f"event_rainfall failed: {exc}")

    if include_hydro:
        hydro_path = out_dir / "hydro_streams.geojson"
        try:
            log("Downloading hydro (NHDPlus HR flowlines/waterbodies; OSM fallback)…")
            src, n, detail = _download_hydro(hydro_path, bbox=bbox)
            report.layers.append(
                LayerResult(
                    "hydro_streams",
                    str(hydro_path),
                    "downloaded",
                    src,
                    n_features=n,
                    detail=detail,
                )
            )
        except Exception as exc:
            report.layers.append(_failed_or_kept("hydro_streams", hydro_path, "NHD/OSM hydro", exc))
            log(f"Hydro failed: {exc}")
    else:
        report.layers.append(
            LayerResult(
                "hydro_streams",
                None,
                "skipped",
                "NHD",
                detail="include_hydro=False",
            )
        )

    # FloodNet: download official aq7i-eu5q + kb2e-tjy3 for held-out validation only.
    # Never added to training labels (labels.include_floodnet remains False).
    floodnet_path = out_dir / "floodnet_sensors.geojson"
    try:
        log("Downloading FloodNet sensors+events (held-out only; aq7i-eu5q / kb2e-tjy3)…")
        from pluvial_flood_risk.floodnet import download_floodnet_heldout

        fn_meta = download_floodnet_heldout(out_dir, bbox=bbox)
        report.layers.append(
            LayerResult(
                "floodnet",
                str(floodnet_path) if floodnet_path.exists() else None,
                "downloaded",
                (
                    f"NYC Open Data {_FLOODNET_EVENTS_DATASET}+{_FLOODNET_SENSORS_DATASET} "
                    "(held-out external validation only; not a training label)"
                ),
                n_features=int(fn_meta.get("n_sensors_in_bbox") or 0),
                detail=(
                    f"events={fn_meta.get('n_events_citywide')}; "
                    f"sensors_citywide={fn_meta.get('n_sensors_citywide')}; "
                    f"sensors_bbox={fn_meta.get('n_sensors_in_bbox')}; "
                    f"landing={_FLOODNET_OPEN_DATA}"
                ),
            )
        )
    except Exception as exc:
        report.layers.append(
            LayerResult(
                "floodnet",
                None,
                "skipped",
                "FloodNet",
                detail=(
                    f"download failed ({exc}); datasets remain public at "
                    f"{_FLOODNET_OPEN_DATA} and {_FLOODNET_SENSORS_LANDING}; "
                    "reserved for held-out validation — do not claim data unavailable"
                ),
            )
        )
        try:
            from pluvial_flood_risk.floodnet import write_floodnet_stub

            write_floodnet_stub(out_dir)
        except Exception:
            pass

    dem_ok = dem_path.exists() and dem_path.stat().st_size > 1000
    dep_ok = dep_path.exists() and dep_path.stat().st_size > 100
    report.assembly_ready = dem_ok and dep_ok

    marker = out_dir / FIXTURE_MARKER
    if report.assembly_ready:
        if marker.exists():
            marker.unlink()
            report.notes.append(f"Removed {FIXTURE_MARKER} — live DEM+DEP present.")
        removed = _remove_undownloaded_schema_files(out_dir, report)
        if removed:
            report.notes.append(
                "Removed undownloaded schema files so fixture geometries are not "
                f"mixed into opendata mode: {', '.join(removed)}"
            )
        _scrub_fixture_properties_note(report)
        try:
            from pluvial_flood_risk.floodnet import write_floodnet_stub

            write_floodnet_stub(out_dir)
        except Exception:
            pass
    else:
        report.notes.append(
            f"Not assembly-ready (need dem.tif + dep_stormwater_flood.geojson). "
            f"Keep or regenerate {FIXTURE_MARKER} via build_nyc_h3.py --fixtures."
        )

    report.finished_at = _now()
    manifest_path = out_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    report.notes.append(f"Wrote {manifest_path}")
    return report


def _download_3dep_dem(
    bbox: tuple[float, float, float, float],
    out_path: Path,
    size: tuple[int, int] = (500, 600),
) -> Path:
    minx, miny, maxx, maxy = bbox
    params = {
        "bbox": f"{minx},{miny},{maxx},{maxy}",
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{size[0]},{size[1]}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    }
    url = _3DEP_EXPORT + "?" + urllib.parse.urlencode(params)
    data = _http_get(url, timeout=180)
    if len(data) < 500 or data[:2] not in (b"II", b"MM"):
        # Sometimes returns HTML error
        raise RuntimeError(f"3DEP export did not return a TIFF ({len(data)} bytes)")
    out_path.write_bytes(data)
    # Tag nodata so zonal stats exclude mask fill
    try:
        import rasterio

        with rasterio.open(out_path, "r+") as ds:
            if ds.nodata is None:
                ds.nodata = -9999.0
    except Exception:
        pass
    return out_path


def _download_arcgis_geojson(
    query_url: str,
    bbox: tuple[float, float, float, float],
    out_path: Path,
    *,
    page_size: int = 2000,
    out_fields: str = "*",
    where: str = "1=1",
    max_allowable_offset: float | None = None,
) -> int:
    features = _query_arcgis_geojson_features(
        query_url,
        bbox,
        page_size=page_size,
        out_fields=out_fields,
        where=where,
        max_allowable_offset=max_allowable_offset,
    )
    collection = {"type": "FeatureCollection", "features": features}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(collection), encoding="utf-8")
    return len(features)


def _query_arcgis_geojson_features(
    query_url: str,
    bbox: tuple[float, float, float, float],
    *,
    page_size: int = 2000,
    out_fields: str = "*",
    where: str = "1=1",
    max_allowable_offset: float | None = None,
) -> list[dict]:
    minx, miny, maxx, maxy = bbox
    features: list[dict] = []
    offset = 0
    while True:
        params: dict[str, str] = {
            "where": where,
            "geometry": f"{minx},{miny},{maxx},{maxy}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultRecordCount": str(page_size),
            "resultOffset": str(offset),
        }
        if max_allowable_offset is not None:
            params["maxAllowableOffset"] = str(max_allowable_offset)
        url = query_url + "?" + urllib.parse.urlencode(params)
        raw = _http_get(url, timeout=180)
        payload = json.loads(raw.decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(str(payload["error"]))
        batch = payload.get("features") or []
        features.extend(batch)
        exceeded = bool((payload.get("properties") or {}).get("exceededTransferLimit"))
        if not batch or (len(batch) < page_size and not exceeded):
            break
        offset += len(batch)
        if offset > 200_000:
            break
        time.sleep(0.15)
    return features


def _download_hydro(
    out_path: Path,
    bbox: tuple[float, float, float, float],
) -> tuple[str, int, str]:
    """Fetch hydro geometries for ``dist_stream_m`` (NHDPlus HR, then OSM Overpass).

    Returns ``(source_name, n_features, detail)``. Honesty: Lower Manhattan coverage
    is mostly tidal river centerlines / waterbodies / shoreline — a distance-to-water
    proxy, not dense inland stream network.
    """
    last_err: Exception | None = None
    try:
        n, detail = _download_nhdplus_hr(out_path, bbox=bbox)
        if n > 0:
            return "usgs_nhdplus_hr", n, detail
        raise RuntimeError("NHDPlus HR returned 0 features in bbox")
    except Exception as exc:
        last_err = exc

    try:
        n, detail = _download_osm_water_overpass(out_path, bbox=bbox)
        if n > 0:
            return "osm_overpass_water", n, detail
        raise RuntimeError("Overpass returned 0 water features in bbox")
    except Exception as exc:
        raise RuntimeError(f"All hydro sources failed (NHD: {last_err}; OSM: {exc})") from exc


def _download_nhdplus_hr(
    out_path: Path,
    bbox: tuple[float, float, float, float],
) -> tuple[int, str]:
    """Combine NHDPlus HR flowlines + areas + waterbodies clipped to bbox."""
    # ~5–10 m simplify keeps Hudson/East River polygons tractable
    max_off = 0.00008
    merged: list[dict] = []
    counts: dict[str, int] = {}
    for layer_id, layer_name, role in _NHD_HYDRO_LAYERS:
        url = f"{_NHDPLUS_HR}/{layer_id}/query"
        try:
            batch = _query_arcgis_geojson_features(
                url,
                bbox,
                page_size=500,
                out_fields="OBJECTID,GNIS_NAME,FType,FCode",
                max_allowable_offset=max_off,
            )
        except Exception:
            # Some layers reject subset fields; retry with *
            batch = _query_arcgis_geojson_features(
                url,
                bbox,
                page_size=500,
                out_fields="*",
                max_allowable_offset=max_off,
            )
        for feat in batch:
            props = feat.setdefault("properties", {}) or {}
            feat["properties"] = props
            props.setdefault("source", "usgs_nhdplus_hr")
            props["nhd_layer"] = layer_name
            props["hydro_role"] = role
            props.setdefault(
                "proxy_note",
                "distance_to_water_proxy; LM is tidal river/shoreline-heavy, not inland streams",
            )
            merged.append(feat)
        counts[layer_name] = len(batch)
        time.sleep(0.2)

    if not merged:
        raise RuntimeError("NHDPlus HR layers empty for bbox")

    # Clip to bbox envelope so huge estuary polygons don't dominate disk/I/O
    clipped = _clip_geojson_features_to_bbox(merged, bbox)
    if not clipped:
        clipped = merged

    collection = {"type": "FeatureCollection", "features": clipped}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(collection), encoding="utf-8")
    detail = (
        "NHDPlus HR flowlines+areas+waterbodies; "
        + ", ".join(f"{k}={v}" for k, v in counts.items())
        + f"; wrote {len(clipped)} after bbox clip. "
        "Honesty: mostly tidal rivers/waterbodies for LM — dist_stream_m is "
        "distance-to-water, not classic stream proximity."
    )
    return len(clipped), detail


def _download_osm_water_overpass(
    out_path: Path,
    bbox: tuple[float, float, float, float],
) -> tuple[int, str]:
    """Fallback: OSM waterways + natural=water via Overpass (EPSG:4326)."""
    minx, miny, maxx, maxy = bbox
    # Overpass bbox is (south,west,north,east)
    south, west, north, east = miny, minx, maxy, maxx
    query = f"""
    [out:json][timeout:90];
    (
      way["waterway"]({south},{west},{north},{east});
      relation["waterway"]({south},{west},{north},{east});
      way["natural"="water"]({south},{west},{north},{east});
      relation["natural"="water"]({south},{west},{north},{east});
      way["landuse"="basin"]({south},{west},{north},{east});
    );
    out geom;
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        _OVERPASS,
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    records: list[tuple[Any, dict]] = []
    for el in payload.get("elements") or []:
        tags = el.get("tags") or {}
        geom = _overpass_element_to_shapely(el)
        if geom is None or geom.is_empty:
            continue
        role = "waterway" if "waterway" in tags else "waterbody"
        props = {
            "source": "osm_overpass_water",
            "hydro_role": role,
            "osm_id": el.get("id"),
            "name": tags.get("name"),
            "waterway": tags.get("waterway"),
            "natural": tags.get("natural"),
            "proxy_note": "OSM fallback distance-to-water proxy for Lower Manhattan",
        }
        records.append((geom, props))

    if not records:
        raise RuntimeError("Overpass water query empty")
    write_geojson_features(out_path, records)
    detail = (
        f"OSM Overpass waterway/natural=water ({len(records)} geoms). "
        "Fallback when NHD unavailable; still a water-proximity proxy."
    )
    return len(records), detail


def _overpass_element_to_shapely(el: dict) -> Any | None:
    """Build shapely geometry from an Overpass ``out geom`` element."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union

    etype = el.get("type")
    if etype == "way":
        coords = [(n["lon"], n["lat"]) for n in (el.get("geometry") or []) if "lon" in n and "lat" in n]
        if len(coords) < 2:
            return None
        tags = el.get("tags") or {}
        if tags.get("natural") == "water" or tags.get("landuse") == "basin":
            if len(coords) >= 4 and coords[0] == coords[-1]:
                return Polygon(coords)
            if len(coords) >= 3:
                try:
                    return Polygon(coords)
                except Exception:
                    return LineString(coords)
        return LineString(coords)
    if etype == "relation":
        polys = []
        lines = []
        for member in el.get("members") or []:
            if member.get("type") != "way":
                continue
            coords = [
                (n["lon"], n["lat"]) for n in (member.get("geometry") or []) if "lon" in n and "lat" in n
            ]
            if len(coords) < 2:
                continue
            if member.get("role") in ("outer", "inner") or len(coords) >= 4:
                try:
                    if coords[0] != coords[-1] and len(coords) >= 3:
                        coords = coords + [coords[0]]
                    polys.append(Polygon(coords))
                    continue
                except Exception:
                    pass
            lines.append(LineString(coords))
        geoms = [g for g in polys + lines if g is not None and not g.is_empty]
        if not geoms:
            return None
        return unary_union(geoms) if len(geoms) > 1 else geoms[0]
    return None


def _clip_geojson_features_to_bbox(
    features: list[dict],
    bbox: tuple[float, float, float, float],
) -> list[dict]:
    """Intersect geometries with bbox polygon; drop empties."""
    from shapely.geometry import box, mapping

    minx, miny, maxx, maxy = bbox
    # Slight pad so shoreline just outside still contributes
    pad = 0.002
    clip = box(minx - pad, miny - pad, maxx + pad, maxy + pad)
    out: list[dict] = []
    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            g = shape(geom)
            if g.is_empty:
                continue
            inter = g.intersection(clip)
            if inter.is_empty:
                continue
            out.append(
                {
                    "type": "Feature",
                    "properties": dict(feat.get("properties") or {}),
                    "geometry": mapping(inter),
                }
            )
        except Exception:
            continue
    return out



def _download_ida_hwm(out_path: Path, bbox: tuple[float, float, float, float] | None = None) -> int:
    """All NYC Ida HWMs (~83). ``bbox`` retained for API symmetry."""
    del bbox
    meta = json.loads(_http_get(_IDA_ITEM, timeout=90).decode("utf-8"))
    files = meta.get("files") or []
    csv_url = None
    for f in files:
        if f.get("name") == "FilteredHWMs_NewYork.csv":
            csv_url = f.get("downloadUri") or f.get("url")
            break
    if not csv_url:
        raise RuntimeError("FilteredHWMs_NewYork.csv not listed on ScienceBase item")

    text = _http_get(csv_url, timeout=120).decode("utf-8", errors="replace")
    # File may start with a citation line before the header
    lines = text.splitlines()
    header_idx = 0
    for i, line in enumerate(lines):
        low = line.lower()
        if "latitude" in low and "longitude" in low:
            header_idx = i
            break
    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text))
    records = []
    for row in reader:
        if not row:
            continue
        lon = _float_field(row, ("longitude_dd", "longitude", "lon", "LONGITUDE"))
        lat = _float_field(row, ("latitude_dd", "latitude", "lat", "LATITUDE"))
        if lon is None or lat is None:
            continue
        props = {
            "hwm_id": row.get("hwm_id") or row.get("HWM_ID") or row.get("site_id"),
            "event": "Ida",
            "height_above_gnd": _float_field(
                row, ("height_above_gnd", "elev_ft", "elevation_ft")
            ),
            "source": "usgs_sciencebase_P9OMBJPQ",
            "hwm_quality": row.get("hwmQualityName") or row.get("hwm_quality"),
            "county": row.get("countyName") or row.get("county"),
        }
        records.append((Point(lon, lat), props))

    if not records:
        raise RuntimeError("Ida HWM CSV parsed zero lon/lat rows")
    write_geojson_features(out_path, records)
    return len(records)


def _download_311_flooding(out_path: Path, bbox: tuple[float, float, float, float]) -> tuple[str, int]:
    """Official 76ig-c548 first; derived ArcGIS/CDN only as labelled fallbacks."""
    last_err: Exception | None = None
    query_sidecar = out_path.with_name(out_path.stem + "_query.json")
    for name, url in _311_CANDIDATES:
        try:
            if name == "soda_76ig_c548_official":
                n, meta = _download_311_soda_official(url, out_path, bbox=bbox)
                if n <= 0:
                    raise RuntimeError(f"{name} returned 0 features in bbox")
                query_sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                return name, n
            if name.startswith("arcgis_") and url.endswith("/query"):
                n = _download_arcgis_geojson(url, bbox, out_path, page_size=2000)
                if n <= 0:
                    raise RuntimeError(f"{name} returned 0 features in bbox")
                n = _filter_311_geojson_date_window(out_path)
                if n <= 0:
                    raise RuntimeError(f"{name} had 0 features after 2010-2014 date filter")
                _annotate_geojson_source(
                    out_path,
                    source=name,
                    extra={
                        "hazard": "pluvial_311",
                        "official_identity_verified": False,
                        "mirror_status": "public_derived_layer",
                        "producer_note": (
                            "ArcGIS streetfloodtime (owner jeichen_GIS) is a derived "
                            "complaint layer, not an official NYC 311 extract. "
                            f"Preferred official dataset is {_311_OFFICIAL_DATASET}."
                        ),
                        "date_window": f"{_311_DATE_START} <= created < {_311_DATE_END_EXCLUSIVE}",
                    },
                )
                query_sidecar.write_text(
                    json.dumps(
                        {
                            "source": name,
                            "official_identity_verified": False,
                            "preferred_dataset": _311_OFFICIAL_DATASET,
                            "date_window": [_311_DATE_START, _311_DATE_END_EXCLUSIVE],
                            "n_features": n,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                return name, n
            if name.startswith("jsdelivr_") or url.endswith(".csv"):
                n = _download_311_csv_mirror(url, out_path, bbox=bbox, source=name)
                if n <= 0:
                    raise RuntimeError(f"{name} returned 0 features in bbox")
                n = _filter_311_geojson_date_window(out_path)
                if n <= 0:
                    raise RuntimeError(f"{name} had 0 features after 2010-2014 date filter")
                return name, n
            n, meta = _download_311_soda_paginated(
                url,
                out_path,
                bbox=bbox,
                dataset_id="erm2-nwe9",
                include_date_filter=True,
            )
            if n <= 0:
                raise RuntimeError(f"{name} returned 0 features in bbox")
            query_sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            return name, n
        except Exception as exc:
            last_err = exc
            continue
    raise RuntimeError(f"All 311 sources failed: {last_err}")


def _311_where_clause(bbox: tuple[float, float, float, float], *, include_date: bool) -> str:
    minx, miny, maxx, maxy = bbox
    parts = [
        f"descriptor = '{_311_DESCRIPTOR}'",
        f"latitude between '{miny}' and '{maxy}'",
        f"longitude between '{minx}' and '{maxx}'",
    ]
    if include_date:
        parts.insert(
            1,
            f"created_date >= '{_311_DATE_START}' AND created_date < '{_311_DATE_END_EXCLUSIVE}'",
        )
    return " AND ".join(parts)


def _download_311_soda_official(
    url: str,
    out_path: Path,
    bbox: tuple[float, float, float, float],
) -> tuple[int, dict[str, Any]]:
    return _download_311_soda_paginated(
        url,
        out_path,
        bbox=bbox,
        dataset_id=_311_OFFICIAL_DATASET,
        include_date_filter=True,
        landing_page=_311_OFFICIAL_LANDING,
        official=True,
    )


def _download_311_soda_paginated(
    url: str,
    out_path: Path,
    bbox: tuple[float, float, float, float],
    *,
    dataset_id: str,
    include_date_filter: bool,
    landing_page: str | None = None,
    official: bool = False,
) -> tuple[int, dict[str, Any]]:
    """SODA JSON with frozen select/where/order, $offset pages, unique_key dedup."""
    base = url.split("?")[0]
    where = _311_where_clause(bbox, include_date=include_date_filter)
    page_hashes: list[str] = []
    by_key: dict[str, dict[str, Any]] = {}
    offset = 0
    while True:
        params = {
            "$select": _311_SELECT_FIELDS,
            "$where": where,
            "$order": "unique_key",
            "$limit": str(_311_PAGE_SIZE),
            "$offset": str(offset),
        }
        full = base + "?" + urllib.parse.urlencode(params)
        raw = _http_get(full, timeout=90)
        page_hashes.append(hashlib.sha256(raw).hexdigest())
        payload = json.loads(raw.decode("utf-8"))
        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(str(payload))
        if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
            rows = []
            for feat in payload.get("features") or []:
                props = dict(feat.get("properties") or {})
                geom = feat.get("geometry") or {}
                coords = geom.get("coordinates") or [None, None]
                props.setdefault("longitude", coords[0])
                props.setdefault("latitude", coords[1])
                rows.append(props)
            payload = rows
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected 311 SODA payload")
        if not payload:
            break
        for row in payload:
            key = str(row.get("unique_key") or "").strip()
            if not key:
                continue
            by_key[key] = row
        if len(payload) < _311_PAGE_SIZE:
            break
        offset += len(payload)
        if offset > 200_000:
            break
        time.sleep(0.15)

    records = []
    for key in sorted(by_key):
        row = by_key[key]
        lon = _float_field(row, ("longitude",))
        lat = _float_field(row, ("latitude",))
        if lon is None or lat is None:
            continue
        records.append(
            (
                Point(lon, lat),
                {
                    "unique_key": key,
                    "complaint_type": row.get("complaint_type"),
                    "descriptor": row.get("descriptor"),
                    "created_date": row.get("created_date"),
                    "agency": row.get("agency"),
                    "incident_address": row.get("incident_address"),
                    "borough": row.get("borough"),
                    "source": f"nyc_311_soda_{dataset_id}",
                    "hazard": "pluvial_311",
                    "official_identity_verified": official,
                },
            )
        )
    write_geojson_features(out_path, records)
    meta = {
        "dataset_id": dataset_id,
        "landing_page": landing_page or f"https://data.cityofnewyork.us/d/{dataset_id}",
        "soda_url": base,
        "select": _311_SELECT_FIELDS,
        "where": where,
        "order": "unique_key",
        "page_size": _311_PAGE_SIZE,
        "date_start": _311_DATE_START if include_date_filter else None,
        "date_end_exclusive": _311_DATE_END_EXCLUSIVE if include_date_filter else None,
        "descriptor": _311_DESCRIPTOR,
        "bbox": list(bbox),
        "n_pages": len(page_hashes),
        "page_sha256": page_hashes,
        "n_unique_keys": len(by_key),
        "n_features_written": len(records),
        "official_identity_verified": official,
        "retrieved_utc": _now(),
    }
    return len(records), meta


def _parse_311_created_date(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text.replace("Z", ""), fmt)
        except ValueError:
            continue
    return None


def _filter_311_geojson_date_window(path: Path) -> int:
    """Keep 2010–2014 records when a created-date field is present; dedup if possible."""
    data = json.loads(path.read_text(encoding="utf-8"))
    feats = data.get("features") or []
    start = datetime(2010, 1, 1)
    end = datetime(2015, 1, 1)
    kept: list[dict] = []
    seen: set[str] = set()
    for feat in feats:
        props = feat.get("properties") or {}
        created = None
        for key in ("created_date", "Created_Da", "Created Date", "created"):
            if key in props:
                created = _parse_311_created_date(props.get(key))
                if created is not None:
                    break
        if created is not None and not (start <= created < end):
            continue
        uniq = str(props.get("unique_key") or props.get("Unique Key") or props.get("FID") or "")
        if uniq:
            if uniq in seen:
                continue
            seen.add(uniq)
        kept.append(feat)
    data["features"] = kept
    path.write_text(json.dumps(data), encoding="utf-8")
    return len(kept)


def _download_311_soda(url: str, out_path: Path, bbox: tuple[float, float, float, float]) -> int:
    """Back-compat wrapper: paginated SODA with the frozen 2010–2014 filter."""
    n, _meta = _download_311_soda_paginated(
        url,
        out_path,
        bbox=bbox,
        dataset_id="legacy",
        include_date_filter=True,
    )
    return n


def _download_311_csv_mirror(
    url: str,
    out_path: Path,
    bbox: tuple[float, float, float, float],
    *,
    source: str,
) -> int:
    """Community CDN mirror of NYC Street Flooding (SJ) complaints (SODA often 403)."""
    raw = _http_get(url, timeout=180)
    text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    minx, miny, maxx, maxy = bbox
    records = []
    for row in reader:
        lon = _float_field(row, ("longitude", "Longitude", "lng"))
        lat = _float_field(row, ("latitude", "Latitude", "lat"))
        if lon is None or lat is None:
            continue
        if not (minx <= lon <= maxx and miny <= lat <= maxy):
            continue
        records.append(
            (
                Point(lon, lat),
                {
                    "unique_key": row.get("unique_key") or row.get("Unique Key"),
                    "complaint_type": row.get("complaint_type") or row.get("Complaint Type"),
                    "descriptor": row.get("descriptor") or row.get("Descriptor"),
                    "created_date": row.get("created_date") or row.get("Created Date"),
                    "source": source,
                    "hazard": "pluvial_311",
                },
            )
        )
    if not records:
        raise RuntimeError("CSV mirror had no points in bbox")
    write_geojson_features(out_path, records)
    return len(records)


def _annotate_geojson_source(path: Path, *, source: str, extra: dict[str, Any] | None = None) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for feat in data.get("features") or []:
        props = feat.setdefault("properties", {})
        props.setdefault("source", source)
        if extra:
            for k, v in extra.items():
                props.setdefault(k, v)
    path.write_text(json.dumps(data), encoding="utf-8")


def _download_nlcd_impervious(
    bbox: tuple[float, float, float, float],
    out_path: Path,
    size: tuple[int, int] = (500, 600),
) -> Path:
    """Export Annual NLCD fractional impervious (percent) and scale to 0–1 fraction."""
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds

    minx, miny, maxx, maxy = bbox
    params = {
        "bbox": f"{minx},{miny},{maxx},{maxy}",
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{size[0]},{size[1]}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    }
    url = _NLCD_IMPERVIOUS + "?" + urllib.parse.urlencode(params)
    data = _http_get(url, timeout=180)
    if len(data) < 500 or data[:2] not in (b"II", b"MM"):
        raise RuntimeError(f"NLCD export did not return a TIFF ({len(data)} bytes)")

    with MemoryFile(data) as mem, mem.open() as src:
        arr = src.read(1).astype(np.float32)
        # NLCD fractional impervious is percent 0–100
        vmax = float(np.nanmax(arr)) if arr.size else 0.0
        if vmax > 1.5:
            arr = arr / 100.0
        arr = np.clip(arr, 0.0, 1.0)
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="float32",
            count=1,
            crs="EPSG:4326",
            transform=src.transform if src.transform else from_bounds(minx, miny, maxx, maxy, size[0], size[1]),
            nodata=-9999.0,
            compress="deflate",
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(arr, 1)
    return out_path


def _write_constant_rainfall(
    bbox: tuple[float, float, float, float],
    out_path: Path,
    *,
    mm_h: float = 75.0,
    size: tuple[int, int] = (100, 120),
) -> Path:
    """Tiny constant rainfall GeoTIFF (scenario hook; not radar/gauge observations)."""
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    minx, miny, maxx, maxy = bbox
    w, h = size
    transform = from_bounds(minx, miny, maxx, maxy, w, h)
    arr = np.full((h, w), float(mm_h), dtype=np.float32)
    profile = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -9999.0,
        "compress": "deflate",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(arr, 1)
    return out_path


def _download_sandy(out_path: Path, bbox: tuple[float, float, float, float]) -> tuple[str, int]:
    last_err: Exception | None = None
    for name, url in _SANDY_CANDIDATES:
        try:
            if "FeatureServer" in url and url.endswith("/query"):
                n = _download_arcgis_geojson(url, bbox, out_path, page_size=2000)
                if n <= 0:
                    raise RuntimeError(f"{name} returned 0 features in bbox")
                _annotate_geojson_source(
                    out_path,
                    source=name,
                    extra={"event": "Sandy", "hazard": "coastal_surge"},
                )
                return name, n
            raw = _http_get(url, timeout=120)
            payload = json.loads(raw.decode("utf-8"))
            feats = payload.get("features") or []
            # clip to bbox
            clipped = []
            minx, miny, maxx, maxy = bbox
            for feat in feats:
                geom = feat.get("geometry")
                if geom is None:
                    continue
                g = shape(geom)
                if g.is_empty:
                    continue
                if g.intersects(
                    shape(
                        {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [minx, miny],
                                    [maxx, miny],
                                    [maxx, maxy],
                                    [minx, maxy],
                                    [minx, miny],
                                ]
                            ],
                        }
                    )
                ):
                    props = feat.get("properties") or {}
                    props.setdefault("event", "Sandy")
                    props.setdefault("hazard", "coastal_surge")
                    props.setdefault("source", name)
                    clipped.append((g, props))
            if not clipped and feats:
                # keep all if clip empty (layer may use different CRS already handled)
                for feat in feats:
                    g = shape(feat["geometry"])
                    props = feat.get("properties") or {}
                    props.setdefault("source", name)
                    clipped.append((g, props))
            if not clipped:
                raise RuntimeError(f"{name} produced empty clip")
            write_geojson_features(out_path, clipped)
            return name, len(clipped)
        except Exception as exc:
            last_err = exc
            continue
    raise RuntimeError(f"All Sandy sources failed: {last_err}")


def _scrub_fixture_properties_note(report: DownloadReport) -> None:
    missing = [
        layer.name
        for layer in report.layers
        if layer.status in ("failed", "skipped")
        and layer.name in ("flooding_311", "fema_sandy", "impervious", "hydro_streams")
    ]
    if missing:
        report.notes.append(
            "Live core layers present. Still missing/skipped ("
            + ", ".join(missing)
            + ") — assemble uses synthetic fill for those feature columns unless fixtures are forced."
        )
    else:
        report.notes.append(
            "Live core + optional layers present (311/Sandy/impervious/hydro when downloaded). "
            "Hydro in Lower Manhattan is mostly tidal river/waterbody — dist_stream_m is a "
            "distance-to-water proxy. event_rainfall constant grid is a scenario hook, not "
            "gauge/radar observations."
        )


def _failed_or_kept(
    name: str,
    path: Path,
    source: str,
    exc: Exception,
    *,
    min_bytes: int = 100,
) -> LayerResult:
    """On fetch failure, keep a prior non-trivial file instead of wiping it."""
    if path.exists() and path.stat().st_size >= min_bytes:
        return LayerResult(
            name,
            str(path),
            "kept_prior",
            source,
            detail=f"Fetch failed ({exc}); kept existing file ({path.stat().st_size} bytes)",
        )
    return LayerResult(name, None, "failed", source, detail=str(exc))


def _remove_undownloaded_schema_files(out_dir: Path, report: DownloadReport) -> list[str]:
    """Delete schema filenames that were not successfully downloaded (avoid fixture bleed)."""
    ok_names = {
        {
            "dem": "dem.tif",
            "dep_stormwater_flood": "dep_stormwater_flood.geojson",
            "building_footprints": "building_footprints.geojson",
            "usgs_ida_hwm": "usgs_ida_hwm.geojson",
            "flooding_311": "flooding_311.geojson",
            "fema_sandy": "fema_sandy.geojson",
            "hydro_streams": "hydro_streams.geojson",
            "impervious": "impervious.tif",
        }.get(layer.name, "")
        for layer in report.layers
        if layer.status in ("downloaded", "kept_prior") and layer.path
    }
    ok_names.discard("")
    removed: list[str] = []
    for fname in NYC_SCHEMA_FILES:
        if fname in ok_names:
            continue
        path = out_dir / fname
        if path.exists():
            path.unlink()
            removed.append(fname)
    return removed


def _http_get(url: str, timeout: float = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()[:300] if hasattr(exc, "read") else b""
            raise RuntimeError(f"HTTP {exc.code} for {url[:120]}… {body!r}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_exc = exc
            time.sleep(0.8 * attempt)
    raise RuntimeError(f"HTTP GET failed for {url[:120]}… {last_exc}") from last_exc


def _float_field(row: dict, keys: tuple[str, ...]) -> float | None:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            try:
                return float(row[k])
            except (TypeError, ValueError):
                continue
        for rk, rv in row.items():
            if rk is None:
                continue
            if str(rk).lower() == k.lower() and rv not in (None, ""):
                try:
                    return float(rv)
                except (TypeError, ValueError):
                    continue
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
