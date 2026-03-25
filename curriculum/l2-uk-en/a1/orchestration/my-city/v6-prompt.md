# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **30: My City** (A1, A1.5 [Places]).

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
module: a1-030
level: A1
sequence: 30
slug: my-city
version: '1.1'
title: My City
subtitle: Бібліотека, аптека, ресторан — city vocabulary
focus: vocabulary
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Name 15+ common city places (бібліотека, аптека, ресторан, etc.)
- Use locative case from M29 with city vocabulary
- Describe what you do at each place (combining verbs from A1.3)
- Give simple directions using є (there is) and тут/там
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — New in the city: — Вибачте, де тут аптека? — Аптека на вулиці Шевченка.
    — А бібліотека? — Бібліотека в центрі, біля парку. — Дякую! — Будь ласка! City
    places in asking-for-directions context.'
  - 'Dialogue 2 — My neighborhood: — Що є біля твого дому? — Біля дому є магазин і
    кафе. — А школа? — Школа далеко, у центрі міста. Review: в/на + locative for all
    places.'
- section: Місця в місті (City Places)
  words: 300
  points:
  - 'Essential city vocabulary: аптека (pharmacy), бібліотека (library), лікарня (hospital),
    магазин (shop), супермаркет (supermarket), ресторан (restaurant), кафе (café),
    банк (bank), пошта (post office), вокзал (train station), готель (hotel), музей
    (museum), театр (theater), кінотеатр (cinema), церква (church), стадіон (stadium),
    університет (university).'
  - 'Each place with its preposition (locative from M29): в аптеці, у бібліотеці,
    у лікарні, в магазині, у ресторані, у кафе, у банку, на пошті, на вокзалі, у готелі,
    в музеї. What you do there: Я купую ліки в аптеці. Я читаю в бібліотеці. Я працюю
    в офісі. Я відпочиваю в парку.'
- section: Де це? (Where Is It?)
  words: 300
  points:
  - 'Location words: тут (here), там (there), далеко (far), близько (near/close),
    біля + gen (near — as chunk: біля парку, біля дому), у центрі (in the center),
    на розі (on the corner). Note: біля requires genitive — learn as chunks, not grammar.'
  - 'Describing your city: У моєму місті є великий парк і два музеї. Бібліотека біля
    університету. Магазин тут, біля дому. Note: є = ''there is/are'' (already used
    since M06).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'City vocabulary with prepositions: В/у: аптеці, бібліотеці, магазині, банку,
    готелі, ресторані. На: пошті, вокзалі, стадіоні, площі. Location words: тут, там,
    далеко, близько, біля. Self-check: Name 5 places near your home. What do you do
    there?'
vocabulary_hints:
  required:
  - аптека (pharmacy, f)
  - бібліотека (library, f)
  - магазин (shop, m)
  - ресторан (restaurant, m)
  - готель (hotel, m)
  - вокзал (train station, m)
  - тут (here)
  - там (there)
  recommended:
  - лікарня (hospital, f)
  - супермаркет (supermarket, m)
  - пошта (post office, f)
  - музей (museum, m)
  - церква (church, f)
  - далеко (far)
  - близько (near)
  - біля (near — + genitive chunk)
activity_hints:
- type: match-up
  focus: 'Match place to activity: аптека ↔ купувати ліки'
  items: 8
- type: quiz
  focus: В or на? Choose preposition for city places.
  items: 8
- type: fill-in
  focus: 'Describe your city: У моєму місті є ___.'
  items: 6
- type: quiz
  focus: Where would you go? Choose the right place for each situation.
  items: 6
connects_to:
- a1-031 (Where To?)
prerequisites:
- a1-029 (Where Is It?)
grammar:
- City vocabulary with locative prepositions (в/на + М.в.)
- 'Location expressions: тут, там, далеко, близько, біля'
- Є = there is/are
register: розмовний
references:
- title: Anna-led module — city vocabulary through practical situations
  notes: No single textbook source — vocabulary compiled from multiple textbook city
    themes.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My City
