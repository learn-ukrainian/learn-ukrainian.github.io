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

# Service definitions: name -> command, port, log file, health check
declare -A SVC_CMD SVC_PORT SVC_LOG SVC_DESC SVC_HEALTH

SVC_CMD[sources]="$VENV/python .mcp/servers/sources/server.py --standalone"
SVC_PORT[sources]=8766
SVC_LOG[sources]="$LOGS_DIR/mcp-sources.log"
SVC_DESC[sources]="MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia)"
SVC_HEALTH[sources]="http://localhost:8766/health"

SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765"
SVC_PORT[api]=8765
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"
SVC_HEALTH[api]="http://localhost:8765/api/health"

SVC_CMD[starlight]="npm run dev --prefix starlight -- --force"
SVC_PORT[starlight]=4321
SVC_LOG[starlight]="$LOGS_DIR/starlight.log"
SVC_DESC[starlight]="Starlight Dev Server (Astro)"
SVC_HEALTH[starlight]="http://localhost:4321/"

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

_pid_on_port() {
    local name="$1"
    local port="${SVC_PORT[$name]}"
    if command -v lsof >/dev/null 2>&1; then
        lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -n 1
    fi
}

_health_check() {
    local name="$1"
    local url="${SVC_HEALTH[$name]-}"

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

_service_state() {
    local name="$1"
    if _health_check "$name"; then
        echo "running"
        return 0
    fi

    if _is_running "$name"; then
        echo "degraded"
        return 0
    fi

    echo "stopped"
}

_is_running() {
    local pidfile
    pidfile="$(_pid_file "$1")"
    if [[ -f "$pidfile" ]]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        # Stale PID file
        rm -f "$pidfile"
    fi

    # Reconcile services started outside this wrapper or after a stale-pid cleanup.
    # If the expected port is already listening, trust that process and refresh the pidfile.
    local port_pid
    port_pid="$(_pid_on_port "$1")"
    if [[ -n "$port_pid" ]]; then
        echo "$port_pid" > "$pidfile"
        return 0
    fi

    return 1
}

_start_service() {
    local name="$1"
    local state
    state="$(_service_state "$name")"
    if [[ "$state" == "running" ]]; then
        echo "  $name is already healthy (PID $(cat "$(_pid_file "$name")"))"
        return 0
    fi
    if [[ "$state" == "degraded" ]]; then
        echo "  $name process exists but is unhealthy (PID $(cat "$(_pid_file "$name")")); restart it instead"
        return 0
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

    if ! _is_running "$name"; then
        echo "  $name is not running"
        # Clean up stale PID file if it exists
        rm -f "$pidfile"
        return 0
    fi

    local pid
    pid=$(cat "$pidfile")
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
        pid="-"
        if [[ -f "$(_pid_file "$name")" ]]; then
            pid=$(cat "$(_pid_file "$name")")
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
