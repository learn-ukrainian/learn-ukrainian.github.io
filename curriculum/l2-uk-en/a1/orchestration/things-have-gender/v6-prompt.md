

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **8: Things Have Gender** (A1, A1.2 [My World]).

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
module: a1-008
level: A1
sequence: 8
slug: things-have-gender
version: '1.1'
title: Things Have Gender
subtitle: він, вона, воно — every noun has a gender
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Determine noun gender using the він/вона/воно test
- Recognize gender by word endings (consonant = m, -а/-я = f, -о/-е = n)
- Name 20+ common objects with correct gender
- Use У мене є with objects (extending from M06 family)
dialogue_situations:
- setting: At a pet shop — looking at animals and their accessories. A кіт (m) sleeps
    in a кошик (m, basket), a рибка (f) swims in an акваріум (m), a черепаха (f, turtle)
    sits near a дзеркало (n, mirror). Use animals and pet items to demonstrate він/вона/воно
    — not room furniture.
  speakers:
  - Марія
  - Оленка
  motivation: Він/вона/воно with кіт(m), рибка(f), кошеня(n), акваріум(m), черепаха(f)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Video call showing your room: — Привіт! Дивись, це моя кімната.
    — Класно! У тебе є стіл? — Так, у мене є стіл і ліжко. Gender emerges naturally
    through мій стіл (m), моя кімната (f), моє ліжко (n).'
  - Dialogue 2 — What's in your bag? — Що у тебе є? — У мене є книга, телефон і фото.
    — А у мене є ручка і зошит.
- section: Він, вона, воно (The Gender Test)
  words: 300
  points:
  - 'Пономарова Grade 3 p.86: Ukrainian nouns have gender. Test: can you replace the
    noun with він, вона, or воно? Чоловічий рід (masculine): стіл — він. Можна додати:
    мій стіл. Жіночий рід (feminine): книга — вона. Можна додати: моя книга. Середній
    рід (neuter): вікно — воно. Можна додати: моє вікно.'
  - 'Вашуленко Grade 3 p.112 — endings by gender: Masculine: usually ends in consonant
    — стіл, телефон, зошит. Feminine: usually ends in -а or -я — книга, лампа, кімната,
    ручка. Neuter: usually ends in -о or -е — вікно, ліжко, крісло, місто. This covers
    ~90% of nouns. Exceptions (like -ь words) come later.'
- section: Предмети навколо (Objects Around Us)
  words: 300
  points:
  - 'Room vocabulary organized by gender: Masculine: стіл (table), стілець (chair),
    телефон (phone), комп''ютер (computer), зошит (notebook), ключ (key). Feminine:
    книга (book), лампа (lamp), сумка (bag), ручка (pen), кімната (room), стіна (wall).
    Neuter: вікно (window), ліжко (bed), крісло (armchair), дзеркало (mirror), фото
    (photo).'
  - 'Extending У мене є from M06 (family) to objects: У мене є стіл. У мене є книга.
    У мене є вікно. Same pattern, new vocabulary.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Gender determination in 3 steps: 1. Say він/вона/воно with the noun — which fits?
    2. Check the ending — consonant? -а/-я? -о/-е? 3. Use the right possessive — мій/моя/моє.
    Self-check: What gender is ''стіл''? What gender is ''книга''? What about ''вікно''?
    Say ''I have a chair'' in Ukrainian.'
vocabulary_hints:
  required:
  - стіл (table, m)
  - книга (book, f)
  - вікно (window, n)
  - кімната (room, f)
  - ліжко (bed, n)
  - стілець (chair, m)
  - лампа (lamp, f)
  - телефон (phone, m)
  - комп'ютер (computer, m)
  - він, вона, воно (he, she, it — gender test words)
  recommended:
  - зошит (notebook, m)
  - ручка (pen, f)
  - сумка (bag, f)
  - крісло (armchair, n)
  - дзеркало (mirror, n)
  - ключ (key, m)
  - фото (photo, n)
  - стіна (wall, f)
activity_hints:
- type: group-sort
  focus: Sort objects into masculine/feminine/neuter
  items: 12
- type: quiz
  focus: він, вона, or воно? Choose for each noun.
  items: 8
- type: fill-in
  focus: мій/моя/моє ___ (match possessive to noun)
  items: 8
