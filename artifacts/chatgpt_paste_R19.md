R19 — cross-section consistency audit (post-R18)

R18 edits are applied. Before finalizing I need a cross-section consistency pass over the parts R18 did not cover in full. Please review the verbatim passages below and answer the numbered questions. Do not re-derive the science; focus on internal consistency, terminology, and prose.

(1) NUMBER CONSISTENCY. Cross-check every numeric claim across Abstract → §6 → §7 → §8 and flag any mismatch.
- Small pilot (n=141): acc 0.784±0.069; F1 0.866; always-pos 0.808/0.893; always-neg acc 0.192; ROC-AUC 0.683; AP 0.861; prevalence 0.801; R2 0.030±0.343; MAE 0.332; random acc 0.690.
- Expanded (n=956): acc 0.642±0.148; F1 0.608; always-pos 0.479/0.641; majority(neg) acc 0.521 / F1 0.000; ROC-AUC 0.703; AP 0.723; prevalence 0.479; R2 0.525±0.112; MAE 0.112; random acc 0.667.
Abstract says ROC-AUC "0.68" and "0.70" (vs table 0.683/0.703) and AP "0.86"/"0.72" (vs 0.861/0.723) — acceptable rounding? Any other mismatch?

(2) RESIDUAL PHRASING R18 MISSED — three spots:

(a) §7.2 limitation 6 still reads:
"Out-of-fold ROC-AUC and average precision are moderate in both pilots, so discrimination is supported at a modest level but is not claimed as strong skill."
R18 fixed the analogous "moderate + threshold-independent" wording in §7.1 but this §7.2 sentence was left behind. Rewrite to avoid applying "moderate" jointly to ROC-AUC and AP?

(b) §6.4 reads:
"...so rainfall has zero training variance and a feature importance of 0."
The paper's stated stance is that PFI_h is explicitly NOT feature importance. Is "a feature importance of 0" acceptable here, or should it become "zero predictive contribution" / "zero split usage" to avoid the colliding vocabulary?

(c) §1 contribution paragraph still ends:
"`PFI_h(c,r)` is defined as a rainfall-conditioned model output and is distinct from both feature-importance measures and PFIb. The analysis is methodological and limited to the evaluated pilot extents rather than constituting a citywide operational flood map."
immediately followed by the separate one-sentence notation paragraph:
"Throughout, `PFI_h(c,r)` denotes the trained model's rainfall-conditioned flood-probability output for an H3 cell; it is distinct from the H3-aggregated building-level index of Svellingen et al. (2026), and Section 4.7 provides the formal definition."
This is the residual redundancy your R18 "single highest-value edit" targeted. Should the PFI_h sentence and the scope sentence be deleted from the contribution paragraph (both are covered by the notation sentence + Abstract/Discussion/Conclusions)?

(3) §3 STUDY AREA AND DATA (verbatim):
"Extent. Two Manhattan pilot extents are used. The smaller is a Lower Manhattan bounding box (approximately 74.02–73.97°W, 40.70–40.76°N); the larger (manhattan_expanded) extends northward to approximately 74.03–73.94°W, 40.68–40.80°N. Both are pilot extents within New York City, not a citywide extent."
"Layers. ... Event rainfall is a constant synthetic rainfall condition representing the Ida-like scenario, not radar or gauge data."

(4) §5 EXPERIMENTAL DESIGN (verbatim, table): E1 assemble table; E2 spatial CV; E3 baselines; E4 Jaccard ladder; E5 adaptive refinement/ablation; E6 rainfall scenarios; E7 Sandy negative control.

(5) TERMINOLOGY UNIFORMITY check:
- §4.2 says "Rainfall is represented as a separate scenario-conditioning feature (rainfall intensity)" but §3 says "rainfall condition r" and §4.7 says "rainfall condition r" and "constant synthetic rainfall input". Should §4.2 say "rainfall condition" for uniformity?
- §3 says "Ida-like scenario"; §6.4 says "Ida-like (75)"; is "Ida-like" consistent everywhere (no "hook" residue)?

(6) FIGURE 1 CAPTION vs §4.1–4.8: the caption says "R9... R10... R11" and "R10 never participates in training" per §4.1. Is the caption's workflow description consistent with §4.1–4.8 (roles of R9/R10/R8/R11)?

Please answer concisely with accept/reject + one-line rationale per item.
