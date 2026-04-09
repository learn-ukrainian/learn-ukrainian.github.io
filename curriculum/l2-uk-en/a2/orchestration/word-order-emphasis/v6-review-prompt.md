<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 50: Порядок слів і наголос у реченні (A2, A2.7 [Complex Sentences and Conditionals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-050
level: A2
sequence: 50
slug: word-order-emphasis
version: '1.0'
title: Порядок слів і наголос у реченні
subtitle: Тема і рема, інверсія для контрасту та природний порядок слів
focus: grammar
pedagogy: PPP
phase: A2.7 [Complex Sentences and Conditionals]
word_target: 2000
objectives:
  - Learner can identify theme (тема, known information) and rheme (рема,
    new information) in Ukrainian sentences and understand that rheme
    typically comes last.
  - Learner can use fronting (moving a word to sentence-initial position) to
    create emphasis or contrast (Книгу я вже прочитав, not *Я вже прочитав
    книгу when emphasizing "the book specifically").
  - Learner can distinguish neutral word order (SVO) from marked word order
    and understand the communicative effect of each.
  - Learner can produce natural Ukrainian sentences where word order conveys
    meaning beyond what grammar alone encodes.
dialogue_situations:
  - setting: 'Roommates dividing chores — clarifying who does what: Хто
      помив посуд? — Посуд помив Тарас. А підлогу? — Підлогу ще ніхто не
      помив. Добре, підлогу помию я.'
    speakers:
      - Оленка
      - Марійка
    motivation: 'Natural fronting for contrast: Посуд помив Тарас (посуд =
      theme, Тарас = rheme). Підлогу помию я (підлогу = theme, я = rheme)'
  - setting: 'Friends discussing a movie — disagreeing about details: Цей
      фільм зняв Сенцов. — Ні, цей фільм зняв не Сенцов, а Лозниця. —
      А от «Номери» — це точно Сенцов зняв.'
    speakers:
      - Друг 1
      - Друг 2
    motivation: 'Contrast through word order shift: neutral (Сенцов зняв
      фільм) vs. contrastive (Цей фільм зняв Сенцов) vs. corrective
      (не Сенцов, а Лозниця)'
content_outline:
  - section: 'Тема і рема: що відоме, що нове? (Theme and Rheme)'
    words: 550
    points:
      - 'Every sentence has two parts: тема (theme, the known/given info,
        what the sentence is about) and рема (rheme, the new info, the
        communicative focus).'
      - 'In neutral Ukrainian word order, тема comes first and рема comes
        last: Тарас (theme) купив нову книгу (rheme). The "news" is at
        the end.'
      - 'Test: answer a question. Хто купив книгу? → Книгу купив Тарас
        (Тарас is the new info = rheme = last). Що купив Тарас? → Тарас
        купив книгу (книгу = rheme = last).'
      - 'This is different from English, where word order is grammatically
        fixed (SVO). Ukrainian uses word order for MEANING — the grammar
        is encoded in case endings, so word order is free to convey emphasis.'
  - section: 'Прямий порядок слів (Neutral Word Order)'
    words: 500
    points:
      - 'Default neutral order: Subject + Predicate + Object (SVO): Студент
        читає книгу. Мама готує вечерю. This is the unmarked, emotionally
        neutral order.'
      - 'Adjective before noun: нова книга, великий будинок (same as English).
        Adverb before verb or after: добре працює / працює добре (both OK,
        but emphasis shifts).'
      - 'Time expressions typically go first or last: Вчора ми ходили в кіно.
        Ми ходили в кіно вчора. (Вчора first = neutral context-setting;
        вчора last = emphasizing "it was yesterday").'
      - 'Practice: identify the neutral word order in sentences and explain
        what the theme and rheme are.'
  - section: 'Інверсія для контрасту (Fronting for Contrast)'
    words: 600
    points:
      - 'Fronting the object: Книгу я вже прочитав (I''ve already read THE
        BOOK — as opposed to something else). The object moves to the front
        to become the theme, and the subject shifts to become part of the
        rheme.'
      - 'Fronting the verb: Прочитав я цю книгу! (emphatic, expressive —
        I DID read this book!). Verb-first order conveys strong assertion
        or emotional emphasis.'
      - 'Corrective contrast: Не Тарас це зробив, а Олег. (Not Taras did
        this, but Oleh.) The corrected element is fronted with не...а.'
      - 'Cleft-like patterns: Це Тарас допоміг мені. (It was Taras who
        helped me.) Це + noun identifies the rheme explicitly.'
      - 'Practice: transform neutral sentences into emphatic ones by changing
        word order, then explain the shift in meaning.'
  - section: 'Порядок слів у реальному мовленні (Word Order in Real Speech)'
    words: 350
    points:
      - 'In conversation, word order constantly shifts based on what is known
        vs. new. Practice with mini-dialogues where each answer reorders
        the sentence to highlight the new information.'
      - 'Common patterns: — Хто це зробив? — Це зробив Тарас. (SVO → OVS).
        — Що ти купив? — Я купив каву. (neutral SVO stays).'
      - 'Reading practice: identifying word order shifts in a short Ukrainian
        text and explaining why the author chose that order.'
