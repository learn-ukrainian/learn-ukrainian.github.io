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

## Out of scope for this driver

- `finalize.py` (publication archive)
- Live Atlas pin-flip / publish
- Re-fetching ULIF / re-running reduce
