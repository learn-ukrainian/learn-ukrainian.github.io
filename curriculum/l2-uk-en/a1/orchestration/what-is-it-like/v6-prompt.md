<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 391 words (target: 1200, minimum: 1020)
- NOTE: Plan expects 4 exercise(s) but content has 3
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

Write the full prose content for module **9: What Is It Like?** (A1, A1.2 [My World]).

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
module: a1-009
level: A1
sequence: 9
slug: what-is-it-like
version: '1.2'
title: What Is It Like?
subtitle: Великий стіл, нова книга — describing things
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Use adjectives that agree with nouns in gender (nominative case only)
- Ask "What kind?" with який/яка/яке
- Describe objects and rooms using common adjective pairs
- Build descriptive sentences combining M08 nouns with M09 adjectives
dialogue_situations:
- setting: 'At a weekend book fair — browsing books, maps, and posters. Describe items:
    новий атлас (m), цікава книга (f), старе фото (n), великий плакат (m), маленька
    листівка (f, postcard). NOT bags or furniture.'
  speakers:
  - Тарас
  - Софія
  motivation: Який/яка/яке? with книга(f), атлас(m), фото(n), плакат(m), листівка(f)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Describing a room (Вашуленко Grade 3 p.131 ''Моя кімната''): — Яка
    твоя кімната? — Моя кімната велика і світла. — А стіл? — Стіл новий. А ліжко —
    старе. Adjective agreement emerges from real description.'
  - 'Dialogue 2 — Shopping (window shopping): — Яка гарна сумка! — Так, але
    вона дорога. — А телефон? Який він? — Він великий і дешевий.'
- section: Який? Яка? Яке? (What kind?)
  words: 300
  points:
  - 'The question ''What kind?'' changes by gender — same pattern as мій/моя/моє:
    Який стіл? (m) → Великий стіл. Яка книга? (f) → Нова книга. Яке вікно? (n) → Чисте
    вікно.'
  - 'Пономарова Grade 3 p.98: Adjective has the same gender as the noun. Masculine:
    -ий (великий, новий, чистий) Feminine: -а (велика, нова, чиста) Neuter: -е (велике,
    нове, чисте) Soft-stem adjectives (-ій/-я/-є like синій) come in M10 Colors. This
    pattern will reappear in every case — learn it well now.'
- section: Прикметники (Common Adjectives)
  words: 300
  points:
  - 'Taught in pairs (opposites — easier to remember): великий ↔ маленький (big ↔
    small) новий ↔ старий (new ↔ old) гарний ↔ поганий (nice/beautiful ↔ bad) чистий
    ↔ брудний (clean ↔ dirty) дорогий ↔ дешевий (expensive ↔ cheap) світлий ↔ темний
    (light ↔ dark)'
  - 'Building descriptions with M08 objects: У мене є великий стіл. Моя кімната маленька,
    але гарна. Вікно велике і чисте. Стілець старий, а ліжко — нове. Note: ''а'' =
    and/but (contrast), ''і'' = and (parallel).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Self-check: What ending does a masculine adjective have? (-ий/-ій) Feminine?
    (-а/-я) Neuter? (-е/-є) Describe your room in 3 sentences using adjectives.'
vocabulary_hints:
  required:
  - який, яка, яке (what kind? — m/f/n)
  - великий (big)
  - маленький (small)
  - новий (new)
  - старий (old)
  - гарний (nice, beautiful)
  - чистий (clean)
  - дорогий (expensive)
  - дешевий (cheap)
  recommended:
  - поганий (bad)
  - брудний (dirty)
  - світлий (light, bright)
  - темний (dark)
  - а (and/but — contrast)
  - але (but)
activity_hints:
- type: fill-in
  focus: 'Add correct adjective ending: нов__ книга, велик__ стіл, чист__ вікно'
  items: 10
- type: match-up
  focus: 'Match adjective opposites: великий ↔ маленький'
  items: 6
- type: quiz
  focus: Який/яка/яке? Choose correct question word.
  items: 6
- type: fill-in
  focus: Describe the room using given nouns and adjectives
  items: 6
