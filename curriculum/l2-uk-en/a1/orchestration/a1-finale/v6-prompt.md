# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **55: A1 Finale** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-055
level: A1
sequence: 55
slug: a1-finale
version: '1.2'
title: A1 Finale
subtitle: One full day in a Ukrainian city — everything you've learned
focus: review
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Simulate a full day in a Ukrainian city using all A1 skills
- Navigate real situations: morning routine, transport, cafe, shopping, socializing
- Use all three tenses naturally in context
- Demonstrate readiness for A2 through integrated communication
content_outline:
- section: Ранок (Morning)
  words: 300
  points:
  - 'Scenario: You wake up in Kyiv. 7:00 — Ти прокинувся/прокинулася в готелі. (Past
    tense — M48) Доброго ранку! Яка сьогодні погода? — Сьогодні тепло і сонячно. (Weather
    — M24) Ти снідаєш у кафе: Будь ласка, каву з молоком і круасан. (Food — M36, cafe
    — M28) Скільки коштує? — Сто двадцять гривень. (Numbers — M10, shopping — M37)
    Дякую! До побачення! (Greetings — M01-M05)'
  - 'Getting around: Вибачте, як дістатися до Хрещатика? — Їдьте на метро, станція
    Хрещатик. (Transport — M34) Ти купуєш квиток. Один квиток, будь ласка. (Numbers,
    polite requests — M43) В метро ти дивишся на карту. Тобі потрібна зелена лінія.
    (Colors — M22) Past tense narration + present tense actions.'
- section: День (Daytime)
  words: 300
  points:
  - 'Exploring the city: Ти гуляєш по Хрещатику. Яка гарна вулиця! (City — M30, adjectives
    — M09) Ти бачиш великий магазин. Ти заходиш і купуєш сувеніри. (Shopping — M37)
    Скільки коштує ця вишиванка? — Тисяча двісті гривень. Дорого! (Demonstratives
    — M12) А ця? — Ця — вісімсот. — Добре, я беру! (This/that — M12)'
  - 'Lunch with a new friend: В кафе ти зустрічаєш Олену. — Привіт! Ти звідки? — Я
    з Канади. (Where from — M06) — Що ти робиш тут? — Я вивчаю українську! (Verbs
    — M16-17) — Як цікаво! Ходімо обідати! (Imperative — M43) Ти замовляєш борщ і
    вареники. Олена замовляє салат. (Food — M36) — Смачно! Ти добре говориш українською!
    — Дякую!'
- section: Вечір (Evening)
  words: 300
  points:
  - 'Evening plans: — Що будемо робити ввечері? — Ходімо в кіно! (Future — M50, invitations
    — M51) — Добре! О котрій? — О сьомій. (Time — M26) Ви дивитеся український фільм.
    Ти не все розумієш, але багато! (Linking — M44) Після кіно ви йдете в ресторан.
    (After — M44, directions — M31)'
  - 'Reflecting on the day: Ввечері в готелі ти думаєш про свій день. Сьогодні був
    чудовий день! Зранку я снідав/снідала у кафе. Потім я гуляв/гуляла по місту і
    познайомився/познайомилася з Оленою. Ввечері ми ходили в кіно і ресторан. Завтра
    я буду їздити по Києву. Я хочу побачити Лавру! All three tenses in natural reflection
    — past (the day), present (feelings), future (tomorrow).'
- section: 'Підсумок: ти готовий/готова! (You''re Ready!)'
  words: 300
  points:
  - 'A1 skills checklist — everything you can now do: Greet, introduce yourself, say
    where you''re from (A1.1). Describe people, things, your family (A1.2). Talk about
    actions, likes, habits (A1.3). Tell time, discuss weather, name days and months
    (A1.4). Navigate a city, give directions, use transport (A1.5). Order food, shop,
    handle money (A1.6). Address people politely, give instructions, connect ideas
    (A1.7). Talk about the past, make plans, handle health and emergencies (A1.8).'
  - 'What''s next — A2 preview: You''ll learn: cases (відмінки), aspect (доконаний/недоконаний
    вид), synthetic future (прочитаю), subordinate clauses, and much more. But right
    now — celebrate! Ти вивчив/вивчила A1! Вітаю! Ти вже можеш жити в українському
    місті. Це тільки початок! Self-check: Can you describe YOUR day in a Ukrainian
    city in 10+ sentences?'
vocabulary_hints:
  required:
  - готовий (ready, adj m)
  - вітаю (congratulations — chunk)
  - початок (beginning, m)
  - сувенір (souvenir, m)
  - квиток (ticket, m)
  - зустріти (to meet)
  recommended:
  - круасан (croissant, m)
  - карта (map, f)
  - лінія (line, f)
  - фільм (film, m)
  - познайомитися (to get acquainted)
  - подорожувати (to travel)
  - Лавра (Lavra — Kyiv monastery)
  - готель (hotel, m)
