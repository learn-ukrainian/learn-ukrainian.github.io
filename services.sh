#!/usr/bin/env bash
# services.sh — Start/stop/restart project services
#
# Usage:
#   ./services.sh start              # Start all services
#   ./services.sh start sources api  # Start specific services
#   ./services.sh stop               # Stop all services
#   ./services.sh stop sources       # Stop specific service
#   ./services.sh restart            # Restart all
#   ./services.sh restart api        # Restart specific service
#   ./services.sh fix                # Health-check all; restart only unhealthy
#   ./services.sh fix api            # Health-check and repair one service
#   ./services.sh start api --live   # Emergency mutable-checkout API mode
#   ./services.sh status             # Show what's running
#   ./services.sh status work        # Show one service
#   ./services.sh logs work          # Show the latest service log
#   ./services.sh supervise api install|status|uninstall
#   ./services.sh build astro        # Run Astro production build (no dev server)
#   ./services.sh clean astro        # Remove Astro build/cache outputs
#   ./services.sh rebuild astro      # Run Astro clean then build
#
# Services: sources, api, astro, work
#
# SSH LocalForward (Mac notebook + Host alias hramatka-tunnel):
#   start/stop/restart auto-delegate to the writer host when any requested
#   service port is owned by an ssh listener, or when LU_SERVICES_SSH_HOST
#   is set. They never spawn or signal local processes in that case.
#   ``start`` with no service args requests ALL services; when any one of
#   those ports is tunneled (or LU_SERVICES_SSH_HOST is set), the whole
#   batch is delegated remotely — not just the tunneled service.
#   ``--live`` and ``--force`` are local API recovery flags; delegated
#   start/stop/restart never forwards them to the remote services.sh.
#   When lsof is absent (or SVC_LSOF_BIN is not executable), port-owner
#   lookup is a no-op: tunnel auto-delegation and foreign-listener checks
#   are skipped until a working lsof is available.
#   fix curls each health URL; unhealthy tunneled ports get a remote
#   restart. Overrides: LU_SERVICES_SSH_HOST (default host alias hramatka),
#   LU_SERVICES_REMOTE_ROOT (default /home/ops/learn-ukrainian).
#
# Note: the `sources` service was historically called `rag`. It serves
# SQLite FTS5 indices over textbook chunks, dictionaries, VESUM, literary
# sources, and Wikipedia — an MCP server, not vector-RAG retrieval. We
# accept legacy service aliases below for backwards compat with old shell
# history and session notes. Remove the aliases after the next quarterly
# cleanup pass.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SVC_LSOF_BIN="${SVC_LSOF_BIN:-lsof}"
LOGS_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/.pids"
VENV="$PROJECT_ROOT/.venv/bin"

# Resolve the human-owned primary checkout even when this script runs from a
# dispatch worktree. The private Work adapter lives in a deterministic sibling
# checkout; tests and nonstandard layouts may override only that filesystem
# root, never the browser endpoint or bind address.
PUBLIC_PRIMARY_ROOT="$PROJECT_ROOT"
git_common_dir="$(git -C "$PROJECT_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
if [[ -n "$git_common_dir" && "$(basename "$git_common_dir")" == ".git" ]]; then
    PUBLIC_PRIMARY_ROOT="$(cd "$(dirname "$git_common_dir")" && pwd)"
fi
WORK_PRIVATE_ROOT="${LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT:-$(dirname "$PUBLIC_PRIMARY_ROOT")/learn-ukrainian-infra-private}"

mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# Bridge defaults for learn-ukrainian. Other projects can set AB_* explicitly.
export AB_MONITOR_URL="${AB_MONITOR_URL:-http://localhost:8765/api/state/summary}"

# Service definitions: name -> command, port, log file, health checks, process match
declare -A SVC_CMD SVC_PORT SVC_HOST SVC_LOG SVC_DESC SVC_HEALTH SVC_HEALTH_ALT SVC_MATCH

SVC_CMD[sources]="$VENV/python .mcp/servers/sources/server.py --standalone --host 127.0.0.1 --port 8766"
SVC_PORT[sources]=8766
SVC_HOST[sources]=127.0.0.1
SVC_LOG[sources]="$LOGS_DIR/mcp-sources.log"
SVC_DESC[sources]="MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia)"
SVC_HEALTH[sources]="http://127.0.0.1:8766/health"
SVC_HEALTH_ALT[sources]="http://localhost:8766/health"
SVC_MATCH[sources]=".mcp/servers/sources/server.py --standalone --host 127.0.0.1 --port 8766"

SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 127.0.0.1 --port 8765 --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"
SVC_PORT[api]=8765
SVC_HOST[api]=127.0.0.1
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"
SVC_HEALTH[api]="http://127.0.0.1:8765/api/health"
SVC_HEALTH_ALT[api]="http://localhost:8765/api/health"
SVC_MATCH[api]="scripts.api.main:app --host 127.0.0.1 --port 8765"

SVC_CMD[work]="$WORK_PRIVATE_ROOT/.venv/bin/python -m work_projection"
SVC_PORT[work]=8769
SVC_HOST[work]=127.0.0.1
SVC_LOG[work]="$WORK_PRIVATE_ROOT/logs/work-projection.log"
SVC_DESC[work]="Private Work Projection Adapter (read-only, sibling checkout)"
SVC_HEALTH[work]="http://127.0.0.1:8769/v1/health"
SVC_MATCH[work]="-m work_projection"

