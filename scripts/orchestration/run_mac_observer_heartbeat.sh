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
  echo "mac-observer-heartbeat: missing --repo-root (primary checkout)" >&2
  exit 78
fi

python="${primary}/.venv/bin/python"
script="$(cd "$(dirname "$0")" && pwd)/observer_heartbeat.py"

if [[ ! -x "${python}" ]]; then
  echo "mac-observer-heartbeat: missing interpreter: ${python}" >&2
  exit 78
fi
if [[ ! -f "${script}" ]]; then
  echo "mac-observer-heartbeat: missing script: ${script}" >&2
  exit 78
fi

exec "${python}" "${script}" --mac-gui "$@"
