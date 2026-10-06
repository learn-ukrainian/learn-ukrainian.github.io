# RB-1 framework interface

This package implements the approved [review-build design](../../../../docs/projects/open-model-data/REVIEW_BUILD.md).
The CLI loads extractors and attribution adapters only through the closed, lazy
registry in `components/__init__.py`. Component modules expose one `COMPONENT`
object. Request files supply host-local data paths, never executable import names.
The library uses the same registered components through
`execute(config_path, guarded_output, components=..., adapters=..., files=...)`.

The CLI defaults to the host-local `batch_state/review_build/request.json` in the
shared repository, resolved through Git's common directory in a worktree.
Initialize the location-only request once, then use it for builds:

```bash
.venv/bin/python -m scripts.projects.open_model_data.review_build init-request
.venv/bin/python -m scripts.projects.open_model_data.review_build build --out "$TMPDIR/rb1-c9" --components C9
.venv/bin/python -m scripts.projects.open_model_data.review_build verify --out "$TMPDIR/rb1-c9" --components C9
```

`--components C3 C4 --components C9` is repeatable; omission selects all components
in the closed registry. Unknown or unavailable components fail closed. `--config`
overrides the default. Build and verify must use the same selection, pinned in the manifest.
The default does not invent extractors or reviewed specs for unfinished packets.
Only selected component modules are imported. Unknown ids refuse; an unfinished
module returns `component_unavailable` with that id alone. Competing adapters for
one source refuse `adapter_conflict`; components sharing a source must share the
same adapter object. C6a/C6b are separate build/accounting components using the
catalog's shared C6 instructions; both retain C6's UA-GEC admission rules.

## Adding a component

1. Implement only the module mapped to your assigned id in the literal registry
   (`C1` → `c1.py`, through C9; C6a/C6b have their own modules). Export one
   `COMPONENT` object implementing the protocol in `components/__init__.py`:
   `spec`, `adapters`, and `iter_candidates(ctx)`; optional `files` maps file-store
   names to `FileStore` adapters. The framework refuses request-defined imports.
2. Put reviewed common policy in `spec` and each operation's binding, independent
   unit query, measured frozen count and primary unit identity in
   `spec["operation_specs"]`. Keep the existing closed `operations` and `reasons`
   declarations. Declare `spec["compatibility"]` as a list of reviewed citation-role
   entries (source identity, store/table, source column/values, role, sensitivity
   and quarantine mappings). Declare `spec["corpus"]` when using UA-GEC, with the
   split/document/author/layer/text column mapping. These declarations are copied
   and pinned with the spec; the gate unions only selected component policies.
   Identical table entries are deduplicated; different entries for one
   `(store, table)` refuse `compatibility_conflict`. Competing corpus mappings
   refuse `corpus_conflict`. Attribution adapters are keyed by register `source_id` and
   authenticate complete bibliography mapping. Reuse a shared adapter instance
   when several components cite the same source.
3. Iterate source rows using `ctx.reader` (the same pinned read transaction used
   by the gate). `ctx.request` supplies a detached, deeply read-only snapshot of
   host-local input configuration; mappings are read-only and sequences are tuples.
   Mutation raises. The framework copies component specs before extraction and
   refuses changes to their pinned digests as `spec_mutated`. Return
   `Candidate` objects for every independently counted unit, including withheld,
   rejected and excluded ones. Never open writable databases or import code from
   request paths. Component file adapters are installed before this reader opens.
4. Run `init-request` (or use `--path P` and then `--config P`) to locate the
   catalog, register, source stores and UA-GEC root. Select ids with CLI
   `--components`, then build and verify with the same selection. The manifest pins
   component specs, generated candidates and all package source files, including
   registry and component code. Generic mutations
   must refuse; the component owns additional semantic must-fail cases.

Tests can pass in-process objects through `main(..., _test_components={...})` or
`load_components(..., _test_overrides={...})`. These seams have no CLI flag or
request-file representation and cannot add ids outside the closed registry.
`test_components.py` proves extraction, adapter wiring, operation accounting,
all five verify mutations and tamper refusal using synthetic SQLite rows.

## Request

`omd-review-request.v2` carries input locations only: required `catalog` and
`register` (YAML paths), `databases` (`store` → database path), and
`ua_gec` containing only `root` (the corpus directory path). Tests may also supply
`synthetic_sources`, restricted to ids starting with `synthetic` and register
forms starting with `SYNTHETIC `. Every other key, including `compatibility`,
`corpus`, `components` or `candidates`, refuses `request_policy_key`. v1 refuses
`request_schema` with a migration hint. Request JSON never selects components or
provides admission policy.

