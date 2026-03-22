<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [2. Linguistic accuracy] [Major]
  Location: `Сік (juice) vs рік (year).`
  Issue: Presented as an example of why precision with vowels matters, right after "Кит vs кіт" and "Дим vs дім". However, "сік" and "рік" have the exact same vowel (і). This is a consonant minimal pair (с vs р), making it invalid as an example of vowel precision.
  Fix: Remove this pair or replace it with a valid vowel minimal pair (e.g., `бик` (bull) vs `бік` (side)).
- FIX: [2. Linguistic accuracy] [Major]
  Location: `Also compare би́ти (to hit) vs бі́ти — the stress and vowel together carry meaning.`
  Issue: Factually incorrect claim. Both words have the stress on the first syllable. The stress does not distinguish them; only the vowel (и vs і) carries the change in meaning.
  Fix: Remove the claim about stress. Rewrite to emphasize that the vowel alone changes the meaning: "Also compare бити (to hit) vs біти (beats) — the vowel alone changes the meaning."
- FIX: [1. Plan adherence] [Major]
  Location: Throughout the module (sections "Склади", "Голосні літери", "Читання слів", "Читаємо разом").
  Issue: The text fails to meet the word count targets for individual sections by 20-27%. The plan requires word targets to be respected within ±10%. The overall module is roughly 250 words short of its 1200-word target.
  Fix: Expand the linguistic explanations in each section. Add more examples of syllable division, more context for iotated vowels, and extend the reading practice text to meet the required word budgets.

- FIX (Linguistic): - **Error found:** "Сік (juice) vs рік (year)" is presented in a paragraph dedicated to teaching vowel minimal pairs (like И vs І: кит vs кіт, дим vs дім), but this is a consonant minimal pair (с vs р), making it confusing and factually incorrect for the context.
- **Error found:** The text claims: "compare би́ти (to hit) vs бі́ти — the stress and vowel together carry meaning." This is factually incorrect. Both "би́ти" and "бі́ти" have identical stress on the first syllable. Only the vowel diffe
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

## 7 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

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

- P1 (~90 words): Open with the golden rule from Большакова Grade 1 p.25: "У слові стільки складів, скільки голосних звуків." Demonstrate with мама (2 vowels А, А → ма-ма = 2 syllables), молоко (3 vowels О, О, О → мо-ло-ко = 3 syllables), банк (1 vowel А → 1 syllable), сон (1 vowel О → 1 syllable). Emphasize: this rule NEVER breaks in Ukrainian.
- P2 (~100 words): Step-by-step method for reading any new word, following Большакова p.29 звуковий аналіз: (1) Find the vowels — they are the syllable cores. (2) Split at syllable boundaries — Ukrainian follows the open-syllable principle (складоподіл), so consonants prefer starting new syllables. (3) Sound out each syllable slowly. (4) Blend at natural speed. Walk through аптека: vowels А, Е, А → а-пте-ка → аптека.
- P3 (~85 words): Practice the method on progressively harder words: оса (2 syllables), школа (2 syllables), молоко (3 syllables), університет (5 syllables — у-ні-вер-си-тет). Note that single-vowel words like ліс, дуб, хліб are one syllable — no splitting needed. Mention Большакова's classroom exercise: "Визнач, скільки складів у кожному слові" — this is exactly how Ukrainian first-graders learn.
- **Exercise: quiz** — "How many syllables? Count the vowels." 8 items: сон, оса, каша, молоко, ананас, книга, бібліотека, університет.

## Голосні літери (Vowel Letters) (~330 words total)

