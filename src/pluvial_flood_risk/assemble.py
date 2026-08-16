"""Assemble an H3 feature (+ optional label) table from rasters/vectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from pluvial_flood_risk.config import (
    ASSEMBLY_FIXTURE,
    ASSEMBLY_HASH,
    ASSEMBLY_OPENDATA,
    FEATURE_COLUMNS,
    PROVENANCE_MIXED,
    PROVENANCE_OBSERVED,
    PROVENANCE_SYNTHETIC,
)
from pluvial_flood_risk.features import (
    building_density_from_vector,
    dist_stream_from_vector,
    engineer_features_for_cells,
)
from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_centers, cell_resolution
from pluvial_flood_risk.labels import attach_labels, attach_observed_labels
from pluvial_flood_risk.raster import (
    merge_raster_feature,
    zonal_flow_accum_from_dem,
    zonal_mean_raster_to_h3,
    zonal_slope_deg_from_dem,
)


@dataclass
class FeatureSources:
    dem_path: Path | None = None
    slope_path: Path | None = None
    impervious_path: Path | None = None
    buildings_path: Path | None = None
    hydro_path: Path | None = None
    flood_polygons_path: Path | list[Path] | None = None
    flood_points_paths: list[Path] = field(default_factory=list)
    coastal_path: Path | None = None
    event_rainfall_path: Path | None = None
    assembly_mode: str = ASSEMBLY_HASH

    def existing_layers(self) -> list[str]:
        names = []
        for label, path in (
            ("dem", self.dem_path),
            ("slope", self.slope_path),
            ("impervious", self.impervious_path),
            ("buildings", self.buildings_path),
            ("hydro", self.hydro_path),
            ("event_rainfall", self.event_rainfall_path),
        ):
            if path and Path(path).exists():
                names.append(label)
        if self.flood_polygons_path:
            paths = (
                self.flood_polygons_path
                if isinstance(self.flood_polygons_path, list)
                else [self.flood_polygons_path]
            )
            if any(Path(p).exists() for p in paths):
                names.append("flood_polygons")
        if any(Path(p).exists() for p in self.flood_points_paths):
            names.append("flood_points")
        if self.coastal_path and Path(self.coastal_path).exists():
            names.append("coastal_negative_control")
        return names


def discover_sources(raw_dir: Path | str, assembly_mode: str | None = None) -> FeatureSources:
    """Pick conventional filenames under ``data/raw`` or ``data/raw/nyc``."""
    raw_dir = Path(raw_dir)
    dem_globs = list((raw_dir / "dem").glob("*.tif")) if (raw_dir / "dem").is_dir() else []
    dem = _first_existing(
        raw_dir / "dem.tif",
        raw_dir / "dem" / "dem.tif",
        *dem_globs,
    )
    slope = _first_existing(raw_dir / "slope.tif", raw_dir / "dem" / "slope.tif")
    impervious = _first_existing(
        raw_dir / "impervious.tif",
        raw_dir / "landcover" / "impervious.tif",
        raw_dir / "landuse" / "corine_clc.tif",
    )
    buildings = _first_existing(
        raw_dir / "building_footprints.geojson",
        raw_dir / "buildings" / "building_footprints.geojson",
        raw_dir / "buildings" / "oslo_bygg.geojson",
    )
    hydro = _first_existing(
        raw_dir / "hydro_streams.geojson",
        raw_dir / "hydro" / "hydro_streams.geojson",
        raw_dir / "hydro" / "nve_elvenett.gpkg",
    )
    floods = _first_existing(
        raw_dir / "dep_stormwater_flood.geojson",
        raw_dir / "floods" / "dep_stormwater_flood.geojson",
        raw_dir / "floods" / "historical_pluvial.geojson",
    )
    points: list[Path] = []
    for cand in (
        raw_dir / "flooding_311.geojson",
        raw_dir / "usgs_ida_hwm.geojson",
        raw_dir / "floods" / "flooding_311.geojson",
        raw_dir / "floods" / "usgs_ida_hwm.geojson",
        raw_dir / "floodnet_sensors.geojson",
    ):
        if cand.exists():
            points.append(cand)
    coastal = _first_existing(
        raw_dir / "fema_sandy.geojson",
        raw_dir / "floods" / "fema_sandy.geojson",
        raw_dir / "sandy_inundation.geojson",
    )
    event_rain = _first_existing(
        raw_dir / "event_rainfall.tif",
        raw_dir / "rainfall" / "event_rainfall.tif",
        raw_dir / "rainfall" / "event.tif",
    )

    live = any(
        p is not None and Path(p).exists()
        for p in (dem, slope, impervious, buildings, hydro, floods)
    )
    mode = assembly_mode or (ASSEMBLY_OPENDATA if live else ASSEMBLY_HASH)
    return FeatureSources(
        dem_path=dem,
        slope_path=slope,
        impervious_path=impervious,
        buildings_path=buildings,
        hydro_path=hydro,
        flood_polygons_path=floods,
        flood_points_paths=points,
        coastal_path=coastal,
        event_rainfall_path=event_rain,
        assembly_mode=mode,
    )


def sources_from_config(cfg: dict) -> FeatureSources:
    paths = cfg.get("paths") or {}
    raw_dir = paths.get("raw_dir")
    if raw_dir and Path(raw_dir).is_dir() and not paths.get("dem"):
        discovered = discover_sources(raw_dir)
    else:
        discovered = FeatureSources()

    flood_points = paths.get("flood_points") or []
    if isinstance(flood_points, (str, Path)):
        flood_points = [flood_points]
    flood_points = [Path(p) for p in flood_points if p]

    labels_cfg = cfg.get("labels") or {}
    include_floodnet = bool(labels_cfg.get("include_floodnet", False))
    floodnet_cfg = _as_path(paths.get("floodnet"))
    if include_floodnet:
        from pluvial_flood_risk.floodnet import usable_floodnet_path

        floodnet_usable = usable_floodnet_path(floodnet_cfg) or usable_floodnet_path(
            Path(raw_dir) / "floodnet_sensors.geojson" if raw_dir else None
        )
        if floodnet_usable is not None and floodnet_usable not in flood_points:
            flood_points = list(flood_points) + [floodnet_usable]

    mode = str(cfg.get("assembly_mode") or cfg.get("data_provenance") or ASSEMBLY_HASH)
    if mode in ("synthetic", "hash_demo"):
        mode = ASSEMBLY_HASH
    elif mode in ("fixture",):
        mode = ASSEMBLY_FIXTURE
    elif mode in ("observed", "opendata"):
        mode = ASSEMBLY_OPENDATA

    return FeatureSources(
        dem_path=_as_path(paths.get("dem")) or discovered.dem_path,
        slope_path=_as_path(paths.get("slope")) or discovered.slope_path,
        impervious_path=_as_path(paths.get("impervious")) or discovered.impervious_path,
        buildings_path=_as_path(paths.get("buildings")) or discovered.buildings_path,
        hydro_path=_as_path(paths.get("hydro")) or discovered.hydro_path,
        flood_polygons_path=_as_path(paths.get("flood_polygons")) or discovered.flood_polygons_path,
        flood_points_paths=flood_points or discovered.flood_points_paths,
        coastal_path=_as_path(paths.get("coastal") or paths.get("sandy")) or discovered.coastal_path,
        event_rainfall_path=_as_path(paths.get("event_rainfall")) or discovered.event_rainfall_path,
        assembly_mode=mode,
    )


def assemble_feature_table(
    cells: list[str],
    rainfall_mm_h: float = 25.0,
    sources: FeatureSources | None = None,
    fallback_synthetic: bool = True,
) -> pd.DataFrame:
    """
    Build per-cell features. Hash/synthetic fills gaps when rasters/vectors are missing.
    """
    sources = sources or FeatureSources()
    df = engineer_features_for_cells(cells, rainfall_mm_h=rainfall_mm_h)
    synth_backup = df[FEATURE_COLUMNS].copy() if len(df) else df
    observed: set[str] = set()

    if sources.dem_path and Path(sources.dem_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.dem_path)
        df = merge_raster_feature(df, zonal, "elevation_m")
        observed.add("elevation_m")
        if not (sources.slope_path and Path(sources.slope_path).exists()):
            try:
                slope = zonal_slope_deg_from_dem(cells, sources.dem_path)
                df = df.drop(columns=["slope_deg"], errors="ignore")
                df = df.merge(slope, on="h3_index", how="left")
                observed.add("slope_deg")
            except ImportError:
                pass
        try:
            flow = zonal_flow_accum_from_dem(cells, sources.dem_path)
            df = df.drop(columns=["flow_accum_proxy"], errors="ignore")
            df = df.merge(flow, on="h3_index", how="left")
            observed.add("flow_accum_proxy")
        except ImportError:
            pass

    if sources.slope_path and Path(sources.slope_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.slope_path)
        df = merge_raster_feature(df, zonal, "slope_deg")
        observed.add("slope_deg")

    if sources.impervious_path and Path(sources.impervious_path).exists():
        zonal = zonal_mean_raster_to_h3(cells, sources.impervious_path)
        df = merge_raster_feature(df, zonal, "impervious_frac")
        df["land_cover_urban"] = (df["impervious_frac"] > 0.45).astype(np.float64)
        observed.update({"impervious_frac", "land_cover_urban"})

    if sources.buildings_path and Path(sources.buildings_path).exists():
        bldg = building_density_from_vector(cells, sources.buildings_path)
        df = df.drop(columns=["building_density"], errors="ignore")
        df = df.merge(bldg[["h3_index", "building_density"]], on="h3_index", how="left")
        observed.add("building_density")

    if sources.hydro_path and Path(sources.hydro_path).exists():
        dist = dist_stream_from_vector(cells, sources.hydro_path)
        df = df.drop(columns=["dist_stream_m"], errors="ignore")
        df = df.merge(dist, on="h3_index", how="left")
        observed.add("dist_stream_m")

    rainfall_source = "scenario_or_config"
    if sources.event_rainfall_path and Path(sources.event_rainfall_path).exists():
        try:
            from pluvial_flood_risk.event_rainfall import attach_event_rainfall_raster

            df = attach_event_rainfall_raster(df, sources.event_rainfall_path)
            # Event GeoTIFF may be a synthetic constant hook (see DOWNLOAD_MANIFEST).
            # Do not mark rainfall_mm_h as an observed static feature.
            rainfall_source = "event_raster"
        except ImportError:
            pass

    if not fallback_synthetic:
        for col in FEATURE_COLUMNS:
            if col not in observed and col != "rainfall_mm_h" and col in df.columns:
                df[col] = np.nan
    elif len(df):
        for col in FEATURE_COLUMNS:
            if col in df.columns and col in synth_backup.columns:
                df[col] = df[col].fillna(synth_backup[col])

    for col in ("elevation_m", "slope_deg", "flow_accum_proxy", "impervious_frac", "building_density", "dist_stream_m"):
        if col in df.columns:
            df[col] = df[col].astype(np.float64)

    n_static_cols = [c for c in FEATURE_COLUMNS if c != "rainfall_mm_h"]
    if not observed:
        feature_source = PROVENANCE_SYNTHETIC
    elif all(c in observed for c in n_static_cols):
        feature_source = PROVENANCE_OBSERVED
    else:
        feature_source = PROVENANCE_MIXED

    if cells:
        lons, lats = cell_centers(cells)
        df["lon"] = lons
        df["lat"] = lats
        df["h3_resolution"] = cell_resolution(cells[0])
    df["feature_source"] = feature_source
    df["assembly_mode"] = sources.assembly_mode
    df["observed_feature_cols"] = ",".join(sorted(observed)) if observed else ""
    df["rainfall_source"] = rainfall_source
    return df


def assemble_h3_table(
    bbox: tuple[float, float, float, float],
    resolution: int,
    rainfall_mm_h: float = 25.0,
    sources: FeatureSources | None = None,
    fallback_synthetic: bool = True,
    synthetic_label_threshold: float = 0.55,
) -> pd.DataFrame:
    """H3 cells + features + labels (observed join when flood files exist)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    cells = bbox_to_cells(min_lon, min_lat, max_lon, max_lat, resolution)
    sources = sources or FeatureSources()
    df = assemble_feature_table(
        cells,
        rainfall_mm_h=rainfall_mm_h,
        sources=sources,
        fallback_synthetic=fallback_synthetic,
    )

    label_paths: list[Path] = []
    if sources.flood_polygons_path:
        pps = (
            sources.flood_polygons_path
            if isinstance(sources.flood_polygons_path, list)
            else [sources.flood_polygons_path]
        )
        label_paths.extend(Path(p) for p in pps if Path(p).exists())
    label_paths.extend(Path(p) for p in sources.flood_points_paths if Path(p).exists())

    if label_paths:
        df = attach_observed_labels(df, label_paths)
    else:
        df = attach_labels(df, threshold=synthetic_label_threshold)

    if sources.coastal_path and Path(sources.coastal_path).exists():
        from pluvial_flood_risk.negative_control import attach_coastal_overlay

        df = attach_coastal_overlay(df, sources.coastal_path, prefix="sandy")
    return df


