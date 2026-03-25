# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **32: Transport** (A1, A1.5 [Places]).

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
module: a1-032
level: A1
sequence: 32
slug: transport
version: '1.1'
title: Transport
subtitle: Автобус, метро, таксі — getting around
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Name common transport types (автобус, метро, таксі, потяг, трамвай)
- Buy a ticket and ask about routes
- Use їхати + transport expressions (їхати автобусом / на метро)
- Combine transport with direction (куди) and locative (де) from M29-31
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Getting to the train station: — Як дістатися до вокзалу? — Їдьте
    автобусом або на метро. — Який автобус? — Номер сім. Зупинка ось там. — Дякую!
    — На здоров''я! Transport vocabulary in practical context.'
  - 'Dialogue 2 — Buying a ticket: — Один квиток до Львова, будь ласка. — В один бік
    чи туди й назад? — Туди й назад. Скільки коштує? — П''ятсот гривень. — О котрій
    відправлення? — О дев''ятій ранку. Combines transport + numbers (M11) + time (M22).'
- section: Транспорт (Transport Types)
  words: 300
  points:
  - 'City transport: автобус (bus, m), тролейбус (trolleybus, m), трамвай (tram, m),
    метро (metro, n — indeclinable), маршрутка (minibus, f), таксі (taxi, n — indeclinable).
    Intercity: потяг (train, m), автобус (bus), літак (plane, m).'
  - 'How to say ''by transport'': їхати автобусом / тролейбусом / трамваєм (instrumental
    chunk — not grammar). їхати на метро / на таксі / на машині (на + locative chunk).
    Note: both patterns mean ''by'' — learn each transport with its pattern.'
- section: Корисні фрази (Useful Phrases)
  words: 300
  points:
  - 'At the station/stop: Зупинка (stop/station), Де зупинка автобуса? (Where''s the
    bus stop?) квиток (ticket), Один квиток, будь ласка. (One ticket, please.) Скільки
    коштує квиток? (How much is a ticket?) Коли наступний потяг? (When is the next
    train?)'
  - 'On the way: Яка це зупинка? (What stop is this?) Мені виходити тут? (Do I get
    off here?) Вибачте, як дістатися до...? (Excuse me, how do I get to...?) прямо
    (straight), направо (right), наліво (left).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Transport communication: Types: автобус, метро, таксі, потяг, трамвай. By: автобусом
    / на метро (two patterns). Buying: Один квиток до... Скільки коштує? Asking: Де
    зупинка? Як дістатися до...? Self-check: How do you get to work? Buy a train ticket
    to Lviv.'
vocabulary_hints:
  required:
  - автобус (bus, m)
  - метро (metro, n)
  - таксі (taxi, n)
  - потяг (train, m)
  - квиток (ticket, m)
  - зупинка (stop, f)
  recommended:
  - трамвай (tram, m)
  - маршрутка (minibus, f)
  - літак (plane, m)
  - направо (right)
  - наліво (left)
  - прямо (straight)
  - дістатися (to get to)
activity_hints:
- type: quiz
  focus: Which transport? Match situation to transport type.
  items: 8
- type: fill-in
  focus: 'Buy a ticket: Один ___ до ___, будь ласка.'
  items: 6
- type: quiz
  focus: Автобусом or на метро? Choose the right pattern.
  items: 6
- type: fill-in
  focus: 'Ask for directions: Як дістатися до ___?'
  items: 6
connects_to:
- a1-033 (Around the City)
prerequisites:
- a1-031 (Where To?)
grammar:
- 'Transport instrumental chunks: автобусом, потягом'
- 'Transport на chunks: на метро, на таксі'
- 'Directional phrases: прямо, направо, наліво'
register: розмовний
references:
- title: Anna-led — transport and travel vocabulary
  notes: Practical communication for getting around Ukrainian cities.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Transport
