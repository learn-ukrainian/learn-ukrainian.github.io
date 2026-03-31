<!-- version: 1.0.0 | updated: 2026-03-27 -->
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

(No injection markers found in prose. All activities will go to workbook.)

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

> **Викладач:** Добрий день! Ласкаво просимо на курс А2. Як вас звати?
>
> **Майкл:** Добрий день! Мене звати Майкл. Я з Канади.
>
> **Викладач:** О, з Канади! Дуже цікаво. А скільки вам років?
>
> **Майкл:** Мені двадцять п'ять років.
>
> **Викладач:** Чудово! Що ви вивчаєте?
>
> **Майкл:** Я вивчаю українську мову. Я дуже люблю Україну.
>
> **Викладач:** А де ви зараз живете?
>
> **Майкл:** Я живу в Києві. У мене маленька квартира біля метро.
>
> **Викладач:** Прекрасно! Дуже приємно, Майкле! Сідайте, будь ласка.

Did you notice? In that short conversation, Майкл and the teacher used four different case forms without thinking about it. «З Канади» — the noun changed. «Мені» — another form. «Українську мову» — the adjective and noun both changed. «В Києві» — yet another ending. And at the very end, even Майкл's own name shifted: «Майкле!»

Помітили? Ви вже знаєте чотири **відмінки** *(cases)*. In A1, you learned to use these forms in real conversations — now it's time to name them and understand why the endings change. The key diagnostic tool is simple: the question a word answers reveals its **відмінок**. Each case has its own question pair, and once you know them, you can identify any case instantly.

### Називний відмінок (Nominative — Хто? Що?)

The **називний** *(nominative)* case is the dictionary form — the form you find when you look up a word. It marks the subject of a sentence and answers **Хто?** *(Who?)* for living beings and **Що?** *(What?)* for things.

Adjectives in the nominative agree with their noun in gender:

- Masculine: **новий студент** *(new student)*, **цікавий підручник** *(interesting textbook)*
- Feminine: **нова книга** *(new book)*, **українська мова** *(Ukrainian language)*
- Neuter: **нове місто** *(new city)*, **велике вікно** *(big window)*

Це цікавий підручник. Марія — студентка. Київ — велике місто.

Think of the називний as your starting point. Every other case is a *change* from this base form — a different ending that signals a different role in the sentence.

### Знахідний відмінок (Accusative — Кого? Що?)

The **знахідний** *(accusative)* case marks the direct object — the thing or person receiving the action. It answers **Кого?** *(Whom?)* for animate nouns and **Що?** *(What?)* for inanimate ones.

Three patterns to remember:

**Feminine nouns** change their ending: книга → книгу, кава → каву, земля → землю. The -а becomes -у, the -я becomes -ю.

**Masculine inanimate nouns** stay the same as називний: підручник → підручник, урок → урок. Хто? Що? and Кого? Що? look identical — context tells you the difference.

**Masculine animate nouns** add -а or -я, just like the родовий case — a key rule you'll use constantly: студент → студента, учитель → учителя.

Here are natural verb-noun pairs you already know:

Я читаю книгу. Олена п'є каву. Ти знаєш відповідь. Ми любимо Україну. Вони бачать студента.

### Місцевий відмінок (Locative — Де? На чому? В чому?)

The **місцевий** *(locative)* case answers **Де?** *(Where?)*, **На чому?** *(On what?)*, **В чому?** *(In what?)*. It has one absolute rule: місцевий *never* appears without a **прийменник** *(preposition)*. The prepositions в/у, на, при, and по always come before it.

Look at these city names — each one takes the ending -і:

Я живу в Києві. Вона вчиться у Харкові. Ми були у Львові.

The same ending appears with common nouns: на уроці, в університеті, при школі, по дорозі.

Soft-stem neuter nouns also take -і: місто → у місті, море → на морі.

Remember the dialogue? «Я живу в Києві» — that's місцевий in action. The preposition в plus the ending -і together signal location.

### Кличний відмінок (Vocative — Звертання)

The **кличний** *(vocative)* case is the case of direct address — you use it when calling someone by name or title. This case is uniquely important in Ukrainian. It shows respect and warmth.

Hard-stem masculine nouns take **-е**: Тарас → Тарасе, друг → друже, хлопець → хлопче.

Soft-stem masculine nouns take **-ю**: Сергій → Сергію, Василь → Василю.

