# Complete-universe build and reconciliation

This reference defines the Phase 6 harness for #10516, under programme #8977
and stream #6321. `scripts.atlas.word_card_universe` builds a private SQLite
checkpoint from frozen, cited-source candidates and accounts for every source
unit. It neither generates Ukrainian nor grants certification or publication.

Passing synthetic tests proves harness behavior. Authentic complete-universe
execution requires independently admitted source, certification, resource, and
inspection evidence. These are separate acceptance obligations. Programme
#8977 remains open until its full exit criteria are met.

## Frozen inputs and trust

The independent steward supplies the specification SHA-256 through the existing
control channel. As in [Phase 5](certification-spec.md), hashes bind bytes;
they do not authenticate actors, expertise, measurement, or honest inspection.
The steward verifies those facts before admitting pins. The author cannot
manufacture independent acceptance by choosing another actor name or family.

All JSON uses the Phase 4 strict reader and closed schemas. References contain
exactly `path` and lowercase hexadecimal `sha256`. Relative references resolve
against the document containing them. Duplicate keys, unknown fields, invalid
Unicode, nonfinite numbers, and booleans used as measurements fail validation.
The module schemas are the machine-readable reference.

`word-card-universe-spec.v1` contains these fields.

| Field | Contract |
| --- | --- |
| `author` | Implementation author's `id` and `family`. |
| `source_spec` | Pinned Phase 4 source specification. Only its complete-data inputs enter enumeration. Protected membership and answers are not assembler inputs. |
| `inventory` | Independently accepted lexical dimensions, card identities, and source strata. |
| `plan` | Frozen disposition for every enumerated source unit. |
| `certifications` | Nonempty inventory of exact Phase 5 receipts. |
| `limits` | Positive integer `batch_units`, `max_card_bytes`, and `min_free_bytes`. |
| `runtime_sha256` | `runtime_fingerprint()` over the interpreter, SQLite version, OS release, and machine architecture. Runtime drift refuses execution. |
| `resource_acceptance` | Independently accepted full-scale resource and interruption trial. |

The complete-data verifier replays the independent source indexes, stage
accounting, lexical membership index, census, and prerequisite receipts.
Enumeration uses every range and unit in the source manifest, including source
units without lexical membership. Unknown membership refuses the freeze.
The denominator includes frozen VESUM entries, checked ULIF entries, and all
declared supplementary and MWE units. It is a finite source universe, not
every Ukrainian word. Changing an input requires a new specification and
checkpoint, never a smaller denominator in an existing build.

`unit_key(link)` hashes the complete source `range_id` and structured identity.
The identity retains its key, homonym, sense, nested path, and occurrence.
Equal spellings never merge source units. No identity is minted from source
order or spelling similarity.

## Lexical dimensions

`word-card-universe-inventory.v1` contains `accepted_by`, `members`, and
`strata`. The accepting actor differs in ID and family from both the code
author and the source assembler. `members` covers every frozen lexical member
exactly once. Each row contains:

- `member_id`, from the complete lexical universe.
- `spellings`, a nonempty inventory of literal spellings.
- `lexemes`, `senses`, `mwes`, and `forms`, separate arrays of stable,
  source-scoped identifiers. Empty arrays mean no declared identity of that
  kind for that member. They do not imply that a spelling is a lexeme.
- `card_ids`, the exact cards independently allocated to supportable identities.
  An unsupported member has no card allocation and remains in the denominator.
- `evidence`, nonempty references to authentic source and identity-allocation
  evidence supporting these dimensions and mappings.

Counts are unions of each dimension's identifiers across members. Repeated
citations of the same lexeme do not increase its count. Distinct homonyms have
distinct lexeme IDs; senses and MWEs retain their own IDs. Separate lexical
identities cannot share a card ID, and allocated identities cannot exceed
allocated cards. Different source members for the same lexical identity may
cite the same card. The steward establishes the semantic validity of these
identifiers and their source bindings, rather than inferring them from counts.

Every `strata` row contains `unit_key` and `stratum`. Every source unit has
exactly one stratum. The steward declares all authentic source and failure
strata absent from the mechanics pilot before freezing the specification.
Dropping an inventory member or stratum refuses the build.

## Dispositions and source-only cards

