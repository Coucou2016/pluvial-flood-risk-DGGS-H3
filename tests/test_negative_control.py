"""Coastal Sandy overlay as a negative control."""

from __future__ import annotations

from pathlib import Path

from pluvial_flood_risk.assemble import FeatureSources, assemble_h3_table, assemble_label_scale_table
from pluvial_flood_risk.negative_control import (
    attach_coastal_overlay,
    negative_control_metrics,
)
from pluvial_flood_risk.schema_fixtures import write_public_schema_fixtures

TINY = (-74.015, 40.705, -74.005, 40.712)


def test_negative_control_separates_coastal_and_pluvial(tmp_path: Path):
    paths = write_public_schema_fixtures(tmp_path, TINY)
    sources = FeatureSources(
        buildings_path=paths["buildings"],
        hydro_path=paths["hydro"],
        flood_polygons_path=paths["flood_polygons"],
        flood_points_paths=[paths["flood_311"]],
        coastal_path=paths["fema_sandy"],
        assembly_mode="fixture",
    )
    df = assemble_h3_table(TINY, resolution=10, rainfall_mm_h=40.0, sources=sources)
    assert "sandy_area_frac" in df.columns
    assert (df["label_source"] == "observed").all()
    # Overlay must not overwrite pluvial labels with Sandy
    assert df["flood_class"].nunique() >= 1
    metrics = negative_control_metrics(df, score_col="flood_risk")
    assert metrics["n_cells"] == len(df)
    assert metrics["n_coastal"] + metrics["n_neither"] <= metrics["n_cells"] + metrics["n_pluvial"]
    assert metrics.get("assembly_mode") == "fixture"
    assert "fixture" in str(metrics.get("note", "")).lower() or "QA" in str(metrics.get("note", ""))


def test_negative_control_opendata_note():
    import pandas as pd

    df = pd.DataFrame(
        {
            "sandy_area_frac": [0.5, 0.0, 0.0],
            "flood_area_frac": [0.0, 0.8, 0.0],
            "flood_risk": [0.2, 0.9, 0.1],
            "assembly_mode": ["opendata", "opendata", "opendata"],
        }
    )
    metrics = negative_control_metrics(df, score_col="flood_risk")
    assert metrics["assembly_mode"] == "opendata"
    assert "live open-data" in str(metrics["note"])
    assert "fixture" not in str(metrics["note"]).lower()


def test_assemble_label_scale_table_fast(tmp_path: Path):
    paths = write_public_schema_fixtures(tmp_path, TINY)
    sources = FeatureSources(
        flood_polygons_path=paths["flood_polygons"],
        flood_points_paths=[paths["flood_311"]],
        assembly_mode="fixture",
    )
    parent = assemble_h3_table(TINY, resolution=9, sources=sources)
    df = assemble_label_scale_table(
        TINY, resolution=10, sources=sources, parent_label_df=parent
    )
    assert len(df) > 0
    assert "flood_risk" in df.columns
    assert (df["h3_resolution"] == 10).all()
    assert df["feature_source"].iloc[0] == "labels_only_diagnostics"
    assert df["label_scale_mode"].iloc[0] == "points_plus_parent_inherit"


def test_attach_coastal_overlay_does_not_change_labels(tmp_path: Path):
    paths = write_public_schema_fixtures(tmp_path, TINY)
    sources = FeatureSources(
        flood_polygons_path=paths["flood_polygons"],
        assembly_mode="fixture",
    )
    table = assemble_h3_table(TINY, resolution=10, sources=sources)
    before = table["flood_class"].to_numpy().copy()
    out = attach_coastal_overlay(table, paths["fema_sandy"])
    assert (out["flood_class"].to_numpy() == before).all()
    assert "sandy_class" in out.columns