- P1 (~100 words): Recall from M01: Ukrainian has 6 vowel sounds but 10 vowel letters. Now learn each one. The 6 simple vowels make one consistent sound each: А [а] (мама), О [о] (молоко), У [у] (вулиця), Е [е] (день), И [и] (кит), І [і] (кіт). No surprises — each letter = one sound, every time. These 6 are the syllable-building sounds from the previous section.
- P2 (~120 words): Iotated vowels — the 4 letters that can represent TWO sounds. Я = [йа] at word start (яблуко) or after a vowel (моя); after a consonant it softens + [а] (пісня — the Н becomes soft). Ю = [йу] at word start (юнак) or after a vowel; after a consonant → softening + [у] (люблю). Є = [йе] at word start (єнот) or after a vowel (синє); after a consonant → softening + [е]. Ї is unique — ALWAYS [йі], never softens a consonant. It appears only at word start (їжак), after a vowel (мої), or after an apostrophe (з'їв). Ї is distinctly Ukrainian.
- P3 (~110 words): Critical minimal pairs where one vowel letter changes the entire meaning: кит (whale) vs кіт (cat), дим (smoke) vs дім (house), лис (fox) vs ліс (forest), сік (juice) vs рік (year). The И vs І distinction doesn't exist in English — both are "ee"-adjacent but differ in tongue position. И is lower and more central; І is higher and fronter. Reference Anna's pronunciation videos for audio examples. Also: бути (to be) vs біти (to hit) — stress and vowel both matter. This is why reading carefully matters from day one.
- **Exercise: match-up** — "Match iotated vowels to their sound components." 4 items: Я=[й]+[а], Ю=[й]+[у], Є=[й]+[е], Ї=[й]+[і].

## Читання слів (Reading Words) (~330 words total)

- P1 (~110 words): The key habit: never read letter-by-letter — read syllable-by-syllable. Apply the method from Section 1 to real words. Demonstrate with книга: find vowels И, А → кни-га → blend → книга. Then школа: vowels О, А → шко-ла → школа. Then столиця: vowels О, И, А → сто-ли-ця → столиця (Київ — столиця України). The faster you spot vowels, the faster you read. Ukrainian spelling is highly regular — once you know the letters, reading is predictable. No silent letters, no surprise pronunciations (unlike English).
- P2 (~110 words): Common word patterns for building reading fluency. CVCV (open syllables): мама, тато, каша, вода, рука, хата, коза, нога — these are the easiest because every syllable ends in a vowel. CVCCV (consonant cluster): школа, книга, парта — the cluster stays together at the syllable start. CVC (closed syllable): дім, сон, ліс, дуб, хліб, банк — single syllable, no splitting needed. Practice reading each group aloud, starting slow, then faster. The more patterns your eye recognizes, the less you need to consciously split.
- P3 (~110 words): Three special letter combinations to watch for now (full treatment in M03). Щ always sounds [шч] — що, ще, щастя. Don't try to pronounce it as one sound; it's always the combination [шч]. Ь (soft sign) has no sound of its own — it softens the consonant before it: день [ден'], сіль [с'іл'], кінь [к'ін']. The apostrophe (') separates a consonant from an iotated vowel, keeping the [й] sound: сім'я [с'імйа], м'ясо [мйасо], п'ять [пйат']. Think of the apostrophe as a wall — the consonant stays hard, and the vowel keeps its two sounds.
- **Exercise: fill-in** — "Divide words into syllables." 8 items: молоко → мо-ло-ко, аптека → а-пте-ка, вулиця → ву-ли-ця, шоколад → шо-ко-лад, людина → лю-ди-на, яблуко → я-блу-ко, столиця → сто-ли-ця, бібліотека → бі-блі-о-те-ка.

## Читаємо разом (Reading Together) (~220 words total)

- P1 (~100 words): Progressive reading ladder — build from simple to complex. Level 1 (2 syllables): мама, тато, вода, рука, хата, каша — all CVCV, all open syllables. Level 2 (3 syllables): аптека, молоко, людина, вулиця — longer but still regular patterns. Level 3 (4+ syllables): університет, бібліотека, фотографія, шоколад — these look intimidating but follow the same rules. Find the vowels, split, sound out, blend. Try reading each word three times: slow → medium → natural speed.
- P2 (~120 words): Read a simple connected text — all using Це + noun pattern (no verb conjugation needed yet). "Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта. Ось бібліотека. Там книги." Every word in this text uses letters and patterns from M01 and this module. Read it once slowly (syllable by syllable), then again at natural speed. Notice how Ukrainian sentences are short and clear — subject + noun, no articles (no "a" or "the"). If you can read this paragraph aloud without stopping, you are reading Ukrainian.
- **Exercise: quiz** — "Read the word and choose its meaning." 6 items: молоко, яблуко, людина, столиця, книга, вулиця — each with 3-4 Ukrainian-image or English-meaning options.

## Підсумок — Summary (~165 words total)

- P1 (~165 words): Recap the four key skills from this module. (1) Syllable counting — "У слові стільки складів, скільки голосних звуків" — you now have a rule that works for every Ukrainian word. (2) Vowel letter system — 6 simple vowels (А, О, У, Е, И, І) each make one sound; 4 iotated vowels (Я, Ю, Є, Ї) can make two sounds or soften a consonant. (3) Reading strategy — find vowels → split into syllables → sound out → blend. Never read letter-by-letter. (4) Special signs preview — Щ = [шч], Ь softens, apostrophe separates (full details in M03). Self-check: read бібліотека aloud — how many syllables? (5: бі-блі-о-те-ка). Can you spot the vowels in університет? (У, І, Е, И, Е — 5 syllables). Next module: Special Signs — Ь, apostrophe, and the full consonant system.

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
