# Phase P2 notes (#8809)

Scope: all 454 `data/lexicon/` classification rows. The 281 K files move to
`registry/lexicon/`; the 173 A files remain byte-identical on disk under
`data/lexicon/`, leave Git, and are covered by six migration manifests.
Untracked local state under `data/lexicon/` is outside this phase.

## K blobs changed only for reviewed path strings

The 269 other K blobs and all K modes remain unchanged. These 12 README files
rewrite links to K files from `data/lexicon/` to `registry/lexicon/`; paths to
untracked state remain under `data/lexicon/`:

- `registry/lexicon/grow-triage-ledgers/README.md`
- `registry/lexicon/source-inventory/grade-01/README.md` through
  `registry/lexicon/source-inventory/grade-11/README.md`

## Embedded path strings in phase data

The pre-edit scan found 82,589 `data/lexicon/` occurrences in 80 K files and
5,135 in five A files. Most are stable provenance identifiers, including
82,414 review-ledger `path:` fields and 5,105 candidate `inventory_path` fields.
Decision matching and source keys depend on these identifiers. The physical
reader of a staged inventory maps its logical identifier to the tracked
`registry/lexicon/` path or verifies a declared A artifact before opening it;
the identifiers in the data stay unchanged. `practice-creation-review.json`
uses its two old path keys only as historical `baseline_sources` metadata.
The recovery snapshot JSONL and parked candidate JSON also retain provenance.

The 12 README links above were the resolvable K references rewritten in the
data files. Grade README references to `data/lexicon/slovnyk_cache/` are
untracked host-state paths. `ohoiko-corpus-intake.summary.md` commands and
references target the untracked source inventory and remain under `data/`.
The remaining paths in the frozen residual census and review ledgers record
their original source identity.

## A producers and readers

Producers routed through the existing `write_artifact` staging and `publish`
path for declared P2 A targets:

- `scripts/lexicon/build_kaikki_lookup.py` (`lexicon_kaikki`)
- `scripts/lexicon/extract_grinchyshyn_paronym_candidates.py`,
  `miyklas_relation_miner.py`, `reconcile_calque_clusters.py`, and
  `heritage_calque_wave.py` (`lexicon_candidates`)
- `scripts/lexicon/extract_book_headword_inventory.py`,
  `extract_textbook_chunk_headword_inventory.py`, and `admit_stem_slice_2a.py`
  (`lexicon_headword_candidates`)
- `scripts/lexicon/ohoiko_paired_headword_split.py`
  (`lexicon_recovery_snapshots`)
- `scripts/lexicon/park_thin_entries.py` (`lexicon_parked`)
- `scripts/practice_deck/end_dictionaries.py` (`lexicon_end_dictionaries`)

Default readers of A files now resolve through `artifact_path()` and fail with
hydrate guidance if missing. The private teacher-lesson candidate producer
defaults outside the repository and rejects repository output paths; it does
not write its historical A row. The two generic grow-candidate writers target
unclassified ignored host state, outside the 173 P2 A rows.

## Review follow-up sweep

The follow-up searched Kaikki constants and defaults, f-string and path-join
constructions containing `lexicon`, and `OSError`/`FileNotFoundError` handlers
that return an empty value. The regenerated 505-row consumer census records
P2 readers and writers with executed checks, including two manually listed
Kaikki readers that its syntax scan does not detect.

- Physical K output: `curated_textbook_jsonl_repromote.py` now defaults to its
  existing registry inventory; `INV_REL` remains a provenance identifier.
  K joins in `build_data_manifest.py`, `esum_garbled.py`,
  `generate_vesum_aliases.py`, `anchor_curation_evidence.py`,
  `apply_anchor_worksheet.py`, `atlas_intake_core.py`,
  `curriculum_atlas_intake.py`, `ohoiko_atlas_intake.py`, and
  `atlas_source_census.py` already target `registry/`. The first two K readers
  now propagate missing or malformed file errors.
- Kaikki A paths: `fill_local.py`, `reenrich_thin_manifest_entries.py`, and
  `repair_plural_noun_aliases.py` now use the verified default and fail when
  unhydrated. `enrich_manifest.py`, `admit_teacher_table.py`,
  `runner/enrich_offline_20k.py`, `runner/reduce_ulif_20k.py`,
  `runner/worker_enrich.py`, `admit_fmu_boosters.py`,
  `admit_stem_slice_2a.py`, `promote_teacher_lesson_intake.py`,
  `grow_lexicon_from_content.py`, `audit/grow_lexicon_from_sources.py`, and
  `audit/grow_lexicon_from_lemmas.py` already use the verified default on
  their execution paths. `build_kaikki_lookup.py` is the declared writer;
  `build_classification_table.py` contains the frozen logical path.
- Other A paths: `source_inventory_review_decisions.py` and
  `load_relation_candidates.py` resolve dynamic candidate paths through
  `artifact_path()`. Declared writers above use `write_artifact()`;
  unregistered new outputs under the migrated tree now raise before writing.
  The specific `.gitignore` rules preserve host state in `cache/`,
  `slovnyk_cache/`, `runner-mirror/`, intake journals and locks, and named
  local grow, triage, and private-intake outputs. Remaining `data/lexicon`
  joins in grow, runner, cache, and report scripts target that host state.
  Joins under `site/public/lexicon`, `/lexicon/` URLs, and other `data/`
  trees do not resolve P2 files.
- Remaining silent-empty catches: `enrich_manifest.py` handles the mutable
  Slovnyk cache, `promote_teacher_lesson_intake.py` a resumable journal,
  `heritage_classifier.py` an unrelated registry lookup and optional DB,
  `runner/finalize.py` optional process metrics, and
  `check_manifest_vocabulary_coverage.py` a Git-diff failure that triggers
  full coverage. None reads a P2 K or A artifact.

## CI test-ID reference

Main changed test IDs after the P1 baseline, so the pre-phase reference is the
full-tier base CI capture in `test-baseline.p2.pre.json` (run 36243687964,
source commit `526a1055ea3c01193f9cd19d0cda260c1867255a`). The final P2
capture in `test-baseline.p2.json` is from full-tier branch CI run 36258686968
on final code commit `9c87ac00a94162e403340d183dcda77f99c205a1`.
Comparing pre-phase to P2 passes with eight new passing review tests, two
sparse-test renames, and two `needs_artifact` dispositions. Both artifact
cases were proven by `host-run-p2.junit.xml`.

A direct P1-to-P2 comparison still reports three test IDs renamed on main
between P1 and the base commit, plus a new restore test that CI skips when its
external tool is unavailable. The comparison tool has no valid disposition
for an unrelated `absent -> skipped` addition. This is why the base CI capture
is the phase's before reference under the locked spec's changed-ID rule; no
P2 lost test ID is left without a disposition.

## Merge-time host operation

The driver runs `artifacts snapshot --phase P2 --manifests-ref origin/<branch>`
in each required long-lived checkout before merge. This worker does not run
that command. After pull, hydrate and verify the six P2 groups on each required
host. The branch contains all six manifests for the snapshot ref.
