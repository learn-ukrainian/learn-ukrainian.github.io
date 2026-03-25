# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **13: Many Things** (A1, A1.2 [My World]).

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
module: a1-013
level: A1
sequence: 13
slug: many-things
version: '1.1'
title: Many Things
subtitle: Столи, книги, вікна — from one to many
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Form nominative plurals of nouns learned in M08-M12
- Recognize the three main plural patterns (-и, -і, -а/-я)
- Use adjective plural form (-і) with plural nouns
- Describe groups of objects using plurals + adjectives + colors
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Describing a classroom (Вашуленко Grade 3 p.114-115): — Що є у класі?
    — Столи, стільці і вікна. — Які столи? — Столи великі й нові. А стільці — старі.
    Plurals emerge naturally from describing a room full of things.'
  - 'Dialogue 2 — Shopping for several items (extending M11): — Мені потрібні ручки.
    — Які ручки? Червоні чи сині? — Сині. І ще зошити. — Скільки? — Три зошити. Plural
    adjectives (-і) in real context.'
- section: Один → багато (Singular → Plural)
  words: 300
  points:
  - 'Большакова Grade 2 p.18: ''Один предмет → багато предметів.'' Three main plural
    patterns for nominative: Masculine → usually -и or -і: стіл → столи, стілець →
    стільці, телефон → телефони, зошит → зошити. Feminine → usually -и or -і: книга
    → книги, лампа → лампи, ручка → ручки, сумка → сумки. Neuter → usually -а or -я:
    вікно → вікна, ліжко → ліжка, крісло → крісла, дзеркало → дзеркала.'
  - 'Guideline (not a rule — exceptions exist): After г, к, х → -и (книга → книги,
    ручка → ручки). After most other consonants → -и or -і (стіл → столи, стілець
    → стільці). Neuter -о → -а (вікно → вікна). Neuter -е → -я (not covered yet).
    Full declension rules come later — for now, learn each plural with its noun.'
- section: Прикметники у множині (Adjectives in Plural)
  words: 300
  points:
  - 'Большакова Grade 2 p.42: який/яка/яке → які, веселий/весела/веселе → веселі.
    ALL adjectives take -і in the plural, regardless of gender: великий стіл → великі
    столи нова книга → нові книги чисте вікно → чисті вікна This is simpler than singular
    — one ending for all genders!'
  - 'Colors in plural (review M10): червоні ручки (red pens), сині зошити (blue notebooks),
    білі стіни (white walls), чорні стільці (black chairs). Demonstratives also have
    a plural form: ці (these) — Ці столи великі. Ці книги нові. ті (those) — Ті вікна
    чисті. Ті стільці старі.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Plural formation summary: Nouns: learn each plural individually (столи, книги,
    вікна). Adjectives: always -і (великі, нові, червоні, сині). Demonstratives: ці
    (these), ті (those). Possessives: мої (my — plural). Self-check: Make these plural
    — стіл, книга, вікно. Describe your classroom: Які столи? Які стільці? Які вікна?'
vocabulary_hints:
  required:
  - столи (tables — pl of стіл)
  - книги (books — pl of книга)
  - вікна (windows — pl of вікно)
  - стільці (chairs — pl of стілець)
  - ці (these — pl of цей/ця/це)
  - ті (those — pl of той/та/те)
  - мої (my — plural)
  - які (what kind? — plural)
  recommended:
  - ручки (pens — pl of ручка)
  - сумки (bags — pl of сумка)
  - лампи (lamps — pl of лампа)
  - зошити (notebooks — pl of зошит)
  - дзеркала (mirrors — pl of дзеркало)
  - крісла (armchairs — pl of крісло)
  - речі (things — pl of річ)
activity_hints:
- type: fill-in
  focus: 'Make it plural: стіл → столи, книга → книги, вікно → вікна'
  items: 10
- type: quiz
  focus: 'Choose the correct plural: стіл → столи/стола/столів?'
  items: 8
- type: fill-in
  focus: 'Adjective agreement in plural: нов__ книги, велик__ столи, чист__ вікна'
  items: 8
- type: group-sort
  focus: Sort words into однина (singular) and множина (plural)
  items: 12
connects_to:
- a1-014 (Checkpoint — My World)
prerequisites:
- a1-012 (This and That)
grammar:
- 'Nominative plural of nouns: -и/-і (m/f), -а/-я (n)'
- 'Adjective plural: always -і (великі, нові, червоні)'
- 'Plural demonstratives: ці (these), ті (those)'
- 'Plural possessive: мої (my)'
register: розмовний
references:
- title: Вашуленко Grade 3, p.114-115
  notes: 'Іменники мають два числа: однину і множину. Exercises with singular→plural.'
- title: Большакова Grade 2, p.18
  notes: Один предмет → багато предметів. First introduction of plural concept.
- title: Большакова Grade 2, p.42
  notes: 'Adjective singular/plural: який/яка/яке → які, веселий → веселі.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Many Things
