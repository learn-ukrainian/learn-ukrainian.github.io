<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/emergencies.yaml` file for module **54: Emergencies** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 10 | 10+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 6 | 9 | extended practice |
| Items per activity | 6 | — | each activity must have at least 6 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 6 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify
- **Inline priority (preferred):** image-to-letter, match-up, fill-in, quiz, watch-and-repeat
- **Workbook types:** fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out
- **Workbook priority (preferred):** fill-in, match-up, group-sort, anagram, unjumble
- **FORBIDDEN at this level:** cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 6–9 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: order-112-call -->`
- `<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-emergency-call -->`
- `<!-- INJECT_ACTIVITY: fill-in-reporting-issue -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct emergency phrase for the situation.
  items:
  - options:
    - Тут аварія! Викличте швидку!
    - Тут пожежа! Допоможіть!
    - Я загубив паспорт.
    question: You see a car crash.
  - options:
    - Тут пожежа! Допоможіть!
    - Тут аварія!
    - Мені потрібен лікар.
    question: You see a building on fire.
  - options:
    - Людині погано! Викличте швидку!
    - Викличте поліцію!
    - Я загубив паспорт.
    question: Someone is feeling very ill on the street.
  - options:
    - Я загубив паспорт.
    - Тут аварія!
    - Мені потрібна швидка.
    question: You cannot find your passport at the airport.
  - options:
    - Викличте поліцію! Допоможіть!
    - Тут пожежа!
    - Мені потрібен лікар.
    question: Someone stole your wallet.
  type: quiz
- focus: Complete the emergency phone call.
  items:
  - Алло! {Допоможіть|Дякую|Вибачте}! Тут аварія!
  - '{Викличте|Загубив|Потрібен} швидку допомогу!'
  - Я на {вулиці|лікарні|поліції} Хрещатик, біля метро.
  - Мене {звати|прізвище|адреса} Адам.
  - Мій номер {телефону|паспорта|будинку} — нуль дев'яносто три...
  - Мені потрібна {допомога|пожежа|аварія}!
  type: fill-in
- focus: Put the dialogue with the 112 operator in the correct order.
  items:
  - — Служба порятунку, слухаю вас.
  - — Допоможіть! Тут пожежа!
  - — Де ви?
  - — На вулиці Шевченка, будинок п'ять.
  - — Зрозуміло. Швидка і пожежники вже їдуть. Як вас звати?
  - — Мене звати Анна. Дякую!
  type: order
- focus: Reporting an issue at the police station or hospital.
  items:
  - Добрий день. Я {загубив|викличте|допоможіть} паспорт.
  - Моє {прізвище|ім'я|номер} — Сміт.
  - Мені {потрібен|погана|хворий} лікар.
  - У мене {алергія|пожежа|аварія} на ці таблетки.
  - Я не розумію. {Повторіть|Допоможіть|Викличте}, будь ласка.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- пожежа (fire, f)
- порятунок (rescue, m)
- паспорт (passport, m)
- адреса (address, f)
- номер (number, m)
- алергія (allergy, f)
- форма (form/document, f)
- будинок (building, m)
required:
- допомога (help, f)
- допоможіть (help! — imperative)
- швидка (ambulance, f — short for швидка допомога)
- поліція (police, f)
- лікарня (hospital, f)
- аварія (accident, f)
- загубити (to lose)
- викликати (to call/summon)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Emergencies happen unexpectedly in any country. In high-stress moments, clear and direct communication is your most valuable tool. You do not need perfect grammar or complex sentences during a crisis. You only need to know specific, formulaic phrases to get immediate assistance. Ukrainian emergency operators are trained to ask simple questions. Your goal is to provide fast, accurate answers without hesitation. We focus on the essential vocabulary for survival in Ukraine. You will learn to state the problem clearly, give your exact location, and provide your personal details. Read the following situations.

> **Оператор:** Служба порятунку, слухаю вас. *(Rescue service, I am listening to you.)*
> **Водій:** Допоможіть! Тут аварія! Людина не рухається! *(Help! There is an accident here! A person is not moving!)*
> **Оператор:** Де ви? *(Where are you?)*
> **Водій:** На вулиці Хрещатик, біля метро Майдан Незалежності. *(On Khreshchatyk street, near the Maidan Nezalezhnosti metro.)*
> **Оператор:** Зрозуміло. Швидка вже їде. Як вас звати? *(Understood. The ambulance is already on its way. What is your name?)*
> **Водій:** Мене звати Адам. Мій номер — нуль дев'яносто три... *(My name is Adam. My number is zero ninety-three...)*
> **Оператор:** Дякую. Залишайтеся на місці. *(Thank you. Stay in place.)*

This dialogue shows a critical situation on the road. The driver uses short, urgent sentences. **Аварія** (accident) immediately tells the operator the nature of the event. The driver then gives the exact location and answers simple questions. The operator confirms that a **швидка** (ambulance) is coming.

> **Адам:** Вибачте, де тут поліція? *(Excuse me, where is the police here?)*
> **Перехожий:** Поліція? Прямо і наліво. *(Police? Straight and to the left.)*
> **Адам:** Дякую! *(Thank you!)*
>
> *(У відділку / At the station)*
> **Адам:** Добрий день. Я загубив паспорт. *(Good day. I lost my passport.)*
> **Офіцер:** Де ви його загубили? *(Where did you lose it?)*
> **Адам:** Я не знаю. Може, в метро. *(I do not know. Maybe in the metro.)*
> **Офіцер:** Як ваше прізвище? *(What is your surname?)*
> **Адам:** Сміт. Адам Сміт. *(Smith. Adam Smith.)*
> **Офіцер:** Ваш номер телефону? *(Your phone number?)*
> **Адам:** Нуль дев'яносто три, п'ятсот двадцять один... *(Zero ninety-three, five hundred twenty-one...)*
> **Офіцер:** Добре. Заповніть цю форму, будь ласка. *(Good. Fill out this form, please.)*

Losing documents is stressful but common. Adam first asks a passerby where the **поліція** (police) is located. Inside the station, he uses the past tense verb **загубив** (lost) to report the missing item. The officer asks standard identification questions. Adam provides his details and receives a **форма** (form) to complete.

Every emergency conversation follows a strict logical structure. You must first state the specific problem so they know who to send. Next, you must give your exact location. Finally, you provide your personal information for their official records.

<!-- INJECT_ACTIVITY: order-112-call -->

## Екстрені ситуації (Emergencies)

Ukraine has a centralized system for emergencies. The universal emergency number is **один один два** (112). This number works everywhere in the country from any mobile phone, even without a SIM card. You can also dial specific services directly if you know exactly what you need. The direct number for the fire service is **один нуль один** (101). The direct number for the police is **один нуль два** (102). The direct number for an ambulance is **один нуль три** (103). These three numbers are standard across Ukraine. Memorize them completely.

When disaster strikes, you must alert people immediately. Use the formal, plural **наказовий спосіб** (imperative mood) to call for help. Do not worry about grammar rules here; simply memorize these phrases as unchangeable chunks.

*   **Допоможіть!** — Help!
*   **Викличте швидку!** — Call an ambulance!
*   **Викличте поліцію!** — Call the police!

Shouting **Допоможіть** (help) is your first line of defense. **Викликати** (to call/summon) is used specifically for ordering emergency services or a taxi. You command others to summon the ambulance or police.

After grabbing attention, state the problem clearly. Use the simple word **тут** (here) followed by the noun.

*   **Тут аварія!** — There is an accident here!
*   **Тут пожежа!** — There is a fire here!

If someone is experiencing a medical crisis, use the fixed expression **людині погано**. This literally means "to a person it is bad". If you are the one in danger, ask for **допомога** (help) directly.

*   **Людині погано!** — Someone is feeling bad!
*   **Мені потрібна допомога!** — I need help!

> Марк на вулиці. Він бачить густий дим. Це велика пожежа. Марк телефонує один один два. Він просить про допомогу.
> *Mark is on the street. He sees thick smoke. It is a big fire. Mark calls one one two. He asks for help.*

The operator will always ask **Де ви?** (Where are you?). You must provide your location accurately. Review the location phrases you already know. Use **я на вулиці** (I am on the street), **я біля** (I am near), **навпроти** (opposite), or **поруч** (nearby).

*   **Я на вулиці Хрещатик.** — I am on Khreshchatyk street.
*   **Я біля метро.** — I am near the metro.
*   **Я в метро.** — I am in the metro.
*   **Аптека навпроти.** — The pharmacy is opposite.

When giving a specific **адреса** (address), provide the street name and the building number. A building is a **будинок**.

*   **Моя адреса: вулиця Хрещатик, будинок десять.** — My address is: Khreshchatyk street, building 10.

:::caution
Beware of the false friend "адрес". In Ukrainian, a physical location is always **адреса** (feminine). The word "адрес" is a formal written tribute, which you will likely never use.
:::

<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->
<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

## Допомога (Getting Help)

Medical emergencies require specific vocabulary. If you arrive at a **лікарня** (hospital) or a clinic, state your primary need immediately. Use the fixed chunk **мені потрібен** (I need) for a masculine noun, or **мені потрібна** for a feminine noun.

*   **Мені потрібен лікар.** — I need a doctor.
*   **Мені потрібна швидка.** — I need an ambulance.

**Лікарня** refers to the physical hospital building, while a **лікар** is the doctor who treats you. Keep your statements brief and direct.

To describe pain, Ukrainian uses a completely different structure than English. You do not say "I have a headache". Instead, you use the fixed structure **у мене болить** (at me it aches), followed by the body part in the **називний відмінок** (nominative case).

*   **У мене болить голова.** — My head hurts.
*   **У мене болить живіт.** — My stomach hurts.
*   **У мене болить горло.** — My throat hurts.

If you have a medical reaction to food or medicine, state this clearly. An allergy is an **алергія**.

*   **У мене алергія на антибіотики.** — I am allergic to antibiotics.

Stressful situations make understanding a foreign language much harder. If you do not comprehend the doctor or the police officer, do not pretend that you do. Ask them to clarify.

*   **Я не розумію.** — I do not understand.
*   **Повторіть, будь ласка.** — Repeat, please.
*   **Ви говорите англійською?** — Do you speak English?

Using the formal imperative **повторіть** ensures they know you need to hear the information again.

Whether you are at a hospital or a police station, authorities require your personal data. They will ask for your name, phone number, and country of origin.

*   **Мене звати Девід.** — My name is David.
*   **Моє прізвище Сміт.** — My surname is Smith.
*   **Мій номер телефону...** — My phone number is...
*   **Я з Канади.** — I am from Canada.
*   **Мій готель — Турист.** — My hotel is Tourist.

If you are at the police station because you lost a document, use the past tense. Remember that the verb **загубити** (to lose) changes its ending based on your grammatical gender.

*   **Я загубив паспорт.** — I lost my passport. (masculine speaker)
*   **Я загубила паспорт.** — I lost my passport. (feminine speaker)

The officer will likely give you a piece of paper and say **заповніть форму** (fill out the form).

> Анна в поліції. Вона дуже сумна. Анна загубила сумку. Там був паспорт. Анна бере форму.
> *Anna is at the police station. She is very sad. Anna lost her bag. The passport was there. Anna takes a form.*

<!-- INJECT_ACTIVITY: fill-in-reporting-issue -->

## Summary

Navigating an emergency abroad is a daunting experience. Your survival kit relies on knowing exactly what to say without thinking about complex grammar. Remember that **один один два** (112) is your universal lifeline in Ukraine. When you face immediate danger, shout your first commands clearly: **Допоможіть!** (Help!), **Викличте швидку!** (Call an ambulance!), or **Викличте поліцію!** (Call the police!).

When the operator answers, state the problem using the word "тут". Tell them **Тут пожежа!** (There is a fire here!) or **Тут аварія!** (There is an accident here!). Immediately follow this with your location: **Я на вулиці...** (I am on ... street), **Я біля...** (I am near...), or provide your full **адреса** (address).

At a medical facility, be direct about your needs. Say **Мені потрібен лікар** (I need a doctor) and describe your symptoms with **У мене болить...** (My ... hurts). Always have your personal information ready. You must be able to state your name, surname, phone number, address, and country. Finally, if you lose something important, report it clearly: **Я загубив паспорт** or **Я загубила паспорт** (I lost my passport). As a final self-check, practice a simulated 112 call aloud: state the specific problem, give your exact location, and give your name.

Review these critical questions to test your readiness for an emergency in Ukraine. Read the question and answer aloud.

*   **Питання:** Як викликати поліцію чи швидку? *(How to call the police or ambulance?)*
    **Відповідь:** Викличте поліцію! Викличте швидку!
*   **Питання:** Як сказати, що сталася аварія або пожежа? *(How to say that an accident or fire happened?)*
    **Відповідь:** Тут аварія! Тут пожежа!
*   **Питання:** Як сказати, що комусь погано? *(How to say that someone is feeling bad?)*
    **Відповідь:** Людині погано! Допоможіть!
*   **Питання:** Як сказати про втрату документів? *(How to tell about the loss of documents?)*
    **Відповідь:** Я загубив паспорт. Я загубила паспорт.
*   **Питання:** Як сказати про біль і потребу в лікарі? *(How to tell about pain and the need for a doctor?)*
    **Відповідь:** У мене болить голова. Мені потрібен лікар.

> Це екстрена ситуація. Антон телефонує один нуль два. Він швидко дає свою адресу. Офіцер слухає уважно. Поліція вже їде.
> *This is an emergency situation. Anton calls one zero two. He quickly gives his address. The officer listens carefully. The police are already on their way.*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: emergencies
level: a1

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (10 total / 4–6 inline / 6–9 workbook,
# 6+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 6 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 6 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 6 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 6 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 6 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 6 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 6 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 6 items total

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 54/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 10 activities.** Inline: 4–6. Workbook: 6–9. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 6 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 6.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 6** workbook activities.
- [ ] **Total ≥ 10.**
- [ ] **Every** activity has **at least 6** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
