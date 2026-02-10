# Phase Fix: Apply Review Fix Plan

> **You are Gemini, executing the Fix phase of an orchestrated rebuild.**
> **Your ONLY task: Apply every fix from the review's Fix Plan. Output complete fixed files.**
> **Do NOT add, remove, or change anything beyond what the Fix Plan specifies.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
# Рецензія: Checkpoint — Full Grammar

**Level:** A2 | **Module:** 56
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] All sections present and aligned with outline.
- Vocabulary: [PASS] Core A2 vocabulary reviewed appropriately.
- Grammar scope: [PASS] Focuses on A2 concepts (cases, aspect) without significant scope creep.
- Objectives: [PASS] Integration challenge effectively tests learning objectives.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Well-structured checkpoint with clear logical flow. |
| 2 | Coherence | 9/10 | <7 | Concepts connect well; history bite adds nice context. |
| 3 | Relevance | 10/10 | <7 | Highly relevant practical skills (shopping, health). |
| 4 | Educational | 8/10 | <7 | Generally good, but teaches incorrect Genitive form for "магазин". |
| 5 | Language | 8/10 | <8 | "До кухні" is less natural than "на кухню"; otherwise solid. |
| 6 | Pedagogy | 8/10 | <7 | Effective TTT approach, marred by broken activity logic. |
| 7 | Immersion | 9/10 | <6 | Good balance of Ukrainian examples and English guidance. |
| 8 | Activities | 6/10 | <7 | **FAIL**: One item enforces wrong grammar; another has double errors making correction ambiguous. |
| 9 | Richness | 9/10 | <6 | Good variety of exercise types and cultural notes. |
| 10 | Beginner Safety | 8/10 | <7 | Confusing error correction tasks lower the safety score. |
| 11 | LLM Fingerprint | 9/10 | <7 | Content feels curated and structured, not hallucinated. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **FAIL**: Explicitly identifies standard form "магазина" as an error. |

**Weighted Overall:** 8.2/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** Items in `error-correction` are factually or logically flawed.
- Beginner safety: 4/5 (Confusion in activities)

## Critical Issues Found

### Issue 1: Incorrect Genitive Form Enforced
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: error-correction` / Item 1
- **Original**: `sentence: Я йду до магазина.`, `error: магазина`, `answer: магазину`, `explanation: Genitive of магазин is магазину (masculine -ин → -у).`
- **Problem**: This is linguistically incorrect. According to *Ukrainian Orthography 2019 (§ 82.2)* and academic dictionaries (SUM-11), nouns denoting buildings/structures like "магазин" take the **-а** ending in Genitive singular ("магазина"). While "-у" is sometimes used for the institution in spoken language, marking the standard "-а" form as an **error** is unacceptable.
- **Fix**: Replace the sentence with a noun that definitely takes **-у** (abstract/space) to teach the rule safely, e.g., "театр" -> "театру" or "парк" -> "парку".

### Issue 2: Double Error in Single-Correction Task
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: error-correction` / Item 3
- **Original**: `sentence: Я купила новий сумка.`
- **Problem**: This sentence contains **two** errors: adjective agreement ("новий" vs "нова/нову") AND noun case ("сумка" vs "сумку"). The task implies finding ONE error. If the student fixes only the adjective to "новую", the sentence is still wrong ("Я купила нову сумка"). If they fix only the noun, it is still wrong. This is confusing and pedagogically broken.
- **Fix**: Provide a sentence with ONLY one error. Example: "Я люблю слухати музика." (Error: музика -> музику).

### Issue 3: Unnatural Preposition Usage
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: mark-the-words` / `text`
- **Original**: `...і йду до кухні, щоб снідати.`
- **Problem**: "Йти до кухні" implies walking up to the kitchen (limit/direction) but not necessarily entering/using it. The standard idiomatic phrase for going to the kitchen to eat/cook is **"йти на кухню"** (similar to "на балкон", "на вулицю").
- **Fix**: Change "до кухні" to "на кухню".

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Fail (The error correction tasks might confuse attentive students)
- Come back tomorrow? Pass

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 10/10
**What to fix:**
1.  **Activity YAML (`error-correction`, Item 1)**:
    *   Change `sentence: Я йду до магазина.` → `sentence: Я йду до парк.`
    *   Change `error: магазина` → `error: парк`
    *   Change `answer: магазину` → `answer: парку`
    *   Change explanation to: `Genitive of парк is парку (spatial concept -у).`
    *   *Reasoning*: "Парку" is the undisputed standard Genitive form, avoiding the specific building exception of "магазин".

### Activities: 6/10 → 10/10
**What to fix:**
1.  **Activity YAML (`error-correction`, Item 3)**:
    *   Change `sentence: Я купила новий сумка.` → `sentence: Я люблю слухати музика.`
    *   Change `error: новий` → `error: музика`
    *   Change `answer: нову` → `answer: музику`
    *   Change `options` to `[музику, музика, музики, музикою]`
    *   Change `explanation` to: `Accusative case is required for the object (музика → музику).`
    *   *Reasoning*: Creates a clean single-variable problem.

### Language: 8/10 → 9/10
**What to fix:**
1.  **Activity YAML (`mark-the-words`)**:
    *   Change `...і йду до кухні...` → `...і йду на кухню...`
    *   *Reasoning*: Uses the most natural idiomatic preposition for this context.

### Projected Overall After Fixes
**(9*1.5 + 9*1 + 10*1 + 9*1.2 + 9*1.1 + 9*1.2 + 9*1 + 10*1.3 + 9*0.9 + 9*1.3 + 9*1 + 10*1.5) / 14 = 9.35/10**

## Verification Summary

- Content lines read: ~140
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: N/A (Vocab list only)
- Issues found: 3 (2 Critical, 1 Naturalness)
- Naturalness score recommendation: 9/10 (after fix)

## Verdict

**FAIL**

The module is well-structured and engaging but fails on Linguistic Accuracy and Activity Logic. It teaches a standard Genitive form ("магазина") as an error, which is factually incorrect per academic norms, and presents a "find the error" task with multiple simultaneous errors. These must be fixed to ensure the checkpoint is pedagogically safe.
```

