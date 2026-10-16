# Handoff and fleet-comms state (drive-epic §8, fleet-comms state)

Read before ending a session or writing a handoff. The §8a inbox drain comes first and is
stated once in the core `SKILL.md` loop; record any action or unresolved request from it
in the file handoff, and never claim the handoff is complete because a one-shot worker
acknowledged a message.

## §8. Handoff — dual-write, cutover-aware

End the session on your seat's handoff signal (canary FAIL-HANDOFF for grok/gemini/kimi;
the SessionStart / thread-handoff for Claude/Sonnet), not on a compact count. Keep the
file handoff current — it stays authoritative through every plane mode.

On a Hramatka epic (#4542) drive, run `hramatka_hygiene_check` before declaring the
handoff verified-clean (`epic-specific.md` §0c).

**Skill source of truth is git, not deploy trees.** Edit only
`agents_extensions/shared/skills/drive-epic/` (`SKILL.md` and `references/`). Never
implement or "fix" process in `.claude/skills/` or other deploy-rsync targets — those
copies are overwritten on the next agents_extensions deploy and are not durable.

**Entire dual-write (Option A — operator GO 2026-08-02; file remains SSOT):** on every
session handoff, also project public continuity into entire-context. This is
**supplemental** (ADR-018): body-free locators only; never store residual narratives,
task ids, or OPSEC-sensitive prose only in Entire; never treat Entire as handoff
authority or retire the file on your own.

Durable sinks for the dual-write (not private deploy trees):

| Sink | What to write | Survives |
| --- | --- | --- |
| **File handoff** (local operational SSOT; gitignored `.claude/<epic>-epic/*` or `docs/session-state/` when the epic uses a tracked pointer) | Next queue, residual narrative | Local session / tracked pointer as applicable |
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
  "handoff dual-write: file=SSOT entire=capsule. Next issues #… Merged PRs #…" \
  --sender "$SESSION_HANDOFF_AGENT" --source <harness> --kind state \
  --idempotency-key "handoff-<epic>-<date>"
```

Also attach the `driver_breadth_report` output (§3-routing item 6).

## Scoped residuals from #10439

The denominator remains nine behaviors. Behaviors 2-8 and the scratch half of 9
are in scope; two residuals remain visible:

- Behavior 1, the authority-plane delivery drain procedure. Owner: infra/harness.
  Reopen when `fleet-comms-coordination.md` and the seat-onboarding live-delivery
  paragraph name the authority drain in their own change. For #10439 only, the
  core inbox block and its legacy counts stay exactly as they are. Follow-up
  #10441 owns the canonical procedure, onboarding link, and mode-aware core inbox
  block. Its residual remains until deployment and fresh-driver live queue proof;
  codex-monitor owns those gates and final disposition.
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

- **File handoff still matters:** fleet-comms is durable authority for messages/jobs,
  but you still write file continuity where the epic uses one (`.claude/<epic>-epic/
  *DRIVER-HANDOFF.md` — gitignored local state — or `docs/session-state/` for infra); see
  the file-handoff steps in §8. Live-driver diagnostics use `session_streams
  handoff-status` (#5530). Live drivers never run `handoff-claim`: the launcher
  has already claimed the lease. `handoff-claim` belongs to the successor
  launcher / proof-gated dead-holder recovery in the local/offline contract
  only; it cannot recover a remote lease. Remote recovery uses Monitor TTL/CAS
  or an attributed operator release, never local PID observations or `--local`.
- **CF and ACP:** sealed formal CF is retired and ACP is toolless intercomm only
  (`review-merge-cleanup.md` §6).
- **Never** flip the plane, enable retention apply, or invent a competing comms design
  from this skill — those remain the infra lane's gated actions, even post-cutover.
