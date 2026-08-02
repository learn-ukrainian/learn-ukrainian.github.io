# Ukrainian Data Foundry Architecture

> **Status:** Operator-approved architecture; implementation contract
> **Owner:** [#6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
> (production successor to completed foundation
> [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056))
> **Architecture issue:** [#6119](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6119)
> **Recorded:** 2026-07-31; delivery boundary refreshed 2026-08-02
> **Does not authorize:** model training, fine-tuning, weight publication,
> dataset upload or release, redistribution, researcher outreach, private-data
> disclosure, or OCR

## Purpose

The Ukrainian Data Foundry is reusable, corpus-portable infrastructure for
preparing and measuring Ukrainian language data. Ukrainian and open-weight
model teams must be able to run it on this project's corpus, their own corpora,
or other licensed collections without transferring those collections to this
project.

The Foundry's job is to make evidence and boundaries explicit:

- what a record is and where it came from;
- which uses are permitted and which remain unknown;
- which Ukrainian period, genre, register, region, and origin it represents;
- what VESUM can and cannot attest about its forms;
- which passages need contextual grammar, calque, collocation, or
  Russian-interference review;
- which decisions are evidence-graded silver, protected, unresolved, or
  optional qualified-human gold; and
- which mechanically disjoint view, if any, may consume the record.

It is not a project-owned general-purpose model and does not claim that one
corpus or one profiler can make a model fluent. The first profiler component is
a foundation for later adjudication, exporters, recipes, and measurement.

## Architecture

```text
Sources and provenance
        ↓
Streaming normalization and language-span handling
        ↓
Period · genre · register · region · origin classification
        ↓
VESUM morphology and unknown-form evidence
        ↓
Grammar · calque · collocation · Russian-interference candidates
        ↓
Evidence-tiered silver · protection · unresolved routing
        ↓
Optional qualified Ukrainian-human gold upgrade
        ↓
Mechanically separate training · correction · preference · evaluation views
        ↓
Frozen baseline harness and before/after measurement
```

Every arrow is a versioned interface. Passing through a layer adds evidence;
it never silently erases an earlier classification, changes unknown into
permission, or promotes a candidate into a human decision.

## Record classifications

The interfaces preserve four independent classification axes. Missing metadata
is recorded as `unknown` or `unresolved`; it is never inferred merely to make a
record eligible.

### Authorship origin

- `human_authored`
- `machine_generated`
- `machine_translated`
- `human_revised_synthetic`
- `unknown`

### Intended linguistic use

- `modern_literary_ukrainian`
- `historical_literary_ukrainian`
- `historical_documents`
- `folk_heritage`
- `regional_dialectal`
- `conversational_marked_register`
- `quoted_foreign_or_multilingual`
- `unresolved`

### Permitted-use state

- `training_eligible`
- `evaluation_only`
- `private_reference`
- `provenance_investigation`
- `rights_redistribution_investigation`
- `unresolved`
- `excluded`

### Evidence state

- `vesum_attested`
- `vesum_attested_with_usage_marker`
- `vesum_unknown`
- `foreign_language_candidate`
- `ocr_encoding_candidate`
- `proper_name_candidate`
- `requires_contextual_review`

These axes are not substitutes for each other. A VESUM-attested form can still
occur in a case, agreement, government, syntax, collocation, or semantic-calque
error. A VESUM-unknown form can be a proper name, historical form, dialect
form, quotation, encoding defect, or genuine non-Ukrainian candidate.

## Interfaces and state transitions

### 1. Source and provenance record

The existing `source_record_v1` contract remains the admission authority. A
Foundry adapter supplies a stable source-record identifier, non-published
locator, content-hash scope, acquisition lineage, bibliographic evidence,
rights evidence, authorship origin, contamination exclusions, and review
state.

Inventory membership is not admission. The #6107 recovery baseline currently
records zero source-record admissions and zero redistribution-cleared assets.
The invalid 5,000-record export may locate an underlying work but cannot prove
source, edition, rights, acquisition lineage, or contamination status.

### 2. Corpus adapter and normalized record

The profiler consumes an explicit, validated adapter configuration. An adapter
maps a streaming source such as read-only SQLite rows or JSON Lines objects to
a common record without assuming a personal filesystem path or this project's
database schema.

The normalized record carries:

- stable record and source-record identifiers;
- a non-published source locator;
- text available only in the local processing stream;
- source family plus known period, genre, register, region, and origin;
- permitted-use, rights, provenance, and contamination states; and
- explicit `unknown` values for unavailable dimensions.

Normalization is deterministic and versioned. It records Unicode and
apostrophe handling and separates Ukrainian-script, foreign-script, mixed, and
encoding-candidate spans. Aggregate or public receipts never contain record
text.

### 2a. Language spans and lexical evidence

Russian quotations, Russian character dialogue, Ukrainian-phonetic Russian,
mixed/surzhyk candidates, historical East Slavic material, Church Slavonic,
and modern Ukrainian narration are not interchangeable. The Foundry classifies
bounded spans on four independent axes: language identity, representation,
discourse role, and downstream disposition. It preserves the original text and
records offsets and evidence; it never silently translates or rewrites a
source.

The binding evidence routing, observed corpus cases, dictionary roles, rights
posture, and #6121 regression set are recorded in the
[language-span and lexical-evidence contract](../research/UKRAINIAN_DATA_FOUNDRY_LANGUAGE_SPAN_AND_LEXICAL_EVIDENCE.md).
In particular, a VESUM miss routes to Ukrainian-source escalation, a direct
`r2u` hit is positive Russian lexical evidence rather than a contextual
verdict, and phonetic Russian requires span-gated reconstruction before
Russian morphology and `r2u` validation.

### 3. Morphology evidence

The morphology layer queries the pinned VESUM interface in bounded batches. It
records token totals, attested and unknown counts, lemma/POS evidence, and
usage-marker coverage where the pinned database supports them.

VESUM is a deterministic morphological authority, not a contextual sentence
judge. `vesum_unknown` means "requires classification". It never means
"confirmed error". The regression phenomenon `звучит` must be detectable as a
VESUM-unknown/non-Ukrainian candidate while `звучить` is attested, but both the
candidate record and tests preserve the non-adjudicative boundary.

### 4. Review candidate

A candidate extractor emits no correction gold. Each candidate contains:

- source-record and local-record identifiers;
- a bounded, non-published locator rather than source text;
- surface and normalized forms;
- VESUM evidence;
- source period, register, region, and origin;
- candidate category and evidence/confidence state; and
- `review_disposition: unresolved`.

Historical, heritage, dialectal, marked-register, proper-name, foreign, and
multilingual candidates are protected from automatic correction. Grammar,
calque, collocation, government, syntax, and semantic layers may consume these
candidates later, but must retain their provenance and uncertainty.

### 5. Evidence-tiered decisions and optional human gold

Only a separate correction-data contract may promote a candidate. The
production path records source-specific evidence, rationale, uncertainty,
protected variation, evidence grade, and destination-specific disposition as
silver. It never labels automated or model-supported evidence as human gold.
Qualified Ukrainian-human review remains an optional upgrade path.

The silver promotion path is fail closed:

```text
profiled candidate
  → provenance and rights screened
  → exact/near-duplicate and evaluation contamination clear
  → source-specific evidence and protection rules applied
  → silver evidence grade or unresolved
  → destination-specific export eligibility
```

An unresolved record remains non-exportable to labeled-learning views. A
protected record remains a keep/no-change example only where its destination
contract permits that role. Synthetic fixtures and model outputs cannot stand
in for qualified human decisions or be called human gold.

The implemented #6121 boundary is the
[correction-factory runbook](../runbooks/ukrainian-data-foundry-correction-factory.md).
Its versioned contracts and deterministic CLI enforce original span
preservation, source-specific evidence, evaluation-contamination joins,
optional human-gold review, and fail-closed handoff. The completed #6168
evidence factory adds the production silver/protection path without claiming
human gold; consumer eligibility remains a separate destination decision.

### 6. Consumer views

Continued-pretraining, correction/instruction, preference, quality-filter, and
evaluation views are separate schemas and artifacts. They share lineage, not
payloads. No view is constructed by renaming or filtering a mixed export after
publication.

A non-evaluation view requires all of the following:

- complete source-record admission evidence;
- granted destination-specific rights;
- known permitted use and authorship origin;
- exact and near-duplicate disposition;
- contamination checks against all frozen evaluation inventories and derived
  rules; and
- the required evidence or adjudication state for that destination.

Failure or absence at any gate yields an investigation, private, evaluation,
unresolved, or excluded state—not `training_eligible`.

The implemented #6122 boundary is the
[model-view and recipe runbook](../runbooks/ukrainian-data-foundry-model-views.md).
It provides separate schemas and commands for continued pretraining,
correction/instruction, preference, quality-filter, and held-out evaluation
artifacts. Non-evaluation views revalidate the source and correction contracts,
all emitted text fields against the complete evaluation-exclusion registry,
private/origin/rights state, and exact/near duplication inside each output.
Modern-Ukrainian pretraining retains source bytes and exposes character-level
loss masks; its payload contract binds every full source or segment to an
explicit derivation receipt and parent content hash. Tokenizer-specific mask
projection is part of the bound preparation recipe. Export receipts report
recomputed source-admission and intra-view deduplication state. Recipe
manifests pin exact view and receipt hashes, immutable model/tokenizer/code
revisions, and positive training hyperparameters, while recording
`training_authorized: false` and `execution_state: not_run`.

### 7. Reference validation and frozen measurement

The implemented #6123 boundary is the
[reference-build runbook](../runbooks/ukrainian-data-foundry-reference-build.md).
It joins every versioned interface in one deterministic command. The local
integration fixture uses the observed `звучит` → `звучить` case to prove
Russian-interference evidence routing, language-span masking, correction
reconstruction, and the separate view contracts without representing fixture
reviewers as qualified humans or admitting the row to training.

The same command can either validate the committed profile receipt or rerun all
189,150 records and 50,298,925 lexical words. The fresh mode regenerates the
6,646,916-row candidate artifact inside a temporary directory, verifies its
exact hash, and deletes it. The deterministic manifest is identical across
both modes; runtime and memory belong to a separate observation receipt.

Frozen baseline validation rebuilds the source-only 677-item request packet,
reimports saved Gemma outputs, and re-scores the identity and model arms. It
performs no generation. Its only decision is whether the measurement interface
reproduces and the saved model arm beats copying the source; it is not a causal
Foundry-training result or a broad Ukrainian model ranking.

## Safety invariants

### Rights and provenance

- Unknown rights are not permission.
- Public accessibility is not redistribution or model-training permission.
- Source-family inventory counts do not establish record-level admission.
- Private references stay private even when they improve internal evidence.
- Aggregate receipts expose logical provenance references, never personal
  mount paths or confidential source content.

### Authorship and variation

- Human-authored, machine-generated, machine-translated, human-revised
  synthetic, and unknown-origin material remain distinct.
- Franko, Hrushevsky, folk material, historical documents, quotations,
  dialects, archaisms, and marked registers do not automatically define modern
  literary Ukrainian.
- Legitimate Ukrainian variation is preserved and labeled rather than
  flattened or silently corrected.
- Machine-generated lessons, FOLK/BIO material, and KubeDojo translations
  remain mechanically separate from human-authored candidate data.
- Russian quotations and character speech remain faithful source evidence;
  they are annotated and masked or excluded from a modern-normative training
  view rather than corrected in place.
- Dictionary evidence remains source-specific. ULIF synonym groups,
  `slovnyk.me` dictionaries, `r2u`, VESUM, and heritage attestations retain
  their distinct authority, period, register, provenance, and rights scope.

### Evaluation contamination

- Closed #2156 and public v0.1.1 remain unchanged and immutable.
- #6057/#6084 remain the separately frozen, coverage-complete v0.2 evaluation
  home.
- Evaluation source IDs, text, references, edits, dispositions, hashes,
  derived rules, exact duplicates, and near duplicates are denied from every
  training, correction, preference, and quality-filter export.
- Generation receives source-only requests; gold and adjudication notes never
  enter prompts.

### Determinism and privacy

- Sources are read-only and ordered by stable identifiers.
- Normalization, tokenization, batching, aggregation, sorting, serialization,
  and hash scopes are versioned.
- Repeated runs over identical inputs produce byte-stable outputs.
- Full candidate files and local runtime state remain uncommitted.
- Committed receipts contain safe aggregate counts, schema/config hashes,
  logical provenance references, limitations, and explicit unresolved
  denominators—never copyrighted corpus text or private data.

## First implementation: full-corpus profiler

Issue #6120 delivers the first substantial component. It must process every
locally accessible public/external human-authored record, not an arbitrary
sample. The current evidence baseline is 189,150 rows and 50,298,925 lexical
words across literary, public/external textbook, external article/transcript,
and Ukrainian Wikipedia families. Private references and all other origin/use
classes are measured or excluded separately rather than silently removed from
the denominator.

The profiler reports:

- processed and excluded rows and lexical words;
- source-family, period, genre, register, region, origin, and permitted-use
  distributions with explicit unknowns;
- VESUM-attested and unknown token counts;
- lemma, POS, and usage-marker coverage where supported;
- unknown-form frequency and source distribution; and
- provenance-linked unresolved review candidates.

Tokenizer diagnostics are optional in this first component unless an existing
approved interface can be included without compromising the full-corpus
morphology deliverable.

## Completed v1 execution chain

1. [#6119](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6119)
   merges this architecture and aligns the control plane.
2. [#6120](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6120)
   implements and runs the full-corpus profiler.
3. [#6121](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6121)
   implements the correction-data intake and qualified adjudication flow.
4. [#6122](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6122)
   implements disjoint exporters and reproducible preparation/training
   recipes without running training.
5. [#6123](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6123)
   validates the end-to-end reference build and frozen baseline harness.

External validation may follow a built artifact. It is not a prerequisite for
any step above. Dataset release, upload, redistribution, model training, weight
publication, private-data disclosure, researcher contact, and OCR each require
separate present-tense authorization.

## Phase 2–4 delivery state

Issues #6166–#6169 are complete: corpus admission evidence, the full-corpus
contextual detector, evidence-tiered silver/protection data, and real disjoint
consumer views now exist. Closed #6170 preserves a historical treatment design
but is not planned and is not part of the delivery chain.

Issue #6171 is the sole remaining Foundry lane. It must correct the executable
capability separation, restore retained source locators, expose one bounded
consumer JSONL adapter and one public CLI, preserve every contextual and
protected-variation route, emit deterministic model-ready views and receipts,
and reproduce the whole bounded path from a clean environment. The project
then stops before model download, accelerator rental, optimizer execution,
adapter creation, upload, or publication. Optional qualified-human gold and
downstream model results may strengthen later evidence, but neither blocks the
Foundry release.
