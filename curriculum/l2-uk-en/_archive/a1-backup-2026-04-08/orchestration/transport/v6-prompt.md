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

Write the full prose content for module **32: Transport** (A1, A1.5 [Places]).

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

1. **IMMERSION TARGET: 15-30% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-032
level: A1
sequence: 32
slug: transport
version: '1.1'
title: Transport
subtitle: Автобус, метро, таксі — getting around
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Name common transport types (автобус, метро, таксі, потяг, трамвай)
- Buy a ticket and ask about routes
- Use їхати + transport expressions (їхати автобусом / на метро)
- Combine transport with direction (куди) and locative (де) from M29-31
dialogue_situations:
- setting: Explaining how to get from Kyiv airport (Бориспіль) to the hotel — автобус
    (m), потяг (m, train), таксі (n), метро (n). Їхати автобусом, потягом. Їхати на
    метро, на таксі.
  speakers:
  - Приїжджий (visitor)
  - Друг (local)
  motivation: 'Transport: автобус(m), потяг(m), таксі(n), метро(n)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Getting to the train station: — Як дістатися до вокзалу? — Їдьте
    автобусом або на метро. — Який автобус? — Номер сім. Зупинка ось там. — Дякую!
    — На здоров''я! Transport vocabulary in practical context.'
  - 'Dialogue 2 — Buying a ticket: — Один квиток до Львова, будь ласка. — В один бік
    чи туди й назад? — Туди й назад. Скільки коштує? — П''ятсот гривень. — О котрій
    відправлення? — О дев''ятій ранку. Combines transport + numbers (M11) + time (M22).'
- section: Транспорт (Transport Types)
  words: 300
  points:
  - 'City transport: автобус (bus, m), тролейбус (trolleybus, m), трамвай (tram, m),
    метро (metro, n — indeclinable), маршрутка (minibus, f), таксі (taxi, n — indeclinable).
    Intercity: потяг (train, m), автобус (bus), літак (plane, m).'
  - 'How to say ''by transport'': їхати автобусом / тролейбусом / трамваєм (instrumental
    chunk — not grammar). їхати на метро / на таксі / на машині (на + locative chunk).
    Note: both patterns mean ''by'' — learn each transport with its pattern.'
- section: Корисні фрази (Useful Phrases)
  words: 300
  points:
  - 'At the station/stop: Зупинка (stop/station), Де зупинка автобуса? (Where''s the
    bus stop?) квиток (ticket), Один квиток, будь ласка. (One ticket, please.) Скільки
    коштує квиток? (How much is a ticket?) Коли наступний потяг? (When is the next
    train?)'
  - 'On the way: Яка це зупинка? (What stop is this?) Мені виходити тут? (Do I get
    off here?) Вибачте, як дістатися до...? (Excuse me, how do I get to...?) прямо
    (straight), направо (right), наліво (left).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Transport communication: Types: автобус, метро, таксі, потяг, трамвай. By: автобусом
    / на метро (two patterns). Buying: Один квиток до... Скільки коштує? Asking: Де
    зупинка? Як дістатися до...? Self-check: How do you get to work? Buy a train ticket
    to Lviv.'
vocabulary_hints:
  required:
  - автобус (bus, m)
  - метро (metro, n)
  - таксі (taxi, n)
  - потяг (train, m)
  - квиток (ticket, m)
  - зупинка (stop, f)
  recommended:
  - трамвай (tram, m)
  - маршрутка (minibus, f)
  - літак (plane, m)
  - направо (right)
  - наліво (left)
  - прямо (straight)
  - дістатися (to get to)
activity_hints:
- type: quiz
  focus: Which transport? Match situation to transport type.
  items: 8
- type: fill-in
  focus: 'Buy a ticket: Один ___ до ___, будь ласка.'
  items: 6
- type: quiz
  focus: Автобусом or на метро? Choose the right pattern.
  items: 6
