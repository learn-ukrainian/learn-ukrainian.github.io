<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 49: Yesterday (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-049
level: A1
sequence: 49
slug: yesterday
version: '1.2'
title: Yesterday
subtitle: Учора я прокинувся, поснідав і пішов — narrating your day
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Narrate a complete past day using sequenced past-tense verbs
- Use time markers to structure a narrative (зранку, вдень, ввечері)
- Combine past tense with known vocabulary (food, places, people)
- Tell a short personal story about yesterday
dialogue_situations:
- setting: 'Police report — describing a stolen велосипед (m, bicycle): Я припаркував
    велосипед біля магазину (m). Потім зайшов у кав''ярню (f). Коли вийшов, велосипед
    зник. Бачив чоловіка (m) в куртці (f) та кепці (f, cap).'
  speakers:
  - Свідок (witness)
  - Поліцейський
  motivation: Past narration with велосипед(m), магазин(m), кав'ярня(f), куртка(f)
content_outline:
- section: Dialogues
  words: 300
  points:
  - Dialogue 1 — How was your day? — Як пройшов твій день? — Добре! Зранку я прокинувся
    о сьомій. — Що ти робив зранку? — Я поснідав і пішов на роботу. — А вдень? — Вдень
    я працював і обідав з колегою. — А ввечері? — Ввечері я дивився фільм і рано ліг
    спати. Full day narration using time markers.
  - 'Dialogue 2 — A fun weekend: — Що ти робила у суботу? — О, я мала чудовий день!
    — Розкажи! — Зранку я ходила на ринок і купила фрукти. — А потім? — Потім я готувала
    обід. А вдень гуляла в парку. — А ввечері? — Ввечері ми з подругою ходили в ресторан.
    — Як файно! Sequencing with потім, а потім.'
- section: Розповідь про день (Narrating a Day)
  words: 300
  points:
  - 'Time markers for structuring a story: зранку (in the morning), вдень (in the
    afternoon), ввечері (in the evening), вночі (at night). спочатку (first), потім
    (then), після цього (after that), нарешті (finally). These words turn separate
    sentences into a story: Спочатку я поснідав. Потім я пішов на роботу. Після цього
    я обідав.'
  - 'Daily routine verbs in past tense (all genders): прокинутися → прокинувся / прокинулася
    поснідати → поснідав / поснідала піти → пішов / пішла обідати → обідав / обідала
    повернутися → повернувся / повернулася лягти спати → ліг / лягла спати'
- section: Мій учорашній день (My Yesterday)
  words: 300
  points:
  - 'Model narrative — Anna''s yesterday: Учора був звичайний день. Зранку я прокинулася
    о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень
    я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин
    і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій
    я лягла спати. Note all verbs are -ла (Anna is female).'
  - 'Your turn — build your own narrative: Use the template: Учора... Зранку я...
    Потім... Вдень... Ввечері... Combine past-tense verbs with places (кафе, парк,
    магазин), food (каша, кава, салат), and people (друг, колега, подруга). Everything
    you learned in A1 comes together here.'
- section: Summary
  words: 300
  points:
  - 'Narration toolkit: Time structure: зранку → вдень → ввечері → вночі. Sequencing:
    спочатку, потім, після цього, нарешті. Daily routine past forms: прокинувся/-лася,
    поснідав/-ла, пішов/пішла, обідав/-ла, повернувся/-лася, ліг/лягла спати. Gender
    consistency: male speakers use -в/-вся forms throughout, female speakers use -ла/-лася
    throughout. Self-check: Tell the story of your yesterday using at least 5 verbs.'
vocabulary_hints:
  required:
  - учора (yesterday)
  - зранку (in the morning)
  - вдень (in the afternoon)
  - ввечері (in the evening)
  - потім (then)
  - прокинутися (to wake up)
  - поснідати (to have breakfast)
  - обідати (to have lunch)
  recommended:
  - спочатку (first/at first)
  - нарешті (finally)
  - повернутися (to return)
  - лягти (to lie down)
  - звичайний (ordinary, adj)
  - продукти (groceries, pl)
  - серіал (TV series, m)
  - колега (colleague, m/f)
