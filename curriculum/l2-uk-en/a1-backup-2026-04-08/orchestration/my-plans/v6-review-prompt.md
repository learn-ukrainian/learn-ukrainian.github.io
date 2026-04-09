<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 51: My Plans (A1, A1.8 [Past, Future, Graduation])
**Writer:** Claude
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
Olya, Taras, and Mariia are planning their weekend in a group chat. The weekend is a time to rest, but it often involves running errands. Pay attention to how they talk about their plans using the word **бу́ду** (I will).
> — **Оля:** Що ти бу́деш роби́ти у субо́ту? *(What will you do on Saturday?)*
> — **Тара́с:** Зра́нку я буду прибира́ти кварти́ру. *(In the morning I will clean the apartment.)*
> — **Оля:** А вдень? *(And in the afternoon?)*
> — **Тарас:** Вдень я буду ходи́ти в магази́н. А ти? *(In the afternoon I will go to the store. And you?)*
> — **Марі́я:** Я буду відпочива́ти! Мо́же, пі́демо в кафе́ вве́чері? *(I will rest! Maybe we will go to a cafe in the evening?)*
> — **Оля:** До́бре! О котрі́й? *(Good! At what time?)*
> — **Марія:** О шо́стій. Добре? *(At six. Good?)*
> — **Тарас:** Чудо́во! До зу́стрічі у суботу! *(Great! See you on Saturday!)*

In this dialogue, the friends are using the future tense combined with specific times. You can see the pattern: **я буду прибирати** (I will clean) and **я буду відпочивати** (I will rest). Notice how they specify the time of day: **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening). The word **кварти́ра** means "apartment", and **кафе** is "cafe". 
When using the analytic future tense with the auxiliary verb **буду**, you only conjugate the auxiliary verb to match the speaker (I, you, he, we). The main action verb always stays in its dictionary form, the infinitive. For example, in the phrase **я буду прибирати** (I will clean), the main verb **прибирати** (to clean) remains unchanged.
Now, let's look at another situation. Anna is telling her friend about her very busy week. She uses the days of the week to map out her schedule.
> — **Дмитро́:** У тебе́ є пла́ни на ти́ждень? *(Do you have plans for the week?)*
> — **А́нна:** Так, бага́то! У понеді́лок я буду працюва́ти допі́зна. *(Yes, many! On Monday I will work until late.)*
> — **Анна:** У вівто́рок буду вчи́тися. У се́реду — зу́стріч з дру́зями. *(On Tuesday I will study. On Wednesday — a meeting with friends.)*
> — **Дмитро:** А у четве́р? *(And on Thursday?)*
> — **Анна:** У четвер я буду готува́ти на вечі́рку. *(On Thursday I will cook for a party.)*
> — **Дмитро:** А в п'я́тницю? *(And on Friday?)*
> — **Анна:** В п'ятницю — вечі́рка! Ти будеш? *(On Friday — a party! Will you be there?)*
> — **Дмитро:** Звича́йно буду! *(Of course I will be!)*

