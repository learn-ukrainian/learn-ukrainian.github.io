#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LU_PRODUCT_ROOT="$ROOT"
bootstrap_python="${LEARN_UKRAINIAN_PYTHON:-${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:+$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT/.venv/bin/python}}"
case "$bootstrap_python" in
  /*) ;;
  *) echo "Set LEARN_UKRAINIAN_PYTHON to an absolute trusted interpreter path" >&2; exit 2 ;;
esac
source "$("$bootstrap_python" -I -c 'from lu_machinery.common.repo_root import machinery_path; print(machinery_path("lib/launcher_core.sh"))')"

# CTO coordination uses the registered epics driver lane, without takeover.
for arg in "$@"; do
  case "$arg" in
    --) break ;;
    --force) launcher_error "CTO launchers reject --force; run --help."; exit 2 ;;
    -h|--help)
      printf 'CTO defaults: --epic epics --model gpt-6.2-sol --effort high. --force is refused.\n'
      ;;
  esac
done
# The lane is a fixed wrapper option: scope re-entry and successors replay the
# caller's argv, and this wrapper adds it exactly once.
LC_WRAPPER_LAUNCHER_ARGS=(--epic epics)
LAUNCHER_MODEL="${LAUNCHER_MODEL:-gpt-6.2-sol}" \
LAUNCHER_EFFORT="${LAUNCHER_EFFORT:-high}" \
launcher_main codex driver "$@"
