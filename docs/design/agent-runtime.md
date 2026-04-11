# Agent Runtime — Design Doc

> **Version:** v1 (post-consultation, 2026-04-10)
> **Status:** APPROVED FOR IMPLEMENTATION pending explicit go-ahead. See v1 changelog at end.
> **Author:** Claude (architect role).
> **Issue:** #1184
> **Related:** #1177 (Codex bridge), #1183 (usage tracker, now superseded by this runtime), and release-notes items #1179–#1182.
> **Consultation provenance:** Codex (msg #28509) and Gemini (msg #28510) reviewed v0 and caught 6+ real bugs. Their findings are incorporated below and posted in full as comments on #1184.

---

## 1. Problem

We have three agents — Claude (architect/reviewer), Gemini (content writer/reviewer), Codex (green team / adversarial reviewer / coding delegate) — and an explicit plan to add more (Grok next, no CLI yet). Today, every coordination path has its own bespoke subprocess logic:

- `scripts/ai_agent_bridge/_codex.py`, `_claude.py`, `_gemini.py` — each builds `codex exec` / `npx claude-code -p` / `gemini -m ... -y` commands from scratch, each handles stdout/stderr capture differently, each has its own error classification.
- `scripts/build/dispatch.py::dispatch_agent` — a second, parallel subprocess implementation for pipeline phases with its own flag-building for `codex`, `codex-tools`, `gemini`, `gemini-tools`, `claude`, `claude-tools`.
- No shared usage tracker. Rate-limit detection is ad hoc where it exists at all.
- No shared stall detection — `_gemini.py` has a `_stream_with_watchdog` prior art at `_STALL_THRESHOLD=120`, but `_claude.py` and `_codex.py` rely on naive `subprocess.run(timeout=N)` that kills healthy processes mid-work.
- Adding a 4th agent (Grok, or anything else) means duplicating all of the above a 4th time.

The Codex integration for issue #1177 already surfaced this pain: Gemini's adversarial review found 6 bugs, 4 of which were "flag X works in non-resume but not resume" or "this env var leaks across subprocesses" — classic signs of per-agent logic that should have been shared from day one.

## 2. Goals

1. **Single runtime, N agents.** Adding a new agent = writing one adapter file + one registry entry. No other code changes.
2. **Shared usage tracking** across every path that invokes any agent CLI (bridge, dispatch, future delegate/consult).
3. **Shared rate-limit detection** with per-agent pattern sets.
4. **Shared stall detection** — streaming stdout watchdog + liveness-file fallback, lifted from `_gemini.py` prior art.
5. **Unified subprocess logic**: timeouts, stdout capture, stderr capture, `-o` output files, worktree cwd, JSON event parsing.
6. **Pluggable agent registry** that captures capabilities, cost tier, default model, invocation flags.
7. **Backward compatible** — existing `ask-gemini`, `ask-claude`, `ask-codex`, and `dispatch.py` callers keep working without changes during migration.
8. **Session resume policy is data-driven and enforced at the caller level**, not the runtime level (see §6.3).

## 3. Non-goals

- Not building a capability benchmark harness in this issue. That's downstream.
- Not building `delegate.py` or `consult.py` in this issue. Those are **consumers** of the runtime and land in follow-up issues.
- Not rewriting the inter-agent message broker (`.mcp/servers/message-broker/`). The runtime is subprocess-level; messaging stays as-is.
- Not touching content pipeline semantics.
- Not touching the user's interactive Claude Code workflow. Session handoffs, `--continue`, autocompact, etc. are unaffected.

## 4. Structure

```
scripts/agent_runtime/
  __init__.py              # 20-line architectural docstring (see §10)
  registry.py              # agent catalog: name → metadata
  usage.py                 # shared per-call usage logger → batch_state/api_usage/
  result.py                # Result + ParseResult dataclasses
  runner.py                # invoke(agent_name, prompt, *, mode, ...) → Result
  adapters/
    __init__.py
    base.py                # AgentAdapter Protocol
    codex.py               # CodexAdapter — wraps `codex exec`
    claude.py              # ClaudeAdapter — wraps `npx @anthropic-ai/claude-code -p`
    gemini.py              # GeminiAdapter — wraps `gemini -m ... -y`
    grok.py                # stub — raises NotImplementedError until Grok CLI exists
    _template.py           # LIVING DOCUMENTATION — reference adapter w/ extensive comments
  errors.py                # RateLimitedError, AgentTimeoutError, AgentStalledError, AgentUnavailableError
  watchdog.py              # stall detection: stdout streamer + mtime poller (§4.6)
```

### 4.1 The Adapter protocol (`adapters/base.py`)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class InvocationPlan:
    """Everything needed to spawn one agent subprocess."""
    cmd: list[str]                # argv list ready for subprocess.Popen
    stdin_payload: str            # prompt to pipe into stdin (or "" if cmd embeds it)
    output_file: Path | None      # if the agent writes final output to a file, its path
    env_overrides: dict[str, str] # merged onto os.environ for THIS subprocess only

@dataclass(frozen=True)
class ParseResult:
    """Rich return from adapter.parse_response — replaces v0's separate protocol methods."""
    ok: bool
    response: str                 # clean text, ready to forward
    stderr_excerpt: str           # first 500 chars of stderr (or output file on error)
    rate_limited: bool            # true if failure was provider rate limiting
    session_id: str | None        # parsed from stdout if the CLI exposes one
    tokens: int | None            # prompt+completion tokens if the CLI exposes them

class AgentAdapter(Protocol):
    name: str                     # "codex" | "claude" | "gemini" | "grok"
    default_model: str
    supported_modes: frozenset[str]  # subset of {"read-only", "workspace-write", "danger"}

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,          # NEW v1 — Gemini #3 (compatibility) + cost data
        tool_config: dict | None,        # NEW v1 — both reviewers (MCP tool restrictions)
    ) -> InvocationPlan: ...

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
    ) -> ParseResult: ...             # v1: one rich dataclass, not three protocol methods

    def liveness_signal_paths(
        self,
        plan: InvocationPlan,
    ) -> list[Path]: ...              # NEW v1 — fallback stall signal when stdout is buffered/redirected
