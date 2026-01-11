# Audit Report: 43-correlative-constructions.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** TTT | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 43-correlative-constructions.yaml: Array validation: {'type': 'translate', 'title': 'Оберіть правильний переклад', 'items': [{'source': 'The one who works hard always achieves success in life.', 'options': [{'text': 'Той, хто наполегливо працює, неодмінно досягає успіху в житті.', 'correct': True}, {'text': 'Той що працює досягає успіху.', 'correct': False}]}, {'source': 'That which is important should be remembered in your heart.', 'options': [{'text': "Те, що справді важливо, варто назавжди запам'ятати у своєму серці.", 'correct': True}, {'text': "Те що важливо варто запам'ятати.", 'correct': False}]}, {'source': 'Where it is quiet, one always thinks well about the future.', 'options': [{'text': 'Там, де панує тиша, завжди дуже добре думається про майбутнє.', 'correct': True}, {'text': 'Там де тихо добре думається.', 'correct': False}]}, {'source': 'When the time comes, you will surely understand everything.', 'options': [{'text': 'Тоді, коли нарешті настане слушний час, ти все обов’язково зрозумієш.', 'correct': True}, {'text': 'Тоді коли настане час ти зрозумієш.', 'correct': False}]}, {'source': 'Take as much as you really need for your work today.', 'options': [{'text': 'Візьми собі стільки, скільки тобі справді потрібно для роботи сьогодні.', 'correct': True}, {'text': 'Візьми стільки скільки потрібно.', 'correct': False}]}, {'source': 'Go where your heart leads you without any hesitation.', 'options': [{'text': 'Іди туди, куди твоє серце тебе кличе без жодних вагань.', 'correct': True}, {'text': 'Іди туди де серце веде.', 'correct': False}]}, {'source': 'Help those who really need it most at this moment.', 'options': [{'text': 'Допоможи тому, хто цього справді найбільше потребує у цей момент.', 'correct': True}, {'text': 'Допоможи тому хто потребує.', 'correct': False}]}, {'source': 'I respect the one who always remains honest with themselves.', 'options': [{'text': 'Я поважаю того, хто завжди залишається чесним із самим собою.', 'correct': True}, {'text': 'Я поважаю той, хто чесний.', 'correct': False}]}, {'source': 'We received such a result as we expected from our team.', 'options': [{'text': 'Ми нарешті отримали такий результат, якого ми так довго очікували.', 'correct': True}, {'text': 'Такий результат що ми очікували.', 'correct': False}]}, {'source': 'I will wait until you finally come to our meeting place.', 'options': [{'text': 'Я буду чекатиму доти, поки ти нарешті не прийдеш на наше місце.', 'correct': True}, {'text': 'Чекатиму доти поки не прийдеш.', 'correct': False}]}, {'source': 'Do it the way you know and can do it best.', 'options': [{'text': 'Роби свою справу саме так, як ти знаєш і вмієш найкраще.', 'correct': True}, {'text': 'Роби так як знаєш.', 'correct': False}]}, {'source': 'From where the wind blows, from there comes cold rain.', 'options': [{'text': 'Звідти, звідки дме вітер, звідти зазвичай і приходить холодний дощ.', 'correct': True}, {'text': 'Звідти звідки вітер звідти й дощ.', 'correct': False}]}], 'instruction': 'Оберіть найбільш точний та граматично правильний переклад речення на українську мову.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 43-correlative-constructions.yaml: [index-1] cloze: passage contains blank lines (\n\n) which break MDX rendering. Use single newlines only.
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 43-correlative-constructions.yaml: [index-6] unjumble: 'items.11' - 'answer' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 43-correlative-constructions.yaml: [index-8] translate: 'items.11.options' - [{'text': 'Звідти, звідки дме вітер, звідти зазвичай і приходить холодний дощ.', 'correct': True}, {'text': 'Звідти звідки вітер звідти й дощ.', 'correct': False}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: grammar) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1894/1750
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 11/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 53/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 90-100% (grammar))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 95 | 24 | 100% | 20% | 20.0% |
| engagement | 12 | 5 | 100% | 15% | 15.0% |
| dialogues | 17 | 4 | 100% | 15% | 15.0% |
| variety | 0.92 | - | 92% | 10% | 9.2% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 3 | 3 | 100% | 10% | 10.0% |
| visual | 14 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 14 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ⚪️ | 56 | Skipped |
| **Тест: Прочитайте текст** | ✅ | 210 | Included in Core |
| **Пояснення** | ⚪️ | 751 | Skipped |
| **Трансформації** | ⚪️ | 83 | Skipped |
| **Практика** | ⚪️ | 275 | Skipped |
| **Діалоги** | ✅ | 260 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Ключові моменти** | ⚪️ | 75 | Skipped |
| **Самооцінка** | ⚪️ | 74 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |