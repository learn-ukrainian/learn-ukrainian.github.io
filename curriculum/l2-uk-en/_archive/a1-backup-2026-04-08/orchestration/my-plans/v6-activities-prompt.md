<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/my-plans.yaml` file for module **51: My Plans** (a1).

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

- `<!-- INJECT_ACTIVITY: 1 -->`
- `<!-- INJECT_ACTIVITY: 2 -->`
- `<!-- INJECT_ACTIVITY: 3 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Combine days of the week, time, and future tense
  items:
  - У {понеділок|вівторок|середу} я буду працювати.
  - У суботу {зранку|ввечері|вдень} я буду прибирати квартиру.
  - '{О|В|На} шостій ми будемо дивитися кіно.'
  - У {неділю|суботу|п'ятницю} він буде відпочивати.
  - У п'ятницю {ввечері|зранку|вдень} буде вечірка.
  type: fill-in
- focus: Match invitations to natural responses
  pairs:
  - Ходімо в кіно!: З задоволенням!
  - Може, підемо в кафе?: Добре! О котрій?
  - Ти будеш вільний у суботу?: На жаль, не можу.
  - Давай зустрінемося о п'ятій!: Чудово! До зустрічі!
  type: matching
- focus: Complete a scheduled plan for the week
  items:
  - У вівторок я {буду вчити|вчив|вчу} українську.
  - У середу ми {будемо готувати|готували|готуємо} вечерю.
  - У четвер вона {буде працювати|працювала|працює} допізна.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- зустрінемося (let's meet — chunk)
- з задоволенням (with pleasure)
- на жаль (unfortunately)
- допізна (until late)
- звичайно (of course)
- квартира (apartment, f)
- кіно (cinema, n)
- вчити (to study/learn)
required:
- план (plan, m)
- тиждень (week, m)
- вільний (free, adj)
- зустріч (meeting, f)
- відпочивати (to rest)
- прибирати (to clean)
- вечірка (party, f)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Dialogues

Olya, Taras, and Mariia are planning their weekend in a group chat. The weekend is a time to rest, but it often involves running errands. Pay attention to how they talk about their plans using the word **буду** (I will).

> **Оля:** Що ти будеш робити у суботу? *(What will you do on Saturday?)*
> **Тарас:** Зранку я буду прибирати квартиру. *(In the morning I will clean the apartment.)*
> **Оля:** А вдень? *(And in the afternoon?)*
> **Тарас:** Вдень я буду ходити в магазин. А ти? *(In the afternoon I will go to the store. And you?)*
> **Марія:** Я буду відпочивати! Може, підемо в кафе ввечері? *(I will rest! Maybe we will go to a cafe in the evening?)*
> **Оля:** Добре! О котрій? *(Good! At what time?)*
> **Марія:** О шостій. Добре? *(At six. Good?)*
> **Тарас:** Чудово! До зустрічі у суботу! *(Great! See you on Saturday!)*

In this dialogue, the friends are using the future tense combined with specific times. You can see the pattern: **я буду прибирати** (I will clean) and **я буду відпочивати** (I will rest). Notice how they specify the time of day: **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening). The word **квартира** means "apartment", and **кіно** is "cinema". 

When using the analytic future tense with the auxiliary verb **буду**, you only conjugate the auxiliary verb to match the speaker (I, you, he, we). The main action verb always stays in its dictionary form, the infinitive. For example, in the phrase **я буду прибирати** (I will clean), the main verb **прибирати** (to clean) remains unchanged. This makes the future tense very approachable once you know your basic verbs.

Now, let's look at another situation. Dmytro is telling his friend about his very busy week. He uses the days of the week to map out his schedule.

> **Анна:** У тебе є плани на тиждень? *(Do you have plans for the week?)*
> **Дмитро:** Так, багато! У понеділок я буду працювати допізна. *(Yes, many! On Monday I will work until late.)*
> **Анна:** У вівторок буду вчитися. У середу — зустріч з друзями. *(On Tuesday I will study. On Wednesday — a meeting with friends.)*
> **Дмитро:** А у четвер? *(And on Thursday?)*
> **Анна:** У четвер я буду готувати на вечірку. *(On Thursday I will cook for a party.)*
> **Дмитро:** А в п'ятницю? *(And on Friday?)*
> **Анна:** В п'ятницю — вечірка! Ти будеш? *(On Friday — a party! Will you be there?)*
> **Дмитро:** Звичайно буду! *(Of course I will be!)*

Here, Dmytro and Anna build a complete schedule. The key pattern is the auxiliary verb **буду** (I will) followed by an infinitive verb. They also use the days of the week as fixed time anchors, such as **у понеділок** (on Monday) and **у вівторок** (on Tuesday). Think about what Anna is doing on Thursday. She is preparing for a **вечірка** (party). Dmytro also mentions he will work **допізна** (until late), and responds enthusiastically with **звичайно** (of course). They also schedule a **зустріч** (meeting).

## Планування (Planning)

When you want to schedule an event or talk about a **план** (plan), you need a reliable formula. In Ukrainian, planning involves combining the day, the time, the auxiliary verb, and the main action. The core pattern looks like this: **У** (On) + day + time + **буду** (I will) + infinitive verb.

To use this formula, you first need to know the days of the week. Notice how we use the preposition **у** (in/on) or **в** (in/on) before the day to say "on [Day]".

*   **у понеділок** (on Monday)
*   **у вівторок** (on Tuesday)
*   **у середу** (on Wednesday)
*   **у четвер** (on Thursday)
*   **у п'ятницю** (on Friday)
*   **у суботу** (on Saturday)
*   **в неділю** (on Sunday)

You can make your plan more specific by adding a time-of-day adverb. We use **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening). These adverbs are incredibly useful because they do not require any extra prepositions. You simply place them next to your verb. You can also add clock time using **о** (at): **о дев'ятій** (at nine), **о третій** (at three), **о шостій** (at six).