- type: fill-in
  focus: 'Ask for directions: Як дістатися до ___?'
  items: 6
connects_to:
- a1-033 (Around the City)
prerequisites:
- a1-031 (Where To?)
grammar:
- 'Transport instrumental chunks: автобусом, потягом'
- 'Transport на chunks: на метро, на таксі'
- 'Directional phrases: прямо, направо, наліво'
register: розмовний
references:
- title: Anna-led — transport and travel vocabulary
  notes: Practical communication for getting around Ukrainian cities.

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

**Confirmed (13/13 plan vocabulary words found):**
- ✅ автобус (noun)
- ✅ метро (noun — indeclinable, 14 matches)
- ✅ таксі — ⚠️ **FLAG**: VESUM returned lemma "така(noun)" — likely matching "такса" (fee/dachshund), not "таксі" (taxi). Таксі is a standard indeclinable borrowing but verify independently at goroh.pp.ua. Functionally safe to use; stress: та́ксі.
- ✅ потяг (noun)
- ✅ квиток (noun)
- ✅ зупинка (noun)
- ✅ трамвай (noun)
- ✅ маршрутка (noun)
- ✅ літак (noun)
- ✅ направо (adv)
- ✅ наліво (adv)
- ✅ прямо (adv)
- ✅ дістатися (verb)

**Additional section words confirmed:**
- ✅ тролейбус (noun)
- ✅ відправлення (noun)
- ✅ вокзал (noun)
- ✅ гривня (noun)
- ✅ рейс (noun)
- ✅ пасажир (noun)

**Not found:** none — all words exist in VESUM.

---

## Textbook Excerpts

### Section: Транспорт (Transport Types)
> «У містах багато високих будинків. […] Вулицями міст їздять тролейбуси, трамваї, автобуси, маршрутні таксі. […] метро, площа, вулиця, парк»
> Source: Большакова, Grade 1 (Буквар, 2018), p. 16 — ✅ All core city transport types appear in Grade 1 Ukrainian primers. Maршрутні таксі is the full form; маршрутка is its colloquial short form.

### Section: Діалоги — Buying a Ticket
> «— Скажіть, будь ласка, чи є сьогодні автобус на Моринці? […] — О котрій годині найближчий рейс? — О десятій. […] — Я можу придбати квиток на цей рейс? — Авжеж. Є ще вільні місця. — Тоді продайте мені, будь ласка, два квитки на цей рейс.»
> Source: Кравцова, Grade 3 (Українська мова, 2020), p. 83 — ✅ Exact match for the plan's ticket-buying dialogue pattern. Confirms "О котрій?" for time + "квиток" + station/bus context.

### Section: Корисні фрази (travel language)
> «Щодня вінничани та гості міста слухають фрази: "Обережно, двері зачиняються!", "Розраховуйтесь, будь ласка, за проїзд" чи "Поступайтесь місцем старшому."»
> Source: Літвінова, Grade 5 (Українська мова, 2022), p. 208 — ✅ Confirms authentic public transport announcements and etiquette phrases.

### Section: Підсумок — correct Ukrainian forms
> «ПРАВИЛЬНО: виходити з автобуса / оплатити проїзд | НЕПРАВИЛЬНО: сходити з автобуса / оплатити за проїзд»
> Source: Заболотний, Grade 9 (Українська мова, 2017), p. 75 — ✅ Critical naturalness rules directly confirmed.

### Section: Potjah/Train dialogue
> «— Наш поїзд оголосили! Ходімо швидше! […] — Який у нас вагон? — 7-й.» + railway ticket context, "О котрій відправлення?"
> Source: Літвінова, Grade 6 (Українська мова, 2023), p. 247 — ✅ Confirms train station dialogue register and "відправлення" for departure.

---

## Grammar Rules

