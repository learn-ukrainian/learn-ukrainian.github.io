<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 61: Слова і відмінки (A2, A2.9 [Metalanguage Bridge & Foundation])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-061
level: A2
sequence: 61
slug: metalanguage-words-and-cases
version: '1.1'
title: Слова і відмінки
subtitle: Частини мови, відмінки та граматичні терміни українською
focus: bridge
pedagogy: Bridge
phase: A2.9 [Metalanguage Bridge & Foundation]
word_target: 2000
objectives:
  - Learner can name all major parts of speech in Ukrainian (іменник, 
    прикметник, дієслово, займенник, числівник, прислівник, прийменник, 
    сполучник) and identify them in sentences.
  - Learner can recite all seven Ukrainian case names with their question pairs 
    (Називний — хто? що?, Родовий — кого? чого?, etc.).
  - Learner can use Ukrainian grammatical gender and number terms (чоловічий, 
    жіночий, середній рід; однина, множина).
  - Learner can follow grammar explanations given entirely in Ukrainian 
    metalanguage.
dialogue_situations:
  - situation: "A student asking the teacher to identify the part of speech of a tricky
      word — Це прислівник чи прикметник? А 'мій' — це займенник? Teacher explains
      with examples"
    functions: ["classifying words", "asking about parts of speech", "distinguishing
          categories"]
    key_vocabulary: ["іменник", "прикметник", "займенник", "частина мови"]
  - situation: "A student practicing case identification with a study partner — one
      reads a sentence, the other names the відмінок of each noun using the question
      method"
    functions: ["identifying cases", "applying question method", "peer practice"]
    key_vocabulary: ["називний", "родовий", "давальний", "знахідний", "орудний"]
content_outline:
  - section: 'Частини мови: що це за слово? (Parts of Speech: What Kind of Word Is
      This?)'
    words: 600
    points:
      - 'Re-labeling known concepts: the learner already uses nouns, verbs, adjectives
        — now they learn what Ukrainian teachers call them. Method: Grade 3-4 textbook
        excerpts showing how Ukrainian children learn these terms.'
      - 'Іменник (noun) — назва предмета: хто? що? — мама, стіл, радість. Прикметник
        (adjective) — ознака предмета: який? яка? яке? — великий, гарна, синє. Дієслово
        (verb) — дія предмета: що робити? що зробити? — читати, написати.'
      - 'Займенник (pronoun) — замість іменника: хто? що? — я, ти, він, хтось. Числівник
        (numeral) — кількість або порядок: скільки? який? — п''ять, третій.'
      - 'Прислівник (adverb) — ознака дії: як? де? коли? — швидко, тут, завтра. Прийменник
        (preposition) — зв''язок слів: у, на, з, до. Сполучник (conjunction) — з''єднує
        слова/речення: і, але, що, бо.'
  - section: 'Сім відмінків: питання та назви (Seven Cases: Questions and Names)'
    words: 550
    points:
      - 'The complete case system with Ukrainian names and questions: Називний (Nominative)
        — хто? що? Родовий (Genitive) — кого? чого? Давальний (Dative) — кому? чому?
        Знахідний (Accusative) — кого? що? Орудний (Instrumental) — ким? чим? Місцевий
        (Locative) — на кому? на чому? Кличний (Vocative) — direct address.'
      - 'Mnemonic strategy: Ukrainian schoolchildren learn "Не Роби Дурниць, Знай,
        Орудуй Місцем, Кличний!" — or the learner can create their own.'
      - 'Practice: given a sentence, identify which відмінок each noun is in, using
        the question method (задати питання).'
      - 'Grade 3-4 textbook excerpt: how Ukrainian teachers explain the case system
        to their students, with simplified examples.'
  - section: 'Рід і число: чоловічий, жіночий, середній (Gender and Number)'
    words: 450
    points:
      - 'Three genders: чоловічий рід (masculine), жіночий рід (feminine), середній
        рід (neuter). How to determine gender by ending: consonant → ч.р., -а/-я →
        ж.р., -о/-е → с.р.'
      - 'Two numbers: однина (singular), множина (plural). How textbooks teach this:
        Один — однина. Багато — множина.'
      - 'Combining terms: identify a word fully — іменник, жіночий рід, множина, родовий
        відмінок (e.g., книг = noun, feminine, plural, genitive).'
      - 'Practice: label 10 words from previous modules with their full grammatical
        description in Ukrainian terms.'
  - section: 'Читаємо граматику українською (Reading Grammar in Ukrainian)'
    words: 400
    points:
      - 'Reading exercise: a Grade 4 textbook page explaining a simple grammar rule
        entirely in Ukrainian. Learner answers comprehension questions about the rule.'
      - 'Building confidence: the learner realizes they can already understand Ukrainian
        grammar explanations. This is the bridge to B1, where grammar will increasingly
        be taught in Ukrainian.'
      - 'Quick reference card: all terms introduced in this module, organized as a
        study aid the learner can return to.'
