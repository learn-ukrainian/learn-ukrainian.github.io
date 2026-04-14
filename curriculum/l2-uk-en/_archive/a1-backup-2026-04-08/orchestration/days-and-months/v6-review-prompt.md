<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 23: Days and Months (A1, A1.4 [Time and Nature])
**Writer:** Claude
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
## Діало́ги (Dialogues)

**Що ти ро́биш у понеді́лок?** Your friend wants to make plans for the week. How do you answer? You need the days of the week — and in Ukrainian, they carry stories inside their names. But first, listen to two conversations that show how Ukrainians talk about time.

**(Планува́ння ти́жня / Planning the week)**

> — **Тара́с:** Що ти робиш у понеділок? *(What are you doing on Monday?)*
> — **Оле́нка:** Я працю́ю. А у вівто́рок? *(I'm working. And on Tuesday?)*
> — **Тарас:** У вівторок я вивча́ю украї́нську. *(On Tuesday I study Ukrainian.)*
> — **Оленка:** А у субо́ту? *(And on Saturday?)*
> — **Тарас:** У суботу гуля́ю з дру́зями. *(On Saturday I hang out with friends.)*
> — **Оленка:** А в неді́лю? *(And on Sunday?)*
> — **Тарас:** Неді́ля — ві́льний день! *(Sunday is a free day!)*

Taras uses **у понеділок** (on Monday), **у вівторок** (on Tuesday), **у суботу** (on Saturday), and **в неділю** (on Sunday) to talk about his schedule. Each day pairs with **у** or **в** — a small word that means "on" when paired with a day. The endings of the days change slightly in these chunks: **субо́та** becomes **суботу**, **неділя** becomes **неділю**. For now, treat each "у/в + day" combination as a fixed phrase to memorize whole.

**(Ко́ли у тебе́ день наро́дження? / When is your birthday?)**

> — **Марі́я:** Коли у тебе день народження? *(When is your birthday?)*
> — **Андрі́й:** У бе́резні. *(In March.)*
> — **Марія:** Яко́го чи́сла? *(What date?)*
> — **Андрій:** П'ятна́дцятого бе́резня. А у тебе? *(The fifteenth of March. And yours?)*
> — **Марія:** У мене́ в се́рпні. *(Mine is in August.)*
> — **Андрій:** О, це лі́то! Тепло́ і со́нячно. *(Oh, that's summer! Warm and sunny.)*

Here you see the same pattern with months: **у березні** (in March), **в серпні** (in August). The phrase **день народження** (birthday, literally "day of birth") is a fixed expression — memorize it as one unit. Андрій also connects the month to a season: **се́рпень** (August) belongs to **літо** (summer).

Notice how **у** or **в** keeps appearing before time words — **у понеділок**, **у вівторок**, **у березні**, **в серпні**. This is the core pattern of this module. Ukrainian uses **у/в** before days, months, and some seasons. You will see it again and again as we go deeper.

## Дні тижня (Days of the Week)

Ukrainian has seven days, and unlike English, they are always written in **lowercase** — no capital letters. English writes "Monday, Tuesday"; Ukrainian writes **понеділок, вівторок**. A capital letter appears only at the start of a sentence.

Here are all seven, starting from the beginning of the Ukrainian week:

- **понеділок** (Monday)
- **вівторок** (Tuesday)
- **середа́** (Wednesday)
- **четве́р** (Thursday)
- **п'я́тниця** (Friday)
- **субота** (Saturday)
- **неділя** (Sunday)

Ukrainian calendars start the week on **понеділок**, not on Sunday as in some English-speaking countries. One important note: **неділя** means "Sunday," but the word for "week" is **ти́ждень**. In some dialects and older texts, **неділя** can mean "week," but in standard modern Ukrainian, a week is always a **тиждень**.

These names are not random sounds — they tell a story. **Четвер** comes from **четве́ртий** (fourth) — it is the fourth day. **П'ятниця** comes from **п'ять** (five) — the fifth day. **Середа** means "middle" — it sits in the middle of the working week. **Субота** has ancient roots shared with the word "Sabbath," borrowed long ago through Greek. Knowing these connections makes the days easier to remember: four, five, middle — **четвер, п'ятниця, середа**.

<!-- INJECT_ACTIVITY: fill-in-days-order -->

To say "on" a specific day, Ukrainian uses **у** or **в** followed by a special form of the day. Memorize each chunk as a whole phrase:

| Day | "On" that day |
|-----|---------------|
| понеділок | **у понеділок** |
| вівторок | **у вівторок** |
| середа | **у се́реду** |
| четвер | **у четвер** |
| п'ятниця | **у п'я́тницю** |
| субота | **в суботу** |
| неділя | **в неділю** |

Some endings change: **середа** becomes **середу**, **п'ятниця** becomes **п'ятницю**, **субота** becomes **суботу**, **неділя** becomes **неділю**. Others stay the same: **понеділок, вівторок, четвер**. Do not try to figure out the grammar rule behind this yet — just memorize each chunk as a unit, the way a child learns "on Monday" without analyzing why "on" is there.

Here are four sentences showing these chunks in action:

- **Я навча́юся у вівторок і в четвер.** — I study on Tuesday and Thursday.
- **Та́то працю́є у понеділок.** — Dad works on Monday.
- **У п'ятницю ми ди́вимося фільм.** — On Friday we watch a movie.
- **В суботу я сплю до́вго.** — On Saturday I sleep late.

## Мі́сяці і по́ри ро́ку (Months and Seasons)

Ukrainian organizes the year into four seasons, and each season holds three months. The seasons are:

- **Зима́** (winter) — сніг і хо́лод (snow and cold)
- **Весна́** (spring) — кві́ти і тепло (flowers and warmth)
- **Літо** (summer) — со́нце і мо́ре (sun and sea)
- **О́сінь** (autumn) — ли́стя і дощ (leaves and rain)

Now the twelve months, grouped by season — all **lowercase**, just like days:

| Зима (winter) | Весна (spring) | Літо (summer) | Осінь (autumn) |
|---|---|---|---|
| **гру́день** (Dec) | **бе́резень** (Mar) | **че́рвень** (Jun) | **ве́ресень** (Sep) |
| **сі́чень** (Jan) | **кві́тень** (Apr) | **ли́пень** (Jul) | **жо́втень** (Oct) |
| **лю́тий** (Feb) | **тра́вень** (May) | **серпень** (Aug) | **листопа́д** (Nov) |

Ukrainian month names come from nature — not from Roman gods like "January" or "March" in English. **Березень** (March) comes from **бере́за** (birch tree) — birch sap flows in early spring. **Липень** (July) comes from **ли́па** (linden tree) — linden blossoms fill the air in July. **Листопад** (November) literally means "leaves fall" — **листя** (leaves) + **па́дати** (to fall). This is a Ukrainian linguistic fingerprint: the calendar is a nature calendar. All twelve months are masculine gender.

<!-- INJECT_ACTIVITY: match-months-seasons -->

To say "in" a specific month, Ukrainian uses **у/в** with a changed form of the month name. Here are all twelve:

- **у січні** (in January), **у лю́тому** (in February), **в березні** (in March)
- **у квітні** (in April), **у травні** (in May), **в че́рвні** (in June)
- **в ли́пні** (in July), **в серпні** (in August), **у ве́ресні** (in September)
- **в жо́втні** (in October), **в листопа́ді** (in November), **в грудні** (in December)

Notice that **лютий** becomes **у лютому** — it follows a different pattern from the other months because **лютий** is originally an adjective (meaning "fierce" — fierce frosts!), not a noun like the rest.

For seasons, Ukrainian uses special frozen forms that cannot be broken apart. Memorize these four chunks:

- **взи́мку** (in winter)
- **навесні́** (in spring)
- **влі́тку** (in summer)
- **восени́** (in autumn)

These are adverbs — single words, not "у + season." They look different from the season names, so just learn each one by heart.

Two model sentences putting this together:

- **Мій день народження в жовтні.** — My birthday is in October.
- **Влітку я ї́жджу на море.** — In summer I go to the sea.

And four more mixing months and seasons:

- **У грудні хо́лодно — це зима.** — In December it's cold — it's winter.
- **Навесні кві́тнуть дере́ва.** — In spring, trees bloom.
- **В серпні ми відпочива́ємо.** — In August we rest.
- **Восени почина́ється шко́ла.** — In autumn, school begins.

<!-- INJECT_ACTIVITY: fill-in-chunks -->

## Підсумок — Summary

Here is everything organized for quick reference and self-testing.

**Дні тижня** (Days of the week):

- понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя
- Chunks: **у понеділок, у вівторок, у середу, у четвер, у п'ятницю, в суботу, в неділю**

**Місяці** (Months):

- січень, лютий, березень, квітень, травень, червень, липень, серпень, вересень, жовтень, листопад, грудень
- Chunks: **у січні, у лютому, в березні, у квітні, у травні, в червні, в липні, в серпні, у вересні, в жовтні, в листопаді, в грудні**

**Пори року** (Seasons):

- зима, весна, літо, осінь
- Chunks: **взимку, навесні, влітку, восени**

Test yourself — answer these questions in Ukrainian:

- **Яки́й сього́дні день?** — What day is today?
- **Який за́раз мі́сяць?** — What month is it now?
- **Яка зараз пора року?** — What season is it now?
- **Коли у тебе день народження?** — When is your birthday?
- **Що ти робиш у суботу?** — What do you do on Saturday?

Try answering out loud. Use the chunks you learned: **У мене день народження в ...** (My birthday is in ...), **У суботу я ...** (On Saturday I ...). The goal is not to construct these from grammar rules — the goal is to reach for the whole chunk automatically, just as a native speaker does.

**Deterministic word count: 1455 words** (calculated by pipeline, do NOT estimate manually)

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
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
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

Verified: 109 words | Not found: 69 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрі — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Неді — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ П'ятна — NOT IN VESUM
  ✗ Планува — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ биш — NOT IN VESUM
  ✗ вго — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ взи — NOT IN VESUM
  ✗ вимося — NOT IN VESUM
  ✗ влі — NOT IN VESUM
  ✗ втень — NOT IN VESUM
  ✗ втні — NOT IN VESUM
  ✗ вівто — NOT IN VESUM
  ✗ гуля — NOT IN VESUM
  ✗ дження — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ дцятого — NOT IN VESUM
  ✗ ждень — NOT IN VESUM
  ✗ жджу — NOT IN VESUM
  ✗ жня — NOT IN VESUM
  ✗ зями — NOT IN VESUM
  ✗ кві — NOT IN VESUM
  ✗ листопа — NOT IN VESUM
  ✗ лод — NOT IN VESUM
  ✗ лодно — NOT IN VESUM
  ✗ лок — NOT IN VESUM
  ✗ льний — NOT IN VESUM
  ✗ мку — NOT IN VESUM
  ✗ наро — NOT IN VESUM
  ✗ неді — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ ння — NOT IN VESUM
  ✗ нську — NOT IN VESUM
  ✗ нце — NOT IN VESUM
  ✗ нячно — NOT IN VESUM
  ✗ п'я — NOT IN VESUM
  ✗ понеді — NOT IN VESUM
  ✗ рвень — NOT IN VESUM
  ✗ рвні — NOT IN VESUM
  ✗ реду — NOT IN VESUM
  ✗ резень — NOT IN VESUM
  ✗ резня — NOT IN VESUM
  ✗ резні — NOT IN VESUM
  ✗ ресень — NOT IN VESUM
  ✗ ресні — NOT IN VESUM

All 109 other words are confirmed to exist in VESUM.

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
