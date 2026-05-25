# Issue #2209 — MDX assembler: stop filtering inline activities out of Tab 3

**Date**: 2026-05-24 (evening)
**Agent**: codex
**Mode**: danger
**Effort**: medium
**Wall budget**: 30-40 min

## Why this matters NOW

We are about to fire m20 attempt #8 via `--writer claude-tools` once the Claude weekly quota resets. The just-merged PR #2264 unblocks the writer side (inline/workbook split in the prompt is correct). But the MDX assembler at `scripts/generate_mdx/core.py:330-333` actively contradicts the V7 design contract on the downstream side — it strips inline-injected activities from Tab 3 (Вправи).

Result: even if writer produces a clean 4-6 inline + 6-9 workbook split per V7 P2, the rendered MDX will be missing the inline activities from the consolidated practice tab. That's a P2 violation: "inline-and-aggregate is intentional" (panel-confirmed; see `docs/best-practices/v7-design-and-corpus.md`).

Fix this BEFORE m20 attempt #8 so the assembler doesn't undo the writer's correct output.

## The exact code site

```python
# scripts/generate_mdx/core.py:330-344
tab3_activities = [
    activity for activity in (yaml_activities or [])
    if str(getattr(activity, 'id', '')) not in injected_activity_ids
]
if tab3_activities:
    activities_content = yaml_activities_to_jsx(tab3_activities, is_ukrainian_forced)
elif yaml_activities and injected_activity_ids:
    no_workbook_msg = (
        "Немає окремих вправ у робочому зошиті; дивіться вкладку «Урок»."
        if is_ukrainian_forced
        else "No workbook activities for this module; see the Lesson tab."
    )
    activities_content = f"*{no_workbook_msg}*"
elif activity_plans:
    activities_content = _activity_plans_to_jsx(activity_plans)
```

The first list-comp filters out any activity whose `id` was inline-injected. That filter is the bug. The "no workbook" fallback message becomes dead code once we keep inline activities, but it's there as defensive handling.

## What V7 P2 requires

Per `docs/best-practices/v7-design-and-corpus.md`:
- **Inline activities**: sparse lesson interruptions woven into prose (Tab 1 / Урок). Carry `id` + matching `<!-- INJECT_ACTIVITY: ... -->` marker.
- **Workbook activities**: majority of practice; live in Tab 3 (Вправи). `id` optional.
- **P2 inline-and-aggregate**: inline activities ALSO appear in Tab 3, annotated with a cross-reference back to the lesson section. Learner gets BOTH the woven-into-prose experience AND a consolidated practice view.

## What to do (mechanically)

1. Drop the filter. Tab 3 renders ALL activities in `yaml_activities`.
2. For activities that ARE in `injected_activity_ids`, render them with a small cross-reference annotation. Two acceptable approaches; pick whichever is cleanest for `yaml_activities_to_jsx`:
   - **Option A**: extend the renderer to accept an `inline_cross_ref: bool` flag per activity, render a "(see lesson)" / "(дивіться урок)" annotation under the activity title. EN/UK variants.
   - **Option B**: pre-process the activity objects, mutate a `notes`/`subtitle`/equivalent field to prepend "(see lesson) " / "(дивіться урок) ". Same EN/UK variants.
3. Workbook-only activities keep rendering as today. Visual diff for workbook entries = zero.
4. The `"No workbook activities..."` fallback becomes effectively unreachable once inline-also-appears-in-Tab-3 is wired. Keep it as defensive code OR remove it cleanly with the activity-plans branch reflowed — either is fine; don't over-engineer.

## Read first (in order)

1. `gh issue view 2209` — issue body + AC list.
2. `docs/best-practices/v7-design-and-corpus.md` — find the P2 section explicitly. Quote the relevant lines in the PR body.
3. `scripts/generate_mdx/core.py` — read the full `_assemble_v7_tabs` function (or equivalent containing function around line 330). Understand `injected_activity_ids` provenance from `_inject_inline_activities` above.
4. `scripts/generate_mdx/core.py` — locate `yaml_activities_to_jsx`. This is where Option A would extend; Option B mutates before calling it.
5. `tests/test_generate_mdx.py`, `tests/test_generate_mdx_v7_resources_vocab.py`, `tests/test_generate_mdx_parsers.py` — existing assembler test patterns to mirror.

## Acceptance criteria (verbatim from issue)

- Inline activities render both inline and in Tab 3
- Cross-reference text appears for inline-rendered activities (in Tab 3)
- Tab 3 no longer filters out injected activity IDs
- Regression test added for P2 inline-and-aggregate behavior

