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
`scripts.lexicon/enrich_manifest.py`, and `scripts.lexicon/verify_manifest.py`.
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
.venv/bin/python scripts/lexicon/enrich_manifest.py
.venv/bin/python -m scripts.audit.generate_search_index
.venv/bin/python scripts/lexicon/export_open_dataset.py
.venv/bin/python -m scripts.audit.generate_daily_pool
.venv/bin/python scripts/lexicon/verify_manifest.py
.venv/bin/python -m scripts.lexicon.publish_manifest
```

The last command publishes a Release asset and must run only when publishing is
authorized. See `docs/bug-autopsies/atlas-manifest-source-split.md` for the
2026-07-13 evidence behind this split.

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
