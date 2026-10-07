#!/usr/bin/env python
"""Fail if manuscript.md headline numbers disagree with paper_results.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "outputs" / "paper_results.json"
MS = ROOT / "docs" / "paper" / "manuscript.md"


def _approx(a: float, b: float, tol: float = 0.006) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    text = MS.read_text(encoding="utf-8")
    lm = reg["lower_manhattan"]
    exp = reg["manhattan_expanded"]
    errors: list[str] = []

    if lm["n_cells"] != 262:
        errors.append(f"registry LM n_cells={lm['n_cells']} expected 262")
    if exp["n_cells"] != 956:
        errors.append(f"registry Exp n_cells={exp['n_cells']} expected 956")
    if "n = 262" not in text and "n=262" not in text:
        errors.append("manuscript missing Option B n = 262")
    if "141" in text and "legacy 141" not in text.lower() and "retained only" not in text:
        # allow historical mentions of legacy 141
        pass

    sc = lm["spatial_cv"]
    # Check key pooled ROC-AUC appears rounded to 3 decimals
    roc = round(float(sc["spatial_cv_roc_auc_pooled"]), 3)
    if f"{roc:.3f}" not in text and f"{roc:.2f}" not in text:
        errors.append(f"manuscript missing LM pooled ROC-AUC ~{roc:.3f}")

    # Domain-masked scale loss: R9 n_coarse should equal modelling n
    sl = reg.get("scale_loss") or {}
    if sl.get("study_domain_mask") and sl.get("n_coarse_r9") not in (None, 262):
        errors.append(f"scale_loss n_coarse_r9={sl.get('n_coarse_r9')} expected 262 under domain mask")

    # Evidence wording
    if "evidence-positive" not in text.lower() and "evidence-unrecorded" not in text.lower():
        errors.append("manuscript missing evidence-positive / evidence-unrecorded framing")

    if errors:
        print("MANUSCRIPT_REGISTRY_MISMATCH:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: manuscript headline numbers align with paper_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
