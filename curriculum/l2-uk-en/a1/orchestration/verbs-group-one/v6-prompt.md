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

Write the full prose content for module **16: Verbs Group I** (A1, A1.3 [Actions]).

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
module: a1-016
level: A1
sequence: 16
slug: verbs-group-one
version: '1.1'
title: Verbs Group I
subtitle: Читаю, читаєш, читає — your first conjugation
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Conjugate Group I (-ати) verbs in present tense for all persons
- Use 6 high-frequency Group I verbs in sentences
- Recognize the Group I ending pattern (-у/-ю, -єш, -є, -ємо, -єте, -ють)
- Build simple sentences about daily activities
dialogue_situations:
- setting: In a shared kitchen — one person cooking, other asking what they're doing
  speakers:
  - Юля (cooking)
  - Сашко (curious)
  motivation: 'Group I verbs in action: читаєш, працюєш, готуєш'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — What do you do? (ULP Ep22 pattern): — Що ти робиш? — Я читаю книгу.
    А ти? — Я слухаю музику. — А що робить Олена? — Вона готує вечерю. All three persons
    (я/ти/він,вона) emerge naturally.'
  - 'Dialogue 2 — At work/school: — Де ти працюєш? — Я працюю в офісі. А ти? — Я не
    працюю, я навчаюся. — Ти знаєш українську? — Так, я вивчаю! Group I verbs in practical
    context.'
- section: Перша дієвідміна (Group I Verbs)
  words: 300
  points:
  - 'Варзацька Grade 4 p.129: verb conjugation table (теперішній час). Group I verbs
    have infinitive in -ати (or -увати, -яти): читати → я читаю, ти читаєш, він/вона
    читає ми читаємо, ви читаєте, вони читають. Pattern: stem + -ю, -єш, -є, -ємо,
    -єте, -ють.'
  - 'Six essential Group I verbs: читати (to read): читаю, читаєш, читає... знати
    (to know): знаю, знаєш, знає... працювати (to work): працюю, працюєш, працює...
    слухати (to listen): слухаю, слухаєш, слухає... гуляти (to walk): гуляю, гуляєш,
    гуляє... готувати (to cook): готую, готуєш, готує...'
- section: Я, ти, він/вона (Persons)
  words: 300
  points:
  - 'Focus on the three most-used forms: Я читаю (I read) — ending -ю Ти читаєш (You
    read) — ending -єш Він/вона читає (He/she reads) — ending -є These three cover
    90% of A1 conversations. Plural forms for recognition: ми читаємо, ви читаєте,
    вони читають.'
  - 'Building sentences with known vocabulary: Я читаю нову книгу. (M08 noun + M09
    adjective + M16 verb) Ти знаєш цю пісню? (M12 demonstrative + M16 verb) Вона слухає
    українську музику. (M16 verb + adjective + noun) Note: the object may change form
    (книгу, пісню) — learn as chunks for now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Group I conjugation pattern: я -ю, ти -єш, він/вона -є, ми -ємо, ви -єте, вони
    -ють. Works for: читати, знати, працювати, слухати, гуляти, готувати. Self-check:
    Conjugate ''слухати'' for я, ти, він/вона. Say what you do (Я читаю...), ask what
    someone does (Що ти робиш?).'
vocabulary_hints:
  required:
  - читати (to read)
  - знати (to know)
  - працювати (to work)
  - слухати (to listen)
  - гуляти (to walk)
  - готувати (to cook)
  recommended:
  - робити (to do — Group II, preview as chunk)
  - вивчати (to study/learn)
  - малювати (to draw)
  - грати (to play)
  - вечеря (dinner, f)
  - музика (music — review from M15)
activity_hints:
- type: fill-in
  focus: 'Conjugate: я чита__, ти чита__, він чита__'
  items: 10
- type: quiz
  focus: 'Choose correct form: Вона (читаю/читаєш/читає) книгу.'
  items: 8
- type: match-up
  focus: 'Match person to verb form: я ↔ читаю, ти ↔ читаєш'
  items: 6
- type: fill-in
  focus: 'Complete the sentence: Що ти ___? — Я ___ музику. (слухати)'
  items: 6
connects_to:
- a1-017 (Verbs Group II)
prerequisites:
- a1-015 (What I Like)
grammar:
- 'Group I conjugation: -ю, -єш, -є, -ємо, -єте, -ють'
- Infinitive → present tense transformation
- 'Simple sentences: Subject + Verb + Object'
- 'Question: Що ти робиш?'
register: розмовний
references:
- title: Варзацька Grade 4, p.129
  notes: 'Conjugation table: теперішній час, persons and endings.'
- title: Захарійчук Grade 4, p.110
  notes: 'Verb conjugation table: однина та множина за особами.'
- title: ULP Season 1, Episode 22
  url: https://www.ukrainianlessons.com/episode22/
  notes: Present tense verbs in daily life.

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

**All 12 words confirmed in VESUM:**

- ✅ читати (verb)
- ✅ знати (verb)
- ✅ працювати (verb)
- ✅ слухати (verb)
- ✅ гуляти (verb)
- ✅ готувати (verb)
- ✅ робити (verb)
- ✅ вивчати (verb)
- ✅ малювати (verb)
- ✅ грати (verb)
- ✅ вечеря (noun)
- ✅ музика (noun — 2 lemma matches, both noun)

**Not found:** none.

---

## Textbook Excerpts

### Section: Перша дієвідміна (Group I Verbs) — conjugation table

> *"До І дієвідміни належать дієслова, які в 3-й особі множини мають закінчення -уть (-ють). НАПРИКЛАД: читають, пишуть, вийдуть. Дієслова І дієвідміни в усіх особових закінченнях (крім 1-ї особи однини та 3-ї особи множини) мають букву е (є)."*
> — **Заболотний, Grade 7 (tier 1, NUS), p. 69**

> Full personal endings listed (Karaman Grade 10 p.179):
> І дієвідміна: **-у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють)**
> Applies when infinitive has suffixes **-а-** (not dropping), **-ува-**, **-ну-**
> Examples: *співати, будувати, кинути*
> — **Карaman, Grade 10 (tier 2), p. 179**

> Conjugation table showing читаю/читаєш/читає (present) and прочитаю/прочитаєш/прочитає (future) — confirms Group I endings across tenses.
> — **Захарійчук, Grade 4 (tier 2), p. 113**

### Section: Я, ти, він/вона (Persons)

> *"Категорія особи дієслова тісно пов'язана з категорією особи займенника (малюю – я малюю; малюєш – ти малюєш, малюють – вони малюють)."*
> — **Заболотний, Grade 7 (tier 1), p. 52**

> Personal pronoun table (direct pedagogical source for how Ukrainian schools present this):
>
> | Особа | Однина | Множина |
> |-------|--------|---------|
> | 1-ша  | я      | ми      |
> | 2-га  | ти     | ви      |
> | 3-тя  | він, вона, воно | вони |
>
> *"Особові займенники вказують на особу або осіб і відповідають на ті самі питання, що й іменники: хто? що?"*
> — **Захарійчук, Grade 4 (tier 2), p. 122**

### Section: Діалоги (Dialogues)

> No direct "що ти робиш" dialogue found in textbook RAG. Closest match is Grade 5, Голуб (tier 1) which has natural person-to-person dialogue patterns (people at work, casual exchange). Textbook evidence confirms: natural Ukrainian dialogues centre on **shared everyday situations** — walking, school, hobbies — not structured question-and-answer interrogation.

> Grade 4 Захарійчук p.122 provides a fill-in exercise: *"... читаєш, ... побачили, ... радіємо, ... читає, ... малюєте"* — showing how all three persons appear naturally in the same activity context. Confirms plan Dialogue 1 structure (reading, listening, cooking) is pedagogically sound.

### Section: Підсумок — Summary

> *"Дієслова теперішнього часу виражають незавершену дію, яка відбувається в момент мовлення. Вони змінюються за особами та числами."*
> — **Захарійчук, Grade 4 (tier 2), p. 110**

> Textbook confirms that identifying verb дієвідміна by **3rd person plural** ending is the standard Ukrainian pedagogical approach: *-уть/-ють* → I дієвідміна.

