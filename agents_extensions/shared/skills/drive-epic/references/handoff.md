# Handoff and fleet-comms state (drive-epic §8, fleet-comms state)

Read before ending a session or writing a handoff. The §8a inbox drain comes first and is
stated once in the core `SKILL.md` loop; record any action or unresolved request from it
in the lane tracker, and never claim the handoff is complete because a one-shot worker
acknowledged a message.

## §8. Handoff — dual-write, cutover-aware

End the session on your seat's handoff signal (canary FAIL-HANDOFF for grok/gemini/kimi;
the SessionStart / thread-handoff for Claude/Sonnet), not on a compact count. The
driver-state database is the lane's handoff through every plane mode (OO-63 and OO-86).

### Record work throughout the cycle

Use `lu-driver-state add --lane <lane>` for every new order, commitment, goal,
in-flight task, blocker, decision and next action. Use the matching kind, an owner
and a done condition. Record goals under their program's `operator_order` with
`--parent <id>`. Every `inflight` item includes the task ID and FULL run nonce;
`scripts/dispatch.py wait <task-id> --run-nonce <nonce>` compares the nonce exactly.

Update existing items with `link`, `note`, `evidence` and `status`. Attach references
with `link`, progress with `note`, and proof with `evidence`. Never delete items or
replace unfinished items with a new session summary. Use
`lu-driver-state status <id> done --reason <reason>` only after evidence supports
the done condition. A `dropped` status requires an operator reference in its reason.
Cite item IDs in cycle reports so unfinished work stays visible.

Tracker blocker items preserve lane continuity. Report blockers through Fleet Comms,
which remains the durable message authority.

### Reconcile and hand off

1. Timestamp with `date -u +%Y-%m-%dT%H:%MZ`.
2. Reconcile `lu-driver-state render --lane <lane>` and
   `lu-driver-state check --lane <lane>`. Every open order, goal, commitment,
   in-flight task, blocker, decision, parked item and next action must have an item.
3. Prepare the rollover with the `thread-rollover` skill. Add one `handoff_note`
   item with `lu-driver-state add --lane <lane> --kind handoff_note`, an owner and a
   done condition. Include the timestamp, session identity, exact lineage and
   rollover IDs, open PR heads and gates, live task IDs and FULL run nonces,
   armed waits, residual owners and resume conditions, and next actions. Cite the
   work item IDs; update those items rather than duplicating their history.
4. Keep `.claude/<lane>-epic/DRIVER-STATE.md` under 4 KB (`wc -c`). Its only content
   is pinned provider facts needed in every model call and instructions to run
   `lu-driver-state render --lane <lane>` and `lu-driver-state check --lane <lane>`
   first. Do not write a markdown handoff block or duplicate tracker state there.
5. Write the durable brief required by core.md P7 as a supplemental record,
   then complete the Entire dual-write and Fleet receipt below. Public briefs
   follow core.md P8; private detail stays in the driver-state database or the
   private infra repository.

On a Hramatka epic (#4542) drive, run `hramatka_hygiene_check` before declaring the
handoff verified-clean (`epic-specific.md` §0c).

**Skill source of truth is git, not deploy trees.** Edit only
`agents_extensions/shared/skills/drive-epic/` (`SKILL.md` and `references/`). Never
implement or "fix" process in `.claude/skills/` or other deploy-rsync targets — those
copies are overwritten on the next agents_extensions deploy and are not durable.

**Entire dual-write (Option A; driver-state database remains authoritative):** on every
session handoff, also project public continuity into entire-context. This is
**supplemental** (ADR-018): body-free locators only; never store residual narratives,
task ids, or OPSEC-sensitive prose only in Entire; never treat Entire as handoff
authority or replace the tracker with a capsule.

Durable sinks for the dual-write (not private deploy trees):

| Sink | What to write | Survives |
| --- | --- | --- |
| **Driver-state database** (`lu-driver-state`) | Work items, evidence, history and one `handoff_note` | Durable lane handoff |
| **Markdown pointer and durable brief** (`.claude/<lane>-epic/DRIVER-STATE.md`; core.md P7 brief) | Pinned provider facts and render/check instructions in the pointer; supplemental continuity in the brief | Local pointer / durable brief as applicable |
| **entire-context projection** (`batch_state/entire-context/…` via CLI) | `bootstrap-git` + capsule via `handoff` + `record-use` | Rebuildable local projection |
| **Fleet-comms channel** | Issue/PR numbers only | Plane authority |
| **GitHub issues** | Residual / next work | Public queue SSOT |

```bash
# 1) Index merge SHAs from this drive (idempotent) — writes the local projection
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha>   # repeat per merge

# 2) Body-free capsule to stdout (≤5 items). Optional: --locator-id clink_… from bootstrap.
#    Do NOT treat a tee into .claude/ as durable process storage (deploy-wiped).
#    For disposable scratch, follow the brief's §4 scratch contract.
.venv/bin/python -m scripts.entire_context handoff --query "<epic keywords>"

# 3) Attest consumption when locators informed the handoff
.venv/bin/python -m scripts.entire_context record-use \
  --task-id <epic-or-stream-id> --consumer <harness> --purpose handoff \
  --locator-id clink_…   # repeat up to the locators used

# 4) Fleet receipt: issue/PR numbers only (no residual tables, no secrets)
.venv/bin/python -m scripts.fleet_comms channel publish <stream-channel> \
  "handoff dual-write: tracker=SSOT entire=capsule. Next issues #… Merged PRs #…" \
  --sender "$SESSION_HANDOFF_AGENT" --source <harness> --kind state \
  --idempotency-key "handoff-<epic>-<date>"
```

Also attach the `driver_breadth_report` output (§3-routing item 6).

## Scoped residuals from #10439

The denominator remains nine behaviors. Behaviors 2-8 and the scratch half of 9
are in scope; two residuals remain visible:

- Behavior 1, the authority-plane delivery drain procedure. Owner: infra/harness.
  Reopen when `fleet-comms-coordination.md` and the seat-onboarding live-delivery
  paragraph name the authority drain in their own change. The existing core inbox
  block and its legacy counts stay exactly as they are.
- Behavior 9's executing-review-at-first-push half. Owner: harness lane. Reopen
  when the review-route policy names it. The existing launcher/hook test step and
  execution-dependent review route remain binding.

## Fleet-comms state — dual-aware, cutover is closed

The message plane's `authority` cutover is **done**: mode `authority` is the production
default (operator GO 2026-08-01, closed with evidence on
[#6159](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6159)).
Fleet-comms is now durable authority for messages/jobs; legacy broker/channel file
stores are read-only migration/projection inputs, not a live write target. Query the
live mode at orient (`orient.md` §0); do not hard-code it.

- **Lane continuity:** Fleet Comms is durable authority for messages/jobs; the
  driver-state database holds lane work and the `handoff_note`. Keep the markdown
  pointer and supplemental durable brief as described in §8. Live-driver diagnostics use `session_streams
  handoff-status` (#5530). Live drivers never run `handoff-claim`: the launcher
  has already claimed the lease. `handoff-claim` belongs to the successor
  launcher / proof-gated dead-holder recovery in the local/offline contract
  only; it cannot recover a remote lease. Remote recovery uses Monitor TTL/CAS
  or an attributed operator release, never local PID observations or `--local`.
- **CF and ACP:** sealed formal CF is retired and ACP is toolless intercomm only
  (`review-merge-cleanup.md` §6).
- **Never** flip the plane, enable retention apply, or invent a competing comms design
  from this skill — those remain the infra lane's gated actions, even post-cutover.
