<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок — Summary'
- NOTE: Latin characters mixed with Cyrillic: r
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

Write the full prose content for module **23: Days and Months** (A1, A1.4 [Time and Nature]).

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

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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

**Confirmed (26/26 — 100%):**
- понеділок ✅ (noun)
- вівторок ✅ (noun)
- середа ✅ (noun)
- четвер ✅ (noun)
- п'ятниця ✅ (noun)
- субота ✅ (noun)
- неділя ✅ (noun)
- тиждень ✅ (noun)
- зима ✅ (noun)
- весна ✅ (noun)
- літо ✅ (noun)
- осінь ✅ (noun)
- січень ✅ (noun)
- **лютий ✅ — ⚠️ ADJECTIVE in VESUM (6 adj matches), NOT noun**
- березень ✅ (noun)
- квітень ✅ (noun)
- травень ✅ (noun)
- червень ✅ (noun)
- липень ✅ (noun)
- серпень ✅ (noun)
- вересень ✅ (noun)
- жовтень ✅ (noun)
- листопад ✅ (noun)
- грудень ✅ (noun)
- день ✅ (noun)
- народження ✅ (noun)

**Not found:** none

**⚠️ CRITICAL NOTE — лютий:** VESUM registers it as an **adjective** (6 adj matches), not a noun. This is correct — лютий (February) is a substantivized adjective in Ukrainian. Its case forms follow **adjective declension**: у лю́тому (locative, not *у лютні*). The plan already implies "у лютому" via the chunk pattern — this is correct. Writer must NOT use noun-pattern declension for лютий.

---

## Textbook Excerpts

### Section: Дні тижня (Days of the Week)
> «Пригадайте назви днів тижня. Послідовно запишіть їх. У середу я планую ? . Для цього мені потрібно ? . Я маю зробити ? . Розкажіть, як ви плануєте свій день (один із днів тижня на вибір).»
> Source: Vashulenko, Grade 2 (2019), p. 83 — **exact match for the "planning your week" activity pattern**

> «Пригадай назви днів тижня. Запиши їх правильно: Понеділок, ?, ?, ?, ?, ?, ?»
> Source: Vashulenko, Grade 3 (2020), p. 79 — shows all 7 days listed from понеділок in sequence

> «ТИЖДЕНЬ — НЕДІЛЯ. У сучасній українській літературній мові проміжок часу в сім днів називають тижнем… Сьомий день тижня, день відпочинку, називають неділею.»
> Source: Voron, Grade 9, p. 121 — **confirms the neділя/тиждень distinction** (план note is correct)

### Section: Місяці і пори року (Months and Seasons)
> «Наші назви місяців прозорі. Легко встановити те, яка ознака покладена в основу називання. Січень дістав свою назву від «сікти»… Лютий названо за люті, злі, жорстокі морози… Березень — місяць, коли збирають березовий сік. Квітень — місяць цвітіння. Травень — буйні рости трав. Червень — від червець… Липень — цвітіння медоносної липи. Серпень — час збору урожаю. Вересень — пора цвітіння вересу. Жовтень — місяць жовтого листя. Листопад — у самому слові чути шелест листя. Грудень — земля змерзається у груддя.»
> Source: Воron, Grade 9, p. 60 — "УКРАЇНСЬКИЙ МІСЯЦЕЛІК" — **gold-standard etymology source for all 12 months, directly usable in the module**

> «Ступив Новий рік на Землю… Тільки не ми! — обізвалися Червень, Липень і Серпень…»
> Source: Kravcova, Grade 2 (2019), p. 60 — months personified by season grouping: зимові (Грудень/Січень/Лютий), весняні (Березень/Квітень/Травень), літні (Червень/Липень/Серпень), осінні (Вересень/Жовтень/Листопад)

### Section: Діалоги — день народження
> «Зазнач дату свого народження за зразком: 15.11.2012 → п'ятнадцяте листопада дві тисячі дванадцятого року. Я народився (народилася) ... (число) ... (місяць) ... (рік).»
> Source: Vashulenko, Grade 2 (2019), p. 92 — **exact birthday date pattern** including ordinal for day + genitive month

