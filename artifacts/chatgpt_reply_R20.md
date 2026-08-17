# ChatGPT R20 reply — final framing + Results prose + figure captions (2026-08-18)

**Paste package:** `artifacts/chatgpt_paste_R20.md`.

## Verdict per item

1. **Abstract underclaim — REVISE.** Replace "This study presents an open-label machine-learning framework for hexagonal pluvial flood screening on the H3 discrete global grid." with "This study presents an open-label machine-learning framework in which H3 provides the common spatial support for learning and spatially blocked evaluation."
2. **§6.1 moderate joint-application — REVISE.** → "Pooled out-of-fold ROC-AUC is 0.683, indicating modest ranking discrimination. Pooled average precision is 0.861, only slightly above the 0.801 positive-class prevalence baseline."
3. **§6.6 moderate joint-application — REVISE.** → "Pooled out-of-fold ROC-AUC is 0.703, indicating moderate ranking discrimination. Pooled average precision is 0.723, clearly above the 0.479 positive-class prevalence baseline."
4. **§6.6 "positive blocked signal" — REVISE.** → "Continuous-risk R² (0.525 ± 0.112) indicates positive predictive performance under blocked evaluation at this scale."
5. **Figure 2 caption — REVISE MINOR.** Add mean±SD band mention: "…(n = 141 cells); horizontal reference bands show the corresponding fold mean ± SD."
6. **Figure 3 caption — ACCEPT** (no change).
7. **Figure 4 caption — REVISE MINOR.** "parents refined" → "R9 cells refined"; "adaptive/uniform" → "adaptive-to-uniform cell-count ratio".
8. **§7.3 Future work — REVISE.** Replace item (ii) (specifying a desired numerical outcome) with a scientific test; "non-synthetic provenance" → "documented provenance"; broaden (iii); (iv) "held-out FloodNet validation … suitable sensor layer".
