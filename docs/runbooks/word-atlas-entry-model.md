# Word Atlas Entry Model

- workflow: `word_atlas_entry_model.v1`
- decided_at: `2026-07-04`
- raw_text_included: false
- candidate_lemmas_included: false
- private_paths_included: false
- discussion_inputs: Codex main synthesis, AGY/Gemini 3.1 Pro High critique
- unavailable_discussion_inputs: Claude CLI could not run locally because the native binary was not installed

## Decision

Word Atlas remains lemma-first, but it is not lemma-only. A public Atlas entry
is an approved, source-backed, searchable article record with a stable slug,
an `entry_type`, public-safe provenance, and deterministic cross-links. Raw
surface forms, private-source rows, generated form aliases, and rejected
candidates are not Atlas entries.

The model has two layers:

- **Article entries**: reviewed records that can have `/lexicon/{slug}` pages
  and are counted in public Atlas entry totals.
- **Evidence and alias records**: surface evidence, inflected forms, spelling
  variants, transliterations, and rejected/noise decisions. These can support
  search or planning, but they do not count as entries.

## Entry Types

| `entry_type` | Counts as Atlas entry | Definition |
| --- | --- | --- |
| `lemma` | yes | Canonical dictionary head for a single lexical item. It should normally be backed by VESUM, a heritage-source fallback, or a narrow modern-term allowlist. |
| `expression` | yes | Fixed functional formula or pragmatic set phrase that learners search as a unit, such as greetings, politeness formulas, discourse markers, and other socially fixed phrases. It is not a generic collocation bin. |
| `phraseologism` | yes | Idiomatic fixed expression whose meaning, register, or usage cannot be predicted from component lemmas. |
| `proverb` | yes | Complete traditional sentential expression that carries a conventional lesson, cultural norm, or evaluative point. |
| `multiword_term` | yes | Compositional but domain-important term naming one concept, grammatical unit, institutional term, or course-relevant lexical unit. |
| `proper_name` | yes | Named entity admitted because it is course-relevant, lexically useful, or needed for Atlas cross-links. |

`noise / rejected` is a candidate-review bucket, not a public `entry_type`.
Existing `form_of` records and future generated form aliases should be handled
as alias/form records and excluded from reviewed entry totals.

## Admission Rules

Create a standalone page only when an item has public-safe reviewed provenance
and at least one of these admission reasons:

- It is an explicit curriculum or reviewed source-inventory target.
- It has meaning, register, government, translation, or usage that is not
  predictable from component lemmas.
- It is a fixed functional formula that learners are likely to look up as a
  unit and is backed by curriculum inclusion or public-corpus frequency.
- It is a phraseologism or proverb that needs its own definition, origin,
  usage note, or cultural framing.
- It is a domain term or grammatical/pedagogical unit that names one concept.
- It is a proper name with course relevance and public source backing.

Keep a phrase only inside lemma pages when it is a productive collocation,
ordinary example sentence, context-specific quote, or source-only surface form
without approved article-level provenance.

For private or copyrighted sources, the standalone head must be reduced to the
canonical minimum form. Do not publish surrounding context, full extracted
sentences, private file paths, private source titles, or raw candidate lists.

## Tie-Breakers

- `expression` vs `phraseologism`: choose `expression` for literal but socially
  fixed formulas; choose `phraseologism` when the meaning is figurative,
  opaque, or idiomatic.
- `expression` vs `multiword_term`: choose `expression` for conversational or
  pragmatic formulas; choose `multiword_term` when the phrase names a domain
  concept or behaves like a terminological unit.
- `phraseologism` vs `proverb`: choose `proverb` only for complete sentential
  traditional sayings. Short idiomatic noun/verb phrases stay
  `phraseologism`.
- `lemma` vs `proper_name`: choose `proper_name` for named entities even when
  VESUM lists the form.
- Unknown multiword candidates must not default into `expression`. If no
  idiom/proverb/formula evidence exists, default reviewed multiword articles
  to `multiword_term`; otherwise keep the item as lemma-page evidence until
  reviewed.