activity_hints:
- type: ordering
  focus: Put the daily routine in chronological order
  items:
  - Зранку я прокинувся.
  - Спочатку я поснідав.
  - Потім я пішов на роботу.
  - Вдень я обідав з колегою.
  - Ввечері я повернувся і дивився серіал.
  - Нарешті я ліг спати.
- type: fill-in
  focus: Complete the narrative with time markers and sequenced verbs
  items:
  - Учора {зранку|вдень|потім} я прокинулася о сьомій.
  - '{Спочатку|Нарешті|Вночі} я поснідала.'
  - '{Потім|Зранку|Ввечері} я пішла на роботу.'
  - Вдень я {обідала|обідав|обідали} в кафе.
  - '{Ввечері|Вдень|Зранку} я готувала вечерю.'
  - О десятій я {лягла|ліг|лягли} спати.
- type: fill-in
  focus: Practice gender consistency in narration (Female speaker 'Anna')
  items:
  - Я мала звичайний день. Я {прокинулася|прокинувся} рано.
  - Потім я {поснідала|поснідав}.
  - Після цього я {пішла|пішов} у магазин.
  - Там я {купила|купив} продукти.
connects_to:
- a1-050 (What Will Happen?)
prerequisites:
- a1-048 (What Happened?)
grammar:
- Past tense in connected narration (not isolated sentences)
- 'Time markers: зранку, вдень, ввечері, вночі'
- 'Sequencing words: спочатку, потім, після цього, нарешті'
- Gender consistency across a narrative
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Past tense applied in narrative context.

</plan_content>

## Generated Content

<generated_module_content>
## Dialogues

To tell what happened yesterday, you need to put actions in order. In this module, you will hear short dialogues and build a simple story from morning to night using time markers and past-tense verbs.

In our first dialogue, let us listen to Petro as he describes a typical workday. Notice how he uses specific time markers to signal each phase of his day.

> **Колега:** Як пройшов твій день? *(How was your day?)*
> **Петро:** Добре! Зранку я **прокинувся** (woke up) о сьомій. *(Good! In the morning I woke up at seven.)*
> **Колега:** Що ти робив зранку? *(What did you do in the morning?)*
> **Петро:** Я **поснідав** (had breakfast) і **пішов** (went) на роботу. *(I had breakfast and went to work.)*
> **Колега:** А вдень? *(And in the afternoon?)*
> **Петро:** Вдень я працював і **обідав** (had lunch) з колегою. *(In the afternoon I worked and had lunch with a colleague.)*
> **Колега:** А ввечері? *(And in the evening?)*
> **Петро:** Ввечері я дивився фільм і рано **ліг** спати. *(In the evening I watched a movie and went to bed early.)*

This short conversation demonstrates how a day can be structured with time markers such as **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening), ending with **лягти спати** (to go to bed). Petro is a man, so when he talks about his own actions in the past, he uses masculine forms such as **прокинувся** (I woke up), **поснідав** (I had breakfast), and **пішов** (I went). Some masculine past forms are irregular, such as **ліг** (I lay down), so do not expect every masculine form to end in **-в** or **-вся**.

Here is one more real-life past-tense situation from this module's theme: a police report about a stolen bicycle.

> **Поліцейський:** Що сталося? *(What happened?)*
> **Свідок:** Я припаркував велосипед біля магазину. Потім зайшов у кав'ярню. Коли вийшов, велосипед зник. *(I parked the bicycle near the store. Then I went into the cafe. When I came out, the bicycle was gone.)*
> **Поліцейський:** Ви бачили когось? *(Did you see anyone?)*
> **Свідок:** Так, бачив чоловіка в куртці та кепці. *(Yes, I saw a man in a jacket and a cap.)*

Now, let us listen to a feminine perspective. Anna is telling her friend about her Saturday. Pay attention to how the verb endings change and how she uses "then" to keep the story moving.

