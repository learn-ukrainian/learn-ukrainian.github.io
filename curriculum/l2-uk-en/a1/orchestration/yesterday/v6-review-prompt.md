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

Being able to say what you did in the past is useful, but the real power of language comes from telling a story. Up until now, we have looked at isolated past tense sentences. Moving from a single statement to a connected narrative changes how you communicate. Compare a present tense fact like **Сьогодні я працюю** (Today I am working) with a past narrative like **Учора я працював** (Yesterday I worked). Knowing how to chain these actions together allows you to describe exactly what happened, step by step.

Sequencing actions is crucial when facts matter. In the situation below, a witness speaks to a police officer about a stolen bicycle. The witness uses past tense verbs to build a precise timeline of events.

> **Свідок:** Я припаркував велосипед біля магазину. *(I parked the bicycle near the store.)*
> **Поліцейський:** А потім? *(And then?)*
> **Свідок:** Потім зайшов у кав'ярню. *(Then I went into the cafe.)*
> **Поліцейський:** Ви довго там були? *(Were you there long?)*
> **Свідок:** Ні. Коли вийшов, велосипед зник. *(No. When I came out, the bicycle disappeared.)*
> **Поліцейський:** Ви бачили когось? *(Did you see anyone?)*
> **Свідок:** Бачив чоловіка в куртці та кепці. *(I saw a man in a jacket and a cap.)*

The words **велосипед** (bicycle) and **магазин** (store) are masculine, while **кав'ярня** (cafe) and **куртка** (jacket) are feminine. The sequence of verbs — **припаркував** (parked), **зайшов** (went in), **вийшов** (came out) — creates a clear, undeniable timeline of the incident.

:::note
When the order of events matters, using clear past tense verbs in sequence is essential. In official situations, a well-structured narrative establishes the facts without confusion.
:::

Narrating a day is just as common in casual conversation. Friends frequently catch up on a typical work day and discuss their routines.

> **Олег:** Як пройшов твій день? *(How was your day?)*
> **Тарас:** Добре! Зранку я прокинувся о сьомій. *(Good! In the morning I woke up at seven.)*
> **Олег:** Що ти робив зранку? *(What did you do in the morning?)*
> **Тарас:** Я поснідав і пішов на роботу. *(I had breakfast and went to work.)*
> **Олег:** А вдень? *(And in the afternoon?)*
> **Тарас:** Вдень я працював і обідав з колегою. *(In the afternoon I worked and had lunch with a colleague.)*
> **Олег:** А ввечері? *(And in the evening?)*
> **Тарас:** Ввечері я дивився фільм і рано ліг спати. *(In the evening I watched a film and went to sleep early.)*

And here is how someone might describe a fun weekend:

> **Максим:** Що ти робила у суботу? *(What did you do on Saturday?)*
> **Ірина:** О, я мала чудовий день! *(Oh, I had a wonderful day!)*
> **Максим:** Розкажи! *(Tell me!)*
> **Ірина:** Зранку я ходила на ринок і купила фрукти. *(In the morning I went to the market and bought fruit.)*
> **Максим:** А потім? *(And then?)*
> **Ірина:** Потім я готувала обід. А вдень гуляла в парку. *(Then I cooked lunch. And in the afternoon I walked in the park.)*
> **Максим:** А ввечері? *(And in the evening?)*
> **Ірина:** Ввечері ми з подругою ходили в ресторан. *(In the evening my friend and I went to a restaurant.)*
> **Максим:** Як файно! *(How nice!)*

Notice how the words **потім** (then) and the phrase **а потім** (and then) act as the glue between different verbs. They keep the story moving forward efficiently. Furthermore, in a connected story, we do not need to repeat the subject **я** (I) in every single sentence. Once the context is established, the verbs themselves carry the narrative perfectly.

## Розповідь про день (Narrating a Day)

To structure any story, you need clear time anchors. The daily routine is typically divided into four main parts. We use **зранку** (in the morning) for the start of the day. As the day progresses, we use **вдень** (in the afternoon). Later, we transition to **ввечері** (in the evening), and finally **вночі** (at night). 

:::caution
Pay attention to the spelling of **вдень**. Written as one word, it means "in the daytime" or "in the afternoon". Do not confuse it with the two-word phrase **в день** (on the day), which is used differently, such as in **в день народження** (on the birthday).
:::

Using the correct time markers gives the listener a clear map of when events occurred. Beyond basic time markers, sequencing words create a chronological chain. Without them, a story is just a list of disconnected facts. Start the sequence with **спочатку** (first). To transition to the next action, use **потім** (then). For further actions, use **після цього** (after that). To conclude the narrative, use **нарешті** (finally). These connectors turn separate thoughts into a fluid story.

*   **Спочатку я поснідав.** *(First I had breakfast.)*
*   **Потім я пішов на роботу.** *(Then I went to work.)*
*   **Після цього я обідав.** *(After that I had lunch.)*

This logical flow makes your Ukrainian sound much more natural and cohesive.

The daily routine relies on a core set of action verbs. Because the Ukrainian past tense must agree with the grammatical gender of the speaker, males use the **-в** or **-вся** ending, while females use the **-ла** or **-лася** ending. The most frequent verbs for narrating a day follow this pattern:

