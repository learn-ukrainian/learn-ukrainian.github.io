<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/vocative-expanded.yaml` file for module **27: Пане лікарю! Друже мій!** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-formal-vocative -->`
- `<!-- INJECT_ACTIVITY: match-professions-vocative -->`
- `<!-- INJECT_ACTIVITY: error-correction-focus-fix-vocative-errors -->`
- `<!-- INJECT_ACTIVITY: quiz-focus-choose-the-correct-vocative-register-for-a-given-social-situation -->`
- `<!-- INJECT_ACTIVITY: group-sort-focus-sort-vocative-forms-by-register-formal-professional-emotional -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the correct vocative of professional titles and names (пане _____, пані
    _____)
  items: 8
  type: fill-in
- focus: Choose the correct vocative register for a given social situation
  items: 8
  type: quiz
- focus: Match nominative forms to their vocative equivalents (лікар → лікарю, вчитель
    → вчителю, друг → друже)
  items: 8
  type: match-up
- focus: Fix vocative errors (*пан лікар → пане лікарю, *друже моя → подруго моя,
    *Мій друже → Друже мій)
  items: 8
  type: error-correction
- focus: Sort vocative forms by register (formal, professional, emotional)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- добродій (sir (literary/diaspora))
- добродійка (madam (literary/diaspora))
- емоційний (emotional)
- ніжний (tender, affectionate)
- колега (colleague)
required:
- кличний (vocative (case))
- звертання (address, appeal)
- пан (Mr., sir)
- пані (Mrs., Ms., madam)
- лікар (doctor)
- вчитель (teacher)
- друг (friend)
- ввічливий (polite)
- офіційний (official, formal)
- професія (profession)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пане, пані: формальне звертання (Formal Address)

In your earlier lessons, you learned how to use the vocative case for basic names, calling out to friends like «Тарасе!» or «Олено!». Now, as you navigate more complex social and professional situations, you need to master formal address. In Ukrainian, politeness requires specific grammatical structures. You cannot simply use a person's name in its dictionary form when talking to them directly. The vocative case is absolutely mandatory for all forms of address. Using the nominative case instead of the vocative sounds unnatural and is often a direct result of Russian influence. Calling someone «Маріє!» is correct, while saying «Пані Марія!» to her face is a grammatical mistake.

Для офіційного звертання ми використовуємо слова «пане» або «пані» разом із назвою професії. Слово «пане» вимагає кличного відмінка для наступного іменника. Іменник із твердим приголосним отримує закінчення «-е», як «пане директоре» або «пане професоре». М’який приголосний вимагає закінчення «-ю», наприклад, «пане лікарю» чи «пане водію».

> *For formal address, we use the words "пане" or "пані" together with the name of the profession. The word "пане" requires the vocative case for the following noun. A noun with a hard consonant gets the ending "-е", like "пане директоре" or "пане професоре". A soft consonant requires the ending "-ю", for example, "пане лікарю" or "пане водію".*

Addressing women formally is slightly different. The word «пані» is invariable, meaning it never changes its form. However, the female profession or title that follows it must still take the vocative case. Most feminine roles will take the «-о» ending. This creates polite and standard forms like «пані вчителько» or «пані директорко».

Ми також використовуємо ці слова разом із прізвищами людей. Чоловічі прізвища обов'язково змінюються у кличному відмінку після слова «пане». Зазвичай вони отримують закінчення «-у». Тому ми завжди кажемо «пане Коваленку» або «пане Шевченку». Жіночі прізвища на «-о» часто не змінюються. Після слова «пані» ми залишаємо жіноче прізвище в називному відмінку. Тому правильно казати «пані Коваленко» або «пані Шевченко».

> *We also use these words together with people's surnames. Masculine surnames necessarily change in the vocative case after the word "пане". Usually, they get the ending "-у". Therefore, we always say "пане Коваленку" or "пане Шевченку". Feminine surnames ending in "-о" often do not change. After the word "пані", we leave the feminine surname in the nominative case. Therefore, it is correct to say "пані Коваленко" or "пані Шевченко".*

Understanding this system is also a matter of cultural identity and decolonization. Historically, «пан» and «пані» were the traditional, respectful ways Ukrainians addressed each other. During the Soviet era, these words were heavily suppressed and replaced by the Russian-derived «товариш» (comrade). Today, using «пане» and «пані» is a conscious choice to speak authentic Ukrainian. It reconnects the language with its roots. You can hear this deep tradition in the famous Ukrainian Christmas carol, which opens with the respectful greeting: «Добрий вечір тобі, пане господарю!».

Існують також красиві літературні альтернативи: «добродію» та «добродійко». Ви рідко почуєте їх на вулиці в щоденних розмовах. Проте це дуже ввічливі форми. Їх часто використовує українська діаспора в офіційних листах. Ви можете написати «Шановний добродію!» для вираження глибокої поваги.

> *There are also beautiful literary alternatives: "добродію" and "добродійко". You will rarely hear them on the street in everyday conversations. However, these are very polite forms. The Ukrainian diaspora often uses them in official letters. You can write "Шановний добродію!" to express deep respect.*

:::info
**Grammar box** — When combining a title and a surname, remember the pattern: «пане Коваленку» (the masculine surname takes the vocative ending) but «пані Коваленко» (the feminine surname remains in the nominative).
:::

<!-- INJECT_ACTIVITY: fill-in-formal-vocative -->

## Професійні звертання (Professional Vocative)

When addressing professionals directly, the vocative case endings depend on the final consonant of the noun. Most masculine professions belong to the second declension. If the word ends in a hard consonant, we add the ending «-е». For example, the word for engineer becomes «інженере», and the word for master becomes «майстре». If the word ends in a soft consonant or a liquid consonant, we use the ending «-ю». This means the word for doctor changes to «лікарю», and the word for teacher becomes «вчителю».

Українська мова має одне цікаве правило для слів іншомовного походження на «-ер» або «-ір». Такі слова мають твердий приголосний у кінці, тому вони отримують закінчення «-е». Ми кажемо «професоре», «директоре» або «офіцере». Але питомі українські слова або давно запозичені професії на «-ар» та «-яр» належать до м'якої групи. Тому ми завжди використовуємо закінчення «-ю» для таких професій. Правильно казати «лікарю», «перукарю» або «касирю».

> *The Ukrainian language has one interesting rule for words of foreign origin ending in "-ер" or "-ір". Such words have a hard consonant at the end, so they get the "-е" ending. We say "професоре", "директоре", or "офіцере". But native Ukrainian words or long-borrowed professions ending in "-ар" and "-яр" belong to the soft group. Therefore, we always use the "-ю" ending for such professions. It is correct to say "лікарю", "перукарю", or "касирю".*

Ukrainian naturally and actively uses femininitives for professions. When you address a female professional, you must use the feminine form of her title. Most of these feminine titles end in «-а» or «-я» and belong to the first declension. This pattern is very straightforward because it follows the basic rule you learned in the A1 level. Words ending in a hard consonant plus «-а» change the ending to «-о» in the vocative case.

Коли ви звертаєтеся до жінки, ви використовуєте жіночу форму професії. Наприклад, слово «вчителька» у кличному відмінку має форму «вчителько». Жінка-лікар — це «лікарка», тому ми кажемо «лікарко». Слово «журналістка» змінюється на «журналістко», а «професорка» стає «професорко». Ця зміна є дуже природною та регулярною. Ви можете легко утворити форму кличного відмінка для більшості жіночих професій.

> *When you address a woman, you use the feminine form of the profession. For example, the word "вчителька" in the vocative case has the form "вчителько". A female doctor is "лікарка", so we say "лікарко". The word "журналістка" changes to "журналістко", and "професорка" becomes "професорко". This change is very natural and regular. You can easily form the vocative case for most feminine professions.*

Some professional nouns are common gender, meaning the same word applies to both men and women. The vocative ending depends strictly on the word's grammatical class, not the gender of the person. For example, the word for colleague takes the «-о» ending for everyone, becoming «колего». Another important word is the one for judge, which is a soft-group noun and takes «-ю» to become «суддю». There are also nouns from the mixed declension group that take the «-у» ending. The word for comrade changes to «товаришу», and the word for listener becomes «слухачу».

:::info
**Grammar box** — The word «колега» always takes the «-о» ending in the vocative case, regardless of whether you are speaking to a man or a woman. You say «пане колего» to a man and «пані колего» to a woman.
:::

Let's see how these formal and professional vocative forms work in a real situation. When visiting a doctor, patients start with a highly formal address. Once the doctor establishes a professional relationship, they might use the patient's surname. Notice how the patient transitions from the full formal title to a simpler professional address at the end.

> — **Пацієнт (Олег):** Добрий день, пане лікарю! Мені потрібна ваша допомога. *(Good afternoon, doctor! I need your help.)*
> — **Лікар:** Добрий день, пане Ковальчуку. Сідайте, будь ласка. Що вас турбує? *(Good afternoon, Mr. Kovalchuk. Please, sit down. What is bothering you?)*
> — **Пацієнт (Олег):** У мене дуже болить голова і висока температура. *(I have a bad headache and a high temperature.)*
> — **Лікар:** Зрозуміло. Зараз я вас огляну. Відкрийте рот. *(Understood. I will examine you now. Open your mouth.)*
> — **Пацієнт (Олег):** Дякую, лікарю. Ви можете виписати мені ліки? *(Thank you, doctor. Can you prescribe me medicine?)*
> — **Лікар:** Так, звичайно. Я напишу рецепт. *(Yes, of course. I will write a prescription.)*

У цьому діалозі Олег спочатку каже «пане лікарю», щоб показати велику повагу. Лікар відповідає «пане Ковальчуку». Він використовує прізвище пацієнта у кличному відмінку. Наприкінці Олег каже просто «лікарю». Це також ввічливо, але трохи менш формально.

<!-- INJECT_ACTIVITY: match-professions-vocative -->

## Друже мій, люба моя: емоційний кличний (Emotional Vocative)

When you speak to close friends or loved ones, the vocative case helps express warmth and intimacy. The word for a male friend is «друг». Because its stem ends in a hard consonant «-г», it undergoes a consonant mutation in the vocative case, changing the «-г» to «-ж». This makes the vocative form «друже».

Коли ви говорите з жінкою, ви кажете «подруга». Це слово має закінчення «-а», тому в кличному відмінку воно стає «подруго». Ви також можете використовувати емоційні слова. Наприклад, ви можете сказати «любий» до чоловіка або «люба» до жінки. Ці слова є прикметниками. Прикметники не змінюють свою форму в кличному відмінку. Вони залишаються в називному відмінку.

> *When you speak to a woman, you say "подруга". This word has the ending "-a", so in the vocative case it becomes "подруго". You can also use emotional words. For example, you can say "любий" to a man or "люба" to a woman. These words are adjectives. Adjectives do not change their form in the vocative case. They remain in the nominative case.*

Ukrainian is often described as a very melodic and tender language. This is partly because it has a rich system of diminutive forms. You can make almost any word sound smaller or more affectionate. These affectionate forms are very common when addressing children, romantic partners, or very close friends.

Люди часто називають коханих людей дуже ніжними словами. Вони кажуть «серденько», що означає маленьке серце. Вони також кажуть «сонечко» або «зіронько». Якщо жінку звати Люба, її можна ніжно назвати «любочко». Іменники середнього роду із закінченням «-ко» можуть мати закінчення «-о» в кличному відмінку. Але часто вони не змінюють свою форму. Ви можете казати і «серденько», і «сонечко» як звертання.

> *People often call their loved ones by very tender words. They say "серденько", which means a little heart. They also say "сонечко" or "зіронько". If a woman's name is Lyuba, she can be tenderly called "любочко". Neuter nouns with the ending "-ко" can have the "-о" ending in the vocative case. But often they do not change their form. You can say both "серденько" and "сонечко" as an address.*

:::tip
**Did you know?** — The Ukrainian word for a star is «зірка», but in folk songs and poetry, people often use the diminutive vocative form «зіронько» to address a beloved woman.
:::

When you use a possessive pronoun like "my" with a vocative noun, the word order changes. In English, you say "My friend". In Ukrainian, the pronoun usually comes after the noun when you address someone directly.

Українці майже завжди кажуть «друже мій», а не «мій друже». Ви також кажете «мамо моя», «любов моя» або «сину мій». Такий порядок слів робить фразу більш емоційною та мелодійною. Зверніть увагу, що займенники «мій» або «моя» не змінюють свою форму. Вони завжди стоять у називному відмінку, навіть якщо іменник стоїть у кличному.

The vocative case is also preserved in common emotional exclamations and religious expressions. The most frequent phrase you will hear is «Боже мій!» which means "My God!". The word «Бог» takes the «-е» ending to become «Боже». Similarly, the word «Господь» becomes «Господи!». 

Коли ви звертаєтеся до кількох людей, ви використовуєте множину. Кличний відмінок у множині зазвичай має таку саму форму, як і називний відмінок. Ви кажете «друзі» або «колеги». Але є один дуже важливий виняток. Слово «пани» в кличному відмінку має форму «панове». Це дуже ввічливе звертання до групи чоловіків або змішаної групи.

> *When you address several people, you use the plural. The vocative case in the plural usually has the same form as the nominative case. You say "друзі" or "колеги". But there is one very important exception. The word "пани" in the vocative case has the form "панове". This is a very polite address to a group of men or a mixed group.*

Let's see how these emotional forms sound in a real conversation. After his visit to the doctor, Oleh calls his close friend and his wife to share the good news. Notice how quickly his language shifts from the formal professional register to a very intimate and emotional tone.

> — **Олег:** Друже мій, уяви собі! Лікар сказав, що я здоровий. *(My friend, imagine that! The doctor said that I am healthy.)*
> — **Друг:** Боже мій! Це чудова новина, Олеже. Я дуже радий. *(My God! This is wonderful news, Oleh. I am very glad.)*
> — **Олег:** Дякую, друже! Зараз я подзвоню дружині. *(Thank you, friend! Now I will call my wife.)*
> — **Олег:** Кохана моя, сонечко! У мене все добре. *(My beloved, sunshine! Everything is fine with me.)*

<!-- INJECT_ACTIVITY: error-correction-focus-fix-vocative-errors -->

## Який кличний обрати? (Choosing the Right Vocative)

Ukrainian uses the vocative case not just to call someone, but to show social distance and respect. Choosing the right word is like choosing the right clothes for an event. If you use a very formal address with a close friend, it sounds cold and strange. But if you use an intimate word with a stranger, it can be rude.

Українська мова має багатий вибір звертань для кожної ситуації. Ми використовуємо офіційні форми для незнайомих людей або на роботі. Наприклад, ми кажемо «пане директоре» або «пані вчителько». Нейтральна ввічливість — це «пане» або «пані» плюс ім'я, наприклад «пані Олено». Для друзів ми беремо просто ім'я: «Тарасе» чи «Анно». А для найрідніших людей існують ніжні слова, такі як «серденько» або «сонечко».

> *The Ukrainian language has a rich choice of addresses for every situation. We use formal forms for strangers or at work. For example, we say "пане директоре" or "пані вчителько". Neutral politeness is "пане" or "пані" plus a first name, for example, "пані Олено". For friends, we just take the first name: "Тарасе" or "Анно". And for the dearest people, there are tender words, such as "серденько" or "сонечко".*

Let's look at some practical situations. Imagine you are writing an email to your university professor. You should start with «Шановний пане професоре» or use their first name and patronymic, like «Сергію Васильовичу». In a restaurant, it is polite to call the waiter «пане офіціанте», not just "boy" or "excuse me".

Якщо ви говорите зі своїм сусідом, який старший за вас, найкраще сказати «пане Степане». Це показує повагу, але не звучить занадто офіційно. Використання імені в кличному відмінку — це золота середина. Це найкращий спосіб звернутися до колеги або знайомого. Використовуйте його, якщо ви маєте добрі стосунки.

> *If you are talking to your neighbor who is older than you, it is best to say "пане Степане". This shows respect but does not sound too formal. Using the first name in the vocative case is the golden mean. It is the best way to address a colleague or an acquaintance. Use it if you have a good relationship.*

When learning Ukrainian, it is easy to make mistakes with direct address. The most common error is using the nominative case instead of the vocative.

:::info
**Grammar box** — Never say «Привіт, Іван!» or «Добрий день, пан директор!». Always change the noun to the vocative: «Привіт, Іване!» and «Добрий день, пане директоре!». If you use the nominative, it sounds like you are talking *about* the person, not *to* them.
:::

Інша часта помилка — це неправильний рід займенника або прикметника. Ви повинні пам'ятати, що слово «друг» чоловічого роду, а «подруга» — жіночого. Тому ми кажемо «друже мій», але «подруго моя». Також зверніть увагу на ім'я Ігор. Сучасна літературна норма вимагає закінчення «-ю», тому правильно говорити «Ігорю», а не «Ігоре».

> *Another frequent mistake is the wrong gender of the pronoun or adjective. You must remember that the word "друг" is masculine, and "подруга" is feminine. Therefore, we say "друже мій", but "подруго моя". Also, pay attention to the name Ihor. The modern literary norm requires the ending "-ю", so it is correct to say "Ігорю", not "Ігоре".*

The vocative case is much more than just a grammatical rule you have to memorize. It is the music of the Ukrainian language. When you use it correctly, you show that you understand the culture.

Кличний відмінок допомагає будувати місток між людьми. Коли ви використовуєте правильне звертання, людина відчуває вашу повагу та увагу. Ви показуєте, що не просто перекладаєте слова з англійської. Ви дійсно думаєте українською мовою. Говоріть красиво, і люди завжди відповідатимуть вам усмішкою.

> *The vocative case helps build a bridge between people. When you use the correct address, the person feels your respect and attention. You show that you are not just translating words from English. You are truly thinking in Ukrainian. Speak beautifully, and people will always answer you with a smile.*

<!-- INJECT_ACTIVITY: quiz-focus-choose-the-correct-vocative-register-for-a-given-social-situation -->
<!-- INJECT_ACTIVITY: group-sort-focus-sort-vocative-forms-by-register-formal-professional-emotional -->

## Підсумок

Ми вивчили багато нових правил сьогодні. Кличний відмінок робить вашу мову природною та ввічливою. Згадаємо три головні закінчення. Жіночі імена та тверді чоловічі іменники часто мають закінчення «-о»: мамо, Оксано. Чоловічі слова із твердим приголосним закінчуються на «-е»: пане, директоре, Петре. М'які слова та пестливі форми отримують закінчення «-ю»: лікарю, вчителю, бабусю.

> *We learned many new rules today. The vocative case makes your speech natural and polite. Let's recall the three main endings. Feminine names and hard masculine nouns often take the ending "-о": мамо, Оксано. Masculine words with a hard consonant end in "-е": пане, директоре, Петре. Soft words and diminutive forms get the ending "-ю": лікарю, вчителю, бабусю.*

Тепер час перевірити свої знання. Спробуйте дати відповіді на ці питання. По-перше, як звернутися до вчителя чоловіка? Правильна відповідь: пане вчителю. По-друге, як сказати «My friend» українською мовою? Правильно говорити: друже мій. По-третє, чи змінюється прізвище жінки після слова «пані»? Ні, воно залишається без змін. І нарешті, яка форма є стандартною для імені Олег? Це форма Олегу.

> *Now it is time to check your knowledge. Try to answer these questions. First, how do you address a male teacher? The correct answer is: пане вчителю. Second, how do you say "My friend" in Ukrainian? It is correct to say: друже мій. Third, does a woman's surname change after the word "пані"? No, it remains unchanged. Finally, what form is standard for the name Олег? It is the form Олегу.*

:::note
**Quick tip** — Don't be afraid to make mistakes with the vocative case. Ukrainians will be very happy and impressed that you are trying to use it!
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: vocative-expanded
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

**Level: A2 (Module 27/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

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
