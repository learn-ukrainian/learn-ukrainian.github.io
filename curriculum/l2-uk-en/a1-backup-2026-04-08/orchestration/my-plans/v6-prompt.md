<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Dialogues'
- FIX: Missing section heading: 'Summary'
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

Write the full prose content for module **51: My Plans** (A1, A1.8 [Past, Future, Graduation]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
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
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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

**Confirmed (15/15):**
- ✅ план (noun)
- ✅ тиждень (noun)
- ✅ вільний (adj)
- ✅ зустріч (noun)
- ✅ відпочивати (verb)
- ✅ прибирати (verb)
- ✅ вечірка (noun)
- ✅ зустрінемося → lemmas: зустрінутися / зустрітися (verb — both found)
- ✅ задоволення (noun — base of «з задоволенням»)
- ✅ жаль (adv + noun — base of «на жаль»)
- ✅ допізна (adv)
- ✅ звичайно (adv)
- ✅ квартира (noun)
- ✅ кіно (noun)
- ✅ вчити (verb)

**Not found:** — none. All 15 vocabulary items confirmed in VESUM.

---

## Textbook Excerpts

### Section: Dialogues — Planning / Future tense
> "У середу я планую ? . Для цього мені потрібно ? . Я маю зробити ? . Розкажіть, як ви плануєте свій день (один із днів тижня на вибір). Що ви в цей день **будете робити**? Наведіть приклад такого плану за зразком. **План — заздалегідь визначена програма дій на певний час.**"
>
> Source: Вашуленко, Grade 2 (p. 83) — confirms days of week + буду + infinitive as the natural planning frame at early levels

### Section: Планування (Planning) — Future tense analytic form
> "Дієслова майбутнього часу, які відповідають на питання що буду робити?, виражених двома словами: **буду іти / будеш іти / буде іти / будемо іти / будете іти / будуть іти**. При змінюванні дієслів майбутнього часу, виражених двома словами, змінюється тільки допоміжне слово **бути**."
>
> Source: Кравцова, Grade 4 (p. 109) — confirms the analytic future (буду + infinitive) conjugation pattern

### Section: Планування — Time expressions (зранку/вдень/ввечері + days)
> "Зараз я (що роблю?) … . Після уроків я (що буду робити?) … . Увечері я (що робитиму?) … ."
>
> Source: Захарійчук, Grade 4 (p. 106) — confirms time-of-day adverbs used naturally alongside future tense planning sentences

### Section: Мій тиждень (My Week) — Days of the week
> "Тиждень починає … . Після нього приходить … . За ним настає … . Четвертий день тижня — … . А п'ятий — … . П'ять днів працюємо, а в **суботу і неділю** відпочиваємо."
>
> Source: Пономарова, Grade 3 (p. 77) — confirms all 7 day names; confirms «в суботу» / «в неділю» as established usage

### Section: Invitation phrases / Responses (згода/відмова)
> "Дякую за запрошення, мені приємно. **Обов'язково прийду.** Радо приймаю твоє запрошення! … **Дякую, але я не зможу бути.** Мені приємно, однак у цей день я не зможу прийти. **Мені шкода**, але я не зможу бути."
>
> Source: Голуб, Grade 5 (p. 202) — rich inventory of natural invitation acceptance/refusal phrases; validates using «Добре! З задоволенням!» and «На жаль, не можу» as the natural register for this module

### Section: Summary (planning toolkit)
> "Уміння планувати й структурувати свій **день, тиждень**, місяць і навіть рік дуже спростить ваше життя й обов'язково приведе до успіху. … Плануйте свій день (тиждень, місяць). Складайте список найбільш термінових завдань."
>
> Source: Заболотний, Grade 8 (p. 239) — confirms «планувати тиждень» as the natural framing; validates the module's planning lexis

---

## Grammar Rules

- **Analytic future (буду + infinitive):** Confirmed by Grades 4 textbooks (Вarzatska, Kravtsova, Zahariichuk). Rule: the two-word future form conjugates only the auxiliary **бути** (буду / будеш / буде / будемо / будете / будуть); the main verb stays in infinitive. This is the primary future form for A1 learners. Grade 7 (Litvinova p. 47) adds context: «Дієслова у формі майбутнього часу позначають дію, що відбуватиметься або відбудеться після моменту мовлення.»

- **У/В alternation before days of week:** Правопис §23 — confirmed. The plan's usage is correct:
  - «у понеділок, у вівторок, у середу, у четвер, у п'ятницю, у суботу» — У before consonant (п, в, с, ч, п, с) ✅ (§23.1.1 — «у вівторок» specifically covered by §23.1.4: use У before в)
  - «в неділю» when preceded by «у суботу» — суботу ends in vowel У → use В before consonant Н (§23.2.6) ✅

- **Days of week (spelling):** Confirmed by Grade 3 (Ponomarova p. 77) — all day names are dictionary words that must be verified. All lowercase in running text.

---

## Calque Warnings

- **«з задоволенням»** (with pleasure): Style guide search returned no warning for this phrase. Natural Ukrainian — the noun задоволення (satisfaction/pleasure) is in VESUM with 7 lemma matches. The phrase is standard and widely attested. **OK ✅**

- **«на жаль»** (unfortunately): Style guide returned no calque warning. Natural Ukrainian adverbial phrase. **OK ✅**

- **«звичайно»** (of course): Style guide returned no direct warning. PULS confirms it as A1. Note: Антоненко-Давидович entry on «звісно» (B1 per PULS) suggests «звісно» as a stylistic alternative, but «звичайно» in the sense of "of course" is standard Ukrainian. **OK ✅**

- **«давай зустрінемося»** (let's meet): ⚠️ **PARTIAL FLAG.** The style guide entry (AD-149) warns that «зустрічатися» must NOT be used in the sense of "to be found / to occur" (a Russianism calquing Russian «встречается»). However, «зустрінемося» in the sense of **physically meeting a person** is the correct, natural usage — confirmed by the style guide example itself: «Зустрінемось через кілька день (днів)» (AD-201). The module usage is correct. **OK for the intended meaning ✅** — but the writer should NOT use «зустрічатися» to mean "to be encountered/found."

- **«вчитися» vs «навчатися»:** The plan uses «буду вчитися» — both вчитися (A1) and навчатися are correct Ukrainian. No calque risk. **OK ✅**

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| план | A1 | ✅ On target |
| тиждень | A1 | ✅ On target |
| відпочивати | A1 | ✅ On target |
| звичайно | A1 | ✅ On target |
| квартира | A1 | ✅ On target |
| кіно | A1 | ✅ On target |
| вчити / вчитися | A1 | ✅ On target |
| вільний | **A2** | ⚠️ One level above — acceptable for M51 (A1.8, graduation) |
| вечірка | **A2** | ⚠️ One level above — acceptable for A1.8 graduation module |
| прибирати | **A2** | ⚠️ One level above — acceptable for A1.8 graduation module |
| допізна | **Not in PULS** | ⚠️ Level unverified — VESUM confirms it exists as adv.; use with care, introduce with context |
| зустріч (noun) | **Not directly in PULS** | ⚠️ зустрітися = A2; зустрінутися = B1. Treat зустріч as A2-level item |

**Summary of CEFR flags:**
- 7 words confirmed A1 ✅
- 3 words at A2 (вільний, вечірка, прибирати) — acceptable for A1.8 graduation module, but should be explicitly introduced/glossed
- допізна: not in PULS database; attested in VESUM; treat as above-A1, use sparingly with full context clue in dialogue
- зустрінемося (chunk): the verb root зустрітися is A2/B1 — present as a formulaic **chunk** ("let's meet"), not as a productive grammar item, which is the plan's stated approach ✅
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
# Verified Knowledge Packet: My Plans
**Module:** my-plans | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 140
> **Score:** 0.33
>
> § 23  Прислівник як частина мови  
> 137
> Їсти (піцу/смачно), повернутися (надвечір/після уроків), 
> чекати (біля супермаркету/отам), планувати (цієї зими/взим­
> ку), працювати (довго/три години), бути (в школі/деінде), по­
> бачитися (зранку/о дев’ятій), дістатися (пішки/тролейбусом), 
> говорити (по­китайськи/китайською мовою).
> Вправа 186
>  
> Доповніть словосполучення прислівниками, що відповідатимуть на по-
> ставлені питання 
> Іти (куди?), іти (коли?), іти (звідки?), іти (як?); співати (як?), 
> співати (коли?), співати (де?); радіти (наскільки?), радіти (де?), 
> радіти (як?), радіти (з якої причини?).
> Вправа 187
>  
> Складіть кілька словосполучень із кожним запропонованим 
> діє словом так, щоб залежним словом був прислівник (за 
> зразком попередньої вправи) 
> Бігти, писати, розуміти.

> **Source:** golub, Grade 6
> **Section:** Сторінка 33
> **Score:** 0.50
>
> 33
> 69   Визначте основну думку тексту. Випишіть приклади словозміни 
> і словотворення. Поділіться досвідом прибирання своєї кімнати, 
> квартири чи будинку. Розберіть за будовою виділені слова. Випи-
> шіть слова, уставляючи пропущені букви. Уявімо собі захаращену кімнату. Безлад у ній не утворю-
> ється сам собою. Ви, людина, яка живе в ній, утворюєте без-
> лад. Є такий вислів: «Безлад у кімнаті — безлад у голові». Чи говорили ви собі: «Я просто не вмію приб..рати» або 
> «Немає сенсу пр..бирати: я від пр..роди неохайна людина»? Багато людей роками підтримують таке негативне уявлення 
> про себе, але воно зникає одразу ж, коли вони опиняються 
> у своєму б..здоганно чистому просторі. Щойно ви почнете пр..бирати, ви «перезавантажите» своє 
> життя. У результаті воно почне змінюватися.

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 138
> 138
> Варіант В. Напишіть есе (6–8 речень) на одну із запропонованих тем: «Мій 
> вихідний», «Мої домашні обов’язки», «Мій день народження». Використайте що-
> найменше два дієприслівники та два дієприкметники.
> Виконайте завдання. 
> 1. Пасивними є обидва дієприкметники в рядку
> А перебитий, усвідомлений
> В розбитий, змарнілий
> Б посивілий, змоклий 
> Г замусолений, навислий
> 2. Орфографічну помилку допущено в рядку
> А Відійшов, не здужавши підняти штангу.
> Б Недобачаючи в темряві, спіткнувся.
> В Говорив завжди правду, не навидячи брехню.
> Г Програли, недооцінивши сили суперника. 
> 3. Окремо треба писати не з дієприкметником у рядку
> А не/дописана картина відомого художника
> Б не/з’ясовані вчасно важливі питання
> В не/прочитаний допис у соцмережі
> Г не/дооцінений талант молодого артиста
> 4.

## Планування (Planning)

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 255
> **Score:** 0.33
>
> 252
> Повторення
> ***
> У мене стільки планів на канікули. А в підсумку як 
> завжди: комп — спати — комп — спати — комп — спати… 
> Проти системи не попреш.
> ***
> Останній тиждень перед літніми канікулами — це така 
> довга п’ятниця перед великими вихідними.
> 2   Випишіть у три групи прийменники, сполучники та частки 
> Вправа 337
> 1  Спишіть сполучення слів, заповнивши пропуски та знявши риску 
> Не/мов/би/то зна..мо, пиш..мо смс/повідомлення аби/
> кому, без/перестанку роб..ш, чим/дуж намага..мося, при-
> йшли хтозна/на/віщо, не/стямлюся з радости, дивит..ся 
> с/під/лоба, робити не/зважаючи/на втому, не/втомний сусід, 
> побач..мося завтра в/день, займа..ся що/неділі.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 193
> **Score:** 0.50
>
> 193
> Відомості із синтаксису й пунктуації. Словосполучення
> 08.00
> 08.15
> 08.30
> 08.45
> 2. Усно назвіть час усіма можливими способами .
> 3. Доповніть і  розіграйте діалог про розклад дзвінків .
> — Коли починається перший урок?
> — О …
> — А закінчується?
> — …
> 4. Об’єднайтесь у  групи й  підготуйте діалоги для різних ситуацій з  вико-
> ристанням позначення часу (зустріч із друзями, відвідування спортивної 
> секції, перегляд улюбленого серіалу…) . Розіграйте ситуації перед класом . 
> Жартувати й  фантазувати можна і  варто!
> Вправа 313
> Виправте помилки .

## Мій тиждень (My Week)

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 16
> **Score:** 0.33
>
> § 1  Мовні обов’язки українців та українок  
> 13
> 3   Що нового для себе ви дізналися з  інфографіки?
> 4  Розіграйте ситуації, у  яких дотримано наведених статей Закону  Напри-
> клад, ви сплачуєте за обід у  шкільній їдальні, проводите шкільний захід, 
> купуєте квиток на фільм, обговорюєте план заходів на перший семестр 
> тощо 
> 5   Пригадайте, чи спостерігали ви порушення Закону про мову  Розка-
> жіть про ці випадки 
> 6   Поміркуйте, як варто поводитися в  ситуації, коли Закон про мову по-
> рушують  Наведіть приклади реплік  Змоделюйте ситуацію 
> Вправа 6 
> 1   Ознайомтеся зі статтею із тлумачного словника 
> Обо́в’язок — те, чого треба беззастережно дотримуватися, 
> що слід безвідмовно виконувати відповідно до вимог суспіль-
> ства або виходячи з власного сумління.

## Summary

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 205
> **Score:** 0.25
>
> 205
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
> ОП
> О
> І
> П
> Н
> М
> Н
> Т
> М
> Ольга Петрівна: Добрий 
> день, шановні учні! 
> Усі пам’ятають, що 
> завтра йдемо на екс-
> курсію? Збираємося 
> біля школи о 10.00. 
> Візьміть із собою 
> бутерброди, воду 
> й кишенькові гро-
> ші. Не запізнюйтеся: 
> на нас чекатимуть. 
> До зустрічі!
> Оксана: Усе зрозуміла, 
> дякую.
> Іван: Ok
> Петро: 
> Наталка: 
> Микита: Це вже завтра?!
> Ніна: 
> Термінатор:  
> Микола: Дякую 
> за нагадування!
> Вправа 333
> 1. Прочитайте повідомлення в  чаті 
> класу .
> 2. Назвіть спочатку розповідні ре-
> чення, потім питальні та  спону-
> кальні .
> 3. Знайдіть у  чаті та випишіть усі 
> односкладні речення . Поміркуйте 
> та висловте припущення: чому їх 
> так багато?
> 4. Чи всі учасники чату дотримують-
> ся норм мовленнєвого етикету?
> 5.

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 140
> **Score:** 0.50
>
> § 23  Прислівник як частина мови  
> 137
> Їсти (піцу/смачно), повернутися (надвечір/після уроків), 
> чекати (біля супермаркету/отам), планувати (цієї зими/взим­
> ку), працювати (довго/три години), бути (в школі/деінде), по­
> бачитися (зранку/о дев’ятій), дістатися (пішки/тролейбусом), 
> говорити (по­китайськи/китайською мовою).
> Вправа 186
>  
> Доповніть словосполучення прислівниками, що відповідатимуть на по-
> ставлені питання 
> Іти (куди?), іти (коли?), іти (звідки?), іти (як?); співати (як?), 
> співати (коли?), співати (де?); радіти (наскільки?), радіти (де?), 
> радіти (як?), радіти (з якої причини?).
> Вправа 187
>  
> Складіть кілька словосполучень із кожним запропонованим 
> діє словом так, щоб залежним словом був прислівник (за 
> зразком попередньої вправи) 
> Бігти, писати, розуміти.

## Grammar Reference

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 170
> **Score:** 0.50
>
> 167
> § 77.  Особливості  вживання  прийменників
> Зауважте!
> Подані словосполучення можна вживати паралельно: гуляти міс-
> том — гуляти по місту; надіслати поштою — надіслати по пошті; 
> тренуватися щосереди — тренуватися по середах; працювати ноча-
> ми — працювати по ночах. 
> 4.	 Відредагуйте та запишіть словосполучення.
> Згідно правила, не прийти із-за хвороби, ліки від ковіду, відповідно із за-
> коном, зошит по хімії, на протязі року, бал по самостійній роботі, сходили за 
> водою, прийшли по справах, виконувати по схемі, поїхати за грибами, зро-
> бити за вимогою, не дивлячись на обставини, стояв у тополі, пливти по течії.
>  
> Зауважте!
> Вибір прийменників у/в, з/із/зі (зо) залежить від звукового оточення. 
> Пригадайте правила вживання цих прийменників.

> **Source:** litvinova, Grade 7
> **Secti

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Планування (Planning)` (~300 words)
- `## Мій тиждень (My Week)` (~300 words)
- `## Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Subordinate clauses (plan teaches them). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Group chat planning the weekend — У суботу буду прибирати квартиру (f). А я буду бігати в парку (m). Може, ввечері підемо в кіно (n)? Ходімо! О котрій?**
     Speakers: Група друзів (3 people)
     Why: Future + scheduling with квартира(f), парк(m), кіно(n)

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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** план (plan, m), тиждень (week, m), вільний (free, adj), зустріч (meeting, f), відпочивати (to rest), прибирати (to clean), вечірка (party, f)
**Recommended:** зустрінемося (let's meet — chunk), з задоволенням (with pleasure), на жаль (unfortunately), допізна (until late), звичайно (of course), квартира (apartment, f), кіно (cinema, n), вчити (to study/learn)

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
## Діалоги (~330 words total)
- P1 (~20 words): Brief scene-setter — Оля, Тарас, і Марія планують суботу в груповому чаті.
- Dialogue 1 (~120 words): Weekend plan — Що ти будеш робити у суботу? / Зранку я буду прибирати квартиру. / А вдень? / Вдень я буду ходити в магазин. А ти? / Я буду відпочивати! Може, підемо в кафе ввечері? / Добре! О котрій? / О шостій. Добре? / Чудово! До зустрічі у суботу! [Labels: future + time + invitation]
- P2 (~20 words): Brief scene-setter — Дмитро розповідає про свій завантажений тиждень.
- Dialogue 2 (~120 words): Busy week — У тебе є плани на тиждень? / Так, багато! У понеділок я буду працювати допізна. У вівторок буду вчитися. У середу — зустріч з друзями. / А у четвер? / У четвер я буду готувати на вечірку. / А в п'ятницю? / В п'ятницю — вечірка! Ти будеш? / Звичайно буду! [Labels: days of week + future planning]
- P3 (~50 words): Brief comprehension note — point out key patterns: буду + infinitive for all persons, days as fixed time anchors (у понеділок, у вівторок... у суботу, в неділю), ввечері/зранку/вдень as time-of-day modifiers. Ask: Що буде робити Дмитро у четвер?

## Планування (~330 words total)
- P1 (~80 words): Scheduling formula — introduce the core pattern: У + day + time + буду + infinitive. Explicit table of all seven days: у понеділок, у вівторок, у середу, у четвер, у п'ятницю, у суботу, в неділю (note: в before н). Add time-of-day adverbs: зранку, вдень, ввечері. Add clock-time: о дев'ятій, о третій, о шостій. Full combined example: У суботу ввечері я буду дивитися фільм.
- P2 (~80 words): Invitation toolkit — explain three registers: Ходімо в кафе! (imperative, warm), Може, підемо в кіно? (soft suggestion with може), Давай зустрінемося о п'ятій! (collaborative давай + perfective). Checking availability: Ти будеш вільний / вільна у суботу? (adj gender agreement). Responses: Добре! Чудово! З задоволенням! vs. На жаль, не можу.
- Exercise 1 (fill-in, ~50 words): Complete time expressions — У {понеділок|вівторок|середу} я буду працювати. / У суботу {зранку|ввечері|вдень} я буду прибирати квартиру. / {О|В|На} шостій ми будемо дивитися кіно. / У {неділю|суботу|п'ятницю} він буде відпочивати. / У п'ятницю {ввечері|зранку|вдень} буде вечірка. [5 items, focus: day + time + future]
- Exercise 2 (matching, ~50 words): Invitations ↔ responses — Ходімо в кіно! → З задоволенням! / Може, підемо в кафе? → Добре! О котрій? / Ти будеш вільний у суботу? → На жаль, не можу. / Давай зустрінемося о п'ятій! → Чудово! До зустрічі! [4 pairs]
- P3 (~70 words): Preposition note — contrast у/в before days: у понеділок, у вівторок, у середу, у четвер, у п'ятницю, у суботу — but в неділю (в before vowel). Recall from M37: the same у/в euphony rule applies to all prepositions. Two quick drills: fill in у or в before: _понеділок, _неділю, _середу, _п'ятницю.

## Мій тиждень (~330 words total)
- P1 (~20 words): Introduce Тарас — he's planning his whole week, one day at a time.
- P2 (~130 words): Тарас's model week — У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати з другом у кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати — піду в кіно. У суботу зранку буду прибирати, а вдень гуляти в парку. В неділю я буду спати довго! [Each sentence = one day; italicize the буду + infinitive structure for visual clarity]
- P3 (~60 words): Your turn — template prompt: У [день] о [час] я буду [дієслово]. Expansion prompts: Де? (у парку, в кафе, вдома) — З ким? (з другом, з сім'єю, сам/сама) — Що саме? (прибирати квартиру, готувати обід, дивитися фільм). Worked example: У суботу о десятій я буду гуляти в парку з другом.
- Exercise 3 (fill-in, ~50 words): Complete the week plan with correct tense form — У вівторок я {буду вчити|вчив|вчу} українську. / У середу ми {будемо готувати|готували|готуємо} вечерю. / У четвер вона {буде працювати|працювала|працює} допізна. [3 items, focus: future vs. past vs. present tense contrast]
- P4 (~70 words): Mini-writing task — plan your ideal weekend in 4–6 sentences using the model. Checklist: ✓ два дні (субота + неділя) ✓ час (зранку / вдень / ввечері або о котрій?) ✓ місце ✓ буду + infinitive. Sample answer: У суботу зранку я буду спати довго. Вдень я буду гуляти в парку. Ввечері ми будемо дивитися фільм. В неділю я буду готувати сніданок для родини.

## Підсумок (~150 words total)
- P1 (~150 words): Planning toolkit recap — bullet-format:
  • Формула: У [день] о [час] я буду [інфінітив] — У суботу о третій я буду готувати обід.
  • Час доби: зранку → вдень → ввечері
  • Запрошення: Ходімо! / Може, підемо? / Давай зустрінемося!
  • Відповіді: Добре! Чудово! З задоволенням! / На жаль, не можу.
  • Дні тижня: понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя (у/в!)
  • Self-check questions: Що ти будеш робити у суботу? / О котрій? / Ти будеш вільний/вільна? / Ходімо в кафе ввечері?

Grand total: ~1140 words (skeleton framework) → target 1200–1320 words in prose build after dialogue and exercise text fills in fully.
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