**Current content** (the file you are fixing):
```
# Checkpoint: Full Grammar (Повна граматика)

## Огляд

**Вітаємо!** You've completed all A2 core grammar modules (M01-55)!
This checkpoint confirms your grammar readiness before Phase A2.6 practical scenarios (M57-70).

> **Note:** This is NOT the final A2 assessment. The cumulative final exam is M70.

**Skills tested:**

1. **Daily Life** - Can you talk about home, routines, and hobbies?
2. **Work & Education** - Can you describe jobs and studies?
3. **Health & Body** - Can you discuss health and symptoms?
4. **Shopping & Travel** - Can you handle transactions and trips?

## Skill 1: Daily Life

**Can you talk about home, routines, and hobbies?**

### Model: Home & Routine Vocabulary

> **Квартира** — apartment, **вітальня** — living room, **кухня** — kitchen
> **Прокидатися** — to wake up, **снідати** — to have breakfast
> **Вечеряти** — to have dinner, **засинати** — to fall asleep

**Daily routine verbs:**

| Verb | Meaning |
|------|---------|
| прокидатися | to wake up |
| вмиватися | to wash face |
| одягатися | to get dressed |
| снідати | to have breakfast |
| обідати | to have lunch |
| вечеряти | to have dinner |

**Hobby vocabulary:**

- подорожувати — to travel
- малювати — to draw
- грати в футбол — to play football
- читати книги — to read books

### Practice: Complete the Routine

1. Вранці я \_\_\_ о 7:00.

   > [!solution] Перевірити
   > прокидаюся — reflexive verb for waking up

2. Потім я \_\_\_ і йду на роботу.

   > [!solution] Перевірити
   > снідаю — breakfast verb

3. Ввечері я люблю \_\_\_ книги.
   > [!solution] Перевірити
   > читати — reading as a hobby

### Self-Check

- Can you describe your morning routine in Ukrainian?
- Do you know room names: кухня, спальня, вітальня, ванна?
- Can you talk about hobbies: подорожувати, малювати, грати?

> [!myth-buster] 🔍 Myth Buster
>
> **Myth:** «Ukrainian daily vocabulary is just like Russian.»
>
> **Truth:** While some words overlap due to shared Slavic origins, Ukrainian has unique daily vocabulary. For example, **вітальня**, **снідати**, and **вечеряти** (dinner) showcase Ukrainian's distinct lexicon!

> [!history-bite] 📜 History Bite
>
> **Home vocabulary survived!** During Russification, Ukrainian families preserved household words orally. Words like **хата**, **світлиця**, and **горище** (attic) remained in use for generations, keeping Ukrainian alive in the home.

---

## Skill 2: Work & Education

**Can you describe jobs and studies?**

### Model: Professional Vocabulary

> **Працювати** + Instrumental = what you work AS
> Він працює **лікарем**. (He works as a doctor.)
> Вона працює **вчителькою**. (She works as a teacher.)

**Key professions:**

| Ukrainian | English |
|-----------|---------|
| лікар | doctor |
| вчитель | teacher |
| програміст | programmer |
| менеджер | manager |
| інженер | engineer |

**Education vocabulary:**

- університет — university
- школа — school
- студент — student
- вчитися — to study
- вивчати — to learn (subject)

### Practice: Work & Study

1. Він \_\_\_ програмістом.

   > [!solution] Перевірити
   > працює — work + instrumental

2. Вона \_\_\_ в університеті.

   > [!solution] Перевірити
   > вчиться — to study as a student

3. Я \_\_\_ українську мову.
   > [!solution] Перевірити
   > вивчаю — to learn a subject

### Self-Check

- Can you use «працювати + Instrumental» for professions?
- Do you know the difference: вчитися vs вивчати?
- Can you name 5 professions in Ukrainian?

> [!tip] 🎯 Pro Tip: Profession Formula
>
> **Працювати + Instrumental** is the key formula!
>
> - Працювати + **лікарем** = work as a doctor
> - Працювати + **вчителькою** = work as a teacher
> - Працювати + **програмістом** = work as a programmer
>
> Never use Nominative after «працювати»!

---

## Skill 3: Health & Body

**Can you discuss health and symptoms?**

### Model: Health Expressions

> **У мене болить голова.** (My head hurts.)
> **Я застудився.** (I caught a cold.)
> **Мені погано.** (I feel bad.)

**Body parts:**

| Ukrainian | English |
|-----------|---------|
| голова | head |
| горло | throat |
| живіт | stomach |
| рука | arm/hand |
| нога | leg/foot |

**At the doctor:**

- лікар — doctor
- аптека — pharmacy
- ліки — medicine
- температура — temperature
- застуда — cold

### Practice: At the Doctor

1. У мене болить \_\_\_.

   > [!solution] Перевірити
   > голова — body part in NOMINATIVE (it's the subject doing the hurting)

2. Яка у вас \_\_\_?

   > [!solution] Перевірити
   > температура — asking about fever

3. Де тут \_\_\_? (pharmacy)
   > [!solution] Перевірити
   > аптека — location for medicine

### Self-Check

- Can you say «something hurts» using «У мене болить...»?
- Do you know body parts: голова, горло, рука, нога?
- Can you describe symptoms and ask for medicine?

> [!note] 📝 Health Expression Patterns
>
> **Pattern 1:** У мене болить + NOMINATIVE
>
> - У мене болить **голова** (NOT голову!)
>
> **Pattern 2:** Мені + ADVERB
>
> - Мені **погано**
> - Мені **холодно** (I'm cold)
>
> **Pattern 3:** Я + VERB
>
> - Я **застудився**

---

## Skill 4: Shopping & Travel

**Can you handle transactions and travel?**

### Model: Shopping Expressions

> **Скільки це коштує?** (How much is this?)
> **Можна заплатити карткою?** (Can I pay by card?)
> **Чи є знижка?** (Is there a discount?)

**Shopping vocabulary:**

| Ukrainian | English |
|-----------|---------|
| гроші | money |
| картка | card |
| готівка | cash |
| чек | receipt |
| знижка | discount |

**Travel vocabulary:**

- подорож — trip
- квиток — ticket
- поїзд — train
- літак — plane
- готель — hotel

### Practice: Shopping & Travel

1. Скільки це \_\_\_?

   > [!solution] Перевірити
   > коштує — asking price

2. Можна заплатити \_\_\_?

   > [!solution] Перевірити
   > карткою — instrumental for payment method

3. Я хочу купити \_\_\_ на поїзд.
   > [!solution] Перевірити
   > квиток — train ticket

### Self-Check

- Can you ask prices and pay in Ukrainian?
- Do you know: гроші, картка, чек, знижка?
- Can you book travel: квиток, поїзд, готель, літак?

> [!warning] ⚠️ Common Shopping Mistake
>
> Don't say: «Скільки це коштує»
> Say: «Скільки це коштує?» with rising intonation!
>
> Also: «Можна заплатити **карткою**?» (Instrumental!) NOT «картку»!

---

## Integration Challenge

Read the story and answer the questions:

> Олег живе у Києві. Він працює **програмістом** в IT-компанії.
> Вранці він **прокидається** о 8:00, снідає і їде на роботу.
> Вчора у нього боліла **голова**. Він пішов до **лікаря**.
> Лікар сказав, що це застуда, і треба пити чай.
> У вихідні Олег хоче поїхати в **подорож** до Карпат.
> Він вже купив **квитки** на поїзд і забронював **готель**.

1. Ким працює Олег?

   > [!solution] Перевірити
   > Програмістом — profession in instrumental

2. Що у нього боліло?

   > [!solution] Перевірити
   > Голова — head

3. Куди він хоче поїхати?

   > [!solution] Перевірити
   > У Карпати — to the Carpathians

4. Що він купив?
   > [!solution] Перевірити
   > Квитки — tickets

# Підсумок

| Skill           | Key Pattern         | Example               |
| --------------- | ------------------- | --------------------- |
| Daily Life      | Routine verbs       | прокидатися, снідати  |
| Work/Education  | працювати + Instr   | працює лікарем        |
| Health          | У мене болить + Nom | болить голова         |
| Shopping/Travel | Transaction vocab   | квиток, гроші, картка |

> 💡 **Успіхи!**
>
> Ви закінчили рівень A2! Тепер ви можете говорити про щоденне життя, роботу, здоров'я і подорожі.
> *You finished A2 level! Now you can talk about daily life, work, health, and travel.*

---

---

## Need More Practice?

To solidify your knowledge, try writing five sentences using the grammar patterns from this module. Use the vocabulary items provided in the sidecar to practice your new words in context!

```