---

## Grammar Rules

Правопис 2019 does not contain a dedicated section on verb personal endings — this is a **morphological** topic covered in grammar textbooks, not orthography (Правопис covers spelling, e.g., which letter е/и to write in endings). The authoritative source is the textbooks above.

**From textbooks (Grade 7, Заболотний — tier 1):**

- **I дієвідміна rule:** 3rd person plural ends in **-уть/-ють** → personal endings use **е/є**: -у/-ю, **-єш**, **-є**, **-ємо**, **-єте**, **-ють**
- **II дієвідміна rule:** 3rd person plural ends in **-ать/-ять** → personal endings use **и/ї**: -у/-ю, **-иш**, **-ить**, **-имо**, **-ите**, **-ать**
- The **е/є vs и/ї** distinction in personal endings is the key orthographic rule (aligns with Правопис principles on vowel alternation in morphological endings).

**Правопис 2019 relevant note (indirect):** The plan correctly presents endings as -ю, -єш, -є, -ємо, -єте, -ють for читати — this is consistent with the -ува- suffix pattern (працю**ва**ти → pracyuyu, pracyuyesh). No spelling error in the planned conjugation tables.

---

## Calque Warnings

**Phrase 1: навчатися** (in Dialogue 2: "я не працюю, я **навчаюся**")
→ **OK — natural Ukrainian.** Антоненко-Давидович (ad-125) lists *навчатися* alongside *вчитися* as fully natural Ukrainian verbs taking the genitive. No calque issue. However see CEFR warning below — *навчатися* is **B1 level**, consider replacing with *учуся* / *я вчуся* (more colloquial, lower register, A1 level pattern in speech).

**Phrase 2: готувати вечерю**
→ **OK — natural Ukrainian.** No calque found. *готувати* + accusative (*вечерю*) is standard Ukrainian construction.

**Phrase 3: працювати в офісі**
→ **OK — natural Ukrainian.** *Працювати в* + locative is standard. (Note for writer: "в офісі" — correct preposition is **в**, not "на офісі". The locative "в офісі" is correct Ukrainian.)

**Bonus finding — музичний vs музикальний** (Антоненко-Давидович ad-101):
→ **Important distinction for M16:** *музичний* = "relating to music" (музичний інструмент, музичний вечір). *Музикальний* = "having a musical ear / musically gifted." These are NOT interchangeable. Module should use **музичний** if describing music-related objects/events.

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| читати | A1 | ✅ on target |
| знати | A1 | ✅ on target |
| працювати | A1 | ✅ on target |
| слухати | A1 | ✅ on target |
| гуляти | A1 | ✅ on target |
| готувати | A1 | ✅ on target |
| малювати | A1 | ✅ on target |
| грати | A1 | ✅ on target |
| вечеря | A1 | ✅ on target |
| музика | A1 | ✅ on target (the C1 entry is the *musician* sense — different lemma) |
| **вивчати** | **A2** | ⚠️ **ABOVE TARGET** — plan vocabulary lists this as A1 but PULS rates it A2 |
| **навчатися** | **B1** | ⚠️ **ABOVE TARGET** — appears in Dialogue 2 ("я навчаюся"); not in plan vocabulary list but used in dialogue |
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
# Verified Knowledge Packet: Verbs Group I
**Module:** verbs-group-one | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 49
> **Score:** 0.33
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

