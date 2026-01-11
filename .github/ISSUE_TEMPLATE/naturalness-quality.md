---
name: A1/A2 Content Quality - Fix Robotic Text
about: Systematically improve naturalness of grammar drill activities
title: 'A1/A2 Content Quality: Fix Robotic/Disconnected Activity Text'
labels: content-quality, a1, a2, naturalness
assignees: ''
---

## Problem

Grammar drill activities contain disconnected sentences scoring below 8/10 on naturalness.

**Sample results (manual check):**
- Score 4: Aspect drill - random subject shifts, no connectors
- Score 4: Daily routine - redundant, incoherent
- Score 4: Spatial prepositions - topic jumps (school → coffee)
- Score 6: Perfective/imperfective - subject shift without connector
- Score 8: Restaurant dialogue ✓
- Score 8: Beach mini-narrative ✓

**Failure rate**: 67% (4/6 sampled)

## Constraints

1. **Vocabulary**: Only words from `docs/l2-uk-en/{A1|A2}-CURRICULUM-PLAN.md`
2. **Grammar point**: Must preserve pedagogical intent
3. **CEFR level**: Maintain A1/A2 complexity

## Approach

Fix systematically:
- Unify subjects (no random Я → Вона → Він shifts)
- Add connectors: а, але, тому, потім, спочатку, нарешті
- Remove redundancy
- Keep drill format (don't force narratives)

## Files to Fix

Starting with known bad examples:
- `curriculum/l2-uk-en/a2/activities/12-aspect-introduction.yaml` (score 4)
- `curriculum/l2-uk-en/a2/activities/13-the-completed-past.yaml` (score 6)
- `curriculum/l2-uk-en/a1/activities/25-my-daily-routine.yaml` (score 4)
- `curriculum/l2-uk-en/a2/activities/07-spatial-prepositions.yaml` (score 4)

Then expand to similar activity types.

## Success Criteria

- [ ] All flagged activities re-scored >= 8/10
- [ ] Vocabulary constraints maintained
- [ ] Grammar points preserved
- [ ] Stage-3 docs updated with quality guidelines
