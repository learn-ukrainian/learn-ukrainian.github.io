<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок — Summary'
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [GLOBAL] NO LLM filler phrases. Do NOT write: "Let us start with...", "Numbers unlock the real Ukraine", "You now possess a complete...", "It is incredibly versatile", "one of the most rewarding skills". Start sections with a dialogue, a question, or a concrete example — never with a generic motivational opener. If a sentence could appear in any language course about any topic, delete it.
- [GLOBAL] Every exercise item must test something EXPLICITLY taught in the preceding prose. If an exercise tests the collocation "малювати картину", the prose must contain "малювати картину" as a taught example. Do NOT test collocations, vocabulary, or patterns that the learner has to infer — test what was taught.
- [GLOBAL] Quiz correct answers must be RANDOMIZED across positions. Do NOT place the correct answer at index 0 for all items. Distribute correct answers roughly evenly across all positions (0, 1, 2) to prevent pattern-guessing.
- [GLOBAL] Do NOT use spatial metaphors for abstract grammatical requirements. Example: "на" with musical instruments is NOT "on top of" — it is an abstract grammatical requirement that must be memorized. Misleading mnemonics cause incorrect generalizations. If a rule must simply be memorized, say so directly.
- [GLOBAL] Memorized chunks are allowed before their grammar is formally taught. Natural Ukrainian expressions (Мені подобається, У мене є, Мене звати, Як справи?, Звідки ти?, Скільки коштує?, Мені ... років) can appear in ANY module as memorized chunks, even if the underlying grammar (dative, genitive, etc.) is not taught until later. This mirrors how Ukrainian children and L2 learners naturally acquire language. Do NOT flag these as forward-references. DO flag premature drilling of case paradigms, untaught vocabulary words, and grammar analysis before its module.
- [GLOBAL] Inline activity markers (<!-- INJECT_ACTIVITY: ... -->) must ONLY appear AFTER all concepts they test have been taught. If an activity tests both soft signs and apostrophes, it must appear after BOTH sections, not after the first one. This is critical in Ukrainian where apostrophe rules (б,п,в,м,ф,р + я,ю,є,ї) appear constantly — placing an apostrophe exercise before the apostrophe section teaches wrong sequencing. Rule: scan each activity's items and verify every tested concept has a preceding H2 section that teaches it.



---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **41: Checkpoint: Food and Shopping** (A1, A1.6 [Food and Shopping]).

**Target: 1000–1500 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1000–1500 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a1-041
level: A1
sequence: 41
slug: checkpoint-food-shopping
version: '1.2'
title: 'Checkpoint: Food and Shopping'
subtitle: Can you order food and buy things in Ukrainian?
focus: review
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1000
objectives:
- Demonstrate food and drink vocabulary in context
- Use accusative case correctly for both inanimate and animate nouns
- Order at a cafe and buy things at a shop/market
- Combine all A1.6 skills in connected scenarios
dialogue_situations:
- setting: 'Hosting a вечеря (f, dinner party) — full flow: shopping for продукти
    (pl) at the ринок (m, market), cooking вареники (pl) and салат (m), setting the
    table with тарілки (pl, plates) and склянки (pl, glasses), serving guests.'
  speakers:
  - Господиня (host)
  - Гості (guests)
  motivation: 'Consolidation: продукти(pl), вареники(pl), тарілка(f), склянка(f)'
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M36-M40: Can you name 10 foods and 5 drinks? (M36) Can you
    say what you eat/drink using accusative? (M37) Can you order at a cafe? (M38)
    Can you ask prices and buy things? (M39) Can you use accusative for people? (M40)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M36-M40. Content: Anna goes to the
    market, buys food, then goes to a cafe. She orders борщ and каву з молоком, asks
    for the bill, then meets a friend and introduces her brother. Uses food vocabulary,
    accusative inanimate and animate, cafe phrases.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.6: 1. Food/drink vocabulary: їжа, напої, meals (M36) 2.
    Accusative inanimate: masc = nom, fem -а→-у (M37) 3. Ordering: Мені каву, будь
    ласка (M38) 4. Prices: Скільки коштує? Гривня/гривні/гривень (M39) 5. Accusative
    animate: fem -а→-у, masc = genitive (M40) 6. Chunks: кава з молоком, кілограм
    яблук (M36, M39)'
