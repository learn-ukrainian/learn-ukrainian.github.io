# Worktree cleanup

This runbook covers immediate post-merge cleanup and the local Linux systemd and macOS launchd Git
hygiene backstops for both Learn Ukrainian repositories.

## Shared Python environment

The primary checkout's `.venv` is the only project virtual environment.
Dispatch worktrees must never create, copy, symlink, activate, or use a local
`.venv`. From any linked worktree, derive and invoke the absolute primary
interpreter instead:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" -m pytest tests/dispatcher/test_core.py
```

Do not substitute `python`, `.venv/bin/python`, or `python -m venv .venv`.
The dispatch launcher records a warning when a local `.venv` is already present;
do not delete it while a task might be active. A local `.venv` is not
disposable residue: the dispatcher keeps a worktree that holds one at
settlement (`dirty`, below).

## Shared node_modules (npm shim)

Dispatch worktrees receive `node_modules` and `site/node_modules` as symlinks into the primary checkout. The agent runtime provides an `npm` (and `npx`) shim that intercepts destructive commands to protect the shared tree.

Every npm/npx call through the shim runs with umask 022 to prevent the tree from becoming group-writable. The refusal message from the ACP adapter prints the exact corrective command class.

## Cleanup at enqueue

The shared publisher returns after authenticated enqueue or already-queued
reconciliation and the existing publication gates. Neither path runs the global
cleanup inventory or common reaper, creates a cleanup receipt, or emits an
`enqueue-cleanup` line. Known enqueue success keeps its return code and raw
transport output. Already-queued unchanged heads return without another enqueue.
The keeper uses the same publisher path. Failed or unknown publication never
authorizes cleanup.

The dispatcher's settlement removal and the post-merge closeout own cleanup and
its durable receipts. All common ownership, liveness,
preservation and branch guards still apply. Publisher queue success does not
prove cleanup complete. Retained, pending or unavailable cleanup blocks full
delivery; it does not authorize another enqueue. Post-merge common closeout
remains mandatory.
A repair starts in a fresh managed worktree from the pushed branch.
Local branch removal uses supported safe cleanup only after its tree is gone
and publication is proven. Remote branches remain until `MERGED`.

## Safety contract

Every Git-based worktree removal preserves ignored output at the sole raw
`git worktree remove` boundary in `scripts/orchestration/worktree_claims.py`,
using `scripts/fleet/ignored_task_output.py`. ACP execution teardown, data-tier
cleanup, sibling Git maintenance, task-family cleanup, and the removal CLI all
inherit this guard. Preservation runs once, after ownership/claim checks and
before deletion. A preservation failure returns a typed skipped/refusal result
and leaves the directory intact. The dispatcher's settlement
(`scripts/dispatcher/git.py` `settle_worktree`) removes through the same
chokepoint: ignored output is inventoried, and untracked files are copied into
`batch_state/preserved/<task>/` (receipt `branch_holder_archive`) before a forced
removal; uncommitted tracked changes keep the tree. `branch_sweep` deletes branch refs only. The legacy temp leak
sweep and review temporary-tree cleanup refuse a candidate containing a linked
worktree's `.git` file or a symlinked `.git` anywhere in its directory tree (or
an unreadable scan).
Matching scratch names do not permit removing linked worktrees outside the
shared guard; ordinary disposable clones with their own `.git` directory
retain their existing scratch-cleanup behavior.

### Removal path audit (#9645)

| Entry point / primitive | Disposition |
| --- | --- |
| `worktree_claims.git_worktree_remove`: raw Git argv | Preserves once before deletion; failures return a refusal. |
| `dispatcher.git.settle_worktree`: task settlement | Shared locked remover under the dispatcher's worktree lock, with the provider proven gone, no uncommitted tracked change, and (a write task that committed) its HEAD published; untracked files are copied before a forced removal. |
| `_acp_execution._remove_runtime_worktree`: context teardown and dead-runtime sweep | Shared locked remover; no-checkout teardown inventories all untracked non-cache files, even without ignore rules. Dead-runtime sweep retains unexpected files. |
| `data_tier.remove_test_worktree`: stale and final cleanup | Shared locked remover. |
| `sibling_git.worktree_remove` | Shared locked remover; preservation uses the public control plane. |
| `task_family.git_safety.remove_unclaimed_worktree`: executor cleanup | Shared locked remover. |
| `worktree_claims remove`, `wt.sh`, RB2 failed-dispatch cleanup | Guarded CLI, then shared locked remover. |
| `tmp_leak_sweep._remove_path`: `shutil.rmtree` | Refuses linked worktree markers, including nested checkouts and unreadable scans. |
| `review.isolation._remove_review_temp_tree`: `shutil.rmtree` | Repairs review permissions without following symlinks, then refuses linked worktree markers, nested checkouts and unreadable scans before deletion. Root symlinks are refused; the orphan sweep reports refusals as errors. Plain temporary trees and disposable clones remain eligible. |

The remaining recursive deletion and `rmdir` hits operate on runtime leases,
review snapshot/neutral metadata, capture records, generated staging/output,
owned hook metadata, empty deployed mirror directories, or audit fixtures.
They are not registered worktree-root removers. In particular,
`audit/test_handoff_identity.sh` removes a mock rollover directory, and
`review/snapshot.py` only calls `rmdir` on an empty extracted overlay member.

The guard inventories all Git-ignored regular files, including `.cache/`
outputs never named in a response. No-checkout runtimes have an empty index and
no on-disk ignore rules, so the guard inventories all untracked non-cache files.
All such output is preserved, including files from earlier attempts in a
reused checkout and files written before the current task started. Start values
(old, missing, malformed, naive, or future) never affect file selection. There
is no time cutoff. Baselines label provenance; canonical record binding and
retention intent guard removal: the record's `worktree_path` (or fallback `cwd`) must
resolve to the checkout being removed. Hot then archived records are checked
for that binding; task ids alone never bind records.
Output retains its relative paths under
`batch_state/preserved/<task-id>/<attempt-nonce>/`. A manifest binds each copy
to its resolved worktree and a digest of the file list and bytes. Retries reuse
an existing copy only after verifying its complete file list and bytes again;
changed output gets a new attempt directory, keeping earlier copies intact.
Missing or ambiguous canonical task attribution retains the tree with an Infra
owner and a concrete next condition. No fallback task identity authorizes
removal. Empty files are included. Copy verification checks size and SHA-256,
refuses conflicting evidence, and independently retrieves the complete copy
before removal.

Known tool directories (`__pycache__`, `.pytest_cache`, `.ruff_cache`,
`.mypy_cache`, `.pytest_breadcrumbs`, `.astro`,
`.hypothesis`, `.tox`, `.nox`, and Git metadata) are excluded. `.cache`
itself is deliberately not a tool-cache exemption. Shared state and verified
provisioned database links survive outside the worktree and are never copied.
Task output placed in an excluded cache remains disposable. Real `.venv`
directories retain the normal output rules. A real ignored `node_modules`
directory is regenerable only with a local regular, tracked sibling
`package-lock.json`. Verified provisioned links are disposable without following
their targets. `worktree_artifacts.is_disposable_path` and
`regenerable_output.is_regenerable_ignored_path` supply the shared taxonomy.

The reviewed site build patterns live in `regenerable_output.SITE_BUILD_OUTPUT_PATTERNS`.
They exclude tracked files, symlink components, database files and unknown output.
`RELEASE_OUTPUT_PATTERNS` adds two conditional classes (#9828, #10061):

- `site/src/data/lexicon-manifest.json`, reproduced by
  `node site/scripts/hydrate-manifest.mjs` from `lexicon-manifest.pointer.json`.
- `site/public/lexicon/practice-{kind}.{level}.json`, for the hydrator's enumerated
  kinds and levels, reproduced by `node site/scripts/hydrate-practice-deck.mjs`
  from `lexicon-practice-deck.pointer.json`.

Each conditional file must be ignored, untracked, a local regular file without
symlink components, and match its committed pointer's byte count and SHA-256.
The pointer and hydrator must be tracked, committed and clean in both index and
worktree. Hashing streams through directory descriptors without following links.
Missing proof, richer unpublished content, `.tmp`, staged manifests and gzip
copies retain the normal preservation and cap rules. No filename-only exemption
applies to these release files. `data/atlas.db` and its sidecars remain task output;
their names and an `atlas:build-db` command do not prove their local provenance.

Task-record inventory retries one complete scan after a read failure, logging
the retry. A vanished task filename must have a visible archive counterpart;
persistent unreadable records or unaccounted disappearance still refuse removal.

The issue-stream audit's refresh sidecars, `batch_state/issue_stream_audit_refresh.json`
and `batch_state/issue_stream_audit_refresh.lock`, are regenerable tool state, not
task output (#10519). The audit now writes them under the primary checkout, but
older runs left them in the checkout they ran from. Exactly these two root-level
names are exempt from inventory and preservation
(`regenerable_output.AUDIT_REFRESH_STATE_FILES`), so a clean worktree holding
only them no longer needs a task record to be removed. The exemption needs an
untracked regular file of at most 4 KiB with no symlink component; any other
name (including `batch_state/issue_stream_audit.json`, nested copies and
`.tmp` leftovers) or a larger file keeps the normal attribution and
preservation rules. An unrelated file beside them retains the tree only when
attribution is missing; attributed output can be preserved and the tree removed.

Automatic preservation is capped at **256 MiB per worktree**, bounding disk
duplication while accommodating text output and small reports. Above the cap,
no partial copy is attempted and the worktree is retained for its owner's
disposition. Inventory, copy, byte-verification, or task-record write failures
also retain it, as do manifest or canonical task-receipt write failures. Task terminal
status never changes preservation eligibility. Existing ownership and liveness
gates still apply before preservation and removal.
Existing task records and removal/closeout receipts report `preserved_artifacts`
with `count`, `bytes`, repository-relative `location`, `worktree_sha256`,
`content_sha256`, `retrieval_proof_sha256`, `reused`, and per-path `path`,
`size`, `sha256` and `class`. Receipts contain no contents or absolute home
paths. Each retained receipt includes `owner` and `next_condition`; disposition
is `retained`, `retrieved`, or `released`.

Creation captures `ignored_output_baseline` in the existing task record while
`delegate.worktree_lock` remains held through record publication, before worker
spawn. It binds path/size/digest entries to task ID, run nonce and directory
identity. Unchanged baseline entries are `pre_existing`; new or modified entries
are `task_created`. Missing, malformed, reused or identity-mismatched baselines
are `unknown_baseline`. All three classes are preserved equally: no timestamp
or baseline excludes output.

Every guarded removal honors canonical `keep_worktree` even when Git is clean.
The gate discovers the bound hot/archive task record itself; caller-supplied
records cannot hide intent. A kept tree may acquire a passing retrieval receipt
but remains retained. No command releases retention intent any more: the
post-task reaper's `--release-retention` command was deleted with it
(FR-01b). Every guarded remover, `worktree_claims remove` included, still
refuses a kept tree. The owner retrieves the output; releasing the tree itself
has no supported command and is an Infra-owned residual.

Continuation rounds keep the checkout's creator as its owner (#10008). Even
without retention intent, attribution requires exactly one creator and settled
reused successors on the same resolved checkout and branch. With no retention
intent, a positively verified detached HEAD may use the common recorded branch;
an unknown branch probe or conflicting recorded branches still refuses attribution.
`session_env` attribution is accepted through those recorded bindings; it does
not grant a successor ownership. A terminal timestamped `--force-new` archive
is excluded from creator attribution only when its same-task canonical
replacement matches the checkout, has a different run nonce, and a current
creator remains. Ordinary archives,
missing replacement evidence, two current creators, or a running successor
remain ambiguous.
All matching records, including excluded history, remain visible to retention
checks and verified receipt release. A historical `keep_worktree` claim must
be retrieved; it is never dropped by attribution filtering.
In a continuation cohort, failed-preparation records with null PID, base SHA
and branch do not prove that no checkout was created: the failure writer also
runs after add attempts and can snapshot an existing HEAD. Without explicit
no-creation evidence they remain ambiguous and never grant ownership.
Infra owns this attribution residual.

Task records written by the retired reaper may carry `worktree_reap_proof`
(`merged-reuse-reap.v1`) for a keep-false continuation cohort. Preservation and
lifecycle recovery still read and verify that proof against current identities
(`scripts/orchestration/worktree_git.py`); nothing writes new ones. The proof
does not release retention intent.
A switched-branch proof identifies the checkout using Git's raw common-directory
and configured-origin output, then checks Git's porcelain registration list in
the primary. The candidate must be inside that primary's cleanup root. The
resolver never reads Git pointer files or normalizes identity output. Unknown
identity refuses the proof before any pull-request query or removal; malformed
origins retain their checkout without aborting the sweep.
This extra owner proof applies only to cohorts of at least two current records;
single-record trees retain their existing behavior. Ignored non-cache bytes
still require verified preservation and retrieval, and merged-head proof never
clears retention intent.

Infra owns legacy-tree and disk-use residuals and retention of
`batch_state/preserved/`. This change adds no automatic deletion policy for
preserved copies. Off-repository historical recovery remains unknown until the
open-model-data owner verifies it.

Cleanup is fail-closed. At settlement the dispatcher keeps the task's worktree
and records `worktree_disposition: retained` with one of these reasons:

- `borrowed_worktree`: the task ran in a `--cwd` it did not create;
- `dirty`: a tracked file has uncommitted changes (untracked and ignored
  files never keep the tree; the chokepoint preserves them);
- `unknown`: Git state or the canonical remote could not be read;
- `unpublished` or `remote_mismatch`: a write task that committed has a HEAD
  that is not on the canonical remote recorded at dispatch (its branch tip, a
  pull-request head, or already in main); a task with no commits needs no proof;
- `borrowed_by_live_task`: another task's provider may still use the tree;
- `provider_processes_alive` or `provider_liveness_unknown`: the provider's
  process tree is not proven gone after settlement's bounded wait
  (`worker.SETTLE_PATIENCE`, 10 seconds);
- `removal_refused`: the `worktree_claims` chokepoint refused (lock busy,
  another unfinished record claims the tree, or artifact preservation failed);
  `worktree_disposition_detail` carries its reason.

A failed removal is recorded as `error` (`worktree_remove_failed` with
`worktree_disposition_detail`, or `settlement_failed`). The next dispatch retries
settlement, in a fresh process, for every reason except `borrowed_worktree` and
`dirty` (`worker.RETRY_REASONS`, `worker.settle_left_worktrees`); a `dirty` tree
stays for its owner. The guarded removers in `worktree_claims` also refuse while an
unfinished task record names the checkout, including a non-terminal review
attempt that reads from it. The task record claims the deepest registered linked checkout containing each of these inputs, including subdirectories and symlink spellings: its `review_contract.input_root`, and every `review_input_paths` entry, namely the attempt manifest (dispatch resolves its path once at admission, so every later read and the worker use the symlink target, never the supplied spelling) and the worker's own code checkout (it runs from there for the whole attempt). A formal attempt takes no output schema (`--review-attempt` with `--output-schema` is refused). Inputs in the primary checkout, or outside any registered checkout, claim nothing. Before it reserves the attempt id, dispatch refuses a review contract without an `input_root`, and refuses the attempt when the fleet scratch root (`LU_SCRATCH_ROOT`, which holds the worker's runtime tmp lease) lies inside a registered linked checkout (`review_scratch_root_in_worktree`). It holds the shared removal lock of every claimed checkout during input preparation until the task record publishes the claims. Only a terminal task status ends the protection; an owner or settled-claim exemption does not, and a record with an unreadable or malformed claim, or an unavailable worktree registration, refuses removal rather than releasing it.

### Finished branch-holder scratch hand-off (#10227, first slice)

Dispatch/review branch attachment may release a terminal, unambiguously bound
holder with only untracked `*.orig`, `*.patch`, or `pytest_out.txt` scratch.
The closed classifier lives in `scripts/fleet/regenerable_output.py`;
these patterns do not become auto-finalize exclusions. Each eligible file is
regular, has one hard link, and is at most 256 MiB. An `.orig` stem must be a
tracked path. A filesystem scan also rejects special files that Git omits.
Tracked changes (including concealed index-flag edits), submodules, nested
repositories, arbitrary links and any other untracked output refuse the entire
release. Ignored output is inventoried separately and archived, with existing
cache and verified provisioned-link exemptions unchanged. The shared 256 MiB
aggregate archive cap also applies.

Under the existing attachment/removal lock, the active-task API must return a
valid `tasks` list with no matching active task; missing or malformed `tasks`
is unknown. Process-CWD and open-file/mapping probes must prove absence, including
the open-file probe's visibility check. These gates bind clean legacy holders
too, regardless of whether an owner record exists. HEAD must equal the exact
live remote branch tip from `git ls-remote`; cached tracking refs cannot prove
that equality.

Before unlinking scratch, the shared preservation boundary copies and retrieves
every selected file, verifies names/sizes/SHA-256, publishes a manifest, and
records `branch_holder_archive` on the canonical task. Hand-off output includes
the repository-relative `manifest_path`, `content_sha256` and
`retrieval_proof_sha256`. Archive or receipt failure deletes nothing. Claims,
liveness, task/run identity, HEAD and the complete inventory are rechecked;
every receipt-covered regular source is renamed descriptor-relatively to an exclusively
reserved private name in its own directory, without following links. The moved
inode must match the open source descriptor and its bytes must match the archived
digest. The entire private set is revalidated before the first unlink. A mismatch
restores staged names without overwriting any new arrivals and refuses release.
A failed restoration retains the bytes under the private name and records typed
`source_restore_failed` evidence with both repository-relative names in
`branch_holder_release_refusal`. Archived ignored output is retired in the same
verified pass, so the common boundary does not archive it again or replace the
receipt; existing regenerable-output exemptions remain unchanged.
Non-force worktree removal then uses the existing common boundary. Dry-run
neither archives nor unlinks.

This lock coordinates cooperating attachment/removal callers; it cannot freeze
an unrelated filesystem writer or a new process after the final absence probe.
Replacement at an ordinary source name between final stat and staging is now
caught and preserved. An unrelated writer targeting a private staging name can
still race its reservation/rename or final verification/unlink; an inode writer
can also change bytes after final private-set verification. The attachment lock
does not exclude unrelated writers from those windows.
Git still refuses new ordinary untracked/modified files at non-force removal;
already archived scratch remains retrievable if removal fails. Unknown state
always refuses release. This slice adds no probe retry, identity bypass,
retention release or automatic archive deletion. Dirty-tree and activity
refusals remain residuals owned by the accountable driver (`claude-monitor`).

The scheduled job reports terminal non-success dispatches as preservation
candidates; it does not commit or push their work. Dispatch v2 has no rescue
subcommand. The accountable driver inspects branch/worktree evidence and
preserves unfinished work before removing the tree with
`worktree_claims remove`. Unknown custody
or unpushed work remains protected.

## Branch sweep evidence (#9909)

`scripts.hygiene.branch_sweep` stays a dry run unless `--apply` is passed. A
merged pull-request head that matches the branch tip, and a tip that is already
an ancestor of `origin/main`, are still the only ancestry proofs. Any other
agent or scratch branch is deleted only when one more proof holds: every commit
that is not on `origin/main` has the same `git patch-id --stable` as a commit
on `origin/main` since the merge base, or the issue named by the branch (or, when
the name does not name one, by its commit messages) is closed and the merged
pull request that closed it changed every file the branch changes. That merge
commit has to be on `origin/main`, and the pull request has to belong to this
repository: `source.issue.repository` must match the origin owner and name, so
a fork pull request that names the issue is not a closer. Merged-PR evidence
is accepted only when the branch exists on origin, the remote tip equals the
local tip when a local ref exists, and every branch commit's committer date is
no later than the closing merge commit's committer date. A local-only branch
is refused, because recovery needs the tip on GitHub. `rescue/` branches can
use only the patch-id proof. An open pull request, a registered worktree, or a
task record that has not finished (including `spawning` and `running`) keeps
the branch. The issue timeline is one REST read; an unreadable read keeps the
branch. `--apply` appends one receipt line to
`batch_state/branch-archive/evidence.jsonl` on the control-plane checkout
before it deletes either ref, then appends a second line after the delete
attempt with `remote_deleted`, `local_deleted`, and any error. The first line
records the branch, tip SHA, evidence kind, evidence detail, and UTC time. It
does not by itself claim that the deletion succeeded. While GitHub still has
the object, `git fetch origin <tip-sha>` recovers it.

`branch_sweep --archive-after-days N` also classifies expired local report-only
branches as `archive-expired` after seven days by default. Apply writes one thin
bundle under `batch_state/branch-archive/`, verifies every selected head, and
appends durable records to `stale-local-receipts.jsonl` before deleting any local
ref. Every existing receipt must be a valid, newline-terminated JSON object;
a broken ledger refuses the batch. A repository-wide exclusive archive lock on
the control-plane checkout covers fresh validation, bundling, receipts, final
guards and ref deletion. The persistent `branch-archive/archive.lock` file is
never unlinked. Each bundle is created and verified under a private temporary
name in the managed `TMPDIR` lease, or the shared scratch root when `TMPDIR` is
unset or empty. An atomic hard link publishes it into the archive directory and
refuses an existing name. Staging and publication must share a filesystem;
cross-filesystem link failure keeps every selected ref and any existing bundle,
without copying into a live archive name. Private staging is removed after the
attempt; published bundles survive later guard or receipt failure.
Thin bundles exclude `origin/main` history.
The receipt's restore command needs those prerequisite commits present: fetch
them from origin or restore in a clone of this repository. Remote refs and
archive bundles are retained; bundles at least 90 days old are listed for review.

Symbolic local refs are retained. Any selected branch failing pre-bundle
validation keeps the entire batch without creating a bundle. After receipts are
durable, a fresh PR snapshot covers the whole selected batch in one GitHub
response, followed by fresh ref, worktree and task-record snapshots compared
with classification. Unknown or changed guards keep the entire batch. The last
local checks before the single `git update-ref --stdin --no-deref` transaction
explicitly refuse occupied worktrees and live or recent tasks. Archival admits
only candidate branches with no associated registered worktree,
including a detached checkout at the candidate tip. The unrelated normal primary
checkout does not prevent archival of unbound branches. Any native in-progress
operation anywhere in the repository's worktree set refuses the entire sweep,
including operations on unrelated branches. The reader checks Git's rebase and
sequencer directories and bisect, merge, cherry-pick, revert and rebase markers;
operation state is refused by presence, without parsing branch names or
`update-refs` contents. An incomplete bisect start also refuses the sweep.
The reader uses Git administrative registrations even for moved, locked or
prunable checkouts. Missing, malformed, unreadable, contradictory or unknown
registration and HEAD evidence refuses deletion. Operation evidence never proves
that a branch is free. The same census runs before classification, for drift
snapshots and again at the final destructive boundary. This conservative fallback
narrows archival availability; it does not certify the original unrestricted
archival outcome while unrelated operations are active.
A guard change after its final snapshot and before the transaction remains a residual race
window; GitHub, task files and worktree registrations do not share a transaction
with Git refs. Expected-SHA checks abort the whole transaction on head moves;
`--no-deref` prevents deletion through a symbolic target. The accountable sweep
driver owns assessment of this residual window before live use.

The scheduled job removes no worktree. Unregistered directories with broken
`.git` pointers are reported as orphans and are never deleted automatically.

### Aggregate-only public reporting

`scheduled_worktree_cleanup.py` prints one JSON summary (`build_public_summary`) with **zero host path dumps**: per repository, the counts of orphans reported, errors, rescue candidates and branches deleted; overall branch, review-temp and task-scratch counts; the session-scratch and batch-state retention summaries; and the receipt id. Full diagnostic receipts containing individual filesystem paths are written only to private local storage (`~/.codex/worktree-cleanup/receipts/v2/`) with strict owner-only permissions (`0600`/`0700`) for recovery.

### Reaper retired (FR-01b)

The worktree reaper (the common reaper, the post-task reaper and the
dispatch-admission disk reaper) and its `learn-ukrainian-worktree-reaper`
service and timer are gone: the dispatcher removes each task's own worktree
when the task settles. Remove one leftover worktree by hand with
`python -m scripts.orchestration.worktree_claims remove <path> --owner-task-id <id> --reason '<why>'`.
On a host that still has the units installed:

```bash
systemctl --user disable --now learn-ukrainian-worktree-reaper.timer
rm -f ~/.config/systemd/user/learn-ukrainian-worktree-reaper.{service,timer}
rm -rf ~/.config/systemd/user/learn-ukrainian-worktree-reaper.service.d
systemctl --user daemon-reload && systemctl --user reset-failed
```

## Deletion ownership

Untracked files that a shell call left in the primary checkout itself are a
separate path: `scripts.hygiene.primary_dirt_cleanup` removes only the files
an audit record proves the calling session created
([`primary-checkout-dirt.md`](primary-checkout-dirt.md), #11253).

Every worktree removal goes through one guarded chokepoint (#8610): Python
callers use `worktree_claims.remove_unclaimed_worktree`, and shell and YAML
callers use `python -m scripts.orchestration.worktree_claims remove PATH`
(`scripts/wt.sh clean`, the RB2 trail's `cleanup_failed_worktree`). Holding
the per-worktree lock dispatch holds from attach until its task record is
published, it runs the caller's ownership proof, proves a forced target clean,
refuses while another task's unfinished record names the checkout, and only
then calls `worktree_claims.git_worktree_remove`, the shared raw
`git worktree remove`. The dispatcher's settlement runs its own non-forced
removal (see the audit table above).
The shared remover checks approved deletion roots for forced removals. Non-force
callers retain Git's ordinary removal
rules, including sibling worktrees created by `wt.sh` and task-family cleanup
when `TMPDIR` is unset.
`tests/orchestration/test_worktree_removal_invariant.py` fails on any other
removal call site under `scripts/`.

Callers and their ownership proofs:

- Regular dispatch worktrees: the dispatcher at settlement
  (`worker._reap_settled` → `git.settle_worktree`).
- `delegate` settle and superseded-review cleanup remove only a checkout the
  dispatch created. `delegate._release_stale_branch_holders` performs a
  non-force release after clean, synced, terminal-owner checks so a blocked
  dispatch may reattach its branch.
- `delegate._settle_failed_worktree_add` removes nothing. After its own
  failed or timed-out `git worktree add`, dispatch leaves the directory it
  reserved with `mkdir` as it is, empty or not, and reports it (see
  "Interrupted `git worktree add`" below).
- `_acp_execution.acp_execution_cwd` force-removes only the detached,
  no-checkout ACP workspace it created, on setup failure or context teardown.
- `_acp_execution.sweep_dead_acp_runtime_worktrees` proves the recorded lock
  owner dead (pid absent, or pid recycled with a different `/proc/<pid>/stat`
  start time) and removes the runtime only while it holds just its `.git`
  pointer, re-checked under the lock. Alive or unknown owners are never
  touched; a sweep failure is logged and never blocks the ask.
- `task_family.git_safety.remove_unclaimed_worktree` is the task-family bundle
  path: its executor repeats frozen-plan, merged-PR, bundle, and candidate
  checks immediately before deletion.

`dispatch.py dispatch` refuses a `--cwd` or `--worktree` inside
`.worktrees/dispatch/acp/`: those runtimes belong to the ACP bridge and are
never a dispatch target.

### ACP runtime worktree ownership and abandoned-runtime removal (#8344)

Every ACP runtime worktree is locked at creation with a reason of the form
`active ACP execution <label> (owner pid=<pid> start=<start>)`, where the
start time is field 22 of `/proc/<pid>/stat`. Any later process can prove the
owner dead without the owner's cooperation: pid absent, or pid recycled with
a different start time. Hosts without `/proc` record `start=unknown` and are
treated as unknown, never as dead. The proof assumes the ask and the sweep
share one PID namespace; a live owner inside a container or private namespace
can read as absent, so do not rely on it across namespace boundaries.

`_acp_execution.sweep_dead_acp_runtime_worktrees` removes a
`.worktrees/dispatch/acp/runtime-*` worktree only when its lock carries owner
information, the owner is provably dead, and the directory holds exactly its
`.git` pointer (no-checkout residue); any other file preserves it. A legacy
owner-less ACP lock is left alone. `acp_execution_cwd` runs this dead-owner
sweep on entry, before creating its own workspace, so a
killed ask's stub is gone by the next ACP call at the latest. As defence in
depth, the ask entry path converts SIGTERM into an orderly unwind
(`SystemExit(143)`) so the context `finally` cleans up when it can.

### Interrupted `git worktree add` (#8663)

Dispatch v2 prepares worktrees through `scripts/dispatcher/git.py`. The legacy
adaptive `DELEGATE_WORKTREE_ADD_*` timeouts and their launcher recovery path
are retired. Do not infer that an interrupted checkout is disposable: inspect
its task record, Git registration, process liveness and custody first. Remove
it with `worktree_claims remove`; unknown or active ownership preserves the
checkout.

## Before re-firing a task id

A detached `dispatch.py dispatch` launcher that is still grinding from a prior
attempt can finish after you re-fire the same task id, leaving two workers on
one worktree (the task record points at the newer pid; the older process is an
orphan). Before re-using a task id, kill any stale detached launcher for it:

```bash
/bin/ps -axo pid,etime,command | grep 'dispatch.py dispatch .*--task-id <id>'
```

Confirm the match is the stale launcher, then terminate that pid before the
new dispatch.

### Evidence before cleanup or reuse

Workers write artifacts under their own worktrees. Dispatch v2 does not preserve
these artifacts automatically or require an evidence retrieval receipt before
worktree reuse. Explicitly retrieve required evidence into durable storage and
verify its content before cleanup or reuse. Put the verdict and supporting
evidence in the result text, and cite verified durable artifact locations.

## Immediate cleanup after merge

On apply, `merge_closeout` first captures local Git facts through the lifecycle
API for each matched task carrying a lifecycle ledger, while its worktree still
exists; it removes no worktree. Existing valid local observations are reused.
Tasks without a ledger keep their existing cleanup behavior. A capture or
ledger-write failure blocks closeout. The exceptional
`--no-lifecycle-observation "reason"` option logs its explicit reason in the
cleanup report.

For a merged task already removed without that observation, use the supported
append-only recovery command. Rehearse on private copies of the ledger, task
record, successful push record and complete preservation tree first. Keep the
tree's `batch_state/preserved/<task>/<attempt>` layout within the copy root.

```bash
.venv/bin/python -m scripts.orchestration.task_closeout recover-local \
  --state-file ledger.json \
  --task-record task.json \
  --preserved-manifest batch_state/preserved/example/attempt.manifest.json \
  --push-record successful-push.json
