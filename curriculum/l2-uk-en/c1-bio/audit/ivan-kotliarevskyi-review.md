# Audit Report: M29 — ivan-kotliarevskyi.md

**Level:** C1 | **Module:** M29 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:11

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
| 1 | quiz | «Розуміння біографії та творчості Івана Котляревського» | 12 | 5 | ✅ |
| 2 | fill-in | «Літературна термінологія Котляревського» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика в біографії письменника» | 12 | 5 | ✅ |
| 4 | match-up | «Літературознавчі поняття» | 12 | 6 | ✅ |
| 5 | select | «Аналіз стилю «Енеїди»» | 5 | 5 | ✅ |
| 6 | true-false | «Факти про життя Котляревського» | 12 | 5 | ✅ |
| 7 | reading | «Сміх крізь сльози: «Енеїда»» | 3 | 1 | ✅ |
| 8 | reading | «Історія першого видання» | 3 | 1 | ✅ |
| 9 | essay-response | «Батько українського слова» | 1 | 1 | ✅ |
| 10 | comparative-study | «Два світи: Сковорода та Котляревський» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз феномену «Енеїди»» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення тез про Котляревського» | 12 | 5 | ✅ |
| 13 | translate | «Літературний переклад» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук літературних термінів» | 11 | 5 | ✅ |
| 15 | true-false | «Світогляд Котляревського» | 12 | 5 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in ivan-kotliarevskyi.yaml: Schema validation error at key '7': {'type': 'reading', 'title': '«Історія першого видання»', 'resource': {'type': 'article', 'url': 'https://localhistory.org.ua/texts/statti/iak-kotliarevskii-eneidu-pisav-i-chomu-vona-stala-revoliutsiieiu/', 'title': '«Як Котляревський «Енеїду» писав і чому вона стала революцією»'}, 'tasks': ['«Як автор статті пояснює феномен успіху «Енеїди» серед російського дворянства?»', '«Які нові факти про видання Парпури наводяться у тексті?»', '«Чому Котляревський спочатку образився на першого видавця свого твору?»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на розвиток мови, Спадщина
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation

**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates

- **Words:** ❌ 1978/4000 (raw: 2202)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
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
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 6 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 80 | Included in Core |
| **Вступ** | ✅ | 220 | Included in Core |
| **Життєпис** | ⚪️ | 848 | Skipped |
| **Внесок** | ⚪️ | 183 | Skipped |
| **Спадщина** | ⚪️ | 377 | Skipped |
| **Порівняльний аналіз** | ✅ | 111 | Included in Core |
| **Підсумок** | ✅ | 71 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 88 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |
