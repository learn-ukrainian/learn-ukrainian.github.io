# Session Handoff — 2026-05-05 Overnight (citation-provenance check shipped)

> **Predecessor:** `2026-05-05-overnight-autonomous-claude-cli-dispatch-fix-and-codeql-cleanup.md`
> **Mode:** User asleep, autonomous orchestration. Worked the predecessor handoff queue end-to-end: landed #1692, implemented + merged #1683 (the predecessor's TOP next priority), audited follow-up reviewer prompts.

---

## TL;DR — what shipped this session

### Merged this session

- **PR #1692 → main** (commit `670ef940e7`): `feat(reviewer): add false-positive Russianism guard to v6-review-language (#1691)`. Closes #1691.
  - Rebased the predecessor's branch onto current main (post-#1693 the inherited test failure cleared automatically). Force-pushed `1bf409989e`. CI 24/25 green (1 advisory `review/review` non-blocking per memory rule #0H). Codex re-review on the rebased branch returned **CLEAN [AGREE]** with explicit endorsement of the deny-list scope ("Keep the deny-list narrow … broadening would risk an unmaintained pseudo-lexicon"). Squash-merged + worktree cleaned up.

- **PR #1694 → main** (commit `c36d159a26`): `feat(bridge): citation-provenance check for channel posts (#1683)`. Closes #1683 (the predecessor's #1 priority).
  - 3 commits on the branch: `fbd8aa535f` (initial), `aacf77f5cb` (Codex blocker fix), `9f594b7cc8` (docstring polish).
  - Codex review: 1 round → 1 BLOCKER (Правопис verifier doing live HTTP via topic→section helper) → fixed → 1 round → CLEAN [AGREE] with one non-blocker docstring nit → addressed in polish commit. Two squashed-merge-ready CI cycles, all-green on both.

### NOT touched this session (per predecessor instructions)

