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

Install the units after merge, from the primary checkout:

```bash
.venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --check
.venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --apply --enable
journalctl --user -u learn-ukrainian-tmp-sweep.service -n 50
```

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
- No inspectable live process has its working directory or an open file at
  or below the entry.
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

The sweep reads `/proc/<pid>/cwd` and `/proc/<pid>/fd` for every process. The
kernel refuses some of these reads, for example root daemons and non-dumpable
session processes such as the user's systemd manager or SSH sessions. For the
scratch class only, a refusal is tolerated, which matches what the operator's
manual rule could see. Any other read failure stops the scratch class with
`liveness_unknown`. Task-attributed entries still need a complete probe.

### Safety mechanics

- The sweep never follows symlinks and never crosses a device or mount point.
  It refuses a temp root outside `/tmp`, `/private/tmp` or `/var/tmp`.
- Removal goes through the common reaper,
  `retention_engine.reap_attributed_temp`. That function removes directories
  with the descriptor-safe task-scratch remover. It unlinks files by
  descriptor after it rechecks device/inode identity, owner, hard-link count
  and mount state.
- Before any removal, `--apply` reclassifies the entry. It then takes one
  last process and task-record probe straight before the reaper. If anything
  changed, the entry is kept (`proof_changed` or
  `final_liveness_or_task_changed`).

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
