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

Kimi models are retired (OO-58, #11327). Dispatch, substitution, launchers and
the bridge refuse every Kimi id. Short names still resolve so the refusal can
name the catalog id. There is no default interactive route and no KimiCC opt-in.

The admission gate still runs first on a Kimi request. Asks, consults,
discussions, reviews, trail sessions and read-only or danger modes raise the
coding-only refusal before the catalog retirement is reached. An admitted
workspace-write then hits the retired-model refusal and does not plan a launch.
Ukrainian-content checks in `scripts/agent_runtime/kimi_admission.py` remain on
that path; they are not a way to send work. A diff that would have been a Kimi
commit still fails closed with `kimi_content_refusal` when it adds Cyrillic.

Targets are admitted in the same step they are resolved:
`scripts/agent_runtime/target_admission.py` `resolve_and_admit` performs every
resolution a request goes through (explicit recipients and model, `data`
attachments, compat names, ACP route pins, slot holders, registry lookups,
quota substitution) and then runs the Kimi gate. Delivery, insertion, wake and
launch sinks in the bridge, channels, ACP, fleet-comms and `dispatch.py` take
the `AdmittedTarget` it returns, never a raw name, and the resolvers are
called from that module only (`tests/test_target_admission_structure.py`).

Do not dispatch `--agent kimi` or start `start-kimi.sh` / `start-kimicc.sh`.
The historical headless Claude Code harness (`kimicc_headless.sh`) is not an
opt-in. Catalog retirement runs after admission and before a launch plan.

Ownership matrix, troubleshooting, and seat smoke (including ACPX scope):
[`docs/runbooks/agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md).
Claude through AGY supports the existing `claude-sonnet-5-5-high` and
`claude-opus-5-5-high` pins for implementation in verified dispatch worktrees.
Sonnet remains excluded from security work. The dispatch keeps the requested
selector separate from the provider-reported initialization identity, including
same-run provenance through failure and cancellation. Missing or invalid
identity cannot establish successful Claude dispatch. Review permissions and
formal-review eligibility remain separate. Per-variant stop conditions and
post-merge driver qualification:
[`docs/runbooks/agy-claude-routes.md`](runbooks/agy-claude-routes.md).

## ACPX structured transport (runtime boundary)

ACPX is a **feature-flagged structured invocation transport** — not a
coordination plane and not a replacement for fleet-comms or authoritative file
handoffs. Supported 2-to-4-seat `discuss` calls use ACPX as their execution
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
- Direct-only seats cover Codex, Grok, Claude, Cursor, Pool,
  AGY/Gemini, GLM, Gemma, and DeepSeek (the registry still names the Kimi and KimiCC seats, but `kimi_admission` refuses them before any side effect) through the fixed registry in
  `scripts/agent_runtime/adapters/acpx.py` (including `acpx-codex-shadow`,
  `acpx-grok-shadow` via `AcpxGrokShadowAdapter`, `acpx-agy-shadow`,
  `acpx-glm-shadow`, `acpx-gemma-shadow`, and `acpx-deepseek-shadow`). They
  are never returned by
  `available_agents()` and never become dispatch/routing/review/failover
  candidates.
- The project-local ACPX dependency and every directly invoked provider CLI
  use rolling compatibility contracts. Before each spawn, the adapter probes
  the exact command/flag surface it will invoke; observed versions are
  telemetry, never allowlists. The contracts are `json-one-shot-v1` (ACPX),
  `agent-stdio-v1` (Grok), `text-plan-sandbox-v1` (AGY), and
  `native-acp-pure-v1` (OpenCode — GLM, Gemma, and DeepSeek since the Hermes
  removal, #6805). The Hermes `text-oneshot-isolated-v1` contract remains
  only for legacy direct-Hermes resolution errors.
- ACPX built-ins are validated at the ACPX boundary (`<seat> exec --file`);
  the project does not duplicate ACPX's responsibility by pinning hidden
  Claude, Kimi, Codex, Cursor, or Pool executables. The project text ACP server
  remains SHA-256 digest-checked before spawn.
- Codex participant:
  `tool_config={"acpx_shadow": True, "target_agent": "codex"}`.
- Grok participant:
  `tool_config={"acpx_shadow": True, "target_agent": "grok"}`.
  Fixed effective model/effort `grok-4.7` / `high`. Custom agent command
  (never built-in `grok-build`): absolute Grok binary +
  `agent --model grok-4.7 --reasoning-effort high --agent-profile
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
surface: never invoke it automatically from a launcher or `dispatch.py`.
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
initial participant calls in parallel (two to four seats), permits one bounded peer
cross-response per participant, then requires authoritative native-Codex
synthesis. Each round calls every participant once. The default two-seat,
two-round panel is five model calls including synthesis. There are no persistent sessions, tools,
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
produce review authority or replace formal cross-family review (sealed `review-pr` / `publish-review-verdict` removed in #8520).

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

## Reviewer findings schemas

Quality-gate callers use `scripts.audit.llm_reviewer.invoke_reviewer_with_schema`.
`scripts/audit/qg_schema.py` defines the authoritative `dimension`, `direct`, and
`audit` wire profiles. They preserve the existing field meanings and scoring
taxonomies. The audit prompt, both per-dimension templates (including the
generator-fed template), and the direct-review template render their output
contracts from these definitions. `prompt_builder.py` registers the generator's
`REVIEWER_OUTPUT_SCHEMA` token; rubric and writer rules remain separate.

The caller writes an invocation-owned schema file, passes its absolute
`output_schema_path` and exact `output_schema_sha256` in `tool_config`, and keeps
it alive until the runtime returns. Adapters verify the digest before spawn and
retain the schema on that invocation's plan for result validation:

| Native harness | Flag | Authoritative result |
| --- | --- | --- |
| Claude | `--json-schema <JSON>` | Final `result` event's `structured_output`, with `subtype=success` and `is_error=false` |
| Codex | `--output-schema <FILE>` | This invocation's `-o` file, after successful process exit |
| AGY | `--output-format json --json-schema <JSON>` | `structured_output` in the JSON envelope with `status=SUCCESS` |
| Grok | `--json-schema <JSON>` with JSON output | `structuredOutput` in the final envelope with `stopReason=end_turn`, without `structuredOutputError` |

### AGY pending supervisory orders

The `pending-orders-announce` overlay runs
`scripts/agy_hooks/pending_orders_inject.sh` on every `PreInvocation`,
independently of `driver-state-pin`. It uses the launcher's
`SESSION_HANDOFF_AGENT` registered slot, including worker slots, and injects
`{"injectSteps":[{"ephemeralMessage":"PENDING ORDERS: ..."}]}` before
the next model call. It never falls back to the `claude` inbox.

`scripts.inbox_pending` opens the configured legacy broker and Fleet Comms
authority SQLite stores read-only. It counts unacknowledged, non-live-consumed
legacy messages and queued or running authority deliveries without durable
generation-bound supervisory consumption or an expired deadline. A consumed
wake receipt records receiver observation and leaves the order pending.
Output contains counts, at most five full message IDs, a truncation flag,
per-store counts and `probe: ok|unknown`.
No body is selected, and no delivery is claimed, consumed or acknowledged.

Legacy recipients follow the bridge inbox policy: resolve the roster alias,
then include permanent seat read aliases. The launcher's `monitor`,
`infra.monitor`, `ops-api`, `ops.api` and `operator-api` selectors all use the
monitor lane. With a readable registry containing registered slots, an empty
monitor area maps `gemini-monitor` to `gemini` in the legacy projection; a
dedicated registered slot reads only its own recipient set. An entirely empty
or unreadable roster returns unknown. Authority publish and claim use exact
recipient names without that roster resolver. For example, `gemini-monitor`
remains `gemini-monitor` in authority deliveries. The probe checks existing
authority admission and returns unknown if admission is unavailable or changes
the recipient. It never uses a legacy empty result to prove authority emptiness.

A proven empty inbox returns `{}`. Pending orders are re-announced on replay
until acknowledged or consumed. The injected line is at most 200 characters;
it includes as many full IDs as fit and marks truncation. A `legacy:` pointer
names `ai_agent_bridge inbox --for` with the resolved legacy recipient. Legacy
stores are read-only migration projections in authority mode; the notice does
not recommend legacy acknowledgement writes. An `authority:` pointer names
`.venv/bin/python -m scripts.fleet_comms deliveries --help`, the existing fenced
delivery workflow. Both pointers appear when both stores have pending work.
The authority workflow uses delivery IDs returned by claim, the lease owner's
worker ID and fence token, and a driver generation for supervisory consumption.
Use the exact `SESSION_HANDOFF_AGENT` for the workflow's `--recipient` argument.
Announcement message IDs are not legacy integer ack IDs or authority delivery
IDs. The hook only prints guidance; it never executes this workflow. In a linked
worktree, run the documented help with the prescribed shared project interpreter.
Missing or unreadable stores, invalid hook JSON,
an invalid or missing slot, and interpreter failures inject `PENDING ORDERS:
unknown` with exit 0. Hook input and output are never written to temporary files.

Deploy the canonical overlay with `npm run agents:deploy`, which copies
`agents_extensions/agy/hooks.json` into the workspace `.agents/hooks.json`
alongside the shared agent configuration. Local synthetic tests prove the
read-only announcement contract; issue #10558 requires a separate live AGY
proof of the next-call timing before certification.

### AGY shell-output guard and startup gate

The native shell event is
`{"toolCall":{"name":"run_command","args":{"CommandLine":"printf AGY_SYNTHETIC_OK"}},"stepIdx":19}`.
`secret_print_hook.py --harness agy` reads `toolCall.args.CommandLine`.
A present `toolCall` is authoritative; `tool_input.command` is accepted only
when `toolCall` is absent. Any tool name carrying `args.CommandLine` follows
the same command validation and detector rules. Empty, whitespace-only or
non-string command text denies. A non-`run_command` tool without that key
allows; `run_command` without it denies. Registration still matches only
`run_command`; whether native matching ever delivers another tool is UNKNOWN.
Malformed JSON, non-object or oversized AGY stdin, and missing, crashing or
late detectors deny. The stdin size cap applies only to AGY; other harnesses
keep their unbounded read and existing decisions.

The entry point normalizes command text to the shared Claude/Bash detector.
Its detector deadline remains five seconds. The AGY detector child omits
`LEARN_UK_SECRETS_OK`; other harnesses keep their existing override behavior.
AGY denials print
`{"decision":"deny","reason":"..."}` and exit 0; other harnesses retain exit 2.
These repo-local outputs do not establish native blocking.

The tracked `agents_extensions/agy/hooks.json` overlay adds the named
`shell-secret-print-guard` to `PreToolUse`, matcher `run_command`, timeout
10 seconds. It invokes the entry point directly, separately from the
fail-open driver wrapper. Existing driver hooks keep their behavior.

Hook commands resolve from the directory containing `hooks.json`.
After deployment in the primary checkout's workspace `.agents/`, the
overlay's `../.venv/bin/python` and `../scripts/agent_runtime/secret_print_hook.py`
resolve within that checkout. Worker installation uses
`scripts.common.repo_root.project_interpreter` to name the shared primary
interpreter and an absolute entry-point path, so a dispatch worktree needs
no local `.venv`. A guarded workspace suffices when ordinary HOME has no
`.gemini/config/hooks.json`; the gate never writes the user's home.
Scoped review homes receive the same absolute registration through the
`review_mcp.py` and `attempt_boundary.py` provisioners, for isolated and full
review access. On the review route, the load-bearing control is the exact
validated command-denial settings (`command(*)` and `write_file(*)` denied,
checked by `_write_review_permissions` before launch), plus `--sandbox`.
Scoped-home guard registration is defense in depth. A PASS certifies
registration in every loadable candidate. It does not certify that the hook
can execute inside the review OS sandbox. The probe at `69690b9667` found the
interpreter and entry point unreadable there. The failure disposition of a
hook that cannot start is UNKNOWN. It can only fire on `run_command`, which
the settings deny.

`agy_hook_config` checks the spawn's workspace `.agents/hooks.json` and
effective-HOME `.gemini/config/hooks.json`. Scoped HOME replaces ordinary
HOME, so the ordinary-home file is not a candidate for that spawn. Every
existing candidate that can load must contain a valid, enabled guard. An
absent candidate cannot load and is skipped. The spawn still refuses unless
at least one candidate exists and contains a valid guard. An existing
unguarded or invalid file refuses even alongside a valid candidate.
PASS requires one enabled guard registration per existing candidate, the
`PreToolUse` event, a matcher covering `run_command`, and a command resolving
to the executable project interpreter and this entry point. Matchers `*`
and `""` pass the local coverage check; other matchers use Python regular
expressions. This check does not establish AGY's native matcher semantics.
Workspace-relative commands must resolve exactly to the project interpreter
and guard entry point. Home commands must use absolute paths. Unresolved
commands and duplicate JSON keys refuse.
The command timeout must be an integer of at least 10 seconds; booleans refuse.
Invalid candidates and the absence of all guarded candidates refuse. The
adapter installs only when the dispatch workspace candidate is absent. It
never repairs an existing unguarded, disabled or invalid file. The explicit
workspace provisioner merges a missing guard without replacing unrelated
named hooks. Installation refuses
traversal and symlink components, then publishes the merged file atomically
through directory descriptors while preserving unrelated hook bytes. A newly
published or merged file has mode 0600; an existing guard left untouched
retains its file mode.

Bridge asks explicitly provision an absolute guard into their caller-owned
scratch workspace when its hooks file is absent. Existing invalid scratch
files remain untouched and refuse in the adapter. Attempt workspaces need
no hooks file because their provisioned scoped home contains the guard.

The launcher checks the deployed root and effective HOME inside
`launcher_adapter_exec`, after extension deployment and before AGY execution.
It starts AGY from that same root, including when called from another
directory. Dry runs do not spawn
AGY or certify wiring. The adapter checks workers and reviews before
`agy --version` or any provider subprocess and raises a typed refusal.
Neither path changes provider on refusal.

The spawn inventory is a file-level regression tripwire, not proof that every
start is found. Each candidate file has one row with the weakest applicable
status: `gated`, `management-exempt`, `probe-exempt`, `ungated-residual-10442`
or `generic-helper`. Generic process helpers receive binaries from callers;
callers are classified by their own rows. Management operations start no model
session or tool call: `_run_agy_mcp` permits exactly `list` and `add`, and the
review catalog probe hardcodes `mcp list`. The tripwire misses starts whose
binary name never appears as the token `agy` in a process-capable candidate
file. Known non-detections include shared-runtime callers that select the
adapter by name without a process API in their file,
`scripts/ai_llm/fallback.py` and `scripts/batch_gemini_runner/execution.py`,
and Python command strings with `agy` embedded after other words. The shared
runtime callers are the residual of
[issue #10448](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10448),
owned by the harness lane. Per-site completeness of UI, ACP, proxy and usage
starts remains the residual of
[issue #10442](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10442),
also owned by the harness lane. Those starts remain ungated. The inventory does
not certify native enforcement.

The adapter captures its runtime-log path and workspace root before launch.
It uses the plan's existing `liveness_paths` and resolved `cwd` fields, keeping
serialized metadata unchanged.
An ordinary caller may replace the log with one inside that captured workspace;
attempt logs remain confined to their enforced write root. These reads reject
traversal, symlinks, hardlinks, and non-regular files regardless of where the
workspace sits relative to a checkout or its Git directory.

A startup PASS proves none of the behaviors below. The post-merge driver
owns the native probe and failure matrix, including permission skipping.
A startup gate cannot guarantee blocking after a hook crash or timeout.

| Native behavior | Evidence state |
| --- | --- |
| Native matcher semantics | UNKNOWN |
| Duplicate-key parsing | UNKNOWN |
| Multi-file precedence among workspace, home, scoped home, app settings and plugins | UNKNOWN |
| Missing hooks file disposition | UNKNOWN |
| Print-mode hook loading | UNKNOWN |
| Interaction with `--dangerously-skip-permissions` | UNKNOWN |
| Missing command disposition | UNKNOWN |
| Non-zero hook exit disposition | UNKNOWN |
| Hook timeout disposition | UNKNOWN |
| Malformed hook output disposition | UNKNOWN |
| Invalid hooks configuration disposition | UNKNOWN |
| Nested-agent coverage | UNKNOWN |
| Shell-stdin coverage | UNKNOWN |
| Scoped-review hook loading | UNKNOWN |
| Failure disposition when the registered hook cannot start inside the review OS sandbox | UNKNOWN |
| Exit 0 plus deny JSON blocking a live `run_command` | UNKNOWN |

AGY's envelope is specified in its
[headless documentation](https://antigravity.google/docs/cli/headless/).
Grok's native field names come from its
[terminal result projector](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/src/headless.rs)
and [structured-output attachment](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/src/headless/reducer/mod.rs).
Adapters return validated canonical JSON in the existing runtime `response`
field. Review callers validate it against the authoritative profile and pass an
object into the dimension/direct consumers. Missing, malformed, truncated,
unsuccessful or schema-rejected results fail; assistant prose cannot rescue
them. Codex schema calls neither return streamed prose nor reap before the CLI
has written its constrained output and exited. Existing tool-call telemetry is
preserved.

Compatibility parsing is selected **before invocation** and logged explicitly,
only for confirmed unsupported CLI surfaces: Cursor `cursor-agent` and OpenCode
`run` via DeepSeek/GLM. Native Gemini capability is unknown and fails closed.
An unknown or non-selectable route does not become an unsupported route. Schema
rejection never triggers a retry without the schema. Legacy recorded audit
responses retain compatibility parsing; the live Claude audit route validates
its structured result before delivering canonical JSON to that parser.

Reviewer choices, configured model pins, lineage checks and QG canaries are
unchanged. Direct review uses the native Claude adapter with its existing
`claude-opus-5-5` pin. A schema-capable adapter does not establish availability,
policy admission or semantic correctness for every configured model. Issue
#7810's frozen 18-cell matrix retains those residuals; held-out evaluation and
cross-family approval belong to the reviewer of record at the exact PR head.

Mechanism coverage: `tests/build/test_reviewer_schema_transport.py`.
Deterministic scoring replay: `tests/build/test_reviewer_scoring_parity.py`
(run with `-q -s` to print before/after summaries). The opt-in `direct_live` test
requires `QG_SCHEMA_DIRECT_LIVE=1`, reads the frozen public module, and redirects
all module artifacts into a temporary test context.

## Session resume policy — the rule that matters

| Path | Resume? | Why |
| --- | --- | --- |
| Native interactive task | not controlled by runtime | Resume the native task. Codex retains reasoning and owns compaction; do not rebuild it from visible messages. |
| Bridge `_claude.py` / `_gemini.py` | **yes** | Cache warmth and multi-turn coherence inside the exact bridge identity. |
| Bridge `_codex.py` | **yes** | Preserve native Codex reasoning and compaction for the exact `task_id`; `--new-session` is the explicit reset. |
| Channel inbox | **yes** for resumable agents | Exact `agent + channel + thread_id`; resumed prompts contain only unseen deliveries. |
| Sealed review | **no** | A review checkout is an isolation boundary and must not inherit a normal-worktree session. |
| `/v1/chat/completions` proxy | **no** | Stateless compatibility endpoint; the caller owns and supplies the full message history. |
| `dispatch.py` (future, coding tasks) | **no** | Worktree is the isolation boundary. Resume across worktrees is an incoherence footgun. |
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
| `read-only` | Adapter-specific read and execution permissions | Consultation, questions, reviews |
| `workspace-write` | CLI can write files in cwd | Coding tasks, refactors, batch fixes |
| `danger` | Sandbox bypassed entirely | Only when explicitly needed (e.g., setup scripts) |

Each adapter declares its `supported_modes` as a frozenset at the class
level. Runner rejects invocations requesting an unsupported mode with
`ValueError`.

`cwd` is **mandatory** for `workspace-write` and `danger`. Runner raises
`ValueError` if missing. This prevents "write to wherever Python happens
to be running" bugs.

Sources access in review routes uses the tool set derived from the server's
`readOnlyHint` annotations, checked by the behavioral side-effect audit. Formal
receipt contracts are subsets of that set. Codex scoped review config lists the
receipt contract's readers; the adapter's final argv overrides enforce that same
contract for formal attempts, including the parent sandbox's stdio proxy. Ad hoc
read-only argv instead expose all audited readers. Both approve each exposed tool
individually and hide writers even when a verified parent OS sandbox requires
nested sandbox bypass. Sealed Codex reviews ignore user config and use only the
injected `sealed_review` server; the adapter adds no Sources settings unless a
Sources transport is explicitly defined. Claude and AGY formal attempts enforce the
receipt contract through the sources boundary and full-review allow rules. The
Sources server also filters listings and refuses calls outside the formal
receipt contract, independently of CLI exposure controls.
Every Claude `read-only` invocation takes both sets from the shared module and
passes each persisting tool in `--disallowedTools`: the ordinary and formal
reviewer profiles, explicit caller allowlists (including `mcp__sources__*`),
`discussion_readonly`, `review_isolation`, and read-only calls with no profile.
Claude matches MCP rules against the configured server name, so each writer is
denied twice: as `mcp__sources__<tool>` and as `mcp__*__<tool>`. A deny glob
must match the whole tool name, so the second rule removes the writer whatever
name an explicit config, `.mcp.json`, user config or plugin registers the server
under (for example `sources_alias`), while `query_ulif_records` and other longer
reader names stay reachable. A same-named tool on another server is denied too.
A live probe on Claude Code 2.1.288 with the real server registered as
`sources_alias` showed all five writers exposed under the canonical deny alone,
and none under the glob deny, even with `mcp__sources_alias__*` allowed.
Claude applies deny rules before allow rules, so the deny also wins over user or
checkout settings. If the server declarations cannot be read, the read-only
invocation fails instead of launching without the denies. Cache-writing ULIF and
Wikipedia tools are excluded from formal receipt contracts and these reviewer
grants; `workspace-write` and `danger` argv are unchanged, so writers' and
builds' cache access is unchanged.

### Claude headless permissions

Ordinary Claude `read-only` dispatches and bridge asks opt in with
`tool_config={"reviewer_tools": True}`. When no explicit `allowed_tools` is
supplied, this enables `dontAsk` with read/search tools, Bash, and web lookup.
An MCP config also grants sources tools. These reviewers can run Python,
pytest, and read-only `git`/`gh` commands without interactive approval.
Edit/Write/NotebookEdit and common
Git/GitHub mutation commands are denied. `discussion_readonly` and
`review_isolation` retain their separate tool profiles. `workspace-write`
passes `--permission-mode dontAsk` and allows Bash, Read, Edit, Write,
Grep, Glob, LS, WebFetch, and WebSearch. NotebookEdit is omitted because
the primary-checkout PreToolUse matcher covers Bash and
`Write|Edit|MultiEdit`. Each server in the worker checkout's `.mcp.json`
(the dispatch cwd) adds one `mcp__<server>__*` allow rule. An explicit
`mcp_config_path` is read instead of that file. A missing file grants no
MCP tools. A present file that cannot be read or parsed, or a server name
that cannot be written into `--allowedTools`, fails the dispatch. An
explicit `allowed_tools` value stays the only allow list. Headless
`claude -p` otherwise starts in manual mode and denies every tool that
would prompt. `dontAsk` is the documented non-interactive mode
(`claude --help` on the installed Claude Code): pre-approved tools run,
and anything that would prompt is denied, so the session does not wait.
`acceptEdits` still prompts for shell and network. `auto` can refuse a
legitimate worker action. `bypassPermissions` is not used for this mode.
It still runs hooks, but it approves every tool with no allow list.
`danger`'s `--dangerously-skip-permissions` stays on the danger argv
alone. An allow glob of `mcp__*` does not grant MCP tools, so each
configured server is named. The tracked PreToolUse guards still load via
`--settings`, including under `dontAsk`; a hook that exits 2 blocks the
call. `--bare` is what skips hooks.

Without the opt-in, read-only calls retain the prior Claude CLI permissions
plus the sources persisting-tool denies.
This covers content quality reviews and tool-less bakeoff calls. Outside sealed
`review_isolation`, an explicit `allowed_tools` value is passed
unchanged as the sole `--allowedTools` argument, including an empty string. The
adapter does not add reviewer tools or `dontAsk`, the reviewer deny list,
publish hook, or push rewrite in that case; it adds only the sources persisting-tool
denies. Shared worker guards still load. This keeps a read-only caller's
`mcp__sources__*` allowlist (V7 dimension reviewers, wiki review) restricted to
the read-only sources tools.

Every headless Claude invocation receives `--settings` with PreToolUse guards
generated from `agents_extensions/shared/settings.json`. Hook commands resolve
to tracked `agents_extensions/shared/hooks` files in the checkout containing
the adapter. Sealed `review_isolation` keeps its existing `--safe-mode` and
sandbox. Safe mode suppresses hooks and shell/write tools there; a live CLI
probe with a missing hook path and a Bash
call completed without trying to load the hook. The guards stop recognized
direct primary-checkout writes while allowing
worktree writes; arbitrary interpreter writes remain a known parser limit.
Code the reviewer runs (Python, scripts, HTTP) can publish using the host's
credentials: it can override its git config to push or write through the GitHub
API. The deny list, publish hook, and push rewrite stop ordinary command forms
only. Prefix Bash deny rules do not cover wrappers such as `git -C`.
Claude `--bare` is disabled because it skips hooks. A live bubblewrap probe
also allowed a primary-checkout write, so the bubblewrap sandbox is not relied
on as the guard.

### Claude headless runs cannot leave background work (#9690)

A `claude -p` run exits when its final turn ends. Work it started in the
background is then killed or never reported, so a worker could end with "the
report will follow" and no verdict. Every `ClaudeAdapter` plan closes this in
two parts, applied in every mode:

- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in `env_overrides`. In Claude Code
  2.1.289 this makes Bash reject `run_in_background` with an
  `InputValidationError`, and it runs a background subagent request in the
  foreground. It also disables MCP auto-backgrounding. `env_sanitize`
  allowlists the variable for the `claude` provider only.
- `permissions.deny` in the `--settings` JSON for `Monitor`, `ScheduleWakeup`,
  `CronCreate` and `Workflow`. The variable leaves these tools available, and
  they still start or schedule work past the turn. A settings deny removes them
  from the tool list in `dontAsk`, `bypassPermissions` and default modes.

Kimi and KimiCC ids are retired (OO-58, #11327). `build_invocation` refuses
them before a plan exists, so neither harness reaches these background controls.
In Claude Code 2.1.289 `--bare` already offers only Bash,
Edit and Read, and Bash has no `run_in_background` there (a capture of the
request sent to a local fake endpoint); the explicit controls keep the route
closed if that reduced tool set changes.

The ACP Claude seat (`acpx-claude-shadow`, #10500) launches the host Claude
Code through the repo-owned `scripts/agent_runtime/claude_acp_exec.sh`, which
`CLAUDE_CODE_EXECUTABLE` names. The adapter reads the launcher only from the
canonical primary checkout, which the adapter's own checkout names through its
git links (`resolve_main_root_without_git`: no git process, so PATH, git
configuration and the environment cannot redirect it); a worktree copy is
never used. Before every launch it validates the launcher and each parent
(owner, mode, no symlink), reads it once without following links, checks the
SHA-256 of those bytes against the adapter's pin
(`_CLAUDE_ACP_LAUNCHER_CLOSURE`; the launcher is self-contained, and its bytes
and the pin change in the same commit), writes them to a private `0700`
per-launch copy under the caller's cache directory, and validates the pinned
host binary. `CLAUDE_CODE_EXECUTABLE` names that copy, so a later change to the
checkout does not change what runs. The primary checkout is resolved from git
metadata files that must have the structure git itself requires (a `.git`
directory with `HEAD`, `objects` and `refs`, or a worktree link with
consistent back-links into such a store); every path component is checked with
`lstat`, no symlink is followed, and a FIFO or device where a metadata file
belongs is refused without blocking.
The copy directory in the caller's cache is checked like the
launcher's parents and must be owned by the caller before anything in it is
touched. Before each launch, a sweep removes copies older than two days, but only
`0700` directories the caller owns, with the generated name, that no live
process holds open (read from `/proc`); sweep failures are logged. The ask's
own copy is removed when its result is parsed. If a live process still holds it
or removal fails (permission, `ENOSPC`, `EBUSY`), the result fails with
`acp_adapter_incompatible` and a logged `ClaudeAcpLauncherCleanupError` instead
of leaving a silent copy; the runner's final cleanup retries.
A missing, unsafe, unreadable or mismatched launcher, an unresolvable primary
checkout or a failed copy refuses with a typed `ClaudeCodeExecutableRefusal`
before any ACP message, with no fallback. Refusal text names no absolute host
path. Host paths in the provider's output are replaced with labels before
the 500-character excerpt is cut. The launcher rechecks the binary's device,
inode, size, and mtime and ctime in nanoseconds with GNU `stat` (`gnustat`
where the system `stat` is the uutils build, which rounds nanoseconds; without
GNU `stat` every launch refuses). It then execs the binary with the deny list
as one `--disallowedTools` argument; the SDK's own `--disallowedTools` follows
and accumulates. After the ask, any result, successful or not, fails when the
binary's identity changed.

These checks are bound to the verified launcher bytes and catch drift,
accidents and honest misconfiguration: an auto-update mid-ask, a stale or
edited checkout, unsafe permissions, corrupt git metadata, and ordinary
concurrent launches. They are not tamper resistance. A writer running as the
same Unix user already controls the host binary, the user configuration and the
checkout, so deliberate replacement or forgery by that writer is out of scope.
Documented residuals (owner: infra; resolved in an isolated-authority phase,
where launcher verification and execution run under an authority the seat's
user cannot write):

- Execution is bound to a pathname after hashing. The SDK receives the private
  copy's path, which that writer can replace between verification and exec.
- That writer can edit the host binary in place and restore its size and
  mtime. The nanosecond ctime comparison catches this unless the writer can
  also reset ctime.
- That writer can fabricate a complete git layout (`HEAD`, `objects`, `refs`
  and consistent links) to select a non-canonical primary checkout. The
  launcher digest still pins the bytes that run.

The seat enforces the denies
through these launcher flags, not through ACPX permissions: `--deny-all` never
covers tools that run without asking, such as `Monitor` and `ScheduleWakeup`.
The plan also sets `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`,
`CLAUDE_CODE_DISABLE_ADVISOR_TOOL`, `CLAUDE_CODE_DISABLE_CRON` and
`CLAUDE_CODE_DISABLE_WORKFLOWS`, allowlisted for this seat only.

Sealed `review_isolation` drops the variable through its own environment
allowlist. It is still closed, because `--tools Read,Grep,Glob` offers no tool
that can background. Interactive launchers (`start-claude.sh`,
`start-claude-driver.sh`, `start-claude-cto.sh`, `scripts/launchers/claude.sh`) do not use the adapter
and keep background tasks. A trailing `&` or `nohup` inside a foreground Bash
call is a different path: `worker_leftovers.py` handles it (#8991).
`tests/agent_runtime/test_claude_no_background.py` launches a fake CLI through
the real runner and checks both parts for the Claude adapter. KimiCC and native
Kimi refuse the retired catalog id before a plan. Every adapter which resolves
the Claude binary stays in the harness table, including the retired KimiCC file.

The CTO launchers `start-claude-cto.sh` and `start-codex-cto.sh` use driver mode
and default to the registered `epics` stream, whose root epic is #10453.
Their model defaults are `claude-sonnet-5-5` and `gpt-6.1-sol`, respectively,
both at `high` effort. Command-line `--model` and `--effort` override
`LAUNCHER_MODEL` and `LAUNCHER_EFFORT`. Both wrappers reject `--force` with exit 2
and retain the driver identity, slot, occupancy, and duplicate-supervisor checks.
They reuse `.claude/epics-epic/DRIVER-STATE.md`, the driver prompts, and `drive-epic`.
Scope re-entry and supervisor successors return through the same CTO wrapper.

Only `start-claude-cto.sh` on the resolved `epics` lane permits Opus selected by
an explicit command-line `--model`. Environment-only Opus and Opus on other
Claude entrypoints or lanes remain refused with exit 7. Every Claude launch
still stops at 99% weekly usage. `LU_CLAUDE_CAP_OVERRIDE=1` bypasses only that
usage stop and does not expand the Opus exception.

### Claude account labels for ordinary workers (#10619)

Moved to [`docs/runbooks/claude-account-labels.md`](runbooks/claude-account-labels.md):
the `dispatch.py dispatch --claude-account` label, its checks and threat model,
and the fleet-wide default-account file a dispatch without the flag reads.

### Native Grok headless permission mapping (#7583)

On native Grok 1.0.x CLI, `acceptEdits --always-approve` still prompts for shell
execution and fails unattended turns (`stopReason=cancelled`), while `plan`
blocks all tool calls outright. The adapter maps `workspace-write` and `danger`
to `bypassPermissions --always-approve`, and
ordinary `read-only` to `auto` with `--deny` on the native write
permission prefixes (`Write`, `Edit`) and `Bash` unless reviewer tools are
opted in. The built-in ID
`search_replace` belongs to `--disallowed-tools`, not `--deny`; `MultiEdit` and
`NotebookEdit` are not documented Grok permission prefixes.
The adapter therefore also removes `search_replace` explicitly from every
ordinary read-only invocation.
Prefix Bash denies are not fail-closed under `auto` (unnamed commands may still
be approved). Ordinary read-only dispatches and bridge asks opt in with
`tool_config={"reviewer_tools": True}`. The opt-in removes the Bash deny and
loads the same tracked fleet PreToolUse guards and reviewer publish guard as
Claude through a per-invocation Grok agent definition. The hook bridge maps
Grok's camelCase event and native tool names to the existing guard input.
`Write`, `Edit`, and `search_replace` stay denied. Trail isolation, sealed
review isolation, strict MCP reviews, explicit tool allowlists, and callers
without the opt-in retain their prior argv. The opt-in also installs the same
ordinary Git push rewrite used by Claude. Code the reviewer runs (Python,
scripts, HTTP) can still publish using host credentials: it can override its
Git config to push or call GitHub APIs directly. The deny rules, publish hook,
and push rewrite stop ordinary command forms only.

On Grok 1.0.41 an explicit `--permission-mode auto` wins over `--always-approve`
and leaves `yolo_mode` false. The auto classifier then refuses `git push`
before the command runs, including a write worker's push of its own branch
(#8965). `workspace-write` and `danger` use `bypassPermissions` so that
classifier is not the session mode. Both also install the tracked fleet
PreToolUse guards from `agents_extensions/shared/settings.json` (primary-checkout
write, secret-print, merge, and the other worker hooks) through
`scripts/agent_runtime/grok_hook_bridge.py` and a per-invocation `lu-write-worker`
agent. That agent does not load `guard-reviewer-publish.py` and does not set
the read-only Git push rewrite. The read-only reviewer opt-in keeps its publish
hook and push rewrite on `auto`. Matchers for the write worker also name the
Grok tool ids `run_terminal_command`, `write`, `search_replace`, and
`hashline_edit`, which the Claude matcher aliases do not all cover.

`hashline_edit` belongs to Grok's hashline file bundle
(`hashline_read`, `hashline_edit`, `hashline_grep`). That bundle replaces the
standard bundle (`read_file`, `search_replace`, `grep`); one session does not
offer both. The file toolset is selected by `[toolset] file_toolset` in the
Grok home `config.toml` (preserved probe: `batch_state/probe-evidence/9008/`,
where that file sets `file_toolset = "hashline"`). Delegate's environment
sanitizer drops `GROK_HOME` and `GROK_CONFIG`: `build_agent_env` in
`scripts/agent_runtime/env_sanitize.py` (lines 421-439) copies a name only
from an allowlist, and neither name is on `_SAFE_NAME_ALLOWLIST` (line 37),
`_SAFE_VALUE_NAME_ALLOWLIST` (line 68), `_PROVIDER_SECRET_ALLOWLIST`
(line 78), or `_PROVIDER_SAFE_NAME_ALLOWLIST` (line 108). A live hashline
session uses a temporary `GROK_HOME` whose `config.toml` sets `file_toolset`.
The write-worker matcher still names `hashline_edit`, and the primary-checkout
guard blocks that tool the same way it blocks `search_replace`.

Issue #9008 keeps `danger` on the same argv as `workspace-write`:
`bypassPermissions`, `--always-approve`, and the `lu-write-worker` agent.
Claude loads the fleet PreToolUse guards for both write modes. Its
`workspace-write` mode is `dontAsk` plus an allow list, and its `danger` mode
is `--dangerously-skip-permissions`. Grok 1.0.41 has no
`--dangerously-skip-permissions` flag. `bypassPermissions` is Grok's
always-approve mode, and the fleet hooks still run under it. `dontAsk` allows
only pre-approved tools, and an explicit `auto` permission mode leaves
`yolo_mode` false, so a headless worker cannot push its branch. The operator
accepted `bypassPermissions` for Grok write workers (#8965). `danger` keeps
the write-guard agent, so the fleet guards stay on that mode too.
`test_danger_argv_matches_workspace_write` pins the shared argv.

## Weak-driver trail isolation (P5)

Trail drivers are never given a shell, workspace writes, GitHub mutation, or
ambient MCP access. A certifiable weak session must use the explicit runtime
profile:

```python
invoke(
    "grok",
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
- Every Kimi seat (native and KimiCC) refuses trail sessions. Kimi models are
  retired (OO-58); `scripts/agent_runtime/kimi_admission.py` still refuses the
  request before a launch is planned.
- GLM/opencode, Hermes Grok, and every unproven harness refuse before spawn. GLM currently ignores tool restrictions, so a refusal is more
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
        model: deepseek-v4.1-flash
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
refused/reset/read timeout, initial-response timeout with no observable local
startup activity, stdout-silence timeout before first stdout, and parsed-but-empty
responses. Startup activity includes stdout/stderr, adapter-declared liveness-file
updates, and CPU/disk work in the agent process tree. It is intentionally a local
liveness signal, not proof that a remote provider accepted or completed the task.
Content-policy refusals, 4xx request-format errors, and mid-stream silence
timeouts after partial output do not fail over.

An adapter that types its outcome sets `ParseResult.provider_error_text` (even
to `""`). The classifier then reads only its `failure_code`: `rate_limited`,
`provider_overloaded` and `provider_auth` trigger, while
`provider_policy_refusal`, `provider_error` and `provider_stream_incomplete`
never do. No raw stdout/stderr text is read; only the runner's own startup
timeouts still mean `transport`.

### Codex outcomes come from `codex exec --json` (#9532)

The Codex adapter runs `codex exec --json`. Exec prints typed JSONL events on
stdout, already filtered to this invocation's thread and turn, and that stream
is the only outcome authority (`scripts/agent_runtime/adapters/codex_events.py`):

- **Completed**: one `turn.completed` with exit 0. The answer is always the `-o`
  file (schema-validated when an output schema is bound), never a streamed
  agent message.
- **Failed**: one `turn.failed`. Its full `error.message` is matched by anchored
  recognisers for the CLI's own usage-limit, quota, capacity, 401 and
  policy-refusal wording. Unfamiliar or conflicting messages are
  `provider_error`.
- **Incomplete** (`provider_stream_incomplete`): no terminal event, malformed
  JSON, a nonzero exit after `turn.completed`, a second thread, turn or
  terminal, or a resumed call whose `thread.started.thread_id` is not the
  session it resumed. The runner keeps its own timeout or cancellation code.

A top-level `error` event is only a notice: followed by `turn.completed` it was
retried and never cools a route. Nested item fields are never searched. These
include agent text, reasoning, command output, MCP results and
`item.type="error"` warnings. Stderr and the shared session rollout are never
read for the outcome. The session id is `thread.started.thread_id`, and tool
telemetry maps typed items: `mcp_tool_call` becomes `mcp__<server>__<tool>`.
Usage is recorded only for fresh threads, because `turn.completed.usage` holds
session totals. Early reap waits for `turn.completed` plus identical non-empty
`-o` bytes on two checks two seconds apart. Exec writes `-o` after
`turn.completed`, so a reaped call is accepted only if `-o` still holds those
bytes.

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

## Dispatch worktree layout

Run detached tasks through `scripts/dispatch.py`. Supply `--agent`, `--model`
and one of `--prompt` or `--prompt-file`. The supported modes are `read-only`
and `workspace-write`.

```bash
.venv/bin/python scripts/dispatch.py dispatch \
  --agent codex --model gpt-6.1-sol --effort high \
  --task-id example-task --prompt-file brief.md \
  --mode workspace-write --worktree --owned-path scripts/example.py
```

Automatic paths are `.worktrees/dispatch/<agent>/<task>/`. Explicit `--worktree`
paths and `--cwd` must name a valid dispatch checkout for that agent. The primary
checkout stays on `main` and is read-only to agents. The worktree planner lives
in `scripts/dispatcher/git.py`.

Default sparse exclusions are defined by `SPARSE_EXCLUDE_DEFAULT` in that
module. Use repeatable `--sparse-include DIR` or `--full-checkout` when a task
needs excluded inputs. Owned paths do not re-include sparse files, and no
anchor files are added automatically.

The dispatcher checks rules-core availability but does not prepend the core or
research pointers to the prompt. The one exception is a read-only Claude run,
which receives the rules core as an appended system prompt because `--restricted`
skips `CLAUDE.md` (`scripts/dispatcher/providers/claude.py` `build`). Include
required instructions and relevant source locators in the brief.

A read-only AGY run executes inside the dispatcher's bubblewrap boundary
(`scripts/dispatcher/agy_sandbox.py`): a read-only root, a private scratch home
and a dispatcher-owned Sources relay that forwards only the read-only tools.
Dispatch refuses it with `read_only_unenforceable` only on a host that cannot
start that boundary. Research flags and owned paths record metadata; write-path claim
admission and overlap overrides are retired.

Use `status TASK --run-nonce NONCE` and `wait TASK --run-nonce NONCE` to observe
the exact run. `list --status running` reports active tasks. Write-task delivery
requires a pushed branch; inspect the terminal record and Git evidence.
A dirty or empty deliverable is not success. The dispatcher removes the task's
worktree at settlement only when nothing in it can be lost; remove a kept one
only with `python -m scripts.orchestration.worktree_claims remove`, whose
custody checks still apply.

Budget/cost/pricing guards, preflight triage, lifecycle-file propagation,
keep/force-worktree switches, repository backfill, Cursor self-dispatch and DoR
checks, dirty-primary admission, open-PR freeze, Kimi boundary hooks, danger
mode and RB2 are retired. Native Grok dispatch is retired; `grok` is not a
dispatch agent, so use `--agent cursor --model grok-4.7-high`.
No additional worker exports beyond `scripts/dispatcher/environment.py` are
promised. The provider adapter layer still serves its other callers.

Bounded workers retain the v2 driver-brief and `--advisory-task` admission paths.
Use `--print-advisory-binding` with the exact worker request. The legacy
advisor-role switches for bounded envelopes are absent; include the requested
envelope and binding in the read-only advisor's brief. `--advisory-role` and
`--advisory-binding` serve only the catalog's `advisory_roles` decisions (today
`review_budget_elevation`, read by the verdict recorder): the read-only task records
the role, route and bound digest, and its worker seals the result at finish
(`bounded_advisory.seal_advisor_result`).

### Review attempts: server and templates must match (#9163)

Dispatch v2 supports bound attempts only in dry runs; protected execution is
unavailable. The retained rendering and MCP helpers define the following
contract for their other callers. A bound review seat runs the Sources MCP server from the primary
checkout, but its prompt may have been rendered in any checkout. The two must
come from the same code, so the check binds the prompt to the checkout that
rendered it (`scripts/review/render_contract.py`):

- **Render time.** `scripts/review/prompts/render.py --output <prompt>` writes a
  `render_contract` record into `<prompt>.files_read.json`: the render checkout,
  the templates the render actually loaded with their sha256 and one digest over
  them, that checkout's server-code digest, and the prompt's sha256.
- **Server-code digest.** Two named components. `repository`:
  `.mcp/servers/sources/server.py` plus every repository module it imports,
  found by a static walk of `import` / `from … import` statements
  (function-level imports included) resolved the way the server's own
  `sys.path` resolves them: `scripts/`, then the repository root, then the
  server's directory. Files are read from disk whether or not git ignores them;
  a symlink contributes its target's bytes; `__pycache__`, documents and
  modules the server never imports do not count. Imports outside the
  repository (standard library, third-party) and dynamic `importlib` imports
  are not traced. `requirements-lock.txt`: the sha256 of the checkout's lock,
  which pins every third-party package the environment is built from; a
  checkout without it refuses as `review_server_lock_missing`. Accepted
  residual: an installed package that changes without a lock change (for
  example a reinstall of `packages/v4-runtime`) is not seen.
- **Contract validation.** `review_mcp.check_review_contract` reports:
  - `review_render_record_missing` — the prompt is a literal or stdin prompt,
    or its sidecar has no render record; re-render with `--output` and dispatch
    with `--prompt-file`;
  - `review_render_record_stale` — the prompt file no longer hashes to the
    prompt its record names;
  - `review_contract_mismatch` — the primary checkout's server code differs
    from the recorded render-time digest, or a loaded template in the render
    checkout changed since rendering. The message names the render checkout,
    the primary checkout, both digests, the differing server components and the
    fix: pull the primary checkout to `origin/main`, then re-render and retry.
- **Launch time.** `review_mcp.prepare_review_attempt` receives the admitted
  contract and, before writing the ledger or the seat's MCP config, digests the
  server again from exactly the checkout and interpreter that config launches
  (`render_contract.check_launch_contract`). If the checkout, the interpreter or
  the digest differs from admission (the primary was pulled in between), it refuses with exit 2 as `review_server_changed`,
  naming both digests and the differing components; no worker is spawned. The
  config is written right after this check; the seat's harness starts the server
  from it when the worker runs, and the worker does not check again (accepted
  residual: a change inside that window is not caught).

These helpers do not imply protected execution support in dispatch v2.

## Common mistakes

- **Writing new subprocess logic outside the runtime.** If you're
  calling an agent CLI, route through `runner.invoke()`. The moment you
  build a second `subprocess.Popen([...])` for an agent, you've
  reintroduced the thing we deleted.
- **Passing `session_id` to `dispatch.py` calls.** Coding tasks are
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
