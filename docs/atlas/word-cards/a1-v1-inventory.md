# Published A1-v1 vocabulary inventory

[`registry/atlas/a1-v1-inventory.json`](../../../registry/atlas/a1-v1-inventory.json)
records #11943 AC-01. It freezes the 55 published vocabulary files at Git commit
`770dadd3fb7d69512f5c05eaff6aa499c25f52fc`, with their Git blob IDs and SHA-256
hashes. The denominator is 2,144 rows and 1,296 normalized keys, comprising
1,116 single-token and 180 multiword keys. These keys count vocabulary inputs.
They do not establish lexical identity or certify word cards.

## Schema

The schema version is `atlas-a1-v1-inventory.v1`.

| Field | Meaning |
| --- | --- |
| `freeze` | Source Git commit, exact file inventory, byte hashes, row counts, unchanged pilot input hashes |
| `rows` | Every YAML row in file and array order, its complete original fields under `source`, lookup key and mapping. `source.lemma` or `source.word` retains the literal spelling |
| `rows[].id` | Repository-relative file path followed by a JSON Pointer into its parsed YAML document |
| `keys` | Normalized key to zero-based positions in `rows`, preserving repeated occurrences |
| `word_evidence` | Case-sensitive lookup to complete entry-qualified `inspect_word` analyses, a `verify_word` result count and hash, and a combined content hash |
| `lemma_evidence` | `verify_lemma` query, result count and hash, with a reference to the lemma's `word_evidence` |
| `sources` | VESUM canonical import identity and marker policy, Sources backend, consumed pilot query hashes |
| `counts` | Row dispositions, resolution states, pilot links and the reconciled denominator |

Keys use NFC normalization, remove U+0301 combining acute, strip edge whitespace
and case-fold, in that order. They retain punctuation, internal whitespace,
apostrophe spelling and slash alternatives. Original YAML values remain intact.
Common-word lookups use the unstressed lowercase form. Names retain their case.
The Sources backend treats ASCII apostrophe, U+2019 and U+02BC as equivalent
for lookup only. JSON content hashes use UTF-8, sorted keys, no ASCII escaping
and compact comma/colon separators. File hashes cover the original bytes.
Shared VESUM import metadata appears once under `sources`. The inventory uses
one record per line to keep the complete evidence below the repository file cap.

## Mapping dispositions

| `mapping.kind` | Disposition |
| --- | --- |
| `lemma` | One compatible, clean VESUM entry with an independently queried lemma |
| `ambiguous` | Several compatible VESUM entry IDs, including homonyms with identical lemma spelling |
| `name` | YAML explicitly labels a proper name. Its separate `resolution` is resolved, ambiguous or unresolved |
| `phrase` | Multiple tokens, or YAML explicitly labels a phrase or expression. No component replaces the whole |
| `slash_alternatives` | Ordered literal alternatives, with individual source queries. No alternative is selected |
| `unresolved` | No compatible attestation, marked or mixed analyses, or a missing lemma witness |

`resolution` is `resolved`, `ambiguous` or `unresolved`. Candidate entry IDs
refer to the full source analyses under `word_evidence`. All analyses remain
there, including those excluded by the row's explicit POS or proper/common
class. The normalization object publishes the exact POS-label constraints.
Translations and examples remain context, without supplying inferred meanings
or selecting among competing lexemes. Different grammatical cases of the same
entry may map to one lemma. Competing entry IDs remain ambiguous.

`mapping.pilot` reuses an existing card ID only when the existing authenticated
ULIF/VESUM paradigm matcher gives one high-confidence match. It records every
candidate pilot ID, source partition and matcher result otherwise. A lemma
outside the pilot has no card ID. The builder allocates no identities and does
not modify `pilot-v1.json` or `identity/registry.json`. Card production, meaning,
stress, examples, publication and practice remain outside AC-01.

## Deterministic replay

