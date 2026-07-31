# Agent seat onboarding — fleet cooperation and ACPX

**Audience:** every supported fleet seat on cold-start (interactive TUI, driver
launcher, headless dispatch).
**Product epic:** #6027 · **Stream:** #4707 (`infra-harness`).
**Status:** documentation contract for the structured-ACP + KimiCC rollout.
**Live routing data:** always re-read `GET /api/rules`,
`scripts/config/model_catalog.yaml`, and
`.venv/bin/python -m scripts.fleet_comms plane-status` — never hard-code live
plane mode, model pins, or formal-review eligibility from memory.

This runbook is the **canonical task-oriented entry point** for seat onboarding.
Other docs point here for ownership and ACPX scope; they do not restate mutable
caps or live modes.

---

## Read first (cold-start order)

1. Operator contract + model assignment via `GET /api/rules` (offline fallbacks
   under `agents_extensions/shared/rules/`).
2. This runbook — ownership matrix, experimental ACPX boundary, Kimi routes.
3. Fleet-comms mid-cutover rule:
   [`agents_extensions/shared/rules/fleet-comms-coordination.md`](../../agents_extensions/shared/rules/fleet-comms-coordination.md).
4. Epic seat routing (operator launch reminder only):
   [`epic-orchestrator-roster.md`](epic-orchestrator-roster.md).
5. Runtime entrypoints:
   [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md) and
   [`docs/SCRIPTS.md`](../SCRIPTS.md).
6. Cooperation detail (deliberation, Green Team, V2):
   [`docs/best-practices/agent-cooperation.md`](../best-practices/agent-cooperation.md).

---

## Ownership matrix (do not conflate)

| Surface | Owns | Never owns |
| --- | --- | --- |
| **`discuss`** (bridge) | Bounded multi-agent deliberation and design input | Implementation, merge authority, or the formal cross-family review gate |
| **`scripts/delegate.py dispatch`** | Isolated implementation execution in a worktree | Durable fleet authority or formal CF |
| **Fleet-comms + file handoffs** | Durable coordination and authority today; **file dual-write remains authoritative in every current plane mode** | Competing message buses; silent plane/retention/eligibility flips |
| **ACPX** | Experimental **structured invocation transport only** — default-off shadow seats plus one explicit fleet-comms `acp-discuss` controller for a bounded Codex/Grok conversation; not a coordination plane | Persistent sessions, backlog, auto-retries, unrestricted chat, plane flips, review eligibility |
| **Buzz** | **Explicitly deferred** | Anything in this rollout — relay-as-authority conflicts with the current authority model |

### Human overview pages

| Page | Canonical observer role | Browser boundary |
| --- | --- | --- |
| **ACP Conversations** (`/acp.html`) | Readable Codex↔Grok ACP transcripts plus the operational event rail | Read-only; cannot start, steer, retry, or cancel ACP |
| **Channels** (`/channels.html`) | Shared channel, thread, context, and delivery visibility | Read-only; send from an agent TUI or the project bridge CLI |
| **Broker Ops** (`/comms.html`) | Legacy broker messages, zombies, batch progress, and health during migration | Read-only; no browser message composition |
| **Build Events** (`/build-events.html`) | Active and recent build activity | Replaces the retired duplicate Comms activity feed |

The legacy send, post, and acknowledgement APIs remain available to their
current project CLI callers. Do not remove those routes or the Broker Ops page
until caller telemetry proves the old paths are unused and every unique
operations panel has a canonical replacement.

### Discuss is not formal review

`.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` produces design
input and transcripts. It does **not** satisfy independent cross-family review.

Formal CF uses:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <PR_NUMBER> --reviewer codex|claude|glm
.venv/bin/python scripts/ai_agent_bridge/__main__.py publish-review-verdict ...
```

Same-family helper output, design panels, and channel chat never seal a PR.

### Delegate is execution, not coordination

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent <lane> \
  --task-id <id> \
  --prompt-file <path> \
  --worktree
```

