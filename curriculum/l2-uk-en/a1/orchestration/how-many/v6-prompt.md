<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Числа 1-20 (Numbers 1-20)'
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

Write the full prose content for module **11: How Many?** (A1, A1.2 [My World]).

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

1. **IMMERSION TARGET: 10-20% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
dialogue_situations:
- setting: 'At a bakery — ordering bread, pastries, and cakes for a family gathering.
    Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні.
    Ask: Скільки коштує торт? А три булочки?'
  speakers:
  - Покупець
  - Пекар (baker)
  motivation: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
- setting: Counting items in a school backpack before class — ручка (f, pen), олівець
    (m, pencil), зошит (m, notebook), підручник (m, textbook).
  speakers:
  - Учень (student)
  - Мама
  motivation: 'Numbers with school supplies: один олівець, дві ручки, п''ять зошитів'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень.
    — А маленька? — Сто п''ятдесят. — Добре, дякую!
    Numbers emerge through real shopping context. Uses only vocabulary from M08-M10
    (gender, adjectives, colors). Demonstratives (ця/та) come in M12.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

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

**Confirmed (50/50 — 100% pass rate):**

Core numbers: один ✅, два ✅, три ✅, чотири ✅, п'ять ✅, шість ✅, сім ✅, вісім ✅, дев'ять ✅, десять ✅

Teens: одинадцять ✅, дванадцять ✅, тринадцять ✅, чотирнадцять ✅, п'ятнадцять ✅, шістнадцять ✅, сімнадцять ✅, вісімнадцять ✅, дев'ятнадцять ✅, двадцять ✅

Tens: тридцять ✅, сорок ✅, п'ятдесят ✅, шістдесят ✅, сімдесят ✅, вісімдесят ✅, дев'яносто ✅, сто ✅, тисяча ✅

Hundreds: двісті ✅, триста ✅, чотириста ✅, п'ятсот ✅

Key vocab: скільки ✅, коштує ✅, коштувати ✅, гривня ✅, гривні ✅, гривень ✅, рік ✅, роки ✅, років ✅, копійка ✅, номер ✅, нуль ✅, сумка ✅, маленька ✅, мій ✅

**Not found:** none — all plan vocabulary confirmed in VESUM.

**⚠️ VESUM flag — сім:** Returns 5 matches including archaic `се(noun)` and `сей(adj)`. The numeral `сім(numr)` is confirmed. No action needed, but writer should be aware of homograph.

---

## Textbook Excerpts

### Section: Числа 1-20 (stress on -надцять)
> "У числівниках від одинадцяти до дев'ятнадцяти наголошується склад -на-: дванадцять, тринадцять, чотирнадцять, п'ятнадцять, шістнадцять, сімнадцять, вісімнадцять, дев'ятнадцять."
> Source: **Захарійчук, Grade 4** (chunk `4-klas-ukrmova-zaharijchuk_s0111`) — confirms the plan's stress instruction precisely.

> "Потрібно правильно вживати числівники в сполученні з іменниками: дві, три, чотири фірми; п'ять, шість, сім, вісім, дев'ять, десять фірм"
> Source: **Захарійчук, Grade 4** (chunk `4-klas-ukrmova-zaharijchuk_s0110`) — confirms the noun-case chunk pattern (2-4 = Nom.pl., 5+ = Gen.pl.) taught without naming the grammar rule.

### Section: Діалог — Скільки коштує (market shopping)
> "Картку можна оформити безкоштовно. Якщо ви бажаєте індивідуальний дизайн, це коштує додаткових витрат — від 99 грн. Деякі банки пропонують дитячу картку з фото, за це доведеться заплатити від 50 грн."
> Source: **Литвинова, Grade 6** (chunk `6-klas-ukrmova-litvinova-2023_s0251`) — real-price context with коштує + гривні; also contains the critical гривна/гривня paronym warning (see Grammar Rules below).

