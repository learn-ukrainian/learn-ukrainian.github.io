# Native Muse delegate workers

The `muse` adapter selects `muse-wonder-full-1.0` or `muse-spark-1.3` explicitly.
Both are worker models. Neither has a review, approval, advisory or driver role.
They have no automatic routing seat or fallback mapping. Wonder-Full is active
for explicit delegate workers; Spark remains on hold. Delegate, direct runner
calls and adapter planning apply the existing catalog execution gate before a
native process or version probe. Activation does not certify native permissions,
contributor/write behavior, formal review or driver use.
After catalog admission, only Wonder-Full's `implementation` role with
`workspace-write`, or `investigation` role with `read-only`, passes worker
classification. Missing roles, other combinations and Spark execution refuse.
Spark stream parsing remains available for qualification without admission.

## Permission and transport contracts

| Delegate mode | Native profile | Available tools |
| --- | --- | --- |
| `read-only` | `:read-only` | `read_file` |
| `workspace-write` | `:ask-me` | `read_file`, `write_file`, `edit_file` |

Shell execution, web tools, reminders, user-input requests and foreign personal
context are disabled. The toolset excludes subordinate agents and session
messaging. Read-only workers also receive `--disable-write`. File edits in write
mode remain subject to the native profile. These workers cannot run commands,
tests, Git commits or pushes themselves. Normal delegate finalization still
decides whether a write task produced its required deliverable.

The adapter pins `--workspace` to the managed dispatch worktree and disables
Muse's separate worktree creation. It uses a fresh session UUID and a private
prompt file in the task's managed scratch lease. Resume is refused. Contributor
mode is explicitly off. The adapter requests `MUSE_NO_AUTO_UPDATE=1`; that
variable must survive the shared child-environment sanitizer before admission.

The shared runner retains process identity, cancellation, deadlines, primary
checkout monitoring, task records and read-only checkout snapshots. Delegate
checks the admitted task, mode, model, workspace and run nonce before Muse
execution. Muse calls disable runner fallback. No launcher guard is changed;
`MUSE_GUARD_PARITY_UNPROVEN` still applies to the driver launcher.

## Inspect an invocation

Use an existing dispatch worktree or the default planned detached worktree.
Spark dispatch and dry-run refuse with `muse_execution_not_admitted` before any
native process or probe. The following command documents Wonder-Full's preview
interface. A real qualification task still needs the accountable driver's
separate authorization and held-out evidence.

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent muse --model muse-wonder-full-1.0 --effort high \
  --task-id muse-worker-preview --mode read-only \
  --cwd "$MUSE_WORKTREE" --prompt-file "$PUBLIC_PROMPT" --dry-run
