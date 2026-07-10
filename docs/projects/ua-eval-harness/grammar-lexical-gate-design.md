# Ukrainian grammar and lexical-naturalness gate design

**Version:** 2
**Date:** 2026-07-10
**Author:** GPT-5.6 Sol; revision input from Codex, AGY, and Claude-Infra
**Status:** Design only. Runtime implementation remains pending.

Normative terms such as **MUST**, **MUST NOT**, **REJECT**, and **AUDIT** are binding requirements for the proposed gate.

## Revision log v1→v2

| Requirement | Version 2 incorporation |
|---|---|
| **R1** | §§4.6, 8, 9 add a finite scan manifest, per-detector coverage states, the complete-or-AUDIT invariant, and `coverage_missing` metrics. |
| **R2** | §5.4 replaces asserted dependency uniqueness with three executable local recognizers, explicit feature domains, exclusions, and negative fixtures in §12.4. |
| **R3** | §§6.4–6.5 make GRAC observations computable but non-rejecting, define a curated contrary-attestation escape, and make Балла AUDIT-only for v2. |
| **R4** | §§4.1–4.5 define token-level boundaries for vocabulary tables, dialogue, grammar notes, and mixed-language surfaces; §12.2 supplies fixtures. |
| **R5** | §§6.1 and 6.7 define required-source predicates, total evidence precedence, an exhaustive fusion table, and the heritage conflict override. |
| **R6** | §§5.2, 8.2–8.4, and 9 define the tokenizer, denominator invariants, correction-family/error-span algorithms, output-total invariants, and conditional score determinism. |
| **R7** | §7 binds every judge result to a candidate locus and hypothesis and exhaustively validates relation × candidate class. |
| **R8** | §§9.2 and 11 add measured target-vocabulary coverage, lexical diversity retention, trend metrics, and rank ineligibility for flattening. |
| **R9** | §§6.1, 6.6, and 12.6 add the WordNet provenance ban citing EPIC #1657, the СУМ-11 counter-evidence contract, and concrete `кобета`/`кобіта` and `коцюба` traps. |

## 1. Purpose and scope

Generated Ukrainian currently fails in three materially different ways:

1. Morphology or orthography is invalid.
2. The words are individually valid and grammatically formed, but the chosen word, sense, government pattern, or collocation is unnatural Ukrainian.
3. A factual claim is false or unsupported.

This gate covers the first two classes. Fact verification remains the responsibility of the existing Layer A/B grounding system.

Tetiana’s motivating observation is preserved: free-tier writers can produce superficially grammatical Ukrainian while remaining blind to the intended English sense and selecting unnatural mappings or `приймати участь`-class calques. VESUM-valid words and plausible inflections therefore cannot, by themselves, establish learner-facing naturalness.

The design introduces:

- **Core G:** deterministic morphology and orthography.
- **Core L:** deterministic lexical rules, collocations, calques, evidence fusion, and residue-candidate generation.
- **Residue J:** a qualified cross-family LLM judge restricted to explicitly generated syntax and sense-in-context candidates.
- A coverage ledger proving which checks ran for every eligible unit.
- A scorecard reporting grammar and collocation/calque errors per 1,000 Ukrainian words without rewarding lexical flattening.

The gate is fail-closed:

```text
confirmed defect                  -> REJECT
complete coverage, no defect      -> ACCEPT
ambiguity, incomplete coverage,
source failure, or invalid output -> AUDIT
```

At artifact level:

```text
all candidates ACCEPT and coverage_missing == 0 -> PASS
one or more REJECT                              -> FAIL_CONTENT
no REJECT, but one or more AUDIT                -> NEEDS_AUDIT
```

Both `FAIL_CONTENT` and `NEEDS_AUDIT` are non-shippable.

## 2. Non-goals

This design does not:

- verify factual claims;
- rank general Ukrainian capability;
- use WordNet synonyms as authoritative evidence;
- treat corpus absence as proof of error;
- treat every uncommon, regional, historical, or dialectal word as defective;
- penalize A1 English scaffolding or vocabulary glosses;
- let an LLM scan prose freely for unregistered findings;
- let an LLM assign counts or scores;
- auto-apply an LLM-suggested correction without re-running the complete gate;
- claim that a VESUM hit proves contextual correctness;
- claim full naturalness coverage where no registered detector or bounded residue candidate exists.

The boundary with general Ukrainian leaderboards remains as defined in [leaderboard-boundary.md](leaderboard-boundary.md).

## 3. Existing contracts reused

### 3.1 Layer B provenance substrate

The gate MUST reuse the following contracts unchanged from [layerb-entailment-gate-design.md](layerb-entailment-gate-design.md):

- `AnchorSegment`;
- `AnchorCandidate`;
- `AnchorSetResult`;
- `JudgeWindow`;
- stable `candidate_id`, `event_output_id`, and `canonical_source_id`;
- complete candidate-set invariants;
- raw and normalized hashes;
- ordered, raw-mappable support spans;
- canonical-source aggregation;
- delimited untrusted-data serialization;
- deterministic prompt-injection screening.

A linguistic evidence binding references an immutable `AnchorCandidate`; it does not copy or weaken its provenance fields.

```text
EvidenceBinding {
  evidence_binding_id: sha256
  candidate_id: AnchorCandidate.candidate_id

  source_role:
    "VESUM_ANALYSIS" |
    "PRAVOPYS_RULE" |
    "UA_GEC_PAIR" |
    "ANTONENKO_STRUCTURED" |
    "ANTONENKO_PROSE" |
    "GRAC_OBSERVATION" |
    "MODERN_ATTESTATION_CARD" |
    "BALLA_OBSERVATION" |
    "PHRASEOLOGICAL_ATTESTATION" |
    "HERITAGE_DEFENSE" |
    "SUM11_SUPPORT" |
    "RUSSIAN_SHADOW_SIGNAL"

  authority_class:
    "NORMATIVE" |
    "CURATED_RULE" |
    "ADJUDICATED_PAIR" |
    "POSITIVE_DEFENSE" |
    "OBSERVATIONAL" |
    "HEURISTIC"

  target_span_ids: non-empty tuple<string>
  rule_or_pair_id: string | null
  corpus_snapshot_id: string
  ancestor_source_ids: tuple<string>
}
```

Any missing output, truncated source result, hash mismatch, incomplete query plan, ambiguous source identity, or forbidden provenance ancestor produces `AUDIT`.

### 3.2 Canonical finding schema

Findings MUST project into `ua_contact_quality_evidence.v1`, documented in [schema.md](schema.md) and implemented by [`qg_schema.py`](../../../scripts/audit/qg_schema.py).

The existing dimensions remain canonical:

- `contact_grammar`;
- `contact_calque`;
- `ukrainian_style`;
- `mechanics`;
- `naturalness`;
- `level_policy`.

Detailed scan, coverage, and gate state lives in the evidence artifact defined in §9.

### 3.3 Existing deterministic machinery

The implementation SHOULD reuse:

- VESUM batching and whitelist policy from [`scripts/audit/config.py`](../../../scripts/audit/config.py);
- canonical phrase and sense-restricted entries from [`calque_corrections.py`](../../../scripts/lexicon/calque_corrections.py), after migration to versioned provenance;
- current Russianism and UA-GEC checks as candidate generators;
- existing `quoted_bad_form`, `teaching_contrast`, `heritage_allowed`, and `suppressed_fp` dispositions;
- the gate hierarchy in [audit-standards.md](../../best-practices/audit-standards.md).

Existing heuristic regexes MUST NOT silently become stronger evidence merely because they are reused.

## 4. Input and surface-role contract

The gate scans parsed user-visible artifacts, not raw writer transcripts. It runs after strict output parsing and before correction, review, promotion, or publication.

### 4.1 Surface partition invariant

Every user-visible Unicode code point MUST belong to exactly one `SurfaceRegion`. Regions MUST be ordered, non-overlapping, raw-mappable, and collectively exhaustive over user-visible content.

```text
SurfaceRegion {
  region_id: sha256
  raw_start: integer
  raw_end: integer
  surface_kind:
    "VOCABULARY_ROW" |
    "DIALOGUE_LINE" |
    "GRAMMAR_NOTE" |
    "LESSON_PROSE" |
    "ACTIVITY_FIELD" |
    "SOURCE_QUOTE" |
    "METADATA"

  role:
    "UKRAINIAN_TARGET" |
    "ENGLISH_GLOSS" |
    "QUOTED_BAD_FORM" |
    "TEACHING_CONTRAST_BAD" |
    "TEACHING_CONTRAST_GOOD" |
    "SOURCE_QUOTE" |
    "PROPER_NAME_OR_CITATION" |
    "CODE_OR_METADATA" |
    "UNKNOWN_ROLE"

  role_method:
    "STRUCTURED_FIELD" |
    "TABLE_COLUMN" |
    "EXPLICIT_LANGUAGE_TAG" |
    "EXPLICIT_BILINGUAL_SEPARATOR" |
    "INLINE_UKRAINIAN_RUN" |
    "QUOTATION_CONTRACT"

  raw_sha256: sha256
}
```

A gap, overlap, invalid offset, or user-visible `UNKNOWN_ROLE` produces `coverage_missing → AUDIT`.

