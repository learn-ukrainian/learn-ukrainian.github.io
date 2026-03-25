# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **38: Іду, їду, лечу** (A2, A2.6 [Aspect, Tenses, and Motion]).

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
module: a2-038
level: A2
sequence: 38
slug: motion-verbs
version: '1.0'
title: Іду, їду, лечу
subtitle: Дієслова руху та моделі дієвідмінювання з чергуванням основи
focus: grammar
pedagogy: PPP
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
- Learner can distinguish between unidirectional (іти, їхати, летіти) and
  multidirectional (ходити, їздити, літати) motion verbs and use each type
  correctly based on whether the motion is one-way/in-progress or habitual/
  round-trip.
- Learner can conjugate all three base motion pairs in present tense and form
  their perfective partners with the prefix по- (піти, поїхати, полетіти).
- Learner can conjugate three irregular verb models — казати → кажу (stem
  consonant change), пити → п'ю (irregular contraction), боротися → борюся
  (-отися reflexive) — and apply these patterns to similar verbs.
- Learner can use motion verbs with appropriate prepositions and cases to
  describe direction (іти до школи, їхати на роботу, летіти в Україну).
content_outline:
- section: Три пари дієслів руху (Three Pairs of Motion Verbs)
  words: 500
  points:
  - 'Ukrainian distinguishes one-way motion (right now, in one direction) from
    habitual/round-trip motion. This is NOT about speed or distance — it is
    about the nature of the trip.'
  - 'Pair 1 — on foot: іти (going right now, one direction) vs. ходити (going
    regularly, back and forth). Я іду до магазину (I am walking to the store
    right now). Я ходжу до магазину щодня (I go to the store every day).'
  - 'Pair 2 — by vehicle: їхати (riding/driving right now) vs. їздити (riding
    regularly). Ми їдемо до Львова (We are driving to Lviv). Ми їздимо до
    Львова щоліта (We go to Lviv every summer).'
  - 'Pair 3 — by air: летіти (flying right now) vs. літати (flying regularly/
    in general). Літак летить до Києва (The plane is flying to Kyiv). Він
    часто літає до Києва (He often flies to Kyiv).'
- section: Дієвідміна та доконаний вид (Conjugation and Perfective Forms)
  words: 500
  points:
  - 'Present tense conjugation of all six verbs. іти: іду, ідеш, іде, ідемо,
    ідете, ідуть. ходити: ходжу, ходиш, ходить, ходимо, ходите, ходять.'
  - 'їхати: їду, їдеш, їде, їдемо, їдете, їдуть. їздити: їжджу, їздиш,
    їздить, їздимо, їздите, їздять.'
  - 'летіти: лечу, летиш, летить, летимо, летите, летять. літати: літаю,
    літаєш, літає, літаємо, літаєте, літають.'
  - 'Perfective with по-: піти (to leave on foot), поїхати (to leave by
    vehicle), полетіти (to fly off). Він пішов додому (He left for home).
    Вона поїхала на роботу (She left for work). Літак полетів (The plane
    took off).'
- section: 'Моделі дієвідмінювання: казати, пити, боротися (Conjugation Models)'
  words: 550
  points:
  - 'Model 1 — Stem consonant change (казати → кажу): the з → ж alternation
    affects the ENTIRE present tense stem (1st conjugation pattern). Full
    conjugation: кажу, кажеш, каже, кажемо, кажете, кажуть. Similar verbs:
    писати → пишу, пишеш (с → ш throughout), сказати → скажу, скажеш.'
  - 'Model 2 — Irregular contraction (пити → п''ю): the stem reduces and
    takes the contracted endings. Full conjugation: п''ю, п''єш, п''є,
    п''ємо, п''єте, п''ють. Similar verbs: бити → б''ю, лити → ллю.'
  - 'Model 3 — Reflexive -отися (боротися → борюся): the reflexive particle
    -ся stays attached throughout. Full conjugation: борюся, борешся,
    бореться, боремося, боретеся, борються. Note the от → ор stem change.'
  - 'Why these models matter: Ukrainian has predictable consonant alternations
    (з/ж, с/ш, т/ч, д/дж) that appear across many verbs. Learning the pattern
    once unlocks dozens of verbs.'
- section: Рух + прийменники + відмінки (Motion + Prepositions + Cases)
  words: 450
  points:
  - 'Direction TO: іти/їхати до + Gen. (до школи, до друга), на + Acc.
    (на роботу, на пошту), в/у + Acc. (в Україну, у місто).'
  - 'Direction FROM: іти/їхати з + Gen. (зі школи, з роботи), від + Gen.
    (від друга).'
  - 'Through/along: через + Acc. (через парк), по + Loc. (по вулиці).'
  - 'Practical dialogues: Куди ти їдеш? — Їду на роботу. Звідки ти йдеш? —
    Іду з магазину. Як ти їдеш? — Автобусом (Instr.).'
