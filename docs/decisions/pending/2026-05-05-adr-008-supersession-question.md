# Pending Decision — ADR-008 supersession-or-keep, given deliberation-as-pre-review

> **Type:** Architectural — affects every Phase-5 module build path
> **Scope:** Pipeline correction architecture (`scripts/build/linear_pipeline.py`); does NOT affect orchestration, content, or curriculum tracks
> **Authored by:** Claude (overnight autonomous session, 2026-05-05)
> **For:** Krisztian morning review
> **Recommendation:** **Keep ADR-008 (DO NOT scope down).** One-sentence why: deliberation prevents bad CONTENT from reaching the reviewer; ADR-008 catches bad MECHANICAL gate output. They operate on different failure modes — removing ADR-008 because deliberation works is a category error.

---

## State of play (3 sentences)

ADR-008's per-gate correction paths shipped via PR #1636 on 2026-05-02 (#1632 closed). Yesterday's session (2026-05-05 handoff) empirically validated multi-agent pre-review deliberation as a quality mechanism — the собака-gender deliberation surfaced and refused a Gemini fabrication that would have shipped pre-protocol-fix. The handoff queued an open question: now that deliberation works, should ADR-008's full gate-correction loop be (a) kept as fallback, (b) scoped down to thin residual policy, or (c) deprecated?

## What the two architectures actually do

| Layer | Fires when | Fixes what | Fails when |
|---|---|---|---|
| **Pre-review deliberation** (`ab discuss` round-2-min) | Cross-agent design / framing / linguistic decisions | Hallucinated citations, training-data-prior framings, domain bias | Agents share the bias (correlated priors on Ukrainian linguistics, etc.) |
| **ADR-008 gate-correction** (`linear_pipeline.py` Python QG → corrective redispatch / reviewer `<fixes>`) | Module build per-gate Python checks | Word-count shortfall, missing required terms, VESUM-failed lexemes, calques, formatting holes | Same gate fails again post-correction (then `previously_passed_regression` terminals) |

These are **different layers operating on different artifacts**:

- Deliberation runs on **deliberation channel posts** — design conversations, linguistic-rule writes, architectural debates. The output is text in a channel.
- ADR-008 runs on **module build artifacts** — generated lesson MDX going through Python QG. The output is `curriculum/.../{slug}.mdx`.

The handoff's framing — "deliberation reduces the rate of REVISE verdicts so ADR-008's per-gate correction loop becomes a thin fallback" — conflates these. The LLM QG reviewer that emits REVISE is the **post-write strict reviewer**, not deliberation. Deliberation never sees module content. So deliberation does NOT reduce REVISE rates; it reduces design-error rates upstream of build.

## What deliberation actually displaces

The thing deliberation makes redundant is **NOT** ADR-008. It's the case where:
- An ambiguous design or linguistic question lands directly in a writer prompt
- The writer encodes a wrong assumption into module content
- The post-write reviewer flags it as REVISE
- ADR-008 corrects it via reviewer `<fixes>`

If deliberation upstream resolves the ambiguity, the writer never encodes the wrong assumption, and the reviewer never has to flag it. So deliberation **shifts work earlier in the pipeline**, but it does not eliminate the per-gate failure modes ADR-008 addresses (word count, VESUM mismatch, formatting holes — these are mechanical failures unrelated to design ambiguity).

## Why scoping down is risky

The four ADR-008 invariants (patch-bounded, full-revalidation, pipeline-assisted dictionary, one-attempt-per-gate) are individually load-bearing:

1. **Patch-bounded** prevents ADR-007's killed full-rewrite ladder. Removing this re-opens the regression ADR-007 fixed.
2. **Full revalidation** with `previously_passed_regression` meta-gate prevents the correction itself from breaking other gates. Removing this allows silent backslide.
3. **Pipeline-assisted dictionary** prevents reviewer-invented replacements (the same hallucination class deliberation surfaced — собака-style fabrications). Removing this re-introduces the failure mode deliberation just exposed.
4. **One-attempt-per-gate** prevents tier escalation cycles. Removing this is fine if the cap is preserved elsewhere; redundant otherwise.

Of the four, only #4 is plausibly redundant. The other three address mechanical-gate failure modes that deliberation cannot reach.

## What scope-down would actually look like (option b)

If you still want a "thinner residual policy," here's the only honest framing:

- **Keep:** all four invariants, all 11 gate-correction paths, `previously_passed_regression` meta-gate.
- **Drop:** none of the above.
- **Re-frame:** describe ADR-008 as "post-write mechanical correction" and add a paragraph to the ADR explicitly noting deliberation operates upstream and reduces design-error volume reaching the reviewer.

That's a documentation change, not an architecture change. Calling it "scope-down" overstates it.

## Three options + my pick

**(a) Keep ADR-008 as-is.** Status bump from PROPOSED → ACCEPTED in `docs/decisions/2026-04-28-targeted-gate-correction-paths.md`. Add a one-paragraph note positioning deliberation as upstream of the reviewer. **(my pick)**

**(b) Re-draft as thinner residual-correction policy** behind deliberation. As argued above, the actual delta this would produce is documentation, not code. The handoff's instinct that this is "probably (b)" assumes deliberation displaces post-write correction; it doesn't.

**(c) Deprecate entirely.** Rolls back PR #1636. Re-introduces the no-correction-path tension that #1620 (round-3.5 verification) hit empirically with `word_count` 1020/1200 fail-terminals. The user explicitly stated 2026-04-28 *"human triage is not feasible we have to be able to fix detected errors and mistakes."* Deprecating ADR-008 contradicts that stated constraint without providing an alternative.

## Concrete action if you pick (a)

Two-line PR:

1. `docs/decisions/2026-04-28-targeted-gate-correction-paths.md` — bump `**Status**: PROPOSED 2026-04-28` → `**Status**: ACCEPTED 2026-05-05 (implemented PR #1636, validated by Phase-5 fan-out tests)`.
2. Append `## Position in the V7 architecture` section noting deliberation operates pre-review and reduces design-error volume; ADR-008 operates post-write on mechanical Python QG gates; LLM QG `<fixes>` 2-round budget (ADR-007) operates between them.

Estimated effort: 15 minutes including adversarial review.

## What I want you to confirm

- Pick (a), (b), or (c) — or tell me my framing is wrong somewhere.
- If (a): I'll write the status-bump PR in a worktree, dispatch Codex review, merge if clean. ~30 min total.
- If (b) or (c): give me the specific scope you want and I'll execute.

---

**File location:** `docs/decisions/pending/2026-05-05-adr-008-supersession-question.md`
**Cross-references:** ADR-008 (`docs/decisions/2026-04-28-targeted-gate-correction-paths.md`), ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`), implementation PR #1636, deliberation-validation handoff `docs/session-state/2026-05-05-deliberation-architecture-validated.md`, deliberation-protocol-fix commit `872d8791`.