Punctuation between two regions inherits a role only if both adjacent regions have the same role. Otherwise it becomes a non-scored separator. Ambiguous punctuation ownership produces `UNKNOWN_ROLE`.

### 4.2 Token-level language boundaries

Token classification is performed after structural parsing:

- A token containing Ukrainian Cyrillic letters and no Latin letters is Ukrainian.
- A token containing Latin letters and no Cyrillic letters is English or metadata according to its structural field.
- A token containing both Latin and Cyrillic letters is `MIXED_SCRIPT`.
- Digits and punctuation do not determine language by themselves.
- In an English grammar-note field, a contiguous Cyrillic run is an embedded `UKRAINIAN_TARGET` unless explicitly marked as a quoted bad form.
- In a Ukrainian field, a contiguous Latin run is not automatically a gloss. It must be structurally bound as an English gloss, citation, code, or proper name; otherwise it audits.
- Language classification never overrides an explicit quoted-error or teaching-contrast role.

A `MIXED_SCRIPT` token in learner-facing text is ledger-visible and produces `INELIGIBLE_COVERAGE` unless a versioned acronym or technical-token contract exempts it.

### 4.3 Vocabulary-table contract

The schema or table header MUST assign column roles before tokenization.

| Field or column | Role |
|---|---|
| Ukrainian lemma/headword | `UKRAINIAN_TARGET` |
| English translation/gloss | `ENGLISH_GLOSS` |
| Ukrainian definition | `UKRAINIAN_TARGET` |
| Ukrainian example | `UKRAINIAN_TARGET` |
| English example translation | `ENGLISH_GLOSS` |
| Explicit bad form | `QUOTED_BAD_FORM` |
| Corrected form | `TEACHING_CONTRAST_GOOD` |
| Source/citation cell | `PROPER_NAME_OR_CITATION` or `SOURCE_QUOTE` |

A row containing both English and Ukrainian MUST preserve separate token spans. The English tokens are excluded by design; the Ukrainian headword and examples still receive full morphology and lexical checks.

A missing, duplicated, or ambiguous column mapping produces `AUDIT / VOCABULARY_ROLE_BINDING_FAILED`.

### 4.4 Dialogue contract

Speaker labels and stage directions have separate regions from dialogue content.

For explicitly bilingual dialogue:

```text
speaker_label | ukrainian_utterance | english_translation
```

or an equivalent schema-bound representation is required.

An em dash is treated as a bilingual separator only when the field schema or an explicit parser contract declares it so. A dash inside ordinary Ukrainian syntax is never guessed to be a translation separator.

The Ukrainian utterance receives full checks. The English translation is excluded from morphology, lexical penalties, and the Ukrainian-word denominator. If the two sides are intended for sense-fan use, they also receive an `EnglishSpanBinding`.

### 4.5 Grammar-note and mixed-language contract

Grammar notes may contain English explanation and embedded Ukrainian examples.

The parser MUST:

1. mark structured English explanatory text `ENGLISH_GLOSS`;
2. identify inline Ukrainian runs at token granularity;
3. preserve quoted-good and quoted-bad example roles separately;
4. treat the correction side of a contrast as `UKRAINIAN_TARGET`;
5. exclude the intentionally bad side from penalties;
6. audit an unstructured bilingual passage whose boundary cannot be reconstructed deterministically.

```text
EnglishSpanBinding {
  binding_id: sha256
  surface_kind: enum

  method:
    "VOCABULARY_COLUMNS" |
    "DIALOGUE_FIELDS" |
    "EXPLICIT_LANGUAGE_TAGS" |
    "REGISTERED_INLINE_PAIR"

  english_span_ids: non-empty tuple<string>
  ukrainian_span_ids: non-empty tuple<string>
  binding_complete: boolean
  binding_sha256: sha256
}
```

Only the four registered methods may establish a bilingual binding. Script proximity alone is insufficient. A failed binding needed by a detector becomes `coverage_missing → AUDIT`.

A1 English scaffolding is intentional. An English gloss such as `hard — складний` is never itself calque-flagged. Its Ukrainian side remains fully eligible for form and contextual-use checks.

### 4.6 Eligible units and scan manifest

The scan universe is finite and deterministic. It contains:

1. Every Ukrainian word token in a scored role.
2. One `LEXICAL_USE` unit for every open-class Ukrainian token.
3. Every contiguous two-to-six-token window within a clause.
4. Every maximal finite clause bounded by sentence or clause punctuation.
5. Every recognized local agreement or government shape.
6. Every registered bilingual pair.
7. Every explicit teaching contrast and quotation disposition.

```text
ScanUnit {
  scan_unit_id: sha256
  unit_kind:
    "TOKEN" |
    "LEXICAL_USE" |
    "PHRASE_WINDOW" |
    "FINITE_CLAUSE" |
    "LOCAL_SHAPE" |
    "BILINGUAL_PAIR" |
    "DISPOSITION"

  region_ids: non-empty tuple<string>
  token_ids: tuple<string>
  raw_start: integer
  raw_end: integer
  required_detector_ids: non-empty tuple<string>
}

DetectorRun {
  detector_run_id: sha256
  scan_unit_id: string
  detector_id: string
  detector_version: string

  applicability:
    "APPLICABLE" |
    "NOT_APPLICABLE"

  outcome:
    "CLEAN" |
    "CANDIDATE" |
    "EXCLUDED" |
    "UNCOVERED" |
    "UNCURATED_SENSE" |
    "BINDING_FAILED" |
    "SPARSE_EVIDENCE" |
    "FAILED"

  candidate_ids: tuple<string>
  evidence_binding_ids: tuple<string>
  failure_reason: string | null
}
```

`NOT_APPLICABLE` is valid only when the detector’s versioned applicability predicate ran successfully and returned false. An absent detector record is not equivalent to `NOT_APPLICABLE`.

For every open-class `LEXICAL_USE`, the contextual-use detector MUST produce one of:

- a matching positive or negative curated card;
- a bounded residue candidate;
- `UNCURATED_SENSE`;
- `UNCOVERED`.

Thus a VESUM-valid but contextually wrong use outside registered coverage cannot disappear. It becomes ledger-visible and audits.

## 5. Core G: morphology and orthography

### 5.1 What VESUM can decide

VESUM can provide deterministic evidence for:

- whether an exact surface form is indexed;
- possible lemmas and parts of speech;
- encoded gender, number, case, person, tense, and related tags;
- whether forms could share a lemma;
- whether a form is marked historical or archaic;
- available paradigms.

VESUM does not decide:

- which analysis is correct in a sentence;
- dependency structure;
- subject, object, modifier, or predicate roles;
- case government;
- cross-word agreement without a proven local relation;
- semantic compatibility;
- collocation naturalness;
- interchangeability;
- intended meaning.

A VESUM hit proves form possibility, not contextual correctness.

### 5.2 Normative Ukrainian-word tokenizer

Tokenization operates on NFC text while retaining raw offsets and raw hashes.

A Ukrainian word token:

1. begins and ends with a Ukrainian letter;
2. may contain internal Ukrainian letters;
3. may contain an apostrophe only when flanked by Ukrainian letters;
4. may contain a hyphen only when flanked by Ukrainian letters or when matching the numeric-compound rule below.

Recognized apostrophes are:

```text
'  U+0027
’  U+2019
ʼ  U+02BC
```

Recognized internal hyphens are U+002D and U+2010. En and em dashes are separators.

Rules:

- `п’ять` is one word.
- `будь-хто` is one word.
- `20-річний` is one eligible numeric-compound word.
- A standalone numeral such as `2026` is not a Ukrainian word.
- A proper name in ordinary Ukrainian target prose, such as `Київ`, is an eligible word and counts in the denominator.
- A citation-only proper name is excluded through its surface role, not through tokenizer guessing.
- An all-Ukrainian acronym is one eligible token and receives the acronym contract.
- A mixed Latin/Cyrillic token is not silently split; it produces `MIXED_SCRIPT` and coverage audit.
- Stress marks may be removed for lookup only. Raw token spans remain authoritative.
- Slash-separated alternatives are separate words unless a registered lexical card defines the complete form.
- Emoji, punctuation, URLs, and markup are not words.

```text
eligible_ukrainian_words =
  count(tokens matching the tokenizer in scored Ukrainian roles)
```

### 5.3 Token validity decisions

| VESUM result | Other evidence | Candidate decision |
|---|---|---|
| One or more analyses | None | `ACCEPT / VESUM_ATTESTED` for form validity only |
| No analysis | Exact curated invalid-form card | `REJECT / INVALID_SURFACE_FORM` |
| No analysis | Proper-name or acronym contract | `ACCEPT / EXEMPT_PROPER_NAME` |
| No analysis | Authentic heritage evidence | `ACCEPT / HERITAGE_ALLOWED` for form validity |
| No analysis | Excluded role | `ACCEPT / EXCLUDED_SURFACE` |
| No analysis | СУМ-11 only | `AUDIT / SUM11_SOLE_AUTHORITY` |
| No analysis | No decisive evidence | `AUDIT / VESUM_UNATTESTED` |
| VESUM unavailable or snapshot mismatch | Eligible token | `AUDIT / VESUM_UNAVAILABLE` |
| Analysis lineage or raw-span mismatch | Any | `AUDIT / ANALYSIS_LINEAGE_CONFLICT` |

