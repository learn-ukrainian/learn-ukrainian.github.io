# Phase 4 sealed word-card golden set

This reference defines the receipt and bundle interface implemented by
`scripts.atlas.word_card_golden_set` for #10514, programme #8977, stream #6321.
The implementation validates supplied evidence. It does not select cases,
author Ukrainian, adjudicate answers, issue source clearance, certify cards,
change assembler behavior, or implement the #9608 isolation service.

The [source accounting contract](../../../registry/atlas/source-completeness/manifest-contract.md)
retains its evidential limits. `STRUCTURALLY_ACCOUNTED`, a matching census,
and passing tests never establish Phase 1 or Phase 2 completion. Admission
also requires an independently approved complete-data receipt. The steward
supplies the trusted specification digest through a separate control channel.
A digest calculated from an unreviewed submission grants no authority.

## Frozen evaluation specification

`word-card-gold-spec.v1` is a closed JSON object. Unknown properties, duplicate
JSON keys, nonfinite numbers, invalid Unicode, and integral floats in integer
fields fail validation. File digests are lowercase SHA-256 of exact bytes.
References contain exactly `path` and `sha256`. Relative references resolve
against the containing specification, except for references inside clearance
and isolation receipts, which resolve against those receipts.

| Field | Contract |
| --- | --- |
| `inputs` | References named `requirements`, `source_manifest`, `stage_evidence`, `lexical_universe`, `legacy_membership`, `atlas_manifest`, `accounting_receipt`, `census`, `complete_data_receipt`, and `development_membership`. |
| `universe_count` | Positive integer equal to the independently indexed lexical member count. |
| `candidate_entry_count` | Positive integer equal to the replayed Candidate A Atlas census entry count. Entries and lexical members retain separate denominators. |
| `case_count` | Positive integer frozen before selection. Each member appears in at most one case. |
| `strata` | Nonempty object mapping stratum names to positive case counts. Its sum equals `case_count`. Selected cases match every stratum exactly. |
| `required_fields` | Distinct field names, including `identity`. Every case contains each field exactly once. |
| `assembler_build_sha256` | Exact assembler artifact fingerprint covered by the isolation evidence. A changed build requires new evidence. |
| `protected_root` | Existing absolute steward custody directory outside the repository. The specification, case staging file, bundle, and isolation receipt remain inside it. |
| `roles` | One `assembler`, one separate `steward`, and at least two distinct qualified `adjudicators`. |
| `selection` | `method: fresh-source-side`, `assembler_outputs_seen: false`, and an evidence reference for independent fresh selection. |

Actors contain `id` and `family`. Both use lowercase letters, digits, periods,
underscores, colons, or hyphens, starting with a letter or digit. Adjudicators
also contain a `qualification` reference. All actor IDs differ. Adjudicators
span at least two families, both outside the assembler's family. Retained
qualification and selection evidence must exist and match its digest.
The steward and driver authenticate identity, family, qualifications, source
adequacy, and chronology independently. Supplied labels cannot establish them.

`development_membership` contains only `protected_keys`, a nonempty array of
distinct identifiers from the development pool and its aliases and related
records. It contains no answers. Selected case IDs, member IDs, source keys,
aliases, and related source keys must be disjoint from that inventory. The old
220 cases remain development regressions. They never define this denominator.
The steward supplies the complete exclusion inventory and source identity
closure, including identities that spelling comparison cannot discover.

## Complete-data receipt gate, AC-01

Before reading or admitting cases, the gate validates the pinned specification
and every input reference. It invokes
`source_completeness_manifest.account` with all five original inputs and the
Atlas manifest, then compares the supplied accounting receipt with the replay.
It compares every accounting output byte for byte and compares the separately
referenced census with the replayed `atlas-census.json`.

The gate rejects unresolved gaps and unknown universe membership. It retains
the original source matrix, ordered source units, source-side indexes, exact
legacy obligation of 123, field obligations, stage evidence, and transitive
artifact checks enforced by the accounting producer. It neither relabels
missing data as absence nor substitutes the Atlas catalogue for the source
universe. The census remains an exact-key observation.

The separately supplied `word-card-complete-data.v1` receipt contains:

- `status: COMPLETE_DATA_APPROVED`, `phase1: COMPLETE`, and `phase2: COMPLETE`.
- `candidate: Candidate A Lexical Universe v1`.
- `accounting_sha256`, `census_sha256`, and `lexical_universe_sha256`, equal to
  the corresponding frozen input references.
- `approved_by`, an actor distinct from the assembler.
- `prerequisites`, references named `source_authority`, `snapshot_boundary`,
  `lexical_fidelity`, `phase1_acceptance`, `phase2_acceptance`, and
  `candidate_a_reconciliation`.

