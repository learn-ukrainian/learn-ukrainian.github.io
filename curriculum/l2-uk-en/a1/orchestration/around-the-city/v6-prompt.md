# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **33: Around the City** (A1, A1.5 [Places]).

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
module: a1-033
level: A1
sequence: 33
slug: around-the-city
version: '1.2'
title: Around the City
subtitle: Де/куди + directions — navigating in Ukrainian
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Combine Де? (locative) and Куди? (accusative) in real navigation
- Give and follow simple directions
- Describe your neighborhood and daily routes
- Synthesize M28-M32 skills in connected urban communication
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? —
    Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте
    на метро до центру. Combines directions + transport + city places.'
  - 'Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду
    на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п''ять
    хвилин. Робота в офісі на площі. Daily route using sequence words + transport
    + places.'
- section: Де і куди разом (Where and Where To Together)
  words: 300
  points:
  - 'Real navigation uses both cases together: Я зараз у парку (де? — locative). Я
    йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative).
    Потім їду на роботу (куди? — accusative). The constant switch between де? and
    куди? is natural Ukrainian.'
  - 'Preposition patterns (synthesis): | Situation | Question | Form | | Static |
    Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By
    transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко /
    близько / пішки |'
- section: Мій район (My Neighborhood)
  words: 300
  points:
  - 'Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин.
    Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму
    районі є кафе, ресторан і бібліотека.'
  - 'Useful phrases for city life: пішки (on foot), хвилина (minute) — П''ять хвилин
    пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці
    (in the center / on the outskirts).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо,
    направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом,
    на метро, пішки. Self-check: Describe your route from home to work/school.'
vocabulary_hints:
  required:
  - пішки (on foot)
  - хвилина (minute, f)
  - район (neighborhood, m)
  - центр (center, m)
  - вибачте (excuse me)
  recommended:
  - дістатися (to get to)
  - ідіть (go! — imperative, preview)
  - їдьте (go by transport! — imperative, preview)
  - поруч (nearby)
  - навпроти (opposite)
  - між (between)
activity_hints:
- type: fill-in
  focus: Give directions using прямо, направо, наліво
  items: 6
  blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
- type: quiz
  focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
- type: fill-in
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
- type: match-up
  focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
connects_to:
- a1-034 (Where From?)
prerequisites:
- a1-032 (Transport)
grammar:
- 'Synthesis: Де? (locative) + Куди? (accusative) in real navigation'
- Direction + transport + location combined
- 'Imperative preview: ідіть, їдьте (formal commands)'
register: розмовний
references:
- title: Synthesis of M28-M32 skills
  notes: Applied communication — no new grammar, just integration.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Around the City
**Module:** around-the-city | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> — Летять, кружляють, танцюють, не гріє, світить, па6
> дають... — школярі запропонували слова, які вказують на
> дії цих предметів, — дієслова.
> — Молодці. Прийдемо в клас і напишемо замітку в
> шкільну газету про те, що ми бачили в осінньому парку. 
> • Під час роботи над заміткою користуйтеся такими порадами: 
> — доберіть тему замітки й назву (заголовок);
> — продумайте послідовність викладу думок, складіть план;
> — звірте дати, назви, цифри, прізвища;
> — розповідайте про найважливіше чи про те, що цікаве;

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 137
> 2   Як правильно будувати діалог?
> 3   Коли діалог називають продуктивним, вдалим, гармо -
> нійним?
> Відповідно до поставлених запитань сформулюйте особисті 
> цілі.
> 330  Поміркуйте й назвіть сфери, де діалог необхідний.
> Діалог — це: 
>   різновид прямої мови;
>   розмова двох осіб.
> Діалог складається з реплік. Кожну репліку пишемо 
> з нового рядка і з великої букви.
> Перед репліками ставимо тире.
> Якщо репліку супроводжують слова автора, то стави-
> мо ті самі розділові знаки, що й при прямій мові, але

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 238
> РОЗДІ Л VІІ. СПІЛКУВАННЯ
> СПІЛКУВАННЯ: ПОВТОРЕННЯ ВИВЧЕНОГО
> § 95
> У музеях спочивають минулі часи, 
> минулі думки і турботи (із журналу).
> Таємниці музеїв
> Слово дня: старожèтності, коштîвності.
> Пригадуємо:
> 1   Що таке цілі спілкування? Наскільки вони важливі?
> 2   Назвіть ознаки результативного спілкування.
> 3   Якому спілкуванню ви надаєте перевагу? Чому?
> 4   Які виклики таїть у собі віртуальне спілкування?
> 5   Як ви убезпечуєте себе?
> 6   Назвіть складники ситуації спілкування.
> Відповідно до пост

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 6
> ЯК ЧИТАЮТЬ КНИЖКИ?
> Люди читають книжки по-різному. Одні швидко,
> інші — повільно, а деякі так швидко, ніби «ковтають» 
> сторінки.
> Швидкість читання значною мірою залежить від того, 
> що і з якою метою ми читаємо. Скажімо, підручник із 
> математики та збірку казок ти, очевидно, читаєш по-
> різному. Текст задачі, наприклад, треба прочитати не 
> поспішаючи кілька разів, щоб зрозуміти кожне слово, 
> запам’ятати дані, розібратися у змісті запитання. Без 
> цього задачу не розв’яжеш. Казку ж ти читаєш зовсім

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 248
> Відомості із синтаксису й пунктуації.  Пряма мова.  Розділові знаки в реченнях
> В трамваї хтось гаркнув бабусі на  вухо: 
> Ану, відступися убік, розвалюхо! 
> Не встигла убік відступити небога — 
> Забрала стареньку «швидка допомога». 
> Буфетнику Про шу в  дитячім кафе 
> Хтось замість подяки та  вигукнув: 
> Пфе! 
> Буфетник облишив буфет і  торти — 
> Його до  сьогодні не  можуть знайти! 
> А далі, як мовиться в  казці, 
> Заби ли триво гу будьласці. 
> Вони невідомих осіб 
> Ловили шістнадцять діб! 
> А потім

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

