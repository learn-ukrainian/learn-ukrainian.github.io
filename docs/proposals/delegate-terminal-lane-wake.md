# Delegate terminal settlement and initiating-seat wake

Status: PROPOSAL, NOT READY FOR ENABLEMENT. This document authorizes no runtime,
process, policy, security configuration, provider execution, or lease change.

## Outcome and review boundary

The intended outcome is a prompt re-entry in the exact native Codex seat that
initiated a delegate run, after that run settles. A background wait returning,
a terminal task record, a Fleet receipt, and a completed resume subprocess are
separate observations. None alone proves that outcome.

The smallest proposed change reuses terminal task records for recovery, Fleet
for durable notification, and the existing inbox wake process for delivery.
It adds no bus, watcher, service, keeper, supervisor, or provider route.
Activation remains disabled until the identity and suppression gaps below have
qualified solutions. Publication of this proposal is not designated approval.

This source inspection is pinned to
`356d44a1ac25046bb2a6e0a94783f3de83985987`.
The authoring contract was frozen before writing, at `2026-10-24T06:00:19Z`:

| Frozen input | SHA-256 |
| --- | --- |
| Dispatch brief | `daf3f293a91c56e3189234d578bad9650b35560e19b237f75029a6c2cbe8a38c` |
| Effective worker prompt | `5b1c5eda11848c69a791d34e55ca6cb016fb035d9cfb9972b35323792c11f845` |
| Normalized authoring contract | `fc7217886c2007101bc107764252ff1da68b431698454503ecaf58eb64787060` |
| Six-criterion ledger | `f2abafc96fabea65478c0673df9a34739a0e0f3114cf744eeed040a2c3178446` |
| Source manifest | `52d236ff47024ec961442a7d4307dedd4381546aeafab9a849471a3b2a7b4016` |

The hashes identify private task evidence without publishing its contents or
location. The proposal's final byte hash and pushed head belong in the review
receipt, avoiding a self-referential document hash.

The denominator is P01 through P06. This delivery is one design document.
Runtime activation, new tests, deployment, plans, rules, agent configuration,
lease actions, quota measurement, and provider probes are non-goals of this
authoring task. They are not removed from eventual runtime acceptance.

The requesting root owns judgment, routing, landing, and residual disposition.
The Sol author supplies the proposal, not its independent approval. Root routes
toolful Opus 5.5 critique and designated input on the exact document hash and
head, and verifies Sol 6.1 author provenance. If that provenance is unavailable,
both qualified advisor approvals are required. Disagreement goes to the operator.
An independent evaluator owns held-out runtime proof after authorization.
No such review, approval, or runtime proof is claimed here.

## Current source facts and complete delivery boundaries

The following are source facts at the pinned head. They are not observations
of an installed watcher, a current native session, or successful activation.

### Dispatch, settlement, and the effective terminal fact

