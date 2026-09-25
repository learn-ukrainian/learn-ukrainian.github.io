# Storage topology v1

Approved layout for bulk sources, active SQLite, and agent-safe fallbacks.

## Topology

| Role | Location | Notes |
| --- | --- | --- |
| Active SQLite | Repository `data/sources.db` | **Always local.** Never open from SMB/network FS. Sources MCP reads this file only. |
| Bulk raw sources (primary) | Windows NTFS share **UkrainianData** → `raw-sources/learn-ukrainian-data` | Full materialized mirror. Mac mounts as `/Volumes/UkrainianData/…` when available. |
| Bulk raw sources (fallback) | Google Drive File Provider `My Drive/Projects/learn-ukrainian-data` | On-demand retrieval when SMB is absent. |
| Mac working set | Git repo + active DBs + small shards | Keep hot runtime artifacts local. |
| Offsite backup | Google Drive (and restic runbook) | Drive is source/backup, not live SQLite. |

**Marker-valid bulk root:** top-level directories `literary_texts/` and
`textbook_chunks/` must both exist. Ambiguous multi-match roots are treated as
unavailable (no guessing).

## Agent / developer commands (Mac)

Read-only status (never materializes cloud-only files):

```bash
# Primary checkout (or any tree that already has the shared project venv)
.venv/bin/python -m scripts.storage status
.venv/bin/python -m scripts.storage status --json

# Dispatch worktree: use the primary checkout interpreter, never a worktree .venv
<path-to-primary-checkout>/.venv/bin/python -m scripts.storage status
```

Environment overrides (optional):

| Variable | Purpose |
| --- | --- |
| `LU_BULK_ROOT` | Force bulk root (must be marker-valid; invalid → unavailable) |
| `LU_SMB_BULK_ROOT` | Preferred SMB bulk path candidate |
| `LU_GDRIVE_DATA` | Force Drive bulk path when SMB is absent (must be marker-valid). Authoritative over auto/caller Drive candidates; **invalid values fail closed** (no silent fallback to other Drive roots). |
| `LU_SOURCES_DB` | Override active DB path (**network paths are refused**) |

Rebuild consumers (`scripts/wiki/config.py` → `GDRIVE_DATA`) use the same
resolver: `LU_BULK_ROOT` → SMB → `LU_GDRIVE_DATA` → auto Drive → unavailable.
The legacy name `GDRIVE_DATA` is retained for call-site compatibility.

## Windows maintenance

Tracked scripts (manual, non-destructive):

1. `scripts/storage/windows/Copy-BulkSourcesFromDrive.ps1` — `rclone copy` only
   (never `sync` / purge / delete) into the share’s **local NTFS** path from
   `Get-SmbShare -Name UkrainianData`.
2. `scripts/storage/windows/Verify-BulkSources.ps1` — marker check and optional
   exact-file JSONL manifest; writes a success receipt **only** on pass.

See `scripts/storage/windows/README.md`. Scheduled Task install is optional and
opt-in; default is a manual run.

## Mac cache (report-only)

When the bulk root is the Drive File Provider path, `status` samples dataless
flags without opening file bodies. To free SSD space after SMB is verified:

1. In **Finder**, select cloud-only items under the Drive project folder.
2. **File → Remove Download**.

Do not invent eviction CLIs, delete cloud objects, or delete the SMB mirror as
part of routine cache reclaim.

## Journal mode (WAL) — declared by writers, relied on by readers

