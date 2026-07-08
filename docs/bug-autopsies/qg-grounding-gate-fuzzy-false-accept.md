# QG grounding gate v2 — fuzzy provenance false-accepted near-copy fabrications

**Date:** 2026-07-08→09 · **Issue:** #4797 (epic #4707) · **PR:** #4798 (merged `077a3a5f1c`)
**Category:** gate-false-accept / green-gate-broken-artifact

## What broke
The v2 grounding gate is a **fail-closed anti-fabrication** check: it must reject a reviewer's
`evidence_excerpt` that is not genuinely present in a captured tool output. The first shipped
implementation **false-accepted near-copy fabrications** — a model copies a real retrieval and swaps one
fact — at the DEFAULT threshold, e.g. real output «Сковорода народився у **1722** році», fabricated excerpt
«…у **1900** році» → `anchored=True, sim=0.95`. It passed green CI, 153 passing tests, and the author's own
skeptical read. It took **5 cross-family review rounds** (codex reviewing agy's builds) + 2 fleet design
panels to harden.

## Why (root causes, one per round)
1. **Fuzzy char-similarity + `any()` content guard.** Acceptance was `SequenceMatcher(excerpt, window).ratio()
   ≥ τ` plus `any(content_token in matched_span)`. A near-copy is ~95% similar (only the year differs), and
   the shared proper noun satisfied `any(...)` while the swapped digit «1900» (absent — real span has «1722»)
   was never required. Fuzzy string similarity **cannot** distinguish a faithful quote from a near-copy with a
   swapped fact.
2. **A test masked the shipped behavior.** The fabrication test pinned `τ=0.9`; the gate's DEFAULT is
   `τ=0.75`, at which the same case false-accepts. Green tests gave false confidence. → A fail-closed gate's
   fabrication tests MUST run at the default threshold.
3. **Edit-distance can't separate UK inflection from name-swap.** The round-1 fix used Levenshtein ≤2 for
   proper nouns. VESUM-verified: `dist(Мирко,Марко)=1 < dist(Львова,Львів)=2` — the different-person pair is
   CLOSER than the same-entity inflection pair, so no distance threshold works. Львова↔Львів (і→о) and
   Києва↔Київ (і→е) are real declensions; only lemma identity separates them, and `data/vesum.db` is
   gitignored + sparse-excluded (absent in CI).
4. **A perf bound introduced a new false-accept.** `_find_best_window` was O(n²) on repetitive input (6.28s).
   The fix capped candidate windows at 64 — but **truncation dropped the rejecting window**, letting an
   earlier lower-scoring window anchor a fabrication (`Марко народився 1900` anchored to a repeated
   `Марко помер 1900` span). The bound's degenerate case did not fail closed. The author reasoned — wrongly —
   that truncation "only causes false-rejects"; codex proved false-accepts and it was reproduced.

## The fix (converged over 2 fleet panels + prototyped before briefing)
Layer A = **positional provenance**, dependency-free: `SequenceMatcher(E_norm, best_window).get_opcodes()` —
**every salient token (digit run OR capitalized proper-noun) must fall entirely within an `'equal'` opcode
block.** Fabricated digits/names land in `replace` blocks → reject; verbatim quotes + formatting variance
(whitespace/case/diacritics/ellipsis) → accept. Edit-distance dropped. Tool/query = τ−0.05 relaxation, not an
additive bonus. Perf bounded via **distinctive-anchor pre-scan**; **candidate truncation fails closed** (never
anchors). Semantic correctness (verb/claim, entity attribution) is explicitly Layer B's job — and Layer B
MUST entail against the RAW tool output, never the excerpt. VESUM lemma tightening is an OPTIONAL follow-up,
never part of the fail-closed guarantee.

## Prevention (the transferable lessons)
1. **A fail-closed gate's adversarial tests must run at the DEFAULT threshold.** A stricter override in a
   test that hides the shipped behavior is worse than no test — it manufactures false confidence.
2. **Fuzzy string similarity cannot ground factual tokens.** Require positional/structural alignment
   (opcode `'equal'` blocks) of the distinctive tokens (dates, numbers, names), not mere presence-in-window.
3. **When adding a performance bound / cap / heuristic to a correctness gate, its degenerate case must fail
   closed BY DEFAULT — specify and test it.** Do not reason post-hoc about whether a bound is "safe"; make it
   safe by construction (truncation → reject, not accept).
4. **Independent cross-family review is load-bearing, not ceremony.** Solo review + 153 passing tests + fully
   green CI ALL missed the core false-accept. codex (gpt, cross-family from agy's gemini) caught every defect
   across 5 rounds. For a load-bearing gate, merge only after adversarial cross-family review, not on green CI.
5. **VESUM-verify morphology before choosing a string-matching primitive.** The Мирко/Марко vs Львова/Львів
   evidence (tool-backed) is what killed the edit-distance approach and forced the positional design.

## Guardrails now in place
- `scripts/audit/grounding_gate_v2.py` (behind `QG_GROUNDING_GATE_VERSION` flag; v1 default until tuned cutover).
- Six fail-closed regression tests at default τ in `tests/test_grounding_gate_v2.py` (number-swap, name-swap,
  short-name collision, digit-elsewhere, truncation-false-accept; plus verbatim + formatting-variance accept).
- `scripts/audit/grounding_shadow_compare.py` dual-runs v1↔v2 over stored artifacts for the tuned-cutover decision.
