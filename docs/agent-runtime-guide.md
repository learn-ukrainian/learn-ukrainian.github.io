# Agent Runtime Guide

> **Read this before touching `scripts/agent_runtime/`.** It's the 200-line
> mental model you need to avoid repeating the dispatch.py mess we built
> the runtime to replace.
>
> Full design rationale: [`docs/design/agent-runtime.md`](design/agent-runtime.md). Issue: [#1184](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1184).

## What it is (30 seconds)

One package — `scripts/agent_runtime/` — that every path invoking an agent
CLI routes through. Replaces four duplicated subprocess + flag-building
copies across `_codex.py`, `_claude.py`, `_gemini.py`, and `dispatch.py`.
Adding a new agent = one new adapter file + one new registry entry.

## The one entrypoint

```python
from agent_runtime.runner import invoke

result = invoke(
    "codex",                        # agent name from registry.AGENTS
    "Please do X",                  # prompt
    mode="read-only",               # "read-only" | "workspace-write" | "danger"
    cwd=Path.cwd(),                 # MANDATORY for write modes
    model=None,                     # None → adapter.default_model
    task_id="issue-1183",           # optional, logged
    session_id=None,                # forbidden for Codex always
    tool_config=None,               # MCP / tool restrictions
    entrypoint="bridge",            # "bridge" | "dispatch" | "delegate" | "consult" | "runtime"
    hard_timeout=1800,              # 30 min wall clock max
    stall_timeout=180,              # 3 min silence → killed as stalled
)
# result.ok, result.response, result.duration_s, result.session_id, etc.
```

No other subprocess building anywhere else in the codebase. If you find
yourself writing `subprocess.Popen([..., "claude", ...])` — stop. Use
`runner.invoke()`.

## Add a new agent in 20 lines

1. Copy `scripts/agent_runtime/adapters/_template.py` to `adapters/youragent.py`.
2. Rename the class, fill in `name`, `default_model`, `supported_modes`.
3. Implement `build_invocation`, `parse_response`, `liveness_signal_paths`.
4. Add an entry to `registry.AGENTS` with `cli_available: True`.
5. Write unit tests mirroring `tests/test_agent_runtime.py`.

Done. The runner handles everything else: stall detection, usage logging,
rate-limit headroom checks, mode validation, cwd enforcement.

## Session resume policy — the rule that matters

| Path | Resume? | Why |
|---|---|---|
| Your interactive Claude Code | not affected by runtime | Keep `--continue`, handoffs, etc. The runtime doesn't touch your session. |
| Bridge `_claude.py` / `_gemini.py` | **yes** | Cache economics — 95% of our tokens are cache reads. Dropping resume here would reproduce the 2026-03-21 cost fiasco (5.8B tokens in 2 days, rate-limited for a week). |
| Bridge `_codex.py` | **no** | Codex quota is per-message, not per-token. Resume saves nothing. And cross-worktree session carry-over is the #1 footgun (Codex's own warning, msg #28506). |
| `delegate.py` (future, coding tasks) | **no** | Worktree is the isolation boundary. Resume across worktrees is an incoherence footgun. |
| `dispatch.py` pipeline | **no** | Already fresh-session today. Don't regress. |

Enforced at TWO layers:
1. **Adapter-level** (defensive): `CodexAdapter.build_invocation()` ignores `session_id` even when passed. Belt.
2. **Caller-level** (declarative): `runner.invoke()` raises `ValueError` if the caller's `entrypoint` is not "bridge" and the adapter's `resume_policy` is "bridge_only", or always if `resume_policy` is "never". Suspenders.

If you need to change this policy, edit `registry.py`, not the call site.

## Mode vocabulary

Three modes, same meaning across all adapters:

| Mode | Meaning | Typical use |
|---|---|---|
| `read-only` | CLI runs with read-only filesystem sandbox | Consultation, questions, reviews |
| `workspace-write` | CLI can write files in cwd | Coding tasks, refactors, batch fixes |
| `danger` | Sandbox bypassed entirely | Only when explicitly needed (e.g., setup scripts) |

Each adapter declares its `supported_modes` as a frozenset at the class
level. Runner rejects invocations requesting an unsupported mode with
`ValueError`.

`cwd` is **mandatory** for `workspace-write` and `danger`. Runner raises
`ValueError` if missing. This prevents "write to wherever Python happens
to be running" bugs.

## Stall detection — why we don't kill healthy slow calls

Previous code used `subprocess.run(timeout=N)` and killed anything that
didn't return in N seconds. That killed healthy slow calls (VESUM
verification of 50 words, multi-file reviews) as often as actually stuck
ones. The runner replaces that with **two-layer stall detection**:

