# Word Atlas etymology — Goroh ingest (roadmap B, phase 1) [#2882]

## Goal
Replace the OCR-garbled ЕСУМ etymology source for the Word Atlas with clean **Goroh**
(goroh.pp.ua) etymology, for the 63 A1 lemmas currently in the Atlas. Etymology coverage is
**19/63** today; lift it. Keep the build **deterministic**: NO live HTTP in the build/enrich
path — a separate one-time ingest script caches into `data/sources.db`, and
`enrich_manifest.py` reads `sources.db` only.

## Verified background (don't re-derive — but DO verify with tools before relying)
- Pipeline: `scripts/lexicon/enrich_manifest.py` → `starlight/src/data/lexicon-manifest.json`.
  The page `starlight/src/pages/lexicon/[lemma].astro` renders `enrichment.etymology` ({text, source}).
- Current etymology = ЕСУМ in `data/sources.db` (А–Г PoC → 19/63). The hook is `_etymology()` at
  `scripts/lexicon/enrich_manifest.py:455` (verify the exact line).
- Lemma list = the 63 entries in `starlight/src/data/lexicon-manifest.json` (`entry.lemma` / `entry.url_slug`).
- **Reuse**: `scripts/ingest/slovnyk_me_ingest.py` is THE precedent for "fetch explicit words,
  sleep politely, store snapshots into sources.db." `scripts/ingest/esum_load.py` = closest
  table-loader. Read both before writing.
- **Goroh canonicalizes**: e.g. `колежанка` resolves to an article headed `колега` (with колежанка a
  derivational variant). Store BOTH requested lemma AND canonical headword.
- **Goroh licensing**: NOT open-licensed (public-electronic-library / takedown model). Scope strictly
  to the 63 Atlas lemmas, store `source_url` + attribution, conservative extract length, NO bulk mirror.

## Tasks (numbered — follow in order)
1. You are already in a `--worktree` on a branch off `origin/main`. Confirm with `git status`.
2. Create `scripts/ingest/goroh_etymology_ingest.py` modeled on `scripts/ingest/slovnyk_me_ingest.py`:
   - Read the 63 lemmas from `starlight/src/data/lexicon-manifest.json`.
   - For each, fetch `https://goroh.pp.ua/Етимологія/{lemma}` (URL-encode the Cyrillic), **sequential**,
     polite delay 1.5–2s, standard User-Agent. Use the HTML-parsing dep slovnyk_me_ingest already uses.
   - Parse the etymology prose + canonical headword. Clean to plain text.
   - Upsert into a NEW `goroh_etymology` table in `data/sources.db`:
     `requested_lemma, headword, etymology_text, source_url, retrieved_at, content_hash` (+ exact-lemma index).
   - Idempotent: skip already-cached lemmas unless `--refresh`. Bounded to the 63 lemmas.
   - If goroh.pp.ua is unreachable / rate-limits hard (429): STOP, don't hammer; partial coverage is fine — report what you got.
3. Wire `_etymology()` (`enrich_manifest.py`) to query `goroh_etymology` FIRST (by requested_lemma,
   then by canonical headword), **falling back to the existing ЕСУМ source** if Goroh has nothing
   (keep ЕСУМ as fallback — do NOT delete it). Return the page's `{text, source}` shape with source
   label like `Горох (за ЕСУМ)` and the `source_url`.
4. Run the ingest locally to populate `goroh_etymology` (you have network + `data/sources.db`).
   Then regenerate the manifest (check `enrich_manifest.py` `__main__` for the regen command).
   Report **before/after** count of lemmas with `enrichment.etymology`.
5. Add a focused test (e.g. `tests/test_goroh_etymology_ingest.py`): fixture ONE canonicalized lemma
   (requested ≠ headword), assert `_etymology()` resolves it. **No network in the test.**
6. `ruff check` new/changed `.py` (must pass).
7. `pytest` the new test + `tests/test_lexicon_enrich_manifest.py` (must pass).
8. Commit conventional (`feat(lexicon): Goroh etymology ingest + wire _etymology [#2882]`),
   `git push -u origin <branch>`, `gh pr create`. **Do NOT auto-merge.**

## #M-4 — your final report MUST quote RAW tool output for each claim (command + cwd + output):
- "coverage lifted": python one-liner counting manifest entries with `enrichment.etymology`, before & after — raw.
- "ingest worked": `sqlite3 data/sources.db "select count(*) from goroh_etymology"` — raw.
- "clean text": print the `etymology_text` for `дім`, `вікно`, `звук` — raw (prove it's NOT OCR garbage).
- "tests pass": pytest summary line — raw.
- "ruff clean": ruff final line — raw.
- "PR opened": `gh pr view --json url` — raw.

## Constraints
- `enrich_manifest.py` must do NO live HTTP — only the ingest script fetches; ingest is a separate manual step.
- Scope: Goroh + the 63 Atlas lemmas ONLY. Wiktionary fallback is a SEPARATE follow-up (not this task).
- Don't touch `[lemma].astro` (the render already handles `enrichment.etymology`).
