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
#   ./services.sh status             # Show what's running
#
# Services: sources, api, starlight
#
# Note: the `sources` service was historically called `rag`. It serves
# SQLite FTS5 indices over textbook chunks, dictionaries, VESUM, literary
# sources, and Wikipedia — an MCP server, not vector-RAG retrieval. We
# accept the legacy name `rag` as an alias below for backwards compat
# with old shell history and session notes. Remove the alias after the
# next quarterly cleanup pass.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/.pids"
VENV="$PROJECT_ROOT/.venv/bin"

mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# Bridge defaults for learn-ukrainian. Other projects can set AB_* explicitly.
export AB_MONITOR_URL="${AB_MONITOR_URL:-http://localhost:8765/api/state/summary}"

# Service definitions: name -> command, port, log file, health checks, process match
declare -A SVC_CMD SVC_PORT SVC_LOG SVC_DESC SVC_HEALTH SVC_HEALTH_ALT SVC_MATCH

SVC_CMD[sources]="$VENV/python .mcp/servers/sources/server.py --standalone"
SVC_PORT[sources]=8766
SVC_LOG[sources]="$LOGS_DIR/mcp-sources.log"
SVC_DESC[sources]="MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia)"
SVC_HEALTH[sources]="http://127.0.0.1:8766/health"
SVC_HEALTH_ALT[sources]="http://localhost:8766/health"
SVC_MATCH[sources]=".mcp/servers/sources/server.py --standalone"

SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765"
SVC_PORT[api]=8765
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"
SVC_HEALTH[api]="http://127.0.0.1:8765/api/health"
SVC_HEALTH_ALT[api]="http://localhost:8765/api/health"
SVC_MATCH[api]="scripts.api.main:app --host 0.0.0.0 --port 8765"

SVC_CMD[starlight]="npm run dev --prefix starlight -- --force"
SVC_PORT[starlight]=4321
SVC_LOG[starlight]="$LOGS_DIR/starlight.log"
SVC_DESC[starlight]="Starlight Dev Server (Astro)"
SVC_HEALTH[starlight]="http://localhost:4321/"
SVC_HEALTH_ALT[starlight]="http://127.0.0.1:4321/"
SVC_MATCH[starlight]="astro dev --force"

ALL_SERVICES="sources api starlight"

# Legacy alias: rewrite `rag` → `sources` when passed as a CLI arg.
# Accept shell history + scripts that still say `./services.sh start rag`.
_rewrite_legacy_alias() {
    local out=()
    for svc in "$@"; do
        if [[ "$svc" == "rag" ]]; then
            out+=("sources")
        else
            out+=("$svc")
        fi
    done
    printf '%s\n' "${out[@]}"
}

_pid_file() { echo "$PIDS_DIR/$1.pid"; }

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
    if command -v lsof >/dev/null 2>&1; then
        # `|| true` because lsof exits 1 when no listener is found, and with
        # `set -eo pipefail` upstream that bubbles up to the caller. We want
        # an empty-stdout, exit-0 contract so callers can distinguish "no
        # owner" from "lookup failed" purely by the captured value.
        lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
    fi
}

_cmdline_for_pid() {
    local pid="$1"
    ps -p "$pid" -o args= 2>/dev/null
}

_pid_matches_service() {
    local name="$1"
    local pid="$2"
    local match="${SVC_MATCH[$name]-}"
    local cmdline

    if [[ -z "$match" ]]; then
        return 1
    fi

    cmdline="$(_cmdline_for_pid "$pid")"
    [[ -n "$cmdline" && "$cmdline" == *"$match"* ]]
}

