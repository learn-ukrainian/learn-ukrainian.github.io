# Dispatch — Atlas translation fill: UK→EN reverse-Балла fallback (#2882)

Close the ~535-word core-vocab **translation** gap in the Word Atlas. Strategy:
`docs/atlas-data-coverage-strategy.md` (read the "translation" row).

## Root cause (don't re-derive — verify, then implement)
`_translation(conn, lemma)` in `scripts/lexicon/enrich_manifest.py` queries the
`balla_en_uk` table, which is **English→Ukrainian, one-way** (column `word` = English
headword; the Ukrainian translation(s) are in the entry text). So a UK lemma rarely
matches `word` directly → ~33% of core vocab has no translation. The fix is to **invert
Балла**: build a UK→EN reverse map from the same table and consult it on a miss.

## #M-4 preamble — tool-back every claim
Report each verifiable claim with the literal command + cwd + raw output. Specifically:
- inspect the real `balla_en_uk` schema + a few rows BEFORE coding (`sqlite3 data/sources.db`
  or a `.venv/bin/python` snippet) — paste the raw columns + 3 sample rows.
- "tests pass" → `pytest` final line raw; "ruff clean" → `ruff check` final line raw.

## Implementation (numbered)
1. `git worktree add` is handled by the dispatch (`--worktree`). Confirm you're in it (`git status`).
2. Inspect `balla_en_uk` (columns, how UK translations are stored in a row) against the
   REAL `data/sources.db`. Decide the parse: split the Ukrainian side into individual
   lemma tokens (handle `,`/`;`/synonym separators; strip parentheticals).
3. Add a **module-level cached** UK→EN reverse map builder in `enrich_manifest.py`
   (build once per process from `balla_en_uk`, invert to `{uk_lemma_casefolded: [en, ...]}`).
   Do NOT mutate `sources.db` (no new table) — build it in-memory at enrich time.
4. In `_translation`, when the existing path yields nothing, consult the reverse map
   (casefold + the project's apostrophe-normalization). Return the same dict shape the
   function already returns, with a `source` crediting Балла (EN→UK, reverse-indexed).
5. Tests: add unit tests in `tests/test_lexicon_enrich_manifest.py` — reverse lookup
   hits a known UK word, misses a nonsense word, dedupes/cleans the EN side. Mirror the
   existing test fixtures there (`_conn()` / in-memory sqlite with a `balla_en_uk` table).
6. `.venv/bin/python -m pytest tests/test_lexicon_enrich_manifest.py -q` → green.
7. `.venv/bin/ruff check scripts/lexicon/enrich_manifest.py tests/` → clean.
8. **Code-only — do NOT run `make atlas` and do NOT commit `site/src/data/lexicon-manifest.json`
   or the fingerprint.** The orchestrator regenerates the manifest after merge.
9. Commit (conventional): `feat(lexicon): UK→EN reverse-Балла translation fallback (#2882)`.
   End with the `X-Agent: cursor/atlas-reverse-balla` trailer.
10. `git push -u origin <branch>` + `gh pr create`. Do NOT merge.

## Acceptance
- A core UK noun absent from the forward path but present in Балла's UK side now gets a
  translation. `pytest` green, `ruff` clean. No manifest/fingerprint committed.
- The reverse map is built from the real `balla_en_uk` only (no fabricated translations).
