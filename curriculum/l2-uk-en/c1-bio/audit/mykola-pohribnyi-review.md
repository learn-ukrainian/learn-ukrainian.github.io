# Audit Report: M101 — mykola-pohribnyi.md
**Level:** C1 | **Module:** M101 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:46

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Життя та діяльність Миколи Погрібного | 6 | 5 | ✅ |
| 2 | match-up | Термінологія вимови та мовознавства | 12 | 6 | ✅ |
| 3 | cloze | Біографія Миколи Погрібного | 12 | 1 | ✅ |
| 4 | true-false | Факти про Миколу Погрібного | 8 | 5 | ✅ |
| 5 | fill-in | Лексика вимови та мовлення | 6 | 6 | ✅ |
| 6 | select | Внесок Погрібного в українську культуру | 5 | 5 | ✅ |
| 7 | error-correction | Граматичні вправи | 5 | 5 | ✅ |
| 8 | unjumble | Твердження про Погрібного | 5 | 5 | ✅ |
| 9 | group-sort | Сфери діяльності Миколи Погрібного | 12 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Погрібний та Огієнко | 1 | 1 | ✅ |
| 11 | essay-response | Аналітичне есе: Роль радіо у збереженні мови | 1 | 1 | ✅ |
| 12 | fill-in | Правила української вимови | 6 | 6 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-pohribnyi.yaml: Schema validation error at key '11': {'type': 'fill-in', 'title': 'Правила української вимови', 'instruction': 'Заповніть пропуски, використовуючи терміни з праць Погрібного.', 'items': [{'sentence': 'В українській мові голосні звуки вимовляються _____ і чітко.', 'answer': 'повнозвучно', 'options': ['повнозвучно', 'невиразно', 'коротко', 'тихо']}, {'sentence': 'Дзвінкі приголосні в кінці слова _____ оглушуються.', 'answer': 'не', 'options': ['не', 'завжди', 'часто', 'іноді']}, {'sentence': 'Літера «г» в українській мові позначає _____ звук.', 'answer': 'гортанний', 'options': ['гортанний', 'проривний', 'шиплячий', 'носовий']}, {'sentence': "М'які приголосні потребують _____ артикуляції.", 'answer': 'палаталізованої', 'options': ['палаталізованої', 'твердої', 'губної', 'зубної']}, {'sentence': 'Наголос в українській мові є _____.', 'answer': 'рухомим', 'options': ['рухомим', 'сталим', 'фіксованим', 'подвійним']}, {'sentence': 'Милозвучність досягається чергуванням _____ та приголосних.', 'answer': 'голосних', 'options': ['голосних', 'наголошених', 'глухих', 'дзвінких']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2473/4000 (raw: 2663)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 11/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9); 1 cloze with year blanks
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 10 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ✅ | 179 | Included in Core |
| **Життєпис** | ⚪️ | 959 | Skipped |
| **Внесок** | ⚪️ | 184 | Skipped |
| **Феномен голосу епохи** | ⚪️ | 446 | Skipped |
| **Останні роки** | ⚪️ | 54 | Skipped |
| **Спадщина** | ⚪️ | 210 | Skipped |
| **Порівняльний аналіз: Погрібний та Огієнко** | ✅ | 209 | Included in Core |
| **Підсумок** | ✅ | 142 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 90 | Skipped |