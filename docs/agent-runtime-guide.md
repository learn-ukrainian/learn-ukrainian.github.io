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
    session_id=None,                # None is fresh; an exact bridge identity may resume
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

## Kimi routes and KimiCC headless route

**Native Kimi is the default** interactive and headless/fleet route
(`./start-kimi.sh`, `delegate.py --agent kimi`, bridge). Native **Kimi K3 is
max-only** — the native adapter does not accept a non-max effort ladder for K3.

**KimiCC is bounded explicit opt-in** (`./start-kimicc.sh`,
`start-kimi.sh --harness claude-code`, or runtime `harness=kimicc`). On the
KimiCC route, **K3 defaults to `high`** in interactive and headless/runtime
paths; supported effort overrides must remain observable in telemetry. Do not
weaken the native Kimi registry to match KimiCC.

To opt into Kimi through the headless Claude Code harness, dispatch
`--agent kimi --harness kimicc`. The adapter runs `claude -p --bare` through
`scripts/agent_runtime/kimicc_headless.sh`; that wrapper sources the same
`scripts/lib/kimicc_route.sh` used by `start-kimi.sh --harness claude-code`,
resolves the catalog route, applies the route guard and context profile, then
resolves credentials immediately before `exec`.

For `kimi login` OAuth, headless runs export one fresh token at spawn and never
write `~/.claude` or an isolated Claude config. Kimi access tokens last roughly
15 minutes, so a long-running headless call must be relaunched; unlike the
interactive launcher, this stateless `--bare` route does not install an
`apiKeyHelper` refresh loop.

