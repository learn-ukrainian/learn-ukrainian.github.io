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
