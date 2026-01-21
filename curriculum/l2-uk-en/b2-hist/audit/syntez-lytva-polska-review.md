# Audit Report: M40 — syntez-lytva-polska.md
**Level:** B2 | **Module:** M40 | **Phase:** HIST.4 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка синтезу знань' Q2 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка синтезу знань' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[SECTION_ORDER]** '## Словник епохи: Литовсько-польська доба' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in syntez-lytva-polska.yaml: Schema validation error at key '3': {'type': 'comparative-study', 'title': 'Порівняльний аналіз: ВКЛ vs Річ Посполита', 'items_to_compare': ['Велике князівство Литовське (до 1569)', 'Річ Посполита (після 1569)'], 'criteria': ['Статус руської мови', "Становище православ'я", 'Рівень закріпачення', 'Автономія українських земель'], 'min_words': 150, 'model_answer': "Порівняння становища українців у ВКЛ та Речі Посполитій демонструє поступову втрату автономії та прав.\n\n**Статус руської мови:** У ВКЛ руська мова була офіційною мовою канцелярії. У Речі Посполитій її поступово витіснила польська.\n\n**Становище православ'я:** У ВКЛ православ'я функціонувало вільно. Після Берестейської унії православні почали зазнавати переслідувань.\n\nВисновок: Люблінська унія означала різке погіршення становища українців.\n"} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Застосування в контексті, Вступ
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 15/100)

- 5 violations (moderate)

## Gates
- **Words:** ❌ 2077/4000
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 98.8% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 12 | 3 | 100% | 24% | 23.8% |
| engagement | 15 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 7 | 4 | 100% | 10% | 9.5% |
| visual | 22 | 4 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 23 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 55 | Included in Core |
| **Огляд періоду: Литовсько-польська доба** | ⚪️ | 691 | Skipped |
| **Первинні джерела** | ⚪️ | 81 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 142 | Skipped |
| **Читання** | ✅ | 161 | Included in Core |
| **Хронологія: Литовсько-польська доба** | ⚪️ | 148 | Skipped |
| **Словник епохи: Литовсько-польська доба** | ⚪️ | 82 | Skipped |
| **Есе-аналіз: Литовсько-польська спадщина** | ✅ | 350 | Included in Core |
| **Зв'язок із сьогоденням** | ⚪️ | 204 | Skipped |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Ключові висновки епохи** | ⚪️ | 0 | Skipped |
| **Модулі цієї епохи** | ⚪️ | 0 | Skipped |
| **Що далі?** | ⚪️ | 129 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 34 | Skipped |