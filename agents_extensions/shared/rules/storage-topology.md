# Storage Topology v1

> Binding layout for bulk sources and active SQLite. Full runbook:
> [`docs/runbooks/storage-topology.md`](../../../docs/runbooks/storage-topology.md).

## Where things live

| Kind | Location | Rule |
| --- | --- | --- |
| Active `sources.db` / VESUM / hot DBs | Repository `data/` on the local host | **Local only.** Never open SQLite from SMB or another network filesystem. |
| Bulk raw sources (primary) | Primary bulk storage mirror → `raw-sources/learn-ukrainian-data` | Prefer when mounted and **marker-valid**. |
| Bulk raw sources (fallback) | Cloud storage fallback | Use when primary bulk mirror is absent; on-demand retrieval. |
| Sources MCP | Local `data/sources.db` | An outage of bulk mirrors must **not** break MCP, tests, or ordinary repo work. |

**Marker-valid bulk root:** both `literary_texts/` and `textbook_chunks/` exist
as directories. If roots are missing or ambiguous, treat bulk as **unavailable**
— do not guess paths or invent host-specific mounts in commits.

## Required agent behavior

1. **Status before path invention:**
   ```bash
   .venv/bin/python -m scripts.storage status
   # or absolute primary interpreter from a worktree
   ```
2. **Rebuild / raw JSONL consumers** go through
   `scripts/wiki/config.py` (`GDRIVE_DATA` is the bulk root alias) or
   `scripts.storage.topology.resolve_bulk_root` — not a second Drive-only path.
3. **Never** set active DB tooling to a path under an external mount or
   a network share.
4. **Never** delete, move, or auto-evict bulk corpus, Drive objects, or SMB
   payloads unless a separate operator-authorized task says so.
5. **Local cache:** report-only. Use standard operating system or cloud provider tools to free space.
   Do not invent eviction commands.
6. **Bulk mirror maintenance:** only
   `scripts/storage/windows/Copy-BulkSourcesFromDrive.ps1` (`rclone copy`, never
   sync) and `Verify-BulkSources.ps1` (receipt only after successful verify), on
   a verified mirror path via `Get-SmbShare`.

## Env overrides (optional)

| Variable | Meaning |
| --- | --- |
| `LU_BULK_ROOT` | Force bulk root (must be marker-valid; invalid → unavailable) |
| `LU_SMB_BULK_ROOT` | SMB candidate |
| `LU_GDRIVE_DATA` | Force Drive bulk path when SMB is absent (marker-valid). Authoritative over auto/caller Drive candidates; **invalid → fail closed** (no silent Drive fallback). |
| `LU_SOURCES_DB` | Explicit local sources store path; invalid or unknown locality returns a path-free refusal |
| `LU_VESUM_DB` | Explicit local VESUM store path; same refusal semantics |
| `LU_LEXDATA_DB` | Explicit local lexdata store path for readers; same refusal semantics (the writer ignores it) |

Precedence: `LU_BULK_ROOT` → SMB → `LU_GDRIVE_DATA` → auto Drive → unavailable.

## Privacy

Do not commit absolute operator home paths, account emails, hostnames, raw IPs,
credentials, or private corpus bodies. The relative folder `learn-ukrainian-data`
is the public topology label.

## Logical read-store bindings (#9945)

New callers use `scripts.storage.topology.resolve_store("sources")`,
`resolve_store("vesum")` or `resolve_store("lexdata")` at call time; the one
`STORE_FILES` mapping names each store's file and environment override. A `StoreBinding` contains `store`,
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

### Sources store generations

`data/sources.db` becomes a selector: a relative symlink to exactly
`sources-generations/sources.<utc>-<sha12>.db` inside the real directory
`data/sources-generations/` (before the one-time bootstrap it is still a regular
file). Generation names are never reused; generations stay WAL and are held
`0444` at rest. Rules:

1. **Write only under the store writer lock** (`data/.sources-writer.lock`). In
   Python use `scripts.storage.generations.store_writer`; run any other writer
   as `.venv/bin/python -m scripts.storage write -- <command>`. A writable open
   of the store without the lock, or of a generation the selector does not
   select, is refused.
2. **Change the selection only through `publish_generation`**, holding the lock
   from reading the current generation to the switch. Never rename, copy or
   link over `data/sources.db` or a generation by hand.
3. **Never delete a generation from automation.** Pruning is an explicit
   operator command (not yet available).
4. The bootstrap is an operator maintenance-window step; follow the runbook's
   "Sources store generations" section exactly.

### Derived lexical store (`lexdata`)

`data/lexdata.db` is a derived store (L1 staging, L2 crosswalk, L3 card
inputs); it is never the only copy of anything, and it never writes
`sources.db` or `vesum.db`. Readers follow the rules above and open it through
`scripts.lexdata.generation.open_generation`, which also refuses an
unpublished or digest-mismatched generation. Its only writer is
`.venv/bin/python -m scripts.lexdata build`, run from the primary checkout:
`build_store.writer_target` refuses a linked worktree, a network or unknown
filesystem and symlinked `data`/`data/lexdata` paths. One build holds an
exclusive lock on `data/lexdata/.build.lock`, writes a new generation file,
verifies it and swaps it in atomically; L0 stores are attached `mode=ro`.

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
