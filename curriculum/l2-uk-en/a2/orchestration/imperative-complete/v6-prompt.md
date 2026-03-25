# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **39: Хай він прочитає!** (A2, A2.6 [Aspect, Tenses, and Motion]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
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
7. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-039
level: A2
sequence: 39
slug: imperative-complete
version: '1.0'
title: Хай він прочитає!
subtitle: Наказовий спосіб для всіх осіб — хай/нехай, -мо, кличний + побажання
focus: grammar
pedagogy: PPP
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
- Learner can form and use 3rd person imperatives with хай/нехай + present tense
  (хай мріє, нехай прочитає, хай вони підуть) for indirect commands, wishes,
  and permissions.
- Learner can form and use 1st person plural imperatives with -мо (читаймо,
  ходімо, зробімо, давайте поїдемо) for group invitations and suggestions.
- Learner can combine the Vocative case with imperatives and Instrumental case
  to express wishes and blessings (Оленко, будь щасливою! Друзі, будьте
  здоровими!).
- Learner can choose the correct aspect for imperatives — imperfective for
  general/repeated actions (читай щодня) vs. perfective for specific/one-time
  results (прочитай цю книгу).
content_outline:
- section: 'Хай і нехай: Наказ для третіх осіб (3rd Person Imperatives)'
  words: 550
  points:
  - 'Formation: хай/нехай + 3rd person present tense (imperfective) or
    perfective present form (future meaning). Хай він читає (Let him read).
    Нехай вона прочитає (Let her read it through).'
  - 'Uses: permission (Хай іде, я не проти — Let him go, I don''t mind),
    wish (Хай щастить! — Good luck!), indirect command (Нехай вони подзвонять
    — Have them call).'
  - 'Хай vs. нехай: нехай is slightly more formal/literary, хай is everyday
    speech. Both are correct and interchangeable in meaning.'
  - 'Plural: Хай вони прийдуть. Нехай діти граються. The verb agrees with
    the subject in person and number as usual.'
  - 'Aspect choice: Хай пише (let him write — ongoing) vs. Хай напише
    (let him write it — get it done).'
- section: 'Читаймо! Ходімо! Перша особа множини (1st Person Plural Imperatives)'
  words: 450
  points:
  - 'Formation: verb stem + -мо. From the 2nd person singular imperative:
    читай → читаймо (let''s read), ходи → ходімо (let''s go), зробі →
    зробімо (let''s do it), поїдь → поїдьмо (let''s go by vehicle).'
  - 'Alternative with давайте: давайте читати (let''s read), давайте
    поїдемо (let''s go). Давайте is softer, more of a suggestion.'
  - 'Common -мо forms in daily life: Ходімо! (Let''s go!), Починаймо!
    (Let''s start!), Зробімо це! (Let''s do it!), Поїдьмо! (Let''s drive!),
    Поговорімо (Let''s talk).'
  - 'Aspect matters: Ходімо до парку (Let''s go — one trip, perfective
    nuance via піді-мо is also possible) vs. Читаймо щодня (Let''s read
    every day — imperfective, habitual).'
- section: 'Кличний + наказовий + орудний: Побажання (Vocative + Imperative +
    Instrumental: Wishes)'
  words: 550
  points:
  - 'The powerful Ukrainian construction: Vocative (address) + Imperative
    (command/wish) + Instrumental (what to be/become). Оленко, будь
    щасливою! (Olenko, be happy!) — Vocative Оленко + imperative будь +
    Instrumental щасливою.'
  - 'More examples: Друзі, будьте здоровими! (Friends, be healthy!).
    Мамо, будь спокійною! (Mom, be calm!). Діти, будьте уважними!
    (Children, be attentive!).'
  - 'Blessings and toasts — a living Ukrainian tradition: Будьте здорові!
    Будь щаслива! Живи довго! These are not just grammar — they are
    culture.'
  - 'Vocative review for this pattern: Олена → Оленко, мама → мамо,
    друг → друже, друзі → друзі (Nom.Pl. = Voc.Pl. for most nouns),
    дитина → дитино.'
  - 'Extended wishes: Хай тобі щастить! (May you have luck!). Нехай
    здійсняться всі мрії! (May all dreams come true!). Combining хай +
    3rd person with Vocative address.'
