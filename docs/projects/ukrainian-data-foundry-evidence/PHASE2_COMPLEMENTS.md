# Phase 2: rights-gated complements

[Українська версія](PHASE2_COMPLEMENTS.uk.md)

Phase 2 is a local, deterministic evidence-routing step. It consumes a
validated Phase 1 `document_signal_record_v1` JSONL manifest and its receipt,
then emits three text-free artifacts:

- a one-for-one `prepared_data_complement_record_v1` JSONL complement;
- an `evidence_resolution_item_v1` JSONL worklist, one item for each actual
  source identifier and unresolved/blocked/excluded capability; and
- a `prepared_data_complement_receipt_v1` receipt, written last as the bundle
  commit marker.

First reproduce Phase 1 locally. The manifest is deliberately not committed;
the committed inputs are `document_signal_config_v1.json` and
`document_signal_receipt_v1.json`.

```bash
.venv/bin/python -m scripts.projects.open_model_data.document_signal_manifest \
  --config data/projects/open_model_data/evidence/document_signal_config_v1.json \
  --input-root . --manifest-output /safe/local/phase1-manifest.jsonl \
  --receipt-output /safe/local/phase1-receipt.json --spool /safe/local/phase1-spool.sqlite
```

Generate the committed public-safe locator sidecar before running Phase 2:

```bash
.venv/bin/python -m scripts.projects.open_model_data.source_work_locator_index \
  --config data/projects/open_model_data/evidence/source_work_locator_config_v1.json \
  --input-root . \
  --output data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl
```

The locator contains only allowlisted source and work metadata, a canonical
locator when one is actually known, opaque Phase 1-compatible identifiers, and
counts. It never contains chunks, source text, evaluation fingerprints, or a
permission claim. The published `.compact.jsonl` is a lossless, UTF-8 compact
transport: its first line declares the semantic row schema, field order,
family descriptors, record count, ordering, and hash of canonical expanded
JSONL. Consumers validate and expand every compact row to the existing full
object before Phase 2 sees it; artifact byte hashes and sizes bind the compact
file itself. A consumer can inspect the committed locator without owning our
corpus; rebuilding it requires the corresponding local source databases.

Then run Phase 2 with the Phase 1 outputs and locator:

```bash
.venv/bin/python -m scripts.projects.open_model_data.source_capability_complements build \
  --phase1-manifest /safe/local/phase1-manifest.jsonl \
  --phase1-receipt /safe/local/phase1-receipt.json \
  --policy data/projects/open_model_data/evidence/source_capability_policy_v1.json \
  --locator-index data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl \
  --complement-output /safe/local/complement.jsonl \
  --worklist-output /safe/local/evidence-worklist.jsonl \
  --receipt-output /safe/local/complement-receipt.json
```

A consumer may independently acquire material it is entitled to use, then
align records using a canonical locator plus work metadata and the complement's
`content_sha256`. The sidecar neither supplies source bytes nor grants learning,
redistribution, download, or publication permission.

Verify every input binding and byte of every output before using an artifact:

```bash
.venv/bin/python -m scripts.projects.open_model_data.source_capability_complements verify \
  --policy data/projects/open_model_data/evidence/source_capability_policy_v1.json \
  --locator-index data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl \
  --phase1-manifest /safe/local/phase1-manifest.jsonl \
  --phase1-receipt /safe/local/phase1-receipt.json \
  --complement /safe/local/complement.jsonl \
  --worklist /safe/local/evidence-worklist.jsonl \
  --receipt /safe/local/complement-receipt.json
```

`filter` is source-blind: it only reads the text-free complement and requires
one known independent capability, state, and optional route.

```bash
.venv/bin/python -m scripts.projects.open_model_data.source_capability_complements filter \
  --complement /safe/local/complement.jsonl \
  --capability local_model_learning --state evidenced --route candidate --faithful
```

## Current policy truth and limits

The policy context is for a public downstream consumer operating locally. It
is an evidence record, not legal advice, and does not decide jurisdictional
law. Capabilities are deliberately independent: acquisition/retention, local
preparation, local model learning, raw redistribution, derived redistribution,
dataset publication, and model publication each retain their own state and
route. No all-capabilities intersection is used.

Existing accepted Wikipedia rights/admission evidence supports local retention,
preparation, and local model learning for the declared local public-consumer
scope. It does not settle raw or derived redistribution, dataset publication,
or model publication. The other family defaults remain unresolved unless a
source-specific override with resolving evidence is added. Partial evidence is
retained with concrete missing keys instead of discarded.