```

Rationale for v1 shape (from consultation):
- **Codex finding #1:** v0 had separate `detect_rate_limit()` + `extract_session_id()` protocol methods. Claude creates session ID *before* launch, Codex parses it *after*, Gemini does neither — one method can't cover three shapes. Collapsed into `ParseResult` as fields.
- **Both reviewers:** `tool_config` must be a protocol input, or `dispatch.py` can't migrate (loses MCP tool restrictions).
- **Gemini finding #3:** `session_id` must be a protocol input, or existing bridge tests break and cache economics collapse for Claude (see §6.3 policy).
- **Cut from v1:** `env_unsets` field and curated base-env (Codex #2). Real concern but rare. Ship `env_overrides` merge-only; add `env_unsets` in v2 if we see an actual leak.

### 4.2 The Runner (`runner.py`)

```python
def invoke(
    agent_name: str,
    prompt: str,
    *,
    mode: str = "read-only",          # {"read-only", "workspace-write", "danger"}
    cwd: Path | None = None,          # subprocess working directory (mandatory for write modes)
    model: str | None = None,         # if None, use adapter.default_model
    task_id: str | None = None,
    session_id: str | None = None,    # caller-level policy enforces when this is set (§6.3)
    tool_config: dict | None = None,  # adapter-specific tool/MCP config
    entrypoint: str = "runtime",      # "bridge" | "dispatch" | "delegate" | "consult" | "runtime"
    hard_timeout: int = 1800,         # wall clock absolute maximum (30 min default)
    stall_timeout: int = 180,         # max time with NO activity before killing (3 min default)
) -> Result:
    """Single entry point for all agent CLI invocations.

    1. Resolves adapter from registry. Raises AgentUnavailableError if unknown/disabled.
    2. Validates mode ∈ adapter.supported_modes. Raises ValueError otherwise.
    3. Validates cwd required for write modes. Raises ValueError otherwise.
    4. Checks usage headroom (has_headroom(agent, model)) — raises RateLimitedError pre-call.
    5. Adapter builds InvocationPlan.
    6. Runner spawns subprocess via Popen + watchdog (§4.6) for stall detection.
    7. On completion: adapter parses response, runner writes usage record, returns Result.
    8. On stall: kills subprocess, writes usage record with outcome="stalled", raises AgentStalledError.
    9. On hard_timeout: kills subprocess, writes usage record with outcome="hard_timeout", raises AgentTimeoutError.
    10. On rate-limit: writes usage record with outcome="rate_limited", updates headroom cache, raises RateLimitedError.
    """
