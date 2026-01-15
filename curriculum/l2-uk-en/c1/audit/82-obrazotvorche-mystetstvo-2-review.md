# Audit Report: 178-obrazotvorche-mystetstvo-2.md
**Phase:** C1.5 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати Марії Примаченко' item 4 has 10 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 178-obrazotvorche-mystetstvo-2.yaml: Schema validation error at key 'blanks': [{'id': 1, 'answer': 'світ', 'options': ['світ', 'село', 'місто', 'район']}, {'id': 2, 'answer': 'освіти', 'options': ['освіти', 'фарби', 'хати', 'землі']}, {'id': 3, 'answer': 'звірі', 'options': ['звірі', 'люди', 'будинки', 'машини']}, {'id': 4, 'answer': 'назву', 'options': ['назву', 'ціну', 'раму', 'вагу']}, {'id': 5, 'answer': 'атомну', 'options': ['атомну', 'холодну', 'стару', 'нову']}, {'id': 6, 'answer': 'наївним', 'options': ['наївним', 'суворим', 'нудним', 'швидким']}, {'id': 7, 'answer': 'фарби', 'options': ['фарби', 'олівці', 'ручки', 'нитки']}, {'id': 8, 'answer': 'фантазії', 'options': ['фантазії', 'бідності', 'ліні', 'роботи']}, {'id': 9, 'answer': 'модний', 'options': ['модний', 'старий', 'брудний', 'дешевий']}, {'id': 10, 'answer': 'ідентичності', 'options': ['ідентичності', 'слабкості', 'байдужості', 'покори']}, {'id': 11, 'answer': 'щирістю', 'options': ['щирістю', 'хитрістю', 'злістю', 'нудьгою']}, {'id': 12, 'answer': 'диво', 'options': ['диво', 'гроші', 'біду', 'страх']}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1987/2000 (13 short)
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 13/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (16 activities)
- **Immersion:** 🇺🇦 98.9% (target 90-100% (fine-arts))
- **Richness:** ✅ 98% (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 30 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 5 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Вступ: Мистецтво в лещатах ідеології** | ⚪️ | 121 | Skipped |
| **Наївне мистецтво: Душа народу** | ⚪️ | 357 | Skipped |
| **Шістдесятники: Мистецтво спротиву** | ⚪️ | 225 | Skipped |
| **Іван Марчук: Геній пльонтанізму** | ⚪️ | 183 | Skipped |
| **Сучасне мистецтво: Нова хвиля та інституції** | ⚪️ | 581 | Skipped |
| **Аналіз** | ✅ | 206 | Included in Core |
| **Підсумок** | ✅ | 93 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 137 | Skipped |