connects_to:
- a1-010 (Colors)
prerequisites:
- a1-008 (Things Have Gender)
grammar:
- Adjective-noun agreement in nominative (-ий/-а/-е pattern)
- Question words який/яка/яке/які
- Adjective opposites as vocabulary strategy
- а (contrast) vs і (parallel)
register: розмовний
references:
- title: Пономарова Grade 3, p.98
  notes: '''Прикметник має такий рід, як іменник, з яким він зв''язаний.'''
- title: Вашуленко Grade 3, p.128-131
  notes: Adjective agreement exercises, 'Моя кімната' description task.

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

- **Confirmed (17/17):** який (adj), яка (adj form of який), яке (adj form of який), великий (adj), маленький (adj), новий (adj), старий (adj), гарний (adj), чистий (adj), дорогий (adj), дешевий (adj), поганий (adj), брудний (adj), світлий (adj), темний (adj), а (conj/part/intj), але (conj/part/intj)
- **Not found:** — (none)

All 17 plan vocabulary words are fully attested in VESUM. No substitutions needed.

---

## Textbook Excerpts

### Section: Діалоги — Describing a room
> «Одна кімната велика. У ній є зручний вихід на балкон. Друга — менша, але вона світла й затишна.»
> Source: Вашуленко, Grade 3, p.130 (§41 «Змінювання прикметників за родами»)

**Note:** Plan cites p.131 «Моя кімната»; RAG confirms adjacent p.130 has the room description. Same lesson unit — page reference is ±1 due to scan pagination. Content fully confirmed. The exact string «Яка твоя кімната? — Моя кімната велика і світла» is a natural A1 derivative of this textbook context.

### Section: Діалоги — Shopping (window shopping)
> «— Боже ж мій, яка сумка! [...] Це дешевий клатч! [...] Справді, для тебе — дешевий?»; also: «— Скільки вона коштує? — Дев'ять тисяч гривень.» (music shop dialogue with price question)
> Source 1: Заболотний, Grade 8, p.194 (natural shopping/window-shopping scene with дорогий/дешевий)
> Source 2: Авраменко, Grade 6, p.18 (§8 «Пряма мова. Діалог» — model shop dialogue)

The Grade 8 extract is too lexically complex for A1. However it confirms that «яка сумка!» + price discussion is a **textbook-attested natural situation**, not an invented one. The Grade 6 shop dialogue confirms the pattern «Скільки це коштує?» as the natural price question. Plan dialogue is pedagogically grounded. ✅

### Section: Який? Яка? Яке? — Gender agreement table
> «Прикметники чоловічого роду мають закінчення -ий, -ій (гарний чоловік, синій колір), жіночого роду — -а, -я (гарна жінка, синя хустка), середнього роду — -е, -є (гарне пальто, синє небо).»
> Source: Пономарова, Grade 3, p.99 (§ «Визначаю родові закінчення прикметників»)

> Corroborated by table in Кравцова, Grade 3, p.72: «який? ч. р. → -ий, -ій / яка? ж. р. → -а, -я / яке? с. р. → -е, -є / які? → -і»
> Source: Кравцова, Grade 3, p.72

**Note:** Вашуленко (p.130) lists neuter ending as «-о, -є» (archaic/regional variant). Пономарова and Кравцова give «-е, -є», which matches the plan's examples (чисте вікно, нове ліжко). Plan is correct — use Пономарова/Кравцова as authority here.

### Section: Прикметники — Antonym pairs
> «Слова «великий» і «малий», «сідати» і «вставати», «холодний» — «теплий» антонімами звати.»; also «темний — світлий, сідати — уставати» as canonical antonym pairs.
> Source 1: Кравцова, Grade 3, p.95 (вірш про антоніми — explicit antonym pairs cited)
> Source 2: Авраменко, Grade 10, p.28 (антоніми — «темний — світлий» as example pair)
> Source 3: Вашуленко, Grade 3, p.56 (§18 «Протилежні за значенням слова — антоніми»)

Teaching adjectives in antonym pairs is **explicitly the Ukrainian textbook method** from Grade 3 upward. Plan structure is fully textbook-aligned. ✅

### Section: Підсумок — Self-check summary
No direct textbook match for a self-check summary of adjective gender endings specifically at A1 level. However, the question pattern «Яке закінчення мають прикметники чоловічого/жіночого/середнього роду?» is the standard Кравцова/Пономарова consolidation format (Grade 3). Plan's self-check questions («What ending does a masculine adjective have?») directly mirror this textbook approach. ✅

