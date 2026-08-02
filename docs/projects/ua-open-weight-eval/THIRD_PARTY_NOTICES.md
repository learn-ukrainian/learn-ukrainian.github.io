# Third-party notices and publication disposition

This notice covers the public payload for UA Open-Weight Evaluation 0.1.0.
It records the project's publication classification; it is not legal advice.
`PUBLICATION_MANIFEST.json` and `SHA256SUMS` bind the notice to the exact
published bytes.

## File-level disposition

| Published file | Disposition |
| --- | --- |
| `cases.jsonl` | Mixed, row-scoped data terms described below |
| `controlled_seeds.jsonl` | Project-authored data under MIT |
| JSON configuration, schema, and receipts | Project-authored metadata under MIT |
| README, data card, contamination policy, and this notice | Project-authored documentation under MIT |
| `LICENSE-MIT.txt` | Verbatim repository MIT license |
| `PUBLICATION_MANIFEST.json` and `SHA256SUMS` | Generated project metadata under MIT |

No model weights, adapters, provider raw output, failed-attempt logs, private
corpus bytes, Google Drive content, non-redistributable literary or textbook
content, VESUM dictionary data, VESUM-derived evidence artifacts, or UA Eval
v0.2 pending-review material is included.

## UA-GEC 2.0 — rows with prefix `uaw-011-`

The 1,000 error rows and 1,000 correct-control rows derive from:

- **Work:** UA-GEC, Ukrainian Grammatical Error Corpus, version 2.0
- **Creators/citation:** Syvokon, Nahorna, Kuchmiichuk, and Osidach,
  *UA-GEC*, UNLP 2023
- **Source:** [grammarly/ua-gec](https://github.com/grammarly/ua-gec)
- **Pinned revision:**
  [`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`](https://github.com/grammarly/ua-gec/tree/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6)
- **License:** [Creative Commons Attribution 4.0 International
  (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Pinned license evidence:**
  [upstream `LICENSE`](https://github.com/grammarly/ua-gec/blob/4757f72f192c4a41e4c8fb1d9690a948f87cf6d6/LICENSE)

Changes made by this project:

- selected the frozen UA Eval 0.1.1 held-out anchor and retained its accepted
  correction references;
- created deterministic context-wrapped error rows;
- created deterministic correct controls from accepted targets;
- added case identifiers, evidence grades, track labels, hashes, expected
  actions, and evaluation-only handling metadata; and
- repeated anchor judgments under controlled wrappers. These transformations
  create 2,000 cases, not 2,000 independent human judgments.

No endorsement by the UA-GEC creators or Grammarly is implied. Reusers must
retain this attribution, link the CC BY 4.0 license, and identify their own
changes.

## Project-authored silver — rows with prefix `uaw-silver-`

The 1,000 protected and 1,000 unresolved rows are deterministic wrappers around
28 project-authored controlled or source-backed test seeds. They are published
under the repository MIT license. Their evidence grades are silver or
unresolved; none is human gold or native-speaker acceptance.

Some seed locators name project tests that used VESUM, SUM, heritage sources,
Russian morphology, or other evidence to exercise routing behavior. The public
payload includes the project-authored test text and locator string only. It
does not copy those dictionaries, source entries, lookup results, or derived
evidence artifacts.

## dict_uk / VESUM v6.8.0 — verification source excluded from payload

The Foundry tests referenced by some silver rows used:

- **Work:** `dict_uk` / VESUM morphological dictionary, release `v6.8.0`
- **Source:** [brown-uk/dict_uk](https://github.com/brown-uk/dict_uk)
- **Pinned revision:**
  [`bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824`](https://github.com/brown-uk/dict_uk/tree/bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824)
- **License:** [Creative Commons Attribution-NonCommercial-ShareAlike 4.0
  International](https://creativecommons.org/licenses/by-nc-sa/4.0/)

No VESUM dictionary byte or VESUM-derived evidence artifact is part of this
publication payload. Consumers who independently use VESUM must comply with
its license.

## Repository software

The extractor, scorer, validators, and offline runner in the tagged source
repository are covered by the repository's [MIT license](../../../LICENSE).
That license does not replace the CC BY 4.0 terms for UA-GEC-derived rows.
