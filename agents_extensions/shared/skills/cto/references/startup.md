# Startup

Run in order before any dispatch, from the read-only primary checkout; scratch goes in the
session scratchpad (`<scratch>`).

## 0. This skill is the entry point

The `cto` agent loads this skill at start; it replaces the lane-driver entry point. Before
the first dispatch load the rules: `/api/rules?scope=core&format=markdown`,
`/api/rules?scope=task:driver&format=markdown` (offline: `agents_extensions/shared/rules/_load-via-api.md`) and
`agents_extensions/shared/rules/model-assignment.md`.

## 1. Confirm the launch

Confirm this session was started by the CTO launcher (see the private operations doc), not
the plain repository wrapper or an ad hoc relaunch script: the launcher sets the CTO role
prompt and the permission mode. If not, do not drive: write the handoff, record a
[ledger](learning.md) entry, and ask for or perform a relaunch through that launcher.

## 2. Read the handoff and the mistakes ledger

The CTO state file (`.claude/epics-epic/DRIVER-STATE.md`) is the seat's only handoff.
Search it for the newest `HANDOFF FINAL` heading and read from there: that block, the
provider-facts and standing-orders blocks it names, then the mistakes ledger (every open
entry and the last ten closed ones, [learning](learning.md)). Older handoff blocks are
history; if the file is over its [budget](handoff.md), trim it at this session's handoff.

## 3. Resume exactly the named rollover

Resume only the lineage and rollover the launch prompt or newest handoff names, never one
chosen by title, with the `thread-rollover` skill (`references/resume.md`). A failed
confirmation means stop and reread the handoff; never guess answers. Leave every other
rollover candidate alone; archive one only through the `thread-rollover` skill.

## 4. Identity and inbox

Your inbox worker identity is `claude-cto-<session id>`. Drain the recipients the supported
inbox path accepts for this seat: `epics`, `cto` and `claude-cto`. For each message apply
it (act, or refuse with the reason), record the outcome, then ack it as consumed by the
live driver (`drive-epic` § The loop). Never ack or consume a supervisory request: it
belongs to the launcher and its watcher (`docs/runbooks/session-supervisor.md`).

## 5. Skip lane-driver items

The SessionStart banner and launch prompt for the epics lane also print lane-driver items.
They do not bind this seat: loading `drive-epic` as the entry point, the `driver_blockers`
delta and record posting, `.claude/epics-epic/CLAUDE-DRIVER-HANDOFF.md` as lane source of
truth (the CTO state file is), and rollover candidates other than the named one.

## 6. Re-arm and cycle

Re-arm in the background `.venv/bin/python scripts/delegate.py wait <task-id> --run-nonce
<nonce>` for every live worker and any PR watcher the handoff names, then run the first
[cycle](cycle.md).

## Orders to lanes

Through Fleet Comms, never chat: publish an ordinary message to the lane's registered slot
(`docs/runbooks/driver-seat-cli-move.md` § 5).
