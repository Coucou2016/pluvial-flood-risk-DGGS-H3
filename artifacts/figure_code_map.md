# Figure ↔ Code ↔ Data mapping + self-audit (2026-08-18)

All four figures live in `docs/paper/figures/` (PNG + PDF). Stale duplicates exist in
`artifacts/figures/` (older timestamps) and must NOT be used. Generating code is
`src/pluvial_flood_risk/figures.py`.

## 1:1 mapping

| Figure | File | Generating function (figures.py) | Data source | Wired into a script? |
|--------|------|----------------------------------|-------------|----------------------|
| Fig 1 | `workflow_schematic.png` | `plot_workflow_schematic()` (L214–389) | none (conceptual) | only via `tests/test_figures.py` |
| Fig 2 | `spatial_cv_folds.png` | `plot_spatial_cv_bars()` (L166–211) | `models/nyc_smoke/spatial_cv_folds.csv` | **NOT wired** (no script calls it) |
| Fig 3 | `jaccard_by_resolution.png` | `plot_jaccard_ladder()` (L99–163) | `outputs/jaccard_by_resolution.csv` | via `pipeline.py:440` / `rollups.py:199` |
| Fig 4 | `adaptive_ablation.png` | `plot_adaptive_ablation()` (L392–435) | `outputs/adaptive_vs_fixed_ablation.csv` | **NOT wired** (no script calls it) |

**Finding 0 (reproducibility):** `plot_spatial_cv_bars` and `plot_adaptive_ablation` have
no script entry point — they were generated ad-hoc and are not reproducible from a command.
Fig 1 is only produced by its unit test. This must be fixed (one `scripts/make_figures.py`).

## Data values (locked, live artifacts)

- Fig 2 (`spatial_cv_folds.csv`): fold acc [0.7551, 0.7600, 0.7727, 0.7143, 0.9167],
  F1 [0.850, 0.850, 0.872, 0.812, 0.944]; means 0.784 / 0.866.
- Fig 3 (`jaccard_by_resolution.csv`): fine=R10; coarse ∈ {8, 9}; aggregation ∈ {mean,max,p90}.
  R8: mean J=0.1667/F1=0.286; max J=1.0/F1=1.0; p90 J=1.0/F1=1.0.
  R9: mean J=0.9767/F1=0.988; max J=1.0/F1=1.0; p90 J=0.9767/F1=0.988.
- Fig 4 (`adaptive_vs_fixed_ablation.csv`): fixed=141, adaptive=3933, uniform fine=6909.

## Self-audit defects (visual + code)

1. **Fig 4 — linear axis hides the fixed-coarse bar.** 141 vs 6909 on a linear scale renders
   the "Fixed coarse" bar as a ~2%-height sliver, nearly invisible. Fails to convey the
   27.9× vs 0.57 ratio. Fix: log scale or explicit ratio annotations, or a 3-panel ratio view.
2. **Fig 3 — degenerate "ladder".** Only 2 coarse resolutions (R8, R9); "max" is a flat 1.0
   line in both panels; "p90" coincides with "max" at R8 (both 1.0) and with "mean" at R9
   (both 0.9767). Three legend entries but the curves are largely coincident → misleading.
   Fix: annotate that max/p90 preserve hotspots by construction, or restyle/annotate.
3. **Fig 3 — x-axis is coarse_res (8,9), but fine R10 never appears on the axis.** "Fine = R10"
   title only on the left panel; right panel title is empty. Confusing.
4. **Fig 2 — mean±SD bands overlap.** Accuracy band (0.78±0.07) and F1 band (0.87±0.05)
   overlap heavily; legend has 2 entries but the plot has 4 visual channels (2 bars + 2
   dashed lines + 2 shaded bands), unexplained in legend.
5. **Fig 2 — Fold4 (0.917, n=24) outlier not flagged in-figure.** Text flags it, figure doesn't.
6. **Fig 1 — text density/overflow risk.** Stage-4 PFI_h box carries ~4 wrapped lines at
   7.4 pt; stage-3 has 4 items (others have 3) so its boxes are shorter; Sandy dashed channel
   arrow enters the bottom of column 4 without a clear target box.
7. **Fig 1 — "constant-class baselines" + "Baselines: logistic / ponding rule"** redundant
   "baselines" wording; also caption repeats what the box already says.

## Next actions
1. Add `scripts/make_figures.py` wiring all four plot functions to their data (Finding 0).
2. Fix Fig 4 (log/ratio), Fig 3 (annotation + axis), Fig 2 (band simplification), Fig 1 (spacing/wording).
3. Regenerate + re-read to verify.
4. Drive ChatGPT review via verbatim code + data + structured findings (image upload blocked).

## Resolution (5 rounds FIG-A→E with ChatGPT, 2026-08-18) — ALL RESOLVED

| Finding | Fix |
|---------|-----|
| 0 (no script entry for Fig 2/4) | Added `scripts/make_figures.py` (regenerates all 4 from locked CSVs, PNG+PDF). |
| 1 (Fig 4 fixed bar invisible) | Kept linear bars; added value labels + two-line top annotation "Adaptive = 27.9× fixed R9 = 56.9% of uniform R11"; relabelled categories to Fixed R9 / Adaptive R9/R11 / Uniform R11. |
| 2 (Fig 3 coincident series) | Line series → offset markers (o/s/^) with distinct colors per mean/max/p90. |
| 3 (Fig 3 fine R10 off-axis) | Moved "reference fine support H3 R10" into the caption; panel titles now "Jaccard similarity"/"F1". |
| 4 (Fig 2 band clutter) | Grouped bars + axhspan → paired markers + single "Mean ± SD" x-position (x=len+0.5) with diamond error bars. |
| 5 (Fig 2 Fold4 outlier) | No outlier styling (per ChatGPT: avoid implying post-hoc skepticism). |
| 6/7 (Fig 1 text overflow/redundancy) | Compressed all boxes to noun phrases; merged baselines; "PFI_h-guided → R11"; Sandy box → "FEMA Sandy negative control"; arrow targets "Sandy coastal-overlap diagnostic" box. |
| NEW (Fig 2 SD ddof bug) | Figure used `df.std()` (ddof=1 → 0.0775) but manuscript locked 0.784 ± 0.069 (ddof=0). Fixed to `std(ddof=0)`; added F1 SD 0.866 ± 0.044 + "population SD" note. |

**ChatGPT final verdict (FIG-E): ACCEPT.** Remaining = defer-to-submission final column-width typography only.

