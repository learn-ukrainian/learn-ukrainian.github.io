# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **39: Shopping** (A1, A1.6 [Food and Shopping]).

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
module: a1-039
level: A1
sequence: 39
slug: shopping
version: '1.2'
title: Shopping
subtitle: Скільки коштує? — prices, quantities, and buying things
focus: communication
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Ask and understand prices (Скільки коштує?)
- Use Ukrainian currency (гривня, копійка) and numbers with prices
- Buy things at a shop or market using polite phrases
- Express quantities (кілограм, літр, пачка, пляшка)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At the market: — Скільки коштує кілограм яблук? — Сорок гривень.
    — А помідори? — Тридцять п''ять гривень за кілограм. — Дайте, будь ласка, два
    кілограми помідорів і кілограм яблук. — Сімдесят п''ять гривень. — Ось, будь ласка.
    Prices, quantities, polite buying at the market.'
  - 'Dialogue 2 — At the supermarket: — Вибачте, де тут хліб? — Хліб у третьому ряді.
    — А молоко? — Молоко в холодильнику, там. — Скільки коштує цей сир? — Сто двадцять
    гривень. — Дорого! А є дешевший? — Так, ось цей — вісімдесят. Navigation, asking
    prices, comparing (дорого/дешево).'
- section: Скільки коштує? (How Much?)
  words: 300
  points:
  - 'Price patterns: Скільки коштує [item]? — [number] гривень/гривні/гривня. Скільки
    коштують [plural item]? — verb agrees with plural. Currency: гривня (1), гривні
    (2-4), гривень (5+). Копійка: one hundredth of a гривня (often rounded).'
  - 'Numbers with prices (review from M12): 21 гривня, 32 гривні, 45 гривень, 100
    гривень. Дорого! (Expensive!) Дешево! (Cheap!) Нормальна ціна. (Fair price.) Є
    знижка? (Is there a discount?) За все — [total]. (Total.)'
- section: Де купити? (Where to Buy)
  words: 300
  points:
  - 'Shopping locations: магазин (shop), супермаркет (supermarket), ринок (market),
    аптека (pharmacy), крамниця (store — Ukrainian synonym for магазин). Specific:
    м''ясний відділ (meat section), молочний (dairy section).'
  - 'Quantity words: кілограм (kilogram): кілограм яблук, два кілограми помідорів.
    літр (liter): літр молока, два літри соку. пачка (pack): пачка масла, пачка чаю.
    пляшка (bottle): пляшка води, пляшка соку. буханка (loaf): буханка хліба. All
    use genitive after quantity — taught as chunks at A1.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Shopping toolkit: Ask: Скільки коштує? Де тут [item]? Buy: Дайте, будь ласка,
    [quantity] [item]. React: Дорого! / Дешево! / Добре, беру. Pay: Скільки за все?
    Можна карткою? Self-check: Buy 3 items at a market. Ask the price, choose a quantity,
    pay.'
vocabulary_hints:
  required:
  - коштувати (to cost)
  - скільки (how much/many)
  - гривня (hryvnia, f)
  - ціна (price, f)
  - магазин (shop, m)
  - ринок (market, m)
  - купувати (to buy)
  - дорого (expensive — adverb)
  - дешево (cheap — adverb)
  recommended:
  - копійка (kopeck, f)
  - кілограм (kilogram, m)
  - літр (liter, m)
  - пляшка (bottle, f)
  - пачка (pack, f)
  - знижка (discount, f)
  - супермаркет (supermarket, m)
  - гроші (money, pl.)
  - готівка (cash, f)
activity_hints:
- type: fill-in
  focus: Скільки коштує ___? — ___ гривень. (match items with prices)
  items:
  - Скільки коштує {хліб|хліба}? — Двадцять гривень.
  - Скільки коштує {вода|воду}? — Десять гривень.
  - Скільки коштує {сир|сиру}? — Сто гривень.
  - Скільки коштують {яблука|яблук}? — Сорок гривень.
  - Скільки коштують {помідори|помідорів}? — Тридцять гривень.
  - Скільки коштує {молоко|молока}? — П'ятдесят гривень.
  - Скільки коштує {сік|соку}? — Шістдесят гривень.
  - Скільки коштують {банани|бананів}? — Сімдесят гривень.