- type: quiz
  focus: What gender? Look at the ending.
  items: 6
connects_to:
- a1-009 (What Is It Like?)
prerequisites:
- a1-007 (Checkpoint — First Contact)
grammar:
- 'Noun gender: чоловічий (він, мій), жіночий (вона, моя), середній (воно, моє)'
- 'Gender by ending: consonant=m, -а/-я=f, -о/-е=n'
- У мене є extended to objects (from M06 family)
register: розмовний
references:
- title: Пономарова Grade 3, p.86
  notes: 'Gender test: він/мій, вона/моя, воно/моє.'
- title: Вашуленко Grade 3, p.112
  notes: 'Gender endings table: consonant, -а/-я, -о/-е.'
- title: ULP Season 1, Episode 6 — Gender naturally through family
  url: https://www.ukrainianlessons.com/episode6/
  notes: Gender emerges from possessives already taught.

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

**Batch 1 (12/12 confirmed):**
- ✅ стіл (noun)
- ✅ книга (noun)
- ✅ вікно (noun)
- ✅ кімната (noun)
- ✅ ліжко (noun)
- ✅ стілець (noun)
- ✅ лампа (noun)
- ✅ телефон (noun)
- ✅ комп'ютер (noun)
- ✅ він (pronoun — filed as noun-class in VESUM, normal)
- ✅ вона (pronoun — filed as noun-class in VESUM, normal)
- ✅ воно (pronoun — filed as noun-class in VESUM, normal)

**Batch 2 (11/11 confirmed):**
- ✅ зошит (noun)
- ✅ ручка (noun)
- ✅ сумка (noun)
- ✅ крісло (noun)
- ✅ дзеркало (noun)
- ✅ ключ (noun)
- ✅ фото (noun, 17 lemma matches — fully inflectable)
- ✅ стіна (noun)
- ✅ мій (adj, 3 matches)
- ✅ моя (adj — correctly resolves to lemma мій)
- ✅ моє (adj — correctly resolves to lemma мій)

**Not found:** none — all 23 words cleared.

---

## Textbook Excerpts

### Section: Він, вона, воно (The Gender Test)
> «Іменники, які можна замінити словом він, належать до чоловічого роду. До них можна додати слово мій. Наприклад: плащ (він, мій). Іменники, які можна замінити словом вона, належать до жіночого роду. До них можна додати слово моя. Наприклад: куртка (вона, моя). Іменники, які можна замінити словом воно, належать до середнього роду. До них можна додати слово моє. Наприклад: пальто (воно, моє).»
> Source: Ponomarova, Grade 3, p. 86 ← **direct match to plan pedagogy**

> «Іменники, до яких можна додати слова мій, він, — чоловічого роду: тато, батько, ранок, січень. Іменники, до яких можна додати слова моя, вона, — жіночого роду: мати, бабуся, річка, зима. Іменники, до яких можна додати слова моє, воно — середнього роду: маля, серце, життя, літо.»
> Source: Vashulenko, Grade 3, p. 110 (Lesson 34: «Рід іменників: чоловічий, жіночий, середній») ← **direct match to plan pedagogy**

### Section: Предмети навколо (Objects Around Us) — Endings by gender
> «Чоловічий рід: можна додати слова мій, він, закінчення -о або нульове. Жіночий рід: можна додати слова моя, вона, закінчення -а, -я або нульове. Середній рід: можна додати слова моє, воно, закінчення -о, -е, -а, -я.»
> Source: Vashulenko, Grade 3, p. 112 ← confirms the endings rule in the plan

> «Склади усну розповідь на тему "Моя кімната", використовуючи іменники з довідки. Кімната, двері, вікно, стеля, стіни, коридор, шафа, стіл, стілець, тумбочка, ліжко, підлога.»
> Source: Vashulenko, Grade 3, p. 131 ← **direct confirmation**: стіл, стілець, вікно, ліжко are standard Grade 3 room vocabulary, used in the exact activity type planned.

### Section: Діалоги (Dialogues)
> «Перед мандрівниками була велика вітальня... Біля каміна стояв невеличкий столик і два крісла.»
> Source: Zabolotnyi, Grade 6, p. 244 — room description with крісло, стіни, вікна in context.

