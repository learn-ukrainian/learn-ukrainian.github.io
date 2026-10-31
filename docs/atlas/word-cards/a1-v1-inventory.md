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
distinct receipts across the batch. The verifier checks the delivered values,
subjects, source identities, sense scopes and field resolutions against the
frozen extraction recipes without rebuilding the cards.

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
