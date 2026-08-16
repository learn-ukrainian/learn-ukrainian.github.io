# Atlas VPS job protocol

Plan a long-running Atlas job, **register it**, run it on a named host, then
**close it with a result**. No SSH-and-hope. No orphan systemd units. No
“finished” without a receipt.

This wraps `launch_reenrich_class_b_remote.sh`. It is not a second message bus
and not a Hetzner snapshot.

## Hosts

| Host | Use | Never |
| --- | --- | --- |
| `atlas-runner` | Reenrich, later ULIF / slovnyk migrate | Teacher API, GH runners |
| `hramatka` | Teacher API, Caddy, CI runners | Catalog reenrich / slovnyk refetch |

Default `ATLAS_RUNNER_HOST` is **`atlas-runner`**. A plan that puts `reenrich`
on `hramatka` is rejected.

SSH aliases live in the operator `~/.ssh/config`. IAC: private
`hramatka/ops/iac/` (merged #495).

## Lifecycle

```
planned → submitted → running → {succeeded | failed | timeout | rejected}
```

`--no-poll` only detaches systemd-run. The registry row stays `running` until
`close`. A unit that exits 0 with `consecutive_misses == targets` or a tripped
circuit breaker is **failed**.

Registry (gitignored, restic-covered): `batch_state/atlas-jobs/<id>.json`  
Result: `batch_state/atlas-jobs/<id>.result.json`  
Remote unit: `atlas-job-<id>.service` (never reuse `atlas-class-b-reenrich.service`)

`status --audit` SSH-pgreps known drivers. A matching process with **no**
`running` registry row is exit 2 (untracked job).

## Plan (`atlas-job.v1`)

Required: `id`, `host`, `kind`, `denominator`, `pointer_write: false`,
`result_sink` (`git` | `restic` | `both`), `success.circuit_breaker`,
`success.min_filled`.

`pointer_write` is always false here. Publish / pointer flip is a later gate.

## Result sinks

| Sink | What comes back |
| --- | --- |
| `git` | Small result JSON in a PR. Never commit manifests, slovnyk cache, or `sources.db`. |
| `restic` | `durable_mirror.py snapshot` → `data/lexicon/runner-mirror/<id>/` then `backup-data.sh backup --execute` (covers `data/` + `batch_state/`). |
| `both` | Both of the above. |

If restic doctor/`#6093` fails, the result still records `restic.attempted` and
`ok: false`. Silence is not a result.

## Commands

```bash
python -m scripts.lexicon.runner.atlas_job validate PLAN.json
python -m scripts.lexicon.runner.atlas_job submit PLAN.json
python -m scripts.lexicon.runner.atlas_job status --host atlas-runner --audit
python -m scripts.lexicon.runner.atlas_job close JOB_ID --summary-file summary.json
python -m scripts.lexicon.runner.atlas_job pull --host atlas-runner
python -m scripts.lexicon.runner.atlas_job list
```

`submit` refuses a second `running` job on the same host. `close` is required
to seal a result after the unit is dead.

## Memory

The existing launcher still pins `MemoryHigh=1.5G` / `MemoryMax=2G` on the
cx33. One heavy job. Two full-catalogs need a later host or a queue.