Ownership matrix, troubleshooting, and seat smoke (including ACPX scope):
[`docs/runbooks/agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md).

## ACPX structured transport (runtime boundary)

ACPX is a **feature-flagged structured invocation transport** — not a
coordination plane and not a replacement for fleet-comms or authoritative file
handoffs. Supported two-seat `discuss` calls use ACPX as their execution
engine; the CLI name remains a compatibility surface. The active path is a
controller-scheduled bounded conversation DAG whose durable state and timeline
are written through existing fleet-comms. The expanded participant registry is
not a new coordination plane.

Approved boundary (#6027, #6043, #6078, #6130, #6158, #6249):

- Feature flag `LU_ACPX_TRANSPORT=off|shadow|active`, **default `off`**.
  `shadow` retains the comparison pilot below. `active` is accepted only by
  the explicit fleet-comms `acp-discuss` controller; it is never a generic
  runner, routing, dispatch, failover, or review setting. Rollback is setting
  the flag to `off` (or unsetting it) and using native transport.
- Direct-only seats cover Codex, Grok, Claude, Kimi, KimiCC K3, Cursor, Pool,
  AGY/Gemini, GLM, and DeepSeek through the fixed registry in
  `scripts/agent_runtime/adapters/acpx.py` (including `acpx-codex-shadow`,
  `acpx-grok-shadow` via `AcpxGrokShadowAdapter`, `acpx-agy-shadow`,
  `acpx-glm-shadow`, and `acpx-deepseek-shadow`). They are never returned by
  `available_agents()` and never become dispatch/routing/review/failover
  candidates.
- The project-local ACPX dependency and every directly invoked provider CLI
  use rolling compatibility contracts. Before each spawn, the adapter probes
  the exact command/flag surface it will invoke; observed versions are
  telemetry, never allowlists. The contracts are `json-one-shot-v1` (ACPX),
  `agent-stdio-v1` (Grok), `text-plan-sandbox-v1` (AGY),
  `native-acp-pure-v1` (OpenCode/GLM), and
  `text-oneshot-isolated-v1` (Hermes/DeepSeek).
- ACPX built-ins are validated at the ACPX boundary (`<seat> exec --file`);
  the project does not duplicate ACPX's responsibility by pinning hidden
  Claude, Kimi, Codex, Cursor, or Pool executables. The project text ACP server
  remains SHA-256 digest-checked before spawn.
- Codex participant:
  `tool_config={"acpx_shadow": True, "target_agent": "codex"}`.
- Grok participant:
  `tool_config={"acpx_shadow": True, "target_agent": "grok"}`.
  Fixed effective model/effort `grok-4.5` / `high`. Custom agent command
  (never built-in `grok-build`): absolute Grok binary +
  `agent --model grok-4.5 --reasoning-effort high --agent-profile
  <hash-pinned-project-no-tool-profile> --no-leader stdio`. The project-owned
  profile is digest-checked before every spawn and removes write, shell,
  subagent, memory, web, MCP, and LSP tools at the Grok server boundary.
- AGY and DeepSeek use `scripts/agent_runtime/acp_text_agent.mjs`: one text
  prompt, source-blind temporary cwd, provider-local sandbox/isolation, and
  cleanup after the turn. GLM uses native `opencode acp --pure` with a fixed
  Z.AI subscription model plus deny-all permissions and disabled tools.
- Adapter safety contract: one in-flight prompt, zero backlog, zero automatic
  prompt retries, bounded timeout/cancellation, required non-empty/bounded
  `task_id`, `correlation_id`, and `idempotency_key` (local runtime metadata
  only — never ACP protocol flags, argv, or stdin; never published to
  fleet-comms, dispatch authority, or review evidence), primary-checkout and
  write-permission refusal. ACPX client confinement and the Grok no-tool
  profile are both required: client flags alone do not remove native Grok
  tools.
- Claude formal sealed reviews expose only the parent-owned
  `sealed_review_read_required` stream. Search, arbitrary file reads, shell,
  and every other evidence tool are denied structurally. Its mandatory stream
  is the hash-bound manifest plus the complete patch, avoiding duplicate
  full-file delivery; reported finding quotes are still verified against the
  exact sealed files before a verdict can pass. A sealed-review-only system
  profile suppresses Claude's incompatible `ReportFindings` handoff and
  requires the canonical JSON verdict in the final ACP assistant message.
- Correlation / shadow telemetry is **evidence only** — the existing participant
  result stays authoritative under shadow compare.
- The only supported comparison caller is
  `scripts.agent_runtime.acpx_pilot`: an explicit worktree-only command that
  runs native first, then one shadow under a global non-blocking lock. It
  suppresses replayed idempotency digests before either call, never queues or
  retries, and persists sanitized classification/parity/duration/token
  aggregates for `GET /api/runtime/acpx`.
- ACPX authentication selection is explicit under `--auth-policy fail`:
  - Codex ChatGPT login: non-secret selector `ACPX_AUTH_CHAT_GPT=1`
  - Grok cached native login: adapter sets `ACPX_AUTH_CACHED_TOKEN=1` and
    scrubs ambient XAI API-key auth selectors (never read/store/log credentials)
- Standard ACP usage reports `used` (tokens currently in context) and `size`
  (context-window capacity). Shadow telemetry records `used`; it must never
  report `size` as consumed tokens.
- **Buzz is deferred** (relay-as-authority conflicts with file dual-write).

### Active ACP conversation: controller-owned and bounded

Only the explicit `acp-discuss` command activates
`LU_ACPX_TRANSPORT=active`, scoped to its controller call and restored on
exit. It accepts a task **on standard input**, never in argv, and schedules
exactly the approved participants: `codex,grok`.

Every supported fleet orchestrator may explicitly select this fixed panel for
one consequential read-only design or risk comparison when direct
cross-provider critique is materially useful. `acp-discuss` is the sole
surface: never invoke it automatically from a launcher or `delegate.py`.
Admission is one conversation repository-wide; `busy` returns immediately with
no queue or automatic retry, and bridge `discuss` is the fallback when ACPX is
busy or unready. A typed partial result is inspectable evidence, not success,
formal review, or coordination authority.

```bash
printf '%s\n' 'Compare the two bounded options and name risks.' |
  ACPX_AUTH_CHAT_GPT=1 \
  .venv/bin/python -m scripts.fleet_comms acp-discuss --cwd . \
  --task-id acp-6078 --correlation-id acp-6078-v1 \
  --idempotency-key acp-6078-v1 --rounds 2 --json
```

The default is two rounds and the hard maximum is three. The DAG runs the
initial Codex and Grok calls in parallel, permits one bounded peer
cross-response per participant, then requires authoritative native-Codex
synthesis. It admits at most two participant calls and five model calls by
default, including synthesis. There are no persistent sessions, tools,
unrestricted loops, hidden failover, or retries. Each model call has a
300-second deadline; the complete conversation has a 1,200-second deadline,
with a reliable-token budget of 160k or a 512 KiB content ceiling.

Idempotency is durable: replay suppression occurs before scheduling and an
orphaned reservation is terminal rather than retried. One single-host,
repository-wide admission file lock is held for the conversation, including
model I/O; no SQLite transaction is held across model I/O. It records typed
partial results and append-only state/timeline events through fleet-comms and
file handoffs, which remain authoritative. The task, participant responses,
credentials, paths, sessions, tool data, and raw model content do not enter
metadata APIs.

The shared primary checkout owns the one project-local ACPX install; dispatch
worktrees resolve that install rather than creating a global copy. The
manifest accepts compatible updates from `0.13.0` onward, while the lockfile
keeps installs reproducible and the runtime capability probe decides whether
the installed version may execute. For E2E/replay verification, run the real stdin-only
`acp-discuss` command once from a registered worktree, then repeat the
identical task, correlation, and idempotency values. The second call must
replay the recorded terminal disposition without scheduling model work.
Finally verify the body-free receipt:

```bash
.venv/bin/python -m scripts.fleet_comms acp-verify \
  --conversation-id conversation_<id> --require-replay --json
```

`verified: true` proves complete participant rounds, native synthesis, and the
replay receipt without reading message bodies. Never reinterpret this check as
permission to retry a failed or partial conversation.

Unless `FLEET_COMMS_ROOT` is explicitly set, fleet-comms storage resolves
through Git's common directory to the primary checkout at
`batch_state/fleet-comms/v1`. A discussion launched from a dispatch worktree
therefore keeps its timeline after that worktree is removed. The SQLite store
uses WAL journaling, full synchronous commits, a bounded busy timeout, and
private owner-only filesystem modes. The standard data-backup run snapshots
this database through SQLite's online backup mechanism and verifies the staged
copy before encrypted retention; do not copy WAL files manually.

Runtime keeps its fleet-facing observability body-free through
`GET /api/runtime/acp/conversations` and
`GET /api/runtime/acp/conversations/{conversation_id}`. The dedicated
Conversations page may additionally call
`GET /api/runtime/acp/conversations/{conversation_id}/transcript` from a direct
loopback connection and loopback URL host. That endpoint returns a bounded
allowlist of inline request, reply, and synthesis text. It sets
`Cache-Control: no-store`, ignores forwarding headers, and exposes no message
IDs, artifact references, hashes, artifact paths, or session metadata as
separate fields.
The body text itself is the conversation and can naturally mention paths or
commands. The page renders each body as inert text and never writes it to
browser storage. It cannot launch, steer, retry, or otherwise control a
conversation. A token field named
`size` is context-window capacity, never consumed-token accounting.

This is deliberation transport, not formal cross-family review. It does not
produce review authority or replace `review-pr` / `publish-review-verdict`.

Do **not** invent ACPX CLI flags, endpoints, or review-eligibility changes in
callers — the adapter's argv is fully confined and callers only ever set
`tool_config` keys the adapter allowlists. Full operator contract:
[`docs/runbooks/agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md).

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
| --- | --- | --- |
| Native interactive task | not controlled by runtime | Resume the native task. Codex retains reasoning and owns compaction; do not rebuild it from visible messages. |
| Bridge `_claude.py` / `_gemini.py` | **yes** | Cache warmth and multi-turn coherence inside the exact bridge identity. |
| Bridge `_codex.py` | **yes** | Preserve native Codex reasoning and compaction for the exact `task_id`; `--new-session` is the explicit reset. |
| Channel inbox | **yes** for resumable agents | Exact `agent + channel + thread_id`; resumed prompts contain only unseen deliveries. |
| Sealed review | **no** | A review checkout is an isolation boundary and must not inherit a normal-worktree session. |
| `/v1/chat/completions` proxy | **no** | Stateless compatibility endpoint; the caller owns and supplies the full message history. |
| `delegate.py` (future, coding tasks) | **no** | Worktree is the isolation boundary. Resume across worktrees is an incoherence footgun. |
| `dispatch.py` pipeline | **no** | Already fresh-session today. Don't regress. |