_verified_port_pid() {
    local name="$1"
    local port_pid

    port_pid="$(_pid_on_port "$name")"
    if [[ -n "$port_pid" ]] && _pid_matches_service "$name" "$port_pid"; then
        printf '%s\n' "$port_pid"
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

    if [[ "$name" == "starlight" ]]; then
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

_service_state() {
    local name="$1"
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

    # Race-safety: even if state is "stopped", the port may still be bound by
    # another concurrent restarter that hasn't published its health endpoint
    # yet, OR the OS may not have released the port from a just-killed PID.
    # Spawning a new uvicorn here would just die with EADDRINUSE.
    # Adopt only if the owner's cmdline matches our service signature
    # (don't accidentally claim a random foreign process bound to the same
    # port — that would write a wrong PID into our pidfile).
    local port_pid
    port_pid="$(_pid_on_port "$name")"
    if [[ -n "$port_pid" ]]; then
        if _pid_matches_service "$name" "$port_pid"; then
            echo "  $name port ${SVC_PORT[$name]} is already bound by PID $port_pid (concurrent start?); not spawning"
            _sync_pidfile "$name" "$port_pid"
            return 0
        else
            echo "  $name port ${SVC_PORT[$name]} is bound by foreign PID $port_pid; not spawning (free the port and retry)"
            return 1
        fi
    fi

    echo "  Starting $name — ${SVC_DESC[$name]}..."
    cd "$PROJECT_ROOT"

    # shellcheck disable=SC2086
    nohup ${SVC_CMD[$name]} >> "${SVC_LOG[$name]}" 2>&1 &
    local pid=$!

    echo "$pid" > "$(_pid_file "$name")"
    echo "  $name started (PID $pid, port ${SVC_PORT[$name]}, log ${SVC_LOG[$name]})"
}

_stop_service() {
    local name="$1"
    local pidfile
    pidfile="$(_pid_file "$name")"

    local pid
    pid="$(_known_service_pid "$name" || true)"
    if [[ -z "$pid" ]]; then
        echo "  $name is not running"
        rm -f "$pidfile"
        return 0
    fi

    echo "  Stopping $name (PID $pid)..."
    kill "$pid" 2>/dev/null || true

    # Wait up to 5 seconds for graceful shutdown
    for _ in $(seq 1 10); do
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

    # Wait for the OS to actually release the listening socket. Process death
    # ≠ port released — macOS holds the socket briefly in TIME_WAIT (or until
    # all child fds close). Without this wait, an immediate _start_service
    # would race a stale port and die with EADDRINUSE.
    for _ in $(seq 1 10); do
        if [[ -z "$(_pid_on_port "$name")" ]]; then
            break
        fi
        sleep 0.5
    done

    # Starlight: clear Astro content collection cache on stop.
    # Astro 6 doesn't reliably pick up new MDX files added while the
    # dev server is running (content-layer deferred modules). Clearing
    # the data-store forces a full re-index on next start.
    if [[ "$name" == "starlight" ]]; then
        local cache_file="$PROJECT_ROOT/starlight/.astro/data-store.json"
        if [[ -f "$cache_file" ]]; then
            rm -f "$cache_file"
            echo "  Cleared Astro content cache (data-store.json)"
        fi
        local vite_cache_dir="$PROJECT_ROOT/starlight/node_modules/.vite"
        if [[ -d "$vite_cache_dir" ]]; then
            rm -rf "$vite_cache_dir"
            echo "  Cleared Vite cache (.vite)"
        fi
    fi

    echo "  $name stopped"
}

_status() {
    printf "%-12s %-8s %-8s %s\n" "SERVICE" "STATUS" "PID" "PORT"
    printf "%-12s %-8s %-8s %s\n" "-------" "------" "---" "----"
    for name in $ALL_SERVICES; do
        local state pid
        state="$(_service_state "$name")"
        pid="$(_known_service_pid "$name" || true)"
        if [[ -z "$pid" ]]; then
            pid="-"
        fi

        case "$state" in
            running)
                printf "%-12s \033[32m%-8s\033[0m %-8s %s\n" "$name" "$state" "$pid" "${SVC_PORT[$name]}"
                ;;
            degraded)
                printf "%-12s \033[33m%-8s\033[0m %-8s %s\n" "$name" "$state" "$pid" "${SVC_PORT[$name]}"
                ;;
            *)
                printf "%-12s \033[31m%-8s\033[0m %-8s %s\n" "$name" "$state" "$pid" "${SVC_PORT[$name]}"
                ;;
        esac
    done
}

# Parse arguments
action="${1:-help}"
shift || true
services="${*:-$ALL_SERVICES}"
# Rewrite legacy alias `rag` → `sources` so old muscle memory still works.
if [[ -n "${services// /}" ]]; then
    # shellcheck disable=SC2086
    services=$(_rewrite_legacy_alias $services | tr '\n' ' ')
fi

case "$action" in
    start)
        echo "Starting services..."
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc (available: $ALL_SERVICES)"
                continue
            fi
            _start_service "$svc"
        done
        echo ""
        _status
        ;;
    stop)
        echo "Stopping services..."
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc"
                continue
            fi
            _stop_service "$svc"
        done
        echo ""
        _status
        ;;
    restart)
        # Serialize across all callers — see _acquire_restart_lock comment.
        if ! _acquire_restart_lock; then
            exit 1
        fi
        trap _release_restart_lock EXIT INT TERM

        echo "Restarting services..."
        for svc in $services; do
            if [[ -z "${SVC_CMD[$svc]+x}" ]]; then
                echo "  Unknown service: $svc"
                continue
            fi
            _stop_service "$svc"
            _start_service "$svc"
        done
        echo ""
        _status
        ;;
    status)
        _status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [service ...]"
        echo ""
        echo "Services:"
        for name in $ALL_SERVICES; do
            printf "  %-12s %s (port %s)\n" "$name" "${SVC_DESC[$name]}" "${SVC_PORT[$name]}"
        done
        echo ""
        echo "Examples:"
        echo "  $0 start                  # Start all"
        echo "  $0 start sources api      # Start specific"
        echo "  $0 stop sources           # Stop one"
        echo "  $0 restart                # Restart all"
        echo "  $0 status                 # Show status"
        echo ""
        echo "Note: 'rag' is accepted as a legacy alias for 'sources'."
        ;;
esac
