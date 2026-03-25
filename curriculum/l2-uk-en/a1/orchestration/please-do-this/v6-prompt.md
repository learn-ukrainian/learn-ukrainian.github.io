# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **43: Please Do This** (A1, A1.7 [Communication]).

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
module: a1-043
level: A1
sequence: 43
slug: please-do-this
version: '1.1'
title: Please Do This
subtitle: Читай! Скажіть! Дайте! — asking people to do things
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form imperative mood for 2nd person singular (ти) and plural/formal (ви)
- Give instructions and make requests using будь ласка
- Recognize common classroom and daily-life imperatives
- Distinguish ти-imperatives from ви-imperatives
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — In the classroom: — Відкрийте підручники, будь ласка. Читайте текст.
    — Вибачте, яку сторінку? — Сторінку двадцять три. — Тепер пишіть. Напишіть три
    речення. — Можна запитати? — Так, запитуйте! Classroom imperatives: відкрийте,
    читайте, пишіть, напишіть.'
  - 'Dialogue 2 — Between friends: — Слухай, ходімо в кафе! — Добре, йди, я зараз.
    — Подивись, яка гарна погода! — Так! Сідай тут. — Дай мені меню, будь ласка. —
    Ось, дивись. — Скажи, що ти хочеш? — Я хочу каву. Informal imperatives: слухай,
    подивись, сідай, дай, скажи.'
- section: Наказовий спосіб (The Imperative Mood)
  words: 300
  points:
  - 'Ukrainian Grade 5 term: наказовий спосіб (imperative mood). Used for commands,
    requests, instructions, invitations. Two forms at A1: ти (informal, one person)
    and ви (formal or plural). Будь ласка makes any command polite: Дай! (Give!) →
    Дай, будь ласка. (Please give.) Дайте! (Give! — formal) → Дайте, будь ласка.'
  - 'Not rude — just direct: Ukrainian imperatives are normal in daily speech. Читай!
    is not rude — it''s how teachers, parents, friends talk. Adding будь ласка = polite.
    Adding tone + name = friendly: Олено, прочитай, будь ласка. (Olena, please read.)'
- section: Як утворити? (How to Form It)
  words: 300
  points:
  - 'Ти-form (informal, singular): Group I (-ати): читати → читай, слухати → слухай,
    писати → пиши. Group II (-ити): говорити → говори, дивитися → дивись, ходити →
    ходи. Irregular (common): дати → дай, сказати → скажи, їсти → їж, іти → іди. Pattern:
    stem + ending. Most are short — one or two syllables.'
  - 'Ви-form (formal or plural): Add -те to the ти-form: читай → читайте, слухай →
    слухайте, пиши → пишіть, говори → говоріть, дивись → дивіться, ходи → ходіть,
    дай → дайте, скажи → скажіть, іди → ідіть. Note: some get -іть (not -ить) — stress
    shifts: пиши → пишіть, сиди → сидіть, дивись → дивіться.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Essential imperatives for daily life: | Infinitive | Ти | Ви | Meaning | | читати
    | читай | читайте | read | | писати | пиши | пишіть | write | | слухати | слухай
    | слухайте | listen | | дивитися | дивись | дивіться | look | | говорити | говори
    | говоріть | speak | | іти | іди | ідіть | go | | дати | дай | дайте | give |
    | сказати | скажи | скажіть | say/tell | | сісти | сядь | сядьте | sit down |
    | відкрити | відкрий | відкрийте | open | Self-check: How do you say ''Please
    read'' to your teacher? To your friend?'
vocabulary_hints:
  required:
  - читати (to read)
  - писати (to write)
  - слухати (to listen)
  - дивитися (to look/watch)
  - говорити (to speak)
  - дати (to give)
  - сказати (to say/tell)
  - іти (to go)
  recommended:
  - відкрити (to open)
  - сісти (to sit down)
  - показати (to show)
  - запитати (to ask)
  - підручник (textbook, m)
  - сторінка (page, f)
  - речення (sentence, n)
activity_hints:
- type: fill-in
  focus: 'Form imperative: читати → читай / читайте, писати → пиши / пишіть'
  items: 10
- type: quiz
  focus: 'Choose correct: ___, будь ласка! (дай / даєш / дати)'
  items: 8
- type: group-sort
  focus: 'Sort: ти-forms vs ви-forms (читай vs читайте, дай vs дайте)'
  items: 10
- type: fill-in
  focus: 'Complete: Олено, ___ книжку! Пане Іване, ___ книжку! (дай/дайте)'
  items: 6
