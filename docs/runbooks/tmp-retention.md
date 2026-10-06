# Temp scratch retention and batch_state staleness

Operator retention decision, 2026-10-06 (#9737). A daily user timer removes
agent scratch from the system temp area that no task owns and that has gone
quiet. It also prints a report of stale `batch_state/` directories. The report
never deletes anything.

## What runs

`learn-ukrainian-tmp-sweep.timer` runs once a day at 05:30 UTC, with up to
15 minutes of random delay. Missed runs catch up. It starts
`learn-ukrainian-tmp-sweep.service`, which runs two steps in order:

1. `scripts.hygiene.batch_state_retention`: the read-only staleness report.
2. `scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary`: the
   sweep. It logs counts and byte totals only, never entry names.

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
- Removal goes through the common reaper,
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
     rename itself sets it.

   The order matters. A process that holds the entry during the process scan
   is found. A process that does not hold it at that point can no longer
   reach it, so any write it made happened before the scan and shows in the
   tree comparison that follows.
3. If anything is found or unknown, the entry is renamed back to its
   original name and kept with a `quarantine_*` reason. If that name has been
   taken in the meantime, the entry stays in the quarantine as
   `restore_blocked` and counts as an error; it is never deleted. Otherwise
   the common reaper removes it from the quarantine.
4. At start, a quarantine left by a crashed run is not deleted. Its snapshot
   died with that run, so its write check is unknown, and each entry is
   renamed back to its original name (`quarantine_restored` in the report).
   It then meets every check again as an ordinary candidate. A quarantine
   still locked by a live run is left alone. A dry run only lists leftovers
   as `quarantine_leftover`.

Remaining gap, inside the boundary: after the re-check, a process of the same
user could still open the entry by deliberately listing the temp root and
entering the sweep's own quarantine directory. A descriptor in flight inside
a Unix socket message belongs to no process and is invisible to any `/proc`
scan.

### Run it by hand

```bash
# Dry run: counts and bytes only
.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --summary
# Full local inventory (contains entry names; keep it out of public issues)
.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --json
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
