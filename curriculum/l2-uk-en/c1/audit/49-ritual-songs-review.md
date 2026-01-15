# Audit Report: 145-ritual-songs.md
**Phase:** C1.5 | **Level:** C1 | **Pedagogy:** Cultural Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 145-ritual-songs.yaml: Schema validation error at key '14': {'type': 'fill-in', 'title': 'Символіка кольорів', 'instruction': 'Вставте колір, що відповідає символу.', 'items': [{'sentence': '___ (колір крові та життя) — символ любові та енергії.', 'answer': 'Червоний', 'options': ['Червоний', 'Білий', 'Чорний', 'Синій']}, {'sentence': '___ (колір чистоти) — символ святості та невинності.', 'answer': 'Білий', 'options': ['Білий', 'Зелений', 'Жовтий', 'Сірий']}, {'sentence': '___ (колір землі) — символ смутку та смерті, але й родючості.', 'answer': 'Чорний', 'options': ['Чорний', 'Блакитний', 'Рожевий', 'Золотий']}, {'sentence': '___ (колір весни) — символ відродження природи.', 'answer': 'Зелений', 'options': ['Зелений', 'Фіолетовий', 'Коричневий', 'Срібний']}, {'sentence': '___ (колір сонця) — символ світла та багатства.', 'answer': 'Жовтий', 'options': ['Жовтий', 'Темний', 'Блідий', 'Мутний']}, {'sentence': '___ (колір води і неба) — символ духовності.', 'answer': 'Синій', 'options': ['Синій', 'Червоний', 'Помаранчевий', 'Бежевий']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'c1-module-template.md'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2034/2000
- **Activities:** ✅ 15/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (15 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (cultural))
- **Richness:** ✅ 100% (cultural)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 11 | 5 | 100% | 33% | 33.3% |
| engagement | 8 | 6 | 100% | 20% | 20.0% |
| visual | 8 | 4 | 100% | 13% | 13.3% |
| variety | 1.00 | - | 100% | 7% | 6.7% |
| paragraph_var | 1.00 | - | 100% | 7% | 6.7% |
| examples | 21 | - | 100% | 7% | 6.7% |
| realworld | 1 | - | 100% | 7% | 6.7% |
| questions | 10 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Міфологічне мислення та циклічність** | ⚪️ | 147 | Skipped |
| **Зимовий цикл: Коляда і Щедрий вечір** | ⚪️ | 364 | Skipped |
| **Семантика символіки: Коди природи у слові** | ⚪️ | 292 | Skipped |
| **Весняний цикл: Пробудження життєвої сили** | ⚪️ | 83 | Skipped |
| **Літній цикл: Купальська містерія вогню** | ⚪️ | 216 | Skipped |
| **Осінній цикл: Жнива та Тріумф хліба** | ⚪️ | 205 | Skipped |
| **Народні інструменти у магії обряду** | ⚪️ | 96 | Skipped |
| **Феномен синкретизму: Двовір'я як гармонія** | ⚪️ | 99 | Skipped |
| **Письмо: Есе-дослідження на тему «Щедрика»** | ⚪️ | 157 | Skipped |
| **Читання: Аналіз тексту стародавньої веснянки** | ✅ | 130 | Included in Core |
| **Need More Practice?** | ⚪️ | 59 | Skipped |
| **Підсумок** | ✅ | 99 | Included in Core |