**Module:** many-things | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 5
> УСНЕ І ПИСЕМНЕ МОВЛЕННЯ
> Ти можеш спілкуватись усно 
>  або письмово 
> .
> Назви ситуації, у яких діти спілкуються усно, а в яких — 
> письмово. Розкажи, як ти спілкуєшся в школі.
> Назви те, що допоможе тобі передати повідомлення усно.
> 1
> 2
> читаю
> слухаю
> розповідаю
> пишу
> прощаюся
> вітаюся
> ручка
> олівець
> телефон
> планшет
> мікрофон

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 8. Так, навіть, подарував (подарувала), я, квіти, 
> акторці.
> 9. Варто, виставу, подивитися, мені, і?
> 10. Цю, обов'язково, виставу, подивитися, варто.
> 11. За, дякую, пораду.
> 16 Прочитайте вітальну листівку. Складіть і запишіть 
> вітання своїм друзям до Нового року за цим зразком. 
> Використовуйте слова — назви дій (дієслова).
> • Озвучте свої вітання для класу.
> Любий друже! / Люба подружко!
> Вітаю тебе з Новим роком! Бажаю 
> чудово провести зимові канікули: 
> відвідати театр, прочитати цікаву 
> книжку, зу

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Умовні позначення
> — початок уроку
> — домашнє завдання
> — мовно-логічні завдання
> — дослідження мовних явищ
> — словникова скарбничка (слово, вимову і написання яко- 
>      го потрібно запам’ятати)
> — робота в парі, групі
> Вересень покликав дітей до школи. З великою радістю 
> чекаю на вас і я, ваша добра приятелька — «Українська мова». 
> Ми з вами знову помандруємо стежками цікавих мовних знахідок 
> та відкриттів. Я допоможу вам збагатити ваше мовлення новими 
> словами, поведу у світ цікавого мовознавства.
> Р

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 79
> Я вивчаю українську мову . . . . . . . 4
> Усне і писемне мовлення . . . . . . . 5
> Слова — назви предметів . . . . . . . 6
> Слова — назви дій . . . . . . . . . . . . . 7
> Слово і речення . . . . . . . . . . . . . . . . 8
> Слово і речення . . . . . . . . . . . . . . . . 9
> Звуки  . . . . . . . . . . . . . . . . . . . . . . . . 10
> Букви  . . . . . . . . . . . . . . . . . . . . . . . . 11
> А а  . . . . . . . . . . . . . . . . . . . . . . . . . . 12
> О о . . . . . . . . . . . . . . . . . . . . . . . . .

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 8
> мова І мовЛЕння 
> мова — це засіб спілкування людей (система звуків 
> і букв, слова, речення, тексти, правила). 
> Мова потрібна, щоб:
> Коли ти розповідаєш про щось, то користуєшся мо-
> вою. Це мовлення. 
> МОВЛЕННЯ
> УСНЕ                               ПИСЕМНЕ
> Я читаю. Я пишу.
> Я говорю. Я слухаю. 
> Привіт!
> Прочитай речення. Спочатку назви ті, у яких ідеться про усне 
> мовлення, потім ті, у яких ідеться про писемне. Спиши ре-
> чення. Зміни речення так, щоб у них про щось запитувалося.
>   Я oлухаЬ gагадку. Я

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 42
> Члени речення
> Навчаюся розпізнавати члени речення
> Листочкиздеревопадаютьназемлю.
> Що опадає на землю?
> Що роблять листочки?
> З чого опадають листочки?
> Куди листочки опадають?
> Листочки.
> Опадають. 
> З дерев.
> На землю.
> Прочитай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова в реченні, що відповідають 
> на 
> певні 
> питання, 
> називаються 
> членами речення.
> —	 Усі слова є членами речення.
> —	 Ні, я з тобою не можу погодитися! Хіба 
> є членами речення слова з, на? 
> Продовжте розмову.
> Хвилинка спілкуванн