`data/sources.db` runs in **WAL** journal mode, and that is a declared invariant, not
an accident of whichever ingest last touched the file (#8527):

- **Why.** The evidence tools (`build-words`, `words-verify`, `build-pack`,
  `pack-verify`) pin **one SQLite snapshot per session**: a read-only connection with an
  explicit deferred `BEGIN` whose first read fixes the read mark, held until the tool
  closes. In WAL a writer keeps committing past a pinned reader and the reader keeps
  seeing the rows it started with. In **DELETE (rollback-journal) mode the same pinned
  read holds a SHARED lock**: the ULIF walk's commit waits `busy_timeout` (30 s) and then
  raises `database is locked` — a snapshot reader would stall the writer.
- **Who declares it.** `scripts/wiki/build_sources_db.py` folds the temp DB back to
  DELETE mode (one self-contained file to swap) and re-enables WAL on the live path
  immediately after the atomic rename (`declare_wal`). `scripts/lexicon/runner/fetch_ulif_homonyms.py`
  `prepare_database` sets `PRAGMA journal_mode=WAL` on every walk start. Both assert the
  PRAGMA **returns** `wal` and fail loudly otherwise. WAL is a persistent file property,
  so these are no-ops on a file that is already WAL.
- **Cost of a pinned reader.** The WAL cannot be checkpointed past the reader's mark, so
  `sources.db-wal` grows for the minutes a build or verify runs (steady state ≈16 MB).
  Readers print `journal_mode`, WAL size at start and end, and the snapshot duration in
  their progress output, and abort with `snapshot_limit` before the next read if the WAL
  exceeds 4 GiB or free disk on the data volume falls below 10 GiB
  (`scripts/curriculum/evidence/config.py`).
- **Check it.** `.venv/bin/python -m scripts.storage status` prints `journal_mode: wal`
  from the SQLite header (bytes 18–19 = `2 2`) without opening a connection; the same
  fact by hand: `od -A d -t u1 -j 18 -N 2 data/sources.db` → `2 2`.
- **Never** run a long-lived read transaction against a DELETE-mode `sources.db` while
  the walk runs, and never switch the live file back to DELETE mode.

## Bulk consumers and the old `data/` links (#8803)

`data/textbooks` and `data/vesum` are no longer tracked symlinks. Both paths
stay gitignored, and no consumer reads bulk data through them:

- **Textbook PDFs** are read from `textbooks/` under the resolved bulk root
  (`scripts/wiki/config.py` `TEXTBOOK_PDFS_DIR`).
- **Custody-access archive locators** (`gdrive:learn-ukrainian-data/<rel>` and
  `gdrive:<rel>`; a bare `<rel>` too) resolve to `<rel>` under the bulk root and
  nowhere else — there is no repository-relative search root. Absolute locators
  and any locator whose symlink-resolved path leaves the bulk root fail closed
  with an error naming the locator kind. When no marker-valid root resolves, the
  source is reported as unmounted.
- **VESUM release-asset cache**: `scripts/rag/build_vesum_shadow.py` downloads
  the public, SHA-pinned `dict_uk` asset into `data/vesum/` unless you pass
  `--asset` or `--cache-dir`. This is a gitignored download cache, not bulk data.
  - **The legacy link goes away on pull, where it is unchanged.** `data/vesum`
    used to be a tracked symlink. Once this change lands, `git pull` deletes it
    from clones where the link is unmodified, because upstream no longer tracks
    it. If git refuses (`git pull --ff-only` stops because the link was changed
    locally), the link stays. Remove it yourself with `rm data/vesum` (this
    deletes the link only; never `rm -r` through it) and pull again. Do this
    before running the VESUM builder. The default then resolves to a plain,
    gitignored directory that the builder creates on demand.
  - **Do not recreate a symlink there.** `data/vesum` must stay a plain
    directory; a host that wants the cache elsewhere passes `--cache-dir`,
    which overrides the location.
  - **The parser default is frozen.** The default lives in
    `scripts/rag/vesum_reingest.py`, whose SHA-256 is pinned by
    `scripts/config/vesum_source.lock.json` and the frozen ua-eval
    v0.1.0/v0.1.1 release chain, so the `data/vesum` default is not changed.

## Outage posture

| Failure | Expected behavior |
| --- | --- |
| SMB unmounted | Bulk resolver falls back to marker-valid Drive; repo work continues |
| Drive + SMB both absent | Bulk root `unavailable`; rebuilds that need raw JSONL fail closed; Sources MCP still serves local `data/sources.db` |
| Someone points `LU_SOURCES_DB` at SMB | Resolver **refuses**; active DB stays repository-local |

## Safety boundaries

- Do not move live SQLite onto SMB or open it across a network filesystem.
- Do not delete or evict corpus bytes from automation in this topology slice.
- Do not commit secrets, account emails, host/IP addresses, or private source text.
- Phase 3/4 product artifacts are out of scope for this runbook.

## Related

- Shared agent rule: `agents_extensions/shared/rules/storage-topology.md`
- Corpus inventory architecture: `docs/corpus-inventory.md`
- Data backup (restic): `docs/runbooks/data-backup.md`
- Issue context: #6375 (Phase 3 recovery depends on durable bulk storage)
