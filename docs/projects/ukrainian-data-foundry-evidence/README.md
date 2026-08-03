# Ukrainian Data Foundry: Document Signals v0

Document Signals v0 is a deterministic, text-free evidence layer over the
project's complete public/external human-authored inventory. It helps a data
team inspect provenance readiness, corpus strata, duplicate candidates,
normalization, script mixture, repeated technical text, and evaluation overlap
before it creates a learning view.

It does not decide whether a sentence is good Ukrainian. It does not admit,
rewrite, delete, redistribute, publish, or train on any source record.

For the Ukrainian version, see [README.uk.md](README.uk.md).

## Measured production result

The production build covered all 189,150 records and all four source families:

| Source family | Records | Current family disposition |
| --- | ---: | --- |
| Literature | 137,723 | unresolved |
| Grade 1–11 public textbooks | 49,193 | unresolved |
| External articles and transcripts | 1,205 | unresolved |
| Ukrainian Wikipedia | 1,029 | admitted at the source-family gate |

The local JSONL contains 189,150 text-free rows and is 398,912,001 bytes. Two
complete builds were byte-identical:

- manifest SHA-256: `c730f57228514141a0253372e54a6f9aa56ffcdfe282d17aa385f843db1913c6`;
- receipt SHA-256: `dcb766f2cede81eedac90842ba44d5ec69426826d52c071a55b6c86e0f55def9`;
- measured wall times: 358.19 and 358.71 seconds; and
- measured maximum resident-set sizes: 181,682,176 and 188,203,008 bytes.

The committed aggregate receipt is
[`document_signal_receipt_v1.json`](../../../data/projects/open_model_data/evidence/document_signal_receipt_v1.json).
The large manifest remains a local reproducible artifact. Neither artifact
contains source text, but content hashes can support membership-confirmation
attacks when an attacker already possesses candidate text. “Text-free” is not
an anonymity guarantee and does not itself authorize publication.

## What the aggregate signals mean

The production receipt reports:

| Signal | Records or groups | Meaning |
| --- | ---: | --- |
| Exact duplicate records | 19,560 records in 9,147 groups | Exact source-byte SHA-256 repeats; no row was removed |
| Cyrillic and ASCII Latin in one record | 79,050 | Descriptive script-mixture signal, often explained by URLs, citations, names, or technical material |
| Ukrainian-specific and Russian-specific letters in one record | 32,779 | Orthographic-contact signal only; not a Russian-language or error verdict |
| NFC change | 859 | Unicode canonical normalization would change the bytes |
| NFKC change | 64,121 | Unicode compatibility normalization would change the bytes |
| Unexpected control characters | 6,877 | Excludes ordinary line breaks, carriage returns, and tabs |
| Replacement character | 28 | At least one Unicode replacement character occurs |
| Repeated nonblank lines | 20,324 | Possible repeated template, header, footer, verse, refrain, or legitimate repetition |
| URL-like token | 1,681 | At least one deterministic URL pattern occurs |
| Held-out textual overlap | 0 | No match under the frozen exact/containment/shingle/character-sequence registry |

These counts are candidate evidence. For example, Russian-specific letters can
occur in a quotation, a bibliographic title, phonetic characterization, or
historical material. Repeated lines can be website chrome, but they can also be
a refrain or intentional literary structure. Consumers must retain the source
period, genre, register, and origin dimensions when reviewing them.

The held-out result covers the frozen textual matching algorithms listed in
the receipt. It does not prove the absence of translated, paraphrased, or
semantic evaluation leakage.

## Record contract

Each JSONL row contains only evidence and opaque identifiers:

- stable `record_id`, `source_id`, and `work_id` values;
- exact `content_sha256` for the source bytes;
- source family and inventory asset identity;
- period, genre, register, and origin dimensions;
- admission evidence for provenance, acquisition, snapshot, rights, origin,
  and contamination;
- separate capability evidence for raw-text redistribution, local model
  learning, model training, and dataset publication;
- deterministic length, script, normalization, and repeated-text signals;
- exact-duplicate group and count;
- an eight-band approximate near-duplicate candidate fingerprint; and
- held-out evaluation-overlap state and matching method.

Every downstream capability is deliberately
`not_decided_by_document_signal_manifest`. Wikipedia's family-level admission
is preserved, but the manifest does not turn that admission into permission to
redistribute text, train, or publish a dataset. The existing capability-specific
rights gate must make those decisions.

## Build and verify

Run from a checkout that has the local `data/sources.db` corpus database:

```bash
mkdir -p batch_state/document-signals

.venv/bin/python scripts/projects/open_model_data/document_signal_manifest.py \
  --config data/projects/open_model_data/evidence/document_signal_config_v1.json \
  --input-root . \
  --manifest-output batch_state/document-signals/document_signal_manifest_v1.jsonl \
  --receipt-output batch_state/document-signals/document_signal_receipt_v1.json
```

Verify an existing pair without reading the source database:

```bash
.venv/bin/python scripts/projects/open_model_data/document_signal_manifest.py \
  --verify-existing \
  --manifest-output batch_state/document-signals/document_signal_manifest_v1.jsonl \
  --receipt-output batch_state/document-signals/document_signal_receipt_v1.json
```

The build reads SQLite with `mode=ro` and `PRAGMA query_only=ON`, uses a bounded
SQLite spool for exact duplicate counts, streams the manifest to a staged file,
and promotes the manifest/receipt pair only after complete coverage and strict
schema validation. An incomplete family or failed row leaves no accepted
output pair.

## How a model team should use it

1. Reproduce the manifest and verify the hashes and complete denominator.
2. Choose the intended capability: local analysis, local learning, training,
   raw-text redistribution, or dataset publication. Resolve that capability's
   rights evidence separately; do not infer it from linguistic signals.
3. Select source families and strata explicitly. Report period, genre,
   register, origin, and family balance rather than describing all rows as
   generic “Ukrainian data.”
4. Group exact duplicate IDs. Use shared approximate bands only to create a
   candidate queue, then calculate or inspect pairwise similarity in context.
5. Investigate normalization, script, control-character, replacement-character,
   and repeated-line candidates. Preserve quotations, literature, historical
   language, dialect, heritage language, and marked register.
6. Re-run the held-out firewall after every transformation. New or derived text
   can create contamination even when the source row was clear.
7. Export a learning view only through the capability-specific Foundry gate,
   with a new receipt binding the exact source rows, transformation, exclusions,
   obligations, and output hash.

This sequence supports a model-neutral prepared-data recipe. It does not ask a
team to trust this project, a language model, or a composite quality score.

## Deliberate limitations

- Letter and script counts are not language identification.
- VESUM attestation and dictionary lookup are not contextual correctness.
- Approximate bands are candidate-generation evidence, not duplicate verdicts.
- Boilerplate signals do not distinguish technical repetition from literary
  repetition.
- Textual contamination checks do not detect semantic or translated leakage.
- No source-family admission or signal automatically creates a training row.
- No model, classifier, accelerator, paid compute, upload, or outreach was used
  to produce this evidence layer.

The next program phase is capability-specific rights resolution and the first
rights-gated, stratified continued-pretraining complement. Contextual
clean-Ukrainian correction and protection data follows on a separate lane that
requires authoritative lexical evidence and Ukrainian-strong linguistic
review.
