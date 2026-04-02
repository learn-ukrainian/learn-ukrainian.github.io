<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 25: My Day (A1, A1.4 [Time and Nature])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-025
level: A1
sequence: 25
slug: my-day
version: '1.2'
title: My Day
subtitle: Спочатку, потім, нарешті — telling a story about your day
focus: communication
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Describe a full day from morning to evening using verbs and time expressions
- Use sequence words to connect events (спочатку, потім, після того, нарешті)
- Combine time (M22), days (M23), weather (M24), and verbs (A1.3)
- Tell a simple coherent story about a typical or specific day
dialogue_situations:
- setting: Writing a blog post / diary entry about your day — reading it to a friend
  speakers:
  - Автор (narrator)
  - Друг (listener, reacting)
  motivation: 'Sequence words: спочатку, потім, нарешті in narration'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - Dialogue 1 — What did you do today? — Як пройшов твій день? — Добре! Вранці я
    працював. — А потім? — Потім обідав о першій. Після обіду гуляв. — А ввечері?
    — Ввечері дивився фільм і читав книгу. Past tense emerges naturally here — teach
    as vocabulary chunks, not grammar (past tense grammar = M48-49).
  - 'Dialogue 2 — Planning tomorrow: — Що ти будеш робити завтра? — Вранці буду працювати.
    — А після обіду? — Буду вивчати українську. А ввечері — гуляти. Future ''буду
    + infinitive'' as a chunk.'
- section: Мій типовий день (My Typical Day)
  words: 300
  points:
  - 'A model text using all A1.3-A1.4 skills: Я прокидаюся о сьомій. Спочатку вмиваюся
    і одягаюся. Потім снідаю. О дев''ятій я працюю. О першій обідаю. Після обіду працюю
    до п''ятої. Ввечері готую вечерю, читаю і дивлюся фільм. О одинадцятій лягаю спати.'
  - 'Parts of the day: вранці (in the morning), вдень (during the day), після обіду
    (in the afternoon — literally ''after lunch''), ввечері (in the evening), вночі
    (at night). These are adverbs — just add them to the beginning of a sentence.'
- section: Від ранку до вечора (From Morning to Evening)
  words: 300
  points:
  - 'Extended sequence words (building on M20): спочатку (first/at first), потім (then/next),
    після того/після цього (after that), нарешті (finally), також (also), а потім
    (and then). These connect sentences into a coherent narrative.'
  - 'Daily activity verbs (review + new): снідати (to have breakfast — review M20),
    обідати (to have lunch), вечеряти (to have dinner), відпочивати (to rest), лягати
    спати (to go to bed — chunk). All Group I (-ати), easy to conjugate with M16 patterns.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Telling your day: Time + sequence + activity = а coherent story. О сьомій прокидаюся.
    Спочатку снідаю. Потім працюю. Після обіду відпочиваю. Ввечері читаю. Нарешті
    лягаю спати. Self-check: Describe your typical Monday from morning to evening.
    Use at least 3 time expressions and 3 sequence words.'
vocabulary_hints:
  required:
  - вранці (in the morning)
  - вдень (during the day)
  - ввечері (in the evening)
  - обідати (to have lunch)
  - вечеряти (to have dinner)
  - відпочивати (to rest)
  - після (after)
  recommended:
  - прокидатися (to wake up — review from M20)
  - вмиватися (to wash — review from M20)
  - одягатися (to get dressed — review from M20)
  - вночі (at night)
  - після обіду (in the afternoon)
  - також (also)
  - лягати спати (to go to bed — chunk)
  - типовий (typical)
  - вільний (free)
activity_hints:
- type: match-up
  focus: Match the activity to the logical time of day
  pairs:
  - прокидаюся ↔ вранці
  - снідаю ↔ вранці
  - працюю ↔ вдень
  - обідаю ↔ вдень
  - вечеряю ↔ ввечері
  - дивлюся фільм ↔ ввечері
  - лягаю спати ↔ вночі
  - сплю ↔ вночі
- type: fill-in
  focus: Complete the logical sequence of the day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і вмиваюся.'
  - Після того я {снідаю|вечеряю|лягаю спати}.
  - Вдень я {працюю|прокидаюся|снідаю} в офісі.
  - О першій годині я {обідаю|вечеряю|прокидаюся}.
  - '{Потім|Спочатку|Вранці} я читаю книгу або дивлюся фільм.'
  - '{Нарешті|Спочатку|Вдень} я лягаю спати о дванадцятій.'