> Room dialogue format with short exchanges confirmed in Kravcova Grade 2, p. 111: «— Привіт, Кирилку! — Привіт, Соломійко!» with terse reply structure matching the plan's proposed dialogues.

### Section: Підсумок — possessive agreement мій/моя/моє
> «дерев'яний стіл / дерев'яна шафа / дерев'яне ліжко» and «синій диван / синя скатертина / синє крісло»
> Source: Vashulenko, Grade 3, p. 130 ← exact three-gender adjective/possessive agreement demonstrated with room furniture, including plan vocabulary стіл, ліжко, крісло.

---

## Grammar Rules

The Правопис 2019 does **not** cover noun gender or noun endings — these are morphology/grammar topics, not orthography. No Правопис section applies. This is correct and expected.

**Authoritative source for the module's grammar:**
- Noun gender (3 types): Ponomarova Grade 3 p. 86; Vashulenko Grade 3 pp. 110–112
- Possessive pronoun agreement мій/моя/моє: Vashulenko Grade 3 p. 130; Zabolotnyi Grade 6 p. 207 (full declension table)
- Standard school rule (confirmed across Grade 3 and Grade 6 Tier 1 and Tier 2 sources): *Рід іменника визначаємо, підставляючи він/вона/воно або мій/моя/моє.*

---

## Calque Warnings

- **«у мене є»**: ✅ OK — natural Ukrainian possessive construction. Антоненко-Давидович (ad-156) explicitly confirms «у мене є» / «є у мене» as the correct Ukrainian form. The calque to avoid is «матися» (from Russian «иметься»), which does not appear in the plan.
- **«класно»**: ✅ OK — no calque flagged by Антоненко-Давидович. Colloquial but authentic Ukrainian usage in dialogue.
- **«дивись»**: ✅ OK — imperative of «дивитися», natural Ukrainian attention-getter in dialogue. No calque warning. (The style guide entry on «не дивлячись» concerns the participle misuse, not the imperative.)

---

## CEFR Check

| Word | PULS Level | Status |
|---|---|---|
| стіл | A1 | ✅ On target |
| стілець | A1 | ✅ On target |
| вікно | A1 | ✅ On target |
| кімната | A1 | ✅ On target |
| телефон | A1 | ✅ On target |
| комп'ютер | A1 | ✅ On target |
| зошит | A1 | ✅ On target |
| фото | A1 | ✅ On target |
| книга | **A2** | ⚠️ Above target — PULS rates **книжка** as A1. Prefer **книжка** in module text; книга acceptable as passive exposure. |
| ключ | **A2** | ⚠️ Slightly above target — usable as enrichment word but flag for writer; not core A1 |
| дзеркало | **A2** | ⚠️ Slightly above target — usable as enrichment word; not core A1 |

**Writer guidance on flagged words:**
- **книга → книжка**: Swap to **книжка** (A1) throughout. Both words exist and mean "book"; книжка is the A1-level everyday form. книга = A2 (more formal/literary). The dialogues should use книжка.
- **ключ, дзеркало**: Keep in vocabulary lists as labeled enrichment (marked with ★ or "bonus word"), not as core tested vocabulary. Do not test these in fill-in or quiz activities — use only in the vocabulary table for exposure.
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
# Verified Knowledge Packet: Things Have Gender
**Module:** things-have-gender | **Phase:** A1.2 [My World]
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

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 85
> **Score:** 0.25
>
> 8. Так, навіть, подарував (подарувала), я, квіти, 
> акторці.
> 9. Варто, виставу, подивитися, мені, і?
> 10. Цю, обов'язково, виставу, подивитися, варто.
> 11. За, дякую, пораду.
> 16 Прочитайте вітальну листівку. Складіть і запишіть 
> вітання своїм друзям до Нового року за цим зразком. 
> Використовуйте слова — назви дій (дієслова).
> • Озвучте свої вітання для класу.
> Любий друже! / Люба подружко!
> Вітаю тебе з Новим роком! Бажаю 
> чудово провести зимові канікули: 
> відвідати театр, прочитати цікаву 
> книжку, зустрітися і поспілкуватися 
> зі своїми друзями.
> Веселих свят!
> Хвилинка спілкування
> — Я так чекаю початку зимових 
> канікул! Ми поїдемо в Карпати.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 62
> **Score:** 0.50
>
> НАВЧАЮСЯ ЗМІНЮВАТИ СЛОВА — 
> НАЗВИ ПРЕДМЕТІВ
> Я — учителька
> Прочитай і розкажи 
> у класі.
> один — багато^
> Я — учитель
> В українській мові слова можуть називати один 
> предмет або багато предметів.
> тварина 
> рослина
> Додай свої 
> слова.
> 32| Випишіть із лічилки Тамари Коломієць слова — назви 
> предметів.
> один
> багато
> £ Що не так на 
> малюнку?
> Біжить півень із причілка 
> і наспівує лічилку:
> — Раз-два — курчата.
> Три-чотири — зайчата. 
> П'ять-шість — гусаки.
> Сім-вісім — їжаки. 
> Дев'ять-десять — йде лисиця. 
> Нам ховатись, їй жмуриться.
> г
> Причілок — бічна стіна будинку.
> І
> І
> І
> 62

## Він, вона, воно (The Gender Test)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 112
> **Score:** 0.33
>
> 112
> Спостерігаю за закінченнями 
> іменників різних родів
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Чоловічий рід
> можна додати  
> слова мій, він,  
> закінчення -о  
> або нульове
>  тато, Петро
>  вечір, Артем
> Жіночий рід
> можна додати  
> слова моя, вона,  
> закінчення -а, -я 
> або нульове
>  мама, Оксана
>  земля, Юлія
>  тінь, заметіль
> Середній рід
> можна додати  
> слова моє, воно,  
> закінчення  
> -о, -е, -а, -я
>  літо
>  сонце
>  курча
>  маля
> 6   Прочитай. Наведи власні приклади іменників. 
> учень
> школяр
> українець 
> учениця
> школярка
> українка
> дівча
> хлоп’я
> дитя
> 	 	
>   Запиши ці слова, познач закінчення іменників.
> 	 	
>   Зроби висновок, до якого роду належать імен­ники кожної групи.
> 	 	
> 7   Відгадайте загадки. Визначте рід відгаданих іменників. Назвіть 
> закінчення.
> 1.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 110
> **Score:** 0.50
>
> 110
> Навчаюся визначати рід іменників
> 34
> Рід іменників:  
> чоловічий, жіночий, середній
> 	 	
> 1   Визначте, істоту якого роду називає 
> кожний іменник.
> 	 	
> 3   Допишіть пари слів за зразком.
> 2   Прочитай, уставляючи замість крапок слова мій, моя, моє, він, 
> вона, воно. Визнач рід іменників і поясни свою відповідь. Запиши 
> утворені речення.
> мати — тато
> дочка — син
> малюк — маля
> Іменники бувають чоловічого, 
> жіночого і середнього роду. 
> Досліди, як визнача-
> ють рід іменників.
> Я — дослідник
> Я — дослідниця
> Іменники, до яких можна додати слова мій, він, — 
> чоловічого роду: тато, батько, ранок, січень.
> Іменники, до яких можна додати слова моя, вона, — 
> жіночого роду: мати, бабуся, річка, зима.

## Предмети навколо (Objects Around Us)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 86
> **Score:** 0.33
>
> 86
> зв’язок сЛІв У реченнІ
> Відгадай загадки. Назви слова, які «допомогли» їх відгадати. 
> Склади речення зі словами-відгадками.  
> Я в клітинку і в лінійку, 
> Паперовий і тонкий,
> Не влаштовую я бійку:
> Цифри, букви і малюнки
> Написати ти зумій. 
> У портфелі є хатинка — 
> ручки там живуть, 
> резинка, клей, 
> лінійка, кутники — 
> школярів помічники.
>  
> Установи зв’язок між словами в реченні. 
> У портфелі лежав новий 
> зошит.
> Бабуся подарувала Олі 
> пенал.
> (Що?) … (що робив?) … .
> (Хто?) … (що зробила?) … .
> Зошит (який?) … . 
> Подарувала (кому?) … .
> Лежить (де?) … .
> Подарувала (що?) … .
>  
> Установи зв’язок між словами в реченні.
> У портфелі лежав дерев’я-
> ний пенал.
> Учителька розповідала казку 
> учням.
> (Що?) … (що робив?) … .
> (Хто?) … (що робила?) … .
> … (який?) … .

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 64
> **Score:** 0.25
>
> 64
> Знайди слово — підпис до малюнка.
> 	
> терен	
> трава	
> талант	
> Тарас
> 	 теремок	
> тропа	
> танок	
> Тетяна
> 	
> терези	
> труба	
> тарілка	
> Тимофій
> 
> Вірш. Тема вірша. Головна думка
> Лиш телефон задзеленчить,
> Іванко в слухавку кричить:
> — Алло! Привіт! Іван на дроті!
> Що? Татусеві по роботі?..
> Так, знаю я, що мамі й тату
> Теж можуть телефонувати.
> Чого я вам сказав «привіт»?
> Напевно, так робить не слід...
> Дорослим незнайомцям діти
> Так не повинні говорити.
> Заждіть хвилиночку лишень...
> Пробачте, прошу... Добрий день!
> 	
> Богдана Бойко
> Як ти розумієш прислів’я?
> Слово чемне кожному приємне.
> 1
> 2
> Т т
> т е|л е|фон

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 32
> **Score:** 0.33
>
> 32
> И и
> к н и|г и
> Знайди слова — підписи до малюнка.  
> Відшукай слово до схеми. 
> 	
> риби	
> пити	
> липи	
> книжка
> 	 гриби	
> лити	
> липень	
> книжечка
> 	грибний	
> мити	
> у липні	
> книжки
> 
> Передбачення
> Розкажи, про що можна 
> дізнатися, розглянувши 
> обкладинку книжки. 
> 
> Текст. Заголовок. Приказка 
> Де ти зберігаєш книги? На полиці, у  шафі, 
> на робочому столі. А якщо книг багато? Тоді їх 
> зберігають у  бі-блі-о-те-ці. Ти можеш прийти 
> в  бі-блі-о-те-ку і почитати книги. А можеш 
> узяти їх додому, а потім повернути. Ще є елек-
> тронні книги. Їх можна знайти в Ін-тер-не-ті.
> Книги читай — розуму набирай.
> 1
> 2
> 3
> автор
> назва
> малюнок

## Підсумок — Summary

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 86
> **Score:** 0.33
>
> 86
> 4. Дізнайся з тексту, чи правильно ви відповіли на останнє 
> запитання Родзинки.
> Іменники, які можна замінити словом він, належать 
> до чоловічого роду. До них можна додати слово мій.
> Наприклад: плащ (він, мій).  
> Іменники, які можна замінити словом вона, належать 
> до жіночого роду. До них можна додати слово моя.
> Наприклад: куртка (вона, моя).
> Іменники, які можна замінити словом воно, належать 
> до середнього роду. До них можна додати слово моє. 
> Наприклад: пальто (воно, моє).
> 2. Допоможи Ґаджикові визначити рід поданих іменників. 
> Запиши їх у відповідні колонки.
> 2
> Книжка, ліс, море, скромність, сором, батько,
> добро, дочкà, курча, шафа, стіл, дзеркало.
> ЧОЛОВІЧИЙ РІД      ЖІНОЧИЙ РІД       СЕРЕДНІЙ РІД
>         (він, мій)                   (вона, моя)               (воно, моє)
> 3.

> **Source:** kravtsova, Grade 3
> **Section:** Сторінка 64
> **Score:** 0.50
>
> 64
> 180.	 1. Прочитай початок казки.
> У країні Мови жив король Іменник. Інколи він полюбляв 
> поділяти слова на групи. Тоді він вигукував:   
> — Він мій! Вона моя! Воно моє!
> Крок 1. Назвиѳ предмети, зображені на малюнку.
> 2.	 Виконай завдання на вибір.
> 	 Випиши іменники в однині, познач закінчення. 
> 	 Випиши наз

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Він, вона, воно (The Gender Test)` (~300 words)
- `## Предмети навколо (Objects Around Us)` (~300 words)
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
  1. **At a pet shop — looking at animals and their accessories. A кіт (m) sleeps in a кошик (m, basket), a рибка (f) swims in an акваріум (m), a черепаха (f, turtle) sits near a дзеркало (n, mirror). Use animals and pet items to demonstrate він/вона/воно — not room furniture.**
     Speakers: Марія, Оленка
     Why: Він/вона/воно with кіт(m), рибка(f), кошеня(n), акваріум(m), черепаха(f)

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