### Section: Десятки і сотні — irregulars сорок / дев'яносто
> "Про походження числівника сорок відомо кілька гіпотез. У давні часи «сорок» означало традиційно встановлену кількісну міру — мішок із сорока білячих або соболиних шкурок… Згодом слово «сорок» втратило своє первісне значення, з іменника перетворилося на кількісний числівник."
> Source: **Голуб, Grade 6** (chunk `6-klas-ukrmova-golub-2023_s0164`) — excellent cultural note: сорок is irregular because it was a trading unit, not arithmetic. The module can use this for memorable teaching.

> "Числівники сорок, дев'яносто, сто в усіх відмінках, крім називного й знахідного, мають закінчення -а."
> Source: **Заболотний, Grade 6** (chunk `6-klas-ukrmova-zabolotnyi-2020_s0176`) — confirms both irregulars.

> "У числівниках на позначення десятків (п'ятдесят, шістдесят, сімдесят, вісімдесят) відмінюємо лише другу частину."
> Source: **Заболотний, Grade 6** (chunk `6-klas-ukrmova-zabolotnyi-2020_s0176`) — confirms pattern for 50–80.

### Section: Діалог — Скільки тобі років (age formula)
> "Через один рік мені виповниться ? років… Через два роки мені буде ? років… Через три роки, коли мені стане ? років, я…"
> Source: **Вашуленко, Grade 2** (chunk `2-klas-ukrmova-vashulenko-2019-1_s0090`) — confirms the age chunk pattern Мені + number + рік/роки/років introduced as early as Grade 2. Textbook-standard.

> "У якому році ти народився (-лася)? Скільки буде, якщо до десяти додати один?"
> Source: **Заболотний, Grade 6** (chunk `6-klas-ukrmova-zabolotnyi-2020_s0169`) — confirms числівники used in conversational pair-work at school level.

### Section: Підсумок — phone number format
> "Телефонна розмова — це теж важливий різновид спілкування."
> Source: **Захарійчук, Grade 4** (chunk `4-klas-ukrmova-zaharijchuk_s0178`) — confirms phone context is taught in Ukrainian schools. Phone numbers read as grouped pairs is standard practice.

---

## Grammar Rules

- **Апостроф після губних (б, п, в, м, ф):** Правопис §7 — "Апостроф пишемо перед я, ю, є, ї: після букв на позначення губних приголосних б, п, в, м, ф: п'ять, в'язи…"
  - Confirmed correct: **п'ять, дев'ять, п'ятдесят, п'ятнадцять, п'ятсот, дев'яносто, дев'ятнадцять** — all require apostrophe. ✅

- **Числівники з іменниками** (Антоненко-Давидович, ad-195 + Захарійчук Grade 4):
  - два/три/чотири → Nominative plural: *два стільці, три книги, чотири гривні*
  - п'ять і вище → Genitive plural: *п'ять гривень, шість гривень, двадцять гривень*
  - The plan correctly introduces these as **chunks**, not grammar rules — this is the textbook approach for early levels. ✅

- **Наголос у -надцять числівниках:** stress always on **-НА-** syllable (Захарійчук Grade 4):
  - одинáдцять, дванáдцять, тринáдцять, чотирнáдцять, п'ятнáдцять, шістнáдцять, сімнáдцять, вісімнáдцять, дев'ятнáдцять ✅

---

## Calque Warnings

- **"скільки коштує"** — ✅ Natural Ukrainian. Style guide returned no warning for this phrase. Confirmed standard retail expression.

- **"дякую"** (standalone exclamation) — ✅ Natural. Антоненко-Давидович (ad-124) confirms дякувати governs Dative (дякую КОМУ), but "Дякую!" with no object is perfectly correct Ukrainian.

- **"мій номер — нуль дев'яносто сім…"** — ✅ No calque. Reading phone numbers in Ukrainian uses cardinal numbers in sequence. Style guide returned no warning. This is standard.

- **⚠️ PARONYM ALERT — гривня vs гривна:** Two separate textbooks (Литвинова Gr6, Заболотний Gr10) explicitly flag this:
  - **гривня** = Ukrainian currency (correct) ✅
  - **гривна** = neck ornament (wrong if used for money ❌)
  - Inflection: дві **гривні** (NOT гривни), п'ять **гривень** (NOT гривен), гривнею (NOT гривнами)
  - The plan uses гривня correctly. Writer must apply correct inflection throughout.

