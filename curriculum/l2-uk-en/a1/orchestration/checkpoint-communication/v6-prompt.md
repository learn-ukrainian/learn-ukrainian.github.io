# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **47: Checkpoint: Communication** (A1, A1.7 [Communication]).

**Target: 1000–1500 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1000+ words
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
7. **Hit the word target** — you MUST write 1000–1500 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a1-047
level: A1
sequence: 47
slug: checkpoint-communication
version: '1.1'
title: 'Checkpoint: Communication'
subtitle: Can you address people, give instructions, and connect ideas?
focus: review
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1000
objectives:
- Use vocative to address people correctly (Олено! Тарасе! Друже!)
- Give instructions and make requests using imperative (Читай! Дайте!)
- Connect ideas with conjunctions (і, а, але, бо, тому що)
- Build complex sentences with що, де, коли
- Use holiday greetings and vocabulary in context
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M42-M46: Can you call someone by name using vocative? (M42)
    Can you ask someone to do something? (M43) Can you connect ideas with і, а, але,
    бо? (M44) Can you build sentences with що, де, коли? (M45) Can you name Ukrainian
    holidays and greet people? (M46)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using all A1.7 skills. Content: Olena calls her friend
    Taras to plan a holiday celebration. She uses vocative (Тарасе!), imperatives
    (Прийди! Принеси!), conjunctions (бо ми святкуємо, але я не знаю, коли ти вільний),
    and holiday vocabulary (Різдво, кутя, колядки). Combines all A1.7 communication
    tools in one realistic scenario.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.7: 1. Vocative: -а→-о (Олено), hard→-е (Тарасе), soft→-ю
    (Андрію) (M42) 2. Imperative: ти (читай, дай), ви (читайте, дайте) (M43) 3. Coordinating:
    і/та (and), а (contrast), але (but), бо (because) (M44) 4. Subordinating: що (that),
    де (where), коли (when) + comma (M45) 5. Holiday greetings: З + instrumental (З
    Різдвом!) (M46)'
- section: Діалог (Connected Dialogue)
  words: 200
  points:
  - 'Planning a holiday gathering: — Олено, привіт! Ти знаєш, що скоро Різдво? — Так,
    Тарасе! Я думаю, що ми можемо святкувати разом. — Добре! Скажи, коли ти вільна,
    бо я хочу запросити друзів. — Я вільна двадцять четвертого. Але я не знаю, де
    ми будемо. — Ходімо до мене! Принеси кутю, будь ласка. — Добре, принесу! І я знаю,
    де купити гарні свічки. З Різдвом! Uses vocative, imperative, conjunctions, що/де/коли,
    and holidays.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'A1.7 achievement summary: You can address people properly in Ukrainian. You can
    ask people to do things, politely and informally. You can connect your ideas into
    longer, natural sentences. You can build complex sentences with що, де, коли.
    You can talk about Ukrainian holidays and congratulate people. Next: A1.8 — Past,
    Future, Graduation.'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: fill-in
  focus: 'Vocative + imperative: ___(Олена), ___(читати) цей текст, будь ласка!'
  items: 8
- type: quiz
  focus: 'Choose the conjunction: Я не йду, ___ хворий. (і / а / бо / що)'
  items: 8
- type: fill-in
  focus: 'Complete complex sentences: Я знаю, ___ він тут. Скажи, ___ ти прийдеш.'
  items: 6
- type: quiz
  focus: 'Holiday match: З Різдвом! / З Великоднем! — match greeting to holiday'
  items: 8
connects_to:
- a1-048 (next module in A1.8)
prerequisites:
- a1-046 (Holidays)
grammar:
- 'Review: vocative case (M42), imperative mood (M43)'
- 'Review: coordinating conjunctions і, а, але, бо (M44)'
- 'Review: subordinating conjunctions що, де, коли (M45)'
- 'Review: holiday greetings З + instrumental (M46)'
register: розмовний
references:
- title: Synthesis of M42-M46 content
  notes: No new material — review and integration of A1.7 phase.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Communication
