# Acceptance report — paper path continuation (2026-08-16 §十九)

## §十九-style checklist for parent / user

| Item | Status |
|------|--------|
| Progress | Continued from prior Paper+SciencePlots sprint; critical thin-report gap addressed |
| ChatGPT URL | https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2 |
| ChatGPT web-search literature | **Not delivered** — `cursor-ide-browser` MCP absent; CallMcpTool/`open_resource` failed (`unknown agent` in subagent). Brief ready: `artifacts/chatgpt_literature_brief.md` |
| ChatGPT GitHub-read | **No** — remote not created |
| Independent literature WebSearch | **Yes** → `artifacts/literature_architecture_conclusions.md` |
| SciencePlots + TNR | Verified in `.venv`; figures present under `docs/paper/figures/` |
| nature-writing axes | `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (documented in manuscript + literature conclusions) |
| Deep report | `docs/paper/report.md` now **~19 KB** (was ~3 KB); HTML rebuilt from MD with 3× Base64 figures; PDF regenerated |
| Tests | `pytest -q`: **57 passed, 1 skipped** (45.29s) |
| GitHub URL | **BLOCKED** — portable `gh` 2.97.0 available but **not logged in** (no token). Local commit only |
| Local git | `git init` + root commit `e6100bc` on `master` (118 files). Used per-command `-c safe.directory=...` and one-shot `-c user.name/email=...` (no persistent `git config` writes) |
| Deploy / migration / production | **None** |
| Force-push | **Not used** |

## Deliverable paths

| Artifact | Path | Notes |
|----------|------|-------|
| Deep report MD | `docs/paper/report.md` | ~19357 bytes; teacher-like 来龙去脉 |
| Report HTML | `docs/paper/report.html` + root `report.html` | ~427517 bytes; 3 Base64 PNGs; inline CSS; no CDN |
| Report PDF | `docs/paper/report.pdf` + root `report.pdf` | ~1.14 MB via Chrome `--headless=new` |
| Manuscript | `docs/paper/manuscript.md/.html/.pdf` | Git baseline note updated |
| Literature conclusions | `artifacts/literature_architecture_conclusions.md` | Updated |
| Collaboration | `artifacts/chatgpt_collaboration_report.md` | Updated |
| HTML builder | `scripts/build_paper_report_html.py` | MD→HTML + figure inject |

## GitHub: what would be pushed vs excluded

**Included in local commit (intended remote contents):** `src/`, `tests/`, `scripts/`, `configs/`, `docs/paper/`, selected `artifacts/` (no ZIPs/CDP inject), `outputs/*.csv|json|png` (small), `models/nyc_smoke/*.json|csv`, `data/raw/DATA_SOURCES.md` + gitkeeps, README, pyproject, CI workflow.

**Excluded (by `.gitignore` / not staged):**
- `data/raw/**/*.tif|tiff|geojson` (~63.5 MB raw stack)
- `*.joblib` model binaries
- large `*.parquet` / `risk_cells.geojson` / `_bench.*`
- `.venv/`, chrome PDF profiles, audit `artifacts/*.zip`, inject/CDP payloads

**To finish remote publish after auth:**

```text
# from portable gh or installed CLI
gh auth login
gh repo create pluvial-flood-risk-DGGS-H3 --private --source=. --remote=origin --push
```

Then paste the resulting URL into ChatGPT with the literature brief.

## Live numbers used (not fabricated)

- Spatial CV accuracy **0.783756 ± 0.069280**, F1 **0.865748**, n=141  
- Jaccard mean R10→R8 = **0.1667**  
- Adaptive/uniform ratio ≈ **0.569**  
- Scenario within-cell `PFI_h` range = **0** (honest gap; mean ≈0.802888 all scenarios)

## Honest 待补充

1. ChatGPT web-search reply + (after push) GitHub-read confirmation  
2. I2 observed event rainfall  
3. Non-flat `PFI_h(c,r)` response  
4. Citywide / expanded bbox primary results  
5. FloodNet held-out validation  
6. Workflow schematic figure  
7. `gh auth login` → remote URL  

## Locked science (unchanged)

Open labels ≠ PFIb; spatial H3-block CV; adaptive H3; `PFI_h` ≠ importance ≠ PFIb; Oslo appendix; fixture≠science; LM≠citywide; reject Jaccard 0.14 equality.
