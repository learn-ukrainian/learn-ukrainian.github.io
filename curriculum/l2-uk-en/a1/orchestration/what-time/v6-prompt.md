<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing 4/7 required vocab: ранок (morning, m), вечір (evening, m), день (day, m), ніч (night, f)
- NOTE: Too long: 1894 words (target: 1200, ceiling: 1800)
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **22: What Time?** (A1, A1.4 [Time and Nature]).

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
module: a1-022
level: A1
sequence: 22
slug: what-time
version: '1.1'
title: What Time?
subtitle: Котра година? О котрій? — telling time in Ukrainian
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Ask and answer "What time is it?" (Котра година?)
- Tell time on the hour and half hour
- Use "at" + time (о + locative as chunk — no case grammar)
- Schedule simple events using time expressions
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Scheduling a meeting: — Котра година? — Десята. — О котрій ти працюєш?
    — О дев''ятій. А ти? — Я працюю о десятій. — Зустрінемося о першій? Time expressions
    emerge through making plans.'
  - 'Dialogue 2 — Daily schedule: — Коли ти снідаєш? — О восьмій ранку. — А обідаєш?
    — О першій. Вечеряю о сьомій. Combining time with verbs from A1.3.'
- section: Котра година? (What Time Is It?)
  words: 300
  points:
  - 'Захарійчук Grade 4 p.117: Котра година? — ordinal numbers for hours. Full hours
    use feminine ordinal numbers (година = feminine): Перша (1:00), друга (2:00),
    третя (3:00), четверта (4:00), п''ята (5:00), шоста (6:00), сьома (7:00), восьма
    (8:00), дев''ята (9:00), десята (10:00), одинадцята (11:00), дванадцята (12:00).
    Learn these as vocabulary — the grammar behind ordinals comes later.'
  - 'Half hours and quarters: Пів на другу (1:30 — literally ''half to the second'').
    Чверть на третю (2:15). За чверть третя (2:45). At A1: focus on full hours and
    ''пів на''. Quarters for recognition only.'
