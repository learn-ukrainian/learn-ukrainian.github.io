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

Write the full prose content for module **35: Checkpoint: Places** (A1, A1.5 [Places]).

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
module: a1-035
level: A1
sequence: 35
slug: checkpoint-places
version: '1.2'
title: 'Checkpoint: Places'
subtitle: Can you navigate a Ukrainian city?
focus: review
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Demonstrate correct use of euphony (у/в, і/й, з/із/зі)
- Use locative for location (Де?) and accusative for direction (Куди?)
- Navigate using city vocabulary, transport, and directions
- Answer Звідки? with genitive chunks
- Combine all A1.5 skills in connected urban scenarios
dialogue_situations:
- setting: 'Video-calling a friend while walking through Одеса (Odesa) — showing:
    Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), порт (m,
    port), пляж (m, beach). Describing where you are, where you''re going.'
  speakers:
  - Мешканець (filming)
  - Онлайн-друг (watching)
  motivation: Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M28-M34: Can you apply euphony rules? (M28) Can you say where
    things are? (M29) Can you name city places? (M30) Can you say where you''re going?
    (M31) Can you use transport? (M32) Can you give directions? (M33) Can you say
    where you''re from? (M34)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M28-M34. Content: a tourist navigates
    Kyiv — asks for directions, takes metro, finds a museum, describes where they''re
    from and where they''re going. Uses euphony, locative, accusative, genitive chunks,
    transport.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.5: 1. Euphony: у/в, і/й, з/із/зі (M28) 2. Де? → в/на + locative:
    в школі, на роботі (M29) 3. Куди? → в/на + accusative: у школу, на роботу (M31)
    4. Звідки? → з + genitive chunk: з України, з роботи (M34) 5. Transport: автобусом,
    на метро (M32) 6. Directions: прямо, направо, наліво (M33) 7. City places with
    correct prepositions (M30)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A tourist in Kyiv asks for help: — Вибачте, я з Канади. Де тут музей? — Музей
    у центрі. Ідіть на метро до станції Хрещатик. — А як дістатися від метро? — Вийдіть
    і йдіть направо. Музей на площі. — Дякую! А потім я хочу їхати у Львів. Де вокзал?
    — Вокзал далеко, їдьте на метро до станції Вокзальна. Uses all A1.5 skills in
    one realistic scenario.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.5 achievement summary: You can now navigate Ukrainian cities. You know euphony
    rules for natural speech. You can say WHERE something is (locative). You can say
    WHERE you''re GOING (accusative). You can say WHERE you''re FROM (genitive chunks).
    You can use transport and give directions. Next: A1.6 — Food and Shopping (ordering,
    buying, accusative for objects).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Choose the correct question: Де? Куди? Звідки?'
  items: 8
  questions:
  - '... ти живеш? — У Києві. (Де / Куди / Звідки)'
  - '... ти йдеш? — У магазин. (Куди / Де / Звідки)'
  - '... ви? — Ми з Канади. (Звідки / Де / Куди)'
  - '... музей? — У центрі. (Де / Куди / Звідки)'
  - '... їде автобус? — На вокзал. (Куди / Де / Звідки)'
  - '... ти їдеш? — З роботи. (Звідки / Куди / Де)'
  - '... аптека? — Направо. (Де / Куди / Звідки)'
  - '... вони? — Зі США. (Звідки / Де / Куди)'
- type: fill-in
  focus: Complete the connected dialogue with correct forms
  items: 6
  blanks:
  - Вибачте, я {з Канади}. Де тут музей?
  - Музей {у центрі}. Ідіть на метро.
  - А як дістатися {від метро}?
  - Вийдіть і йдіть {направо}. Музей на площі.
  - Я хочу їхати {у Львів}. Де вокзал?
  - Вокзал далеко, їдьте {на метро}.
- type: group-sort
  focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks)
  items: 9
  groups:
  - name: Локація (Де?)
    items:
    - у школі
    - на площі
    - в центрі
  - name: Напрямок (Куди?)
    items:
    - на роботу
    - у Львів
    - в Канаду
  - name: Походження (Звідки?)
    items:
    - з України
    - зі США
    - з роботи
- type: quiz
  focus: 'Euphony rules check: у/в, і/й, з/із/зі'
  items: 8
  questions:
  - Брат ... сестра (і / й)
  - Вона живе ... Львові (у / в)
  - Я йду ... школи (зі / з)
  - Він ... Києві (у / в)
  - Мама ... тато (і / й)
  - Ми ... України (з / із)
  - Я ... кімнаті (в / у)
  - Вона ... США (зі / з)
connects_to:
- a1-036 (Food and Drink)
prerequisites:
- a1-034 (Where From?)
grammar:
- 'Review: locative for location (Де?)'
- 'Review: accusative for direction (Куди?)'
- 'Review: genitive chunks for origin (Звідки?)'
- 'Review: euphony and transport'
register: розмовний
references:
- title: Synthesis of M28-M34 content
  notes: No new material — review and integration of A1.5 phase.

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

**Batch 1** — Place nouns & proper names:
- ✅ музей (noun)
- ✅ площа (noun)
- ✅ вокзал (noun)
- ✅ центр (noun)
- ✅ школа (noun)
- ✅ робота (noun) — note: VESUM also returns робот; робота confirmed separately ✅
- ✅ метро (noun)
- ✅ автобус (noun)
- ✅ станція (noun)
- ✅ Хрещатик (proper noun)

**Batch 2** — Directional adverbs & movement verbs:
- ✅ прямо (adv)
- ✅ направо (adv, lemma: направо)
- ✅ наліво (adv)
- ✅ тут (adv)
- ✅ далеко (adv)
- ✅ вийдіть (verb form → вийти)
- ✅ йдіть (verb form → йти)
- ✅ їдьте (verb form → їхати)
- ✅ їхати (verb)
- ✅ іти (verb)

**Batch 3** — Dialogue & support vocabulary:
- ✅ вибачте (verb form → вибачити)
- ✅ дякую (verb form → дякувати)
- ✅ турист (noun)
- ✅ зупинка (noun)
- ✅ транспорт (noun)
- ✅ ліворуч (adv)
- ✅ праворуч (adv)
- ✅ автобусом (instrumental form → автобус)
- ✅ перехід (noun)
- ✅ вулиця (noun)

**Not found:** none — all 30 words confirmed in VESUM.

---

## Textbook Excerpts

### Section: Граматика — Euphony (у/в, і/й, з/із/зі)
> "Чергування у–в та і–й забезпечує милозвучність мови. Завдяки йому уникаємо незручних для вимови збігів голосних і приголосних звуків. [...] у між приголосними: він у домі, брат умивається; в між голосними: риба в акваріумі."
>
> Source: Авраменко, Grade 6, tier 1 (NUS 2022+) — §23 Чергування у–в та і–й

> "З — між двома буквами, перша з яких позначає голосний, а друга — приголосний: з любов'ю. ЗІ — якщо буквосполучення наступного слова має початкові з, с, ш, щ: зі школи, зі Львова, зі святом. ІЗ — перед свистячими та шиплячими: із золота, із шовку."
>
> Source: Літвінова, Grade 5, tier 1 (NUS 2022+) — §Чергування З/ЗІ/ІЗ

### Section: Граматика — Де? Locative / Куди? Accusative / transport prepositions
> "Прийменник на вживають з назвами установ, приміщень: **станція, вокзал, пошта** → піти на пошту, приїхати на вокзал, забігти на станцію. З рештою просторових іменників і географічних назв уживають прийменник **в (у)** (і до): приїхати в Україну, зайти в школу (і до школи), потрапити в Париж (і до Парижа)."
>
> Source: Авраменко, Grade 11, tier 2 — Прийменники в і на з географічними назвами

> ⚠️ **Critical pedagogical note for module writer:** The plan's grammar summary says "в школі, на роботі." This is correct — but the plan's dialogue uses "до станції Хрещатик" (correct! до + genitive for destination) and "на площі" (correct! на + locative for place). HOWEVER, the pattern needs to explicitly teach: transport hubs (станція, вокзал, зупинка) take **на**: на станції, на вокзалі — NOT в станції, в вокзалі.

### Section: Читання / Transport & City Places vocabulary
> "У містах є музеї, театри, супермаркети. Вулицями міст їздять тролейбуси, трамваї, автобуси, маршрутні таксі." Wordlist illustrated: **вулиця, парк, метро, площа, супермаркет.**
>
> Source: Большакова, Grade 1 (Буквар), tier 2 — p.16, letter М/м

### Section: Діалог — Movement verbs in imperative (вийдіть, йдіть, їдьте)
> "Зразок. Пам'ятаю – пам'ятай, пам'ятаймо, пам'ятайте, хай пам'ятає, хай пам'ятають." [imperative paradigm]. "Написати у формі спонукальних речень п'ять правил поведінки на дорозі."
>
> Source: Заболотний, Grade 7, tier 1 (NUS 2022+) — p.74, Наказовий спосіб