vocabulary_hints:
  required:
    - порядок (order)
    - речення (sentence)
    - тема (theme, topic (linguistics))
    - рема (rheme, new information)
    - наголос (stress, emphasis)
    - інверсія (inversion)
    - контраст (contrast)
    - підкреслювати (to emphasize, to underline)
    - початок (beginning)
    - кінець (end)
  recommended:
    - виділяти (to highlight, to single out)
    - означення (attribute, modifier)
    - нейтральний (neutral)
    - емфатичний (emphatic)
    - акцент (accent, emphasis)
activity_hints:
  - type: quiz
    focus: 'Identify the rheme (new information) in each sentence based on
      the question it answers'
    items: 8
  - type: match-up
    focus: Match questions with the correctly word-ordered answers (Хто
      приїхав? → Приїхав Тарас, not Тарас приїхав)
    items: 8
  - type: fill-in
    focus: Reorder words to create the correct emphasis for a given context
      (the book / I / already / read → for emphasis on "the book")
    items: 8
  - type: group-sort
    focus: Sort sentences into neutral word order vs. marked/emphatic word
      order
    items: 8
  - type: error-correction
    focus: 'Fix sentences where word order creates unintended emphasis
      (e.g., answering "What did you buy?" with *Каву купив я instead
      of Я купив каву)'
    items: 6
references:
  - title: Заболотний Grade 8, §10-12
    notes: Порядок слів у реченні, прямий і зворотний порядок
  - title: Авраменко Grade 8, §6-7
    notes: Тема і рема, актуальне членування речення
  - title: 'ULP: Ukrainian Word Order'
    url: https://www.ukrainianlessons.com/word-order/
    notes: How Ukrainian word order differs from English

</plan_content>

## Generated Content

<generated_module_content>
## Вступ та Діалог 1

В українській мові порядок слів називають **вільним** *(free)*. Але це не означає, що слова стоять хаотично. Порядок слів — це важливий інструмент. В англійській мові граматика диктує, де стоїть підмет, а де присудок. В українській мові ми використовуємо **порядок слів** *(word order)*, щоб передати зміст та емоції. Слово, яке стоїть на початку або в кінці речення, має найбільше значення.

Оленка та Марійка — **сусідки по кімнаті** *(roommates)*. Вони ділять домашні обов'язки. Зверніть увагу, як змінюється порядок слів, коли вони говорять про нову інформацію.

> — **Оленка:** Хто помив посуд? *(Who washed the dishes?)*
> — **Марійка:** Посуд помив Тарас. А підлогу? *(Taras washed the dishes. And the floor?)*
> — **Оленка:** Підлогу ще ніхто не помив. Добре, підлогу помию я. *(No one has washed the floor yet. Okay, I will wash the floor.)*

Оленка запитує про посуд. Для Марійки посуд — це вже відома інформація, тобто **тема** *(theme)*. Тому слово «посуд» стоїть на початку речення. А слово «Тарас» — це нова інформація, або **рема** *(rheme)*. Тому це слово стоїть у кінці речення. Так само працює слово «підлога».

## Тема і рема: що відоме, що нове?

Кожне речення має дві частини. Це те, про що ми говоримо, і що повідомляємо. У лінгвістиці їх називають **тема** *(theme)* і **рема** *(rheme)*. Тема — це відома інформація, яку співрозмовник уже знає. Рема — це нова інформація, або **фокус повідомлення** *(focus of the message)*. Українське речення зазвичай рухається від відомого до нового. Ми починаємо зі знайомих фактів і закінчуємо головною новиною.