> **Подруга:** Що ти робила у суботу? *(What did you do on Saturday?)*
> **Анна:** О, я мала чудовий день! *(Oh, I had a wonderful day!)*
> **Подруга:** Розкажи! *(Tell me!)*
> **Анна:** Зранку я **ходила** (went) на ринок і **купила** (bought) фрукти. *(In the morning I went to the market and bought fruit.)*
> **Подруга:** А **потім** (then)? *(And then?)*
> **Анна:** **Потім** я готувала обід. А вдень гуляла в парку. *(Then I was cooking lunch. And in the afternoon I walked in the park.)*
> **Подруга:** А ввечері? *(And in the evening?)*
> **Анна:** Ввечері ми з подругою **ходили** (went) в ресторан. *(In the evening me and a friend went to a restaurant.)*
> **Подруга:** Як файно! *(How lovely!)*

Because Anna is female, her verbs end in **-ла**: **ходила** (went), **купила** (bought), **готувала** (cooked). She also uses the word **потім** (then) several times. In Ukrainian, **потім** is a very useful "glue" word that allows you to link one event to another without repeating the time of day. You can also use **а потім** (and then) to add a bit of variety to your storytelling.

## Розповідь про день (Narrating a Day)

To tell a story effectively, you need a timeline. Ukrainian uses four primary adverbs to divide the day into manageable chunks. These words usually appear at the start of a sentence to establish the context immediately.

*   **зранку** (in the morning) — used for everything from waking up to starting work.
*   **вдень** (in the afternoon / during the day) — used for the middle of the day, typically lunchtime and work hours.
*   **ввечері** (in the evening) — used for the time after work, dinner, and relaxation.
*   **вночі** (at night) — used for the late hours when the world is asleep.

When you put these together, you create a natural progression. For example, a student might say:

**Зранку** я читав книгу. **Вдень** я був в університеті. **Ввечері** я відпочивав.
> *In the morning I read a book. In the afternoon I was at the university. In the evening I was resting.*

Once you have your time blocks, you need sequencing words to connect the dots. Without these, your story sounds like a grocery list of isolated facts. Ukrainian provides a specific set of adverbs to help you navigate through time:

*   **спочатку** (first / at first) — sets the very first scene.
*   **потім** (then) — the most common way to move to the next event.
*   **після цього** (after that) — a slightly more formal way to say "after that."
*   **нарешті** (finally) — used to signal the last action in a sequence.

Observe how these words transform separate sentences into a cohesive narrative paragraph:

**Спочатку** я **поснідав**. **Потім** я **пішов** на роботу. **Після цього** я **обідав**. **Нарешті** я **повернувся** додому.
> *First I had breakfast. Then I went to work. After that I had lunch. Finally I returned home.*

The "engine" of your narrative consists of daily routine verbs. In the past tense, these verbs must match your gender. Here is a table showing the most common routine verbs in their masculine and feminine forms.

| Verb (Infinitive) | Male Speaker (Він) | Female Speaker (Вона) | Meaning |
| :--- | :--- | :--- | :--- |
| **прокинутися** | **прокинувся** | **прокинулася** | to wake up |
| **поснідати** | **поснідав** | **поснідала** | to have breakfast |
| **піти** | **пішов** | **пішла** | to go / set out |
| **працювати** | **працював** | **працювала** | to work |
| **бути** | **був** | **була** | to be |

:::tip
Notice the verb **пішов** (masculine) and **пішла** (feminine). This is an irregular shift from the infinitive **піти**. It is one of the most common verbs in the past tense, so it is worth memorizing these two forms early!
:::

As the day continues, you will need verbs for the afternoon and evening activities. These follow the same gender-agreement patterns.

*   **обідати** (to have lunch) → **обідав** / **обідала**
*   **повернутися** (to return) → **повернувся** / **повернулася**
*   **вечеряти** (to have dinner) → **вечеряв** / **вечеряла**
*   **лягти** спати (to go to bed) → **ліг** спати / **лягла** спати

The verb **лягти** (to lie down) is particularly unique. A man says **я ліг**, while a woman says **я лягла**. This change from **і** to **я** is a common feature in some old Ukrainian verbs, but for now, just treat them as a pair of set forms for "going to bed."

<!-- INJECT_ACTIVITY: order-daily-routine -->

## Мій учорашній день (My Yesterday)