activity_hints:
- type: order
  focus: Put the events of the day in chronological order.
  items:
  - Зранку я прокинувся в готелі.
  - Потім я снідав у кафе.
  - Після сніданку я їхав на метро в центр.
  - Я гуляв по місту і купив сувеніри.
  - Вдень я обідав з новою подругою Оленою.
  - Ввечері ми ходили в кіно.
  - Потім ми вечеряли в ресторані.
  - Вночі я повернувся в готель і відпочивав.
- type: fill-in
  focus: Complete the sentences narrating the day using past, present, and future
    tenses.
  items:
  - '{Зранку|Завтра|Ввечері} я снідав у кафе.'
  - Зараз я {гуляю|гуляв|буду гуляти} по Хрещатику, тут дуже гарно!
  - Учора я {купив|купую|буду купувати} квиток на поїзд.
  - Завтра я {буду подорожувати|подорожував|подорожую} по Україні.
  - Ввечері ми {ходили|ходимо|будемо ходити} в кіно.
  - Зараз Олена {замовляє|замовляла|замовить} борщ і салат.
  - Учора була гарна погода, і ми {гуляли|гуляємо|будемо гуляти} в парку.
  - Я вже {готовий|початок|сувенір} до рівня А2! Вітаю!
- type: match-up
  focus: Match the situation to the correct A1 survival phrase.
  items:
  - Ordering coffee == Будь ласка, каву з молоком.
  - Asking for directions == Вибачте, як дістатися до метро?
  - Buying a souvenir == Скільки коштує ця вишиванка?
  - Meeting someone new == Привіт! Звідки ти?
  - Emergency == Допоможіть! Викличте швидку!
  - At the pharmacy == Дайте, будь ласка, таблетки від головного болю.
  - Saying goodbye == Дякую! До побачення!
- type: quiz
  focus: Review of key A1 grammar and survival vocabulary.
  items:
  - question: How do you ask about the price of a ticket?
    options:
    - Скільки коштує квиток?
    - Де тут квиток?
    - Дайте один квиток.
  - question: You are inviting a friend to a cafe. What do you say?
    options:
    - Ходімо в кафе!
    - Я був у кафе.
    - Де кафе?
  - question: How do you say 'My head hurts'?
    options:
    - У мене болить голова.
    - У мене температура.
    - Я хворий.
  - question: Someone asks 'Де ви?'. How do you answer?
    options:
    - Я на вулиці Хрещатик.
    - Мене звати Адам.
    - Я з Канади.
  - question: What tense is 'Завтра я буду читати книгу'?
    options:
    - Future
    - Past
    - Present
connects_to: []
prerequisites:
- a1-054 (Emergencies)
grammar:
- 'Review: all three tenses (past, present, future) in integrated context'
- 'Review: imperative for requests and invitations'
- 'Review: У мене болить, Мені потрібен — impersonal chunks'
- No new grammar — integration and consolidation of all A1 grammar
register: розмовний
references:
- title: ULP Season 1, Episodes 36-40
  url: https://www.ukrainianlessons.com/episode36/
  notes: Consolidation episodes — daily life in Ukrainian.
- title: State Standard 2024
  notes: A1 completion — all thematic areas covered.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: A1 Finale
**Module:** a1-finale | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Ранок (Morning)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 29
> 58.	 Доберіть антоніми до обох слів у словосполученнях і запишіть 
> утворені словосполучення. 
> ЗРАЗОК. Веселий ранок – сумний вечір. 
> Теплий день, минуле літо, добрий друг, гарний початок, 
> перша перемога, корисний холод.
> 59.	 І. Прочитайте текст, визначте його тип мовлення. Що нового ви 
> дізна­лися? 
> ПРО КОРИСТЬ ХОЛОДУ
> Холод – це не завжди погано. Він має і корисні власти-
> вості. Саме морозна, холодна погода змушує організм по-
> силювати свій імунітет. Холод пришвидшує циркулювання 
> крові. Так

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 130
> 1.	Прочитайте речення та виконайте завдання.
> 1. Ясне сонечко викотилося геть із-за гори (Панас Мирний). 2. Дивлюсь 
> я на яснії зорі (Леся Українка). 3. Ой зійди, зійди, ясен місяцю (Нар. тв.).
> А.	Які відмінності в будові виділених прикметників?
> Б.	Яка форма прикметника звична для вас? 
> В українській мові розрізняють повні та короткі прикметники.
> Повні прикметники змінюємо за відмінками, родами та числами: зе-
> лений → зеленого, зелена, зелені; певний → певного, певна, певні.
> Короткі прикме

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 153
> 153
> Відредагуйте усно речення. Поясніть суть допущених помилок.
> 1. Їхати ранковим рейсом найбільш зручніше. 2.  Сьогодні я 
> одягнувся більш тепліше. 3. Мишко намагався ступати якнай-
> тихесенько. 4. Сергій більш відповідальніше ставиться до на-
> вчання. 5. Тарас прочитав вірш саме краще. 6. Ірина поганіше
> почала ставитися до мене.
> Запишіть речення, замінюючи прислівник або простою формою вищого сту-
> пеня, або складеною.  
> ЗРАЗОК. Діти відповідали впевнено. – Діти відповідали впев-
> неніше. Діти

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

