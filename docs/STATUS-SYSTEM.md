# Status Cache System (v2.0)

This document describes how the incremental status tracking system works.

## Problem

Auditing 1000+ modules takes ~30 minutes if done sequentially. This makes generating a "Current Status" report painfully slow and wasteful.

## Solution

We use a JSON-based status cache that stores the results of the last successful audit.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       AUDIT PIPELINE                              │
│                                                                   │
│   .venv/bin/python scripts/audit_module.py {module}.md           │
│                                                                   │
│   1. Runs all validation checks                                  │
│   2. Generates review file in audit/                             │
│   3. Writes status cache to status/{slug}.json                   │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STATUS CACHE (JSON)                          │
│                                                                   │
│   curriculum/l2-uk-en/{level}/status/{slug}.json                 │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STATUS GENERATION                               │
│                                                                   │
│   .venv/bin/python scripts/generate_level_status.py {level}      │
│                                                                   │
│   1. Reads JSON cache files (fast path)                          │
│   2. Falls back to subprocess audit (slow path if stale)         │
│   3. Generates docs/{LEVEL}-STATUS.md                            │
└─────────────────────────────────────────────────────────────────┘
```

## Structure

Audit results are cached per-module in:
`curriculum/l2-uk-en/{level}/status/{slug}.json`

### Schema

The cache follows `schemas/module-status.schema.json`:

```json
{
  "timestamp": "2026-01-26T12:00:00Z",
  "source_file": "curriculum/l2-uk-en/b2-hist/kozatstvo-vytoky.md",
  "source_mtimes": {
    "md": 1706270400,
    "meta": 1706270400,
    "activities": 1706270400,
    "vocabulary": 1706270400,
    "plan": 1706270400
  },
  "word_count": 4250,
  "word_target": 4000,
  "activity_count": 18,
  "unique_activity_types": 6,
  "vocabulary_count": 35,
  "naturalness_score": 9,
  "naturalness_status": "PASS",
  "gates": {
    "words": "PASS",
    "activities": "PASS",
    "unique_types": "PASS",
    "engagement": "PASS",
    "naturalness": "PASS"
  },
  "overall": "PASS",
  "violations": [],
  "warnings": []
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `timestamp` | When the audit was run |
| `source_mtimes` | Modification times of all source files |
| `gates` | PASS/FAIL status for each audit gate |
| `overall` | Global status and list of blocking issues |
| `violations` | Array of FAIL-level issues |
| `warnings` | Array of WARN-level issues |

## Workflow

### 1. Generation (Automatic)

The status cache is updated every time `scripts/audit_module.py` is run:
- If audit passes → status is `PASS`
- If audit fails → status is `FAIL` + list of issues

### 2. Retrieval (Instant)

Commands like `/module-status` and `/level-status` read directly from the JSON files.

Status generation scripts (`scripts/generate_level_status.py`) use the cache-first approach:

1. Check if `{slug}.json` exists
2. Compare `source_mtimes` in JSON with current file mtimes on disk
3. If files are unchanged → **USE CACHE** (Instant)
4. If any file is newer than the cache → **RE-AUDIT** only that module

## Commands

### View Module Status

```bash
/module-status b1 5
```

Reads from `b1/status/{slug}.json` and displays:
- Gate status (words, activities, naturalness, etc.)
- Word count vs target
- Violations and warnings

### View Level Status

```bash
/level-status b1
```

Reads all JSON files in `b1/status/` and generates summary:
- Total modules
- Modules by status (PASS/FAIL/PENDING)
- Common violations

### Force Re-audit

If you suspect the cache is stale but timestamps haven't changed:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{file}.md
```

### npm Commands

```bash
npm run status:b1        # Generate B1 status from cache
npm run status:b2-hist   # Generate B2-HIST status from cache
npm run status:all       # Generate all levels
```

## Performance

| Operation | Without Cache | With Cache |
|-----------|--------------|------------|
| Single module status | ~30s | ~0.1s |
| Level status (100 modules) | ~50 min | ~5s |
| Full curriculum status | ~8 hours | ~1 min |

**Speed improvement:** ~300x for cached lookups.

## Benefits

- **Speed**: Full level status in < 5 seconds (previously 30s+)
- **Persistence**: Status persists across sessions without re-auditing
- **Granularity**: Detailed failure reasons are stored machine-readably
- **Incremental**: Only stale modules are re-audited

## Integration with QA Commands

All QA commands update the status cache automatically:

| Command | Updates Cache |
|---------|---------------|
| `/module-lesson-qa` | ✅ |
| `/module-act-qa` | ✅ |
| `/module-vocab-qa` | ✅ |
| `/module-fix` | ✅ (after each iteration) |

## Troubleshooting

### Cache Out of Sync

If status doesn't match reality:

```bash
# Force re-audit to refresh cache
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

### Missing Cache

If cache file doesn't exist, commands will fall back to running a full audit.

### Bulk Cache Regeneration

To regenerate cache for an entire level:

```bash
# Audits all modules and updates their cache files
.venv/bin/python scripts/generate_level_status.py {level}
```

## Related Documentation

- `docs/ARCHITECTURE-PLANS.md` - Three-layer architecture (plans, content, status)
- `docs/PLANNING-GUIDE.md` - How to create/update plans
- `docs/SCRIPTS.md` - Script reference
- `claude_extensions/commands/module-status.md` - Module status command
- `claude_extensions/commands/level-status.md` - Level status command
