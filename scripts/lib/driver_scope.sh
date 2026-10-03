#!/usr/bin/env bash
# Per-session user scopes. Sizing and install procedure: driver-memory-scope.md.

driver_scope_refuse() {
  printf 'DRIVER_SCOPE_REFUSED reason=%s; no unbounded override; restore the user manager and installed lu-driver.slice.\n' "$1" >&2
  return 6
}

driver_scope_config() {
  # One configuration point, byte values; overrides may only lower limits.
  DS_HIGH="${LU_DRIVER_MEMORY_HIGH:-3221225472}"
  DS_MAX="${LU_DRIVER_MEMORY_MAX:-5368709120}"
  DS_SWAP="${LU_DRIVER_MEMORY_SWAP_MAX:-1073741824}"
  local value
  for value in "$DS_HIGH" "$DS_MAX" "$DS_SWAP"; do
    [[ "$value" =~ ^[0-9]{1,12}$ ]] || { driver_scope_refuse invalid-limits; return 6; }
  done
  if (( 10#$DS_HIGH <= 0 || 10#$DS_HIGH >= 10#$DS_MAX || 10#$DS_HIGH > 3221225472 || 10#$DS_MAX > 5368709120 || 10#$DS_SWAP > 1073741824 )); then
    driver_scope_refuse invalid-limits; return 6
  fi
  DS_HIGH=$((10#$DS_HIGH)); DS_MAX=$((10#$DS_MAX)); DS_SWAP=$((10#$DS_SWAP))
}

driver_scope_bus() {
  # Headless tool shells can lack the bus environment. Derive only this user's
  # owned logind directory, never another session's address.
  if [ -z "${XDG_RUNTIME_DIR+x}" ]; then
    local runtime="/run/user/$(id -u)"
    if [ -d "$runtime" ] && [ ! -L "$runtime" ] && [ -O "$runtime" ] && [ -S "$runtime/bus" ]; then
      export XDG_RUNTIME_DIR="$runtime"
    fi
  fi
  command -v systemd-run >/dev/null && command -v systemctl >/dev/null || {
    driver_scope_refuse systemd-unavailable; return 6;
  }
  local state
  state="$(systemctl --user show lu-driver.slice -p LoadState --value 2>/dev/null)" || {
    driver_scope_refuse user-manager-unavailable; return 6;
  }
  [ "$state" = loaded ] || { driver_scope_refuse slice-not-installed; return 6; }
}

driver_scope_verify() {
  local actual="" line props key value cg="" slice="" oom="" active="" identity=""
  while IFS= read -r line; do
    case "$line" in 0::*) actual="${line#0::}" ;; esac
  done < "/proc/$$/cgroup"
  case "$actual" in
    */lu.slice/lu-driver.slice/lu-driver-*.scope) ;;
    *) driver_scope_refuse cgroup-mismatch; return 6 ;;
  esac
  [ "${actual##*/}" = "$LU_DRIVER_SCOPE_UNIT" ] || { driver_scope_refuse unit-mismatch; return 6; }
  props="$(systemctl --user show "$LU_DRIVER_SCOPE_UNIT" -p Id -p ControlGroup -p Slice -p OOMPolicy -p ActiveState 2>/dev/null)" || {
    driver_scope_refuse unit-unverifiable; return 6;
  }
  while IFS='=' read -r key value; do
    case "$key" in
      Id) identity="$value" ;; ControlGroup) cg="$value" ;; Slice) slice="$value" ;;
      OOMPolicy) oom="$value" ;; ActiveState) active="$value" ;;
    esac
  done <<< "$props"
  if [ "$cg" != "$actual" ] || [ "$slice" != lu-driver.slice ] || [ "$oom" != continue ] \
      || [ "$active" != active ] || [ "$identity" != "$LU_DRIVER_SCOPE_UNIT" ]; then
    driver_scope_refuse unit-properties-mismatch; return 6
  fi
  local root="/sys/fs/cgroup$actual" file expected observed
  for file in memory.high memory.max memory.swap.max; do
    case "$file" in memory.high) expected="$DS_HIGH" ;; memory.max) expected="$DS_MAX" ;; memory.swap.max) expected="$DS_SWAP" ;; esac
    observed="$(cat "$root/$file" 2>/dev/null)" || { driver_scope_refuse limits-unreadable; return 6; }
    [ "$observed" = "$expected" ] || { driver_scope_refuse limits-mismatch; return 6; }
  done
  # Kernel parent counters include persistent charges after their writer exits.
  local memory swap
  memory="$(cat "$root/../memory.current" 2>/dev/null)" && swap="$(cat "$root/../memory.swap.current" 2>/dev/null)" || {
    driver_scope_refuse counters-unreadable; return 6;
  }
  [[ "$memory" =~ ^[0-9]+$ && "$swap" =~ ^[0-9]+$ ]] || { driver_scope_refuse counters-invalid; return 6; }
  printf 'DRIVER_SCOPE_VERIFIED unit=%s parent_memory_current=%s parent_swap_current=%s\n' "$LU_DRIVER_SCOPE_UNIT" "$memory" "$swap" >&2
}