- **Instrumental for transport (їхати автобусом / трамваєм)**: This is taught as a **lexical chunk** in the plan — correct A1 approach. Правопис §57 covers noun declension endings; instrumental singular of 2nd declension masculine nouns takes **-ом/-ем**. автобус → автобусом ✅; трамвай → трамваєм ✅ (soft stem, -єм).
- **Indeclinable nouns (метро, таксі)**: Правопис §53 — foreign-origin nouns ending in a vowel are indeclinable neuter nouns in Ukrainian. на метро / на таксі (prepositional "на" + unchanged form) ✅
- **Preposition до for directional movement**: Антоненко-Давидович §"У(в)–до" confirms: movement *toward* a city/place → **до** (Як дістатися **до** вокзалу? ✅). Movement/location *inside* → у/в.
- **Правопис query for орудний відмінок** returned §16 (consonant alternations) — not the declension table. Instrumental case endings are in §57. No rule violation found in the plan content.

---

## Calque Warnings

- **«Як дістатися до вокзалу?»** → ✅ **OK** — natural Ukrainian. Антоненко-Давидович confirms «до» is correct for directional movement toward a destination. Not a calque.

- **«В один бік чи туди й назад?»** → ✅ **OK** — natural Ukrainian phrasing for one-way/round-trip. «Туди й назад» is idiomatic. No calque detected.

- **«На здоров'я!»** as a response to «Дякую!» → ⚠️ **POTENTIAL ISSUE**: Антоненко-Давидович has no entry confirming this as a standard thanks-response. «На здоров'я!» in standard Ukrainian is used as a **toast** (when drinking) or a **response to sneezing** — not typically as "you're welcome." This usage may be a Polonism common in western Ukraine. **Recommended alternative: «Будь ласка!»** or **«Прошу!»** for a standard thanks-response. Flag for native speaker check. <!-- VERIFY -->

- **«О котрій відправлення?»** → ✅ **OK** — confirmed in Grade 6 Litvinova textbook. Natural Ukrainian at the train station.

- **«Один квиток до Львова»** → ✅ **OK** — «до» + city name confirmed as correct (movement toward destination per Антоненко-Давидович). Not «у Львів» for the ticket destination context.

---

## CEFR Check

- **автобус**: A1 ✅ — on target
- **квиток**: A1 ✅ — on target
- **зупинка**: A1 ✅ — on target
- **маршрутка**: A1 ✅ — on target
- **трамвай**: A1 ✅ — on target
- **літак**: A1 ✅ — on target
- **потяг**: ⚠️ **A2** per PULS — one level above target. Note: PULS also lists **поїзд** at A1. However, «потяг» is the more authentically Ukrainian term (поїзд is a Soviet-era Russianism). Since this module is A1.5 and teaches transport as functional vocabulary, **потяг is pedagogically preferable** and acceptable as a taught chunk — flag for awareness but do not substitute поїзд.
- **дістатися**: ⚠️ **Not in PULS directly** (closest matches: B1–B2 verbs). As an analyzed verb it is above A1. However, the plan teaches «Як дістатися до...?» as a **formulaic phrase** (lexical chunk), which is standard A1 functional language pedagogy — ✅ acceptable approach, do not decompose grammatically at this level.
- **тролейбус**: Not checked in PULS but confirmed in Grade 1 Bolshakova alongside автобус/трамвай — A1 appropriate.
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
# Verified Knowledge Packet: Transport
**Module:** transport | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** litvinova, Grade 6
> **Section:** Сторінка 247
> **Score:** 0.33
>
> § 52. Правильне вживання числівниківна позначення дат і часу   
> 247
> — Наш поїзд оголосили! Ходімо швидше! І  на табло 
> вже є!
> — Не поспішай, ми встигаємо. Зараз 07.05.
> — Який у  нас вагон?
> — 7-й.
> 2. Попросіть у дорослих або знайдіть у мережі «Інтернет» залізнич-
> ний квиток, дайте відповідь на запитання: у  якому вагоні їдуть ман-
> дрівники, коли вони приїжджають у  пункт призначення, яка вартість 
> квитка, чи сплачено за послуги (білизна, чай).
> Вправа 501
> 1. Прочитайте електронного листа.
> 17:25
> 93%
> Привіт, сестричко!
> Ми з батьками визначилися з датою приїзду 
> та  взяли квитки. Вирушаємо 26.06 о 13.55, на місці 
> будемо 27.06 о 9.10. Час заселення в готель — 14.00, 
> тому нам доведеться почекати, але це не страшно.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 208
> **Score:** 0.50
>
> 208
> Відомості із синтаксису й пунктуації.  Види речень за емоційним забарвленням
> Вправа 339
> 1.	 Прочитайте новину.
> ДОЇХАЛИ КОМФОРТНО?  
> ПОДЯКУЙТЕ ЕКІПАЖУ!
> «Марафон взаємоввічливості» оголосила Вінницька тран-
> спортна компанія. Тепер пасажири й  пасажирки можуть 
> віддячити за  чемність у  трамваї, тролейбусі та  автобусі, 
> проголосувавши за  найвідповідальніший екіпаж міського 
> громадського транспорту. Якщо їдете у вінницькому тран-
> спорті, знайдіть плакат із  номером екіпажу й  відскануйте 
> QR-код. Далі виконайте три прості дії: натисніть на  зна-
> чок голосування, оберіть номер екіпажу, який сподобався, 
> і  клацніть на  кнопку «голосувати».

