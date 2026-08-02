# Cloze residual taxonomy

Run date: 2026-08-02

Scope: hydrated release `atlas-practice-v1-4369ff38d9b16567`, the A1-C1
`practice-lexemes.*.json` shards, the base sentence inventory, and its additive
`lexicon-sentence-inventory.residual.json` sidecar. This is a current-state
taxonomy, not a completion claim for #6188.

## Current coverage

The release has 4,264 cloze-eligible practice lemmas out of 6,000. The
uncovered set is therefore 1,736 lemmas.

| Level | Practice lemmas | Cloze-eligible | Residual | Coverage |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1,470 | 1,005 | 465 | 68.37% |
| A2 | 1,444 | 1,097 | 347 | 75.97% |
| B1 | 1,617 | 1,279 | 338 | 79.10% |
| B2 | 940 | 700 | 240 | 74.47% |
| C1 | 529 | 183 | 346 | 34.59% |
| **All** | **6,000** | **4,264** | **1,736** | **71.07%** |

The inventory contains 5,135 base rows and 51 sidecar rows. They are 5,186
unique inventory IDs; 5,185 intersect the current Practice set. Within the
1,736 residual lemmas, 923 have an inventory row and 813 have no inventory row.
The inventory reader accepts 618 of those 923 residual rows as blankable
candidates and rejects 305 before the builder stage.

## Mutually exclusive partition

The buckets below use this precedence: `function-POS`, then `multiword-id`,
then `no public sentence`, then the remaining inventory-reader candidates.
This prevents overlaps from inflating the total. `multiword-id` means a
multi-token or slash-form `lemmaPlain` shape; apostrophe-bearing single words
are not counted as multiword. `no public sentence` includes both
the 813 no-inventory residuals and the 305 inventory rows that the public
inventory reader cannot turn into one blankable sentence. It means “no current
public blankable sentence,” not “this lemma can never be sourced.”

| Bucket | Count | Definition in this snapshot |
| --- | ---: | --- |
| function-POS | 121 | Residual lexeme `pos` is in the builder’s function-POS set. |
| multiword-id | 170 | Multi-token/slash-form residual after the function-POS precedence rule. |
| no public sentence | 936 | No inventory row, or a row rejected by the public inventory reader, after the two precedence rules. |
| inventory-present-build-empty | 509 | Inventory reader candidate remains, but no current published cloze is present after function/multiword exclusion. This is a combined residual funnel bucket, not a claim that every row has one identical root cause. |
| would_emit-still-trimmed | 0 | No current published cloze shard reports an over-budget payload; all five `sizeBudget.ok` values are true. This does not claim that a future no-budget rebuild would add no cards. |
| other | 0 | No unclassified residual remains after the stated partition. |
| **Total** | **1,736** | **Exact residual set.** |

The function-POS and multiword classifications overlap in three raw IDs; the
precedence rule assigns those three to `function-POS`. The multiword bucket has
173 raw shape matches before that rule and 170 primary assignments. The
inventory-present bucket is intentionally conservative: it does not turn the
historical 299 quality-gate-empty and 311 identity-option failures recorded in
the earlier builder trace into a new “done” bar.

## Budget check

The hydrated cloze shard metadata is below the current per-level limits of
2,250,000 raw bytes and 240,000 gzip bytes:

| Level | Raw bytes | Gzip bytes | `sizeBudget.ok` |
| --- | ---: | ---: | --- |
| A1 | 1,746,501 | 190,859 | true |
| A2 | 1,880,605 | 201,728 | true |
| B1 | 2,203,585 | 237,023 | true |
| B2 | 1,217,519 | 131,160 | true |
| C1 | 320,810 | 35,093 | true |

The current maximum is B1, with 46,415 raw bytes and 2,977 gzip bytes of
metadata-reported headroom. Thus there is no tool evidence for a currently
still-trimmed bucket. A future deck rebuild must remeasure the untrimmed and
post-budget sets rather than treating this zero as permanent.

## Residual-only textbook FTS probe

The residual-only probe used the complete hydrated Practice target set, removed
both the base inventory and its `.residual.json` sibling, and searched up to
250 ranked textbook chunks per target. The two database arguments below refer
to the machine-local read-only canonical source/VESUM data; their absolute link
targets are deliberately not recorded in this public evidence.

```bash
.venv/bin/python -m scripts.audit.generate_sentence_inventory \
  --practice-lexemes-dir site/public/lexicon \
  --residual-from site/src/data/lexicon-sentence-inventory.json \
  --sources-db data/sources.db \
  --vesum-db data/vesum.db \
  --max-per-lemma 1 \
  --textbook-search-limit 250 \
  --out batch_state/6188-textbook-residual.json
```

The executed probe reported:

```text
sentence inventory residual targets: 815 of 6000
sentence inventory: 0 rows
```

The 815 targets include two lemmas already covered by a non-inventory cloze
source; the current uncovered no-inventory residual is 813. A separate
shape-only probe with VESUM disabled found 64 candidate rows, but the
quality-gated VESUM run found zero. Those 64 unverified rows are not a
mineable tranche. No new rows were added to the residual sidecar and no deck
publish was run.

## Named impossibles and next work

- **No public blankable sentence (936 primary assignments):** the current
  inventory either has no row or rejects the available row before cloze
  construction. The next useful source work is a new public, rights-aware
  corpus or a dedicated, reviewed textbook end-dictionary extractor; FTS alone
  did not yield a quality-gated tranche here.
- **Function-POS (121):** automatic identity clozes remain gated by the current
  function-POS policy. Any exception needs an explicitly reviewed exercise
  contract, not a blanket gate removal.
- **Multiword IDs (170):** these need a multiword-aware cloze/source contract.
  Treating a phrase or paired-form ID as one single-token identity answer would
  violate the existing blankability and option-quality gates.
- **Inventory-present-build-empty (509):** these are the next code/data funnel
  to instrument per lemma. The current evidence does not authorize lowering
  VESUM, source, capitalization, or option gates.
- **Still-trimmed (0):** no current budget pressure is demonstrated. Do not
  raise limits or claim recovered coverage without a fresh untrimmed/post-budget
  comparison.

The next mineable tranche remains **not established**. The residual sidecar
pattern from #6230 and the quality gates from #6212 remain unchanged.

## Commands and evidence used

Hydrate the pinned release:

```bash
.venv/bin/python -m scripts.practice_deck.io
# Hydrated Atlas practice deck atlas-practice-v1-4369ff38d9b16567 (45 shards).
```

Read the published coverage counts:

```bash
jq -r '.files[] | select(.kind == "index") |
  [.level, .counts.lexemes, .counts.clozeEligibleLexemes,
   .counts.clozeCoverage] | @tsv' \
  site/src/data/lexicon-practice-deck.pointer.json
```

The residual-set and inventory-reader measurement used the builder’s
`_FUNCTION_POS`, `read_sentence_inventory`, all hydrated lexeme shards, all
five hydrated cloze shards, and both inventory files. It produced:

```text
residual 1736 raw_inventory 923 reader 618 no_reader 305 no_inventory 813
function 121 function_raw 118 function_reader 109 function_no_inventory 3 function_no_reader 9
multiword_shape 173 multiword_raw 0 multiword_reader 0 multiword_no_inventory 173 overlap_function 3
partition {'no public sentence': 936, 'inventory-present-build-empty': 509,
           'multiword-id': 170, 'function-POS': 121,
           'would_emit-still-trimmed': 0, 'other': 0}
partition_sum 1736
```

The budget check read each hydrated `practice-cloze.<level>.json` payload’s
`sizeBudget` object and confirmed `ok=true` for A1 through C1.
