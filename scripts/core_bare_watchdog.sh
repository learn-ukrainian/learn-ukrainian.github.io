#!/usr/bin/env bash
# Watchdog daemon: continuously asserts core.bare == false on this repository.
# Auto-resets to false if it drifts to true. See #2842.
# Runs completely independently of git work-tree ops, making it resilient
# against the breakage it tries to heal.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting core.bare watchdog for $REPO_DIR"

while true; do
    if [ "$(git -C "$REPO_DIR" config --get core.bare 2>/dev/null)" = "true" ]; then
        git -C "$REPO_DIR" config --local core.bare false 2>/dev/null
        echo "⚠️  watchdog: reset core.bare true→false (git work tree was broken; see #2842)" >&2
    fi
    sleep 5
done
