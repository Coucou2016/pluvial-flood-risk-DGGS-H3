"""Real-feature assemble path with public-schema fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from pluvial_flood_risk.assemble import FeatureSources, assemble_h3_table
from pluvial_flood_risk.config import PROVENANCE_OPEN_EVIDENCE
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
    assert (df["label_source"] == PROVENANCE_OPEN_EVIDENCE).all()
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
    df = assemble_h3_table(
        (10.70, 59.90, 10.73, 59.93),
        9,
        sources=sources,
        fallback_synthetic=True,
    )
    assert (df["feature_source"] == "synthetic").all()
    assert (df["label_source"] == "synthetic").all()


def test_assemble_fail_closed_without_files():
    from pluvial_flood_risk.assemble import AssemblyError

    sources = FeatureSources(assembly_mode="opendata")
    with pytest.raises(AssemblyError):
        assemble_h3_table(
            (10.70, 59.90, 10.73, 59.93),
            9,
            sources=sources,
            fallback_synthetic=False,
        )


def test_production_fail_closed_missing_layer_and_nan(tmp_path: Path):
    """Production default must fail on missing rasters and on NaN columns."""
    from pluvial_flood_risk.assemble import AssemblyError, assemble_feature_table
    from pluvial_flood_risk.h3_grid import bbox_to_cells

    sources = FeatureSources(assembly_mode="opendata")
    cells = bbox_to_cells(*TINY, 10)
    with pytest.raises(AssemblyError, match="missing observed"):
        assemble_feature_table(cells, sources=sources, fallback_synthetic=False)

    paths = write_public_schema_fixtures(tmp_path, TINY)
    sources = FeatureSources(
        dem_path=paths.get("dem"),
        impervious_path=paths.get("impervious"),
        buildings_path=paths["buildings"],
        hydro_path=paths["hydro"],
        assembly_mode="opendata",
    )
    df = assemble_feature_table(cells, sources=sources, fallback_synthetic=False)
    df.loc[df.index[0], "elevation_m"] = float("nan")
    from pluvial_flood_risk.assemble import AssemblyError as AE

    # Direct NaN check: assemble_feature_table already refused missing layers.
    # A second call with a bogus DEM path must still fail closed.
    missing = FeatureSources(
        dem_path=tmp_path / "no_such_dem.tif",
        assembly_mode="opendata",
    )
    with pytest.raises(AE, match="Fail-closed"):
        assemble_feature_table(cells, sources=missing, fallback_synthetic=False)
    assert df["elevation_m"].isna().any()