## Перша дієвідміна (Group I Verbs)

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 129
> **Score:** 0.25
>
> 129
> 272. 1. Із поданих складів утвори і запиши слова. Яке се-
> ред них «зайве»? Чому?
> 2. Спиши прислів’я. Поясни, як ти розумієш його зміст.
> Сій не пусто, то збереш густо.
> 273. 1. Розгляньте таблицю змінювання дієслів теперіш-
> нього часу. Зробіть висновок.
> ЗМІНЮВАННЯ ДІЄСЛІВ  
> ТЕПЕРІШНЬОГО ЧАСУ
> Число
> Особа
> Питання
> Приклади
> Однина
> 1-ша (я)
> що роблю?
> пишу, читаю, 
> біжу, стою
> 2-га (ти)
> що робиш?
> пишеш, читаєш, 
> біжиш, стоїш
> 3-тя  
> (він, вона, 
> воно)
> що робить?
> пише, читає, 
> біжить, стоїть
> Множина
> 1-ша (ми)
> що робимо?
> пишемо, читаємо, 
> біжимо, стоїмо
> 2-га (ви)
> що робите?
> пишете, читаєте, 
> біжите, стоїте
> 3-тя 
> (вони)
> що  
> роблять?
> пишуть, читають, 
> біжать, стоять
> Дієслова теперішнього часу змінюються за особами 
> і числами.

## Я, ти, він/вона (Persons)

> **Source:** savchenko, Grade 3
> **Section:** Сторінка 37
> **Score:** 0.50
>
> 37
> Дівчинкакнижкучитає,
> аСонцеперегортає
> сторінкийсвітловливає
> влітеритавслова.
>  Хто дійові особи вірша?
>  Поміркуй, чому соняшника образило прохання дівчин-
> ки. Що його потім здивувало?
>  Яку інтонацію читання підказують вислови: дуже 
> довго дивився, прохати, здивувався, засоромлено
> пооглядався?
> Поміркуйте разом! Розгляньте малюнок до вірша.

> **Source:** savchenko, Grade 4
> **Section:** Сторінка 157
> **Score:** 0.33
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

> **Source:** savchenko, Grade 3
> **Section:** Сторінка 52
> **Score:** 0.33
>
> 52
> Народні пісні мають форму вірша. За змістом вони
> часом нагадують казки.
> У п³сні, що ти прочитаєш, природні явища та рослини 
> зображені як живі істоти. Читати пісні треба насп³вно, 
> наче ведеш довірливу розмову. Використовуй поради 
> щодо виразного читання.
> ТРИ ТОВАРИШІ
> Українська народна пісня
> Ой| за горою,| за кам’яною,||
> ой|там зібрались три товариші:||
> один товариш|| — то Сонце крàсне,|
> другий товариш|| — то Місяць ÿсний,|
> третій товариш|| — то дрібнèй Дощик.||
>     А Сонце каже:|| «Як ізійду я,|
> як ізійду я раненько-рано,|
> то ізрадіють усі на світі».|||
> А Місяць каже:|| «Як ізійду я,|
> як ізійду я| звечора рано,||
> то ізрадіє| риба у морі,||
> люди в дорозі,|| звірі у полі».|||
> А Дощик каже:|| «Як упаду я,|
> як упаду я|| тричі на землю,||
> Вчися читати виразно
>  Зрозумій зміст твору:
> визн...

## Підсумок — Summary

> **Source:** , Grade 4
> **Section:** Сторінка 122
> **Score:** 0.25
>
> •  Спишіть текст, уставляючи на місці крапок пропущені займен­
> ники я, ти, він, вона, воно, ми, ви, вони. Поміркуйте, на що 
> вказують (на яких осіб) ці займенники. Звірте свої міркуван­
> ня з таблицею, поданою нижче.
> 276. Розгляньте таблицю.
> Особа
> Число
> На що вказують займенники
> Однина
> Множина
> 1-ша
> я
> МИ
> я — на особу, яка говорить про себе; 
> ми — на осіб (двох і більше), які гово­
> рять про себе
> 2-га
> ти
> ви
> ти — на особу, до якої звертаються; 
> ви — на осіб, до яких звертаються
> 3-тя
> він,
> вона,
> воно
> вони
> він, вона, воно — на особу, про яку 
> щось говорять;
> вони — на осіб чи предмети, про які 
> говорять
> •  Випишіть виділені слова з таблиці. Це особові займенники.

## Grammar Reference

