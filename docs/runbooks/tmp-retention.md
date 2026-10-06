# Temp scratch retention and batch_state staleness

Operator retention decision, 2026-10-06 (#9737). A daily user timer removes
agent scratch from the system temp area that no task owns and that has gone
quiet. It also prints a report of stale `batch_state/` directories. The report
never deletes anything.

Removal is recoverable (#9887): the sweep moves an entry into a quarantine,
records it in an append-only ledger first, and deletes it only after 7 days,
when the same checks still pass. Until then `tmp_sweep restore <ledger-id>`
puts it back. See [Deletion ledger and quarantine](#deletion-ledger-and-quarantine).

## What runs

`learn-ukrainian-tmp-sweep.timer` runs once a day at 05:30 UTC, with up to
15 minutes of random delay. Missed runs catch up. It starts
`learn-ukrainian-tmp-sweep.service`, which runs two steps in order:

1. `scripts.hygiene.batch_state_retention`: the read-only staleness report.
2. `scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary`: the
   sweep. It purges expired quarantine entries, then quarantines newly proven
   ones. It logs counts and byte totals only, never entry names; the ledger
   holds the names.

The service has no network: `RestrictAddressFamilies=AF_UNIX` refuses every
IPv4 and IPv6 socket. `PrivateNetwork=yes` is not used, because the user
manager accepts it without isolating anything. `IPAddressDeny=any` is set as
well, but a user manager does not enforce it either.

Install the units after merge, from the primary checkout:

```bash
.venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --check
.venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --apply --enable
journalctl --user -u learn-ukrainian-tmp-sweep.service -n 50
```

The installer refuses a symlinked unit file, and a symlink in any directory
from the home directory down to the unit directory; the error names the
component.

## The temp-scratch rule

`tmp_sweep` considers only direct children of the temp root. With
`--unattributed-scratch`, an entry that no task owns is removed only when all
of these hold:

- It is a regular file or a real directory. Symlinks, sockets, FIFOs and
  devices are kept. A directory that contains a socket or FIFO is kept.
- The agent user owns the entry and everything inside it.
- The entry itself is older than `--scratch-age-hours` (default 24), and
  nothing inside it was written for `--scratch-quiet-hours` (default 24).
  Inode change time counts as a write. An archive extracted an hour ago
  therefore stays young, even though its files keep their old mtimes.
- Every live process could be inspected, and none has its working directory,
  an open file or a memory-mapped file at or below the entry.
- Every current task record could be read. No unsettled task names the entry,
  a path inside it, or the temp root itself in any path value, such as
  `runtime_tmp_root`, `worktree_path`, `cwd` or an environment value.
- The name does not start with `.`, `claude-`, `tmux-`, `ssh-` or
  `systemd-`, and it is not a harness runtime name (`codex-`, `gemini-` and
  the like).
- The entry is not managed scratch (`LU_SCRATCH_ROOT`, the runtime temp base,
  `TMPDIR`), not a registered worktree, holds no `.git` metadata, has no
  hard-linked content, and is not on another device or a mount point.

An entry whose name maps to a dispatch task still follows the task rules from
#8755: it goes only once that task has settled. The scratch rule never
overrides a task that is still unsettled.

### Process coverage

The sweep reads `/proc/<pid>/cwd`, `/proc/<pid>/fd` and `/proc/<pid>/maps`
for every process.
The kernel refuses some of these reads. Examples are other users' processes,
such as root daemons, and non-dumpable processes of the agent user, such as
its systemd manager or SSH sessions. A process that cannot be read could hold
any entry. Any refusal therefore makes the probe incomplete, and every
candidate in both classes is kept as `liveness_unknown`.

Consequence: an unprivileged user cannot read root's processes on a normal
Linux host. The probe is then never complete, so the timer reports what it
would remove and removes nothing. Reclaiming space needs a liveness probe
that can read every process. Such a probe is a new privileged design, and it
needs operator or advisor approval before anyone builds it.

No single read capability makes the probe complete (#9887, measured with
transient units running as the agent user under `NoNewPrivileges=yes`).
`/proc/<pid>/fd` is a mode-0500 directory owned by the target process, so
listing it takes `CAP_DAC_READ_SEARCH`. Resolving `cwd`, the descriptor links
and `maps` is a ptrace read-access check, so it takes `CAP_SYS_PTRACE`. With
either capability alone the probe stays incomplete; it is complete only with
both. `CAP_SYS_PTRACE` also allows attaching to any process and writing its
memory through `/proc/<pid>/mem`, so it is not a read-only privilege. Because
the issue's stop rule allows one narrow read privilege at most, no system unit
ships. The sweep keeps running as the user unit until the operator decides.

### Task coverage

The sweep reads every `*.json` record in the task directory. Superseded
`<task>.<stamp>.archived.json` runs claim nothing. If the directory is
missing or unreadable, or a current record is unreadable, malformed,
symlinked or names a different task, the inventory is incomplete. An
otherwise removable entry is then kept as `task_inventory_unknown`. An entry
that an unsettled task references by path is kept as `task_reference`.

### Safety mechanics

- The sweep never follows symlinks and never crosses a device or mount point.
  It refuses a temp root outside `/tmp`, `/private/tmp` or `/var/tmp`.
- Final deletion, at purge time, goes through the common reaper,
  `retention_engine.reap_attributed_temp`. That function removes directories
  with the descriptor-safe task-scratch remover. It unlinks files by
  descriptor after it rechecks device/inode identity, owner, hard-link count
  and mount state.
- Before any removal, `--apply` records a snapshot of every node in the entry
  (identity, type, links, owner, size, mtime and ctime), then reclassifies the
  entry; any difference keeps it as `proof_changed`.

### Consistency boundary: quarantine, verify, then delete

Removal crosses one defined boundary: a rename.

1. The sweep renames the proven entry, atomically and without replacing
   anything (`renameat2` with `RENAME_NOREPLACE`), into this run's quarantine
   directory: `.lu-tmp-sweep-quarantine-<random>` inside the same temp root,
   owner-only and locked for the run. The leading dot keeps it out of the
   sweep's own candidates. If the rename fails (`EXDEV`, `EBUSY`, `ENOENT`,
   permission), the entry stays where it is as `quarantine_failed`, with the
   error code.
2. After the rename, opening the old path fails with `ENOENT`. This is the
   standard behaviour of a temp cleaner: a process that still wants the entry
   by its old name finds it gone, just as if it had been deleted. No process
   can newly reach the entry by that name. The sweep then re-checks the
   quarantined entry in a fixed order:
   - the task inventory: complete, attribution unchanged, and no unsettled
     task names the old or the new path;
   - every process: working directory, open files and memory maps. A holder
     that opened the entry before the rename is found at its new path. Any
     process that cannot be inspected makes the result unknown;
   - the tree: the snapshot taken again must equal the one taken before the
     rename, node by node. Any write, truncate, create, delete or metadata
     change sets a node's ctime, so this is the recent-write check against
     the pre-rename state. Only the top-level ctime is left out, because the
     rename itself sets it. In its place the snapshot records the top-level
     entry's extended attributes and, for a regular file, a SHA-256 digest of
     its bytes, read without touching atime. A same-size rewrite with the
     mtime put back, through a descriptor opened before the rename, therefore
     still differs, whether it lands just before the rename or during the
     final process scan. A directory's contents are its descendants, whose
     ctimes are kept. An entry that cannot be read is unknown and kept.

   The order matters. A process that holds the entry during the process scan
   is found. A process that does not hold it at that point can no longer
   reach it, so any write it made happened before the scan and shows in the
   tree comparison that follows.
3. If anything is found or unknown, the entry is renamed back to its
   original name and kept with a `quarantine_*` reason. If that name has been
   taken in the meantime, the entry stays in the quarantine as
   `restore_blocked` and counts as an error; it is never deleted. Otherwise
   the entry stays in the quarantine (`quarantined`) for the retention
   window; nothing is deleted in this step.
4. At start, a quarantined entry with no ledger record (a run from before the
   ledger, or a lost ledger) is not deleted. There is nothing to re-verify it
   against, so it is renamed back to its original name (`quarantine_restored`
   in the report) and meets every check again as an ordinary candidate. A
   quarantine still locked by a live run is left alone. A dry run only lists
   such leftovers as `quarantine_leftover`. Ledgered entries follow the
   reconciliation rules below.

Residuals outside the boundary: after the re-check, a process of the same
user could still open the entry by deliberately listing the temp root and
entering the sweep's own quarantine directory. A descriptor in flight inside
a Unix socket message belongs to no process and is invisible to any `/proc`
scan. Both are outside what the boundary observes, and stay residuals.

### Deletion ledger and quarantine

Code: `scripts/hygiene/tmp_sweep_ledger.py` (ledger, manifest) and
`scripts/hygiene/tmp_sweep.py` (passes and CLI).

**Where.** `$XDG_STATE_HOME/learn-ukrainian/tmp-sweep/ledger.jsonl`, or
`~/.local/state/learn-ukrainian/tmp-sweep/ledger.jsonl` when
`XDG_STATE_HOME` is unset (`--state-dir` overrides). The sweep refuses a
ledger directory under the temp root or inside the repository, so cleaning
the temp area never removes the record. Directory mode 0700, file mode 0600.
The summary shows the location as `ledger_path`.

**How it is written.** One JSON object per line, schema
`tmp-sweep-ledger.v1`. Each write opens the file with `O_APPEND`, writes one
whole record and calls `fsync`. Records are never rewritten. If a crash left
a torn last line, the next write first ends it with a newline, so it stays
one malformed line (`ledger_malformed_lines`) and never merges with a new
record. Apply runs and restores hold `ledger.lock`, so only one writer runs
at a time; a restore during a sweep is refused with exit code 1.

**Durability.** `fsync` on a file does not persist the directory entry that
names it, so every change to a directory entry is followed by an `fsync` of
the directory before any record says it happened: each newly created ledger
directory or ancestor (its parent is synced), the ledger file on creation,
each new quarantine directory (the temp root), every rename (its source
directory, then its destination), and every purge (the quarantine directory).
If a sync fails, the run stops with exit code 1 and the step stays
unconfirmed in the ledger; the next run reconciles it as below.

**What a removal records.** The `quarantine` record is written and synced
before the rename. It holds:

| Field | Meaning |
| --- | --- |
| `ledger_id`, `run_id`, `at` | Entry id (12 hex), the sweep run, UTC time |
| `original_path`, `quarantine_path` | Where it was and where it now is |
| `owner_uid`, `identity` | Owner, and device and inode (a rename keeps them) |
| `kind`, `reason`, `task` | File or directory, why it was proven removable, owning task if any |
| `allocated_bytes`, `total_bytes`, `file_count` | Disk use, sum of file sizes, number of regular files |
| `newest_mtime`, `newest_ctime` | Latest write and change anywhere inside (UTC) |
| `digest_limit_bytes`, `digest_skipped_files`, `manifest` | Per node: relative path (`.` is the entry), type, mode, mtime (ns); files add size and SHA-256, or `digest_skipped_size` above the limit (default 64 MiB, `--digest-limit-mib`; counted in `digest_skipped_files`); symlinks add their target |

Every later step appends a short record with the same `ledger_id`:
`quarantined` (re-verified after the rename, retained), `returned` (the
re-check found something; renamed back), `return_blocked`,
`quarantine_failed`, `purge` then `purged` (or `purge_failed`),
`purge_kept_ambiguous`, `restore` then `restored` (or `restore_failed`), and
`reconciled` with an `outcome`.

**Reconciliation after a crash.** At the start of each apply run, every
entry whose last record leaves its location open is resolved by where its
inode actually is, and the result is appended. A step that stopped at a
directory sync looks exactly like one that finished, so before any record
that confirms a step the run syncs both directories involved again (the
quarantine directory, if it still exists, then the original's directory);
a failed sync stops the run with nothing recorded. Likewise the first record
of every run or restore is preceded by syncing the ledger directory and the
parent of each of its ancestors owned by this user on the same filesystem,
so a directory created by an earlier run whose sync failed is made durable
before anything is written into it.

- `quarantine` record but the inode is still at its original path: the
  rename never happened, `reconciled` / `at_origin`.
- `quarantine` record and the inode is in quarantine: it was never
  re-verified after the rename, so it is renamed back, `reconciled` /
  `returned` (or `return_blocked` while the name is taken; retried each run).
- `purge` record and the inode is gone: `reconciled` / `purged`. If it is
  still there, the purge pass retries it (see Purge).
- `restore` record: `restored` (verified now) if it is back at its path,
  otherwise `restore_failed`.
- A retained entry that vanished (for example, a reboot cleared a tmpfs
  `/tmp`): `reconciled` / `missing`.

A dry run changes nothing and lists such entries as `ledger_unreconciled`.

**Purge.** Before scanning for new candidates, each apply run looks at
retained entries older than `--quarantine-days` (default 7). Each one is
re-checked under the same predicates as the boundary, against its quarantine
location: a complete task inventory naming neither path, a complete process
scan with no holder, the tree safety facts, no change time after its
`quarantined` record, and a manifest equal to the recorded one. Only then is
a `purge` record written, the common reaper deletes it, and a `purged`
record follows. Anything else keeps it with a typed reason
(`purge_live_process`, `purge_liveness_unknown`, `purge_task_reference`,
`purge_task_inventory_unknown`, `purge_recent_write`,
`purge_manifest_changed`, `purge_<tree reason>`, `purge_refused`). A dry
run reports what would go as `would_purge`. Files above the digest limit
pass the manifest check on size and mtime; together with the change-time
check that is the purge's evidence for them.

A purge that stopped part-way (`purge_failed`, or a crash after the `purge`
record) is retried under the same holder and task checks, and only if its
tree is provably untouched: every recorded node still present, equal to its
record, with no change time after the `quarantined` record, and nothing new.
That holds when the purge failed before deleting anything. Once it deleted
part of the tree, the directories that lost children changed, and the sweep
does not try to tell that change from anyone else's (an extended attribute,
say, is not recorded). The safe default wins: the survivors are kept, never
deleted on a guess.

**`purge_kept_ambiguous`.** Such an entry (also one whose tree cannot be
read) gets a `purge_kept_ambiguous` record and stays in quarantine with that
state. It is never purged automatically. Every apply run lists it as
`purge_kept_ambiguous`, counts it in `errors` (exit 1) and in
`quarantine_kept_ambiguous_entries`, until a person disposes of it, in
either of two ways:

1. Restore it (preferred): `.venv/bin/python -m scripts.hygiene.tmp_sweep
   restore <ledger-id>` renames what survives back to the original path; the
   result reports `mismatch` and lists what is missing or changed (exit 1 is
   expected here). Inspect it there. Anything left becomes an ordinary
   candidate again, and a later run quarantines it with a fresh manifest and
   purges it after the window.
2. Remove it by hand, after inspecting it: delete the `quarantine_path`
   shown by `tmp_sweep quarantine`. The next apply run records the entry as
   `reconciled` / `missing`.

**Restore.** `restore <ledger-id>` works for a retained entry. It refuses if
anything exists at the original path, then renames the entry back with
`renameat2(RENAME_NOREPLACE)`, so a path created in between is never
replaced (`restore_failed`, `EEXIST`). It then compares the restored tree
with the manifest and reports `verification`, which the `restored` ledger
record carries too:

| `verification` | Meaning | Exit code |
| --- | --- | --- |
| `verified` | Every node matches and every file was hashed: byte-identical | 0 |
| `unverified_digest_skipped` | Every node matches, but files above the digest limit matched by size and mtime only, which cannot prove their bytes (`digest_unverified` lists them); `verified` is false | 3 |
| `mismatch` | Restored, but different (`mismatches` lists the paths) | 1 |
| `unreadable` | Restored, but the tree could not be read | 1 |

A refused or failed restore also exits 1; an unknown ledger id exits 2.

**Report fields.** `ledger_path`, `quarantined_entries` and
`bytes_quarantined` (this run), `quarantine_held_entries` and
`quarantine_held_bytes` (all retained entries for this temp root),
`quarantine_kept_ambiguous_entries` (retained entries waiting for a person,
see above), `purgeable_entries` and `bytes_purgeable` (dry run), `purged_entries` and
`bytes_reclaimed` (bytes actually freed this run). `projected_free_bytes`
is free space plus `bytes_purgeable`: a newly quarantined entry frees nothing
until its purge.

**Residuals.** On a host whose `/tmp` is a tmpfs, a reboot empties the
quarantine together with everything else in `/tmp`; the ledger survives and
records those entries as `missing`. A rewrite with identical bytes and the
mtime put back, within one kernel clock tick after the `quarantined` record,
leaves no trace, but by definition it leaves the content unchanged. Above the
digest limit, a same-size rewrite with the mtime put back is not detected by
the manifest; the purge still sees its change time, and a restore reports
such files as unverified rather than identical.
The ledger is never compacted.

### Run it by hand

```bash
# Dry run: counts, bytes, ledger location, quarantine and purge counts
.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --summary
# Full local inventory (contains entry names; keep it out of public issues)
.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --json
# What was removed: by path substring, date or run
.venv/bin/python -m scripts.hygiene.tmp_sweep ledger --path my-scratch --since 2026-10-01
.venv/bin/python -m scripts.hygiene.tmp_sweep ledger --run-id <run-id> --json
# What is held now, with age, size and purge date
.venv/bin/python -m scripts.hygiene.tmp_sweep quarantine
# Put one entry back
.venv/bin/python -m scripts.hygiene.tmp_sweep restore <ledger-id>
```

### Hold a temp path

There is no hold list for temp scratch. Anything worth keeping does not
belong in the system temp area. To keep a path, do one of the following:

- Move it under `batch_state/` and, if it is evidence, add it to the
  retention list (see below).
- Keep a process attached to it, for example a shell whose working directory
  is inside it.
- Give it an excluded name prefix only when it really is harness or session
  state.

## The batch_state staleness report

`scripts.hygiene.batch_state_retention` lists every top-level `batch_state/`
directory with no write for 7 days (`--stale-days`). For each one it shows the
allocated size and the date of the newest write. It skips `tasks/`,
`preserved/`, `reports/` and `branch-archive/`. It never deletes anything.
Cleanup stays a separate, deliberate action.

### Hold evidence in batch_state

Add an entry to `scripts/hygiene/batch_state_retention.json`. Land it with a PR
that cites the issue the evidence serves:

```json
{
  "path": "batch_state/<dir>/<subpath>/",
  "reason": "Evidence for #NNNN.",
  "until": "#NNNN closes"
}
```

A hold anywhere below a top-level directory makes the report show that whole
directory as `held`, not `stale`. When the condition in `until` is met,
remove the entry. A malformed list makes the report exit with code 2, so a
hold is never ignored without notice.
