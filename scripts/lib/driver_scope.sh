#!/usr/bin/env bash
# Per-session user scopes for driver and interactive launches. Sizing and
# install procedure: driver-memory-scope.md.

driver_scope_refuse() {
  printf 'DRIVER_SCOPE_REFUSED reason=%s; no unbounded override; restore the user manager and installed lu-driver.slice.\n' "$1" >&2
  return 6
}

# Tracked entry points a scope may replay, each with its provider, mode and
# interactive unit label (drivers use their lane). Re-entry replays the wrapper
# the caller invoked, never a name derived from the provider: start-glmcc.sh
# must not become start-glm.sh, which selects another route (#9624).
driver_scope_entrypoint() {
  local row
  case "$1" in
    start-claude.sh) row='claude interactive claude' ;;
    start-codex.sh) row='codex interactive codex' ;;
    start-gemini.sh) row='gemini interactive gemini' ;;
    start-grok.sh) row='grok interactive grok' ;;
    start-kimi.sh) row='kimi interactive kimi' ;;
    start-kimicc.sh) row='kimi interactive kimicc' ;;
    start-glm.sh) row='glm interactive glm' ;;
    start-glmcc.sh) row='glm interactive glmcc' ;;
    scripts/start-bio-driver.sh) row='claude interactive bio' ;;
    start-claude-driver.sh|start-claude-cto.sh) row='claude driver -' ;;
    start-codex-driver.sh|start-codex-cto.sh) row='codex driver -' ;;
    start-cursor-driver.sh) row='cursor driver -' ;;
    start-gemini-driver.sh) row='gemini driver -' ;;
    start-grok-driver.sh) row='grok driver -' ;;
    start-muse-driver.sh) row='muse driver -' ;;
    *) return 1 ;;
  esac
  read -r DS_ENTRY_PROVIDER DS_ENTRY_MODE DS_ENTRY_LABEL <<< "$row"
}

driver_scope_invoked_entry() {
  # The wrapper this shell runs, as a path relative to the checkout. A copy or
  # alias outside the checkout's root and scripts/ is not an entry point.
  local dir root
  dir="$(CDPATH='' cd -P -- "$(dirname -- "$0")" 2>/dev/null && pwd)" || return 1
  root="$(CDPATH='' cd -P -- "${LC_ROOT:-}" 2>/dev/null && pwd)" || return 1
  case "$dir" in
    "$root") DS_ENTRY_PATH="${0##*/}" ;;
    "$root/scripts") DS_ENTRY_PATH="scripts/${0##*/}" ;;
    *) return 1 ;;
  esac
  driver_scope_entrypoint "$DS_ENTRY_PATH"
}

driver_scope_cgroup() {
  # This shell's unified-hierarchy cgroup path, read from the kernel.
  local line
  DS_CGROUP=""
  while IFS= read -r line; do
    case "$line" in 0::*) DS_CGROUP="${line#0::}" ;; esac
  done < "/proc/$$/cgroup"
  [ -n "$DS_CGROUP" ]
}

driver_scope_terminal_foreground() {
  # True when this shell's process group is its terminal's foreground group,
  # the group a keyboard INT or QUIT reaches as a whole.
  local stat pgrp tpgid
  IFS= read -r stat < "/proc/$$/stat" || return 1
  # After the parenthesised command name, which may contain spaces: state,
  # ppid, pgrp, session, tty_nr, tpgid (proc_pid_stat(5)).
  read -r _ _ pgrp _ _ tpgid _ <<< "${stat##*) }"
  [ -n "$pgrp" ] && [ "$pgrp" = "$tpgid" ]
}

# Generic, conservative fallbacks (bytes), not sized for any host. Each
# deployment sets its real limits in the environment or in the config file
# below; see docs/runbooks/driver-memory-scope.md.
DS_FALLBACK_HIGH=2147483648
DS_FALLBACK_MAX=3221225472
DS_FALLBACK_SWAP=536870912
DS_FALLBACK_PYTEST_WORKERS=2

driver_scope_load_config() {
  # KEY=VALUE lines, parsed and never sourced; the environment wins.
  local file="${LU_DRIVER_SCOPE_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/driver-scope.env}"
  local key value
  [ -f "$file" ] && [ -r "$file" ] || return 0
  while IFS='=' read -r key value || [ -n "$key" ]; do
    case "$key" in
      LU_DRIVER_MEMORY_HIGH|LU_DRIVER_MEMORY_MAX|LU_DRIVER_MEMORY_SWAP_MAX|LU_DRIVER_PYTEST_MAX_WORKERS) ;;
      *) continue ;;
    esac
    [[ "$value" =~ ^[0-9]{1,15}$ ]] || continue
    [ -n "${!key:-}" ] || printf -v "$key" '%s' "$value"
  done < "$file"
}

