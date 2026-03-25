# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **44: Linking Ideas** (A1, A1.7 [Communication]).

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
module: a1-044
level: A1
sequence: 44
slug: linking-ideas
version: '1.1'
title: Linking Ideas
subtitle: І, а, але, бо — connecting your thoughts
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Use coordinating conjunctions і, та, а, але to connect clauses
- Express reasons with бо and тому що
- Build longer, more natural sentences instead of choppy short ones
- Recognize conjunctions in spoken and written Ukrainian
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Making plans: — Ти хочеш каву чи чай? — Каву, бо я дуже втомлений.
    — А я хочу чай, але без цукру. — Ходімо в кафе, і я візьму ще тістечко. — Я теж
    хочу, але я на дієті! Conjunctions: бо (because), а (and/but contrast), але (but),
    і (and).'
  - 'Dialogue 2 — Talking about the day: — Що ти робив сьогодні? — Я працював, а потім
    ходив у магазин. — Я хотів зателефонувати, але ти не відповів. — Вибач, бо телефон
    був без звуку. — Нічого! — Завтра я вільний, і ми можемо зустрітися. Natural use
    of conjunctions in everyday talk.'
- section: Сполучники (Conjunctions)
  words: 300
  points:
  - 'What are conjunctions? Ukrainian term: сполучник (from сполучити — to connect).
    They connect words, phrases, or whole sentences. Without: Я люблю каву. Я люблю
    чай. (choppy) With: Я люблю каву і чай. (natural) Without: Я хочу піти. Я втомлений.
    (disconnected) With: Я хочу піти, бо я втомлений. (connected thought)'
  - 'Grade 4-5 approach: сполучники сурядності (coordinating). These connect EQUAL
    parts: і / та — ''and'' (та = synonym of і, common in writing): мама і тато, хліб
    та масло, Я читаю і пишу. а — ''and'' with contrast or switch: Я люблю каву, а
    ти? Він працює, а вона відпочиває. але — ''but'' (stronger contrast): Я хочу,
    але не можу. Він молодий, але розумний.'
- section: Бо і тому що (Because)
  words: 300
  points:
  - 'Two ways to say ''because'': бо — short, common in speech: Я не йду, бо я хворий.
    тому що — longer, common in writing: Я не йду, тому що я хворий. Both are correct.
    Both are Ukrainian. бо is NOT informal or wrong. Comma rule: always put a comma
    before бо and тому що. Я втомлений, бо багато працював. Ми не гуляємо, тому що
    йде дощ.'
  - 'Building reasons: Чому? (Why?) → Бо / Тому що... — Чому ти вчиш українську? —
    Бо я люблю Україну. — Чому ти не їси? — Тому що я не голодний. — Чому ви тут?
    — Бо ми чекаємо друга. Бо answers the question Чому? — this is how Ukrainians
    explain things.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Conjunction quick reference: | Conjunction | Meaning | Example | | і / та | and
    | Я їм хліб і п''ю воду. | | а | and (contrast) | Я читаю, а він пише. | | але
    | but | Я хочу, але не можу. | | бо | because | Я не йду, бо хворий. | | тому
    що | because | Я не йду, тому що хворий. | Comma rules: always before а, але,
    бо, тому що. Before і — only when connecting two full sentences. Self-check: Connect
    these pairs with the right conjunction: Я люблю каву. Я не люблю чай. → Я люблю
    каву, а/але...'
