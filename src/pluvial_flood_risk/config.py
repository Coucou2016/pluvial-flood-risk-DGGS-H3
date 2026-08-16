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

FEATURE_COLUMNS = [
    "elevation_m",
    "slope_deg",
    "flow_accum_proxy",
    "impervious_frac",
    "building_density",
    "dist_stream_m",
    "rainfall_mm_h",
    "land_cover_urban",
]

TARGET_COLUMN = "flood_risk"
TARGET_CLASS_COLUMN = "flood_class"

RANDOM_SEED = 42

PROVENANCE_SYNTHETIC = "synthetic"
PROVENANCE_OBSERVED = "observed"
PROVENANCE_MIXED = "mixed"
PROVENANCE_FIXTURE = "fixture"

ASSEMBLY_HASH = "hash_demo"
ASSEMBLY_FIXTURE = "fixture"
ASSEMBLY_OPENDATA = "opendata"

DEFAULT_SPATIAL_CV_K = 2
DEFAULT_SPATIAL_CV_FOLDS = 5

# Lower Manhattan (paper main study). Oslo remains transfer/appendix.
NYC_MANHATTAN_BBOX = (-74.02, 40.70, -73.97, 40.76)
