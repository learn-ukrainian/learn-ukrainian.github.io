# Ukrainian Data Foundry corpus admission

`admit_existing_corpus.py` turns the existing public/external denominator into
a local, content-blind row manifest and a portable aggregate receipt. It is an
admission-disposition step, never training, publication, acquisition, OCR, or
rights certification.

## Inputs and boundaries

The checked-in configuration is
`data/projects/open_model_data/admission/public_external_full_corpus_admission_v1.json`.
It binds the four public/external families to the frozen profile denominator:
189,150 rows and 50,298,925 lexical words. A public location, corpus
membership, author death, or a family name is not permission. Three families
remain unresolved. On 2026-08-01, the operator accepted exactly the 1,029-row
Ukrainian Wikipedia family for the source-admission destination
`open_weight_ukrainian_continued_pretraining_text_v1`. The recorded acceptance
does not authorize payload export, training, upload, model release, dataset
redistribution, or publication.

The runner reads `data/sources.db` in SQLite read-only/query-only mode. It
keeps source text in process only for lexical-word counting and the frozen
evaluation exact/near-contamination registry. The JSONL manifest has opaque
hash-derived record/source/work IDs, attributes, disposition, and word count;
it has no source text, raw URL, or absolute path. The separate Wikipedia
source-record JSONL retains the canonical article URL, capture
date and timestamp, exact stored-text hash, acquisition-code receipt,
bibliographic identity, rights evidence, and contamination exclusion. It does
not contain article text or host paths. Keep both potentially large manifests
local and uncommitted.

## Sol advisor contract verdict

The frozen source-record contract permits this article-level captured
snapshot. A MediaWiki revision ID would improve upstream identity, but it is
not a contract requirement:

- `acquisition` requires `receipt_id`, `source_or_catalog_url`, and
  `retrieved_on`;
- `content` requires the exact `sha256` and a declared `hash_scope`;
- `derivation` records source/derived lineage; and
- each evidence receipt carries an ID, citation, URL, retrieval date, and
  SHA-256.

The schema has `additionalProperties: false` and contains no revision-ID
field. The contract prose likewise specifies an acquisition receipt and
catalog URL, content SHA-256, and derivation lineage; it does not prescribe a
Wikipedia dump or revision identifier. Each local record therefore binds the
captured bytes with its article URL, exact UTC capture timestamp in the
bibliographic edition identity, content SHA-256, and one acquisition-code
cohort. The acquisition `retrieved_on` remains the schema-prescribed date.

All four rights statements remain `legal_conclusion: not_asserted`. The
operational advisor finding is narrower: the primary terms expressly allow
reproduction, sharing, and adaptation for any purpose, including commercial
purposes, subject to attribution, share-alike, modification notice, license
notice, and no-additional-restrictions conditions. That supports a proposed
local continued-pretraining input view; it is not legal advice or a release
decision.

## Frozen primary evidence

The committed evidence packet is
`data/projects/open_model_data/admission/wikipedia_primary_rights_evidence_v1.json`.
The downloaded bodies remain local under `batch_state/`. Receipts were taken
on 2026-08-01.

| Primary evidence | Exact receipt URL | SHA-256 |
| --- | --- | --- |
| Ukrainian Wikipedia copyright/attribution policy, revision 47661434 | `https://uk.wikipedia.org/w/index.php?title=%D0%92%D1%96%D0%BA%D1%96%D0%BF%D0%B5%D0%B4%D1%96%D1%8F%3A%D0%90%D0%B2%D1%82%D0%BE%D1%80%D1%81%D1%8C%D0%BA%D1%96_%D0%BF%D1%80%D0%B0%D0%B2%D0%B0&oldid=47661434&action=raw` | `39a3ba4f3b106b1a03d4000fc77190e1eeaca5cb64044222c1294c049dbe7b70` |
| Wikimedia Terms of Use, controlling English revision 554852 | `https://foundation.wikimedia.org/w/index.php?title=Policy%3ATerms_of_Use%2Fen&oldid=554852&action=raw` | `bbb5ebfb89700c0e4732109cddbd45e6d8d2ba5dc339b206c7c5089ec4a4812b` |
| CC BY-SA 4.0 deed | `https://creativecommons.org/licenses/by-sa/4.0/deed.en` | `17de6b7071e8f4816b103fb45aff75f71c94821f303534fc3e21cb68bd0f7148` |
| CC BY-SA 4.0 legal code | `https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt` | `28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5` |
| CC BY-SA 3.0 deed cited by the local policy | `https://creativecommons.org/licenses/by-sa/3.0/deed.en` | `5d66bca8d914a4e7ce5ac18292ec69abc018f911578f685b7d86dac27607f535` |
| CC BY-SA 3.0 legal code cited by the local policy | `https://creativecommons.org/licenses/by-sa/3.0/legalcode` | `7e09ceffbcaa8dab3e66625f6264a7274912be272fc80e9cd94a29f94090b00c` |

