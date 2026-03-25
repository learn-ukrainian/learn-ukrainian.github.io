# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **38: At the Cafe** (A1, A1.6 [Food and Shopping]).

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
module: a1-038
level: A1
sequence: 38
slug: at-the-cafe
version: '1.2'
title: At the Cafe
subtitle: У кафе — ordering, paying, and cafe culture
focus: communication
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Order food and drinks at a Ukrainian cafe
- Use polite request phrases (Можна...? Дайте, будь ласка...)
- Read a simple Ukrainian menu and ask about items
- Understand Ukrainian cafe culture (tipping, paying)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Ordering at a cafe: — Добрий день! Ось меню. — Дякую. Що ви рекомендуєте?
    — Борщ дуже смачний. — Добре, мені борщ і хліб, будь ласка. — А що будете пити?
    — Каву з молоком. — Добре, одну хвилинку. Polite ordering with будь ласка, мені
    + accusative.'
  - 'Dialogue 2 — Paying the bill: — Рахунок, будь ласка. — Ось, будь ласка. Сто двадцять
    гривень. — Можна карткою? — Так, звичайно. — Дякую, дуже смачно було! — Дякуємо,
    приходьте ще! Paying, complimenting food, tipping.'
- section: Як замовити (How to Order)
  words: 300
  points:
  - 'Ordering patterns: Мені [accusative], будь ласка. (Мені каву, будь ласка.) Можна
    [accusative]? (Можна воду?) Дайте, будь ласка, [accusative]. (Дайте, будь ласка,
    борщ.) Я хочу / Я буду [accusative]. (Я буду салат.) All use accusative from M37
    — real application.'
  - 'Asking about the menu: Що ви рекомендуєте? (What do you recommend?) Це гостре?
    (Is it spicy?) Це з м''ясом? (Is it with meat?) А що це? (What is this?) Скільки
    коштує? (How much?) Є вегетаріанське меню? (Is there a vegetarian menu?)'
- section: Культура кафе (Cafe Culture)
  words: 300
  points:
  - 'Ukrainian cafe culture: Кафе vs ресторан: кафе is casual, ресторан is formal.
    Меню: the waiter brings it, or it''s on the wall/board. Рахунок: ask for the bill
    — it doesn''t come automatically. Чайові (tips): 10% is standard, not obligatory.
    Карткою чи готівкою? (Card or cash?) — most places take cards.'
  - 'Useful cafe phrases: Вільно? / Тут вільно? (Is this seat free?) Можна меню? (Can
    I have the menu?) Ще одну каву, будь ласка. (One more coffee, please.) Без цукру.
    (Without sugar.) З лимоном. (With lemon.) Все було дуже смачно! (Everything was
    delicious!)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Cafe communication toolkit: Order: Мені [accusative], будь ласка. Ask: Скільки
    коштує? Що рекомендуєте? Pay: Рахунок, будь ласка. Можна карткою? Compliment:
    Дуже смачно! Self-check: Order a full meal (starter, main, drink) at a cafe. Ask
    for the bill and pay.'
vocabulary_hints:
  required:
  - кафе (cafe, n, indecl.)
  - меню (menu, n, indecl.)
  - рахунок (bill, m)
  - замовляти (to order)
  - офіціант (waiter, m)
  - смачно (delicious — adverb)
  - будь ласка (please)
  recommended:
  - ресторан (restaurant, m)
  - рекомендувати (to recommend)
  - чайові (tip/gratuity, pl.)
  - готівка (cash, f)
  - картка (card, f)
  - гостре (spicy — neuter adj.)
  - вегетаріанський (vegetarian — adj.)
activity_hints:
- type: fill-in
  focus: 'Order at a cafe: Мені ___, будь ласка. (choose correct accusative)'
  items:
  - Мені {каву|кава|каві}, будь ласка.
  - Мені {воду|вода|водою}, будь ласка.
  - Мені {борщ|борщу|борщем}, будь ласка.
  - Мені {салат|салату|салатом}, будь ласка.
  - Мені {суп|супу|супом}, будь ласка.
  - Дайте, будь ласка, {чай|чаю|чаєм}.
  - Я буду {піцу|піца|піці}.
  - Можна {хліб|хліба|хлібом}?
