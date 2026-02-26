# Audit Report: M80 — analiz-tekstu.md
**Level:** B2 | **Module:** M80 | **Phase:** B2.4 | **Pedagogy:** CBI | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-25 20:35:52

## Configuration
**Type:** B2-skills
**Word Target:** 4000 words
**Activities:** 14-18 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥5 types required
**Priority Types:** cloze, fill-in, quiz, translate
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[EUPHONY]** Line 251: «з червоними» — з перед з/с/ш/ч; має бути «із червоними»
  - FIX: Replace «з» with «із» (before sibilant)
- **[LLM_FINGERPRINT_REPETITION]** Repetitive LLM rhetorical patterns (12 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x5 — robotic prose
  - FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
- **[YAML_SCHEMA_VIOLATION]** Schema error in analiz-tekstu.yaml: Schema validation error at key '11': {'type': 'quiz', 'title': 'Практичний аналіз: Визначте стилістичний прийом', 'items': [{'question': 'Який стилістичний прийом використано у відомій фразі Світло правди завжди перемагає темряву брехні?', 'explanation': 'Світло та темрява, правда та брехня — це слова з протилежним значенням (антоніми).', 'options': [{'text': 'антоніми', 'correct': True}, {'text': 'еліпсис', 'correct': False}, {'text': 'вставні слова', 'correct': False}, {'text': 'термінологія', 'correct': False}]}, {'question': 'Що яскраво ілюструє поетична фраза Україно моя, ти для мене справжнє диво?', 'explanation': 'Це пряме риторичне звертання до абстрактного поняття або країни для підвищення емоцій.', 'options': [{'text': 'риторичне звертання', 'correct': True}, {'text': 'постколоніальну оптику', 'correct': False}, {'text': 'штучну хибну дихотомію', 'correct': False}, {'text': 'серйозну логічну хибу', 'correct': False}]}, {'question': 'До якого культурного архетипу належить стиль із розгалуженим синтаксисом та холодним аналізом?', 'explanation': 'Такий раціональний та структурний стиль характерний для архетипу Будівельника (Іван Франко).', 'options': [{'text': 'архетип Будівельника (Франко)', 'correct': True}, {'text': 'архетип Пророка (Шевченко)', 'correct': False}, {'text': 'архетип Воїна (Спаська)', 'correct': False}, {'text': 'архетип Мандрівника (Сковорода)', 'correct': False}]}, {'question': 'Якщо журналіст пише безжальна різанина робочих місць замість скорочення штату, що це таке?', 'explanation': 'Це інформаційна маніпуляція за допомогою використання слів, що викликають страх або паніку.', 'options': [{'text': 'емоційно заряджена лексика', 'correct': True}, {'text': "академічний об'єктивний аналіз", 'correct': False}, {'text': 'спокійний логічний висновок', 'correct': False}, {'text': 'прихована Езопова мова', 'correct': False}]}, {'question': 'Який засіб використовує автор, коли різко пише Я йду додому, а він швидко на роботу?', 'explanation': 'Пропуск дієслова йде у другій частині для динамізації тексту називається еліпсисом.', 'options': [{'text': 'еліпсис', 'correct': True}, {'text': 'епітет', 'correct': False}, {'text': 'метафору', 'correct': False}, {'text': 'алюзію', 'correct': False}]}, {'question': 'Яка додаткова інформація передається словом Борітеся поборете в сучасному публіцистичному тексті?', 'explanation': 'Це відома цитата з Тараса Шевченка, яка працює як глибока алюзія на спільний культурний код нації.', 'options': [{'text': 'інтертекстуальна алюзія', 'correct': True}, {'text': 'точний науковий термін', 'correct': False}, {'text': 'небезпечна хибна дихотомія', 'correct': False}, {'text': 'пряма агресивна маніпуляція', 'correct': False}]}, {'question': 'Якщо ви читаєте український вислів водити когось за ніс, як саме слід його аналізувати?', 'explanation': 'Це ідіома (фразеологізм), тому її категорично не можна сприймати чи перекладати буквально.', 'options': [{'text': 'як стійкий фразеологізм, що означає обманювати', 'correct': True}, {'text': 'як точний буквальний опис жорстокої фізичної дії', 'correct': False}, {'text': 'як надзвичайно складну філософську концепцію', 'correct': False}, {'text': 'як явний прояв глибокого постколоніального синдрому', 'correct': False}]}, {'question': 'Що найімовірніше вказує на ретельно приховану позицію автора в довгому художньому тексті?', 'explanation': 'Вибір специфічних епітетів (як позитивних, так і негативних) часто видає справжнє ставлення автора до свого героя.', 'options': [{'text': 'специфічний вибір епітетів для детального опису героя', 'correct': True}, {'text': 'часте використання стандартних розділових знаків', 'correct': False}, {'text': 'загальна фізична кількість надрукованих сторінок', 'correct': False}, {'text': 'стандартна наявність короткого вступу та висновків', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 30/100)

- 3 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 3549/4000 (raw: 3903)
- **Activities:** ❌ 0/14
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/5 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 5/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/20
- **Structure:** ✅ Valid Structure
- **Ipa:** ✅ Clean IPA
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 14-18)
- **Immersion:** 🇺🇦 98.3% (target 90-100% (skills))
- **Richness:** ✅ 96% (skills)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 96% (minimum: 80%)
**Module Type:** skills

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 86 | 15 | 100% | 26% | 25.5% |
| engagement | 4 | 5 | 80% | 19% | 15.5% |
| variety | 1.00 | - | 100% | 12% | 12.2% |
| cultural | 3 | - | 100% | 12% | 12.2% |
| realworld | 3 | 3 | 100% | 12% | 12.2% |
| visual | 6 | 2 | 100% | 6% | 6.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.1% |
| questions | 38 | 4 | 100% | 6% | 6.1% |
| **TOTAL** | | | | | **96.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Аналіз тексту** | ✅ | 74 | Included in Core |
| **Вступ та термінологічні засади** | ✅ | 813 | Included in Core |
| **Стилістичні засоби та синтаксис** | ✅ | 816 | Included in Core |
| **Авторська позиція та культурні архетипи** | ✅ | 652 | Included in Core |
| **Контекстуальний аналіз та деколонізація** | ✅ | 527 | Included in Core |
| **Логіка аргументації та запобігання помилкам** | ✅ | 493 | Included in Core |
| **Підсумок** | ✅ | 174 | Included in Core |