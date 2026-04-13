<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-adjectives-pronouns.yaml` file for module **29: З моїм найкращим другом** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-add-correct-instrumental-adjective-endings-to-complete-noun-phrases -->`
- `<!-- INJECT_ACTIVITY: match-up-nom-ins -->`
- `<!-- INJECT_ACTIVITY: quiz-pronoun-gender -->`
- `<!-- INJECT_ACTIVITY: fill-in-full-chains -->`
- `<!-- INJECT_ACTIVITY: error-correction-find-and-fix-agreement-errors-in-instrumental-phrases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Add correct Instrumental adjective endings to complete noun phrases
  items: 8
  type: fill-in
- focus: Match Nominative phrases (мій новий друг) to Instrumental forms (моїм новим
    другом)
  items: 8
  type: match-up
- focus: Choose the correct pronoun form (моїм vs. моєю) based on noun gender
  items: 8
  type: quiz
- focus: Build full sentences using preposition + pronoun + adjective + noun in Instrumental
  items: 8
  type: fill-in
- focus: Find and fix agreement errors in Instrumental phrases (e.g., *з моїм новою
    другом → з моїм новим другом, *моєю великим містом → моїм великим містом)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- домашній (home (adj.), domestic)
- синій (blue)
- сусідка (neighbor (female))
- тим часом (meanwhile)
- цим вечором (this evening)
required:
- мій (my)
- твій (your (informal))
- наш (our)
- ваш (your (formal/plural))
- цей (this)
- той (that)
- новий (new)
- старий (old)
- великий (big, large)
- гарний (nice, beautiful)
- найкращий (the best)
- сусід (neighbor (male))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Прикметники в орудному відмінку (Adjectives in the Instrumental Case)

When we talk about who we are with or what tools we use, the noun gives us the basic information. For example, «з другом» tells us you are with a friend. But usually, we want to add more detail. We want to say you are with your best friend, or writing with a new pen. To do this, we need adjectives in the Instrumental case. In Ukrainian, this process is called agreement («узгодження»). An adjective must always mirror its noun. If the noun is in the Instrumental case, the adjective must also take the Instrumental case. It must also match the noun's gender and number. This creates a strong, connected phrase where every word works together.

Let's start with the most common adjectives, which belong to the Hard Group. These are adjectives whose dictionary form ends in a hard consonant sound before the ending, like «новий» (new) or «великий» (big). For masculine and neuter nouns, the Instrumental ending for these adjectives is **-им**.

Я вчора довго розмовляв з новим другом. Ми сиділи в парку під великим деревом. Мій брат працює з тим відомим лікарем.

> *Yesterday I talked for a long time with a new friend. We sat in the park under a big tree. My brother works with that famous doctor.*

Notice how Ukrainian marks every word in the phrase. In English, you say "with a new friend," changing only the preposition. In Ukrainian, it is «з нов**им** друг**ом**». Both the adjective and the noun show the Instrumental case.

For feminine nouns, the Hard Group adjective ending is very distinct. It takes the ending **-ою**. This creates a beautiful, echoing sound when paired with a feminine noun, which often also ends in **-ою**.

Вона завжди гуляє з гарною собакою. Я люблю пити каву з холодною водою. Кіт спить за великою книжкою.

> *She always walks with a beautiful dog. I like to drink coffee with cold water. The cat is sleeping behind a big book.*

Forms like «гарною», «новою», and «великою» are unmistakable. When you hear that «ою» sound repeated across the phrase, like in «з нов**ою** подруг**ою**», you instantly know it is the Instrumental case. It is one of the most recognizable patterns in the language.

:::info
**Grammar box**
Remember that the preposition «з» means "with" when it is followed by the Instrumental case. When building these phrases, make sure the adjective and the noun both use their specific Instrumental endings.
:::

Now let's look at the Soft Group. These are adjectives like «синій» (blue) or «літній» (summer). Because their stem ends in a soft consonant, their Instrumental endings shift slightly. For masculine and neuter nouns, the ending becomes **-ім**.

Я малюю небо синім олівцем. Ми насолоджуємося теплим літнім вечором.

> *I am drawing the sky with a blue pencil. We are enjoying a warm summer evening.*

For feminine nouns, the Soft Group adjective takes the ending **-ьою**. This preserves the softness of the consonant before adding the familiar «ою» sound. So, «синя» becomes «синь**ою**», and «домашня» becomes «домашнь**ою**». Compare this to the hard ending: «з новою машиною» versus «із синьою машиною».

Ukrainian students formally learn these exact adjective declension tables in the fourth grade. The core pattern they memorize is straightforward. For masculine and neuter nouns, you choose between **-им** (hard) and **-ім** (soft). For feminine nouns, you choose between **-ою** (hard) and **-ьою** (soft).

Сьогодні я йду на каву з добрим сусідом. А завтра я зустрічаюся з давнім знайомим. Ми будемо говорити українською мовою.

> *Today I am going for coffee with a kind neighbor. And tomorrow I am meeting with an old acquaintance. We will speak the Ukrainian language.*

Notice the contrast between «з добрим сусідом» and «з давнім знайомим». The hard and soft groups simply offer two parallel tracks for making your descriptions richer and more precise.

<!-- INJECT_ACTIVITY: fill-in-add-correct-instrumental-adjective-endings-to-complete-noun-phrases -->

## Присвійні та вказівні займенники (Possessive and Demonstrative Pronouns)

Now that you know how adjectives work in the Instrumental case, let us look at possessive pronouns. The three most common ones are **мій** (my), **твій** (your), and **свій** (one's own). They behave very much like adjectives, but they have a unique «ї» or «є» sound in their stems when they change. For masculine and neuter nouns, they take the ending **-їм**: «моїм», «твоїм», «своїм». For feminine nouns, they take the ending **-єю**: «моєю», «твоєю», «своєю».

Я часто гуляю з моїм найкращим другом. Минулого тижня я познайомився з твоєю старшою сестрою. Я дуже пишаюся своєю сестрою. Мій брат любить подорожувати зі своєю сім'єю.

> *I often walk with my best friend. Last week I met your older sister. I am very proud of my sister. My brother likes to travel with his family.*

Notice how the pronoun «свій» is used here. When the subject of the sentence owns the object, Ukrainian naturally prefers «свій» over «його» or «її». 

The possessive pronouns for "our" and "your" (plural/formal) are much simpler. The pronouns **наш** and **ваш** act exactly like standard hard group adjectives. For masculine and neuter nouns, you add **-им**: «нашим», «вашим». For feminine nouns, you add **-ою**: «нашою», «вашою».

Ми з радістю працюємо над нашим спільним проєктом. Я дуже задоволена вашою новою ідеєю. Це допоможе нашій команді працювати краще.

> *We gladly work on our joint project. I am very satisfied with your new idea. This will help our team work better.*

The word for "their" is **їхній**. It acts like a soft group adjective, so it takes the endings **-ім** and **-ьою**.

Я вчора розмовляв з їхнім сусідом. Вони часто гуляють із їхньою маленькою собакою.

> *Yesterday I talked with their neighbor. They often walk with their little dog.*

:::note
**Decolonization Note**
Always use the fully declinable pronoun **їхній** (their). You might hear some people use the invariable word «їх» (as in «з їх другом»), but this is a direct Russian influence. In standard Ukrainian, «їхній» changes its endings to match the noun perfectly, just like any other adjective: «з їхнім другом», «за їхньою школою».
:::

Not all pronouns change their form. The pronouns **його** (his/its) and **її** (her) are completely invariable when they show possession. This means they look exactly the same in every single case, including the Instrumental. You do not need to add any endings to them.

Вона вчора ходила в кіно з його другом. Ми сиділи в кафе з її сестрою. Я хочу поговорити з його новим учителем.

> *She went to the movies yesterday with his friend. We sat in the cafe with her sister. I want to talk with his new teacher.*

This is a common point of confusion for learners. Because words like «моєю» and «твоєю» change so clearly, students sometimes try to invent forms like "йогом" or "їєю". These words do not exist. The pronoun stays frozen, while the adjective and noun around it still take their proper Instrumental endings: «з його **новим** друг**ом**».

Finally, let us look at demonstrative pronouns: **цей** (this) and **той** (that). These words are crucial for pointing out specific people, objects, or locations in space. For «цей», the Instrumental forms are **цим** (masculine/neuter) and **цією** (feminine). For «той», the forms are **тим** and **тією**.

Мій кіт любить спати за цим великим будинком. А собака часто ховається під тією старою ялинкою. Я не хочу розмовляти з тим чоловіком.

> *My cat likes to sleep behind this big building. And the dog often hides under that old spruce. I do not want to talk with that man.*

These pronouns are also very common in temporal expressions. When you want to say "this evening," you simply put both words in the Instrumental case: «цим вечором».

Цим вечором ми йдемо в театр. Тим часом мій брат готує вечерю вдома.

> *This evening we are going to the theater. Meanwhile, my brother is making dinner at home.*

<!-- INJECT_ACTIVITY: match-up-nom-ins -->
<!-- INJECT_ACTIVITY: quiz-pronoun-gender -->

## Повні словосполучення в орудному відмінку (Full Instrumental Phrases)

В українській мові слова в реченні завжди працюють разом. Коли ми будуємо повне словосполучення з прийменником, займенником, прикметником та іменником, ми створюємо граматичний ланцюжок. Кожна ланка в цьому ланцюжку повинна стояти в орудному відмінку. Стандартна модель виглядає так: прийменник + займенник + прикметник + іменник.

> *In Ukrainian, words in a sentence always work together. When we build a full phrase with a preposition, a pronoun, an adjective, and a noun, we create a grammatical chain. Every link in this chain must stand in the Instrumental case. The standard model looks like this: preposition + pronoun + adjective + noun.*

Я часто гуляю з моїм найкращим другом у нашому парку. Це мій улюблений час для відпочинку. Ми довго сидимо під старим високим деревом і розмовляємо. Я завжди ділюся з ним моїм новим планом.

> *I often walk with my best friend in our park. This is my favorite time for rest. We sit for a long time under an old tall tree and talk. I always share my new plan with him.*

Notice how every word in the phrase changes to match the noun. The preposition «з» tells us to use the Instrumental case for companionship. Thus, the pronoun becomes «моїм», the adjective becomes «найкращим», and the masculine noun becomes «другом».

Звучання цього ланцюжка повністю залежить від роду головного іменника. Чоловічий та середній рід використовують закінчення «-ім», «-им» та «-ом». Жіночий рід має інший ритм, де переважають звуки «о» та «е». А тепер подивіться на типовий жіночий ланцюжок.

Учора я познайомився з моєю новою сусідкою. Вона приїхала сюди зі своєю маленькою донькою. Ми довго стояли перед нашою старою школою. Потім ми пили чай з її старшою сестрою.

> *Yesterday I met my new neighbor. She came here with her little daughter. We stood for a long time in front of our old school. Then we drank tea with her older sister.*

The feminine chain, such as «з моєю новою сусідкою», uses a rhythmic repetition of «-єю» and «-ою». The repeated vowel sounds make these phrases incredibly easy to pronounce and remember once you catch the general pattern.

:::note
**Quick tip**
When you speak, try to memorize the whole chain as one continuous block of sound. Do not think about the grammar of each word separately. Just practice saying «з моєю новою сусідкою» out loud until it feels natural.
:::

Це граматичне правило працює для кожної функції орудного відмінка. Неважливо, чи ви говорите про компанію, місце або інструмент. Усі слова в групі повинні мати однакову форму.

Мій кіт часто спить за нашим великим будинком. А мій старший брат завжди пише цією новою ручкою. Я люблю малювати моїм синім олівцем у зошиті. Усі ці маленькі речі роблять мій день кращим.

> *My cat often sleeps behind our big building. And my older brother always writes with this new pen. I like to draw with my blue pencil in the notebook. All these little things make my day better.*

As you can see, the preposition «за» triggers the Instrumental case for location, giving us the full chain «за нашим великим будинком». The tool function works entirely without a preposition, so «ця нова ручка» directly becomes «цією новою ручкою».

Орудний відмінок також дуже часто зустрічається в сталих виразах. Це фрази, які носії мови використовують щодня. Два дуже популярні вирази часу використовують вказівні займенники: «тим часом» та «цим разом». Їх легко запам'ятати.

Тим часом ми готуємо смачну вечерю на кухні. Цим разом я зроблю все абсолютно правильно. Я роблю цю роботу з великим задоволенням. Ми швидко закінчимо проєкт з вашою допомогою.

> *Meanwhile, we are preparing a tasty dinner in the kitchen. This time I will do everything absolutely right. I do this work with great pleasure. We will quickly finish the project with your help.*

Phrases like «з великим задоволенням» (with great pleasure) and «з вашою допомогою» (with your help) bridge the gap between abstract grammar rules and fluent speech. You should memorize these collocations as fixed blocks of vocabulary to sound more natural.

<!-- INJECT_ACTIVITY: fill-in-full-chains -->

## Практика: Опиши свій день (Practice: Describe Your Day)

Сьогодні ми поєднаємо всі ці знання в одній історії. Уявіть, що ви пишете сторінку у свій щоденник про ідеальний вихідний. Зверніть увагу, як орудний відмінок допомагає описати компанію, місце та навіть атмосферу цього дня.

> *Today we will combine all this knowledge in one story. Imagine you are writing a page in your diary about a perfect weekend. Notice how the Instrumental case helps describe the company, the location, and even the atmosphere of this day.*

Сьогодні був просто чудовий день. Зранку я смачно снідала зі своєю найкращою подругою в новому кафе. Ми розмовляли про все на світі з великим задоволенням. Потім я гуляла тихим парком за цим старим кам'яним мостом. Була чудова погода, і я милувалася цією ранньою весною під високим синім небом. Вечір я провела з моїм коханим чоловіком за дуже романтичною вечерею. Ми насолоджувалися нашою смачною їжею, спокійною музикою та приємною бесідою.

> *Today was simply a wonderful day. In the morning, I had a delicious breakfast with my best friend in a new cafe. We talked about everything in the world with great pleasure. Then I walked through the quiet park behind this old stone bridge. The weather was wonderful, and I admired this early spring under the high blue sky. I spent the evening with my beloved husband at a very romantic dinner. We enjoyed our tasty food, calm music, and pleasant conversation.*

У реальному житті ви будете використовувати ці ланцюжки, щоб відповідати на питання «з ким?» або «чим?». Ставити запитання в орудному відмінку так само важливо, як і відповідати на них. Тепер давайте послухаємо, як звучать ці фрази в живій розмові двох друзів. Зверніть особливу увагу на незмінний займенник «його» та узгодження прикметників.

> *In real life, you will use these chains to answer questions like "with whom?" or "with what?". Asking questions in the Instrumental case is just as important as answering them. Now let's listen to how these phrases sound in a live conversation between two friends. Pay special attention to the invariable pronoun "його" (his) and the agreement of adjectives.*

> — **Андрій:** Привіт! З ким ти вчора ходив у кіно? *(Hi! Who did you go to the movies with yesterday?)*
> — **Богдан:** Привіт. Я ходив туди з моїм новим колегою. *(Hi. I went there with my new colleague.)*
> — **Андрій:** О, цікаво. А якою машиною ви туди їхали? *(Oh, interesting. And by what car did you go there?)*
> — **Богдан:** Ми їхали його старою Тойотою. *(We went by his old Toyota.)*
> — **Андрій:** Ви сиділи перед тим великим екраном? *(Did you sit in front of that big screen?)*
> — **Богдан:** Ні, ми сиділи за їхнім останнім рядом. *(No, we sat behind their last row.)*
> — **Андрій:** А після кіно ви гуляли містом? *(And after the movies, did you walk around the city?)*
> — **Богдан:** Так, ми зустрілися з нашою спільною знайомою. *(Yes, we met with our mutual acquaintance.)*
> — **Андрій:** З тією високою дівчиною? *(With that tall girl?)*
> — **Богдан:** Саме так. Вона прийшла зі своїм маленьким сином. *(Exactly. She came with her little son.)*

Коли ви тільки починаєте будувати такі довгі фрази, дуже легко зробити помилку. Найважливіше правило — уникати закінчень, які не існують в українській мові. Ніколи не використовуйте закінчення «-ым» для чоловічого роду або «-ой» для жіночого. Це груба помилка та ознака суржику. Пам'ятайте також, що слова «його» та «її» ніколи не змінюються, коли означають приналежність. Навіть якщо іменник стоїть в орудному відмінку, ми кажемо «з його братом», а не «з йоговим братом». А от слово «їхній» — це повноцінний прикметник, тому воно відмінюється: «з їхніми друзями».

> *When you are just starting to build such long phrases, it is very easy to make a mistake. The most important rule is to avoid endings that do not exist in the Ukrainian language. Never use the "-ым" ending for the masculine gender or "-ой" for the feminine. This is a gross mistake and a sign of Surzhyk. Also remember that the words "його" (his) and "її" (her) never change when they indicate possession. Even if the noun is in the Instrumental case, we say "з його братом", not "з йоговим братом". But the word "їхній" (their) is a full-fledged adjective, so it declines: "з їхніми друзями".*

:::tip
**Did you know?**
Proper Instrumental case endings are a strong marker of natural Ukrainian speech. Saying «з моїм новим другом» (with the clear «-им» ending) immediately sounds authentic and educated. Similarly, the feminine «-ою» ending in «з гарною дівчиною» creates a rhythmic flow that is uniquely Ukrainian.
:::

<!-- INJECT_ACTIVITY: error-correction-find-and-fix-agreement-errors-in-instrumental-phrases -->

## Підсумок

Let's review the core rules for building full noun phrases in the Instrumental case.

1. **Hard adjectives** take the endings **-им** (masculine/neuter) and **-ою** (feminine), as in «з новим другом» or «з гарною дівчиною».
2. **Soft adjectives** take the endings **-ім** and **-ьою**, as in «з останнім клієнтом» or «за синьою машиною».
3. **Possessive pronouns** decline similarly to adjectives. The pronoun **мій** becomes **моїм** or **моєю**, and **наш** becomes **нашим** or **нашою**.
4. The possessive pronouns **його** and **її** never change. You simply attach them to the declined noun: «з його братом».
5. Always use **full chains of agreement**, where every word matches the case of the noun: «з моїм найкращим другом».

Тепер ви можете легко розповідати про своїх друзів, колег та родичів. Головне — завжди пам'ятати про правильні закінчення.

> *Now you can easily talk about your friends, colleagues, and relatives. The main thing is to always remember the correct endings.*

:::info
**Self-check:**
1. How do you say "with our new neighbor (f)"?
2. Which pronoun never changes in the Instrumental case?
3. What is the ending for a soft masculine adjective?
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-adjectives-pronouns
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

**Level: A2 (Module 29/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю


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
