# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **52: My Story** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-052
level: A1
sequence: 52
slug: my-story
version: '1.2'
title: My Story
subtitle: Я народився, я живу, я буду... — your life in three tenses
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Combine all three tenses (past, present, future) in one coherent narrative
- Tell a simple life story: where you were born, where you live, what you plan
- Use time expressions to signal tense shifts
- Understand a short biography read aloud or in text
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone deeply: — Розкажи про себе! — Я народився
    в Канаді, у Торонто. — А зараз ти живеш тут? — Так, зараз я живу в Києві. — Чому
    ти переїхав? — Я хотів вивчати українську. Мої бабуся і дідусь з України. — А
    що ти будеш робити далі? — Я буду працювати тут і вчити мову. — Чудово! Успіхів
    тобі! All three tenses in one conversation.'
  - 'Dialogue 2 — Anna''s story: — Я народилася у Львові. Там я вчилася в школі. —
    Потім я переїхала в Київ і закінчила університет. — Зараз я працюю вчителькою
    і живу в центрі міста. — А що далі? — Я буду подорожувати! Я хочу побачити Японію.
    — І ти будеш вчити японську? — Може! Але спочатку — українська для тебе! Past
    → present → future flow.'
- section: Три часи разом (Three Tenses Together)
  words: 300
  points:
  - 'Life story structure: PAST (минулий час): Я народився/народилася в... Я жив/жила
    в... Я вчився/вчилася... Я працював/працювала... PRESENT (теперішній час): Зараз
    я живу в... Я працюю... Я вивчаю... Я люблю... FUTURE (майбутній час): Я буду
    працювати... Я буду вивчати... Я буду жити...'
  - 'Signal words that mark tense shifts: Past: раніше (before), у дитинстві (in childhood),
    коли я був/була маленьким/маленькою (when I was little). Present: зараз (now),
    сьогодні (today), цього року (this year). Future: потім (then), далі (further),
    наступного року (next year). These words help the listener know which tense is
    coming.'
- section: Моя історія (My Story)
  words: 300
  points:
  - 'Model story — Taras''s life: Я народився в Одесі у тисяча дев''ятсот дев''яносто
    п''ятому році. Я жив там з батьками і сестрою. Я ходив у школу і любив математику.
    Потім я переїхав у Київ і вчився в університеті. Зараз я живу в Києві. Я працюю
    програмістом. Я люблю свою роботу. У вільний час я граю у футбол і читаю книжки.
    Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві — це
    моє місто! Past (народився, жив, ходив) → Present (живу, працюю) → Future (буду
    подорожувати).'
  - 'Your turn — tell YOUR story: Start: Я народився/народилася в [city/country].
    Past: Я жив/жила... Я вчився/вчилася... Я працював/працювала... Present: Зараз
    я живу... Я працюю... Я вивчаю українську, тому що... Future: Я буду... Я хочу...
    Use at least 3 past verbs, 3 present verbs, and 3 future constructions.'
- section: Summary
  words: 300
  points:
  - 'Three tenses — one story: Past: -в/-ла/-ло/-ли (gender endings). Я народився.
    Я жила. Present: person endings. Я живу. Ти працюєш. Вона вивчає. Future: буду
    + infinitive. Я буду працювати. Вона буде жити. Signal words: раніше → past, зараз
    → present, далі → future. Life story vocabulary: народитися (to be born), жити
    (to live), вчитися (to study), переїхати (to move), подорожувати (to travel).
    Self-check: Write your life story in 8-10 sentences using all three tenses.'
vocabulary_hints:
  required:
  - народитися (to be born)
  - жити (to live)
  - вчитися (to study)
  - переїхати (to move)
  - зараз (now)
  - раніше (before/earlier)
  - далі (further/next)
  - розповідати (to tell/narrate)
  recommended:
  - подорожувати (to travel)
  - закінчити (to finish/graduate)
  - дитинство (childhood, n)
  - університет (university, m)
  - програміст (programmer, m)
  - успіх (success, m)
  - мрія (dream, f)
  - батьки (parents, pl)
activity_hints:
- type: ordering
  focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
- type: fill-in
  focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
- type: matching
  focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
- type: fill-in
  focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народиться|народжуся} у Львові.
  - Там я {вчилася|вчиться|буду вчитися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
connects_to:
- a1-053 (Health)
prerequisites:
- a1-051 (My Plans)
grammar:
- 'All three tenses combined: past (-в/-ла), present (person endings), future (буду
  + inf)'