**Module:** my-city | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 409. Доберіть до дієслів прислівники, які найбільше підходять за 
> змістом.
> Написав (як? ).... Почулося (звідки? ) .... Зашуміло (де?) 
> .... Попросив (як?) ... . Заговорили (як?) ... . Світить (де?) 
> .... Зацвіли (коли?) .... Співає (як?) .... Віє (звідки?) ....
> •  Складіть і запишіть речення з 2 словосполученнями.
> 410. Прочитайте текст. Перекажіть.
> Телефонна розмова — це теж важ­
> ливий різновид спілкування. Мовлен­
> нєвий етикет передбачає обов’язково 
> представитися незнайомій людині.
> Говорити по

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 244
> 551   Визначте, які етикетні формули доцільно використовувати 
> в таких ситуаціях. Для чого ми їх використовуємо?
> 1. … ти приніс мені словник? 2. … котра година? 3. … ви не 
> підкажете, як пройти до вулиці Київської? 4. … я не можу 
> виконати це доручення. 5. … з якої колії відправляється 
> потяг № 242? 6. Сергію, відчини, … , вікно.
> 552   Прочитайте вголос діалог і схарактеризуйте його. Які норми 
> мовленнєвого етикету порушено? Відредагуйте діалог так, щоб 
> тональність спілкування набула доброз

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 9
> Норми поведінки та правила чемності називають ети-
> кетом. В українському мовному етикеті передбачені 
> репліки — відповіді на подяку. Їхній вибір залежить від 
> того, за що дякують. Якщо за їжу, то відповідають: на 
> здоров’я, їжте на здоров’я. Якщо дякують за якусь 
> річ, то відповідають: носіть (-и) здорові (-а,-ий). Та-
> кож поширені відповіді на подяку — прошу й будь 
> ласка. Їх називають етикетними формулами.
> Спілкуймося красно
> 	 Складіть діалог, використовуючи етикетні формули.
> 16.		Прочитай п

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 216
> Мета спілкування – це те, чого ви прагнете (про щось 
> повідомити, щось з’ясувати, до чогось спонукати, вислови-
> ти почуття тощо).
> 522.	Поміркуйте, хто може стати адресатом вашого висловлення, коли 
> ви завітаєте до музичної школи, бібліотеки, аквапарку, поліклініки, ма-
> газину, театру.
> 523.	І. Розгляньте малюнки. Усно опишіть ситуацію спілкування, зобра-
> жену на кожному з них: 1) коли й де відбувається спілкування; 2) хто 
> спілкується; 3) про що можуть говорити; 4) з якою метою.
> ІІ. ПОПРАЦЮЙТ

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 237
> 580  
> І   Прочитайте текст. Про що він? Що засмутило пані Монсен? 
> Оцініть дії Анни. Як би ви відреагували на настрій бібліотекар-
> ки? Чи достатньо в цій ситуації слів утішання? Запропонуйте 
> власний план дій.
> Ця історія почалася в бібліотеці. Анна часто ходила туди 
> після уроків. Пані Монсен, яка там працювала, теж любила 
> книжки. 
> Коли бібліотека порожніла, вони з бібліотекаркою навви-
> передки гортали сторінки книжок. На початках вигравала 
> пані Монсен. Але невдовзі Анна стала спритнішою з