The runner enforces the boundary: it raises `ValueError` if a caller passes a
session to a `bridge_only` adapter from any entrypoint other than `bridge`, and
always rejects a session for `resume_policy="never"`. Codex turns a permitted
session into `codex exec resume <session-id>`.

Do not infer proxy conversation identity from `user`, model, request ID, or
prompt text. Do not automatically replay ambiguous bridge failures: a
write-capable call may have completed side effects before transport failed.

If you need to change this policy, edit `registry.py`, not the call site.

## Mode vocabulary

Three modes, same meaning across all adapters:

| Mode | Meaning | Typical use |
| --- | --- | --- |
| `read-only` | CLI runs with read-only filesystem sandbox | Consultation, questions, reviews |
| `workspace-write` | CLI can write files in cwd | Coding tasks, refactors, batch fixes |
| `danger` | Sandbox bypassed entirely | Only when explicitly needed (e.g., setup scripts) |

Each adapter declares its `supported_modes` as a frozenset at the class
level. Runner rejects invocations requesting an unsupported mode with
`ValueError`.

`cwd` is **mandatory** for `workspace-write` and `danger`. Runner raises
`ValueError` if missing. This prevents "write to wherever Python happens
to be running" bugs.

## Weak-driver trail isolation (P5)

Trail drivers are never given a shell, workspace writes, GitHub mutation, or
ambient MCP access. A certifiable weak session must use the explicit runtime
profile:

