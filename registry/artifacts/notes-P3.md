# Phase P3a notes (#8809)

## Status

P3a — migration complete (1,125 rows), producer routing and consumer
dispositions still partial; P3b
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

## Round-3 source identity and standalone K writers

The frozen historical-protection generator SHA-256
`9aab109f9dd676f28c5b834d4979fef4a3aff017381ec2b2bd2363bc00717632`
equals the source blob at selected base `55d0ed1515`, independently of the
contract's own field. It is now named `FROZEN_GENERATOR_SHA256` and remains
the contract's provenance, not the live implementation hash. The generator
still verifies every pinned input byte and reconstructs the exact frozen
contract; `--check` remains byte-exact. Its bound
`open_model_other_indexes` companion remains on the approved K-only set route.

The V3-A, V3-B, and V3-C contracts likewise bind pre-migration validator
source hashes `9526e76ddc65`, `b0638a47a737`, and `0f9453193ceb` (full
hashes in the source and frozen contracts). V3-B also binds predecessor
validator hashes `50a6ef3de21e` and `9526e76ddc65`. Each was confirmed
against `git show 55d0ed1515:<source> | sha256sum`; these exact source
identities are retained as historical provenance. Actual predecessor K
artifact bytes are still checked against their independent pinned hashes.
The V3 foundation validator's frozen identity is `50a6ef3de21e` and its
bound K inputs are read from the registry while retaining frozen logical
names. The five focused top-level suites and isolated writer fixtures passed
`157 passed, 1 skipped`.

V3-A/B/C `write_outputs()` now construct and validate their complete bundles
before direct registry publication. The narrow publisher checks that every
destination is tracked and clean against HEAD, preserves file modes, and
does not touch A paths or manifests; three isolated writer fixtures passed.
The classification rows 1105–1111 name seven K files, but these functions
write six: V3-A reads its schema and writes only its artifact and matrix;
V3-B and V3-C each write a schema and artifact. They have no A owner and
require no new companion binding.

The source-identity inventory found 28 checkpoint-changed Python sources whose original
hash occurs in a frozen K contract. Besides the V3/historical-protection
sources above, the affected contracts refer to `admit_existing_corpus`,
`correction_protection_consumer`, `gemma_hardware_probe`,
`language_contact_detector`, `model_view_exporter`,
`phase3_audit_entropy`, `phase3_cycle_void_receipt`,
`phase3_functional_roles`, `phase3_historical_materialization`,
`phase3_historical_representation`, `phase3_lavra_near_caves_intake`,
`phase3_linguistic_representation`, `phase3_pravopys_delta`,
`phase3_recovery_contracts`, `phase3_rule_author_packets`,
`phase3_rule_author_runner`, `phase3_source_dispositions`,
`phase3_source_production_transport`,
`phase3_spas_catalog_materialization`, `phase3_spas_glyph_adapter`,
`phase3_spas_layout_candidates`, `phase3_spas_source_attribution`,
`phase3_textbook_nonhit`, `phase3_v2_compatibility`,
`phase3_v3_cooperative_control_plane`, `phase3_vspu_db_cutover`, and
`silver_evidence_factory`. The remaining references need entry-point
validation before landing; a frozen hash is never treated as the current
implementation hash.

The `end-of-file-fixer` hook now excludes only the exact frozen
`registry/projects/open_model_data/admission/phase3_vspu_post_ingest_audit_v1.json`
path. Its classified Git blob `9c1ab66a89d54c2303cec5d4714abdf3a2c29e88`
and mode `100644` remain unchanged; the hook passed on it and a normal
applicable Python file. Ruff formatted the changed Python files without
changing frozen K bytes.

## Round-4 consumer checkpoint

The driver completed the P3 store snapshot for the existing manifests. In this
worktree, `artifacts verify --group` exited 0 for all six groups: archive 80,
component 17, evidence 10, other 49, release 233, study 23. The repeated
table/index/disk/manifest audit printed
`rows=1125 K=713 K_bytes=12942226 A=412 A_bytes=637987720 errors=0`.
No A file or P3 manifest was changed by this round.

The committed consumer checkpoint `f11b10134b61a7bd241af27598b64506f2ce11c6`
routed portable package assets, language contact, adoption and foundry inputs,
correction-protection mixed release consumption, and several top-level and
project tests. Its full top-level selection printed
`694 failed, 1401 passed, 66 skipped, 6 errors` across 2,167 tests. The
project selection reached 94 percent and printed
`171 failed, 2034 passed, 12 skipped, 17 errors` before its
`v6_mine_general_assistant_textbooks` content-filter test exceeded the
configured timeout; the exact pytest process was interrupted. These are
diagnostic checkpoint results, not passing final-head proofs.

