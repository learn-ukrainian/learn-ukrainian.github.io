#!/usr/bin/env bash
# Live apply, pre-apply check and rollback for the shared lu.slice pool (#9624).
# Usage: scripts/ops/lu_slice_apply.sh check|apply|rollback
# Never restarts or stops scopes: slice limits change in place.
#
# The unit file carries no limits. Each deployment installs a limits drop-in
# next to the installed unit (lu.slice.d/10-limits.conf). check and apply read
# the expected values from the manager and refuse unless that drop-in is
# loaded and every value is finite, so installing the unit never lifts the cap.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${LU_SLICE_SOURCE:-$ROOT/packaging/systemd/lu.slice}"
UNIT_DIR="${LU_SLICE_UNIT_DIR:-$HOME/.config/systemd/user}"
CGROUP="${LU_SLICE_CGROUP:-/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/lu.slice}"
CONTROL_DIRS=("${LU_SLICE_CONTROL_DIR:-$HOME/.config/systemd/user.control}/lu.slice.d"
              "${LU_SLICE_RUNTIME_CONTROL_DIR:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/systemd/user.control}/lu.slice.d")
LIMITS_DIR="$UNIT_DIR/lu.slice.d"
HIGH_BYTES="" MAX_BYTES="" SWAP_BYTES=""

die() { printf 'LU_SLICE_REFUSED %s\n' "$1" >&2; exit "${2:-1}"; }
read_cg() { local v; v="$(cat "$CGROUP/$1" 2>/dev/null)" || die "unreadable-$1" 3; printf '%s' "$v"; }

expected_limits() {
  # Effective values as the manager resolved them, drop-in precedence included.
  local props key value dropins=""
  HIGH_BYTES="" MAX_BYTES="" SWAP_BYTES=""
  props="$(systemctl --user show lu.slice -p MemoryHigh -p MemoryMax -p MemorySwapMax -p DropInPaths)" \
    || die "user-manager-unavailable" 3
  while IFS='=' read -r key value; do
    case "$key" in
      MemoryHigh) HIGH_BYTES="$value" ;; MemoryMax) MAX_BYTES="$value" ;;
      MemorySwapMax) SWAP_BYTES="$value" ;; DropInPaths) dropins="$value" ;;
    esac
  done <<< "$props"
  local path found=0
  for path in $dropins; do
    case "$path" in "$LIMITS_DIR"/*.conf) found=1 ;; esac
  done
  (( found )) || die "limits-dropin-missing: install and verify $LIMITS_DIR/10-limits.conf first" 7
  local v
  for v in "$HIGH_BYTES" "$MAX_BYTES" "$SWAP_BYTES"; do
    [[ "$v" =~ ^[0-9]+$ ]] || die "limits-not-finite high=$HIGH_BYTES max=$MAX_BYTES swap=$SWAP_BYTES" 7
  done
  (( HIGH_BYTES < MAX_BYTES )) || die "limits-invalid high=$HIGH_BYTES max=$MAX_BYTES" 7
}

check() {
  local cur
  expected_limits
  cur="$(read_cg memory.current)"
  [[ "$cur" =~ ^[0-9]+$ ]] || die "invalid-memory.current" 3
  if (( cur > MAX_BYTES )); then
    die "memory.current=$cur above MemoryMax=$MAX_BYTES; applying would reclaim or OOM-kill now" 4
  fi
  if (( cur >= HIGH_BYTES )); then
    printf 'LU_SLICE_WARN memory.current=%s at or above MemoryHigh=%s; the pool throttles as soon as the cap applies\n' "$cur" "$HIGH_BYTES" >&2
  fi
  printf 'LU_SLICE_CHECK_OK memory.current=%s high=%s max=%s\n' "$cur" "$HIGH_BYTES" "$MAX_BYTES"
}

expect() {  # file expected
  local got; got="$(read_cg "$1")"
  [ "$got" = "$2" ] || { printf 'LU_SLICE_MISMATCH %s=%s expected %s\n' "$1" "$got" "$2" >&2; return 1; }
}

apply() {
  check
  local high="$HIGH_BYTES" max="$MAX_BYTES" swap="$SWAP_BYTES"
  install -d -m 0700 "$UNIT_DIR"
  install -m 0644 "$SRC" "$UNIT_DIR/lu.slice"
  systemctl --user daemon-reload
  # The drop-in must still win after the reload, with the same values.
  expected_limits
  [ "$HIGH_BYTES/$MAX_BYTES/$SWAP_BYTES" = "$high/$max/$swap" ] \
    || die "limits-changed-during-apply high=$HIGH_BYTES max=$MAX_BYTES swap=$SWAP_BYTES" 5
  if ! { expect memory.high "$high" && expect memory.max "$max" && expect memory.swap.max "$swap"; } 2>/dev/null; then
    # Same values as the drop-in; rollback removes this runtime override too.
    systemctl --user set-property --runtime lu.slice MemoryHigh="$high" MemoryMax="$max" MemorySwapMax="$swap"
  fi
  expect memory.high "$high" && expect memory.max "$max" && expect memory.swap.max "$swap" \
    || die "apply-verify-failed" 5
  printf 'LU_SLICE_APPLIED high=%s max=%s swap=%s\n' "$high" "$max" "$swap"
}

rollback() {
  # Lift the cap at once, then remove every persistent source of it. The
  # deployment reinstalls its limits drop-in on its next run.
  systemctl --user set-property --runtime lu.slice MemoryHigh=infinity MemoryMax=infinity MemorySwapMax=infinity
  rm -f "$UNIT_DIR/lu.slice"
  local d
  for d in "$LIMITS_DIR" "${CONTROL_DIRS[@]}"; do
    [ -d "$d" ] || continue
    rm -f -- "$d"/*.conf
    rmdir -- "$d" || die "control-dropin-dir-not-empty $d" 5
  done
  systemctl --user daemon-reload
  expect memory.high max && expect memory.max max && expect memory.swap.max max || die "rollback-verify-failed" 5
  printf 'LU_SLICE_ROLLED_BACK memory.high=max memory.max=max memory.swap.max=max\n'
}

case "${1:-}" in
  check) check ;;
  apply) apply ;;
  rollback) rollback ;;
  *) printf 'usage: %s check|apply|rollback\n' "$0" >&2; exit 2 ;;
esac