This creates an important linguistic principle called "end focus". У нейтральному мовленні найважливіша інформація стоїть у кінці речення. Саме там знаходиться рема. Порівняйте два варіанти. Перший: «Тарас купив книгу». Тут фокус падає на слово «книгу». Співрозмовник знає Тараса, але не знає, що він купив. Другий: «Книгу купив Тарас». Тут рема — це слово «Тарас». Співрозмовник знає про покупку книги, але не знає покупця. The word at the very end of the sentence naturally carries the main communicative weight.

You can easily identify the rheme by asking a simple question. Українська відповідь завжди ставить нову інформацію в кінець. Уявіть питання: «Хто купив книгу?». Слово «книга» вже прозвучало, тому це тема. Нова інформація — це людина. Тому правильна відповідь: «Книгу купив Тарас». Тепер уявіть інше питання: «Що купив Тарас?». Тут відома інформація — це Тарас. Тому відповідь буде іншою: «Тарас купив книгу». Слова змінюють позиції залежно від питання.

Why can Ukrainian do this so effortlessly? Відповідь ховається у відмінках. In English, strict word order tells you exactly who is the subject and who is the object. В українській мові граматичну роль показують **закінчення** *(endings)*. Слово «книгу» має закінчення знахідного відмінка **-у**. Це слово завжди буде додатком. Нам не важливо, де воно стоїть. Саме відмінки дозволяють нам вільно переставляти слова.

There is also a psychological reason for this order. Люди інтуїтивно ставлять нові або довгі поняття в кінець речення. Це допомагає співрозмовнику легше сприймати інформацію. Спочатку людина чує знайомі слова, які готують ґрунт. Потім вона отримує свіжий **акцент** *(accent)*. Такий **порядок слів** *(word order)* робить українське мовлення виразним інструментом.

<!-- INJECT_ACTIVITY: quiz-identify-rheme --> [quiz, Identify the rheme (new information) based on the context/question, 8 items]

## Прямий порядок слів

Українська мова має базовий, або **прямий порядок слів** *(direct word order)*. Це нейтральна схема: **підмет** *(subject)*, **присудок** *(predicate)*, **додаток** *(object)*. Ми використовуємо прямий порядок слів для констатації фактів. Він часто звучить у новинах, наукових текстах або офіційних повідомленнях. Наприклад: «Студент читає текст». «Мама готує вечерю». Тут немає жодних емоцій. Це просто інформація. When you want to state a simple fact without emphasizing any specific part, use this SVO structure. It is the safest choice for beginners.

Де стоїть **означення** *(attribute/adjective)*? У нейтральному реченні прикметник завжди стоїть перед іменником. Ми кажемо: «цікава книга», «велике місто», «холодний вітер». Це звичайна характеристика предмета. Але будьте обережні, коли змінюєте порядок. Якщо ви поставите прикметник після іменника, він стане присудком. Порівняйте: «Це велике місто» *(This is a big city)*. Але: «Місто — велике» *(The city IS big)*. У другому випадку ми робимо акцент на розмірі міста. The position of the adjective completely changes the grammatical structure of the sentence.

Тепер поговоримо про **обставини** *(adverbial modifiers)*. Вони показують, як саме відбувається дія. В українській мові прислівник може стояти перед дієсловом або після нього. Обидва варіанти правильні. Ви можете сказати: «Він добре працює» або «Він працює добре». Є невелика різниця. Коли прислівник стоїть у кінці, він має трохи більше ваги. Це знову правило реми. Moving the adverb to the very end of the sentence naturally makes it the focus of your statement.

Слова, які позначають час або місце, дуже рухливі. Їхня позиція залежить від вашої мети. Часто вони стоять на початку речення. Це створює контекст для всієї ситуації. Наприклад: «Вчора я був удома» *(Yesterday I was at home)*. «У Києві йде дощ» *(It is raining in Kyiv)*. Це нейтральний початок розповіді. Але якщо ви поставите час або місце в кінець, вони стануть ремою. «Я був удома вчора» *(I was at home YESTERDAY)*. Це означає, що ви наголошуєте саме на вчорашньому дні, а не сьогоднішньому.

