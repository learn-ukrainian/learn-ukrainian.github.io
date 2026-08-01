# Ukrainian Data Foundry Correction Factory

> **Owner:** [#6121](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6121)
> under [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
> **Boundary:** review intake and adjudication, not model-ready export

## What this component produces

The correction factory takes span-aware, unresolved candidates from a local
detector or enrichment stage and produces two deterministic artifacts:

1. a review packet that preserves the original bounded context, offsets,
   language/representation/discourse axes, source-specific evidence, and
   separate view dispositions; and
2. an adjudicated correction record that preserves the complete candidate and
   qualified-human decision while remaining ineligible for training or export.

The component does not infer corrections. A detector, VESUM miss, Russian
morphology result, `r2u` hit, dictionary result, exact mismatch, or model vote
remains evidence until the qualified-human review contract is satisfied.

## Contracts

| Interface | Contract |
| --- | --- |
| Unresolved span candidate | `correction_candidate_v1.schema.json` |
| Qualified reviewer decision | `correction_reviewer_decision_v1.schema.json` |
| Adjudicated record | `correction_record_v1.schema.json` |
| Deterministic receipt | `correction_factory_receipt_v1.schema.json` |

All contracts are in `data/projects/open_model_data/contracts/`. The runtime
validates the schemas before writing output and replaces existing artifacts
only after all rows and receipts pass validation.

## Prepare a review packet

Run from the repository root with local, non-published paths:

```bash
.venv/bin/python scripts/projects/open_model_data/correction_factory.py prepare \
  --candidates /local/path/correction-candidates.jsonl \
  --packet-output /local/path/review-packet.jsonl \
  --receipt-output /local/path/review-packet.receipt.json
```

The command binds every candidate to the committed v0.1.1 held-out manifest
and v0.2 review packet. It recomputes exact and near-duplicate dispositions,
checks the frozen manifest/packet hashes, validates original text and offsets,
and rejects stale or falsely cleared contamination fields.

A candidate producer must supply:

- the upstream profiler candidate hash and profile identifier;
- bounded source context plus exact span offsets without rewriting the text;
- language identity, representation, discourse role, and proposed downstream
  disposition as independent axes;
- separate faithful, modern-Ukrainian, correction, preference, and evaluation
  view dispositions;
- source-specific lexical evidence with source identity, locator, period,
  register, parser status/version, content hash, and rights posture; and
- unresolved detector state with `automatic_error_label: false` and
  `model_output_used_as_gold: false`.

When VESUM does not attest a form, the packet must record completed routing to
ULIF, a heritage dictionary, one named underlying `slovnyk.me` dictionary, and
Ukrainian corpus context. Missing results are valid evidence; omitted routes
are not. `slovnyk.me` itself is never accepted as the dictionary identity.

Ukrainian-phonetic Russian requires a suspicious bounded span and at least one
preserved reconstruction. Each reconstruction records its gate,
transformation path, score, Russian morphology result, and `r2u` result. A
global character substitution is not an accepted input.

## Import adjudication

```bash
.venv/bin/python scripts/projects/open_model_data/correction_factory.py adjudicate \
  --packet /local/path/review-packet.jsonl \
  --decisions /local/path/reviewer-decisions.jsonl \
  --records-output /local/path/correction-records.jsonl \
  --receipt-output /local/path/correction-records.receipt.json
```

The decisions must be in exact packet order and carry the canonical candidate
hash. Two different qualified Ukrainian humans must make independent first
passes. Matching projections are preserved exactly. A conflict either remains
unresolved or is resolved by a third, distinct qualified Ukrainian human;
the final projection must equal that third review.

Synthetic reviewers are supported only by the explicit
`--allow-test-fixtures` test switch. They always add a safety blocker and can
never produce qualified correction intake.

## Fail-closed promotion

A record is marked `qualified_correction_intake: true` only when all of these
are true:

- the human final decision is `correction` and includes an accepted form;
- review is adjudicated through the required independent-human path;
- provenance and destination-specific rights are complete and granted;
- intended use and human/synthetic origin are known;
- private-data screening is clear;
- exact and near-duplicate checks are clear against both evaluation versions;
- no dictionary request is incomplete or in a parser/transient-error state;
- the span is not historical, heritage, dialectal, regional, archaic, rare,
  slang/marked, quoted Russian, multilingual, or otherwise protected; and
- no test-fixture reviewer participated.

Russian quotations and dialogue retain their source bytes in the faithful
view and are masked or excluded from modern-Ukrainian loss. Historical and
protected variation remains faithful/protected. The canonical source is never
silently translated or rewritten.

Every record still carries:

```json
{
  "model_training_or_export_eligible": false,
  "owner_issue": 6122
}
```

Issue #6122 implements that separate consumer boundary in the
[model-view and recipe runbook](ukrainian-data-foundry-model-views.md). Its
exporter revalidates rights, contamination, view separation, and this handoff;
it does not reinterpret an unresolved or protected record as correction data.
The upstream `model_training_or_export_eligible: false` remains unchanged.

## ULIF completeness

Parser version `ulif-dictua-v2` treats an exact DictUA headword match with a
complete WebForms/tab traversal as successful even when no inflection table
exists. This covers non-inflecting headwords that expose synonym or other
relation data. Missing WebForms state, a malformed result list, an interrupted
tab sequence, or a transient network failure still fails closed.

ULIF synonym evidence retains ordered sense groups, register labels,
citations, parser status/version, locator, and content hash. Raw HTML is not a
correction-packet field and remains non-exportable without permission.

## Required verification

```bash
.venv/bin/python -m pytest -q \
  tests/test_open_model_correction_factory.py \
  tests/test_ulif_dictua.py \
  tests/test_lexicon_runner_offline_reduce.py

.venv/bin/ruff check \
  scripts/projects/open_model_data/correction_factory.py \
  scripts/rag/source_query.py \
  scripts/lexicon/runner/ulif_dictua_parse.py \
  tests/test_open_model_correction_factory.py \
  tests/test_ulif_dictua.py \
  tests/test_lexicon_runner_offline_reduce.py
```

The focused regression suite covers Russian quotation and dash dialogue,
phonetic Russian, VESUM-presence ambiguity, historical protection,
`перекличка`, shared Ukrainian/Russian forms, ULIF completeness, per-dictionary
source identity, contamination and rights gates, deterministic bytes, and the
detector-not-gold boundary.