### Section: Діалоги — planning the week
> «Розкажіть, як ви плануєте свій день (один із днів тижня на вибір). Що ви в цей день будете робити? Наведіть приклад такого плану за зразком. Планування — ключ до успіху в житті.»
> Source: Vashulenko, Grade 2 (2019), p. 83 — validates the week-planning dialogue pattern in Plan

---

## Grammar Rules

- **Days of week + months → малої літери (lowercase):** Правопис §45–§49 do not list them as proper nouns (власні назви). All textbook examples confirm: понеділок, вівторок, січень, лютий etc. are written with **мала літера** as загальні назви (common nouns). This contrasts with English capitalization — a key teaching point. Confirmed by textbook evidence: Grade 3 Vashulenko p.79 "Понеділок, ?, ?, ?, ?, ?, ?" (capital only because it opens the sentence).

- **Preposition у/в + accusative for days:** у понеділок, у вівторок, у середу, у четвер, у п'ятницю, **в суботу**, **в неділю** — the у/в alternation follows standard phonetic rule (§ у-в: use **в** before vowels and when preceding word ends in vowel; use **у** after consonants). Субота and неділя take **в** because the preceding word typically ends in a vowel in speech flow.

- **Seasonal adverbs — irregular chunks:** взимку, навесні, влітку, восени — these are **pronominal adverbs** (прислівники), not prepositional phrases. They cannot be broken into у + noun at A1 — teach as frozen forms.

- **лютий — adjective declension:** As a substantivized adjective: Nom. лютий, Gen. лютого, Dat. лютому, Acc. лютий, Instr. лютим, Loc. у лютому. Plan's chunk "у лютому" is confirmed correct.

---

## Calque Warnings

- **вільний день** — OK. This is natural Ukrainian. The style guide discussion around "вихідний день" (day off) vs. "вільний день" (free day) notes both are used. No calque. ✅

- **у понеділок** — OK. Natural Ukrainian prepositional phrase. No calque. ✅

- **вивчати українську** — OK. Natural Ukrainian. No calque. ✅

- **⚠️ WATCH: "пара днів"** — Антоненко-Давидович explicitly flags this as a Russianism: *"Так сказати по–українському не можна"*. Correct form: **кілька днів** / **два–три дні**. The dialogue plan doesn't use this phrase, but if any dialogue says "через пару днів" → rewrite to "через кілька днів".

- **день народження** — OK. This is the standard Ukrainian collocation. Not a calque. ✅

---

## CEFR Check

- понеділок: **A1** — ✅ on target
- субота: **A1** — ✅ on target
- тиждень: **A1** — ✅ on target
- зима: **A1** (взимку also A1) — ✅ on target
- осінь: **A1** — ✅ on target
- січень: **A1** — ✅ on target
- день: **A1** — ✅ on target

**No words above A1 level.** All vocabulary is confirmed A1-appropriate per PULS CEFR database.
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
# Verified Knowledge Packet: Days and Months
**Module:** days-and-months | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** , Grade 4
> **Section:** Сторінка 110
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Які зі слів 
> позначають кількість предметів, а які — порядок їх під час 
> лічби?
> Слова, що означають кількість предметів або їх 
> порядок під час лічби, називаються числівниками.

## Дні тижня (Days of the Week)

> **Source:** , Grade 4
> **Section:** Сторінка 110
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Які зі слів 
> позначають кількість предметів, а які — порядок їх під час 
> лічби?
> Слова, що означають кількість предметів або їх 
> порядок під час лічби, називаються числівниками.

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 77
> **Score:** 0.50
>
> 77
> 2. Допоможи Щебетунчикові вставити пропущені назви 
> днів тижня. Перевір їх написання за словником. Спиши 
> текст,  підкресли  орфограми  в  дібраних  словах.
> Якщо до слова не можна дібрати перевірне слово,
> то його написання треба перевіряти за словником.
> Тиждень починає … .  Після нього приходить … .
> За ним настає … . Четвертий день тижня — … .
> А п’ятий — … . П’ять днів працюємо, а в … і … 
> відпочиваємо.
> 3. Прочитай і розв’яжи задачу Родзинки.
> Марійка з дідусем вирушили в похід на третій 
> день тижня. А повернулися з походу через три дні.
> Поміркуй, у який день тижня Марійка з дідусем
> вирушили в похід, а в який повернулись.
> 5. Запиши слова у дві колонки: до першої — ті, що переві-
> ряються за правилом, до другої — ті, що перевіряються
> за словником. Підкресли орфограми.
> 5
> 4.

