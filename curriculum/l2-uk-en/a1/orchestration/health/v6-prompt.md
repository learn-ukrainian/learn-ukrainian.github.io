# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **53: Health** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-053
level: A1
sequence: 53
slug: health
version: '1.2'
title: Health
subtitle: У мене болить голова — body parts and symptoms
focus: vocabulary
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Name basic body parts in Ukrainian (голова, рука, нога, живіт, горло, спина)
- Describe symptoms using "У мене болить..." as a chunk
- Tell a doctor or pharmacist what hurts
- Use basic health vocabulary in practical situations
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — At the doctor''s: — Що у вас болить? — У мене болить голова і горло.
    — Давно? — З учора. І в мене температура. — Ви кашляєте? — Так, трохи. І в мене
    нежить. — Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! — Дякую, лікарю!
    Doctor visit: symptoms + basic diagnosis.'
  - 'Dialogue 2 — At the pharmacy: — Добрий день! У мене болить голова. Дайте, будь
    ласка, таблетки. — Від головного болю? — Так. І від кашлю, будь ласка. — Ось,
    будь ласка. Ще щось? — А є щось від нежиті? — Так, ось краплі. — Дякую! Скільки
    це коштує? Pharmacy: asking for medicine using known polite forms.'
- section: Тіло (The Body)
  words: 300
  points:
  - 'Essential body parts (Grade 1-2 textbooks: частини тіла): голова (head, f), горло
    (throat, n), спина (back, f), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot,
    f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m). Note: рука = whole
    arm including hand. нога = whole leg including foot. These are the most useful
    for A1 — not an anatomy lesson.'
  - 'Body part gender matters for adjectives (review from M09): велике око (big eye
    — neuter), великий ніс (big nose — masc), велика рука (big hand — fem). But at
    A1, focus on recognition — you''ll use these mainly with болить.'
- section: У мене болить... (It Hurts...)
  words: 300
  points:
  - 'The magic phrase: У мене болить + body part. У мене болить голова. (I have a
    headache. — literally ''at me hurts head'') У мене болить живіт. (My stomach hurts.)
    У мене болить горло. (My throat hurts.) У мене болить спина. (My back hurts.)
    У мене болить зуб. (I have a toothache.) Learn this as a CHUNK — don''t analyze
    the grammar (that''s dative, A2+).'
  - 'Common symptoms (as chunks): У мене температура. (I have a fever.) У мене кашель.
    (I have a cough.) У мене нежить. (I have a runny nose.) Мені холодно. (I''m cold.)
    Мені погано. (I feel bad.) Я хворий/хвора. (I''m sick. — masc/fem) Note: ''У мене
    болять зуби'' (teeth hurt — plural form болять). Just recognize it.'
- section: Summary
  words: 300
  points:
  - 'Health toolkit: Body parts: голова, горло, живіт, спина, рука, нога, око, вухо,
    зуб, ніс. Symptoms: У мене болить [body part]. У мене температура/кашель/нежить.
    State: Я хворий/хвора. Мені погано. At the doctor: Що у вас болить? — У мене болить...
    At the pharmacy: Дайте таблетки від [symptom], будь ласка. від головного болю
    (for headache), від кашлю (for cough), від нежиті (for runny nose). Self-check:
    How do you say ''My throat hurts and I have a fever''?'
vocabulary_hints:
  required:
  - голова (head, f)
  - горло (throat, n)
  - живіт (stomach, m)
  - рука (hand/arm, f)
  - нога (leg/foot, f)
  - болить (hurts — chunk: у мене болить)
  - лікар (doctor, m)
  - аптека (pharmacy, f)
  recommended:
  - спина (back, f)
  - око (eye, n)
  - вухо (ear, n)
  - зуб (tooth, m)
  - ніс (nose, m)
  - температура (fever/temperature, f)
  - кашель (cough, m)
  - нежить (runny nose, f)
  - таблетка (pill, f)
  - хворий (sick, adj)
activity_hints:
- type: match-up
  focus: Match body parts to their English translations.
  items:
  - голова == head
  - живіт == stomach
  - горло == throat
  - спина == back
  - рука == hand/arm
  - нога == leg/foot
  - зуб == tooth
  - око == eye
- type: fill-in
  focus: Complete the sentence with the correct symptom or body part.
  items:
  - У мене болить {голова|рука|нога}. Я хочу спати.
  - У мене болить {живіт|вухо|око}. Я не хочу їсти.
  - У мене болить {горло|спина|ніс} і є температура. Я не можу говорити.
  - У мене {кашель|нежить|зуб}, я постійно кашляю.
  - У мене болить {зуб|голова|нога}, мені потрібен стоматолог.
  - Я {хворий|лікар|аптека}. У мене болить голова і спина.