Let's combine these elements into full sentences:
*   **У суботу ввечері я буду дивитися фільм.** (On Saturday evening I will watch a movie.)
*   **У середу зранку я буду працювати.** (On Wednesday morning I will work.)
*   **У п'ятницю о шостій я буду відпочивати.** (On Friday at six I will rest.)

When you want to invite someone to join your plan, you have a handy toolkit of phrases. These phrases vary in their tone.
*   **Ходімо в кафе!** (Let's go to a cafe!) — This uses the warm imperative form to create a friendly, active invitation. It implies that you are already ready to go.
*   **Може, підемо в кіно?** (Maybe we'll go to the cinema?) — This is a soft suggestion using the word **може** (maybe), making it sound more like an open proposal.
*   **Давай зустрінемося о п'ятій!** (Let's meet at five!) — This is a collaborative invitation using the chunk **зустрінемося** (let's meet).

Before making an invitation, you might want to check if the person has a **вільний** (free) schedule. You can ask: **Ти будеш вільний у суботу?** (Will you be free on Saturday? — speaking to a male) or **Ти будеш вільна у суботу?** (Will you be free on Saturday? — speaking to a female).

When someone invites you, you need to know how to respond. You can accept enthusiastically or decline politely.
*   **Добре!** (Good!)
*   **Чудово!** (Great!)
*   **З задоволенням!** (With pleasure!) — The word **задоволення** means satisfaction or pleasure. This shows genuine enthusiasm.
*   **На жаль, не можу.** (Unfortunately, I cannot.) — This combines **на жаль** (unfortunately) with a polite refusal.

<!-- INJECT_ACTIVITY: 1 -->

<!-- INJECT_ACTIVITY: 2 -->

You might have noticed a small detail when listing the days of the week. We say **у понеділок**, **у вівторок**, **у середу**, **у четвер**, **у п'ятницю**, and **у суботу**. But for Sunday, we say **в неділю**. Why the difference? This follows the same euphony rule (harmonious sound) you saw in earlier modules. The word **суботу** ends in a vowel, so the next word naturally starts with a consonant to keep the speech flowing smoothly. If the previous word ends in a vowel, you use **в** before a consonant. If it ends in a consonant, you use **у** before a consonant. Let's practice filling in the blanks mentally: "я буду працювати _ понеділок", but "я буду відпочивати _ неділю".

## Мій тиждень (My Week)

Let's introduce Taras. He is a very organized person and likes to plan his entire **тиждень** (week) in advance. He breaks down his schedule one day at a time, making sure he balances work, studies, and time to **відпочивати** (to rest). 

Here is Taras's model week:
*   **У понеділок я буду працювати.** (On Monday I will work.)
*   **Після роботи буду вчити українську.** (After work I will study Ukrainian.)
*   **У вівторок я буду обідати з другом у кафе.** (On Tuesday I will have lunch with a friend in a cafe.)
*   **У середу ввечері я буду дивитися футбол.** (On Wednesday evening I will watch football.)
*   **У четвер я буду готувати вечерю для родини.** (On Thursday I will cook dinner for the family.)
*   **У п'ятницю я буду відпочивати — піду в кіно.** (On Friday I will rest — I will go to the cinema.)
*   **У суботу зранку буду прибирати, а вдень гуляти в парку.** (On Saturday morning I will clean, and in the afternoon walk in the park.)
*   **В неділю я буду спати довго!** (On Sunday I will sleep long!)

Notice how every single day uses the structure **буду** + infinitive. This is the most natural way to describe an ongoing or planned activity in the future. The phrase **я буду прибирати** means that the action of cleaning will be a process taking up his time. The verb **вчити** (to study/learn) is perfect for describing a continuous educational goal. When he says **я буду відпочивати**, he implies a continuous period of rest. 

Now it is your turn to create your own schedule. You can use this simple template:
**У** [day] **о** [time] **я буду** [infinitive verb].

To make your sentences richer, you can answer three expansion questions:
1.  **Де?** (Where?) — **у парку** (in the park), **в кафе** (in the cafe), **вдома** (at home).
2.  **З ким?** (With whom?) — **з другом** (with a friend), **з сім'єю** (with family), **сам** / **сама** (alone).
3.  **Що саме?** (What exactly?) — **прибирати квартиру** (to clean the apartment), **готувати обід** (to cook lunch), **дивитися фільм** (to watch a movie).

Let's look at a worked example that uses all these pieces:
**У суботу о десятій я буду гуляти в парку з другом.** (On Saturday at ten I will walk in the park with a friend.)

<!-- INJECT_ACTIVITY: 3 -->

Now, try a mini-writing task. Plan your ideal weekend in four to six sentences using the model you just learned. Make sure your plan includes two days: **субота** (Saturday) and **неділя** (Sunday). Include the time of day (**зранку**, **вдень**, **ввечері**) or a specific clock time (**о котрій?**). Mention the place, and use the **буду** + infinitive structure.

Here is a sample answer to guide you:
**У суботу зранку я буду спати довго. Вдень я буду гуляти в парку. Ввечері ми будемо дивитися фільм. В неділю я буду готувати сніданок для родини.** (On Saturday morning I will sleep long. In the afternoon I will walk in the park. In the evening we will watch a movie. On Sunday I will cook breakfast for the family.)

## Summary

When you want to organize your schedule and invite friends, you now have a complete planning toolkit. The future tense for planning is built on a straightforward formula that you can adapt to any situation. 

The core formula is: **У** [day] **о** [time] **я буду** [infinitive verb].
For example: **У суботу о третій я буду готувати обід.** (On Saturday at three I will cook lunch.)

You can modify the time of day using these adverbs:
*   **зранку** (in the morning)
*   **вдень** (in the afternoon)
*   **ввечері** (in the evening)

To bring people into your plans, use these invitations:
*   **Ходімо!** (Let's go!)
*   **Може, підемо?** (Maybe we'll go?)
*   **Давай зустрінемося!** (Let's meet!)

And to reply to those invitations, you have several options ranging from enthusiastic agreement to polite refusal:
*   **Добре!** (Good!)
*   **Чудово!** (Great!)
*   **З задоволенням!** (With pleasure!)
*   **На жаль, не можу.** (Unfortunately, I cannot.)

Your days of the week review:
*   **понеділок** (Monday)
*   **вівторок** (Tuesday)
*   **середа** (Wednesday)
*   **четвер** (Thursday)
*   **п'ятниця** (Friday)
*   **субота** (Saturday)
*   **неділя** (Sunday)

Remember the euphony rule when attaching prepositions: we say **у суботу** but **в неділю** depending on the preceding sounds. The Ukrainian language naturally avoids awkward clusters of consonants or vowels. This makes your sentences flow beautifully.

## Підсумок

You are now ready to make plans in Ukrainian! Let's do a quick self-check to ensure you feel confident with this material. Try to answer these questions aloud:

*   **Що ти будеш робити у суботу?** (What will you do on Saturday?)
*   **О котрій?** (At what time?)
*   **Ти будеш вільний?** / **Ти будеш вільна?** (Will you be free?)
*   **Ходімо в кафе ввечері?** (Let's go to a cafe in the evening?)

If you can answer these questions, you are ready to coordinate your schedule, set up a **зустріч** (meeting), and enjoy your **вечірка** (party) with friends. Keep practicing your weekly routine, and soon these future tense patterns will feel completely natural.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: my-plans
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

**Level: A1.4+ (Module 51/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present
- **fill-in** — Відмінюй дієслово: Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Find incorrectly conjugated verb and fix it

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


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
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
