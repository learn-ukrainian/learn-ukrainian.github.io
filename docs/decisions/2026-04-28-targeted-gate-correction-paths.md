# ADR-008: Targeted gate-specific correction paths

**Status**: PROPOSED 2026-04-28 (pending implementation; see EPIC linkage below).
**Date**: 2026-04-28
**Deciders**: Engineering (Krisztian K.) + cross-agent review (Gemini-3.1-pro-preview, Codex-gpt-5.5; broker task `adr-008-review`).
**Related**: ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`), EPIC #1577 (curriculum reboot), #1620 (round-3.5 verification surfaced the no-correction-path tension), #1622 (round-4 bakeoff).
**Refines**: ADR-007 (does not supersede; preserves all of ADR-007's kills).

---

## Context

ADR-007 (2026-04-23) killed V6's rewrite ladder — `section_rewrite`, `full_rewrite`, `writer_swap`, auto-heal for word-budget shortfall. Empirical justification: a1/colors regressed via `full_rewrite` after `<fixes>` had already corrected the flag-color hallucination. Gemini measured 9.6 → 9.2 → 8.4 across rewrite rounds. Rewrites *destroyed converged work*.

ADR-007's enforcement in `scripts/build/linear_pipeline.py` is currently strict-fail-fast: when Python QG flags a content gate (e.g. `word_count` short, `vesum_verified` failed, `russianisms_clean` hit), the build terminals. No reviewer is called. No `<fixes>` are emitted. No second writer pass.

This is too brittle for the 1700-module Phase-5 fan-out target. **Round-3.5 verification (#1620, PR #1621) terminated on `word_count` failure (1020/1200) before LLM QG ever ran.** At fan-out scale, marginal Python QG failures will dominate the failure mode and require human triage. The user has stated explicitly (2026-04-28): *"human triage is not feasible we have to be able to fix detected errors and mistakes."*

The question this ADR answers: **how does the pipeline autonomously fix detected errors without re-introducing ADR-007's failure pattern?**

The answer rests on a distinction ADR-007 did not draw explicitly: *blind regeneration* (run the writer again with the same prompt, hoping for stochastic improvement — empirically destroys content) versus *targeted gate-specific correction with explicit feedback* (run the writer or reviewer with the specific gate diagnostic + a bounded change directive — adds information between attempts). V7's existing strict-JSON corrective redispatch on parse failure is already an instance of the latter pattern; this ADR generalises it across content gates.

---

## Decision

**Each detected gate failure MAY trigger one targeted correction attempt, bounded by hard architectural constraints that prevent the correction sliding into ADR-007's killed pattern.**

### Hard constraints (all four MUST hold for any gate's correction path)

1. **Patch-bounded.** Writer corrective redispatch is **append/insert-only**. The writer's correction prompt template MUST include the previously-passing prose verbatim, plus an explicit instruction to *modify in place via append/insert, never re-author or regenerate*. Forbidden phrases in the prompt include "regenerate", "rewrite", "produce again", "start over". Reviewer corrections emit only `<fixes>` find/replace blocks, never `<rewrite>` directives (per ADR-007).

2. **Full revalidation.** After ANY correction, ALL Python QG gates re-run, not just the failed one. A new `previously_passed_regression` meta-gate fires terminal if any prior-passing gate now fails — this is the explicit ladder-prevention guard. (Codex finding, ADR-008 review.)

3. **Pipeline-assisted dictionary.** For lexical gates (`vesum_verified`, `russianisms_clean`, `surzhyk_clean`, `calques_clean`, `paronym_clean`, `citations_resolve`), the pipeline performs deterministic dictionary lookup against VESUM / Антоненко-Давидович / sources registry and proposes verified replacement candidates. The reviewer's role is to **select among proposed candidates** and emit `<fixes>` find/replace; the reviewer does NOT invent replacements (hallucination risk per Codex finding).

4. **One attempt per gate.** Each Python QG gate gets ONE correction attempt. If correction fails verification, the build terminals with a structured diagnostic. No tier escalation, no second-strategy fallback. The LLM QG `<fixes>` 2-round budget from ADR-007 is preserved unchanged.

### Per-gate correction paths

| Gate | Correction path | Cognition | Mechanism | Notes |
|---|---|---|---|---|
| `strict_json_parse` | corrective redispatch | writer | feedback prompt with parse error | EXISTS in V7 (round-3 contract) |
| `word_count` | corrective redispatch | writer | feedback: section budget gap, max-words bound, `insert_after` location | append-only |
| `plan_sections` | corrective redispatch | writer | feedback: per-section budget gap, plan points to address | append-only, section-targeted |
| `immersion` | reviewer `<fixes>` | reviewer | find English instructional phrasing, replace with Ukrainian equivalent | local lexical change (Gemini finding) |
| `formatting_standards` | corrective redispatch | writer | feedback: missing mandatory callouts (e.g. `> [!model-answer]`) | append-only insert (Gemini finding) |
| `mdx_render` | corrective redispatch | writer | feedback: render error + line | append-only fix unless deterministic repair available |
| `vesum_verified` | reviewer `<fixes>` | reviewer + pipeline | pipeline proposes VESUM-verified alternatives; reviewer selects | deterministic candidate generation |
| `russianisms_clean` / `surzhyk_clean` / `calques_clean` / `paronym_clean` | reviewer `<fixes>` | reviewer + pipeline | pipeline proposes Антоненко-Давидович alternatives; reviewer selects | deterministic candidate generation |
| `citations_resolve` | reviewer `<fixes>` | reviewer + pipeline | pipeline proposes from sources registry; reviewer selects | deterministic candidate generation |
| `inject_activity_ids` | deterministic pipeline insert | pipeline | mechanical insertion of `<!-- INJECT_ACTIVITY: id -->` markers | no LLM call |
| `ai_slop_clean` | reviewer `<fixes>` | reviewer | find banlist hit, replace with natural phrasing | banlist-driven |
| `component_props` | terminal (zero retry) | none | failure indicates writer cannot follow schema = template/plan fault | per Codex finding |
| `previously_passed_regression` (META) | terminal (zero retry) | none | any prior-passing gate now failing after correction | ladder-regression guard |
| LLM QG REVISE on per-dim score | reviewer `<fixes>` | reviewer | find/replace per dim feedback | UNCHANGED from ADR-007, max 2 rounds |

### What this ADR does NOT do

- Does NOT revive any of ADR-007's killed strategies (`section_rewrite`, `full_rewrite`, `writer_swap`, auto-heal).
- Does NOT change the LLM QG fix-loop budget (still 2 rounds per ADR-007).
- Does NOT change the reviewer-as-fixer policy for content quality (still `<fixes>` find/replace, never blind regen).
- Does NOT introduce a tiered escalation — every correction is a single targeted shot.
- Does NOT enumerate all V7 gates. Additional gates (vocab consistency, activity ID uniqueness, citation provenance, forbidden-language leakage, asset/link existence, duplicate detection) are separate gate-inventory work, tracked as follow-up issues, not part of this ADR.

---

## Consequences

### Positive

- **Phase 5 fan-out becomes feasible.** Marginal Python QG failures (12% short on word count, one stray russianism) are autonomously corrected with bounded cognition, not human-triaged.
- **Round-4 bakeoff (#1622) measures something predictive.** Phase 5 will run with corrections; bakeoff under ADR-008 measures first-pass quality + correction-responsiveness, the actual signal we need to choose claude-tools vs gemini-tools.
- **ADR-007 evidence holds.** All four killed strategies remain killed. The 9.6 → 8.4 regression pattern cannot recur because (a) writer is patch-bounded, (b) reviewer doesn't invent dictionary replacements, (c) `previously_passed_regression` terminals on any backslide, (d) one attempt per gate.

### Negative

- **More complexity in the pipeline.** Each gate now has a per-type correction handler instead of a uniform terminal path.
- **Test surface grows.** Need test coverage per gate × correction path, plus the meta-gate for regression detection.
- **Bakeoff timing.** Round-4 bakeoff (#1622) is blocked on ADR-008 implementation (in addition to wiki integration migration). Sequencing: wiki migration + ADR-008 implementation in parallel, both ship before bakeoff fires.

### Risks

- **Drift back to ladder.** Mitigated by: structural test asserting no second-strategy fallback exists; `previously_passed_regression` meta-gate; explicit forbidden-phrase audit on writer correction prompt template.
- **Pipeline-assisted dictionary lookup quality.** If the candidate generator is weak, reviewer has nothing good to select from and emits a poor `<fixes>` block. Mitigated by: dictionary lookups are well-tested in MCP `sources` (VESUM, Антоненко-Давидович, СУМ-11); gate is verifiable.
- **Patch-bound enforcement.** If the writer ignores the "modify in place" directive and re-authors, `previously_passed_regression` fires terminal. The recovery path is a new dispatch with a tighter prompt — not a heavier correction.

---

## Sequencing

1. **ADR-008 (this document)**: PROPOSED → ACCEPTED on user signoff.
2. **Wiki integration migration** (independent): port V6's `_build_wiki_packet` + `compress_wiki_packet` into `linear_pipeline`; replace deprecated Qdrant call. Tracked as a separate issue (TBD #).
3. **ADR-008 implementation**: per-gate correction handlers + `previously_passed_regression` meta-gate + structural drift-prevention tests. Tracked as a separate issue (TBD #).
4. **Round-4 bakeoff (#1622)**: fires after both (2) and (3) merge to main. Bakeoff brief updated to capture first-pass gate-failure rate as a sub-metric.

ADR-008 implementation and the wiki migration are independent and can ship in parallel.

---

## Cross-agent review summary

Both reviewers (Gemini-3.1-pro-preview and Codex-gpt-5.5) returned **REVISE** on the v1 proposal of this ADR; v2 (this version) incorporates their findings. Strong agreement across both reviews on:

- Patch-bound constraint on writer redispatch (CRITICAL)
- Full revalidation after correction (HIGH)
- Pipeline-assisted dictionary candidates rather than reviewer-invented replacements (HIGH)
- One attempt per gate; no tier escalation

Codex contributed: zero-retry list (`component_props`, etc.); `previously_passed_regression` meta-gate; gate-inventory misses (filed as separate follow-ups).

Gemini contributed: `immersion` reassigned writer → reviewer (lexical change discipline); `formatting_standards` new gate; explicit "modify in place" prompt-template directive.

Disagreement on sequencing: Codex preferred ADR-008 *after* round-4 bakeoff (clean V7 baseline); Gemini preferred ADR-008 *before* (predictive signal for Phase 5). This ADR resolves in favour of Gemini's position — the bakeoff is meant to inform Phase 5 fan-out, and Phase 5 will run with corrections.

Review messages preserved in `.mcp/servers/message-broker/messages.db` under `task_id='adr-008-review'`.

---

## Implementation pointers

- `scripts/build/linear_pipeline.py:run_python_qg` — current strict-fail-fast path; this is where per-gate correction routing lives.
- `scripts/build/linear_pipeline.invoke_writer` — already supports corrective redispatch via the strict-JSON parse-fail path; pattern extends to other gates with feedback construction.
- `scripts/build/phases/v6-review` — V6's `<fixes>` apply path; pattern transfers to per-gate reviewer corrections.
- `scripts/audit/check_self_review.py` — `SELF_REVIEW_DETECTED` gate; reviewer for `<fixes>` must be different from writer.
- `claude_extensions/rules/non-negotiable-rules.md` §4 — reviewer-as-fixer rule; ADR-008 refines the scope to include pre-LLM-QG gates.
- `claude_extensions/rules/pipeline.md` — needs an ADR-008 reference once accepted.

---

## Drift prevention

The following structural tests MUST exist after ADR-008 implementation, paralleling `tests/test_no_rewrite_contract.py` from ADR-007:

1. `test_no_writer_rewrite_in_correction` — asserts the writer correction prompt template contains the "modify in place" directive and the forbidden-phrase list ("regenerate", "rewrite", "produce again", "start over").
2. `test_correction_fully_revalidates` — feeds an artifact with deliberate `word_count` short through the correction path; asserts ALL Python QG gates run after correction, not just `word_count`.
3. `test_correction_does_not_regress_passing_gates` — feeds an artifact where correction reintroduces a russianism; asserts `previously_passed_regression` fires terminal.
4. `test_one_attempt_per_gate` — asserts each Python QG gate has at most one corrective handler invocation per build, and no second-tier escalation logic exists.
5. `test_pipeline_proposes_dictionary_candidates` — asserts that for `vesum_verified` / `russianisms_clean` / etc., pipeline-side candidate generation runs before the reviewer is invoked.
