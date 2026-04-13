<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/complex-subordinate-object.yaml` file for module **76: З'ясувальні речення** (b1).

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

- `<!-- INJECT_ACTIVITY: reading-complex-sentence-intro -->`
- `<!-- INJECT_ACTIVITY: fill-in-complex-sentence-intro -->`
- `<!-- INJECT_ACTIVITY: quiz-complex-sentence-intro -->`
- `<!-- INJECT_ACTIVITY: match-up-object-clauses -->`
- `<!-- INJECT_ACTIVITY: error-correction-object-clauses -->`
- `<!-- INJECT_ACTIVITY: essay-response-object-clauses -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Прочитайте текст про складнопідрядне речення: вступ і дайте відповіді на
    запитання.'
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «З'ясувальні підрядні
    частини».
  type: essay-response
- focus: 'Вставте правильну граматичну форму у реченнях на тему складнопідрядне речення:
    вступ.'
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему з'ясувальні підрядні частини.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Складнопідрядне
    речення: вступ».'
  type: quiz
- focus: З'єднайте терміни з розділу «З'ясувальні підрядні частини» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- аби (synonym of щоб — less formal)
- ніби (as if — conjunction of manner)
- наче (as though — conjunction of comparison)
- непрямі відмінки (indirect cases — all except називний)
- дієслово мовлення (verb of speech — сказати, запитати)
- дієслово мислення (verb of thought — думати, знати)
required:
- складнопідрядне речення (complex sentence with subordination)
- головна частина (main clause)
- підрядна частина (subordinate clause)
- з'ясувальне речення (explanatory/object clause)
- сполучник підрядності (subordinating conjunction)
- сполучне слово (relative/connective word)
- пояснюване слово (explained word — verb in main clause)
- що (that — conjunction or relative word)
- щоб (in order to/that — conjunction of desire/purpose)
- чи (whether — conjunction for questions)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Складнопідрядне речення: вступ

In module 66, you explored compound sentences, known as *складносурядні речення*, where two or more independent clauses are joined together by coordinating conjunctions like «і», «або», or «але». In those structures, both parts of the sentence carry equal grammatical weight and can usually stand completely alone as independent thoughts without losing their core meaning. Now, we are shifting our grammatical focus to a significantly different type of complex structure where the relationship between the connected clauses is fundamentally unequal. This new sentence structure is absolutely essential for expressing complex thoughts, reporting what someone said to you, or explaining the deeper reasons behind a specific action.

**Складнопідрядне речення** (complex sentence with subordination) — це складне речення, яке складається з двох або більше нерівноправних частин. Одна частина завжди є головною, а інша — підрядною. **Головна частина** (main clause) містить основну думку, тоді як **підрядна частина** (subordinate clause) лише доповнює або пояснює її. Ці частини з'єднуються за допомогою спеціальних службових слів, які називаються сполучниками або сполучними словами. Ви не можете розділити таке речення на два окремих, оскільки підрядна частина втратить свій сенс без головної.

> *A complex sentence with subordination is a complex sentence that consists of two or more unequal parts. One part is always the main clause, and the other is subordinate. The main clause contains the main idea, while the subordinate clause only complements or explains it. These parts are connected using special functional words called a subordinating conjunction or a relative/connective word. You cannot divide such a sentence into two separate ones, because the subordinate clause will lose its meaning without the main one.*

:::info
**Grammar box**
Always look at the verb in the main clause first. Verbs of speech (говорити, казати), thought (думати, знати), and perception (бачити, чути) are your strongest signals that an object clause is coming next.

*References: Заболотний Grade 8, p. 84-94; Ворон Grade 9, p. 57-69; Авраменко Grade 8, p. 73.*
:::
info
**The core difference**
In a compound sentence, the clauses hold hands as equals. In a complex sentence, the subordinate clause completely depends on the main clause, much like a child holding a parent's hand. This structural inequality is the defining feature of subordination in Ukrainian syntax.
:::

The single most important skill for mastering complex subordinate sentences is recognizing and understanding this deep dependency relationship. Because the clauses are completely unequal, you can always establish a clear, logical link leading from one clause directly to the other. The main clause always acts as the stable anchor of the sentence, containing a specific **пояснюване слово** (explained word — verb in main clause) that naturally poses a question. The subordinate clause exists solely to answer that exact grammatical question, connected by a **сполучник підрядності** (subordinating conjunction) or a **сполучне слово** (relative/connective word). Identifying this hidden question is the ultimate key to knowing exactly which type of subordinate clause you are dealing with and which specific conjunction is the most appropriate to use in that context.

Щоб знайти та правильно проаналізувати підрядну частину, вам завжди потрібно поставити логічне питання від головної частини. Розглянемо дуже простий і поширений приклад із нашого повсякденного спілкування: «Я знаю, що він прийде». У цьому короткому реченні головна частина — це слова «Я знаю». Від цієї частини ми ставимо питання: я знаю (що саме?). Точна відповідь на це питання міститься саме у підрядній частині: «що він прийде». Завдяки цьому простому питанню ми чітко бачимо нерозривний логічний зв'язок і розуміємо, чому ці дві частини не можуть існувати одна без одної. Сполучник **що** (that — conjunction or relative word) слугує містком, який допомагає приєднати цю необхідну відповідь до головної дії.

By actively asking these specific questions, you can easily classify all subordinate clauses into different functional categories. This systematic method is exactly how Ukrainian schoolchildren learn syntax when they reach the ninth grade. The specific question you ask from the main clause completely determines the nature of the new information the subordinate clause provides. Does it describe a noun in the main clause, functioning much like a long adjective? Does it explain the surrounding circumstances of an action, acting like an adverb? Or does it function like a direct object, answering the complex questions of the indirect noun cases?

Якщо підрядна частина детально описує певний іменник у головній частині, вона завжди відповідає на питання «який?», «яка?», «яке?» або «які?». Розглянемо такий приклад: «Книга, яку я прочитав, була дуже цікава». Головна частина тут — «Книга була дуже цікава», а від слова «книга» ми ставимо питання (яка саме книга?): «яку я прочитав». Це класичне означальне підрядне речення. Якщо ж підрядна частина вказує на точний час, місце або причину певної дії, вона відповідає на питання обставин: «Коли пішов дощ, ми швидко сховались». Ми сховались (коли саме?): «коли пішов дощ». Це вже типове обставинне підрядне речення.

According to the standard Ukrainian school grammar curriculum, there are three primary functional categories of complex subordinate sentences: attributive, adverbial, and explanatory. As you clearly saw in the previous instructional examples, attributive clauses describe a specific object in detail, while adverbial clauses set the broader scene by explaining exactly when, where, why, or how a particular event happened. The third major type, and arguably the absolute most common category encountered in daily conversational Ukrainian, is the **з'ясувальне речення** (explanatory/object clause). This type is fundamental for expressing complex thoughts and reporting information.

У цьому важливому модулі ми зосередимося виключно на з'ясувальних реченнях. Вони граматично виконують роль звичайного додатка і завжди відповідають на питання непрямих відмінків, такі як «кого?», «чого?», «кому?», «чому?», «ким?», «чим?». Ми постійно і дуже активно використовуємо їх у щоденному мовленні, коли переказуємо чиїсь слова, висловлюємо свої власні думки, ділимося глибокими почуттями або передаємо чиїсь прохання. Ви поступово навчитеся будувати такі складні речення, використовуючи сполучник **щоб** (in order to/that — conjunction of desire/purpose) та сполучник **чи** (whether — conjunction for questions), а також дізнаєтеся, як правильно ставити коми.

Before we dive deep into the specific grammatical rules and the various conjunctions uniquely used for object clauses, let's carefully read and analyze a short introductory text. This narrative passage clearly demonstrates how naturally different types of complex sentences blend together in normal conversational Ukrainian. As you read, pay close attention to exactly how the clauses connect with one another. Try to quickly spot the main idea hiding within each complex sentence and see how the subordinate parts add vital details.

Вчора я несподівано зустрів свого дуже давнього друга, який щойно повернувся з неймовірно довгої подорожі світом. Він з великим захопленням розповів мені, що відвідав багато цікавих і красивих міст у Західній Європі. Я одразу запитав його, чи йому дійсно сподобалася ця довга поїздка. Мій друг щиро відповів, що він дуже щасливий, бо нарешті побачив ті знамениті місця, про які завжди так палко мріяв. Він також наполегливо порадив, щоб я обов'язково поїхав туди наступного року під час відпустки. Коли ми тепло прощалися ввечері, я раптом зрозумів, як важливо мати такі яскраві та позитивні спогади у своєму житті.

<!-- INJECT_ACTIVITY: reading-complex-sentence-intro -->
<!-- INJECT_ACTIVITY: fill-in-complex-sentence-intro -->
<!-- INJECT_ACTIVITY: quiz-complex-sentence-intro -->

## З'ясувальні підрядні частини

In Ukrainian syntax, a **складнопідрядне речення** (complex sentence with subordination) often relies on object clauses to deliver its full meaning. Specifically, a **з'ясувальне речення** (explanatory/object clause) functions essentially like a noun or a pronoun within a sentence. This type of **підрядна частина** (subordinate clause) takes on the role of an object, answering the complex questions associated with the indirect cases.

These indirect cases, known as **непрямі відмінки** (indirect cases — all except називний), cover questions like whom, of what, to whom, what, by whom, or with what. Whenever you would naturally ask these questions after the **головна частина** (main clause), you are dealing with an explanatory clause. These clauses are deeply essential for reporting speech, expressing personal thoughts, or sharing emotions.

To smoothly connect this subordinate part to the main clause, Ukrainian relies on a specific set of conjunctions. The most common primary conjunctions you will encounter are **що** (that — conjunction or relative word), **щоб** (in order to/that — conjunction of desire/purpose), and **чи** (whether — conjunction for questions). Depending on the exact nuance, the language also utilizes other conjunctions such as аби, мов, як, ніби, наче, and неначе.

Окрім звичайних сполучників, українська мова дуже часто використовує спеціальне **сполучне слово** (relative/connective word) для приєднання з'ясувальної підрядної частини. До цієї важливої категорії належать такі слова: хто, який, чий, котрий, де, куди, звідки, коли, чому, скільки, як. Головна різниця полягає в тому, що ці слова не просто механічно з'єднують дві частини складного речення, а й зберігають своє власне лексичне значення. Вони завжди виступають повноцінними членами підрядної частини, наприклад, підметом, додатком або обставиною. Коли ми використовуємо таке слово, ми одночасно ставимо питання і даємо на нього відповідь у межах одного висловлювання. Вибір конкретного слова повністю залежить від того, яку саме інформацію ми хочемо з'ясувати або доповнити.

> *In addition to regular conjunctions, the Ukrainian language very often uses a special connective word to attach the explanatory subordinate clause. This important category includes words like who, which, whose, which one, where, where to, from where, when, why, how much, and how. The main difference is that these words do not just mechanically connect two parts of a complex sentence; they also retain their own lexical meaning. They always act as full-fledged members of the subordinate clause, for example, as a subject, object, or adverbial modifier. When we use such a word, we simultaneously ask a question and provide an answer to it within a single statement. The choice of a specific word depends entirely on what exactly we want to clarify or supplement.*

Structurally, the placement of an explanatory clause within a sentence follows a strict logical flow. The subordinate clause almost always stands immediately after the **пояснюване слово** (explained word — verb in main clause) located in the main sentence. This explained word is the structural anchor of the entire complex sentence. But what exactly is an explained word, and why does it demand further clarification? A sentence often contains a verb or an adjective whose meaning feels incomplete on its own. If you simply walk into a room and declare, "I know" or "She said," your listeners will immediately expect more information. The meaning of these verbs inherently points outward, actively requiring an object or an entire dependent clause to resolve the thought and deliver the actual message. The explanatory clause steps in to fulfill this exact grammatical and semantic need. It unpacks the content of the thought, the substance of the statement, or the target of the emotion. The main clause containing the explained word naturally comes first, setting the stage for the crucial information that follows in the subordinate clause.

:::info
**Structural anchor**
The explained word acts as a bridge. Without it, the main clause would feel abruptly cut off, and the subordinate clause would have nothing to attach to logically.
:::

Найчастіше роль пояснюваного слова в головній частині виконують дієслова мовлення та дієслова мислення. Дієслова мовлення, такі як сказати, запитати, відповісти, повідомити, кричати або розповідати, вимагають чіткого розкриття змісту того, що саме було озвучено. Вони є необхідними для побудови непрямої мови та переказу чужих слів чи розповідей. Наприклад, ми часто кажемо: «Він упевнено сказав, що приїде завтра вранці». Тут дієслово «сказав» потребує детального доповнення, яке надає підрядна частина. Інша величезна група — це дієслова мислення, наприклад, знати, думати, вважати, розуміти, пам'ятати, міркувати або припускати. Ці дієслова описують внутрішні когнітивні процеси людини, які завжди спрямовані на певну ідею, факт або явище. Без пояснення того, про що саме людина думає чи що вона пам'ятає, речення залишається порожнім і позбавленим сенсу. Розглянемо такий приклад: «Обов'язково запитай, чи він прийде на нашу зустріч». У цьому випадку мислення і комунікація поєднуються, формуючи складну структуру, де підрядна частина з'ясовує конкретну умову або можливість майбутньої події.

Beyond speech and thought, two other major semantic categories frequently serve as the explained word in the main clause: verbs of perception and verbs of desire. Verbs of perception, such as verbs meaning to feel, to see, to hear, and to notice, describe how we interact with the external world through our senses. When you observe an event unfolding, the subordinate clause captures the specific details of that observation. Verbs of desire and volition, including verbs meaning to want, to wish, and to request, express an internal will directed toward a specific outcome or action performed by someone else. For instance, you might say a sentence like this:

**Я хочу, щоб ти допоміг.** — *I want you to help.*

The main clause states the desire, while the subordinate clause specifies exactly what that desire entails. Similarly, when using relative words, you might say:

**Ніхто не знає, де він живе.** — *No one knows where he lives.*