The complement faithfully binds each Phase 1 non-text field, including
dimensions, evidence state, content hash, signals, duplicate signals, and
heldout-contamination signal. Those diagnostics never erase records. Faithful
representation is only a candidate when both local preparation and local model
learning are evidenced. Loss-masked and protected representations remain
`not_classified_phase2` without row-level evidence.

Build requires exactly one schema-valid locator row for every actual Phase 1
`source_id`/`work_id` pair. It rejects missing, extra, reordered, duplicate,
family-mismatched, inventory-mismatched, or hash-drifted locator mappings.
Each complement row binds its locator record and index hash; each work item
contains usable locator references for its affected works; and the receipt
binds both locator artifact and schema. Locator presence is alignment metadata
only: it never grants model-learning, redistribution, download, or publication
rights.

Builds stream Phase 1 and emitted JSONL. Their retained state is one current
row, the complete text-free locator map, aggregate counters, source/work pair
counts, and locator references per source needed to construct the worklist.
They do not retain source text or all Phase 1 rows.

## Production receipt

The complete 2026-08-03 build reconciled all 189,150 Phase 1 records and 42,302
source/work locators. The locator comprises 3,309 literary, 36,759 textbook,
1,205 external-article, and 1,029 Wikipedia mappings. The capability worklist
contains 3,511 source-level evidence tasks.

The compact locator contains 42,302 semantic records and 42,303 physical
lines including its header. It is 16,560,805 bytes with SHA-256
`9941d3e7deffb2d05934aa36b6381ca6e0ad1744f20996a97d4135af902382e2`.
Strict expansion produces 32,991,831 bytes of canonical full-object JSONL with
semantic SHA-256
`1d3f85ae6bb4241b9691c18cf855ec71e3e2ab7c97d18bf52e522f9d2ae07a60`.

Current evidence routes 1,029 Wikipedia rows to faithful `candidate` for local
preparation and local model learning. It routes the other 188,121 records to
`metadata_only` for those capabilities; that means evidence remains unresolved,
not that the records are linguistically defective or permanently unusable. All
189,150 rows remain `metadata_only` for raw or derived redistribution, dataset
publication, and model publication. Phase 2 makes no loss-masked or protected
linguistic classification.

Two complete builds were byte-identical. The independent verifier rebuilt the
bundle and matched every byte. The full-corpus source-blind filter returned the
same 1,029 evidenced faithful candidates. The committed receipt binds the local
958,068,153-byte complement and 67,845,464-byte worklist; those two material
artifacts remain local and are not publication payloads.

| Run | Wall time | Maximum RSS | Peak memory footprint |
| --- | ---: | ---: | ---: |
| Complete build 1 | 340.48 s | 378,830,848 bytes | 352,797,344 bytes |
| Complete build 2 | 336.50 s | 386,531,328 bytes | 352,830,112 bytes |
| Independent rebuild verifier | 340.04 s | 2,106,720,256 bytes | 2,114,816,040 bytes |

The complement SHA-256 is
`3f0a1458fcf9380a679237f6cfb2915c58d2c33c3764fcb25d63b6e7aa6254e0`;
the worklist SHA-256 is
`a60321052721231b5828b604ec098064271d42a2afc4dcb91f968e90f0d60b0a`;
and the 32,380-byte committed receipt SHA-256 is
`12308712b6022557c5da6f3bb76cacbe21738c9c53e5ce97b8b4a6c28f353c4b`.
The 1,029-row source-blind candidate view is 5,437,809 bytes with SHA-256
`d885a6c9fc4877d658b87f9c9e44347a36d80f161c303a165af5da9454d0b365`;
it contains no source text, local path, or evaluation fingerprint.
The builder uses atomic temporary files rather than a SQLite spool. Budget at
least 2.5 GB of free local disk for the bound Phase 1 inputs, existing outputs,
and one complete staged or verifier rebuild, excluding the source databases
needed to regenerate Phase 1 and the locator.

Receipt `coverage.by_period` preserves Phase 1's declared historical-period
dimension; it is not a linguistic verdict. `coverage.by_textbook_grade` reports
the exact grade balance, while `route_totals` and `representation_totals` make
the capability and representation decisions auditable without reading text.

This process neither generates a production corpus nor runs a model. The next
rights-resolution canary is the 52-row Wikisource per-page packet, followed by
work/edition resolution for materially useful literary strata. The next
linguistic phase is separate: authoritative clean-Ukrainian correction and
protection evidence, not automatic normalization of historical, dialectal,
regional, quoted, or language-contact material.
