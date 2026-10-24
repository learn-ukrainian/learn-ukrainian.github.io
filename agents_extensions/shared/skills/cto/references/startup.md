# Startup

Run in order before any dispatch, from the read-only primary checkout; scratch goes in the
session scratchpad (`<scratch>`).

## 0. This skill is the entry point

The `cto` agent loads this skill at start; it replaces the lane-driver entry point. Before
the first dispatch load the rules: `/api/rules?scope=core&format=markdown`,
`/api/rules?scope=task:driver&format=markdown` (offline: `agents_extensions/shared/rules/_load-via-api.md`) and
`agents_extensions/shared/rules/model-assignment.md`.

## 1. Confirm the launch

Confirm this session used the host CTO launcher `lu-start-cto [a|b] [--here]`, naming the account.
Never print or suggest the repository launcher script in a handoff or message; it skips account choice.
If not launched this way, do not drive: write the handoff, record a
[ledger](learning.md) entry, and ask for or perform a relaunch through that launcher.

## 2. Read the handoff and the mistakes ledger

FIRST run `lu-driver-state render --lane cto` for open items and
`lu-driver-state check --lane cto`. The database is the CTO state.
Then read `.claude/epics-epic/DRIVER-STATE.md`, which holds only pinned provider facts.
Treat `UNOWNED`, `STALE` and `OVERDUE` findings as a worklist. Read the program and plan
first: the `operator_order` item and its child `goal` items. Use `lu-driver-state show <id>`
for their full history and links, then read standing orders, the latest `handoff_note`,
in-flight work, blockers and the mistakes ledger (every open entry and the last ten closed
ones, [learning](learning.md)). The database is the seat's handoff; the markdown file is
only a pointer ([handoff](handoff.md)).

## 3. Resume exactly the named rollover

Resume only the lineage and rollover the launch prompt or newest handoff names, never one
chosen by title, with the `thread-rollover` skill (`references/resume.md`). A failed
confirmation means stop and reread the handoff; never guess answers. Leave every other
rollover candidate alone; archive one only through the `thread-rollover` skill.

## 4. Identity and inbox

Your inbox worker identity is `claude-cto-<session id>`. Drain the launcher's registered
slot and the epics recipients: `claude-epics` (`scripts/config/area_assignments.yaml`
`epics.slots`), `epics`, `cto` and `claude-cto`. The Fleet authority service admits every
exact recipient, even where a convenience CLI lists fewer. For each message run the
authority-delivery procedure in `docs/runbooks/driver-seat-cli-move.md` § 5: claim, read
the body, reconcile prior effects, apply or refuse, record the outcome, then ack with the
returned fence. Never ack or consume a supervisory request: it belongs to the launcher and
its watcher (`docs/runbooks/session-supervisor.md`).

## 5. Skip lane-driver items

The SessionStart banner and launch prompt for the epics lane also print lane-driver items.
They do not bind this seat: loading `drive-epic` as the entry point, the `driver_blockers`
delta and record posting, `.claude/epics-epic/CLAUDE-DRIVER-HANDOFF.md` as lane source of
truth (the CTO driver-state database is), and rollover candidates other than the named one.

## 6. Re-arm and cycle

Re-arm in the background `.venv/bin/python scripts/delegate.py wait <task-id> --run-nonce
<nonce>` for every live worker and any PR watcher the handoff names, then run the first
[cycle](cycle.md).

## Orders to lanes

Through Fleet Comms, never chat: publish an ordinary message to the lane's registered slot
(`docs/runbooks/driver-seat-cli-move.md` § 5).
