# Ukrainian Data Foundry corpus admission

`admit_existing_corpus.py` turns the existing public/external denominator into
a local, content-blind row manifest and a portable aggregate receipt. It is an
admission-disposition step, never training, publication, acquisition, OCR, or
rights certification.

## Inputs and boundaries

The checked-in configuration is
`data/projects/open_model_data/admission/public_external_full_corpus_admission_v1.json`.
It binds the four public/external families to the frozen profile denominator:
189,150 rows and 50,298,925 lexical words. Its current evidence state is
intentionally unresolved: a public location, corpus membership, author death,
or a family name is not permission.

The runner reads `data/sources.db` in SQLite read-only/query-only mode. It
keeps source text in process only for lexical-word counting and the frozen
evaluation exact/near-contamination registry. The JSONL manifest has opaque
hash-derived record/source/work IDs, attributes, disposition, and word count;
it has no source text, raw URL, or absolute path. Keep that potentially large
manifest local and uncommitted.

## Run

Run from the repository worktree with the real read-only databases available:

```bash
.venv/bin/python scripts/projects/open_model_data/admit_existing_corpus.py \
  --manifest-output batch_state/public_external_admission_manifest_v1.jsonl \
  --receipt-output batch_state/public_external_admission_receipt_v1.json \
  --runtime-output batch_state/public_external_admission_runtime_v1.json
```

Repeat the command with distinct output names and compare the manifest and
receipt hashes. Runtime is deliberately separate because it is not a
deterministic content receipt. Exit status `0` means exact denominator
reconciliation; `2` means inaccessible input or an expected/actual mismatch.
An incomplete receipt still records the full expected denominator and writes
an empty local manifest, rather than silently reducing coverage.

## Dispositions and the human gate

Every processed row is exactly one of `proposed_admission`,
`investigation_only`, `excluded`, or `unresolved`.

- Missing provenance, acquisition, snapshot, rights, origin, or contamination
  evidence produces `unresolved`.
- Any exact or near evaluation match is `excluded`.
- Complete evidence with an explicit destination can be
  `proposed_admission`, but the runner always writes
  `training_eligible_emitted: false`.

The operator packet at
`data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json`
lists the current evidence gaps and the only accept/reject choices. Operator
acceptance is a separate source-family gate; it does not authorize an export,
training run, redistribution, or publication.
