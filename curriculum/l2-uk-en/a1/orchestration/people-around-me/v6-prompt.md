# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **40: People Around Me** (A1, A1.6 [Food and Shopping]).

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
module: a1-040
level: A1
sequence: 40
slug: people-around-me
version: '1.2'
title: People Around Me
subtitle: Я бачу маму, знаю Олену — accusative for people
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Use accusative case for animate nouns (Я бачу маму, знаю Олену)
- Recognize that masculine animate accusative = genitive (бачу брата, друга)
- Distinguish animate vs inanimate accusative
- Talk about people in your daily life using accusative
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Who do you see? — Кого ти бачиш? — Я бачу маму і тата. — А хто це?
    — Це мій брат. Ти знаєш мого брата? — Ні, я не знаю твого брата. — Ходімо, я тебе
    познайомлю! Accusative animate: маму (f), тата (m), брата (m).'
  - 'Dialogue 2 — At work: — Ти знаєш нашу вчительку? — Так, я знаю Олену Петрівну.
    — А нового лікаря? — Ні, я ще не знаю лікаря. — Він дуже добрий. Я чекаю його
    зараз. Animate accusative with people around you.'
- section: Кого? (Whom?)
  words: 300
  points:
  - 'Accusative animate vs inanimate: Inanimate (M37): Я їм (що?) хліб. → no change
    for masculine. Animate (M40): Я бачу (кого?) брата. → masculine changes! The question
    word is the key: що? = inanimate (things) → masculine stays same. кого? = animate
    (people, animals) → masculine changes.'
  - 'Ukrainian school approach (Grade 4): ''Бачу кого? що?'' — two questions, two
    patterns. Кого? triggers the animate rule: masculine animate accusative = genitive
    form. брат → брата, друг → друга, тато → тата, лікар → лікаря. This is why animate
    accusative matters — it changes masculine nouns.'
- section: Знахідний відмінок — живе (Accusative Animate)
  words: 300
  points:
  - 'Feminine animate: same as inanimate (-а → -у, -я → -ю): мама → маму (Я бачу маму),
    сестра → сестру (Я знаю сестру), Олена → Олену (Я чекаю Олену), подруга → подругу
    (Я люблю подругу). No surprise — same ending as M37 (кава → каву).'
  - 'Masculine animate: accusative = genitive (THE new rule): брат → брата (Я бачу
    брата), друг → друга (Я знаю друга), тато → тата (Я люблю тата), лікар → лікаря
    (Я чекаю лікаря), вчитель → вчителя (Я знаю вчителя), сусід → сусіда (Я бачу сусіда).
    Pattern: masculine animate in accusative takes the genitive ending. Compare: Я
    бачу хліб (inanimate — no change) vs Я бачу брата (animate — changes).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative summary — the full picture: | | Inanimate (що?) | Animate (кого?)
    | | Masculine | = nominative (хліб) | = genitive (брата) | | Feminine | -а → -у
    (каву) | -а → -у (маму) | | Neuter | = nominative (молоко) | (rare at A1) | Key
    verbs with animate accusative: бачити (to see), знати (to know), любити (to love),
    чекати (to wait for), шукати (to look for). Self-check: Я бачу ___ (мама → маму,
    брат → брата).'
vocabulary_hints:
  required:
  - бачити (to see)
  - знати (to know)
  - любити (to love)
  - чекати (to wait for)
  - шукати (to look for)
  - друг (friend, m)
  - подруга (friend, f)
  recommended:
  - сусід (neighbor, m)
  - колега (colleague, m/f)
  - викладач (lecturer, m)
  - вчитель (teacher, m)
  - лікар (doctor, m)
  - продавець (seller, m)
  - покупець (buyer, m)
