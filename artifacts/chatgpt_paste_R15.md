# ChatGPT round R15 — academic tone + remove AI-draft traces (text only)

**Public repo:** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3 (master current; commit b8adee0)
**R14 outcome:** Results tables/captions cleaned, in-text figure references added, PDF vector output enabled. Science and numbers unchanged.

## The problem (author's own assessment, not mine)

The manuscript still reads like a "research summary / review / AI-assisted draft" rather than a polished IJDRR-style paper. The author wants significant refinement in: (a) academic tone, (b) logical flow, (c) removal of AI-generated traces, and asks that the revision match the register of the cited reference papers (Svellingen et al. 2026 IJDRR; Li et al. 2022; Bersabe & Jun 2025), and follow standard academic-writing guidance. Do NOT change any number, result, table value, or scientific claim. Only prose, structure, and register.

## Verbatim passages flagged as AI-draft / summary-like (rewrite these)

### A. Meta/draft markers that must disappear from a submission manuscript
- Header line: "Working manuscript (methods orientation, IJDRR-shaped)."
- Final reference line: "Additional venue-specific references to be added."

### B. Introduction, contribution paragraph (enumerated "three parts" + formulaic question)
> "This study addresses the following question: can an open, multi-source label stack on H3 support spatially blocked evaluation, diagnose scale loss, and drive adaptive refinement with an explicit rainfall-conditioned cell index, without claiming reproduction of any proprietary product? Unlike Svellingen et al. (2026), who aggregate a pre-existing building-level, insurance-derived index into H3 cells for scalable communication, this study learns directly from open flood observations on the H3 support, evaluates transfer across held-out H3 spatial blocks, and adapts the grid itself rather than merely re-aggregating a fixed index. The contribution is a methods protocol rather than a citywide operational map, and consists of three parts. First, an open-label H3 feature and label assembly procedure with explicit provenance for assembly mode, feature source, label source, and rainfall source. Second, primary evaluation through spatial H3-block cross-validation, with random splits relegated to diagnostics and class-prevalence baselines disclosed alongside accuracy and F1. Third, a scale-loss Jaccard/F1 ladder and an adaptive H3 refinement stage screened by trained cell scores, together with a binding definition of `PFI_h(c,r)` that is neither feature importance nor PFIb."

### C. Related Work — bold inline topic-tags, including two tags jammed into ONE paragraph
> "**From building indices to hexagonal screening.** Svellingen et al. (2026, IJDRR) aggregate a machine-learning building-level pluvial susceptibility index (PFIb) into H3 cells ..."
> "**Hexagonal DGGS as an analysis substrate.** Independently of insurance labels, Li et al. (2022) ..."
> "**Spatial holdouts in GeoAI.** Random train/test splits routinely inflate skill ..."
> "**Open urban flood observations and their biases.** New York City 311 flooding complaints have previously supported ... **Urban pluvial machine-learning susceptibility.** City-scale studies map susceptibility from ..."

The last paragraph runs two different bold topic-tags together — a clear AI-outline artifact. Should Related Work use real `###` subheadings, or smooth flowing paragraphs without bold lead-ins?

### D. Informal / jargon phrases scattered through the manuscript
1. "Event rainfall is a synthetic constant **Ida-like hook** rather than radar or gauge data." (also appears as "synthetic constant hook" in §6.4 and §7.2)
2. "FloodNet sensor data are available only as a **stub** and are not used."
3. "the mean `PFI_h` ... **cannot yet respond to** rainfall" (§4.7)
4. "the proximity is **coincidental**" and "is **not narrated as** matching" (§7.1)
5. "maximum and p90 aggregations retain extrema by construction and therefore should **not be read as 'no scale loss'**" (§6.2)
6. Scenario loop: "across {moderate 25, heavy 40, **ida_like 75**, extreme 100 mm/h}" — snake_case leaking into prose.
7. "**hook**" is used repeatedly; "stub" and "hook" are developer vocabulary.

## Focused questions

1. For §2 Related Work: subheadings vs. flowing paragraphs — which is closer to the cited IJDRR/ISPRS register? Give the cleanest concrete restructure (keep every citation and every factual claim).
2. Rewrite the §1 contribution paragraph (B) to remove the "question: can ... ?" + "First/Second/Third" enumeration, while preserving all three contribution components and the explicit contrast to Svellingen et al. 2026.
3. List every word/phrase in (D) that should be replaced, with the exact replacement, keeping scientific meaning identical.
4. Are there other AI-trace tell-tales you would expect in a text of this kind (e.g., em-dash overuse, "the present study" repetition, "it is worth noting", "plays a crucial role", "Furthermore/Moreover" chains)? Point to concrete sentences to fix.
5. Give the next 5 highest-value tone/register edits, each with exact location + reason + suggested phrasing.

Rules: text only; do not invent or change any number, result, or scientific claim; if you need a value that is not stated, say so rather than guessing.