**Module:** checkpoint-communication | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Що ми знаємо? (What Do We Know?)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 120
> Щоб визначити в реченні другорядні члени, необхідно 
> пам’ятати такі правила:
> 1) додаток залежить від члена речення, вираженого 
> дієсловом або іменником (Керівники (чого?) сайту 
> карають (кого?) порушників баном); 
> 2) означення залежить від члена речення, вираженого 
> іменником (Боти навмисне створюють багато про-
> філів під різними іменами. Іменами (якими?) 
> різними); 
> 3) обставини конкретизують дію, а тому залежать від 
> члена речення, вираженого дієсловом (Є боти також 
> (де?) у соціальних мер

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> І якраз у яму 
> втрапить. А ми вже вириємо, постараємося.

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 24
> 24
> слухаємо 
> прогноз погоди
> отримуємо 
> інформацію
> розповідаємо 
> про погоду
> передаємо 
> інформацію
> беремо в дорогу 
> парасольку
> використовуємо
> інформацію
> телеканал   газета
> соціальна мережа
> державна установа
> посадова особа
> документ
> рекламний щит
> учасник події
>  енциклопедія
>   книга
>   буклет
>   банер
>  вебсайт 
> Зверніть увагу!
> рете інформацію. Будь-хто може записати відео, але це зовсім
> не робить людину експертом з того чи того питання, про яке
> вона говорить. НАПРИКЛАД, коли йдеться про військові по

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 35
> 77
>   Чи знайома вам ситуація вибору? Чим ви керуєтеся, приймаючи 
> рішення? Чи завжди враховуєте результат і чи берете на себе 
> за це відповідальність? Висловіть припущення, що станеться, 
> якщо ви цю тему вивчите старанно або якщо ви її проігноруєте. 
> Наведіть приклади вдалого і невдалого вибору. Зверніть увагу 
> на «слова дня». Які з них допомагають під час вибору, а які  — 
> шкодять?
> Пригадуємо:
> 1   Що вам відомо про написання слів іншомовного 
> походження?
> 2   Які з іншомовних запозичень корис

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> — А так, бо ще опівночі з дзеркала ворожать, але це вже, 
> так сказати, ворожба грішна.
> — Чому?
> — А пригадайте собі, як воно є в Шевченковій «Тополі»: 
> «Не питайте свою долю, само серце знає, кого любить…» 
> Я нікому не раджу ворожити з дзеркала опівночі поміж дво-
> ма горючими свічками. (…)
> Тому-то я кажу, що така ворожба — це гріх. І най Бог бо-
> ронить, щоби з вас котра зважилася на таке діло.
> — А правда воно, тітусю?
> — А невже ми знаємо, діти, що правда, а що ні?
> Шафковий годинник тікав, поліна

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 226
> Розвиток мовлення
> Сучасні планшети можуть мати один із
> трьох основних типів матриць: TFT, IPS або
> OLED. Кут огляду в IPS-матрицях стано-
> вить трохи менше 180, а зображення – со-
> ковите з гарною передачею кольору. На від-
> міну від IPS, зображення на OLED-дисплеї
> більш контрастне, з ідеальною передачею
> чор ного кольору.
> * * *
> Чому до вишиванки ставляться з такою 
> повагою та любов’ю?
> По-перше, вишиванка ідеально поєдну-
> ється з будь-яким одягом: шкільною фор-
> мою, джинсами, шортами різних фасо

## Читання (Reading Practice)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 114
> Комунікативні можливості речень
> 291   Прочитайте текст. Про що в ньому йдеться? Які емоції викликає 
> у вас це свято? Які очікування і передчуття у вас напередодні 
> Різдва? Які речення за метою висловлювання використовує 
> письменниця? Чому? Напишіть, що для вас означає це свято.
> Різдво для мене — це не просто біблійний сюжет, можли-
> вість замислитися над мудрістю Божого промислу, занурити-
> ся в його барвистість. Це набагато більше. Бо моєму Різдву 
> не одна тисяча літ. Воно з житніх нив та з т

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 11. Казки завжди мають щасливий фінал. Який він у творі Г. Пагутяк?
>  12. Визнач тему та ідею твору.
> Домашнє завдання (два на вибір)
>  
> 1. Назви прислів’я, наведені на початку розділу, які відповідають 
> казці Г. Пагутяк.
>  
> 2. Постав по одному запитанню різного виду до твору і дай 
> відповіді на них.
>  
> 3. Намалюй «хмарку слів», запиши в ній риси характеру Діда і Баби.
>  
> 4. Продовж казку Г. Пагутяк та запиши це продовження в ро-
> бочий зошит.
>  Ти — творча особистість
>  
>  Зимовий цикл свят є найбільш по

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 162
> Протягом навчання в школі ви ще матимете щасливу нагоду ознайоми-
> тись не лише із творами поетеси для дітей, які склали збірочку «Бузино вий 
> цар», але й з «дорослими» поезіями та романами. Читайте уважно. Бо за 
> кожним рядком поезій Ліни Костенко – відкрита для болю ду ша і непід-
> робна щирість, історія української душі і пристрасна думка, високе мис-
> тецтво, за яким ми  давно вже визначаємо справжнє мірило прекрасного...
> ЧАЙКА НА КРИЖИНІ
> В цьому році зима
> Не вдягала білої свити.
> Часом вже

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 144
> 345   Складіть і запишіть по три словосполучення зі «словами дня». 
> Що вам відомо про «читацький смак», «хист до читання»? 
> 346   Запишіть речення. Знайдіть із-поміж них прості, речення з одним 
> головним членом і складні. 
> 1. Книжку читають не очима, а розумом. 2. У книжці 
> шукай не букви, а думки. 3. Книжка дає крила (Нар. твор-
> чість). 4. Книжки — найбільш мовчазні й найвірніші друзі; 
> вони — найдоступніші й наймудріші порадники і найтерпля-
> чіші вчителі (Ч.-У. Еліот). 5. Багатьох життєвих

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 10
> ПІСЕННІ СКАРБИ РІДНОГО КРАЮ
> Освіжає, звеселяє, молодить.
> Серце завмирає, дух перехоплює. 
> Краса.
> 10.	 Домашнє завдання.
> 1.	 Які українські традиції та обряди ви знаєте? Опишіть одну/один із них 
> (усно).
> 2.	 Дослідіть пісню «Ой весна, весна — днем красна» за планом. 
> Ой весна, весна — днем красна 
> — Ой весна, весна — днем красна. 
> Що ж ти нам, весно, принесла?
> — Принесла я вам літечко,
> Ще й рожевую квіточку,
> Хай вродиться житечко,
> Ще й озимая пшениця,
> І усякая пашниця. 
> — Ой весна, весна, ти к

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 150
> 150
> привітно, яблуневоцвітно
> б
> (П. Тичина). 3. День догоряв хризан-
> темно, айстрово (І. Коваленко). 4. Життя проходить без по дійно,
> так заметільно, сніговійно (І. Коваленко). 5. I джмели но,
> і бджолино урочисто хор співа, і якась мала пташина про мовля 
> святі слова (I. Коваленко). 6. А веселка проста і велична сонце-
> барвно із хмар вироста (П. Перебийніс).
> ІІ. Спишіть останнє речення. Підкресліть члени речення. 
> ІІІ. Спробуйте утворити нові прислівники від наявних у мові слів. Складіть 
> з о

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 226
> 515   Прочитайте тексти. Визначте наміри мовців. Розподіліть ролі 
> і прочитайте тексти виразно.
> — Дай Боже щастя, 
> дідусю!
> — Дякую, внучку! Дай 
> Боже і тобі!
> — Зашпиліть куртку, 
> бо застудитеся. Сьогодні 
> холодно. І не нудно вам 
> отут 
> так 
> замітати? 
> Щодня одне й те саме.
> — 
> Ні, 
> хлопчику, 
> я люблю свою роботу. 
> Подивися, яка чудова 
> осінь. Яке гарне барвис-
> те 
> листя, 
> як 
> твій 
> портфель. 
> Уяви 
> собі, 
> що в світі нема двох 
> однакових листочків, як 
> і людей. Господь кожно-
> го створив неповт

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 144
> Прикметник
> І. Прочитайте виразно вірш. За допомогою яких художніх засобів автору
> вдалося передати любов до матері? Поясніть роль прикметників у тексті.
> МАТЕРІ
> В хаті сонячний промінь косо
> На долівку ляга з вікна...
> Твої чорні шовкові коси
> Припорошила вже сивина.
> Легкі зморшки обличчя вкрили –
> Це життя трудового плід.
> Але в кожному русі – сила,
> В очах юності видно слід.
> Я таку тебе завжди бачу,
> Образ в серці такий несу –
> Материнську любов гарячу
> І твоєї душі красу.

> **Source:** unknown, Grade 7
> **S

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~200 words)
- `## Підсумок — Summary` (~150 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1000 words minimum.

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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it), Subordinate clauses (plan teaches them), Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary



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
