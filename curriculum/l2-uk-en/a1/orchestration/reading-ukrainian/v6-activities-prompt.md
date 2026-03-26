# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/reading-ukrainian.yaml` file for module **2: Reading Ukrainian** (a1).

Output **pure YAML only** — no markdown fencing, no preamble, no explanation. Just the YAML document.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-syllable-count -->`
- `<!-- INJECT_ACTIVITY: match-iotated-vowels -->`
- `<!-- INJECT_ACTIVITY: fill-in-syllable-division -->`
- `<!-- INJECT_ACTIVITY: quiz-read-and-match -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
  type: fill-in
- focus: How many syllables? Count the vowels.
  items: 8
  type: quiz
- focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
  type: match-up
- focus: Read the word and choose its meaning
  items: 6
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- університет (university) — long word practice
- бібліотека (library) — 5 syllables
- фотографія (photography) — long word with Ф
- шоколад (chocolate) — Ш + О + К combination
required:
- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
<!-- TAB:Урок -->

## Склади (Syllables)

You know the Ukrainian alphabet from Module 1. You can name every letter. But a letter on its own is not reading — reading means looking at a word like **аптека** (pharmacy) and hearing it in your mind without stopping at each letter. How do Ukrainian children learn this skill? With one unbreakable rule, taught on page 25 of every first-grade textbook:

:::tip
**У слові стільки складів, скільки голосних звуків.**
A word has as many syllables as it has vowel sounds.
:::

Count the vowels, count the syllables. It works every time. Look at **мама** (mother) — two vowels, А and А, so two syllables: ма-ма. Now **молоко** (milk) — three vowels, О, О, О — three syllables: мо-ло-ко. What about **банк** (bank)? One vowel, А — one syllable: банк. And **оса** (wasp)? Two vowels, О and А — two syllables: о-са. No exceptions. This rule never breaks.

Now for the method itself. Ukrainian teachers use a process called **звуковий аналіз** (sound analysis), described in Большакова Grade 1 on page 29. Here is how to read any new word you encounter:

1. **Find the vowels** — they are the cores of each syllable.
2. **Split at syllable boundaries** — Ukrainian follows the open-syllable principle (складоподіл): consonants prefer to start new syllables rather than close old ones.
3. **Sound out each syllable** separately.
4. **Blend** the syllables into the full word at natural speed.

Walk through **аптека** (pharmacy): the vowels are А, Е, А — three syllables. Split: а-пте-ка. Sound each piece, then blend them together. Now try **університет** (university): vowels У, І, Е, И, Е — five syllables. Split: у-ні-вер-си-тет. Five pieces, blended into one word.

Try counting without splitting — just count the vowels. **Сон** (dream) — 1. **Сало** (lard) — 2. **Ламана** (broken line) — 3. **Смола** (resin) — 2. **Ананас** (pineapple) — 3. **Бібліотека** (library) — 5. Remember: Ь (soft sign) and the apostrophe are NOT vowels. Never count them. You may also notice that one syllable in each word sounds louder than the others — that is **наголос** (stress), which Module 3 covers fully. For now, focus on splitting and blending.

<!-- INJECT_ACTIVITY: quiz-syllable-count -->

## Голосні літери (Vowel Letters)

Module 1 introduced this fact: Ukrainian has 6 vowel sounds but 10 vowel letters. Now meet all ten individually and understand exactly what each one does.

The first six are simple — each letter represents ONE consistent sound, with no surprises:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | [а] | **аптека** (pharmacy) |
| **О** | [о] | **око** (eye) |
| **У** | [у] | **рука** (hand) |
| **Е** | [е] | **село** (village) |
| **И** | [и] | **кит** (whale) |
| **І** | [і] | **кіт** (cat) |

Unlike English vowels, which shift depending on the word (compare the "a" in "father" versus "fate"), Ukrainian vowels stay constant. **А** is always [а]. **О** is always [о]. What you see is what you hear.

The remaining four letters are called **iotated vowels** because they can represent TWO sounds — a [й] glide followed by a vowel. This happens at the beginning of a word or after another vowel.

**Я** = [йа] at word start or after a vowel: **яблуко** (apple) sounds like [йаблуко], **моя** (my, feminine) sounds like [мойа]. But after a consonant, Я softens that consonant and contributes only [а]: in **пісня** (song), the Н before Я becomes soft.