- type: quiz
  focus: 'Choose correct: 23 (гривня / гривні / гривень)'
  items:
  - question: 21 ___
    options:
    - гривня
    - гривні
    - гривень
  - question: 32 ___
    options:
    - гривні
    - гривня
    - гривень
  - question: 45 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 100 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 1 ___
    options:
    - гривня
    - гривні
    - гривень
  - question: 3 ___
    options:
    - гривні
    - гривня
    - гривень
  - question: 10 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 54 ___
    options:
    - гривні
    - гривня
    - гривень
- type: fill-in
  focus: 'At the market: Дайте ___ (кілограм/літр/пляшка) ___.'
  items:
  - Дайте {кілограм|літр|пляшку} яблук.
  - Дайте {літр|кілограм|пачку} молока.
  - Дайте {пляшку|кілограм|літр} води.
  - Дайте {пачку|літр|пляшку} чаю.
  - Дайте {буханку|літр|кілограм} хліба.
  - Дайте {кілограм|літр|пляшку} помідорів.
- type: match-up
  focus: Where do you buy it? Match item to shop type.
  items:
  - помідори: ринок
  - м'ясо: м'ясний відділ
  - сир: молочний відділ
  - хліб: крамниця
  - молоко: супермаркет
  - вода: магазин
  - кава: кафе
  - борщ: ресторан
connects_to:
- a1-040 (People Around Me)
prerequisites:
- a1-038 (At the Cafe)
grammar:
- Скільки коштує/коштують? — singular/plural agreement
- 'Currency: гривня/гривні/гривень (1/2-4/5+)'
- 'Quantity + genitive as chunks: кілограм яблук, літр молока'
register: розмовний
references:
- title: ULP Season 1, Episode 31
  url: https://www.ukrainianlessons.com/episode31/
  notes: Shopping vocabulary, prices, quantities.
- title: State Standard 2024, Topic 3 (купівля)
  notes: 'Communicative situation: shopping, prices, paying.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Shopping
