# ADR-007: No hard grade filter for CEFR-track retrieval

**Status**: Accepted
**Date**: 2026-04-20
**Deciders**: Krisztian Koos (project owner), Claude (architecture)
**Related**: #1339 (introduced the gate), #1340 (removed the gate), #1348 (dense rerank that obviates it), ADR-006 (compile-layer retrieval)

## Context

#1339 (2026-04-18) introduced a hard SQL filter mapping CEFR tracks → Ukrainian school grades:

```python
_TRACK_GRADE_RANGES = {"a1": ("1","2","3","4"), "a2": ("1","2","3","4"), ...}
```

It was added in response to one symptom: a Grade 10 morphology textbook chunk surfaced in an A1 vowels lesson via the FTS5-only retrieval path, producing 19 cited sources where one was pedagogically absurd. The fix gated all `search_textbooks` / `_search_sections_fts5` calls by track→grade.

Two weeks later (#1340), the project owner challenged the premise. The challenge:

1. **CEFR L2 levels and Ukrainian L1 school grades describe orthogonal scaffolding systems.** CEFR describes what an L2 learner can DO in the target language (functional capability). School grades describe staged content for NATIVE speakers who already speak Ukrainian fluently (developmental sequencing for L1). They are not interchangeable.

2. **Adult L2 metacognition rewires the level mapping.** A Grade 5 systematic phonetics chapter ("Голосні утворюються голосом, приголосні — голосом і шумом, шум виникає коли струмінь повітря прориває перешкоду, створену органами мовлення") would overwhelm a Grade 1 native who lacks the metalinguistic scaffolding, but is exactly the explicit, terminology-rich treatment that helps an adult L2 A1 learner. Grade 1-2 primer language ("Голосні почуєш в пісні") is also useful but not because it's "A1-appropriate" — because it's a different register.

3. **The 2026-04-18 symptom was a relevance bug, not a scope bug.** Pre-#1348 retrieval used FTS5 keyword match only. Grade 10 morphology surfaced for a vowels query because the FTS5 ranking didn't understand topic semantics. Post-#1348 dense rerank handles topic relevance natively. The grade gate became a band-aid for a cured disease.

Empirical retrieval-playback (`a1/sounds-letters-and-hello`, commit `ae56349e9`):

| Strategy | Concept coverage | Verdict |
|---|---|---|
| Pre-#1340 (gate enforced) | 3/10 modern_dense, 6/10 legacy_chunk | retrieval_bottleneck |
| Post-#1340 (gate removed) | 7/9 modern_dense, 7/9 legacy_chunk | writer_bottleneck |

The gate was suppressing 4 reachable concepts (`larynx_touch_exercise`, `final_voicing`, `milozvuchnist_v_to_w_gloss`, `sound_before_letter`) that live in Grade 5+ Ukrainian-language textbooks and are pedagogically right for L2 A1.

## Decision

Hard SQL grade filters are not used in CEFR-track retrieval. Specifically:

1. `_search_sections_fts5` and `search_textbooks` accept a `track` parameter for backward compatibility but no longer apply `WHERE grade IN (...)`.
2. The `_TRACK_GRADE_RANGES` symbol is removed from `scripts/wiki/sources_db.py`. Tests assert it does not exist (guard against accidental reintroduction).
3. Topic relevance is the responsibility of:
   a. **Dense rerank** (#1348 `mlx_dense_rerank`) — primary mechanism.
   b. **Per-track corpus priors** in `scripts/wiki/track_priors.yaml` — soft weighting at rerank time.
   c. **Diagnostic playback** (`scripts/wiki/diagnostics/retrieval_playback.py`) — empirical verification that the in-scope concepts for a target module are actually reachable.

If a future change wants to re-introduce grade-aware retrieval, it MUST take the form of a **soft prior** (additive rerank-time boost), not a hard SQL gate, and MUST be gated behind a #1340-style retrieval-playback diagnostic showing dense rerank cannot solve the relevance problem on its own.

## Alternatives considered

- **A. Restore the hard gate (#1339 status quo)** — rejected. The gate suppressed 4/9 reachable A1 concepts because it confused L2 capability with L1 developmental staging. The original symptom that motivated the gate is solved by dense rerank.

- **B. Keep `_TRACK_GRADE_RANGES` as dead code "in case we need it later"** — rejected. Dead code accrues stale comments and tempts future agents to re-wire it. Git history preserves the mapping; if we resurrect it, we resurrect it deliberately.

- **C. Replace the hard gate with a soft prior NOW** — deferred, not rejected. The empirical evidence shows dense rerank alone gets us to 7/9 with `writer_bottleneck` verdict. Adding a soft prior is premature optimization until we know the writer/reviewer side is also fixed. Filed as separate issue (see Verification below).

- **D. Keep the gate but tier it by rough developmental zones (`a1`→1-6, `a2`→1-8, etc.)** — rejected. Same architectural error, less aggressive form. CEFR and school grades remain orthogonal regardless of how we set the band.

## Consequences

**Positive**:
- Grade 5+ systematic Ukrainian-language pedagogy reachable for A1/A2 learners (was unreachable).
- Dense rerank is now the single source of truth for topic relevance — easier to reason about, audit, and improve.
- Future content-quality improvements happen at the rerank/prior layer, not the SQL filter layer (closer to the actual relevance signal).

**Negative / risks**:
- Stage-appropriateness depends entirely on dense rerank quality. A regression in the rerank model could let pedagogically inappropriate Grade 9-10 theoretical text into A1 articles. Empirically observed in the post-#1340 playback: `final_voicing`, `v_to_w_rule`, `yi_letter_two_sounds`, `ya_yu_ye_dual` are currently satisfied by Grade 9-10 chunks in the modern_dense path. The diagnostic flags this with `writer_bottleneck` but the underlying rank-order issue is real.
- Removes a defense-in-depth layer. If dense rerank is the only stage-appropriateness signal, a dense-rerank failure has no fallback.

**Neutral / follow-ups**:
- Track→grade mapping preserved in git (`scripts/wiki/sources_db.py` deletion in commit `ae56349e9`) for reference.
- Codex adversarial review of #1340 (2026-04-20) confirmed: no hidden consumer of `search_textbooks`/`search_sources` relies on the implicit grade gate. The only production caller is `scripts/wiki/enrichment.py`. `scripts/research/build_knowledge_packet.py` never passed `track`.

## Verification

1. **Test guard**: `tests/wiki/test_grade_filter.py::test_search_textbooks_does_not_apply_hard_grade_filter` asserts `_TRACK_GRADE_RANGES` is not present and that A1 retrieval reaches Grade 5+ chunks.
2. **Empirical diagnostic**: `scripts/wiki/diagnostics/retrieval_playback.py` re-runnable as `--track a1 --slug sounds-letters-and-hello --compare`. PASS threshold = 80% concept coverage.
3. **Rank-order regression test (FUTURE WORK)**: Codex review #1340 flagged that "concept present anywhere" is too lax — Grade 9/10 chunks should not outrank Grade 1/2 or Grade 5 primers for A1 queries. A separate issue tracks adding a rank-order test (pedagogical-proximity metric) that asserts primer chunks are surfaced first. Until that test exists, "no hard grade filter" depends on dense-rerank quality being adequate, which is empirically true today but not guarded.
4. **Revisit trigger**: If we observe a content-review failure traceable to "Grade 10 stylistics text in A1 lesson" or similar, this ADR should be revisited — not by restoring the hard gate (rejected above), but by implementing the soft prior (Alternative C) with the empirical diagnostic that justifies it.