- type: fill-in
  focus: Choose the correct part of the day
  items:
  - Я п'ю каву {вранці|вночі|ввечері}.
  - Ми вечеряємо {ввечері|вранці|вдень}.
  - Вона працює з дев'ятої до п'ятої {вдень|вночі|вранці}.
  - Вони гуляють у парку {після обіду|вночі|вранці}.
connects_to:
- a1-026 (Free Time)
prerequisites:
- a1-024 (Weather)
grammar:
- 'Sequence words: спочатку, потім, після того, нарешті'
- 'Parts of the day as adverbs: вранці, вдень, ввечері, вночі'
- 'Preview chunks only: працював/працювала, буду + infinitive (grammar in A1.8)'
register: розмовний
references:
- title: Вашуленко Grade 2, p.83
  notes: Planning your day activity — connecting activities to time.

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)

You already know how to tell time, name the days of the week, and describe the weather outside. Now it's time to put it all together — telling someone about your whole day. Below are two conversations: one about yesterday, one about tomorrow. The past-tense and future forms here are frozen phrases — just memorize them as chunks for now. The full grammar comes later.

**(Як пройшо́в твій день? / How was your day?)**

> — **Марко́:** Приві́т! Як пройшов твій день? *(Hi! How was your day?)*
> — **Оле́нка:** До́бре! Вра́нці я працюва́ла в о́фісі. *(Good! In the morning I worked at the office.)*
> — **Марко:** А **по́тім**? *(And then?)*
> — **Оленка:** **Потім** обі́дала о пе́ршій. **Пі́сля обі́ду** гуля́ла у парку. *(Then I had lunch at one. After lunch I walked in the park.)*
> — **Марко:** А вве́чері що роби́ла? *(And in the evening, what did you do?)*
> — **Оленка:** Ввечері диви́лася фільм і чита́ла кни́гу. **Наре́шті** лягла́ спа́ти о двана́дцятій. *(In the evening I watched a film and read a book. Finally I went to bed at twelve.)*
> — **Марко:** О дванадцятій? Пі́зно! *(At twelve? Late!)*

The past forms — **працювала** *(worked)*, **обідала** *(had lunch)*, **гуляла** *(walked)*, **дивилася** *(watched)*, **читала** *(read)*, **лягла** *(went to bed)* — are chunks for now. Full past-tense grammar comes in M48–49.

:::tip
Notice the pattern: **sequence word + verb + time**. For example: **Потім обідала о першій.** The sequence word opens the sentence, the verb follows, and time closes it.
:::

**(Що ти бу́деш роби́ти за́втра? / What will you do tomorrow?)**

> — **Оленка:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
> — **Марко:** Вранці **бу́ду працюва́ти**. *(In the morning I will work.)*
> — **Оленка:** А **після обіду**? *(And in the afternoon?)*
> — **Марко:** **Після обіду** буду вивча́ти украї́нську. *(In the afternoon I will study Ukrainian.)*
> — **Оленка:** А ввечері? *(And in the evening?)*
> — **Марко:** Ввечері **буду** гуля́ти. А вночі́? **Нарешті буду** спати! *(In the evening I'll walk. And at night? Finally I'll sleep!)*

The future pattern **буду** *(I will)* + infinitive works like a chunk: **буду працювати** *(I will work)*, **буду вивчати** *(I will study)*, **буду гуляти** *(I will walk)*. Full future-tense grammar is in M46.

Same structure, two timelines — yesterday Olenka **працювала** *(worked)*, tomorrow Marko **буду працювати** *(will work)*. The sequence words stay the same either way.

## Мій типовий день (My Typical Day)

Below is a complete model day — a narrative using the present tense you already know from A1.3, combined with time expressions from M22 and the parts-of-day adverbs you'll master in this module. Read it through like a short story, then study how it's built.

> **Я прокида́юся о сьо́мій. Споча́тку вмива́юся і одяга́юся. Потім сні́даю о во́сьмій. О дев'я́тій почина́ю працювати. Вдень я працю́ю до пе́ршої. О першій обі́даю. Після обіду ще працюю до п'я́тої. Ввечері готу́ю вече́рю і відпочива́ю. О дев'ятій дивлю́ся фільм або́ чита́ю книгу. Нарешті о дванадцятій ляга́ю спати.**

