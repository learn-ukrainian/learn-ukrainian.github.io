# Atlas 20k Runner Durability

Fixes #5884. Related incident: 2026-07-29 wipe (sole laptop copies fail).

The `fetch_ulif_20k.py` / `reduce_ulif_20k.py` / `enrich_offline_20k.py`
runners write their durable state under a work-dir on the remote runner VPS
(default `/home/ops/atlas-runner/run-20k`):

| Artifact | Path |
| --- | --- |
| Fetch ledger | `$WORK_DIR/ledger.sqlite` |
| ULIF network cache (raw + parsed) | `$WORK_DIR/network-cache.sqlite` |
| Reduce candidate | `$WORK_DIR/candidate-ulif-reduce.json` |
| Enrich work dir | `$WORK_DIR/offline_enrich/` |
| Enriched output | `$WORK_DIR/offline_enrich/candidate-enriched.json` |
| Logs | `$WORK_DIR/enrich.log`, `$WORK_DIR/reduce.log` |

That VPS has no backup of its own. A runner wipe or local cleanup before this
recipe runs means a full ULIF refetch (politeness-limited: ~1 lemma/s,
20,323 lemmas).

This does **not** introduce a second backup mechanism. `scripts/backup-data.sh`
(#6014) already makes encrypted, versioned restic snapshots of everything
under this repo's local `data/`. The fix is to mirror the VPS work-dir into
`data/lexicon/runner-mirror/<work-dir-name>/` — gitignored, checksummed, and
therefore picked up automatically by the next `backup-data.sh backup
--execute` — instead of building a competing bus. `data/lexicon/cache/`
(local enrichment caches) is already covered the same way; this closes the
one gap: the VPS itself.

The v0.1 open dataset (`data/lexicon-dataset.pointer.json` → GitHub Release
asset `atlas-open-dataset`) is a different, unrelated mechanism for
*publishing* derived, license-cleared data. Do not route raw ULIF scrape
output or the runner ledger through it — that pattern is for the public
open-dataset export, not for private durability of in-progress runner state.

## Tool

`scripts/lexicon/runner/durable_mirror.py` — sync, checksum, verify, and gate:

```bash
# Sync a source (local path or user@host:/path) into a local mirror and
# (re)write its manifest.json (sha256 per file):
.venv/bin/python scripts/lexicon/runner/durable_mirror.py snapshot \
  --source ops@<runner-host>:/home/ops/atlas-runner/run-20k \
  --mirror-dir data/lexicon/runner-mirror/run-20k

# Recompute checksums and compare against the manifest (corruption check):
.venv/bin/python scripts/lexicon/runner/durable_mirror.py verify \
  --mirror-dir data/lexicon/runner-mirror/run-20k

# Fail closed unless the mirror is present, non-empty, internally verified,
# and newer than --max-age-hours (default 24). Exit 2 on any failure:
.venv/bin/python scripts/lexicon/runner/durable_mirror.py require \
  --mirror-dir data/lexicon/runner-mirror/run-20k
```

`snapshot` uses `rsync -az --delete`: the mirror always reflects the VPS
work-dir's *current* state. History/versioning is the restic bus's job
downstream, not this mirror's.

`scripts/lexicon/runner/mirror_20k_runner.sh` wraps the common laptop-side
case (env: `ATLAS_RUNNER_HOST`, `ATLAS_RUN_ROOT`, `ATLAS_WORK_DIR_NAME`,
`ATLAS_MIRROR_DIR`):

```bash
ATLAS_RUNNER_HOST=ops@<runner-host> scripts/lexicon/runner/mirror_20k_runner.sh
scripts/lexicon/runner/mirror_20k_runner.sh --require-only   # gate only, no sync
```

## Required workflow

1. After every fetch/reduce/enrich phase on the VPS (or at minimum daily
   during an active run), sync:

   ```bash
   ATLAS_RUNNER_HOST=ops@<runner-host> scripts/lexicon/runner/mirror_20k_runner.sh
   ```

2. Push the refreshed mirror into the restic bus:

   ```bash
   ./scripts/backup-data.sh backup
   ./scripts/backup-data.sh backup --execute
   ```

3. Before touching, cleaning, or wiping `$WORK_DIR` on the VPS, or before
   deleting the local `data/lexicon/runner-mirror/` copy, gate on a fresh
   verified mirror:

   ```bash
   scripts/lexicon/runner/mirror_20k_runner.sh --require-only
   ```

   A nonzero exit means: do not proceed. Re-sync (step 1) and re-check.

## Restore drill

After a VPS wipe or a fresh runner host:

```bash
# 1) Restore the local repo's data/ (including the runner mirror) from restic
#    into an empty staging directory — see docs/runbooks/data-backup.md.
./scripts/backup-data.sh restore latest --to /absolute/path/to/restore-test
./scripts/backup-data.sh restore latest --to /absolute/path/to/restore-test --execute

# 2) Verify the staged mirror before trusting it.
.venv/bin/python scripts/lexicon/runner/durable_mirror.py verify \
  --mirror-dir /absolute/path/to/restore-test/data/lexicon/runner-mirror/run-20k

# 3) Copy the verified mirror back to a fresh VPS work-dir.
rsync -az /absolute/path/to/restore-test/data/lexicon/runner-mirror/run-20k/ \
  ops@<new-runner-host>:/home/ops/atlas-runner/run-20k/

# 4) Resume. The fetch/enrich ledgers are resumable by design — the same
#    work-dir with an intact ledger.sqlite resumes rather than restarting:
scripts/lexicon/runner/launch_enrich.sh
```

If step 3's target work-dir is missing `ledger.sqlite`/`network-cache.sqlite`
entirely (mirror predates the wipe, or was never synced), the runner starts
a fresh run for whatever lemmas are not yet reflected in the restored
`candidate-ulif-reduce.json` / `candidate-enriched.json` — re-fetch is bounded
to the gap, not the full 20,323-lemma cohort.

## What this does not cover

- The remote VPS's own OS/root disk durability — out of scope; the mirror
  makes the runner's *durable state* survive a VPS loss, not the VPS itself.
- Promotion of `candidate-enriched.json` into the published lexicon manifest
  — that is `finalize.py` + the #5138/#5331 publish gate, explicitly out of
  scope for the enrich driver and this mirror.