## Search Aliases And Forms

Every article entry needs:

- `url_slug`: one stable route segment.
- `display_head`: the public headword or phrase shown to users.
- `entry_type`: one of the article types above.
- `search_aliases`: public-safe alias records with `alias`, `kind`, `source`,
  and `target_slug`.

Allowed alias kinds:

- `canonical`: the display head normalized for search.
- `unstressed`: stress marks removed.
- `transliteration`: Latin user query support.
- `inflected_form`: generated or reviewed inflected form.
- `spelling_variant`: approved orthographic variant.
- `translation_hint`: short public translation used for search ranking.
- `component_head`: component lemma backlink for multiword entries.

Alias rules:

- Alias `target_slug` must resolve to an approved public Atlas article.
- Public aliases must be deduplicated before search-index generation.
- Private/copyrighted source surfaces may not be emitted as aliases unless
  independently approved as canonical minimum forms.
- Lemma inflections may be generated from VESUM or committed reviewed alias
  maps. Multiword aliases require curated entries or reviewed templates;
  do not blindly combine component paradigms.

## Cross-Linking

Lemma pages should include related fixed expressions, phraseologisms, proverbs,
multiword terms, and proper names through `related_entries` records:

```yaml
related_entries:
  - slug: byty-baidyky
    entry_type: phraseologism
    relation: contains_component
    component_role: verb
```

Expression-like pages should link back to component lemmas with explicit
component roles where useful. A standalone multiword entry may temporarily link
to a component that is queued but not yet published only when the unresolved
component is marked in aggregate-only internal planning output; public pages
must not render broken links.

## Provenance Requirements

Every public article entry must carry public-safe provenance:

- `source_family`: curriculum, public dictionary, Ohoiko/ULP, textbook,
  teacher_lesson, corpus, or reviewer decision.
- `source_locator`: safe public locator or neutral internal label. Do not
  expose private paths, private titles, raw snippets, or copyrighted text.
- `extraction_mode`: curated headword, curriculum headword, reviewed inventory,
  public dictionary head, generated alias, or explicit rejection.
- `review_state`: `approved`, `needs_review`, or `rejected`.
- `visibility`: `public` for publishable article/alias data; private-source
  evidence stays non-public by default.

Additional type-specific requirements:

- `lemma`: VESUM, heritage fallback, deliberate warning entry, proper-name
  exemption, or modern-term allowlist path must be explainable.
- `expression`: evidence that the whole phrase is a fixed functional formula.
- `phraseologism`: idiom or phraseological source, or explicit reviewer
  decision with definition.
- `proverb`: source or reviewer decision identifying it as a proverb/saying.
- `multiword_term`: course, grammar, domain, or dictionary evidence that it is
  one concept.
- `proper_name`: public source or curriculum evidence, plus a reason it belongs
  in Atlas rather than only in a lesson.

## Counting Rules

Public Atlas counts must use these aggregates:

- `reviewed_entries_by_type`: approved article entries only, grouped by
  `entry_type`.
- `total_reviewed_entries`: sum of approved article entries.
- `alias_records`: form aliases, `form_of` records, spelling variants, and
  generated search rows. These are excluded from entry totals.
- `candidate_evidence_by_bucket`: aggregate-only planning counts from source
  surfaces or reviewed inventories.
- `noise_rejected`: aggregate count of candidates explicitly rejected or
  filtered as noise.

Do not call raw surface counts "entries", "lemmas", or "vocabulary size".
Surface counts from lessons, activities, textbooks, or private notes are
evidence for prioritization until lemmatized and reviewed.

## POC And Schema Changes Required

The current implementation is still per-lemma in several places. The next
implementation phase must update these surfaces together:

- Manifest schema: require `entry_type`, `review_state`, `visibility`,
  `display_head`, and public-safe `source_provenance` on article records.
