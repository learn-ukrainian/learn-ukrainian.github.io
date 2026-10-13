# Author-owned PR lifecycle, slice 1

Slice 1 records branch ownership before the first writer starts and evaluates
Harness `CHANGES_REQUESTED` events in shadow mode. It never starts a repair
worker, records a verdict, enqueues a PR, adopts an orphan or resumes a session.
The driver retains review judgment, landing and terminal disposition.

## Ownership

`delegate.py` calls `author_binding.bind_dispatch` after existing admission and
the advisory recheck, before publishing the initial task record and spawning.
It observes write tasks on an identified repository branch. Read-only tasks,
reviews and dry runs do not bind authors. Dispatches without a resolved GitHub
repository remain unclassified under the existing admission contract.

The shared store is `batch_state/author-lifecycle/v1/bindings/<digest>.json`.
The digest covers repository and branch, so repositories cannot collide.
Schema version 1 stores `repository`, `branch`, `driver`, `lane`, `issue`,
`pr`, `authors`, `author_task_ids`, `author_families` and `round_count`.
The first writer has round count zero. Each distinct later author task appends
one entry, adds its family, and increments the round count. Repeated task IDs
are idempotent; changed family attribution is refused. Unknown families remain
explicit and prevent repair proposals. Missing records mean unbound branches;
corrupt records cause failure and are never replaced with new ownership.

The lane classification comes from the dispatch's explicit research track;
unknown classification can be resolved during shadow reconciliation using the
fresh canonical issue membership cache. The issue comes from the admitted DoR
card when it identifies exactly one task issue. Ambiguous issue cards remain
unknown and cannot supply a repair packet. Foreign issue-card numbers also
remain unknown; the dispatcher does not reinterpret them in the code repository.
The dispatcher never chooses an
issue from event free text, a branch prefix or a roster.

`BindingStore.load(repository, branch)` is the read interface for keeper and
reaper consumers. `BindingStore.attach_pr(repository, branch, number)` allows
the dispatcher or a later PR-open integration to attach a PR once. Repeating
the same PR is idempotent; changing it fails. This slice does not change the
keeper, reaper or PR publisher. The dispatcher attaches the number only after
live GitHub reconciliation.

Each branch uses its own `flock`, including read/modify/replace and PR
attachment. Writes fsync the temporary file, atomically rename it and fsync
the containing directory. Ownership survives task-record archival; task lookups
use the existing hot/archive reader.

## Evaluate an event

Use the task-prescribed project interpreter from a dispatch worktree:

```bash
<project-interpreter> -m scripts.orchestration.author_repair_dispatcher event event.json
<project-interpreter> -m scripts.orchestration.author_repair_dispatcher report
```

The input is an object of at most 32 KiB:

```json
{
  "repository": "owner/repository",
  "branch": "codex/repair-topic",
  "head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "review_task_id": "review-topic-r1",
  "verdict": "CHANGES_REQUESTED",
  "occurred_at": 1791849600.0
}
```

`occurred_at` is a finite Unix timestamp from the event producer. Future or
negative timestamps are rejected. Extra free-text fields do not supply prompts,
routing, permissions or file paths. Events are evidence, never instructions.

`LocalSources` rereads the completed, branch-pinned, read-only review task and
its result through the recorder's hot/archive reader. Task identity, repository,
branch, reviewed head and verdict must match the event. A reviewer from any
bound author family is refused. Structured `code-review-findings.v1` results
provide finding bodies and unresolved dispositions. Legacy verdict-only results
can be reconciled, but cannot produce a packet without structured findings.
They are deferred rather than summarized from transcripts.

This is the current shadow reconciliation source, not an authenticated
recorder ledger. The prerequisite protection must replace or strengthen that
source before a live implementation is admitted. A comment alone never supplies
the canonical review result in this slice.

