# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **50: What Will Happen?** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-050
level: A1
sequence: 50
slug: what-will-happen
version: '1.2'
title: What Will Happen?
subtitle: Я буду читати — your first future tense
focus: grammar
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Form analytic future tense using буду + infinitive for all persons
- Distinguish analytic future from present tense
- Use future tense to talk about plans and intentions
- Ask and answer "What will you do?" (Що ти будеш робити?)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Plans for tomorrow: — Що ти будеш робити завтра? — Завтра я буду
    працювати. — А ввечері? — Ввечері я буду готувати вечерю. — А що буде робити Олена?
    — Вона буде читати. — А ви будете гуляти? — Так, ми будемо гуляти в парку! All
    persons of буду + infinitive.'
  - 'Dialogue 2 — Weekend plans: — Що ви будете робити на вихідних? — У суботу ми
    будемо відпочивати. — А в неділю? — У неділю я буду готувати, а чоловік буде гуляти
    з дітьми. — Звучить добре! А я буду дивитися футбол. — Ти завжди будеш дивитися
    футбол! Future in natural planning conversation.'
- section: Майбутній час (Future Tense)
  words: 300
  points:
  - 'Grade 3-4 textbooks: майбутній час (future tense). Ukrainian has TWO futures.
    At A1 we learn ONE — the analytic future: буду + infinitive (like English ''will''
    + verb). я буду читати (I will read) ти будеш читати (you will read) він/вона
    буде читати (he/she will read) ми будемо читати (we will read) ви будете читати
    (you will read) вони будуть читати (they will read) The infinitive stays the same
    — only буду changes by person.'
  - 'Compare all three tenses: Минулий (past): Я читав/читала книжку. (I read a book.)
    Теперішній (present): Я читаю книжку. (I am reading a book.) Майбутній (future):
    Я буду читати книжку. (I will read a book.) Past = gender endings. Present = person
    endings. Future = буду + infinitive. Note: the synthetic future (прочитаю) exists
    but is A2 material.'
- section: Практика (Practice)
  words: 300
  points:
  - 'Core verbs in future tense: читати → буду читати, будеш читати, буде читати...
    працювати → буду працювати, будеш працювати... готувати → буду готувати, будеш
    готувати... гуляти → буду гуляти, будеш гуляти... дивитися → буду дивитися, будеш
    дивитися... говорити → буду говорити, будеш говорити...'
  - 'Building sentences about the future: Завтра я буду працювати з дев''ятої до п''ятої.
    Ввечері ми будемо дивитися фільм. У суботу вони будуть гуляти в парку. Що ви будете
    їсти на вечерю? Time words for future: завтра (tomorrow), наступного тижня (next
    week), у суботу (on Saturday), ввечері (in the evening).'
- section: Summary
  words: 300
  points:
  - 'Analytic future formation: буду / будеш / буде / будемо / будете / будуть + infinitive.
    The infinitive never changes — only буду conjugates. Three tenses now: Учора я
    читав. (Past — gender) Зараз я читаю. (Present — person) Завтра я буду читати.
    (Future — буду + infinitive) Question: Що ти будеш робити? (What will you do?)
    Answer: Я буду + infinitive. Self-check: What will you do tomorrow morning, afternoon,
    and evening?'
vocabulary_hints:
  required:
  - завтра (tomorrow)
  - буду (I will — form of бути)
  - будеш (you will)
  - буде (he/she/it will)
  - будемо (we will)
  - будете (you pl. will)
  - будуть (they will)
  - робити (to do)
  recommended:
  - відпочивати (to rest)
  - наступний (next, adj)
  - тиждень (week, m)
  - план (plan, m)
  - звучати (to sound)
  - футбол (football, m)
  - зараз (now)
activity_hints:
- type: matching
  focus: Match pronoun to the correct form of 'бути' (future)
  pairs:
  - я: буду
  - ти: будеш
  - він/вона: буде
  - ми: будемо
  - ви: будете
  - вони: будуть
- type: fill-in
  focus: Complete the analytic future tense (бути + infinitive)
  items:
  - Завтра я {буду|буде|будемо} працювати.
  - Що ти {будеш|буду|будете} робити ввечері?
  - Вона {буде|будуть|будемо} читати книжку.
  - Ми {будемо|буде|буду} дивитися футбол.
  - Ви {будете|будеш|будуть} гуляти в парку?
  - Вони {будуть|будемо|буде} відпочивати.
- type: fill-in
  focus: Distinguish between past, present, and future tenses
  items:
  - Зараз я {читаю|читав|буду читати}.
  - Учора він {гуляв|гуляє|буде гуляти} у парку.
  - Завтра ми {будемо дивитися|дивилися|дивимося} фільм.
  - Минулого тижня вона {працювала|працює|буде працювати}.
