# Context-cost baseline

This command measures stored input bytes and provider-reported token categories
from a frozen local sample for #10421. It changes no lifecycle policy.
Synthetic tests prove arithmetic and privacy behavior. They do not prove anything
about real sessions. The private baseline supplies the host measurement.

## Run locally

Use the project interpreter from the dispatch contract. Linked worktrees use the
shared absolute interpreter; do not create a worktree virtual environment.
Set a restrictive output mask before redirecting the baseline JSON.

```bash
umask 077
.venv/bin/python scripts/ops/context_cost_report.py freeze \
  --manifest batch_state/monitor-blocker-dedupe/sample-manifest.json
.venv/bin/python scripts/ops/context_cost_report.py report \
  --manifest batch_state/monitor-blocker-dedupe/sample-manifest.json \
  --tool-sha "$(git rev-parse HEAD)" \
  > batch_state/monitor-blocker-dedupe/sample-baseline.json
.venv/bin/python scripts/ops/context_cost_report.py report \
  --manifest batch_state/monitor-blocker-dedupe/sample-manifest.json --text
```

Run `freeze` before any metrics. Record its `manifest_sha256`. A report never
rescans the roots. Re-running `report` against this manifest preserves the sample
and skips changed sessions. A new `freeze` creates a different sample.
Commit and push the tool before capturing the final baseline so `tool_sha` binds
to the pushed SHA. Pass the verified 40-hex SHA using `--tool-sha`; the
parser launches no subprocess and defaults to `unknown` when this metadata is
absent. The invoking driver verifies it against Git and the remote. Keep
manifests, baseline JSON and host totals local and ignored.
Never include them in a public issue or PR body. The manifest contains private
paths; the baseline contains only digests and aggregates.

## Frozen definitions

- Denominator: Codex `~/.codex/sessions/**/rollout-*.jsonl` and Claude `~/.claude/projects/**/*.jsonl` whose mtime is in `[run_start_utc − 7 days, run_start_utc)`, excluding paths that contain `subagents/` or a filename matching `agent-*.jsonl`, with at least 20 PAIRED tool calls (a tool call is paired when a call record and its result record join by the rule below). Grok, AGY, Gemini, Kimi and Cursor are reported `unavailable` with reason `no_documented_root`. Do not walk the home directory.
- Freeze: before any metric, write a mode-0600 manifest (under `batch_state/monitor-blocker-dedupe/`, never committed) that stores the full session path, harness, size, mtime, paired-tool-call count, and a 16-hex SHA-256 digest of the path; print the SHA-256 of the manifest file. `report` opens only paths listed in the manifest. If size or mtime differs from the manifest, skip that session as `stale_session`; never rescan. Stdout, the baseline JSON, error strings, tests and the runbook emit the 16-hex digest only, never the path or the raw session id.
- Join rule: Claude `tool_use.id` pairs with `tool_result.tool_use_id`; Codex `call_id` on `custom_tool_call` (and `function_call`, handled as a sibling) pairs with the matching output record. An unpaired result counts toward class 4 bytes with shape `other` and toward no other class.
- Hash and size basis: SHA-256 of the UTF-8 result body (canonical JSON with sorted keys when the body is an object); size is that body's byte length.
- Identity series (kept separate, never merged): (a) normalized path (collapse `.` and `..`, strip one trailing slash, do NOT resolve symlinks); (b) URL as scheme+host+path with query and fragment removed, then hashed; (c) allowlisted command shape (below). An identical path read through two different command shapes stays two series.
- Metric classes (per session, aggregated per harness, and per model where the model is recoverable from the transcript). Waste classes report BYTES only; classes are disjoint:
  1. `cold_start`: UTF-8 bytes of records whose type is on an explicit pre-action list (document the list in the module docstring), occurring before the first Claude `tool_use` or Codex `custom_tool_call`/`function_call`. If the system prompt is not a distinct stored field, the class is `unknown`. The first call's provider usage goes only into class 7 as `first_call_uncached_input`, `first_call_cache_creation`, `first_call_cache_read`. File reads belong to classes 3 and 6, never here.
  2. `per_call_reinjection`: `(occurrences − 1) × hashed size` of `hook_additional_context` payloads whose hash recurs on later model calls in the same session. These bytes are excluded from class 8.
  3. `repeated_reads`: for the same normalized path, or the same URL hash, read more than once with the same content hash: `(n − 1) × size`. A changed content hash is `changed_reread` and is excluded from waste (reported separately).
  4. `raw_tool_payload`: paired or unpaired tool results above 20,000 bytes: count, total bytes, share of all tool-result bytes, and the top five allowlisted command shapes by bytes.
  5. `unchanged_polls`: the same allowlisted command shape and normalized argument-free key repeated with an identical output hash, NON-READ commands only: `(n − 1) × output size`. (Reads are class 3; the same call is never counted twice.)
  6. `post_compaction_rehydration`: bytes of paired reads in the next 20 TOOL calls after a compaction marker that reuse a normalized path seen before that marker. Marker: Codex `type == compacted`, or a Claude `type`/`subtype` pair you name in the docstring BEFORE coding the metrics. With no such field the class is `unknown`. Never infer resume from a time gap.
  7. `totals`: wall time is the delta of event `timestamp` fields when both ends exist, otherwise `unknown`; paired-call count; model-call count; provider tokens, each category summed within itself and never across categories. Claude: each assistant `usage` is one request; sum `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens` separately. Codex: sum `last_token_usage` when present, otherwise delta `total_token_usage`, and on a negative delta (counter reset after `compacted`) add the new total as that event's increment. Copy a Codex key into a Claude category only when the key string is identical; otherwise that category is `unknown`. A bytes÷4 estimate may appear only in a separate field named `estimate`. Request-level cache counters are NOT assigned to any waste class (a repeated hook payload inside a stable cached prefix is far cheaper than the same payload in the uncached tail; this packet measures bytes, not cost).
  8. `reminder_attachments`: for the exact Claude attachment types `total_tokens_reminder`, `deferred_tools_record`, `silent_turn_reminder` and `queued_command`, waste is `(n − 1) × UTF-8 size` even when the text differs. Exclude `hook_success` and `hook_additional_context`. Codex is `unknown` until a named recurring type is written into the docstring. Any other type increments `other`.