**Розкажи, хто тобі це сказав.** — *Tell me who told you this.*

In all these cases, the explained word creates a distinct grammatical vacuum that only the explanatory clause can adequately fill.

Щоб правильно формувати свої думки, дуже важливо розуміти специфічну функцію, яку виконує кожен **сполучник підрядності** (subordinating conjunction) у реченні. Найбільш універсальним і частотним є сполучник «що», який використовується виключно для констатації реальних фактів, об'єктивних подій або передачі точної інформації без додаткових емоційних відтінків. Якщо ж ви хочете висловити сильне бажання, наказ, прохання або вказати на конкретну мету певної дії, вам необхідно використовувати сполучник «щоб» або його розмовний стилістичний синонім «аби». Ці слова завжди вказують на певну інтенцію або бажаний результат у майбутньому. Окрему і важливу роль відіграє сполучник «чи». Він слугує головним інструментом для передачі непрямих запитань, які передбачають альтернативу або відповідь «так» чи «ні». Важливо пам'ятати, що українська мова чітко розділяє умову та непряме питання, тому використання слова «якщо» замість «чи» в з'ясувальних реченнях є серйозною граматичною помилкою. Кожен сполучник має своє точне місце і своє унікальне логічне навантаження в архітектурі складного речення.

For English speakers, the conjunction **чи** is particularly important because it serves as the direct equivalent of "if" or "whether" when forming indirect questions. While English relies on "if" for both conditional statements ("If it rains...") and indirect yes/no questions ("I asked if it will rain"), Ukrainian strictly separates these two distinct functions. 

<!-- INJECT_ACTIVITY: match-up-object-clauses -->

## Сполучник vs сполучне слово

One of the most critical grammatical distinctions you must master when building a **складнопідрядне речення** (complex sentence with subordination) is identifying the exact nature of the connecting element. A **сполучник підрядності** (subordinating conjunction) has absolutely no syntactic role inside the **підрядна частина** (subordinate clause). Its only job is to function purely as a structural link connecting the main clause to the explanatory information. Common examples of pure conjunctions include words like «щоб» and «чи». However, the most versatile connector is the word «що». Let us examine a standard example: «Я знаю, що він прийде». In the subordinate clause of this sentence, the word «він» serves as the subject, while «прийде» is the predicate. The word «що» is just a transparent connector linking the two clauses together. It is structurally necessary, but it carries no semantic weight of its own.

In stark contrast, a **сполучне слово** (relative/connective word) is fundamentally different because it is an active, functional member of the subordinate clause. It does not merely connect; it replaces an independent part of speech and carries tangible semantic meaning. When you encounter the word **що** (that — conjunction or relative word) acting as a relative pronoun, it typically represents a specific thing or idea. Let us analyze the sentence: «Я знаю, що ти читаєш». Here, the **пояснюване слово** (explained word — verb in main clause) points to the process of possessing knowledge. In the subordinate clause, «ти» is the subject, and «читаєш» is the predicate. However, the action of reading requires a direct object. The connector steps in to fulfill that role, representing the actual thing being read. Therefore, in this context, it serves as the direct object of the verb «читаєш», making it an indispensable, active member of the clause rather than a simple link.

Сполучне слово завжди відповідає на певне питання всередині підрядної частини. Його неможливо просто вилучити з тексту, адже тоді весь зміст висловлювання буде зруйновано. Якщо ви сумніваєтеся щодо його синтаксичної ролі, спробуйте знайти, яку саме самостійну частину мови воно замінює. Цей простий аналіз допоможе вам уникнути поширених стилістичних помилок і зробити ваше мовлення значно більш природним.

> *A relative word always answers a specific question inside the subordinate clause. It is impossible to simply remove it from the text, because then the entire meaning of the statement will be destroyed. If you have doubts about its syntactic role, try to find exactly which independent part of speech it replaces. This simple analysis will help you avoid common stylistic mistakes and make your speech significantly more natural.*

How can you confidently distinguish between these two functions? There are two reliable tests you can apply to any sentence containing this connector. The first method is the substitution test. Ask yourself: can you replace «що» with the expanded phrase «те, що»? If the sentence maintains its logical meaning, you are dealing with a relative word. For instance, «Я знаю, що ти читаєш» easily transforms into «Я знаю те, що ти читаєш». The second method is the deletion test. Can you drop «що» entirely, and does the **з'ясувальне речення** (explanatory/object clause) still make complete grammatical sense on its own? If you can successfully remove the word without destroying the internal grammatical structure, it is a simple conjunction connecting to the **головна частина** (main clause). For example, removing the connector from «Я знаю, що він прийде» leaves you with «він прийде», which is a complete independent sentence.