SVC_CMD[astro]="npm run dev --prefix site -- --host 127.0.0.1 --port 4321 --force"
SVC_PORT[astro]=4321
SVC_HOST[astro]=127.0.0.1
SVC_LOG[astro]="$LOGS_DIR/astro.log"
SVC_DESC[astro]="Astro Course UI Dev Server"
SVC_HEALTH[astro]="http://127.0.0.1:4321/"
SVC_HEALTH_ALT[astro]="http://localhost:4321/"
# Live ``npm run dev`` resolves to ``node …/.bin/astro dev``; older
# installs still expose ``astro.mjs dev``. Match either argv form.
SVC_MATCH[astro]=".bin/astro dev|astro.mjs dev"

ALL_SERVICES="sources api astro work"

# Remote writer host for tunneled Mac notebooks. LU_SERVICES_SSH_HOST is
# an SSH config Host alias only; leave it unset for local-process mode.
# The default target is used only after a tunnel (or an explicit host) is
# detected — it does not by itself force delegation.
LU_SERVICES_REMOTE_ROOT="${LU_SERVICES_REMOTE_ROOT:-/home/ops/learn-ukrainian}"

# Legacy aliases: rewrite old service names when passed as CLI args.
# Accept shell history + scripts that still say `./services.sh start rag`
# or `./services.sh restart site`.
_rewrite_legacy_alias() {
    local out=()
    for svc in "$@"; do
        case "$svc" in
            rag)
                out+=("sources")
                ;;
            site)
                out+=("astro")
                ;;
            *)
                out+=("$svc")
                ;;
        esac
    done
    printf '%s\n' "${out[@]}"
}

_pid_file() { echo "$PIDS_DIR/$1.pid"; }

_tmux_session_name() {
    local name="$1"
    local root_hash
    root_hash="$(printf '%s' "$PROJECT_ROOT" | cksum | awk '{print $1}')"
    printf 'learn-ukrainian-%s-%s' "$name" "$root_hash"
}

# ---------------------------------------------------------------------------
# Restart serialization (cross-process)
# ---------------------------------------------------------------------------
# `flock` is not in macOS base; use atomic mkdir instead.
# Without this, parallel `services.sh restart api` invocations race: each
# stop_service clears the .pid file, each start_service then sees state
# "stopped", every shell spawns its own uvicorn, and only one wins the
# port-bind — the rest die with EADDRINUSE. The 2026-04-18 incident
# accumulated 623 wasted process spawns this way.
_acquire_restart_lock() {
    local lockdir="$PIDS_DIR/.restart.lock.d"
    local waited=0
    local max_wait=30
    while ! mkdir "$lockdir" 2>/dev/null; do
        # Reclaim if holder PID died without releasing.
        if [[ -f "$lockdir/pid" ]]; then
            local holder
            holder=$(cat "$lockdir/pid" 2>/dev/null || true)
            if [[ -n "$holder" ]] && ! kill -0 "$holder" 2>/dev/null; then
                rm -rf "$lockdir" 2>/dev/null || true
                continue
            fi
        fi
        if (( waited >= max_wait )); then
            local holder=""
            [[ -f "$lockdir/pid" ]] && holder=$(cat "$lockdir/pid" 2>/dev/null || true)
            echo "  Could not acquire restart lock within ${max_wait}s (held by PID ${holder:-unknown})." >&2
            return 1
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo $$ > "$lockdir/pid"
    return 0
}

_release_restart_lock() {
    local lockdir="$PIDS_DIR/.restart.lock.d"
    rm -rf "$lockdir" 2>/dev/null || true
}

_pid_on_port() {
    local name="$1"
    local port="${SVC_PORT[$name]}"
    local host="${SVC_HOST[$name]-}"
    if command -v "$SVC_LSOF_BIN" >/dev/null 2>&1; then
        # `|| true` because lsof exits 1 when no listener is found, and with
        # `set -eo pipefail` upstream that bubbles up to the caller. We want
        # an empty-stdout, exit-0 contract so callers can distinguish "no
        # owner" from "lookup failed" purely by the captured value.
        if [[ -n "$host" ]]; then
            "$SVC_LSOF_BIN" -tiTCP@"$host":"$port" -sTCP:LISTEN 2>/dev/null || true
        else
            "$SVC_LSOF_BIN" -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
        fi
    fi
}

_cmdline_for_pid() {
    local pid="$1"
    local cmdline
    local proc_cmdline="/proc/$pid/cmdline"

    # Linux exposes the argv vector directly.  Unlike ``ps -o args=``, this
    # does not depend on procps personality or command-width formatting, both
    # of which can alter the string used for our service identity match.
    # Only open /proc when the file is readable: a bare ``tr < /proc/...``
    # redirect lets bash itself print "No such file or directory" on macOS
    # (``2>/dev/null`` was on ``tr``, not the redirect). Fall back to ``ps``.
    if [[ -r "$proc_cmdline" ]] \
        && cmdline=$(tr '\0' ' ' < "$proc_cmdline" 2>/dev/null) \
        && [ -n "$cmdline" ]; then
        # The kernel terminates every argv element with NUL, including argv[0].
        # Remove only the terminal separator introduced by ``tr``.
        printf '%s\n' "${cmdline% }"
        return 0
    fi

    # ``command ps`` avoids a shell alias such as ``ps=procs`` breaking identity.
    command ps -p "$pid" -o args= 2>/dev/null
}