Subsequent routing uses `REGISTRY_OPEN_MODEL_DATA_DIR` for K inputs while
keeping frozen logical `data/` locators in contracts. P1's mixed source
universe reads its eight A ledgers from one verified
`open_model_evidence_indexes` snapshot. The P1, P2, and modern-contact
builders reconstruct their frozen outputs byte for byte (`True` for all
three); their changed bound K publication uses the existing companion-only
set transaction. Focused tests after Ruff formatting printed `182 passed`
for P1/P2/modern-contact, `246 passed, 7 skipped` for ten source-intake
suites, and `8 passed` for companion-only publication fixtures.

Historical source identities were independently compared with
`git show 55d0ed1515:<source> | sha256sum` before adding each pinned
provenance constant. Frozen receipt self-hashes gate the historical identity
for Babych, DonNU, LNU, Pliush, UzhNU, VSPU, ZhDU, Minchak, and Wave-L
intakes; new receipts bind their current implementation. P1, P2, and
modern-contact retain their original generator hashes as frozen provenance
while checking the actual migrated input bytes. A scan of changed source
hashes in K contracts found 36 source bindings from the earlier checkpoint,
and 21 more candidate K-only modules affected by this round. The remaining
bindings need entry-point checks; this inventory is not yet complete.

The two local decolonization component failures involving missing source
records were reproduced with the same messages against an archive of base
`55d0ed1515` using the same shared databases. Their CI baseline status was
`skipped`, so the local base replay is the evidence for those two tests.

The next round-4 checkpoint ran the full top-level selection before its
latest consumer fixes: `359 failed, 1789 passed, 13 skipped, 6 errors`.
Physical K reads were then corrected in the P4 pilot, recovery validator,
source-disposition adapter, chronology, and historical spine. The frozen P4
pilot was reconstructed byte for byte with its original generator provenance,
while both predecessor implementations received independent current source
pins. The historical spine kept its frozen logical paths and source hashes;
current migrated sources received exact separate pins, each old identity
matched to a Git history blob. The combined focused selection for these
consumers printed `332 passed` with no failures or errors. The full top-level
and project selections must be rerun on the final head; this checkpoint is
not consumer acceptance.

A round-4 frozen-source scan independently hashed every Python source at
`55d0ed1515` and searched all tracked migrated K bytes for the hash. It found
65 source identities referenced by 72 K contracts; 63 of those sources have
different current bytes. The ignored diagnostic table is
`.pytest-tmp/source-pin-report.tsv`. These old hashes are historical contract
provenance. This scan is a candidate inventory, not evidence that every
producer's self/predecessor validation route has been exercised or that
older-than-base identities have all been found.

## Round-5 diagnostic checkpoint

The first top-level `tests/test_open_model_*.py` run on the inherited round-4
tree reported `196 failed, 1959 passed, 13 skipped` across 2,168 tests.
The `tests/projects/open_model_data` run reached 94 percent and reported
`124 failed, 2086 passed, 12 skipped, 17 errors` before an exact-process
interrupt. Two consecutive 110-second timeout stacks identified
`test_v6_mine_general_assistant_textbooks.py::test_held_out_firewall_zero_leakage`
and `::test_dynamic_verification_functions_pass`. Both runs used an in-checkout
pytest base; many private-source and private-output tests explicitly reject
that fixture location. The external-temp full top-level replay on code head
`2cfecf5fe2` passed `2155 passed, 13 skipped`. The external-temp project
selection excluding the timed-out 33-test textbook module reported
`124 failed, 2184 passed, 14 skipped, 11 errors` across 2,333 tests.
The 135 exact failing/error IDs are in ignored local
`.pytest-tmp/r5-project-failing-ids.txt`; the 33 omitted IDs are in
`.pytest-tmp/r5-omitted-nodeids.txt`. The first project errors still open
K schemas and receipts at old `data/` paths. Full project-suite replay and
test-by-test base comparisons remain open. The ignored local logs are
`.pytest-tmp/r5-top.log`, `.pytest-tmp/r5-project.log`,
`.pytest-tmp/r5-top-external.log`, and `.pytest-tmp/r5-project-external.log`.

On the same code head, the six P3 A-group `artifacts verify --group` runs
passed with counts `80, 17, 10, 49, 233, 23`. The table/blob/disk/manifest
audit reported
`rows=1125 K=713 K_bytes=12942226 A=412 A_bytes=637987720 errors=0`.
The storage/classification/sparse-guard selection passed `219 passed,
4 skipped`, and `git ls-files data` equalled the tracked-data allowlist.