The dispatcher reads live GitHub PR state and current head. Before a PR exists,
it uses a read-only `git ls-remote` query against the branch's GitHub repository.
It also reads the fresh, complete issue-to-stream membership cache. Only `infra-harness` is
eligible. Missing or ambiguous membership, evidence, scope or Git objects
defers the event. A moved head or closed branch drops it. The local source
requires an active canonical task record for the bound driver and explicit
`operator_paused: false`; an unavailable owner produces an orphan alert and an
unknown pause defers. It does not infer ownership from a PID or acquire a lease.
Active or unknown branch writers, including `needs_finalize`, defer repairs.

The bounded packet includes issue acceptance criteria, reviewed/current head,
diff stat, unresolved finding dispositions, failed check IDs/conclusions and
head evidence, prior shadow round outcomes, author-family exclusions and the
latest author's declared write scope. Its limit is 32 KiB; oversized evidence
is deferred intact. Raw transcripts and event free text are excluded. Canonical
review and branch state are reread before recording the proposal.

## Limits and shadow gate

The idempotency key is `<reviewed-head>:<review-task-id>`, scoped by repository
and branch. The atomic `events.json` snapshot contains observations, complete
would-be dispatches and embedded packets, packet digests and budget reservations.
A replay logs a duplicate observation, never another proposal. Deferred events
can be retried after the blocking writer exits. A store lock serializes shadow
decisions; it does not replace delegate's admission or live writer locks.

At most two shadow repair rounds are reserved per bound branch repair episode,
including new review task IDs and process restarts. The third eligible event
produces an escalation addressed to the original driver with prior event keys
and proposed task IDs. There is no automatic budget reset or orphan adoption in
this slice. Each proposed task has `--hard-timeout 7200`, a fresh task identity,
`--branch`, `--worktree`, `--mode danger`, a bounded prompt-file reference and
the canonical author's `--owned-path` declarations. Routing is Sol at high
through Codex, as ordered for this security-relevant dispatcher. No proposal
contains review, verdict-recording, enqueue or `--allow-merge` capabilities.

`config.json` in the same private runtime store has two boolean keys:

```json
{"phase_971_1_merged": false, "phase_971_1_deployed": false}
```

Both default to false. The accountable Harness driver may set them to true
only after verifying the phase 1 merged SHA and its deployed recorder-ledger
protection. These keys document the prerequisite and are read into each shadow
entry as `gate_ready`. They grant no authority by themselves. `--live` records
intent only, and `live_enabled` remains false even with both keys true. A later,
separately approved slice must supply authenticated records, live dispatch,
pause/ownership authority and writer reservation. This implementation has no
worker-launch call. The proposed packet path is descriptive; this slice embeds
the packet in the ledger and does not materialize a prompt file or Fleet job.

## Metrics and interpretation

`report` reads the committed snapshot without creating files or locks. Its
denominator is every distinct eligible observed key, including deferred,
dropped, orphaned and escalated events. Duplicate deliveries are observations,
not additional eligible events. Ignored events are counted separately. A review
that fails canonical reconciliation is counted as dropped, not as a missed
eligible event. Unknown ownership produces an alert with `owner_state_unknown`,
not a claim that no owner exists.

| Field | Source and interpretation |
| --- | --- |
| `event_to_repair_start_seconds` | Proposal timestamp after reconciliation minus producer event time. Shadow latency only; no actual repair started. |
| `event_to_reviewed_repair_head_seconds` | `null` in slice 1. Later join actual repair start, pushed head and exact-head independent review receipts. |
| `duplicates` | Replay observations after a committed proposal. |
| `missed_events` | Distinct eligible observed keys without a proposal, including deferred/escalated/dropped/orphaned keys. |
| `unseen_events` | `null`. Detecting events never delivered requires an independent canonical event census. |
| `driver_interventions` | Escalation observations requesting driver intervention, not proof the driver acted. |
| `billed_usage` | `null`. Later read the repair task's settled provider billing telemetry; unknown never means zero. |
| `shadow_dispatches` | Committed would-be dispatches, never real launches. |

Operators should evaluate alerts every keeper cycle. This slice supplies the
single-event command, not a new timer or event transport. No shadow metric
demonstrates reduced idle time, successful repairs, review approval or delivery.
