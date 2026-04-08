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
- `<!-- INJECT_ACTIVITY: match-up-match-nominative-phrases-to-instrumental-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-pronoun-form-vs-based-on-noun-gender -->`
- `<!-- INJECT_ACTIVITY: fill-in-build-full-sentences-using-preposition-pronoun-adjective-noun-in-instrumental -->`
- `<!-- INJECT_ACTIVITY: error-correction-correct-errors-in-instrumental-agreement -->`

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
## Прикметники в орудному відмінку (Adjectives in the Instrumental Case) (~600 words)

Ми вже знаємо, як говорити про компанію або інструменти. Ми кажемо «я гуляю з другом» або «я пишу олівцем». Але часто нам потрібно додати цікаві деталі у розмову. Який це друг? Який це олівець? Коли ми додаємо **прикметник** *(adjective)*, ми створюємо повнішу картину. Наприклад, ми використовуємо слово **найкращий** *(the best)* і можемо сказати «з найкращим другом» *(with the best friend)*. Або ми кажемо «новим олівцем» *(with a new pencil)*.
In Ukrainian grammar, adjectives must always agree with the noun they describe. This fundamental concept is called **узгодження** *(agreement)*. If the main noun is in the Instrumental case, the describing adjective must also take the Instrumental case. It must exactly match the noun's gender and number as well. This means both words change their endings together in the sentence. This is very different from English, where the adjective "new" stays the same everywhere. Understanding this agreement is the key to speaking naturally.

Давайте подивимося на прикметники твердої групи. Це слова з твердим приголосним звуком. Наприклад, **новий** *(new)*, **гарний** *(nice, beautiful)* або **старий** *(old)*. Для чоловічого та середнього роду ми використовуємо закінчення **-им**.
Наприклад, словосполучення «новий друг» змінюється на «з новим другом» в орудному відмінку. Both words get a completely new ending to show their grammatical role: «нов**им** друг**ом**». In English, you only need to add the preposition "with" to the phrase "a new friend". In Ukrainian, the preposition «з» automatically triggers the Instrumental case, which structurally changes both the adjective and the noun.
Для середнього роду правило працює абсолютно так само. Ми кажемо: «Ми відпочиваємо під високим небом» *(We are resting under the high sky)*. Слово «високий» отримує закінчення «-им», як і слова чоловічого роду.

Тепер детально поговоримо про жіночий рід твердої групи. Тут ми маємо красиве і дуже характерне закінчення **-ою**. Воно звучить глибоко, традиційно і мелодійно. Прикметники жіночого роду, такі як **гарна** *(beautiful)* або **нова** *(new)*, змінюються на **гарною** та **новою**.
Ми часто використовуємо це закінчення, коли говоримо про людей або предмети жіночого роду. Наприклад: «Я йду в кіно з новою подругою» *(I am going to the cinema with a new friend)*. Або: «Мій телефон лежить за великою книжкою» *(My phone is lying behind the big book)*. The ending «-ою» is a very strong and clear phonetic marker of the Instrumental case for feminine nouns and adjectives. It is very hard to confuse it with any other case in the language. Notice how the adjective and noun rhyme: «нов**ою** подруг**ою**».

В українській мові також є прикметники м'якої групи. Вони мають м'який приголосний звук перед закінченням. Наприклад, **синій** *(blue)*, **літній** *(summer)* або **домашній** *(domestic)*. Для цих прикметників закінчення будуть трохи іншими.
Для чоловічого та середнього роду ми використовуємо закінчення **-ім**. Слово «синій» стає «синім». Наприклад: «Я пишу нотатки синім олівцем» *(I write notes with a blue pencil)*.
Для жіночого роду ми маємо цікаве закінчення **-ьою**. Воно дуже схоже на тверде «-ою», але зберігає м'якість основи. Ми кажемо «синьою» або «домашньою». Наприклад: «Вона малює картину синьою ручкою» *(She is drawing a picture with a blue pen)*. The soft sign «ь» specifically shows that the consonant before it must remain soft when pronounced. This is an important distinction from the hard ending «-ою».

В українських школах діти вивчають ці граматичні правила у четвертому класі. Для тих, хто вивчає українську як іноземну, дуже важливо чітко запам'ятати ці базові патерни.
Here is a quick structural summary of the patterns for L2 learners. For masculine and neuter adjectives, use **-им** for hard stems and **-ім** for soft stems. For feminine adjectives, use **-ою** for hard stems and **-ьою** for soft stems.
Давайте порівняємо ці форми на живій практиці. Ми можемо довго розмовляти «з добрим сусідом» *(with a kind neighbor)* — це тверда група. Або ми розмовляємо «з давнім знайомим» *(with an old acquaintance)* — це м'яка група. Practice these adjective and noun pairings together frequently to make them sound completely natural in your own speech.

