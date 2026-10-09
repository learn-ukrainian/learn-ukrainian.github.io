# Fleet-comms coordination (binding authority cutover)

<critical>

**Cutover issue:** #6159 · **Stream:** #4707 (infra-harness) · **Operator GO:** 2026-08-01
**Applies to:** every standalone TUI/UI and epic-driver seat (Claude/Sonnet, Grok, Kimi, Cursor, wrappers; AGY/Gemini only as a standalone TUI seat, never an epic-driver seat) — not only agents that load a skill.

This is the **shared-context SSOT** for coordination after the fleet-comms authority cutover. It is
served in `GET /api/rules?scope=task:fleet-comms`, `scope=task:driver`, or `scope=full`.
Launchers inject a short pointer; the **`drive-epic` skill**
teaches the full method loop. Neither may invent a competing design or silently flip
cutovers.

Aligned with the post-#5632 surface (drive-epic + per-model drive wrappers + Sol CF on
that skill). Do not reintroduce claims Sol rejected (see §Plane modes).

## Layering (do not conflate)

| Layer | Role | Where |
| --- | --- | --- |
| **This rule** | Binding musts for every TUI/UI cold-start | `/api/rules?scope=task:fleet-comms` (or `scope=task:driver` / `scope=full`) + offline path |
| **Seat onboarding contract** | Task-oriented ownership matrix (discuss / delegate / fleet-comms / ACPX / Buzz deferred), Kimi routes, smoke | `docs/runbooks/agent-seat-onboarding.md` |
| **`drive-epic` skill** | Method playbook (orient → topology → route → dispatch → settle → CF → merge → handoff) | `agents_extensions/shared/skills/drive-epic/SKILL.md` |
| **Epic roster runbook** | Operator seat routing (which model drives which epic) | `docs/runbooks/epic-orchestrator-roster.md` |
| **Live routing data** | Caps, ladders, reviewer seats, **live plane mode** | `/api/rules?scope=task:routing` (or `scope=full`) model-assignment + `scripts/config/model_catalog.yaml` + `scripts/config/fleet_communications.yaml` + `.venv/bin/python -m scripts.fleet_comms plane-status` |
| **Launchers** | Lease claim + dual-aware pointer (not a second design) | interactive `start-*.sh`, provider `start-*-driver.sh` |

**Golden rule (from drive-epic):** rules + skill teach **method**; roster/caps/modes are
**live data** — always re-read; never hard-code from memory. Fresh supported seats start
at the **onboarding contract** for ownership and experimental ACPX scope; this rule does
**not** duplicate mutable model pins, effort ladders, or a hard-coded live plane mode.

## Communication & execution layers (do not conflate)

| Layer | Role |
| --- | --- |
| Fleet-comms | Durable authority for queues, receipts, jobs |
| ACP / ACPX | Toolless provider transport for ordinary inter-agent asks/discuss only |
| Toolful native / `delegate.py` | Plan, create, review, design, implementation |
| Caveman | Optional output-style compression (lite default); never persisted GitHub/curriculum text |

