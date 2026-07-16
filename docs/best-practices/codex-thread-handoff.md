# Fleet Task Rollover and Codex Handoff Runbook

This runbook covers replacement-thread rollover when a Codex, Claude, Gemini,
or orchestrator heartbeat thread approaches the auto-compaction zone.

## Verified Capabilities

Verified locally through 2026-07-15:

- Codex app tools can expose `create_thread`, `list_threads`, `read_thread`,
  `send_message_to_thread`, `set_thread_title`, `set_thread_pinned`,
  `set_thread_archived`, and `automation_update`. Availability is runtime
  dependent and must be checked in the app-capable task.
- Native `read_thread` status is suitable for exact-identity reconciliation,
  but the current response does not provide authoritative pin state. A missing
  pin field is `unknown`, not proof of `unpinned`, so automatic predecessor
  archive remains blocked unless another native app fact supplies it.
- Those app tools are not callable from a repo-local Python subprocess.
  Local automation must therefore generate state, prompts, and guardrails
  without depending on them.
- `$CODEX_HOME/state_5.sqlite` contains a `threads` table plus related
  `thread_dynamic_tools` and job tables. `$CODEX_HOME/session_index.jsonl`
  is a compact local thread index.
- `$CODEX_HOME/automations/` existed but had no `automation.toml` files in
  this audit, only `.run-jitter-salt`.
- `scripts/ai_agent_bridge/_ui_codex.py` already supports sending messages
  to an existing Codex UI thread with `codex exec resume`; it does not create
  a new app thread.
- Monitor state for orchestration is available through `/api/orient` (including
  its read-only `rollovers` identity-candidate projection),
  `/api/delegate/active`, `/api/delegate/tasks`, and `/api/worktrees`.

## Architecture

The handoff system has four separate layers:

- Canonical task identity: the shared `task-identity.v1` envelope and visible-title policy.
- Durable role handoff: repo-tracked state for the role an agent is playing.
- Thread rollover packet: local state for replacing one saturated thread with
  a fresh thread.
- Worker inbox: delegate task state and result excerpts collected from
  `batch_state/tasks/`.

The thread rollover layer uses a lineage-scoped lease, a generated bootstrap
prompt, and a Task Family Manager transition operation:

- Lease state: `.agent/thread-rollovers/<agent>/<lineage-id>/lease.json`
  (gitignored)
- Packet directory:
  `.agent/thread-rollovers/<agent>/<lineage-id>/generation-NNNN/<rollover-id>/`
  (gitignored)
- Native transition plan, binding, events, and receipts:
  `.agent/task-families/<family-id>/operations/<operation-id>/` (gitignored)
- Durable Codex orchestrator handoff:
  `docs/session-state/codex-orchestrator-handoff.md`
- Codex role handoff pointer:
  `docs/session-state/current.orchestrator.md` (thin pointer to the durable
  orchestrator handoff above)
- Other durable agent handoffs: `docs/session-state/current.<agent>.md`
- Compatibility router: `docs/session-state/current.md` (git-tracked; not used
  for normal thread rollover)
- Script: `scripts/orchestration/thread_handoff.py`
- Canonical schema: `agents_extensions/shared/schemas/task-identity.v1.schema.json`
- Canonical contract: `agents_extensions/shared/contracts/task-identity.md`

Agent names are lower-case slugs matching `[a-z][a-z0-9-]*`. The standard
agents are `orchestrator`, `codex`, `claude`, and `gemini`; additional agents
can use the same naming rule.

`docs/session-state/current.md` is git-tracked compatibility state. It may
exist for historical Monitor API compatibility, but it is not the thread
rollover mechanism. Do not write it during context-threshold handoff.

For compatibility, `docs/session-state/current.orchestrator.md` remains as a
thin pointer to `docs/session-state/codex-orchestrator-handoff.md`. Do not put
new detailed orchestrator state in the pointer.

The lease records:

- active orchestrator generation and thread id, when known
- active heartbeat automation id, when known
- replacement generation
- replacement status: `pending_start`, `resumed`, or `started`
- repository, one stream epic, scoped issue and URL when applicable
- immutable semantic title plus readable bounded visible title
- task family, role, predecessor/replacement IDs, lineage/generation, and typed
  terminal goal (`merge`, `deploy`, or `certify`), lifecycle state,
  carrier titles, and migration provenance
