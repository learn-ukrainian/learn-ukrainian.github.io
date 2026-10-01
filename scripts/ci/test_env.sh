#!/usr/bin/env bash
# Overlap the slow parts of a CI pytest shard's setup.
#
#   test_env.sh start TASK...   run each task in the background; they keep
#                               running across workflow steps
#   test_env.sh wait            block until every started task finished, print
#                               its log, and fail if any failed or did not
#                               finish within TEST_ENV_WAIT_TIMEOUT_S seconds
#                               (default 240, one deadline for the whole call)
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
    # The default must stay below the workflow step timeout (5 minutes) so this bound fires first.
    limit="${TEST_ENV_WAIT_TIMEOUT_S:-240}"
    case "$limit" in
      '' | *[!0-9]* | 0*)
        echo "TEST_ENV_WAIT_TIMEOUT_S must be a positive integer, got: '$limit'" >&2
        exit 2
        ;;
    esac
    # One deadline for the whole call, so a stalled task cannot stretch the
    # step past it (#9450). SECONDS is bash's own elapsed-time counter.
    deadline=$((SECONDS + limit))
    status=0
    while read -r task; do
      while [ ! -f "$dir/$task.rc" ] && [ "$SECONDS" -lt "$deadline" ]; do sleep 1; done
      if [ ! -f "$dir/$task.rc" ]; then
        echo "::group::${task} setup (no exit code yet)"
        cat "$dir/$task.log"
        echo "::endgroup::"
        echo "::error::${task} setup did not finish within ${limit}s"
        status=1
        continue
      fi
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