**Required:** стіл (table, m), книга (book, f), вікно (window, n), кімната (room, f), ліжко (bed, n), стілець (chair, m), лампа (lamp, f), телефон (phone, m), комп'ютер (computer, m), він, вона, воно (he, she, it — gender test words)
**Recommended:** зошит (notebook, m), ручка (pen, f), сумка (bag, f), крісло (armchair, n), дзеркало (mirror, n), ключ (key, m), фото (photo, n), стіна (wall, f)

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
## Діалоги (Dialogues) (~310 words)

- P1 (~30 words): Frame — every Ukrainian noun belongs to one of three gender families: він (masculine), вона (feminine), воно (neuter). Before learning the rules, meet gender in action.
- Dialogue 1 (~110 words): Video call between Марія and Оленка, 7 turns. Марія shows her room: — Привіт! Дивись, це моя кімната. — Класно! У тебе є стіл? — Так, є. Це мій стіл, а ось моє ліжко. — А що ще є? — Є лампа — моя лампа, і ще є крісло. Моє крісло дуже зручне! Gender surfaces in possessives мій стіл (m), моя кімната/лампа (f), моє ліжко/крісло (n) — no explanation, just exposure.
- P2 (~25 words): Observation bridge — "Did you notice? стіл gets мій, кімната gets моя, ліжко gets моє. Every noun belongs to a gender family. That family decides which word goes with it."
- Dialogue 2 (~110 words): Classroom, 6 turns. Оленка and Марія compare bag contents: — Що у тебе в сумці? — У мене є книга, телефон і фото. — А у мене є ручка і зошит. — Книга — це цікаво! Яка книга? — Це моя книга. Вона українська! — А мій зошит новий. Uses книга (f), телефон (m), фото (n), ручка (f), зошит (m) — mixed genders across both nouns and possessive echoes вона/він.
- P3 (~35 words): Wrap-up — these nouns fall into три групи, three families. One family goes with він and мій. One with вона and моя. One with воно and моє. Ukrainian grammar calls this рід — gender.

---

## Він, вона, воно (The Gender Test) (~340 words)

- P1 (~55 words): Introduce the three genders formally (Вашуленко Grade 3 p.110, Ponomarova Grade 3 p.86). Чоловічий рід (masculine) — use він and мій. Жіночий рід (feminine) — use вона and моя. Середній рід (neuter) — use воно and моє. Every Ukrainian noun belongs to exactly one of these three families — permanently.
- P2 (~85 words): The test step-by-step. Take стіл. Ask: він стіл? ✓ — feels right. вона стіл? ✗ — sounds wrong. воно стіл? ✗ — also wrong. Result: стіл is чоловічий. Try книга: вона книга? ✓ — жіночий. Try вікно: воно вікно? ✓ — середній. Reinforce with мій/моя/моє: мій стіл (m) → моя книга (f) → моє вікно (n). The он/вона/воно test and the possessive test always agree.
- P3 (~55 words): Real-world context — in M06 you used У мене є with family members. Same structure works for objects. У мене є стіл. У мене є книга. У мене є вікно. Now you know each of those nouns carries a gender, which matters the moment you say мій, моя, or моє.

- **Exercise (Quiz — 8 items):** він, вона, or воно? Learner assigns gender to: телефон / лампа / ліжко / зошит / сумка / крісло / ключ / фото. Items span all three genders and cover required + recommended vocabulary.

- P4 (~55 words): Transition to endings — "Do you have to test every noun from scratch forever? No. Look at the ending. Ukrainian endings carry the gender with them — a built-in shortcut. This covers about 90% of all nouns you'll meet at A1."
- P5 (~90 words): Endings rule (Вашуленко Grade 3 p.112). Masculine — ends in a consonant: стіл (-л), телефон (-н), зошит (-т), ключ (-ч). Feminine — ends in -а or -я: книга, лампа, кімната, ручка, сумка. Neuter — ends in -о or -е: вікно (-о), ліжко (-о), крісло (-о), дзеркало (-о). Tip: when you learn a new noun, notice the ending first — it announces the gender.

---

## Предмети навколо (Objects Around Us) (~340 words)

