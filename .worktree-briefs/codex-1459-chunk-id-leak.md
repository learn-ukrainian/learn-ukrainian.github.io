# Fix #1459 (P3-C) — `compiler._format_sources` S-prefix chunk-ID leakage (#1450 Fix 2a)

## Context

Residual 2% of ghost citations after #1434 lands are caused by a prompt-format collision: `compiler._format_sources` prints `Chunk ID: \`S3931\`` per source, and Gemini sometimes reads the `S`-prefixed chunk_id and writes `[S3931]` as inline citation when it means `[S7]`. 24 citations across 5 A1/A2 wikis observed. Full diagnosis: `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` §2 Pattern B2 + §4 Fix 2a.

## Scope

Small prompt-format change in `scripts/wiki/compiler.py`. No other files affected. Safe to dispatch after #1434 lands (no code conflict, same file) or in parallel.

## Fix

In `scripts/wiki/compiler.py::_format_sources` (lines 281-287):

Replace:
```python
header = " | ".join(header_parts) if header_parts else f"Source {i}"
chunk_id = chunk.get("chunk_id", "")
text = _clean_chunk_text(chunk)

parts.append(f"### Source {i}: {header}\n"
             f"Chunk ID: `{chunk_id}`\n\n"
             f"{text}")
```

With:
```python
header = " | ".join(header_parts) if header_parts else f"Source {i}"
chunk_id = chunk.get("chunk_id", "")
text = _clean_chunk_text(chunk)
# Strip leading "S" from textbook_sections chunk_ids so the number
# cannot be confused with the [S1]..[SN] citation format (§B2 leakage:
# writer was copying "S3931" from this line into prose).
display_ref = (
    chunk_id.removeprefix("S")
    if str(chunk.get("source_type")) == "textbook"
    else chunk_id
)

parts.append(f"### Source {i}: {header}\n"
             f"(internal ref: `{display_ref}` — cite this source as `[S{i}]`)\n\n"
             f"{text}")
```

## Test

Extend `tests/test_wiki_compiler.py` with a case:
- Given `sources=[{"chunk_id": "S3931", "source_type": "textbook", ...}]`
- Assert formatted prompt contains `"internal ref: \`3931\`"` and `"cite this source as \`[S1]\`"`
- Assert formatted prompt does NOT contain `"Chunk ID: \`S3931\`"`

## Verify

1. `.venv/bin/pytest tests/test_wiki_compiler.py` green
2. `.venv/bin/pytest` full suite green
3. Live smoke: compile one A1 wiki (`scripts/wiki/compile.py --track a1 --slug where-is-it --force`); confirm no `[S\d+]` citations > retrieved N in the output body

## PR

Title: `fix(wiki): disambiguate chunk-ID label — strip S-prefix to stop citation leakage (#1450 Fix 2a) (#1459)`

Push + open PR. Do NOT auto-merge.

## Worktree

`.worktrees/codex-1459-chunk-id-leak` on branch `codex/1459-chunk-id-leak` (already created from origin/main).

## References

- `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` §2 Pattern B2 + §4 Fix 2a
- GH #1459 — P3-C of EPIC #1451