- type: quiz
  focus: What do you say? Match situation to phrase (order/pay/ask/compliment)
  items:
  - question: You want to order coffee. What do you say?
    options:
    - Мені каву, будь ласка.
    - Рахунок, будь ласка.
    - Що ви рекомендуєте?
  - question: You want to pay. What do you say?
    options:
    - Рахунок, будь ласка.
    - Можна меню?
    - Це гостре?
  - question: You want to know the price. What do you say?
    options:
    - Скільки коштує?
    - Це з м'ясом?
    - Тут вільно?
  - question: You want to ask for a recommendation. What do you say?
    options:
    - Що ви рекомендуєте?
    - Є вегетаріанське меню?
    - Все було дуже смачно!
  - question: You want to praise the food. What do you say?
    options:
    - Все було дуже смачно!
    - Можна карткою?
    - Без цукру.
  - question: You want to know if a seat is free. What do you say?
    options:
    - Тут вільно?
    - Ще одну каву, будь ласка.
    - Рахунок, будь ласка.
  - question: You want to ask if the dish is spicy. What do you say?
    options:
    - Це гостре?
    - Це з м'ясом?
    - Скільки коштує?
  - question: You want to pay by card. What do you say?
    options:
    - Можна карткою?
    - Є вегетаріанське меню?
    - Що ви рекомендуєте?
- type: fill-in
  focus: Complete the cafe dialogue with correct phrases
  items:
  - — Добрий день! Ось {меню|рахунок|картка}.
  - — Дякую. Що ви {рекомендуєте|коштуєте|платите}?
  - — Борщ дуже {смачний|гострий|вільний}.
  - — Добре, {мені|я|мене} борщ і хліб, будь ласка.
  - — А що будете {пити|їсти|читати}?
  - — Каву з молоком. — Добре, одну {хвилинку|годину|каву}.
- type: match-up
  focus: Match Ukrainian cafe phrases with their functions
  items:
  - Рахунок, будь ласка.: Asking for the bill
  - Що ви рекомендуєте?: Asking for advice
  - Мені борщ, будь ласка.: Ordering food
  - Скільки коштує?: Asking the price
  - Можна карткою?: Asking about payment method
  - Дуже смачно!: Complimenting the food
  - Тут вільно?: Asking for a seat
  - Можна меню?: Asking to see the options
connects_to:
- a1-039 (Shopping)
prerequisites:
- a1-037 (I Eat, I Drink)
grammar:
- Мені + accusative (ordering pattern)
- Можна + accusative (polite request)
- 'Review: accusative inanimate from M37'
register: розмовний
references:
- title: ULP Season 1, Episodes 11-12
  url: https://www.ukrainianlessons.com/episode11/
  notes: Ordering at a cafe, restaurant vocabulary.
- title: State Standard 2024, Topic 3 (ресторан)
  notes: 'Communicative situation: ordering food and drinks.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: At the Cafe
**Module:** at-the-cafe | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 103
> 5. Із тексту про японську мову випиши в колонку дієс-
> лова, вжиті у множині. Утвори від них форму однини
> і  запиши  у  другу  колонку.
> 5
> 6. Напиши повідомлення японським школярам про україн-
> ську мову (3–4 речення).
> 6
> 7. Прочитай текст. Випиши в колонку дієслова. Зміни їх
> за числами й запиши поряд. Напиши, які страви з рису 
> ти знаєш. Які тобі доводилося їсти? 
> Рис називають японським хлі-
> бом. Найчастіше японці їдять 
> його без будь-яких приправ, 
> масла і навіть солі. Вони вважа-
> ють, що рис

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 239
> Відомості із синтаксису й пунктуації. Кома між частинами складного речення
> Про борщ я можу розпо-
> відати годинами. Ні для кого 
> не секрет що майже у кожній 
> родині існує свій особливий 
> рецепт борщу. Хтось не уявляє 
> борщ без квасолі а хтось готує 
> його без капусти. Всі ці варіан-
> ти мають право на існування 
> бо немає якогось «правильно-
> го» рецепту, просто в кожного 
> є свій сімейний борщ.
> І досі популярним є узвар із сухофруктів це дуже корисний 
> і поживний напі й.
> Полтава славиться галушк

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 78
> Морфологiя та орфографiя 
>  
>  ПОСПІЛКУЙТЕСЯ. Яке народне свято вам подобається найбільше? Чим 
> саме?
> ЧОМУ ТАК? Поясніть, чому в першому реченні виділене слово вважаємо 
> прик метником, а в другому – прислівником.
> 1. Добре слово кожному приємне.
> 2. Хто добре працює, той добре відпочиває.
> І. Спишіть прислів’я і підкресліть члени речення. Над кожним словом 
> надпишіть частину мови. Які слова є службовими? 
> 1. Добрий горщик, та поганий борщик. 2. Сила без голови
> шаліє, а розум без сили мліє. 3. Прац

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 91
> 5. Прочитай заголовок тексту. Чи знаєш ти, що означає цей 
> вислів? Прочитай текст, щоб перевірити свою думку.
> Шведський стіл
> У давнину шведи відвідували своїх родичів, до-
> лаючи велику відстань поганими дорогами. Їм було 
> не до очікування прибуття інших гостей. Тому гос-
> подарі ставили на стіл різні страви. Подавали їх
> у великих мисках, і кожен міг брати стільки, скіль-
> ки хотів. Це давало змогу втамувати перший голод 
> і залишало час для спілкування. Іноземці називали 
> такий спосіб пригощання

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 201
> Шукаємо відповіді на запитання:
> 1   Що називають запрошенням?
> 2   Кого, куди і як правильно запрошувати?
> Відповідно до поставлених запитань сформулюйте особисті 
> цілі.
> Запрîшення — коротке повідомлення про якусь подію 
> і прохання взяти в ній участь.
> Запрошення може бути усне або письмове.
> Слова запросити і просити, прохання мають однако-
> вий корінь. Це дає підстави вважати запрошення різ-
> новидом прохання.
> 467   Розгляньте подану інформацію. Що вам відоме, а що   — нове? 
> Яких помилок припус

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 228
>  
> ІІ   Пригадайте і запишіть найціннішу пораду, якою ви скориста-
> лися. Складіть і запишіть діалог, використавши в ньому цю 
> пораду. Яке значення вона для вас мала?
>  
> ІІІ   Напишіть есе «Чому здоров’я — найвища людська цінність?».
> ЕЛЕКТРОННИЙ ЛИСТ
> § 91
> Нащо мені друзі
> Лист — це розмова відсутнього з присутнім 
> за допомогою письма, а не голосу (Квінтиліан).
> Дружба примножує радості і дробить печалі (Г. Дж. Бон).
> Слово дня: всемерåжжя, власнорóч, об³рóч.
> Пригадуємо:
> 1   Із чим у вашій уяві асо

