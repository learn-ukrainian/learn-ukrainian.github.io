# QG Layer B annotation guide

This guide operationalizes the `qg-layer-b-labels.v2` sidecar in [the Layer B
design](layerb-entailment-gate-design.md). It is a Phase 0 labeling contract;
it does not authorize runtime changes to Layer A, scoring, shadow execution, or
judge routing.

## Scope and roles

The labeling lead freezes inputs, builds the candidate union, and assigns two
independent annotators. Each annotator records the complete case independently.
An adjudicator resolves material disagreement without rewriting either original
record. The labeler must use the frozen audit artifact, fixture set, captured
tool outputs, and the versioned schema. Do not use a search result, a summary,
or a model recollection in place of the captured raw output.

The population is a set union, not a sum: all v1-reject/v2-effective
recoveries, regressions, abstains, gold-false incremental candidates, currently
unlabeled recoveries, and a stratified control sample from both-gates-accept and
both-gates-reject rows. Re-derive membership and counts from
`audit/2026-07-09-qg-shadow-baseline/baseline-effective-tau075.md` at labeling
time; the design's baseline counts are not a substitute for that derivation.

## Twelve-step procedure

1. **Freeze the evidence.** Record the SHA-256 of every audit artifact and
   fixture set in `source_artifacts`. Record each case's `artifact_sha256` and
   do not relabel against a changed artifact.
2. **Label truth separately.** Set `claim_is_true` from the fixture's fact
   label before examining provenance. It is not evidence that the reviewer
   excerpt was present, complete, or entailing.
3. **Enumerate before deciding.** Search every captured output for every valid
   occurrence assignment. Create one `candidates_by_event_output_id` entry per
   matching event output before assigning `ANCHOR`, `REJECT`, or `AUDIT`.
4. **Record exact spans.** For each excerpt fragment, record half-open
   normalized-excerpt, normalized-output, and raw-output code-point offsets,
   plus SHA-256 values for both extracted segment strings.
5. **Prove same-output multi-span provenance.** For an ellipsized excerpt,
   confirm every non-empty fragment belongs to the same event-output map key,
   remains in excerpt order, and does not overlap another segment. A cross-event
   join is `REJECT` with `CROSS_EVENT_STITCH_FORBIDDEN`.
6. **Record completeness independently.** Set case-level
   `anchor_scan_complete` and `candidate_set_complete` independently from every
   candidate's `output_capture_complete` and `anchor_scan_complete`. Any
   incomplete enumeration, scan, or captured output is not an `ANCHOR`.
7. **Classify source and errors.** For every candidate, label `eligibility` and
   `error_status` from the structured tool envelope before considering flattened
   text. A potentially ambiguous error string stays ambiguous; do not convert it
   into evidence.
8. **Judge raw source, not the excerpt.** Label `expected_source_relation`
   against the candidate's raw captured output. The reviewer excerpt establishes
   possible provenance only; it is never a replacement for source text.
9. **Mark decisive support.** When the expected relation is entailment,
   contradiction, explicit uncertainty, or mixed, record non-empty half-open
   `expected_support_spans` and their roles. Do not label a plausible but
   irrelevant offset as support.
10. **Use two annotators.** Two annotators complete all decision-bearing fields
    independently: candidate membership, offsets, hashes, completeness,
    eligibility/error, relation, spans, and aggregate decision.
11. **Adjudicate every disagreement.** Compare the independent records against
    the frozen raw evidence. Record `AGREED` when no material discrepancy
    exists; otherwise a named adjudicator records `ADJUDICATED` and a rationale.
    If it cannot be resolved, record `UNRESOLVED` and add an explicit
    qualification blocker. Unresolved cases remain ineligible for qualification.
12. **Re-probe fixture-only facts.** Independently re-probe any fact whose only
    support is a fixture before allowing it to gate a content decision. Keep the
    sidecar bound to the original frozen artifact while preserving the re-probe
    evidence in the annotation record.

## `corpus_verification_status` decision rule

Use `VERIFIED` only after an independent re-probe of the configured corpus
confirms the fact being used for a content decision. Use `FIXTURE_ATTESTED` when
the frozen fixture attests the fact but no independent re-probe has confirmed
it. Use `UNVERIFIED` when verification is required but absent, failed, or
inconclusive. Use `NOT_APPLICABLE` only when the case does not gate a corpus
content fact.

`FIXTURE_ATTESTED` and `UNVERIFIED` cannot silently authorize a content-gating
decision: retain a qualification blocker until the required independent re-probe
has succeeded. A completed re-probe changes the status to `VERIFIED`; it does
not retroactively alter frozen artifact hashes.

## Two-annotator adjudication flow

```text
Frozen artifacts and outputs
            |
            v
 Annotator A ----------- Annotator B
            |               |
            +---- compare --+
                    |
         same material fields? ---- yes --> AGREED (adjudicator: null)
                    |
                    no
                    v
    named adjudicator checks frozen raw evidence
             |                         |
          resolved                  unresolved
             |                         |
             v                         v
   ADJUDICATED + rationale    UNRESOLVED + qualification blocker
```

Material fields include all identities and hashes, candidate completeness,
segment offsets, expected Layer A result, eligibility/error status, source
relation, support spans, aggregate relation, and fact-check decision. Cosmetic
wording may be normalized only when it changes none of those fields.

## Validation boundary

Validate the sidecar with
`schemas/qg-layer-b-labels.v2.schema.json`. JSON Schema validates shape, known
enums, SHA-256 syntax, and `ANCHOR` completeness. The Phase 0 schema test helper
additionally validates source-byte-dependent and cross-field properties that a
standard JSON Schema cannot express: hash contents, normalized-to-raw
round-trips, strict half-open spans, segment order and non-overlap, one output
per candidate, diagnostic-only source indexes, and canonical-source identity
consistency. That helper is a label-contract check only, not a Layer A runtime
implementation.
