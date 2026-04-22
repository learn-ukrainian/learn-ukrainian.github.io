# Codex Brief — #1405 CI Infrastructure Red

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1405
**Task ID:** `codex-1405-ci-red`
**Worktree:** `.worktrees/codex-1405-ci-red`
**Branch:** `codex/codex-1405-ci-red`
**Effort:** medium (mostly mechanical fixes)

## Why this matters

Two PRs today (#1402, #1393) needed `--admin` override to merge purely because of pre-existing CI red. That bypass is a process risk — every time we admin-merge we erode the CI gate. Fix the underlying red so future PRs merge clean.

## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/codex-1405-ci-red`. Do NOT create a feature branch in the main checkout. Setup:

    git worktree add -b codex/codex-1405-ci-red .worktrees/codex-1405-ci-red
    cd .worktrees/codex-1405-ci-red
    # do work, commit, push

## Hard prohibitions (read this twice)

1. **DO NOT MERGE the PR yourself.** Open it only. The user / next Claude session reviews + merges. This is the rule that the 2026-04-22 #1403 incident exists for.
2. **DO NOT use `gh pr merge`, `gh pr review --approve`, or `--admin` for any reason.**
3. **DO NOT branch in the main checkout.**
4. **DO NOT touch unrelated files.** Resist scope creep — this issue is CI workflow + config files only, NOT code changes in `scripts/`.
5. **DO NOT bypass the rebase/merge by force-pushing to origin/main.**
6. If you find yourself wanting to do any of (1)–(5), STOP and write a comment on issue #1405 instead.

## Acceptance criteria

### AC-1 — `jsonschema` installed in CI for audit-importing workflows

Affected jobs: `Curriculum Plans → Validate Plan vs Config`, `Schema JSON Syntax`, `Test (pytest)`.

Failure: `ModuleNotFoundError: No module named 'jsonschema'` when importing through `scripts/audit/checks/meta_validator.py`.

Fix path:
- Find the workflow file(s) — likely `.github/workflows/curriculum-plans.yml` or similar
- Locate the pip install step
- Add `jsonschema` to the install list, OR install from a requirements file that already pins it (`requirements.txt` / `requirements-lock.txt` / `requirements-dev.txt`). Whichever is closer to the existing pattern.
- Verify by running the offending workflow logic locally if possible.

### AC-2 — gitleaks job decision

Failure: gitleaks v8.x requires a license key for org/private use. Two options:

**Option A** (preferred per Codex's #1400 review): Migrate the gitleaks JOB (not pre-commit) to `trufflesecurity/trufflehog` action. Pre-commit can stay on gitleaks (local use is unrestricted in v8.x).

**Option B**: Add `GITLEAKS_LICENSE` GitHub Secret + reference in workflow. But this requires the user to obtain a license — flag this as a separate user action and pick Option A.

Pick Option A. Make sure trufflehog config covers the same .gitleaks.toml allowlist patterns (Algolia public key, *.lock files).

### AC-3 — `.pre-commit-config.yaml` yamllint clean

Failures (from PR #1393 CI logs):
- 49:121 line too long (131 > 120)
- 68:121 line too long (225 > 120)
- 79:121 line too long (369 > 120)
- 68:163 syntax error: mapping values not allowed here

Fix path:
- Read `.pre-commit-config.yaml` lines 49, 68, 79
- Wrap long lines using YAML folded scalars (`>-`) or YAML literal scalars (`|`) where appropriate
- Fix the syntax error at line 68 (probably an unquoted value with `:` in it)
- Verify locally: `yamllint .pre-commit-config.yaml`

### AC-4 — Quality Gates (radon)

Failure unknown without log inspection. Likely accumulated complexity above threshold.

Fix path:
- Run the radon job locally to see what's flagged
- If it's 1-2 functions: refactor them (favor small extracts; do NOT rewrite logic)
- If it's many functions: bump the threshold modestly (document why in commit message) — this is a fallback only

### AC-5 — Verify all required PR checks pass on a no-op PR

After landing AC-1 through AC-4:
- Open a no-op test PR (touch a comment in a low-risk file, e.g., add a blank line to `docs/best-practices/ci-health.md` if you create it)
- Confirm ALL required checks pass
- Then close the test PR (don't merge)
- Document the green-baseline state in `docs/best-practices/ci-health.md` so the next regression is visible

### AC-6 — Adversarial review

Before opening the final PR for #1405:
- Run `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude "Adversarial review of #1405 CI red fix. Read the diff. Look for: (1) bypasses that hide rather than fix the red (e.g., disabling a check vs fixing the dep), (2) license/legal issues with trufflehog migration, (3) yamllint fix that semantically changes the pre-commit config, (4) radon threshold bump masking a real complexity issue." --task-id 1405-review`
- Address findings. Document any rejected feedback in the PR body with rationale.

## Reference

- Issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1405
- Previous handoff: `docs/session-state/2026-04-22-afternoon-ops-infra-pass.md`
- Related: #1400 (partial CI fix — root-scripts + 1 ruff)
- Related: #1394 (git hygiene, separately)

## Workflow

1. Create worktree (per worktree instructions above)
2. Work through AC-1 → AC-5 in order; each AC is its own commit
3. Run AC-6 adversarial review
4. Push branch
5. Open PR with title `fix(ci): repair pre-existing red — jsonschema, gitleaks, yamllint, radon (#1405)` and body summarizing what landed per AC
6. STOP. Do not merge. Notify completion via the dispatch result.

## Done when

PR opened, all 6 ACs documented in PR body, adversarial review noted, dispatch reports `done`.