driver_scope_mem_total() {
  # Physical memory in bytes, the only ceiling a deployment value may not pass.
  local key value unit
  while read -r key value unit; do
    [ "$key" = MemTotal: ] && [[ "$value" =~ ^[0-9]+$ ]] && { printf '%s' $((value * 1024)); return 0; }
  done < /proc/meminfo
  return 1
}

driver_scope_config() {
  # One configuration point, byte values: environment, then config file, then
  # the generic fallbacks. High < Max <= MemTotal and swap <= Max.
  driver_scope_load_config
  DS_HIGH="${LU_DRIVER_MEMORY_HIGH:-$DS_FALLBACK_HIGH}"
  DS_MAX="${LU_DRIVER_MEMORY_MAX:-$DS_FALLBACK_MAX}"
  DS_SWAP="${LU_DRIVER_MEMORY_SWAP_MAX:-$DS_FALLBACK_SWAP}"
  DS_PYTEST_WORKERS="${LU_DRIVER_PYTEST_MAX_WORKERS:-$DS_FALLBACK_PYTEST_WORKERS}"
  local value total
  for value in "$DS_HIGH" "$DS_MAX" "$DS_SWAP" "$DS_PYTEST_WORKERS"; do
    [[ "$value" =~ ^[0-9]{1,15}$ ]] || { driver_scope_refuse invalid-limits; return 6; }
  done
  total="$(driver_scope_mem_total)" || { driver_scope_refuse memtotal-unreadable; return 6; }
  if (( 10#$DS_HIGH <= 0 || 10#$DS_HIGH >= 10#$DS_MAX || 10#$DS_MAX > total || 10#$DS_SWAP > 10#$DS_MAX )); then
    driver_scope_refuse invalid-limits; return 6
  fi
  DS_HIGH=$((10#$DS_HIGH)); DS_MAX=$((10#$DS_MAX)); DS_SWAP=$((10#$DS_SWAP))
  DS_PYTEST_WORKERS=$((10#$DS_PYTEST_WORKERS))
}

driver_scope_bus() {
  # Headless tool shells can lack the bus environment. Derive only this user's
  # owned logind directory, never another session's address.
  if [ -z "${XDG_RUNTIME_DIR+x}" ]; then
    local runtime
    runtime="/run/user/$(id -u)"
    if [ -d "$runtime" ] && [ ! -L "$runtime" ] && [ -O "$runtime" ] && [ -S "$runtime/bus" ]; then
      export XDG_RUNTIME_DIR="$runtime"
    fi
  fi
  command -v systemd-run >/dev/null && command -v systemctl >/dev/null || {
    driver_scope_refuse systemd-unavailable; return 6;
  }
  local props key value state="" fragment=""
  props="$(systemctl --user show lu-driver.slice -p LoadState -p FragmentPath 2>/dev/null)" || {
    driver_scope_refuse user-manager-unavailable; return 6;
  }
  while IFS='=' read -r key value; do
    case "$key" in LoadState) state="$value" ;; FragmentPath) fragment="$value" ;; esac
  done <<< "$props"
  # Slice names can be loaded implicitly without an installed unit file.
  [ "$state" = loaded ] && [ -n "$fragment" ] || { driver_scope_refuse slice-not-installed; return 6; }
}

driver_scope_verify() {
  # $1: the mode the scope must have been started for. $2 (re-entry only): the
  # unit-name prefix the running wrapper's provider, mode and label produce.
  local mode="$1" prefix="${2:-}" actual="" props key value cg="" slice="" oom="" active="" identity=""
  driver_scope_cgroup 2>/dev/null && actual="$DS_CGROUP"
  case "$actual" in
    */lu.slice/lu-driver.slice/lu-*.scope) ;;
    *) driver_scope_refuse cgroup-mismatch; return 6 ;;
  esac
  [ "${actual##*/}" = "${LU_DRIVER_SCOPE_UNIT:-}" ] || { driver_scope_refuse unit-mismatch; return 6; }
  # The unit name records the mode it was started for: a driver never adopts
  # an interactive scope, nor the reverse.
  local token='[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.scope'
  case "$mode" in driver|interactive) ;; *) driver_scope_refuse mode-mismatch; return 6 ;; esac
  [[ "$LU_DRIVER_SCOPE_UNIT" =~ ^lu-${mode}-[a-z]+-[A-Za-z0-9_.:-]+-${token}$ ]] || {
    driver_scope_refuse mode-mismatch; return 6;
  }
  # Exactly this provider and label, then the token: lanes may contain '-'.
  if [ -n "$prefix" ]; then
    case "$LU_DRIVER_SCOPE_UNIT" in
      "$prefix"*) [[ "${LU_DRIVER_SCOPE_UNIT#"$prefix"}" =~ ^${token}$ ]] || { driver_scope_refuse identity-mismatch; return 6; } ;;
      *) driver_scope_refuse identity-mismatch; return 6 ;;
    esac
  fi
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