---

## Grammar Rules

- **Adjective gender agreement (endings -ий/-а/-е):** Confirmed by Пономарова Grade 3 §«Визначаю родові закінчення прикметників» and Кравцова Grade 3 p.72. Rule: «Прикметники в однині змінюються за родами. Чол. рід: -ий/-ій; Жін. рід: -а/-я; Сер. рід: -е/-є.»

- **Правопис §33** (returned by query): Covers adjective *derivational* suffixes (-н-, -ист-, -ев- etc.) — **not** relevant to this module's gender agreement rule. Gender agreement endings for adjectives are covered in Ukrainian school grammar (morphology), not Правопис 2019 per se. No Правопис section conflict — gender agreement is unambiguous.

- **Adjective agrees in gender with its noun:** Confirmed by Заболотний Grade 11 (coordination/узгодження rule): «Залежне слово вживається у тому самому роді, числі й відмінку, що й головне слово» — covers the agreement principle underlying this module.

---

## Calque Warnings

- **«гарний» vs «красивий»:** ✅ OK — Антоненко-Давидович explicitly recommends гарний over красивий: *«Який красивий будинок! — не замислюючись над тим що, може краще сказати: гарний (чудовий) будинок»*. Plan correctly uses **гарний**. Do NOT use красивий in this module.

- **«а» (contrast) vs «але» (adversative):** ✅ OK — Антоненко-Давидович confirms «а» is used for contrast in Ukrainian (е.g. «Брати працювали, а я сидів»). Plan correctly distinguishes «а» (contrast/and-but) from «але» (stronger adversative). Note: also confirmed in plan example «Стілець старий, а ліжко — нове» — this is textbook-natural.

- **«дешевий/дорогий»:** ✅ No calque issues. Both are native Ukrainian words with no style guide concerns.

---

## CEFR Check

| Word | PULS Level | Status |
|---|---|---|
| який | A1 | ✅ On target |
| великий | A1 | ✅ On target |
| маленький | A1 | ✅ On target |
| новий | A1 | ✅ On target |
| старий | A1 | ✅ On target |
| гарний | A1 | ✅ On target |
| дорогий | A1 | ✅ On target |
| поганий | A1 | ✅ On target |
| темний | A1 | ✅ On target |
| світлий | A1 | ✅ On target |
| чистий | A2 | ⚠️ One level above target |
| брудний | A2 | ⚠️ One level above target |
| дешевий | A2 | ⚠️ One level above target |

**Assessment on A2-tagged words:** чистий, брудний, and дешевий are PULS-tagged A2, but this is **M09 in A1.2** (not A1.1 beginner). All three are: (a) VESUM-confirmed standard adjectives, (b) part of the pedagogically essential antonym pairs (чистий↔брудний, дорогий↔дешевий), and (c) thematically necessary for describing rooms and shopping. **Recommend retaining all three** — they are appropriate stretch vocabulary for A1.2 and directly serve the module's paired-antonym teaching strategy.
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
# Verified Knowledge Packet: What Is It Like?
**Module:** what-is-it-like | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 131
> **Score:** 0.50
>
> 131
> 	
>   Перевірте свої міркування за поданим висновком. 
> крісло
> зручне
> Шукаймо 
> прикметники до назв 
> предметів інтер’єру!
> 	 	
> 3   Склади усну розповідь на тему «Моя кімната», використову-
> ючи іменники з довідки. Добери до іменників прикметники 
> і використай їх у тексті. 
> Кімната, двері, вікно, стеля, стіни, коридор, шафа, стіл, стілець, 
> тумбочка, ліжко, підлога. 
> Довідка
> Навчаюся визначати рід і число прикметників  
> за іменником
> Рід і число прикметників визначаються за формами 
> роду і числа іменників, з якими зв’язані прикметники. 
> 	 	
> 4   Прочитайте сполучення слів і порівняйте їх.

