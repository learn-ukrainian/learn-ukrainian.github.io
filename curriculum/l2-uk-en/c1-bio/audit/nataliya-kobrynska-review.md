# Audit Report: M45 — nataliya-kobrynska.md

**Level:** C1 | **Module:** M45 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:18

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
| 1 | quiz | Життя і діяльність Наталії Кобринської | 12 | 5 | ✅ |
| 2 | fill-in | Лексика фемінізму та права | 12 | 6 | ✅ |
| 3 | match-up | Поняття та їх значення | 12 | 6 | ✅ |
| 4 | select | Аналіз діяльності Кобринської | 6 | 5 | ✅ |
| 5 | error-correction | Граматика в біографічному тексті | 12 | 5 | ✅ |
| 6 | group-sort | Кобринська vs Кобилянська | 24 | 1 | ✅ |
| 7 | essay-response | Критичний аналіз: Економіка і Свобода | 1 | 1 | ✅ |
| 8 | comparative-study | Порівняння епох | 1 | 1 | ✅ |
| 9 | reading | Аналіз новели | 3 | 1 | ✅ |
| 10 | essay-response | Есе: Право бути людиною | 1 | 1 | ✅ |
| 11 | unjumble | Цитати Кобринської | 6 | 5 | ✅ |
| 12 | cloze | Життєвий шлях Наталії Кобринської | 12 | 1 | ✅ |
| 13 | translate | Переклад тез про Кобринську | 6 | 5 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in nataliya-kobrynska.yaml: Schema validation error at key '12': {'type': 'translate', 'title': 'Переклад тез про Кобринську', 'items': [{'source': "She organized the first women's society in Halychyna.", 'options': [{'text': 'Вона організувала перше жіноче товариство в Галичині.', 'correct': True}, {'text': 'Вона організувала жіночий клуб у Києві.', 'correct': False}, {'text': 'Вона була членом чоловічого товариства.', 'correct': False}, {'text': 'Вона заснувала школу для дівчат.', 'correct': False}]}, {'source': 'She believed that economic independence is key to freedom.', 'options': [{'text': 'Вона вірила, що економічна незалежність є ключем до свободи.', 'correct': True}, {'text': 'Вона вважала, що гроші не важливі.', 'correct': False}, {'text': 'Вона думала, що свобода не залежить від економіки.', 'correct': False}, {'text': 'Вона хотіла, щоб жінки були багатими.', 'correct': False}]}, {'source': "She edited the almanac 'The First Wreath'.", 'options': [{'text': "Вона редагувала альманах 'Перший вінок'.", 'correct': True}, {'text': "Вона написала роман 'Перший вінок'.", 'correct': False}, {'text': 'Вона купила вінок.', 'correct': False}, {'text': 'Вона продавала альманахи.', 'correct': False}]}, {'source': 'Her works address acute social problems.', 'options': [{'text': 'Її твори порушують гострі соціальні проблеми.', 'correct': True}, {'text': 'Її твори описують природу.', 'correct': False}, {'text': "Вона писала про проблеми зі здоров'ям.", 'correct': False}, {'text': 'Вона уникала соціальних тем.', 'correct': False}]}, {'source': 'She died of typhus in 1920.', 'options': [{'text': 'Вона померла від тифу в 1920 році.', 'correct': True}, {'text': 'Вона народилася в 1920 році.', 'correct': False}, {'text': 'Вона виїхала в 1920 році.', 'correct': False}, {'text': 'Вона захворіла в 1920 році.', 'correct': False}]}, {'source': "She advocated for women's right to vote.", 'options': [{'text': 'Вона виступала за право жінок голосувати.', 'correct': True}, {'text': 'Вона була проти виборів.', 'correct': False}, {'text': 'Вона голосувала лише вдома.', 'correct': False}, {'text': 'Вона не цікавилася політикою.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 1907/4000 (raw: 2145)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 11 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ** | ✅ | 129 | Included in Core |
| **Життєпис** | ⚪️ | 679 | Skipped |
| **Спадщина** | ⚪️ | 56 | Skipped |
| **Внесок** | ⚪️ | 54 | Skipped |
| **Історичний контекст** | ✅ | 433 | Included in Core |
| **Порівняльний аналіз** | ✅ | 47 | Included in Core |
| **Критичне мислення** | ⚪️ | 70 | Skipped |
| **Есе** | ⚪️ | 38 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 238 | Skipped |
| **Підсумок** | ✅ | 75 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 12 | Skipped |
