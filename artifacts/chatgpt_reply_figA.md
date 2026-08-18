# ChatGPT FIG-A reply — figure code + data review (2026-08-18)

**Paste package:** `artifacts/chatgpt_paste_figA.md`. (Image upload blocked in this env; review done via verbatim code + data + my 7 visual findings.)

## Recommendations (priority order)

1. **Fig 2 (spatial CV) — redesign first.** Replace grouped bars with paired fold-level markers (Accuracy + F1 offset per fold); add a 6th x-position "Mean ± SD" with error bars. Drop the overlapping `axhspan` bands. Do NOT mark Fold 4 as an outlier (star/warning) — a neutral n=24 note only if sizes shown for all folds.
2. **Fig 3 (jaccard) — de-overlap second.** Replace 3 line series with offset marker series at R8/R9; distinct marker shapes per mean/max/p90; panel titles "Jaccard similarity" / "F1"; move "Fine = R10" to figure level or caption. Keep ylim(0,1.05) so the 1.0 markers don't hit the top spine; don't place labels above 1.0.
3. **Fig 1 (workflow) — text compression third.** Shorten every box to noun phrases. Stage 3 → "Gradient boosting / H3-block CV / Logistic, ponding & constant baselines." Stage 4 → separate "PFI_h(c,r)", "Scale-loss diagnostics", "Adaptive refinement", "Sandy coastal-overlap diagnostic". Route dashed Sandy arrow only into the Sandy diagnostic box.
4. **Fig 4 (adaptive) — annotation fourth.** Keep linear axis + 3 bars + count labels; add two compact annotations "27.9× fixed" and "56.9% of uniform R11". Relabel categories to encode resolution: "Fixed R9" / "Adaptive R9/R11" / "Uniform R11".

## Additional notes
- Fig 3: 1.0 values sit at the hard metric ceiling → keep ylim(0,1.05); place any direct labels below the marker, not above.
- Fig 2: singling out Fold 4 visually implies post-hoc skepticism → avoid outlier styling.
