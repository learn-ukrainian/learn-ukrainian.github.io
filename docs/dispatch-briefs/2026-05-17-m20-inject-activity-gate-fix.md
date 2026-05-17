# Dispatch brief — m20 inject_activity_ids gate: fail on unused activities (#2096)

## Root cause (verified in m20 build #17 python_qg.json)

`scripts/build/linear_pipeline.py:_inject_activity_gate` returns `passed: true` whenever `missing` is empty, even if every single activity in `activities.yaml` is `unused` (i.e., never referenced from `module.md` via `<!-- INJECT_ACTIVITY: act-N -->` markers).

m20 build #17 evidence:
- `inject_activity_ids.passed = true` (no missing IDs)
- `inject_activity_ids.unused = ["act-1", "act-2", ..., "act-10"]` (every activity unused)
- `l2_exposure_floor.observed.uk_tab3_activities = 0` (counter at `linear_pipeline.py:6056` uses `_INJECT_RE.findall(text)` — zero INJECT markers → zero "tab3 activities")
- Build fails `l2_exposure_floor` even though `activities.yaml` has 10 well-formed activities.

The auto-correction `_apply_activity_id_inserts` (line 3801) is the right shape — it appends `<!-- INJECT_ACTIVITY: id -->` markers for every unused activity — but it only runs when the gate FAILS (`PIPELINE_INSERT_GATES` correction path at line 3628-3630). With the gate always passing, auto-injection never triggers.

## Verifiable claims this work produces

| Claim | Evidence |
|---|---|
| `_inject_activity_gate` now fails when `unused` is non-empty | `git diff main scripts/build/linear_pipeline.py` showing the predicate change |
| Regression test added | `git diff main tests/build/test_linear_pipeline.py` |
| Tests pass | `.venv/bin/pytest tests/build/test_linear_pipeline.py -k inject_activity` raw output |
| Pre-commit hooks pass | `git push` output |
| PR opened | `gh pr view --json url` raw URL |

## Worktree setup (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-inject-gate-fix -b fix/m20-inject-activity-gate-fail-on-unused origin/main
cd .worktrees/m20-inject-gate-fix
```

## The patch

Target: `scripts/build/linear_pipeline.py` — function `_inject_activity_gate` around line 6420.

Read the function first to confirm exact wording. The change shape:

**OLD logic (current — incorrect):**
- `passed` is true iff `missing` is empty.

**NEW logic:**
- `passed` is true iff BOTH `missing` is empty AND `unused` is empty.
- When `unused` is non-empty (but `missing` is empty), `passed` becomes false with a reason like `"unused_activities_not_injected"`. The PIPELINE_INSERT_GATES correction path then triggers `_apply_activity_id_inserts` (already exists at line 3801) which appends the missing markers. After auto-correction, the gate re-runs and now passes because `unused` becomes empty.

Verify that `inject_activity_ids` is in `PIPELINE_INSERT_GATES` (it should be — that's the existing infrastructure). If not, add it.

## Regression test

Add to `tests/build/test_linear_pipeline.py`:

A test that:
1. Constructs `text` with zero INJECT markers + `activities` list with 3 activities.
2. Calls `_inject_activity_gate(text, activities)`.
3. Asserts `passed is False`.
4. Asserts `unused == ["act-1", "act-2", "act-3"]` (or whatever IDs the test uses).
5. Asserts the reason mentions "unused_activities" or similar.

Also a happy-path test:
1. Constructs `text` with `<!-- INJECT_ACTIVITY: act-1 -->` for each activity.
2. Asserts `passed is True` and `unused == []`.

## Verification

```bash
# venv symlinked into worktree by delegate.py
# Quote raw output in the PR body for each:
.venv/bin/pytest tests/build/test_linear_pipeline.py -k inject_activity -v
git diff --stat main
git diff --name-only main
# Expected: scripts/build/linear_pipeline.py + tests/build/test_linear_pipeline.py
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pre_commit run --files scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
```

## Commit + PR

```bash
# venv symlinked into worktree by delegate.py
git add scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
git commit -m "fix(audit): inject_activity_ids gate fails when activities are unused (#2096)

The gate's predicate \`passed iff missing.empty\` ignored the \`unused\`
list. m20 build #17 evidence: every one of 10 activities was unused
(activities.yaml had act-1..act-10, module.md had zero
<!-- INJECT_ACTIVITY: --> markers) but the gate reported passed=true.

Downstream effect: \`l2_exposure_floor\` counted uk_tab3_activities=0
because the INJECT markers were never auto-appended by
_apply_activity_id_inserts (which only triggers on gate failure via
PIPELINE_INSERT_GATES).

This patch flips the predicate to \`passed iff missing.empty AND
unused.empty\`. The PIPELINE_INSERT_GATES correction path then triggers
the existing auto-injection on unused IDs, satisfying l2_exposure_floor
on the next gate pass.

Regression test covers both directions:
- All unused → gate fails with explicit reason
- All injected → gate passes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Codex <noreply@anthropic.com>"
git push -u origin fix/m20-inject-activity-gate-fail-on-unused
gh pr create --title "fix(audit): inject_activity_ids gate fails when activities are unused (#2096)" --body "$(cat <<'EOF'
## Summary

m20 build #17 (post-PR #2094) showed:
- inject_activity_ids gate passed (no missing IDs)
- BUT all 10 activities in activities.yaml were marked \`unused\` (zero INJECT_ACTIVITY markers in module.md)
- l2_exposure_floor failed counting \`uk_tab3_activities = 0\`

Root cause: \`_inject_activity_gate\` only fails on missing IDs, ignoring the \`unused\` list. The auto-correction in \`_apply_activity_id_inserts\` exists and is wired through PIPELINE_INSERT_GATES, but never triggers because the gate never fails.

This patch makes the predicate strict (both missing AND unused must be empty for pass). Auto-correction then runs on gate-fail and appends \`<!-- INJECT_ACTIVITY: --\>\` markers for unused IDs, unblocking l2_exposure_floor downstream.

## Test plan

- [x] Regression test: gate fails when all activities unused
- [x] Regression test: gate passes when all activities injected
- [ ] After merge: m20 rebuild expected to pass l2_exposure_floor's uk_tab3_activities check

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Out of scope (do NOT)

- Do NOT touch the auto-injection function `_apply_activity_id_inserts` — already works correctly.
- Do NOT touch `_l2_exposure_floor_gate` — the counter is correct; the upstream gate is what was broken.
- Do NOT modify any other file.

## Anti-fabrication

- Quote raw pytest output (the `N passed in Ms` summary line) in PR body.
- If `PIPELINE_INSERT_GATES` doesn't already include `inject_activity_ids`, the fix needs to add it. Quote a grep showing what's there before/after.
- NO auto-merge; orchestrator merges after diff review.
