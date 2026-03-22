<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [2. Linguistic accuracy] [critical]
  Location: section "Склади (Syllables)", paragraph 1: "...straight from the букварь"
  Issue: "букварь" is a Russian word. The Ukrainian word is "буквар" (without the soft sign).
  Fix: Change "букварь" to "буквар".
- FIX: [5. Exercise quality] [major]
  Location: `:::fill-in` exercise block, item `яб-лу-___` and `пі-___-я`
  Issue: The exercise contradicts the text. The text teaches the open-syllable principle and explicitly states "split as я-блу-ко" and "split as пі-сня". The exercise uses `яб-лу-___` (violating the open-syllable rule taught) and `пі-___-я` (which is just letter-filling, not syllable division).
  Fix: Change the items to reflect correct syllable boundaries taught in the text. E.g., prompt `я-блу-___` (answer: `ко`) and prompt `пі-___` (answer: `сня`).
- NOTE: [2. Linguistic accuracy] [minor]
  Location: "Додаткові слова з уроку" table at the end of the module.
  Issue: The table includes grammatical fragments and capitalized particles as vocabulary words: "Це", "ЦЯ", "ТЬ", "що", "ще".
  Fix: Remove these grammatical fragments and particles from the vocabulary list. Only include actual lexical items.

- FIX (Linguistic): - "букварь": Russianism. The Ukrainian word is "буквар".
- The vocabulary table under "Додаткові слова з уроку" includes non-words that were capitalized or used as grammatical examples in the text: "Це", "ЦЯ", "ТЬ".
</correction_directive>

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

## 6 Hard Rules

1. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
2. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
3. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
4. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
5. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
6. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format. Base your exercises on the `activity_hints` in the Plan — each hint should become one exercise.

Write REAL content: real questions, real answers, real distractors. Every exercise must be solvable by a learner who read the preceding prose.

### DSL Format

Use these exact formats. Each block starts with `:::type` and ends with `:::`.

**Quiz** (multiple choice):
```
:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
:::
```

**Fill-in** (complete the sentence):
```
:::fill-in
title: "Complete the greeting"
---
- sentence: "Привіт! Як ___?"
  answer: "справи"
- sentence: "Дякую, ___."
  answer: "добре"
:::
```

**Match-up** (connect pairs):
```
:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like [в], not [b]"
- left: "Н"
  right: "sounds like [н], not [h]"
:::
```

**Group-sort** (classify into categories):
```
:::group-sort
title: "Classify letters"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::
```

**True-false**:
```
:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
- statement: "Голосних звуків більше, ніж приголосних."
  answer: false
:::
```

Spread exercises evenly throughout the module. Never cluster them.

### Approved Exercise Patterns

Use these Ukrainian textbook-inspired patterns (Заболотний, Авраменко) instead of generic "quiz" types:

- **Знайди помилку (Find the error):** Give 3 correct sentences and 1 with an error. Learner identifies the mistake. Tests: grammar rules, calques, Russianisms.
- **Обери правильне слово (Choose the right word):** Fill in the blank from 2-3 options (synonyms, paronyms, or confusable words). Tests: vocabulary nuance, register.
- **Утвори пару (Match-up):** Match words to antonyms, translations, or grammatical pairs (e.g., masculine → feminine). Tests: vocabulary, morphology.
- **Розподіли (Group-sort):** Sort items into 2-3 categories (e.g., голосні vs приголосні, hard vs soft consonants). Tests: foundational phonetics, grammar classification.
- **Склади речення (Build a sentence):** Give scrambled words, learner arranges into correct order. Tests: word order, sentence structure.
- **Знайди місце (Find the right place):** Give 4 sentences with blanks and 4 words — each word fits exactly one sentence. Tests: contextual meaning, collocations.

---

