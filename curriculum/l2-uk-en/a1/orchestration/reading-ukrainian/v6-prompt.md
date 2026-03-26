# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **2: Reading Ukrainian** (A1, A1.1 [Sounds, Letters, and First Contact]).

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

## 8 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.1'
title: Reading Ukrainian
subtitle: From letters to words to sentences
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Read any Ukrainian word by sounding out letters and blending syllables
- Apply the syllable rule — count vowels to count syllables
- Read multisyllable words confidently (not letter by letter)
- Understand how the 10 vowel letters map to 6 vowel sounds
content_outline:
- section: Склади (Syllables)
  words: 250
  points:
  - 'Большакова Grade 1 p.25: ''У слові стільки складів, скільки голосних звуків.''
    Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels
    = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).'
  - 'How to read a new word: 1. Find the vowels (they''re the syllable cores) 2. Split
    at syllable boundaries (consonants prefer starting new syllables) 3. Sound out
    each syllable 4. Blend into the full word at natural speed Practice: а-пте-ка,
    у-ні-вер-си-тет, шо-ко-лад. Note: Ukrainian phonetic syllable division (складоподіл)
    follows the open-syllable principle — consonants prefer starting new syllables.'
  - 'Following Большакова p.29 звуковий аналіз method: identify vowels, divide into
    syllables, then read. This is how Ukrainian children learn.'
- section: Голосні літери (Vowel Letters)
  words: 300
  points:
  - 'Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple
    vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes
    ONE consistent sound — no surprises.'
  - 'Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or
    after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never
    softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.'
  - 'Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім
    (house). Listen to Anna''s pronunciation videos for each — the difference is subtle
    but changes meaning.'
- section: Читання слів (Reading Words)
  words: 300
  points:
  - 'Apply M01 letter knowledge to read real words fluently. Strategy: don''t read
    letter-by-letter. Read syllable-by-syllable. Start with the vowels (find them
    first), then build outward. Example: книга — find vowels И, А → кни-га → read.'
  - 'Common word patterns for reading practice: CVCV: мама, тато, каша, вода, рука,
    хата, коза, нога CVCCV: школа, книга, банда, парта CVC: дім, сон, ліс, дуб, хліб,
    банк The more patterns you see, the faster you read.'
  - 'Special letter combinations to watch for: Щ is always [шч] — що, ще, щастя. Ь
    has no sound — it softens: день, сіль, кінь. '' (apostrophe) separates: сім''я,
    м''ясо, п''ять. These will be explored fully in M03.'
- section: Читаємо разом (Reading Together)
  words: 200
  points:
  - 'Progressive reading practice — start simple, build up: Level 1 (2 syllables):
    мама, тато, вода, рука, хата, каша Level 2 (3 syllables): аптека, молоко, людина,
    вулиця Level 3 (4+ syllables): університет, бібліотека, фотографія'
  - 'Reading a simple text (all Це + noun, no verbs): Це Київ. Це столиця. Тут аптека
    і банк. Там школа. Що це? Це кафе. А це пошта.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel
    sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe
    do? Read this word: бібліотека — how many syllables?'
vocabulary_hints:
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
activity_hints:
- type: fill-in
  focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
- type: quiz
  focus: How many syllables? Count the vowels.
  items: 8
- type: match-up
  focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
- type: quiz
  focus: Read the word and choose its meaning
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- 'Syllable rule: count vowels = count syllables (складоподіл)'
- 10 vowel letters → 6 vowel sounds mapping
- Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])
- 'Reading fluency: syllable-by-syllable word reading'
- Ь, apostrophe, voiced/voiceless (preview — detailed in M03)
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.25
  notes: 'Syllable rule: ''У слові стільки складів, скільки голосних звуків.'''
- title: Большакова Grade 1 буквар, p.29
  notes: Звуковий аналіз слова method — how to analyze word sounds.
- title: Захарійчук Grade 1 (NUS 2025), p.13-15
  notes: 'Sound notation: [•] for vowels, [–] for consonants, [=] for soft.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Reading Ukrainian