**Current activities** (fix if review mentions activity issues):
```
- type: match-up
  title: Vocabulary Categories
  pairs:
  - left: квартира
    right: Daily Life
  - left: вітальня
    right: Daily Life
  - left: лікар
    right: Work
  - left: програміст
    right: Work
  - left: голова
    right: Health
  - left: горло
    right: Health
  - left: гроші
    right: Shopping
  - left: квиток
    right: Travel
  - left: прокидатися
    right: Daily Life
  - left: вчитися
    right: Education
  - left: температура
    right: Health
  - left: знижка
    right: Shopping
  instruction: З'єднайте відповідні елементи.
- type: cloze
  title: Vocabulary Test
  passage: 'Вранці я {прокидаюся|засинаю|сплю} о 7:00. Він працює {лікарем|лікар|лікаря}.
    У мене болить {голова|голову|голові}. (head)

    Скільки це {коштує|коштувати|коштував}? (costs) Можна заплатити {карткою|картку|картка}?
    Я хочу купити {квиток|квитка|квитку}. (ticket)

    Вона {вчиться|вчить|вче} в університеті. (studies) Я {вивчаю|вчуся|вивчити} українську
    мову. (learn) Де тут {аптека|аптеку|аптеці}? (pharmacy)

    Яка у вас {температура|температуру|температурі}? Він живе у великому {місті|місто|місту}.
    (city-LOC) Ввечері я йду в {спортзал|спортзалі|спортзалу}. (gym-ACC)'
  instruction: Заповніть пропуски, обравши правильні слова.
- type: quiz
  title: A2 Vocabulary Quiz
  items:
  - question: What is the meaning of the reflexive verb «прокидатися» in English?
    options:
    - text: To wake up
      correct: true
    - text: To fall asleep
      correct: false
    - text: To eat breakfast
      correct: false
    - text: To get dressed
      correct: false
  - question: Which grammatical case is used in the phrase «працювати лікарем»?
    options:
    - text: Instrumental case
      correct: true
    - text: Accusative case
      correct: false
    - text: Nominative case
      correct: false
    - text: Genitive case
      correct: false
  - question: In the phrase «У мене болить голова», what is the grammatical role of
      «голова»?
    options:
    - text: Nominative (subject)
      correct: true
    - text: Accusative (object)
      correct: false
    - text: Genitive
      correct: false
    - text: Dative
      correct: false
  - question: In the phrase «Заплатити карткою», what case is «карткою» in?
    options:
    - text: Instrumental (means)
      correct: true
    - text: Accusative
      correct: false
    - text: Dative
      correct: false
    - text: Locative
      correct: false
  - question: What is the primary meaning of the verb «вчитися» in an educational
      context?
    options:
    - text: To study
      correct: true
    - text: To teach a class
      correct: false
    - text: To learn a subject
      correct: false
    - text: To read a book
      correct: false
  - question: What does the verb «вивчати» specifically mean when talking about education?
    options:
    - text: To learn
      correct: true
    - text: To be a student
      correct: false
    - text: To teach
      correct: false
    - text: To write
      correct: false
  - question: What is the English translation of the travel word «квиток»?
    options:
    - text: Ticket
      correct: true
    - text: Key
      correct: false
    - text: Bag
      correct: false
    - text: Map
      correct: false
  - question: What does the shopping word «знижка» mean in a store?
    options:
    - text: Discount
      correct: true
    - text: Receipt
      correct: false
    - text: Price
      correct: false
    - text: Change
      correct: false
  - question: What part of the body is «горло» in English?
    options:
    - text: Throat
      correct: true
    - text: Head
      correct: false
    - text: Leg
      correct: false
    - text: Arm
      correct: false
  - question: What is the correct translation for the word «подорож»?
    options:
    - text: Trip/journey
      correct: true
    - text: Work/job
      correct: false
    - text: Food/meal
      correct: false
    - text: Rest/sleep
      correct: false
  - question: What kind of establishment is a «готель» for travelers?
    options:
    - text: Hotel
      correct: true
    - text: House
      correct: false
    - text: Restaurant
      correct: false
    - text: Hospital
      correct: false
  - question: Which room in the house is called «вітальня» in Ukrainian?
    options:
    - text: Living room
      correct: true
    - text: Bedroom
      correct: false
    - text: Kitchen
      correct: false
    - text: Bathroom
      correct: false
  instruction: Оберіть правильну відповідь.
- type: group-sort
  title: Vocabulary Domains
  groups:
  - name: Daily Life
    items:
    - квартира
    - вітальня
    - прокидатися
    - снідати
  - name: Work & Education
    items:
    - лікар
    - програміст
    - вчитися
    - університет
  - name: Health
    items:
    - голова
    - горло
    - температура
    - аптека
  - name: Shopping & Travel
    items:
    - гроші
    - квиток
    - готель
    - знижка
  instruction: Розподіліть елементи за групами.
- type: true-false
  title: Vocabulary Rules
  items:
  - statement: «Працювати + Instrumental» describes profession.
    correct: true
    explanation: Correct! Працювати лікарем.
  - statement: «У мене болить» = my... hurts.
    correct: true
    explanation: Yes! У мене болить голова.
  - statement: «Голову» is correct after «болить».
    correct: false
    explanation: No! «Голова» — it's the subject.
  - statement: «Вчитися» = to be a student.
    correct: true
    explanation: Correct! Вона вчиться в університеті.
  - statement: «Вивчати» = to learn a subject.
    correct: true
    explanation: Yes! Я вивчаю українську.
  - statement: «Картка» in Instrumental is «картку».
    correct: false
    explanation: No! Instrumental is «карткою».
  - statement: «Знижка» means discount.
    correct: true
    explanation: Correct!
  - statement: Reflexive verbs end in "-ся".
    correct: true
    explanation: Yes! Прокидатися, вмиватися.
  - statement: «Квиток» and «готель» are health vocabulary.
    correct: false
    explanation: No! They are travel vocabulary.
  - statement: «Скільки це коштує?» asks the price.
    correct: true
    explanation: Correct!
  - statement: «Поїзд» means train.
    correct: true
    explanation: Yes!
  - statement: «Вітальня» is the kitchen.
    correct: false
    explanation: No! Вітальня = living room, кухня = kitchen.
  instruction: Визначте, чи твердження правильне.
- type: cloze
  title: A Day in Life
  passage: 'Вранці я {прокидаюся|засинаю|сплю} о 7:00.

    Потім я {снідаю|вечеряю|сплю} і йду на роботу.

    Я працюю {менеджером|менеджер|менеджера} в офісі.

    Вчора у мене боліла {голова|голову|голові}.

    Я пішов до {аптеки|аптека|аптеку} і купив ліки.

    У вихідні я хочу поїхати в {подорож|роботу|аптеку}.

    Я вже купив {квитки|квиток|квитку} на поїзд.

    Я забронював {готель|парк|вокзал} у центрі.

    Там я буду {гуляти|працювати|хворіти} і відпочивати.

    Ввечері я піду в {ресторан|магазин|банк} на вечерю.

    Я люблю {вивчати|забувати|втрачати} нові місця.

    Це буде чудова {поїздка|робота|хвороба}!'
  instruction: Заповніть пропуски, обравши правильні слова.
- type: unjumble
  title: Daily Routines
  items:
  - words:
    - Вранці
    - я
    - завжди
    - прокидаюся
    - дуже
    - рано
    - о
    - сьомій
    answer: Вранці я завжди прокидаюся дуже рано о сьомій
  - words:
    - Мій
    - старший
    - брат
    - зараз
    - успішно
    - працює
    - програмістом
    answer: Мій старший брат зараз успішно працює програмістом
  - words:
    - Сьогодні
    - у
    - мене
    - дуже
    - сильно
    - болить
    - голова
    answer: Сьогодні у мене дуже сильно болить голова
  - words:
    - Скажіть
    - будь ласка
    - чи
    - можна
    - тут
    - заплатити
    - карткою
    answer: Скажіть будь ласка чи можна тут заплатити карткою
  - words:
    - Вона
    - зараз
    - дуже
    - старанно
    - вчиться
    - в
    - національному
    - університеті
    answer: Вона зараз дуже старанно вчиться в національному університеті
  - words:
    - Вибачте
    - скажіть
    - де
    - тут
    - є
    - найближча
    - аптека
    answer: Вибачте скажіть де тут є найближча аптека
  instruction: Розташуйте слова у правильному порядку.
- type: mark-the-words
  title: Find the Vocabulary
  text: Вранці я прокидаюся о 7:00 і йду на кухню, щоб снідати. --- Моя сестра працює
    лікаркою. Вона вчилася в університеті 6 років. --- У мене болить голова і горло.
    Де тут аптека?
  answers:
  - прокидаюся
  - кухню
  - снідати
  - працює
  - лікаркою
  - вчилася
  - університеті
  - голова
  - горло
  - аптека
  instruction: Клацніть на слова, що відповідають критерію.
- type: translate
  title: English to Ukrainian
  items:
  - source: I wake up at 7:00.
    options:
    - text: Я прокидаюся о сьомій годині.
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  - source: He works as a programmer.
    options:
    - text: Він працює програмістом.
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  - source: My head hurts.
    options:
    - text: У мене болить голова.
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  - source: I want to buy a ticket.
    options:
    - text: Я хочу купити квиток.
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  - source: She studies at the university.
    options:
    - text: Вона вчиться в університеті.
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  - source: Can I pay by card?
    options:
    - text: Можна заплатити карткою?
      correct: true
    - text: Неправильно
      correct: false
    - text: Інший варіант
      correct: false
  instruction: Оберіть правильний переклад.
- type: translate
  title: Vocabulary Review Translation
  items:
  - source: Kitchen
    options:
    - text: Кухня
      correct: true
    - text: Кімната
      correct: false
    - text: Коридор
      correct: false
  - source: Weather
    options:
    - text: Погода
      correct: true
    - text: Природа
      correct: false
    - text: Пора
      correct: false
  - source: To cook
    options:
    - text: Готувати
      correct: true
    - text: Варити
      correct: false
    - text: Смажити
      correct: false
  - source: Mountain
    options:
    - text: Гора
      correct: true
    - text: Долина
      correct: false
    - text: Ріка
      correct: false
  - source: Summer
    options:
    - text: Літо
      correct: true
    - text: Зима
      correct: false
    - text: Весна
      correct: false
  - source: Furniture
    options:
    - text: Меблі
      correct: true
    - text: Одяг
      correct: false
    - text: Посуд
      correct: false
  instruction: Оберіть правильний переклад.
- type: error-correction
  title: Grammar Errors
  items:
  - sentence: Я йду до парк.
    error: парк
    answer: парку
    options:
    - парку
    - парк
    - парка
    - парком
    explanation: Genitive of парк is парку (spatial concept -у).
  - sentence: Вона читає книга.
    error: книга
    answer: книгу
    options:
    - книгу
    - книга
    - книги
    - книгою
    explanation: Accusative feminine -а → -у.
  - sentence: Я люблю слухати музика.
    error: музика
    answer: музику
    options:
    - музику
    - музика
    - музики
    - музикою
    explanation: Accusative case is required for the object (музика → музику).
  - sentence: Він працюють у банку.
    error: працюють
    answer: працює
    options:
    - працює
    - працюють
    - працюємо
    - працюєш
    explanation: Third person singular needs -є ending.
  - sentence: Ми їхали до Львова вчора.
    error: їхали
    answer: поїхали
    options:
    - поїхали
    - їхали
    - їдемо
    - їздили
    explanation: Single completed action requires perfective поїхали.
  - sentence: Діти грають на футбол.
    error: на
    answer: у
    options:
    - у
    - на
    - в
    - до
    explanation: Play football = грати у/в футбол.
  instruction: Знайдіть і виправте помилку в реченні.
- type: fill-in
  title: Grammar Fill-In
  instruction: Заповніть пропуски правильним словом.
  items:
  - sentence: Я іду [___] роботу.
    answer: на
    options:
    - на
    - до
    - в
    - від
  - sentence: Вона живе [___] Києві.
    answer: у
    options:
    - у
    - на
    - до
    - від
  - sentence: Він [___] українську мову щодня.
    answer: вивчає
    options:
    - вивчає
    - вчиться
    - навчає
    - вивчати
  - sentence: Ми [___] в кіно вчора ввечері.
    answer: ходили
    options:
    - ходили
    - ходимо
    - йшли
    - піти
  - sentence: Мені [___] допомога.
    answer: потрібна
    options:
    - потрібна
    - потрібно
    - потрібні
    - потрібний
  - sentence: Вони [___] на концерт наступної суботи.
    answer: підуть
    options:
    - підуть
    - йдуть
    - ходять
    - піти
  - sentence: Я [___] каву без цукру.
    answer: п'ю
    options:
    - п'ю
    - їм
    - пити
    - випити
  - sentence: Студенти [___] іспит завтра.
    answer: складатимуть
    options:
    - складатимуть
    - склали
    - складають
    - здавати

```

