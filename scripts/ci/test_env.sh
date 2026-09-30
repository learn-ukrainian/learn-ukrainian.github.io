#!/usr/bin/env bash
# Overlap the slow parts of a CI pytest shard's setup.
#
#   test_env.sh start TASK...   run each task in the background; they keep
#                               running across workflow steps
#   test_env.sh wait            block until every started task finished, print
#                               its log, and fail if any failed
#
# Tasks:
#   postgres  scripts/ci/start_postgres.sh (bubblewrap, PostgreSQL 16, DSN check)
#   npm       npm ci --ignore-scripts (needs setup-node first)
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"
dir="$RUNNER_TEMP/test-env"

run_task() {
  case "$1" in
    postgres) bash scripts/ci/start_postgres.sh ;;
    npm) npm ci --ignore-scripts ;;
    *)
      echo "unknown task: $1" >&2
      return 2
      ;;
  esac
}

case "${1:-}" in
  start)
    shift
    mkdir -p "$dir"
    for task in "$@"; do
      echo "$task" >> "$dir/tasks"
      # Each subshell always records its exit code (`|| rc=$?` keeps set -e
      # from ending it first) and must not hold the step's stdout/stderr, or
      # the runner waits for it before starting the next step.
      (rc=0; run_task "$task" || rc=$?; echo "$rc" > "$dir/$task.rc") > "$dir/$task.log" 2>&1 < /dev/null &
    done
    ;;
  wait)
    status=0
    while read -r task; do
      while [ ! -f "$dir/$task.rc" ]; do sleep 1; done
      rc="$(cat "$dir/$task.rc")"
      echo "::group::${task} setup (exit ${rc})"
      cat "$dir/$task.log"
      echo "::endgroup::"
      if [ "$rc" != 0 ]; then
        echo "::error::${task} setup failed (exit ${rc}); see its log group above"
        status=1
      fi
    done < "$dir/tasks"
    exit "$status"
    ;;
  *)
    echo "usage: $0 start TASK... | wait" >&2
    exit 2
    ;;
esac