```

### 4.3 Result (`result.py`)

```python
@dataclass(frozen=True)
class Result:
    ok: bool
    agent: str
    model: str
    mode: str
    response: str                # clean text, ready to forward
    stderr_excerpt: str          # v1: renamed from error_excerpt (Gemini #6)
    duration_s: float
    session_id: str | None
    rate_limited: bool
    stalled: bool                # NEW v1 — distinguishes stall from hard timeout
    returncode: int | None
    usage_record: dict           # the record written to usage log
```

### 4.4 Registry (`registry.py`)

```python
AGENTS: dict[str, dict] = {
    "codex": {
        "adapter": "scripts.agent_runtime.adapters.codex:CodexAdapter",
        "default_model": "gpt-5.4",
        "cost_tier": "medium",
        "capabilities": {"code_writing", "code_review", "debugging", "adversarial_review"},
        "cli_available": True,
        "resume_policy": "never",      # §6.3 — Codex is fresh-session-only always
    },
    "claude": {
        "adapter": "scripts.agent_runtime.adapters.claude:ClaudeAdapter",
        "default_model": "claude-opus-4-6",
        "cost_tier": "high",
        "capabilities": {"architecture", "review", "content_a1", "planning"},
        "cli_available": True,
        "resume_policy": "bridge_only", # §6.3 — resume allowed for bridge messaging, forbidden for delegate/dispatch
    },
    "gemini": {
        "adapter": "scripts.agent_runtime.adapters.gemini:GeminiAdapter",
        "default_model": "gemini-3.1-pro-preview",
        "cost_tier": "low",
        "capabilities": {"content_writing", "content_review", "adversarial_review"},
        "cli_available": True,
        "resume_policy": "bridge_only", # §6.3 — same as Claude
    },
    "grok": {
        "adapter": "scripts.agent_runtime.adapters.grok:GrokAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": set(),
        "cli_available": False,         # raises NotImplementedError until real CLI exists
        "resume_policy": "never",
    },
}
```

Capabilities are **informational, not enforced**. The benchmark harness (future issue) will populate real capability scores from evidence.

### 4.5 Usage logger (`usage.py`)

**File layout:**
```
batch_state/api_usage/usage_<agent>-<entrypoint>_YYYY-MM-DD.jsonl
batch_state/api_usage/summary_<agent>-<entrypoint>.json   (rolling daily summary)
```

Examples: `usage_codex-bridge_2026-04-10.jsonl`, `usage_gemini-dispatch_2026-04-10.jsonl`, `usage_claude-delegate_2026-04-10.jsonl`.

The existing `/api/batch/usage` endpoint (`scripts/api/main.py:152`) already reads `summary_*.json` from this directory. **Zero new plumbing required** — dashboards and API consumers pick it up automatically.

**Record schema:**
```json
{
  "ts": "2026-04-10T12:34:56Z",
  "agent": "codex",
  "entrypoint": "bridge",
  "task_id": "issue-1183",
  "cwd": "/Users/.../learn-ukrainian",
  "model": "gpt-5.4",
  "mode": "read-only",
  "session_id": "abc123..." ,
  "duration_s": 42.1,
  "input_chars": 1234,
  "output_chars": 5678,
  "returncode": 0,
  "outcome": "ok",
  "rate_limited": false,
  "stalled": false,
  "stderr_excerpt": null,
  "tokens": null
}
```

Outcome values: `"ok" | "rate_limited" | "stalled" | "hard_timeout" | "error"`. Five distinct categories — fixes the v0 problem of misclassifying slow-but-healthy calls.

**Atomicity — Codex finding #3 (stronger than Gemini #4):**
```python
# NOT this (Python buffered I/O can interleave):
with open(path, "a") as f:
    f.write(json.dumps(record) + "\n")