Є один дуже цікавий і специфічний випадок. Це порядок слів із числівниками. Коли ви називаєте точну кількість, числівник стоїть перед іменником. Наприклад: «До центру п’ять кілометрів» *(It is five kilometers to the center)*. Це точний факт. Але якщо ви поміняєте їх місцями, значення зміниться. «До центру кілометрів п’ять» *(It is ABOUT five kilometers to the center)*. Ця **інверсія** *(inversion)* автоматично робить число приблизним. Ukrainian uses this simple word-swap trick instead of adding extra words like "about" or "approximately".

<!-- INJECT_ACTIVITY: match-question-answer --> [match-up, Match questions with the correctly word-ordered answers, 8 items]

<!-- INJECT_ACTIVITY: group-sort-neutral-marked --> [group-sort, Sort sentences into neutral word order vs. marked/emphatic order, 8 items]

## Діалог 2 та Інверсія для контрасту

> — **Друг 1:** Ти дивився кіно вчора? Цей фільм зняв Сенцов.
> — **Друг 2:** Ні, цей фільм зняв не Сенцов, а Лозниця.
> — **Друг 1:** А, зрозумів. А от «Номери» — це точно Сенцов зняв!

У цьому діалозі друзі обговорюють режисерів. Зверніть увагу на їхні слова. Вони використовують **інверсію** *(inversion)*. Це навмисна зміна порядку слів для **контрасту** *(contrast)*.

