# Native Muse delegate workers

The `muse` adapter selects `muse-wonder-full-1.0` or `muse-spark-1.3` explicitly.
Both are worker models. Neither has a review, approval, advisory or driver role.
They have no automatic routing seat or fallback mapping. Their catalog hold
records pending qualification.

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
The dry run prints the native argv, workspace, mode and metadata. It makes no
model request. Its temporary prompt file is reaped with the dry-run lease.

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent muse --model muse-wonder-full-1.0 --effort high \
  --task-id muse-worker-preview --mode read-only \
  --cwd "$MUSE_WORKTREE" --prompt-file "$PUBLIC_PROMPT" --dry-run
```

CLI compatibility is pinned in the adapter to the inspected build. Reinspect
`muse --version`, `muse exec --help` and both `muse model-profile show` results
with auto-update disabled when that build changes. The [native settings and
launch contract](https://dev.meta.ai/docs/muse-code/configuration) describes
per-run overrides. The [permission contract](https://dev.meta.ai/docs/muse-code/permissions)
distinguishes profiles, approvals and filesystem enforcement.

## Interpret completion evidence

Muse exec emits native JSONL records. The MSP schema export describes a
different protocol. The adapter requires a single fresh session/run, the pinned
workspace, a completed terminal and a matching run-scoped `run.usage` record.
Missing, malformed, duplicate, foreign, failed or ambiguous evidence refuses
success. Human stderr and model/tool prose cannot supply usage or a terminal.

Usage must name the requested model, contain positive total token usage, count
every call as completed and exclude child usage. Input plus output gives the
normalized token total. Cached tokens are part of input; reasoning tokens are
part of output. The [provider token contract](https://dev.meta.ai/docs/token-counting)
defines those subsets. Native usage model labels describe CLI accounting;
they do not independently attest a provider model version. Tool-call telemetry
remains unknown until its native event contract is qualified.

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

Before a paid probe, the accountable driver must obtain exact-head independent
critical review, confirm the child environment and runtime telemetry integration,
and resolve these security boundaries. The driver owns admission, the semantic
fixture proof, CI, queue landing and common cleanup. A source push satisfies
only the author milestone.