Workers implement inside `.worktrees/dispatch/<agent>/<task>/`. They do not
become a second coordination plane.

### Sol-advised bounded execution

For bounded implementation or investigation, read the machine-readable
`execution_routing.sol_advised_bounded` route in
[`scripts/config/model_catalog.yaml`](../../scripts/config/model_catalog.yaml)
before dispatching:

1. Ask `gpt-5.6-sol` at `high` for an advisory envelope containing the task
   contract, exact owned paths, maximum changed-file and non-test-LOC ceilings,
   constraints, risk boundaries, acceptance evidence, and escalation triggers.
2. If the envelope is complete and the work is bounded, hand it to
   `gpt-5.6-luna` at `xhigh`. Luna executes within that contract; it does not
   re-decide the task.
3. Use direct Luna at `medium` only for simple evidence or mechanical checks.
   Use Terra when the envelope is missing or broader autonomous integration is
   required.
4. The accountable orchestrator checks the owned paths and ceilings before
   dispatch and again against Luna's returned diff. Luna escalates any ceiling
   overrun, consequential architecture, security, release, high-risk go/no-go,
   unresolved consequential ambiguity, broader integration, and final
   disposition. Sol's advisory is same-family context and never replaces the
   required independent cross-family review.

Record the envelope and Luna's acceptance evidence with the task handoff. If an
escalation trigger fires, stop bounded execution and return the unresolved point
to Sol or the accountable orchestrator before making a consequential decision.

### Fleet-comms and file dual-write

```bash
.venv/bin/python -m scripts.fleet_comms plane-status
```

- Implemented modes are only `off` | `shadow` | `dual_write`.
- **File dual-write / lane diaries stay authoritative in every mode today.**
- `dual_write` mirrors plane traffic; it is **not** post-cutover plane-only
  authority (that state is not implemented).
- Do not hard-code a live mode in docs or prompts — always query `plane-status`.
- Plane / retention-apply / `formal_review_eligible` flips belong to the
  infra/harness lane after parity + present-tense operator/advisor GO.

### ACPX — experimental transport boundary

ACPX is **not** a coordination product and **not** a second fleet bus.
Two direct-only shadow seats (Codex + Grok) are **not a new coordination plane** —
fleet-comms + file dual-write stay authoritative, and native Codex / native
Grok stay authoritative under shadow compare.

