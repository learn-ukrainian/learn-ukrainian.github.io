#!/bin/bash
# Self-healing dispatcher wrapper.
# Restarts automatically on crash. Cleans stale locks before each start.
# Usage: nohup ./run-dispatcher.sh > dispatcher.log 2>&1 &

cd "$(dirname "$0")"
MAX_HOURS=72
RESTART_DELAY=10

echo "=== Dispatcher wrapper started at $(date) ==="
echo "  Max runtime: ${MAX_HOURS}h | Restart delay: ${RESTART_DELAY}s"

drop_unneeded_dispatcher_secrets() {
    local name names
    if ! names="$(.venv/bin/python scripts/agent_runtime/env_sanitize.py --provider dispatcher)"; then
        echo "dispatcher secret sanitizer failed; refusing to start" >&2
        return 1
    fi
    while IFS= read -r name; do
        case "$name" in
            ''|*[!A-Za-z0-9_]*) continue ;;
        esac
        unset "$name"
    done <<< "$names"
}

while true; do
    # Clean stale locks before each run
    rm -f batch_state/locks/*.lock 2>/dev/null
    drop_unneeded_dispatcher_secrets || exit 1

    echo ""
    echo "=== Starting dispatcher at $(date) ==="
    .venv/bin/python scripts/batch_dispatcher.py run --max-runtime-hours "$MAX_HOURS"
    EXIT_CODE=$?

    echo "=== Dispatcher exited with code $EXIT_CODE at $(date) ==="

    # Exit code 0 = normal completion (all done or max runtime)
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Clean exit. Stopping wrapper."
        break
    fi

    echo "Crash detected. Restarting in ${RESTART_DELAY}s..."
    sleep "$RESTART_DELAY"
done

echo "=== Wrapper finished at $(date) ==="
