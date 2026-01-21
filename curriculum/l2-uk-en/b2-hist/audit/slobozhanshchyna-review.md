# Audit Report: M38 — slobozhanshchyna.md
**Level:** B2 | **Module:** M38 | **Phase:** HIST.4 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q3 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q5 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in slobozhanshchyna.yaml: Schema validation error at key '3': {'type': 'comparative-study', 'title': 'Порівняльний аналіз: Слобідські полки vs Гетьманщина', 'items_to_compare': ['Слобідські козацькі полки', 'Полки Гетьманщини'], 'criteria': ['Політичний статус', 'Рівень автономії', 'Відносини з Московією', 'Соціальна структура'], 'min_words': 150, 'model_answer': 'Порівняння слобідських полків і Гетьманщини виявляє як спільні риси, так і суттєві відмінності.\n\n**Політичний статус:** Гетьманщина формально мала статус автономного утворення з власним гетьманом. Слобідські полки підпорядковувалися безпосередньо Розрядному приказу в Москві.\n\n**Рівень автономії:** Парадоксально, слобідські полки часом мали більшу фактичну автономію, оскільки перебували на периферії.\n\n**Соціальна структура:** На Слобожанщині не було кріпацтва до 1765 року, тоді як у Гетьманщині воно зростало.\n'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 5 violations (moderate)

## Gates
- **Words:** ❌ 2903/4000
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 20 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 8 | 4 | 100% | 10% | 9.5% |
| visual | 15 | 4 | 100% | 10% | 9.5% |
| variety | 0.93 | - | 93% | 5% | 4.4% |
| paragraph_var | 0.88 | - | 88% | 5% | 4.2% |
| questions | 19 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ** | ⚪️ | 255 | Skipped |
| **Заселення Слобожанщини** | ⚪️ | 588 | Skipped |
| **П'ять слобідських козацьких полків** | ⚪️ | 468 | Skipped |
| **Суспільство Слобожанщини** | ⚪️ | 415 | Skipped |
| **Читання** | ✅ | 177 | Included in Core |
| **Первинні джерела** | ⚪️ | 326 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 433 | Skipped |
| **Підсумок** | ✅ | 129 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 42 | Skipped |