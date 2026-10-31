# Storage topology v1

Approved layout for bulk sources, active SQLite, and agent-safe fallbacks.

## Topology

| Role | Location | Notes |
| --- | --- | --- |
| Active SQLite | Repository `data/sources.db` | **Always on a local filesystem.** On service hosts, repository `data/` resides on an attached local volume at the same path; never open from network filesystems. Sources MCP reads this file only. |
| Bulk raw sources (primary) | Primary bulk storage mirror → `raw-sources/learn-ukrainian-data` | Full materialized mirror when mounted and marker-valid. |
| Bulk raw sources (fallback) | Cloud storage fallback | On-demand retrieval when primary bulk mirror is absent. |
| Local working set | Git repo + active DBs + small shards | Keep hot runtime artifacts local. |
| Offsite backup | Secondary backup store | Source/backup archive, not live SQLite. |

**Marker-valid bulk root:** top-level directories `literary_texts/` and
`textbook_chunks/` must both exist. Ambiguous multi-match roots are treated as
unavailable (no guessing).

## Linux repository data volume (#8804)

The migration window moves the entire repository `data/` tree to a 40 GB
attached cloud volume and bind-mounts it back at `<repo>/data`. Application paths
stay the same, and SQLite remains on a local filesystem. Hosts
before migration have no `/etc/learn-ukrainian/data-volume.uuid` file.

Before writing the UUID marker, make `/etc/learn-ukrainian` searchable by the
service user (for example, mode 0755 or membership in its access group) and
make the marker readable by that user. An unreadable marker or parent refuses
service starts with exit 78. After the volume and bind mount are verified, the
driver restarts the listener services; a guard refusal does not retry
automatically. Restart any timer service that failed before the mount as well.

Once the UUID file exists, `scripts/storage/data_volume_guard.sh` checks the
UUID reported by `findmnt -no UUID,SOURCE -T <repo>/data`. It exits 78 if the
mount is absent, unreadable, or from a different volume. `services.sh`
checks before `start`, `restart`, and `fix` on both systemd and direct-process
paths; `status` prints the observed `data: volume <uuid>` or
`data: root disk` (and `data: unknown` if mount identity cannot be read).
The systemd user-service drop-ins in `packaging/systemd/dropins/` wrap
each original `ExecStart` with the same guard and set
`RestartPreventExitStatus=78`. This covers loopback listeners and
timer-triggered services, including backup, OpenCode retention, and data-tier tests, without changing
the timer files. Preview
the rendered `/etc/systemd/user/` files with
`<primary-checkout>/.venv/bin/python scripts/storage/install_data_volume_dropins.py`;
the driver runs `--apply` from the primary checkout during the migration window,
then reloads the user manager. `--apply` refuses dispatch worktrees. The
installer does not mount, move data, reload, or start services. The reporter
drop-in uses the resolved primary checkout for its guard, command, and working
directory.

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
| `LU_SOURCES_DB` | Explicit local sources store path; invalid or unknown locality returns a path-free refusal |
| `LU_VESUM_DB` | Explicit local VESUM store path; same refusal semantics |

Rebuild consumers (`scripts/wiki/config.py` → `GDRIVE_DATA`) use the same
resolver: `LU_BULK_ROOT` → SMB → `LU_GDRIVE_DATA` → auto Drive → unavailable.
The legacy name `GDRIVE_DATA` is retained for call-site compatibility.

## Hold or lift SQLite permissions

Quiesce database clients before changing permissions, and prevent concurrent
creation, removal, or replacement of database components. Reopen connections
afterwards: existing connections can retain writable file descriptors.

```bash
.venv/bin/python -m scripts.storage hold example.db --json
.venv/bin/python -m scripts.storage lift example.db --json
```

