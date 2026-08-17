#!/bin/bash
# launchd binds LWCR to ProgramArguments[0]. That must stay /bin/bash
# (Apple-signed). Never put .venv/bin/python there: a venv rebuild
# replaces the binary and launchd then fails with
# "Unable to get updated LWCR ... error 0x3 - No such process" (exit 78).
set -euo pipefail

primary=""
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  if [[ "${args[$i]}" == "--repo-root" ]]; then
    primary="${args[$((i + 1))]:-}"
    break
  fi
done

if [[ -z "${primary}" ]]; then
  echo "monitor-api: missing --repo-root (primary checkout)" >&2
  exit 78
fi

python="${primary}/.venv/bin/python"
supervisor="$(cd "$(dirname "$0")" && pwd)/launchd_supervisor.py"

if [[ ! -x "${python}" ]]; then
  echo "monitor-api: missing interpreter: ${python}" >&2
  exit 78
fi
if [[ ! -f "${supervisor}" ]]; then
  echo "monitor-api: missing script: ${supervisor}" >&2
  exit 78
fi

cd "${primary}"
exec "${python}" -m scripts.api.launchd_supervisor "$@"