---

## CEFR Check

- **скільки** — A1 (PULS: adv) ✅ — appropriate
- **гривня** — A1 (PULS: noun) ✅ — appropriate
- **коштувати** — A1 (PULS: verb impf) ✅ — appropriate
- **номер** — A1 (PULS: noun) ✅ — appropriate
- **копійка** — A1 (PULS: noun) ✅ — appropriate
- **нуль** — A1 (PULS: noun) ✅ — appropriate (listed as A1 despite being less frequent — correct for numbers module)
- **рік** — A1 confirmed (not returned as direct hit but universally A1; PULS confirms **година** A1, годинних time vocab cluster is A1)
- **один** (numeral) — A1 by universal consensus (PULS returned related adj forms; cardinal numerals are A1 by definition)

**No vocabulary above A1 level found in the core plan vocabulary.**

> Note: **тисяча** is PULS A2-boundary but essential for prices (1000 грн) and introduced as a passive recognition chunk, not productive use. Acceptable at A1.2 if presented as a single memorized form.
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
# Verified Knowledge Packet: How Many?
**Module:** how-many | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 142
> Досліди, скількома 
> способами 
> можна 
> прочитати числовий 
> вираз.
> Я — дослідник
> Я — дослідниця
> Навчаюся читати числові вирази
> 70 + 25
> 80 – 25
> Сума чисел сімдесят і двадцять  
> п’ять.
> Сімдесят збільшити на двадцять  
> п’ять.
> Перший доданок сімдесят, другий — 
> двадцять п’ять.
> До сімдесяти додати двадцять п’ять.
> Різниця чисел вісімдесят і двадцять п’ять.
> Вісімдесят зменшити на двадцять п’ять.
> Зменшуване вісімдесят, від’ємник —  
> двадцять п’ять.
> Від вісімдесяти відняти двадцять п’ять.
> Правильно утворюй форми числівників і вимовляй їх: 
> сімдесяти, вісімдесяти.
> 	 	
> 9   Прочитайте кожен числовий вираз різними способами.
> 	 	
> 10   Розв’яжи задачу. Склади і запиши числові вирази на додавання.
> 	 	
> 11   Прочитай і розв’яжи задачу. Запиши розв’язок.

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 28
> **Score:** 0.33
>
> 26
> — З днем народження вітаю! —
> Друзі кажуть і близькі.
> Із захопленням відповідаю:
> — Дякую! Люблю вас всіх!
>                                                            Євгенія Крук
> Мій день народження
> 	 Який подарунок на день народження ти очікуєш?
> 	 Скільки на малюнку дів­чаток?
> — Дві дівчинки.
> 	 Ти створив / створила речення.
> Речення — це закінчена думка. Речення скла-
> дається зі слів. У ньому позначаємо кожне сло-
> во так, як показано нижче. 
> Дівчинка: 
>   (перше слово речення). 
> Дві дівчинки: 
>  . 
> Дівчинка з друзями:  
> .
> 	 Розглянь малюнки.

