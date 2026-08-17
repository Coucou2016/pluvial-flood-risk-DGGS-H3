R20 — final framing + Results prose + figure captions (post-R19)

R19 consistency fixes are applied. Three remaining areas need a final look before I consider the manuscript mature. Answer concisely (accept/reject + one-line rationale).

(1) ABSTRACT UNDERCLAIM. In R18 you noted: "One underclaim: the abstract says what the components are, but not quite the conceptual H3 innovation. A reviewer can still read it as 'H3 plus several standard tools'." The current abstract opening is:

"Intense short-duration rainfall can overwhelm urban drainage and produce pluvial flooding with limited warning, and city-scale screening increasingly relies on machine learning and multi-resolution grids. Some data-driven pluvial-flood screening approaches rely on proprietary damage or insurance labels, while random train-test splits can overstate performance when spatial dependence is not accounted for. This study presents an open-label machine-learning framework for hexagonal pluvial flood screening on the H3 discrete global grid."

Question: should the third sentence be strengthened to state the conceptual H3 innovation (H3 as the common spatial support for learning AND evaluation, not merely a post-hoc aggregation grid), or is the current phrasing adequate? If strengthen, give the exact replacement sentence (keep it ~1 clause, not adding more than ~15 words).

(2) RESULTS NARRATIVE PROSE — content logic + expressions. Review verbatim:

§6.1: "The held-out labels are highly imbalanced (80.1% positive). A trivial always-positive classifier would reach mean accuracy 0.808 and mean F1 0.893 across the same folds, which exceeds the model's 0.784 accuracy and 0.866 F1. Spatial blocking makes the evaluation design more defensible but does not by itself establish discrimination. The threshold-independent out-of-fold metrics are moderate: pooled ROC-AUC is 0.683 and pooled average precision is 0.861, the latter only slightly above the 0.801 prevalence baseline for a random ranker. Fold4 accuracy (0.917) coincides with a small test set (n = 24, two blocks) and is not interpreted in isolation. Continuous-risk R² (0.030 ± 0.343) is weak and reported for completeness. Random-split accuracy (0.690) remains diagnostic only."

§6.6: "The expanded extent is a second, larger open-data pilot (956 cells over 28 blocks), still not citywide. Its held-out labels are near-even (47.9% positive), in contrast to the 80% prevalence of the smaller table. Under the same H3-block protocol, spatial cross-validation accuracy is 0.642 ± 0.148, exceeding both the always-positive baseline (0.479) and the constant majority-class baseline (0.521). Out-of-fold discrimination is moderate: pooled ROC-AUC is 0.703 and pooled average precision is 0.723, the latter clearly above the 0.479 prevalence baseline. Mean F1 (0.608) nevertheless remains below the fold-mean always-positive F1 (0.641). The per-fold spread (accuracy 0.419–0.801; F1 0.343–0.832) coincides with heterogeneous held-out class composition—Fold1 and Fold3 are majority-negative, Fold0 and Fold4 are majority-positive, and Fold2 is nearly balanced (97/94)—and is not attributed to prevalence without further analysis. Continuous-risk R² (0.525 ± 0.112) is a positive blocked signal at this scale. This is reported as a robustness check on the framework, not as citywide skill."

Note: §6.1 still says "The threshold-independent out-of-fold metrics are moderate" and §6.6 says "Out-of-fold discrimination is moderate" — same "moderate" joint-application issue as the §7.2 sentence I just fixed. Should both be rewritten to separate ROC-AUC (ranking discrimination) from AP (prevalence-relative)? Give exact replacements.

(3) FIGURE CAPTIONS 2–4 — final format check (verbatim):
- Fig 2: "Spatial H3-block cross-validation performance for the Lower Manhattan pilot. Classification accuracy and F1 are shown for each of five held-out folds formed from seven R7 H3 blocks (n = 141 cells)."
- Fig 3: "Open-label hotspot scale-loss diagnostics across H3 resolutions. Jaccard similarity and F1 compare R10-derived hotspot sets (top decile, quantile 0.9) with R9 and R8 representations under mean, maximum, and p90 aggregation."
- Fig 4: "Adaptive refinement versus uniform fine grids by cell count. Fixed R9, adaptive mixed R9/R11, and uniform R11 representations are compared for the Lower Manhattan pilot (adaptive/uniform ≈ 0.569; 79 of 141 parents refined)."
Any remaining caption issues? Are they self-contained (a reader should understand without the body)?

(4) §7.3 FUTURE WORK (verbatim): "Future work should (i) ingest observed event rainfall with non-synthetic provenance; (ii) produce non-flat scenarios, that is, a within-cell PFI_h range greater than zero across rainfall intensities on the same static features; (iii) extend to a citywide or larger profile under the same spatial cross-validation protocol; and (iv) perform FloodNet held-out validation when a non-empty sensor layer is available."
Any issue?
