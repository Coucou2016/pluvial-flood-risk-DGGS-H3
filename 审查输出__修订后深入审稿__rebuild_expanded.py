from pathlib import Path

from pluvial_flood_risk.assemble import assemble_h3_table, sources_from_config
from pluvial_flood_risk.config_loader import load_study_config, resolve_bbox


cfg = load_study_config(Path("configs/nyc.yaml"))
cfg["paths"] = dict(cfg.get("paths") or {})
cfg["paths"]["raw_dir"] = Path("data/raw/nyc_expanded")
for key in (
    "dem",
    "slope",
    "impervious",
    "buildings",
    "hydro",
    "flood_polygons",
    "flood_points",
    "coastal",
    "sandy",
    "event_rainfall",
    "floodnet",
):
    cfg["paths"].pop(key, None)
cfg["assembly_mode"] = "opendata"

table = assemble_h3_table(
    resolve_bbox(cfg, "manhattan_expanded"),
    int(cfg["resolution"]),
    rainfall_mm_h=float(cfg["rainfall_mm_h"]),
    sources=sources_from_config(cfg),
    fallback_synthetic=False,
)
out = Path("审查输出/修订后深入审稿/rebuild_expanded.parquet")
table.to_parquet(out, index=False)
print(out)