`hold` sets the database and existing `-wal`, `-shm`, and `-journal` files to
`0444`. `lift` sets the same files to `0644`. Missing companions are optional;
a missing database is an error. JSON maps affected paths to octal mode strings.
The commands refuse symlinks and non-regular files, with one exception: the
Sources store's selector `data/sources.db` (and, before the bootstrap, its
regular file). For the store, both commands take the store writer lock and
change the generation the selector selects; naming a generation file directly
is refused (`generation_named_directly`). A lifted store cannot be published
(`current_generation_writable`) until it is held again. See
[Sources store generations](#sources-store-generations).

The programmatic API exports `hold_database`, `lift_database`,
`get_companion_paths`, and `inspect_database_permissions` from `scripts.storage`.
Inspection returns integer modes, with `None` for absent components.
`strict=False` on hold or lift skips missing paths, including the database.
Other filesystem errors still raise.

If chmod fails, the helper attempts to restore every changed file's original
mode. A rollback failure is reported alongside the original error. Multi-file
chmod is not crash-atomic and does not exclude concurrent clients. Privileged
users can bypass mode bits. See the helper's module documentation for its contract.

## Mirror maintenance

Tracked scripts (manual, non-destructive):

1. `scripts/storage/windows/Copy-BulkSourcesFromDrive.ps1` — `rclone copy` only
   (never `sync` / purge / delete) into the mirror's local path via
   `Get-SmbShare`.
2. `scripts/storage/windows/Verify-BulkSources.ps1` — marker check and optional
   exact-file JSONL manifest; writes a success receipt **only** on pass.

See `scripts/storage/windows/README.md`. Scheduled Task install is optional and
opt-in; default is a manual run.

## Local cache (report-only)

When the bulk root is a cloud provider path, `status` samples dataless
flags without opening file bodies. To free local disk space after mirrors are verified:

1. Select cloud-only items under the provider project folder.
2. Free local storage via provider interface or file manager.

Do not invent eviction CLIs, delete cloud objects, or delete bulk mirrors as
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
- **Who declares it.** The generation publisher (`scripts/storage/generations.py`)
  puts every candidate in WAL before it publishes it, so a published generation
  is always WAL. `scripts/wiki/build_sources_db.py` folds its temp DB back to
  DELETE mode and, for any target other than the live store, re-enables WAL
  after the atomic rename (`declare_wal`). `scripts/lexicon/runner/fetch_ulif_homonyms.py`
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

## Sources store generations

The Sources store can be republished while readers and writers are live. No
reader sees mixed data and no writer loses a commit. The code is
`scripts/storage/generations.py`.

### Layout

| Path | What it is |
| --- | --- |
| `data/sources-generations/` | A real directory, never a symlink. It holds one file per published generation, named `sources.<utc>-<sha12>.db` (publication time and the first 12 hex digits of the file's SHA-256). A name is never reused. |
| `data/sources.db` | The **selector**: a relative symlink whose text is exactly `sources-generations/<name>`. Any other link text, a missing target or a symlinked generation directory is refused (`resolve_store`, the writer lock and backup all apply the same check). |
| `data/sources-generations/<name>.receipt.json` | The publication receipt: `previous` generation, `sha256`, `size_bytes`, `mode`, and `state` (`staged`, then `published`). |
| `data/.sources-writer.lock` | The one store-wide writer lock. It is never a generation file. |

SQLite resolves the selector when it opens the database and names the `-wal`
and `-shm` sidecars after the generation file. A reader that resolved the
selector before a switch therefore keeps a whole, unchanged old generation with
its own sidecars. Generations stay in WAL mode and are held read-only (`0444`)
at rest.

Before the bootstrap (below), `data/sources.db` is still one regular file.
Everything in this section also accepts that layout, except publication.

### Readers

Readers change nothing. `resolve_store("sources")` validates the selector and
returns the selected generation. The Sources MCP reader cache checks the
selector on every request once it holds a generation. After a switch, new
calls get the new generation; a call already running keeps the old connection,
which closes when that call ends. A pinned evidence session keeps its
generation for the whole session.

### Writers

A writer takes the writer lock first, then resolves the selector, and closes its
connections before it releases the lock. The lock is never waited for: a busy
lock is the refusal `writer_lock_busy`.

- **In-process writers** use `generations.store_writer(path)`. It locks, makes
  the selected generation writable, yields it, and on exit closes tracked
  connections and holds the generation again. The ULIF walk (`run`, `walk`,
  `parse`) and `python -m scripts.wiki.sources_db --migrate` do this.
- **Every other script** that opens the store writable calls the write guard
  (`scripts.lib.readonly_sqlite.refuse_writable_corpus_database`) first. For
  the store it refuses unless this process holds the lock, and only the
  selected generation may be opened (`writer_lock_not_held`,
  `not_selected_generation`). Run such a script under the lock:

  ```bash
  .venv/bin/python -m scripts.storage write -- .venv/bin/python scripts/ingest/<script>.py --db data/sources.db
  ```

  `write` refuses if the lock is busy. It makes the selected generation
  writable, runs the command with the locked descriptor inherited, then holds
  the generation again and releases the lock. The writer is killed after
  `--timeout` seconds (default 24 hours, exit 124); SQLite rolls back an
  interrupted transaction.
- Fixtures, staged copies and any path that is not the store are not affected.

### Publication

`publish_generation(candidate, held)` is the only way to change the selector.
The caller holds the writer lock from the moment it reads the current
generation until the switch. It builds the candidate from that generation (for
example with SQLite's backup API) as a closed file in `data/`. The publisher
then:

1. Refuses when the current generation changed since the lock was taken
   (`current_generation_changed`), when it is writable
   (`current_generation_writable`), or when the selector is still a regular file
   (`selector_is_regular_file`; only the bootstrap accepts that).
2. Refuses unless free space is at least the generation size, plus the 10 GiB
   evidence free-disk floor, plus a 4 GiB WAL allowance
   (`insufficient_free_space`; both limits come from
   `scripts/curriculum/evidence/config.py`).
3. Puts the candidate in WAL mode, holds it read-only, and hard-links it into the
   generation directory under its new name. It fsyncs the file and the directory,
   and writes a `staged` receipt.
4. Creates a temporary link, `os.replace`s it onto `data/sources.db`, and fsyncs
   `data/`. This is the commit point.
5. Removes the staging name and marks the receipt `published`. A receipt left
   `staged` on a selected generation is completed by the next publication.

A failure before step 4 leaves the old selection in place, plus at most an
unselected generation file (an orphan). A retry of the same candidate reuses its
own link.

`scripts/wiki/build_sources_db.py` publishes through this routine when its
target is the selector. It refuses the pre-bootstrap live file
(`rebuild_requires_selector`), because the old in-place swap unlinks the
sidecars and renames over a file that readers have open.

Retention: publication keeps every generation, and no automation deletes one.
The free-space check makes publication fail safely when the disk fills up.
Pruning old generations is a separate, operator-run command that is not
available yet.

`.venv/bin/python -m scripts.storage generations` (read-only) prints the layout,
the selected generation, whether it is held, and each retained generation with
its receipt state. Backup and restore are described in
[`data-backup.md`](data-backup.md): a backup copies only the selected
generation; a restore puts it back under its own name and switches the selector
with `python -m scripts.storage restore-generation`.

### Bootstrap (one maintenance window)

The bootstrap turns the regular `data/sources.db` into the first generation. It
hard-links the same file, so it copies nothing and needs no extra space. Run it
once, from the primary checkout, with every Sources reader and writer stopped.

1. **Stop every Sources client.** Stop the dispatcher and end every agent
   session (each session runs its own stdio Sources MCP). Then stop the HTTP
   Sources MCP and the timers that read the store:

   ```bash
   ./services.sh stop sources
   systemctl --user stop learn-ukrainian-sources-watchdog.timer learn-ukrainian-data-tier.timer learn-ukrainian-backup.timer
   ```

   Stop any ULIF walk, ingest, rebuild or evidence run.
2. **Prove that nothing has the store open.** This prints nothing when the
   store is free:

   ```bash
   fuser -v data/sources.db data/sources.db-wal data/sources.db-shm
   ```

3. **Take a backup first** and check that it completed
   (see [`data-backup.md`](data-backup.md)):

   ```bash
   ./scripts/backup-data.sh backup --execute
   ./scripts/backup-data.sh snapshots
   ```

4. **Check the starting state.** Expect `layout: legacy_file` and `held=True`:

   ```bash
   .venv/bin/python -m scripts.storage generations
   ```

5. **Bootstrap:**

   ```bash
   .venv/bin/python -m scripts.storage bootstrap --maintenance-window
   ```

   This takes the writer lock and folds the WAL into the file. It refuses with
   `store_in_use` (exit 3) if any other connection still has the file open, idle
   or reading. It then hashes the
   file (about a minute for the current store), links it into
   `data/sources-generations/`, and replaces `data/sources.db` with the
   selector. Last, it removes the empty legacy `-wal`/`-shm` names. It prints
   `selector now selects sources.<utc>-<sha12>.db`.
6. **Verify.** `generations` must show `layout: selector`, `held=True` and
   `receipt=published`; `status` must show `journal_mode: wal`;
   `readlink data/sources.db` must print `sources-generations/<that name>`.

   ```bash
   .venv/bin/python -m scripts.storage generations --json
   .venv/bin/python -m scripts.storage status
   readlink data/sources.db
   ```

7. **Restart** what step 1 stopped (`./services.sh start sources`,
   `systemctl --user start` for the three timers, then the dispatcher). Then
   check one Sources MCP lookup.

**Rollback** (before anything has written to the new layout): with every client
stopped again, put the regular file back in one atomic rename:

```bash
ln data/sources-generations/<name> data/.sources.db.rollback
mv -T data/.sources.db.rollback data/sources.db
```

The generation's hard link stays in place and costs no space.

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
| Someone points `LU_SOURCES_DB` or `LU_VESUM_DB` at SMB | `resolve_store` returns a path-free refusal; no fallback |
| Legacy `resolve_active_sources_db` network override (pending migration) | Existing fallback object retained; new callers must use `resolve_store` |

## Managed artifact publication

`scripts.storage.artifacts publish` uses the group transaction engine for one
existing A file. For a group-wide regeneration, stage every A output and tracked
K companion away from `data/` and `registry/`, then pass a JSON plan to
`publish-set --plan <path>` or call `write_artifact_set()` with staged writer
callbacks. The plan names one `group`, a `producer`, the exact
old `expected_members` (paths relative to `data/`), and `artifacts` rows with
`operation` (`add`, `replace`, `remove`), `rel`, staged `source` for writes, and
`expected_sha256` (`null` only for an addition). `companions` rows name a
`registry/` path, staged `source`, and expected old hash. Removal has no source.
`artifacts` may be an empty list when `companions` is non-empty. That
companion-only publication may change only companions already bound to the
group. It leaves every A entry, membership, retirement record, byte, mode, and
timestamp unchanged, journals only the changed K rows, and returns an empty
A-change mapping. `expected_manifest` is optional on every plan and required
for a companion-only plan: it is the canonical digest of
`paths.artifact_set(group).manifest`, checked under the publication lock before
any mutation. A companion whose staged bytes already equal its expected,
descriptor-bound live bytes is an assertion. Its mode is checked and the file
is not rewritten. Changed companion bytes still require a clean Git HEAD. A
request made only of successful assertions returns without a transaction.
An addition must match a narrow `registration_patterns` declaration in that
group's tracked manifest. Unmatched and cross-group paths are refused. Every
existing component of a published or retired path beneath the checkout root
must be a real directory or file, never a symlink.

The writer preserves old and new objects in the host store, installs all rows,
and atomically replaces one group manifest as the commit descriptor. That
manifest binds exact A membership and K hashes. A reader of the whole set uses
`paths.artifact_set(group)`, which returns verified bytes and raises if a
publication is unfinished or a member differs. It does not create a store.
After a crash, run `artifacts status` to recover the transaction before retrying
publication. The journal names each planned target temp before it is created;
recovery removes those named temps under the publication lock. Do not discard
a journal whose recovery refuses drift. Explicitly
retired paths keep their store objects and are removed during `hydrate` only
when their bytes match a recorded retired version. Run `snapshot` after a local
publication to verify the active objects in that host store, then transfer
them to each required host. Local publication alone proves no off-host backup.

Path validation refuses a static symlink in a published path or the store path
before publication creates store or lock state. A second process can still swap
a path component for a symlink after validation while the publisher holds its
lock; cooperating writers are expected to honor that lock. If the threat model
includes hostile concurrent path changes, open every component through directory
file descriptors with per-component `O_NOFOLLOW` and
`os.open(..., dir_fd=)` before treating publication as safe against that race.

## Safety boundaries

- Do not move live SQLite onto SMB or open it across a network filesystem.
- Do not delete or evict corpus bytes from automation in this topology slice.
- Do not commit secrets, account emails, host/IP addresses, or private source text.
- Phase 3/4 product artifact migration remains out of scope for this runbook.

## Related

- Shared agent rule: `agents_extensions/shared/rules/storage-topology.md`
- Corpus inventory architecture: `docs/corpus-inventory.md`
- Data backup (restic): `docs/runbooks/data-backup.md`
- Issue context: #6375 (Phase 3 recovery depends on durable bulk storage)

## Logical read-store bindings (#9945)

New callers use `scripts.storage.topology.resolve_store("sources")` or
`resolve_store("vesum")` at call time. A `StoreBinding` contains `store`,
`path`, `access_mode="read"`, and `provenance`; pass its path to
`scripts.lib.readonly_sqlite.open_readonly`. A `StoreRefusal` contains only
`store` and `reason`, with no path attribute and no silent fallback.

Precedence is an injected test binding, then the explicit store environment
override, then the primary checkout's `data/<store>.db` located by
`main_checkout_root`. Empty, whitespace, relative, URI, nonexistent, directory,
network, and unknown-locality inputs are refused. Symlinks to existing local
files are validated at their resolved target. A linked worktree's own
`data/<store>.db` file or symlink (including a dangling link) is refused.
The resolver creates no files or connections and grants no write access.

The legacy `resolve_active_sources_db` and `require_local_active_sources_db`
retain their existing behavior pending caller migration. In particular, the
legacy resolution object can carry a fallback path on network refusal; it is
not the supported contract for new readers.

The store-access ratchet covers `scripts/` and `tests/`. Reproduce its frozen
baseline with the project interpreter:

```bash
<primary-checkout>/.venv/bin/python -m scripts.hygiene.lint_source_db_writable_connects --census <base-commit>
```

It reads tracked commit
blobs, including sparse paths, and excludes untracked and ignored files from
that census. Baseline identities use path, class, enclosing scope, normalized
AST fingerprint, and occurrence; line movement does not grandfather new code.
Resolved migrations remove their corresponding baseline entries; stale entries
fail lint. Once the initial census lands, `base_commit` and `file_counts` remain
frozen while `entries` shrink; do not regenerate counts during caller migration.
Before that first landing, a corrected census must reproduce the same base
commit exactly. Shallow checkouts without that base classify every current
file rather than using the base-blob shortcut. Joins onto a store filename from
an unresolved anchor and helpers taking `data` plus a store filename are also
findings, except paths with test-fixture provenance. Only declared resolver
functions may build new repository store paths.

## Declared write locations (#9977)

The 88 selected caller identities and frozen additional consumers use declared
store contracts. Policy identities, the legacy Sources resolver, the mirror
publisher and the nine explicit-input ingest writers retain their recorded
#9937 dispositions; this slice does not claim a universal writer migration.

Readers resolve `StoreBinding` at call time with `resolve_store` and open it
through `open_readonly`. `WriteStoreBinding` is a separate type. Writers call
`resolve_store_for_write` with explicit intent (`update` or `create`), operation
(`sqlite` or `replace`) and, for explicit inputs, `ExplicitStoreWriteTarget`.
An explicit target takes precedence over the environment and primary checkout.
Invalid inputs never fall back. Resolution opens no connection and creates no
file, directory, backup or link. Refusals contain only store and reason.

`active` defaults to update and never allows create for Sources or VESUM.
`staging` admits a separate SQLite target and explicit creation. `shadow` also
admits whole-file VESUM replacement. Both output roles refuse canonical slots,
configured active locations and aliases by resolved path or inode. All roles
refuse conventional store slots in non-primary Git checkouts, even absent slots.
Relative staging/shadow inputs are anchored to the calling checkout; active and
environment inputs must be absolute. Parent traversal, network and unknown
locality are refused. Replacement refuses leaf symlinks. SQLite URIs use only
`Path.as_uri()` and `mode=rw` or `mode=rwc`.

The connection owner freezes `_prepare_store_write_target` before acquiring
`generations.store_writer(request.location)`. It resolves the final Sources
binding inside that context, keeps the lock through commit/rollback and explicit
connection closure, and never caches a binding beyond that lifetime. The private
helper selects the unresolved request only. Invalid declarations, slots,
locality and staging aliases are refused before a live lock is entered.
Generation selection and validation occur under the lock. Primary and selector
requests require selector/legacy-live classification and a registered or
inherited holder for the exact selector and lock directory. Classification
errors refuse; they cannot fall back to fixture behaviour. Plain fixtures and
staged copies retain lockless operation. Inherited locks are reused without
nested acquisition. The existing lock registry is process-wide, including
threads; bindings are location validation, not OS capabilities.

Sources create with active role returns `active_sources_create_forbidden`;
VESUM returns `active_vesum_create_forbidden`. Sources replacement returns
`sources_replace_forbidden`; selection changes only through `publish_generation`.
`lexdata` returns `unsupported_write_store` before target or environment access.
Bootstrap and publication require their existing operator maintenance authority.

Dispatchers provision no Sources or VESUM worktree entries. AGY requires an
empty worktree store slot and one primary trust anchor agreed by Git common-dir
and `main_checkout_root`. It presents only the selected generation, its existing
WAL/SHM sidecars read-only, and the exact relative selector symlink, or the
supported legacy regular file. It exposes no history or receipts. It creates no
private or writable sidecars and never uses `immutable=1`. The positive canary
resolves, opens read-only and queries inside the sandbox. If read-only WAL
access cannot work without sidecars it returns a typed refusal; the Sources
relay remains available. Existing write-denial, secret and network probes bind.
