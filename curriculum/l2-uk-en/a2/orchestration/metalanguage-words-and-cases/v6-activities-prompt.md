<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/metalanguage-words-and-cases.yaml` file for module **61: Слова і відмінки** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-etc-to-english-equivalents -->`
- `<!-- INJECT_ACTIVITY: group-sort-sort-a-list-of-24-words-into-five-buckets -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-the-case-name-and-its-question-pair-e-g -->`
- `<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-and-case-of-underlined-words-in-simple-sentences -->`
- `<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match Ukrainian grammar terms to their English equivalents
  items: 8
  type: match-up
- focus: Identify the part of speech of underlined words in Ukrainian sentences
  items: 8
  type: quiz
- focus: Sort words into parts of speech (іменник, прикметник, дієслово, etc.)
  items: 8
  type: group-sort
- focus: Complete case questions (Родовий — ___? ___?)
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- множина (plural)
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- частина мови (part of speech)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
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
Іменники мають дуже важливу роль у реченні. Вони бувають чоловічого, жіночого та середнього роду. Вони також мають однину і множину.

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

<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-etc-to-english-equivalents -->

Крім цих трьох гігантів, в українській мові є інші частини мови.
**Займенник** *(pronoun)*. Він працює як заміна для іменника або прикметника. Приклади: **я** *(I)*, **ти** *(you)*, **ми** *(we)*, **цей** *(this)*.
**Числівник** *(numeral)*. Він показує точну кількість або порядок предметів при лічбі. Він відповідає на питання «скільки?» або «який?». Приклади: **один** *(one)*, **другий** *(second)*, **п'ять** *(five)*.
Також є незмінні слова. Вони ніколи не змінюють своїх закінчень.
**Прислівник** *(adverb)*. Він описує дію або іншу ознаку. Він відповідає на питання «як?», «де?», «коли?». Приклади: **тут** *(here)*, **завтра** *(tomorrow)*, **швидко** *(quickly)*.
Є також службові слова, які допомагають будувати речення.
**Прийменник** *(preposition)*. Він стоїть перед іменником. Приклади: **у** *(in)*, **на** *(on)*, **з** *(with)*, **до** *(to)*.
**Сполучник** *(conjunction)*. Він з'єднує слова або частини речення між собою. Приклади: **і** *(and)*, **але** *(but)*, **бо** *(because)*.

<!-- INJECT_ACTIVITY: group-sort-sort-a-list-of-24-words-into-five-buckets -->


## Сім відмінків: питання та назви

Ми знаємо, що слова в реченні працюють разом. *(We know that words in a sentence work together.)* Щоб показати свою роль, іменники, прикметники та займенники змінюють закінчення. *(To show their role, nouns, adjectives, and pronouns change endings.)* Цей процес називається **відмінювання** *(declension)*. Українська мова має систему відмінків. **Відмінок** *(case)* — це граматичний статус слова в реченні. *(Case is the grammatical status of a word in a sentence.)* Відмінок показує, що саме робить слово. *(The case shows exactly what the word does.)* Воно є головним героєм чи об'єктом дії? *(Is it the main character or the object of the action?)* Це інструмент чи місце? *(Is it an instrument or a place?)* В англійській мові ви використовуєте прийменники або порядок слів. *(In English, you use prepositions or word order.)* В українській мові ми змінюємо закінчення слова. *(In Ukrainian, we change the ending of the word.)* Це дуже важливий механізм. *(This is a very important mechanism.)*

Давайте послухаємо, як студенти тренуються визначати відмінки. *(Let's listen to how students practice identifying cases.)*
> — **Марко:** Наступне речення: «Я бачу кота». *(Next sentence: "I see a cat".)*
> — **Анна:** Добре, шукаємо іменник. Це слово «кота». *(Good, we look for the noun. It is the word "cat".)*
> — **Марко:** Який це відмінок? *(Which case is this?)*
> — **Анна:** Треба задати питання від дієслова. Бачу кого? — Кота. *(We need to ask a question from the verb. See whom? — A cat.)*
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

Головний секрет відмінків — це метод питань. *(The main secret of cases is the question method.)* Не треба відразу вчити всі закінчення. *(You don't need to learn all endings right away.)* Спочатку треба навчитися **задати питання** *(to ask a question)*. *(First, you need to learn to ask a question.)* Ми завжди задаємо питання від дієслова до іменника. *(We always ask the question from the verb to the noun.)* Наприклад, у нас є таке речення: «Я даю подарунок братові». *(For example, we have such a sentence: "I give a gift to my brother".)* Як знайти відмінок слова «братові»? *(How to find the case of the word "brother"?)* Ми беремо дієслово «даю» і питаємо: даю кому? — братові. *(We take the verb "give" and ask: give to whom? — to brother.)* Питання «кому?» — це завжди Давальний відмінок. *(The question "to whom?" is always the Dative case.)* Цей метод чудово працює. *(This method works wonderfully.)*

<!-- INJECT_ACTIVITY: fill-in-complete-the-case-name-and-its-question-pair-e-g -->

Українські підручники для початкової школи дуже просто пояснюють цю тему. *(Ukrainian primary school textbooks explain this topic very simply.)* Наприклад, підручник автора Вашуленка пише цікаву річ. *(For example, Vashulenko's textbook writes an interesting thing.)* Там сказано, що відмінки допомагають словам «дружити» між собою. *(It is said there that cases help words "make friends" with each other.)* Це створює **зв'язок слів у реченні** *(connection of words in a sentence)*. Без відмінків ми мали б просто випадковий список слів. *(Without cases, we would just have a random list of words.)* Відмінки — це клей, який тримає речення разом. *(Cases are the glue that holds the sentence together.)* Тому їх так важливо розуміти. *(That is why it is so important to understand them.)*


## Рід і число: чоловічий, жіночий, середній

В українській мові кожен **іменник** *(noun)* має свій **граматичний рід** *(grammatical gender)*. *(In the Ukrainian language, every noun has its own grammatical gender.)* Ми маємо три роди. *(We have three genders.)* Перший — це **чоловічий рід** *(masculine gender)*, або скорочено **ч.р.** *(First is masculine gender, or abbreviated ч.р.)* Другий — це **жіночий рід** *(feminine gender)*, або **ж.р.** *(Second is feminine gender, or ж.р.)* Третій — це **середній рід** *(neuter gender)*, або **с.р.** *(Third is neuter gender, or с.р.)* Рід іменника — це постійна ознака. *(The gender of a noun is a permanent feature.)* Це означає, що слово не може змінити свій рід. *(This means that a word cannot change its gender.)* Наприклад, слово «стіл» — це завжди чоловічий рід. *(For example, the word "table" is always masculine gender.)* Ми повинні знати рід, щоб правильно використовувати **прикметник** *(adjective)*. *(We must know the gender to correctly use an adjective.)* Без роду ми не знаємо, яке закінчення вибрати. *(Without gender, we don't know which ending to choose.)*

Як дізнатися рід слова? *(How to find out the gender of a word?)* Ми дивимося на останню літеру. *(We look at the last letter.)* Якщо слово закінчується на приголосний звук, це чоловічий рід. *(If a word ends in a consonant sound, this is masculine gender.)* Наприклад, слова «**брат**» *(brother)*, «дім», «парк». *(For example, the words "brother", "house", "park".)* Якщо слово закінчується на «-а» або «-я», це жіночий рід. *(If a word ends in "-a" or "-ya", this is feminine gender.)* Наприклад, слова «**сестра**» *(sister)*, «родина». *(For example, the words "sister", "family".)* Якщо слово закінчується на «-о», «-е», це середній рід. *(If a word ends in "-o", "-e", this is neuter gender.)* Наприклад, слова «**вікно**» *(window)*, «море». *(For example, the words "window", "sea".)* Коли ви шукаєте нове слово у словнику, ви завжди бачите його рід. *(When you look for a new word in a dictionary, you always see its gender.)* Словник пише короткі літери: ч., ж., або с. *(The dictionary writes short letters: ч., ж., or с.)* Це допомагає вам запам'ятати слово правильно. *(This helps you remember the word correctly.)*

Інша важлива категорія — це **число** *(number)*. *(Another important category is number.)* В українській мові є два числа. *(In the Ukrainian language, there are two numbers.)* Перше число — це **однина** *(singular)*. *(The first number is singular.)* Друге число — це **множина** *(plural)*. *(The second number is plural.)* Українські підручники вчать дітей дуже простому правилу. *(Ukrainian textbooks teach children a very simple rule.)* Вони кажуть: «Один — це однина, багато — множина». *(They say: "One is singular, many is plural".)* Коли ми змінюємо число, ми змінюємо закінчення слова. *(When we change the number, we change the ending of the word.)* Наприклад, ми маємо один стіл — це однина. *(For example, we have one table — this is singular.)* Але якщо їх багато, ми кажемо столи — це множина. *(But if there are many of them, we say tables — this is plural.)* Число може змінюватися, на відміну від роду. *(Number can change, unlike gender.)* Ви можете легко зробити з однини множину. *(You can easily make plural from singular.)*

На рівні А2 ми вчимося робити повний аналіз слова. *(At the A2 level, we learn to do a full analysis of a word.)* Як це виглядає на практиці? *(How does this look in practice?)* Уявіть, що у нас є речення: «На столі немає книг». *(Imagine that we have a sentence: "There are no books on the table".)* Ми беремо слово «**книг**» *(books)*. *(We take the word "books".)* Як український вчитель опише це слово? *(How will a Ukrainian teacher describe this word?)* Вчитель скаже: «Книг» — це іменник, жіночий рід, множина, родовий відмінок. *(The teacher will say: "Knyh" is a noun, feminine gender, plural, genitive case.)* Це звучить як код, але це дуже логічно. *(It sounds like a code, but it is very logical.)* Ми визначили частину мови, постійну ознаку і змінні ознаки. *(We determined the part of speech, the permanent feature, and variable features.)* Цей аналіз допомагає вам бачити систему мови. *(This analysis helps you see the system of the language.)* Ви не просто вгадуєте закінчення. *(You are not just guessing the ending.)* Ви точно знаєте, чому слово має таку форму. *(You know exactly why the word has such a form.)* Це ваша головна мета на цьому етапі. *(This is your main goal at this stage.)*

<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-and-case-of-underlined-words-in-simple-sentences -->


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
Про який саме відмінок іде мова у правилі? *(Exactly which case is being discussed in the rule?)* Мова йде про знахідний відмінок. *(The accusative case is being discussed.)*
На які два питання відповідає іменник у знахідному відмінку? *(What two questions does a noun in the accusative case answer?)* Він відповідає на питання *кого?* або *що?* *(It answers the questions whom? or what?)*
Яке питання ми ставимо до назв істот? *(What question do we ask for names of animate beings?)* Ми ставимо питання *кого?* *(We ask the question whom?)*
Яке питання ми ставимо до назв неістот? *(What question do we ask for names of inanimate objects?)* Ми ставимо питання *що?* *(We ask the question what?)*
З яким відмінком збігається форма знахідного відмінка для всіх істот? *(Which case does the accusative form for all animates coincide with?)* Вона збігається з родовим відмінком. *(It coincides with the genitive case.)*
Українські вчителі використовують дуже зрозумілу мову для своїх учнів. *(Ukrainian teachers use very clear language for their students.)*

Ви щойно успішно прочитали справжню сторінку з українського підручника. *(You just successfully read a real page from a Ukrainian textbook.)* Ви самостійно зрозуміли нове граматичне правило без перекладу! *(You independently understood a new grammar rule without translation!)* Це ваш великий і важливий крок уперед. *(This is your big and important step forward.)* Це ваш міст до рівня B1. *(This is your bridge to the B1 level.)* На наступному етапі ви будете читати граматику тільки українською мовою. *(At the next stage, you will read grammar only in the Ukrainian language.)* Ви вже повністю готові до цього нового виклику. *(You are already fully ready for this new challenge.)* Ви знаєте всі необхідні терміни. *(You know all the necessary terms.)*

<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->


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

**Самоперевірка** *(Self-check)*: Чи можу я назвати свою професію та три предмети у моїй кімнаті, використовуючи українські терміни **іменник** та **прикметник**? *(Can I name my own profession and 3 objects in my room using the labels noun and adjective?)* Якщо так, ви чудово попрацювали сьогодні! *(If so, you did a great job today!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: metalanguage-words-and-cases
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

**Level: A2 (Module 61/60) — ELEMENTARY**

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

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