**Module:** reading-ukrainian | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Склади (Syllables)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 25
> СКЛАД  
> У слові стільки складів, скільки голосних звуків.
> 1. Визначаю в слові 
> голосні звуки.
> ЯК ПОДІЛИТИ 
> СЛОВО 
> НА СКЛАДИ
> 2. Ділю слово 
> на склади. 
> М А М А
> М А М А
> Визнач, скільки складів у кожному слові. 
>  
> сон 
> слон 
> оса 
> ананас
>  
> со|сна 
> сало 
> ламана 
> смола
>  
> Розглянь малюнок вище. Правда чи неправда?
>  Кіт стоїть на стільці. 
>  Миша сидить на підлозі.
>  Кіт стоїть поруч зі стільцем.  Миша сидить на стільці.
> 1
>  
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Визначте кількість складів у словах, не поділяючи їх на 
> склади. Доведіть свою думку.
> бібліотека 
> книгосховище 
> грамота 
> наука 
> мудрість
> Я — учителька
> Прочитай і розкажи
> ■ у класі.
> Я — учитель
> мудрість
> ? звуків,
> ? букв,
> ? складів
> У слові стільки складів, скільки в ньому голосних 
> звуків.
> 5| Запишіть приказку, яка «заховалася».
> Перед вами складовиця, 
> а в ній приказка таїться. 
> Доберіть усе до ладу, 
> згрупувавши склад до складу.
> складовиця 
> ? звуків, ? букв, 
> ? складів
> б| Випиши з тексту виділені

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 29
> ЗВУКОВИЙ СКЛАД СЛОВА
> ЯК ЗРОБИТИ 
> ЗВУКОВИЙ АНАЛІЗ СЛОВА
> 1. Визначаю в слові 
> голосні звуки.
> М А М А
> М А М А
> 4. Позначаю 
> приголосні звуки. 
> М А М А
> 2. Ділю слово 
> на склади. 
> М А М А
> 3. Ставлю наголос. 
> Знайди слово — підпис до малюнка.
> Зроби звуковий аналіз слів.
>  
> ко|са 
> колос 
> ласка
>  
> каска 
> молоко 
> маска
>  
> Правда чи неправда?
> Прочитай або послухай речення. 
>  Ганна любить молоко.
>  Мама питиме какао.
>  Ганна їсть манну кашу.
>  Собака Лоло їсть ковбасу.
>  Лоло любить солому.
> 1
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> ЗВУКО-БУКВЕНИЙ СКЛАД 
> СЛОВА
> АНАЛІЗУЮ ЗВУКОВИЙ СКЛАД СЛОВА
> звуки.
> Г
> звук
> в
> о
> Мовний звук — елемент людської мови, 
> утворений за допомогою органів мовлення.
> Хвилинка спілкування
> 1
> — В українській мові шість голосних 
> звуків.
> — Я думаю, що їх десять.
> — Ні. Запам'ятай шість голосних 
> звуків:
> [а], [о], [у], [е], [и], [і].
> — Добре. Запам’ятаю!
> 4

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> . . . . . . . . . . . . . . . . . . . . 26
> К к . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
> Наголос . . . . . . . . . . . . . . . . . . . . . . 28
> Звуковий склад слова . . . . . . . . . 29
> И и . . . . . . . . . . . . . . . . . . . . . . . . . . 30
> И и . . . . . . . . . . . . . . . . . . . . . . . . . . 31
> Р р  . . . . . . . . . . . . . . . . . . . . . . . . . . 32
> Р р  . . . . . . . . . . . . . . . . . . . . . . . . . . 33
> Б б . . . . . . . . . . . . . . . . . . . . . . . . . . 34
> Б

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 14
> Склад може складатися з одного голосного звука.
> 44.	
> 1.	 Назвіть звуки в словах оса, жук. Скільки звуків у 
> кожному слові? 
> 2.	 Дослідіть, чи однакова кількість складів у цих словах. Чому?
> 47.	
> 1.	 Прочитай. Визнач, де слово, а де — склад.
> 2.	 Спиши слова, позначаючи склади дужками.
> Зразок. Учень.
> 45.	
> Додай склад так, щоб утворилося нове слово. Запиши.
> ..лото,  мете.., ..гілля, ..жити, ..рис.
> Склади для довідки: зо, ву, дру, і, лик.
> у
> к
> в
> е
> р
> е
> с
> е
> н
> ь
> р
> о
> о
> ж
> о
> в
> т
> е
> н
> ь
> т
> ь
> б
> я
> в
> а
> з
> л
> и
> с

## Голосні літери (Vowel Letters)

