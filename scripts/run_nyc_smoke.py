#!/usr/bin/env python
"""Manhattan paper-path smoke (fixtures if Open Data is absent)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.pipeline import nyc_smoke_test  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(nyc_smoke_test(), indent=2, default=str))
