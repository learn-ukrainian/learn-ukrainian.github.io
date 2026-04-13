<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-source.yaml` file for module **9: Звідки ти? З чого це зроблено?** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-euphony-z-iz-zi -->`
- `<!-- INJECT_ACTIVITY: fill-in-vid-z -->`
- `<!-- INJECT_ACTIVITY: match-up-preposition-phrases -->`
- `<!-- INJECT_ACTIVITY: group-sort-prepositions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct variant з/із/зі based on the following word
  items: 8
  type: quiz
- focus: Complete sentences with від or з + correct Genitive noun form
  items: 8
  type: fill-in
- focus: Match preposition phrases to their English meanings (origin, material, time)
  items: 8
  type: match-up
- focus: Sort phrases into з (place/material) vs. від (person/protection) vs. після
    (time)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дитинство (childhood)
- шовк (silk)
- парасолька (umbrella)
- сусід (neighbor)
required:
- прийменник (preposition)
- джерело (source)
- походження (origin)
- матеріал (material)
- далеко (far)
- недалеко (not far, nearby)
- подарунок (gift)
- сніданок (breakfast)
- вечеря (dinner, supper)
- канікули (vacation, holidays)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Звідки? З/із/зі + родовий (Where From? З/із/зі + Genitive) (~770 words)

Imagine you are at an international potluck dinner. Everyone has brought something delicious from their home country or a recent trip. As people gather around the table, they naturally start asking where everything came from. It is a perfect opportunity to practice talking about geographical origins and the sources of various dishes.

> **Марта:** Привіт усім! Я принесла закуски. Це сир з Франції, дуже смачний. *(Hello everyone! I brought snacks. This is cheese from France, very tasty.)*
> **Джон:** О, чудово! А я маю свіжі оливки з Греції. *(Oh, great! And I have fresh olives from Greece.)*
> **Анна:** Який чудовий стіл! Я принесла десерт. Це шоколад від бабусі з Бельгії. *(What a wonderful table! I brought dessert. This is chocolate from my grandmother from Belgium.)*
> **Карлос:** А це червоне вино ми привезли після подорожі Італією. *(And this red wine we brought after a trip through Italy.)*
> **Марта:** Дякую! У нас вийшла справжня міжнародна вечеря. *(Thank you! We have a real international dinner.)*

When you want to talk about **походження** (origin) or the **джерело** (source) of something, you need the **прийменник** (preposition) "з" followed by the Genitive case. This combination directly answers the question «Звідки?» (Where from?). The core meaning of this structure is moving away from a place, indicating where a person or an object originated. This is how you state your home country, your city, or where a specific product was made. The Genitive case is strictly required here; you cannot simply use the Nominative dictionary form. If you want to say "from Kyiv", you must change "Київ" to "Києва".

Мої старі друзі приїхали з України, але зараз вони живуть тут. Наш новий колега по роботі родом з Києва. Ця неймовірно смачна кава приїхала до нас аж зі Швеції. Мій найулюбленіший сучасний письменник родом зі Львова.

> *My old friends came from Ukraine, but now they live here. Our new colleague at work is originally from Kyiv. This incredibly delicious coffee arrived to us all the way from Sweden. My most favorite contemporary writer is originally from Lviv.*

:::info
**Grammar box**
Remember that the Genitive case endings for masculine cities usually take **-а** (з Києва, з Лондона), while feminine countries ending in **-а** change to **-и** (з України, з Америки).
:::

Ukrainian is a highly melodic language, and it has a built-in system to prevent awkward clusters of consonants. This principle is called euphony, or «милозвучність». Because of this rule, the preposition meaning "from" has three different shapes: з, із, and зі. You choose the correct shape based entirely on the sounds that immediately follow it. The most common and basic form is a single «з». You use «з» when the next word starts with a vowel, or when it starts with a single consonant that is easy to pronounce after "z". This rule ensures that your speech does not get stuck and flows rapidly.

Студенти вийшли з великої аудиторії відразу після лекції. Моя подруга повернулася з Одеси тільки вчора ввечері. Ми дуже часто беремо товсті книги з університету. Цей жовтий автобус швидко їде з центру міста.

> *The students came out of the large lecture hall immediately after the lecture. My friend returned from Odesa only yesterday evening. We very often take thick books from the university. This yellow bus drives fast from the city center.*

Sometimes, placing a single "з" before another consonant creates a harsh hissing or buzzing sound that stops the flow of speech. To fix this problem, Ukrainian adds a vowel to make the form «із». You must use «із» before words that start with a single sibilant consonant, which includes the sounds [з], [с], [ц], [ж], [ч], and [ш]. You also use «із» when the preposition is squeezed right between two other consonants, acting as a vocalic bridge to keep the rhythm smooth and natural. 

Ця красива і дорога каблучка зроблена із чистого золота. Вони приїхали із далекого села до міста на свята. Вчора я отримав дуже довгий лист із сонячної Бразилії. Ми швидко вийшли із шумного приміщення на тиху вулицю.

> *This beautiful and expensive ring is made of pure gold. They arrived from the distant village to the city for the holidays. Yesterday I received a very long letter from sunny Brazil. We quickly walked out of the noisy room onto the quiet street.*

The third variant, «зі», is specifically designed to handle heavy consonant clusters. When a word begins with two or more consonants grouped together—especially if that cluster starts with letters like з, с, or ш—you cannot simply attach another "з" or "із" in front of it. It would be physically difficult to say without pausing. Instead, you use «зі» to create a comfortable gap before the heavy cluster. Mastering these three variants will instantly make your spoken Ukrainian sound much more authentic and fluid.

Сьогодні мій молодший брат повернувся зі школи дуже рано. Швидкий поїзд зі Львова завжди прибуває на першу платформу. Чорний кіт несподівано стрибнув зі стола на м'який диван. Вона обережно взяла свої нові речі зі шафи.

> *Today my younger brother returned from school very early. The fast train from Lviv always arrives at the first platform. The black cat unexpectedly jumped from the table onto the soft sofa. She carefully took her new things from the wardrobe.*

<!-- INJECT_ACTIVITY: quiz-euphony-z-iz-zi -->

Beyond geographic origin, the preposition «з» combined with the Genitive case is also used to describe the **матеріал** (material) something is made of, or its physical composition. If you want to explain what ingredients went into a dish or what fabric a piece of clothing is sewn from, you use exactly the same grammar structure as you do for cities and countries. It is as if the object "originates" from that specific material. Notice how the noun denoting the material changes its ending to the Genitive form, just like the names of cities do. 

Я завжди ставлю красиві квіти у велику вазу зі скла. Цей свіжий і солодкий сік повністю зроблений з червоних яблук. На велике свято вона одягнула красиву довгу сукню з шовку. Ми вчора купили новий зручний стіл з темного дерева.

> *I always put beautiful flowers in a large vase made of glass. This fresh and sweet juice is completely made of red apples. For the big holiday, she wore a beautiful long dress made of silk. We bought a new comfortable table made of dark wood yesterday.*

Finally, this versatile preposition is crucial for expressing time. When you pair «з» with a time expression in the Genitive case, it translates to the English word "since". It marks the starting point of an action or state that began in the past and continues onward into the present. This is incredibly useful for talking about your daily routine, your habits, or how long you have been doing something. Just remember to apply the correct Genitive ending to the time word, such as changing "ранок" (morning) to "ранку".

Я активно працюю над цим складним проєктом з самого ранку. Ми серйозно вирішили почати нове життя з наступного понеділка. Мій найкращий друг глибоко цікавиться історією ще з дитинства. Вона терпляче чекає на твій важливий дзвінок з минулого тижня.

> *I have been actively working on this difficult project since early morning. We seriously decided to start a new life since next Monday. My best friend has been deeply interested in history since childhood. She has been patiently waiting for your important call since last week.*

:::tip
**Quick tip**
When talking about daily meals, you can also use this structure to describe leftovers. For example, «піца з вечері» means pizza left over from **вечеря** (dinner, supper), and «хліб зі сніданку» is bread left over from **сніданок** (breakfast).
:::

## Від кого? Від + родовий (From Whom? Від + Genitive) (~620 words)

In English, the word "from" is incredibly versatile. You can get a letter from a friend, or you can travel from a city. In Ukrainian, these two situations require completely different prepositions. When you are receiving something from a person, you must use the **прийменник** (preposition) «від» followed by the Genitive case. This word specifically points to a human sender or a living entity as the starting point of an action or an object. Whether you are getting a physical **подарунок** (gift), a digital message, or just hearing some fresh news from a **сусід** (neighbor), «від» is your go-to word.

Сьогодні вранці я отримав довгий електронний лист від мами. Це дуже приємний і несподіваний подарунок від найкращого друга. Ми щодня з нетерпінням чекаємо на свіжі новини від старого сусіда. Цей красивий годинник дістався мені від улюбленого дідуся.

> *This morning I received a long email from mom. This is a very pleasant and unexpected gift from a best friend. We look forward to fresh news from the old neighbor every day. I got this beautiful watch from my beloved grandfather.*

A very common mistake for English speakers is to use «з» for absolutely everything that translates to "from". It is crucial to separate the concepts of geographic **походження** (origin) and a human **джерело** (source). You use «з» when you are talking about leaving a physical place, a country, or a city. You use «від» when a specific person is giving you something or sending information. If you say «подарунок з друга», it sounds absurd—as if the friend is a location you traveled away from, or perhaps the **матеріал** (material) the gift is made of.

Мій новий колега приїхав з великого Києва, і я маю важливі документи від Олени. Вона вчора повернулася з Німеччини і привезла чудові сувеніри від брата. Ми щойно отримали цікавий лист з університету від нашого професора.

> *My new colleague arrived from big Kyiv, and I have important documents from Olena. She returned from Germany yesterday and brought wonderful souvenirs from her brother. We just received an interesting letter from the university from our professor.*

:::info
**Grammar box**
Always ask yourself when translating "from": Is the starting point a place on a map (`з`) or a breathing person (`від`)?
:::

Another major function of «від» is expressing physical distance between two points in space. When you want to explain how far or close something is, you pair this preposition with spatial adverbs like **далеко** (far) or **недалеко** (not far, nearby). The point you are measuring the distance from will always take the Genitive case. This structure is absolutely essential for giving clear directions or describing where you live relative to important landmarks in a city. 

Наш новий просторий офіс знаходиться дуже далеко від центру міста. Я спеціально орендував світлу квартиру недалеко від залізничного вокзалу. Моя стара школа стоїть зовсім недалеко від великого зеленого парку. Цей туристичний готель розташований дуже далеко від галасливої дороги.

> *Our new spacious office is located very far from the city center. I specifically rented a bright apartment not far from the railway station. My old school stands quite not far from a large green park. This tourist hotel is located very far from the noisy road.*

Beyond physical movement and measuring distance, «від» has a very specific use: protection. When you talk about things that shield, cure, or defend you against something unpleasant, you use this exact preposition. It acts as a linguistic barrier between you and the problem. The thing you are being protected against always goes into the Genitive case. Instead of saying "medicine for", Ukrainians literally say "medicine from". This applies to taking pills or simply carrying a **парасолька** (umbrella) in bad weather.

В аптеці я купив ефективні ліки від сильного головного болю. У мене завжди є велика чорна парасолька від раптового дощу. Цей дорогий зимовий крем чудово захищає шкіру від сильного морозу. Влітку на пляжі ми носимо темні окуляри від яскравого сонця.

> *At the pharmacy, I bought effective medicine for a severe headache. I always have a large black umbrella for sudden rain. This expensive winter cream perfectly protects the skin from severe frost. In summer on the beach, we wear dark glasses against the bright sun.*

As you practice these communicative structures, quickly review how the Genitive case affects the nouns that follow «від». For feminine nouns, the ending typically changes to «-и» for hard stems and «-і» for soft ones, giving us forms like «від мами». For masculine nouns, you must carefully choose between «-а» and «-у». Nouns representing concrete people take «-а» to become «від друга» or «від сусіда». Abstract concepts or natural phenomena, such as pain or rain, take «-у», giving us «від болю» and «від дощу».

Сьогодні ми уважно чекаємо на важливий дзвінок від генерального директора. Я хочу швидко сховатися в теплому будинку від холодного вітру. Вона несподівано отримала це дивне повідомлення від своєї старшої сестри. Ми довго стояли на вулиці далеко від ресторану.

> *Today we are attentively waiting for an important call from the general director. I want to quickly hide in the warm house from the cold wind. She unexpectedly received this strange message from her older sister. We stood on the street for a long time far from the restaurant.*

<!-- INJECT_ACTIVITY: fill-in-vid-z -->

## Що було потім? Після + родовий (What Happened Next? Після + Genitive) (~770 words)

Ukrainian uses the **прийменник** (preposition) **після** (after) to sequence events. It strictly requires the Genitive case. You will use it often to describe what you do after long **канікули** (vacation, holidays).

Сьогодні ввечері, після довгого уроку, я хочу просто відпочити вдома. Зазвичай ми п’ємо міцну каву після смачного обіду в ресторані. Мій старший брат завжди читає останні новини після важкої роботи. Вони нарешті повернулися до рідного міста після зимових канікул. Ми плануємо нову подорож після цього складного тижня. Вона завжди слухає приємну музику після довгої дороги.

> *Tonight, after a long lesson, I want to rest at home. Usually, we drink strong coffee after a tasty lunch. My older brother always reads the latest news after hard work. They finally returned to their hometown after the winter holidays. We are planning a new trip after this difficult week. She always listens to pleasant music after a long road.*

Many events and abstract concepts take the **-у** or **-ю** ending. Hard masculine stems take **-у**, while soft stems take **-ю**. Some specific time words act as exceptions.

**після екзамену** — *after the exam*

**після дня** — *after the day*

Студенти часто гучно святкують після дуже складного екзамену. Після сильного дощу повітря на вулиці стає дуже свіжим. Я дуже люблю повільно гуляти в міському парку після довгого робочого дня. Після ранкового сніданку ми одразу йдемо в наш новий офіс. Мій друг завжди п'є гарячий чай після сильного холоду. Вони хочуть спати після важкого турніру.

> *Students often celebrate after a difficult exam. After heavy rain, the air outside becomes very fresh. I love walking in the city park after a long working day. After morning breakfast, we immediately go to our new office. My friend always drinks hot tea after severe cold. They want to sleep after a hard tournament.*

> — **Марко:** Куди ти йдеш після лекції? *(Where are you going after the lecture?)*
> — **Анна:** Після лекції я йду в новий басейн. *(After the lecture I am going to the new pool.)*
> — **Марко:** О, це чудово! А що ти робиш після басейну? *(Oh, that is great! And what do you do after the pool?)*
> — **Анна:** Після басейну я маю обід з подругою. *(After the pool I have lunch with a friend.)*
> — **Марко:** Бажаю смачного обіду! *(Wishing you a tasty lunch!)*
> — **Анна:** Дякую! Побачимося після вихідних! *(Thank you! See you after the weekend!)*

Feminine nouns change **-а** to **-и**, or **-я** to **-і**. Hard neuter nouns smoothly change **-о** to **-а**. 

**після роботи** — *after work*

**після свята** — *after the holiday*

Ми домовилися зустрітися в затишному кафе після цікавої лекції. Маленькі діти були дуже втомлені після великого родинного свята. Моя подруга завжди телефонує мені після роботи, щоб поговорити. Після довгої та виснажливої подорожі вони міцно спали весь наступний день. Він купив свіжі продукти після ранкової пробіжки. Ми підемо в кіно після цієї важливої презентації.

> *We agreed to meet in a cozy cafe after an interesting lecture. The small children were tired after a big family holiday. My friend always calls me after work to talk. After an exhausting journey, they slept soundly the entire next day. He bought fresh groceries after his morning run. We will go to the cinema after this presentation.*

This preposition explains the flow of your routine, from your morning **сніданок** (breakfast) to buying a **подарунок** (gift), until your evening **вечеря** (dinner, supper).

Щоранку після сніданку я швидко йду на автобусну зупинку. Після роботи я зазвичай купую подарунок для друга або просто готую смачну вечерю для родини. Після вечері я дивлюся новий документальний фільм або читаю книгу. Це мій звичайний розклад на кожен день тижня. Моя сестра робить домашнє завдання після школи. Ми завжди відпочиваємо після важких тренувань.

> *Every morning after breakfast, I quickly go to the bus stop. After work, I usually buy a gift for a friend or prepare a tasty dinner for the family. After dinner, I watch a documentary film or read a book. This is my usual schedule for every day of the week. My sister does her homework after school. We always rest after hard workouts.*

> — **Віктор:** Ти маєш плани після екзамену? *(Do you have plans after the exam?)*
> — **Максим:** Так, після екзамену я їду додому. *(Yes, after the exam I am going home.)*
> — **Віктор:** А що ти будеш робити після дороги? *(And what will you do after the road?)*
> — **Максим:** Після дороги я буду спати два дні! *(After the road I will sleep for two days!)*
> — **Віктор:** Розумію тебе. Відпочинок після стресу дуже потрібен. *(I understand you. Rest after stress is very necessary.)*
> — **Максим:** Точно. А ти що робиш після університету? *(Exactly. And what are you doing after university?)*
> — **Віктор:** Я йду на вечірку! *(I am going to a party!)*

Contrast this preposition with **до** (before) to practice the endings. Both words require the Genitive case.

**до обіду** — *before lunch*

**після обіду** — *after lunch*

### Читаємо українською

Я завжди п'ю склянку чистої води до сніданку, а гарячу каву — після сніданку. Студенти уважно читають новий текст до уроку і роблять письмові вправи після уроку. Ми маємо коротку зустріч до обіду, але ми можемо детально поговорити після обіду. Дуже важливо ретельно мити руки до вечері. Він ніколи не їсть солодке після вечері. Цей контраст допомагає нам планувати наш довгий день. Я роблю складні завдання до перерви, а легкі завдання — після перерви. Це мій улюблений секрет успіху на кожен день.

:::info
**Grammar box**
Запам'ятайте ці корисні фрази (Remember these useful phrases):
* Після довгого дня — *after a long day*
* Після важкої роботи — *after hard work*
* Після смачного обіду — *after a tasty lunch*
* Після зимових канікул — *after the winter holidays*
:::

<!-- INJECT_ACTIVITY: match-up-preposition-phrases -->
<!-- INJECT_ACTIVITY: group-sort-prepositions -->

> — **Марія:** Привіт! Ти вільний після роботи?
> — **Олег:** Привіт! Так, після роботи я маю багато вільного часу.
> — **Марія:** Чудово! Ми йдемо в кіно після вечері. Ти з нами?
> — **Олег:** Звичайно! Я дуже люблю відпочивати після довгого дня.
> — **Марія:** Тоді зустрінемося після фільму в кафе!
> — **Олег:** Домовилися!

Let us review. The prepositions **з/із/зі** express **походження** (origin), time, and **матеріал** (material).

The preposition **від** indicates the **джерело** (source) person, protection, or if a place is **далеко** (far) or **недалеко** (not far, nearby). We use **після** to sequence events.

Ця важлива граматика допомагає нам набагато краще розуміти українську мову. Тепер ми добре знаємо, як детально розповісти про своє рідне місто, улюблені речі та плани на день. Продовжуйте активно практикувати ці нові слова та граматичні правила кожного дня. Ваша розмовна мова стає все більш впевненою та природною. Успіхів вам у навчанні після цього модуля!

> *This grammar helps us understand the Ukrainian language better. Now we know how to talk about our hometown, favorite things, and plans for the day. Continue practicing these new words and grammar rules every day. Your spoken language is becoming increasingly confident and natural. Good luck in your studies after this module!*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-source
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

**Level: A2 (Module 9/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
