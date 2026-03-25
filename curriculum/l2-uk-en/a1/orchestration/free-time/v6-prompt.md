# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **26: Free Time** (A1, A1.4 [Time and Nature]).

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
module: a1-026
level: A1
sequence: 26
slug: free-time
version: '1.2'
title: Free Time
subtitle: Хобі, спорт, музика — what you do for fun
focus: communication
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Talk about hobbies, sports, and entertainment using learned verb patterns
- Invite someone to an activity using Ходімо! / Давай!
- Express frequency (часто, іноді, рідко, ніколи)
- Combine all A1.4 skills: time + day + weather + activities
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Weekend plans: — Що ти робиш у вихідні? — Зазвичай я гуляю і читаю.
    — Ходімо в кіно в суботу! — Добре! О котрій? — О п''ятій. — Чудово! Invitation
    pattern + time + day.'
  - 'Dialogue 2 — Talking about hobbies: — Ти любиш спорт? — Так, я граю у футбол.
    — Як часто? — Двічі на тиждень, у вівторок і четвер. — А ще? — Іноді слухаю музику
    і малюю. Frequency + hobby vocabulary.'
- section: Хобі і спорт (Hobbies and Sports)
  words: 300
  points:
  - 'Hobby vocabulary (extending M15 люблю + infinitive): грати у футбол / баскетбол
    / теніс (to play football/basketball/tennis) грати на гітарі / піаніно (to play
    guitar/piano — ''на'' + instrument as chunk) слухати музику (to listen to music)
    дивитися фільми / серіали (to watch movies/series) малювати (to draw), фотографувати
    (to take photos)'
  - 'Entertainment and culture: ходити в кіно (to go to the cinema) ходити в театр
    (to go to the theater) ходити на концерт (to go to a concert) ходити в музей (to
    go to a museum) Note: ходити + в/на is a chunk — the case grammar comes in A1.5.'
- section: Як часто? (How Often?)
  words: 300
  points:
  - 'Frequency adverbs: завжди (always), зазвичай (usually), часто (often), іноді
    / інколи (sometimes), рідко (rarely), ніколи (never). Word order: frequency adverb
    usually before the verb: Я часто гуляю. Я іноді читаю. Я ніколи не працюю у неділю.
    Ніколи requires не (double negation — review M19).'
  - 'Frequency expressions with numbers: раз на тиждень (once a week), двічі на тиждень
    (twice a week), тричі на тиждень (three times a week), кожен день (every day).
    Я граю у футбол двічі на тиждень. Я ходжу в кіно раз на місяць.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Free time communication: Hobbies: Я люблю + infinitive. Я граю у/на... Invitations:
    Ходімо! Давай! (Let''s go! Let''s!) Frequency: завжди, часто, іноді, рідко, ніколи.
    Self-check: Name 3 hobbies. How often do you do each? Invite a friend to do something
    this weekend.'
