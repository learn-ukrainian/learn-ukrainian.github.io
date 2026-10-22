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

Drain four recipients: `epics`, `cto`, `claude-cto`, `claude-epics`. For each, claim into
an empty scratch directory, read every message, record consumption for supervisory
requests, then ack. Claim without ack lets the lease expire; the delivery is re-queued and
dead-letters after three attempts, so ack every claim in the same pass.

Put the loop in a scratch script, not an inline shell loop (see
[recipes](recipes.md#primary-checkout-write-guard)). The installed `lu-inbox` helper does
claim and ack (`command -v lu-inbox`):

```bash
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> claim <recipient> <scratch>/in<n>-<recipient>
LU_INBOX_WORKER=claude-cto-<session id> .venv/bin/python <lu-inbox> ack <scratch>/in<n>-<recipient>
```

Between claim and ack, for each `claims.json` entry whose `kind` is `supervisory-request`:

```python
from scripts.fleet_comms.authority import AuthorityService
AuthorityService(root=None).record_supervisory_consumption(
    c["delivery_id"], worker_id="claude-cto-<session id>",
    fence_token=c["fence_token"], driver_generation="claude-cto-<session id>-g1")
```

Apply each message (act, answer or record why not) before the next dispatch. An ack that
prints `"error"` means some deliveries were not acked: rerun the drain.

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