- section: Вид дієслова в наказовому способі (Aspect in Imperatives)
  words: 450
  points:
  - 'Imperfective imperative = general instruction, repeated action, or
    politeness: Читай більше! (Read more — general advice). Пишіть
    щодня! (Write every day — habitual). Сідайте, будь ласка (Please
    sit down — polite invitation).'
  - 'Perfective imperative = specific one-time command with expected result:
    Прочитай цю статтю! (Read this article — and finish it). Напиши
    мені! (Write to me — do it). Закрий двері! (Close the door — now).'
  - 'Negative imperatives — typically imperfective: Не читай це! (Don''t
    read this). Не відкривайте вікно! (Don''t open the window). Using
    perfective in negation can sound harsh or warning-like: Не впади!
    (Don''t fall! — careful!).'
  - 'Summary table: general advice → impf., specific task → pf., habitual
    → impf., negative → usually impf., urgent warning → pf.'
vocabulary_hints:
  required:
  - хай (let — particle for 3rd person imperative)
  - нехай (let — formal variant)
  - наказовий спосіб (imperative mood)
  - побажання (wish, blessing)
  - кличний відмінок (Vocative case)
  - будь / будьте (be — imperative of бути)
  - щасливий / щасливою (happy / happy — Instr.f.)
  - здоровий / здоровими (healthy / healthy — Instr.pl.)
  - ходімо (let's go)
  - давайте (let's — suggestion particle)
  recommended:
  - спокійний (calm)
  - уважний (attentive)
  - живи (live — imperative)
  - здійснитися (to come true)
  - мрія (dream)
activity_hints:
- type: fill-in
  focus: Form the correct imperative — 3rd person with хай/нехай or 1st plural
    with -мо — from given infinitives
  items: 6
- type: quiz
  focus: Choose the correct aspect (imperfective or perfective) for imperatives
    in various situations (general advice vs. specific command)
  items: 6
- type: match-up
  focus: Match Vocative + imperative + Instrumental combinations to create
    correct wishes (Оленко + будь + щасливою)
  items: 6
references:
- title: Заболотний Grade 7, §50-51
  notes: Наказовий спосіб дієслів — formation for all persons
- title: Авраменко Grade 7
  notes: Кличний відмінок у поєднанні з наказовим способом

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Хай він прочитає!
**Module:** imperative-complete | **Phase:** A2.6 [Aspect, Tenses, and Motion]
**Textbook grades searched:** 1, 2, 3, 5

---

## Хай і нехай: Наказ для третіх осіб (3rd Person Imperatives)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 3
> Дорогий друже!
> Ти хочеш учитися читати?
> Ти прагнеш спілкуватися?
> Ти любиш фантазувати?
> Тоді ця книга саме для тебе! 
> Вона допоможе тобі навчитися читати, 
> висловлювати думки й почуття, спілкуватися.
> Умовні позначення:
>  
>  — слухаю 
>  
> — досліджую мовлення
>  
>  — читаю 
>  — обговорюю малюнок
>  
>  — спілкуюся 
>  
> — мислю критично

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> НАВЧАЮСЯ ПРАВИЛЬНО ВІДТВОРЮВАТИ ІНТОНАЦІЮ
> СПОНУКАЛЬНИХ РЕЧЕНЬ
> Я — учителька
> Прочитай і розкажи 
> ; у класі.
> Я — учитель
> У реченнях можуть висловлюватися різні 
> спонукання: прохання, запрошення, заклик, 
> порада, заборона, застереження, наказ тощо. 
> Речення, у якому є спонукання, називається 
> спонукальним. У кінці спонукального речення 
> ставиться крапка ( . ) або знак оклику ( ! ).
> 9| Прочитай і вивчи напам'ять вірш 
> Лесі Лужецької.
> Слухняним будь. 
> Люби свій край!
> Батькам завжди допомагай.
> Це — сп

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 76
> 7. Напиши записку вчительці/вчителеві або комусь із
> рідних  чи  другові/подружці.  
> 10. Чому усміхнувся тато? У яких випадках надсилають
> смс-повідомлення? У яких — пишуть записку?
> 1
> 9. Прочитай текст.
> Оксанка гукнула із сусідньої кімнати:
> — Тату, 
> я 
> зараз 
> надішлю 
> тобі 
> термінове
> смс-повідомлення!
> Тато усміхнувся: 
> — Донечко! Краще скажи мені його вголос.
> 11. Напиши, що зручніше тобі писати — записку чи 
> смс-повідомлення. Чому? 
> 7
> 1
> ÏÅÐÅÂ²ÐßÞ ÍÀÏÈÑÀÍÍß ÑË²Â 
> ÏÅÐÅÂ²ÐßÞ ÍÀÏÈÑÀÍÍß ÑË²Â 
> Ç ÍÅÍÀ

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 236
> 531  
> І   Прочитайте речення. Що вони означають? Чи є серед них си-
> нонімічні? Назвіть їх. Про яке спілкування ідеться в реченнях.
> 1. Краєм вуха слухати. 2. Одним вухом слухати. 3. Слухати 
> обома вухами. 4. Лікарка зайшла, щоб послухати пульс. 5. Я 
> слухаю вухами, очима та серцем. 6. Я слухаю море. 7. Гаї 
> шумлять — я слухаю (П. Тичина). 8. Послухаю цей дощ. 
> Підкрався і шумить. Бляшаний звук води, веселих крапель 
> кроки (Л. Костенко).
>  
> ІІ   Що означає слухати, як «гаї шумлять», як «підкрав

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 16
> Й й
> Бачу Й, й (йот). Чую  [й].
> а й в а
>  [ •  =   |  –• ]
> а й с т р и
> * а й в о р о
> а
> о
> и
> і
> Й
> га
> ми
> рі
> Й
> н о к
> лій- 
> 	
> ліній-
> 	
> май- 
> чай- 
> 	
> гай- 
> 	
> чай- 
> мий	
> лий 	
> чай	
> грай
> вимий	
> долий	
> чайник	
> зіграй
> ай
> ой
> ий
> ій
> а
> о
> і
> і
> ч
> й
> д
> м
> й
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 109
> 390. Прочитай слова. Чи можуть вони спонукати до дії?
> 391. Дослідиѳ, які бувають речення за метою висловлювання.
> Крок 1. Прочитай речення.
> Діти, пригадаймо казки. А тепер перегляньмо мульт- 
> фільм!
> Крок 2. Яка мета даних речень?
> а) запитати про казку, розповісти про мультфільм;
> б) закли́кати пригадати казки, запросити до перегляду 
> мультфільму.
> Крок 3. Зроби висновок. 
> Речення, у яких висловлюється заклик, запрошення, про- 
> хання, порада, заборона, застереження, наказ, нази-
> вають спонукальн

