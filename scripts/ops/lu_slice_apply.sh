#!/usr/bin/env bash
# Live apply, pre-apply check and rollback for the shared lu.slice pool (#9624).
# Usage: scripts/ops/lu_slice_apply.sh check|apply|rollback
# Never restarts or stops scopes: slice limits change in place.
set -euo pipefail

HIGH_BYTES=25769803776  # 24G
MAX_BYTES=27917287424   # 26G
SWAP_BYTES=4294967296   # 4G
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${LU_SLICE_SOURCE:-$ROOT/packaging/systemd/lu.slice}"
UNIT_DIR="${LU_SLICE_UNIT_DIR:-$HOME/.config/systemd/user}"
CGROUP="${LU_SLICE_CGROUP:-/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/lu.slice}"
CONTROL_DIRS=("${LU_SLICE_CONTROL_DIR:-$HOME/.config/systemd/user.control}/lu.slice.d"
              "${LU_SLICE_RUNTIME_CONTROL_DIR:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/systemd/user.control}/lu.slice.d")

die() { printf 'LU_SLICE_REFUSED %s\n' "$1" >&2; exit "${2:-1}"; }
read_cg() { local v; v="$(cat "$CGROUP/$1" 2>/dev/null)" || die "unreadable-$1" 3; printf '%s' "$v"; }

check() {
  local cur
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
  install -d -m 0700 "$UNIT_DIR"
  install -m 0644 "$SRC" "$UNIT_DIR/lu.slice"
  systemctl --user daemon-reload
  if ! { expect memory.high "$HIGH_BYTES" && expect memory.max "$MAX_BYTES" && expect memory.swap.max "$SWAP_BYTES"; } 2>/dev/null; then
    # Same values as the unit file; rollback removes this runtime override too.
    systemctl --user set-property --runtime lu.slice MemoryHigh="$HIGH_BYTES" MemoryMax="$MAX_BYTES" MemorySwapMax="$SWAP_BYTES"
  fi
  expect memory.high "$HIGH_BYTES" && expect memory.max "$MAX_BYTES" && expect memory.swap.max "$SWAP_BYTES" \
    || die "apply-verify-failed" 5
  printf 'LU_SLICE_APPLIED high=%s max=%s swap=%s\n' "$HIGH_BYTES" "$MAX_BYTES" "$SWAP_BYTES"
}

rollback() {
  # Lift the cap at once, then remove every persistent source of it.
  systemctl --user set-property --runtime lu.slice MemoryHigh=infinity MemoryMax=infinity MemorySwapMax=infinity
  rm -f "$UNIT_DIR/lu.slice"
  local d
  for d in "${CONTROL_DIRS[@]}"; do rm -rf -- "$d"; done
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