The Ukrainian local policy still describes CC BY-SA 3.0 in its body while the
governing Terms identify CC BY-SA 4.0. The packet keeps that versioning
ambiguity explicit and retains article titles and URLs for the older
title-level attribution practice. Wikimedia also warns that imported
text can carry additional attribution requirements and that fair-use or
similar exceptions can apply. Article histories, talk pages, and banners were
not refetched; those checks remain mandatory at the separately controlled
export/publication gate.

The 183 capture timestamps reconcile to three code cohorts:

| Rows | Acquisition-code commit | Git blob | File SHA-256 |
| ---: | --- | --- | --- |
| 165 | `a902d06698e113a065e09e93a12c9a0d8e2ca26a` | `f18a6beec8b52d714d31b1136a56bfbc974be819` | `68a6048dae85dbf9df13b4f25698a0731399a6e0b79238db89fcd58fc7762e86` |
| 861 | `79291ce6d8ea83eee4b6a05deefbdf5afa9ebd88` | `c8b0b2aade612f3ac860eef8c2afc20395c254d0` | `645497c74852b26723f2fca33e3ed4952651aab4345190c30fad554cd3b791f4` |
| 3 | `b92d82b434cc001e41e888daa8013ea2e3aa9958` | `a256528fb4b4ab333bb0198979ea208a77ca7f42` | `10fca065b79d9cf347c8192b331c5f97b21b7c408d6d77a2a832ab03fcf0bebf` |

## Run

Run from the repository worktree with the real read-only databases available:

```bash
.venv/bin/python scripts/projects/open_model_data/admit_existing_corpus.py \
  --manifest-output batch_state/public_external_admission_manifest_v1.jsonl \
  --source-record-output batch_state/wikipedia_source_records_v1.jsonl \
  --receipt-output batch_state/public_external_admission_receipt_v1.json \
  --runtime-output batch_state/public_external_admission_runtime_v1.json
```

Repeat the command with distinct output names and compare the main manifest,
source-record manifest, and receipt hashes. Runtime is deliberately separate
because it is not a deterministic content receipt. Exit status `0` means exact
denominator reconciliation; `2` means inaccessible input or an expected/actual
mismatch. An incomplete receipt still records the full expected denominator
and writes empty local manifests, rather than silently reducing coverage.

The 2026-08-01 accepted pass ran the full denominator twice with byte-identical
results. Its small text-free aggregate receipt is committed as
`data/projects/open_model_data/admission/public_external_accepted_admission_receipt_v1.json`;
the 142.5 MB disposition manifest and 6.1 MB source-record manifest remain
local and uncommitted.

| Artifact/disposition | Rows | Lexical words | SHA-256 |
| --- | ---: | ---: | --- |
| Full local disposition manifest | 189,150 | 50,298,925 | `69516568590be55f625a7884aaa293420dc102f331c8119bbc5f0d145ec9ccbd` |
| Admitted Wikipedia `source_record_v1` manifest | 1,029 | 2,865,506 | `6b91e718622911a5a2c9a907e53dee7f3cf4c2805b0d3350c49e619f5422da68` |
| Aggregate admission receipt | 189,150 | 50,298,925 | `1359e2d2067795c4246be93cb4187d708b22a9d7af406e089d5ac087095c09d4` |
| Operator decision packet | 1 accepted family | 1,029 rows | `53b12ed59d06929ed3218b3243f07b4aa0724812935b725e2999d44c726444cd` |
| `admitted` | 1,029 | 2,865,506 | Wikipedia only |
| `unresolved` | 188,121 | 47,433,419 | Literary, public-textbook, and external-article families |
| Evaluation exact/near exclusions | 0 | 0 | Frozen registry applied |

All 1,029 generated source records satisfy the frozen JSON contract and now
carry `usage.role: training_candidate`. The frozen semantic validator reports
1,029 admitted and zero rejected. This is a source-contract admission only:
the aggregate receipt still emits `training_eligible_emitted: false`, and the
separate exporter and training authorization gates remain closed. The two runs
completed in 92.37 and 89.60 seconds with peak RSS of 195,510,272 and
198,606,848 bytes respectively.

## Dispositions and the human gate

Every processed row is exactly one of `admitted`, `proposed_admission`,
`investigation_only`, `excluded`, or `unresolved`.

- Missing provenance, acquisition, snapshot, rights, origin, or contamination
  evidence produces `unresolved`.
- Any exact or near evaluation match is `excluded`.
- Complete evidence with an explicit destination is `proposed_admission` until
  a validated operator packet accepts or rejects the exact family denominator.
- Accepted records become source-contract `admitted` records and
  `training_candidate` source records; neither state is a training payload or
  training authorization. The runner always writes
  `training_eligible_emitted: false`.

The operator packet at
`data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json`
lists the current evidence gaps and the exact accept/reject choices. The Sol
advisor verdict is that the proposal is supportable. The operator acceptance
is recorded in [issue #6166](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6166#issuecomment-5151977634)
and bound into the packet by date, operator ID, family, destination, and packet
SHA-256.

The accepted scope retains all attribution, share-alike, modification,
no-additional-restrictions, lineage, and downstream-review obligations. It
advances only to separately controlled exporter and training gates.

The other 188,121 rows remain unresolved. Acceptance does not authorize export,
training, upload, model release, redistribution, or publication and does not
emit `training_eligible`.