## Числа 1-20 (Numbers 1-20)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 140
> **Score:** 0.50
>
> 140
> Вимова і правопис найуживаніших 
> числівників
> Вивчаю числівники 5, 9, 11–20, 30, 50, 60, 70, 80
> 44
> Правильно наголошуй числівники!
> одинадцять
> дванадцять
> тринадцять
> чотирнадцять
> п’ятнадцять
> шістнадцять
> сімнадцять
> вісімнадцять
> дев’ятнадцять
> двадцять
> тридцять
> п’ятдесят
> шістдесят
> сімдесят
> вісімдесят
> 	 	
> 1   Назвіть числа і запишіть числівники. Поставте наголос у словах.
> 	 	
> 3   Утворіть від слів п’ять, шість, сім, 
> вісім, дев’ять нові числівники за 
> зразком. Поставте наголос у словах.
> 2   Запиши повні відповіді на запитання.
> 1 дес. 1 од. 
> 1 дес. 2 од.
> 1 дес. 3 од.
> Скільки дівчаток у вашому класі?
> Скільки хлопчиків?
> Скільки загалом дітей у вашому класі?
> 1 дес. 4 од. 
> 1 дес. 5 од. 
> 1 дес. 6 од.
> 1 дес. 7 од.
> 1 дес. 8 од.
> 1 дес.

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 105
> **Score:** 0.50
>
> 103
> 	
> Визнач, що не так на малюнку.
> 	 Хто один, а кого на малюнку зображено бага-
> то?
> 	 Вимов слова — назви намальованих пред-
> метів, у яких є ь.
> Апельсин      _____ ,   ______ ,     _______ ,    ______.
> 12345678      6 7 8       2 3 8 5        6 1 8 7       4 7 2 1
> 	 Утвори нові слова. Запиши.
> 	
> Поміркуй, хто куди спішить.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 92
> **Score:** 0.25
>
> 92
> 331. 1.	 Поміркуй, як за допомогою числівників Кирилко заши-
> фрував слова.
> 2.	 Прочитай та запиши утворені слова. Підкресли слова, близькі 
> за значенням.
> 332. 1.	 Прочитай лічилку. Згадай, коли та як її промовляють.
> Лічилка-безконечка
> Один і два — росла трава,
> три, чотири — покосили,
> п’ять — на сонечку сушили,
> шість — в копичку поскладали,
> сім — корівку годували,
> вісім — молочко давала,
> дев’ять — діток напувала,
> десять — привела телятко.
> Починаймо все спочатку! 
> Один і два — росла трава…  (Леся Вознюк)
> 329. 1.	 Відгадай загадки. Знайди слова, які відповідають на питання 
> скільки?
> 1. Два скельця, три дужки — на ніс і на вушка. 2. П’ять 
> комірчин, а одні двері. 3. Деревце — не полінце; шість дірочок 
> має, весело співає.

## Десятки і сотні (Tens and Hundreds)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 140
> **Score:** 0.33
>
> 140
> Вимова і правопис найуживаніших 
> числівників
> Вивчаю числівники 5, 9, 11–20, 30, 50, 60, 70, 80
> 44
> Правильно наголошуй числівники!
> одинадцять
> дванадцять
> тринадцять
> чотирнадцять
> п’ятнадцять
> шістнадцять
> сімнадцять
> вісімнадцять
> дев’ятнадцять
> двадцять
> тридцять
> п’ятдесят
> шістдесят
> сімдесят
> вісімдесят
> 	 	
> 1   Назвіть числа і запишіть числівники. Поставте наголос у словах.
> 	 	
> 3   Утворіть від слів п’ять, шість, сім, 
> вісім, дев’ять нові числівники за 
> зразком. Поставте наголос у словах.
> 2   Запиши повні відповіді на запитання.
> 1 дес. 1 од. 
> 1 дес. 2 од.
> 1 дес. 3 од.
> Скільки дівчаток у вашому класі?
> Скільки хлопчиків?
> Скільки загалом дітей у вашому класі?
> 1 дес. 4 од. 
> 1 дес. 5 од. 
> 1 дес. 6 од.
> 1 дес. 7 од.
> 1 дес. 8 од.
> 1 дес.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 142
> Досліди, скількома 
> способами 
> можна 
> прочитати числовий 
> вираз.
> Я — дослідник
> Я — дослідниця
> Навчаюся читати числові вирази
> 70 + 25
> 80 – 25
> Сума чисел сімдесят і двадцять  
> п’ять.
> Сімдесят збільшити на двадцять  
> п’ять.
> Перший доданок сімдесят, другий — 
> двадцять п’ять.
> До сімдесяти додати двадцять п’ять.
> Різниця чисел вісімдесят і двадцять п’ять.
> Вісімдесят зменшити на двадцять п’ять.
> Зменшуване вісімдесят, від’ємник —  
> двадцять п’ять.
> Від вісімдесяти відняти двадцять п’ять.
> Правильно утворюй форми числівників і вимовляй їх: 
> сімдесяти, вісімдесяти.
> 	 	
> 9   Прочитайте кожен числовий вираз різними способами.
> 	 	
> 10   Розв’яжи задачу. Склади і запиши числові вирази на додавання.
> 	 	
> 11   Прочитай і розв’яжи задачу. Запиши розв’язок.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 94
> **Score:** 0.50
>
> 94
> 1. (Скільки?) … разів відміряй, (скільки?) … раз відріж. 
> 2. (Скільки?) …  літо краще, як (скільки?)  …  зим. 3. (Скільки?) 
> … голова добре, а (скільки?) … — краще. 
> Слова для довідки: одна, один, одне, сім, дві, сто.
> 2.	 Запишіть одне прислів’я (на вибір). Підкресліть числівник 
> з іменником. 
> 337. 1.	 Розглянь малюнки. З яких казок зображені герої?
> 2.	 Склади речення за двома малюнками (на вибір). Уживай 
> числівники.
> 338. 1.	 Дай відповіді на запитання двома словами.
> Скільки м’ячів? Скільки скакалок? Скільки олівців? 
> Скільки книг?
> 2.	 Запиши утворені сполучення слів. 
> 336. 1.	 Прочитайте прислів’я та вставте пропущені числів-
> ники. За потреби користуйтеся словами для довідки.

