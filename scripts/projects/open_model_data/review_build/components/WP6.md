# WP6 private extraction and receipts

C6b accounts for all 342 `style_guide` rows. Missing positive page and section
withholds as `locator_unavailable`. No automatic semantic pair parser is used:
the packet contains a reference to the complete cited passage, and the two seats
select exact rejected/recommended spans. Without a receipt the row is pending.
Only a jointly approved, explicitly calque-marked pair can be accepted.

C7's initial **candidate** census contains 20,162 distinct exact SUM-11
headwords per book row, anchored at their first whole-token occurrence. It scans
the entire passage, rather than only its title. This is a conservative superset,
not the approved design's semantic denominator of forms the book names as wrong.
That denominator remains unknown until the driver adjudicates and reconciles the
census. Neither the candidate count nor a passing structural gate establishes
C7 semantic completeness. No records are admitted on headword matching alone.

Both ids are already registered in the framework's closed registry. Each exports
`COMPONENT`; shared objects in `antonenko.py` prevent competing book adapters.
The integration owner must reconcile the ULIF/VESUM adapter objects with the
other work packages before a combined build. Current book and SUM-11 register
forms contain unresolved bibliography placeholders; the adapters withhold them.
They accept only a complete exact `bibliography` with held
`bibliography_evidence`, never an invented edition, year, volume or page.

`artifact_files(ctx)` emits private `C6b/` or `C7/adjudication-packets/` files
and shared per-component `passages/` files through the framework output guard.
Packet names use SHA-256 of the UTF-8 unit id. Each packet pins its schema,
component, unit, source row, complete source-field digest and review requirements.

The optional request key `antonenko_receipts` names a private driver-controlled
directory. Its files are `<component>/<unit-id-sha256>.json`. The receipt schema
is `antonenko-adjudication-receipt.v1`, with `component`, `unit_id`, `pair_id`
(the actual `style_guide` key), `packet_sha256`, `source_text_sha256`,
`rejected_span`, `recommended_span`, `calque`, and `sol`/`opus` objects. Each seat
object contains `model`, `family`, `harness`, `task_id`, `session_id`, `verdict`,
`packet_sha256`, both spans, and nonempty `tool_evidence`; C6b also requires each
seat's `calque` to agree. Verdicts are `APPROVE`, `REJECT`, or `UNSUPPORTED`.
Distinct fresh sessions and both `APPROVE` are mandatory. Missing or unsupported
adjudication withholds; malformed, stale, self-reviewed or swapped receipts refuse.

Receipt files are trusted only as driver-controlled review artifacts. Their
hashes and exact selected fields are pinned; this format does not cryptographically
attest model execution. The driver supplies the authentic fleet task/model/tool
provenance. No review seats are run by these extractors.

An all-withheld build has `missing_coverage` metrics. The current framework
`verify` refuses generic accepted-record mutation proof as `mutation_unavailable`;
this limitation is reported, not converted into a pass.