`init-request [--path P]` creates a 0600 file in a 0700 parent, pointing at the
shared repository's `data/sources.db`, `data/vesum.db`, `data/ua-gec`,
`registry/projects/open_model_data/instruction_catalog.yaml` and
`docs/sources/permissions-register.yaml`. It refuses existing files and symlinks;
a pre-existing parent must already be private. Without `--path`, it writes
`batch_state/review_build/request.json`. Build/verify without `--config` read
that file; absence refuses `request_missing` with an `init-request` hint.
Relative input paths resolve against the request's directory. Real callers
supply `AttributionAdapter` and `FileStore` objects through registered code.

Input file bytes, the location-only request, copied component declarations
(including admission policy), framework source files, checkout SHA and
file-store digests are pinned in the manifest. DB snapshots pin cited columns'
bytes as `(row_key, field_sha256)` pairs, not entire rows. `verify` re-runs the
gate against the live DB and compares all expected output bytes, including
provenance and pins. It then generates and checks generic mutation fixtures
under `--out/mutation-fixtures/`. Those private fixtures are not committed or
included in the build manifest.

## Component specs

C1 and C6a use the held official UA-GEC reader. Their registered component
specs own the UA-GEC compatibility, sensitivity and corpus mappings; the request
supplies only `ua_gec.root`. The root must match the shared repository's
`data/ua-gec`, so request data cannot select another executable reader package.
Each build/verify opens a fresh file store. Authentic reasoning-marker sentences
are withheld as `reasoning_marker_in_source`. Raw markup outside the reader's
parsed spans, including markers split across newlines and unauthenticated stray
braces, is withheld as `unparsed_annotation_markup`; parsed delimiters and learner
braces inside authenticated source spans remain source text.

Every component spec requires:

- `unit_query`: `{kind: sql, store: ..., sql: SELECT ..., parameters: [...]}`;
  exactly one column gives the canonical unit id. File stores implement their
  own reviewed independent unit query (for example a glob plus official reader).
- `unit_id`: `{primary: [{selector: ..., store: ..., table: ..., key: ...}],
  separator: ";"}`. Selectors name primary citations only; each part pins the
  store/table and extracts the named primary-key component from `row_key` (omit
  `key` to use the whole row key). Joining the parts must equal the independent
  query's unit id. Swapped citations fail `unit_id_mismatch`, including on
  withheld/excluded accounting rows.
- `frozen_count`: exact measured count at that unit grain.
- `reasons`: closed arrays for `accepted`, `rejected`, `withheld`, `excluded`.
  Include framework withholding codes `attribution_unresolved`,
  `locator_unavailable`, `catalog_inapplicable` where applicable. Reason codes
  must be lowercase ASCII identifiers for the safe manifest projection.
- `operations`: closed catalog operation list; empty record buckets are reported
  as missing coverage, never PASS.
- `binding`: `binding-spec.v1` with a nonempty `rules` array (below).

For operations with different unit domains, keep `operations` as the closed list
and declare `operation_specs: {operation: {unit_query, frozen_count, unit_id,
binding, ...}}`. Every listed operation requires all four declarations. Common
reasons, transforms and serializers may stay on the component; operation keys
override them. C3's ULIF sections and sense definitions can use different primary
tables, counts, identity and binding rules. Accounting enforces each operation
separately, then aggregates component totals. Reused ids across operations are
allowed; duplicates within an operation fail. The manifest's
`operation_accounting` records separate denominators. Flat specs retain their
existing shared unit domain.

Span/composite identity uses `unit_id: {format: citation.v1, primary:
[{selector: ..., store: ..., table: ..., span: true}, ...]}`. The gate emits
canonical compact JSON of ordered identities `[[store, table, row_key,
[start,end]], ...]`; omit `span` for a row-only part. Every part selects a primary
citation, with its actual store/table/key revalidated. A multi-selector can
select an ordered composite of primary citations from several values/pages.
The independent unit query must emit the same JSON (SQL `json_array` can produce
it). Query ids must equal candidate ids, recomputed by the gate for all outcomes.
Two headings on a page differ by span; multipage bodies can bind every page.
`key` is disallowed for `citation.v1`, preserving the complete primary key.
Legacy joined identity also supports `span: true`, appending canonical
`[start,end]` with its declared separator.

