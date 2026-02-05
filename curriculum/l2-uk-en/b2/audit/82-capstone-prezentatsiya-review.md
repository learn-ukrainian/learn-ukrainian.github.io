# Audit Report: M82 — 82-capstone-prezentatsiya.md
**Level:** B2 | **Module:** M82 | **Phase:** B2.4 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:04:41

## Configuration
**Type:** B2-history
**Word Target:** 2000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Термінологія виступу | 12 | 8 | ✅ |
| 2 | group-sort | Структура презентації | 18 | 1 | ✅ |
| 3 | quiz | Дизайн слайдів: Так чи Ні? | 8 | 8 | ✅ |
| 4 | match-up | Риторичні прийоми | 12 | 8 | ✅ |
| 5 | fill-in | Фрази для вступу | 8 | 8 | ✅ |
| 6 | match-up | Мова тіла | 12 | 8 | ✅ |
| 7 | quiz | Складні запитання | 8 | 8 | ✅ |
| 8 | group-sort | Підготовка vs Виступ | 22 | 1 | ✅ |
| 9 | match-up | Фрази-переходи | 12 | 8 | ✅ |
| 10 | fill-in | Фрази для висновку | 8 | 8 | ✅ |
| 11 | quiz | Голос оратора | 8 | 8 | ✅ |
| 12 | match-up | Візуальні засоби | 12 | 8 | ✅ |
| 13 | true-false | Міфи про публічні виступи | 8 | 8 | ✅ |
| 14 | true-false | Фінальний чек-лист | 8 | 8 | ✅ |
| 15 | essay-response | Рефлексія оратора | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Capstone: Презентація | 3 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 3-9) ❌
- Unique types: 7 (minimum: 2) ✅
- Priority types used: 2/4 (essay-response, reading) ✅
- Required types used: 3/3 (essay-response, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 82-capstone-prezentatsiya.yaml: Schema validation error at key '13': {'type': 'true-false', 'title': 'Фінальний чек-лист', 'items': [{'statement': 'Я знаю свою тему на 100%.', 'correct': True, 'explanation': 'Компетентність — основа впевненості.'}, {'statement': 'Я перевірив презентацію на помилки.', 'correct': True, 'explanation': 'Помилки псують враження.'}, {'statement': 'Я знаю, скільки часу займає мій виступ.', 'correct': True, 'explanation': 'Таймінг — це повага до публіки.'}, {'statement': 'Я підготував відповіді на можливі питання.', 'correct': True, 'explanation': 'Щоб не розгубитися.'}, {'statement': 'Я виспався перед виступом.', 'correct': True, 'explanation': 'Втомлений оратор — нудний оратор.'}, {'statement': 'Я перевірив техніку (проектор, мікрофон).', 'correct': True, 'explanation': 'Техніка часто підводить.'}, {'statement': 'Я взяв воду.', 'correct': True, 'explanation': 'Голос може сісти.'}, {'statement': 'Я налаштований позитивно.', 'correct': True, 'explanation': 'Усмішка — ваша зброя.'}], 'instruction': 'Визначте, чи твердження правильне.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 1868/2000 (raw: 1936)
- **Activities:** ✅ 16/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 7/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 8 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 16 (target 3-9)
- **Immersion:** 🇺🇦 98.8% (target 90-100% (history))
- **Richness:** ❌ 70% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 70% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 13 | 24 | 54% | 20% | 10.8% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| realworld | 9 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 14 | 5 | 100% | 5% | 5.0% |
| proverbs | 0 | 1 | 0% | 5% | 0.0% |
| **TOTAL** | | | | | **70.7%** |

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
- ❌ **NO_PROVERBS**
  - FIX:
    Add 1+ Ukrainian proverb. Use this format:
    
    Українці кажу|ть: «[Proverb in Ukrainian]»
    
    Зверніть увагу: **[word]** — [aspect] вид, бо [explanation why this aspect is used].
    
    Example: «Не кажи гоп, поки не перескочиш» — **перескочиш** is perfective because it's about the result.

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Огляд — Усна презентація** | ⚪️ | 367 | Skipped |
| **Структура презентації** | ⚪️ | 358 | Skipped |
| **Візуальні матеріали** | ⚪️ | 358 | Skipped |
| **Техніка виступу** | ⚪️ | 269 | Skipped |
| **Відповіді на запитання** | ⚪️ | 249 | Skipped |
| **Репетиція та фінал** | ⚪️ | 43 | Skipped |
| **Підсумок** | ✅ | 224 | Included in Core |