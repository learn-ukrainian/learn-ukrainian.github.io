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
#   npm       npm ci --ignore-scripts from the setup-node cache, with bounded
#             retries (needs setup-node first)
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"
dir="$RUNNER_TEMP/test-env"

# npm ci revalidates registry data by default and its own fetch timeout (300 s)
# outlives the shared wait deadline, so one registry incident can hang the
# shard. Prefer the restored download cache, skip the registry-only audit/fund
# calls, and own the retries here, inside a budget derived from the same
# deadline `wait` enforces. The budget must leave room for the SIGKILL that
# `timeout --kill-after` may need after a TERM-resistant npm, plus the final
# message write, or a short deadline is reported as "did not finish" while npm
# is still dying. npm's internal retry stack is disabled so the total bound is
# deterministic. Each attempt may use the whole remaining budget, so a slow but
# working cold install still completes; a dead registry returns from the
# per-request fetch cap in time for a bounded retry, and a process-level hang is
# cut off before the shared deadline. Any missing cache entry still comes from
# the registry, but it fails instead of hanging.
npm_install() {
  local limit="${TEST_ENV_WAIT_TIMEOUT_S:-240}"
  case "$limit" in
    '' | *[!0-9]* | 0*) limit=240 ;;
  esac
  # Reserve the termination grace the per-attempt timeout may consume and a
  # margin for the final message. A deadline too short for even one second of
  # install after that reserve fails now, with a typed message, rather than
  # letting the task outlive `wait`.
  local kill_grace=1 report_margin=1
  local reserve=$((kill_grace + report_margin))
  [ "$reserve" -le "$limit" ] || reserve=$limit
  local budget=$((limit - reserve))
  if [ "$budget" -lt 1 ]; then
    echo "npm ci cannot start within the ${limit}s shared wait deadline: ${reserve}s is reserved for termination (${kill_grace}s kill grace) and reporting (${report_margin}s); the registry may be unreachable and the npm cache cold" >&2
    return 1
  fi
  local max_attempts=3
  local start=$SECONDS attempt=0 rc=0 remaining slice fetch_ms backoff
  local -a cmd=(npm ci --ignore-scripts --prefer-offline --no-audit --no-fund --fetch-retries=0)
  while [ "$attempt" -lt "$max_attempts" ]; do
    attempt=$((attempt + 1))
    remaining=$((budget - (SECONDS - start)))
    [ "$remaining" -gt 0 ] || break
    slice=$remaining
    # One dead request must return while a retry still fits; 60 s is far below
    # the 300 s npm default that outlives the deadline.
    fetch_ms=$((slice * 1000))
    [ "$fetch_ms" -le 60000 ] || fetch_ms=60000
    if command -v timeout > /dev/null 2>&1; then
      timeout --kill-after=1 "$slice" "${cmd[@]}" "--fetch-timeout=${fetch_ms}"
      rc=$?
    else
      "${cmd[@]}" "--fetch-timeout=${fetch_ms}"
      rc=$?
    fi
    if [ "$rc" -eq 0 ]; then
      return 0
    fi
    remaining=$((budget - (SECONDS - start)))
    if [ "$attempt" -ge "$max_attempts" ] || [ "$remaining" -le 0 ]; then
      break
    fi
    backoff=$((1 << (attempt - 1)))
    [ "$backoff" -le "$remaining" ] || backoff=$remaining
    echo "npm ci attempt ${attempt}/${max_attempts} failed (exit ${rc}); retrying in ${backoff}s" >&2
    sleep "$backoff"
  done
  echo "npm ci failed after ${attempt} attempt(s) within the ${budget}s install budget (shared wait deadline ${limit}s); the registry may be unreachable and the npm cache cold" >&2
  return 1
}

run_task() {
  case "$1" in
    postgres) bash scripts/ci/start_postgres.sh ;;
    npm) npm_install ;;
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
