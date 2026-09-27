# Phase P3a notes (#8809)

## Status

P3a — migration complete (1,125 rows), producer routing blocked; P3b
residuals: `v5_mine_kyivan_rus_epigraphy.py`, `v5_mine_middle_ukrainian.py`,
and `v4_production_shards_assembly.py` native archive regeneration (owner:
claude-infra). P3 completion: NO (P3a).

This is an incomplete P3a checkpoint, not a landing claim. A green migration
count alone does not establish producer or consumer completion.

## Selected base and prerequisites

The selected base is `55d0ed1515835e5f7b7d1d12b933ad4c46706e1f`, the
merge of issue #8955 (PR #8968), which admits companion-only set publication.
The round-1 migration index was integrated from saved tree
`2512a80476d99c6eb5b1c9a31890258c2b445292` on top of that base without
restarting the migration or deleting any untracked A bytes. Its saved backup
ref is `refs/p3a-backup/20260927-r1-staged` at
`b66c4f1ed2af3383abf502ea64f07c42772eb519`.

In this worktree, each `git merge-base --is-ancestor <sha> HEAD` exited 0 for
P2 `d3506e3b794d2db39f9ab15ebc6585733389c896`, set engine
`702502930188d7842178f09c3c99221cc73baa90`, reactivation
`6eebba6d8ab5359bf864c478097e0b1970326d91`, and companion-only engine
`55d0ed1515835e5f7b7d1d12b933ad4c46706e1f`.

## Frozen migration reconciliation

The frozen table has 713 K files (12,942,226 bytes) and 412 A files
(637,987,720 bytes) under `data/projects/open_model_data/`. The post-integration
row audit compared every K target's staged blob and Git mode with the table,
hashed every K disk file, compared every A row with its selected-base Git blob
and mode, verified every A disk SHA-256 against both pre-untrack hashes in its
manifest, checked its executable mode, and confirmed it is untracked. Raw
summary: `rows=1125 K=713 K_bytes=12942226 A=412 A_bytes=637987720 errors=0`.
No production generator ran for this evidence. The 412 A bytes remain on disk
at their original public `data/` paths; only the Git index untracks them.

| Class | Group | Rows | Bytes |
| --- | --- | ---: | ---: |
| A | open_model_archive_payload | 80 | 102,252,004 |
| A | open_model_component_payload | 17 | 12,547,174 |
| A | open_model_evidence_indexes | 10 | 67,249,187 |
| A | open_model_other_indexes | 49 | 76,736,852 |
| A | open_model_release_payload | 233 | 339,882,386 |
| A | open_model_study_outputs | 23 | 39,320,117 |
| K | open_model_archive_evidence | 16 | 32,357 |
| K | open_model_components | 268 | 6,953,519 |
| K | open_model_contracts | 246 | 2,114,307 |
| K | open_model_controls | 131 | 3,157,025 |
| K | open_model_evidence_controls | 28 | 338,109 |
| K | open_model_release_evidence | 22 | 345,211 |
| K | open_model_study_recipes | 2 | 1,698 |

## Exact-base CI before baseline

The selected-base full-tier CI run is
`https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/36343787225`:
`headSha=55d0ed1515835e5f7b7d1d12b933ad4c46706e1f`, `conclusion=success`.
All ten `pytest-junit-shard-*` artifacts were downloaded in this worktree.
`scripts.storage.test_baseline capture` recorded `34285 test IDs across 10 jobs`
in ignored scratch `.p3a-ci-before-55d0/baseline.json` for the later P3a
after-run comparison.

## Post-merge hydration and held-out checks

The driver must snapshot the six P3 manifests from the pushed branch before
merge. After merge, hydrate and verify P3 in every long-lived checkout that
materialises `data/projects/open_model_data/`: the primary, Mac clone, and
dispatch worktrees. Run from each checkout with its contracted interpreter:

```sh
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --phase P3
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts verify --phase P3
```

The driver/reviewer held-out check compares the table's pre-untrack hashes,
manifest hashes, store objects, and post-hydrate disk bytes for all 412 A rows;
a fresh non-shallow clone must hydrate then verify, while a shallow clone must
report missing A rows with hydrate guidance. Storage publication is distinct
from a study's semantic validity: a changed recipe can invalidate old study
results, which verification must report.

## Unresolved P3a gates at this checkpoint

- The classified K contract writers
  `freeze_phase3_v3a_taxonomy_denominator_compatibility.py`,
  `phase3_v3b_cooperative_control_plane.py`, and
  `phase3_v3c_heldout_extension_solo_custody.py` expose callable
  `write_outputs()` and CLI `--write` routes. Their seven contract outputs are
  classified `open_model_contracts` K in table rows 1105–1111, but no current
  P3 A manifest binds them as companions. They still use direct writes and an
  old `data/` base. The approved companion-only operation requires an owning A
  group and a prior binding; assigning a new owner is an unresolved output
  policy decision, not an implementer assumption. These live producers cannot
  be placed on the fixed historical P3b list.
- `phase3_historical_protection_channels.py` can now build from registry
  inputs while retaining historical logical path identifiers, but its source
  hash changed with the producer edit, so the generated contract differs from
  the frozen K contract. The existing `--check` cannot pass without changing
  that frozen output. No production regeneration was run or authorized.
- The six `artifacts verify --group <P3 group>` commands currently report
  missing store objects for migrated rows. The 412 public A files passed the
  disk/table/manifest hash audit, but this checkout has no P3 store copies yet.
  The driver owns the pre-merge snapshot; verification remains open.