_pid_matches_service() {
    local name="$1"
    local pid="$2"
    local match="${SVC_MATCH[$name]-}"
    local cmdline
    local needle
    local IFS='|'

    if [[ -z "$match" ]]; then
        return 1
    fi

    cmdline="$(_cmdline_for_pid "$pid")"
    [[ -z "$cmdline" ]] && return 1

    # SVC_MATCH may list '|' alternatives (astro: .bin/astro vs astro.mjs).
    for needle in $match; do
        [[ -n "$needle" && "$cmdline" == *"$needle"* ]] && return 0
    done
    return 1
}

_verified_port_pid() {
    local name="$1"
    local port_pid

    for port_pid in $(_pid_on_port "$name"); do
        if [[ -n "$port_pid" ]] && _pid_matches_service "$name" "$port_pid"; then
            printf '%s\n' "$port_pid"
            return 0
        fi
    done

    return 1
}

_is_ssh_tunnel_pid() {
    local pid="$1"
    local comm cmdline

    comm="$(command ps -p "$pid" -o comm= 2>/dev/null || true)"
    comm="${comm##*/}"
    comm="${comm%%$'\n'*}"
    comm="${comm%% *}"
    if [[ "$comm" == "ssh" || "$comm" == "ssh.exe" ]]; then
        return 0
    fi

    cmdline="$(_cmdline_for_pid "$pid")"
    [[ -z "$cmdline" ]] && return 1
    case "$cmdline" in
        ssh[\ ]*|ssh$|*/ssh[\ ]*|*/ssh)
            return 0
            ;;
    esac
    return 1
}

_ssh_tunnel_port_pid() {
    local name="$1"
    local port_pid

    for port_pid in $(_pid_on_port "$name"); do
        if [[ -n "$port_pid" ]] && _is_ssh_tunnel_pid "$port_pid"; then
            printf '%s\n' "$port_pid"
            return 0
        fi
    done

    return 1
}

_ssh_delegate_host() {
    printf '%s\n' "${LU_SERVICES_SSH_HOST:-hramatka}"
}

_requested_has_ssh_tunnel() {
    local name
    for name in "$@"; do
        [[ -z "${SVC_CMD[$name]+x}" ]] && continue
        if _ssh_tunnel_port_pid "$name" >/dev/null; then
            return 0
        fi
    done
    return 1
}

# Delegate when the operator set LU_SERVICES_SSH_HOST, or when any requested
# service port is an ssh LocalForward listener. The default host alias is
# applied only at ssh time — it is not a trigger.
_should_delegate_remote() {
    if [[ -n "${LU_SERVICES_SSH_HOST:-}" ]]; then
        return 0
    fi
    _requested_has_ssh_tunnel "$@"
}

_delegate_remote() {
    local remote_action="$1"
    shift
    local host root remote_cmd arg
    host="$(_ssh_delegate_host)"
    root="${LU_SERVICES_REMOTE_ROOT:-/home/ops/learn-ukrainian}"
    remote_cmd="./services.sh $(printf '%q' "$remote_action")"
    for arg in "$@"; do
        remote_cmd+=" $(printf '%q' "$arg")"
    done
    echo "Delegating ${remote_action}${*:+ $*} to ${host} (ssh LocalForward or LU_SERVICES_SSH_HOST); not starting or stopping local processes."
    command ssh -o BatchMode=yes "$host" "cd $(printf '%q' "$root") && ${remote_cmd}"
}

_maybe_delegate_and_exit() {
    local remote_action="$1"
    shift
    local name
    if _should_delegate_remote "$@"; then
        for name in "$@"; do
            if [[ -z "${SVC_CMD[$name]+x}" ]]; then
                echo "  Unknown service: $name (available: $ALL_SERVICES)"
                exit 1
            fi
        done
        _delegate_remote "$remote_action" "$@"
        exit $?
    fi
}

_abort_if_ssh_owned_port() {
    local name="$1"
    if _ssh_tunnel_port_pid "$name" >/dev/null; then
        echo "ERROR: $name port $(_port_owner_label "$name") is owned by an ssh LocalForward; refusing to spawn locally. Use '$0 fix $name' or '$0 restart $name' to restart the remote service." >&2
        return 1
    fi
    return 0
}

_foreign_port_pid() {
    local name="$1"
    local port_pid

    for port_pid in $(_pid_on_port "$name"); do
        if [[ -n "$port_pid" ]] && ! _pid_matches_service "$name" "$port_pid"; then
            printf '%s\n' "$port_pid"
            return 0
        fi
    done

    return 1
}

_any_port_pid() {
    local name="$1"
    local port_pid

    for port_pid in $(_pid_on_port "$name"); do
        if [[ -n "$port_pid" ]]; then
            printf '%s\n' "$port_pid"
            return 0
        fi
    done

    return 1
}

_port_owner_label() {
    local name="$1"
    local host="${SVC_HOST[$name]-}"
    local port="${SVC_PORT[$name]}"

    if [[ -n "$host" ]]; then
        printf '%s:%s' "$host" "$port"
    else
        printf '%s' "$port"
    fi
}

_health_probe() {
    local name="$1"
    local url="$2"

    if [[ -z "$url" ]]; then
        return 1
    fi

    if ! command -v curl >/dev/null 2>&1; then
        return 1
    fi

    if [[ "$name" == "astro" ]]; then
        curl -fsSI --max-time 2 "$url" >/dev/null 2>&1
    else
        curl -fsS --max-time 2 "$url" >/dev/null 2>&1
    fi
}

