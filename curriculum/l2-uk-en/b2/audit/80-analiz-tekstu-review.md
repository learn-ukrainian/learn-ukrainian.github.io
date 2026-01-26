# Audit Report: M80 — 80-analiz-tekstu.md
**Level:** B2 | **Module:** M80 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:39

## Configuration
**Type:** B2-skills
**Word Target:** 1750 words
**Activities:** 14-18 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥5 types required
**Priority Types:** cloze, fill-in, quiz, translate
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Термінологія аналізу | 14 | 8 | ✅ |
| 2 | quiz | Визначення стилю тексту | 8 | 8 | ✅ |
| 3 | match-up | Мета автора | 12 | 8 | ✅ |
| 4 | quiz | Виявлення упередженості | 8 | 8 | ✅ |
| 5 | match-up | Читаємо підтекст | 12 | 8 | ✅ |
| 6 | fill-in | Структура аргументації | 8 | 8 | ✅ |
| 7 | match-up | Порядок частин есе | 12 | 8 | ✅ |
| 8 | group-sort | Сортування джерел | 18 | 14 | ✅ |
| 9 | match-up | Техніки маніпуляції | 12 | 8 | ✅ |
| 10 | quiz | Плагіат чи ні? | 8 | 8 | ✅ |
| 11 | fill-in | Лексика в контексті | 8 | 8 | ✅ |
| 12 | match-up | Види посилань | 12 | 8 | ✅ |
| 13 | quiz | Факт чи думка? | 8 | 8 | ✅ |
| 14 | match-up | Логічні хиби | 12 | 8 | ✅ |
| 15 | essay-response | Аналітичний розбір маніпуляції | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 14-18) ✅
- Unique types: 5 (minimum: 5) ✅
- Priority types used: 2/4 (fill-in, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 80-analiz-tekstu.yaml: Schema validation error at key '12': {'type': 'quiz', 'title': 'Факт чи думка?', 'items': [{'question': '«Київ офіційно є головною столицею сучасної незалежної європейської держави Україна згідно з Основним Законом нашої країни».', 'options': [{'text': 'Факт', 'correct': True}, {'text': 'Думка', 'correct': False}, {'text': 'Гіпотеза', 'correct': False}, {'text': 'Міф', 'correct': False}]}, {'question': '«Київ — це, без жодного сумніву, найкраще місто для життя у світі».', 'options': [{'text': 'Думка', 'correct': True}, {'text': 'Факт', 'correct': False}, {'text': 'Статистика', 'correct': False}, {'text': 'Аксіома', 'correct': False}]}, {'question': '«Планета Земля постійно обертається навколо Сонця за певною еліптичною траєкторією, що зумовлює зміну пір року».', 'options': [{'text': 'Факт', 'correct': True}, {'text': 'Думка', 'correct': False}, {'text': 'Помилка', 'correct': False}, {'text': 'Вигадка', 'correct': False}]}, {'question': '«Цей новий пригодницький фільм здався мені надзвичайно нудним, затягнутим та абсолютно нецікавим для сучасного глядача».', 'options': [{'text': 'Думка', 'correct': True}, {'text': 'Факт', 'correct': False}, {'text': 'Доказ', 'correct': False}, {'text': 'Закон', 'correct': False}]}, {'question': '«В Україні на даний момент офіційно проживає понад тридцять мільйонів людей».', 'options': [{'text': 'Факт', 'correct': True}, {'text': 'Думка', 'correct': False}, {'text': 'Емоція', 'correct': False}, {'text': 'Смак', 'correct': False}]}, {'question': '«Податки у нашій країні є занадто високими для малого бізнесу».', 'options': [{'text': 'Думка', 'correct': True}, {'text': 'Факт', 'correct': False}, {'text': 'Число', 'correct': False}, {'text': 'Дата', 'correct': False}]}, {'question': '«День Незалежності України офіційно відзначається державою щороку саме двадцять четвертого серпня на честь проголошення Акту незалежності».', 'options': [{'text': 'Факт', 'correct': True}, {'text': 'Думка', 'correct': False}, {'text': 'Прогноз', 'correct': False}, {'text': 'План', 'correct': False}]}, {'question': '«Математика — це найбільш складна та нудна наука з усіх існуючих».', 'options': [{'text': 'Думка', 'correct': True}, {'text': 'Факт', 'correct': False}, {'text': "Об'єкт", 'correct': False}, {'text': 'Вимір', 'correct': False}]}], 'instruction': "Визначте, чи є наведене твердження об'єктивним фактом чи суб'єктивною думкою."} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення' per template 'b2-module-template.md'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2147/1750 (raw: 2324)
- **Activities:** ✅ 15/14
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 5/5 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 1 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (15 activities)
- **Immersion:** 🇺🇦 98.5% (target 90-100% (skills))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 22 | 24 | 92% | 20% | 18.4% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 7 | 4 | 100% | 15% | 15.0% |
| variety | 1.00 | - | 100% | 10% | 10.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 13 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 32 | 5 | 100% | 5% | 5.0% |
| proverbs | 6 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 105 | Included in Core |
| **Вступ: Тріада розуміння** | ✅ | 420 | Included in Core |
| **Стратегії: Читання між рядків** | ✅ | 302 | Included in Core |
| **Deep Dive: Структура аргументації** | ✅ | 189 | Included in Core |
| **Практика: Виявлення маніпуляцій** | ⚪️ | 185 | Skipped |
| **Методи деконструкції: Практичний посібник** | ⚪️ | 227 | Skipped |
| **Риторичні засоби: Механіка впливу в політиці** | ⚪️ | 179 | Skipped |
| **Академічна доброчесність: Чесність у науці** | ⚪️ | 101 | Skipped |
| **Цифрові інструменти для аналізу: Майбутнє критичного мислення** | ✅ | 229 | Included in Core |
| **Підсумок** | ✅ | 100 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |