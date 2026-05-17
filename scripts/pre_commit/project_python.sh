#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

python=".venv/bin/python"
if [[ ! -x "$python" ]]; then
  common_dir="$(git rev-parse --git-common-dir)"
  python="$(cd "$common_dir/.." && pwd)/.venv/bin/python"
fi

if [[ ! -x "$python" ]]; then
  echo "[project-python] ERROR: project Python not found at .venv/bin/python" >&2
  echo "[project-python]        or at the parent of git common dir" >&2
  exit 127
fi

exec "$python" "$@"
