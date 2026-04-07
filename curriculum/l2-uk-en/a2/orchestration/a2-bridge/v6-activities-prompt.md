<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-bridge.yaml` file for module **1: Ласкаво просимо до рівня А2** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: case-identification-drill -->`
- `<!-- INJECT_ACTIVITY: fill-in-phonology -->`
- `<!-- INJECT_ACTIVITY: match-up-euphony -->`
- `<!-- INJECT_ACTIVITY: error-correction-euphony -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Case Identification Drill
  items: 8
  type: quiz
- focus: Phonological Alternation Pairs
  items: 8
  type: fill-in
- focus: Euphony Choice Exercise
  items: 8
  type: match-up
- focus: Euphony Error Correction
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- милозвучність (euphony, melodiousness)
- огляд (review, overview)
- система (system)
- правило (rule)
required:
- відмінок (case)
- називний (nominative)
- знахідний (accusative)
- місцевий (locative)
- кличний (vocative)
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- наголос (stress (accent))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пригадуємо відмінки (Reviewing Cases)

> — **Новий студент:** Добрий ранок! Я — новий студент. *(Good morning! I am a new student.)*
> — **Оксана:** Привіт! Ласкаво просимо. Як справи? *(Hi! Welcome. How are you?)*
> — **Новий студент:** Дякую, добре. Я вивчаю українську мову. *(Thank you, fine. I am studying the Ukrainian language.)*
> — **Оксана:** Це чудово! Де ти зараз живеш? *(That is wonderful! Where do you live now?)*
> — **Новий студент:** Я живу в Києві. *(I live in Kyiv.)*
> — **Оксана:** Привіт, Оксано! — так ти можеш вітатися зі мною. *(Hi, Oksana! — this is how you can greet me.)*

In this short everyday exchange, the student and the teacher naturally used four completely different forms of nouns depending entirely on their specific role in the sentence.

The Nominative case, or **Називний відмінок** *(Nominative case)*, is the fundamental starting point for all words. It answers the questions **хто?** *(who?)* and **що?** *(what?)*. This is the exact dictionary form of a word that you always learn first. In a sentence, it almost always acts as the main subject—the person or thing performing the primary action. It simply names the object or person without any modifications. For example, «**урок** починається» *(the lesson begins)* or «**книга** лежить» *(the book lies)*. Here, the lesson and the book are the main actors driving the entire sentence forward.

When an action is directly applied to an object, we use the Accusative case, or **Знахідний відмінок** *(Accusative case)*. It answers the specific questions **кого?** *(whom?)* and **що?** *(what?)*. This form consistently acts as the direct object of the sentence. You must remember the critical rule for feminine nouns: the ending usually changes to **-у** or **-ю**. For example, you read «**книжку**» *(a book)* and drink «**каву**» *(coffee)*. However, masculine inanimate nouns stay exactly the same as they appear in the dictionary form. You start «**урок**» *(a lesson)* and buy «**стіл**» *(a table)* without changing the ending at all.

To talk about physical locations, we rely heavily on the Locative case, or **Місцевий відмінок** *(Locative case)*. It answers the simple question **де?** *(where?)*. A strict and unbreakable rule in Ukrainian grammar is that the Locative case is never used entirely alone; it is always paired with a preposition, usually **у/в** *(in/at)* or **на** *(on/at)*. When you want to clearly state where something is currently happening, you say «**у школі**» *(at school)*, «**в Ужгороді**» *(in Uzhhorod)*, or «**на заводі**» *(at the factory)*.

Finally, whenever we address someone directly in a conversation, we use the Vocative case, or **Кличний відмінок** *(Vocative case)*. It does not answer any specific questions. It is used purely for calling out to people or even inanimate things. This case is a vibrant, living marker of the authentic Ukrainian language. While it has largely disappeared from modern Russian, it remains absolutely mandatory in Ukrainian everyday speech. Using the Nominative case instead of the proper Vocative when addressing someone immediately sounds unnatural. You should always say «**друже**» *(friend)*, «**Олю**» *(Olia)*, and «**вчителю**» *(teacher)*.

These four cases form the absolute core of your ability to make basic statements, describe direct actions, specify locations, and interact politely with people. However, the complete Ukrainian noun system actually consists of seven cases in total. To reach true A2 level fluency, you will soon master the remaining three missing pieces of the grammar puzzle: the Genitive case to show absence or possession, the Dative case to indicate the recipient of an action, and the Instrumental case to describe the specific tool used to perform an action.

<!-- INJECT_ACTIVITY: case-identification-drill -->

## Магія української фонології (The Magic of Ukrainian Phonology)

A closed syllable is one that ends in a **приголосний** *(consonant)*. When a word is in its dictionary form, the last syllable is often closed, and the **голосний** *(vowel)* **і** feels right at home. For example, you say «**стіл**» *(a table)*, «**Київ**» *(Kyiv)*, and «**вечір**» *(evening)*. However, when you add a case ending that starts with a **голосний**, you open up that syllable. That **і** transforms back into its original historical vowel, which is usually **о** or **е**. Therefore, you do not say "стіла", but rather «**стола**» *(of a table)*. You travel to «**Києва**» *(of Kyiv)*, not "Київа", and you wait for «**вечора**» *(of an evening)*. Recognizing this pattern helps you predict how words behave.

Vowels are not the only sounds that change in Ukrainian grammar. A **приголосний** can also undergo predictable transformations, a process we call mutation or palatalization. The first major pattern of consonant mutation affects the sounds **г**, **к**, and **х**. Historically, when these consonants met certain vowels, they shifted into the softer sounds **ж**, **ч**, and **ш**. You will encounter this historical shift constantly when forming affectionate diminutives. For instance, the word «**нога**» *(a leg)* has a hard **г**. But if you want to talk about a small leg, it becomes a «**ніжка**» *(a little leg)*, where the **г** turns into a **ж**. Similarly, a «**рука**» *(a hand)* transforms into a small «**ручка**» *(a little hand)*, changing **к** to **ч**. And an «**вухо**» *(an ear)* becomes a tiny «**вушко**» *(a little ear)*, shifting **х** to **ш**.

The second major pattern of consonant mutation is absolutely critical for mastering the Locative and Dative cases. This transformation occurs specifically when the hard consonants **г**, **к**, and **х** are immediately followed by the vowel ending **-і**. In these specific grammatical situations, they soften into the sounds **з**, **ц**, and **с**. If you forget this rule, your Ukrainian will sound unnatural to native speakers. Let us look at some everyday examples. If you are walking on a «**дорога**» *(a road)*, you must say that you are «**на дорозі**» *(on the road)*, where **г** becomes **з**. If you are holding a phone in your «**рука**» *(hand)*, you hold it «**в руці**» *(in the hand)*, changing **к** to **ц**. And if you want to give a crumb to a «**муха**» *(a fly)*, you give it to the «**мусі**» *(to the fly)*, shifting **х** to **с**.

Beyond the letters themselves, the melody of Ukrainian relies heavily on word stress, or **наголос** *(stress/accent)*. Unlike languages where the stress always falls on a predictable syllable, the Ukrainian **наголос** is free and mobile. It can land anywhere in a word, and it can even move around when a word changes its grammatical form. Sometimes, the placement of the **наголос** is the only thing that distinguishes two completely different words, known as homographs. A classic example is the word spelled "замок". If you place the **наголос** on the first syllable, it is a «**замок**» *(a castle)*. But if you shift the **наголос** to the final syllable, it suddenly becomes a «**замок**» *(a lock)*. Paying close attention to where native speakers place their emphasis is just as important as learning the correct vowels and consonants.

Another fascinating aspect of Ukrainian phonology is how certain consonants blend together. You have probably noticed the letter combinations **дз** and **дж**. It is crucial to understand that these are not two separate sounds forcefully pushed together; they represent single, unified sounds called affricates. You should pronounce them as one smooth motion, just like you hear in «**дзвінок**» *(a bell)* or «**бджола**» *(a bee)*. Furthermore, a **приголосний** sometimes influences the voicing of its immediate neighbor to make pronunciation physically easier. This is called voicing assimilation. When a voiceless **приголосний** stands right before a voiced one, it borrows some of that voice. For example, the word «**просьба**» *(a request)* has a voiceless **с** followed by a voiced **б**. In natural speech, that **с** sounds exactly like a **з**, so we pronounce it as [проз'ба]. Likewise, in the word «**вокзал**» *(a train station)*, the voiceless **к** before the voiced **з** sounds just like a **ґ**, making the pronunciation [воґзал].

The mobility of the **наголос** does not just create homographs; it also plays a huge role in the everyday declension of nouns. As you learn new words, you will discover that the **наголос** often shifts between the main stem of the word and its grammatical ending, depending entirely on the case or the number. A very common pattern involves feminine nouns. Let us take the word «**вода**» *(water)*. In the Nominative case, the **наголос** falls heavily on the final **-а**. But when you want to drink that water and use the Accusative case, the **наголос** jumps back to the stem, and you ask for «**воду**» *(water)*. A similar shift happens with body parts. You have one «**рука**» *(hand)*, with the **наголос** at the very end. However, if you are talking about both of your hands in the plural, the **наголос** moves to the first syllable, giving you «**руки**» *(hands)*. Noticing these rhythmic shifts will help you predict the correct pronunciation.

<!-- INJECT_ACTIVITY: fill-in-phonology -->

## Милозвучність мови: евфонія (The Melody of Language: Euphony)

The law of euphony, or «**милозвучність**» *(melodiousness)*, requires a delicate, rhythmic balance between a **голосний** *(vowel)* and a **приголосний** *(consonant)*. To prevent the awkward clashing of too many consonants or a sudden sequence of vowels, the language actively shifts its prepositions and conjunctions.

The most common euphonic shift you will encounter every single day is the alternation between the prepositions «**у**» *(in/at)* and «**в**» *(in/at)*. The primary rule is designed to prevent a heavy cluster of consonants that would disrupt the melody of the sentence. If the preceding word ends in a **приголосний** and the following word begins with a **приголосний**, you must use «**у**» to create a necessary vocalic bridge. For example, you say «**був у школі**» *(he was at school)*. However, if the preceding word ends in a **голосний**, you use «**в**» to maintain the rhythmic flow, resulting in «**була в школі**» *(she was at school)*. This tiny adjustment ensures that your sentences sound completely natural and effortless.

Similarly, the essential conjunction meaning "and" alternates between «**і**» and «**й**» to maintain this crucial rhythm. The principle remains exactly the same as with our prepositions. When you are connecting two words that would otherwise create a harsh cluster of consonants, you insert the **голосний** «**і**» to separate them smoothly. For instance, you naturally say «**він і вона**» *(he and she)*. But when the preceding word ends in a **голосний**, using another full vowel would create a sudden, staccato pause. To avoid this unnatural break, you use the consonant «**й**», allowing the words to glide together perfectly, as you hear in the phrase «**ти й я**» *(you and I)*.

Finally, Ukrainian employs special "protective" particles to handle particularly difficult consonant clusters, specifically with the preposition meaning "with" or "from". While the standard, everyday form is «**з**» *(with/from)*, it seamlessly transforms into «**із**» *(with/from)* or «**зі**» *(with/from)* when placed before words starting with multiple challenging consonants. This brilliant mechanism prevents your tongue from stumbling over complex sounds. For example, the cluster «**мн**» is quite difficult to pronounce immediately after another **приголосний**, so we always say «**зі мною**» *(with me)* instead of forcing the sounds together. Likewise, to maintain an elegant flow before combinations like «**зд**» or «**св**», we rely on these extended forms. You will often hear native speakers warmly say «**із задоволенням**» *(with pleasure)* or greet each other with «**зі святом**» *(happy holiday)*. Paying close attention to these small protective words will instantly make your spoken Ukrainian sound incredibly fluent and sophisticated.

<!-- INJECT_ACTIVITY: match-up-euphony -->
<!-- INJECT_ACTIVITY: error-correction-euphony -->

## Що нас чекає на рівні А2? (Summary & Roadmap)

The A2 curriculum introduces the Ukrainian verbal aspect. We will deeply explore the crucial difference between the imperfective and perfective forms, which is truly the beating heart of the Ukrainian verb system. You will learn exactly when an action is an ongoing process and when it is a successfully completed result. Next, we will tackle the fascinating verbs of motion, learning precisely why we use «**іти**» *(to go by foot)* in one specific situation and «**їхати**» *(to go by vehicle)* in another. Finally, we will complete your noun declension map by introducing the remaining three cases: the Genitive, the Dative, and the Instrumental.

Can you confidently answer these three fundamental questions?

* «**Які чотири відмінки ви вже знаєте?**» *(Which four cases do you already know?)* You should immediately recognize and name the Nominative, Accusative, Locative, and the uniquely Ukrainian Vocative case.
* «**Що таке чергування о/і?**» *(What is the o/i alternation?)* You must remember that this is the natural shift of a **голосний** that occurs whenever a word forms a closed syllable.
* «**Коли ми використовуємо "зі"?**» *(When do we use "zi"?)* You should easily recall that this protective euphonic particle always appears before heavy consonant clusters, exactly as you hear in the common phrase «**зі мною**» *(with me)*.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-bridge
level: a2

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
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

**Level: A2 (Module 1/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
