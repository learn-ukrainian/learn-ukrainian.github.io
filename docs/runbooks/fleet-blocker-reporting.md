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
   If the baseline is unknown, report every current blocker. If source coverage fails, stop the normal lane transition and escalate; do not post a partial replacement.
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

## Report complete finalization attention

The normal driver sequence includes every applicable `needs_finalize` run for
its full registered stream, including all member epics. Launcher aliases and
the issue-stream registry resolve `SESSION_EPIC`. `SESSION_HANDOFF_AGENT` must
be an exact registered slot for that stream. An unknown, ambiguous or mismatched
scope fails closed. Outside a driver session, select that same scope on both
commands:

```bash
.venv/bin/python -m scripts.driver_blockers delta --epic infra --current blockers.json --task-initiator codex-infra --task-stream-epic 6943
.venv/bin/python -m scripts.driver_blockers record --epic infra --current blockers.json --task-initiator codex-infra --task-stream-epic 6943 --receipt receipt.json --body-file posted.md --expect-generation 30
```

The explicit member epic selects the entire registered stream. It cannot narrow
the denominator or conflict with launcher identity. Neither explicit nor launcher
scope means non-driver use; it infers no task ownership. The compatibility
single-epic Python helpers retain their existing call shapes and behavior; the
normal CLI uses the stream collector and reconciles recording under its lock.

`complete: true` means exhaustive reporting coverage. It does not establish
historical ownership. A known lifecycle epic in the selected registered stream
is included regardless of initiator. Positive membership in another registered
stream excludes it. For unknown original streams, the full exact registered slot
can assign **current reporting custody only**. Original stream and initiator
unknowns remain literal unknowns. Unmatched slots, missing initiators and
unregistered original epics remain individually visible possible-owned attention.
Changing a provider seat does not change reporting custody row text.

One checked read of every hot JSON unit supplies the full stream. Every read,
parse and object check must succeed, even for noncandidates. Parsed units whose
status is not exactly `needs_finalize` are counted by status class. Unrecognized
status and purpose remain `UNKNOWN`; exclusion establishes no legitimate
provenance, health or successful outcome. Candidate task/run identity must be
safe and unambiguous. Identical same-run copies merge with diagnostic accounting;
contradictory copies refuse the entire command.

`LU_NEEDS_FINALIZE_MAX_AGE_MINUTES` defaults to 30 finite positive minutes. It
controls initial attention for fully attributed in-scope records only. Known
age equal to the threshold remains within the allowance. Missing or invalid age,
configuration or historical attribution requires attention. Age uses recorded
`finished_at`, never mtime. Exact ages and classification counts appear in
`finalization_attention` and `finalization_coverage`, outside row fingerprints.
Rows use stable pending-finalization wording and sanitized public causes.

Every recorded generated ID is retained while its exact run remains
`needs_finalize`, including after threshold increases or supported archive moves.
Before dropping one, the collector checks every exact-stem canonical, force-new,
PID and recursively stamped collision candidate in hot and archive. It reuses
hot bodies and reads only matching archive bodies. No newest or hot copy wins.
Every matching body must pass checked reads and embedded identity, nonce, status
and contradiction checks. A newer nonce, unknown status, statusless stub,
disappearance or changed inferred custody cannot resolve the prior run. Removal
requires positive exact-run recognized status other than `needs_finalize`, or
positive lifecycle membership in another registered stream. This is removal of
finalization attention, not evidence of task delivery. Ordinary caller blocker
absence still requires the exact standalone `RESOLVED <id>` post line.

Unsafe, missing, unreadable, unstable, malformed or contradictory required source
stops the whole lane and preserves ledger bytes, generation and anchor. Unknown
attention cannot stand in for unread source. The accountable Infra driver owns
and escalates unprovable exact-run evidence. Recovery requires authentic original
bytes restored by the operator through existing custody procedures to a supported
name in the same store. The existing `stale_task_records restore <exact-name.json>`
dry run and operator-executed `--apply` support valid archived records; they do
not recover missing backups, overwrite hot destinations or change status.
Both `.moving` and `.unplaced-*` residue remain unavailable to ordinary lookup.
A dated operator residual acceptance disposes only the escalation. It does not
remove attention, supply `RESOLVED` evidence or unstop the lane.

Before any real post, measure the actual combined observation, changed/resolved
body, prospective **indented** ledger and diagnostics bytes. The existing 1 MiB
bounds remain; task reads are bounded to 32 MiB. Overflow stops before posting.
Never clip, aggregate away members, split one recording, reset the ledger or
substitute another store. A successful post followed by a rejected record must
retain its original receipt and immutable bytes. Do not automatically repost.

After a normal accepted record, the next semantically identical delta returns
`UNCHANGED`, `post_required=false` and the same generation. This means unchanged
attention, including unknown attention, rather than zero blockers. The five-field
wire, three-field anchor, exact receipt/body SHA, selected recipient, stable lock,
CAS and atomic publisher remain unchanged. Tests establish mechanism behavior;
they do not certify real Infra and DevOps post/record/UNCHANGED acceptance criteria.
The accountable driver owns independent held-out proof on reviewed, merged and
deployed source for both complete lanes and parent closeout.

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
