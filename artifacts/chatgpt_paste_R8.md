# ChatGPT paste — Round 8 (Results honesty pass)

**Paste into:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Enable:** Web search ON  
**Rules:** TEXT only. Fetch/read URLs. Reject any fabricated numbers.  
**Public repo:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3

---

Please fetch/read:

1. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/artifacts/chatgpt_paste_R8.md  
2. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/docs/paper/manuscript.md  
3. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/models/nyc_smoke/run_metadata.json  
4. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/outputs/jaccard_by_resolution.csv  
5. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/outputs/adaptive_vs_fixed_ablation.csv  
6. https://raw.githubusercontent.com/Coucou2016/pluvial-flood-risk-DGGS-H3/master/outputs/negative_control.json  

## Locked live numbers (must match; do not invent)
- n=141; spatial CV Acc **0.783756 ± 0.069280**; F1 **0.865748**
- Per-fold Acc/F1: 0.755/0.850; 0.760/0.850; 0.773/0.872; 0.714/0.813; 0.917/0.944
- Jaccard mean R10→R8 = **0.1667** (not “equal to” Svellingen 0.14)
- adaptive/uniform cell_count_ratio ≈ **0.569**; parents refined 79/141
- PFI_h scenario means all **0.802888**; within-cell range **0**
- coastal_only frac ≈0.057; pluvial−coastal mean score ≈0.120

## Ask (R8)
1. Line-edit Results §6 for soft overclaims (efficiency→runtime, Fold4→citywide, Jaccard→reproduction, PFI→importance, flat scenarios→discrimination).
2. Propose safer verb choices (`indicate` / `consistent with` / `do not demonstrate`).
3. Flag any number in the manuscript that does not match the live tables above.
4. Keep Abstract aligned with Results honesty.

Return a numbered cut/reword list only.