```

The push JSON must record `status: pushed_exact_head`, equal `head` and
`remote_head`, the task's worktree in `cwd`, and a `steps` entry named `push`
with integer `exit_code: 0`. A failed push log is insufficient. The delegate
record must bind the lifecycle, preservation receipt and merged PR reaper
proof, including the task's branch/head member. Recovery validates every
preserved file and appends a receipt marked `recovered_from_preserved` with
SHA-256 references to all three source records. These new receipts store
repository-relative input locators, `repo_root: .`, `primary_checkout: .`, and
a repository-relative dispatch `worktree`. Absolute locators, `..` components,
and symlinks escaping the repository are refused. Source records retain their
original bytes and digests, including the original worktree's SHA-256 binding.

Keep the source records and complete preservation tree under the repository's
primary root for later validation. Private rehearsal copies must keep the
relative layout within a copied repository containing the required commits.
The repository and evidence can move together without changing the receipt.
Validation resolves locators against the current repository, or the CLI's
explicit `--repo-root`, rather than a stored host path.

Existing observations are not rewritten. The shared `observe_local_git` API
still returns the older absolute `primary_checkout` and `worktree` fields to
other callers. Removing those pre-existing fields is a separate infra-owned
residual; the new capture and recovery writers convert their own copies.

Recovery never recreates a worktree, backdates an observation or edits previous
receipts. Ordinary same-carrier recovery makes no GitHub calls. Repeating recovery
returns the existing verified receipt. Missing inputs, changed digests, wrong task/branch and unavailable or
unrelated commits produce typed `RECOVERY_*` refusals. Reconcile with current
GitHub authority afterward; recovery alone does not close the issue or prove
review, CI or delivery.

For a later child PR delivered by an attempt carrying an earlier lifecycle,
add `--associate-child` to the recovery command above, pointing `--state-file`
at the child's ledger. This explicit mode reads that ledger's PR from GitHub
and requires `MERGED`, its exact repository-qualified URL, head and branch.
The preserved task's `worktree_reap_proof` must independently name that child
in `pr_number` and `pr_head_sha`, retain `pr_state: MERGED`, and contain the
task's branch/head member. Missing proof refuses with
`RECOVERY_MERGED_PR_UNPROVEN`; a different child PR/head/branch refuses with
`RECOVERY_CHILD_PR_MISMATCH`; an unavailable GitHub read refuses with
`RECOVERY_CHILD_PR_UNAVAILABLE`. Do not fill missing proof from ancestry or
edit the author carrier to match the child.

Rehearse with the copied child ledger and original evidence tree. Verify that
one receipt contains `recovered_from_preserved.association`, naming both
lifecycle identities, the exact task/run nonce and child PR/head. Repeat the
command and check that the receipt ID is unchanged. Confirm that the earlier
ledger and carrier bytes are unchanged. Alter a copied input and confirm a
typed refusal with no append. The association supplies local observation only;
review, CI and behavior evidence require their own verification.

The merge owner closes out the exact PR as soon as GitHub reports it `MERGED`, using
`scripts.orchestration.merge_closeout`. This is the one command that proves the PR
MERGED, finds every worktree still tied to it (by branch, by exact merged head SHA,
or by an earlier commit that exists only on that PR, including detached
review-checkout siblings), and proves the remote and local branch are both gone. It
removes no worktree: the dispatcher removes each task's own worktree when the task
settles, and a worktree it kept (dirty, unpublished, live process ...) is reported as
a residual.

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
cd "$PRIMARY_REPO"

"$PRIMARY_REPO/.venv/bin/python" -m scripts.orchestration.merge_closeout <PR_NUMBER> --apply
```

