<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок — Summary'
- FIX: Too short: 995 words (target: 1200, minimum: 1020)
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

Write the full prose content for module **37: I Eat, I Drink** (A1, A1.6 [Food and Shopping]).

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
module: a1-037
level: A1
sequence: 37
slug: i-eat-i-drink
version: '1.2'
title: I Eat, I Drink
subtitle: Я їм хліб, п'ю каву — accusative for what you eat and drink
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Conjugate їсти and пити in present tense
- Use accusative case for inanimate direct objects (Я їм хліб, п'ю каву)
- Recognize feminine accusative ending change (-а → -у): кава → каву, вода → воду
- Describe eating and drinking habits using accusative
dialogue_situations:
- setting: 'Lunch break at work — unpacking lunch boxes: Я їм бутерброд (m, sandwich)
    і п''ю чай (m, tea). А ти? Я їм салат (m) і п''ю каву (f, coffee). Also: яблуко
    (n), банан (m), вода (f), сік (m, juice).'
  speakers:
  - Колега 1
  - Колега 2
  motivation: 'Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Breakfast conversation: — Що ти їш на сніданок? — Я їм кашу і п''ю
    каву. — А Олена? — Вона їсть хліб з маслом і п''є чай. — А діти? — Вони їдять
    яйця і п''ють молоко. Full conjugation of їсти and пити in natural context.'
  - 'Dialogue 2 — At lunch: — Що ви їсте на обід? — Ми їмо суп і салат. — А що п''єте?
    — Ми п''ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Review of їсти/пити
    with plural subjects.'
- section: Їсти і пити (To Eat and To Drink)
  words: 300
  points:
  - 'Conjugation of їсти (irregular — NOT Group I or II): я їм, ти їси, він/вона їсть,
    ми їмо, ви їсте, вони їдять. Conjugation of пити (Group I): я п''ю, ти п''єш,
    він/вона п''є, ми п''ємо, ви п''єте, вони п''ють. Both are essential daily verbs
    — high frequency.'
  - 'Ukrainian school approach (Grade 4 — знахідний відмінок): ''Бачу що? кого?''
    — the accusative answers ''what do I see/eat/drink?'' Я їм (що?) хліб. Я п''ю
    (що?) каву. The question що? triggers accusative for inanimate objects.'
- section: Знахідний відмінок — неживе (Accusative Inanimate)
  words: 300
  points:
  - 'Accusative for inanimate nouns — what changes: Masculine inanimate: NO CHANGE
    (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п''ю
    сік). Neuter: NO CHANGE (= nominative). молоко → молоко (Я п''ю молоко), яйце
    → яйце (Я їм яйце).'
  - 'Feminine -а → -у (THE key change at A1): кава → каву (Я п''ю каву), вода → воду
    (Я п''ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю
    (Я їм картоплю). Pattern: feminine nouns ending in -а change to -у, ending in
    -я change to -ю. This is the ONLY accusative change learners need now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative inanimate summary: Masculine/Neuter: no change (хліб, молоко stay
    the same). Feminine -а → -у, -я → -ю (кава → каву, картопля → картоплю). Test:
    Я їм ___ (риба → рибу). Я п''ю ___ (вода → воду). Self-check: Say 3 things you
    eat and 3 things you drink today. Use the correct accusative form for each.'
vocabulary_hints:
  required:
  - їсти (to eat — irregular)
  - пити (to drink)
  - їм (I eat)
  - п'ю (I drink)
  - каву (coffee — accusative)
  - воду (water — accusative)
  - рибу (fish — accusative)
  recommended:
  - кашу (porridge — accusative)
  - картоплю (potato — accusative)
  - сметану (sour cream — accusative)
  - їсть (he/she eats)
  - п'є (he/she drinks)
  - їдять (they eat)
  - п'ють (they drink)
activity_hints:
- type: fill-in
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
- type: quiz
  focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
- type: fill-in
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
- type: group-sort
  focus: Sort nouns based on how they change in the accusative case (inanimate)
  items: 8
  groups:
  - name: Змінюється (-у/-ю)
    items:
    - кава
    - вода
    - риба
    - каша
  - name: Не змінюється (як у називному)
    items:
    - хліб
    - сік
    - молоко
    - м'ясо
connects_to:
- a1-038 (At the Cafe)
prerequisites:
- a1-036 (Food and Drink)
grammar:
- 'Accusative inanimate: masculine/neuter = nominative, feminine -а→-у, -я→-ю'
- Conjugation of їсти (irregular) and пити (Group I)
- Question що? as accusative trigger for inanimate
register: розмовний
references:
- title: ULP Season 1, Episode 32
  url: https://www.ukrainianlessons.com/episode32/
  notes: Accusative case introduction — inanimate objects.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу що? кого?'

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

**Confirmed (14/14):**
- їсти → verb ✅
- пити → verb ✅
- їм → їсти (verb) ✅ *(note: also matches вони/noun — context disambiguates)*
- п'ю → пити ✅
- каву → кава (noun) ✅
- воду → вода (noun) ✅
- рибу → риба (noun) ✅
- кашу → каша (noun) ✅
- картоплю → картопля (noun) ✅
- сметану → сметана (noun) ✅
- їсть → їсти ✅
- п'є → пити ✅
- їдять → їсти ✅
- п'ють → пити ✅

**Not found:** none — all 14 forms are in VESUM.

---

## Textbook Excerpts

### Section: Їсти і пити — conjugation table
> *"Форми теперішнього часу від дієслова їсти мають іншу систему закінчень: їм, їси, їсть, їмо, їсте, їдять."*
> Source: **Заболотний, Grade 7** (Зверніть увагу! box)

> Full paradigm table confirmed:
> | Особа | Однина | Множина |
> |-------|--------|---------|
> | 1-ша | їм | їмо |
> | 2-га | їси | їсте |
> | 3-тя | їсть | їдять |
> Source: **Litvinova, Grade 7, §10** (Tier 1); **Avramenko, Grade 7, §33** (Tier 1) — both confirm the same paradigm.

> *"Дієслова дати, їсти та похідні від них… належать до окремого типу дієвідмінювання."*
> Source: **Litvinova, Grade 7** — confirms їсти is NOT Group I or II.

### Section: Діалоги — breakfast/lunch conversations
> *"Привчіть себе їсти не раніше, ніж через пів години після пробудження… Потім займіться звичними справами: прийміть душ, одягніться… Ось тепер – снідайте."*
> Source: **Заболотний, Grade 5, p.150** — natural breakfast context for dialogue framing.

> *"Кони попили (воду, води). Діти поїли (кашу, каші)."*
> Source: **Заболотний, Grade 6** — direct accusative vs. genitive contrast with їсти/пити and feminine nouns.

### Section: Знахідний відмінок — іменник
> *"Іменник у формі знахідного відмінка означає предмет, на який спрямована дія, і в реченні виступає додатком."*
> Source: **Заболотний, Grade 6, §** (Tier 2)

> *"Прямий додаток — знахідний відмінок без прийменника: Як прати й сушити джинси?"*
> Source: **Avramenko, Grade 8, §34–35** (Tier 1) — confirms the що? question triggers accusative without preposition.

> Grade 4 textbook models: *"Початкова форма (що? лава). … Відмінок (знахідний)."* — shows how Ukrainian schools introduce accusative from Grade 4.
> Source: **Ponomarova, Grade 4** (Tier 2)

### Section: Підсумок / self-check
> *"Спишіть сполучення, ставлячи іменники в потрібному відмінку… Кони попили (воду, води). Діти поїли (кашу, каші)."*
> Source: **Заболотний, Grade 6** — ideal summary/self-check template.

---

## Grammar Rules

- **їсти conjugation (special class):** Правопис §§ on orthography do not cover verb paradigms (morphology is in grammar books, not правопис). **Authoritative source is textbooks:** Avramenko Grade 7 §33 and Litvinova Grade 7 §10 both give the full paradigm: їм / їси / їсть / їмо / їсте / їдять.

- **⚠️ CRITICAL — 2nd person singular:** The correct form is **їси** (not *їш*). Антоненко-Давидович warns explicitly: *"ти даси, їси, відповіси, розповіси — а не даш, їш, відповіш, як то часом, надто в західних областях України, кажуть."* The plan correctly lists **ти їси** ✅ — but the dialogue section does NOT include a ти їси example. Recommend including at least one ти-form to pre-empt the common western Ukrainian error.

- **Accusative inanimate — feminine:** правопис does not govern this (it is morphology). Textbook rule (Заболотний Grade 6, Litvinova Grade 6): *feminine nouns ending in -а → -у; ending in -я → -ю* in accusative inanimate. **The plan's formulation matches exactly.** Masculine and neuter inanimate = no change (= nominative). ✅

- **Accusative vs. Partitive Genitive — potential trap:** Avramenko Grade 8 notes: *"Може, ми вип'ємо кави?"* — the genitive here marks a partial amount ("some coffee"), while accusative marks the whole object. The plan keeps it simple by using only accusative (Я п'ю воду/каву) which is correct. **Do NOT introduce the partitive distinction at A1** — it is not in scope.

---

## Calque Warnings

- **замовляй!** (in Dialogue 2): ✅ **NATURAL** — Антоненко-Давидович §142 confirms: *замовити/замовляти* = "to order (food, goods)" is correct Ukrainian. The Russianism is *заказати* (= "to order" in the Russian sense) — which is WRONG and means "to forbid" in Ukrainian. The dialogue correctly uses **замовляй** ✅.

- **їсти + accusative:** ✅ Natural. No calque. Textbooks confirm *їсти що? → знахідний* as standard Ukrainian.

- **хліб з маслом** (Dialogue 1): ✅ **NATURAL** — Антоненко-Давидович uses *хліб* examples naturally throughout; no calque flag. The construction *X з Y* (bread with butter) is standard Ukrainian.

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| їсти | **A1** | ✅ On target |
| пити | **A1** | ✅ On target |
| кава | **A1** | ✅ On target |
| вода | **A1** | ✅ On target |
| картопля | **A1** | ✅ On target |
| риба | **A1** | ✅ On target |
| молоко | **A1** | ✅ On target |
| сметана | **A1** | ✅ On target |
| каша | **A2** | ⚠️ One level above — see note below |

**Note on каша (A2):** PULS classifies каша as A2, but it is a foundational Ukrainian food item and appears in Grade 4-5 textbooks naturally. It is contextually appropriate for A1.6 (food module) and serves the accusative pattern (каша → кашу) perfectly. **Recommend keeping it** — flag it in the словнік tab with a note that it's a culturally essential word introduced slightly early.

---

## Summary for Writer

✅ **All 14 vocabulary forms verified in VESUM** — safe to use  
✅ **Conjugation paradigm confirmed** by two independent Tier 1 Grade 7 textbooks (Litvinova, Avramenko)  
✅ **замовляй is natural Ukrainian** — not a calque  
✅ **All vocabulary is A1 level** (except каша = A2 — acceptable exception for food module)  
⚠️ **Include at least one ти їси example** in dialogues — preempts the common *їш* error flagged by Антоненко-Давидович  
⚠️ **Do NOT introduce partitive genitive** (вип'ємо кави) — accusative only at A1
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
# Verified Knowledge Packet: I Eat, I Drink
**Module:** i-eat-i-drink | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 49
> **Score:** 0.25
>
> 49
>  § 19.  Омоніми
> 1.	Прочитайте діалог і виконайте завдання. 
> — Алло! Привіт, Олю! Що робиш?
> — Обідаю. 
> — А що ти їси? 
> — Лисички.
> — А хіба цих тварин їдять?! 
> — Відколи гриби стали тваринами? 
> — Нічого не розумію…
> А. Через яке слово виникло непорозуміння між подругами? 
> Б. Які значення має це слово?
> Омоніми — це слова, однакові за звучанням і написанням, але різні за 
> лексичним значенням: кран — трубка із затвором для виливання ріди-
> ни і кран — механізм для піднімання й переміщення вантажів. 
> Здебільшого омоніми утворюються внаслідок випадкового звукового 
> збігу власне українського й іншомовного слів, наприклад: лава — різ-
> новид меблів і лава (з іт.) — розплавлена вулканічна маса. 
> 2.	Прочитайте речення та виконайте завдання. 
> 1.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 236
> **Score:** 0.33
>
> 236
> Відомості із синтаксису й пунктуації. Складне речення
> 4. Яка інформація з  тексту була для вас новою?
> 5. Пригадайте, які хімічні досліди на кухні (з перерахованих у тексті чи інші) 
> проводили ви . Розкажіть про це друзям, використовуючи складні речення .
> Вправа 380
> 1. Прочитайте рекомендації щодо здорового сніданку .
> СМУЗІ
> z
> z яблуко — 1 шт.,
> z
> z банан — 1 шт.,
> z
> z склянка води,
> z
> z кілька заморожених ягід 
> (на ваш смак),
> z
> z ложка лляного насіння.
> ОМЛЕТ З ОВОЧАМИ 
> ТА ЗЕЛЕННЮ
> z
> z яйця — 1—2 шт.,
> z
> z молоко — 2 ст. л.,
> z
> z овочі на вибір — 50 г,
> z
> z сіль, перець за смаком, 
> зелень.
> СИРНИКИ
> z
> z кисломолочний сир 5—9 % 
> жирності — 200 г,
> z
> z яйце — 1 шт.,
> z
> z манка або борошно — 
> 2 ст. л.,
> z
> z ванільний цукор 
> (за бажанням) — 1 ч. л.
> 2.

> **Source:** , Grade 4
> **Section:** Сторінка 53
> **Score:** 0.25
>
> « а
> Зміню вання ім енників за числами
> 109. Прочитайте вірш Надії Красоткіної.
> Думала Оленкатак: «Щоб здоров’я мати,
> Треба їсти їй буряк, пити чай із м ’яти, 
> їсти супчики й борщі, вареники з сиром,
> І котлетки, й вергунці, але знати міру».
> •  Випишіть іменники, які вжиті в множині.
> І р  •  Поясніть правопис виділених іменників. Зробіть їх звуко-бук- 
> вений аналіз.
> 110. Прочитайте текст, розкриваючи дужки.
> Україна завжди славилася сво­
> єю кухнею. її (страва) знані дале­
> ко за межами країни. Усім відомі 
> українські (борщ), (галушка), (ва­
> реник), (корж), (калач), (гречаник).
> У багатьох стравах вдало сполу­
> чаються овочі та м ’ясо. Смачні 
> (голубець) з м’ясом, (перець), фаршировані рисом і 
> м ’ясом.

## Їсти і пити (To Eat and To Drink)

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 232
> **Score:** 0.50
>
> 232
> Відомості із синтаксису й пунктуації. Складне речення
> Складне речення
> Вправа 374
> 1. Прочитайте речення .
> Іван добре їсть. Іван добре 
> працює.
> Хто добре їсть, той добре 
> працює (Нар. тв.).
> Наше здоров’я залежить 
> від продуктів. Ми щодня спо-
> живаємо продукти.
> Наше здоров’я залежить 
> від продуктів, які ми спожи-
> ваємо щодня.
> 2. Перепишіть і підкресліть у реченнях граматичні основи (підмети й при-
> судки) .
> 3. Зробіть висновки, чим відрізняються речення за  будовою і  за  змістом .
> За будовою речення поділяємо на  прості та  складні .
> Простими називаємо речення, що мають одну граматичну 
>  основу (дивіться приклади з  лівої колонки) .
> Складними називаємо речення, що мають дві граматичні ос-
> нови або більше (дивіться приклади з  правої колонки) .

## Знахідний відмінок — неживе (Accusative Inanimate)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 185
> **Score:** 0.25
>
> 185
> 185
> § 94.  Відмінювання  займен­ників.  Приставний  н  у  формах  особових займенників
> 4.	 Прочитайте речення. Визначте відмінок кожного займенника (усно). 
> 1. Чистим зерном сійте поле, то вродить хліб, як море, а нечистим посієте — 
> собі шкоди надієте. 2. Який порядок у себе заведеш, таке й життя проведеш 
> (Нар. тв.).  
> Відмінювання питальних і відносних займенників
> Займенники який, чий, котрий змінюємо за родами, числами й від­
> мінками; займенники хто, що, скільки — тільки за відмінками.
> 5.	 «Лінгвістичне спостереження». Визначте закінчення у всіх формах за-
> йменників чий, чия, чиє, чиї (усно).
> Однина
> Множина
> Н. в.
> хто
> що
> чий
> чиє
> чия
> чиї
> Р. в.
> кого
> чого
> чийого
> чийого
> чиєї
> чиїх
> Д. в. 
> кому
> чому
> чиєму
> чиєму
> чиїй
> чиїм
> Зн. в. кого
> що
> чий / чийого чиє
> чию
> чиї / чиїх
> Ор. в.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 57
> **Score:** 0.50
>
> 57
> 57
> § 30.  Похідні  і  непохідні  слова.  Твірне  слово
> 4.	 Виконайте завдання в тестовій формі.
> 1.	 Непохідним є слово
> А	 чайник
> Б	 лампа
> В	 несмак 
> Г	 дубок
> 2.	 Твірне й похідне від нього слово записано в рядку
> А	 кит → Китай 
> Б	 кава → кавалер 
> В	 мис → миска 
> Г	 сад → садок 
> 3.	 Твірні й похідні від них слова записано в усіх рядках, ОКРІМ
> А	 сир → сироп 
> Б	 читач → читачка
> В	 брат → братство 
> Г	 жовтий → жовтенький 
> 5.	 Прочитайте текст і виконайте завдання.
> Не було ще такого літнього ранку, щоб дід Арсен усидів удома. Де там! 
> Як тільки над обрієм зажевріє велика досвітня зоря, уже Арсен на ногах.

## Підсумок — Summary

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 14
> **Score:** 0.50
>
> 14
> ТЕКСТ. РЕЧЕННЯ. СЛОВО (ПОВТОРЕННЯ)
> 2. Прочитайте речення та виконайте завдання. У віддаленій перспективі в таких пернатих можуть сформуватися так 
> звані «крила ангела», що стирчать у горизонтальній площині, а не обтічно 
> лежать на тілі. Більшість птахів із цією вадою не вміють літати. Хліб — шкідлива їжа для диких водоплавних птахів, що не має ніякої 
> поживної цінності, окрім калорій. Постійне підгодовування хлібом зму-
> шує їх покладатися на людину як на джерело корму, а не на свій природ-
> ний раціон. Отже, хлібна дієта — це легкий доступ птахів до нездорового 
> раціону, унаслідок якого вони недоотримують поживні речовини. Треба пам’ятати: якщо ми перестанемо під-
> годовувати водоплавних птахів хлібом, вони 
> не зникнуть.

> **Source:** savchenko, Grade 4
> **Section:** Сторінка 38
> **Score:** 0.25
>
> 38
> БЕЗ ТРУДА НЕМА ПЛОДА
> Народна притча
> Якось один чоловік почастував вовка хлібом.
> — Ну й смачний! — похвалив вовк. А далі питає:
> — А де ти його взяв?
> — Та де взяв! Землю виорав…
> — І все?
> — Ні, потім посіяв жито…
> — І вже маєш хліб?
> — Та ні, — каже чоловік. — Почекав, поки жито зі-
> йшло, виросло, поспіло. Потім я його вижав, змоло-
> тив, намолов борошна, замісив тісто й аж тоді напік 
> буханців.
> — Що смачний хліб, то смачний, — сказав вовк. —
> Та скільки ж коло нього походити треба!
> — Твоя правда, — сказав чоловік. — Клопоту багато.

## Grammar Reference


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Речення, його граматична основа
> **Source:** МійКлас — [Речення, його граматична основа](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/rechennia-iogo-gramatichna-osnova-pidmet-i-prisudok-39372)

### Теорія:

*www.ua.pistacja.tv*  
Речення
Реченням називаємо одне або кілька слів, що виражають закінчену думку.
Саме за допомогою речень ми спілкуємось, висловлюємо прохання, наказ, виражаємо емоції, повідомляємо інформацію.
Приклад:
- Весна іде, красу несе \(Нар. творчість\). 
- Ліс. Тиша. Благодать. 
Слова в реченні зв'язані між собою **за змістом** і **граматично**. **Граматичний зв'язок** — це поєднання за допомогою **закінчень** і **службових слів**. На початок і кінець речення вказує **інтонація**. Між реченнями робимо **паузи**.
Ознаки речення
1. Речення відображає дійсність. Інформація **стверджується** або **заперечується**, сприймається як **р

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Їсти і пити (To Eat and To Drink)` (~300 words)
- `## Знахідний відмінок — неживе (Accusative Inanimate)` (~300 words)
- `## Підсумок — Summary` (~300 words)
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
  1. **Lunch break at work — unpacking lunch boxes: Я їм бутерброд (m, sandwich) і п'ю чай (m, tea). А ти? Я їм салат (m) і п'ю каву (f, coffee). Also: яблуко (n), банан (m), вода (f), сік (m, juice).**
     Speakers: Колега 1, Колега 2
     Why: Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)

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

**Required:** їсти (to eat — irregular), пити (to drink), їм (I eat), п'ю (I drink), каву (coffee — accusative), воду (water — accusative), рибу (fish — accusative)
**Recommended:** кашу (porridge — accusative), картоплю (potato — accusative), сметану (sour cream — accusative), їсть (he/she eats), п'є (he/she drinks), їдять (they eat), п'ють (they drink)

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

- P1 (~20 words): Brief scene-setter — two colleagues at lunch break, unpacking food, establishing natural context for їсти/пити.
- Dialogue 1 (~120 words): Breakfast conversation (3–4 turns). — Що ти їш на сніданок? — Я їм кашу і п'ю каву. — А Олена? — Вона їсть хліб з маслом і п'є чай. — А діти? — Вони їдять яйця і п'ють молоко. Introduces full paradigm of їсти and пити across я/вона/вони in natural flow.
- P2 (~15 words): Short bridge note — same verbs, now with plural subjects at lunch.
- Dialogue 2 (~120 words): Lunch scene (4–5 turns). — Що ви їсте на обід? — Ми їмо суп і салат. — А що п'єте? — Ми п'ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Reinforces ми/ви forms and introduces воду/сік as direct objects in accusative.
- P3 (~55 words): Post-dialogue reading comprehension note — ask learners: "Що їсть Олена? Що п'ють діти? Що їмо ми на обід?" — three questions anchoring the dialogues to accusative use without yet naming the grammar rule.

## Їсти і пити (~320 words total)

- P1 (~80 words): Present-tense conjugation of їсти (irregular). Full table: я їм, ти їси, він/вона їсть, ми їмо, ви їсте, вони їдять. Highlight irregularity — this verb does NOT follow Group I or II patterns. Three example sentences: Я їм хліб. Він їсть рибу. Вони їдять кашу.
- P2 (~80 words): Present-tense conjugation of пити (Group I). Full table: я п'ю, ти п'єш, він/вона п'є, ми п'ємо, ви п'єте, вони п'ють. Note the apostrophe before ю/є/є (п'ю, п'єш, п'є) — a Ukrainian spelling rule. Three example sentences: Я п'ю каву. Вона п'є воду. Вони п'ють сік.
- P3 (~80 words): Side-by-side comparison of the two verbs — parallel columns showing я їм / я п'ю, ти їси / ти п'єш, etc. Emphasize: їсти is the exception to learn by heart; пити is a regular model. Both are extremely high-frequency daily verbs — you will use them every single day.
- P4 (~80 words): Ukrainian school concept (Grade 4 approach) — the question що? as the trigger for accusative. Я їм (що?) хліб. Я п'ю (що?) каву. When you eat or drink something, ask "що?" — the answer is always in the accusative case. This is the bачу що? / їм що? / п'ю що? rule from Ukrainian textbooks. Frame it as a habit: always ask "що?" before choosing the noun ending.
- Exercise: fill-in (8 items) — Conjugate the verbs їсти and пити. Blanks: Я {їм} суп. / Ми {п'ємо} чай. / Вона {їсть} хліб. / Вони {п'ють} воду. / Ти {їси} рибу? / Ви {п'єте} каву? / Він {п'є} сік. / Вони {їдять} кашу.

## Знахідний відмінок — неживе (~330 words total)

- P1 (~70 words): Introduce the accusative case for inanimate nouns — what changes and what doesn't. Masculine inanimate: NO change (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п'ю сік), банан → банан (Я їм банан). Neuter: NO change. молоко → молоко (Я п'ю молоко), яйце → яйце (Я їм яйце). Rule: masculine and neuter inanimate nouns look exactly like nominative after їсти/пити.
- P2 (~100 words): THE key change — feminine -а → -у, -я → -ю. Eight examples: кава → каву (Я п'ю каву), вода → воду (Я п'ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю (Я їм картоплю), сметана → сметану (Я їм сметану), каша → кашу, земля → землю. Pattern stated explicitly: -а becomes -у; -я becomes -ю. Emphasize: this is the ONLY accusative ending change learners need at A1. Everything else stays the same.
- P3 (~60 words): Quick contrast drill in prose — three pairs side by side showing before/after: [Nominative: кава — Accusative: каву] / [Nominative: вода — Accusative: воду] / [Nominative: картопля — Accusative: картоплю] vs. [Nominative: хліб — Accusative: хліб] / [Nominative: сік — Accusative: сік] / [Nominative: молоко — Accusative: молоко]. Learner sees the pattern visually before the exercises.
- P4 (~50 words): Natural sentences wrapping it all together — four sentences mixing genders: Я їм рибу і хліб. Вона п'є каву і воду. Ми їмо кашу і яйця. Вони п'ють сік і молоко. Learner reads and identifies which nouns changed and why.
- P5 (~50 words): Laysense mnemonic — "If a noun ends in -а or -я (like кав**а**, вод**а**, картопл**я**), swap the ending for -у or -ю when you eat or drink it. Everything else stays the same. One rule. That's it."
- Exercise 1: fill-in (8 items) — Form the accusative. Blanks: Я їм (риба) {рибу}. / Вона п'є (вода) {воду}. / Він їсть (хліб) {хліб}. / Ми п'ємо (молоко) {молоко}. / Вони їдять (каша) {кашу}. / Ти п'єш (кава) {каву}. / Я їм (суп) {суп}. / Вона їсть (картопля) {картоплю}.
- Exercise 2: quiz (6 items) — Select the correct accusative form. Questions: Я п'ю… (каву / кава / кави) / Він їсть… (рибу / риба / рибі) / Ми п'ємо… (сік / соку / соком) / Вона їсть… (м'ясо / м'ясу / м'яса) / Вони п'ють… (воду / вода / воді) / Ти їш… (кашу / каша / каші).
- Exercise 3: group-sort (8 items) — Sort nouns by accusative behavior. Group "Змінюється (-у/-ю)": кава, вода, риба, каша. Group "Не змінюється (як у називному)": хліб, сік, молоко, м'ясо.

## Підсумок (~150 words total)

- P1 (~150 words): Recap of the two verbs — їсти (irregular: їм, їси, їсть, їмо, їсте, їдять) and пити (regular: п'ю, п'єш, п'є, п'ємо, п'єте, п'ють). Recap of accusative rule — masculine/neuter inanimate: no change (хліб, суп, молоко, сік stay the same); feminine -а → -у, -я → -ю (кава → каву, вода → воду, картопля → картоплю). Self-check bulleted list:
  - Я їм ___ (риба → ?)  → **рибу**
  - Я п'ю ___ (вода → ?) → **воду**
  - Вони їдять ___ (хліб → ?) → **хліб**
  - Вона п'є ___ (кава → ?) → **каву**
  
  Final prompt: Say three things you eat today and three things you drink. Use the correct accusative form for each. (Наприклад: Я їм кашу, рибу і хліб. Я п'ю каву, воду і сік.)

Grand total: ~1330 words
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
