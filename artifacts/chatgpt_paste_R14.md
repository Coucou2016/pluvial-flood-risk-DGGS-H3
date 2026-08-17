# ChatGPT round R14 — Results presentation + figure/table format + captions (text only)

**Public repo:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 (master current; commit 49e756e)
**R13 outcome:** Methods §4.1–4.8 rewritten for reproducibility with code-verified definitions (target construction, R7-parent GroupKFold, ponding-rule equation, seed 42, hotspot/adaptive quantiles, PFI_h probability semantics). Landed + pushed.

## Current figure captions (verbatim)

- **Figure 1** — "Open-label H3 pluvial flood learning protocol (workflow). Conceptual pipeline. (1) Open multi-source inputs: flood labels (DEP stormwater polygons, 311 flooding points, USGS Ida high-water marks), static predictors, and a rainfall condition r (a synthetic constant hook in this pilot, not radar). (2) H3 assembly at R9 with provenance tags. (3) Learning and blocked evaluation: gradient-boosting classifier + continuous-risk regressor, H3-block GroupKFold spatial CV as primary blocked evaluation, constant-class baselines (always-positive and always-negative), and logistic/ponding-rule baselines. (4) Diagnostics and outputs: PFI_h(c,r) (a definition/interface in this pilot, with currently flat scenario response), a scale-loss Jaccard ladder (R10 to R9/R8), adaptive refinement, and a Sandy negative-control diagnostic."
- **Figure 2** — "Spatial H3-block cross-validation fold metrics. Per-fold classification accuracy and F1 on the Lower Manhattan pilot (n=141; 5 folds; 7 blocks). Primary reporting uses mean ± sd across folds; individual high folds (e.g. Fold4) are not interpreted as citywide skill, and accuracy/F1 are reported alongside constant-class baselines."
- **Figure 3** — "Open-label scale loss across H3 resolutions. Jaccard similarity and F1 between fine (R10) hotspot parent sets and coarse (R8/R9) hotspot sets under mean, maximum, and p90 aggregation. Mean aggregation at R8 yields Jaccard ≈0.167, consistent with smoothing of local extremes; max and p90 preserve extrema by construction. Must not be equated to Svellingen et al.'s PFIb Jaccard of 0.14."
- **Figure 4** — "Adaptive refinement versus uniform fine grids (cell counts). Fixed coarse (R9), adaptive mixed, and uniform fine (R11) cell counts for the pilot table (adaptive/uniform ≈ 0.569; 79 of 141 parents refined). The comparison is restricted to cell counts; not a wall-clock or citywide runtime claim."

## Results tables (labels as they currently appear — flag any that are unpolished)

§6.1 smoke table rows include: n_cells; spatial_cv_n_folds; spatial_cv_n_blocks; spatial_cv_accuracy_mean ± std; spatial_cv_f1_mean; spatial_cv_r2_mean ± std; spatial_cv_mae_mean; random_split_val_accuracy (diagnostic only); positive-class prevalence (held-out); always-positive (majority) baseline accuracy; always-positive (majority) baseline F1; always-negative baseline accuracy; spatial_cv_roc_auc_pooled; spatial_cv_pr_auc_pooled.

§6.6 expanded table rows include: n_cells; spatial_cv_n_folds; spatial_cv_n_blocks; spatial_cv_accuracy_mean ± std; spatial_cv_f1_mean; spatial_cv_r2_mean ± std; spatial_cv_mae_mean; random_split_val_accuracy (diagnostic only); positive-class prevalence (held-out); always-positive baseline accuracy; always-positive baseline F1 (fold-mean); constant majority-class (always-negative) baseline accuracy; constant majority-class (always-negative) baseline F1; spatial_cv_roc_auc_pooled; spatial_cv_pr_auc_pooled.

§6.2 Jaccard table; §6.3 adaptive table (score used for screening PFI_h; n_fixed_coarse 141; n_adaptive_mixed 3933; n_uniform_fine 6909; adaptive_cell_count_ratio 0.569; n_parents_refined 79; score_quantile 0.8); §6.4 rainfall scenarios; §6.5 Sandy negative control (n_cells 141; n_coastal 31; n_pluvial 71; n_both 23; n_coastal_only 8; frac_coastal_only ≈0.057; pluvial-minus-coastal mean score ≈0.120).

## Figures themselves (for format review)

- All figures are matplotlib + SciencePlots style, Times New Roman, generated to `docs/paper/figures/` as PNG (and embedded in the HTML report). Font sizes: titles ~11pt, axis/tick labels ~9–10pt, captions ~9pt.
- Figure 1 is a pure schematic (matplotlib boxes/arrows). Figure 2 is a grouped bar of fold accuracy/F1. Figure 3 is a grouped bar of Jaccard/F1 across resolution+aggregation. Figure 4 is a grouped bar of cell counts (fixed/adaptive/uniform).

## R14 focus (do NOT change science/results/numbers)

1. **Table polish.** Which table row labels are internal JSON field names rather than reader-facing labels? Give the exact clean replacement for each (e.g., "spatial_cv_roc_auc_pooled" → "ROC-AUC (pooled out-of-fold)"). Is "always-positive (majority)" in §6.1 acceptable given that pilot is 80% positive, or should it be relabeled for consistency with §6.6?
2. **Captions.** Are the four captions complete and self-contained? Any caption that overclaims, underclaims, or omits a quantity a reader needs (units, n, panel explanation)? Are figure numbers referenced in the main text at the right places?
3. **Figure format (journal convention).** For an IJDRR-style submission: are the current font sizes, legend placement, and the four-panel/bar-chart choices appropriate? Any specific, concrete format fix (e.g., "Figure 3 should use log-scale", "Figure 2 should show error bars", "legends should be removed because groups are self-evident")?
4. **Results narrative.** Does the Results prose lead with the table it describes, or does it bury key comparisons? Any sentence that states a number not present in its table, or a table row never discussed in prose?
5. Give the next 3 highest-value Results/figure edits, each with exact location and reason.

Rules: text only; do not invent numbers; if a figure detail (exact DPI, exact font pt) is not stated, say so rather than guessing.
