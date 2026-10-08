"""Submission hard gates (Major Revision 2026-10-08, spec §Tests 1-8).

These are the gates that a formal reviewer report requires to be *fail-closed*:
in strict release mode (`PAPER_RELEASE_STRICT=1`) a missing critical artifact is a
FAILURE rather than a skip, so a stripped or partially regenerated repository
cannot silently pass the release gate.

Gates
-----
1. FloodNet cannot be a training label (typed ``EvidenceSource.role`` raises).
2. FloodNet timestamps are all ``< analysis_freeze_utc`` (enforced on data).
3. ``outputs/paper_results.json`` contains no absolute local paths.
4. No uncalibrated-model ``probability`` / legacy ``PFI_h`` terminology.
5. An UN-refined hotspot must give ``hotspot_refinement_recall == 0``.
6. Scale reconstruction MAE = 0.5 for fine {0,1} vs parent mean 0.5 (not 0).
7. In strict release mode, a missing critical artifact FAILS instead of skipping.
8. Manifest <-> file consistency (sha256, row count, dataset id, retrieval time).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pluvial_flood_risk.config import (
    PROCESSED_DIR,
    PROJECT_ROOT,
    STRICT_RELEASE_ENV,
    strict_release_mode,
)
from pluvial_flood_risk.labels import EvidenceSource, attach_training_labels

ROOT = PROJECT_ROOT
REGISTRY = ROOT / "outputs" / "paper_results.json"
RAW_DIRS = [ROOT / "data" / "raw" / "nyc", ROOT / "data" / "raw" / "nyc_expanded"]
MANIFEST_NAME = "DOWNLOAD_MANIFEST.json"

# Critical artifacts: in strict mode these MUST exist (no skip).
CRITICAL_ARTIFACTS = [
    REGISTRY,
    ROOT / "outputs" / "floodnet_heldout_validation.json",
    ROOT / "outputs" / "block_sensitivity.json",
    ROOT / "outputs" / "source_ablation.json",
    ROOT / "outputs" / "adaptive_r11_hotspot_retention.json",
    ROOT / "outputs" / "jaccard_by_resolution.csv",
    PROCESSED_DIR / "nyc_h3_cells.parquet",
]


def _require(*paths: Path) -> None:
    """Fail-closed artifact gate.

    Strict release mode (``PAPER_RELEASE_STRICT=1``): a missing critical artifact
    is a hard FAILURE. Otherwise (interactive dev) it skips with a clear reason.
    """
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.exists()]
    if not missing:
        return
    msg = f"Missing critical release artifact(s): {missing}"
    if strict_release_mode():
        pytest.fail(f"[{STRICT_RELEASE_ENV}=1] {msg}")
    pytest.skip(msg)


# ---------------------------------------------------------------------------
# Gate 7 — strict mode turns "skip" into "fail" (tested directly, no artifacts)
# ---------------------------------------------------------------------------
def test_gate7_strict_mode_missing_artifact_fails(monkeypatch: pytest.MonkeyPatch):
    missing = ROOT / "outputs" / "__definitely_not_here__.json"
    # Non-strict: skip.
    monkeypatch.delenv(STRICT_RELEASE_ENV, raising=False)
    assert strict_release_mode() is False
    with pytest.raises(pytest.skip.Exception):
        _require(missing)
    # Strict: hard failure.
    monkeypatch.setenv(STRICT_RELEASE_ENV, "1")
    assert strict_release_mode() is True
    with pytest.raises(pytest.fail.Exception):
        _require(missing)


def test_gate7_critical_artifacts_present_in_strict_mode():
    if not strict_release_mode():
        pytest.skip("set PAPER_RELEASE_STRICT=1 to force the release gate")
    _require(*CRITICAL_ARTIFACTS)


# ---------------------------------------------------------------------------
# Gate 1 — FloodNet cannot be a training label
# ---------------------------------------------------------------------------
def test_gate1_floodnet_cannot_be_training_label(tmp_path: Path):
    # A tiny synthetic H3 frame; the role check must raise BEFORE any geometry work.
    import h3

    cells = [h3.latlng_to_cell(40.71, -74.0, 9)]
    df = pd.DataFrame({"h3_index": cells})

    floodnet = EvidenceSource(
        path=tmp_path / "floodnet_sensors.geojson",
        kind="floodnet",
        role="external_validation",
    )
    with pytest.raises(ValueError, match="Non-training source"):
        attach_training_labels(df, [floodnet])

    sandy = EvidenceSource(
        path=tmp_path / "fema_sandy.geojson", kind="sandy", role="negative_control"
    )
    with pytest.raises(ValueError, match="Non-training source"):
        attach_training_labels(df, [sandy])

    # A training_label source passes the role gate. Give it a valid (empty)
    # GeoJSON so it assembles; the point is only that the role check is not hit.
    ok_path = tmp_path / "dep_stormwater_flood.geojson"
    ok_path.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
    ok = EvidenceSource(path=ok_path, kind="dep", role="training_label")
    out = attach_training_labels(df, [ok])
    assert "evidence_positive" in out.columns


def test_gate1_nyc_config_has_no_include_floodnet():
    cfg_text = (ROOT / "configs" / "nyc.yaml").read_text(encoding="utf-8")
    assert "include_floodnet" not in cfg_text
    # FloodNet must be declared under an external_validation block.
    assert re.search(r"^external_validation:", cfg_text, flags=re.MULTILINE)
    assert re.search(r"^negative_control:", cfg_text, flags=re.MULTILINE)
    assert re.search(r"^\s+role:\s*external_validation\s*$", cfg_text, flags=re.MULTILINE)
    assert re.search(r"^\s+role:\s*negative_control\s*$", cfg_text, flags=re.MULTILINE)


def test_gate1_assemble_rejects_include_floodnet_config():
    from pluvial_flood_risk.assemble import sources_from_config

    with pytest.raises(ValueError, match="include_floodnet"):
        sources_from_config({"labels": {"include_floodnet": True}})


# ---------------------------------------------------------------------------
# Gate 2 — FloodNet freeze enforced on data
# ---------------------------------------------------------------------------
def test_gate2_floodnet_timestamps_before_freeze():
    from pluvial_flood_risk.floodnet import (
        filter_events_before_freeze,
        filter_sensors_before_freeze,
        freeze_time,
    )

    freeze = freeze_time()
    events = [
        {"flood_start_time": "2021-09-01T12:00:00+00:00"},  # kept
        {"flood_start_time": "2099-01-01T00:00:00+00:00"},  # dropped (post-freeze)
        {"flood_start_time": "not-a-date"},  # unparseable -> dropped, counted
    ]
    kept, audit = filter_events_before_freeze(events, freeze)
    assert audit["n_events_downloaded"] == 3
    assert audit["n_events_before_freeze"] == 1
    assert audit["n_events_after_freeze_dropped"] == 1
    assert audit["n_events_unparseable_timestamp"] == 1
    ts = pd.to_datetime(audit["events_max_timestamp_after_filter"], utc=True)
    assert ts < pd.Timestamp(freeze)

    sensors = [
        {"sensor_id": "a", "date_installed": "2021-01-01T00:00:00+00:00"},
        {"sensor_id": "b", "date_installed": "2099-01-01T00:00:00+00:00"},
    ]
    s_kept, s_audit = filter_sensors_before_freeze(sensors, freeze)
    assert [s["sensor_id"] for s in s_kept] == ["a"]
    assert s_audit["n_sensors_before_freeze"] == 1
    assert s_audit["n_sensors_after_freeze_dropped"] == 1


def test_gate2_registry_records_freeze_audit_counters():
    _require(REGISTRY)
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ext = payload.get("external_validation")
    if ext is None:
        pytest.fail("registry has no external_validation block")
    assert ext.get("analysis_freeze_utc")
    # Query-time freezer + post-download filter counters must be present.
    for pilot in ext.get("pilots", []):
        audit = pilot.get("freeze_audit") or {}
        for key in (
            "n_events_downloaded",
            "n_events_before_freeze",
            "n_events_after_freeze_dropped",
            "events_max_timestamp_after_filter",
            "n_sensors_before_freeze",
        ):
            assert key in audit, f"freeze audit missing {key} for {pilot.get('pilot')}"


def test_gate2_registry_external_validation_is_not_a_label():
    _require(REGISTRY)
    ext = json.loads(REGISTRY.read_text(encoding="utf-8"))["external_validation"]
    assert ext.get("used_in_training_or_evaluation_labels") is False
    assert str(ext.get("role", "")).startswith("external_validation")


# ---------------------------------------------------------------------------
# Gate 3 — no absolute paths in the registry
# ---------------------------------------------------------------------------
_ABS_PATTERNS = [
    re.compile(r"[A-Za-z]:\\\\"),  # C:\\...
    re.compile(r"[A-Za-z]:/"),  # C:/...
    re.compile(r"\\\\[A-Za-z0-9_.\-]+\\"),  # UNC \\server\share
    re.compile(r"/(?:Users|home)/[A-Za-z0-9_.\-]+/"),  # POSIX home
]


def _walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def test_gate3_registry_has_no_absolute_paths():
    _require(REGISTRY)
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    offenders = []
    for where, value in _walk_strings(payload):
        # URLs (https://...) are fine; only local filesystem paths are banned.
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", value):
            continue
        for pat in _ABS_PATTERNS:
            if pat.search(value):
                offenders.append((where, value))
                break
    assert not offenders, f"absolute local paths in registry: {offenders[:5]}"


def test_gate3_no_absolute_paths_in_raw_manifests():
    for raw in RAW_DIRS:
        manifest = raw / MANIFEST_NAME
        _require(manifest)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for entry in payload.get("files", []):
            p = str(entry.get("path", ""))
            assert not re.match(r"^[A-Za-z]:", p), f"absolute path in {manifest}: {p}"
            assert p.startswith("data/"), f"manifest path must be project-relative: {p}"


# ---------------------------------------------------------------------------
# Gate 4 — no probability / PFI_h terminology for the uncalibrated model
# ---------------------------------------------------------------------------
_TERMINOLOGY_SCAN = [
    ROOT / "README.md",
    ROOT / "docs" / "paper" / "manuscript.md",
    ROOT / "docs" / "paper" / "report.md",
]


def test_gate4_no_probability_or_legacy_pfi_terminology():
    offenders: list[str] = []
    for path in _TERMINOLOGY_SCAN:
        if not path.exists():
            pytest.fail(f"missing terminology-scanned doc: {path}")
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if "pfi_h" in lowered and "legacy" not in lowered and "delete" not in lowered:
                offenders.append(f"{path.name}:{line_no}: PFI_h -> {line.strip()[:90]}")
            if "flood_probability" in lowered:
                offenders.append(
                    f"{path.name}:{line_no}: flood_probability -> {line.strip()[:90]}"
                )
    assert not offenders, "uncalibrated-model probability/PFI_h terminology:\n" + "\n".join(
        offenders
    )


def test_gate4_feature_columns_have_no_rainfall():
    from pluvial_flood_risk.config import EVENT_FEATURE_COLUMNS, FEATURE_COLUMNS

    assert "rainfall_mm_h" not in FEATURE_COLUMNS
    assert "rainfall_mm_h" in EVENT_FEATURE_COLUMNS
    assert "flow_accum_proxy" not in FEATURE_COLUMNS
    assert "dem_d8_accum_proxy" in FEATURE_COLUMNS
    assert "dist_stream_m" not in FEATURE_COLUMNS
    assert "dist_mapped_water_m" in FEATURE_COLUMNS


def test_gate4_scenario_guard_raises_on_zero_variance_feature():
    from pluvial_flood_risk.config import assert_feature_is_trained_for_scenario

    train = pd.DataFrame({"rainfall_mm_h": [40.0] * 10})
    with pytest.raises(ValueError, match="min_unique"):
        assert_feature_is_trained_for_scenario(train, "rainfall_mm_h", min_unique=3)
    varying = pd.DataFrame({"rainfall_mm_h": np.arange(10.0)})
    assert_feature_is_trained_for_scenario(varying, "rainfall_mm_h", min_unique=3) is None


# ---------------------------------------------------------------------------
# Gate 5 — an UN-refined hotspot must give refinement recall == 0
# ---------------------------------------------------------------------------
def test_gate5_unrefined_hotspot_recall_zero():
    from pluvial_flood_risk.adaptive import adaptive_vs_uniform_metrics
    from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_children

    coarse = bbox_to_cells(-74.02, 40.70, -73.99, 40.72, 9)[:12]
    fine_res = 11
    uniform_fine = []
    for c in coarse:
        uniform_fine.extend(cell_children(c, fine_res))
    scores = np.linspace(0.0, 1.0, len(uniform_fine))

    # NO parent is refined: the mixed index is just the coarse cells themselves.
    n_refined_children = 0
    metrics_unrefined = adaptive_vs_uniform_metrics(
        mixed_cells=list(coarse),
        uniform_fine_cells=uniform_fine,
        uniform_scores=scores,
        hotspot_quantile=0.9,
        refined_fine_cells=[],  # nothing actually refined to R11
    )
    assert n_refined_children == 0
    # The OLD metric (coverage) is 1.0 by construction — the tautology.
    assert metrics_unrefined["hotspot_coverage_recall"] == pytest.approx(1.0)
    # The NEW metric (actual refinement) must be 0.
    assert metrics_unrefined["hotspot_refinement_recall"] == pytest.approx(0.0)

    # Now refine exactly the top-scoring parent: recall becomes > 0.
    ordered = sorted(zip(uniform_fine, scores, strict=True), key=lambda t: -t[1])
    hot_cell = ordered[0][0]
    hot_parent = hot_cell[: len(coarse[0])]
    refined = cell_children(hot_parent, fine_res)
    metrics_refined = adaptive_vs_uniform_metrics(
        mixed_cells=[c for c in coarse if c != hot_parent] + refined,
        uniform_fine_cells=uniform_fine,
        uniform_scores=scores,
        hotspot_quantile=0.9,
        refined_fine_cells=refined,
    )
    assert metrics_refined["hotspot_refinement_recall"] > 0.0


# ---------------------------------------------------------------------------
# Gate 6 — reconstruction MAE = 0.5 for fine {0,1} vs parent mean 0.5
# ---------------------------------------------------------------------------
def test_gate6_scale_reconstruction_mae_is_not_zero():
    from pluvial_flood_risk.rollups import resolution_ladder_topk_diagnostics

    # Two fine R10 cells (same R9 parent) with opposite extremes: fine scores 0/1.
    # Mean aggregation gives the parent score 0.5; expanding that back onto the
    # fine cells gives |0-0.5| + |1-0.5| => area-weighted MAE = 0.5 (NOT 0).
    import h3

    parent = h3.latlng_to_cell(40.71, -74.0, 9)
    children = sorted(h3.cell_to_children(parent, 10))[:2]
    df = pd.DataFrame(
        {
            "h3_index": children,
            "h3_resolution": [10, 10],
            "observed_risk": [0.0, 1.0],
        }
    )
    ladder = resolution_ladder_topk_diagnostics(
        df, value_col="observed_risk", resolutions=[9], hotspot_budget=0.5
    )
    mean_row = ladder.loc[ladder["aggregation"] == "mean"].iloc[0]
    assert mean_row["reconstruction_mae"] == pytest.approx(0.5, abs=1e-9)
    assert mean_row["reconstruction_rmse"] == pytest.approx(0.5, abs=1e-9)
    # The identity QA diagnostic (parent mean vs its own parent mean) IS 0 —
    # that is the metric P0-9 deleted from the paper.
    assert mean_row["continuous_mae"] == pytest.approx(0.0, abs=1e-9)


def test_gate6_registry_scale_loss_uses_reconstruction_error():
    _require(REGISTRY)
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = (payload.get("scale_loss") or {}).get("rows") or []
    assert rows, "scale_loss rows missing"
    mean_r9 = [r for r in rows if r["aggregation"] == "mean" and r["coarse_res"] == 9]
    assert mean_r9, "no mean/R9 ladder row"
    row = mean_r9[0]
    assert row["reconstruction_mae"] > 0.0
    assert row["reconstruction_rmse"] > 0.0
    assert row["reconstruction_mae"] != pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Gate 8 — manifest <-> file consistency
# ---------------------------------------------------------------------------
def test_gate8_manifest_file_consistency():
    checked = 0
    for raw in RAW_DIRS:
        manifest = raw / MANIFEST_NAME
        _require(manifest)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload.get("schema") == "raw_download_manifest/v2"
        for entry in payload.get("files", []):
            # No absolute paths (also gate 3), project-relative under data/.
            rel = str(entry["path"])
            path = ROOT / rel
            assert path.exists(), f"manifest lists missing file: {rel}"
            assert int(entry["bytes"]) == path.stat().st_size, f"byte size drift: {rel}"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == entry["sha256"], f"sha256 drift (re-run the manifest): {rel}"
            # Every indexed layer carries a dataset identity.
            assert entry.get("dataset_id"), f"missing dataset_id: {rel}"
            assert entry.get("type") in {"raster", "vector", "json"}
            if entry.get("type") in {"vector", "json"}:
                # n_records must match the on-disk feature/event count.
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("features"), list):
                    assert int(entry["n_records"]) == len(data["features"])
                elif isinstance(data, dict) and isinstance(data.get("events"), list):
                    assert int(entry["n_records"]) == len(data["events"])
            checked += 1
    assert checked > 0, "no manifest entries checked"


def test_gate8_floodnet_query_sidecar_records_freeze_and_fetch_time():
    query = ROOT / "data" / "raw" / "nyc" / "floodnet_query.json"
    _require(query)
    meta = json.loads(query.read_text(encoding="utf-8"))
    assert meta.get("analysis_freeze_utc")
    assert meta.get("retrieved_utc")
    assert "flood_start_time <" in str(meta.get("query_where_events", ""))
