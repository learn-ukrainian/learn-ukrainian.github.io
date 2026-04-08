<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/shopping-and-health.yaml` file for module **15: На ринку та у лікаря** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-market-genitive -->`
- `<!-- INJECT_ACTIVITY: quiz-health-phrases -->`
- `<!-- INJECT_ACTIVITY: match-up-remedies -->`
- `<!-- INJECT_ACTIVITY: true-false-grammar -->`

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
## На ринку: скільки вам? (At the Market: How Much Do You Want?)

«Ринок — це серце українського міста. Тут завжди багато людей, свіжі продукти та цікаві розмови.» (A market is the heart of a Ukrainian city. Here there are always many people, fresh products, and interesting conversations.)

Going to a **ринок** (market) in Ukraine is more than just shopping; it is a cultural experience. Whether you visit the historic **Бессарабський ринок** (Besarabskyi market) in the center of Kyiv, the bustling **Житній ринок** (Zhytnii market) in Podil, or a small local bazaar in your neighborhood, the expectation is the same: quality and freshness. Supermarkets are convenient, but Ukrainians often prefer the market for fresh vegetables, meat, and dairy. Here, you buy directly from the farmer or vendor. You can ask about the origin of the food, request to taste a piece of cheese, and negotiate quantities. The interaction is direct, personal, and requires specific vocabulary. You do not just put items in a basket; you must tell the **продавець** (vendor) exactly what you want and how much.

:::note
**Читаємо українською (Reading in Ukrainian)**
Українці люблять купувати свіжі продукти на ринку.
Там можна купити домашнє молоко, сир та м'ясо.
Продавці часто пропонують скуштувати їхній товар.
Вони кажуть: «Спробуйте, це дуже смачно!»
На ринку завжди можна знайти найсвіжіші овочі та фрукти.
:::

When you ask for a specific amount of food at the market, you must use the Genitive case. In Ukrainian, words that denote a measure of weight, volume, or quantity act like containers. The item you are measuring goes into the Genitive case, answering the question "a kilogram of what?" or "a bottle of what?". This rule applies every time you use a unit of measurement.

[Кількість] + [Іменник у родовому відмінку]
([Quantity] + [Noun in Genitive])
кілограм (kilogram) + цукор (sugar) → кілограм **цукру**
літр (liter) + молоко (milk) → літр **молока**
пляшка (bottle) + олія (oil) → пляшка **олії**

:::tip
**Читаємо українською (Reading in Ukrainian)**
Дайте, будь ласка, кілограм цукру.
Мені потрібен один літр домашнього молока.
Я хочу купити пів кілограма свіжого сиру.
Ось ваша пляшка олії.
У мене є велика склянка води.
:::

This structure is essential. You cannot just say the unit and the item in their dictionary forms. The item being measured must take its Genitive singular ending.

Beyond kilograms and liters, you will use many container and portion words when shopping or cooking. These words function exactly like units of measurement. The container is the main word, and the substance inside it takes the Genitive case. 

Let us look at common examples you will hear at the market or read in recipes:
- **пачка** (pack) + масло (butter) → пачка **масла** (a pack of butter)
- **банка** (jar) + мед (honey) → банка **меду** (a jar of honey)
- **шматок** (piece) + сало (salo/pork fat) → шматок **сала** (a piece of salo)
- **склянка** (glass) + сік (juice) → склянка **соку** (a glass of juice)
- **десяток** (a dozen/ten) + яйця (eggs) → десяток **яєць** (a dozen eggs)

:::note
**Читаємо українською (Reading in Ukrainian)**
Мені потрібна одна пачка вершкового масла.
Чи є у вас банка гречаного меду?
Дайте мені, будь ласка, невеликий шматок сала.
Я випив склянку яблучного соку на сніданок.
Купіть один десяток свіжих яєць.
:::

Notice that «яєць» is in the Genitive plural, because a dozen contains multiple individual items, whereas honey or butter is an uncountable substance in the Genitive singular.