# But this (kernel-level atomic append, no buffering layer):
import os, json
line = (json.dumps(record) + "\n").encode("utf-8")
fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
try:
    os.write(fd, line)
finally:
    os.close(fd)
```

POSIX guarantees `write(2)` with `O_APPEND` on a regular file < `PIPE_BUF` bytes is atomic across concurrent writers. Our JSONL lines are always < 4KB so we're well inside the guarantee. No `filelock` dependency.

**Headroom check** — Codex finding #7:
```python
def has_headroom(agent: str, model: str) -> tuple[bool, str]:
    """
    Returns (ok, reason). Checks the last 5h of records for (agent, model)
    across all entrypoints. Returns (False, "rate_limited 1h 22m ago") if
    any rate_limit entry within 5h. Scoped by (agent, model), not just
    agent — so a rate limit on gpt-5.4 doesn't block gpt-5.4-mini.
    """
```

**Rate-limit pattern matching** — Gemini finding #5:
```python
_RATE_LIMIT_PATTERNS = (
    r"\b429\b",
    r"\bHTTP 429\b",
    r"\bstatus 429\b",
    r"usage limit reached",
    r"rate limit",
    r"rate_limit",
    r"quota exceeded",
    r"too many requests",
    r"RESOURCE_EXHAUSTED",
    r"No capacity available",
)
# Case-insensitive regex, \b boundaries for bare "429" to prevent URL false positives.
# BONUS: same fix lands in scripts/build/dispatch.py:30 as part of this issue.
```

### 4.6 Stall detection (`watchdog.py`) — NEW in v1

Two complementary signals feed one `last_activity` clock:

**Signal 1 — Streaming stdout watchdog (primary):**
- Runner uses `Popen` (not `subprocess.run`) so stdout is streamable.
- A background thread reads stdout line-by-line; every line bumps `last_activity = monotonic()`.
- Lifted from prior art in `_gemini.py::_stream_with_watchdog` (`_STALL_THRESHOLD=120`).

**Signal 2 — Liveness file mtime polling (fallback):**
- For adapters where stdout is redirected to a file (Codex's `-o <file>`, Gemini's `--output-path`), stdout streaming can't see activity.
- Adapter's `liveness_signal_paths(plan)` returns files the runner should poll mtime on (e.g., `~/.gemini/tmp/learn-ukrainian/chats/<session>.json`, `~/.codex/logs_1.sqlite`, the `-o` output file itself, `~/.claude/projects/.../<session>.jsonl`).
- A second background thread polls these every 5s; `last_activity` is updated when any tracked file's mtime bumps.

**Discovered session file paths per agent:**

| Agent | Path pattern | Update cadence |
|---|---|---|
| Gemini | `~/.gemini/tmp/learn-ukrainian/chats/session-<ts>-<hash>.json` | mtime bumps per message + tool call |
| Codex | `~/.codex/logs_1.sqlite` and the `-o <file>` passed on the command line | continuous during `codex exec` |
| Claude | `~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/<session>.jsonl` | one line appended per tool call / message |

**Runner loop:**
```
1. Spawn subprocess via Popen.
2. Record start_time, last_activity = start_time.
3. Start stdout streamer thread (Signal 1).
4. Start mtime poller thread (Signal 2) with adapter.liveness_signal_paths(plan).
5. Main thread polls proc.poll() every 1s:
     if returncode is not None:         → normal flow (parse, log, return Result)
     elif (now - start_time) > hard_timeout: → kill, log outcome="hard_timeout", raise
     elif (now - last_activity) > stall_timeout: → kill, log outcome="stalled", raise
     else:                              → continue
