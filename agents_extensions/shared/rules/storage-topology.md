# Storage Topology v1

> Binding layout for bulk sources and active SQLite. Full runbook:
> [`docs/runbooks/storage-topology.md`](../../../docs/runbooks/storage-topology.md).

## Where things live

| Kind | Location | Rule |
| --- | --- | --- |
| Active `sources.db` / VESUM / hot DBs | Repository `data/` on the Mac | **Local only.** Never open SQLite from SMB or another network filesystem. |
| Bulk raw sources (primary) | Windows NTFS share **UkrainianData** → `raw-sources/learn-ukrainian-data` | Prefer when mounted and **marker-valid**. |
| Bulk raw sources (fallback) | Google Drive `My Drive/Projects/learn-ukrainian-data` | Use when SMB is absent; on-demand File Provider retrieval. |
| Sources MCP | Local `data/sources.db` | An SMB outage must **not** break MCP, tests, or ordinary repo work. |

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
3. **Never** set active DB tooling to a path under `/Volumes/UkrainianData` or
   a UNC share.
4. **Never** delete, move, or auto-evict bulk corpus, Drive objects, or SMB
   payloads unless a separate operator-authorized task says so.
5. **Mac cache:** report-only. Supported reclaim is Finder **Remove Download**.
   Do not invent eviction commands.
6. **Windows mirror maintenance:** only
   `scripts/storage/windows/Copy-BulkSourcesFromDrive.ps1` (`rclone copy`, never
   sync) and `Verify-BulkSources.ps1` (receipt only after successful verify), on
   **local NTFS** via `Get-SmbShare`.

## Env overrides (optional)

| Variable | Meaning |
| --- | --- |
| `LU_BULK_ROOT` | Force bulk root (must be marker-valid) |
| `LU_SMB_BULK_ROOT` | SMB candidate |
| `LU_GDRIVE_DATA` | Drive candidate |
| `LU_SOURCES_DB` | Active DB override; **network paths are refused** |

## Privacy

Do not commit absolute operator home paths, account emails, hostnames, raw IPs,
credentials, or private corpus bodies. Share **name** `UkrainianData` and the
relative folder `learn-ukrainian-data` are the public topology labels.
