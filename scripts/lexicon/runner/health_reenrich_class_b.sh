#!/usr/bin/env bash
# Thin remote health probe for the #6369 Class-B re-enrich job. Read-only:
# never syncs, launches, or mutates anything on the VPS (mirrors
# health_20k_runner.sh's fail-closed reporting shape).
#
# Env overrides:
#   ATLAS_RUNNER_HOST (default vps), ATLAS_RUN_ROOT, ATLAS_RE_ENRICH_WORK_DIR
set -uo pipefail

HOST="${ATLAS_RUNNER_HOST:-vps}"
RUN_ROOT="${ATLAS_RUN_ROOT:-/home/ops/atlas-runner}"
WORK_DIR="${ATLAS_RE_ENRICH_WORK_DIR:-$RUN_ROOT/run-class-b-reenrich}"

host_reachable=false
work_dir_present=false
running=false
pid=""
log_tail=""
disk_line=""

if ! ssh -o BatchMode=yes -o ConnectTimeout=10 -- "$HOST" "true" 2>/dev/null; then
  printf 'host_reachable=false\n'
  printf 'reenrich health check failed: cannot reach %s over SSH.\n' "$HOST" >&2
  exit 2
fi
host_reachable=true

remote_probe="$(ssh -o BatchMode=yes -o ConnectTimeout=10 -- "$HOST" "
  work_dir=$(printf '%q' "$WORK_DIR")
  if [[ -d \"\$work_dir\" ]]; then echo 'work_dir_present=true'; else echo 'work_dir_present=false'; fi
  pid_file=\"\$work_dir/reenrich-driver.pid\"
  if [[ -f \"\$pid_file\" ]] && kill -0 \"\$(cat \"\$pid_file\")\" 2>/dev/null; then
    echo 'running=true'
    echo \"pid=\$(cat \"\$pid_file\")\"
  else
    echo 'running=false'
  fi
  df -h / | tail -n 1
" 2>/dev/null)"

work_dir_present=$(printf '%s\n' "$remote_probe" | sed -n 's/^work_dir_present=//p')
running=$(printf '%s\n' "$remote_probe" | sed -n 's/^running=//p')
pid=$(printf '%s\n' "$remote_probe" | sed -n 's/^pid=//p')
disk_line=$(printf '%s\n' "$remote_probe" | tail -n 1)

log_tail=$(ssh -o BatchMode=yes -o ConnectTimeout=10 -- "$HOST" "tail -n 20 $(printf '%q' "$WORK_DIR/reenrich.log") 2>/dev/null" || true)

printf 'host_reachable=%s\n' "$host_reachable"
printf 'work_dir_present=%s\n' "${work_dir_present:-false}"
printf 'running=%s\n' "${running:-false}"
if [[ -n "$pid" ]]; then
  printf 'pid=%s\n' "$pid"
fi
printf 'disk=%s\n' "$disk_line"
if [[ -n "$log_tail" ]]; then
  printf -- '--- log tail ---\n%s\n' "$log_tail"
fi

if [[ "${work_dir_present:-false}" != "true" ]]; then
  exit 2
fi
exit 0