A VESUM miss alone MUST NOT be described as proof that a word “does not exist.”

Form validity acceptance does not complete the token’s `LEXICAL_USE` or clause coverage.

### 5.4 Executable local recognizers

Every local recognizer has:

```text
LocalRecognizer {
  recognizer_id: stable string
  version: string
  token_class_alphabet: closed enum
  feature_domain: non-empty tuple<feature>
  positive_conditions: non-empty tuple<predicate>
  exclusion_conditions: non-empty tuple<predicate>
  positive_fixture_ids: non-empty tuple<string>
  negative_fixture_ids: non-empty tuple<string>
}
```

A rejection is permitted only when:

```text
recognizer matched
AND every positive condition is true
AND every exclusion condition is false
AND all required analyses are complete
AND no permitted analysis tuple satisfies the feature rule
```

A dropped or unmatched shape is recorded as `UNCOVERED` or becomes a bounded residue candidate. It never silently passes.

#### 5.4.1 Prenominal modifier + noun

Recognizer: `LOCAL_PRENOMINAL_MODIFIER_NOUN_V1`

Feature domain:

```text
case
number
gender when number == singular
```

Finite-state form:

```text
LEFT_BOUNDARY MODIFIER HEAD_NOUN RIGHT_BOUNDARY
```

Positive conditions:

1. `MODIFIER` immediately precedes `HEAD_NOUN`.
2. Every modifier analysis is adjective or pronominal adjective.
3. Every head analysis is noun.
4. Neither token has a competing noun/adjective analysis.
5. The pair is within one clause and contains no punctuation.
6. The left and right token classes establish a maximal two-token noun phrase.
7. At least one complete VESUM analysis exists for each token.

Permitted left boundaries:

```text
BOS
CLAUSE_PUNCTUATION
FINITE_VERB
REGISTERED_PREPOSITION
```

Permitted right boundaries:

```text
EOS
CLAUSE_PUNCTUATION
FINITE_VERB
PREPOSITION
```

Exclusions:

- coordination;
- comma or dash;
- apposition;
- numeral phrase;
- nominalized adjective;
- vocative attachment;
- proper-name sequence;
- preceding or following modifier/head candidate;
- genitive or other dependent tail;
- ellipsis;
- any competing attachment.

Examples such as `новий і цікавий підручник`, `Черговий відповів`, and `нова школа мистецтв` are outside the recognizer unless a later version proves their structure. They become residue or `UNCOVERED`.

#### 5.4.2 Nominative personal pronoun + finite verb

Recognizer: `LOCAL_NOMINATIVE_SUBJECT_VERB_V1`

Feature domain:

```text
person and number for non-past finite verbs
number for past finite verbs
gender for third-person singular past forms
```

Positive conditions:

1. The pronoun immediately precedes the finite verb.
2. Every surviving pronoun analysis is a personal pronoun in nominative case.
3. Pronoun person and number are uniquely determined.
4. The verb is unambiguously finite.
5. The clause contains no other nominative subject candidate.
6. There is no punctuation or conjunction between the tokens.
7. The verb is not in the registered impersonal or non-nominative-experiencer registry.
8. The local clause is complete.

Exclusions:

- accusative, genitive, dative, instrumental, locative, or ambiguous pronoun;
- inverted verb–subject order;
- impersonal construction;
- dative-experiencer verb;
- relative clause;
- coordination;
- quotation boundary;
- competing nominative noun;
- elided predicate;
- ambiguous finite/non-finite form.

`Мене бачить Олена` is excluded because `Мене` is not nominative and `Олена` is a competing nominative subject.

`Їй подобаються квіти` is excluded because `Їй` is dative, `подобатися` is registered as a non-nominative-experiencer construction, and `квіти` supplies the nominative agreement controller.

Neither negative fixture may produce `AGREEMENT_IMPOSSIBLE`.

#### 5.4.3 Preposition + proven noun-phrase head

Recognizer: `LOCAL_PREPOSITION_GOVERNMENT_V1`

Feature domain:

```text
case of the proven noun-phrase head
```

Finite-state forms:

```text
PREPOSITION HEAD
PREPOSITION MODIFIER HEAD
```

Positive conditions:

1. The preposition has one lemma analysis.
2. A versioned `GovernmentCard` matches that exact lemma and local construction.
3. The card provides one closed allowed-case set.
4. The noun or pronoun head is uniquely established by the finite-state form.
5. Optional modifier agreement is independently compatible.
6. Every head analysis exposes case.
7. The phrase is complete and punctuation-free.

```text
GovernmentCard {
  card_id: string
  preposition_lemma: string
  construction_id: string
  allowed_cases: non-empty tuple<case>
  sense_preconditions: tuple<predicate>
  excluded_shapes: tuple<predicate>
  source_binding_ids: non-empty tuple<string>
  positive_fixture_ids: tuple<string>
  negative_fixture_ids: tuple<string>
}
```

Exclusions:

- multi-case preposition without a closed sense cue;
- coordination;
- apposition;
- numeral phrase;
- indeclinable or case-opaque head;
- genitive chain or competing head;
- ellipsis;
- punctuation;
- more than one possible construction card;
- incomplete NP boundary.

A preposition is never called “unambiguous” merely because it appears on a list. The head and applicable case regime must both be proven.

#### 5.4.4 Local-recognizer decisions

| Recognizer result | Feature compatibility | Decision |
|---|---|---|
| Complete positive match | At least one valid analysis tuple | `ACCEPT / LOCAL_RELATION_COMPATIBLE` |
| Complete positive match | No valid analysis tuple | `REJECT / LOCAL_RELATION_IMPOSSIBLE` |
| Exclusion condition fires | Any | `DEFER / SYNTAX_RESIDUE` |
| Shape is outside all recognizers | Any | `UNCOVERED` unless a residue candidate is generated |
| Missing or ambiguous analysis | Any | `AUDIT / ANALYSIS_INCOMPLETE` |
| Recognizer failure | Any | `AUDIT / LOCAL_RECOGNIZER_FAILED` |

## 6. Core L: lexical naturalness

### 6.1 Evidence sources, authority, and required-source predicates

| Source | Permitted role |
|---|---|
| Curated exact Антоненко card | Deterministic rejection within recorded construction and sense |
| Антоненко prose | Rule support and missing-entry recovery |
| Adjudicated UA-GEC native pair | Exact pattern evidence |
| GRAC | Computable observation and conflict discovery; never sole rejection |
| Балла EN→UK | AUDIT-only observation in v2 |
| Phraseological dictionary | Positive set-expression evidence |
| Heritage sources | False-positive and register defense |
| Russian-shadow heuristic | Candidate generation only |
| СУМ-11 | Secondary supporting or counter-evidence only |
| Auto-translated WordNet | Forbidden from authority and curated-rule ancestry |

A source is **required** when a versioned detector applicability predicate is true:

- VESUM is required for every eligible Ukrainian word except a structurally excluded role.
- The compiled Pravopys registry is required for every eligible token; an individual rule card is applicable only when its trigger matches.
- The curated lexical-rule registry is required for every `PHRASE_WINDOW` and `LEXICAL_USE`.
- UA-GEC is required only when a registered adjudicated pattern trigger matches.
- Heritage lookup is required before any VESUM-miss, Russian-shadow, unfamiliar-word, dialect, archaic, or curated-style rejection becomes final.
- GRAC is required only when a rule or observation card explicitly invokes it. A sparse or failed invoked query audits.
- Балла is required only for a registered bilingual sense-fan trigger. Its v2 result is non-rejecting and AUDIT-only.
- СУМ-11 is never required as sole authority.
- WordNet is never required and can never satisfy a source predicate.

A required-source failure produces `AUDIT` before lower-priority evidence is fused.

#### WordNet exclusion and provenance validation

