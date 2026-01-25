# Audit Report: M56 — mykhailo-hrushevskyi-biography.md
**Level:** C1 | **Module:** M56 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:15

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
| 1 | quiz | «Науковий спадок та формування національної ідентичності» | 5 | 5 | ✅ |
| 2 | match-up | «Хронологія життя та політичної боротьби» | 8 | 6 | ✅ |
| 3 | fill-in | «Державотворча та політична термінологія» | 6 | 6 | ✅ |
| 4 | true-false | «Факти, оцінки та історичні контексти» | 5 | 5 | ✅ |
| 5 | select | «Політичні досягнення та ідеї лідера» | 5 | 5 | ✅ |
| 6 | error-correction | «Граматика та академічний стиль» | 5 | 5 | ✅ |
| 7 | group-sort | «Сфери діяльності та наукові акценти» | 12 | 1 | ✅ |
| 8 | unjumble | «Декларації української самостійності» | 5 | 5 | ✅ |
| 9 | quiz | «Трагічний фінал та вічна пам'ять» | 5 | 5 | ✅ |
| 10 | essay-response | «Грушевський — Битва за минуле як битва за майбутнє» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз державотворчої філософії Грушевського» | 1 | 1 | ✅ |
| 12 | comparative-study | «Професори-президенти — Грушевський та Масарик» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykhailo-hrushevskyi-biography.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Декларації української самостійності»', 'items': [{'words': ['«Віднині»', '«Українська»', '«Народна»', '«Республіка»', '«стає»', '«самостійною»', '«ні»', '«від»', '«кого»', '«незалежною»', '«вільною»', '«суверенною»', '«державою»', '«всього»', '«українського»', '«народу»'], 'answer': '«Віднині Українська Народна Республіка стає самостійною ні від кого незалежною вільною суверенною державою всього українського народу»'}, {'words': ['«Ми»', '«маємо»', '«науково»', '«довести»', '«що»', '«українська»', '«історія»', '«має»', '«свої»', '«витоки»', '«у»', '«княжому»', '«Києві»', '«а»', '«не»', '«у»', '«московських»', '«болотах»'], 'answer': '«Ми маємо науково довести що українська історія має свої витоки у княжому Києві а не у московських болотах»'}, {'words': ['«Тільки»', '«через»', '«пізнання»', '«власного»', '«минулого»', '«нація»', '«може»', '«здобути»', '«справжню»', '«інтелектуальну»', '«свободу»', '«та»', '«збудувати»', '«своє»', '«власне»', '«щасливе»', '«майбутнє»'], 'answer': '«Тільки через пізнання власного минулого нація може здобути справжню інтелектуальну свободу та збудувати своє власне щасливе майбутнє»'}, {'words': ['«Наша»', '«головна»', '«мета»', '«це»', '«соборна»', '«демократична»', '«Україна»', '«яка»', '«буде»', '«рівною»', '«серед»', '«рівних»', '«у»', '«великій»', '«родині»', '«європейських»', '«вільних»', '«народів»'], 'answer': '«Наша головна мета це соборна демократична Україна яка буде рівною серед рівних у великій родині європейських вільних народів»'}, {'words': ['«Вчений»', '«має»', '«йти»', '«попереду»', '«свого»', '«народу»', '«вказуючи»', '«йому»', '«шлях»', '«до»', '«правди»', '«навіть»', '«якщо»', '«цей»', '«шлях»', '«буде»', '«надзвичайно»', '«важким»'], 'answer': '«Вчений має йти попереду свого народу вказуючи йому шлях до правди навіть якщо цей шлях буде надзвичайно важким»'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1947/4000 (raw: 2196)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 11/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 100% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 13 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ** | ✅ | 312 | Included in Core |
| **Біографія** | ⚪️ | 988 | Skipped |
| **Історичний контекст** | ✅ | 212 | Included in Core |
| **Порівняльний аналіз** | ✅ | 91 | Included in Core |
| **Критичне мислення** | ⚪️ | 173 | Skipped |
| **Summary** | ✅ | 84 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |