# Phase 3 correction and protection product

> **Recovery status:** the artifacts documented here are the historical
> `ENGINE_READY` engine/seed release from #6333, not a completed Phase 3
> linguistic product. Its 9/9 benchmark reuses authored public canaries that
> produced five literal correction patterns; it is regression evidence, not
> independent linguistic validation. The 189,150 Phase 2 stand-off rows are
> metadata dispositions and do not count as correction coverage. Recovery
> continues under #6375 until `SOURCE_COVERAGE_READY`,
> `LINGUISTICALLY_VALIDATED`, and `CONSUMER_PROVEN` join `ENGINE_READY` on
> merged `origin/main`. Phase 4 remains blocked.

The historical release ships a directly runnable, model-neutral Ukrainian
correction and protection engine. It does not train a project model and it is
not human gold.
Every record says `assurance_tier: evidence_graded_non_gold` and
`authoritative: false`.

The product enables five concrete decisions:

- **correction** — propose a reversible, evidence-backed change;
- **filtering** — retain, exclude, or abstain without editing the source;
- **preference** — prefer a proposed form while preserving the original;
- **protection** — retain quoted, historical, dialectal, regional, heritage,
  folklore, or contested material; and
- **abstention** — withhold a case when the released evidence or gate is not
  strong enough.

The public files are in
`data/projects/open_model_data/release/correction_protection_v1/`.

## What is released

The full reproducible bundle covers 189,249 cases derived from the complete
189,150-row Phase 2 complement plus 99 public known-answer cases:

| Disposition | Count |
| --- | ---: |
| `correction` | 9 |
| `correct` | 17 |
| `protected` | 30,409 |
| `excluded` | 0 |
| `unresolved` | 158,814 |

Only the nine public positives pass a correction gate: five Russian finite
`звучит` narration cases and four contextual calque/collocation cases. The
other Phase 2 records remain source-blind stand-off candidates, protected
records, or terminal unresolved cases. An unknown token, Russian-looking
string, model vote, or VESUM absence is never converted automatically into an
error.

The public product contains 99 project-authored cases, 245 separately
attributed evidence records, four model-disagreement records, and 194
model-neutral views. These public cases are frozen canaries and are always
`learning_eligible: false`.

## Category gates

All eight required categories have acceptable controls and protected examples.
The release mode is deliberately different by category:

| Category | Gate | Correction release |
| --- | --- | --- |
| Russian lexical/inflectional intrusion | passed | allowed for five positives |
| Contextual calque, government, valency | passed | allowed for four positives |
| Modern literary Ukrainian control | passed | no correction rule |
| Marked Russian quotation/code-switching | passed | protection only |
| Phonetic Russian in literature | passed | protection only |
| Historical/archaic Ukrainian | passed | protection only |
| Dialect/regional/heritage/folklore | passed | protection only |
| Surzhyk/contested contact | research-only | no correction rule |

The frozen threshold hash is
`e65c6b528610a143d37abeb08e276b214612a7bf62ce7c90b5db91ba826a0d82`.
A failed category remains research-only; the implementation does not lower a
threshold to obtain more rows. The gate verifies every named required canary,
measures protected/control false corrections separately against their frozen
zero caps, and permits only the dispositions declared for that category.

## Mandatory `звучит` behavior

The consumer recipe detects the Russian finite form in Ukrainian narration:

```text
Фраза звучит значно вишуканіше.
```

It proposes `звучить` reversibly. The same occurrence inside a paired quote,
dash dialogue, or explicit `<ru>...</ru>` boundary produces a protection view,
not a correction. Token boundaries are mandatory, so `звучит` cannot match the
correct Ukrainian form `звучить` as a prefix.

The public non-erasure harness freezes 9/9 correction detections, 37/37
acceptable controls preserved, and 53/53 protected examples preserved.

## Apply the recipe to a consumer-controlled corpus

Prepare UTF-8 JSONL with a unique `id` and `text` per row:

```json
{"id":"narration","text":"Фраза звучит значно вишуканіше."}
{"id":"quotation","text":"Автор навів: «Фраза звучит значно вишуканіше.»"}
{"id":"unknown","text":"Цей запис не відповідає жодному випущеному правилу."}
```

Run the source-blind recipe:

```bash
.venv/bin/python -m scripts.projects.open_model_data.correction_protection_consumer apply \
  --input /path/to/consumer.jsonl \
  --output-dir /path/to/phase3-output
```

The output directory contains separate `correction.jsonl`, `filtering.jsonl`,
`preference.jsonl`, `protection.jsonl`, and `abstention.jsonl` files plus a run
receipt. Input bytes are never changed. Records unmatched by a released rule
go to abstention.

