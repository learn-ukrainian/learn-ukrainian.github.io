# Gemini brief — fix stale `test_normal_api_launch_uses_workers_and_uvicorn_limits`

**Issue:** N/A (orchestrator-driven, blocking main + all open PRs).
**Task ID:** `gemini-fix-api-launch-test`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b gemini-fix-api-launch-test .worktrees/gemini-fix-api-launch-test origin/main
cd .worktrees/gemini-fix-api-launch-test
```

## Why this is blocking

`tests/test_api_resilience.py::test_normal_api_launch_uses_workers_and_uvicorn_limits` has been failing on **main** since commit `6d81e694b1` (late evening 2026-05-09 — *"api auto-reload"*). That commit changed `package.json` `scripts.api` and `scripts.api:bg` from production-style (`--workers 2 --limit-concurrency 32 --timeout-keep-alive 5`) to dev-style (`--reload`), but did not update the test. Result: `Test (pytest)` blocking-fails on every open PR (currently #1849 and #1850), even though those PRs don't touch any Python.

Verified at handoff time:

```
$ python -c "import json; s=json.load(open('package.json'))['scripts']; print(s['api']); print(s['api:bg']); print(s['api:reload'])"
.venv/bin/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --reload --log-config scripts/api/logging.json 2>&1 | tee logs/api.log
.venv/bin/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --reload --log-config scripts/api/logging.json >> logs/api.log 2>&1 & echo "PID: $!" | tee -a logs/api.log
npm run api
```

The current contract is: `api` runs uvicorn with `--reload`; `api:bg` runs the same in background; `api:reload` is now an alias (`npm run api`). There is no production launch script anymore.

## Fix

Update `tests/test_api_resilience.py::test_normal_api_launch_uses_workers_and_uvicorn_limits` (currently lines ~103-114) to match the current contract:

```python
def test_normal_api_launch_uses_uvicorn_with_reload():
    """package.json scripts.api / scripts.api:bg launch uvicorn in dev-reload mode.

    Pinned 2026-05-10 after commit 6d81e694b1 ("api auto-reload"). The previous
    contract (--workers 2 --limit-concurrency 32 --timeout-keep-alive 5) was a
    production-style launcher; the project does not run a production API and
    has standardized on --reload for the localhost:8765 dev server.
    """
    scripts = json.loads((ROOT / "package.json").read_text())["scripts"]

    for name in ("api", "api:bg"):
        command = scripts[name]
        assert ".venv/bin/python -m uvicorn" in command
        assert "scripts.api.main:app" in command
        assert "--host 0.0.0.0" in command
        assert "--port 8765" in command
        assert "--reload" in command
        assert "--log-config scripts/api/logging.json" in command

    # api:reload is now an alias of api (legacy name preserved for muscle memory).
    assert scripts["api:reload"] == "npm run api"
```

Rename the function from `test_normal_api_launch_uses_workers_and_uvicorn_limits` to `test_normal_api_launch_uses_uvicorn_with_reload` so the name matches the new contract. Update any imports / `pytest -k` patterns in the repo if they reference the old name (`grep -rn 'test_normal_api_launch_uses_workers_and_uvicorn_limits' tests/ scripts/ docs/` — should be zero matches outside the test file itself, but verify).

## Acceptance criteria

1. `.venv/bin/pytest tests/test_api_resilience.py::test_normal_api_launch_uses_uvicorn_with_reload -xvs` passes.
2. `.venv/bin/pytest tests/test_api_resilience.py -x` — all tests in file pass (no other test depended on the old name).
3. `.venv/bin/ruff check tests/test_api_resilience.py` clean.
4. **Boy-Scout check**: `grep -rn 'workers 2\|limit-concurrency\|timeout-keep-alive' tests/ scripts/ docs/` — verify zero stale references to the dropped flags. If any docs still describe the production launcher, update or remove those mentions in the same commit (likely none, but check).

## #M-4 evidence (commit body)

- Raw output of `python -c "import json; s=json.load(open('package.json'))['scripts']; print(s['api'])"` (current contract).
- Raw output of `pytest tests/test_api_resilience.py -v` AFTER fix.
- Raw output of `git log --oneline 6d81e694b1 -1` to anchor the regression to its source commit.

## Pre-submit checklist (AGENTS.md:11-26) — applies. Diff should be ≤ 30 lines, 1 file.

## Workflow

1. Worktree setup
2. Edit `tests/test_api_resilience.py` per Fix section
3. Run AC commands; capture #M-4 evidence
4. `git add tests/test_api_resilience.py`
5. `git commit -m "test(api): pin --reload launch contract (post 6d81e694b1)"` with body containing evidence
6. `git push -u origin gemini-fix-api-launch-test`
7. `gh pr create` — title same, body references this brief and the api auto-reload commit
8. Do NOT auto-merge. Tag the PR body: *"Unblocks pytest CI on all open PRs (currently #1849, #1850)."*
