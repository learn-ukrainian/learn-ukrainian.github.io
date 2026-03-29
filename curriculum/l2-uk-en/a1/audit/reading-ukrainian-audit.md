# Audit Report: M02 — reading-ukrainian.md
**Level:** A1 | **Module:** M02 | **Phase:** A1.1 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-03-29 01:13:25

## Configuration
**Type:** A1
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥1 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Чита́ння слів (Reading Words) | 85 | 2 | ✅ |

**Summary:**
- Total activities: 1 (target: 0-4) ✅
- Unique types: 1 (minimum: 0) ✅
- Priority types used: 0/8 (none) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[GRAMMAR]** Participle used before B1: 'відкритий'
  - FIX: Participles not allowed until B1. Use relative clauses or simple sentences.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (86% overlap): "*(Who is this?)*</div>
> <div class="dialogue-line"><span class="speaker">Марко:</span> Це кіт.". Shares significant keywords with sentence at index 3.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (88% overlap): "*(This is a cat.)*</div>
> <div class="dialogue-line"><span class="speaker">Анна:</span> Де кит?". Shares significant keywords with sentence at index 2.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in reading-ukrainian.yaml: Schema validation error at key '0': {'id': 'fill-in', 'type': 'fill-in', 'instruction': 'Divide the words into syllables using hyphens based on the Open Syllable Principle (e.g., мо-ло-ко, а-пте-ка).', 'items': [{'sentence': 'університет -> _____', 'answer': 'у-ні-вер-си-тет'}, {'sentence': 'бібліотека -> _____', 'answer': 'бі-блі-о-те-ка'}, {'sentence': 'фотографія -> _____', 'answer': 'фо-то-гра-фі-я'}, {'sentence': 'аптека -> _____', 'answer': 'а-пте-ка'}, {'sentence': 'молоко -> _____', 'answer': 'мо-ло-ко'}, {'sentence': 'шоколад -> _____', 'answer': 'шо-ко-лад'}, {'sentence': 'вулиця -> _____', 'answer': 'ву-ли-ця'}, {'sentence': 'людина -> _____', 'answer': 'лю-ди-на'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ✅ 2068/1200 (raw: 2626)
- **Activities:** ✅ 1/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 1/0 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 1/1
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 56/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 13.1% (target 5-15% (M02))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Склади (Syllables)** | ✅ | 330 | Included in Core |
| **Голосні лі́тери (Vowel Letters)** | ✅ | 446 | Included in Core |
| **Чита́ння слів (Reading Words)** | 🎮 | 85 | Activity (85 items, min 2) |
| **Підсумок — Summary** | ✅ | 802 | Included in Core |