> **Source:** unknown, Grade 1
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
> я

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 35
> Вимов слова. Запиши їх у два стовпчики. Познач звуки [а], 
> [у], [е] знаком , звуки [йа], [йу], [йе] — знаками 
> .
> Яблуко, маля, буряк, м’ята, юшка, люблю, в’юн, калюжа, 
> єнот, синє, в’є, давнє.
> Один звук: [а], [у], [е]
> Два звуки: [йа], [йу], [йе]
> Маля, …
> Яблуко, …
>  
> Спиши. У яких словах букви я, ю, є позначають два звуки? 
> Склади речення з парами слів на вибір.
> Буряк — бур’ян, ягоди — малята, юнак — тюлень, 
> зозуля — яблуко, лілія — мушля, єнот — літнє, співає — 
> вечірнє.
> БУква ї
> Буква ї завжд

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 81
> 	 Хто є головною героїнею тексту? Який пода-
> рунок отримала Катруся? Що вона показува-
> ла ляльці? Що росло на городі?
> Повторюємо разом
>  Буква я. Звукове  
> значення букви я
> 	 Випиши з тексту слова, виділені блакитним 
> кольором. Зроби звукові схеми. Які звуки по-
> значає буква я в цих словах?
> 	 Перепиши підкреслене речення. Зроби зву-
> кову схему слова з буквою  я. 
> 	 Прочитай тексти.
> Навесні в лісі все оживає. Вироста-
> ють травинки. Розпускаються листочки. 
> Розкриваються квіти. Чиста вода напов­

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 10
> 29.	
> Поміркуй, що спільного у звуковому складі кожного слова:
> а) кількість складів;	 	
> б) звук [й].
> яблуко
> єнот
> юрта
> їжак
> 30.
> Дослідиѳ, скільки звуків позначають букви я, ю, є, ї на 
> початку складу.
> Крок 1. Який перший звук ти чуєш у назвах букв я, ю, є, ї?
> Крок 2. Скільки звуків позначають букви я, ю, є, ї на початку складу?
> Букви я, ю, є на початку складу позначають два звуки:
> [йа], [йу], [йе]. Буква ї завжди позначає два звуки — [йі].
> 31.
> 1.	 Прочитай слова, уставляючи пропущені букви. Які

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> УКРАЇНСЬКА МОВА
> БУКВАР 
> ЧАСТИНА 1
> 1 
> КЛАС
> ї
> І. О. БОЛЬШАКОВА
> М. С. ПРИСТІНСЬКА
> о
> о
> м
> н р
> л
> е
> е
> е
> е
> А
> И
> Л
> М
> Є
> О
> І
> Ю
> У
> Е
> Я
> ам
> ам
> ам
> ум
> ум
> ум
> ом
> ом
> ом
> кит
> ліс
> лис
> кіт
> дим
> сік
> дім
> рік
> о
> п
> к
> в
> т
> н
> л

> **Source:** unknown, Grade 2
> **Score:** 0.25
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

