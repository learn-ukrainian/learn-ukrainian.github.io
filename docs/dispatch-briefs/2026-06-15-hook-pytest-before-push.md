# Dispatch — #1908 hook: #M-7 pytest-before-push guard (script + tests ONLY)

Push the recurring "#M-7 run pytest locally before pushing to MAIN" rule down to the
enforcement layer (it was violated 2026-05-13 despite being canonical). Two coordinated
hooks. **Pattern to mirror:** `agents_extensions/shared/hooks/guard-admin-merge.py` and
`guard-branch-switch-in-main.py` (PreToolUse Bash, stdin JSON `tool_input.command`,
`shlex` tokenize, exit 2 = block + stderr reason, exit 0 = allow). **Read both first.**

## CRITICAL scope constraint
**Write ONLY the two hook scripts + their tests. DO NOT edit `agents_extensions/shared/settings.json`**
— the orchestrator registers the hooks (serial, to avoid settings.json merge conflicts with
sibling hook PRs). DO NOT run the deploy script.

## Two hooks
1. `agents_extensions/shared/hooks/stamp-pytest.sh` — **PostToolUse(Bash)** stamper.
   Reads stdin JSON; if the executed command contained a real `pytest` invocation
   (`.venv/bin/python -m pytest` / `pytest ` / `dagger call pytest`), `touch` a marker
   `"${TMPDIR:-/tmp}/learn-uk-pytest.$(git branch --show-current).stamp"`. Fire-and-forget
   (always exit 0; never block). Mirror `tool-timing.sh` for the PostToolUse payload shape.
2. `agents_extensions/shared/hooks/guard-push-pytest.py` — **PreToolUse(Bash)** guard.
   Block (exit 2) iff ALL of:
   - the command is a `git push` to a remote (not `--dry-run`), AND
   - the **current branch is `main`** (the push updates main — feature-branch pushes go to
     PR CI which runs pytest, so only direct-to-main is guarded), AND
   - the diff being pushed (`git diff --name-only origin/main..HEAD`) contains a
     test-trigger path: `*.py`, `tests/`, `scripts/`, `curriculum/`,
     `agents_extensions/shared/rules/`, OR `.dagger/`, AND
   - the pytest marker for `main` is missing OR older than 10 minutes.
   Otherwise exit 0. **FAIL-OPEN** on any error (can't determine branch/diff/marker →
   allow; this is a discipline net, not a security guard — never block a legit push on a
   hook bug). Override: env `SKIP_PYTEST_HOOK=1` → allow. Quote-aware (`shlex`) so a
   `git commit -m "...git push..."` body is not a false match. Clear stderr reason naming
   the marker path + the override.

## #M-4 + steps
- Report `pytest`/`ruff` final lines raw.
1. Confirm worktree (`git status`). 2. Write the 2 hooks (chmod +x both). 3. Tests in
   `tests/test_guard_push_pytest.py` — load the .py hook via importlib (mirror
   `tests/test_guard_admin_merge.py`); monkeypatch branch/diff/marker; assert: push-to-main
   + test-trigger + stale marker → 2; fresh marker → 0; non-main branch → 0; non-push cmd
   → 0; `SKIP_PYTEST_HOOK=1` → 0; quoted-body → 0. Plus a bash smoke for the stamper.
4. `.venv/bin/python -m pytest tests/test_guard_push_pytest.py -q` green. 5. `.venv/bin/ruff check` clean.
6. Commit `feat(harness): #M-7 pytest-before-push guard hook (#1908)` + `X-Agent: codex/hook-pytest-push`.
7. `git push -u origin <branch>` + `gh pr create`. NO merge. NO settings.json edit.

## Acceptance
Direct push to main of a `.py`/tests change without a recent pytest → blocked (exit 2,
override documented). Feature-branch push → never blocked. Hook errors → fail-open. Tests green.