launcher_enter_driver_scope() {
  [ "$LC_MODE" = driver ] || return 0
  driver_scope_config || return 6
  driver_scope_bus || return 6
  # Same-PID re-entry only. A child driver inherits the environment but gets
  # another scope. No environment variable alone is evidence of containment.
  if [ "${LU_DRIVER_SCOPE_PID:-}" = "$$" ]; then
    driver_scope_verify || return 6
    return 0
  fi
  local token unit entry rc=0 child pending=""
  token="$(cat /proc/sys/kernel/random/uuid)" || { driver_scope_refuse identity-unavailable; return 6; }
  [[ "$LC_EPIC" =~ ^[A-Za-z0-9_.:-]+$ ]] || { driver_scope_refuse invalid-lane; return 6; }
  unit="lu-driver-${LC_PROVIDER}-${LC_EPIC}-${token}.scope"
  entry="$(mktemp)" || { driver_scope_refuse entry-marker-unavailable; return 6; }
  printf 'DRIVER_SCOPE_START unit=%s high=%s max=%s swap=%s oom=continue\n' "$unit" "$DS_HIGH" "$DS_MAX" "$DS_SWAP" >&2
  # The outside shell only waits. All preparation/leases run after verified
  # entry. Keep stdin/TTY and the existing session/process group unchanged.
  trap 'pending=INT; [ -z "${child:-}" ] || kill -INT "$child" 2>/dev/null || true' INT
  trap 'pending=TERM; [ -z "${child:-}" ] || kill -TERM "$child" 2>/dev/null || true' TERM
  trap 'pending=HUP; [ -z "${child:-}" ] || kill -HUP "$child" 2>/dev/null || true' HUP
  (
    trap - INT TERM HUP
    exec systemd-run --user --scope --expand-environment=no --slice=lu-driver.slice --unit="$unit" --collect --quiet \
    --property="MemoryHigh=$DS_HIGH" --property="MemoryMax=$DS_MAX" --property="MemorySwapMax=$DS_SWAP" \
    --property=OOMPolicy=continue -- bash "$LC_ROOT/scripts/lib/driver_scope.sh" \
    --entry "$unit" "$entry" "$LC_ROOT/start-${LC_PROVIDER}-driver.sh" "${LC_SCOPE_ORIGINAL_ARGS[@]}"
  ) 0<&0 &
  child=$!
  [ -z "$pending" ] || kill -"$pending" "$child" 2>/dev/null || true
  while :; do
    wait "$child" && rc=0 || rc=$?
    kill -0 "$child" 2>/dev/null || break
  done
  trap - INT TERM HUP
  if [ ! -s "$entry" ]; then
    rm -f "$entry"
    driver_scope_refuse scope-start-failed
    exit 6
  fi
  rm -f "$entry"
  case "$pending" in INT) rc=130 ;; TERM) rc=143 ;; HUP) rc=129 ;; esac
  exit "$rc"
}

if [ "${1:-}" = --entry ] && [ "${BASH_SOURCE[0]}" = "$0" ]; then
  shift
  export LU_DRIVER_SCOPE_UNIT="$1" LU_DRIVER_SCOPE_PID="$$"
  entry="$2"; shift 2
  driver_scope_config && driver_scope_verify || exit 6
  printf 'verified\n' > "$entry"
  exec bash "$@"
fi
