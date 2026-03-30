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

Write the full prose content for module **19: Questions** (A1, A1.3 [Actions]).

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
module: a1-019
level: A1
sequence: 19
slug: questions
version: '1.1'
title: Questions
subtitle: Хто? Що? Де? — asking about the world
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Ask questions using хто, що, де, куди, коли, чому, як
- Use negation with не (verb) and ні (nothing/nobody)
- Form yes/no questions with intonation (no word order change)
- Combine question words with verbs from M16-M18
dialogue_situations:
- setting: A tourist asking a local for help navigating the city center
  speakers:
  - Турист
  - Перехожий (passerby)
  motivation: 'Question words: Де? Куди? Як? Коли? in real navigation'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone (extending M05): — Хто ти? — Я студент.
    — Що ти вивчаєш? — Я вивчаю українську. — Де ти живеш? — Я живу в Києві. — Коли
    ти працюєш? — Вранці. Question words demonstrated in real conversation.'
  - 'Dialogue 2 — At home: — Де моя книга? — Я не знаю.
    — А хто знає? — Мама знає. — Чому мама? — Тому що вона все знає! Questions
    + negation in practical context.'
- section: Питальні слова (Question Words)
  words: 300
  points:
  - 'Seven essential question words: Хто? (Who?) — Хто це? Хто говорить? Що? (What?)
    — Що це? Що ти робиш? Де? (Where?) — Де ти живеш? Де книга? Куди? (Where to?)
    — Куди ти ходиш? Коли? (When?) — Коли ти працюєш? Чому? (Why?) — Чому ти не працюєш?
    Як? (How?) — Як справи? Як тебе звати?'
  - 'Word order: question word + verb + subject (flexible): Де ти живеш? = Ти де живеш?
    (both acceptable). Yes/no questions: just raise intonation at the end: Ти говориш
    українською? ↑ (no special word needed). Чи ти говориш? — formal/written (optional
    for A1).'
- section: Заперечення (Negation)
  words: 300
  points:
  - 'Не = not (before verb): Я не знаю. Він не працює. Ми не розуміємо. Не goes directly
    before the verb — never separated. Review: Я не хочу. Мені не подобається. (from
    M15, M18)'
  - 'Ні = no (standalone) / nothing, nobody (with pronouns): Ні, я не знаю. (No, I
    don''t know.) Нічого (nothing), ніхто (nobody), ніколи (never), ніде (nowhere).
    Double negation is REQUIRED in Ukrainian: Я нічого не знаю. (literally: I nothing
    don''t know = I don''t know anything.) Ніхто не говорить. (Nobody speaks.) — unlike
    English, both не and ні- are needed.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Questions: Хто? Що? Де? Куди? Коли? Чому? Як? Yes/no: intonation only (Ти знаєш?
    ↑) Negation: не before verb (Я не знаю). Double negation: Ніхто не знає. Я нічого
    не бачу. Self-check: Ask 3 questions about a friend (Де...? Що...? Коли...?).
    Make 2 negative sentences (Я не... / Ніхто не...).'
vocabulary_hints:
  required:
  - хто (who)
  - що (what)
  - де (where)
  - куди (where to)
  - коли (when)
  - чому (why)
  - як (how)
  - не (not)
  - ні (no)
  recommended:
  - ніхто (nobody)
  - нічого (nothing)
  - ніколи (never)
  - жити (to live)
  - розуміти (to understand)
  - тому що (because)
activity_hints:
- type: quiz
  focus: 'Choose the right question word: ___ ти живеш? (Де/Що/Хто)'
  items: 8
- type: fill-in
  focus: 'Make it negative: Я знаю → Я не знаю, Хтось знає → Ніхто не знає'
  items: 8
- type: match-up
  focus: 'Match question to answer: Де ти живеш? ↔ У Києві.'
  items: 6
- type: quiz
  focus: 'Double negation: choose the correct Ukrainian sentence.'
  items: 6
