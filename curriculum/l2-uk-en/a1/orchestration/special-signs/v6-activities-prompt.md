# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/special-signs.yaml` file for module **3: Special Signs** (a1).

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

- `<!-- INJECT_ACTIVITY: fill-in-soft-apostrophe -->`
- `<!-- INJECT_ACTIVITY: quiz-soft-apostrophe-neither -->`
- `<!-- INJECT_ACTIVITY: match-voiced-voiceless -->`
- `<!-- INJECT_ACTIVITY: quiz-g-vs-g -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Does this word have a soft sign, apostrophe, or neither?
  items: 8
  type: quiz
- focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, etc.'
  items: 8
  type: match-up
- focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
  type: fill-in
- focus: Choose the correct pronunciation for Г vs Ґ words
  items: 4
  type: quiz


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- батько (father, formal) — soft sign
- учитель (teacher) — soft sign at end
- дев'ять (nine) — apostrophe
- комп'ютер (computer) — apostrophe in cognate
- м'який (soft) — apostrophe + soft sign
required:
- сім'я (family) — apostrophe word
- день (day) — soft sign after Н
- сіль (salt) — soft sign after Л
- м'ясо (meat) — apostrophe after М
- п'ять (five) — apostrophe after П
- гарно (nicely, beautifully) — Г [ɦ] practice
- риба (fish) — Р and И practice


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
<!-- TAB:Урок -->

## М'який знак (The Soft Sign — Ь)

Look at these two words: **рис** (rice) and **рись** (lynx). The only difference is a small sign at the end — **Ь**, the soft sign. That tiny mark changes the meaning entirely.

**Ь** has no sound of its own. It never speaks — its only job is to soften the consonant before it. Ukrainian distinguishes between **тверді** (hard) and **пом'якшені** (softened) consonants, and Ь is how writing shows the difference. In Ukrainian school textbooks, hard consonants are marked [–] and soft consonants are marked [=]. Compare: **тин** (fence) vs **тінь** (shadow), **син** (son) vs **синь** (blue expanse). Same letters, but Ь transforms the final consonant — and the entire word. As the poet Ганна Чубач wrote: «Ви без мене слово «камінь» прочитали б як «камін»!» — without Ь, the word **камінь** (stone) becomes **камін** (fireplace).

Where does Ь appear? It follows specific consonants in predictable patterns. After **Н**: **день** (day), **кінь** (horse), **осінь** (autumn), **камінь** (stone). After **Л**: **сіль** (salt), **біль** (pain). After **Т**: **мить** (moment), **радість** (joy). After **З**: **мазь** (ointment). You will see Ь in everyday words everywhere: **учитель** (teacher), **батько** (father), **маленький** (small), **стілець** (chair). One important rule — Ь appears only after consonants. It never starts a word, and it never stands alone.

When you see Ь while reading, soften the consonant before it. Imagine pressing that consonant gently with your tongue closer to the palate. Practice reading aloud: **день**, **сіль**, **кінь**, **учитель**, **батько**, **маленький**, **стілець**. Feel the soft ending on each word.

<!-- INJECT_ACTIVITY: fill-in-soft-apostrophe -->

Ь softens consonants. But Ukrainian has another sign that does the opposite — it keeps consonants hard. That sign is the apostrophe.

## Апостроф (The Apostrophe)

Compare two words: **моря** (seas) and **подвір'я** (yard). In **моря**, the Р is soft and the Я represents one sound. In **подвір'я**, the apostrophe after Р keeps it hard, and Я splits into two sounds: [й] + [а]. One small mark — completely different pronunciation.

The rule comes straight from Захарійчук Grade 1, page 97: the apostrophe appears after the consonants **б**, **п**, **в**, **м**, **ф**, **р** — and only before the vowels **я**, **ю**, **є**, **ї**. Its job is the opposite of Ь. Where Ь softens, the apostrophe keeps the consonant hard and gives the following vowel its full two-sound value. Think of the apostrophe as a wall between the consonant and the vowel — they stay separate, each keeping its own character.

Here are the key words. **Сім'я** (family) — the М stays hard, and Я sounds as [й] + [а]. **М'ясо** (meat) — hard М, then [й] + [а]. **П'ять** (five) — hard П, then [й] + [а]. **Комп'ютер** (computer) — hard П, then [й] + [у]. **Дев'ять** (nine) — hard В, then [й] + [а]. Without the apostrophe, the consonant would soften and the vowel would lose its double sound — a completely different pronunciation. The textbook shows another clear pair: **буряк** (beetroot) has no apostrophe, so Р is soft. But **бур'ян** (weeds) has an apostrophe, so Р stays hard and Я gives two sounds.

Practice reading from textbook examples: **м'яч** (ball), **м'який** (soft), **п'ятниця** (Friday), **ім'я** (name), **сім'я** (family), **подвір'я** (yard), **здоров'я** (health), **об'єкт** (object). Read each word aloud. Feel the hard consonant before the apostrophe, then the full vowel after it.

<!-- INJECT_ACTIVITY: quiz-soft-apostrophe-neither -->

A quick comparison: **Ь** softens the consonant before it (**день**, **сіль**). The apostrophe keeps the consonant hard before **я**, **ю**, **є**, **ї** (**м'ясо**, **сім'я**). Two signs, opposite jobs. Both essential for reading Ukrainian correctly.

## Дзвінкі і глухі (Voiced and Voiceless)

Every consonant in Ukrainian is either **дзвінкий** (voiced) or **глухий** (voiceless). There is a simple test straight from Ukrainian classrooms: put your hand on your throat. Say **Б** — you feel vibration. Now say **П** — no vibration. Your lips are in the same position both times. The only difference is whether your vocal cords are active. Vibration means voiced. Silence means voiceless.

Ukrainian consonants form eight voiced-voiceless pairs: **Б**–**П**, **Д**–**Т**, **Г**–**Х**, **Ґ**–**К**, **З**–**С**, **Ж**–**Ш**, **ДЗ**–**Ц**, **ДЖ**–**Ч**. Notice the last two pairs — **ДЗ** and **ДЖ**. These are written with two letters but represent single sounds. Linguists call them африкати (affricates). When you see **ДЗ** in a word like **дзвонити** (to ring), it is one sound, not Д + З. The same applies to **ДЖ** — one unified sound, like English "j" in "jump" but with the tongue slightly further forward.

Here is a critical difference from Russian: Ukrainian does NOT devoice consonants at word end. In Russian, the word for "oak" sounds like *[дуп], and "frost" sounds like *[морос]. In Ukrainian, **дуб** is [дуб] and **мороз** is [мороз]. Every consonant keeps its true voice all the way to the end of the word. This is authentic Ukrainian pronunciation — if you have been exposed to Russian, resist the habit of swallowing the final consonant's voice.

<!-- INJECT_ACTIVITY: match-voiced-voiceless -->

Minimal pairs show why voicing matters: **балка** (beam) vs **палка** (stick), **коза** (goat) vs **коса** (braid). One sound changes — the entire meaning shifts. Getting voicing right is not optional decoration; it is the difference between words.

## Важкі звуки (Tricky Sounds)

**И** — the sound that trips up every English speaker. It is not English "ee" (as in "see") and not English "i" (as in "sit"). It lives somewhere between them. Here is the technique: start to smile as if you were going to say "ee," but pull your tongue back slightly. Your jaw drops a tiny bit compared to **І**. The result is a rounder, deeper vowel — distinctly Ukrainian. Practice words: **бик** (bull), **лист** (leaf), **зима** (winter), **тихо** (quietly), **синій** (blue). Now listen for the difference between **И** and **І**: **бик** (bull) vs **бік** (side), **лис** (fox) vs **ліс** (forest). They are different sounds, different letters, different words.

**Г** — the voiced glottal fricative. This is not the Russian hard [г] and not the English "h." It is like saying English "h" but with your voice switched on — a breathy, voiced sound that comes from the throat. Words: **гарно** (beautifully), **гори** (mountains), **голова** (head), **гарячий** (hot). Now contrast with **Ґ** — the hard [g] sound, which exists in very few Ukrainian words: **ґанок** (porch), **ґудзик** (button), **ґречний** (polite). Think of **Г** as the default Ukrainian sound, appearing in thousands of words. **Ґ** is the rare exception — you can count the common Ґ-words on your fingers.

**Р** — rolled and trilled, similar to Spanish or Italian R. The tip of your tongue taps the ridge just behind your upper teeth. Practice: **рука** (hand), **робота** (work), **ранок** (morning), **риба** (fish). Even an imperfect Р is always understood — do not let it stop you from speaking. It improves naturally with practice.

<!-- INJECT_ACTIVITY: quiz-g-vs-g -->

These four sounds — **И**, **Г**, **Ґ**, **Р** — take time. The goal is not perfection today but awareness. You now know what to listen for, and your ear will sharpen with every Ukrainian word you hear.

## Підсумок — Summary

Four concepts from this module form the foundation for reading Ukrainian accurately. **Ь** (the soft sign) softens the consonant before it — it has no sound of its own. Words like **день**, **сіль**, and **кінь** all end with a softened consonant thanks to Ь. The apostrophe does the opposite: after **б**, **п**, **в**, **м**, **ф**, **р**, it keeps the consonant hard and gives **я**, **ю**, **є**, **ї** their full two-sound value. That is why **сім'я**, **м'ясо**, and **п'ять** sound the way they do. Voiced and voiceless consonants come in eight pairs, and unlike Russian, Ukrainian keeps consonants voiced at word end — **дуб** is [дуб], not *[дуп]. Finally, **И**, **Г**, and **Р** need practice, but awareness is the first step.

Self-check — answer these questions. What does Ь do to a consonant? After which six letters can the apostrophe appear? Name three voiced-voiceless pairs. How is **Г** different from **Ґ**? How is **И** different from English "ee"? If you can answer all five, you understand the special signs.

Final reading challenge — read these words aloud with confidence: **сім'я**, **день**, **п'ять**, **гарно**, **кінь**, **м'ясо**, **батько**, **риба**, **комп'ютер**, **учитель**. Each word uses something you learned today — a soft sign, an apostrophe, a tricky sound. If you can read all ten, you are ready for the next step: **наголос** — stress and melody.


<!-- TAB:Словник -->

### Обов'язкові та рекомендовані слова

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **сім'я́** | family | ім. | ж. |
| **м'я́со** | meat | ім. | с. |
| **га́рно** | beautifully, nicely | присл. |  |
| **ри́ба** | fish | ім. | ж. |
| **ба́тько** | father | ім. | ч. |
| **учи́тель** | teacher | ім. | ч. |
| **де́в'ять** | nine | числ. |  |
| **комп'ю́тер** | computer | ім. | ч. |
| **м'яки́й** | soft | прикм. |  |
| **рис** | rice | ім. | ч. |
| **рись** | lynx | ім. | ж. |
| **тверді** | hard (consonants) | прикм. |  |
| **пом'я́кшені** | softened (consonants) | прикм. |  |
| **тин** | fence | ім. | ч. |
| **тінь** | shadow | ім. | ж. |
| **син** | son | ім. | ч. |
| **синь** | blue expanse | ім. | ж. |
| **ка́мінь** | stone | ім. |  |
| **камі́н** | fireplace | ім. | ч. |
| **о́сінь** | autumn | ім. | ж. |
| **біль** | pain | ім. | ч. |
| **мить** | moment | дієсл. |  |
| **ра́дість** | joy | ім. | ж. |
| **мазь** | ointment | ім. | ж. |
| **мале́нький** | small | прикм. |  |
| **стіле́ць** | chair | ім. | ч. |
| **подві́р'я** | yard | ім. | с. |
| **буря́к** | beetroot | ім. | ч. |
| **бур'я́н** | weeds | ім. | ч. |
| **м'яч** | ball | ім. | ч. |
| **п'я́тниця** | Friday | ім. | ж. |
| **ім'я́** | name | ім. | с. |
| **здоро́в'я** | health | ім. | с. |
| **об'є́кт** | object | ім. | ч. |
| **дзвінки́й** | voiced (consonant) | прикм. |  |
| **глухи́й** | voiceless (consonant) | прикм. |  |
| **дзвони́ти** | to ring | дієсл. |  |
| **моро́з** | frost | ім. | ч. |
| **ба́лка** | beam | ім. | ж. |
| **па́лка** | stick | ім. | ж. |
| **коза́** | goat | ім. | ж. |
| **коса** | braid | ім. | ж. |
| **бик** | bull | ім. | ч. |
| **лист** | leaf | ім. | ч. |
| **зима́** | winter | ім. | ж. |
| **ти́хо** | quietly | присл. |  |
| **си́ній** | blue | прикм. |  |
| **бік** | side | ім. | ч. |
| **го́ри** | mountains | ім. | ж. |
| **голова́** | head | ім. | ч. |
| **гаря́чий** | hot | прикм. |  |
| **ґа́нок** | porch | ім. | ч. |
| **ґу́дзик** | button | ім. | ч. |
| **ґре́чний** | polite | прикм. |  |
| **рука́** | hand | ім. | ж. |
| **робо́та** | work | ім. | ч. |
| **ра́нок** | morning | ім. |  |
| **на́голос** | stress (word accent) | присл. |  |

### Картки — Flashcards

<FlashcardDeck client:only="react" cards={[{ front: "сім'я́", back: "family", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "м'я́со", back: "meat", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "га́рно", back: "beautifully, nicely", subtitle: "присл." }, { front: "ри́ба", back: "fish", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ба́тько", back: "father", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "учи́тель", back: "teacher", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "де́в'ять", back: "nine", subtitle: "числ." }, { front: "комп'ю́тер", back: "computer", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "м'яки́й", back: "soft", subtitle: "прикм." }, { front: "рис", back: "rice", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "рись", back: "lynx", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "тверді", back: "hard (consonants)", subtitle: "прикм." }, { front: "пом'я́кшені", back: "softened (consonants)", subtitle: "прикм." }, { front: "тин", back: "fence", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "тінь", back: "shadow", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "син", back: "son", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "синь", back: "blue expanse", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ка́мінь", back: "stone", subtitle: "ім." }, { front: "камі́н", back: "fireplace", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "о́сінь", back: "autumn", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "біль", back: "pain", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "мить", back: "moment", subtitle: "дієсл." }, { front: "ра́дість", back: "joy", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "мазь", back: "ointment", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "мале́нький", back: "small", subtitle: "прикм." }, { front: "стіле́ць", back: "chair", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "подві́р'я", back: "yard", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "буря́к", back: "beetroot", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "бур'я́н", back: "weeds", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "м'яч", back: "ball", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "п'я́тниця", back: "Friday", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ім'я́", back: "name", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "здоро́в'я", back: "health", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "об'є́кт", back: "object", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "дзвінки́й", back: "voiced (consonant)", subtitle: "прикм." }, { front: "глухи́й", back: "voiceless (consonant)", subtitle: "прикм." }, { front: "дзвони́ти", back: "to ring", subtitle: "дієсл." }, { front: "моро́з", back: "frost", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ба́лка", back: "beam", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "па́лка", back: "stick", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "коза́", back: "goat", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "коса", back: "braid", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "бик", back: "bull", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "лист", back: "leaf", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "зима́", back: "winter", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ти́хо", back: "quietly", subtitle: "присл." }, { front: "си́ній", back: "blue", subtitle: "прикм." }, { front: "бік", back: "side", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "го́ри", back: "mountains", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "голова́", back: "head", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "гаря́чий", back: "hot", subtitle: "прикм." }, { front: "ґа́нок", back: "porch", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ґу́дзик", back: "button", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ґре́чний", back: "polite", subtitle: "прикм." }, { front: "рука́", back: "hand", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "робо́та", back: "work", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ра́нок", back: "morning", subtitle: "ім." }, { front: "на́голос", back: "stress (word accent)", subtitle: "присл." }]} />


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

**Джерела — References**

- Захарійчук Grade 1 (NUS 2025), p.97
  _Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї._
- Захарійчук Grade 1 (NUS 2025), p.15
  _Hard [–] vs soft [=] consonant notation._
- Большакова Grade 1, p.45-47
  _Тверді і пом'якшені приголосні звуки._
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: special-signs
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

**Level: A1.1 (Module 3/55) — COMPLETE BEGINNER**

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
