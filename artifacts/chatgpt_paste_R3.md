# ChatGPT paste — Round 3 (Results honesty)

**Paste into:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2  
**Or new chat:** `R3 results honesty`  
**Public GitHub:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**Sources (live only):** `models/nyc_smoke/run_metadata.json`, `spatial_cv_folds.csv`, `outputs/jaccard_by_resolution.csv`, `outputs/adaptive_vs_fixed_ablation.csv`, `outputs/pfi_h_scenarios.csv`, `outputs/negative_control.json`

---

All numbers below are **copied from live artifacts** (Lower Manhattan open-data smoke). Tell us what we **can** and **cannot** claim. Do not invent numbers.

## Table A — Spatial H3-block CV (primary)
| Metric | Value |
|--------|-------|
| n_cells | 141 |
| spatial_cv_n_folds | 5 |
| spatial_cv_n_blocks | 7 |
| spatial_cv_accuracy_mean ± std | 0.783756 ± 0.069280 |
| spatial_cv_f1_mean | 0.865748 |
| spatial_cv_r2_mean ± std | 0.030333 ± 0.342841 |
| spatial_cv_mae_mean | 0.332182 |
| random_split_val_accuracy (diagnostic) | 0.689655 |

Per-fold accuracy/F1: 0.755/0.850; 0.760/0.850; 0.773/0.872; 0.714/0.813; 0.917/0.944

## Table B — Jaccard ladder (fine_res=10, hotspot_q=0.9)
| coarse | agg | jaccard | f1 |
|--------|-----|---------|-----|
| 8 | mean | 0.1667 | 0.2857 |
| 8 | max | 1.000 | 1.000 |
| 8 | p90 | 1.000 | 1.000 |
| 9 | mean | 0.9767 | 0.9882 |
| 9 | max | 1.000 | 1.000 |
| 9 | p90 | 0.9767 | 0.9882 |

## Table C — Adaptive ablation
| Field | Value |
|-------|-------|
| score_col | PFI_h |
| n_fixed_coarse (R9) | 141 |
| n_adaptive_mixed | 3933 |
| n_uniform_fine (R11) | 6909 |
| adaptive_cell_count_ratio | 0.569257 |
| adaptive_n_parents_refined | 79 |

## Table D — Rainfall scenarios
141 cells × {moderate 25, heavy 40, ida_like 75, extreme 100 mm/h}; mean PFI_h ≈ **0.802888** for every scenario; **within-cell PFI_h range across scenarios = 0**.

## Table E — Sandy negative control
n_cells=141; n_coastal=31; n_pluvial=71; n_both=23; n_coastal_only=8; frac_coastal_only≈0.0567; pluvial_minus_coastal_mean_score≈0.1198. Coastal = **not** a training label.

## Ask
1. Claim matrix: ALLOWED / FORBIDDEN / 待补充 for each table.
2. How to write Results prose so Fold4 0.917 does not become “excellent citywide skill”.
3. How to discuss Jaccard 0.1667 vs Svellingen 0.14 without equality.
4. Exact wording for flat PFI_h scenarios.
5. Which Results sentences should move to Discussion/limitations.

Return: claim matrix + 6–10 safe Results bullets we may paste into the manuscript.