- section: О котрій? (At What Time?)
  words: 300
  points:
  - '''At'' + time uses о/об + locative form (taught as chunks): О першій (at 1),
    о другій (at 2), о третій (at 3), о четвертій (at 4), о п''ятій (at 5), о шостій
    (at 6), о сьомій (at 7), о восьмій (at 8), о дев''ятій (at 9), о десятій (at 10),
    об одинадцятій (at 11), о дванадцятій (at 12). Note: об before vowels (об одинадцятій).'
  - 'Time of day words: ранку (in the morning), дня (in the afternoon), вечора (in
    the evening), ночі (at night). О сьомій ранку (at 7 AM). О третій дня (at 3 PM).
    О десятій вечора (at 10 PM). Опівдні (at noon). Опівночі (at midnight).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Telling time: Котра година? — Десята. (What time? — Ten o''clock.) О котрій?
    — О десятій. (At what time? — At ten.) Пів на другу (1:30). О пів на другу (at
    1:30). Self-check: What time is it now? When do you wake up? When do you eat lunch?
    Say 3 times in Ukrainian.'
vocabulary_hints:
  required:
  - година (hour, f)
  - котра (which — feminine, for time)
  - перша, друга, третя (1st, 2nd, 3rd — feminine ordinals)
  - ранок (morning, m)
  - вечір (evening, m)
  - день (day, m)
  - ніч (night, f)
  recommended:
  - четверта, п'ята, шоста (4th, 5th, 6th)
  - сьома, восьма, дев'ята (7th, 8th, 9th)
  - десята, одинадцята, дванадцята (10th, 11th, 12th)
  - пів (half)
  - чверть (quarter)
  - опівдні (at noon)
activity_hints:
- type: quiz
  focus: Котра година? Match clock faces to spoken time.
  items: 8
- type: fill-in
  focus: 'О котрій? Complete: Я снідаю о ___. (восьмій)'
  items: 8
- type: match-up
  focus: 'Match times: 7:00 ↔ сьома, 9:00 ↔ дев''ята'
  items: 6
- type: quiz
  focus: Ранку, дня, or вечора? Choose the right time of day.
  items: 6
connects_to:
- a1-023 (Days and Months)
prerequisites:
- a1-021 (Checkpoint — Actions)
grammar:
- Ordinal numbers for hours (feminine forms — learned as vocabulary)
- О/об + locative time expressions (memorized chunks)
- Пів на + ordinal (half-hour pattern)
register: розмовний
references:
- title: Захарійчук Grade 4, p.117
  notes: О котрій годині? Котра година? — time expressions with ordinals.
- title: Літвінова Grade 6, p.245-246
  notes: 'Full time expression system: на, по, до, пів на.'
- title: Авраменко Grade 6, p.172
  notes: 'Прийменники на позначення часу: о, за, на, по, до.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: What Time?
**Module:** what-time | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 10   Доповни загадку словами з довідки і відгадай. 
> 9   Запиши відгадані слова, познач у них закінчення. 
> 	
>   Якою темою об’єднано ці слова? Склади і запиши речення про 
> школу. Визнач у цьому слові закінчення.
> 	
>   Запиши слово-відгадку. Визнач у ньому закінчення.
> 	
>   Наведи приклади слів, які мають таке саме закінчення. Запиши їх.
> Пограйтесь  
> у слова.
> Хоч не солодкий, та дуже  ? .
> Хоч і  ? , проте дорогий.
> ?  обідати — він на столі.
> ?  його і дорослі, й малі.
> крейда
> роук   
> докаш   
> трапа

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> •  Складіть текст-розповідь за малюнком і словосполученнями. 
> Запишіть. Підкресліть словосполучення, яким позначено час.
> Правильно вимовляємо, пишемо, відповідаємо на 
> питання о котр ій год ині? котра година?
> Прокинувся о сьомій годині ранку. Чекатиму об оди­
> надцятій годині. На сімнадцяту годину прийду. Чверть 
> на третю розпочнемо. О пів на д ев’яту продзвенів 
> дзвінок (пів до дев ’ятої). За чверть хвилин дванадця­
> та година буде (чверть хвилин до дванадцятої). 
> Десять хвилин на п ’ятнадцяту го

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 193
> Відомості із синтаксису й пунктуації. Словосполучення
> 08.00
> 08.15
> 08.30
> 08.45
> 2. Усно назвіть час усіма можливими способами .
> 3. Доповніть і  розіграйте діалог про розклад дзвінків .
> — Коли починається перший урок?
> — О …
> — А закінчується?
> — …
> 4. Об’єднайтесь у  групи й  підготуйте діалоги для різних ситуацій з  вико-
> ристанням позначення часу (зустріч із друзями, відвідування спортивної 
> секції, перегляд улюбленого серіалу…) . Розіграйте ситуації перед класом . 
> Жартувати й  фантазувати можн

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 56
> 18
> Протилежні за значенням  
> слова — антоніми
> Розпізнаю протилежні 
> за значенням слова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова, які мають протилежне зна-
> чення, називаються антонімами.
> вечір — ранок
> сидіти — стояти
> вгорі — внизу
> день — ніч
> Хто швидше відгадає загадку?
> Чорна корова всіх людей поборола.
> А білий віл усіх людей побудив.
> Нових друзів май,
> Більше думай,
> Ледачий голодний,
> плакати
> схід
> запитання
> мовчати
> швидкий
> а працьовитий ситий.
> а менше говори.
> а старих не заб

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 86
> 209.		Розгляньте таблицю та обговоріть її зміст.
> 	 Склади п’ять  речень із правильними формулами на позначення 
> часу, які подані в таблиці (на вибір). Запиши.
> 210.		Прочитай слова та формули на позначення часу.
> Працював ...	
> о сьомій годині п’ятнадцять хвилин.
> Прокинулася ...	
> до тринадцятої години.
> Зателефонував ...	чверть по одинадцятій.
> Показує ...	
> о десятій годині.
> 	 З’єднай слова та формули на позначення часу. Запиши.
> 211.		Розглянь малюнки.
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8
> 3
> 9
> 6
> 10
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8

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

## Котра година? (What Time Is It?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 88
> ÇÌ²ÍÞÞ ²ÌÅÍÍÈÊÈ ÇÀ ×ÈÑËÀÌÈ
> ÇÌ²ÍÞÞ ²ÌÅÍÍÈÊÈ ÇÀ ×ÈÑËÀÌÈ
> 1. Прочитай слова. Визнач, до якої частини мови вони
> належать.
> 1
> дівчина 
>  
> дівчата 
> будинок 
>  
> будинки
> птах 
>  
>  
> птахи 
>  Проведи дослідження!
> 1. Поясни, чим відрізняються слова першої і другої колонок.
> 2. У якій колонці іменники мають форму однини?
> 3. У якій колонці іменники стоять у формі множини? Перевір 
> себе за правилом.
> Іменники змінюються за числами. 
> Іменники в однині називають один предмет.
> Наприклад: їжак, олівець.
> Іменники у мно

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 86
> 209.		Розгляньте таблицю та обговоріть її зміст.
> 	 Склади п’ять  речень із правильними формулами на позначення 
> часу, які подані в таблиці (на вибір). Запиши.
> 210.		Прочитай слова та формули на позначення часу.
> Працював ...	
> о сьомій годині п’ятнадцять хвилин.
> Прокинулася ...	
> до тринадцятої години.
> Зателефонував ...	чверть по одинадцятій.
> Показує ...	
> о десятій годині.
> 	 З’єднай слова та формули на позначення часу. Запиши.
> 211.		Розглянь малюнки.
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8
> 3
> 9
> 6
> 10
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 193
> Відомості із синтаксису й пунктуації. Словосполучення
> 08.00
> 08.15
> 08.30
> 08.45
> 2. Усно назвіть час усіма можливими способами .
> 3. Доповніть і  розіграйте діалог про розклад дзвінків .
> — Коли починається перший урок?
> — О …
> — А закінчується?
> — …
> 4. Об’єднайтесь у  групи й  підготуйте діалоги для різних ситуацій з  вико-
> ристанням позначення часу (зустріч із друзями, відвідування спортивної 
> секції, перегляд улюбленого серіалу…) . Розіграйте ситуації перед класом . 
> Жартувати й  фантазувати можн

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 138
> Поняття про числівник як частину 
> мови
> Навчаюся розпізнавати числівники
> Прочитай і розкажи у 
> класі.
> Я — учителька
> Я — учитель
> два
> дванадцять
> двадцять
> двісті
> Слова, які називають кількість предметів і відповідають 
> на питання скільки?, є числівниками. Числівник — це 
> частина мови.
> 43
> Числівники можуть називати і порядок предметів під 
> час лічби і відповідати на питання котрий?: другий, 
> дванадцятий, двадцятий, двохсотий.
> 1   Прочитай вірш Лесі Лужецької. Вивчи його напам’ять. Розкажи 
> однок

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> •  Складіть текст-розповідь за малюнком і словосполученнями. 
> Запишіть. Підкресліть словосполучення, яким позначено час.
> Правильно вимовляємо, пишемо, відповідаємо на 
> питання о котр ій год ині? котра година?
> Прокинувся о сьомій годині ранку. Чекатиму об оди­
> надцятій годині. На сімнадцяту годину прийду. Чверть 
> на третю розпочнемо. О пів на д ев’яту продзвенів 
> дзвінок (пів до дев ’ятої). За чверть хвилин дванадця­
> та година буде (чверть хвилин до дванадцятої). 
> Десять хвилин на п ’ятнадцяту го

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> Випишіть фразеологізми: перша група ‒ із 1‒3 розді-
> лів, друга  – із 4‒6 розділів, третя  – із 7‒9 розділів. Запропонуйте учасникам 
> інших груп пояснити значення виписаних вами фразеологізмів.

## О котрій? (At What Time?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 63
> 8. Спиши речення. Підкресли слова з апострофом. Випи-
> ши ті, у яких апостроф стоїть після префікса. Поділи їх на
> склади  для  переносу.
> 1. За ніч сова з’їдає до п’ятнадцяти гризунів. 
> 2. Весною на деревах з’являються молоді листочки. 
> 3. Пташка в клітці рветься, б’ється. 
> 4. Після від’їзду мами ми з нетерпінням чекали її 
> повернення.
> 1. Запиши пари споріднених слів. Познач у них закінчення, 
> основу і корінь.
> риба — рибка 
> міст — місток 
> добрий — добренький 
> ÂÈÇÍÀ×ÀÞ ÑÓÔ²ÊÑ Ó ÑËÎÂÀÕ
> ÂÈÇÍÀ×ÀÞ Ñ

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Випишіть із тексту числівники. Поставте до них питання. 
> Підкресліть наголошений склад у числівниках.
> і Потрібно правильно вживати числівники в сполученні з і 
> \ іменниками: дві, три, чотири фірми; п ’ять, шість, сім, [ 
> [ вісім, дев’ять, десять фірм; п ’яти фірмам; шістьма фір- [ 
> і мами. 
> і
> •  Складіть речення зі словосполучен

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Котра година? (What Time Is It?)` (~300 words)
- `## О котрій? (At What Time?)` (~300 words)
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

**Required:** година (hour, f), котра (which — feminine, for time), перша, друга, третя (1st, 2nd, 3rd — feminine ordinals), ранок (morning, m), вечір (evening, m), день (day, m), ніч (night, f)
**Recommended:** четверта, п'ята, шоста (4th, 5th, 6th), сьома, восьма, дев'ята (7th, 8th, 9th), десята, одинадцята, дванадцята (10th, 11th, 12th), пів (half), чверть (quarter), опівдні (at noon)

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