**Module:** shopping | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> •  Випишіть із тексту словосполучення іменників із залежним 1 
> від них числівниками. Запишіть числівники словами, поставте 
> до них питання.
> 263. Прочитайте словосполучення, розкриваючи дужки.
> 5 (олівець), 8 (зошит), 20 (курча), 3 (стіл), 60 (лист), 
> 11 (стілець), 20 (яблуко), 24 (ящик), 70 (кілограм), 500 
> (дерево).
> •  Спишіть словосполучення за зразком, запишіть числівники 
> словами.
> Зразок
> П’ять олівців, п’ятсот кілограмів.
> гь'зіж ябт ,
> 264. Прочитайте текст.
> Паць вийшов із будинку за п’ять хви

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 236
> Відомості із синтаксису й пунктуації. Складне речення
> 4. Яка інформація з  тексту була для вас новою?
> 5. Пригадайте, які хімічні досліди на кухні (з перерахованих у тексті чи інші) 
> проводили ви . Розкажіть про це друзям, використовуючи складні речення .
> Вправа 380
> 1. Прочитайте рекомендації щодо здорового сніданку .
> СМУЗІ
> z
> z яблуко — 1 шт.,
> z
> z банан — 1 шт.,
> z
> z склянка води,
> z
> z кілька заморожених ягід 
> (на ваш смак),
> z
> z ложка лляного насіння.
> ОМЛЕТ З ОВОЧАМИ 
> ТА ЗЕЛЕННЮ
> z
> z яйця — 1—2

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 185
> Числiвник
> Якщо до складу числівника входять слова з поло-
> виною, із чвертю, то іменник узгоджуємо із цілим
> числом. НАПРИКЛАД:
> два з половиною лимони, 
> шість із половиною лимонів.
> ПОРІВНЯЙМО:
> ПРАВИЛЬНО
> НЕПРАВИЛЬНО
> дві третіх кілограма
> двом третім кілограма
> півтора кілограма
> два із чвертю кілограми
> дві третіх кілограми
> двом третім кілограмам
> півтора кілограми
> два із чвертю кілограма
> Іменники при складених числівниках уживаємо в тому відмінку, яко-
> го вимагає останнє слово. НАПРИКЛАД: двадцять

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 121.1. Відгадай загадки. Усно зміни слова-відгадки за числами і від­
> мінками.
> 1. Соковите, червоненьке, круглобоке, солоденьке. 2. Чи 
> то жовта, чи то синя — соковита господиня. Чи то сонце, чи то 
> злива — пригостить нас влітку ... . 3. Цього фрукта по шматку 
> в чай додам я для смаку. Запашний він та кисленький, наче 
> сонечко, жовтенький.
> 2. Користуючись таблицею зі с. 42, запиши змінювання 
> одного зі слів-відгадок за відмінковими питаннями 
> і числами.
> 3. Зіскануй (Ж-код і перевір за допомогою с

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 27
> 58
>   Розгляньте слова, записані ліворуч і праворуч. Які запозичення, 
> на вашу думку, збагачують мову, а які — шкодять їй? Відповідь 
> обґрунтуйте.
> 1)  грошові одиниці: ліра, 
> лат, крона, фунт стер-
> лінгів, долар;
> 2)  національні 
> страви: 
> паелья, паста, суші;
> 3)  одяг: сарі, кімоно, пончо;
> 4)  танці: фламенко, лез-
> гінка, сальса, самба, 
> танго
> Допис — пост;
> виклик — челендж;
> світлина — фотографія; 
> наплічник — рюкзак; 
> цькування — булінг;
> летовище — аеродром;
> мить — момент;
> зміна — ротація; 
> с

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 171
> 171
> § 87.  Узгодження  кількісних числівників  з  іменниками
> райдужної троянди стартує від двадцяти долара (З інтернету). 5. Десять 
> раз поспіль обирали запорожці Сірка отаманом (М. Слабошпицький).
> А.	 Виконайте розбір виділеного числівника як частини мови (письмово).
> Б.	 Визначте, до яких груп за значенням належать усі числівники (усно).
> 4.	 Виконайте завдання в тестовій формі.
> 1.	 Помилково узгоджено числівник з іменником у варіанті
> А	 два шестикласника
> Б	 п’ять із чвертю тонн
> В	 дев’ять к