- 'Tense-shift signal words: раніше, зараз, далі'
- 'Life story verbs: народитися, жити, вчитися, переїхати'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: All three tenses combined in narrative — capstone grammar for A1.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My Story
**Module:** my-story | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 132
> Єв­ген Гу­ца­ло на­ро­див­ся в с. Ста­рий Жи­во­тів на Він­нич­
> чи­ні в учи­тель­ській сім’ї: бать­ко вик­ла­дав ук­ра­їн­ську мо­ву 
> й лі­те­ра­ту­ру, ма­ма — хі­мію та бі­о­ло­гію. Ось звід­ки в Єв­ге­на 
> була та­ка лю­бов і до мо­ви, і до при­ро­ди. Ко­ли хлопчику бу­ло 
> чо­ти­ри ро­ки, розпо­ча­ла­ся Друга світова вій­на, яка не мог­ла 
> не поз­на­чи­ти­ся в май­бут­ньо­му на твор­чос­ті пись­мен­ни­ка.
> Та­лант до сло­ва в Єв­ге­на про­я­вив­ся ра­но. Якось тре­ба бу­ло 
> на­пи­са­ти твір

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Розділ 5. Іменник 
> 132
> Вправа 269
> 1. Прочитайте текст.
> Чи знаєте ви, звідки походять назви українських міст 
> і сіл? Нескладно здогадатися, як утворилися назви Івано-
> Франківськ, Хмельницький чи, 
> скажімо, Сковородинівка: вони 
> бережуть пам’ять про відомих 
> людей свого регіону.
> У подібний спосіб утворено 
> й  інші топоніми, наприклад, 
> Київ від імені полянського князя 
> Кия чи Львів на честь князя 
> Лева Даниловича.
> Але це далеко не єдиний 
> спосіб творення назв населених 
> пунктів. Якщо дослідити їхн

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 6
>  віра
> Героям Слава!
> Доброго вечора, ми з України!
> Патрон 
>  Відбій повітряної тривоги!
> любов
> ЗСУ
> Україна
> СЛОВНИК  ЄДНАННЯ
> бавовна
> волонтерство
> перемога
>  ППО
>  НАТО
> паляниця
> О. Павлова.
> Коміксовий персонаж
> Кіт Інжир 
> Чи добре ви знаєте українську мову? Сканувавши QR-код або 
> перейшовши за посиланням, проведіть у класі вікторину «Дивослово».
> За бажанням можете скласти свою вікторину за поданим зразком.
> https://cutt.ly/AwLINW4X
> І. Прочитайте текст і передайте його зміст 2–3 реченнями. Чому саме бук

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 6
> Любі п’ятикласники та  п’ятикласниці!
> Цього року у вас починається новий етап шкільного життя.  Позаду 
> залишилася початкова школа, а попереду чекає сповнений відкриттів 
> шлях здобуття середньої освіти.  
> Ви вже вивчали звуки й букви, значення та правопис слів, части-
> ни мови, будову речення.  Пропонуємо збагатити ваші знання про 
> мову та  вдосконалити навички спілкування, адже в  сучасному світі 
> вміння зрозуміло й грамотно висловлюватися надзвичайно важливе.  
> Згадайте хоча б: коли ви правил

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 100
> 233  
> І   Підготуйте мультимедійну презентацію «Знайомтеся, це я!» 
> про походження свого імені й історію найменування.
>  
> ІІ   Провідміняйте й запишіть своє ім’я по батькові, а також імена 
> по батькові котрогось зі своїх батьків, дідусів чи бабусь / інших 
> дорослих. Підкресліть відмінкові закінчення.
>  
> ІІІ   Проєктна ді яльність «Українські художники та художни-
> ці». Об’єднайтеся в групу (5–7 осіб), кожен з учасників якої 
> готує стисле повідомлення про українських художників та 
> художниць за

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 138
> Розділ 3.  ЙДУЧИ ДОРОГАМИ ЖИТТЯ
> Розділ 3. 
> ЙДУЧИ ДОРОГАМИ ЖИТТЯ
> МУДРІСТЬ КОБЗАРЯ
> Тарас ШЕВЧЕНКО
> (1814–1861)
> Тарас Шевченко народився 9 берез-
> ня 
> 1814 
> р. 
> в 
> селі 
> М;оринці 
> на 
> Черкащині. Дитячі роки  пройшли в 
> селі Кир;илівці (тепер – Шевченкове). 
> Хлопець був кріпаком, тому вимуше-
> но 
> переїхав 
> разом 
> із 
> паном 
> Енгельгардтом спочатку до Вільна 
> (зараз Вільнюс – столиця Литви), 
> а згодом – до Петербурга, на довгі 
> роки залишаючи Україну. 
> 22 квітня 1838 року Тараса Шевченка звільнили з