connects_to:
- a1-051 (My Plans)
prerequisites:
- a1-049 (Yesterday)
grammar:
- 'Analytic future: буду + infinitive (only this form at A1)'
- 'Conjugation of бути in future: буду, будеш, буде, будемо, будете, будуть'
- 'Three-tense comparison: past (gender), present (person), future (буду + inf)'
- 'Question: Що ти будеш робити?'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Future tense — analytic form (буду + infinitive) at A1.
- title: 'Grade 3-4 textbook: Майбутній час'
  notes: 'Future tense formation: складений майбутній час (analytic future).'
- title: ULP Season 1, Episode 28
  url: https://www.ukrainianlessons.com/episode28/
  notes: 'Future tense: talking about plans.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: What Will Happen?
**Module:** what-will-happen | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 251
> Кажу** літу:
> — Ти вже врізало день, щодня доточуєш ночі, підганяєш 
> усіх достигати, а саме — холоднішати. Навіщо? Я ще нічого 
> літнього не встигла.
> А воно мені каже:
> — Якби я чекало, допоки люди перероблять свою роботу, 
> то так ніколи б і не настало. Або ніколи не скінчилося.
> — Другий варіант мені подобається більше.
> — Ну навряд чи тобі хотілось би жити у світі вічнозелених 
> вишень і ніколи недостиглих кавунів. Усьому свій час. Мені 
> час минати потроху.
> — Але ж…
> — Що але ж? Просто не відклад

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Поміркуй над прочитаним
>  
> 1. Прочитай виразно вірш. Зверни увагу на його інтонацію. Як 
> треба читати поезію: швидко чи повільно, весело чи сумно, 
> бадьоро, жваво, енергійно чи розмірено й спокійно? Назви 
> слова, які допомогли тобі правильно визначити інтонацію 
> твору.
>  
> 2. Який настрій створила в тебе поезія І. Франка? Свою відповідь 
> обґрунтуй.
>  
> 3. Яку пору року відтворено у вірші? Свою думку обґрунтуй, 
> спираючись на його текст.
>  
> 4. У робочому зошиті намалюй «хмарку слів», якими автор 
> створ

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> Розділ 4  ПРИСЛІВНИК
> 160
> Підсумкові тести
> Виконайте тестові завдання.
> 1   Прислівниками є  обидва слова в  рядку
> А  вечеря, увечері
> Б  зранку, рано
> В літній, літувати
> Г половина, наполовину
> 2  Прислівник є  в реченні
> А Шановні відвідувачі зоопарку, годувати тварин заборо-
> нено.
> Б Обережно, двері зачиняються.
> В Кінцева станція. Шановні пасажири, не залишайте свої 
> речі.
> Г Пані та панове, ми розпочинаємо. Переведіть свої теле-
> фони у беззвучний режим.
> 3  Прислівник є  в усіх реченнях, ОКРІМ
> А Усі

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 211
> Готуємося до тематичного оцінювання
> Виконайте завдання. Перевірте виконання, користуючись відповідями 
> на форзаці.
> 1. Звертання є в реченні
> А	 Настали осінні, тихі та смутні дні... (С. Васильченко).
> Б	 Замело снігами полтавські села та хутори (І. Цюпа).
> В	 Намалюй, зимова нічко, білосніжні сни (З. Мороз).
> Г	 Хтось, може, винен перед ними (Л. Костенко).
> 2. Однорідні члени є в реченні
> А	 Десь там матуся в обіймах втоми виходить зустрічать мене 
> на шлях (О. Довгоп’ят).
> Б	 Схилились вишні в р

> **Source:** unknown, Grade 6
> **Score:** 0.33
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

