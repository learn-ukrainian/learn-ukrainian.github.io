#!/usr/bin/env bash
# Verify a detached job's real cgroup before executing any workload (#9624).
set -euo pipefail

if [[ "${1:-}" == --help ]]; then
  cat <<'HELP'
Verify a detached job's memory containment, then execute its command.
Use inside a systemd user unit in lu.slice, never as an unbounded fallback.
Usage: bash scripts/lib/job_memory_scope.sh MAX_BYTES -- COMMAND [ARG...]
Example: systemd-run --user --scope --slice=lu.slice -p MemoryMax=192M -p MemorySwapMax=0 bash scripts/lib/job_memory_scope.sh 201326592 -- true
Outputs: executes COMMAND only after kernel memory/swap readback matches.
Exit codes: command's status; 2 invalid arguments; 6 containment refused.
Related: docs/runbooks/driver-memory-scope.md, issue #9624.
HELP
  exit 0
fi
if [[ $# -lt 3 || "$2" != -- || ! "$1" =~ ^[1-9][0-9]*$ ]]; then
  echo 'usage: job_memory_scope.sh MAX_BYTES -- COMMAND [ARG...]' >&2
  exit 2
fi
expected="$1"
shift 2
refuse() { printf 'JOB_SCOPE_REFUSED reason=%s\n' "$1" >&2; exit 6; }
relative=""
while IFS= read -r line; do
  case "$line" in 0::*) relative="${line#0::}" ;; esac
done < /proc/self/cgroup || refuse cgroup-unreadable
case "$relative" in
  /user.slice/user-*.slice/user@*.service/lu.slice/*) ;;
  *) refuse outside-pool ;;
esac
group="/sys/fs/cgroup$relative"
pool="/sys/fs/cgroup${relative%%/lu.slice/*}/lu.slice"
maximum="$(cat "$group/memory.max" 2>/dev/null)" || refuse memory-limit-unreadable
swap="$(cat "$group/memory.swap.max" 2>/dev/null)" || refuse swap-limit-unreadable
[[ "$maximum" == "$expected" && "$swap" == 0 ]] || refuse limits-mismatch
maximum="$(cat "$pool/memory.max" 2>/dev/null)" || refuse pool-limit-unreadable
swap="$(cat "$pool/memory.swap.max" 2>/dev/null)" || refuse pool-swap-unreadable
[[ "$maximum" =~ ^[0-9]+$ && "$maximum" =~ [1-9] && "$swap" =~ ^[0-9]+$ ]] || refuse pool-unbounded
exec "$@"