_health_check() {
    local name="$1"
    local primary="${SVC_HEALTH[$name]-}"
    local alt="${SVC_HEALTH_ALT[$name]-}"

    if _health_probe "$name" "$primary"; then
        return 0
    fi

    # Host-scoped services must be healthy on their configured bind address.
    # Otherwise a sibling process on localhost/IPv6 can mask a dead worktree
    # preview and make `services.sh restart astro` refuse to respawn it.
    if [[ -n "${SVC_HOST[$name]-}" ]]; then
        return 1
    fi

    if [[ -n "$alt" ]]; then
        _health_probe "$name" "$alt"
    else
        return 1
    fi
}

_known_service_pid() {
    local name="$1"
    local pidfile pid verified_pid

    pidfile="$(_pid_file "$name")"
    if [[ -f "$pidfile" ]]; then
        pid=$(cat "$pidfile" 2>/dev/null || true)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && _pid_matches_service "$name" "$pid"; then
            printf '%s\n' "$pid"
            return 0
        fi
    fi

    verified_pid="$(_verified_port_pid "$name")"
    if [[ -n "$verified_pid" ]]; then
        printf '%s\n' "$verified_pid"
        return 0
    fi

    return 1
}

_sync_pidfile() {
    local name="$1"
    local pid="$2"
    local pidfile

    pidfile="$(_pid_file "$name")"
    if [[ -n "$pid" ]]; then
        printf '%s\n' "$pid" > "$pidfile" 2>/dev/null || true
    fi
}

_reconcile_api_pid() {
    local name="api"
    local pidfile
    pidfile="$(_pid_file "$name")"
    local file_pid=""
    if [[ -f "$pidfile" ]]; then
        file_pid=$(cat "$pidfile" 2>/dev/null | tr -d '[:space:]' || true)
    fi

    # Find the actual listener PID using lsof -nP -iTCP:$port -sTCP:LISTEN
    local listener_pid=""
    if command -v "$SVC_LSOF_BIN" >/dev/null 2>&1; then
        while read -r lpid; do
            if [[ -n "$lpid" ]]; then
                if _pid_matches_service "$name" "$lpid"; then
                    listener_pid="$lpid"
                    break
                fi
            fi
        done < <("$SVC_LSOF_BIN" -t -nP -iTCP:${SVC_PORT[api]} -sTCP:LISTEN 2>/dev/null || true)
    fi

    # Mismatch check
    if [[ -n "$listener_pid" ]]; then
        if [[ "$file_pid" != "$listener_pid" ]]; then
            if [[ -n "$file_pid" ]]; then
                echo "  WARNING: pid file mismatch for $name (file: $file_pid, listener: $listener_pid); reconciling..." >&2
            fi
            # Rewrite the pid file
            echo "$listener_pid" > "$pidfile"
        fi
    else
        # No listener found on port. If the pid file has a pid, it is a mismatch (stopped/not listening)
        if [[ -n "$file_pid" ]]; then
            echo "  WARNING: pid file exists for $name (file: $file_pid) but no listener found on port; removing stale pid file..." >&2
            rm -f "$pidfile"
        fi
    fi
}

_work_unavailable_reason() {
    if [[ ! -d "$WORK_PRIVATE_ROOT/.git" && ! -f "$WORK_PRIVATE_ROOT/.git" ]]; then
        echo "private_checkout_missing"
    elif [[ ! -x "$WORK_PRIVATE_ROOT/.venv/bin/python" ]]; then
        echo "private_venv_missing"
    elif [[ ! -d "$WORK_PRIVATE_ROOT/work_projection" ]]; then
        echo "private_module_missing"
    fi
    return 0
}

_service_state() {
    local name="$1"

    # The Work health path is not identity. A foreign listener can return 2xx
    # from /v1/health, so require a matching argv before declaring it running.
    if [[ "$name" == "work" ]]; then
        if _known_service_pid "$name" >/dev/null; then
            if _health_check "$name"; then
                echo "running"
            else
                echo "degraded"
            fi
            return 0
        fi
        if _ssh_tunnel_port_pid "$name" >/dev/null && _health_check "$name"; then
            echo "tunneled"
            return 0
        fi
        if _foreign_port_pid "$name" >/dev/null; then
            echo "blocked"
            return 0
        fi
        if [[ -n "$(_work_unavailable_reason)" ]]; then
            echo "unavailable"
            return 0
        fi
        echo "stopped"
        return 0
    fi

    if _ssh_tunnel_port_pid "$name" >/dev/null && _health_check "$name"; then
        echo "tunneled"
        return 0
    fi

    if _health_check "$name"; then
        echo "running"
        return 0
    fi

    if _known_service_pid "$name" >/dev/null; then
        echo "degraded"
        return 0
    fi

    echo "stopped"
}

_is_running() {
    if _known_service_pid "$1" >/dev/null; then
        return 0
    fi

    return 1
}

_api_supervisor_available() {
    # Tests inject SVC_API_SUPERVISOR_BIN. macOS has launchctl. Linux systemd
    # units supervise uvicorn directly, so services.sh must not call launchd.
    [[ -n "${SVC_API_SUPERVISOR_BIN:-}" ]] || command -v launchctl >/dev/null 2>&1
}

_api_supervisor() {
    if [[ -n "${SVC_API_SUPERVISOR_BIN:-}" ]]; then
        "$SVC_API_SUPERVISOR_BIN" "$@"
        return
    fi
    "$VENV/python" -m scripts.api.launchd_supervisor "$@"
}

