# Phase 5 exact-artifact word-card certification

This reference defines #10515 under programme #8977 and stream #6321.
`scripts.atlas.word_card_certification` evaluates pinned evidence and refuses
acceptance or export without an exact-artifact certification receipt.
It writes no approvals, gold, card content, review-ledger entries, or releases.

Passing repository tests establishes harness behavior on synthetic inputs.
It does not certify Ukrainian, establish complete source acquisition, accept a
pilot, or authorize publication. The committed review ledger grants no cards
approval until an independent authority admits their evidence.

## Authority and prerequisite contracts

The independent steward supplies the specification and evaluation SHA-256 pins
through the existing control channel. The assembler or code author cannot
appoint itself as evaluator or manufacture its own trusted pins. As with the
[Phase 4 contract](golden-set-spec.md), hashes prove retained byte bindings.
The steward authenticates qualifications, family identities, source authority,
chronology, and the semantic adequacy of inspection evidence before admitting
pins. This module is not a signature service or an OS isolation boundary.

The gate uses Phase 4 `verify`, including replay of source accounting, every
complete-data prerequisite, the exact sealed membership and answers, and
independent custody evidence. A copied `COMPLETE_DATA_APPROVED` or
`VERIFIED_RECEIPTS` string cannot replace this replay. Changed transitive
captures and source indexes invalidate the evidence even if a top-level receipt
remains unchanged. The gold custody build fingerprint must equal the frozen
implementation fingerprint.

`evaluate_certification(spec_path, spec_sha256, evaluation_path,
evaluation_sha256)` returns a deterministic receipt or raises on inadmissible
evidence. A semantically failed evaluation returns `status: FAILED` with its
findings. Invalid prerequisites, reduced coverage, and malformed submissions
raise instead of producing a certification. The function has no network or
provider calls and never authors Ukrainian.

All JSON inputs use the Phase 4 strict reader and closed schemas. References
contain exactly `path` and `sha256`; SHA-256 hashes use lowercase hexadecimal.
Relative references resolve against the containing specification, mechanics
receipt, or evaluation. Receipt references in the authority ledger resolve
against the ledger's directory. Input file digests cover exact bytes.
`digest(value)` covers sorted, compact UTF-8 JSON without a trailing newline.
It rejects nonfinite numbers. Unknown fields, duplicate keys, invalid Unicode,
missing evidence, and booleans used as counts cannot establish certification.

## Frozen certification specification, AC-01

`word-card-certification-spec.v1` has the following required fields.

| Field | Meaning |
| --- | --- |
| `gold_spec` | Pinned Phase 4 specification reference. |
| `gold_seal` | Reference to the sealed bundle's `seal.json`. |
| `isolation` | Pinned independently verified Phase 4 custody adapter. |
| `complete_data_receipt` | The same receipt digest used by the Phase 4 specification. |
| `mechanics_receipt` | Independent accepted-mechanics adapter described below. |
| `frozen` | `implementation_sha256`, `rules_sha256`, and `inputs_sha256`. |
| `author` | Implementation author `id` and `family`. |
| `evaluators` | At least two qualified evaluators with distinct IDs spanning at least two families outside both the implementation author's and assembler's families. Each has `id`, `family`, and a retained `qualification` reference. |
| `projections` | A mapping for all six facets. Each entry contains `gold_field` and `card_pointer`. Gold fields and card pointers are distinct. |
| `cases` | Ordered `case_id` and `card` references, matching every sealed case exactly. Card IDs are unique. |
| `controls` | Frozen planted-control inventory, described below. |

The freeze precedes evaluator inspection. The language evaluation binds its
`spec_sha256` to these exact bytes. Any specification change requires a new
pinned evaluation. The denominator is every sealed case, every declared
failure stratum, all six facets per case, and every appointed evaluator.
Controls have separate class denominators. Controls never increase the number
of genuine gold cases or compensate for a failed ordinary case.