- section: Діалог (Connected Dialogue)
  words: 200
  points:
  - 'A day of food and shopping: — Що ти їш на сніданок? — Я їм кашу і п''ю каву з
    молоком. — Потім іду на ринок. Скільки коштують помідори? — Тридцять гривень.
    — Дайте кілограм, будь ласка. — Потім у кафе: Мені борщ і воду, будь ласка. —
    О, я бачу Олену! Олено, привіт! Ти знаєш мого брата? Combines all A1.6 skills
    in one realistic day.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'A1.6 achievement summary: You can talk about food and drinks. You can use accusative
    for things AND people. You can order at a cafe and pay. You can shop at a market
    and ask prices. Next: A1.7 — Communication (phone, email, making plans).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Accusative check: choose correct form for inanimate AND animate nouns'
  items:
  - question: Я їм ___.
    options:
    - салат
    - салата
    - салату
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - брату
  - question: Я п'ю ___.
    options:
    - воду
    - вода
    - води
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я люблю ___.
    options:
    - борщ
    - борща
    - борщу
  - question: Я чекаю ___.
    options:
    - друга
    - друг
    - другу
  - question: Я купую ___.
    options:
    - хліб
    - хліба
    - хлібу
  - question: Я бачу ___.
    options:
    - лікаря
    - лікар
    - лікарю
  - question: Я їм ___.
    options:
    - піцу
    - піца
    - піци
  - question: Я люблю ___.
    options:
    - маму
    - мама
    - мами
- type: fill-in
  focus: Complete the cafe + market dialogue with correct forms
  items:
  - — Що ти їш на сніданок? — Я їм {кашу|каша|каші} і п'ю каву.
  - — Потім іду на ринок. Скільки {коштують|коштує|коштувати} помідори?
  - — Тридцять {гривень|гривні|гривня}.
  - — Дайте {кілограм|літр|пляшку} яблук, будь ласка.
  - '— Потім у кафе: {Мені|Я|Меня} борщ і воду, будь ласка.'
  - — Рахунок, будь ласка. Можна {карткою|картка|картки}?
  - — О, я бачу {Олену|Олена|Олени}! Олено, привіт!
  - — Ти знаєш мого {брата|брат|братом}?
- type: group-sort
  focus: 'Sort accusative forms: inanimate (що?) vs animate (кого?)'
  groups:
  - name: Inanimate (що?)
    items:
    - борщ
    - хліб
    - сік
    - чай
    - сир
  - name: Animate (кого?)
    items:
    - брата
    - лікаря
    - сусіда
    - друга
    - вчителя
- type: quiz
  focus: What do you say? Match shopping/cafe situations to correct phrases
  items:
  - question: 'You want to order coffee:'
    options:
    - Мені каву, будь ласка.
    - Скільки коштує?
    - Тут вільно?
  - question: 'You ask for the price:'
    options:
    - Скільки коштує?
    - Можна карткою?
    - Що ви рекомендуєте?
  - question: 'You want to pay with a card:'
    options:
    - Можна карткою?
    - Рахунок, будь ласка.
    - Дорого!
  - question: 'You ask for the bill:'
    options:
    - Рахунок, будь ласка.
    - Мені борщ.
    - Все було дуже смачно!
  - question: 'You ask for 1 kg of apples:'
    options:
    - Дайте кілограм яблук.
    - Скільки коштує?
    - Можна меню?
  - question: 'You think the price is high:'
    options:
    - Дорого!
    - Дешево!
    - Нормальна ціна.
  - question: 'You ask if a seat is free:'
    options:
    - Тут вільно?
    - Можна меню?
    - Рахунок, будь ласка.
  - question: 'You compliment the food:'
    options:
    - Все було дуже смачно!
    - Можна карткою?
    - Це гостре?
