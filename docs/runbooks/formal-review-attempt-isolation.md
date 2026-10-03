# Formal review attempt isolation

## Curriculum reviews use full access

Operator direction adopted on 2026-10-01 (#9464) requires curriculum plan,
lesson and lesson re-review seats to check Ukrainian against sources and project
material. These reviews use `--review-access full` (the dispatch default) with
`--full-checkout --mode read-only`. Claude Code, Codex and AGY retain their
ordinary read/search tools, repository and git context. The actual working tree
must match every manifest input hash; a mismatch refuses as
`full_review_tree_mismatch`. The same check runs again before adapter launch.

Full access uses the same isolated attempt boundary, sources socket forwarder
and `AttemptEgress` allowlist proxy as isolated mode. Its only wider grant is
read-only access to the verified full checkout, the Git metadata and object
store needed by that checkout, and the repository's shared `data/` corpus.
A linked checkout gets its own Git metadata plus common objects, refs and
configuration; the owning checkout and sibling worktrees are not mounted.
`batch_state/`, nested dispatch checkouts and other worktrees' Git metadata are
hidden. External Git object alternates are refused with
`full_review_git_alternates_unsupported`. Read sets containing sockets, FIFOs
or device files are refused with `full_review_special_file_refused`: a
read-only socket mount would still allow host command execution.

Bubblewrap starts from an empty root, with private network, PID, IPC and UTS
namespaces, a private procfs, `--new-session`, `--die-with-parent` and dropped
capabilities. A synthetic single-account passwd/group pair supports native shell discovery
without exposing the host account databases. The real home, host `/run`, user
D-Bus, host loopback services,
abstract Unix listeners, receipt store, task records and saved results are
unmounted or unreachable. Only the attempt's private runtime/home/return tree
is writable; checkout and corpus files are read-only. The sources server and
ledger writer remain outside and are reached through the attempt socket.
The namespace-local TCP forwarder sends provider traffic through the parent
CONNECT-only proxy to exact allowlisted API hosts. Clearing proxy variables
does not create a host network route. Claude stages only selected provider
authentication, including a fresh Linux OAuth access token, into the private
seat environment; it receives no real-home credential directory.

Missing Bubblewrap refuses with `sandbox_unavailable:linux_bwrap_missing`;
failed namespace/read/write probes refuse with `sandbox_probe_*`, and a
missing proxy refuses with `attempt_egress_unavailable`. There is no weaker
fallback. CLI compatibility and effective-MCP probes run inside the same
boundary. Codex defers its nested sandbox to the OS boundary so sources stdio
remains usable. AGY's native sandbox is supplementary; its permission bypass
remains forbidden. Full AGY attempts project `permissions.allow` into the private
`$AGY_APP_DATA_DIR/settings.json`, enumerating the exact targets
`mcp(sources/<tool>)` from `scripts.review.receipts.ledger.review_tools("full")`.
For example, the word verifier is granted by `mcp(sources/verify_words)`.
There are no wildcards or grants to other servers or built-in tools.
AGY 1.2.14 does not accept the server-only `mcp(sources)` rule for this call;
the authenticated fixture must verify the exact target syntax.
The sources-only MCP catalog does not itself
grant permission: without this rule, headless sandboxed AGY auto-denies MCP
calls. The launch gate refuses missing or widened settings, including wildcard
and additional grants. Legacy isolated-mode settings and flags are unchanged.
Detached children of the seat are killed with the PID
namespace. This statement does not certify authenticated provider completion:
use the captured runtime probes below for each actual seat.

The reviewed-tree check runs before `prepare_review_attempt` creates an
exclusive ledger/config. A refused tree leaves its attempt id reusable; a
newly provisioned checkout is removed through the common worktree reaper.
Reused checkouts remain their owner's responsibility. The tree is checked
again before the sandboxed adapter launch.

`review_access` lives beside, never inside, the task's exact `review_attempt`
binding. The recorder reads it from that task, verifies the saved result bytes,
result hash, fresh rendered prompt and attempt identity as before, and stores
`access`, resolved model, family and harness. Full plan projections carry these
fields; promotion receipts carry `review_access` and reviewer provenance. Old
task records and historical database rows retain `isolated`. Findings schema,
verdict thresholds, stale checks, attempt budgets and failure counting stay the
same. Version 5 adds only `attempts.access` to the findings database.

Every attempt's stdio sources process receives `LU_REVIEW_ACCESS`: full mode
advertises and accepts exactly `FULL_REVIEW_TOOLS`, including `search_resources`;
isolated mode retains exactly `REVIEW_TOOLS`. Calls outside the set are refused
and ledgered. Missing or invalid access advertises no tools and refuses before
execution. Ordinary non-review sources sessions keep their full catalog. Full
Claude seats grant these exact MCP names alongside their ordinary reviewer tools, preserving the
write-denial profile and hooks; they use no MCP wildcard. Codex and AGY reach
the same attempt-specific server and recording gate.

After landing a server change, the accountable driver must restart the running
sources service to load it, after confirming no live dispatch depends on that
service. Fixture probes launch the candidate worktree server without changing
the running service.

Full-mode rendered prompts require ledgered sources checks for every Ukrainian claim
relied on, including approval-critical clean checks, and allow `search_resources`
for catalogue evidence. Repository/corpus/git reads are context: only sources
receipts are citable. Other attempts' returns, verdict projections,
`plan-review*.yaml` and the findings database for this artifact are forbidden
inputs, except supplied manifest/context pins and a re-review's explicitly
pinned previous attempt and ledger. Clean-check citations fit YAML comments;
the return schema and verdict dimensions are unchanged.

### Residuals and owners

- **Plan-author family — plan driver:** no model-bearing plan writer record is
  produced by the existing pipeline. `X-Agent` trailers identify a harness/task,
  not a concrete model family reliably. The recorder enforces same-family
  refusal for lessons through their writer record; the plan driver must retain
  author provenance and select an independent family until reliable plan writer
  records are available. A trailer alone is not that proof.
- **Runtime coverage — review-harness driver:** fake Claude, Codex and AGY seats
  execute the same escape script under their real adapter's OS boundary. It
  attempts systemd/D-Bus command access, host TCP ports 22 and 8765, a host
  abstract Unix listener, private-home credentials and writes to five protected
  targets. Git log/show and corpus reads must work; detached children must die.
  Separate per-seat tests perform a real sources handshake, verify the outside
  server's ledger receipt, and prove allowed TLS proxy traffic with a
  deterministic provider fixture. Fake seats prove the mechanism, not paid
  provider completion. Real Claude/Codex checks are opt-in and require captured
  shell execution and sources receipts. Real AGY completion remains unverified
  until the accountable driver completes AC-04.
- **AC-04 — accountable driver:** after landing, run a real bound full review
  with a short timeout. Require task binding plus `review_access: full`, a cited
  nonempty ledger, a trace of an outside-pin repo read or git command, recorder
  content disposition, status naming the same manifest, and one-input-change
  stale detection. A captured-return fixture proves the mechanism only.

Full-mode boundary regressions and authenticated negative probes:

```bash
"$PROJECT_PYTHON" -m pytest tests/agent_runtime/test_full_review_access.py -q -s
LU_FULL_REVIEW_REAL_PROBES=1 "$PROJECT_PYTHON" -m pytest tests/review/test_full_review_access.py -q -s
# Scratch Claude catalogue proof; never records a curriculum review verdict:
LU_FULL_REVIEW_REAL_PROBES=1 "$PROJECT_PYTHON" -m pytest tests/review/test_full_review_access.py -k claude_full_review_search_resources -q -s
```

The fake-seat denominator is Claude, Codex and AGY across the must-fail and
must-succeed matrix above. Host listeners have outside-sandbox positive
controls. Shared Git/corpus access has a linked-worktree regression that also
proves neighboring checkout denial. Authenticated probes reuse the same script
and require captured command/output, unchanged protected bytes, an outside
sources receipt and detached-child teardown. Actual provider completion proves
allowlisted provider connectivity. These are runtime boundary probes; the
linguistic review and recorder acceptance proof remains AC-04.

## Explicit isolated mode

Issue #9251's filesystem boundary remains available with
`--review-access isolated` for non-curriculum uses that require isolation.
Curriculum review of record must use full mode. The existing isolated AGY/Codex
route and its refusals are unchanged. Render and check with `--review-access
isolated` to retain the main prompt bytes and original tool list; the evidence
duty paragraph and `search_resources` are full-mode additions only. Claude isolated attempts still refuse with
`attempt_boundary_claude_adapter_pending`; full Claude attempts do not. Cursor
and other unsupported harnesses remain refused.

Isolated attempts on Linux have a private network namespace (`--unshare-net`),
private PID namespace and private procfs. The host network and its loopback,
interface listeners and abstract Unix sockets are unreachable, even when proxy
variables are cleared or overridden. Ordinary dispatches retain their launch
and network settings. Their parent file reads use trusted adapter roots resolved
before launch, so legitimate symlinks above those roots remain supported.
Rollout discovery treats a refused, unbound candidate as a non-match.
Platforms without the network namespace mechanism are refused for isolated
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

For `--branch B --review-attempt <manifest>`, render from a detached worktree
at the exact commit (`git worktree add --detach <render-worktree> <commit>`).
The render worktree must not hold the dispatch's target branch. Dispatch
protects a branch holder containing the attempt manifest or the render record's
`input_root` or `render_checkout` and refuses before admission with
`review_attempt_branch_holder_conflict`, suggesting a detached render worktree
(#9388). Ordinary dispatches retain their stale-holder release behavior.

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
directory to check record integrity. Formal manifest admission then independently
re-renders using the **server checkout's** templates, derived from the running
admission code and runtime configuration, never from the render record. The
record's `input_root` remains only the pinned-input locator: containment and
pin-hash checks still apply. A different recorded template directory refuses as
`review_render_record_prompts_dir_mismatch`, even with matching template hashes. A
record copied from another attempt refuses as `review_render_record_attempt_mismatch`;
edited or stale digests refuse as `review_render_record_digest_mismatch`. The
existing prompt-hash, server-code and launch-time checks still apply. Older
render records require a fresh render; they cannot authorize a new attempt.

Issue #9378 adds server template authority at this pre-launch gate. Admission
passes the recorded reads, path hashes and logical template map to `check_prompt`.
The checker derives the complete loaded-template set from its own server render,
then compares exact loader names and hashes and requires byte equality of the
prompt. It relocates only exact template loader paths between checkouts; it does
not relocate input pins or case-fold names. A copied tree with an injected template
refuses as `prompt_render_invalid: prompt_not_exact_render`; omitted or substituted
dependencies refuse as `template_read_not_recorded` or `template_sha256_mismatch`
under the same admission code. A loaded template absent from the server refuses;
missing templates on both sides still refuse as
`review_render_record_digest_mismatch`. An unused added template is admissible.
Absolute or traversal loader names refuse as `review_render_template_name_invalid`;
the renderer refuses symlink aliases as `template_alias_refused`, and a sidecar
path outside its declared template directory that resolves to a loaded server
template refuses as `template_identity_mismatch`. Nested list or
mapping IDs refuse as `non_scalar_attempt_id` through `attempt_ids_unreadable`
(manifest prompts) or `prompt_attempt_ids_unreadable` (custom prompts).

Clean worktrees at the server commit, plan worktrees behind it with unchanged
used templates, fixture input roots and `previous_attempt` re-reviews remain
admissible. If a legitimate flow cannot meet these checks, stop and report it;
do not substitute render-checkout templates. Pinning tests live in
`tests/review/test_template_admission.py` and
`tests/test_delegate.py::test_render_manifest_server_authority_refuses_before_launch`.

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

The Claude adapter is unchanged in this branch. Only isolated Claude
attempts remain refused; full attempts use the private boundary above. The separate Claude follow-up owns the remaining parent-read audit:

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

The isolated Claude adapter change is excluded from this branch so it can receive an
eligible cross-family review: changing that adapter excludes Claude reviewers
because it governs their own boundary. A Claude Opus worker owns the follow-up
PR, reviewed by `gpt-6.1-sol`.

At critical and high risk the automatic bench (`scripts.review.bench_health`, #9394) gives Anthropic-authored code a single automatic cross-family reviewer, `openai_frontier`, and exits 1 for that shortfall; at high risk OpenAI-authored code likewise has only `claude-opus-5-5`, because high admits only those two models (#9538). Explicit-pin reserves never satisfy the two-seat minimum.

Under `review_attempt_boundary`, replace the ordinary worker-guard `--settings`
with `--setting-sources ""` and `--disable-slash-commands`. Empty setting sources
prevent host/project settings and hooks from loading; disabling slash commands
prevents command expansion. Keep the instruction-free fresh home and OS closure.
Do not add `--bare`: it disables subscription authentication, as documented in the
[Claude authentication reference](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token).
The follow-up must remove the isolated-only typed refusal, restore Claude's isolated launch-proof test
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

The curriculum driver owns the post-landing full-access proof (AC-04 of #9464).
For the AGY permission regression, first run the opt-in fixture probe, which
uses a harness-only review id and never records a curriculum verdict:

```bash
LU_FULL_REVIEW_REAL_PROBES=1 "$PROJECT_PYTHON" -m pytest \
  tests/review/test_full_review_access.py::test_real_agy_full_review_sources_permission -q -s
```

Require a completed final reply with `AGY_FULL_SOURCES_COMPLETE`, a receipt id
present in that reply, and at least one successful `verify_words` ledger row.
`LU_FULL_REVIEW_PROBE_ARTIFACT_DIR` optionally retains the proof JSON and ledger
in ignored local storage. This proves full-mode permission and receipt transport;
it does not certify a plan's semantic review or replace the post-landing proof.

Set `MANIFEST` to the current engine-produced plan manifest, `INPUT_ROOT` to
an expendable full review checkout containing those exact pinned inputs and git
history, and `PROMPT` to an ignored prompt file. Use fresh IDs and a short timeout:

```bash
REVIEW_ID=plan-a1-position2-full-proof
ATTEMPT_ID=agy-full-9464
"$PROJECT_PYTHON" -m scripts.review.prompts.render "$MANIFEST" \
  --repo-root "$INPUT_ROOT" --output "$PROMPT" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py dispatch \
  --agent agy --model gemini-3.8-flash-high --mode read-only \
  --review-profile ukrainian --effort high \
  --task-id review-9464-plan-proof --cwd "$INPUT_ROOT" \
  --full-checkout --review-access full --hard-timeout 180 \
  --prompt-file "$PROMPT" --review-attempt "$MANIFEST" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py wait review-9464-plan-proof
```

After live routing/capacity preflight, record the captured task result through
`scripts.review.record`. The proof is independent of the verdict: require the
exact task binding and `review_access: full`; a nonempty ledger cited by the
return; a trace showing a repo read outside the pins or a git command; a recorder
content disposition; `plan_review_status` naming that manifest; and changing
one input making the review stale. A completion string or APPROVE alone is
insufficient. The captured-return fixture establishes the chain but not real
seat access or source use; AC-04 remains open until this run. The driver also
owns independent exact-head review and landing of this implementation.