```python
invoke(
    "grok",  # or "kimi" with harness="kimicc"
    prompt,
    mode="read-only",
    cwd=Path.cwd(),
    tool_config={"trail_isolation": True},
)
```

The runner creates a private MCP configuration with exactly one `trail`
server and exactly three visible tools:

| Tool | Parent-owned P3 runner action |
| --- | --- |
| `trail_status` | `trail_runner.py status --run-id …` |
| `trail_step` | `trail_runner.py step --run-id … --expected-step …` |
| `trail_summon` | Reads the `summons` returned by `status`; P3 creates those atomically when it parks a run. |

The MCP server has no generic command, begin, resume, verify-chain, or close
tool. `trail_step` is the only execution request and P3 still validates the
SQLite-authoritative current cursor before it launches the pinned command.

The admission policy is fail-closed:

- Native Grok gets a private MCP cwd, an exact three-tool allowlist, explicit
  allows for those tools, and explicit denies for Bash, reads/writes/edits,
  web, and discovery tools.
- Kimi is eligible only through `tool_config={"harness": "kimicc", "trail_isolation": True}`.
  KimiCC forwards Claude Code's exact `--tools`, `--allowedTools`,
  `--strict-mcp-config`, and empty `--setting-sources` profile.
- Native Kimi, GLM/opencode, Hermes Grok, and every unproven harness refuse
  before spawn. GLM currently ignores tool restrictions, so a refusal is more
  honest than a pretend sandbox.

The boundary prevents accidental weak-driver deviation, not a malicious
process sharing the same Unix account. CI, branch protection, and merge guards
remain required controls.

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

## Runner-level provider failover (#4497)

Provider failover is optional and configured per runtime lane in
`scripts/config/agent_runtime_failover.yaml`. The default file has
`chains: {}`; absent lane chain means `runner.invoke()` keeps the previous
single-route behavior exactly.

Configured chains are ordered route lists:

```yaml
chains:
  deepseek:
    cooldown_ttl_s: 300
    routes:
      - provider: deepseek
        model: deepseek-v4-flash
      - provider: openrouter
        model: qwen/qwen3.6-plus
```

