# Stalled dispatch work

Issue #11212 returns committed work to its dispatching lane until it lands or
the owner explicitly abandons it. The report scans hot task records younger
than 14 days and open PRs in the public repository. It imports the existing
stale-record classifiers without settling, archiving or editing any record.

```bash
.venv/bin/python -m scripts.orchestration.stalled_work stalled
.venv/bin/python -m scripts.orchestration.stalled_work stalled --route
```

The JSON rows name the task, dispatch `initiator` lane, commit or PR, stall
kind, starting timestamp and age in hours. Unrecognized initiators and PRs
without a matching recent task go to `claude-cto`. Worker provider and branch
prefix do not establish ownership.

Unpushed work requires a local branch or worktree commit absent from every
freshly fetched origin branch. Pushed branches without an open PR get a
two-hour grace period measured from terminal dispatch completion. Git does
not retain the remote push timestamp. Branches already contained in origin's
`main` or tied to a merged PR by exact commit identity are excluded. This also
excludes squash merges. Rejected PRs require a trusted recorder comment for the
current head, no live matching task, and two hours since both the rejection
and the latest terminal repair task. New commits supersede older verdicts.
Explicit `terminal_abandon` records and `terminal-abandon.v1` ABANDON receipts
are excluded. This observer does not authorize abandonment or cleanup.

## Keeper entry point

The packaged keeper service calls this command after its queue pass:

```bash
.venv/bin/python -m scripts.orchestration.stalled_work stalled --tick
```

The same command can be called by an existing five-minute lane-wake tick.
Do not install a second timer. The entry point serializes concurrent calls
using its cadence checkpoint in shared `batch_state/stalled-work/cadence.json`.
It writes no task records. A failed scan or partial routing attempt leaves
the cycle retryable. Fleet deduplicates messages already accepted on retry.

| Environment value | Default | Effect |
| --- | --- | --- |
| `LU_STALLED_WORK_CADENCE_MINUTES` | `30` | Minimum scheduling bucket size in minutes |
| `LU_STALLED_WORK_ROUTE_ENABLED` | `0` | `1` enables routing from `--tick` |

Report-only is the default. Direct `--route` explicitly sends requests.
Routing emits one supervisory message per owning lane and a separate CTO
summary through `AuthorityService(root=None)`. Keys include cycle, lane and
the digest of the sorted row set, excluding changing age values. Retries in
one cycle deduplicate; the next cycle repeats unresolved work. No tmux input,
push, rebase, deletion or task-record write occurs. Missing Git or GitHub
evidence produces errors, exit 1 and no routing from that report.

After merge, the host configuration owner must deploy the updated keeper
service or add the entry point to its existing private lane-wake service,
then set `LU_STALLED_WORK_ROUTE_ENABLED=1` in that service's environment.
Host/private configuration and live enablement are outside this public change.
Verify a report first, then inspect the tick's Fleet message receipts.
