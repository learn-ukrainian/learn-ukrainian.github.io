# Audit Report: 141-slang-youth.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Sociolinguistics | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 141-slang-youth.yaml: Array validation: {'type': 'error-correction', 'title': 'Виправлення "дідового" сленгу', 'instruction': 'Знайдіть застарілий сленг, який вже не вживають, і замініть його на сучасний.', 'items': [{'sentence': 'Цей фільм просто [[бомба-ракета]].', 'error': 'бомба-ракета', 'answer': 'топчик', 'options': ['topchyk', 'bomba', 'klas', 'super'], 'explanation': "'Бомба-ракета' — це сленг 2000-х або старшого покоління. Молодь скаже 'топчик' або 'імба'."}, {'sentence': 'Привіт, [[медвед]].', 'error': 'медвед', 'answer': 'бро', 'options': ['bro', 'drug', 'chuvak', 'kent'], 'explanation': "'Медвед' (превед медвед) — це мем 2006 року. Зараз кажуть 'йо', 'бро' або просто 'привіт'."}, {'sentence': 'Це повний [[отстой]].', 'error': 'отстой', 'answer': 'крінж', 'options': ['krinzh', 'zashkvar', 'vidstij', 'bida'], 'explanation': "'Отстой' — русизм 90-х. Сучасні відповідники: 'крінж', 'треш', 'зашквар'."}, {'sentence': 'Я сиджу в [[асьці]].', 'error': 'асьці', 'answer': 'телеграмі', 'options': ['telehrami', 'insti', 'tiktoki', 'zumi'], 'explanation': "ICQ ('аська') померла. Всі сидять у Телеграмі, Інстаграмі або ТікТоці."}, {'sentence': 'Він реальний [[лох]].', 'error': 'лох', 'answer': 'нуб', 'options': ['nub', 'luser', 'bot', 'rak'], 'explanation': "'Лох' — кримінальний жаргон 90-х. Геймери скажуть 'нуб', 'бот' або 'рак'."}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2013/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 98.1% (target 90-100%)
- **Richness:** ✅ 97% (style)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 15 | 2 | 100% | 25% | 25.0% |
| model_answers | 36 | 3 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| register_analysis | 15 | 5 | 100% | 15% | 15.0% |
| visual | 3 | 4 | 75% | 10% | 7.5% |
| variety | 0.99 | - | 99% | 5% | 5.0% |
| cultural | 5 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 75 | Included in Core |
| **Вступ: Код покоління** | ⚪️ | 94 | Skipped |
| **Презентація первинних текстів** | ✅ | 205 | Included in Core |
| **Порівняльний аналіз** | ✅ | 98 | Included in Core |
| **Історія українського сленгу** | ⚪️ | 538 | Skipped |
| **Психологія сленгу: Чому ми так говоримо?** | ⚪️ | 267 | Skipped |
| **Сленг у музиці та поп-культурі** | ✅ | 102 | Included in Core |
| **Граматика сленгу** | ⚪️ | 161 | Skipped |
| **Соціокультурний аспект** | ✅ | 184 | Included in Core |
| **Фразеологія: Нові ідіоми** | ⚪️ | 38 | Skipped |
| **Письмо: Коментар у соцмережі** | ⚪️ | 115 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 54 | Skipped |
| **Підсумок** | ✅ | 82 | Included in Core |