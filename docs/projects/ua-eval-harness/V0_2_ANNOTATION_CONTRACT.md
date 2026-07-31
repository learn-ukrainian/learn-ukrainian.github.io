# v0.2 annotation and adjudication contract

The v0.2 review packet is a deterministic, evaluation-only queue derived from
the frozen v0.1.1 evidence. It does not add an item, alter an item, run a model,
or decide that a source, reference, or model output is linguistically correct.
Its freeze-manifest receipt is
`b95edea210ae9133059181a4e2d161c8682108bfcacdde50f98adaae2221e65f`.

## Queue and data boundary

`build_v02_review_packet.py` selects the union, once per item and in the frozen
evidence order, of `needs_ua_review`, possible benchmark-defect, and protected
variation-risk signals. It meta-validates `annotation_schema_v1.json` as a
Draft 2020-12 schema and structurally validates every row before it writes a
packet. The v0.1.1 counts are 14, 12, and 3; their union is 14.
The intersections are review/defect 12, review/protection 3,
defect/protection 1, and all three 1. Every generated row is `pending`, has no
decision, retains item/source/freeze receipts, and is evaluation-only. It must
not enter a training or export view.

Exact source-span/replacement measurements, dictionary markers, and saved model
responses are evidence only. They are not linguistic truth or an adjudication.
The packet's blind reviewer view excludes model names, outputs, and measurement
winner; its coordinator metadata is for queue routing and must not be shown to
the first reviewer.

## Reviewer protocol

Two independent qualified Ukrainian humans review the blinded source and the
available frozen references before seeing routing signals. A qualified reviewer
is a native/near-native Ukrainian editor, credentialed Ukrainian linguist, or
otherwise qualified Ukrainian language reviewer, with a stable identity and
qualification evidence. An AI agent, model output, or an unverified claim of
language ability cannot satisfy this role.

Each final import record preserves exactly two independent first-pass reviews,
each with a distinct qualified-human identity, qualification evidence, source
citations, rationale, uncertainty, and proposed decision. The record then has
one final disposition, so it remains one packet-ordered row per item.
`unresolved` is a valid final outcome and is required whenever evidence does
not support a confident adjudication. Synthetic fixtures carry
`test_fixture: true`; the importer rejects them outside tests. A protected
variation includes heritage, regional, dialectal, register, archaic, or marked
use that must not be silently normalized. Multiple references are alternative
frozen reference targets, not a license to infer a single preferred form
without contextual evidence.

The allowed vocabulary is deliberately exclusive: `benchmark_defect` (the
benchmark/reference needs repair), `valid_alternative` (a proposed or source
form is acceptable), `model_error` (the model output is wrong in context),
`protected_variation` (a protected form must not be normalized), and
`unresolved`. A `benchmark_defect` or `protected_variation` decision requires
the corresponding packet signal, preventing an importer from inventing a
contradictory disposition.

If reviewers disagree, preserve both blinded decisions and send the item,
citations, uncertainty, and conflict statement to a third qualified Ukrainian
adjudicator. The third reviewer has a distinct identity and does not see first
reviewer identities or model measurements. A disagreement can be finalized
only with that third-human adjudication or an `unresolved_conflict` final
resolution; do not coerce a majority outcome. A third-human resolution carries
the full third review (identity, qualification evidence, proposed decision,
citations, rationale, and uncertainty). Its final decision, citations,
rationale, and uncertainty must exactly match that review. A third reviewer
who remains unresolved must use `unresolved_conflict`, not adjudication.

## Import and validation

`reviewer_decision_schema_v1.json` is enforced with Draft 2020-12 JSON Schema
before cross-record checks. `validate_v02_annotations.py --decisions FILE`
fails if that schema is unavailable or invalid, then checks the packet-ordered
import. It rejects structural violations (including unknown fields and invalid
citation kinds), missing, extra, duplicate, reordered, source-mismatched,
contradictory, uncited, and unqualified decisions. A completed decision cannot
be synthesized from packet evidence: it must come from real qualified humans.

The schemas are portable structural contracts; the validator supplies the
cross-row checks JSON Schema cannot express. Decisions remain outside model
generation and all training/export paths.