**Seat-selection evidence (#6043, API-backed):** in the 2026-07-30 snapshot
from `/api/comms/live-activity?limit=500&minutes=120`, all **95** broker
dispatches had sender counts **Codex 26**, **grok-atlas 25**, and
**Claude 22** among the three busiest senders; the remaining **22** were
**Gemini 11**, **OpenCode 6**, **GLM 4**, and **AGY 1**. The same-day
30-day runtime sample from
`/api/runtime/usage?days=30` had **Codex 20**, **Claude 15**, and **Grok 1**.
Broker centrality is therefore strong for Grok, while **direct-runtime
evidence remains limited** — Grok is a deliberately conservative second
pilot, not fleet-wide enablement. These are dated selection-evidence
snapshots, not permanent routing weights.

**Exact contract (#6027 Codex pilot, #6043 Grok second pilot):**

- Feature flag `LU_ACPX_TRANSPORT=off|shadow|active`, **default `off`**.
  `shadow` is the unchanged comparison pilot. `active` is accepted only by the
  explicit `acp-discuss` controller described below.
- Direct-only seat names `acpx-codex-shadow` and `acpx-grok-shadow`; never
  registered for dispatch, routing, review, or failover.
- Local pin `acpx@0.13.0` — both adapters refuse to spawn on any other
  resolved binary version.
- Grok seat additionally preflights the installed native Grok CLI at exact
  semver `0.2.117` and refuses wrong/missing/unparseable versions before
  prompt.
- Every invocation requires a non-empty, bounded, local `task_id`,
  `correlation_id`, and `idempotency_key`, plus
  `tool_config={"acpx_shadow": True, "target_agent": "codex"|"grok"}`, and
  runs against a read-only, non-primary worktree.

**In scope (approved):**

- Feature-flagged adapters (default off / shadow comparison).
- Exactly one read-only/stateless **Codex** ACP participant
  (`acpx-codex-shadow`) and exactly one read-only/stateless **Grok** ACP
  participant (`acpx-grok-shadow`) for structured invocation.
- Grok fixed effective model/effort: `grok-4.5` / `high` (caller may pass
  only `None` or those exact values; metadata never fabricates otherwise).
- Grok ACP server command (single custom agent argument; never built-in
  `grok-build`, which cannot force `--no-leader`): absolute resolved Grok
  binary plus exact argv order
  `agent --model grok-4.5 --reasoning-effort high --agent-profile
  <hash-pinned-project-no-tool-profile> --no-leader stdio`.
- The project-owned Grok profile is digest-checked before every spawn. Its
  empty tool allowlist plus explicit denylist removes write, shell, subagent,
  memory, web, MCP, and LSP tools inside the Grok ACP server. This is required
  in addition to ACPX `--deny-all --no-fs --no-terminal --allowed-tools ""`:
  ACPX client flags alone do not remove native Grok tools.
- Correlation / idempotency fields recorded as **evidence** (local runtime
  metadata only — never ACP protocol flags, argv, or stdin; never published
  to fleet-comms, dispatch authority, or review evidence), not as a new
  authority source.
- Rollback = turn the feature flag off and use the existing native transport.

**Out of scope (forbidden in this rollout):**

- Persistent or named ACP sessions
- Queued prompt backlog
- Automatic prompt retries
- Unrestricted ACP agent-to-agent chat or any chat surface outside the bounded controller DAG
- Plane-mode or retention changes via ACPX
- Review-eligibility changes via ACPX
- Primary-checkout writes or write-mode ACP work
- Treating Grok + Codex ACPX as a coordination plane, review bus, or
  fleet-comms replacement

**Do not invent CLI flags, endpoints, or review eligibility here.** The
adapter's argv is fully confined and callers only ever set the `tool_config`
keys it allowlists (`acpx_shadow`, `target_agent`, `correlation_id`,
`idempotency_key`); this runbook describes ownership and safety, not a
floating CLI surface.

#### Active controller-backed ACP conversation

The active path is a **bounded fleet-comms-backed conversation**, not a new
bus. It is accepted only by `.venv/bin/python -m scripts.fleet_comms
acp-discuss`, which scopes `LU_ACPX_TRANSPORT=active` to the controller call
and restores the prior environment on exit; generic runtime callers cannot
turn it on. Pass the task on stdin and never place task or model-response data
in argv:

```bash
printf '%s\n' 'Compare the two bounded options and name risks.' |
  ACPX_AUTH_CHAT_GPT=1 \
  .venv/bin/python -m scripts.fleet_comms acp-discuss --cwd . \
  --task-id acp-6078 --correlation-id acp-6078-v1 \
  --idempotency-key acp-6078-v1 --rounds 2 --json
```

### When an orchestrator may use the ACP panel

Every supported fleet orchestrator may **explicitly** use this fixed
Codex↔Grok panel for one consequential, read-only design or risk comparison
when direct cross-provider critique is materially useful. It is not an
automatic launcher or `delegate.py` feature, and `acp-discuss` is the sole
surface. Use the default two rounds; three is the hard maximum.

Admission is one conversation repository-wide. If it is occupied, return
`busy` immediately: there is no queue, wait, automatic retry, or hidden
failover. On `busy`, unavailable ACPX, or an unready participant, use the
bounded bridge `discuss` path instead. A typed partial ACP outcome is valid
evidence to inspect, but not a successful discussion, formal review, or
coordination authority.

Fleet-wide means **caller-access parity**, not participant expansion. The live
caller classes below may request the same fixed panel when acting as the
accountable orchestrator; ordinary workers and review-only seats receive the
contract for awareness but do not start conversations independently.

| Caller class | ACP access | Boundary |
| --- | --- | --- |
| Claude orchestrators | Eligible caller | Explicit advisory invocation only |
| Codex orchestrators | Eligible caller | Explicit advisory invocation only |
| AGY/Gemini orchestrators | Eligible caller | Explicit advisory invocation only |
| Grok orchestrators | Eligible caller | Explicit advisory invocation only |
| Kimi and KimiCC orchestrators | Eligible caller | Explicit advisory invocation only |
| Cursor orchestrators with an explicit model | Eligible caller | Never use an automatic/opaque model route |
| Dispatch-only, worker, and review-only seats | Awareness only | The accountable orchestrator owns invocation |

Caller identity never changes panel membership: participants remain exactly
Codex and Grok. Do not add, rotate, or silently substitute a participant when
one is unavailable. Supporting a new participant requires a separately
approved provider adapter with the same no-tool, read-only confinement. ACP
must stay idle during startup, stream claim, dispatch, CI, PR events, formal
review, and plane-status checks.

### Shared ACPX install and E2E/replay verification

ACPX is installed once at the shared primary checkout as the pinned local
`acpx@0.13.0`; a dispatch worktree resolves that primary install and must not
create its own global or floating ACPX installation. For an E2E/replay check,
run the real stdin-only `acp-discuss` command from a registered worktree with
one bounded read-only task, then repeat the **identical** task, correlation,
and idempotency values. The first terminal result is evidence; the second must
be durable replay suppression, never another model run. Then run:

```bash
.venv/bin/python -m scripts.fleet_comms acp-verify \
  --conversation-id conversation_<id> --require-replay --json
```

The verifier is read-only and body-free. `verified: true` requires the fixed
participants to succeed in every requested round, successful native synthesis,
terminal `COMPLETE`, and an observed replay. It never authorizes a retry.

Participants are exactly `codex,grok`. Two rounds are the default and three is
the hard maximum: parallel initial participant calls, a bounded peer
cross-response, then authoritative native-Codex synthesis. The controller
allows at most two participant calls and five model calls by default,
including synthesis. It starts no persistent session, tool-enabled run,
unrestricted loop, hidden failover, or retry. Each model call is capped at 300
seconds, the whole conversation at 1,200 seconds, and content at 160k reliable
tokens or 512 KiB.

Replay suppression is durable and occurs before scheduling. An orphaned
reservation is terminal: never retry it. The single-host repository admission
file lock covers the conversation, including model I/O; no SQLite transaction
may cover model I/O. Typed partial results, idempotency disposition, and append-only
state/timeline events are durably recorded through existing fleet-comms and
file handoffs; those handoffs retain authority. This conversation neither
changes plane/retention state nor gains dispatch, routing, failover, or review
authority.

The privacy boundary is strict: task bodies, model responses, credentials,
paths, session data, and tool data do not appear in Runtime metadata. The
fleet-facing observability routes remain
`GET /api/runtime/acp/conversations` and
`GET /api/runtime/acp/conversations/{conversation_id}`; both are body-free.
The local Conversations page may also read
`GET /api/runtime/acp/conversations/{conversation_id}/transcript`. This
separate route requires both a direct loopback peer and a loopback URL host,
ignores forwarding headers, returns only bounded inline request/reply/synthesis
text plus display metadata, and sets `Cache-Control: no-store`. The page uses
inert text rendering and no browser storage. All three routes are read-only:
no dashboard control can start, steer, retry, or cancel a conversation.
Standard ACP token `size` means context-window capacity, never consumed-token
accounting.

This is deliberation transport, not formal cross-family review. It cannot
replace `review-pr` / `publish-review-verdict` or provide review eligibility.

#### Explicit comparison pilot

Run the dedicated pilot only from a dispatch/registered worktree. The prompt
arrives on stdin rather than argv. Codex additionally requires its non-secret
ChatGPT auth-method selector:

```bash
printf '%s\n' 'Reply with exactly READY.' |
  ACPX_AUTH_CHAT_GPT=1 LU_ACPX_TRANSPORT=shadow \
  .venv/bin/python -m scripts.agent_runtime.acpx_pilot \
  --target codex --cwd . --task-id pilot-6063 \
  --correlation-id pilot-6063-codex-v1 \
  --idempotency-key pilot-6063-codex-v1
```

For Grok, use the same command with `--target grok` and omit
`ACPX_AUTH_CHAT_GPT=1`; the adapter selects the existing cached Grok login.

This surface calls the native seat first and exactly one ACPX shadow second.
The native outcome and exit disposition remain authoritative even when the
shadow fails or disagrees. One global non-blocking lock admits at most one
comparison; contention returns immediately with no queue. A previously
executed idempotency-key digest suppresses both calls, and there are no
automatic retries or sessions. Runner failover is disabled for both pilot
calls, so the command cannot silently add a second native or shadow attempt.

The local terminal result may show both responses for operator inspection.
Persisted comparison evidence contains only target, outcome classes, parity,
durations, token counts when exposed, and digests of correlation/idempotency
values—never prompts, responses, raw identifiers, paths, sessions, commands,
stderr, auth material, or tool data. The read-only Runtime dashboard aggregates
that evidence; it cannot send or control ACPX traffic. The supporting native
and shadow pilot-leg usage rows also suppress task/run/session identifiers,
paths, telemetry labels, and stderr while retaining structured operational
counts and outcomes.

#### Safety and budgets (adapter contract)

| Guardrail | Rule |
| --- | --- |
| In-flight | **One** in-flight prompt maximum |
| Backlog | **Zero** queued prompts |
| Retries | **Zero** automatic prompt retries |
| Timeout / cancel | Bounded wall-clock timeout; cancellation must tear down cleanly |
| Correlation | Required correlation/idempotency fields on every attempt |
| Authority | Existing participant result remains authoritative under shadow compare |
| Writes | Refuse primary-checkout and write-permission paths |
| Evidence | Record correlation, classification parity, duplicates, timeout/recovery, and token data when the ACP stream exposes them — **without** promoting that log to authority |

#### Failure handling and troubleshooting

| Symptom | What to do |
| --- | --- |
| Feature flag off | Expected default — use native `runner.invoke` / bridge / discuss paths |
| `AUTH_REQUIRED` with an existing ChatGPT Codex login | Verify `codex login status`, then set the non-secret per-process selector `ACPX_AUTH_CHAT_GPT=1`; `--auth-policy fail` deliberately refuses implicit method selection |
| `AUTH_REQUIRED` on the Grok shadow seat | Establish the native Grok CLI's cached login outside this adapter; the Grok adapter automatically sets the non-secret per-process selector `ACPX_AUTH_CACHED_TOKEN=1` and scrubs ambient XAI API-key auth selectors so cached native login is the only accepted path |
| Other auth failure | Fail closed; do not retry in-adapter; fix credentials outside the adapter and never store or log API keys in the repository |
| Timeout / cancel | Treat as terminal for that prompt; no auto-replay |
| Crash / malformed NDJSON | Classify and record; do not promote partial output to authority |
| Duplicate correlation id | Treat as replay protection; do not double-apply side effects (there should be none) |
| Shadow mismatch | Keep the existing native/participant result authoritative; file evidence for infra |
| Implausibly large token usage matching a model context limit | Treat as a telemetry defect: standard ACP `used` is the live context count and `size` is capacity; never record `size` as consumed tokens |

#### Rollback

1. Disable the ACPX feature flag (default-off posture).
2. Continue on native agent runtime transport
   (`scripts/agent_runtime/` via `runner.invoke`, bridge, `delegate.py`) —
   native Codex and native Grok remain the authoritative paths.
3. Leave fleet-comms plane mode and formal-review eligibility unchanged.
4. Keep file dual-write handoffs current.
5. Grok + Codex ACPX seats are independent observability pilots only; turning
   either (or both) off is not a plane cutover.

### Buzz — deferred

Buzz is **not** part of this rollout. Its relay-as-authority model conflicts
with authoritative file handoffs + fleet-comms. Do not prototype Buzz as a
coordination plane, review bus, or ACPX peer until a separate operator/advisor
GO reopens that design.

---

## Kimi routes (native default vs KimiCC opt-in)

| Route | When | Effort contract |
| --- | --- | --- |
| **Native Kimi** (`./start-kimi.sh`, `delegate.py --agent kimi`) | **Default** headless/fleet and default interactive harness | K3 is **max-only** — non-max effort requests are ignored/refused at the native boundary |
| **KimiCC** (`./start-kimicc.sh`, `./start-kimi.sh --harness claude-code`, or `delegate.py --agent kimi --harness kimicc`) | **Bounded explicit opt-in** for Claude Code ergonomics with Kimi models | K3 defaults to **`high`** in interactive and headless/runtime paths; supported overrides remain observable in telemetry |

Do not weaken the shared native Kimi registry to match KimiCC. Native `kimi-code/k3`
stays max-only; KimiCC's high default is a KimiCC-route policy only.

See also: [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md) (KimiCC
headless route) and [`docs/SCRIPTS.md`](../SCRIPTS.md) (launcher flags).

---

## Command surfaces (no bare `ab`)

On some machines `ab` is ApacheBench. Always use the explicit project entrypoints:

```bash
# Deliberation (not formal review)
.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss <channel> "..." --with ...

# Formal CF
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <PR_NUMBER> --reviewer codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py publish-review-verdict ...

# Execution
.venv/bin/python scripts/delegate.py dispatch --agent <lane> --worktree ...

# Topology (never hard-code the answer)
.venv/bin/python -m scripts.fleet_comms plane-status
```

---

## Fresh-agent smoke (no-auth / read-only / no GitHub / no hidden session)

Use this checklist when validating that a **new** seat session understands
routes and authority. It must not require credentials beyond local repo tools,
must not mutate the tree, must not call GitHub, and must not depend on a hidden
prior session.

```bash
# 1) Confirm worktree / branch identity (read-only)
git status --short --branch
git rev-parse --show-toplevel

# 2) Load rules surface (method, not mutable caps)
test -f agents_extensions/shared/rules/fleet-comms-coordination.md
test -f docs/runbooks/agent-seat-onboarding.md
# When Monitor is available, read `GET /api/rules` through its configured host.

# 3) Query plane mode — do not assert a hard-coded mode
.venv/bin/python -m scripts.fleet_comms plane-status

# 4) Prove ownership vocabulary is present in the onboarding contract
rg -n "discuss|delegate\.py|fleet-comms|ACPX|Buzz" docs/runbooks/agent-seat-onboarding.md

# 5) Prove formal CF is separate from discuss
rg -n "review-pr|publish-review-verdict|not formal review|discussion is not" \
  docs/runbooks/agent-seat-onboarding.md \
  agents_extensions/shared/rules/fleet-comms-coordination.md

# 6) No writes: do not create files, do not git commit, do not gh, do not
#    open ACPX write paths. Exit with a clean tree identical to entry.
git status --short
```

**Pass criteria:** the seat selects discuss vs delegate vs plane-status vs
formal `review-pr` correctly in prose, quotes live `plane-status` rather than a
memorized mode, refuses to treat discuss as CF, and leaves a clean worktree.

---

## Related surfaces

| Doc | Role |
| --- | --- |
| [`fleet-comms-coordination.md`](../../agents_extensions/shared/rules/fleet-comms-coordination.md) | Binding mid-cutover musts on `/api/rules` |
| [`epic-orchestrator-roster.md`](epic-orchestrator-roster.md) | Which seat drives which epic (operator) |
| [`agent-cooperation.md`](../best-practices/agent-cooperation.md) | Deliberation, V2, review discipline |
| [`agent-runtime-guide.md`](../agent-runtime-guide.md) | `runner.invoke`, KimiCC headless, session policy |
| [`SCRIPTS.md`](../SCRIPTS.md) | Launcher and bridge command index |
| [`agent-activity-matrix.md`](../best-practices/agent-activity-matrix.md) | Fleet roster and capacity routing |
