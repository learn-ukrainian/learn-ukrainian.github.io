# Ordered source accounting contract

Issue #10512; requirements [matrix](required-source-matrix.md); approved programme
[plan](../../../docs/projects/open-model-data/WORD_CARDS_DATA_PLAN.md).
This is the input/output contract of
`scripts.projects.open_model_data.source_completeness_manifest`. It adds an
engineering envelope around supplied evidence. It does not replace the word-card
schema, select sources, establish identities, grant freeze authority or certify data.

## Scope and status

All twenty matrix requirement IDs and their existing gap owners remain required.
The producer checks their order and gap IDs against the canonical matrix bytes.
The matrix remains UNFROZEN. Supply existing source-side identities verbatim;
never derive the source universe from assembler output, local populated tables,
a pilot or a consumer list. A caller's `source_side` declaration records its
claimed evidential role. The producer cannot authenticate that role or turn it
into approval. Independent source authority and strict snapshot evidence remain
external prerequisites, even when structural accounting succeeds.

The denominator includes every supplied source unit, lexical member and original
legacy member. Unknown source ranges remain UNPARTITIONED with a null unit count
and null partitions. The original #9401 AC-03 obligation remains 123 when its
membership is UNKNOWN. Never fill it with guessed IDs or a replacement sample.

| Exit | Receipt status or stderr | Meaning |
| --- | --- | --- |
| 0 | `STRUCTURALLY_ACCOUNTED` | Every finite supplied requirement, unit, field, stage and member has structural accounting without unresolved gaps. |
| 2 | `INCOMPLETE_DIAGNOSTIC` | Inputs are valid; source ranges, memberships, stage evidence or member links remain unresolved. Diagnostic manifests and receipt are committed. |
| 3 | `INVALID_EVIDENCE` on stderr | Malformed, ambiguous, inconsistent, reordered or digest-drifted evidence. This invocation publishes nothing. |
| 4 | `PUBLICATION_FAILURE` on stderr | Output storage or publication failed. This invocation commits no receipt. |

Neither exit 0 nor exit 2 establishes lexical fidelity, source completeness,
complete-data clearance, an accepted freeze, Phase 1 exit, gold, certification or
any #10512 acceptance criterion. The original five criteria and Phase 4/5 holds
remain unchanged. Source-free tests provide author development evidence only.
The driver obtains independent exact-head, exact-input reconciliation and review.

## Invocation and storage

All five input files and an output directory are required:

```bash
.venv/bin/python -m scripts.projects.open_model_data.source_completeness_manifest \
  --requirements requirements.json \
  --source-manifest source-manifest.json \
  --stage-evidence stage-evidence.json \
  --lexical-universe lexical-universe.json \
  --legacy-membership legacy-membership.json \
  --output-dir "$TMPDIR/source-accounting"
```

From a dispatch worktree use its prescribed shared interpreter instead of a
worktree `.venv`. Output must be a new directory below managed `$TMPDIR` or this
worktree's ignored `batch_state/reports/`. Symlink output paths and overlap with
any direct or transitive input are refused. Inputs and source stores are read
only. The producer has no database, crawler, account, Hub or network operation.

Outputs are twenty `SRC-*.json` manifests in matrix order, `members.json`, and
`manifest-receipt.json`. Each source manifest preserves range order and source
unit order with zero-based ordinals within its range. The receipt binds the
exact input bytes, versions, transitive artifact digests, ordered output files,
counts, requirement dispositions, gaps and external prerequisites. Every gap
names requirement, field, stage, gap ID, owner and evidence, plus range/unit
where known. Unknown ranges keep a separate gap for every applicable field.
A lexical-universe gap applies across requirements and has a null
requirement ID with `G-UNIVERSE`. `programme_completeness` is always `UNRESOLVED`.

Publication follows the repository's same-directory temporary file, flush,
fsync and atomic replace pattern. The receipt is the final commit marker.
Interrupted staging files or manifests without that receipt are uncommitted.
Reruns verify an existing byte-identical bundle without modifying it. A changed,
damaged or partial directory is refused; use a fresh explicit output path.
An invalid rerun preserves prior committed artifacts and their original input
bindings; it does not produce a new receipt. Readers must check receipt hashes
before using manifests. Generated evidence is never committed to Git.

## Exact input envelopes