**Module:** transport | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 146
> Завмерли трамваї, тролейбуси стали,
> автомобілі загальмували...
> Не їде ніхто, не йде, не біжить —
> рух зупинився навколо умить.
>  
>  
>  
>  
>  
>  
>     Оксана Сенатович
> трамва’й
> троле’йбус
> 2. Як, на вашу думку, птахи могли зупинити рух на вулицях 
> міста?
> 310. 1. Розгляньте малюнки. Прочитайте і спишіть речення.
> Вранці Андрійко збирається до школи. Він одягається, 
> взувається.
> Вранці Андрійко збирає братика до дитячого садка. Він 
> одягає та взуває малюка.
> дисциплі’на
> гардеро’ б
> 2. Які дієслова називают

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 208
> Відомості із синтаксису й пунктуації.  Види речень за емоційним забарвленням
> Вправа 339
> 1.	 Прочитайте новину.
> ДОЇХАЛИ КОМФОРТНО?  
> ПОДЯКУЙТЕ ЕКІПАЖУ!
> «Марафон взаємоввічливості» оголосила Вінницька тран-
> спортна компанія. Тепер пасажири й  пасажирки можуть 
> віддячити за  чемність у  трамваї, тролейбусі та  автобусі, 
> проголосувавши за  найвідповідальніший екіпаж міського 
> громадського транспорту. Якщо їдете у вінницькому тран-
> спорті, знайдіть плакат із  номером екіпажу й  відскануйте 
> QR-к

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
> 272.1. Як, на твою думку, можна удосконалити сучасні автомобілі? 
> Прочитай текст.
> Як ти гадаєш, що чекає людей у майбутньому? Можливо, 
> вони літатимуть, як птахи? Чи плаватимуть, як риби? Чи бігати­
> муть, як найпрудкіші звірі?
> Але це станеться не відразу. Тому нашим надійним поміч­
> ником залишиться звичний для нас транспорт. Звісно, він теж 
> зміниться. Уявляєш, варто буде лише подумати про те, що вже 
> час вирушати до школи, як біля ґанку з’явиться твій власний 
> автомобіль! Він усміхнеться, запит

> **Source:** unknown, Grade 5
> **Score:** 0.33
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
> **Score:** 0.33
>
> § 52. Правильне вживання числівниківна позначення дат і часу   
> 247
> — Наш поїзд оголосили! Ходімо швидше! І  на табло 
> вже є!
> — Не поспішай, ми встигаємо. Зараз 07.05.
> — Який у  нас вагон?
> — 7-й.
> 2. Попросіть у дорослих або знайдіть у мережі «Інтернет» залізнич-
> ний квиток, дайте відповідь на запитання: у  якому вагоні їдуть ман-
> дрівники, коли вони приїжджають у  пункт призначення, яка вартість 
> квитка, чи сплачено за послуги (білизна, чай).
> Вправа 501
> 1. Прочитайте електронного листа.
> 17:25
> 93