vocabulary_hints:
  required:
    - іменник (noun)
    - прикметник (adjective)
    - дієслово (verb)
    - займенник (pronoun)
    - числівник (numeral)
    - прислівник (adverb)
    - прийменник (preposition)
    - сполучник (conjunction)
    - називний відмінок (nominative case)
    - родовий відмінок (genitive case)
    - рід (gender, grammatical)
    - однина (singular)
  recommended:
    - множина (plural)
    - чоловічий рід (masculine gender)
    - жіночий рід (feminine gender)
    - середній рід (neuter gender)
    - частина мови (part of speech)
activity_hints:
  - type: match-up
    focus: Match Ukrainian grammar terms to their English equivalents
    items: 8
  - type: quiz
    focus: Identify the part of speech of underlined words in Ukrainian 
      sentences
    items: 8
  - type: group-sort
    focus: Sort words into parts of speech (іменник, прикметник, дієслово, etc.)
    items: 8
  - type: fill-in
    focus: Complete case questions (Родовий — ___? ___?)
    items: 8
references:
  - title: Вашуленко Grade 3, Частини мови
    notes: How Ukrainian primary school introduces parts of speech terminology
  - title: Большакова Grade 4, Іменник. Відмінювання іменників
    notes: Case names and questions as taught in Ukrainian schools

</plan_content>

## Generated Content

<generated_module_content>
## Частини мови: що це за слово?

Ви вже багато знаєте і вмієте говорити українською. You already use nouns, verbs, and adjectives every day. Але тепер ми починаємо говорити про саму мову. From now on, you will read and hear grammar instructions in Ukrainian. Щоб розуміти ці правила, нам потрібні спеціальні слова. Це як робота механіка. A mechanic knows how to fix a car, but they also need to know the names of their tools. Наші інструменти — це **частини мови** *(parts of speech)*. У кожної частини мови є своє ім'я і своя робота в реченні.

Уявіть урок української мови. A student is asking the teacher about some tricky words.
> — **Студент:** Скажіть, будь ласка, слово «мій» — це яка частина мови? *(Tell me please, the word "my" — what part of speech is it?)*
> — **Вчитель:** Слово «мій» — це **займенник** *(pronoun)*.
> — **Студент:** Чому воно так називається? *(Why is it called that?)*
> — **Вчитель:** Тому що воно стоїть замість імені. *(Because it stands instead of a name.)* Воно не називає предмет. Воно тільки вказує на нього. *(It only points to it.)*
> — **Студент:** А слово «швидко»? *(And the word "quickly"?)*
> — **Вчитель:** Це **прислівник** *(adverb)*. Воно показує, як саме ми робимо дію. *(It shows exactly how we do an action.)*