**Current vocabulary** (fix if review mentions vocabulary issues):
```
---
module: 56-checkpoint-full-grammar
level: A2
version: '2.0'
items:
- lemma: горище
  ipa: /ɦɔrˈɪʃt͡ʃɛ/
  translation: attic
  pos: noun
  gender: n
- lemma: світлиця
  ipa: /sʋitlˈɪt͡sja/
  translation: living room (traditional), light room
  pos: noun
  gender: f

```

**Plan file** (source of truth for scope — check if fixes align):
```
module: a2-56
level: A2
sequence: 56
slug: checkpoint-full-grammar
version: '2.0'
title: Checkpoint — Full Grammar
subtitle: A2 Mastery Review
content_outline:
- section: Огляд
  words: 100
  points:
  - Overview of checkpoint
  - Self-assessment focus
- section: 'Skill 1: Daily Life'
  words: 241
  points:
  - Daily life vocabulary review
  - Practical situations
- section: 'Skill 2: Work & Education'
  words: 160
  points:
  - Work and education vocabulary
  - Professional situations
- section: 'Skill 3: Health & Body'
  words: 167
  points:
  - Health vocabulary review
  - Body and wellness
- section: 'Skill 4: Shopping & Travel'
  words: 148
  points:
  - Shopping and travel vocabulary
  - Practical transactions
- section: Integration Challenge
  words: 111
  points:
  - Comprehensive assessment
  - Mixed skills practice
- section: Підсумок
  words: 73
  points:
  - Summary and next steps
word_target: 1000
vocabulary_hints:
  required:
  - повторення (review)
  - відмінок (case)
  - дієслово (verb)
  - граматика (grammar)
  - речення (sentence)
  - слово (word)
  - правильно (correctly)
  - помилка (mistake)
  recommended:
  - вид (aspect)
  - доконаний (perfective)
  - недоконаний (imperfective)
  - вправа (exercise)
activity_hints:
- type: quiz
  focus: A2 grammar comprehensive test
  items: 30
- type: fill-in
  focus: Case and aspect selection
  items: 25
- type: error-correction
  focus: Fix common mistakes
  items: 15
- type: quiz
  focus: Demonstrate A2 proficiency
  items: 10
focus: checkpoint
pedagogy: TTT
prerequisites:
- a2-54 (Sports and Fitness)
- a2-55 (Vocabulary Expansion Checkpoint)
connects_to:
- a2-57 (Practical Intro)
objectives:
- Learner can integrate A2 vocabulary in conversation
- Learner can use all grammatical cases correctly
- Learner can navigate common daily situations
- Learner can demonstrate A2 proficiency
grammar:
- A2 vocabulary review (all thematic areas)
- Case system review (all 7 cases)
- Verb aspect review (perfective/imperfective)
register: розмовний
phase: A2.5 [Vocabulary Expansion]

```

