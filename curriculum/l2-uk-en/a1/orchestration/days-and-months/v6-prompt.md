# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **23: Days and Months** (A1, A1.4 [Time and Nature]).

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
module: a1-023
level: A1
sequence: 23
slug: days-and-months
version: '1.2'
title: Days and Months
subtitle: У понеділок, у січні — the calendar in Ukrainian
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Name all 7 days of the week and use "on" (у/в + day as chunk)
- Name all 12 months and 4 seasons
- Say dates using ordinal numbers (as chunks)
- Plan a week using days, times, and activities
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Planning the week (ULP Ep15 pattern): — Що ти робиш у понеділок?
    — Я працюю. А у вівторок? — У вівторок я вивчаю українську. — А у суботу? — У
    суботу гуляю. Неділя — вільний день! Days of the week in practical scheduling.'
  - Dialogue 2 — When is your birthday? — Коли у тебе день народження? — У березні.
    — Якого числа? — П'ятнадцятого березня. А у тебе? — У мене в серпні. — О, це літо!
    Months and seasons in personal context.
- section: Дні тижня (Days of the Week)
  words: 300
  points:
  - 'Seven days — all LOWERCASE in Ukrainian (not capitalized like English): понеділок
    (Monday), вівторок (Tuesday), середа (Wednesday), четвер (Thursday), п''ятниця
    (Friday), субота (Saturday), неділя (Sunday). Вашуленко Grade 2 p.83: planning
    your week activity. Note: неділя = Sunday AND ''week'' in some dialects. Standard
    ''week'' = тиждень.'
  - '''On'' a day = у/в + accusative (chunk — no grammar analysis): у понеділок, у
    вівторок, у середу, у четвер, у п''ятницю, в суботу, в неділю. Note the endings
    change — just memorize each form.'
- section: Місяці і пори року (Months and Seasons)
  words: 300
  points:
  - '12 months — also lowercase, organized by season: Зима: грудень (Dec), січень
    (Jan), лютий (Feb). Весна: березень (Mar), квітень (Apr), травень (May). Літо:
    червень (Jun), липень (Jul), серпень (Aug). Осінь: вересень (Sep), жовтень (Oct),
    листопад (Nov). All months are masculine. Many come from nature words (березень
    ← береза, липень ← липа, листопад ← листя падає).'
  - '4 seasons: зима (winter, f), весна (spring, f), літо (summer, n), осінь (autumn,
    f). ''In'' a month/season = у/в + locative (chunk): у січні, у лютому, в березні...
    влітку, взимку, восени, навесні. Seasonal forms are irregular — memorize as chunks.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Calendar vocabulary: Days: понеділок → неділя (у понеділок, в суботу). Months:
    січень → грудень (у січні, в серпні). Seasons: зима, весна, літо, осінь (взимку,
    навесні, влітку, восени). Self-check: What day is today? What month? What season?
    When is your birthday? Plan your next week in Ukrainian.'
vocabulary_hints:
  required:
  - понеділок, вівторок, середа (Mon, Tue, Wed)
  - четвер, п'ятниця (Thu, Fri)
  - субота, неділя (Sat, Sun)
  - тиждень (week, m)
  - зима, весна, літо, осінь (winter, spring, summer, autumn)
  recommended:
  - січень, лютий, березень (Jan, Feb, Mar)
  - квітень, травень, червень (Apr, May, Jun)
  - липень, серпень, вересень (Jul, Aug, Sep)
  - жовтень, листопад, грудень (Oct, Nov, Dec)
  - день народження (birthday)
activity_hints:
- type: fill-in
  focus: Put days of the week in order
  items:
  - понеділок, {вівторок|субота|четвер}, середа
  - середа, {четвер|п'ятниця|неділя}, п'ятниця
  - п'ятниця, {субота|вівторок|середа}, неділя
  - неділя, {понеділок|вівторок|четвер}, вівторок
  - вівторок, середа, {четвер|п'ятниця|неділя}
  - четвер, п'ятниця, {субота|понеділок|вівторок}
  - субота, {неділя|понеділок|п'ятниця}, понеділок
- type: match-up
  focus: Match the month to the correct season
  pairs:
  - січень ↔ зима
  - квітень ↔ весна
  - липень ↔ літо
  - жовтень ↔ осінь
  - лютий ↔ зима
  - травень ↔ весна
  - серпень ↔ літо
  - листопад ↔ осінь
- type: fill-in
  focus: Use the correct 'in/on' chunk for days and months
  items:
  - Я працюю {у понеділок|понеділок|в понеділок}.
  - Мій день народження {у березні|березень|в березень}.
  - Ми гуляємо {в суботу|субота|у субота}.
  - '{Взимку|Зима|У зима} холодно.'
  - Я вивчаю українську {у вівторок|вівторок|в вівторок}.
  - Вони відпочивають {у серпні|серпень|в серпень}.
connects_to:
- a1-024 (Weather)
prerequisites:
- a1-022 (What Time?)
grammar:
- 'Days of the week: у/в + accusative chunk (у понеділок, в суботу)'
- 'Months: у/в + locative chunk (у січні)'
- 'Seasons: adverbial forms (взимку, навесні, влітку, восени)'
register: розмовний
references:
- title: Вашуленко Grade 2, p.83
  notes: Planning your week — days of the week activity.
- title: Вашуленко Grade 2, p.69-89
  notes: Months through seasonal stories and poems.
- title: ULP Season 1, Episode 15
  url: https://www.ukrainianlessons.com/episode15/
  notes: Days of the week and planning.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Days and Months
**Module:** days-and-months | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 79
> 4   Пригадай назви днів тижня. Запиши їх правильно, користуючись 
> орфографічним словником.  
> 5   Знайди у тлумачному словнику значення 
> трьох невідомих тобі слів і запиши їх.
> 	 	
> 6   Запиши подані слова в абетковій 
> послідовності.
> 	 	
> 3   Прочитайте прізвища сучасних українських 
> дитячих письменників та письменниць.
> 	
>   Запиши ці прізвища в абетковій послідовності.
> 	
>   З допомогою дорослих назви твори цих авторів (авторок). 
> 	
>   Підкресли орфограми  у словах.
> 	
>   Спробуй скласти речен

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Як

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 29
>  
> ІІ   Зверніть увагу на «слово дня». Що воно означає? Чи можете 
> ви його вжити стосовно себе? Скажіть про це реченням. До-
> беріть і запишіть ключові слова, що визначають зміст ваших 
> захоплень. Які з них власне українські, а які — запозичені?
> Чи потрібні мові запозичення? Які саме? Наскільки важли-
> во для людини мати захоплення?
> +
> Що нове 
> на уроці?
> *
> Що 
> відоме 
> раніше?
> –
> Із чим 
> ви не 
> згодні?
> ?
> Що не 
> зрозуміли?
> !
> Про 
> що ще 
> хотіли б 
> дізнатися?
> 64   І   Прочитайте текст. Яку проблему ав

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 77
> 2. Допоможи Щебетунчикові вставити пропущені назви 
> днів тижня. Перевір їх написання за словником. Спиши 
> текст,  підкресли  орфограми  в  дібраних  словах.
> Якщо до слова не можна дібрати перевірне слово,
> то його написання треба перевіряти за словником.
> Тиждень починає … .  Після нього приходить … .
> За ним настає … . Четвертий день тижня — … .
> А п’ятий — … . П’ять днів працюємо, а в … і … 
> відпочиваємо.
> 3. Прочитай і розв’яжи задачу Родзинки.
> Марійка з дідусем вирушили в похід на третій 
> день

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> Довідка: привітався, відповів, поцікавився, усміхнувся.
> •  Випишіть примовки, поясніть їх зміст. Визначте час, особу та 
> число дієслів, ужитих у примовках.
> 363. Прочитайте словосполучення з дієсловами в 2-й особі мно­
> жини теперішнього часу.
> Виход..те на наступній зупинці, зачиня..те двері, роз­
> гортайте книжки, ужива..те заходів, ставитеся до при­
> ятеля, залеж..те від умов, складайте іспити, виход..те на 
> зупинці, пиш..те листівку.
> •  Запишіть словосполучення, уставляючи пропущені букви.
> 364. П

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 12
> РОЗВИТОК МОВЛЕННЯ
> Поміркуйте!
> За яких обставин (офіційних чи неофіційних) може відбувати­
> ся спілкування в поданих ситуаціях?
>  Супермаркет; 
>  день народження брата; 
>  пікнік зі своєю родиною;
>  спортзал; 
>  кінотеатр.
> 3. Складіть усний діалог за однією із ситуацій спілкування (не менше 
> п’яти реплік від кожного/кожної учасника/учасниці діалогу). 
> ••
> Вам дали завдання вирвати бур’ян на шкільній клумбі й полити кві-
> ти. Ваші однокласник чи однокласниця хочуть перекласти на вас усю 
> роботу. Переко

## Дні тижня (Days of the Week)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 77
> 2. Допоможи Щебетунчикові вставити пропущені назви 
> днів тижня. Перевір їх написання за словником. Спиши 
> текст,  підкресли  орфограми  в  дібраних  словах.
> Якщо до слова не можна дібрати перевірне слово,
> то його написання треба перевіряти за словником.
> Тиждень починає … .  Після нього приходить … .
> За ним настає … . Четвертий день тижня — … .
> А п’ятий — … . П’ять днів працюємо, а в … і … 
> відпочиваємо.
> 3. Прочитай і розв’яжи задачу Родзинки.
> Марійка з дідусем вирушили в похід на третій 
> день

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  Запишіть відповіді на запитання. Підкресліть слова, що відпо­
> відають на питання скільки? котрий? котра? котре? Як

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 41
> Лексикологія.  Омоніми
> Запрошуємо на  концерт мешканців і  гостей городу!
> Вам потрібен лише один час раз в  неділю!
> Це вірна відповідь.
> Треба щодня читати на  протязі години.
> Макаронні вироби з  муки вищого сорту.
> Вітання з  чемпіонату миру!
> Відпочинок на  любий смак!
> Українське слово
> Слово з  іншої мови
> неділя — день тижня
> рос.  неделя (укр.   — тиждень)
> інтелігентний  — освічений; 
> розумово розвинутий; культурний
> англ.  intelligent (укр.   — 
> розум­ний) 
> диван — предмет меблів
> польськ.  dyw

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 79
> 4   Пригадай назви днів тижня. Запиши їх правильно, користуючись 
> орфографічним словником.  
> 5   Знайди у тлумачному словнику значення 
> трьох невідомих тобі слів і запиши їх.
> 	 	
> 6   Запиши подані слова в абетковій 
> послідовності.
> 	 	
> 3   Прочитайте прізвища сучасних українських 
> дитячих письменників та письменниць.
> 	
>   Запиши ці прізвища в абетковій послідовності.
> 	
>   З допомогою дорослих назви твори цих авторів (авторок). 
> 	
>   Підкресли орфограми  у словах.
> 	
>   Спробуй скласти речен

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 97
> 2. Спишіть перше речення. Розберіть його за частинами 
> мови і поширте прикметниками.
> 3. Прочитайте і спишіть подані нижче слова. Усно поставте 
> до них питання. З’ясуйте, чи є ці слова спорідненими. 
> Доведіть свою думку.
> П’ятеро, п’ять, п’ятірка, п’ятий, уп’ятьох, уп’яте, п’ят-
> ниця, п’ятдесят, п’ятсот.
> п’ятдеся’т
> п’ятсо’ т
> 206. 1. Із поданих складів утвори і запиши спільнокореневі 
> слова. До яких частин мови вони належать?
> 2. Спиши приказку. Про кого так кажуть? 
>  
>   Сім п’ятниць на тиждень.

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> РОЗДІЛ 1
> 38
> 17
> 18
> 2
> 20
> 7
> 1
> 2
> 5
> 11
> 14
> 17
> 18
> 24
> 8
> 19
> 23
> 3
> 4
> АРХЕОЛОГІЧНІ

## Місяці і пори року (Months and Seasons)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 105
>  
>  Послухайте текст Антоніни Назаренко «Який це 
> місяць?» і дайте відповідь на запитання, яке міститься 
> в заголовку.
>  Про які зміни в природі розповідає Антоніна 
> Назаренко?
>  З чого зрозуміло, що це рання весна?
>  Як же називається цей весняний місяць?
> Весна днем красна.
> Притрушує, пригрітих, сльозяться, передчуттям, підтри- 
> мують, повернувшись.
> Прочитай правильно
> 48
> Степан Мацюцький
> У  ГОСТЯХ  У  ВЕСНИ
> Ще ховаються по байраках сірі брили злежаного снігу. 
> Уночі морозець притрушує білою

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> ЧИСЛІВНИК
> -  
>  
>  
>  
>  - 
>   
>  
>  
>  
> ....
> ^\Ґ| Ч ислівник як частина мови
> 254. Прочитайте запитання.
> Скільки місяців має рік? Скільки днів має тиждень? 
> Який за порядком лічби день тижня вівторок? Котра на 
> малюнку за порядком лічби лялька в рожевій сукні, 
> котра — у блакитній, а котре — яблуко? Які числа ви бачи­
> те на листках календаря?
> 2015
> ВЕРЕСЕНЬ
> 2
> Середа
> 2015
> ВЕРЕСЕНЬ
> З
> Четвер
> •  З

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Дні тижня (Days of the Week)` (~300 words)
- `## Місяці і пори року (Months and Seasons)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
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

**Required:** понеділок, вівторок, середа (Mon, Tue, Wed), четвер, п'ятниця (Thu, Fri), субота, неділя (Sat, Sun), тиждень (week, m), зима, весна, літо, осінь (winter, spring, summer, autumn)
**Recommended:** січень, лютий, березень (Jan, Feb, Mar), квітень, травень, червень (Apr, May, Jun), липень, серпень, вересень (Jul, Aug, Sep), жовтень, листопад, грудень (Oct, Nov, Dec), день народження (birthday)

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