## Скільки коштує? (How Much?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 124
> 1. Яку інформацію містить кожна купюра?
> 2. Чим купюри відрізняються, а що в них подібне?
> 3. Чиї портрети зображають на купюрах? Чому?
> 4. Чи можна в наш час обійтися без купюр? 
> 5. Поясніть, як розумієте вислови: «розрахунок
> готівкою», «безготівковий розрахунок». 
> 5. Прочитай 
> інформацію 
> Родзинки, 
> щоб 
> перевірити,
> чи  правильно  ви  міркували. 
> Готівка — це гроші. Розрахуватися готівкою — 
> означає заплатити за товар чи послуги грошима. 
> Безготівковий розрахунок здійснюється шляхом пе-
> рерах

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 167
> герб, тризуб. Ці гроші згодом стали називати гривнями. 
> Тож наші сучасні гривні мають довгу й цікаву історію! 
> (З інтернету).
>  
> ІІ   Порівняйте тексти — уміщений у підручнику і записаний 
> вами. Назвіть їхні спільні ознаки. Чим різняться тексти?
> Пригадуємо:
> 1   Що таке текст?
> 2   Що таке тема тексту?
> Шукаємо відповіді на запитання:
> 1   Що таке первинні і вторинні тексти?
> 2   Чим відрізняються первинні і вторинні тексти?
> 3   У яких життєвих ситуаціях створюють первинні тексти?
> Відповідно до за

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Розділ 7. Числівник 
> 244
> із  6-річного віку, а  підліток у  віці 
> від 14 до 18 (роки) може само-
> стійно відкрити рахунок на своє 
> ім’я.
> Картку можна оформити без-
> коштовно. Якщо ви бажаєте інди-
> відуальний дизайн, це коштує додаткових витрат  — від 
> 99 грн. Деякі банки пропонують дитячу картку з  фото, 
> за це доведеться заплатити від 50  грн.
> (Із сайту Національного банку України)
> 2. Чи маєте ви банківську картку? Якщо так, то в  яких ситуаціях її вико-
> ристовуєте?
> 3. Які, на ваш погляд, є  пере

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 47
> 90. 
> 1. Прочитай текст і розглянь малюнок. Постав запи-
> тання до кожного абзацу.
> ОДНА ГРИВНЯ — ОДИН ВІЛ
> Гривня з’явилася за часів Київської Русі. Це був зли-
> ток — срібний, іноді золотий. За одну гривню можна було 
> купити вола.
> Гривні знову з’явилися за часів відродження україн-
> ської державності в 1919–1920 роках. Тепер — це наші 
> українські гроші.
> 2. Визнач рід та відмінок виділених іменників. За потреби 
> користуйся таблицями на сс. 41–42.
> 91. 
> 1. Прочитай і спиши речення. Підкресли в них г

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 27
> 58
>   Розгляньте слова, записані ліворуч і праворуч. Які запозичення, 
> на вашу думку, збагачують мову, а які — шкодять їй? Відповідь 
> обґрунтуйте.
> 1)  грошові одиниці: ліра, 
> лат, крона, фунт стер-
> лінгів, долар;
> 2)  національні 
> страви: 
> паелья, паста, суші;
> 3)  одяг: сарі, кімоно, пончо;
> 4)  танці: фламенко, лез-
> гінка, сальса, самба, 
> танго
> Допис — пост;
> виклик — челендж;
> світлина — фотографія; 
> наплічник — рюкзак; 
> цькування — булінг;
> летовище — аеродром;
> мить — момент;
> зміна — ротація; 
> с

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 21
> Пригадуємо:
> 1   Які слова називають змінюваними? Наведіть приклади.
> 2   Чи всі слова мають закінчення?
> 3   Чому це важливо знати?
> Шукаємо відповіді на запитання:
> 1   За якою ознакою слова поділяють на незмінювані 
> і змінювані?
> 2   Як визначити, змінюване чи незмінюване слово?
> 3   Якого складника в будові незмінюваного слова немає?
> Відповідно до запитань сформулюйте особисті цілі.
> 39   Розгляньте схеми. Використовуючи їх, розкажіть про те, чим 
> різняться змінювані і незмінювані слова.
> Змінюван

## Де купити? (Where to Buy)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Гардерîб — одяг людини.
> • Чи можна цей текст назвати заміткою? Про які поради щодо
> написання замітки забув автор. Запишіть.
> • У якому музеї може бути предмет, назва
> якого записана в рамці? 
> 48. Прочитайте замітку, яку написав відвідувач Музею хліба.
> Учора я відвідав Музей хліба. Це унікальний музей!
> У ньому зібрано понад дві тисячі експонатів. Тут є майже
> двісті різновидів хліба, понад сто п’ятдесят короваїв із
> різних куточків України. Є в музеї навіть космічний хліб.
> Нам розказали, що цей спеці

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 236
> Відомості із синтаксису й пунктуації. Складне речення
> 4. Яка інформація з  тексту була для вас 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Скільки коштує? (How Much?)` (~300 words)
- `## Де купити? (Where to Buy)` (~300 words)
- `## Підсумок — Summary` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary

**Required:** коштувати (to cost), скільки (how much/many), гривня (hryvnia, f), ціна (price, f), магазин (shop, m), ринок (market, m), купувати (to buy), дорого (expensive — adverb), дешево (cheap — adverb)
**Recommended:** копійка (kopeck, f), кілограм (kilogram, m), літр (liter, m), пляшка (bottle, f), пачка (pack, f), знижка (discount, f), супермаркет (supermarket, m), гроші (money, pl.), готівка (cash, f)

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
