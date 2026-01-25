# Audit Report: M29 — 29-surzhyk.md
**Level:** C1 | **Module:** M29 | **Phase:** C1.2 | **Pedagogy:** Not Specified | **Target:** 3000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:24:22

## Configuration
**Type:** C1-grammar
**Word Target:** 3000 words
**Activities:** 12-16 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Required Types:** cloze, error-correction, fill-in, group-sort, match-up, quiz
**Engagement:** ≥7 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Що таке суржик? | 12 | 5 | ✅ |
| 2 | group-sort | Суржик чи Норма? | 16 | 12 | ✅ |
| 3 | match-up | Виправляємо помилки | 12 | 6 | ✅ |
| 4 | fill-in | Редагування тексту | 10 | 6 | ✅ |
| 5 | group-sort | Типи помилок | 16 | 12 | ✅ |
| 6 | quiz | Культурний феномен | 12 | 5 | ✅ |
| 7 | match-up | Фальшиві друзі | 14 | 6 | ✅ |
| 8 | fill-in | Мовна чистота | 10 | 6 | ✅ |
| 9 | unjumble | Речення без суржику | 8 | 5 | ✅ |
| 10 | quiz | Лінгвістична теорія | 12 | 5 | ✅ |
| 11 | essay-response | Есе: Проблема Суржику | 1 | 1 | ✅ |
| 12 | mark-the-words | Знайдіть суржик | 6 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 12-16) ✅
- Unique types: 7 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Required types used: 4/6 (fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: Schema validation error at key 'words': ['Наступна', 'автобусна', 'зупинка', 'знаходиться', 'прямо', 'біля', 'великого', 'продуктового', 'супермаркету', 'на', 'куті'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2328/3000 (raw: 2546)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 7/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 90-100% (grammar))
- **Richness:** ❌ 79% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 79% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 31 | 24 | 100% | 20% | 20.0% |
| engagement | 14 | 5 | 100% | 15% | 15.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 20 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 17 | 5 | 100% | 5% | 5.0% |
| proverbs | 0 | 1 | 0% | 5% | 0.0% |
| **TOTAL** | | | | | **79.9%** |

### Dryness Flags & Fixes
- ❌ **NO_DIALOGUE**
  - FIX:
    Add 4+ mini-dialogues. Use this exact format:
    
    **Діалог: [Location in Ukraine]**
    
    > — [Speaker 1 line with **bolded** grammar examples]
    > — [Speaker 2 response with **bolded** grammar examples]
    > — [Speaker 1 continuation]
    > — [Speaker 2 conclusion]
    
    Example locations: На Бесарабському ринку, У львівській кав'ярні, В одеському трамваї, На Подолі

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 31 | Included in Core |
| **1. Що таке суржик?** | ⚪️ | 154 | Skipped |
| **Соціолінгвістичний аналіз** | ✅ | 233 | Included in Core |
| **3. Чому ми так говоримо? (Історичний контекст)** | ✅ | 157 | Included in Core |
| **4. Суржик у культурі: Від сорому до сміху** | ✅ | 175 | Included in Core |
| **5. Інтернет-суржик: Нова реальність** | ⚪️ | 120 | Skipped |
| **6. Читання: Суржик у діалозі** | ✅ | 230 | Included in Core |
| **7. Приклади вживання суржику** | ⚪️ | 158 | Skipped |
| **8. Мовна гігієна: Як перейти на чисту мову?** | ⚪️ | 174 | Skipped |
| **9. Приклади з життя: Діалоги** | ✅ | 193 | Included in Core |
| **10. Практикум редагування** | ⚪️ | 200 | Skipped |
| **Підсумок** | ✅ | 81 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 95 | Skipped |