**Ю** follows the same pattern: [йу] at word start — **юнак** (young man) — or softening + [у] after a consonant: in the word **люблю** (I love), both Л sounds are softened by Ю.

**Є** = [йе] at word start: **єнот** (raccoon). After a consonant, it softens + [е]: **синє** (blue, neuter).

Then the unique one. **Ї** ALWAYS represents two sounds [йі] — it never softens a preceding consonant. It appears only at the start of a word, after a vowel, or after an apostrophe: **їжак** (hedgehog), **мої** (my, plural). Ї is uniquely Ukrainian — no other Slavic language has this letter.

Now for minimal pairs where one vowel letter changes the entire meaning. **И** and **І** look similar but produce different sounds: **кит** (whale) vs **кіт** (cat), **дим** (smoke) vs **дім** (house), **лис** (fox) vs **ліс** (forest), **рик** (roar) vs **рік** (year), **бик** (bull) vs **бік** (side). И is a back vowel — your tongue pulls back. І is a front vowel — your tongue pushes forward. The difference is subtle but it changes meaning entirely. Listen to Anna's pronunciation videos for each pair to train your ear.

<!-- INJECT_ACTIVITY: match-iotated-vowels -->

<!-- INJECT_ACTIVITY: fill-in-syllable-division -->

## Читання слів (Reading Words)

Time to apply everything and read real Ukrainian words fluently. The key strategy: do not read letter-by-letter. Read syllable-by-syllable. Start with the vowels — they are your anchors — then build outward.

Take **книга** (book). Find the vowels: И, А — two syllables. Split: кни-га. Blend them together: книга. Now **шоколад** (chocolate): vowels О, О, А — three syllables. Split: шо-ко-лад. Blend: шоколад. One more: **вулиця** (street) — vowels У, И, Я — three syllables: ву-ли-ця. The more you practice this vowel-first approach, the faster you read any new word without hesitation.

Common word patterns build reading speed. Start recognizing shapes:

**CVCV** (consonant-vowel-consonant-vowel) — the simplest pattern, two syllables of alternating sounds: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (leg).

**CVCCV** — a consonant cluster appears before the second vowel: **лампа** (lamp), **банда** (gang), **парта** (desk).

**CVC** — one syllable, closed by a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **мак** (poppy), **сир** (cheese).

Longer words follow the same logic: **аптека** (pharmacy) is V-CCV-CV, **молоко** (milk) is CV-CV-CV, **столиця** (capital) is CCV-CV-CV. Read each group aloud — start slow, then speed up. Pattern recognition is what turns mechanical decoding into natural reading.

Watch for three special letter combinations. **Щ** always sounds like [шч]: **що** (what), **ще** (still), **щастя** (happiness). **Ь** (soft sign) has no sound of its own — it softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The apostrophe separates a consonant from an iotated vowel: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). Module 3 explores all three in depth — for now, just recognize them when you see them.

<!-- INJECT_ACTIVITY: quiz-read-and-match -->

## Читаємо разом (Reading Together)

A reading ladder — start where you feel comfortable, then climb.

**Level 1** (2 syllables): **мама** (mother), **тато** (father), **вода** (water), **рука** (hand), **хата** (house), **каша** (porridge), **книга** (book), **школа** (school), **пісня** (song).

**Level 2** (3 syllables): **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street), **столиця** (capital), **машина** (car).

**Level 3** (4+ syllables): **університет** (university), **бібліотека** (library), **фотографія** (photography), **шоколадний** (chocolate, adjective).

Read each level until it feels comfortable, then move to the next. Speed comes from practice, not rushing.

Now read a simple connected text. Every sentence uses **Це** (this is) + a noun, or a location word — no verbs yet:

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. А це що? Це кафе. Поруч пошта. Тут вулиця, там парк.**

*(This is Kyiv. This is the capital. Here is a pharmacy and a bank. There is a school. And what is this? This is a café. Nearby is a post office. Here is a street, there is a park.)*

Read it aloud three times: first slowly, syllable by syllable. Then at a normal pace. Then try reading without pausing between words. You just read Ukrainian sentences.

Challenge round — try these longer words using the vowel-first method: **бібліотека** (library) — vowels І, І, О, Е, А → 5 syllables. **Університет** (university) — vowels У, І, Е, И, Е → 5 syllables. **Фотографія** (photography) — vowels О, О, А, І, Я → 5 syllables. If you can read these, you can read any Ukrainian word. The syllable rule and vowel-first strategy work every time.

