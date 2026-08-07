# Offline enrich driver (20k ULIF path)

CLI: `enrich_offline_20k.py`  
Launcher: `launch_enrich.sh`

Consumes the **reduce** candidate (`candidate-ulif-reduce.json` from
`reduce_ulif_20k.py` / `offline_reduce.py`) and runs sealed offline enrich
phases (CEFR → relations → leaf chunks) with a resumable ledger.

**Stops before** finalize / publish / pin-flip.

## Local dry-run (fixture / ≤50 lemmas)

```bash
# Plan only — no enrich, no sources.db open beyond path checks
.venv/bin/python scripts/lexicon/runner/enrich_offline_20k.py \
  --dry-run \
  --work-dir /tmp/enrich-dry \
  --candidate tests/fixtures/lexicon/runner_pr1/slice_input.json \
  --sources-db tests/fixtures/lexicon/runner_pr1/sources_slice.sqlite \
  --kaikki-json tests/fixtures/lexicon/runner_pr1/kaikki_slice.json \
  --max-lemmas 50

# Small in-process slice (tests / smoke)
.venv/bin/python scripts/lexicon/runner/enrich_offline_20k.py \
  --work-dir /tmp/enrich-smoke \
  --candidate tests/fixtures/lexicon/runner_pr1/slice_input.json \
  --sources-db tests/fixtures/lexicon/runner_pr1/sources_slice.sqlite \
  --kaikki-json tests/fixtures/lexicon/runner_pr1/kaikki_slice.json \
  --grac-cache tests/fixtures/lexicon/runner_pr1/grac_frequency_slice.json \
  --max-lemmas 50 \
  --chunk-size 25 \
  --stop-after-chunks 1 \
  --in-process
```

Bare invocation and `--help` never start a multi-hour run (#5393 class).

## VPS recipe (run-20k, post-reduce)

Assumes fetch + reduce already completed under `/home/ops/atlas-runner/run-20k`:

| Artifact | Path |
| --- | --- |
| Network cache | `$WORK_DIR/network-cache.sqlite` |
| Reduce candidate | `$WORK_DIR/candidate-ulif-reduce.json` |
| Enrich work dir | `$WORK_DIR/offline_enrich/` |
| Enriched output | `$WORK_DIR/offline_enrich/candidate-enriched.json` |
| Log | `$WORK_DIR/enrich.log` |

```bash
# Optional: plan against live reduce artifact
.venv/bin/python scripts/lexicon/runner/enrich_offline_20k.py \
  --dry-run \
  --repo /home/ops/atlas-runner/repo \
  --work-dir /home/ops/atlas-runner/run-20k/offline_enrich \
  --candidate /home/ops/atlas-runner/run-20k/candidate-ulif-reduce.json

# Detached under MemoryHigh=1.5G MemoryMax=2.0G (idempotent)
scripts/lexicon/runner/launch_enrich.sh

# Resume after kill / reboot (same work-dir; ledger resumes)
scripts/lexicon/runner/launch_enrich.sh

# Smoke: one chunk then exit (resume later)
scripts/lexicon/runner/launch_enrich.sh --stop-after-chunks 1
```

Tail progress:

```bash
tail -f /home/ops/atlas-runner/run-20k/enrich.log | grep --line-buffered '"event"'
```

## Durability (#5884)

`$WORK_DIR` on the VPS has no backup of its own — a runner wipe or local
cleanup means a full ULIF refetch. After every fetch/reduce/enrich phase
(and always before touching/cleaning `$WORK_DIR`), sync it into this repo's
`data/` so the existing restic backup (`scripts/backup-data.sh`, #6014)
covers it:

```bash
ATLAS_RUNNER_HOST=ops@<runner-host> scripts/lexicon/runner/mirror_20k_runner.sh
```

Atlas drivers can prove this run's remote work-dir and local durability state
without starting enrichment by running:

```bash
ATLAS_RUNNER_HOST=ops@<runner-host> scripts/lexicon/runner/health_20k_runner.sh
```

Before any cleanup, execute the full durability order — **snapshot → restic
backup → receipt gate → wipe**. The gate rejects a stale, missing, corrupt,
or not-yet-backed-up mirror instead of guessing:

```bash
./scripts/backup-data.sh backup --execute
scripts/lexicon/runner/mirror_20k_runner.sh --require-only
```

Full recipe, restore drill, and coordination with #6014's restic bus:
[`docs/runbooks/atlas-20k-runner-durability.md`](../../../docs/runbooks/atlas-20k-runner-durability.md).

## Out of scope for this driver

- `finalize.py` (publication archive)
- Live Atlas pin-flip / publish
- Re-fetching ULIF / re-running reduce

## Class-B residual EN re-enrich (#6369, run-class-b-reenrich)

Separate, much smaller job: fills sourced English translation cards for the
Class-B residual — old-gate manifest entries with no learner English gloss
(`scripts/lexicon/reenrich_thin_manifest_entries.py --target
missing-translation`, scoped with `--slugs-file`). Runs on the same VPS
under the same memory discipline, in its own work-dir
(`run-class-b-reenrich`) so it never collides with a live 20k run.

**Do not run this on the Mac.** Orchestration is driven from a
[layout-A](../../../AGENTS.md) worktree, execution happens on the VPS.

The VPS repo checkout at `$REPO` is treated as read-only for this job (it is
routinely stale/dirty — large `data/` dirs are deliberately deleted there for
disk headroom). The Mac-side orchestrator never runs `git pull`/`checkout`/
`reset` against it; it scp's the driver + launcher into the work-dir instead
(the `--slugs-file` flag lands via #6398 — if that PR hasn't merged yet, this
is the "scp the script from the PR branch" fallback).

```bash
# From the Mac worktree — syncs residual slugs + driver + launcher, starts
# the job detached under MemoryHigh=1.5G/MemoryMax=2.0G, polls until done
# (bounded, default 900s), then pulls manifest.json + reenrich.log +
# reenrich-summary.json back into batch_state/class-b-reenrich-pulled/.
scripts/lexicon/runner/launch_reenrich_class_b_remote.sh

# Smoke: 5 slugs only
scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --limit 5

# Fire-and-forget (skip the poll loop)
scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --no-poll

# Just pull back current artifacts (job already finished, or checking
# mid-run without re-syncing/re-launching)
scripts/lexicon/runner/launch_reenrich_class_b_remote.sh --pull-only

# Read-only status check (pid, log tail, disk) without pulling anything
scripts/lexicon/runner/health_reenrich_class_b.sh
```

Resumable: a resumed run reuses the same work-dir manifest snapshot (taken
once from the live checkout's hydrated manifest) — `missing-translation`
targeting only touches entries that still lack a translation, so re-running
after a kill/reboot picks up exactly where it left off.

**Does not** finalize, publish, or pin-flip. The pulled-back `manifest.json`
is the input to the existing publish gate — that step runs on the worktree,
same as any other Atlas manifest change, and is not part of this launcher.
