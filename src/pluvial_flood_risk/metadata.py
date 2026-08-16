"""Run provenance and reproducibility metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h3
import sklearn

from pluvial_flood_risk.config import RANDOM_SEED


def build_run_metadata(
    data_provenance: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "data_provenance": data_provenance,
        "h3_version": h3.__version__,
        "sklearn_version": sklearn.__version__,
        "framework": "pluvial-flood-risk-dggs-h3",
        "framework_version": "0.1.0",
    }
    if extra:
        meta.update(extra)
    return meta


def write_run_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
