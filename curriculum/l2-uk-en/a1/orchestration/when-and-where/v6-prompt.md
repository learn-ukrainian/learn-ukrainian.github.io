# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **45: When and Where** (A1, A1.7 [Communication]).

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
module: a1-045
level: A1
sequence: 45
slug: when-and-where
version: '1.1'
title: When and Where
subtitle: Що, де, коли — building your first complex sentences
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Use що, де, коли as subordinating conjunctions in basic complex sentences
- Build sentences like Я знаю, що...; Я не знаю, де...; Скажи, коли...
- Distinguish що/де/коли as question words vs conjunctions
- Combine main clause + subordinate clause naturally
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Planning to meet: — Ти знаєш, де нове кафе? — Так, я знаю, де воно.
    — Скажи, коли ти вільний. — Я вільний, коли закінчу роботу. — Добре. Я думаю,
    що о шостій буде добре. — Так, я теж думаю, що це гарний час. Subordinating conjunctions:
    де (where), коли (when), що (that).'
  - 'Dialogue 2 — Asking about someone: — Ти знаєш, що Олена вже в Києві? — Ні, я
    не знав! А де вона живе? — Я не знаю, де саме. Але я знаю, що біля центру. — Скажи
    їй, коли побачиш, що я хочу зустрітися. — Добре, скажу, коли побачу. Complex sentences
    in natural conversation.'
- section: Складне речення (Complex Sentences)
  words: 300
  points:
  - 'In M44 you learned to connect EQUAL ideas: Я читаю, і він пише. Now: connecting
    a MAIN idea with a DEPENDENT idea. Main clause + що/де/коли + subordinate clause:
    Я знаю, + що він тут. (I know that he''s here.) Я не знаю, + де він живе. (I don''t
    know where he lives.) Скажи мені, + коли ти прийдеш. (Tell me when you''ll come.)
    Grade 5 term: складнопідрядне речення (complex sentence with subordinate clause).'
  - 'Comma rule — always before що, де, коли as conjunctions: Я думаю, що це правильно.
    (comma before що) Він не знає, де магазин. (comma before де) Зателефонуй, коли
    прийдеш. (comma before коли) This is different from English — Ukrainian ALWAYS
    uses a comma here.'
- section: Що, де, коли — двоє облич (Two Faces)
  words: 300
  points:
  - 'These words have two jobs: 1. Question words (already known from M20): Що це?
    (What is this?) Де ти? (Where are you?) Коли ти прийдеш? (When?) 2. Conjunctions
    (NEW — connecting clauses): Я знаю, що це книжка. Я знаю, де ти. Скажи, коли прийдеш.
    How to tell? Question → at the start, with ? at the end. Conjunction → in the
    middle, connecting two parts.'
  - 'Common patterns with що, де, коли: Я знаю, що... / Я не знаю, що... (I know/don''t
    know that...) Я думаю, що... (I think that...) Він каже, що... (He says that...)
    Я знаю, де... / Я не знаю, де... (I know/don''t know where...) Скажи, коли...
    / Я не знаю, коли... (Tell me when... / I don''t know when...) Коли я прийду,
    ми поговоримо. (When I arrive, we''ll talk.)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Subordinating conjunctions at A1: | Conjunction | Meaning | Example | | що |
    that | Я знаю, що він тут. | | де | where | Я не знаю, де кафе. | | коли | when
    | Скажи, коли прийдеш. | Always a comma before the conjunction. Combined with
    M44 conjunctions, you can now build rich sentences: Я не йду, бо я не знаю, де
    це. (two conjunctions!) Він каже, що прийде, коли закінчить. (two subordinate
    clauses!) Self-check: Build 3 sentences with що, де, коли: Я думаю, що... Я не
    знаю, де... Скажи мені, коли...'
vocabulary_hints:
  required:
  - що (that — conjunction)
  - де (where — conjunction)
  - коли (when — conjunction)
  - знати (to know)
  - думати (to think)
  - казати (to say/tell)
  recommended:
  - сказати (to say — perfective)
  - бачити (to see)
  - чути (to hear)
  - розуміти (to understand)
  - речення (sentence, n)
  - головне (main — as in main clause)
activity_hints:
- type: fill-in
  focus: 'Complete: Я знаю, ___ він тут. Я не знаю, ___ вона живе. Скажи, ___ ти прийдеш.'
  items: 8
- type: quiz
  focus: Question word or conjunction? Де ти живеш? vs Я знаю, де ти живеш.
  items: 8
