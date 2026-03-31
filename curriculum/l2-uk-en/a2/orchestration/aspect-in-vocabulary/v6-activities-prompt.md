<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-vocabulary.yaml` file for module **3: Дієслова ходять парами** (a2).

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

- focus: Find the Partner (Verb Matching)
  items: 8
  type: quiz
- focus: Categorize by Formation Type
  items: 8
  type: fill-in
- focus: Fill in the Blanks with the Correct Pair
  items: 8
  type: match-up
- focus: Sentence Translation (Aspect Focus)
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- утворювати (to form)
- словник (dictionary)
- запам'ятовувати (to memorize)
- базовий (basic)
required:
- пара (pair)
- префікс (prefix)
- суфікс (suffix)
- корінь (root)
- читати / прочитати (to read)
- писати / написати (to write)
- брати / взяти (to take)
- говорити / сказати (to speak / to say)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs)

Два речення — одне слово змінилося:

> «Я писала листа цілий вечір.»

> «Я написала листа.»

Both sentences describe writing a letter. Both use the same root — *пис-*. But the first sentence stretches across an entire evening: the writing was happening, unfinished, ongoing. The second sentence lands like a stamp on an envelope: done. The letter exists. What changed? A single prefix — **на-** — transformed the verb from a process into a result. This is not decoration. This is the core engine of how Ukrainian verbs work.

In Ukrainian, most verbs live as a **видова пара** *(aspect pair)* — two forms that belong together like inhale and exhale. One form describes the **process** — the action unfolding, repeated, or habitual. This is the **недоконаний вид** *(imperfective aspect)*, and it answers the question **що робити?** The other form describes the **completed result** — the action finished, achieved once, done. This is the **доконаний вид** *(perfective aspect)*, answering **що зробити?** From now on, every verb you learn has a standard notation: imperfective **/** perfective. Not just «писати» — but «**писати / написати**» *(to write / to have written)*. Learning only one form is like owning one chopstick — a real object, but useless without its partner.

Here is the practical consequence: from today, every new verb in your notebook gets two slots. When you look up a word on slovnyk.ua or e2u.org.ua, you will see both forms listed together. Ukrainian school textbooks do exactly this — Заболотний's Grade 6 textbook (§52) introduces **вид дієслова** by always showing the pair side by side. Dictionaries mark them: **недок.** *(imperfective)* and **док.** *(perfective)*. If you find only one form, search for its partner before moving on.

Think of two columns in your mind:

**Недоконаний вид** — process, duration, repetition. **Доконаний вид** — completed action, one-time result. Three structural patterns explain how most pairs are formed. Some pairs differ by a prefix: «писати / **на**писати». Some change a suffix or vowel: «запитувати / запитати» *(to ask, repeatedly / to ask, once)*. And a few are completely different words: «брати / взяти» *(to take — process / to take — completed)*. You will learn all three patterns in the sections ahead.

But first — aspect in action:

> **Бабуся:** «Ліпи вареники — ось так, знову і знову.»
>
> **Онучка:** «Я зліпила перший!»
>
> **Бабуся:** «Чудово! Тепер вари їх рівно десять хвилин.»
>
> **Онучка:** «А скільки ще варити?»
>
> **Бабуся:** «Як тільки звариш — вони спливуть на поверхню.»

Notice the pairs: **ліпити / зліпити** *(to shape, keep going / to finish shaping one)* and **варити / зварити** *(to boil, ongoing / to finish boiling)*. Бабуся says «ліпи» — keep forming, one after another, the process continues. Онучка says «зліпила» — one varenyк is done, result achieved. «Вари десять хвилин» — the boiling is a process with duration. «Звариш» — the moment they are fully cooked, finished.

The recipe makes the distinction concrete: every kitchen instruction switches between «keep doing this» and «finish doing that.»


## Спосіб 1: Додавання префікса

The most common way to form a perfective verb in Ukrainian is to add a **префікс** *(prefix)* to the imperfective base. The prefix seals the action — it signals that the verb now describes a completed act with a concrete result. But here is the critical detail: the prefix assigned to each pair is fixed. You cannot guess it. You must learn «писати / **на**писати» as a single unit, the same way you learned «видова пара» in the previous section — two forms, one meaning, always together.

Here are five core pairs. Notice how each prefix is different — and how the meaning stays the same, only the completion changes:

**писати / написати** *(to write / to write — completed)*

> «Вона **писала** повідомлення п'ять хвилин.»
> «Вона **написала** повідомлення.»

**читати / прочитати** *(to read / to read — completed)*

> «Ми **читали** книжку цілий тиждень.»
> «Ми **прочитали** її вчора.»

**робити / зробити** *(to do, to make / to do — completed)*

> «Він **робив** домашнє завдання.»
> «Він **зробив** усе завдання.»

**бачити / побачити** *(to see / to see — completed)*

> «Я часто **бачила** його в метро.»
> «Я **побачила** його вчора на вулиці.»

**готувати / приготувати** *(to cook, to prepare / to cook — completed)*

> «Мама **готувала** вечерю годину.»
> «Мама **приготувала** борщ.»

Five verbs, five different prefixes: **на-**, **про-**, **з-**, **по-**, **при-**. Each one is the assigned prefix for that particular verb. Swapping them produces either a wrong word or a completely different meaning.

Now five more pairs from everyday A2 vocabulary. The same principle holds — each verb has its own fixed prefix:

- **варити / зварити** *(to boil / to boil — completed)* — prefix **з-**
- **вчити / вивчити** *(to study / to learn — completed)* — prefix **ви-**
- **їсти / з'їсти** *(to eat / to eat — completed)* — prefix **з-**
- **пити / випити** *(to drink / to drink — completed)* — prefix **ви-**
- **малювати / намалювати** *(to draw, to paint / to draw — completed)* — prefix **на-**

Notice the variety: **з-**, **ви-**, **на-**. There is no universal rule that tells you which prefix goes with which verb. «Вчити» takes **ви-**, but «їсти» takes **з-**. Each pair must be memorized as a unit.

One important warning. A prefix on a verb does not always create a simple aspectual partner. Compare two prefixed forms of «писати»:

> «**Написати** листа.» — to write a letter *(completed)*
> «**Підписати** документ.» — to sign a document

«Написати» is the perfective partner of «писати» — same meaning, just completed. But «підписати» is a different verb entirely, with a new meaning. The prefix **під-** shifted the action from writing to signing. Here is your test: does the prefixed verb mean the same thing as the imperfective, only completed? If yes — it is an aspectual pair. If the meaning changed — it is a new verb, not a partner.

<!-- INJECT_ACTIVITY: quiz, Find the Partner — match imperfective verb to correct perfective from three options; items: писати, читати, бачити, їсти, пити, малювати, готувати, вчити; distractors use plausible-but-wrong prefixes (e.g., записати for читати) -->

Five more pairs to build your recognition range. These use slightly less obvious patterns:

- **розповідати / розповісти** *(to tell, to narrate / to tell — completed)*
- **забувати / забути** *(to forget — habitual / to forget — once)*
- **відкривати / відкрити** *(to open — process / to open — completed)*
- **закривати / закрити** *(to close — process / to close — completed)*
- **починати / почати** *(to begin — process / to begin — completed)*

Look closely at «розповідати / розповісти» — the root itself changes: **розповід-** becomes **розповіст-**. And «забувати / забути» drops the **-ва-** suffix entirely. These pairs still use prefixes, but something else is happening inside the word too. That pattern — changes in the root or suffix — is exactly what the next section explores.

Now read these five sentences aloud. For each verb in bold, decide: is it imperfective or perfective?

> «Я щодня **читаю** новини. Сьогодні вже **прочитав** дві статті.»

> «Він **робив** вправи і нарешті **зробив** усі правильно.»

> «Вона **готувала** тісто й **приготувала** пиріг до обіду.»

> «Ми **вчили** слова і **вивчили** всі п'ятнадцять.»

> «Він **пив** каву та **випив** цілу чашку.»

Each sentence pairs a process with its result. The first verb stretches across time — the second one lands.


## Спосіб 2: Зміна в корені або суфіксі

The previous section showed how a prefix turns an imperfective verb into its perfective partner. But Ukrainian has a second pattern that works in the opposite direction. When a perfective verb — often one that already carries a prefix — needs an imperfective partner, Ukrainian builds one by adding a suffix, most commonly **-ува-** or **-юва-**, or by shifting a vowel inside the root. Linguists call this process **imperfectivization** — creating an imperfective from a perfective base. The result is a longer, softer-sounding verb. Compare: **запитати** *(to ask — completed)* is short and decisive, while **запитувати** *(to ask — ongoing)* stretches out with that **-ува-** ending. When you hear **-увати** or **-ювати** at the end of a verb, you can be almost certain it is imperfective.

The **-ува-** suffix is the most productive pattern. Here are four core pairs with model sentences that show the contrast between completed and ongoing action:

- **запитати / запитувати** *(to ask — once / to ask — repeatedly)*

> «Вона **запитала** мене про адресу.»

> «Він завжди **запитує** мене про погоду.»

- **вирішити / вирішувати** *(to decide, to solve — completed / to decide, to solve — process)*

> «Ми **вирішили** проблему.»

> «Вони довго **вирішували**, куди їхати.»

- **відповісти / відповідати** *(to answer — once / to answer — regularly)*

> «Студент **відповів** на питання.»

> «Вона **відповідає** на листи кожного ранку.»

- **показати / показувати** *(to show — once / to show — repeatedly)*

> «Він **показав** мені карту.»

> «Учителька **показує** нові слова на дошці.»

Notice the consistent direction: the perfective ends in **-ати** or **-іти**, and the imperfective partner stretches it out to **-увати** or **-ювати**. The suffix is a reliable signal — it marks the verb that describes the process, not the result. If you see **-увати** at the end, you are looking at the imperfective member of the pair.

Now the second sub-pattern within Method 2: vowel alternation inside the root. Instead of adding a suffix, Ukrainian shifts the root vowel — most commonly **о → а** — to create the imperfective partner.

- **допомогти / допомагати** *(to help — completed / to help — ongoing)*

> «Він **допоміг** мені вчора.»

> «Вона завжди **допомагає** друзям.»

- **забути / забувати** *(to forget — once / to forget — habitually)*

> «Я **забув** ключі вдома.»

> «Він часто **забуває** речі.»

- **зрозуміти / розуміти** *(to understand — at a moment / to understand — ongoing)*

> «Вона **зрозуміла** завдання одразу.»

> «Я поступово **розумію** більше.»

Look at the roots: **допомог-** becomes **допомаг-** — the **о** stretches into **а**. This is not an irregularity. It is a phonological feature of Ukrainian. The vowel change signals duration, just as the **-ува-** suffix does. The imperfective form sounds longer and more open — it mirrors the open, ongoing nature of the action.

Sometimes both changes happen at once — the root vowel shifts AND the ending changes. Take **розповісти / розповідати** *(to tell — completed / to tell — ongoing)*: the root changes from **розповіс-** to **розповід-**, and the ending shifts from **-ти** to **-ати**. The same double pattern appears in **відповісти / відповідати** — root **відповіс-** becomes **відповід-**, ending **-ти** becomes **-ати**. This combination can look disorienting at first. Two things are changing inside the same word. But the principle stays the same: the longer, more open form is always the imperfective. With repeated exposure, these pairs start to feel natural. Your ear learns to recognize the **-ува-** suffix and the **о → а** root shift as imperfective markers before your conscious mind catches up.

<!-- INJECT_ACTIVITY: fill-in, Categorize by Formation Type — eight verb pairs; learner categorizes each into Method 1 (prefix only), Method 2a (-ува- suffix), or Method 2b (vowel change); pairs: писати/написати, запитати/запитувати, допомогти/допомагати, читати/прочитати, вирішити/вирішувати, забути/забувати, готувати/приготувати, відповісти/відповідати -->

Here is your quick-reference chart — twelve pairs from both methods in one place:

| Недоконаний вид | Доконаний вид | Спосіб |
|---|---|---|
| писати | написати | префікс |
| читати | прочитати | префікс |
| варити | зварити | префікс |
| вчити | вивчити | префікс |
| їсти | з'їсти | префікс |
| пити | випити | префікс |
| запитувати | запитати | -ува- |
| вирішувати | вирішити | -ува- |
| показувати | показати | -ува- |
| відповідати | відповісти | -ува- / корінь |
| допомагати | допомогти | о → а |
| розповідати | розповісти | корінь |

The left column is always the imperfective — the process, the habit, the ongoing action. The right column is always the perfective — the result, the single event, the completed action. When you need to look up a pair, check the ending first: **-увати** points to Method 2, a bare prefix on a simple root points to Method 1.

Now read these five sentences aloud. In each one, underline the part of the bold verb that signals its aspect — the suffix or the changed root vowel:

> «Він **відповідав** довго, поки нарешті **відповів** правильно.»

> «Вона **вирішувала** задачу і зрештою **вирішила** її.»

> «Я не завжди **розумію** все одразу, але цей текст **зрозумів** добре.»

> «Він **запитував** кілька разів, перш ніж **запитав** директора.»

> «Вони **допомагали** будувати, і разом **допомогли** завершити.»

Each pair contrasts the stretched-out imperfective with the compact perfective. The first verb in each sentence carries the aspect marker — **-ува-**, **-ід-**, **-а-** in the root — while the second verb snaps shut with its shorter perfective form.


## Спосіб 3: Зовсім інші слова (суплетивізм)

The first two methods follow predictable logic — add a prefix, change a suffix, shift a vowel. The third method follows no logic at all. Some of the most common Ukrainian verbs form their aspectual pairs from completely different roots. No prefix trick will connect them. No suffix pattern will help you guess. The imperfective and the perfective simply look like two unrelated words. Linguists call this **суплетивізм** *(suppletion)*. The good news: these pairs are few. The bad news: they include verbs you will use in almost every conversation.

Here are the four essential suppletive pairs. Read each mini-dialogue and notice how the two verbs share no visible connection:

**брати / взяти** *(to take — ongoing / to take — completed)*

> «Вона **бере** книжки з полиці щодня.»

> «Вона **взяла** словник і вийшла.»

**говорити / сказати** *(to speak, to talk — ongoing / to say, to tell — completed)*

> «Він завжди **говорить** тихо.»

> «Вона **сказала** мені правду.»

This pair deserves special attention. **Говорити** describes the ongoing process of speaking — a conversation, a habit, a manner of speech. **Сказати** captures a single utterance — one sentence, one statement, one reply. Ukrainian uses this distinction constantly in storytelling: «Він довго **говорив**, а потім **сказав**: "Досить."»

**ловити / зловити** *(to catch — ongoing / to catch — completed)*

> «Кіт **ловив** метелика в саду.»

> «Він нарешті **зловив** його.»

**шукати / знайти** *(to look for — ongoing / to find — completed)*

> «Ми **шукали** ключі всюди.»

> «Ми **знайшли** їх під столом.»

Notice that **зловити** at least shares the root **лов-** with **ловити** — it looks almost like a prefix pair. True suppletion means zero shared material, as in **брати / взяти** or **шукати / знайти**. Linguists still group **ловити / зловити** here because the prefix **з-** does not create the perfective meaning the way **на-** creates **написати** from **писати** — it merely reinforces a root that already implies catching.

Why do these irregular pairs exist at all? The most frequent verbs in any language resist regularization. They are used so often, by so many speakers, that their ancient forms survive unchanged across centuries. English has the same phenomenon: *go / went* comes from two different Old English verbs that merged. Ukrainian **брати / взяти** similarly inherits two separate roots from Old Slavic — one for the process, one for the result. Knowing this makes the irregularity feel less random. These are not exceptions. They are survivors.

Here are the twenty most important A2 aspectual pairs across all three methods — your quick-reference master list:

| Недоконаний вид | Доконаний вид | Тип |
|---|---|---|
| писати | написати | П |
| читати | прочитати | П |
| робити | зробити | П |
| бачити | побачити | П |
| готувати | приготувати | П |
| варити | зварити | П |
| вчити | вивчити | П |
| їсти | з'їсти | П |
| пити | випити | П |
| малювати | намалювати | П |
| запитувати | запитати | С |
| відповідати | відповісти | С |
| вирішувати | вирішити | С |
| розповідати | розповісти | С |
| допомагати | допомогти | К |
| забувати | забути | С |
| показувати | показати | С |
| брати | взяти | З |
| говорити | сказати | З |
| шукати | знайти | З |

**П** = префікс, **С** = суфікс, **К** = кореневе чергування, **З** = зовсім інші слова.

<!-- INJECT_ACTIVITY: match-up, Fill in the Blanks with the Correct Pair — eight sentences with gaps requiring correct aspect form; context clues signal тривалість vs. результат; items: шукати/знайти, говорити/сказати, брати/взяти, ловити/зловити, писати/написати, читати/прочитати, готувати/приготувати, допомагати/допомогти -->

How do you memorize pairs that share no visible root? Three strategies work:

First, always learn them inside a mini-story — never as isolated words. «Вона шукала і знайшла.» «Він говорив і сказав.» «Я брав і взяв.» The two verbs live together in one sentence, one situation. Your memory binds them through narrative, not through spelling.

Second, notice a practical pattern: the suppletive imperfectives tend to be longer and end in **-ити** or **-ати** — **ловити**, **шукати**, **говорити**, **брати**. Their perfective partners are often shorter or end in a bare **-ти** — **зловити**, **знайти**, **сказати**, **взяти**. This is not a rule, but it is a useful instinct to develop.

Third, put both verbs on one flashcard with the mini-story on the back. Never study one form alone. A verb without its partner is only half a word — and these partners cannot be guessed, only known.


## Summary

Ukrainian verbs live in aspectual pairs — **недоконаний вид** (imperfective, process) and **доконаний вид** (perfective, result). You now know three structural patterns for how these pairs form: prefixation (**писати / написати**), suffix or vowel change (**запитувати / запитати**, **допомагати / допомогти**), and suppletion (**брати / взяти**, **шукати / знайти**). From today, enter every new verb in pairs — one form alone is only half the picture. The notation "impf / pf" is your default tool for organizing vocabulary. When you meet a verb in a text, immediately ask: where is its partner? Which formation type connects them? That reflex will build faster than any grammar table.

<!-- INJECT_ACTIVITY: match-up, Sentence Translation with Aspect Focus — eight English prompts requiring Ukrainian translation with correct aspect choice; items: "She was reading for an hour" → impf, "He finally found his keys" → pf, "They cooked the varenyky (finished)" → pf, "We were helping all evening" → impf, "I wrote the letter (completed)" → pf, "The children were playing in the yard" → impf, "She said one word and left" → pf, "He was looking for his phone everywhere" → impf -->

**Перевір себе** (Self-check):

- Яке питання ставлять до недоконаного дієслова? — «Що робити?»
- Яке питання ставлять до доконаного дієслова? — «Що зробити?»
- Як утворити доконаний вид у парі «читати / ___»? — «Прочитати» — додаємо префікс «про-».
- Який суфікс є сигналом недоконаного виду? — Суфікс «-ува-» або «-юва-».
- Назви дві суплетивні пари. — «Брати / взяти» і «шукати / знайти».

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-vocabulary
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

**Level: A2 (Module 3/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

### Pattern: grammar-verb-aspect
- **group-sort** — Доконаний чи недоконаний?: Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Identify aspect of a given verb

### Pattern: general-vocabulary
- **match-up** — Слово → переклад: Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Fill in the missing word from context
- **anagram** — Склади слово: Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Choose correct translation from options


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
