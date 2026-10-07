#!/usr/bin/env python
"""One-shot demo: generate data, train, evaluate, predict."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pluvial_flood_risk.pipeline import smoke_test  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(smoke_test(), indent=2))
