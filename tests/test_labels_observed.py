"""Observed polygon/point → H3 labels."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Point

from pluvial_flood_risk.config import PROVENANCE_OBSERVED, TARGET_CLASS_COLUMN, TARGET_COLUMN
from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_boundary_polygon, cell_center
from pluvial_flood_risk.labels import attach_observed_labels
from pluvial_flood_risk.vector_io import write_geojson_features


def test_polygon_area_fraction_on_matching_cell(tmp_path: Path):
    cells = bbox_to_cells(10.70, 59.90, 10.75, 59.95, 9)
    poly = cell_boundary_polygon(cells[0])
    path = write_geojson_features(tmp_path / "floods.geojson", [(poly, {"src": "test"})])
    df = pd.DataFrame({"h3_index": cells})
    out = attach_observed_labels(df, path)
    hit = out.loc[out["h3_index"] == cells[0]].iloc[0]
    assert hit["flood_area_frac"] > 0.9
    assert hit[TARGET_CLASS_COLUMN] == 1
    assert hit["label_source"] == PROVENANCE_OBSERVED
    assert (out[TARGET_CLASS_COLUMN] == 0).any()


def test_point_counts_at_cell_center(tmp_path: Path):
    cells = bbox_to_cells(10.70, 59.90, 10.74, 59.94, 9)
    lon, lat = cell_center(cells[3])
    path = write_geojson_features(
        tmp_path / "hwm.geojson",
        [(Point(lon, lat), {"event": "test"}), (Point(lon, lat), {"event": "test"})],
    )
    df = pd.DataFrame({"h3_index": cells})
    out = attach_observed_labels(df, path)
    row = out.loc[out["h3_index"] == cells[3]].iloc[0]
    assert int(row["flood_point_count"]) == 2
    assert row[TARGET_COLUMN] == 1.0
    assert (out["flood_point_count"] == 0).sum() >= 1


def test_multi_source_paths(tmp_path: Path):
    cells = bbox_to_cells(10.70, 59.90, 10.73, 59.93, 9)
    poly = cell_boundary_polygon(cells[0])
    lon, lat = cell_center(cells[1])
    p1 = write_geojson_features(tmp_path / "poly.geojson", [(poly, {})])
    p2 = write_geojson_features(tmp_path / "pts.geojson", [(Point(lon, lat), {})])
    out = attach_observed_labels(pd.DataFrame({"h3_index": cells}), [p1, p2])
    assert out.loc[out["h3_index"] == cells[0], TARGET_CLASS_COLUMN].iloc[0] == 1
    assert int(out.loc[out["h3_index"] == cells[1], "flood_point_count"].iloc[0]) == 1


def test_missing_file_raises(tmp_path: Path):
    df = pd.DataFrame({"h3_index": ["892a107288bffff"]})
    with pytest.raises(FileNotFoundError):
        attach_observed_labels(df, tmp_path / "nope.geojson")


def test_gpkg_roundtrip_optional(tmp_path: Path):
    gpd = pytest.importorskip("geopandas")
    cells = bbox_to_cells(10.70, 59.90, 10.72, 59.92, 9)
    poly = cell_boundary_polygon(cells[0])
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[poly], crs="EPSG:4326")
    gpkg = tmp_path / "floods.gpkg"
    gdf.to_file(gpkg, driver="GPKG")
    out = attach_observed_labels(pd.DataFrame({"h3_index": cells}), gpkg)
    assert out.loc[out["h3_index"] == cells[0], "flood_area_frac"].iloc[0] > 0.9