An independent replay of the candidate source-pin table compared all 65
sources against base `55d0ed1515` and current disk bytes:
`rows=65 contracts=72 drift=63 hash_report_errors=0`. Two source bytes remain
unchanged. Eleven of the 63 drifting sources changed in the checkpoint commit.
This validates the recorded byte identities only; semantic equivalence,
entry-point checks, and a search for older-than-base identities remain open
under Decision H. The ignored candidate table is
`.pytest-tmp/source-pin-report.tsv`.

The final-tree scanner regenerated `consumers-P3.tsv` with 3,166 rows and
3,166 blank checks (737 distinct consumers). Each executable row still needs an exercised
disposition; doc and logical-id rows need reasons. This is a stop gate for P3a.

## Round-6 reader routing checkpoint

Readers that still opened moved K files under `data/projects/open_model_data/`
now resolve them with `resolve_open_model_path()` in
`scripts/projects/open_model_data/paths.py`. The function uses the frozen
classification table: K members resolve under
`registry/projects/open_model_data/`, A members stay under
`data/projects/open_model_data/`, and logical `data/` strings stored in
contracts are left unchanged. Mixed directories keep the caller's prefix.
The scanner base list includes `resolve_open_model_path`.

The round-5 project failures were concentrated in the V4 pilot, provenance,
language, extraction, split, dataset, canary, grammar, dialect, ULIF, and
delivery readers. Those filesystem opens now go through the classifier.
Delivery verification treats a managed study snapshot mismatch as a failed
check. Replaying the 135 round-5 failure IDs reported `133 passed, 2 failed`.
The two failures are `test_decolonization_component_8340.py` textbook lookups
(`decol_syn_032`, `decol_lex_003`). `git diff 55d0ed1515` does not change the
`textbooks_fts` query or the missing-evidence error in
`query_source_evidence`, so they are the same `sources.db` misses already
recorded against that base. The full `tests/projects/open_model_data` run on the routing commit, including
the general-assistant module, reported `3 failed, 2347 passed, 17 skipped`.
Two failures are the `sources.db` lookups above. The third was
`test_synthetic_pipeline_hermetic_run` opening
`v1_general_assistant_eval_record.schema.json` under `data/`; that schema
read now uses `resolve_open_model_path()`, and the isolated rerun passed.
`consumers-P3.tsv` still has blank checks.

## Decision H frozen-contract semantics

For every source in `.pytest-tmp/source-pin-report.tsv` whose current bytes
differ from base `55d0ed1515` (63 identities, 72 contracts), `git rev-parse`
of `HEAD:registry/projects/open_model_data/<rel>` equals
`55d0ed1515:data/projects/open_model_data/<rel>`. Result:
`contract blob mismatches 0`. The frozen contract documents are the
pre-migration blobs, so their semantics are unchanged. Two further identities
in that table have identical source bytes. The code diffs are path routing,
formatting, publication through the existing companion or standalone-K
routes, and historical provenance pins. One current-file pin,
`EXPECTED_CHRONOLOGY_V1_IMPLEMENTATION_SHA256` in
`phase3_historical_document_chronology_source_dates.py`, moved from the base
hash of `phase3_historical_document_chronology.py` (`67ae42be05f8`) to that
file's current hash (`ee7721a822eb`). The spine contract does not embed
either value.

The consumer-check column remains open at this checkpoint.

## Unresolved P3a gates at this checkpoint

- The round-3 top-level `tests/test_open_model_*.py` consumer run failed:
  `1103 failed, 774 passed, 67 skipped, 73 errors` on its checkpoint head.
  The first errors show live readers and tests still opening K inputs at old `data/` locations
  (for example `phase3_p1_universe_freeze_v1.json` and
  `examples/portable-corpus-v1.jsonl`). All executable consumer dispositions
  and the source-identity inventory must be completed by the P3a
  implementer before exact-head review.
- The round-3 `tests/projects/open_model_data` run also failed:
  `704 failed, 1543 passed, 17 skipped, 101 errors`. Its first failures are
  the same moved-K path class, including old `data/` references to contract
  schemas and admission receipts. The P3a implementer owns those reader and
  test routes; these are failed required proofs, not P3b deferrals.
- The store snapshot and six-group verification are complete. The current
  `consumers-P3.tsv` still has unchecked entries, and the wider K-only
  entry-point census remains unfinished. The after-CI baseline is intentionally
  deferred until exact-head cross-family review under Decision J. P3a producer
  and consumer completion and the driver-owned held-out checks remain open.
  No PR should be opened from this checkpoint.

No production generator or contract regeneration ran in round 3.
The storage/classification/sparse-guard selection passed `219 passed, 4
skipped`; the focused frozen-contract and standalone-K selection passed
`157 passed, 1 skipped`. These passing selections do not override the failed
consumer suites above.

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
