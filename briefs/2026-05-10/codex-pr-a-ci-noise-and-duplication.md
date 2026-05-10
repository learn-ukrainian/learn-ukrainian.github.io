# Codex brief — PR-A: CI noise + trigger duplication

**Source review:** `reviews/2026-05-10/quorum-verdict.md` (Codex + Gemini + Claude judge — read this first; it has the file:line refs verified).
**Task ID:** `codex-pr-a-ci-noise`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b codex-pr-a-ci-noise .worktrees/codex-pr-a-ci-noise origin/main
cd .worktrees/codex-pr-a-ci-noise
```

(The dispatch CLI provides a worktree at `.worktrees/dispatch/codex/pr-a-ci-noise/` — work there, do NOT do another `git worktree add` inside it. The Gemini v5/v6 banner brief had this bug; don't repeat.)

## Critical context

- **Only `Test (pytest)` is a required check on main** (verified via `gh pr checks NNNN --required` — returns only `Test (pytest)`). All other checks are reported but not branch-protection-blocking. So you have wide latitude to rename / drop / restructure other checks; ONLY `Test (pytest)` name + always-emit guarantee must be preserved.
- The `Test (pytest)` always-emit guarantee comes from `ci.yml:320`'s `if: !cancelled() && (needs.lint.result == 'success' || needs.lint.result == 'skipped')`. **Do NOT touch this condition.**
- Duplication root cause confirmed: `gh pr checks 1853 --required` shows `Test (pytest)` twice (one fail / one pass) — once for push event, once for PR event. The `push:` triggers without `branches:` filter cause the same workflow to fire twice on every feature-branch commit.

## Five concrete edits

### Edit 1 — `ci.yml`: restrict push trigger to main

`ci.yml:6-26` — add `branches: [main]` under `push:`. Keep paths filter as-is (it's still useful for limiting which main commits trigger CI).

```yaml
on:
  push:
    branches: [main]    # NEW LINE — restricts push trigger
    paths:
      - '.github/workflows/ci.yml'
      ...               # existing paths unchanged
  pull_request:
    paths: ...          # unchanged — feature-branch commits go through pull_request only
```

### Edit 2 — `validate-yaml.yml`: same restriction

`validate-yaml.yml:6-16` — add `branches: [main]` under `push:`. Same pattern as Edit 1.

### Edit 3 — `rules-deployment-check.yml`: same restriction

`rules-deployment-check.yml:6-26` — add `branches: [main]` under `push:`. Same pattern.

### Edit 4 — `gemini-dispatch.yml`: drop the `debugger` job

`gemini-dispatch.yml:25-43` — delete the `debugger` job entirely (`if:` is `${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}` → always false unless an env var is explicitly set, so always emits a skipped check). If you want to keep debug ability, fold the print step into the start of the `dispatch` job behind the same `if:` condition (Gemini's suggestion). For PR-A keep it minimal: just delete the job.

### Edit 5 — `gemini-dispatch.yml`: drop review-comment / review-submit triggers

`gemini-dispatch.yml:4-9` — delete the `pull_request_review_comment` and `pull_request_review` trigger blocks. Keep `pull_request: { types: [opened] }`, `issues: { types: [opened, reopened] }`, `issue_comment: { types: [created] }`. The `@gemini-cli` predicate at line 49 always rejects normal review comments, so all 6 downstream jobs (review, triage, invoke, plan-execute, fallthrough) cascade-skip on every review activity — pure noise for zero signal.

### Edit 6 — `ci.yml`: cache key cleanup

`ci.yml:304` — drop `requirements.txt` from `hashFiles(...)`. Keep `requirements-lock.txt` and `pyproject.toml`. (The repo doesn't have a `requirements.txt` file; verify with `ls requirements*` before edit.)

```yaml
key: pip-${{ runner.os }}-${{ hashFiles('requirements-lock.txt', 'pyproject.toml') }}
```

### CodeQL `actions` lane

The CodeQL config is in repo settings (default-setup), NOT in `.github/workflows/`. **Do not** create a CodeQL YAML file to override — that would require switching from default-setup to advanced-setup, which is out of scope for PR-A. Instead, **add a single line to the PR body** noting: *"Reviewer (you/maintainer) — please disable the `actions` language in repo Settings → Code security → CodeQL default setup. This is a UI action; cannot be done via PR."* Same pattern as the #1762 CodeQL UI dismissal pending action.

## Acceptance criteria

1. `git diff --stat` shows changes ONLY in: `.github/workflows/ci.yml`, `.github/workflows/validate-yaml.yml`, `.github/workflows/rules-deployment-check.yml`, `.github/workflows/gemini-dispatch.yml`. No other files modified. Total LoC: ~25-30.
2. **YAML still parses** for all 4 workflows: `.venv/bin/python -c "import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/ci.yml', '.github/workflows/validate-yaml.yml', '.github/workflows/rules-deployment-check.yml', '.github/workflows/gemini-dispatch.yml']]"` succeeds.
3. **`Test (pytest)` job survives.** `grep -A1 'name: Test (pytest)' .github/workflows/ci.yml` still shows the job. `grep -B1 -A4 "if:.*!cancelled()" .github/workflows/ci.yml` still shows the always-emit guard.
4. **`@gemini-cli` command path survives.** `grep "@gemini-cli" .github/workflows/gemini-dispatch.yml` still returns the predicate at line ~49. The `dispatch` job + the 4 callable workflow jobs (`review`, `triage`, `invoke`, `plan-execute`) are still wired.
5. **PR opens green.** Once PR-A opens, its own CI run should show: NO duplicate check entries, NO `debugger` skipped row, NO cascade of 4 skipped Gemini downstream jobs from a non-`@gemini-cli` event. Quote `gh pr checks <new-PR-number>` output in the PR body to demonstrate.

## #M-4 evidence (commit body)

- Raw output of `gh pr checks 1853 --required` BEFORE this PR (shows current duplication: 2× pytest entries).
- Raw output of `ls requirements*` (shows file existence reality).
- Raw output of `grep -c '@gemini-cli\|pull_request_review' .github/workflows/gemini-dispatch.yml` BEFORE and AFTER (numerically demonstrates the trigger drops).
- After PR opens, append PR comment with `gh pr checks <new-PR-number>` raw output showing the noise reduction.

## Pre-submit checklist (AGENTS.md:11-26) — applies. 4 files changed, well under 20.

## Workflow

1. Worktree setup (use the dispatch-provided worktree, no nested `git worktree add`)
2. Read `reviews/2026-05-10/quorum-verdict.md` for full context
3. Apply edits 1-6 (skip CodeQL — covered as a PR-body note instead)
4. Run AC commands; capture #M-4 evidence
5. `git add` named files only
6. `git commit -m "ci: kill trigger duplication + skipped-check noise"` with body containing evidence blocks + a "Closes" reference to the quorum verdict file
7. `git push -u origin codex-pr-a-ci-noise`
8. `gh pr create` with title same as commit subject, body that:
   - References `reviews/2026-05-10/quorum-verdict.md`
   - Includes the BEFORE/AFTER `gh pr checks` evidence
   - Has a single line at the bottom: *"Reviewer manual action: disable CodeQL `actions` language in Settings → Code security → Default setup."*
9. Do NOT auto-merge.