## Транспорт (Transport Types)

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 146
> **Score:** 0.50
>
> 146
> Завмерли трамваї, тролейбуси стали,
> автомобілі загальмували...
> Не їде ніхто, не йде, не біжить —
> рух зупинився навколо умить.
>  
>  
>  
>  
>  
>  
>     Оксана Сенатович
> трамва’й
> троле’йбус
> 2. Як, на вашу думку, птахи могли зупинити рух на вулицях 
> міста?
> 310. 1. Розгляньте малюнки. Прочитайте і спишіть речення.
> Вранці Андрійко збирається до школи. Він одягається, 
> взувається.
> Вранці Андрійко збирає братика до дитячого садка. Він 
> одягає та взуває малюка.
> дисциплі’на
> гардеро’ б
> 2. Які дієслова називають дії Андрійка, спрямовані на нього 
> самого? Які дієслова означають дії Андрійка, спрямовані 
> на іншу особу (братика)? Зробіть висновок, якого змісту 
> надає дієсловам -ся.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 208
> **Score:** 0.50
>
> 208
> Відомості із синтаксису й пунктуації.  Види речень за емоційним забарвленням
> Вправа 339
> 1.	 Прочитайте новину.
> ДОЇХАЛИ КОМФОРТНО?  
> ПОДЯКУЙТЕ ЕКІПАЖУ!
> «Марафон взаємоввічливості» оголосила Вінницька тран-
> спортна компанія. Тепер пасажири й  пасажирки можуть 
> віддячити за  чемність у  трамваї, тролейбусі та  автобусі, 
> проголосувавши за  найвідповідальніший екіпаж міського 
> громадського транспорту. Якщо їдете у вінницькому тран-
> спорті, знайдіть плакат із  номером екіпажу й  відскануйте 
> QR-код. Далі виконайте три прості дії: натисніть на  зна-
> чок голосування, оберіть номер екіпажу, який сподобався, 
> і  клацніть на  кнопку «голосувати».

## Корисні фрази (Useful Phrases)