<!-- INJECT_ACTIVITY: fill-in-add-correct-instrumental-adjective-endings-to-complete-noun-phrases -->


## Присвійні та вказівні займенники (Possessive and Demonstrative Pronouns)

Зараз ми поговоримо про присвійні займенники. Це такі слова, як **мій** *(my)*, **твій** *(your)* та **свій** *(one's own)*. В орудному відмінку вони мають спеціальні форми для чоловічого та середнього роду. Ми використовуємо закінчення **-їм**. Отже, ми кажемо «з моїм другом» *(with my friend)* або «з твоїм братом» *(with your brother)*. Для жіночого роду ми маємо красиве закінчення **-єю**. Ми кажемо «з моєю мамою» *(with my mom)* або «з твоєю сестрою» *(with your sister)*. These three pronouns behave very similarly to adjectives. However, they feature a unique «ї» or «є» sound right before the ending. This makes them sound very melodic. Займенник «свій» працює абсолютно так само. Наприклад: «Я пишаюся своєю сестрою» *(I am proud of my sister)*. Або: «Він працює зі своїм батьком» *(He is working with his father)*. They perfectly match the gender and case of the noun they describe. Remember to always change both the pronoun and the noun together.

Тепер розглянемо займенники **наш** *(our)* та **ваш** *(your)*. Вони поводяться як звичайні прикметники твердої групи. Для чоловічого та середнього роду ми маємо закінчення **-им**. Ми кажемо «з нашим сусідом» *(with our neighbor)* або «з вашим сином» *(with your son)*. Для жіночого роду ми використовуємо стандарт закінчення **-ою**. Наприклад: «Ми розмовляємо з вашою вчителькою» *(We are talking with your teacher)*. Або: «Вони стоять за нашою школою» *(They are standing behind our school)*. However, the pronoun **їхній** *(their)* is different. It belongs to the soft group of adjectives. Тому ми кажемо «з їхнім братом» *(with their brother)* та «з їхньою донькою» *(with their daughter)*. In Ukrainian, it is standard and grammatically correct to decline the word for "their" just like an adjective. You might sometimes hear people use the invariable form «їх» instead. This is a common mistake influenced by Russian grammar. Always use the fully declined forms like «їхнім» and «їхньою» to speak clean and natural Ukrainian.

В українській мові є два присвійні займенники, які ніколи не змінюються. Це слова **його** *(his)* та **її** *(her)*. When these words act as possessive pronouns, they completely ignore the case of the surrounding words. Вони залишаються однаковими в усіх відмінках. Якщо ми говоримо про друга чоловіка, ми кажемо «з його другом» *(with his friend)*. Займенник «його» не отримує жодного нового закінчення. Якщо ми говоримо про сестру жінки, ми кажемо «з її сестрою» *(with her sister)*. Слово «її» також залишається незмінним. This rule is incredibly important because it is a very frequent source of errors for learners. Many students try to invent forms like «йогом» or «їєю» by analogy with other pronouns. Це велика граматична помилка. Simply memorize that «його» and «її» are locked in their base forms. Ми завжди кажемо «за його будинком» *(behind his house)*. Або ми кажемо «під її столом» *(under her table)* без жодних змін займенника.

Наостанок ми вивчимо важливі вказівні займенники. Це слова **цей** *(this)* та **той** *(that)*. Вони дуже часто використовуються в орудному відмінку для вказівки на місце або час. Займенник «цей» змінюється на **цим** для чоловічого та середнього роду. Для жіночого роду він змінюється на **цією**. Наприклад, ми можемо сказати «за цим будинком» *(behind this building)*. Або ми кажемо «перед цією машиною» *(in front of this car)*. Займенник «той» має схожі форми. Він змінюється на **тим** та **тією**. Ми кажемо «під тим деревом» *(under that tree)* або «за тією ялинкою» *(behind that spruce)*. These demonstrative pronouns are also essential for common temporal expressions. We frequently use the phrase «цим вечором» *(this evening)* to describe when an event happens. Ми також часто кажемо «тим часом» *(meanwhile)* у розповідях. Завжди узгоджуйте ці займенники з іменниками, щоб ваша мова звучала правильно та природно.

<!-- INJECT_ACTIVITY: match-up-match-nominative-phrases-to-instrumental-forms -->
<!-- INJECT_ACTIVITY: quiz-choose-the-correct-pronoun-form-vs-based-on-noun-gender -->


## Повні словосполучення в орудному відмінку (Full Instrumental Phrases)

Тепер ми можемо будувати довгі та красиві фрази. Українська мова дуже логічна. Уявіть, що ваші слова — це великий ланцюг. When we build a full phrase, we create a strict "Agreement Chain". Every single descriptive word in this chain must share the same case, gender, and number as the noun. The classic and most useful pattern has four parts: a preposition, a pronoun, an adjective, and a noun. Подивіться уважно на цю фразу: «з моїм найкращим другом» *(with my best friend)*. Спочатку ми маємо прийменник **з** *(with)*. Далі йде присвійний займенник **моїм** *(my)*. Потім ми додаємо прикметник **найкращим** *(best)*. І наприкінці стоїть іменник **другом** *(friend)*. Усі три слова (займенник, прикметник, іменник) стоять в орудному відмінку чоловічого роду. Це ідеальний граматичний ланцюг. You cannot mix cases or drop the endings for the adjectives. Every link in the chain must perfectly agree to make the sentence correct and natural.

Давайте порівняємо чоловічий та жіночий ланцюги. Вони звучать по-різному, але завжди мають однакову логіку. Чоловічий ланцюг має багато звуків «и» та «м». Наприклад: «Я розмовляю з моїм новим сусідом» *(I am talking with my new neighbor)*. Тут ми чуємо закінчення **-ім**, **-им**, **-ом**. Це звучить дуже твердо і послідовно. Жіночий ланцюг звучить зовсім інакше. Він дуже ритмічний і має багато голосних звуків «о» та «е». Ми кажемо: «Я говорю з моєю новою сусідкою» *(I speak with my new female neighbor)*. Тут ми використовуємо закінчення **-єю**, **-ою**, **-ою**. Це дуже гармонійний і мелодійний патерн. Notice how the feminine chain naturally flows because of the repeated rhythmic vowel sounds. Кожне слово в ланцюгу обов'язково змінюється. Ви ніколи не можете сказати «з мій новою сусідкою» або «з моєю новий сусідкою». Ви повинні змінити абсолютно всі слова.

Ці граматичні ланцюги працюють для всіх функцій орудного відмінка. Ви вже знаєте, що орудний відмінок показує компанію, місце або інструмент. Правила узгодження діють усюди однаково. Якщо ми говоримо про компанію, ми використовуємо прийменник «з». Наприклад: «Я обідаю з моєю старшою сестрою» *(I have lunch with my older sister)*. Якщо ми говоримо про місце, ми часто використовуємо прийменники «за» *(behind)* або «під» *(under)*. Наприклад: «Наш собака спить за нашим великим будинком» *(Our dog sleeps behind our big house)*. The same strict agreement chain applies when we talk about instruments or tools. We simply do not use a preposition here. Ми кажемо: «Я пишу цією новою ручкою» *(I am writing with this new pen)*. Граматика завжди залишається стабільною.

В українській мові є популярні сталі фрази, які використовують цей відмінок. Вони допомагають говорити більш природно та швидко. Ми часто використовуємо вказівні займенники для вираження часу. Наприклад, ми кажемо **тим часом** *(meanwhile)*, коли розповідаємо цікаву історію або новини. Або ми кажемо **цим разом** *(this time)*, коли розпочинаємо нову справу. We also have standard daily collocations that use full instrumental chains. Ми виконуємо улюблену роботу **з великим задоволенням** *(with great pleasure)*. Ми завжди кажемо хорошим друзям: «Я зробив це **з вашою допомогою** *(with your help)*». Це дуже корисні фрази для щоденного та ввічливого спілкування. Memorize these common chunks, and your spoken Ukrainian will sound much more authentic and fluid.

<!-- INJECT_ACTIVITY: fill-in-build-full-sentences-using-preposition-pronoun-adjective-noun-in-instrumental -->


## Практика: Опиши свій день (Practice: Describe Your Day)

Сьогодні ми будемо багато практикувати. Ми будемо описувати свій день. Коли ми розповідаємо історії, ми завжди згадуємо інших людей або речі. Використовуйте повні фрази в орудному відмінку для цього. Давайте прочитаємо сторінку зі щоденника. Дівчина описує свій ідеальний вихідний день. Вона використовує багато прикметників та займенників, щоб зробити текст цікавим. Зверніть увагу на закінчення слів. Усі слова в ланцюгу обов'язково мають однаковий відмінок. Це створює гарну гармонію в реченні.

> — **Щоденник:** Сьогодні був просто чудовий день. Я снідала зі своєю найкращою подругою в нашому улюбленому кафе. Ми розмовляли про все на світі. Ми пили каву з гарячим молоком і багато сміялися. Потім я довго гуляла великим міським парком. Я стояла за тим старим дерев'яним мостом і дивилася на воду. Там дуже красиво восени. Вечір я провела з моїм коханим чоловіком за дуже романтичною вечерею. Ми смачно їли і говорили про наші нові плани на майбутнє. Я відчуваю себе дуже щасливою людиною.

Цей короткий текст показує, як ми природно використовуємо граматичні ланцюги кожного дня. «Зі своєю найкращою подругою» — це ідеальний приклад узгодження. Кожне слово стоїть в орудному відмінку жіночого роду і має типове закінчення. «З моїм коханим чоловіком» — це чоловічий рід. Усі закінчення звучать чітко і твердо. Ви можете спробувати написати такий щоденник самостійно.

А тепер давайте послухаємо розмову двох хороших друзів. Вони давно не бачилися і зустрілися на вулиці. Вони запитують одне одного про останні новини. Зверніть особливу увагу на займенники **його** *(his)* та **її** *(her)* у їхній розмові. Remember that these specific possessive pronouns never change their form, even in the Instrumental case. They are invariable in Ukrainian.

> — **Андрій:** Привіт, Богдане! Як твої справи? З ким ти вчора ходив у кіно?
> — **Богдан:** Привіт, Андрію! Все добре. Я був з моїм новим колегою. Його звати Марко. Він щойно почав працювати з нами.
> — **Андрій:** Класно. А якою машиною ви їхали в центр? Вашою новою Хондою?
> — **Богдан:** Ні, ми їхали його старою Тойотою. Наша машина зараз у ремонті, тому він запропонував поїхати разом.
> — **Андрій:** Зрозуміло. А де ви вечеряли перед фільмом?
> — **Богдан:** За тим великим супермаркетом є дуже гарне кафе. Ми вечеряли там перед сеансом.

Ви бачите різницю в цій розмові? Ми кажемо «з моїм новим колегою». Тут усі слова змінюються за правилами. Але ми кажемо «його старою Тойотою». Займенник «його» залишається абсолютно незмінним. Змінюються лише прикметник «старою» і іменник «Тойотою». Це дуже важливо пам'ятати, коли ви говорите про інших людей та їхні речі.

Коли ви активно вивчаєте українську мову, дуже важливо говорити природно. Іноді студенти роблять типові помилки на початку. They often forget to change the pronoun and adjective together with the noun in the sentence. Sometimes learners use endings from other Slavic languages by mistake. In Ukrainian, the Instrumental case has very distinct, melodic, and beautiful sounds. Для чоловічого роду ми завжди використовуємо закінчення **-им** або **-ім**. Ми кажемо тільки «з моїм новим другом». Це звучить дуже по-українськи і граматично правильно. Для жіночого роду ми маємо закінчення **-ою** або **-єю**. Ми завжди кажемо «з моєю новою сусідкою». Використання правильних українських закінчень показує вашу велику повагу до мови. Це справжній маркер вашої української ідентичності та культури. Ваша мова звучить автентично, коли ви чітко дотримуєтеся цих правил. Завжди перевіряйте свій граматичний ланцюг у розмові. Не поспішайте, коли будуєте нову фразу. З часом ви будете говорити швидко і без помилок. Ваші українські друзі будуть приємно здивовані вашою правильною вимовою. Практика допомагає зробити ці правила автоматичними.

<!-- INJECT_ACTIVITY: error-correction-correct-errors-in-instrumental-agreement -->


## Підсумок

Давайте коротко повторимо головні правила, які ми сьогодні вивчили. Орудний відмінок має дуже чіткі закінчення. First, hard adjectives always take **-им** for masculine and neuter, and **-ою** for feminine (з новим, з новою). Second, soft adjectives take **-ім** and **-ьою** (з синім, із синьою). Third, possessive pronouns change too: «мій» becomes **моїм** or **моєю**, and «наш» becomes **нашим** or **нашою**. Fourth, remember the golden rule about **його** and **її**. These pronouns never change their form in the Instrumental case. Нарешті, завжди будуйте повні граматичні ланцюги. Усі слова у фразі «з моїм найкращим другом» повинні стояти в орудному відмінку. 

Тепер перевірте себе. Спробуйте дати відповіді на ці три запитання:
1. How do you say "with our new neighbor (f)" in Ukrainian?
2. Which possessive pronouns never change in the Instrumental case?
3. What is the correct ending for a soft masculine adjective?

Ваша українська мова стає дедалі кращою!

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
