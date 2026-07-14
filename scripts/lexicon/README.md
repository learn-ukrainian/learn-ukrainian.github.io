# Word Atlas Lexicon Pipeline

## Course-vocabulary rebuild

`make atlas` rebuilds a **course-vocabulary-only** manifest from every
`curriculum/l2-uk-en/*/*/vocabulary.yaml` plus the small warning and heritage
seed sets:

```bash
make atlas
```

It is appropriate when deliberately constructing that source layer. It is not
the release command for an existing full Atlas manifest: its first step,
`scripts.lexicon.build_data_manifest`, replaces the manifest and therefore
does not retain entries promoted by `content_lexicon_grow` or
`source_inventory_grow`.

The target runs `scripts.lexicon.build_data_manifest`,
`scripts/lexicon/enrich_manifest.py`, and `scripts/lexicon/verify_manifest.py`.
It writes the derived local Atlas data files:

- `site/src/data/lexicon-manifest.json`
- `site/src/data/lexicon-manifest.fingerprint.json`

`make atlas-publish` depends on this target, so do not use it for a
relation-only or other in-place re-enrichment of a published full manifest.

## Re-enrich and publish the full manifest

For relation changes or any update that must retain the promoted Atlas layer,
run this sequence from a data-enabled primary checkout. The first command
hydrates the content-addressed release pointer when the local manifest is
missing or poorer. It refuses to overwrite a richer or newer local intake
manifest, so do not set `ATLAS_MANIFEST_FORCE_HYDRATE=1` for this workflow.

```bash
.venv/bin/python -c \
  "from scripts.lexicon.manifest_io import load_manifest; print(len(load_manifest()['entries']))"
cp site/src/data/lexicon-manifest.json /tmp/atlas-hydrated-baseline.json   # #5077 shrink-gate baseline
.venv/bin/python scripts/lexicon/enrich_manifest.py
.venv/bin/python -m scripts.audit.generate_search_index --db data/atlas.db
.venv/bin/python scripts/lexicon/export_open_dataset.py
.venv/bin/python -m scripts.audit.generate_daily_pool
.venv/bin/python scripts/lexicon/verify_manifest.py --baseline /tmp/atlas-hydrated-baseline.json
.venv/bin/python -m scripts.lexicon.publish_manifest
```

The last command publishes a Release asset and must run only when publishing is
authorized. See `docs/bug-autopsies/atlas-manifest-source-split.md` for the
2026-07-13 evidence behind this split.

### Offline enrich is non-destructive (preserve-vs-retract, #5077)

`enrich_manifest.py` recomputes gated sections (synonyms/antonyms/homonyms/paronyms/
idioms) from scratch each run. The **synonyms** and **idioms** sections need a live
slovnyk lookup (synonyms from the slovnyk synonym dictionaries; idioms from the
Фразеологічний page). With `LEXICON_SLOVNYK_OFFLINE=1` — or after the per-lemma cache
is reset when its `schema_version` bumps, or a transient error — a gate that **cannot
run** used to return empty and silently overwrite the previously-confirmed published
section (809 sections stripped + 1,748 shrunk on the 2026-07-13 go-live). Enrich now
distinguishes three per-section outcomes and records the notable ones in an entry's
`gate_provenance` map:

- **ran-and-confirmed** — gate ran, kept/added items (default; not recorded).
- **ran-and-rejected** — gate ran and dropped items (a quality win, e.g. WordNet
  auto-translation junk `ключ→джерело/живець`); recorded as `rejected`.
- **did-not-run** — gate could not consult its source; a confirmed item that would be
  dropped is preserved byte-for-byte, and the non-consultation is always recorded as
  `skipped-offline` (even when nothing was lost), so the audit trail distinguishes a
  freshly-gated section from one carried over unconsulted.

"Did the gate run" is decided **per relevant slug set**, not `bool(lookups)`: the
synonyms gate ran only when a synonym slug was consulted, the idioms gate only when
the phraseology slug was. A partial cache that holds only unrelated slugs (e.g. the
davydov warning slug) does not count as the synonym gate having run. **Homonyms,
antonyms and paronyms are local** (VESUM/СУМ numbering, Вікісловник, approved corpus
relation pairs, ZNO paronym pairs) — their source is always available, so their gate
always runs and offline runs let their authoritative local data update.

`gate_provenance` is a **current-run snapshot**: it replaces any prior map wholesale
so each field reflects this run's status (the signal the shrink gate reads); it is not
a history log. Because an offline gate that did not run **preserves** rather than
recomputes, an offline run cannot add brand-new items to a preserved slovnyk section —
run online (the full recipe above, on a data-enabled checkout) to pick up new
slovnyk-sourced chips.

`verify_manifest.py --baseline <hydrated>` adds a **shrink gate**: any per-section
item-count regression vs the hydrated baseline fails the promote unless the entry's
`gate_provenance` marks it `rejected` (gate ran) or the `(lemma, section)` pair is on
`scripts/lexicon/shrink_allowlist.yaml`. This is the second line of defence the old
NONEMPTY→EMPTY hazard scan lacked — it also catches partial shrinks.

## Module Release Recipe

When a module release adds or changes `curriculum/l2-uk-en/*/*/vocabulary.yaml`:

1. Promote or edit the module files.
2. Use the full-manifest recipe above when the published Atlas already contains
   promoted growth entries; use `make atlas` only for an intentionally
   course-only reconstruction.
3. Commit the module changes plus the updated fingerprint and pointer files.
4. Open the PR and let CI run the Atlas freshness and vocabulary coverage gates.
5. After merge, publish with the authorized Atlas publish flow.

Push-to-main deploy remains intentionally disabled in `.github/workflows/deploy-pages.yml`.
Re-enabling automatic deploy is a separate owner decision, not part of the Atlas refresh.

For module promotions, `scripts/sync/promote_module.py --refresh-atlas ...` can run
`make atlas` after `vocabulary.yaml` is promoted. Use it only for an intentionally
course-only reconstruction on machines with the local dictionary data and caches
needed by Atlas enrichment; it is not a replacement for the full-manifest recipe.

## Source Inventory Candidate Intake

Curated ULP/Ohoiko/textbook/headword lists feed Atlas growth candidates with
explicit provenance through:

```bash
.venv/bin/python -m scripts.audit.grow_lexicon_from_sources \
  --inventory data/lexicon/source-inventory/ulp.yaml \
  --out data/lexicon/grow_candidates.json \
  --report
```

The source inventory parser accepts CSV, TSV, JSONL, JSON, or YAML. YAML/JSON
structured inventories use this minimal v1 shape:

```yaml
version: 1
kind: atlas_source_inventory
sources:
  - id: ulp-001
    source_family: ulp
    extraction_mode: curated_headword
    title: Ukrainian Lessons Podcast 1
    url: https://example.test/ulp-001
    headwords:
      - lemma: авто
        context: lesson headword list
```

Flat CSV/TSV/JSONL rows require `lemma`, `source_family`, and
`extraction_mode`; optional provenance fields are `source_id`, `source_title`,
`source_url`, `source_path`, `source_locator`, `context`, `pos`, and `notes`.
Malformed rows fail before candidate output is written. Source-fed candidates
use the same `auto_merge` / `needs_review` payload as content-grown candidates
and carry `source_provenance` through promotion.