---

## Grammar Rules

- **у/в alternation:** Правопис §23 — У вживаємо між приголосними (він у домі), на початку речення перед приголосним (У лісі), перед в, ф, льв, хв (у Львові, у вагоні). В вживаємо між голосними (риба в акваріумі), після голосного перед приголосним (пішла в садок).

- **і/й alternation:** Правопис §24 — І вживаємо між приголосними (брат і сестра), на початку речення перед приголосним, при зіставленні понять (батьки і діти), перед й/є/ї/ю/я. Й вживаємо між голосними (Ольга й Андрій), між голосним і приголосним.

- **з/із/зі:** Правопис §25 — З перед голосним на початку речення (З одним рибалкою) і перед більшістю приголосних. ІЗ перед свистячими/шиплячими (із школи, із золота). ЗІ перед словами, що починаються з з, с, ш, щ (зі Львова, зі школи, зі святом). ЗО тільки з два, три, мною (зо дві сотні; зо мною).

- **в/на + locative (Де?):** Авраменко Grade 11 — Транспортні вузли (станція, вокзал, зупинка) → **на**: на станції, на вокзалі. Школа, університет, місто → **в/у**: в школі, у місті.

---

## Calque Warnings

- **"їхати у Львів"** (dialogue): ⚠️ POTENTIAL CALQUE — Антоненко-Давидович (ad-219): "коли мовиться про рух у напрямі міста, тоді треба ставити прийменник **до**: поїхати **до** Москви." The correct form for "going to Lviv" (direction) is **"їхати до Львова"** (до + genitive). The plan dialogue uses "хочу їхати у Львів" — this is influenced by the Russian "ехать в Львов." Note: Авраменко (Grade 11) allows both "в Київ" і "до Київа" for cities, so this is not outright wrong, but "до Львова" is the more natural, stylistically preferred Ukrainian form. **Recommendation:** change to "хочу їхати до Львова" in the dialogue.

- **"направо/наліво"** — OK. These are confirmed native Ukrainian adverbs (A1 in PULS). No calque issue. Style guide check returned no warnings for these terms.

- **"дістатися"** (як дістатися?) — OK. "Як дістатися до...?" is authentic Ukrainian for "How do I get to...?" Style guide check returned no calque warning. This is natural Ukrainian.

---

## CEFR Check

- музей: **A1** ✅ — appropriate
- вокзал: **A1** ✅ — appropriate
- метро: **A1** ✅ — appropriate
- транспорт: **A1** ✅ — appropriate
- площа: **A1** ✅ — appropriate
- станція: **A1** ✅ — appropriate
- направо: **A1** ✅ — appropriate
- наліво: **A1** ✅ — appropriate
- прямо: **A1** ✅ — appropriate
- центр: **A1** ✅ — appropriate

⚠️ **Level note:** PULS lists **ліворуч** (A2) and **праворуч** (A2) as higher-register synonyms of наліво/направо. The plan correctly uses направо/наліво (A1). If the module writer includes ліворуч/праворуч as alternatives, these should be labeled as "also used" rather than primary A1 vocabulary.
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
# Verified Knowledge Packet: Checkpoint: Places
**Module:** checkpoint-places | **Phase:** A1.5 [Places]
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

> **Source:** savchenko, Grade 4
> **Section:** Сторінка 157
> **Score:** 0.50
>
> 157
> ЗМICТ
> ЧИТАЄМО Й РОЗПОВІДАЄМО
> ПРО СВОЇ ЗАХОПЛЕННЯ
> Ліна Костенко. Вже брами літа замикає осінь…  . . . . . . . . . . . . . . . 5
> Олександра Савченко. Як читають книжки? . . . . . . . . . . . . . . . . . . 6
> Марія Манеру. Читач Максимко . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7 
> ВЕСЕЛЕ СЛОВО. Василь Марсюк. Диктант . . . . . . . . . . . . . . . . . . . 8
> Медіавіконце: види і джерела інформації . . . . . . . . . . . . . . . . . 9
> Давид Гуліа. Розум, знання і сила . . . . . . . . . . . . . . . . . . . . . . . . . . 10
> ПРАГНЕМО ЗРОЗУМІТИ СВОЇХ ПРЕДКІВ
> Як ще не було початку світа… 
> (Українська народна обрядова пісня) . . . . . . . . . . . . . . . . . . . . . . . 13
> Створення світу (За єгипетськими міфами). Переповіла Ольга Бондарук . . . . . . . . . . . . . . . . . . . . .

