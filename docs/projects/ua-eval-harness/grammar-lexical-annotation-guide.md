# Ukrainian grammar and lexical annotation guide

This guide operationalizes the Phase 0 data contracts in
[the grammar and lexical gate design](grammar-lexical-gate-design.md). It
defines labels and static validation only. It does not authorize runtime work,
writer dispatch, audit-threshold changes, source behavior changes, scoring, or
judge routing.

## Scope and frozen inputs

The labeling lead freezes the input artifact, source snapshots, detector and
registry versions, and skeleton dataset before annotation. Record their stable
identities and SHA-256 digests in the evidence artifact. Do not replace a
captured source result with a search summary, a recollection, a newly generated
answer, or a synonym.

Phase 0 is deliberately not qualification-ready. Each partial skeleton dataset
sets `qualification_eligible: false` and lists its missing coverage. It is not
evidence that the gate is implemented, calibrated, or eligible to block
learner-facing content.

## Twelve-step labeling procedure

1. **Freeze the case.** Record the artifact hash, source snapshots, input text,
   parser version, and planned detector versions before assigning labels.
2. **Partition every visible surface.** Create ordered, raw-mappable,
   non-overlapping `SurfaceRegion` records that cover every user-visible code
   point. A gap, overlap, invalid offset, or learner-visible `UNKNOWN_ROLE` is
   coverage missing, never a pass.
3. **Assign roles structurally.** Use only the registered role methods:
   `STRUCTURED_FIELD`, `TABLE_COLUMN`, `EXPLICIT_LANGUAGE_TAG`,
   `EXPLICIT_BILINGUAL_SEPARATOR`, `INLINE_UKRAINIAN_RUN`, and
   `QUOTATION_CONTRACT`. Do not infer a bilingual relationship from proximity.
4. **Tokenize after roles are known.** Keep raw spans and hashes. English gloss
   tokens, citation-only text, code, and metadata do not enter the Ukrainian
   denominator. Ukrainian target text still receives all applicable scans.
5. **Materialize the finite scan manifest.** For each eligible token, lexical
   use, phrase window, finite clause, local shape, bilingual pair, and
   disposition, record every required detector. An omitted detector record is
   not `NOT_APPLICABLE`.
6. **Record outcomes before fusion.** Every detector run has an applicability
   state and one registered outcome. `UNCOVERED`, `UNCURATED_SENSE`,
   `BINDING_FAILED`, required `SPARSE_EVIDENCE`, and `FAILED` remain visible as
   coverage missing.
7. **Bind evidence immutably.** Each `EvidenceBinding` points to its immutable
   Layer B candidate and records exact source role, authority class, target
   spans, snapshot, and ancestors. A missing, truncated, mismatched, ambiguous,
   or forbidden-provenance source audits.
8. **Label local recognizers conservatively.** Assign a deterministic
   compatibility or impossibility decision only when the registered local
   recognizer has a complete positive match and all exclusion conditions are
   false. Otherwise record residue, uncovered coverage, or audit; do not parse
   the sentence by intuition.
9. **Fuse lexical evidence in the fixed precedence order.** Structural
   exclusion and required-source integrity come first; heritage and modern
   contrary-attestation conflicts precede exact rule outcomes. GRAC and Балла
   are observational in v2 and cannot reject by themselves.
10. **Bind residue candidates.** A `GateCandidate` needs a candidate class,
    locus spans, falsifiable hypothesis, target window, and closed allowed
    relation set. An LLM output is valid only when it stays inside that supplied
    candidate and relation contract.
11. **Account for coverage and errors separately.** A word is scored only when
    its token and every required containing higher-order unit are terminal.
    Preserve `eligible_ukrainian_words`, `scored_ukrainian_words`, and
    `coverage_missing_ukrainian_words` so the identity
    `eligible = scored + coverage_missing` can be checked.
12. **Mark qualification honestly.** Record adjudication status and all missing
    fixture families. Do not call a partial set eligible or publish comparative
    rates when coverage is incomplete.