connects_to:
- a1-042 (next module in A1.7)
prerequisites:
- a1-040 (People Around Me)
grammar:
- 'Review: accusative inanimate (M37) and animate (M40)'
- 'Review: ordering patterns (M38) and price patterns (M39)'
- 'Review: з + noun chunks (M36, M39)'
register: розмовний
references:
- title: Synthesis of M36-M40 content
  notes: No new material — review and integration of A1.6 phase.

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification

### Batch 1 — Core nouns (15/15 ✅)
- Confirmed: **їжа** (noun), **напої** ← напій (noun), **борщ** (noun), **кава** (noun), **молоко** (noun), **каша** (noun), **вода** (noun), **помідори** ← помідор (noun), **яблука** ← яблуко (noun), **гривня** (noun), **гривні** (grivnya soft-decl + гривна hard-decl — see Calque Warning §4), **гривень** ← гривня (noun), **сніданок** (noun), **ринок** (noun), **кафе** (noun, indeclinable)
- Not found: none

### Batch 2 — Verb forms & accusative forms (15/15 ✅)
- Confirmed: **їм** ← їсти (verb), **п'ю** ← пити (verb), **іду** ← іти (verb), **бачу** ← бачити (verb), **знаєш** ← знати (verb), **кілограм** (noun), **тридцять** (numeral), **кашу** ← каша (Acc.sg.), **каву** ← кава (Acc.sg.), **Олену** ← Олена (Acc.sg. proper noun), **брата** ← брат (Acc.sg. animate), **мого** ← мій (pron adj Acc.sg.m.), **коштує** ← коштувати (verb), **коштують** ← коштувати (verb), **дайте** ← дати (imperative pl.)
- Not found: none

### Batch 3 — Supplementary food + shopping vocab (15/15 ✅)
- Confirmed: **снідаю** ← снідати (verb), **обід** (noun), **вечеря** (noun), **чай** (noun), **сік** (noun), **хліб** (noun), **м'ясо** (noun), **риба** (noun), **суп** (noun), **салат** (noun), **фрукти** ← фрукт (noun), **овочі** ← овоч (noun), **ціна** (noun), **рахунок** (noun), **замовити** (verb, pf.)
- Not found: none

**Total: 45/45 words confirmed in VESUM. No words to avoid.**

---

## Textbook Excerpts

### Section: Що ми знаємо? (Self-check M36–M40)
> *"Їжа й напої українців у XIX ст., як і раніше, були пов'язані з продуктами землеробства та тваринництва… Повсякденними стравами були, як і колись, борщ, пшоняний куліш, різні каші… Із напоїв домашнього приготування найпоширенішими були узвари зі свіжих та сушених фруктів…"*
> Source: Grade 9, gisem (tier 2) — establishes борщ, каші, напої as culturally grounded Ukrainian food vocabulary.

### Section: Читання (Anna at the market and café)
> *"Плануєте швидко пообідати? Тоді вам до нас! Широкий вибір холодних закусок: салатів, бутербродів, тарталеток, фруктових та овочевих соків. Пропонуємо холодні та гарячі напої, лимонади! Кожна шоста чашечка кави за наш рахунок!"*
> Source: Grade 8, Заболотний (tier 1, p.172) — authentic café notice text modeling menu language, кава, рахунок, ordering context. Use as model for the читання text.

### Section: Граматика — Знахідний відмінок inanimate
> *"Іменник у формі знахідного відмінка означає предмет, на який спрямована дія, і в реченні виступає додатком. ПОРІВНЯЙМО: Їде автомобіль. / Ремонтують автомобіль. … Знахідний відмінок виражає повне охоплення предмета дією, а родовий – часткове. ПОРІВНЯЙМО: купи сіль (усю) / купи солі (частину). Діти поїли (кашу, каші)."*
> Source: Grade 6, Заболотний (tier 2, p.94) — direct textbook explanation of Acc. inanimate with food example **кашу**. Also contrasts Acc/Gen partial—critical for M37 recap.

### Section: Граматика — Скільки коштує / Гривня forms
> *"В українській мові маємо пароніми гривна і гривня. Гривна — металева прикраса у вигляді обруча… Гривня — назва української грошової одиниці. Скорочено позначаємо грн (без крапки в кінці). Зверніть увагу! Ці два іменники належать до різних груп відмінювання: гривна — до твердої (гривни, гривною), а гривня — до м'якої (гривні, гривнею)."*
> Source: Grade 6, Литвинова (tier 1, p.244) — authoritative paronym warning + declension paradigm for гривня. Essential for M39 recap: use **гривня / гривні / гривень** (soft declension), never гривна forms.

### Section: Граматика — Знахідний відмінок animate (маsc = Genitive)
> *"Іменники, що позначають назви істот, відповідають на питання хто?, а назви неістот — на питання що?… Істоти — назви людей: тато, Алла; тварин: їжак, колібрі; міфологічних і казкових персонажів: мавка, Перун, Колобок; померлих людей: мрець, покійник; шахових фігур, карт та іграшок, що імітують людей і тварин: пішак, валет, лялька"*
> Source: Grade 6, Авраменко (tier 1, p.78–79) — defines animate (хто?) vs inanimate (що?), listing human names as animate. Grounds the "Acc animate masc = Genitive" rule: **брата** (Gen.sg. = Acc.sg.) ← брат.

### Section: Діалог (Day of food and shopping)
> *"Ситуація. Складіть діалог (6–8 реплік) в офіційно-діловому стилі… Варіант Б. Ви зайшли в кабінет… щоб замовити учнівський квиток."*
> Source: Grade 6, Заболотний (tier 2, p.33) — dialogue structure model (6–8 реплік). Also note: the café notice from Grade 8 (above) provides authentic language for ordering dialogue.

### Section: Підсумок — Числівники (тридцять)
> *"Числівники від п'яти до тридцяти, а також кільканадцять відмінюються однаково… Н. п'ять / Р. п'яти, п'ятьох / Зн. п'ять, п'ятьох … [тридцять — same paradigm]"*
> Source: Grade 11, Авраменко (tier 2, p.37) — confirms **тридцять** is a regular numeral in the 5–30 group. Nom/Acc form = тридцять ✅ (correct in dialogue: *Тридцять гривень*).

---

## Grammar Rules

- **Знахідний відмінок inanimate**: Fem. nouns -а → -у (каша→кашу, вода→воду, кава→каву); masc. inanimate = Nom. (борщ→борщ, суп→суп). Confirmed by Grade 6 Заболотний textbook directly.
  
- **Знахідний відмінок animate masculine = Genitive**: брат→брата, Андрій→Андрія. Confirmed by animate/inanimate rule in Grade 6 Авраменко (§41). Feminine animate -а→-у same as inanimate (Олена→Олену). In plan dialogue: *ти знаєш мого брата?* — **брата** (Gen.sg. = Acc.sg. animate masc.) ✅

- **Гривня declension (soft group)**: Н. гривня / Р. гривні / Д. гривні / Зн. гривню / Ор. гривнею / М. гривні. Plural Gen: гривень. Правопис 2019 §84 (noun declension soft group — Правопис search returned §5 on letter Г, which is not the case rule; morphology rules are in §§84–100 of Правопис). Confirmed by Grade 6 Литвинова.
  
- **⚠️ PARONYM WARNING — гривна ≠ гривня**: гривна = jewelry (hard declension); гривня = currency (soft declension). NEVER write *гривна* when meaning money. The plan correctly uses гривня/гривні/гривень ✅.

- **тридцять** (numeral 30): Nom./Acc. = тридцять. Gen. = тридцяти/тридцятьох. Used correctly in dialogue: *Тридцять гривень* ✅.

---

## Calque Warnings

- **замовити** (to order food): ✅ CORRECT — Антоненко-Давидович explicitly confirms: "заказати" means "to forbid/command" — using it for ordering food is an error. Correct Ukrainian = **замовити** (pf.) / **замовляти** (impf.). Plan uses замовити throughout ✅.

- **кава з молоком**: ✅ OK — No calque flagged. "З + Instrumental" for "with" is natural Ukrainian structure. кава з молоком is standard Ukrainian ✅.