## Три часи разом (Three Tenses Together)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 220
> Відомості із синтаксису й пунктуації. Обставина
> Якийсь час прабабуня жила з нами в місті. А потім зібра-
> ла речі й повернулася назад. «У Заліссі народилася, в Заліссі 
> й помру», — сказала мамі.
> Раз на рік я приїжджаю в гості. Мені частіше не можна, 
> «бо радіація» У цей день час летить, мов шалений. Не всти-
> гає прабабуня показати мені своє господарство: ягоди, гриби, 
> фрукти, овочі, — як час повертатися додому. А я ще навіть 
> з її сусідами не познайомилася. Сусідами прабабуня називає 
> ведме

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> часу минуло багато лiт, певно бiльше як тридцять. Я був тодi 
> невеличкий сiльський хлопчина i бiгав, граючись, по лiсах 
> i полях мойого рiдного села. Власне надiйшла весна, один iз перших гарних теплих днiв. Перший раз по довгiй зимовiй неволi в тiсних душних хатах 
> ми, сiльськi дiти, могли побiгати собi свобiдно. Ми вибiгли 
> на сiножать, що ще була гола i сiра вiд скиненої недавно зи-
> мової перини. Тiльки десь-не-десь прокльовувалася з землi 
> свiжа зелень: сквапливi острi листки тростини, ще по

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 58
> 58
> Виконайте тестові завдання. 
> 1. У формі теперішнього часу вжито обидва дієслова в рядку
> А співаю, спізнишся  
> В шепочу, усміхаєшся
> Б міркую, подорожували
> Г прочитаємо, мріємо
> 2. Дієслово у формі майбутнього часу вжито в словосполученні 
> А вивчатимемо напам’ять
> В розцвітає навесні 
> Б просили прочитати
> Г віримо в перемогу
> 3. Дієслово у  формі минулого часу вжито в кожному реченні, ОКРІМ
> А З брудної води ще ніхто чистим не вийшов (Нар. творчість).
> Б  Топчуть ноги радісно і струнко сонні трави

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 154
> Розділ 3. ВІД КАЗКИ ДО КНИГИ БУТТЯ
> А в річках жили русалки,
> Хапуни-водяники,
> Лісовик свистав у лісі,
> І сміялися мавки.
> Треба добре було знати
> Душі всіх богів земних,
> То коритись, то змагатись,
> То просити ласки в них.
> І змагалася людина,
> І вперед невпинно йшла,
> Де ясним промінням-цвітом
> Дивна папороть цвіла...
> ...Заспіваю вам не пісню
> Про стару старовину,
> Розкажу я вам не казку,
> А бувальщину одну.
> Розкажу вам, як на горах
> Славний Київ наш постав,
> Як він жив і розвивався,
> Як столицею він став.

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 17
> ЗАПИТАННЯ І ЗАВДАННЯ
> I.
> Знаю й систематизую нову інформацію
> С а м о о ц і н ю в а н н я
> Оцініть свої успіхи в опануванні теми «Як виникли системи літо-
> числення. Історична періодизація: світ і Україна». Дайте відповіді на 
> запитання.
> ?
> Прекрасно
> Добре
> Нічого 
> не зрозуміло
> Якими одиницями вимірюють час?
> Які види календарів винайшли 
> в давнину?
> Чому історики використовують
> єдину систему лічби часу?
> Які існують способи упорядкування 
> історичного часу?
> Треба
> попрацювати
> II. Обговоріть у групі
> Обг

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> Розділ 1  ДІЄСЛОВО
> 38
> § 9  Часи діє слова
> Вправа 48
> 1   Прочитайте речення 
> Я 
> роблю  
> вчора 
> уроки.
> Я 
> робила  
> завтра 
> уроки.
> Я 
> робитиму 
> зараз 
> уроки.
> 2   Поміркуйте, чи правильно побудовані речення  
> Що в  них не так?
> 3   Скоригуйте й  запишіть правильні варіанти 
> 4   Поміркуйте, у  якій частині діє слова закладено значення часу 
> Дієслова у формі дійсного способу виражають дію, що 
> відбувалася, відбувається або відбувати меться. Вони  мають 
> форми трьох часів: теперішнього, минулого та майб

## Моя історія (My Story)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 132
> Єв­ген Гу­ца­ло на­ро­див­ся в с. Ста­рий Жи­во­тів на Він­нич­
> чи­ні в учи­тель­ській сім’ї: бать­ко вик­ла­дав ук­ра­їн­ську мо­ву 
> й лі­те­ра­ту­ру, ма­ма — хі­мію та бі­о­ло­гію. Ось звід­ки в Єв­ге­на 
> була та­ка лю­бов і до мо­ви, і до при­ро­ди. Ко­ли хлопчику бу­ло 
> чо­ти­ри ро­ки, розпо­ча­ла­ся Друга світова вій­на, яка не мог­ла 
> не поз­на­чи­ти­ся в май­бут­ньо­му на твор­чос­ті пись­мен­ни­ка.
> Та­лант до сло­ва в Єв­ге­на про­я­вив­ся ра­но. Якось тре­ба бу­ло 
> на­пи­са­ти твір

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Оксана Сайко
> НОВЕНЬКА
> Вона з’явилася у їхньому класі в роз-
> палі весни. Сонце сліпучими відбл

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Три часи разом (Three Tenses Together)` (~300 words)
- `## Моя історія (My Story)` (~300 words)
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

**Required:** народитися (to be born), жити (to live), вчитися (to study), переїхати (to move), зараз (now), раніше (before/earlier), далі (further/next), розповідати (to tell/narrate)
**Recommended:** подорожувати (to travel), закінчити (to finish/graduate), дитинство (childhood, n), університет (university, m), програміст (programmer, m), успіх (success, m), мрія (dream, f), батьки (parents, pl)

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