Here, Anna maps out her complete schedule while Dmytro asks follow-up questions. The key pattern is the auxiliary verb **буду** (I will) followed by an infinitive verb. They also use the days of the week as fixed time anchors, such as **у понеділок** (on Monday) and **у вівторок** (on Tuesday). Think about what Anna is doing on Thursday. She is preparing for a **вечірка** (party). Anna also mentions she will work **допізна** (until late), and Dmytro responds enthusiastically with **звичайно** (of course). They also schedule a **зустріч** (meeting).
## Планува́ння (Planning)
When you want to schedule an event or talk about a **план** (plan), you need a reliable formula. In Ukrainian, planning involves combining the day, the time, the auxiliary verb, and the main action. The core pattern looks like this: **У** (On) + day + time + **буду** (I will) + infinitive verb.
To use this formula, you first need to know the days of the week. Notice how we use the preposition **у** (in/on) or **в** (in/on) before the day to say "on [Day]".
*   **у понеділок** (on Monday)
*   **у вівторок** (on Tuesday)
*   **у середу** (on Wednesday)
*   **у четвер** (on Thursday)
*   **у п'ятницю** (on Friday)
*   **у суботу** (on Saturday)
*   **в неді́лю** (on Sunday)
You can make your plan more specific by adding a time-of-day adverb. We use **зранку** (in the morning), **вдень** (in the afternoon), and **ввечері** (in the evening). These adverbs do not require any extra prepositions — you simply place them next to your verb. You can also add clock time using **о** (at): **о дев'я́тій** (at nine), **о тре́тій** (at three), **о шостій** (at six).
Let's combine these elements into full sentences:
*   **У суботу ввечері я буду диви́тися фільм.** (On Saturday evening I will watch a movie.)
*   **У середу зранку я буду працювати.** (On Wednesday morning I will work.)
*   **У п'ятницю о шостій я буду відпочивати.** (On Friday at six I will rest.)
When you want to invite someone to join your plan, you have a handy toolkit of phrases. These phrases vary in their tone.
*   **Ході́мо в кафе!** (Let's go to a cafe!) — This uses the warm imperative form to create a friendly, active invitation. It implies that you are already ready to go.
*   **Може, підемо в кіно́?** (Maybe we'll go to the cinema?) — This is a soft suggestion using the word **може** (maybe), making it sound more like an open proposal.
*   **Дава́й зустрі́немося о п'я́тій!** (Let's meet at five!) — This is a collaborative invitation using the chunk **зустрінемося** (let's meet).
Before making an invitation, you might want to check if the person has a **ві́льний** (free) schedule. You can ask: **Ти будеш вільний у суботу?** (Will you be free on Saturday? — speaking to a male) or **Ти будеш ві́льна у суботу?** (Will you be free on Saturday? — speaking to a female).
When someone invites you, you need to know how to respond. You can accept enthusiastically or decline politely.
*   **Добре!** (Good!)
*   **Чудово!** (Great!)
*   **З задово́ленням!** (With pleasure!) — The word **задово́лення** means satisfaction or pleasure. This shows genuine enthusiasm.
*   **На жаль, не мо́жу.** (Unfortunately, I cannot.) — This combines **на жаль** (unfortunately) with a polite refusal.
<!-- INJECT_ACTIVITY: quiz-days-of-week -->
<!-- INJECT_ACTIVITY: fill-in-invitations -->
You might have noticed that Ukrainian uses both **у** and **в** before the days of the week. For example: **у суботу** but **в неділю**. Which one you choose depends on the sounds around the preposition — specifically, the sound at the end of the previous word and the sound at the start of the next word. The basic pattern: use **у** between consonant sounds (він **у** до́мі), and **в** after a vowel sound before a consonant (вона́ **в** домі). At the start of a sentence, use **у** before a consonant: **У** понеділок я буду працювати. This is the same euphony rule (милозву́чність) you saw in earlier modules — Ukrainian avoids awkward clusters of similar sounds. Here are some examples of how this works:
*   **Він** бу́де працювати **у** понеділок. (consonant + у + consonant)
*   Я буду працювати **в** понеділок. (vowel + в + consonant)
*   **У** суботу я буду відпочивати. (sentence start + у + consonant)

At A1, the key takeaway is: both **у** and **в** are correct — the choice depends on the surrounding sounds, and you will develop a feel for it naturally.
## Мій тиждень (My Week)
Let's introduce Taras. He is a very organized person and likes to plan his entire **тиждень** (week) in advance. He breaks down his schedule one day at a time, making sure he balances work, studies, and time to **відпочивати** (to rest). 
Here is Taras's model week:
*   **У понеділок я буду працювати.** (On Monday I will work.)
*   **Пі́сля робо́ти буду вчи́ти украї́нську.** (After work I will study Ukrainian.)
*   **У вівторок я буду обі́дати з дру́гом у кафе.** (On Tuesday I will have lunch with a friend in a cafe.)
*   **У середу ввечері я буду дивитися футбо́л.** (On Wednesday evening I will watch football.)
*   **У четвер я буду готувати вече́рю для роди́ни.** (On Thursday I will cook dinner for the family.)
*   **У п'ятницю я буду відпочивати — піду́ в кіно.** (On Friday I will rest — I will go to the cinema.)
*   **У суботу зранку буду прибирати, а вдень гуля́ти в парку.** (On Saturday morning I will clean, and in the afternoon walk in the park.)
*   **У неділю я буду спа́ти до́вго!** (On Sunday I will sleep long!)
Notice how every single day uses the structure **буду** + infinitive. This is the most natural way to describe an ongoing or planned activity in the future. The phrase **я буду прибирати** means that the action of cleaning will be a process taking up his time. The verb **вчити** (to study/learn) is perfect for describing a continuous educational goal. When he says **я буду відпочивати**, he implies a continuous period of rest. 
Now it is your turn to create your own schedule. You can use this simple template:
**У** [day] **о** [time] **я буду** [infinitive verb].
To make your sentences richer, you can answer three expansion questions:
1.  **Де?** (Where?) — **у парку** (in the park), **в кафе** (in the cafe), **вдо́ма** (at home).
2.  **З ким?** (With whom?) — **з другом** (with a friend), **з сім'є́ю** (with family), **сам** / **сама** (alone).
3.  **Що са́ме?** (What exactly?) — **прибирати квартиру** (to clean the apartment), **готувати обід** (to cook lunch), **дивитися фільм** (to watch a movie).
Let's look at a worked example that uses all these pieces:
**У суботу о деся́тій я буду гуляти в парку з другом.** (On Saturday at ten I will walk in the park with a friend.)
<!-- INJECT_ACTIVITY: fill-in-schedule-formula -->
Now, try a mini-writing task. Plan your ideal weekend in four to six sentences using the model you just learned. Make sure your plan includes two days: **субо́та** (Saturday) and **неді́ля** (Sunday). Include the time of day (**зранку**, **вдень**, **ввечері**) or a specific clock time (**о котрій?**). Mention the place, and use the **буду** + infinitive structure.
Here is a sample answer to guide you:
**У суботу зранку я буду спати довго. Вдень я буду гуляти в парку. Ввечері ми бу́демо дивитися фільм. В неділю я буду готувати сніда́нок для родини.** (On Saturday morning I will sleep long. In the afternoon I will walk in the park. In the evening we will watch a movie. On Sunday I will cook breakfast for the family.)
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
*   **середа́** (Wednesday)
*   **четвер** (Thursday)
*   **п'я́тниця** (Friday)
*   **субота** (Saturday)
*   **неділя** (Sunday)
Remember the euphony rule when attaching prepositions: we say **у суботу** but **в неділю** depending on the preceding sounds. The Ukrainian language naturally avoids awkward clusters of consonants or vowels. This makes your sentences flow beautifully.

**Deterministic word count: 1902 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 98 words | Not found: 57 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Дмитро — NOT IN VESUM
  ✗ Звича — NOT IN VESUM
  ✗ Зра — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Планува — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ бага — NOT IN VESUM
  ✗ вве — NOT IN VESUM
  ✗ вго — NOT IN VESUM
  ✗ вдо — NOT IN VESUM
  ✗ вече — NOT IN VESUM
  ✗ вечі — NOT IN VESUM
  ✗ вівто — NOT IN VESUM
  ✗ гом — NOT IN VESUM
  ✗ готува — NOT IN VESUM
  ✗ гуля — NOT IN VESUM
  ✗ дев'я — NOT IN VESUM
  ✗ деся — NOT IN VESUM
  ✗ деш — NOT IN VESUM
  ✗ допі — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ ждень — NOT IN VESUM
  ✗ задово — NOT IN VESUM
  ✗ зустрі — NOT IN VESUM
  ✗ зями — NOT IN VESUM
  ✗ лення — NOT IN VESUM
  ✗ ленням — NOT IN VESUM
  ✗ лок — NOT IN VESUM
  ✗ льна — NOT IN VESUM
  ✗ льний — NOT IN VESUM
  ✗ магази — NOT IN VESUM
  ✗ милозву — NOT IN VESUM
  ✗ неді — NOT IN VESUM
  ✗ немося — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нна — NOT IN VESUM
  ✗ ння — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ нську — NOT IN VESUM
  ✗ п'я — NOT IN VESUM
  ✗ пла — NOT IN VESUM
  ✗ понеді — NOT IN VESUM
  ✗ працюва — NOT IN VESUM
  ✗ реду — NOT IN VESUM
  ✗ рка — NOT IN VESUM
  ✗ рку — NOT IN VESUM
  ✗ сля — NOT IN VESUM
  ✗ субо — NOT IN VESUM

All 98 other words are confirmed to exist in VESUM.

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