Every verb here is present tense — forms you already know from M16–M21. The sequence words **спочатку**, **потім**, and **нарешті** connect the actions into a story instead of a random list.

Now let's look at the five parts-of-day adverbs that make this narrative possible:

- **вранці** (in the morning) — roughly before noon. *Вранці я снідаю.*
- **вдень** (during the day) — the working hours, roughly 9 to 17. *Вдень я працюю.*
- **після обіду** (in the afternoon) — literally "after lunch." *Після обіду я відпочиваю.*
- **ввечері** (in the evening) — roughly 18 to 22. *Ввечері я читаю.*
- **вночі** (at night) — roughly 22 to 6. *Вночі я сплю.*

Four of these are single adverbs — unchanging words. No case endings, no conjugation. Just place them at the start of a sentence: **Ввечері я читаю.** Compare this with clock time: **о сьомій** *(at seven)* uses a preposition and an ordinal number, while **вранці** *(in the morning)* is a single adverb — no preposition needed.

<!-- INJECT_ACTIVITY: fill-in-part-of-day -->

One more detail: **після обіду** is two words functioning together as a time marker. You can use it alone — **Після обіду я відпочиваю.** *(In the afternoon I rest.)* — or pair it with a clock time: **Після обіду, о тре́тій, я вчу українську.** *(In the afternoon, at three, I study Ukrainian.)*

## Від ра́нку до ве́чора (From Morning to Evening)

You've seen **потім** and **нарешті** in the dialogues. Here is the full set of sequence words that let you connect one event to the next, turning isolated sentences into a coherent story:

- **спочатку** (first, to start with) — *Спочатку я снідаю.* *(First I have breakfast.)*
- **потім** (then, next) — *Потім я йду на робо́ту.* *(Then I go to work.)*
- **після того́** / **після цього́** (after that) — *Після того я відпочиваю.* *(After that I rest.)*
- **нарешті** (finally) — *Нарешті я лягаю спати.* *(Finally I go to bed.)*
- **та́ко́ж** (also) — *Я також читаю вранці.* *(I also read in the morning.)*
- **а потім** (and then — with a light contrast) — *Я снідаю, а потім іду́ до о́фісу.* *(I have breakfast, and then I go to the office.)*

A quick note: **спочатку** is a sequence marker — it means "first" in a chain of events. Don't confuse it with **на поча́тку** *(at the beginning of something)*. At A1, **після того** and **після цього** are interchangeable — use whichever feels natural.

Now let's expand your daily activity verbs. You already know **сні́дати** *(to have breakfast)* from M20. Here are the other two meal verbs — together they form a natural triad:

- **снідати** (to have breakfast) — review from M20
- **обі́дати** (to have lunch) — new
- **вече́ряти** (to have dinner) — new

All three are Group I verbs, conjugated exactly like **чита́ти**: **я снідаю**, **ти сні́даєш**, **він/вона́ сні́дає**. The pattern is identical for **обідати** *(я обідаю)* and **вечеряти** *(я вече́ряю)*.

Two more useful verbs: **відпочива́ти** *(to rest)* — also Group I: **я відпочиваю**, **ти відпочива́єш**. And the chunk **ляга́ти спати** *(to go to bed)* — treat it as one unit at A1. Full reflexive verb grammar comes in M38.

Combine any verb with a time expression and you have a sentence about your day:

- **О першій я обідаю.** *(At one I have lunch.)*
- **Після робо́ти я відпочиваю.** *(After work I rest.)*
- **Ввечері я вечеряю о сьомій.** *(In the evening I have dinner at seven.)*
- **О дванадцятій я лягаю спати.** *(At twelve I go to bed.)*

<!-- INJECT_ACTIVITY: match-time-of-day -->

Here's how all three tools — sequence words, time adverbs, and activity verbs — stack together in a natural chain: **Вранці я прокидаюся о сьомій. Спочатку снідаю. Потім іду на роботу. Після того обідаю о першій. Ввечері відпочиваю. Нарешті лягаю спати.** Any two sentences about your day can be connected with **потім** or **після того** — just pick one and keep going.

## Підсумок — Summary