_start_api_supervised() {
    local args=(start --repo-root "$PROJECT_ROOT")
    if [[ "$API_LIVE_MODE" -eq 1 ]]; then
        args+=(--live)
        echo "  WARNING: API live mode enabled; serving mutable checkout code" >&2
    fi

    echo "  Starting api — ${SVC_DESC[api]} (launchd supervised)..."
    if ! _api_supervisor "${args[@]}"; then
        echo "  ERROR: launchd did not accept the API start request." >&2
        return 1
    fi

    local pid=""
    pid="$(_verified_port_pid api || true)"

    if [[ -n "$pid" ]]; then
        _sync_pidfile api "$pid"
        echo "  api started (PID $pid, port ${SVC_PORT[api]}, log ${SVC_LOG[api]})"
    else
        rm -f "$(_pid_file api)"
        echo "  api launch requested; waiting for launchd snapshot build (log ${SVC_LOG[api]})"
    fi
}

_disable_api_supervisor() {
    if ! _api_supervisor stop; then
        echo "  ERROR: launchd did not confirm API supervision is disabled." >&2
        return 1
    fi
}

_start_service() {
    local name="$1"
    local state
    state="$(_service_state "$name")"
    if [[ "$state" == "running" ]]; then
        local pid
        pid="$(_known_service_pid "$name" || true)"
        _sync_pidfile "$name" "$pid"
        echo "  $name is already healthy (PID ${pid:-unknown})"
        return 0
    fi
    if [[ "$state" == "degraded" ]]; then
        local pid
        pid="$(_known_service_pid "$name" || true)"
        echo "  $name process exists but is unhealthy (PID ${pid:-unknown}); restart it instead"
        return 0
    fi
    if [[ "$state" == "unavailable" ]]; then
        echo "  work unavailable ($(_work_unavailable_reason)); public services remain independent"
        return 0
    fi

    if ! _abort_if_ssh_owned_port "$name"; then
        return 1
    fi

    # Self-heal astro deps before spawning the dev server (node_modules can be wiped).
    if [[ "$name" == "astro" ]]; then
        _ensure_astro_deps || return 1
    fi

    # Race-safety: even if state is "stopped", the port may still be bound by
    # another concurrent restarter that hasn't published its health endpoint
    # yet, OR the OS may not have released the port from a just-killed PID.
    # Spawning a new uvicorn here would just die with EADDRINUSE.
    # Adopt only if the owner's cmdline matches our service signature
    # (don't accidentally claim a random foreign process bound to the same
    # port — that would write a wrong PID into our pidfile).
    local port_pid
    port_pid="$(_verified_port_pid "$name" || true)"
    if [[ -n "$port_pid" ]]; then
        echo "  $name port $(_port_owner_label "$name") is already bound by PID $port_pid (concurrent start?); not spawning"
        _sync_pidfile "$name" "$port_pid"
        return 0
    fi

    port_pid="$(_foreign_port_pid "$name" || true)"
    if [[ -n "$port_pid" ]]; then
        echo "  $name port $(_port_owner_label "$name") is bound by foreign PID $port_pid; not spawning (free the port and retry)"
        return 1
    fi

    if [[ "$name" == "api" ]] && _api_supervisor_available; then
        _start_api_supervised
        return
    fi

    echo "  Starting $name — ${SVC_DESC[$name]}..."
    cd "$PROJECT_ROOT"

    local pid=""
    if [[ "$name" == "work" ]]; then
        mkdir -p "$(dirname "${SVC_LOG[work]}")"
        (
            cd "$WORK_PRIVATE_ROOT"
            exec "$WORK_PRIVATE_ROOT/.venv/bin/python" -m work_projection
        ) </dev/null >> "${SVC_LOG[$name]}" 2>&1 &
        pid=$!
    elif [[ "$name" == "astro" ]] && command -v tmux >/dev/null 2>&1; then
        local session
        session="$(_tmux_session_name "$name")"
        tmux kill-session -t "$session" 2>/dev/null || true
        # shellcheck disable=SC2086
        tmux new-session -d -s "$session" "cd \"$PROJECT_ROOT\" && ${SVC_CMD[$name]} >> \"${SVC_LOG[$name]}\" 2>&1"
        for _ in $(seq 1 20); do
            pid="$(_verified_port_pid "$name" || true)"
            if [[ -n "$pid" ]]; then
                break
            fi
            sleep 0.25
        done
    else
        # shellcheck disable=SC2086
        nohup ${SVC_CMD[$name]} </dev/null >> "${SVC_LOG[$name]}" 2>&1 &
        pid=$!
    fi

    if [[ "$name" == "work" ]]; then
        local healthy=0
        local listener_pid=""
        for _ in $(seq 1 20); do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            listener_pid="$(_verified_port_pid work || true)"
            if [[ "$listener_pid" == "$pid" ]] && _health_check work; then
                healthy=1
                break
            fi
            sleep 0.25
        done
        if [[ "$healthy" -ne 1 ]]; then
            kill "$pid" 2>/dev/null || true
            rm -f "$(_pid_file work)"
            echo "  work failed to become healthy; inspect with: $0 logs work" >&2
            return 1
        fi
    fi

    if [[ -n "$pid" ]]; then
        echo "$pid" > "$(_pid_file "$name")"
        echo "  $name started (PID $pid, port $(_port_owner_label "$name"), log ${SVC_LOG[$name]})"
    else
        rm -f "$(_pid_file "$name")"
        echo "  $name start requested, but no matching listener appeared yet (log ${SVC_LOG[$name]})"
    fi
}