- type: fill-in
  focus: 'Build complex sentences: Я думаю, що ___. Він каже, що ___.'
  items: 6
- type: quiz
  focus: Where is the comma? Choose correct punctuation in complex sentences
  items: 8
connects_to:
- a1-046 (Holidays)
prerequisites:
- a1-044 (Linking Ideas)
grammar:
- 'Subordinating conjunctions: що (that), де (where), коли (when)'
- 'Complex sentence structure: main clause + comma + conjunction + subordinate clause'
- 'Dual role of що/де/коли: question words vs conjunctions'
register: розмовний
references:
- title: State Standard 2024, §4.3.2
  notes: Basic complex sentences — що, де, коли as subordinating conjunctions.
- title: 'Grade 5 textbook: Складнопідрядне речення (Заболотний)'
  notes: Introduction to subordinate clauses with що, де, коли.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: When and Where
**Module:** when-and-where | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 218
> Доброго ранку! Добрий день! Привіт! Радий бачити тебе. 
> * * *
> До побачення! На все добре! Гарного дня! Бувайте здорові! До зу-
> стрічі!
> Бажаю успіхів! Хай щастить! Рада була зустрітися.
> * * *
> Вибачте. Пробачте. Прошу вибачити (пробачити).
> Даруйте. Перепрошую. Вибачте, що турбую.
> * * *
> Дякую. Щиро дякую. Я тобі дуже вдячний. Будь ласка. Нема 
> за що.
> 528.	І. ПОПРАЦЮЙТЕ В ПАРАХ. Уявіть, що хтось із вас опинився в 
> чужому місті і йому необхідно з’ясувати, де розміщено стадіон (цирк чи 
> театр). А

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) рано; пи-
> шаюся (чим?) успіхами.  
> Підмет

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 235
> 235
> Зверніть увагу! 
> Вибір того чи того стійкого етикетного вислову залежить від 
> ситуації спілкування, а також від віку, соціального статусу, 
> Люди, які володіють мовленнєвим етикетом, більш успішні й
> швидше досягають порозуміння з іншими. Під час спіл ку ван-
> ня можемо використовувати стійкі етикетні вислови. 
> Етикетні
> тематичні групи
> Стійкі етикетні вислови
> (формули спілкування)
> Вітання
> Добрий день! Добридень! Вітаю! Привіт! Добро-
> го здоров’я! Моє шанування! Радий(-а) тебе ба-
> чити! Здор

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 218
> Недоліки 
>   Обмежені просторові (не -
> можливість спілкування з 
> тими, хто далеко) і часові 
> (потрібно інколи погодити 
> час для спілкування) мож -
> ливості.
>   Сором’язливість, невпевне-
> ність в умовах реального 
> спілкування подолати важче
>   Обмежене сприйняття іншої 
> людини.
>   Заміна живих емоцій.
>   Погіршення якості мовного 
> оформлення.
>   Створення надмірно теплич-
> них умов.
>   Багато можливостей для 
> обману, шахраювання.
>   Поява інтернет-залежності
> 499   Прочитайте репліки. Відреагуйте на них

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 58
> ПОЕТИЧНИЙ  ДИВОСВІТ
> •	 Виділене у вірші слово означає
> А 	 розтрушувати сипкі й інші предмети
> Б	 видавати різні звуки пошепки, майже беззвучно
> В	 надзвичайно швидко пересуватися в просторі
> Г 	 їхати верхи, трясучись від нешвидкого бігу коня
> Чи вірите ви в те, що різні предмети у вашому 
> домі живуть своїм життям? Вони так само, як і ви, 
> спілкуються, дружать, запрошують на чай… Якщо 
> не вірите, то прочитайте казковий вірш І. Жиленко «Гном у буфеті» та 
> переконайтеся в цьому. 
>           ГНОМ У Б

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 149
> 149
> ІІ. ПОПРАЦЮЙТЕ В ПАРАХ. Розподіліть між собою світлини. Доберіть за обра-
> ною світлиною 4–6 прислівників і запишіть. Зіставте свої записи. Чи є у вас одна-
> кові прислівники?  
> ІІІ. Складіть усно речення за одним із зображень, використавши кілька дібраних 
> прислівників.
> ПО РІВ НЯЙМО:
> добре
> Ранком
> КОЛО ДУМОК. Поміркуйте, до якої частини мови належить кожне виділене 
> слово. Розберіть ці слова за будовою.
> 1. Вечорами корисно бігати, щоб бути в гарній фізичній фор-
> мі (З довідника). 2. Я суму

