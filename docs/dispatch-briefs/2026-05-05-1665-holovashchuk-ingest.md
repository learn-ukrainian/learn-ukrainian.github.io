# Codex Dispatch Brief — #1665 Holovashchuk Usage Dictionary Ingest

**Issue:** #1665
**Parent EPIC:** #1657
**Risk class:** MEDIUM (PDF extraction + license caveat)
**Mode:** danger (worktree)
**Agent:** Codex (mechanical pattern-apply work fits Codex strengths)
**Goal:** open a single PR fully implementing #1665's ACs. NOT auto-merged — human reviews license posture.

---

## Worktree instructions (mandatory)

Numbered explicitly per dispatch-brief checklist:

1. **Sync base:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian
   git fetch origin main
   ```

2. **Create worktree from origin/main (NOT local main):**
   ```bash
   git worktree add -b codex-1665-holovashchuk-ingest .worktrees/dispatch/codex/1665-holovashchuk-ingest origin/main
   cd .worktrees/dispatch/codex/1665-holovashchuk-ingest
   ```

3. **Verify base is current** (no commits behind origin/main):
   ```bash
   git log --oneline HEAD..origin/main  # must be empty
   ```

---

## The work (per #1665 ACs)

### AC 1: PDF extraction
- Download PDF: `https://kpdi.edu.ua/biblioteka/С/Словник-довідник%20%20з%20українського%20літературного%20слововживання%20Головащук%20С.І..pdf`
- Verify the link is live (HEAD request) before bulk download
- Save to `data/raw/holovashchuk_2004.pdf`
- Extract text via `pdftotext -layout`
- Validate output is non-empty + has Ukrainian characters

### AC 2: Entry segmentation
- Parse the extracted text into entries: `{headword, usage_advice_block, page}`
- Pattern likely follows: bold/uppercase headword, then advice paragraph, then next entry. Inspect 5-10 random pages first.
- Store as JSONL at `data/raw/holovashchuk_entries.jsonl` for reproducibility

### AC 3: FTS5 table
- Add `holovashchuk_usage` table to `data/sources.db` with columns: `headword`, `body`, `page` (sourcery normalize: `headword` is the FTS-indexed primary lookup)
- Use the same FTS5 setup pattern as existing dictionaries (e.g. Антоненко-Давидович). Look at `scripts/ingestion/` or `scripts/rag/` for the closest reference implementation
- Ingest script: `scripts/ingestion/ingest_holovashchuk.py` — modeled on existing dictionary ingest scripts in the repo
- Add `--ingest-holovashchuk` flag to whatever orchestration script registers MCP source tables (look for the parent dispatcher; `scripts/data/build_sources_db.py` or similar)

### AC 4: New MCP tool
- Add `search_usage_holovashchuk(query: str, limit: int = 5) -> list[dict]` to whichever module hosts the existing search-style-guide / search-grinchenko tools (likely `scripts/sources/sources_server.py` or under `scripts/mcp/`)
- Mirror the function signature and return shape of `search_style_guide` for consistency

### AC 5: Tool description with provenance
- Description must include: ISBN `966-00-0350-1`, 448 pages, publisher `Київ : Наукова думка, 2004`, license caveat ("Open PDF, no explicit open license stated; use under non-commercial educational fair-use posture per project policy"), source URL.

### AC 6: Update rules
- Update `claude_extensions/rules/mcp-sources-and-dictionaries.md` — add `mcp__sources__search_usage_holovashchuk` to the dictionary tools section with the same level of detail as Антоненко-Давидович etc.
- Run `npm run claude:deploy` to sync `.claude/`, `.agent/`, `.gemini/`

### AC 7: Smoke tests
- Add `tests/test_holovashchuk_ingest.py` with at least 5 query cases:
  - `щодо`
  - `у зв'язку з`
  - `що стосується`
  - One single-word entry (pick from a random page)
  - One multi-word entry (pick from a random page)
- Each test asserts: query returns ≥1 hit, hit text contains the query lemma, page number is non-zero

---

## Hard requirements

