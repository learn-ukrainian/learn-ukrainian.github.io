# Legacy practice meaning withdrawal (#9160)

The approved fallback withdraws all legacy meanings. No source and sense
admission mechanism from the earlier containment rounds has accepted independent
evidence. This includes A1 English. The loss of A1 scaffolding is an explicit
containment cost, not a change to the curriculum's immersion policy.

Flashcards, matching, choice, antonym and homonym modes are unavailable. The last
two previously fell through to meaning-choice rendering. The shared mode boundary
also excludes them from Mixed, direct entry, saved-session history and unresolved
review queues. Practice daily previews, saved daily sets, custom-deck fallbacks,
Words of the Day and miss summaries cannot display the legacy glosses. Daily
cards show a localized unavailability notice and retain their independent examples.

The generator preserves its existing lexeme membership decision, then emits empty
`gloss` and `glossClean` fields with `meaningMcEligible: false`. Its historical
article cleaner remains only for that membership decision. Its output is never
admitted as a learner meaning. Publication and static-asset validation refuse
nonempty meaning fields or advertisements for a withdrawn mode.

## Frozen input and local reproduction

The source is the published 55-shard package `atlas-practice-v1-f1e1cf95470ce319`.
Its gzip SHA-256 is
`d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19`.
The decoded package SHA-256 is
`844328730fcd714ac51c8aa2fac696ab97dc7b92ea3d1f8f7ed6486a8f164d11`.
The local transform produces `atlas-practice-v1-5a2556011031edd2`.

`withdraw_meanings_from_pinned_package` replaces the historical synonym-only
transform. It checks the pinned source identity and every decoded file hash,
blanks both meaning fields, disables meaning multiple choice, and removes the
five modes and their counters. It preserves every lexeme and independent drill.
Only deck-version metadata and size budgets also change.

Given the downloaded source gzip and its source pointer, run this from a dispatch
worktree. The helper writes local shards and uploads nothing.

```python
import json
from pathlib import Path
from scripts.practice_deck.publish import withdraw_meanings_from_pinned_package

scratch = Path('batch_state/meaning-withdrawal-9160')
version = withdraw_meanings_from_pinned_package(
    scratch / 'source.json.gz',
    json.loads((scratch / 'source-pointer.json').read_text()),
    scratch / 'shards',
)
assert version == 'atlas-practice-v1-5a2556011031edd2'
```

## Accounting

The reason for every withheld meaning is missing accepted source and sense
admission. There are zero retained meanings and zero admitted mechanisms, so
there is no retained population for a 150-row sample. Verification instead
checks every row and compares every shard against the frozen input outside the
permitted changes.

| Level | Lexemes preserved | Meanings withheld | Stress membership preserved | Cloze membership preserved | Paradigm membership preserved |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 1,496 | 1,496 | 1,244 | 1,041 | 760 |
| A2 | 1,511 | 1,511 | 1,362 | 1,100 | 778 |
| B1 | 1,505 | 1,505 | 902 | 585 | 874 |
| B2 | 1,040 | 1,040 | 975 | 686 | 567 |
| C1 | 665 | 665 | 592 | 174 | 416 |
| Total | 6,217 | 6,217 | 5,075 | 3,586 | 3,395 |

These are index memberships, not independent certification of the preserved
drills. Classify, paronym and heritage memberships also remain unchanged. A full
regeneration has a fresh denominator and needs its own evidence.

## Delivery and residuals

This local transform is not a published release. The standard publisher still
requires its linguistic checks and a version matching the current generator
inputs. It does not accept a withdrawal fingerprint as a fresh regeneration.
The frozen artifact also retains pre-existing content defects outside its
meaning fields. It cannot substitute for integrated regeneration under #10672.

#9160 stays open until the required independent reviews, publication authorization,
release replacement and live checks are complete. Coverage restoration belongs to
#8977. Re-enabling meanings requires source-bound evidence, independent semantic
evaluation and normal delivery gates. The test-only meaning-mode opt-in exists
for isolated scheduling and formatter tests. Containment tests use the disabled
default.