connects_to:
- a1-044 (Linking Ideas)
prerequisites:
- a1-042 (Hey, Friend!)
grammar:
- 'Imperative mood (наказовий спосіб): 2nd person ти and ви forms only'
- 'Ти-form: читай, пиши, дай, скажи, іди'
- 'Ви-form: add -те (читайте) or -іть (пишіть, скажіть)'
- Будь ласка for politeness
register: розмовний
references:
- title: State Standard 2024, §4.2.4.2
  notes: Imperative mood — 2nd person only at A1.
- title: 'Grade 5 textbook: Наказовий спосіб (Заболотний)'
  notes: Formation of imperative from verb stem. Ти and ви forms.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Please Do This
**Module:** please-do-this | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 204
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
>  Дайте домашку 
> з математики.
> 15:28
> Я загубила в класі 
> щоденник. Ніхто 
> не бачив?
> 15:39
> На завтра треба 
> готувати поробку?
> 15:53
> Візьміть завтра під-
> ручники з англій-
> ської, буде заміна. 
> 16:21
> Ходімо разом 
> у кіно. 
> р
> 16:42
> Я не знаю, як 
> розв’язати задачу. 
> Допоможіть!!!  
>  
>  
> Д
>  
>  
>  
> 17:36
> Вправа 331
> 1. Прочитайте речення, узяті з чату 
> класу .
> 2. Назвіть спочатку розповідні ре-
> чення, потім питальні та  спону-
> кальн

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 33
> Лексикологiя.  Фразеологiя
> СИТУАЦІЯ. Складіть діалог (6–8 реплік) в офіційно-діловому стилі, 
> можливий в одній з описаних ситуацій (на вибір). Використайте стилістично 
> забарвлені слова.
> ВАРІАНТ А. Ви прийшли записатися до бібліотеки. Повідомте мету свого
> візиту, а також на прохання бібліотекарки – своє прізвище та ім’я, дату 
> народження, місце проживання (для оформлення картки читача). Розпитайте 
> про години роботи закладу, правила користування літературою. 
> ВАРІАНТ Б. Ви зайшли в кабінет за

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> Розділ 7  ЧАСТКА
> 220
> Вправа 304
> 1  Спишіть речення 
> 1) Пропоную піти в кіно чи боулінг. Чи ти не чуєш? 2) І не 
> треба зі мною сперечатися! Іване, розгорни підручник і почи-
> най працювати. 3) Дай, будь ласка, це мені. На вчання — це 
> розвиток. 4) Який зараз урок? Який гарний хлопчик! 5) Що 
> за розумничка! Що за цим поворотом? 6) Кожен візьміть собі 
> води. Ідіть собі з богом!
> 2   Над виділеними словами надпишіть частину мови  Поясніть, як ви її ви-
> значили 
> 3  Поміркуйте, які наміри спілкування за

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 202
> Відомості із синтаксису й пунктуації.  Речення з одним головним членом
> Вправа 328
> Розгляньте світлини на с.  188.  Складіть за ними речення.  Запишіть їх і під-
> кресліть граматичні основи.
> Вправа 329
> Виконайте тест.  У кожному завданні лише один правильний варіант від-
> повіді.
> 1.	 Односкладним є  речення
> А	У двері постукали.
> Б	 У двері хтось постукав.
> В	 У двері постукав Петро.
> Г	 Я почув стук у двері.
> 2.	 Двоскладним є  речення
> А	Лунає пісня.
> Б	 Чути пісню.
> В	 Заспіваймо пісню!
> Г	 Яка чудов

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 3
> Дорогі діти!
> Вітаємо вас — ви продовжуєте вивчати історію! Вашим 
> помічником в осягненні історії України та світу буде цей 
> підручник. Навчальний матеріал підручника поділений на 
> розділи й параграфи, у яких для зручності виділені окремі 
> пункти. Зазвичай на кожному уроці ви будете вивчати один 
> параграф. Він містить навчальний текст, ілюстрації, пояс-
> нення основних понять. Зорієнтуватись у підручнику допо-
> можуть рубрики.
> Цікаві завдання й запитання дозволять вам навчитися 
> розмірковувати, з

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