connects_to:
- a1-020 (My Morning)
prerequisites:
- a1-018 (I Want, I Can)
grammar:
- 'Question words: хто, що, де, куди, коли, чому, як'
- Yes/no questions with rising intonation
- 'Negation: не before verb'
- 'Double negation: ніхто не + verb, нічого не + verb'
register: розмовний
references:
- title: Варзацька Grade 4, p.41
  notes: Question words in case system context (хто? що? кого? чого?).
- title: ULP Season 1, Episode 35
  url: https://www.ukrainianlessons.com/episode35/
  notes: Questions in Ukrainian — word order and intonation.

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

- **Confirmed (14/15):**
  - хто (noun/pronoun) ✅
  - що (conj, noun) ✅
  - де (adv, part) ✅
  - куди (adv) ✅
  - коли (adv/conj — 7 matches including homophone кіл; коли as adverb confirmed) ✅
  - чому (adv; also дативна форма що) ✅
  - як (adv, conj) ✅
  - не (part) ✅
  - ні (part) ✅
  - ніхто (noun/pronoun) ✅
  - нічого (noun; gen. form of ніщо) ✅
  - ніколи (adv) ✅
  - жити (verb) ✅
  - розуміти (verb) ✅

- **Not found as single unit (1/15):**
  - **тому що** — NOT FOUND as a single token ⚠️ (expected: it is a two-word conjunction; both тому and що exist individually in VESUM. Use as two words, not hyphenated. No content problem.)

---

## Textbook Excerpts

### Section: Питальні слова (Question Words)

> «Коли? Де? Як? Скільки? Чому? — слова, якими найчастіше починаються питальні речення.»
> **Source: Grade 2, Кравцова, tier 2** (p. 108)

> «Питальні займенники вживаються в питальних реченнях. Ці займенники вам добре знайомі, адже вони є питаннями до всіх іменних частин мови: хто? що? який? чий? котрий? скільки?»
> **Source: Grade 6, Літвінова, tier 1** (p. 264)

> «Хто? що?» used to distinguish living (хто) vs. non-living (що) nouns from first lessons.
> **Source: Grade 1, Большакова, tier 2** (p. 6) — earliest introduction of хто/що

### Section: Діалоги (Dialogues)

> Etiquette formulas from textbook include: «Як тебе (вас) звати? Як ся маєш? Як ваші справи?» — confirmed as natural classroom dialogue phrases.
> **Source: Grade 6, Авраменко, tier 1** (p. 8) — direct confirmation of plan's «Як справи?» and «Як тебе звати?»

### Section: Заперечення (Negation)

> «Написання ні з різними частинами мови: із заперечними займенниками й прислівниками — РАЗОМ: ніхто, ніякий, нічий… ніде, ніколи, ніяк, нітрохи»
> **Source: Grade 10, Авраменко, tier 2** (p. 148)

> «Заперечні займенники вказують на відсутність особи, предмета, їхніх ознак чи кількості. Утворюємо від питальних додаванням префікса ні: ніщо, ніхто, ніякий, нічий, ніскільки»
> **Source: Grade 6, Заболотний, tier 2** (p. 203) — canonical negative pronoun introduction

> «Ніхто не може змусити вас робити те, що ви вважаєте неправильним» — double negation required (ніхто + не).
> **Source: Grade 6, Літвінова, tier 1** (p. 269)

### Section: Підсумок (Summary)

> No direct textbook match needed — summary section synthesises rules already grounded above.

---

## Grammar Rules

- **Double negation (подвійне заперечення):** Правопис 2019 RAG returned no direct result for "заперечення". However, the rule is confirmed by multiple-tier textbooks: Grade 6 Заболотний, Grade 6 Літвінова, Grade 10 Авраменко all show mandatory double negation — **ніхто не говорить**, **я нічого не знаю** — as the standard Ukrainian norm. Unlike English, both the ні- pronoun/adverb AND не before the verb are obligatory.

- **Написання ні разом/окремо:** Confirmed by Grade 10 Авраменко and Grade 10 Кaрамaн: ніхто, ніколи, ніде, нічого — РАЗОМ. With preposition splits into three words: ні з ким, ні до кого.

- **Не перед дієсловом (окремо завжди):** Consistently shown across all grades. «Не» is always written separately from the verb: **я не знаю**, **він не працює**, **ми не розуміємо**.

- **Word order in questions:** Confirmed in grade-level examples — question word + verb order is natural but flexible; both «Де ти живеш?» and «Ти де живеш?» are acceptable in Ukrainian. The plan's note on this is accurate.

---

## Calque Warnings

- **«Як справи?»** — Style guide search returned справа/діло guidance. Антоненко-Давидович distinguishes "справа" (справа/діло as near-synonyms). «Як справи?» is a well-established Ukrainian greeting phrase — confirmed in Grade 6 Авраменко textbook as an etiquette formula («Як ваші справи?»). **✅ Not a calque — confirmed natural Ukrainian.**

- **«Як тебе звати?»** — Confirmed in Grade 6 Авраменко textbook directly («Як тебе (вас) звати?»). ✅ Natural Ukrainian etiquette formula. No calque issue.

- **«Я нічого не знаю»** — Антоненко-Давидович cites «Справді, нічого не знаю» from «живих уст» as a natural Ukrainian sentence. ✅ Double negation is correct Ukrainian, not a calque.

- **«тому що»** (because) — Natural Ukrainian subordinating conjunction. No calque issue. Written as two separate words. ✅

---

## CEFR Check

- **де**: A1 (прислівник) — ✅ On target
- **куди**: A1 (прислівник) — ✅ On target
- **коли**: A1 (прислівник) — ✅ On target
- **чому**: A1 (прислівник) — ✅ On target
- **як**: A1 (прислівник) — ✅ On target
- **жити**: A1 (дієслово недок.) — ✅ On target
- **розуміти**: A1 (дієслово недок.) — ✅ On target
- **хто**: PULS matched semantic neighbour «чий» (A1) — хто itself is a core A1 pronoun, earliest introduced in Grade 1 textbooks ✅
- **що**: PULS matched «чого» (B2) — this is a lookup artefact (чого = genitive form); що as a question word is Grade 1 / A1 by every standard ✅
- **ніхто**: PULS matched «нічий» (B2) — ⚠️ **Monitor**: ніхто itself is standard A1 grammar content (introduced in A1 question/negation units in all major curricula). The PULS B2 match is for нічий (a possessive negative pronoun), not ніхто. Safe to use at A1, but keep the introduction brief — introduce ніхто/нічого/ніколи as pattern examples of double negation, not as full vocabulary items requiring production.

---

## Summary of Blockers