:::info
**Grammar box** — Always try the deletion test when in doubt. If dropping the connector leaves you with a broken or incomplete sentence fragment (like «ти читаєш» without its object), the connector was functioning as a crucial relative word. If the remaining clause is fully intact, it was merely a conjunction.
:::

While «що» can operate as either a conjunction or a relative word, several other relative words always function as active clause members. These words introduce the subordinate clause while simultaneously fulfilling specific syntactic roles. For example, the relative pronoun «хто» frequently serves as the subject. If someone says, «Я не знаю, хто це зробив», the word «хто» performs the primary action. Similarly, words indicating location act as adverbials. In the sentence «Скажи, де ти був», the relative word «де» functions as an adverbial of place. When the focus shifts to movement, «куди» acts as an adverbial of direction, as seen in «Я не пам'ятаю, куди поклав ключі». Finally, the word «коли» operates as an adverbial of time, answering when an event occurred, while «скільки» indicates quantity, as in «Вона не знає, скільки це коштує». You will also frequently use **щоб** (in order to/that — conjunction of desire/purpose) and **чи** (whether — conjunction for questions) as pure conjunctions in similar structures.

## Пунктуація та побудова

In Ukrainian, the rules for punctuation in complex sentences are strict, formal, and highly predictable. The most important rule to remember when writing a **складнопідрядне речення** (complex sentence with subordination) is that you must always place a comma before the word that introduces the **підрядна частина** (subordinate clause). This boundary punctuation is a fundamental requirement of Ukrainian syntax, not a stylistic suggestion.

Whether you are using a simple **сполучник підрядності** (subordinating conjunction) or a functioning **сполучне слово** (relative/connective word), the comma is absolutely mandatory to separate the distinct clauses. It serves as a crucial visual marker of the grammatical boundary, signaling to the reader that a new thought—with its own subject and predicate—is beginning.

Цей синтаксичний закон діє без винятків. Кома чітко розділяє дві граматичні основи, допомагаючи читачу миттєво зрозуміти внутрішню структуру вашої думки. Наприклад: «Я думаю, що це правильно» або «Він не знає, де я живу». В англійській мові перед словом «that» кому зазвичай не ставлять, тому це правило часто стає пасткою для іноземців. Проте в українській мові відсутність розділового знака перед словом «що» вважається грубою пунктуаційною помилкою, яка одразу видає невпевненість автора.

There is one structural variation you might encounter, primarily when reading classical literature or listening to highly emphatic, emotionally charged speech. Occasionally, the **з'ясувальне речення** (explanatory/object clause) is placed entirely before the main clause it modifies. In this reversed, inverted structure, the comma still serves its vital role of separating the two distinct clauses, but it appears at the end of the subordinate thought rather than before the conjunction.

Така інверсія створює сильну емоційну напругу та привертає увагу до самого факту або події. Розгляньмо такий незвичний приклад: «Що він приїде, я дізнався вчора». У цьому реченні головна інформація знаходиться в кінці, а підрядна частина слугує емоційним, навіть дещо драматичним вступом. Цей порядок слів є дуже архаїчним і майже ніколи не звучить у стандартному повсякденному мовленні. Сучасні українці віддають перевагу прямій, логічній послідовності думок, де головна ідея передує деталям.

The natural and overwhelmingly preferred position for these explanatory clauses is immediately following the **головна частина** (main clause). Specifically, the subordinate thought must come directly after the **пояснюване слово** (explained word — verb in main clause) that requires clarification. This rigid placement is a defining characteristic of explanatory clauses, ensuring that the listener instantly receives the logical completion of the thought introduced by the main verb.

Ця строга, незмінна позиція відрізняє їх від багатьох інших типів підрядних речень. Наприклад, обставинні речення, які вказують на час, місце або причину дії, мають значно більшу синтаксичну свободу. Ви можете легко і природно сказати: «Коли почався сильний дощ, ми швидко пішли додому» або навпаки: «Ми швидко пішли додому, коли почався сильний дощ». Але з'ясувальна частина міцно прив'язана до свого дієслова-присудка і не може вільно мандрувати текстом. Її місце завжди поруч із тим словом, яке вона має пояснювати.

Let's compare the natural order with the rare, inverted order to see the structural difference clearly. The natural phrasing «Я знаю, **що** (that — conjunction or relative word) він тут» flows smoothly and logically, matching standard communication patterns. The rare inversion «Що він тут, я знаю» sounds defensive, poetic, or highly theatrical. When constructing these sentences, native English speakers often encounter a specific, stubborn interference issue regarding desires, requests, and intentions.

In English, you might frequently use an infinitive object phrase, like "I want you to go" or "She asked him to help." In Ukrainian, this direct infinitive structure is completely impossible when the action is performed by someone else. You cannot link two different actors in a single simple sentence using an infinitive. For these cases, you must use **щоб** (in order to/that — conjunction of desire/purpose) or **чи** (whether — conjunction for questions) to create a brand new clause.

