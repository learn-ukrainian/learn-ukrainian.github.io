# Audit Report: M34 — hanna-barvinok.md
**Level:** C1 | **Module:** M34 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:02

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
| 1 | quiz | Глибоке розуміння біографії та культурного внеску Ганни Барвінок | 12 | 5 | ✅ |
| 2 | unjumble | Аналіз стилістичних особливостей прози Ганни Барвінок | 12 | 5 | ✅ |
| 3 | cloze | Життєвий і творчий шлях Ганни Барвінок | 12 | 1 | ✅ |
| 4 | true-false | Факти про життя та спадщину письменниці | 12 | 5 | ✅ |
| 5 | fill-in | Термінологія та лексика модуля | 12 | 6 | ✅ |
| 6 | match-up | Співвіднесення понять та визначень | 12 | 6 | ✅ |
| 7 | select | Аналіз культурно-історичних аспектів | 6 | 5 | ✅ |
| 8 | error-correction | Корекція помилок у біографічних твердженнях | 12 | 5 | ✅ |
| 9 | group-sort | Класифікація концептів та контекстів | 24 | 1 | ✅ |
| 10 | essay-response | Критичний аналіз: Жінка в тіні чи Світло? | 1 | 1 | ✅ |
| 11 | comparative-study | Порівняння: Традиція vs Бунт | 1 | 1 | ✅ |
| 12 | reading | Аналіз мовностилістичних особливостей | 3 | 1 | ✅ |
| 13 | essay-response | Творча робота: Жіночий голос | 1 | 1 | ✅ |
| 14 | translate | Переклад тез про творчість | 6 | 5 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in hanna-barvinok.yaml: Schema validation error at key '13': {'type': 'translate', 'title': 'Переклад тез про творчість', 'items': [{'source': 'She was the first female prose writer in Ukrainian literature.', 'options': [{'text': 'Вона була першою жінкою-прозаїком в українській літературі.', 'correct': True}, {'text': 'Вона перша писала вірші українською мовою.', 'correct': False}, {'text': 'Вона стала першим автором жінкою в світі.', 'correct': False}, {'text': 'Вона почала писати прозу виключно для жінок.', 'correct': False}]}, {'source': 'Her stories are based on ethnographic observations.', 'options': [{'text': 'Її оповідання базуються на етнографічних спостереженнях.', 'correct': True}, {'text': 'Її історії є лише про етнографію села.', 'correct': False}, {'text': 'Вона писала наукові праці про етнографію.', 'correct': False}, {'text': 'Спостереження етнографії є головною темою творів.', 'correct': False}]}, {'source': 'She focused on the inner world of peasant women.', 'options': [{'text': 'Вона зосередилася на внутрішньому світі селянок.', 'correct': True}, {'text': 'Вона писала про зовнішній вигляд селянок.', 'correct': False}, {'text': 'Внутрішній світ жінок не був її темою.', 'correct': False}, {'text': 'Вона фокусувала увагу на роботі селянок.', 'correct': False}]}, {'source': "She sacrificed her wealth to preserve her husband's legacy.", 'options': [{'text': 'Вона пожертвувала своїм багатством заради збереження спадщини чоловіка.', 'correct': True}, {'text': 'Вона віддала всі гроші за спадщину батька.', 'correct': False}, {'text': 'Вона втратила багатство через помилки чоловіка.', 'correct': False}, {'text': 'Вона зберегла спадщину і примножила багатство.', 'correct': False}]}, {'source': 'Her voice was quiet but distinct.', 'options': [{'text': 'Її голос був тихим, але виразним.', 'correct': True}, {'text': 'Вона говорила дуже тихо і нечітко.', 'correct': False}, {'text': 'Її голос мав тишу і вираз обличчя.', 'correct': False}, {'text': 'Вона мала занадто тихий голос для сцени.', 'correct': False}]}, {'source': 'She proved that women have a voice.', 'options': [{'text': 'Вона довела, що жінки мають голос.', 'correct': True}, {'text': 'Вона сказала, що жінки мовчать.', 'correct': False}, {'text': 'Вона співала голосом жінки.', 'correct': False}, {'text': 'Вона втратила голос.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2017/4000 (raw: 2280)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 5 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ** | ✅ | 148 | Included in Core |
| **Життєпис** | ⚪️ | 375 | Skipped |
| **Внесок** | ⚪️ | 254 | Skipped |
| **Аналіз ключових творів** | ✅ | 172 | Included in Core |
| **Спадщина** | ⚪️ | 48 | Skipped |
| **Історичний контекст** | ✅ | 368 | Included in Core |
| **Порівняльний аналіз** | ✅ | 129 | Included in Core |
| **Критичне мислення** | ⚪️ | 60 | Skipped |
| **Есе** | ⚪️ | 50 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 253 | Skipped |
| **Підсумок** | ✅ | 69 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 15 | Skipped |