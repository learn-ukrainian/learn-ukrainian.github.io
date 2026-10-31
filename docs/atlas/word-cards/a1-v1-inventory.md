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
plan file and the word registry. The frozen selection contains 177 rows,
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
