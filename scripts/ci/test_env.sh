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

# Print at most the last 200 lines / 32 KiB of a task log, so a huge log can
# never hold the step past its deadline (32 KiB stays well inside a 64 KiB pipe
# buffer, so a stalled reader cannot wedge the reports that follow). The whole
# print also runs under one time bound, so a blocked reader or a slow
# filesystem cannot hold the script either: ~12 s at most per print (#9450).
# A missing log or a failed print must not abort the script.
print_log() {
  if [ ! -f "$1" ]; then
    echo "(no log)"
    return 0
  fi
  local rc=0
  if command -v timeout > /dev/null 2>&1; then
    timeout --kill-after=2 10 bash -c 'tail -c 32768 -- "$1" | tail -n 200' _ "$1" || rc=$?
  else
    # Without coreutils `timeout` only the byte/line bound applies.
    tail -c 32768 -- "$1" | tail -n 200 || rc=$?
  fi
  # 124: timeout fired; 137: it had to SIGKILL the print.
  if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
    echo "(log output truncated: timed out)" >&2
  fi
  return 0
}

# Succeeds only when the task's completion marker holds a whole integer; an
# empty or partial marker means "not finished yet".
rc_ready() {
  [ -f "$dir/$1.rc" ] || return 1
  case "$(cat "$dir/$1.rc" 2> /dev/null)" in
    '' | *[!0-9]*) return 1 ;;
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
      # the runner waits for it before starting the next step. The marker is
      # written to a temp file and renamed, so `wait` never sees it empty.
      (rc=0; run_task "$task" || rc=$?; echo "$rc" > "$dir/$task.rc.tmp" && mv -f "$dir/$task.rc.tmp" "$dir/$task.rc") > "$dir/$task.log" 2>&1 < /dev/null &
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
      while ! rc_ready "$task" && [ "$SECONDS" -lt "$deadline" ]; do sleep 1; done
      if ! rc_ready "$task"; then
        echo "::error::${task} setup did not finish within ${limit}s"
        echo "::group::${task} setup (no exit code yet)"
        print_log "$dir/$task.log"
        echo "::endgroup::"
        status=1
        continue
      fi
      rc="$(cat "$dir/$task.rc")"
      echo "::group::${task} setup (exit ${rc})"
      print_log "$dir/$task.log"
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