| Item | Status | Action |
|------|--------|--------|
| тому що | ⚠️ Not in VESUM as unit | Write as two words — no content change needed |
| ніхто/нічого/ніколи CEFR | ⚠️ PULS neighbours at B2 | Introduce as recognition items / double-negation pattern; not active production vocab |
| коли VESUM match | ℹ️ Homophones returned | Word exists; no issue |
| All other vocabulary | ✅ Confirmed A1 | Proceed |
| Dialogues | ✅ Grounded in textbooks | Авраменко Gr.6 confirms both dialogue situations |
| Double negation rule | ✅ Confirmed in 3 textbooks | State rule clearly: both ніхто AND не required |
| Calques | ✅ None found | All key phrases confirmed natural Ukrainian |
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
# Verified Knowledge Packet: Questions
**Module:** questions | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 4
> **Score:** 0.33
>
> 4
> ЧОГО  Я  ВЧУСЯ?
> Вдома вчить мене матуся,
> в школі вчить мене учитель,
> і сама я добре вчуся
> рідним словом говорити.
> Вчусь не тільки говорити,
> а й читати і писати.
> Щоб усі раділи діти,
> щоб пишались мама й тато.
> Щоб пішла між люди слава,
> щоб сказали: «От дитинка
> добра, мудра і ласкава.
> Це маленька українка!»
> Що таке текст
> 1
> Розпізнаю текст за його основними ознаками
> 	 	
> 1   Прочитайте вірш Михайла Маморського. Про що розповідається 
> в кожному з речень? Чи пов’язані вони одне з одним? Чи 
> становлять ці речення текст?
> Досліди, що озна-
> чає слово канікули. 
> Де про це можна 
> діз­натися?
> Я — дослідник
> Я — дослідниця
> Поділися своїми враженнями 
> про канікули з однокласниками 
> (однокласницями). Чи можна 
> назвати твою розповідь текстом?
> Перевірте свої 
> міркування за поданим 
> висновком.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 222
> **Score:** 0.50
>
> 222
> Відомості із синтаксису й пунктуації. Обставина
> Вправа 361
> Виконайте тест . У завданнях 1 і 2 лише один правильний варіант відповіді, 
> у  завданні 3 потрібно встановити відповідність між варіантами .
> 1. Обставинами є  усі виділені слова, ОКРІМ
> Поки ми їдемо до Києва, я думаю про неї. Зараз восьма ве-
> чора, а значить, прабабуня вечеряє. У кімнаті цокає годинник 
> і про щось торохтить радіо.
> А до Києва
> Б зараз
> В у кімнаті
> Г про щось
> 2. Непоширеним є  речення
> А Створіть своє родинне дерево через наш сервіс.
> Б Спочатку додайте запис про себе.
> В Далі вводьте інформацію про родичів.
> Г Ми допоможемо!
> 3.

## Питальні слова (Question Words)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 245
> **Score:** 0.33
>
> Ч а с т и н и   м о в и
> Самостійні 
> Іменник 
> сонце
> хто? що?
> Прикметник
> сонячний, мамин
> який? чий?
> Числівник
> три, третій
> скільки? котрий?
> Займенник
> я, ти, він
> хто? що?
> Дієслово
> сидіти
> що робити? що зробити?
> Прислівник 
> сонячно, восени
> як? де? коли? куди?
> Службові
> Прийменник
> на, в, з, до
> Не відповідають на 
> питання
> Сполучник
> і, й, та, але
> Частка
> не, б, хай
> В и д и  р е ч е н ь
> За метою 
> висловлювання
> За емоційним 
> забарвленням
> За будовою
> розповідне
> окличне
> просте
> питальне
> неокличне
> складне
> спонукальне
> Ч л е н и   р е ч е н н я
> Головні
> Другорядні
> Підмет
> Присудок
> Означення
> Обставина
> Додаток
> хто? 
> що?
> що робить?
> що зробить?
> який? чий?
> як? де? 
> коли?
> та ін.
> кого? чого? 
> кому? чому? 
> та ін.