vocabulary_hints:
  required:
  - і (and)
  - та (and — synonym of і)
  - а (and/but — contrast)
  - але (but)
  - бо (because)
  - тому що (because — longer form)
  recommended:
  - чому (why)
  - тому (therefore/that's why)
  - також (also)
  - теж (also — colloquial)
  - або (or)
  - чи (or — in questions)
activity_hints:
- type: fill-in
  focus: 'Choose: і, а, але, бо — Я хочу ___ не можу. Він працює, ___ вона відпочиває.'
  items: 10
- type: quiz
  focus: Which conjunction? Я не йду, ___ хворий. (і / а / бо)
  items: 8
- type: fill-in
  focus: 'Connect with бо/тому що: Я вчу українську, ___.'
  items: 6
- type: group-sort
  focus: 'Sort: і/та (addition) vs а/але (contrast) vs бо/тому що (reason)'
  items: 10
connects_to:
- a1-045 (When and Where)
prerequisites:
- a1-043 (Please Do This)
grammar:
- 'Coordinating conjunctions: і/та (and), а (contrast), але (but)'
- 'Causal conjunctions: бо, тому що (because)'
- 'Comma rules: before а, але, бо, тому що'
register: розмовний
references:
- title: State Standard 2024, §4.3.2
  notes: Basic complex sentences — і, а, але, бо.
- title: 'Grade 4-5 textbook: Сполучники (Заболотний)'
  notes: 'Coordinating conjunctions: сполучники сурядності.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Linking Ideas
**Module:** linking-ideas | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 217
> Шукаємо відповіді на запитання:
> 1   Які є види спілкування?
> 2   Яке спілкування називають віртуальним, а яке — 
> живим?
> 3   Які переваги й недоліки віртуального спілкування?
> Відповідно до поставлених запитань сформулюйте особисті 
> цілі.
> Віртуàльним називають спілкування, що відбувається 
> через засоби масової комунікації — телефон, смарт-
> фон, планшет, комп’ютер, інтернет. Головними озна-
> ками живого спілкування є реальні умови й безпосе-
> редній контакт зі співрозмовником.
> Пам’ятайте: жодні те

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 243
> 592   Згрупуйте приклади, розташувавши їх у такому порядку: 1)  між-
> особистісне спілкування; 2)  групове спілкування; 3)  масове 
> спілкування. Вибір обґрунтуйте.
> Я вдома з братом; кандидат у депутати на зібранні з вибор-
> цями; тренер і спортсмени на тренуванні; оратор на урочис-
> тому зібранні; моя сестра в кав’ярні з подругою; пасажири 
> в транспорті і водій; бабуся і лікар у реєстратурі поліклініки; 
> мама в чаті з мешканцями нашого будинку; конферансьє 
> на концерті; екскурсовод і група тури

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
> 203
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
> Види речень за метою висловлення
> Вправа 330
> 1. Прочитайте речення .
> Інформація про екскурсію в чаті. 
> Інформація про екскурсію в чаті? 
> Будь ласка, викладіть інформацію про екскурсію в чат. 
> 2. Висловте свої думки: чим відрізняються ці речення одне від одного?
> 3. Згадайте і розкажіть, як називаються такі види речень . 
> Ви вже знаєте, що ми спілкуємося реченнями . Іноді ми хочемо 
> просто передати інформацію, деколи нам тре

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 240
> УСНЕ І ПИСЬМОВЕ СПІЛКУВАННЯ. 
> ЕМОЦІЙНИЙ СТАН СПІВРОЗМОВНИКІВ
> § 96
> Зміст моїх емоцій
> Слово дня: нèкнути, осорóжний, натхнåнний.
> Пригадуємо:
> 1   Які є види спілкування?
> 2   Коли спілкування приносить задоволення?
> 3   Як стати бажаними співрозмовниками / спів розмов -
> ницями?
> Шукаємо відповіді на запитання:
> 1   Які особливості й переваги усного та письмового 
> спілкування?
> 2   Яку роль у спілкуванні відіграють емоції?
> 3   Навіщо розуміти свої та чужі емоції?
> Відповідно до поставлених запитань ви

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 263
> 263
> ТЕМА 15. СТВОРЕННЯ ТА РОЗІГРУВАННЯ
> ДІАЛОГІВ
> ПРИГАДАЙМО. Чим діалогічне мовлення відрізняється від монологічного?
> І. Поміркуйте, що є запорукою успішної комунікації.
> ІІ. Прочитайте й виправте допущені помилки (усно). 
> 1. Велике дякую! 2. Вибачте мене. 3. Перепрошую, винува-
> тий. 4. Вибачаюся. 5. Виказую свою вдячність. 6. Сьогоднішній
> день. 7. Щасливого путі!
> ПОПРАЦЮЙТЕ В ПАРАХ. Складіть і розіграйте за особами діалог (7–8 реп-
> лік) відповідно до запропонованої ситуації спілкування, дотри

