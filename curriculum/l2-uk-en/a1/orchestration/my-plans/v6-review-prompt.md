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

Weekend plans are a natural context for the future tense. In this dialogue, three friends share a **план**, ask when something will happen, and invite each other out.

> **Оксана:** Що ти будеш робити у суботу? *(What will you be doing on Saturday?)*
> **Максим:** Зранку я буду прибирати квартиру. *(In the morning, I will be cleaning the apartment.)*
> **Оксана:** А вдень? *(And in the afternoon?)*
> **Максим:** Вдень я буду ходити в магазин. А ти? *(In the afternoon, I will go to the store. And you?)*
> **Дарина:** Я буду відпочивати! Може, підемо в кафе ввечері? *(I will be resting! Maybe we will go to a cafe in the evening?)*
> **Оксана:** Добре! О котрій? *(Good! At what time?)*
> **Дарина:** О шостій. Добре? *(At six. Good?)*
> **Максим:** Чудово! До зустрічі у суботу! *(Great! See you on Saturday!)*

This short conversation is rich with real-world communication patterns. Notice how Максим combines a time of day with a future action to structure his day. He uses the words **зранку** (in the morning) and **вдень** (in the afternoon) to divide his Saturday into clear segments. Дарина shifts the conversation from personal routines to a shared invitation. Then, Оксана quickly confirms the specific time using the question phrase **о котрій?** (at what time?). This flow moves logically from individual tasks to a shared group activity, representing exactly how friends communicate.

Here is how someone might describe their simple plans for a single day:

Сьогодні я буду відпочивати. Вдень я буду гуляти в парку. Ввечері я буду читати книгу.
> *(Today I will rest. In the afternoon I will walk in the park. In the evening I will read a book.)*

:::caution
When discussing plans, avoid translating directly from English phrases like "I have plans." Instead, use the structure **У мене є плани** (I have plans), which relies on the possession pattern you already know.
:::

Now, read a different conversation about organizing a busy **тиждень** (week) filled with work, studies, and social events. Scheduling involves mapping out commitments day by day.

> **Антон:** У тебе є плани на тиждень? *(Do you have plans for the week?)*
> **Віктор:** Так, багато! *(Yes, many!)*
> **Віктор:** У понеділок я буду працювати допізна. *(On Monday, I will work until late.)*
> **Віктор:** У вівторок буду вчитися. У середу — зустріч з друзями. *(On Tuesday, I will study. On Wednesday — a meeting with friends.)*
> **Антон:** А у четвер? *(And on Thursday?)*
> **Віктор:** У четвер я буду готувати на вечірку. *(On Thursday, I will prepare for a party.)*
> **Антон:** А в п'ятницю? *(And on Friday?)*
> **Віктор:** В п'ятницю — вечірка! Ти будеш? *(On Friday — a party! Will you be there?)*
> **Антон:** Звичайно буду! *(Of course I will!)*

This second dialogue shifts focus from a single day to the entire week. The speakers map out their obligations chronologically, from Monday to Friday. They use the days of the week alongside the future tense to create a clear timeline of events like a **зустріч** (meeting) or a **вечірка** (party). Notice the question **Ти будеш?** (Will you be there?) — this is a highly natural, conversational way to confirm attendance at an event. You do not always need a full verb like "attend"; the verb "to be" in the future tense is perfectly sufficient for asking if someone plans to show up.

## Планування (Planning)

Scheduling requires combining the day of the week with the correct preposition. To say "on a certain day," use the temporal pattern **У/В** + Accusative case form of the day.

- **у понеділок** (on Monday)
- **у вівторок** (on Tuesday)
- **у середу** (on Wednesday)
- **у четвер** (on Thursday)
- **у п'ятницю** (on Friday)
- **у суботу** (on Saturday)
- **в неділю** (on Sunday)

:::note
Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, **субота**, and **неділя** change their final **-а** or **-я** to **-у** or **-ю**. Masculine days like **понеділок** remain unchanged.
:::

To specify the exact time of an event, use the preposition **о** (or **об** before a vowel) followed by the ordinal number in the Locative case. You can combine the hour with the parts of the day to be precise.

- **о третій** (at three)
- **о шостій** (at six)
- **о дев'ятій** (at nine)
- **об одинадцятій** (at eleven)

You can easily pair the day, the time, and the part of the day.

- У понеділок вранці я працюю. *(On Monday morning I work.)*
- У суботу ввечері ми читаємо. *(On Saturday evening we read.)*
- В неділю вдень вона гуляє. *(On Sunday afternoon she walks.)*

To express what you plan to do at these times, use the compound future tense. This structure is very straightforward: use the future form of the verb "to be" (**бути**), which must match the subject (like **я буду**, **ти будеш**, **ми будемо**), and add an imperfective infinitive verb. The imperfective aspect emphasizes the process or the duration of the action, which is perfect for laying out a continuous schedule. The full structural formula is **У [day] о [time] я буду [verb]**.

- У суботу о третій я буду готувати. *(On Saturday at three I will cook.)*
- У вівторок ввечері ти будеш читати. *(On Tuesday evening you will read.)*
- В неділю зранку ми будемо спати. *(On Sunday morning we will sleep.)*

