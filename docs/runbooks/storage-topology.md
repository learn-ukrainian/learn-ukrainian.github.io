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