## Наказовий спосіб (The Imperative Mood)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 42
> Лексикологія.  Омоніми
> щоб бити по  них ногою або словом. Коли ти ко паєш когось 
> ногою, то завдаєш фізичного болю. А  коли дошкуляєш обра-
> зливим словом  — то болю морального. Ви  ж робите боляче, 
> невже не  зрозуміло?
> —  Тю. Вони також нас ображають! Ми тільки для сміху 
> написали сиріткам, які вони боягузи, а  вони почали відгав-
> куватися, наговорюють на  нас казна-що! Ти сама це чита-
> ла, — виправдовувалася Вередунка. Їй не  подобалося, коли її 
> сварили та  не  цінували її вміння вигадува

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> В. Прочитайте текст удруге й докладно його перекажіть (усно).

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> § 11  Наказовий спосіб діє слів  
> 59
> Вправа 84 
>  
> Спишіть речення, утворивши від діє слів у дужках форми наказового способу 
> 1) Так (сказати), ви хочете стати справжніми богатирями? 
> (Є. Кравченко). 2) (Слухати), добрий чоловіче, коли вже дове­
> лося нам іти разом, (зробити) так (Нар. тв.). 3) Котигорошок 
> поклонився батькові в ноги й каже: «Батечку, (піти) до кова­
> ля, (викувати) мені сильну залізну булаву» (А.  Лотоцький). 
> 4) (Приїхати) самі, (знайти) мене, і я вас обов’язково з ними 
> познайом

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> Розділ 1. МИСТЕЦЬКИЙ СПАДОК НАЩАДКАМ
> 46
> За­сіб  чи­тан­ня
> З­на­чен­ня­
> ­Темп чи­тан­ня
> Си­ла го­ло­су
> Тембр зву­ка
> Дик­ція
> Па­у­за
> Ін­то­на­ці­я
> ш­вид­кість чи­тан­ня — рів­на, упо­віль­не­на чи прис­ко­
> ре­на (за­леж­но від зміс­ту)
> ­мак­си­маль­ний сту­пінь ви­я­ву го­ло­су, йо­го нап­ру­же­
> ність (най­час­ті­ше по­си­лю­ють го­лос у реп­лі­ках, особ­
> ли­во в ок­лич­них ре­чен­нях)
> ха­рак­тер­не за­бар­влен­ня, зав­дя­ки яко­му лю­ди­на 
> го­во­рить ні­би різ­ни­ми го­ло­са­ми
> чіт­ка ви­мо­ва з

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 192
> 1.	Прочитайте речення та виконайте завдання. 
> Шановні батьки, запрошує­
> мо вас/Вас на збори. 
> Шановна Ольго Степанівно, 
> запрошуємо вас/Вас на збори. 
> А.	 Виберіть для кожного речення потрібний варіант написання займенника.
> Б.	 Поясніть свій вибір.
> За давньою традицією українці послуговуються займенником ви під 
> час звертання до однієї особи, а саме: до незнайомої людини, старшої 
> особи, до чужих дітей віком від 14-ти років, а також за офіційних об­
> ставин. Спілкуватися на ви теж потрібно, а

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 82
> Зауважте!
> У дієсловах наказового способу пишемо м’який знак у кінці слова та 
> складу після д, т, з, с, ц, л, н:  лізь, лізьте, будь, будьте, глянь, гляньте, 
> занось, заносьте.
> 2.	 Утворіть усі можливі форми наказового способу (за зразком). Запишіть 
> їх і виділіть у них закінчення.
> Зразок. Несу — несімо, неси, несіть, хай несе, хай несуть. 
> Несу, кричу, роблю, знаю, їду, бережу, лізу. 
> 1.	Прочитайте діалог і виконайте завдання. 
> У неділю вранці Ігор телефонує Марині: 
> — Марино, пішли сьогодні

## Як утворити? (How to Form It)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 21
> Вступ. Українська мова в житті українців. Види інформації . Робота з підручником
> Іноді, старанно прочитавши текст, ми не можемо запам’я-
> тати інформацію. Існують різні прийоми, які допоможуть упо-
> ратися із цією проблемою.
> Для того, щоб краще запам’ятати прочитане, кілька разів 
> повторіть його. Пригадайте, як ми запам’ятовуємо тексти пі-
> сень: спеціально їх не вчимо, але після кількох прослуховувань 
> уже знаємо напам’ять. Проте велику книжку важко перечита-
> ти кілька разів. Тому виділіть голо

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> В. Прочитайте текст удруге й докладно його перекажіть (усно).

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> Б. Зробіть звуковий запис виділених слів.

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 236
> 531  
> І   Прочитайте речення. Що вони означають? Чи є серед них си-
> нонімічні? Назвіть їх. Про яке спілкування ідеться в реченнях.
> 1. Краєм вуха слухати. 2. Одним вухом слухати. 3. Слухати 
> обома вухами. 4. Лікарка зайшла, щоб послухати пульс. 5. Я 
> слухаю вухами, очима та серцем. 6. Я слухаю море. 7. Гаї 
> шумлять — я слухаю (П. Тичина). 8. Послухаю цей дощ. 
> 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Наказовий спосіб (The Imperative Mood)` (~300 words)
- `## Як утворити? (How to Form It)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

**Required:** читати (to read), писати (to write), слухати (to listen), дивитися (to look/watch), говорити (to speak), дати (to give), сказати (to say/tell), іти (to go)
**Recommended:** відкрити (to open), сісти (to sit down), показати (to show), запитати (to ask), підручник (textbook, m), сторінка (page, f), речення (sentence, n)

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