- **іти на ринок**: ✅ OK — Антоненко-Давидович discusses "базар/ринок" context. The modern standard Ukrainian word for a food market is **ринок**. Plan's *Потім іду на ринок* is natural ✅. (Avoid "базар" which has more informal/Soviet connotations in modern usage.)

- **рахунок** (bill at café): ✅ OK in café context — Антоненко-Давидович warns against *"по рахунку"* (= "sparingly" calqued from Russian "по счёту") and against using рахунок in evaluative sense ("на доброму рахунку"). However, **рахунок** as "the bill/check at a restaurant" is correct Ukrainian. Plan's implied usage (рахунок = restaurant bill) is ✅.

- **Мені каву, будь ласка**: ✅ OK — Dative "Мені" for ordering (elliptical: "bring me") is natural Ukrainian ellipsis used in textbook café situations. Not a calque ✅.

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| їжа | **A1** | ✅ On target |
| борщ | **A1** | ✅ On target |
| кафе | **A1** | ✅ On target |
| гривня | **A1** | ✅ On target |
| сніданок | **A1** | ✅ On target |
| кілограм | **A1** | ✅ On target |
| замовляти / замовити | **A1** | ✅ On target |
| їсти | **A1** | ✅ On target |
| кава | **A1** | ✅ On target |
| ринок | **A2** | ⚠️ One level above A1 target |

**Note on ринок (A2):** This word was introduced in M39 (shopping) and is being reviewed in this checkpoint module — using it in a recap context is pedagogically sound. The word appears in authentic A1–A2 Ukrainian teaching materials. No substitution needed for a checkpoint module. Flag in writer notes that this is review vocabulary, not new introduction.
</pre_verified_facts>


## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Food and Shopping
**Module:** checkpoint-food-shopping | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Що ми знаємо? (What Do We Know?)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 143
> **Score:** 0.50
>
> І якраз у яму 
> втрапить. А ми вже вириємо, постараємося.

## Читання (Reading Practice)

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 239
> **Score:** 0.33
>
> 239
> Відомості із синтаксису й пунктуації. Кома між частинами складного речення
> Про борщ я можу розпо-
> відати годинами. Ні для кого 
> не секрет що майже у кожній 
> родині існує свій особливий 
> рецепт борщу. Хтось не уявляє 
> борщ без квасолі а хтось готує 
> його без капусти. Всі ці варіан-
> ти мають право на існування 
> бо немає якогось «правильно-
> го» рецепту, просто в кожного 
> є свій сімейний борщ.
> І досі популярним є узвар із сухофруктів це дуже корисний 
> і поживний напі й.
> Полтава славиться галушками і ми із задоволенням ласуємо 
> ними коли приїжджаємо в це місто до родичів.
> 2. Підкресліть граматичні основи, визначте тип речень .
> 3. Згадайте ваші улюблені страви . Опишіть їх складними реченнями .
> Вправа 384
> 1. Прочитайте допис відомого 
> українського шеф-кухаря 
> Євгена Клопотенка .
> 2.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 237
> **Score:** 0.50
>
> 237
> Відомості із синтаксису й пунктуації. Кома між частинами складного речення
> Кома між частинами складного 
> речення, з’єднаними безсполучниковим 
> і  сполучниковим зв’язком
> Вправа 381
> 1. Прочитайте речення .
> В усьому світі відомі 
> український борщ 
> і вареники.
> В усьому світі відомий україн-
> ський борщ, і вареники не посту-
> паються йому за популярністю.
> Рецепт вергунів 
> передала моїй мамі її 
> прабабця і попросила збе-
> рігати його в нашій сім’ї.
> Рецепт вергунів передала моїй 
> мамі її прабабця, і він досі збері-
> гається в нашій сім’ї.
> Між частинами складного речення в  усному мовленні робимо 
> паузу і  підвищуємо тон; на  письмі ставимо розділовий знак  — 
> переважно ко му .

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 158
> **Score:** 0.33
>
> 158
> ЖИВИЛЬНІ ДЖЕРЕЛА МУДРИХ КНИГ
> Вона в нас не вимовляє літе-
> ру «р». 
> За мить Яришка вже ставила 
> на стільці переді мною молоко, 
> яєчню, сир і хліб із маслом.
> Я збагнув, що в хаті нікого 
> немає, усі на роботі, і їй доручено 
> доглядати мене.
> – Будь ласка, любий бгатику, 
> їж! – сказала вона солодким голосом.
> Я насторожився.
> А коли вона втретє сказала «любий бгатику» («Любий 
> бгатику, спегшу пгоковтни таблетку»), це вже мене зовсім 
> збентежило.
> «Любий бгатику!» Вона ніколи мене так не називала. 
> Вона завжди казала на мене «загаза чогтова», «так тобі й 
> тгеба», «щоб ти гозбив свою погану могду...». І раптом – 
> «любий бгатику!..».
> Кепські, виходить, мої справи. Може, і зовсім безнадійні. 
> Може, я вже й не встану. Тому-то всі такі ніжні до мене: 
> і батько, і мати, і дід...