## Транспорт (Transport Types)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 146
> Завмерли трамваї, тролейбуси стали,
> автомобілі загальмували...
> Не їде ніхто, не йде, не біжить —
> рух зупинився навколо умить.
>  
>  
>  
>  
>  
>  
>     Оксана Сенатович
> трамва’й
> троле’йбус
> 2. Як, на вашу думку, птахи могли зупинити рух на вулицях 
> міста?
> 310. 1. Розгляньте малюнки. Прочитайте і спишіть речення.
> Вранці Андрійко збирається до школи. Він одягається, 
> взувається.
> Вранці Андрійко збирає братика до дитячого садка. Він 
> одягає та взуває малюка.
> дисциплі’на
> гардеро’ б
> 2. Які дієслова називают

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 208
> Відомості із синтаксису й пунктуації.  Види речень за емоційним забарвленням
> Вправа 339
> 1.	 Прочитайте новину.
> ДОЇХАЛИ КОМФОРТНО?  
> ПОДЯКУЙТЕ ЕКІПАЖУ!
> «Марафон взаємоввічливості» оголосила Вінницька тран-
> спортна компанія. Тепер пасажири й  пасажирки можуть 
> віддячити за  чемність у  трамваї, тролейбусі та  автобусі, 
> проголосувавши за  найвідповідальніший екіпаж міського 
> громадського транспорту. Якщо їдете у вінницькому тран-
> спорті, знайдіть плакат із  номером екіпажу й  відскануйте 
> QR-к

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 88
> транспорту у великих містах, фактично варіант залізниці, 
> лінії якого можуть бути розташовані під землею й на землі; 
> автомобіль громадського користування з оплатою проїзду 
> за лічильником (таксометром).
> 205   Ознайомтеся зі змістом таблиці. Доповніть її власними при -
> к ладами.
> Рід незмінюваних іменників
> Правило
> Чоловічий рід
> Жіночий рід
> Середній рід
>  Назви осіб
> кюре, рантьє, 
> денді, конфе-
> рансьє, маестро 
> леді, мадам, 
> міледі, міс, 
> пані, фрау
>   Назви тварин 
> і птахів 
> (якщо стать 
> не вказ

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 272.1. Як, на твою думку, можна удосконалити сучасні автомобілі? 
> Прочитай текст.
> Як ти гадаєш, що чекає людей у майбутньому? Можливо, 
> вони літатимуть, як птахи? Чи плаватимуть, як риби? Чи бігати­
> муть, як найпрудкіші звірі?
> Але це станеться не відразу. Тому нашим надійним поміч­
> ником залишиться звичний для нас транспорт. Звісно, він теж 
> зміниться. Уявляєш, варто буде лише подумати про те, що вже 
> час вирушати до школи, як біля ґанку з’явиться твій власний 
> автомобіль! Він усміхнеться, запит

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 209
> Відомості із синтаксису й пунктуації. Види речень за емоційним забарвленням
> 2. Знайдіть і  прочитайте речення з  такими характеристиками: розповідні 
>  неокличні й окличні, питальні неокличні й окличні, спонукальні неокличні 
> й  окличні . Чи всі типи речень є  в  цьому тексті?
> 3. Сформулюйте 5 правил поведінки в громадському транспорті, використо-
> вуючи спонукальні неокличні речення . Скористайтеся різними джерелами 
> інформації: інтернет, література, опитування серед дорослих .
> Наприклад: Зах

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 34
> Лексикологiя.  Фразеологiя
> Пр
> Слова, що властиві мовленню людей певної 
> професії, називають професійними. НАПРИКЛАД:
> оранка, плуг, озимин
> о
> а (з мовлення працівників
> сільського господарства); боцман, швартові, 
> палуба (з мовлення моряків).
> Існує професійна лексика лікарів, учителів, юрис-
> тів, водіїв, шахтарів, бухгалтерів, акторів тощо.
> І. Прочитайте текст. Визначте ключові слова. Що нового для себе ви ді-
> зналися із цього тексту? 
> ПЕРШИЙ ТРАМВАЙ
> Перші трамваї з’явилися ще на початку ХІХ сто

## Корисні фрази (Useful Phrases)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 60
> 1. Читалочка і Щебетунчик по-різному записали закін-
> чення у виділеному слові. Визнач, хто з них помилився.
> Скористайся правилом.
> 2. Спиши речення з попереднього завдання, дібравши по-
> трібне закінчення у виділеному слові. Поясни свій вибір.
> 2
> 3. Спиши словосполучення, розкривши дужки. Познач
> закінчення у змінених словах. Із трьома з них склади
> й  запиши  речення.
> 3
> багато (машина)  
>  
> нових (зустріч)
> цікавих (подорож) 
>  
> високих (гора)
> ДОСЛІДЖУЮ  ЗАКІНЧЕННЯ  ІМЕННИКІВ 
> ДОСЛІДЖУЮ  ЗАКІНЧЕННЯ

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 166
> Зверніть увагу!
> У питальному окличному реченні ставимо знак питан-
> ня і знак оклику. НАПРИКЛАД: Ліси мої, хто вас убереже?! 
> (О. Пахльовська).
> ПУНКТОГРАМА
> З

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Транспорт (Transport Types)` (~300 words)
- `## Корисні фрази (Useful Phrases)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

**Required:** автобус (bus, m), метро (metro, n), таксі (taxi, n), потяг (train, m), квиток (ticket, m), зупинка (stop, f)
**Recommended:** трамвай (tram, m), маршрутка (minibus, f), літак (plane, m), направо (right), наліво (left), прямо (straight), дістатися (to get to)

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