Each prerequisite must resolve to retained bytes with the pinned digest.
Independent source authority must have accepted these artifacts and all
original #10512 criteria before the driver accepts the specification pin.
The harness checks their bindings, not their semantic truth. It never produces
this clearance receipt or promotes accounting output into clearance.

## Cases and adjudication, AC-02 and AC-03

The input envelope is `word-card-gold-cases.v1` with a `cases` array. Each case
contains `case_id`, `member_id`, `stratum`, `source_keys`, `aliases`,
`related_source_keys`, and `expectations`. Every member belongs to the frozen
source universe. `source_keys` equals the keys in its existing source-unit
links. Empty alias and related-key arrays explicitly record an empty supplied
closure, whose adequacy still requires independent review.

Each expectation contains these fields:

| Field | Contract |
| --- | --- |
| `field` | One frozen required field. |
| `state` | `value`, `conflict`, or `abstention`. |
| `claims` | Nonempty, distinct source evidence claims. |
| `reason` | Nonblank adjudication rationale, retained inside protected custody. |
| `votes` | Exactly one vote from every appointed adjudicator, with `adjudicator_id` and `disposition` equal to `agree`, `disagree`, or `abstain`. |

A claim contains `value`, `reference`, `pointer`, `scope`, and `source_unit`.
The unit has the existing accounting `range_id` and complete `identity` object.
It must belong to that case's source-side member links. The cited artifact
must be authenticated by accounting and bound to that unit through its source
index, literal capture, or stage evidence. A JSON pointer selects the literal
source value. The harness compares canonical JSON bytes without normalizing,
paraphrasing, translating, or generating Ukrainian. Identity expectations also
match the source identity object exactly.

Pointers use `/`-separated JSON object keys or zero-based array indices with
`~0` and `~1` escapes. Invalid escapes, missing keys, invalid indices, or a
mismatch between the expected value and cited source value fail validation.
Structured retained evidence is required for this version. Opaque captures
need an independently authenticated structured extraction already bound by
the source accounting receipt. The gold tool does not create that extraction.

A `value` expectation has one distinct source value and at least one agreeing
vote. A `conflict` has at least two distinct source values. Any disagreeing
vote requires `conflict`. Unanimous abstention requires `abstention`.
Abstentions retain source claims supporting the decision and an explicit
reason, rather than inventing a missing value. The tool preserves every vote.

Independent adjudicators inspect authenticated sources without assembler
outputs. They determine the proper claim scope, linguistic authority, conflict,
and abstention. A literal equality test proves evidence binding, not that a
source establishes the claimed norm. Modern meaning, stress, and form still
follow the project's facet-specific source rules. Historical evidence keeps
its historical scope. No model-written Ukrainian enters the set.

## Bundle and custody, AC-04 and AC-05

The steward's `seal` operation publishes exactly three files in a new directory
outside the repository:

- `membership.json`, version `word-card-gold-membership.v1`, contains case
  membership, stratum, source keys, aliases, and related source keys.
- `answers.json`, version `word-card-gold-answers.v1`, contains ordered case
  IDs and their complete expectations and adjudications.
- `seal.json`, version `word-card-gold-seal.v1`, binds the specification digest,
  both file digests, case count, and `isolation: UNVERIFIED`.

The tool writes the seal last, flushes files, and syncs the directory. The
bundle directory starts at mode `0700` and files at `0400`. A retry accepts only
an identical complete bundle and changes no bytes or timestamps. Partial,
different, or symlink output paths fail. Interruption leaves no usable seal;
recovery requires a fresh output directory. These permissions do not isolate
processes that share the steward's identity. #9608 owns the actual access
boundary, every protected read, and its independently verified access logs.

`verify` reconstructs cases from the sealed files, checks their digests and
order, and repeats completeness and source-grounding validation. It also
requires an independently trusted digest for a
`word-card-gold-isolation.v1` adapter receipt. This interface consumes retained
#9608 evidence; it does not claim that #9608 already emits this adapter format.
The owning custody lane must supply an authenticated adapter and its evidence.