## Regression test (REQUIRED)

Add at minimum one new test (extend `tests/test_generate_mdx.py` or new `tests/test_generate_mdx_v7_tab3_inline_aggregate.py`):

- Setup: a v7 module with 2 inline activities (id=act-1, act-2) + 2 workbook activities (no id or id=act-3, act-4 without INJECT marker).
- Assert: rendered MDX Tab 3 (Вправи) section contains references to all 4 activities (act-1, act-2, act-3, act-4).
- Assert: rendered MDX Tab 3 entries for act-1 + act-2 contain the cross-reference annotation (substring match on "see lesson" OR "дивіться урок" depending on `is_ukrainian_forced`).
- Bonus: assert the inline `<!-- INJECT_ACTIVITY: act-1 -->` markers in Tab 1 still resolve correctly (no regression on `_inject_inline_activities`).

## REQUIRED steps (numbered)

1. From project root: `git fetch origin && git worktree add -b fix/issue-2209-mdx-tab3-inline .worktrees/dispatch/codex/issue-2209-mdx-tab3-inline-2026-05-24 origin/main`
2. `cd .worktrees/dispatch/codex/issue-2209-mdx-tab3-inline-2026-05-24 && ln -s ../../../../.venv .venv`
3. Read the 5 files in "Read first" list. Quote the V7 P2 section line range in the PR body.
4. Apply the fix to `scripts/generate_mdx/core.py`. After edit, `git diff scripts/generate_mdx/core.py | head -60` — verify visually.
5. Add the regression test per above. Run targeted: `.venv/bin/pytest tests/test_generate_mdx.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_generate_mdx_parsers.py -v 2>&1 | tail -25`. ALL must pass. NEW test must be in the pass list.
6. Run wider: `.venv/bin/pytest tests/test_generate_mdx*.py -v 2>&1 | tail -10`. Capture final summary line raw.
7. Ruff: `.venv/bin/ruff check scripts/generate_mdx/core.py tests/test_generate_mdx*.py 2>&1`. Must be clean.
8. Commit conventional: `fix(mdx-assembler): keep inline activities in Tab 3 with cross-ref (closes #2209)`. Include in body: the V7 P2 quote + the line numbers of the diff.
9. `git push -u origin fix/issue-2209-mdx-tab3-inline`
10. `gh pr create --base main --title "fix(mdx-assembler): inline-and-aggregate for Tab 3 (#2209)" --body "..."` — body includes acceptance-criteria checklist with each item checked.
11. `gh pr checks <NEW_PR> --watch --interval 15` until green. (F7 `review / review` advisory will fail — that's the known Gemini-Dispatch auth issue; OK to ignore per project policy.)
12. Report final state. **NO auto-merge.** Orchestrator merges after review.

## Verifiable claims (#M-4 anti-fabrication)

| Claim | Evidence required (command + cwd + raw output) |
|---|---|
| "Filter removed at core.py:330" | `git diff scripts/generate_mdx/core.py \| head -40` raw |
| "Cross-reference annotation added for inline activities" | Diff hunk showing the annotation logic raw |
| "Tests pass" | Final pytest summary line raw `N passed in M.MMs` |
| "New regression test exists" | `grep -n 'test_.*inline.*aggregate\\|test_.*tab3_inline' tests/test_generate_mdx*.py` raw |
| "Ruff clean" | `ruff check` final line raw |
| "PR opened" | `gh pr view --json url` raw URL line |
| "CI green (blocking)" | `gh pr checks <N> --json bucket` showing only review/review in fail bucket |

## What success unblocks

Once #2209 lands:
- m20 attempt #8 via claude-tools can fire (after weekly quota reset) without the Tab 3 inline-aggregate regression undoing the writer's correct output.
- P2 contract is honored end-to-end (writer prompt PR #2260 + writer prompt #2264 + assembler #2209 form a coherent set).
- The 10-check verify-before-promote per #M-11 can pass the "Tab 3 contains both inline and workbook activities" check.

## Out of scope (do NOT do)

- Do NOT touch the writer prompt (`scripts/build/phases/linear-write.md`) — #2208 just landed and is correct.
- Do NOT change `_inject_inline_activities` — the inline injection itself is correct.
- Do NOT change `activities.yaml` schema.
- Do NOT mutate `id` fields or `INJECT_ACTIVITY` markers.
- Do NOT remove the "No workbook activities..." fallback message wholesale — keep it as defensive code unless reflowing reads more cleanly (judgment call; small diff either way).
