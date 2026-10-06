# RB-1 framework interface

This package implements the approved [review-build design](../../../../docs/projects/open-model-data/REVIEW_BUILD.md).
It contains no component extractor, real attribution adapter or real dataset fixture.
Call `execute(config_path, guarded_output, adapters=..., files=...)` from component
integration code, or use the module CLI for a JSON request. Adapters are passed as
objects implementing the published protocols; request files cannot import code.

## Request and component specs

`omd-review-request.v1` requires `candidates` (JSONL of the frozen `Candidate`
contract), `catalog` and `register` (YAML), `databases` (`store` to path),
`components` (component id to spec), and `compatibility` (citation role rows).
Relative input paths resolve against the request's directory. `synthetic_sources`
permits only ids starting with `synthetic` and register forms starting with
`SYNTHETIC `. Real callers supply `AttributionAdapter` and `FileStore` objects.
Input file bytes, component declarations, framework source files, checkout SHA,
read rows and file-store digests are pinned in the manifest. Verification reruns
all gates and compares all expected output bytes, including provenance and pins.
It then generates and checks generic mutation fixtures under `--out/mutation-fixtures/`.
Those private fixtures are not committed or included in the build manifest.

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

Optional keys: `slot_serializers` maps C2's `slot` to `{id:
c2-header-cells.v2, section: [source slot names], row: source slot name or null,
column: [source slot names]}`. It emits the catalog's positional three-element
JSON header array using only cited cell text and fixed separators; absent levels
remain positional empty arrays/strings, and all-empty cells withhold.
Other optional keys: `transforms` (closed transform id to policy),
`context_serializer` and `response_serializer` (`text` joins exact parts with LF;
`json_array` uses canonical JSON string arrays), `unit_grain`, `annotation_layer`,
`reference_multiplicity` (reviewed README metadata), and `applicability` for C2.
C2 `with_sense`/`without_sense` are arrays of `[selector, expected_source_value]`
assertions. These must authenticate discrimination, equal homonym forms and the
absence of group parse errors from source rows, never candidate flags. Source
cell authentication and complete variant-group agreement belong to WP2's binding
spec and component tests; this framework does not infer them from model text.

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

- `equal`: `values` selectors must have equal source operands.
- `literal`: one `values` selector must equal `expected` control metadata.
- `same_row`: `values` citations share store, table and the real primary key.
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
- `contrast_pair`: selectors `rejected`, `recommended`, `response` establish the
  visible direction. `book_rejected`/`book_recommended` cite one `book_source`
  row that contains both members as whole Unicode tokens (including apostrophes
  and combining marks); `rejected_key`/`recommended_key` bind their separate forms.
  `sum11_source` must equal the rejected member after unstressing;
  `ulif_source` and `vesum_source` independently attest the recommended form.
  `receipt` selects a cited adjudication row whose `pair_field` names the shared
  book row key and whose `sol_field`/`opus_field` are APPROVE. WP6 owns receipt
  authenticity and the source-specific adjudication contract and tests.

Supporting citations must connect to their own primary citation through
exact-field equality/form agreement, or the contrast rule's independently checked
book/form witnesses. Mentioning a supporting row or comparing it with itself is
insufficient. Structural binding is mechanism proof; D3 supplies semantic judgment.

## Citation roles and splits

Each compatibility row requires `store`, `table`, `source_id`, `role` (one of
`modern`, `sum11`, `ua_gec`, `textbook`, `forbidden`). All citation triples must
match this reviewed table. Each entry also requires `source_column` and nonempty
`source_values`: the cited row must have that column and one of its expected
values. Missing columns and unexpected values fail `source_compatibility`.
Source roles, sensitivity, split and grade are read from the cited row, never
candidate metadata. Optional field mappings:
`source_file` (default `source_file`), `sensitive` (default `is_sensitive`),
`quarantine`. UA-GEC mappings require `split`, `document`, `text`, `layer`, `edits`.
UA-GEC and textbook roles require a present, non-null sensitivity column with a
known 0/1 value; a missing/unknown value fails `sensitivity_unavailable`.
Textbooks require `grade` and exact `allowlisted_files`; school grades are 1–11,
university rows use `university` and an allowlisted `uni-*` file. СУМ-11 requires
`risk` and `keywords` (defaults `sovietization_risk`, `sovietization_keywords`),
an admitted C7 contrast, opt-in/context flags, and use only in the rejected
model-visible member. Risk and keywords are copied from the source to provenance.

The request's `corpus` mapping supplies `store`, `table`, `split`, `document`,
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
fails `mutation_admitted`. Component-specific mutations stay with WP1–WP6.
