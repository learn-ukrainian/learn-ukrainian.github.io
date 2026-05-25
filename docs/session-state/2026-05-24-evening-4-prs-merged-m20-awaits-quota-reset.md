---
date: 2026-05-24 (evening continuation)
session: "Evening continuation of the daytime handoff. Three open PRs at handoff merged (#2262 codex runtime fixes, #2263 gemini ext-article backfill, #2264 workbook auto-inject fix). #2209 V7 MDX Tab 3 inline-aggregate assembler fix dispatched to codex (issue-2209-mdx-tab3-inline-2026-05-24), landed in 19.5min as PR #2265, merged. Net 4 PRs landed tonight, 5 issues fully closed (#2208, #2251, #2159, #2209 via auto-close; #2134, #2071 manually with cross-ref to #2262). m20 attempt #8 held for Claude weekly quota reset per user direction."
status: infra-shipping-m20-awaits-quota
main_sha: 0014318188
main_green: clean (review/review F7 advisory persists)
working_tree_dirty: pre-existing untracked carry-overs from prior sessions (audit reports, dispatch briefs, orchestrator-frictions.md, backfill_ext_articles.py, daytime handoff itself); 5 redundant 2026-05-23 dispatch briefs removed at session start (lint-cleaned versions on main via #2259)
prs_merged_this_session: ["#2262 codex runtime fixes (#2159 #2134 #2071 stdin tempfile + initial_response_timeout + needs_finalize)", "#2263 gemini ext-article-N backfill (closes #2251)", "#2264 writer-prompt INLINE/WORKBOOK split (closes #2208)", "#2265 MDX assembler inline-and-aggregate for Tab 3 (closes #2209)"]
prs_closed_this_session: []
issues_closed_this_session: ["#2208 via #2264", "#2251 via #2263", "#2159 via #2262 (auto-close)", "#2134 manually with cross-ref to #2262", "#2071 manually with cross-ref to #2262", "#2209 via #2265"]
issues_filed_this_session: []
active_dispatches: []
active_builds: []
m20_attempt_8: "HELD for Claude weekly quota reset. User answered AskUserQuestion 'Wait for weekly reset' — quota at 7% at daytime handoff, refresh tomorrow morning. Fire after reset signal."
headline_finding: "**Three pre-m20 infrastructure fixes shipped tonight (#2262 + #2264 + #2265) cleanly map to verify-before-promote checks 2/4/6.** PR #2264 fixes the writer-prompt side (INLINE/WORKBOOK split — closes #2208). PR #2265 fixes the assembler side (Tab 3 inline-and-aggregate — closes #2209). PR #2262 fixes 3 codex CLI runtime bugs that would have made future codex dispatches flakier. Net: m20 attempt #8 has the cleanest pipeline yet — when Claude weekly quota resets, fire `--writer claude-tools` and the writer/assembler should produce a P2-coherent module."
next_session_first_item: "1) Wait for user signal that Claude weekly quota has reset. 2) Fire `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer claude-tools --effort xhigh --worktree` with Monitor on JSONL events. 3) If python_qg fires plan_reference_match gate (#2257) on Grade 4 fabrication: implement Option B (hoist gate to pre-python_qg + extend ADR-008 correction message for 'remove resources.yaml entry by source_ref/chunk_id'). 4) If python_qg green + LLM dim review acceptable: 10-check verify-before-promote per #M-11 + docs/best-practices/v7-design-and-corpus.md Section 4 → promote as first V7 anchor under post-reset shape. 5) If #1969 (resources_search_attempted=0 regression from 2026-05-13) still bites: ship Option A pre-emit checklist patch. Otherwise close #1969 as obsolete — writer prompt has been substantially restructured since then."
---

# 2026-05-24 evening — 4 PRs merged, m20 awaits quota reset

## Session arc (compact)

Started from the daytime continuation handoff with 3 open PRs awaiting review. Sequence:

1. **Orient + merge the open queue.** Monitor API reported #2208 codex dispatch DONE; PR #2264 already opened with all blocking CI green. Reviewed diffs for #2264 + #2263 + #2262; all clean. Merged in order: #2264 (m20 unblocker first) → #2263 → #2262.
2. **Local main sync hiccups.** Fast-forward pull blocked twice: once by stale `.git/index.lock`, once by 5 untracked dispatch briefs (the same files that #2259 had lint-cleaned and committed to main). Removed both classes; pull succeeded. Post-merge hook pruned 10 stale local branches.
3. **Close auto-close-missed issues.** PR #2262 body listed "Closes #2159, #2134, #2071" but only #2159 auto-closed (GH only honors the first issue in the keyword footer). Manually closed #2134 and #2071 with cross-references.
4. **Asked user about m20 quota.** AskUserQuestion gave 4 options: fire claude-tools now (~30K from 7% remaining), wait for reset, substitute via deepseek-as-claude-backend, or pivot writer family. User picked "Wait for weekly reset" — m20 attempt #8 held.
5. **Dispatched #2209.** V7 MDX assembler Tab 3 inline-aggregate fix. Issue body well-scoped (single file + clear AC + named buggy line). Brief at `docs/dispatch-briefs/2026-05-24-issue-2209-mdx-assembler-tab3-inline-codex.md`. Fired to codex, danger mode, effort=medium, 60min hard-timeout, monitored via background poll on batch_state status file (single notification when terminal — per #M-8 the right signal for codex).
6. **#2209 landed clean.** Codex finished in 19.5min, opened PR #2265, all blocking CI green. Diff exactly matched the brief: filter dropped at `core.py:330`, `converters.py:yaml_activities_to_jsx` extended with optional `inline_cross_ref_ids` set, regression test in `tests/test_generate_mdx.py` covers 2+2 inline+workbook, the previously-bug-enshrining `tests/test_assemble_mdx_v7.py` was FLIPPED (per the orchestrator skill's adapter-bug discipline rule). Cross-ref text uses `_(see lesson)_` / `_(дивіться урок)_` italic markdown — codex pragmatically dropped the `§<section>` part of the brief since the converter doesn't have section context at render time; the simpler form is fine.
7. **Merged #2265.** Same local-branch-delete-blocked-by-worktree pattern as #2264 — workaround was `git worktree remove --force` then `git branch -D` then pull. Main now at `0014318188`.

## What's shipped tonight (4 PRs)

| PR | Commit / SHA at merge | Scope |
|---|---|---|
| #2264 | `c7fe321ee7` (squash) | `scripts/build/phases/linear-write.md` — INLINE/WORKBOOK split contract. Inline activities (4-6) carry `id` + matching `<!-- INJECT_ACTIVITY: ... -->` marker. Workbook activities (6-9) omit `id` and never get markers. "ONLY inline activities are injected" stated explicitly. Net: prevents the "10 inline / 0 workbook" anti-pattern that got m20 attempt #6 reverted at `944f4200e4`. |
| #2263 | gemini branch (squash) | 100+ wiki `.sources.yaml` files: backfill ext-article-N stubs with real titles + URLs. Pure data; no code. Closes #2251 (and supersedes #1960 which was closed as duplicate). |
| #2262 | codex branch (squash) | `scripts/agent_runtime/runner.py`, `errors.py`, `watchdog.py`, `scripts/delegate.py`, 6 files. Three runtime fixes: (a) stdin via temp file (closes #2159 — large prompts via PTY stdout + PIPE stdin broke at the runner level), (b) `initial_response_timeout` default 180s (closes #2071 — startup hangs with `response_chars=0` now die in 3min not 30-60min), (c) `needs_finalize` status for dirty danger worktree with 0 commits ahead (closes #2134 — orchestrator can salvage uncommitted work). |
| #2265 | `c136543323` (squash) | `scripts/generate_mdx/core.py:330` — drop the filter that stripped inline-injected activities from Tab 3. `scripts/generate_mdx/converters.py:yaml_activities_to_jsx` — optional `inline_cross_ref_ids: set[str]` param; inserts `_(see lesson)_` / `_(дивіться урок)_` italic line under the activity title for those IDs. Regression test in `tests/test_generate_mdx.py:150-219` covers 2 inline + 2 workbook; previously-bug-enshrining test at `tests/test_assemble_mdx_v7.py:123-134` FLIPPED to assert P2 inline-and-aggregate. Closes #2209. |

## What this unblocks for m20 attempt #8

The 10-check verify-before-promote list at `docs/best-practices/v7-design-and-corpus.md` Section 4 has three checks that tonight's fixes directly enable:

- **Check #2** (Tab 3 has activities or correct fallback) ← PR #2264 (writer-prompt side stops auto-promoting all to inline)
- **Check #4** (Inline-and-aggregate cross-refs appear per P2) ← PR #2265 (assembler stops stripping inline from Tab 3)
- **Check #6** (INLINE/WORKBOOK split respected, A1: ~4-6 / ~6-9) ← PR #2264

Other checks (#1 4-tab render, #3 corpus citations, #5 student-aware framing, #7 activity types per-level, #8 FlashcardDeck+VocabCards, #9 DialogueBox or `>` quotes, #10 IPA notation) remain writer-output-correctness checks that we can't prevent — they're caught at promote time, not pre-build.

The plan_reference_match gate (PR #2257) is still wired to catch Grade 4 fabrication if it re-appears in resources.yaml. If it fires at python_qg time on m20 attempt #8, F2-today (Option B: hoist gate to pre-python_qg + extend ADR-008 correction) is the next step.

## What's NOT done

- **m20 attempt #8.** Held per user direction. Fire after weekly quota reset (per daytime handoff: 7% at session start, refresh "tomorrow morning"). User-signaled or quota-checked.
- **#2261 torchvision 0.27.0 CI break.** Defensive infra; no impact unless someone tries to bump torchvision. Not dispatched.
- **#1969 resources_search_attempted=0 regression.** Originally filed 2026-05-13 against build #4. Writer prompt has been substantially restructured since (PRs #2260, #2264 today; PR #2257 plan_reference_match gate; PR #2255 cursor-tools wiring). Verify if still happening on m20 attempt #8 outcome before dispatching the Option A pre-emit checklist patch — may be already-fixed by the structural rewrites.
- **#2210 V7 learner-state vocabulary drift.** Investigation+design task, not a clean dispatch. Needs orchestrator judgment before brief-writing.
- **Other 24 codex / 4 cursor / 4 gemini / 3 orchestrator labeled issues.** Backlog; addressable after m20 anchor ships.

## State at handoff

- **Main**: `0014318188` (tonight's 4 PRs on top of `a492cf2206`).
- **Open PRs**: 0.
- **Active dispatches**: 0.
- **Active builds**: 0.
- **Working tree**: same pre-existing untracked carry-overs as at daytime handoff (audit reports + dispatch briefs from this session and earlier + `docs/orchestrator-frictions.md` + `scripts/wiki/backfill_ext_articles.py` + the daytime handoff file itself). Not from tonight's work. Not blocking.
- **Claude weekly quota**: presumably still ~7% remaining (no Claude dispatches tonight; only orchestrator interactive turns). Awaiting reset signal.
- **Codex weekly**: abundant per daytime handoff ("reset last night per user").
- **Gemini**: unmetered.

## Tomorrow's first action — DO THIS

```bash
# Step 0: confirm quota reset (user signal OR check Claude usage)
# Step 1: fire m20 attempt #8
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning \
  --writer claude-tools --effort xhigh --worktree 2>&1 \
  | grep --line-buffered -E '^\{"event"|^Traceback|Error|FAILED|REJECT|module_done|module_failed|phase_done|writer_end_gate|review_score'

# Step 2: if python_qg fires plan_reference_match (Grade 4 fabrication caught):
#   implement Option B (pre-python_qg gate + ADR-008 correction) before re-firing.
# Step 3: if python_qg green + LLM dim review acceptable:
#   10-check verify-before-promote per docs/best-practices/v7-design-and-corpus.md Section 4
#   then `scripts/sync/promote_module.py --latest --level a1 --slug my-morning`
# Step 4: if #1969 still bites:
#   patch linear-write.md per #1969 Option A (pre-emit checklist, ~25 LOC)
#   otherwise close #1969 as obsolete.
```

Full session arc + commits + monitoring patterns above. Tonight's contribution: shrink the pre-m20 gap from 3 PRs + 1 inline aggregate bug → 0 PRs + clean assembler. m20 attempt #8 is the next ship-or-iterate signal.
