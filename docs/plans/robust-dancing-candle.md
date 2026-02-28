# Plan: Import VESUM Morphological Dictionary (#694)

## Context

Both Claude and Gemini hallucinate Ukrainian word forms (e.g., горонька, сльозонька). RAG vector search catches some errors but can't verify isolated forms. VESUM (415K headwords, ~4-6M inflected forms) provides exact morphological lookup: "is this a real Ukrainian word?" — yes/no + lemma + POS + tags. This replaces Claude Phase D reviews for morphological correctness.

## Approach

### Step 1: Download VESUM data

- Download `dict_corp_vis.txt.bz2` from GitHub releases v6.7.5 (17.4 MB)
- Decompress to `data/vesum/dict_corp_vis.txt` (~100-150 MB)
- Add `data/vesum/` to `.gitignore`

### Step 2: Build import script (`scripts/rag/import_vesum.py`)

Parse the visual/indented format:
- Unindented line = new lemma (format: `word_form tags`)
- Indented line (2 spaces) = inflected form of current lemma (format: `  word_form tags`)
- Extract: `word_form`, `lemma` (carried from last unindented line), `tags` (full colon-separated string), `pos` (first tag token)

Build SQLite database at `data/vesum.db`:
```sql
CREATE TABLE forms (
    word_form TEXT NOT NULL,
    lemma TEXT NOT NULL,
    tags TEXT NOT NULL,
    pos TEXT NOT NULL
);
CREATE INDEX idx_form ON forms(word_form);
CREATE INDEX idx_lemma ON forms(lemma);
```

Register filtering during import:
- Skip entries tagged `bad` (incorrect forms)
- Keep `vulg`, `obsc`, `arch`, `rare`, `coll` but store the tags (filter at query time, not import time — curriculum modules filter, but the dictionary should be complete)

### Step 3: Add VESUM query functions (`scripts/rag/query.py`)

Add two functions using lazy-loaded SQLite connection:

```python
_vesum_conn = None  # Lazy-loaded, same pattern as _qdrant_client

def verify_word(word: str) -> list[dict]:
    """Check if a word form exists in VESUM. Returns list of {lemma, pos, tags} matches."""

def verify_lemma(lemma: str) -> list[dict]:
    """Get all inflected forms of a lemma. Returns list of {word_form, pos, tags}."""
```

### Step 4: Add MCP tools (`.mcp/servers/rag/server.py`)

Add two new tools to existing RAG server following established patterns:

1. `verify_word` — input: `word` (required), `pos_filter` (optional). Returns matches or "not found".
2. `verify_lemma` — input: `lemma` (required). Returns all forms grouped by POS.

Follow existing patterns: register in `list_tools()`, dispatch in `call_tool()`, use `asyncio.to_thread()` for SQLite queries.

### Step 5: Deploy and verify

- Run import: `.venv/bin/python scripts/rag/import_vesum.py`
- Run `npm run claude:deploy` to sync MCP server changes
- Test via MCP tools:
  - `verify_word("берізонька")` → found (noun, diminutive)
  - `verify_word("горонька")` → not found
  - `verify_word("слізонька")` → found
  - `verify_lemma("коза")` → коза, кози, козі, козу, козою, козо, кіз, козам...

## Files to create/modify

| File | Action |
|------|--------|
| `scripts/rag/import_vesum.py` | **CREATE** — download + parse + SQLite |
| `scripts/rag/query.py` | **MODIFY** — add `verify_word()`, `verify_lemma()` |
| `.mcp/servers/rag/server.py` | **MODIFY** — add 2 MCP tools |
| `.gitignore` | **MODIFY** — add `data/vesum/` |
| `scripts/rag/config.py` | **MODIFY** — add `VESUM_DB_PATH`, `VESUM_URL` constants |

## Verification

1. Run `scripts/rag/import_vesum.py` — should download, parse, build SQLite
2. Check DB: `sqlite3 data/vesum.db "SELECT COUNT(*) FROM forms"` → expect 4-6M rows
3. Check DB: `sqlite3 data/vesum.db "SELECT * FROM forms WHERE word_form='берізонька'"` → should return result
4. Check DB: `sqlite3 data/vesum.db "SELECT * FROM forms WHERE word_form='горонька'"` → should return empty
5. Restart MCP server, test `mcp__rag__verify_word` and `mcp__rag__verify_lemma` tools
6. Send to Gemini for adversarial review
