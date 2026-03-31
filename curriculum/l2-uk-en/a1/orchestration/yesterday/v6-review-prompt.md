<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 49: Yesterday (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini Pro
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

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Тарас:</span> Привіт, Оксано! Як пройшов твій день? *(Hi, Oksana! How was your day?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Добре! Зранку я прокинулася о сьомій. *(Good! In the morning I woke up at seven.)*</div>

<div class="dialogue-line"><span class="speaker">Тарас:</span> Що ти робила зранку? *(What did you do in the morning?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Я поснідала і пішла на роботу. *(I had breakfast and went to work.)*</div>

<div class="dialogue-line"><span class="speaker">Тарас:</span> А вдень? *(And in the afternoon?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Вдень я працювала і обідала з колегою. *(In the afternoon I worked and had lunch with a colleague.)*</div>

<div class="dialogue-line"><span class="speaker">Тарас:</span> А ввечері? *(And in the evening?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Ввечері я дивилася серіал і лягла спати о десятій. *(In the evening I watched a TV series and went to bed at ten.)*</div>

</div>

Тарас walks Оксана through her entire day using three simple questions — **зранку** (in the morning), **вдень** (in the afternoon), **ввечері** (in the evening). These three time markers are the spine of every past-day story in Ukrainian. Notice that Оксана uses **-ла** endings throughout: **прокинулася**, **поснідала**, **пішла**, **працювала**, **обідала**, **дивилася**, **лягла**. She is female, so every verb matches.

Now a second conversation — this time with a male speaker.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Марія:</span> Що ти робив у суботу? *(What did you do on Saturday?)*</div>

<div class="dialogue-line"><span class="speaker">Іван:</span> О, я мав чудовий день! *(Oh, I had a wonderful day!)*</div>

<div class="dialogue-line"><span class="speaker">Марія:</span> Розкажи! *(Tell me!)*</div>

<div class="dialogue-line"><span class="speaker">Іван:</span> Зранку я ходив на ринок і купив фрукти. *(In the morning I went to the market and bought fruit.)*</div>

<div class="dialogue-line"><span class="speaker">Марія:</span> А потім? *(And then?)*</div>

<div class="dialogue-line"><span class="speaker">Іван:</span> Потім я готував обід. А вдень гуляв у парку. *(Then I cooked lunch. And in the afternoon I walked in the park.)*</div>

<div class="dialogue-line"><span class="speaker">Марія:</span> А ввечері? *(And in the evening?)*</div>

<div class="dialogue-line"><span class="speaker">Іван:</span> Ввечері ми з другом ходили в ресторан. *(In the evening my friend and I went to a restaurant.)*</div>

<div class="dialogue-line"><span class="speaker">Марія:</span> Як файно! *(How nice!)*</div>

</div>

Compare the two stories. Оксана says **прокинулася**, **пішла**, **дивилася** — all with **-ла** or **-лася**. Іван says **ходив**, **купив**, **готував**, **гуляв** — all with **-в**. The gender rule is simple: pick your form at the start and keep it for the whole story. If you are male, every past verb ends in **-в** or **-вся**. If you are female, every past verb ends in **-ла** or **-лася**. Never switch mid-story.

## Розповідь про день (Narrating a Day)

Every good story about your day has a frame. In Ukrainian, four adverbs create that frame — four time slots that carry you from morning to night:

- **Зранку** (in the morning) — Зранку я поснідав.
- **Вдень** (in the afternoon) — Вдень я обідав.
- **Ввечері** (in the evening) — Ввечері я дивився фільм.
- **Вночі** (at night) — Вночі я спав.

These words never change form. They work the same way whether you are male, female, talking about yourself or someone else. They are adverbs — **незмінні** — and they simply answer the question **коли?** (when?).

But time slots alone give you snapshots, not a story. To connect events into a flowing narrative, you need sequencing words:

- **спочатку** (first) — Спочатку я поснідав.
- **потім** (then) — Потім я пішов на роботу.
- **після цього** (after that) — Після цього я обідав.
- **нарешті** (finally) — Нарешті я ліг спати.

Compare these two versions of the same three events:

Without connectors (choppy): **Я поснідав. Я пішов на роботу. Я обідав.**

With connectors (flowing): **Спочатку я поснідав. Потім я пішов на роботу. Після цього я обідав.**

Which version sounds like a story? The second one. The connectors **спочатку → потім → після цього → нарешті** turn a list of facts into a narrative.

Now the verbs themselves. Here are the six daily routine verbs you need, with both gender forms side by side:

| Infinitive | He (male) | She (female) |
|---|---|---|
| **прокинутися** (to wake up) | прокинувся | прокинулася |
| **поснідати** (to have breakfast) | поснідав | поснідала |
| **піти** (to go) | пішов | пішла |
| **обідати** (to have lunch) | обідав | обідала |
| **повернутися** (to return) | повернувся | повернулася |
| **лягти спати** (to go to bed) | ліг спати | лягла спати |

Most pairs follow a clear pattern: **-в / -ла** or **-вся / -лася**. But two pairs look different from the rest. **Пішов / пішла** — the male form has **-шов**, not a simple **-в**. And **ліг / лягла** — the male form has no suffix at all, just **ліг**. These are irregular, so learn them as fixed pairs:

- **Він пішов на роботу.** *(He went to work.)*
- **Вона пішла на роботу.** *(She went to work.)*
- **Він ліг спати о десятій.** *(He went to bed at ten.)*
- **Вона лягла спати о десятій.** *(She went to bed at ten.)*

<!-- INJECT_ACTIVITY: ordering-daily-routine -->

## Мій учорашній день (My Yesterday)

Here is a complete story of one person's day. Read it through — every verb is in the **-ла** form because the speaker, Anna, is female.

:::note
**Учора був звичайний день.** Зранку я прокинулася о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій я лягла спати.

*(Yesterday was an ordinary day. In the morning I woke up at half past six. I had breakfast — I ate porridge and drank coffee. Then I went to work. In the afternoon I had lunch at a café near the office. I ordered a salad and juice. After work I went to the store and bought groceries. In the evening I cooked dinner and watched a TV series. At eleven I went to bed.)*
:::

Count the past-tense verbs Anna uses: **прокинулася**, **поснідала**, **їла**, **пила**, **пішла**, **обідала**, **замовила**, **ходила**, **купила**, **готувала**, **дивилася**, **лягла** — twelve verbs, all with **-ла** or **-лася**. Not a single **-в** form. This is gender consistency in action. Anna chose her gender at the first verb and never switched.

Now it is your turn. Build your own **учорашній день** (yesterday) using this template:

- **Учора...** *(Yesterday...)*
- **Зранку я ___.**
- **Потім ___.**
- **Вдень я ___.**
- **Ввечері ___.**
- **О ___ годині я ліг/лягла спати.**

Plug in verbs from the table above. Add places you already know — **кафе**, **парк**, **магазин**, **робота** (work). Add people — **друг** (friend, male), **колега** (colleague), **подруга** (friend, female). Remember: pick your gender at the start. If you are male, use **прокинувся**, **поснідав**, **пішов**, **ліг**. If you are female, use **прокинулася**, **поснідала**, **пішла**, **лягла**. Keep it consistent to the very last verb.

<!-- INJECT_ACTIVITY: fill-in-time-markers -->

<!-- INJECT_ACTIVITY: fill-in-gender-consistency -->

## Summary

Everything you need to narrate your day fits into four categories:

**1. Time frame** — the skeleton of the story:
**зранку** → **вдень** → **ввечері** → **вночі**

**2. Sequence chain** — the connectors that turn sentences into a story:
**спочатку** → **потім** → **після цього** → **нарешті**

**3. Past-tense forms** — the six essential daily verbs:
**прокинувся / прокинулася**, **поснідав / поснідала**, **пішов / пішла**, **обідав / обідала**, **повернувся / повернулася**, **ліг спати / лягла спати**. The irregular pairs — **пішов/пішла** and **ліг/лягла** — look different from the regular **-в / -ла** pattern. Know them cold.

**4. Gender rule** — choose male or female at sentence one and never switch mid-story.

After 49 modules, you can introduce yourself, ask for things, talk about your family, describe your home, order food, and tell the time. Now you can tell the full story of your day. **Учора я прокинувся, поснідав і пішов** — three verbs, one sentence, a whole morning. That is what narrative sounds like in Ukrainian. In модуль 50, you will learn the future tense — and the same skeleton (**зранку / вдень / ввечері**) will work for **завтра** (tomorrow) too.

The same past-narration toolkit works in any situation — not just daily routines. Here is a short scene at a police station:

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Поліцейський:</span> Де ви припаркували велосипед? *(Where did you park the bicycle?)*</div>

<div class="dialogue-line"><span class="speaker">Свідок:</span> Я припаркував велосипед біля магазину. *(I parked the bicycle near the store.)*</div>

<div class="dialogue-line"><span class="speaker">Свідок:</span> Потім я зайшов у кав'ярню. *(Then I went into a café.)*</div>

<div class="dialogue-line"><span class="speaker">Свідок:</span> Я вийшов — велосипед зник. *(I came out — the bicycle was gone.)*</div>

<div class="dialogue-line"><span class="speaker">Поліцейський:</span> Ви бачили когось? *(Did you see anyone?)*</div>

<div class="dialogue-line"><span class="speaker">Свідок:</span> Я бачив чоловіка в куртці та кепці. *(I saw a man in a jacket and cap.)*</div>

</div>

Five past-tense verbs — **припаркував**, **зайшов**, **вийшов**, **зник**, **бачив** — in a real-world situation. Same toolkit, different context. Past narration works everywhere.

**Deterministic word count: 1333 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 126 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Поліцейський — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ лася — NOT IN VESUM

All 126 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