## Граматика (Grammar Summary)

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 47
> **Score:** 0.50
>
> 47
> 90. 
> 1. Прочитай текст і розглянь малюнок. Постав запи-
> тання до кожного абзацу.
> ОДНА ГРИВНЯ — ОДИН ВІЛ
> Гривня з’явилася за часів Київської Русі. Це був зли-
> ток — срібний, іноді золотий. За одну гривню можна було 
> купити вола.
> Гривні знову з’явилися за часів відродження україн-
> ської державності в 1919–1920 роках. Тепер — це наші 
> українські гроші.
> 2. Визнач рід та відмінок виділених іменників. За потреби 
> користуйся таблицями на сс. 41–42.
> 91. 
> 1. Прочитай і спиши речення. Підкресли в них голов-
> ні члени. Визнач, у яких відмінках ужито виділений 
> іменник. Обґрунтуй свою відповідь.
> 1. Українська державність відродилася в 1919–1920 ро-
> ках. 2. Український народ виборов свою державність 
> у 1919–1920 роках.
> 2.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 171
> **Score:** 0.25
>
> 171
> 171
> § 87.  Узгодження  кількісних числівників  з  іменниками
> райдужної троянди стартує від двадцяти долара (З інтернету). 5. Десять 
> раз поспіль обирали запорожці Сірка отаманом (М. Слабошпицький).
> А.	 Виконайте розбір виділеного числівника як частини мови (письмово).
> Б.	 Визначте, до яких груп за значенням належать усі числівники (усно).
> 4.	 Виконайте завдання в тестовій формі.
> 1.	 Помилково узгоджено числівник з іменником у варіанті
> А	 два шестикласника
> Б	 п’ять із чвертю тонн
> В	 дев’ять кавунів 
> Г	 три харків’янина
> 2.	 Правильно узгоджено числівник з іменником у варіанті
> А	 два вагона
> Б	 три озера
> В	 чотири дня 
> Г	 сто два грама
> 3.	 Правильно узгоджено числівник з іменником у рядку
> А	 тридцять два грузини
> Б	 сорок три львів’яни
> В	 сто чотири кияни 
> Г	 три вінничани  
> 5.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 18
> **Score:** 0.33
>
> 18
> 1.	Прочитайте тексти та виконайте завдання.
> У крамниці музичних інструментів:
> — Чи є у вас трембіта? 
> — Так, є, — відповіла продавчиня.
> — Скільки вона коштує? 
> — Дев’ять тисяч гривень.
> Відвідувач крамниці му­
> зичних інструментів поціка­
> вився, чи є в продажу трем­
> біта й скільки вона коштує. 
> Йому відповіли, що є і вар­
> тість її — дев’ять тисяч гри­
> вень.
> А.	 У якому тексті за допомогою мовних засобів краще передано атмо­
> сферу й динаміку живого спілкування?
> Б.	 Завдяки чому досягнуто такого ефекту? 
> Пряма мова — це точно передане висловлення певної особи: Покупець 
> запитав у продавчині: «Чи є у вас трембіта?» Згадайте правила вживан­
> ня розділових знаків за схемами (П — пряма мова, А, а — слова автора): 
> А: «П».         А: «П?»          А: «П!»       «П», — а.      «П?» — а.