## Який? Яка? Яке? (What kind?)

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 66
> **Score:** 0.50
>
> 66
> Знайди букви Я і я в рядку.
> Я 
> Ф 
> В 
> Р 
> я 
> р 
> ф 
> ь 
> я 
>  
>  яб 
> яв 
> яг 
> яд 
> яз 
> як 
> ял 
> ям 
> ян 
> яп
>  яр 
> яс 
> ят 
> ях 
> яш 
> ящ 
> яб 
> яв 
> яг 
> яд
>  
> Знайди слово — підпис до малюнка. 
>  
> ягода 
> яма 
> ясен 
> маяк
>  
> ялина 
> явір 
> язик 
> мрія
>  
> яблуня 
> якір 
> ящик 
> надія
>  
> Буква я позначає два звуки [йа] на початку слова і складу.
> М А|Я К
> Я К
> [й а]
> [й а]
> «Зайві» слова
>  Над болотом летить яблуко, крапля, чапля.
>  У вазі стояла конвалія, мелодія, паляниця.
>  У дворі росла парасоля, тополя, яблуня.
> 1
> 2
> 3
> 4
> Я я
> я|бл у|к о

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 35
> **Score:** 0.50
>
> 35
> Книжки треба шанувати. Не можна 
> їх бруднити, рвати. Пошкоджені книжки 
> слід полагодити.
> Прочитай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Якщо речення вимовляють з особ­
> ливим почуттям, із підсилювальною 
> інтонацією, то вони стають оклич-
> ними. У кінці окличних речень став-
> лять знак оклику.
> 2   Прочитай текст. Визнач, які це речення 
> за метою висловлювання.
> 	 	
> 3   Розгляньте малюнки. Складіть за одним із них невеликий 
> текст, використовуючи окличні речення. Прочитайте його 
> з потрібною інтонацією.
> 	 	
>   Перебудуй речення так, щоб вони стали спонукальними. Запиши 
> утворений текст.
>   Запишіть текст, ставлячи потрібні розділові знаки в кінці речень.

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 36
> **Score:** 0.50
>
> 36
> Запиши слова з буквою ї. Визнач звуки, які позначає буква ї.
> Мій — мої, твій — твої, вія — вії, лілія — лілії, лінія — лінії.
>  
> Утвори і запиши речення за зразком.
> Зразок. Колюче їжаченя з’їло слимака.
> Колючий
> Колюча
> Колюче
> Колючі
> їжак
> їжачиха
> їжаченя
> їжаки
> їсть
> з’їла
> з’їло
> їдять
> слимака.
> жука.
> равлика.
> черв’яка.
>  
> Редагуємо
> Їжак і жаба допомагають 
> садівнику поїдати комах. 
>  
> Запиши речення на вибір, у якому: 1) пояснюється, чому їжак 
> не робить запаси на зиму; 2) описується поведінка їжачка 
> восени. 
> Восени їжачок носить на своїх голках листя, а не їжу. 
> Їжак не запасає їжу на зиму. Узимку він не їсть, а спить. 
> Тому і готує звірятко тепле гніздо для зимівлі. 
> • Склади речення за питаннями.
> Коли?
> Хто?
> Що?
> Що робить?
> Де?
> скЛаД. наГоЛос.

## Прикметники (Common Adjectives)

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 31
> **Score:** 0.33
>
> СЛОВО 
> ЗНАЧЕННЯ СЛОВА
> А
> У розділі ти будеш вивчати:
> г
> СЛОВА, БЛИЗЬКІ
> ЗА ЗНАЧЕННЯМ
> СЛОВА, ПРОТИЛЕЖНІ 
> ЗА ЗНАЧЕННЯМ
> красивий, гарний, 
> хороший
> працювати — 
> відпочивати
> говорити, балакати, 
> розмовляти
> великий — малий
> БАГАТОЗНАЧНІ 
> СЛОВА
> гребінець у півня — 
> гребінець у хлопчика — 
> гребінець хвилі
> СЛОВА ІЗ ПРЯМИМ 
> І ПЕРЕНОСНИМ 
> ЗНАЧЕННЯМ
> золота сережка —
> золота осінь

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 98
> **Score:** 0.33
>
> 98
> Прикметники в однині змінюються за родами. 
> Прикметник має такий рід, як іменник, з яким він 
> зв’язаний. Наприклад: зелена трава, зелене дерево, 
> зелений кущ.
> У множині рід прикметника не визначається.
> 2. Прочитай інформацію Ґаджика. Випиши з виділених
> речень сполучення іменників з прикметниками. Познач 
> рід прикметників.
> 2
> Одеса — велике місто. За кількістю жителів 
> воно посідає третє місце в Україні. Морський порт
> в Одесі є найбільшим у нашій державі. 
> Назву місту дала французька мова. У ній є 
> вислів, що означає «достатньо води». Якщо його 
> прочитати у зворотному напрямку, то отримаємо 
> слово «одеса».
>                      ж. р.
> Зразок: чиста вода.
> 4. Прочитай і спиши текст. Підкресли прикметники разом з 
> іменниками, з якими вони зв’язані. 
> Є на Одещині містечко Вилкове.

