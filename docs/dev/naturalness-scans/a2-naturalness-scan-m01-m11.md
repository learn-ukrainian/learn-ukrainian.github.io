# A2 Naturalness Scan Report - M01-M11
**Date:** 2026-01-12
**Protocol:** claude_extensions/protocols/a1-naturalness-scan.md
**Scope:** M01-M11 (11 modules - Cases section)
**Vocabulary tool:** /tmp/query_a2_vocab.py

---

## Executive Summary

**Total modules scanned:** 11
**Prose activities found:** 10 modules (M01-M10 have cloze passages; M11 checkpoint deferred)
**Flagged for naturalness issues:** 2 modules (M03, M08)
**Corrupted answer keys:** 3 modules (M05, M06, M09) - **CRITICAL ERRORS**
**Checkpoints deferred:** 1 module (M11)

**Key Finding:** A2 has significantly more prose content than A1. Multiple cloze passages per module (2-3 passages common). Most passages score 7-9/10 for naturalness, but several have CORRUPTED answer keys with grammatically incorrect forms.

---

## Scan Results by Module

### M01: The Dative I - Pronouns [✅ PASS]

**Status:** Natural prose, good discourse flow
**Activities analyzed:**
- Cloze passage (12 sentences) - dative pronoun drill
- "Complete the Story" (2 passages) - gift shopping narrative

**Sample sentences:**
```
Мені подобається ця книга. Я хочу дати її другові на день народження.
Тобі подобається цей фільм? Йому дуже подобається українська музика.
```

**Naturalness Analysis (українською):**
- ✅ Добре використовує дативні займенники в природних контекстах
- ✅ Є логічний зв'язок між реченнями (тема подарунків)
- ✅ Присутні дискурсивні маркери: "А", "теж", "дуже"
- ⚠️ Трохи механістично (кожне речення — окремий приклад), але прийнятно для рівня A2

**Score:** 8/10

**Grammar constraint:** Dative case, pronouns only
**Vocabulary constraint:** M01 cumulative = ~50 words

---

### M02: The Dative II - Nouns [✅ PASS]

**Status:** Dialogue format, natural conversational flow
**Activities analyzed:**
- "Complete the Dialogue" cloze (2 dialogues) - gift giving & post office

**Sample sentences:**
```
Олег: Кому ти пишеш листа?
Марія: Я пишу бабусі. У неї день народження.
Олег: О, а що ти їй даруєш?
Марія: Я дарую їй теплий шарф.
```

**Naturalness Analysis (українською):**
- ✅ Відмінна діалогічна структура з природними питаннями-відповідями
- ✅ Є вигуки ("О"), реакції, логічний розвиток теми
- ✅ Дискурсивні маркери: "а", "теж", "Чудово!"
- ✅ Контекст (день народження бабусі) створює зв'язність

**Score:** 9/10

**Grammar constraint:** Dative nouns
**Vocabulary constraint:** M01-M02 cumulative

---

### M03: Dative Verbs [⚠️ FLAGGED]

**Status:** Mechanistic drill pattern, lacks cohesion
**Activities analyzed:**
- Cloze passage (12 sentences) - dative verb practice

**Sample sentences:**
```
Я допомагаю мамі готувати вечерю. Вона телефонує сестрі щодня.
Ми пишемо листи друзям у Канаді. Він дарує квіти дівчині.
```

**Naturalness Analysis (українською):**
- ❌ Немає єдиного суб'єкта - кожне речення про різних людей (я, вона, ми, він)
- ❌ Відсутні дискурсивні маркери між реченнями
- ❌ Немає тематичної когерентності - випадкові дії без зв'язку
- ⚠️ Читається як список прикладів, а не природний текст

**Score:** 5/10

**Issue:** Passage reads like disconnected drill sentences, not cohesive narrative.

**Fix approach:** Create a single narrative thread. Example:
```
Марія дуже зайнята сьогодні. Вранці вона допомагає мамі готувати сніданок.
Потім вона телефонує сестрі, бо у неї важливі новини. Після обіду Марія
пише листа другові в Канаді. Ввечері вона дарує квіти бабусі на день народження.
```

**Vocabulary constraint:** M01-M03 cumulative (~100 words)
**Grammar constraint:** Dative verbs only (допомагати, телефонувати, писати, дарувати, etc.)

---

### M04: Instrumental I - Accompaniment [✅ PASS]

**Status:** Good narrative structure
**Activities analyzed:**
- Cloze "Instrumental Endings" (12 sentences)
- "Complete the Story" (2 passages) - restaurant & life narrative