When you look at masculine nouns that denote substances, materials, or collective items, you might notice a specific pattern. Why do we say «кілограм **сиру**» (a kilogram of cheese) and «банка **меду**» (a jar of honey) with an «-у» ending, instead of the «-а» ending we see in words like «брат» → «брата»? In Ukrainian, abstract concepts and uncountable materials in the masculine gender often take the endings **-у** or **-ю** in the Genitive singular. This is called the Partitive Genitive. It shows that you are taking a portion of a larger mass.

Common masculine substances ending in -у/-ю:
- сир → **сиру** (cheese)
- цукор → **цукру** (sugar)
- чай → **чаю** (tea)
- сік → **соку** (juice)
- часник → **часнику** (garlic)

:::tip
**Читаємо українською (Reading in Ukrainian)**
Я хочу випити чашку гарячого чаю.
Додайте трохи цукру у вашу каву.
Купіть кілограм твердого сиру на ринку.
Дайте мені головку свіжого часнику.
У нас немає томатного соку.
:::

This distinction is a beautiful and natural feature of the Ukrainian language. Remember: if you can pour it, scoop it, or cut a piece from a larger block, a masculine word will likely end in -у or -ю.

When paying for your groceries, you need to understand prices and how numbers interact with nouns. The currency is the **гривня** (hryvnia). Asking the price is simple: «**Скільки коштує...?**» (How much does it cost?). When the vendor answers, the form of the noun depends on the number preceding it. We learned this rule for objects, and it applies exactly the same way to units of weight and currency.

- **1** takes the Nominative singular: одна **гривня**, один **кілограм**.
- **2, 3, 4** take the Nominative plural: дві **гривні**, три **кілограми**, чотири **пляшки** (bottles).
- **5 and above** take the Genitive plural: п'ять **гривень**, десять **кілограмів**, двадцять **яєць**.

:::note
**Читаємо українською (Reading in Ukrainian)**
Скільки коштують ці яблука?
Вони коштують сорок п'ять гривень за кілограм.
Дайте мені два кілограми, будь ласка.
З вас рівно дев'яносто гривень.
Це дуже дешево, а помідори дорогі.
:::

Let us put this grammar into practice. Read this natural exchange between a **покупець** (buyer) and a продавець.

> — **Продавець:** Добрий день! Що вам запропонувати? *(Good day! What can I offer you?)*
> — **Покупець:** Добрий день. Скажіть, будь ласка, скільки коштують ці помідори? *(Good day. Tell me, please, how much do these tomatoes cost?)*
> — **Продавець:** Вісімдесят гривень за кілограм. Вони дуже свіжі та солодкі. *(Eighty hryvnias per kilogram. They are very fresh and sweet.)*
> — **Покупець:** Добре. Дайте мені півтора кілограма, будь ласка. І ще кілограм огірків. *(Good. Give me one and a half kilograms, please. And also a kilogram of cucumbers.)*
> — **Продавець:** Звісно. Огірки по шістдесят гривень. Щось ще? *(Of course. Cucumbers are at sixty hryvnias. Anything else?)*
> — **Покупець:** Ні, це все. Скільки з мене? *(No, that is all. How much do I owe?)*
> — **Продавець:** З вас сто вісімдесят гривень. *(You owe one hundred eighty hryvnias.)*
> — **Покупець:** Ось, візьміть. Дякую! *(Here, take it. Thank you!)*
> — **Продавець:** Дякую вам. Смачного! *(Thank you. Enjoy your meal!)*

When you visit a market, you will notice that vendors try to create a warm, friendly atmosphere. They often use diminutive forms of words to sound welcoming and encouraging. Instead of «картопля» (potatoes), you might hear «**картопелька**» (nice little potatoes). Instead of «яблука» (apples), they might offer «**яблучка**» (sweet little apples). This is a very common feature of everyday Ukrainian. You do not need to use these forms yourself, but recognizing them helps you feel the cultural warmth of the interaction. Simply reply politely with «**Дякую**» (Thank you) and say «**На все добре**» (All the best) when leaving.

<!-- INJECT_ACTIVITY: fill-in-market-genitive -->


## У лікаря: що вас турбує?

Коли ви погано почуваєтесь, вам треба звернутися до лікаря. В Україні люди зазвичай ідуть у поліклініку або в приватну лікарню. Лікар завжди спочатку запитає вас про ваші симптоми.