_stop_service() {
    local name="$1"
    local pidfile
    pidfile="$(_pid_file "$name")"

    # ``launchctl disable`` happens before the listener is signalled. A
    # deliberate ``services.sh stop api`` therefore cannot be resurrected by
    # KeepAlive while the old process drains.
    if [[ "$name" == "api" ]] && _api_supervisor_available; then
        _disable_api_supervisor || return 1
    fi

    local pid
    pid="$(_known_service_pid "$name" || true)"
    if [[ -z "$pid" ]]; then
        echo "  $name is not running"
        rm -f "$pidfile"
        return 0
    fi

    if [[ "$name" == "api" ]]; then
        local is_valid=0
        local listener_pid=""
        if command -v "$SVC_LSOF_BIN" >/dev/null 2>&1; then
            while read -r lpid; do
                if [[ -n "$lpid" ]]; then
                    if _pid_matches_service "$name" "$lpid"; then
                        listener_pid="$lpid"
                        break
                    fi
                fi
            done < <("$SVC_LSOF_BIN" -t -nP -iTCP:${SVC_PORT[$name]} -sTCP:LISTEN 2>/dev/null || true)
        fi

        if [[ -n "$listener_pid" && "$pid" == "$listener_pid" ]]; then
            is_valid=1
        fi

        local ppid=""
        ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d '[:space:]' || true)
        if [[ -n "$ppid" && -n "$listener_pid" && "$ppid" == "$listener_pid" ]]; then
            is_valid=1
        fi

        if [[ "$is_valid" -ne 1 ]]; then
            echo "  ERROR: PID $pid is not verified as the listener or a direct child of the verified listener. Refusing to kill." >&2
            if [[ -n "$listener_pid" ]]; then
                echo "  Reconciling pid file to reflect reality (listener: $listener_pid)..." >&2
                echo "$listener_pid" > "$pidfile"
            else
                echo "  Removing stale/invalid pid file..." >&2
                rm -f "$pidfile"
            fi
            return 1
        fi
    fi

    echo "  Stopping $name (PID $pid)..."
    kill "$pid" 2>/dev/null || true

    # Wait for graceful shutdown (12s for api, 5s for others)
    local wait_secs=5
    if [[ "$name" == "api" ]]; then
        wait_secs=12
    fi
    local iterations=$((wait_secs * 2))
    for _ in $(seq 1 $iterations); do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 0.5
    done

    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        echo "  Force killing $name..."
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$pidfile"
    if [[ "$name" == "astro" ]] && command -v tmux >/dev/null 2>&1; then
        tmux kill-session -t "$(_tmux_session_name "$name")" 2>/dev/null || true
    fi

    # Wait for the OS to actually release the listening socket. Process death
    # ≠ port released — macOS holds the socket briefly in TIME_WAIT (or until
    # all child fds close). Without this wait, an immediate _start_service
    # would race a stale port and die with EADDRINUSE.
    for _ in $(seq 1 10); do
        if [[ -z "$(_any_port_pid "$name" || true)" ]]; then
            break
        fi
        sleep 0.5
    done

    if [[ "$name" == "astro" ]]; then
        _astro_cleanup_cache
    fi

    echo "  $name stopped"
}

_astro_cleanup_cache() {
    local cache_file="$PROJECT_ROOT/site/.astro/data-store.json"
    local vite_cache_dir="$PROJECT_ROOT/site/node_modules/.vite"

    # Astro 6 doesn't reliably pick up new MDX files added while the dev
    # server is running (content-layer deferred modules). Clearing the
    # content cache forces a full re-index on next startup.
    if [[ -f "$cache_file" ]]; then
        rm -f "$cache_file"
        echo "  Cleared Astro content cache (data-store.json)"
    fi
    if [[ -d "$vite_cache_dir" ]]; then
        rm -rf "$vite_cache_dir"
        echo "  Cleared Vite cache (.vite)"
    fi
}

_astro_cleanup_build_artifacts() {
    local dist_dir="$PROJECT_ROOT/site/dist"
    local astro_dir="$PROJECT_ROOT/site/.astro"

    if [[ -d "$dist_dir" ]]; then
        rm -rf "$dist_dir"
        echo "  Removed Astro build output (dist)"
    fi
    if [[ -d "$astro_dir" ]]; then
        rm -rf "$astro_dir"
        echo "  Removed Astro generated directory (.astro)"
    fi
}

# Self-heal: site/node_modules gets wiped intermittently (npm collisions /
# parallel processes), leaving `astro: command not found`. Reinstall on demand so
# `services.sh build|rebuild|start astro` never dies on a missing binary.
_ensure_astro_deps() {
    if [[ -x "$PROJECT_ROOT/site/node_modules/.bin/astro" ]]; then
        return 0
    fi
    echo "  site deps missing (no node_modules/.bin/astro) — self-healing with npm ci..."
    ( cd "$PROJECT_ROOT/site" && npm ci && npm rebuild esbuild sharp ) || {
        echo "  ERROR: npm ci failed in site; cannot build/start astro" >&2
        return 1
    }
    echo "  site deps restored."
}

