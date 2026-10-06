# W0 selection handback — #9862

W0 is **blocked before selection**, under the issue's stop policy for a required
source key that the foundation cannot express. No cases have been selected or
admitted, and no golden manifest, pool membership or source-admission receipt
has been written. This packet is a compatibility handback, not an admission
request ready for approval. Accountable owner: `claude-open-model-data`, #6321.

The smallest prerequisite is to establish the foundation contracts required by
the already approved golden-set outcome. Do not substitute weaker cases,
mislabel source rows as paradigms, split 220 cases into pilot-sized manifests,
or author an admission receipt to get past the guard.

## Measured evidence

Read-only probes ran from the assigned dispatch worktree on 2026-10-06, against
base `141f3f269ed6e4b18a1deb2f50d3b292aaea25e8`. Every database was opened with
SQLite URI `mode=ro`. Source content was not rewritten. The reproducible probe
and one disposable membership diagnostic are host-only; the driver receives
their locations in the dispatch handback.

| Query scope | Raw result | Evidential limit |
| --- | ---: | --- |
| Checked, status-ok ULIF entry rows | 262735 | Rows, not golden cases |
| Distinct queries among those rows | 250680 | Spellings, not lexical identities |
| Queries having multiple such rows | 10560 | Broad homograph candidates, not the Atlas-only category denominator |
| ULIF phraseology section rows | 8133 | Sections, not distinct expressions |
| Identical nonblank phraseology text under multiple distinct checked ULIF queries | 1994 | Structural candidate groups; no idiom identity adjudication |
| Wiktionary rows | 50278 | Supplemental key-contract probe; **not** tier-3 evidence |

Reproduction SQL for the relevant multi-headword candidates:

```sql
SELECT min(s.id), count(*), count(DISTINCT e.normalized_query)
FROM ulif_dictua_sections s
JOIN ulif_dictua_entries e ON e.id = s.entry_id
WHERE s.kind = 'phraseology'
  AND e.homonym_checked = 1 AND e.status = 'ok'
  AND trim(json_extract(s.payload_json, '$.text')) != ''
GROUP BY json_extract(s.payload_json, '$.text')
HAVING count(DISTINCT e.normalized_query) > 1;
```

Raw aggregate result: `1994` groups. The first group ordered by minimum section
ID is `(7963, 3, 3)`: three sections under three distinct checked queries.
These are candidate groups, not verified Ukrainian judgments or selected cases.

## Stop evidence and prerequisites

1. **Required MWE source key.** A literal row at
   `ulif:ulif_dictua_sections:id:7963` has `kind = phraseology` and belongs to
   the multi-headword candidate group above. Calling
   `word_card_foundation.intrinsic(record, [])` on that row refuses with
   `Invalid object fields`. Its payload has `citations`, `raw_html`,
   `raw_response_ref`, `register_labels`, `sense_or_group_id`, `source_order`,
   `terms`, and `text`. The current section contract accepts only paradigm
   matrices (`rows`) and requires `kind == paradigm`. Source-record aliases
   therefore cannot represent the required phraseology evidence. A separate
   Wiktionary literal-row probe refuses with `Missing approved source-key
   contract`; it supplies no category or tier judgment.
2. **Golden case denominator.** `selection_check` on 220 distinct, literal,
   checked ULIF entry rows with unique anchors and matching separate counts
   refuses with `Pilot denominator drift; require exactly 150 admitted units`.
   The same structural probe limited to 150 passes with
   `{'units': 150, 'source_records': 150, 'atlas_articles': 0}`. Neither probe is
   a golden selection. Golden cases also expand to multiple source partitions;
   a case count must not be conflated with the pilot's source-unit count.
3. **Joint isolation proof.** A disposable keys-only membership diagnostic
   holding a source locator absent from the pilot/identity inputs refuses
   `isolation([pilot, registry], membership, ('registry',))` with
   `Unresolved membership keys; isolation cannot be checked`. The same inputs
   without membership return `unverified`. AC3 needs all golden membership keys
   known to the verification inputs while retaining pilot closure evidence;
   an unknown key must never be treated as checked or silently discarded.

The first prerequisite triggers the explicit stop policy. No new source-key,
selection-schema or verification-input contract has been invented in this
packet. The driver owns approval and routing of those prerequisites, followed
by a resumed selection packet. The existing independent Google-family source
admission procedure remains a separate non-author step.

## Category accounting

All selected counts are zero because selection stopped before any membership
was authored. A dash means the category's eligible maximum was **not measured**
after the stop, not that held sources contain zero candidates.

| Category | Selected / target | Measured candidate scope |
| --- | ---: | --- |
| Homographs | 0 / 40 | 10560 broad ULIF query groups; Atlas-only eligibility unmeasured |
| Stress doublets | 0 / 20 | — |
| Proper/common pairs | 0 / 20 | — |
| Aspect pairs | 0 / 20 | — |
| Aspect homographs | 0 / 5 | — |
| MWEs under several headwords | 0 / 20 | 1994 identical-text structural groups; key contract blocked |
| Multi-sense cases | 0 / 20 | — |
| Stress disagreements | 0 / 20 | — |
| Tier-3-only cases | 0 / 10 | — |
| ULIF header damage | 0 / 10 | — |
| Russification pairs | 0 / 15 | — |
| Ordinary controls | 0 / 20 | — |
| **Total** | **0 / 220** | **No padded or substitute cases** |

No Ukrainian judgment was authored; no Ukrainian content was added to fields.
Sources MCP category verification remains pending for a resumed selection.
The deterministic seed and stratified 132/88 replay/held-out split remain
pending; the pilot denominator remains its admitted 150 units. No expected
answers have been created.

## Acceptance and next owner

AC1–AC4 remain open (4). The author has not claimed a frozen membership SHA,
pilot/held-out disjointness, `heldout_isolation: checked`, or evaluation
readiness. The three prerequisites above belong to `claude-open-model-data`.
After their disposition: measure every category, verify Ukrainian judgments
with sources MCP, select each case once, stratify and test conservative alias
closure against the pilot, then route exact candidate bytes for non-author
source admission. Only after a valid receipt may freeze/allocate/verify run.
No PR was requested; this worker returns a pushed branch to the driver.

## Validation of the unchanged foundation

Commands used the task-prescribed shared project interpreter from the assigned
worktree. No production code or tests changed.

- `-m scripts.atlas.word_card_foundation verify --manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json`:
  exit 0; 150 units, 272 source records, 114 legacy articles, 140 legacy aliases;
  `heldout_isolation: unverified`, `evaluation_readiness: unknown`, 22 unresolved
  card mappings. This is existing foundation consistency, not golden-set proof.
- `-m pytest -q tests/test_word_card_foundation.py`: 437 tests passed, but process
  exit 1 because the author created the packet files during the run and the
  checkout guard detected them. This was an author sequencing failure.
- After staging both files and making no edits during the run,
  `-m pytest -q -n 2 tests/test_word_card_foundation.py`: exit 0;
  `437 passed in 269.28s (0:04:29)`; checkout/process guards passed. This includes
  the existing held-out adjudication and conservative alias-closure refusals;
  it supplies no independent held-out evaluation of new cases.
- `-m ruff check scripts/atlas/word_card_foundation.py tests/test_word_card_foundation.py`:
  exit 0, `All checks passed!`.

Independent case-category review, non-author source admission, exact-head
cross-family branch review, PR CI and merged/shipped proof remain absent.