The builder calls the `verify_word`, `verify_lemma` and `inspect_word` backend
used by Sources, plus the existing pilot correspondence machinery. Stores open
read-only. It reads vocabulary bytes from the frozen Git objects rather than
the current working files. ULIF paradigms authenticate against the existing
raw-response cache. Missing authority or a changed pilot anchor refuses replay.
Changed Sources evidence produces a comparison failure rather than silently
updating the committed inventory.

```sh
.venv/bin/python -m scripts.atlas.a1_vocabulary_inventory --check
.venv/bin/python -m scripts.atlas.a1_vocabulary_inventory > registry/atlas/a1-v1-inventory.json
```

The default command emits JSON to stdout. `--check` compares bytes and prints
counts. Neither mode writes files or source stores. Shell redirection writes
the inventory. Run `--help` for explicit fixture store arguments.

## Slice 2 receipt batch

The approved [slice-2 manifest](../../../registry/atlas/a1-v1-slice2.json)
selects every inventory row with disposition `lemma`, resolution `resolved`
and an authenticated pilot `card_id`. This fixed batch contains 19 rows,
12 vocabulary keys and 11 existing cards. Its row ledger retains the other
2,125 mappings as `deferred_outside_slice2`. This batch starts #11943 AC-02
through AC-06. It does not complete the course denominator or certify cards.

The [allocation companion](../../../registry/atlas/identity/a1-v1-slice2.json)
appends source-local senses, source records and mint evidence to the frozen
base allocation. It changes no pilot file or original identity. The manifest
pins the base, companion and effective allocation independently. The assembler
refuses a different union before attaching assertions. Assembly never mints
identities, and the pilot's allocation validator keeps its original contract.

`scripts.atlas.a1_card_capture.capture` reads saved actual Sources replies and
authenticates the admitted complete ВТС witnesses. It performs no network
lookup or source-store write. The tool results retain their arguments, response
hashes, original source metadata and literal payloads. The source bundle is a
host-only input, pinned by the batch manifest. It must be retained for replay
and independent review. Capturing another source version requires a new freeze.

Each manifest claim selects an exact Unicode interval in a named payload.
Definition spans and labels keep their source-local sense scope. Mirrors retain
their source role. An English-to-Ukrainian hit requires an explicit usage-pair
mapping before it supplies an English gloss. Unaligned relation and mirror
units remain in the residuals. VESUM form alternatives share one grammatical
slot proposition, with a separate receipt for each form and its tags.

The builder writes only ignored output in its running dispatch worktree:

```sh
.venv/bin/python -m scripts.atlas.a1_word_cards \
  --sources batch_state/a1/sources.json --output batch_state/a1/batch.json
.venv/bin/python -m scripts.atlas.a1_word_cards \
  --sources batch_state/a1/sources.json --output batch_state/a1/batch.json --check
```

The output bundle has separate `.cards.json`, `.receipts.json`, `.rows.json`
and `.residuals.json` projections beside it. Each applicable field has an
accounting row. An unsupported field stays empty with its reason, dependency
and owner. Counts distinguish assertions, distinct receipts per field and
distinct receipts across the batch. The receipt verifier checks the delivered values,
subjects, source identities, sense scopes and field resolutions against the
frozen extraction recipes. The CLI's `--check` also rebuilds from the frozen
inputs and requires the supplied output bytes to match, including every row
mapping, review reference and residual state.

Examples stay empty until independent Ukrainian review approves the exact
quotation, source span, sense and A1 suitability. The approved evidence must
bind the receipt and sense, and must refer to the actual independent review.
A family label or a successful build does not establish that review. Changing
the manifest or review metadata changes the artifact and requires the ordinary
exact-head review gates.

After independent example approval, rebuild the bundle. Then require the real
end-to-end receipt chain:

```sh
.venv/bin/python -m scripts.atlas.a1_word_cards \
  --sources batch_state/a1/sources.json --output batch_state/a1/batch.json \
  --check --require-chain
```