## Місця в місті (City Places)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 80
> 1. Розгляньте у групі обкладинки книжок. Яку інформацію
> з них можна почерпнути? Чи відомі вам головні персо-
> нажі цих книжок?
> 2. Читалочка віртуально подорожувала країною, у якій 
> були написані ці книжки. Чи знаєш ти назву цієї країни?
> Перевір себе, прочитавши подане слово справа наліво. 
> Знайди цю країну на карті.
> 2
> Я І Л Г Н А
> 3. Прочитай інформацію про Англію. Випиши виділені
> слова і постав до них питання. Пригадай, яка це частина 
> мови. Перевір себе за правилом на наступній сторінці. 
> 3
> А

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 188
> ні місця знайомі хатки садки доріжки – усе те миготить в 
> очах, у голові думки будить... (Панас Мирний). 3. І на сто-
> лі і на полицях – скрізь були папери (М. Коцю­бинський). 
> 4. Карі очі чорні брови – усе в неї сміється (П. Куліш).
> 461.	Прочитайте речення. Знайдіть у них логічні помилки. Поясніть 
> суть допущених помилок. 
> 1. Тато помив весь посуд, тарілки, чашки, виделки. 2. На 
> пероні вокзалу були жінки, чоловіки, дівчатка та хлопчи-
> ки, діти. 3. У саду ростуть різні дерева: вишні, троянди

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 1
> 53. 1. Прочитай текст. Що цікавого ти дізнався / дізналася?
> Хочеш здійснити подорож у часі? Тоді уяви себе в старовин­
> ному місті. Як ти гадаєш, де можна побачити найбільше людей? 
> Так, на торжку
> *!
> Ось стельмах продає вози та сани. Ось підійшов гутник. Він 
> виготовляє скло та вироби зі скла.
> Сьогодні все по-іншому. Відповідно — інші професії. Напри­
> клад, коуч або коучка допомагають іншим досягнути поставленої 
> мети. Маркетолог або маркетологйня організовують продаж 
> товарів чи послуг. Дієтол

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 69
> Лексикологія. Написання слів іншомовного походження
> Л(и/і)тература — це храм, куди можна ввійти лише з чи-
> стою совістю і благородними намірами (Ф. Шиллер).
> Моя батьківщина там, де моя б(и/і)бл(и/і)отека (Е. Роттер-
> дамський).
> Вправа 100
> 1. Прочитайте текст, звертаючи увагу на слова з пропущеними літерами . 
> Випишіть ці слова, уставивши, де потрібно, літери на вивчені орфограми .
> БУККРОС..ИНГ
> Буккрос..инг (з англ. bookcrossing) — це хоб..і та громад-
> ський рух, що діє за пр..нц..пом соц..альн

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> назви транспортних засобів, 
> магазинів і виробів
> літак «Мрія», мотоцикл «Ява», су-
> пермаркет «Сільпо», печиво «Дніпро» 
> назви 
> періодичних 
> видань, 
> мистецьких творів
> журнал «Vo­gue», газета «Порад­ни­
> ця», повість «Климко», мульт­фільм 
> «Рататуй»
> Потрібно розрізняти загальні назви й утворені від них умовні власні 
> назви: біла церква (храм білого кольору) — Біла Церква (місто); сві-
> тить сонечко — дитсадок «Сонечко». Назви періодичних видань, мистецьких творів і виробів, а також умов­
> ні назви п

## Де це? (Where Is It?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 20
> близько, — його домівка. Я зарубав на носі, як поводи-
> тися із цим красенем! (За В. Перепелюком).
> 	 Спиши текст, замінюючи підкреслені сполучення слів фразео-
> логізмами з вправи 43. Поясни значення виділеного фразеоло-
> гізму.
> 46.		Прочитай фразеологізми. З’єднай їх із відповідними зна-
> ченнями, запиши. Скористайся словником фразеологізмів.
> Ані рудої миші; берегти як зіницю ока; блудити словами; 
> дірка від бублика; з дорогою душею; накивати п’ятами.
> Старанно доглядати; безлюдно; говорити без п

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Пробачте, на цей раз — у собачу будку на Ци­га­
> новому подвір’ї. Там, поклавши голову на волохаті, у реп’яхах 
> лапи, дрімає здоровенний рудий Бровко.

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 51
> Лексикологiя.  Фразеологiя
> Моя найкраща подруга – Наталка. Ми всігда разом ходимо
> д

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Місця в місті (City Places)` (~300 words)
- `## Де це? (Where Is It?)` (~300 words)
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

**Required:** аптека (pharmacy, f), бібліотека (library, f), магазин (shop, m), ресторан (restaurant, m), готель (hotel, m), вокзал (train station, m), тут (here), там (there)
**Recommended:** лікарня (hospital, f), супермаркет (supermarket, m), пошта (post office, f), музей (museum, m), церква (church, f), далеко (far), близько (near), біля (near — + genitive chunk)

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