On eligible failures only, the runner marks the failed provider/model/profile
route in a SQLite cooldown store at
`batch_state/agent_runtime_failover_cooldowns.sqlite3` and reinvokes the same
adapter with the next route. Parallel dispatches share that cooldown state.
The next dispatch starts at the first non-cooling route, so a recently dead
primary is not re-probed immediately.

Eligible trigger classes are deliberately narrow: 401/403 auth failure,
429/quota exhaustion, 5xx/overloaded, transport failures such as connection
refused/reset/read timeout, initial-response timeout with no observed output,
stdout-silence timeout before first stdout, and parsed-but-empty responses.
Content-policy refusals, 4xx request-format errors, and mid-stream silence
timeouts after partial output do not fail over.

Every runner-level switch emits the same substitution-shaped payload used by
Hermes fallback surfacing: `requested_provider`, `requested_model`,
`actual_provider`, `actual_model`, `substituted`, `source`, and `marker`.
The payload flows into the usage record, delegate state, telemetry event, and
a loud stderr/logger marker (`AGENT_RUNTIME_FAILOVER_SUBSTITUTION`). Silent
provider/model substitution is forbidden.

v1 adapter coverage:

| Lane | Route override support |
| --- | --- |
| `deepseek`, `qwen`, `grok` | Hermes provider + model via runner route metadata and `--provider` when forced. |
| `agy` | Model override through the existing `--model` mapping; provider is informational unless encoded by the CLI model label. |
| Other adapters | Model-only chains work when the adapter's existing `model` argument can express the route. |

The runner rejects zai/GLM failover targets before launch using the shared
local-only route guard.

## Dispatch worktree layout (#1476)

`delegate.py dispatch --worktree ...` creates the dispatched agent a
private git worktree so its writes are isolated from the main checkout.
Two layouts are currently supported:

| Layout | Path | Status | Triggered by |
| --- | --- | --- | --- |
| **dispatch subtree** (new) | `.worktrees/dispatch/{agent}/{task}/` | **default** for new dispatches | `--worktree` (bare, no path) |
| flat (legacy) | `.worktrees/{agent}-{task}/` | deprecated, still accepted | `--worktree <explicit-path>` under `.worktrees/` |
| custom | anywhere you point it | accepted | `--worktree <explicit-path>` anywhere |

`delegate.py list` and `delegate.py status` print a deprecation notice
when they encounter a flat-layout worktree.

Operator-created non-dispatch worktrees may live alongside these and are **out
of scope** for delegate lifecycle; do not prune or rename them without proving
ownership. `start-codex.sh` itself runs from the canonical `main` checkout and
does not own a persistent worktree. Legacy `.worktrees/codex-interactive/`
checkouts remain protected as operator-created state until explicitly removed.

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

For follow-up work on an existing PR, pass `--branch EXISTING` to
`delegate.py dispatch`. Delegate fetches `origin/EXISTING`, attaches the
worktree to that branch rather than `origin/main`, and applies the same clean
tree / branch-match validation. Staleness and fast-forward are validated
against `origin/EXISTING` itself — never `origin/main`, since a follow-up
worktree is almost always legitimately behind main. It refuses `main`/`master`
and a branch already checked out in another worktree. A branch-reuse
`--dry-run` validates an existing worktree without creating or rebasing one.

Offline fallback: if `git fetch` fails (no network, no remote), delegate
warns on stderr and branches from the local ref. Pin the `--base` flag
to override the default `main`.

### Branch-name normalization (Fix 2 of #1476)

Task-ids that already include the agent name (our common convention:
`codex-1472-foo`) don't produce doubled-prefix branch names. The
normalizer strips a leading `{agent}-` or `{agent}/` before prefixing:

| Agent | Task-id | Branch |
| --- | --- | --- |
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

Telemetry uses `not-exposed` when a CLI genuinely has no effort setting (for
example Agy and Cursor), instead of printing an `unknown` warning on every
dispatch. `unknown` remains reserved for an unexpected resolution failure.
Every terminal state records a concrete subprocess `returncode`, or a
`returncode_reason` when no child process ever yielded one.

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