## Майбутній час (Future Tense)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 186
> Види читання
> Мета читання:
> Мовчки
> (про себе)
> Вголос
> отримання
> інформації
>      набуття чуттєвого
>      досвіду
>      набуття естетичного
>      досвіду
> 435   Зберіть «розсипані» прислів’я, запишіть їх. Поясніть, як ви розу-
> мієте їх. У якому з них ідеться про читання з метою отримання 
> інформації?
> 1. Хто, той, багато, знає, багато, читає. 2. Книжки, нудьги, 
> читати, не знати. 3. Книжку, свято, купити, зробити, собі. 
> 4. Пізнати, книжки, хочеш, світ, читай. 5. Зірку, книжка, 
> за, яскравіша, хороша

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 1
> Правила  читання
> 1
> Першочергово у тексті твору шукай відповіді 
> на запитання:
> • Хто діє? Які його / її вчинки?
> • Де і коли відбуваються події?
> • Кого або що описує автор/авторка?
> 2
>  
> При повторному читанні:
> 1. Виділи деталі в тексті (портреті, пейзажі, 
> описі предмета чи приміщення).
> 2. Проаналізуй, яку роль вона відіграє:
> • у портреті: передає зовнішню 
> характеристику чи звертає увагу на 
> внутрішні якості героя / героїні;
> • у пейзажі: відтворює різноманітні стани 
> природи чи внутрішній стан г

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> § 9  Часи діє слова  
> 47
> Проєкт
> Виконайте завдання на вибір:
> • Заплануйте відвідання екскурсії у своєму місті. 
> • Підготуйте екскурсію по своєму місту/селищу/вулиці: 
> зберіть інформацію, продумайте план, напишіть орі-
> єнтовний текст, проведіть захід.
> Майбутній час
> Дієслова у формі майбутнього часу позначають дію, що 
> відбуватиметься або відбудеться після моменту мовлення. 
> Відповідають на питання що робитиму? що зробиш? що ро­
> битимуть? що зробить? тощо.
> Діє слова у формі майбутнього часу змінюю

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 251
> Кажу** літу:
> — Ти вже врізало день, щодня доточуєш ночі, підганяєш 
> усіх достигати, а саме — холоднішати. Навіщо? Я ще нічого 
> літнього не встигла.
> А воно мені каже:
> — Якби я чекало, допоки люди перероблять свою роботу, 
> то так ніколи б і не настало. Або ніколи не скінчилося.
> — Другий варіант мені подобається більше.
> — Ну навряд чи тобі хотілось би жити у світі вічнозелених 
> вишень і ніколи недостиглих кавунів. Усьому свій час. Мені 
> час минати потроху.
> — Але ж…
> — Що але ж? Просто не відклад

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> ви. Не могли вони таку малу дитину надовго кинути. Давай 
> краще чкурнемо звідси. (…)
> Ми не стали баритися. Шугонули вниз і кинулися навтікача. Бігти було важко, 
> бо доісторична трава була густа, висока й колюча. Але коли 
> вам загрожує небезпека й ви тікаєте, то думати про те, щоб 
> бігти було зручно й приємно, не доводиться. Коли ми вже зовсім захекались і відчули, що погоні нема, 
> ми спинилися й сіли перепочити під кущем якоїсь гігантської 
> папороті. (…)
> Поміркуй над прочитаним
>  
> 1. Чому уявні п

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> Розділ 1  ДІЄСЛОВО
> 38
> § 9  Часи діє слова
> Вправа 48
> 1   Прочитайте речення 
> Я 
> роблю  
> вчора 
> уроки.
> Я 
> робила  
> завтра 
> уроки.
> Я 
> робитиму 
> зараз 
> уроки.
> 2   Поміркуйте, чи правильно побудовані речення  
> Що в  них не так?
> 3   Скоригуйте й  запишіть правильні варіанти 
> 4   Поміркуйте, у  якій частині діє слова закладено значення часу 
> Дієслова у формі дійсного способу виражають дію, що 
> відбувалася, відбувається або відбувати меться. Вони  мають 
> форми трьох часів: теперішнього, минулого та майб

## Практика (Practice)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 185
> ЧИТАННЯ. ВИДИ ЧИТАННЯ. 
> МЕТА ЧИТАННЯ
> § 65
> Життєво важлива звичка — 
> читати щодня
> Книжки мають особливу чарівність, вони дають нам насолоду: 
> вони розмовляють з нами, дають добрі поради, стають живими друзями 
> (Ф. Петрарка).
> Слово дня: читàння, розкодувàння, уподобàння, смакîлик.
> 432   Прочитайте епіграф. Про які функції читання ідеться? Чи є зв’язок 
> між темою уроку і «словами дня»?
> Пригадуємо:
> 1  Що таке читання?
> 2  Яку роль у житті людини відіграє читання?
> 3   У яких ситуаціях ми читаємо в

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> За потреби скористай­
> теся додатковими джерелами. Підручник  
> Видавництво «Ранок»

> **Source:** unknown,

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Майбутній час (Future Tense)` (~300 words)
- `## Практика (Practice)` (~300 words)
- `## Summary` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** завтра (tomorrow), буду (I will — form of бути), будеш (you will), буде (he/she/it will), будемо (we will), будете (you pl. will), будуть (they will), робити (to do)
**Recommended:** відпочивати (to rest), наступний (next, adj), тиждень (week, m), план (plan, m), звучати (to sound), футбол (football, m), зараз (now)

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