Перша і найголовніша частина мови — це **іменник** *(noun)*. Українські школярі вчать, що іменник — це **назва предмета** *(name of an object)*. Слово «іменник» походить від слова «ім'я». Усі іменники відповідають на два головні питання. Якщо це жива людина або тварина, ми завжди питаємо **«хто?»** *(who?)*. Якщо це звичайний неживий предмет, явище природи або ідея, ми питаємо **«що?»** *(what?)*.
Подивіться на ці приклади:
* Хто? — **мама** *(mom)*, **собака** *(dog)*, **студент** *(student)*, **лікар** *(doctor)*.
* Що? — **стіл** *(table)*, **радість** *(joy)*, **місто** *(city)*, **сонце** *(sun)*.
Іменники відіграють дуже важливу роль у реченні. Вони бувають чоловічого, жіночого та середнього роду. Вони також мають однину і множину.

Друга важлива частина мови — це **прикметник** *(adjective)*. Прикметник завжди показує **ознаку предмета** *(characteristic of an object)*. Колір, розмір, вік, характер — усе це прикметники. Ця частина мови ніби «приклеюється» до іменника і детально описує його. Прикметники відповідають на питання «який?», «яка?», «яке?» або «які?». Прикметник — дуже слухняне слово. Він завжди має такий самий рід, число і відмінок, як і його іменник.
Подивіться на узгодження:
* який стіл? — **великий стіл** *(big table)*.
* яка мама? — **гарна мама** *(beautiful mom)*.
* яке небо? — **синє небо** *(blue sky)*.
* які дні? — **теплі дні** *(warm days)*.
Без прикметників наша мова була б дуже бідною.

Третя велика категорія слів — це **дієслово** *(verb)*. Назва цієї частини мови говорить сама за себе. Дієслово означає слово, яке показує дію. Українські підручники пишуть, що дієслово — це **дія предмета** *(action of an object)*. Усі дієслова в початковій формі відповідають на питання «що робити?» або «що зробити?».
Наприклад:
* що робити? — **читати** *(to read)*, **писати** *(to write)*, **бігати** *(to run)*.
* що зробити? — **прочитати** *(to have read)*, **написати** *(to have written)*.
Дієслова — це мотор нашого речення. Вони постійно змінюються. Дієслова змінюють свою форму за особами та за часом. Вони також мають доконаний та недоконаний вид.

<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->

Крім цих трьох гігантів, в українській мові є інші частини мови.
**Займенник** *(pronoun)*. Він працює як заміна для іменника або прикметника. Приклади: **я** *(I)*, **ти** *(you)*, **ми** *(we)*, **цей** *(this)*.
**Числівник** *(numeral)*. Він показує точну кількість або порядок предметів при лічбі. Він відповідає на питання «скільки?» або «який?». Приклади: **один** *(one)*, **другий** *(second)*, **п'ять** *(five)*.
Також є незмінні слова. Вони ніколи не змінюють своїх закінчень.
**Прислівник** *(adverb)*. Він описує дію або іншу ознаку. Він відповідає на питання «як?», «де?», «коли?». Приклади: **тут** *(here)*, **завтра** *(tomorrow)*, **швидко** *(quickly)*.
Є також службові слова, які допомагають будувати речення.
**Прийменник** *(preposition)*. Він стоїть перед іменником. Приклади: **у** *(in)*, **на** *(on)*, **з** *(with)*, **до** *(to)*.
**Сполучник** *(conjunction)*. Він з'єднує слова або частини речення між собою. Приклади: **і** *(and)*, **але** *(but)*, **бо** *(because)*.

<!-- INJECT_ACTIVITY: group-sort-sort-words-into-parts-of-speech-imennyk-prykmetnyk-diieslovo-etc -->

## Сім відмінків: питання та назви

Ми знаємо, що слова в реченні працюють разом. *(We know that words in a sentence work together.)* Щоб показати свою роль, іменники, прикметники та займенники змінюють закінчення. *(To show their role, nouns, adjectives, and pronouns change endings.)* Цей процес називається **відмінювання** *(declension)*. Українська мова має систему відмінків. **Відмінок** *(case)* — це граматичний статус слова в реченні. *(Case is the grammatical status of a word in a sentence.)* Відмінок показує, що саме робить слово. *(The case shows exactly what the word does.)* Воно є головним героєм чи об'єктом дії? *(Is it the main character or the object of the action?)* Це інструмент чи місце? *(Is it an instrument or a place?)* В англійській мові ви використовуєте прийменники або порядок слів. *(In English, you use prepositions or word order.)* В українській мові ми змінюємо закінчення слова. *(In Ukrainian, we change the ending of the word.)* Це дуже важливий механізм. *(This is a very important mechanism.)*