- Every class value is a number or `unknown` plus a reason from a fixed enum (for example `field_absent`, `no_marker`, `unpaired`, `stale_session`, `no_documented_root`).
- Non-goals: no threshold or policy proposals; no edits to hooks, launchers, keeper, `current.md`, skills or rules; no session restarts; no worktree scanning or cleanup; no transcript text, commands, file contents or paths in any output, fixture or commit; no new message bus or service; no weakening of any gate.
- Independent held-out check (a later driver gate, not part of your completion): a different-family worker recomputes classes 2–5 and class 7 from these frozen sentences for six manifest digests chosen by a seed you never see, and compares wasted bytes and each class 7 category with `abs(a−b)/max(a,b)` (both zero is agreement; one `unknown` and one number is failure). Above 2% fails the packet; the implementation is then fixed to match THIS prompt, never the tolerance. You document exactly these rules in the module docstring and runbook and do not narrow them. Synthetic tests are necessary and are not evidence about real sessions.
- Stop terms: stop and report BLOCKED / ERROR / STILL WORKS / ASK if a transcript format cannot yield a class without guessing (report that class `unknown` for that harness). Two failed gate pushes with the same root cause: stop and report.

## Shapes and normalization

The exact output shape labels are `git-status`, `git-diff`, `git-log`,
`gh-pr-view`, `gh-pr-diff`, `file-read`, `file-search`, `pytest`,
`curl-local-api` and `other`. They never contain arguments. Subcommands match
exactly; compound shell commands, substitutions and ambiguous targets cannot
be attributed to a single read and remain `other` or have no read identity.
A paired read with a missing identity makes classes 3 and 6 unknown, rather
than presenting an incomplete count as zero; class 6 still uses `no_marker`
when no marker exists. The `read_identity_absent` counter records these cases.
An unknown command cannot be an unchanged poll. Read tools with missing paths
also cannot be polls. A local API `curl` is a URL read, not a poll.

Paths normalize lexically with POSIX `normpath`. Relative paths join the stored
cwd before normalization. The parser never resolves symlinks. URL identities
keep scheme, host and path, drop query and fragment, then hash. Identities and
call IDs survive only as SHA-256 hashes. Results use UTF-8 strings or compact
JSON with sorted object keys and `ensure_ascii=False`. Cold-start bytes use the
stored JSON record bytes, excluding its newline, not a reserialized record.

Each identity/content-hash series is separate. A/B/A contains one changed
reread and one repetition of A. Poll output hashes also form separate series.
A reminder's repeated occurrences use each occurrence's own byte length,
including changed text. Hook hashes count once per model-call interval; identical
copies within an interval are not later model calls.

Class 4 takes precedence for large, unpaired and oversized results. Class 6
then takes eligible paired path reads in the 20-call window. Classes 3 and 5
classify the remaining results. These assignments keep waste bytes disjoint.
Large results still update read/poll history. The class 4 denominator contains
all result-body bytes, including small results, unpaired results and oversized
lines. The class 4 count includes only results above 20,000 bytes; a small
unpaired result adds bytes as required by the join rule, without incrementing
that count. Changed rereads are a separate diagnostic, never added to waste totals.

## Record dependencies and limits