> **Source:** golub, Grade 6
> **Section:** Сторінка 198
> **Score:** 0.33
>
> 198
> Коли гучномовець оголосив пасажирці її чергу пред’являти 
> квиток, вона все ще палала від обурення. І от уявіть собі збен-
> теження жінки, коли та, потягнувшись у сумочку за квит-
> ком, виявила там свій непочатий пакунок. Отже, вона їла 
> тістечка того чоловіка…
> Подумай про відчуття жінки до моменту істини («От гру-
> біян і нахаба!») і після («Який сором! А він ще так люб’язно 
> поділився зі мною тим останнім тістечком!»).
> У чому ж суть? Дуже просто: нам не треба так поспішно 
> судити, навішувати ярлики, бути категоричними, оцінюючи 
> інших, — зрештою, як і самих себе. Маючи обмежену інфор-
> мацію, важко побачити всю картину, урахувати всі факти 
> (за кн. «Сім звичок високоефективних підлітків»).
>  
> ІІ   До слова, позначеного зірочкою, доберіть синоніми.

## Підсумок — Summary

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 146
> **Score:** 0.50
>
> 146
> Завмерли трамваї, тролейбуси стали,
> автомобілі загальмували...
> Не їде ніхто, не йде, не біжить —
> рух зупинився навколо умить.
>  
>  
>  
>  
>  
>  
>     Оксана Сенатович
> трамва’й
> троле’йбус
> 2. Як, на вашу думку, птахи могли зупинити рух на вулицях 
> міста?
> 310. 1. Розгляньте малюнки. Прочитайте і спишіть речення.
> Вранці Андрійко збирається до школи. Він одягається, 
> взувається.
> Вранці Андрійко збирає братика до дитячого садка. Він 
> одягає та взуває малюка.
> дисциплі’на
> гардеро’ б
> 2. Які дієслова називають дії Андрійка, спрямовані на нього 
> самого? Які дієслова означають дії Андрійка, спрямовані 
> на іншу особу (братика)? Зробіть висновок, якого змісту 
> надає дієсловам -ся.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 208
> **Score:** 0.50
>
> 208
> Відомості із синтаксису й пунктуації.  Види речень за емоційним забарвленням
> Вправа 339
> 1.	 Прочитайте новину.
> ДОЇХАЛИ КОМФОРТНО?  
> ПОДЯКУЙТЕ ЕКІПАЖУ!
> «Марафон взаємоввічливості» оголосила Вінницька тран-
> спортна компанія. Тепер пасажири й  пасажирки можуть 
> віддячити за  чемність у  трамваї, тролейбусі та  автобусі, 
> проголосувавши за  найвідповідальніший екіпаж міського 
> громадського транспорту. Якщо їдете у вінницькому тран-
> спорті, знайдіть плакат із  номером екіпажу й  відскануйте 
> QR-код. Далі виконайте три прості дії: натисніть на  зна-
> чок голосування, оберіть номер екіпажу, який сподобався, 
> і  клацніть на  кнопку «голосувати».

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 148
> **Score:** 0.33
>
> 148
> ЖИВИЛЬНІ ДЖЕРЕЛА МУДРИХ КНИГ
>  ÏÅÐÅÂ²ÐßªÌÎ
> 1. Розгадайте зашифровані назви тварин. Яких із них згадано 
> в першій частині повісті «Тореадори з Васюківки»?
>      
> 2. Найдорожчу ціну за вхід у метро юні «будівельники» встанови-
> ли для
>  
> А своїх родичів 
>  
> В учительки математики
>  
> Б далеких сусідів  
> Г туристів із міста 
> 3. Ява й Павлуша врятувалися від Контрибуції 
>  
> А у ставку     Б на дереві     В на городі     Г у лісі
>  ÀÍÀË²ÇÓªÌÎ
> 4. Яке враження справила на вас перша частина повісті В. Нестай-
> ка? Що запам’яталося найбільше? 
> 5. Розкажіть, як завершився намір друзів вирити метро під сви-
> нарником. Як на цю витівку відреагував дід Варава та чи 
> зробили хлопці правильні висновки?
> 6.

