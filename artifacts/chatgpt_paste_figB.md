FIG-B — round 2: applied your FIG-A fixes; please re-review

I applied all four of your FIG-A recommendations. Below are the key code changes and what each figure now shows. Please re-review the code and flag any remaining issues (correctness, legibility, publication quality). Image upload is still blocked here, so I give you code + a precise description of the rendered result.

== Fig 2 (spatial_cv) — redesigned to paired markers + mean±SD error bar ==
New code (key):
  x = np.arange(len(df))                      # 5 folds
  offsets = {"accuracy": -0.08, "f1": 0.08}
  markers = {"accuracy": "o", "f1": "s"}
  for metric in ("accuracy","f1"):
      ax.plot(x + offsets[metric], df[metric], marker=markers[metric], linestyle="",
              color=colors[metric], label=metric.capitalize(), markersize=5)
  mx = float(len(df))
  for metric in ("accuracy","f1"):
      ax.errorbar(mx + offsets[metric], mean, yerr=sd, fmt="D", color=colors[metric],
                  capsize=4, markersize=5)
  ax.set_xticks(list(range(len(df))) + [mx])
  ax.set_xticklabels([f"Fold {i}" ...] + ["Mean ± SD"])
  ax.set_ylim(0.0, 1.05)
No outlier styling on Fold 4 (per your note). The axhspan bands are gone.

== Fig 3 (jaccard) — offset markers, distinct shapes/colors ==
New code (key):
  style = {"mean": ("o","#4C72B0"), "max": ("s","#C44E52"), "p90": ("^","#55A868")}
  offsets = {"mean": -0.06, "max": 0.0, "p90": 0.06}
  xv = coarse_res + offsets[agg]              # coarse_res in {8,9}
  axes[0].plot(xv, jaccard, marker, linestyle="", color, label=agg)
  axes[1].plot(xv, f1, marker, linestyle="", color, label=agg)
  axes[0].set_title("Jaccard similarity"); axes[1].set_title("F1")
  ax.set_xticks([8,9]); ax.set_xticklabels(["R8","R9"]); ax.set_ylim(0,1.05)
The "Fine = R10" per-panel title is removed (I plan to move "reference support R10" into the caption).

== Fig 4 (adaptive) — bars + single top-band annotation ==
New code (key):
  labels = ["Fixed R9", "Adaptive R9/R11", "Uniform R11"]
  values = [141, 3933, 6909]; ax.bar(...); ylim(0, 6909*1.22)
  value labels on top of each bar: 141 / 3,933 / 6,909
  ax.text(1.0, ymax*1.10,
      f"Adaptive = {adaptive/fixed:.1f}x fixed R9 = {adaptive/uniform*100:.1f}% of uniform R11",
      ha="center", va="bottom", fontsize=8.5)
(Note: I placed the two ratios on ONE top-band line because the inter-bar gaps are only ~0.2 units wide and a 19-char label would overlap the bars.)

== Fig 1 (workflow) — compressed to noun phrases ==
Stage 3 items -> "Gradient-boosting classifier\n+ continuous-risk regressor",
  "H3-block GroupKFold spatial CV", "Logistic, ponding & constant-class baselines".
Stage 4 items -> "PFI_h(c,r)", "Scale-loss Jaccard ladder\n(R10 → R9 / R8)",
  "Adaptive refinement\n(PFI_h screens → R11)", "Sandy coastal-overlap diagnostic".
Sandy box label -> "FEMA Sandy negative control\n(never a training label)";
  dashed arrow already enters only the last (Sandy) box in column 4.

Also added scripts/make_figures.py to regenerate all four figures from their locked CSVs in one command (previously Fig 2 and Fig 4 had no script entry point).

== QUESTIONS ==
Q1. Fig 4: is the single top-band line "Adaptive = 27.9x fixed R9 = 56.9% of uniform R11" acceptable, or would you still prefer two separate short labels? Any layout concern?
Q2. Fig 3: with the "Fine = R10" title removed, should the caption explicitly say "reference (fine) support is H3 R10"? Confirm the wording.
Q3. Fig 2: does the "Mean ± SD" error-bar x-position read clearly, or should the mean markers be visually separated further from the folds (e.g., a thin vertical divider line)?
Q4. Fig 1: with 4 items in stage 4 and 3 in stage 3, is there any residual text-overflow risk I should check, given boxes are drawn top-down with equal height split?
Q5. Any other remaining code-level or visual issue you can see?
