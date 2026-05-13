# DECISION REQUIRED — a1-m15-24 module shape contract: dialogue format, citation discipline, source-blockquote exemption

**Status:** PROPOSED — multi-agent converged via `ab discuss a1-m15-24-shape-contract` (thread `767f107789e2`, codex+gemini, 2 rounds — round-2 [AGREE] from Gemini on Codex's refinements).
**Surfaced:** 2026-05-13, m20 build #3 python_qg revealed 4 gate failures (#1962). Gate 1 dispatched separately (PR #1963 codex/vesum-gate-scope-2026-05-13). Gates 2-4 (citations_resolve, l2_exposure_floor, long_uk_ceiling) **interact** and need joint design.
**Source:** Empirical evidence from `.worktrees/builds/a1-my-morning-20260513-164953/curriculum/l2-uk-en/a1/my-morning/python_qg.json` + the multi-agent discussion. Discussion transcript: `ab channel tail a1-m15-24-shape-contract --thread 767f107789e241919a36f573be37d4ca`.
**Scope:** Writer prompt template `scripts/build/phases/linear-write.md`, gate counter logic in `scripts/build/linear_pipeline.py` (`_count_uk_dialogue_lines` + `_unsupported_run_segments`), and the existing citation matcher `scripts/build/citation_matcher.py`. **Does NOT touch:** Phase B band thresholds (kept at `uk_dialogue_lines=14`), gate framework, MDX assembler.

---

## TL;DR (the converged contract)

The 3 remaining gate failures aren't 3 independent calibration problems. They're an **aligned writer-output-format / gate-counter / citation-discipline** package. Specifically:

- **Axis 1 (citations_resolve):** Bounded fuzzy match — same author + grade + small page drift. Tighten via writer prompt: NO new sources outside `plan_references` unless the citation is grounded by Knowledge Packet content the writer was given.
- **Axis 2 (l2_exposure_floor):** Keep `uk_dialogue_lines=14` (matches deployed A1 P10 per Phase B calibration `audit/immersion-gate-calibration-2026-05-13/REPORT.html:53-55`). The current m20 module HAS 14 dialogue turns — they're in em-dash form (`— Привіт, Насте!`) that `_count_uk_dialogue_lines` doesn't count. Fix the **gate-writer format mismatch**: writer prompt mandates `<DialogueBox>` component OR `> `-blockquote form for dialogues, gate already counts both.
- **Axis 2b (long_uk_ceiling-related):** Writer prompt requires **inline gloss within 8 words** for each dialogue line (instead of block-bottom gloss). Block-bottom gloss is documented as anti-pattern.
- **Axis 3 (long_uk_ceiling exemption):** Exempt **citation-grounded source blockquotes only** — those identifiable by textbook_grounding citation evidence (`python_qg.json:104 matched`). Keep learner-facing practice `> `-blockquotes (like the 4-sentence morning template) under the 28-word/8-word rule. Blanket `> ` exemption would hide real A1 wall-of-UK.

The structural insight: writer-output format and gate-counter must agree. Today they disagree on dialogue convention. Fix at writer prompt (mandate the gate-readable format) rather than loosening either side.

---

## What's being proposed (per axis, with implementation surface)

### Axis 1 — Citation discipline

**Convention:** Writer cites in natural Ukrainian publishing style (`Кравцова Н. М. та ін. Українська мова, 4 клас, с. 112`) — this is what `sources.db` metadata yields per the existing search_text result format. The matcher already normalizes compact vs expanded forms by parsed author/grade/page key (`scripts/build/citation_matcher.py:80`, `scripts/build/linear_pipeline.py:4645`).

**Tighten via writer prompt:** sources MUST be either (a) listed in `plan_references`, OR (b) cited from content the writer's MCP tool calls actually retrieved and quoted (Knowledge Packet hit). Forbid adding new textbook references that lack BOTH plan_reference AND search_text-grounded provenance.

**Tighten via matcher:** restrict fuzzy match to small page drift (±5 pages? ±1 page-range? — finalize during dispatch design). Same author + same grade required.

**Concrete failure to clear:** `Аврамченко О. М. Українська мова, 6 клас, с. 10` (m20 build #3) — writer added a 6th-grade reference not in plan. Must fail until plan_references is updated OR writer drops it.

### Axis 2 — Dialogue format + gloss strategy

**Convention:** All Ukrainian dialogue lines emitted as either:
- `<DialogueBox>` component (preferred for V7's React rendering), OR
- `> `-prefixed blockquote line (Markdown fallback)

**Anti-pattern explicitly forbidden:** em-dash dialogue convention (`— Привіт, Насте!`) under a `## Діалоги` heading WITHOUT `<DialogueBox>` or `> ` wrapping. The gate doesn't count these and will miscount L2 exposure.

**Gloss rule:** Each Ukrainian dialogue line MUST have inline English gloss within 8 tokens of proximity. Two valid shapes:
- Right after the UK line (italic): `— Привіт, Насте! *(Hi, Nastia!)*`
- Inside the same DialogueBox prop: `<DialogueBox uk="..." en="...">`

**Anti-pattern:** Block-bottom gloss block (all UK lines, then a "translation:" section at the end). Causes `long_uk_ceiling` to flag the entire dialogue as one offending UK run.

**Floor:** `uk_dialogue_lines=14` STAYS at calibrated value. Deployed A1 P10=14, P90=19, max=22 per Phase B report. m20's 14 em-dash lines DO meet the floor — the gate just doesn't count them.

### Axis 3 — Source-blockquote exemption from long_uk_ceiling

**Source blockquote** = a `> `-prefixed UK block that quotes a textbook the writer's `search_text` retrieved and that maps to a `plan_references` (or knowledge-packet-grounded) citation. Identifiable via the existing `textbook_grounding` evidence in `python_qg.json:97-119 matched/missing/blockquotes_checked`.

**Exempt these from `long_uk_ceiling`:** they're source material, not learner-target prose. Long UK runs in source citations are expected (verbatim textbook excerpts ≥30 words is a separate writer-prompt mandate at `scripts/build/phases/linear-write.md:83`).

**Keep these UNDER the ceiling:** learner-facing practice blockquotes (4-sentence morning template, self-check prompts, sample sentences) that aren't textbook-citation-bearing. Use the same 28-word + 8-token gloss rule.

**Implementation:** in `_unsupported_run_segments` (`scripts/build/linear_pipeline.py:5398`), receive the textbook_grounding evidence as input, skip blocks whose content overlaps with a citation-grounded blockquote span.

---

## Implementation plan (one PR per axis, OR one bundled PR)

| Axis | File(s) | Approx LOC | Tests |
|---|---|---|---|
| 1 | `scripts/build/phases/linear-write.md` (writer-prompt directive), `scripts/build/citation_matcher.py` (page-drift tolerance, opt) | ~15 prompt + ~5-10 matcher | 2 fixtures: in-plan citation with page drift passes, out-of-plan citation fails |
| 2 | `scripts/build/phases/linear-write.md` (DialogueBox / `> ` mandate + inline-gloss directive) | ~25 prompt | 2 fixtures: em-dash-only dialogue fails gate count, DialogueBox-wrapped dialogue passes count |
| 3 | `scripts/build/linear_pipeline.py` (`_unsupported_run_segments` gets textbook_grounding evidence input) | ~30 code | 2 fixtures: citation-grounded source blockquote exempt, learner practice blockquote still under ceiling |

Recommended: **one bundled PR** covering all 3 axes — they cohere as "a1-m15-24 module shape contract" and shipping piecemeal risks one axis landing without the others' enabling logic. Codex dispatch territory; mechanical fixture work.

---

## Validation path

1. **Dispatch the implementation** (this PR) → land.
2. **Re-run m20 build #4** (will be #5 by count) → verify all 4 #1962 gates GREEN:
   - vesum_verified (already shipped via #1963)
   - citations_resolve (Аврамченко out-of-plan rejected if not in packet; Кравцова/Захарійчук small-page-drift accepted)
   - l2_exposure_floor (m20 writer re-emits dialogues in `<DialogueBox>` form → 14 lines counted)
   - long_uk_ceiling (source blockquotes exempt; dialogue lines have inline gloss)
3. **If all 4 gates GREEN on m20**, the build advances to review phase + MDX assembly + final module_done event. First true student-aware A1 module per `2026-05-13-ulp-derived-student-aware-immersion.md` § Phase 5.
4. **Then Phase 2b (m01-m07 warm-up batch)** unblocks per existing brief at `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`. Candidate `/goal` invocation target per `goal-driven-runs.md` predicate-bounded batch shape.

---

## Open questions for user signoff

1. **Bundled PR vs 3 PRs?** Recommendation: bundled (axes cohere, shipping piecemeal risks partial deployment). Override to 3 PRs only if there's a specific gating reason (e.g. you want to ship axis 2 alone first to verify dialogue count alignment).
2. **Page-drift tolerance for citation matcher?** Default proposal: same author + same grade + page distance ≤5 pages. Stricter (≤1)? Looser (same grade only, page ignored)? My instinct: ±5 is right — Кравцова Grade 4 p.112 vs plan p.113 is the same lesson; p.50 vs p.200 is clearly a different lesson.
3. **Knowledge-Packet-grounded vs strict plan_references?** Default proposal: writer MAY cite sources the Knowledge Packet's search_text retrieved, even if not in `plan_references`, AS LONG AS the citation is verifiable in `writer_tool_calls.json`. Override to strict-plan-only if you prefer the writer-can't-add-sources discipline.

If you have no override on questions 1-3, I'll dispatch the bundled implementation with default answers.

---

## Discussion artifacts

- `ab channel tail a1-m15-24-shape-contract --thread 767f107789e241919a36f573be37d4ca`
- Codex r1+r2 (both rounds same position): "Bounded B for citations; keep dialogue floor at 14, fix gate-counter alignment; exempt source-only blockquotes."
- Gemini r1 (initial position) → r2 [AGREE] with Codex's refinements.
- Round-2 convergence shape: harness flagged `still disagreeing: codex` because Codex's `[DISAGREE]` flag remained, but content-wise Gemini moved to Codex's position. Effective consensus: Codex's framing.

---

## Predecessors / related

- **Replaces aspect of:** `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (the structural gate accepted earlier today). That card defines 4 sub-gates; this card refines what they enforce at the writer-output-format level.
- **Built on Card 1 (#1953):** writer-isolation Tier 1 boundary holds — we can now see this format/counter alignment cleanly without Bash/Read context-leak noise.
- **Builds path to Phase 2b:** `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md` queued post-m20 GREEN.

---

*Format spec: `docs/decisions/pending/README.md`. If accepted, move to `docs/decisions/2026-05-13-a1-m15-24-shape-contract.md` and flip status to ACCEPTED with implementation PR cross-references.*
