All the original violations are fixed:
- **true-false activity**: Added with correct `correct` field (not `answer`)
- **match-up pairs**: Expanded from 8 to 12 pairs
- **unjumble items 1-3**: Expanded from 4 words to 6 words each
- **Pedagogy gate**: Now passes (was 4 violations, now 0)

The remaining failure is a **review citation validation** issue — the existing review file has stale citations that don't match the module content. This is a separate issue from the escalation's scope (it's about the review file, not the activities or content), and requires a full review regeneration via `/review-content-v4`.

All 4 original pedagogy violations and the missing `true-false` activity type are resolved.