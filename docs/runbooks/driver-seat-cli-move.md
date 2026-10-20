# Move a driver seat to another CLI

Use this procedure for an already-authorized move of one driver stream. Keep
one accountable driver and preserve the existing shell and tmux session.
This guide does not authorize a move, a route change, or a lease takeover.

The launcher owns the stream lease lifecycle. The agent must never open,
claim, renew, release, or recover that lease. A delivery claim below leases a
message, not the stream. Source: [agents_extensions/shared/rules/core.md:157](../../agents_extensions/shared/rules/core.md#L157).
The ownership boundaries follow the existing
[cooperation best practice](../best-practices/agent-cooperation.md#cooperation-surfaces-ownership--do-not-conflate).

The six required elements, in their original order, are:

1. Durable handoff, native quit, and attributed fenced exit (steps 1–2).
2. Keep the existing shell pane for the successor launcher (step 4).
3. Verify both native dry runs and their quoted output (step 3).
4. Reconcile open orders and their exact authority recipients (step 5).
5. Use the quoted Grok model-table key as syntax only (step 6).
6. Stop on failed or unknown prerequisites (step 7).

This is the requirements checklist. Execute the steps below in numerical order:
both dry runs must pass before typing any real launcher command.

## 1. Save the predecessor's durable handoff

Drain the current driver's own authority deliveries. Record applied orders,
unfinished orders and their message IDs, in-flight workers and armed waits,
review and CI state, blockers, housekeeping, and the next action in the durable
lane handoff. Preserve the existing stream and order identities.

Use the current [thread-rollover skill](../../agents_extensions/shared/skills/thread-rollover/SKILL.md)
for handoff preparation and the required dual-write. Keep session handoff files
as continuity evidence. Fleet Comms owns durable messages and jobs; legacy
stores remain read-only. ACP carries ordinary communication, not durable
orders, lease authority, or formal review. Source:
[agents_extensions/shared/rules/core.md:158](../../agents_extensions/shared/rules/core.md#L158).

Preserve the current seat's health protocol. Grok, Gemini, and Kimi mint and
score their canaries only within `thread-rollover`; stop on FAIL-HANDOFF below
8/10. Claude and Sonnet use SessionStart/PostCompact and thread-handoff, with
no model-specific canary lane. Do not run a canary merely to validate this
guide. Source: [agents_extensions/shared/rules/core.md:126](../../agents_extensions/shared/rules/core.md#L126).

Stop if the handoff is missing, incomplete, or failed, or if the stream's
ownership or outstanding work cannot be reconciled. Do not quit a seat that
still owns unrecorded work.

## 2. Quit natively and wait for the predecessor's fenced exit

In the predecessor's TUI, enter `/quit`. Grok documents `/quit` as an alias
for `/exit` in its [native command reference](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/README.md#slash-commands).
Cursor lists `/quit` as Exit in its
[CLI reference](https://cursor.com/docs/cli/reference/slash-commands).
For another CLI, use that CLI's supported native quit command.

Wait for the predecessor's launcher to finish. It stops its watcher and renewal
and closes its exact exported fenced lease before returning the exit status.
A close failure changes an otherwise successful provider exit into a failure.
Source: [scripts/lib/launcher_core.sh:1351](../../scripts/lib/launcher_core.sh#L1351).

Require the predecessor's attributed `DRIVER_SCOPE_EXIT` with `rc=0`, plus
the existing shell prompt. The following is a synthetic shape, not a captured
exit from this documentation task:

```text
DRIVER_SCOPE_EXIT epic=<lane> rc=0 signal=none ts=<UTC-timestamp>
```

The scope waiter emits the lane, status, signal, and timestamp after waiting
for its child. Source: [scripts/lib/driver_scope.sh:329](../../scripts/lib/driver_scope.sh#L329).
Attribute the marker to the predecessor's launcher and exact fenced lease
using its existing local receipts. The text alone contains no lease ID,
generation, or fencing token. An old marker or another seat's marker is not
proof of release.

Stop on a missing or unattributed marker, nonzero status, `DRIVER_SCOPE_REFUSED`,
`close_failure_reason=`, unknown authority, or an occupied lease. Do not kill
a process or session, use `--force`, run a lease-close command, or recover a
remote lease from local PID observations. The launcher owns release; unresolved
release or expiry needs the existing authorized supervisor flow. Follow the
[current lease boundary](../../agents_extensions/shared/rules/core.md#unconditional-invariants)
and the corrected [Grok canary protocol](grok-session-canary.md#lifecycle).

## 3. Verify both native dry runs before a real launch

From the repository checkout in an existing shell pane, run both commands.
Do not replace the shell with a launcher and do not invoke a real launcher yet.
These examples check two routes; they do not authorize moving between streams.

```bash
LAUNCHER_DRY_RUN=1 ./start-grok-driver.sh --epic infra
LAUNCHER_DRY_RUN=1 ./start-cursor-driver.sh --epic devops
```

Require exit status 0 from each command. Verify its selected stream, native
harness, registered slot, and would-execute arguments against the intended
route. Rerun the intended route's dry run if the lane or arguments differ.
Stop if either dry run fails or selects the wrong route. Inspect current source
before using dry-run after a launcher change.

The following public-safe lines are verbatim excerpts captured on 2026-10-19.
Full output stays in private task evidence because arguments can contain local
paths and session details. These are observations, not permanent stream pins.

Grok, `--epic infra`, exit status 0:

```text
launcher: would claim lease stream=epic:6943 agent=grok harness=grok-tui
launcher: session epic=infra slot=grok-infra handoff=.claude/infra-epic/CLAUDE-DRIVER-HANDOFF.md
launcher: would bind drive-epic after lease; provider canary: not run
```

Cursor, `--epic devops`, exit status 0:

```text
launcher: would claim lease stream=epic:5703 agent=cursor harness=cursor-agent
launcher: session epic=devops slot=cursor-devops handoff=.claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md
launcher: would bind drive-epic after lease; provider canary: not run
```

The shared dry-run path skips scope entry, deployment, and rollover import.
Its lease branch prints and returns before calling the supervisor. Sources:
[scripts/lib/launcher_core.sh:1581](../../scripts/lib/launcher_core.sh#L1581),
[scripts/lib/launcher_core.sh:965](../../scripts/lib/launcher_core.sh#L965).
The native adapters print arguments and return before provider execution:
[scripts/launchers/grok.sh:44](../../scripts/launchers/grok.sh#L44),
[scripts/launchers/cursor.sh:47](../../scripts/launchers/cursor.sh#L47).

A successful dry run proves local argument construction, not authentication,
provider health, quota, model runtime compatibility, or a lease claim. Unknown
health remains unknown and current routing gates still apply. The Grok adapter's
"would run provider canary" line is a dry-run message. Cursor has no launcher
semantic canary. Source: [scripts/launchers/cursor.sh:19](../../scripts/launchers/cursor.sh#L19).
These commands cover native Grok and Cursor only. Do not generalize this safety
proof to Hermes or probe Hermes as part of this procedure.

## 4. Type the real launcher into the existing shell pane

Only after the durable handoff, attributed fenced exit, and both successful dry
runs, type the already-authorized launcher command at the existing shell prompt.
Use the exact lane and arguments that passed the intended route's dry run.
For the two checked examples, choose only the authorized stream's command:

```bash
./start-grok-driver.sh --epic infra
# Or, for the separate DevOps stream:
./start-cursor-driver.sh --epic devops
```

Run the command as a foreground shell command. Never use `exec`,
`tmux respawn-pane`, or a launcher as the pane's initial command. Keep the
shell as the pane process so it remains when the launcher exits. The driver
waiter preserves the terminal, stdin, and process group and returns its child's
status. Source: [scripts/lib/driver_scope.sh:283](../../scripts/lib/driver_scope.sh#L283).

Let the launcher acquire the successor's lease and supply its own session
identity. Do not copy the predecessor's `SESSION_STREAM_*` envelope or use
another session's transcript. Stop on launch, hydration, fencing, or health
failure. Do not start a second supervisor or retry an ambiguous launch.

## 5. Restore open orders to the new authority inbox slot

On successor startup, read the durable lane handoff before acting. Confirm the
launcher-provided slot against the registered slots and selector mapping.
The current examples map to `grok-infra` and `cursor-devops`; arbitrary
`grok-<lane>` or `cursor-<lane>` strings are not registration. Sources:
[scripts/lib/handoff_identity.sh:493](../../scripts/lib/handoff_identity.sh#L493),
[scripts/lib/handoff_identity.sh:503](../../scripts/lib/handoff_identity.sh#L503),
[scripts/config/area_assignments.yaml:21](../../scripts/config/area_assignments.yaml#L21),
[scripts/config/area_assignments.yaml:37](../../scripts/config/area_assignments.yaml#L37).
Publication admits explicit recipients through `_admit_recipients`; it normalizes
whitespace and applies bridge admission. It does not certify an arbitrary name
as a registered driver slot. Verify registration separately as above. Sources:
[scripts/fleet_comms/authority.py:135](../../scripts/fleet_comms/authority.py#L135),
[scripts/fleet_comms/authority.py:563](../../scripts/fleet_comms/authority.py#L563).

Have the authorized sender reconcile unfinished orders against their durable
outcomes before any re-publication. Preserve each original kind, body, reference,
correlation ID, reply reference, and remaining acceptance criteria in the handoff
and delivery record. Do not repeat completed side effects or rewrite an order as
a new kind. Use a fresh idempotency key for each new delivery; reuse that key
only for the identical publication. This task publishes no orders.

For an ordinary message, this authorized-sender template uses `cto`, a channel
named by the existing supervisor publication path. Verify that the channel already exists;
do not create a channel to make this example work. Source:
[scripts/lib/session_supervisor.sh:332](../../scripts/lib/session_supervisor.sh#L332).
Replace every placeholder and use the project interpreter prescribed for the
seat. In a dispatch worktree, use the primary interpreter, not a worktree `.venv`.

```bash
"$PROJECT_PYTHON" -m scripts.fleet_comms channel publish cto - \
  --sender "<authorized-sender>" --recipient "<new-registered-slot>" \
  --kind "<original-non-supervisory-kind>" \
  --conversation-id "<original-conversation-id>" \
  --correlation-id "<original-correlation-id>" \
  --in-reply-to "<original-reply-message-id>" \
  --deadline-at "<original-deadline-at>" \
  --idempotency-key "<fresh-delivery-key>" \
  < "<private-order-body-file>"
```

Omit an optional reference or deadline flag only if that field was absent originally.
Use the unchanged original body from the private body file. Preserve the original
order reference and remaining criteria in durable continuity records even when
the body only refers to them. Record the original message ID alongside the new
message and delivery IDs. An `--in-reply-to` parent must exist in the same
authority store; stop on a missing parent instead of dropping the reference.
Source: [scripts/fleet_comms/authority.py:1887](../../scripts/fleet_comms/authority.py#L1887).

`channel publish` passes the explicit recipient, original kind, conversation,
correlation, reply reference, and idempotency key to
`AuthorityService.publish_message`, which creates the message and deliveries
in one transaction. Sources: [scripts/fleet_comms/cli.py:983](../../scripts/fleet_comms/cli.py#L983),
[scripts/fleet_comms/authority.py:541](../../scripts/fleet_comms/authority.py#L541).

For `supervisory-request`, retain the canonical supervisory path instead of
using the ordinary-message template. The existing
[supervisory integration](session-supervisor.md#supervisory-event-integration)
uses `AuthorityService.enqueue_supervisory_request(sender=..., recipient=...,
body=..., correlation_id=..., idempotency_key=..., deadline_at=...)`. Preserve the
original body, correlation ID, and optional deadline and use a fresh delivery key. Its recipient remains
`supervisor:epic:<number>`, not the new driver inbox slot. Source:
[scripts/fleet_comms/authority.py:582](../../scripts/fleet_comms/authority.py#L582).
The supervisor accepts only the existing bounded `supervisory-wake.v1` wake/restart contract;
do not convert arbitrary driver orders to wake/restart events. Reconcile the
body's predecessor generation with the existing supervisor lifecycle. A stale
event does not authorize a new restart or a changed body. The helper has no
`in_reply_to` parameter; if an original request has an unsupported reference,
stop and retain it for the sender rather than dropping that reference.

The successor claims ordinary messages only from its own new slot with its own
worker identity:

```bash
"$PROJECT_PYTHON" -m scripts.fleet_comms deliveries claim \
  --recipient "<new-registered-slot>" --worker-id "<successor-worker-id>"
```

Read the original body through the existing authority reader,
`AuthorityService.read_message_body(message_id)`. Source:
[scripts/fleet_comms/authority.py:645](../../scripts/fleet_comms/authority.py#L645). Claim output contains metadata and body artifact references, not the
order body. Reconcile prior effects and remaining criteria, apply only the
remaining authorized work, record its verified outcome, and acknowledge the
exact claimed delivery with that worker identity and its returned fence token:

```bash
"$PROJECT_PYTHON" -m scripts.fleet_comms deliveries ack "<delivery-id>" \
  --worker-id "<successor-worker-id>" --fence-token "<returned-fence-token>"
```

For a `supervisory-request` only, the existing supervisor claims its canonical
recipient and reads the original body. It records generation-bound consumption
before any authorized effect, reconciles the outcome, then acknowledges with
the same worker identity and current delivery fence. Its supported consumption
command shape is shown below for reference. The launcher/watcher owns this
sequence; do not execute supervisory consumption from the agent seat.

```bash
"$PROJECT_PYTHON" -m scripts.fleet_comms deliveries consume "<supervisor-delivery-id>" \
  --worker-id "<supervisor-worker-id>" --fence-token "<current-delivery-fence>" \
  --driver-generation "<launcher-driver-generation>"
```

The ordinary-message ack example above is not a substitute for this supervisory
sequence. Do not use `consume` for ordinary messages; it refuses them.
The CLI exposes claim, consume, and ack with explicit identities and fences.
Sources: [scripts/fleet_comms/cli.py:854](../../scripts/fleet_comms/cli.py#L854),
[scripts/fleet_comms/authority.py:1372](../../scripts/fleet_comms/authority.py#L1372).
Recipient mismatch, worker mismatch, stale fences, and missing supervisory
consumption have existing counterexamples in
[tests/fleet_comms/test_delivery_cli.py:77](../../tests/fleet_comms/test_delivery_cli.py#L77).

Never claim or acknowledge the old slot's deliveries as the new identity.
Legacy bridge `send`, `inbox`, and `ack --consumed-by-live-driver` are not the
authority delivery path. An empty legacy inbox proves nothing about new-slot
orders. Stop if the slot, plane, body artifact, current fence, or order outcome
is unknown. Keep unresolved orders durable with their owner and next action;
a new prompt or successful launch alone does not prove continuity.

## 6. Check the Grok model-table syntax

For Grok, recognize the quoted model-table key as TOML syntax:

```toml
[model."grok-4.7"]
```

The [official Grok model configuration reference](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/README.md#model-configuration)
defines the `model.<name>` table. The [TOML key specification](https://toml.io/en/v1.0.0#keys)
requires quotes to keep a dot inside one key. Thus `model."grok-4.7"` has one
model key, while bare `model.grok-4.7` creates nested `grok-4` and `7` keys.
This is syntax evidence only; runtime acceptance by the installed Grok CLI is
unverified. Do not edit live configuration or authentication to follow this
guide. Stop if the intended route needs an unapproved configuration change or
unproven runtime behavior. Grok preserves its last model selection unless the
caller supplies a model or effort; verify the intended model against current
routing before proceeding. Source: [scripts/launchers/grok.sh:31](../../scripts/launchers/grok.sh#L31).

## 7. Stop conditions

Stop before a real launch if the handoff or health protocol failed, the
predecessor's fenced exit is missing or unattributed, either dry run failed,
the intended route differs, or authority, lease expiry, or health is unknown.
Keep the shell pane and durable continuity evidence intact. The launcher owns
fenced lease close; an agent never claims, renews, releases, or recovers it.

Stop on an unregistered successor slot, missing body or reference, stale delivery
fence, unknown prior effect, or unsupported supervisory body or generation.
Keep each unresolved order's original identity, remaining criteria, owner, and
next action in the handoff. Never replace missing proof with a new prompt,
plain acknowledgment, forced lease operation, or a second supervisor.
