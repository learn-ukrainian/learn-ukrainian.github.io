# Textbook leftover residual census (#6371)

Census id: `atlas-6371-textbook-leftover-residual.v1`

Source of truth is the committed oneshot textbook inventory plus the
in-repo Bolshakova/Vashulenko leftover lists and their already-approved
ledgers. This report does not invent lemmas, dump corpus, or commit PDFs.

## Artifacts

| artifact | present | path |
| --- | --- | --- |
| `oneshot_inventory` | yes | `data/lexicon/source-inventory/oneshot/textbook-jsonl-curated-2026-07-19-bulk.yaml` |
| `oneshot_decisions` | yes | `data/lexicon/source-inventory-review-decisions/2026-07-19-textbook-jsonl-curated-bulk-approve.yaml` |
| `named_inventory_0` | yes | `data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml` |
| `named_inventory_1` | yes | `data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml` |
| `named_inventory_2` | yes | `data/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml` |
| `named_decisions_0` | yes | `data/lexicon/source-inventory-review-decisions/2026-06-30-third-approved-textbook-ledger-batch.yaml` |
| `named_decisions_1` | yes | `data/lexicon/source-inventory-review-decisions/2026-07-03-fourth-approved-textbook-ledger-batch.yaml` |
| `named_decisions_2` | yes | `data/lexicon/source-inventory-review-decisions/2026-07-03-fifth-approved-textbook-ledger-batch.yaml` |
| `vesum_db` | **NO** | `data/vesum.db` |
| `sources_db` | **NO** | `data/sources.db` |
| `pointer` | yes | `site/src/data/lexicon-manifest.pointer.json` |

## Blockers

- `data/vesum.db`
- `data/sources.db`

## Atlas catalog

- loaded: `True`
- source: `https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest-d22972ff9d43.json.gz`
- unique keys: `20112`
- entry lemmas: `20112`
- json_sha256: `d22972ff9d4313943a55c19fd4ec6da73702538a7c4d14edb2529f828a7a640c`

## Oneshot bulk (`textbook-jsonl-curated-2026-07-19`)

- inventory rows: `24682`
- approved decisions: `24682`
- approved unique lemmas: `24682`
- approved English-gloss rows (teacher P1 bar): `0`
- already in Atlas: `16932`
- missing from Atlas: `7750`

Oneshot approved glosses are SUM-11 Ukrainian dumps. They are **not**
teacher-P1 eligible and must not be admitted from this census.

Sample of oneshot leftovers still missing (first 10, lemma-only):

- `абревіація`
- `абрикосовий`
- `абсентеїзм`
- `абсолютизм`
- `абстрагування`
- `абстрагуватися`
- `абстракціонізм`
- `абстракція`
- `абсурдність`
- `авангардизм`

## Named leftover inventories (Bolshakova + Vashulenko)

- inventory rows: `114`
- approved decisions: `91`
- approved unique lemmas: `89`
- approved English-gloss rows (teacher P1 bar): `91`
- already in Atlas: `89`
- missing from Atlas: `0`

### Named teacher-P1 leftovers still missing

- none — every unique named leftover with an English learner gloss is already in Atlas

## Admission

Admit only leftovers already approved the same way as teacher P1: approve_for_publish + learner-English gloss, lemma taken verbatim from a committed inventory. Refuse invented lemmas, oneshot SUM-11 dumps, and any write when vesum.db or sources.db is missing.

- refused: `True`
- reason: BLOCKED: missing data/vesum.db, data/sources.db; no named teacher-P1 leftovers are missing from the Atlas catalog
- admitted this run: `[]`

Issue #6371 stays open. Practice/deck publish and pointer flip are
out of scope until the blockers above are cleared on a host that
has `data/vesum.db` and `data/sources.db`.