Starting a later review round (`review-<topic>-rN`) also removes earlier clean
rounds of that same series, including detached ones that no longer hold the
branch, but only when that checkout's HEAD is already an ancestor of
`origin/main` or reachable from some `refs/remotes/origin/*` ref. A dirty,
still-running, or uncontained round is left in place, and its local branch is
not deleted.

Default is dry-run; pass `--apply` to delete residual branches. `--json` emits a
machine-readable payload. It exits non-zero if the PR cannot be proven `MERGED`, if
a matched worktree is still registered, or if the remote or local branch is still
present after `--apply` ran (residual branches are reported, never force-deleted
past an exact-head-match proof). A kept worktree is a blocker for its owner to
resolve, not permission to remove it with `--force`.

The canonical PR lifecycle trail (`scripts/config/trails/rb3-pr-lifecycle.trail.yaml`)
runs its own post-merge step: it deletes the merged remote branch when no open PR
uses it, prunes origin, and removes no worktree; a worktree still on disk stops the
trail at `STOP-hygiene-failed`. Other merge owners must invoke the exact command
above before declaring closeout complete.

Git closeout for **every** merge is exactly three things: worktree gone,
remote branch gone, local branch gone. If GitHub did not delete the remote
head, delete it. Then delete the local branch. Host pulls, tunnels, occupancy
probes, service restarts, and similar proofs are **task remainder**, not this
list — name them for this task and finish them, but do not add them to standing
merge hygiene.