- Route semantics: treat `/lexicon/{slug}` as an entry slug, not as a lemma
  parameter, even if the current Astro file is named `[lemma].astro`.
- Article component: branch section labels and morphology expectations by
  `entry_type`; proverbs and phraseologisms should not be forced through lemma
  morphology.
- Search index: index article entries and alias records separately, with
  aliases resolving to approved article slugs.
- POC route map: include at least one expression-like detail design, not only
  lemma pages.
- Static API status: publish entry counts by `entry_type`, plus separate alias
  and candidate-evidence counts.

## Acceptance Gates

Implementation must not proceed without deterministic gates for:

- `entry_type_enum`: every article record has a valid `entry_type`.
- `entry_type_shape`: `lemma` is single-head unless explicitly allowed;
  expression-like types are multiword or otherwise explicitly justified.
- `article_vs_alias_count`: `form_of` and alias records do not increment
  reviewed entry totals.
- `alias_target_integrity`: every alias `target_slug` resolves to an approved
  public article entry.
- `alias_deduplication`: duplicate aliases collapse before public search-index
  generation.
- `component_cross_links`: expression-like entries link to existing component
  lemmas or omit broken public links.
- `provenance_by_type`: every article type meets its source requirement.
- `privacy_boundary`: public docs, APIs, search rows, and reports contain no
  private paths, private raw text, private source titles, candidate lemma lists,
  or copyrighted textbook snippets.
- `static_api_counts_by_type`: public status JSON reports reviewed counts by
  type and keeps alias/candidate counts separate.
- `poc_route_map_alignment`: the POC route map names the entry templates that
  implementation claims to support.
- `scripts_documented`: any new or materially changed Atlas operational script
  is documented in `docs/SCRIPTS.md`.

## Sense-Level Fields (v1 delta — #6437)

- decided_at: `2026-08-07`
- discussion_inputs: Gemini (AGY) consultation, verdict AGREE-WITH-CHANGES
  (`batch_state/atlas-drive/gemini-consult-entry-lint.out`, not committed)

`entry_type` (above) classifies the article as a whole. Within a `lemma` or
other article entry, a `senses` array separates the lexicographical
definition, the learner-facing hint, and the drill target for each distinct
meaning. This closes two related problems: EN/UK glosses truncated mid-word
by hard length caps, and bare single-word EN drill targets that hide the
polysemy of the source word (e.g. `брак` surfacing only ordinal "second"
instead of defect/scarcity/manufacturing "seconds").

A `senses` entry has this shape:

```yaml
senses:
  - id: "brak_defect"            # stable; drills key off this, not array order
    pos: "noun"
    grammar_notes: "…"           # optional UA pedagogy note
    uk_source_def: "…"           # immutable raw SUM/BTC text — lint reads it,
                                  # nothing in the lint or enrich pipeline may
                                  # rewrite it
    learner_uk: "недолік, вада"
    learner_en: ["defect", "flaw", "scarcity"]
    en_disambiguation: "imperfection/flaw (not marriage/ordinal second)"
    source: "sum20_vetted|btc|dmklinger|manual_native|rag_verified|ai_minimum"
    completeness: "complete|truncated|draft"
```

Field notes:

- `id`: stable per-sense slug. Practice/drill wiring keys off `senses[id]`,
  never off array position or `learner_en[0]` / `enrichment.translation.en[0]`,
  so re-ordering or adding a sense cannot silently drift what a learner drills
  (LINT-003).
- `uk_source_def`: the raw lexicographical definition (СУМ-20/BTC/etc). This
  is ingestion data — the lint gate reads it read-only and does not mutate it.
- `learner_uk` / `learner_en`: the pedagogy-facing gloss and drill target(s).
  `learner_en` is a list because a sense can have more than one accepted EN
  target; a single-item list on a high-risk polysemous word is exactly what
  LINT-002 flags.
- `en_disambiguation`: required whenever `learner_en` is a bare single word
  that reads as a different, unrelated sense in general English (see
  LINT-002 denylist in `scripts/audit/lint_word_atlas.py`).