## Підсумок — Summary

This module gave you three tools that work together to unlock Ukrainian reading.

**First: the syllable rule.** Count the vowels to count the syllables. **Молоко** — three vowels, three syllables. **Банк** — one vowel, one syllable. It never fails.

**Second: the 10 vowel letters.** Six are simple — **А**, **О**, **У**, **Е**, **И**, **І** — each making one consistent sound. Four are iotated — **Я**, **Ю**, **Є**, **Ї** — capable of representing two sounds at word start or after a vowel. **Ї** is uniquely Ukrainian and always represents [йі].

**Third: the reading strategy.** Find the vowels first, split into syllables, sound out each piece, blend into the full word. These three tools let you read any Ukrainian word you encounter, even one you have never seen before.

Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters. When does **Я** represent two sounds? What makes **Ї** unique? What does **Ь** do? Read this word: **бібліотека** — how many syllables?

Coming in Module 3: **наголос** (stress), the soft sign and apostrophe in detail, and voiced versus voiceless consonant pairs.


<!-- TAB:Словник -->

### Обов'язкові та рекомендовані слова

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **склад** | syllable | ім. | ч. |
| **голосни́й** | vowel (sound/letter) | прикм. |  |
| **лі́тера** | letter | ім. | ж. |
| **на́голос** | stress (accent) | присл. |  |
| **складопо́діл** | syllable division | ім. | ч. |
| **апте́ка** | pharmacy | ім. | ж. |
| **університе́т** | university | ім. | ч. |
| **бібліоте́ка** | library | ім. | ж. |
| **фотогра́фія** | photography | ім. | ж. |
| **шокола́д** | chocolate | ім. | ч. |
| **я́блуко** | apple | ім. | с. |
| **молоко́** | milk | ім. | с. |
| **люди́на** | person | ім. | ж. |
| **ву́лиця** | street | ім. | ж. |
| **столи́ця** | capital (city) | ім. | ж. |
| **ка́ша** | porridge | ім. | ж. |
| **пі́сня** | song | ім. | ж. |
| **ма́ма** | mother | ім. | ж. |
| **та́то** | father | ім. | ч. |
| **о́ко** | eye | ім. | с. |
| **рука́** | hand | ім. | ж. |
| **село́** | village | ім. | с. |
| **кит** | whale | ім. | ч. |
| **кіт** | cat | ім. | ч. |
| **оса́** | wasp | ім. | ж. |
| **са́ло** | lard | ім. | с. |
| **смола́** | resin | ім. | ж. |
| **анана́с** | pineapple | ім. | ч. |
| **вода́** | water | ім. | ж. |
| **ха́та** | house (traditional) | ім. | ж. |
| **коза́** | goat | ім. | ж. |
| **нога́** | leg | ім. | ж. |
| **шко́ла** | school | ім. | ж. |
| **кни́га** | book | ім. | ж. |
| **па́рта** | desk (school) | ім. | ж. |
| **ліс** | forest | ім. | ч. |
| **дуб** | oak | ім. | ч. |
| **хліб** | bread | ім. | ч. |
| **ще** | still, yet | присл. |  |
| **ща́стя** | happiness | ім. | с. |
| **день** | day | ім. | ч. |
| **сіль** | salt | ім. | ж. |
| **кінь** | horse | ім. | ч. |
| **сім'я́** | family | ім. | ж. |
| **м'я́со** | meat | ім. | с. |
| **п'ять** | five | числ. |  |
| **юна́к** | young man | ім. | ч. |
| **єно́т** | raccoon | ім. | ч. |
| **їжа́к** | hedgehog | ім. | ч. |
| **моя́** | my (feminine) | прикм. |  |
| **мої́** | my (plural) | прикм. |  |
| **люблю́** | I love | дієсл. |  |
| **дим** | smoke | ім. | ч. |
| **лис** | fox | ім. | ч. |
| **рік** | year | дієсл. |  |
| **сир** | cheese | ім. | ч. |
| **тут** | here | присл. |  |
| **там** | there | присл. |  |
| **по́руч** | nearby | присл. |  |
| **кафе́** | café | ім. | с. |
| **по́шта** | post office | ім. | ж. |
| **парк** | park | ім. | ч. |
| **шокола́дний** | chocolate (adjective) | прикм. |  |
| **сло́во** | word | ім. | с. |
| **при́голосний** | consonant | прикм. |  |

