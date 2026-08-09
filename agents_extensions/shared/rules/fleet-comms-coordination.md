# Fleet-comms coordination (binding authority cutover)

<critical>

**Cutover issue:** #6159 · **Stream:** #4707 (infra-harness) · **Operator GO:** 2026-08-01
**Applies to:** every standalone TUI/UI and epic-driver seat (Claude/Sonnet, Grok, AGY/Gemini, Kimi, Cursor, wrappers) — not only agents that load a skill.

This is the **shared-context SSOT** for coordination after the fleet-comms authority cutover. It is
served in `GET /api/rules`. Launchers inject a short pointer; the **`drive-epic` skill**
teaches the full method loop. Neither may invent a competing design or silently flip
cutovers.

Aligned with the post-#5632 surface (drive-epic + per-model drive wrappers + Sol CF on
that skill). Do not reintroduce claims Sol rejected (see §Plane modes).

## Layering (do not conflate)

| Layer | Role | Where |
| --- | --- | --- |
| **This rule** | Binding musts for every TUI/UI cold-start | `/api/rules` + offline path |
| **Seat onboarding contract** | Task-oriented ownership matrix (discuss / delegate / fleet-comms / ACPX / Buzz deferred), Kimi routes, smoke | `docs/runbooks/agent-seat-onboarding.md` |
| **`drive-epic` skill** | Method playbook (orient → topology → route → dispatch → settle → CF → merge → handoff) | `agents_extensions/shared/skills/drive-epic/SKILL.md` |
| **Epic roster runbook** | Operator seat routing (which model drives which epic) | `docs/runbooks/epic-orchestrator-roster.md` |
| **Live routing data** | Caps, ladders, reviewer seats, **live plane mode** | `/api/rules` model-assignment + `scripts/config/model_catalog.yaml` + `scripts/config/fleet_communications.yaml` + `plane-status` |
| **Launchers** | Lease claim + dual-aware pointer (not a second design) | interactive `start-*.sh`, provider `start-*-driver.sh` |

**Golden rule (from drive-epic):** rules + skill teach **method**; roster/caps/modes are
**live data** — always re-read; never hard-code from memory. Fresh supported seats start
at the **onboarding contract** for ownership and experimental ACPX scope; this rule does
**not** duplicate mutable model pins, effort ladders, or a hard-coded live plane mode.

## Two halves (do not conflate)

| Half | Status | Surfaces |
| --- | --- | --- |
| **Session stream / lease** | Live | `claim_session_supervisor_env`, `SESSION_STREAM_*`, stream tail/digest, canary mint (hook-less seats) |
| **Message plane + CF-comms** | Authority | `scripts.fleet_comms`; PR CF via direct `ask-*` + PR comment (sealed `review-pr` RETIRED) |

Launchers already claim leases. Drivers must **also** speak the message-plane + CF half.

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
# ONE round. Ask a cross-family lane for verdict + findings at the current head,
# then post on the PR (gh pr comment / gh pr review). Merge when CI is green.
# Then reap worktrees + temps (drive-epic §7a / reap_worktrees.py --apply).
printf '%s\n' "Cross-family review of PR #<N> at head <SHA>: verdict + findings." | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - --task-id review-<N> --type review
# SHIELDED formal path (review-pr / lu-review snaps / shielded-reviews) is RETIRED —
# do not run it. CLI fails closed unless LU_FORMAL_SHIELDED_CF=1 (unit tests only).
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

- Cross-family review is **direct only** (`ask-<lane>` + post verdict on the PR).
  Shielded formal `review-pr` / eligibility pins are RETIRED (operator 2026-08-07).
  Route the reviewer seat by model-assignment (outside the author's family).

## Standalone TUI/UI contract

Every epic driver session (any harness) MUST:

1. Obey this rule (via `/api/rules` or offline fallback of this file).
2. Run `plane-status` before assuming message-plane availability.
3. Use fleet-comms for durable coordination, queues, messages, conversations, artifacts,
   retries, dead letters, receipts, formal jobs, and session continuity. In authority
   mode, never create a new legacy bridge/channel/broker/file coordination write.
4. Review of record = ONE cross-family round posted on the PR at the current head
   (direct ask + posted verdict). **Shielded formal CF (`review-pr`, sealed MCP,
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
8. **Post-merge cleanup is mandatory** (operator 2026-08-07). A squash-merge is not
   done until worktree + branch + any temp residue for that PR are reaped and
   `df -h /` + `git worktree list` prove no zombie. Prefer
   `scripts/orchestration/reap_worktrees.py --apply` (also sweeps review temps
   under `$TMPDIR` and `$TMPDIR/shielded-reviews`). Do not create formal sealed
   review trees. Session chat promises do not bind; this rule and §7a do.
   The P0 automatic reaper is live: for a merged exact head, use
   `.venv/bin/python -m scripts.orchestration.reap_worktrees --apply --merged`;
   `LU_REAPER_DISABLED=1` is its immediate kill switch.
   `post_task_reap` delegates regular dispatch cleanup to that same reaper, so do not invent a
   second deletion path. If it cannot run, follow `docs/runbooks/worktree-cleanup.md` for
   rescue restore and the narrowly allowlisted manual fallback.

## Operator launch surface (#5632)

- Driver entrypoints: `./start-grok-driver.sh --epic <epic>`,
  `./start-gemini-driver.sh --epic <epic>`,
  `./start-claude-driver.sh --epic <epic> [--model claude-fable-5|claude-sonnet-5]`,
  and `./start-codex-driver.sh --epic <epic>`. Interactive launchers reject `--epic`.
- Seat routing reminder: `docs/runbooks/epic-orchestrator-roster.md` (Gemini→harness/corpus,
  Grok→atlas/tracks, Sonnet-5→judgment-dense, Opus→hardest-judgment exception only — it
  spends the cross-family review-of-record seat). **Live policy** is still
  `model_catalog.orchestrator_seats` + `/api/rules`.
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
Review of record = one direct cross-family `ask-*` + posted PR verdict. ACP is
structured provider transport for ordinary `ask-*` / `discuss`; fleet-comms owns
durable coordination state.

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
transport. Fleet launchers make ordinary `ask-*` and 2–6 participant `discuss`
calls use the durable ACP controller for enabled routes: Codex, Grok, Claude,
Kimi, KimiCC K3, Cursor, Pool, AGY, GLM, and DeepSeek. The direct
`.venv/bin/python -m scripts.fleet_comms acp-discuss` surface remains available
to operators. Selection starts no process at cold start and does not change
`delegate.py`. The default is two rounds and the hard maximum is three.

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
Served in `GET /api/rules` (`scripts/api/rules_router.py` `RULE_SOURCES`).
Onboarding contract (not served as a rules blob; linked from this rule):
`docs/runbooks/agent-seat-onboarding.md`.

</critical>
