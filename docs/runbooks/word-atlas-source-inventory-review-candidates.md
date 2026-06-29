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

The committed source inventory input is:

- `data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml`

The older `ohoiko-abetka-keywords.yaml` and
`bolshakova-bukvar-keywords.yaml` files remain tracked as noun smoke
inventories, but they are not the representative review-candidate input.

The candidate JSON follows the existing grow-candidate shape: `counts`,
`auto_merge`, and `needs_review`. The wrapper also adds `review_only` metadata
with the workflow id, inventory paths, review output path, and
`production_outputs_updated: []`.
It also adds `review_triage`, a review-only publish-readiness summary. The
grow `auto_merge` bucket means the candidate passed low-level dictionary/POS
gates; it is not approval to publish. `review_triage.counts.publish_ready`
requires grow `auto_merge` plus source provenance, POS, and a visible English
anchor. `review_triage.counts.needs_publish_review` lists candidates that need
human review before any live Atlas publish batch.

To render the full human review queue for those held rows, write a Markdown
report outside the repository:

```bash
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates \
  --report \
  --queue-report-out /tmp/atlas-source-inventory-publish-review-queue.md
```

The queue report is intentionally ephemeral. The script rejects
`--queue-report-out` paths inside the repository so generated review material
does not land in `docs/reports/`, `curriculum/**/review/`, `status/`,
`audit/`, or live Atlas output paths by accident. Use `--queue-report` only
when you want the full Markdown queue on stdout. Queue rows include stable
queue ids, lemma, POS, grow bucket, English-anchor state, review reasons, and
source references.

Every generated candidate must retain non-empty `source_provenance`. The
representative smoke run currently processes 20 source inventory headwords:
two rows each for noun, adjective, numeral, pronoun, verb, adverb,
preposition, conjunction, particle, and interjection.
Optional per-headword `gloss` is for curated learner-facing English anchors
when dictionary enrichment lacks a visible English translation.

When a candidate is later promoted into a manifest entry,
`promote_grow_candidates.manifest_entry_from_candidate()` copies
`source_provenance` through verbatim at the top level, so the granular
source-id/title/locator/context origin is not dropped on promotion. This is
separate from `course_usage`, which is derived only from
`source_context`/`source_contexts` and stays empty for source-inventory rows.

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