Feminine nouns ending in -а take **-о**: мама → мамо, Ганна → Ганно. Feminine nouns ending in -ія take **-є**: Марія → Маріє.

Some forms are fixed: тато → тату.

Remember how the teacher ended the dialogue? «Дуже приємно, Майкле!» That's кличний — the teacher addressed Майкл directly, and his name changed to show it.

Привіт, Сергію! Мамо, де моя книга? Друже, ходімо на каву!

<!-- INJECT_ACTIVITY: quiz, Case Identification Drill -->

### Сім відмінків (The Full Case Map)

Now let's see the complete picture — all seven Ukrainian cases. Four you already know from A1. Three new ones await you in the coming modules.

| | Відмінок | Питання | Функція | Приклад |
|---|---|---|---|---|
| ✅ | Називний | Хто? Що? | Subject | студент читає |
| ✅ | Знахідний | Кого? Що? | Direct object | бачу студента |
| ✅ | Місцевий | Де? На чому? | Location | у Києві |
| ✅ | Кличний | — | Direct address | Майкле! |
| 🔜 | Родовий | Кого? Чого? | Possession, negation | книга студента |
| 🔜 | Давальний | Кому? Чому? | Recipient, age | мені двадцять п'ять |
| 🔜 | Орудний | Ким? Чим? | Means, company | пишу ручкою |

The **родовий** *(genitive)* case shows possession and appears after negation. The **давальний** *(dative)* marks the recipient of an action and expresses age. The **орудний** *(instrumental)* shows the tool or means used, and the person you do something *with*.

Три нові відмінки — це три нові способи виражати думки. Почнемо вже в наступному модулі.


## Магія української фонології (The Magic of Ukrainian Phonology)

Ukrainian words change in ways that can surprise you at first. You learned that **стіл** means *table* — so why does the genitive form become **стола**? That і disappeared, and an о appeared in its place. This is not an exception. This is a **чергування** *(alternation)* — a predictable sound change built into the language. Ukrainian has two categories of alternations: **чергування голосних** *(vowel alternations)* and **чергування приголосних** *(consonant alternations)*. Both follow clear rules based on two triggers: whether a syllable is **закритий** *(closed)* or **відкритий** *(open)*, and which consonant sits before a front vowel. After this section, you will understand *why* стіл becomes стола — not just memorize it.

### Чергування о/і (The О/І Vowel Alternation)

This is the most important vowel alternation in Ukrainian. The rule is elegant: when a **склад** *(syllable)* is **закритий** — meaning it ends in a consonant with no vowel after it — the vowel becomes **і**. When an ending adds a vowel and the syllable **opens**, the і reverts to **о**. Look at these four anchor pairs:

| Називний (закритий склад) | Родовий (відкритий склад) |
|---|---|
| стіл | стола |
| кіт | кота |
| ніч | ночі |
| піч | печі |

In the називний form, the word ends in a consonant — the syllable is closed, so the vowel is **і**. In the родовий, the ending -а or -і opens the syllable, and the vowel shifts back to **о** or **е**.

Ось речення з обома формами: «На столі стоїть новий стіл.» The місцевий form **столі** keeps the і because the stress pattern preserves the closed-syllable quality — but the root vowel tells you exactly what happened historically.

### Чергування е/і (The Е/І Alternation)

The same closed-syllable rule governs another set of words — but here the vowel alternates between **е** and **і** instead of о and і. These are two expressions of one phenomenon, just with different historical source vowels.

Корінь → кореня. Камінь → каменя. Осінь → осені.

In the називний, the syllable is closed: **корінь**, **камінь**, **осінь** — all with і. In the родовий, the ending -я or -і opens the syllable, and і becomes е: **кореня**, **каменя**, **осені**.

You will not need to produce these forms from scratch at this stage. You will encounter them in case endings and need to *recognize* the pattern. Practical tip: when a родовий or давальний form looks unfamiliar, check whether the називний has і — if it does, the open-syllable form likely restores о or е. Це одне правило — два варіанти.

### Чергування приголосних (Consonant Alternations)

Ukrainian consonants also alternate — and they follow a three-way pattern. The consonants **г**, **к**, **х** each have two alternate forms depending on the grammatical context.