- durable title-transition binding, mutation, readback, or honest fallback receipts
- exact source/replacement native IDs and typed `replacement_of` plus
  `rollover_generation_of` relations after native creation
- bootstrap prompt path
- cleanup guard: `old_automation_ready_to_delete`

The cleanup guard is false after `prepare`. It becomes true only after
`confirm-started --new-thread-id ...` succeeds. This keeps the old heartbeat
alive if the replacement thread was not actually started.

## Standard Orchestrator Rollover

Run this from the repo root when the heartbeat thread enters the rollover
zone:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent orchestrator --harness codex-app \
  --active-thread-id <current-thread-id> \
  --stream-epic <one-stream-epic-number> \
  --issue-number <scoped-issue-number> \
  --semantic-title "<specific semantic task title>" \
  --task-family <task-family> \
  --role "<role>" \
  --terminal-goal <merge|deploy|certify> \
  --context-percent 86
```

If the active thread id or automation id is known, include them:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent orchestrator \
  --active-thread-id <current-thread-id> \
  --active-automation-id <old-heartbeat-automation-id> \
  --stream-epic <one-stream-epic-number> \
  --semantic-title "<specific semantic task title>" \
  --task-family <task-family> \
  --terminal-goal <merge|deploy|certify> \
  --context-percent 86
```

This writes the lineage-scoped lease and packet plus an immutable Task Family
Manager transition plan and receipt. Issue-backed visible titles are
`#<issue> — <semantic title>`; otherwise they are
`<task family> — <semantic title>`. Blank and generic labels, UUID-only titles,
and lineage/rollover/generation-only titles are rejected. Legacy identity-less
packets receive a deterministic semantic fallback with migration provenance;
its `terminal_goal: unknown` is reserved for migration and explicit callers
must choose `merge`, `deploy`, or `certify`. Raw runtime identifiers never
become the primary visible title.
The Task Family Manager family remains stable for one lineage generation, while
the operation ID is deterministic for the exact rollover packet. A forced
same-generation packet therefore cannot collide with or rewrite an older
immutable operation.

It does not modify git-tracked handoff files by default.

The generated prompt is the exact replacement-thread bootstrap. The
app-capable path first runs `native-action --action create` and calls native
`create_thread` only when authorized. It must obtain a real `threadId`; a queued
`clientThreadId` is not sufficient to bind identity. It immediately records
the successful native result, then runs `register-created` with the exact
replacement UUID and asks
`native-action --action title` for the exact mutation, calls native
`set_thread_title` only when authorized, records the acknowledgement or
failure, and reconciles native read-back. If an app API is absent, record the
failure and preserve the durable operation for retry rather than creating or
choosing another task by title.

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py native-action \
  --agent orchestrator --lineage-id <lineage-id> \
  --rollover-id <rollover-id> --action create
# After native create_thread returns an exact threadId:
.venv/bin/python scripts/orchestration/thread_handoff.py record-native-result \
  --agent orchestrator --lineage-id <lineage-id> \
  --rollover-id <rollover-id> --action create --succeeded \
  --evidence "create_thread returned exact threadId"
.venv/bin/python scripts/orchestration/thread_handoff.py register-created \
  --agent orchestrator --lineage-id <lineage-id> \
  --rollover-id <rollover-id> \
  --replacement-thread-id <exact-replacement-thread-id> \
  --evidence "native create_thread result"
.venv/bin/python scripts/orchestration/thread_handoff.py native-action \
  --agent orchestrator --lineage-id <lineage-id> \
  --rollover-id <rollover-id> --action title
```

Use the returned exact `arguments` with native `set_thread_title`, then run
`record-native-result --action title --succeeded --evidence "..."` and
`reconcile-native --action title`. For a failed native call, use `--failed
--error "..."`. Always retry through `native-action`; its receipt and read-back
logic prevent duplicate successful mutations. A title acknowledgement without
exact readback does not count as reconciled and cannot unlock resume.
Readback uses raw exact string equality; whitespace is not normalized. A later
failed retry cannot overwrite an already durable acknowledgement or exact
readback receipt.

### Harnesses without native title mutation

When `prepare` reports `native_title_supported: false`, create or bind the
exact replacement through that harness, then persist the carrier fallback:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py bind-replacement \
  --agent <agent> --lineage-id <lineage-id> \
  --rollover-id <rollover-id> \
  --replacement-task-id <exact-replacement-task-id> \
  --evidence "<exact dispatch/harness binding receipt>"
```

