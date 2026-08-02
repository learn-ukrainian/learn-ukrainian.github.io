# Cloze residual taxonomy

Run date: 2026-08-02

Scope: hydrated release `atlas-practice-v1-72aefaf645e8d390`, the A1-C1
`practice-lexemes.*.json` shards, the base sentence inventory, and its additive
`lexicon-sentence-inventory.residual.json` sidecar. The before comparison is
the v12 build from release `atlas-practice-v1-4369ff38d9b16567`; this is a
current-state taxonomy, not a completion claim for #6188.

## Current coverage

The published v13 release has 4,440 cloze-eligible practice lemmas out of
6,000. The uncovered set is therefore 1,560 lemmas.

| Level | Practice lemmas | Cloze-eligible | Residual | Coverage |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1,470 | 1,080 | 390 | 73.47% |
| A2 | 1,444 | 1,154 | 290 | 79.92% |
| B1 | 1,617 | 1,296 | 321 | 80.15% |
| B2 | 940 | 723 | 217 | 76.91% |
| C1 | 529 | 187 | 342 | 35.35% |
| **All** | **6,000** | **4,440** | **1,560** | **74.00%** |

The inventory contains 5,135 base rows and 51 sidecar rows. They are 5,186
unique inventory IDs; 5,185 intersect the current Practice set. Within the
1,560 final residual lemmas, 442 have an inventory-reader candidate and 1,118
have no candidate. The 442 includes function/multiword IDs that are assigned
to those higher-precedence buckets below.

## #6188 before/after measurement

The v12 builder measured the original 509 inventory-present residual IDs as
follows. The categories are mutually exclusive: a quality-gate rejection is
classified before VESUM, and an option failure is classified only after a raw
cloze item exists.

| Builder snapshot | Quality gate empty | Identity-option fail | VESUM miss | Level mismatch | Other | Safe raw candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v12, before fix | 4 | 300 | 205 | 0 | 0 | 0 |
| v13, same 509 IDs, before budget | 4 | 75 | 205 | 0 | 0 | 225 |

The v13 change only renders normalized dictionary decoys at the source
surface's initial-capital state before applying the existing length, POS,
CEFR, answer-leak, and option validators. It does not lower any quality gate.
All 225 recovered option sets validated before budgeting. The published deck
retains 222 of those original-509 cards; three are in the B1 budget-trimmed
residual.

The published coverage change is 4,264 to 4,440 eligible lemmas (+176) and
1,736 to 1,560 residual lemmas (-176). B1 is the only level that needed
budget trimming: the no-budget v13 B1 cloze payload measured 2,336,106 raw /
250,806 gzip bytes, while the published payload is within the 2,250,000 /
240,000 limits. The 60 final `would_emit-still-trimmed` IDs comprise the three
original-509 cards plus 57 previously published B1 IDs displaced by the
larger v13 payload.

## Mutually exclusive partition

The buckets below use this precedence: `function-POS`, then `multiword-id`,
then `no public sentence`, then the remaining inventory-reader candidates.
Within that final candidate set, the published builder-funnel result is split
into `inventory-present-build-empty` and `would_emit-still-trimmed`. This
prevents overlaps from inflating the total. `multiword-id` means a multi-token
or slash-form `lemmaPlain` shape; apostrophe-bearing single words are not
counted as multiword. `no public sentence` includes the 1,118 no-candidate
residuals and inventory rows rejected before the remaining builder funnel. It
means “no current public blankable sentence,” not “this lemma can never be
sourced.”

| Bucket | Count | Definition in this snapshot |
| --- | ---: | --- |
| function-POS | 110 | Residual lexeme `pos` is in the builder’s function-POS set. |
| multiword-id | 170 | Multi-token/slash-form residual after the function-POS precedence rule. |
| no public sentence | 936 | No current candidate remains after the function/multiword precedence rules. |
| inventory-present-build-empty | 284 | Remaining inventory candidates rejected by the v13 quality, VESUM, level, or option gates: 4 quality-gate empty, 75 identity-option fail, 205 VESUM miss, 0 level mismatch, and 0 other. |
| would_emit-still-trimmed | 60 | A no-budget v13 trace produced a valid cloze/options set, but the default budget omitted the ID from the published index. All five published `sizeBudget.ok` values remain true. |
| other | 0 | No unclassified residual remains after the stated partition. |
| **Total** | **1,560** | **Exact residual set.** |