## Місяці і пори року (Months and Seasons)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 105
> **Score:** 0.50
>
> 105
>  
>  Послухайте текст Антоніни Назаренко «Який це 
> місяць?» і дайте відповідь на запитання, яке міститься 
> в заголовку.
>  Про які зміни в природі розповідає Антоніна 
> Назаренко?
>  З чого зрозуміло, що це рання весна?
>  Як же називається цей весняний місяць?
> Весна днем красна.
> Притрушує, пригрітих, сльозяться, передчуттям, підтри- 
> мують, повернувшись.
> Прочитай правильно
> 48
> Степан Мацюцький
> У  ГОСТЯХ  У  ВЕСНИ
> Ще ховаються по байраках сірі брили злежаного снігу. 
> Уночі морозець притрушує білою пудрою зелене листя осо-
> ки на болоті, а вже красується золотими сережками ліщина 
> і на пригрітих сонцем галявинах випинаються молодими 
> соковитими стрілами трави.
> У таку пору я поспішаю в ліс. Поспішаю в гості до самої 
> весни.
> Ранок теплий, сонячний. Дихає свіжістю земля.

## Підсумок — Summary

> **Source:** , Grade 4
> **Section:** Сторінка 110
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Які зі слів 
> позначають кількість предметів, а які — порядок їх під час 
> лічби?
> Слова, що означають кількість предметів або їх 
> порядок під час лічби, називаються числівниками.

## Grammar Reference

> **Source:** , Grade 4
> **Section:** Сторінка 110
> **Score:** 0.33
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Які зі слів 
> позначають кількість предметів, а які — порядок їх під час 
> лічби?
> Слова, що означають кількість предметів або їх 
> порядок під час лічби, називаються числівниками.

---
**Total textbook excerpts found:** 6
**Grades searched:** 3, 4, 5
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Дні тижня (Days of the Week)` (~300 words)
- `## Місяці і пори року (Months and Seasons)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
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
  1. **At a doctor's reception — booking an appointment**
     Speakers: Пацієнт, Реєстратор
     Why: Days and months: У понеділок? Ні, у середу. В якому місяці?

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

GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):
Time expressions, days, months, weather, daily routines.

ALLOWED:
- All present tense (from A1.3)
- Time expressions as chunks (О першій, У понеділок)
- Sequence adverbs (спочатку, потім, нарешті)
- Impersonal weather constructions (Сьогодні холодно)

BANNED: Past/future tense, case endings (time chunks only),
participles, passive voice, complex subordination

### Vocabulary

**Required:** понеділок, вівторок, середа (Mon, Tue, Wed), четвер, п'ятниця (Thu, Fri), субота, неділя (Sat, Sun), тиждень (week, m), зима, весна, літо, осінь (winter, spring, summer, autumn)
**Recommended:** січень, лютий, березень (Jan, Feb, Mar), квітень, травень, червень (Apr, May, Jun), липень, серпень, вересень (Jul, Aug, Sep), жовтень, листопад, грудень (Oct, Nov, Dec), день народження (birthday)

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

- D1 (~110 words): Dialogue 1 — Planning the week. Taras asks Olena about her schedule across 4 turns. Lines include: "— Що ти робиш у понеділок? — Я працюю. А у вівторок? — У вівторок я вивчаю українську. — А у суботу? — У суботу гуляю з друзями. Неділя — вільний день!" Introduces у/в + day as pure chunk — no grammar label, just exposure. Spoken register (ти forms).
- D2 (~110 words): Dialogue 2 — Birthday and months. Two friends: "— Коли у тебе день народження? — У березні. — Якого числа? — П'ятнадцятого березня. А у тебе? — У мене в серпні. — О, це літо! Тепло і сонячно." Shows у/в + month and а season comment (це літо) naturally. Introduces день народження as a fixed phrase.
- P1 (~110 words): Brief framing paragraph between or after dialogues — note the recurring pattern: у + [day/month] keeps appearing. Learner's takeaway: Ukrainian uses у/в before time words. No grammar terms yet — just "you'll see this pattern again and again."