- `source`: dictionary-backed values (`sum20_vetted`, `btc`, `dmklinger`,
  `manual_native`, `rag_verified`) for sourced senses. Use `ai_minimum` when
  the learner gloss is an AI-minimum placeholder rather than a vetted
  dictionary sense — honesty over silent thinness (#6437 enrich honesty tags).
  `apply_sense_honesty_tags` must not overwrite a dictionary-backed `source`
  already in that sourced set.
- `completeness`: `truncated` is the honest tag for text a hard cap cut off
  mid-word; a `learner_uk`/`learner_en`/`en_disambiguation` value ending in
  `...`/`…` without this tag is what LINT-001 flags. `draft` marks thin /
  incomplete learner text (including AI-minimum glosses). Helpers
  `truncate_with_honesty` + `apply_sense_honesty_tags` in
  `scripts/lexicon/enrich_manifest.py` are wired into the enrich emit path via
  `apply_manifest_sense_honesty`, called at the end of `enrich_entry` (#6437
  PR3): it hard-caps an oversized `en_disambiguation`/`grammar_notes`
  annotation (never `uk_source_def` — immutable ingestion text — and never
  the `learner_uk`/`learner_en` drill content itself) and labels a sense with
  no recorded dictionary `source` as `ai_minimum`.

### Lint gate (PR1 + PR2 + PR3 + PR4 + PR5 scope)

`scripts/audit/lint_word_atlas.py` implements six read-only, advisory rules:

| ID | Name | Checks |
| --- | --- | --- |
| LINT-001 | `TRUNCATED_TEXT_CUTOFF` | A learner-facing sense field ends `...`/`…` while `completeness != "truncated"`. |
| LINT-002 | `AMBIGUOUS_BARE_EN` | `learner_en` is a single-item list, the word is in a high-risk polysemy denylist, and `en_disambiguation` is empty. |
| LINT-003 | `DRILL_SENSE_ID_MISSING` | A practice binding / deck item references a lemma without a non-empty `senseId` / `sense_id` (no `en[0]` fallback). |
| LINT-004 | `UNVETTED_EN_SOURCE` | Published non-empty `learner_en` while `source` is missing, blank, or outside `SENSE_SOURCE_SOURCED ∪ {ai_minimum}` (`sum20_vetted`, `btc`, `dmklinger`, `manual_native`, `rag_verified`, `ai_minimum`). Honest `ai_minimum` does not fire. |
| LINT-101 | `MULTI_SENSE_UK_SINGLE_EN` | Entry has ≥2 senses but only one publishes `learner_en`, or a single shared EN list (entry-level `learner_en`, or identical sense `learner_en` lists) without per-sense `en_disambiguation`. Bypassed when `is_fixed_expression` is true. |
| LINT-102 | `POS_TRANSFORM_MISMATCH` | Sense `pos` disagrees with entry/lexeme POS after coarse family normalization, with a clear mismatch signal. Documented multi-POS (`multi_pos`, slash/semicolon/`pos` lists, multi-value `allowed_sense_pos`) is not flagged. Does not infer EN-gloss POS. |

No CI gate is wired to `lint_word_atlas.py` yet — it runs as a standalone
advisory check until a residual-count policy is agreed (issue #6437 D6-7).
Gemini consult also sketched EN-gloss POS conflict detection for LINT-102
(e.g. noun *брак* → bare ordinal *"second"*); that reading is deferred here
because it needs a vetted EN POS lexicon and would raise false positives on
legitimate dual-POS words.

## Open Decisions

- Whether `form_of` records stay in the manifest as non-entry records or move
  fully into a separate alias/search artifact.
- Exact public-corpus frequency threshold for standalone `expression`
  admission when no curriculum target exists.
- Whether component lemmas are required before publishing an expression-like
  article, or whether a queued component can temporarily suppress the public
  link.
- Whether the route source file should be renamed from `[lemma].astro` to
  `[slug].astro` when the schema migration lands.