The function-POS and multiword classifications overlap in three raw IDs; the
precedence rule assigns those three to `function-POS`. The multiword bucket has
173 raw shape matches before that rule and 170 primary assignments. The final
inventory-present candidate set is 344 IDs: 4 quality-gate empty, 75
identity-option failures, 205 VESUM misses, and 60 valid-but-budget-trimmed
IDs. The 284/60 split above keeps the budget residual separate from genuine
builder-empty failures.

## Budget check

The published hydrated cloze shard metadata is below the current per-level
limits of 2,250,000 raw bytes and 240,000 gzip bytes:

| Level | Raw bytes | Gzip bytes | `sizeBudget.ok` |
| --- | ---: | ---: | --- |
| A1 | 1,871,315 | 204,492 | true |
| A2 | 1,979,290 | 211,996 | true |
| B1 | 2,218,308 | 237,387 | true |
| B2 | 1,257,264 | 135,573 | true |
| C1 | 327,274 | 35,679 | true |

The current maximum is B1, with 31,692 raw bytes and 2,613 gzip bytes of
metadata-reported headroom. The post-budget payloads fit, but the no-budget
trace above proves that 60 cards remain capacity-trimmed; a future deck build
must remeasure both the untrimmed and post-budget sets.

## Residual-only textbook FTS probe (baseline evidence)

The pre-v13 residual-only probe used the complete v12 hydrated Practice target
set, removed both the base inventory and its `.residual.json` sibling, and
searched up to 250 ranked textbook chunks per target. The two database
arguments below refer to the machine-local read-only canonical source/VESUM
data; their absolute link targets are deliberately not recorded in this public
evidence.

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

The 815 targets included two lemmas already covered by a non-inventory cloze
source; the v12 uncovered no-inventory residual was 813. A separate shape-only
probe with VESUM disabled found 64 candidate rows, but the quality-gated VESUM
run found zero. Those 64 unverified rows are not a mineable tranche. This
evidence predates the v13 builder-only change; no new rows were added to the
residual sidecar.

## Named impossibles and next work

- **No public blankable sentence (936 primary assignments):** no current
  inventory candidate remains after the function/multiword precedence rules.
  The next useful source work is a new public, rights-aware corpus or a
  dedicated, reviewed textbook end-dictionary extractor; the baseline FTS
  probe did not yield a quality-gated tranche here.
- **Function-POS (110):** automatic identity clozes remain gated by the current
  function-POS policy. Any exception needs an explicitly reviewed exercise
  contract, not a blanket gate removal.
- **Multiword IDs (170):** these need a multiword-aware cloze/source contract.
  Treating a phrase or paired-form ID as one single-token identity answer would
  violate the existing blankability and option-quality gates.
- **Inventory-present-build-empty (284):** the remaining failures are 4
  quality-gate empty, 75 identity-option fail, and 205 VESUM miss. The current
  evidence does not authorize lowering VESUM, source, capitalization, or option
  gates.
- **Still-trimmed (60):** these are valid no-budget candidates omitted by the
  current B1 size budget. Do not raise limits or claim their coverage without a
  fresh quality review and untrimmed/post-budget comparison.

The next mineable tranche remains **not established**. The residual sidecar
pattern from #6230 and the quality gates from #6212 remain unchanged.

## Commands and evidence used

Hydrate the pinned release:

```bash
.venv/bin/python -m scripts.practice_deck.io
# Hydrated Atlas practice deck atlas-practice-v1-72aefaf645e8d390 (45 shards).
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
residual 1560 inventory_reader_candidates 442 no_candidate 1118
function 110 function_candidate 98 function_no_candidate 12
multiword_shape 173 multiword_raw 0 multiword_reader 0 multiword_no_inventory 173 overlap_function 3
partition {'no public sentence': 936, 'inventory-present-build-empty': 284,
           'multiword-id': 170, 'function-POS': 110,
           'would_emit-still-trimmed': 60, 'other': 0}
partition_sum 1560
```

The budget check read each hydrated `practice-cloze.<level>.json` payload’s
`sizeBudget` object and confirmed `ok=true` for A1 through C1. The separate
no-budget build trace produced 60 valid option sets absent from the final
published index, which is why `would_emit-still-trimmed` is nonzero even though
the published payload metadata is truthful.
