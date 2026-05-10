# Codex brief — PR-B: pytest performance (torch reinstall + pip cache abstraction)

**Source review:** `reviews/2026-05-10/quorum-verdict.md` Tier 2.
**Predecessor:** PR-A (`codex-pr-a-ci-noise`) must be merged first; this branch should fork from a main that already has PR-A.
**Task ID:** `codex-pr-b-pytest-perf`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main` (after PR-A merges)

## Worktree

```
git worktree add -b codex-pr-b-pytest-perf .worktrees/codex-pr-b-pytest-perf origin/main
cd .worktrees/codex-pr-b-pytest-perf
```

(Use the dispatch-provided worktree; do NOT do another `git worktree add` inside it.)

## Context

`Test (pytest)` takes ~5 min on every PR. Two structural fixes (Codex + Gemini agreement on Tier 2):

1. **`ci.yml:308-317`** runs an unconditional torch + torchvision reinstall **with `--force-reinstall`** before every test cycle. `--force-reinstall` defeats the pip cache. Estimated ~2-3 min direct saving.
2. **`ci.yml:300-306`** uses a manual `actions/cache` block. Replace with `setup-python`'s `cache: 'pip'` parameter — cleaner abstraction, granular invalidation, less brittle.

## Two concrete edits

### Edit 1 — Drop `--force-reinstall` torch/torchvision step

`ci.yml:315-317` currently:

```yaml
.venv/bin/python -m pip install --no-deps --force-reinstall \
  --index-url https://download.pytorch.org/whl/cpu \
  torch==2.11.0 torchvision==0.26.0
```

**Decision needed**: is this step required at all? Check whether `requirements-lock.txt` already pins torch + torchvision at the cpu wheels. Run:

```
grep -E '^torch(vision)?==' requirements-lock.txt
```

- **If torch + torchvision are pinned in `requirements-lock.txt`** → the line at `ci.yml:313` (`pip install --no-deps -r requirements-lock.txt`) already installs them. The cpu-wheel index-url + force-reinstall is redundant. **Delete lines 315-317 entirely.**
- **If they're NOT in `requirements-lock.txt`** → keep the install but drop `--force-reinstall` (let pip respect the cache):

  ```yaml
  .venv/bin/python -m pip install --no-deps \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.11.0 torchvision==0.26.0
  ```

Quote `grep` output in the commit body so the decision is auditable.

### Edit 2 — Replace manual `actions/cache` with `cache: 'pip'`

`ci.yml:300-306` currently:

```yaml
- uses: actions/cache@27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5
  if: needs.changes.outputs.code == 'true'
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('requirements-lock.txt', 'pyproject.toml') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

(Note: PR-A already removed `requirements.txt` from `hashFiles`. If PR-A hasn't merged yet, do that part too in this PR.)

Replace this block with `cache: 'pip'` parameter on the existing `actions/setup-python` step. Find that step (likely a few lines above 300) and add:

```yaml
- uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
  with:
    python-version: '3.12'
    cache: 'pip'
    cache-dependency-path: |
      requirements-lock.txt
      pyproject.toml
```

Then DELETE the manual `actions/cache` block (lines 300-306). The setup-python step manages cache key + invalidation automatically.

Verify the path: `actions/setup-python`'s `cache: 'pip'` looks at `requirements*.txt`, `pyproject.toml`, etc. by default — `cache-dependency-path` overrides that to be explicit. Without `cache-dependency-path`, default behavior may try to find a `requirements.txt` (which doesn't exist in this repo); be explicit.

## Acceptance criteria

1. `git diff --stat` shows changes only in `.github/workflows/ci.yml`. ~10-15 LoC net.
2. **CI must run on this PR's branch.** When this PR opens, the `Test (pytest)` job must:
   - Still emit (required check name preserved)
   - Complete successfully (passes the test suite)
   - Show shorter wall-clock than the previous baseline. Quote the timing in the PR body: BEFORE (~4-5 min from recent merged PRs) vs AFTER (this PR's run time).
3. Cache hit rate visible in CI logs — first run after PR-B merges may be cold; subsequent PRs should show `Cache restored from key: ...` in setup-python step.
4. YAML still parses: `.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`.

## #M-4 evidence (commit body)

- `grep -E '^torch(vision)?==' requirements-lock.txt` raw output (drives the Edit 1 decision).
- `git diff` of the touched section.
- After PR opens, append PR comment with: BEFORE pytest wall-clock (last 3 merged PRs), AFTER pytest wall-clock (this PR), delta.

## Pre-submit checklist (AGENTS.md:11-26) — applies. 1 file, well under 20.

## Workflow

1. Worktree setup
2. Read `reviews/2026-05-10/quorum-verdict.md` for context
3. Run the `grep` for torch in requirements-lock.txt → make the Edit 1 decision
4. Apply Edit 1 + Edit 2
5. Run AC commands; capture #M-4 evidence
6. `git add .github/workflows/ci.yml`
7. `git commit -m "ci: drop torch force-reinstall + use setup-python pip cache"` with body containing grep evidence + diff
8. Push, `gh pr create` with title same as commit subject
9. Do NOT auto-merge.
