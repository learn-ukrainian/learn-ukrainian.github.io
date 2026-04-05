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

(No injection markers found in prose. All activities will go to workbook.)

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


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

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

Український **ринок** (market) або **базар** (bazaar) — це особливе місце. Тут люди не просто купують їжу, а ще й активно спілкуються. Українці дуже люблять ходити на базар у вихідні. 

When you visit a Ukrainian market, the experience is different from a standard supermarket. You will speak with vendors, ask about products, discuss the weather, and even try the food before buying. Every vendor will proudly tell you their food is **свіжий** (fresh) and **домашній** (homemade). It is normal to ask to **скуштувати** (to taste) a piece of fruit or cheese. To navigate the market confidently, you need to know how to ask for specific quantities of different items. This is where the Genitive case becomes your best tool for everyday survival.

> — **Продавець:** Добрий день! Підходьте, дивіться! Усе свіже, домашнє! *(Good day! Step right up, look! Everything is fresh, homemade!)*
> — **Покупець:** Добрий день. А можна скуштувати цей сир? *(Good day. May I taste this cheese?)*
> — **Продавець:** Звісно, беріть! Дуже смачно. Я сам робив. *(Of course, take it! Very tasty. I made it myself.)*
> — **Покупець:** Дійсно дуже смачний сир. *(Indeed a very tasty cheese.)*

When buying fresh produce like vegetables, fruits, or meat, you will almost always use weights. The most common units are **кілограм** (kilogram) and **півкіло** (half a kilo). The grammatical rule is strict: after measurement words, the item you are buying must be in the Genitive case. For uncountable items or singular concepts, you use the Genitive singular. For countable items like apples or tomatoes, you must use the Genitive plural. Vendors will often ask exactly how much you need.

**Читаємо українською:**
Дайте мені **кілограм помідорів** (a kilogram of tomatoes).
Мені потрібно **півкіло картоплі** (half a kilo of potatoes).
Зважте, будь ласка, **два кілограми яблук** (weigh, please, two kilograms of apples).
Вона сьогодні купила **кілограм м'яса** (she bought a kilogram of meat today).
Я хочу купити **півкіло сиру** (I want to buy half a kilo of cheese).
Скільки коштує **кілограм огірків**? (How much does a kilogram of cucumbers cost?)

For liquids and items sold in specific containers, the grammar rule is exactly the same as with weights. The container word is the main noun, and it is followed by the substance in the Genitive case. You will frequently need words like **пляшка** (bottle), **літр** (liter), and **банка** (jar). Another very useful container word is **склянка** (glass), which is often used when asking for a drink at a café or when buying berries measured by the glass at the market.

**Читаємо українською:**
Мені потрібна одна велика **пляшка води** (I need one large bottle of water).
Дайте, будь ласка, один **літр молока** (give me, please, one liter of milk).
Моя бабуся продає велику **банку меду** (my grandmother is selling a large jar of honey).
Я дуже хочу випити **склянку соку** (I really want to drink a glass of juice).
Він купив на базарі **літр олії** (he bought a liter of oil at the market).
Бабуся продає малину, одна **склянка ягід** (grandmother is selling raspberries, one glass of berries).

Some items have specific counting or packaging words. In Ukraine, eggs are typically counted and sold by tens, not dozens. The word for a group of ten is **десяток** (ten). Many dry goods or dairy products are sold in a **пачка** (pack/packet). Just like with weights and containers, the item that follows these quantity words takes the Genitive case.

**Читаємо українською:**
Дайте мені, будь ласка, **десяток яєць** (give me, please, ten eggs).
Мені потрібна одна **пачка масла** (I need one pack of butter).
Він забув купити **пачку солі** (he forgot to buy a pack of salt).
Я візьму на завтра один **десяток яєць** (I will take one ten of eggs for tomorrow).
Вона купила в магазині **пачку чаю** (she bought a pack of tea in the store).
Дайте ще **пачку цукру** (give me also a pack of sugar).