> **Source:** kovalenko, Grade 6
> **Section:** Сторінка 257
> **Score:** 0.50
>
> 1
> Правила  читання
> 1
> Першочергово у тексті твору шукай відповіді 
> на запитання:
> • Хто діє? Які його / її вчинки?
> • Де і коли відбуваються події?
> • Кого або що описує автор/авторка?
> 2
>  
> При повторному читанні:
> 1. Виділи деталі в тексті (портреті, пейзажі, 
> описі предмета чи приміщення).
> 2. Проаналізуй, яку роль вона відіграє:
> • у портреті: передає зовнішню 
> характеристику чи звертає увагу на 
> внутрішні якості героя / героїні;
> • у пейзажі: відтворює різноманітні стани 
> природи чи внутрішній стан героя / героїні;
> • в інтер’єрі: описує вигляд предмета чи 
> приміщення або через деталь допомагає 
> зрозуміти звички й уподобання 
> героя/героїні.
> 3. Поміркуй, як деталь пов’язана з попередніми 
> епізодами.
> 4.

## Граматика (Grammar Summary)

## Діалог (Connected Dialogue)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 120
> **Score:** 0.50
>
> 120
> ЖИВИЛЬНІ  ДЖЕРЕЛА  МУДРИХ  КНИЖОК
> — Тю, — ледве сказав Ява.
> — Тьху, — ледве сказав я. 
> Це вся розмова, на яку ми спро­моглися.
> І тільки за хвилин двадцять ми нарешті отямились і змогли обміняти-
> ся думками з приводу того, що сталося.
> — Так ... — зітхнув Ява. — Можна сказати, зіпсував ти мені кар’єру. 
> А що?! Хто ж мене тепер у міліцію візьме...
>  
> 1.	 Хрещатик «утикається» на Європейській площі в
> А	 метро «Арсенальна»
> Б	 метро «Хрещатик»
> В	   колишній костел
> Г	   філармонію
> 2.	 	Репліка «Лізь, голубе, під землю, як усі люди» адресована
> А	 інтелігентному дідусеві 
> Б	 опасистому дядьку
> В  	міліціонерові
> Г  	 інтуристу
> 3.	 Установіть відповідність.
> Ге­рой по­віс­ті
> Опис зов­ніш­нос­ті 
> 1	 мі­лі­ці­о­нер
> 2	 дядь­ко  в мет­ро
> 3	 ін­ту­рист	
> А	 «...

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 126
> **Score:** 0.25
>
> Розділ 5. Іменник 
> 126
> Пирогів варто відвідати в пе-
> ріод релігійних свят — Різдва, 
> Великодня, 
> Івана 
> Купала 
> чи 
> Спаса, адже в цей час у музеї 
> проходять 
> надзвичайно 
> цікаві 
> й  колоритні дійства.
> Дістатися до музею можна ав-
> тобусом № 27 від станції метро 
> «Либідська».
>  (За матеріалами туристичного 
> порталу «IGotoWorld»)
> 2. Випишіть із тексту власні назви, поясніть їхній правопис. Над кожною 
> назвою надпишіть номер правила, яке регулює написання великої лі-
> тери (за правилами на с. 123—124).
> 3. Випишіть у  словничок незнайомі вам слова.
> 4. Сформулюйте основну думку тексту. Запишіть ключові слова — теги, 
> за якими би ви шукали інформацію про музей в  інтернеті. Стисло пе-
> рекажіть текст так, щоб розповідь могла зацікавити ваших друзів чи 
> подруг.
> 5.

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

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 107
> **Score:** 0.50
>
> 107
> ТВОРИ НА ІСТОРИЧНУ ТЕМАТИКУ
> – Хто я такий, питаєте? – і кивнув на хлопців, що зніче-
> но переминалися з ноги на ногу. – Ото в них краще 
> поцікавтесь. Вони, бач, гадають, що я якийсь Тишкевич. 
> А я того Тишкевича і в очі не бачив. Мені треба до Демида, 
> товариша мого давнього. Чули про такого?
> Василь Байлемів замислився.
> – Здається, чув. Тільки він далеко звідсіля. Десь внизу 
> оселився, і не на острові, а в плавнях... То ти таки не Тиш-
> кевич?
> – І не був ніколи. Я Семен Задорожний із Байбузівки, 
> є таке село за Черкасами. Може, чули? Ну от. Вирішили 
> ми з друзями моїми до Демида дістатися, теж трохи поко-
> закувати. От. А сюди я зайшов, аби запитати, де той бісів 
> Демид оселився цього літа.
> – А хутро хто брав? – запитав Грицик.
> – Яке хутро? – здивувався в’язень.

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 33
> **Score:** 0.33
>
> 33
> Мої навчальні досягнення
> Карта пам’яті: від тексту — до мене
> Прочитайте текст.
> Був ясний осінній день. У по-
> вітрі пливли тоненькі павутинки. 
> Д..рева скидали золоті л..стки. 
> Високо в небі з’явився ключ жу-
> равлів. Вони приземлилися на 
> лузі, немов радилися. Старий ле-
> лека злітав, кружляв у небі й знову 
> прилітав до родичів. Беззахисні 
> молоді лелеки вперше летять у 
> теплий край. У теплий, але чужий 
> край. Бо Батьківщина там, де на-
> родився, зріс і почав літати (За 
> В. Сухомлинським).
> Зміст
> 1.	 Де й коли відбуваються події?
> 2.	Куди вирушають журавлі?
> Префікси
> 1. Випиши два слова з префіксом при-. Познач його.
> 2. Випиши слово з апострофом після префікса.
> 3. Випиши слово з подвоєнням приголосних на 
> межі префікса та кореня.
> 4. Випиши слово з префіксом з-.
> Суфікси
> 1.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Співвідношення звуків і букв
> **Source:** МійКлас — [Співвідношення звуків і букв](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/spivvidnoshennia-zvukiv-i-bukv-41281)