## Plan

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.0'
title: Reading Ukrainian
subtitle: "From letters to words to sentences"
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
- section: "Склади (Syllables)"
  words: 250
  points:
  - "Большакова Grade 1 p.25: 'У слові стільки складів, скільки голосних звуків.'
    Count the vowels, count the syllables. This rule never breaks.
    ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables),
    банк (1 vowel = 1 syllable)."
  - "How to read a new word:
    1. Find the vowels (they're the syllable cores)
    2. Split at syllable boundaries (consonants prefer starting new syllables)
    3. Sound out each syllable
    4. Blend into the full word at natural speed
    Practice: а-пте-ка, у-ні-вер-си-тет, шо-ко-лад.
    Note: Ukrainian phonetic syllable division (складоподіл) follows the
    open-syllable principle — consonants prefer starting new syllables."
  - "Following Большакова p.29 звуковий аналіз method: identify vowels,
    divide into syllables, then read. This is how Ukrainian children learn."
- section: "Голосні літери (Vowel Letters)"
  words: 300
  points:
  - "Review from M01: 6 sounds, 10 letters. Now learn all 10 individually.
    Simple vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і].
    Each makes ONE consistent sound — no surprises."
  - "Iotated vowels (two sounds or softening):
    Я = [йа] at word start (яблуко) or after vowel (моя).
    After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е].
    Ї = ALWAYS [йі] — never softens. Only at word start, after vowel,
    or after apostrophe. Unique to Ukrainian."
  - "Critical minimal pairs:
    И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house).
    Listen to Anna's pronunciation videos for each — the difference
    is subtle but changes meaning."
- section: "Читання слів (Reading Words)"
  words: 300
  points:
  - "Apply M01 letter knowledge to read real words fluently.
    Strategy: don't read letter-by-letter. Read syllable-by-syllable.
    Start with the vowels (find them first), then build outward.
    Example: книга — find vowels И, А → кни-га → read."
  - "Common word patterns for reading practice:
    CVCV: мама, тато, каша, вода, рука, хата, коза, нога
    CVCCV: школа, книга, банда, парта
    CVC: дім, сон, ліс, дуб, хліб, банк
    The more patterns you see, the faster you read."
  - "Special letter combinations to watch for:
    Щ is always [шч] — що, ще, щастя.
    Ь has no sound — it softens: день, сіль, кінь.
    ' (apostrophe) separates: сім'я, м'ясо, п'ять.
    These will be explored fully in M03."
- section: "Читаємо разом (Reading Together)"
  words: 200
  points:
  - "Progressive reading practice — start simple, build up:
    Level 1 (2 syllables): мама, тато, вода, рука, хата, каша
    Level 2 (3 syllables): аптека, молоко, людина, вулиця
    Level 3 (4+ syllables): університет, бібліотека, фотографія"
  - "Reading a simple text (all Це + noun, no verbs):
    Це Київ. Це столиця. Тут аптека і банк. Там школа.
    Що це? Це кафе. А це пошта."
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: How do you count syllables in a Ukrainian word?
    What are the 6 vowel sounds? Name the 4 iotated vowel letters.
    What does Ь do? What does the apostrophe do?
    Read this word: бібліотека — how many syllables?"
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
  focus: "Divide words into syllables: мо-ло-ко, ап-те-ка"
  items: 8
- type: quiz
  focus: "How many syllables? Count the vowels."
  items: 8
- type: match-up
  focus: "Match iotated vowels to their sound components: Я=[й]+[а]"
  items: 4
- type: quiz
  focus: "Read the word and choose its meaning"
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- "Syllable rule: count vowels = count syllables (складоподіл)"
- "10 vowel letters → 6 vowel sounds mapping"
- "Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])"
- "Reading fluency: syllable-by-syllable word reading"
- "Ь, apostrophe, voiced/voiceless (preview — detailed in M03)"
register: розмовний
references:
- title: "Большакова Grade 1 буквар, p.25"
  notes: "Syllable rule: 'У слові стільки складів, скільки голосних звуків.'"
- title: "Большакова Grade 1 буквар, p.29"
  notes: "Звуковий аналіз слова method — how to analyze word sounds."
- title: "Захарійчук Grade 1 (NUS 2025), p.13-15"
  notes: "Sound notation: [•] for vowels, [–] for consonants, [=] for soft."
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

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

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- Dialogues: natural, not stilted. Real situations, real responses.
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

Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

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

