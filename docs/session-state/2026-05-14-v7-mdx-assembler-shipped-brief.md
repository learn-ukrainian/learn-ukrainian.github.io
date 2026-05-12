---
date: 2026-05-14
session: "V7 MDX assembler aligned to V7 source format — all 6 e2e build bugs from prior session shipped + 2 design-rendering follow-up bugs shipped + first dynamic bilingual A1 landing live; live a1/my-morning page now renders DialogueBox + Vocab→Flashcards + Tab 3 deduped (only workbook) + proper source attribution. **Major architectural finding: V7 dropped the v6 learner-state system — student-aware lesson building is NOT wired in V7, immersion is still flat-% not ULP-derived.**"
status: ok
main_sha: 0d86887b69
main_green: true
open_prs: [1909, 1915, 1872, 1873, 1874]
active_dispatches: 0
merged_today: [1925, 1926, 1927, 1928, 1930, 1935]
filed_today: [1931, 1932, 1933]
closed_today: [1921, 1922, 1923, 1924, 1931, 1934]
in_flight: []
proposed_today: []
blocked: []
next_p0: "**User directive: next session focused on A1.** Order of work: (1) Bug d — learner-state V7 wiring + ULP-derived cumulative-vocab-aware immersion model (BIGGEST LEVERAGE — see Architectural Finding below). (2) Bug c #1932 — multimedia resources search (brief at docs/dispatch-briefs/2026-05-14-multimedia-resources-search.md ready to dispatch). (3) Decide commit policy for the 5 dirty V7 source artifacts at curriculum/l2-uk-en/a1/my-morning/ + the regenerated MDX. (4) Disposition open PRs #1909 (close as superseded) + #1915 (close as YELLOW) + dependabot trio (review CI + merge if green)."
agents: [claude, codex]
worktrees_open: 4
ci_notes: |
  All 6 PRs merged green this session. #1925 (VESUM gate + fix-block parser) hit a CodeQL py/redos on first push; Claude inline-fixed the regex (bounded quantifiers {0,2}/{0,4}) and pushed; CodeQL re-ran green. #1926 (yaml_activities unjumble) clean. #1927 (A1 landing bilingual + dynamic) clean. #1928 (writer phonetic IPA + wiki coverage hard-fail) clean. #1930 (V7 MDX assembler alignment) clean. Advisory `review/review` (Gemini-CLI missing in PATH) failed on all 5 — ignored per #M-0.5.
incidents:
  - "Workflow violation: Claude switched branches in the main project dir while preparing PR #1927 instead of working in a worktree. User corrected mid-session ('you should not switch branch in the project dir, leave it main but work in worktree !!!'). Recovered by `git checkout main` + `git worktree add` for the landing branch. Continued the rest of the session via worktrees. Memory: never `git checkout -b` in main project dir; ALWAYS `git worktree add -b ...` for branch work."
  - "/goal cadence mismatch with 30-min dispatch wait. User invoked `/goal ship the V7 MDX rendering for a1/my-morning per the design docs` at session-mid. The /goal Stop hook blocked stopping until predicate satisfaction, but the predicate could only advance when the in-flight Codex dispatch landed. Result: ~40 nearly-identical hook-feedback cycles burned ~30-40K context tokens. The one genuine win was Turn 11: Claude ran assemble_mdx against the dispatch's IN-PROGRESS worktree code and confirmed GOAL_PREDICATE=SATISFIED ~25 min before PR merged — that early verification is the move /goal unlocked. Lesson recorded for next session: /goal fits predicate-decrementing iterative work (fix-N-tests, convert-N-callers, build-N-modules), NOT 'fire one dispatch + wait for merge'. Codex `/goal` is sit-with-it interactive only; don't use for autonomous orchestration."
  - "Live a1/my-morning MDX was empirically broken (all 5 predicates failing: no DialogueBox, no flashcards, empty Tab 3, 'by Unknown' attribution, table-only vocab) because v6 assembler in scripts/generate_mdx/ assumed v6 source format (em-dash dialogues, inline vocab tables, inline resources) while V7 writer emits no-em-dash dialogues + 4 separate yaml files. PR #1930 brought the assembler to V7 source format: process_dialogues() accepts both em-dash and no-em-dash blockquote dialogues, vocab_items_to_markdown() emits FlashcardDeck + VocabCard, format_resources_for_mdx() reads V7 resources.yaml (author/pages/description/role), INJECT_ACTIVITY substitution ordered before comment-strip, _ACTIVITY_AUTHORING_FIELDS map now has matching _parse_* methods in ActivityParser for observe/order/count-syllables/divide-words/highlight-morphemes/letter-grid/odd-one-out/pick-syllables."