vocabulary_hints:
  required:
  - вихідні (weekend, pl)
  - спорт (sport, m)
  - футбол (football, m)
  - кіно (cinema, n — indeclinable)
  - часто (often)
  - іноді (sometimes)
  - рідко (rarely)
  - ходімо (let's go!)
  recommended:
  - завжди (always)
  - зазвичай (usually)
  - ніколи (never)
  - театр (theater, m)
  - концерт (concert, m)
  - музей (museum, m)
  - давай (let's — informal)
  - раз (once/time)
activity_hints:
- type: match-up
  focus: Match the verb to the logical noun (hobbies)
  pairs:
  - грати ↔ у футбол
  - грати ↔ на гітарі
  - слухати ↔ музику
  - дивитися ↔ фільми
  - ходити ↔ в кіно
  - ходити ↔ в театр
  - читати ↔ книгу
  - малювати ↔ картину
- type: fill-in
  focus: Complete the invitations and frequency sentences
  items:
  - Я {ніколи не|завжди|часто} працюю у неділю.
  - Вона грає у теніс двічі {на тиждень|у тиждень|в тиждень}.
  - — {Ходімо|Давай|Ідемо} в кіно у суботу! — Добре!
  - Я люблю спорт, тому {часто|ніколи|рідко} граю у баскетбол.
  - Я не маю часу, тому {рідко|часто|завжди} читаю книги.
  - — Що ти робиш {у вихідні|вихідні|на вихідні}? — Відпочиваю.
- type: fill-in
  focus: Choose the correct preposition for the activity
  items:
  - Він грає {на|у|в} піаніно.
  - Ми граємо {у|на|в} футбол.
  - Я хочу піти {на|в|у} концерт.
  - Вони ходять {в|на|у} театр раз на місяць.
connects_to:
- a1-027 (Checkpoint — Time and Nature)
prerequisites:
- a1-025 (My Day)
grammar:
- 'Frequency adverbs: завжди, часто, іноді, рідко, ніколи'
- Ходімо! / Давай! invitation patterns
- Грати у + sport, грати на + instrument (preposition chunks)
register: розмовний
references:
- title: ULP — various episodes on hobbies and sports
  notes: Conversational patterns for discussing free time.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Free Time
**Module:** free-time | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 51
> Прочитай приховане речення.  
> Як ти його розумієш?
> ни
> пла
> за
> сльо
> тень
> че
> ми
> жов
> хо
> ми
> лод
> 	 	
> 3   Запишіть сполучення слів, у яких слова вжито у прямому 
> і переносному значеннях. Поясніть значення слів.
> Наведіть свої 
> приклади.
> Пряме значення
> Переносне значення  
> Танцює дитина — танцює листя.
> Залізне здоров’я — залізні двері.
> Чистий рушник — чиста совість.
> 	 	
>   Складіть і запишіть речення з кожним сполученням слів.
> Навчаюся доречно вживати слова в мовленні 
> Сумує (верба, дитина), залізний

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 23
> 1. Прочитай цікаву інформацію про французів. Розкажи,
> як  ти  ставишся  до  свого  харчування.
> Сніданок, обід, вечеря, їжа та всі пов’язані з ними 
> слова — священні для французів. Конкурувати
> з ними можуть тільки регбі, велосипед, футбол. 
> Про харчування дбають у французьких шко-
> лах. Учні молодших класів мають велику перерву,
> під час якої можуть піти додому, щоб пообідати.
> ДОСЛІДЖУЮ ФРАЗЕОЛОГІЗМИ
> ДОСЛІДЖУЮ ФРАЗЕОЛОГІЗМИ
> 2. Прочитай, що дізналася Читалочка про вподобання 
> французьких  друзів.

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 28
> 61
>   Пригадайте і запишіть за відведений час якомога більше запо-
> зичених слів, що мають у нашій мові відповідники. Яким із них 
> варто віддавати перевагу?
> 62
>   Прочитайте слова. Виберіть будь-яку пару слів і складіть із ними 
> діалог, в основі якого має бути пропозиція одного зі співрозмов-
> ників і згода іншого.
> Глосарій — словничок, дисонанс — розлад, голкіпер — 
> воротар, кутюр’є — кравець.
> 63   І   Не знаючи вас, ми ось так зобразили світ ваших захоплень. 
> Розгляньте малюнок і скажіть, чи зб

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 33
> Пам’ятайте 
> про культуру 
> спілкування.
> 	 	
> 3   Розгляньте світлину. Поставте запитання за її змістом і запишіть 
> відповіді.
> 	 	
> 4   Побудуйте речення за поданими схемами і запишіть.
> .
> .
> ?
> 	 	
> 5   Уяви себе журналістом (журналісткою), 
> що цікавиться, як ваш клас готується до 
> Свята осені. Продумай запитання і можливі 
> відповіді. Розіграйте сценку в класі. 
> Кличуть нас ліси, поля, сади
> дозбирати осені плоди.
> Із дерев спадає листя жовте.
> То землею ходить місяць ? .
>   Укажи, скільки тут є реч

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 118
> 1. Постав питання до виділених слів і запиши словосполу-
> чення.
> 3. Розгляньте у групі однокласників/
> однокласниць герб країни, у якій 
> віртуально побувала Родзинка.
> Чи здогадуєтеся, як називається 
> ця країна? Знайдіть її на карті.
> 3
> працюють (…?) дружно 
> повертає (…?) вліво
> стоїть (…?) попереду  
> цвітуть (…?) навесні
> 2. Прочитай прислів’я. Поясни, як ти їх розумієш. Випиши
> прислівники з дієсловами, з якими вони пов’язані.
> 1. Чесне діло роби сміло. 2. Хто йде вперед, за тим 
> і перемога. 3. Сп

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 217
> ТЕМА 2. ПРАВИЛА СПІЛКУВАННЯ.  
> МОНОЛОГІЧНЕ ТА ДІАЛОГІЧНЕ СПІЛКУВАННЯ.  
> СКЛАДАННЯ ДІАЛОГІВ
> 525.	Ознайомтеся з основними правилами спілкування. Поясніть, чому 
> їх потрібно дотримуватися.
> Правила спілкування
>  Бути ввічливими, привітними й доброзичливими.
>  Уважно, не перебиваючи, слухати співрозмовника.
>  Заохочувати співрозмовника до висловлення власної 
> думки.
>  Уміти доброзичливо висловити незгоду з позицією 
> співрозмовника.
>  Не розмовляти без потреби голосно.
>  Не використовувати груби

## Хобі і спорт (Hobbies and Sports)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 8   Упізнайте види спорту і запишіть слово до кожного малюнка. 
> Зробіть висновок, чому утворені іменники є назвами неістот.
> 	 	
> 7   Запишіть слова і допишіть іменники — 
> назви професій людей, пов’язані з цими 
> словами.
> актор
> банкір
> водій
> гончар
>  На яке питання 
> відповідають ці 
> слова? 
> салон
> зачіска
> ножиці
> стрижка
> фен
> кермо
> фари
> сигнал
> навігатор
> мотор
> монітор
> програма
> клавіатура
> сайт
> скайп
> 	
>   Зробіть висновок, чому дописані іменники є назвами істот.
> 	
>   Від записаних назв видів спорту утвор

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 89
> 4. Склади й запиши два речення: із займенниками
> 1-ої  особи  множини  і  2-ої  особи  однини.
> 5. Спиши текст. Встав зазначені в дужках займенники. 
> 6. Прочитай повідомлення Ґаджика. Який недолік має цей 
> текст? Виправ його і запиши.
> 4
> (1 ос., мн.) зустрілися на стадіоні. (1 ос., одн.) при-
> їхав на велосипеді. (2 ос., одн.) — на роликах. Там 
> були наші друзі. (3 ос., мн.) грали в бадмінтон. 
> У Швеції всі люблять спорт. Спорт 
> популярний серед людей різного віку. 
> Спортом займаються цілими сім’

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 104
> 249.	СИТУАЦІЯ. Уявіть, що вчитель фізкультури попросив вас по-
> відомити (усно) про проведення шкільних олімпійських ігор. Прочи- 
> тайте вголос оголошення, правильно вимовляючи назви видів спор-
> ту. У яких назвах уподібнюємо приголосні? 
> У наступну суботу на стадіоні відбудеться відкриття 
> шкільних олімпійських ігор. 
> До програми змагань включено такі види спорту: 
> легка атлетика, 	
> важка атлетика, 	
> вільна боротьба, 	
>  
> стрибки на батуті,
> футбол,
> гандбол.
> 250.	Запишіть слова фонетичною транс

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 117
> 	
>   Випишіть іменники в однині. Поставте їх у формі множини і запишіть. 
> Які іменники не вдалося поставити у формі множини? Зробіть 
> висновок.
> 	 	
> 9   Прочитайте початок тексту. Доповніть його відомою вам 
> інформацією (усно).
> 	 	
> 8   Запишіть іменники у два стовпчики. Доведіть, що вони вжива-
> ються в одній числовій формі.
> Гра в шахи поєднує науку, мистецтво і спорт. Навчає 
> зосереджувати увагу, логічно мислити і діяти за планом. 
> Окуляри, бадилля, граблі, борошно, гроші, павутиння, 
> жіноц

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 88
> 2. Прочитай, як називаються підкреслені займенники.
> у бугая на спині. Бугай почав вистрибувати й ви-
> хилятися на всі боки, щоб скинути Пеппі. Але вона 
> вперлася п’ятами бугаєві в боки й не падала. Бугай 
> ревів, бігав по всьому лузі, аж у бугая пара йшла
> з ніздрів. А Пеппі сміялася і підганяла бугая
> криком... 
> За Астрід Ліндґрен (переклад Ольги Сенюк)
> 1. Спиши текст. Підкресли займенники. Усно постав до них 
> питання. Яку частину мови вони замінюють?
> Ми займаємося спортом. Я граю у волейбол, 
> а

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 28
> 61
>   Пригадайте і запишіть за відведений час якомога більше запо-
> зичених слів, що мають у нашій мові відповідники. Яким із них 
> варто віддавати перевагу?
> 62
>   Прочитайте слова. Виберіть будь-яку пару слів і складіть із ними 
> діалог, в основі якого має бути пропозиція одного зі співрозмов-
> ників і згода іншого.
> Глосарій — словничок, дисонанс — розлад, голкіпер — 
> воротар, кутюр’є — кравець.
> 63   І   Не знаючи вас, ми ось так зобразили світ ваших захоплень. 
> Розгляньте малюнок і скажіть, чи зб

## Як часто? (How Often?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 57
> Зàгадка — це цікава задача. Вона має форму питаль-
> ного або розповідного речення, у якому слова часто
> римуються. У загадках зображається не сам предмет, іс-
> тота або явище, а подібний до них за суттєвими ознаками.
> ПРО НЕБО, ЗЕМЛЮ, ЯВИЩА ПРИРОДИ
> y Торох, торох, розсипався горох, почало світати, 
> нема що збирати.
> y Що світить по всьому світі?
> y Поле не міряне, вівці не лічені, пастух рогатий.
> y Усі його люблять, усі його чекають, а хто поди-
> виться — кожен скривиться.
> y Що у світі найбагатше?
> y

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Зразок
> Приїжджала (коли?) влітку.
> ОС*Я/ К'/ Ь<ЬС’£$Ю /
> Спілкуючись, завжди

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Хобі і спорт (Hobbies and Sports)` (~300 words)
- `## Як часто? (How Often?)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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

GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):
Time expressions, days, months, weather, daily routines.

ALLOWED:
- All present tense (from A1.3)
- Time expressions as chunks (О першій, У понеділок)
- Sequence adverbs (спочатку, потім, нарешті)
- Impersonal weather constructions (Сьогодні холодно)

BANNED: Past/future tense, case endings (time chunks only),
participles, passive voice, complex subordination

### Vocabulary

**Required:** вихідні (weekend, pl), спорт (sport, m), футбол (football, m), кіно (cinema, n — indeclinable), часто (often), іноді (sometimes), рідко (rarely), ходімо (let's go!)
**Recommended:** завжди (always), зазвичай (usually), ніколи (never), театр (theater, m), концерт (concert, m), музей (museum, m), давай (let's — informal), раз (once/time)

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