## Підсумок — Summary

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 18
> **Score:** 0.25
>
> 16
> Й й
> Бачу Й, й (йот). Чую  [й].
> а й в а
>  [ •  =   |  –• ]
> а й с т р и
> * а й в о р о
> а
> о
> и
> і
> Й
> га
> ми
> рі
> Й
> н о к
> лій- 
> 	
> ліній-
> 	
> май- 
> чай- 
> 	
> гай- 
> 	
> чай- 
> мий	
> лий 	
> чай	
> грай
> вимий	
> долий	
> чайник	
> зіграй
> ай
> ой
> ий
> ій
> а
> о
> і
> і
> ч
> й
> д
> м
> й
> Pidruchnyk.com.ua

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 36
> **Score:** 0.33
>
> 36
> Запиши слова з буквою ї. Визнач звуки, які позначає буква ї.
> Мій — мої, твій — твої, вія — вії, лілія — лілії, лінія — лінії.
>  
> Утвори і запиши речення за зразком.
> Зразок. Колюче їжаченя з’їло слимака.
> Колючий
> Колюча
> Колюче
> Колючі
> їжак
> їжачиха
> їжаченя
> їжаки
> їсть
> з’їла
> з’їло
> їдять
> слимака.
> жука.
> равлика.
> черв’яка.
>  
> Редагуємо
> Їжак і жаба допомагають 
> садівнику поїдати комах. 
>  
> Запиши речення на вибір, у якому: 1) пояснюється, чому їжак 
> не робить запаси на зиму; 2) описується поведінка їжачка 
> восени. 
> Восени їжачок носить на своїх голках листя, а не їжу. 
> Їжак не запасає їжу на зиму. Узимку він не їсть, а спить. 
> Тому і готує звірятко тепле гніздо для зимівлі. 
> • Склади речення за питаннями.
> Коли?
> Хто?
> Що?
> Що робить?
> Де?
> скЛаД. наГоЛос.

## Grammar Reference

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 103
> **Score:** 0.50
>
> 101
> Повторюємо разом
> Слова — назви ознак. 
> Слова, протилежні за 
> значенням
>  
> 	 Розглянь малюнки. 
> Який?
> Яка? 
> Яка? 
> Слова, які відповідають на питання 
> який? яка? яке? які?, указують на 
> ознаку предмета.
> 	 Перепиши перше речення тексту (с. 99). Під-
> кресли слова — назви ознак кошеняти. По-
> став до цих слів запитання.
> 	 Прочитай текст.
> Чижик-Пижик сидів на високій гілці й 
> крутив головою. Раптом перед ним про-
> летіла яскрава бабка. Він хотів її схопи-
> ти, але зірвався з гілки. Зірвався, за-
> крутився і полетів!
> Pidruchnyk.com.ua


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
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

### Іменник як частина мови
> **Source:** МійКлас — [Іменник як частина мови](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/imennik-43064/imennik-iak-chastina-movi-41979)

### Теорія:

*www.ua.pistacja.tv*  
 
**Що ж ми називаємо іменником?**
***
***Дмитро Білоус дав таке визначення іменнику:
Іменник\! Він узяв собі на плечі
Велике діло — визначати речі…
Зверни увагу\!
Назву «*іме

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Який? Яка? Яке? (What kind?)` (~300 words)
- `## Прикметники (Common Adjectives)` (~300 words)
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
  1. **At a weekend book fair — browsing books, maps, and posters. Describe items: новий атлас (m), цікава книга (f), старе фото (n), великий плакат (m), маленька листівка (f, postcard). NOT bags or furniture.**
     Speakers: Тарас, Софія
     Why: Який/яка/яке? with книга(f), атлас(m), фото(n), плакат(m), листівка(f)

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