| Дієслово (Infinitive) | Чоловічий рід (Masculine) | Жіночий рід (Feminine) |
| :--- | :--- | :--- |
| **прокинутися** *(to wake up)* | **прокинувся** | **прокинулася** |
| **поснідати** *(to have breakfast)* | **поснідав** | **поснідала** |
| **піти** *(to go)* | **пішов** | **пішла** |
| **обідати** *(to have lunch)* | **обідав** | **обідала** |
| **повернутися** *(to return)* | **повернувся** | **повернулася** |
| **лягти спати** *(to lie down to sleep)* | **ліг спати** | **лягла спати** |

Notice that for the verb meaning to lie down (**лягти**), the masculine form **ліг** drops the **-в** suffix entirely, while the feminine form **лягла** keeps the standard **-ла** ending. This is a common pattern for verbs with stems ending in a consonant.

<!-- INJECT_ACTIVITY: ordering-daily-routine -->

## Мій учорашній день (My Yesterday)

A complete narrative relies on these structural elements. Anna describes her yesterday below. Since Anna is female, every past tense verb she uses ends in **-ла** or **-лася**. Her story chains actions logically using time markers.

*   **Учора був звичайний день.** *(Yesterday was an ordinary day.)*
*   **Зранку я прокинулася о пів на сьому.** *(In the morning I woke up at half past six.)*
*   **Я поснідала — їла кашу і пила каву.** *(I had breakfast — I ate porridge and drank coffee.)*
*   **Потім я пішла на роботу.** *(Then I went to work.)*
*   **Вдень я обідала в кафе біля офісу.** *(In the afternoon I had lunch in a cafe near the office.)*
*   **Я замовила салат і сік.** *(I ordered a salad and juice.)*
*   **Після роботи я ходила в магазин і купила продукти.** *(After work I went to the store and bought groceries.)*
*   **Ввечері я готувала вечерю і дивилася серіал.** *(In the evening I cooked dinner and watched a TV series.)*
*   **О одинадцятій я лягла спати.** *(At eleven I went to sleep.)*

This narrative is highly structured. Starting with **звичайний день** (ordinary day) sets the context immediately. Notice the strict gender agreement between the speaker and her actions. Because Anna is speaking, every verb aligns with her feminine gender: **прокинулася** (woke up), **поснідала** (had breakfast), **пішла** (went), **обідала** (had lunch), **купила** (bought), **готувала** (cooked), and **лягла** (lay down). If a man were telling this exact same story, all of those endings would shift to the masculine forms. 

:::tip
The pronoun **я** (I) remains the same, so the verb ending is the only indicator of the speaker's gender. Memorize the ending that matches your own gender and use it consistently.
:::

It is your turn to build a narrative. Use the following template to structure your thoughts:

*   **Учора...** *(Yesterday...)*
*   **Зранку я...** *(In the morning I...)*
*   **Потім...** *(Then...)*
*   **Вдень я...** *(In the afternoon I...)*
*   **Ввечері я...** *(In the evening I...)*

Combine these past-tense verbs with places you already know, such as a **кафе** (cafe), a **парк** (park), or a **магазин** (store). Add food items like **каша** (porridge), **кава** (coffee), or a **салат** (salad). You can also include the people you interacted with, whether it was a **друг** (friend), a **колега** (colleague), or a **подруга** (female friend). Everything you learned in A1 comes together here to help you share your personal story clearly and accurately.

<!-- INJECT_ACTIVITY: fill-in-narrative-flow -->
<!-- INJECT_ACTIVITY: gender-consistency-drill -->

## Summary

The narration toolkit contains the elements needed to describe past experiences. Telling a coherent story requires organizing verbs with time anchors and maintaining strict grammatical consistency.

*   **Time structure:** **зранку** → **вдень** → **ввечері** → **вночі**.
*   **Sequencing:** **спочатку**, **потім**, **після цього**, **нарешті**.
*   **Daily routine past forms:** **прокинувся/-лася**, **поснідав/-ла**, **пішов/пішла**, **обідав/-ла**, **повернувся/-лася**, **ліг/лягла спати**.
*   **Gender consistency:** male speakers use **-в/-вся** forms throughout, female speakers use **-ла/-лася** throughout.

Before you finish, perform a final self-check on your storytelling skills. Ask yourself these questions when building a narrative:

*   **Чи використав я принаймні 5 дієслів у минулому часі?** *(Did I use at least 5 verbs?)*
*   **Чи всі дієслова мають однаковий рід (чоловічий або жіночий)?** *(Are all verbs the same gender?)*
*   **Чи є в моїй розповіді «спочатку» і «потім»?** *(Are there "first" and "then"?)*

Tell the story of your yesterday using at least 5 verbs aloud, either to a partner or to yourself. Make absolutely sure to include what you ate for breakfast, using **поснідав** or **поснідала**, and mention when you went to sleep, using **ліг спати** or **лягла спати**. Practice this daily until the sequence feels natural and your verb endings match your gender automatically.
</generated_module_content>

**PIPELINE NOTE — Word count: 1506 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 138 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Поліцейський — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ лася — NOT IN VESUM

All 138 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
