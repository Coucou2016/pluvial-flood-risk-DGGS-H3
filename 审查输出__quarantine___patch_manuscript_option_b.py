"""One-shot manuscript metric rewrite for Major Revision Option B."""
from pathlib import Path

p = Path("docs/paper/manuscript.md")
t = p.read_text(encoding="utf-8")

repls = [
    (
        "On the 141-cell Lower Manhattan R9 support",
        "On the 262-cell Lower Manhattan R9 support (Option B)",
    ),
    (
        "ROC-AUC 0.780 and average precision 0.805 at 67.4% positive prevalence",
        "ROC-AUC 0.847 and average precision 0.851 at 63.0% positive prevalence",
    ),
    (
        "| Accuracy | 0.781 ± 0.123 | 0.821 ± 0.033 |",
        "| Accuracy | 0.809 ± 0.046 | 0.821 ± 0.033 |",
    ),
    (
        "| F1 | 0.822 ± 0.116 | 0.819 ± 0.038 |",
        "| F1 | 0.846 | 0.819 |",
    ),
    (
        "| Evidence-score R² | 0.048 ± 0.348 | 0.333 ± 0.144 |",
        "| Evidence-score R² | 0.227 ± 0.196 | 0.336 ± 0.146 |",
    ),
    (
        "| MAE | 0.330 ± 0.073 | 0.286 ± 0.036 |",
        "| MAE | 0.270 | 0.285 |",
    ),
    (
        "| Pooled ROC-AUC | 0.780 | 0.883 |",
        "| Pooled ROC-AUC | 0.847 | 0.883 |",
    ),
    (
        "| Pooled average precision | 0.805 | 0.812 |",
        "| Pooled average precision | 0.851 | 0.812 |",
    ),
    (
        "| Always-positive accuracy | 0.662 | 0.475 |",
        "| Always-positive accuracy | 0.629 | 0.475 |",
    ),
    (
        "| Always-positive F1 | 0.794 | 0.643 |",
        "| Always-positive F1 | 0.762 | 0.643 |",
    ),
    (
        "| Always-negative accuracy | 0.338 | 0.525 |",
        "| Always-negative accuracy | 0.371 | 0.525 |",
    ),
    (
        "| Majority-class F1 | 0.794 (positive) | 0 (negative) |",
        "| Majority-class F1 | 0.762 (positive) | 0 (negative) |",
    ),
    (
        "for the smaller pilot the positive class is the majority class (67.4%)",
        "for the smaller pilot the positive class is the majority class (63.0%)",
    ),
    ("| Fixed R9 | 141 |", "| Fixed R9 | 262 |"),
    ("| Adaptive R9/R11 | 4,845 |", "| Adaptive R9/R11 | 7,222 |"),
    ("| Uniform R11 | 6,909 |", "| Uniform R11 | 12,838 |"),
    (
        "Across the 141 cells, 31 intersect Sandy",
        "Across the 262 cells, 74 intersect Sandy",
    ),
    (
        "**Table 6. Sandy negative-control statistics on the 141-cell pilot.**",
        "**Table 6. Sandy negative-control statistics on the 262-cell Option B pilot.**",
    ),
    (
        "Lower Manhattan (n = 141) and the expanded pilot (n = 956)",
        "Lower Manhattan Option B (n = 262) and the expanded pilot (n = 956)",
    ),
    ("0.781 vs 0.662; 0.822 vs 0.794", "0.809 vs 0.629; 0.846 vs 0.762"),
    (
        "Jaccard 0.180 to R9, 0.111 to R8 at a matched 10% budget), while adaptive refinement concentrates representation into 70% of a uniform fine grid",
        "Jaccard 0.216 to R9, 0.105 to R8 under area-matched 10% budgets), while adaptive refinement concentrates representation into 56% of a uniform fine grid",
    ),
    (
        "(0.780 and 0.883), with average precision 0.805 and 0.812",
        "(0.847 and 0.883), with average precision 0.851 and 0.812",
    ),
    ("(0.674 and 0.475)", "(0.630 and 0.475)"),
    (
        "The submission version is archived under the immutable tag `submission-v2`; the corresponding commit and provenance of all reported outputs are recorded in the accompanying audit document.",
        "The working tree is currently dirty under Major Revision; an immutable submission tag will be created only after author confirmation. Provenance of reported outputs is recorded in `outputs/paper_results.json` and the accompanying audit document.",
    ),
    (
        "During the preparation of this work the authors used ChatGPT (OpenAI) as an editorial reviewer to review manuscript language, organization, and the presentation of scientific framing. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.",
        "During preparation of this work, generative AI tools (including Cursor/Composer agents) assisted with language editing, code review and debugging, test design, figure consistency checks, and drafting of the technical audit. Authors executed the scientific code, verified numerical outputs against regenerated artifacts, and take full responsibility for the content. Author names, affiliations, ORCID, and CRediT statements remain human placeholders pending confirmation.",
    ),
    (
        "Fixed R9 (141), adaptive mixed R9/R11 (4,845), and uniform R11 (6,909) representations are compared for the Lower Manhattan pilot (adaptive = 34.4× fixed R9 = 70.1% of uniform R11; 98 of 141 R9 cells refined).",
        "Fixed R9 (262), adaptive mixed R9/R11 (7,222), and uniform R11 (12,838) representations are compared for the Lower Manhattan Option B pilot (adaptive = 56.3% of uniform R11; 145 of 262 R9 cells refined).",
    ),
    ("141-cell R9 supervised", "262-cell R9 supervised"),
    (
        "| LM | 1 (R8) | 27 | 0.750 | 0.650 | 0.809 | 0.864 | −0.053 |",
        "| LM | 1 (R8) | 48 | 0.829 | 0.839 | 0.809 | 0.848 | 0.373 |",
    ),
    (
        "| LM | 2 (R7) | 7 | 0.780 | 0.798 | 0.781 | 0.822 | 0.048 |",
        "| LM | 2 (R7) | 12 | 0.847 | 0.831 | 0.809 | 0.846 | 0.227 |",
    ),
    (
        "| LM | 3 (R6) | 3 | 0.697 | 0.586 | 0.840 | 0.899 | −0.319 |",
        "| LM | 3 (R6) | 4 | 0.790 | 0.815 | 0.854 | 0.620 | — |",
    ),
    (
        "Moran's I (composite evidence score): 0.224 (LM), 0.433 (Exp).",
        "Moran's I (composite evidence score): 0.385 (LM), 0.433 (Exp).",
    ),
    (
        "LM = Lower Manhattan (n = 141); Exp = expanded pilot (n = 956).",
        "LM = Lower Manhattan Option B (n = 262); Exp = expanded pilot (n = 956).",
    ),
]

