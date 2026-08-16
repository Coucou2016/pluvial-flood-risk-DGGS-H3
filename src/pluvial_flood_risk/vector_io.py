"""Load vector flood / building / hydro layers (GeoJSON, GeoPackage)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry


VectorRecord = tuple[BaseGeometry, dict[str, Any]]


def load_vector_records(path: Path | str) -> list[VectorRecord]:
    """
    Load geometries + properties from GeoJSON (.geojson/.json) or GPKG (.gpkg).

    GeoJSON uses stdlib json + shapely (no geopandas). GPKG needs geopandas, fiona,
    or pyogrio. Coordinates are assumed EPSG:4326 unless a GPKG backend reprojects.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Vector file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".geojson", ".json"}:
        return _load_geojson(path)
    if suffix == ".gpkg":
        return _load_gpkg(path)
    raise ValueError(
        f"Unsupported vector format '{suffix}' for {path}. Use GeoJSON or GeoPackage."
    )


def load_vector_records_many(paths: Path | str | list[Path | str]) -> list[VectorRecord]:
    if isinstance(paths, (str, Path)):
        return load_vector_records(paths)
    records: list[VectorRecord] = []
    for p in paths:
        records.extend(load_vector_records(p))
    return records


def write_geojson_features(
    path: Path | str,
    geoms_and_props: list[tuple[BaseGeometry, dict[str, Any]]],
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for geom, props in geoms_and_props:
        features.append(
            {
                "type": "Feature",
                "properties": {k: _jsonable(v) for k, v in (props or {}).items()},
                "geometry": mapping(geom),
            }
        )
    collection = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(collection), encoding="utf-8")
    return path


def _jsonable(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _load_geojson(path: Path) -> list[VectorRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
    crs = data.get("crs")
    if isinstance(crs, dict):
        name = str(crs.get("properties", {}).get("name", ""))
        if name and "4326" not in name and "CRS84" not in name.upper():
            import warnings

            warnings.warn(
                f"{path} declares CRS {name}; H3 join assumes WGS84 lon/lat.",
                stacklevel=2,
            )

    if data.get("type") == "FeatureCollection":
        features = data.get("features") or []
    elif data.get("type") == "Feature":
        features = [data]
    elif "coordinates" in data:
        features = [{"type": "Feature", "geometry": data, "properties": {}}]
    else:
        raise ValueError(f"Unrecognized GeoJSON in {path}")

    records: list[VectorRecord] = []
    for feat in features:
        geom_obj = feat.get("geometry")
        if geom_obj is None:
            continue
        geom = shape(geom_obj)
        if geom.is_empty:
            continue
        props = feat.get("properties") or {}
        records.append((geom, dict(props)))
    return records


def _load_gpkg(path: Path) -> list[VectorRecord]:
    tried: list[str] = []

    try:
        import geopandas as gpd

        gdf = gpd.read_file(path)
        if gdf.crs is not None:
            crs_str = str(gdf.crs)
            if "4326" not in crs_str:
                gdf = gdf.to_crs("EPSG:4326")
        records: list[VectorRecord] = []
        props_df = gdf.drop(columns=["geometry"], errors="ignore")
        for geom, (_, row) in zip(gdf.geometry, props_df.iterrows(), strict=False):
            if geom is None or geom.is_empty:
                continue
            records.append((geom, {k: row[k] for k in props_df.columns}))
        return records
    except ImportError:
        tried.append("geopandas")

    try:
        import fiona
        from shapely.geometry import shape as shp_shape

        records = []
        with fiona.open(path) as src:
            for feat in src:
                geom_obj = feat.get("geometry")
                if geom_obj is None:
                    continue
                geom = shp_shape(geom_obj)
                if geom.is_empty:
                    continue
                records.append((geom, dict(feat.get("properties") or {})))
        return records
    except ImportError:
        tried.append("fiona")

    try:
        import pyogrio

        gdf = pyogrio.read_dataframe(path)
        if getattr(gdf, "crs", None) is not None and "4326" not in str(gdf.crs):
            gdf = gdf.to_crs("EPSG:4326")
        records = []
        props_df = gdf.drop(columns=["geometry"], errors="ignore")
        for geom, (_, row) in zip(gdf.geometry, props_df.iterrows(), strict=False):
            if geom is None or geom.is_empty:
                continue
            records.append((geom, {k: row[k] for k in props_df.columns}))
        return records
    except ImportError:
        if "pyogrio" not in tried:
            tried.append("pyogrio")
    except Exception:
        pass

    raise ImportError(
        f"Reading GeoPackage {path} requires geopandas, fiona, or pyogrio "
        f"(tried: {', '.join(tried) or 'none'}). GeoJSON does not need extra packages."
    )
