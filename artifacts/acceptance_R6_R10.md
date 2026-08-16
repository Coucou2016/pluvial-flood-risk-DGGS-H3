# Acceptance report — R6–R10 paper maturation (§十九 style)

**Date:** 2026-08-17  
**Public GitHub (locked):** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**Preferred ChatGPT chat:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Force-push / repo recreate:** **Not used**

## §十九 checklist

| Item | Status |
|------|--------|
| Progress | R6–R10 paste packages written; manuscript/report/README matured; HTML rebuilt; pushed to `origin/master` |
| ≥5 new ChatGPT paste packages | **Yes** — `artifacts/chatgpt_paste_R6.md` … `R10.md` |
| ≥5 ChatGPT substantive replies captured live via browser | **No** — MCP tabs vanish immediately (`No browser tab available` / `Browser view not found`) |
| Manual URL pack for user | `artifacts/chatgpt_paste_github_urls_R6_R10.md` |
| Round log | `artifacts/chatgpt_round_log.md` |
| Independent verification | Live CSVs/JSON + WebSearch (Svellingen IJDRR DOI abstract) |
| Paper vs report split | **Enforced** in R6 (paths/process stripped from manuscript) |
| Manuscript | `docs/paper/manuscript.md` + `manuscript.html` |
| Research report | `docs/paper/report.md` + `report.html` (+ root `report.html`) |
| Tests | **Paper-only** this batch (no pipeline code edits); pytest not required |
| Push | See commit SHAs below |

## Commit SHAs (this batch)

| Round | SHA (short) | Message focus |
|-------|-------------|----------------|
| R6 | `093bc00` | Strip manuscript paths; paper/report boundary |
| R7 | `e7f8985` | Related-work polish; honest novelty |
| R8 | `2c133b7` | Results honesty vs live metrics |
| R9 | `0f566e0` | Discussion structure; figure captions |
| R10 | d7d51a2 | Full polish; README abstract; acceptance; HTML |

Baseline before batch: `2836ddb`.

## Round outcomes

| Round | Topic | ChatGPT live? | Accepted local edits | Rejected / deferred |
|-------|-------|---------------|----------------------|---------------------|
| R6 | Paper vs report boundary | No | Path/process strip from manuscript; boundary table in report | Advisor URLs in paper |
| R7 | Related work / style / innovation | No | Svellingen-style trade-off framing; honest novelty paragraph; protocol-not-product intro | PFIb parity; Jaccard equality |
| R8 | Results honesty | No | Weak R² disclosure; Fold4/`n_test=24`; flat PFI; cell-count-only adaptive | Rainfall discrimination; runtime savings |
| R9 | Discussion / captions | No | Numbered limitations; journal-ready F2–F4 captions | Inventing F1 schematic |
| R10 | Full polish + README | No | Conclusions polish; README academic abstract pointer; HTML rebuild; URL pack | Fabricated ChatGPT replies |

## Live numbers lock (re-verified)

| Artifact | Key numbers |
|----------|-------------|
| `models/nyc_smoke/run_metadata.json` | n=141; Acc **0.783756 ± 0.069280**; F1 **0.865748**; R² **0.030 ± 0.343** |
| `spatial_cv_folds.csv` | Fold4 Acc 0.917 on `n_test=24` |
| `outputs/jaccard_by_resolution.csv` | mean R10→R8 Jaccard **0.1667** |
| `outputs/adaptive_vs_fixed_ablation.csv` | adaptive/uniform **0.569**; parents refined **79**/141 |
| `outputs/pfi_h_scenarios.csv` | mean PFI_h **0.802888** all scenarios; within-cell range **0** |
| `outputs/negative_control.json` | coastal_only ≈0.057; pluvial−coastal ≈0.120 |

## Checklist of fixes

- [x] Manuscript free of local `outputs/` / `models/nyc_smoke/` path literals and Cursor/ChatGPT process notes  
- [x] Report retains paths, reproducibility, 来龙去脉, and boundary audit  
- [x] Related work reframed vs PFIb→H3 aggregation without overclaim  
- [x] Results scrubbed for soft overclaims (Fold4, Jaccard≈0.14 coincidence, adaptive runtime, flat PFI, weak R²)  
- [x] Discussion limitations numbered; F2–F4 captions academicized; F1 待补充  
- [x] README academic abstract pointer to manuscript  
- [x] `manuscript.html` / `report.html` regenerated  
- [x] R6–R10 paste MDs + URL pack on public GitHub path  
- [ ] Live ChatGPT replies archived (awaiting user paste from preferred chat)

## Remaining 待补充

1. Manual ChatGPT R6–R10 URL-read replies returned to Cursor for archival.  
2. I2 observed event rainfall (non-synthetic provenance).  
3. Non-flat within-cell `PFI_h(c,r)` across rainfall scenarios.  
4. Expanded bbox / citywide profile under the same spatial CV protocol.  
5. FloodNet held-out validation.  
6. Workflow schematic Figure 1.  
7. Additional venue-specific references after advisor literature replies.

## Locked science (unchanged)

Open labels ≠ PFIb; spatial H3-block CV; adaptive H3; `PFI_h` ≠ importance ≠ PFIb; Oslo appendix; fixture≠science; LM≠citywide; reject Jaccard 0.14 equality; flat scenario PFI_h honest (range=0).

## Public URLs (convenience)

- Repo: https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
- Manuscript raw: https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/manuscript.md  
- Report raw: https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/report.md  
- URL pack: https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/artifacts/chatgpt_paste_github_urls_R6_R10.md  
- Acceptance: https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/artifacts/acceptance_R6_R10.md  

## Gates

| Gate | Result |
|------|--------|
| Code touched? | **No** |
| `.venv` pytest | **Skipped** (paper-only; noted) |
| HTML rebuild | **Yes** — `scripts/build_paper_report_html.py` |
| Force-push | **No** |