## Surface-role probes

Use the design §12.2 probes as structural labels, not prose judgments.

- In `hard | складний | Це складне завдання.`, the first field is
  `ENGLISH_GLOSS`; the Ukrainian headword and example are targets.
- For the bilingual dialogue `Олена: Я беру участь у гуртку. — I take part in
  the club.`, separate the speaker label, Ukrainian utterance, and English
  translation only when the field contract declares the separator.
- In `Use «Я беру участь у гуртку» for “I take part in the club.”`, classify the
  embedded Ukrainian run independently from the English explanation.
- In `Кажемо «Я беру участь», а не *«Я приймаю участь».`, preserve the correction
  side as Ukrainian target text and the intentionally bad side as
  `TEACHING_CONTRAST_BAD`; the latter is not an authored-content error.
- In `hard — складний`, English remains excluded from Ukrainian calque scoring,
  while the Ukrainian side stays eligible for form and lexical-use coverage.

Never guess an undeclared dash separator, flatten a mixed-language block into a
single coarse role, or silently split a mixed-script learner token.

## Local-recognizer probes

The §12.4 fixtures label recognizer boundaries as carefully as positive cases.
`нова книжка`, `Я читаю.`, and `без цукру` test compatible registered shapes;
`новий книжка`, `Я читає.`, and `без цукор` test complete incompatible shapes.

The adversarial probes are equally binding: `новий і цікавий підручник`,
`Черговий відповів.`, `нова школа мистецтв`, `Мене бачить Олена.`, `Їй
подобаються квіти.`, `за столом`, and `без цукру й молока` must not become
invented deterministic grammar failures. Label the documented exclusion,
residue, uncovered coverage, or audit outcome.

## Lexical and source-contract probes

Exact curated evidence can decide only its recorded construction and sense.
The `приймати участь` / `брати участь` rows test rejection and positive allowance
in their stated roles. A quoted bad-form role suppresses an otherwise exact
rule. A matching heritage conflict or active `ModernAttestationCard` changes an
otherwise exact rejection to audit; raw GRAC observations do not.

Use the evidence-source restrictions exactly:

- WordNet auto-translation is forbidden in every transitive curated-rule
  ancestry. The WordNet provenance trap rejects the rule card before it enters a
  registry.
- СУМ-11 is `SECONDARY_SOVIET_PERIOD` support only. `SUM11_SUPPORT` alone is
  `AUDIT / SUM11_SOLE_AUTHORITY`; contrary СУМ-11 use does not overrule an
  independent modern exact rule.
- Preserve both raw and normalized heritage lookup forms for `кобета -> кобіта`.
  Lookup normalization does not rewrite learner text.
- `коцюба` is a negative control against a false nonword or Russianism claim;
  `кочерга` is not a quotation-equivalent or automatic substitution.
- Балла result order has no frequency or correctness meaning. A complete
  applicable observation remains `AUDIT / BALLA_UNQUALIFIED_V2` in v2.

## Coverage and flattening controls

Label a complete-or-audit outcome for every required scan unit. Missing
detectors, failed bilingual bindings, sparse required GRAC, unresolved residue,
unknown roles, mixed-script learner tokens, and source or registry failures are
coverage missing. They must not be converted into zero errors.

Record target-vocabulary realization and lexical-diversity fields even when no
rate can be published. A target-vocabulary coverage below `1.0` or lexical
diversity retention below `0.85` is flattening and makes the scorecard
`INELIGIBLE_FLATTENING`; lower grammar or lexical error counts cannot override
that status.

## Validation boundary

Validate evidence with
`schemas/ua-grammar-lexical-evidence.v2.schema.json` and scorecards with
`schemas/ua-grammar-lexical-score.v2.schema.json`. JSON Schema checks closed
shape, required fields, registered enums, and SHA-256 syntax. The Phase 0
contract tests additionally check representative coverage and output-total
invariants and round-trip the data-only golden skeletons. Those tests are not
gate runtime logic.
