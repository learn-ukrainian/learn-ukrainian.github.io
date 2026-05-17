#!/usr/bin/env bash
#
# Pre-push hook: full GHA-replay pytest via Dagger.
#
# Invoked by pre-commit framework (stage=pre-push) when the push touches
# scripts/, tests/, .dagger/, or any .py file. The file filter is set in
# .pre-commit-config.yaml (id: dagger-pytest), so this script just runs
# unconditionally when called.
#
# Behavior:
#   - If `dagger` is not installed: WARN and exit 0 (allow push). CI
#     remains the safety net; we don't punish devs who haven't installed
#     Dagger yet.
#   - If `dagger` is installed: run `dagger call pytest --source=.`.
#     Exit non-zero on test failure (blocks push). Exit 0 on success.
#
# Why this exists:
#   MEMORY.md #M-7 — "PYTEST LOCALLY BEFORE PUSH TO MAIN" — encodes the
#   lesson that pre-commit's ruff-only checks are insufficient. We've
#   merged red commits to main by skipping local pytest before push.
#   This hook makes the slow-but-safe path automatic so it can't be
#   forgotten.
#
# Bypass:
#   `git push --no-verify`  — only when you're sure (e.g. you know the
#   path filter caught a non-Python change that triggered the hook).
#
# Reference: PR #TBD (added 2026-05-17).

set -u

# Find repo root (works inside main checkout and inside worktrees).
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "[dagger-pytest] ERROR: not inside a git repository" >&2
  exit 1
fi
cd "$REPO_ROOT" || exit 1

# Graceful fallback: Dagger not installed.
if ! command -v dagger >/dev/null 2>&1; then
  echo "[dagger-pytest] WARN: 'dagger' not found in PATH; skipping local pytest replay."
  echo "[dagger-pytest]       CI will run the full pytest suite remotely."
  echo "[dagger-pytest]       Install Dagger to enable this hook: https://docs.dagger.io/install/"
  exit 0
fi

# Sanity-check the Dagger module exists. If .dagger/ is missing, the
# project's GHA replay isn't set up — skip with a warning rather than
# fail-loop.
if [[ ! -d ".dagger" ]]; then
  echo "[dagger-pytest] WARN: .dagger/ directory missing; cannot run GHA replay locally."
  echo "[dagger-pytest]       Skipping (CI will catch failures)."
  exit 0
fi

# Graceful fallback: Docker daemon not reachable. Dagger needs Docker
# (or compatible like OrbStack/colima) to execute pipelines. If the
# daemon is down, we can't run pytest — but that's an INFRASTRUCTURE
# gap, not a test failure. WARN and allow the push; CI is the safety net.
if ! docker version >/dev/null 2>&1; then
  echo "[dagger-pytest] WARN: Docker daemon not reachable; skipping local pytest replay."
  echo "[dagger-pytest]       Start Docker / OrbStack / Colima and retry, or push --no-verify."
  echo "[dagger-pytest]       CI will run the full pytest suite remotely."
  exit 0
fi

echo "[dagger-pytest] Running full pytest via Dagger (~2-3 min warm)..."
echo "[dagger-pytest] Bypass with 'git push --no-verify' if you must."
echo

# Run Dagger and stream output. Capture exit code; preserve failures.
DAGGER_NO_NAG=1 dagger call pytest --source=. 2>&1
rc=$?

echo
if [[ $rc -eq 0 ]]; then
  echo "[dagger-pytest] ✅ pytest passed via Dagger — push proceeding."
else
  echo "[dagger-pytest] ❌ pytest FAILED (exit $rc) — push BLOCKED."
  echo "[dagger-pytest] Fix the failing tests or bypass with 'git push --no-verify'."
fi
exit $rc