### Теорія:

*www.ua.pistacja.tv*  
 
Як ти вже знаєш, в українській мові є  38  **звуків** і 33  **літери** для передачі цих звуків на письмі.
Чому така різниця між кількістю звуків і букв?
Деякі букви \(я, ю, є\) позначають **два** звуки у певних позиціях.

Букви ї, щ завж

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~300 words)
- `## Підсумок — Summary` (~250 words)
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
  1. **Video-calling a friend while walking through Одеса (Odesa) — showing: Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), порт (m, port), пляж (m, beach). Describing where you are, where you're going.**
     Speakers: Мешканець (filming), Онлайн-друг (watching)
     Why: Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)

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

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
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
- P1 (~60 words): Opening self-check framing — "You've covered 7 modules in A1.5. Before moving forward, let's see what you can do." Present a checklist-style intro: Can you apply euphony? Can you say where things are? Can you say where you're going? Can you say where you're from? Can you name city places and transport?
- P2 (~80 words): Quick self-check questions in Q&A format — learner tests themselves: (1) Де ти живеш? — У Києві. (2) Куди ти йдеш? — У магазин. (3) Звідки ти? — Я з Канади. (4) Як ти їдеш? — Автобусом. (5) Де музей? — Музей у центрі. (6) Скажи: "і" чи "й"? Брат ___ сестра. (7) Скажи: "у" чи "в"? Я живу ___ Львові.
- P3 (~80 words): Encouragement + orientation — "If these feel natural, you're ready. If some felt tricky, this checkpoint will help you see the full picture. We'll review all the patterns together — euphony (M28), location (M29), city vocabulary (M30), direction (M31), transport (M32), directions (M33), and origin (M34) — in one connected practice."

## Читання (~280 words total)
- P1 (~40 words): Setup — "Read this short text about a tourist navigating Kyiv. Notice how all the A1.5 patterns appear together in natural Ukrainian."
- P2 (~200 words): Reading text — tourist narrative in Ukrainian:
  «Мене звати Томас. Я з Канади, але зараз я у Києві.
  Сьогодні я хочу побачити місто. Вранці я їду на метро до станції Хрещатик. Метро у Києві дуже зручне.
  Я виходжу зі станції й іду направо. Попереду — Хрещатик, головна вулиця міста. Я йду прямо і бачу красивий парк. У парку є фонтани й лавки.
  Потім я питаю перехожого: "Вибачте, де Національний музей?" Він відповідає: "Музей на площі Свободи. Ідіть прямо, потім наліво."
  Після музею я хочу їхати у Лавру. Я сідаю в автобус і їду до зупинки "Арсенальна". Від зупинки до Лаври пішки — п'ять хвилин.
  Увечері я телефоную другові в Канаду: "Я зараз у готелі. Сьогодні я був у музеї, в парку і в Лаврі. Завтра хочу поїхати у Львів!"»
