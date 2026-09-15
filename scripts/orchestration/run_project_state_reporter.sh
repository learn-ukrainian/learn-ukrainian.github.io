#!/usr/bin/env bash
# Loopback POST wrapper for scripts/api/project_state_local.py (#7188).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -n "${LEARN_UKRAINIAN_PYTHON:-}" ]]; then
  PYTHON="$LEARN_UKRAINIAN_PYTHON"
elif [[ -n "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-}" ]]; then
  PYTHON="${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT}/.venv/bin/python"
else
  PYTHON="$REPO_ROOT/.venv/bin/python"
fi
if [[ ! -x "$PYTHON" ]]; then
  echo "project interpreter missing: $PYTHON (set LEARN_UKRAINIAN_PYTHON or LEARN_UKRAINIAN_PRIMARY_REPO_ROOT)" >&2
  exit 1
fi
exec "$PYTHON" "$REPO_ROOT/scripts/api/project_state_local.py" report
