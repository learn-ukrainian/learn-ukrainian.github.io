# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 23: Days and Months (A1, A1.4 [Time and Nature])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-023
level: A1
sequence: 23
slug: days-and-months
version: '1.2'
title: Days and Months
subtitle: У понеділок, у січні — the calendar in Ukrainian
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Name all 7 days of the week and use "on" (у/в + day as chunk)
- Name all 12 months and 4 seasons
- Say dates using ordinal numbers (as chunks)
- Plan a week using days, times, and activities
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Planning the week (ULP Ep15 pattern): — Що ти робиш у понеділок?
    — Я працюю. А у вівторок? — У вівторок я вивчаю українську. — А у суботу? — У
    суботу гуляю. Неділя — вільний день! Days of the week in practical scheduling.'
  - Dialogue 2 — When is your birthday? — Коли у тебе день народження? — У березні.
    — Якого числа? — П'ятнадцятого березня. А у тебе? — У мене в серпні. — О, це літо!
    Months and seasons in personal context.
- section: Дні тижня (Days of the Week)
  words: 300
  points:
  - 'Seven days — all LOWERCASE in Ukrainian (not capitalized like English): понеділок
    (Monday), вівторок (Tuesday), середа (Wednesday), четвер (Thursday), п''ятниця
    (Friday), субота (Saturday), неділя (Sunday). Вашуленко Grade 2 p.83: planning
    your week activity. Note: неділя = Sunday AND ''week'' in some dialects. Standard
    ''week'' = тиждень.'
  - '''On'' a day = у/в + accusative (chunk — no grammar analysis): у понеділок, у
    вівторок, у середу, у четвер, у п''ятницю, в суботу, в неділю. Note the endings
    change — just memorize each form.'
- section: Місяці і пори року (Months and Seasons)
  words: 300
  points:
  - '12 months — also lowercase, organized by season: Зима: грудень (Dec), січень
    (Jan), лютий (Feb). Весна: березень (Mar), квітень (Apr), травень (May). Літо:
    червень (Jun), липень (Jul), серпень (Aug). Осінь: вересень (Sep), жовтень (Oct),
    листопад (Nov). All months are masculine. Many come from nature words (березень
    ← береза, липень ← липа, листопад ← листя падає).'
  - '4 seasons: зима (winter, f), весна (spring, f), літо (summer, n), осінь (autumn,
    f). ''In'' a month/season = у/в + locative (chunk): у січні, у лютому, в березні...
    влітку, взимку, восени, навесні. Seasonal forms are irregular — memorize as chunks.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Calendar vocabulary: Days: понеділок → неділя (у понеділок, в суботу). Months:
    січень → грудень (у січні, в серпні). Seasons: зима, весна, літо, осінь (взимку,
    навесні, влітку, восени). Self-check: What day is today? What month? What season?
    When is your birthday? Plan your next week in Ukrainian.'
vocabulary_hints:
  required:
  - понеділок, вівторок, середа (Mon, Tue, Wed)
  - четвер, п'ятниця (Thu, Fri)
  - субота, неділя (Sat, Sun)
  - тиждень (week, m)
  - зима, весна, літо, осінь (winter, spring, summer, autumn)
  recommended:
  - січень, лютий, березень (Jan, Feb, Mar)
  - квітень, травень, червень (Apr, May, Jun)
  - липень, серпень, вересень (Jul, Aug, Sep)
  - жовтень, листопад, грудень (Oct, Nov, Dec)
  - день народження (birthday)
activity_hints:
- type: fill-in
  focus: Put days of the week in order
  items:
  - понеділок, {вівторок|субота|четвер}, середа
  - середа, {четвер|п'ятниця|неділя}, п'ятниця
  - п'ятниця, {субота|вівторок|середа}, неділя
  - неділя, {понеділок|вівторок|четвер}, вівторок
  - вівторок, середа, {четвер|п'ятниця|неділя}
  - четвер, п'ятниця, {субота|понеділок|вівторок}
  - субота, {неділя|понеділок|п'ятниця}, понеділок
- type: match-up
  focus: Match the month to the correct season
  pairs:
  - січень ↔ зима
  - квітень ↔ весна
  - липень ↔ літо
  - жовтень ↔ осінь
  - лютий ↔ зима
  - травень ↔ весна
  - серпень ↔ літо
  - листопад ↔ осінь
- type: fill-in
  focus: Use the correct 'in/on' chunk for days and months
  items:
  - Я працюю {у понеділок|понеділок|в понеділок}.
  - Мій день народження {у березні|березень|в березень}.
  - Ми гуляємо {в суботу|субота|у субота}.
  - '{Взимку|Зима|У зима} холодно.'
  - Я вивчаю українську {у вівторок|вівторок|в вівторок}.
  - Вони відпочивають {у серпні|серпень|в серпень}.
connects_to:
- a1-024 (Weather)
prerequisites:
- a1-022 (What Time?)
grammar:
- 'Days of the week: у/в + accusative chunk (у понеділок, в суботу)'
- 'Months: у/в + locative chunk (у січні)'
- 'Seasons: adverbial forms (взимку, навесні, влітку, восени)'
register: розмовний
references:
- title: Вашуленко Grade 2, p.83
  notes: Planning your week — days of the week activity.
- title: Вашуленко Grade 2, p.69-89
  notes: Months through seasonal stories and poems.
- title: ULP Season 1, Episode 15
  url: https://www.ukrainianlessons.com/episode15/
  notes: Days of the week and planning.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Time shapes our daily routines. Whenever you want to arrange a meeting with a friend, plan a study session, or ask about an upcoming celebration, you rely on the vocabulary of the calendar. Mastering the names of the days and months is an essential step toward full independence in a new language. Before we examine the individual words, let us observe how native speakers use them in real life.

Below is a brief exchange between two colleagues. Notice how they inquire about each other's schedules.

<div class="dialogue">


**Марія:** Що ти робиш у понеділок? *(What are you doing on Monday?)*


**Олег:** Я працюю. А у вівторок? *(I am working. And on Tuesday?)*


**Марія:** У вівторок я вивчаю українську. *(On Tuesday I study Ukrainian.)*


**Олег:** А у суботу? *(And on Saturday?)*


**Марія:** У суботу гуляю. *(On Saturday I go for a walk.)*


**Олег:** Неділя — вільний день! *(Sunday is a free day!)*


</div>



In this conversation, Maria asks a direct question: «Що ти робиш у понеділок?». Oleg replies efficiently: «Я працюю». In Ukrainian, the present tense verb covers both the simple and continuous meanings found in English. You do not need extra auxiliary words to say "I am working." When Maria and Oleg mention a specific day, they place the preposition **у** right before it. 

Now, consider a different scenario. How do you talk about the time of year you were born? Pay attention to the way the months and seasons are mentioned in this second dialogue.

<div class="dialogue">


**Анна:** Коли у тебе день народження? *(When is your birthday?)*


**Богдан:** У березні. *(In March.)*


**Анна:** Якого числа? *(What date?)*


**Богдан:** П'ятнадцятого березня. А у тебе? *(On the fifteenth of March. And you?)*


**Анна:** У мене в серпні. *(Mine is in August.)*


**Богдан:** О, це літо! *(Oh, that is summer!)*


</div>



When Bogdan answers the question about his birthday, he first gives the broad time frame: «У березні». When pressed for details, he provides the exact date: «П'ятнадцятого березня». The word **число** translates to "number" or "date" in this context. The phrase «Якого числа?» is the standard way to ask for a specific calendar date. Finally, the conversation ends with a realization about the season of the year.

## Дні тижня (Days of the Week)

In Ukraine, the standard calendar week begins on Monday. This structure makes logical sense: you dedicate your energy to work or study for five days, and the weekend sits exactly at the end of the row. When you write these days in a sentence, remember a simple rule: they are always written in lowercase letters.

Here are the seven days of the week:

*   **понеділок** (Monday)
*   **вівторок** (Tuesday)
*   **середа** (Wednesday)
*   **четвер** (Thursday)
*   **п'ятниця** (Friday)
*   **субота** (Saturday)
*   **неділя** (Sunday)

The names of these days possess fascinating historical meanings. The word **середа** comes from the concept of «середина» (middle), marking the exact middle of the traditional working week. The words **четвер** and **п'ятниця** are directly related to the numbers four and five. The word **неділя** historically means a day when you "do nothing" (не ділати) — a designated day of rest. And **понеділок** simply means the day that comes "after Sunday" (по неділі).

:::tip
The standard Ukrainian word for "week" is **тиждень**. However, in some regional dialects, you might hear people use the word **неділя** to mean the entire week, not just Sunday! For clear communication, stick to **тиждень** when you mean "week."
:::

When you want to say that something happens *on* a specific day, you do not just use the basic dictionary word. Instead, you add the preposition **у** or **в** and change the ending of the word. At this stage, you do not need to analyze the complex grammar rules behind these changes. It is much faster and more effective to simply memorize them as fixed chunks.

Here are the chunks you need to successfully plan your week:

*   **у понеділок** (on Monday)
*   **у вівторок** (on Tuesday)
*   **у середу** (on Wednesday)
*   **у четвер** (on Thursday)
*   **у п'ятницю** (on Friday)
*   **в суботу** (on Saturday)
*   **в неділю** (on Sunday)

In Ukrainian elementary schools, children learn to organize their time using a weekly planner. If you look at a textbook like *Вашуленко* for Grade 2, you will see practical exercises where students write down their daily routines to understand this concept. They practice saying things like:

*   **Я читаю в суботу.** (I read on Saturday.)
*   **Ми гуляємо в неділю.** (We go for a walk on Sunday.)

:::fill-in
title: "Put days of the week in order"
---
- sentence: "понеділок, {вівторок|субота|четвер}, середа"
- sentence: "середа, {четвер|п'ятниця|неділя}, п'ятниця"
- sentence: "п'ятниця, {субота|вівторок|середа}, неділя"
- sentence: "неділя, {понеділок|вівторок|четвер}, вівторок"
- sentence: "вівторок, середа, {четвер|п'ятниця|неділя}"
- sentence: "четвер, п'ятниця, {субота|понеділок|вівторок}"
- sentence: "субота, {неділя|понеділок|п'ятниця}, понеділок"
:::

## Місяці і пори року (Months and Seasons)

The Ukrainian year is divided into four distinct seasons. These seasons dictate the rhythm of life, agriculture, and cultural celebrations. The transition between seasons in Ukraine is visually striking, and the language reflects this dramatic change. Winter brings deep snow, spring thaws the frozen earth, summer is warm and golden, and autumn paints the forests in vibrant colors.

The four seasons are:

*   **зима** (winter)
*   **весна** (spring)
*   **літо** (summer)
*   **осінь** (autumn)

Within these four seasons, we have twelve months. Just like the days of the week, the names of the months are always written in lowercase. Furthermore, all twelve months in Ukrainian are grammatically masculine words.

Instead of borrowing names from the Roman calendar, the Ukrainian language preserves an ancient, highly descriptive system. The names of the months are deeply connected to nature, weather, and the agricultural cycle. Learning these words feels like taking a walk through a traditional Ukrainian village.

Let us look at the months organized by their season:

**Зима** (Winter)
*   **грудень** (December) — from **груда** (frozen clod of earth), when the wet ground freezes into hard lumps.
*   **січень** (January) — from **сікти** (to cut), because winter was the traditional season for felling timber in the forest.
*   **лютий** (February) — meaning "fierce" or "angry," describing the harsh winter weather.

**Весна** (Spring)
*   **березень** (March) — from **береза** (birch tree), when the birch sap begins to flow.
*   **квітень** (April) — from **квітка** (flower), the beautiful month of blooming.
*   **травень** (May) — from **трава** (grass), when the whole world turns vibrant green.

**Літо** (Summer)
*   **червень** (June) — from **червоний** (red), when the red berries ripen.
*   **липень** (July) — from **липа** (linden tree), which blossoms and provides sweet honey.
*   **серпень** (August) — from **серп** (sickle), the traditional tool used for the grain harvest.

**Осінь** (Autumn)
*   **вересень** (September) — from **верес** (heather), an evergreen plant that blooms in early autumn.
*   **жовтень** (October) — from **жовтий** (yellow), the color of the falling autumn leaves.
*   **листопад** (November) — literally meaning **листя падає** (leaves fall).

When you want to say that an event happens *in* a specific month, you must use the preposition **у** or **в**. The ending of the month also changes. Most months end in **-і**, while **лютий** changes to **лютому**. Memorize these forms as set chunks:

*   **у січні** (in January)
*   **у лютому** (in February)
*   **у березні** (in March)
*   **у квітні** (in April)
*   **у травні** (in May)
*   **у червні** (in June)
*   **у липні** (in July)
*   **у серпні** (in August)
*   **у вересні** (in September)
*   **у жовтні** (in October)
*   **у листопаді** (in November)
*   **у грудні** (in December)

When talking about seasons, you do not use the preposition **у**. Instead, Ukrainian uses special single-word adverb forms to mean "in the winter" or "in the summer."

*   **взимку** (in winter)
*   **навесні** (in spring)
*   **влітку** (in summer)
*   **восени** (in autumn)

Let us look at some practical examples of how to use these seasonal adverbs in complete sentences:

*   **Взимку дуже холодно.** (In winter it is very cold.)
*   **Навесні тепло.** (In spring it is warm.)
*   **Влітку я гуляю.** (In summer I walk.)
*   **Восени ми читаємо.** (In autumn we read.)

These adverbs are incredibly useful because they do not require any extra prepositions. You simply place the adverb at the beginning or end of your sentence.

:::match-up
title: "Match the month to the correct season"
---
- left: "січень"
  right: "зима"
- left: "квітень"
  right: "весна"
- left: "липень"
  right: "літо"
- left: "жовтень"
  right: "осінь"
- left: "лютий"
  right: "зима"
- left: "травень"
  right: "весна"
- left: "серпень"
  right: "літо"
- left: "листопад"
  right: "осінь"
:::

## Підсумок — Summary

You now have the essential vocabulary you need to navigate the calendar in Ukrainian. You know the seven days of the week, starting with the busy **понеділок** and ending with the restful **неділя**. You also know the four distinct seasons: **зима**, **весна**, **літо**, and **осінь**.

The twelve months of the year offer a beautiful reflection of the natural world, from the freezing, cutting winds of **січень** to the vibrant blooming flowers of **квітень** and the falling leaves of **листопад**.

The most important grammatical skill you practiced today is how to form time chunks. Instead of analyzing complex case endings every time you speak, you can simply memorize these fixed phrases.

For days of the week, use **у** or **в** followed by the specific day form:
*   **у понеділок** (on Monday)
*   **в суботу** (on Saturday)

For months, use **у** or **в** followed by the modified month name:
*   **у січні** (in January)
*   **у серпні** (in August)

For seasons, use the special single-word adverbial forms:
*   **взимку** (in winter)
*   **навесні** (in spring)
*   **влітку** (in summer)
*   **восени** (in autumn)

You also practiced one more important skill in the dialogues: saying a specific date. When someone asks «Якого числа?» (What date?), you answer with an ordinal number in the genitive case. At this stage, memorize these as chunks:

*   **першого січня** (on the first of January)
*   **п'ятнадцятого березня** (on the fifteenth of March)
*   **двадцять п'ятого грудня** (on the twenty-fifth of December)

The pattern is always the same: ordinal number + month in genitive. You already saw this in the dialogue when Bogdan said «П'ятнадцятого березня». As you learn more numbers, you will be able to say any date.

Now test yourself. Try to answer each question out loud in Ukrainian:

*   Який сьогодні день тижня? *(What day of the week is it today?)*
*   Який зараз місяць? *(What month is it now?)*
*   Яка зараз пора року? *(What season is it now?)*
*   Коли у тебе день народження? Якого числа? *(When is your birthday? What date?)*
*   Що ти робиш у понеділок? А в суботу? *(What do you do on Monday? And on Saturday?)*

If you can answer all five questions, you have mastered the Ukrainian calendar. You are ready to plan your week, talk about your birthday, and describe the seasons like a native speaker.

:::fill-in
title: "Use the correct in/on chunk for days and months"
---
- sentence: "Я працюю {у понеділок|понеділок|на понеділок}."
- sentence: "Мій день народження {у березні|березень|в березень}."
- sentence: "Ми гуляємо {в суботу|субота|у субота}."
- sentence: "{Взимку|Зима|У зима} холодно."
- sentence: "Я вивчаю українську {у вівторок|вівторок|на вівторок}."
- sentence: "Вони відпочивають {у серпні|серпень|в серпень}."
:::

**Deterministic word count: 1680 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
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

Verified: 112 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Богдан — NOT IN VESUM
  ✗ Вашуленко — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Олег — NOT IN VESUM

All 112 other words are confirmed to exist in VESUM.

</vesum_verification>