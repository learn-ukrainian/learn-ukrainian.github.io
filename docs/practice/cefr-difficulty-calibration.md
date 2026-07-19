# CEFR difficulty calibration — practice selection

Issue: #5504 (related: #4700, #4387)

## Current difficulty drivers

1. **Shard filters / level cascade**
   `LexiconPractice` loads every level up to the learner’s selected level via
   `levelsUpTo()` and merges lower-level shards into the active deck for density
   and SRS review coverage. This means a B1 session contains A1 and A2 items,
   which can make the session feel too easy if they are not weighted.

2. **Distractor pools**
   `meaningDistractors()` already preferred same-CEFR distractors, but when a
   level had too few eligible candidates it fell back to *any* other level.
   A B1 answer could therefore be undermined by A1 distractors, or an A1 answer
   could be ambushed by much harder vocabulary.

3. **Cloze gaps**
   Cloze items are only offered after the corresponding lemma reaches the
   recognition-mastery threshold (`minRecognitionStability`). Until higher-level
   recognition cards mature, lower-level cloze items dominate mixed sessions.

4. **Synonym / paronym / heritage floors**
   Drill-mode shards are sparser than core lexeme shards. In mixed mode this can
   leave basic recognition items from lower levels over-represented.

5. **Level bias only for new cards**
   `selectNextPracticeItem()` previously applied a level preference only to
   brand-new cards. Due and lapsed reviews from lower levels intermixed freely
   with selected-level reviews.

## Fixes

- `rankCandidates()` now applies a **CEFR-distance penalty** to every candidate,
  not just new cards. Within the same urgency bucket, items at the selected
  learner level are preferred over lower-level items, while still preserving the
  higher priority of due/lapsed cards and mode variety.

- `meaningDistractors()` builds **concentric CEFR rings** around the answer.
  It exhausts the closest ring before moving outward, keeping multiple-choice
  options semantically comparable and preventing huge level leaps.

- Existing mode eligibility is unchanged (index `modes` + recognition mastery
  for cloze). Better item selection reduces the perceived dilution instead of
  lowering quality bars by hiding valid reviews or easier modes.

## Spot-check expectations

- **A1**: only A1 items exist in the deck, so level bias is a no-op.
- **A2**: A2 due reviews are preferred over same-urgency A1 reviews; a much
  more overdue A1 card still wins because urgency is the primary sort key.
- **B1**: B1 new cards and due reviews are preferred over A2/A1 ties; lower-
  level cards still appear when they are genuinely due.