driver_scope_relay() {
  # Trap action of the waiting launcher. A keyboard INT or QUIT has already
  # reached the interactive provider through the terminal's foreground process
  # group; relaying it would deliver it twice. Drivers keep their relay.
  case "$LC_MODE:$1" in
    interactive:INT|interactive:QUIT)
      if driver_scope_terminal_foreground; then return 0; fi
      ;;
  esac
  relayed="$1"
  [ -z "${child:-}" ] || kill -"$1" "$child" 2>/dev/null || true
}

launcher_enter_driver_scope() {
  local label
  case "$LC_MODE" in driver|interactive) ;; *) driver_scope_refuse invalid-mode; return 6 ;; esac
  driver_scope_invoked_entry || { driver_scope_refuse entrypoint-not-allowlisted; return 6; }
  if [ "$DS_ENTRY_PROVIDER" != "$LC_PROVIDER" ] || [ "$DS_ENTRY_MODE" != "$LC_MODE" ]; then
    driver_scope_refuse entrypoint-mismatch; return 6
  fi
  # Drivers label their unit with the lane; interactive sessions have none.
  label="$DS_ENTRY_LABEL"
  [ "$LC_MODE" = interactive ] || label="$LC_EPIC"
  [[ "$label" =~ ^[A-Za-z0-9_.:-]+$ ]] || { driver_scope_refuse invalid-lane; return 6; }
  driver_scope_config || return 6
  # Same-PID re-entry only. A child launcher inherits the environment but gets
  # another scope. No environment variable alone is evidence of containment.
  if [ "${LU_DRIVER_SCOPE_PID:-}" = "$$" ]; then
    driver_scope_bus || return 6
    driver_scope_verify "$LC_MODE" "lu-${LC_MODE}-${LC_PROVIDER}-${label}-" || return 6
    unset LC_SUPERVISORY_PREDECESSOR_GENERATION
    return 0
  fi
  # A worker in the dispatch slice must stay under that slice's cap; a new
  # scope in lu-driver.slice would leave it.
  driver_scope_cgroup 2>/dev/null || { driver_scope_refuse caller-cgroup-unavailable; return 6; }
  case "$DS_CGROUP/" in
    */lu-dispatch.slice/*) driver_scope_refuse inside-dispatch-slice; return 6 ;;
  esac
  driver_scope_bus || return 6
  local token unit entry rc=0 child relayed=""
  token="$(cat /proc/sys/kernel/random/uuid)" || { driver_scope_refuse identity-unavailable; return 6; }
  unit="lu-${LC_MODE}-${LC_PROVIDER}-${label}-${token}.scope"
  entry="$(mktemp)" || { driver_scope_refuse entry-marker-unavailable; return 6; }
  # The waiting launcher owns the marker. Distinct read/write offsets and
  # inherited descriptors preserve verified entry across unlink or namespaces.
  if ! { exec 218<"$entry" 219>"/proc/self/fd/218"; }; then
    exec 218<&- 219>&-
    rm -f "$entry"
    driver_scope_refuse entry-marker-unavailable; return 6
  fi
  rm -f "$entry"
  printf 'DRIVER_SCOPE_START unit=%s high=%s max=%s swap=%s oom=continue\n' "$unit" "$DS_HIGH" "$DS_MAX" "$DS_SWAP" >&2
  # The outside shell only waits. All preparation/leases run after verified
  # entry. Keep stdin/TTY and the existing session/process group unchanged.
  trap 'driver_scope_relay INT' INT
  trap 'driver_scope_relay TERM' TERM
  trap 'driver_scope_relay HUP' HUP
  [ "$LC_MODE" = driver ] || trap 'driver_scope_relay QUIT' QUIT
  (
    trap - INT TERM HUP
    # An interactive provider keeps the terminal's QUIT, as with direct exec.
    [ "$LC_MODE" = driver ] || trap - QUIT
    exec 218<&-
    exec systemd-run --user --scope --expand-environment=no --slice=lu-driver.slice --unit="$unit" --collect --quiet \
    --property="MemoryHigh=$DS_HIGH" --property="MemoryMax=$DS_MAX" --property="MemorySwapMax=$DS_SWAP" \
    --property=OOMPolicy=continue -- bash "$LC_ROOT/scripts/lib/driver_scope.sh" \
    --entry "$LC_MODE" "$unit" 219 "$LC_ROOT/$DS_ENTRY_PATH" ${LC_SCOPE_ORIGINAL_ARGS[@]+"${LC_SCOPE_ORIGINAL_ARGS[@]}"}
  ) 0<&0 &
  child=$!
  exec 219>&-
  [ -z "$relayed" ] || kill -"$relayed" "$child" 2>/dev/null || true
  while :; do
    wait "$child" || true
    kill -0 "$child" 2>/dev/null || break
  done
  # A trapped signal ends wait early; bash keeps the child's own status.
  wait "$child" && rc=0 || rc=$?
  trap - INT TERM HUP QUIT
  local verified=""
  IFS= read -r verified <&218 || true
  exec 218<&-
  # The entry helper already reported a typed configuration/verification
  # refusal. Preserve it; only failure to start an entry is scope-start-failed.
  if [ "$verified" = refused ]; then
    rc=6
  elif [ "$verified" != verified ]; then
    driver_scope_refuse scope-start-failed || true
    # Only a supervisory driver successor carries a captured predecessor
    # generation; an interactive session never publishes, whatever it
    # inherited. This path has never claimed a lease and must never close one.
    if [ "$LC_MODE" = driver ] \
        && [ -n "${SESSION_SUPERVISOR_WAKE_DELIVERY:-}" ] \
        && [ -n "${LC_SUPERVISORY_PREDECESSOR_GENERATION:-}" ]; then
      # shellcheck source=scripts/lib/session_supervisor.sh
      if source "$LC_ROOT/scripts/lib/session_supervisor.sh"; then
        session_supervisor_publish_start_failure "${SESSION_SUPERVISOR_WAKE_STREAM:-}" \
          "$LC_SUPERVISORY_PREDECESSOR_GENERATION" scope-start-failed
      fi
    fi
    rc=6
  else
    # A signal this shell relayed ended the session; otherwise the status is
    # the provider's own.
    case "$relayed" in INT) rc=130 ;; TERM) rc=143 ;; HUP) rc=129 ;; QUIT) rc=131 ;; esac
  fi
  local exit_line stamp
  stamp="rc=$rc signal=${relayed:-none} ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit_line="DRIVER_SCOPE_EXIT epic=$LC_EPIC $stamp"
  [ "$LC_MODE" = driver ] || exit_line="DRIVER_SCOPE_EXIT mode=interactive unit=$unit $stamp"
  # A closed stderr reader must not SIGPIPE the waiting launcher before the
  # journal write or replace the child's status. Isolate the write's signal.
  (printf '%s\n' "$exit_line" >&2) || true
  logger -t lu-driver "$exit_line" 2>/dev/null || true
  exit "$rc"
}

if [ "${1:-}" = --entry ] && [ "${BASH_SOURCE[0]}" = "$0" ]; then
  shift
  # The launcher's validated mode; the replayed wrapper checks its own again.
  mode="$1"
  export LU_DRIVER_SCOPE_UNIT="$2" LU_DRIVER_SCOPE_PID="$$"
  entry="$3"; shift 3
  if ! { driver_scope_config && driver_scope_verify "$mode"; }; then
    printf 'refused\n' >&"$entry" || true
    exec 219>&-
    exit 6
  fi
  # #9624: pytest `-n auto`/`-n logical` inside a session scope resolves to at
  # most the deployment's worker cap, sized with the scope's MemoryHigh. An
  # inherited value from 0 (no xdist workers) up to the cap is kept; CI never
  # runs through this entry.
  inherited="${PYTEST_XDIST_AUTO_NUM_WORKERS:-}"
  if ! [[ "$inherited" =~ ^[0-9]{1,4}$ ]] || (( 10#$inherited > DS_PYTEST_WORKERS )); then
    export PYTEST_XDIST_AUTO_NUM_WORKERS="$DS_PYTEST_WORKERS"
  fi
  printf 'verified\n' >&"$entry"
  exec 219>&-
  exec bash "$@"
fi