- type: quiz
  focus: Choose the logical response to the health problem.
  items:
  - question: У мене болить голова.
    options:
    - Ось таблетки від головного болю.
    - Ось краплі від нежиті.
    - Випийте сироп від кашлю.
  - question: У мене сильний кашель.
    options:
    - Вам потрібні таблетки від кашлю.
    - Ось краплі для носа.
    - У мене болить зуб.
  - question: Що у вас болить?
    options:
    - У мене болить горло.
    - Я лікар.
    - Де аптека?
  - question: Добрий день. Дайте, будь ласка, щось від нежиті.
    options:
    - Ось краплі, будь ласка.
    - У мене болить спина.
    - Це таблетки від головного болю.
- type: fill-in
  focus: At the pharmacy or doctor - using target chunks.
  items:
  - Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю.
  - Що у вас {болить|хворий|лікар}?
  - У мене {температура|аптека|лікар} і болить горло.
  - Мені {погано|хворий|добре}. Викличте лікаря!
  - Де тут найближча {аптека|голова|спина}? Мені потрібні ліки.
connects_to:
- a1-054 (Emergencies)
prerequisites:
- a1-052 (My Story)
grammar:
- У мене болить + body part (impersonal chunk — no grammar analysis)
- Body part gender for adjective agreement (recognition only)
- Я хворий/хвора (gender agreement in short adjectives)
register: розмовний
references:
- title: State Standard 2024, §3
  notes: 'Thematic area: health (здоров''я) — body parts, symptoms, doctor visits.'
- title: 'Grade 1-2 textbook: Частини тіла'
  notes: Body parts vocabulary with pictures.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Health
**Module:** health | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 147
> ослаблення імунітету. Крім того, якщо вранці ви не поїли, 
> будьте певні, що за обідом з’їсте мінімум у два рази більше, 
> ніж зазвичай.
> Привчіть себе їсти не раніше, ніж через пів години після 
> пробудження. Уставши з ліжка, випийте пів склянки теплень-
> кої води. Це активізує процеси життєдіяльності в організмі. 
> Можна додати у воду кілька крапель лимонного соку. По-
> тім займіться звичними справами: прийміть душ, одягніться, 
> зберіть сумку. За цей час шлунок почне працювати – і ви від-
> чуєте л

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Послухавши пульс, вона підняла мені сорочку, схилилась і приклала 
> маленьке холодне вухо до моїх грудей. Вона завжди вислу­ховувала хво-
> рих просто так, вухом, без усякого лікарського причан­далля. І тільки вислухавши мене, вона сказала весело:
> — Молодець! Усе гаразд! Скоро будеш здоровий. І ляснула мене долонею по пузі. — Еге! Гаразд! — буркнув я. — Оно вже і їсти не можу. Організм не прий­
> має. І голова крутиться, підвестися несила. — Що? — вона здивовано глянула на тарілки, що стояли на стіль

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> А вже б і 
> пора! – Ось нате вам, – соромлячись, виймаю квіти із шапочки й 
> подаю вчительці.

> **Source:** unknown, Grade 5
> **Score:** 0.33
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
> **Score:** 0.33
>
> його сумнi, повнi тихої резигнацiї оченята, прошептали менi 
> його повiльнi рухи тi несамовито страшнi слова:
> — Ах, моя весна пропала! Я в неволi! Знаю вже, знаю, 
> чим-то воно скiнчиться!
> I вiдтодi я не можу позбутися сього спомину. Вiн затроює 
> менi кожну хвилину щастя, розбиває мою силу i вiдвагу 
> в нещастi. Вiн мучить моє сумлiння грижею, i менi здаєть-
> ся, що все дурне, безцiльне, жорстоке i погане, що я тiльки 
> коли зробив у своїм життi, скристалiзувалося в конкретний 
> образ отсього малого,

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

