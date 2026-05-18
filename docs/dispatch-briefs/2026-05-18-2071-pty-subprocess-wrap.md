# Dispatch brief — Issue #2071: PTY-wrap delegate subprocess spawn (root-cause fix)

**Agent:** Claude (Opus 4.7 xhigh, headless)
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** #2071 — Codex dispatches hang with `response_chars=0`
**Sibling PR (already merged or merging):** #2122 — stopgap bump of
`DEFAULT_SILENCE_TIMEOUT_S` from 1800 to 3600s
**Severity:** HIGH (recurring false-kills on long Codex dispatches;
worktree work lost every time)

---

## Why

When `delegate.py` spawns an agent CLI via `subprocess.Popen(...,
stdout=PIPE, stderr=PIPE)` in `scripts/agent_runtime/runner.py:700`,
the agent's stdout pipe is NOT a TTY. libc inside the agent process
switches stdout to **block-buffered mode** (typically 4-8 KB). The
agent's stream-json events accumulate inside the agent's stdout buffer
and only flush when:

1. The buffer fills, OR
2. The agent process exits, OR
3. The agent explicitly calls `fflush(stdout)` after each write
   (which most don't).

`scripts/agent_runtime/watchdog.py:_stdout_streamer` reads
`proc.stdout.readline()` in a thread. With block-buffered stdout, no
line arrives until the buffer flushes. The watchdog's
`last_stdout_activity` counter doesn't advance. After
`stdout_silence_timeout` seconds (currently 3600s post-#2122, was
1800s previously), the watchdog kills the agent — even though the
agent was actively producing events that were stuck in its own
libc buffer.

**Evidence from tonight's failure** (`adopt-kubedojo-artifacts-20260517-215941`):

- `status=timeout`, `duration_s=1801.57`, `response_chars=0`
- `worktree_dirty_on_exit=true` — Codex modified
  `scripts/api/artifacts_page.py` (new), `scripts/api/docs_router.py`
  (modified), `starlight/src/content/docs/a1/index.mdx` (modified),
  `tests/api/test_artifacts_page.py` (new), and others
- File mtimes show edits between T+8min and T+24min — Codex was
  actively producing tool-call events, but none reached delegate.py

The historical incident chain referenced in
`scripts/agent_runtime/watchdog.py:323-332` (#1184) describes the
identical pattern in Gemini and explicitly names "Gemini block-buffers
stdout when not a TTY" as the root cause. The 2026-04-10 fix at that
time abandoned mtime-poller-based stall detection in favor of pure
stdout-line-watching — which works as long as stdout actually
streams. For block-buffered subprocesses it does not.

**The proper fix is to PTY-wrap the subprocess spawn**, so the agent's
stdout looks like a TTY → libc switches to line-buffering → events
arrive in real time → the watchdog's existing `last_stdout_activity`
logic works correctly without changes.

User direction (2026-05-18 midnight): *"fix this asap pls to run it
under pty, probably it will be needed for other agents as well"* — so
the design must work for all 5 agents (codex, gemini, claude,
deepseek, grok), not just codex.

---

## What you build

### 1. New PTY-wrapped spawn helper in `scripts/agent_runtime/runner.py`

Add a helper function alongside the existing Popen invocation:

```python
def _spawn_pty_subprocess(
    cmd: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    pty_window: tuple[int, int] = (40, 200),  # rows, cols
) -> tuple[subprocess.Popen, int, int]:
    """Spawn cmd in a PTY so stdout/stderr line-buffer naturally.

    Returns (proc, stdout_master_fd, stderr_master_fd).
    The slave fds are closed in the parent after spawn.
    Caller is responsible for closing the master fds when the process exits.

    PTY usage forces the child's libc to detect a TTY and switch from
    block-buffered to line-buffered stdout. Without this, agents that
    write to stdout via stdio (most CLIs) emit no data to the parent
    for minutes at a time, defeating the watchdog's silence-timeout
    detection. See #2071 + watchdog.py:323-332 incident chain (#1184).
    """
    import fcntl
    import os
    import pty
    import struct
    import termios

    stdout_master, stdout_slave = pty.openpty()
    stderr_master, stderr_slave = pty.openpty()

    # Set sane window size so agents that query TIOCGWINSZ for output
    # formatting (e.g. ANSI tables) get reasonable defaults.
    winsize = struct.pack("HHHH", pty_window[0], pty_window[1], 0, 0)
    fcntl.ioctl(stdout_slave, termios.TIOCSWINSZ, winsize)
    fcntl.ioctl(stderr_slave, termios.TIOCSWINSZ, winsize)

    proc = subprocess.Popen(
        list(cmd),
        cwd=str(cwd),
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=stdout_slave,
        stderr=stderr_slave,
        text=False,  # we'll decode after reading from master fds
        start_new_session=True,
    )

    # Parent does NOT need slave fds; close them so EOF arrives on
    # master when child closes its side.
    os.close(stdout_slave)
    os.close(stderr_slave)

    return proc, stdout_master, stderr_master
```

**Replace** the existing `subprocess.Popen(... stdout=PIPE, stderr=PIPE)`
call at runner.py:700-703 with `_spawn_pty_subprocess(...)`. The
function signature change ripples downstream — the watchdog state and
streamer threads need fd handles instead of `proc.stdout` / `proc.stderr`.

### 2. Update watchdog streamer threads to read from PTY fds

In `scripts/agent_runtime/watchdog.py`:

- `_stdout_streamer` currently does `for line in iter(proc.stdout.readline, "")`.
  Change to read from the master_fd: use `os.read(master_fd, 4096)`,
  buffer bytes, split on `\n`, emit lines. The streamer signature
  becomes `_stdout_streamer(master_fd: int, state: WatchdogState)`.
- Same change for `_stderr_streamer` with `stderr_master_fd`.
- Handle `OSError: [Errno 5] Input/output error` (raised when child
  closes its end of the PTY on exit) as a clean shutdown signal —
  identical semantics to today's `for line in iter(...readline, "")`
  ending on EOF.
- The `cleanup_watchdog_streams` helper at watchdog.py:281-300
  currently calls `proc.stdout.close()` + `proc.stderr.close()`. With
  PTY, instead close the master fds via `os.close(master_fd)`. Wrap
  in `with contextlib.suppress(OSError)` because the fd may already
  be closed by the streamer's exception path.

### 3. Update `start_watchdog` signature

Today:

```python
def start_watchdog(
    proc: subprocess.Popen,
    liveness_paths: Iterable[Path],
) -> tuple[WatchdogState, list[threading.Thread]]:
```

After PTY:

```python
def start_watchdog(
    proc: subprocess.Popen,
    *,
    stdout_master_fd: int,
    stderr_master_fd: int,
    liveness_paths: Iterable[Path],
) -> tuple[WatchdogState, list[threading.Thread]]:
```

Caller (runner.py) passes the fds returned by `_spawn_pty_subprocess`.

### 4. Decoding bytes -> str

The streamer reads bytes via `os.read`. Decode lazily with
`bytes.decode("utf-8", errors="replace")` per-line as you append to
`state.stdout_lines` / `state.stderr_lines`. The "errors=replace" is
load-bearing — agent CLIs sometimes emit partial UTF-8 sequences in
ANSI-color escape contexts; raising on decode kills the streamer
silently. Existing tests + behavior expect `list[str]`, not
`list[bytes]`, so this matches.

### 5. ANSI escape stripping (optional but recommended)

PTY-wrapped agents may detect TTY and emit ANSI color codes / cursor
movement sequences. The current code path expects plain stream-json.
Add a small regex-based stripper at the streamer level:

```python
_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
def _strip_ansi(line: str) -> str:
    return _ANSI_RE.sub("", line)
```

Apply once per line before appending to `state.stdout_lines`. Keep it
narrowly scoped — don't try to handle every terminal escape sequence,
just the SGR (color) ones agents commonly emit. If an agent's
stream-json includes literal `\x1b` characters in payload strings,
this stripper will corrupt them — but stream-json by RFC 8259 does
NOT include control chars in payloads (must be escaped as ``),
so this is safe.

### 6. Feature flag for opt-out

Add an env var escape hatch in case PTY breaks some agent we
haven't anticipated:

```python
_DISABLE_PTY = os.environ.get("DELEGATE_DISABLE_PTY", "").lower() in {"1", "true", "yes"}
```

When set, fall back to the pre-PTY pipe-based spawn (keep the old
code path callable as `_spawn_pipe_subprocess`). Default is PTY ON.

Document the env var in `docs/best-practices/harness-engineering.md`
or wherever delegate.py env vars live.

### 7. Tests

Add `tests/agent_runtime/test_pty_subprocess_wrap.py`. Minimum 10 cases:

1. **PTY spawn returns valid fds**: `_spawn_pty_subprocess(["echo",
   "hi"], ...)` returns a `Popen` + two master fds; both fds are
   valid integers; `os.read(master_fd, 1024)` returns `b"hi\r\n"`
   (note `\r\n` — PTYs add carriage returns) or `b"hi\n"` depending
   on termios.
2. **PTY window size set**: after spawn, child sees the configured
   rows/cols via `stty size` — spawn `["stty", "size"]` and assert
   the output matches `f"{rows} {cols}\n"` (after `\r` strip).
3. **EOF on child exit**: child exits → next `os.read(master_fd, ...)`
   raises `OSError: [Errno 5]` or returns `b""`. Streamer must treat
   both as clean shutdown.
4. **Streamer reads block-buffered child output**: spawn a Python
   one-liner that does `import sys, time; print("a"); time.sleep(0.5);
   print("b")` WITHOUT `sys.stdout.flush()`. With pipe-based spawn,
   under block-buffering the watchdog would not see "a" for 30+
   seconds (or until exit). With PTY spawn, the watchdog's
   `last_stdout_activity` advances immediately on "a", before the
   0.5s sleep, before "b".
5. **Streamer handles UTF-8 split across read boundary**: emit a
   multi-byte UTF-8 sequence (`"україна\n"`) split across two
   `os.read` calls of 1 byte each. Streamer must NOT corrupt or drop
   characters.
6. **ANSI escape stripped**: emit `"\x1b[31mhello\x1b[0m\n"` →
   `state.stdout_lines[0] == "hello\n"`.
7. **DELEGATE_DISABLE_PTY env var falls back to pipe spawn**: set
   env var, call wrapper, assert the spawn used pipes (mock both
   spawn paths and assert the right one was hit).
8. **Master fd closed on cleanup**: after `cleanup_watchdog_streams`,
   the master fds are closed (`os.fstat(fd)` raises `OSError:
   [Errno 9]`).
9. **Multiple lines per single os.read call**: PTY delivers 3 lines
   in one read chunk → streamer splits and emits 3 separate entries
   in `state.stdout_lines`.
10. **Streamer thread joins cleanly on child kill**: spawn a sleeping
    child, kill it, assert streamer thread exits within 1s.
11. **End-to-end smoke**: invoke runner.invoke() with a fake adapter
    that runs a Python child producing 10 lines with 0.1s sleeps
    between them and NO explicit flushes. Assert all 10 lines reach
    `state.stdout_lines` within ~1s (proving line-buffering kicked in
    via PTY).

For (4) and (11) the block-buffering behavior is the load-bearing
assertion — if PTY isn't working, those tests fail. They are the
regression guard.

### 8. Per-agent smoke validation (manual but quoted in PR body)

Write a small shell script `scripts/agent_runtime/_smoke_pty_agents.sh`
that fires a 30s no-op dispatch to each of codex, gemini, claude,
deepseek, grok and asserts:

- `response_chars > 0` (output was captured)
- Lines arrived during the run, not just at the end (check
  `last_stdout_activity` from the watchdog state OR check that the
  task json shows the worker produced output before exit)

Quote the per-agent smoke output in the PR body. If any agent
regresses (e.g. PTY makes it hang on TIOCGWINSZ query, or emits
ANSI codes that break stream-json parsing), STOP, document the
regression, and either fix the agent's spawn path specifically OR
default `DELEGATE_DISABLE_PTY` ON for just that agent.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Spawn helper added | `git diff --stat origin/main` showing runner.py + watchdog.py rows |
| Streamer threads read from fds | `git diff scripts/agent_runtime/watchdog.py` showing the `os.read(master_fd, ...)` rewrite |
| New tests pass | `.venv/bin/pytest tests/agent_runtime/test_pty_subprocess_wrap.py -v` final summary raw |
| Existing watchdog/runner tests still pass | `.venv/bin/pytest tests/agent_runtime/ -q` final summary raw |
| Full pytest green | `.venv/bin/pytest tests/ -q` final summary raw (NO `-x` per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/agent_runtime/ tests/agent_runtime/test_pty_subprocess_wrap.py` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed>` raw |
| Per-agent smoke validation | `bash scripts/agent_runtime/_smoke_pty_agents.sh` raw output showing per-agent timestamps + response_chars |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

Branch: `fix/2071-pty-subprocess-wrap`. Path:
`.worktrees/dispatch/claude/2071-pty-subprocess-wrap-<timestamp>/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/agent_runtime/test_pty_subprocess_wrap.py -v
.venv/bin/pytest tests/agent_runtime/ -q
.venv/bin/pytest tests/ -q
.venv/bin/ruff check scripts/agent_runtime/ tests/agent_runtime/
.venv/bin/python -m pre_commit run --files \
    scripts/agent_runtime/runner.py \
    scripts/agent_runtime/watchdog.py \
    tests/agent_runtime/test_pty_subprocess_wrap.py
bash scripts/agent_runtime/_smoke_pty_agents.sh
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: NO `-x` flag.

## Commit + PR

Conventional commit. Title: `fix(runtime): PTY-wrap subprocess spawn
to fix block-buffered stdout hangs (#2071)`. Body covers the root
cause analysis, the PTY mechanism, per-agent smoke results, and
quotes the verifiable-claims raw outputs.

NO `--auto-merge`. Leave the PR open; orchestrator merges after CI
green.

## Out of scope

- Don't change adapter-level behavior (each agent's adapter at
  `scripts/agent_runtime/adapters/*.py` stays as-is — they construct
  the CLI command, the PTY change is at the spawn layer).
- Don't change watchdog's kill logic, mtime poller, or
  `last_stdout_activity` semantics. The PTY change is purely about
  making the existing watchdog logic SEE the data it expected.
- Don't bump `DEFAULT_SILENCE_TIMEOUT_S` back down to 1800 — leave
  the #2122 stopgap in place as belt-and-suspenders. After 1 week of
  green PTY operation we can revisit, but not in this PR.
- Don't add PTY-specific monitoring (file descriptor count metrics,
  etc.) — separate concern, file a follow-up if needed.
- Don't change Windows compatibility shim — delegate.py is POSIX-only
  in practice; if Windows support is ever added, PTY needs alternative
  (`pywinpty` or named pipes). Document the limitation in a code
  comment near `_spawn_pty_subprocess`.

## Anti-fabrication

If anything in this brief surprises you when you actually read the
code:

- the spawn site is not at runner.py:700 (the line could have
  shifted)
- `start_watchdog` takes a different signature than described
- the watchdog already has PTY handling (very unlikely but check)
- the agent CLIs reject TTY input for stream-json (some have a
  `--non-interactive` flag that would need to be passed to keep
  stream-json output stable in PTY mode)

STOP and quote the surprise verbatim before patching. Don't paper over.

If `pty.openpty()` is unavailable on the target platform (the
codebase MAY hit Linux containers via Dagger), the PTY path must
fail-soft: catch the `OSError` / `AttributeError` and fall back to
the pipe spawn with a logged warning. Don't crash the whole runner.

If a specific agent's CLI emits problematic data in PTY mode (most
likely culprits: ANSI color codes confusing stream-json parser; or
the CLI explicitly checks `os.isatty(0)` for stdin and disables
non-interactive mode), document the regression in the PR body and
set `DELEGATE_DISABLE_PTY=1` per-adapter as a temporary workaround
while filing a follow-up issue for the agent-specific fix.

---

## Notes for orchestrator (Claude, not Claude-the-dispatched)

* Pre-June-15 Claude dispatch lane still available (budget doubled
  until mid-July per MEMORY #0). After June 15, this brief would
  need to dispatch to Codex instead — note in PR description for
  future reference.
* Dispatch CAP usage at fire time: 2/2 Codex (kubedojo timed out
  T-30, PR3 in flight), 1/2 DeepSeek, 1/2 Gemini. Claude lanes
  free — this brief is the right home.
* Estimated duration: 60-90 min (substantial refactor + tests +
  per-agent smoke). Hard timeout 5400s should be enough; if PTY
  smoke takes longer, the dispatch can request more time in its PR.
* On PR finalize: read the per-agent smoke section carefully — if
  any agent regressed, the merge is held until the regression has a
  documented workaround.
