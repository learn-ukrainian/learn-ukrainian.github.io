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
| **ACPX** | Experimental **structured invocation transport only** — initially one read-only/stateless Codex participant behind a default-off/shadow feature flag | Persistent sessions, backlog, auto-retries, agent-to-agent chat, plane flips, review eligibility |
| **Buzz** | **Explicitly deferred** | Anything in this rollout — relay-as-authority conflicts with the current authority model |

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

**In scope (approved):**

- Feature-flagged adapter (default off / shadow comparison).
- Exactly one read-only/stateless **Codex** ACP participant for structured
  invocation.
- Correlation / idempotency fields recorded as **evidence**, not as a new
  authority source.
- Rollback = turn the feature flag off and use the existing native transport.

**Out of scope (forbidden in this rollout):**

- Persistent or named ACP sessions
- Queued prompt backlog
- Automatic prompt retries
- Direct ACP agent-to-agent chat
- Plane-mode or retention changes via ACPX
- Review-eligibility changes via ACPX
- Primary-checkout writes or write-mode ACP work

**Do not invent CLI flags or endpoints here.** The stable contract is the
runtime feature flag + adapter boundary owned by the integration worker. Exact
command wording is reconciled during assembly against the reviewed pin; this
runbook describes ownership and safety, not a floating CLI surface.

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
| Auth failure | Fail closed; do not retry in-adapter; fix credentials outside the adapter |
| Timeout / cancel | Treat as terminal for that prompt; no auto-replay |
| Crash / malformed NDJSON | Classify and record; do not promote partial output to authority |
| Duplicate correlation id | Treat as replay protection; do not double-apply side effects (there should be none) |
| Shadow mismatch | Keep the existing native/participant result authoritative; file evidence for infra |

#### Rollback

1. Disable the ACPX feature flag (default-off posture).
2. Continue on native agent runtime transport
   (`scripts/agent_runtime/` via `runner.invoke`, bridge, `delegate.py`).
3. Leave fleet-comms plane mode and formal-review eligibility unchanged.
4. Keep file dual-write handoffs current.

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
