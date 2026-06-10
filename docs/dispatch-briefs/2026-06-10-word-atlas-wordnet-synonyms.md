# Dispatch brief — Word Atlas data: WordNet synonyms + gloss/entity cleanup (#2882)

Deterministic local-DB enrichment of the Word Atlas (Лексикон). ONE generator file + regenerate its
output. **NO visual redesign** (gated behind the A1 POC pilot). **NO etymology** (locked to Горох/Wiktionary,
handled separately). **NO LLM curation** (ranking of attestations is a later step). Data-only, deterministic.

## Files
- Edit: `scripts/lexicon/enrich_manifest.py`
- Regenerate: `starlight/src/data/lexicon-manifest.json` (find the exact regen command in the script
  header / Makefile / docs — do NOT hand-edit the JSON).

## #M-4 verification — final report = `command + cwd + raw output` for EACH claim
- **"synonyms lifted"** → count of lexicon entries with non-empty synonyms, BEFORE and AFTER. A python
  one-liner counting entries whose synonyms field is non-empty in `lexicon-manifest.json`. Expect ~5 → ~45-49
  of 63. Quote both raw outputs.
- **"no fabricated synonyms"** → for 3 sample lemmas, run the `ukrajinet` sqlite query and show the rows that
  produced each surfaced synonym. EVERY surfaced synonym MUST appear in an `ukrajinet` synset row that also
  contains the lemma. Quote the sqlite output raw.
- **"chunk leak gone"** → `grep -c chunk starlight/src/data/lexicon-manifest.json` → `0` (was 9). Raw.
- **"entities gone"** → `grep -c '&amp;\|&lt;\|&gt;' starlight/src/data/lexicon-manifest.json` → `0` (was 4). Raw.
- **"build green"** → `npm run build:full --prefix starlight` final line raw.
- **"tests pass"** → pytest for any lexicon test (e.g. `tests/test_lexicon*.py` if present) + `npm test --prefix starlight` final line raw.

## Task 1 — WordNet synonyms (the win: ~5/52 → ~49)
Source: `data/sources.db` table `ukrajinet(id INTEGER, synset_id TEXT, words TEXT, text TEXT, source TEXT)`,
122K synsets, index on `words COLLATE NOCASE`.
1. FIRST inspect a few rows to learn the `words` delimiter/format:
   `sqlite3 data/sources.db "SELECT synset_id, words, text FROM ukrajinet WHERE words LIKE '%дім%' LIMIT 5;"`
2. Algorithm: for each lexicon lemma, find `ukrajinet` rows whose `words` contains the lemma **as a whole
   token** (split `words` on its delimiter, exact match — NOT a substring LIKE, so «рік» never matches
   «рікою»); collect the OTHER members across those synsets; dedupe; drop the lemma itself; cap at a sane N
   (e.g. 8).
3. **GUARDS (hard):** (a) whole-token match only; (b) ONLY emit words that literally appear in an `ukrajinet`
   synset row containing the lemma — NEVER invent or "improve"; (c) zero matches → emit empty synonyms, do
   NOT guess.
4. **Antonyms:** this schema has no relation/antonym table. If no antonym source exists, **SKIP antonyms
   entirely** (do not fabricate). Note this explicitly in the PR body.

## Task 2 — gloss "chunk" leak (9 entries)
The user-facing `gloss` leaks a pedagogical "chunk" annotation, e.g. `"Goodbye — chunk"`,
`"All the best — farewell chunk"`, `"Good day / Hello — formal chunk, stress \`Добрий день\`"`. Trace where
`gloss` is built in `enrich_manifest.py`; the "chunk" tag bleeds in from the course-glossary source. Strip the
chunk annotation from the user-facing gloss while KEEPING the clean EN translation and any legitimate stress
note. Verify `grep -c chunk = 0`.

## Task 3 — HTML entity double-escape (4 entries)
Definitions from Wiktionary/СУМ contain double-escaped entities: `"...частотою від 20&amp;nbsp;Гц до
20&amp;nbsp;кГц..."` (should render `20 Гц`), and `&lt;`. Apply `html.unescape()` (twice if double-escaped) to
definition/gloss text at the generator, OR normalise `&amp;nbsp;`→space, `&lt;`→`<`, `&gt;`→`>`. Verify grep = 0.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree.
2. Inspect `ukrajinet` sample rows (delimiter/format) + the `enrich_manifest.py` gloss + synonym code paths.
3. Implement Task 1 (synonyms), Task 2 (chunk strip), Task 3 (entity unescape).
4. Regenerate `lexicon-manifest.json` via its documented command.
5. Run the full #M-4 verification (before/after synonym counts, 3-lemma source cross-check, both greps, build, tests).
6. `.venv/bin/ruff check scripts/lexicon/enrich_manifest.py`.
7. Commit (conventional + `X-Agent` trailer): `feat(lexicon): WordNet synonyms (ukrajinet) + gloss chunk/entity cleanup [#2882]`.
8. `git push -u origin <branch>`; `gh pr create` — body carries the #M-4 evidence. **DO NOT merge. DO NOT deploy.**
