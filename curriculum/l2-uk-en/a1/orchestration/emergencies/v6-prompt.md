# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **54: Emergencies** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-054
level: A1
sequence: 54
slug: emergencies
version: '1.2'
title: Emergencies
subtitle: Допоможіть! Викличте швидку! — survival Ukrainian
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Call for help using key emergency phrases (Допоможіть! Викличте...)
- Call 112 and explain a basic emergency in Ukrainian
- Ask for help at a pharmacy, hospital, or police station
- Give basic personal information in an emergency (name, address, phone)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Calling 112: — Служба порятунку, слухаю вас. — Допоможіть! Тут аварія!
    Людина не рухається! — Де ви? — На вулиці Хрещатик, біля метро Майдан Незалежності.
    — Зрозуміло. Швидка вже їде. Як вас звати? — Мене звати Адам. Мій номер — нуль
    дев''яносто три... — Дякую. Залишайтеся на місці. Emergency call: location + problem
    + personal info.'
  - 'Dialogue 2 — Lost documents: — Вибачте, де тут поліція? — Поліція? Прямо і наліво.
    — Дякую! (at the station) Добрий день. Я загубив паспорт. — Де ви його загубили?
    — Я не знаю. Може, в метро. — Як ваше прізвище? — Сміт. Адам Сміт. — Ваш номер
    телефону? — Нуль дев''яносто три, п''ятсот двадцять один... — Добре. Заповніть
    цю форму, будь ласка. Police station: reporting a lost document.'
- section: Екстрені ситуації (Emergencies)
  words: 300
  points:
  - 'Emergency number: 112 (один один два) — works everywhere in Ukraine. Key phrases
    (learn as chunks!): Допоможіть! (Help! — formal/plural imperative) Викличте швидку!
    (Call an ambulance!) Викличте поліцію! (Call the police!) Тут аварія! (There''s
    an accident here!) Тут пожежа! (There''s a fire here!) Людині погано! (Someone
    is feeling bad!) Мені потрібна допомога! (I need help!)'
  - 'Giving your location: Де ви? — Where are you? Я на вулиці... (I''m on ... street.)
    Я біля... (I''m near...) Я в метро... (I''m in the metro...) Адреса: вулиця Хрещатик,
    будинок десять. (Address: Khreshchatyk street, building 10.) Use places vocabulary
    from A1.5 (біля, навпроти, поруч).'
- section: Допомога (Getting Help)
  words: 300
  points:
  - 'At the hospital / лікарня: Мені потрібен лікар. (I need a doctor.) У мене болить...
    (My ... hurts — from M53.) У мене алергія на... (I''m allergic to...) Я не розумію.
    Повторіть, будь ласка. (I don''t understand. Please repeat.) Ви говорите англійською?
    (Do you speak English?)'
  - 'Personal information for emergencies: Мене звати... (My name is...) Моє прізвище...
    (My surname is...) Мій номер телефону... (My phone number is...) Я з [country].
    (I''m from [country].) Мій паспорт... / Я загубив/загубила паспорт. (My passport...
    / I lost my passport.) Мій готель — ... (My hotel is...) All review from previous
    modules — applied to a critical situation.'
- section: Summary
  words: 300
  points:
  - 'Emergency survival kit: 112 — universal emergency number. Допоможіть! (Help!)
    Викличте швидку / поліцію! Тут аварія / пожежа! Location: Я на вулиці... Я біля...
    At hospital: У мене болить... Мені потрібен лікар. At police: Я загубив/загубила
    [document]. Personal info: ім''я, прізвище, номер телефону, країна, адреса. Self-check:
    Practice a 112 call — state the problem, give your location, give your name.'
vocabulary_hints:
  required:
  - допомога (help, f)
  - допоможіть (help! — imperative)
  - швидка (ambulance, f — short for швидка допомога)
  - поліція (police, f)
  - лікарня (hospital, f)
  - аварія (accident, f)
  - загубити (to lose)
  - викликати (to call/summon)
  recommended:
  - пожежа (fire, f)
  - порятунок (rescue, m)
  - паспорт (passport, m)
  - адреса (address, f)
  - номер (number, m)
  - алергія (allergy, f)
  - форма (form/document, f)
  - будинок (building, m)
activity_hints:
- type: quiz
  focus: Choose the correct emergency phrase for the situation.
  items:
  - question: You see a car crash.
    options:
    - Тут аварія! Викличте швидку!
    - Тут пожежа! Допоможіть!
    - Я загубив паспорт.
  - question: You see a building on fire.
    options:
    - Тут пожежа! Допоможіть!
    - Тут аварія!
    - Мені потрібен лікар.
  - question: Someone is feeling very ill on the street.
    options:
    - Людині погано! Викличте швидку!
    - Викличте поліцію!
    - Я загубив паспорт.
  - question: You cannot find your passport at the airport.
    options:
    - Я загубив паспорт.
    - Тут аварія!
    - Мені потрібна швидка.
  - question: Someone stole your wallet.
    options:
    - Викличте поліцію! Допоможіть!
    - Тут пожежа!
    - Мені потрібен лікар.
- type: fill-in
  focus: Complete the emergency phone call.
  items:
  - Алло! {Допоможіть|Дякую|Вибачте}! Тут аварія!
  - '{Викличте|Загубив|Потрібен} швидку допомогу!'
  - Я на {вулиці|лікарні|поліції} Хрещатик, біля метро.
  - Мене {звати|прізвище|адреса} Адам.
  - Мій номер {телефону|паспорта|будинку} — нуль дев'яносто три...
  - Мені потрібна {допомога|пожежа|аварія}!
- type: order
  focus: Put the dialogue with the 112 operator in the correct order.
  items:
  - — Служба порятунку, слухаю вас.
  - — Допоможіть! Тут пожежа!
  - — Де ви?
  - — На вулиці Шевченка, будинок п'ять.
  - — Зрозуміло. Швидка і пожежники вже їдуть. Як вас звати?
  - — Мене звати Анна. Дякую!
- type: fill-in
  focus: Reporting an issue at the police station or hospital.
  items:
  - Добрий день. Я {загубив|викличте|допоможіть} паспорт.
  - Моє {прізвище|ім'я|номер} — Сміт.
  - Мені {потрібен|погана|хворий} лікар.
  - У мене {алергія|пожежа|аварія} на ці таблетки.
  - Я не розумію. {Повторіть|Допоможіть|Викличте}, будь ласка.
connects_to:
- a1-055 (A1 Finale)
prerequisites:
- a1-053 (Health)
grammar:
- 'Emergency imperatives: Допоможіть! Викличте! Повторіть! (review from M43)'
- 'Location phrases: на вулиці, біля, в метро (review from A1.5)'
- Мені потрібен/потрібна (I need — chunk, no grammar analysis)
register: розмовний
references:
- title: State Standard 2024, §3
  notes: 'Thematic area: health and safety — emergency situations.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Emergencies
**Module:** emergencies | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
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
> **Score:** 0.50
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
> **Score:** 0.50
>
> 242
> 242
> Як бачиш, усе триває менше як дві десяті секунди. Тому без
> необхідних запобіжних заходів людина не має шансів вижити в 
> такій аварії.
> Тому правила дорожнього руху визначають: якщо в тран-
> спорті передбачені ремені безпеки, то пасажири зобов’язані при-
> стебнутися.
> (З підручника «Основи здоров’я». І. Бех та ін.)
> * ДТП (дорожньо-транспортна пригода) – подія, що сталася під
> час руху транспортного засобу, унаслідок якої загинули або поранені
> люди чи завдані матеріальні збитки.
> Текст Б
> В Украї

> **Source:** unknown, Grade 5
> **Score:** 0.33
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
> 133
> § 59–60. Прислівник.  Розряди   прислівників  за  значенням  (практично)
> 10.	Складіть і розіграйте діалог із гостем / гостею міста Харкова. 
> А.	 Допоможіть зорієнтуватися в метро (за однією з поданих ситуацій).
> 1. Треба дістатися від станції «Майдан Конституції» до станції «Перемога».
> 2. Як дістатися від станції «Захисників України» до станції «Київська»?
> Б.	 Використайте формули подяки з прислівниками міри і ступеня дії.
>                                                  Формули подяки
> Дуже в

## Екстрені ситуації (Emergencies)

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
> **Score:** 0.50
>
> 5. Мені допоміг друг, проживаю-
> чий неподалік. 6. На стадіон прийшли хлопці, бажаючі грати 
> у футбол. ІІ. Доберіть кілька прикладів неправильного вживання дієприслівників або діє-
> прикметників у рекламних оголошеннях. Виправте помилки. 527 
> 528 
> 529 
> 530

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 222
> Відомості із синтаксису й пунктуації. Обставина
> Вправа 361
> Виконайте тест . У завданнях 1 і 2 лише один правильний варіант відповіді, 
> у  завданні 3 потрібно встановити відповідність між варіантами .
> 1. Обставинами є  усі виділені слова, ОКРІМ
> Поки ми їдемо до Києва, я думаю про неї. Зараз восьма ве-
> чора, а значить, прабабуня вечеряє. У кімнаті цокає годинник 
> і про щось торохтить радіо.
> А до Києва
> Б зараз
> В у кімнаті
> Г про щось
> 2. Непоширеним є  речення
> А Створіть своє родинне дерево через

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 228
> Розвиток мовлення
> мовленнєвого етикету. Використайте звертання та слова (сполучення) увічли-
> вості. Ви можете скористатися поданими нижче зразками.
> СИТУАЦІЯ А. Ви перебуваєте в незнайомому місті й шукаєте потрібну вулицю 
> (будівлю). З якими словами ви звернетеся до перехожого? Що скажете на про-
> щання?
> Скажіть, будь ласка, де...; перепрошую, ви не знаєте...; вибачте, 
> ви не скажете...; добродію, будьте ласкаві, підкажіть...; шановний, 
> якщо ваша ласка, скажіть мені...; дякую вам; на все добр

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 228
> 228
> Відредагуйте усно речення. Поясніть суть допущених помилок.
> 1. Просимо відповідати за чергою. 2. Відділ по розкриттю 
> зло чинів знаходиться в сусідньому приміщенні. 3. Моя сестра 
> старша мене на два роки. 4. Ми прийшли по їх проханню. 5. Не 
> годиться жити на чужий рахунок. 6. Маринка допустила дві 
> помилки по неуважності. 7. На канікулах я не поїхала до бабусі 
> завдяки тому, що захворіла. 8. Згідно розпорядження директо-
> ра завтра буде вихідний.
> Придумайте, дотримуючись поданих критеріїв

## Допомога (Getting Help)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 91
>  § 38–39.  Наголос.  Орфоепічна  помилка
> А. З’ясуйте лексичне значення виділених слів. 
> Б. Визначте в кожному рядку слово, на яке падає логічний наголос. Ви­
> разно прочитайте вірш повторно, посилюючи голос на виділених 
> словах. 
> В. Опишіть своїми словами, як Л. Костенко в поезії зображає природу 
> (її стан, атмосферу), який настрій викликав вірш у вас, яку проблему 
> в ньому порушено (письмово; п’ять–сім речень).
> Культура слова
> •	 Розрізняйте за значенням слова лікарський, лікарський і лікарня

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 89
> Iменник
> І. Запишіть словосполучення, добираючи правильне закінчення.
> Головн(ий/а) біль, нов(ий/а) шампунь, нелегк(ий/а) путь,
> вищ(ий/а) ступінь, вітальн(ий/а) туш, яскрав(ий/а) гуаш,
> сильн(ий/а) нежить, біл(ий/а) тюль, гірк(ий/а) полин, бара-
> бан н(ий/а) дріб, нов(ий/а) рукопис, друг(ий/а) степінь,
> яскрав(ий/а) емаль, висок(ий/а) насип.
> ІІ. Складіть усно речення з одним поданим словосполученням.
> СИТУАЦІЯ. Уявіть, що вам треба викликати 
> лікаря для знайомого, який застудився

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Екстрені ситуації (Emergencies)` (~300 words)
- `## Допомога (Getting Help)` (~300 words)
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

**Required:** допомога (help, f), допоможіть (help! — imperative), швидка (ambulance, f — short for швидка допомога), поліція (police, f), лікарня (hospital, f), аварія (accident, f), загубити (to lose), викликати (to call/summon)
**Recommended:** пожежа (fire, f), порятунок (rescue, m), паспорт (passport, m), адреса (address, f), номер (number, m), алергія (allergy, f), форма (form/document, f), будинок (building, m)

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