activity_hints:
- type: fill-in
  focus: 'Я бачу ___ (nominative → accusative: мама → маму, брат → брата)'
  items:
  - Я бачу {маму|мама|мами}.
  - Я бачу {брата|брат|брату}.
  - Я знаю {Олену|Олена|Олени}.
  - Я знаю {друга|друг|другу}.
  - Я люблю {тата|тато|таті}.
  - Я чекаю {вчителя|вчитель|вчителю}.
  - Я шукаю {подругу|подруга|подруги}.
  - Я бачу {сусіда|сусід|сусіду}.
  - Я чекаю {лікаря|лікар|лікарю}.
  - Я знаю {сестру|сестра|сестри}.
- type: group-sort
  focus: 'Sort: animate (кого?) vs inanimate (що?) — changes vs stays same for masculine'
  groups:
  - name: Animate (кого?)
    items:
    - брата
    - маму
    - друга
    - лікаря
    - Олену
  - name: Inanimate (що?)
    items:
    - хліб
    - каву
    - воду
    - чай
    - борщ
- type: quiz
  focus: 'Choose correct: Я знаю (Олена / Олену / Олени)'
  items:
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - братом
  - question: Я люблю ___.
    options:
    - подругу
    - подруга
    - подруги
  - question: Я чекаю ___.
    options:
    - сусіда
    - сусід
    - сусідом
  - question: Я шукаю ___.
    options:
    - вчителя
    - вчитель
    - вчителю
  - question: Я знаю ___.
    options:
    - лікаря
    - лікар
    - лікарем
  - question: Я бачу ___.
    options:
    - колегу
    - колега
    - колеги
  - question: Я люблю ___.
    options:
    - тата
    - тато
    - татом
- type: fill-in
  focus: 'Complete: Я люблю ___, знаю ___, чекаю ___. (family/friends)'
  items:
  - — Кого ти {бачиш|бачити|бачить}?
  - — Я бачу {брата|брат|братом} і маму.
  - — Ти знаєш мого {друга|друг|другу} Тараса?
  - — Ні, я не {знаю|знає|знати} твого друга.
  - — А кого ти {чекаєш|чекати|чекає}?
  - — Я чекаю {лікаря|лікар|лікарем}.
connects_to:
- a1-041 (Checkpoint — Food and Shopping)
prerequisites:
- a1-039 (Shopping)
grammar:
- 'Accusative animate: feminine -а→-у (= inanimate), masculine = genitive'
- 'Animate vs inanimate distinction: кого? vs що?'
- 'Key pattern: masculine animate accusative = genitive (брат → брата)'
register: розмовний
references:
- title: ULP Season 1, Episode 33
  url: https://www.ukrainianlessons.com/episode33/
  notes: Accusative case — animate nouns.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу кого? що? — animate accusative = genitive.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: People Around Me