A natural story combines actions with places, food, and people. That is why the model narrative below mixes routine verbs with familiar vocabulary from earlier modules.

Let us look at a model narrative from Anna. She is describing an **звичайний** (ordinary) day. Pay close attention to how she weaves together her routine, her meals, and her evening relaxation.

**Учора** був **звичайний** день. **Зранку** я **прокинулася** о пів на сьому. Я **поснідала** — їла кашу і пила каву. **Потім** я **пішла** на роботу. **Вдень** я **обідала** в кафе біля офісу. Я замовила салат і сік. Після роботи я **ходила** в магазин і купила **продукти** (groceries). **Ввечері** я готувала вечерю і дивилася **серіал** (TV series). О одинадцятій я **лягла** спати.
> *Yesterday was an ordinary day. In the morning I woke up at half past six. I had breakfast — I ate porridge and drank coffee. Then I went to work. In the afternoon I had lunch in a cafe near the office. I ordered a salad and juice. After work I went to the store and bought groceries. In the evening I was cooking dinner and watching a TV series. At eleven I went to bed.*

If we analyze Anna's story, we can see why it sounds so natural. When Anna talks about her own past actions with **я**, she uses feminine forms such as **прокинулася**, **поснідала**, **пішла**, **обідала**, **ходила**, and **лягла**. Notice, however, that past-tense verbs agree with their subject: in **Учора був звичайний день**, the verb **був** is masculine because **день** is masculine. She also grounds the story with concrete details such as **кафе**, **магазин**, **салат**, and **продукти**.

:::note
Even in a simple story, Ukrainian style prefers to avoid repetition. Anna uses **потім** (then) and **після роботи** (after work) to transition between scenes. This prevents every sentence from starting with "I did this, I did that."
:::

Now it is your turn to build your own narrative. You can use the template below as a guide. Simply choose the verb forms that match your gender and fill in the details of your own life.

**Учора...** (**Учора був гарний день!**)
**Зранку я...** (Select: **прокинувся** / **прокинулася**)
**Потім я...** (Select: **поснідав** / **поснідала** ... **каву / чай / кашу**)
**Вдень я...** (Select: **працював** / **працювала** ... **в офісі / вдома**)
**Ввечері я...** (Select: **дивився** / **дивилася** ... **серіал / фільм**)
**Нарешті я...** (Select: **ліг** / **лягла** ... **спати**)

Try to include at least one **колега** (colleague) or **друг** (friend) in your story to make it more social. The more you practice connecting these chunks, the faster you will move from "translating" to "thinking" in Ukrainian.

<!-- INJECT_ACTIVITY: fill-in-time-markers -->

<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->

## Summary

To narrate your day in Ukrainian, organize the story with time markers such as **зранку**, **вдень**, **ввечері**, and, when needed, **вночі**. Then connect the actions with sequencing words such as **спочатку**, **потім**, **після цього**, and **нарешті** so the story moves clearly from one event to the next.

In this module, we have focused on a core toolkit of routine verbs that cover the vast majority of daily life. Mastering these few forms allows you to describe almost any day:

*   **прокинувся/-лася** (woke up)
*   **поснідав/-ла** (had breakfast)
*   **пішов/пішла** (went)
*   **обідав/-ла** (had lunch)
*   **повернувся/-лася** (returned)
*   **ліг/лягла** спати (went to bed)

The most important rule to remember is agreement in the first person past tense. When you talk about your own actions with **я**, choose the form that matches your gender: for example, **я пішов / я пішла**, **я прокинувся / я прокинулася**. But past-tense verbs still agree with their actual subject, so **день був звичайний** stays masculine because **день** is masculine. Mixing **я пішов** and **я пішла** in the same self-narration is a common learner mistake.

As a final self-check, try to tell the story of your **учора** (yesterday) aloud right now. Use at least five of the routine verbs and three different time markers. If you can tell your story from morning to night without stopping, you have mastered the art of Ukrainian narration!
</generated_module_content>

**PIPELINE NOTE — Word count: 1756 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 131 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Петро — NOT IN VESUM
  ✗ Поліцейський — NOT IN VESUM
  ✗ лася — NOT IN VESUM

All 131 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
