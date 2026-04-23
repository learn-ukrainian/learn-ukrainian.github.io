# #1450 follow-up — fix attribution routing + chunk-ID leakage

**Context:** closes 98% of wiki writer attribution failures surfaced by the
#1450 diagnostic. Report:
`docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md`.

**Two fixes, two files, trivial complexity.** Do NOT bundle other wiki
refactors into this PR.

## Scope

Inline code-only changes. No prompt content edits (those land in #1447).
No yaml backfill (those land in #1445).

## Fix 1 — attribution routing for textbook sections

**File:** `scripts/wiki/sources_db.py`

**Location:** `_search_sections_fts5`, the `results.append({...})` block
currently at lines 315–322.

**Before:**
```python
        results.append({
            **meta,
            **ranked,
            "text": meta["full_text"],
            "chunk_id": f"S{meta['section_id']}",
            "title": meta["section_title"],
            "source_type": "textbook",
        })
```

**After:**
```python
        results.append({
            **meta,
            **ranked,
            "text": meta["full_text"],
            "chunk_id": f"S{meta['section_id']}",
            "title": meta["section_title"],
            "source_type": "textbook",
            "corpus": "textbook_sections",
            "unit_key": f"textbook_sections:S{meta['section_id']}",
        })
```

**Why:** every sibling `_search_*_candidates` function in the same module
sets `corpus` on its result rows (literary line ~413, external line ~470,
wikipedia line ~526, ukrainian_wiki line ~604). This one alone omits it.
`compiler._build_sources_registry` reads
`source.get("corpus") or source.get("source_type")`, so without `corpus`
it falls back to `"textbook"` — which `_CORPUS_ALIASES` maps to the older
`textbooks` table, missing every real `textbook_sections` lookup and
dropping attribution to `type: unknown` + `file: S####`. One-line
contract restoration.

## Fix 2 — stop `S`-prefix chunk ID leaking into writer output

**File:** `scripts/wiki/compiler.py`

**Location:** `_format_sources`, lines 281–287.

**Before:**
```python
        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = _clean_chunk_text(chunk)

        parts.append(f"### Source {i}: {header}\n"
                     f"Chunk ID: `{chunk_id}`\n\n"
                     f"{text}")
```

**After:**
```python
        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = _clean_chunk_text(chunk)
        # Strip leading "S" from textbook_sections chunk_ids so the number
        # cannot be visually confused with the [S1]..[SN] citation format.
        # Pattern B2 leakage (see #1450 report §2): writer was copying
        # "S3931" from this line straight into prose as "[S3931]".
        display_ref = (
            chunk_id.removeprefix("S")
            if str(chunk.get("source_type")) == "textbook"
            else chunk_id
        )

        parts.append(f"### Source {i}: {header}\n"
                     f"(internal ref: `{display_ref}` — cite this source as `[S{i}]`)\n\n"
                     f"{text}")
```

**Why:** Gemini reads `Chunk ID: \`S3931\`` in the prompt, sees the
adjacent "use `[S1]` to cite" instruction, and elides the two formats,
writing `[S3931]` in prose when it means `[S7]`. 24 phantom citations
across 5 A1/A2 wikis reproduce this pattern (diagnostic report §2
Pattern B2). Removing the `S` prefix kills the literal character-shape
collision; relabelling as `internal ref` + appending the explicit
`cite this source as [S{i}]` makes the positional contract unambiguous.

## Tests

1. **New / extended unit test — `tests/test_wiki_sources_db.py`**
   (create if absent). Case: build a minimal in-memory sources.db with
   a textbook_sections row (section_id=123, etc.), run
   `_search_sections_fts5` through its public entry, assert
   `results[0]["corpus"] == "textbook_sections"` and the `unit_key` is
   well-formed.

2. **Round-trip test — `tests/test_wiki_source_attribution.py`**
   (exists per prior PR history). Case: call
   `resolve_chunk_attribution("S3931", "textbook_sections")`. Assert
   the returned dict has `type="textbook"` and
   `file` matching `r"^\d+-klas-.+_s\d+$"`. This guards against future
   regressions in the routing-key contract.

3. **New / extended — `tests/test_wiki_compiler.py`** (exists per PR
   #1447 body). Case: given
   `sources = [{"chunk_id": "S3931", "source_type": "textbook",
   "text": "...", "section_title": "..."}]`, assert `_format_sources`
   output contains `"internal ref: \`3931\`"` and
   `"cite this source as \`[S1]\`"` and does NOT contain the literal
   `"Chunk ID: \`S3931\`"` substring. Also assert a non-textbook chunk
   (`source_type="literary"`) retains its chunk_id unchanged.

## Out of scope

- `source_attribution.py` already handles `corpus="textbook_sections"`
  correctly. No change needed there.
- Writer prompt files (`compile_*.md`) are owned by #1447. Do not edit.
- Historical yaml backfill is #1445. Do not edit yamls in this PR.
- `scripts/wiki/compile.py` hooks for discipline validation are
  expected in #1447. If #1447 merges before this PR, rebase; if after,
  no conflict expected.

## Verification checklist

- [ ] `pytest tests/test_wiki_sources_db.py tests/test_wiki_source_attribution.py tests/test_wiki_compiler.py` green.
- [ ] `ruff check scripts/wiki/sources_db.py scripts/wiki/compiler.py` clean.
- [ ] Live smoke (user runs manually; DO NOT execute builds from this brief):
  - `.venv/bin/python scripts/wiki/compile.py --track b1 --slug adjectives-comparative --force`
  - Inspect `wiki/grammar/b1/adjectives-comparative.sources.yaml`.
  - Expect every entry: `type: textbook`, `file: {grade}-klas-ukrmova-{author}-{year}_s{section_id}`, `grade: {n}`.
  - No `type: unknown` + `file: S####` pairs.

## PR title

```
fix(wiki): route textbook_sections through attribution + stop S-prefix chunk-ID leakage (#1450)
```

## PR body — tl;dr

Closes #1450's §4 Fix 1 + Fix 2. Diagnosis shows 98% of observed
"phantom citations" were routing failures, not Gemini inventions; this
PR closes that routing failure. The residual 2% (true writer
inventions) is handled by #1447's mechanical validator; this PR adds
the prompt-format disambiguation that stops new inventions of
pattern B2 (raw section-id leakage into citation tokens).

## Do NOT auto-merge.
