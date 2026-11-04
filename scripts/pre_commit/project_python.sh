#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# The machinery roots configuration's interpreter (LEARN_UKRAINIAN_PYTHON, #12681;
# scripts/common/repo_root.py) wins when set, and an unusable value refuses rather
# than falling back. Kept inline, not sourced: the pre-push gate fingerprints this
# file alone, and checks copy it on its own.
python="${LEARN_UKRAINIAN_PYTHON:-}"
if [[ -n "$python" ]]; then
  if [[ "$python" != /* ]]; then
    echo "[project-python] ERROR: LEARN_UKRAINIAN_PYTHON must be an absolute path, got $python" >&2
    exit 127
  fi
  if [[ ! -f "$python" || ! -x "$python" ]]; then
    echo "[project-python] ERROR: LEARN_UKRAINIAN_PYTHON=$python is not an executable file" >&2
    exit 127
  fi
else
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
fi

exec "$python" "$@"