Якщо ваше бажання чи прохання стосується іншої людини, ви зобов'язані побудувати повноцінне складнопідрядне речення. Категорично не можна просто перекласти англійську конструкцію і сказати «Я хочу тебе піти». Ви маєте використати цільовий сполучник «щоб» і дієслово виключно в минулому часі. Правильний і єдино можливий граматичний варіант звучить так: «Я хочу, щоб ти пішов». Так само чітко будуються непрямі питання за допомогою сполучника «чи», наприклад: «Він запитав мене вчора, чи я згоден допомогти».

> *If your desire or request concerns another person, you are obligated to build a full complex sentence with subordination. You categorically cannot simply translate the English construction and say "I want you to go." You must use the purpose conjunction "щоб" and a verb exclusively in the past tense. The correct and only possible grammatical variant sounds like this: "I want that you went" [I want you to go]. Indirect questions are built just as clearly using the conjunction "чи", for example: "He asked me yesterday whether I agree to help."*

:::info
**Grammar box** — Never translate the English pattern "want + object + infinitive." Desires directed at another person always require a subordinate clause starting with «щоб» followed by a verb in the past tense. If you attempt to use an infinitive here, the resulting sentence will sound completely broken and incomprehensible to a native speaker.
:::

<!-- INJECT_ACTIVITY: error-correction-object-clauses -->

## З'ясувальні речення у мовленні

In daily communication, expressing what you think, believe, or feel is one of the most common functions of language. Whenever you share a personal opinion, you are almost certainly building a complex sentence with an object clause.

У повсякденному спілкуванні ми постійно ділимося своїми думками, враженнями та переконаннями з іншими людьми. Для цього українська мова пропонує зручні й дуже поширені синтаксичні конструкції, основою яких є з'ясувальне речення. Найчастіше такі фрази починаються з дієслів мислення, наприклад: «я думаю», «я вважаю», «мені здається» або «я впевнений». Ці слова є своєрідним вступом, який готує вашого співрозмовника до сприйняття суб'єктивної інформації. Далі обов'язково йде сполучник підрядності, який надійно з'єднує вашу думку з основною частиною речення.

> *In everyday communication, we constantly share our thoughts, impressions, and beliefs with other people. For this, the Ukrainian language offers convenient and very common syntactic constructions, the basis of which is the explanatory clause. Most often, such phrases begin with verbs of thought, for example: "I think," "I believe," "it seems to me," or "I am sure." These words are a kind of introduction that prepares your conversational partner to receive subjective information. Then, a subordinating conjunction inevitably follows, securely connecting your thought with the main part of the sentence.*

English speakers are used to dropping the conjunction "that" in casual speech, saying "I think it's raining." In Ukrainian, skipping the connecting word is completely unnatural and grammatically incorrect. You must always explicitly link your clauses. If you say «Я думаю, це добре», native speakers will understand you, but it sounds like a literal translation from English. The natural, correct way to express this is «Я думаю, **що** це добре» (I think that it is good). Another highly frequent expression is «Я вважаю, **що**...» (I consider that...). This is slightly more formal than «я думаю» but is widely used when you want to sound confident about your stance. For example, «Я вважаю, що ми маємо допомогти» (I believe that we should help). Whenever you state your beliefs, remember that the little word **що** (that — conjunction or relative word) is the grammatical glue that holds your entire sentence together.

Another massive area where you will use these structures is when you need to relay information you heard from someone else. This is known as reported speech, or indirect speech. When you transform a direct quote into a reported fact, you rely heavily on verbs of speech acting as the **пояснюване слово** (explained word) in your main clause.

Окрім вираження власних думок, ми часто переказуємо слова інших людей, розповідаємо новини або ділимося чутками. У таких випадках з'ясувальні підрядні частини стають незамінним інструментом у вашому мовному арсеналі. Головна частина речення зазвичай містить дієслово мовлення: «сказати», «повідомити», «розповісти» або «заявити». Ці дієслова вимагають обов'язкового логічного продовження, яке розкриває суть того, що саме було сказано.

> *Besides expressing our own thoughts, we often retell the words of other people, tell news, or share rumors. In such cases, explanatory subordinate clauses become an absolutely indispensable tool in your linguistic arsenal. The main clause usually contains a verb of speech: "to say," "to inform," "to tell," or "to declare." These verbs require a mandatory logical continuation that reveals the essence of exactly what was said.*

