# Audit Report: poisoned_module.md
**Phase:** A1 | **Level:** A1 | **Pedagogy:** PPP | **Target:** 750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[LINGUISTIC_PURITY]** Found Russian-only characters in module: ё, Ы, э
  - FIX: Remove Russian characters (ё, ъ, ы, э) or ensure they are properly contextually framed.
- **[COMPLEXITY]** quiz 'Test Quiz' has 1 items (minimum: 8)
  - FIX: Add more items. A1 quiz requires at least 8 items.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Test Quiz' Q1 prompt length 1 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[HEADING_LEVEL]** Main section 'Activities' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Activities' to '# Activities' for top-level TOC compliance
- **[HEADING_LEVEL]** Main section 'Vocabulary' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Vocabulary' to '# Vocabulary' for top-level TOC compliance
- **[HEADING_LEVEL]** Main section 'Summary' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Summary' to '# Summary' for top-level TOC compliance
- **[VOCAB_FORMAT]** A1/A2 vocabulary requires 6 columns, found 2: | Word | Translation |
  - FIX: Format: | Word | IPA | English | POS | Gender | Note |
- **[LINGUISTIC_PURITY]** Found Russian-only characters in module: ё, Ы, э
  - FIX: Remove Russian characters (ё, ъ, ы, э) or ensure they are properly contextually framed.
- **[MISSING_RESOURCES]** Module is missing [!resources] callout with external learning resources
  - FIX: Add a [!resources] section with links to Ukrainian Lessons, YouTube videos, or other quality Ukrainian learning resources.

## Recommendation
**🔄 REWRITE** (severity 100/100)

- 9 pedagogical violations (significant)
- Immersion 29% off target (major rebalancing needed)
- Activity count below minimum
- Activity density below minimum
- Vocabulary count below minimum

## Gates
- **Words:** ❌ 37/750
- **Activities:** ❌ 1/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ❌ 1/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ❌ 0 < 1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 9 violations
- **Immersion:** ❌ 6.2% LOW (target 35-55% (M999))

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| quiz: Test Quiz | quiz | 1 | 8 | Add 7 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Bad Actor Test** | ⚪️ | 37 | Skipped |
| **Activities** | ➖ | 0 | Excluded Type |
| **quiz: Test Quiz** | 🎮 | 1 | Activity (1 items, min 8) |
| **Vocabulary** | ➖ | 0 | Excluded Type |
| **Summary** | ✅ | 5 | Included in Core |