Do not put networked worktree deletion in Git's `post-merge` hook. GitHub merges
do not run a local hook, and a later `git pull` is not reliable ownership
evidence for an arbitrary dispatch worktree.

## Manual dual-repository sweep

Dry run:

```bash
.venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py
```

Apply:

```bash
.venv/bin/python scripts/orchestration/scheduled_worktree_cleanup.py --apply
```

Each run performs the following in both repository roots:

1. fetches `origin` and prunes deleted remote refs, with automatic
   maintenance disabled on that command (`maintenance.auto=false` and
   `gc.auto=0`) so the fetch cannot expire reflogs before branch cleanup runs;
2. prunes stale Git worktree registrations;
3. reports terminal-task worktrees finished more than six hours ago that are
   still on disk and dirty or hold commits absent from `origin` (rescue
   candidates; report only, clean published trees are not listed);
4. deletes origin heads that are not checked out, have no open PR, and are not
   `entire/` refs, only when the tip is proven contained: the GitHub PR is
   MERGED or CLOSED at the exact live origin SHA (`ls-remote` +
   `--force-with-lease`), the tip is contained in a MERGED PR and is not an
   ancestor of `origin/main`, or the tip is already an ancestor of
   `origin/main`. Names `*/review-*`, `rescue/*`, and `pr-*` are not that
   proof. They only widen the set of refs examined, because `gh pr list --head`
   never sees them. A scratch-named origin ref may also be deleted when its
   tip is reachable from some other `refs/remotes/origin/*` ref. Its own
   remote ref does not count. A git error during that check is not
   containment, and an unproven scratch ref is kept;