> **Source:** kravtsova, Grade 4
> **Section:** Сторінка 107
> **Score:** 0.50
>
> Читаєте — що ви робите? — 2-га особа множини.
> Щоб визначити, яку букву писати в закінченнях дієслів 2-ї 
> особи однини теперішнього часу, користуйся схемою.
> ( ти )-» 2-га особа однини ( -еш, -єш ) ( -иш, -їш )
> ( ви )-» 2-га особа множини ( -ете, -єте ) ( -ите, -їте )
> І 
> і
> (вони) > 3-тя особа множини (-уть, -ють) ( -ать, -ять )
> 292. Зіскануй ОЯ-код та виконай завдання.
> 293.1. Прочитай. Яку назву має денна зірка? Чому?
> ЗІРКА, ЩО СВІТИТЬ УДЕНЬ
> Чи чули ви, що є зірка, яку ми бачимо тільки 
> вдень? Що ж це за зоря, яка не блякне в променях 
> нашого світила? Не шукайте її очима. Бо ця зірка — 
> саме Сонце, наше Сонце!
> Астрономи, які знаються на планетах і зірках, 
> називають його — «денна зірка» (за Тарасом Кіньком).
> 2. Випиши дієслова у формі теперішнього часу. Познач закін­
> чення.


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
1. Речення відображає дійсність. Інформація **стверджується** або **заперечується**, сприймається як **реальна** або **нереальна**, **можлива** або **неможлива**.
  
2. Речення є **інтонаційно** й **змістово** завершеним.
  
3.

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

- слова «синій», «зелений» вказують на ознаку і відповідають на питання ***як

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Перша дієвідміна (Group I Verbs)` (~300 words)
- `## Я, ти, він/вона (Persons)` (~300 words)
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
  1. **In a shared kitchen — one person cooking, other asking what they're doing**
     Speakers: Юля (cooking), Сашко (curious)
     Why: Group I verbs in action: читаєш, працюєш, готуєш

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

**Required:** читати (to read), знати (to know), працювати (to work), слухати (to listen), гуляти (to walk), готувати (to cook)
**Recommended:** робити (to do — Group II, preview as chunk), вивчати (to study/learn), малювати (to draw), грати (to play), вечеря (dinner, f), музика (music — review from M15)

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

- P1 (~30 words): Brief scene-setter — Юля and Сашко are in a shared kitchen. One line introduces the situation: "Юля готує вечерю. Сашко заходить і питає:"
- Dialogue 1 (~110 words): Full 8-turn exchange covering я/ти/він-вона: — Що ти робиш, Юле? — Я готую вечерю. А ти що робиш? — Я читаю. — Що читаєш? — Я читаю книгу. А де Олена? — Вона слухає музику. — Вона завжди слухає музику! — Так, але вона знає багато пісень! Natural exits on -ю, -єш, -є for three persons.
- P2 (~25 words): Callout box — "Помітив/-ла? Three persons appear: я готую / ти читаєш / вона слухає. That's Group I conjugation."
- Dialogue 2 (~110 words): 8-turn work/study exchange: — Де ти працюєш? — Я працюю в офісі. А ти? — Я не працюю — я навчаюся. Я студент. — Ти вивчаєш українську? — Так, я вивчаю! — Добре! Я теж вивчаю. — Ти гуляєш увечері? — Так, я гуляю в парку. Covers працювати, навчатися, вивчати, гуляти across я/ти persons.
- P3 (~55 words): Post-dialogue note — underline the six verbs that appeared: готувати, читати, слухати, знати, працювати, вивчати, гуляти. Remind learner: "All follow the same pattern. The next section shows exactly how."

---

## Перша дієвідміна (Group I Verbs) (~330 words total)