- P3 (~40 words): Comprehension check — three quick questions: (1) Звідки Томас? (2) Куди він їде вранці? (3) Де музей? — "Did you understand all three? Good — you're reading Ukrainian!"

## Граматика (~220 words total)
- P1 (~40 words): Framing — "Here are the 7 key patterns from A1.5. Think of this as your personal grammar card for navigating Ukrainian cities."
- P2 (~50 words): Pattern 1 — Euphony. Rule: у/в alternates based on surrounding sounds; і/й alternates the same way; з/із/зі for consonant clusters. Examples: Я у школі. / Він в офісі. / Брат і сестра. / Він й вона. / Я з України. / Зі США.
- P3 (~40 words): Pattern 2 & 3 — Де? vs Куди? contrast. Де? → в/на + locative: у школі, на роботі, в центрі, на площі. Куди? → в/на + accusative: у школу, на роботу, у Львів, на площу.
- P4 (~40 words): Pattern 4 & 5 — Звідки? and transport. Звідки? → з/із/зі + genitive: з України, зі США, з роботи, з Канади. Transport: їхати автобусом/метро/трамваєм; на метро до станції Хрещатик.
- P5 (~50 words): Pattern 6 & 7 — Directions and city places. Directions: іди/йдіть прямо, направо, наліво; вийдіть, потім поверніть. City nouns with prepositions: у музеї, на вокзалі, в парку, на ринку, у бібліотеці, на площі, у готелі.

## Діалог (~330 words total)
- P1 (~30 words): Context-setting — "Марко is visiting Kyiv for the first time. He stops a local (Оксана) to ask for help. Notice how all A1.5 patterns appear in this one conversation."
- Dialogue (~200 words):
  — Вибачте! Ви місцева?
  — Так, я з Києва. Можу допомогти?
  — Дякую! Я з Канади, я тут уперше. Де Національний музей?
  — Музей у центрі, на вулиці Грушевського. Звідси — на метро до станції Арсенальна, потім пішки.
  — А де станція метро?
  — Ось тут, за рогом. Підете прямо, потім направо — і побачите вхід.
  — Чудово! А після музею я хочу їхати у Львів. Де вокзал?
  — Центральний вокзал далеко звідси. Найкраще їхати на метро до станції Вокзальна. Це пряма гілка.
  — Скільки їхати?
  — Хвилин двадцять. Вокзал прямо біля станції, не заблукаєте.
  — А де можна поїсти поблизу?
  — Є кафе на площі Незалежності. Це одна зупинка метро — станція Майдан Незалежності.
  — Ви дуже допомогли! Дякую!
  — Будь ласка! Гарної подорожі до Львова!
- P2 (~50 words): Post-dialogue analysis — "Look at the patterns Марко used: Де музей? (locative) → у центрі. Куди їхати? (accusative) → у Львів. Звідки? → з Канади. Transport → на метро до станції. Directions → прямо, направо. All 7 patterns in one natural conversation."
- P3 (~50 words): Speaking prompt — "Now try it yourself. You're visiting Одеса. Video-call a friend and describe: Я зараз на Дерибасівській вулиці. Іду до порту. Потім хочу на пляж. Я приїхав з [your city]. Use at least 5 of the 7 patterns."

## Підсумок (~220 words total)
- P1 (~50 words): Achievement header — "You've completed A1.5 — Places. Here's what you can now do in Ukrainian:"
- P2 (~100 words): Bulleted achievement list:
  • ✅ Euphony (M28) — You choose у/в, і/й, з/із/зі automatically based on surrounding sounds
  • ✅ Location (M29) — Де? → в/на + locative: у школі, на роботі, в центрі
  • ✅ City vocabulary (M30) — вулиця, площа, парк, музей, вокзал, ринок, аптека, бібліотека
  • ✅ Direction (M31) — Куди? → в/на + accusative: у школу, у Львів, на площу
  • ✅ Transport (M32) — їхати автобусом, трамваєм; на метро до станції Хрещатик
  • ✅ Giving directions (M33) — ідіть прямо, поверніть направо/наліво, вийдіть
  • ✅ Origin (M34) — Звідки? → з/із/зі + genitive: з України, зі США, з Канади
- P3 (~70 words): What's coming next — "In A1.6 — Food and Shopping, you'll learn how to order food, buy things at a market, and use the accusative case for objects (not just directions). You'll say: Я хочу каву. Дайте мені хліб. Скільки коштує? The accusative you practiced for direction (у школу) now works for objects too — a natural extension of what you already know."

Grand total: ~1270 words
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