> **Source:** golub, Grade 5
> **Section:** Сторінка 14
> **Score:** 0.25
>
> 14
>  
>  А як тлумачить це слово словник? Випишіть тлумачення слова 
> «книжка».
>  
> ІІ   Напишіть есе «Книжка в моєму житті». У разі потреби скорис-
> тайтеся схемою.
> КНИЖКА
> Комусь вона …
> У чиїйсь уяві книжка 
> постає …
> А от 
> для мене ...
>  Для когось 
> книжка — …
> Хтось із нею 
> пов‘язує …
>  
> ІІІ   Погортайте книжку, яку ви нещодавно прочитали. Випишіть 
> із неї слова, що стали для вас відкриттям. З’ясуйте за словни-
> ком їхнє значення і запишіть у зошит. Перевірте, чи знають 
> їх однокласники та однокласниці.
> ОДНОЗНАЧНІ Й БАГАТОЗНАЧНІ СЛОВА
> § 4
> Уява — крок до здійснення мрії
> Якщо ти можеш щось уявити — ти можеш цього досягти (З. Зіглар).
> А той, хто робить кроки до мети, пройде крізь всі вибоїни й тенета, 
> бо сенс якраз у тому, щоб іти! (І.

## Заперечення (Negation)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 245
> **Score:** 0.25
>
> Ч а с т и н и   м о в и
> Самостійні 
> Іменник 
> сонце
> хто? що?
> Прикметник
> сонячний, мамин
> який? чий?
> Числівник
> три, третій
> скільки? котрий?
> Займенник
> я, ти, він
> хто? що?
> Дієслово
> сидіти
> що робити? що зробити?
> Прислівник 
> сонячно, восени
> як? де? коли? куди?
> Службові
> Прийменник
> на, в, з, до
> Не відповідають на 
> питання
> Сполучник
> і, й, та, але
> Частка
> не, б, хай
> В и д и  р е ч е н ь
> За метою 
> висловлювання
> За емоційним 
> забарвленням
> За будовою
> розповідне
> окличне
> просте
> питальне
> неокличне
> складне
> спонукальне
> Ч л е н и   р е ч е н н я
> Головні
> Другорядні
> Підмет
> Присудок
> Означення
> Обставина
> Додаток
> хто? 
> що?
> що робить?
> що зробить?
> який? чий?
> як? де? 
> коли?
> та ін.
> кого? чого? 
> кому? чому? 
> та ін.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 31
> **Score:** 0.50
>
> 28
> Багатозначне слово може мати кілька антонімічних пар. 
> ПОРІВНЯЙМО:
>  тихий (який здійснюється повільно) – швидкий;
>  тихий (який звучить слабо) – голосний;
>  тихий (без хвилювання) – тривожний.
> Є спеціальні словники антонімів. 
> Антоніми допомагають:
> чітко розрізнити поняття
> висловити протилежні думки
> яскраво й образно показати різні явища
> Зверніть увагу!
> Слова на зразок старий – нестарий не є антонімами, бо 
> перше слово стверджує наявність ознаки, а друге – просто її 
> заперечує. Але слова воля – неволя, друг – недруг є антоні-
> мами, бо в цих випадках префікс не- формує слово з новим 
> лексичним значенням.
> 55.	 І. Спишіть прислів’я, розкриваючи дужки та розставляючи про­
> пущені розділові знаки. Поясніть значення двох з поданих прислів’їв.
> 1. Маленька праця краща за велике безділ(л)я. 2.

## Підсумок — Summary

> **Source:** savchenko, Grade 3
> **Section:** Сторінка 122
> **Score:** 0.50
>
> Знаю…
>  Нàзви казок, які ти прочитав/прочитала.
>  Хто автори прочитаних байок?
>  З якої байки висновок: на себе не надійся, чужому лихові 
> не смійся?
>  У яку країну мандрував Білячок?
> Розумію, можу пояснити…
>  Які особливості побудови тексту має п’єса?
>  Чому Роман з п’єси-казки «Стрімкий, як вітер» вирішив
> залишити дельфінарій?
>  Чому прочитані казки можна назвати чарівними?
>  Чому тільки Мартіно вдалося пройти дорогу, яка нікóди 
> не вела?
> Вмію…
>  Визначати головну думку в прочитаних творах.
>  Знаходити висновок (мораль) байки.
>  Визначати, які вчинки дійових осіб позитивні, а які — 
> негативні.
>  Брати участь в інсценізації казки, п’єси.
>  Скласти план прочитаного твору та переказати його зміст.

> **Source:** , Grade 4
> **Section:** Сторінка 128
> **Score:** 0.50
>
> — А куди ти підеш? — знову питає його сорока.
> — Піду в інший ліс, де мене ніхто не знає, де люди доб­
> рі, а собаки лагідні.
> Тоді сорока сказала:
> — Там, куди ти йдеш, добра тобі не буде, бо звички твої 
> погані й зуби в тебе гострі. Отож усі й ставляться так до тебе.
> •  Випишіть із тексту сполучення особових займенників і слів, 
> від яких вони залежать. Визначте особу, число й відмінок 
> займенників.
> Зразок
> Жити (кому?) мені — 1 -ша ос., Д. в., одн.
> •  Допишіть золоте правило «Стався до людей так, як би ти хотів 
> (хотіла), щоб вони ставилися до ...». Підкресліть займенники.
> 290.

## Grammar Reference

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 158
> **Score:** 0.50
>
> 158
> Мої навчальні досягнення
> Карта пам’яті: від тексту — до мене
> Прочитайте текст.
> У тому темному лісі не живуть 
> ні звірі, ні птахи, ні метелики, ні ко-
> махи. Ніхто не живе, бо він холод-
> ний. У ньому виють не вовки, а Дикі 
> Вітри. Вони виють щоранку, щодня 
> та щоночі. Двадцять чотири годи-
> ни на добу! Вітри сідають на дебе-
> лі гілляки старезних сосон, звішу-
> ють довгі ноги й так відпочивають. 
> Інакше не вміють. Тоді неймовір-
> ною тишею вражає ліс. Чути, як 
> дихає сосна, як тремтить осика, 
> як шелестить трава. Та одного дня 
> зранку, о 10-й годині, тут з’явилася 
> Біла Панночка.  Вона ступала так 
> легенько, наче боялася на когось 
> наступити. Здивовані Вітри рап-
> том замовкли… (За Г. Кирпою).


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Питальні слова (Question Words)` (~300 words)
- `## Заперечення (Negation)` (~300 words)
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
  1. **A tourist asking a local for help navigating the city center**
     Speakers: Турист, Перехожий (passerby)
     Why: Question words: Де? Куди? Як? Коли? in real navigation

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

**Required:** хто (who), що (what), де (where), куди (where to), коли (when), чому (why), як (how), не (not), ні (no)
**Recommended:** ніхто (nobody), нічого (nothing), ніколи (never), жити (to live), розуміти (to understand), тому що (because)

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

- P1 (~30 words): Brief intro — in Ukrainian, questions use special question words (питальні слова). Two dialogues below show them in real conversation before we study each word.
- Dialogue 1 (~110 words): Getting to know someone — 8-turn exchange between two students meeting for the first time. Covers: — Хто ти? — Я студент. — Що ти вивчаєш? — Я вивчаю українську мову. — Де ти живеш? — Я живу у Львові. — А де ти народився? — У Харкові. — Коли ти приїхав? — Минулого року. — Як тебе звати? — Мене звати Олег. Each question word bolded; short explanation in parentheses after each turn.
- Dialogue 2 (~110 words): At home — 6-turn exchange between siblings. Covers questions + negation: — Де моя книга? — Я не знаю. — А хто знає? — Ніхто не знає. — Що це на столі? — Нічого цікавого. — Чому ти не відповідаєш? — Тому що я не чув. Question words and negation appearing naturally together; not і ніхто bolded.
- P2 (~80 words): Comprehension bridge — 3 observation sentences pointing out what learners just saw: (1) question words come at the start, (2) word order stays the same after them, (3) не and ніхто/ніщо often appear together. Sets up the next two sections.

---

## Питальні слова (~330 words total)

- P1 (~80 words): Introduce the seven core question words as a set: Хто? — Що? — Де? — Куди? — Коли? — Чому? — Як? Brief framing: these seven cover almost everything you want to ask at A1. Each word gets its English gloss and one anchor example sentence drawn from the dialogues above (e.g., Хто ти? Що ти робиш? Де ти живеш? Куди ти йдеш? Коли ти працюєш? Чому ти не відповідаєш? Як тебе звати?).
- P2 (~70 words): Де vs. Куди distinction — the one pair learners confuse. Де = location (static): Де ти живеш? Де книга? Куди = direction (movement toward): Куди ти йдеш? Куди вони їдуть? Rule: де with жити/бути/стояти; куди with іти/їхати/ходити. 2 contrast pairs shown side by side.
- Exercise: quiz — 8 items "Choose Де or Куди: ___ ти ходиш щодня? / ___ твоя сестра? / ___ вони їдуть?" etc.
- P3 (~80 words): Word order — question word + verb + subject, but all permutations acceptable in spoken Ukrainian: Де ти живеш? = Ти де живеш? = Живеш де ти? (informal). The question word carries the emphasis regardless of position. 3 example pairs showing this flexibility.
- P4 (~70 words): Yes/no questions — no special word needed, just rising intonation (↑) at the end: Ти говориш українською? ↑ Він живе тут? ↑ Вона знає? ↑ Contrast with English (do/does). Note чи (formal/written, e.g., Чи ти розумієш?) — recognise it, but intonation is normal for A1 speech.
- Exercise: match-up — 6 pairs matching question word to answer: Де ти живеш? ↔ У Києві. / Коли ти працюєш? ↔ Вранці. / Як тебе звати? ↔ Мене звати Тарас. / Куди ти йдеш? ↔ До школи. / Чому ти не їси? ↔ Тому що я не голодний. / Хто це? ↔ Це моя сестра.

---

## Заперечення (~330 words total)

- P1 (~80 words): Introduce не — goes directly before the verb, never separated. 5 examples recycling verbs from M16-M18: Я не знаю. Він не працює. Ми не розуміємо. Вона не хоче. Вони не говорять. Contrast with English: "do not" is two words; Ukrainian не is one particle glued to the verb. Stress note: не is usually unstressed (becomes enclitic).
- P2 (~80 words): Introduce ні as a standalone "no": Ти знаєш? — Ні, не знаю. Then the ні- negative pronouns: ніхто (nobody), нічого (nothing), ніколи (never), ніде (nowhere), нікуди (to nowhere). Table of 5 forms with English gloss and one example sentence each.
- P3 (~100 words): Double negation — the most important rule in this section. Ukrainian REQUIRES both the ні- word AND не before the verb. Wrong (English pattern): *Ніхто знає. Correct: Ніхто не знає. 4 full example pairs: Я нічого не знаю. (I don't know anything.) / Ніхто не говорить. (Nobody speaks.) / Вона ніколи не запізнюється. (She is never late.) / Ми ніде не були. (We haven't been anywhere.) Explicit note: this is NOT a logic error — it is standard Ukrainian grammar.
- Exercise: fill-in — 8 items: transform affirmative → negative using the correct form: Я знаю → Я не знаю / Хтось знає → Ніхто не знає / Він завжди приходить → Він ніколи не приходить / Вона щось бачить → Вона нічого не бачить, etc.
- P4 (~70 words): Short contrast paragraph — не vs ні- in a side-by-side: не = negates one verb (Я не знаю); ні-word = negates the entire idea + must still use не with verb (Ніхто не знає). Final 2 example sentences combining a question word with negation: Хто це? — Ніхто. Що ти бачиш? — Нічого не бачу.
- Exercise: quiz — 6 items on double negation: choose the correct Ukrainian sentence from two options, e.g., (A) Ніхто знає. (B) Ніхто не знає. ✓

---

## Підсумок (~150 words total)

- P1 (~150 words): Summary in bullet format as specified by plan:
  - **Питальні слова:** Хто? Що? Де? Куди? Коли? Чому? Як? — 7 words, question word first, flexible word order.
  - **Де vs. Куди:** Де — location (Де книга?); Куди — direction (Куди ти йдеш?).
  - **Так/ні питання:** rising intonation only — Ти знаєш? ↑ No extra word needed.
  - **Не:** directly before verb — Я не знаю. Він не приходить.
  - **Подвійне заперечення:** ніхто/нічого/ніколи/ніде + не + дієслово — Ніхто не знає. Я нічого не бачу.
  - **Self-check — try this now:** (1) Ask 3 questions about a friend: Де вона живе? Що він вивчає? Коли вони приходять? (2) Make 2 negative sentences: Я нічого не знаю. / Ніхто не розуміє. (3) Turn a statement into a yes/no question: Він говорить українською. → Він говорить українською? ↑

---

Grand total: ~1140 + ~190 (exercises) = ~1330 words
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
