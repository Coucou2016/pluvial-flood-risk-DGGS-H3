FIG-D — round 4: caught and fixed a real SD-convention bug; confirm

You twice flagged "Fig 2 ddof consistency". I verified it and it was a real bug.

== The bug ==
fold accuracy = [0.7551, 0.7600, 0.7727, 0.7143, 0.9167]; mean = 0.7838.
- population SD (ddof=0) = 0.0693  -> matches manuscript "0.784 ± 0.069".
- sample SD (ddof=1)   = 0.0775  -> what the old figure code (df.std(), pandas default ddof=1) was plotting.

So the figure error bars were numerically inconsistent with the locked manuscript table. Fixed:
  sd = float(df[metric].std(ddof=0))   # accuracy 0.0693, F1 0.0437

== Also fixed ==
- Manuscript table now lists F1 mean ± SD = 0.866 ± 0.044 (was "F1 mean 0.866" only), so the figure's F1 error bar now has a matching tabulated value.
- Report.md updated to F1 0.865748 ± 0.043729 for full precision.
- Regenerated figures + rebuilt HTML; tests 2 passed.

== QUESTIONS ==
Q1. Confirm this ddof=0 (population SD) choice is defensible for "mean ± SD across k=5 folds" and internally consistent, or would you argue for ddof=1 (sample SD) instead — in which case I must also change the manuscript's 0.069 → 0.077? Which is more standard for a journal table?
Q2. Now that Fig 2 error bars match the table exactly, is there any remaining numerical consistency issue between the four figures and their tabulated values?
Q3. Of the production-only checks you listed (legibility at column width, PDF clipping, grayscale, Fig 4 annotation margin, Fig 1 font size), which one, if any, do you want me to verify explicitly next?