| Основа | Перша зміна (ж/ч/ш) | Друга зміна (з/ц/с) |
|---|---|---|
| г → | ж (нога → ніжка) | з (нога → нозі) |
| к → | ч (рука → ручка) | ц (рука → руці) |
| х → | ш (вухо → вушко) | с (вухо → у вусі) |

The first change (г→ж, к→ч, х→ш) appears in diminutives and some verb forms. The second change (г→з, к→ц, х→с) appears in the **місцевий** case singular — the very case you reviewed in the previous section.

«Я пишу рукою — але я тримаю ручку.»

«Де моя рука? На руці — браслет.»

These consonant alternations directly preview the місцевий endings you will build in A2 modules 3–5. When you see руці instead of руки, you now know why.

In verbs, the same pattern appears: пекти → печу (к→ч), бігти → біжу (г→ж), їхати → їду (х drops entirely). Ці зміни — не випадкові. Вони системні.

### Наголос як розрізнювач значень (Stress as a Meaning-Differentiator)

Ukrainian **наголос** *(stress)* is **вільний** *(free)* — it is not fixed to a particular syllable position the way it is in Polish or French. It is also **рухомий** *(mobile)* — it can shift from one syllable to another within the same word's paradigm.

This means stress can change meaning entirely. **Замок** with stress on the first syllable means *castle*. **Замок** with stress on the second syllable means *lock*. **Атлас** with first-syllable stress means *atlas* (a book of maps). **Атлас** with second-syllable stress means *satin fabric*.

Stress also shifts within paradigms: рука (називний) → руки (родовий однини) → руки (називний множини). Сестра → сестри → сестер. The word changes its stress depending on case and number.

Practical advice: Ukrainian dictionaries always mark stress. Use goroh.pp.ua to check any new word. Запам'ятовуйте наголос разом зі словом — не лише літери.

### Чергування приголосних у дієсловах (Verb Consonant Alternations Preview)

The same г/к/х → ж/ч/ш pattern appears in verb conjugation — specifically in the **first person singular** present tense. This makes the phonology you just learned directly actionable.

Писати → пишу (с→ш). Казати → кажу (з→ж). Їздити → їжджу (зд→жд). Просити → прошу (с→ш). Водити → воджу (д→дж).

This is a bonus payoff: if you understand the consonant alternation pattern, you already know why these verb forms look different from their infinitives. You will not need to memorize each form as a separate exception — the pattern is the same one you saw in nouns.

«Я кажу вам: ця закономірність — системна.»

When you reach verb conjugation tables in later A2 modules, these changes will feel familiar. Фонологія — ваш найкращий друг.

<!-- INJECT_ACTIVITY: fill-in, Phonological Alternation Pairs -->


## Милозвучність мови: евфонія (The Melody of Language: Euphony)

The phonological patterns you just reviewed — vowel and consonant alternations — serve a deeper purpose. Ukrainian actively avoids dissonant sound clusters through alternating variant pairs. This is not optional style — it is the norm. The term for this quality is **милозвучність** *(euphony, melodiousness)* — literally, «милозвучна мова» means *melodious language*. Three alternating pairs to master at A2: **у/в**, **і/й**, and **з/зі/із**. Consider this sentence from a Ukrainian textbook exercise: «В ваших родинах панує злагода.» Read it aloud. The «в в» collision grates against the ear. The correct form flows naturally: «У ваших родинах панує злагода.»

### У/В

The core rule is simple: **after a vowel, use в**; **after a consonant or at the start of a sentence before a consonant, use у**.

«Я в університеті.»

The word «я» ends in a vowel — so «в» follows.

«Він у університеті.»

The word «він» ends in a consonant — so «у» follows.

The same logic applies everywhere:

«Ми в Харкові.» — «ми» ends in a vowel.

«Студент у Харкові.» — «студент» ends in a consonant.

At the beginning of a sentence, check the first sound of the next word. Before a consonant, use «у»: «У Києві є метро.» Before a vowel, use «в»: «В Одесі є море.»

A common learner error: «В вторник.» This is wrong in two ways — «вторник» is a Russian word, and «в в» breaks euphony. The correct Ukrainian form: «У вівторок.»

### І/Й

The same phonetic logic governs the conjunction **і/й** *(and)*: **after a consonant or at sentence start, use і**; **after a vowel, use й**.

«Мати і батько.» — «мати» ends in a vowel? No — the sound is [и], classified as a vowel, so this seems contradictory. The practical rule: «і» is the default form, «й» appears after clear open vowels.