- P1 (~70 words): Hook — present a long word like університет and ask "how would you even start reading this?" Introduce the golden rule from Большакова Grade 1 p.25: "У слові стільки складів, скільки голосних звуків." Count vowels = count syllables. Demonstrate: ма-ма (А, А = 2 syllables), мо-ло-ко (О, О, О = 3), банк (А = 1). This rule never breaks in Ukrainian.

- P2 (~80 words): Step-by-step method for reading any new word, adapted from Большакова p.29 звуковий аналіз. Four steps: (1) Find the vowels — circle them mentally, (2) Split at syllable boundaries — consonants prefer starting new syllables (open-syllable principle), (3) Sound out each syllable slowly, (4) Blend at natural speed. Demonstrate with аптека: vowels А, Е, А → а-пте-ка → аптека.

- P3 (~55 words): Practice the method on progressively longer words: о-са (2), шко-ла (2), мо-ло-ко (3), у-ні-вер-си-тет (5). Emphasize that every Ukrainian word, no matter how long, follows the same rule. Reminder: vowels are the skeleton of the word — find them first.

- Exercise: fill-in — divide 8 words into syllables (шо-ко-лад, бі-блі-о-те-ка, ву-ли-ця, лю-ди-на, сто-ли-ця, ка-ша, пі-сня, яб-лу-ко).

- P4 (~70 words): Syllable-counting exercise framed as a game — "How many syllables?" Count vowels, don't split: бібліотека (5), фотографія (5), людина (3), вулиця (3), каша (2), дім (1), сон (1), хліб (1). Connect to comprehension: knowing syllable count helps predict word rhythm and find the stressed syllable (наголос — coming in M03).

## Голосні літери (Vowel Letters) (~330 words total)

- P1 (~60 words): Recall from M01: Ukrainian has 6 vowel sounds but 10 vowel letters. Now learn each one. Introduce the simple vowels first — six letters that each make exactly one sound: А [а], О [о], У [у], Е [е], И [и], І [і]. No surprises, no variations. One letter = one sound, always.

- P2 (~90 words): The four iotated vowels — letters that can represent TWO sounds. Я = [йа] at word start (яблуко, яма, ясен) or after a vowel (моя, мрія). After a consonant, Я softens the consonant + [а] (пісня — the Н becomes soft). Same pattern for Ю = [йу] (юрта at start; люблю after consonant) and Є = [йе] (єнот at start; синє after vowel). Use textbook examples: маяк → ма|як, the Я starts a new syllable so it's [йа].

