# Plan: Admin/Maintenance API + Dashboard

## Context

The project has a Qdrant vector DB (561 MB, Docker), a SQLite message broker, scattered logs, and various maintenance scripts — but no centralized way to backup, health-check, or maintain them. The user wants:

1. Qdrant backup (to iCloud/Google Drive)
2. Other periodic maintenance tasks behind API calls
3. A dashboard page to trigger these operations

The existing FastAPI server (`scripts/api/main.py`, port 8765) already has modular routers for RAG, comms, state, images. Adding an `admin_router.py` follows the established pattern.

**Issue**: To be created after plan approval.

## What Maintenance Operations Do We Need?

| Operation | Frequency | Current State |
|-----------|-----------|---------------|
| Qdrant backup (snapshot → file) | Before risky ops / weekly | Manual `tar` only |
| Qdrant collection stats | On-demand | Exists in `rag_router.py /api/rag/stats` |
| Qdrant re-index (text/images/literary) | After new scraping/extraction | Manual CLI scripts |
| Message broker cleanup (stale msgs) | Weekly | Exists: `POST /api/comms/cleanup` |
| Message broker vacuum (SQLite) | Monthly | Not implemented |
| Log cleanup (scattered in `logs/`, `.mcp/`) | Monthly | Not implemented |
| Disk usage report | On-demand | Not implemented |
| Image annotation stats | On-demand | Manual `--stats` flag on script |
| Embedding cache stats | On-demand | Manual `--stats` flag on script |

## Step 1: Create `scripts/api/admin_router.py`

New router at `/api/admin/` with these endpoints:

### Backup
- `POST /api/admin/backup/qdrant` — Create Qdrant snapshot via REST API (`POST http://localhost:6333/snapshots`), then copy snapshot file to a configurable backup dir (default: `~/Library/Mobile Documents/com~apple~CloudDocs/learn-ukrainian-backups/` for iCloud, or `data/backups/` for local). Returns snapshot path + size.
- `GET /api/admin/backup/list` — List existing backups with timestamps and sizes.
- `DELETE /api/admin/backup/{filename}` — Delete old backup.

### Health
- `GET /api/admin/health` — Unified health check: Qdrant status, Docker container status, disk usage for `data/`, message broker DB status, API uptime.
- `GET /api/admin/disk-usage` — Breakdown: `data/qdrant/storage/`, `data/textbook_images/`, `data/textbooks/`, `data/literary_texts/`, `data/textbook_chunks/`, `logs/`, `data/vesum.db`.

### Maintenance
- `POST /api/admin/maintenance/vacuum-broker` — `VACUUM` the SQLite message broker DB.
- `POST /api/admin/maintenance/clean-logs` — Rotate/delete logs older than N days (default 30). Covers `logs/`, `.mcp/servers/*/logs/`.
- `GET /api/admin/maintenance/embedding-cache-stats` — Show cache status from `data/literary_texts/.embed_cache/`.
- `GET /api/admin/maintenance/annotation-stats` — Image annotation quality stats (teaching_value distribution, empty descriptions, garbled encoding count).

### Collection Management
- `GET /api/admin/collections` — Extended stats: points count, disk vs on-disk JSONL count, coverage gaps per grade/collection.
- `POST /api/admin/collections/verify` — Compare Qdrant point counts vs JSONL chunk counts for all three collections, report gaps.

## Step 2: Create `playgrounds/admin.html`

Simple dashboard page (follows existing playground pattern — single HTML file with fetch calls to API).

### Layout

```
┌─────────────────────────────────────────────┐
│  🔧 Admin & Maintenance                     │
├──────────┬──────────────────────────────────┤
│          │                                  │
│ Backup   │  [Create Qdrant Backup]          │
│          │  Last backup: 2026-03-01, 561 MB │
│          │  Backups: (list with delete)      │
│          │                                  │
├──────────┼──────────────────────────────────┤
│          │                                  │
│ Health   │  Qdrant: ● green (35K points)    │
│          │  Broker: ● healthy (12 KB)       │
│          │  Disk: 4.2 GB total              │
│          │                                  │
├──────────┼──────────────────────────────────┤
│          │                                  │
│ Maintain │  [Vacuum Broker DB]              │
│          │  [Clean Old Logs]                │
│          │  [Verify Collections]            │
│          │                                  │
├──────────┼──────────────────────────────────┤
│          │                                  │
│ Stats    │  Embedding cache: 147/162 cached  │
│          │  Image annotations: 11,478        │
│          │    high: 1,947 | garbled: 159    │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

### Interaction
- Buttons trigger POST endpoints, show spinner, display result
- Health section auto-refreshes every 30s
- No frameworks — vanilla HTML/CSS/JS (matches existing playgrounds)

## Step 3: Wire Up

### `scripts/api/main.py`
Add 2 lines:
```python
from .admin_router import router as admin_router
app.include_router(admin_router, prefix="/api/admin")
```

### `playgrounds/index.html`
Add link to admin page in the nav.

### Backup directory
Default to `data/backups/` (gitignored). User can configure iCloud path via env var `BACKUP_DIR`.

## Key Files

| File | Action |
|------|--------|
| `scripts/api/admin_router.py` | **CREATE** — all admin endpoints |
| `playgrounds/admin.html` | **CREATE** — dashboard UI |
| `scripts/api/main.py` | **EDIT** — mount admin router (2 lines) |
| `playgrounds/index.html` | **EDIT** — add admin link |
| `.gitignore` | **EDIT** — add `data/backups/` |
| `scripts/api/rag_router.py` | READ — reuse `_qdrant_available()` pattern |
| `scripts/api/comms_router.py` | READ — reuse broker DB connection pattern |

## What Does NOT Change

- Qdrant Docker setup — unchanged
- Existing routers — no modifications
- MCP servers — unchanged
- Ingestion scripts — unchanged (admin only reports stats, doesn't trigger re-ingestion)

## Verification

1. Start API: `npm run api:reload`
2. Test backup: `curl -X POST http://localhost:8765/api/admin/backup/qdrant`
3. Test health: `curl http://localhost:8765/api/admin/health`
4. Test disk: `curl http://localhost:8765/api/admin/disk-usage`
5. Test verify: `curl -X POST http://localhost:8765/api/admin/collections/verify`
6. Open dashboard: `http://localhost:8765/admin.html`
7. Click "Create Backup" — verify file appears in `data/backups/`