JSON objects reject unknown keys, duplicate keys, non-JSON constants, invalid
UTF-8 and invalid Unicode. Digests are full lowercase 64-character SHA-256 of
file bytes. Arrays preserve order and multiplicity. A reference has exactly:

```json
{"path":"retained-file.json","sha256":"<64 lowercase hex>","schema_version":"source-index.v1","locator":"source-visible locator"}
```

Reference paths resolve relative to the enclosing top-level input's directory.
Opaque evidence may use a descriptive version such as `opaque-bytes.v1`.
Structured index and absence references must also match their JSON version.
Missing referenced files and digest mismatches are invalid evidence, not
successful acquisitions. To report a known damaged capture, retain and bind its
actual damaged bytes and record `corrupt` with its reason; do not supply a false
expected digest as though the bytes matched.

Each unit is an existing identity, locator and source-byte digest:

```json
{"identity":{"key":"source key","homonym":"source homonym","sense":"source sense","path":["group","nested unit"],"occurrence":0},"locator":"source-visible unit locator","sha256":"<64 lowercase hex>"}
```

`path` preserves nested order; `occurrence` distinguishes repeated source units.
`occurrence` and `expected_obligation` require JSON integers. Integral floats,
including `0.0` and `-0.0`, are invalid at every identity and index boundary.
An absent source homonym or sense stays `null`, without an invented label.
Identical spellings with different source homonyms/senses or occurrence paths
remain separate. The producer does no normalization or fuzzy linking. An exact
duplicate identity is ambiguous and rejected; expected repeated values must have
their existing distinct occurrence identities. These are accounting coordinates,
not new persistent word-card identities or a cross-snapshot identity policy.
Within a range, distinct units require distinct exact unit locators. A shared
page locator alone cannot distinguish units. Missing or blank locators are
invalid. Locator drift against the independent index is reported by ordinal.

### Requirements

`source-requirements.v1` has `schema_version`, `matrix_sha256` and `requirements`.
Its twenty requirement records, in matrix order, each have:

- `requirement_id`, `gap`, `owner` from the existing matrix. The owner remains
  `open-model-data`; the source authority retains specialist dependency details.
- `fields`, an ordered nonempty array of `{name, applicability, reason}`.
  Applicability is `applicable` or `not_applicable`. Reasons must identify the
  source role, including why a field does not apply. At least one field must be
  applicable; a requirement cannot be erased through applicability flags.
- `consumers`, a nonempty ordered list of distinct existing projection names.

Field/projection selection is a supplied scope description requiring external
adequacy review against the matrix and approved plan. The producer checks its
structural accounting, never approves a smaller field or consumer denominator.

### Source manifest and independent index

`source-manifest.v1` has `schema_version`, `requirements_sha256`, `origin` equal
to `source_side`, and ordered `ranges`. Unavailable whole requirements may have
no range records; their dispositions remain explicitly UNPARTITIONED.

Each range has `range_id`, `requirement_id`, `edition`, `range`, `snapshot`,
`source_locator`, `register_kind`, `retrieved_at`, `membership`, `index`, `units`.
Boundary strings must be explicit source descriptions, not inferred local row
counts. `retrieved_at` is an actual UTC ISO timestamp ending in `Z`.
`register_kind` is `checked_register`, `unchecked_extension` or `source_index`.
Keep the historical checked register and unchecked extension in separate range
records, with their own retrieval dates and boundaries. A historical manifest
is not a current publisher-extent freeze or strict cross-store snapshot seal.

`KNOWN` membership requires an independently retained `source-index.v1` reference.
That index contains `schema_version`, all nine boundary fields from `range_id`
through `retrieved_at`, and ordered `units`. Every boundary and unit must exactly
match the range, including identity, locator and digest. `UNKNOWN` requires
`index: null` and `units: []`, and does not establish an empty universe.
An independently indexed empty finite range can be structurally represented;
its authority still needs external proof. Duplicate range IDs are invalid.
Reconciliation reports missing and extra identity counts, identity order drift,
and the first locator or digest discrepancy's ordinal on stderr. These are
invalid evidence, never a reduction of the expected denominator.

### Stage evidence

`stage-evidence.v1` has `schema_version`, `source_manifest_sha256`, and `records`.
Each record has `range_id`, `identity`, `source_unit_sha256`, `field`, `stage`,
`state`, `reason`, `evidence` and `absence_evidence`.