1. [`cmd_dispatch`](../../scripts/delegate.py#L14194) chooses `run_nonce` from
   the argument, inherited runtime value, or generator, then resolves caller
   attribution. [`resolve_invocation_attribution`](../../scripts/agent_runtime/attribution.py#L47)
   accepts explicit attribution, forwarded attribution, or session environment.
   A Codex environment can resolve to bare `codex`; unknown remains `unknown`.
   Attribution identifies a caller label. It does not authenticate a native seat.
2. The [initial state](../../scripts/delegate.py#L16114) carries `task_id`,
   `run_nonce`, repository, `initiator`, `attribution_source`, worker agent,
   and execution metadata before the worker forks. The inspected fields do not
   bind that initiator to its native Codex thread and launcher lease generation.
   The worker's target `agent` is not the initiating seat.
3. [`_run_worker`](../../scripts/delegate.py#L11875) imports
   `agent_runtime.runner.invoke` as `runtime_invoke` and
   [calls it](../../scripts/delegate.py#L12331), then derives the effective
   outcome after finalization checks.
   Its [core terminal checkpoint](../../scripts/delegate.py#L13037) persists
   status, finish and result information before optional enrichment. A second
   [final write](../../scripts/delegate.py#L13266) adds optional metadata.
   Wake eligibility must use the complete core terminal fact, not wait for the
   later telemetry emitter or count enrichment as another settlement.
4. [`_write_state_atomic`](../../scripts/delegate.py#L919) holds the per-task
   lock and calls `_write_record_unlocked`, which sanitizes public reasons and
   calls [`write_state_unlocked`](../../scripts/orchestration/dead_worker_state.py#L166).
   That writer writes a temporary JSON file and replaces the task file.
   It has no Fleet publication call or explicit file/directory `fsync`.
   Atomic visibility is not proof of power-loss durability.
5. [`_emit_terminal_dispatch_event`](../../scripts/delegate.py#L11789) emits
   event type `dispatch` through [`emit_event`](../../scripts/telemetry/emit.py#L43)
   after the final write. This is best-effort, file-only telemetry. Its payload
   includes task and status, but omits the run nonce and initiating-slot binding.
   Its telemetry session ID can be minted locally. It is not a native initiating
   session identifier, a Fleet delivery, or a wake trigger.
6. [`cmd_wait`](../../scripts/delegate.py#L20237) reads live or archived state,
   checks an expected nonce, and may heal a proven dead worker. It prints terminal
   state and returns 0 only for `done`, 124 for task or wait timeout, and otherwise
   1. It calls no native initiating-seat activation path. Wait timeout can occur
   while the task remains active and must not create a terminal wake.
7. Terminal production is broader than the telemetry call. The
   [dead-worker markers](../../scripts/orchestration/dead_worker_state.py#L180),
   [provisioning refusal](../../scripts/delegate.py#L13422), and forwarding refusal
   also persist terminal records. A callback only at normal worker exit misses
   these paths. [`task_record_store`](../../scripts/orchestration/task_record_store.py#L1)
   distinguishes hot records, by-ID archive fallback, and historical enumeration.
   An empty active projection does not cover this denominator.

The [wait terminal set](../../scripts/delegate.py#L20215) is `done`, `failed`,
`timeout`, `rate_limited`, `crashed`, `cancelled`, `dry_run`, `needs_finalize`,
and `no_deliverable`. Each settled run is attention data. Only `done` reports
worker success; even that does not prove initiating-seat re-entry.

### Fleet delivery and native inbox wake are different paths

| Path | Current call graph and boundary |
| --- | --- |
| Durable Fleet message | [`AuthorityService.publish_message`](../../scripts/fleet_comms/authority.py#L541) admits recipients, starts a transaction, and calls `_publish_message_tx`. It commits an immutable body reference, metadata, recipient deliveries, an emitted wake receipt, and an idempotency entry together. Exact replay returns the existing message; changed payload with the same key fails. |
| Fleet receipt lifecycle | [`claim_next_delivery`](../../scripts/fleet_comms/authority.py#L1204) claims queued delivery with a fence and increments attempts. Expired claims requeue or dead-letter; deadlines expire. `acknowledge_delivery` calls `finish_delivery`, validates the current claim, and records a terminal receipt. These delivery claims are not stream lease claims. |
| Supervisory consumption | [`record_supervisory_consumption`](../../scripts/fleet_comms/authority.py#L1274) records generation-bound intent for `supervisory-request`. It requires that kind. It does not prove an external action finished. The existing supervisory request body accepts only wake or restart, not this proposed settlement notification. |
| Existing ordinary Codex wake | [`run_supervisory_wake_watcher`](../../scripts/ai_agent_bridge/_inbox_watch.py#L456) polls the ordinary bridge database through `poll_once`, reading unconsumed integer message IDs and seat aliases. With events, `wake_driver_once` checks the remote active Codex lease, discovers the exact owner process's open rollout, rechecks authority and readiness, then calls `_ui_codex.send`. It does not read ordinary Fleet authority deliveries here. |
| Existing native resume | [`find_live_session`](../../scripts/ai_agent_bridge/_ui_codex.py#L471) verifies the process's inherited lease envelope and requires one matching native thread. [`send`](../../scripts/ai_agent_bridge/_ui_codex.py#L558) starts `codex exec resume` for a UUID and returns parsed events and process outcome. This is a candidate mechanism already in source, not a selected or newly authorized activation route. |
| Post-resume observation | `RolloutReader.wake_result` observes lifecycle overlap and uncertainty. `wake_driver_once` requires `CLEAN`, exit 0, one start, and one completion before advancing its in-memory bridge cursor. OVERLAP and UNKNOWN retain watcher-owned receipts. Durable consumption still belongs to the live driver. |
| Offline supervisory wake | Without ordinary inbox events, the watcher uses the separate generation-fenced supervisory path and existing launcher. This proposal must never fall through to that path to wake a terminal notification's offline initiator. |

There is no complete source-backed edge from delegate settlement to Fleet
publication to an ordinary authority delivery to native initiating-seat re-entry.
The existing `emitted`, `received`, and `consumed` Fleet wake receipt states
describe delivery processing, not native activation.

Slot validation uses
[`handoff_slot_registry`](../../scripts/orchestration/handoff_slot_registry.py#L1)
and the bridge's roster/alias readers. A roster-valid provider alias is not
necessarily a unique native initiating seat. The proposal requires an exact
registered slot and an exact runtime binding, rather than routing bare `codex`
to whichever session looks active. No private session or transcript was read
to fill this gap.

### Busy state, human source, and known activation limits

[`RolloutReader.ready`](../../scripts/ai_agent_bridge/_ui_codex.py#L360) streams
complete lifecycle records. Starts mean BUSY; completions and aborts mean READY.
Missing, partial, malformed, or changing input refuses wake. Its pre-send state
uses the last lifecycle event. In particular, `start A, start B, end A` can be
reported READY despite B remaining open.

The [session-supervisor contract](../runbooks/session-supervisor.md#live-codex-inbox-readiness-10133)
explicitly documents the final-check-to-attach race and limits of `CLEAN`.
The overlap detector cannot close that race or prove visible TUI delivery.
The document names #10217 and owner `claude-monitor` for prevention; that is a
source locator, not a verified current issue status or proof of upstream support.

[`context_guard.human_activity`](../../scripts/ops/context_guard.py#L260)
defers on recent tmux client input and treats unreadable client telemetry as
possible human activity. This is an existing guard for its own actions, not an
authoritative Codex turn or human-origin classifier. In particular, no attached
tmux client does not establish that a native seat is safe for automation.

[`session_record.update_session`](../../scripts/lib/session_record.py#L295)
persists `session_source` for Claude session metadata, and
[`claudex_supervisor`](../../scripts/orchestration/claudex_supervisor.py#L369)
can carry that field. Those fields do not establish a Codex human-source
contract. The inspected Codex wake path checks neither a human-source field nor
the context guard's human activity observation. A Codex human-source authority
and an atomic human/busy suppression boundary remain UNKNOWN.

The [Codex hooks runbook](../runbooks/codex-hooks.md#L139) also distinguishes
inbox notices from consumption and reports limits on Desktop context delivery.
A hook notice, a latest transcript, a quiet pane, elapsed time, or PID existence
cannot substitute for native re-entry evidence.

## Proposed durable notification

Everything in this and subsequent sections is a proposal. Schema names and
outcome labels below are design vocabulary, not existing flags or endpoints.

### One identity and one Fleet delivery

Use the logical identity `(repository, task_id, run_nonce)`. Define key K as
`delegate-terminal-wake:v1:` followed by the SHA-256 of its canonical tuple.
The tuple and encoding must be specified in the implementation contract.
Neither a mutable status nor an observation timestamp enters K.

At dispatch, capture the initiating slot and the initiating native thread from
that caller's own trusted context, bound to the existing launcher stream,
session, lease generation, and fencing envelope. Store this binding on the
existing task record. Check roster membership and exact correspondence to
the caller. Explicit `--initiator` text alone grants no wake authority.
If any element cannot be authenticated, record `UNKNOWN_TARGET` and permit
no automatic activation. Do not search other seats' transcripts or use the
newest matching session. Do not infer a slot from the worker provider.

Publish a single immutable Fleet message to that exact existing registered
slot, with proposed kind `delegate-terminal-wake`. Its bounded typed body
contains K's tuple, the verified target binding reference, the stable terminal
core digest, terminal status, and a logical result reference. It contains no
instructions, shell text, routing override, credential, environment dump,
absolute host path, or transcript body. Resolve a result reference through
the existing task-record authority under the consumer's permissions.

Use `AuthorityService.publish_message` and its existing idempotency key.
Do not write a parallel bridge message, publish to the CTO channel, or use a
`supervisory-request` that can launch or restart a provider. The proposed kind
needs a reviewed parser and authority delivery selector in the existing wake
process. It does not inherit the supervisory consume API by name alone.

Propose a canonical terminal-core digest over repository, task, nonce, status,
`result_sha256`, `returncode`, `returncode_reason`, `needs_finalize`, and the
public `finalize_error` and `last_error` codes. Required fields and explicit
nulls must be defined for worker-exit, pre-execution refusal, and healed-crash
variants. `finished_at`, duration, memory measurements, absolute result paths,
and optional enrichment stay outside that digest. Publish only after the
producer's complete variant is persisted. Optional cost, cleanup, and telemetry
enrichment cannot change the published payload or generate another wake.
If the settled semantic core changes for the same nonce, retain
`TERMINAL_CONFLICT` for root reconciliation.
Do not conceal that conflict with a second key.

### Recovery without another queue

The existing task record is the replay source for a settlement, not another
message bus. Add bounded reconciliation to the already-owned inbox wake loop:

1. Enumerate task records for that exact target binding, including the documented
   archive and redispatch history. Verify embedded task and nonce identity,
   rather than trusting a filename. Nonterminal records produce no notification.
2. For each complete terminal core, construct the same payload and publish K.
   An immediate existing-worker publication may reduce delay, but correctness
   depends on reconciliation, including provisioning and dead-worker terminals.
   Omit that optional fast path from the first implementation if unnecessary.
3. After a crash before publication, a later pass republishes the same fact.
   After a crash following Fleet commit but before recording its ID, replay K
   and obtain the same message and delivery. A local publication marker is an
   optimization only. Fleet remains the notification authority.
4. Keep each pass bounded and schedule continuations through the existing loop.
   Require fair coverage across pages and recipients. A cursor must not skip a
   record that changes to terminal behind it; wrap and reconcile again.
   A restart must recover without trusting the previous in-memory cursor.

This design requires durable recoverability until Fleet publication. The
current JSON writer does not prove power-loss durability, and the inspected
archive interfaces do not prove retention until a notification commits.
Before implementation, the storage and reaper owners must prove the existing
retention/durability contract or obtain designated approval for the smallest
repair in the existing writer/archive path. No retention change is authorized
here. Without that proof, report `RECOVERY_SOURCE_UNKNOWN`; do not claim no-loss
delivery. Likewise, a nonexistent or stopped existing wake allocation yields
`CONSUMER_UNAVAILABLE`, not permission to install another process.

The rationale follows the dual-write failure analysis in the
[transactional outbox guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).
The file write and Fleet transaction are not one atomic transaction. Reconciliation
therefore requires a retained, durable source and idempotent publication.
[SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) describes
transaction durability, not atomicity with an unrelated JSON replacement.
These are engineering references, not authority to add a database or service.

The [Fleet ownership contract](../../agents_extensions/shared/rules/fleet-comms-coordination.md)
and [seat onboarding contract](../runbooks/agent-seat-onboarding.md#infra-atlas-and-supervisor-cold-start)
supply the binding authority and consumption boundaries. The
[agent-runtime ADR](../architecture/adr/adr-004-agent-runtime.md) and
[broker storage decision](../decisions/2026-05-06-broker-stays-on-sqlite.md)
are architectural context, not current route, health, or quota evidence.
The source-backed session-supervisor limits above control this proposal's
activation claims. A telemetry-only callback cannot recover the publish gap.
A shorter keeper interval cannot establish exact-seat re-entry or safe admission.

## Proposed delivery and suppression contract

The existing wake process owns bounded automation attempts, Fleet owns the
delivery, and the launcher continues to own the stream lease. The live seat
owns reading, applying, and acknowledging the message as itself.

Before claiming a delivery for execution, inspect its kind, exact recipient,
terminal identity, native thread, and current launcher envelope. Inspect the
authoritative busy and human-source/activity state for that same native seat.
Require an explicit automation-eligible source, no open turn, and no active
human interaction. Unknown is a hold. Do not import the context guard's PID,
pane-text, or time thresholds as substitute busy or source heuristics.

Defer BUSY and HUMAN_ACTIVE deliveries without repeatedly claiming them and
exhausting Fleet's delivery-attempt budget. Revisit the retained delivery at
the next existing readiness observation or scheduled tick. Select other
eligible deliveries fairly; a held row must not block ordinary inbox traffic.
The necessary kind-aware selection and consumption semantics are proposed
extensions of Fleet authority, not a claim that the current generic
`claim_next_delivery` already supplies them.

When the seat is ready, claim the exact eligible delivery under the existing
delivery fence and durably record intent before activation. The adapter must
revalidate the binding and atomically admit an automation turn only if that
same seat is still eligible. A check followed by `exec resume` is insufficient.
The wake payload cannot select a new session injection or security route.

No verified native operation with those admission properties was established
in this authoring task. `_ui_codex.send` is not approved as the answer to that
gap. Until a qualified owner supplies a supported operation and falsifiable
proof, delivery remains `ACTIVATION_UNSUPPORTED` with zero execution attempts.
This explicitly blocks enablement, while leaving the durable notification
design reviewable.

After admission, bind the native turn and semantic activation proof to K and
the Fleet delivery fence. A crash after intent or possible admission is
`ACTIVATION_UNKNOWN`, retained for reconciliation. Never automatically resume
again because a process timed out or its receipt was lost. Reconcile native
turn identity and live-seat consumption first. An admission boundary also
needs a stable operation identity or conclusive non-admission proof before
any retry. Fleet message idempotency alone cannot deduplicate a native turn.

Only the exact live seat may apply the terminal fact and acknowledge its
delivery with the semantic proof reference. Do not mark a delivery consumed
merely because an adapter observed `turn.completed`. The existing supervisory
consumption restriction needs an explicitly approved settlement-kind contract;
do not generalize that API silently.

Eventual delivery is conditional on the same target becoming ready, unchanged
valid authority, the existing consumer running, recoverable records, and a
supported atomic admission operation. Once those conditions hold, the proposed
bound for activating an eligible published delivery is two configured consumer
intervals plus the bounded native operation deadline. Terminal-to-activation also includes
one full fair reconciliation sweep. Freeze a maximum sweep duration against
the enumerated source denominator and batch size before evaluating that bound.
If backlog or unavailable sources prevent a bounded sweep, report delayed or
unknown delivery rather than claiming the bound. This is an acceptance target,
not measured latency.
Human-source sessions stay held until an attributed operator eligibility
decision. Inactivity alone never changes source classification.

## Failure and race matrix

These labels describe proposed wake dispositions. They do not replace delegate
task statuses or existing Fleet delivery states.

| Condition | Proposed disposition and durable action | Execution rule |
| --- | --- | --- |
| Task still running; only wait timed out | `NOT_TERMINAL`; retain task observation | No Fleet terminal wake. |
| Task `done` or another wait-terminal status | `TERMINAL_OBSERVED`; publish K with the actual status | Completion is attention, not permission to continue work. |
| Worker cancellation or task timeout | Wake carries `cancelled` or `timeout`; include typed reason reference | Notify only. Never restart worker or undo a STOP. |
| Operator cancels continuation or pauses stream | `CONTINUATION_CANCELLED`; preserve notification and disposition | No autonomous prompt execution until attributed release. |
| Producer crashes after terminal write, before publish | Reconcile retained fact and publish K | No second worker. |
| Publish response lost; duplicate terminal observer | Replay K; existing Fleet message returned | One message and one recipient delivery for the run. |
| Optional terminal enrichment changes | Same allowlisted core and payload | No second message. |
| Same nonce has different semantic terminal core | `TERMINAL_CONFLICT`; retain both evidence references | Stop automatic activation. |
| Old nonce arrives after task-ID reuse | `STALE_RUN`; verify exact historical run | No delivery to a different run or inferred successor. |
| Native turn open, or human interaction active | `DEFERRED_BUSY` or `DEFERRED_HUMAN`; retain queued delivery | No activation or attempt-budget churn. Revisit when eligible. |
| Human source, missing source authority, bad rollout, or unknown busy state | `HELD_HUMAN_SOURCE` or `READINESS_UNKNOWN`; retain and expose reason | No time-based escape or claim of readiness. |
| Slot removed, lease moved, rollover, or native binding differs | `STALE_TARGET`; retain for accountable-root reconciliation | Never retarget to current seat or launch a successor. |
| Human input or turn start races readiness check | Native admission must refuse atomically | If no such boundary exists, `ACTIVATION_UNSUPPORTED`. |
| Crash or timeout after activation intent | `ACTIVATION_UNKNOWN`; retain fenced intent and proof locators | No blind second activation. |
| Consumer restarts after Fleet claim | Existing claim expiry/fence rules apply; reconcile any intent first | New fence never licenses repeating an ambiguous side effect. |
| Deadline expiry or attempt exhaustion | Existing `expired` or `dead_lettered`; typed root-owned attention | No drop, auto-republication under another key, or retry storm. |
| Task record missing before publication; Fleet unavailable; no existing consumer | `RECOVERY_SOURCE_UNKNOWN`, `PUBLICATION_PENDING`, or `CONSUMER_UNAVAILABLE` | Preserve evidence. No alternate bus or new service. |
| Native receipt says CLEAN but lacks exact target response | `SEMANTIC_PROOF_MISSING` | No success or consumption claim. |

State changes, not every loop iteration, should produce diagnostics. Coalesce
pending notifications only for the same exact seat and authority envelope;
each K retains its own delivery and proof. Set a bounded batch size in the
reviewed implementation contract. A held or ambiguous K cannot be retried by
changing its key, and cannot prevent unrelated eligible notifications.

## Held-out proof of terminal-to-seat activation

No native or paid proof runs are authorized by this proposal-writing task.
The following is a proposed acceptance experiment, owned by an independent
evaluator after designated approval and separate execution authorization.

The evaluator freezes the reviewed implementation SHA, document hash, native
runtime identity, target binding, authority generation, test inputs, and
consumer interval/deadline before execution. Changed runtime, parser, prompt,
or adapter invalidates the proof. Use only a task-owned initiating session.
Do not borrow an unrelated active session or transcript.

The evaluator supplies a hidden challenge to an isolated delegate only after
the initiating seat has armed its wait and returned to a native ready state.
The delegate returns that challenge in its result and settles with a fresh
task and nonce. The initiating seat has no other source for the challenge.
The awakened seat must read the exact Fleet delivery and matching result,
answer the challenge in that same native seat, apply the terminal disposition,
and record its own durable consumption. The evaluator compares native turn
and target identity with the frozen binding using a supported observation
mechanism. The adapter's echo or a copied receipt is not independent evidence.
The original native conversation/control surface must receive the new turn;
a detached subprocess that shares a persisted thread UUID does not satisfy
this requirement by itself.
The availability of such native observation is itself an unresolved gate.

Every matrix row above must have held-out coverage. The evaluator chooses
unseen task IDs, nonces, challenge bytes, and crash/race schedules. Required
observations include:

- A terminal success and a terminal failure re-enter the intended native seat
  within the proposed bound, with one semantic consumption per K and zero
  activations in other seats.
- BUSY and HUMAN_ACTIVE suppress every attempt, including input racing the
  final check. Readiness later delivers the retained event once. A human-source
  session never activates without the required eligibility decision.
- Duplicate publication, checkpoint enrichment, consumer restart, and each
  crash boundary retain the event without duplicate native execution.
- Cancellation, wait timeout versus task timeout, stale nonce, rollover,
  unknown state, expiry, and exhausted attempts have the matrix dispositions.
- Fairness survives a held queue head and bounded multi-message batches.

Count success against all applicable matrix rows, with zero safety violations,
zero unexplained lost wakes, and zero duplicate native activations. Run no
repeated provider calls to turn an ambiguous result green. Stop on wrong-seat
delivery, human/busy overlap, unknown admission, missing native correlation,
unrecoverable source, or any requirement for an unapproved security or route
change. Preserve that failure as an owned residual. Transport-only receipt,
worker `done`, resumed-thread JSONL growth, and `CLEAN` are insufficient.

## Bounded implementation ownership and rollout proposal

This table identifies candidate paths for a future approved packet. It grants
no edit authority in this task. Avoid shared runtime changes unless inspection
proves an existing boundary cannot supply the required invariant.

| Owner role | Candidate existing paths | Bounded responsibility |
| --- | --- | --- |
| Delegate authoring lane | `scripts/delegate.py`, `scripts/agent_runtime/attribution.py` | Capture authenticated initiating binding and stable terminal core. Keep worker success independent of notification availability. |
| Storage/reaper owner | `scripts/orchestration/dead_worker_state.py`, `scripts/orchestration/task_record_store.py`, `scripts/orchestration/stale_task_records.py` | Prove durable replay and archive coverage. Propose any necessary repair for separate approval before touching retention or cleanup. |
| Fleet authority owner | `scripts/fleet_comms/authority.py`, `scripts/fleet_comms/contracts.py`, `scripts/fleet_comms/migrations.py` only if required | Define settlement-kind selection, fenced intent, semantic consumption, and typed holds using the existing authority store. No new database. Schema extension needs explicit design approval. |
| Inbox/native adapter owner | `scripts/ai_agent_bridge/_inbox_watch.py`, `scripts/ai_agent_bridge/_ui_codex.py` | Reconcile facts and consume Fleet deliveries in the existing process. Resolve atomic native admission, exact-seat proof, and human suppression before activation. |
| Documentation owner | This proposal and `docs/runbooks/session-supervisor.md` | Record approved behavior and remaining limits alongside implementation. No plan, rule, launcher, or agent configuration changes in this packet. |

No new test is authorized. After runtime scope approval, root obtains approval
for specific behavioral test additions if needed; existing relevant test
coverage and its gaps must be inspected then. The held-out protocol above is
a design contract, not a claim that tests exist or passed.

Proposed rollout sequence:

1. Obtain exact-hash Opus critique and designated agreement. Resolve the gates
   below and freeze the implementation packet with qualified review paths.
   Approval of this design must distinguish notification work from permission
   to invoke a native seat or change a gate during the current gate freeze.
2. Implement notification and recovery in the existing allocation, with native
   activation disabled. Migrate only newly bound runs first. Existing runs
   lacking an authenticated initiating binding stay `UNKNOWN_TARGET`; do not
   guess their identities or bulk-replay history.
3. Verify publication, crash recovery, privacy, and authority selection with
   deterministic checks. Then, only after explicit authorization, execute the
   held-out native experiment on one task-owned target through the approved
   existing adapter. Do not enable ordinary sessions from transport results.
4. Expand only when all applicable acceptance rows pass and root accepts the
   evidence on the exact reviewed head. No new service, watcher allocation,
   provider route, or lease action is part of expansion.

Rollback stops only the proposed activation and publication integration through
the approved existing deployment mechanism. Keep Fleet messages, intent,
consumption, and ambiguous outcomes for reconciliation. Restore the established
inbox behavior and existing waits without purging receipts, weakening fences,
releasing leases, or launching replacements. The exact disable mechanism needs
owner approval; this document invents no flag or live configuration key.

Public documentation and diagnostics contain repo-relative source locators,
opaque task/event references, status codes, hashes, and aggregate results.
Native UUIDs, lease envelopes, concrete runtime paths, raw events, and challenge
responses stay in access-controlled task evidence. Read only the bound caller's
own metadata. Do not export transcripts, process environments, personal input,
or credentials. A notification is untrusted data and grants no work authority.

## Acceptance ledger and unresolved decisions

`design_evidence` below means the document supplies the requested design.
`UNKNOWN` means runtime or authority proof remains outstanding. It is not a
waiver or a partially enabled implementation.

| ID | Design acceptance and evidence | Runtime disposition |
| --- | --- | --- |
| P01 | `design_evidence`: current producer, checkpoint, nonce/initiator, registry, Fleet lifecycle, wait, ordinary inbox, and native adapter call graphs above, with source links | `UNKNOWN`: no authenticated initiator-to-native-seat binding or measured installed terminal-to-seat path. |
| P02 | `design_evidence`: K, immutable core payload, Fleet transaction/idempotency, replay reconciliation, duplicate and crash matrix | `UNKNOWN`: durable JSON recovery and retention through publication need owner proof. |
| P03 | `design_evidence`: queued holds, fair eventual-ready delivery, distinct human-source and activity checks, fenced intent, typed failure matrix | `UNKNOWN`: atomic human/busy admission and Codex human-source authority are unproved. |
| P04 | `design_evidence`: independent hidden challenge, exact native target/turn/consumption evidence, full matrix denominator, falsifiable bound and stops | `NOT RUN`: native activation and held-out execution were prohibited in this task. |
| P05 | `design_evidence`: bounded candidate source ownership, reuse, migration, rollout, rollback, privacy, failure matrix, and six-row ledger | `DESIGN ONLY`: no source, process, test, rule, plan, or live configuration changes. |
| P06 | `design_evidence`: gates and reviewers below, root-owned judgment, exact-hash approval before runtime authoring | `PENDING DESIGNATED INPUT`: no approval inferred from proposal publication. |

Root retains these unresolved gates and routes them to the proposed existing
owner roles. Naming a role here does not create a stream, transfer custody, or
claim a lease.

| Gate | Required evidence or decision | Proposed owner/reviewer |
| --- | --- | --- |
| G1: Target identity | Authenticate caller slot, native thread, and launcher envelope; define stale target and rollover disposition without successor inference | Existing delegate and launcher owners; Opus 5.5 security/design critique. |
| G2: Safe native admission | Supported atomic idle-only automation turn with human-source/activity suppression and replay-safe operation identity; current `exec resume` path is insufficient proof | Existing native adapter owner; source-located #10217 owner `claude-monitor`; qualified Opus 5.5 and Sol 6.1 input. |
| G3: Durable recovery | Prove terminal core survives required crashes and remains available through archive/reap until Fleet commits; resolve any retention or writer repair explicitly | Existing storage and common-reaper owners; designated review of any contract change. |
| G4: Authority consumption | Approve settlement-kind selection, hold/fairness behavior, intent reconciliation, native semantic consumption, and deadline policy inside Fleet | Existing Fleet authority owner; independent toolful Opus 5.5 critique. |
| G5: Native held-out observability | Prove correct initiating native seat, turn correlation, human suppression, and semantic response independently; prove the existing consumer allocation is available | Independent evaluator selected by root; no provider run in this task. |
| G6: Approval and enablement | Exact proposal hash/head and attested authorship, designated agreement, implementation authorization, gate-freeze applicability, and separately authorized native evaluation | Root routes Opus 5.5 and Sol 6.1; operator resolves disagreement and security-config decisions. |

The current disposition is DESIGN PROPOSED with G1 through G6 unresolved.
Source inspection and the authoring ledger are the evidence delivered here.
There is no held-out activation proof, quota measurement, or enablement claim.
