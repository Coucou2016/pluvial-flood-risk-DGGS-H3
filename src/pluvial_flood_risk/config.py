"""Project paths and default H3 / model settings."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Demo study area: small bbox near Oslo (paper context: Norway)
DEFAULT_BBOX = (10.70, 59.90, 10.85, 59.98)  # min_lon, min_lat, max_lon, max_lat

# H3 resolution: ~0.1 km² at res 9; use 9 for city-scale demo, 8 for regional
DEFAULT_H3_RESOLUTION = 9

# Production estimator inputs (Major Revision 2026-10-08):
# - ``rainfall_mm_h`` is dropped: it is constant in training (zero variance), so the
#   GBM cannot learn a rainfall response. Event-scaled rainfall belongs in a future
#   explicit event model (see EVENT_FEATURE_COLUMNS).
# - ``flow_accum_proxy`` renamed to ``dem_d8_accum_proxy`` (a DEM-derived D8
#   accumulation *proxy*, not real drainage accumulation).
# - ``dist_stream_m`` renamed to ``dist_mapped_water_m`` (distance to mapped water,
#   computed in EPSG:2263 metres; Lower Manhattan is tidal-river / shoreline-heavy).
# - ``building_area_fraction`` added (footprint area fraction, land-normalised
#   exposure), so building exposure is not carried only by a per-cell count density.
# ``land_cover_urban`` stays omitted (deterministic copy of impervious_frac).
FEATURE_COLUMNS = [
    "elevation_m",
    "slope_deg",
    "dem_d8_accum_proxy",
    "impervious_frac",
    "building_density",
    "building_area_fraction",
    "dist_mapped_water_m",
]

# Deprecated feature aliases kept so older tables/figures still resolve. These are
# NOT model inputs; they point at the renamed canonical columns.
FEATURE_ALIASES = {
    "flow_accum_proxy": "dem_d8_accum_proxy",
    "dist_stream_m": "dist_mapped_water_m",
}

# Future explicit event interface (not trained here: no radar/gauge rainfall in the
# frozen table). Documented so a scenario hook cannot pretend rainfall is a learned
# driver. ``assert_feature_is_trained_for_scenario`` guards any scenario that tries.
EVENT_FEATURE_COLUMNS = [
    "rainfall_mm_h",
    "rainfall_return_period_yr",
    "antecedent_moisture",
]

# Pre-specified GBM hyperparameters (no nested CV retuning on the production path).
GBM_N_ESTIMATORS = 80
GBM_MAX_DEPTH = 4
GBM_LEARNING_RATE = 0.08
OPERATING_THRESHOLD_DEFAULT = 0.5

# --- Target ontology (Major Revision P0-1 / P0-10) ---------------------------
# MAIN target is a BINARY union of three heterogeneous open-evidence sources:
#   evidence_positive = (dep_area_frac>0) | (complaint_count>0) | (ida_hwm_count>0)
# The previous cross-source continuous `max(area_frac, point_presence)` composite is
# removed from the main result. Any continuous target is DEP-only and named
# ``evidence_coverage_proxy``.
TARGET_COLUMN = "evidence_score"
TARGET_CLASS_COLUMN = "evidence_positive"
TARGET_PROXY_COLUMN = "evidence_coverage_proxy"
LEGACY_TARGET_COLUMN = "flood_risk"
LEGACY_TARGET_CLASS_COLUMN = "flood_class"

RANDOM_SEED = 42

PROVENANCE_SYNTHETIC = "synthetic"
PROVENANCE_OBSERVED = "observed"
PROVENANCE_MIXED = "mixed"
PROVENANCE_FIXTURE = "fixture"
# Composite flood-evidence label assembled from heterogeneous open public
# sources (DEP model-derived stormwater polygons + 311 crowd-reported points +
# USGS Ida high-water marks). These are NOT a single "observed" ground truth:
# DEP is hydrologic/hydraulic model output, 311 is reported (not verified)
# inundation, and only the HWM points are direct observations.
PROVENANCE_OPEN_EVIDENCE = "open_public_evidence"

ASSEMBLY_HASH = "hash_demo"
ASSEMBLY_FIXTURE = "fixture"
ASSEMBLY_OPENDATA = "opendata"

# Spatial-CV parent-resolution offset (P0-6): the coarse "block" is the H3
# parent this many resolutions *up* from the modelling resolution. At R9 with
# offset 2 the blocks are R7 cells. This was misnamed ``k_ring`` historically —
# it is a parent-resolution offset, NOT an H3 k-ring.
DEFAULT_PARENT_RESOLUTION_OFFSET = 2
# Deprecated alias (kept so older call sites/tests keep resolving).
DEFAULT_SPATIAL_CV_K = DEFAULT_PARENT_RESOLUTION_OFFSET
DEFAULT_SPATIAL_CV_FOLDS = 5

# Buffered spatial CV (P0-5): purge training cells within these metre buffers of
# any held-out cell (projected to EPSG:2263). 0 = current GroupKFold behaviour.
DEFAULT_CV_BUFFER_METERS: tuple[int, ...] = (0, 250, 500, 1000)
# Spatial-block bootstrap resamples (P0-5) for pooled AUC/AP 95% CI.
SPATIAL_BLOCK_BOOTSTRAP_N = 1000

# Lower Manhattan (paper main study). Oslo remains transfer/appendix.
NYC_MANHATTAN_BBOX = (-74.02, 40.70, -73.97, 40.76)

# Strict release mode: missing critical artifacts FAIL instead of skip.
STRICT_RELEASE_ENV = "PAPER_RELEASE_STRICT"


def strict_release_mode() -> bool:
    """True when ``PAPER_RELEASE_STRICT=1`` (CI/paper gate mode)."""
    import os

    return str(os.environ.get(STRICT_RELEASE_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def assert_feature_is_trained_for_scenario(
    train_df,
    feature: str,
    min_unique: int = 3,
) -> None:
    """Fail closed if a scenario feature is constant (zero-variance) in training.

    ``rainfall_mm_h`` was constant in the frozen training table, so a rainfall
    scenario interface can silently pretend the model learned a rainfall
    response. Any retained scenario hook must call this guard.
    """
    if feature not in train_df.columns:
        raise KeyError(
            f"Scenario feature '{feature}' is not present in the training table; "
            "it cannot be a learned driver. See config.EVENT_FEATURE_COLUMNS."
        )
    n_unique = int(train_df[feature].nunique(dropna=True))
    if n_unique < int(min_unique):
        raise ValueError(
            f"Scenario feature '{feature}' has only {n_unique} unique training value(s) "
            f"(< min_unique={min_unique}); the model did not learn a response to it. "
            "Refusing to present it as a scenario driver."
        )