## Де і куди разом (Where and Where To Together)

> **Source:** unknown, Grade 4
> **Score:** 0.50
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
> **Score:** 0.50
>
> 118
> ІІ. Складіть усне висловлення за схемою, доповнивши її наведеною 
> поруч інформацією з Правил дорожнього руху. Що означають зобра­
> жені дорожні знаки? 
> Пішоходам
> заборонено
> дозволено
>  виходити на проїзну час-
> тину, не впевнившись у 
> відсутності небезпеки для 
> себе та інших учасників 
> руху
>  рухатися по тротуарах 
> і пішохідних доріжках, 
> тримаючись правого боку
>  переходити проїзну частину по пішохідних переходах, 
> а в разі їх відсутності – на перехрестях по лініях тро-
> туарів або узбіч
> 

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 3. Може, десь у лісах ти чар/зілля шукала, сонце-ру­
> ту знайшла і мене зчарувала? (В. Івасюк). 4. Для реалізації проєкту по­
> трібно скласти бізнес/план (З розмови). А. Перепишіть речення, знявши риску. Б. Надпишіть над виділеними словами спосіб їхнього творення.

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 104
> 	 Добери з тексту сполучення слів, у яких дієслова вжиті в пере-
> носному значенні. Запиши.  
> 	 Випиши речення із фразеологізмами. Який із них відповідає 
> значенню «зазнати невдачі»? Підкресли дієслова, які вжиті в 
> неозначеній формі. Познач суфікси.
> 247.		Склади й запиши три речення з дієсловами, які вжито в 
> переносному значенні.
> 248.		Прочитай дитячу мирилку.
> Вишнi спілі розвиваються,
> Синє озеро розливається,
> Ясне сонечко усмiхається,
> Жито силоньки набирається.
> 	 Добери з вірша дієслова до

> **Source:** unknown, Grade 5
> **Score:** 0.33
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
> **Score:** 0.33
>
> 193
> 193
> § 98.  Уживання  займенника ви 
> 3.	 Прочитайте текст і виконайте завдання. 
> Сашко зайшов у тихий двір лікарні. 
> Від лікарні до моря було недалеко. Сашко пройшов коридор першого 
> поверху — ніде нікого. Піднявся на другий поверх: літня жінка в білому 
> халаті натирала шваброю підлогу.
> — Здрастуйте! — привітався Сашко. — Скажіть, будь ласка, а де у вас 
> той лікар, що лікує очі. Я здалеку, і в мене мало часу. Але я хотів би з тим 
> вашим лікарем поговорити.
> — Приходьте після обіду, — відповіла

## Мій район (My Neighborhood)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 62
> Мої навчальні досягнення
> Карта пам’яті: від тексту — до мене
> Прочитайте текст.
> У Західній Україні є село На-
> гуєвичі, що недалеко від міста 
> Дрогобича. Тут народився україн-
> ський письменник Іван Франко.
> У його батька була кузня, куди 
> приходили різні люди: молоді та 
> стар­шого віку, з далеких і близь-
> ких сіл. Івась із радістю слухав 
> розповіді про давні часи України. 
> Хлопчик був дуже здібним. За 
> два роки навчився читати (укра-
> їнська), (німецька) та (польська) 
> мовами. Малий Івась записув

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 118
> ІІ. Складіть усне висловлення за схемою, доповнивши її наведеною 
> поруч інформацією з Правил дорожнього руху. Що означають зобра­
> жені дорожні знаки? 
> Пішоходам
> заборонено
> дозволено
>  виходити на проїзну час-
> тину, не впевнившись у 
> відсутності небезпеки для 
> себе та інших учасників 
> руху
>  рухатися по тротуарах 
> і пішохідних доріжках, 
> тримаючись правого боку
>  переходити пр

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Де і куди разом (Where and Where To Together)` (~300 words)
- `## Мій район (My Neighborhood)` (~300 words)
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

**Required:** пішки (on foot), хвилина (minute, f), район (neighborhood, m), центр (center, m), вибачте (excuse me)
**Recommended:** дістатися (to get to), ідіть (go! — imperative, preview), їдьте (go by transport! — imperative, preview), поруч (nearby), навпроти (opposite), між (between)

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