- ACP / ACPX are **toolless**. Use them only for inter-agent communication (state transfer). Do **not** use `ask-*` ACP/ACPX for plan, create, review, or design tasks.
- For plan, create, review, and design, use **toolful** native or `delegate.py` seats (claude/codex/glm/opencode; agy only for bounded task-level work, never plan or design, operator decision 2026-10-03, #9584; Kimi takes web, UI and backend coding only, never plan, review or design).
- Explicit: `ask-* --type review` over ACP is **not** the review-of-record path when the reviewer needs to read the tree. Review of record = qualified toolful approval before PR, then `record_cf_verdict.py` binding + same-head CI (drive-epic §6–§7).
- Caveman is **style**, not transport. Default intensity: **lite** (drop filler/hedging, keep articles and full sentences). Never use it as a substitute for fleet-comms durable state, and never caveman persisted artifacts (commits, PR/issue bodies, curriculum, runbooks, review-of-record text posted on GitHub).

## Two halves (do not conflate)

| Half | Status | Surfaces |
| --- | --- | --- |
| **Session stream / lease** | Live | `claim_session_supervisor_env`, `SESSION_STREAM_*`, stream tail/digest, canary mint (hook-less seats) |
| **Message plane + CF-comms** | Authority | `scripts.fleet_comms`; PR CF via toolful review + `record_cf_verdict.py` (sealed `review-pr` RETIRED) |

Driver launchers already claim stream leases. Drivers must **also** speak the
message-plane + CF half. An occupied lease fails closed: do not start a second
supervisor, open/resume the stream yourself, or switch to local lease authority.
Remote leases remain live until `expires_at`; a local PID is not remote liveness
proof. Wait for expiry or an attributed operator release through the existing
supervisor flow.

The live driver reads and applies its inbox, then acknowledges consumption with
`ack --consumed-by-live-driver <message-id>` through the project bridge CLI.
Plain `ack` and detached worker receipts do not prove live-driver consumption.
Use the launcher's `SESSION_HANDOFF_AGENT` identity; do not borrow another seat's
identity or infer it from the provider/model name.

## Plane modes

```bash
.venv/bin/python -m scripts.fleet_comms plane-status
```

Implemented modes are `off` | `shadow` | `dual_write` | `authority`. Production
default is **`authority`** after the present-tense operator GO in #6159. Override
only for an explicit rollback or compatibility probe.

| Fact | Binding |
| --- | --- |
| `authority` mode | Fleet-comms is the durable source of truth; legacy stores are read-only migration/projection sources |
| `dual_write` mode | Compatibility soak/rollback mode, not normal operation |
| ACP | Provider transport only; durable queues, retries, conversations, artifacts, and receipts belong to fleet-comms |
| Who may roll back authority / retention apply / eligibility | **Infra/harness lane** with present-tense operator/advisor approval |

Do not create new authoritative bridge, channel, broker, or diary writes. Historical
stores stay available through bounded read-only projections and idempotent migration.
Session handoff files still carry continuity, not competing message or lease authority.
Preserve required handoff continuity without creating new legacy message/job writes
or another control plane; existing stream ownership remains binding.

Forbidden: inventing a third message bus; encoding only file-handoff folklore in new
cold-prompts; silent plane flips; “for now” cutovers.

## Required primitives (tool-backed)

```bash
# Topology / health / parity
.venv/bin/python -m scripts.fleet_comms plane-status
.venv/bin/python -m scripts.fleet_comms metrics
.venv/bin/python -m scripts.fleet_comms backlog
.venv/bin/python -m scripts.fleet_comms dead-letters

# Continuity (lease already claimed by launcher — do not re-open)
.venv/bin/python -m agents_extensions.shared.session_streams tail --stream epic:<N> --limit 20
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status

# Cross-family PR review — DIRECT only (operator 2026-08-06; sealed formal RETIRED 2026-08-07):
# Push the author branch, then get exact-head APPROVE before opening any PR.
# Delegate admission pins the remote-tracking target; fetch refuses movement.
# Compare task pinned_head/worktree_base_sha with the pushed tip, not ask stdout.
# Ask waits synchronously without nonce; on expiry continue the same task/nonce
# using drive-epic §6's wait recipe, never repeat this launch.
printf '%s\n' "Review pushed branch <branch> at its resolved remote head; return verdict + findings." | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - \
    --task-id review-<id> --review --branch <branch>
# Only after APPROVE matches that SHA, open the PR and bind the completed review:
.venv/bin/python scripts/review/record_cf_verdict.py --task-id review-<id> --pr <N>
# Then require CI on that same SHA before landing; see drive-epic §7 / §7a for cleanup.
# SHIELDED formal path (review-pr / lu-review snaps / shielded-reviews) is RETIRED —
# do not run it. Its commands were removed in #8520, and the snapshot flow is
# refused with no bypass.
```

### Routing observability contract

Use `/runtime.html` → **Routing overview**, or the body-free
`GET /api/runtime/routing-assignments?limit=100` projection, to diagnose which
orchestrator initiated a request, whether selection was automatic or explicit,
which route/model was admitted, and how the reservation terminated. Summary
cards, lifecycle groups, filters, and route distributions cover only the
loaded recent window; they are not all-time totals, routing weights, provider
quotas, or caching evidence.

Inspect the chronological event and selection trace before attributing
concentration to an orchestrator or scheduler. A “No ledger update” cue is
stale activity evidence, not provider-liveness proof and not authority to
reclaim a lease early. Corroborate headroom with CodexBar and durable authority
job/reservation state. The dashboard is read-only: its filters, search,
details, and load-more controls never select, retry, cancel, reclaim, or reroute
work.

- Cross-family review is **direct only** (qualified toolful APPROVE before PR, then
  `record_cf_verdict.py` binding + same-head CI; drive-epic §6–§7).
  Shielded formal `review-pr` / eligibility pins are RETIRED (operator 2026-08-07).
  Route the reviewer seat by model-assignment (outside the author's family).

## Standalone TUI/UI contract

Every epic driver session (any harness) MUST:

1. Obey this rule (via `/api/rules?scope=task:fleet-comms`, `scope=task:driver`,
   `scope=full`, or offline fallback of this file).
2. Run `.venv/bin/python -m scripts.fleet_comms plane-status` before assuming message-plane availability.
3. Use fleet-comms for durable coordination, queues, messages, conversations, artifacts,
   retries, dead letters, receipts, formal jobs, and session continuity. In authority
   mode, never create a new legacy bridge/channel/broker/file coordination write.
4. Review of record = one round of direct cross-family review on the pushed branch before the PR;
   after opening the PR, `record_cf_verdict` binds the completed review to its
   head and author qualification. **Shielded formal CF (`review-pr`, sealed MCP,
   multi-GB `lu-review-*` / `shielded-reviews` clones) is RETIRED** (operator
   2026-08-07) — disk and process harm outweighed isolation benefit. Discussion
   and same-family chat are still not the gate.
5. Treat launcher-claimed stream leases as held — do not open/resume the lease yourself.
6. **Session health by seat:**
   - **grok / gemini / kimi:** canary mint/score
     (`.venv/bin/python -m scripts.session_canary.{grok,gemini,kimi}_lane …`); end on
     FAIL-HANDOFF (&lt;8/10), not compact count.
   - **Claude / Sonnet:** SessionStart / PostCompact + thread-handoff — **no** canary lane
     (do not invent `<model>_lane`).
7. Provider drivers inject the **`drive-epic`** binding after their lease and
   provider canary. Interactive launchers never claim a driver lease.
8. **Post-merge cleanup is mandatory.** Follow the single recipe in
   `agents_extensions/shared/rules/workflow.md` § Merge policy / Post-merge
   cleanup: MERGED, worker exit, common-reaper exit 0 and residue-free receipts.
   Never create formal sealed review trees, force removal or invent a second
   deletion path. `LU_REAPER_DISABLED=1` remains the reaper's immediate kill switch.
   If it cannot run, use only the rescue restore and narrowly allowlisted manual
   fallback in `docs/runbooks/worktree-cleanup.md`.

## Operator launch surface (#5632)

- Driver entrypoints: `./start-grok-driver.sh --epic <epic>`,
  `./start-claude-driver.sh --epic <epic> [--model claude-fable-5-1|claude-sonnet-5-5]`,
  and `./start-codex-driver.sh --epic <epic>`. Interactive launchers reject `--epic`.
- Gemini/AGY (Flash) is not an epic-driver seat (operator decision 2026-10-03, #9584).
- Seat routing reminder: `docs/runbooks/epic-orchestrator-roster.md` (Grok→atlas/tracks, Sonnet 5.5→well-scoped routine work, Opus→hard Claude-lane work — it
  spends the cross-family review-of-record seat). **Live policy** is still
  `model_catalog.orchestrator_seats` + `/api/rules?scope=task:routing` (or `scope=full`).
- **Codex is the named alternate for the harness / infra and DevOps streams** (re-added
  2026-07-23 after HydrationCapsuleV1 changed the rollover-cost calculus). Its launcher
  fails closed before lease acquisition on ambiguous, already-resumed, or native-app
  rollover packets; a fresh CLI packet is bound to the exact SessionStart task ID and
  the generated cold-start board is injected automatically. Infra uses `epic:4707`;
  DevOps independently uses `epic:5703`. Codex never concurrently co-owns a same-stream
  lease and remains a formal-CF **review** + coding lane.

## Ownership pointer (do not invent a second design)

Supported fleet seats cold-start through:

1. This rule (binding fleet-comms musts).
2. **`docs/runbooks/agent-seat-onboarding.md`** — ownership matrix for `discuss`,
   `delegate.py dispatch`, Fleet Comms authority + read-only legacy projections,
   experimental ACPX (default-off/shadow, one read-only/stateless Codex
   participant), and **Buzz deferred**. Also covers Kimi native (default; K3
   max-only) vs explicit KimiCC (K3 defaults `high`), rollback, and no-auth
   fresh-agent smoke.

Discussion is never the review of record. **Shielded formal CF (`review-pr` /
`publish-review-verdict` / sealed `lu-review-*`) is RETIRED** (operator 2026-08-07).
Review of record = one direct cross-family `ask-* --review --branch <name>` on
the pushed branch before PR creation, followed after PR creation by
`record_cf_verdict` to bind the completed review, head, and author qualification.
ACP is structured provider transport for ordinary `ask-*` / `discuss`; fleet-comms
owns durable coordination state.

### CF thrash ban (operator 2026-08-06; formal path retired 2026-08-07)

Agents MUST NOT:

1. Push **empty commits** whose only purpose is re-triggering review / CI reseal.
2. Re-request the same cross-family review when the PR head already has an
   explicit APPROVED verdict for that SHA (idempotent stop).
3. Burn another review seat when the tip tree is unchanged and no product delta
   landed.
4. Spend scarce review seats while **GitHub Actions** is in outage/degraded
   (check githubstatus) unless the operator overrides.

Never auto-reset branches for review thrash. Do not reintroduce sealed formal CF.

## ACP provider transport

For normal **read-only inter-agent communication**, ACP is the only provider
transport. Fleet launchers make ordinary (non-review) `ask-*` and `discuss`
calls that name **2 to 4 distinct enabled seats** use the durable ACP controller:
Codex, Grok, Claude, Cursor, Pool, AGY, GLM, and DeepSeek. Kimi seats are never participants (web, UI and backend coding only; the runtime refuses them).
Any other participant count is rejected
loudly before a conversation begins. The direct `.venv/bin/python -m
scripts.fleet_comms acp-discuss` surface remains available to operators.
Selection starts no process at cold start and does not change `delegate.py`.
The default is two rounds and the hard maximum is three.

**ACP is intercommunication only — never review** (operator 2026-08-23,
#7155). Its `--deny-all --no-fs --no-terminal` chat transport cannot run
`gh`/pytest/fs, so a reviewer seated there cannot ground a verdict (live
proof: `ask-codex --review --pr 7155` ABSTAINed via ACP with `gh auth`
unavailable; the same review via headless dispatch with tools approved).
For pre-PR CF, `ask-<lane> --review --branch <name>` uses native dispatch +
synchronous wait. Delegate admission pins the remote-tracking target and fetch
refuses movement; compare task SHA evidence, not reply stdout (drive-epic §6).
Require qualified outside-family APPROVE before PR, then bind it with
`record_cf_verdict.py` and require same-head CI. Continue an expired wait on
the same task/nonce (§6), never repeat the launch.
`--pr` targets an existing PR; only non-review `ask-*` stays on ACP.

There is no bridge/provider-execution fallback. Unknown routes, invalid model or
effort overrides, unavailable ACP, cancellation, timeout, and partial results are
typed durable outcomes and never trigger a second provider call. Fleet-comms owns
bounded queueing, leases, deadlines, retries, dead letters, idempotency, transcripts,
and wake receipts. ACP output is deliberation evidence: a typed partial outcome is
valid evidence but never a successful discussion or formal review. The
exact command, primary-install and body-free `acp-verify` E2E/replay procedure
are in the onboarding contract.

## Offline fallback path

`agents_extensions/shared/rules/fleet-comms-coordination.md` (this file).
Served in `GET /api/rules?scope=task:fleet-comms` or `scope=task:driver`, and in
`GET /api/rules?scope=full` (`scripts/api/rules_router.py` `RULE_SOURCES`).
Onboarding contract (not served as a rules blob; linked from this rule):
`docs/runbooks/agent-seat-onboarding.md`.

</critical>
