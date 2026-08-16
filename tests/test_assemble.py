"""Real-feature assemble path with public-schema fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from pluvial_flood_risk.assemble import FeatureSources, assemble_h3_table
from pluvial_flood_risk.config import PROVENANCE_OBSERVED
from pluvial_flood_risk.features import count_points_to_h3
from pluvial_flood_risk.schema_fixtures import write_public_schema_fixtures

TINY = (-74.015, 40.705, -74.005, 40.712)


def test_count_points_to_h3():
    import pandas as pd

    pts = pd.DataFrame({"lon": [-74.01, -74.01], "lat": [40.708, 40.708]})
    out = count_points_to_h3(pts, resolution=10)
    assert out["point_count"].iloc[0] == 2


def test_assemble_fixture_uses_observed_join(tmp_path: Path):
    pytest.importorskip("rasterio")
    paths = write_public_schema_fixtures(tmp_path, TINY)
    sources = FeatureSources(
        dem_path=paths.get("dem"),
        impervious_path=paths.get("impervious"),
        buildings_path=paths["buildings"],
        hydro_path=paths["hydro"],
        flood_polygons_path=paths["flood_polygons"],
        flood_points_paths=[paths["flood_311"], paths["ida_hwm"]],
        coastal_path=paths["fema_sandy"],
        assembly_mode="fixture",
    )
    df = assemble_h3_table(TINY, resolution=10, rainfall_mm_h=40.0, sources=sources)
    assert len(df) > 5
    assert (df["label_source"] == PROVENANCE_OBSERVED).all()
    assert (df["assembly_mode"] == "fixture").all()
    assert df["flood_class"].nunique() >= 1
    assert "elevation_m" in df.columns
    assert df["building_density"].notna().all()
    assert df["dist_stream_m"].notna().all()
    assert df["feature_source"].iloc[0] in {"observed", "mixed"}
    assert "sandy_area_frac" in df.columns
    assert "flow_accum_proxy" in df.columns
    assert "rainfall_source" in df.columns
    assert "rainfall_mm_h" not in str(df["observed_feature_cols"].iloc[0]).split(",")


def test_assemble_hash_fallback_without_files(tmp_path: Path):
    sources = FeatureSources(assembly_mode="hash_demo")
    df = assemble_h3_table((10.70, 59.90, 10.73, 59.93), 9, sources=sources)
    assert (df["feature_source"] == "synthetic").all()
    assert (df["label_source"] == "synthetic").all()
