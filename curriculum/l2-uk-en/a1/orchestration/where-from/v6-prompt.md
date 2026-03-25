# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **34: Where From?** (A1, A1.5 [Places]).

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
module: a1-034
level: A1
sequence: 34
slug: where-from
version: '1.2'
title: Where From?
subtitle: Звідки ти? Я з України — origins and directions
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Ask and answer Звідки? (Where from?) using з/із + country/city
- Name Ukrainian cities and common countries
- Complete the location trio: Де? / Куди? / Звідки?
- Talk about origins, nationality, and travel history
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone (extending M05, ULP Ep4): — Звідки ти? — Я з України,
    з Києва. А ти? — Я з Канади, із Торонто. — Давно тут? — Ні, я приїхав місяць тому.
    Звідки? pattern with countries and cities.'
  - 'Dialogue 2 — Coming from somewhere: — Звідки ти йдеш? — Я йду з роботи. — А Олена?
    — Вона йде зі школи. — Куди вона йде? — Додому. Direction FROM (з + genitive chunk)
    vs TO (в/на + accusative).'
- section: Звідки? (Where From?)
  words: 300
  points:
  - 'Three direction questions complete: Де ти? — В Україні. (locative — where you
    ARE) Куди ти їдеш? — В Україну. (accusative — where you''re GOING) Звідки ти?
    — З України. (genitive — where you''re FROM) At A1: learn з + country/city as
    chunks. Genitive grammar = A2.'
  - 'Pattern: з/із/зі + genitive (memorized forms): з України, з Києва, зі Львова,
    з Одеси, з Харкова. з Канади, зі США (зі Штатів), з Англії, з Німеччини, з Польщі.
    з роботи, зі школи, з магазину, з банку. Note: euphony rules from M28 apply: з/із/зі.'
- section: Країни і міста (Countries and Cities)
  words: 300
  points:
  - 'Ukrainian cities: Київ (Kyiv), Львів (Lviv), Одеса (Odesa), Харків (Kharkiv),
    Дніпро (Dnipro), Запоріжжя (Zaporizhzhia). Countries (common for learners): Україна,
    Канада, США, Англія, Німеччина, Польща, Франція, Італія, Японія.'
  - 'Nationality and language links: Я з України → Я українець/українка → Я говорю
    українською. Review from M05: Мене звати..., Я з..., Я говорю... New: Я живу в
    Києві, але я зі Львова. (current location vs origin)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three location questions: Де? → в/на + locative (В Україні) Куди? → в/на + accusative
    (В Україну) Звідки? → з/із/зі + genitive chunk (З України) Self-check: Where are
    you from? Where do you live now? Where are you going after this lesson?'
vocabulary_hints:
  required:
  - звідки (where from)
  - з/із/зі (from — + genitive chunk)
  - Україна (Ukraine)
  - Київ (Kyiv)
  - Львів (Lviv)
  - Канада (Canada)
  recommended:
  - Одеса (Odesa)
  - Харків (Kharkiv)
  - США (USA)
  - Англія (England)
  - Німеччина (Germany)
  - Польща (Poland)
  - додому (home — direction)
activity_hints:
- type: fill-in
  focus: Answer Звідки? using з/із/зі + memorized genitive chunks
  items: 8
  blanks:
  - Звідки ти? — Я {з України}.
  - Вона {з Канади}.
  - Ми {з Києва}, а ви?
  - Джон {зі США}.
  - Мій друг {з Німеччини}.
  - Я {зі Львова}.
  - Вони {з Англії}.
  - Олена {з Одеси}.
- type: group-sort
  focus: Categorize phrases into Де? (Locative), Куди? (Accusative), Звідки? (Genitive)
  items: 9
  groups:
  - name: Де? (Where?)
    items:
    - в Україні
    - в Києві
    - на роботі
  - name: Куди? (Where to?)
    items:
    - в Україну
    - в Київ
    - на роботу
  - name: Звідки? (Where from?)
    items:
    - з України
    - з Києва
    - з роботи
- type: quiz
  focus: Choose correct preposition (в/на/з) for location/direction
  items: 8
  questions:
  - Я йду... роботи. (з / на / в)
  - Вона йде... школу. (в / на / зі)
  - Ми зараз... Україні. (в / з / на)
  - Я їду... Канаду. (в / з / на)
  - Він... Німеччини. (з / в / на)
  - Вони... Львові. (у / зі / на)
  - Я йду... магазину. (з / в / на)
  - Олена... школи. (зі / в / на)
- type: fill-in
  focus: Contrast current location (в/на) and origin (з/із)
  items: 6
  blanks:
  - Я живу {в Києві}, але я {зі Львова}.
  - Вона живе {в Канаді}, але вона {з України}.
  - Ми зараз {в Англії}, але ми {з Польщі}.
  - Він живе {в Одесі}, але він {з Харкова}.
  - Я {з Німеччини}, але зараз я {в Україні}.
  - Ти {зі США}, але живеш {у Києві}.