## Підсумок — Summary

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 142
> Досліди, скількома 
> способами 
> можна 
> прочитати числовий 
> вираз.
> Я — дослідник
> Я — дослідниця
> Навчаюся читати числові вирази
> 70 + 25
> 80 – 25
> Сума чисел сімдесят і двадцять  
> п’ять.
> Сімдесят збільшити на двадцять  
> п’ять.
> Перший доданок сімдесят, другий — 
> двадцять п’ять.
> До сімдесяти додати двадцять п’ять.
> Різниця чисел вісімдесят і двадцять п’ять.
> Вісімдесят зменшити на двадцять п’ять.
> Зменшуване вісімдесят, від’ємник —  
> двадцять п’ять.
> Від вісімдесяти відняти двадцять п’ять.
> Правильно утворюй форми числівників і вимовляй їх: 
> сімдесяти, вісімдесяти.
> 	 	
> 9   Прочитайте кожен числовий вираз різними способами.
> 	 	
> 10   Розв’яжи задачу. Склади і запиши числові вирази на додавання.
> 	 	
> 11   Прочитай і розв’яжи задачу. Запиши розв’язок.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 140
> **Score:** 0.33
>
> 140
> Вимова і правопис найуживаніших 
> числівників
> Вивчаю числівники 5, 9, 11–20, 30, 50, 60, 70, 80
> 44
> Правильно наголошуй числівники!
> одинадцять
> дванадцять
> тринадцять
> чотирнадцять
> п’ятнадцять
> шістнадцять
> сімнадцять
> вісімнадцять
> дев’ятнадцять
> двадцять
> тридцять
> п’ятдесят
> шістдесят
> сімдесят
> вісімдесят
> 	 	
> 1   Назвіть числа і запишіть числівники. Поставте наголос у сло

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Числа 1-20 (Numbers 1-20)` (~300 words)
- `## Десятки і сотні (Tens and Hundreds)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

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
  1. **At a bakery — ordering bread, pastries, and cakes for a family gathering. Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні. Ask: Скільки коштує торт? А три булочки?**
     Speakers: Покупець, Пекар (baker)
     Why: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
  2. **Counting items in a school backpack before class — ручка (f, pen), олівець (m, pencil), зошит (m, notebook), підручник (m, textbook).**
     Speakers: Учень (student), Мама
     Why: Numbers with school supplies: один олівець, дві ручки, п'ять зошитів

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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary

**Required:** один, два, три, чотири, п'ять (1-5), шість, сім, вісім, дев'ять, десять (6-10), двадцять, тридцять, сорок (20, 30, 40), сто, тисяча (100, 1000), скільки (how many/how much), коштує (costs — from коштувати), гривня (hryvnia — Ukrainian currency), рік, роки, років (year/years — age chunks)
**Recommended:** п'ятдесят, шістдесят, сімдесят (50, 60, 70), вісімдесят, дев'яносто (80, 90), двісті, триста, п'ятсот (200, 300, 500), копійка (kopek), номер (number — phone/room), нуль (zero)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



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
## Діалоги (Dialogues) (~330 words total)

