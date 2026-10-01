# Formal review attempt isolation

Issue: #9251. This boundary applies to `delegate.py dispatch --review-attempt`
for plan, lesson and lesson re-review attempts, using AGY or Codex.
Claude formal attempts refuse before boundary provisioning or adapter launch
with `attempt_boundary_claude_adapter_pending` until its adapter change lands
separately. Ordinary Claude dispatches remain supported.
Cursor is explicitly refused at admission and provisioning until it has a
proven boundary. Other unsupported harnesses remain refused.

Formal attempts on Linux have a private network namespace (`--unshare-net`),
private PID namespace and private procfs. The host network and its loopback,
interface listeners and abstract Unix sockets are unreachable, even when proxy
variables are cleared or overridden. Ordinary dispatches retain their launch
and network settings. Their parent file reads use trusted adapter roots resolved
before launch, so legitimate symlinks above those roots remain supported.
Rollout discovery treats a refused, unbound candidate as a non-match.
Platforms without the network namespace mechanism are refused for formal
attempts; the former macOS filesystem-only capability is insufficient here.

The authorized manifest closure is the complete set of eligible, hashed file
pins in the manifest: `inputs.*`, plus lesson `module_digest` and
`upstream_lessons`. A lesson re-review additionally admits **exactly** its
`previous_attempt.review`, `previous_attempt.ledger` and `diff` pins. Existing
schema and pin-eligibility rules decide admission; this does not extend the
review contract. References inside an input do not authorize more reads.

Before adapter planning, the runner verifies the manifest against the attempt's
MCP manifest digest, verifies each input hash, and copies the closure into a
private input directory. Relative input paths are preserved, except the previous
receipt ledger, projected as `authorized/previous-ledger.jsonl`. Neither the
original shared state directory nor any neighboring receipt is exposed. The
rendered prompt already contains these inputs, including the re-review evidence.

The real harness process and its tool subprocesses run inside the existing
verified Bubblewrap sandbox on Linux. The input directory is read-only. The writable
directory holds only this attempt's fresh home, configuration, transcript, temp
files and return. The installed executable and its narrow runtime dependencies
are readable; its native binary's parent directory is not granted. No original
checkout, Git objects, original home, prior session, receipt store or review
harness source is mounted. CLI authentication is staged narrowly into the fresh
home; sessions, project instructions, hooks and provider configuration are not
copied. An unavailable sandbox or a failed capability probe refuses launch;
there is no shared-network or filesystem-isolation fallback.

Runtime access and seat evidence are separate. A parent-owned sources process
runs outside the seat sandbox with the attempt's original receipt environment.
A byte-only stdio client inside the sandbox connects to that process through
one attempt-local Unix socket. The model can call sources tools, but cannot read
the sources implementation, current ledger, sidecar, or receipt directory. The
host worker captures the return and `scripts/review/record.py` records it outside
the seat boundary. Receipt and canonical return layouts are unchanged. The
runner parses the fresh transcript before cleaning up the boundary and sources
processes, including on refusal, timeout or failure. Formal attempts cannot resume
or trigger runner provider failover.

Codex uses its fresh sources-only home and bypasses its nested
sandbox, which otherwise cancels stdio MCP calls. AGY uses a fresh home and
app-data directory under the same OS boundary. AGY's separate sealed code-review
`review_isolation` mode remains refused; formal content attempts use the
runner-owned manifest boundary, rather than enabling that unsupported mode.

## Artifact binding at admission and recording

Issues #9012, #9025 and #9242 bind each artifact to the same attempt. A render
manifest prompt is admitted through `check_prompt` with the dispatch review and
attempt IDs: its bytes must equal a fresh render of the authorized manifest.
Custom prompts retain the ID parser, which checks every attempt declaration
and refuses conflicting or unreadable later IDs, including prose and nested
mappings, lists, anchors and merge keys within each attempt or schema. YAML schema
examples nested inside `data_fence` blocks remain pinned data, not return schemas.
An invalid render refuses as `prompt_render_invalid` before provisioning or launch.