This command refuses unless one actual card has a sourced meaning, stress,
VESUM forms and an approved example together. A draft build without that chain
is partial engineering evidence. Neither command publishes, grants practice
eligibility, changes the public preview or satisfies AC-07 through AC-09.

## Slice 3: cards for the first eight reviewed plans

The [slice-3 manifest](../../../registry/atlas/a1-v1-slice3.json) freezes
`reviewed_plan_vocabulary_to_inventory_mapping_lemma_v1`. It joins explicit
core, incidental and recycled vocabulary in reviewed positions 1–8 to
non-null inventory `mapping.lemma` values. W-ID references resolve through
the same revision's word registry; formulas retain their complete text.
The join normalizes NFC, removes combining acute, strips edge whitespace
and casefolds. It preserves original spelling, proper/common identity,
VESUM entry IDs and every repeated or inflected inventory occurrence.
Missing lemma mappings are never inferred from vocabulary keys.

The source is the specified reviewed-plan fallback commit
`e7a9ac497da8bbeba5531937a4c8543369462942`. That eight-plan edition was
not merged at the start of this slice. The manifest pins every consumed
plan file and the word registry. A [verbatim input snapshot](../../../registry/atlas/a1-v1-slice3-plan-inputs.json)
retains all ten approved Git blobs with an independent digest. Selection
rechecks the existing per-file hashes without requiring Git history,
including in shallow checkouts. The frozen selection contains 177 rows,
74 inventory keys and 45 targets: 41 lexemes and four proper names.
All fit the 60-card cap. The row ledger separately records the 19 rows
delivered by slice 2 and the other 1,948 deferred rows.

The [slice-3 allocation](../../../registry/atlas/identity/a1-v1-slice3.json)
appends to the exact base-plus-slice-2 union. It preserves existing IDs,
including the three source-adjudicated pilot candidates, and never changes
the pilot matcher or frozen inventory. Allocation creation is separate
from assembly. The builder consumes the reviewed allocation; it never
regenerates its IDs. Source disagreements, held source units and unsupported
fields retain their dependencies and Atlas coordinator ownership.

Slice 3 admits meanings from official СУМ-20, admitted ВТС or a qualified
ULIF sense gloss. It admits stress from qualified ULIF forms or an official
СУМ-20 accented headword. Mirrors, СУМ-11 and ВТС stress do not supply these
fields. Forms retain their VESUM entry, exact tags and source alternatives.
Examples remain empty until exact quotation, span, sense and A1 suitability
receive independent Gemini/AGY Sources approval.