| Class | Stored fields required |
| --- | --- |
| 1 | Explicit pre-action list and a distinct stored system field |
| 2 | `attachment.type=hook_additional_context` and its payload; request boundary |
| 3 | Paired tool result, recognizable read target, body hash and command shape |
| 4 | Result body; oversized lines use their full drained byte length |
| 5 | Paired result, exact non-read command shape and output hash |
| 6 | Explicit compaction marker, tool-call order and previously seen path |
| 7 | Event timestamps, paired IDs and provider usage records |
| 8 | Claude attachment types named in the frozen definition |

The module docstring fixes the pre-action list. Codex uses `session_meta`,
`turn_context` and system/developer `response_item/message` records before the
first tool call. Claude uses `system` and system-role assistant messages.
A distinct system field is required, even when pre-action records exist.
Codex `session_meta.payload.base_instructions.text`, `turn_context.payload`
`system_prompt`/`system_instructions`, or a system-role message qualifies.
Claude `system.systemPrompt`/`system_prompt` or a system-role message qualifies.
Reading a rules file is a read, never cold-start context.

Claude compaction is exactly `type=system`, `subtype=compact_boundary`.
Codex compaction is exactly `type=compacted`. No marker means `no_marker`.
Rehydration uses call order, including unpaired calls, not result order.
No time-gap heuristic or inferred resume is used.

Claude tool pairs use assistant `message.content[].tool_use` and user
`message.content[].tool_result`. Codex uses `response_item.payload` calls and
outputs, including the `function_call` sibling. A Claude `function_call` item
has no documented join rule and is not silently treated as a Codex record.
Reverse-order call/result pairs join; duplicate IDs count once.

Claude token requests use assistant `message.usage`. Codex token requests use
`event_msg.payload.type=token_count` and `info.last_token_usage`, otherwise
`info.total_token_usage` deltas. Raw `token_usage_record` events are not added
again to those counters. A negative cumulative delta contributes the new total.
Absent request categories remain unknown, including Claude cache categories
whose names differ from Codex `cached_input_tokens`. No token estimate is emitted.
First-request counters belong only to totals. No waste class receives tokens.

Hook payload fields are `attachment.content`, then `text`, then `stdout`;
otherwise the attachment object excluding `type`. Claude reminder bodies use
the same extraction. Codex class 8 remains `field_absent`; no recurring type is
invented. A missing hook field is `field_absent` for class 2.

A record is decoded one line at a time. Results become hashes and sizes before
the next line. Metadata, pending join hashes, read history and model totals are
retained; result bodies and command text are not. Lines above 8 MiB are drained
in bounded chunks and assigned to class 4 as `other`; their JSON is not decoded.
Malformed and truncated records increment counters without raising. Unknown
record/event types increment `other` without printing their names.

The manifest stores nanosecond mtime, file size and pairing count. Freeze checks
size and mtime before and after counting; report checks both before and after
parsing. Changed files are `stale_session`, without rescan or replacement.
Root absence or no qualifying sessions yields `unavailable` with
`no_eligible_session`. Undocumented harnesses use `no_documented_root`.
IO failures emit only `io_error` and a 16-hex digest, never exception text.

## Output and verification

Numeric measures have `{"value": N}`. Unknown measures have
`{"value": "unknown", "reason": "field_absent"}` or another fixed reason.
The reason enum is `field_absent`, `no_marker`, `unpaired`, `stale_session`,
`no_documented_root`, `no_eligible_session`, `io_error`, `invalid_manifest`
and `ambiguous_model`. Counters distinguish malformed, truncated, oversized,
unknown, duplicate and unpaired records. Aggregates propagate unknowns rather
than labeling a partial sum complete. Class 4 share is weighted by result bytes,
not an average of session shares. Wall durations are summed across sessions;
they do not describe unique elapsed host time. Wall time requires two stored
timestamps and uses first-to-last event order, rather than sorting timestamps.

Session output lists digests, per-session metrics and per-model metrics.
Harness output aggregates each category separately and includes model groups.
Only recognized model-label syntax is emitted; absent identity is `unknown`.
Cold records before model identification can be attributed to a single known
model; with multiple models that preamble stays in the unknown model bucket.
Provider tokens are attributed to the model on their record. Tool-result bytes
are attributed to the paired call's model. Metadata-only preamble records do
not invent unknown-model requests.

Run the explicit new test file and Ruff on the changed Python files. The tests
create synthetic JSONL and assert literal byte totals, joins, exclusions,
reset arithmetic, frozen sample checks and output redaction. The independent
held-out comparison is the later driver gate specified above; it is not
replaced by these tests, schema checks or a successful CLI invocation.

Packet delivery requires a pushed SHA matching `git ls-remote`, green tests and
Ruff, and local manifest/baseline files. The baseline `tool_sha` must match the
pushed SHA and its manifest digest must match the actual manifest file.
The driver owns held-out recomputation, exact-head cross-family review,
PR/CI, landing and parent closeout. This packet opens no PR.