def assemble_label_scale_table(
    bbox: tuple[float, float, float, float],
    resolution: int,
    sources: FeatureSources | None = None,
    parent_label_df: pd.DataFrame | None = None,
    synthetic_label_threshold: float = 0.55,
) -> pd.DataFrame:
    """
    Lightweight fine H3 + labels for Jaccard / scale-loss ladders.

    Avoids slow DEP polygon area-fraction overlays at fine resolutions (R10+).
    Instead:
    - joins **point** open labels (311 / Ida HWM) at the fine resolution;
    - optionally inherits polygon/label scores from a coarser ``parent_label_df``
      via H3 parent mapping (``label_scale_mode=points_plus_parent_inherit``).

    Hotspots are open-label diagnostics — not ML scores / PFIb.
    """
    import h3

    min_lon, min_lat, max_lon, max_lat = bbox
    cells = bbox_to_cells(min_lon, min_lat, max_lon, max_lat, resolution)
    sources = sources or FeatureSources()
    if not cells:
        return pd.DataFrame(
            columns=[
                "h3_index",
                "lon",
                "lat",
                "h3_resolution",
                "flood_risk",
                "flood_class",
                "label_source",
                "assembly_mode",
                "feature_source",
                "label_scale_mode",
            ]
        )

    lons, lats = cell_centers(cells)
    df = pd.DataFrame(
        {
            "h3_index": cells,
            "lon": lons,
            "lat": lats,
            "h3_resolution": cell_resolution(cells[0]),
            "assembly_mode": sources.assembly_mode,
            "feature_source": "labels_only_diagnostics",
        }
    )

    point_paths = [Path(p) for p in sources.flood_points_paths if Path(p).exists()]
    if point_paths:
        df = attach_observed_labels(df, point_paths)
        point_risk = df["flood_risk"].to_numpy(dtype=np.float64)
    else:
        point_risk = np.zeros(len(df), dtype=np.float64)
        df["flood_risk"] = point_risk
        df["flood_class"] = 0
        df["label_source"] = "none"

    inherited = np.zeros(len(df), dtype=np.float64)
    mode = "points_only"
    if parent_label_df is not None and len(parent_label_df) and "h3_index" in parent_label_df.columns:
        value_col = (
            "flood_risk"
            if "flood_risk" in parent_label_df.columns
            else ("flood_area_frac" if "flood_area_frac" in parent_label_df.columns else None)
        )
        if value_col is not None:
            parent_res = int(parent_label_df["h3_resolution"].iloc[0]) if "h3_resolution" in parent_label_df.columns else None
            if parent_res is None:
                parent_res = cell_resolution(str(parent_label_df["h3_index"].iloc[0]))
            if parent_res < resolution:
                pmap = {
                    str(r.h3_index): float(getattr(r, value_col))
                    for r in parent_label_df[["h3_index", value_col]].itertuples(index=False)
                    if np.isfinite(getattr(r, value_col))
                }
                inherited = np.array(
                    [pmap.get(h3.cell_to_parent(str(c), parent_res), 0.0) for c in df["h3_index"]],
                    dtype=np.float64,
                )
                mode = "points_plus_parent_inherit"

    combined = np.maximum(point_risk, inherited)
    df["flood_risk"] = combined
    df["flood_class"] = (combined > 0).astype(int)
    if mode == "points_plus_parent_inherit":
        df["label_source"] = "observed_points_plus_parent"
    df["label_scale_mode"] = mode
    df["assembly_mode"] = sources.assembly_mode
    df["feature_source"] = "labels_only_diagnostics"

    if point_paths or mode == "points_plus_parent_inherit":
        return df

    # No points and no parent inherit → full assemble fallback (fixtures / demo).
    return assemble_h3_table(
        bbox,
        resolution,
        sources=sources,
        fallback_synthetic=True,
        synthetic_label_threshold=synthetic_label_threshold,
    )


def _first_existing(*candidates: Path) -> Path | None:
    for p in candidates:
        if p and Path(p).exists():
            return Path(p)
    return None


def _as_path(value) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)