vocabulary_hints:
  required:
  - іти / ходити (to go on foot — unidirectional/multidirectional)
  - їхати / їздити (to go by vehicle — unidirectional/multidirectional)
  - летіти / літати (to fly — unidirectional/multidirectional)
  - піти (to leave on foot — pf.)
  - поїхати (to leave by vehicle — pf.)
  - казати / кажу (to say — stem change model)
  - пити / п'ю (to drink — irregular model)
  - боротися / борюся (to fight/struggle — reflexive model)
  - напрямок (direction)
  - рух (movement, motion)
  recommended:
  - чергування (alternation)
  - однонапрямний (unidirectional)
  - різнонапрямний (multidirectional)
  - звідки (from where)
activity_hints:
- type: group-sort
  focus: Sort motion verb forms into unidirectional vs. multidirectional categories
  items: 6
- type: fill-in
  focus: Complete sentences with the correct motion verb form based on whether
    the action is one-way/now or habitual/round-trip
  items: 6
- type: quiz
  focus: Conjugate казати, пити, and боротися — choose the correct form for the
    given person and number
  items: 6
- type: match-up
  focus: Match motion verbs with the correct preposition and case for direction
    (до + Gen., на + Acc., з + Gen.)
  items: 6
references:
- title: Заболотний Grade 7, §39-41
  notes: Дієвідміни дієслів, чергування приголосних при дієвідмінюванні
- title: 'Ohoiko, Verbs of Motion with Prefixes (2024)'
  notes: Chart of іти/ходити, їхати/їздити, летіти/літати + prefix system

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Іду, їду, лечу
**Module:** motion-verbs | **Phase:** A2.6 [Aspect, Tenses, and Motion]
**Textbook grades searched:** 1, 2, 3, 5

---

## Три пари дієслів руху (Three Pairs of Motion Verbs)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 36
> Бачу  Ї, ї. Чую  [й], [і].
> Ї ї
> у к р а ї
> У к р а
> К и ї в
> ї
> *
> н
> н а
> і
>  [ –•| = •– ] 
> сво
> тво
> мо
> Ї
> м
> ж
> жа
> жак
> сти
> їжа		
> 	
>   мої   	 	
> доїхав   
>  [ =•|–• ] 
>  [ –•| =•]  
>  [ –•| =•|–•– ] 
> Їжак, їжаченя
> Їздять по гриби щодня.
> Їжачиха помагає —
> Сироїжки їм збирає (нар. тв.).
> Скоромовка
> 	
> Прочитай скоромовку.
> 	 Які звуки позначає буква, виділена червоним 
> кольором? Вимов ці звуки. 
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
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

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 152
> Досліди, як змінюються 
> дієслова за часами.
> Я — дослідник
> Я — дослідниця
> Навчаюся змінювати дієслова за часами
> міркували
> міркуємо
> будемо міркувати
> 6   Прочитай слова і порівняй їх.
> Що означає дієслово? Коли відбувається дія?
> На яке питання відповідає дієслово?
> До якої часової форми належить кожне дієслово?
>   Зроби висновок, як змінювати дієслова за часами, і звір його з таблицею.
> Час дієслів
> Питання
> Приклади
> Теперішній час
> що роблю?
> що робиш?
> що робить?
> що роблять?
> лечу, пишу
> летиш, пишеш

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 27
>  § 10. Лексичне  значення  слова
> 1. Прочитайте діалог між братом і молодшою сестрою та виконайте зав­
> дання. 
> — На вулиці посіріло, зірвався вітер, мабуть, зараз піде дощ!
> — Піде?! А хіба дощ може ходити? 
> А. Через яке слово сестра не зрозуміла брата?
> Б. Яка причина непорозуміння?
> Лексичне значення — це те, що означає слово. Наприклад, лексичне 
> значення слова дощ — різновид опадів, що випадають із хмар у вигляді 
> краплин води. 
> Лексичне значення слів можна з’ясувати за тлумачним словником.

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 30
> Знайди слово до схеми. 
> 	
> їжа	
> ї-жа-чи-ха	
> ї-хав	
> Ки-їв
> 	 їжак	
> ї-жа-че-ня	
> по-ї-хав	
> У-кра-ї-на
> 	 їжаки	 си-ро-їж-ка	
> по-їзд	
> у-кра-їн-ці
> 
> 	 Один — багато
> Які слова називають багато предметів?
> 	 гай — гаї	
> музей — музеї
> 	 чай — чаї	
> трамвай — трамваї 
> 
> Заголовок. Передбачення 
> Чому їжачок колючий? Що було б, якби він був без голок? 
> Одяг для їжачка
> У сім’ї їжаків на-ро-ди-ло-ся їжаченя. Ма-
> лень-ке, пу-хна-сте, зовсім без голок. Їжак та 
> ї-жа-чи-ха су-му-ва-ли. З’їсть лисичка ї-жа-че-ня.

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 53
> • Продовж діалог. Запиши кілька реплік діалогу в зошит. 
> Пробач. 
> Я вчинив негарно.
> Дякую, що 
> вибачився.
> • Випиши слова — назви дій. 
> Зразок. Квіти (що роблять?) пнуться, ... .
> • Назви слова, які описують стани людини. Склади з двома 
> словами речення.
> Боїться, радіє, бігає, цікавиться, співає, дивується, танцює.
> сЛова — назви ДІЙ
> Що ти робиш у школі, удома, на вулиці? Запиши слова — 
> назви дій у стовпчики.
> Читаю, читання, пишу, письмо, малюю, малювання, 
> стрибаю, граю, гра, співаю, танцюю, т

