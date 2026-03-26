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

- P1 (~40 words): Brief scene-setting — numbers are everywhere in daily life: prices at the market, ages when meeting people, phone numbers. This module teaches counting and using numbers in real situations. Transition to first dialogue.
- Dialogue 1 (~100 words): At a market stall. Оксана shops for a bag. — Скільки коштує ця сумка? — Двісті гривень. — А ця? — Сто п'ятдесят. — Ой, дорого! А є дешевше? — Ось ця — вісімдесят гривень. — Добре, я беру цю. Include natural filler (ой, ось) and the chunk "я беру цю" without explaining accusative. Seller uses friendly tone.
- P2 (~30 words): Brief gloss of key phrases from Dialogue 1: Скільки коштує? (How much does it cost?), гривень (hryvnias), дорого (expensive), дешевше (cheaper), я беру (I'll take). No grammar — just meaning.
- Dialogue 2 (~100 words): At a student gathering, extending M05 introductions. — Привіт! Як тебе звати? — Андрій. А тебе? — Марина. Скільки тобі років? — Мені двадцять п'ять. А тобі? — Мені тридцять два. А це мій брат Тарас. — Скільки йому років? — Йому вісімнадцять. Include Мені/тобі/йому pattern naturally across three people.
- P3 (~60 words): Gloss of the age chunk pattern: Мені ... років literally = "to me ... of years." Present the three forms as memorized chunks: рік (1 — двадцять один рік), роки (2-4 — двадцять два роки), років (5+ — двадцять п'ять років). Explicit note: just memorize the pattern, grammar comes later in A2.

## Числа 1-20 (Numbers 1-20) (~330 words total)

- P1 (~80 words): Numbers 1-10 presented in a clear list: один, два, три, чотири, п'ять, шість, сім, вісім, дев'ять, десять. Pronunciation notes: п'ять and дев'ять have apostrophe (the lips open wide for я after the consonant); сім (not "сем" — the і is clear); шість (soft ть at the end). Each number shown with a familiar noun from M08: один стіл, два стільці, три книги, чотири вікна.
- P2 (~50 words): Gender note as chunk — один/одна/одне depending on the noun: один стіл, одна книга, одне вікно. Similarly два/дві: два стільці, дві книги. Present as patterns to memorize with familiar nouns, not as grammar rules. "You'll notice the noun changes too — just copy the patterns for now."
- Exercise 1 (fill-in, 10 items): Write the number in words. Numerals shown: 3, 7, 5, 9, 1, 6, 10, 8, 4, 2. Mixed order to prevent mechanical counting.
- P3 (~90 words): Numbers 11-19 built on the -надцять pattern: одинадцять, дванадцять, тринадцять, чотирнадцять, п'ятнадцять, шістнадцять, сімнадцять, вісімнадцять, дев'ятнадцять. Explain the pattern: base number + надцять (compare English "-teen"). Stress always on -на́-: одина́дцять, двана́дцять, п'ятна́дцять. Then двадцять (20) — stands alone, stress двáдцять. Note apostrophe carries over: п'ятнадцять, дев'ятнадцять.
- P4 (~50 words): Mini counting practice — connect to real life. Скільки тобі років? Practice saying ages in the teens: Мені тринадцять. Мені п'ятнадцять. Мені вісімнадцять. Мені дев'ятнадцять. Reinforce the рік/роки/років pattern: тринадцять років, чотирнадцять років (all use років because 13-19 end in 5+).
- Exercise 2 (quiz, 6 items): Скільки років? Match ages to descriptions: "Оксана is a university student (19)" → дев'ятнадцять; "Тарас just got his driver's license (18)" → вісімнадцять; etc.

## Десятки і сотні (Tens and Hundreds) (~330 words total)

- P1 (~80 words): Tens 20-90 as a clear list: двадцять (20), тридцять (30), сорок (40), п'ятдесят (50), шістдесят (60), сімдесят (70), вісімдесят (80), дев'яносто (90), сто (100). Highlight two irregulars with emphasis: сорок (NOT "чотиридесят") and дев'яносто (NOT "дев'ятдесят") — these must simply be memorized. The regular pattern: base + -десят (п'ять → п'ятдесят).
- P2 (~60 words): Combined numbers — just add the unit after the ten: двадцять один (21), тридцять п'ять (35), сорок сім (47), п'ятдесят три (53), шістдесят вісім (68), дев'яносто дев'ять (99). No hyphen, no special joining — two separate words. Practice reading: your age, a friend's age, a parent's age.
- Exercise 3 (fill-in, 10 items): Write the number in words: 15 → п'ятнадцять, 47 → сорок сім, 23 → двадцять три, 90 → дев'яносто, 40 → сорок, 68 → шістдесят вісім, 11 → одинадцять, 52 → п'ятдесят два, 34 → тридцять чотири, 99 → дев'яносто дев'ять.
- P3 (~70 words): Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400), п'ятсот (500), шістсот (600), сімсот (700), вісімсот (800), дев'ятсот (900), тисяча (1000). Pattern: 2-4 use -ста (двісті is irregular), 5-9 use -сот. Combined: сто двадцять п'ять (125), двісті п'ятдесят (250), п'ятсот сімдесят три (573).
- P4 (~70 words): Гривня with numbers — three memorized patterns: одна гривня (1), дві гривні (2-4: три гривні, чотири гривні), п'ять гривень (5+: десять гривень, сто гривень, двісті гривень). Real prices from Ukrainian life: кава — тридцять п'ять гривень, хліб — двадцять гривень, квиток у метро — вісім гривень. Reference ULP Ep9: Anna teaches numbers through real prices.
- Exercise 4 (quiz, 8 items): Скільки коштує? Match price tags (shown as numerals: 250 грн, 45 грн, 1000 грн, etc.) to their written-out forms. Include гривня/гривні/гривень agreement in the options.

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Phone numbers — Ukrainian format: +38 (0XX) XXX-XX-XX. Read digit by digit or in pairs: нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім. Introduce нуль (zero). Practice with two example numbers: Мій номер — нуль дев'яносто три, п'ять сім два, тридцять один, дев'яносто два. Note: Ukrainians often say digits in pairs for the last six digits.
- Exercise 5 (fill-in, 4 items): Phone number dictation — numbers shown as audio transcription prompts: "нуль дев'яносто сім, шість п'ять чотири, двадцять два, тридцять один" → student writes 097-654-22-31. Four different numbers.
- P2 (~100 words): Three practical uses of numbers recap. 1. Prices: Скільки коштує? — Двісті п'ятдесят гривень. Дорого чи дешево? 2. Age: Скільки тобі/вам років? — Мені двадцять три роки. Remember: рік (1), роки (2-4), років (5+). 3. Phone: Мій номер телефону — ... Read pairs of digits. Нуль is zero. Quick reference table showing the рік/роки/років and гривня/гривні/гривень patterns side by side — same logic (1 = singular, 2-4 = special plural, 5+ = genitive plural), memorized as chunks.
- P3 (~80 words): Self-check challenges — say these aloud in Ukrainian: your age (Мені ... років/роки/рік), a price (двісті п'ятдесят гривень for 250 UAH), your phone number digit by digit, count from 1 to 20 without pausing, say these numbers: 40, 90, 100, 500, 1000 (the tricky ones). Cultural note: Ukrainians use гривня (₴), divided into 100 копійок. One копійка, дві копійки, п'ять копійок.
- P4 (~70 words): What's next preview — in Module 12 (This and That), you'll point at things and describe them. You already know ця сумка from the market dialogue — next you'll learn how to say "this one" and "that one" for all genders. The numbers from this module will keep appearing in every future module — prices, ages, addresses, dates. Keep practicing: say every number you see in Ukrainian.

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
