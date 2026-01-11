# Audit Report: 112-druha-svitova-okupatsii.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння історичного тексту' Q13 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновлення тексту' item 1 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновлення тексту' item 2 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновлення тексту' item 5 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновлення тексту' item 8 has 6 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[FORBIDDEN_HEADER]** Forbidden header '## Зовнішні ресурси' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Зовнішні ресурси' header. This section is auto-injected from docs/resources/external_resources.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.
- **[FORBIDDEN_HEADER]** Forbidden header '## Активності' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Активності' header. This section is auto-injected from activities/{slug}.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ, Граматика в контексті, Контекст: Пакт Молотова — Ріббентропа та «Перші совіти»
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Первинні джерела' per template 'b2-history-module-template'
  - FIX: Add '## Первинні джерела' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[FORBIDDEN_HEADER]** Forbidden header '## Зовнішні ресурси' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Зовнішні ресурси' header. Template 'b2-history-module-template' specifies this section is auto-injected from YAML sidecars.
- ❌ **[FORBIDDEN_HEADER]** Forbidden header '## Активності' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Активності' header. Template 'b2-history-module-template' specifies this section is auto-injected from YAML sidecars.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 16 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2668/2000
- **Activities:** ✅ 19/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 18/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 27/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 9 violations
- **Content_heavy:** ⚠️ Too many activities: 19 (target 10-14)
- **Immersion:** 🇺🇦 98.4% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 99 | Included in Core |
| **Вступ** | ⚪️ | 204 | Skipped |
| **Друга світова: окупації та трагедії** | ⚪️ | 1177 | Skipped |
| **Спадщина та Пам'ять: Сучасний дискурс** | ⚪️ | 280 | Skipped |
| **Порівняльний аналіз окупаційних режимів** | ✅ | 89 | Included in Core |
| **Хронологія основних подій** | ⚪️ | 0 | Skipped |
| **Обговорення: Діалоги про пам'ять** | ✅ | 129 | Included in Core |
| **Деколонізаційний погляд** | ⚪️ | 314 | Skipped |
| **Граматика в контексті** | ✅ | 148 | Included in Core |
| **Підсумок** | ✅ | 112 | Included in Core |
| **Зовнішні ресурси** | ⚪️ | 0 | Skipped |
| **Активності** | ⚪️ | 6 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |