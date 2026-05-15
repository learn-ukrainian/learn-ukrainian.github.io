# DECISION — Retire runtime transliteration; textbook matcher queries Cyrillic `author_uk` directly

**Status:** ACCEPTED 2026-05-15.
**Decided:** Approve as recommended — the runtime depends on Cyrillic, not Latin.
**Source:** Dispatch brief `docs/dispatch-briefs/2026-05-15-cyrillic-native-matcher.md`. Surfaced by the A1/A2 (#2007) and B1/B2 (#2011) `plan_references` audits, which exposed how a hand-maintained Cyrillic→Latin transliteration dict (`_TEXTBOOK_AUTHOR_TRANSLITS`) drifted from corpus reality every time a new author appeared.
**Scope:** runtime resolution of `Author Grade N, p.M` textbook citations in `scripts/build/linear_pipeline.py` and `scripts/audit/plan_references_audit.py`. **Does NOT touch:** Latin `textbooks.author` column values (kept for backwards compatibility), `source_file` slug strings on disk (separate decolonization PR), PDF filenames, or wiki/literary/dictionary ingestion paths.

---

## Context — the Soviet-era seam

`textbooks.source_file` values were built by scraping pipelines that used Russian-mediated transliteration schemes (`Заболотний → zabolotnyi`/`zabolotnij`, `Голуб → golub` not the native `holub`, `Захарійчук → zakhariychuk`/`zaharijchuk`/`zahariichuk`). The chunks are real Ukrainian textbook content; the file naming is a Latin scar from the scraping path.

Plan files cite authors in Cyrillic, the way Ukrainian speakers read and write them. To bridge plan-Cyrillic to corpus-Latin, the runtime carried a hand-maintained dict, `_TEXTBOOK_AUTHOR_TRANSLITS`, mapping each Cyrillic name to one or more Latin slug fragments and matching via `source_file LIKE %-{translit}-%`. Every newly-cited author needed a manual entry; #2013 added 6 in a single PR after audit #2007 surfaced 19 broken citations.

The transliteration dependency is a Soviet-era artifact: the runtime should never have to know any romanization scheme, let alone a Russian-mediated one. Ukrainian names match against Ukrainian names.

## Decision

1. Add a Cyrillic column `textbooks.author_uk` and back-fill it from the legacy Latin `author` column via a one-time migration (`scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py`). The migration owns the only remaining Latin→Cyrillic mapping in the codebase.
2. Rewrite `_source_files_for_textbook_reference` and `plan_references_audit._source_files_for` to query `WHERE author_uk = ? AND grade = ?` — direct equality, no LIKE patterns, no transliteration.
3. Add a small `_canonicalize_author_uk()` helper that maps Cyrillic spelling variants to their canonical form (`Литвінова → Літвінова`, `Пономарьова → Пономарова`). This is **not** transliteration: both ends are Cyrillic. It captures Ukrainian-internal spelling history, the kind of variation that exists between regional/historical orthographies of a single name.
4. Update ingestion paths (`scripts/wiki/build_sources_db.py`, `scripts/ingest/*`) to require an explicit Cyrillic `author_uk` per row. Fail loudly when an entry has `author` but no `author_uk`.

The Latin `author` column stays in the schema — archived analytics and existing source_file naming depend on it — but the runtime matcher does not read it.

## Why now

Three forcing functions converged: (a) audits #2007 and #2011 quantified the maintenance tax (19 + 12 broken citations from missing TRANSLITS entries); (b) #2013 added six entries by hand and the dict was still incomplete; (c) every new textbook ingestion would have required another round-trip through TRANSLITS. The bridge had to retire before the next ingestion wave.

## Scope boundary (deliberately conservative)

- `textbooks.author` (Latin) **stays** — deprecated via docstring, not deleted, so archived analytics, the orphan back-fill helper (`scripts/wiki/backfill_school_textbook_orphans.py`), and historical SQL queries against the column continue to work.
- `textbooks.source_file` values **stay Latin** — these are opaque corpus keys downstream. Renaming them touches ~91 file slugs on disk plus their references in chunk JSONLs, plan citations cached as `resolved_source_file`, and the broker. Filed as a follow-up decolonization PR.
- PDF filenames on disk **stay** — separate from the DB rename.
- Wiki/literary/dictionary tables **not touched** — `literary_texts.author` is already Cyrillic where applicable.

## Verification (#M-4 deterministic claims)

| Claim | Tool |
|---|---|
| Migration adds the column | `sqlite3 data/sources.db ".schema textbooks"` shows `author_uk TEXT DEFAULT ''` |
| Back-fill rate | `SELECT COUNT(*) FROM textbooks WHERE author_uk != ''` reports 25,714 / 25,714 = 100% |
| Idempotent re-run | Second `apply()` reports `rows_updated=0` |
| Matcher resolves Cyrillic citations | `tests/test_textbook_grounding.py` — 11 tests pass |
| Spelling variants canonicalize | `test_litvinova_cyrillic_variant_resolves_same_as_primary`, `test_ponomarova_cyrillic_variant_resolves_same_as_primary` |
| Audit logic preserved | `tests/test_plan_references_audit.py` — 13 tests pass |
| Migration round-trips | `tests/test_migrations.py` — 4 tests pass |

## Expiry

Revisit when source_file strings are renamed to Cyrillic (the follow-up PR). At that point the migration script's `_LATIN_TO_UK` dict can be deleted: there will be no Latin-named author state anywhere in the codebase or DB.

## Non-negotiable

`_LATIN_TO_UK` in the migration script is **the only place transliteration is acknowledged**. It must not be re-imported into runtime code. If a future ingestion path needs a Latin→Cyrillic translation, the work belongs in the migration's bridge dict at ingestion time, not in the matcher at query time.
