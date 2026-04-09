<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/metalanguage-sentences-and-classroom.yaml` file for module **63: Речення і клас** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: fill-in-morphemes -->`
- `<!-- INJECT_ACTIVITY: group-sort-roots -->`
- `<!-- INJECT_ACTIVITY: quiz-classroom-instructions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match sentence member terms to their question words
  items: 8
  type: match-up
- focus: Break words into morphemes (корінь, префікс, суфікс, закінчення)
  items: 8
  type: fill-in
- focus: Read a classroom instruction in Ukrainian and choose what to do
  items: 8
  type: quiz
- focus: Sort words into groups by shared корінь (root families)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- основа (stem)
- споріднені слова (cognate words)
- підкресліть (underline — imperative)
- вставте (insert — imperative)
- визначте (determine — imperative)
required:
- речення (sentence)
- підмет (subject)
- присудок (predicate)
- додаток (object)
- означення (attribute)
- обставина (adverbial modifier)
- корінь (root)
- префікс (prefix)
- суфікс (suffix)
- закінчення (ending)
- прочитайте (read — imperative)
- запишіть (write down — imperative)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Члени речення: хто що робить?

Кожне речення в українській мові має свою основу. (Every sentence in the Ukrainian language has its foundation.) У школі діти вивчають, що це **граматична основа** (grammatical foundation). Вона складається з двох головних частин. Це головні **члени речення** (sentence members). Вони показують, про кого або про що йде мова, і що ця людина чи предмет робить у даний момент. (They show who or what is being discussed, and what this person or object is doing at the given moment.) Ця основа — це фундамент, на якому будується весь зміст нашої розмови. (This foundation is the base on which the entire meaning of our conversation is built.) Без граматичної основи речення просто не може існувати як закінчена думка. (Without a grammatical foundation, a sentence simply cannot exist as a complete thought.) Українська граматика вимагає чіткої структури. (Ukrainian grammar requires clear structure.)

Перший головний член речення — це **підмет** (subject). Він завжди відповідає на питання «хто?» (who?) або «що?» (what?). Підмет — це головний герой нашої історії. (The subject is the main character of our story.) Зазвичай це іменник або займенник у називному відмінку. (Usually, this is a noun or pronoun in the nominative case.) У школі на уроках граматики діти підкреслюють підмет однією прямою лінією. (At school in grammar lessons, children underline the subject with one straight line.) Кожен учень знає це просте правило. (Every student knows this simple rule.)
Розглянемо приклади:
«Сонце сходить». (The sun rises.) Що? — сонце. Це підмет, який виконує дію. (This is the subject that performs the action.)
«Вчитель пояснює нове правило». (The teacher explains the new rule.) Хто? — вчитель. Це також наш підмет у цьому реченні. (This is also our subject in this sentence.)

Другий головний член речення — це **присудок** (predicate). Присудок розказує, що саме робить підмет. (The predicate tells exactly what the subject does.) Він відповідає на питання «що робить?», «що зробив?», «що буде робити?» або «який він є?». Присудок — це дія або стан нашого головного героя. (The predicate is the action or state of our main character.) Найчастіше присудок виражений дієсловом. (Most often, the predicate is expressed by a verb.) За шкільним правилом української мови присудок завжди підкреслюють двома прямими лініями. (According to the school rule of the Ukrainian language, the predicate is always underlined with two straight lines.)
Подивимося на приклади:
«Річка дихала». (The river breathed.) Що робила річка? — дихала. Це присудок.
«Вечір є дуже тихий». (The evening is very quiet.) Який є вечір? — тихий. У цьому реченні присудок описує стан. (In this sentence, the predicate describes a state.)

Інші слова в реченні — це **другорядні члени речення** (secondary sentence members). Вони додають важливі деталі до нашої розповіді. (They add important details to our story.) Їх є три основні види.
Перший вид — це **додаток** (object). Він відповідає на питання непрямих відмінків: «кого?», «що?», «кому?», «ким?», «чим?».
Другий вид — це **означення** (attribute). Означення описує предмет і відповідає на питання «який?», «яка?», «яке?», «чиє?».
Третій вид — це **обставина** (adverbial modifier). Обставина показує місце, час, причину або спосіб дії. (The adverbial modifier shows the place, time, reason, or manner of action.) Вона відповідає на питання «де?», «коли?», «як?», «куди?».
Проаналізуємо велике речення:
«Моя подруга читає цікаву книгу ввечері». (My friend reads an interesting book in the evening.)
Хто? — подруга (підмет). Подруга чия? — моя (означення). Що робить подруга? — читає (присудок). Читає що? — книгу (додаток). Книгу яку? — цікаву (означення). Читає коли? — ввечері (обставина). Тепер ви бачите всі члени речення. (Now you see all the sentence members.)

Речення бувають різні за своєю будовою. (Sentences can be different by their structure.) Якщо речення має тільки одну граматичну основу, це **просте речення** (simple sentence). Якщо воно має дві або більше граматичних основ, це **складне речення** (compound sentence).
Також просте речення може бути коротким або довгим. (Also, a simple sentence can be short or long.) Якщо в реченні є тільки підмет і присудок, це непоширене речення. (If a sentence has only a subject and a predicate, it is an unextended sentence.) Наприклад: «Ідуть дощі». (Rains are falling.) Тут є лише основа. (Here is only the foundation.)
Але коли ми додаємо другорядні члени речення, воно стає набагато ширшим. (But when we add secondary sentence members, it becomes much broader.) **Поширене речення** (extended sentence) має багато деталей. Наприклад: «Сьогодні в лісі ідуть теплі дощі». (Today warm rains are falling in the forest.) Тут є обставини часу і місця («сьогодні», «в лісі») та означення («теплі»).

> — **Марко:** Вибачте, пане вчителю. Як визначити підмет у цьому довгому реченні? *(Excuse me, Mr. Teacher. How to determine the subject in this long sentence?)*
> — **Вчитель:** Це не дуже складно. Спочатку постав питання «хто?» або «що?». *(It is not very difficult. First, ask the question "who?" or "what?".)*
> — **Марко:** Я розумію це правило. А далі що мені робити? *(I understand this rule. And then what should I do?)*
> — **Вчитель:** Далі шукай іменник або займенник у називному відмінку. *(Next, look for a noun or pronoun in the nominative case.)*
> — **Марко:** А якщо це слово відповідає на питання «як?»? Це також підмет? *(And if this word answers the question "how?"? Is it also a subject?)*
> — **Вчитель:** Ні, Марку. Слово, яке відповідає на питання «де?», «коли?», або «як?», — це обставина. *(No, Marko. A word that answers the questions "where?", "when?", or "how?" is an adverbial modifier.)*
> — **Марко:** Дуже дякую вам! Тепер я можу правильно підкреслити всі слова. *(Thank you very much! Now I can correctly underline all the words.)*

<!-- INJECT_ACTIVITY: match-up -->


## Будова слова: корінь, префікс, суфікс

Українські слова дуже схожі на дитячий конструктор або пазл. (Ukrainian words are very similar to a children's constructor or a puzzle.) Вони гармонійно складаються з кількох маленьких частин. (They harmoniously consist of several small parts.) Ці важливі будівельні блоки називаються морфемами. (These important building blocks are called morphemes.) Головна та найважливіша частина кожного слова — це **корінь** (root). Корінь завжди має основне лексичне значення. (The root always has the main lexical meaning.) Уявіть собі звичайне слово «ліс» (forest). Ми можемо легко створити нові слова від цього ж кореня. (We can easily create new words from this same root.) Наприклад: невеликий лісок (small forest), зелений лісовий (forest adjective), старий лісник (forester). Усі ці прекрасні слова мають спільний корінь **-ліс-**. (All these beautiful words have the common root -lis-.) Тому вони називаються **споріднені слова** (cognate words). Споріднені слова — це одна велика лінгвістична сім'я. (Cognate words are one big linguistic family.) Вони завжди мають схоже значення і обов'язково спільний корінь. (They always have a similar meaning and obligatorily a common root.)

Друга дуже важлива частина слова — це **префікс** (prefix). Ця коротка морфема завжди стоїть прямо перед коренем. (This short morpheme always stands right before the root.) Він активно створює нові слова і швидко змінює їхнє значення. (It actively creates new words and quickly changes their meaning.) Префікси дуже часто ілюструють напрямок фізичного руху. (Prefixes very often illustrate the direction of physical movement.) Візьмемо для прикладу просте дієслово «ходити» (to walk). Додамо різні цікаві префікси до цього базового кореня. (Let's add various interesting prefixes to this base root.) Якщо ми швидко йдемо всередину кімнати, це **за**ходити (to enter). Якщо ми повільно йдемо назовні, це **ви**ходити (to exit). Якщо ми успішно йдемо до своєї мети, це **при**ходити (to arrive). Якщо ми обережно йдемо через широку вулицю, це **пере**ходити (to cross). Корінь залишається повністю однаковий, але префікси роблять слова абсолютно різними. (The root remains completely the same, but prefixes make the words absolutely different.)

Ще одна надзвичайно корисна частина слова — це **суфікс** (suffix). Ця морфема завжди стоїть одразу після головного кореня. (This morpheme always stands right after the main root.) Суфікси можуть професійно робити дві дуже важливі речі. (Suffixes can professionally do two very important things.) По-перше, вони легко створюють нові самостійні частини мови. (First, they easily create new independent parts of speech.) Наприклад, звичайний іменник «рука» (hand) стає прикметником «ручний» (manual). (For example, the regular noun "hand" becomes the adjective "manual".) Це відбувається саме завдяки маленькому суфіксу **-н-**. (This happens exactly thanks to the small suffix -n-.) По-друге, суфікси чудово додають яскравих емоцій до слова. (Second, suffixes wonderfully add bright emotions to the word.) Ви вже добре знаєте цю тему з попередніх модулів. (You already know this topic well from previous modules.) Вони швидко роблять слова зовсім маленькими або дуже милими. (They quickly make words completely small or very cute.) Слово «рука» може миттєво стати ласкавим словом «рученька» (little hand). Тут активно працює наш улюблений емоційний суфікс **-еньк-**. (Our favorite emotional suffix -enk- actively works here.)

Остання важлива, але дуже змінна частина слова — це **закінчення** (ending). Ця специфічна морфема стоїть у самому кінці нашого слова. (This specific morpheme stands at the very end of our word.) Важливо пам'ятати, що воно ніколи не створює нові слова. (It is important to remember that it never creates new words.) Закінчення лише регулярно змінює форму слова для правильної граматики. (The ending only regularly changes the word form for correct grammar.) Воно чітко показує нам потрібний відмінок, рід або число. (It clearly shows us the needed case, gender, or number.) Подивіться на цей приклад: лежить цікава книга, немає старої книги, читаю нову книгу. Корінь тут завжди **-книг-** (або іноді -книж-). Він абсолютно не змінює своє базове лексичне значення. (It absolutely does not change its base lexical meaning.) А ось закінчення (-а, -и, -у) постійно і динамічно змінюються. (But the endings (-a, -y, -u) change constantly and dynamically.) Частина слова без цього змінного закінчення називається **основа** (stem). Основа слова «книга» — це просто частина «книг». (The stem of the word "knyha" is simply the part "knyg".)

У школі всі українські діти обов'язково роблять **розбір слова за будовою** (word analysis by structure). Вони охайно малюють спеціальні графічні символи прямо над кожним словом. (They neatly draw special graphic symbols right above each word.) Це дуже добре допомагає візуалізувати всі приховані морфеми. (This helps very well to visualize all hidden morphemes.) Головний корінь завжди позначають простою дугою ⁀ зверху. (The main root is завжди marked with a simple arch ⁀ on top.) Змінне закінчення студенти беруть у маленький рівний квадрат □. (Students put the changeable ending in a small even square □.) Передній префікс традиційно позначають прямим кутом ￢. (The front prefix is traditionally marked with a right angle ￢.) А задній суфікс зазвичай позначають гострим «дашком» ∧. (And the back suffix is usually marked with a sharp "hat" ∧.) Завдяки цьому простому аналізу ми чітко бачимо внутрішню структуру. (Thanks to this simple analysis we clearly see the internal structure.) Слова «ліс» та «лісовий» — це зовсім різні частини мови. (The words "forest" and "forest" (adj) are completely different parts of speech.) Але вони мають один спільний корінь і є близькими родичами. (But they have one common root and are close relatives.)

<!-- INJECT_ACTIVITY: fill-in-morphemes -->
<!-- INJECT_ACTIVITY: group-sort-roots -->


## Мова класу: накази вчителя

У школі вчителі щодня використовують спеціальні дієслова. (In school, teachers use special verbs every day.) Це наказовий спосіб, який спонукає учнів до дії. (This is the imperative mood, which prompts students to action.) Ви вже добре знаєте цю граматичну тему. (You already know this grammar topic well.) Але зараз ми детально розберемо саме мову класу. (But now we will analyze exactly the classroom language.) Українські викладачі зазвичай звертаються до студентів на формальне «Ви». (Ukrainian teachers usually address students as formal "You".) Тому всі офіційні накази мають типові закінчення **-іть** або **-йте**. (Therefore all official commands have typical endings -іть or -йте.) Вчитель просто бере основу слова і додає це закінчення. (The teacher simply takes the word stem and adds this ending.) Ось найважливіші дієслова для уроку: **прочитайте** (read) та **запишіть** (write down). (Here are the most important verbs for a lesson: read and write down.) Коли є багато варіантів, вчитель каже: **виберіть** (choose). (When there are many options, the teacher says: choose.) Якщо треба звернути увагу на текст, ви почуєте: **подивіться** (look). (If you need to pay attention to the text, you will hear: look.)

Тепер перейдемо до письмових завдань та вправ. (Now let's move to written tasks and exercises.) У підручниках ви побачите багато нових інструкцій українською мовою. (In textbooks you will see many new instructions in the Ukrainian language.) Дуже часто там пишуть: **вставте** (insert) пропущені букви. (Very often they write there: insert missing letters.) Це означає, що слово неповне, і вам треба додати літеру. (This means that the word is incomplete, and you need to add a letter.) Інше популярне завдання з граматики: **підкресліть** (underline) головні члени. (Another popular grammar task: underline main members.) Ви берете ручку і малюєте лінію під словом. (You take a pen and draw a line under the word.) Згадайте, як ми підкреслюємо підмет однією лінією, а присудок — двома. (Remember how we underline the subject with one line, and the predicate with two.) Іноді автори підручника спеціально роблять помилку в тексті. (Sometimes textbook authors purposefully make an error in the text.) Тоді ви бачите інструкцію: **знайдіть** (find) помилку. (Then you see the instruction: find the error.) Такі завдання чудово тренують вашу увагу до деталей. (Such tasks wonderfully train your attention to details.) Ви вчитеся бачити текст як справжній редактор. (You learn to see the text like a real editor.)

На уроках ми не тільки читаємо, але й багато аналізуємо. (In lessons we not only read, but also analyze a lot.) Для цього існують серйозні аналітичні дієслова. (For this there exist serious analytical verbs.) Найголовніше слово в українській граматиці — це **визначте** (determine). (The most important word in Ukrainian grammar is determine.) Кожна друга вправа просить вас: визначте відмінок. (Every second exercise asks you: determine the case.) Також вчитель може попросити: **порівняйте** (compare) ці два речення. (Also the teacher can ask: compare these two sentences.) Ви дивитеся на структуру і шукаєте різницю. (You look at the structure and look for the difference.) Якщо речення не закінчене, інструкція каже: **доповніть** (complete). (If the sentence is not finished, the instruction says: complete.) Це означає, що ви повинні додати свої власні слова. (This means that you must add your own words.) Наприкінці вправи вчитель завжди ставить запитання. (At the end of the exercise the teacher always asks a question.) Тоді він використовує фразу: **дайте відповідь** (give an answer). (Then he uses the phrase: give an answer.) Ця команда вимагає вашої активної реакції на матеріал. (This command requires your active reaction to the material.)

Для успішного навчання вам потрібна спеціальна лексика. (For successful learning you need special vocabulary.) Ми використовуємо ці слова щодня в аудиторії та онлайн. (We use these words every day in the classroom and online.) Ваш головний інструмент — це **підручник** (textbook). (Your main tool is the textbook.) У ньому є кожна **сторінка** (page), яку ви відкриваєте на уроці. (In it is every page that you open in the lesson.) На сторінках розташована кожна практична **вправа** (exercise). (On the pages is located every practical exercise.) Вчитель може дати вам складне домашнє **завдання** (task). (The teacher can give you a complex homework task.) А якщо ви працюєте в інтернеті, вам надсилають **посилання** (link). (And if you work on the internet, they send you a link.) Ви натискаєте на посилання і бачите нову тему. (You click on the link and see a new topic.) Знати ці слова дуже корисно для спілкування. (Knowing these words is very useful for communication.)

> — **Олена:** Максиме, ти розумієш цю вправу? *(Maksym, do you understand this exercise?)*
> — **Максим:** Так, дивись сюди. Прочитай завдання. *(Yes, look here. Read the task.)*
> — **Олена:** «Вставте пропущені букви». А що далі? *("Insert the missing letters". And what next?)*
> — **Максим:** Тут треба виділити закінчення у кожному слові. *(Here it is necessary to highlight the ending in every word.)*
> — **Олена:** Добре, я вже все написала. *(Good, I already wrote everything.)*
> — **Максим:** Чудово. Порівняймо наші відповіді! *(Excellent. Let's compare our answers!)*
> — **Олена:** У мене в першому реченні закінчення «-у». *(I have the ending "-u" in the first sentence.)*
> — **Максим:** Правильно, у мене теж так. *(Correct, I also have it like that.)*

<!-- INJECT_ACTIVITY: quiz-classroom-instructions -->


## Усе разом: аналізуємо текст

Тепер ми можемо проаналізувати справжній текст. (Now we can analyze a real text.) Уявіть, що ви відкриваєте підручник. (Imagine that you are opening a textbook.) Прочитайте цей короткий текст про школу: (Read this short text about school:)

> Сьогодні школярі писали тест. Вони уважно слухали вчителя. Зранку йшов дощ. У класі було тепло. Дівчинка швидко закінчила завдання. Урок закінчився вчасно.
> *(Today the schoolchildren wrote a test. They listened to the teacher attentively. In the morning it rained. In the classroom it was warm. The girl quickly finished the task. The lesson finished on time.)*

Зробімо міні-аудит цього тексту. (Let's do a mini-audit of this text.) Знайдіть перше речення. (Find the first sentence.) Хто? (Who?) Школярі. (Schoolchildren.) Це наш підмет. (This is our subject.) Що вони робили? (What did they do?) Писали. (Wrote.) Це присудок. (This is the predicate.) Тепер знайдіть третє речення. (Now find the third sentence.) Коли йшов дощ? (When did it rain?) Зранку. (In the morning.) Це обставина. (This is the adverbial modifier.) А тепер подивіться на дієслово «закінчила». (And now look at the verb "finished".) Корінь тут «-кін-». (The root here is "-kin-".) Яка частина слова стоїть перед коренем? (What part of the word stands before the root?) Це префікс «за-». (This is the prefix "za-".)

На рівні B1 ви будете читати правила українською мовою. (At the B1 level you will read rules in the Ukrainian language.) Це називається **зануренням** (immersion). Спробуйте зрозуміти це пояснення без перекладу: (Try to understand this explanation without translation:)

> Ця частина слова завжди стоїть після кореня. Вона допомагає утворювати нові слова. Наприклад, від слова «ліс» ми утворюємо слово «лісок». Ця частина може робити слово пестливим.
> *(This part of the word always stands after the root. It helps to form new words. For example, from the word "forest" we form the word "little forest". This part can make the word affectionate.)*

Про що цей текст? (What is this text about?) Звичайно, він про суфікс. (Of course, it is about the suffix.) Ви вже знаєте ці терміни. (You already know these terms.) Тому ви можете розуміти такі інструкції. (Therefore you can understand such instructions.)

## Підсумок

Час перевірити свої знання. (Time to check your knowledge.) Дайте відповідь на ці запитання: (Give an answer to these questions:)

* Як називається головний член речення, що відповідає на питання «хто? що?» (What is the name of the main sentence member that answers the questions "who? what?") Це підмет. (This is the subject.)
* Як називається частина слова, що стоїть перед коренем? (What is the name of the part of the word that stands before the root?) Це префікс. (This is the prefix.)
* Що означає команда «Підкресліть»? (What does the command "Underline" mean?) Вона означає: намалюйте лінію під словом. (It means: draw a line under the word.)
* Яка різниця між простим і складним реченням? (What is the difference between a simple and a complex sentence?) Просте речення має одну граматичну основу. (A simple sentence has one grammatical foundation.) Складне речення має дві або більше. (A complex sentence has two or more.)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: metalanguage-sentences-and-classroom
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

**Level: A2 (Module 63/60) — ELEMENTARY**

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
