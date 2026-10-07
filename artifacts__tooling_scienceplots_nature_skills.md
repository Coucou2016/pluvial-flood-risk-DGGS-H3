# Tooling note — SciencePlots & nature-skills

**Date:** 2026-08-16

## SciencePlots (project `.venv`)

```text
E:\Projects\20260522-pluvial-flood-risk-DGGS-H3\.venv\Scripts\python.exe -m pip install SciencePlots
```

- Package: **SciencePlots 2.2.2**
- Location: `.venv\Lib\site-packages`
- Also declared in `pyproject.toml` optional extras `plot` / `dev`
- Figure API: `pluvial_flood_risk.figures.apply_paper_style()` uses `plt.style.use(["science", "no-latex"])` + Times New Roman; CJK fallback (SimSun / Noto / YaHei) when Chinese detected in titles/captions

## nature-skills (Cursor skill path — already present)

- **Not** an npm/pip package for this workspace.
- Located at: `C:\Users\Administrator\.cursor\skills\nature-skills\`
- Used skill: `nature-writing` (`skills/nature-writing/SKILL.md`)
- Detected axes for this draft: `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (IJDRR-compatible structure + Nature claim discipline)
- Stance applied: no invented results; claim/evidence/boundary first; gaps marked 待补充

No additional pip install of nature-skills was required or found on PyPI as a manuscript engine for this project.