Learning eligibility fails closed. By default every result has
`learning_eligible: false`. A consumer may add `--authorize-local-learning`
only for a corpus it controls and has independently authorized for local model
learning. Even with that flag, an exact or near match to either frozen
evaluation registry is emitted only as `excluded` with
`learning_eligible: false`.

The command performs no training, model inference, accelerator work, upload,
or publication.

## Run and verify the non-erasure harness

```bash
.venv/bin/python -m scripts.projects.open_model_data.correction_protection_consumer benchmark \
  --output /tmp/phase3-non-erasure.json

.venv/bin/python -m scripts.projects.open_model_data.correction_protection_consumer verify
```

Public canaries are visible by design and are not a held-back equivalent. A
post-publication held-back packet stays outside the repository at
`batch_state/issue-6333/heldback/phase3-v1`. An operator can supply it with both
`--heldback` and `--heldback-sha256`; a missing or mismatched hash fails closed.
The public release does not depend on qualified human review and makes no claim
that the private packet is human gold.

## Reproduce the factory and public release

The two full factory builds use distinct output roots and the complete Phase 2
complement. The second command refuses to issue a release receipt unless every
artifact hash matches the first build.

```bash
.venv/bin/python -m scripts.projects.open_model_data.correction_protection_factory candidate \
  --phase2-input batch_state/issue-6327/phase2-production/complement.jsonl \
  --phase2-receipt batch_state/issue-6327/phase2-production/receipt.json \
  --model-evidence data/projects/open_model_data/evidence/correction_protection_model_lanes_v1.json \
  --full-output-dir batch_state/issue-6333/rebuild-1/full \
  --public-output-dir batch_state/issue-6333/rebuild-1/public \
  --index-output batch_state/issue-6333/rebuild-1/build-index.json

.venv/bin/python -m scripts.projects.open_model_data.correction_protection_factory build \
  --phase2-input batch_state/issue-6327/phase2-production/complement.jsonl \
  --phase2-receipt batch_state/issue-6327/phase2-production/receipt.json \
  --model-evidence data/projects/open_model_data/evidence/correction_protection_model_lanes_v1.json \
  --full-output-dir batch_state/issue-6333/rebuild-2/full \
  --public-output-dir batch_state/issue-6333/rebuild-2/public \
  --index-output batch_state/issue-6333/rebuild-2/build-index.json \
  --comparison-index batch_state/issue-6333/rebuild-1/build-index.json \
  --comparison-full-output-dir batch_state/issue-6333/rebuild-1/full \
  --manifest-output /tmp/phase3-bundle-manifest.json \
  --receipt-output /tmp/phase3-release-receipt.json

.venv/bin/python -m scripts.projects.open_model_data.correction_protection_consumer build-release \
  --factory-public-dir batch_state/issue-6333/rebuild-2/public \
  --output-dir /tmp/phase3-public-release
```

The byte-identical build-index SHA-256 is
`5d0d9c29d16a71995d1a8af1c813291f9ba6d476ccd6dcc90d3b4419ed8b6945`.
The public consumer receipt is
`cp_consumer_receipt:61fc91ca581c3f4051bde42b702ddbdc2a5d5c63fbbd8cf17119a8e864eeb89a`.

## Evidence and claim boundaries

Evidence channels stay separate:

- VESUM means morphological attestation or non-attestation only;
- R2U and Russian morphology mean Russian-form evidence only;
- cached ULIF `dictua` evidence retains parser and raw-response hashes;
- `slovnyk.me` cannot strengthen a disposition without a named contributing
  dictionary;
- corpus, source/work, period, genre, register, quotation, and heritage
  evidence provide context; and
- Ukrainian-strong models provide attributed proposals and dissent, never
  authority or gold.

The clean Grok lane is retained with exact model ID, proposal, dissent, prompt
hash, and raw-response hash. A Gemini lane with corrupted Ukrainian output is
retained as failed and cannot strengthen a gate. Model agreement is not human
review.

The full source families publish revision-pinned, text-free stand-off records.
Only the 99 project-authored short canaries include source context, under their
explicit publication capability. See the source-family datasheet for exact
family boundaries.

## Limitations

- This is a small high-precision correction seed plus a large conservative
  stand-off/protection product, not a claim that all Ukrainian errors are
  covered.
- Source metadata alone cannot decide a span-level correction; 158,814 cases
  therefore remain terminal unresolved.
- Surzhyk is sociolinguistically and contextually contested and remains
  research-only.
- Public canaries cannot measure post-publication memorization. Use a separately
  hashed held-back refresh for that purpose.
- External adoption, model quality gains, and qualified-human gold are not
  claimed.