`frozen_artifact(authority, cards)` recomputes the implementation and rules
fingerprints using the existing repository-relative file inventories. The
implementation inventory includes parsers, extraction and export helpers, the
certification evaluator, and the VESUM lock. Rules include word-card schemas,
identity, export invariants, the acceptance-path census, and the Phase 4 and
Phase 5 specifications. Input hashes bind the complete `build.inputs` mapping
by card ID. Every declared S, V, I, and O snapshot must match current authority;
VESUM, overlay, suppressions, rules, normaliser, and register are mandatory.

`word-card-mechanics-acceptance.v1` contains `status: MECHANICS_ACCEPTED`,
`frozen`, `cards_sha256`, `accepted_by`, and nonempty retained `evidence`
references. `cards_sha256` is `digest(cards)` in frozen case order.
The accepting actor differs in ID and family from the author and assembler.
The frozen hashes must match the certification specification exactly.
The adapter references the accepted mechanics artifacts and independent
acceptance evidence. The existing #9402 `mechanics_only_uncertified` batch
receipt alone is insufficient. This module consumes the adapter; it does not
create independent acceptance or claim an existing producer emits it.

## Language evaluation, AC-02

The semantic facets are `identity`, `sense_binding`, `stress`,
`source_fidelity`, `citation_validity`, and `abstention`. Each evaluator inspects
the complete exact card and authenticated source evidence. The inspection
covers identity attachment and homonyms, sense scope, stress authority,
qualifiers and labels, claim-to-span bindings, citations, and appropriate
abstention. Evaluators follow the project's facet-specific Ukrainian source
rules. Literal equality alone does not establish linguistic correctness.

`projections` maps each facet to a sealed expectation and a JSON pointer in the
actual card. The field must exist in each sealed answer. A value expectation
requires exact canonical equality with its source-backed value. Conflict and
abstention expectations require a null projected value. The harness performs
no translation, normalization, paraphrase, or display transformation.
Pointers can target retained raw assertions while evaluators inspect display
transformations against frozen rules. Display transformations preserve the
cited source values, qualifiers, labels, and span bindings. Changing a
transformation changes its implementation or rules fingerprint and invalidates
certification. Gold membership and answers remain outside assembler inputs.

`word-card-language-evaluation.v1` contains `spec_sha256` and `reports`.
Each report contains the appointed `evaluator_id` and an `items` array covering
every case and control exactly once. Each item has:

- `item_id`, the frozen case or control ID.
- `card_sha256`, computed with `digest` over the complete card.
- `inspected_complete_card: true`.
- `scores`, exactly one entry for each of the six facets.

Each score contains `facet`, `verdict` equal to `pass` or `fail`, a nonblank
`reason`, `source_claims_sha256`, and `findings`. The source digest binds the
complete sealed expectation, including claims, source-unit links, literal span
pointers, scope, rationale, and adjudicator votes. Phase 4 rechecks the actual
source values. The evaluator's reason remains retained inspection evidence;
the harness cannot infer expertise or honest inspection from that string.

Each finding contains `code`, `owner`, `dependency`, and an `evidence`
reference. Codes are `invented_ukrainian`, `wrong_identity`, and `material`.
Every finding blocks its facet. A failed score requires a named source-gap or
repair owner and a concrete dependency. A pass with a finding is invalid.
Resolution requires new evidence and a new pinned evaluation; copied
"resolved" labels cannot clear findings. Any failed ordinary facet fails the
entire certification. Scores never average away a wrong identity or invention.

## Planted semantic controls, AC-03

Every control contains `control_id`, `case_id`, `class`, and a `card` reference.
Control IDs are distinct from case IDs and from each other. Each control uses
the same card ID as its base case and changes exactly one frozen projection.
The remaining card content is identical. Each class appears at least once:

| Class | Required failed facet |
| --- | --- |
| `wrong-homonym` | `identity` |
| `wrong-stress` | `stress` |
| `unsupported-definition` | `source_fidelity` |