`word-card-universe-plan.v1` contains `dispositions`, with one row per source
unit, including units outside lexical membership. Each row has `unit_key`,
`status`, `cards`, `reason`, `owner`, `dependency`, and nonempty `evidence`.

| Status | Required accounting |
| --- | --- |
| `mapped` | Nonempty card references matching the accepted lexical allocation for that unit. Owner and dependency are null. |
| `unresolved` | No cards. A named source gap, owner, and concrete dependency remain. |
| `excluded` | No cards. A source-scoped exclusion reason, owner, and concrete dependency remain visible. |

Evidence resolves against the plan's directory. Duplicate, missing, and extra
unit rows refuse the build. Duplicate card references within one mapping also
refuse it. Many source units may legitimately map to the same card; that card
is stored and counted once. Every supportable card allocated by the accepted
inventory must occur in the build.

Candidates are immutable outputs of the existing source assembler. Phase 6
preserves their complete JSON objects and hashes. It admits only nonempty,
cited `source_extract` assertions, with source, snapshot, and locator bindings.
It performs no translation, paraphrase, generation, or field filling. Missing
or ambiguous fields remain as independently certified abstentions. An entire
unsupported identity stays explicitly unresolved with its named source gap.

Every candidate passes `load_certified_card_for_export`. Each declared Phase 5
receipt is replayed, and each candidate must occur with its exact digest in
that frozen certification inventory. The Phase 5 complete-data receipt must
match the source universe being built. A receipt for another card, source
universe, implementation, rule set, or snapshot cannot authorize the mapping.
The harness never edits the trusted review ledger to admit new candidates.

## Resource acceptance and crash-safe resume

`word-card-universe-resources.v1` contains:

- `inputs_sha256`, returned by `input_binding(spec)`, covering author, source
  specification, inventory, plan, certifications, limits, and runtime fingerprint.
- `source_unit_count` and `limits`, exactly matching the complete build.
- `accepted_by`, independent of the implementation author.
- Positive integer `peak_rss_bytes` and `rss_budget_bytes`, with the observed
  peak within the admitted budget.
- `interrupted_after`, nonempty positive unit boundaries below the full count.
- `uninterrupted` and `resumed`, references to retained trial disposition
  streams. Both byte hashes must equal the full frozen disposition stream.
- Nonempty `evidence` retaining authentic full-scale measurements, interruption
  observations, environment compatibility, and independent acceptance.

These are acceptance adapters supplied by the independent steward, not a
claim that an existing producer already emits them. The harness compares
their full denominator, limits, retained output bytes, and input bindings.
The steward verifies that the retained trials actually ran and measured the
declared work. A copied status or pilot-size trial is insufficient. Runtime
RSS is accepted from those measurements, not enforced by this Python module.
The existing complete-data verifier materializes its JSON inputs in memory;
batch size does not bound total process memory.

`build(..., resource_trial=True)` permits measuring this implementation before
resource acceptance exists. It retains every source, inventory, certification,
disk, size, and checkpoint integrity gate. Its states have the
`RESOURCE_TRIAL_` prefix. The pinned trial specification may reference a
not-yet-produced resource adapter; only that adapter is not dereferenced.
`freeze_inventory`, ordinary `build`, and `reconcile` always require accepted
resource proof. The accepted specification changes when its resource reference
is pinned, so its ordinary build uses a new checkpoint. `input_binding` omits
the resource reference to let the accepted proof bind the same trial inputs
without a circular hash. The trial does not grant acceptance or export.

`freeze_inventory(spec_path, spec_sha256)` replays prerequisites and returns
counts and output hashes before any checkpoint is created. `build` repeats
that verification and creates SQLite `metadata`, `units`, and `cards` tables.
The checkpoint belongs to exactly one pinned specification. SQLite uses
`synchronous=FULL`; one transaction commits each bounded batch of units and
their exact cards. An interruption rolls back the incomplete batch. Completed
batches survive and are verified on the next invocation.

`build(spec_path, spec_sha256, checkpoint, max_units=None)` accepts a positive
optional interruption boundary. It returns `INTERRUPTED` until all units are
accounted, then `BUILT_UNRECONCILED`. Neither state grants acceptance. Disk
headroom is checked before checkpoint creation and before every batch.
Candidate file size is checked against `max_card_bytes` before reading it.

