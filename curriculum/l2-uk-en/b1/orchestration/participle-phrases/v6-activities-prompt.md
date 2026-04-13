<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/participle-phrases.yaml` file for module **67: Дієприкметниковий зворот** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-focus-on-identifying-the-and-the-in-12-sentences -->`
- `<!-- INJECT_ACTIVITY: match-up-connect-terms-like-and-with-their-comma-rules-and-examples -->`
- `<!-- INJECT_ACTIVITY: fill-in-insert-the-correctly-inflected-participle-into-a-phrase-based-on-the-noun-provided -->`
- `<!-- INJECT_ACTIVITY: essay-response-sentences -->`
- `<!-- INJECT_ACTIVITY: error-correction-find-10-sentences-with-misplaced-or-missing-commas-in-participle-phrases-and-fix-them -->`
- `<!-- INJECT_ACTIVITY: reading-comprehension -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про що таке дієприкметниковий зворот? і дайте відповіді
    на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Правила відокремлення».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему що таке дієприкметниковий
    зворот?.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему правила відокремлення.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Що таке дієприкметниковий
    зворот?».'
  type: quiz
- focus: З'єднайте терміни з розділу «Правила відокремлення» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- пунктограма (punctuation rule)
- обставинне значення (adverbial shade — causal/conditional)
- трансформація (transformation — converting between structures)
- стилістика (stylistics — choice between phrase and clause)
required:
- дієприкметниковий зворот (participle phrase)
- означуване слово (modified word — the noun the participle refers to)
- означення (attribute — syntactic role of the participle phrase)
- відокремлення (setting off — punctuation with commas)
- постпозиція (postposition — phrase after the noun)
- препозиція (preposition — phrase before the noun)
- підрядне речення (subordinate clause)
- залежні слова (dependent words)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке дієприкметниковий зворот?

> — **Журналіст:** Прямий ефір із Закарпаття. Річка, що вийшла з берегів, затопила навколишні поля та дороги. Ситуація залишається напруженою. *(Live from Zakarpattia. The river that overflowed its banks has flooded the surrounding fields and roads. The situation remains tense.)*
> — **Рятувальник:** Так, це правда. Будинки, пошкоджені повінню, потребують капітального ремонту. Місцеві жителі зараз перебувають у безпечних зонах. *(Yes, that is true. The houses damaged by the flood require major repairs. Local residents are currently in safe zones.)*
> — **Журналіст:** Чи достатньо у вас людей та техніки для ліквідації наслідків стихії? *(Do you have enough people and equipment to deal with the aftermath of the disaster?)*
> — **Рятувальник:** Додаткові рятувальники, викликані вранці, прибули на місце за годину. Вони вже працюють над відновленням інфраструктури. *(Additional rescuers called in the morning arrived at the scene within an hour. They are already working on restoring the infrastructure.)*

In the news report above, pay attention to the phrases *пошкоджені повінню* (damaged by the flood) and *викликані вранці* (called in the morning). These are not simply standalone adjectives or single participles; they are complete descriptive phrases built around a participle. In Ukrainian grammar, when a participle combines with dependent words, they form a **дієприкметниковий зворот** (participle phrase). The participle serves as the structural core of this phrase, while the dependent words provide crucial additional context—such as how, when, by whom, or where the action took place. For example, in the sentence «Фільм, знятий в Україні, отримав найвищу нагороду» (The film shot in Ukraine received the highest award), the word *знятий* (shot) is the passive participle, and *в Україні* (in Ukraine) are its dependent words. Together, they create a cohesive, information-dense unit. This construction allows speakers and writers to pack a significant amount of detail into a single sentence without having to start a completely new subordinate clause.

Кожен дієприкметниковий зворот завжди пов'язаний з певним словом у реченні. Це слово називається означуваним словом. Означуване слово — це іменник або займенник, який описується зворотом і від якого ми ставимо питання. Наприклад, просте слово «книжка» дає лише загальне поняття предмета. Але додавши дієприкметниковий зворот, ми отримуємо ширшу картину: «книжка, написана відомим автором». Тут «книжка» є означуваним словом, а «написана відомим автором» — зворотом, який від неї залежить. Зворот завжди узгоджується зі своїм означуваним словом у роді, числі та відмінку.

> *Every participle phrase is always connected to a specific word in the sentence. This word is called the modified word (означуване слово). The modified word is a noun or pronoun described by the phrase and from which we ask the question. For example, the simple word "book" (книжка) gives only a general concept of the object. But by adding a participle phrase, we get a broader picture: "a book written by a famous author" (книжка, написана відомим автором). Here, "book" is the modified word, and "written by a famous author" is the phrase that depends on it. The phrase always agrees with its modified word in gender, number, and case.*

When analyzing syntax, it is essential to recognize that the entire дієприкметниковий зворот functions as a single sentence member. Even though the phrase contains multiple words, it acts as one extended attribute (**означення**). It serves the exact same syntactic purpose as a regular adjective, answering the questions *який?* (which one? / what kind? masculine), *яка?* (feminine), *яке?* (neuter), or *які?* (plural) about the modified noun. For instance, in the sentence «Книга, прочитана всіма учнями, лежала на столі» (The book read by all the students lay on the table), you ask the question from the subject: Книга (*яка?*) — прочитана всіма учнями. You do not break the phrase apart when mapping the sentence structure; the participle and all its dependent words are treated together as one cohesive attribute.

:::info
**Grammar box**
Because the phrase functions as an attribute, the participle inside it determines the gender, number, and case of the whole structure. If the modified noun changes case, the participle must change its ending to match, while the internal dependent words remain unaffected.
:::

Існує суттєва стилістична різниця між використанням одиничного дієприкметника та цілого дієприкметникового звороту. Одиничний дієприкметник дає предмету лише одну коротку характеристику і не завжди розкриває повний контекст. Наприклад, у реченні «Ми подивились обговорюваний фільм» слово «обговорюваний» просто констатує загальний факт дискусії. Проте, якщо ми використаємо повноцінний зворот: «Фільм, обговорюваний усіма глядачами після прем'єри, викликав багато суперечок», ми миттєво додаємо важливі деталі. Ми чітко розуміємо, ким саме він обговорюваний і коли відбувалася ця подія. Дієприкметниковий зворот несе значно більше смислового навантаження, роблячи опис глибоким і дуже точним. Це корисно для сучасних літературних текстів чи офіційних новин. Крім того, наявність залежних слів серйозно впливає на правила пунктуації.

<!-- INJECT_ACTIVITY: quiz-focus-on-identifying-the-and-the-in-12-sentences -->

## Правила відокремлення

Найважливіша частина вивчення дієприкметникових зворотів — це правильна пунктуація. Уживання розділових знаків залежить від того, де розташований зворот щодо свого означуваного слова. Ця залежність є ключовим синтаксичним правилом. В українській мові ми розрізняємо дві основні позиції. Перша позиція називається **постпозиція**. Це означає, що дієприкметниковий зворот стоїть після іменника або займенника, який він описує. Друга позиція має назву **препозиція**, коли зворот розташований перед своїм означуваним словом. Вибір розташування впливає не лише на розставляння ком, але й на інтонацію та ритм речення. Коли ви пишете текст, ваше стилістичне рішення щодо позиції звороту автоматично диктує вам правила використання ком. Розуміння концепцій препозиції та постпозиції є фундаментом для грамотного письма на рівні B1. Без цього знання неможливо правильно структурувати довгі речення в текстах. Саме тому ми детально розглянемо кожен із цих випадків, щоб ви навчилися вільно орієнтуватися в правилах української пунктуації.

> *The most important part of studying participle phrases is correct punctuation. The use of punctuation marks depends on where the phrase is located relative to its modified word. This dependence is a key syntactic rule. In the Ukrainian language, we distinguish two main positions. The first position is called **постпозиція** (postposition). This means that the participle phrase stands after the noun or pronoun it describes. The second position is called **препозиція** (preposition), when the phrase is located before its modified word. The choice of placement affects not only the use of commas but also the intonation and rhythm of the sentence. When you write a text, your stylistic decision regarding the position of the phrase automatically dictates the rules for using commas. Understanding the concepts of preposition and postposition is a foundation for literate writing at the B1 level. Without this knowledge, it is impossible to correctly structure long sentences in texts. That is exactly why we will examine each of these cases in detail, so that you learn to freely navigate the rules of Ukrainian punctuation.*

Якщо дієприкметниковий зворот стоїть у постпозиції, тобто безпосередньо після свого означуваного слова, він завжди відокремлюється комами. Це залізне правило української мови, яке не має винятків для іменників. Коли розгорнутий зворот розриває речення всередині, ми повинні поставити коми з обох боків, щоб візуально та інтонаційно виділити цю додаткову інформацію. Якщо ж зворот логічно завершує речення, ми ставимо кому перед ним, а в кінці ставимо крапку. Таке відокремлення допомагає читачеві зробити логічну паузу. Розглянемо три класичні приклади, які яскраво ілюструють це базове правило. Перший приклад показує опис поля: «Поле, засіяне пшеницею, тягнулося до самого горизонту». Головним означуваним словом є іменник «поле». Зворот «засіяне пшеницею» стоїть після нього, тому ми виділяємо його комами з обох боків. Другий приклад описує будинок: «Стіна, побілена вапном, сліпуче сяяла на сонці». Означуване слово «стіна» стоїть першим, а зворот слідує за ним, вимагаючи обов'язкового відокремлення комами. Третій приклад передає зимову атмосферу: «Земля, припорошена снігом, виглядала святково». Іменник «земля» передує означенню «припорошена снігом», і пунктуація залишається незмінною.

А тепер змінимо позицію і подивимося на пунктуацію у випадку препозиції. Якщо дієприкметниковий зворот стоїть строго перед означуваним словом, коми зазвичай не ставляться взагалі. Коли зворот передує іменнику, він зливається з ним у єдину інтонаційну групу без паузи. Давайте реконструюємо наші попередні три приклади. Для цього ми просто поміняємо слова місцями. Замість попередньої конструкції маємо таку: «Засіяне пшеницею поле тягнулося до самого горизонту». Як бачите, коми повністю зникли, хоча зміст речення залишився тим самим. Наступний приклад трансформується аналогічно: «Побілена вапном стіна сліпуче сяяла на сонці». Жодного розділового знака між зворотом та іменником немає. І третій приклад звучить так: «Припорошена снігом земля виглядала святково». Відсутність ком у препозиції робить речення більш динамічним та монолітним. Змінюється потік подачі інформації: ми одразу починаємо з ознак і готуємо читача до появи самого предмета в кінці фрази. Цей прийом часто використовується в літературі для створення більш плавного ритму читання.

:::info **Grammar box**
Пам'ятайте базове правило: якщо спочатку йде іменник, а потім дієприкметниковий зворот — коми потрібні. Якщо спочатку йде зворот, а потім іменник — коми не потрібні. Це основа синтаксису.
:::

З кожного загального правила існують важливі винятки. Настав час детально поговорити про особливий випадок, який стосується виключно особових займенників (я, ти, він, вона, воно, ми, ви, вони). Запам'ятайте критично важливе правило: якщо означуваним словом виступає будь-який особовий займенник, дієприкметниковий зворот виділяється комами завжди, незалежно від його позиції в тексті. Вам більше не потрібно перевіряти, чи стоїть зворот перед займенником, чи після нього. Особовий займенник є занадто коротким словом, щоб утворювати інтонаційну групу з довгим зворотом, тому він вимагає паузи. Порівняємо дві правильні конструкції. У першому варіанті зворот стоїть перед займенником: «Стомлений дорогою, я заснув одразу після вечері». Хоча маємо препозицію, кома є обов'язковою через займенник «я». У другому варіанті зворот стоїть після займенника: «Я, стомлений дорогою, заснув одразу після вечері». Тут зворот розриває головне речення, тому ми обов'язково ставимо коми з обох боків. Пунктуація залишається стабільною саме через присутність займенника.

Існує ще одна ситуація, коли дієприкметниковий зворот у препозиції все ж таки відокремлюється комою. Це правило стосується зворотів, які мають додаткове **обставинне значення** (adverbial shade), найчастіше — значення причини. Іноді зворот не просто описує предмет, а й пояснює, чому саме відбулася основна дія. До такого звороту можна легко поставити питання «чому?». Якщо дієприкметниковий зворот перед іменником містить цю причину, він відокремлюється комою. Розглянемо виразний приклад: «Наляканий громовицею, кінь голосно заіржав». Зворот «наляканий громовицею» стоїть перед іменником «кінь». За загальним правилом коми бути не повинно. Але чому кінь заіржав? Саме тому, що він злякався громовиці. Оскільки присутній сильний причиновий зв'язок, ми зобов'язані поставити кому. Якщо ви сумніваєтесь, спробуйте подумки замінити зворот на конструкцію зі словом «оскільки»: «Оскільки кінь був наляканий громовицею, він заіржав». Якщо зміст зберігається, перед вами зворот із причиновим відтінком, і кома потрібна.

<!-- INJECT_ACTIVITY: match-up-connect-terms-like-and-with-their-comma-rules-and-examples -->

<!-- INJECT_ACTIVITY: fill-in-insert-the-correctly-inflected-participle-into-a-phrase-based-on-the-noun-provided -->

## Трансформація: зворот ↔ підрядне речення

Кожен дієприкметниковий зворот можна легко перетворити на підрядне означальне речення, і навпаки. Ця трансформація є корисною навичкою, яка дозволяє гнучко керувати стилем та ритмом мовлення. Підрядне означальне речення завжди починається зі сполучних слів «який», «яка», «яке» або «які». Зворот — це компактна конструкція, що об'єднує дієприкметник та залежні від нього слова в один синтаксичний блок. Коли ми розгортаємо цей блок у підрядне речення, ми створюємо складну синтаксичну структуру з власним підметом та присудком. Така заміна не змінює основного змісту висловлювання, адже обидві граматичні форми виконують однакову функцію. Проте зміна форми глибоко впливає на те, як речення сприймається читачем. Давайте детальніше розглянемо логіку цього процесу. Дієприкметниковий зворот функціонує як великий прикметник. Він ніби приклеюється до іменника, описуючи його стан після певної дії. Підрядне речення робить крок назад: воно відновлює дію у вигляді повноцінного дієслова, повертаючи фразі динаміку. Завдяки цій властивості ви можете обирати, на чому зробити акцент. Якщо ви хочете підкреслити статичну ознаку предмета, ви залишаєте зворот. Якщо ж вам важливо показати розвиток подій, ви розгортаєте його у підрядне речення. Здатність вільно переходити від однієї форми до іншої є ознакою високого рівня володіння українською мовою.

А тепер перейдемо до конкретних кроків і розглянемо механізм перетворення на практиці. Візьмемо для аналізу просте речення з дієприкметниковим зворотом: «Книга, прочитана мною, лежала на столі». Щоб перетворити цей зворот на підрядне речення, нам потрібно виконати кілька послідовних маніпуляцій. Насамперед ми знаходимо означуване слово, яким у цьому випадку є іменник «книга». Після нього ми ставимо кому і додаємо сполучне слово «яку», тому що в новому реченні вона стане об'єктом дії. Наступний крок є найважливішим: ми беремо пасивний дієприкметник «прочитана» і повертаємо його до форми звичайного дієслова минулого часу — «прочитав». Тепер нам потрібен виконавець дії, який стане новим підметом. У звороті виконавцем був займенник «мною» в орудному відмінку. У підрядному реченні цей агент переміщується на позицію підмета, тому ми ставимо його в називний відмінок і отримуємо «я». Зібравши всі ці елементи разом, ми конструюємо нову фразу: «Книга, яку я прочитав, лежала на столі». Як бачите, зміст залишився абсолютно ідентичним, але структура змінилася. Головне правило полягає в тому, щоб правильно визначити час дієслова та узгодити підмет із присудком. Якщо у звороті немає вказівки на виконавця, ми використовуємо неозначено-особову форму дієслова. Наприклад, фразу «Збудований у минулому столітті міст досі функціонує» ми перетворимо так: «Міст, який збудували у минулому столітті, досі функціонує». Ми додали дієслово у множині «збудували», маючи на увазі невідомих людей у минулому.

> *Now let's move on to specific steps and examine the mechanism of transformation in practice. Let's take a simple sentence with a participle phrase for analysis: "Книга, прочитана мною, лежала на столі". To transform this phrase into a subordinate clause, we need to perform several sequential manipulations. First of all, we find the modified word, which in this case is the noun "книга". After it, we place a comma and add the conjunction "яку", because in the new sentence it will become the object of the action. The next step is the most important: we take the passive participle "прочитана" and return it to the form of a regular past tense verb — "прочитав". Now we need the performer of the action, who will become the new subject. In the phrase, the performer was the pronoun "мною" in the instrumental case. In the subordinate clause, this agent moves to the subject position, so we put it in the nominative case and get "я". Putting all these elements together, we construct a new phrase: "Книга, яку я прочитав, лежала на столі". As you can see, the meaning remained absolutely identical, but the structure changed. The main rule is to correctly determine the tense of the verb and agree the subject with the predicate. If there is no indication of the performer in the phrase, we use an indefinitely personal form of the verb. For example, we will transform the phrase "Збудований у минулому столітті міст досі функціонує" like this: "Міст, який збудували у минулому столітті, досі функціонує". We added the plural verb "збудували", meaning unknown people in the past.*

:::info
**Grammar box**
Зверніть увагу на зміну відмінків при трансформації звороту. Слово, яке було додатком в орудному відмінку (ким? чим?), стає повноцінним підметом у називному відмінку (хто? що?). Водночас дієприкметник перетворюється на звичайне дієслово.
:::

Чому ж українська мова пропонує нам два абсолютно різні способи висловлення однієї думки? Відповідь ховається у стилістиці. Дієприкметниковий зворот традиційно вважається ознакою формального та книжного стилю. Його стислість робить його ідеальним інструментом для написання офіційних документів, наукових статей та художньої літератури. Зворот дозволяє спакувати великий обсяг інформації в мінімальну кількість слів, не перевантажуючи текст сполучниками. Коли ви читаєте серйозний матеріал, звороти додають йому академічної ваги та солідності. З іншого боку, підрядні речення зі словом «який» або «що» є набагато природнішими для живого усного мовлення. У щоденному спілкуванні ми рідко формулюємо ідеї настільки щільно, як на письмі. Нам набагато простіше розбити складну ситуацію на кілька частин, використовуючи повноцінні граматичні основи. Слухачеві також значно легше миттєво обробляти інформацію, яка подається поступово. У розмові фраза «Ми обговорили проєкт, який ви запропонували вчора» прозвучить органічніше, ніж «Ми обговорили запропонований вами вчора проєкт». Крім того, українська мова не має активних дієприкметників минулого часу. Форми на кшталт «прочитавший» чи «зробивший» є російськими кальками, тому підрядне речення залишається єдиним правильним варіантом. Знання цих нюансів дозволяє вам адаптувати своє мовлення до будь-якої ситуації.

Незважаючи на гнучкість обох граматичних структур, надмірне захоплення однією з них може зіпсувати враження від тексту. Важливо відчувати баланс і знати, коли краще уникати підрядних речень, а коли варто відмовитися від зворотів. Якщо ви перевантажите абзац конструкціями зі словом «який», він стане надто багатослівним і монотонним. Безперервне повторення цього слова створює ефект стилістичної бідності. З іншого боку, надмірне нагромадження дієприкметникових зворотів робить текст бюрократичним і штучним. Такий стиль часто називають «канцеляритом». Давайте подивимося на практичний приклад. Уявіть таке речення: «Доповідь, яку підготував наш відділ, містить дані, які зібрали дослідники, які працюють у лабораторії». Це звучить дуже незграбно через потрійне повторення. Речення ніби спотикається на кожному кроці. Тепер застосуємо наші знання про трансформацію і замінимо два підрядні речення на компактні дієприкметникові звороти. Новий варіант звучатиме так: «Підготовлена нашим відділом доповідь містить дані, зібрані дослідниками лабораторії». Текст миттєво стає більш елегантним, академічним та легким для читання. Ми позбулися зайвих слів і зберегли весь інформаційний обсяг. Уміле чергування простих речень, дієприкметникових зворотів та підрядних конструкцій робить вашу українську мову по-справжньому виразною.

<!-- INJECT_ACTIVITY: essay-response-sentences -->

## Складні випадки та помилки

Іноді одне слово може мати кілька означень. Це трапляється, коли ми хочемо дати максимально повну характеристику предмету. У таких випадках ми використовуємо кілька дієприкметникових зворотів, які стосуються одного означуваного слова. Правила пунктуації тут схожі на правила для однорідних членів речення. Якщо два звороти стоять після означуваного слова і з'єднані неповторюваним сполучником «і», кома між ними не ставиться. Ми ставимо коми лише на початку першого звороту та в кінці другого. Наприклад: «Доповідь, написана студентом і перевірена професором, викликала дискусію». Як бачите, сполучник «і» зшиває два звороти в одну конструкцію. Ми відокремлюємо її від решти речення, але всередині ком немає. Проте, якщо сполучника немає, кожен зворот відокремлюється: «Доповідь, написана студентом, перевірена професором, викликала дискусію». Якщо ж ці два звороти стоять перед словом і з'єднані сполучником «і», коми зникають: «Написана студентом і перевірена професором доповідь викликала дискусію». Розуміння цієї логіки допоможе вам створювати складні речення без зайвого нагромадження розділових знаків.

Однією з найпоширеніших помилок є загублена кома в середині речення. Цю помилку часто називають проблемою «відкритого бутерброда». Коли дієприкметниковий зворот стоїть після означуваного слова, він завжди вимагає відокремлення. Якщо зворот знаходиться в кінці речення, ми ставимо кому перед ним, а після нього йде крапка. Але ситуація змінюється, коли зворот розриває речення навпіл. У такому випадку він повинен бути виділений комами з обох боків, подібно до того, як начинка лежить між двома шматками хліба. Дуже часто люди ставлять першу кому, але забувають про другу. Неправильний варіант виглядає так: «Книга, написана відомим автором лежала на столі». Це груба помилка, адже зворот зливається з присудком. Правильно писати: «Книга, написана відомим автором, лежала на столі». Завжди перевіряйте, чи закрили ви дієприкметниковий зворот комою.

Ще одна серйозна проблема — це «відірваний» дієприкметниковий зворот. Ця помилка виникає тоді, коли зворот логічно не узгоджується з підметом речення або стосується іншого слова. Дієприкметник завжди описує ознаку, що виникла внаслідок дії, і ця ознака має належати конкретному предмету. Класичний приклад такої помилки звучить так: «Прочитана всіма, бібліотекар забрала книгу». Якщо ми проаналізуємо це речення, то виявиться, що означуваним словом для звороту є підмет «бібліотекар». Виходить абсурдна ситуація: нібито всі прочитали бібліотекаря, а потім вона забрала книгу. Щоб уникнути цієї помилки, потрібно перевіряти, до якого слова належить дія. Правильний варіант вимагає зміни структури речення, щоб зворот стояв біля свого справжнього означуваного слова. Ми повинні сказати: «Прочитану всіма книгу бібліотекар забрала». Тепер усе логічно: книга є прочитаною, а бібліотекар просто виконує дію.

:::info
**Grammar box**
В українській мові заборонено використовувати активні дієприкметники минулого часу із суфіксами -вш- або -ш-. Це грубі російські кальки, які засмічують мову і псують її природне звучання.
:::

Найважливішим кроком до чистої української мови є відмова від активних дієприкметників минулого часу. Форми на кшталт «читавший», «зробивший» чи «склавший» є штучними утвореннями. Сучасна українська літературна норма не визнає таких слів. Замість них ми завжди використовуємо підрядні означальні речення зі словами «який», «що» або «той, що». Розгляньмо п’ять типових суржикових кальок та їхні правильні відповідники. Замість слова «побідивший» слід казати «той, що переміг». Слово «прийшовший» легко замінюється на «який прийшов». Замість «написавший» ми кажемо «який написав». Кальку «співавший» треба замінити на «який співав», а замість «побачивша» слід використовувати «яка побачила». Використання підрядних речень у таких ситуаціях не лише виправляє помилку, але й робить ваше мовлення автентичним. Це маркер високого рівня володіння українською мовою.

> *The most important step toward clean Ukrainian is abandoning active past participles. Forms like «читавший», «зробивший», or «склавший» are artificial constructs. The modern Ukrainian literary standard does not recognize such words. Instead, we always use subordinate clauses with the words «який», «що», or «той, що». Let's look at five typical Surzhyk calques and their correct equivalents. Instead of the word «побідивший», you should say «той, що переміг». The word «прийшовший» is easily replaced by «який прийшов». Instead of «написавший», we say «який написав». The calque «співавший» must be replaced by «який співав», and instead of «побачивша», you should use «яка побачила». Using subordinate clauses in such situations not only fixes an error but also makes your speech authentic. This is a marker of a high level of Ukrainian proficiency.*

<!-- INJECT_ACTIVITY: error-correction-find-10-sentences-with-misplaced-or-missing-commas-in-participle-phrases-and-fix-them -->

## Читання та практика

We have analyzed the grammar and punctuation of participle phrases in detail, exploring how they are formed and punctuated depending on their position in a sentence. Now, let us see how they function in real texts. Participle phrases are a hallmark of formal, journalistic, and encyclopedic Ukrainian. They allow writers to condense complex information into a single, elegant sentence, avoiding the repetitive use of simple clauses. Read the following news report about a natural disaster in the Carpathian Mountains. Pay close attention to how the journalist uses participle phrases to describe the causes and consequences of the flood concisely. Notice the strategic placement of these phrases before and after the nouns they modify.

Екстрені новини Закарпаття. Сильні осінні дощі, що не припинялися протягом останніх трьох днів, спричинили масштабну повінь у гірському регіоні. Швидка річка, переповнена дощовою водою, несподівано вийшла з берегів та затопила кілька великих сіл у долині. Зруйновані мости суттєво ускладнюють роботу місцевих рятувальних служб та волонтерів. Затоплені угіддя завдають величезних фінансових збитків фермерам, які щойно зібрали врожай. Люди, евакуйовані рятувальниками, зараз перебувають у тимчасових наметових таборах та міських школах. Житлові будинки, пошкоджені безжальною стихією, потребують капітального ремонту або навіть повної відбудови. Регіональний уряд негайно пообіцяв надати всебічну фінансову допомогу всім постраждалим родинам. Кошти, виділені з державного резервного фонду, надійдуть на рахунки людей уже наступного тижня, щоб вони могли розпочати процес відновлення.

> *Breaking news from Zakarpattia. Heavy autumn rains that did not stop over the last three days caused a massive flood in the mountain region. The fast river, overfilled with rainwater, unexpectedly overflowed its banks and flooded several large villages in the valley. Destroyed bridges significantly complicate the work of local rescue services and volunteers. Flooded farmlands cause huge financial losses for farmers who had just harvested their crops. People evacuated by rescuers are currently in temporary tent camps and city schools. Residential houses damaged by the merciless elements require major repairs or even complete rebuilding. The regional government immediately promised to provide comprehensive financial assistance to all affected families. The funds allocated from the state reserve fund will arrive in people's accounts as early as next week so they can begin the recovery process.*

Notice how the participle phrases in the news report act as compressed relative clauses. Instead of saying «мости, які були зруйновані» (bridges that were destroyed), the journalist simply writes «зруйновані мости». This condensation is essential for news reporting, where strict word counts and reading speed matter immensely. A dense, informative style keeps the audience engaged without bogging them down in unnecessary functional words. 

:::tip
**Did you know?**
Journalists frequently use preposed participle phrases (placed directly before the noun) because they save even more space by eliminating commas. While «люди, евакуйовані рятувальниками» is grammatically correct and elegant, a newspaper headline might shorten it to «евакуйовані рятувальниками люди» to save precious physical space on the printed page.
:::

Now, let us look at an even more formal register: an encyclopedic entry about a major historical monument. This style relies heavily on participle phrases to build an authoritative tone.

Софійський собор, розташований у самому історичному центрі стародавнього Києва, є видатною пам’яткою архітектури часів могутньої Київської Русі. Цей величний християнський собор, збудований Ярославом Мудрим у першій половині одинадцятого століття, швидко став головним символом духовної могутності давньої української держави. Товсті внутрішні стіни, прикрашені мозаїками та яскравими фресками, дивом зберегли свою оригінальну красу до наших днів, незважаючи на численні війни. Головна вівтарна мозаїка, відома всьому світу під назвою Оранта, глибоко вражає відвідувачів неперевершеною майстерністю виконання та прихованим філософським змістом. Цей старовинний храм, занесений до списку ЮНЕСКО, щороку приваблює десятки тисяч захоплених туристів і науковців з усього світу. Мальовнича територія навколо собору, оточена високим кам’яним муром, створює дивовижну атмосферу глибокого спокою серед галасливого гомінкого мегаполіса. Весь унікальний архітектурний ансамбль, визнаний європейськими експертами одним із найкращих зразків візантійського стилю, назавжди залишається важливим центром української національної культури.

The encyclopedic text about Saint Sophia Cathedral demonstrates the true stylistic power of participle phrases in formal Ukrainian prose. In academic writing, a high density of factual information is required within a limited space. Authors must convey dates, creators, locations, and artistic details efficiently. Let us compare the first sentence of the cathedral text with a highly simplified version that avoids participle phrases entirely.

The simplified, beginner-level version sounds like this: «Софійський собор розташований у центрі Києва. Він є видатною пам’яткою архітектури». This structure, consisting of two short, completely independent sentences, feels slightly repetitive and noticeably simplistic. It wastes the reader's time by requiring two separate subject-verb pairings to deliver one core idea.

By using a postposed participle phrase surrounded by commas, we combine these ideas seamlessly and elegantly: «Софійський собор, розташований у самому історичному центрі стародавнього Києва, є видатною пам’яткою архітектури». This combined sentence has a much more historical and authoritative register. It immediately signals to the reader that the text is written by an educated expert who knows how to manipulate sentence structure for maximum impact. 

Furthermore, observe how the encyclopedic text stacks these phrases to build an immersive atmosphere. The sentence describing the walls uses the phrase «прикрашені мозаїками та яскравими фресками» to embed a vivid visual description directly into the subject before moving on to the main verb. Mastering this stylistic transformation is a critical step for achieving B1+ literacy, allowing you to elevate your writing from basic transactional communication to truly sophisticated prose.

Now it is your turn to practice this formal register and apply everything you have learned in this module. Your final task is to write a short, formal description of a famous historical landmark, an important building, or a well-known monument in your own city. Imagine you are writing a professional brochure for foreign tourists or an introductory paragraph for a Wikipedia article. 

Write a cohesive paragraph consisting of six to eight well-structured sentences. You must consciously use at least four distinct participle phrases in your text to elevate the register. To demonstrate your complete mastery of Ukrainian punctuation rules, you must alternate between preposition and postposition. Specifically, use two participle phrases placed directly before the noun (ensuring there are no commas) and two phrases placed after the noun (properly enclosed by commas). 

Pay extremely close attention to the grammatical agreement in gender, number, and case between your chosen participle and its modified noun. Remember that the participle is essentially an adjective derived from a verb, so it must perfectly mirror the noun it describes. Read your text aloud to check the flow and verify that you have not created any dangling participles.

<!-- INJECT_ACTIVITY: reading-comprehension -->

## Підсумок

Дієприкметниковий зворот — це потужний стилістичний інструмент, який робить ваше мовлення більш лаконічним, книжним та професійним. Протягом цього модуля ми детально розглянули три головні правила пунктуації, які ви повинні запам'ятати. Перше правило стосується позиції: якщо зворот стоїть після означуваного слова, ми завжди відокремлюємо його комами, але якщо він стоїть перед іменником, коми зазвичай не потрібні. Друге важливе правило стосується особових займенників: якщо зворот описує займенник, наприклад, «я», «ми» або «вони», він завжди виділяється комами, незалежно від свого місця в реченні. Третє правило — це наявність обставинного відтінку причини. Якщо зворот, що стоїть перед іменником, пояснює причину дії, ми також обов'язково ставимо кому. Крім того, ми навчилися трансформувати довгі підрядні речення зі словом «який» у компактні дієприкметникові звороти. Ця трансформація є ключовою навичкою для написання текстів офіційно-ділового та наукового стилів, дозволяючи уникати тавтології та повторень.

> *The participle phrase is a powerful stylistic tool that makes your speech more concise, literary, and professional. Throughout this module, we have detailed the three main punctuation rules you must remember. The first rule concerns position: if the phrase stands after the modified word, we always set it off with commas, but if it stands before the noun, commas are usually not needed. The second important rule concerns personal pronouns: if the phrase describes a pronoun, such as "I," "we," or "they," it is always set off by commas, regardless of its place in the sentence. The third rule is the presence of an adverbial shade of reason. If a phrase standing before a noun explains the reason for the action, we also necessarily place a comma. Furthermore, we learned to transform long subordinate clauses with the word "which" into compact participle phrases. This transformation is a key skill for writing texts in formal and academic styles, allowing you to avoid tautology and repetition.*

:::info
**Comma checklist**
1. After the noun? **Always commas.**
2. Refers to a personal pronoun? **Always commas.**
3. Has a causal shade? **Always commas.**
4. Just a regular phrase before the noun? **No commas.**
:::

Перед тим як завершити цей модуль, дуже важливо зробити коротку самоперевірку. Спробуйте чесно відповісти на кілька запитань, щоб оцінити свій поточний рівень розуміння теми. По-перше, чи можу я швидко та безпомилково знайти означуване слово в будь-якому складному реченні? По-друге, чи вмію я впевнено ставити коми, якщо дієприкметниковий зворот стоїть безпосередньо після цього іменника? По-третє, чи завжди я пам'ятаю про обов'язкові коми, коли зворот стосується займенників «я», «ми», «ви» або «вони»? Нарешті, чи можу я легко замінити підрядне речення зі словом «який» на витончений дієприкметниковий зворот під час написання формального тексту? Якщо ви відповіли «так» на всі ці запитання, ви чудово засвоїли матеріал. Якщо ж ви відчуваєте невпевненість, варто ще раз переглянути практичні вправи цього розділу.

> *Before completing this module, it is very important to do a short self-check. Try to honestly answer a few questions to evaluate your current level of understanding of the topic. First, can I quickly and flawlessly find the modified word in any complex sentence? Second, do I know how to confidently place commas if the participle phrase stands directly after this noun? Third, do I always remember the mandatory commas when the phrase refers to the pronouns "I," "we," "you," or "they"? Finally, can I easily replace a subordinate clause with the word "which" with an elegant participle phrase when writing a formal text? If you answered "yes" to all these questions, you have mastered the material perfectly. If you feel unsure, you should review the practical exercises in this section once more.*

While participle phrases are long, descriptive, and typical of formal writing, the next module will introduce you to something much shorter. In Module 60, we will cover short adjectives, known as **короткі прикметники** (short form adjectives), such as **зелен** (green) and **повен** (full). Unlike the bureaucratic precision of participle phrases, short adjectives are a stylistic tool used for poetic, expressive, and folkloric Ukrainian. They will add a beautiful, lyrical rhythm to your vocabulary, allowing you to appreciate the language's rich cultural heritage.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: participle-phrases
level: b1

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

**Level: B1 (Module 67)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