## Grammar Reference

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 85
> **Score:** 0.33
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьо

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Транспорт (Transport Types)` (~300 words)
- `## Корисні фрази (Useful Phrases)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Explaining how to get from Kyiv airport (Бориспіль) to the hotel — автобус (m), потяг (m, train), таксі (n), метро (n). Їхати автобусом, потягом. Їхати на метро, на таксі.**
     Speakers: Приїжджий (visitor), Друг (local)
     Why: Transport: автобус(m), потяг(m), таксі(n), метро(n)

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

**Required:** автобус (bus, m), метро (metro, n), таксі (taxi, n), потяг (train, m), квиток (ticket, m), зупинка (stop, f)
**Recommended:** трамвай (tram, m), маршрутка (minibus, f), літак (plane, m), направо (right), наліво (left), прямо (straight), дістатися (to get to)

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

- P1 (~25 words): Scene-setting intro — Оля зустрічає друга Марка в аеропорту Бориспіль. Він приїхав до Києва вперше і не знає, як дістатися до готелю.
- Dialogue 1 (~100 words): Multi-turn exchange — Марко asks «Як мені дістатися до центру?»; Оля offers three options: «Можна їхати автобусом — номер сімдесят один, можна потягом — "Експрес", або на таксі». Марко asks «А метро є?»; Оля explains «Метро нема в аеропорту. Але в центрі є. Поїдьте потягом, а потім на метро». Марко: «Добре. Де квиток?» / «Ось там, у касі».
- P2 (~20 words): Brief note — two patterns appear in the dialogue: їхати автобусом / потягом (instrumental) vs. їхати на метро / на таксі (на + noun). Learners will study both below.
- Dialogue 2 (~100 words): Ticket window exchange — Марко at the kiosk: «Один квиток до центру, будь ласка». Каса: «На автобус чи на потяг?» / «На потяг». / «Гаразд. Сто двадцять гривень». / «О котрій відправлення?» / «О дев'ятій двадцять». / «Дякую!» / «Будь ласка. Приємної поїздки!». Combines квиток, гривні (M11), time expression (M22).
- P3 (~85 words): Post-dialogue note — highlight two new questions learners just heard: «О котрій відправлення?» (What time does it depart?) and «Приємної поїздки!» (Have a good trip! — fixed phrase, not analysed further). Recap which transport words appeared: автобус, потяг, метро, таксі — and flag their genders. These genders matter for the instrumental pattern in the next section.

---

## Транспорт (~330 words total)

- P1 (~100 words): City transport vocabulary with gender labels — автобус (bus, m), тролейбус (trolleybus, m), трамвай (tram, m), маршрутка (minibus, f). Each given with a short real-world cue: «автобус і тролейбус є у більшості міст; трамвай є у Києві, Львові, Вінниці; маршрутка — невеликий мікроавтобус, дуже поширений в Україні». Stress marked: авто́бус, тролейбус, трамва́й, маршру́тка.
- P2 (~60 words): Indeclinable nouns — метро (metro, n) and таксі (taxi, n). Key point: these words never change form — метро is always метро, таксі is always таксі. No instrumental form possible, so they use a different pattern (на + the word). Contrast: потяг (train, m) and літак (plane, m) — these DO change.
- P3 (~90 words): Pattern 1 — їхати + instrumental chunk. Presented as a fixed chunk to memorise with each masculine noun: їхати авто́бусом, їхати тролейбусом, їхати трамваєм, їхати поїздом / поїздом (note: потяг → потягом). Table of 5 forms. Framed explicitly as a CHUNK, not grammar: «Learn each transport with its form — don't analyse the ending at this stage».
- P4 (~80 words): Pattern 2 — їхати на + noun (for indeclinables and машина). Examples: їхати на метро, їхати на таксі, їхати на машині. Note: метро and таксі use на because they don't change form. машина adds на for a different reason — but at A1 treat all three as chunks. «Which pattern? Learn it WITH the word: потяг → потягом; метро → на метро».
- Exercise: Quiz — "Автобусом or на метро?" — 6 items. Learner chooses the correct pattern for: трамвай, таксі, тролейбус, метро, потяг, маршрутка.