for a, b in repls:
    if a not in t:
        print("MISSING:", a[:90])
    else:
        t = t.replace(a, b)
        print("OK:", a[:70])

# Longer paragraphs via start markers
marker = "The smaller pilot contains 141 R9 cells"
if marker in t:
    start = t.index(marker)
    end = t.index("Table 3 summarises these numbers together with the expanded-pilot results.")
    end = end + len("Table 3 summarises these numbers together with the expanded-pilot results.")
    new = (
        "The smaller pilot contains 262 R9 cells distributed over 12 R7 blocks. "
        "Five-fold spatial cross-validation yields accuracy 0.809 ± 0.046 and F1 0.846 (Fig. 4). "
        "Here SD denotes the population standard deviation across the five held-out folds (ddof = 0). "
        "The held-out labels are positive in 63.0% of cells, and the model exceeds the always-positive "
        "baseline on both accuracy (0.809 vs 0.629) and F1 (0.846 vs 0.762); the always-negative baseline "
        "accuracy is 0.371. Pooled out-of-fold ROC-AUC is 0.847 and pooled average precision is 0.851, "
        "above the 0.630 positive-prevalence reference. The evidence-score R² is 0.227 ± 0.196 and is "
        "reported for completeness; it quantifies fit to the constructed flood-evidence score rather "
        "than to any physical severity variable. Table 3 summarises these numbers together with the "
        "expanded-pilot results."
    )
    t = t[:start] + new + t[end:]
    print("OK: 4.2 paragraph")
else:
    print("MISSING: 4.2 paragraph")