The approved batch contains one complete chain for `мама`
(`wc_ea2fvbcb6p3k`): VESUM forms, ULIF stress, the ВТС maternal
sense and the exact textbook quotation «Моя мама найкраща!». Its
[example review](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/12221#issuecomment-6541516724)
binds the quotation, source span and sense. Other examples remain empty.

```sh
.venv/bin/python -m scripts.atlas.a1_slice3_inputs --check-selection
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice3 \
  --sources batch_state/a1-slice3/sources.json --output batch_state/a1-slice3/batch.json
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice3 \
  --sources batch_state/a1-slice3/sources.json --output batch_state/a1-slice3/batch.json \
  --check --require-chain
```

The Sources bundle is a pinned, host-only replay input retained in artifact
custody. The command writes the same four projections as slice 2. Delivery
verification compares all projection bytes with the verified main bundle;
the inherited CLI `--check` verifies only the main bundle. The default
`--batch slice2` keeps the original denominator, pins and behavior. This
batch does not publish cards, enable practice or close AC-07 through AC-09.

## Slice 4: the next 60 remaining entry-qualified targets

The [slice-4 selection inputs](../../../registry/atlas/a1-v1-slice4-inputs.json)
freeze source revision `0398eb5caa1c6a98dccaf9275520ccb2f978a95c` and join
`remaining_resolved_entry_priority_inventory_order_v1`. The input bytes are the
seven unchanged checked-in inventory, prior manifests, plan snapshot and identity
files named there. Independent raw-byte pins in `a1_slice4_inputs.py` and repeated
manifest pins verify those bytes without requiring historical Git objects. The
whole selection has its own independent canonical digest; the builder recomputes
and compares every selected target and row. Duplicate JSON keys refuse replay.

The [manifest](../../../registry/atlas/a1-v1-slice4.json) selects exactly 191
original occurrences for 60 VESUM entries. It excludes the disjoint 19 slice-2
and 177 slice-3 rows. The reviewed first-eight-plan snapshot has 84 normalized
terms and no preferred remaining target. Selection therefore uses the original
inventory order, with entry ID as the final tie-break. Whole formula references
remain whole. Of 1,948 remaining rows, 1,294 belong to the other 599 eligible
targets; 463 are ineligible: 272 phrase, 149 ambiguous, 18 name, 20 unresolved
and four slash-alternative rows. Every original occurrence remains in the ledger.

The [allocation companion](../../../registry/atlas/identity/a1-v1-slice4.json)
adds 58 cards to the unchanged base-plus-slice-2-plus-slice-3 registry. It reuses
`wc_yd5ekty2j7kb` for VESUM `422190`, ULIF `259921`, and
`wc_xbw7msqev2mz` for VESUM `17025`, common-noun ULIF `21977`. Their earlier
unsplit senses, spelling-only predecessors and the separate proper-name `Банк`
remain intact. Curator correspondences preserve the original pilot matcher's
unresolved results and source form alternatives. Independent exact-head Ukrainian
adjudication remains required. Assembly reads the allocation and never mints IDs.

Slice 4 retains the slice-3 authority map. Unsupported fields stay empty, with
reason, dependency and owner at every card and allocated sense. Each consumed
quotation must occur in its saved actual Sources response and its recorded
Unicode interval. Qualified ULIF supplies stress first; official СУМ-20 is the
fallback. Mirrors and ВТС never supply stress. The explicit ULIF animacy conflict
for `круасан` is retained and its stress stays empty. Missing cached numeric GRAC
attestation stays unknown. Pending examples belong to the independent reviewer;
missing sources and later curation belong to Atlas.

The current bundle holds the exact candidate quotation «Столиця України — місто
Київ.» from Большакова, Ukrainian language, grade 2, part 2, 2019, page 32. It
remains pending until independent Gemini/AGY Sources review approves its exact
quotation, span, settlement sense and A1 suitability. A pending candidate does
not establish a complete chain.

```sh
.venv/bin/python -m scripts.atlas.a1_slice4_inputs --check-selection
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice4 \
  --sources batch_state/a1-slice4/sources.json --output batch_state/a1-slice4/batch.json
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice4 \
  --sources batch_state/a1-slice4/sources.json --output batch_state/a1-slice4/batch.json \
  --check --require-chain
```

The host-only Sources bundle and generated output remain in durable artifact
custody. Delivery compares all four sibling projections with the verified main
bundle; the inherited CLI checks only the main bundle. F5–F8 remain Atlas-owned
P3 follow-ups, with this batch's actual stress references, literal quotation
containment and sibling comparisons recorded separately. This slice does not
close #11943, satisfy the issue-wide 50-card held-out requirement or publish a site.


## Slice 5: the next 60 allocated entry targets

The [slice-5 inputs](../../../registry/atlas/a1-v1-slice5-inputs.json)
preserve the approved proposal verbatim. Its canonical SHA-256 is
`584d3fa472b7973fbe896e9317437b101f11a46fbf635896780551fffcaacc14`.
The selector replays the original inventory and first-eight-plan join, excludes
prior allocations, and compares every selected target and occurrence with that
proposal. Independent raw-byte pins cover the unchanged inputs. Selection and
allocation do not certify earlier cards. All slice-4 review approvals remain
invalid until the required audit and independent review establish new evidence.

The [slice-5 manifest](../../../registry/atlas/a1-v1-slice5.json) selects
289 original rows for 60 entries. The complete row ledger preserves
2144 occurrences: 19 slice-2 rows, 177 slice-3 rows,
191 allocated and unreviewed slice-4 rows, 289 slice-5 rows,
1005 deferred eligible rows, and 463 ineligible rows.
The unchanged ineligible dispositions are 272 phrases, 149 ambiguous rows,
18 name rows, 20 unresolved rows, and four slash-alternative rows.
There are no preferred remaining targets in the original eight-plan join.

The [allocation companion](../../../registry/atlas/identity/a1-v1-slice5.json)
adds 59 cards. The existing `читати` card `wc_043h3npd7ed4` is reused
through VESUM entry `420694` and ULIF entry `258655`, preserving its original
unsplit sense and the separate spelling-only predecessor. The companion appends
49 source-local senses and preserves every earlier identity, source
record, and history event. Independent Ukrainian adjudication of the reuse
remains required. Assembly reads the companion and never allocates identities. The unchanged pilot
ULIF and PULS rows retain their original source-record IDs after complete
canonical-row comparison with the captured replies.

Literal runtime Sources replies supply VESUM forms, ULIF stress, ВТС meanings,
and PULS levels. Each consumed payload is rederived from its captured response.
Source-local Unicode intervals and response digests bind every quotation.
The official СУМ-20 reply for `прокидатися` remains available for adjudication
because its printed figurative labels conflict with the literal waking sense.
The separate ВТС waking sense is retained. СУМ-20 mirrors and historical evidence
remain contextual. No СУМ-11 field is asserted.

The malformed ULIF `хто` identity and duplicated wording in the ВТС `хто`
definition remain named gaps. Reference-only definitions and source misses stay
empty. Every empty field retains a reason, dependency, and owner. Missing numeric
GRAC evidence remains unknown. Missing source evidence belongs to Atlas.

The candidate example for `читати` is an exact original line from Савченко,
Ukrainian language, grade 4, part 2, 2021, page 93. Its source-local interval
is computed from the captured chunk. The example stays pending and its displayed
field stays empty until independent Sources review approves its exact version,
reading sense, and A1 suitability. No complete receipt chain is approved.

```sh
.venv/bin/python -m scripts.atlas.a1_slice5_inputs --check-selection
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice5 \
  --sources batch_state/a1-slice5/sources.json --output batch_state/a1-slice5/cards.json
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice5 \
  --sources batch_state/a1-slice5/sources.json --output batch_state/a1-slice5/cards.json --check
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice5 \
  --sources batch_state/a1-slice5/sources.json --output batch_state/a1-slice5/cards.json --check --require-chain
```

Slice-5 `--check` compares the rebuilt main bundle and all four sibling
projections. `--require-chain` refuses with
`reviewed_full_receipt_chain_pending` while no actual example has independent
approval. The governed source bundle, raw calls, per-card versions, projections,
and mandatory-row review packet remain in durable Fleet custody. Replays use
those frozen source bytes. Fresh source acquisition requires a new freeze.
This authoring slice does not close #11943 or its nine acceptance criteria,
fulfill the parent held-out and browser obligations, publish a site, or establish
independent semantic approval.

## Slice 6: next remaining entries, held for independent review

The [slice-6 inputs](../../../registry/atlas/a1-v1-slice6-inputs.json)
retain the approved proposal verbatim. The selector reproduces all
60 entries and 258 ordered occurrences from the original inventory,
excluding 676 prior allocated rows. The same eight-plan priority join
has no preferred remaining targets. Selection does not certify earlier slices.

The [slice-6 manifest](../../../registry/atlas/a1-v1-slice6.json) and
[allocation companion](../../../registry/atlas/identity/a1-v1-slice6.json)
append 57 card identities and 55 source-local senses. Existing ULIF-backed
identities for `яблуко`, `новий`, and `чорний` retain their IDs, original
unsplit senses, and separate spelling-only predecessors. Their correspondence
still requires independent Ukrainian review. Every prior creation key,
sense, source record, and history event is preserved.

Before allocation, the source census compares every consumed observation
with the full canonical pilot rows and the frozen slice-2 through slice-5
Sources bundles. It also compares the actual runtime calls. The six unchanged
ULIF and PULS rows for those three reused cards keep their original
source-record IDs. Different headwords returning the same unavailable
response remain separate query observations. An unavailable response supplies
no frequency claim.

The complete ledger retains all 2144 original rows:

| State | Rows |
| --- | ---: |
| `allocated_slice4_unreviewed` | 191 |
| `ineligible_slice6` | 463 |
| `delivered_slice2` | 19 |
| `allocated_slice5_unreviewed` | 289 |
| `delivered_slice3` | 177 |
| `card_produced` | 258 |
| `cap_deferred_slice6` | 747 |

The unchanged ineligible kinds are phrases, ambiguous rows, names, unresolved
rows, and slash alternatives. All original row mappings remain intact.

Literal Sources replies support VESUM forms for all 60 cards,
ULIF stress for 51 cards, and 55 ВТС definition spans across
52 cards. Every quotation interval and digest is computed from its
captured response. Official СУМ-20 misses and mirror-only replies remain
explicit. Mirrors and heritage evidence are contextual. СУМ-11 supplies no
normative field. Source retrieval times absent from a reply stay unknown.

Meanings remain empty for `вчителька`, `канадка`, `продавчиня`, `купити`,
`дорого`, `дешево`, and `глечик`, where the captured modern dictionary
misses or provides only a cross-reference. Stress remains empty for
`продавчиня` and the seven monosyllabic headwords without an explicit accent
in the captured priority sources. Unsupported fields retain a reason,
dependency, and owner. Source gaps belong to Atlas.

The frozen `скільки` target remains VESUM adverb entry `360598`.
The captured ULIF numeral and ВТС quantity-question sense have no adjudicated
correspondence to that entry. Its meaning and stress fields remain empty,
and its three price-question rows carry an explicit identity and sense hold.
Atlas owns source reconciliation; an independent Sources reviewer owns the
linguistic verdict. The first committed allocation excludes the unsupported
anchor and provisional sense from the unpublished author attempt. That attempt
is retained in Fleet evidence, and its withdrawn provisional sense ID stays
reserved. Every prior committed identity and mint remains unchanged.

The candidate `вода` example retains the original sentence and line break
from Захарійчук's 2025 grade-1 буквар, chunk
`1-klas-bukvar-zaharijchuk-2025-2_s0080`. Its displayed field stays empty.
Independent Sources review must establish the exact-version quotation,
sense, and A1 suitability. No example approval or complete chain is claimed.

The generated field ledger contains 1494 rows:
443 supported, 866 empty, and 185 not applicable.
The full raw Sources bundle, per-card versions, all four projections,
source identity census, and mandatory 60-entry review packet are retained
in durable Fleet custody. Replays use the exact sealed source bytes.

```sh
.venv/bin/python -m scripts.atlas.a1_slice6_inputs --check-selection
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice6 \
  --sources "$TMPDIR/sources.json" --output "$TMPDIR/cards.json"
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice6 \
  --sources "$TMPDIR/sources.json" --output "$TMPDIR/cards.json" --check
.venv/bin/python -m scripts.atlas.a1_word_cards --batch slice6 \
  --sources "$TMPDIR/sources.json" --output "$TMPDIR/cards.json" --check --require-chain
```

`--check` compares the rebuilt main bundle and all four sibling projections.
`--require-chain` refuses with `reviewed_full_receipt_chain_pending` until a
real example has independent approval. Slices 4 and 5 are merged, and this PR
now targets `main`. It remains held pending the review infrastructure gate,
explicit release, current-head CI, and independent review of all 60 entries.
#11943 and all nine parent criteria remain open. This slice supplies no
publication, browser acceptance, or independent held-out proof.