| Isolation field | Required evidence |
| --- | --- |
| `spec_sha256`, `seal_sha256`, `assembler_build_sha256` | Exact artifacts and build under evaluation. |
| `verified_by` | Independent actor distinct from the assembler. |
| `custody_evidence` | Nonempty references to the underlying #9608 boundary and access-log proof. |
| `readable_roots`, `writable_roots` | Complete lists of existing absolute assembler access directories, including mounted and delegated access. |
| `assembler_inputs` | Complete inventory of objects containing `role` and `reference`. Role is `source` or `mutation`. Each reference binds exact input bytes. |
| `roots_complete`, `log_complete` | Both `true`, independently established for selection through the evaluated build. |
| `alias_related_closure_checked` | `true`, including alternate identities, related records, and indirect access. |
| `adjudication_blind` | `true`, independently confirmed for all appointed adjudicators. |
| `access_log` | Records containing `actor_id`, `resource`, `operation`, and boolean `allowed`. Resources are `membership`, `answers`, `aliases`, and `related`. Operations are `read` and `write`. |

Verification rejects any overlap between the protected custody directory and
assembler access roots, including resolved symlink aliases. It refuses bundle
symlinks, hard-linked bundle files, extra files, and missing files. Source inputs
must match artifacts from the approved complete-data accounting, frozen before
gold selection. The assembler can read the full source universe without knowing
which members the steward selected. Source inputs may contain literal source
keys and opaque source bytes.

Mutation inputs include overlays, registry decisions, configuration, and other
assembler inputs that can carry adjudications. They are JSON. The gate rejects
protected case, member, source, alias, or related identifiers in mutation inputs,
including JSON keys, prose references, and nested JSON strings. Keys starting
with `expected` or `adjudicated` also fail. Relabelling a mutation as `source`
fails unless its exact bytes already belong to the approved source snapshot.
Verification requires
a denied assembler read and write probe for every resource class and rejects
any allowed assembler access in the complete log.

An empty log, membership hash, caller-provided zero counter, or input scan
alone cannot pass. The external verifier remains responsible for the actual
principal boundary, complete input inventory, non-JSON mutation channels, semantic
aliases, and log completeness. The harness cannot observe another process's
access history from file permissions. Receipt validation returns
`VERIFIED_RECEIPTS`, which denotes the supplied evidence contract, not card
certification, dataset release, or automatic completion of #10514.

## CLI and stopping behavior

```bash
.venv/bin/python -m scripts.atlas.word_card_golden_set seal \
  --spec "$STEWARD_ROOT/spec.json" --spec-sha256 "$SPEC_SHA256" \
  --cases "$STEWARD_ROOT/cases.json" --bundle "$STEWARD_ROOT/gold"

.venv/bin/python -m scripts.atlas.word_card_golden_set verify \
  --spec "$STEWARD_ROOT/spec.json" --spec-sha256 "$SPEC_SHA256" \
  --bundle "$STEWARD_ROOT/gold" \
  --isolation "$STEWARD_ROOT/isolation.json" --isolation-sha256 "$ISOLATION_SHA256"
```

Dispatch worktrees use the prescribed shared interpreter. CLI stdout contains
aggregate counts, status, and digests. It never prints protected identifiers,
answers, evidence text, or file locations. Exit `0` means that operation's
contract passed. Exit `2` means refused, incomplete, unavailable, malformed,
or drifted evidence. Invalid CLI syntax also exits `2`.

Any changed source input, specification, answer, membership, assembler build,
or custody artifact invalidates its corresponding pin and proof. The steward
retains disagreements and abstentions. A held-out case used to repair an
assembler rule leaves the held-out pool and requires an independently chosen
replacement under a new approved specification. The driver owns review,
CI, landing, and closeout. Independent source and custody lanes own unresolved
complete-data and isolation evidence. Missing evidence leaves admission or
verification blocked without reducing any frozen denominator.

## Validation evidence and limits

The scoped checks are:

```bash
.venv/bin/python -m pytest -q tests/test_word_card_golden_set.py
.venv/bin/python -m pytest -q tests/test_word_card_foundation.py
```

The new tests use source-free accounting fixtures and deliberate incomplete,
self-adjudicated, altered-source, altered-answer, alias-leakage, related-record,
and allowed-access falsifiers. They prove mechanics only. Real completion
requires independently selected held-out cases, authenticated linguistic
adjudication, actual complete-data approval, #9608 denial controls and complete
access records, exact-head cross-family review, and same-head CI. This change
contains no real gold or private answer keys and leaves those outcome gates
with their owning lanes.

The existing [migration reference](migration.md#4-gate-2--the-golden-set-with-an-independent-held-out-evaluation-before-full-scale-gates-c2)
provides historical gate context. The active #10514 outcome keeps its old pilot
cases development-only. General leakage guidance comes from the
[scikit-learn data leakage reference](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
Closed object validation follows the
[JSON Schema object reference](https://json-schema.org/understanding-json-schema/reference/object).
These external references explain mechanics and evaluation practice; they do
not approve this project's source universe or authorize custody changes.
