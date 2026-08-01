# Ukrainian Data Foundry Correction Factory

> **Owner:** [#6121](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6121)
> under [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
> **Boundary:** review intake and adjudication, not model-ready export

> **Current scope:** the implemented contracts below remain the optional
> qualified-human-gold branch. [#6168](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6168)
> owns a separate evidence-backed silver branch for the solo-operator critical
> path. Silver must use a distinct contract and must not be relabelled as
> `qualified_correction_intake`, `headline_gold`, or human review.

## What this component produces

The correction factory takes span-aware, unresolved candidates from a local
detector or enrichment stage and produces two deterministic artifacts:

1. a review packet that preserves the original bounded context, offsets,
   language/representation/discourse axes, source-specific evidence, and
   separate view dispositions; and
2. an adjudicated correction record that preserves the complete candidate and
   qualified-human decision while remaining ineligible for training or export.

This qualified-gold component does not infer corrections. A detector, VESUM
miss, Russian morphology result, `r2u` hit, dictionary result, exact mismatch,
or model vote remains evidence until the qualified-human review contract is
satisfied.
The separate silver branch may combine such evidence under its own explicit
grade and uncertainty rules, but it cannot satisfy this human contract.

## Contracts

| Interface | Contract |
| --- | --- |
| Unresolved span candidate | `correction_candidate_v1.schema.json` |
| Qualified reviewer decision | `correction_reviewer_decision_v1.schema.json` |
| Adjudicated record | `correction_record_v1.schema.json` |
| Deterministic receipt | `correction_factory_receipt_v1.schema.json` |
| Text-free full-corpus sampling item | `language_contact_frame_item_v1.schema.json` |
| Sampling-frame receipt | `language_contact_frame_receipt_v1.schema.json` |
| Operator-approved sampling plan | `language_contact_sampling_plan_v1.schema.json` |
| Blind Ukrainian-human review item | `language_contact_blind_review_item_v1.schema.json` |
| Blind Ukrainian-human response | `language_contact_blind_response_v1.schema.json` |
| Prepared-wave receipt | `language_contact_wave_receipt_v1.schema.json` |
| First-pass reliability summary | `language_contact_first_pass_summary_v1.schema.json` |
| Campaign stop evaluation | `language_contact_campaign_receipt_v1.schema.json` |
| Conflict resolver item/response | `language_contact_resolver_review_item_v1.schema.json` / `language_contact_resolver_response_v1.schema.json` |
| Real-human gold freeze | `language_contact_gold_freeze_receipt_v1.schema.json` |
| Non-human evidence observation | `language_contact_silver_observation_v1.schema.json` |
| Non-human evidence record | `language_contact_silver_record_v1.schema.json` |
| Non-human evidence receipt | `language_contact_silver_receipt_v1.schema.json` |

All contracts are in `data/projects/open_model_data/contracts/`. The runtime
validates the schemas before writing output and replaces existing artifacts
only after all rows and receipts pass validation.

## Non-human silver production

`silver_evidence_factory.py` is the implemented solo-operator path. It streams
the exact detector artifact, validates its hash/count/byte receipt and every
candidate span, preserves source/rights/period/register/context lineage, and
writes one explicitly non-human evidence record per non-evaluation candidate.
It never calls a network service. Missing R2U, ULIF, `slovnyk.me`, heritage, or
corpus evidence remains visible as missing or unavailable; absence is not a
negative linguistic claim.

The five evidence grades are `deterministic_source_backed_silver`,
`independently_triangulated_silver`, `model_only_research`, `protected`, and
`unresolved`. A correction needs modern narration, Russian morphology and R2U
corroboration, plus an alternative attested by at least one separate
authoritative Ukrainian source. Two independent source identities produce the
triangulated grade. Model proposals and Hramatka feedback cannot promote a
record. Protected, historical/register, quoted/multilingual, OCR, proper-name,
and unresolved dispositions remain separate.

Run it after producing a detector artifact:

```bash
.venv/bin/python \
  scripts/projects/open_model_data/silver_evidence_factory.py \
  --candidates /local/path/language-contact-candidates.jsonl \
  --detector-receipt /local/path/language-contact-receipt.json \
  --detector-config \
  data/projects/open_model_data/detector/language_contact_config_v1.json \
  --input-root . \
  --output /local/path/language-contact-silver.jsonl \
  --receipt-output /local/path/language-contact-silver.receipt.json
```

The committed non-symbolic validation receipt covers the complete
`external_articles` source family: 1,205 source rows, 1,837,518 lexical words,
11,297 detector candidates, and 11,297 byte-stable silver records. Current
bounded evidence promoted no correction. It routed 5,864 spans as quoted or
multilingual, 3,943 as protected variation, 25 as proper names, and 1,465 as
unresolved. Only 131 records reached the independently corroborated `protected`
grade; 11,166 remain evidence-grade unresolved. This is a measured evidence
gap, not permission to manufacture replacements. The reproducible detector
slice config and receipt are under `data/projects/open_model_data/silver/`;
large row artifacts remain local.

The full production receipt covers all 739,564 detector candidates. It excludes
61 exact-normalized evaluation matches before output and emits 739,503 real
records (4,593,831,256 bytes; SHA-256
`87be02fcac78e26d6060574d93a1e5dd83e0f8351f9a1997c530ebf285aab502`).
The result contains 116,647 independently supported protected records and
622,856 unresolved records. Its dispositions preserve 297,791 protected
variations, 195,722 historical/register cases, 95,910 quoted or multilingual
spans, 27,272 technical/OCR cases, 15,825 proper names, and 106,983 unresolved
cases. Current bounded sources support zero correction-grade targets: the
measured correction lane is empty rather than populated from Russian
reconstructions, single dictionary hits, or model preferences.

All source families remain in their existing admission state. Silver output is
`investigation_only`, never correction-training eligible, never redistribution
cleared, and never human gold. Its compatibility target records how a later
qualified-human decision could upgrade the same candidate without weakening
the existing human contract.

## Full language-contact frame

The language-contact detector output is 2.17 GB and cannot be treated as a
small review packet. Build a text-free random-access frame over the complete
artifact before choosing review targets:

```bash
.venv/bin/python \
  scripts/projects/open_model_data/language_contact_adjudication.py \
  build-frame \
  --candidates /local/path/language-contact-candidates.jsonl \
  --detector-receipt /local/path/language-contact-receipt.json \
  --frame-output /local/path/language-contact-frame.jsonl \
  --receipt-output /local/path/language-contact-frame.receipt.json
```

The verified v1 frame contains all 739,564 detector candidates. It is
566,140,004 bytes, has SHA-256
`ca4c8ed88daa3c5addcf2a13ba70bc5d1470073c0c366f8e2b699d174c30b2ad`,
and binds the detector artifact with SHA-256
`3b051594a00477cde0c3001a82fe85861ac6afee5f12c51bf9281828aded83a8`.
Two complete builds were byte-identical. The first used 431.83 seconds and a
140,869,632-byte maximum resident set; the repeat used 527.09 seconds and a
140,197,888-byte maximum resident set.

The measured calibration strata are:

| Stratum | Candidates |
| --- | ---: |
| Modern-interference candidates | 38,187 |
| Valid-word contact candidates | 1,511 |
| False-positive rescue candidates | 297,791 |
| Historical candidates | 298,238 |
| Regional/dialectal candidates | 297,791 |
| Conversational/marked candidates | 11,594 |
| Quoted/multilingual candidates | 173,028 |
| Uncertain candidates | 67,593 |
| Technical/OCR candidates | 27,333 |
| Proper names | 15,825 |

These strata overlap. In particular, `regional_or_dialectal_candidate` is a
review stratum derived from automatic protected-variation rescue; it is not a
human-confirmed dialect label. Counts must not be summed as if they partition
the corpus.

## Freeze the review plan before sampling

Create the measured pending plan without inventing sample counts, reviewer
throughput, or a stopping threshold:

```bash
.venv/bin/python \
  scripts/projects/open_model_data/language_contact_adjudication.py \
  draft-plan \
  --frame-receipt /local/path/language-contact-frame.receipt.json \
  --plan-output /local/path/language-contact-sampling-plan.json \
  --plan-id language-contact-v1 \
  --issue-url https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6168
```

An approved plan must name two distinct qualified Ukrainian first-pass
reviewers and a distinct qualified resolver, record measured items per hour
and hours available per wave, define calibration and production targets for
every stratum, and freeze an explicit statistical stopping rule. Packet salts
are operator secrets; only their hashes belong in the plan. Store each value
in a local, uncommitted, owner-readable file. Salt values are never command-line
arguments because process listings and shell history can expose them. A
pending plan cannot produce a wave.

## Prepare and conduct one blind wave

After plan approval, `prepare-wave` streams the frame, retains the lowest
deterministic ranks in each approved stratum, takes the unique union, verifies
that it fits each first-pass reviewer's measured capacity, seeks only those
rows in the 2.17 GB detector artifact, and produces two independently ordered
blind packets plus two offline Ukrainian workspaces:

```bash
.venv/bin/python \
  scripts/projects/open_model_data/language_contact_adjudication.py \
  prepare-wave \
  --candidates /local/path/language-contact-candidates.jsonl \
  --detector-receipt /local/path/language-contact-receipt.json \
  --frame /local/path/language-contact-frame.jsonl \
  --frame-receipt /local/path/language-contact-frame.receipt.json \
  --plan /local/path/approved-sampling-plan.json \
  --input-root /local/path/corpus-root \
  --stage calibration \
  --wave-number 1 \
  --salt-a-file /local/private/reviewer-a.salt \
  --salt-b-file /local/private/reviewer-b.salt \
  --selected-output /local/path/selected-frame.jsonl \
  --correction-output /local/path/correction-candidates.jsonl \
  --blind-a-output /local/path/blind-a.jsonl \
  --blind-b-output /local/path/blind-b.jsonl \
  --workspace-a-output /local/path/reviewer-a.html \
  --workspace-b-output /local/path/reviewer-b.html \
  --receipt-output /local/path/wave.receipt.json
```

Calibration is exactly wave 1 and has no prior-wave inputs. Every production
wave must provide the calibration receipt/selected manifest and every earlier
production receipt/selected manifest as paired, repeatable
`--prior-wave-receipt` and `--prior-selected-manifest` arguments. The tool
validates the complete numbered chain and excludes every earlier candidate;
omitting a prior wave, repeating a candidate, or mixing plan/frame hashes fails
closed. Packet IDs include stage and wave number, so later waves cannot be
silently substituted for earlier reviewer output.

Each offline workspace exports complete
`language_contact_blind_response_v1` rows. It records the named reviewer's
qualification evidence and independence attestation, per-item start and end
time, evidence viewed, citations, language/representation/discourse axes,
separate downstream views, uncertainty, and rationale. Detector categories,
confidence, queue route, model votes, prior labels, and the other reviewer's
answers remain hidden.

Validate and assemble the two complete first passes:

```bash
.venv/bin/python \
  scripts/projects/open_model_data/language_contact_adjudication.py \
  assemble-first-pass \
  --plan /local/path/approved-sampling-plan.json \
  --stage calibration \
  --wave-number 1 \
  --wave-receipt /local/path/wave.receipt.json \
  --selected-manifest /local/path/selected-frame.jsonl \
  --correction-packet /local/path/correction-candidates.jsonl \
  --blind-a /local/path/blind-a.jsonl \
  --blind-b /local/path/blind-b.jsonl \
  --responses-a /local/path/reviewer-a.responses.jsonl \
  --responses-b /local/path/reviewer-b.responses.jsonl \
  --decisions-output /local/path/first-pass-decisions.jsonl \
  --summary-output /local/path/first-pass-summary.json
```

Agreement across the full adjudicative core becomes a first-pass agreement;
both reviewers' citations, uncertainty, and rationale remain preserved in the
merged projection. Any core difference remains an `unresolved_conflict`; the
tool does not manufacture a linguistic consensus. A distinct qualified
Ukrainian resolver is required before such a row can become adjudicated gold.

Timing, evidence-view, and blinding attestations remain in the validated blind
response artifacts. Assembly validates them before projecting reviewer identity
and linguistic judgment into the frozen `correction_reviewer_decision_v1`
shape. They are not copied into that older contract: doing so would silently
break v1 consumers, and a third resolver necessarily sees the prior reviews.

The summary records adjudicative-core agreement, decision agreement, conflict
rate, and correction yield with identified Wilson intervals overall and for
every overlapping stratum. The adjudicative core includes the decision,
language, representation, discourse role, accepted correction and alternatives,
and all view dispositions. Independent wording, citations, and uncertainty are
merged and preserved rather than misclassified as linguistic disagreement.
Insufficient data remains `null`; it is never rendered as zero agreement or a
passing interval.

For every conflict, build the conflict-only packet for the distinct resolver:

```bash
.venv/bin/python scripts/projects/open_model_data/language_contact_adjudication.py \
  prepare-resolver \
  --plan /local/path/approved-sampling-plan.json \
  --stage calibration --wave-number 1 \
  --wave-receipt /local/path/wave.receipt.json \
  --first-pass-summary /local/path/first-pass-summary.json \
  --decisions /local/path/first-pass-decisions.jsonl \
  --blind-a /local/path/blind-a.jsonl \
  --packet-output /local/path/resolver-packet.jsonl \
  --workspace-output /local/path/resolver.html
```

The resolver sees the two anonymized primary projections but not detector/model
authority. `resolve-conflicts` requires the predeclared distinct resolver,
records that prior reviewer output was exposed, and promotes only a non-
`unresolved` third-human projection. An unresolved resolver answer stays
explicitly unresolved.

After each numbered production wave, run `summarize-campaign` with the complete
ordered sequence of `--first-pass-summary` and paired `--wave-receipt` inputs.
It checks production category coverage, Wilson interval width, the predeclared
per-stratum agreement stability threshold, and correction-yield learning-curve
stability across the required consecutive waves. Calibration alone and too few
production waves always return `stop_eligible: false` with explicit reasons.

Only a stopped campaign can run `freeze-gold`. The freeze requires every wave's
two response files, resolver packet/response and resolution summary, final
decisions, and correction packet. It validates the complete non-overlapping
chain, reruns the #6121 correction factory, binds the frozen evaluation
registry, and writes one real-human freeze receipt. The frozen records remain
`model_training_or_export_eligible: false`; rights, provenance, contamination,
training preregistration, and Phase 4 export gates are separate controls.
Calibration rows are reported as non-gold evidence; only adjudicated production
rows enter the receipt's `headline_gold` count, and unresolved production rows
remain explicitly `unresolved_non_gold`.

Evidence enrichment is selected-only. A miss in the current bounded `r2u`
cache means only that the exact query is absent from that cache; it is not a
negative lookup against all of `r2u`. ULIF and a named underlying dictionary
represented by `slovnyk.me` remain pending until their specific parsers and
source receipts complete. No bulk scraping or raw grey-area payload is emitted
into reviewer or model artifacts.

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
The reconstructed surface is Russian evidence used to query R2U; it is never
itself emitted as a Ukrainian correction alternative.

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