- **4 Gemini draft PRs** (#1687/#1688/#1689/#1690) — STILL DRAFT for user security review. Untouched per the predecessor's "do not auto-merge" instruction.
- **#1665 (Holovashchuk dictionary ingest)** — still deferred pending alternative live PDF source (kpdi.edu.ua URL is 404).
- **ADR-008 supersession brief** — `docs/decisions/pending/2026-05-05-adr-008-supersession-question.md` — still awaiting user signoff.

---

## #1683 implementation summary (the engineering meat of this session)

`feat(bridge): citation-provenance check for channel posts (#1683)`

**Driving incident.** On 2026-05-05, two `ab discuss` runs hours apart on собака gender (threads `482884ca054e` + `7c6e401053bb`) produced the same fabricated Антоненко-Давидович citation: *"explicitly emphasized by Антоненко-Давидович у посібнику «Як ми говоримо», who categorizes the use of feminine agreement with собака as a morphological calque/Russianism."* АД has no entry on собака per `mcp__sources__search_style_guide` — the model's prior was the bug, not the source. The deliberation-protocol fix (`872d8376b0`) caught the live channel-post case by blocking round-1 short-circuit. This PR closes the gap when a fabrication survives multiple rounds of `[AGREE]`.

**Scope.** ~1365 LOC across 4 files (final, post-Codex-fixes):

- `scripts/ai_agent_bridge/_citation_check.py` (NEW, ~510 LOC): detection + verification + annotation.
- `scripts/ai_agent_bridge/_channels.py` (modified, ~30-LOC delta): adds `verify_citations: bool = True` keyword to `post()`. Hooks the check before the DB insert.
- `tests/test_citation_check.py` (NEW, ~620 LOC, 33 cases): unit + integration coverage including the canonical Gemini fabrication regression + the Правопис soft-skip regression Codex asked for.
- `docs/best-practices/agent-cooperation.md` (modified): new "Citation provenance check" subsection under Multi-Agent Deliberation.

**Algorithm v1 (annotate-mode, not block-mode):**

1. Detect source-name matches with permissive Cyrillic inflection. Sources split into two tiers:
   - **DB-verified** (flag on absent headword): Антоненко-Давидович, Грінченко 1907, СУМ-11, ЕСУМ.
   - **Detection-only / soft-skip** (count, never flag): Правопис 2019, VESUM, Шевельов, Вихованець, Пономарів.
2. Extract headword from local window (italicized `*foo*`, code-fenced ``` `foo` ```, quoted, or "іменник X" / "слово X" / "лексема X" patterns). Bias toward post-citation matches; pre-citation fallback when no post-citation candidate exists.
3. Verify via `wiki.sources_db` lookups. АД uses word-column lookup + body-LIKE fallback because `style_guide.word` column holds section titles, not lemmas (only 279 entries — fast).
4. Multi-pattern same-source mentions within ~200 chars dedupe to one citation.
5. Annotation appended BEFORE any trailing `[AGREE]`/`[DISAGREE]` token so deliberation tail-check (`_channels_cli.py:1306-1308`) keeps matching.
6. Missing `data/sources.db` → soft-skip; never flag (deployment problem cannot manufacture false positives).

**Annotation format:**

```
<!-- CITATION-UNVERIFIED: source=antonenko_davydovych headword="собака" reason="no entry for «собака» in Антоненко-Давидович (verified via search_style_guide + body LIKE scan)" -->
```

**Out of scope (deferred):**

- Fuzzy-match of quoted text against source body content (would require search-then-content-similarity).
- LLM-based attribution detection (regex misses paraphrases).
- Block-mode rejection.
- Local Правопис headword index (would unlock the Правопис tier from soft-skip → DB-verified).

The v1 catches outright fabrication where the headword does not exist anywhere in the source corpus — exactly the собака/АД class.

---

## Handoff item #6 — reviewer-prompt audit (CLOSED)

The predecessor handoff listed item #6 as: *"Audit other reviewer prompts if #1692 merges cleanly: v6-review-factual.md, v6-review-honesty.md, v6-review-uk.md, linear-review-dim.md."*

**Audit result: no further changes needed.**

- `v6-review-factual.md` only mentions "Russianism" as a rejection example for invalid factual findings ("should be стіл not стол" → that's a Language dim concern). No flagging logic.
- `v6-review-honesty.md` and `linear-review-dim.md` have no Russianism/calque/собака mentions at all.
- `v6-review-uk.md` lists Russianisms as one of 4 mandatory checks but is NOT wired up via `_resolve_phase_template_path` in `v6_build.py` — it appears to be a legacy / unwired prompt. Active per-dim path is `v6-review/v6-review-language.md` (already guarded by #1692).
- `v6-review.md` similarly not wired up for live review (referenced in comments only at `v6_build.py:8433,8608`).
- `v6-review-style.md` already has a partial guard ("When in doubt about a calque/Russicism, check the style guide first") — sufficient per Codex's "keep narrow" review of #1692.

**Conclusion.** The Russianism-fabrication risk is now contained by three layers:
1. #1692's per-dim language-reviewer guard + 5-headword deny-list.
2. The existing style-reviewer's "check style guide first" wording.
3. PR #1694's general citation-provenance check that catches verbatim АД/Грінченко/СУМ-11/ЕСУМ fabrications across ALL channel posts (not just review verdicts).

The three-layer defense is the right scope — broadening would either (a) duplicate logic across dead reviewer prompts (`v6-review.md` / `v6-review-uk.md`) or (b) violate Codex's "keep narrow" directive on the deny-list.

---

## Next-session priorities

1. **User reviews 4 Gemini draft PRs** (#1687/#1688/#1689/#1690). Same recommendation as the predecessor handoff: review in order B → C → D → A. No agent action — these need human security/license judgment.

2. **ADR-008 supersession brief** — `docs/decisions/pending/2026-05-05-adr-008-supersession-question.md`. Recommendation: option (a) keep ADR-008 as-is, status bump only. ~30 min of work pending user signoff.

3. **Re-dispatch #1665 (Holovashchuk ingest)** if user surfaces an alternative live PDF source. Comment on #1665 listed candidates: lounb.org.ua, slovnyk.me linguistic_norm mirror, chtyvo.org.ua.

4. **HIST/OES seminar deliberation pilot** (predecessor handoff item #6). NOT touched this session. Lower priority but still open.

5. **(Optional v2)** Build a deterministic local Правопис headword index. The v1 soft-skip is correct but eventually we want Правопис citations to flag fabrications too. Spec: a SQLite table mapping every Правопис rule's headwords (extracted from the rule body) → section number, queryable by exact headword. Replaces the topic→section dict in `rag.source_query.PRAVOPYS_SECTIONS` for verification purposes (the existing dict can stay for actual rule-fetching). When this ships, swap `_verify_pravopys` from soft-skip to a real verifier and remove the regression `test_pravopys_never_flags_in_v1`.

---

## Workflow lessons captured this session

1. **Worktree sparse-checkout interacts badly with `data/`-dependent tests.** When implementing #1683 from the worktree, `wiki.sources_db._get_conn()` resolved `PROJECT_ROOT/data/sources.db` to the WORKTREE path (no `data/`), not the main repo's `data/`. Same for `data/external_articles/*.jsonl` (`test_channels_registry` / `test_wiki_channels` failed in worktree). Symlinking the missing files into the worktree was the workaround. Long-term: either make `SOURCES_DB_PATH` overridable via env var, or stop sparse-checking out `data/` in worktrees that need to run sibling tests. CI has full `data/` so the issue doesn't reproduce in CI — only stings local development from worktree.

2. **Body-text fallback is required for АД.** AD's `style_guide` table indexes by section TITLE, not lemma — `search_style_guide("собака")` returns empty even when АД genuinely covers the word in body content. The v1 `_citation_check._verify_antonenko` does word-column lookup THEN body LIKE scan. AD has 279 entries so `WHERE text LIKE %word%` is fast.

3. **Headword extraction needs post-citation bias with pre-citation fallback.** First implementation gave equal weight to both sides and would pick the wrong headword in `"Earlier we mentioned *вертеп*. Antonenko-Davydovych says *собака* is..."`. Fixed: prefer matches AFTER `span_end`, fall back to BEFORE `span_start` if no after-candidate exists. Codex flagged the missing pre-fallback test.

4. **The deliberation tail check is load-bearing for any annotation system.** `_channels_cli.py:1306-1308` strict-`endswith("[AGREE]")` check means any annotation has to go BEFORE the tail token, not after. The annotation logic in `_citation_check.annotate_body` does this explicitly via a regex tail-search. Future PR that adds annotation behavior must respect this constraint.

5. **Don't let a "topic→X" helper masquerade as a "headword→presence" verifier.** Codex caught this on round 1 of the #1683 review. `rag.source_query.pravopys_lookup` looks like a verifier, but (a) it returns None for unmapped headwords (which my generic verifier treated as "absent" → false flag), and (b) on mapped topics it does live HTTP via `pravopys_section`. **General lesson:** before plumbing any external lookup into a synchronous-pre-commit code path, read its implementation, not just its signature.

---

## Statistics

- **PRs opened:** 1 (#1694)
- **PRs merged:** 2 (#1692, #1694)
- **Issues closed:** 2 (#1691 via #1692 merge; #1683 via #1694 merge)
- **Commits on my branches:** 3 on #1694 (`fbd8aa535f` initial, `aacf77f5cb` Codex-blocker fix, `9f594b7cc8` docstring polish), 1 force-push rebase on #1692 (`1bf409989e`)
- **Adversarial review cycles:** 1 round with Codex on #1692 (CLEAN [AGREE] first pass); 2 rounds with Codex on #1694 (round 1: 1 BLOCKER → fixed; round 2: CLEAN [AGREE] with 1 non-blocker docstring nit → also fixed)
- **Codex dispatches:** 0 — only 2 inbox-runner invocations for review processing
- **Gemini dispatches:** 0
- **Worktrees alive at session end:** 4 (the 4 Gemini codeql draft worktrees from the predecessor session, untouched per instructions)
- **Token budget at session end:** ~280K (within 400K hard target)
- **Wall-clock duration:** ~2.5h from session start to handoff write

## Cross-thread notes (still active)

- **Codex weekly cap** still cleared. Used 2 inbox-runner invocations this session.
- **Gemini uncapped** — no Gemini work this session (all Codex review).
- **slovnyk.me license posture** unchanged.
- **Memory rules #0F + #0G applied** — verified the predecessor handoff's framing of #1683 ACs against the actual issue body before designing; verified #1692's CI-failure diagnosis as "inherited from #1693" by reading the actual job log before rebasing.
- **Memory rule #0H applied twice** — merged #1692 and #1694 myself after CI cleared + Codex CLEAN without asking the user. Each merge was 30 seconds of action vs. waiting for the user to sign off on green CLEAN reviews.
- **Memory rule "investigate before acting" applied** — when Codex's BLOCKER on #1694 said `pravopys_lookup` does live HTTP, I read `rag/source_query.py:812` to confirm before designing the fix. Codex was right; the fix landed clean on round 2.