connects_to:
- a1-035 (Checkpoint — Places)
prerequisites:
- a1-033 (Around the City)
grammar:
- Звідки? + з/із/зі + genitive (memorized chunks)
- 'Location trio: Де? (M.в.) / Куди? (Зн.в.) / Звідки? (Р.в. chunk)'
- Country/city names in three case forms
register: розмовний
references:
- title: ULP Season 1, Episode 4
  url: https://www.ukrainianlessons.com/episode4/
  notes: Where are you from? — nationalities and countries.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Where From?
**Module:** where-from | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Зразок
> Приїжджала (коли?) влітку.
> ОС*Я/ К'/ Ь<ЬС’£$Ю /
> Спілкуючись, завжди пам’ятайте про інтонацію. Так, 
> слово дякую можна вимовити м ’яко або грубо, тепло 
> чи холодно, сором’язливо або нахабно. Якщо це слово 
> прозвучить іронічно, глузливо чи єхидно, то така інто­
> нація принизить людину.
> •  Випишіть із рубрики прислівники.
> 388. Прочитайте фразеологізми.
> 1. Одна нога тут, а друга там. 2. Ніс у ніс. 3. До останньої 
> нитки. 4. Голкою ніде ткнути. 5. Бурмотіти під носа. 6. На 
> одній ноті. 7. На вл

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 19
> 37
>   Прочитайте речення. Які слова в них образливі для співрозмов-
> ника? Чому їх потрібно уникати? Доберіть синоніми до цих слів 
> і замініть їх. Наскільки важливо ретельно добирати слово із си-
> нонімічного ряду?
> 1. Чого це ти надувся, як сич на мороз? (С. Талан). 2. Гей, 
> новенький! Ти, кажуть, петраєш у компах? (В. Бердт). 3. Чого 
> ти приперся? Я тобі сказала коли прийти? (С. Талан). 4. Ну 
> чого ти тут стовбичиш і мовчиш? (С. Гридін). 5. Але хто бовк-
> нув дідові про нашу вигадку? (В. Кохан).

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 282
> ВІД СМІШНОГО ДО ВЕЛИКОГО
> ÇÀÌÎÐÑÜÊ² ÃÎÑÒ²
> ГУМОРЕСКА
> Прилетіли в Україну
> Гості із Канади.
> Мандруючи по столиці,
> Зайшли до міськради.
> Біля входу запитали
> Міліціонера:
> – Чи потрапити ми можем
> На прийом до мера? –
> Козирнув сержант бадьоро.
> – Голови немає.
> Він якраз нові будинки
> В Дарниці приймає.
> Здивуванням засвітились
> Очі у туриста.
> – Ваша мова бездоганна
> І вимова чиста.
> А у нас там, у Канаді,
> Галасують знову,
> Що у Києві забули
> Українську мову.
> Козирнув сержант і вдруге.
> – Не дивуйтесь, – каже.

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 131
> 315.		Прочитай правила ввічливого спілкування, уставляючи 
> пропущені прислівники. Звертай увагу на колір.
> ... й ... вітайся та усміхайся
> доброзичливо, щиро
> ... й ... стався до людей
> тактовно, приязно
> ... та ... слухай співрозмовника
> уважно, вдумливо
> говори ... й ...
> небагато, виразно
> запитуй ... й ...
> спокійно, делікатно
> Перебуваючи в оточенні малознайомих людей, завжди:
> 	 Запиши правила ввічливого спілкування. Чи дотримуєшся ти їх? 
> 316.		Прочитай текст, самостійно добираючи прислівники від

> **Source:** unknown, Grade 5
> **Score:** 0.33
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
> А Створіть своє родинне дерево через

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 26
> 1.	Прочитайте діалог і виконайте завдання.
> — Як довго ще чекати на подорож до моря?
> — Неділю? 
> — Як? Один день залишився? Я не встигну зібратися! 
> — Не один, а сім днів! Так що встигнеш…
> А.	 Через яке слово сталося непорозуміння?
> Б.	 Яка причина цього непорозуміння?
> До лексичних помилок належать: 
> •	 тавтологія — уживання того самого слова або спільнокореневих 
> слів в одному чи в сусідніх реченнях: Використання екологічно чис-
> тих продуктів корисне для здоров’я;
> •	 калькування — слово або вис