---

## Дні тижня (~330 words total)

- P1 (~80 words): Introduce the 7 days as a visual list, all lowercase (explicit contrast with English capitals): понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя. Point out the week starts on понеділок in Ukrainian calendars (not Sunday). Note: неділя = Sunday AND an archaic/dialectal word for "week"; standard "week" = тиждень.
- P2 (~90 words): Etymology micro-notes to aid memory — 3 examples: четвер ← четвертий (4th day), п'ятниця ← п'ять (5th day), середа = "middle" of the week. One sentence on субота (Sabbath origin, borrowed). Framing: these aren't random sounds — the days tell a story.
- Exercise: fill-in — "Put days of the week in sequence" (7 items from activity_hints, e.g.: понеділок, ___, середа → вівторок).
- P3 (~100 words): "On" a day = у/в + the chunk form. Full list of all 7 forms: у понеділок, у вівторок, у середу, у четвер, у п'ятниця → у п'ятницю, в суботу, в неділю. Highlight that endings change (середа→середу, п'ятниця→п'ятницю, субота→суботу) but неділя→неділю follows the same pattern. Explicit instruction: memorize each full chunk — don't try to construct it yet.
- P4 (~60 words): Short reinforcement — 4 model sentences using different days: "Я навчаюся у вівторок і в четвер. Тато працює у понеділок. У п'ятницю ми дивимося фільм. В суботу я сплю довго."

---

## Місяці і пори року (~330 words total)

- P1 (~90 words): Four seasons as the organizing frame. Introduce зима (f), весна (f), літо (n), осінь (f) with one sentence of sensory association each (e.g., "Зима — сніг і холод. Весна — квіти і тепло. Літо — сонце і море. Осінь — листя і дощ."). Then present the 12 months grouped under each season: Зима: грудень, січень, лютий. Весна: березень, квітень, травень. Літо: червень, липень, серпень. Осінь: вересень, жовтень, листопад. All lowercase.
- P2 (~80 words): Etymology 3 months to make them memorable: березень ← береза (birch tree blooms), липень ← липа (linden tree flowers), листопад ← листя + падати (leaves fall). Point out Ukrainian months come from nature — not from Roman gods like January/February. This is a Ukrainian linguistic fingerprint. All months are masculine gender.
- Exercise: match-up — "Match the month to the correct season" (8 pairs from activity_hints: січень↔зима, квітень↔весна, липень↔літо, жовтень↔осінь, лютий↔зима, травень↔весна, серпень↔літо, листопад↔осінь).
- P3 (~100 words): "In" a month = у/в + locative chunk. Full list of all 12 locative forms: у січні, у лютому, в березні, у квітні, у травні, в червні, в липні, в серпні, у вересні, в жовтні, в листопаді, в грудні. For seasons — irregular adverbial forms (memorize as chunks): взимку, навесні, влітку, восени. 2 model sentences: "Мій день народження в жовтні. Влітку я їжджу на море."
- P4 (~60 words): Short reinforcement — 4 sentences mixing months and seasons: "У грудні холодно — це зима. Навесні квітнуть дерева. В серпні ми відпочиваємо. Восени починається школа."
- Exercise: fill-in — "Use the correct 'in/on' chunk" (6 items from activity_hints: Я працюю ___ (у понеділок), Мій день народження ___ (у березні), Ми гуляємо ___ (в суботу), ___ холодно (Взимку), Я вивчаю українську ___ (у вівторок), Вони відпочивають ___ (у серпні)).

---

## Підсумок (~150 words total)

- P1 (~150 words): Vocabulary recap as structured self-check. Present three labeled lists then four self-check questions:
  - **Дні тижня:** понеділок → неділя (chunk: у понеділок / в суботу / в неділю)
  - **Місяці:** січень → грудень (chunk: у січні / в серпні)
  - **Пори року:** зима, весна, літо, осінь (chunks: взимку, навесні, влітку, восени)
  Self-check questions (answer in Ukrainian):
  - Який сьогодні день?
  - Який зараз місяць?
  - Яка зараз пора року?
  - Коли у тебе день народження?
  - Що ти робиш у суботу?

---

Grand total: ~1340 words
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