**Module:** people-around-me | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 4
> 	 Розглянь фото Оксани. Чому в неї поганий настрій? Як можна її 
> втішити? 
> 	 Склади й запиши кілька речень про очікування від навчання в 
> цьому році.
> 3.	 	Розгляньте діаграму. Прочитайте назви розділів, які ви буде-
> те вивчати в 4 класі. 
> Діаграма — це малюнок, креслення чи графічне зображення, 
> подані як певні позначення об’єктів і понять, що порівнюються, 
> і можуть показувати відношення між ними.
> Мова і мовлення.
> Українська абетка:
> звуки та букви
> Іменник
> Прикметник
> Числівник
> Займенник
>  Діє

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> – Та я вже, – каже чоловік, – і сам бачу, що погано. Чи ви, дідусю, не 
> знаєте, як мені мого сина вгадати?

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

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 10
> 2. Чи легко жити серед байдужих людей? Чи можна від них 
> дочекатися допомоги, співчуття, поради, підтримки? Чи 
> розділить така людина твою радість, твоє горе?
> 3. Розкажи, хто до тебе завжди чуйний, уважний, хвилю-
> ється за тебе, вболіває, радіє твоїм радощам і успіхам.
> 16. 1. Розгляньте малюнок і прочитайте оповідання.
> НАШ ТАТО ОДУЖАВ
> Зустріла Катруся на подвір’ї двох своїх однокласників 
> і поділилася радістю:
> — Наш тато одужав.
> Петро й Гриць подивилися на Катрусю, знизали пле-
> чима і, нічого

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 206
> вали! (В. Нестайко). 3. Дружній череді вовк не страшний 
> часто говорив батько (М. Номис). 4. Я нахилився до Ту­сі 
> й запитав Слухай, а ти собак боїшся? (В. Нестайко). 5. Я 
> сказав Сонце, сонце! Уділи мені живущої води... (В. Сві­- 
> д­зинський).
> 51. ДІАЛОГ
> Про розмову двох або кількох осіб та  
> про вживання розділових знаків 
> 508.	 Прочитайте текст. Хто бере участь у розмові? Простежте, як пе-
> редано на письмі слова кожного учасника спілкування, які розділові 
> знаки вжито.
> ТІКÀЄ
> Прогулюючись

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> Розділ 8. Займенник 
> 256
> 4. Згадайте інші прислів’я та приказки на цю тему. Назвіть у  них займен-
> ники.
> Проєкт!
> Підготуйте усне висловлення на одну з тем: «Спілку-
> вання в  моєму житті», «Чи можу я  прожити без спіл-
> кування», «Який я  співрозмовник».
> Особові займенники
> Особові займенники вказують на особу мовця (я, 
> ми), співрозмовника (ти, ви) або ж  осіб, про яких го-
> ворять (він, вона, воно, вони).
> Однина
> Множина
> 1 особа (мовець)
> я
> ми
> 2 особа (співрозмовник)
> ти
> ви
> 3 особа (особа, про яку 
> г

## Кого? (Whom?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 107
> — Ні. Я допомагав годувати телят, а вони на птахофермі 
> доглядали каченят.
> 2. Спишіть текст. Підкресліть займенники та вкажіть їх особу 
> і число. За потреби користуйтесь таблицею на с. 106.
> Міркуйте так: хто? — я, займенник, вказує на особу, яка 
> говорить про себе: 1-ша особа однини.
> 3. Складіть усну розповідь про те, як ви допомагаєте стар -
> шим. Використовуйте у своєму творі особові займен -
> ники.
> 228. 1. Розглянь світлину і прочитай текст. 
> Ми з братом Михайлом виїхали в поле. Брат — трак

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 215
> 493   Розгляньте схему. Чи можна вважати малюнок ілюстрацією спіл-
> кування? Обґрунтуйте відповідь. Поясніть, у чому полягає важ-
> ливість спілкування.
>  СПІЛКУВАННЯ ПЕРЕДБАЧАЄ:
> Інформування
> Налагодження 
> добрих стосунків
> Допомогу
> Узгодження, 
> коригування спільних 
> дій і планів
> Пораду
> Обмін 
> враженнями
> Вплив на думку, 
> поведінку
> Підтримку
> Інф
> в
> 494   Порівняйте тексти в обох колонках. Яке спілкування більш ко-
> рисне? Чому? Що ви відредагували б у діалогах? Чи може бути 
> спілкування марнуванням

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 158
> ЖИВИЛЬНІ ДЖЕРЕЛА МУДРИХ КНИГ
> Вона в нас не вимовляє літе-
> ру «р». 
> За мить Яришка вже ставила 
> на стільці переді мною молоко, 
> яєчню, сир і хліб із маслом.
> Я збагнув, що в хаті нікого 
> немає, усі на роботі, і їй доручено 
> доглядати мене.
> – Будь ласка, любий бгатику, 
> їж! – сказала вона солодким голосом.
> Я насторожився.
> А коли вона втретє сказала «любий бгатику» («Любий 
> бгатику, спегшу пгоковтни таблетку»), це вже мене зовсім 
> збентежило.
> «Любий бгатику!» Вона ніколи мене так не називала. 
> В

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> Як хліб …
> Я так люблю, я так люблю тебе,
> Моя співуча українська мово!
> В тобі шумить Полісся голубе,
> І дужі хвилі гомонять Дніпрові.
> В тобі живе Карпатська височінь,
> Що манить у незвідане майбутнє,
> І степова безкрая широчінь,
> І Кобзарева дума незабутня!
> Ти, рідна мово, чиста, як роса,
> Цілюща й невичерпна, як криниця.
> Святине наша, гордість і краса,
> Ти — розуму народного скарбниця!
> Як легко йти з тобою по землі
> І підставлять вітрам лице відкрите!
> Для мене ти — як і насущний хліб,
> Без тебе я не змі

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 52
> Лексикологія. Антоніми
> Антоніми
> Вправа 70
> 1. Прочитайте вірш Алли Свашенко .
> * * *
> Два брати жили на світі
> Був один з них працьовитий,
> А другий — ледачий дуже.
> Слухай казку про них, друже.
> День і ніч брати сварились
> І ніколи не мирились.
> Все, що перший будував,
> Другий миттю руйнував…
> Той хоробрий і правдивий,
> Той брехливий, полохливий.
> Той розумний, той дурний,
> Той великий, той малий.
> Хоч брати вже й помирились,
> Після них слова лишились,
> Дуже горді, незалежні,
> Абсолютно ПРОТИЛЕЖНІ.
> 2. Знайдіт

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 204
> ВІД  СМІШНОГО  ДО  ВЕЛИКОГО
> Теорія літератури
> «Та щось, — каже, — не то світить
> Край ваших віконців!»
> «Як-то, — каже, — не то світить?..
> Та ж то братик сонців!»
> Коли братик — так і братик,
> Нічого чинити;
> Мусив бідний циганюга
> Всю ніч молотити.
> На другий день той із хати,
> А циган у хату.
> «А, здоровенькі, панотче!
> Чи не можна б плату?»
> «Можна, — каже, — чом не можна,
> Як не дати плати?
> Ходім, — каже, — до засіка1,
> Будем насипати».
> Прийшов циган до засіка,
> Торбу підставляє.
> Пішов гарнець2, пішов

## Знахідний відмінок — живе (Accusative Animate)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 130.1. Прочитай речення.
> Богдан милувався квітами. Аліна раділа подарункові. Над 
> полем красувалася веселка. На лавочці сиділи діти. Взимку 
> ми підгодовуємо птахів.
> 2. Випиши словосполучення з виділеними іменниками. Познач 
> відмінок іменників. Запиши за зразком.
> Зразок. Йшла (чим?) садом (Од. в.).
> РОЗРІЗНЕННЯ НАЗИВНОГО ТА ЗНАХІДНОГО ВІДМІНКІВ^
> * 
> 131.1. Пригадай відмінки іменників та питання, на які вони від­
> повідають. Визнач відмінок виділених іменників.
> Тато намалював кошеня. Кошеня лягло на

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 171
> НАПРИКЛАД: 
>       я к о м у?
> У міському парку ростуть троянди. 
>    ч и й?
> Мій брат навчається в університеті.
> Означення підкреслюємо так:        .
> Означення найчастіше виражаємо прикметником або за-
> йменником, рідше – іменником.
> Зверніть увагу!
> 	я к и й?	
>      я к і?	
> ч и ї?
> сік з винограду    гілки ялини    батькові слова
> 419.	Прочитайте речення. Доведіть, що підкреслені члени речення – 
> означення. Які з них виражено прикметниками?
> 1. Вулиця як довга к

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Кого? (Whom?)` (~300 words)
- `## Знахідний відмінок — живе (Accusative Animate)` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary

**Required:** бачити (to see), знати (to know), любити (to love), чекати (to wait for), шукати (to look for), друг (friend, m), подруга (friend, f)
**Recommended:** сусід (neighbor, m), колега (colleague, m/f), викладач (lecturer, m), вчитель (teacher, m), лікар (doctor, m), продавець (seller, m), покупець (buyer, m)

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