_fix_service() {
    local name="$1"

    if _health_check "$name"; then
        echo "  $name ok"
        return 0
    fi

    echo "  $name unhealthy"

    if [[ -n "${LU_SERVICES_SSH_HOST:-}" ]] || _ssh_tunnel_port_pid "$name" >/dev/null; then
        echo "  $name is ssh-forwarded (or LU_SERVICES_SSH_HOST is set); restarting remotely."
        if ! _delegate_remote restart "$name"; then
            echo "  ERROR: remote restart of $name failed." >&2
            return 1
        fi
        if _health_check "$name"; then
            echo "  $name ok"
            return 0
        fi
        echo "  ERROR: $name still unhealthy after remote restart." >&2
        return 1
    fi

    echo "  Restarting $name locally..."
    if [[ "$name" == "api" ]]; then
        _reconcile_api_pid
    fi
    _stop_service "$name"
    if ! _start_service "$name"; then
        return 1
    fi
    if _health_check "$name"; then
        echo "  $name ok"
        return 0
    fi
    echo "  ERROR: $name still unhealthy after local restart." >&2
    return 1
}

_build_astro() {
    echo "  Building astro..."
    cd "$PROJECT_ROOT"
    _ensure_astro_deps || return 1
    npm run build --prefix site
}

_clean_astro() {
    local state
    state="$(_known_service_pid astro || true)"
    if [[ -n "$state" ]]; then
        echo "  Stopping astro before clean..."
        _stop_service astro
    fi

    local had_outputs=0
    if [[ -d "$PROJECT_ROOT/site/dist" || -f "$PROJECT_ROOT/site/.astro/data-store.json" || -d "$PROJECT_ROOT/site/.astro" || -d "$PROJECT_ROOT/site/node_modules/.vite" ]]; then
        had_outputs=1
    fi

    _astro_cleanup_cache
    _astro_cleanup_build_artifacts

    if [[ "$had_outputs" -eq 0 ]]; then
        echo "  No Astro build/cache outputs to remove."
    fi
}

_rebuild_astro() {
    _clean_astro
    _build_astro
}

_status() {
    local selected="${*:-$ALL_SERVICES}"
    printf "%-12s %-11s %-8s %-15s %s\n" "SERVICE" "STATUS" "PID" "PORT" "DETAIL"
    printf "%-12s %-11s %-8s %-15s %s\n" "-------" "------" "---" "----" "------"
    for name in $selected; do
        if [[ -z "${SVC_CMD[$name]+x}" ]]; then
            printf "%-12s %-11s %-8s %-15s %s\n" "$name" "unknown" "-" "-" "not_managed"
            continue
        fi

        local state pid detail="-"
        state="$(_service_state "$name")"
        pid="$(_known_service_pid "$name" || true)"
        if [[ -z "$pid" ]]; then
            pid="$(_ssh_tunnel_port_pid "$name" || true)"
        fi
        if [[ -z "$pid" ]]; then
            pid="-"
        fi

        case "$state" in
            running)
                printf "%-12s \033[32m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "$detail"
                ;;
            tunneled)
                printf "%-12s \033[32m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "ssh_tunnel"
                ;;
            degraded)
                printf "%-12s \033[33m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "health_check_failed"
                ;;
            blocked)
                printf "%-12s \033[31m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "foreign_listener"
                ;;
            unavailable)
                detail="$(_work_unavailable_reason)"
                printf "%-12s \033[33m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "$detail"
                ;;
            *)
                printf "%-12s \033[31m%-11s\033[0m %-8s %-15s %s\n" "$name" "$state" "$pid" "$(_port_owner_label "$name")" "$detail"
                ;;
        esac
    done
}

_logs() {
    local name="$1"
    local logfile="${SVC_LOG[$name]}"
    echo "Log: $logfile"
    if [[ ! -f "$logfile" ]]; then
        echo "  No log has been created for $name yet."
        return 0
    fi
    tail -n 80 "$logfile"
}

# Parse arguments
action="${1:-help}"
shift || true

# Extract API mode and --force flags if present.
FORCE=0
API_LIVE_MODE=0
remaining_args=()
for arg in "$@"; do
    if [[ "$arg" == "--force" ]]; then
        FORCE=1
    elif [[ "$arg" == "--live" ]]; then
        API_LIVE_MODE=1
    else
        remaining_args+=("$arg")
    fi
done

services="${remaining_args[*]:-$ALL_SERVICES}"
# Rewrite legacy alias `rag` → `sources` so old muscle memory still works.
if [[ -n "${services// /}" ]]; then
    # shellcheck disable=SC2086
    services=$(_rewrite_legacy_alias $services | tr '\n' ' ')
fi