### Вирази

| Вираз | Переклад |
|-------|----------|
| **звуковий аналіз** | sound analysis |
| **У слові стільки складів, скільки голосних звуків.** | A word has as many syllables as it has vowel sounds. |

### Картки — Flashcards

<FlashcardDeck client:only="react" cards={[{ front: "склад", back: "syllable", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "голосни́й", back: "vowel (sound/letter)", subtitle: "прикм." }, { front: "лі́тера", back: "letter", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "на́голос", back: "stress (accent)", subtitle: "присл." }, { front: "складопо́діл", back: "syllable division", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "апте́ка", back: "pharmacy", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "університе́т", back: "university", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "бібліоте́ка", back: "library", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "фотогра́фія", back: "photography", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "шокола́д", back: "chocolate", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "я́блуко", back: "apple", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "молоко́", back: "milk", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "люди́на", back: "person", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ву́лиця", back: "street", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "столи́ця", back: "capital (city)", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ка́ша", back: "porridge", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "пі́сня", back: "song", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ма́ма", back: "mother", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "та́то", back: "father", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "о́ко", back: "eye", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "рука́", back: "hand", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "село́", back: "village", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "кит", back: "whale", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "кіт", back: "cat", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "оса́", back: "wasp", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "са́ло", back: "lard", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "смола́", back: "resin", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "анана́с", back: "pineapple", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "вода́", back: "water", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ха́та", back: "house (traditional)", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "коза́", back: "goat", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "нога́", back: "leg", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "шко́ла", back: "school", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "кни́га", back: "book", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "па́рта", back: "desk (school)", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ліс", back: "forest", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "дуб", back: "oak", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "хліб", back: "bread", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ще", back: "still, yet", subtitle: "присл." }, { front: "ща́стя", back: "happiness", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "день", back: "day", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "сіль", back: "salt", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "кінь", back: "horse", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "сім'я́", back: "family", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "м'я́со", back: "meat", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "п'ять", back: "five", subtitle: "числ." }, { front: "юна́к", back: "young man", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "єно́т", back: "raccoon", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "їжа́к", back: "hedgehog", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "моя́", back: "my (feminine)", subtitle: "прикм." }, { front: "мої́", back: "my (plural)", subtitle: "прикм." }, { front: "люблю́", back: "I love", subtitle: "дієсл." }, { front: "дим", back: "smoke", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "лис", back: "fox", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "рік", back: "year", subtitle: "дієсл." }, { front: "сир", back: "cheese", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "тут", back: "here", subtitle: "присл." }, { front: "там", back: "there", subtitle: "присл." }, { front: "по́руч", back: "nearby", subtitle: "присл." }, { front: "кафе́", back: "café", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "по́шта", back: "post office", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "парк", back: "park", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "шокола́дний", back: "chocolate (adjective)", subtitle: "прикм." }, { front: "сло́во", back: "word", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "при́голосний", back: "consonant", subtitle: "прикм." }]} />


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

**Джерела — References**

- Большакова Grade 1 буквар, p.25
  _Syllable rule: 'У слові стільки складів, скільки голосних звуків.'_
- Большакова Grade 1 буквар, p.29
  _Звуковий аналіз слова method — how to analyze word sounds._
- Захарійчук Grade 1 (NUS 2025), p.13-15
  _Sound notation: [•] for vowels, [–] for consonants, [=] for soft._
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: reading-ukrainian
level: a1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

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
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.1 (Module 2/55) — COMPLETE BEGINNER**

The learner is on their FIRST DAYS learning Ukrainian. They:
- Cannot read Ukrainian yet (learning the alphabet)
- Know zero Ukrainian grammar
- Can recognize only a few words (мама, тато, привіт)

**ALL instructions MUST be in English.** The learner cannot read Ukrainian instructions.

**Best activity types for this level:**
- image-to-letter: hear/see → pick the letter
- letter-grid: interactive alphabet practice
- match-up: letter ↔ sound, letter ↔ word
- quiz: in ENGLISH about Ukrainian sounds ('What sound does В make?')
- observe: show patterns in Ukrainian with English prompts
- group-sort: sort letters into vowels/consonants

**DO NOT use:** fill-in with Ukrainian sentences, error-correction, translate (learner can't write Ukrainian yet), cloze, unjumble.


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