```

**Bonus: on error, tail the liveness file into the dispatch log.** If a call fails AND the adapter returned liveness paths, the runner reads the last N lines of the newest liveness file and appends them to the error log. Solves the "Gemini failed, stderr was empty" mystery for free.

**Why both layers, not just stdout streaming:** Codex's `codex exec -o <file>` pipes the final message to a file and may emit nothing on stdout for minutes. Pure stdout streaming would kill it as stalled. The mtime fallback catches these cases.

## 5. Migration strategy

Revised order based on Codex and Gemini reviews (both correct in different ways — synthesis follows):

**Phase 1 — Foundation (this issue):**
1. Create `scripts/agent_runtime/` package skeleton.
2. Implement `ParseResult`, `Result`, `InvocationPlan`, errors.
3. Implement `usage.py` with atomic append + headroom check.
4. Implement `watchdog.py` with both signals.
5. Implement `runner.invoke()` end-to-end.
6. Implement `CodexAdapter` first — cleanest existing shape, fastest feedback loop on runner plumbing.
7. Write living adapter `_template.py`.
8. Unit tests for adapter flag building, parse_response, rate-limit detection, usage logger atomicity.
9. Integration test: real `codex exec` smoke call through `runner.invoke()`.
10. Write `docs/agent-runtime-guide.md`.

**Phase 2 — Gemini adapter (pressure test the protocol):**
11. Implement `GeminiAdapter` covering `--allow-write`, `--output-path`, `--extract`, MCP tool config.
12. Confirm `tool_config` contract holds against dispatch.py's Gemini requirements.
13. Confirm stall detection handles the `_stream_with_watchdog` prior art cleanly.

**Phase 3 — Migrate dispatch.py for Codex and Gemini:**
14. Refactor `scripts/build/dispatch.py` Codex and Gemini branches to `runner.invoke()`.
15. Audit MCP tool restrictions preserved (write a test that asserts reviewer dispatch still carries only the reviewer tool list).
16. Run the full pipeline test suite. Any regression = stop and fix.

**Phase 4 — Migrate bridge:**
17. Refactor `_codex.py` and `_gemini.py` onto `runner.invoke()`.
18. Preserve bridge-specific session tracking (the SQLite `sessions` table still owns the `task_id → session_id` mapping; the runner just receives `session_id` as a param).

**Phase 5 — Claude last:**
19. Implement `ClaudeAdapter`.
20. Refactor `_claude.py` and `dispatch.py` Claude branch.
21. Claude is last because (a) it has the most special-case logic (`--bare`, `--session-id`/`--resume` split, background launch mode), and (b) by the time we get here the runner has absorbed every abstraction Codex and Gemini needed — Claude fits whatever shape survived.

**Phase 6 — Cleanup:**
22. Delete dead code from `_codex.py` / `_claude.py` / `_gemini.py` / `dispatch.py`.
23. Update `docs/best-practices/agent-cooperation.md` with the runtime architecture.
24. Update `docs/SCRIPTS.md`.

**Phase 7+ (separate issues, downstream):**
- `scripts/delegate.py` (ad-hoc coding delegation — consumer of runtime)
- `scripts/consult.py` (multi-agent consultation — consumer of runtime)
- Capability benchmark harness
- GrokAdapter once Grok CLI exists

## 6. Design decisions

### 6.1 Protocol vs ABC
Use `typing.Protocol` (structural). Lighter than ABC, no runtime overhead, supports `mypy --strict`. Both reviewers agreed.

### 6.2 Mode vocabulary — `{"read-only", "workspace-write", "danger"}`
Keep these names. They already match the shape the code uses (`_codex.py:16`, `dispatch.py:46`). Gemini said "excellent," Codex agreed with the caveat that `supported_modes` must be real and the runner must reject unsupported modes explicitly. Runner raises `ValueError` if `mode not in adapter.supported_modes`.

### 6.3 Session resume policy — data-driven

**Token-usage data** (`memory/token-usage-insights.md`, `docs/token-usage/token_report.md`):
- 95% of all tokens are cache reads. Cold vs warm cache is where cost concentrates.
- The worst 2-day stretch (Mar 20–21) hit 5.8B tokens and rate-limited the account for a week.
- Top-cost sessions were multi-subagent interactive sessions with cold-cache reloads of SESSION-HANDOFF docs.

**The runtime's impact on cache economics** (Session B in §6.3.1) is different for each provider:

| Provider | Resume saves cost? | Resume causes harm? |
|---|---|---|
| Anthropic (Claude) | **YES** — warm prompt cache reused across bridge calls on same task_id | No — Claude `-p --resume <uuid>` is well-scoped to a session |
| Google (Gemini) | Likely yes (caching mechanics unclear but similar model) | No — multi-turn bridge coherence |
| OpenAI (Codex) | **NO** — Codex quota is per-message, not per-token; resume doesn't save slots | **YES** — resume + `-C` flag limitation = cross-worktree contamination (see Codex's consultation, footgun #5) |

**Policy (enforced in two layers):**

Layer 1 — adapter default (`resume_policy` in registry):
- `CodexAdapter` has `resume_policy="never"` and **ignores `session_id` even if passed**. Belt + suspenders.
- `ClaudeAdapter` / `GeminiAdapter` have `resume_policy="bridge_only"`.

Layer 2 — caller enforcement:
- `_claude.py`, `_gemini.py`, `_codex.py` (bridge messaging) → may pass `session_id` from the existing SQLite `sessions` table.
- `scripts/delegate.py` (future) → hard-refuses to pass `session_id`; asserts runtime-side that `resume_policy != "bridge_only" OR entrypoint != "delegate"`.
- `scripts/build/dispatch.py` → never passes `session_id` (already true today).

#### 6.3.1 Clarification: two different meanings of "session"

**Session A** = the user's interactive Claude Code workflow (this terminal, `--continue`, handoff docs, autocompact). **Unaffected by the runtime.** Keep doing handoffs; they are necessary when context gets heavy. Separate optimization work can shrink handoff docs to reduce cold-reload cost, but that is not this issue.

**Session B** = bridge subprocess `claude -p --resume <uuid>` invocations. **This is what the resume policy above applies to.** Each Session B invocation is a short-lived subprocess that runs for seconds; the UUID lets Anthropic's prompt cache hit across multiple bridge calls on the same `task_id`.

### 6.4 Headroom check semantics
`runner.invoke()` refuses to call an agent that's rate-limited (raises `RateLimitedError` pre-call). Strict refuse is safer; callers that want the retry behavior can catch and handle.

### 6.5 Parallel consultation support
The runner is **synchronous** per invocation. `consult.py` (future) will sequence calls or use `concurrent.futures.ThreadPoolExecutor` around `runner.invoke()`. No `asyncio` in the runtime itself — Gemini's residual risk warning. Keeps the code simple.

### 6.6 Grok stub behavior
Load loudly — `GrokAdapter.build_invocation()` raises `NotImplementedError` with a clear message. The registry flag `cli_available: False` prevents the runner from ever calling it; `runner.invoke("grok", ...)` raises `AgentUnavailableError` immediately. Silent skip would hide configuration errors.

## 7. Vulnerabilities and mitigations

| Vulnerability | Mitigation in v1 |
|---|---|
| Env var leakage between adapters | `InvocationPlan.env_overrides` merged fresh per subprocess; no `os.environ.update()` ever. `env_unsets` deferred to v2 if needed. |
| Concurrent usage log corruption | `os.open(O_APPEND\|O_CREAT\|O_WRONLY) + os.write()` — POSIX atomicity guarantee for sub-PIPE_BUF writes. No filelock. |
| Stall detection missing (kills healthy slow calls) | Streaming stdout watchdog (primary) + `liveness_signal_paths()` mtime polling (fallback). New `"stalled"` outcome distinguishes from hard timeout. |
| Protocol drift as we add agents | `_template.py` living adapter as canonical reference. Protocol tests assert every registered adapter implements the protocol correctly. `mypy --strict` on the `agent_runtime` package. |
| Resume footgun in coding tasks (Codex) | Enforced at two layers: adapter `resume_policy="never"` + caller-side enforcement in `delegate.py` and `dispatch.py`. Codex adapter defensively ignores `session_id` even if passed. |
| MCP tool restrictions lost during migration | `tool_config` in protocol. Phase 3 AC explicitly asserts dispatch.py reviewer paths still carry only the reviewer tool list. Integration test locks this. |
| Cost regression from breaking resume | Data-driven policy: Claude/Gemini bridge paths KEEP resume for cache warmth. Only Codex and delegate/dispatch paths go fresh-only. |
| Future agents add features we can't handle | `tool_config: dict[str, Any]` is deliberately untyped. Adapters ignore keys they don't understand. Forward-compatible. |
| Rate-limit false positives from "429" in URLs | `\b429\b` regex boundaries + specific phrases (`"HTTP 429"`, `"status 429"`). Applied to both new runtime and existing `dispatch.py` as free cleanup. |
| Error signal loss when Gemini call fails with empty stderr | Runner auto-tails the newest liveness file into the error log on failure. Free feature given liveness_signal_paths is already in play. |
| Session B subprocess killed prematurely on stall | Stall detection respects per-call `stall_timeout` (default 180s, Gemini can request higher). Kills only on genuine inactivity. |

## 8. Failure modes still worth watching

1. **Output file races.** If two invocations use the same `-o` temp file, data corrupts. Mitigation: `tempfile.NamedTemporaryFile(prefix=f"{agent}-{task_id}-", suffix=".txt")` — unique per process + monotonic.

2. **Partial writes on SIGKILL.** If the subprocess is killed mid-write, `output_file` contains truncated JSON. Adapter's `parse_response` must detect truncation and classify as error, not partial success. Write a test.

3. **CWD confusion across concurrent invocations.** Adapters MUST pass `cwd=` to `subprocess.Popen`. They MUST NEVER call `os.chdir()`. Enforced by code review and a unit test that asserts `os.getcwd()` is unchanged after `runner.invoke()` returns.

4. **Liveness polling overhead with many paths.** If an adapter returns 10 paths, the mtime poller does 10 stat calls per tick. At 5s tick this is ~2 stats/sec — negligible. But cap the list at 5 paths per adapter.

5. **Usage log disk growth.** JSONL files grow unbounded. Mitigation: daily rotation is automatic (date in filename). Add a monthly rollup script to `summary_*.json` as a follow-up issue, not blocking.

6. **Rate-limit cache staleness.** `has_headroom` reads from disk every call. If we hit a rate limit, call continues normally for the next headroom-check-interval. Mitigation: on first `outcome="rate_limited"` record, runner also updates an in-memory cache so subsequent calls in the same process short-circuit immediately.

## 9. Migration invariants (cross-phase)

These must hold throughout Phase 1–6:

1. **No existing test breaks.** If a test starts failing during refactoring, either (a) fix the refactor to match original behavior, or (b) explicitly document why the behavior intentionally changed and update the test in the same commit.
2. **No silent regression in audit gates.** Content pipeline audit gates (`SELF_REVIEW_DETECTED`, etc.) must continue to detect violations after dispatch.py migration.
3. **No cost regression.** The first post-migration week's token usage must not exceed the pre-migration baseline by >10%. Enforced by comparing `scripts/token_usage.py` output across the migration boundary.
4. **No loss of observability.** Every `runner.invoke()` writes a usage record. No silent calls.
5. **Branch safety.** All writes go to worktrees. `main` is never modified by any agent runtime call.

## 10. Documentation requirements (Phase 1 AC — non-negotiable)

The cost of bad documentation here is specifically what triggered the runtime rewrite in the first place — `dispatch.py` had no mental model doc and I had to re-read it every session. We will not repeat that mistake.

**Four artifacts, all produced in Phase 1:**

1. **`docs/agent-runtime-guide.md`** (NEW, target <200 lines) — single source of truth for humans AND agents. Sections:
   - 30-second mental model
   - "Add a new agent in 20 lines" copy-paste template
   - How `invoke()` flows: adapter → runner → watchdog → usage log
   - Session resume policy table (§6.3)
   - Mode vocabulary (§6.2)
   - Stall detection: how it works, how to tune `stall_timeout`
   - Common mistakes: resume-in-coding-task, env leaks, missing tool_config, cwd=None for write mode
   - A `mypy --strict`-clean example adapter stub

2. **`scripts/agent_runtime/__init__.py`** — 20-line architectural docstring at the top of the package. Anyone opening the package sees the shape before reading a single class.

3. **`scripts/agent_runtime/adapters/_template.py`** — living documentation adapter. Not registered. Extensive inline comments. New adapter authors (human or AI) copy this, not the production adapters.

4. **Cross-references so every agent sees the guide:**
   - `CLAUDE.md` — add to Reference Docs table: `| Agent runtime | docs/agent-runtime-guide.md |`
   - `.gemini/docs/WORKFLOW.md` — auto-loaded into Gemini prompts — append pointer
   - Codex standing rules in `scripts/ai_agent_bridge/_prompts.py::_CODEX_STANDING_RULES` — append pointer: "If a task involves `scripts/agent_runtime/`, read `docs/agent-runtime-guide.md` FIRST"

This is AC #11 on #1184. The guide is shipped in the same PR as the runtime code; no "docs follow later."

## 11. Non-scope (explicit)

- Not touching curriculum content.
- Not touching message broker schema.
- Not adding a GUI.
- Not building the benchmark harness (separate issue).
- Not building delegate.py or consult.py (separate issues).
- Not migrating paths that the current tests don't cover — if a path isn't tested, we add a test before refactoring it.
- Not touching the user's interactive Claude Code session management.

---

## v1 Changelog — changes from consultation (2026-04-10)

**Consultation sources:**
- Codex review: bridge msg #28509 (task `issue-1184-design-review`)
- Gemini review: bridge msg #28510 (task `issue-1184-design-review`)
- User feedback on liveness monitoring and complexity budget
- Token usage data from `scripts/token_usage.py` and `memory/token-usage-insights.md`

**Changes landed in v1:**

| # | Source | Change |
|---|---|---|
| 1 | Codex #5 + Gemini #1 (HIGH) | Added `tool_config: dict \| None` to `build_invocation()` and `runner.invoke()` — would have silently broken dispatch.py MCP tool restrictions |
| 2 | Gemini #3 (HIGH) + cost data | Added `session_id: str \| None` to `build_invocation()` and `runner.invoke()` with per-adapter `resume_policy` + caller-level enforcement |
| 3 | Gemini #2/#5 + user | NEW §4.6 stall detection: streaming stdout watchdog + liveness mtime polling + new `"stalled"` outcome |
| 4 | Codex #1 | Collapsed `detect_rate_limit()` + `extract_session_id()` protocol methods into `ParseResult` dataclass |
| 5 | Codex #3 (stronger than Gemini #4) | Usage log uses `os.open(O_APPEND)` + `os.write()` for kernel-level atomicity, not Python buffered I/O |
| 6 | Gemini #6 | Renamed `Result.error_excerpt` → `Result.stderr_excerpt` for schema consistency |
| 7 | Gemini #5 | Rate-limit patterns use `\b429\b` regex boundaries; applied to both runtime and dispatch.py |
| 8 | Codex + Gemini synthesis | Migration order: Codex adapter → Gemini adapter (hardens protocol) → dispatch.py for both → bridge → Claude last |
| 9 | Codex #7 | Headroom check scoped by `(agent, model)`, not just agent |
| 10 | User feedback | NEW §10 documentation requirements — 4 artifacts shipped in Phase 1, AC-gated |
| 11 | User feedback + both reviewers | NEW §7 vulnerabilities + mitigations table |
| 12 | User feedback (Session A/B clarification) | Added §6.3.1 distinguishing interactive Claude Code sessions from bridge subprocess resume |
| 13 | Token-usage data (HIGH) | §6.3 resume policy is data-driven: Claude/Gemini bridge keep resume for cache warmth, Codex always fresh, delegate/dispatch always fresh |

**Deliberately cut from v1 (ship in v2 if needed):**

- `env_unsets` field on `InvocationPlan` (Codex #2) — real concern but rare. Ship `env_overrides` merge-only; revisit if we see a real leak.
- Parallel/async runner (Gemini residual risk) — `consult.py` can sequence or threadpool around sync runner.
- Rolling monthly usage summaries — separate follow-up issue.

**Open for next round** (not blockers, but worth discussing in the implementation PR):

- Default `stall_timeout` value per adapter. Current proposal: 180s runner default, Gemini adapter may request 300s based on `_STALL_THRESHOLD` history. Decide during implementation.
- Liveness path cap per adapter. Current proposal: 5 paths max. Arbitrary but bounded.
- Token extraction from CLIs. Current proposal: `tokens: null` always in v1, populate when CLIs expose it. Defensible per Gemini, avoids inventing numbers.