1. **Stdout streamer (primary).** A background thread reads stdout
   line-by-line and bumps `last_activity` on every line. Works for any
   agent that talks to stdout. Lifted from prior art in
   `_gemini.py::_stream_with_watchdog`.
2. **Liveness file mtime poller (fallback).** For agents that buffer
   stdout or write final output to a `-o <file>` (Codex), the adapter
   returns paths in `liveness_signal_paths(plan)`. A second thread polls
   mtimes every 5s; any bump is treated as activity.

Both signals feed ONE `last_activity` clock. Runner kills only when:
- `now - last_activity > stall_timeout` → `AgentStalledError`
- `now - start_time > hard_timeout` → `AgentTimeoutError`

Distinct exception types so callers can handle them differently. The
usage record carries the outcome as `"stalled"` or `"hard_timeout"`
(NOT collapsed into generic "error") so metrics stay honest.

Defaults: `stall_timeout=180` (3 min), `hard_timeout=1800` (30 min).
Override per-call when you know the workload needs more.

## Usage logging — zero new plumbing

Every `runner.invoke()` call writes exactly one JSONL record to:
```
batch_state/api_usage/usage_<agent>-<entrypoint>_YYYY-MM-DD.jsonl
```

Schema and atomicity details in `scripts/agent_runtime/usage.py`. Key
points:

- **Atomic append**: `os.open(O_APPEND|O_CREAT|O_WRONLY) + os.write()`.
  Bypasses Python's buffered I/O entirely. POSIX guarantees atomicity
  for sub-PIPE_BUF writes, so concurrent callers never interleave lines.
  No `filelock`.
- **Reuses existing `/api/batch/usage` endpoint** at `scripts/api/main.py:152`.
  The endpoint reads `batch_state/api_usage/summary_*.json` — we write
  matching files automatically and dashboards pick them up for free.
- **Rate-limit headroom check**: `has_headroom(agent, model)` scans the
  last 5h of records scoped by `(agent, model)` and returns `False` if
  any record has `outcome: "rate_limited"`. Runner calls this pre-call
  and raises `RateLimitedError` before burning a quota slot on a
  known-rate-limited call.

## Dispatch worktree layout (#1476)

`delegate.py dispatch --worktree ...` creates the dispatched agent a
private git worktree so its writes are isolated from the main checkout.
Two layouts are currently supported:

| Layout | Path | Status | Triggered by |
|---|---|---|---|
| **dispatch subtree** (new) | `.worktrees/dispatch/{agent}/{task}/` | **default** for new dispatches | `--worktree` (bare, no path) |
| flat (legacy) | `.worktrees/{agent}-{task}/` | deprecated, still accepted | `--worktree <explicit-path>` under `.worktrees/` |
| custom | anywhere you point it | accepted | `--worktree <explicit-path>` anywhere |

`delegate.py list` and `delegate.py status` print a deprecation notice
when they encounter a flat-layout worktree.

Two non-dispatch worktrees live alongside these and are **out of scope**
for delegate lifecycle — don't prune or rename:
- `.worktrees/codex-interactive/` — the persistent interactive session
  from `start-codex.sh` (detached HEAD, symlinks to `.venv`, `data/`,
  `starlight/node_modules`).
- Any operator-created `.worktrees/*` that predates the dispatch layout.

### Stale-base safety (the actual #1476 bug)

Before creating or reusing a worktree, `delegate.py` runs
`git fetch origin <base>` and branches from `origin/<base>`, not local
`<base>`. The local ref drifts the moment a PR merges while a dispatch
is queued — the resulting worktree would miss any commits landed in the
gap. This is what shipped PRs #1473 and #1474 against stale tips
(2026-04-23).

When a worktree is reused, it is validated:
1. **Branch match** — must be on the expected derived branch
   (`{agent}/{task_normalized}`). Mismatch → `WorktreeBranchMismatch`.
