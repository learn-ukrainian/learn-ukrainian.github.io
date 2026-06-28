# Word Atlas Source Inventory Review Candidates

Use this workflow to turn the committed source inventory seeds into a small
review-only Atlas candidate artifact.

```bash
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates --report
```

By default the command writes
`/tmp/atlas-source-inventory-review-candidates.json`. The output is review
material only. Do not commit it and do not copy it into the live Atlas data
files.

The committed source inventory inputs are:

- `data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml`
- `data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml`

The candidate JSON follows the existing grow-candidate shape: `counts`,
`auto_merge`, and `needs_review`. The wrapper also adds `review_only` metadata
with the workflow id, inventory paths, review output path, and
`production_outputs_updated: []`.

Every generated candidate must retain non-empty `source_provenance`. The seed
smoke run currently processes all six source inventory headwords: `кіт`,
`риба`, `ракета`, `яблуко`, `єнот`, and `цирк`.

This workflow does not update the live Atlas manifest, search index, browse
files, Words Day pool, daily practice sources, cloze outputs, manifest pointer,
or manifest fingerprint. In this repository those live outputs are under
`site/src/data/`, including:

- `site/src/data/lexicon-manifest.json`
- `site/src/data/lexicon-search-index.json`
- `site/src/data/lexicon-browse-meta.json`
- `site/src/data/lexicon-browse-flagged.json`
- `site/src/data/lexicon-daily-pool.json`
- `site/src/data/lexicon-practice-reviewed-sources.json`
- `site/src/data/lexicon-manifest.pointer.json`
- `site/src/data/lexicon-manifest.fingerprint.json`

The full enrichment step requires the local ignored `data/sources.db`. If a
worktree does not have that database, link or copy the local project database
into the worktree before the smoke run. Keep `data/sources.db` untracked.