«Батько й мати.» — «батько» ends in [о], a vowel — so «й» follows.

«Марія й Олег.» — «Марія» ends in [а] — so «й».

«Олег і Марія.» — «Олег» ends in a consonant — so «і».

Note: both the **сполучник** *(conjunction)* і/й and the **прийменник** *(preposition)* у/в obey the same vowel-consonant logic. Russian «и» has no such alternation. Милозвучність — це суто українська риса.

### З/Зі/Із

The preposition **з** *(from, with)* has three forms. Use «з» before most words starting with a single consonant or a vowel: «з Канади», «з Києва», «з тобою.» Use **зі** before consonant clusters that are hard to pronounce — especially лв-, шк-, зл-, зб-: «зі Львова», «зі школи», «зі зламаним замком.» Use **із** before words starting with з- or с-: «із Запоріжжя», «із сестрою.»

The rule of thumb: whichever variant flows most smoothly when you say it aloud is almost always correct.

<!-- INJECT_ACTIVITY: match-up, Euphony Choice Exercise -->

Милозвучність becomes automatic with exposure. Native speakers do not consciously apply these rules — they hear what sounds natural. For learners, the best practice is simple: read Ukrainian text aloud, paying attention to transitions between words. When something sounds awkward — two consonants colliding, two vowels bumping — that is your ear signaling a euphony error. Спробуйте читати вголос щоразу, коли вивчаєте нові тексти. By B1, these choices will feel natural rather than calculated.


## Що нас чекає на рівні А2? (What Awaits Us in A2?)

At A1, you learned four cases — enough to name things, point to them, say where you are, and call someone by name. Three new cases will unlock the rest of Ukrainian communication.

**Родовий відмінок** *(Genitive case)* answers «Кого? Чого?» and expresses what English handles with "of," "no," and quantity words. Right now you cannot say whose book it is. After Genitive: «Це книга **брата**.» You cannot negate existence. After Genitive: «У мене нема **часу**.» You cannot count beyond one. After Genitive: «Багато **студентів** приїхали з різних країн.»

**Давальний відмінок** *(Dative case)* answers «Кому? Чому?» — it marks the recipient, the person affected. «Я дав книгу **другові**.» Remember the dialogue? «**Мені** двадцять п'ять років.» That was Dative — age in Ukrainian belongs to the person, not describes them. Obligation works the same way: «**Студентам** треба вчитися щодня.»

**Орудний відмінок** *(Instrumental case)* answers «Ким? Чим?» — the tool, the companion, the profession. «Я пишу **ручкою**.» «Я іду **з другом** у кафе.» «Він є **лікарем**.» These three patterns — tool, company, identity — appear in nearly every Ukrainian conversation.

Aspect is the conceptual heart of A2. Ukrainian verbs come in pairs: **недоконаний вид** *(imperfective)* for ongoing or repeated actions, **доконаний вид** *(perfective)* for completed, single events. «Я **читав** цю книгу щодня.» — a habit, repeated. «Я **прочитав** цю книгу вчора.» — finished, done. Core pairs to learn: читати/прочитати, писати/написати, говорити/сказати, робити/зробити. Dedicated modules on aspect begin in A2.2.

Ukrainian also has a dedicated system for **дієслова руху** *(verbs of motion)*. Two core pairs: **іти/ходити** *(on foot)* and **їхати/їздити** *(by vehicle)*. «Я **іду** зараз на урок.» — one direction, right now. «Я **ходжу** на уроки щодня.» — habitual, repeated. Prefixes transform meaning entirely: при-їхати *(arrive)*, ви-їхати *(depart)*, пере-їхати *(cross)*. Mastering motion verbs unlocks travel, daily routines, and storytelling.

A1 gave you simple facts. A2 is the inflection point — you begin to **explain**, **compare**, and **narrate**. Пригадайте початок уроку. Майкл сказав: «Я з Канади» і «Я живу в Києві.» By the end of A2, he will say: «Книга, яку я купив **у центрі міста**, написана **відомим українським автором**.» Шлях починається тут.

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

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 1/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress
- **quiz** — Де наголос?: Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Pick the word with different stress pattern

### Pattern: grammar-cases
- **fill-in** — Який відмінок?: Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Find wrong case ending and correct it


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

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

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
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
