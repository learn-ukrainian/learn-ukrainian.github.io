# Audit Report: M999 — c1-bio-checkpoint.md

**Level:** C1 | **Module:** M999 | **Phase:** C1 | **Pedagogy:** TTT | **Target:** 1750
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:27:06

## Configuration

**Type:** C1-checkpoint
**Word Target:** 1750 words
**Activities:** 14-18 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, quiz
**Required Types:** essay-response, match-up, oral-presentation, quiz, timeline
**Engagement:** ≥4 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥15 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Княжа доба та Середньовіччя (M36-42) | 5 | 5 | ✅ |
| 2 | quiz | Козацька епоха та Гетьманщина (M43-51) | 5 | 5 | ✅ |
| 3 | quiz | Культурне відродження та XIX століття (M52-83) | 5 | 5 | ✅ |
| 4 | quiz | XX століття та Спротив (M84-114) | 5 | 5 | ✅ |
| 5 | match-up | Постаті та їхні сфери діяльності | 10 | 6 | ✅ |
| 6 | fill-in | Біографічна лексика (Review) | 7 | 6 | ✅ |
| 7 | match-up | Біографічні терміни та визначення | 8 | 6 | ✅ |
| 8 | error-correction | Граматика та Стиль | 6 | 5 | ✅ |
| 9 | group-sort | Класифікація діячів за епохами | 15 | 14 | ✅ |
| 10 | select | Аналіз концепції Деколонізації | 5 | 5 | ✅ |
| 11 | cloze | Інтеграційний текст: «Спадщина свободи» | 14 | 14 | ✅ |
| 12 | mark-the-words | Знайдіть біографічні терміни | 9 | 5 | ✅ |
| 13 | true-false | Перевірка знань про сучасних діячів (M115-130) | 6 | 5 | ✅ |
| 14 | comparative-study | Порівняння правозахисних епох | 1 | 1 | ✅ |
| 15 | essay-response | Підсумкове есе: Постаті та майбутнє | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 14-18) ✅
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 4/4 (cloze, error-correction, fill-in, quiz) ✅
- Required types used: 3/5 (essay-response, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['timeline', 'oral-presentation']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent
- **[YAML_SCHEMA_VIOLATION]** Schema error in c1-bio-checkpoint.yaml: Schema validation error at key '12': {'type': 'true-false', 'title': 'Перевірка знань про сучасних діячів (M115-130)', 'items': [{'statement': 'Леонід Каденюк був першим космонавтом незалежної України.', 'correct': True, 'explanation': 'Це сталося у 1997 році на борту шатла Columbia.'}, {'statement': 'Сергій Жадан є автором роману «Танґо смерті».', 'correct': False, 'explanation': 'Автором «Танґо смерті» є Юрій Винничук.'}, {'statement': 'Олександра Матвійчук очолює Центр громадянських свобод.', 'correct': True, 'explanation': 'Саме ця організація отримала Нобелівську премію миру.'}, {'statement': 'Ярослав Грицак відомий передусім як балетмейстер.', 'correct': False, 'explanation': 'Грицак — відомий історик та публічний інтелектуал.'}, {'statement': 'Василь Шкляр написав роман «Залишенець» про боротьбу холодноярців.', 'correct': True, 'explanation': 'Цей твір став знаковим для сучасної історичної прози.'}, {'statement': 'Оксана Забужко є авторкою есеїстичного твору «Музей покинутих секретів».', 'correct': True, 'explanation': 'Це один із найважливіших романів сучасної української літератури.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template.md'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ✅ 1817/1750 (raw: 1957)
- **Activities:** ✅ 15/14
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 15 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (checkpoint - no gate)
- **Richness:** ❌ 81% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details

**Score:** 81% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 32 | 24 | 100% | 20% | 20.0% |
| engagement | 4 | 5 | 80% | 15% | 12.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| realworld | 3 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 16 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **81.9%** |

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
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Огляд** | ⚪️ | 26 | Skipped |
| **Навички** | ⚪️ | 106 | Skipped |
| **Навичка 1: Біографічний наратив та академічний регістр** | ⚪️ | 308 | Skipped |
| **Навичка 2: Історичний контекст та тяглість** | ✅ | 249 | Included in Core |
| **Інтеграційне завдання** | ⚪️ | 815 | Skipped |
| **Підсумок** | ✅ | 92 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 149 | Skipped |