Every sentence you've built in this module follows one formula:

**[Sequence word] + [Time expression] + [Verb + object]**

The pieces are interchangeable. Look at how they combine:

- **О сьомій** [time] — **прокидаюся** [verb] → *At seven — I wake up.*
- **Спочатку** [sequence] — **снідаю** [verb] → *First — I have breakfast.*
- **Потім** [sequence] — **о дев'ятій** [time] — **іду на роботу** [verb + complement] → *Then — at nine — I go to work.*

Time expressions and sequence words both sit at the start of the sentence. You can use one or both — **Потім о дев'ятій іду на роботу** works just as well as **О дев'ятій іду на роботу**.

Here is a longer model day that weaves everything from this module together. Read it, then write your own version below:

> **Мій типовий понеді́лок почина́ється о шо́стій. Спочатку я вмиваюся і одягаюся. Потім снідаю — п'ю ка́ву і їм бутербро́д. О дев'ятій починаю працювати. Вдень я ду́же за́йнятий. О першій обідаю в кафе́. Після обіду ще працюю до шо́стої. Ввечері відпочиваю — готую вечерю і дивлюся серіа́л. Також читаю пе́ред сном. Нарешті о дванадцятій лягаю спати. Завтра — те са́ме!**

*(My typical Monday starts at six. First I wash up and get dressed. Then I have breakfast — I drink coffee and eat a sandwich. At nine I start working. During the day I'm very busy. At one I have lunch at a café. After lunch I work until six. In the evening I rest — I cook dinner and watch a series. I also read before bed. Finally at twelve I go to bed. Tomorrow — the same!)*

<!-- INJECT_ACTIVITY: fill-in-sequence -->

Now it's your turn. Describe your own typical day using what you've learned:

- Write about your typical Monday from morning to evening (5–8 sentences).
- Use at least 3 time expressions (e.g., **о восьмій**, **після обіду**, **ввечері**).
- Use at least 3 sequence words (**спочатку**, **потім**, **нарешті**).
- Include at least 4 daily activity verbs (**прокидатися**, **снідати**, **обідати**, **відпочивати**, **лягати спати**).
- Starter: **Мій типовий понеділок починається о ___. Спочатку я ___…**

Try reading your text aloud. Does it flow from one event to the next? If two sentences feel disconnected, add **потім** or **після того** between them — that's all it takes to turn a list into a story.

**Deterministic word count: 1519 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 117 words | Not found: 47 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Вра — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Наре — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Приві — NOT IN VESUM
  ✗ Споча — NOT IN VESUM
  ✗ бутербро — NOT IN VESUM
  ✗ вве — NOT IN VESUM
  ✗ вече — NOT IN VESUM
  ✗ втра — NOT IN VESUM
  ✗ гуля — NOT IN VESUM
  ✗ двана — NOT IN VESUM
  ✗ дев'я — NOT IN VESUM
  ✗ деш — NOT IN VESUM
  ✗ дцятій — NOT IN VESUM
  ✗ зно — NOT IN VESUM
  ✗ йнятий — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ лася — NOT IN VESUM
  ✗ лок — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нську — NOT IN VESUM
  ✗ нці — NOT IN VESUM
  ✗ п'я — NOT IN VESUM
  ✗ понеді — NOT IN VESUM
  ✗ поча — NOT IN VESUM
  ✗ працюва — NOT IN VESUM
  ✗ пройшо — NOT IN VESUM
  ✗ ред — NOT IN VESUM
  ✗ ршої — NOT IN VESUM
  ✗ ршій — NOT IN VESUM
  ✗ ряти — NOT IN VESUM
  ✗ ряю — NOT IN VESUM
  ✗ серіа — NOT IN VESUM
  ✗ сля — NOT IN VESUM
  ✗ стої — NOT IN VESUM
  ✗ сьмій — NOT IN VESUM
  ✗ сьо — NOT IN VESUM
  ✗ тку — NOT IN VESUM
  ✗ украї — NOT IN VESUM
  ✗ фісу — NOT IN VESUM
  ✗ фісі — NOT IN VESUM
  ✗ чора — NOT IN VESUM
  ✗ шті — NOT IN VESUM
  ✗ юся — NOT IN VESUM
  ✗ ється — NOT IN VESUM

All 117 other words are confirmed to exist in VESUM.

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