When you feel unwell in Ukraine, the first step is usually to visit a **поліклініка** (clinic) or a private hospital to see a **терапевт** (general practitioner). The medical culture here is quite direct. When you enter the office, the doctor will not ask you about your day. Instead, they will start with a very specific, practical question.

«**Що вас турбує?**» (What is bothering you?) is the standard opening phrase. You will also often hear «**На що скаржитесь?**» (What are you complaining about?). To answer these questions, you need to describe your physical state accurately.

Кожна людина іноді хворіє. У мене часто болить голова. Мій друг каже, що у нього болить спина.

In English, you say "I have a headache" or "My throat hurts". In Ukrainian, we almost exclusively use the construction «**у мене болить...**» (it hurts at my place) to describe pain. This is very similar to how we say "I have", but instead of an object, the subject of the sentence is the body part that hurts.

Because the body part is the subject, it must be in the Nominative case. The verb «**боліти**» (to hurt, to ache) must agree with the number of the body part. If one thing hurts, use the singular «**болить**». If multiple things hurt, use the plural «**болять**».

- **У мене болить...** (Singular) + **голова** (head), **горло** (throat), **живіт** (stomach), **спина** (back).
- **У мене болять...** (Plural) + **ноги** (legs), **очі** (eyes), **коліна** (knees), **вуха** (ears).

:::note **Читаємо українською (Reading in Ukrainian)**
Лікар завжди питає, що мене турбує.
Сьогодні у мене дуже сильно болить голова.
Мій брат каже, що у нього болить живіт після обіду.
Після довгої прогулянки парком у мене болять ноги.
У мого дідуся часто болять коліна.
:::

Минулого тижня я був хворий, але зараз у мене немає температури.

When visiting a doctor, you also need to explain what symptoms you *do not* have. We already know that the word «**немає**» (there is no) requires the Genitive case. This rule is extremely important for medical conversations.

When a doctor asks «**Чи є у вас температура?**» (Do you have a fever?), your negative answer must use the Genitive.

- **немає температури** (no fever)
- **немає апетиту** (no appetite)
- **немає кашлю** (no cough)
- **немає сил** (no energy)
- **немає нежиті** (no runny nose)

:::tip **Читаємо українською (Reading in Ukrainian)**
Сьогодні я відчуваю себе значно краще.
У мене вже немає високої температури.
Але я досі слабкий, у мене зовсім немає сил.
Лікар сказав, що у мене немає грипу.
У хворої дитини немає апетиту, вона нічого не їсть.
:::

Лікар виписав мені сильні ліки від кашлю.

The preposition «**від**» (from, against) always takes the Genitive case. In a medical context, it has two very important functions.

First, it describes the cause of your pain or discomfort. For example, «**У мене болить горло від холоду**» (My throat hurts from the cold).

Second, and most importantly for a pharmacy or clinic, «від» describes the *purpose* of a medicine. In English, you take medicine "for" a cough. In Ukrainian, you take medicine "against" or "from" it.

- **ліки від кашлю** (cough medicine)
- **краплі від нежиті** (drops for a runny nose)
- **таблетки від головного болю** (headache pills)
- **сироп від болю у горлі** (syrup for a sore throat)

:::note **Читаємо українською (Reading in Ukrainian)**
> — **Покупець:** Добрий день. Мені потрібні ліки від алергії. *(Good day. I need medicine for allergy.)*
> — **Фармацевт:** Добрий день. У вас є рецепт? *(Good day. Do you have a prescription?)*
> — **Покупець:** Ні, немає. Дайте щось без рецепта. *(No, I do not. Give me something without a prescription.)*
> — **Фармацевт:** Ось хороші таблетки. Вони дуже допомагають. *(Here are good pills. They help a lot.)*
:::

Let us see how these phrases come together in a typical visit to the clinic. Read this dialogue between a **пацієнт** (patient) and a **лікар** (doctor).