The receipt records that native mutation/readback are unsupported and that no
rename was attempted. The same visible title remains in the dispatch record,
brief, lease ledger, inbox/bootstrap, monitor projection, and final receipt.
Do not fabricate `set_thread_title` success. Conversely, if an adapter declares
native support but acknowledgement or exact readback fails, fail closed rather
than silently downgrading to this fallback.

The bootstrap starts with a checklist that is deliberately hard to skip:

- repo root + `git status --short --branch`
- local `.agent/<agent>-thread-handoff.md`
- `/api/orient?fresh=true`
- `.venv/bin/python scripts/orchestration/issue_stream_audit.py --json` when
  the GitHub issue subsection errors or times out
- open PR list
- current worktree hygiene via `git worktree list`

The generated bootstrap also tells the replacement thread to read the
orchestrator worker inbox:

```bash
.venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results
```

That inbox summarizes delegate task state and result excerpts so the new
thread does not have to rediscover raw files under `batch_state/tasks/`.

The replacement thread reads both durable role state and thread rollover state:

- durable role state:
  `docs/session-state/codex-orchestrator-handoff.md`
- local thread rollover packet:
  the exact `handoff_file` under
  `.agent/thread-rollovers/orchestrator/<lineage-id>/generation-NNNN/<rollover-id>/`

After the replacement thread is visibly running, confirm it:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --agent orchestrator \
  --lineage-id <lineage-id> \
  --rollover-id <rollover-id> \
  --new-thread-id <replacement-thread-id> \
  --canary-proof <reserved-canary-proof-path> \
  --strict-probe <reserved-strict-probe-path> \
  --strict-verdict <reserved-strict-verdict-path>
```

Only if the output shows `"old_automation_ready_to_delete": true` may the old
heartbeat automation be deleted or paused through the Codex app
`automation_update` tool. This existing proof gate is independent from and not
weakened by task archival.

After confirmation, inspect the exact `predecessor_thread_id` through the app.
Run `native-action --action archive` with authoritative status and pin facts.
The command authorizes native `set_thread_archived` only when the exact bound
predecessor is idle and unpinned, the replacement title is reconciled, and the
canary plus strict 10/10 recall and cleanup proofs all pass. Pinned, running,
ambiguous, unrelated, or unconfirmed tasks are preserved. Unknown status or pin
state is a durable blocker. Record and reconcile an authorized archive exactly
as for title.

## Non-Orchestrator Agent Rollover

Agents other than the orchestrator write only their own handoff by default:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent <agent> --harness <harness> \
  --active-thread-id <exact-active-task-id> \
  --stream-epic <one-stream-epic-number> \
  --semantic-title "<specific semantic task title>" \
  --task-family <task-family> \
  --terminal-goal <merge|deploy|certify> \
  --context-percent 86
```

That writes only the Codex lineage-scoped runtime packet and Task Family
Manager operation. It does not modify `docs/session-state/current.md` and does
not touch durable role handoff files.

`--write-current` is deprecated and rejected unless paired with
`--allow-git-router`. Use that pair only for an explicitly approved
compatibility-router update, never for thread rollover. The router must stay
tiny and must keep `Latest-Brief:` plus the `Agent-Handoff:` mapping.

Confirm the replacement with the same agent name:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --agent codex \
  --lineage-id <lineage-id> \
  --rollover-id <rollover-id> \
  --new-thread-id <replacement-thread-id> \
  --canary-proof <reserved-canary-proof-path> \
  --strict-probe <reserved-strict-probe-path> \
  --strict-verdict <reserved-strict-verdict-path>
```

## Safety Checks

Check the lease at any time:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py check \
  --agent <agent> --lineage-id <lineage-id>
```

Warnings mean the old heartbeat automation should stay active. Common
warnings:

- replacement is still `pending_start`
- pending replacement is stale
- active generation has not been seen recently
- context estimate is at or above the threshold
- cleanup says ready but no replacement thread id is recorded
- lease state file is unreadable or corrupt

`detect` never collapses multiple live packets into a generic error. Its
`MULTIPLE_LIVE_PENDING_ROLLOVERS` diagnostic lists each candidate's semantic
title, issue, lineage/generation, rollover and predecessor/replacement IDs,
creation/update times, confirmation states, and safe exact-ID resolution. Do
not resolve candidates by directory order, age, title similarity, or automatic
supersession.

