# ChatGPT round R17 — data authenticity final audit + submission readiness (text only)

**Public repo:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 (master; commits b8adee0 → 8805260 R15 tone → 9898082 R16 figures)
**R15 outcome:** drafting metadata removed, contribution paragraph + Related Work rewritten as flowing prose, "hook/stub/binding/ida_like" developer vocabulary removed. No number changed.
**R16 outcome:** figure titles/audit-footers removed, mean±SD bands + direct labels added; PDF vector output. Science unchanged.

## Data authenticity audit (already written as `docs/paper/audit.md`)

The audit document proves every number is produced by the repo's own code on local open data (not copied from Svellingen et al. 2026 or any reference). Structure:

1. **Authenticity** — data acquisition chain (config → download script → `DOWNLOAD_MANIFEST.json` → `DATA_SOURCES.md`); label sources are NYC DEP stormwater, NYC 311, USGS Ida HWM (DOI 10.5066/P9OMBJPQ), FEMA Sandy (negative control only); rainfall is an explicitly-labelled synthetic constant.
2. **Accuracy** — per-number reconciliation tables: expanded n=956 (prevalence 0.479, acc 0.642±0.148, F1 0.608, R² 0.525±0.112, ROC-AUC 0.703, AP 0.723) and Lower Manhattan n=141 (0.784/0.866/0.030/0.683/0.861); fold-by-fold tables; the R11 always-positive-vs-majority fix is documented.
3. **Completeness** — code/test coverage table; full suite **58 passed, 1 skipped**; honest "not done" list (observed rainfall, citywide, FloodNet) marked 待补充, with no fabricated numbers.
4. Reproducibility steps (commands) for a reviewer.

## What I need from you (submission readiness)

I am preparing this for an IJDRR-style submission. The manuscript currently has: Title, Abstract, Keywords, §1 Introduction, §2 Related work, §3 Study area and data, §4 Methods, §5 Experimental design, §6 Results, §7 Discussion, §8 Conclusions, Figure captions, Data and code availability, References (17 items, currently in Nature-style author-year with DOIs).

Answer with concrete, ordered edits (do NOT invent or change any number/result):

1. **Submission components missing for IJDRR/Elsevier.** Which required/expected front-matter items are absent (e.g., Highlights, CRediT author contributions, Declaration of competing interest, Funding, Acknowledgements, structured vs unstructured abstract, word limits)? Give the exact list I should add, in IJDRR order.
2. **Reference style.** The current references use Nature-style ("Author, A. & Author, B. … *Journal* **vol**, page (year). DOI"). What is the correct Elsevier/IJDRR numbered style, and should I convert now or at typesetting? Give the exact target format with one worked example from my reference list (e.g., the Svellingen 2026 IJDRR item).
3. **Abstract length.** My abstract is one long paragraph (~330 words). Does IJDRR require a shorter/structured abstract? Give the target length and whether I should split it.
4. **Audit-document sufficiency.** Is the authenticity/accuracy/completeness evidence chain (above) sufficient for a reviewer/data-availability check, or is a specific category missing? Flag any concrete gap.
5. **Next 5 highest-value submission-readiness edits**, each with exact location + reason.

Rules: text only; do not invent or change any number, result, or scientific claim; if a journal requirement (exact word limit, exact reference format) is not something you can state with confidence, say so rather than guessing.