> — **Лікар:** Добрий день! Проходьте, сідайте. Що вас турбує? *(Good day! Come in, sit down. What is bothering you?)*
> — **Пацієнт:** Добрий день. Я погано почуваюсь. Я застудився. *(Good day. I feel unwell. I caught a cold.)*
> — **Лікар:** Розумію. У вас болить горло? *(I understand. Does your throat hurt?)*
> — **Пацієнт:** Так, болить горло і дуже болить голова. *(Yes, my throat hurts and my head hurts a lot.)*
> — **Лікар:** Чи є у вас температура? *(Do you have a fever?)*
> — **Пацієнт:** Ні, температури немає. Але у мене сильний кашель і немає сил. *(No, there is no fever. But I have a bad cough and no energy.)*
> — **Лікар:** Я випишу вам рецепт. Ось ліки від кашлю. *(I will write you a prescription. Here is cough medicine.)*
> — **Пацієнт:** Дякую. Скільки разів на день їх пити? *(Thank you. How many times a day should I drink them?)*
> — **Лікар:** Тричі на день. І вам треба багато відпочивати. *(Three times a day. And you need to rest a lot.)*

Іноді у нас немає сильного болю, але є загальна слабкість. Мені дуже погано і холодно. Мене нудить після вечері.

Sometimes you do not have a specific pain, but your overall state is bad. For these general feelings, Ukrainian uses impersonal constructions. Instead of saying "I feel cold", you say "To me it is cold". The person experiencing the feeling takes the Dative case (which we will study later, but you should learn these fixed phrases now as «**мені**» — to me).

- **Мені погано.** (I feel bad.)
- **Мені краще.** (I feel better.)
- **Мені холодно.** (I am cold.)
- **Мені гаряче.** (I am hot.)

Якщо у вас проблеми зі шлунком, ви використовуєте спеціальне дієслово.

If you feel sick to your stomach, you use a special verb: «**Мене нудить**» (I feel nauseous). 

:::tip **Читаємо українською (Reading in Ukrainian)**
Учора ввечері мені було дуже погано.
Я випив гарячий чай, і зараз мені краще.
Відчини вікно, будь ласка, бо мені гаряче.
Одягни теплий светр, якщо тобі холодно.
Я не хочу їсти, бо мене нудить.
:::

Combining these phrases with the Genitive vocabulary gives you a complete toolkit to explain your health to any doctor.

<!-- INJECT_ACTIVITY: quiz-health-phrases -->


## В аптеці та повсякденне здоров'я

When you visit an **аптека** (pharmacy) in Ukraine, you will find that many common remedies are available over the counter. If you have a light cold or a minor headache, you can easily buy **вітаміни** (vitamins) or simple remedies without seeing a doctor. The key distinction is whether you need a **рецепт** (prescription) or not. When asking for everyday items, you use the Genitive case to specify exactly what the medicine is meant to treat. For example, if you are sneezing, you will ask the pharmacist for **краплі від нежиті** (drops for a runny nose).

:::tip **Читаємо українською (Reading in Ukrainian)**
В Україні є багато аптек на кожній вулиці.
Я часто купую там вітаміни для сім'ї.
Якщо у вас застуда, рецепт не потрібен.
Ви можете купити краплі від нежиті просто так.
Але сильні ліки продають тільки за рецептом.
:::

Understanding how to take medicine correctly requires knowing prepositions that trigger the Genitive case. Two important time prepositions are **після** (after) and **перед** (before). Doctors and pharmacists will often tell you to take pills **після їжі** (after a meal) or to drink a soothing tea **перед сном** (before sleep). The Genitive is also used to describe what a product lacks, using the preposition **без** (without). If you are trying to eat healthier, you might look for food **без цукру** (without sugar) or order your coffee **без кофеїну** (without caffeine).

:::note **Читаємо українською (Reading in Ukrainian)**
Мій дідусь п'є ліки тільки після їжі.
Я завжди п'ю тепле молоко перед сном.
Цей чай дуже смачний, хоча він без цукру.
Лікар сказав мені пити каву без кофеїну.
Я не можу жити без солодкого.
:::

Another vital preposition that takes the Genitive case is **для** (for). In the context of health and shopping, we use «для» to show the main purpose or beneficiary of an item. When you buy fresh produce at the market, you are buying it **для здоров'я** (for health). If you want to boost your immune system, you ask for vitamins **для імунітету** (for immunity). Older people often buy herbal teas **для серця** (for the heart). This grammatical word beautifully connects the food you buy directly to your physical wellbeing.