## Читаймо! Ходімо! Перша особа множини (1st Person Plural Imperatives)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 103
> 	 Тобі сподобався Чижик-Пижик? Він уперше 
> полетів. Що ти хотів би / хотіла б йому поба-
> жати?
> Читаємо разом
> Слова — назви дій
>  
> Слова — назви дій предмета відпо-
> відають на питання що робити? що 
> робить? що роб­лять? 
> 	 Розглянь малюнки. 
> 1
> 5
> 3
> 7
> 2
> 6
> 4
> 	 Прочитай слова — назви дій.
> Поливає, снідає, читає, ідуть, навча-
> ються, малює, чистить зуби.
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 55
> оДнина І мноЖина
> Що відбувається? Склади та запиши речення за малюнком. 
> Підкресли слова — назви дій. 
> ганчірка
> витирає
> праска
> підодіяльник
> прибирання
> прасує
> простирадло
> віяло
> Зразок. Дарина несе простирадло в шафу.
>  
> Напиши, яку домашню роботу ти виконуєш один (пиши я), 
> а яку ви в родині виконуєте разом чи по черзі (пиши ми).
> Зразок. Я гуляю з собакою. Ми вибиваємо килим.
> Слова для довідки. Поливаю, підмітаю, прибираю пило-
> сосом, складаю, витираю, прасую, перу, мию, готую.
>  
> Розглянь предм

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 116
> Досліди, чи всі іменни-
> ки можуть мати фор-
> му однини і множини.
> Я — дослідник
> Я — дослідниця
> Спостерігаю за іменниками, які вживаються тільки  
> в однині або тільки у множині
> 6   Прочитай слова і порівняй їх. 
> 	
>   Визначте число виділених іменників. Зробіть висновок, у якій 
> числовій формі вживаються ці іменники.
> дружба
> птаство
> дітвора
> сани
> окуляри
> двері
> Поясни, що спільне є між цими словами, а що — відмінне.
> Чи можна утворити форму множини від іменників у лівому 
> стовпчику?
> Чи можна утвор

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 30
> 61.	 ПОСПІЛКУЙТЕСЯ. Уявіть, що у вас з’явилася нагода звернутися 
> одним чи двома реченнями до дорослих від імені всіх дітей планети. 
> Що ви сказали б? Використайте антоніми.
> 62.	 Хто добере більше антонімів, за допомогою яких можна порівня-
> ти два малюнки?
>    
> 63.	 Прочитайте текст, замінюючи слова антонімами, де це можливо. 
> Як така заміна вплинула на зміст тексту? 
> Справа була взимку. Нам було холодно, тому ми йшли 
> все швидше й швидше. Повернули праворуч, а через квар-
> тал – ліворуч. Попер

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 7
> СЛОВА — НАЗВИ ДІЙ
> Кожну дію ти можеш назвати словом.
> ЩО РОБИТЬ?
> бігає
> стрибає
> сидить
> читає
> спить
> Діти на подвір’ї. Олена стрибає. Тарас бігає. 
> Алла сидить на лаві. Ганна читає книжку. 
> Кіт Нявчик спить.
> Що робить кожен хлопчик? Вибери правильну відповідь.
>  
>  Малює картину.
>  Читає книжку.
>  Грає на барабані.
>  Миє посуд.
>  Готує бутерброд.
>  П’є чай.
> 1

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслов

## Кличний + наказовий + орудний: Побажання (Vocative + Imperative + Instrumental: Wishes)

> **Source:** unknown, Grade 1
> **Score:** 0.50
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
> **Score:** 0.50
>
> 95
> ЗимовІ свята
> Колядки. Щедрівки
> 1. Добрий вечір тобі, пане господарю! 
> Винеси ти нам ковбасок пару.
> Винеси сала, не скупися,
> Щоб ячмінь твій уродився.
> Щоб худоба водилася,
> Щоб пшениця родилася,
> Щоб у хаті всього мали — 
> Колядників пригощали!
> 2. Прийшли щедрувати до вашої хати.
> Щедрий вечір, добрий вечір!
> Тут живе господар — багатства володар,
> А його багатство — золотії руки.
> А його потіха — хорошії діти. 
> Щедрий вечір, добрий вечір!
>  
> Вірш. Автор. Художні засоби 
> ЗИМОВІ КАНІКУ...
> відурочено ур

> **Source:** unknown, Grade 3
> **Score:** 0.

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Хай і нехай: Наказ для третіх осіб (3rd Person Imperatives)` (~550 words)
- `## Читаймо! Ходімо! Перша особа множини (1st Person Plural Imperatives)` (~450 words)
- `## Кличний + наказовий + орудний: Побажання (Vocative + Imperative + Instrumental: Wishes)` (~550 words)
- `## Вид дієслова в наказовому способі (Aspect in Imperatives)` (~450 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

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



### Vocabulary

**Required:** хай (let — particle for 3rd person imperative), нехай (let — formal variant), наказовий спосіб (imperative mood), побажання (wish, blessing), кличний відмінок (Vocative case), будь / будьте (be — imperative of бути), щасливий / щасливою (happy / happy — Instr.f.), здоровий / здоровими (healthy / healthy — Instr.pl.), ходімо (let's go), давайте (let's — suggestion particle)
**Recommended:** спокійний (calm), уважний (attentive), живи (live — imperative), здійснитися (to come true), мрія (dream)

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