## Дієвідміна та доконаний вид (Conjugation and Perfective Forms)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 94
> Бачу Д, д (де). Чую [д], [д'].
> д р і * д
> д * т е л
> дро-ва
> две-рі
> до-ріж-ка схо-ди
> ве-ран-да
> л е * і д *
>  [ –    =  • –  – ]
>  [ = • |  –•  – ]
>  [ – • |  =•  =  ]
> а
> о
> у
> и
> і
> Д
> да
> до
> ду
> ди
> ді
> а
> о
> у
> и
> і
> ад
> од
> уд
> ид
> ід
> Д
> бу-ди-нок
> під-ві-кон-ня
> дах
> ди-мар
> Д д

> **Source:** unknown, Grade 2
> **Score:** 0.50
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

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 127
> ÐÎÇÐ²ÇÍßÞ ÐÎÇÏÎÂ²ÄÍ², 
> ÐÎÇÐ²ÇÍßÞ ÐÎÇÏÎÂ²ÄÍ², 
> ÏÈÒÀËÜÍ² ² ÑÏÎÍÓÊÀËÜÍ² 
> ÏÈÒÀËÜÍ² ² ÑÏÎÍÓÊÀËÜÍ² 
> ÐÅ×ÅÍÍß, ÎÊËÈ×Í² É ÍÅÎÊËÈ×Í² 
> ÐÅ×ÅÍÍß, ÎÊËÈ×Í² É ÍÅÎÊËÈ×Í² 
> 1. Прочитай речення. Визнач, яке з них є розповідним,
> яке — питальним, а яке — спонукальним. Перевір себе 
> за правилом.
> 1. Яке місто відвідали друзі?
> 2. Друзі милувалися Полтавою. 
> 3. Дізнайтеся, що цікавого є в Полтаві.
> Речення, 
> у 
> якому 
> про 
> щось 
> розповідається 
> (повідомляється),  називається  розповідним. 
> Речення, у якому про щось за

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 26
> 48.	 Доберіть якнайбільше синонімів до слів: 
> 1) іти (роблячи кроки, пересуватися);
> 2) говорити (передавати щось словами); 
> 3) швидкий (який швидко біжить, летить тощо).
> 49.	 І. Доберіть по 2–3 синоніми до кожного з поданих слів. Утворені 
> синонімічні ряди запишіть. Визначте відмінність у відтінках лексичного 
> значення (якщо вони є) синонімів одного з рядів.
> Радісний, ввічливий, думати, завірюха, повільно.
> ІІ. Із двома синонімами одного ряду (на вибір) складіть і запишіть ре-
> чення.
> 50.	 І. П

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 36
> Бачу  Ї, ї. Чую  [й], [і].
> Ї ї
> у к р а ї
> У к р а
> К и ї в
> ї
> *
> н
> н а
> і
>  [ –•| = •– ] 
> сво
> тво
> мо
> Ї
> м
> ж
> жа
> жак
> сти
> їжа		
> 	
>   мої   	 	
> доїхав   
>  [ =•|–• ] 
>  [ –•| =•]  
>  [ –•| =•|–•– ] 
> Їжак, їжаченя
> Їздять по гриби щодня.
> Їжачиха помагає —
> Сироїжки їм збирає (нар. тв.).
> Скоромовка
> 	
> Прочитай скоромовку.
> 	 Які звуки позначає буква, виділена червоним 
> кольором? Вимов ці звуки. 
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
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

## Моделі дієвідмінювання: казати, пити, боротися (Conjugation Models)

> **Source:** unknown, Grade 1
> **Score:** 0.50
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
> **Score:** 0.50
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
> б| Розглянь малюнки

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Три пари дієслів руху (Three Pairs of Motion Verbs)` (~500 words)
- `## Дієвідміна та доконаний вид (Conjugation and Perfective Forms)` (~500 words)
- `## Моделі дієвідмінювання: казати, пити, боротися (Conjugation Models)` (~550 words)
- `## Рух + прийменники + відмінки (Motion + Prepositions + Cases)` (~450 words)
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

**Required:** іти / ходити (to go on foot — unidirectional/multidirectional), їхати / їздити (to go by vehicle — unidirectional/multidirectional), летіти / літати (to fly — unidirectional/multidirectional), піти (to leave on foot — pf.), поїхати (to leave by vehicle — pf.), казати / кажу (to say — stem change model), пити / п'ю (to drink — irregular model), боротися / борюся (to fight/struggle — reflexive model), напрямок (direction), рух (movement, motion)
**Recommended:** чергування (alternation), однонапрямний (unidirectional), різнонапрямний (multidirectional), звідки (from where)

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
