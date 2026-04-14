<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing 2/6 required vocab: магазин → у/в магазині (shop), місто → у/в місті (city)
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

Write the full prose content for module **29: Where Is It?** (A1, A1.5 [Places]).

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
module: a1-029
level: A1
sequence: 29
slug: where-is-it
version: '1.1'
title: Where Is It?
subtitle: В школі, на роботі — the locative case
focus: grammar
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Use в/у and на + locative to answer Де? (Where?)
- Form basic locative endings for familiar nouns
- Distinguish в (inside) from на (on/at) with place vocabulary
- Use the Grade 4 helper word method: М. (на, у) — "на/у кому? на/у чому?"
dialogue_situations:
- setting: 'First week in a new city — asking a neighbor where to find: аптека (f,
    pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), лікарня (f,
    hospital), парк (m, park). В аптеці, на пошті, у банку.'
  speakers:
  - Новий мешканець (newcomer)
  - Сусід (neighbor)
  motivation: В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Where is everyone? (ULP Ep17 pattern): — Де Олена? — Вона в школі.
    — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — Вона на дивані!
    Locative case emerges naturally from answering ''Де?'''
  - 'Dialogue 2 — Describing locations: — Де ти живеш? — Я живу в Києві, на вулиці
    Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. City + street + building
    locations.'
- section: Місцевий відмінок (The Locative Case)
  words: 300
  points:
  - 'Grade 4 case system: helper word method (Захарійчук Gr4 p.74): М. = місцевий
    відмінок: на/у кому? на/у чому? The locative ALWAYS needs a preposition — в/у
    or на. В/у = inside: в школі, у банку, в магазині, у лікарні. На = on/at: на роботі,
    на вулиці, на площі, на уроці.'
  - 'Basic locative endings (most common patterns): Masculine: -і or -у — в парку,
    у банку, в офісі, на уроці. Feminine: -і — в школі, на роботі, у лікарні, на вулиці.
    Neuter: -і — в місті, на морі. Note: endings depend on the noun''s declension
    — learn the common places as fixed phrases for now.'
- section: В чи на? (В or На?)
  words: 300
  points:
  - 'General guide: В/у = enclosed spaces: в школі, в магазині, у банку, в лікарні,
    в кафе. На = open spaces, surfaces, events: на вулиці, на площі, на роботі, на
    концерті. Some are conventional: на пошті (not в пошті), на вокзалі (not в вокзалі).
    Learn each place with its preposition — like English ''at school'' vs ''in the
    office''.'
  - 'Country/city rule: В/у + country/city: в Україні, у Києві, у Львові, в Одесі.
    На + some special cases: на Хрещатику (on Khreshchatyk street). Remember: NEVER
    ''на Україні'' — it''s ЗАВЖДИ ''в Україні''. This is not just grammar — it''s
    a matter of respect and sovereignty.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Locative case = where something IS (static location). Де? → в/у + locative (inside)
    or на + locative (on/at). Helper word: М. (на, у) — на/у кому? на/у чому? Common
    places: в школі, на роботі, у банку, в парку, на вулиці. Self-check: Where are
    you right now? Where do you work? Where do you live?'
vocabulary_hints:
  required:
  - школа → в школі (school)
  - робота → на роботі (work)
  - банк → у банку (bank)
  - магазин → у/в магазині (shop)
  - вулиця → на вулиці (street)
  - місто → у/в місті (city)
  recommended:
  - парк → у/в парку (park)
  - лікарня → у/в лікарні (hospital)
  - кафе → у/в кафе (café — indeclinable)
  - площа → на площі (square)
  - вокзал → на вокзалі (train station)
  - пошта → на пошті (post office)
activity_hints:
- type: quiz
  focus: В or на? Choose the correct preposition for each place.
  items: 10
- type: fill-in
  focus: 'Answer Де?: Олена ___ (школа). Тарас ___ (робота).'
  items: 8
- type: match-up
  focus: 'Match nominative to locative: школа ↔ в школі'
  items: 8
- type: quiz
  focus: Where is it? Choose the correct locative form.
  items: 6
connects_to:
- a1-030 (My City)
prerequisites:
- a1-028 (Euphony)
grammar:
- 'Locative case: в/у + М.в. (inside), на + М.в. (on/at)'
- 'Helper word method: М. (на, у) — на/у кому? на/у чому?'
- 'Basic locative endings: -і (most common), -у (masculine some)'
- В Україні (never на Україні)
register: розмовний
references:
- title: Захарійчук Grade 4, p.74
  notes: 'Case system table: М.в. = на/у кому? на/у чому?'
- title: ULP Season 1, Episode 17
  url: https://www.ukrainianlessons.com/episode17/
  notes: Locative case for places — where things are.

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

### Base forms (12/12 confirmed)
- ✅ **школа** — noun (школа)
- ✅ **робота** — noun (робота) — note: VESUM also has "робот" (robot); context "на роботі" = at work is correct
- ✅ **банк** — noun
- ✅ **магазин** — noun
- ✅ **вулиця** — noun
- ✅ **місто** — noun
- ✅ **парк** — noun
- ✅ **лікарня** — noun
- ✅ **кафе** — noun (14 matches — all uninflected, confirms indeclinable status)
- ✅ **площа** — noun
- ✅ **вокзал** — noun
- ✅ **пошта** — noun

### Locative forms (11/11 confirmed — кафе has no locative form, correct)
- ✅ **школі** ← школа
- ✅ **роботі** ← робота
- ✅ **банку** ← банк
- ✅ **магазині** ← магазин
- ✅ **вулиці** ← вулиця
- ✅ **місті** ← місто
- ✅ **парку** ← парк
- ✅ **лікарні** ← лікарня
- ✅ **площі** ← площа
- ✅ **вокзалі** ← вокзал
- ✅ **пошті** ← пошта
- ⚠️ **кафе** — indeclinable: locative = у кафе (same form), confirmed by 14 VESUM matches all returning кафе(noun)

**Not found:** none — all 23 verified forms confirmed.

---

## Textbook Excerpts

### Section: Місцевий відмінок (The Locative Case)

> М. в. — питання: (на/у) кому? (на/у) чому? — Іменники, що мають однакові закінчення в давальному і місцевому відмінках однини, розрізняють за значенням і питаннями. Місцевий відмінок — зазвичай із прийменниками.
> **Source:** Кравцова, Grade 4, p. 48

> Table (М. в. однина): Жіночий рід: (у) школі, (у) пісні; Чоловічий рід: (на) бику(-ові), (у) меду(-ові); Середній рід: (на) теляті, (у) вікні
> **Source:** Захарійчук, Grade 4, p. 57 — the "школа → (у) школі" example appears directly in the declension table, making it ideal for the module.

> У місцевому відмінку однини паралельні закінчення -ові/-еві або -у/-ю мають назви неістот чоловічого роду: у банку — у банкові, у будинку — у будинкові. Закінчення -і (-ї) мають назви неістот чоловічого роду (переважно безсуфіксні): в акті, на березі, у ґрунті… Середнього роду без суфікса -к-: у місті, на селі.
> **Source:** Авраменко, Grade 10, p. 167 — authoritative breakdown of masc/neut locative endings.

### Section: В чи на? (В or На?)

> Прийменник **на** вживають з назвами установ, приміщень, їхніх частин: кухня, дім, фабрика, завод, **станція, вокзал, пошта** → піти на пошту, приїхати на вокзал. З рештою просторових іменників і географічних назв уживають прийменник **в (у)**: зайти в школу.
> **Source:** Авраменко, Grade 11, p. 72 — direct textbook authority for на вокзалі / на пошті and в школі.

> Прийменник **в (у)** вживають з іменниками, що позначають: **види навчальних закладів** — у школі, у коледжі, в інституті. Прийменник **на** вживають з іменниками, що позначають: **вулиці, проспекти, площі** — на проспекті Миру, на вулиці Басейній. Сполука **на Україні** застаріла — лише **в Україні**.
> **Source:** Глазова, Grade 11, p. 73, §16 — confirms every в/на distinction in the plan.

### Section: Діалоги (Dialogues)

> — Добрий день! / — Добрий день! / — Перепрошую за дзвінок, але змушений попередити, що завтра пропущу навчальні заняття, оскільки о 11:30 мені призначено візит до сімейного лікаря. / — Дякую за попередження. Не забудь узяти довідку…
> **Source:** Авраменко, Grade 8 (Tier 1), p. 80, §36 — oral dialogue in school context. Good model for realistic dialogue structure (this is B1+ register, but the structural pattern — topic statement + natural response — applies to A1 at simpler vocabulary level).

> Dialogue excerpt from Grade 2 Кравцова (metro): — Привіт, Кирилку! — Привіт, Соломійко! — Тобі сподобалося їздити на ескалаторі? — Так, дуже!
> **Source:** Кравцова, Grade 2, p. 111 — short A1-register dialogues with natural question-answer ping-pong. Good model for Dialogue 1 structure.

### Section: Підсумок — Summary

> Відмінок М. в. — питання (на/у) кому? (на/у) чому? — helper word М. (місцевий): на/у кому? на/у чому? Із таблиці: М.в. → (у) школі, (у) пісні, (на) коні, (у) вікні.
> **Source:** Захарійчук, Grade 4, p. 43, p. 57 — the standard "helper question" method taught in Ukrainian schools. Use М. = (на) кому? (на) чому? as the mnemonic.

---

## Grammar Rules

- **У/В alternation:** Правопис §23 — У used between consonants, at start of sentence before consonant, before в/ф/льв/зв/св/дв etc. В used between vowels, at start before vowel, after vowel before most consonants. Applied to plan: **у банку** (б→consonant), **в офісі** (о→vowel), **у Києві** (К→consonant before К). Full rule at https://2019.pravopys.net/sections/23/

- **Locative always requires preposition:** Confirmed by Grade 4 Захарійчук p. 73: "У називному відмінку іменники вживаються без прийменників, у місцевому — **тільки з прийменниками**."

- **Locative endings** (from Grade 10 Авраменко): Masculine nouns: -у/-ю (банку, парку) OR -і (офісі); the choice depends on stress/suffix. Feminine: -і (школі, роботі, вулиці, лікарні). Neuter: -і (місті). Indeclinable (кафе): no change.

- **На пошті / на вокзалі** (not *в пошті / *в вокзалі): Авраменко Grade 11 p. 72 explicitly lists вокзал and пошта in the "на + установи" category. The plan's note is correct and textbook-verified.

---

## Calque Warnings

- **"на Україні"** → ❌ CALQUE / archaic — Авраменко Grade 11 p. 72: "Сполука на Україні застаріла, її вживали в ХІХ ст., коли землі нашої країни входили до складу різних імперій." Correct form: **в Україні** (always). The plan correctly flags this as sovereignty issue — ✅ plan is right.

- **"в/у + місця vs до + місця"** → potential confusion source — Антоненко-Давидович (ad-219): use **у(в)** for static location/being inside; use **до** for directional motion toward a place. Plan teaches locative (static: де?) — correct. Note for module: avoid conflating "Я в школі" (static, locative) with "Я йду до школи" (direction, genitive).

- **Locative plural endings** → Антоненко-Давидович (ad-010): Under Russian influence, learners may write *по пальцям, по горам* — WRONG. Correct: **по пальцях, по горах** (-ах/-ях, not -ам/-ям). Module doesn't use plural locative (A1 scope), but worth flagging for activities if "по" constructions appear.

- **"місцевий відмінок в у на" phrases checked** → No calques found in the plan content. All preposition choices (в школі, на роботі, у банку, на площі, на вокзалі, на пошті) are confirmed by textbook sources.

---

## CEFR Check

| Word | Level | Status |
|------|-------|--------|
| школа | **A1** | ✅ On target |
| вокзал | **A1** | ✅ On target |
| лікарня | **A1** | ✅ On target |
| банк | **A1** | ✅ On target |
| магазин | **A1** | ✅ On target |
| площа | **A1** | ✅ On target |
| вулиця | **A1** | ✅ On target |
| парк | **A1** | ✅ On target |
| місто | (not in PULS — but universally A1 in all references) | ✅ On target |
| пошта | (not queried — basic civic vocabulary, confirmed A1 by textbook context) | ✅ On target |

**No vocabulary above A1 level found.** All 12 place nouns are level-appropriate.

---

## Summary Notes for Writer

1. **All 23 VESUM forms verified** — no ghost words in the vocabulary list.
2. **Textbook gold:** Захарійчук Grade 4 p. 57 table (школа → у школі) and Авраменко Grade 11 p. 72 (вокзал/пошта → на) are primary references for this module.
3. **Правопис §23** covers у/в alternation — include practical rule: "у банку" (consonant before) vs "в офісі" (vowel before).
4. **Critical calque to prevent:** "на Україні" — must always be "в Україні". Plan already flags this correctly.
5. **кафе** is indeclinable — у кафе (no ending change). This is explicitly noted in the plan and confirmed by VESUM.
6. **на пошті / на вокзалі** are conventional, textbook-verified exceptions to the в/у enclosed-space pattern — teach as fixed phrases.
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
# Verified Knowledge Packet: Where Is It?
**Module:** where-is-it | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 209
> **Score:** 0.33
>
> 206
> вали! (В. Нестайко). 3. Дружній череді вовк не страшний 
> часто говорив батько (М. Номис). 4. Я нахилився до Ту­сі 
> й запитав Слухай, а ти собак боїшся? (В. Нестайко). 5. Я 
> сказав Сонце, сонце! Уділи мені живущої води... (В. Сві­- 
> д­зинський).
> 51. ДІАЛОГ
> Про розмову двох або кількох осіб та  
> про вживання розділових знаків 
> 508.	 Прочитайте текст. Хто бере участь у розмові? Простежте, як пе-
> редано на письмі слова кожного учасника спілкування, які розділові 
> знаки вжито.
> ТІКÀЄ
> Прогулюючись біля річки, Олесь із Галинкою, мабуть, 
> уперше побачили тренувальний катер зі спортсменом на 
> водних лижах.
> – Поглянь, катер мчить, як вихор! – вигукнула, дивую-
> чись, дівчинка.
> – Бо ж тікає, – переконливо пояснив Олесь.

## Місцевий відмінок (The Locative Case)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 106
> **Score:** 0.50
>
> 106
> 1.	Прочитайте sms-повідомлення та виконайте завдання.
> Дорог.. Віталіє! Чекаю тебе в 
> парку о 18:00. 
> Люб.. Віталію!
> Буду вчасно. До зустрічі! 
> А.	 У якому відмінку вжито імена?
> Б.	 Яке закінчення пропущено в першому повідомленні, а яке — у другому?
> Кличний відмінок використовуємо у звертаннях до людей або тварин: 
> Світлано, братику, котику, а в художній літературі — і до неживих 
> предметів: Зоре моя вечірняя, зійди над горою (Т. Шевченко). 
> І відміна
> -о
> іменники твердої групи
> мамо, Миколо, країно
> -е, -є
> іменники м’якої та мішаної груп
> Маріє, Ілле, круче 
> -ю
> пестливі іменники м’якої групи
> бабусю, Галю, АЛЕ: На-
> сте, Катре
> ІІ відміна
> -е
> іменники чол. роду твердої групи
> брате, друже, Іване
> -ю
> іменники чол.

## В чи на? (В or На?)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 42
> **Score:** 0.50
>
> 39
> 1. Мама робила в лікарні й пишалася своєю роботою. 
> 2.  Сніжна заметіль замела все навколо. 3. Помітивши за 
> вікном друга, хлопець непомітно вислизнув з хати. 4. У по-
> відомленні повідомлялося про новий кінофільм. 5. Учителі 
> та школярі провели флешмоб на шкільному подвір’ї.
> 86.	 Знайдіть для кожного слова місце в реченні й запишіть. Ви може-
> те використати кожне слово лише один раз. Ви можете скористатися 
> таблицею «Культура мовлення» на с. 40. 
> відкрити / відчинити / розплющити / розгорнути
> 1. Прошу ... ваші зошити. 2. Уранці мені не хотілося на-
> віть ... очі. 3. Спеціальний ключ допоможе ... банку. 4. Щоб 
> провітрити кімнату, треба ... вікна. 
> 87.	 Виберіть із рамки біля речення слово, яке потрібно вставити на 
> місці пропуску. Запишіть утворені речення. 
> 1.

> **Source:** , Grade 4
> **Section:** Сторінка 45
> **Score:** 0.25
>
> 90. Прочитайте групи слів.
> Вода, водій, водичка, водяний, водяним, у воді; берег, 
> прибережний, на березі, на прибережному; квітка, квіт­
> ник, у квітнику, заквітчати, на квітці, квітковий; лікар, ліку­
> вати, до лікаря, лікоть, лікарня, у лікарні; вулиця, вуличка, 
> на вулиці, вуличний, вулик, вуличкою.
> • Спишіть слова, розділивши їх на групи: 1) спільнокореневі 
> слова; 2) однозвучні слова; 3) форми одного зі спільнокоре- 
> невих слів.
> •  Позначте будову спільнокореневих слів.
> 91. Прочитайте текст.
> На в..личезному бе..крайому лану 
> гречки пасут..ся бджолята. Як гарно їм 
> тут на просторах, у білому квітучому 
> царстві! Трудят..ся вони тут і мед носять 
> пудами*.
> Порядкує біля бджіл дяд-.ко Роман.
> Він, кажуть, знає таємну бджолину мову.
> Ходит.. ДЯД..КО серед ВУЛИКІВ І ЩОСЬ 
> намовляє бджолятам.

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 158
> **Score:** 0.33
>
> (...)
> Що ж вони збираються робити в банку? Може, я втрапив до банди гра­біж­
> ників і вони хочуть викрасти золоті зливки, що зберігаються в броньованих 
> підвалах? Тоді мені кінець: банк стереже ціла армія озброєних охоронців, 
> а камери спостереження встановлено в кожному приміщенні. Я так поринув 
> у роздуми, що підскочив мов ошпарений, коли бабуся поклала мені руку на 
> плече.

## Підсумок — Summary

## Grammar Reference

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 122
> **Score:** 0.25
>
> 122
> КНИЖКА ВЧИТЬ, ЯК У СВІТІ ЖИТЬ
> Хто й коли у ньому княжив
> І в який ходив поход,
> Хто боровсь за Україну,
> За державність, за народ.
> Розкажу вам, як боролись
> Наші прадіди колись,
> Як за щастя України
> Ріки крові розлились.
> Розкажу, чому і досі
> Чути стогони її
> І чому так довго в хмарах
> Сонце рідної землі...
> Заспіваю вам не пісню
> Про стару старовину,
> Розкажу я вам не казку,
> А бувальщину одну.
>  ÏÅÐÅÂ²ÐßªÌÎ
> 1. У тексті згадано всіх названих нижче богів, ОКРІМ
>  
> А Дажбога     Б Нептуна     В Перуна     Г Стрибога
> 2. У рядках «Як за щастя України // Ріки крові розлились» використано
>  
> А метафору     Б епітет     В порівняння     Г гіперболу 
>  ÀÍÀË²ÇÓªÌÎ
> 3. Що означає назва «Заспів»? Прочитайте початок цієї частини. Чому авт ор обрав 
> саме такий початок? 
> 4.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Прийменник як службова частина мови
> **Source:** МійКлас — [Прийменник як службова частина мови](https://www.miyklas.com.ua/p/ukrainska-mova/7-klas/priimennik-48228/priimennik-iak-sluzhbova-chastina-movi-nepokhidni-i-pokhidni-priimenniki-48229)

### Теорія:

*www.ua.pistacja.tv*  
**Прийменник** — службова незмінна частина мови, що виражає відношення між предметами, відношення дії та ознаки до предмета, залежність іменника, числівника, займенника від інших слів у реченні і разом з ними вказує на об’єкт дії, напрям, місце, час, причину, мету.
Приклад:
Ще ****в ****дитинстві я ходив ****у**** трави, ****в**** гомінливі трепетні ліси…\(В.

### Словосполучення з прийменником ПО
> **Source:** МійКлас — [Словосполучення з прийменником ПО](https://www.miyklas.com.ua/p/ukrainska-mova/11-klas/sintaksichna-norma-380223/slovospoluchennia-z-priimennikom-po-380391)

### Теорія:
Прийменник **по** вживають, коли треба вказати

Зверни увагу\!
Прийменник по вживаємо також у сполуках по батькові, по суті, по правді, по праву, по можливості: *називати на ім'я й по батькові, сказати по правді, отримати щось по праву.*
Прийменник по вживаємо в конструкціях з іменниками в знахідному відмінку при вказуванні на предмет, місце, простір, час, що є межею поширення певної дії  або ознаки: загрузнути по кісточки, чашки повні по краї, відпочивати по перше вересня.
Російському прийменнику по відповідають українські за, з, на, у \(в\), для, до, через, щодо або безприйменникові конструкції.

### Уживання прийменників В і НА з географічними назвами
> **Source:** МійКлас — [Уживання прийменників В і НА з географічними назвами](https://www.miyklas.com.ua/p/ukrainska-mova/11-klas/sintaksichna-norma-380223/uzhivannia-priimennikiv-v-i-na-z-geografichnimi-nazvami-i-prostorovimi-i_-380264)

### Теорія:
Прийменник на
Прийменник на вживають з назвами:
- установ, приміщень, чітко обмеженого простору: *були на заводі, зустрінемось на вулиці, повернувся на базу, чекали на пероні, були на морі;*
  
- адміністративно\-територіальних одиниць \(областей, районів\), островів та острівних держав: *відпочинок на Закарпатті, народився на Полтавщині, полетіли на Балі, конфлікти на Близькому Сході.* 
Прийменник на вживаємо в мовних конструкціях, що означають:
- вмістилища, покликані містити об'єкти: *шухляда на білизну, мішок на картоплю*;
  
- матеріали, покликані на прикінцеві вироби: *шовк на сукню, борошно на пиріг.* 
Зверни увагу\!

---
**Total textbook excerpts found:** 7
**Grades searched:** 4, 5, 6
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Місцевий відмінок (The Locative Case)` (~300 words)
- `## В чи на? (В or На?)` (~300 words)
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
  1. **First week in a new city — asking a neighbor where to find: аптека (f, pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), лікарня (f, hospital), парк (m, park). В аптеці, на пошті, у банку.**
     Speakers: Новий мешканець (newcomer), Сусід (neighbor)
     Why: В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)

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

**Required:** школа → в школі (school), робота → на роботі (work), банк → у банку (bank), магазин → у/в магазині (shop), вулиця → на вулиці (street), місто → у/в місті (city)
**Recommended:** парк → у/в парку (park), лікарня → у/в лікарні (hospital), кафе → у/в кафе (café — indeclinable), площа → на площі (square), вокзал → на вокзалі (train station), пошта → на пошті (post office)

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
## Діалоги (Dialogues) (~330 words total)

- P1 (~20 words): One-sentence hook introducing the Де? question — today we answer it with real Ukrainian places using the locative case.
- Dialogue 1 (~120 words): "Де всі?" — 6-line exchange with Маринка and Олег. Маринка asks where each family member is: — Де Олена? — Вона в школі. — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — О, кішка на дивані! Formatted with speaker labels; each answer written in bold locative form.
- P2 (~30 words): Brief bridge — notice the pattern: nominative школа becomes в школі, робота becomes на роботі. The noun changed its ending to answer Де?
- Dialogue 2 (~120 words): "Де ти живеш?" — 6-line exchange between Назар and Емілі (a newcomer). — Де ти живеш? — Я живу в Києві, на вулиці Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. — А де ти навчаєшся? — В університеті, в центрі міста. Shows nesting: city → street → building.
- P3 (~40 words): Wrap-up observation — both dialogues show the same structure: Де? → preposition (в or на) + a changed noun. In the next section we learn exactly how and why the noun changes.

---

## Місцевий відмінок (The Locative Case) (~330 words total)

- P1 (~70 words): Introduce the locative case using the Grade 4 helper-word method (Захарійчук Gr4 p.74): every Ukrainian noun belongs to one of seven відмінки (cases). The locative, М.в. = місцевий відмінок, always answers the question на/у кому? на/у чому? and ALWAYS requires a preposition — it never stands alone. Write the helper question in a callout box: М. (на, у) — на/у кому? на/у чому?
- P2 (~80 words): В/у = enclosed spaces — inside a building, room, city. Five model nouns in nominative → locative: школа → в школі (she went in, now she's inside), банк → у банку, магазин → у/в магазині, лікарня → у лікарні, місто → у місті. Brief rule: в before consonant cluster or when it sounds better; у elsewhere (euphony reminder links back to M28).
- P3 (~80 words): На = on a surface, open area, or by convention for certain places. Five model nouns: робота → на роботі, вулиця → на вулиці, площа → на площі, урок → на уроці, море → на морі. Emphasis: на is not "wrong" — it's simply the word that particular place travels with. Learn place + preposition as a unit, just as English says "at work" not "in work."
- P4 (~70 words): The three most common locative endings for familiar nouns. Masculine: -у (у банку, у парку, на вокзалі → -і after soft/sibilant stem) or -і (в офісі, на уроці). Feminine: -і almost everywhere (в школі, на роботі, у лікарні, на вулиці). Neuter: -і (у місті, на морі). Practical advice: for now, learn the 12 required vocabulary nouns as fixed phrases — the pattern will emerge naturally.
- Exercise (~30 words): **Fill-in (8 items)** — Answer Де? with the correct locative phrase: Олена ___ (школа) → в школі. Тарас ___ (робота). Діти ___ (парк). Ми ___ (місто). Кіт ___ (диван). Я ___ (лікарня). Він ___ (офіс). Вони ___ (магазин).

---

## В чи на? (В or На?) (~330 words total)

- P1 (~80 words): В/у signals an enclosed, bounded space — you are physically inside. Prototype examples from the dialogues: в школі (inside the school building), у банку (inside the bank), в магазині (inside the shop), у лікарні (inside the hospital). Special case: в кафе — кафе is an indeclinable neuter noun (borrowed word ending in a vowel), so the noun itself never changes; only the preposition marks location. В кафе is always в кафе.
- P2 (~80 words): На signals an open area, surface, or — most importantly — conventional association. Prototype open spaces: на вулиці (on the street, outdoors), на площі (on the square), на морі (at the sea). Then the tricky conventional ones: на роботі (at work — not inside a single building but the concept of work), на вокзалі (at the train station — convention, not logic), на пошті (at the post office — also conventional). Rule of thumb: when in doubt, learn each place with its preposition as a fixed phrase.
- P3 (~80 words): Country and city rule — always в/у: в Україні, у Києві, у Львові, в Одесі, у Харкові. Special case for streets: на + street name — на вулиці Хрещатик, на Майдані Незалежності. Cultural note set apart in a box: НІКОЛИ не кажи "на Україні" — ЗАВЖДИ "в Україні." This is not just a grammar rule — it reflects Ukraine's recognition as a sovereign state, not a borderland. Russian imperial usage promoted "на Україні"; modern Ukrainian rejects it.
- Exercise (~30 words): **Quiz (10 items)** — В or на? Choose the correct preposition: ___ школі / ___ банку / ___ вулиці / ___ парку / ___ пошті / ___ місті / ___ вокзалі / ___ лікарні / ___ роботі / ___ кафе.
- P4 (~60 words): Summary contrast table (prose, not a grid): В/у → school, bank, shop, hospital, café, city, country. На → street, square, station, post office, work, sea, lesson. Pattern check: if you can picture being physically enclosed inside — usually в. If it's a surface, open area, or set by tradition — usually на. When unsure, look up the place + check with в or на.
- Exercise (~30 words): **Match-up (8 items)** — Match nominative to correct locative phrase: школа ↔ в школі; робота ↔ на роботі; банк ↔ у банку; вулиця ↔ на вулиці; місто ↔ у місті; площа ↔ на площі; пошта ↔ на пошті; вокзал ↔ на вокзалі.

---

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Consolidation prose — the locative case (місцевий відмінок, М.в.) answers one question: Де? — where something IS right now, static location. It never stands alone; it always needs в/у or на in front of it. Use the helper-word test: can you ask на/у кому? or на/у чому? before the noun? If yes, it's locative. Example: (на/у чому?) → на вулиці, у банку, в школі, на роботі. Every noun on today's vocabulary list has been shown in its locative form — review them as pairs: школа / в школі, банк / у банку.
- P2 (~80 words): В/у vs. на quick recap in prose — в/у = enclosed space or city/country (в школі, у банку, в Україні, у Києві). На = open area, surface, or convention (на вулиці, на роботі, на пошті, на вокзалі). The sovereign rule: в Україні — always, without exception. Conventional forms (на пошті, на вокзалі) must be learned as fixed phrases, just as English learners memorize "at work" rather than deriving it.
- P3 (~80 words): Endings summary — most feminine nouns take -і in the locative (school → в школі, street → на вулиці). Most masculine nouns take -у or -і (bank → у банку, park → у парку, office → в офісі, lesson → на уроці). Neuter takes -і (city → у місті, sea → на морі). Indeclinable foreign nouns don't change at all (café → в кафе). For now, twelve vocabulary nouns are enough — patterns solidify with practice.
- Self-check (~60 words): Three reflection questions (bulleted, with model answers):
  - Де ти зараз? → Я зараз вдома / в кімнаті / у кафе.
  - Де ти працюєш/навчаєшся? → Я працюю в офісі / навчаюся в університеті.
  - Де живе твоя сім'я? → Вони живуть у Києві / у Лондоні / у маленькому місті.
- Exercise (~30 words): **Quiz (6 items)** — Where is it? Choose the correct locative form: банк → (банку / банці / банкові). школа → (школу / школі / школою). місто → (місту / місті / містом). вулиця → (вулицю / вулиці / вулицею). парк → (парку / парці / паркові). пошта → (пошту / пошті / поштою).

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
