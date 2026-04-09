<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/education-and-work.yaml` file for module **52: Навчання і робота** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-complex-education -->`
- `<!-- INJECT_ACTIVITY: match-up-education-scenarios -->`
- `<!-- INJECT_ACTIVITY: quiz-complex-sentence-types -->`
- `<!-- INJECT_ACTIVITY: true-false-structure-culture -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences about education and work using тому що, щоб, який, якщо
  items: 8
  type: fill-in
- focus: Choose the correct complex sentence type for work/education scenarios
  items: 8
  type: quiz
- focus: Match education/career situations to appropriate responses using complex
    sentences
  items: 8
  type: match-up
- focus: Judge whether statements about Ukrainian education and work culture use correct
    complex sentence structures
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- факультет (faculty, department)
- зарплата (salary)
- співбесіда (job interview)
- керівник (manager, supervisor)
- магістратура (master's program)
required:
- освіта (education)
- навчання (studying, learning)
- університет (university)
- спеціальність (specialty, major)
- професія (profession)
- працювати (to work)
- робота (work, job)
- досвід (experience)
- іспит (exam)
- диплом (diploma, degree)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Про освіту: школа та університет

Привіт! Сьогодні ми говоримо про дуже важливу тему. Це **освіта** *(education)*. Наш шлях починається, коли ми йдемо до школи. В українській мові ми використовуємо дієслова **закінчувати** *(to be finishing)* та **закінчити** *(to finish)*. Наприклад: «Я закінчив **школу** *(school)* у дві тисячі п'ятнадцятому році». Або: «Моя сестра зараз закінчує дев'ятий клас». Що ми робимо далі? Ми хочемо **вступати** *(to be entering)* або **вступити** *(to enter)* до нового закладу. Пам'ятайте важливе граматичне правило. Після прийменника «до» ми завжди використовуємо родовий відмінок. Ми кажемо: вступити до **університету** *(university)*, вступити до **ліцею** *(lyceum)*, або вступити до **коледжу** *(college)*. Це дуже природна конструкція. Якщо ви знаєте недоконаний і доконаний вид, ви можете точно описати свій досвід. «Вона вступала до університету два роки, і нарешті вступила». Цей процес вимагає багато сил та часу.

Чому ми вибираємо певну **професію** *(profession)*? Щоб пояснити причину, ми використовуємо сполучник «тому що» *(because)*. Це робить наші речення складними та цікавими. Наприклад: «Я вступив на юридичний **факультет** *(faculty/department)*, тому що хочу бути **адвокатом** *(lawyer)*». В українській мові є дві важливі фрази про навчання. Якщо ми говоримо про майбутню професію, ми кажемо «вчитися на» плюс знахідний відмінок. Наприклад: «Мій брат вчиться на **програміста** *(programmer)*». Або: «Вона вчиться на лікарку». Але якщо ми говоримо про конкретний предмет, ми використовуємо дієслово «вивчати» плюс знахідний відмінок без прийменника. Наприклад: «Я вивчаю **історію** *(history)*», або «Ми вивчаємо вищу математику». Не плутайте ці конструкції! Вони обидві дуже корисні, коли ви говорите про свій студентський досвід. Ви можете сказати: «Я вчуся на інженера, тому що люблю вивчати фізику».

Коли ми розповідаємо про освіту, ми часто описуємо різні місця та предмети. Для цього нам потрібні слова «який» *(which)* та «де» *(where)*. Вони допомагають з'єднати дві прості ідеї в одне гарне складне речення. Подивіться на цей приклад: «**Предмет** *(subject)*, який мені подобався найбільше — це література». Слово «який» змінюється за родами, числами та відмінками. Якщо слово жіночого роду, ми кажемо «яка». Наприклад: «Спеціальність, яка мені дуже подобається, вимагає багато читати». А як сказати про місце? Ми використовуємо слово «де». Наприклад: «Університет, де я навчаюся, знаходиться в самому центрі міста». Або: «Школа, де він працює вчителем, дуже велика і сучасна». Ці слова роблять вашу українську мову багатою та природною. Ви можете легко описати свій улюблений предмет або свій рідний навчальний заклад.

Кожна дія в нашому житті має мету. Чому ми читаємо товсті книжки? Чому ми щодня слухаємо подкасти? Щоб відповісти на ці питання, ми використовуємо слово «щоб» *(in order to)*. Конструкція дуже проста: ми ставимо дієслово, потім кому, потім «щоб», а потім інфінітив. Це ідеальний спосіб говорити про ваші цілі та амбіції. Наприклад: «Я багато вчуся, щоб отримати **диплом** *(diploma/degree)*». Інший гарний приклад: «Він поїхав до Києва, щоб вступити до престижної магістратури». Або: «Я вивчаю українську мову, щоб жити і працювати в Україні». Зверніть увагу, що перед словом «щоб» ми завжди обов'язково ставимо кому. Ця маленька конструкція насправді дуже могутня. Вона показує вашу внутрішню мотивацію і ваші серйозні плани на майбутнє. Спробуйте подумати: що ви робите сьогодні, щоб мати успішне завтра?

Давайте детальніше подивимося на рівні вищої освіти в сучасній Україні. Спочатку студенти чотири роки вчаться і закінчують **бакалаврат** *(bachelor's program)*. Це базова вища освіта. Після цього можна вступити у **магістратуру** *(master's program)* на півтора або два роки. Для тих, хто хоче серйозно займатися наукою, існує **аспірантура** *(postgraduate/PhD program)*. Щоб перейти на новий академічний рівень, треба мати гарні знання. Студенти повинні проходити через складний **іспит** *(exam)*. Тут є дуже важлива пара дієслів: «складати» та «скласти». Дієслово «складати» *(to be taking an exam)* — це тривалий процес. Дієслово «скласти» *(to pass an exam)* — це успішний фінальний результат. Деякі люди кажуть «здавати екзамен», але це русизм. Українською правильно казати «складати іспит». Наприклад: «Я довго складав іспит з математики і нарешті склав його на відмінно». Це завжди дуже радісний момент для кожного студента.

Прочитайте цей короткий діалог. Студент прийшов на важливу консультацію. Він детально пояснює свій академічний вибір.
> — **Консультант:** Добрий день! Розкажіть, яку **спеціальність** *(specialty/major)* ви врешті-решт обрали?
> — **Студент:** Добрий день! Я довго думав і обрав **філологію** *(philology)*.
> — **Консультант:** Дуже цікаво. А чому саме цю гуманітарну сферу?
> — **Студент:** Я активно вивчаю іноземні мови, тому що хочу бути професійним перекладачем.
> — **Консультант:** Чудово! А який предмет вам зараз подобається найбільше?
> — **Студент:** Предмет, який я просто обожнюю — це сучасна європейська література.
> — **Консультант:** Які у вас амбітні плани після завершення бакалаврату?
> — **Студент:** Я хочу багато читати та писати, щоб успішно скласти іспит у магістратуру.
> — **Консультант:** Університет, де ви зараз вчитеся, має дуже гарну магістерську програму.
> — **Студент:** Так, я це добре знаю. Але я також серйозно думаю про **економіку** *(economics)*.
> — **Консультант:** Якщо ви дійсно хочете вивчати економіку, вам потрібна сильна математика.
> — **Студент:** Я чудово це розумію. Я буду багато вчитися, щоб мати різні варіанти.

<!-- INJECT_ACTIVITY: fill-in-complex-education -->
<!-- INJECT_ACTIVITY: match-up-education-scenarios -->


## Про роботу: ким ви працюєте?

Коли ми знайомимося з новими людьми, ми часто говоримо про кар'єру. В українській мові, щоб запитати про чиюсь професію, ми кажемо: «Ким ви працюєте?». Notice the Instrumental case. When we answer, we also use the Instrumental case. «Я працюю **вчителем** *(as a teacher)*». «Вона працює **менеджером** *(as a manager)*». «Він працює **інженером** *(as an engineer)*». It is important to remember the difference between two words. **Робота** *(work, job)* is a noun. **Працювати** *(to work)* is a verb. We say: «Це моя нова робота». But we say: «Я дуже люблю працювати». When we talk about the place of work, we use the Locative case. We say: «Я працюю в **офісі** *(in an office)*». We also say: «Вона працює на **фірмі** *(at a firm)*». Remember these simple rules to speak correctly.

Now let's add more details about our work. We use the words «який», «яка», «яке» or «які» *(which/who)*. They help us describe our company or colleagues. These words must agree in gender and number with the noun. **Компанія** *(company)* is feminine. So we use «яка». «Я працюю в компанії, яка виробляє меблі». Ви також можете сказати: «Це фірма, яка швидко росте». **Проєкт** *(project)* is masculine. We use «який». «Це новий проєкт, який дуже важливий для нас». We also use these words to talk about people at work. **Колега** *(colleague)* can be masculine or feminine. «Моя колега, яка сидить поруч, допомагає мені». «Мій колега, який добре знає англійську, перекладає цей текст». This grammar makes your professional story much more interesting. You can explain exactly what your team does.

Мотивація дуже важлива для кожної людини. Why do we choose our professions? To explain the reason, we use «тому що» *(because)*. «Я люблю свою роботу, тому що вона цікава». «Він став лікарем, тому що хоче допомагати людям». But every job has some difficulties. To show contrast, we use the word **хоча** *(although/even though)*. This word helps us balance the good and bad sides. «Хоча **зарплата** *(salary)* невелика, наш колектив дуже дружній». «Хоча я працюю багато, я маю вільний час у вихідні». «Хоча мій офіс далеко, я люблю туди їздити». Notice that we always put a comma before «тому що». We also put a comma between the two parts of the sentence with «хоча». These complex sentences show your high level of Ukrainian.

Кожен офіс має свої власні традиції та правила. Every workplace has rules and routines. To talk about conditions, we use the construction «якщо..., то...» *(if..., then...)*. This is a real conditional. We use it for normal, everyday situations. «Якщо я закінчую проєкт вчасно, то отримую **премію** *(bonus)*». «Якщо є багато роботи, то я залишаюся в офісі довше». You can also skip the word «то». The sentence is still correct and natural. «Якщо я маю питання, я питаю свого колегу». «Якщо мій комп'ютер не працює, я дзвоню в технічну підтримку». This construction is very useful for explaining your daily professional life. It shows cause and effect clearly. Practice using it when you describe your typical working day or your office rules.

Let's look at some important vocabulary for the workplace. Знати цю лексику дуже корисно для вашого резюме. Your official role is your **посада** *(position)*. Your working hours are your **графік** *(schedule)*. For example: «У мене дуже зручний графік роботи». Your boss or manager is your **керівник** *(manager/supervisor)*. «Мій керівник завжди допомагає нашій команді». When you want a new job, you need to go to a **співбесіда** *(job interview)*. We have two important verbs for career changes. **Шукати роботу** *(to look for a job)* is the process of finding employment. «Мій брат зараз шукає роботу в IT-сфері». **Змінювати роботу** *(to change jobs)* means leaving one job for another. «Вона вирішила змінити роботу, щоб мати кращу посаду». These words will help you discuss your career path.

Let's see how professionals use these words in real life. Зверніть увагу на складні речення в їхній розмові. Read this dialogue. Two people meet at a social event and discuss their careers.

> — **Анна:** Привіт! Ми ще не знайомі. Ким ви працюєте?
> — **Віктор:** Добрий день! Я працюю архітектором на будівельній фірмі. А ви?
> — **Анна:** Я працюю менеджером у компанії, яка продає техніку.
> — **Віктор:** Це цікаво! Вам подобається ваша посада?
> — **Анна:** Так, я люблю свою роботу, тому що вона динамічна. Хоча графік дуже складний.
> — **Віктор:** Я вас чудово розумію. Якщо у нас новий проєкт, я теж працюю до ночі.
> — **Анна:** А де знаходиться офіс, де ви працюєте?
> — **Віктор:** У центрі міста. Мій керівник, який керує нашим відділом, сидить поруч зі мною.
> — **Анна:** Чудово! Якщо ви любите свою роботу, то це найголовніше.

<!-- INJECT_ACTIVITY: quiz-complex-sentence-types -->


## Плани на майбутнє

Let's talk about our plans for the future. Ми часто думаємо про нашу кар'єру та освіту. Для цього ми використовуємо конструкцію «якщо..., то...». Це допомагає нам показати майбутній результат наших дій. We use it to talk about real conditions and their future results. «Якщо я **отримаю** *(will receive)* диплом, то знайду гарну роботу». «Якщо я вивчу англійську мову, то зможу працювати в міжнародній компанії». «Якщо він складе іспит, то вступить до магістратури». Notice how the condition comes first. Умова завжди стоїть на першому місці в реченні. Результат показує наші логічні очікування від ситуації. «Якщо ми закінчимо університет з відзнакою, то матимемо більше шансів». «Якщо я знайду вільний час, то піду на курси програмування». Ця граматика дуже важлива для успішної співбесіди. Менеджери завжди хочуть чути про ваші кар'єрні плани. Вони часто запитують про ваш **розвиток** *(development)* та цілі. «Якщо ви отримаєте цю посаду, що ви будете робити?». «Якщо я стану менеджером, то зроблю нашу роботу ефективнішою». Планувати своє майбутнє дуже корисно. 

We can also use this structure to give good advice. У цьому випадку ми використовуємо наказовий спосіб дієслів. «Якщо хочеш стати директором, треба дуже багато працювати». «Якщо тобі не подобається твоя **спеціальність** *(specialty)*, зміни її зараз». «Якщо ви шукаєте нову роботу, напишіть гарне резюме». It is a very direct and helpful way to speak. Українці часто дають такі щирі поради друзям або колегам. «Якщо ти втомився від проєктів, візьми коротку відпустку». «Якщо компанія не платить премію, активно шукай іншу роботу». «Якщо вам потрібен новий досвід, знайдіть хороше стажування». Це звучить дуже природно в розмові. We do not always need the word «то» when giving advice. «Якщо хочеш змінити професію, просто почни інтенсивно вчитися». «Якщо ти любиш дітей, іди працювати у звичайну школу». Пам'ятайте, що правильний вибір професії — це важливий крок. Якщо ви маєте сумніви щодо кар'єри, запитайте поради у професіоналів. Якщо ви готові до змін у житті, дійте сьогодні.

Sometimes our career plans have difficulties or unexpected exceptions. У таких складних ситуаціях ми використовуємо слово «хоча». «Хоча я ще навчаюся на четвертому курсі, я вже маю **досвід** *(experience)* роботи». Багато амбітних студентів в Україні починають працювати дуже рано. Вони часто шукають роботу на **частковий робочий день** *(part-time)*. Це допомагає швидко отримати практику та перші власні гроші. «Хоча він працює лише на частковий робочий день, він заробляє достатньо». Коли студенти нарешті отримують диплом, вони шукають інший формат. Тоді вони хочуть знайти роботу на **повний день** *(full-time)*. Робота на повний день вимагає значно більше вашого часу та енергії. «Хоча ця нова робота важка, вона дає мені корисний досвід». «Хоча я працюю на повний день, я також вчуся на курсах». Університет дає нам базову теорію, а реальна робота дає практику. «Хоча академічна теорія дуже важлива, щоденна практика допомагає більше». Ви можете вільно використовувати всі ці складні речення разом. Це покаже, що ви впевнено володієте українською мовою на роботі.

Let's see how a candidate uses these structures in a real situation. Прочитайте цей важливий діалог на офіційній співбесіді. Кандидат відповідає на всі запитання дуже чітко та грамотно.
> — **Менеджер:** Добрий день! Розкажіть про університет, де ви успішно навчалися.
> — **Кандидат:** Добрий день! Я закінчив університет у Києві, який має чудовий економічний факультет.
> — **Менеджер:** Чому ви колись обрали саме цю складну спеціальність?
> — **Кандидат:** Я став економістом, тому що я дуже люблю працювати з великими цифрами.
> — **Менеджер:** Яка ваша головна професійна мета саме зараз?
> — **Кандидат:** Я шукаю стабільну роботу, щоб отримати новий досвід у такій великій компанії.
> — **Менеджер:** Хоча у вас поки мало практичного досвіду, ваше резюме дуже цікаве.
> — **Кандидат:** Якщо ви дасте мені цей шанс, я буду працювати максимально старанно.
> — **Менеджер:** Ми шукаємо відповідальну людину на повний день. Ви готові до цього?
> — **Кандидат:** Так, якщо ваш графік зручний, я повністю готовий працювати на повний день.
This candidate successfully answered all questions using complex sentences. Він показав свій високий рівень освіти. 

<!-- INJECT_ACTIVITY: true-false-structure-culture -->


## Підсумок

Сьогодні ми вивчили чотири типи складних речень. Вони дуже корисні для розмови про вашу освіту та кар'єру. 

Перший тип — це **причина** *(cause)*. Ми використовуємо «тому що». «Я працюю, тому що мені потрібні гроші». 

Другий тип — це **мета** *(purpose)*. Ми використовуємо слово «щоб». «Вона вчиться, щоб знайти хорошу роботу». 

Третій тип — це **означення** *(relative clause)*. Ми використовуємо слова «який» або «де». «Це компанія, де я працюю». 

Четвертий тип — це **умова** *(condition)*. Ми використовуємо слово «якщо». «Якщо я складу іспит, я поїду відпочивати». 

Також ми використовуємо слово «хоча» для дуже складних ситуацій та винятків.

Тепер перевірте себе. Дайте відповіді на ці чотири запитання:

1. Як сказати українською "I work as a lawyer"?
2. Який **прийменник** *(preposition)* вживаємо зі словом «університет» у фразі «вступити ... університету»?
3. Як поєднати дві частини речення: «Я вчуся» та «отримати диплом»? 
4. Як правильно сказати українською "If I pass the exam, I will travel"?

Якщо ви знаєте всі ці відповіді, ви повністю готові до нових граматичних тем. Ваша українська мова стає значно кращою з кожним новим уроком!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: education-and-work
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

**Level: A2 (Module 52/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
