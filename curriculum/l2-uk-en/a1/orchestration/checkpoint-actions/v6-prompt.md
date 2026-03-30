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

Write the full prose content for module **21: Checkpoint: Actions** (A1, A1.3 [Actions]).

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
module: a1-021
level: A1
sequence: 21
slug: checkpoint-actions
version: '1.1'
title: 'Checkpoint: Actions'
subtitle: Can you say what you do, want, and ask questions?
focus: review
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Demonstrate ability to conjugate Group I and Group II verbs
- Use modal verbs (хотіти, могти, мусити) with infinitives
- Ask questions using all 7 question words
- Describe a routine using reflexive verbs and sequence words
- Combine A1.1-A1.3 skills in connected speech
dialogue_situations:
- setting: Job interview — describing your typical day, skills, and schedule
  speakers:
  - Кандидат (applicant)
  - Менеджер
  motivation: 'Consolidation: verbs, modals, questions, reflexives'
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M15-M20: Can you say what you like? (M15) Can you conjugate
    Group I verbs? (M16) Can you conjugate Group II verbs? (M17) Can you say what
    you want, can, and must? (M18) Can you ask questions? (M19) Can you describe your
    morning? (M20)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M15-M20. No
    new words. The learner reads aloud. Content: a person describes their day — morning
    routine, work, hobbies. Example: Я прокидаюся о сьомій. Потім вмиваюся і снідаю.
    Я працюю в офісі. Я люблю читати. Увечері я дивлюся фільм.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.3: 1. Infinitive: -ти (читати, говорити, хотіти) 2. Group
    I: -ю, -єш, -є, -ємо, -єте, -ють 3. Group II: -ю/-у, -иш, -ить, -имо, -ите, -ять
    4. Modals: хочу/можу/мушу + infinitive 5. Questions: хто, що, де, куди, коли,
    чому, як 6. Negation: не + verb; double negation (ніхто не) 7. Reflexive: verb
    + ся (прокидаюся, вмиваюся)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A complete conversation combining all A1.3 skills: Meeting + plans scenario.
    — Привіт! Що ти робиш? — Я читаю книгу. А ти? — Я хочу гуляти. Ти можеш?
    — Не можу, мушу працювати. — Шкода! Коли ти працюєш? — До шостої. — Добре, тоді
    гуляємо ввечері! Uses: both verb groups, modals, questions, negation.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.3 achievement summary: You can now talk about actions in Ukrainian. You can
    conjugate verbs in two groups. You can express wants, abilities, and obligations.
    You can ask questions and negate statements. You can describe your daily routine.
    Next: A1.4 — Time and Nature (time, days, weather).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Mixed conjugation: choose correct form for Group I and II verbs'
  items: 10
- type: fill-in
  focus: Complete the dialogue with modals, questions, and verb forms
  items: 8
- type: fill-in
  focus: 'Describe your day: morning routine → work → evening'
  items: 6
- type: group-sort
  focus: 'Sort verbs by group: Group I vs Group II vs Reflexive'
  items: 12
connects_to:
- a1-022 (What Time?)
prerequisites:
- a1-020 (My Morning)
grammar:
- 'Review: Group I and II conjugation'
- 'Review: modal verbs + infinitive'
- 'Review: question words and negation'
- 'Review: reflexive verbs and sequence words'
register: розмовний
references:
- title: Synthesis of M15-M20 content
  notes: No new material — review and integration of A1.3 phase.

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

### Batch 1 — Verb forms
- **Confirmed:** читати, говорити, хотіти, гуляти, прокидаюся (← прокидатися), вмиваюся (← вмиватися), снідаю (← снідати), працюю (← працювати), люблю (← любити), дивлюся (← дивитися), хочу (← хотіти/хтіти), можу (← могти), мушу (← мусити), мусити
- **Not found:** none

### Batch 2 — Nouns, question words, adverbs
- **Confirmed:** офіс, книга, фільм, ранок, хто, що, де, куди, ввечері, шкода, тоді, ніхто, привіт
- **Confirmed:** як, коли, чому — all found; note: `коли` matched 7 forms (incl. кіл-noun declensions as false positives), but коли (adv/conj "when") is fully standard Ukrainian
- **Not found:** none

