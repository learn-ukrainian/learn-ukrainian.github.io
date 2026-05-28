---
date: 2026-05-27
session: "Part 10 of the multi-day m20 V7 anchor sprint. Pt 9 hardened the pipeline (4 PRs landed: #2366, #2367, #2370, #2371) and produced a clean writer output blocked by gate-vs-prompt drift in wiki_coverage. Pt 10 closed that drift via PR #2371 (per-item gate matching + writer-side wiki_coverage_required_items block) and re-fired Phase 2a. **The hardening DEMONSTRABLY works**: required-vocab coverage jumped from 1/7 to 6/7 in one refire; all hardening gates PASS; the lesson reads clean. **Single remaining failure: word_count 1058 vs 1104 min** (45 words under, 4.1% under tolerance). **Path B dispatched as PR #2372** — small writer-prompt tweak for stricter per-section prose-only minimums + wiki_coverage rendering hint that vocab table entry alone is NOT coverage. CI in flight at session close."
status: path-b-pr-2372-ci-running
main_sha: 20ab69072d (post PR #2371)
main_green: clean
working_tree_dirty: 7 dispatch briefs + Pt 9 + Pt 10 + Pt 10 addendum untracked
session_close: 2026-05-27 evening
---

# 2026-05-27 — Part 10: hardening validated, single gate gap

**Read the TL;DR. Read the empirical comparison table. Then the next-step path.**

## TL;DR

**The 4-PR hardening WORKS.** Empirical proof from one Phase 2a re-fire:

- **Required-vocab coverage**: 1/7 → **6/7** (up from `сніданок`-only to `зарядка`, `сніданок`, `раненько`, `швиденько`, `завжди`, `ніколи` — only `вода` still missing).
- **All hardening gates pass**: `chunk_context_for_all_refs`, `published_quote_for_publishable_refs`, `textbook_quote_fidelity`, `register_consistency`, `formatting_standards`, `vesum_verified`, `russianisms_strict`, `surzhyk_clean`, `calques_clean`, `paronym_clean`, `engagement_floor`, `l2_exposure_floor`, `component_props`, `activity_schema`, `plan_reference_match`, `citations_resolve`, `ai_slop_clean`.
- **0 tool theatre violations**. 8 MCP tool calls (`verify_words` ×2, others). Writer ran 286s.
- **Salad is gone**: lesson reads in single voice, grammar terms throughout, no scaffolding labels, no Grade 1 textbook blockquotes.

**Single failure**: `word_count` gate. **1058 vs 1104 min** (target 1200, 8% tolerance below). 45 words short. Raw `wc -w` is 1335 — the gap is because the gate doesn't count callouts / tables / dialogue boxes, where this lesson invests its content density.

**Path B (chosen by user)** is the unblock: tiny writer-prompt tweak emphasizing minimum-prose-words-per-section + explicit reminder for items the writer dropped (`вода`). Estimated 30 min round-trip.

## What's at 20ab69072d (main right now)

Pt 9 closed with main at `6c49ee86ab`. Pt 10 work:

- **PR #2371 merged**: wiki_coverage per-item gate matching + writer-side `wiki_coverage_required_items` block. Resolves the gate-vs-prompt drift Pt 9 surfaced. Main now `20ab69072d`.
- **Phase 2a re-fired** under fully hardened pipeline. Worktree `.worktrees/builds/a1-my-morning-20260527-185032/`. Output is in worktree's `curriculum/l2-uk-en/a1/my-morning/module.md`.

## Empirical comparison — Pt 9 refire (worktree 163310) vs Pt 10 refire (worktree 185032)

| Metric | Pt 9 refire | Pt 10 refire | Δ |
|---|---|---|---|
| Writer phase duration | 346s | 286s | -60s |
| Tool calls total | 6 | 8 | +2 |
| Tool theatre violations | 0 | 0 | = |
| Sections with CoT | 4/4 | 4/4 | = |
| `сніданок` (step-5 vocab) | ✓ | ✓ | = |
| `вода` (step-5 vocab) | ❌ | ❌ | = |
| `зарядка` (step-5 vocab) | ❌ | ✓ | +1 |
| `раненько` (step-5 vocab) | ❌ | ✓ | +1 |
| `швиденько` (step-5 vocab) | ❌ | ✓ | +1 |
| `завжди` (step-5 vocab) | ❌ | ✓ | +1 |
| `ніколи` (step-5 vocab) | ❌ | ✓ | +1 |
| Step-5 vocab coverage | 1/7 | 6/7 | +5 items |
| Step-4 content (дивлюся + л) | ✓ partial | ✓ (2×, 3×) | better |
| `chunk_context_for_all_refs` | PASS | PASS | = |
| `published_quote_for_publishable_refs` | PASS | PASS | = |
| `textbook_quote_fidelity` | PASS | PASS | = |
| `wiki_coverage` block on writer prompt | NO | YES (PR #2371) | new |
| **Wiki coverage step-N gate** | **FAIL on `Крок N:` literal-match drift** | **Did not run (build halted at word_count)** | gate fixed but unverified end-to-end |
| `word_count` | passed (~1100+) | **FAIL: 1058 < 1104** | regressed |
| `plan_sections` (overall) | passed | passed (sections under min but no missing headings) | ~= |
| Raw `wc -w` total words | 1335 | 1335 | = |

**Key insight**: the lessons are the SAME raw size (~1335 words by `wc -w`) but Pt 10 codex distributed more content into structured elements (tables, callouts, dialogue boxes) the gate doesn't count, and less into bare prose. Net: word_count gate fell off the cliff.

This is consistent with adding the `wiki_coverage_required_items` block to the writer prompt — codex sees the explicit per-obligation requirements and integrates them into structured forms (vocabulary tables, model sentences) rather than expanding prose. That's pedagogically correct behavior but trips the count.

## The 4-PR hardening — full record

| PR | Files | What | Status |
|---|---|---|---|
| **#2366** | `linear-write.md` + `linear-review-dim.md` + prompt-pinning tests | 6 `#R-` writer rules (`#R-SINGLE-VOICE-A1`, `#R-AUDIENCE-LANGUAGE-A1`, `#R-NO-CHILDREN-PRIMARY-QUOTES`, `#R-NO-SCAFFOLDING-LEAKS`, `#R-GRAMMAR-TERMS-A1`, `#R-CLEAN-TABLES`) + matching reviewer REJECT criteria + inline resolution of the Grade 1 plan-conflict by softening `#R-TEXTBOOK-30W` for Grade 1-3 grounding | ✅ Merged |
| **#2367** | `linear_pipeline.py` + `prev_next.py` + tests | HARD `verify_quote` gate (catches m20 `Кнак` typo class) + prev/next null-over-wrong link safety | ✅ Merged (after follow-up commit added missing tests) |
| **#2370** | `linear_pipeline.py` + `linear-write.md` + tests | `textbook_grounding` split into `chunk_context_for_all_refs` + `published_quote_for_publishable_refs` with `is_publishable_ref` helper (multilingual grade parsing) | ✅ Merged |
| **#2371** | `wiki_coverage_gate.py` + `linear_pipeline.py` + `prompt_builder.py` + `linear-write.md` + tests | Per-item gate matching (normalize `Крок N:` + `[S\d+]` markers, extract vocab + examples, match each item) + writer-side `wiki_coverage_required_items` block surfacing per-obligation requirements | ✅ Merged |

## Brain-pick session that drove the design

Saved at `audit/2026-05-27-codex-brain-pick-m20/turn-{1,2,3}-*.md`. Three turns via `ab send-codex-ui --thread 019e6944-d4c8-7da0-853f-8676ddf526b0`.

Codex's core framings:
- **"Visible compliance tokens"** — gates rewarded local-knob-hitting (one callout for engagement_floor, 15 dialogue boxes for l2_exposure_floor, prose mass for word_count) rather than integrated teaching. The salad is the SUM of separate compliances each locally rational.
- **The wiki_coverage gate's literal-label matching** was the most dangerous "rewards row satisfaction over lesson flow" pattern — resolved by PR #2371.
- **The textbook_grounding gate's Grade 1 conflict** — resolved by PR #2370 (codex independently arrived at the split during PR #2366 work).
- **The "rendered-lesson pass"** before emission (strip comments + read as learner + delete off-audience content) is the residual fix. Brain-pick turn 2 Q5: ship as (a) writer-prompt rule + (b) regex hard gate. STILL QUEUED for Pt 11+.

## Path B brief — what's firing next

Small writer-prompt tweak. Target file: `scripts/build/phases/linear-write.md`. Specifically the `## Tone and immersion (mandatory)` section that already has the `#R-WORD-COUNT-FLOOR` or equivalent — find it and tighten.

Two surgical changes:

1. **Strengthen per-section minimum-prose-words** language:
   - Current: probably says "section budgets 270-330 each"
   - New: add "**Prose words only.** Callouts, dialogue boxes, table cells, and code blocks do NOT count toward the per-section budget. If your section relies on a table/callout for the teaching, you must STILL include ≥270 words of explanatory prose AROUND the structure. The `plan_sections` gate counts prose; structural elements are bonus."

2. **`wiki_coverage_required_items` block rendering enhancement** in `prompt_builder.py`:
   - When rendering the block, include explicit hint: "**Every item below must appear at least once in module.md prose, in a model sentence or definition. A vocab table entry alone is not coverage** — the writer must demonstrate usage in a learner-readable sentence."
   - This addresses the `вода` miss and any future miss where writer cites the item in a table but doesn't model it in prose.

This is small enough to do as a single dispatch (gemini default per #M0, mechanical prompt-near-code) OR inline (15-20 LOC of prompt + render function change). Brain-pick turn 3 also gave us a concrete §Діалоги target shape we can use for visual diff during review.

## What to do first when you wake up

1. **Read the produced Pt 10 module.md**: `cat .worktrees/builds/a1-my-morning-20260527-185032/curriculum/l2-uk-en/a1/my-morning/module.md`. Verify the lesson reads coherently, then approve Path B as outlined above.
2. **Fire Path B**. Dispatch shape: gemini, brief in `docs/dispatch-briefs/2026-05-27-path-b-writer-prompt-section-floor-gemini.md` (not yet drafted — Pt 10 work).
3. **After Path B merges, re-fire Phase 2a (third refire)**. Expected outcome: word_count clears, `вода` lands, lesson ships clean. If it does, this becomes the m20 the user wanted.
4. **If Path B Phase 2a still has issues**, examine the new gaps and iterate ONCE more. Cap at 4 Phase 2a refires under the hardened pipeline before pivoting (so far 2 refires used).

## Issues filed today (all open)

- **#2368**: `/api/delegate/active` route handler returns empty while `/api/orient` works. Low priority.
- **#2369**: PR #2367 scope-creep evaluation (`_contract_yaml` vocabulary fields + `linear-write.md` dialogue-gloss "block-bottom" sentence). Comment added with read-only investigation — DialogueBox component does NOT support "block-bottom"; sentence revertable.

## Build worktrees on disk (per #M-10 forensic-keep)

```
.worktrees/builds/a1-my-morning-20260527-073037/  pre-hardening
.worktrees/builds/a1-my-morning-20260527-073705/  pre-hardening
.worktrees/builds/a1-my-morning-20260527-161219/  Pt 9 mid-hardening (stale)
.worktrees/builds/a1-my-morning-20260527-163310/  ⭐ Pt 9 clean writer output (gate-blocked on wiki_coverage)
.worktrees/builds/a1-my-morning-20260527-163621/  Pt 9 mid-hardening (stale)
.worktrees/builds/a1-my-morning-20260527-163804/  Pt 9 killed mid-build
.worktrees/builds/a1-my-morning-20260527-185032/  ⭐⭐ Pt 10 — closer to ship; 6/7 vocab + word_count short
```

Keep both `163310` and `185032` — they're the forensic record of Pt 9 + Pt 10. Once Path B's refire ships clean, cleanup all of these in a single pass.

## Tasks state at end of Pt 10

```
✅ #1, #2, #3, #4, #5, #10, #12, #13 — Phase 1 hardening + brain-pick + Phase 2a writer refires + wiki_coverage cleanup
🔄 NEW: Path B writer-prompt tweak (Pt 10 → Pt 11 transition)
⏸ #6 Phase 3a cursor brain-pick — still queued (codex must work fully first per user direction; almost there)
⏸ #7 Phase 3b cursor-tools m20 build — deferred until cursor brain-pick + kubedojo integration lands
⏸ #8 Phase 4 gemini-via-agy-UI m20 — deferred until shape (a) productized or shape (b) hand-relay run
⏸ #9 Phase 5 decision card rewrite — pending Phase 2a clean ship
⏸ #11 Brain-pick follow-up slate Q5-Q6 (rendered-lesson rule + scaffolding regex gate + whitelist cleanup) — pending after m20 ships
```

## Key lesson — encode in MEMORY when there's budget

**Gate-vs-prompt drift caught 3 times in one session (PR #2370 textbook_grounding, PR #2371 wiki_coverage, Pt 10 word_count via structural-density shift).** The pattern: writer prompt change shifts WHAT the writer produces; gate keeps measuring the OLD shape; gap appears. Whenever a writer prompt rule changes the output structure (more tables, fewer blockquotes, no scaffolding labels), audit gates that depend on those structures.

The corollary: **structural-density shift trips word_count.** When writer is told to use clean tables + callouts + dialogue boxes (the new shape from PR #2366 `#R-CLEAN-TABLES`), the prose density per section drops. The gate counts prose only. So either: (a) writer prompt explicitly emphasizes minimum prose floor per section, OR (b) gate counts structural content density too. Path B picks (a) because it's smaller. Future PR may consider (b) for robustness.

End of 2026-05-27 Pt 10. The hardening works. One small nudge from clean ship.

---

## Session-close addendum (2026-05-27 evening) — Path B in flight

After Pt 10 main body was written, Path B was dispatched + the PR opened. Capturing in-flight state here so resumption is clean.

### Path B dispatch

- **Brief**: `docs/dispatch-briefs/2026-05-27-path-b-writer-prompt-section-floor-gemini.md`
- **Task ID**: `path-b-writer-prompt-section-floor-2026-05-27`
- **Agent**: gemini, model `gemini-3.1-pro-preview`, mode danger
- **Branch**: `gemini/path-b-writer-prompt-section-floor-2026-05-27`
- **Base SHA**: `20ab69072d`
- **Worktree**: `.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27/`

### Path B PR

- **PR #2372**: `feat(writer-prompt): per-section prose floor + wiki_coverage prose-demonstration hint`
- **CI state at session close**: 5 of ~16 checks still running, 0 failures so far.

### What the next orchestrator does on resume

1. **Check PR #2372 final CI**: `gh pr view 2372 --json mergeStateStatus,statusCheckRollup`. If all green and `mergeStateStatus` is `CLEAN` or `UNSTABLE` (advisory CANCELLED only), proceed to step 2.
2. **Adversarial review of PR #2372 diff**:
   - Confirm `#R-PROSE-FLOOR-A1` (or whatever rule name was used) is in `linear-write.md` with the key phrases: "Prose words only", "structural elements are *bonus content density*", "Reach the prose floor BEFORE you optimize".
   - Confirm `_render_wiki_coverage_required_items` in `scripts/build/prompt_builder.py` got a prepended coverage-rule hint with "vocab table entry alone is NOT coverage" (or similar phrasing).
   - Scope check: only `scripts/build/phases/linear-write.md`, `scripts/build/prompt_builder.py`, `tests/test_writer_prompt_*.py`, possibly `tests/audit/test_wiki_coverage*.py`. No scope creep into gates, reviewer rubric, curriculum/.
3. **Merge** if clean: `gh pr merge 2372 --squash --delete-branch`. (Local branch-delete may fail because of the worktree; that's the same harmless issue seen on PRs #2366, #2367, #2370, #2371 — clean up via `git worktree remove` after.)
4. **Sync local main**: `git fetch origin main --quiet && git pull --ff-only origin main`.
5. **Fire the third Phase 2a refire**:
   ```bash
   .venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer codex-tools --worktree > /tmp/v7-build-phase2a-third-refire.log 2>&1 &
   ```
   Capture PID via `echo $!` + `disown`. Set Monitor on the log file with the JSONL event filter (see Pt 10 main body for the regex pattern that worked).
6. **When build completes**, read `module.md` from the new worktree (`ls -t .worktrees/builds/a1-my-morning-*` will show it). Expected:
   - `word_count` ≥ 1104 (gate threshold)
   - All step-5 vocab covered including `вода` this time
   - All hardening gates still PASS
   - Lesson reads as one coherent A1 lesson (no salad)
7. **If clean**: this is the m20 user has been waiting for. Promote to main as a new commit replacing the current published `curriculum/l2-uk-en/a1/my-morning/module.md` + accompanying YAML files. PR title like `feat(a1): re-ship my-morning under fully hardened pipeline`. Compare to current shipped version (PR #2364) in PR body to show the salad → clean transformation.
8. **If still failing**: diagnose. Two iterations max under hardened pipeline before pivoting to investigate writer-prompt issue more deeply. So far Pt 9 + Pt 10 refires (2 used). Path B refire = 3rd. Cap at 4 before escalation.

### Untracked artifacts at session close

```
docs/session-state/2026-05-27-pt9-hardening-works-wiki-gate-blocks.md
docs/session-state/2026-05-27-pt10-phase2a-validates-only-word-count-gap.md  (this file)
docs/dispatch-briefs/2026-05-27-v7-prompt-hardening-codex.md
docs/dispatch-briefs/2026-05-27-verify-quote-gate-gemini.md
docs/dispatch-briefs/2026-05-27-verify-quote-tests-gemini-followup.md
docs/dispatch-briefs/2026-05-27-textbook-grounding-gate-split-gemini.md
docs/dispatch-briefs/2026-05-27-wiki-coverage-manifest-cleanup-gemini.md
docs/dispatch-briefs/2026-05-27-path-b-writer-prompt-section-floor-gemini.md
docs/dispatch-briefs/2026-05-27-agy-ui-bridge-codex.md  (from earlier)
audit/2026-05-27-codex-brain-pick-m20/turn-1-findings.md
audit/2026-05-27-codex-brain-pick-m20/turn-2-followups.md
audit/2026-05-27-codex-brain-pick-m20/turn-3-target-shape-dialogue.md
```

Bundle these into a single docs PR after Phase 2a refire ships clean. Title: `docs(session-state): 2026-05-27 Pt 9-10 — pipeline hardening + Phase 2a empirical validation`. Body: cite the 5 hardening PRs (#2366, #2367, #2370, #2371, #2372 when merged) + the empirical 1/7 → 6/7 vocab-coverage proof.

### Tasks state at session close

```
✅ #1, #2, #3, #4, #5, #10, #12, #13 — Phase 1 hardening + brain-pick + 2 Phase 2a refires + wiki_coverage cleanup
🔄 #14 — Path B in flight (PR #2372 CI running at session close)
⏸ #6 Phase 3a cursor brain-pick — codex must work fully first (almost there)
⏸ #7 Phase 3b cursor-tools m20 build — deferred behind cursor brain-pick + kubedojo integration
⏸ #8 Phase 4 gemini-via-agy-UI m20 — deferred
⏸ #9 Phase 5 decision card rewrite — pending Phase 2a clean ship
⏸ #11 Brain-pick follow-up slate Q5-Q6 (rendered-lesson rule + scaffolding regex gate + whitelist cleanup) — pending after m20 ships
```

### Issues open at session close

- **#2368** `/api/delegate/active` route handler regression — low priority workaround via `/api/orient`
- **#2369** PR #2367 scope-creep evaluation (`_contract_yaml` vocabulary fields + `linear-write.md` dialogue-gloss "block-bottom" sentence) — comment added with read-only evidence; sentence revertable

### One-paragraph context dump for fresh-session resume

If the next session is a fresh Claude Code instance: the m20 V7 anchor was shipped as PR #2364 (Pt 8) but post-ship review revealed 6 substantive failure modes (salad/kaleidoscope register, UK metalanguage to learner, scaffolding leak `Крок 5:`, hallucinated proper noun `Кнак`, folksy "is a thing" paraphrase, Grade 1 textbook blockquote in adult content). The user corrected the framing: stop manual patching, fix the pipeline so the workflow itself produces clean lessons. Pt 9-10 landed 4 hardening PRs (#2366 + #2367 + #2370 + #2371), did a 3-turn codex brain-pick session that produced the design proposals, and validated the hardening with two Phase 2a refires. The Pt 10 refire (worktree `a1-my-morning-20260527-185032/`) is nearly shippable — all hardening gates PASS, vocab coverage 6/7, single failure is `word_count` 45 words short due to structural-density shift. PR #2372 (Path B) is the small writer-prompt tweak to close that gap. After it merges + third refire + read, the m20 should ship as the user-acceptable A1 anchor.

End of session close addendum.
