# Record Fleet blocker reports

Send ordinary owned blocker reports to the existing `epics` Fleet authority.
Use `cto` only for explicit operator escalation. `scripts.driver_blockers`
compares and records reports. It does not send messages or establish routing authority.

## Compare, post, and record

1. Prepare a complete snapshot in `blockers.json`:

   ```json
   {"epic":"infra","complete":true,"items":[{"id":"blocked-build","state":"blocked","owner":"infra","waits_on":"review","action":"obtain review"}]}
   ```

   Every item requires exactly five non-empty strings: `id`, `state`, `owner`,
   `waits_on`, and `action`. Include every currently owned blocker.

2. Read the delta and its generation:

   ```bash
   .venv/bin/python -m scripts.driver_blockers delta --epic infra --current blockers.json
   ```

   Post every `NEW` or `CHANGED` item with all five fields on the same line.
   Post each `RESOLVED` item as exactly `RESOLVED <id>` on its own line.
   The token is case-sensitive. Do not add other fields or prose to that line.
   If the command fails or the baseline is unknown, report every current blocker.
   Partial observations cannot suppress reports or establish resolutions.

3. Send the report to `epics` through the existing Fleet workflow under your own
   identity. Preserve the genuine receipt as `receipt.json` and the exact posted
   UTF-8 bytes as `posted.md`.

4. After successful publication, record with the generation returned by delta:

   ```bash
   .venv/bin/python -m scripts.driver_blockers record --epic infra --current blockers.json --receipt receipt.json --body-file posted.md --expect-generation 30
   ```

   The default expected recipient is `epics`. To record an explicitly selected
   CTO escalation, append `--reporting-target cto`. You may also select
   `--reporting-target epics` explicitly. No other targets are accepted.
   Never derive the expected target from the receipt.

## Python API and validation

`record(path, epic, observation, receipt, body, expect_generation)` defaults to
`epics`. The keyword-only `reporting_target="cto"` selects CTO escalation.
The caller selects the expected target before receipt validation.

The receipt must contain a matching `recipient`, a non-empty `message_id`, the
exact body `content_sha256`, and an ISO-8601 `created_at` with a timezone.
An existing baseline requires a new message ID and a strictly later timestamp.
The expected generation must match under the recorder's lock.
Wrong recipients, altered body bytes, incomplete fields, invalid resolution
tokens, replay, stale generations, malformed inputs, and unsafe filesystem
entries are rejected without advancing the baseline.
CLI inputs are bounded to 1 MiB and are never clipped.

## Preserve the original baseline

The private sidecar remains `CTO-BLOCKERS-LEDGER.json` next to `DRIVER-STATE.md`.
Its lock, filename, and schema remain compatible. Existing valid CTO anchors
have no recipient field and remain readable. An epics receipt can advance that
same generation history without resetting or migrating the ledger.
Do not rename the sidecar or add recipient fields to historical anchors.

`show` and the shared `scripts.driver_state` consumer report
`Blocker baseline: generation N; M recorded blockers`. This wording does not
claim a historical recipient. The consumer also imports the same usage rule
that specifies ordinary epics reports and explicit CTO escalation.

Unit tests use isolated fixtures and never send live Fleet reports.
Publication and a recorded baseline do not prove live authority consumption.
The accountable driver owns exact-head cross-family review, landing, deployed
consumer verification, genuine epics apply and fenced ACK evidence, typed
acceptance evidence, and cleanup for [#10419](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10419).

## Report aged finalization work

Ordinary driver `delta` and `record` commands automatically include terminal
task attention. The launcher supplies `SESSION_HANDOFF_AGENT` as the exact
initiator and `SESSION_EPIC` as the stream selector. Existing launcher aliases
and the issue-stream registry bind that selector to its registered epics,
including nested programs. An unknown or mismatched driver stream fails visibly.

Outside a driver session, supply an explicit exact initiator and lifecycle epic
on both commands:

```bash
.venv/bin/python -m scripts.driver_blockers delta --epic infra --current blockers.json --task-initiator codex-infra --task-stream-epic 6943
.venv/bin/python -m scripts.driver_blockers record --epic infra --current blockers.json --task-initiator codex-infra --task-stream-epic 6943 --receipt receipt.json --body-file posted.md --expect-generation 30
```

Use the same scope on both commands. Without a launcher driver identity or an
explicit scope, the CLI does not infer ownership of another driver's tasks.
The scan reads the existing dispatch task
store and includes only matching initiator and lifecycle stream identities.
It does not adopt or repair tasks in another lane. Missing task storage fails
visibly. No command sends a message. Include all other owned blockers in the
original complete snapshot, then post and record the combined delta as above.

`LU_NEEDS_FINALIZE_MAX_AGE_MINUTES` defaults to **30 minutes**. It must be finite
and positive. A known age equal to the threshold is still within the allowance;
a greater age becomes a blocker. Age comes from the recorded `finished_at`,
never file modification time. Missing, invalid, timezone-free, or future terminal
timestamps produce attention. Invalid configuration also produces attention
instead of an unlimited wait.

Blocker IDs bind the task ID and run nonce. Each five-field blocker names its
owner, terminal timestamp, stable age lower bound, finalization reason, and
concrete publication recovery action. The `finalization_attention` output gives
the exact observed age and configuration state outside the snapshot fingerprint.
An unchanged task therefore stays `UNCHANGED` as time passes. Changed reasons
or attempts require another report. The exact body, receipt hash, completeness,
and generation-CAS checks remain unchanged.

The existing inbox checkpoint also checks aged `needs_finalize` tasks and posts
an action-required message to the `cto` Fleet Comms channel. This automatic
escalation is authorized for finalization attention; it does not change the
routing of ordinary blocker reports. No driver command, timer or daemon is
required. The checkpoint and driver report use `finalization_age` and the same
`DEFAULT_FINALIZE_AGE_MINUTES` setting. Unknown age or configuration is explicit.

The checkpoint retains per-task/run message IDs in the existing broker alert
state. A repeated scan does not post the same task/run again, including when
its age crosses another multiple of the threshold. A new run nonce identifies
a new attempt. Messages contain task identity, age, typed reason, owner and
recovery action; raw diagnostics stay private. Author tests use an isolated
broker and never post to the production `cto` channel.
