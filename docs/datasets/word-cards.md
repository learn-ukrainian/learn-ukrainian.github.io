# Word-card dataset

The local release engine is
`scripts.projects.open_model_data.word_cards.dataset_projection`.
It produces versioned, cited JSON or JSONL packages from Atlas word cards.
It does not publish a package or grant linguistic certification.

Intended uses include citation-aware lexical research and reproducible model-data
experiments under the recorded source terms. Consumers retain field citations
and distinguish parallel source assertions from resolved language answers.

## Sources and permissions

[The permissions register](../sources/permissions-register.yaml) records source
scope, attribution, license terms, operator decisions, and removal routes.
The projection includes an assertion only when its source explicitly lists
`dataset` in `appears_in`. Unknown sources and internal-only sources are filtered.
The register digest in the card's build inputs must match either the current
file bytes or the canonical digest of referenced entries and their cited legal
references. Entries may cover all register sources or the card's assertion
sources. Pilot assembly binds the source list in
`registry/atlas/pilot/pilot-v1.register-pin.json` across the whole build,
including sources absent from an individual card. The projection recomputes
that digest from the current register, so unrelated additions are allowed and
changes to referenced entries or legal references are refused. The release
manifest always records the whole current register file digest.
The assertion's `licence_ref` must name the same source and register schema version.

Dataset scope is distinct from an open license. Recorded operator decisions
permit some proprietary sources. The engine preserves their actual terms and
does not relabel them as open data. VESUM records CC BY-NC-SA 4.0 for dictionary
data, ULIF records proprietary terms, and other sources retain their own entries.
There is no blanket license that replaces these source terms.

By default, every input card must pass
[`load_certified_card_for_export`](../../scripts/atlas/word_card_certification.py)
with dataset approval. Set `allow_candidates=True` in `create_release` or
`withdraw_release`, or pass `--allow-candidates` to the CLI, to include
uncertified cards with `status: "CANDIDATE"`. Each card still passes the
assembled-card schema, register binding, citation checks, and withdrawal filters.
Only active cards may be projected. A failed, missing, withdrawn, or inapplicable
certification never earns `CERTIFIED` status. Candidate output grants no
certification or publication approval. Public releases requiring certification
must retain the default `allow_candidates=False`. See the certified-card
[acceptance and export invariants](../atlas/word-cards/export-invariants.md).

## Input formats

`--cards` accepts a single card, a JSON array, a card-ID map, an assembly object
with a `cards` member, JSONL, or a directory of card JSON files. An assembly
directory can contain a `cards/` subdirectory.

`registry/atlas/pilot/pilot-v1.json` is a frozen input manifest. When given this
manifest, the loader calls existing Atlas assembly with the identity registry
and read-only source stores. The resulting pilot cards need exact-artifact
dataset certification for `CERTIFIED` status. Candidate projection requires
the explicit opt-in above. Assembly success grants no approval.

## Release schema

The manifest schema identifier is `word-card-dataset.v1`. Release versions use
the form `v0.1.0-pilot`. Each fresh output directory contains:

| Artifact | Contents |
| --- | --- |
| `word-cards.jsonl` | One card per line, UTF-8, sorted by card ID |
| `word-cards.json` | Alternative JSON array selected with `--format json` |
| `manifest.json` | Versions, exact dataset SHA-256 and byte count, denominators, source breakdown, register digest, input digest, and cumulative withdrawals |
| `withdrawal-notice.json` | Present for a withdrawal, with selector, justification, previous and replacement digests, and removed citation count |

Each dataset card contains:

| Property | Meaning |
| --- | --- |
| `card_id` | Original stable card ID |
| `card_version` | Explicit input `card_version`, otherwise `build.card_version`, with `0.1.0` as fallback |
| `card_kind` | Original card kind, such as `lexeme` |
| `status` | `CERTIFIED` only after exact-artifact dataset certification passes; otherwise `CANDIDATE` when allowed |
| `known_gaps` | Input `known_gaps` array, or `[]` when absent; declared gaps are metadata, not cited language facts |
| `fields` | Surviving cited assertions, sorted by `assertion_id` |

The projection accepts optional top-level `card_version` and `known_gaps`
annotations alongside the assembled-card schema. The version must be a nonempty
string and gaps must be an array. Other schema constraints remain binding.
Certification checks the exact original card through its existing schema and
authority; adding annotations cannot preserve an earlier certification.

Each field has these properties:

| Property | Meaning |
| --- | --- |
| `assertion_id` | Original assertion identity |
| `subject` | Original card, sense, or link subject |
| `field` | Original field name |
| `value` | Source-backed assertion value |
| `citation` | Source ID, snapshot, locator, optional persistent source-record ID and key, original `licence_ref`, register attribution, license terms, and terms reference |

The projection preserves parallel assertions. It does not select a modern
definition from conflicting sources. Cached field resolutions, identity keys,
links, and quality prose cannot add uncited fields. Only the version and gap
metadata described above accompany the cited assertions.