## Тіло (The Body)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 105
> Фонетика. Графіка. Орфоепія. Орфографія. Фонетика . Звуки мовлення
> Вправа 152
> Назвіть три органи з перелічених, не  задіяні у  вимові звуків .
> Язик, зуби, нога, губи, права рука, нижня щелепа, підне-
> біння, очі.
> Вправа 153
> 1. Прочитайте уривок вірша Оксани Лущевської .
> Я — МОВ ЗАЙЧИК
> Я — мов зайчик: ніс рожевий, великі вуха,
> довкола принюхуюся і прислухаюся,
> а серце теленькає-теленькає:
> я всього боюся.
> Вітер дмухне: «Хоч би не ураган…»
> Дощ накрапає: «Аби не злива…»
> Звідкись грюкне: «Лише б н

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 74
> 1.	Прочитайте слова в колонках і виконайте завдання. 
> світанок 
> зелень
> свіжість  
> світанковий 
> зелений
> свіжий  
> світати
> зеленіти 
> свіжішати
> А.	 За яким принципом розподілено слова в колонки?
> Б.	 На яке питання відповідають слова кожної колонки? 
> В.	 Опрацюйте матеріал таблиць «Частини мови» на першому форзаці. 
> САМОСТІЙНІ  ТА  
> СЛУЖБОВІ  ЧАСТИНИ 
> МОВИ
> § 39
> МОРФОЛОГІЯ. 
> ОРФОГРАФІЯ
> Морфологія — це розділ науки про мову, що вивчає слова як час­
> тини мови. Більшість термінів на позначення частин

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> Ух! Очі мої лізуть на лоба: я відчуваю, як жабеня, пірнувши в живіт, 
> починає веселий свій танок десь аж біля пупа (...).

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 31
>  § 11–12.  Слово  як  частина  мови
> А. Уявіть, що ви працюєте диктором / дикторкою на радіо. Навчіться ви­
> разно читати цей текст, дотримуючись відповідної інтонації. 
> Б. Перегляньте документальний фільм «Микола Сядристий — найкра­
> щий мініатюрист світу» і перекажіть його (усно). 
> Культура слова
> •	 Розрізняйте слова книга і книжка. Книга велика за розміром: енцикло­
> педія, альбом із репродукціями картин, літопис, Біблія та ін. А книжками 
> називають підручники, посібники, художні твори та ін.

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 117
>  Відповідно до запитань сформулюйте особисті цілі. 
> 282   Прочитайте текст, визначте, про яку пору року йдеться? Спишіть, 
> уставляючи потрібні, на вашу думку, прикметники. На  що вони 
> вказують? Порівняйте поданий і доповнений тексти. Яку роль 
> відіграють прикметники? Назвіть у записаному тексті словоспо-
> лучення, у яких прикметники вжиті в переносному значенні. Роз-
> кажіть про свій вихідний день, використовуючи якомога більше 
> прикметників. 
> Неділя. Ранок. Сиджу вдома. Дивлюсь у вікно. А за

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> Самостійні частини мови
> ЧАСТИНИ МОВИ (МОРФОЛОГІЯ)
> Частина мови
> Позначення
> Питання
> Приклади
> Іменник
> ім’я людини, наймен-
> ня предмета чи явища хто? що? Катерина, телефон, 
> вітер
> Прикметник
> прикмета когось або 
> чогось
> який? чий? щасливий, Максимів
> Числівник
> число або порядок 
> при лічбі
> скільки? котрий? п’ять, сімнадцятий
> Займенник
> замість іменника,  
> прикметника або 
> числівника
> хто? що? який? чий? скільки? котрий? ти, дещо, цей, мій, 
> жоден, котрий
> Дієслово:
> • неозначена форма 
> (інфінітив)
> • особов

## У мене болить... (It Hurts...)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 2 ВгатAити грAеблю – 
> перегородити 
> річку. 3 ГлухAий кут – тут: 
> кут у хаті, де 
> сходяться дві 
> стіни без вікон. 4 ПідкурAити – тут: 
> обдати димом.

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Послухавши пульс, вона підняла мені сорочку, схилилась і приклала 
> маленьке холодне вухо до моїх грудей. Вона завжди вислу­ховувала хво-
> рих просто так, вухом, без усякого лікарського причан­далля. І тільки вислухавши мене, вона сказала весело:
> — Молодець! Усе гаразд! Скоро будеш здоровий. І ляснула мене долонею по пузі. — Еге! Гаразд! — буркнув я. — Оно вже і їсти не можу. Організм не прий­
> має. І голова крутиться, підвестися несила. — Що? — вона здивовано глянула на тарілки, що стояли на стіль

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 80
> 80
> Зверніть увагу! 
> Написання не з деякими дієсловами залежить від лексичного
> значення слова. 
> нездужати (хворіти)
> неславити (ганьбити)
> непокоїтися (хвилюватися)
> не здужати (не змогти)
> не славити (не прославляти)
> не покоїтися (не бути похова-
> ним, схованим де-небудь)
> ОРФОГРАМА
> Не з дієсловами
> ПРИМІТКА. Про написання не з дієприкметниками йтиметься в наступних па-
> раграфах.
> І. Прочитайте прислів’я. Обґрунтуйте написання не з дієсловами.  
> 1. На чужій стерні кінь не напасеться. 2. І сокіл вище

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 147
> ослаблення імунітету. Крім того, якщо вранці ви не поїли, 
> будьте певні, що за обідом з’їсте мінімум у два рази більше, 
> ніж зазвичай.
> Привчіть себе їсти не раніше, ніж через пів години після 
> пробудження. Уставши з ліжка,

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Тіло (The Body)` (~300 words)
- `## У мене болить... (It Hurts...)` (~300 words)
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

**Required:** голова (head, f), горло (throat, n), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot, f), {'болить (hurts — chunk': 'у мене болить)'}, лікар (doctor, m), аптека (pharmacy, f)
**Recommended:** спина (back, f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m), температура (fever/temperature, f), кашель (cough, m), нежить (runny nose, f), таблетка (pill, f), хворий (sick, adj)

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
