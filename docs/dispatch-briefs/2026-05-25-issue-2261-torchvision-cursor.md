# Dispatch brief — Issue #2261 torchvision 0.27.0 CI break

**Agent**: cursor (composer-2.5)
**Mode**: danger
**Effort**: medium
**Branch base**: `origin/main`
**Task ID**: `issue-2261-torchvision-fix-2026-05-25`

## Read first
- `gh issue view 2261` — has full CI evidence + the root cause analysis
- `requirements-lock.txt` line containing `torchvision==0.27.0`
- `.github/workflows/` for the CI step that installs CPU wheels explicitly

## Verifiable claims preamble (#M-4)
- "CI now passes" → quote `gh pr checks <N>` showing `Test (pytest)` green
- "wheel mismatch resolved" → quote the diff of `requirements-lock.txt` + any CI workflow edit
- "import works" → run `.venv/bin/python -c "import torchvision; print(torchvision.__version__)"` and quote output

## Background
Per the issue: CI installs `torch==2.11.0+cpu / torchvision==0.26.0+cpu` from `https://download.pytorch.org/whl/cpu` FIRST, then `pip install -r requirements-lock.txt` later replaces `torchvision` with the PyPI wheel (0.27.0, NOT the `+cpu` build). The PyPI wheel's C extension is incompatible → `RuntimeError: operator torchvision::nms does not exist`.

## Steps

1. `git worktree add -B fix/issue-2261-torchvision-cpu-wheel .worktrees/dispatch/cursor/issue-2261 origin/main && cd .worktrees/dispatch/cursor/issue-2261`
2. Pick ONE of two fixes — state which in the PR body:
   - **Option A (preferred — pin the +cpu build)**: change `requirements-lock.txt` to `torchvision==0.27.0+cpu` and reference the PyTorch CPU index in the install step (or via `--extra-index-url` in pip install). Verify CI re-installs the +cpu build.
   - **Option B (downgrade)**: pin `torchvision==0.26.0` in `requirements-lock.txt` until PyTorch ships a 0.27.0 CPU wheel on PyPI. Close PR #2226 (the dependabot bump) as wont-fix-until-upstream.
3. Run `dagger call pytest --source=.` locally OR `.venv/bin/python -m pytest tests/ -q` to verify imports pass.
4. Commit: `fix(deps): pin torchvision to CPU wheel to match torch (closes #2261)`
5. Push, open PR.
6. If dependabot PR #2226 is still open, close it with cross-ref to this PR.

## Stop conditions
- Option A discovers `torchvision==0.27.0+cpu` isn't published yet on PyTorch CPU index → fall back to Option B + file follow-up issue for re-bump when upstream lands.
- Other downstream imports (transformers, sentence_transformers) break under the chosen version → STOP and report; this may be a broader version-compat issue.

## Done criteria
PR URL + `gh pr checks <N>` showing all blocking green + raw output of the `python -c "import torchvision; ..."` quote.
