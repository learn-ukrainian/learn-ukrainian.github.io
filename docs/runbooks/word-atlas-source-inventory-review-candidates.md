# Word Atlas Source Inventory Review Candidates

Use this workflow to turn committed source inventory seeds into a small
review-only Atlas candidate artifact.

```bash
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates --report
```

The default command writes `/tmp/atlas-source-inventory-review-candidates.json`.
The output is review material only. Do not commit it and do not copy it into
live Atlas data files.

The committed source inventory input is:

- `data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml`
- `data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml`
- `data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-39-58.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-59-78.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-79-98.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-99-118.yaml`
- `data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-119-138.yaml`
- `data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml`

The candidate JSON follows the existing grow-candidate shape: `counts`,
`auto_merge`, and `needs_review`. The wrapper also adds `review_only` metadata:
workflow id, inventory paths, review output path, and
`production_outputs_updated: []`.

It also adds `review_triage`, a review-only publish-readiness summary. The grow
`auto_merge` bucket means a candidate passed low-level dictionary/POS gates; it
is not approval to publish. `review_triage.counts.publish_ready` requires grow
`auto_merge` plus source provenance, POS, and visible English anchor.
`review_triage.counts.needs_publish_review` lists candidates that need human
review before any live Atlas publish batch.

To render the full human-review queue for held rows, write a Markdown report
outside the repository:

```bash
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates \
  --report \
  --queue-report-out /tmp/atlas-source-inventory-publish-review-queue.md
```

The queue report is intentionally ephemeral. The script rejects
`--queue-report-out` paths inside the repository so generated review material
does not land in `docs/reports/`, `curriculum/**/review/`, `status/`, `audit/`,
or live Atlas output paths by accident. Use `--queue-report` only when you want
the full Markdown queue on stdout.

Queue rows include stable queue ids, lemma, POS, grow bucket,
English-anchor state, review reasons, and source references. Human review
decisions should survive beyond the ephemeral queue in tracked ledger files
under `data/lexicon/source-inventory-review-decisions/`. Those files are still
review records, not live Atlas output. Validate them with:

```bash
.venv/bin/python -m scripts.audit.source_inventory_review_decisions
```

Decision rows use stable source-inventory keys derived from lemma, inventory
path, and source locator. Do not use queue row numbers as publish keys; queue
ids can change when row ordering changes.

After review decisions are committed, build the next publish boundary as
another review-only artifact:

```bash
.venv/bin/python -m scripts.audit.plan_source_inventory_promotion \
  --generate-candidates \
  --out /tmp/atlas-source-inventory-approved-promotion-plan.json \
  --report-out /tmp/atlas-source-inventory-approved-promotion-plan.md \
  --report
```

This consumes approved ledger rows and the review-candidate payload, then writes
proposed manifest additions to `/tmp`. It does not publish them. The plan maps
`approved_pos` and `approved_gloss` into the proposed manifest entry, preserves
`source_provenance`, records the source-inventory key, and reports skipped or
missing candidates. The command rejects outputs inside the repository, including
live Atlas data, static lexicon outputs, `status/`, `audit/`, `review/`, and
telemetry artifact paths.

Every generated candidate must retain non-empty `source_provenance`. The
POS-balanced grammar sample contributes 20 source inventory headwords: two rows
each for noun, adjective, numeral, pronoun, verb, adverb, preposition,
conjunction, particle, and interjection. Optional per-headword `gloss` values
are curated learner-facing English anchors for cases where dictionary
enrichment lacks a visible English translation.

The private teacher-lesson seeds contribute 147 reviewed `teacher_lesson`
headwords from an explicit local vocabulary table, with approval ledgers now
covering rows 1-138. Their committed rows are derived metadata only: no raw
private lesson material, private document paths, or teacher-identifying labels
should appear in the inventory.

When a candidate is later promoted into a manifest entry,
`promote_grow_candidates.manifest_entry_from_candidate()` copies
`source_provenance` through verbatim at top level, so granular
source-id/title/locator/context origin is not dropped on promotion. Separate
`course_usage`, derived only from `source_context`/`source_contexts`, stays empty
for source-inventory rows.

Source-inventory manifest promotion is browse/search by default. Do not use
manifest promotion as implicit permission for Words of the Day, practice, or
cloze. If a reviewed row should enter a learner-facing surface later, add a
`surface_admission` mapping to the decision row with explicit boolean keys:
`daily`, `practice`, and `cloze`. Missing `surface_admission` means
`daily: false`, `practice: false`, `cloze: false` for `source_inventory_grow`
entries.

This workflow does not update live Atlas manifest, search index, browse files,
Words of the Day pool, daily practice sources, cloze outputs, manifest pointer,
or manifest fingerprint. In-repository live outputs under `site/src/data/`
include:

- `site/src/data/lexicon-manifest.json`
- `site/src/data/lexicon-search-index.json`
- `site/src/data/lexicon-browse-meta.json`
- `site/src/data/lexicon-browse-flagged.json`
- `site/src/data/lexicon-daily-pool.json`
- `site/src/data/lexicon-practice-reviewed-sources.json`
- `site/src/data/lexicon-manifest.pointer.json`
- `site/src/data/lexicon-manifest.fingerprint.json`

The full enrichment step requires local ignored `data/sources.db`. A worktree
does not contain the database by default; symlink the local project database
into the worktree before a smoke run and remove it afterward:

```bash
ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates --report
rm -f data/sources.db
```

Keep `data/sources.db` untracked.