## День (Daytime)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 192
> КНИЖКА ВЧИТЬ, ЯК У СВІТІ ЖИТЬ
> – Добривечір, сусіде! Добривечір, дорогий! – почав Семен Семенович, 
> усміхаючись сонцесяйно і привітно. – Вечір добрий! – ґречно відповів Павло Максимович. – Ви знаєте, сусіде, – мовби між іншим сказав Семен Семенович. – 
> Я завтра якраз їду в район, у фінвідділ. То можу заодно отого хлоп’ячого 
> білета в ощадкасу завезти. Щоб часу не гаяти. Бо його ж іще в Київ на 
> перевірку посилатимуть. Давайте! Павло Максимович якось дивно глянув на Семена Семеновича і враз 
> с

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 64
> 158   Прочитайте порівняння. Що вони означають? Складіть із ними 
> речення.
> Як у віночку. Як у кожусі.
> Здійсніть  рефлексію в довільний спосіб.
> 159   І   Доберіть і запишіть по 15 слів — назв старовинного й сучасно-
> го одягу. Поясніть значення кожного слова.
>  
> ІІ   Знайдіть інформацію і дайте письмові розгорнуті відповіді 
> на запитання: Які два види одягу були в київських князів? 
> Які відмінності, особливості має чоловіча вишита сорочка? 
> Що таке «відлога»? Яку хустину називають терновою?
>  
> ІІ

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 77
> розділ 2
> Тарас Григорович запросив з нього сто п’ятдесят карбованців. 
> А пан йому каже:
> – Що це ви так дорого хочете?
> – Дорого? Тоді це буде коштувати триста карбованців.
> Пан розсердився й пішов од нього. А Тарас Григорович узяв 
> портрет, що накидав олівцем з того пана, приставив до нього осля-
> чі вуха, поніс у магазин і сказав прикажчикові:
> – Постав цей портрет на вітрині, а хто купить, нехай заплатить 
> п’ятсот карбованців.
> От іде пан вулицею, дивиться – на вітрині його портрет, тільки 
> з ос

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 168
> Фонетика. Графіка. Орфоепія. Орфографія. Наголос в українській мові
> Мої любі подруги та при-
> ятелі, пропоную взяти участь 
> у флешмобі до Дня захисту 
> тварин. Завдання таке: при-
> нести фото своїх домашніх 
> улюбленців. Зустрічаємося 
> біля нової піцерії рівно о чо-
> тирнадцятій годині та разом 
> чіпляємо фото на розміщений 
> посередині стіни стенд. Дрес-
> код — зручний одяг і чарівні 
> усмішки.
> Вправа 278
> 1. Прочитайте пари слів .
> поділ (ділення) і поділ (низовина),
> атлас (сукупність мап) — атла

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 115
> Всеволод  Нестайко
>   • Прочитайте розділ другий повісті (частина друга) 
>            і виконайте завдання. 
> ЧАСТИНА ДРУГА
> (розказана зновутаки Павлушею Завгороднім)
> Незнайомець із тринадцятої квартири,  
> або Злодії шукають потерпілого
> Розділ другий
> Випадок у метро. «Космонавт». Конфлікт із київською міліцією
> Ми приїхали до Києва. На цілий місяць. У гості до мого рідного дядька 
> й моєї рідної тітки.
> Це було прекрасно. Ми цілий рік мріяли про цей день. Не те що ми ніко-
> ли не бували в Києві. Б

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 66
> 66
> будівлі; (щ о  з р о б и м о ? ) ... на найвищу будівлю; (щ о  р о б и -
> т и м у ? ) ... враженнями від подорожі.
> ІІ. Які міста зображено на світлинах? До якої з них може підійти найбільше утво-
> рених словосполучень?
> ПОСПІЛКУЙТЕСЯ. Чому про людину, яка подорожує, можна ска-
> зати, що вона по-справжньому багата?
> 150 
> Дієслова у формі майбутнього часу змінюємо за особами
> та числами.
> Особа
> Проста форма
> Однина
> Множина
> Однина
> Множина
> 1-ша
> скажу
> скажемо
> вивчу
> вивчимо
> 2-га
> скажеш
> скажете
> вивчиш
> ви

## Вечір (Evening)

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
> 3. Варто ознайомити учнів зі зраз­
> ком тесту, який вже існує. 4. Радіємо тому, що в нас скільки друзів! 5. Ві­
> таю іх від усієї душі! 6. Кухарі запрошують на майстер-к

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Ранок (Morning)` (~300 words)
- `## День (Daytime)` (~300 words)
- `## Вечір (Evening)` (~300 words)
- `## Підсумок: ти готовий/готова! (You're Ready!)` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 25-40% Ukrainian.
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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** готовий (ready, adj m), вітаю (congratulations — chunk), початок (beginning, m), сувенір (souvenir, m), квиток (ticket, m), зустріти (to meet)
**Recommended:** круасан (croissant, m), карта (map, f), лінія (line, f), фільм (film, m), познайомитися (to get acquainted), подорожувати (to travel), Лавра (Lavra — Kyiv monastery), готель (hotel, m)

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
