<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/shopping-and-health.yaml` file for module **15: На ринку та у лікаря** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-genitive-phrase-for-health-complaints-and-remedies -->`
- `<!-- INJECT_ACTIVITY: match-up-match-health-problems-to-their-remedies -->`
- `<!-- INJECT_ACTIVITY: true-false-judge-whether-shopping-and-health-phrases-use-the-genitive-correctly -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete market dialogue lines with correct quantity + Genitive forms
  items: 8
  type: fill-in
- focus: Choose the correct Genitive phrase for health complaints and remedies
  items: 8
  type: quiz
- focus: Match health problems to their remedies (ліки від..., краплі від...)
  items: 8
  type: match-up
- focus: Judge whether shopping and health phrases use the Genitive correctly
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- помідор (tomato)
- нежить (runny nose, cold)
- алергія (allergy)
- таблетка (pill, tablet)
- шматок (piece)
required:
- ринок (market)
- кілограм (kilogram)
- пляшка (bottle)
- здоров'я (health)
- температура (temperature, fever)
- рецепт (prescription, recipe)
- аптека (pharmacy)
- ліки (medicine)
- кашель (cough)
- апетит (appetite)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## На ринку: скільки вам? (~800 words total)

The heart of local commerce in Ukraine is the **ринок** (market). Here, buying food is an interactive process. You must talk to the vendor and specify what you need. This makes the market the perfect place to master the Genitive case.

Я дуже люблю ходити на ринок у суботу вранці. Там завжди багато людей, свіжі овочі та фрукти. Я купую продукти на весь тиждень. Можна вибрати найкращі яблука чи молоко. Люди говорять про ціни, запитують про свіжість продуктів.

> *I really like going to the market on Saturday morning. There are always a lot of people, fresh vegetables, and fruits there. I buy groceries for the whole week. You can choose the best apples or milk. People talk about prices, ask about the freshness of products.*

Let us look at a typical interaction when you approach a stall. A **покупець** (buyer) asks about the produce, while the **продавець** (vendor) calculates the cost. 

> — **Покупець:** Добрий день! У вас є свіжі помідори? *(Do you have fresh tomatoes?)*
> — **Продавець:** Добрий день! Так, дуже свіжі і солодкі. Скільки вам? *(Yes, very fresh and sweet. How much for you?)*
> — **Покупець:** Дайте мені, будь ласка, один **кілограм** (kilogram) помідорів. І ще кілограм яблук. *(Give me, please, one kilogram of tomatoes. And a kilogram of apples.)*
> — **Продавець:** Які красиві яблука! Вони дуже солодкі і соковиті. Яблука з мого саду.
> — **Покупець:** Добре, я візьму ще два кілограми яблук.
> — **Продавець:** Будь ласка, обирайте найкращі. Щось ще бажаєте?
> — **Покупець:** Так, мені ще потрібні огірки. Дайте пів кіло огірків. *(Give me half a kilo of cucumbers.)*
> — **Продавець:** З вас дев'яносто гривень. *(That will be ninety hryvnias from you.)*
> — **Покупець:** Дякую, ось гроші.
> — **Продавець:** Дякую за покупку! Приходьте ще.

The core rule of shopping is Quantity + Genitive. Whenever you specify an amount, a precise weight, or a container for a **рецепт** (recipe), the noun that follows takes the Genitive case.

Ми часто використовуємо цю граматику вдома. Для цього рецепта мені потрібен кілограм яблук. Також я маю купити літр молока і пачку масла. Без цих продуктів я не зможу спекти пиріг. Ми завжди купуємо два кілограми м'яса на вихідних.

> *We often use this grammar at home. For this recipe I need a kilogram of apples. Also I have to buy a liter of milk and a pack of butter. Without these products I will not be able to bake a pie. We always buy two kilograms of meat on the weekend.*

We must distinguish between uncountable substances and countable items. For masculine substances, Ukrainian uses the **-у** or **-ю** ending in the Genitive singular. For countable items, use the Genitive Plural.

:::info
**Grammar box**
Remember that for masculine substances, the **-у/-ю** ending is the standard. The language strongly prefers this form for materials: чаю, соку, рису.
:::

Мама просить мене піти в сусідній магазин. Вона каже: купи, будь ласка, кілограм цукру і двісті грамів сиру. Я записую все на папірці. У магазині я також беру десяток яєць і пів кілограма рису. Тепер у нас є все для сніданку.

> *Mom asks me to go to the neighboring store. She says: buy, please, a kilogram of sugar and two hundred grams of cheese. I write everything down on a piece of paper. In the store, I also take a ten of eggs and half a kilogram of rice. Now we have everything for breakfast.*

You will also need measure words and partitives like **склянка** (glass), **шматок** (piece), or **пляшка** (bottle). These also trigger the Genitive case. Another common word is the prefix **пів** (half).

Я хочу випити велику склянку соку. Дайте мені, будь ласка, шматок свіжого хліба. Ця велика пластикова пляшка мінеральної води коштує сорок гривень. Вчора я купив пів літра молока. Моя сестра випила чашку зеленого чаю без цукру.

> *I want to drink a large glass of juice. Give me, please, a piece of fresh bread. This large plastic bottle of mineral water costs forty hryvnias. Yesterday I bought half a liter of milk. My sister drank a cup of green tea without sugar.*

When buying, pay attention to whether the item is singular or plural. You ask "Скільки коштує?" for singular, but "Скільки коштують?" for plural. Vendors often use diminutives to sound friendly.

> — **Покупець:** Добрий день, чи є у вас свіжа картопелька? *(Do you have fresh potatoes?)*
> — **Продавець:** Добрий день! Так, звичайно є. Дуже добра картопля.
> — **Покупець:** Скільки коштує один кілограм? *(How much does one kilogram cost?)*
> — **Продавець:** Тридцять гривень. Будете брати?
> — **Покупець:** Дайте мені, будь ласка, два кілограми. І ще десяток яєць. *(Give me, please, two kilograms. And a ten of eggs.)*
> — **Продавець:** Ось ваша картопелька. Дуже гарна, без бруду. Я завжди продаю тільки найкраще для моїх клієнтів.
> — **Покупець:** Дуже дякую. Я завжди купую овочі тільки у вас.
> — **Продавець:** Добре. З вас дев'яносто гривень загалом. *(That will be ninety hryvnias in total.)*
> — **Покупець:** Тримайте сто гривень.
> — **Продавець:** Ваша решта — десять гривень. Гарного дня!
> — **Покупець:** До побачення!

The Genitive case is strictly required after numbers five and above. This "five plus" rule is essential for handling money and quantities. Any number from five onwards takes the Genitive Plural.

З вас вісімдесят гривень, каже продавець. Я купую п'ять кілограмів картоплі і три кілограми цибулі на зиму. Мій старший брат несе важкі сумки додому. У моєму кошику акуратно лежить десяток яєць. Ми витратили сто п'ятдесят гривень на ринку сьогодні вранці. Ринок — це чудове місце. Там можна купити все необхідне. Я завжди приходжу сюди з радістю.

> — **Продавець:** Добрий ранок!
> — **Покупець:** Добрий ранок! Скільки коштують ці яблука?
> — **Продавець:** Сорок гривень за кілограм.
> — **Покупець:** Дайте мені один кілограм.
> — **Продавець:** Будь ласка. З вас сорок гривень.
> — **Покупець:** Дякую!

<!-- INJECT_ACTIVITY: fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms -->

## У лікаря: що вас турбує? (~800 words total)

We have just learned how to use the Genitive case to buy food and describe quantities at the **ринок** (market). Now, let us imagine you need to visit a clinic to talk about your **здоров'я** (health). The language of medicine relies heavily on the grammatical patterns you just practiced. Whether you are asking for a **кілограм** (kilogram) of apples or explaining to a doctor that you do not have a fever, the Genitive case remains a vital tool. We use it frequently to talk about what we lack or to identify the source of a problem.

Сьогодні ми йдемо до лікаря, бо мій брат несподівано захворів. Він каже, що йому дуже погано і потрібна медична допомога. У нього зовсім немає сил, тому я йду разом із ним до поліклініки. Ми хочемо дізнатися, що сталося, і як швидко повернути його здоров'я.

> *Today we are going to the doctor because my brother unexpectedly got sick. He says that he feels very bad and needs medical help. He has absolutely no energy, so I am going together with him to the clinic. We want to find out what happened, and how to quickly restore his health.*

Here is a typical conversation you might have during a medical consultation. Pay attention to how the doctor asks about symptoms and how the patient responds using simple, direct phrases.

> — **Лікар:** Добрий день! Що вас турбує? *(Good day! What troubles you?)*
> — **Пацієнт:** Добрий день. У мене дуже сильно болить горло і голова. *(Good day. My throat and head hurt very much.)*
> — **Лікар:** Як давно це почалося? *(How long ago did this start?)*
> — **Пацієнт:** Вчора ввечері, після роботи. *(Yesterday evening, after work.)*
> — **Лікар:** Чи є у вас температура? *(Do you have a fever?)*
> — **Пацієнт:** Ні, температури немає, але є сильний кашель. *(No, there is no fever, but there is a strong cough.)*

When you want to say that something hurts, you cannot literally translate the English phrase "I have a headache." Instead, Ukrainian uses a special construction: **У мене болить...** (literally: "At me hurts..."). In this structure, the body part that hurts is the actual subject of the sentence, so it must be in the Nominative case. Importantly, the verb **боліти** (to hurt) must agree with that body part in number.

У мене болить голова, тому я сьогодні не хочу читати. Мій дідусь часто каже, що у нього болять коліна після довгої прогулянки. Якщо у вас сильно болить живіт, вам треба йти до лікарні. У моєї сестри болять очі, коли вона довго працює за комп'ютером.

> *My head hurts, so today I do not want to read. My grandfather often says that his knees hurt after a long walk. If your stomach hurts a lot, you need to go to the hospital. My sister's eyes hurt when she works at the computer for a long time.*

:::info
**У мене болить / болять**
Use **болить** (singular verb) for one body part: У мене болить спина (My back hurts).
Use **болять** (plural verb) for multiple body parts: У мене болять ноги (My legs hurt).
:::

Another crucial use of the Genitive case in a medical context is the Genitive of Absence. Whenever you want to state that you *do not* have a certain symptom, like an **апетит** (appetite) or a **температура** (temperature, fever), you must use the negative word **немає** followed by the symptom in the Genitive case. This is a strict rule that applies to the absence of anything, whether it is a physical object like a **пляшка** (bottle) of syrup or a medical condition.

Лікар уважно дивиться на мене і питає, чи є у мене алергія. Я швидко відповідаю, що у мене немає алергії. Інший пацієнт каже, що у нього зовсім немає апетиту вже два дні. На щастя, у мого брата немає високої температури.

> *The doctor looks at me carefully and asks if I have an allergy. I quickly answer that I have no allergy. Another patient says that he has absolutely no appetite for two days already. Fortunately, my brother has no high fever.*

Sometimes you just feel unwell without a specific localized pain. To describe your general physical state, Ukrainian uses impersonal constructions featuring the Dative case and an adverb. You place the pronoun in the Dative (such as **мені**, **йому**, **їй**) and follow it with a descriptive adverb like **погано** (bad) or **холодно** (cold). If you feel nauseous, there is a specific verb used with the Accusative case: **Мене нудить** (I feel nauseous).

Взимку на вулиці мені часто буває дуже холодно. Коли ми довго їхали в старому автобусі, моїй мамі раптом стало погано. Вона сказала, що її трохи нудить від запаху бензину. Зараз їй вже набагато краще, і ми йдемо додому.

> *In winter outside I am often very cold. When we were riding for a long time in an old bus, my mom suddenly started to feel bad. She said that she felt a little nauseous from the smell of gasoline. Now she is already much better, and we are walking home.*

If you know the cause of your pain or physical state, you can explain it using the preposition **від** (from) followed by the Genitive case. This is very common when describing symptoms related to weather, such as a **кашель** (cough) from the cold. Interestingly, we also use this exact same preposition when we buy medicine *against* a specific symptom.

У мене зараз сильно болить горло від холодної води. Цей жахливий кашель у мого колеги з'явився від пилу на будівництві. Моя подруга скаржиться, що у неї болить голова від гучної музики. Ввечері ми підемо купувати ефективні краплі від нежиті.

> *Right now I have a very sore throat from cold water. This terrible cough of my colleague appeared from the dust at the construction site. My friend complains that her head hurts from loud music. In the evening we will go to buy effective drops for a runny nose.*

At the end of your visit, the doctor will usually give you some professional advice and write out a **рецепт** (prescription). These instructions often combine simple imperative verbs with the quantity words we learned earlier, which naturally require the Genitive case. Finally, the doctor will tell you to go to the **аптека** (pharmacy) to buy your **ліки** (medicine).

Лікар серйозно дивиться на брата і каже: пийте багато теплої води та більше відпочивайте. Він радить їсти багато свіжих фруктів і менше цукру. Потім він виписує рецепт і каже йти в найближчу аптеку. Там ми купимо всі необхідні ліки.

> *The doctor looks seriously at my brother and says: drink a lot of warm water and rest more. He advises eating a lot of fresh fruits and less sugar. Then he writes a prescription and says to go to the nearest pharmacy. There we will buy all the necessary medicine.*

<!-- INJECT_ACTIVITY: quiz-choose-the-correct-genitive-phrase-for-health-complaints-and-remedies -->

## В аптеці та повсякденне здоров'я (~600 words total)

When you go to the **аптека** (pharmacy), you can ask for **ліки** (medicine). The pharmacist can give you excellent advice if your symptoms are mild and you do not yet have a **рецепт** (prescription). Let's look at a typical conversation where someone asks for medicine. Notice how the patient describes their condition and how the pharmacist responds with a solution.

> — **Фармацевт:** Добрий день! Чим я можу допомогти? *(Good day! How can I help?)*
> — **Пацієнт:** Добрий день. Мені потрібні краплі від нежиті. І ще, що ви порадите від кашлю? *(Good day. I need drops for a runny nose. And also, what do you recommend for a cough?)*
> — **Фармацевт:** У вас є температура або алергія? *(Do you have a fever or an allergy?)*
> — **Пацієнт:** Ні, температури немає. Але я зовсім не маю апетиту. *(No, there is no fever. But I have absolutely no appetite.)*
> — **Фармацевт:** Ось хороші ліки від кашлю. Вони продаються без рецепта. *(Here is good medicine for a cough. They are sold without a prescription.)*

In Ukrainian, when we buy medicine, we literally ask for a remedy *against* the symptom. We use the preposition **від** followed immediately by the Genitive case. For example, you ask for something against a **кашель** (cough). This is a very common structure, as it differs from the English phrase "for a cough". You will use this exact pattern for almost every remedy you buy.

Коли ми йдемо в аптеку, ми купуємо ліки від кашлю або краплі від нежиті. Якщо у вас сильно болить голова, вам потрібні ефективні таблетки від головного болю. Зверніть увагу на закінчення чоловічого роду в родовому відмінку. Слова «кашель» та «біль» мають закінчення «-ю».

> *When we go to the pharmacy, we buy medicine for a cough or drops for a runny nose. If your head hurts a lot, you need effective pills for a headache. Pay attention to the masculine endings in the Genitive case. The words "кашель" (cough) and "біль" (pain) have the "-ю" ending.*

There are other essential prepositions that require the Genitive case. You will often see the preposition **для** (for) to indicate purpose, such as vitamins for your **здоров'я** (health). You will also use **без** (without), and **після** (after) or **до** (before) for instructions on when to take your medication. 

Ці вітаміни дуже корисні для здоров'я. Ви можете купити ці таблетки без рецепта від вашого лікаря. Завжди уважно читайте інструкцію, коли купуєте новий сироп. Деякі препарати треба приймати до їжі, а інші — тільки після їжі.

> *These vitamins are very useful for health. You can buy these pills without a prescription from your doctor. Always read the instructions carefully when you buy a new syrup. Some medications need to be taken before a meal, and others — only after a meal.*

:::info
**Grammar box** — The Genitive case is triggered by specific prepositions. In health contexts, remember these essential triggers: **від** (from/against), **для** (for), **без** (without), **до** (before), and **після** (after).
:::

Everyday health and diet connect directly back to the quantity concepts we used at the **ринок** (market). Eating well means making smart choices about how much of certain foods we consume. Whether you are asking for a **кілограм** (kilogram) of vegetables or deciding to drink a **пляшка** (bottle) of water, you are managing quantities with the Genitive case.

Важливо завжди дбати про здоров'я. Лікарі радять їсти мало цукру і солі, але багато свіжих фруктів. Вчора на ринку я купив кілограм яблук і кілограм моркви. Кожного дня я випиваю одну велику пляшку чистої води. Я також намагаюся пити чай без кофеїну.

> *It is important to always care about health. Doctors advise eating little sugar and salt, but a lot of fresh fruits. Yesterday at the market I bought a kilogram of apples and a kilogram of carrots. Every day I drink one large bottle of clean water. I also try to drink tea without caffeine.*

<!-- INJECT_ACTIVITY: match-up-match-health-problems-to-their-remedies -->

The Genitive case is the ultimate connector in everyday Ukrainian life. It is essential for navigating daily situations smoothly. You use it to specify a quantity when shopping, to state that you lack a **температура** (temperature), or to say you have no **апетит** (appetite). Mastering these practical patterns will make you confident in both the market and the clinic.

Родовий відмінок допомагає нам у багатьох життєвих ситуаціях. Ми часто просимо кілограм яблук або купуємо таблетки від болю. Також ми кажемо лікареві, що у нас немає температури. Це дуже корисна і важлива граматика.

> *The Genitive case helps us in many life situations. We often ask for a kilogram of apples or buy pills for pain. Also, we tell the doctor that we have no fever. This is very useful and important grammar.*

<!-- INJECT_ACTIVITY: true-false-judge-whether-shopping-and-health-phrases-use-the-genitive-correctly -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: shopping-and-health
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 15/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