## Сполучники (Conjunctions)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 233
> Відомості із синтаксису й пунктуації.  Складне речення
> Частини складного речення можуть бути поєднані лише інтона-
> ційно або ж за допомогою інтонації та сполучників чи сполучних 
> слів.  Залежно від способу зв’язку між частинами складного речення 
> визначають його типи: складні безсполучникові та сполучнико-
> ві речення.  Порівняйте:
> Складні  
> безсполучникові речення
> Складні  
> сполучникові речення
> Уявіть: у  вас з’явився 
> собака найкращої породи 
> вартістю в  кілька тисяч 
> доларів.
> Уявіть, що у

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 176
> 1.	Прочитайте сполуки слів і виконайте завдання. 
> Ми читаємо; хто-небудь запитає; ніхто не відмовить; твоє навчання.
> А.	 З’ясуйте, у якій сполуці слів займенник указує на особу, у якій — на відсут-
> ність осіб, у якій — на належність особі, у якій — на невизначеність особи. 
> Б.	 З поданої нижче таблиці доберіть назви, які відповідають кожному із цих 
> займенників.
> За значенням займенники поділяють на розряди.
> Розряди займенників
> №
> Розряди
> Значення
> Займенники
> 1
> Особові
> особа, предмети, явища
> я,

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> § 32  Сполучники сурядности й підрядности  
> 195
> § 32  Сполучники сурядности й  підрядности
> Вправа 271
> 1  Прочитайте повідомлення в  чаті, віднайдіть загублені сполучники (за по-
> треби скористайтеся довідкою) 
> Степан
> Пані Галина
> Микола
> Вікторія
> Ми всі старалися, … все вдалося! 
> Круто!!!
> Неймовірно вами пишаюся! Перший крок 
> зроблено, … успіху на наступному етапі!
> Доброго дня! Надійшли результати конкурсу: ми 
> перемогли! … було непросто, … ми впоралися 
> разом! Щиро вітаю всіх нас!
> Миколо, ти справ

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 190
> Відомості із синтаксису й пунктуації.  Словосполучення
> який?
> що?
> як?
> м’яч
> футбольний
> іду
> швидко
> читати
> книжку
> Словосполученням називаємо поєднання повнозначних слів, 
> одне з  яких головне, а  друге залежне.  Наприклад:
> Слова у словосполученні поєднуються граматично, тобто за до-
> помогою закінчень і службових слів, наприклад: м’яч (який?) фут-
> больний, форма (яка?) футбольна, поле (яке?) футбольне, гра-
> ти (у що?) у  футбол.  Неправильна побудова словосполучень 
> зумовлює появу граматичних пом

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 66
> 1.	Розгляньте зображення та виконайте завдання.
> Слово, що має два або більше коренів, називаємо складним: відеофайл, 
> темноволосий. 
> Частини складних слів можуть бути поєднані за допомогою сполучних 
> голосних [о] та [е] (на письмі їх позначаємо буквами о, е, є): теплохід, 
> землекоп, зброєносець.
> Сполучний голосний [о] — буква о
> прикметник + основа
> жовтий + рот → жовторотий, 
> синій + крило → синьокрилий
> іменник або займенник з 
> основою на твердий приголо­с­
> ний + основа 
> ліс + степ → лісостеп,

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 172
> 2.	 «Лінгвістичне спостереження». Яка роль сполучників кожної групи? 
> 1.	Прочитайте речення та виконайте завдання.
> Молоде орля, та вище старого літає (нар. тв.).
> Я хочу, щоб кожен українець був орлом (О. Кобилянська).
> А.	 У якому реченні сполучник має значення протиставлення? 
> Б.	 Який із виділених сполучників указує на з’ясування обставини?
> Для поєднання однорідних членів речення та рівноправних частин 
> складного речення послуговуємося сполучниками сурядності: Скрізь 
> добре, а вдома найліпш

## Бо і тому що (Because)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 8
> У цьому розділі ми поговоримо про таке: 
>  Для чого нам потрібна мова та чому її варто вивчати?
>  Чому мову називають основним засобом спілкування?
>  Чому українцям важливо розмовляти 
> українською  мовою?
> ВСТУП. 
> УКРАЇНСЬКА  МОВА  В  ЖИТТІ  УКРАЇНЦІВ

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 4
> Дорогі шестикласники та шестикласниці!
> Ви здіймаєтеся ще на один щабель у здобуванні освіти. Перше, 
> що необхідно засвоїти, — це те, що українська мова — не просто 
> шкільний предмет, це скарб українського народу, його ознака, 
> його пам’ять і сила, його кордон і зброя. Мову потрібно вивчати 
> не заради іспитів, не лише для спілкування, а передусім для ствер-
> дження себе як частинки української нації

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Сполучники (Conjunctions)` (~300 words)
- `## Бо і тому що (Because)` (~300 words)
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

**Required:** і (and), та (and — synonym of і), а (and/but — contrast), але (but), бо (because), тому що (because — longer form)
**Recommended:** чому (why), тому (therefore/that's why), також (also), теж (also — colloquial), або (or), чи (or — in questions)

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