5. deletes local branches whose upstream is gone, or that were never tracked,
   on the same containment evidence (`entire/` refs are preserved);
6. preserves and reports unproven gone branches and orphaned worktree
   directories;
7. records Git maintenance as `scheduled_separately`;
8. writes an immutable JSON receipt.

It removes no worktree. Open PRs, checked-out branches, and unmerged branch heads
remain untouched.

### Bounded Git maintenance (#11157)

The separate `learn-ukrainian-git-maintenance.timer` starts at 03:30 UTC.
`Persistent=false` prevents a missed run from starting during daytime validation.
The hourly hygiene job and macOS launchd job perform no GC.

The maintenance service invokes the same wrapper with `--git-maintenance --apply`,
which runs only GC and writes its private receipt. It caps the whole process tree
at 2 GiB memory, zero swap, one CPU and 32 tasks. Each repository has a 600-second
foreground deadline. Timeout cleanup gives Git a five-second SIGTERM grace period
without reaping it, then requests SIGKILL for the entire group before reaping Git.
This lets Git clean up its locks while still terminating children that close their
pipes before exiting. The service allows 1300 seconds
for both repositories and kills its entire cgroup on expiry. Effective kernel
limits, including ancestors, must meet these bounds or GC refuses to run.
Manual shells and systems without cgroup v2 therefore cannot run this mode unbounded.

