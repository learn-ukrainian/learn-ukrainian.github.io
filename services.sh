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
#   ./services.sh start api --live   # Emergency mutable-checkout API mode
#   ./services.sh status             # Show what's running
#   ./services.sh build astro        # Run Astro production build (no dev server)
#   ./services.sh clean astro        # Remove Astro build/cache outputs
#   ./services.sh rebuild astro      # Run Astro clean then build
#
# Services: sources, api, astro
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

mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# Bridge defaults for learn-ukrainian. Other projects can set AB_* explicitly.
export AB_MONITOR_URL="${AB_MONITOR_URL:-http://localhost:8765/api/state/summary}"

# Service definitions: name -> command, port, log file, health checks, process match
declare -A SVC_CMD SVC_PORT SVC_HOST SVC_LOG SVC_DESC SVC_HEALTH SVC_HEALTH_ALT SVC_MATCH

SVC_CMD[sources]="$VENV/python .mcp/servers/sources/server.py --standalone"
SVC_PORT[sources]=8766
SVC_LOG[sources]="$LOGS_DIR/mcp-sources.log"
SVC_DESC[sources]="MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia)"
SVC_HEALTH[sources]="http://127.0.0.1:8766/health"
SVC_HEALTH_ALT[sources]="http://localhost:8766/health"
SVC_MATCH[sources]=".mcp/servers/sources/server.py --standalone"

SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"
SVC_PORT[api]=8765
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"
SVC_HEALTH[api]="http://127.0.0.1:8765/api/health"
SVC_HEALTH_ALT[api]="http://localhost:8765/api/health"
SVC_MATCH[api]="scripts.api.main:app --host 0.0.0.0 --port 8765"

SVC_CMD[astro]="npm run dev --prefix site -- --host 127.0.0.1 --port 4321 --force"
SVC_PORT[astro]=4321
SVC_HOST[astro]=127.0.0.1
SVC_LOG[astro]="$LOGS_DIR/astro.log"
SVC_DESC[astro]="Astro Course UI Dev Server"
SVC_HEALTH[astro]="http://127.0.0.1:4321/"
SVC_HEALTH_ALT[astro]="http://localhost:4321/"
SVC_MATCH[astro]="site/node_modules/.bin/astro dev --host 127.0.0.1"

ALL_SERVICES="sources api astro"

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

    for port_pid in $(_pid_on_port "$name"); do
        if [[ -n "$port_pid" ]] && _pid_matches_service "$name" "$port_pid"; then
            printf '%s\n' "$port_pid"
            return 0
        fi
    done

    return 1
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