**Required:** який, яка, яке (what kind? — m/f/n), великий (big), маленький (small), новий (new), старий (old), гарний (nice, beautiful), чистий (clean), дорогий (expensive), дешевий (cheap)
**Recommended:** поганий (bad), брудний (dirty), світлий (light, bright), темний (dark), а (and/but — contrast), але (but)

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

- P1 (~35 words): Scene-setting intro. Adjectives describe what nouns ARE LIKE. Two dialogues show this in real life: first, a room at home; second, browsing a book fair. No grammar yet — just exposure.

- Dialogue 1 (~90 words): Room description (Вашуленко Grade 3 p.131 pattern). Тарас asks, Оля answers. 5 exchanges: — Яка твоя кімната? — Велика і світла. — А стіл? — Стіл новий. — А ліжко? — Воно старе. — Вікно? — Вікно чисте і велике. — А стілець? — Маленький, але зручний. Nouns: кімната (f), стіл (m), ліжко (n), вікно (n), стілець (m) — all M08 nouns, now with adjectives attached.

- P2 (~30 words): Bridge note. Same question word — Який? Яка? Яке? — but a new setting: a weekend book fair. Watch how the question word shifts with each noun.

- Dialogue 2 (~100 words): Book fair. Тарас і Софія browse. 6 exchanges: — Який цікавий атлас! — Так, але він дорогий. — А ця книга? Яка вона? — Нова і дешева. — Яке гарне фото! — Справді. А плакат? — Великий і яскравий. — Подивись — маленька листівка. Яка вона? — Стара, але гарна. Items: атлас (m), книга (f), фото (n), плакат (m), листівка (f) — five genders represented deliberately.

- P3 (~30 words): Observation prompt. In Dialogue 2: атлас → який, книга → яка, фото → яке. The question word matched the noun. That pattern is the entire grammar point for this module.

- Exercise (~45 words): **Comprehension check (3 true/false statements)** — "Атлас дешевий. True or false?" / "Книга стара. True or false?" / "Листівка маленька. True or false?" Forces learners to re-read dialogues for adjective meaning before studying the pattern formally.

---

## Який? Яка? Яке? (What kind?) (~330 words total)

- P1 (~60 words): Core rule. In Ukrainian, the question "What kind?" changes its ending to match the noun's gender — just like мій/моя/моє from M08. Masculine noun → Який? (Який стіл? → Великий стіл.) Feminine noun → Яка? (Яка книга? → Нова книга.) Neuter noun → Яке? (Яке вікно? → Чисте вікно.) Three questions, three answers — same gender in each pair.

- P2 (~70 words): Ending pattern laid out clearly. Adjectives change the same way as the question word. Masculine: -ий (великий, новий, чистий, дорогий). Feminine: -а (велика, нова, чиста, дорога). Neuter: -е (велике, нове, чисте, дороге). Source: Пономарова Grade 3 p.98: "Прикметник має такий рід, як іменник, з яким він зв'язаний." The adjective copies the gender of its noun — always.

- P3 (~50 words): Pattern comparison to мій/моя/моє. Learners already know: мій стіл, моя книга, моє вікно. Adjectives follow the exact same rule. If you can say мій стіл, you can say великий стіл. The gender is in the noun — the adjective just agrees.

- Exercise (~45 words): **Fill-in (10 items)** — add correct ending: нов__ книга → нова; велик__ стіл → великий; чист__ вікно → чисте; стар__ атлас → старий; дорог__ листівка → дорога; нов__ фото → нове; маленьк__ плакат → маленький; гарн__ кімната → гарна; дешев__ олівець → дешевий; чист__ небо → чисте.

- P4 (~55 words): Soft-stem preview note. Some adjectives end in -ій/-я/-є (синій, синя, синє). These follow the same gender logic but with a soft stem. They appear in M10 (Colors) — don't worry about them now. For this module: всі прикметники end in hard -ий/-а/-е. One pattern, one module.