## Діалог (Connected Dialogue)

## Підсумок — Summary

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 3
> **Score:** 0.25
>
> . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
> Підсумковий тест . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 84
> Підсумовуємо й  узагальнюємо . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
> ФРАЗЕОЛОГІЯ . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
> Фразеологізми . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
> Різновиди фразеологічних одиниць . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 96

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 4
> **Score:** 0.50
>
> 4
> Зміст
> Підсумковий тест . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
> Підсумовуємо й  узагальнюємо . . . . . . . . . . . . . . . . . . . . . . . . . . 102
> ФОНЕТИКА. ГРАФІКА. ОРФОЕПІЯ. ОРФОГРАФІЯ . . . . . . . . . 103
> Фонетика. Звуки мовлення . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
> Транскрипція  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 107
> Голосні та приголосні звуки . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110
> Голосні наголошені й  ненаголошені  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
> Особливості вимови ненаголошених  голосних . . . . . . . . . . . . . . .

## Grammar Reference


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Співвідношення звуків і букв
> **Source:** МійКлас — [Співвідношення звуків і букв](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/spivvidnoshennia-zvukiv-i-bukv-41281)

### Теорія:

*www.ua.pistacja.tv*  
 
Як ти вже знаєш, в українській мові є  38  **звуків** і 33  **літери** для передачі цих звуків на письмі.
Чому така різниця між кількістю звуків і букв?
Деякі букви \(я, ю, є\) позначають **два** звуки у певних позиціях.