For example, if your friend Taras says «Я купив квитки» (I bought the tickets), you report this to someone else by saying «Тарас сказав, **що** він купив квитки» (Taras said that he bought the tickets). Notice how the pronoun changes from "I" to "he," just like in English, and the two parts are firmly connected by our most versatile connector. More formal situations use verbs like «повідомити» (to inform/notify): «Вона повідомила, що зустріч скасовано» (She informed that the meeting is canceled). The beauty of this structure is its predictability. Once you recognize that a verb of speech is coming, your brain should automatically prepare to hear the conjunction and the factual statement that follows it.

Sometimes, the information we want to convey isn't a stated fact, but rather a question or a feeling of uncertainty. When you want to ask an indirect question or express that you don't know something, the structure shifts slightly. Instead of stating a fact with "that", you are presenting an alternative with "whether".

Коли ми не впевнені в чомусь або хочемо ввічливо запитати про щось, ми використовуємо непрямі питання. Для цього українська мова має спеціальний інструмент — сполучник **чи** (whether — conjunction for questions). Він допомагає передати сумнів, вибір між двома варіантами або просто відсутність інформації. Наприклад, ви можете сказати: «Я не знаю, чи він прийде сьогодні». Це звучить набагато природніше і м'якше, ніж пряме запитання «Він прийде сьогодні?».

> *When we are not sure about something or want to politely ask about something, we use indirect questions. For this, the Ukrainian language has a special tool — the conjunction "чи". It helps to convey doubt, a choice between two options, or simply a lack of information. For example, you can say: "I do not know whether he will come today." This sounds much more natural and softer than the direct question "Will he come today?".*

Here, we must address a very common trap for English speakers. In English, you use "if" for both conditionals ("If it rains, I will stay") and indirect questions ("I don't know if it will rain"). Ukrainian strictly separates these two concepts. You use «якщо» only for conditions. For indirect questions answering a "yes or no" premise, you must absolutely use **чи**. Never say «Запитай, якщо магазин працює». This is a direct translation and sounds completely wrong. You must say «Запитай, **чи** магазин працює» (Ask whether the store is open). This tiny word is incredibly powerful for expressing your curiosity, doubts, and inquiries in a polite, culturally appropriate way.

:::info
**Grammar box** — Never translate the English indirect question "if" as «якщо». The word «якщо» strictly means "in the event that" (conditional). When you mean "whether," you must use the conjunction **чи**. For example: «Я не пам'ятаю, **чи** я зачинив двері» (I don't remember if/whether I locked the door).
:::

Moving beyond thoughts and facts, we also use these complex sentences to talk about what we want others to do, or to describe processes we have witnessed. As we discussed earlier, expressing a desire about someone else's actions strictly requires a subordinate clause. You cannot use an infinitive.

Ця конструкція є частотною в українському мовленні, адже ми постійно просимо когось щось зробити, даємо поради або висловлюємо свої побажання щодо інших людей. Дієслова волевиявлення, такі як «хотіти», «просити», «радити» або «вимагати», завжди слугують міцною опорою для підрядної частини, яка починається зі сполучника **щоб** (in order to/that — conjunction of desire/purpose). Зверніть увагу, що після цього слова дієслово завжди стоїть у формі минулого часу, незалежно від реального часу дії.

> *This construction is extremely frequent in Ukrainian speech, because we constantly ask someone to do something, give advice, or express our wishes regarding other people. Verbs of volition, such as "to want," "to ask," "to advise," or "to demand," always serve as a strong support for the subordinate clause, which begins with the conjunction "щоб". Note that after this word, the verb always stands in the past tense form, regardless of the real time of the action.*

For instance, «Мама хоче, **щоб** ти зателефонував» (Mom wants you to call). Another vivid way to use object clauses is with verbs of perception like «бачити» (to see) or «чути» (to hear). When you want to describe an ongoing process that you witnessed, you use the relative word «як» (how/as). For example, «Я бачив, **як** вони танцювали» (I saw them dancing / I saw how they were dancing). This paints a much more dynamic picture than simply stating a fact with "що". It emphasizes that you observed the action as it was unfolding.

Let's see how all these different types of explanatory clauses naturally weave together in a real-life conversation. Imagine a phone call between a mother and her adult child who is studying at a university in Odesa.
 Phone conversations are prime territory for this grammar because people are catching up, sharing news, reporting what others have said, and expressing their worries or beliefs about the future. In just a few lines of dialogue, you will see how the speakers seamlessly switch between stating facts, expressing uncertainty, and communicating desires, proving that this grammar is the absolute backbone of fluent conversational Ukrainian.

Here is a snippet of their conversation. Pay close attention to the verbs in the main clauses and the connectors that follow them.

