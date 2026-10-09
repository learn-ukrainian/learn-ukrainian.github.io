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

- `registry/lexicon/source-inventory/pos-balanced-grammar-sample.yaml`
- `registry/lexicon/source-inventory/ohoiko-abetka-keywords.yaml`
- `registry/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-39-58.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-59-78.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-79-98.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-99-118.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-119-138.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-139-158.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-159-178.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-179-198.yaml`
- `registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-199-218.yaml`
- `registry/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml`
- `registry/lexicon/source-inventory/vashulenko-grade3-headwords.yaml`

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
under `registry/lexicon/source-inventory-review-decisions/`. Those files are still
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

The private teacher-lesson seeds contribute 228 `teacher_lesson` headwords from
an explicit local vocabulary table. Approval ledgers cover rows 1-218; after PR
`#4208`, live Atlas provenance also covers rows 1-198. Rows 199-218 are
approved for later controlled browse/search publish; they are not live Atlas
output yet. Their committed rows are derived metadata only: no raw private
lesson material, private document paths, or teacher-identifying labels should
appear in the inventory or ledger.

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
does not contain the database by default; symlink the primary checkout
database (via `LEARN_UKRAINIAN_PRIMARY_REPO_ROOT` or cwd/git discovery) into
the worktree before a smoke run and remove it afterward:

```bash
ln -s "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:?}/data/sources.db" data/sources.db
.venv/bin/python -m scripts.audit.generate_source_inventory_review_candidates --report
rm -f data/sources.db
```

Keep `data/sources.db` untracked.

## Published-record holds and exact recovery (#10181)

`registry/lexicon/published-record-dispositions/10181-six.yaml` is a separate,
mandatory version-1 disposition ledger. The adjacent `10181-six.preserved.json`
contains the six complete already-published payloads, their original positions,
the original envelope and transaction digests. These claims are opaque recovery
data; their preservation is not a linguistic endorsement. The holds record
reviewed conflicts or unresolved evidence as `needs_more_evidence`; they make
no replacement, nonexistence, Russianism, POS or CEFR judgment. In particular,
ULIF outer attestation with an entry parse error remains UNKNOWN.

The existing v1 inventory decision validator and admission gates are unchanged.
Selected `--decision-file` subsets cannot omit this mandatory authority. The
planner removes held approvals, while saved-plan application and provenance
overlay reject held contributions before mutation. The shared applier validates
again at the writer boundary, including when a producer supplies a custom
self-check. All four curated/intake producers use these central boundaries.
Built-vocabulary ingestion checks the exact raw row before normalization drops
its identity. Internal row identity survives normalization until merge admission
and never becomes a published payload field. The final build and
`verify_manifest.run()` also enforce active holds; the latter does so even
with conformance disabled. Missing or malformed authority refuses operation.

Inventory predecessors bind complete canonical **rows**, not whole YAML files.
An unrelated ledger rewrite or unrelated vocabulary-row edit does not release
a hold. A changed or moved identified row fails identity verification. Explicit
historical/current keys and paths remain distinct from the separately labelled
one-based structural locators. Built indexes are zero-based with an explicit
one-based row label. Canonical row/payload digests use UTF-8 JSON with
`ensure_ascii=False`, `sort_keys=True`, comma/colon separators and no newline;
ordered-survivor digests add one newline after each canonical payload.

Same-head contributions with independent explicit provenance may survive.
Held provenance remains disallowed under aliasing or slug collisions; a mixed
or opaque contribution refuses operation rather than being guessed apart.
Unresolved `form_of`, relation slugs, alias targets and link-catalog targets block
withdrawal. Unlinked cited synonym text remains verbatim.

Exercise recovery on a prospective copy with an explicit path:

```bash
.venv/bin/python -m scripts.lexicon.dispose_published_records \
  --manifest "$TMPDIR/prospective-manifest.json" --action withdraw
# Apply only after reviewing the dry-run result:
.venv/bin/python -m scripts.lexicon.dispose_published_records \
  --manifest "$TMPDIR/prospective-manifest.json" --action withdraw --write
```

The command defaults to dry-run. It accepts only the exact original or exact
already-withdrawn state, verifies all six identities, re-reads authority before
replacement and conserves every survivor and its order. It refreshes only
present `stats.lemmas_total`, `stats.from_built`, `stats.form_of_count` and
`entries_count` using the established writer predicates; all other envelope
values are preserved. Divergence or missing authority exits 2 without replacing
the manifest. Replacement uses the existing atomic `manifest_io` writer. The
command never rewrites preservation data or derives runtime/publication output.

No releases exist initially. Restoration requires explicit reviewed release
rows (`approve_for_publish` / `restore_projection`) that supersede the retained
holds with exact origin, projection and predecessor-row identities. Forks,
cycles, orphan rows and competing tips fail closed. Root owns exact-head
outside-family CF, same-head CI and merge-queue/merge authorization for that
tracked change before accepting a release for application.

The ledger's `release_reviews` field adapts the existing
`code-review-receipt.v1` carrier and `record_cf_verdict` comment. Each binding
names the canonical release-row digest and superseded hold-row digest, plus
the exact retained receipt JSON (`receipt_json`), recorder verdict body
(`verdict_body`) and their complete UTF-8 byte digests. This keeps the existing
review carrier readable in CI without a dependency on local task files.
Keeping the binding beside the rows avoids a circular digest inside the release
row. The recorder verdict body must contain both literal labels:

```text
release-row-sha256: <canonical release-row digest>
superseded-hold-row-sha256: <canonical hold-row digest>
```

The resolver requires a clean completed receipt, distinct author/reviewer
families, native model/family/harness provenance and the recorder's exact-head
APPROVED cross-family verdict. Arbitrary clearance JSON or a bare approval
string is insufficient. This deterministic validation checks structure and
bindings; it does not prove that a review occurred. Root verifies the genuine
completed review and landing gates using the existing review process.

After valid release authorization, `--action restore` (also dry-run by default)
accepts the exact withdrawn state and restores the preserved bytes, complete
payloads, original ordering and original envelope values, including historical
stale counters. It does not reconstruct missing source-book bytes. Actual
canonical application, independent held-out proof, merged-SHA verification and
Atlas publication remain the accountable root's responsibility.