_api_launch_context() {
    API_LAUNCH_CWD="$PROJECT_ROOT"
    API_PYTHONPATH="$PROJECT_ROOT"

    if [[ "$API_LIVE_MODE" -eq 1 ]]; then
        local warning="WARNING: API live mode enabled; serving mutable checkout code"
        echo "  $warning" >&2
        printf '%s\n' "$warning" >> "${SVC_LOG[api]}"
        return 0
    fi

    local head_sha origin_main_sha release_dir prune_summary release_line
    head_sha="$(git -C "$PROJECT_ROOT" rev-parse --verify HEAD)"
    origin_main_sha="$(git -C "$PROJECT_ROOT" rev-parse --verify origin/main 2>/dev/null || echo unavailable)"
    echo "  API release source: HEAD $head_sha; origin/main $origin_main_sha"
    release_dir="$(cd "$PROJECT_ROOT" && "$VENV/python" -m scripts.api.release_snapshot build --repo-root "$PROJECT_ROOT" --sha "$head_sha")"
    prune_summary="$(cd "$PROJECT_ROOT" && "$VENV/python" -m scripts.api.release_snapshot prune --repo-root "$PROJECT_ROOT" --keep 3)"
    API_LAUNCH_CWD="$release_dir"
    API_PYTHONPATH="$release_dir"
    release_line="release: $head_sha data-root: $PROJECT_ROOT"
    echo "  $release_line"
    printf '%s\n' "$release_line" >> "${SVC_LOG[api]}"
    echo "  API release prune: $prune_summary"
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

    if [[ "$name" == "api" ]]; then
        # Log rotation check: size > 10MB (10485760 bytes)
        local log_file="${SVC_LOG[$name]}"
        if [[ -f "$log_file" ]]; then
            local size
            size=$(wc -c < "$log_file" | tr -d '[:space:]')
            if (( size > 10485760 )); then
                echo "  api log exceeds 10MB; rotating..."
                rm -f "${log_file}.3"
                [[ -f "${log_file}.2" ]] && mv "${log_file}.2" "${log_file}.3"
                [[ -f "${log_file}.1" ]] && mv "${log_file}.1" "${log_file}.2"
                mv "$log_file" "${log_file}.1"
            fi
        fi

        # Crashloop backoff check: start < 60s ago
        local last_start_file="$PIDS_DIR/${name}.last_start"
        local now
        now=$(date +%s)
        if [[ -f "$last_start_file" ]]; then
            local last_start
            last_start=$(cat "$last_start_file" 2>/dev/null || echo 0)
            local diff=$((now - last_start))
            if (( diff < 60 )) && [[ "$FORCE" -ne 1 ]]; then
                echo "  ERROR: $name started less than 60s ago (diff: ${diff}s); potential crashloop!" >&2
                echo "  Use --force to override this safety guard." >&2
                if [[ -f "$log_file" ]]; then
                    echo "  Last 20 log lines:" >&2
                    tail -n 20 "$log_file" >&2
                fi
                return 1
            fi
        fi
        echo "$now" > "$last_start_file"
    fi

    echo "  Starting $name — ${SVC_DESC[$name]}..."
    if [[ "$name" == "api" ]]; then
        _api_launch_context
        cd "$API_LAUNCH_CWD"
    else
        cd "$PROJECT_ROOT"
    fi

    local pid=""
    if [[ "$name" == "astro" ]] && command -v tmux >/dev/null 2>&1; then
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
        if [[ "$name" == "api" ]]; then
            (
                unset GIT_INDEX_FILE GIT_PREFIX GIT_COMMON_DIR GIT_OBJECT_DIRECTORY
                unset GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE GIT_CEILING_DIRECTORIES
                unset GIT_DISCOVERY_ACROSS_FILESYSTEM
                export LEARN_UK_REPO_ROOT="$PROJECT_ROOT"
                export GIT_DIR="$PROJECT_ROOT/.git"
                export GIT_WORK_TREE="$PROJECT_ROOT"
                export PYTHONPATH="$API_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"
                exec nohup ${SVC_CMD[$name]}
            ) </dev/null >> "${SVC_LOG[$name]}" 2>&1 &
        else
            nohup ${SVC_CMD[$name]} </dev/null >> "${SVC_LOG[$name]}" 2>&1 &
        fi
        pid=$!
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

    rm -f "$PIDS_DIR/${name}.last_start"
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
            if [[ "$svc" == "api" ]]; then
                _reconcile_api_pid
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
            if [[ "$svc" == "api" ]]; then
                _reconcile_api_pid
            fi
            _stop_service "$svc"
            _start_service "$svc"
        done
        echo ""
        _status
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
        _reconcile_api_pid
        _status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|build|clean|rebuild} [service ...]"
        echo ""
        echo "Services:"
        for name in $ALL_SERVICES; do
            printf "  %-12s %s (port %s)\n" "$name" "${SVC_DESC[$name]}" "${SVC_PORT[$name]}"
        done
        echo ""
        echo "Examples:"
        echo "  $0 start                  # Start all"
        echo "  $0 start sources api      # Start specific"
        echo "  $0 start api --live       # Emergency API fallback (mutable checkout)"
        echo "  $0 stop sources           # Stop one"
        echo "  $0 restart                # Restart all"
        echo "  $0 build astro            # Build Astro"
        echo "  $0 clean astro            # Clean Astro cache/build outputs"
        echo "  $0 rebuild astro          # Clean then build Astro"
        echo "  $0 status                 # Show status"
        echo ""
        echo "Note: 'rag' is accepted as a legacy alias for 'sources'; 'site' is accepted as a legacy alias for 'astro'."
        ;;
esac
