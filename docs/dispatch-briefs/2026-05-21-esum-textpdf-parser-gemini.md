# Dispatch brief — adapt `esum_ingest.py` to handle IA text.pdf format (vols 4, 5)

**Agent**: gemini (default model)
**Mode**: danger
**Worktree**: `.worktrees/dispatch/gemini/esum-textpdf-parser-2026-05-21` (REQUIRED)
**Task ID**: `esum-textpdf-parser-2026-05-21`
**Issue**: #2174
**Created**: 2026-05-21

## Why

Gemini-2.5-flash re-OCR project (issue #2001) was killed today after a bake-off found 97% wrong-page hallucination. Replacement path uses Internet Archive's pre-extracted text layers. Vols 4 and 5 don't have ABBYY XML on IA — they only have `_text.pdf` (searchable PDF with text layer). This issue covers the text.pdf parser path.

See `docs/session-state/2026-05-21-issue-2001-ocr-handoff.md` § E for the IA-format inventory.

## What

Adapt `scripts/ingest/esum_ingest.py` to handle text.pdf-derived input alongside the existing djvutxt path.

### Source files (gitignored, local at `data/raw/esum/ia-text-pdf/`)

- `vol4-text.pdf` (39 MB) → `vol4-text.txt` (4.0 MB, extracted via `pdftotext` no `-layout`)
- `vol5-text.pdf` (43 MB) → `vol5-text.txt` (4.2 MB, same)

Re-downloadable from `https://archive.org/download/etslukrmov{4,5}/tom %20{4,5}*_text.pdf` if the local files are missing.

### Bug profile (measured before this dispatch)

| Pipeline | Entries parsed (vol4) | Expected | Status |
|---|---|---|---|
| djvutxt baseline | ~5,000-6,000 | ~6,088 | works (current deployed) |
| `pdftotext` (no `-layout`) | 1,042 | ~6,088 | broken — 80% loss |
| `pdftotext -raw` | 1 | ~6,088 | catastrophically broken |

Parser entry-boundary heuristics assume djvutxt's specific line-break conventions; text.pdf flows text differently because it is a real PDF text layer, not a flat OCR dump.

### Touch points

1. **`scripts/ingest/esum_ingest.py`**:
   - Add a `--source-format {djvutxt,text-pdf}` flag (default `djvutxt` for backward compat).
   - New parser branch for text.pdf: handle pdftotext's column-flow conventions (line wraps, paragraph re-flow, column-break artifacts).
   - Re-use the existing emission code: same JSONL schema (`lemma, vol, page, etymology_text, ...`), same lemma-extraction heuristics where they apply.
   - Keep the existing djvutxt branch byte-identical for backward compat (regression-protect with a test).

2. **Tests** (`tests/`):
   - Pytest coverage for BOTH source formats. The existing djvutxt test must keep passing unchanged.
   - New test for text.pdf input using a small fixture (10-20 entries) — check entry count, sample lemmas, and one full etymology body.
   - Regression assertion: vol1 djvutxt parses to ≥5,000 entries (current is 5,146 — leave a small margin).

3. **Documentation** — none beyond the CLI `--help` output and module docstring update describing the new format.

### Acceptance gates

- **Entry count parity**: parser run on `vol4-text.txt` produces ≥4,800 entries (80% of 6,088); same for vol5 (≥80% of current deployed).
- **Spot-check 5 random pages**: lemmas + etymology bodies match the actual scan content (cross-check `data/raw/esum/vol4.txt` djvutxt as ground truth for the same pages).
- **Pytest green** for both branches: `.venv/bin/python -m pytest tests/ -k esum -v`.
- **Ruff green**: `.venv/bin/ruff check scripts/ingest/`.

## Don't

- Don't touch vols 1, 2, 3, 6 — those go through the ABBYY XML path (separate dispatch, #2175).
- Don't reload `data/sources.db` — that's #2176, downstream.
- Don't modify the existing djvutxt parser branch (regression-test it stays at 5,146 entries for vol1).
- Don't invent a new JSONL schema. Match what `data/processed/esum_vol*.jsonl` already uses.

## Verification before commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ingest/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k esum -v --tb=short
# Smoke-run on real data:
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/ia-text-pdf/vol4-text.txt --output /tmp/esum_vol4_textpdf.jsonl --vol 4 --source-format text-pdf
wc -l /tmp/esum_vol4_textpdf.jsonl   # ≥ 4800
# Regression — djvutxt path unchanged:
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/vol1.txt --output /tmp/esum_vol1_djvu.jsonl --vol 1
wc -l /tmp/esum_vol1_djvu.jsonl     # ≥ 5140
```

All green required before commit. Per `#M-7`: pre-commit hook is not a test run.

## Commit + PR shape

- **Branch**: `feat/esum-textpdf-parser-2026-05-21`
- **One or two conventional commits** (parser change + tests can be one; CLI/docstring polish can be a second).
- **PR title**: `feat(esum): add text.pdf parser branch for IA vols 4 + 5`
- **PR body**: link issue #2174, link this brief, paste the smoke-run line counts, name the entry-boundary heuristic chosen.
- **Do NOT auto-merge.** Orchestrator (Claude) reviews and merges after `gh pr checks {N} --watch` passes.

## Steps (mandatory)

1. `git worktree add -B feat/esum-textpdf-parser-2026-05-21 .worktrees/dispatch/gemini/esum-textpdf-parser-2026-05-21 origin/main`
2. Read `scripts/ingest/esum_ingest.py` end-to-end to understand the djvutxt heuristics before changing anything.
3. Inspect `data/raw/esum/ia-text-pdf/vol4-text.txt` to understand what pdftotext output actually looks like (head/tail + grep for entry-boundary patterns).
4. Implement `--source-format` flag and the text.pdf branch.
5. Write tests with a small fixture.
6. Run verification commands; iterate until green.
7. Single (or two) conventional commit(s).
8. `git push -u origin feat/esum-textpdf-parser-2026-05-21`
9. `gh pr create --title ... --body ...` (NO auto-merge).
10. Report task done with the smoke-run wc -l output in the report.

## Anti-fabrication (per #M-4)

Every "tests pass" / "ruff clean" / "PR opened" / "entries parsed = N" claim MUST be backed by literal command output (cmd + cwd + raw last lines). A bare "all green" with no transcript is invalid. Quote the actual line-count number from `wc -l`, the actual pytest summary line, the actual ruff "All checks passed!" line.