**All 30 words confirmed in VESUM.**

---

## Textbook Excerpts

### Section: Граматика — Group I / Group II conjugation
> "І дієвідміна — Особові закінчення: -у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють)… ІІ дієвідміна — Особові закінчення: -у(-ю), -иш(-їш), -ить, -іть(-їть), -имо, -імо(-їмо), -ите(-їте), -ать(-ять)"
> Source: Karaman, Grade 10

> "Форму теперішнього часу мають лише дієслова недоконаного виду… Дієслова в теперішньому часі змінюються за особами та числами: пишу/роблю, пишеш/робиш, пише/робить, пишемо/робимо, пишете/робите, пишуть/роблять"
> Source: Litvinova, Grade 7 (tier 1)

⚠️ **WRITER FLAG — хотіти is Group I, not a simple Group II verb:** The Karaman textbook explicitly lists хотіти under **"Окремі дієслова" of Group I** (alongside гудіти, сопіти, іржати). Its forms are: хочу, хочеш, хоче, хочемо, хочете, хочуть — all Group I endings. The grammar summary must NOT list хотіти as Group II. The plan's modals (хочу/можу/мушу) are all Group I 1st-person forms — this is pedagogically fine, but the summary should clarify хотіти belongs to Group I.

### Section: Граматика — Reflexive verbs (-ся)
> "Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними: навчатися, закохатися… Уживається -ся(-сь) після інфінітивного суфікса -ти(-ть) або закінчення в особових формах дієслова: вмивати — вмиватися, взувати — взуватися."
> Source: Karaman, Grade 10

> "Дієслова на -ся, -сь виражають дію, спрямовану на самого виконавця (на самого себе)." (with pronunciation: шся → [с':а], -ться → [ц':а])
> Source: Kravtsova, Grade 4

### Section: Граматика — Infinitive
> "Початковою формою дієслова є інфінітив, тобто форма, що закінчується суфіксом -ти (ходити, бігати, малювати)… У дієсловах, які називають дію, спрямовану виконавцем на самого себе, суфікс інфінітива стоїть перед -ся: представлятися, фотографуватися."
> Source: Litvinova, Grade 7 (tier 1)

### Section: Граматика — Negation / Double negation
> "Ніхто не може змусити вас робити те, що ви вважаєте неправильним і непристойним." (zaperechnі zaimennyky + не = double negation pattern)
> Source: Litvinova, Grade 6

> "Заперечні займенники вказують на відсутність особи, предмета… Заперечні займенники утворюємо від питальних додаванням префікса ні: ніщо, ніхто, ніякий…" "Заперечні займенники з ні пишемо разом."
> Source: Zabolotnyi, Grade 6 (confirms ніхто не as correct double-negation)

### Section: Читання — daily routine vocabulary
> (читає/читають paradigm), temporal expressions (коли?), place (де? куди?)
> Source: Zabolotnyi, Grade 7 (tier 1) — verb tenses table; Kravcova Grade 2 — question words for sentences

### Section: Діалог — question words in conversation
> "Питальні займенники вживаються в питальних реченнях… хто? що? який? чий? котрий? скільки?" + interrogative adverbs де? куди? коли? чому? як? all confirmed as standard interrogative tools at this level.
> Source: Litvinova, Grade 6; Kravcova, Grade 2

---

## Grammar Rules