`audit` includes the same read-only `task_identity` snapshot. Monitor and
orientation integrations consume
`scripts.orchestration.thread_handoff.rollover_identity_snapshot(...)` so the
API view uses this envelope instead of reconstructing titles from lineage IDs.

`prepare` and `confirm-started` refuse to overwrite an unreadable lease file.
Inspect or restore the file first. If the operator intentionally wants to
discard the corrupt lease and start a new one, run:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent orchestrator \
  --force-reset-state \
  --context-percent 86
```

Dry-run without writing files:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent codex --dry-run
```

### Superseded native-intent recovery

`prepare --force-new-replacement` is fail closed. It supersedes only the exact
prior intent when its receipt is pristine and no native create was authorized
or attempted. The successor plan is durable before the live lease can expose
it. Prepare, legacy repair, and create authorization serialize through the same
blocking cross-process `fcntl.flock` lineage lock, so competing mutators cannot
publish different successors. A rejected first prepare may leave only this
gitignored lock file and its lineage directory; detection considers `lease.json`
files only. The predecessor immutable plan is never rewritten: its operation gains an
immutable `rollover-supersession.json`, skipped planned actions, a blocked
`superseded_before_native_create` state, and the exact successor IDs. Binding,
actual actions, successful or failed acknowledgements, authorization, and
ambiguous state all preserve the old packet and block forced replacement.

Older deployments could create a same-generation lease/receipt mismatch. When
the current lease points to a pristine legacy operation whose immutable plan
contains a different rollover ID, native creation is forbidden. After verifying
through the app and receipt that `create_thread` was never called, run:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py repair-native-intent \
  --agent codex \
  --lineage-id <lineage-id> \
  --rollover-id <current-rollover-id> \
  --evidence "App stopped before create_thread; exact receipt and binding are pristine."
```

This command performs no Codex app mutation. It creates the correct
packet-specific transition, receipts the exact untouched legacy operation, and
updates the lease last while preserving the bootstrap, checkout binding, canary,
and cleanup=false guard. Retries must use the same successor and evidence. Do
not manually edit or delete the lease, plan, receipt, or operation directory.
After a successful repair, restart at `native-action --action create`.

## Fresh Codex App Task/Restart Smoke

The repository E2E suite exercises the process, hook, and real-worktree seams,
but it cannot create a Codex app task. Run this smoke from the app before
calling a restart change accepted. A fresh replacement is a new task identity;
do not fork, continue, or run `codex exec resume` on provider conversation
history.

Before opening the fresh project task, deploy the canonical checkout and
prepare the packet:

```bash
set -euo pipefail
canonical=$(git rev-parse --show-toplevel)
evidence="/tmp/rollover-smoke-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$evidence"
cd "$canonical"
npm run agents:deploy | tee "$evidence/canonical-deploy.txt"
test -z "$(git status --porcelain)"
source_head=$(git rev-parse HEAD)
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent codex --harness codex-app \
  --active-thread-id <predecessor-task-id> \
  --active-automation-id <predecessor-automation-id> \
  --stream-epic <one-stream-epic-number> \
  --issue-number <scoped-issue-number> \
  --semantic-title "Verify fleet task rollover continuity" \
  --task-family infra-harness \
  --role smoke-verifier \
  --terminal-goal certify \
  | tee "$evidence/prepare.json"
lineage_id=$(jq -r .lineage_id "$evidence/prepare.json")
rollover_id=$(jq -r .rollover_id "$evidence/prepare.json")
lease_rel=$(jq -r .state_file "$evidence/prepare.json")
lease="$canonical/$lease_rel"
.venv/bin/python scripts/orchestration/thread_handoff.py native-action \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" --action create \
  | tee "$evidence/create-action.json"
test "$(jq -r .needs_native_action "$evidence/create-action.json")" = true
```

Create one genuinely fresh Codex app project task and record its new task id
and app-created worktree path. Do not fork or continue the predecessor task.
If the app supports a worktree setup command, configure the bootstrap helper
below to run before the task first opens. Otherwise use the task's first turn
only to run the helper. That first SessionStart is not acceptance evidence.

```bash
fresh=<absolute-app-worktree-path>
initial_replacement_task_id=<fresh-task-id>
printf '%s\n' "$initial_replacement_task_id" \
  > "$evidence/initial-replacement-task-id.txt"
.venv/bin/python scripts/orchestration/thread_handoff.py record-native-result \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" --action create --succeeded \
  --evidence "smoke create_thread returned $initial_replacement_task_id"
