# Dispatch brief — ABBYY FineReader XML parser for ЕСУМ (vols 1, 2, 3, 6)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/codex/esum-abbyy-parser-2026-05-21` (REQUIRED)
**Task ID**: `esum-abbyy-parser-2026-05-21`
**Issue**: #2175
**Created**: 2026-05-21

## Why

Issue #2001 (Gemini re-OCR) was killed after a bake-off found 97% wrong-page hallucination. Replacement uses IA's pre-extracted text layers. ABBYY FineReader XML is the gold-standard structured source for vols 1, 2, 3, 6 (vols 4, 5 lack ABBYY — they go through the separate text.pdf parser, #2174).

ABBYY XML provides explicit `<page>` / `<block>` / `<par>` / `<line>` / `<charParams>` structure — that's signal a flat-text parser can't recover. Bounding boxes preserve italic/bold formatting that distinguishes headwords from body. This is structurally superior to djvutxt.

See `docs/session-state/2026-05-21-issue-2001-ocr-handoff.md` § E for IA-format inventory and `audit/etymology-ocr-bakeoff/REPORT.md` (branch `codex/esum-bakeoff-2026-05-21`) for quality measurements (text.pdf vs ABBYY cross-validation: mean Jaccard 0.953).

## What

Write a new ABBYY XML parser for ЕСУМ, emitting the same JSONL schema as the existing djvutxt parser. This is **novel implementation** — not a tweak. Treat the existing `esum_ingest.py` as reference for the output schema and for the entry-validation heuristics (homonym markers, body-start / body-end anchors, page tracking), but the input-side reading code is new.

### Source files (gitignored, local at `data/raw/esum/ia-abbyy-xml/`)

- `vol1-abbyy.xml` (482 MB, 634 pages)
- `vol2-abbyy.xml` (438 MB, 573 pages)
- `vol3-abbyy.xml` (421 MB, 553 pages)
- `vol6-abbyy.xml` (419 MB, 569 pages)

Also `vol{1,2,3,6}-abbyy.gz` compressed. Re-downloadable from `https://archive.org/download/etslukrmov{1,2,3,6}/*_abbyy.gz` if missing.

### Schema (FineReader10-schema-v1)

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<document xmlns="http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml">
  <page width="N" height="N" ...>
    <block blockType="Text" ...>
      <text>
        <par>
          <line baseline="N" ...>
            <formatting ff="..." italic="1" bold="1" ...>
              <charParams l="x" t="y" r="x2" b="y2">а</charParams>
              ...