- **Infinitive suffix -ти**: confirmed by Litvinova Grade 7 — суфікс -ти is the standard literary form; forms ending in -ть (e.g., ходить instead of ходити) are dialectal/colloquial, not литературна норма — do NOT use -ть infinitives in the module.
- **Group I endings** (-ю/-у, -єш, -є, -ємо, -єте, -ють): confirmed Karaman Grade 10. Plan lists these correctly.
- **Group II endings** (-ю/-у, -иш, -ить, -имо, -ите, -ять): confirmed Karaman Grade 10. Plan lists these correctly.
- **Reflexive -ся**: always after the verb ending; after -ти in infinitives: вмивати+ся = вмиватися; after personal endings: вмиваєш+ся = вмиваєшся (pronunciation [с':а]).
- **Double negation**: ніхто не, нічого не = standard Ukrainian (NOT an error). Ukrainian requires both the negative pronoun AND не before the verb. This is correct and differs from English.
- **Negation не + verb**: written separately from the verb (не can + мушу → не можу, мушу, НЕ мушу).

*(Правопис query for дієслово returned no direct section match — rules are embedded in morphology chapters as confirmed via textbook RAG above.)*

---

## Calque Warnings

- **"дивлюся фільм"** → ✅ OK — natural Ukrainian; no calque. ("дивитися" correctly means "to watch"; Антоненко-Давидович uses "подивитись" without concern)
- **"приймати душ"** → ⚠️ NOT in the plan (plan uses вмиваюся = "wash up"), but if a writer adds it, flag it. The correct form is **брати душ** or simply **митися під душем**. The style guide confirms приймати is a problem verb (приймати участь → брати участь; приймати душ → брати душ).
- **"до шостої"** (dialogue: "Я працюю до шостої") → ✅ OK — Антоненко-Давидович confirms ordinal time expressions ("до шостої години") are standard Ukrainian. Do NOT write "до шість годин" (cardinal = calque from Russian "до шести часов"). "До шостої" is the correct Ukrainian form.
- **"снідаю"** (to eat breakfast) → ✅ OK — снідати is native Ukrainian; "їсти сніданок" would be a calque.

---

## CEFR Check

- **читати**: A1 ✅
- **працювати**: A1 ✅
- **хотіти**: A1 ✅
- **могти**: A1 ✅
- **гуляти**: A1 ✅
- **офіс**: A1 ✅
- **ранок**: A1 ✅
- **мусити**: ⚠️ **A2 per PULS** — This is a checkpoint module (M21) reviewing M18 content where мусити was introduced. Since it was taught in M18, reviewing it here is appropriate. However the writer should be aware it's technically A2-level vocabulary per PULS. Use sparingly and only in contexts that clearly echo M18.

**All other key vocabulary confirmed A1. No unexpected above-level words found.**

---

## Summary of Flags for Writer

| # | Flag | Severity | Recommendation |
|---|------|----------|----------------|
| 1 | **хотіти is Group I** (not irregular Group II) | 🔴 Must fix | List хотіти under Group I in the grammar summary. Its endings: хочу, хочеш, хоче… follow Group I paradigm. |
| 2 | **мусити is PULS A2** | 🟡 Awareness | Fine in this checkpoint (taught in M18); use confidently but note it's the upper edge of A1.3 scope. |
| 3 | **"приймати душ"** | 🟡 Avoid | If morning routine includes shower, write "митися під душем" or "брати душ" — never "приймати душ". |
| 4 | **Time expression** in dialogue | ✅ Confirmed | "до шостої" (ordinal) = correct Ukrainian. Do NOT use "до шість годин". |
| 5 | **-ть infinitive** | 🔴 Avoid | Only -ти infinitives in the module (ходити, not ходить). -ть is dialectal/colloquial. |
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
# Verified Knowledge Packet: Checkpoint: Actions
**Module:** checkpoint-actions | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Що ми знаємо? (What Do We Know?)

## Читання (Reading Practice)

## Граматика (Grammar Summary)

> **Source:** golub, Grade 5
> **Section:** Сторінка 199
> **Score:** 0.25
>
> 199
> 462   Прочитайте речення. Визначте комунікативний намір мовців 
> (прохання, умовляння, благання, клянчення чи пропозиція). 
> Обґрунтуйте свій вибір. На  яке прохання ви відгукнулися б? 
> Хто з мовців найкраще обґрунтував свої бажання?
> 1. Мамо, купи мені цю іграшку, купи, купи, купи, купи!!! 
> У Вероніки є точнісінько така, і я хочу! Купи-и-и-и!!! 
> 2. Дідусю, благаю, візьми мене з собою в похід на Говерлу! 
> Я ще там ніколи не був! 3. Тату, можна я не буду пристібатися 
> паском безпеки?! Я ж не маленький! Ну дозволь! Дозволь! 
> Глянь, не всі навіть дорослі пристебнуті! 4. «Дмитрику, цього 
> року так рясно вродили в нашому садку яблука! Допоможи 
> мені зібрати врожай! Мені самій не впоратися!» — мовила 
> бабуся. 5.

## Діалог (Connected Dialogue)

> **Source:** kravtsova, Grade 4
> **Section:** Сторінка 20
> **Score:** 0.50
>
> 1
> 53. 1. Прочитай текст. Що цікавого ти дізнався / дізналася?
> Хочеш здійснити подорож у часі? Тоді уяви себе в старовин­
> ному місті. Як ти гадаєш, де можна побачити найбільше людей? 
> Так, на торжку
> *!
> Ось стельмах продає вози та сани. Ось підійшов гутник. Він 
> виготовляє скло та вироби зі скла.
> Сьогодні все по-іншому. Відповідно — інші професії. Напри­
> клад, коуч або коучка допомагають іншим досягнути поставленої 
> мети. Маркетолог або маркетологйня організовують продаж 
> товарів чи послуг. Дієтолог або дієтологйня розробляють індиві­
> дуальні схеми харчування. А ким хочеш стати ти?
> 2. Знайди орфограми в тексті та поясни їхнє написання.
> 3. Виконай завдання на вибір.
> о Спиши абзац, у якому найбільше нових слів.
> о Спиши абзац, у якому найбільше застарілих слів.
> 54.

> **Source:** golub, Grade 5
> **Section:** Сторінка 129
> **Score:** 0.50
>
> 129
> подякувати
> звернутися 
> з проханням
> пояснити свій 
> учинок
> порадити
> поділитися 
> досвідом, 
> враженнями
> висловити 
> припущення
> За допомогою складних 
> речень можна реалізувати 
> будь-який комунікативний 
> намір:
> 1. Розкажи мені щось цікаве, щоб я слухав і мав з того 
> користь. 2. Люблю гортати старі книги, бо від них віє спо-
> коєм. 3. Дай мені розуміння і сили прощати, щоб і я був про-
> щений. 4. Люблю писати історії, у яких слова грають, як 
> інструменти в оркестрі. 5. Якщо зробиш крок назад, застряг-
> неш у вчорашньому дні (Із тв. М. Дочинця).
> 318   Виберіть один із текстів. Прочитайте його, дайте відповіді на за-
> питання і виконайте завдання. 
> І. Розгулявся січень хугою**. Усеньку добу висвистував гуч-
> ними вітрами. І в моє вікно почали стукати синички. Холодно 
> їм, голодно.

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

Букви ї, щ завжди позначають **два** звуки.
 
Буквосполучення дж, дз інколи позначають **два** звуки, а інколи — **один**.
 
В українській мові розрізняють тверді приголосні звуки \(22\) й м'які приголосні \(10\), голосні звуки \(6\).

### Дієслово: загальне значення, морфологічні ознаки
> **Source:** МійКлас — [Дієслово: загальне значення, морфологічні ознаки](https://www.miyklas.com.ua/p/ukrainska-mova/7-klas/diyeslovo-14736/diyeslovo-zagalne-znachennia-morfologichni-oznaki-sintaksichna-rol-38752)

### Теорія:

*www.ua.pistacja.tv*  
Загальне значення
**Звернімо увагу на слова у двох стовпчиках:**
 

| *** боротьба  *** |  *** боротися  *** | 
|---|---|
|  ***спів*** |   ***заспівати*** | 
|  ***синій*** |   ***синіти*** | 
| *** зелений*** |   ***зазеленіти  *** | 
*** *** 
**Якщо порівняти ці слова як частини мови, зробимо висновок:**
- слова «боротьба», «спів» означають назву дії і відповідають на питання ***що?***, отже,  це іменники;

- слова «синій», «зелений» вказують на ознаку і відповідають на питання ***який?***, отже, це прикметники;

- слова «боротися», «синіти», «заспівати», «зазеленіти» означають дію предмета, відповідають на питання ***що робити? що зробити?***, отже, це дієслова.

### І і ІІ дієвідміни. Дієвідмінювання дієслів
> **Source:** МійКлас — [І і ІІ дієвідміни. Дієвідмінювання дієслів](https://www.miyklas.com.ua/p/ukrainska-mova/7-klas/diyeslovo-14736/i-i-ii-diyevidmini-diyevidminiuvannia-diyesliv-39539)

### Теорія:

*www.ua.pistacja.tv*  
Зміна дієслів за особами і числами називається **дієвідмінюванням.**
Розрізняють два типи дієвідмінювання — І \(першу\) і ІІ \(другу\) дієвідміни.
 
***Найпростіше визначити дієвідміну за закінченнями ***3\-ї особи множини ***теперішнього часу недоконаного виду чи майбутнього часу доконаного виду:***
- І дієвідміна — закінчення \-уть \(\-ють\): допомож\-уть, мрі\-ють;

- ІІ дієвідміна — закінчення \-ать \(\-ять\): стеж\-ать, говор\-ять.

---
**Total textbook excerpts found:** 6
**Grades searched:** 3, 4, 5
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
  1. **Job interview — describing your typical day, skills, and schedule**
     Speakers: Кандидат (applicant), Менеджер
     Why: Consolidation: verbs, modals, questions, reflexives

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

GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):
Present tense verbs, modals, questions, reflexives.

ALLOWED:
- Present tense conjugation (both groups: -ати and -ити)
- Modal verbs: хотіти, могти, мусити + infinitive
- Question words: Хто? Що? Де? Куди? Коли? Чому?
- Negation: не/ні
- Reflexive verbs (-ся/-сь)
- 'Мені подобається' as lexical chunk (NO dative grammar)

BANNED: Past/future tense, cases beyond nominative,
participles, passive voice, complex subordinate clauses

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
- P1 (~60 words): Framing paragraph — this checkpoint covers M15-M20 (A1.3 phase). Direct address to learner: "Before we start the next phase, let's see how much you already know." Sets up the self-check as a confidence builder, not a test. Examples: short statements — Я читаю, Він хоче спати, Вона прокидається.
- P2 (~160 words): Self-check block — 6 bulleted questions with YES/NO self-assessment. One bullet per module: (M15) Can you say what you like? "Я люблю каву. Мені подобається музика." (M16) Can you conjugate Group I verbs? "Я читаю / ти читаєш / він читає." (M17) Can you conjugate Group II verbs? "Я говорю / ти говориш / він говорить." (M18) Can you use modal verbs? "Я хочу їсти. Вона може допомогти. Він мусить працювати." (M19) Can you ask all 7 questions? "Хто? Що? Де? Куди? Коли? Чому? Як?" (M20) Can you describe your morning? "Я прокидаюся, вмиваюся, снідаю."

---

## Читання (~275 words total)
- P1 (~25 words): Introduction to the reading — learner reads aloud. Reminder: every word here is from M15-M20. No new vocabulary.
- Reading text (~180 words): A 10-sentence passage. Taras describes his day: "Мене звати Тарас. Я прокидаюся о сьомій годині. Спочатку вмиваюся і чищу зуби. Потім снідаю — я люблю каву і бутерброди. Я працюю в офісі. Моя робота починається о дев'ятій. Я можу читати документи і відповідати на листи. Увечері я хочу відпочивати. Я слухаю музику або дивлюся фільм. Я мушу лягати спати о десятій — завтра знову рано вставати." Covers: reflexives (вмиваюся, прокидаюся), Group I (читаю, слухаю, дивлюся), Group II (починається, відповідаю), modals (можу, хочу, мушу), sequence words (спочатку, потім, увечері).
- P2 (~70 words): Post-reading comprehension prompts (not activities — just think-aloud questions). "Що Тарас робить вранці? О котрій він починає працювати? Що він хоче робити увечері?" Learner answers mentally or aloud. Reminds them these question words (що, о котрій, коли) were from M19.

---

## Граматика (~220 words total)
- P1 (~50 words): Intro — one paragraph summarizing the logic of the A1.3 grammar system: Ukrainian verbs change form depending on who is doing the action. Two main patterns (дієвідміни). Modal verbs use the infinitive (-ти). Reflexive verbs add -ся. Questions use 7 fixed question words.
- P2 (~80 words): Conjugation table recap — Group I vs Group II side-by-side. Left column: читати — читаю, читаєш, читає, читаємо, читаєте, читають. Right column: говорити — говорю, говориш, говорить, говоримо, говорите, говорять. One sentence identifying the key signal: Group I ends in -ють (3pl), Group II in -ять. Mnemonic: "If they all '-ять' together, it's Group II."
- P3 (~55 words): Modal verbs recap — хотіти, могти, мусити always followed by infinitive (-ти). Three model sentences: Я хочу читати. Ти можеш говорити. Він мусить працювати. Negative: Я не хочу спати. Я не можу прийти. Note: мусити/мушу — stress on му́шу.
- P4 (~35 words): Reflexive verbs recap — verb + -ся signals action done to/by oneself. Four examples: прокидаюся, вмиваюся, одягаюся, називаюся. Pattern: regular conjugation + -ся appended.

---

## Діалог (~330 words total)
- P1 (~30 words): Setup — Оля зустрічає Максима в парку в суботу вранці. The dialogue combines ALL A1.3 skills in one natural conversation.
- Dialogue block (~240 words): 16-turn exchange.
  — Привіт, Максиме! Що ти тут робиш?
  — Привіт, Олю! Я гуляю. А ти?
  — Я теж хочу гуляти. Можна з тобою?
  — Звичайно! Ти часто тут гуляєш?
  — Так, зазвичай вранці. Я прокидаюся рано і люблю свіже повітря.
  — А я мушу вставати рано через роботу. Де ти працюєш?
  — Я працюю в лікарні. Я лікар. А ти?
  — Я вчитель. Я викладаю математику.
  — Цікаво! Тобі подобається твоя робота?
  — Так, дуже! Я люблю говорити з дітьми. А ти можеш розповісти про свій день?
  — Можу! Я прокидаюся о шостій, вмиваюся, снідаю. Потім їду на роботу.
  — Коли ти починаєш?
  — О восьмій. Мушу бути там вчасно!
  — А що ти робиш увечері?
  — Увечері я хочу відпочивати. Я читаю або слухаю музику. А ти?
  — Я теж люблю читати. Я зараз читаю цікаву книгу!
  Uses: Group I (гуляю, люблю, читаю, слухаю), Group II (говорю, викладаю, починаю), modals (хочу, можу, мушу), all key question words (що, де, коли, як), reflexives (прокидаюся, вмиваюся), sequence words (зазвичай, потім, увечері).
- P2 (~60 words): Post-dialogue analysis — two sentences pointing out patterns. "Notice how both verb groups appear naturally in this dialogue. Notice how modals always connect to an infinitive: мушу бути, хочу відпочивати, можу розповісти." Draws learner's attention to the grammar they just saw in action.

---

## Підсумок (~270 words total)
- P1 (~60 words): Achievement statement — "You have completed A1.3: Actions. This is a major milestone. You can now do six things in Ukrainian that are core to any conversation: describe actions, express wants and obligations, ask questions, use reflexive verbs, build a daily routine, and combine all of these in connected speech."
- P2 (~120 words): Bulleted recap of six A1.3 skills with one example sentence each:
  • **Дієслова І групи** — Я читаю книгу. Вони слухають музику.
  • **Дієслова ІІ групи** — Ти говориш добре. Вона вчить українську.
  • **Модальні дієслова** — Я хочу спати. Він може прийти. Ми мусимо працювати.
  • **Питальні слова** — Хто це? Що ти робиш? Де ти живеш? Куди ти йдеш? Коли починається? Чому ти мовчиш? Як ти себе почуваєш?
  • **Заперечення** — Я не хочу їсти. Ніхто не знає.
  • **Зворотні дієслова** — Я прокидаюся, вмиваюся, одягаюся.
- P3 (~90 words): Forward look — "In A1.4 — Time and Nature, you will learn to say what time it is (котра година?), name the days of the week and months, talk about the weather, and describe the seasons. These topics build directly on your verb skills: Зараз третя година. Сьогодні неділя. Надворі холодно. Восени я люблю гуляти в парку. You already have the verbs. Now you will add time, days, and nature to your Ukrainian world."

---

**Grand total: ~1315 words**
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