Every separate invocation rechecks current certification and evidence,
including cards already present in a resumed checkpoint. Withdrawn approvals,
changed inputs, corrupt rows, foreign card IDs, and changed freezes refuse
resume. Each public operation uses a fresh context for authority verification;
an enclosing caller's export cache cannot conceal a withdrawal across calls.
The harness never silently repairs corrupt checkpoint content. A
missing unit may be reprocessed under the same freeze; a missing card for a
committed mapping is corruption. Checkpoints contain source material and stay
in private, ignored storage. The existing assembler containment guard checks
the database and SQLite sidecar paths before opening a writable checkpoint.
Primary, sibling, and tracked checkout destinations are refused. Checkpoints
are never public dataset exports.

## Independent reconciliation and coverage

`reconcile(spec_path, spec_sha256, checkpoint, independent_proof, proof_base)`
opens the checkpoint read-only and re-enumerates source inputs. It compares
every stored unit and card with the frozen inputs, checks exact membership,
and refuses incomplete, extra, duplicated, or corrupt accounting. Checkpoint
totals and copied completion strings cannot establish conservation.

The independently supplied `word-card-universe-reconciliation.v1` report binds
`spec_sha256`, `source_unit_count`, `dispositions_sha256`, and `cards_sha256`.
Its `accepted_by` differs in ID and family from the implementation author.
Its `inspections` cover every source-range and declared-stratum combination
for each of these checks:

- `source_fidelity`, `scope`, and `citations`.
- `withdrawals`, `reimports`, and `resumed_builds`.
- `homonyms`, `senses`, and `mwes`.

Each inspection names an existing `unit_key`, a `check`, a `verdict`, a
nonblank `reason`, and nonempty retained `evidence`. Verdicts are `pass` or
`not_applicable`; the latter requires an independently justified source-scope
reason and evidence. Failed or uncertain inspections cannot produce this
acceptance adapter. The steward verifies authentic source comparisons and
controls, sample adequacy, and the independence of inspection before admitting
its pin. Author-generated reports and synthetic fixtures are not held-out
product evidence. The module enforces coverage and bindings but cannot
authenticate real inspection or interpret an opaque witness semantically.

The private `word-card-universe-receipt.v1` reports `RECONCILED` with:

- Separate counts for source units, lexical members, spellings, lexemes,
  senses, MWEs, forms, and cards.
- The conservation equation `source_units = mapped + unresolved + excluded`,
  with zero missing and duplicated units.
- Partition counts per source range and per declared stratum.
- Exact certification receipt digests and each receipt's card hashes.
- Disposition and card stream hashes and the independent inspection reference.
- Every unresolved or excluded unit's reason, owner, and concrete dependency.
- `programme_completion: UNRESOLVED` and `export_authorized: false`.

Streams use compact, sorted-key UTF-8 JSON with one trailing newline per row.
Disposition rows sort by `unit_key` and bind source identity, unit digest,
lexical member links, stratum, disposition, evidence, and exact card hashes.
Card rows sort by card ID. Stream digests cover exact bytes. SQLite page bytes
are not reproducible artifacts and do not enter proof hashes.

Reconciliation, certification, export, and public release remain distinct.
Every later export or reimport must re-enter the Phase 5 boundary against
current authority; a historical reconciliation receipt cannot unlock it.
Private receipts and checkpoints contain protected identifiers, references,
and source text. Public reporting retains only approved aggregates and hashes.

## Verification and programme residual

`tests/test_word_card_universe.py` exercises independent source conservation,
homonym and sense identity, MWE and form counts, interruption boundaries,
transaction rollback, checkpoint corruption, stale certification, withdrawals,
reimports, missing inspection strata, and full-scale prerequisite refusal.
It uses source-free fixtures and never establishes Ukrainian validity.

The accountable `gemini-open-model-data` driver owns authentic execution and
programme acceptance. Dependencies are independently admitted complete source
and lexical inventories, exact-certified candidates, authentic full-scale
resource and resume trials, and held-out source-stratum inspection. Missing
evidence remains a residual rather than synthetic completion. The worker's
pushed implementation is subject to exact-head independent review and CI;
it does not close #10516 or #8977 by itself.