case "$action" in
    start)
        # shellcheck disable=SC2086
        _maybe_delegate_and_exit start $services
        echo "Starting services..."
        start_failed=0
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc (available: $ALL_SERVICES)"
                continue
            fi
            if ! _start_service "$svc"; then
                start_failed=1
            fi
        done
        echo ""
        _status
        if [[ "$start_failed" -ne 0 ]]; then
            exit 1
        fi
        ;;
    stop)
        # shellcheck disable=SC2086
        _maybe_delegate_and_exit stop $services
        echo "Stopping services..."
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc"
                continue
            fi
            if [[ "$svc" == "api" ]]; then
                _reconcile_api_pid
            fi
            _stop_service "$svc"
        done
        echo ""
        _status
        ;;
    restart)
        # shellcheck disable=SC2086
        _maybe_delegate_and_exit restart $services
        # Serialize across all callers — see _acquire_restart_lock comment.
        if ! _acquire_restart_lock; then
            exit 1
        fi
        trap _release_restart_lock EXIT INT TERM

        echo "Restarting services..."
        restart_failed=0
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc"
                continue
            fi
            if [[ "$svc" == "api" ]]; then
                _reconcile_api_pid
            fi
            _stop_service "$svc"
            if ! _start_service "$svc"; then
                restart_failed=1
            fi
        done
        echo ""
        _status
        if [[ "$restart_failed" -ne 0 ]]; then
            exit 1
        fi
        ;;
    fix)
        # Serialize local restarts with restart; remote repair skips spawn.
        if ! _acquire_restart_lock; then
            exit 1
        fi
        trap _release_restart_lock EXIT INT TERM

        echo "Fixing services..."
        fix_failed=0
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc (available: $ALL_SERVICES)"
                continue
            fi
            if ! _fix_service "$svc"; then
                fix_failed=1
            fi
        done
        echo ""
        _status
        if [[ "$fix_failed" -ne 0 ]]; then
            exit 1
        fi
        ;;
    supervise)
        supervisor_service="${remaining_args[0]:-}"
        supervisor_action="${remaining_args[1]:-}"
        if [[ "$supervisor_service" != "api" ]]; then
            echo "Usage: $0 supervise api <install|status|uninstall>" >&2
            exit 1
        fi
        case "$supervisor_action" in
            install)
                _api_supervisor install --repo-root "$PROJECT_ROOT"
                ;;
            status)
                _api_supervisor status
                ;;
            uninstall)
                _api_supervisor uninstall
                ;;
            *)
                echo "Usage: $0 supervise api <install|status|uninstall>" >&2
                exit 1
                ;;
        esac
        ;;
    build)
        if [[ "$#" -eq 0 ]]; then
            echo "Usage: $0 build <service>"
            echo "Supported service: astro"
            exit 1
        fi
        supported_astro=0
        for svc in $services; do
            if [[ "$svc" == "astro" ]]; then
                supported_astro=1
                _build_astro
            else
                echo "  Unsupported service for build: $svc (supported: astro)"
            fi
        done
        if [[ "$supported_astro" -eq 0 ]]; then
            exit 1
        fi
        ;;
    clean)
        if [[ "$#" -eq 0 ]]; then
            echo "Usage: $0 clean <service>"
            echo "Supported service: astro"
            exit 1
        fi
        supported_astro=0
        for svc in $services; do
            if [[ "$svc" == "astro" ]]; then
                supported_astro=1
                _clean_astro
            else
                echo "  Unsupported service for clean: $svc (supported: astro)"
            fi
        done
        if [[ "$supported_astro" -eq 0 ]]; then
            exit 1
        fi
        ;;
    rebuild)
        if [[ "$#" -eq 0 ]]; then
            echo "Usage: $0 rebuild <service>"
            echo "Supported service: astro"
            exit 1
        fi
        supported_astro=0
        for svc in $services; do
            if [[ "$svc" == "astro" ]]; then
                supported_astro=1
                _rebuild_astro
            else
                echo "  Unsupported service for rebuild: $svc (supported: astro)"
            fi
        done
        if [[ "$supported_astro" -eq 0 ]]; then
            exit 1
        fi
        ;;
    status)
        if [[ " $services " == *" api "* ]]; then
            _reconcile_api_pid
        fi
        _status "$services"
        ;;
    logs)
        if [[ "${#remaining_args[@]}" -ne 1 ]]; then
            echo "Usage: $0 logs <service>" >&2
            exit 1
        fi
        log_service="${remaining_args[0]}"
        if [[ -z "${SVC_CMD[$log_service]+x}" ]]; then
            echo "Unknown service: $log_service (available: $ALL_SERVICES)" >&2
            exit 1
        fi
        _logs "$log_service"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|fix|status|logs|supervise|build|clean|rebuild} [service ...]"
        echo ""
        echo "Services:"
        for name in $ALL_SERVICES; do
            printf "  %-12s %s (port %s)\n" "$name" "${SVC_DESC[$name]}" "${SVC_PORT[$name]}"
        done
        echo ""
        echo "Examples:"
        echo "  $0 start                  # Start all"
        echo "  $0 start sources api      # Start specific"
        echo "  $0 start work             # Start the private sibling adapter"
        echo "  $0 start api --live       # Emergency API fallback (mutable checkout)"
        echo "  $0 stop sources           # Stop one"
        echo "  $0 restart                # Restart all"
        echo "  $0 fix                    # Health-check all; restart only unhealthy"
        echo "  $0 fix api                # Health-check and repair one service"
        echo "  $0 supervise api install  # Write the launchd supervisor plist"
        echo "  $0 supervise api uninstall # Disable and remove the supervisor plist"
        echo "  $0 build astro            # Build Astro"
        echo "  $0 clean astro            # Clean Astro cache/build outputs"
        echo "  $0 rebuild astro          # Clean then build Astro"
        echo "  $0 status                 # Show status"
        echo "  $0 status work            # Show adapter status and typed failure reason"
        echo "  $0 logs work              # Show the latest adapter log"
        echo ""
        echo "SSH LocalForward: start/stop/restart auto-delegate when a requested"
        echo "port is owned by ssh (e.g. Host alias hramatka-tunnel), or when"
        echo "LU_SERVICES_SSH_HOST is set. They do not spawn local processes then."
        echo "  LU_SERVICES_SSH_HOST      SSH Host alias (default: hramatka)"
        echo "  LU_SERVICES_REMOTE_ROOT   Remote repo root (default: /home/ops/learn-ukrainian)"
        echo ""
        echo "Note: 'rag' is accepted as a legacy alias for 'sources'; 'site' is accepted as a legacy alias for 'astro'."
        ;;
esac