- P3 (~70 words): Ї — the unique one. ALWAYS two sounds [йі], never softens a consonant. Only appears at word start (їжак, їсти), after a vowel (мої, твої, лілії), or after apostrophe (з'їла). This letter exists only in Ukrainian — not in Russian, not in any other Slavic language. Practice words: їжак, їжаченя, з'їло (from textbook: "Колюче їжаченя з'їло слимака").

- Exercise: match-up — match 4 iotated vowels to their sound components: Я=[й]+[а], Ю=[й]+[у], Є=[й]+[е], Ї=[й]+[і].

- P4 (~60 words): Critical minimal pairs for И vs І — these are the hardest vowels for English speakers. кит (whale) vs кіт (cat), дим (smoke) vs дім (house), лис (fox) vs ліс (forest), сік (juice) vs рік (year). The difference changes meaning completely. Reference Anna's pronunciation videos for ear training. И is a back vowel (deeper), І is a front vowel (brighter).

- Exercise: quiz — 8 items: "How many syllables does this word have?" (бібліотека=5, їжак=2, яблуко=3, університет=5, дім=1, молоко=3, фотографія=5, каша=2). Students count vowels to answer.

- P5 (~50 words): Summary table of the 10 vowel letters organized in two rows: simple (А О У Е И І) and iotated (Я Ю Є Ї). Note the visual pairing: А↔Я, У↔Ю, Е↔Є, І↔Ї. The iotated letter adds [й] before its paired vowel sound. This pattern makes them easy to remember.

## Читання слів (Reading Words) (~330 words total)

- P1 (~80 words): Transition from individual letters to fluent word reading. Key principle: don't read letter-by-letter — read syllable-by-syllable. Demonstrate with книга: find vowels И, А → split кни-га → read each syllable → blend. Then школа: vowels О, А → шко-ла. The syllable is the natural reading unit in Ukrainian, just as it is in how Ukrainian children learn (Большакова method). Letter-by-letter reading is slow and loses meaning.

- P2 (~80 words): Common word patterns for reading practice, organized by structure. CVCV (consonant-vowel-consonant-vowel): мама, тато, каша, вода, рука, хата, коза, нога — the easiest pattern, two open syllables. CVC: дім, сон, ліс, дуб, хліб — one closed syllable, common short words. CVCCV: школа, книга, парта — consonant cluster in the middle, split before the cluster. Practice reading each group aloud, building speed.

- P3 (~70 words): Special letter combinations to watch for when reading. Щ is always pronounced [шч] — що, ще, щастя (never just [ш]). Ь (soft sign) has no sound of its own — it softens the preceding consonant: день, сіль, кінь. The apostrophe (') separates a consonant from an iotated vowel: сім'я [сімйа], м'ясо [мйасо], п'ять [пйать]. These will be explored fully in M03 — for now, just recognize them while reading.

- Exercise: quiz — read the word and choose its meaning, 6 items (яблуко=apple, молоко=milk, людина=person, столиця=capital, вулиця=street, шоколад=chocolate).

- P4 (~50 words): Reading tip: when you encounter a new word, use finger tracking — point to each syllable as you say it, then remove your finger and say the whole word. This physical technique helps bridge syllable-by-syllable reading to fluent whole-word reading. Ukrainian teachers use this method through Grade 1 and 2.

- P5 (~50 words): Words with iotated vowels in reading context — apply both skills together. Read: яблуко (я-блу-ко, Я at start = [йа]), пісня (пі-сня, Я after consonant = softening), моя (мо-я, Я after vowel = [йа]). Each position of the iotated vowel changes its role.

## Читаємо разом (Reading Together) (~220 words total)

- P1 (~60 words): Progressive reading ladder — start with the easiest words and build confidence. Level 1 (2 syllables): мама, тато, вода, рука, хата, каша. Level 2 (3 syllables): аптека, молоко, людина, вулиця. Level 3 (4+ syllables): університет, бібліотека, фотографія. Read each level until comfortable, then move up. Speed isn't the goal — accuracy is.

- P2 (~90 words): First connected reading passage — simple sentences using Це + noun structure (no verb conjugation needed). "Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта. Це вулиця. Тут людина. Це мама і тато." Read the passage slowly first, syllable by syllable. Then read again faster, blending words. Notice how much you can already read after just two modules — real Ukrainian sentences about a real Ukrainian city.

- P3 (~70 words): Reading self-assessment — try reading these words without help, then check. Present 6 words mixing all learned skills: бібліотека (5 syllables, all simple vowels), їжаченя (4 syllables, Ї at start), яблуко (3 syllables, Я at start), сім'я (2 syllables, apostrophe), столиця (3 syllables, ЦЯ combination), щастя (2 syllables, Щ + softened ТЬ). If you can read all six, you're ready for M03.

## Підсумок — Summary (~165 words total)

- P1 (~90 words): Recap the three core skills from this module. First: the syllable rule — count vowels to count syllables, works every time (У слові стільки складів, скільки голосних звуків). Second: the 10 vowel letters — 6 simple (А О У Е И І) and 4 iotated (Я Ю Є Ї), where iotated vowels represent two sounds at word/syllable start but soften consonants elsewhere. Third: reading strategy — find vowels, split into syllables, blend. You now have a method to read ANY Ukrainian word.

- P2 (~75 words): Self-check questions for review. How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe do? How many syllables in бібліотека? (Answer: 5 — count the vowels: І, І, О, Е, А.) Next module: M03 — Special Signs — deep dive into Ь, apostrophe, and consonant features.

Grand total: ~1320 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
