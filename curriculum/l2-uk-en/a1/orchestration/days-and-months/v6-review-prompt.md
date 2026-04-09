<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 23: Days and Months (A1, A1.4 [Time and Nature])
**Writer:** Gemini
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
dialogue_situations:
- setting: At a doctor's reception — booking an appointment
  speakers:
  - Пацієнт
  - Реєстратор
  motivation: 'Days and months: У понеділок? Ні, у середу. В якому місяці?'
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
## Діалоги — Dialogues

Time management and scheduling are essential parts of daily life. In Ukraine, planning revolves around the **тиждень** (week). For anyone accustomed to calendars starting on Sunday, a small mental adjustment is required. The Ukrainian week strictly begins on **понеділок** (Monday). Observe how two friends, Olena and Marko, coordinate their plans for the upcoming week. They use days as time markers to organize their activities.

> **Олена:** Привіт, Марку! Що ти робиш у понеділок? *(Hi Marko! What are you doing on Monday?)*
> **Марко:** У понеділок я працюю. *(On Monday I am working.)*
> **Олена:** А у вівторок? *(And on Tuesday?)*
> **Марко:** У вівторок я вивчаю українську. *(On Tuesday I study Ukrainian.)*
> **Олена:** А у суботу? *(And on Saturday?)*
> **Марко:** У суботу гуляю. Неділя — вільний день! *(On Saturday I walk. Sunday is a free day!)*

Notice how Olena uses the question **Що ти робиш у...?** (What are you doing on...?) to ask about specific days. Marko responds using the exact same grammatical structure to state his plans. He also highlights a very important lifestyle concept: **неділя — вільний день** (Sunday is a free day). A **вільний день** (free day) is a day without professional obligations, which contrasts directly with a **робочий день** (work day). 

When discussing birthdays, the vocabulary naturally shifts from days of the week to months and seasons. Read how Andriy and Sofia discuss their birthdays.

> **Андрій:** Софіє, коли у тебе день народження? *(Sofia, when is your birthday?)*
> **Софія:** У березні. *(In March.)*
> **Андрій:** Якого числа? *(What date?)*
> **Софія:** П'ятнадцятого березня. *(The fifteenth of March.)*
> **Андрій:** Це весна? *(Is that spring?)*
> **Софія:** Так, початок весни. *(Yes, the beginning of spring.)*

When Andriy wants to know the exact day, he asks **Якого числа?** (What date?). For now, treat both the question **Якого числа?** and the response **П'ятнадцятого березня** (The fifteenth of March) as fixed vocabulary chunks to memorize.

## Дні тижня — Days of the Week

To effectively plan a schedule, the seven days of the week are required. In order, they are: **понеділок** (Monday), **вівторок** (Tuesday), **середа** (Wednesday), **четвер** (Thursday), **п'ятниця** (Friday), **субота** (Saturday), and **неділя** (Sunday). There are two golden rules you must remember about the Ukrainian calendar. First, days of the week are never capitalized in Ukrainian unless they start a sentence. They are common nouns. Second, the week always starts on Monday. 

When you want to say that something happens "on" a specific day, you use the prepositions **у** or **в** followed by the day. The ending of the word might change depending on its gender. For masculine days, the form remains completely stable. You simply add the preposition: **у понеділок** (on Monday), **у вівторок** (on Tuesday), **у четвер** (on Thursday). For feminine days ending in a vowel, the final vowel shifts to an -у or -ю sound. You simply memorize this pattern: **середа** → **у середу** (on Wednesday), **п'ятниця** → **у п'ятницю** (on Friday), **неділя** → **в неділю** (on Sunday). The same rule applies to Saturday: **субота** → **в суботу** (on Saturday).

Let us focus specifically on the word **неділя** (Sunday). For learners coming from other Slavic languages, this word can be a tricky false friend. In Russian, a similar-sounding word means "week." In Ukrainian, **неділя** only means Sunday. The etymology is fascinating and helps anchor its meaning: it comes from the phrase "не ділати," which translates to "not to work." Note that while **неділя** means Sunday in standard Ukrainian, in some regional dialects it can also mean "week." However, the standard word for "week" is always **тиждень**.

