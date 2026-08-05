# Phase 3: evidence-graded correction and protection contracts

> **Recovery status:** these contracts and their current engine satisfy
> `ENGINE_READY` only. The public authored canaries are regression fixtures,
> not an independent held-out set, and the Phase 2 stand-off inventory is not a
> linguistic denominator. Issue #6375 owns the remaining source-coverage,
> linguistic-validation, and consumer-proof gates; Phase 4 is blocked.

[Українська версія](PHASE3_CONTRACTS.uk.md)

Phase 3 adds a model-neutral, evidence-graded product lane for Ukrainian
correction and non-erasure decisions. It does not create human gold and does
not alter the existing qualified-human correction lane.

Every Phase 3 case uses one terminal disposition:

- `correct` — an acceptable control that must remain unchanged;
- `correction` — a non-authoritative proposal that passed its frozen category
  gate;
- `protected` — a context that must not be normalized by the released rule;
- `excluded` — material outside a learning or correction view; or
- `unresolved` — a valid terminal abstention.

The assurance tier is not implied by those words. Every record and consumer
view carries the schema-enforced constants
`assurance_tier: evidence_graded_non_gold` and `authoritative: false`.
Phase 3 case identifiers use the separate `cp_case:` namespace and can never
be parsed as `correction_record_v1` human-gold records.

## Evidence and source boundary

Evidence channels remain separate. VESUM supports morphological attestation
or non-attestation; R2U and Russian morphology support Russian-form evidence;
ULIF, named heritage dictionaries, LanguageTool, `nlp_uk`, corpus context, and
model proposals retain their own identities, versions, locators, parser
receipts, and limitations. A single model vote or a VESUM miss cannot create a
`correction` disposition.

Original source text is immutable. Public records contain source text only
when the exact source and exact publication capability are evidenced.
Otherwise the release uses stand-off data: revision-pinned locators, offsets,
hashes, source/work identity, evidence, and reproduction code. Project-authored
canaries identify their provenance explicitly.

Phase 2 remains the capability source of truth. Its current public policy
routes 1,029 Wikipedia records to local preparation and local model learning,
but all 189,150 records remain metadata-only for raw redistribution, derived
redistribution, dataset publication, and model publication. Phase 3 therefore
does not infer publication rights from local-learning evidence.

## Frozen VESUM-unattested sample

The first production evidence is a deterministic source-stratified sample of
the exact 9,292,022 VESUM-unattested token occurrences recorded by the full
corpus profile. The sampler:

1. streams the four eligible source families from read-only SQLite;
2. reproduces the profile's normalization and VESUM interface;
3. allocates a fixed family quota across period, genre, and register strata by
   deterministic largest-remainder allocation;
4. ranks occurrences by a domain-separated SHA-256 identity; and
5. emits text-free records in stable order.

Each selected occurrence is routed to one evidence bucket:
`ocr_or_noise`, `proper_name`, `historical_orthography`,
`foreign_or_russian_quotation`, `phonetic_russian`,
`plausible_modern_ukrainian_error`, `legitimate_ukrainian_variation`, or
`unresolved`. These are evidence-graded sample routes, not error labels. The
aggregate unknown-token count is never used as a linguistic disposition.

The committed config freezes the sample size, per-family quotas, axes,
identity algorithm, input pins, no-text rule, and held-back storage boundary.
The receipt binds the exact denominator, input hashes, category counts,
coverage, output bytes/hash, and a comparison against a distinct first-build
artifact.

## Incumbent-tool delta

The checked-in ecosystem manifest pins the inspected LanguageTool Ukrainian,
`nlp_uk`, and VESUM revisions and separately records the bounded R2U and ULIF
web-interface observations. Phase 3 supplements these tools; it does not claim
to replace them or to cover every feature they may have.

The measurable delta is per-case evidence provenance plus policy-driven
`protected` and `unresolved` outcomes. Tool output remains diagnostic evidence:
a match, no-match, dictionary hit, or dictionary non-hit does not by itself
prove a Ukrainian form correct or incorrect.

## Frozen category gates

The category-gate config is committed before any Phase 3 case factory runs.
Each category declares its consumer decision, minimum source-backed cases and
controls, protected-class requirements, allowed dispositions, and no-go
conditions. A failed gate remains `research_only`; the category still appears
in coverage and non-erasure evaluation but cannot emit released corrections.

The mandatory source-blind canary is a three-way project-authored corpus:

1. `Фраза звучит значно вишуканіше.` in narration must be flagged as Russian
   finite morphology;
2. the same form inside a marked Russian quotation must be protected; and
3. a VESUM-attested modern-Ukrainian control must remain unchanged.

Phase 3 adds boundary mutations around the quotation case. The public examples
are regression canaries, not a leakage-resistant heldout set. Held-back
selection evidence lives only in the configured ignored private store, outside
the public repository.

## Reproduction boundary

Consumers need the repository's pinned Python environment, the local Phase 1
manifest under `batch_state/issue-6327/phase1-production/`,
`data/sources.db`, and `data/vesum.db`. The production command is:

```bash
.venv/bin/python scripts/projects/open_model_data/vesum_unattested_sample.py candidate \
  --config data/projects/open_model_data/profiles/vesum_unattested_sample_config_v1.json \
  --profile data/projects/open_model_data/profiles/public_external_full_corpus_v1.json \
  --profile-receipt data/projects/open_model_data/profiles/full_corpus_profile_v1.json \
  --phase1-manifest batch_state/issue-6327/phase1-production/document_signal_manifest.jsonl \
  --phase1-receipt batch_state/issue-6327/phase1-production/document_signal_receipt.json \
  --source-database data/sources.db --vesum-database data/vesum.db \
  --detector-config data/projects/open_model_data/detector/language_contact_config_v1.json \
  --output batch_state/issue-6333/first-build.jsonl

.venv/bin/python scripts/projects/open_model_data/vesum_unattested_sample.py build \
  --config data/projects/open_model_data/profiles/vesum_unattested_sample_config_v1.json \
  --profile data/projects/open_model_data/profiles/public_external_full_corpus_v1.json \
  --profile-receipt data/projects/open_model_data/profiles/full_corpus_profile_v1.json \
  --phase1-manifest batch_state/issue-6327/phase1-production/document_signal_manifest.jsonl \
  --phase1-receipt batch_state/issue-6327/phase1-production/document_signal_receipt.json \
  --source-database data/sources.db --vesum-database data/vesum.db \
  --detector-config data/projects/open_model_data/detector/language_contact_config_v1.json \
  --comparison-output batch_state/issue-6333/first-build.jsonl \
  --output data/projects/open_model_data/profiles/vesum_unattested_sample_v1.jsonl \
  --receipt data/projects/open_model_data/profiles/vesum_unattested_sample_receipt_v1.json
```

The production build was executed twice from the databases. The second build
matched the independent first-build artifact byte-for-byte before the receipt
was written. The verified result is 256 records, 64 for
each of `external_articles`, `literary`, `public_textbooks`, and `wikipedia`:

- output SHA-256:
  `a8d2ed4f8ef2170e27bd52cc4e9d475efa5261fec7e6f822703bf9340630b414`;
- receipt SHA-256:
  `54f6af17bcc862505966d35db82f27e2042cf4e211eaced9bfaf297917cfe872`;
- routes: 200 `unresolved`, 26 `foreign_or_russian_quotation`, 20
  `legitimate_ukrainian_variation`, four `historical_orthography`, four
  `plausible_modern_ukrainian_error`, one `ocr_or_noise`, and one
  `proper_name`.

The command reads both databases in read-only mode. No training, model
download, accelerator work, upload, or external data publication occurs.
