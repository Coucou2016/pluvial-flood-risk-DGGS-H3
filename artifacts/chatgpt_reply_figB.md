# ChatGPT FIG-B reply — re-review of applied fixes (2026-08-18)

**Paste package:** `artifacts/chatgpt_paste_figB.md`.

## Verdict: FIG-A redesigns solved the substantive problems; remaining = final-layout polish.

1. **Fig 4 — ACCEPT (minor):** make the top annotation two centered lines ("Adaptive = 27.9× fixed R9" / "= 56.9% of uniform R11"); use × not x; keep y based on data max (6909), not padded ylim.
2. **Fig 3 — ACCEPT:** caption must state reference support explicitly → "Jaccard similarity and F1 compare hotspot sets defined on the reference fine support, H3 R10, with R9 and R8 representations under mean, maximum, and p90 aggregation."
3. **Fig 2 — REVISE:** set summary position to mx = len(df) + 0.5 (extra gap) so "Mean ± SD" doesn't read as a sixth fold.
4. **Fig 1 — ACCEPT (check font size/overflow at final journal size):** verify no text touches box edges; if Stage 4 cramped, increase column height rather than shrink fonts.
5. **Remaining minor:** Fig 2 — ddof consistency (df.std() default ddof=1 matches sample SD); errorbar must not add a 2nd legend entry (it doesn't, no label passed). Fig 3 — ONE shared figure legend (not duplicate per-panel); symmetric x-limits around R8/R9. Fig 1 — "PFI_h screens → R11" → "PFI_h-guided → R11". make_figures.py — good (reads locked CSVs, emits PDF+PNG).