Before enabling the timer, the driver must retain `gc.auto=0` and
`maintenance.auto=false` in each repository's configuration. Maintenance verifies
these settings and refuses otherwise. Its command overrides the automatic GC
thresholds with Git's defaults of 6700 loose objects and 50 packs, disables
detachment, and sets `pack.threads=1`, `pack.windowMemory=64m` and
`pack.deltaCacheSize=64m`. Existing expiry settings remain in effect. An exit-zero
GC can be a no-op; the receipt reports `changed` from before/after object counts.
Concurrent ordinary Git writes can also change those counts. This observation
does not prove that GC performed a repack.

Maintenance takes the existing Git-hygiene lock and the validation gate's global
admission lock exclusively and nonblockingly. Active serial or parallel validation,
another maintenance run, or hourly hygiene produces `deferred`; the next timer
run retries. Maintenance holds admission through GC and timeout recovery, so
validation cannot start between a check and a repack. Gate wait limits are unchanged.

Install the reviewed service, timer and data-volume drop-in together, then verify
effective limits and lock deferral in a disposable repository before enabling the
timer. Production rollout and confirmation that this hour fits the host's workload
remain driver responsibilities. A cgroup OOM kill is reported by systemd and may
prevent the process from writing its JSON receipt; absence of a receipt is not success.
This command does not remove incident temporary packs manually. Their disposition
requires a supported Git operation with verified retention and concurrency semantics.

