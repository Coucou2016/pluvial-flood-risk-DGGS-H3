from pathlib import Path

import pytest

from pluvial_flood_risk.model import require_model_artifacts


def test_require_model_artifacts_missing():
    missing_dir = Path(__file__).resolve().parent / "_no_models_here"
    with pytest.raises(FileNotFoundError, match="pluvial-train"):
        require_model_artifacts(missing_dir)
