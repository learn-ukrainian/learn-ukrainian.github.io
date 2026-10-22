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

## 3. Bind exactly the named rollover

Bind only the lineage and rollover the launch prompt or newest handoff names, never one
chosen by title (`thread-rollover` skill, `references/resume.md`):

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py bind-replacement \
  --agent <agent> --lineage-id <lineage-id> --rollover-id <rollover-id> \
  --replacement-task-id <session id> --evidence "<binding receipt>"
.venv/bin/python scripts/orchestration/thread_handoff.py bootstrap-replacement \
  -a <agent> -l <lineage-id> -r <rollover-id> -t <session id> -e "<evidence>"
```

Fill `semantic-snapshot.json` from its template using only the handoff (real
`source_ref`s). Run `confirm-replacement -a <agent> -l <lineage-id> -r <rollover-id>`
three times: it writes `strict-questions.json`; answer in `strict-answers.json` as a flat
`{"<question id>": "<answer>"}` from the handoff, then PASS, then `already_confirmed`.
A FAIL means stop and reread the handoff; never guess answers.

## 4. Identity and inbox

Export `LU_INBOX_WORKER=claude-cto-<session id>` for every inbox command. Drain `epics`,
`cto`, `claude-cto` and `claude-epics`. Per message: claim into an empty scratch
directory; consume a `supervisory-request`; on `replay` or `reconciliation` inspect the
earlier action's outcome before acting; act or refuse; persist the outcome; ack last. An
early ack loses the request on a crash; an unacked claim re-queues and dead-letters after
three attempts, so finish each claim in one pass.

```bash
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> claim <recipient> <scratch>/in<n>-<recipient>
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> ack <scratch>/in<n>-<recipient>
```

```python
from scripts.fleet_comms.authority import AuthorityService
svc = AuthorityService(root=None)
seen = svc.record_supervisory_consumption(
    c["delivery_id"], worker_id="claude-cto-<session id>",
    fence_token=c["fence_token"], driver_generation="claude-cto-<session id>-g1")
svc.act_on_supervisory_delivery(  # or refuse_supervisory_delivery(..., result=b"<reason>")
    c["delivery_id"], worker_id="claude-cto-<session id>",
    fence_token=c["fence_token"], acknowledgment=b"<outcome>")
```

Those two calls record the outcome and ack together. Use `lu-inbox ack` only for a claim
directory with no supervisory entries; otherwise ack the others one by one with
`svc.acknowledge_delivery(c["delivery_id"], worker_id=..., fence_token=c["fence_token"])`.
An ack printing `"error"` means rerun the drain.

## 5. Re-arm and cycle

Re-arm in the background `.venv/bin/python scripts/delegate.py wait <task-id> --run-nonce
<nonce>` for every live worker and any PR watcher the handoff names, then run the first
[cycle](cycle.md).

## Orders to lanes

Through Fleet Comms, never chat, with the body stamped by `time.gmtime()` at send time:

```python
AuthorityService(root=None).enqueue_supervisory_request(
    sender="claude-cto", recipient="<lane recipient>", body=body,
    correlation_id="<topic>", idempotency_key="<unique key>")
```