.venv/bin/python scripts/orchestration/thread_handoff.py register-created \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" \
  --replacement-thread-id "$initial_replacement_task_id" \
  --evidence "fresh smoke create_thread result" \
  | tee "$evidence/register-created.json"
.venv/bin/python scripts/orchestration/thread_handoff.py native-action \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" --action title \
  | tee "$evidence/title-action.json"
# The app-capable agent calls set_thread_title with title-action.json's exact
# arguments, then persists its acknowledgement before read-back.
.venv/bin/python scripts/orchestration/thread_handoff.py record-native-result \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" --action title --succeeded \
  --evidence "smoke set_thread_title acknowledgement"
.venv/bin/python scripts/orchestration/thread_handoff.py reconcile-native \
  --agent codex --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" --action title \
  | tee "$evidence/title-reconcile.json"
bash "$fresh/scripts/lib/thread_rollover_link.sh" "$canonical" "$fresh" \
  | tee "$evidence/fresh-bootstrap.txt"
git -C "$canonical" worktree list | tee "$evidence/worktrees.txt"
readlink "$fresh/.agent/thread-rollovers" | tee "$evidence/rollover-link.txt"
test -f "$fresh/.codex/hooks.json"
test -x "$fresh/.codex/hooks/session-setup.sh"
test "$(readlink "$fresh/.agent/thread-rollovers")" = \
  "$canonical/.agent/thread-rollovers"
test "$(git -C "$fresh" rev-parse HEAD)" = "$source_head"
test -z "$(git -C "$fresh" status --porcelain)"
```

For this smoke, do not pre-export `CODEX_CANONICAL_REPO_ROOT`. The reopened
task's automatic SessionStart output must name the prepared `lineage_id` and
`rollover_id` and show `PENDING THREAD ROLLOVER DETECTED` without the prompt
pre-supplying either id. Sending another message or archiving and unarchiving
the task does not restart its agent session and is not acceptance evidence.

With the Codex app's managed worktree sandbox, the fresh worktree can read the
canonical packet through the link above but cannot update the canonical lease;
`resume` fails closed with `Operation not permitted`. Use the app's task handoff
operation to move that same logical fresh task to the canonical checkout and
send a bootstrap-only follow-up. Record both the initial fresh task id and the
handoff destination task id because the app may allocate a new id at this
boundary. The destination's automatic SessionStart output is the restart
evidence. It must show the prepared pending packet before any claim command.

The canonical checkout must still be clean and at `source_head`; the app may
temporarily place it on the fresh task's dedicated branch. From that canonical
destination, claim only the automatically detected packet:

```bash
claim_task_id=<handoff-destination-task-id>
cd "$canonical"
test "$(git rev-parse HEAD)" = "$source_head"
test -z "$(git status --porcelain)"
.venv/bin/python scripts/orchestration/thread_handoff.py resume \
  --agent codex \
  --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" \
  --replacement-thread-id "$claim_task_id" \
  | tee "$evidence/resume.json"
```

Read the packet and durable role handoff named by SessionStart. Write the ten
truthful semantic anchors to the lease's reserved snapshot path. Answer the
generated questions from restored context; do not read the answer-bearing
probe to manufacture recall answers.

```bash
snapshot_rel=$(jq -r .replacement.semantic_snapshot_path "$lease")
probe_rel=$(jq -r .replacement.strict_probe_path "$lease")
questions_rel=$(jq -r .replacement.strict_questions_path "$lease")
answers_rel=$(jq -r .replacement.strict_answers_path "$lease")
verdict_rel=$(jq -r .replacement.strict_verdict_path "$lease")
proof_rel=$(jq -r .replacement.canary_proof_path "$lease")
challenge=$(jq -r .replacement.canary_challenge "$lease")

# The canonical destination writes "$canonical/$snapshot_rel" from the packet.
.venv/bin/python scripts/context_canary.py mint \
  --snapshot "$canonical/$snapshot_rel" --out "$canonical/$probe_rel"
.venv/bin/python scripts/context_canary.py questions \
  --probe "$canonical/$probe_rel" --out "$canonical/$questions_rel"
# The canonical destination now writes {"<question-id>": "<recalled-answer>"} to
# "$canonical/$answers_rel" without opening the probe.
.venv/bin/python scripts/context_canary.py score \
  --probe "$canonical/$probe_rel" \
  --answers "$canonical/$answers_rel" \
  --expected-lineage-id "$lineage_id" \
  --expected-rollover-id "$rollover_id" \
  --verdict "$canonical/$verdict_rel" \
  | tee "$evidence/strict-score.txt"