---

## Корисні фрази (~330 words total)

- P1 (~110 words): At the stop / station — six phrases presented in a realistic street scenario. Марко needs to find the bus stop: «Вибачте, де зупинка автобуса?» — «Ось там, навпроти». Then at the ticket window: «Один квиток, будь ласка» / «Скільки коштує квиток?» / «Коли наступний потяг до Львова?» Each phrase given in Ukrainian with English gloss. Vocabulary spotlighted: зупи́нка (stop, f), кви́ток (ticket, m), ка́са (ticket window, f), відправле́ння (departure, n).
- Exercise: Fill-in — "Buy a ticket" — 6 items: Один ___ до Харкова, будь ласка. / Скільки ___ квиток? / Коли ___ потяг? etc. (fills: квиток, коштує, наступний).
- P2 (~110 words): On the vehicle / navigating — five phrases for during the journey. «Яка це зупинка?» (What stop is this?), «Мені виходити тут?» (Do I get off here?), «Вибачте, як дістатися до вокзалу?» (Excuse me, how do I get to the station?), «Їдьте прямо» (Go straight), «Поверніть направо / наліво» (Turn right / left). Real-world note: on Kyiv metro, stop names are announced — learners can listen for «Наступна станція — Хрещатик». Vocabulary: прямо (straight), напра́во (right), налі́во (left), діста́тися (to get to — imperfective, used in questions).
- Exercise: Fill-in — "Ask for directions" — 6 items: Як дістатися до ___? (fills: метро, вокзалу, центру, готелю, аеропорту, зупинки).
- P3 (~110 words): Putting it together — short narration: Марко gets off the train at Kyiv Central (Київ-Пасажирський). He asks a passer-by: «Вибачте, як дістатися до метро?» / «Прямо, потім направо. П'ять хвилин». He buys a metro token: «Один жетон, будь ласка. Скільки коштує?» / «Вісімнадцять гривень». Он enters: «Яка це станція?» / «Вокзальна». He smiles — he did it! Vocabulary recycled: жетон (metro token, m), станція (station, f).

---

## Підсумок (~330 words total)

- P1 (~80 words): Recap paragraph — Transport in Ukrainian cities is rich: автобус, тролейбус, трамвай, маршрутка in most cities; метро in Kyiv, Kharkiv, Dnipro. Intercity: потяг (trains are popular — Укрзалізниця connects all major cities), літак (for longer distances). Reinforce: two words never change — метро and таксі — so they always take «на».
- P2 (~100 words): Pattern summary — explicit side-by-side comparison. Left column (їхати + instrumental): автобусом, тролейбусом, трамваєм, маршруткою, потягом. Right column (їхати на + noun): на метро, на таксі, на машині. Rule of thumb presented as a mnemonic: «If the word ends in -с, -й, -г, -а → it changes → use the -ом/-ею form. If the word sounds the same in all contexts (метро, таксі) → use на».
- P3 (~150 words): Self-check — bulleted Q&A list (not prose):
  - Як сказати «by bus»? → автобусом
  - Як сказати «by metro»? → на метро
  - Як запитати про зупинку? → Де зупинка автобуса?
  - Як купити квиток? → Один квиток до ___, будь ласка.
  - Як запитати ціну? → Скільки коштує квиток?
  - Як запитати час відправлення? → О котрій відправлення?
  - Як запитати, як дістатися? → Як дістатися до ___?
  - Як сказати «turn right»? → Поверніть направо.
  - Challenge: How does Марко get from Boryspil airport to his hotel using two types of transport? Write 2 sentences using їхати.
- Exercise (activities from plan, placed at section end):
  - Quiz — "Which transport?" — 8 items: Match situation to transport (e.g., «Потрібно перетнути місто швидко і дешево» → метро; «Немає квитка, швидко треба» → таксі).

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