- The current `consumers-P3.tsv` has unchecked entries and the wider K-only
  writer census found more bound companions to route. P3a consumer and producer
  completion, the after CI baseline, and held-out checks remain open. No PR
  should be opened from this checkpoint.
- The selected focused producer/package suite passed 63 tests, and staged
  Python files passed Ruff lint. Ruff format check reported 68 staged Python
  files needing formatting. This checkpoint has not run the full P3a acceptance
  suite; these are not green landing gates.

The generic `end-of-file-fixer` hook attempts to append a newline to the
frozen K file `registry/projects/open_model_data/admission/phase3_vspu_post_ingest_audit_v1.json`.
That would change a table-frozen blob for formatting alone. Its attempted
worktree edit was restored from the staged index; the checkpoint commit skips
only this conflicting hook while retaining the frozen K blob and running the
other commit checks.

## Live registration patterns already declared

| Owning A group | Producer | Narrow path pattern |
| --- | --- | --- |
| `open_model_component_payload` | `build_grammar_component_8342.py` | `data/projects/open_model_data/components/grammar/grammar_train_shard_*_of_*.jsonl` |
| `open_model_component_payload` | `build_grammar_component_8342.py` | `data/projects/open_model_data/components/grammar/grammar_eval_shard_*_of_*.jsonl` |
| `open_model_other_indexes` | `build_decolonization_cases.py` | `data/projects/open_model_data/decolonization/consumer/uldr_dpo_*_part*.jsonl` |
| `open_model_other_indexes` | `build_decolonization_cases.py` | `data/projects/open_model_data/decolonization/consumer/uldr_sharegpt_*_part*.jsonl` |

## Directory split from frozen rows

Each listed dirname is counted directly from the frozen TSV; mixed rows require file-level routing. K files use the registry base; A files use the managed artifact base through `artifact_path()` and set publication.

| Relative directory | K | A |
| --- | ---: | ---: |
| `adjudication` | 2 | 0 |
| `admission` | 46 | 0 |
| `archive/quarantined_historical` | 1 | 0 |
| `archive/quarantined_historical/uldr_v04a_kyivan_rus` | 4 | 1 |
| `archive/quarantined_historical/uldr_v04a_kyivan_rus/sft` | 2 | 30 |
| `archive/quarantined_historical/uldr_v04b_middle_ukrainian` | 4 | 1 |
| `archive/quarantined_historical/uldr_v04b_middle_ukrainian/sft` | 2 | 30 |
| `archive/uldr_v1_production` | 3 | 0 |
| `archive/uldr_v1_production/dpo` | 0 | 6 |
| `archive/uldr_v1_production/sft` | 0 | 12 |
| `canary` | 2 | 5 |
| `components/decolonization` | 6 | 4 |
| `components/decolonization/reviews` | 250 | 0 |
| `components/dialects` | 1 | 0 |
| `components/grammar` | 9 | 13 |
| `components/idioms` | 1 | 0 |
| `components/textbooks` | 1 | 0 |
| `contracts` | 246 | 0 |
| `custody` | 3 | 1 |
| `dataset` | 2 | 1 |
| `decolonization/consumer` | 1 | 8 |
| `decolonization/generated` | 1 | 8 |
| `decolonization/mined` | 1 | 3 |
| `decolonization/partitions` | 5 | 2 |
| `decolonization/seeds` | 3 | 5 |
| `decolonization/stem_controls` | 1 | 1 |
| `delivery` | 1 | 0 |
| `detector` | 5 | 1 |
| `evidence` | 25 | 2 |
| `evidence/phase3_heldout_partition_v1` | 1 | 0 |
| `evidence/source_universe_v1` | 2 | 8 |
| `examples` | 2 | 0 |
| `extraction` | 3 | 1 |
| `integrations` | 1 | 0 |
| `inventory` | 6 | 2 |
| `language` | 2 | 1 |
| `model_views` | 11 | 0 |
| `pilot` | 3 | 1 |
| `profiles` | 4 | 1 |
| `provenance` | 3 | 1 |
| `reference` | 3 | 2 |
| `release/correction_protection_v1` | 2 | 5 |
| `release/uldr_v03_dialect` | 4 | 2 |
| `release/uldr_v05_grammar_valency` | 4 | 1 |
| `release/uldr_v05_grammar_valency/sft` | 2 | 70 |
| `release/uldr_v06_general_assistant` | 6 | 0 |
| `release/uldr_v06_general_assistant/eval` | 2 | 5 |
| `release/uldr_v06_general_assistant/sft` | 2 | 150 |
| `silver` | 3 | 0 |
| `soviet_candidates` | 2 | 2 |
| `splits` | 2 | 1 |
| `study` | 2 | 14 |
| `study/run_output` | 0 | 6 |
| `study/run_output/adapter` | 0 | 3 |
| `trajectories` | 1 | 2 |
| `treatments` | 6 | 0 |
| `trust` | 6 | 0 |

Directories: 57; mixed: 35.

## Constant map

`REGISTRY_OPEN_MODEL_DATA_DIR` is `registry/projects/open_model_data/` for K files; `ARTIFACT_OPEN_MODEL_DATA_DIR` is `data/projects/open_model_data/` for A files. The component, decolonization, idiom, grammar, textbook, dialect, release, correction-protection, archive, archived-ULDR, and quarantined-historical subdirectories each have `REGISTRY_*` and `ARTIFACT_*` constants in `scripts/projects/open_model_data/paths.py`. `CONTRACTS_DIR` derives from the registry base. The former `OPEN_MODEL_DATA_DIR` is removed. A directory constant does not determine an individual file's class; the table and group manifest do.
