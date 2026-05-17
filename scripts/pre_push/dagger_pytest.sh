#!/usr/bin/env bash
#
# Full GHA-replay pytest via Dagger — MANUAL invocation only.
#
# Status: this script was originally a pre-push pre-commit hook (id:
# dagger-pytest in .pre-commit-config.yaml). Removed from the pre-push
# stage 2026-05-17 because Dagger's cache_volume design accumulated pip
# wheels every cold run (was 30 GB/run pre-#2088, ~6 GB/run after the
# .venv mount filter), and the disk creep filled the SSD to 99% twice
# in 12 hours. CI's `Test (pytest)` workflow is the canonical pre-merge
# gate; this script is kept in-tree for ad-hoc GHA-replay debugging of
# a CI-only failure that needs reproduction locally.
#
# Usage:
#   bash scripts/pre_push/dagger_pytest.sh
#
# Behavior:
#   - If `dagger` is not installed: WARN and exit 0.
#   - If `dagger` is installed: run `dagger call pytest --source=.`.
#     Exit non-zero on test failure. Exit 0 on success.
#
# Cost reminder:
#   Each cold run rebuilds the `learn-ukrainian-pip` cache_volume to
#   ~6 GB. Use `docker volume prune -f` (after stopping
#   `dagger-engine-v*`) periodically if you invoke this often.
#
# Why MEMORY.md #M-7 still applies:
#   The hook automation is gone but the obligation is not — run pytest
#   locally before push when editing .py, scripts/, tests/, .dagger/,
#   or hardcoded test fixtures. For most pushes, the faster path is
#   `.venv/bin/python -m pytest <targeted-paths>` (5s vs Dagger's
#   3-5 min). Use this script only when you suspect a CI-only diff.
#
# Reference: PR #TBD (de-hooked 2026-05-17).

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
