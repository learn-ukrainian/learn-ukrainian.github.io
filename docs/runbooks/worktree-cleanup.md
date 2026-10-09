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
"$PRIMARY_REPO/.venv/bin/python" -m pytest tests/test_delegate.py
```

Do not substitute `python`, `.venv/bin/python`, or `python -m venv .venv`.
The dispatch launcher records a warning when a local `.venv` is already present;
do not delete it while a task might be active. After the normal merged-PR guards
pass, the P0 reaper removes the entire disposable worktree, including ignored
environment residue.

## Shared node_modules (npm shim)

Dispatch worktrees receive `node_modules` and `site/node_modules` as symlinks into the primary checkout. The agent runtime provides an `npm` (and `npx`) shim that intercepts destructive commands to protect the shared tree.

Every npm/npx call through the shim runs with umask 022 to prevent the tree from becoming group-writable. The refusal message from the ACP adapter prints the exact corrective command class.

## Safety contract

Every Git-based worktree removal preserves ignored output at the sole raw
`git worktree remove` boundary in `scripts/orchestration/worktree_claims.py`,
using `scripts/fleet/ignored_task_output.py`. The dispatch exit and post-task
reapers, ACP execution teardown, data-tier cleanup, sibling Git maintenance,
task-family cleanup, and removal CLI all inherit this guard. The common P0
reaper calls the same boundary under its own ownership/liveness lock;
`merge_closeout` and scheduled cleanup invoke that reaper. Preservation runs
once, after ownership/claim checks and before deletion. A preservation failure
returns a typed skipped/refusal result and leaves the directory intact.
`branch_sweep` deletes branch refs only. The separate husk removal accepts
only unregistered directories with no files or symlinks. The legacy temp leak
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
| `delegate._remove_dispatch_worktree`: settle, stale holder and superseded review cleanup | Shared locked remover, then guarded raw Git. |
| `post_task_reap._remove_acp_runtime_worktree` | Shared locked remover; regular dispatches use the common reaper. |
| `_acp_execution._remove_runtime_worktree`: context teardown and dead-runtime sweep | Shared locked remover; no-checkout teardown inventories all untracked non-cache files, even without ignore rules. Dead-runtime sweep retains unexpected files. |
| `data_tier.remove_test_worktree`: stale and final cleanup | Shared locked remover. |
| `sibling_git.worktree_remove` | Shared locked remover; preservation uses the public control plane. |
| `task_family.git_safety.remove_unclaimed_worktree`: executor cleanup | Shared locked remover. |
| `worktree_claims remove`, `wt.sh`, RB2 failed-dispatch cleanup | Guarded CLI, then shared locked remover. |
| `reap_worktrees._reap_qualified_worktree`; `merge_closeout`; scheduled cleanup | Locked reaper pipeline, then guarded raw Git. |
| `reap_worktrees._remove_dispatch_husk_locked`: `shutil.rmtree` | Only unregistered, file-free and symlink-free husks; rechecked under the shared lock. |
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
`.hypothesis`, `.tox`, `.nox`, `.entire/logs`, and Git metadata) are excluded. `.cache`
itself is deliberately not a tool-cache exemption. Shared state and verified
provisioned database links survive outside the worktree and are never copied.
Task output placed in an excluded cache remains disposable. Real `.venv` and
`node_modules` directories are never disposable, including below caches; only
verified provisioned links are disposable. `worktree_artifacts.is_disposable_path`
is the shared taxonomy for creation, preservation and scheduled reaping.

Automatic preservation is capped at **256 MiB per worktree**, bounding disk
duplication while accommodating text output and small reports. Above the cap,
no partial copy is attempted and the worktree is retained for its owner's
disposition. Inventory, copy, byte-verification, or task-record write failures
also retain it, as do manifest or canonical task-receipt write failures. Task terminal
status never changes preservation eligibility. Existing ownership and liveness
gates still apply before preservation and removal.
Existing task records and reap/closeout receipts report `preserved_artifacts`
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

Both removal pipelines honor canonical `keep_worktree` even when Git is clean.
The gate discovers the bound hot/archive task record itself; caller-supplied
records cannot hide intent. A kept tree may acquire a passing retrieval receipt
but remains retained. Only an explicit existing-owner release through
`post_task_reap --release-retention --apply` clears intent. The command uses
`owner_release_refusal`, requires an existing passing retrieval receipt for the
same owner/run, rechecks preserved bytes against current output, and records the
release before removal. Missing proof, changed output, corrupt copies, a reused
checkout or mismatched owner refuses release. Dry-run never releases intent.
No new lock or state authority is introduced.

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
be retrieved and released; it is never dropped by attribution filtering.
In a continuation cohort, failed-preparation records with null PID, base SHA
and branch do not prove that no checkout was created: the failure writer also
runs after add attempts and can snapshot an existing HEAD. Without explicit
no-creation evidence they remain ambiguous and never grant ownership.
Infra owns this attribution residual.

For a keep-false continuation cohort, merged-PR-head containment plus a
clean checkout permits the common reaper to record `worktree_reap_proof`
(`merged-reuse-reap.v1`) on the creator and `merged_head_proof` in its removal
receipt. The proof records the PR, checkout head, PR head, their relation,
creator/run and cohort identities. The worktree lock precedes task-state locks
and all identities are rechecked.
The head must come from a branch or PR-number lookup; a commit-search hit
only proves commit membership and is refreshed by number before taking locks.
A `needs_finalize` creator additionally requires a done successor whose
recorded head is the checkout head, with every recorded process proven absent.
An earlier checkout head qualifies only when detached and proven to be an
ancestor of the authoritative merged PR head. Every current cohort record must
have a complete task/run/process identity and a commit contained in the checkout
head. Unknown Git objects, divergent commits, unmerged PRs and live or unknown
processes retain the tree. This proof does not release retention intent.
This extra owner proof applies only to cohorts of at least two current records;
single-record trees retain their existing behavior. Its status remains unchanged.
Removal uses no force flag for this cohort and still checks the delete target;
ignored non-cache bytes still require verified preservation and retrieval.
Retention intent continues to require the receipt-based retrieve/release
sequence above; merged-head proof never clears it.

```bash
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <task-id> --release-retention --apply
```

Infra owns legacy-tree and disk-use residuals and retention of
`batch_state/preserved/`. This change adds no automatic deletion policy for
preserved copies. Off-repository historical recovery remains unknown until the
open-model-data owner verifies it.

Cleanup is fail-closed. A worktree is preserved when any of these is true:

- its pull request is open (`open_pr`);
- its pull-request head does not exactly match the worktree HEAD, unless the PR
  is `MERGED` and the origin branch is gone, or it lacks merge proof (`unmerged`);
- its task is active or non-terminal, a live process has a working directory inside it,
  or an active task lease, rollover lease, write-ownership claim, or reap reservation exists (`active_dispatch`);
- a non-terminal review attempt reads from it. The task record claims the deepest registered linked checkout containing each of these inputs, including subdirectories and symlink spellings: its `review_contract.input_root`, and every `review_input_paths` entry, namely the attempt manifest (dispatch resolves its path once at admission, so every later read and the worker use the symlink target, never the supplied spelling) and the worker's own code checkout (it runs from there for the whole attempt). A formal attempt takes no output schema (`--review-attempt` with `--output-schema` is refused). Inputs in the primary checkout, or outside any registered checkout, claim nothing. Before it reserves the attempt id, dispatch refuses a review contract without an `input_root`, and refuses the attempt when the fleet scratch root (`LU_SCRATCH_ROOT`, which holds the worker's runtime tmp lease) lies inside a registered linked checkout (`review_scratch_root_in_worktree`). It holds the shared removal lock of every claimed checkout during input preparation until the task record publishes the claims. Only a terminal task status ends the protection; an owner or settled-claim exemption does not, and a record with an unreadable or malformed claim, or an unavailable worktree registration, refuses removal rather than releasing it;
- it is the repository's primary checkout (`primary`);
- it has uncommitted changes or untracked files (`dirty`), which are retained as exceptions and never force-deleted;
- it is in a detached HEAD or unresolvable state and does not meet the
  `detached_clean_contained` proof below (`detached_unknown`);
- it encountered filesystem permission errors during evaluation or removal (`permission_error`), which are retained as exceptions;
- it is outside the repository's `.worktrees/` directory or not a registered worktree (`foreign`).

The scheduled job reports terminal non-success dispatches older than six hours
as rescue candidates in its result and status; it does not commit or push them.
A clean tree with unpushed commits is flagged at task exit as
`unpushed work - needs rescue` when the upstream count is known, or
`unpushed state unknown - needs rescue` otherwise. The driver inspects the
report and explicitly runs rescue when appropriate. Rescue commits dirty work
on `rescue/<task-id>`, pushes it, and verifies the remote head with
`git ls-remote`. A failed push, unverified remote head, or changed file over
5 MB leaves the worktree in place. To inspect candidates without writing:

```bash
"$PRIMARY_REPO/.venv/bin/python" scripts/delegate.py rescue --all-stale --older-than 6h
```

To preserve a reviewed candidate explicitly, run:

```bash
"$PRIMARY_REPO/.venv/bin/python" scripts/delegate.py rescue TASK_ID --apply
```

After the driver has inspected a rescue, use `git log origin/rescue/<task-id>`
to see its commits. Delete an unneeded rescue branch explicitly with
`git push origin --delete rescue/<task-id>` only after its work is otherwise
preserved or discarded by the responsible driver. Scheduled branch cleanup
retains a rescue ref with unique commits; a ref whose tip is proven contained
in another origin ref may be removed under the existing containment rules.

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

The scheduled job uses
`git worktree remove --force` only as the final deletion step after all P0
guards and their final TOCTOU checks have passed; this removes disposable
ignored residue such as a worker `.venv`, not a bypass for cleanliness, PR,
task, or live-process guards. Unregistered directories with broken `.git`
pointers are reported as recovery candidates and are never deleted
automatically.

### Canonical preservation classes

The dual-repo reaper and scheduler categorize all worktrees into strict canonical preservation classes:

| Preservation class | Description | Default disposition |
|---|---|---|
| `primary` | Primary repository checkout root | Preserved |
| `active_dispatch` | Live process CWD, active task, active worker/rollover lease, write claim, or reap reservation | Preserved |
| `open_pr` | Worktree branch has an OPEN pull request | Preserved |
| `dirty` | Uncommitted modifications or untracked changes | Preserved as exception |
| `detached_unknown` | Detached HEAD or unverifiable branch state, and not `detached_clean_contained` | Preserved |
| `detached_clean_contained` | Clean, unlocked, detached `.worktrees/dispatch/<agent>/<task>/` checkout whose HEAD is already on origin, with only ignored caches or verified provisioned links (see below) | **Reaped** by `--safe-only` |
| `permission_error` | Filesystem permission denied during inspection or removal | Retained as exception |
| `foreign` | Outside repository `.worktrees/` subtree | Preserved |
| `unmerged` | Unpushed commits or lacking exact merged-PR / origin-main ancestry proof | Preserved |

### Aggregate-only public reporting

Public stdout emissions from both `scheduled_worktree_cleanup.py` and `reap_worktrees.py --aggregate` emit strictly aggregate summaries containing counts, owners, and retained exceptions with **zero host path dumps**. Full diagnostic receipts containing individual filesystem paths are written only to private local storage (`~/.codex/worktree-cleanup/receipts/v2/`) with strict owner-only permissions (`0600`/`0700`) for recovery.

P0 automatic reaping includes clean `.worktrees/` checkouts whose GitHub PR is
`MERGED` at the exact local head, or whose PR is `MERGED` and origin branch is
gone despite extra local reconcile commits after a squash merge. All P0 guards
still apply. The scheduled job also enables a separately
guarded terminal-dispatch class: only worktrees below `.worktrees/dispatch/`
whose task record is explicitly `done`, `failed`, or `no_deliverable`, whose PID
is dead, whose active-task and live-CWD probes are available and clear, and
whose GitHub query confirms no open PR. Set `LU_REAPER_TERMINAL_DISPATCHES=0`
to disable only this optional scheduled class during an incident; merged-clean
reaping remains enabled. Before removal the reaper writes an
append-only local journal, reserves the path as reap-pending, and creates a
`refs/reaper-rescue/...` ref. Set `LU_REAPER_DISABLED=1` to stop automatic
reaps immediately. Apply mode also recovers interrupted reap reservations:
new reservations record the holding PID, and recovery requires that PID to be
absent plus acquisition of the worktree attachment lock. Live or unverifiable
PIDs are retained regardless of age. Legacy reservations without a PID require
a timestamp at least one hour old, the exclusive sweep lock, and the attachment
lock. Malformed or future legacy timestamps remain reserved. A stable sidecar lock
serializes pending-state replacements so concurrent writers cannot lose entries.
Recovery journals `reservation-recovery` before releasing a reservation, then
reruns the normal safety proofs; dirty, active, or unmerged trees remain refused.
Dry runs and disabled reapers never release reservations. To recover one target,
use the existing `reap_worktrees --apply --merged --worktree <path>` command;
never edit `reap-pending.json` manually. Reservations for already removed trees
can also be released; no second deletion path is used.
The first seven days are capped by
`LU_REAPER_MAX_REAPS_PER_DAY` (default 25); when the eligible backlog of
fully safety-qualified worktrees exceeds the remaining daily budget, the cap
may expand up to a hard ceiling of 2x the configured base (journaled as
`cap-expansion` with the justifying backlog size; the ceiling is not
env-expandable). An approved policy lift uses
`LU_REAPER_LIFT_FIRST_CLASS_CAP=1`. Restore only to a new path under
`.worktrees/`:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
"$PRIMARY_REPO/.venv/bin/python" scripts/orchestration/reap_worktrees.py restore \
  --restore-ref refs/reaper-rescue/<timestamp>/<branch>-<sha> \
  --restore-branch <branch> \
  --restore-worktree .worktrees/dispatch/<agent>/<task>
```

