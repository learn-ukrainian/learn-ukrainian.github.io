#!/usr/bin/env bash
# services.sh — Start/stop/restart project services
#
# Usage:
#   ./services.sh start              # Start all services
#   ./services.sh start rag api      # Start specific services
#   ./services.sh stop               # Stop all services
#   ./services.sh stop rag           # Stop specific service
#   ./services.sh restart            # Restart all
#   ./services.sh restart api        # Restart specific service
#   ./services.sh status             # Show what's running
#
# Services: rag, api, starlight

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
PIDS_DIR="$PROJECT_ROOT/.pids"
VENV="$PROJECT_ROOT/.venv/bin"

mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# Service definitions: name -> command, port, log file
declare -A SVC_CMD SVC_PORT SVC_LOG SVC_DESC

SVC_CMD[rag]="$VENV/python .mcp/servers/rag/server.py --standalone"
SVC_PORT[rag]=8766
SVC_LOG[rag]="$LOGS_DIR/rag-server.log"
SVC_DESC[rag]="RAG MCP Server (Qdrant + embeddings)"

SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765"
SVC_PORT[api]=8765
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"

SVC_CMD[starlight]="npm run dev --prefix starlight"
SVC_PORT[starlight]=4321
SVC_LOG[starlight]="$LOGS_DIR/starlight.log"
SVC_DESC[starlight]="Starlight Dev Server (Astro)"

ALL_SERVICES="rag api starlight"

_pid_file() { echo "$PIDS_DIR/$1.pid"; }

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
    return 1
}

_start_service() {
    local name="$1"
    if _is_running "$name"; then
        echo "  $name is already running (PID $(cat "$(_pid_file "$name")"))"
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
    fi

    echo "  $name stopped"
}

_status() {
    printf "%-12s %-8s %-8s %s\n" "SERVICE" "STATUS" "PID" "PORT"
    printf "%-12s %-8s %-8s %s\n" "-------" "------" "---" "----"
    for name in $ALL_SERVICES; do
        if _is_running "$name"; then
            local pid
            pid=$(cat "$(_pid_file "$name")")
            printf "%-12s \033[32m%-8s\033[0m %-8s %s\n" "$name" "running" "$pid" "${SVC_PORT[$name]}"
        else
            printf "%-12s \033[31m%-8s\033[0m %-8s %s\n" "$name" "stopped" "-" "${SVC_PORT[$name]}"
        fi
    done
}

# Parse arguments
action="${1:-help}"
shift || true
services="${*:-$ALL_SERVICES}"

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
        echo "  $0 start              # Start all"
        echo "  $0 start rag api      # Start specific"
        echo "  $0 stop rag           # Stop one"
        echo "  $0 restart            # Restart all"
        echo "  $0 status             # Show status"
        ;;
esac