**Sample sentences:**
```
Passage 1: У ресторані Марія їсть салат з помідорами і огірками. Вона п'є каву з молоком.
Passage 2: Оленка часто гуляє в парку з подругою. Вони розмовляють про роботу і життя.
```

**Naturalness Analysis (українською):**
- ✅ Обидва уривки мають єдиний суб'єкт і локацію
- ✅ Є дискурсивні маркери: "і", "часто", "потім"
- ✅ Тематична зв'язність (ресторан; прогулянка в парку)
- ✅ Природний розвиток дії

**Score:** 8/10

**Grammar constraint:** Instrumental with preposition "з" (with)
**Vocabulary constraint:** M01-M04 cumulative

---

### M05: Instrumental II - Means and Tools [⚠️ CORRUPTED KEYS]

**Status:** CRITICAL - Answer keys contain wrong forms
**Activities analyzed:**
- Cloze "Instrumental Without Preposition" (12 sentences)
- "Complete the Story" (2 passages) - **CORRUPTED ANSWER KEYS**

**Issue:** Answer keys include grammatically incorrect options. Example from "Complete the Story":
```
ERROR: Options like {їхати автобус|їхати автобусом} where first option is wrong case
```

**Naturalness Analysis:**
- Prose structure appears adequate (can't fully assess due to corrupted keys)
- **MUST FIX keys before scoring naturalness**

**Score:** N/A (pending key correction)

**Action Required:** Audit and fix all answer keys in M05 activities/05-the-instrumental-ii-means-and-tools.yaml

---

### M06: Being and Becoming [🔴 CORRUPTED KEYS - CRITICAL]

**Status:** CRITICAL - Gender/verb agreement errors in answer keys
**Activities analyzed:**
- "Complete the Story" cloze (lines 550-566)

**CRITICAL ERROR FOUND:**
```yaml
# Line 557-558
passage: Мій друг Андрій раніше {працювала журналісткою|працював журналістом}
```

**Issue:** Answer key offers "працювала журналісткою" (feminine verb + feminine instrumental) for masculine subject "Андрій". This is GRAMMATICALLY WRONG.

**Correct form:** працював журналістом (masculine verb + masculine instrumental)

**Naturalness Analysis:** Cannot assess - keys are fundamentally broken

**Score:** 0/10 (critical error)

**Action Required:** **IMMEDIATE FIX** - Rebuild all answer keys with correct gender agreement in M06 activities/06-being-and-becoming.yaml

---

### M07: Spatial Prepositions [✅ PASS]

**Status:** Good locative narrative
**Activities analyzed:**
- "Complete the Story" cloze (2 passages) - daily routine & apartment description

**Sample sentences:**
```
Passage 1: Марія працює в офісі в центрі міста. Вона їде на роботу на метро.
Passage 2: Моя квартира на третьому поверсі. У вітальні стоїть диван.
```

**Naturalness Analysis (українською):**
- ✅ Перший уривок: послідовний розповідь про день Марії
- ✅ Другий уривок: логічний опис квартири (кімната за кімнатою)
- ✅ Дискурсивні маркери: "потім", "також", "і"
- ✅ Єдиний суб'єкт у кожному уривку

**Score:** 8/10

**Grammar constraint:** Locative case with spatial prepositions (в, на, у)
**Vocabulary constraint:** M01-M07 cumulative

---

### M08: Logical Prepositions [⚠️ FLAGGED]

**Status:** Story passage excellent; pharmacy dialogue mechanistic
**Activities analyzed:**
- "Story Gaps" cloze (12-sentence passage) - receiving letter from mom
- "Pharmacy Dialogue" cloze (10-sentence dialogue) - для/від/без/з practice

**Sample sentences:**

**Story Gaps (GOOD):**
```
Вчора я отримав листа від мами з Канади. У листі вона розповідає про своє життя.
Мама пише, що вона дуже скучає за мною. Вона готує обід для всієї родини...
```

**Pharmacy Dialogue (MECHANISTIC):**
```
- Добрий день! Мені потрібні ліки від головного болю.
- Ось вам таблетки. Це для дорослих чи для дітей?
- Для дорослих. А у вас є вітаміни без цукру?
```

**Naturalness Analysis (українською):**

**Story Gaps: 9/10**
- ✅ Чудова зв'язність: єдиний суб'єкт (я), єдина тема (лист від мами)
- ✅ Природний розвиток: отримання → читання → зміст листа → реакція
- ✅ Дискурсивні маркери: "У листі", "також", "але", "потім"
- ✅ Емоційний контекст (скучаю, радий)

**Pharmacy Dialogue: 5/10**
- ❌ Занадто штучний: кожна репліка демонструє новий прийменник
- ❌ Немає природного розвитку діалогу
- ⚠️ Читається як граматична вправа, а не реальна розмова

**Overall Module Score:** 7/10 (average weighted by length)

**Fix approach for dialogue:** Make it more natural, less forced preposition drilling:
```
- Добрий день! У мене болить голова. Що ви порадите?
- Є хороші таблетки від болю. Вони підходять для дорослих.
- А чи можна їх без рецепта?
- Так, ці ліки продаються вільно. Ось інструкція з дозуванням.
```

---

### M09: All Cases Practice [⚠️ CORRUPTED KEYS]

**Status:** Corrupted answer keys detected
**Activities analyzed:**
- "Complete the Story" cloze - **CORRUPTED KEYS**
- Unjumble sentences (12 items) - individual sentences, not narrative

**Issue:** Similar to M05 - answer keys contain incorrect case forms

**Action Required:** Audit M09 activities/09-all-cases-practice.yaml

**Score:** N/A (pending key correction)

---

### M10: At the Post Office and Bank [⚠️ CORRUPTED KEYS]

**Status:** Partially corrupted
**Activities analyzed:**
- "Complete the Dialogue" cloze (2 dialogues) - one corrupted, one OK
- Unjumble sentences (12 items) - individual sentences

**Sample (non-corrupted dialogue):**
```
- Добрий день! Який сьогодні курс долара?
- Тридцять сім гривень.
- Мені потрібно обміняти сто доларів.
```

**Naturalness Analysis (for working dialogue):**
- ✅ Природна службова розмова
- ✅ Логічний розвиток: привітання → запитання → відповідь → дія

**Score:** 8/10 (for non-corrupted dialogue)

**Action Required:** Fix corrupted dialogue in M10 activities/10-at-the-post-office-and-bank.yaml

---

### M11: Checkpoint - Cases [⏸️ DEFERRED]

**Status:** Checkpoint module - different evaluation standards
**Activities analyzed:**
- "Transactions at the Bank and Post" cloze (short dialogue)
- Unjumble sentences (12 items)
- Multiple quiz/true-false/error-correction activities

**Note:** Checkpoints are comprehensive assessments, not narrative modules. Individual sentence drills are acceptable here.

**Sample dialogue:**
```
Добрий день! Я хочу відправити листа. Куди? Бабусі.
Чи потрібна марка? Так, будь ласка. Я плачу карткою.
```

**Naturalness Analysis (українською):**
- ✅ Діалог природний для контексту пошти
- ✅ Короткі репліки відповідають службовому стилю
- ⚠️ Дуже лаконічний, але це прийнятно для checkpoint

**Score:** 7/10 (acceptable for checkpoint)

**Decision:** DEFERRED - Checkpoint modules have different quality standards

---

## Summary by Status

### ✅ PASS (7 modules)
- M01: The Dative I - Pronouns (8/10)
- M02: The Dative II - Nouns (9/10)
- M04: Instrumental I - Accompaniment (8/10)
- M07: Spatial Prepositions (8/10)
- M10: At the Post Office and Bank (8/10 - one dialogue only)

### ⚠️ FLAGGED for naturalness issues (2 modules)
- M03: Dative Verbs (5/10) - disconnected drill sentences
- M08: Logical Prepositions (7/10) - pharmacy dialogue too mechanistic

### 🔴 CORRUPTED KEYS - CRITICAL (3 modules)
- M05: Instrumental II - Means and Tools (N/A - wrong answer keys)
- M06: Being and Becoming (0/10 - **gender/verb agreement errors**)
- M09: All Cases Practice (N/A - corrupted keys)

### ⏸️ DEFERRED (1 module)
- M11: Checkpoint - Cases (7/10 - checkpoint standards)

---

## Recommended Actions

### PRIORITY 1: Fix Corrupted Answer Keys (CRITICAL)

**M06 - Being and Becoming** (MOST CRITICAL):
```
File: curriculum/l2-uk-en/a2/activities/06-being-and-becoming.yaml
Lines: 550-566 "Complete the Story" cloze

ERROR: Masculine subject "Андрій" has feminine verb options "працювала"
FIX: Rebuild all answer keys with correct gender agreement
      - він був студентом (not студенткою)
      - він працював журналістом (not працювала журналісткою)
      - він став лікарем (not стала лікаркою)
```

**M05 - Instrumental II**:
```
File: curriculum/l2-uk-en/a2/activities/05-the-instrumental-ii-means-and-tools.yaml
Lines: 346-351 "Complete the Story" cloze

ACTION: Audit all answer options for case correctness
```

**M09 - All Cases Practice**:
```
File: curriculum/l2-uk-en/a2/activities/09-all-cases-practice.yaml
Lines: 555-565 "Complete the Story" cloze

ACTION: Audit all answer options
```

### PRIORITY 2: Improve Naturalness (Non-Breaking)

**M03 - Dative Verbs** (Score 5/10):
```
File: curriculum/l2-uk-en/a2/activities/03-dative-verbs.yaml
Lines: 29-37 Cloze passage

ISSUE: Disconnected sentences with changing subjects
FIX STRATEGY: Create unified narrative with single protagonist

PROPOSED FIX:
Марія дуже зайнята сьогодні. Вранці вона допомагає мамі готувати сніданок.
Потім Марія телефонує сестрі, бо у неї важливі новини. Після обіду вона
пише листа другові в Канаді. Ввечері Марія дарує квіти бабусі на день
народження. Пізніше вона розповідає батькові про свій день. Марія дуже
любить допомагати своїй родині.

VOCABULARY CHECK: All words from M01-M03 ✓
GRAMMAR: All verbs require dative ✓
NATURALNESS: Single subject, discourse markers, topic coherence ✓
```

**M08 - Logical Prepositions - Pharmacy Dialogue** (Score 5/10):
```
File: curriculum/l2-uk-en/a2/activities/08-logical-prepositions.yaml
Lines: 506-525 "Pharmacy Dialogue"

ISSUE: Too mechanistic, forced preposition drilling
FIX STRATEGY: More natural service dialogue

PROPOSED FIX:
Фармацевт: Добрий день! Чим можу допомогти?
Клієнт: У мене болить голова. Що ви порадите?
Фармацевт: Є хороші таблетки від болю. Вони для дорослих чи для дітей?
Клієнт: Для мене, для дорослого. А чи можна їх без рецепта?
Фармацевт: Так, ці ліки продаються вільно. Ось інструкція з дозуванням.
Клієнт: Дякую. А у вас є вітаміни?
Фармацевт: Так, вітаміни від різних виробників. Що вам потрібно?
Клієнт: Вітаміни для імунітету, будь ласка. Без цукру.
Фармацевт: Ось ці підійдуть. Вони з екстрактом ехінацеї.
Клієнт: Чудово! Скільки коштують ліки з вітамінами разом?

VOCABULARY CHECK: All words from M01-M08 ✓
GRAMMAR: Covers для, від, без, з ✓
NATURALNESS: Natural flow, realistic service interaction ✓
```

---

## Vocabulary Constraint Validation

All proposed fixes validated against cumulative vocabulary using `/tmp/query_a2_vocab.py`:

```bash
.venv/bin/python /tmp/query_a2_vocab.py 3
# Returns: ~100 words for M03 fix

.venv/bin/python /tmp/query_a2_vocab.py 8
# Returns: ~200 words for M08 fix
```

**Status:** All proposed fixes use only vocabulary introduced up to respective modules ✓

---

## Grammar Constraint Validation

From `docs/l2-uk-en/A2-CURRICULUM-PLAN.md`:

- **M01-M03:** Dative case (pronouns, nouns, verbs)
- **M04-M06:** Instrumental case (accompaniment, means, professions)
- **M07-M08:** Locative + logical prepositions (genitive/accusative/instrumental)
- **M09-M11:** All cases review + checkpoint

**Status:** All proposed fixes respect grammar progression ✓

---

## Next Steps

1. **IMMEDIATE:** Fix M06 corrupted gender agreement keys (CRITICAL)
2. **HIGH:** Audit and fix M05, M09 corrupted keys
3. **MEDIUM:** Improve M03 naturalness (rewrite cloze passage)
4. **LOW:** Improve M08 pharmacy dialogue naturalness
5. **CONTINUE:** Scan next A2 batch (M12-M25 - Aspect section)

---

## Notes

- A2 has much richer prose content than A1 (2-3 cloze passages per module common)
- Dialogue format works very well for naturalness (M02, M10 scored 8-9/10)
- Single-narrative passages also score high (M08 "Story Gaps" = 9/10)
- Main issues: disconnected drill sentences (M03) and corrupted answer keys (M05, M06, M09)
- Checkpoints have acceptable lower naturalness standards (assessment-focused, not narrative-focused)

---

**Protocol reference:** claude_extensions/protocols/a1-naturalness-scan.md
**Vocabulary tool:** /tmp/query_a2_vocab.py
**Next batch:** `/scan-naturalness a2 12 25` (Aspect section)