To talk about your week broadly, you can group the days into two main categories. The days from Monday to Friday are called **робочі дні** (work days). The days of rest, Saturday and Sunday, are called **вихідні** (the weekend). In Ukrainian elementary schools, such as in the Grade 2 textbook by Vashulenko, students learn days of the week by creating a personal weekly schedule.

*   **У робочі дні я в офісі.** (On work days I am at the office.)
*   **У вихідні я вдома.** (On the weekend I am at home.)

<!-- INJECT_ACTIVITY: fill-in-days-order -->

## Місяці і пори року — Months and Seasons

Just as the days form a week, the twelve months form a year. In Ukrainian schools, such as in the Grade 2 textbook by Vashulenko, months are introduced through seasonal stories and poems, connecting the vocabulary directly to the natural world. The twelve months organized by their respective season are listed below. All are written in lowercase letters.

*   **Зима** (Winter): **грудень** (December), **січень** (January), **лютий** (February).
*   **Весна** (Spring): **березень** (March), **квітень** (April), **травень** (May).
*   **Літо** (Summer): **червень** (June), **липень** (July), **серпень** (August).
*   **Осінь** (Autumn): **вересень** (September), **жовтень** (October), **листопад** (November).

The story of the Ukrainian months is deeply rooted in the natural world. While English and Russian use names derived from the ancient Latin calendar, Ukrainian has preserved its native Slavic system. The names describe exactly what is happening in nature. For example, **березень** (March) comes from the word for birch tree, as this is when birch sap begins to flow. **Квітень** (April) is related to flowers blooming. **Липень** (July) is named after the linden tree. **Вересень** (September) is tied to the blooming of heather. Perhaps the most obvious is **листопад** (November), which literally means "leaf fall."

When you want to say that something happens "in" a specific month, you again use the prepositions **у** or **в**. However, months require a different grammatical ending than days. You must add the ending **-і** to the base word. Often, the final fleeting vowel **-е-** in the month's name drops out. Here is the pattern you need to learn: **січень** → **у січні** (in January), **березень** → **у березні** (in March), **квітень** → **у квітні** (in April), **жовтень** → **у жовтні** (in October). The exception is **лютий**, which takes a different ending: **у лютому** (in February).

Finally, you also need to know how to say "in" a specific season. When acting as an adverb to answer the question "when?", the seasons take irregular forms that you simply must memorize as fixed vocabulary items: **взимку** (in winter), **навесні** (in spring), **влітку** (in summer), **восени** (in autumn). Compare these to the base nouns: **зима**, **весна**, **літо**, **осінь**.

<!-- INJECT_ACTIVITY: match-up-months-seasons -->

<!-- INJECT_ACTIVITY: fill-in-day-month-chunks -->

## Підсумок — Summary

To help organize the calendar vocabulary, here is a consolidated reference table mapping the base noun, which answers the question **Що?** (What?), to the time expression, which answers the question **Коли?** (When?).

| Що? (What?) | Коли? (When?) |
| :--- | :--- |
| **понеділок** | **у понеділок** |
| **середа** | **у середу** |
| **січень** | **у січні** |
| **зима** | **взимку** |

Learning this vocabulary is a vital step in thinking like a Ukrainian. By using native Slavic names like **березень** instead of Latin-based alternatives, and by structuring your week to begin on **понеділок**, you are aligning yourself with the cultural rhythms of Ukraine. Remember to practice the soft endings on months like **січень** and **вересень** to make your pronunciation sound natural and authentic. The soft sign **ь** indicates that the preceding consonant is soft.

Answer the following questions based on today's actual date and your own life. Speak the answers out loud to practice forming the complete phrases.

*   Який сьогодні день тижня? (Сьогодні ...)
*   Який зараз місяць? (Зараз ...)
*   Яка зараз пора року? (Зараз ...)
*   Коли у тебе день народження? (Мій день народження у ...)
*   Що ти робиш у суботу? (У суботу я ...)

Mastering these basic questions provides the confidence to schedule meetings, talk about the past, and make plans for the future in Ukrainian.
</generated_module_content>

**PIPELINE NOTE — Word count: 1286 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 89 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Софія — NOT IN VESUM
  ✗ Софіє — NOT IN VESUM

All 89 other words are confirmed to exist in VESUM.

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