Every evaluator must explicitly fail each control's target facet and retain
an owned finding. An evaluator who passes a wrong value fails the control even
when the literal comparator independently detects it. Untargeted failures
remain material findings. Missing classes, unchanged controls, foreign card
identities, or changes outside the target projection refuse evaluation.
The steward independently verifies that the planted substitutions actually
exercise their declared semantic classes. Arbitrary string changes in tests
prove harness discrimination only, never real homonym or stress detection.

## Exact-artifact receipt and export, AC-04

`word-card-certification-receipt.v1` contains `status`, pinned `spec` and
`evaluation` references, `frozen`, `gold_seal_sha256`, `case_count`, `strata`,
`evaluators`, per-facet `scores`, per-class `controls`, `findings`, and `cards`.
The `cards` mapping binds each card ID to the digest of its entire JSON object,
including review metadata and build inputs. A card outside the evaluated set
cannot borrow another card's certification. This is not a universe-wide claim.

A trusted review-ledger entry still needs its existing active review, version,
build, scope, implementation, and rules bindings. It now also requires
`certification_receipt`, a pinned reference to the exact-artifact receipt.
Legacy approvals without this reference fail closed. Synthetic export fixtures
must provide the same Phase 5 evidence interface.

`verify_certification_receipt(ref, base)` hashes the receipt, reruns evaluation
against its pinned inputs and current implementation, rules, sources and
custody evidence, and compares the entire receipt with the replay. Only an
identical `CERTIFIED` receipt passes. An edited status, stale report, modified
card, source, parser, rules, qualification, or transitive evidence invalidates
certification. Restoring a historical authority repository is outside this
module's trust boundary; no rollback is authorized here.

`load_certified_card_for_export` requires this replay before returning a card.
The existing shared boundary propagates the refusal to acceptance, dataset
export, package publication, hydration, and runtime projections. It retains
separate site and dataset approvals. Receipt results are cached within one
`certification_run`, then discarded. Each separate export or reimport reads
current evidence again. The module never lifts the review or release gates.

## Results, publication, and residuals, AC-05

The returned private receipt preserves independent evaluator identities,
qualification references, case and failure-stratum denominators, six separate
pass counts and denominators, three control detection counts and denominators,
and owned findings. The original pinned evaluation retains every score,
inspection reason, and evidence reference. Both remain available for audit.

The steward retains exact receipt bytes and records their SHA-256 in the
trusted review ledger only after independent acceptance. Full receipts contain
private paths and protected case IDs. They must remain in protected custody,
not a public issue, PR, or tracked test artifact. Public evaluation reporting
uses aggregate scores, control results, finding counts and classes, and the
exact private receipt's digest. No Ukrainian source text, gold membership,
answers, private paths, or inspection narratives belong in that report.
`certification_summary(ref, base)` replays either a passed or failed receipt and
returns only aggregate scores, control results, evaluator and case counts,
finding counts and codes, and the pinned receipt digest. It writes nothing.

A failed report remains failed until its owners repair every material finding
and independent evaluators inspect the new artifact. Certification, programme
completion, public release, and the later held-out product evaluation remain
separate dispositions. Missing real receipts or qualified evaluation is a
residual owned by the accountable open-model-data driver, never a synthetic
passing result.

## Verification

The dedicated test suite uses source-free fixtures and deliberate falsifiers.
It exercises prerequisite replay, evaluator independence, all six facet gates,
planted controls, source and implementation drift, receipt replay, and export
refusal. It also checks that a valid synthetic receipt can pass the boundary.

```bash
.venv/bin/python -m pytest -q tests/test_word_card_certification.py
.venv/bin/python -m pytest -q tests/test_word_card_golden_set.py
.venv/bin/python -m pytest -q tests/test_word_card_foundation.py
```

Tests importing the changed shared certification helper also require affected
boundary checks. Test success does not populate the authority ledger or close
real certification criteria.