Stages are independently counted: `acquisition`, `raw_custody`, `parsing`,
`admission`, and `consumer:<name>` for each supplied consumer. Evidence at one
stage never implies another. Missing records produce `missing` gaps while
retaining the independently indexed denominator. Supplied records must be a
source-ordered subsequence within each range/field/stage. Extra identities,
duplicates, reordered identities and inconsistent source digests are invalid.
Records for unknown ranges, extra stages or not-applicable fields are invalid.

States retain the matrix's meanings: `verified-complete`, `missing`, `corrupt`,
`quarantined`, `genuinely_absent`. A non-missing state requires retained evidence;
`verified-complete` acquisition/raw custody must include the exact source-byte
digest. These checks establish supplied structural support only, not authentic
custody or usable linguistic fields. Unknown raw authenticity is an external
prerequisite, never converted to acceptance through a state string.

`genuinely_absent` cannot appear for acquisition/raw custody or an unchecked
extension. It requires acquisition and raw custody records with exact-byte
support and a structured `absence_evidence` reference. The referenced
`source-absence.v1` object must contain exactly `schema_version`,
`source_manifest_sha256`, `range_id`, `identity`, `field`, `locator`; its locator
must match the range's source locator. This is positive source-evidence binding,
not a new authority system. A source declaration alone cannot approve absence.
Source authority must independently inspect the cited evidence. Unchecked
`not_found`, missing acquisitions, damaged captures and parse loss never prove
absence. Other states require `absence_evidence: null`.

Partitions are disjoint per unit/field/stage. Unit structural summaries use
`corrupt` before `quarantined` before `missing`; a unit whose parsing, admission and consumer fields all have positive absence
states is `genuinely_absent`, and otherwise fully accounted fields summarize as
`verified-complete`. These summaries describe structural coverage only; readers
must inspect every field and stage. `not_applicable` fields retain their reasons
outside the five states. Stage counts count applicable unit-field obligations,
not unique lexical entries; per-range unit partition counts count units once.
Known empty ranges have explicit zero counts for every stage and state. Unknown
ranges have null stage counts and partitions. Receipt totals cover only supplied
known unit-field obligations, as its `stage_count_scope` states.

### Lexical universe and original legacy membership

`lexical-universe.v1` has `schema_version`, `source_manifest_sha256`,
`membership`, `index`, `members`. `legacy-membership.v1` adds
`expected_obligation: 123`. Unknown inputs explicitly use `membership: UNKNOWN`,
`index: null`, `members: []`; member counts remain null, not zero.

Known membership requires an independently retained `membership-index.v1` with
`schema_version`, `origin: source_side`, `members`, `provenance`. Provenance has
`source_locator`, `source_snapshot`, `consumer_version`, and `role`, which is
`lexical_universe` or `original_legacy123` respectively. This preserves an exact
original locator/version claim for independent comparison. Known legacy
membership must contain exactly 123 unique member IDs. No synthetic member list
can establish original membership, even if structurally valid.

Members are ordered `{member_id, locator, source_units}` records. A source-unit
link is exactly `{range_id, identity}` and must reference an indexed source unit.
An empty link array retains that member as an explicit unresolved linkage gap.
Duplicate member IDs or links, invalid references, reordered membership or index
drift are invalid. The producer preserves every supplied lexical member and
legacy member; it does not infer linguistic identity or approve link validity.

## Verification and remaining programme evidence

Run the source-free focused CLI tests and existing record-contract tests:

```bash
.venv/bin/python -m pytest -n 2 -q \
  tests/projects/open_model_data/test_source_completeness_manifest.py \
  tests/test_open_model_source_record_contract.py tests/test_ulif_word_records.py
.venv/bin/python -m pytest -n 2 -q tests/test_docs_catalogue_coverage.py
.venv/bin/python -m scripts.docs.catalogue readme --check
```

The fixture suite compares literal ordered expectations to actual CLI files,
including unknown ranges, stage losses, digest/order drift, separate homonyms,
source-role applicability and publication failures. It cannot replace independent
held-out evaluation of authentic source data. Open-model-data owns unresolved
source boundaries, original legacy membership, source/consumer reconciliation,
strict snapshot proof and all five original acceptance criteria.
