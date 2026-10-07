# ChatGPT delivery — Pluvial Flood Audit Plan

- **Conversation:** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2
- **Captured:** 2026-08-15 (Cursor lead browser session)
- **Note:** ZIP auto-upload was blocked (OS file picker). Brief was pasted as text. ChatGPT2LocalBridge reconnect prompt was dismissed with "Not now".
- **Cursor lead correction:** In this repository, `PFI_h(c, r)` means hex-level pluvial flood index / flood probability conditioned on rainfall intensity `r` (mm/h), **not** permutation/SHAP feature importance. Treat ChatGPT section 3.5 accordingly.

---

1) Executive summary

The paper’s defensible contribution is adaptive H3 spatial modeling for pluvial flood risk with spatially blocked evaluation, not reproduction of a prior Jaccard score.

Current positioning should remain: H3+ML framework, open flood labels (DEP/311/Ida), spatial H3-block CV, adaptive H3, PFI_h(c,r).

The main scientific risk is confusing a functioning software fixture/smoke pipeline with evidence of generalizable flood skill.

Lower Manhattan smoke tests can validate pipeline integrity but cannot support citywide claims.

Synthetic rainfall and FloodNet stubs currently weaken external validity unless clearly isolated as engineering placeholders.

The experiment package needs stronger negative controls, spatial CV reporting, and benchmark ladders before paper submission.

The manuscript gap is critical: methods, assumptions, limitations, and claim boundaries must be formalized before additional engineering.

No PFIb, no claimed Jaccard 0.14 reproduction, and no citywide performance claims without full geographic validation.

2) Problem audit table

| Severity | Issue | Evidence path / symbol to verify | Claim risk |
|----------|-------|----------------------------------|------------|
| P0 | FloodNet implementation is a stub rather than a validated data source | FloodNet module/config/import path | High. Placeholder cannot support multi-source validation claims. |
| P0 | Synthetic event_rainfall used in experiments | rainfall/event generation path | High. Synthetic forcing ≠ predictive flood skill. |
| P0 | Lower Manhattan smoke ≠ citywide evaluation | nyc_smoke fixture/test metadata | High. Local demo misread as NYC-scale validation. |
| P0 | Spatial CV sample size around n≈141 needs justification | H3-block CV splitter/results | High. Unstable estimates / weak confidence. |
| P0 | Manuscript absent | paper/manuscript root | High. Claims can drift without manuscript alignment. |
| P1 | Jaccard ladder too thin | metric reporting/evaluation scripts | Medium-high. |
| P1 | Sandy negative-control interpretation unclear | Sandy experiment/config/results | Medium-high. |
| P1 | Demo vs nyc_smoke metadata confusion | smoke metadata/config naming | Medium. |
| P1 | Adaptive H3 contribution not isolated | adaptive resolution selection logic | Medium-high. Need ablation vs fixed H3. |
| P1 | PFI_h(c,r) interpretation needs formalization | PFI implementation/training evaluation | Medium. (**Correct: rainfall-conditioned index, not feature importance.**) |
| P2 | Oslo appendix role unclear | appendix experiment config | Low-medium. |
| P2 | Fixture≠science boundary needs documentation | tests/readme/docs | Medium. |
| P2 | Rainfall source honesty fixed | rainfall metadata | Reduced risk. |
| P2 | P7 nyc_smoke trained-PFI_h fix completed | P7 pipeline | Reduced risk. |

3) Paper work plan — see conversation for Methods 3.1–3.5, experiment checklist, claim matrix.

4) Prioritized fixes — P0.1–P0.5, P1.1–P1.4, P2 as in conversation.

5) Patches — none (ChatGPT correctly declined without ZIP contents).

6) Residual risks — live GB/data questions listed in conversation.