## Як замовити (How to Order)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> уживає такі слова: не переймайтеся, не хвилюйтеся, про0
> шу, усе нормально.
> Уміння чемно відмовитися чи погодитися — теж мис6
> тецтво спілкування. Невміння делікатно відмовитися мо6
> же образити людину. У ситуації відмови користуються
> висловами: дякую, але я сьогодні маю інші справи; спа0
> сибі, але наступним разом; вибачте, але я, на жаль,
> не зможу. Якщо ж погоджуємося з чимось, то викорис6
> товуємо такі вислови: я із задоволенням приймаю Вашу
> пропозицію; щиро дякую; мені приємно, що я теж можу
> бути

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 201
> Шукаємо відповіді на запитання:
> 1   Що називають запрошенням?
> 2   Кого, куди і як правильно запрошувати?
> Відповідно до поставлених запитань сформулюйте особисті 
> цілі.
> Запрîшення — коротке повідомлення про якусь подію 
> і прохання взяти в ній участь.
> Запрошення може бути усне або письмове.
> Слова запросити і просити, прохання мають однако-
> вий корінь. Це дає підстави вважати запрошення різ-
> новидом прохання.
> 467   Розгляньте подану інформацію. Що вам відоме, а що   — нове? 
> Яких помилок припус

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> • прикликати урожай, успіх, лад у сім’ї;
> • просити долю для дитини, здоров’я, красу, щастя;
> • закохати в себе хлопця / дівчину;
> • відвернути небажане (нелюба, смерть, хворобу);
> • зупинити кров, ворогів, силу негативного впливу, ви-
> качати страх тощо.
> Замовляння промовляли вголос. Вважалося, що чим емо-
> ційніше сказати замовляння, тим більша його сила впливу.
> Запитання і завдання
>  1. 
> Поясни, які тексти називають замовляннями. Чому вони 
> виникли?
>  2. 
> Прочитай замовляння. Визнач, до яких тематичн

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 1. 
> Скажи мені, хто твій друг, і я скажу тобі, хто ти. 2. Ми 
> з тобою, як риба з водою. 3. Як ми до людей, так люди до 
> нас. 4. Ви робіть добро, і вам добре буде. 5. Він тобі й зорі 
> з неба зніме.
> *
> •  Спишіть прислів’я, підкресліть займенники. Провідміняйте 
> підкреслений займенник.
> 300. Прочитайте прислів’я. Розкрийте їх зміст.
> В усному й писемному мовленні вживайте висло­
> ви: вибач м ені, пробачте м ені, дякую вам, вибачайте 
> нам, порадь м ені, даруйте м ені, я перепрошую, 
> болить у мене, зрад

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 199
> 462   Прочитайте речення. Визначте комунікативний намір мовців 
> (прохання, умовляння, благання, клянчення чи пропозиція). 
> Обґрунтуйте свій вибір. На  яке прохання ви відгукнулися б? 
> Хто з мовців найкраще обґрунтував свої бажання?
> 1. Мамо, купи мені цю іграшку, купи, купи, купи, купи!!! 
> У Вероніки є точнісінько така, і я хочу! Купи-и-и-и!!! 
> 2. Дідусю, благаю, візьми мене з собою в похід на Говерлу! 
> Я ще там ніколи не був! 3. Тату, можна я не буду пристібатися 
> паском безпеки?! Я ж не мал

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

## Культура кафе (Cafe Culture)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 109
> 4. Прочитай етикетку улюбленого напою китайців. Розка-
> жи, яку  інформацію вона  містить.  Що в ній для  тебе  як
> споживача  найважливіше?
> 4
> 5. Родзинка дізналася, де винайшли чай. Прочитай і ти.
> Вирощувати й заварювати чай почали в Китаї. 
> А сталося це, коли випадково листок чайного куща 
> впав у чашку з окропом. 
> Чай буває білий, зелений, чорний. Усі вони
> з листя одного куща, який називається «Каме-
> лія китайська». Тільки сушать листя по-різному. 
> Тому й виходить різний смак і властивості ч

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 20
> Культура мовлення
> ПРАВИЛЬНО
> НЕПРАВИЛЬНО
> прочитати правильно
> увімкнути світло
> відчиняти ворота
> розгорнути зошит
> наступний урок 
> прочитати вірно
> включити світло
> відкривати ворота
> роз

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Як замовити (How to Order)` (~300 words)
- `## Культура кафе (Cafe Culture)` (~300 words)
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

**Required:** кафе (cafe, n, indecl.), меню (menu, n, indecl.), рахунок (bill, m), замовляти (to order), офіціант (waiter, m), смачно (delicious — adverb), будь ласка (please)
**Recommended:** ресторан (restaurant, m), рекомендувати (to recommend), чайові (tip/gratuity, pl.), готівка (cash, f), картка (card, f), гостре (spicy — neuter adj.), вегетаріанський (vegetarian — adj.)

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