The version-4 render record includes the review ID, attempt ID, prompt hash,
input root and render checkout. Dispatch recomputes the recorded server components
and template hashes from that checkout's canonical `scripts/review/prompts`
directory. A different recorded template directory refuses as
`review_render_record_prompts_dir_mismatch`, even with matching template hashes. A
record copied from another attempt refuses as `review_render_record_attempt_mismatch`;
edited or stale digests refuse as `review_render_record_digest_mismatch`. The
existing prompt-hash, server-code and launch-time checks still apply. Older
render records require a fresh render; they cannot authorize a new attempt.

Dispatch stores the manifest hash supplied by `prepare_review_attempt`'s plan;
it does not reopen the manifest to construct the task's binding. The runner's
terminal task record also stores `result_sha256` for the UTF-8 bytes saved in
its canonical task result file. Before attesting a placeholder or admitting a
formal bound return with a real prompt hash, the recorder requires a `done`
task with matching review/attempt/manifest IDs, the canonical result pointer,
the recorded result hash, and byte equality with the saved result. Copying the
result unchanged to a separate return file is allowed. Editing, extracting or
substituting other bytes refuses as `review_return_task_mismatch`, before any
saved return or attempt row is written. Use the raw saved task result;
do not strip fences or normalize it before recording. Placeholder substitution
happens only after this binding succeeds. Existing custom returns without a
formal task binding retain their validator path; failure recording is unchanged.

## Parent read boundary and site inventory

Seat-writable names remain untrusted after exit. `safe_read_attempt_file` in
`scripts/agent_runtime/attempt_boundary.py` anchors its walk at the parent-owned,
already-resolved attempt `write_root` or known adapter root, then walks every
component below it with `openat` directory descriptors and `O_NOFOLLOW | O_DIRECTORY`,
then opens the leaf with `O_NOFOLLOW | O_NONBLOCK | O_NOCTTY`. It checks the opened
fd for a regular file, runner UID ownership and exactly one hard link. Full and
invocation-suffix reads cap accepted data at 64 MiB, refusing overflow; session-ID
reads consume up to a 1 MiB prefix and parse at most 25 lines, irrespective of
total rollout size. Checked fd metadata supplies resumed lengths, and diagnostic
tails seek on that fd.
Reads use that fd only, with a bounded read and a second metadata check. Missing
optional telemetry remains absent; unsafe reads raise body-free `AttemptReadError`
codes. Runner parsing converts refusals to failed `ParseResult` values with no response, without
rollout, stdout or provider fallback. A refused, unbound rollout candidate is a
non-match; a refused bound rollout remains a typed failure. V4 finalization
records empty output and the typed refusal instead of raising on the same read.
Diagnostic tail refusals yield no text.

