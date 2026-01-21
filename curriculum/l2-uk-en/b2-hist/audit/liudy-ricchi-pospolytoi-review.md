# Audit Report: M39 — liudy-ricchi-pospolytoi.md
**Level:** B2 | **Module:** M39 | **Phase:** HIST.4 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q3 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння тексту' Q8 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in liudy-ricchi-pospolytoi.yaml: Schema validation error at key '3': {'type': 'comparative-study', 'title': 'Порівняльний аналіз: Суспільні стани', 'items_to_compare': ['Шляхта', 'Міщани', 'Селяни'], 'criteria': ['Політичні права', 'Економічні можливості', 'Судовий захист', 'Свобода пересування'], 'min_words': 150, 'model_answer': 'Порівняння трьох основних станів Речі Посполитої демонструє глибоку соціальну нерівність.\n\n**Політичні права:** Шляхта мала повні права — участь у сеймі, вибори короля. Міщани мали обмежене самоврядування. Селяни не мали жодних політичних прав.\n\n**Судовий захист:** Шляхтича не можна було арештувати без суду. Селян судив пан — тобто їхній гнобитель.\n\nВисновок: лише шляхта користувалася реальною свободою.\n'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ❌ 2535/4000
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 98.9% (target 90-100% (history))
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
| engagement | 19 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 14 | 2 | 100% | 14% | 14.3% |
| cultural | 8 | 4 | 100% | 10% | 9.5% |
| visual | 17 | 4 | 100% | 10% | 9.5% |
| variety | 0.94 | - | 94% | 5% | 4.5% |
| paragraph_var | 0.92 | - | 92% | 5% | 4.4% |
| questions | 19 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 57 | Included in Core |
| **Вступ** | ⚪️ | 220 | Skipped |
| **Шляхта і магнати** | ⚪️ | 536 | Skipped |
| **Міщани і ремісники** | ⚪️ | 399 | Skipped |
| **Селяни і кріпацтво** | ⚪️ | 486 | Skipped |
| **Читання** | ✅ | 181 | Included in Core |
| **Первинні джерела** | ⚪️ | 230 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 281 | Skipped |
| **Підсумок** | ✅ | 110 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 35 | Skipped |