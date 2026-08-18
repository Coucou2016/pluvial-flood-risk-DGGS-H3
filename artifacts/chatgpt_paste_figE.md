FIG-E — round 5 (final): holistic figure-set sign-off

This is the final round. Summarising the complete figure audit across FIG-A→D so you can give a closing verdict.

== What changed (figures.py, all four) ==
1. Fig 1 workflow: compressed to noun phrases; "PFI_h-guided → R11"; Sandy box relabelled "FEMA Sandy negative control (never a training label)"; dashed Sandy arrow enters only the "Sandy coastal-overlap diagnostic" box.
2. Fig 2 spatial CV: grouped bars → paired markers (o/s) + a "Mean ± SD" x-position (x = len+0.5) with diamond+error bars; SD now population (ddof=0) to match the table exactly (accuracy 0.0693, F1 0.0437).
3. Fig 3 jaccard: line series → offset markers with distinct shapes/colors per mean/max/p90; panel titles "Jaccard similarity"/"F1"; ONE shared horizontal legend below panels; symmetric x-limits; ylim(0,1.05).
4. Fig 4 adaptive: labels "Fixed R9 / Adaptive R9/R11 / Uniform R11"; value labels 141 / 3,933 / 6,909; two-line top annotation "Adaptive = 27.9× fixed R9 = 56.9% of uniform R11".

== Caption + table sync (manuscript.md, report.md, HTML) ==
- Fig 2/3/4 captions rewritten to match (no "bars"/"reference bands"/"linestyle" remain).
- Fig 3 caption now states "reference fine support, H3 R10".
- Fig 4 caption states 27.9× and 56.9%.
- Manuscript §6.1: F1 row now "0.866 ± 0.044"; added "SD denotes population SD (ddof=0)" note.
- report.md: F1 0.865748 ± 0.043729.

== Reproducibility ==
- New scripts/make_figures.py regenerates all four from locked CSVs (PNG+PDF). Tests 2 passed.

== Data integrity (locked values, unchanged) ==
- Fig 2 folds: acc [0.7551,0.7600,0.7727,0.7143,0.9167], f1 [0.850,0.850,0.872,0.812,0.944].
- Fig 3: R8 mean J/F1 = 0.1667/0.286; R9 mean 0.9767/0.988; max/p90 structurally ~1.0.
- Fig 4: 141 / 3,933 / 6,909.

== One remaining production item (not yet done) ==
Final column-width sizing: figures are authored at 6.0–11.2 in wide; when scaled to a journal single column (~3.5 in) the 7.4–10.5 pt text would shrink below legibility. This is a submission-template step, not a content/correctness issue.

== QUESTION ==
Q1. Final verdict: are the four figures + captions now internally consistent, numerically reconciled, and free of substantive design/correctness defects? State any last must-fix vs. defer-to-submission item, so I can mark the figure audit complete.