1. **Verify license posture before bulk extraction.** PDF copyright is visible. Project policy is non-commercial fair-use. If kpdi.edu.ua serves a `LICENSE` or `robots.txt` Disallow, STOP and document — don't bulk-extract over a Disallow.
2. **Pin the PDF URL + sha256 in source provenance** in the new ingest script's docstring, so future re-ingests can verify the same source.
3. **No `--no-verify`** on commits.
4. **Reference #1665 in every commit.**

---

## Final steps (numbered, per dispatch-brief checklist memory rule)

5. **Run full test suite for affected files:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/test_holovashchuk_ingest.py tests/ -k 'sources or holovashchuk or mcp' -x -q
   ```

6. **Run ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/ingestion/ingest_holovashchuk.py scripts/sources/ tests/test_holovashchuk_ingest.py
   ```

7. **Commit** with conventional message + #1665 ref:
   ```
   feat(sources): ingest Holovashchuk «Словник-довідник з українського літературного слововживання» (2004) (#1665)

   - PDF → pdftotext → JSONL → FTS5 table holovashchuk_usage in data/sources.db
   - New MCP tool: search_usage_holovashchuk(query, limit=5)
   - 448 pages, ISBN 966-00-0350-1, fair-use license posture per non-commercial policy
   - Smoke tests on щодо / у зв'язку з / що стосується + 2 sampled entries
   - Updated claude_extensions/rules/mcp-sources-and-dictionaries.md

   Closes #1665.

   Co-Authored-By: Codex (gpt-5.5) <noreply@openai.com>
   ```

8. **Push:**
   ```bash
   git push -u origin codex-1665-holovashchuk-ingest
   ```

9. **Open PR** (NOT draft — implementation is well-specified, ready for review):
   ```bash
   gh pr create --title "feat(sources): ingest Holovashchuk usage dictionary (#1665)" --body "$(cat <<'EOF'
   ## Summary
   Implements #1665 ACs in full. Adds Holovashchuk «Словник-довідник з українського літературного слововживання» (2004, 448p, ISBN 966-00-0350-1) as a new MCP-queryable usage dictionary.

   ## ACs (all checked)
   - [x] PDF downloaded + pdftotext extracted, ≥X chars Ukrainian text
   - [x] Y entries segmented to JSONL
   - [x] FTS5 table holovashchuk_usage in data/sources.db
   - [x] MCP tool search_usage_holovashchuk(query, limit=5)
   - [x] Tool description with ISBN/page/license caveat
   - [x] mcp-sources-and-dictionaries.md updated + npm run claude:deploy ran
   - [x] Smoke tests on 5 query cases pass

   ## License posture
   <FILL IN: confirmation of robots.txt + license caveat verification>

   ## Test plan
   - [x] pytest tests/test_holovashchuk_ingest.py passes
   - [x] ruff check clean
   - [ ] CI green
   - [ ] Human review

   🤖 Dispatched by Claude (overnight 2026-05-05) via delegate.py.
   EOF
   )"
   ```

10. **Do NOT enable auto-merge.** This is data ingestion; human verifies license posture + sample queries before merge.

---

## Stop conditions

- If PDF link is dead → STOP, report, do not improvise alternative source.
- If pdftotext output is mostly garbled → try `pdftotext -layout` vs `-raw` vs OCR, document which worked, fail gracefully if none.
- If license posture is incompatible with project's non-commercial CC posture → STOP, document, file follow-up issue. Don't bulk-extract.
- If existing tooling (sources_server.py / build_sources_db.py / etc.) is not where you expected → STOP and grep for `search_grinchenko_1907` / `search_style_guide` to find the canonical pattern; mirror it.

---

## Branch-base verification (per memory rule, mandatory)

Codex MUST run as step 1:
```bash
git -C /Users/krisztiankoos/projects/learn-ukrainian fetch origin main
```

And as step 3 (after worktree):
```bash
git log --oneline HEAD..origin/main  # must be empty
```

If non-empty: `git rebase origin/main && git push --force-with-lease`. This catches stale-base dispatches per memory rule (3 stale-base hits 2026-04-23).

---

## Deliverable

Open PR (not draft) implementing #1665 in full. License-posture confirmation in PR body. All ACs checked. Tests + ruff green. Awaiting human review for license verification.