- D1 (~110 words): Bakery dialogue — Покупець asks Пекар about prices. 6 turns: Скільки коштує торт? — Двісті гривень. А хліб? — П'ятнадцять гривень. А три булочки? — Сорок п'ять гривень. А одне тістечко? — Двадцять гривень. Introduces один хліб (m), одна булочка (f), одне тістечко (n) — one-line inline gloss per noun gender. Final line: Дякую, до побачення!
- P1 (~40 words): Bridging commentary — point out скільки коштує? as the key question pattern. Highlight the three nouns from the dialogue (торт/хліб/тістечко) as recycled vocabulary from M08-M09. Note: noun endings after numbers will be explained in A2 — for now, memorize as chunks.
- D2 (~110 words): Age exchange — student Оленка meets new classmate Тарас at school. 6 turns: Скільки тобі років? — Мені чотирнадцять. А тобі? — Мені тринадцять. А твоя сестра старша? — Так, їй вісімнадцять. А твій брат? — Йому одинадцять. Introduces Мені/тобі/йому/їй + number + років as memorized chunks with English gloss "I am / you are / he is / she is [age]."
- P2 (~40 words): Brief note — Мені X років uses three different number-noun combos (рік, роки, років). At A1 we memorize: 1 рік, 2–4 роки, 5+ років. No case grammar — pure pattern recognition. Frame as a Ukrainian "age formula."
- Exercise (~30 words overhead): **Quiz** — "How old are they?" Match 6 cartoon faces with caption ages (11, 13, 18, 22, 35, 47) to spoken Ukrainian sentences. 6 items.

---

## Числа 1–20 (Numbers 1–20) (~330 words total)