## Складне речення (Complex Sentences)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 132
> Між частинами складного речення ставимо кому.
> Сполучники, що з’єднують частини складного речення: 
> і (й), та, але, проте, зате, однак; що, щоб, бо, тому 
> що та інші.
> Частини складного речення поєднують також займен-
> ники: хто, що, який, чий, котрий і прислівники: де, 
> коли, як, куди, звідки. 
> Наприклад: Успіху досягає лише той, хто працює над 
> досягненням його (Д. Браун, Н. Кей).
> Життя постійно пропонує нам вибір, не сходь із пра-
> вильного шляху (Д. Браун).
> 322   Виявляється, складне речення

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 68
> 1.	Прочитайте слова в колонках і виконайте завдання.
> південно-західний
> українсько-німецький 
> м’ясо-молочний 
> південноукраїнський 
> західнонімецький 
> м’ясокомбінат
> А.	 У якій колонці частини складних слів незалежні, однотипні й між ними 
> можна поставити сполучник і? 
> Б.	 Як пишемо (разом чи з дефісом) складні слова, частини яких незалежні, 
> однотипні?
> Складні слова пишемо разом або з дефісом. 
> Разом
> складні іменники зі сполучними 
> голосними о, е
> лісостеп, газогін, водолаз, хвиле-
> різ
> складні пр

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 30
> 1.	Прочитайте слова в колонках і виконайте завдання.
> давньогрецький
> північноєвропейський
> жовтогарячий
> українсько-грецький
> північно-західний
> жовто-синій
> А.	 У якій колонці частини складних слів рівноправні?
> Б.	 Сформулюйте правило написання складних слів разом і з дефісом.
> 2.	 Доберіть по два приклади до кожного правила написання складних слів 
> (усно). 
> Написання складних слів разом
> Правило
> Приклади
> складні іменники зі сполучним голосним о, е
> … , …
> складні прикметники із залежними частинами
> …

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 240
> Відомості із синтаксису й пунктуації.  Кома між частинами складного речення
> Вправа 386
> Виконайте тест.  У завданнях 1 і 2 лише один правильний варіант відповіді, 
> у  завданні 3 потрібно встановити відповідність між варіантами.
> 1.	 Складні речення записано в  усіх рядках, ОКРІМ
> А	Піч варила, а я солила.
> Б	 Не кожен хліб заробляє, а кожен його їсть.
> В	 Хліб і на ноги поставить, і з ніг звалить.
> Г	 Млин меле водою, а чоловік живе їдою.
> 2.	 Пунктуаційну помилку допущено в  реченні
> А	Він спав, а

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 14
> 1.	Прочитайте речення та виконайте завдання. 
> Зараз, на жаль, піде дощ.
> Зараз, на щастя, піде дощ.
> А.	 За допомогою яких слів передано протилежне ставлення до природно-
> го явища?
> Б.	 Чому ці слова виділено комами?
> Вставні слова виражають ставлення мовця до сказаного, а саме: 
> •	 (не)впевненість: може, мабуть, очевидно, здається, звісно, без сум-
> ніву;
> •	 емоційну оцінку: на жаль, як на зло, на лихо, на щастя, на радість;
> •	 джерело інформації: кажуть, по-моєму, вважаю, бачу, на думку … ; 
> •

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 210
> 210
> 2. Частку таки пишемо окремо від того слова, якого вона
> стосується, якщо вона стоїть перед ним. ПОРІВНЯЙМО: таки
> написав – написав-таки.
> ОРФОГРАМА
> Написання часток разом, окремо і з дефісом
> Прочитайте речення. Поясніть написання виділених слів (сполучень слів) 
> окремо, разом або з дефісом. 
> 1. Хай плещуть хвилями пісень мої слова! (Олександр Олесь). 
> 2. А деколи дім здатен уміститися до розмірів валізи (І. Цілик). 
> 3. Отак-бо, друже мій великий, усе минуле ожива (А. Малиш-
> ко). 4. Сонце

## Що, де, коли — двоє облич (Two Faces)

> **Source:** unknown, Grade 5
> **Score:** 0.50
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
> спонука

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 239
> Уяви, що в тебе з’явився підписник, із яким ти не зна

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Складне речення (Complex Sentences)` (~300 words)
- `## Що, де, коли — двоє облич (Two Faces)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary

**Required:** що (that — conjunction), де (where — conjunction), коли (when — conjunction), знати (to know), думати (to think), казати (to say/tell)
**Recommended:** сказати (to say — perfective), бачити (to see), чути (to hear), розуміти (to understand), речення (sentence, n), головне (main — as in main clause)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*

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
