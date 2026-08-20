# Atlas VPS job protocol

**systemd on the host is the source of truth; the local registry is a
journal/mirror.** Never treat a laptop JSON row as the mutex.

Plan a long-running Atlas job, **register it**, run it on a named host, then
**close it with a result**. No SSH-and-hope. No orphan systemd units. No
“finished” without a receipt. No empty-summary success.

This wraps `launch_reenrich_class_b_remote.sh`. It is not a second message bus
and not a Hetzner snapshot.

## Hosts

Atlas jobs may run on **both** `atlas-runner` and `hramatka` (operator GO
2026-08-17). Each host is its own mutex — `submit` refuses a second active
`atlas-job-*` unit on the *same* host, but the two hosts may run concurrently.

| Host | Use | Never |
| --- | --- | --- |
| `atlas-runner` | Reenrich, later ULIF / slovnyk migrate | Teacher API, GH runners |
| `hramatka` | Reenrich (class-B, memory-capped) **and** teacher API, Caddy, CI runners | Writing under `/opt/hramatka` or `/srv` (teacher-service data) |

Default `ATLAS_RUNNER_HOST` is **`atlas-runner`**; pass `host: hramatka` (or
the `vps` ssh alias — same machine, see `scripts/config/trails/estate.v1.yaml`)
to target the other host. Unknown host strings are still rejected.

Per-host default work root (only used when the plan omits `workdir`, and
overridable via `ATLAS_RUN_ROOT`):

| Host | Default root |
| --- | --- |
| `atlas-runner` | `/home/ops/atlas-runner` |
| `hramatka` / `vps` | `/home/ops/atlas-jobs` (does not exist yet on the host — `submit`/the launcher `mkdir -p` it on first use) |

`hramatka`'s reenrich work root is deliberately separate from its
teacher-facing `/opt/hramatka` and `/srv` trees — never point a job's
`workdir` there.

**Memory on hramatka.** The class-B launcher (`launch_reenrich_class_b.sh`)
already pins `systemd-run --property=MemoryHigh=1536M --property=MemoryMax=2048M`
regardless of host — this is intentionally conservative on hramatka so a
reenrich run cannot starve the teacher API / Caddy / GH runners sharing that
box. Do not raise these limits for hramatka jobs without checking headroom
against the resident services first.

SSH aliases live in the operator `~/.ssh/config`. IAC: private
`hramatka/ops/iac/` (merged #495). Occupancy/load on the Monitor host
itself uses `ATLAS_JOB_SELF_HOST` (local collection, no SSH-to-self).
Remote mapped hosts still need BatchMode SSH from that Monitor host.

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

| Method | Path | Wraps / Description |
| --- | --- | --- |
| GET | `/api/atlas-jobs` | List journal entries |
| GET | `/api/atlas-jobs/health` | Service health & restic block status |
| GET | `/api/atlas-jobs/load[?host=x][&fresh=true]` | Non-blocking host load & resource telemetry |
| GET | `/api/atlas-jobs/results[?host=x][&state=x][&limit=n][&cursor=c]` | Allowlisted result receipts (newest-first keyset pagination) |
| POST | `/api/atlas-jobs/submit` | Validate + host check + submit |
| GET | `/api/atlas-jobs/{id}` | Status reconcile against host systemd |
| POST | `/api/atlas-jobs/{id}/close` | Close & seal fail-closed receipt |

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

`--host` accepts `atlas-runner` or `hramatka` (`vps` alias) everywhere above.
`submit` refuses a second active `atlas-job-*` unit on that host — the other
host may still have its own job running. `close` seals a result after the
unit is dead (or records `needs_finalize` when evidence is missing).

## Memory

The class-B launcher pins `MemoryHigh=1.5G` / `MemoryMax=2G` on every host —
one heavy job at a time per host. On `hramatka` this cap is load-bearing (see
Hosts above): it exists so a reenrich run cannot starve the teacher API / GH
runners on the same box. Two full-catalog runs on one host need a later host
or a queue; two hosts running one campaign each is the supported dual-host
shape.