Sometimes you only want a specific portion of something, not the whole item. This is called the partitive Genitive. To ask for a piece or a slice, use words like **шматок** (piece) or **скибка** (slice). For a smaller piece, you can use the diminutive form **шматочок** (small piece). This vocabulary is especially useful when buying bread, cheese, meat, and traditional Ukrainian foods like salo at the farmer's market.

**Читаємо українською:**
Відріжте мені невеликий **шматок сиру** (cut me a small piece of cheese).
Я з'їв на сніданок тільки одну **скибку хліба** (I ate only one slice of bread for breakfast).
Дайте мені дуже смачний **шматочок сала** (give me a very tasty small piece of lard).
Він відрізав великий **шматок м'яса** (he cut a large piece of meat).
Вона з радістю відкусила **скибку кавуна** (she happily took a bite of a slice of watermelon).
Я хочу маленький **шматок торта** (I want a small piece of cake).

Let's see how all these phrases come together in a real market situation. Listen to how the buyer asks for specific quantities and how the vendor interacts with them, offering tastes and discussing the quality of the food.

> — **Продавець:** Підходьте, купуйте! Свіжі овочі та фрукти! *(Step right up, buy! Fresh vegetables and fruits!)*
> — **Покупець:** Добрий день. Дайте, будь ласка, кілограм **помідорів** (of tomatoes). *(Good day. Give me, please, a kilogram of tomatoes.)*
> — **Продавець:** Звісно. Які бажаєте? Ось ці дуже **солодкі** (sweet). *(Of course. Which ones do you want? These are very sweet.)*
> — **Покупець:** Добре, давайте їх. І ще півкіло **огірків** (of cucumbers). *(Good, let's have them. And also half a kilo of cucumbers.)*
> — **Продавець:** Ось, тримайте. Хочете скуштувати виноград? Дуже смачний! *(Here, take them. Do you want to taste the grapes? Very tasty!)*
> — **Покупець:** Ні, дякую. Це все. *(No, thank you. That's all.)*

Finally, you need to know how to ask about the price. At a traditional market, prices might not always be written on signs. You can point to an item and ask **По скільки...?** (How much for...?). When you have finished your order, you can politely ask **Скільки з мене?** (How much do I owe? - literally "How much from me?"). If a price seems high, it is **дорого** (expensive), but a good deal is **дешево** (cheap).

**Читаємо українською:**
Скажіть, будь ласка, **по скільки помідори** сьогодні? (Tell me, please, how much are the tomatoes today?)
Дякую за ці покупки. **Скільки з мене**? (Thank you for these purchases. How much do I owe?)
На цьому ринку дуже **дешево** купувати овочі (it is very cheap to buy vegetables at this market).
Ці яблука коштують занадто **дорого** для мене (these apples cost too expensive for me).
Скільки коштує **кілограм яблук**? (How much does a kilogram of apples cost?)
Це дуже **дорого**, я не буду купувати (this is very expensive, I will not buy).

<!-- INJECT_ACTIVITY: fill-in, focus on quantity + Genitive forms in a market context, 8 items -->


## У лікаря: що вас турбує?

When you feel unwell, you visit a **поліклініка** (clinic) or go directly to the **кабінет лікаря** (doctor's office). Medical consultations in Ukraine follow a standard etiquette. After a polite greeting, the doctor will usually ask you to describe your symptoms. The most common opening question is **Що вас турбує?** (What is bothering you?) or **На що скаржитесь?** (What are you complaining about?). Knowing how to answer these questions accurately is essential for getting the right help. You will use the Genitive case frequently to explain what you feel or, just as importantly, what you do not feel.

**Читаємо українською:**
Я йду в **поліклініку** на десяту годину (I am going to the clinic at ten o'clock). Де знаходиться **кабінет лікаря**? (Where is the doctor's office located?). Заходьте, сідайте, **що вас турбує** сьогодні? (Come in, sit down, what is bothering you today?). **На що скаржитесь**, пане Іване? (What are you complaining about, Mr. Ivan?). Лікар уважно слухає пацієнта (The doctor carefully listens to the patient).

In English, you say "I don't have a fever." In Ukrainian, expressing the absence of a symptom requires the word **немає** (there is no) followed by the Genitive case. This is a fundamental rule: negation with **немає** always takes the Genitive. For example, the Nominative word **температура** (fever, temperature) becomes **температури** (of fever). If you want to say you have no appetite, **апетит** (appetite) becomes **апетиту**. If you feel exhausted, you can say you have no energy, using the plural word **сили** (strength, energy) in the Genitive plural: **сил**.

**Читаємо українською:**
У мене сьогодні зовсім **немає температури** (I have absolutely no fever today). Пацієнт каже, що у нього **немає апетиту** (The patient says that he has no appetite). Після важкої роботи у мене **немає сил** іти в магазин (After hard work I have no energy to go to the store). У неї **немає кашлю**, тільки легкий нежить (She has no cough, only a mild runny nose). У дитини **немає алергії** на ці ліки (The child has no allergy to this medicine).

Sometimes you need to explain the cause of your discomfort. To say that something hurts or happens "from" or "due to" a specific trigger, use the preposition **від** (from) followed by the Genitive case. For instance, if your hands hurt from the cold weather, the word **холод** (cold) changes to **холоду**. If you have a cough caused by an allergic reaction, **алергія** (allergy) becomes **алергії**. If dust makes you sneeze, **пил** (dust) changes to **пилу**.

**Читаємо українською:**
Мої руки дуже болять **від холоду** (My hands hurt a lot from the cold). У неї сильний кашель **від алергії** на котів (She has a strong cough from an allergy to cats). Я постійно чхаю **від пилу** в цій старій кімнаті (I constantly sneeze from the dust in this old room). Мої очі червоні **від вітру** на вулиці (My eyes are red from the wind outside). Він має проблеми зі шлунком **від стресу** (He has stomach problems from stress).

When describing pain, you will often name body parts. If you are pointing out where it hurts, you might use constructions that require the Genitive. For example, saying "pain of the throat" uses the Genitive form of **горло** (throat) — **горла**. The word **спина** (back) becomes **спини**, and **голова** (head) becomes **голови**. Doctors also use formal medical phrases like **біль у ділянці серця** (pain in the heart area), where **серце** (heart) is in the Genitive: **серця**. Conversely, if you want to report that a pain has stopped, you use **немає** with the Genitive of **біль** (pain) — **немає болю** (no pain).

**Читаємо українською:**
У мене сильний біль **горла** (I have a strong pain of the throat). Лікар оглядає пацієнта через постійний біль **спини** (The doctor examines the patient because of constant back pain). Чи є у вас біль у ділянці **серця**? (Do you have pain in the heart area?). Після таблетки у мене більше **немає болю** (After the pill I have no more pain). Вона часто скаржиться на біль **голови** (She often complains about pain of the head).

> — **Лікар:** Добрий день! Проходьте, сідайте. **Що вас турбує**? *(Good day! Come in, sit down. What is bothering you?)*
> — **Пацієнт:** Добрий день. У мене сильний **кашель** (cough) і **нежить** (runny nose). *(Good day. I have a strong cough and a runny nose.)*
> — **Лікар:** Зрозуміло. А чи є у вас висока температура? *(Understood. And do you have a high fever?)*
> — **Пацієнт:** Ні, температури **немає**, але я відчуваю слабкість. *(No, there is no fever, but I feel weakness.)*
> — **Лікар:** Добре, я вас огляну. Відкрийте рот. Так, горло червоне. Тепер послухаю ваші **легені** (lungs). **Дихайте** (breathe) глибоко. Не дихайте. *(Good, I will examine you. Open your mouth. Yes, the throat is red. Now I will listen to your lungs. Breathe deeply. Do not breathe.)*
> — **Пацієнт:** Це щось серйозне? *(Is this something serious?)*
> — **Лікар:** Ні, це звичайна застуда. У легенях чисто. *(No, this is a common cold. The lungs are clear.)*

After the examination, the doctor gives recommendations. Medical advice often involves prescribing quantities of food, drink, or rest, which requires the Genitive case. Words like **багато** (much, a lot) and **мало** (little, few) are followed by the Genitive. For example, a doctor might tell you to drink a lot of water: **вода** (water) becomes **води**. They might advise you to have less stress (**менше стресу**) and more rest (**більше відпочинку**).

**Читаємо українською:**
Лікар каже, що треба пити **багато води** щодня (The doctor says that one needs to drink a lot of water every day). Вам потрібно мати **менше стресу** на роботі (You need to have less stress at work). Для здоров'я корисно їсти **багато фруктів** (For health it is useful to eat a lot of fruits). Спіть більше, вам треба **більше відпочинку** (Sleep more, you need more rest). Вона їсть дуже **мало цукру** зараз (She eats very little sugar now).

<!-- INJECT_ACTIVITY: quiz, focus on choosing correct Genitive phrase for complaints and symptoms, 8 items -->


## В аптеці та повсякденне здоров'я

When you feel unwell, you will likely visit a pharmacy. In Ukraine, you ask a pharmacist for advice or present a prescription from your doctor. 

У місті працює нова, сучасна **аптека** (pharmacy). Там працює досвідчений **фармацевт** (pharmacist). Ви можете купити різні **ліки** (medicine) або корисні **вітаміни** (vitamins). Якщо ліки дуже сильні, вам обов'язково потрібен **рецепт** (prescription) від вашого лікаря.

To ask for a recommendation for a specific problem, use the phrase «Що ви порадите від...?» (What do you advise for...?), followed by the Genitive case of your symptom. This is the most natural way to explain what you need.

> — **Клієнт:** Добрий день! **Що ви порадите від** (What do you advise for) кашлю? *(Good day! What do you advise for a cough?)*
> — **Фармацевт:** Добрий день. У нас є дуже хороший сироп. *(Good day. We have a very good syrup.)*
> — **Клієнт:** Дякую. А ці вітаміни можна купити без рецепта? *(Thank you. And can one buy these vitamins without a prescription?)*
> — **Фармацевт:** Так, звичайно, вони завжди є. *(Yes, of course, they are always available.)*

The preposition **від** (from/against) always requires the Genitive case. In a pharmacy, this structure mirrors the market phrases like a "bottle of water", but here it means "medicine against [symptom]". You are asking for a remedy to remove the problem. For example, **кашель** (cough) becomes **кашлю**. **Нежить** (runny nose) becomes **нежиті**. **Біль** (pain) becomes **болю**.

**Читаємо українською:**
Мені терміново потрібні **ліки від кашлю** (medicine for cough).
Дайте, будь ласка, хороші **краплі від нежиті** (drops for runny nose).
У вас є ефективні **таблетки від головного болю** (pills for headache)?
Цей сироп дуже добре допомагає **від болю** (from pain) у горлі.
Я хочу купити щось нове **від алергії** (for allergy).
Моя мама шукає крем **від опіків** (for burns).

When a pharmacist explains how to take your medicine, they use time-based prepositions. The prepositions **після** (after), **до** (before), and **під час** (during) also require the Genitive case. This helps you understand exactly when to use your treatment. The word **їжа** (meal/food) becomes **їжі**. **Сніданок** (breakfast) becomes **сніданку**. **Обід** (lunch) becomes **обіду**.

> — **Пацієнт:** Як правильно приймати ці таблетки кожного дня? *(How to correctly take these pills every day?)*
> — **Фармацевт:** Пийте одну таблетку **після їжі** (after a meal). *(Drink one pill after a meal.)*
> — **Пацієнт:** А ці краплі від нежиті? *(And these drops for a runny nose?)*
> — **Фармацевт:** Їх треба приймати **до обіду** (before lunch). *(They need to be taken before lunch.)*
> — **Пацієнт:** Чи можна пити воду **під час сніданку** (during breakfast)? *(Can one drink water during breakfast?)*
> — **Фармацевт:** Так, пийте багато чистої води. *(Yes, drink a lot of clean water.)*

**Читаємо українською:**
Приймайте ці вітаміни тільки **після сніданку** (after breakfast).
Я завжди п'ю гарячий чай **до обіду** (before lunch).
Не можна пити міцну каву **під час їжі** (during a meal).

The Genitive case is also essential for describing healthy habits and daily dietary choices. The preposition **для** (for) shows purpose, while **без** (without) shows absence. Both prepositions strictly take the Genitive. **Здоров'я** (health) becomes **здоров'я**, and **імунітет** (immunity) becomes **імунітету**. **Цукор** (sugar) becomes **цукру**, and **кофеїн** (caffeine) becomes **кофеїну**.

**Читаємо українською:**
Регулярний спорт дуже корисний **для здоров'я** (for health).
Свіжі фрукти та овочі важливі **для імунітету** (for immunity).
Я щоранку п'ю каву **без цукру** (without sugar).
Дайте мені, будь ласка, зелений чай **без кофеїну** (caffeine-free).
Ми часто їмо свіжі салати **без солі** (without salt).

<!-- INJECT_ACTIVITY: match-up, focus on matching health problems to their remedies using "від", 8 items -->
<!-- INJECT_ACTIVITY: true-false, focus on correct usage of Genitive case in shopping and health instructions, 8 items -->

Throughout this module, you have seen how the Genitive case connects many different everyday situations. Whether you are buying fresh food at a noisy market, speaking to a doctor, or visiting a quiet pharmacy, the grammatical patterns remain identical. 

You use it for specific quantities, indicating that you want a part of a larger whole: **кілограм яблук** (a kilogram of apples). You use it to express complete absence or a missing element: **немає яблук** (there are no apples) or чорна кава **без цукру** (black coffee without sugar). Finally, you use it to show purpose, origin, or a specific remedy: ефективні **ліки від кашлю** (effective medicine for a cough). Master these patterns, and you will navigate Ukrainian shops and health services with confidence.

**Читаємо українською:**
На ринку я часто купую **кілограм яблук** (a kilogram of apples).
Сьогодні у мене вдома **немає яблук** (there are no apples).
В аптеці я купую **ліки від кашлю** (medicine for cough).
Він п'є мінеральну воду **без газу** (without gas) **для здоров'я** (for health).
У лікаря пацієнт завжди просить **рецепт від болю** (prescription for pain).


## Підсумок

Перевірте себе, чи знаєте ви відповіді на ці запитання: *(Check yourself if you know the answers to these questions:)*
- Як сказати "a kilo of tomatoes" та "a bottle of water"?
- Як сказати "I don't have a fever"?
- Який прийменник ми вживаємо, коли просимо ліки "for" (against) a headache?
- Як сказати "take medicine after a meal"?

The Genitive case is our primary tool for expressing specific amounts, the absence of something, and the target of a medical remedy. Whether you ask for **кілограм помідорів** (a kilogram of tomatoes), declare **у мене немає температури** (I don't have a fever), or buy **ліки від головного болю** (medicine for a headache), the grammatical rules remain identical. The prepositions **від** (for/against) and **після** (after) are also reliable indicators that the Genitive case is required. Master these simple structures, and you will communicate with confidence.

**Читаємо українською:**
Я часто ходжу на ринок купувати свіжі продукти. Сьогодні мені потрібен кілограм помідорів та пляшка води. Потім я маю піти до аптеки. Там я купую ефективні ліки від головного болю. У мене немає температури, але я трохи хворію. Я приймаю ці таблетки тільки після їжі.

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

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