## Один → багато (Singular → Plural)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 64
> Знайди слово — підпис до малюнка.
> 	
> терен	
> трава	
> талант	
> Тарас
> 	 теремок	
> тропа	
> танок	
> Тетяна
> 	
> терези	
> труба	
> тарілка	
> Тимофій
> 
> Вірш. Тема вірша. Головна думка
> Лиш телефон задзеленчить,
> Іванко в слухавку кричить:
> — Алло! Привіт! Іван на дроті!
> Що? Татусеві по роботі?..
> Так, знаю я, що мамі й тату
> Теж можуть телефонувати.
> Чого я вам сказав «привіт»?
> Напевно, так робить не слід...
> Дорослим незнайомцям діти
> Так не повинні говорити.
> Заждіть хвилиночку лишень...
> Пробачте, прошу... Добрий день!

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 73
> • Чому кишеню назвали щедрою? 
> • Напиши, коли ти буваєш щедрим. Чому?
> • Установи послідовність малюнків відповідно до тексту. 
> Перекажи оповідання, користуючись малюнками.
> сЛова оДноЗначнІ Й БаГатоЗначнІ
> СЛОВА
> одне значення
> багато значень
> однозначні
> багатозначні
> Багатозначні слова називають предмети, ознаки, дії, 
> у чомусь схожі між собою.

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 48
> 15
> Багатозначні слова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова в мові щось означають, 
> тобто мають значення. 
> Слова бувають однозначними 
> і багато­значними.
> Пояснюю значення багатозначних слів
> Однозначне
> слово має тільки одне 
> значення, тобто називає 
> якусь одну істоту, предмет, 
> ознаку, дію
>  моряк — людина, яка 
> служить на флоті
>  сом — прісноводна риба
> Багатозначне
> слово має багато значень, 
> уживається в різних 
> значеннях
>  йти
> людина йде (пересувається)
> літак іде на по

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 32
> 	
> Визнач предмети, у назвах яких є звук [г]; 
> у якому є звук [ґ]; два звуки [ш].
> 	
> Знайди «загублений» склад у словах — на-
> звах намальованих предметів. 
> 	
> Визнач, якому слову — назві зображеного 
> предмета відповідає кожна схема.
> ___ -ба-ба	
> кул-,	
> куль-,	
> буль-
> бе- ____ -за	
> -ра-,	
> -ри-,	
> -ре-
> че-ре- ___ -ха	 -ре-,	
> -па-,	
> -ба-
>  [  = •   =   |  – •]
>  [  – • |  – • |  – • ]
>  [  – • | – • ]
> Мої навчальні досягнення. Я вмію, можу
>  [  – • –  | – • |  = •]
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> НАВЧАЮСЯ ЗМІНЮВАТИ СЛОВА — 
> НАЗВИ ПРЕДМЕТІВ
> Я — учителька
> Прочитай і розкажи 
> у класі.
> один — багато^
> Я — учитель
> В українській мові слова можуть називати один 
> предмет або багато предметів.
> тварина 
> рослина
> Додай свої 
> слова.
> 32| Випишіть із лічилки Тамари Коломієць слова — назви 
> предметів.
> один
> багато
> £ Що не так на 
> малюнку?
> Біжить півень із причілка 
> і наспівує лічилку:
> — Раз-два — курчата.
> Три-чотири — зайчата. 
> П'ять-шість — гусаки.
> Сім-вісім — їжаки. 
> Дев'ять-десять — йде лисиця. 
> Нам хо

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 15
> Слова можуть бути однозначними й багатозначними. 
> Одне значення мають переважно назви людей за різними 
> ознаками, назви тварин, рослин, конкретних предметів тощо. 
> Багатозначним є слово, що має два і більше значень. Бага-
> тозначні слова називають предмети, ознаки, дії, у чомусь 
> подібні між собою. 
> Цікаво знати! Переважна більшість слів української мови — 
> багатозначні.
> 37.	
> Розглянь зображення. Прочитай слова. На кожному малюнку 
> знайди одну основну ознаку, спільну для обох предметів. 
> 38.
> 1

## Прикметники у множині (Adjectives in Plural)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 23
> 	
> Які? (розмір)
> 	
> Які? (колір)
> 	
> Які? (смак)
> (яке?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (           ?)
> Слова — назви ознак предметів
> 	 Який у тебе сьогодні настрій? Вибери.
> Який?
> Яка?
> Яке?
> Які?
> (яка?)
> (яка?)
> (яка?)
> (           ?)

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 42
> оДнина І мноЖина 
> Слова — назви ознак уживаються в однині й у множині.
> Добери до слів — назв предметів слова-ознаки.
> діти
> веселий
> здоровий
> розумний
> добрий
> який? яка? яке?
> які?
> Ігор
> Яна
> щеня
> і
>  
>  
> Доповни таблицю. Придумай слово — назву предмета до 
> кожного слова — назви ознаки. 
> однина
> множина
> Який?
> Яка?
> Яке?
> Які?
> веселий
> весела
> веселе
> веселі
> сумний
> добрі
>  
> Правда чи неправда? Запиши одне правдиве висловлювання.
> Я намалював 
> квадратний будинок 
> з трикутним дахом 
> і прямокутними 
> дверима.
> Я на

> **Sour

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Один → багато (Singular → Plural)` (~300 words)
- `## Прикметники у множині (Adjectives in Plural)` (~300 words)
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

**Required:** столи (tables — pl of стіл), книги (books — pl of книга), вікна (windows — pl of вікно), стільці (chairs — pl of стілець), ці (these — pl of цей/ця/це), ті (those — pl of той/та/те), мої (my — plural), які (what kind? — plural)
**Recommended:** ручки (pens — pl of ручка), сумки (bags — pl of сумка), лампи (lamps — pl of лампа), зошити (notebooks — pl of зошит), дзеркала (mirrors — pl of дзеркало), крісла (armchairs — pl of крісло), речі (things — pl of річ)

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