## Звідки? (Where From?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 111
> 236. Спиши речення. Підкресли займенник 2-ї особи та 
> визнач, у якому відмінку його вжито.
> Україно! Доки жити буду, доти відкриватиму тебе.
> Василь Симоненко
> 237. 1. Прочитай текст. 
> Я часто буваю на станції юних техніків. Там у нас багато 
> цікавих занять. Найбільше мені подобається працювати 
> в майстерні. А головне — разом зі мною станцію юних 
> техніків відвідують мої друзі.
> 2. Усно постав питання до займенників. Визнач їх особу, 
> число та відмінок.
> 3. Перебудуй текст так, щоб розповідь вела

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 81
>  § 34–35.  Позначення  звуків  мовлення  на  письмі.  Алфавіт
> 3.	Розташуйте й запишіть назви обласних центрів України за алфавітом. 
> У дужках додайте інформацію про напрямок руху до кожного міста, 
> якщо виїжджати з вашого населеного пункту (за зразком). 
> Напрямки руху: 
> •	 західний;
> •	 східний;
> •	 південний; 
> •	 північний; 
> •	 південно-західний; 
> •	 південно-східний; 
> •	 північно-західний, 
> •	 північно-східний.
> Зразок. Мій населений пункт — м. Київ. 
> Вінниця (південно-західний);
> Дніпро (півде

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Що для тебе 
> означає бути 
> патріотом 
> України?
> Розділ  4
> Навчальний маршрут розділу

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> З тобою розлука — гірка моя мука,
> Печаль журавля без гнізда в чужині.
> Моя Україно, білявко-хатино,
> З твойого вікна світить доля мені.
> •  Випишіть із вірша строфу, у якій одне з дієслів стоїть у почат­
> ковій формі. Змініть його за особами в теперішньому часі.
> •  Підкреслені дієслова розберіть як частину мови, користую­
> чись схемою розбору на форзаці підручника.
> 366. Прочитайте текст.
> Волелюбна Грузія знаходиться в самому серці Кавказу. 
> Столичне її місто Тбілісі розміщене серед гір. На орлиних 
> в

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 115
> Дайте, будь ласка, три квитки до ... .
> Харків
> Миколаїв
> Канів
> Львів
> Тетіїв
> Чугуїв 
> Фастів
> Бориспіль
> ЗРАЗОК. Дайте, будь ласка, три квитки до Бердичева.
> 280.	І. Спишіть слова, уставляючи на місці пропуску букву е або и. По-
> ясніть орфограми, покликаючись на правила написання е, и в коренях 
> слів та відомості про чергування голосних звуків.
> 1. Вит..рати, вит..рти, вист..лю, вист..лати. 2. Сп..кти, 
> пол..тіти, поч..пити. 
> ІІ. Прокоментуйте чергування звуків у словах. 
> Можу – мігши, вела – вівши,

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> Розділ 5. Іменник 
> 132
> Вправа 269
> 1. Прочитайте текст.
> Чи знаєте ви, звідки походять назви українських міст 
> і сіл? Нескладно здогадатися, як утворилися назви Івано-
> Франківськ, Хмельницький чи, 
> скажімо, Сковородинівка: вони 
> бережуть пам’ять про відомих 
> людей свого регіону.
> У подібний спосіб утворено 
> й  інші топоніми, наприклад, 
> Київ від імені полянського князя 
> Кия чи Львів на честь князя 
> Лева Даниловича.
> Але це далеко не єдиний 
> спосіб творення назв населених 
> пунктів. Якщо дослідити їхн

## Країни і міста (Countries and Cities)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 77
> Словенія, Албанія, Македонія, Польща, Швейцарія, Чехія. 
> Для цих країн Дунай є рідною річкою, яку люблять і бере-
> жуть (З енциклопедії).
> 	 Випиши назви земель, які прикрашає та напуває Дунай. Під­
> кресли суфікси. Що пишемо в цих суфіксах?
> 188.		Прочитай запитання.
> — Як називають Січ, де жили українські козаки?
> — Як називають сузір’я, за яким орієнтувалися чумаки?
> — Як називають річки, що протікають у горах?
> — Як називають берег моря?
> — Як називають області, центрами яких є міста Вінни-
> ця, К

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 81
>  § 34–35.  Позначення  звуків  мовлення  на  письмі.  Алфавіт
> 3.	Розташуйте й запишіть назви обласних центрів України за алфавітом. 
> У дужках додайте інформацію про напрямок руху до кожного міста, 
> якщо виїжджати з вашого населеного пункту (за зразком). 
> Напрямки руху: 
> •	 західний;
> •	 східний;
> •	 південний; 
> •	 північний; 
> •	 південно-західний; 
> •	 південно-східний; 
> •	 північно-західний, 
> •	 північно-східний.
> Зразок. Мій населений пункт — м. Київ. 
> Вінниця (південно-західний);
> Дніпро (півде

> **Source:** unknown, Grade 6
>

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Звідки? (Where From?)` (~300 words)
- `## Країни і міста (Countries and Cities)` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
participles, passive voice, complex subordination

### Vocabulary

**Required:** звідки (where from), з/із/зі (from — + genitive chunk), Україна (Ukraine), Київ (Kyiv), Львів (Lviv), Канада (Canada)
**Recommended:** Одеса (Odesa), Харків (Kharkiv), США (USA), Англія (England), Німеччина (Germany), Польща (Poland), додому (home — direction)

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
