# Codex dispatch brief — #1778 check_plan.py track-level plan handling

**Background:** `scripts/audit/check_plan.py` (added in #1765) expects module-level plans (e.g. `a1` with per-module `references[]`). It rejects track-level plans like `curriculum/l2-uk-en/plans/ruth.yaml` with `"No modules found for level ..."`.

Read full issue body via `gh issue view 1778`. Three options laid out — adopt **Option 1**: detect track-level vs module-level plans and apply different validation rules.

## Worktree

You start in `.worktrees/dispatch/codex/1778-check-plan-track-level/`. Do NOT `cd` out.

## Approach (Option 1 from issue)

Track-level plan schema (e.g. `ruth.yaml`) has top-level keys like `phases`, `linguistic_evolution`. Module-level plan has `modules[]` with `references[]`.

In `check_plan.py`:
1. Detect the plan type after YAML load:
   ```python
   if "modules" in plan_dict:
       plan_type = "module-level"
   elif "phases" in plan_dict or "linguistic_evolution" in plan_dict:
       plan_type = "track-level"
   else:
       plan_type = "unknown"
   ```
2. Branch validation:
   - module-level: existing logic (per-module `references[]` audit).
   - track-level: minimum sanity check — file parses as YAML, has at least one of the expected top-level keys. Don't audit module references because there are no modules.
   - unknown: clear error message identifying which keys ARE present so the user can disambiguate.

## Files

- `scripts/audit/check_plan.py` — add the type detector + branched validation.
- `tests/test_check_plan.py` (or wherever existing tests live — find via `grep -rln "check_plan" tests/`) — add coverage.

## Numbered steps

1. Verify worktree.
2. Read `scripts/audit/check_plan.py` end-to-end + look at sample track-level vs module-level YAML files (`curriculum/l2-uk-en/plans/ruth.yaml` for track-level; `curriculum/l2-uk-en/plans/a1.yaml` or similar for module-level).
3. Implement the detector + branched validation.
4. Tests:
   - `test_check_plan_accepts_module_level_plan` (existing happy path)
   - `test_check_plan_accepts_track_level_plan_ruth` — load ruth.yaml, expect exit 0.
   - `test_check_plan_clearly_rejects_unknown_schema` — synthetic file with neither shape; expect exit non-zero with informative message.
5. Smoke verify against the issue's reproducer:
   ```
   .venv/bin/python scripts/audit/check_plan.py curriculum/l2-uk-en/plans/ruth.yaml
   ```
   Expect exit 0 + "track-level plan validated" or similar message.
6. Run targeted tests + lint.
7. Commit:
   ```
   fix(audit): check_plan.py handles track-level plans (#1778)

   Adds plan-type detection (module-level vs track-level) before
   validation. Track-level plans (ruth.yaml, etc.) get a minimum-
   schema sanity check; module-level plans keep the existing
   references[] audit.

   Closes #1778
   Refs #1771, #1765 (the check_plan.py introduction)
   ```
8. Push + PR. Do NOT auto-merge.

## What NOT to do

- Do NOT move track-level plans to a different directory (the issue's Option 2). That breaks references everywhere.
- Do NOT validate track-level plan content beyond "parses as YAML + has expected top-level keys" — there's no defined schema for track-level yet, so don't over-constrain.
- Do NOT enable auto-merge.

## Acceptance criteria

- [ ] `check_plan.py` detects plan type without false positives.
- [ ] Track-level plan validation passes for `ruth.yaml` (and any other track-level plans in `curriculum/l2-uk-en/plans/`).
- [ ] Module-level plan validation unchanged — existing tests still pass.
- [ ] Unknown-shape input gets a clear, actionable error.
- [ ] At least 3 new tests.
