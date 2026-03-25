# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **11: How Many?** (A1, A1.2 [My World]).

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
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format.

**CRITICAL: Each exercise MUST match a specific `activity_hints` entry from the Plan.**
- Use the EXACT `type` specified (quiz, fill-in, match-up, group-sort, true-false)
- Follow the `focus` description EXACTLY — if the plan says "Answer: У тебе є...? Так / Ні", your quiz must test exactly that pattern
- Match the `items` count specified
- Do NOT invent different exercises — the plan's activity_hints are the specification

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
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує ця сумка? — Двісті гривень.
    — А ця? — Сто п''ятдесят. — Добре, я беру цю. (Accusative ''цю'' as chunk — no
    grammar.) Numbers emerge through real shopping context.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: How Many?
**Module:** how-many | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 6
> СЛОВА — НАЗВИ ПРЕДМЕТІВ
> Кожний предмет ти можеш назвати словом.
> ХТО? хлопчик
> ХТО? дівчинка
> ЩО? м’яч
> ЩО? сонце
> Які слова відповідають на питання хто? що?
> дерево
> Олег
> голуб
> Оля
> собака
> м’яч
> трава
>  
> З якою думкою ти погоджуєшся? Поясни чому.
> 1
> 2
> Слово квітка відповідає 
> на питання що?
> Слово кіт відповідає 
> на питання хто?

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> ■мИ|28| Змініть подані слова за зразком і запишіть.
> навчати — навчання_ >
> Розкажи про свої 
> успіхи в навчанні.
> читати 
> міркувати 
> додавати 
> малювати 
> бажати 
> уміти
> • Поясніть, що називають записані слова. На які питання вони 
> відповідають? Усно складіть речення з однією парою слів 
> (на вибір).
> 29 Заміни сполучення слів за зразком і запиши.
> Книжка з бібліотеки — ? 
> Шафа для книжок — ?
> Вистава в театрі — ?
> Гра на комп'ютері — ?
> розм°ва по телефону — телефонна розмова
> • Запиши утворені сполучення с

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 142
> Досліди, скількома 
> способами 
> можна 
> прочитати числовий 
> вираз.
> Я — дослідник
> Я — дослідниця
> Навчаюся читати числові вирази
> 70 + 25
> 80 – 25
> Сума чисел сімдесят і двадцять  
> п’ять.
> Сімдесят збільшити на двадцять  
> п’ять.
> Перший доданок сімдесят, другий — 
> двадцять п’ять.
> До сімдесяти додати двадцять п’ять.
> Різниця чисел вісімдесят і двадцять п’ять.
> Вісімдесят зменшити на двадцять п’ять.
> Зменшуване вісімдесят, від’ємник —  
> двадцять п’ять.
> Від вісімдесяти відняти двадцять п’ять.
> Правильно утв

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 95
> —	 Доб-ро-го ран-ку! — мов-лю за 
> зви-ча-єм. 
> —	 Доб-ро-го ран-ку! — кож-но-му 
> зи-чу  я. 
> —	 Доб-ро-го  дня! — лю-дям ба-
> жа-ю.
> —	 Ве-чо-ра  доб-ро-го! — стріч-
> них  ві-та-ю.
> І  ус-мі-ха-ють-ся   в   від-по-відь  лю-
> ди  — доб-рі  сло-ва  ж  бо  для  кож-
> но-го лю-бі.
>                                                    Вадим Бі­рюков 
> 	 Як ми називаємо виділені слова?
> 	 Добери до кожної ситуації слова ввічливості.

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> § 15 СЛОВА — НАЗВИ ЧИСЕЛ 
> (ЧИСЛІВНИКИ)
> НАВЧАЮСЯ ВИЗНАЧАТИ СЛОВА, ЯКІ НАЗИВАЮТЬ ЧИСЛА
> Я — учителька
> Прочитай і розкажи 
> ; у класі.
> розрізняю
> Я — учитель
> скільки? 
> ----------- -- - >
> котрий?
> В українській мові є слова — назви чисел (кількості 
> предметів), які відповідають на питання скільки?. 
> Це числівники.
> і[ Вивчи лічилку напам'ять. Розкажи у класі.
> Число числівник називає,
> і кожен з нас це добре знає. 
> Один, два, три, чотири, п'ять — 
> учімось, друзі, рахувать!
> п ять
> ? звуків, ? букв,
> ? складів

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 138
> Поняття про числівник як частину 
> мови
> Навчаюся розпізнавати числівники
> Прочитай і розкажи у 
> класі.
> Я — учителька
> Я — учитель
> два
> дванадцять
> двадцять
> двісті
> Слова, які називають кількість предметів і відповідають 
> на питання скільки?, є числівниками. Числівник — це 
> частина мови.
> 43
> Числівники можуть називати і порядок предметів під 
> час лічби і відповідати на питання котрий?: другий, 
> дванадцятий, двадцятий, двохсотий.
> 1   Прочитай вірш Лесі Лужецької. Вивчи його напам’ять. Розкажи 
> однок

## Числа 1-20 (Numbers 1-20)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 103
> 	
> Визнач, що не так на малюнку.
> 	 Хто один, а кого на малюнку зображено бага-
> то?
> 	 Вимов слова — назви намальованих пред-
> метів, у яких є ь.
> Апельсин      _____ ,   ______ ,     _______ ,    ______.
> 12345678      6 7 8       2 3 8 5        6 1 8 7       4 7 2 1
> 	 Утвори нові слова. Запиши.
> 	
> Поміркуй, хто куди спішить.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Числівники можуть називати і порядок предметів 
> під час лічби. Тоді вони відповідають на питання 
> '« котрий?: перший, другий.
> 3| Прочитай і запиши прислів'я, 
> об'єднавши за змістом сполучення 
> слів у колонках.
> Яка перша буква 
> в абетці?
> Сім разів відміряй,
> аніж сім разів почути.
> Краще один раз побачити, 
> Де сім господинь,
> там хата не метена. 
> а один раз відріж.
> • Назви числівник, який повторюється у прислів'ях. На яке
> питання він відповідає?
> Про кого
> так говорять?
> Г
> У нього сім ? 
> на тиждень.
> Ус

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 140
> Вимова і правопис найуживаніших 
> числівників
> Вивчаю числівники 5, 9, 11–20, 30, 50, 60, 70, 80
> 44
> Правильно наголошуй числівники!
> одинадцять
> дванадцять
> тринадцять
> чотирнадцять
> п’ятнадцять
> шістнадцять
> сімнадцять
> вісімнадцять
> дев’ятнадцять
> двадцять
> тридцять
> п’ятдесят
> шістдесят
> сімдесят
> вісімдесят
> 	 	
> 1   Назвіть числа і запишіть числівники. Поставте наголос у словах.
> 	 	
> 3   Утворіть від слів п’ять, шість, сім, 
> вісім, дев’ять нові числівники за 
> зразком. Поставте наголос у словах.
> 2   Запи

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 92
> 	
> Утвори нові слова.
> 	
> «Збери» слова. Прочитай прислів’я. Перше 
> слово написане на кленових листках, дру-
> ге — на тополиних, третє — на листках дуба. 
> Поясни, як ти розумієш це прислів’я.
> 	 Розкажи, що змінилося на малюнках. Поясни 
> чому.
> все
> Лі
> ко
> ні
> ни
> ли
> му
> во
> — Сходи вверх і вниз біжать!
> — Ну а люди?
> — Всі стоять!
> — Знаю я! — сказав Дмитро.—
> Сходи — _________ у метро (М. Братко).
> Загадка
> Е к с к а в а т о р   _______ , _______ ,  ______ , ... .
> Ескалатор — рухомі сходи в метро.
> 1 2 3 4 5

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 94
> 1. (Скільки?) … разів відміряй, (скільки?) … раз відріж. 
> 2. (Скільки?) …  літо краще, як (скільки?)  …  зим. 3. (Скільки?) 
> … голова добре, а (скільки?) … — краще. 
> Слова для довідки: одна, один, одне, сім, дві, сто.
> 2.	 Запишіть одне прислів’я (на вибір). Підкресліть числівник 
> з іменником. 
> 337. 1.	 Розглянь малюнки. З яких казок зображені герої?
> 2.	 Склади речення за двома малюнками (на вибір). Уживай 
> числівники.
> 338. 1.	 Дай відповіді на запитання двома словами.
> Скільки м’ячів? Скільки

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 142
> Досліди, скількома 
> способами 
> можна 
> прочитати числовий 
> вираз.
> Я — дослідник
> Я — дослідниця
> Навчаюся читати числові вирази
> 70 + 25
> 80 – 25
> Сума чисел сімдесят і двадцять  
> п’ять.
> Сімдесят збільшити на двадцять  
> п’ять.
> Перший доданок сімдесят, другий — 
> двадцять п’ять.
> До сімдесяти додати двадцять п’ять.
> Різниця чисел вісімдесят і двадцять п’ять.
> Вісімдесят зменшити на двадцять п’ять.
> Зменшуване вісімдесят, від’ємник —  
> двадцять п’ять.
> Від вісімдесяти відняти двадцять п’ять.
> Правильно утв

## Десятки і сотні (Tens and Hundreds)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 92
> 	
> Утвори нові слова.
> 	
> «Збери» слова. Прочитай прислів’я. Перше 
> слово написане на кленових листках, дру-
> ге — на тополиних, третє — на листках дуба. 
> Поясни, як ти розумієш це прислів’я.
> 	 Розкажи, що змінилося на малюнках. Поясни 
> чому.
> все
> Лі
> ко
> ні
> ни
> ли
> му
> во
> — Сходи вверх і вниз біжать!
> — Ну а люди?
> — Всі стоять!
> — Знаю я! — сказав Дмитро.—
> Сходи — _________ у метро (М. Братко).
> Загадка
> Е к с к а в а т о р   _______ , _______ ,  ______ , ... .
> Ескалатор — рухомі сходи в метро.
> 1 2 3 4 5

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 94
> 1. (Скільки?) … разів відміряй, (скільки?) … раз відріж. 
> 2. (Скільки?) …  літо краще, як (скільки?)  …  зим. 3. (Скільки?) 
> … голова добре, а (скільки?) … — краще. 
> Слова для довідки: одна, один, одне, сім, дві, сто.
> 2.	 Запишіть одне прислів’я (на вибір). Підкресліть числівник 
> з іменником. 
> 337. 1.	 Розглянь малюнки. З яких казок зображені герої?
> 2.	 Склади речення за двома малюнками (н

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Числа 1-20 (Numbers 1-20)` (~300 words)
- `## Десятки і сотні (Tens and Hundreds)` (~300 words)
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

**Required:** один, два, три, чотири, п'ять (1-5), шість, сім, вісім, дев'ять, десять (6-10), двадцять, тридцять, сорок (20, 30, 40), сто, тисяча (100, 1000), скільки (how many/how much), коштує (costs — from коштувати), гривня (hryvnia — Ukrainian currency), рік, роки, років (year/years — age chunks)
**Recommended:** п'ятдесят, шістдесят, сімдесят (50, 60, 70), вісімдесят, дев'яносто (80, 90), двісті, триста, п'ятсот (200, 300, 500), копійка (kopek), номер (number — phone/room), нуль (zero)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
