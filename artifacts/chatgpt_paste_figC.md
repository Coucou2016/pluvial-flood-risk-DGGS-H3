FIG-C — round 3: applied FIG-B polish + synced captions; verify consistency

I applied all FIG-B items. Changes since FIG-B:

== Code changes (figures.py) ==
1. Fig 2: summary position now mx = len(df) + 0.5 (extra half-step gap before "Mean ± SD").
2. Fig 3: replaced per-panel legends with ONE figure-level shared legend (fig.legend, ncol=3, below panels); added symmetric x-limits coarse[0]-0.6 .. coarse[-1]+0.6; kept ylim(0,1.05).
3. Fig 4: top annotation now TWO centered lines:
     Adaptive = 27.9× fixed R9
     = 56.9% of uniform R11
   (uses × not x; y anchored at data max 6909, not padded ylim).
4. Fig 1: "PFI_h screens → R11" → "PFI_h-guided → R11"; Sandy box text now "FEMA Sandy negative control (never a training label)".

Also: scripts/make_figures.py regenerates all four (reads locked CSVs, emits PNG+PDF). Tests: 2 passed.

== Caption sync (manuscript.md, report.md, build HTML) ==
Fig 2 (new): "...paired markers for each of five held-out folds ...; a final x-position shows the fold mean ± SD with error bars."
Fig 3 (new): "...compare hotspot sets defined on the reference fine support, H3 R10 (top decile, quantile 0.9), with R9 and R8 representations under mean, maximum, and p90 aggregation."
Fig 4 (new): "...Fixed R9 (141), adaptive mixed R9/R11 (3,933), and uniform R11 (6,909) ... (adaptive = 27.9× fixed R9 = 56.9% of uniform R11; 79 of 141 R9 cells refined)."
Fig 1: "Sandy negative-control check" → "Sandy coastal-overlap diagnostic"; "...enters only the Sandy diagnostic; it is never a training label."

== QUESTIONS ==
Q1. Do the four captions now match the redesigned figures exactly (no stale wording like "bars"/"reference bands"/"linestyle")? Flag any remaining mismatch.
Q2. Fig 3 shared legend: is a single horizontal legend below both panels (ncol=3) the right choice, or would you prefer it inside one panel? Any risk it overlaps the x-axis label "Coarse H3 resolution"?
Q3. Fig 2: with the summary at x=5.5 and a "Mean ± SD" tick label, is there any remaining ambiguity, or is it now clear the summary is not a sixth fold?
Q4. Any final correctness/legibility issue before I consider the figure set publication-ready?
