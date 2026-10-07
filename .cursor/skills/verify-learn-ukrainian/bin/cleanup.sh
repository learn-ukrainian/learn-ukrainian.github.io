#!/usr/bin/env bash
# Tear down the instance this verification run started. Never kills by process name.
# Evidence under LU_VERIFY_EVIDENCE_DIR is kept.
set -euo pipefail

STATE_DIR="${LU_VERIFY_STATE_DIR:-}"
PID_FILE="${LU_VERIFY_PID_FILE:-}"

if [[ -z "$STATE_DIR" && -z "$PID_FILE" ]]; then
  echo "cleanup: nothing to do (set LU_VERIFY_STATE_DIR or LU_VERIFY_PID_FILE from launch.sh)" >&2
  exit 0
fi

if [[ -z "$PID_FILE" && -n "$STATE_DIR" && -f "${STATE_DIR}/site.pid" ]]; then
  PID_FILE="${STATE_DIR}/site.pid"
fi

# Prefer Astro's own stop when we launched a preview from site/.
if [[ -d "$(pwd)/site" ]] || [[ -d /workspace/site ]]; then
  root_guess="$(cd "$(dirname "$0")/../../../.." && pwd)"
  if [[ -d "$root_guess/site" ]]; then
    (cd "$root_guess/site" && npx astro preview stop >/dev/null 2>&1) || true
  fi
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
