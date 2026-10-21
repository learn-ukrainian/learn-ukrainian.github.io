# GitHub cache maintenance

The GitHub client expires identifiable responses after seven days and caps their
logical body plus header bytes at 64 MiB. SQLite retains freed pages for reuse.
The logical limit does not bound the database file, unknown rows, budget rows,
filesystem allocation or host-wide free space.

Use the supported command to inspect the existing owning-client cache:

```bash
.venv/bin/python -m scripts.maintenance.github_cache
```

Reporting is the default. It opens the existing database read-only without
constructing a client, initializing a schema, probing writability or pruning
rows. The target follows the client's `LU_GITHUB_CACHE_DIR` override, otherwise
its module repository's Git common-root cache selection. There is no database
filename argument or alternate-target fallback. A missing or unresolved target
is a refusal, never an empty database or an in-memory success.

An authorized operator can explicitly reclaim unused pages:

```bash
.venv/bin/python -m scripts.maintenance.github_cache --apply --timeout-seconds 60
```

This command invokes SQLite `VACUUM` on the existing database. It does not unlink,
replace, rename or manually copy the database. Retained values in every cache
and budget row remain intact, including expired responses, credential-scoped
keys and unclassified stored types or malformed headers. The existing client
retention and budget authority still apply when that client next opens the cache.
SQLite may renumber implicit rowids; the owning schema uses composite primary
keys, and rowids are not its identity contract.

## Eligibility and safe refusal

The command requires the owning client's exact cache and budget tables and its
optional retention index. Additional tables, views, triggers or altered indexes
are ambiguous and refused. It never repairs or migrates an unexpected schema.
A cache with no free pages reports `compact`; applying to it returns `no_op`
without running `VACUUM`. Eligibility in a report is a snapshot, not a reservation.
Apply repeats validation while holding the database lock.

The selected database must already exist as a regular, singly linked file owned
by the current user. Its directory must belong to that user. Symlinks in any
component, traversal, group/world-writable cache directories or files, foreign
ownership and unsafe sidecars are refused. Ancestors must belong to root or the
current user and not permit other writers, apart from root-owned sticky temporary
directories. The command pins directory and file descriptors and checks target
identity before SQL and before maintenance. This assumes the current user and
root do not maliciously replace their own trusted directories during maintenance.

The client creates a rollback-journal database by default. Maintenance accepts
that existing format without changing journal mode. A WAL-format file or nonempty
journal/WAL/shared-memory sidecar is refused before SQLite opens it. Reporting
must not recover a hot journal or create WAL sidecars. Leave recovery and journal
mode decisions to the owning client/operator; never remove sidecars to make this
command pass. A future change to the owner's storage format requires corresponding
maintenance support and validation.

## Contention, interruption and storage

Apply requests SQLite exclusive locking mode and `BEGIN EXCLUSIVE`, then validates
and measures under that lock. Exclusive locking mode retains the lock across
`COMMIT`, so the following `VACUUM` has no admission gap. Existing readers or
writers that prevent exclusive acquisition cause `busy`; there is no retry or
force. New connections wait or fail according to their own SQLite lock timeout.
Idle connections without a transaction do not prevent safe maintenance. Existing
client fallback behavior during contention is unchanged.

Each lock wait lasts at most one second, or the requested smaller deadline.
The default SQL deadline is 30 seconds; accepted values are greater than zero
and at most 300 seconds. A progress handler checks the monotonic deadline every
1,000 SQLite VM instructions. SIGINT and SIGTERM request interruption through
that handler. The command closes the connection and SQLite rolls back an
interrupted write. OS I/O, rollback and connection close are not hard wall-clock
bounded by the VM deadline. Receipt collection retains the progress checks;
a post-commit interruption is `applied_unverified`. Termination after commit
cannot undo it.

SQLite uses its own temporary database and rollback journal internally, and may
need free space up to twice the original file size. Ensure enough free space on
the relevant filesystems before an authorized apply. A disk or SQLite error is a
refusal with no destructive fallback. After an uncatchable kill or power loss,
SQLite's journal recovery belongs to the next owning-client open; this command
refuses pending journal state instead of deleting it. Filesystem and hardware
integrity remain SQLite's prerequisites.

## Receipts and verification

The JSON receipt contains only fixed outcome/reason codes and aggregate counts.
It omits target paths, credentials, scoped keys, headers, bodies and raw exception
messages. Its measurements have separate meanings:

- `logical_response_bytes` counts identifiable retained body/header bytes only.
- `file_bytes` is the main file's length, independent of sparse allocation.
- `allocated_bytes` is the main file's allocated filesystem blocks times 512.
- `page_size`, `page_count` and `freelist_count` describe SQLite pages.
- `free_page_bytes` is page size times free pages; it is not a promised shrinkage.
- Response, unclassified and budget row counts describe preserved categories.

Outcomes are `report`, `reclaimed`, `no_op` or `refused`. A successful apply
includes before/after measurements and `reclaimed_file_bytes`; physical
reclamation requires a positive measured file-length difference. If maintenance
committed but subsequent receipt collection fails, `applied_unverified` with
`applied: true` requires a fresh report and operator reconciliation. Never treat
that state as proof of refusal without mutation or as verified reclamation.
Exit code 0 means report or verified apply/no-op; 2 means refusal or unverified
post-commit evidence; 130 means interruption. Invalid CLI syntax follows argparse
exit code 2. Raw exceptions are never public output.

For operational proof retain the aggregate before/after receipt and reviewed
source SHA privately. Compare actual physical bytes, rather than a successful
SQL statement or host-wide `df`. Source tests and CI do not authorize live
maintenance. The driver applies the merged, reviewed command under the existing
operator authorization and verifies the physical receipt before closing #11362.

## Source and focused checks

The owning contracts live in `scripts/common/github_client.py`; the command is
`scripts/maintenance/github_cache.py`. Synthetic controls cover reclamation,
compact no-op, missing and wrong-schema targets, unsafe paths, busy transactions,
failure/interruption and privacy. They never open the real cache.

```bash
.venv/bin/python -m pytest -n2 tests/test_github_client.py tests/maintenance/test_github_cache.py
```

SQLite's [VACUUM contract](https://www.sqlite.org/lang_vacuum.html),
[exclusive locking mode](https://www.sqlite.org/pragma.html#pragma_locking_mode),
[transaction locks](https://www.sqlite.org/lang_transaction.html) and
[read-only/read-write URI modes](https://www.sqlite.org/uri.html) describe the
maintenance and concurrency primitives. No journal or retention policy changes
are part of this operation.
