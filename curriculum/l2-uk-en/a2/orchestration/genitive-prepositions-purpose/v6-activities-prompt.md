<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-purpose.yaml` file for module **10: Для кого? Без чого? Біля чого?** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->`
- `<!-- INJECT_ACTIVITY: true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-location-descriptions-with-correct-genitive-form -->`
- `<!-- INJECT_ACTIVITY: match-up-match-ukrainian-prepositional-phrases-to-their-english-equivalents -->`
- `<!-- INJECT_ACTIVITY: true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete location descriptions with біля/навпроти/коло + correct Genitive
    form
  items: 8
  type: fill-in
- focus: Choose для, без, or біля to complete everyday sentences
  items: 8
  type: quiz
- focus: Match Ukrainian prepositional phrases to their English equivalents
  items: 8
  type: match-up
- focus: Judge whether preposition + noun form combinations are grammatically correct
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- навчання (studying, education)
- церква (church)
- вокзал (train station)
- річка (river)
required:
- призначення (purpose, destination)
- відпочинок (rest, relaxation)
- допомога (help, assistance)
- сумнів (doubt)
- будинок (building, house)
- зупинка (stop (bus/tram))
- бібліотека (library)
- лікарня (hospital)
- площа (square (city))
- станція (station)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Для кого це? Для + родовий (Who Is It For? Для + Genitive) (~700 words)

> — **Ігор:** Для кого ця ковдра? *(Who is this blanket for?)*
> — **Марта:** Для Олени. Вона завжди мерзне ввечері. *(For Olena. She is always cold in the evening.)*
> — **Ігор:** Добре. А де мій ліхтарик? Без ліхтарика — ніяк! *(Good. And where is my flashlight? Without a flashlight — no way!)*
> — **Марта:** Він у рюкзаку. Ми поставимо намет біля **річки**. *(It is in the backpack. We will put the tent near the **river**.)*
> — **Ігор:** Чудово! Це ідеальне місце для **відпочинку**. *(Great! This is an ideal place for **rest**.)*

Look closely at the small words in the dialogue above: **для** (for), **без** (without), and **біля** (near). These three prepositions are incredibly common in everyday Ukrainian and form the backbone of basic communication. They all share one strict grammatical rule: they always demand the Genitive case (родовий відмінок). Whenever you use these prepositions, the noun, adjective, or pronoun that follows them must change its ending. In this section, we will focus entirely on the preposition **для**.

The preposition **для** is primarily used to express purpose, function, or destination. When you want to explain why a specific object exists, what it is used for, or what an action is meant to achieve, you ask the question «Для чого?» (For what purpose?). The noun that follows this preposition provides the answer and must take the Genitive case. This is a fundamental structure for describing the utility of the things around you in daily life. Whether you are talking about household items, professional tools, or even abstract concepts, the grammatical rule remains the exact same.

Цей новий стіл — для роботи, а не для ігор. Ми купили ці товсті зошити спеціально для **навчання**. Свіже повітря та щоденний спорт дуже корисні для здоров'я. Ця велика кімната має зовсім інше **призначення**.

> *This new desk is for work, and not for games. We bought these thick notebooks specifically for **studying**. Fresh air and daily sports are very useful for health. This large room has a completely different **purpose**.*

It is important to remember that abstract concepts like health, work, or education are frequently paired with **для**. These combinations often translate directly to English structures, making them relatively easy to master once you know the core vocabulary and the corresponding Genitive endings.

Ця програма створена для розвитку бізнесу. Ми збираємо гроші для ремонту. Цей інструмент потрібен для точного вимірювання.

> *This program is created for business development. We are collecting money for repairs. This tool is needed for precise measurement.*

Another major use of **для** is to indicate the intended recipient of an object, a feeling, or an action. When you buy a gift, prepare a meal, or do a favor, you answer the question «Для кого?» (For whom?). Just like with inanimate objects, the person or animal receiving the item must be put into the Genitive case. This is how you clearly show that someone is the primary beneficiary of your actions. It is a structure you will use every time you interact with friends, family, and colleagues.

Це дуже гарний подарунок для мами. Я купив два квитки в театр для мого найкращого друга. Цей великий солодкий торт — для дітей. Ми зараз готуємо приємний сюрприз для нашої нової колеги.

> *This is a very beautiful gift for mom. I bought two tickets to the theater for my best friend. This big sweet cake is for the children. We are currently preparing a pleasant surprise for our new colleague.*

:::note
**Quick tip** — When translating the English word "for", you must be careful to choose the correct Ukrainian equivalent based on context. If "for" means "for the purpose of" or "intended for someone", you should use **для** + Genitive. However, if it means "going to an event" (like "going for a meeting"), Ukrainian uses **на** + Accusative.
:::

To use the preposition **для** correctly in fast-paced conversation, you need to confidently recall the Genitive case endings across all three genders and their different stem types. The preposition itself never changes, but the noun following it always transforms. Let's look closely at how the endings change when we add **для** to everyday words. Notice the distinct patterns for hard and soft stems, and pay special attention to the vowels.

Для чоловічого роду ми найчастіше додаємо закінчення -а або -я. Наприклад, це квиток для брата, а це нова книга для вчителя. Для жіночого роду ми зазвичай використовуємо закінчення -и, -і або -ї. Ось свіжі квіти для сестри, а це гаряча кава для Марії. Для середнього роду закінчення змінюються на -а або -я. Спокій потрібен для щастя, а чиста вода необхідна для щоденного життя.

> *For the masculine gender, we most often add the ending -a or -я. For example, this is a ticket for a brother, and this is a new book for a teacher. For the feminine gender, we usually use the endings -и, -і, or -ї. Here are fresh flowers for a sister, and this is hot coffee for Mariia. For the neuter gender, the endings change to -a or -я. Peace is needed for happiness, and clean water is necessary for daily life.*

The endings might seem overwhelming at first, but they follow highly predictable patterns that you have already started to recognize. By regularly practicing these phrases, the correct Genitive forms will soon become second nature to you.

Finally, there are many high-frequency, everyday phrases built with **для** that you will hear constantly in fluent Ukrainian speech. When using personal pronouns, remember that they also have their own special Genitive forms that you must memorize. For example, the pronoun «ти» (you) becomes «тебе», and «я» (I) becomes «мене». Mastering these set phrases will make your Ukrainian sound much more natural, polite, and grammatically precise.

У мене є невеликий подарунок для тебе. Неділя — це ідеальний час для **відпочинку**. Ця нова інформація дуже важлива для мене. Мені зараз потрібна твоя **допомога** для цього складного проєкту.

> *I have a small gift for you. Sunday is an ideal time for **rest**. This new information is very important to me. I need your **help** right now for this complex project.*

When you want to emphasize that something is done exclusively for someone's benefit, you can combine **тільки** (only) with **для**. This creates a strong emotional resonance in your sentences.

Я роблю це тільки для тебе. Цей сюрприз був підготовлений спеціально для неї. Ми організували це свято для вас.

> *I am doing this only for you. This surprise was prepared specifically for her. We organized this holiday for you.*

<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->

## Без чого? Без + родовий (Without What? Без + Genitive)

The preposition **без** means "without". You will use it constantly to express the absence or lack of something. The noun that follows **без** must always be in the Genitive case, answering the questions **кого?** or **чого?**.

Я завжди п'ю каву без цукру, а мій брат любить чорний чай без молока. Це був дуже довгий день без дощу. Діти пішли гуляти без курток, тому що на вулиці сьогодні дуже тепло. Ми не можемо уявити ранок без смачного сніданку.

> *I always drink coffee without sugar, and my brother likes black tea without milk. It was a very long day without rain. The children went for a walk without jackets because it is very warm outside today. We cannot imagine a morning without a tasty breakfast.*

Beyond physical objects, **без** is heavily used with abstract concepts to form common conversational fillers. For example, you will often use words like **сумнів** (doubt), **допомога** (help, assistance), or **відпочинок** (rest, relaxation). You might also describe an object without a clear **призначення** (purpose, destination).

Цей старий інструмент лежить тут без призначення. Він вирішив це складне завдання без моєї допомоги. Цей студент, без сумніву, найкращий у нашій групі. Ми працювали весь день без відпочинку. Вона завжди робить свою роботу без проблем і без помилок.

> *This old tool lies here without a purpose. He solved this complex task without my help. This student is, without a doubt, the best in our group. We worked all day without rest. She always does her work without problems and without mistakes.*

:::note
**Quick tip** — The phrase «без сумніву» is a fantastic conversational filler to agree enthusiastically with someone.
:::

To use **без** accurately, apply the correct Genitive endings based on the noun's stem. Masculine hard stems take **-а** or **-у**, while soft stems take **-я** or **-ю**. Feminine hard stems take **-и**, and soft stems take **-і**. Neuter nouns take **-а** or **-я**.

Сьогодні ми обідаємо без хліба, а учень прийшов на урок без олівця. Я не можу жити без чистої води. Цей грибний суп зовсім без солі. У кімнаті темно, бо вона без вікна. Ми не хочемо відпочивати без моря.

> *Today we are having lunch without bread, and the student came to the lesson without a pencil. I cannot live without clean water. This mushroom soup is completely without salt. It is dark in the room because it is without a window. We do not want to rest without the sea.*

Specific verbs naturally pair with **без**. The verb «могти» in the negative expresses strong dependency. You will also use **без** with verbs of motion. Personal pronouns also change forms: «він» becomes «нього», «ми» becomes «нас».

Я зовсім не можу жити без ранкової кави. Вона прийшла на зустріч без парасольки, хоча йшов сильний дощ. Ми поїхали в подорож без нього, бо він був дуже зайнятий на роботі. Вони почали виступ без нас.

> *I absolutely cannot live without morning coffee. She came to the meeting without an umbrella, even though it was raining heavily. We went on the trip without him because he was very busy at work. They started the performance without us.*

> — **Олена:** Ти справді п'єш каву без молока?
> — **Марко:** Так, я завжди п'ю каву без молока і без цукру. Це дуже смачно.
> — **Олена:** А як щодо десерту? Ти теж їси без цукру?
> — **Марко:** Ні, звичайно. Я не можу без солодкого.
> — **Олена:** Я теж! Без смачного торта життя не цікаве. А ти любиш чай без лимона?
> — **Марко:** Я взагалі не п'ю чай. Тільки каву.

One nuance to master is the Genitive endings for masculine nouns. Use **-а/-я** for concrete, countable objects, like a **будинок** (building, house). For abstract concepts, uncountable substances, and natural phenomena, use **-у/-ю**. You will often see this rule applied in places like a **бібліотека** (library) or a **лікарня** (hospital).

:::tip
**Did you know?** — The choice between **-а** and **-у** is one of the most unique features of the Ukrainian Genitive case. It distinguishes Ukrainian from other Slavic languages and adds precision to your speech.
:::

Він ремонтує старий стіл без молотка і без ножа. Я не можу працювати без комп'ютера. У бібліотеці всі читають спокійно і без шуму. Цей новий будинок стоїть зовсім без світла. У лікарні пацієнти сплять без проблем.

> *He is repairing the old table without a hammer and without a knife. I cannot work without a computer. In the library, everyone reads calmly and without noise. This new building stands completely without light. In the hospital, patients sleep without problems.*

Сьогодні дуже теплий весняний день, тому небо чисте і зовсім без хмар. Ми вирішили піти в парк без курток і без теплих шапок. Мій друг прийшов без собаки, бо його собака зараз спить вдома. Ми гуляємо без поспіху і просто насолоджуємося чудовою погодою. Я також люблю гуляти містом без чіткої мети, без карти і без навігатора. Можна зайти в нове кафе, випити смачний чай без цукру і відпочити. Головне — це гарний настрій і вихідний день без стресу.

У нашому місті є новий ресторан. Там готують дуже смачні страви. Я часто замовляю салат без м'яса і суп без сметани. Мій друг завжди бере картоплю без соусів. Вони також роблять чудові десерти без цукру. Ми можемо сидіти там весь вечір і розмовляти без пауз. Це чудове місце для відпочинку.

> — **Степан:** Привіт! Ти сьогодні без машини?
> — **Ганна:** Так, моя машина зараз у ремонті. Я їду на автобусі.
> — **Степан:** Тоді ми можемо поїхати разом. Мій офіс біля твого.
> — **Ганна:** Дуже дякую! Без тебе я б точно запізнилася на зустріч.
> — **Степан:** Без проблем! Сідай, поїхали.

<!-- INJECT_ACTIVITY: true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct -->

## Де це? Біля, навпроти, коло + родовий (Where Is It? Біля, навпроти, коло + Genitive)

Now that we have covered how to express purpose and absence, we can transition from abstract concepts to physical space. When you want to describe where something is located, the most common preposition for proximity is **біля** (near, next to). It is your default, go-to word whenever you need to say that one object is physically close to another. Even though it clearly answers the question "Where?", it strictly requires the noun to be in the Genitive case. This is a very common point of confusion for beginners, who often try to use the Locative case here.

Моя нова школа знаходиться біля великого парку. Щоранку я зустрічаю друзів біля входу. Ми любимо гуляти біля річки після уроків. Наш старий будинок стоїть біля лісу, тому там завжди свіже повітря. Мій брат залишив свій велосипед біля магазину. Ми часто п'ємо каву біля вікна і дивимося на вулицю. Це чудове місце для життя та відпочинку.

> *My new school is located near a large park. Every morning I meet friends near the entrance. We like to walk near the river after classes. Our old house stands near the forest, so there is always fresh air there. My brother left his bicycle near the store. We often drink coffee by the window and look at the street. This is a wonderful place for living and rest.*

Another very useful spatial preposition is **навпроти** (opposite, across from). You use it specifically when describing two objects that are facing one another, like buildings on opposite sides of a street or people sitting across a table. While **біля** just means something is nearby, **навпроти** gives a much more precise geometric relationship. Like the others we have studied in this module, it always takes the Genitive case.

Нова бібліотека працює навпроти мого університету. Я часто читаю там книги для навчання. Велика церква стоїть навпроти центрального вокзалу. Туристи люблять фотографувати будівлі навпроти великої площі. Мій улюблений ресторан знаходиться навпроти старого театру. Ми сиділи в кафе навпроти один одного і довго розмовляли.

> *The new library works opposite my university. I often read books there for studying. A large church stands opposite the central train station. Tourists like to photograph buildings opposite the large square. My favorite restaurant is located opposite the old theater. We sat in the cafe opposite one another and talked for a long time.*

You will also encounter the preposition **коло** (near, by). It is completely synonymous with **біля** and also requires the Genitive case for the following noun. While **біля** is the standard, neutral choice in everyday spoken Ukrainian, **коло** has a slightly more literary, warm, or folksy flavor. You will often hear it in traditional folk songs, classical poetry, and historical literature. It evokes a cozy feeling of being close to home or nature.

Маленька дівчинка грається коло білої хати. Старе високе дерево росте коло дороги. Ми сиділи коло вогнища теплим літнім вечором і співали народні пісні. Діти бігали коло швидкої річки цілий день. Моя бабуся завжди садила гарні квіти коло вікна. Це було ідеальне місце для нашого табору.

> *A little girl is playing by the white house. An old tall tree grows by the road. We sat by the fire on a warm summer evening and sang folk songs. The children ran by the fast river all day. My grandmother always planted beautiful flowers by the window. It was an ideal place for our camp.*

Combining these spatial prepositions allows you to give precise directions and clearly describe city locations. This is an absolutely essential skill for everyday life and navigation in any Ukrainian city. When someone asks for help finding a specific place, or when you are trying to explain where you live, you can confidently guide them using these exact patterns.

Без сумніву, це найкращий і найзручніший район міста. Трамвайна зупинка знаходиться просто біля станції метро. Кінцевий пункт призначення цього автобуса — старий залізничний вокзал. Якщо вам потрібна термінова допомога, відділення поліції розташоване біля центрального банку. Ця сучасна міська лікарня стоїть коло нового парку. Ми завжди зустрічаємося біля головного входу.

> *Without a doubt, this is the best and most convenient district of the city. The tram stop is located right near the subway station. The final destination of this bus is the old train station. If you need urgent help, the police department is situated near the central bank. This modern city hospital stands by the new park. We always meet near the main entrance.*

> — **Марта:** Вибачте, ви не знаєте, де тут найближча аптека? *(Excuse me, do you know where the nearest pharmacy is here?)*
> — **Ігор:** Звичайно. Вона знаходиться біля станції метро. *(Of course. It is located near the subway station.)*
> — **Марта:** А як туди дійти пішки? *(And how do I get there on foot?)*
> — **Ігор:** Ідіть прямо до великої площі. Аптека буде навпроти міської лікарні. *(Go straight to the large square. The pharmacy will be opposite the city hospital.)*
> — **Марта:** Це далеко звідси? *(Is it far from here?)*
> — **Ігор:** Ні, це дуже близько. Ви побачите її коло великого супермаркету. *(No, it is very close. You will see it by the large supermarket.)*
> — **Марта:** Дуже дякую за допомогу! Без вас я б довго шукала. *(Thank you very much for the help! Without you I would have searched for a long time.)*
> — **Ігор:** Без проблем! Гарного дня. *(No problem! Have a good day.)*

When giving directions in a busy city, pay close attention to nouns from the mixed group and feminine nouns ending in **-ія**. These specific endings are common traps for learners because they sound slightly different, but they follow perfectly predictable Genitive patterns. Soft feminine nouns ending in **-ія** always change to **-ії**, while mixed feminine nouns change to **-і**. Mastering these will make your spoken Ukrainian sound incredibly natural and fluent.

Туристи часто зустрічаються біля станції метро перед екскурсією. Маленька кав'ярня знаходиться навпроти великої площі в центрі міста. Моя старша сестра працює біля дитячої лікарні. Ми завжди купуємо свіжий хліб біля місцевої пекарні. Вони живуть навпроти нової студії танців. Студенти люблять читати біля лабораторії.

> *Tourists often meet near the subway station before an excursion. A small coffee shop is located opposite the large square in the city center. My older sister works near the children's hospital. We always buy fresh bread near the local bakery. They live opposite the new dance studio. Students like to read near the laboratory.*

:::info
**Grammar box** — The prepositions **біля**, **навпроти**, and **коло** answer the question "Where?" and describe a location. Because of this, it is very tempting to use the Locative case. However, because they are prepositions of proximity (showing a relationship to another object), they strictly govern the Genitive case. Always ask yourself "Near what?" to trigger the correct ending.
:::

:::tip
**Decolonization note** — When speaking Ukrainian, you must completely avoid the word **возле**. This is a Russianism and a very common error in Surzhyk. The correct, natural Ukrainian prepositions for proximity are exclusively **біля** and **коло**.
:::

Many learners who have had previous exposure to Russian, or who hear a mixed language on the streets, might accidentally use the preposition **возле**. It is crucial to consciously filter this out of your vocabulary if you want to speak pure, beautiful Ukrainian. Using **біля** or **коло** immediately signals that you are speaking correctly.

Ми ніколи не кажемо це слово. Українці завжди чекають своїх друзів біля театру або коло кінотеатру. Це просте правило є дуже важливим для чистої та правильної мови. Я залишив свою нову машину біля великого будинку. Справжня українська мова завжди звучить красиво і без помилок.

> *We never say this word. Ukrainians always wait for their friends near the theater or by the cinema. This simple rule is very important for clean and correct language. I left my new car near the large building. Real Ukrainian language always sounds beautiful and without mistakes.*

To wrap up this grammar topic, you now have a highly versatile and powerful "Genitive Preposition Toolkit" at your disposal. By mastering **для** for purpose, **без** for absence, and the spatial group of **біля**, **навпроти**, and **коло** for location, you can confidently describe a wide range of everyday situations. These small words unlock a massive amount of expressive power in A2 Ukrainian and serve as the foundation for navigating the physical world around you.

<!-- INJECT_ACTIVITY: fill-in-complete-location-descriptions-with-correct-genitive-form -->
<!-- INJECT_ACTIVITY: match-up-match-ukrainian-prepositional-phrases-to-their-english-equivalents -->
<!-- INJECT_ACTIVITY: true-false-judge-whether-preposition-noun-form-combinations-are-grammatically-correct -->
<!-- INJECT_ACTIVITY: quiz-choose-or-to-complete-everyday-sentences -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-purpose
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

**Level: A2 (Module 10/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень


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