```

Reference: <https://support.abbyy.com/hc/en-us/articles/360017269940>.

Use `lxml` (already in repo deps; see `requirements.txt`). `lxml.etree.iterparse` for streaming — these XMLs are ~450 MB each, you cannot load them whole into memory at scale.

### Touch points

1. **New module**: `scripts/ingest/esum_abbyy_parser.py` (preferred over adding a `--source-format abbyy` branch — these files are large enough that the parsing surface is meaningfully different). Mirror the CLI shape of `esum_ingest.py` (`--input`, `--output`, `--vol`).

   Alternatively, if you find a clean refactor that adds `--source-format abbyy` to `esum_ingest.py` without bloating it past readability, that's acceptable — but the streaming-XML reader is enough new code that a separate module is the more defensible choice. Document the choice in the commit message.

2. **Parser core**:
   - Stream `<page>` elements via `iterparse`, `clear()` each one to free memory.
   - Within a page, iterate `<line>` in reading order. Reconstruct line text from `<charParams>` (concatenate the character data; respect ordering as given).
   - Detect entry boundaries using `<par>` structure + headword formatting cues (bold/italic on the leading character span). Headwords in ЕСУМ are typeset distinctly — exploit this. Document the boundary heuristic in module docstring with at least 3 concrete examples.
   - Track page number from the page index (1-based) or from the page's printed footer if one is reliably parsed; document which you chose.
   - Emit JSONL matching `data/processed/esum_vol1.jsonl` schema exactly: `{lemma, vol, page, etymology_text, ...}`. Inspect a current sample to confirm field names.

3. **Cross-validation gate** (the deliverable proof):
   - Run the new parser on `vol1-abbyy.xml`.
   - Compare lemma set against the existing `data/processed/esum_vol1.jsonl`.
   - Expectation: ~5,146 entries (current djvutxt count), substantially-overlapping lemma sets where current entries are correct. **The new parser should NOT replicate the deployed lemma-extraction bugs visible in spot-checks** (e.g., the wrong-lemma case at vol4/p0250 documented in the handoff).
   - Produce a small diff report in the PR body: total entries, overlap count, sample of lemmas the new parser improved.

4. **Tests** (`tests/`):
   - Small XML fixtures (one valid `<page>` with 2-3 entries, plus an edge case like a continuation paragraph).
   - Unit test for `<charParams>` → line text reconstruction.
   - Unit test for entry-boundary detection on a fixture page.
   - Integration test that runs end-to-end on a fixture and asserts on output JSONL count + first lemma.

5. **Documentation**:
   - Module docstring with schema reference + worked-example of the entry-boundary heuristic.
   - Add a line to `scripts/ingest/README.md` (or create it if absent) describing when to use which parser.

### Acceptance gates

- **Entry-count parity** for vol1: parser produces 4,800-5,500 entries (current deployed is 5,146; allow ±10% for boundary-detection differences that may net out as improvements or losses).
- **Pytest green**: `.venv/bin/python -m pytest tests/ -k 'esum or abbyy' -v`.
- **Ruff green**: `.venv/bin/ruff check scripts/ingest/ tests/`.
- **Memory bound**: parser must complete on the largest XML (vol1, 482 MB) without exceeding ~1 GB RSS. Use `/usr/bin/time -l` (macOS) to measure; report peak.

## Don't

- Don't touch vols 4, 5 — those are the text.pdf parser path (#2174).
- Don't reload `data/sources.db` — that is #2176, downstream.
- Don't load the whole XML into memory (`lxml.etree.parse()` is forbidden on these files). Use `iterparse` + `clear()`.
- Don't invent a new JSONL schema. Match `data/processed/esum_vol*.jsonl` field names exactly.
- Don't widen scope to vols 4, 5 if you "happen to find" ABBYY files for them — IA doesn't have them. If you think you do, stop and ask.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ingest/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k 'esum or abbyy' -v --tb=short
# Smoke-run on real data:
cd /Users/krisztiankoos/projects/learn-ukrainian && /usr/bin/time -l .venv/bin/python scripts/ingest/esum_abbyy_parser.py --input data/raw/esum/ia-abbyy-xml/vol1-abbyy.xml --output /tmp/esum_vol1_abbyy.jsonl --vol 1
wc -l /tmp/esum_vol1_abbyy.jsonl   # 4800-5500
# Sample diff vs deployed:
head -3 /tmp/esum_vol1_abbyy.jsonl
head -3 data/processed/esum_vol1.jsonl
```

All green required before commit. Per `#M-7`: pre-commit hook is not a test run.

## Commit + PR shape

- **Branch**: `feat/esum-abbyy-parser-2026-05-21`
- **One commit** (parser + tests + docs together; this is a coherent feature).
- **PR title**: `feat(esum): ABBYY XML parser for vols 1, 2, 3, 6`
- **PR body**: link issue #2175, link this brief, paste the smoke-run wc -l + peak RSS + lemma-overlap stats, describe the entry-boundary heuristic in 2-3 sentences.
- **Do NOT auto-merge.** Orchestrator reviews and merges.

## Steps (mandatory)

1. `git worktree add -B feat/esum-abbyy-parser-2026-05-21 .worktrees/dispatch/codex/esum-abbyy-parser-2026-05-21 origin/main`
2. Read `scripts/ingest/esum_ingest.py` end-to-end to understand the JSONL schema + existing entry-validation heuristics.
3. Inspect a small slice of `vol1-abbyy.xml` to understand the structure (xmllint --shell, head, etc.). DO NOT pretty-print the whole 482 MB file.
4. Implement the parser as a streaming iterator.
5. Write tests + small XML fixtures.
6. Run verification; iterate until green.
7. Single conventional commit.
8. `git push -u origin feat/esum-abbyy-parser-2026-05-21`
9. `gh pr create --title ... --body ...` (NO auto-merge).
10. Report task done with wc -l + peak RSS + first 3 emitted lemmas.

## Anti-fabrication (per #M-4)

Every "tests pass" / "ruff clean" / "PR opened" / "entries parsed = N" / "peak RSS = N MB" claim MUST be backed by literal command output (cmd + cwd + raw last lines). A bare "all green" with no transcript is invalid. Quote the actual numbers — `wc -l` raw output, pytest summary line raw, ruff "All checks passed!" raw, `/usr/bin/time -l` raw `maximum resident set size` line.