Давайте послухаємо, як студенти тренуються визначати відмінки. *(Let's listen to how students practice identifying cases.)*
> — **Марко:** Наступне речення: «Я бачу кота». *(Next sentence: "I see a cat".)*
> — **Анна:** Добре, шукаємо іменник. Це слово «кота». *(Good, we look for the noun. It is the word "cat".)*
> — **Марко:** Який це відмінок? *(Which case is this?)*
> — **Анна:** Треба поставити питання від дієслова. Бачу кого? — Кота. *(We need to ask a question from the verb. See whom? — A cat.)*
> — **Марко:** Питання «кого?» має **Знахідний відмінок** *(Accusative case)*. *(The question "whom?" has the Accusative case.)*
> — **Анна:** Правильно! А слово «я» — це **Називний відмінок** *(Nominative case)*. *(Correct! And the word "I" is the Nominative case.)*
> — **Марко:** Так, бо це головний герой. Хто? — Я. *(Yes, because it is the main character. Who? — I.)*

В українській мові є сім відмінків. *(There are seven cases in the Ukrainian language.)* Кожен відмінок має назву та спеціальні питання. *(Each case has a name and special questions.)* Ми завжди ставимо два питання: для істот і для неістот. *(We always ask two questions: for animate and inanimate objects.)* Ось повний список: *(Here is the full list:)*
1. **Називний** *(Nominative)* — хто? що? *(who? what?)*
2. **Родовий** *(Genitive)* — кого? чого? *(of whom? of what?)*
3. **Давальний** *(Dative)* — кому? чому? *(to whom? to what?)*
4. **Знахідний** *(Accusative)* — кого? що? *(whom? what?)*
5. **Орудний** *(Instrumental)* — ким? чим? *(by whom? with what?)*
6. **Місцевий** *(Locative)* — на кому? на чому? *(on whom? on what?)*
7. **Кличний** *(Vocative)* — це форма для звертання *(this is the form for address)*. Він не має питань. *(It does not have questions.)*

Ці сім відмінків — база української граматики. *(These seven cases are the base of Ukrainian grammar.)*

Як запам'ятати всі ці назви по порядку? *(How to remember all these names in order?)* Українські школярі мають один секрет. *(Ukrainian schoolchildren have one secret.)* Вони вчать спеціальну фразу: «**Нашого Ромчика Дивує Зебра — Оця Маленька Красуня**» *(Our Romchik is surprised by the zebra — this little beauty)*. Перша літера кожного слова — це перша літера назви відмінка. *(The first letter of each word is the first letter of the case name.)*
* Н — Називний
* Р — Родовий
* Д — Давальний
* З — Знахідний
* О — Орудний
* М — Місцевий
* К — Кличний

Це дуже зручний і веселий метод. *(This is a very convenient and fun method.)* Ви можете придумати власну фразу! *(You can invent your own phrase!)*

Головний секрет відмінків — це метод питань. *(The main secret of cases is the question method.)* Не треба відразу вчити всі закінчення. *(You don't need to learn all endings right away.)* Спочатку треба навчитися **ставити питання** *(to ask a question)*. *(First, you need to learn to ask a question.)* Ми завжди ставимо питання від дієслова до іменника. *(We always ask the question from the verb to the noun.)* Наприклад, у нас є таке речення: «Я даю подарунок братові». *(For example, we have such a sentence: "I give a gift to my brother".)* Як знайти відмінок слова «братові»? *(How to find the case of the word "brother"?)* Ми беремо дієслово «даю» і питаємо: даю кому? — братові. *(We take the verb "give" and ask: give to whom? — to brother.)* Питання «кому?» — це завжди Давальний відмінок. *(The question "to whom?" is always the Dative case.)* Цей метод чудово працює. *(This method works wonderfully.)*

<!-- INJECT_ACTIVITY: fill-in-complete-case-questions-rodovyi -->

Українські підручники для початкової школи дуже просто пояснюють цю тему. *(Ukrainian primary school textbooks explain this topic very simply.)* Наприклад, підручник автора Вашуленка пише цікаву річ. *(For example, Vashulenko's textbook writes an interesting thing.)* Там сказано, що відмінки допомагають словам «дружити» між собою. *(It is said there that cases help words "make friends" with each other.)* Це створює **зв'язок слів у реченні** *(connection of words in a sentence)*. Без відмінків ми мали б просто випадковий список слів. *(Without cases, we would just have a random list of words.)* Відмінки — це клей, який тримає речення разом. *(Cases are the glue that holds the sentence together.)* Тому їх так важливо розуміти. *(That is why it is so important to understand them.)*

## Рід і число: чоловічий, жіночий, середній

В українській мові кожен **іменник** *(noun)* має свій **граматичний рід** *(grammatical gender)*. *(In the Ukrainian language, every noun has its own grammatical gender.)* Ми маємо три роди. *(We have three genders.)* Перший — це **чоловічий рід** *(masculine gender)*, або скорочено **ч.р.** *(First is masculine gender, or abbreviated ч.р.)* Другий — це **жіночий рід** *(feminine gender)*, або **ж.р.** *(Second is feminine gender, or ж.р.)* Третій — це **середній рід** *(neuter gender)*, або **с.р.** *(Third is neuter gender, or с.р.)* Рід іменника — це постійна ознака. *(The gender of a noun is a permanent feature.)* Це означає, що слово не може змінити свій рід. *(This means that a word cannot change its gender.)* Наприклад, слово «стіл» — це завжди чоловічий рід. *(For example, the word "table" is always masculine gender.)* Ми повинні знати рід, щоб правильно використовувати **прикметник** *(adjective)*. *(We must know the gender to correctly use an adjective.)* Без роду ми не знаємо, яке закінчення вибрати. *(Without gender, we don't know which ending to choose.)*

Як дізнатися рід слова? *(How to find out the gender of a word?)* Ми дивимося на останню літеру. *(We look at the last letter.)* Якщо слово закінчується на приголосний звук, це чоловічий рід. *(If a word ends in a consonant sound, this is masculine gender.)* Наприклад, слова «**брат**» *(brother)*, «дім», «парк». *(For example, the words "brother", "house", "park".)* Якщо слово закінчується на «-а» або «-я», це жіночий рід. *(If a word ends in "-a" or "-ya", this is feminine gender.)* Наприклад, слова «**сестра**» *(sister)*, «родина». *(For example, the words "sister", "family".)* Якщо слово закінчується на «-о», «-е», це середній рід. *(If a word ends in "-o", "-e", this is neuter gender.)* Наприклад, слова «**вікно**» *(window)*, «море». *(For example, the words "window", "sea".)* Коли ви шукаєте нове слово у словнику, ви завжди бачите його рід. *(When you look for a new word in a dictionary, you always see its gender.)* Словник пише короткі літери: ч., ж., або с. *(The dictionary writes short letters: ч., ж., or с.)* Це допомагає вам запам'ятати слово правильно. *(This helps you remember the word correctly.)*

Інша важлива категорія — це **число** *(number)*. *(Another important category is number.)* В українській мові є два числа. *(In the Ukrainian language, there are two numbers.)* Перше число — це **однина** *(singular)*. *(The first number is singular.)* Друге число — це **множина** *(plural)*. *(The second number is plural.)* Українські підручники вчать дітей дуже простому правилу. *(Ukrainian textbooks teach children a very simple rule.)* Вони кажуть: «Один — це однина, багато — множина». *(They say: "One is singular, many is plural".)* Коли ми змінюємо число, ми змінюємо закінчення слова. *(When we change the number, we change the ending of the word.)* Наприклад, ми маємо один стіл — це однина. *(For example, we have one table — this is singular.)* Але якщо їх багато, ми кажемо столи — це множина. *(But if there are many of them, we say tables — this is plural.)* Число може змінюватися, на відміну від роду. *(Number can change, unlike gender.)* Ви можете легко зробити з однини множину. *(You can easily make plural from singular.)*

На рівні А2 ми вчимося робити повний аналіз слова. *(At the A2 level, we learn to do a full analysis of a word.)* Як це виглядає на практиці? *(How does this look in practice?)* Уявіть, що у нас є речення: «На столі немає книг». *(Imagine that we have a sentence: "There are no books on the table".)* Ми беремо слово «**книг**» *(books)*. *(We take the word "books".)* Як український вчитель опише це слово? *(How will a Ukrainian teacher describe this word?)* Вчитель скаже: «Книг» — це іменник, жіночий рід, множина, родовий відмінок. *(The teacher will say: "Knyh" is a noun, feminine gender, plural, genitive case.)* Це звучить як код, але це дуже логічно. *(It sounds like a code, but it is very logical.)* Ми визначили частину мови, постійну ознаку і змінні ознаки. *(We determined the part of speech, the permanent feature, and variable features.)* Цей аналіз допомагає вам бачити систему мови. *(This analysis helps you see the system of the language.)* Ви не просто вгадуєте закінчення. *(You are not just guessing the ending.)* Ви точно знаєте, чому слово має таку форму. *(You know exactly why the word has such a form.)* Це ваша головна мета на цьому етапі. *(This is your main goal at this stage.)*

<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-of-underlined-words-in-ukrainian-sentences -->

## Читаємо граматику українською

Тепер ми маємо дуже цікаве і корисне завдання. *(Now we have a very interesting and useful task.)* Ви вже знаєте багато слів і можете читати довгі речення. *(You already know many words and can read long sentences.)* Ви також добре знаєте базові українські граматичні терміни. *(You also know basic Ukrainian grammatical terms well.)* Давайте прочитаємо короткий текст із реального українського підручника. *(Let's read a short text from a real Ukrainian textbook.)* Цей підручник читають діти у четвертому класі на уроках української мови. *(Children in the fourth grade read this textbook in Ukrainian language lessons.)* Текст розповідає про **знахідний відмінок** *(accusative case)*. *(The text tells about the accusative case.)* Ми навмисно не даємо переклад цього граматичного тексту. *(We intentionally do not give a translation of this grammatical text.)* Ваше завдання — спробувати зрозуміти його логіку самостійно! *(Your task is to try to understand its logic yourself!)* Перед читанням подивіться на нові специфічні слова у цій таблиці. *(Before reading, look at the new specific words in this table.)*

| Український термін | English meaning |
| :--- | :--- |
| **істота** | animate noun (living being) |
| **неістота** | inanimate noun |
| **збігатися** | to coincide, to match |
| **об'єкт дії** | object of an action |

Ось текст із шкільного підручника: *(Here is the text from the school textbook:)*

«Іменники в знахідному відмінку відповідають на питання *кого?* або *що?* Питання *кого?* ми ставимо до іменників, які називають істот. Наприклад: я бачу (кого?) друга, маму, вчителя, собаку. Питання *що?* ми ставимо до іменників, які називають неістот. Наприклад: я купив (що?) олівець, стіл, зошит, телефон. Форма знахідного відмінка для неістот часто збігається з формою називного відмінка. А форма знахідного відмінка для істот завжди збігається з формою родового відмінка. Знахідний відмінок показує прямий об'єкт дії.»

Чи ви зрозуміли цей оригінальний текст? *(Did you understand this original text?)* Це абсолютно нормально, якщо ви читали його повільно. *(It is absolutely normal if you read it slowly.)* Читати граматику іноземною мовою завжди складно. *(Reading grammar in a foreign language is always difficult.)* Давайте разом перевіримо ваше розуміння прочитаного матеріалу. *(Let's check your understanding of the read material together.)* Я буду ставити питання українською мовою. *(I will ask questions in the Ukrainian language.)* Спробуйте знайти відповідь у тексті та сказати її вголос. *(Try to find the answer in the text and say it out loud.)*

Про яку частину мови розповідає цей шкільний текст? *(What part of speech does this school text talk about?)* Цей текст розповідає про іменник. *(This text talks about the noun.)*
Про який саме відмінок ідеться у правилі? *(Exactly which case is being discussed in the rule?)* Йдеться про знахідний відмінок. *(The accusative case is being discussed.)*
На які два питання відповідає іменник у знахідному відмінку? *(What two questions does a noun in the accusative case answer?)* Він відповідає на питання *кого?* або *що?* *(It answers the questions whom? or what?)*
Яке питання ми ставимо до назв істот? *(What question do we ask for names of animate beings?)* Ми ставимо питання *кого?* *(We ask the question whom?)*
Яке питання ми ставимо до назв неістот? *(What question do we ask for names of inanimate objects?)* Ми ставимо питання *що?* *(We ask the question what?)*
З яким відмінком збігається форма знахідного відмінка для всіх істот? *(Which case does the accusative form for all animates coincide with?)* Вона збігається з родовим відмінком. *(It coincides with the genitive case.)*
Українські вчителі використовують дуже зрозумілу мову для своїх учнів. *(Ukrainian teachers use very clear language for their students.)*

Ви щойно успішно прочитали справжню сторінку з українського підручника. *(You just successfully read a real page from a Ukrainian textbook.)* Ви самостійно зрозуміли нове граматичне правило без перекладу! *(You independently understood a new grammar rule without translation!)* Це ваш великий і важливий крок уперед. *(This is your big and important step forward.)* Це ваш міст до рівня B1. *(This is your bridge to the B1 level.)* На наступному етапі ви будете читати граматику тільки українською мовою. *(At the next stage, you will read grammar only in the Ukrainian language.)* Ви вже повністю готові до цього нового виклику. *(You are already fully ready for this new challenge.)* Ви знаєте всі необхідні терміни. *(You know all the necessary terms.)*

## Підсумок

Ось ваш короткий граматичний довідник. *(Here is your short grammar reference guide.)* Збережіть цю інформацію для наступних уроків. *(Save this information for the next lessons.)* Ви будете часто використовувати ці терміни. *(You will use these terms often.)*

*   **Частини мови** *(Parts of speech)*:
    *   **іменник** *(noun)* — стіл, радість
    *   **прикметник** *(adjective)* — великий, гарна
    *   **дієслово** *(verb)* — читати, знати
    *   **займенник** *(pronoun)* — я, він, хтось
    *   **числівник** *(numeral)* — п'ять, перший
    *   **прислівник** *(adverb)* — швидко, завтра
    *   **прийменник** *(preposition)* — у, на, біля
    *   **сполучник** *(conjunction)* — і, але, бо

*   **Відмінки** *(Cases)*:
    *   **Н.** (Називний) — хто? що?
    *   **Р.** (Родовий) — кого? чого?
    *   **Д.** (Давальний) — кому? чому?
    *   **Зн.** (Знахідний) — кого? що?
    *   **Ор.** (Орудний) — ким? чим?
    *   **М.** (Місцевий) — на кому? на чому?
    *   **Кл.** (Кличний) — звертання *(direct address)*

*   **Граматичні категорії** *(Grammatical categories)*:
    *   **рід** *(gender)*: чоловічий рід (ч.р.), жіночий рід (ж.р.), середній рід (с.р.)
    *   **число** *(number)*: однина *(singular)*, множина *(plural)*

**Самоперевірка** *(Self-check)*: Чи можу я назвати свою професію та три предмети у своїй кімнаті, використовуючи українські терміни **іменник** та **прикметник**? *(Can I name my own profession and 3 objects in my room using the labels noun and adjective?)* Якщо так, ви чудово попрацювали сьогодні! *(If so, you did a great job today!)*
</generated_module_content>

**PIPELINE NOTE — Word count: 3174 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 639 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Вашуленка — NOT IN VESUM
  ✗ Ромчика — NOT IN VESUM

All 639 other words are confirmed to exist in VESUM.

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