.venv/bin/python scripts/orchestration/thread_handoff_canary.py \
  --rollover-id "$rollover_id" \
  --replacement-thread-id "$claim_task_id" \
  --challenge "$challenge" \
  --proof-file "$canonical/$proof_rel" \
  | tee "$evidence/canary.json"
test "$(git rev-parse HEAD)" = "$source_head"
test -z "$(git status --porcelain)"
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --agent codex \
  --lineage-id "$lineage_id" \
  --rollover-id "$rollover_id" \
  --new-thread-id "$claim_task_id" \
  --canary-proof "$canonical/$proof_rel" \
  --strict-probe "$canonical/$probe_rel" \
  --strict-verdict "$canonical/$verdict_rel" \
  | tee "$evidence/confirm.json"
```

The smoke passes only when the score says `10/10`, the canary says `PASS`, the
logical fresh task differs from the predecessor, and `confirm.json` says
`"old_automation_ready_to_delete": true`. Record the predecessor id, initial
fresh task id, canonical claim task id, title, both checkout paths, and every
automatic SessionStart result. After confirmation, use the app handoff
operation to return the logical task to its app worktree; verify the canonical
checkout is back on `main`, both checkouts are clean, and all tracked files are
unchanged. If the return handoff fails, do not force it or delete either
worktree. First require both checkouts to remain clean and at `source_head`, then
restore the canonical checkout with `git -C "$canonical" switch main`. Treat an
index lock as live unless `lsof` proves no process owns it; remove only a proven
stale lock before switching. Stop for manual recovery if either checkout is
dirty or any Git process still owns the lock. Archive the exact confirmed
predecessor only through the authorized native archive sequence above. Preserve
every task whose status, pin state, identity, or relation is unknown, and remove
only clean app worktrees whose exact ownership is proven.

Keep all captured evidence under `/tmp/rollover-smoke-*`; the packet itself
stays under gitignored `.agent/thread-rollovers/`. Delete or pause the
predecessor automation only after all four checks pass. `prepare`, `resume`,
and `confirm-started` fail closed if their invoking checkout is dirty, is at a
different HEAD, or if a live pending/resumed lease lacks the source-checkout
binding.

## Worker Run Inbox

Use `scripts/orchestration/orchestrator_control.py` when worker dispatch state
must survive a thread rollover. It keeps a gitignored run ledger under
`batch_state/orchestrator-runs/` and reads delegate state from
`batch_state/tasks/`.

Create a run:

```bash
.venv/bin/python scripts/orchestration/orchestrator_control.py start-run \
  --run-id a1-gate-policy \
  --description "A1 gate policy repair"
```

Dispatch a worker and record it in that run:

```bash
.venv/bin/python scripts/orchestration/orchestrator_control.py dispatch \
  --run-id a1-gate-policy \
  --task-id a1-gate-policy-worker \
  --agent codex \
  --mode danger \
  --worktree \
  --prompt-file /tmp/a1-gate-policy-worker.md
```

Attach an already-started delegate task:

```bash
.venv/bin/python scripts/orchestration/orchestrator_control.py add-task \
  --run-id a1-gate-policy \
  --task-id a1-existing-worker
```

Read the worker inbox from any current or replacement thread:

```bash
.venv/bin/python scripts/orchestration/orchestrator_control.py inbox \
  --run-id a1-gate-policy \
  --include-results
```

Without `--run-id`, `inbox` shows recent delegate tasks. The markdown output is
intended for humans; pass `--format json` when another tool needs a structured
packet.

Audit local Codex metadata:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py audit
```

Include live Monitor API state in the audit:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py audit --include-monitor
```

## Heartbeat Behavior

At 75 percent context, run `prepare --dry-run` to verify the packet renders.

At 82 percent context or higher, run `prepare --agent <name>` and start the
replacement thread using `.agent/<name>-thread-bootstrap.md`. If the Codex app
thread-management tools are available, create/fork/send the continuation with
that bootstrap prompt. Otherwise ask the user to start a fresh thread with the
same prompt. Keep the old heartbeat active until `confirm-started --agent
<name>` records the replacement thread id.

At 90 percent context or higher, stop non-handoff work. The current thread
should only write the handoff packet, start or prompt for the replacement
thread, and preserve the old automation until confirmation.