**Research notes** (reference for factual accuracy):
```
# Research: Checkpoint — Full Grammar (A2 Mastery)

**Module**: A2 M56 "Checkpoint: Full Grammar"
**Level**: A2 (Consolidation)
**Focus**: Comprehensive review of A2 morphology and syntax

## 1. Grammar: State Standard 2024 Reference

This module consolidates the grammatical competencies defined in **Section 2.4.2.4 (Каталог В. Зміст мовної компетентності)** of the *Ukrainian State Standard 2024* for **Level A2 (Початковий рівень другого ступеня)**.

Specific sections covered:
*   **§4.2.2. Уживання відмінкових форм іменників**: Comprehensive usage of all 7 cases in singular and plural (Nominative subject/identity, Genitive dates/quantity/absence, Dative beneficiary/age, Accusative direct object/direction, Instrumental instrument/profession, Locative place/time, Vocative address).
*   **§4.2.3. Особові форми дієслова**: Present, Past, and Future tenses; Imperative mood (2nd/3rd person).
*   **§4.3.2. Видові пари дієслів**: Distinction between imperfective and perfective aspect (e.g., *робити – зробити, писати – написати*).
*   **§4.4.2. Складне речення**: Compound and complex sentences using connectors *і, але, що, де, куди, тому що, бо, щоб*.
*   **§3 (Каталог Б)**: Integration of grammar within thematic contexts: Daily Life (§3.3), Work (§3.8), Health (§3.12), and Travel (§3.5).

> **Quote**: "Обсяг граматичних умінь рівня А2 охоплює усі аспекти, що перелічені на рівні А1, але з розширенням лексичного матеріалу, зростанням діапазону синтаксичних структур та ситуацій комунікації." (Standard, p. 48)

## 2. Vocabulary Frequency

This checkpoint activates high-frequency A2 core vocabulary.

**High-Frequency (Core A2):**
*   **Verbs of Motion**: *йти/ходити, їхати/їздити* (basic distinction required by Standard §3.6).
*   **Modal/State Verbs**: *могти, хотіти, мусити, подобатися*.
*   **Common Aspect Pairs**: *читати/прочитати, купувати/купити, брати/взяти, говорити/сказати*.
*   **Connectors**: *тому що, щоб, якщо, коли, після того як*.

**Thematic A2 Vocabulary (Contextual):**
*   **Travel**: *вокзал, квиток, митниця, валіза, відправлятися*.
*   **Health**: *лікар, хворіти, голова болить, ліки, аптека*.
*   **Daily Life**: *зустріч, домовлятися, запізнюватися, вихідні*.

**Collocations:**
*   *мати рацію* (to be right)
*   *брати участь* (to take part)
*   *робити замовлення* (to make an order)
*   *справляти враження* (to make an impression)

## 3. Cultural Hook

**The Vocative Case implies Relationship**:
Using the Vocative case (*Олено, Іване, пане, друже*) is not just a grammatical rule in Ukrainian; it is a marker of cultural respect and recognition. Omitting it (using Nominative for address) can sound rude, detached, or Russified. At A2, mastering *пане/пані* + Vocative is crucial for polite service interactions.

**Aspect and Politeness**:
Ukrainian culture encodes politeness in verbal aspect. The Imperative mood often swaps aspect for nuance:
*   *Сідайте* (Imperfective) – "Take a seat" (invitation, polite, process).
*   *Сядьте* (Perfective) – "Sit down" (command, specific action).
Learners should know that imperfective imperatives are often more welcoming for guests.

## 4. Pedagogical Notes

**Key Differences from English:**
*   **Aspect vs. Tense**: English speakers rely on complex tenses (Perfect, Continuous) to show completion or process. Ukrainian uses **Aspect** (Perfective/Imperfective). Learners often overuse the Imperfective past (*я купував квиток*) when they mean the result (*я купив квиток*).
*   **Motion Verbs**: The "Go" concept is split into *foot/vehicle* and *unidirectional/multidirectional*. This concept needs constant reinforcement.
*   **Object Marking**: English SVO word order is rigid. Ukrainian relies on Case endings (Accusative/Dative) to mark the object, allowing flexible word order.

**Common A2 Errors:**
*   **Case Confusion**: Using Locative for direction (*Я йду в парку*) instead of Accusative (*Я йду в парк*).
*   **Genitive Absence**: Forgetting the Genitive after *немає* or negative verbs (*Я не бачу автобус* instead of *автобуса*).
*   **Numerals**: Incorrect case agreement with numbers 2, 3, 4 (using Genitive Plural instead of Nominative Plural).
*   **"Щоб" Usage**: Using *для* + Infinitive (calque from English "for to...") instead of *щоб* + Infinitive.

**Teaching Sequence:**
1.  **Review**: Quick scan of Case endings (hard/soft).
2.  **Integrate**: Mix cases in sentences (Subject + Verb + Dir. Object + Ind. Object + Place).
3.  **Nuance**: Aspect pairs in past/future contexts.
4.  **Complexity**: Combine simple sentences into complex ones using *бо, тому що, щоб*.

## 5. Scope Boundaries

**IN SCOPE (Known & Testable):**
*   **Cases**: All 7 cases for Nouns, Adjectives, Pronouns (Singular & Plural).
*   **Tenses**: Present, Past, Future (Compound & Simple).
*   **Aspect**: Basic pairs, general meaning (process vs result).
*   **Motion**: Basic prefixes (*при-, по-, ви-, за-*), Uni/Multi distinction.
*   **Syntax**: *Коли/якщо* clauses, Reported speech (*Він сказав, що...*), Purpose (*...щоб...*).
*   **Conditional**: Basic *якби* + past tense (real/unreal simple conditions).
*   **Imperative**: Standard 2nd person forms.

**OUT OF SCOPE (Do NOT Test):**
*   **Participles**: Active/Passive participles (*зроблений, читаючий*) are B1/B2.
*   **Gerunds**: *Дієприслівник* (*йдучи, зробивши*) is B1.
*   **Passive Voice**: Passive constructions with *-но/-то* are B1.
*   **Abstract Morphology**: Complex word formation rules beyond basic prefixes/suffixes.
*   **Stylistics**: Dialects, jargon, or highly formal bureaucratic register.
*   **Advanced Motion**: Complex prefixes (*над-, під-, пере-* nuances) beyond basic A2 set.

```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. For each fix listed, apply it to the correct file
3. Output the COMPLETE fixed files (not diffs, not partial)