Canonical JSON sorts object keys, uses compact separators, preserves Unicode,
rejects nonfinite numbers, and ends with a newline. The dataset digest covers
the exact exported bytes. Repeating an export with identical inputs and options
produces identical dataset and manifest bytes. No clock value enters a release.
The existing RB-1 output guard requires private output outside every checkout.
Directories use mode `0700` and files use mode `0600`. Symlink routes and
existing output directories are refused. The manifest is written last.

`card_count` counts cards with at least one included assertion.
`certified_count` and `candidate_count` count emitted cards by status and sum to
`card_count`. Inputs with no surviving assertions do not increase these counts.
`field_citation_count` counts included assertions, including parallel citations.
Input card and assertion counts retain the original denominator. Source breakdowns
count included and filtered assertions and unique source rows. A row is identified
by snapshot and persistent record ID, then record key, then assertion locator.
`mixed_source_rows` reports rows with both included and filtered assertions, so
the two row totals are not necessarily disjoint. Public tombstones count under
`_tombstone` without invented source rows.

## Exclusions and known gaps

The engine excludes inactive assertions, rejected assertions, ambiguous or
unresolved mappings, generators, and estimators. Generated assertions require
their own verified dependency lineage before they can enter this projection.

All СУМ-11 assertions and historical contrast fields are excluded from this
modern-definition dataset. Historical evidence remains in the internal card
store. The projection does not infer whether an unlabelled source value contains
Soviet distortion. Source attribution and independent linguistic certification
must establish that provenance before release.

The regression fixtures prove permission, citation, hashing, and withdrawal
mechanics. They do not certify Ukrainian content or prove complete source
coverage. This package schema is separate from the existing Atlas shard
publisher's package schema. It is a local artifact, not an upload instruction.

## Withdrawal contract

`withdraw_release` rebuilds from the original cards with the same candidate policy
as `create_release`. A selector contains
`source_id`, `locator`, or both. `locator` matches an exact assertion locator or
an exact `source_record_key`. When both properties are supplied, both must match.
The selector must match an active assertion, and justification must be nonempty.

The replacement uses a different release version. Its notice binds the
deterministically reconstructed previous dataset and replacement dataset by
SHA-256. Keep the original inputs and options to reproduce those exact bytes.
Carry all prior selectors in `withdrawals` or the CLI's `--withdrawals` JSON
array to preserve earlier removals. Each array item has `selector` and
`justification` properties. Removing every included assertion produces a valid
empty replacement dataset with zero output cards and citations.

Rights holders request removal through
[GitHub issues](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues),
naming the source and affected record. Maintainers record a public justification,
build the replacement and withdrawal notice, and retire any distributed old
release through its publication route. Local suppression does not recall copies
already downloaded. Notices must not include private request text.

Run `--help` for release and withdrawal command examples, arguments, and exit
codes. Use the interpreter prescribed by the dispatch contract.

## Atlas0 pairing

`scripts/projects/open_model_data/generate_atlas_pairing.py` writes
`data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json`.
A card is paired only when its spelling assertion matches one active
`atlas0:slug:` registry entry with compatible part of speech, the Atlas article
covers one VESUM entry, and no other release card claims that entry.
For common cards with `card_kind == "lexeme"`, spelling matching uses
`casefold()` and is case-insensitive. For example, `Батьківщина`
(`wc_6hg8x80fcnk2`) pairs to `atlas0:slug:батьківщина`.
For other card kinds, including `proper_name`, capitalization remains significant.
Part of speech separates Atlas homonyms when the card has one part-of-speech
value.

The generator records these disposition reasons:

- `atlas_entry_covers_multiple_homonyms`: `ambiguous` because the Atlas article
  covers multiple VESUM entries, as with `бар`, `баран`, and `замок`.
- `pos_mismatch_with_atlas_entry`: `unpaired` because the card's part of speech
  does not match the Atlas entry, as with the `adv` card for `щось` and its
  Atlas pronoun article, whose registry POS is `noun`. Multiple part-of-speech
  values also produce this reason.
- `phraseologism_mwe_no_atlas_entry`: `unpaired` for phraseologism MWE cards
  with `mwe_form` assertions.
- `homonym_unresolved`: `ambiguous` because multiple Atlas entries remain
  candidates or multiple release cards claim the same Atlas entry.
- `conflicting_spelling_assertions`: `ambiguous` because the card has multiple
  distinct spelling assertions.
- `new_candidate_no_current_atlas_entry`: `unpaired` because the card has no
  spelling assertion or no current Atlas entry matches its spelling.

The generator does not open `sources.db`. `--check` exits 0 when the artifact
matches the inputs and 1 when it drifts.

The scoped mechanics regression command is:

```bash
.venv/bin/python -m pytest -n 2 -q tests/projects/open_model_data/word_cards/test_dataset_projection.py tests/projects/open_model_data/test_word_card_dataset_release.py
```
