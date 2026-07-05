# Word Atlas — Entry-Model v1 DB + full-corpus fill plan

- status: active
- owner: Claude atlas-track driver
- decided_with_user: 2026-07-05
- supersedes framing in: `docs/atlas-data-coverage-strategy.md` (fill tactics still valid)
- entry-model SSOT: `docs/runbooks/word-atlas-entry-model.md` (v1, 2026-07-04)
- design SSOT: `docs/poc/word-atlas/{landing,detail,heritage-defense}.html` + `word-atlas.css`

> **Constraint (user 2026-07-05, MEMORY #M-14):** quality, not cost. NOT $-gated. Real limit =
> per-agent 5h/weekly windows + slovnyk.me live rate-limit. "Scale" = grind the corpus through
> SMARTLY within rate limits, prefer improving cheap models with tool grounding. No LLM review where
> deterministic dictionaries suffice. No 20-headword-at-a-time manual batches.

## 1. Why (the gap — verified 2026-07-05 on real data)

**Structural gap — entry-model v1 is ~0% implemented in the 5,517 live entries:**

| entry-model v1 requires | present in manifest |
|---|---|
| `entry_type` (lemma/expression/phraseologism/proverb/multiword_term/proper_name) | 0 / 5517 |
| `search_aliases` (canonical/unstressed/transliteration/inflected_form/spelling_variant/translation_hint/component_head) | 0 / 5517 |
| `related_entries` (component cross-links + roles) | 0 / 5517 |
| `review_state` (approved/needs_review/rejected), `visibility` (public/private), `display_head` | 0 / 5517 |
| `source_provenance` (source_family/source_locator/extraction_mode) | 364 / 5517 (7%) |

**Enrichment gap — fillers exist (`scripts/lexicon/enrich_manifest.py`) but coverage is partial:**
enrichment 80% · pronunciation 61% · synonyms/sections 41% · wiki 24%. Cause = word absent from the
consulted dictionary, not missing code.

**Scale gap — the storage form does not scale:** 46.6 MB / 5,517 = 8.2 KB/entry → **~2.1 GB as one JSON
at 250k**. A single static manifest cannot be rebuilt incrementally, queried, or shipped to a browser.

## 2. Optimal DB form — SQLite SSOT (`data/atlas.db`)

Build-time source of truth = SQLite, modeled on entry-model v1. The JSON manifest becomes a **generated
export**, not the store. Enables resumable per-entry writes (no 46 MB rewrite per fill), the article-vs-alias
split the design demands, and FTS5 search for free.

### Schema (v1)

```
articles(
  slug TEXT PRIMARY KEY,           -- stable route segment
  display_head TEXT NOT NULL,      -- public headword/phrase
  lemma TEXT NOT NULL,             -- canonical (may == display_head)
  entry_type TEXT NOT NULL,        -- lemma|expression|phraseologism|proverb|multiword_term|proper_name
  pos TEXT,
  gloss TEXT,
  review_state TEXT NOT NULL,      -- approved|needs_review|rejected
  visibility TEXT NOT NULL,        -- public|private
  cefr TEXT,                       -- level or NULL (never fabricated; PULS/estimate-labeled)
  heritage_classification TEXT,    -- standard|archaic|dialect|russianism|calque|...
  created_at TEXT, updated_at TEXT
)
article_provenance(slug, source_family, source_locator, extraction_mode)   -- N per article
aliases(alias, kind, source, target_slug)                                  -- kind ∈ 7 allowed; excluded from entry totals
related_entries(slug, related_slug, entry_type, relation, component_role)  -- cross-links
enrichment(slug, section, payload_json, source, filled_at, phase)          -- section ∈ meaning/definition_cards/
  -- etymology/morphology/stress/pronunciation/translation/synonyms/antonyms/idioms/literary_attestation/
  -- wiki_reference/cefr/heritage_status/calque_note ; phase ∈ local|slovnyk|uncovered
articles_fts USING fts5(display_head, lemma, gloss, aliases)               -- search
```

Rendered-section → source map (from the 3 design pages + enrich_manifest fillers):

| Section (UA label) | source(s) | phase |
|---|---|---|
| Значення / def-cards (СУМ-11, СУМ-20, Грінченко, ВТС) | local СУМ-11 + slovnyk.me СУМ-20 live | local+slovnyk |
| Походження + статус | ЕСУМ + Kaikki/Wiktionary | local |
| word-stress / pronunciation (IPA) | ukrainian-word-stress + Kaikki | local |
| paradigm-table (morphology) | VESUM | local |
| Синоніми та антоніми | slovnyk.me + WordNet + Балла | slovnyk |
| Фразеологізми та сталі вирази | Фразеологічний + slovnyk.me | local+slovnyk |
| Літературні засвідчення | literary corpus FTS | local |
| translation (EN) | Kaikki + Балла | local |
| Стилістичні нотатки / editorial-calque (§6 moat) | heritage merge + Антоненко | local |
| status-badge cefr | PULS CEFR (5.9k ceiling; else labeled estimate) | local |
| status-badge heritage-ok/archaic/dialect | heritage classify | local |
| used-in-card / resources (textbook/blog/youtube) | course_usage + curated resources | local |
| wiki-card (Wikipedia) | query_wikipedia | slovnyk-paced (network) |
| provenance-footer / src-pill | article_provenance per data point | local |

## 3. Two-phase fill

- **Phase 1 — local, unthrottled, whole corpus at once:** VESUM (POS/morphology/validity + inflected
  aliases), Kaikki (IPA/etymology/translation), stress dict, ЕСУМ, local СУМ-11, Фразеологічний, literary
  FTS, russian_shadow+heritage classification, PULS CEFR. Fills most sections for all entries fast.
- **Phase 2 — slovnyk.me live + Wikipedia, paced (~8 req/s + Retry-After backoff, already built), as a
  resumable work-queue:** СУМ-20 meaning fallback, synonyms, idioms, wiki summaries — only for entries
  Phase 1 left empty. Cache to `data/lexicon/slovnyk_cache` / `wiki_reference.json`.
- **Genuine gaps** (CEFR beyond PULS 5.9k; some borrowings' etymology) → section `phase=uncovered`,
  **never fabricated.** Lesson (coverage doc): reverse-Балла + ЕСУМ suffix-strip shipped garbage → closed.
  Verify every fill's OUTPUT on real data before trusting it.

## 4. Deterministic classification (no LLM review)

Validity/russianism is a rule, not a judgment:
- valid Ukrainian + POS ← VESUM.
- russianism/calque ← `russian_shadow` + heritage merge (Грінченко + ЕСУМ + slovnyk.me + Антоненко).
- **Encoded reject rule:** russian_shadow ≥ threshold AND no Грінченко/ЕСУМ heritage attestation → reject
  (the щитовидка / місцезнаходження precedent, encoded not re-litigated).
- entry_type ← rules: single VESUM head → `lemma`; multiword → `multiword_term` default, promote to
  `expression`/`phraseologism`/`proverb` only on idiom/formula/proverb evidence (Фразеологічний / proverb list).
Only VESUM-absent + no-heritage words land in `needs_review` for a human glance — everything else is automatic.

## 5. Practice coverage — the data supports many drill types; only 4 modes are live

Per the LOCKED spec `docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` (user 2026-06-24; re-homed to
`/words-of-the-day/practice/` #3811). The atlas enrichment already carries the data for far more drills than
the 4 live modes (Flashcards, Matching, Choice-MC, Cloze). **Add proper coverage** by turning the rich fields
into drill types, all from prebuilt decks:

| Atlas data field | Drill type to add |
|---|---|
| `enrichment.morphology.paradigm.cases` | declension / conjugation (case + number production) |
| `enrichment.stress` | stress-placement drill (choose the stressed syllable) |
| `sections.synonyms` / `antonyms` | synonym / antonym match |
| `enrichment.pronunciation.ipa` + audio (future) | listening / dictation |
| `heritage_status` / `§6 calque` | "pick the non-russianism" decolonization drill |
| `enrichment.idioms` | idiom-meaning match |
| `enrichment.cefr` | level-segmented session mixing (already the deck axis) |

Deck build stays **static, CEFR-segmented, sharded** (`practice-index/lexemes/cloze.{lvl}.json`); FSRS card unit
= `lemmaId + mode`. Cloze answer model is case-demanding + scaffolded (§4 of the spec). Feed decks from
`data/atlas.db` (this DB) once populated. `is_practice_eligible` gate = gloss + CEFR/course anchor, no derived
forms, no surzhyk.

## 5b. Backend — a PLANNED scale-up goal for the Practice Hub (user 2026-07-05)

**Phase 1 (now): static.** Astro SSG from the DB + prebuilt FTS index + prebuilt CEFR-sharded decks +
client-side FSRS-6 (`ts-fsrs`) + `localStorage`. Ships value with no server and unblocks corpus fill + the
first new drill types.

**Phase 2 (as we scale — a REAL goal, not deferred-indefinitely): add a Practice Hub backend.** Tracked in
**#4384**. Hard problems it must solve:
- **Accounts + cross-device sync** of FSRS scheduling state (localStorage is per-device; learners want their
  streak/progress everywhere). Auth, user data model, conflict-free sync of card deltas keyed by `lemmaId+mode`
  + `deckVersion`.
- **Server-side scheduling / analytics** — aggregate difficulty, item-level performance, deck health, adaptive
  selection beyond what a static deck can do.
- **Search / data API** if the client index outgrows a shippable size at 250k (per-form aliases → millions).
- **Live/on-demand enrichment** — slovnyk.me/wiki fetch behind a cache API instead of prebuild-only.
Design must keep the static path working (offline-first / progressive enhancement), not fork the app.
This is genuinely hard (auth, sync semantics, data model, hosting for a non-commercial project) — a fable task.

## 6. Roadmap (sequenced — schema BEFORE mass-fill, else we migrate 250k twice)

1. **[this PR] Schema + migration.** Create `data/atlas.db` schema (§2); migrate the 5,517 manifest entries
   (assign entry_type by rule, backfill provenance, generate VESUM inflected aliases). Deterministic gates:
   `entry_type_enum`, `entry_type_shape`, `article_vs_alias_count`, `alias_target_integrity`.
2. **Phase-1 local fill** over the migrated corpus (all local dictionaries) — resumable, whole corpus.
3. **Teacher-source intake into the DB** (rows 239-610 + bulk 13,974) via deterministic classify → article
   rows, replacing the 20-at-a-time YAML-ledger cadence. Multiword idioms become phraseologism/expression rows.
4. **Phase-2 slovnyk/wiki paced fill** — background work-queue within rate limits.
5. **Manifest/site generation from the DB** (Astro SSG) + entry-model gates in CI.
6. **Other resources** (curriculum #4222, textbooks #3934, Ohoiko #4223) via the same DB intake path.
7. **Practice coverage — GH #4383. START WITH DESIGN (user 2026-07-05):** first EXPAND
   `docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` + the design page `docs/poc/word-atlas/practice-hub.html` to
   define the new drill types (declension/conjugation, stress, synonym/antonym, idiom, decolonization), the
   backend sync model, and scaling — THEN implement decks from `data/atlas.db` (§5). Spec is the interaction SSOT.
8. **Practice Hub backend — GH #4384 (§5b):** static-first (client FSRS + localStorage), then add accounts +
   cross-device FSRS sync + analytics as a real scale-up goal, offline-first / progressive enhancement.

> **Honest scope note (correcting an earlier overclaim):** the DB foundation (#4380) is the START, not "the
> hard part done." Hard problems still open: enrichment QUALITY at scale (garbage-fill risk — Kaikki
> translation+etymology wiring, honest `uncovered` labeling), entry_type edge cases (proper names / idiom-vs-term /
> homographs / aspect pairs), inflected-alias generation from VESUM at 250k, search + SSG at 250k, the practice
> pedagogy (FSRS across modes, anti-gaming, cloze answer model), and the backend (auth + sync semantics). These
> are why fable drives from here — for the hard problems, not a mechanical grind.

## 7. Open validation items
- Confirm SQLite-wasm client FTS size is acceptable at 250k before committing to no-backend search.
- Verify each Phase-1 filler's output on a real sample before trusting the fill (garbage-fill lesson).
- Reconcile with the existing source-inventory-review-decisions ledger lane (keep as the human-review audit
  trail for `needs_review` items; the DB is the runtime store).