- P1 (~70 words): Introduce the group — Group I verbs have infinitive ending in -ати (читати, слухати, гуляти), -увати (готувати, працювати), or -яти (вивчати, малювати). The infinitive is the "dictionary form." To conjugate, remove -ти and add person endings. Anchor example: читати → stem чита- → add endings.
- P2 (~80 words): Full conjugation table for читати — я читаю, ти читаєш, він/вона читає, ми читаємо, ви читаєте, вони читають. Source: Варзацька Grade 4 p.129. Pattern summary: singular -ю, -єш, -є; plural -ємо, -єте, -ють. Note the consistent -є- vowel running through forms 2 sg → 3 pl.
- P3 (~100 words): Six essential verbs, each shown with three singular forms as a mini-table: читати (читаю / читаєш / читає), знати (знаю / знаєш / знає), працювати (працюю / працюєш / працює), слухати (слухаю / слухаєш / слухає), гуляти (гуляю / гуляєш / гуляє), готувати (готую / готуєш / готує). Note: stem of -увати verbs drops -ува- → готу-, працю-.
- Exercise — fill-in (~10 words intro): "Заповни пропуски: я чита___, ти чита___, він чита___. Я слуха___, ти слуха___, вона слуха___." 10 blanks targeting Group I endings.
- P4 (~70 words): Contrast note — робити (to do) appears in the dialogue question "Що ти робиш?" but belongs to Group II (different endings: -иш, -ить). Treat it as a chunk right now: Що ти робиш? = What are you doing? It will be explained fully in M17. This prevents premature confusion.

---

## Я, ти, він/вона (Persons) (~330 words total)

- P1 (~70 words): Focus the learner — at A1, three forms cover 90% of real conversations: я (the speaker), ти (the person you talk to), він/вона (someone you talk about). Recall the pronoun table from M10. Drill those three forms first. Plural forms (ми/ви/вони) are shown for recognition but not memorization pressure yet.
- P2 (~80 words): Three persons in action — build full sentences with known vocabulary (nouns from M08, adjectives from M09): Я читаю нову книгу. / Ти знаєш цю пісню? / Він слухає українську музику. / Вона готує смачну вечерю. / Я гуляю в парку. / Ти працюєш тут? Each sentence labels its verb form. Source pattern: Варзацька Grade 4 p.129 table.
- Exercise — quiz (~10 words intro): "Вибери правильну форму: Вона (читаю / читаєш / читає) книгу. Ти (знаю / знаєш / знає) цю пісню?" 8 multiple-choice items, all three persons tested.
- P3 (~70 words): Object forms as chunks — the learner may notice книга becomes книгу, пісня becomes пісню. Brief reassurance: that's the accusative case (coming in M20). For now, learn these as fixed phrases — читаю книгу, слухаю музику, готую вечерю. No rule required; recognition is enough at A1.
- Exercise — match-up (~10 words intro): "З'єднай особу з правильною формою: я ↔ ?, ти ↔ ?, він ↔ ?, вона ↔ ?, ми ↔ ?, вони ↔ ?." 6 pairs using слухати. Builds form recognition across all persons.
- P4 (~90 words): Plural forms for passive recognition — ми готуємо вечерю (we cook dinner), ви знаєте українську? (do you [pl.] know Ukrainian?), вони гуляють у парку (they walk in the park). Presented as natural sentences, not a grammar drill. Note -ємо/-єте/-ють endings. Mention: ви is also polite singular (formal address) — preview only, no drill.
- Exercise — fill-in context (~10 words intro): "Що ти ___? — Я ___ музику. (слухати). Де вона ___? — Вона ___ в офісі. (працювати)." 6 blanks combining verb form + context from dialogues.

---

## Підсумок — Summary (~165 words total)

- P1 (~80 words): Recap — Group I verbs (infinitive in -ати/-увати/-яти) conjugate with these endings: я -ю, ти -єш, він/вона -є, ми -ємо, ви -єте, вони -ють. The six core verbs: читати, знати, працювати, слухати, гуляти, готувати. To conjugate: remove -ти, add ending. A helpful anchor: "ти завжди -єш" — ти читаєш, ти слухаєш, ти гуляєш. That form is the most useful to drill first.
- P2 — Self-check (~85 words):
  - Conjugate слухати for я, ти, він/вона: → слухаю / слухаєш / слухає ✓
  - What's the ти form of працювати? → працюєш ✓
  - Say "She reads a new book" in Ukrainian: → Вона читає нову книгу ✓
  - Ask "What are you doing?" → Що ти робиш? ✓
  - Say two things you do every day: Я читаю... Я слухаю... (open production)
  - **Coming next:** M17 — Group II verbs (говорити, робити) — a different ending pattern.

Grand total: ~1155 base words + ~165 dialogue word counts = **~1320 words**
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