Auto-translated WordNet remains excluded pending the quality work tracked by [EPIC #1657](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1657).

Every curated rule, positive card, correction card, and sense card MUST pass a transitive provenance validator:

```text
for each rule source:
  expand all ancestor_source_ids
  if any ancestor.authority_class == WORDNET_AUTO_TRANSLATED:
      reject registry entry
```

A forbidden descendant cannot be made acceptable by copying it through an intermediate file or human-unreviewed transform. If an affected registry entry reaches runtime, registry loading fails closed and applicable scan units audit.

#### СУМ-11 source contract

СУМ-11:

- MUST NOT be the sole authority for acceptance, rejection, correction, heritage status, or modern-register preference;
- MAY generate a candidate or supply historical usage context;
- MAY corroborate an already independent modern or heritage source;
- MUST be labeled `SECONDARY_SOVIET_PERIOD`;
- MUST retain exact provenance and sense spans;
- MUST NOT qualify as `MODERN_ATTESTATION_CARD`;
- MUST NOT override post-1991 normative evidence or authentic heritage evidence.

Counter-evidence rules:

1. `SUM11_ONLY` yields `AUDIT / SUM11_SOLE_AUTHORITY`.
2. A modern exact rule plus contrary СУМ-11 usage remains governed by the modern rule if no independent modern or heritage conflict exists.
3. СУМ-11 plus authentic heritage evidence uses the heritage evidence for the form-validity defense; СУМ-11 contributes no additional authority.
4. СУМ-11 conflicting with independent modern and heritage sources is attached as counter-evidence but cannot cause rejection by itself.
5. Any unresolved source-identity or sense mismatch audits.

### 6.2 UA-GEC matching

A UA-GEC pattern may reject only if:

1. The row is `F/Calque` or `F/Collocation`.
2. Error and correction spans are preserved.
3. Native-author status is recorded where required.
4. The pair is adjudicated and uncontested.
5. The target matches the registered exact or lemma-slot pattern.
6. The correction changes the same lexical relation.
7. Quoted-error and teaching-contrast exclusions do not apply.
8. Any sense restriction is resolved by a deterministic card or a valid residue candidate.
9. Heritage preflight has completed.

An uncurated FTS hit remains `lookup_heuristic`; it cannot hard-fail production.

### 6.3 Антоненко structured and prose lookups

For a Russianism or calque verification query, the plan MUST include both:

- `search_style_guide`;
- the full Антоненко prose corpus.

Absence from either source is not acceptance evidence. An exact condemnation may support a curated rule card. Conflicting, incomplete, or sense-restricted evidence audits or becomes a bounded residue candidate.

Ellipsized excerpts MUST use Layer B `ordered_segment_spans`. Cross-output stitching is forbidden.

### 6.4 GRAC contract

GRAC is observational. It contains historical, edited, unedited, quoted, contact-influenced, and erroneous language.

Every usable observation MUST contain:

```text
GracObservation {
  observation_id: sha256
  corpus_snapshot_id: string
  query_plan_version: string

  candidate_query: canonical object
  alternative_query: canonical object
  normalization_version: string

  subcorpus: string
  register: string
  time_start: integer
  time_end: integer

  candidate_occurrences: integer
  alternative_occurrences: integer
  corpus_token_count: integer

  candidate_frequency_per_million: number
  alternative_frequency_per_million: number

  candidate_distinct_document_count: integer
  alternative_distinct_document_count: integer

  aggregate_counts_complete: boolean
  matched_slot_contract_id: string
  concordance_sample_hash: sha256
  concordance_validation_complete: boolean
}
```

Candidate and alternative queries MUST use the same snapshot, subcorpus, time range, normalization, and grammatical-slot contract.

Choices required by R3:

- **Wilson interval:** removed from blocking v2. Current aggregate expression counts do not prove matched binomial exposure; no Wilson result may affect a verdict.
- **Frequency floors:** computable but non-rejecting. A floor is expressed only in `frequency_per_million`; raw counts are completeness diagnostics, not floors.
- **Strong modern attestation:** formalized below, but it can trigger conflict review only, never prove an error or automatically clear a rule.
- **Contrary-attestation escape:** implemented through versioned `ModernAttestationCard` records.
- **Балла:** AUDIT-only in v2 because cue incompatibility, ranking, and general bilingual alignment are not yet qualified.

GRAC observation states:

```text
SPARSE:
  candidate_frequency_per_million < 0.10
  AND alternative_frequency_per_million < 0.10

MODERN_ATTESTATION_OBSERVED:
  time_start >= 1991
  AND register in {"edited", "academic", "journalistic"}
  AND candidate_frequency_per_million >= 0.50
  AND candidate_occurrences >= 20
  AND candidate_distinct_document_count >= 5
  AND concordance_validation_complete == true

ALTERNATIVE_DOMINANCE_OBSERVED:
  alternative_frequency_per_million >= 1.00
  AND alternative_frequency_per_million >=
      20 * max(candidate_frequency_per_million, 0.01)
  AND alternative_occurrences >= 20
  AND alternative_distinct_document_count >= 5
  AND concordance_validation_complete == true

INCONCLUSIVE:
  every other complete result
```

These states are non-rejecting in v2:

| GRAC state | Effect |
|---|---|
| `MODERN_ATTESTATION_OBSERVED` | May initiate a curated contrary-attestation review |
| `ALTERNATIVE_DOMINANCE_OBSERVED` | May corroborate an independent rule; never rejects alone |
| Both forms attested | No corpus-only rejection |
| `SPARSE` after GRAC was required | `coverage_missing → AUDIT` |
| Historical-only attestation | Does not clear a modern rule |
| Incomplete metadata or query inconsistency | `AUDIT / GRAC_QUERY_INCONSISTENT` |
| Timeout or truncation | `AUDIT / GRAC_UNAVAILABLE` |

Sparse GRAC is not an error finding.

#### Contrary-attestation escape

A curated exact rejection is overridden to `AUDIT / SOURCE_CONFLICT` when a matching active card exists:

```text
ModernAttestationCard {
  card_id: string
  target_construction: versioned exact or lemma-slot expression
  sense_and_register_preconditions: non-empty tuple<predicate>

  grac_observation_ids: non-empty tuple<string>
  independent_modern_source_binding_ids: non-empty tuple<string>

  required_state: "MODERN_ATTESTATION_OBSERVED"
  adjudication_status: "ADJUDICATED"
  adjudicators: at least two distinct identities
  active: boolean

  positive_fixture_ids: tuple<string>
  negative_fixture_ids: tuple<string>
}
```

A card applies only on exact construction, sense, and register match. A raw GRAC hit, sparse result, or unadjudicated observation is not an escape.

The escape prevents a rare-but-valid modern form from being automatically rejected; it does not automatically accept the construction.

### 6.5 Балла sense observations

Балла result order MUST NOT be interpreted as frequency, quality, priority, or default sense.

In v2:

```text
BallaObservation {
  observation_id: sha256
  english_span_binding_id: string
  selected_ukrainian_span_id: string
  mapping_candidate_ids: tuple<string>
  source_snapshot_id: string
  result_order_ignored: true
}
```

Rules:

- A complete `EnglishSpanBinding` is mandatory.
- A failed or ambiguous binding produces `coverage_missing → AUDIT`.
- No frequency rank is constructed.
- No “incompatible” predicate is asserted.
- No cue rule may produce a deterministic rejection.
- Every applicable Балла observation produces `AUDIT / BALLA_UNQUALIFIED_V2`.
- A later phase may promote Балла only after defining and calibrating provenance-bearing cue cards, compatibility predicates, ranking, ties, and alignment.

This preserves its diagnostic value without allowing an underspecified fan to condemn learner text.

### 6.6 Heritage defense

Before rejecting an unfamiliar Ukrainian-looking word, Russian-shadow hit, or exact style-rule target, the gate MUST consult the heritage-defense layer.

| Heritage result | Effect |
|---|---|
| Authentic modern Ukrainian | Clears blanket nonword/Russianism claim |
| Authentic regional or dialectal Ukrainian | `heritage_allowed`; separate register policy may apply |
| Authentic historical or archaic Ukrainian | Clears nonword claim; modern-register use may audit |
| Authentic heritage conflicts with exact curated style rule | `AUDIT / HERITAGE_RULE_CONFLICT` with both chains |
| No evidence | Does not prove invalidity |
| Tool unavailable or incomplete | `AUDIT` if a rejection depends on it |

Lookup normalization is versioned and evidence-bearing:

```text
HeritageLookupKey {
  raw_form: string
  normalized_lookup_form: string
  normalization_rule_id: string
  normalization_source_binding_id: string
}
```

Normalization changes lookup keys only. It MUST NOT silently rewrite learner text or become a correction.

The precedent `кобета → кобіта` is represented as a versioned lookup alias with both raw and normalized forms preserved.

`коцюба` is a load-bearing negative control. Authentic evidence must prevent false nonword or Russianism rejection. The system MUST NOT substitute `кочерга` as quotation-equivalent, synonym-equivalent, or a default correction.

Heritage evidence clears blanket suspicion only. It does not prove every sense or collocation correct.

### 6.7 Total lexical fusion

Evidence is normalized into exactly one fused class:

```text
EXACT_ANTONENKO_REJECT
EXACT_UA_GEC_REJECT
EXACT_RULE_PLUS_MODERN_CONTRARY
POSITIVE_EXACT_ALLOW
AUTHENTIC_HERITAGE_DEFENSE
HEURISTIC_OR_GRAC_ONLY
BALLA_OBSERVATION
NO_DECISIVE_EVIDENCE
LINEAGE_OR_SOURCE_FAILURE
```

Context/defense state is normalized into exactly one column:

- `X`: structurally excluded surface;
- `F`: non-excluded surface with required-source or lineage failure;
- `A`: context or sense is ambiguous;
- `N`: exact context, no authentic heritage conflict;
- `H`: exact context with authentic heritage evidence.

The following table is exhaustive:

| Fused evidence class | `X` Excluded | `F` Required failure | `A` Ambiguous | `N` Exact/no heritage | `H` Exact/heritage |
|---|---|---|---|---|---|
| `EXACT_ANTONENKO_REJECT` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `DEFER` | `REJECT` | `AUDIT/HERITAGE_RULE_CONFLICT` |
| `EXACT_UA_GEC_REJECT` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `DEFER` | `REJECT` | `AUDIT/HERITAGE_RULE_CONFLICT` |
| `EXACT_RULE_PLUS_MODERN_CONTRARY` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT` | `AUDIT/SOURCE_CONFLICT` | `AUDIT/SOURCE_CONFLICT` |
| `POSITIVE_EXACT_ALLOW` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT` | `ACCEPT` | `ACCEPT/HERITAGE_ALLOWED` |
| `AUTHENTIC_HERITAGE_DEFENSE` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `ACCEPT_FORM_ONLY` | `ACCEPT_FORM_ONLY` | `ACCEPT/HERITAGE_ALLOWED` |
| `HEURISTIC_OR_GRAC_ONLY` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT` | `AUDIT/HEURISTIC_ONLY` | `ACCEPT/HERITAGE_ALLOWED` |
| `BALLA_OBSERVATION` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT/BALLA_UNQUALIFIED_V2` | `AUDIT/BALLA_UNQUALIFIED_V2` | `AUDIT/BALLA_UNQUALIFIED_V2` |
| `NO_DECISIVE_EVIDENCE` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT/COVERAGE_MISSING` | `AUDIT/COVERAGE_MISSING` | `AUDIT/COVERAGE_MISSING` |
| `LINEAGE_OR_SOURCE_FAILURE` | `ACCEPT/SUPPRESSED_FP` | `AUDIT` | `AUDIT` | `AUDIT` | `AUDIT` |

`ACCEPT_FORM_ONLY` resolves only a form-validity candidate. The containing `LEXICAL_USE` still requires contextual coverage.

Any unmapped evidence class, context state, or combination defaults to `AUDIT`.

Total precedence is:

1. Valid structural exclusion.
2. Integrity, scan, binding, lineage, and required-source failures.
3. Heritage and contrary-attestation conflicts.
4. Exact curated rejection or positive cards.
5. Qualified residue-judge result.
6. Non-decisive observational evidence.
7. No evidence → coverage audit.

No implementation may change this result by iterating sources in a different order.

## 7. Residue J: qualified cross-family judge

### 7.1 Allowed scope

The judge receives only deterministic residue candidates for:

- agreement outside executable local recognizers;
- unresolved case government;
- sense-restricted calques;
- context-dependent word choice;
- context-dependent collocation.

It MUST NOT:

- scan the complete artifact for new findings;
- decide whether an unverified word exists;
- replace Pravopys;
- use tools or retrieval;
- assign a numeric score;
- resolve facts;
- treat corpus absence as an error;
- return a finding without binding it to a supplied candidate.

### 7.2 Candidate contract

Every judge candidate MUST contain a locus and falsifiable hypothesis:

```text
GateCandidate {
  candidate_id: sha256
  candidate_class:
    "AGREEMENT" |
    "CASE_GOVERNMENT" |
    "SENSE_RESTRICTED_CALQUE" |
    "WORD_SENSE_SELECTION" |
    "COLLOCATION"

  hypothesis: {
    hypothesis_id: sha256
    type: registered enum
    target_locus_spans: non-empty tuple<raw span>
    involved_token_ids: non-empty tuple<string>
    asserted_risk: registered string
  }

  target_window: JudgeWindow
  evidence_candidate_ids: tuple<string>
  allowed_relations: non-empty tuple<relation>
  canonical_rule_family: string
}
```

A missing locus, empty hypothesis, unknown class, or empty relation set produces `AUDIT` before model dispatch.

### 7.3 Family independence

```text
judge_family != writer_family
judge_family != correction_model_family
```

Unknown lineage produces `AUDIT`. A route is eligible only after clearing the frozen Ukrainian grammar and sense-context calibration set.

### 7.4 Input and output contracts

```json
{
  "schema_version": "ua-grammar-lexical-judge-input.v2",
  "target_artifact_id": "stable-id",
  "target_artifact_sha256": "sha256",
  "candidates": [
    {
      "candidate_id": "stable-id",
      "candidate_class": "WORD_SENSE_SELECTION",
      "hypothesis": {
        "hypothesis_id": "sha256",
        "type": "WRONG_CONTEXTUAL_SENSE",
        "target_locus_spans": [
          {"start": 140, "end": 151}
        ],
        "involved_token_ids": ["token-id"],
        "asserted_risk": "selected lemma may express the wrong contextual sense"
      },
      "target_window": {
        "candidate_id": "anchor-id",
        "window_start": 120,
        "window_end": 260,
        "window_sha256": "sha256",
        "logical_unit_complete": true
      },
      "evidence_candidate_ids": ["anchor-id"],
      "allowed_relations": [
        "ACCEPTABLE",
        "WORD_CHOICE_ERROR",
        "MIXED",
        "INSUFFICIENT_CONTEXT",
        "ABSTAIN"
      ]
    }
  ]
}
```

```json
{
  "schema_version": "ua-grammar-lexical-judge-output.v2",
  "candidates": [
    {
      "candidate_id": "stable-id",
      "hypothesis_id": "sha256",
      "relation": "WORD_CHOICE_ERROR",
      "support_spans": [
        {
          "window_candidate_id": "anchor-id",
          "start": 18,
          "end": 31,
          "role": "ERROR_LOCUS"
        },
        {
          "window_candidate_id": "anchor-id",
          "start": 0,
          "end": 48,
          "role": "CONTEXT"
        }
      ],
      "confidence": "high",
      "prompt_injection_observed": false,
      "proposed_replacements": []
    }
  ]
}
```

Caller validation requires:

- exactly one output row per input candidate;
- exact `candidate_id` and `hypothesis_id` match;
- returned relation belongs to that candidate’s `allowed_relations`;
- every decisive result has valid support spans;
- at least one decisive support span overlaps a registered target locus;
- `ACCEPTABLE` includes a locus-overlapping span plus sufficient context;
- no missing, extra, or duplicate candidate;
- high confidence;
- valid hashes and offsets.

A broad-window `ACCEPTABLE` that does not bind to the candidate locus is invalid and becomes `AUDIT`.

### 7.5 Relation × candidate-class table

`A` = `ACCEPT`, `R` = `REJECT`, `U` = `AUDIT`, `I` = invalid combination → `AUDIT`.

| Relation | `AGREEMENT` | `CASE_GOVERNMENT` | `SENSE_RESTRICTED_CALQUE` | `WORD_SENSE_SELECTION` | `COLLOCATION` |
|---|---:|---:|---:|---:|---:|
| `ACCEPTABLE` | A | A | A | A | A |
| `AGREEMENT_ERROR` | R | I | I | I | I |
| `CASE_GOVERNMENT_ERROR` | I | R | I | I | I |
| `WORD_CHOICE_ERROR` | I | I | R | R | I |
| `COLLOCATION_ERROR` | I | I | I | I | R |
| `MIXED` | U | U | U | U | U |
| `INSUFFICIENT_CONTEXT` | U | U | U | U | U |
| `ABSTAIN` | U | U | U | U | U |

Any unmapped candidate class, relation, or combination defaults to `AUDIT`.

Support-span requirements:

- `AGREEMENT_ERROR` requires spans for all agreement controllers.
- `CASE_GOVERNMENT_ERROR` requires preposition/governor and governed-head spans.
- `WORD_CHOICE_ERROR` requires `ERROR_LOCUS` and sense-disambiguating context.
- `COLLOCATION_ERROR` requires every member of the condemned relation.
- `ACCEPTABLE` requires locus overlap and relevant context.
- `MIXED` requires spans for both readings.
- `INSUFFICIENT_CONTEXT` and `ABSTAIN` require empty spans.

Target text and evidence are serialized using Layer B’s delimited untrusted-data contract. Injection flags, delimiter collisions, malformed output, irrelevant offsets, medium/low confidence, timeout, lineage conflict, or budget failure produce `AUDIT`.

Suggested replacements are non-authoritative and do not affect the verdict.

## 8. Coverage and finding aggregation

### 8.1 Complete-or-AUDIT invariant

For every `ScanUnit`:

```text
set(required_detector_ids)
==
set(detector_run.detector_id for that scan_unit)
```

A unit is complete only when every required detector is:

- successfully recorded as `NOT_APPLICABLE`;
- `CLEAN`;
- `EXCLUDED`;
- or has candidates whose final decisions are all terminal `ACCEPT` or `REJECT`.

The following produce `coverage_missing`:

- missing detector;
- detector failure;
- missing or failed English-span binding;
- `UNCOVERED`;
- `UNCURATED_SENSE`;
- required sparse GRAC;
- incomplete source capture;
- unresolved candidate;
- judge failure;
- invalid role;
- mixed-script learner token;
- unknown registry or source state.

```text
artifact.result == PASS
  =>
coverage_missing == 0
AND every eligible scan unit is complete
AND every candidate == ACCEPT
```

A VESUM-valid form outside contextual or syntactic coverage remains `UNCOVERED`; it cannot vanish into PASS.

### 8.2 Minimal raw error span

Every candidate generator records the exact error-bearing token IDs. The judge cannot redefine them.

Canonical span construction:

1. Sort error-bearing tokens by raw offset.
2. Reject duplicate, overlapping, or cross-region token identities as `AUDIT`.
3. For one token, use that token’s raw span.
4. For a multi-token atomic construction, use the interval from the first token start through the final token end, including internal whitespace.
5. For an error/correction pair, tokenize both sides and remove the longest identical prefix and suffix. The remaining error-side tokens define the span.
6. If the edit has multiple disjoint regions, emit separate candidates unless a versioned rule card explicitly declares the construction atomic.
7. Agreement and government spans contain every controller and dependent token named by the recognizer or hypothesis.
8. A disagreement between detectors about the registered locus audits rather than guessing a smaller span.

### 8.3 Equivalent correction family

Every rejecting rule or candidate MUST have a registry-issued `canonical_rule_family`.

```text
correction_family_id =
  sha256(
    dimension_bucket,
    canonical_rule_family,
    normalized_registered_repair_kind
  )
```

Normalization consists only of:

- NFC;
- apostrophe normalization;
- stress-mark removal for lookup identity;
- casefolding where the rule card permits it;
- VESUM lemma identity where uniquely resolved.

Synonym inference is forbidden.

Two findings are equivalent only if their `correction_family_id` values are identical. Same-token findings from different registered families remain separate error units, even when one repair may incidentally affect both. This makes same-token multi-error accounting computable and reviewable.

An LLM-only candidate without an authoritative replacement uses its `hypothesis_id` as its repair-kind component.

### 8.4 Error units and denominator coverage

An error unit is keyed by:

```text
target_artifact_sha256
dimension_bucket
minimal_raw_error_span
correction_family_id
```

Rules:

1. Same key from multiple detectors counts once.
2. Grammar and lexical errors at the same span count once in each dimension.
3. Different correction families at one token count separately.
4. Repeated occurrences at different offsets count separately.
5. A deterministic rejection outranks a judge acceptance for the same candidate.
6. Conflicting decisive results audit.
7. Suppressed, quoted, contrast-bad, and heritage-defense dispositions do not count as errors.
8. Missing coverage never becomes zero errors.

A Ukrainian word is `scored` only when:

- its token checks are complete; and
- every required higher-order scan unit containing it has a terminal decision.

```text
eligible_ukrainian_words
  = scored_ukrainian_words
  + coverage_missing_ukrainian_words
```

For any rank-eligible scorecard:

```text
eligible_ukrainian_words == scored_ukrainian_words
coverage_missing_ukrainian_words == 0
```

An artifact with incomplete coverage may display diagnostic counts but cannot publish comparative rates.

### 8.5 Artifact aggregation

| Confirmed errors | Audits or coverage missing | Result |
|---:|---:|---|
| 0 | 0 | `PASS` |
| ≥1 | Any | `FAIL_CONTENT` |
| 0 | ≥1 | `NEEDS_AUDIT` |

Production and Atlas cutover use zero tolerance.

## 9. Evidence and scoring artifacts

### 9.1 Per-artifact evidence

```text
ua_grammar_lexical_evidence.v2 {
  artifact_kind: "gate_result"
  run_id: stable string
  gate_version: string

  target: {
    artifact_id: string
    artifact_type:
      "module" |
      "activity" |
      "vocabulary" |
      "atlas_entry" |
      "eval_output"

    content_sha256: sha256
    level_policy: string | null
    writer_model_id: string | null
    writer_family: string | null
  }

  source_snapshots: {
    vesum: string
    pravopys_rules: string
    ua_gec: string
    antonenko: string
    grac: string
    balla: string
    heritage: string
    sum11: string
  }

  surface_regions: tuple<SurfaceRegion>
  tokens: tuple<SurfaceToken>
  scan_units: tuple<ScanUnit>
  detector_runs: tuple<DetectorRun>
  candidates: tuple<GateCandidate>
  evidence_bindings: tuple<EvidenceBinding>
  findings: tuple<ua_contact_quality_evidence finding>
  audits: tuple<AuditRecord>

  coverage: {
    scan_units_total: integer
    scan_units_complete: integer
    coverage_missing: integer
    coverage_missing_by_reason: object
    eligible_ukrainian_words: integer
    scored_ukrainian_words: integer
    coverage_missing_ukrainian_words: integer
  }

  metrics: {
    confirmed_grammar_errors: integer
    confirmed_lexical_errors: integer
    unresolved_candidates: integer

    target_vocab_required: integer
    target_vocab_realized: integer
    target_vocab_coverage: number | null

    content_lemma_tokens: integer
    mattr_window: integer | null
    mattr: number | null
    reference_mattr: number | null
    lexical_diversity_retention: number | null
    flattening_flag: boolean
  }

  result: "PASS" | "FAIL_CONTENT" | "NEEDS_AUDIT"
}
```

### 9.2 Per-model scorecard and anti-flattening metrics

```text
ua_grammar_lexical_score.v2 {
  artifact_kind: "model_scorecard"

  evaluation_set_id: string
  evaluation_set_sha256: sha256
  prompt_set_sha256: sha256
  generation_config_sha256: sha256
  reference_set_sha256: sha256

  model: {
    provider: string
    model_id: string
    family: string
    revision: string | null
  }

  gate_version: string
  source_snapshot_ids: object
  output_artifact_ids: tuple<string>

  counts: {
    outputs_total: integer
    outputs_pass: integer
    outputs_fail_content: integer
    outputs_needs_audit: integer

    eligible_ukrainian_words: integer
    scored_ukrainian_words: integer
    coverage_missing_ukrainian_words: integer
    coverage_missing: integer

    grammar_error_units: integer
    lexical_error_units: integer
    unresolved_candidates: integer

    target_vocab_required: integer
    target_vocab_realized: integer
    outputs_below_target_vocab: integer
    outputs_flattened: integer
  }

  rates: {
    grammar_errors_per_1000: number | null
    lexical_errors_per_1000: number | null
    target_vocab_coverage: number | null
    aggregate_mattr: number | null
    lexical_diversity_retention: number | null
    flattening_trend_delta: number | null
  }

  reproducibility:
    "DETERMINISTIC_NO_JUDGE" |
    "DETERMINISTIC_CONDITIONAL_ON_FROZEN_GATE_OUTPUTS"

  rank_eligibility:
    "ELIGIBLE" |
    "INELIGIBLE_AUDIT" |
    "INELIGIBLE_COVERAGE" |
    "INELIGIBLE_FLATTENING"
}
```

Output invariants:

```text
outputs_total
  == outputs_pass
   + outputs_fail_content
   + outputs_needs_audit

outputs_total == count(unique(output_artifact_ids))

aggregate eligible/scored/error counts
  == exact sums of unique per-artifact records
```

Duplicate artifact IDs, missing artifacts, or sum mismatches produce `INELIGIBLE_COVERAGE`.

Rates are published only when eligible and scored word counts are equal:

```text
grammar_errors_per_1000 =
  1000 * grammar_error_units / eligible_ukrainian_words

lexical_errors_per_1000 =
  1000 * lexical_error_units / eligible_ukrainian_words
```

Judge-confirmed errors are non-deterministic-source findings. Aggregation is deterministic only conditional on frozen, validated gate outputs. The scorecard MUST NOT claim pure end-to-end determinism when a judge contributed.

#### Target-vocabulary coverage

For artifacts with a plan vocabulary set:

```text
target_vocab_coverage =
  unique required target lemmas realized in eligible learner text
  /
  unique required target lemmas
```

Required targets are minimums. A value below `1.0` marks the artifact flattened and rank-ineligible.

#### Lexical diversity

Content lemmas are uniquely resolved VESUM lemmas with POS noun, verb, adjective, or adverb. Proper names are excluded from diversity but remain in the word denominator.

For `N` content lemmas:

```text
window = min(50, N)
MATTR = mean(
  distinct_lemma_count(window_i) / window
  for every contiguous window_i
)
```

Fewer than ten content lemmas yields insufficient diversity coverage.

Each evaluation prompt has a frozen adjudicated reference output:

```text
lexical_diversity_retention =
  artifact_mattr / reference_artifact_mattr
```

An artifact is flattened when:

```text
target_vocab_coverage < 1.0
OR lexical_diversity_retention < 0.85
```

A model is `INELIGIBLE_FLATTENING` when any evaluated artifact misses required target vocabulary or aggregate diversity retention is below `0.85`.

Trend monitoring compares the same frozen evaluation set and configuration:

```text
flattening_trend_delta =
  current aggregate MATTR
  - median(previous three qualified aggregate MATTR values)
```

A delta at or below `-0.05` produces a flattening alert and qualification audit. Lower grammar-error rates cannot override flattening ineligibility.

## 10. Application points

### 10.1 V7 writer-output gate

The gate runs over parsed:

- module content;
- user-facing activity fields;
- vocabulary lemmas, translations, and examples;
- learner-facing resource text.

It runs after `parse_writer_output_strict_json()` and before downstream admission. It also runs after every correction affecting learner-facing text.

A rejected or audited output may enter a bounded correction loop. The corrected artifact receives a fresh content hash and complete scan manifest. No earlier acceptance or coverage record is reused.

### 10.2 Word Atlas and lexicon surfaces

The gate covers learner-visible:

- lemma heads;
- English-gloss links;
- translations;
- definitions;
- examples;
- usage notes;
- stylistic warnings;
- promoted grow candidates.

Raw dictionary citations are not authored curriculum prose, but their provenance remains validated.

Heritage-backed regional and historical entries remain publishable with appropriate labels. WordNet-derived synonyms never clear or condemn a candidate.

### 10.3 Model bakeoffs

Each writer output produces a sibling `*.grammar-lexical.json` artifact. [`bakeoff_aggregate.py`](../../../scripts/audit/bakeoff_aggregate.py) consumes them and adds:

- grammar errors per 1,000 Ukrainian words;
- collocation/calque errors per 1,000 Ukrainian words;
- coverage missing;
- target-vocabulary coverage;
- lexical-diversity retention;
- flattening status.

Grammar and collocation/calque rates remain independent leaderboard dimensions. A missing, audited, coverage-incomplete, or flattened output is rank-ineligible.

Word-count and plan gates remain load-bearing so a model cannot improve rates by producing too little Ukrainian.

## 11. Failure-mode analysis

| Failure class | Required handling |
|---|---|
| Invented word absent from VESUM | Reject only with exact invalid-form evidence; otherwise audit |
| VESUM-valid form used in the wrong context | Context unit or syntax unit must resolve; otherwise coverage audit |
| Homograph with multiple analyses | Residue candidate or audit |
| VESUM used as a parser | Forbidden |
| Regex ending treated as grammar proof | Forbidden |
| Proper name absent from VESUM | Proper-name contract; otherwise audit |
| Authentic dialect word flagged as Russianism | Heritage defense |
| `кобета` lookup misses `кобіта` | Versioned heritage lookup normalization |
| `коцюба` replaced with `кочерга` | Forbidden synonym substitution |
| Archaic word in quotation | Excluded/heritage disposition |
| Archaic word in modern instruction | Register warning or audit, not nonword |
| Exact Pravopys violation | Versioned rule card |
| Uncompiled orthographic intuition | Audit or uncovered |
| Pronoun object mistaken for subject | Local recognizer exclusions |
| Dative experiencer mistaken for subject | Local recognizer exclusions |
| Modifier attachment guessed from adjacency | Local recognizer exclusions |
| Preposition case guessed without a head | Local recognizer exclusions |
| Corpus-zero phrase | Never reject from absence |
| Sparse GRAC result | Coverage audit if invoked; no error finding |
| GRAC expression counts treated as matched binomial trials | Forbidden |
| GRAC mode inconsistency | Audit |
| Rare modern form conflicts with curated rule | `ModernAttestationCard` escape → audit |
| UA-GEC near-match treated as exact | Diagnostic or audit |
| No Антоненко structured hit | Prose lookup still required |
| СУМ-11 used as sole authority | Forbidden; audit |
| СУМ-11 overrides modern/heritage evidence | Forbidden |
| WordNet lineage enters a rule card | Registry validation failure |
| Балла first result treated as correct | Forbidden |
| Балла ordering treated as frequency | Forbidden |
| A1 English gloss flagged as calque | Surface-role suppression |
| Ukrainian side of bilingual pair skipped | Coverage failure |
| Mixed-language block assigned one coarse role | Forbidden |
| Bad form taught as contrast | Bad side excluded; correction side scanned |
| Multiple detectors count one occurrence repeatedly | Correction-family deduplication |
| Same-token distinct errors collapse accidentally | Separate registered families |
| Judge introduces a new finding | Invalid response → audit |
| Judge returns broad-window `ACCEPTABLE` | Invalid unless locus-bound |
| Same-family judge approves writer | Audit |
| Prompt injection | Layer B delimiter and screening contract |
| Invalid support offsets | Audit |
| LLM correction applied without re-gating | Forbidden |
| Partial scan | Coverage audit |
| Audit shown as low error rate | Rank-ineligible |
| Writer narrows vocabulary to game the gate | Target-coverage and diversity ineligibility |
| Writer repeats safe lemmas across revisions | Trend alert and qualification audit |

## 12. Test plan

### 12.1 Contract, lineage, and coverage

1. Accept a complete valid gate and score artifact.
2. Reject unknown enums and schema versions.
3. Require stable content, source, candidate, region, and scan-unit hashes.
4. Reject missing or duplicate candidate IDs.
5. Reject inconsistent source identity.
6. Reject incomplete scan presented as PASS.
7. Reject a missing required detector record.
8. Accept explicit `NOT_APPLICABLE` only after its predicate ran.
9. Convert detector timeout to `coverage_missing`.
10. Convert `UNCURATED_SENSE` to `coverage_missing`.
11. Convert failed bilingual binding to `coverage_missing`.
12. Convert required sparse GRAC to `coverage_missing`.
13. Verify raw-to-normalized offset round trips.
14. Reject cross-output evidence stitching.
15. Verify `eligible = scored + coverage_missing_words`.

### 12.2 Surface-role fixtures

16. Vocabulary row:

```text
hard | складний | Це складне завдання.
```

Expected: `hard` is excluded English; `складний` and the Ukrainian example receive full checks.

17. Vocabulary negative:

```text
hard | складний | Це складний завдання.
```

Expected: English remains excluded; Ukrainian modifier–noun disagreement rejects.

18. Bilingual dialogue:

```text
Олена: Я беру участь у гуртку. — I take part in the club.
```

Expected: speaker label separated; Ukrainian utterance fully scanned; English excluded; binding complete.

19. Dialogue with an undeclared dash separator.

Expected: no guessed bilingual split; `UNKNOWN_ROLE → AUDIT`.

20. Mixed grammar note:

```text
Use «Я беру участь у гуртку» for “I take part in the club.”
```

Expected: English tokens excluded; quoted Ukrainian example fully scanned.

21. Teaching contrast:

```text
Кажемо «Я беру участь», а не *«Я приймаю участь».
```

Expected: correct side scanned; intentionally bad side receives `TEACHING_CONTRAST_BAD` and no authored-content penalty.

22. A1 gloss:

```text
hard — складний
```

Expected: English never calque-flagged; Ukrainian form and lexical use remain eligible.

23. Code, URL, metadata, and JSON-key exclusions.

24. Mixed-script learner token produces `INELIGIBLE_COVERAGE`.

### 12.3 Morphology, tokenizer, and orthography

25. Tokenizer input:

```text
Київ — 20-річний проєкт; будь-хто й п’ять, 2026, UAБ.
```

Expected:

- eligible Ukrainian words: `Київ`, `20-річний`, `проєкт`, `будь-хто`, `й`, `п’ять` = 6;
- `2026` excluded as a standalone numeral;
- `UAБ` is one mixed-script failure, not silently split;
- proper name `Київ` counts.

26. Apostrophe variants normalize for lookup but preserve raw offsets.

27. VESUM-attested form accepts form validity only.

28. VESUM miss plus exact invalid-form card rejects.

29. VESUM miss with no decisive evidence audits.

30. Proper-name and acronym exemptions.

31. Modern versus archaic-only VESUM metadata.

32. Pravopys rule-card positive, negative, and exception fixtures.

33. VESUM or Pravopys snapshot failure audits.

### 12.4 Executable local-recognizer fixtures

34. `нова книжка` → compatible modifier–noun relation.

35. `новий книжка` → `REJECT / LOCAL_RELATION_IMPOSSIBLE`.

36. `новий і цікавий підручник` → coordination exclusion; residue or uncovered, never deterministic rejection.

37. `Черговий відповів.` → nominalized adjective exclusion.

38. `нова школа мистецтв` → competing dependent-tail exclusion.

39. `Я читаю.` → compatible nominative subject–verb relation.

40. `Я читає.` → impossible person/number relation.

41. `Мене бачить Олена.` → excluded from subject recognizer; no false agreement rejection.

42. `Їй подобаються квіти.` → dative-experiencer exclusion; no false agreement rejection.

43. `без цукру` with a matching government card → compatible.

44. `без цукор` with complete incompatible analyses → reject.

45. `за столом` without a closed sense card → residue or uncovered, never guessed.

46. `без цукру й молока` → coordination exclusion unless a later recognizer covers it.

47. Missing NP-head analysis → audit.

### 12.5 Lexical, GRAC, Балла, and fusion fixtures

48. Exact `приймати участь` curated rule in authored target prose → reject.

49. Correct `брати участь` positive card → accept corresponding lexical unit.

50. Exact rule in quoted bad-form role → suppressed.

51. Exact rule plus authentic heritage evidence → `AUDIT / HERITAGE_RULE_CONFLICT`.

52. Exact rule plus matching active `ModernAttestationCard` → `AUDIT / SOURCE_CONFLICT`, never reject.

53. Raw modern GRAC hits without a card do not override an exact rule.

54. GRAC candidate and alternative both below `0.10` per million after a required query → `SPARSE_EVIDENCE`, coverage audit, zero error units.

55. GRAC alternative dominance alone → no rejection.

56. GRAC query-mode or snapshot mismatch → audit.

57. UA-GEC exact adjudicated `F/Collocation` match → reject if all preconditions hold.

58. UA-GEC FTS near-match → diagnostic or audit, not reject.

59. Structured Антоненко miss plus prose hit remains eligible for rule curation.

60. Балла input:

```text
hard — твердий / складний / важкий
```

Expected in v2: result ordering ignored; no frequency rank or incompatibility decision; applicable observation yields `AUDIT / BALLA_UNQUALIFIED_V2`.

61. Балла observation with failed English-span binding → coverage audit before observation use.

62. Any unrecognized fusion combination → AUDIT.

### 12.6 Source-contract and heritage traps

63. WordNet provenance trap:

```text
CuratedRuleCard.source
  -> intermediate-generated-list
  -> auto-translated-wordnet
```

Expected: transitive provenance validator rejects the rule card; it cannot enter the curated registry.

64. СУМ-11 sole-authority trap:

```text
target form: VESUM miss
evidence: SUM11_SUPPORT only
```

Expected: `AUDIT / SUM11_SOLE_AUTHORITY`, never accept or reject.

65. СУМ-11 counter-evidence trap:

```text
target: приймати участь
evidence:
  exact modern curated rejection card
  contrary SUM11 usage attestation
  no independent modern contrary card
  no heritage conflict
```

Expected: exact modern rule remains `REJECT`; СУМ-11 does not qualify as a contrary-attestation escape.

66. Heritage lookup-normalization trap:

```text
raw lookup form: кобета
registered lookup alias: кобета -> кобіта
```

Expected: raw form preserved; normalized lookup key used; authentic heritage result clears blanket nonword/Russianism suspicion; no silent text rewrite.

67. Heritage no-false-nonword trap:

```text
Коцюба стояла біля печі.
```

Expected: authentic heritage evidence prevents nonword or Russianism rejection.

68. Heritage no-synonym-substitution trap:

```text
candidate token: коцюба
proposed substitution: кочерга
```

Expected: substitution is rejected as non-authoritative; the two words are never treated as quotation-equivalent or automatically interchangeable.

### 12.7 Residue-judge fixtures

69. High-confidence agreement error with exact candidate and locus binding.

70. High-confidence acceptable relation with a locus-overlapping span.

71. Broad-window `ACCEPTABLE` that does not overlap the candidate locus → audit.

72. Returned relation absent from `allowed_relations` → audit.

73. Wrong `hypothesis_id` → audit.

74. Missing, extra, and duplicate candidate rows → audit.

75. Invalid or irrelevant support offsets → audit.

76. `WORD_CHOICE_ERROR` without sense-disambiguating context → audit.

77. `CASE_GOVERNMENT_ERROR` without governor and head spans → audit.

78. Medium or low confidence → audit.

79. Same-family or unknown-family route → audit.

80. Prompt injection requesting `ACCEPTABLE` → audit.

81. Fake delimiter content → audit.

82. Timeout, malformed JSON, lineage conflict, and budget failure → audit.

83. LLM-proposed correction must pass a fresh complete gate before use.

### 12.8 Scoring and anti-flattening fixtures

84. Three detectors reporting the same correction family and span count once.

85. Independent grammar and lexical families on one token count separately.

86. Two distinct grammar families on one token count separately.

87. Repeated occurrences at different offsets count separately.

88. English glosses and quoted bad forms are excluded from the denominator.

89. Proper names in ordinary target prose count in the denominator.

90. Exact per-1,000 formulas with complete coverage.

91. Rates become null and row rank-ineligible when eligible and scored counts differ.

92. Verify output-total, sum, and unique-artifact invariants.

93. Any audit makes the model row rank-ineligible.

94. Required target vocabulary omitted despite low error rate → `INELIGIBLE_FLATTENING`.

95. Output with diversity retention below `0.85` → `INELIGIBLE_FLATTENING`.

96. Three-run aggregate MATTR drop of at least `0.05` → trend audit.

97. Frozen judge outputs reproduce identical counts; regenerated judge calls are not claimed deterministic.

98. One reject or coverage audit prevents production PASS.

## 13. Calibration and rollout

### Phase 0 — labels and schemas

Freeze a labeled union containing:

- UA-GEC `F/Calque`, `F/Collocation`, `G/Case`, and `G/Gender`;
- curated phrase and sense-restricted rules;
- VESUM-valid and VESUM-gap forms;
- all local-recognizer positive and adversarial probes;
- English polyseme cases;
- all surface-role and bilingual-binding forms;
- A1 gloss and teaching-contrast negatives;
- heritage, dialect, archaism, WordNet, and СУМ-11 traps;
- coverage-missing cases;
- lexical-flattening controls.

Every label records:

- raw spans and token IDs;
- complete scan units and required detectors;
- detector outcomes;
- correction spans where applicable;
- evidence candidate IDs;
- candidate locus and hypothesis;
- adjudication status;
- qualification eligibility.

Cases from one lexical or correction family MUST NOT cross train, development, and held-out splits.

### Phase 1 — offline shadow

Publish by model, level, surface role, and failure class:

- scan units and detector completion;
- `coverage_missing` by reason;
- deterministic candidates;
- judge residue;
- confirmed errors;
- audits;
- false accepts and false rejects;
- source coverage;
- judge calls, latency, tokens, and cost;
- grammar and lexical rates;
- target-vocabulary coverage;
- MATTR and diversity retention;
- flattening flags and trend.

GRAC frequency observations and Балла remain non-rejecting. Tool failures cannot be omitted.

### Phase 2 — qualification thresholds

Blocking requirements:

- 100% correct complete-or-AUDIT behavior on missing-detector and partial-scan probes.
- 100% on orthography, exact curated calque, local-recognizer adversarial negatives, quoted bad forms, teaching contrasts, A1 glosses, bilingual segmentation, heritage, WordNet, СУМ-11, delimiter, injection, and scoring-integrity traps.
- Zero WordNet-authority decisions.
- Zero СУМ-11 sole-authority decisions.
- Zero corpus-absence rejections.
- Zero false subject-agreement flags on `Мене бачить Олена` and `Їй подобаються квіти`.
- At least 95% precision for confirmed errors overall.
- At least 90% precision in every residue class.
- At least 95% recall on held-out blocking errors.
- Support-span F1 of at least 90%.
- Audit rate no greater than 15% overall and 25% on sense-context candidates.
- Zero unsafe accepts in at least 300 adversarial positive rows.
- Zero false rejects in at least 300 heritage/A1/quotation negative controls.
- Zero observed vocabulary-target omissions in rank-eligible rows.
- No qualified row with lexical-diversity retention below `0.85`.
- No V7, Atlas, QG-schema, or bakeoff regression.

GRAC or Балла may gain stronger roles only through a later independently reviewed contract and labeled qualification run. Their v2 behavior remains fixed until then.

### Phase 3 — canary

Canary:

- early A1 with designed English scaffolding;
- later core;
- advanced core;
- seminar;
- Atlas enrichment batch;
- fixed writer bakeoff cell.

Requirements:

- two consecutive green runs;
- identical deterministic findings on replay;
- no unresolved audit or coverage gap;
- complete target-vocabulary realization;
- no flattening flag;
- fresh evidence after any gate, prompt, model, source snapshot, tokenizer, schema, delimiter, parser, or registry change;
- corrections fully re-gated.

### Phase 4 — cutover

Enable V7 and Atlas blocking only after qualification and canaries pass.

Operational rules:

- one confirmed learner-facing defect rejects;
- one unresolved audit or coverage gap prevents shipping;
- any unsafe false accept disarms the active gate;
- any surface-partition regression disarms the active gate;
- source or model changes invalidate affected cache rows;
- cache identity includes content hash, regions, tokens, scan units, rule versions, source snapshots, judge family/model, prompt/delimiter version, and label-set hash;
- maintain a one-step rollback to shadow mode.

## 14. First PR scope

The first PR MUST contain only:

- `docs/projects/ua-eval-harness/grammar-lexical-gate-design.md`;
- `schemas/ua-grammar-lexical-evidence.v2.schema.json`;
- `schemas/ua-grammar-lexical-score.v2.schema.json`;
- schema validation tests and golden fixture skeletons if explicitly included in the approved Phase 0 scope.

It MUST NOT modify:

- V7 runtime or writer dispatch;
- audit thresholds;
- `scripts/audit/config.py`;
- VESUM behavior;
- Atlas manifests or enrichment code;
- bakeoff aggregation;
- reviewer prompts or routes;
- generated audit, status, review, or telemetry artifacts.

A partial fixture set MUST declare:

```text
qualification_eligible = false
```

and enumerate its missing coverage.

## 15. Open questions for later phases

1. Which additional UA-GEC `G/*` families have sufficiently reliable adjudicated labels?
2. Which additional local syntax recognizers can prove attachment without becoming an undeclared parser?
3. What GRAC interface changes are needed for stable register, document-identity, and query-consistency evidence?
4. How should modern and historical registers be weighted for seminar prose without weakening heritage defense?
5. What independently reviewed contract could qualify Балла cue cards, compatibility predicates, and ties after v2?
6. Which route matrix clears the frozen grammar and sense-context set while preserving cross-family independence?
7. Should `MIXED` remain permanently audit-only?
8. When should authentic regional Atlas entries receive a visible usage label rather than promotion failure?
9. Which corrections are safe for deterministic application after exact-card verification?
10. What evaluation-set sizes stabilize per-model error and lexical-diversity comparisons?
11. Should a later leaderboard add an explicitly calibrated composite, or retain separate grammar, lexical-error, target-coverage, and diversity dimensions?
