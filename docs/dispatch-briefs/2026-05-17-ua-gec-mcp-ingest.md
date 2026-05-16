# Dispatch brief: UA-GEC ingest + MCP tool (PENDING H2 CONFIRM)

**Status:** READY TO FIRE. H2 (PR #2049) confirmed UA-GEC earned 9 of 33 sev≥2 flag citations across 6 models — the only NEW channel that converted into actual evidence anchors. Tag filter updated per H2 lessons (F/Style dropped).

**Agent:** Gemini headless (unmetered, mechanical ingest pattern — see #M0 row 2 "running existing scripts, ingestion runs")
**Mode:** `--mode danger`
**Base branch:** `main`
**Task ID:** `ua-gec-mcp-ingest-2026-05-17`

## Why this work

H2 (PR #TBD) validated that UA-GEC's ~7K annotated error pairs are a
high-signal evidence source for russianism judging — but only via an
inline judge-harness helper. This brief promotes that capability to
the project-wide MCP surface so that writers, reviewers, ad-hoc agent
queries, and the `ab ask-*` bridge all benefit from the same evidence
layer the judge gained.

UA-GEC source: `data/ua-gec/` (already cloned, MIT-licensed, ~4,162
annotated essay files, professional-annotator quality, Grammarly UA
team).

## Source data quality (verified 2026-05-17)

Tag distribution across all 4,162 .ann files:

| Tag | Count | Relevance to russianism judging |
|---|---|---|
| `F/Calque` | 2,397 | **HIGHEST** — direct russianism calques |
| `F/Style` | 3,725 | high — register/word choice (often russianism-adjacent) |
| `F/Collocation` | 459 | high — unnatural pairings |
| `G/Case` | 5,024 | medium — russian-pattern case usage |
| `G/Gender` | 1,057 | medium — russian-pattern gender |
| `Punctuation` / `Spelling` | 57,365 | low — not russianism-related, EXCLUDE |

Default tag filter (CONFIRMED from H2 PR #2049 §3): `{F/Calque,
F/Collocation, G/Case, G/Gender}` — total ~8,937 high-signal
annotations. **F/Style EXCLUDED** — H2 diagnostic showed F/Style triggers
canonical-greeting near-misses (`Доброго дня → Добрий день`) and adds
no calque signal beyond what F/Calque already provides.

## Deterministic claims (#M-4)

| Claim | Required evidence |
|---|---|
| "ua_gec_errors table created with N rows" | raw `sqlite3 data/sources.db "SELECT COUNT(*) FROM ua_gec_errors"` |
| "FTS5 index live" | raw `sqlite3 data/sources.db "SELECT COUNT(*) FROM ua_gec_errors_fts"` matches main table |
| "MCP tool registered" | raw `grep -c 'search_ua_gec_errors' .mcp/servers/sources/server.py` ≥ 3 |
| "Smoke test passes" | raw pytest output of new `tests/mcp/test_ua_gec_search.py` |
| "Rule file updated" | raw `grep -c 'search_ua_gec' .claude/rules/mcp-sources-and-dictionaries.md` ≥ 1 AND same in `claude_extensions/rules/...` source |
| "PR opened, not merged" | raw `gh pr view --json url,state` line OPEN |

## Numbered execution steps

### 1. Worktree + data symlink

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/ua-gec ]     || { rm -f data/ua-gec;     ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/ua-gec     data/ua-gec; }
```

**WARNING:** `data/sources.db` is the production DB (~1.6 GB). All
writes must be transactional. ALWAYS back up before running ingest:

```
cp data/sources.db data/sources.db.bak-pre-ua-gec
```

### 2. Use the upstream UA-GEC python library

```
.venv/bin/python -m pip install -e data/ua-gec/python
.venv/bin/python -c "from ua_gec import Corpus; c = Corpus('gec-only', 'train'); print(len(list(c)))"
```

DO NOT write a custom .ann parser — upstream `ua_gec.annotated_text`
already handles the format correctly, including edge cases (nested
annotations, whitespace, multi-byte characters). Use `Corpus(...)` and
`AnnotatedText.iter_annotations()`.

### 3. Build the ingest script `scripts/ingest/ua_gec_ingest.py`

Skeleton:

```python
import sqlite3
from pathlib import Path
from ua_gec import Corpus

INCLUDED_TAGS = {"F/Calque", "F/Style", "F/Collocation", "G/Case", "G/Gender"}  # TBD-confirm-from-H2

def ingest(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ua_gec_errors (
                id INTEGER PRIMARY KEY,
                error TEXT NOT NULL,
                correct TEXT NOT NULL,
                error_type TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                annotator_id TEXT NOT NULL,
                partition TEXT NOT NULL,
                is_native INTEGER,
                source_lang TEXT
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS ua_gec_errors_fts
            USING fts5(error, correct, error_type, content='ua_gec_errors', content_rowid='id', tokenize='unicode61')
        """)
        # Triggers to keep FTS in sync
        # Trim any existing rows first (idempotent)
        conn.execute("DELETE FROM ua_gec_errors")
        conn.execute("DELETE FROM ua_gec_errors_fts")

        rows = 0
        for partition in ("gec-only/train", "gec-only/test", "gec-fluency/train", "gec-fluency/test"):
            collection, split = partition.split("/")
            corpus = Corpus(collection, split)
            for doc in corpus:
                for ann in doc.annotated.iter_annotations():
                    if ann.meta.get("error_type") not in INCLUDED_TAGS:
                        continue
                    conn.execute(
                        "INSERT INTO ua_gec_errors(error, correct, error_type, doc_id, annotator_id, partition, is_native, source_lang) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (ann.source_text, ann.top_suggestion, ann.meta["error_type"],
                         doc.doc_id, doc.annotator_id, partition,
                         int(doc.meta.is_native or 0), doc.meta.source_language)
                    )
                    rows += 1
        # Populate FTS
        conn.execute("INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type) SELECT id, error, correct, error_type FROM ua_gec_errors")
        conn.commit()
        return rows
    finally:
        conn.close()
```

Tests in `tests/ingest/test_ua_gec_ingest.py`:
- After ingest, table count > 8000 (rough lower bound on 12K with tag filter)
- FTS row count matches main table count
- Known-russianism query (e.g. `повістка дня`) returns ≥1 hit with `error_type IN ('F/Calque', 'F/Style')`

### 4. Run the ingest

```
.venv/bin/python -m scripts.ingest.ua_gec_ingest --db data/sources.db
sqlite3 data/sources.db "SELECT error_type, COUNT(*) FROM ua_gec_errors GROUP BY error_type ORDER BY 2 DESC"
```

### 5. Add MCP tool to `.mcp/servers/sources/server.py`

Follow the existing `search_style_guide` pattern (server.py:601, 1156,
1237, 1938). Add:

- Tool schema entry (after `search_style_guide` tool definition)
- Handler in the dispatch table
- Backend method in `sdb` module (wherever `search_style_guide` lives)

Signature:

```python
search_ua_gec_errors(
    query: str,
    *,
    tag_filter: list[str] | None = None,  # default: all included tags
    limit: int = 10,
    require_native_author: bool = False,
) -> list[dict]
```

Returns rows with `error`, `correct`, `error_type`, `doc_id`,
`is_native`, `source_lang`. Use FTS5 MATCH with tokenizer `unicode61`
(unicode-safe; Ukrainian-aware).

### 6. Smoke test the MCP tool

Boot the sources MCP server in a subshell, call the new tool via the
MCP test client (see existing `tests/mcp/` patterns), verify it
returns hits on a known russianism. New test file:

```
tests/mcp/test_ua_gec_search.py
```

### 7. Update rule file (source + deploy target)

`claude_extensions/rules/mcp-sources-and-dictionaries.md` AND
`.claude/rules/mcp-sources-and-dictionaries.md` (keep in sync).

Add to "Dictionary tools" section:

```
- `mcp__sources__search_ua_gec_errors` — UA-GEC (Ukrainian Grammatical
  Error Corpus, Grammarly UA team, MIT). Returns human-annotated
  error→correction pairs from N rows, filtered to russianism-relevant
  tags (F/Calque, F/Style, F/Collocation, G/Case, G/Gender). Highest-
  signal evidence for register/phraseological calques that aren't in
  Antonenko. Pair with `search_style_guide` (structured Antonenko)
  and `search_text source=antonenko-davydovych-yak-my-hovorymo`
  (full-text Antonenko prose) for the complete russianism evidence
  layer.
```

Update the "Dictionaries" table at the bottom with the new row.

### 8. Update `_judge_eval_lib.py` (optional but consistent)

Once the MCP tool exists, the judge harness can call it via the local
DB path instead of file-system scan. Less code, faster, consistent
with the rest of the project. Replace the inline UA-GEC index scan
from H2 with a thin wrapper around the new DB table.

### 9. Tests + lint + commit + PR (no auto-merge)

Standard checklist.

## Hard rules

- BACKUP `data/sources.db` before any write.
- Use the upstream `ua_gec` Python library for parsing — do not
  reinvent.
- Tag filter set must match what H2 confirmed valuable. If H2 showed
  F/Style was noisy, drop it from `INCLUDED_TAGS`.
- License header in the schema migration: "Source: ua-gec by Grammarly
  Ukraine, MIT licensed."
- Don't include high-volume low-signal tags (Punctuation, Spelling) —
  they'll bloat FTS by 50K rows for zero russianism value.
- No `--no-verify` on commits.
- No auto-merge.

## What you do NOT do

- Don't touch any other table in `sources.db`.
- Don't run if `data/sources.db.bak-pre-ua-gec` write fails (no
  backup → no proceed).
- Don't ingest the full document text — only the error→correct
  annotation pairs.
- Don't skip the smoke test even if the ingest counts look right.