For regular dispatch worktrees, `post_task_reap` delegates automatic removal
to this same P0 reaper rather than maintaining a second deletion path.

## Deletion ownership

Every worktree removal goes through one guarded chokepoint (#8610): Python
callers use `worktree_claims.remove_unclaimed_worktree`, and shell and YAML
callers use `python -m scripts.orchestration.worktree_claims remove PATH`
(`scripts/wt.sh clean`, the RB2 trail's `cleanup_failed_worktree`). Holding
the per-worktree lock dispatch holds from attach until its task record is
published, it runs the caller's ownership proof, proves a forced target clean,
refuses while another task's unfinished record names the checkout, and only
then calls `worktree_claims.git_worktree_remove`, the repository's one raw
`git worktree remove`. The P0 reaper's `_reap_qualified_worktree` calls that
raw remover directly, under the same lock and claim scan.
The shared remover checks approved deletion roots for forced removals. The
reaper also checks them explicitly for non-force continuation cohorts, including
approved scratch roots. Other non-force callers retain Git's ordinary removal
rules, including sibling worktrees created by `wt.sh` and task-family cleanup
when `TMPDIR` is unset.
`tests/orchestration/test_worktree_removal_invariant.py` fails on any other
removal call site under `scripts/`.

Callers and their ownership proofs:

- Regular dispatch worktrees: the P0 reaper. `post_task_reap`'s main path and
  `delegate`'s completed-worktree cleanup call it rather than removing
  anything themselves.
- `delegate` settle and superseded-review cleanup remove only a checkout the
  dispatch created. `delegate._release_stale_branch_holders` performs a
  non-force release after clean, synced, terminal-owner checks so a blocked
  dispatch may reattach its branch.
- `delegate._settle_failed_worktree_add` removes nothing. After its own
  failed or timed-out `git worktree add`, dispatch leaves the directory it
  reserved with `mkdir` as it is, empty or not, and reports it (see
  "Interrupted `git worktree add`" below).
- `post_task_reap._remove_acp_runtime_worktree` removes only task-state-bound
  ACP runtime paths below `.worktrees/dispatch/acp/`, after its own terminal,
  clean, and liveness checks; it forces for ignored runtime residue.
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

`delegate.py dispatch` refuses a `--cwd` or `--worktree` inside
`.worktrees/dispatch/acp/`: those runtimes belong to the ACP bridge and are
never a dispatch target.

### ACP runtime worktree ownership and abandoned-runtime reaping (#8344)

Every ACP runtime worktree is locked at creation with a reason of the form
`active ACP execution <label> (owner pid=<pid> start=<start>)`, where the
start time is field 22 of `/proc/<pid>/stat`. Any later process can prove the
owner dead without the owner's cooperation: pid absent, or pid recycled with
a different start time. Hosts without `/proc` record `start=unknown` and are
treated as unknown, never as dead. The proof assumes the ask and the reaper
share one PID namespace; a live owner inside a container or private namespace
can read as absent, so do not rely on it across namespace boundaries.

`reap_worktrees` reaps a `.worktrees/dispatch/acp/runtime-*` worktree under
`--apply` and `--safe-only` when it is detached, locked by an ACP reason, and:

- the lock carries owner information and the owner is provably dead; or
- the lock is a legacy owner-less ACP lock **and** the worktree is older than
  24h **and** the process-CWD probe is available and shows no live process
  inside.

The directory must hold exactly its `.git` pointer (no-checkout residue); any
other file preserves it. The class never consults PR state and re-proves
every precondition immediately before deletion. `acp_execution_cwd` also runs
the same dead-owner sweep on entry, before creating its own workspace, so a
killed ask's stub is gone by the next ACP call at the latest. As defence in
depth, the ask entry path converts SIGTERM into an orderly unwind
(`SystemExit(143)`) so the context `finally` cleans up when it can.

### Clean detached dispatch checkouts (`detached_clean_contained`)

A worker's baseline or scratch checkout (`git worktree add --detach`) holds
nothing unique once its commit is pushed, so it must not pile up on a
disk-limited host. `reap_worktrees` reaps it under `--apply` and `--safe-only`
(and in the default merged mode) when **all** of these hold:

- it is exactly `.worktrees/dispatch/<agent>/<task>/` with a detached HEAD,
  and is not an ACP runtime worktree;
- `git status --porcelain=v1 -z --ignored --untracked-files=all` succeeds and
  every entry is an **ignored** (`!!`) regenerable cache or verified
  provisioned link. The public `worktree_artifacts.is_disposable_path` interface
  owns the cache taxonomy at any depth outside real environments. Any staged,
  modified, renamed or untracked
  entry preserves the checkout. The only provisioned link paths are
  `data/sources.db`, `data/vesum.db`, `node_modules` and `site/node_modules`;
  each must be a symlink resolving to the same relative path in the primary
  checkout. Regular files, directories, links elsewhere, broken or looping
  links, and any additional non-disposable residue preserve the checkout.
  Removal unlinks these symlinks without removing their targets. Cache paths
  with a `.venv` or `node_modules` segment (even inside a `__pycache__/`) and
  loose `*.pyc` files outside `__pycache__/` preserve it. The allowlists are fixed and never consult
  `.gitignore` or `info/exclude`; a git failure preserves. Documented residual:
  a hand-made file placed inside an ignored known cache directory
  is treated as disposable;
- HEAD is an ancestor of `origin/main` or contained in some
  `refs/remotes/origin/*` ref (no age threshold, no task record needed);
- it is not locked, no live process has its working directory inside it, and
  no non-terminal task (`queued`, `starting`, `running`, ...) is bound to it;
  an unavailable active-task probe fails closed (preserved, reported as
  `active-task probe unavailable`), at qualification and again before removal;
- its PR state is not `OPEN`, consulted only as the same guard every class
  honours; the class's own proof never depends on PR state.

It goes through the same qualified-reap path as the other safe classes
(reap reservation, per-worktree lock, recovery ref, journal, daily cap) and
re-proves the conditions under the lock before removal. Everything else stays
in `detached_unknown` / `dirty` / `unmerged` and is preserved. Reason string:
`detached clean contained: HEAD <sha12> is <an ancestor of origin/main | contained in an origin/* ref>`.

### Review checkouts (#9129)

Native `codex exec` reviews and agent scratchpads leave clean checkouts that
no task record or branch ties to a settled task. Three further classes reap
them. Every one requires a tree holding only regenerable ignored caches or
verified provisioned links (the detached-class residue guard). The only
provisioned link paths are `data/sources.db`, `data/vesum.db`, `node_modules`
and `site/node_modules`; each must be an ignored symlink resolving to the same
relative path in the primary checkout. Removal unlinks these symlinks without
removing their targets. Regular files, directories, links elsewhere, broken
or looping links, staged, modified, renamed or untracked entries, and any
additional non-disposable residue preserve the checkout. Cache paths with a
`.venv` or `node_modules` segment (even inside a `__pycache__/`) and loose
`*.pyc` files outside `__pycache__/` preserve it too. Each class also requires
HEAD contained in a `refs/remotes/origin/*` ref, no lock, no live process cwd inside, no
unfinished task, and a known active-task probe. Under the per-worktree lock
each class is proved again from fresh state (residue, PR heads, age and task
record, detached HEAD for the detached classes) before removal, and
`--preserve-then-reap` keeps its rescue ref as for every other class.

- **Superseded PR checkout.** Detached HEAD is a commit of an open PR (named by
  the `review-<N>` path or found by commit search) but not that PR's current
  head. Reason `superseded PR #N head <old12> (current <new12>)`. A checkout
  AT an open PR's current head stays, and an unreadable PR head keeps it too.
- **Unrecorded detached checkout.** Detached, no task record, and no file
  changed in the last 2 h. Reason `unrecorded detached checkout`.
- **Foreign registration.** A registered worktree of this repo outside
  `.worktrees/`, strictly under `/tmp`, `/var/tmp`, `$TMPDIR` or a
  `scratchpad` directory. Reason `foreign registered checkout`. Any other
  outside path is still reported as `outside repo .worktrees/`.
  Qualification and the locked removal recheck also require a bounded
  `lsof +D` probe with no open file descriptors or mapped files inside the
  checkout, including nested mount points. An unavailable probe, warning,
  error or timeout preserves the checkout. An empty selection also requires
  readable process FD and mapping entries in procfs; partial visibility or
  a platform without that proof preserves it. Negative proof additionally
  requires the initial PID namespace and an unrestricted procfs mount;
  nested namespaces, filtered procfs mounts and process-entry overmounts
  preserve the checkout. Unprivileged runs that cannot inspect every process
  retain all foreign checkouts, including idle ones. Infra owns this cleanup
  residual until a complete process view is available through an authorized
  execution context; this check never changes host permissions.
  Its refusal reason contains no
  file paths. This probe complements the existing cwd and lock checks.
  Long readers such as backups should take `git worktree lock --reason
  "long reader" <checkout>` before reading and `git worktree unlock
  <checkout>` after they finish. Hold the lock for the entire read, including
  gaps between opened files: a point-in-time activity probe cannot protect
  future reads. Unlock only the lock that the reader owns.

### Interrupted `git worktree add` (#8663)

`delegate.py` bounds `git worktree add` by `DELEGATE_WORKTREE_ADD_*` in
`scripts/config.py`: a base window, then more time only while the checkout is
still gaining files, up to a hard ceiling. The add runs in the C locale (so
git's lock reason is the literal `initializing`) in its own process group.

Stopping a slow add:

1. SIGTERM goes to the add's process group. Git's signal handler deletes the
   worktree directory and admin directory it was building; the branch ref is
   kept. Tests prove this on the host git (2.53.0) with SIGTERM before the
   checkout starts, at its first file, mid-checkout and at its last file.
2. Dispatch waits up to `_WORKTREE_ADD_STOP_GRACE_S` (30 s) for git to exit.
   SIGKILL follows only after that grace.
3. Dispatch worktree preparation removes nothing, not even the empty
   directory it reserved with `mkdir`. Git 2.53 can write another add's
   admin registration while that directory is still empty and before its
   `.git` exists, so an `rmdir` could disrupt that add. The directory stays
   as it is; `worktree_prep.reserved_dir_left: true` and the failure output
   record that it was left. An empty, unregistered one is later swept by the
   reaper's existing zero-file dispatch-husk rule
   (`reap_worktrees._reap_dispatch_husks`, described at the end of this
   section, with its one-hour age floor).

Before git starts, dispatch reserves the path with `mkdir`: a path that
already exists is never passed to git and never removed. Dispatch also
records the reservation as `worktree_prep` in the task record. The record
holds the path, `dir_dev`/`dir_ino`, `base_sha`, the dispatcher's
`owner_pid`/`owner_start`, and git's `git_pid`/`git_start` (start time from
`/proc/<pid>/stat` field 22). The failed task record keeps `worktree_prep`
and stores the outcome as `worktree_prep_cleanup`.

**Nothing removes, unlocks or prunes a registered worktree automatically.**
Dispatch and the reapers both follow this rule. Three review rounds tried to
prove ownership well enough for automatic removal, and each proof left a race
in which a foreign or completed worktree could qualify. A leftover can happen
when git was SIGKILLed, when its cleanup failed, or when the dispatcher died
mid-add. It stays registered and locked `initializing`, and it is reported as
`needs_attention: initializing_leftover`:

- dispatch's `worktree_prep_cleanup` and its stderr carry `needs_attention`
  and the command;
- `reap_worktrees` reports a dispatch worktree locked `initializing` whose
  task record carries `worktree_prep` for that path. The row is `skipped`,
  its reason starts with `needs_attention: initializing_leftover`, and
  `needs_attention` holds the evidence. The aggregate output lists it under
  "Needs attention", the Monitor GC sweep summary under `needs_attention`,
  and every pass appends a `needs_attention` journal event. No other class
  sees the worktree. While the reserving dispatch may still be running its
  add, the row says so instead;
- `post_task_reap` routes such a task's worktree to that report. Its JSON
  carries a top-level `needs_attention` list.

The evidence (`worktree_prep.leftover_evidence`) covers:

- the `worktree_prep` facts;
- whether the directory is still the reserved inode;
- whether the recorded git add (and its process group) and the dispatcher
  are proven gone;
- HEAD against `base_sha`;
- a `git status` summary.

To act on a leftover:

1. Check the evidence. Git and the dispatcher should be gone and nothing
   should be running inside the worktree. HEAD should be the base commit,
   and the status should show only a partial checkout (deleted and untracked
   files).
2. Only then run the reported command, which starts with `verify first:`:
   `git -C <repo> worktree unlock <path> && git -C <repo> worktree remove --force <path>`.
   The branch ref is not touched.

The dispatcher's `owner_pid`/`owner_start` serve one more purpose. While
`git worktree add` runs, the task record says `spawning` with `pid: null`. If
the dispatcher dies before writing a terminal record, two paths mark it
`crashed` with `returncode_reason: dispatch_died_during_worktree_prep` once
the owner is proven gone (`worktree_prep.is_orphaned_prep_record`): the lazy
heal in `delegate.py status|wait|list`, and `reconcile_sweep --apply`. The
ownership ledger stops counting such a record immediately.

Unregistered directories under `.worktrees/dispatch/<agent>/` that contain
zero files (empty placeholder trees, e.g. only `site/ node_modules/ data/`
subdirectories) are reported as `would_remove` husks and removed under
`--apply`. A directory containing any file, symlink, or git metadata is never
removed by this rule. The rule fails closed on every other guard too: an
unavailable process-CWD probe skips the directory, a live process cwd inside
preserves it, and it must be at least one hour old measured by the newest
mtime anywhere in its subtree — a directory a concurrent `delegate.py` is
still provisioning (created before `git worktree add` registers it) is never
"old". Husk removals, dry-run observations, and skips are recorded through
the same `reaper_lifecycle` journal as every other reaper action.

## Before re-firing a task id

A detached `delegate.py dispatch` launcher that is still grinding from a prior
attempt can finish after you re-fire the same task id, leaving two workers on
one worktree (the task record points at the newer pid; the older process is an
orphan). Before re-using a task id, kill any stale detached launcher for it:

```bash
/bin/ps -axo pid,etime,command | grep 'delegate.py dispatch .*--task-id <id>'
```

Confirm the match is the stale launcher, then terminate that pid before the
new dispatch.

## Immediate cleanup after merge

The merge owner closes out the exact PR as soon as GitHub reports it `MERGED`, using
`scripts.orchestration.merge_closeout` — not the P0 reaper directly. This is the one
command that proves the PR MERGED, finds every worktree tied to it (by branch, by
exact merged head SHA, or by an earlier commit that exists only on that PR, including
detached review-checkout siblings), reaps each one
through the P0 reaper, and proves the remote and local branch are both gone. Run it
from a separate shell after every agent, editor, server, and terminal has left the
target worktree(s):

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

Default is dry-run; pass `--apply` to actually reap and delete. `--json` emits a
machine-readable payload. `merge_closeout` introduces no second deletion hand for the
worktree step: it delegates removal to `scripts.orchestration.reap_worktrees` with
`--merged`/`merged_pr_only` and an exact `--worktree` target per match — never
`--force`, never a second ad hoc `git worktree remove`. It exits non-zero if the PR
cannot be proven `MERGED`, if any reap fails, or if the remote or local branch is
still present after `--apply` ran (residual branches are reported, never
force-deleted past an exact-head-match proof).

The underlying reap step validates GitHub PR state, PR-head or origin-branch-gone
evidence, local HEAD, cleanliness, task state, and process activity. A skipped
worktree is a blocker, not permission to retry with `--force`.

The live-process check intentionally includes the invoking process tree. A
cleanup launched from inside the target worktree therefore self-protects and
must be retried from the primary checkout after that process exits. If `lsof`
cannot inspect process working directories, apply mode fails closed; resolve
the local macOS permission or tooling problem before retrying.

The canonical PR lifecycle trail already performs worktree-first cleanup after
merge. Other merge owners must invoke the exact command above before declaring
closeout complete.

Git closeout for **every** merge is exactly three things: worktree reaped,
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

1. fetches `origin` and prunes deleted remote refs;
2. prunes stale Git worktree registrations;
3. automatically removes only clean, inactive worktrees with exact merged-PR
   head evidence (including same-tree squash siblings) or MERGED PR evidence with
   the origin branch gone, plus the terminal-dispatch
   class described above; open or GitHub-unknown PR state remains a hard skip;
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
7. runs `git gc --auto`;
8. writes an immutable JSON receipt.

Dirty worktrees, open PRs, active/non-terminal tasks, checked-out branches, and
unmerged branch heads remain untouched.

```text
~/.codex/worktree-cleanup/receipts/v2/
```

An unavailable fetch or process-activity probe blocks apply for that
repository. Standard output contains the same summary as the receipt.

## Linux systemd default

The shipped `packaging/systemd/learn-ukrainian-worktree-gc.service` passes
`--apply`, the same as macOS launchd. Its timer fires every 4 hours
(`OnUnitActiveSec=4h`, matching the launchd cadence below) using the existing
cleanup wrapper and P0 reaper; this adds no daemon or cleanup class, and the
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

After installation, inspect the first receipt and confirm that protected
worktrees appear as `skipped`, not `removed`. A venv rebuild does not require
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
