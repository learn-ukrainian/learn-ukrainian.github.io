# Atlas VPS job protocol

**systemd on the host is the source of truth; the local registry is a
journal/mirror.** Never treat a laptop JSON row as the mutex.

Plan a long-running Atlas job, **register it**, run it on a named host, then
**close it with a result**. No SSH-and-hope. No orphan systemd units. No
“finished” without a receipt. No empty-summary success.

This wraps `launch_reenrich_class_b_remote.sh`. It is not a second message bus
and not a Hetzner snapshot.

## Hosts

| Host | Use | Never |
| --- | --- | --- |
| `atlas-runner` | Reenrich, later ULIF / slovnyk migrate | Teacher API, GH runners |
| `hramatka` | Teacher API, Caddy, CI runners | Catalog reenrich / slovnyk refetch |

Default `ATLAS_RUNNER_HOST` is **`atlas-runner`**. A plan that puts `reenrich`
on `hramatka` is rejected (no override).

SSH aliases live in the operator `~/.ssh/config`. IAC: private
`hramatka/ops/iac/` (merged #495).

## Lifecycle

```
planned → submitted → running → {succeeded | failed | timeout | rejected | needs_finalize | crashed}
```

- `submit` checks `systemctl --user list-units 'atlas-job-*'` over SSH before
  accept. The **unit is the mutex**; the registry only journals.
- `--no-poll` only detaches systemd-run. The journal row stays `running` until
  `close` **or** `status` reconciles: unit inactive + journal `running` ⇒
  `needs_finalize` (or `crashed` when `resume: never` and no exit-status file).
- Units get `Restart=no`, optional `RuntimeMaxSec=` from `timeout_seconds`, and
  `ExecStopPost=` writing `exit-status.json` next to the per-job workdir.
- A unit that exits 0 with `consecutive_misses == targets` or a tripped
  circuit breaker is **failed**.
- `close` without summary evidence **and** without host exit-status ⇒
  `needs_finalize` (non-zero). Empty `{}` is never success.

Registry (gitignored, restic-covered): `batch_state/atlas-jobs/<id>.json`  
Result: `batch_state/atlas-jobs/<id>.result.json`  
Schema-capped git receipt: `batch_state/atlas-jobs/receipts/<id>.json`  
Remote unit: `atlas-job-<id>.service` (never reuse `atlas-class-b-reenrich.service`)  
Remote workdir: `$ATLAS_RUN_ROOT/run-atlas-job-<id>` (per job; set via
`ATLAS_RE_ENRICH_WORK_DIR`)

`status --audit` uses systemd MainPID / unit membership first; `pgrep` is
secondary. A matching process with **no** tracked running unit/row is exit 2.
Unreachable SSH is an error, never a clean empty list.

## Plan (`atlas-job.v1`)

Required: `id`, `host`, `kind`, `denominator`, `pointer_write: false`,
`result_sink` (`git` | `restic` | `both`), `success.circuit_breaker`,
`success.min_filled`, **`issue`** (one GitHub issue per campaign/kind — not
per job).

Optional: `resume` (`idempotent` | `checkpoint` | `never`, default `never`),
`timeout_seconds` (default 86400), `args`, `slugs_file`.

`pointer_write` is always false here. Publish / pointer flip is a later gate.

## Result sinks

| Sink | What comes back |
| --- | --- |
| `git` | Schema-capped receipt (~10 KB allowlist). Reject absolute paths / hostnames / credential-like text. Never commit manifests, slovnyk cache, or `sources.db`. |
| `restic` | `durable_mirror.py snapshot` → primary `data/lexicon/runner-mirror/<id>/` then `backup-data.sh backup --execute`. Result field: `backup: {attempted, ok, snapshot_id\|error}`. |
| `both` | Both of the above. |

Backup failure policy:

- Job keeps its real outcome (`succeeded` / `failed` / …).
- Close exit is non-zero when a required restic sink fails (`delivery: failed`).
- **Never delete** the remote workdir on backup fail.
- Schema-capped git receipt still lands.
- New restic-sink submits are refused until `backup-data.sh doctor` is green
  (`.restic-sink-blocked` gate).
- Doctor/backup always target the **primary checkout** (`LU_BACKUP_PROJECT_ROOT`
  via git common-dir) and load `~/.secrets/learn-ukrainian-backup.env` when
  present — dispatch worktrees lack `.agent` / `.claude/*-epic` recovery roots.

`pulled` is true only after `pull()` actually ran successfully.

## Monitor API

Thin facade on the existing Monitor app (no new daemon):

| Method | Path | Wraps |
| --- | --- | --- |
| GET | `/api/atlas-jobs` | list |
| POST | `/api/atlas-jobs/submit` | validate + host check + submit |
| GET | `/api/atlas-jobs/{id}` | status reconcile |
| POST | `/api/atlas-jobs/{id}/close` | close |

## Commands

Use the shared project interpreter (never bare `python`):

```bash
.venv/bin/python -m scripts.lexicon.runner.atlas_job validate PLAN.json
.venv/bin/python -m scripts.lexicon.runner.atlas_job submit PLAN.json
.venv/bin/python -m scripts.lexicon.runner.atlas_job status --host atlas-runner --audit
.venv/bin/python -m scripts.lexicon.runner.atlas_job close JOB_ID --summary-file summary.json
.venv/bin/python -m scripts.lexicon.runner.atlas_job pull --host atlas-runner --job-id JOB_ID
.venv/bin/python -m scripts.lexicon.runner.atlas_job list
```

`submit` refuses a second active `atlas-job-*` unit on the host. `close` seals
a result after the unit is dead (or records `needs_finalize` when evidence is
missing).

## Memory

The existing launcher still pins `MemoryHigh=1.5G` / `MemoryMax=2G` on the
cx33. One heavy job. Two full-catalogs need a later host or a queue.
