"""Load YAML study configs (e.g. configs/demo_oslo.yaml, configs/nyc.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pluvial_flood_risk.config import DEFAULT_BBOX, DEFAULT_H3_RESOLUTION, PROJECT_ROOT


def _as_bbox4(value: Any, *, name: str) -> tuple[float, float, float, float]:
    bbox = tuple(value)
    if len(bbox) != 4:
        raise ValueError(f"{name} must have four values: min_lon, min_lat, max_lon, max_lat")
    return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))


def load_study_config(path: Path | str | None = None) -> dict[str, Any]:
    path = Path(path or PROJECT_ROOT / "configs" / "demo_oslo.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    try:
        import yaml
    except ImportError as exc:
        raise ImportError("PyYAML required: pip install pyyaml") from exc

    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    profiles_raw = cfg.get("bbox_profiles") or {}
    profiles: dict[str, tuple[float, float, float, float]] = {}
    if isinstance(profiles_raw, dict):
        for key, value in profiles_raw.items():
            profiles[str(key)] = _as_bbox4(value, name=f"bbox_profiles.{key}")
    cfg["bbox_profiles"] = profiles

    # Prefer explicit bbox; else named study profile; else DEFAULT.
    if "bbox" in cfg:
        bbox = _as_bbox4(cfg["bbox"], name="bbox")
    elif "lower_manhattan" in profiles:
        bbox = profiles["lower_manhattan"]
    elif "study" in profiles:
        bbox = profiles["study"]
    else:
        bbox = _as_bbox4(DEFAULT_BBOX, name="DEFAULT_BBOX")
    cfg["bbox"] = bbox

    cfg.setdefault("resolution", DEFAULT_H3_RESOLUTION)
    cfg.setdefault("random_seed", 42)
    cfg.setdefault("default_build_profile", "lower_manhattan")
    cfg.setdefault("default_smoke_profile", "smoke")

    if "smoke_bbox" in cfg:
        cfg["smoke_bbox"] = _as_bbox4(cfg["smoke_bbox"], name="smoke_bbox")
    elif "smoke" in profiles:
        cfg["smoke_bbox"] = profiles["smoke"]

    # Keep aliases in sync so older callers still work.
    if "smoke_bbox" in cfg:
        profiles.setdefault("smoke", cfg["smoke_bbox"])
    profiles.setdefault("lower_manhattan", bbox)
    profiles.setdefault("study", bbox)
    cfg["bbox_profiles"] = profiles

    cfg["paths"] = resolve_config_paths(cfg.get("paths") or {}, PROJECT_ROOT)
    return cfg


def resolve_bbox(
    cfg: dict[str, Any],
    profile: str | None = None,
    *,
    default: str | None = None,
) -> tuple[float, float, float, float]:
    """
    Resolve a study extent from ``bbox_profiles`` / legacy ``bbox`` / ``smoke_bbox``.

    Profile aliases:
    - ``smoke`` → ``smoke_bbox`` or ``bbox_profiles.smoke``
    - ``study`` / ``bbox`` / ``lower_manhattan`` → main ``bbox``
    - any other key → ``bbox_profiles[key]``
    """
    profiles = cfg.get("bbox_profiles") or {}
    name = (profile or default or "").strip()
    if not name:
        return _as_bbox4(cfg["bbox"], name="bbox")

    if name in ("smoke",):
        if "smoke_bbox" in cfg:
            return _as_bbox4(cfg["smoke_bbox"], name="smoke_bbox")
        if "smoke" in profiles:
            return _as_bbox4(profiles["smoke"], name="bbox_profiles.smoke")
        return _as_bbox4(cfg["bbox"], name="bbox")

    if name in ("study", "bbox", "lower_manhattan"):
        if name in profiles:
            return _as_bbox4(profiles[name], name=f"bbox_profiles.{name}")
        return _as_bbox4(cfg["bbox"], name="bbox")

    if name in profiles:
        return _as_bbox4(profiles[name], name=f"bbox_profiles.{name}")
    raise KeyError(
        f"Unknown bbox profile '{name}'. Known: {sorted(set(profiles) | {'smoke', 'study', 'bbox', 'lower_manhattan'})}"
    )


def resolve_config_paths(paths: dict[str, Any], root: Path) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in paths.items():
        if value is None or value == "":
            resolved[key] = None
            continue
        if isinstance(value, list):
            resolved[key] = [_resolve_one(v, root) for v in value]
        else:
            resolved[key] = _resolve_one(value, root)
    return resolved


def _resolve_one(value: Any, root: Path) -> Path:
    p = Path(str(value))
    return p if p.is_absolute() else (root / p)


def rainfall_scenarios_from_config(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = cfg.get("rainfall_scenarios") or []
    out: list[dict[str, Any]] = []
    for item in scenarios:
        if isinstance(item, dict):
            name = str(item.get("name", "unnamed"))
            mm_h = float(item.get("mm_h", item.get("rainfall_mm_h", 25.0)))
            out.append({"name": name, "mm_h": mm_h})
        else:
            out.append({"name": f"r{item}", "mm_h": float(item)})
    if not out:
        out.append({"name": "default", "mm_h": float(cfg.get("rainfall_mm_h", 25.0))})
    return out