- P1 (~45 words): Setup — your room, bag, and desk are full of Ukrainian nouns waiting to be named. Here are 20 common objects organized by gender. For each one, check the ending, then confirm with він/вона/воно — both tests point to the same family.
- P2 (~85 words): Masculine objects (він, мій) — стіл, стілець, телефон, комп'ютер, зошит, ключ. Short illustrative sentences to make each word stick: Це мій стіл. Він дерев'яний. Де мій телефон? — Він тут, на столі. Де ключ? — Ось він, мій ключ. Every noun ends in a consonant — the ending signals чоловічий рід before learners even say the word.
- P3 (~85 words): Feminine objects (вона, моя) — книга, лампа, сумка, ручка, кімната, стіна. Sentences: Це моя книга. Вона цікава. Моя сумка — синя. Де ручка? — Ось вона, моя ручка. Це кімната — моя кімната. Every noun ends in -а — the pattern is visible in every example. Learners see the rule confirmed, not stated.
- P4 (~75 words): Neuter objects (воно, моє) — вікно, ліжко, крісло, дзеркало, фото. Sentences: Це моє вікно. Воно велике. Де моє ліжко? — Ось воно. У мене є дзеркало і фото. All end in -о (фото is indeclinable but follows neuter agreement). Briefly flag: фото never changes its ending — it's a borrowed word — but voно and моє still apply.

- **Exercise (Group-sort — 12 items):** Sort into три колонки: він, мій | вона, моя | воно, моє. Items: стілець, ручка, фото, комп'ютер, лампа, крісло, ключ, кімната, дзеркало, телефон, книга, вікно. Equal 4 items per column.

- P5 (~50 words): У мене є bridge from M06 (family vocabulary). Same construction, new objects: У мене є стіл. У мене є книга. У мене є вікно. Now add a possessive: Це мій стіл. Це моя книга. Це моє вікно. Two sentences, same noun — links the structures already known.

- **Exercise (Fill-in — 8 items):** мій, моя, or моє? _____ стіл / _____ книга / _____ вікно / _____ сумка / _____ крісло / _____ ключ / _____ лампа / _____ ліжко. Learner applies the rule, not just recognizes it.

---

## Підсумок — Summary (~330 words)

- P1 (~70 words): Three-step gender check (following plan's point exactly). Step 1 — Try він/вона/воно with the noun: which fits? Step 2 — Check the ending: consonant → чоловічий, -а/-я → жіночий, -о/-е → середній. Step 3 — Use the matching possessive: мій / моя / моє. Both methods give the same answer. Use whichever is faster for you. With practice, gender recognition becomes automatic.
- P2 (~90 words): Self-check Q&A list (plan's point: "Self-check questions"):
  - Якого роду слово «стіл»? → Чоловічого. Він закінчується на приголосний (-л). → Мій стіл.
  - Якого роду «книга»? → Жіночого. Закінчення -а. → Моя книга.
  - А «вікно»? → Середнього. Закінчення -о. → Моє вікно.
  - Скажіть: "I have a chair." → У мене є стілець.
  - Скажіть: "This is my mirror." → Це моє дзеркало.

- **Exercise (Quiz — 6 items):** What gender? Look at the ending only, no testing needed. Nouns: зошит (consonant -т → m), ручка (-а → f), крісло (-о → n), ліжко (-о → n), ключ (consonant -ч → m), стіна (-а → f). Learner states gender + ending evidence.

- P3 (~80 words): Looking ahead to M09 — "In the next module you'll meet adjectives: великий, маленький, синій. Every adjective must agree with its noun's gender — великий стіл (m), велика книга (f), велике вікно (n). The gender system you learned today is the foundation. Every adjective, every possessive, every demonstrative pronoun in Ukrainian depends on gender — and you now have all three."
- P4 (~90 words): Vocabulary recap — all 20 words with gender label in a clean two-column format: стіл (він, м) | книга (вона, ж) | вікно (воно, с) | стілець (він, м) | лампа (вона, ж) | ліжко (воно, с) | телефон (він, м) | ручка (вона, ж) | крісло (воно, с) | зошит (він, м) | сумка (вона, ж) | дзеркало (воно, с) | ключ (він, м) | кімната (вона, ж) | фото (воно, с) | комп'ютер (він, м) | стіна (вона, ж).

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