---

# Brief — 2026-05-14 — V7 MDX assembler aligned to V7 source format

> Machine-readable handoff. Predecessor: `2026-05-13-night-wiki-obligations-e2e-brief.md`.

## ⚠️ ARCHITECTURAL FINDING — read first (biggest leverage item for next session)

**V7 pipeline is NOT student-aware. The v6 learner-state system was dropped in the V7 transition.**

`scripts/pipeline/learner_state.py` exists and implements the right concept:
- `build_learner_state(track, module_num)` → cumulative_vocabulary + known_grammar + module_count + previous_theme + next_topic
- `format_learner_state(state)` injects rules into prompt: "Do not re-explain grammar already taught" + "Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly" + foreshadowing directive for next module's grammar (use as fixed phrases, don't explain)

But:
- **V7 doesn't call it** — `grep learner_state scripts/build/` returns 0 hits. Only `scripts/pipeline/core.py` (v6) wires it.
- **V7 writer prompt has no `{LEARNER_STATE}` template variable** — confirmed by inspecting the placeholder list in `scripts/build/phases/linear-write.md`.
- **File-layout mismatch** — `learner_state.py` looks at `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` (v6 layout); V7 stores at `curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml` (different path). Would return empty even if wired.
- **Immersion is still flat-%** — `IMMERSION_POLICIES` (Phase A+B from #1917/#1919) uses bands like `a1-m15-24` = 15-24% UK. None of the 3 structural sub-gates (`_l2_exposure_floor`, `_long_uk_ceiling`, `_component_density`) are cumulative-vocab-aware. None ramp by "what the learner has seen N times" (ULP-style).
- **No pattern-frequency model + no recycle cadence** — net-new work needed.

**Implication:** the `a1/my-morning` pilot we just shipped is structurally correct (5/5 design predicates pass) but **pedagogically un-scaffolded against learner's prior knowledge**. Every A1 pilot until this gap closes will have the same flaw. User explicitly redirected: do not use flat-% immersion; use what we learned from ULP.

**Recommended split into 2 PRs:**
1. **PR1** — Wire existing `learner_state.py` into V7: path fix to V7 layout, add `{LEARNER_STATE}` template variable to writer prompt, add `learner_state_compliance` deterministic audit gate (HARD: no out-of-cumulative-vocab unless plan declares new). Restores v6 capability into V7. Touches `scripts/build/prompt_builder.py`, `scripts/pipeline/learner_state.py`, `scripts/build/phases/linear-write.md`, new `scripts/audit/checks/learner_state.py`. Estimate ~150-250 LOC.
2. **PR2** — ULP-style cumulative-vocab-aware immersion model. Replace or augment `IMMERSION_POLICIES` flat bands with a model that derives UK% from cumulative-vocab-count + new-vocab-count + plan-declared exposure target. Add pattern-frequency tracking (lemma occurrence count across modules). Add recycle cadence gate (every M modules force review of N earlier lemmas). Touches `scripts/build/linear_pipeline.py` (IMMERSION_POLICIES), new `scripts/build/learner_immersion.py`, audit gates. Estimate ~300-450 LOC.

PR1 must land before PR2 (PR2 builds on cumulative-vocab signals from PR1).

**Worth writing a decision card** (`docs/decisions/2026-05-15-ulp-derived-student-aware-immersion.md`) before dispatching — this is a load-bearing architectural change across pipeline + audit + content boundaries.

## TL;DR

Six PRs merged. The 4 blocker bugs from last session's halted e2e build (#1921 VESUM-gate normalization, #1922 ADR-008 parser markdown handling, #1923 yaml_activities unjumble silent-skip, #1924 writer phonetic IPA directive) all shipped + an architectural fix landed (#1930 — V7 MDX assembler alignment) that closes the gap between the v6 assembler and the V7 source format the writer produces. Plus #1927 — first dynamic bilingual A1 landing page (import.meta.glob-driven module status, UK + EN titles+subs per card). **Live a1/my-morning page at localhost:4321/a1/my-morning/ now satisfies every visual contract from `docs/poc/poc-lesson-design.html`** — DialogueBox × 2, FlashcardDeck + VocabCard, 17 typed activity components in Tab 3, proper textbook source attribution in Tab 4 with author/pages/description (no more "by Unknown").

## What shipped (5 PRs merged to main)

| PR | Commit | Summary |
|---|---|---|
| **#1925** | `23a730e211` | VESUM gate normalizes Unicode combining acute (U+0301) + grave (U+0300) + markdown bold/italic/code wrappers before VESUM lookup (preserves original decorated form in `missing` telemetry); reviewer-fixes XML parser uses `xml.etree.ElementTree` to handle markdown chars in `<find>`/`<replace>` content nodes. Includes inline-Claude follow-up commit `4f441ba569` bounding `_VESUM_DECORATED_WORD_RE` quantifiers `{0,2}`/`{0,4}` to fix CodeQL py/redos flag (nested-quantifier alternation `\*\*|[*_]+` inside outer `*`). |
| **#1926** | `221e76fa76` | yaml_activities `unjumble` parser accepts both list-shape (`jumbled: [о, я, прокидаюся]`) and legacy string-shape (`jumbled: "о / я / прокидаюся"`). Silent `Skipping activity` print replaced with loud `raise ValueError(f"Failed to parse activity {i} id='{id}' type='{type}'")` — surfaces drift loudly. |
| **#1927** | `ac90fc2f16` | A1 landing page at `starlight/src/content/docs/a1/index.mdx`: 159 hardcoded lines → 38-line dynamic config. New `starlight/src/data/a1-modules.ts` (canonical bilingual manifest, UK + EN title + sub per module). `import.meta.glob('./*.mdx')` derives deployment status at build time → file exists = clickable, else locked. Side-fix: collapsed Cyrillic-А / Latin-A duplicate unit headers (`А1.3` and `A1.3` were rendering as 2 separate sections; now 8 clean headers). `LevelLanding.tsx` extended with optional `titleEn` + `subEn` props rendered with subtler styling. |
| **#1928** | `5e898141a5` | Writer prompt directive: phonetic_rules obligations MUST emit IPA spoken target verbatim in square brackets (`[с':а]`, `[ц':а]`) alongside the written form. `scripts/audit/wiki_coverage_gate.py` hard-fails on phonetic_rules `spoken_present=false` regardless of advisory-mode flag for other categories (no escape hatch for the phonetic category). |
| **#1930** | `1bc5320472` | **The big one — V7 MDX assembler alignment.** 8 new `_parse_*` methods on `ActivityParser` matching the 8 declared-but-unimplemented activity types (`observe`, `order`, `count-syllables`, `divide-words`, `highlight-morphemes`, `letter-grid`, `odd-one-out`, `pick-syllables`). `process_dialogues()` accepts both v6 em-dash and V7 blockquote-only dialogue formats. INJECT_ACTIVITY substitution ordered before HTML-comment-to-JSX-block strip. New `vocab_items_to_components()` renders V7 `vocabulary.yaml` as `<FlashcardDeck>` + `<VocabCard>`. `format_resources_for_mdx()` reads V7 `resources.yaml` `author/pages/description/role` fields (eliminates "by Unknown"). 4 dedicated test files. |

## Verifier predicate satisfied

`bash /tmp/post-merge-verify.sh` (sync main + run `assemble_mdx` on `curriculum/l2-uk-en/a1/my-morning/` + check 5 predicates against regenerated MDX):

```
PREDICATE_REPORT for starlight/src/content/docs/a1/my-morning.mdx:
  P1_ASSEMBLE_MDX=PASS
  P2_DIALOGUEBOX_count=2 (need >= 1)
  P3_FLASHCARD_OR_VOCABCARD_count=2 (need >= 1)
  P4_ACTIVITY_COMPONENT_count=17 (need >= 4)
  P5_BY_UNKNOWN_count=0 (need = 0)
  P5_NAMED_AUTHORS_count=5 (need >= 1)
GOAL_PREDICATE=SATISFIED
```

25,715 chars in the regenerated MDX vs. the previous session's manually-assembled 234-line broken artifact.

## Held items + dispositions

- **PR #1909** (writer-prompt-tune — `claude/writer-prompt-tune-2026-05-13`) — premise from 2026-05-13 midday bakeoff (citation parity + budget discipline + immersion long-UK-sentence rule). Likely fully SUPERSEDED by #1920's prompt restructure + #1928's phonetic IPA directive. **Recommend: close with reference to #1920 + #1930.**
- **PR #1915** (twopass YELLOW — `codex/pass2-only-contract-test-2026-05-13`) — premise from 2026-05-13 afternoon. Anchor preservation mechanism works (74/74 anchors round-tripped byte-identical), immersion outside band (32% vs 18-22 target). **Recommend: close** — wiki-obligations-manifest #1920 is now the cross-tab contract that Track B was groping toward.
- **Dependabot trio #1872 (astro 6.2→6.3.1), #1873 (@astrojs/starlight 0.38→0.39.2), #1874 (react 19.2.5→19.2.6)** — minor bumps from 2026-05-11. CI status not checked this session. **Recommend: review CI, merge if green.**

## Source artifacts in working tree (uncommitted, user decision pending)

5 modified + 5 untracked files at `curriculum/l2-uk-en/a1/my-morning/`:

```
 M activities.yaml (V7 writer output — 10 activities incl. observe + order, now parser-supported)
 M module.md (V7 writer output — 14 dialogue lines, 4 INJECT_ACTIVITY placeholders)
 M resources.yaml (V7 writer output — 3 textbook citations with author/pages/description/role)
 M vocabulary.yaml (V7 writer output — 20 entries with lemma/translation/pos/example)
 M starlight/src/content/docs/a1/my-morning.mdx (assembled output, 25,715 chars)
?? knowledge_packet.md, python_qg.json, wiki_manifest.json, writer_output.raw.md, writer_tool_calls.json
```

**Decision pending:** commit the 4 source yamls + the regenerated MDX as a single PR? They represent the first end-to-end-validated V7 a1/my-morning module. Or rebuild from scratch via `v7_build a1 my-morning` and commit the rebuild's output?

The build artifacts (`python_qg.json`, `writer_tool_calls.json`, `writer_output.raw.md`, `wiki_manifest.json`, `knowledge_packet.md`) are intermediate/telemetry. Per AGENTS.md pre-submit checklist these should NOT be in a PR — likely candidates for `.gitignore` if not already.

## Carry-over queue (priority-ordered — A1 focus per user directive)

| # | Item | State |
|---|---|---|
| **1** | **Bug d — write decision card `docs/decisions/2026-05-15-ulp-derived-student-aware-immersion.md`** ratifying the 2-PR split (learner-state V7 wiring → ULP cumulative-vocab immersion model). See "Architectural Finding" above | 📋 **P0 — biggest leverage on A1 pedagogy** |
| **2** | **Bug d / PR1 — learner-state V7 wiring + path fix + audit gate** | 📋 dispatch after decision card lands |
| **3** | **Bug d / PR2 — ULP-style cumulative-vocab-aware immersion model** | 📋 dispatch after PR1 lands |
| 4 | Bug c — multimedia resources search (#1932) — brief ready at `docs/dispatch-briefs/2026-05-14-multimedia-resources-search.md` | 📋 dispatch in parallel with bug d work (different file scope, no conflict) |
| 5 | Disposition PR #1909 (close as superseded by #1920 + #1928) | 📋 user decision |
| 6 | Disposition PR #1915 (close as YELLOW; premise predates wiki manifest) | 📋 user decision |
| 7 | Disposition dependabot trio (#1872 astro / #1873 starlight / #1874 react) — check CI, merge if green | 📋 |
| 8 | Commit-or-leave-dirty the 5 V7 source artifacts + regenerated MDX for a1/my-morning | 📋 user decision |
| 9 | **Rebuild a1/my-morning** end-to-end via `v7_build a1 my-morning` AFTER bug d ships — first true student-aware A1 module — user-run only per CLAUDE.md | 📋 P1 after bug d lands |
| 10 | Build a second A1 module end-to-end (post-graduation) to confirm assembler + learner-state generalize | 📋 deferred until bug d + module 1 graduate |
| 11 | Revisit Decision Card 2-REVISED (`docs/decisions/pending/2026-05-13-writer-split-by-tab.md`) | 📋 deferred |
| 12 | Per-track pilot strategy decision card (proposed but NOT written this session — user redirected to A1 focus first) | 📋 deferred until A1 graduates |
| 13 | #1908 Layered-harness audit (EPIC #1865 structural) | 📋 |
| 14 | #1905 Pipeline replay-mode regression suite (EPIC #1865 structural) | 📋 |
| 15 | #1896 Secret-leak prevention follow-ups | 📋 |
| 16 | #1933 /goal v2 wishlist (4 harness improvements) | 📋 filed this session |
| 17 | Pending Decision Cards: `2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-09-decision-graph-view.md`, `2026-05-06-multi-ui-channel-participation.md` | 📋 |

## /goal lessons (record for next session)

User invoked `/goal ship the V7 MDX rendering for a1/my-morning per the design docs` mid-session. The pattern worked for the ship outcome (PR landed, predicate verified) but burned ~30-40K context tokens on ~40 cycles waiting for a single 30-min dispatch. **Fit assessment:**

- /goal cadence assumes per-turn measurable predicate advancement (fix-N-tests, convert-N-callers, build-N-modules).
- Our task was "fire one dispatch + wait for merge" — predicate flat at NOT_SATISFIED for 50 turns, then flips to SATISFIED at the merge.
- The mismatch forced empty cycles.
- **One genuine win the /goal grammar unlocked**: Turn 11 — running `assemble_mdx` against the dispatch's IN-PROGRESS worktree code (before commit) confirmed GOAL_PREDICATE=SATISFIED ~25 min before PR merged. That early verification move would not have happened without the predicate framing.

**Codex `/goal` recommendation:** Codex doesn't have a headless `/goal` surface — only the in-REPL form. Use for sit-with-it interactive iteration (bakeoffs, prompt tuning), NOT for autonomous orchestration. Per `claude_extensions/rules/goal-driven-runs.md` already.

## Structural note (carry forward)

Previous session flagged Claude's "soft-pedal at load-bearing moments" pattern (DEFERRED clauses, menus, escape hatches). This session:

- Workflow violation when preparing PR #1927: switched branches in main project dir instead of worktree. User corrected mid-session in caps. Recovered by `git checkout main` + worktree. **Pattern to watch: ALWAYS `git worktree add -b ...`, never `git checkout -b` in main dir.**
- `/goal` cycle was a context-burn but did ship correct work. The early-worktree-verification at Turn 11 IS the kind of moment the previous handoff was warning about — but in a good direction (used the grammar to verify pre-merge correctness rather than waiting blind).

**Decision pending from last session:** Claude vs Codex as orchestrator. User raised it; not retracted. This session shipped 5 PRs cleanly via 4 dispatches + 1 inline-Claude regex fix; Codex was the executor on all 5. Codex-as-orchestrator hasn't been tested operationally yet — would require Codex to run dispatch + monitor + verify rather than just receive briefs.

## Predecessor brief

`docs/session-state/2026-05-13-night-wiki-obligations-e2e-brief.md` — set up the 4 bug-fix queue (#1921-1924) + flagged the first-e2e-build halt at python_qg. This session shipped all 4 bugs + the architectural assembler alignment + the bilingual landing page. The empirical proof of the wiki-obligations architecture (from the predecessor) extended: the rebuilt a1/my-morning now also exercises the full 4-tab render shape with all design components, not just wiki-content coverage.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". MD per #M-2 (ai→ai orchestrator-loadable). Opening action for next session: read this brief + check `gh pr list` (decisions pending on #1909, #1915, dependabot trio) + decide commit policy for a1/my-morning source artifacts.*