> — **Мама:** Привіт, синку. Кажу тобі, що все добре, але я все одно хвилююся. *(Hi, son. I am telling you that everything is fine, but I still worry.)*
> — **Студент:** Знаю, що ти хвилюєшся. Але все нормально. *(I know that you are worrying. But everything is fine.)*
> — **Мама:** Тато питав, чи ти вже купив квитки на поїзд додому. *(Dad asked if you already bought the tickets for the train home.)*
> — **Студент:** Ще ні. Я не знаю, чи будуть вільні місця на п'ятницю. *(Not yet. I don't know if there will be available seats for Friday.)*
> — **Мама:** Не вірю, що вже зима. Я хочу, щоб ти тепло одягався. *(I don't believe that it's already winter. I want you to dress warmly.)*
> — **Студент:** Не переживай. Думаю, що складу іспит завтра і одразу піду на вокзал. *(Don't worry. I think that I will pass the exam tomorrow and immediately go to the station.)*
> — **Мама:** Ми дуже хочемо, щоб ти приїхав. *(We really want you to arrive.)*

**Comprehension Questions:**
— Знайдіть усі з'ясувальні підрядні частини.
— Визначте пояснюване слово для кожної.
— Визначте: сполучник чи сполучне слово?

<!-- INJECT_ACTIVITY: essay-response-object-clauses -->

## Підсумок та перехід до M68

In this module, we have thoroughly examined the **складнопідрядне речення** (complex sentence with subordination) and its most frequently used conversational variant. The **з'ясувальне речення** (explanatory/object clause) functions essentially as a heavy-duty object that expands and clarifies the meaning of a specific verb. When a simple noun is not enough to convey a complex thought, an entire clause steps in to complete the picture.

Every such sentence has a logical structure. It begins with a base **головна частина** (main clause) which sets the stage. Within this first half, you will find the key **пояснюване слово** (explained word — verb in main clause), which demands further clarification. Attached to this is the dependent **підрядна частина** (subordinate clause), which answers the questions of indirect cases like «кого?», «чого?», «кому?», «що?» or «ким?».

Завжди пам'ятайте, що ці дві частини речення не є рівноправними. Друга частина повністю залежить від першої і не може існувати як самостійне висловлювання. Вона лише розкриває зміст думок, слів, почуттів або бажань, про які йшлося на самому початку. Саме тому правильний вибір засобу зв'язку між ними є критично важливим для розуміння.

> *Always remember that these two parts of the sentence are not equal. The second part completely depends on the first and cannot exist as an independent statement. It only reveals the content of thoughts, words, feelings, or desires that were mentioned at the very beginning. That is why the correct choice of connection between them is critically important for understanding.*

To connect these structural parts seamlessly, we rely on a specific set of linguistic tools. You must always choose the right **сполучник підрядності** (subordinating conjunction) based on your communicative intent. If you are stating a known fact or reporting someone else's direct speech, you will use **що** (that — conjunction or relative word). If you want to express a strong desire, a strict request, or a purpose, you must switch your tool and use **щоб** (in order to/that — conjunction of desire/purpose).

When you are reporting a yes-or-no question or expressing personal uncertainty, the correct choice is **чи** (whether — conjunction for questions). Besides regular conjunctions, we very often use full-fledged question words to create a flexible connection. Every **сполучне слово** (relative/connective word), such as «хто», «де», «куди», «коли», «як» or «скільки», does double duty. It connects the two halves while remaining a full member of its own clause.

Пам'ятайте залізне правило української пунктуації: перед усіма цими підрядними сполучниками та питальними словами завжди обов'язково ставиться кома. Без цієї коми ваше письмове мовлення буде вважатися граматично неправильним.

Now that you know exactly how to build a complex clause that acts as an object, it is time to look forward. In the next module, M68, we will explore a completely different type of dependent structure called "Означальні речення" (Attributive clauses). While the clauses we learned today replace a noun object and attach to verbs, the clauses in the next module will act as giant, complex adjectives. They will directly describe a specific noun in the main clause, adding rich details and answering the questions «який?», «яка?», «яке?», or «які?» (which/what kind of?).

Перед тим як остаточно переходити до вивчення наступного модуля, будь ласка, перевірте свої поточні знання. Уважно прочитайте ці короткі запитання для самоконтролю, щоб переконатися, що ви повністю готові рухатися далі і будувати складні тексти:
- Чи можу я легко побудувати з'ясувальне речення зі сполучником «що» для передачі факту?
- Чи знаю я напевно, коли саме потрібно використовувати «щоб» замість «що»?
- Чи розумію я, як правильно передати непряме запитання за допомогою частки «чи»?
- Чи пам'ятаю я, що перед будь-яким підрядним зв'язком обов'язково ставиться кома?
- Чи можу я впевнено відрізнити звичайний підрядний сполучник від повноцінного сполучного слова?

:::info
**Grammar box**
Always look at the verb in the main clause first. Verbs of speech (говорити, казати), thought (думати, знати), and perception (бачити, чути) are your strongest signals that an object clause is coming next.
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: complex-subordinate-object
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

**Level: B1 (Module 76)**

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
