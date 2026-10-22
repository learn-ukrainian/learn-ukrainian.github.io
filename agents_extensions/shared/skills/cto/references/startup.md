# Startup

Run in order before any dispatch, from the read-only primary checkout; scratch goes in the
session scratchpad (`<scratch>`).

## 1. Confirm the launch

Confirm this session was started by the CTO launcher (see the private operations doc), not
the plain repository wrapper or an ad hoc relaunch script: the launcher sets the CTO role
prompt and the permission mode. If not, do not drive: write the handoff, record a
[ledger](learning.md) entry, and ask for or perform a relaunch through that launcher.

## 2. Read the handoff and the mistakes ledger

In the CTO state file (`.claude/epics-epic/DRIVER-STATE.md`) read the newest
`HANDOFF FINAL` block, the provider-facts and standing-orders blocks it names, then the
mistakes ledger: every open entry and the last ten closed ones ([learning](learning.md)).
Older handoff blocks are history.

## 3. Resume exactly the named rollover

Resume only the lineage and rollover the launch prompt or newest handoff names, never one
chosen by title, with the `thread-rollover` skill (`references/resume.md`). A failed
confirmation means stop and reread the handoff; never guess answers.

## 4. Identity and inbox

Your inbox worker identity is `claude-cto-<session id>`. Drain `epics`, `cto`,
`claude-cto` and `claude-epics`: claim, reconcile prior effects, act or refuse, record the
outcome, then ack, as `docs/runbooks/driver-seat-cli-move.md` § 5 describes. Supervisory
requests belong to the launcher and its watcher, never to the seat
(`docs/runbooks/session-supervisor.md`).

## 5. Re-arm and cycle

Re-arm in the background `.venv/bin/python scripts/delegate.py wait <task-id> --run-nonce
<nonce>` for every live worker and any PR watcher the handoff names, then run the first
[cycle](cycle.md).

## Orders to lanes

Through Fleet Comms, never chat: publish an ordinary message to the lane's registered slot
(`docs/runbooks/driver-seat-cli-move.md` § 5).
