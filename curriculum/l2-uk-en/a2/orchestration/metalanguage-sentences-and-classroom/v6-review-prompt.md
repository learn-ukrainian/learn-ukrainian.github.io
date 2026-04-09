<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 63: Речення і клас (A2, A2.9 [Metalanguage Bridge & Foundation])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-063
level: A2
sequence: 63
slug: metalanguage-sentences-and-classroom
version: '1.1'
title: Речення і клас
subtitle: Синтаксичні терміни, будова слова та мова класу
focus: bridge
pedagogy: Bridge
phase: A2.9 [Metalanguage Bridge & Foundation]
word_target: 2000
objectives:
  - Learner can name and identify sentence members in Ukrainian (підмет, 
    присудок, додаток, означення, обставина) in simple sentences.
  - Learner can identify word anatomy parts using Ukrainian terms (корінь, 
    префікс, суфікс, закінчення) and break words into morphemes.
  - Learner can understand and respond to classroom imperatives in Ukrainian 
    (Прочитайте, Запишіть, Виберіть, Підкресліть, Вставте, Дайте відповідь).
  - Learner can follow a Ukrainian-language grammar exercise format, preparing 
    for B1 immersion-style instruction.
dialogue_situations:
  - situation: "A student asking the teacher how to analyze a sentence — Як визначити
      підмет? Що таке обставина? Teacher explains using simple examples"
    functions: ["asking about grammar terms", "requesting clarification", "understanding
          instructions"]
    key_vocabulary: ["підмет", "присудок", "означення", "обставина"]
  - situation: "Two students working through a Ukrainian textbook exercise together
      — reading instructions in Ukrainian and helping each other with morpheme analysis"
    functions: ["following instructions in Ukrainian", "peer collaboration", "analyzing
          word structure"]
    key_vocabulary: ["корінь", "префікс", "суфікс", "прочитайте", "визначте"]
content_outline:
  - section: 'Члени речення: хто що робить? (Sentence Members: Who Does What?)'
    words: 550
    points:
      - 'Re-labeling with Grade 3-4 textbook method: Ukrainian children learn sentence
        analysis (розбір речення) by asking questions. Підмет (subject) — хто? що?
        — underlined with one line. Присудок (predicate) — що робить? що зробив? —
        underlined with two lines.'
      - 'Другорядні члени речення (secondary sentence members): Додаток (object) —
        кого? що? кому? чим? — answers case questions. Означення (attribute) — який?
        яка? яке? чий? — describes the noun. Обставина (adverbial modifier) — де?
        коли? як? куди? — describes the action.'
      - 'Practice: analyze 5-6 simple sentences, identifying підмет, присудок, and
        other members. Grade 4 textbook format: draw arrows and underline.'
      - 'Simple vs. compound sentence: просте речення (one підмет + присудок) vs.
        складне речення (two or more pairs).'
  - section: 'Будова слова: корінь, префікс, суфікс (Word Anatomy: Root, Prefix, Suffix)'
    words: 500
    points:
      - 'Корінь (root) — the core meaning: ліс → лісок, лісовий, лісник, пролісок.
        All share the root ліс-. Споріднені слова (cognate words) share a root.'
      - 'Префікс (prefix) — before the root, changes meaning: ходити → виходити, заходити,
        приходити, переходити. Each prefix adds a new direction or nuance.'
      - 'Суфікс (suffix) — after the root, changes part of speech or adds meaning:
        ліс → лісок (diminutive), лісовий (adjective), лісник (person). Connect to
        diminutive suffixes from M52.'
      - 'Закінчення (ending) — the grammatical ending that changes by case, gender,
        number: книга, книги, книзі, книгу, книгою. Основа (stem) = everything except
        the закінчення.'
      - 'Practice: break 8-10 words into morphemes using the корінь-префікс-суфікс-закінчення
        framework.'
  - section: 'Мова класу: накази вчителя (Classroom Language: Teacher Instructions)'
    words: 550
    points:
      - 'Essential classroom imperatives the learner will encounter in B1+ Ukrainian-language
        instruction: Прочитайте (Read), Запишіть (Write down), Виберіть (Choose),
        Підкресліть (Underline), Вставте (Insert), Дайте відповідь (Give an answer),
        Знайдіть (Find), Визначте (Determine), Порівняйте (Compare), Доповніть (Complete/supplement).'
      - 'These are formal imperative (ви-form). Connect to nakazovyy sposib from M56.
        Formation: stem + -іть/-йте.'
      - 'Common exercise instructions: Вставте пропущені букви (Insert missing letters).
        Підкресліть підмет і присудок (Underline subject and predicate). Визначте
        відмінок іменника (Determine the case of the noun).'
      - 'Practice: read 5-6 Ukrainian exercise instructions and do the exercise. This
        simulates real Ukrainian classroom work.'
  - section: 'Усе разом: аналізуємо текст (Putting It All Together: Text Analysis)'
    words: 400
    points:
      - 'Integrated exercise: a short Ukrainian text (6-8 sentences). The learner
        identifies parts of speech (частини мови), sentence members (члени речення),
        and breaks selected words into morphemes (будова слова).'
      - 'Reading: a Grade 4 textbook exercise page — the learner works through it
        as a Ukrainian student would, following instructions in Ukrainian.'
      - 'Self-assessment: Can I understand grammar instructions in Ukrainian? Am I
        ready for B1 where more content will be in Ukrainian?'
vocabulary_hints:
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
  recommended:
    - основа (stem)
    - споріднені слова (cognate words)
    - підкресліть (underline — imperative)
    - вставте (insert — imperative)
    - визначте (determine — imperative)
activity_hints:
  - type: match-up
    focus: Match sentence member terms to their question words
    items: 8
  - type: fill-in
    focus: Break words into morphemes (корінь, префікс, суфікс, закінчення)
    items: 8
  - type: quiz
    focus: Read a classroom instruction in Ukrainian and choose what to do
    items: 8
  - type: group-sort
    focus: Sort words into groups by shared корінь (root families)
    items: 8
references:
  - title: Вашуленко Grade 3, Будова слова
    notes: Root, prefix, suffix as taught to Ukrainian 3rd graders
  - title: Большакова Grade 4, Речення. Члени речення
    notes: Sentence analysis method with підмет and присудок identification

</plan_content>

## Generated Content

<generated_module_content>
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
</generated_module_content>

**PIPELINE NOTE — Word count: 3179 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 724 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Олена — NOT IN VESUM
  ✗ еньк — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ книж — NOT IN VESUM
  ✗ іть — NOT IN VESUM

All 724 other words are confirmed to exist in VESUM.

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
