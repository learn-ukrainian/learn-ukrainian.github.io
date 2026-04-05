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

(No injection markers found in prose. All activities will go to workbook.)

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

Ми вже добре знаємо, як говорити про спільну дію. Ми кажемо **«з другом»** *(with a friend)* або **«з братом»** *(with a brother)*. Але як описати цього друга? When we add an adjective to describe a noun, the adjective must perfectly match the noun's case and gender. We need special endings for adjectives in the Instrumental case. Це робить нашу мову красивою і дуже точною. *(This makes our language beautiful and very precise.)* Ми завжди змінюємо обидва слова у фразі. *(We always change both words in the phrase.)*

Почнемо з чоловічого та середнього роду. Більшість прикметників української мови належить до твердої групи. The hard group of adjectives in the masculine and neuter genders always takes the ending **-им** in the Instrumental case. The vowel «и» is the characteristic sound of the hard group here. Розглянемо кілька дуже корисних прикладів. *(Let's look at a few very useful examples.)* Ми часто відпочиваємо **під великим дубом** *(under a big oak)*. Новий магазин стоїть **за новим будинком** *(behind a new house)*. Діти граються **під старим деревом** *(under an old tree)*. Зверніть увагу на ці закінчення. Слово **новий** *(new)* легко стає **новим**. Слово **старий** *(old)* стає **старим**. Усі ці популярні слова закінчуються на **-им**. You simply replace the Nominative ending with **-им** for masculine and neuter nouns. Мій старший брат працює **з добрим другом** *(with a kind friend)*. Це просте і зрозуміле граматичне правило. *(This is a simple and clear grammatical rule.)*

Тепер подивимося на жіночий рід. Тут правило також дуже просте і логічне. The hard group of adjectives in the feminine gender takes the ending **-ою** in the Instrumental case. Notice the grammatical harmony between the feminine noun ending and the adjective ending. Both words in the phrase often end in «-ою». Він із задоволенням гуляє **з гарною дівчиною** *(with a beautiful girl)*. Студент уважно сидить **з великою книгою** *(with a big book)*. Я завжди пишу **новою ручкою** *(with a new pen)*. Слово **гарна** *(beautiful)* гармонійно змінюється на **гарною**. Слово **велика** *(big)* стає **великою**. Закінчення **-ою** звучить дуже м'яко і мелодійно. *(The ending -ою sounds very soft and melodic.)* The adjective and the noun work together to create a rhythmic pair, like «новою ручкою». Це допомагає легко запам'ятати правильну форму. *(This helps to easily remember the correct form.)* Моя сестра довго говорить **зі старою подругою** *(with an old friend)*. 

В українській мові є також м'яка група прикметників. Їх небагато, але вони дуже важливі для щоденного спілкування. For the soft group of adjectives in the masculine and neuter genders, the Instrumental case ending is **-ім**. The vowel «і» perfectly reflects the softening effect, replacing the hard «и» sound. Маленький хлопчик малює **синім олівцем** *(with a blue pencil)*. Ми довго гуляємо містом **літнім днем** *(on a summer day)*. Мій син зараз працює над **домашнім завданням** *(with homework)*. Прикметник **синій** *(blue)* стає **синім**. Прикметник **літній** *(summer)* стає **літнім**. The letter «і» keeps the preceding consonant soft in pronunciation. Це робить вимову слів дуже легкою і приємною. *(This makes the pronunciation of words very easy and pleasant.)*

Для жіночого роду м'якої групи ми маємо трохи інше закінчення. The feminine adjectives in the soft group take the ending **-ьою** in the Instrumental case. The soft sign «ь» preserves the softness of the consonant, and the letter «ю» completes the unique ending. Маленька дівчинка грається **синьою стрічкою** *(with a blue ribbon)*. Ми милуємося зоряною **літньою ніччю** *(on a summer night)*. Вони із задоволенням насолоджуються смачною **домашньою кухнею** *(with home cooking)*. Прикметник **синя** *(blue)* перетворюється на **синьою**. Прикметник **літня** *(summer)* стає **літньою**. Notice exactly how the soft sign connects the root of the word with the feminine ending. Ми дуже часто користуємося цією формою у нашому повсякденному житті. *(We very often use this form in our everyday life.)* Це нове закінчення також звучить дуже красиво і ритмічно. *(This new ending also sounds very beautiful and rhythmic.)*

<!-- INJECT_ACTIVITY: fill-in, Add correct Instrumental adjective endings to complete noun phrases, 8 items -->


## Присвійні та вказівні займенники (Possessive and Demonstrative Pronouns)

Займенники також змінюють свою форму в орудному відмінку. *(Pronouns also change their form in the Instrumental case.)* Ми використовуємо їх, коли говоримо про наші речі або про наших друзів. *(We use them when we talk about our things or about our friends.)* The possessive pronouns for the first and second person singular are «мій» *(my)* and «твій» *(your)*. For masculine and neuter nouns, these pronouns take the ending **-ім**: **моїм** and **твоїм**. Для жіночого роду ми використовуємо закінчення **-єю**: **моєю** та **твоєю**. *(For the feminine gender, we use the ending -єю: моєю and твоєю.)* Я часто гуляю в парку **з моїм татом** *(with my dad)*. Ти любиш довго говорити **з твоєю мамою** *(with your mom)*. Сьогодні я йду в кіно **з моїм новим другом** *(with my new friend)*. Вона працює над **твоєю важливою проблемою** *(on your important problem)*. These forms share phonetic similarities with soft adjective endings. Це правило робить нашу мову мелодійною. *(This rule makes our language melodic.)* Ми постійно використовуємо ці слова. *(We constantly use these words.)*

Тепер подивимося на займенники для множини та ввічливої форми. *(Now let's look at the pronouns for plural and formal form.)* The possessive pronouns «наш» *(our)* and «ваш» *(your)* behave exactly like hard group adjectives. For masculine and neuter nouns, they take the ending **-им**: **нашим** and **вашим**. Для жіночого роду вони мають закінчення **-ою**: **нашою** та **вашою**. *(For the feminine gender, they have the ending -ою: нашою and вашою.)* Ми любимо відпочивати **за нашим будинком** *(behind our house)*. Вони посадили квіти **перед нашим садом** *(in front of our garden)*. Директор дуже задоволений **вашою ідеєю** *(with your idea)*. Я хочу поговорити з **вашим лікарем** *(with your doctor)*. The grammatical harmony here is very consistent. Займенник і прикметник завжди мають схожі закінчення. *(The pronoun and the adjective always have similar endings.)* Це робить українську граматику передбачуваною. *(This makes Ukrainian grammar predictable.)* Ми пишаємося **нашою новою школою** *(of our new school)*.

Іноді нам потрібно вказати на конкретний предмет або час. *(Sometimes we need to point to a specific object or time.)* Для цього ми використовуємо вказівні займенники «цей» *(this)* та «той» *(that)*. Demonstrative pronouns also change their form to match the noun in the Instrumental case. The pronoun «цей» becomes **цим** for masculine/neuter and **цією** for feminine. The pronoun «той» changes to **тим** and **тією**. Я хочу поїхати додому **цим автобусом** *(by this bus)*. Ми зустрінемося **цим вечором** *(this evening)*. Мій кіт любить спати **за тією стіною** *(behind that wall)*. Хто зараз стоїть **під тим деревом** *(under that tree)*? These pronouns are useful for pointing out specific things or particular moments in time. Я пишу листи **цією синьою ручкою** *(with this blue pen)*. Він працює над **тим складним завданням** *(on that difficult task)*. Зверніть увагу на вимову. *(Pay attention to the pronunciation.)*

Нарешті, ми маємо поговорити про особливі випадки. *(Finally, we have to talk about special cases.)* In Ukrainian, the pronoun for the third person plural is «їхній» *(their)*. This word looks and acts exactly like a soft group adjective. Тому в орудному відмінку воно стає **їхнім** для чоловічого та середнього роду. *(Therefore, in the Instrumental case, it becomes їхнім for masculine and neuter gender.)* Для жіночого роду ми маємо форму **їхньою**. *(For the feminine gender, we have the form їхньою.)* Ми задоволені **їхнім новим проектом** *(with their new project)*. Вони пишаються **їхньою розумною донькою** *(of their smart daughter)*. However, the pronouns «його» *(his)* and «її» *(her)* are invariable. These words never change, regardless of the case or the gender of the noun. Я розмовляю з **його лікарем** *(with his doctor)*. Мій сусід гуляє з **її собакою** *(with her dog)*. Це правило дуже легко запам'ятати. *(This rule is very easy to remember.)* Вам не потрібно змінювати ці два слова. *(You do not need to change these two words.)*

<!-- INJECT_ACTIVITY: match-up, Match Nominative phrases (мій новий друг) to Instrumental forms (моїм новим другом), 8 items -->
<!-- INJECT_ACTIVITY: quiz, Choose the correct pronoun form (моїм vs. моєю) based on noun gender, 8 items -->


## Повні словосполучення в орудному відмінку (Full Instrumental Phrases)

Тепер ми готові будувати довгі речення. *(Now we are ready to build long sentences.)* In Ukrainian, every word in a noun phrase must agree in case, gender, and number. Це називається ланцюгом узгодження. *(This is called an agreement chain.)* Let's look at a full chain for masculine and neuter nouns. The structure is usually: preposition + pronoun + adjective + noun. Усі ці слова мають стояти в орудному відмінку. *(All these words must stand in the Instrumental case.)* Наприклад, ми кажемо: я гуляю **з моїм найкращим другом** *(with my best friend)*. The preposition «з» requires the Instrumental case. The pronoun «мій» becomes **моїм** *(my)*. The adjective «найкращий» becomes **найкращим** *(best)*. The noun «друг» becomes **другом** *(friend)*. Усе дуже логічно і послідовно. *(Everything is very logical and consistent.)* Ще один приклад: мій кіт спить **під цим великим вікном** *(under this big window)*. The neuter noun «вікно» becomes **вікном** *(window)*. The demonstrative pronoun «цей» changes to **цим** *(this)*. The adjective «великий» becomes **великим** *(big)*. Notice how the endings rhyme. Це допомагає відчути ритм мови. *(This helps to feel the rhythm of the language.)* Ми часто використовуємо такі довгі фрази щодня. *(We often use such long phrases every day.)* Вони роблять наше мовлення багатим. *(They make our speech rich.)*

Для жіночого роду цей ланцюг працює ще простіше. *(For the feminine gender, this chain works even more simply.)* The grammatical harmony in feminine phrases is extremely consistent. Almost every word will end in **-ою** or **-ьою**. Це дуже приємно звучить. *(This sounds very pleasant.)* Наприклад, дівчина розмовляє **зі своєю старшою сестрою** *(with her older sister)*. The noun «сестра» becomes **сестрою** *(sister)*. The possessive pronoun «свій» becomes **своєю** *(one's own)*. The adjective «старша» becomes **старшою** *(older)*. Зверніть увагу на вимову цих закінчень. *(Pay attention to the pronunciation of these endings.)* Усі слова ніби співають одну пісню. *(All the words seem to sing one song.)* Інший приклад: ми зустрінемося **за тією новою школою** *(behind that new school)*. The noun «школа» becomes **школою** *(school)*. The demonstrative pronoun «та» changes to **тією** *(that)*. The adjective «нова» changes to **новою** *(new)*. Якщо слово м'яке, ми використовуємо закінчення **-ьою**. *(If the word is soft, we use the ending -ьою.)* Наприклад: вона пише **цією синьою ручкою** *(with this blue pen)*. This strong rhyme makes feminine Instrumental phrases easy to remember and use correctly.

Орудний відмінок також допомагає нам говорити про час. *(The Instrumental case also helps us talk about time.)* In Ukrainian, we often use full Instrumental phrases without any prepositions. This expresses "when" something happens or "how" it occurs. Ми називаємо це сталими виразами. *(We call this set expressions.)* Наприклад, ми часто кажемо **цим вечором** *(this evening)* або **тим вечором** *(that evening)*. Я хочу піти в кіно **цим вечором**. *(I want to go to the cinema this evening.)* Another very common phrase is **тим часом** *(meanwhile)*. Він читав книгу, а вона **тим часом** готувала вечерю. *(He was reading a book, and she meanwhile was cooking dinner.)* Ви також можете почути фразу **кожним разом** *(every time)*. **Кожним разом** він робить це краще. *(Every time he does it better.)* Ці фрази є частиною щоденного спілкування. *(These phrases are part of daily communication.)* Вони звучать дуже природно. *(They sound very natural.)*

Коли ми будуємо такі довгі фрази, важливо пам'ятати про прийменники. *(When we build such long phrases, it is important to remember the prepositions.)* The preposition «з» means "with". It shows companionship or the tool used for an action. Наприклад: я працюю **з цим новим комп'ютером** *(with this new computer)*. However, other prepositions indicate spatial relationships. These include **між** *(between)*, **за** *(behind)*, **під** *(under)*, and **перед** *(in front of)*. Собака сидить **перед нашим старим будинком** *(in front of our old house)*. Both uses require the exact same grammatical agreement chain. Their real-world meaning, however, is entirely different.

<!-- INJECT_ACTIVITY: fill-in, Build full sentences using preposition + pronoun + adjective + noun in Instrumental, 8 items -->


## Практика: Опиши свій день (Practice: Describe Your Day)

Сьогодні був абсолютно ідеальний день. *(Today was an absolutely perfect day.)* Вранці я довго гуляв **з моїм найкращим другом** *(with my best friend)* у центральному парку. Ми сиділи на траві під **тим великим деревом** *(under that big tree)* і слухали птахів. Потім ми обідали **за цим маленьким столом** *(at this small table)* у нашому улюбленому кафе. Я пив чорну каву і розмовляв **з моїм новим колегою** *(with my new colleague)*, який працює поруч. Він приїхав у кафе **своїм старим автомобілем** *(by his old car)*. Після обіду я інтенсивно працював **за своїм робочим столом** *(at my work desk)*. Робота здавалася легкою і приємною. *(The work seemed easy and pleasant.)* Увечері я зустрівся **зі своєю новою сусідкою** *(with my new neighbor)*. Вона гуляла **зі своїм маленьким сином** *(with her small son)* перед нашим високим будинком. Ми говорили про життя і мистецтво **цим теплим вечором** *(this warm evening)*. Я повернувся додому **останнім нічним автобусом** *(by the last night bus)*. Це був дуже довгий, але цікавий день. *(It was a very long, but interesting day.)*

Олег і Катерина дуже давно не бачилися. *(Oleh and Kateryna haven't seen each other for a very long time.)* Вони випадково зустрілися на вулиці біля магазину. *(They accidentally met on the street near the store.)*

> — **Олег:** Привіт, Катерино! *(Hi, Kateryna!)* Я не бачив тебе майже цілий рік! *(I haven't seen you for almost a whole year!)*
> — **Катерина:** Привіт, Олегу! *(Hi, Oleh!)* Так, я багато подорожувала Європою **зі своєю старшою сестрою** *(with my older sister)*.
> — **Олег:** Як цікаво! *(How interesting!)* Ви постійно літали літаком? *(Did you constantly fly by plane?)*
> — **Катерина:** Ні, я їхала додому **цим новим швидким потягом** *(by this new fast train)*. Це набагато зручніше. *(It is much more convenient.)* А що в тебе нового в житті? *(And what's new in your life?)*
> — **Олег:** Я вчора довго розмовляв **з нашим спільним знайомим** *(with our mutual acquaintance)*. Він тепер працює **головним фінансовим менеджером** *(as a chief financial manager)* у банку.
> — **Катерина:** О, це дійсно чудова новина. *(Oh, that is really great news.)* Я також активно шукаю нову роботу **з хорошим гнучким графіком** *(with a good flexible schedule)*.

When building these long phrases, the final noun is always the anchor for the whole grammatical structure. Every single word in the phrase must match the gender, number, and case of that specific noun. A common mistake for learners is mixing endings from different genders. For example, you cannot say *з моїм новою другом. The possessive pronoun «моїм» is masculine, the adjective «новою» is feminine, and the noun «другом» is masculine. The entire chain must agree perfectly to sound natural. The correct form is **з моїм новим другом** *(with my new friend)*. Always check the gender of the noun first in the Nominative case before you speak. If the noun is feminine, like «подруга» *(female friend)*, then every word gets a feminine ending: **з моєю новою подругою** *(with my new female friend)*.

<!-- INJECT_ACTIVITY: error-correction, Find and fix agreement errors in Instrumental phrases, 6 items -->

Орудний відмінок дуже часто допомагає нам детально описувати багато різних ситуацій. *(The Instrumental case very often helps us describe many different situations in detail.)* Ми регулярно використовуємо його для опису компанії, інструменту, точного місця та професії. *(We regularly use it to describe company, instrument, exact place, and profession.)* Тепер ви можете впевнено будувати довгі, красиві та правильні українські речення. *(Now you can confidently build long, beautiful, and correct Ukrainian sentences.)*


## Підсумок

У цьому модулі ми будували довгі словосполучення в орудному відмінку. *(In this module, we built long phrases in the Instrumental case.)* Ви тепер вмієте правильно узгоджувати іменники, прикметники та займенники. *(You now know how to correctly agree nouns, adjectives, and pronouns.)* 

Перевірте свої знання та дайте відповіді на ці питання: *(Check your knowledge and answer these questions:)*

- Як змінюється закінчення твердої групи прикметників у чоловічому роді? *(How does the ending of the hard group of adjectives change in the masculine gender?)* Відповідь: **-им**.
- Яке закінчення мають присвійні займенники жіночого роду в орудному відмінку? *(What ending do feminine possessive pronouns have in the Instrumental case?)* Відповідь: **-ою**.
- Як сказати «with my best friend» (masculine) та «with my best friend» (feminine)? Відповідь: **з моїм найкращим другом** / **з моєю найкращою подругою**.
- Чи змінюються займенники «його» та «її»? *(Do the pronouns "його" and "її" change?)* Відповідь: Ні, вони незмінні. *(No, they are invariable.)*

Ви чудово засвоїли цей матеріал! *(You have mastered this material perfectly!)*

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
