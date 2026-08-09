# Intentional background session tasks

Use this pattern only for an operator-owned local service that must outlive the
agent task that launches it: for example, a local teacher app or a deliberately
long-lived diagnostic loop. Ordinary builds, reviews, and `delegate.py wait`
remain harness background tasks and must end with their task.

## Why detachment is required

The dispatch runtime gives each agent invocation a fresh process group. On a
timeout, cancellation, or runner exception, it kills that group so CLI children
cannot leak. The runtime-temp orphan sweep is directory-only: it removes only
dispatcher-owned task leases and never sends a process signal. It must remain
strict.

An intentional child that stays in the invocation's group can therefore be
killed together with the invocation, even when no driver issued `TaskStop` for
that child. The supported escape is a deliberate double-fork plus `setsid`, not
weakening the orphan cleanup.

## Launch contract

Run the helper from a dispatch worktree or the operator's shell. All three
lifecycle paths are required and must be outside a dispatch task's `$TMPDIR`:

```bash
SERVICE_ROOT="/path/to/durable/local-teacher"
SERVICE_LOG="$SERVICE_ROOT/local-teacher.log"
SERVICE_PID="$SERVICE_ROOT/local-teacher.pid"

/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  scripts/tools/detach_session_task.py \
  --workdir "$SERVICE_ROOT" \
  --log-file "$SERVICE_LOG" \
  --pid-file "$SERVICE_PID" \
  -- /bin/bash "$SERVICE_ROOT/start-local-teacher.sh"
```

The command prints the detached PID after the new session is established and
writes the same PID atomically to `--pid-file`. It redirects standard input to
`/dev/null`, appends both output streams to `--log-file`, removes task-scoped
temporary-directory and session-lease variables, resets inherited signal state,
and closes inherited file descriptors. Do not use a `TemporaryDirectory` owned
by the launching task for the service database, invite state, logs, PID file, or
working directory.

The helper refuses to replace a PID file that names a live process. Verify
readiness using the service's normal health endpoint or its explicit completion
notification; do not add a polling loop.

## Stop contract

Only stop the exact recorded service PID after checking it is the expected
process. Remove a stale PID file only after proving the recorded PID is gone.

```bash
SERVICE_PID="/path/to/durable/local-teacher/local-teacher.pid"
pid="$(tr -d '[:space:]' < "$SERVICE_PID")"
ps -p "$pid" -o pid=,command=
kill -TERM "$pid"
```

The detached service is intentionally outside harness lifecycle tracking. Its
operator owns readiness, shutdown, logs, and durable state.