:::tip **Читаємо українською (Reading in Ukrainian)**
Свіжі овочі та фрукти дуже корисні для здоров'я.
Я купую лимони та мед для імунітету.
Ці таблетки потрібні моїй бабусі для серця.
Спорт і свіже повітря — це найкраще для тіла.
Я роблю цей салат для всієї нашої родини.
:::

Let us look at a practical situation where you need to ask a pharmacist for advice. If you do not know exactly which medicine to buy, you can describe your symptom and simply ask: «**Що ви порадите від...?**» (What do you recommend for...?). Notice how the pharmacist gives instructions using the Genitive prepositions.

> — **Покупець:** Добрий день. Що ви порадите від болю в горлі? *(Good day. What do you recommend for a sore throat?)*
> — **Фармацевт:** Добрий день. Ось дуже хороший сироп. *(Good day. Here is a very good syrup.)*
> — **Покупець:** Він продається без рецепта? *(Is it sold without a prescription?)*
> — **Фармацевт:** Так, звичайно. Це просто сироп на травах. *(Yes, of course. This is just a herbal syrup.)*
> — **Покупець:** Як його правильно приймати? *(How should I take it correctly?)*
> — **Фармацевт:** Пийте двічі на день після їди. А ще візьміть ці краплі. *(Drink it twice a day after a meal. And also take these drops.)*
> — **Покупець:** Дякую. А що у вас є для імунітету? *(Thank you. And what do you have for immunity?)*
> — **Фармацевт:** Візьміть ці вітаміни. Пийте одну таблетку перед сном. *(Take these vitamins. Drink one pill before sleep.)*

Whether you are bargaining for fresh vegetables at a market or seeking relief at a clinic, the Genitive case is the engine of your daily communication. It is the most versatile tool in Ukrainian for defining limits, quantities, and relationships between objects. We use it to quantify the exact amount of food we want, like a **кілограм яблук** (kilogram of apples) or **багато ліків** (a lot of medicine). We use it to express absence, such as asking for tea **без цукру** (without sugar) or telling a doctor we have **немає нежиті** (no runny nose). Finally, we use it to show purpose, from buying a **ніж для хліба** (knife for bread) to taking **ліки від грипу** (medicine for the flu). Mastering these patterns helps you confidently navigate practical life in Ukraine.

:::note **Читаємо українською (Reading in Ukrainian)**
На ринку ми купуємо багато свіжих фруктів.
У лікарні ми кажемо, що у нас немає температури.
В аптеці ми просимо ліки від сильного кашлю.
Ми п'ємо чай без цукру для нашого здоров'я.
Родовий відмінок допомагає нам говорити правильно та чітко.
:::

<!-- INJECT_ACTIVITY: match-up-remedies -->
<!-- INJECT_ACTIVITY: true-false-grammar -->


## Підсумок

**Ви чудово попрацювали!** (You have worked wonderfully!) You learned how to use the Genitive case at a market and a pharmacy. Let us review the core phrases.

*   Як сказати «one kilogram of tomatoes» та «five kilograms of cucumbers»? It is **кілограм помідорів** (a kilogram of tomatoes) and **п'ять кілограмів огірків** (five kilograms of cucumbers).
*   Як ввічливо попросити шматок сиру на ринку? Use the polite request and the Genitive of quantity. You say: «**Дайте, будь ласка, шматок сиру**» (Give me, please, a piece of cheese).
*   Яку фразу використати, якщо у вас болить голова, але немає температури? Use the physical state construction and the word for absence. Say: «**У мене болить голова, але немає температури**» (I have a headache, but no fever).
*   Що ви купите в аптеці «від кашлю»? You can buy **сироп від кашлю** (cough syrup) or **таблетки від кашлю** (cough pills).
*   Коли треба приймати ліки, якщо лікар сказав «після їди»? This instruction means you must take the medicine **після їди** (after eating).

**Здоров'я вам і смачних покупок!** (Good health to you and tasty shopping!)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: shopping-and-health
level: a2

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
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

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
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

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