- P1 (~100 words): Numbers 1–10 — full list: один, два, три, чотири, п'ять, шість, сім, вісім, дев'ять, десять. Pronunciation warnings for three tricky ones: (a) п'ять — apostrophe softens п before я, sounds like "p-yat'"; (b) сім — NOT "сем" (Russian ghost); (c) дев'ять — apostrophe again, two syllables "dev-yat'." Practice frame: count items from M08 classroom — один стіл, два стільці, три книги, чотири ручки, п'ять зошитів. Numbers come first, nouns are recycled vocabulary.
- P2 (~120 words): Numbers 11–20 — full list from Vashulenko Grade 3 p.140: одинадцять, дванадцять, тринадцять, чотирнадцять, п'ятнадцять, шістнадцять, сімнадцять, вісімнадцять, дев'ятнадцять, двадцять. Pattern explanation: base number + -надцять (parallel to English "-teen"). Stress rule from textbook: the stress ALWAYS falls on the -на- syllable in -надцять (одинáдцять, дванáдцять, тринáдцять — mark stresses explicitly). One spelling trap: шістнадцять not "шістьнадцять." Counting rhyme from Kravcova Grade 2 p.92: "Один і два — росла трава, три, чотири — покосили…" — gives 1–7 in context.
- P3 (~80 words): Productive practice frame — two ways to use 1–20 right now. (1) Count real objects around you: скільки стільців у кімнаті? скільки книжок на столі? (2) Answer age questions: Мені + number + років. Prompt learner to say their own age, their sibling's age, a friend's age — all with numbers from this section. Anticipation note: combined numbers (двадцять один, тридцять п'ять) come in the next section.
- Exercise (~30 words overhead): **Fill-in** — "Write the number in words": 11 → \_\_\_, 15 → \_\_\_, 18 → \_\_\_, 19 → \_\_\_, 20 → \_\_\_. Also 6 → \_\_\_, 9 → \_\_\_, 7 → \_\_\_. 8 items.

---

## Десятки і сотні (Tens and Hundreds) (~330 words total)

- P1 (~120 words): Tens 20–100 — list from Vashulenko p.140 plus the two irregulars: двадцять (20), тридцять (30), **сорок** (40 — NOT "чотиридесят"; это irregularne, memorize it!), п'ятдесят (50), шістдесят (60), сімдесят (70), вісімдесят (80), **дев'яносто** (90 — NOT "дев'ятдесят"; another irregular). сто (100). Stress tip from Vashulenko p.142: вимовляй правильно — сімдесяти, вісімдесяти (genitive forms used in math); at A1 we only need nominative. Combined numbers = tens + unit, no connector word: двадцять один (21), тридцять п'ять (35), сорок сім (47), вісімдесят дев'ять (89). Three practice examples with items: двадцять три студенти, сорок вісім гривень, дев'яносто дві копійки.
- P2 (~120 words): Hundreds for prices — сто (100), двісті (200), триста (300), чотириста (400), п'ятсот (500), шістсот (600), сімсот (700), вісімсот (800), дев'ятсот (900), тисяча (1000). Note the pattern shift at 200: двісті (not "двасто"). At 300–400: триста/чотириста (not "три сто"). At 500–900: -сот suffix. Practice with гривня: одна гривня (1), дві гривні (2–4), п'ять гривень (5+). Memorize three price chunks from Dialogue 1: п'ятнадцять гривень (15₴), двісті гривень (200₴), сорок п'ять гривень (45₴). The noun changes гривня/гривні/гривень are learned here as price chunks — case grammar arrives in A2.
- P3 (~60 words): Phone number pattern — Ukrainian mobiles: 0XX XXX XX XX. Break into groups for easier recall: нуль дев'яносто сім (097) — пауза — три два один (321) — пауза — сорок п'ять (45) — пауза — шістдесят сім (67). Read each group as a sub-number. Sample: Мій номер — нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім.
- Exercise 1 (~30 words overhead): **Quiz** — "Скільки коштує?" Match 8 price tags (15₴, 47₴, 200₴, 350₴, 99₴, 500₴, 1000₴, 75₴) to spoken Ukrainian. 8 items.
- Exercise 2 (~30 words overhead): **Fill-in** — Complete the phone number dictation. Hear 4 Ukrainian phone numbers in XXX-XXX-XX-XX format; write the missing groups in words. 4 items.

---

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Recap of the three number systems built in this module — (1) cardinal 1–20 with two apostrophe rules and the -надцять pattern; (2) tens with the two irregulars сорок and дев'яносто; (3) hundreds with the двісті shift and тисяча. Emphasize: combined numbers never need a connector — двадцять три, сто сорок п'ять. All three systems feed directly into the three practical applications below.
- P2 (~60 words): Practical use #1 — **Prices.** Question: Скільки коштує [noun]? Answer: [number] гривень/гривні/гривня. Three memorized frames: 15 гривень (хліб), 45 гривень (три булочки), 200 гривень (торт). Students can now ask and answer any price up to 1000₴ using vocabulary they already know.
- P3 (~60 words): Practical use #2 — **Age.** Question: Скільки тобі/йому/їй років? Answer: Мені/Йому/Їй [number] рік / роки / років. Three memorized frames: Мені чотирнадцять років (14), Йому двадцять два роки (22), Їй тридцять п'ять років (35). The rік/роки/років switch is a chunk — feel it, not analyze it.
- P4 (~60 words): Practical use #3 — **Phone numbers.** Pattern: read in groups of 3–2–2–2. Practice with three sample numbers: (a) 097-321-45-67; (b) 050-112-33-99; (c) 073-456-78-10. Learner should be able to dictate their own number in Ukrainian. Link to Dialogue 1 context: bakery could call you when your cake is ready — Мій номер телефону...
- Self-check (~70 words): Bulleted Q&A:
  - Як сказати 17 по-українськи? → сімнадцять
  - Як сказати 40 по-українськи? → сорок (не "чотиридесять"!)
  - Як сказати 90 по-українськи? → дев'яносто (не "дев'ятдесять"!)
  - Скільки коштує торт, якщо торт коштує 250 гривень? → Двісті п'ятдесят гривень.
  - Скажіть своє ім'я і вік: Мене звати \_\_\_, мені \_\_\_ років.
  - Продиктуйте свій номер телефону по-українськи.

Grand total: ~1320 words
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