### Rules

1. **Apply EVERY fix** from the Fix Plan — do not skip any, even if they require adding substantial content
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies, leave unflagged sections untouched
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "add vocabulary to the section", you MUST add it. This is not "rewriting" — it's applying the fix.
4. **Preserve structure** — keep the same H2/H3 headings, same activity order, same vocabulary order
5. **Preserve voice** — do not change the writing style of unflagged content
6. **Activities YAML must be bare list at root** — no `activities:` wrapper
7. **Vocabulary YAML keeps its header** — preserve `module:`, `level:`, `version:`, `items:` structure
8. **If a fix is ambiguous**, choose the option that matches the plan file
9. **Never output "no changes needed"** — if the Fix Plan lists fixes, there ARE changes to make. Read more carefully.

### What NOT to Do

- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT change IPA unless the Fix Plan flags specific IPA errors
- Do NOT remove content unless the Fix Plan says to remove it
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed files

## Output Format

**CRITICAL: You MUST output fixed files between delimiter lines. Delimiters must appear on their own line, NOT inside code blocks.**

Output ONLY the files that need changes. If a file has no fixes, skip it entirely.

For EACH file that needs changes, output the COMPLETE file between these EXACT delimiter lines:

**Content fixes** — put the delimiter on its own line, then the complete markdown, then the end delimiter:

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**Activity fixes** — same pattern:

===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===

**Vocabulary fixes** — same pattern:

===VOCABULARY_START===
(complete fixed vocabulary YAML — with module/level/version/items header)
===VOCABULARY_END===

**After all files, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. [File: content] Line {N}: {what changed} — {which review issue this addresses}
2. [File: activities] Activity "{title}", Item {N}: {what changed} — {which review issue}
3. [File: vocabulary] Added/removed: {lemma} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}

## Files Changed: {list: content, activities, vocabulary — or subset}
## Files Unchanged: {list of files that needed no fixes}
===CHANGES_END===

## Boundaries

- Do NOT output files that have no changes — only output what you fixed
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- Do NOT add vocabulary not in the plan unless the Fix Plan explicitly says to
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
- If you encounter `NEEDS_HELP:` situations, report them clearly