Optional keys: `slot_serializers` maps C2's `slot` to `{id:
c2-header-cells.v2, section: [source slot names], row: source slot name or null,
column: [source slot names]}`. It emits the catalog's positional three-element
JSON header array using only cited cell text and fixed separators; absent levels
remain positional empty arrays/strings, and all-empty cells withhold.
Other optional keys: `transforms` (closed transform id to policy),
`context_serializer` and `response_serializer` (`text` joins exact parts with LF;
`json_array` uses canonical JSON string arrays), `unit_grain`, `annotation_layer`,
`reference_multiplicity` (reviewed README metadata), and `applicability` for each variant operation.
The catalog's `sense_variant` declarations supply variant names; operation
contracts' applicability declarations must include every referenced variant.
Template slot differences supply presence predicates: populated varying slots
must remain visible, and omitted varying slots must still exist as empty strings.
No variant names are embedded in the framework. Every declared variant also
requires nonempty component-owned source predicates keyed by that exact name:

- `[selector, expected_source_value]` compares an independently read source operand.
- `{query: unit_query, parameters: [selectors...], expected: [values...]}` compares
  the exact one-column query result, with parameters derived from cited rows.

The gate evaluates predicates for slot-compatible variants and requires exactly
one variant to pass. Missing declarations are mechanism failures
(`applicability_spec`). A component must classify a unit with no eligible variant
as withheld (`catalog_inapplicable`); an accepted candidate with no passing variant
aborts the build.
C2 predicates authenticate discrimination, equal homonym forms and absence of
parse errors. C3 predicates authenticate the selected article's unquarantined
sense count and that sense's citations, including model-visible same-sense
context for the citation variant. The catalog's prose states those semantic
requirements; component-owned selectors, queries, bindings and tests implement
them. The framework never interprets prose as code or trusts candidate flags.

`record_id` includes every slot, context and response value, in contract order;
quotation and attribution are rechecked for each citation. Rejected candidates
must carry positive citation evidence: each `evidence` entry is the SHA-256 of
canonical JSON of one cited `Citation` object (`gate.evidence_id`). Withheld and
excluded candidates retain nonempty reason evidence. Unresolved attribution or
catalog applicability changes an accepted candidate to withheld, preserving its
unit and values in private candidate accounting. Other mechanism failures fail
the build. Duplicate instruction/response pairs from distinct units are reported.

## Binding-spec.v1

A selector is `{area: slots|context|response, slot: name, citation: index,
field: optional_column}`. Index defaults to zero; `field` selects a source row
column. Without `field`, index zero selects quoted value text; a supporting index
selects that citation's independent source field. Unknown rules fail closed.

Add `match: all, min: N` to select every value with that slot in contract order
(N defaults to 1 and must be at least 1). `index: I` selects one occurrence of a
repeated slot; scalar selectors still require exactly one value. Add
`citation: all, citation_min: N` to quantify over every citation of each selected
value. Expanded refs keep both indices: evidence for one repeated slot cannot
authenticate another. `equal`, `literal`, `same_row`, `one_group` and
`contiguous_pages` quantify over expanded selectors. Scalar-only operations
refuse inappropriate cardinality. Sense/article `one_group` rules with
`citation: all` check every witness; quotation agreement is still required.

- `equal`: `values` selectors must have equal source operands.
- `literal`: one `values` selector must equal `expected` control metadata.
- `same_row`: `values` citations share store, table and the real primary key.
- `whole_field`: every selected primary value has no span and equals its entire
  independently transformed source field. This refuses a correctly quoted
  fragment substituted for a required complete paragraph.
- `pattern_absent`: a nonempty reviewed regular expression must not match any
  selected text operand (for example an unresolved printed line-end hyphen).
- `one_group`: `values` operands are non-null and identify one group.
- `example_list`: one `values` selector's span must equal a whole trimmed
  comma/semicolon-delimited item after an example-introducing colon. Regions end
  at the sentence's period followed by whitespace and an uppercase letter, a
  later colon, or a line boundary before a numbered/rule line. Each colon is
  considered independently. Explicit example introductions permit one item;
  otherwise a comma/semicolon list is required. Ambiguous prose is refused.
- `contiguous_pages`: `values` page columns equal `range(first, next_heading)`
  and their `source_field` columns name one book. Bounds can be integers, source
  selectors, or `{query: unit_query, parameters: [selectors...]}` producing one
  integer from an independent read query. WP5 supplies reviewed heading detection
  and the independent next-heading boundary query.
- `form_agreement`: two `values` selectors match after NFC and removal of the
  combining acute accent; `left_tags` and `right_tags` from the respective cited
  rows agree. Stored/model-visible bytes remain unchanged.
- `set_query_equal`: `values` selects the record's variants (use `match: all`);
  `normalizer` is `identity` or `unstress_nfc`. `queries` is a nonempty list of
  `{query: {kind: sql, store: ..., sql: SELECT ...}, parameters: [selectors...]}`.
  The gate derives scalar parameters from cited operands, runs each one-column
  query in the pinned read transaction, normalizes for comparison only, and
  requires **each** result set to equal the record value set. Repeated source
  rows collapse as sets; missing, extra or divergent variants fail. This checks
  complete variant agreement independently of extraction, without replacing
  quotation or supporting-citation authentication.
- `contrast_pair`: selectors `rejected`, `recommended`, `response` establish the
  visible direction. `book_rejected`/`book_recommended` cite one `book_source`
  row that contains both members as whole Unicode tokens (including apostrophes
  and combining marks); `rejected_key`/`recommended_key` bind their separate forms.
  `sum11_source` must equal the rejected member after unstressing;
  `ulif_source` and `vesum_source` independently attest the recommended form.
  `receipt` selects a cited adjudication row whose `pair_field` names the shared
  book row key and whose `sol_field`/`opus_field` are APPROVE. WP6 owns receipt
  authenticity and the source-specific adjudication contract and tests.

Optional rule-level `citation_field` pins the actual citation field, and
`locator_field` names the held row column that must equal each citation's
locator. Both constraints quantify over every expanded witness.

Supporting citations must connect to their own primary citation through
exact-field equality/form agreement, or the contrast rule's independently checked
book/form witnesses. Mentioning a supporting row or comparing it with itself is
insufficient. Structural binding is mechanism proof; D3 supplies semantic judgment.

## Citation roles and splits

SQL unit queries may call `omd_example_spans(text)`, the closed `example_list`
binding grammar exposed as a deterministic JSON array of `[start,end]` spans.
`json_each` can then enumerate primary citation identities independently of a
component's candidate stream. It never accepts request-defined parsers.

Each compatibility row requires `store`, `table`, `source_id`, `role` (one of
`modern`, `sum11`, `ua_gec`, `textbook`, `forbidden`). All citation triples must
match this reviewed table. Each entry also requires `source_column` and nonempty
`source_values`: the cited row must have that column and one of its expected
values. Missing columns and unexpected values fail `source_compatibility`.
Source roles, sensitivity, split and file names are read from the cited row, never
candidate metadata. Optional field mappings:
`source_file` (default `source_file`), `sensitive` (required column name or null
for sources with no sensitivity concept),
`quarantine`. UA-GEC mappings require `split`, `document`, `text`, `layer`, `edits`.
UA-GEC always requires sensitivity (default column `is_sensitive`); null cannot
disable it. Other sources default to none. Any declared sensitivity column must
be present with a known 0/1 value: unknown fails `sensitivity_unavailable`, and
1 fails `sensitive_source`. Textbooks require exact `allowlisted_files`, and the
cited `source_file` must match `N-klas-*` for N=1–11, `10-11-klas-*`, or `uni-*`.
The combined-grade pattern follows the two measured source filenames; other
grade ranges are refused until authenticated. Admission is re-derived from each
cited row, even when grade metadata is zero or misleading. Grade metadata
does not control admission; university grade-0 rows are admitted by allowlisted
filenames. СУМ-11 requires
`risk` and `keywords` (defaults `sovietization_risk`, `sovietization_keywords`),
an admitted C7 contrast, opt-in/context flags, and use only in the rejected
model-visible member. Risk and keywords are copied from the source to provenance.

The component spec's `corpus` mapping supplies `store`, `table`, `split`, `document`,
`author`, `layer`, `text`. The gate independently scans that corpus, orders whole
train authors by SHA-256 of `omd-rb1-dev` + author id, and includes authors until
at least 10% of gec-only train documents are carved out. Test sentence overlap
uses NFC, casefold and collapsed whitespace, then UTF-8 SHA-256. Both layers
exclude all documents of carved authors, including fluency-only documents. C6
UA-GEC citations must be gec-fluency rows with nonempty all-`F/Calque` edits. WP1 supplies the official-reader file-store adapter
and its metadata/annotation-unit bindings; no DB or corpus text is embedded here.

`line_excision@1` requires full-line regular-expression `patterns`; it records
1-based dropped line ranges. `dehyphenate@1` requires `{store: vesum.db, table:
..., field: ...}` and joins only a positively attested combined form whose
hyphenated form is unattested, recording original offsets and each join. HTML
text nodes retain document order; whitespace collapses without added words.

## Attribution and repository configuration

An adapter must keep `mapped_form == form`; the register form may contain
placeholders once the adapter resolves them. The resulting bibliography must
have no placeholders or instruction text (`instruction_form` must be false).
Adapters can call `reader.read_repository_config("scripts/config/vesum_source.lock.json")`
for raw pinned bytes. Names must be repository-relative and cannot escape through
traversal or symlinks. Each file is read once per reader; the manifest's
`repository_configs` records its SHA-256. A new verify run re-reads it and refuses
drift, including changes to configuration bytes that leave rendering unchanged.

## Output and proof boundary

Directories/files are `0700`/`0600`, with umask `077`; descriptor-relative writes
refuse symlinks, hardlinks, unsafe modes/ownership and POSIX ACLs. Linux mountinfo
must match the resolved target's device (or its nearest existing ancestor) and
identify ext4, xfs or btrfs. Among matching entries the last at the longest path
prefix wins; missing or ambiguous matches refuse, as do unreadable checks.
Read/write OS errors fail `output_io`. Repository ancestry
is checked without Git commands or environment variables. Tracebacks are private
output files only; stdout/stderr carry fixed status/error codes, digests, counts,
record ids, components and hashed row keys, never source locators or paths.

`private-manifest.json` is a schema-checked projection of hashes, counts,
versions, code SHA and reason-code tallies. It contains no arbitrary string
fields or Cyrillic. It is written only under guarded output; this framework
never commits it. The README marks insufficient/missing operation evidence as
not training-ready. D2, fresh independent D3, real component fixtures and real
RB-1 delivery remain driver/component responsibilities. `verify` owns the generic
absent-quote, wrong-span, empty-locator, missing-unit and swapped-citation
fixtures, derives them from an admitted component's actual candidate citations,
and requires their specific gate refusals. A build with no admitted candidate or
no distinct donor citation fails `mutation_unavailable`; a passing mutation
fails `mutation_admitted`. Selected registered components may expose optional
`COMPONENT.mutation_fixtures(ctx, candidates, gate)`, yielding `MutationFixture` objects
with a private payload, stable name, expected error code and gate probe. CLI
`verify` runs every yielded probe and requires that exact `BuildError` code;
success, a different refusal, duplicate names or an empty generator fail verification.
Payloads and `component-results.json` stay under the guarded host-only output.
Component-specific fixture definitions stay with WP1–WP6.

`dehyphenate@2` preserves `@1` and resolves each printed line-break hyphen,
including stored inline alternatives, with a held folded VESUM form index or
an unhyphenated whole-token witness in the same held source corpus. The policy
adds `lookup_field`, `normalizer: vesum_fold`, and a `witness` mapping identifying
store, table, text field, source column/id, alternatives field and count field.
Both readings attested, neither reading attested, or unmatched metadata remain
unresolved. A hyphenated VESUM form prevents a join; when only that form is
attested, the hyphen remains and only line whitespace is removed. Every decision
records its raw offsets, resulting form and evidence kind in `join_evidence`;
`joins` continues to record actual hyphen removals. Held text and metadata reads
are pinned in the source snapshot. No word lists or source edits participate.

The `transform_resolved` binding recomputes `dehyphenate@2` from the cited
field and checks unresolved positions only where the value's visible span
carries them, projecting original offsets through earlier resolved edits.
Unlocated metadata fails closed. Whole-field responses carry every position.
`source_text_defect` requires positive lost-boundary evidence in the cited
original text; dictionary absence and possible splits into dictionary forms
do not establish that a word printed by the source is defective. Detected
boundary loss is withheld, never repaired. This check does not certify a PDF
extraction: comparison with the printed source remains separate evidence.
C5 retains raw printed example spans and quotes for identity and `example_list`
binding; its catalog target is the complete paragraph with the resolved reading.
Paragraph reasons are `paragraph_hyphenation_unresolved`, `source_text_defect`
or unavailable metadata. Bibliographic attribution remains a separate gate.
C5 uses register id `pravopys_2019` while its source-row keys retain
`pravopys_2019_official`. Its adapter authenticates the register's edition
statement against the held bibliography, file digest and pinned official-source
document, and substitutes the cited paragraph number in the register placeholder.
The catalog requires complete § responses, so an unresolved hyphen in any
included example is also visible in every other record carrying that §.
