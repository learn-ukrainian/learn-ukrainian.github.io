#!/usr/bin/env bash
# Loopback POST wrapper for scripts/api/project_state_local.py (#7188).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${LEARN_UKRAINIAN_PYTHON:-$REPO_ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="${HOME}/projects/learn-ukrainian/.venv/bin/python"
fi
exec "$PYTHON" "$REPO_ROOT/scripts/api/project_state_local.py" report
