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
resolved review, and operation-specific rights:

| Operation | Required granted rights |
| --- | --- |
| `local_learning` (default) | copyright, license, model_training |
| `deterministic_local_analysis` | copyright, license, model_training |
| `public_redistribution` | copyright, license, model_training, redistribution |

These operations concern model-consumer views. Private local admission accepts
unknown, conflicting, or denied redistribution permission; it does not alter
that permission or authorize publication. Public model-view export always
recomputes admission from the exact source record and requires redistribution.
Existing reviewed evidence in each record's `rights` resolves the applicable
permission; no new approval document or blanket source re-verification is
required. Source-specific exclusions remain binding.
It also invokes `Draft202012Validator.check_schema` before use and requires a
granted license to carry the exact-terms receipt described above. Evidence IDs
must be unique within a record so that array order cannot change which receipt
is resolved. Acquisition and evidence locations must be absolute HTTP(S) URLs
without embedded credentials; admission checks this directly and does not
depend on optional JSON Schema format packages.
`unknown`, `conflicting`, or `denied` status for a required right fails closed. This is an admission
rule, not a claim that a grant is legally sufficient.

`evaluation_only` is always rejected for training/export admission, regardless
of its other fields. `excluded` and records with contamination exclusion IDs are likewise rejected. The validator returns
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
For a mixed JSON list, the receipt reports separate contract and legacy counts
and retains each per-record disposition; only an all-legacy input suppresses
record-level output. A zero-record input is labeled `empty`, not contract
conformant.


## Private human-source build and export (#7888)

The active path is `source_record_v1` plus a reviewed
`foundry_source_payload_v1`, consumed by `model_view_exporter`. Dataset source
text must be human-authored. STEM, video captions/transcripts, OCR-derived text,
and private teaching material remain excluded; preserve the established
source-specific exclusions and evidence. Explicit `source_family` or genre
classifications `stem`, `video_captions`, `video_transcripts`, `ocr`, `ocr_derived`,
and `private_teaching_material` are denied. Other source-specific exclusions use
`usage.role: excluded`; the validator does not guess topic or acquisition method
from prose. The former V4 original-row factory is
stopped, and zero existing AI candidates are admitted. Its 100-slot denominator
and non-reconstruction checks are historical, not requirements for this path.

Prepare payloads from the exact human source bytes under the existing approved
custody and source review. Bind `source_record_id`, the source content hash,
origin evidence, normalization, privacy and language-span receipts. A
`full_source` payload must hash to its source record; a `character_span` retains
its exact source offsets and derivation receipt. Do not overwrite source text
with model annotations or corrections. Review/split clearance and the frozen
evaluation exclusion registry remain required; model annotations are separate
correction handoffs. Consumer masks affect loss, never the source bytes.

The optional materializer accepts existing full-source reviewed payload metadata
with `text` and `text_sha256` omitted (or already exactly matching). It fills
only those two fields from UTF-8 source bytes, including original line endings;
all source identity, hashes, rights and review evidence must already be supplied.
It refuses invalid metadata and leaves an existing destination unchanged.

```bash
$VENV/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  materialize-human-source --source-records /approved-custody/source-records.jsonl \
  --reviewed-payload /approved-custody/reviewed-metadata.json \
  --source-text /approved-custody/source.txt --output /approved-custody/reviewed-human-payloads.jsonl
$VENV/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  continued-pretraining --source-records /approved-custody/source-records.jsonl \
  --payloads /approved-custody/reviewed-human-payloads.jsonl --origin human_authored \
  --representation-view faithful_literary --operation local_learning \
  --output /approved-custody/local-view.jsonl --receipt-output /approved-custody/local-receipt.json
```

`--operation public_redistribution` additionally checks redistribution permission;
it still writes only a local artifact and never publishes. Every new receipt
names its admission operation. A local-learning receipt or row eligibility flag
is not publication authority: rerun the public operation against the exact
source records and reviewed payloads. An older receipt without an operation
must not be interpreted as publication permission.

Machine-origin structural fixtures require explicit fixture mode and remain
ineligible for training. The CLI integration test
`tests/projects/open_model_data/test_v4_human_source_admission.py` verifies one
cited human-authored excerpt reaches local output reproducibly, using controlled
permission/review test doubles. It proves software behavior, not admission or
release of the private corpus. The dataset/source steward retains responsibility
for the real input records and their established permissions and clearances.
