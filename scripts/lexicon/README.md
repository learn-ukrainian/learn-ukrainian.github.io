# Word Atlas Lexicon Pipeline

`make atlas` is the release command for refreshing the static Word Atlas data:

```bash
make atlas
```

The target runs `scripts.lexicon.build_data_manifest`, `scripts/lexicon/enrich_manifest.py`,
and `scripts/lexicon/verify_manifest.py`. It writes the committed Atlas data files:

- `site/src/data/lexicon-manifest.json`
- `site/src/data/lexicon-manifest.fingerprint.json`

## Module Release Recipe

When a module release adds or changes `curriculum/l2-uk-en/*/*/vocabulary.yaml`:

1. Promote or edit the module files.
2. Run `make atlas`.
3. Commit the module changes plus the updated manifest and fingerprint.
4. Open the PR and let CI run the Atlas freshness and vocabulary coverage gates.
5. After merge, publish with the manual `deploy-pages.yml` `workflow_dispatch`.

Push-to-main deploy remains intentionally disabled in `.github/workflows/deploy-pages.yml`.
Re-enabling automatic deploy is a separate owner decision, not part of the Atlas refresh.

For module promotions, `scripts/sync/promote_module.py --refresh-atlas ...` can run
`make atlas` after `vocabulary.yaml` is promoted and include the manifest outputs in the
promotion commit. Use it only on machines with the local dictionary data and caches needed
by Atlas enrichment.

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
