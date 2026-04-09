<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 51: My Plans (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-051
level: A1
sequence: 51
slug: my-plans
version: '1.2'
title: My Plans
subtitle: У суботу я буду... — scheduling and weekend plans
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Talk about weekend and weekly plans using analytic future
- Schedule activities with specific days and times
- Combine future tense with time expressions (у суботу, о третій, ввечері)
- Invite someone and respond to invitations using future tense
dialogue_situations:
- setting: Group chat planning the weekend — У суботу буду прибирати квартиру (f).
    А я буду бігати в парку (m). Може, ввечері підемо в кіно (n)? Ходімо! О котрій?
  speakers:
  - Група друзів (3 people)
  motivation: Future + scheduling with квартира(f), парк(m), кіно(n)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Making plans: — Що ти будеш робити у суботу? — Зранку я буду прибирати
    квартиру. — А вдень? — Вдень я буду ходити в магазин. А ти? — Я буду відпочивати!
    Може, підемо в кафе ввечері? — Добре! О котрій? — О шостій. Добре? — Чудово! До
    зустрічі у суботу! Future + time + invitation.'
  - 'Dialogue 2 — A busy week: — У тебе є плани на тиждень? — Так, багато! — У понеділок
    я буду працювати допізна. — У вівторок буду вчитися. У середу — зустріч з друзями.
    — А у четвер? — У четвер я буду готувати на вечірку. — А в п''ятницю? — В п''ятницю
    — вечірка! Ти будеш? — Звичайно буду! Days of week + future planning.'
- section: Планування (Planning)
  words: 300
  points:
  - 'Scheduling patterns: У + day: у понеділок, у вівторок, у середу, у четвер, у
    п''ятницю. У суботу / в неділю (on Saturday / on Sunday). О + time: о дев''ятій,
    о третій, о шостій. Зранку / вдень / ввечері (morning / afternoon / evening).
    Combine: У суботу ввечері я буду дивитися фільм.'
  - 'Invitation phrases: Ходімо в кафе! (Let''s go to a cafe! — imperative from M43)
    Може, підемо в кіно? (Maybe we''ll go to the cinema?) Ти будеш вільний/вільна
    у суботу? (Will you be free on Saturday?) Давай зустрінемося о п''ятій! (Let''s
    meet at five!) Responses: Добре! Чудово! З задоволенням! На жаль, не можу.'
- section: Мій тиждень (My Week)
  words: 300
  points:
  - 'Model plan — Taras''s week: У понеділок я буду працювати. Після роботи буду вчити
    українську. У вівторок я буду обідати з другом у кафе. У середу ввечері я буду
    дивитися футбол. У четвер я буду готувати вечерю для родини. У п''ятницю я буду
    відпочивати — піду в кіно. У суботу зранку буду прибирати, а вдень гуляти в парку.
    В неділю я буду спати довго! Each day = буду + activity.'
  - 'Your turn — plan your week: Template: У [day] я буду [activity]. Add details:
    time (о котрій?), place (де?), with whom (з ким?). У суботу о десятій я буду гуляти
    в парку з другом. Use all the A1 vocabulary: places, food, people, activities.'
- section: Summary
  words: 300
  points:
  - 'Planning toolkit: Day + time + буду + infinitive: У суботу о третій я буду готувати
    обід. Invitations: Ходімо! Може, підемо? Давай зустрінемося! Responses: Добре!
    З задоволенням! На жаль, не можу. Days review: понеділок, вівторок, середа, четвер,
    п''ятниця, субота, неділя. Self-check: Plan your ideal weekend — what will you
    do on Saturday and Sunday?'
vocabulary_hints:
  required:
  - план (plan, m)
  - тиждень (week, m)
  - вільний (free, adj)
  - зустріч (meeting, f)
  - відпочивати (to rest)
  - прибирати (to clean)
  - вечірка (party, f)
  recommended:
  - зустрінемося (let's meet — chunk)
  - з задоволенням (with pleasure)
  - на жаль (unfortunately)
  - допізна (until late)
  - звичайно (of course)
  - квартира (apartment, f)
  - кіно (cinema, n)
  - вчити (to study/learn)
activity_hints:
- type: fill-in
  focus: Combine days of the week, time, and future tense
  items:
  - У {понеділок|вівторок|середу} я буду працювати.
  - У суботу {зранку|ввечері|вдень} я буду прибирати квартиру.
  - '{О|В|На} шостій ми будемо дивитися кіно.'
  - У {неділю|суботу|п'ятницю} він буде відпочивати.
  - У п'ятницю {ввечері|зранку|вдень} буде вечірка.
- type: matching
  focus: Match invitations to natural responses
  pairs:
  - Ходімо в кіно!: З задоволенням!
  - Може, підемо в кафе?: Добре! О котрій?
  - Ти будеш вільний у суботу?: На жаль, не можу.
  - Давай зустрінемося о п'ятій!: Чудово! До зустрічі!
- type: fill-in
  focus: Complete a scheduled plan for the week
  items:
  - У вівторок я {буду вчити|вчив|вчу} українську.
  - У середу ми {будемо готувати|готували|готуємо} вечерю.
  - У четвер вона {буде працювати|працювала|працює} допізна.
connects_to:
- a1-052 (My Story)
prerequisites:
- a1-050 (What Will Happen?)
grammar:
- 'Future tense in scheduling: day + time + буду + infinitive'
- 'Invitation patterns: Ходімо! Може, підемо? Давай зустрінемося!'
- 'Day-of-week prepositions: у понеділок, у суботу, в неділю'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Future tense applied in planning and scheduling context.

</plan_content>

## Generated Content

<generated_module_content>
## Dialogues

As we approach the end of our A1 journey, our ability to communicate moves beyond describing the present moment and past events. We are now stepping into the future. Whether you are organizing your weekend, outlining your work schedule, or preparing for graduation, planning is the ultimate social tool. A typical group chat provides the perfect context for friends to coordinate their leisure time. Stating intentions in Ukrainian is surprisingly straightforward, relying on a simple two-part verb structure. The days of the week, specific times, and future verbs combine effortlessly into a complete schedule.

> **Оля:** Що ти будеш робити у суботу? *(What will you be doing on Saturday?)*
> **Максим:** Зранку я буду прибирати квартиру. *(In the morning I will be cleaning the apartment.)*
> **Іра:** А вдень? *(And in the afternoon?)*
> **Максим:** Вдень я буду ходити в магазин. А ти? *(In the afternoon I will go to the store. And you?)*
> **Іра:** Я буду відпочивати! Може, підемо в кафе ввечері? *(I will be resting! Maybe we'll go to a cafe in the evening?)*
> **Оля:** Добре! О котрій? *(Good! At what time?)*
> **Іра:** О шостій. Добре? *(At six. Good?)*
> **Максим:** Чудово! До зустрічі у суботу! *(Wonderful! See you on Saturday!)*

Notice how **Оля** asks **Може, підемо в кіно?** in the plan context, or in this case, **Іра** suggests **Може, підемо в кафе ввечері?**. This is a natural way to propose an idea. The future actions are formed simply: **буду прибирати** (will be cleaning), **буду ходити** (will be going), and **буду відпочивати** (will be resting).

:::note
Notice how the word **план** (plan) behaves just like its English equivalent, but is usually pluralized when asking about general intentions: **У тебе є плани?** (Do you have plans?).
:::

> **Марія:** У тебе є плани на тиждень? *(Do you have plans for the week?)*
> **Петро:** Так, багато! У понеділок я буду працювати допізна. *(Yes, many! On Monday I will work until late.)*
> **Петро:** У вівторок буду вчитися. У середу — зустріч з друзями. *(On Tuesday I will study. On Wednesday — a meeting with friends.)*
> **Марія:** А у четвер? *(And on Thursday?)*
> **Петро:** У четвер я буду готувати на вечірку. *(On Thursday I will cook for the party.)*
> **Марія:** А в п'ятницю? *(And on Friday?)*
> **Петро:** В п'ятницю — вечірка! Ти будеш? *(On Friday — the party! Will you be there?)*
> **Марія:** Звичайно буду! *(Of course I will be!)*

**Петро** outlines his busy week using the word **тиждень** (week). Be careful not to confuse this with **неділя** (Sunday). While they sound similar to words in other Slavic languages, in Ukrainian, **тиждень** is the entire seven-day period, and **неділя** is specifically the day of rest at the end of it.

## Планування (Planning)

To say that an event happens *on* a certain day, English uses the preposition "on". Ukrainian uses the preposition **у** (or its phonetic variant **в**) followed by the day of the week. Because we are showing the time when an action takes place, the day of the week must change its ending if it is a feminine noun. This happens because we are using the temporal accusative case. The masculine and neuter days remain exactly the same, which makes them very easy to remember. The feminine days, however, change their final vowel to «у» or «ю».

- **у понеділок** (on Monday) — masculine, no change.
- **у вівторок** (on Tuesday) — masculine, no change.
- **у середу** (on Wednesday) — feminine, changes from **середа**.
- **у четвер** (on Thursday) — masculine, no change.
- **у п'ятницю** (on Friday) — feminine, changes from **п'ятниця**.
- **у суботу** (on Saturday) — feminine, changes from **субота**.
- **в неділю** (on Sunday) — feminine, changes from **неділя**.

:::caution
English speakers frequently attempt to translate the phrase "on the weekend" word-for-word. In Ukrainian, you must use the specific phrase **на вихідних** (on the weekend). Never use the preposition **в** for this context.
:::

To specify the time of day, use the words **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening). You can easily combine these with the days:
- **У суботу ввечері я буду дивитися фільм.** *(On Saturday evening I will watch a film.)*

When you want to ask someone "At what time?", the natural Ukrainian phrase is **О котрій годині?**. English speakers often try to translate "at seven o'clock" literally by using the preposition "в" (in). This is a common mistake that immediately sounds unnatural. In Ukrainian, you must always use the preposition **о** followed by an ordinal number (first, second, third) in the locative case. Think of it as answering "on which hour?".

- **о третій** (at three)
- **о п'ятій** (at five)
- **о шостій** (at six)
- **о дев'ятій** (at nine)

If the number starts with a vowel sound, the preposition smoothly changes to **об** to avoid two vowels clashing. This makes pronunciation much easier:

- **об одинадцятій** (at eleven)

Now that you can state the day and the time, you need the social tools to invite someone. You can use several natural communicative chunks to propose a plan to your friends or colleagues.

- **Ходімо в кафе!** *(Let's go to a cafe!)*
- **Може, підемо в кіно?** *(Maybe we'll go to the cinema?)*
- **Ти будеш вільний у суботу?** *(Will you be free on Saturday? — asking a male)*
- **Ти будеш вільна у суботу?** *(Will you be free on Saturday? — asking a female)*
- **Давай зустрінемося о п'ятій!** *(Let's meet at five!)*

When someone invites you, you need a polite response. If you are free and willing, you can accept warmly:

- **Добре!** *(Good!)*
- **Чудово!** *(Wonderful!)*
- **З задоволенням!** *(With pleasure!)*

If you have other plans, you should decline politely and clearly:

- **На жаль, не можу.** *(Unfortunately, I cannot.)*

<!-- INJECT_ACTIVITY: fill-in-days-time -->
<!-- INJECT_ACTIVITY: matching-invitations -->

## Мій тиждень (My Week)

The Narrative Model: Taras's Busy Week. These grammatical pieces come together logically in a longer narrative. **Тарас** is planning his entire week, and he combines days, times, and activities into a clear schedule.

- **У понеділок я буду працювати.** *(On Monday I will work.)*
- **Після роботи буду вчити українську.** *(After work I will study Ukrainian.)*
- **У вівторок я буду обідати з другом у кафе.** *(On Tuesday I will dine with a friend in a cafe.)*
- **У середу ввечері я буду дивитися футбол.** *(On Wednesday evening I will watch football.)*
- **У четвер я буду готувати вечерю для родини.** *(On Thursday I will cook dinner for the family.)*
- **У п'ятницю я буду відпочивати — піду в кіно.** *(On Friday I will rest — I will go to the cinema.)*
- **У суботу зранку буду прибирати, а вдень гуляти в парку.** *(On Saturday morning I will clean, and in the afternoon walk in the park.)*
- **В неділю я буду спати довго!** *(On Sunday I will sleep long!)*

Notice how **Тарас** anchors each activity to a specific time and place. He uses the future tense effortlessly. 

:::tip
The verb **бути** (to be) changes to match the speaker (**я буду**, **ми будемо**), but the second verb always remains in its infinitive dictionary form (**працювати**, **вчити**, **відпочивати**). You only conjugate the first word.
:::

Guided Writing Workshop. Now it is your turn to build a schedule. Use the "My Week" template to create your own personalized plan. Start with the basic grammatical framework: **У** [день] **я буду** [що робити]. For example, you can write **У вівторок я буду працювати** (On Tuesday I will work). Once you have established the core sentence, you should add layers of detail to make your schedule richer and more descriptive. Ask yourself specific questions: **о котрій?** (at what time?), **де?** (where?), and **з ким?** (with whom?).

- **У суботу о десятій я буду гуляти в парку з другом.** *(On Saturday at ten I will walk in the park with a friend.)*

When you talk about your schedule, always remember to use the natural Ukrainian construction for possession: **У мене є плани** (I have plans). Do not use the direct English translation "Я маю плани". Using the correct structure makes your spoken Ukrainian sound authentic and natural. Try mapping out your next few days right now using all the vocabulary you know for places, food, people, and daily activities.

<!-- INJECT_ACTIVITY: fill-in-weekly-plan -->

## Summary

Recap of the Planning Toolkit. You now possess the essential grammatical and social tools to organize your future effectively. The grammatical foundation of planning in Ukrainian is the compound future tense, which pairs the helper word **буду** (will) with an infinitive action verb. We anchor these future actions in time using the preposition **у** (or its phonetic variant **в**) for days of the week, and the preposition **о** (or **об**) for specific hours. This precise combination allows you to say exactly when and what you will be doing in any situation:

- **У суботу о третій я буду готувати обід.** *(On Saturday at three I will cook lunch.)*

You also learned the key communicative chunks for making invitations: **Ходімо!**, **Може, підемо?**, and **Давай зустрінемося!**. You can reply with **Добре!**, **З задоволенням!**, or **На жаль, не можу.**

Final Review of Days. Review the days of the week carefully. When used with the preposition **у** to indicate when something happens, it is absolutely vital to remember the difference between the masculine and feminine noun endings. The masculine days remain unchanged in this context, while the feminine days must change their final vowel to «у» or «ю»:

- **понеділок** → **у понеділок**
- **вівторок** → **у вівторок**
- **середа** → **у середу**
- **четвер** → **у четвер**
- **п'ятниця** → **у п'ятницю**
- **субота** → **у суботу**
- **неділя** → **в неділю**

Self-Check. Before moving on to the next module, verify your skills with this checklist.

- Can you say "On Wednesday at six I will be cleaning"? (**У середу о шостій я буду прибирати.**)
- Can you invite a friend to a cafe? (**Може, підемо в кафе?**)
- Can you politely decline an invitation? (**На жаль, не можу.**)
- Can you plan your ideal weekend — what will you do on Saturday and Sunday?
</generated_module_content>

**PIPELINE NOTE — Word count: 1593 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 90 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іра — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Петро — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM

All 90 other words are confirmed to exist in VESUM.

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