In Ukrainian, you can freely move the object to the front of the sentence. Ми називаємо це винесенням додатка на **початок** *(beginning)*. Наприклад, ви можете сказати: «Книгу я вже прочитав». Тут ви протиставляєте цю книгу іншим речам. As for the book, I have already read it (maybe I haven't watched the movie yet). Це дуже популярна конструкція. Ви робите книгу головною темою вашої розмови.

Іноді ми ставимо дієслово на найперше місце в реченні. Це інверсія присудка. Наприклад: «Прочитав я цю книгу!». What does this specific order mean? Putting the verb first shows strong emotion, frustration, or absolute certainty. Це показує ваші сильні емоції або логічну завершеність дії. Ви хочете підкреслити, що дія точно відбулася.

Порядок слів також чудово допомагає швидко виправити помилку співрозмовника. Для цього ми використовуємо конструкцію «не..., а...» *(not..., but...)*. If someone assumes you walked in the park, but you actually walked in the forest, you change the word order to highlight the truth. Ви кажете: «Не в парку ми гуляли, а в лісі». You put the corrected information right at the front for maximum emphasis.

Як ще можна зробити сильний **наголос** *(emphasis)* на одному слові? Ми часто використовуємо просту частку «це» *(this/it)*. Порівняйте два варіанти: «Тарас мені допоміг» та «Це Тарас мені допоміг». The second sentence works exactly like a cleft sentence in English: "It was Taras who helped me." Ви чітко показуєте, хто саме виконав цю важливу дію.

Багато студентів дуже бояться самостійно змінювати порядок слів. Вони думають, що будуть звучати дивно, як майстер Йода з кінофільму «Зоряні війни». Але це міф. Речення «Книгу я бачив» — це абсолютно правильна і красива українська мова. У правильному контексті це звучить стовідсотково природно. Не бійтеся ставити слова у новий порядок у **кінець** *(end)* або на початок речення!

<!-- INJECT_ACTIVITY: fill-in-reorder-words-to-create-the-correct-emphasis-for-a-given-context -->

## Порядок слів у реальному мовленні

Уявіть звичайну розмову. Ми постійно передаємо нову інформацію. Як це працює на практиці? Дуже часто рема одного речення стає темою для наступного. Це наче ланцюжок. This chain structure helps speakers track what is already known and what is new. Подивіться на цей короткий діалог:
> — **Максим:** Де ти був сьогодні?
> — **Андрій:** Я був у парку.

У відповіді Андрія слово «парку» — це нова інформація, тобто рема. Воно стоїть у кінці речення. А тепер Максим запитує далі:
> — **Максим:** А в парку ти що робив?

Тепер «парк» — це вже відома інформація. Це тема. Тому Максим ставить ці слова на початок свого питання. А нова інформація (що саме Андрій там робив) буде в кінці. Ця ланцюжкова структура робить розмову дуже логічною.

Коли ми говоримо, ми використовуємо не тільки порядок слів. Ми також використовуємо голос. Це називається **логічний наголос** *(logical stress)*. Ми робимо голос сильнішим на найважливішому слові. Usually, logical stress naturally falls on the rheme at the end of the sentence. But when we use inversion, we combine both tools. Ми змінюємо порядок слів і додаємо інтонацію. Наприклад, ви хочете підкреслити свою довіру до конкретної людини. Ви кажете: «Тобі я вірю». Слово «тобі» стоїть на початку. І ви також виділяєте його голосом. By moving the object to the front and stressing it with your voice, you create a powerful contrast. Цей подвійний **акцент** *(emphasis)* робить ваші емоції дуже зрозумілими. Українці постійно використовують цей прийом у щоденному спілкуванні.

Є ще один дуже важливий **шаблон** *(template)*. Уявіть, що ви розповідаєте історію. Вам потрібно представити нового героя або нову подію. Як ви це зробите? In English, you would use "There is..." or just Subject + Verb ("A teacher entered"). В українській мові ми використовуємо інверсію. Ми ставимо дієслово перед підметом. Ми кажемо: «Увійшов старий вчитель» *(An old teacher entered)*. Чому ми не кажемо «Старий вчитель увійшов»? Тому що поява вчителя — це головна новина. When introducing a brand new subject into the narrative, the subject itself is the rheme, so it goes last. Ви часто почуєте такі фрази: «Прийшла весна» *(Spring came)*, «Почалася злива» *(A downpour started)*, «Настала ніч» *(Night fell)*. Це не просто художній стиль. Це найприродніший спосіб повідомити співрозмовнику про щось нове і раптове. Тепер ви знаєте, як зробити свою розповідь справді українською!

<!-- INJECT_ACTIVITY: error-correction-fix-sentences-where-word-order-creates-unintended-emphasis -->

## Підсумок

Let's review what we have learned today in this module. Порядок слів в українській мові — це дуже потужний інструмент. Це не просто граматична структура. Це спосіб показати ваші емоції, ваші наміри та ваші акценти. Кожен елемент має своє місце, але це місце може змінюватися. When you change the word order, you change the focus of your entire message.

First, you must understand the difference between theme and rheme. Чи розумієте ви різницю між темою та ремою? Тема — це вже відома інформація. Рема — це зовсім нова інформація. Куди зазвичай ставиться нова інформація в нейтральному реченні? In neutral speech, the most important new information always goes to the end. Якщо ви відповідаєте на запитання, ваша головна відповідь має стояти саме в кінці речення.

Second, adjectives and nouns have a strict relationship. Що трапиться, якщо прикметник поставити після іменника? It is no longer just a simple modifier. Він відразу стане присудком. Наприклад, фраза «Холодний вітер» означає просто "a cold wind." Але речення «Вітер холодний» означає "The wind is cold." Це вже повна і самостійна думка.

Third, fronting is your tool for contrast. Для чого виносити об'єкт на початок речення? We do this to create focus or a strong contrast. Коли ви кажете «Каву я вже пив», ви виділяєте саме слово «кава». You show that you drank the coffee, not the tea or juice.

Finally, word order helps with numbers. Як виразити приблизну кількість за допомогою порядку слів? Якщо ви ставите числівник перед іменником, ви називаєте абсолютно точну кількість. Наприклад, «П'ять кілометрів» — це рівно п'ять. Але якщо ви ставите іменник перед числівником, ви говорите про приблизну кількість. Фраза «Кілометрів п'ять» означає "about five kilometers."

Українська мова дає вам велику свободу у спілкуванні. You do not need to speak with a fixed subject-verb-object structure all the time. Ви можете вільно змінювати порядок слів у щоденній розмові. Це допоможе вашій мові звучати природно, емоційно та по-справжньому українською. Уважно слухайте, як розмовляють українці на вулиці чи у фільмах. Звертайте увагу на те, яке слово стоїть першим, а яке — останнім. Не бійтеся експериментувати з інверсією. Читайте українські тексти та аналізуйте логічний наголос. З часом ви відчуєте справжню красу та гнучкість українського синтаксису!
</generated_module_content>

**PIPELINE NOTE — Word count: 2049 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 603 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Андрія — NOT IN VESUM
  ✗ Йода — NOT IN VESUM
  ✗ Сенцов — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тараса — NOT IN VESUM
  ✗ прийом — NOT IN VESUM

All 603 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