```

Both live and preview planning validate the nonce and dispatch path before
resolution, reject symlink components and use the existing scratch-lease
validator. Native version probes use the shared sanitizer's non-secret
allowlists, without resolving GitHub credentials or copying Git configuration.
These environment checks do not establish credential-file isolation.

The adapter accepts the installed Muse CLI without an exact version or version
range. It records the observed `muse --version` string and the resolved binary's
SHA-256 in the invocation plan and validated task companion. Compatibility is
checked through the native envelope's `schema_version`, `payload_schema_version`,
events, model, session, run, workspace and permission bindings. Unknown schemas
fail closed with `muse_event_schema_unknown` and the observed CLI version.
Inspect `muse exec --help` with auto-update disabled for supported controls.
The [native settings and
launch contract](https://dev.meta.ai/docs/muse-code/configuration) describes
per-run overrides. The [permission contract](https://dev.meta.ai/docs/muse-code/permissions)
distinguishes profiles, approvals and filesystem enforcement.
The shared runner enforces the existing delegate timeout. A task budget may
supply `max_model_steps` and `max_tool_output_bytes` through `tool_config`; the
adapter passes them as `--max-model-steps` and `--max-tool-output-bytes`.
Steps must be positive integers. Tool-output bytes must be zero or an integer
of at least nine, as documented by CLI help. Absent values retain native CLI
defaults; the adapter does not invent budget values. Delegate's worker config
must carry any per-task values to planning. These controls accompany workspace
confinement, declared permission profiles and the sanitized environment.
Steps, tool-output bytes and timeouts are not generation-token caps. An
aggregate-generation-token cap is not an execution prerequisite. Actual
consumption comes from the validated stream and the existing durable writer.

## Interpret completion evidence

Muse exec emits native JSONL records. The MSP schema export describes a
different protocol. The adapter requires a single fresh session/run, the pinned
workspace, a completed terminal and a matching run-scoped `run.usage` record.
Per-stream sequences must be contiguous from one. Every accepted event binds
to the command; task lifecycle events also bind to a linked task and its
observed lifecycle order. These checks describe the preserved exec envelope,
not an MSP schema or proof that a side effect was authorized.
Missing, malformed, duplicate, foreign, failed or ambiguous evidence refuses
success. Human stderr and model/tool prose cannot supply usage or a terminal.

Usage must name the requested model, contain positive total token usage, count
every call as completed and exclude child usage. Input plus output gives the
normalized token total. Cached tokens are part of input; reasoning tokens are
part of output in the validated CLI usage contract. The
[provider token-counting documentation](https://dev.meta.ai/docs/token-counting)
describes preflight context counts, not proof of these CLI generation fields.
Native usage model labels describe CLI accounting;
they do not independently attest a provider model version. Tool-call telemetry
remains unknown until its native event contract is qualified. Effective
permission and backend-model attestation remain unknown: neither the launch
profile nor the usage model label supplies them. A fully validated stream
returns `ok=True`, its exact terminal answer, provider session and input-plus-output
tokens. This is usable transport completion, not semantic correctness or native
qualification. Unknown events and asserted MSP-style attestations still refuse.

One immutable typed `MuseRunEvidence` companion supplies the `muse_run`
projection in the existing usage record, `Result.usage_record` and task record.
It binds the trusted task/nonce to native session/run IDs, CLI version and
binary digest, prompt digest, workspace match, declared mode/profile/toolset
and validated counters. It records the requested selector separately from the
CLI usage model. `observed_model` stays null, `identity_state` and
`effective_permissions` stay `unknown`. No raw workspace or answer appears in
the companion. Its `receipt_ref` and SHA-256 identify the same evidence in each
mirror; a task mirror is not another consumption event. Runtime session/run IDs
remain distinct from provider session/run IDs.

The producer stores the validated, locally computed CLI and prompt SHA-256
digests as immutable bytes. Its JSON projection represents `cli_sha256`,
`prompt_sha256` and `receipt_sha256` as arrays of exactly 32 integers in
the range 0 through 255, in digest byte order. For any of these fields,
`bytes(value).hex()` reconstructs the full hexadecimal digest. This is the
lossless byte representation of a [hashlib digest](https://docs.python.org/3/library/hashlib.html#hashlib.hash.digest).
It contains no source bytes, prompt text or provider secret.

`receipt_sha256` hashes the UTF-8 encoding of
`json.dumps(fields, sort_keys=True, separators=(",", ":"))`, with Python's
default `ensure_ascii=True`. Here `fields` is the projected companion without
`receipt_ref` and `receipt_sha256`, including both launch digest arrays.
The launch digests come only from the trusted invocation plan after validation;
provider strings cannot supply them. String fields still pass through normal
sink redaction. The usage and task writers remain unchanged.

The normal delegate checkout and deliverable guards still decide task success.
A later guard failure preserves the private result answer and the validated
usage companion while leaving the task failed. Malformed or incomplete streams
have unknown usage and no companion. The existing usage writer is best-effort;
qualification must read back the matching durable bytes rather than infer
persistence from a returned dictionary.

Transport completion does not prove the answer. Qualification requires one
separately authorized read-only task to read a public tracked fixture pinned by
commit and content digest. Keep its literal expected result outside the prompt.
Compare the exact response, native session/run events, usage and checkout
snapshots. Any mismatch, missing model/workspace/read-only/usage proof, provider
error or guard refusal stops qualification. Do not retry or change providers.

## Remaining qualification

Offline echo runs prove CLI parsing and event shape only. Echo's absent model
identity and zero usage must be refused as model-task evidence. They do not
prove native tool denials, malicious tool-output containment, managed-policy or
plugin precedence, credential-file isolation, or a real Meta completion.
Provider-origin model identity needs an independently qualified native witness
bound to the same invocation/session/run and task/nonce. Effective permissions
need exact-build evidence for policy/defaults, tool denials, workspace and private
scratch boundaries, credential files, and configuration/plugin precedence.
Requested argv, a clean checkout and a correct answer establish none of these
missing predicates. `muse-wonder-1.0` remains unavailable; Spark remains on hold.
Wonder-Full activation permits explicit workers only, with no automatic routing,
fallback, formal-review or driver eligibility.

Before a paid probe, the accountable driver must obtain exact-head independent
critical review, confirm the child environment and runtime telemetry integration,
and resolve these security boundaries. The driver owns admission, the semantic
fixture proof, CI, queue landing and common cleanup. A source push satisfies
only the author milestone. The original genuine read-only task remains 0/1.
Changed critical patch coverage of at least 80%, effective native security, critical
cross-family delta review, current-head CI, merge-queue CI, confirmed merge and
common cleanup remain root-owned until independently proven. The denominator
remains five original acceptance criteria, two model routes, two dry-run
receipts and one genuine read-only task. Source verification cannot close it.
