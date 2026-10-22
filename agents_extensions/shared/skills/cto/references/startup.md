# Startup

Run these in order before any dispatch. Commands run from the primary checkout root, which
is read-only: scratch files go in the session scratchpad (`<scratch>` below), never in the
tree.

## 1. Read the newest handoff block

Open the CTO state file (`.claude/epics-epic/DRIVER-STATE.md`) and read the newest
`HANDOFF FINAL` block first, then the provider-facts and standing-orders blocks it points
to. The handoff names the exact lineage and rollover to bind, the open PRs with heads, the
live workers with nonces and the next three actions. Older handoff blocks are history.

## 2. Bind exactly the named rollover

Bind only the lineage and rollover the launch prompt or newest handoff names; never an older
one and never one chosen by title. The general procedure is the `thread-rollover` skill
(`references/resume.md`); the CTO seat's sequence is:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py bind-replacement \
  --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> \
  --replacement-task-id <session id> --evidence "<binding receipt>"
.venv/bin/python scripts/orchestration/thread_handoff.py bootstrap-replacement \
  -a <agent> -l <lineage-id> -r <rollover-id> -t <session id> -e "<evidence>"
```

Then fill the packet's `semantic-snapshot.json` from its template using only the handoff
(real `source_ref` values, no padding). Run `confirm-replacement -a <agent> -l <lineage-id>
-r <rollover-id>`: the first run writes `strict-questions.json`. Write
`strict-answers.json` as a flat `{"<question id>": "<answer>"}` object from the handoff,
run `confirm-replacement` again (PASS), and a third time (`already_confirmed`). A FAIL
means the handoff is not restored: stop and reread it, never guess answers.

## 3. Set identity

The CTO inbox worker ID is `claude-cto-<session id>`. Export it for every inbox command:
`LU_INBOX_WORKER=claude-cto-<session id>`. Use only your own session ID and transcript.

## 4. Drain the inbox

Drain four recipients: `epics`, `cto`, `claude-cto`, `claude-epics`. Each message goes
through this order, and the acknowledgement always comes after the action, never before:

1. **Claim** into an empty scratch directory.
2. **Consume**: for a `supervisory-request`, record consumption (below).
3. **Reconcile**: if consumption reports `replay` or `reconciliation`, this delivery was
   seen before. Inspect the external outcome of the earlier action (PR, dispatch, comment)
   before doing anything; never repeat it blindly. Consumption proves intent, not completion.
4. **Act or refuse**: do what the message asks, or decide not to and say why.
5. **Persist the outcome**: record what was done (or the refusal) where the next session
   will find it.
6. **Acknowledge** last.

A crash between an early ack and the action loses the request for good, which is why the
ack waits. Claim without ack lets the lease expire; the delivery is re-queued and
dead-letters after three attempts, so finish each claimed message in the same pass.

The installed `lu-inbox` helper does claim and ack (`command -v lu-inbox`):

```bash
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> claim <recipient> <scratch>/in<n>-<recipient>
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> ack <scratch>/in<n>-<recipient>
```

For each `claims.json` entry whose `kind` is `supervisory-request`, consume, then record the
outcome after acting; `act_on_supervisory_delivery` and `refuse_supervisory_delivery` record
the outcome and acknowledge in one step:

```python
from scripts.fleet_comms.authority import AuthorityService
svc = AuthorityService(root=None)
seen = svc.record_supervisory_consumption(
    c["delivery_id"], worker_id="claude-cto-<session id>",
    fence_token=c["fence_token"], driver_generation="claude-cto-<session id>-g1")
# seen["replay"] or seen["reconciliation"]: inspect the earlier outcome first.
# ... act, or decide to refuse ...
svc.act_on_supervisory_delivery(
    c["delivery_id"], worker_id="claude-cto-<session id>",
    fence_token=c["fence_token"], acknowledgment=b"<outcome>")
# or svc.refuse_supervisory_delivery(..., result=b"<reason>")
```

`lu-inbox ack` re-acknowledges every entry in the directory without an outcome, which
conflicts with a supervisory delivery already finished with one. Use it only for a claim
directory with no supervisory entries; otherwise acknowledge each other entry after acting
on it with `svc.acknowledge_delivery(c["delivery_id"], worker_id=..., fence_token=c["fence_token"])`.
An ack that prints `"error"` means some deliveries were not acked: rerun the drain.

## 5. Re-arm what died with the last session

Background watchers, `delegate.py wait` calls and wake timers die with their session. For
every live worker the handoff lists, re-arm
`.venv/bin/python scripts/delegate.py wait <task-id> --run-nonce <nonce>` in the background,
and re-arm any PR verdict watcher it names. Then run the first [cycle](cycle.md).

## Sending orders and nudges

Orders to lanes go through Fleet Comms, never chat:

```python
from scripts.fleet_comms.authority import AuthorityService
m = AuthorityService(root=None).enqueue_supervisory_request(
    sender="claude-cto", recipient="<lane recipient>", body=body,
    correlation_id="<topic>", idempotency_key="<unique key>")
```

Stamp the body from the clock at send time (substitute a `{NOW}` placeholder with
`time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())` in the script), never a typed time.