References: [Git GC configuration](https://git-scm.com/docs/git-gc),
[systemd resource limits](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html).

```text
~/.codex/worktree-cleanup/receipts/v2/
```

A failed fetch skips every deletion that relies on remote containment.
Standard output carries the path-free public summary described under
"Aggregate-only public reporting"; the receipt holds the full detail.

## Linux systemd default

The collector sweeps both repository roots. Before installing the service
template, replace both `@REPO_ROOT@` and `@PRIVATE_ROOT@`.

The shipped `packaging/systemd/learn-ukrainian-worktree-gc.service` passes
`--apply`, the same as macOS launchd. Its timer fires hourly
(`OnCalendar=hourly`, `RandomizedDelaySec=0`), retaining `OnBootSec=15min`
and `Persistent=true`, using the existing
cleanup wrapper; this adds no daemon or cleanup class, and the
denser cadence does not loosen the dirty/open-PR/unreadable-GitHub-state
guards. See `packaging/systemd/README.md` for enable and disable
instructions.

## Inspect the LaunchAgent

Render the plist without writing system configuration:

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py render
```

The job runs at load and every 4 hours. launchd `Program` is `/bin/bash`
(Apple-signed, survives a `.venv` rebuild) plus
`scripts/orchestration/run_scheduled_worktree_cleanup.sh`, which execs the
public checkout's `.venv/bin/python`. Pointing `Program` at the venv
interpreter is what produced exit 78 (`Unable to get updated LWCR ... error
0x3`) after the 2026-08-15 venv rewrite. The wrapper passes both repository
roots explicitly and persists logs under:

```text
~/.codex/worktree-cleanup/logs/
```

## Install

Install only after the cleanup code is merged into the public primary checkout.
Both primary checkouts must be on `main`.

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py install
```

Installation is idempotent. It writes and loads:

```text
~/Library/LaunchAgents/com.learn-ukrainian.worktree-cleanup.plist
```

Verify the persisted plist and live service:

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py status
```

After installation, inspect the first receipt for errors. A venv rebuild does not require
reinstall anymore; `status` still verifies the plist still binds `Program` to
`/bin/bash`.

A red or missing scheduled run surfaces on the existing integrity canary
(`/api/orient` `health.worktree_cleanup_integrity_ok`, plus the dispatch
pre-flight warning). Probe:

```bash
.venv/bin/python scripts/audit/check_worktree_cleanup_integrity.py
```

## Uninstall

```bash
.venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py uninstall
```

Uninstalling preserves receipts and logs for audit and recovery.

## Ad-hoc `/tmp` leak sweep

Agents sometimes leave full clones under `/tmp` outside the formal review isolation
prefixes (`review-6621`, `pr6591-exact-*`, `lu-*`, local CI fixtures). Those trees do
not match `sweep_review_temp_orphans` and will refill the disk within hours.

```bash
# dry-run
.venv/bin/python -m scripts.orchestration.tmp_leak_sweep

# apply
.venv/bin/python -m scripts.orchestration.tmp_leak_sweep --apply
```

The scheduled git-hygiene runner (`scheduled_worktree_cleanup.py`) invokes the same
sweep after the review-temp reaper. Age gates: 2h normally, 30m when free space is
below the configured pressure floor. Live and liveness-unknown paths are skipped (see below for the proof).

### Atlas/QA legacy residue (#8738)

Only five exact names are ever auto-deleted by the sweep, once the age, ownership and
liveness gates pass: the #8307 Atlas 410k outputs `atlas-8307-410k-final.db`,
`atlas-8307-410k-r2.db`, `atlas-8307-synthetic-410k.json`, and the #8686 QA scratch
directories `qa-8686-ui-r2`, `qa-8686-exercises-r2`. Every other `atlas-<n>-*` /
`qa-<n>-*` entry is **inventoried** (`inventory_only` count and list in the report)
but never deleted without fresh ownership proof. Names containing `promotion`, and
any `decision*.yaml`/`.yml`, are protected: never deleted, never listed as residue.

Liveness is not `pgrep -f` alone. The actual proof required before a deletion is
both of:

1. `pgrep -f <path>` exits 1 (no command line of any user names the path); and
2. a `/proc` walk in which **every** process except the sweep itself was fully
   probed (scheduler state, command line, working directory, environment, open
   descriptors) and none references the path or a descendant.

Every process is probed the same way regardless of its owner. A foreign-uid
process can hold a world-readable legacy file open without naming it on its
command line, so ownership is never treated as proof of absence. Any process that
refuses inspection of any probe, for any reason (`EACCES`/`EPERM` from a
non-dumpable same-uid daemon, a root-owned service or a kernel thread, `EIO`, an
unreadable `stat` or `cmdline`), makes the verdict unknown, and unknown preserves
the entry (`skipped` reason `liveness_unknown`, distinct from `live_process`). Only
two things turn an unreadable process into "holds nothing": `/proc/<pid>` has
vanished (the process exited), or its state is zombie/dead. A host without `/proc`
(macOS) cannot detect a process that holds a candidate as its cwd or through an
open descriptor, so a negative `pgrep` there is `liveness_unknown`, never clear.

Consequence: the legacy auto-sweep is **inventory-only in practice**. On the
primary Linux host, root-owned services and kernel threads deny cwd/fd/environ to
the sweep's uid, and `systemd --user`, `(sd-pam)`, `ssh-agent`, `sshd-session` are
non-dumpable same-uid daemons, so every deletable candidate is reported as
`liveness_unknown` and nothing is deleted (verified on 2026-09-24 after this
change: `path_liveness` on a fresh, unreferenced path returned `unknown`; 94
same-uid processes probed clear, 4 same-uid and every foreign-uid process were
unknown). On macOS the sweep is inventory-only by construction. That is intended:
the legacy allowlist is a best-effort drain, and the reliable path for large
residue is the managed `task-scratch` lifecycle below, whose recovery proves
ownership from recorded metadata instead of guessing from `/proc`. Drain legacy
names by hand after confirming with `lsof`/`fuser` that nothing holds them.

The managed `task-scratch` namespace, every scratch root (`/var/tmp/lu`, the
`<tmp>/lu-scratch` fallback, `$LU_RUNTIME_TMP_BASE_ROOT`) and their ancestors are
excluded from the scan even when a basename matches a pattern.

## Claude session scratch and one-off reporting (#8783)

The scheduled hygiene runner also handles Claude session scratch (#8783) once
per host run. Its default is report-only; `--apply` enables removal. The sweep
recognizes UUID session directories immediately under the per-user Claude temp
root or under a project directory. It never follows directory symlinks, including
root ancestors, and uses descriptor-relative, symlink-resistant removal. A
positive live-process match always preserves the session. The sweep reads Claude
Code's per-process `sessions/<pid>.json` registry under `CLAUDE_CONFIG_DIR`
(default: the user's Claude config directory). A registry PID with a matching
kernel start time (`procStart`) protects its `sessionId`, even when process
enumeration omits it or the executable has another name. PID reuse with a different
start time does not establish liveness.

Removal requires readable registry evidence whose `pidDomain` matches the
sweeper's machine identity and PID namespace, plus no unidentified Claude process.
A missing, empty, malformed or inaccessible registry, a mismatched domain, or a
Claude executable/first argument, native executable under `claude/versions/`, or
Node running Claude Code's `claude-code/cli.js` entrypoint without a matching
registry entry prevents absence proof, including for confirmed v2 thread-handoff
predecessors. Access denied on unrelated processes and later data argument paths
containing `claude` do not block absence proof. Unknown entries remain preserved; session age never
authorizes deletion. Deep-tree recursion errors are reported per entry and do
not abort the remaining hygiene run. Registry JSON parse failures, including
excessive nesting, prevent absence proof. Lease JSON parse failures are recorded
as errors and preserve sessions without a positive live match as `unknown_session`;
an unreadable lease cannot safely identify which predecessor it affects.

Apply rechecks liveness immediately before removal, but this is not an atomic
transaction with Claude's session startup. A `claude --resume <id>` starting
after that recheck can race with removal and lose scratch. Avoid starting or
resuming sessions during an apply run; use dry-run when that cannot be ensured.

To inspect session scratch independently:

```bash
.venv/bin/python -m scripts.maintenance.claude_session_scratch
```

Add `--rollover-root .agent/thread-rollovers/claude` to read confirmed lineage
records, or `--apply` to remove proven-ended directories. The independent CLI
prints counts and bytes only. Scheduled private receipts retain per-entry reasons;
public summaries retain only aggregate counts, bytes and preservation reasons.

The batch-state sweep lists regular files at least 100 MiB outside managed
`tasks/` state in `one_off_artifacts`, including `manifest_*.json` outputs. Each
entry has a batch-state-relative path, bytes, age in days and `report_only` action.
Owners use this list to decide disposition; the one-off report never removes
these files. Scheduled public summaries expose their count and total bytes.

## Worker-held runtime scratch (#10000)

Dispatch v2 does not automatically preserve cited runtime scratch or
`held_work`. The legacy launcher preservation module is retired. Preserve required
evidence explicitly before cleanup, with a
retrieval receipt where a guarded remover requires one. Existing unknown
custody remains protected. The standalone task-scratch wrapper below retains
its explicit evidence-directory contract.

## Task-owned scratch for large ad-hoc runs (#8738)

Large one-off outputs (synthetic Atlas DBs, runtime-shard exports, delegated QA
scratch) must not be written to hand-named `/tmp` paths: nothing ties such files to
the process that made them, so the sweep can neither prove them abandoned nor drain
them. Run the producer through the wrapper instead. The command below is copyable
from any dispatch worktree: a worktree has no `.venv`, no `data/atlas.db` (sparse
checkout) and none of the generated `site/public/lexicon` decks the exporter
registers, so every one of those comes from the primary checkout via
`PRIMARY_REPO`, which is **exported** so the `bash -euc` child shell sees it:

```bash
export PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" scripts/tools/task_scratch.py run --task-id atlas-8307-410k \
    --evidence-dir batch_state/tmp/atlas-8307-410k-evidence -- \
    bash -euc '
      "$PRIMARY_REPO/.venv/bin/python" -m scripts.benchmarks.generate_synthetic_atlas \
          --source-db "$PRIMARY_REPO/data/atlas.db" --out "$LU_TASK_SCRATCH_DIR/atlas.db" \
          --seed 8307 --target 410000
      "$PRIMARY_REPO/.venv/bin/python" -m scripts.atlas.export_runtime_shards \
          --db "$LU_TASK_SCRATCH_DIR/atlas.db" \
          --out-dir "$LU_TASK_SCRATCH_DIR/export" \
          --deck-dir "$PRIMARY_REPO/site/public/lexicon" --verify
      mkdir -p "$LU_TASK_SCRATCH_DIR/evidence"
      cp "$LU_TASK_SCRATCH_DIR/export/atlas/current.json" "$LU_TASK_SCRATCH_DIR/evidence/"
    '
```

Rehearse with `--target 50` and an isolated `--scratch-root` before a 410k run; the
rehearsal on 2026-09-24 from a dispatch worktree took about ten seconds, exited 0,
exported one evidence file and left the scratch root empty.

What the wrapper guarantees:

- one unique directory per invocation under `<scratch root>/task-scratch/` (owner-only
  `0700`); the task id is lease metadata, not a deterministic path, so two concurrent
  runs of the same task never collide;
- `TMPDIR`, `TMP`, `TEMP` and `$LU_TASK_SCRATCH_DIR` all point at the payload
  directory. The `bash -euc '...'` form above is the documented way to chain the two
  Atlas steps in one run; the child shell expands `$LU_TASK_SCRATCH_DIR` and
  `$PRIMARY_REPO`, so keep the script single-quoted and export `PRIMARY_REPO`;
- the child starts in its own session behind a launch gate: the wrapper records the
  child's pid, process group and `/proc` start time in `lease.json` *before* the
  payload may run. A wrapper killed before that release leaves a child that exits
  without running anything;
- SIGINT/SIGTERM/SIGHUP are forwarded to the process group; the wrapper waits for the
  group, escalates to SIGKILL after `--kill-after-s` (30 s), and cleans. Normal exit
  and nonzero exit clean too, preserving the child's status (`128 + signal` when
  signal-killed). Grandchildren that outlive the leader get `--group-grace-s` (15 s),
  then TERM/KILL. Detached services do not belong here: give them a durable path;
- **the scratch disappears after a successful run.** Copy the small summary you need
  into `$LU_TASK_SCRATCH_DIR/evidence/` and pass `--evidence-dir` (16 MiB cap);
  `--keep` / `--keep-on-failure` leave the lease for the scheduled recovery instead.

Both Atlas producers already route every output under their `--out` / `--out-dir`
arguments (the exporter only reads `--deck-dir`), so no hard-coded destination stands
in the way. Existing scripts that hard-code `/tmp/...` paths bypass the wrapper
entirely; migrate each producer by pointing its output flags at
`$LU_TASK_SCRATCH_DIR`. The wrapper does not claim to capture writes it was not given.

### Recovery of interrupted runs

```bash
# inventory: every lease with the guard that preserves it (mutation-free)
"$PRIMARY_REPO/.venv/bin/python" scripts/tools/task_scratch.py recover

# reclaim proven orphans (what the scheduled runner does)
"$PRIMARY_REPO/.venv/bin/python" scripts/tools/task_scratch.py recover --apply
```

`scheduled_worktree_cleanup.py` runs the same recovery after the `/tmp` leak sweep.
A lease is reclaimed only when **all** of the following hold:

1. the entry is a plain directory owned by the current uid on the namespace's device,
   with a regular (non-symlink) `lease.json` of the current schema whose device/inode
   match the directory and whose uid is ours;
2. the lease lock is free (an owning wrapper holds it for its whole lifetime);
3. the recorded owner is provably dead: pid absent, pid present with a different
   start time (reuse), or a different kernel boot id;
4. the recorded child group is provably dead: leader absent or start-time mismatch
   **and** no process left in the recorded group. Any surviving member, a reused
   numeric group id, or an unreadable `/proc` preserves;
5. the newest modification anywhere in the lease is at least 2 h old, or 30 min when
   the scratch volume is below the configured pressure floor. Pressure shortens the age gate only.

Recovery never signals a process. Deletion (both the owning wrapper's and recovery's)
is fd-relative with `O_NOFOLLOW` and proves containment on every destructive step:

- before anything is unlinked, a non-destructive pass over the lease re-proves every
  directory's identity (device/inode), device, and **mount id** on the descriptor it
  just opened. The mount id comes from `/proc/self/fdinfo/<fd>`, so a bind mount of
  the same filesystem (same `st_dev`) is refused even when it was placed after the
  path-based `/proc/self/mountinfo` scan; a pre-existing mount therefore refuses with
  nothing deleted and the lease metadata intact;
- the same identity/device/mount-id proof repeats on every directory descent during
  deletion, and every `rmdir` re-identifies its target with the emptied directory
  still held open. Linux has no fd-based `rmdir`, so after the call the held
  descriptor's link count is checked: a swap inside that last window removes only an
  *empty* directory and is reported as a containment error, never counted as clean;
- unavailable mount information (`/proc/self/mountinfo` or the per-fd mount id) is a
  refusal, not a pass. On a host without those (`/proc`-less, e.g. macOS) the wrapper
  preserves the lease with `mount information unavailable` and recovery reports
  `mount_info_unavailable`; such leases are cleaned by hand.

Symlinks inside a lease are unlinked, never followed, and a device change is refused.
Anything malformed, foreign, symlinked, in use or unknown stays and is counted under
`preserved_by_reason` in the receipt; receipts carry counts and bytes only, never paths.

## Terminal worker publication

Dispatch v2 checks delivery; it does not run the legacy finalize or rescue
commands. A worker must commit with its required trailer and push its branch.
Inspect the task's terminal delivery fields and the remote head before claiming
success. Unpushed commits, dirty work and unknown delivery remain the
accountable driver's responsibility. Guarded-remover custody checks still bind.
