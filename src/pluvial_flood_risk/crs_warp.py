"""CRS helpers: warp rasters/vectors to EPSG:4326 for H3 joins."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform


TARGET_CRS = "EPSG:4326"


def warp_raster_to_4326(
    src_path: Path | str,
    dst_path: Path | str,
    *,
    resampling: str = "bilinear",
    dst_nodata: float | None = None,
) -> Path:
    """
    Reproject a GeoTIFF to EPSG:4326 (WGS84 lon/lat).

    NYC DEM tiles are often EPSG:2263 (NAD83 / New York Long Island ftUS).
    3DEP exports may already be 4326 — this is a no-op copy when CRS matches.
    """
    from pluvial_flood_risk.raster import require_rasterio

    require_rasterio()
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import calculate_default_transform, reproject

    src_path = Path(src_path)
    dst_path = Path(dst_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    resampling_enum = getattr(Resampling, resampling, Resampling.bilinear)

    with rasterio.open(src_path) as src:
        src_crs = src.crs
        if src_crs is None:
            raise ValueError(f"{src_path} has no CRS; cannot warp.")
        if _crs_is_4326(src_crs):
            # Already lon/lat — stream copy with float32 elevation safety
            profile = src.profile.copy()
            profile.update(driver="GTiff", compress="deflate")
            with rasterio.open(dst_path, "w", **profile) as dst:
                dst.write(src.read())
            return dst_path

        transform, width, height = calculate_default_transform(
            src_crs,
            TARGET_CRS,
            src.width,
            src.height,
            *src.bounds,
        )
        profile = src.profile.copy()
        nodata = dst_nodata if dst_nodata is not None else src.nodata
        profile.update(
            crs=TARGET_CRS,
            transform=transform,
            width=width,
            height=height,
            nodata=nodata,
            compress="deflate",
        )
        with rasterio.open(dst_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=resampling_enum,
                    src_nodata=src.nodata,
                    dst_nodata=nodata,
                )
    return dst_path


def reproject_geojson_to_4326(
    src_path: Path | str,
    dst_path: Path | str | None = None,
    *,
    source_crs: str | None = None,
) -> Path:
    """
    Reproject a GeoJSON FeatureCollection to EPSG:4326.

    Uses pyproj Transformer when available; otherwise requires coordinates
    already in lon/lat (writes a warning and copies).
    """
    src_path = Path(src_path)
    dst_path = Path(dst_path) if dst_path else src_path
    data = json.loads(src_path.read_text(encoding="utf-8"))
    crs_name = source_crs or _geojson_crs_name(data)
    if crs_name is None or _name_is_4326(crs_name):
        if dst_path != src_path:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(json.dumps(data), encoding="utf-8")
        return dst_path

    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise ImportError(
            "Reprojecting non-WGS84 GeoJSON requires pyproj "
            "(bundled with rasterio). Install: pip install -e '.[raster]'"
        ) from exc

    transformer = Transformer.from_crs(crs_name, TARGET_CRS, always_xy=True)

    def _xy(x, y, z=None):
        lon, lat = transformer.transform(x, y)
        if z is None:
            return lon, lat
        return lon, lat, z

    features = data.get("features") or []
    out_features = []
    for feat in features:
        geom_obj = feat.get("geometry")
        if geom_obj is None:
            continue
        geom = shape(geom_obj)
        if geom.is_empty:
            continue
        warped = shp_transform(_xy, geom)
        out_features.append(
            {
                "type": "Feature",
                "properties": feat.get("properties") or {},
                "geometry": mapping(warped),
            }
        )

    out = {"type": "FeatureCollection", "features": out_features}
    # RFC7946 GeoJSON is always WGS84; strip legacy crs member
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(json.dumps(out), encoding="utf-8")
    return dst_path


def ensure_raster_4326(path: Path | str, *, inplace: bool = True) -> Path:
    """Warp ``path`` to EPSG:4326 if needed; optionally overwrite in place."""
    path = Path(path)
    from pluvial_flood_risk.raster import require_rasterio

    require_rasterio()
    import rasterio

    with rasterio.open(path) as src:
        if src.crs is not None and _crs_is_4326(src.crs):
            return path
    tmp = path.with_suffix(".4326.tif")
    warp_raster_to_4326(path, tmp)
    if inplace:
        tmp.replace(path)
        return path
    return tmp


def transform_bbox(
    bbox: tuple[float, float, float, float],
    src_crs: str,
    dst_crs: str = TARGET_CRS,
) -> tuple[float, float, float, float]:
    """Transform (minx, miny, maxx, maxy) between CRS."""
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise ImportError("bbox transform requires pyproj") from exc

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    minx, miny, maxx, maxy = bbox
    xs = [minx, minx, maxx, maxx]
    ys = [miny, maxy, miny, maxy]
    out_x, out_y = transformer.transform(xs, ys)
    return float(min(out_x)), float(min(out_y)), float(max(out_x)), float(max(out_y))


def _crs_is_4326(crs: Any) -> bool:
    try:
        return crs.to_epsg() == 4326
    except Exception:
        return _name_is_4326(str(crs))


def _name_is_4326(name: str) -> bool:
    u = name.upper()
    return "4326" in u or "CRS84" in u or "WGS 84" in u or "WGS84" in u


def _geojson_crs_name(data: dict) -> str | None:
    crs = data.get("crs")
    if isinstance(crs, dict):
        props = crs.get("properties") or {}
        name = props.get("name")
        if name:
            return str(name)
    return None