When you want to include others in your plans, you need functional chunks for making and responding to invitations.

- **Ходімо в кафе!** *(Let's go to a cafe!)*
- **Може, підемо в кіно?** *(Maybe we will go to the cinema?)*
- **Ти будеш вільний у суботу?** *(Will you be free on Saturday? - masculine)*
- **Ти будеш вільна у суботу?** *(Will you be free on Saturday? - feminine)*
- **Давай зустрінемося о п'ятій!** *(Let's meet at five!)*

Responding naturally keeps the conversation moving.

- **Добре!** *(Good!)*
- **Чудово!** *(Great!)*
- **З задоволенням!** *(With pleasure!)*
- **На жаль, не можу.** *(Unfortunately, I cannot.)*

Here is how these scheduling elements look in a continuous thought:

У п'ятницю я працюю допізна. У суботу ввечері ми будемо дивитися кіно. Давай зустрінемося о шостій біля кафе!
> *(On Friday I work until late. On Saturday evening we will watch a movie. Let's meet at six near the cafe!)*

<!-- INJECT_ACTIVITY: fill-in-schedule-time -->

<!-- INJECT_ACTIVITY: match-invitations -->

## Мій тиждень (My Week)

When you connect your daily routines into a larger timeline, you form a cohesive narrative about your life. Look at this model monologue detailing Taras's entire week. Notice how he strings sentences together chronologically.

У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати в кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати. Я піду в кіно. У суботу зранку я буду прибирати. Вдень я буду гуляти в парку. В неділю я буду спати довго!
> *(On Monday I will work. After work I will study Ukrainian. On Tuesday I will have lunch in a cafe. On Wednesday evening I will watch football. On Thursday I will prepare dinner for the family. On Friday I will rest. I will go to the cinema. On Saturday morning I will clean. In the afternoon I will walk in the park. On Sunday I will sleep long!)*

Taras uses the same foundational structure for every single day, creating a steady rhythm. The action moves smoothly from the start of the week toward the weekend. By keeping his sentences short and focused, he communicates his entire weekly availability without using complicated grammar.

Now, you can create your own weekly plan. Use the core template **У [day] я буду [activity]**. This template is your safest tool for building confidence. To make your sentences more descriptive, expand the basic template by adding specific details. Answer the question **о котрій?** (at what time?) to set a schedule. Answer **де?** (where?) to provide a location. Answer **з ким?** (with whom?) to include the people in your life.

For example, instead of just saying "I will walk," you can build a detailed sentence that paints a much clearer picture of your afternoon:

- У суботу я буду гуляти в парку з другом. *(On Saturday I will walk in the park with a friend.)*
- У середу ввечері ми будемо читати вдома. *(On Wednesday evening we will read at home.)*
- В неділю вдень вона буде обідати в кафе. *(On Sunday afternoon she will have lunch in a cafe.)*

Take a moment to map out your own upcoming days. Use the vocabulary you already know for places like your apartment, a restaurant, or the cinema. Include your daily activities like studying, working, cleaning, and resting.

<!-- INJECT_ACTIVITY: fill-in-weekly-plan -->

## Summary

The ability to structure your time and share your schedule is a major milestone in communication. The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive. This scheduling focus aligns with **State Standard 2024, §4.2.4.1**. This pattern is the primary way you will express future plans in the early stages of your learning journey.

У суботу о третій я буду готувати обід. Ввечері я буду відпочивати. У неділю я буду читати.
> *(On Saturday at three I will prepare lunch. In the evening I will rest. On Sunday I will read.)*

When you want to turn your personal schedule into a social event, you rely on a few key invitation chunks. You can propose an outing with **Ходімо!** (Let's go!), suggest an idea with **Може, підемо?** (Maybe we will go?), or specify a time with **Давай зустрінемося!** (Let's meet!). You can then respond enthusiastically with **Добре!** (Good!) or **З задоволенням!** (With pleasure!), or politely decline using **На жаль, не можу** (Unfortunately, I cannot).

To successfully navigate a calendar, you must retain the days of the week. Review the sequence to ensure they come to mind effortlessly: **понеділок**, **вівторок**, **середа**, **четвер**, **п'ятниця**, **субота**, **неділя**.

:::tip
Mental practice is one of the most effective ways to solidify new vocabulary. While riding the bus or waiting in line, try to list the days of the week silently to yourself.
:::

Now it is time for a self-check task. Mentally plan your ideal weekend using these new structures. Ask yourself: **Що ти будеш робити у суботу?** (What will you do on Saturday?). Think about Sunday: **А в неділю?** (And on Sunday?). Finally, consider the people you want to see: **З ким ти будеш зустрічатися?** (Who will you be meeting?). Formulate your answers in complete Ukrainian sentences to prove you can manage your own schedule.
</generated_module_content>

**PIPELINE NOTE — Word count: 1665 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 97 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Антон — NOT IN VESUM
  ✗ Віктор — NOT IN VESUM
  ✗ Дарина — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM

All 97 other words are confirmed to exist in VESUM.

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