2. **Clean tree** — no uncommitted changes. Dirty → `WorktreeDirty`.
3. **Base freshness** — at most 0 commits behind `origin/<base>`; if
   behind, attempt `git rebase origin/<base>` and raise
   `WorktreeStaleBase` if that fails.

Offline fallback: if `git fetch` fails (no network, no remote), delegate
warns on stderr and branches from the local ref. Pin the `--base` flag
to override the default `main`.

### Branch-name normalization (Fix 2 of #1476)

Task-ids that already include the agent name (our common convention:
`codex-1472-foo`) don't produce doubled-prefix branch names. The
normalizer strips a leading `{agent}-` or `{agent}/` before prefixing:

| Agent | Task-id | Branch |
|---|---|---|
| codex | `codex-1472-foo` | `codex/1472-foo` |
| codex | `codex/1472-foo` | `codex/1472-foo` |
| codex | `1472-foo` | `codex/1472-foo` |
| codex | `random-name` | `codex/random-name` (no strip — `random` ≠ `codex`) |
| claude | `claude-bar` | `claude/bar` |

### Dispatch telemetry (Fix 5 of #1476)

The state file at `batch_state/tasks/<task-id>.json` now carries:
- `worktree_path`, `worktree_branch`, `worktree_layout` (`flat` | `dispatch` | `external`)
- `worktree_base`, `worktree_base_sha` — resolved at dispatch start
- `worktree_rebased`, `worktree_reused` — reuse-path telemetry
- `worktree_dirty_on_exit` — whether the agent left uncommitted changes

`delegate.py list` surfaces `worktree_layout`; `delegate.py status`
prints a deprecation notice for flat-layout tasks.

## Common mistakes

- **Writing new subprocess logic outside the runtime.** If you're
  calling an agent CLI, route through `runner.invoke()`. The moment you
  build a second `subprocess.Popen([...])` for an agent, you've
  reintroduced the thing we deleted.
- **Passing `session_id` to `delegate.py` calls.** Coding tasks are
  ALWAYS fresh-session. The runner will raise `ValueError` at you.
- **Omitting `cwd` for write-mode calls.** Runner raises `ValueError`.
  Even if it worked, every write-mode call needs a pinned cwd to
  prevent cross-worktree contamination.
- **Swallowing `RateLimitedError` silently and retrying.** Don't. The
  headroom system exists so you don't waste quota. Back off, wait, try
  later. If you need automated backoff, build it on top of the runner,
  not by catching-and-retrying in-place.
- **Mutating `os.environ` in an adapter.** Use `InvocationPlan.env_overrides`
  instead. The runner merges it onto a fresh dict per subprocess — no
  leakage to other adapters running concurrently.
- **Calling `os.chdir()` anywhere.** Pass `cwd=` to `subprocess.Popen`.
  The runner already does this.
- **Inventing token counts.** If your CLI doesn't expose tokens, return
  `tokens=None` from `parse_response`. Making up numbers pollutes the
  cost dashboards.

## Tests — where they live

- `tests/test_agent_runtime.py` — adapter unit tests, runner behavior,
  mode/cwd/resume validation, watchdog logic.
- `tests/test_claude_version.py` — version-gate helper for
  `scripts/utils/claude_version.py` (not strictly runtime but closely
  related).
- Integration smoke tests (real CLI invocations) live alongside unit
  tests but are marked with a fixture to skip when the CLI isn't
  installed.

Run them all: `.venv/bin/python -m pytest tests/test_agent_runtime.py tests/test_claude_version.py`.

## When in doubt

1. Re-read the Session Resume Policy table — that's where the most
   expensive mistakes happen.
2. Check `docs/design/agent-runtime.md` § 7 Vulnerabilities for the
   specific failure mode you're worried about.
3. Read `_template.py` — it's the "add an agent in 20 lines" living doc.
4. Look at how `CodexAdapter` does it — it's the reference production
   adapter.

---

*Last updated: 2026-04-23 (#1476 dispatch hardening: fetch-before-branch,
reuse validation, branch normalization, dispatch/ subtree layout).
When behavior changes, update this guide in the same commit. This file
is also auto-loaded into Gemini and Codex prompts via the bridge — keep
it accurate.*
