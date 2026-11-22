#!/usr/bin/env bash
# Tear down the instance this verification run started. Never kills by process name.
# Evidence under LU_VERIFY_EVIDENCE_DIR is kept.
if [[ "${1:-}" == --help ]]; then
  cat <<'EOF'
Usage: bash .cursor/skills/verify-learn-ukrainian/bin/cleanup.sh
Stop an instance started by launch.sh; never use to stop a shared server.
First source the exact env.sh path printed by launch.sh.
Inputs: LU_VERIFY_STATE_DIR and/or LU_VERIFY_PID_FILE from that run.
State must be named lu-verify-<run-id> directly under ${TMPDIR:-/tmp}.
Outputs: signals the recorded process group, deletes PID and scratch state.
Evidence in LU_VERIFY_EVIDENCE_DIR is retained separately.
Exit: 0 on cleanup/no instance; nonzero for unsafe state or removal errors.
Related: launch.sh, ../SKILL.md.
EOF
  exit 0
fi
set -euo pipefail

STATE_DIR="${LU_VERIFY_STATE_DIR:-}"
PID_FILE="${LU_VERIFY_PID_FILE:-}"

if [[ -z "$STATE_DIR" && -z "$PID_FILE" ]]; then
  echo "cleanup: nothing to do (set LU_VERIFY_STATE_DIR or LU_VERIFY_PID_FILE from launch.sh)" >&2
  exit 0
fi

# Validate before reading a PID, signaling processes, or removing scratch state.
if [[ -n "$STATE_DIR" ]]; then
  temp_root="$(readlink -f -- "${TMPDIR:-/tmp}")"
  state_parent="$(readlink -m -- "$(dirname -- "$STATE_DIR")")"
  state_name="$(basename -- "$STATE_DIR")"
  if [[ "$state_parent" != "$temp_root" || "$state_name" != lu-verify-* || "$state_name" == lu-verify- || -L "$state_parent/$state_name" ]]; then
    echo "cleanup FAIL: unsafe state directory; require a lu-verify-<run-id> directory directly under the temporary root" >&2
    exit 1
  fi
fi

if [[ -z "$PID_FILE" && -n "$STATE_DIR" && -f "${STATE_DIR}/site.pid" ]]; then
  PID_FILE="${STATE_DIR}/site.pid"
fi

if [[ -n "$PID_FILE" && -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE")"
  if [[ -n "$pid" && -d "/proc/$pid" ]]; then
    # Kill the process group we started (astro/npm may spawn children).
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      [[ -d "/proc/$pid" ]] || break
      sleep 0.25
    done
    if [[ -d "/proc/$pid" ]]; then
      kill -9 -- "-$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
    fi
    echo "cleanup: stopped PID ${pid}"
  else
    echo "cleanup: PID ${pid:-unknown} already gone"
  fi
  rm -f "$PID_FILE"
fi

# Scratch state only — never remove evidence.
if [[ -n "$STATE_DIR" && -d "$STATE_DIR" ]]; then
  rm -rf "$STATE_DIR"
  echo "cleanup: removed state dir (evidence kept)"
fi

if [[ -n "${LU_VERIFY_EVIDENCE_DIR:-}" ]]; then
  echo "cleanup: evidence remains at ${LU_VERIFY_EVIDENCE_DIR}"
fi
exit 0
