# ChatGPT round R12 — innovation/novelty positioning + related-work gaps (text only)

**Public repo (read-only, fetch raw files):** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3
**Raw manuscript:** https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/manuscript.md
**Raw report:** https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/report.md
**Raw audit doc:** https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/audit.md
**Raw README:** https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/README.md

## What changed since R11 (all landed + committed + pushed, verified live)

1. **Baseline bug fixed.** `_majority_baseline()` no longer calls always-positive the "majority" class. The code now reports BOTH constant classifiers (always-positive AND always-negative) per fold with fold-mean aggregation, and derives the true constant-majority from pooled class counts. Expanded pilot: 458 pos / 498 neg, so majority = negative. Model accuracy 0.642 > 0.521 (true majority) and > 0.479 (always-positive); model F1 0.608 < 0.641 (fold-mean always-positive).
2. **Out-of-fold discrimination materialized.** ROC-AUC and average precision (PR-AUC) now archived from held-out per-cell probabilities. LM smoke: pooled ROC-AUC 0.683, PR-AUC 0.861 (random baseline 0.801). Expanded: pooled ROC-AUC 0.703, PR-AUC 0.723 (random baseline 0.479).
3. **Manuscript rewritten** in a plainer academic register (removed AI-summary/review tone); report.md softened to "extent-sensitivity hypothesis" (no longer claims the 80% prevalence was a proven spatial artifact).
4. **Figure 1 updated**: Sandy as a dashed side-channel bypassing learning; footer "Manhattan open-data pilots"; PFI_h output box notes flat scenario response.
5. **New audit doc** `docs/paper/audit.md` proving data authenticity/accuracy/completeness.

## Live numbers (locked; verify against the JSON/CSV in the repo)

- LM smoke (n=141, 5 folds / 7 blocks): acc 0.784 ± 0.069, F1 0.866, R² 0.030 ± 0.343, prevalence 0.801, always-positive acc/F1 0.808/0.893.
- Expanded (n=956, 5 folds / 28 blocks): acc 0.642 ± 0.148, F1 0.608, R² 0.525 ± 0.112, prevalence 0.479, always-positive acc/F1 0.479/0.641, majority (negative) acc 0.521.
- Jaccard mean R10→R8 = 0.167; adaptive/uniform cell-count ratio ≈ 0.569 (79/141 parents refined).

## R12 focus — novelty positioning and related work (do NOT change the science)

Read the manuscript Introduction + Related work + Discussion. Tell me, concretely and with locations:

1. **Is the contribution claim honest AND sharp?** The paper currently positions itself as "open labels + spatial H3-block CV + adaptive refinement + a rainfall-conditioned index PFI_h(c,r), not PFIb." Is that a defensible, publishable novelty, or does it read as a thin re-skin of Svellingen et al. 2026? Where does the manuscript under-sell or over-sell the gap?
2. **Related-work framing.** Are the four related-work paragraphs (building indices→H3; DGGS substrate; spatial holdouts in GeoAI; urban pluvial susceptibility) doing enough to carve out the gap? What is missing or mis-attributed? (e.g., is any citation claimed for work it didn't do?)
3. **The PFI_h(c,r) notation collision.** We reuse the symbol from Svellingen but redefine it as a rainfall-conditioned model probability. Is the current one-paragraph disambiguation sufficient, or does it create more confusion than value? Should we rename it?
4. **Where exactly is the strongest single novelty sentence** in the current manuscript, and is it placed where a reviewer will see it (Abstract + end of Introduction)?
5. Give the next 3 highest-value edits toward a sharper contribution statement, each with file/line location and the exact reason.

Rules: text only, do not upload files; read the repo raw files. Do not invent numbers. Flag any overclaim or underclaim with a quote and a suggested replacement.
