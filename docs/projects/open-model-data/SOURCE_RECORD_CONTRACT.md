# Source record v1 contract

## Status and boundary

This is a reusable, fail-closed provenance admission contract. It freezes a
schema and validator only. It does not rebuild, clean, copy, upload, publish,
export, train on, or release any dataset. It does not adjudicate legal rights.

The [Literary Poltava candidate audit](../../research/hramatka_literary_poltava_candidate_audit.md)
documents why the earlier 5,000-record candidate fails: external source
identity, edition, acquisition, rights, redistribution, training-permission,
translation-origin, region, and register evidence are missing. The validator
can report those established gaps without reading records into output or
asserting a legal conclusion.

## Record shape

`source_record_v1.schema.json` is a Draft 2020-12 JSON Schema. A record has
stable `record_id`, `work_id`, and `source_id`; acquisition receipt and catalog
URL; bibliographic edition/editor/publisher/translation origin; descriptive
author/date/period/genre/register/region fields; a content SHA-256 and
derivation lineage; evidence citations with retrieval dates; review identity,
qualification, confidence, and unresolved state; plus a usage role and
contamination exclusions.

Each copyright, license, redistribution, and model-training statement records
a status, jurisdiction, cited evidence IDs, and whether a legal conclusion is
asserted. A granted license additionally requires a precise identifier or
expression and an exact-terms evidence ID. That cited evidence must have a
canonical terms/source URL, retrieval date, and SHA-256 receipt of the
retrieved terms. Unknown, conflicting, and denied licenses keep these fields
nullable rather than fabricating terms. The supplied synthetic example uses
`not_asserted`: evidence is recorded, but the contract itself makes no legal
conclusion.

## Admission semantics

JSON Schema validates structure. The validator additionally requires the
current schema hash, complete derivation consistency, referenced evidence, a
resolved review, and `granted` status for all four rights/permission fields.
It also invokes `Draft202012Validator.check_schema` before use and requires a
granted license to carry the exact-terms receipt described above.
`unknown`, `conflicting`, or `denied` status fails closed. This is an admission
rule, not a claim that a grant is legally sufficient.

`evaluation_only` is always rejected for training/export admission, regardless
of its other fields. `excluded` is likewise rejected. The validator returns
canonical sorted JSON containing only record IDs, aggregate counts, hashes, and
reason codes; it does not emit content or create output artifacts.

## Use

Use the repository Python interpreter in check-only mode:

```bash
.venv/bin/python scripts/projects/open_model_data/validate_source_records.py \
  data/projects/open_model_data/contracts/source_record_v1.example.json
```

The tracked example is synthetic and clearly marked as such. It is a schema and
admission fixture, not source data or a release artifact. A supplied legacy
JSONL candidate is classified as non-contract input and receives deterministic
aggregate fail-closed reasons for the ten previously evidenced missing fields.
