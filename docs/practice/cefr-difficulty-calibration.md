# CEFR difficulty calibration — practice selection

Issues: #6143 (parent: #6132; epic: #4387)

## Current difficulty drivers

1. **Published-shard loading**
   `LexiconPractice` loads all published practice levels. The learner level is
   a preference signal, not an eligibility cap: lower and higher CEFR items can
   still be practiced when they are otherwise admitted.

2. **Distractor pools**
   `meaningDistractors()` builds concentric CEFR rings around the answer. A
   missing CEFR value is retained as unknown guidance and is ranked after
   known values; it is never rewritten as A1 or another inferred level.

3. **Cloze quality**
   Cloze items are only offered after the corresponding lemma reaches the
   recognition-mastery threshold (`minRecognitionStability`). An unlevelled
   lemma remains recognition-eligible, but does not enter level-sensitive cloze
   construction until it has the metadata required by that mode.

4. **Synonym / paronym / heritage floors**
   Drill-mode shards are sparser than core lexeme shards. In mixed mode this can
   leave recognition items over-represented; those mode-specific quality and
   curator availability floors remain unchanged.

5. **Soft session preference**
   `selectNextPracticeItem()` uses CEFR distance only as a tiebreak after due,
   lapsed, and anti-monotony priorities. The selected level is preferred, then
   nearby lower levels, then nearby higher levels; unknown CEFR is last among
   otherwise equivalent candidates.

## Fixes

- `rankCandidates()` now applies a **CEFR-distance preference** to every
  candidate, not just new cards. Due and lapsed cards remain primary, so this
  preference cannot hide a genuinely urgent review.

- `meaningDistractors()` builds **concentric CEFR rings** around the answer.
  It exhausts the closest known ring before moving outward, while preserving
  nullable CEFR metadata for unlevelled recognition entries.

- The factory keeps the existing lemma-quality/course-anchor gate. Missing CEFR
  no longer drops an admitted recognition lexeme: its index and lexeme records
  carry `cefr: null`, transported in the A1 shard solely for compatibility.
  It receives recognition modes only; VESUM, cloze, and curated drill gates are
  not lowered.
- Custom imports use the same rule: an Atlas-attested candidate with a real
  gloss can be saved without CEFR. No UI or builder fallback assigns A1.

## Spot-check expectations

- **A1**: A1 items are preferred; other published levels remain eligible.
- **A2**: A2 due reviews are preferred over same-urgency nearby levels; a much
  more overdue card still wins because urgency is the primary sort key.
- **B1**: B1 items are preferred over equally urgent nearby items, while A1/A2,
  B2/C1, and nullable-CEFR recognition items remain available.
