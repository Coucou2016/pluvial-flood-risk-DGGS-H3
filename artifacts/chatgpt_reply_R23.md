# ChatGPT R23 reply — real image visual review (2026-08-19)

**Channel:** 4 PNGs uploaded by user into ChatGPT; ChatGPT confirmed it opened and inspected each image directly. manuscript.md still Cache-miss on its side, so prose cross-check used the R18–R21 pasted text + the 4 real PNGs.

## Verdict: figures numerically correct; only small surgical fixes needed.

### Fig 1 workflow — 小修后定稿
1. `PFI_h(c,r)` / `PFI_h-guided` still use code-style underscore; should be true math subscript `PFI_h(c,r)` and `PFI_h-guided → R11`.
2. **Most substantive:** "Static predictors" box lists only elevation/slope/impervious/building density/distance-to-water, but Methods §4.2 also includes flow-accumulation proxy and urban-land flag → box reads as a "complete list" and under-reports features. Minimal fix: summarize ("terrain, flow accumulation, land cover, buildings, hydrologic proximity") or prefix `e.g.,`.
3. Optional: add "(R7 parent blocks)" to the H3-block GroupKFold CV line.
4. Sandy dashed channel now unambiguous — fix confirmed good.

### Fig 2 spatial CV — 数值正确
- x-label "H3-block spatial CV fold" is semantically off because the last x-position is the "Mean ± SD" summary (not a fold). Change to "H3-block spatial CV".
- ddof=0 fix confirmed consistent.

### Fig 3 jaccard — 数值正确
- Legend "mean / max / p90" → "Mean / Maximum / P90" (avoid code-style field names).

### Fig 4 adaptive — 数值完全一致
- Re-verified 27.9× (3933/141=27.8936) and 56.9% (3933/6909=0.56926).
- Optional only: red/green not colorblind-friendly; single neutral palette acceptable. NOT must-fix.

### Five-category manuscript notes
- [创新性] accept; optionally define "open-label" at first use: "open-label, i.e. labels derived from publicly accessible flood observations".
- [文字] "demonstrate the framework end-to-end" → "demonstrate implementation and evaluation of the framework on the stated pilot extents" (remove SW-engineering flavor).
- [内容逻辑] Fig 1 predictor list vs §4.2 (the one substantive fix above).
- [图片格式] final physical column width still the only production item.
- [表述] three in-figure terminology unifications (PFI_h subscript; Mean/Maximum/P90; x-label).

## No figure–table numeric conflict found this round.