This uses the directory-fd method described in the
[Linux open/openat reference](https://man7.org/linux/man-pages/man2/open.2.html);
`O_NOFOLLOW` on the leaf alone does not protect preceding components.

| Parent read site | Walk anchor and ownership | Disposition |
| --- | --- | --- |
| Codex `parse_response`: final output file | Plan `parent_read_root`: parent-owned attempt `write_root`; ordinary temp root resolved before launch; `/` without a plan. | Shared reader; unsafe output returns typed failure immediately. |
| Shared `_output_schema.load_output_schema` and Codex `_tool_config_flags`: caller-supplied output schema | Parent-owned `review_write_root` when supplied; otherwise schema parent resolved before launch. | Shared reader before JSON/hash validation. Dispatch refuses `--review-attempt` with `--output-schema` as `attempt_output_schema_unsupported`. |
| Codex `_read_rollout_segment`: completion, prompt binding and tool trace | Adapter `_rollout_read_root`: parent-owned attempt `write_root`; ordinary Codex home resolved before launch; `/` for unplanned calls. | Shared reader with invocation offset; unsafe reads cannot be swallowed by matching/recovery. |
| Codex `_select_rollout_for_plan` and `_read_rollout_session_id`: session metadata | Same `_rollout_read_root`, passed through to the session-ID reader; `/` for direct calls. | Shared reader before metadata parsing. |
| AGY `_read_transcript_events`: transcript events | `_transcript_read_location`: parent-owned attempt `write_root`; ordinary app-data root resolved before launch; `/` for changed ordinary overrides or direct calls. | Shared reader with invocation offset; a shortened resumed transcript remains unbound. |
| AGY `_transcript_baseline`: resumed prefix sizing | App-data root resolved before launch, while still parent-controlled; formal attempts cannot resume. | Checked fd `fstat` size; no transcript bytes read. |
| AGY `_conversation_id_from_log`: invocation log | Plan `log_read_root`: parent-owned attempt `write_root`; ordinary log parent resolved before launch; `/` for direct calls. | Shared reader before UUID extraction. |
| AGY `_inline_saved_tool_result_pointer`: saved result | Plan's transcript read root carried through FIFO, indexed and generic result pairing; parent-owned attempt `write_root`, ordinary pre-launch app-data root, or `/` for direct calls. Ordinary dispatches map a captured app-data alias lexically onto the pre-launch resolved root; attempts never get an alias. Conversation steps directories are lexical containment only, never walk anchors. | The no-follow read stays anchored at the resolved root; the shared reader refuses replaced conversation ancestors even after the transcript has been read. |
| Runner `_finalize_v4_runner_origin`: output observation | Plan `parent_read_root` (parent-owned attempt `write_root` or ordinary pre-launch adapter root); `/` if absent. | Shared reader before recording; refusal cannot persist host bytes. |
| Runner failure diagnostics via watchdog `tail_liveness_file_for_debug` | Default `/`: parent-owned filesystem root, with every descendant walked no-follow. | Checked fd seek and bounded tail read; unsafe files yield no diagnostic bytes. |
| Runner `_prepare_stdin_handle`: prompt input | No named-file walk anchor. | Retains the original parent-created descriptor through spawn, without reopening its name. |

The anchor audit found no other seat-writable walk anchor in these consumers.
Ordinary pre-launch roots are trusted adapter configuration, not formal-attempt
isolation claims. A fallback `/` is conservative and does not trust a replaced
intermediate directory. The sandbox swap regression builds each plan with its
real adapter and preserves these anchors while substituting the probe command.

Residual N5: the Codex session-ID prefix bound is raised from 64 KiB to 1 MiB,
giving more headroom for session metadata containing instructions and configuration.
Metadata truncated by that bound or beyond the first 25 lines remains unbound;
partial JSON and unvalidated session IDs are not accepted. Infra owns any future
change to these limits, with an oversized metadata-line regression and exact-head
review before landing.

Codex rollout timestamps, snapshot sizes, liveness mtime polling and runner
cleanup size checks inspect metadata only; they never read target bytes.
Attempt provisioning reads manifest pins, MCP configuration, installed runtime
headers and parent-created proxy configuration before any seat launches. These
are authorized inputs or parent-owned setup, not post-launch seat output reads.
Stdout/stderr are existing parent-held pipes or PTYs, not reopened names.

The Claude adapter is unchanged in this branch and remains refused for formal
attempts. The separate Claude follow-up owns this complete read audit:

| Claude site | Required follow-up |
| --- | --- |
| `_tool_calls_from_claude_session_jsonl` | Route seat-writable session telemetry through the shared reader. |
| `_mcp_server_names` | Use the shared reader for scoped MCP configuration; runs before launch today. |
| `build_invocation` sources-only MCP bytes check | Preserve containment and use the shared reader for writable scoped configuration. |
| `_worker_guard_settings` | Reads tracked settings before launch; retain trusted source provenance. |

The regression denominator includes sandboxed seat swaps of both Codex output
and AGY transcript with outside-boundary sentinel controls, plus hard links,
FIFOs, a device, oversized/growing files, wrong owners, directory symlinks and
swaps immediately before/after descriptor opens. These are boundary integrity
proofs, not semantic curriculum-review acceptance. Infra owns exact-head
cross-family re-review and landing; the Claude follow-up owns its deferred sites.

## Claude adapter follow-up

The Claude adapter change is excluded from this branch so it can receive an
eligible cross-family review: changing that adapter excludes Claude reviewers
because it governs their own boundary. A Claude Opus worker owns the follow-up
PR, reviewed by `gpt-6.1-sol`.

Under `review_attempt_boundary`, replace the ordinary worker-guard `--settings`
with `--setting-sources ""` and `--disable-slash-commands`. Empty setting sources
prevent host/project settings and hooks from loading; disabling slash commands
prevents command expansion. Keep the instruction-free fresh home and OS closure.
Do not add `--bare`: it disables subscription authentication, as documented in the
[Claude authentication reference](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token).
The follow-up must remove the typed refusal, restore Claude's launch-proof test
matrix, and establish its own exact-head provider compatibility proof.

## Provider egress boundary

`scripts/config/attempt_provider_egress.yaml` contains the exact per-harness
hostname allowlist. It includes the native provider startup/eligibility services
as well as the inference endpoints; AGY's profile-image dependency is an exact
hostname, with no domain suffix or wildcard grant. No runtime override admits
additional hosts. The parent loads this config before launching a seat.

The parent proxy (`attempt_network.py`) listens on a per-attempt Unix socket.
It accepts only `CONNECT canonical-host:443` with exact allowlist membership,
rejecting plain HTTP, IP literals, userinfo, malformed authorities, suffix
lookalikes, conflicting or duplicate Host headers and request bodies. It
normalizes mapped addresses and validates every DNS answer: one non-global,
multicast, reserved, unspecified or host-interface address rejects the entire
request. Interface addresses are enumerated at startup. Connections use only
the validated numeric addresses, with no second lookup.

The projected stdlib forwarder (`attempt_forwarder.py`) starts inside the
namespace before the CLI. It relays bytes from namespace loopback to that Unix
socket, without interpretation. It replaces inherited proxy variables with
`HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY`, `http_proxy`, `ALL_PROXY` and
`all_proxy`, and sets both `NO_PROXY` spellings empty. The HTTP variables ensure
plain HTTP requests go to the proxy and are refused. A CLI that ignores these
variables has no direct network route. Sources keeps its separate stdio-to-Unix
bridge; sources does not use provider egress.

The parent enforces an 8 KiB header cap, 16 concurrent connections, two resolver
processes, 5-second header/resolver deadlines, a 10-second total connect deadline
and 60-second idle/drain deadlines. Relays read 64 KiB chunks with backpressure;
stream reader buffers are bounded. Resolver output is capped at 64 KiB. DNS
processes are killed and reaped on timeout or cancellation. Destination/byte
aggregates are bounded by the allowlist and contain no payloads or addresses.
Parent cleanup cancels connections and resolvers and closes the listener. A
stopped proxy, failed forwarder or failed namespace refuses launch without
falling back to the host network.

## Provider compatibility proof

At the exact implementation head, record the SHA-256 of the allowlist and each
native CLI version. For AGY and Codex, wrap their real adapter invocation
with `AttemptBoundary.wrap`, provide a minimal prompt requesting a fixed token
without tools, and parse the actual terminal response with that adapter. Retain
only the implementation SHA, allowlist digest, CLI version, tested variable,
exit status, exact-token verdict and destination/byte aggregates in ignored local
evidence. Never retain credentials, payloads, host addresses or host paths in
public evidence. Proxy traffic alone or `--version` is insufficient proof.

To identify a variable unambiguously, launch a projected stdlib helper after the
forwarder that leaves only `HTTPS_PROXY` set before executing the mounted native
CLI. Require a successful authenticated fixed-token response and positive proxy
bytes correlated with that invocation. Then stop the parent proxy and repeat the
same wrapped invocation: it must refuse before the CLI can produce the token.
A harness failure remains a blocker; do not broaden the network namespace or
silently substitute a provider. Independently repeat this proof on the reviewed
head before landing; a changed proxy, allowlist or invocation voids prior proof.

AC-2 retains the AGY and Codex proof rows. The Claude row is excluded from this
branch's compatibility claims and belongs to the adapter follow-up; its refusal
tests prove only that an attempt cannot launch, not provider compatibility.

## Verification and post-merge proof (AC-4)

Set `PROJECT_PYTHON` to the prescribed shared project interpreter. Run from the
merged dispatch checkout. These are scoped foreground tests; no provider/model
request is made by the host probes:

```bash
"$PROJECT_PYTHON" -m pytest \
  tests/agent_runtime/test_attempt_safe_read.py \
  tests/agent_runtime/test_attempt_boundary.py \
  tests/agent_runtime/test_attempt_network.py \
  tests/agent_runtime/test_codex_adapter.py \
  tests/agent_runtime/test_codex_rollout_match.py \
  tests/agent_runtime/test_codex_hook_probe.py \
  tests/agent_runtime/adapters/test_agy_adapter.py \
  tests/agent_runtime/test_review_mcp.py \
  tests/agent_runtime/test_stdin_tempfile_spawn.py \
  tests/agent_runtime/test_runner_failover.py \
  tests/test_agent_runtime.py \
  tests/test_agent_runtime_tool_calls.py \
  tests/test_agent_runtime_json_parse.py \
  tests/test_agent_runtime_rate_limit.py \
  tests/build/test_reviewer_schema_transport.py -q
LU_REVIEW_HOST_PROBES=1 "$PROJECT_PYTHON" -m pytest \
  tests/agent_runtime/test_attempt_boundary.py -q
```

The first command includes protocol parsing, DNS rebinding/mixed-answer denials,
resolver hangs, slow headers, floods, connect deadlines and proxy failures. Every
inside-boundary denial probe must exit zero with an explicit denial, and every
forbidden fixture has an outside-boundary positive control. The escape matrix
includes IPv6/mapped sockets, cleared/overridden proxies, redirects, host abstract
sockets, neighboring attempt sockets, inherited file/socket/namespace descriptors,
private procfs and absent sysfs. A subprocess launch error never proves denial.

The second command requires the actual installed AGY and Codex CLIs.
It fails if their real executables or dependencies cannot launch inside the
boundary. The test matrix exercises each harness and each attempt kind, denying
absolute reads, traversal, symlinks, Git history, prior homes and sessions;
allowing copied inputs, sources calls, receipt recording and the own return.
Claude's plan, lesson and re-review rows instead prove the typed refusal before
adapter planning or process launch.
The normal CI run uses a native executable fixture for adapter startup only;
filesystem probes and sources calls use the real production boundary in both
modes. A separate reviewer should run these probes on the target host at the
merged SHA and retain the output. These tests establish Linux capability only; other platforms remain refused.

The curriculum consumer owns the clean #8425 A1 position-2 plan-review rerun.
Set `MANIFEST` to its current engine-produced plan manifest, `INPUT_ROOT` to
the checkout containing those pinned inputs, and `PROMPT` to an ignored local
prompt file. Use fresh review/attempt IDs; do not reuse any earlier attempt:

```bash
REVIEW_ID=plan-a1-position2-isolation-proof
ATTEMPT_ID=agy-clean-9251
"$PROJECT_PYTHON" -m scripts.review.prompts.render "$MANIFEST" \
  --repo-root "$INPUT_ROOT" --output "$PROMPT" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py dispatch \
  --agent agy --model gemini-3.8-flash-high --mode read-only \
  --task-id review-9251-plan-proof --worktree \
  --prompt-file "$PROMPT" --review-attempt "$MANIFEST" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py wait review-9251-plan-proof
```

After the current routing/capacity preflight, the consumer runs this once and
records the return through the existing review recorder. Infra independently
checks the transcript and receipt ledger: no forbidden read succeeds, the
sources calls have current-attempt receipts, and the return is attributable to
the same manifest and dispatched head. A provider completion or an APPROVE
string alone is insufficient. Material exposure blocks shipment; two review
rounds then escalate under the issue's stop policy. Infra owns boundary/host
proof failures; the curriculum consumer owns the semantic review rerun. Issue
closeout waits for both proofs, exact-head cross-family approval and landing.
