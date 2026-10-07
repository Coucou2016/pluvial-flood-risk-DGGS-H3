# Acceptance report — paper path sprint (2026-08-16)

## §十九-style checklist for parent / user

| Item | Status |
|------|--------|
| ChatGPT URL(s) | Intended: https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2 — **browser MCP could not open any tab** (`No browser tab available` even with `newTab: true`). No login/CAPTCHA observed (page never loaded). Brief ready: `artifacts/chatgpt_literature_brief.md` |
| Baseline | **NO_GIT** (no `.git`; not initialized). Local-only; **no commit / push / PR / deploy** |
| Context sent to ChatGPT | Not delivered via browser. Independent WebSearch + conclusions persisted |
| Advisor suggestions accepted | IJDRR-shaped structure + Nature claim discipline; open-label / spatial CV / adaptive / `PFI_h` innovations (from independent survey + locked positioning) |
| Rejected / refused claims | PFIb reproduction; Jaccard=0.14 equality; citywide from LM smoke; radar rainfall; empirical rainfall discrimination from flat scenario CSV; fixture/Oslo as science |
| I2 rainfall | **Blocked** — synthetic `event_raster` only; documented; proceeded with paper/report from live outputs |
| SciencePlots | Installed in `.venv` (2.2.2); figures regenerated |
| nature-skills | Cursor skill path present (`nature-writing`); documented in `artifacts/tooling_scienceplots_nature_skills.md` — not a pip package |
| Tests | `pytest -q`: **57 passed, 1 skipped**. `pluvial-smoke`: **OK** (synthetic demo). `nyc_smoke_test()` re-run: **OK** (~8.5 min live assemble/adaptive; exit 0) |

## Deliverable paths

| Artifact | Path |
|----------|------|
| Manuscript MD | `docs/paper/manuscript.md` |
| Manuscript HTML | `docs/paper/manuscript.html` |
| Manuscript PDF | `docs/paper/manuscript.pdf` (Chrome headless `--print-to-pdf`) |
| Report HTML (primary) | `docs/paper/report.html` |
| Report HTML (root copy) | `report.html` |
| Report MD | `docs/paper/report.md` |
| Report PDF | `docs/paper/report.pdf` (Chrome headless; WeasyPrint broken GTK; xhtml2pdf failed on CSS `var()`) |
| Innovation framework | `docs/paper/innovation_and_framework.md` |
| Literature conclusions | `artifacts/literature_architecture_conclusions.md` |
| ChatGPT paste brief | `artifacts/chatgpt_literature_brief.md` |
| Figures | `docs/paper/figures/*.png`, `artifacts/figures/*.png`, `outputs/jaccard_by_resolution.png` |
| HTML builder | `scripts/build_paper_report_html.py` |

## Live numbers used (not fabricated)

- Spatial CV accuracy 0.784±0.069, F1 0.866, n=141 (`models/nyc_smoke/run_metadata.json`)
- Jaccard mean R10→R8 = 0.167 (`outputs/jaccard_by_resolution.csv`)
- Adaptive/uniform ratio ≈ 0.569 (`outputs/adaptive_vs_fixed_ablation.csv`)
- Scenario `PFI_h` within-cell range = **0** (honest gap)

## Code / config changes

- `src/pluvial_flood_risk/figures.py` — SciencePlots + TNR + CJK fallback; spatial CV & adaptive plot helpers
- `pyproject.toml` — SciencePlots in `plot`/`dev` extras
- `artifacts/prioritized_fix_plan.md` — I2 blocked note; I5/I6 added

## Risks

1. ChatGPT advisor reply still missing until parent pastes brief.
2. Flat `PFI_h` scenarios undermine empirical event-conditioning claims until fixed (I6).
3. PDF via Chrome headless may omit some print CSS nuances; HTML is canonical.
4. Concurrent `pluvial-nyc-smoke` instances can stall; avoid parallel smoke runs.

## Local-only status

All work remains on disk under `E:\Projects\20260522-pluvial-flood-risk-DGGS-H3`. No remote publish.