- P5 (~50 words): Three mini-sentences modeling full descriptions using M08 nouns + M09 adjectives together: У мене є великий стіл. (m) / Моя кімната маленька, але гарна. (f) / Вікно велике і чисте. (n) — Learners see the adjective placed both before and after the noun. Both positions are correct in Ukrainian.

---

## Прикметники (Common Adjectives) (~330 words total)

- P1 (~45 words): Strategy note. Ukrainian vocabulary is easier to learn in opposites — your brain stores both at once. This module's core adjectives come in six pairs. Each pair, one example sentence shows both words in use together with an M08 noun.

- P2 (~120 words): Six adjective pairs with example sentences for each:
  1. великий ↔ маленький — Стіл великий, а стілець маленький.
  2. новий ↔ старий — Книга нова, але атлас старий.
  3. гарний ↔ поганий — Яка гарна листівка! А цей плакат поганий.
  4. чистий ↔ брудний — Вікно чисте, а підлога брудна.
  5. дорогий ↔ дешевий — Атлас дорогий. Книга дешева.
  6. світлий ↔ темний — Кімната світла і велика.
  Each pair presented as: bold headword (m form) ↔ bold headword (m form), then one sentence showing both in action. Feminine and neuter forms illustrated where the example sentence uses f or n nouns.

- Exercise (~40 words): **Match-up (6 pairs)** — match adjective opposites: великий / маленький / новий / старий / чистий / брудний / дорогий / дешевий / світлий / темний / гарний / поганий. Reinforces both vocabulary and the concept of opposition.

- P3 (~70 words): Building full descriptions — combining M08 nouns with M09 adjectives into connected sentences. Model paragraph about a room: У мене є маленька кімната. Стіл новий, а ліжко старе. Вікно велике і чисте. Стілець — маленький і старий, але зручний. — Point out two connectors: і = and (both true in parallel); а = and/but (contrast between two things). Example: Стіл новий, а стілець старий. vs. Кімната мала і темна.

- Exercise (~55 words): **Fill-in (6 items)** — describe a room using given noun + adjective pair. Learner writes the full sentence with correct agreement: (вікно / чистий) → Вікно чисте. (кімната / світлий) → Кімната світла. (стіл / новий) → Стіл новий. (ліжко / старий) → Ліжко старе. (стілець / маленький) → Стілець маленький. (книга / цікавий) → Книга цікава.

---

## Підсумок — Summary (~330 words total)

- P1 (~50 words): Module recap. Today's core: adjectives in Ukrainian change their ending to match the gender of the noun they describe. Three endings to know now: -ий (m), -а (f), -е (n). The question words Який? Яка? Яке? follow the same pattern. The adjective always agrees with its noun.

- Self-check Q&A (~100 words):
  - What ending does a masculine adjective have? → -ий (великий, новий, чистий)
  - What ending does a feminine adjective have? → -а (велика, нова, чиста)
  - What ending does a neuter adjective have? → -е (велике, нове, чисте)
  - Which question word goes with книга? → Яка? (Яка книга?)
  - Which question word goes with стіл? → Який? (Який стіл?)
  - Which question word goes with вікно? → Яке? (Яке вікно?)
  - What's the difference between і and а? → і = and (parallel); а = and/but (contrast)
  - Name three adjective opposites. → великий/маленький, новий/старий, дорогий/дешевий

- Exercise (~60 words): **Quiz (6 items)** — choose Який / Яка / Яке for each noun: стіл → Який; кімната → Яка; фото → Яке; плакат → Який; книга → Яка; ліжко → Яке. Immediate application of the gender-agreement rule before the module closes.

- P2 (~60 words): What's coming next. Colors in Ukrainian (M10) introduce soft-stem adjectives: синій (m) / синя (f) / синє (n) — the same gender logic, different stem. After M10, describing objects will be fully unlocked: великий синій стіл, нова червона книга, чисте біле вікно. The pattern you learned today carries forward into every module that follows.

- P3 (~60 words): Production prompt. Write 3 sentences describing your real room or your desk using today's adjectives. Try to use: one masculine noun + adjective, one feminine noun + adjective, one neuter noun + adjective. Use і or а to connect at least one pair. No English. Think in Ukrainian: Який мій стіл? → Мій стіл ____. Don't translate — describe directly.

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