## Читання слів (Reading Words)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 26
> Знайди слова — підписи до малюнка.  
> Відшукай слово до схеми. 
> 	
> кіт	
> кобза	
> краб	
> книга
> 	 котик	
> кобзар	
> кран	
> книгарня
> 	 кицька	
> козак	
> кропива	
> книжковий
> 
> Речення і малюнок.
>  Кіра читає книгу про тварин.
>  Карина читає казки.
>  Максим читає о-по-ві-дан-ня про дітей.
>  Кирило читає ен-ци-кло-пе-ді-ю про техніку.
> 1
> 2
> К к
> к н иж|к а
> Кіра
> Карина
> Кирило
> Максим

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Утвори і прочитай слова. Назви одним словом.
> маам
> отат
> дусьід
> басябу
> барт
> састер
> • Поміркуй, якими іншими словами ми називаємо сім’ю. 
> Склади тематичну павутинку (на аркуші паперу).
> Послухай пісню Наталії Май «Родина».
> *—• • Що ти відчував (відчувала), коли звучала пісня?
> • За що дитина дякує батькам?
> ~ Прочитай вірш.
> ДИВО-ТАТУСЬ
> Леся Вознюк
> Як весняне сонечк

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Склади (Syllables)` (~250 words)
- `## Голосні літери (Vowel Letters)` (~300 words)
- `## Читання слів (Reading Words)` (~300 words)
- `## Читаємо разом (Reading Together)` (~200 words)
- `## Підсумок — Summary` (~150 words)
- `## Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
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
- Dialogues: natural, not stilted. Real situations, real responses. **Use the knowledge packet** — it contains textbook excerpts with real Ukrainian dialogues and situations. Adapt them, don't invent artificial conversations. A dialogue about немає should show someone SEARCHING for something and not finding it (keys, notebook, phone), not an interrogation. A dialogue about the market should sound like a real market conversation. If the knowledge packet has a textbook dialogue on the topic, use that pattern.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M03):
NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.

ALLOWED structures (Ukrainian examples only):
- Це + noun: «Це кіт», «Це мама»
- Noun + тут/там: «Мама тут», «Кіт там»
- Question words: «Хто це?», «Що це?», «Де мама?»
- Так/Ні: «Так, це кіт», «Ні, це не кіт»
- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт

BANNED: ALL verbs, past/future tense, cases, compound sentences

STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.
The pipeline adds stress marks deterministically after you write.

METALANGUAGE: English prose, Ukrainian examples. Bilingual headings.

### Vocabulary

**Required:** яблуко (apple) — Я at word start = [йа], молоко (milk) — 3 syllables, all simple vowels, людина (person) — Л + Ю combination, вулиця (street) — Ц sound practice, столиця (capital) — Київ — столиця України, каша (porridge) — Ш sound practice, пісня (song) — softening by Я after consonant
**Recommended:** університет (university) — long word practice, бібліотека (library) — 5 syllables, фотографія (photography) — long word with Ф, шоколад (chocolate) — Ш + О + К combination

### Pronunciation Videos



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
## Склади (Syllables) (~275 words total)

- P1 (~90 words): Hook — you already know all 33 letters from M01. Now learn to read ANY Ukrainian word, even ones you've never seen. The secret: Ukrainian spelling is phonetic — each letter makes one sound, every time. No silent letters, no surprises. This means if you can sound out syllables, you can read anything. Introduce the core question: how do you break a word into syllables?

- P2 (~100 words): The syllable rule from Большакова Grade 1 p.25 — «У слові стільки складів, скільки голосних звуків.» Count the vowels, count the syllables. This rule NEVER breaks in Ukrainian. Examples with progressive difficulty: мама (А, А → 2 syllables: ма-ма), молоко (О, О, О → 3 syllables: мо-ло-ко), банк (А → 1 syllable), сон (О → 1 syllable), аптека (А, Е, А → 3 syllables: а-пте-ка). Introduce the open-syllable principle: consonants prefer starting new syllables (мо-ло-ко, not мол-ок-о).

- P3 (~85 words): The звуковий аналіз method from Большакова p.29 — step-by-step process Ukrainian children use: 1) Find the vowels (circle them mentally), 2) Split at syllable boundaries, 3) Sound out each syllable slowly, 4) Blend into the full word at natural speed. Walk through університет: У, І, Е, И, Е → 5 syllables → у-ні-вер-си-тет. Then бібліотека: І, І, О, Е, А → 5 syllables → бі-блі-о-те-ка.

- **Exercise — Fill-in** (from activity_hints #1): Divide 8 words into syllables: молоко, аптека, школа, книга, вулиця, шоколад, людина, фотографія.

## Голосні літери (Vowel Letters) (~330 words total)

- P1 (~80 words): Recap from M01 — Ukrainian has 6 vowel sounds but 10 vowel letters. Now learn each one individually. The simple six (one letter = one sound, always): А [а], О [о], У [у], Е [е], И [и], І [і]. These are completely predictable — А always sounds like [а], never changes. Compare to English where "a" has 5+ sounds. Ukrainian: one letter, one sound.

- P2 (~100 words): The iotated vowels — Я, Ю, Є, Ї. These are "two-in-one" letters with dual behavior. At word start or after a vowel: Я = [й] + [а] (яблуко, моя), Ю = [й] + [у] (юнак, мою), Є = [й] + [е] (єнот, синє). After a consonant: they soften the consonant and give just the vowel: пісня (Н softened + [а]), люблю (Л softened + [у]), синє (Н softened + [е]). Use the textbook формула from Grade 2: «Букви я, ю, є на початку складу позначають два звуки: [йа], [йу], [йе].»

- P3 (~70 words): Ї — the unique Ukrainian letter. ALWAYS two sounds [й] + [і], never softens. Only appears at word start (їжак, їсти), after a vowel (мої, твої), or after apostrophe (з'їсти). Never after a consonant — that's what makes it unique among iotated vowels. This letter doesn't exist in any other Slavic language.

- P4 (~80 words): Critical minimal pairs — И vs І. These two sounds distinguish meaning: кит (whale) vs кіт (cat), дим (smoke) vs дім (house), лис (fox) vs ліс (forest), вил (poured) vs віл (ox). И is a back vowel (tongue back, lips neutral). І is a front vowel (tongue forward, lips spread). The Большакова буквар pairs these deliberately on the same page. Practice hearing and producing the difference — it changes meaning.

- **Exercise — Match-up** (from activity_hints #3): Match 4 iotated vowels to their sound components: Я → [й]+[а], Ю → [й]+[у], Є → [й]+[е], Ї → [й]+[і].

- **Exercise — Quiz** (from activity_hints #2): How many syllables? 8 items — їжак, яблуко, єнот, університет, пісня, мої, столиця, каша. (Count vowels to answer.)

## Читання слів (Reading Words) (~330 words total)

- P1 (~100 words): Strategy shift — stop reading letter-by-letter, start reading syllable-by-syllable. When you see a new word: find the vowels FIRST (they're the anchors), then build syllables around them, then blend. Walk through книга step by step: spot vowels И, А → two syllables → кни-га → read at natural speed. Then столиця: О, И, Я → three syllables → сто-ли-ця. Then вулиця: У, И, Я → three syllables → ву-ли-ця. The vowels are your roadmap through any word.

- P2 (~110 words): Common word patterns — reading practice organized by structure. Two-syllable CVCV (the most common Ukrainian pattern): мама, тато, каша, вода, рука, хата, коза, нога. These flow naturally — open syllables, easy rhythm. Two-syllable CVCCV: школа, книга, парта. The consonant cluster stays in one syllable. One-syllable CVC: дім, сон, ліс, дуб, хліб, банк. Just one vowel, one syllable, quick to read. Three-syllable words: аптека, людина, вулиця, столиця. The more patterns you recognize, the faster you read — your brain starts seeing syllable shapes automatically.

- P3 (~80 words): Special letter combinations to watch for (preview — full treatment in M03). Щ is always [шч]: що, ще, щастя — one letter, two sounds. Ь (soft sign) has no sound of its own — it softens the preceding consonant: день, сіль, кінь. The apostrophe (') separates a consonant from an iotated vowel: сім'я [сім-йа], м'ясо [м-йасо], п'ять [п-йать]. Recognize these when reading — don't let them slow you down.

- **Exercise — Quiz** (from activity_hints #4): Read the word and choose its meaning. 6 items: книга (book), вода (water), хліб (bread), школа (school), аптека (pharmacy), людина (person).

- P4 (~40 words): Encourage speed — re-read the pattern lists above faster each time. First pass: syllable by syllable. Second pass: whole words. Third pass: pairs of words. Ukrainian reading fluency comes from repetition, not memorization.

## Читаємо разом (Reading Together) (~220 words total)

- P1 (~70 words): Progressive reading ladder. Level 1 — two-syllable words (read these quickly now): мама, тато, вода, рука, хата, каша, школа, книга. Level 2 — three-syllable words (find the vowels first): аптека, молоко, людина, вулиця, столиця, аптека. Level 3 — four or more syllables (the real test): університет, бібліотека, фотографія, шоколад. If you can read бібліотека without stopping, you can read anything.

- P2 (~80 words): Your first Ukrainian text — read this aloud, sentence by sentence. All simple structures (Це + noun, no conjugation needed): «Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта. Ось бібліотека. Тут книги.» Every word uses only letters and patterns from M01 and this module. Read it again faster. You just read real Ukrainian sentences.

- P3 (~70 words): Reading tips for self-study. Read aloud — Ukrainian is a phonetic language, hearing yourself helps. Point to each syllable as you read, then graduate to pointing at whole words. Find Ukrainian signs, menus, or labels online — try to sound them out before checking a translation. Every word you decode builds confidence. In M03, you'll learn the special signs (Ь, apostrophe, Ґ) in detail and start reading longer texts.

- **Exercise — Fill-in** (bonus, reinforcement): Read the mini-text and fill in missing words from a word bank: «Це ___. Це ___. Тут ___ і ___.» (Київ, столиця, аптека, банк).

## Підсумок — Summary (~165 words total)

- P1 (~165 words): Recap the four skills mastered in this module. First: the syllable rule — count vowels to count syllables, a rule that never breaks (молоко = 3 vowels = 3 syllables). Second: the 10 vowel letters — 6 simple (А, О, У, Е, И, І) making one sound each, and 4 iotated (Я, Ю, Є, Ї) that can make two sounds or soften consonants. Third: the reading strategy — find vowels first, build syllables, blend into words. Fourth: pattern recognition — the more word shapes you see (CVCV, CVCCV, CVC), the faster you read. Self-check questions: How many syllables in «бібліотека»? (5 — count the vowels: І, І, О, Е, А.) What two sounds does Я make at the start of «яблуко»? ([й] + [а].) What's the difference between «кит» and «кіт»? (whale vs cat — И vs І.) Next in M03: the soft sign, apostrophe, and the uniquely Ukrainian letter Ґ.

Grand total: ~1320 words (275 + 330 + 330 + 220 + 165)
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
