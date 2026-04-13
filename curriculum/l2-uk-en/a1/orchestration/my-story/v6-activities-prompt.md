<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-story.yaml` file for module **52: My Story** (a1).

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

- `<!-- INJECT_ACTIVITY: matching-tense -->`
- `<!-- INJECT_ACTIVITY: fill-in-signal-words -->`
- `<!-- INJECT_ACTIVITY: ordering-chronological -->`
- `<!-- INJECT_ACTIVITY: fill-in-biography -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
  type: ordering
- focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
  type: fill-in
- focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
  type: matching
- focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народився|народилися} у Львові.
  - Там я {вчилася|вчився|вчилися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- подорожувати (to travel)
- закінчити (to finish/graduate)
- дитинство (childhood, n)
- університет (university, m)
- програміст (programmer, m)
- успіх (success, m)
- мрія (dream, f)
- батьки (parents, pl)
required:
- народитися (to be born)
- жити (to live)
- вчитися (to study)
- переїхати (to move)
- зараз (now)
- раніше (before/earlier)
- далі (further/next)
- розповідати (to tell/narrate)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Every person has a unique life path. We all come from different places. We all have different jobs and dreams. To share your journey, you need to navigate through time. You need to talk about the past, the present, and the future. In this module, you will learn to connect all three tenses into one cohesive narrative. 

**Моя подорож**
Кожна людина має свою історію. Ми живемо в різних містах. Ми багато працюємо. Ми цікаво вчимося. Ми маємо великі плани. Далі ми будемо говорити про це.

> *Every person has their story. We live in different cities. We work a lot. We study interestingly. We have big plans. Next we will talk about this.*

When you meet someone new or talk to family, sharing your life journey is a natural step. Let's listen to a grandfather sharing his past, present, and future with his grandchildren.

> **Онук:** **Дідусю, розкажи про себе!** *(Grandpa, tell about yourself!)*
> **Дідусь:** **Я народився в селі.** *(I was born in a village.)*
> **Дідусь:** **Там я ходив у школу.** *(There I went to school.)*
> **Онука:** **А зараз ти живеш тут?** *(And now you live here?)*
> **Дідусь:** **Зараз я живу в місті.** *(Now I live in a city.)*
> **Дідусь:** **Я працюю в лікарні.** *(I work in a hospital.)*
> **Онук:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Дідусь:** **Я буду відпочивати на дачі!** *(I will rest at the dacha!)*

Now, let's look at another conversation where two friends, Marko and David, get to know each other deeply.

> **Марко:** **Розкажи про себе!** *(Tell about yourself!)*
> **Девід:** **Я народився в Канаді.** *(I was born in Canada.)*
> **Девід:** **Це було у Торонто.** *(It was in Toronto.)*
> **Марко:** **А зараз ти живеш тут?** *(And now you live here?)*
> **Девід:** **Так, зараз я живу в Києві.** *(Yes, now I live in Kyiv.)*
> **Марко:** **Чому ти переїхав?** *(Why did you move?)*
> **Девід:** **Я хотів вивчати українську.** *(I wanted to study Ukrainian.)*
> **Девід:** **Мої дідусь і бабуся з України.** *(My grandfather and grandmother are from Ukraine.)*
> **Марко:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Девід:** **Я буду працювати тут.** *(I will work here.)*
> **Девід:** **І я буду вчити мову.** *(And I will study the language.)*
> **Марко:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*

Notice how the speakers naturally move through time to explain their current situation and future goals. David starts with the past tense to establish his origins. He smoothly transitions to the present tense to explain his current life. Finally, he uses the future tense to state his future plans. This structure is the key to clear storytelling.

Now, let's look at Anna’s story. She provides a continuous narrative flow from her **дитинство** (childhood, n) to her future plans. She connects her past, present, and future in a logical order, making her biography easy to follow. Let's listen to her conversation with Maksym.

> **Максим:** **Анно, розкажи свою історію.** *(Anna, tell your story.)*
> **Анна:** **Я народилася у Львові.** *(I was born in Lviv.)*
> **Анна:** **Там я вчилася в школі.** *(There I studied in school.)*
> **Анна:** **Потім я переїхала в Київ.** *(Then I moved to Kyiv.)*
> **Анна:** **Тут я закінчила університет.** *(Here I graduated university.)*
> **Анна:** **Зараз я працюю вчителькою.** *(Now I work as a teacher.)*
> **Анна:** **Я живу в центрі міста.** *(I live in the city center.)*
> **Максим:** **А що далі?** *(And what next?)*
> **Анна:** **Я буду подорожувати!** *(I will travel!)*
> **Анна:** **Я хочу побачити Японію.** *(I want to see Japan.)*
> **Максим:** **І ти будеш вчити японську?** *(And you will study Japanese?)*
> **Анна:** **Може! Але спочатку — українська!** *(Maybe! But first — Ukrainian!)*

Anna begins with her past in Lviv, using the feminine past tense verb **народилася**. She brings us to the present with **працюю**. Then she reveals her **мрія** (dream, f) for the future using **буду подорожувати**. 

## Три часи разом (Three Tenses Together)

A complete life story is never stuck in just one moment of time. It requires all three tenses to create a full picture of who you are. You need the past tense to answer the fundamental question "Where are you from?" and explain your origins. You need the present tense to answer "What do you do?" and describe your daily reality. Finally, you need the future tense to answer "What are your plans?" and share your ambitions. Let's review how these tenses operate together.

**Мій брат**
Раніше мій брат жив у селі. Він багато читав. Зараз він живе в місті. Він працює в університеті. Далі він буде писати книгу. Він буде багато подорожувати.

> *Earlier my brother lived in a village. He read a lot. Now he lives in a city. He works at a university. Next he will write a book. He will travel a lot.*

The past tense (**минулий час**) is the foundation of your biography. When talking about yourself, the past tense strictly requires gender agreement for the pronoun **я** (I). A male speaker must use the masculine ending **-в**, while a female speaker must use the feminine ending **-ла**. This gender distinction is a core feature of the Ukrainian past tense. It is crucial to remember that the past tense does not change based on who you are talking to, but rather the gender of who is speaking or who you are talking about.

| Pronoun | Verb (to live) | English |
|---------|----------------|---------|
| Я (masculine) | **жив** | I lived |
| Я (feminine) | **жила** | I lived |
| Він (He) | **жив** | He lived |
| Вона (She) | **жила** | She lived |
| Ми (We) | **жили** | We lived |

*   **Я народився в місті.** *(I was born in a city. — masculine)*
*   **Я народилася в селі.** *(I was born in a village. — feminine)*
*   **Я жив тут.** *(I lived here. — masculine)*
*   **Я жила там.** *(I lived there. — feminine)*
*   **Я вчився добре.** *(I studied well. — masculine)*
*   **Я працювала в школі.** *(I worked in a school. — feminine)*

The present tense (**теперішній час**) describes your current situation and regular habits. Unlike the past tense, the present tense does not use gender endings. Instead, it relies on standard person endings based on the subject pronoun. The present tense focuses entirely on the person performing the action. Notice that the ending **-ю** is common for the first person singular (**я**).

| Pronoun | Verb (to live) | English |
|---------|----------------|---------|
| Я | **живу** | I live |
| Ти | **живеш** | You live |
| Він / Вона | **живе** | He / She lives |
| Ми | **живемо** | We live |

*   **Зараз я живу в місті.** *(Now I live in a city.)*
*   **Я працюю в лікарні.** *(I work in a hospital.)*
*   **Я вивчаю українську мову.** *(I am studying the Ukrainian language.)*
*   **Я люблю читати книги.** *(I love to read books.)*
*   **Мій друг працює програмістом.** *(My friend works as a programmer.)*

The future tense (**майбутній час**) allows you to share your goals. The most common and simple way to express the future is by using the compound form. You create this by combining the conjugated helper verb **бути** (to be) with the infinitive form of the main action verb. This compound future is incredibly flexible because you only need to conjugate the helper verb. The main verb always stays in its dictionary infinitive form.

| Pronoun | Verb (to work) | English |
|---------|----------------|---------|
| Я | **буду працювати** | I will work |
| Ти | **будеш працювати** | You will work |
| Він / Вона | **буде працювати** | He / She will work |
| Ми | **будемо працювати** | We will work |

*   **Я буду працювати тут.** *(I will work here.)*
*   **Я буду вивчати історію.** *(I will study history.)*
*   **Я буду жити в місті.** *(I will live in a city.)*
*   **Я буду подорожувати.** *(I will travel.)*
*   **Вона буде читати книгу.** *(She will read a book.)*

To help your listener clearly follow your story, you should use time signal words. These words act as anchors, marking tense shifts on your timeline. For the past tense, use words like **раніше** (before/earlier) or **у дитинстві**. For the present tense, use **зараз** (now) or **сьогодні** (today). For the future tense, use **потім** (then) or **далі** (further/next). These signal words prepare the listener for the grammar that follows.

*   **Раніше я жив у Лондоні.** *(Before I lived in London.)*
*   **Зараз я живу в Києві.** *(Now I live in Kyiv.)*
*   **Далі я буду жити в Одесі.** *(Next I will live in Odesa.)*

<!-- INJECT_ACTIVITY: matching-tense -->
<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя історія (My Story)

Now it is time to transition from individual sentences to a complete, structured monologue. Telling a personal narrative requires organization. A clear story always has three main parts: an introduction, a main body, and a conclusion. By combining your past, present, and future into this structure, you can confidently **розповідати** (to tell/narrate) your unique biography.

Let's read a model text that brings everything together. This is Taras's life story. Notice how he structures his narrative.

**Моя історія**
Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році. Я жив там з батьками і сестрою. Я ходив у школу. Я любив математику. Потім я переїхав у Київ. Там я вчився в університеті. Зараз я живу в Києві. Я працюю програмістом. Я люблю свою роботу. У вільний час я граю у футбол. Я читаю книжки. Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві. Це моє місто!

> *I was born in Odesa in nineteen ninety-five. I lived there with my parents and sister. I went to school. I loved math. Then I moved to Kyiv. There I studied at a university. Now I live in Kyiv. I work as a programmer. I love my work. In my free time I play football. I read books. Next I will travel. I will study English. And I will live in Kyiv. This is my city!*

Let's deconstruct Taras's story to see how it works. His biography has a clear, logical chronological flow. He starts his introduction in the past to establish his background, using verbs like **народився** (was born), **жив** (lived), and **переїхав** (moved). Then, the main body transitions to his present reality using verbs like **живу** (live) and **працюю** (work). Finally, his conclusion looks to the future using the compound constructions **буду подорожувати** (will travel) and **буду вивчати** (will study).

Now it is your turn to create your own biography. Use this scaffolding template to build your narrative block by block. 

Start with your origin in the past tense: 
*   **Я народився / Я народилася в...** (I was born in...)
*   **Я жив / Я жила...** (I lived...)
*   **Я вчився / Я вчилася...** (I studied...)

Then, move your story to the present tense: 
*   **Зараз я живу...** (Now I live...)
*   **Я працюю...** (I work...)

Finally, share your future plans: 
*   **Я буду...** (I will...)
*   **Я хочу...** (I want...)

Try to use at least three verbs for each tense to build a complete text. This structured approach helps you build a complex story from simple parts.

<!-- INJECT_ACTIVITY: ordering-chronological -->
<!-- INJECT_ACTIVITY: fill-in-biography -->

## Summary

You now have the linguistic tools to tell your complete life story. Let's recap the core grammar of the three tenses. The past tense relies on gender endings for the speaker. A male says **Я народився** (I was born), while a female says **Я народилася** (I was born). The present tense uses standard person endings regardless of gender, giving us forms like **Я живу** (I live) and **Я працюю** (I work). The future tense combines the helper verb **буду** with an infinitive action verb, creating phrases like **Я буду працювати** (I will work). By combining all three, you build a cohesive timeline.

**Наші плани**
Раніше ми жили в Америці. Там ми вчили англійську мову. Зараз ми живемо в Україні. Тут ми вчимо українську мову. Далі ми будемо вільно говорити.

> *Earlier we lived in America. There we studied the English language. Now we live in Ukraine. Here we study the Ukrainian language. Next we will speak fluently.*

Do not forget the crucial signal words that guide the narrative timeline. These anchors help your listener understand exactly when an event happened. Use **раніше** (before/earlier) to signal the past tense. Use **зараз** (now) to mark the present tense. Finally, use **далі** (further/next) to introduce your future plans.

Let's quickly recap your core biographical vocabulary. Your foundation includes the verbs **народитися** (to be born), **жити** (to live), **вчитися** (to study), **переїхати** (to move), and **подорожувати** (to travel). When discussing your career, remind yourself to use the instrumental case for professions. For example, you should say **Я працюю програмістом** (I work as a programmer) or **Я працюю вчителькою** (I work as a teacher). Achieving **успіх** (success, m) in storytelling is all about using these blocks correctly. Mastering these verbs will give you the confidence to speak about your life in any situation. You can discuss your early life or your time at the **університет** (university, m).

Self-check: Write your own life story in eight to ten sentences using all three tenses. Ensure you include where you were born, where you live now, and your future plans.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-story
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

**Level: A1.4+ (Module 52/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