Букви ї, щ завжди позначають

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~200 words)
- `## Підсумок — Summary` (~150 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1000 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **Hosting a вечеря (f, dinner party) — full flow: shopping for продукти (pl) at the ринок (m, market), cooking вареники (pl) and салат (m), setting the table with тарілки (pl, plates) and склянки (pl, glasses), serving guests.**
     Speakers: Господиня (host), Гості (guests)
     Why: Consolidation: продукти(pl), вареники(pl), тарілка(f), склянка(f)

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary



### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Що ми знаємо? (~220 words total)
- P1 (~60 words): Opening self-check framing — "A1.6 covered five topics. Let's see what you can do!" Present 5 checkboxes as self-assessment prompts: ✓ Name 10 foods and 5 drinks (М36) ✓ Say what you eat/drink using accusative (М37) ✓ Order at a café (М38) ✓ Ask prices and buy things (М39) ✓ Use accusative for people (М40)
- P2 (~80 words): Quick vocabulary warm-up — two mini-lists for self-check. Їжа: борщ, вареники, салат, хліб, сир, піца, каша, яєчня, суп, котлета. Напої: кава, чай, вода, сік, молоко. Encourage learner: "Cover the list. Can you recall 10 foods and 5 drinks without looking? Then you're ready."
- P3 (~80 words): Grammar warm-up prompt — four quick pattern checks with answers to verify: (1) Я їм ___ (борщ → борщ, салат → салат). (2) Я п'ю ___ (кава → каву, вода → воду). (3) Мені ___, будь ласка (сік → сік, піца → піцу). (4) Я бачу ___ (Олена → Олену, брат → брата). "If all four feel natural, proceed. If not, revisit M37 and M40."

---

## Читання (~270 words total)
- P1 (~30 words): Short lead-in — "Read about Anna's day. Notice how she uses accusative for food, drinks, and people. Find at least six accusative forms."
- Reading text (~200 words): Titled "День Анни" — a connected narrative paragraph using M36-M40 vocabulary. Anna wakes up, eats кашу and drinks каву з молоком for breakfast. She goes to the ринок and asks: «Скільки коштують помідори?» — «Тридцять гривень кілограм.» — «Дайте кілограм, будь ласка.» She buys хліб, сир, і яблука. Then she goes to a café, sits down: «Тут вільно?» She orders: «Мені борщ і воду, будь ласка.» She sees a friend Олена across the room: «О, я бачу Олену! Олено, привіт!» Олена comes over. Anna says: «Ти знаєш мого брата Михайла? Це мій брат.» They eat together. At the end: «Рахунок, будь ласка. Можна карткою?» — «Звичайно.»
- P2 (~40 words): Comprehension check — 3 quick questions after the text: (1) Що Анна купує на ринку? (2) Що вона замовляє в кафе? (3) Кого вона бачить у кафе? Learner answers in Ukrainian using full sentences.

---

## Граматика (~220 words total)
- P1 (~50 words): Mini-header "Шість ключових шаблонів A1.6" — frame as a quick-reference summary, not new material. "You learned all of this in M36–M40. Here it is in one place."
- P2 (~40 words): Pattern 1 — Food/drink vocabulary chunks. Їжа + напої + meals: сніданок, обід, вечеря. Key chunk: кава з молоком, борщ зі сметаною, хліб із сиром. «Я їм кашу на сніданок. Я п'ю каву з молоком.»
- P3 (~40 words): Pattern 2 — Accusative inanimate. Rule: masculine nouns don't change (борщ → борщ, хліб → хліб). Feminine -а/-я nouns: кава → каву, вода → воду, піца → піцу. Three column mini-table: Nominative | Accusative | Example sentence.
- P4 (~40 words): Pattern 3 — Ordering and prices. Fixed phrases: «Мені ___, будь ласка» / «Скільки коштує/коштують?» / «Дайте ___, будь ласка» / «Рахунок, будь ласка» / «Можна карткою?» / гривня → гривні → гривень (1/2-4/5+).
- P5 (~50 words): Pattern 4 — Accusative animate. Feminine same as inanimate: Олена → Олену, мама → маму. Masculine animate = genitive ending: брат → брата, лікар → лікаря, друг → друга, вчитель → вчителя. Quick contrast: «Я бачу борщ» (inanimate, no change) vs «Я бачу брата» (animate, -а).

---

## Діалог (~220 words total)
- P1 (~20 words): Scene-setter — "Наталя та Дмитро починають день. Читайте і стежте за відмінками." (Natalia and Dmytro start their day.)
- Dialogue (~140 words): Three-scene connected dialogue covering all A1.6 skills:

**Сніданок:**
— Що ти їш на сніданок?
— Я їм кашу і п'ю каву з молоком. А ти?
— Я їм яєчню і хліб із сиром.

**На ринку:**
— Скільки коштують помідори?
— П'ятнадцять гривень кілограм.
— Дорого! А яблука?
— Двадцять гривень. Дуже смачні!
— Добре, дайте кілограм яблук, будь ласка.

**У кафе:**
— Тут вільно?
— Так, сідайте!
— Мені борщ і воду, будь ласка.
— О, я бачу Олену! Олено, привіт! Ти знаєш мого брата Дмитра?
— Ні, не знаю. Дуже приємно, Дмитре!
— Рахунок, будь ласка. Можна карткою?
— Звичайно. Все було дуже смачно!

- P2 (~60 words): Post-dialogue note — annotate the three grammar patterns used. Bold two examples for each: (1) Accusative inanimate: **кашу**, **яєчню**, **воду**, **борщ**. (2) Accusative animate: **Олену**, **брата Дмитра**. (3) Café/market phrases: **Мені борщ**, **Дайте кілограм**, **Рахунок, будь ласка**. "Did you spot all of them in the dialogue?"

---

## Підсумок (~150 words total)
- P1 (~150 words): A1.6 achievement summary in celebratory but informative tone. "You have completed A1.6 — Food and Shopping. Here is what you can now do:
  - ✓ Talk about їжа та напої — foods, drinks, and meals (М36)
  - ✓ Use the accusative case for inanimate nouns — борщ, каву, воду, піцу (М37)
  - ✓ Order at a кафе — «Мені борщ, будь ласка» / «Рахунок» / «Можна карткою?» (М38)
  - ✓ Shop at the ринок — «Скільки коштує?» / «Дайте кілограм» / гривня/гривні/гривень (М39)
  - ✓ Use the accusative case for animate nouns — «Я бачу Олену» / «Я знаю брата» (М40)

  **Наступний крок — A1.7: Спілкування.** You will learn to make plans, write messages, and talk on the phone. Ukrainian is becoming your language."

---

Grand total: ~1080 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