marker = "Fine-resolution hotspots are defined at R10 by exact top-k"
if marker in t:
    start = t.index(marker)
    end = t.index("Fig. 5 maps the R10 open-evidence score surface")
    new = (
        "Fine-resolution hotspots are defined at R10 by tie-aware top-k ranking "
        "(k = round(0.10 × n_fine) of 1857 native R10 cells) with fractional membership at tied "
        "boundary scores—no lexicographic H3-index tie-break. Coarse budgets are matched by "
        "projected parent support area of the fine hotspot rather than equal cell-count fractions; "
        "cell-count “matched budgets” are not claimed. Under mean aggregation the R9 rollup yields "
        "hard Jaccard 0.216 (soft 0.249) and the R8 rollup yields hard Jaccard 0.105 (soft 0.111); "
        "maximum aggregation retains presence far better (hard Jaccard 1.0 at both R9 and R8 under "
        "this protocol). Soft Jaccard, area-weighted overlap, and Spearman rank correlation are "
        "reported alongside hard set metrics. These diagnostics reduce concern about quantile "
        "inflation and H3 tie artefacts but do not prove that coarsening preserves operational "
        "hotspot decisions.\n\n"
    )
    t = t[:start] + new + t[end:]
    print("OK: hotspot paragraph")
else:
    print("MISSING: hotspot paragraph")

old_t4_start = "**Table 4. Scale-loss ladder under exact top-k"
if old_t4_start in t:
    start = t.index(old_t4_start)
    end = t.index("### 4.4 Adaptive versus fixed")
    new = (
        "**Table 4. Scale-loss ladder under tie-aware top-k hotspots "
        "(10% budget; area-matched parent support; fractional membership ties).** "
        "Fine R10 support n = 1857 (Option B). Hard Jaccard shown; soft Jaccard / "
        "area-weighted overlap are in `outputs/jaccard_by_resolution.csv`.\n\n"
        "| Coarse resolution | Aggregation | Jaccard | Soft Jaccard | Fine-parent recall | Coarse precision |\n"
        "|---|---|---|---|---|---|\n"
        "| R9 | Mean | 0.216 | 0.249 | 0.216 | 1.000 |\n"
        "| R9 | Maximum | 1.000 | 0.866 | 1.000 | 1.000 |\n"
        "| R9 | P90 | 0.540 | 0.623 | 0.540 | 1.000 |\n"
        "| R8 | Mean | 0.105 | 0.111 | 0.105 | 1.000 |\n"
        "| R8 | Maximum | 1.000 | 0.947 | 1.000 | 1.000 |\n"
        "| R8 | P90 | 0.526 | 0.556 | 0.526 | 1.000 |\n\n"
        "Note: `matched_budgets_cell_count=false`; budgets are projected-parent-area matched. "
        "The full ladder is plotted in Supplementary Fig. S1.\n\n"
    )
    t = t[:start] + new + t[end:]
    print("OK: table4")
else:
    print("MISSING: table4")

marker = "The R7 block size (k = 2) was fixed a priori, so its adequacy was tested"
if marker in t and "12 R7 blocks" not in t[t.index(marker) : t.index(marker) + 800]:
    start = t.index(marker)
    end = t.index("**Table 8. Block-size sensitivity")
    new = (
        "The R7 block size (k = 2) was fixed a priori, so its adequacy was tested by repeating "
        "the spatial cross-validation with R8 (k = 1) and R6 (k = 3) parent blocks and by computing "
        "Moran's I of the composite evidence score under native R9 k-ring adjacency (Table 8). "
        "The composite target is positively spatially autocorrelated (Moran's I 0.385 in Lower "
        "Manhattan, 0.433 in the expanded pilot), confirming that spatially blocked rather than "
        "i.i.d. splitting is required. In the expanded pilot, ranking discrimination is stable "
        "across block sizes (pooled ROC-AUC 0.888, 0.883, and 0.873 at R8, R7, and R6). The Lower "
        "Manhattan Option B pilot (12 R7 blocks) yields pooled ROC-AUC 0.829 (R8), 0.847 (R7), "
        "and 0.790 (R6; 4 blocks → 4 folds). Block-size sensitivity is therefore reported rather "
        "than deferred as future work.\n\n"
    )
    t = t[:start] + new + t[end:]
    print("OK: block para")
else:
    print("SKIP/MISSING: block para")

p.write_text(t, encoding="utf-8")
print("wrote", p, "chars", len(t))
