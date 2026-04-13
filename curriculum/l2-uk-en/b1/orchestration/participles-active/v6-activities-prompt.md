<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/participles-active.yaml` file for module **65: Активні дієприкметники** (b1).

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

- `<!-- INJECT_ACTIVITY: quiz-participle-definition -->`
- `<!-- INJECT_ACTIVITY: fill-in-present-formation -->`
- `<!-- INJECT_ACTIVITY: match-up-definitions -->`
- `<!-- INJECT_ACTIVITY: essay-response-nature -->`
- `<!-- INJECT_ACTIVITY: error-correction-calques -->`
- `<!-- INJECT_ACTIVITY: reading-comprehension-nature -->`
- `<!-- INJECT_ACTIVITY: match-up-term-definitions -->`
- `<!-- INJECT_ACTIVITY: quiz-active-participles-review -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про що таке дієприкметник? і дайте відповіді на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Активні дієприкметники
    теперішнього часу (-уч-/-юч-, -ач-/-яч-)».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему що таке дієприкметник?.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему активні дієприкметники теперішнього
    часу (-уч-/-юч-, -ач-/-яч-).
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Що таке дієприкметник?».'
  type: quiz
- focus: З'єднайте терміни з розділу «Активні дієприкметники теперішнього часу (-уч-/-юч-,
    -ач-/-яч-)» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- пекучий (burning, scorching — lexicalized active participle)
- киплячий (boiling — lexicalized active participle)
- лежачий (lying — lexicalized, as in лежачий камінь)
- потерпілий (victim — past active participle used as noun)
- збанкрутілий (bankrupt — past active participle)
- змарнілий (emaciated — past active participle)
- панівний (dominant — replaces Russian calque домінуючий)
- мийний (washing/cleaning — replaces Russian calque миючий)
- завідувач (head/manager — replaces Russian calque завідуючий)
required:
- дієприкметник (participle — verb form expressing attribute by action)
- активний дієприкметник (active participle — subject performs the action)
- пасивний дієприкметник (passive participle — subject receives the action)
- квітучий (blooming — natural active participle)
- палаючий (blazing — natural active participle)
- зів'ялий (wilted — past active participle)
- розквітлий (blossomed — past active participle)
- опалий (fallen, shed — past active participle, leaves)
- зниклий (disappeared — past active participle)
- посивілий (gone grey — past active participle)
- чинний (current, valid — replaces Russian calque діючий)
- наявний (existing, available — replaces Russian calque існуючий)
- описовий зворот (descriptive phrase — alternative to participle)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що таке дієприкметник?

Уявіть слово, яке поєднує в собі динаміку живої дії та стабільність постійної ознаки. У сьомому класі українських шкіл, за підручником О. Литвінової, учні дізнаються, що дієприкметник — це особлива форма дієслова. Вона означає ознаку предмета за дією або станом. Це справжній мовний гібрид, який бере найкраще від двох різних світів. Від дієслова він успадковує час, вид та стан, зберігаючи внутрішню енергію процесу. Від прикметника він отримує здатність відповідати на питання «який?», «яка?», «яке?», «які?», а також змінюватися за родами, числами та відмінками. Щоб краще зрозуміти цю подвійну природу, порівняйте звичайне дієслово «квітнути» та утворений від нього дієприкметник «квітучий». Дієслово просто констатує факт дії у часі, тоді як дієприкметник перетворює цю дію на яскраву характеристику самого предмета, дозволяючи нам малювати словами глибокі та точні образи.

> *Imagine a word that combines the dynamics of a live action and the stability of a permanent trait. In the seventh grade of Ukrainian schools, according to O. Lytvynova's textbook, students learn that a participle is a special form of a verb. It denotes an attribute of an object based on an action or state. It is a true linguistic hybrid that takes the best from two different worlds. From the verb, it inherits tense, aspect, and voice, preserving the internal energy of the process. From the adjective, it gets the ability to answer the questions "which?", as well as to change by gender, number, and case. To better understand this dual nature, compare the regular verb "квітнути" and the participle "квітучий" formed from it. The verb simply states the fact of the action in time, while the participle turns this action into a vivid characteristic of the object itself, allowing us to paint deep and precise images with words.*

Головна відмінність дієприкметника від звичайного прикметника полягає саме в джерелі походження цієї ознаки. Звичайний прикметник називає постійну, стабільну властивість предмета, яка зовсім не пов'язана з жодним процесом у часі. Наприклад, словосполучення «красивий сад» або «високий дуб» описують об'єкти, які мають ці якості постійно, від природи. Натомість дієприкметник виражає ознаку, яка виникає лише в результаті певної дії. Як зазначає підручник О. Заболотного для восьмого класу, дієприкметник виражає саме ознаку предмета за дією або станом. Словосполучення «квітучий сад» описує не просто гарне місце, а простір, який саме зараз перебуває у процесі інтенсивного цвітіння. Ця ознака тимчасова, вона жорстко прив'язана до конкретного моменту, коли дерева розкривають свої квіти. Такі слова, як «тремтячий», «зів'ялий», «вишитий» або «розквітлий», завжди ховають усередині себе маленьку історію про те, що саме відбувалося з цим предметом раніше чи відбувається зараз.

Усі дієприкметники в українській мові чітко поділяються на дві великі категорії залежно від того, хто саме виконує дію. Ці категорії називаються активними та пасивними дієприкметниками. Активні дієприкметники вказують на ознаку предмета, який самостійно виконує певну дію. Наприклад, коли ми кажемо «ревучий водоспад», ми чітко розуміємо, що водоспад сам виконує дію — він реве. Суб'єкт є повноцінним і активним учасником процесу. На противагу цьому, пасивні дієприкметники описують предмет, який зазнає на собі фізичної чи емоційної дії з боку когось іншого. Якщо перед нами «прочитана книга» або «збудований міст», це означає, що книгу хтось цілеспрямовано взяв і прочитав, а міст хтось спроєктував і збудував. Вони були лише пасивними об'єктами чиєїсь чужої діяльності. У цьому модулі ми зосередимося виключно на активних дієприкметниках, детально досліджуючи, як українська мова дозволяє предметам самим творити свої ознаки через власні динамічні дії.

:::info
**Граматична підказка**
Активний дієприкметник завжди можна перетворити на конструкцію «той, який виконує дію». Якщо «вогонь палає», то він — «палаючий». Якщо «листя опало», то воно — «опале».
:::

Щоб ніколи не плутати ці споріднені частини мови, використовуйте надійну логіку потрійної перевірки. Коли ви бачите нове слово, яке описує ознаку, поставте йому кілька уточнювальних запитань. Візьмемо для наочного прикладу три схожі слова: «тремтливий», «тремтить» та «тремтячий». Перше слово, «тремтливий», відповідає на питання «який?» і називає постійну рису об'єкта. Тому це звичайний прикметник, який не має ні часу, ні виду. Друге слово, «тремтить», відповідає на питання «що робить?», вказує на теперішній час, недоконаний вид і третю особу. Тому це чисте дієслово. А тепер уважно подивіться на третє слово — «тремтячий». Воно також відповідає на питання «який?» і узгоджується з іменником, але має дієслівний корінь та специфічний суфікс, який вказує на процес у теперішньому часі. Якщо слово відповідає на питання прикметника, але зберігає дієслівний корінь і суфікс часу, перед вами стовідсотковий дієприкметник. Цей простий, але ефективний алгоритм допоможе вам миттєво розпізнавати такі гібридні форми в будь-якому тексті.

<!-- INJECT_ACTIVITY: quiz-participle-definition -->

## Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)

Active participles of the present tense describe an action that the subject is performing right now. To form them, we must look at the verb's conjugation class, because this determines the suffix we will use. For verbs belonging to the first conjugation, the process is straightforward. You take the third-person plural form of the verb in the present tense, which usually ends in «-уть» or «-ють». Then, you simply drop the final «-ть» and replace it with the adjectival ending «-чий». The resulting suffix will be «-учий» or «-ючий». This mechanical transformation clearly shows how the verb's present tense stem merges with an adjectival ending to create a new word that acts like both. For instance, if you take the verb «читати», its third-person plural form is «читають». By dropping the ending, you get the stem «читаю-», to which you add «-чий», resulting in «читаючий». This formation mechanism is absolutely universal for all verbs of the first conjugation. From the verb «знати» we form the third-person plural «знають», and then transform it into the participle «знаючий». If we take the verb «існувати», we first get the form «існують», from which it is easy to form the word «існуючий». Likewise, from the word «працювати» the form «працюють» is created, which gives us the participle «працюючий». It is important to remember that these words decline by gender, number, and case exactly the same way as regular adjectives of the hard group.

Для дієслів другої дієвідміни логіка залишається такою ж, але голосні звуки в суфіксах змінюються відповідно до основи дієслова. Дієслова другої дієвідміни утворюють форму третьої особи множини із закінченнями «-ать» або «-ять». Коли ми відкидаємо кінцеве «-ть» і додаємо закінчення «-чий», у нас залишаються суфікси «-ачий» або «-ячий». Як зазначається у шкільному підручнику Олександра Заболотного для сьомого класу, цей чіткий поділ між дієвідмінами є єдиним надійним способом гарантувати, що ви використовуєте правильну голосну літеру в суфіксі дієприкметника. Ви не можете просто вгадувати між літерами «у» та «а»; ви повинні точно знати, як дієслово поводиться в теперішньому часі. Розгляньмо дієслово «лежати». Його форма третьої особи множини — «лежать». Дотримуючись нашого правила, ми забираємо останню частину і додаємо прикметникове закінчення, утворюючи слово «лежачий». Аналогічно дієслово «тремтіти» у множині стає «тремтять», яке потім перетворюється на активний дієприкметник «тремтячий». Іншим поширеним прикладом є слово «стояти», яке перетворюється на «стоять», а зрештою — на «стоячий».

> *For verbs of the second conjugation, the logic remains exactly the same, but the vowels in the suffixes change according to the verb stem. Second conjugation verbs form the third-person plural with the endings "-ать" or "-ять". When we drop the final "-ть" and add the ending "-чий", we are left with the suffixes "-ачий" or "-ячий". As noted in Oleksandr Zabolotnyi's seventh-grade school textbook, this clear division between conjugations is the only reliable way to ensure you are using the correct vowel in the participle's suffix. You cannot just guess between the letters "у" and "а"; you must know exactly how the verb behaves in the present tense. Let us consider the verb "лежати". Its third-person plural form is "лежать". Following our rule, we remove the last part and add the adjectival ending, forming the word "лежачий". Similarly, the verb "тремтіти" becomes "тремтять" in the plural, which then turns into the active participle "тремтячий". Another common example is the word "стояти", which turns into "стоять", and ultimately into "стоячий".*

While the mechanical rules for forming present active participles are clear and precise, their actual usage in modern Ukrainian is remarkably restricted. This is a crucial stylistic nuance that separates native-sounding Ukrainian from awkward, unnatural speech. In his eleventh-grade textbook, the prominent linguist Oleksandr Avramenko emphasizes that active participles of the present tense are generally not characteristic of the Ukrainian language. They often sound excessively bookish, archaic, or, worst of all, like direct calques from Russian, where such forms are extremely common and neutral. When a learner overuses words like «читаючий» or «йдучий», the sentence instantly feels heavy and artificial to a native speaker. Instead of using these participles, Ukrainian strongly prefers descriptive clauses starting with the words «який» or «що». Rather than saying «читаючий учень», a native speaker will almost always say «учень, який читає». However, this restriction is not absolute. Over centuries, a specific subset of these participles has broken away from their verb origins and seamlessly integrated into the language as regular adjectives. These lexicalized forms, such as «співучий» or «палючий», no longer describe a temporary action but rather a permanent, inherent quality of the noun.

Ці лексикалізовані форми є природними для сучасної української мови, оскільки вони втратили своє значення тимчасового процесу. Вони перетворилися на звичайні прикметники, які називають постійну ознаку предмета. Наприклад, коли ми говоримо про «пекучий біль», ми не маємо на увазі біль, який виконує дію просто зараз. Ми описуємо саму природу цього болю, його інтенсивність та характер. Так само вислів «киплячий чайник» став усталеною назвою для приладу в певному стані, а не просто описом води, яка нагрівається в дану секунду. Ще яскравішим прикладом є відоме українське прислів'я: «Під лежачий камінь вода не тече». Слово «лежачий» тут не описує камінь, який раптом вирішив лягти й відпочити. Воно позначає нерухомий, пасивний об'єкт, який ніколи не змінює свого положення. Саме через цю сталість ознаки такі слова, як «квітучий сад» або «ревучий водоспад», сприймаються носіями мови як гарні, поетичні та стилістично бездоганні конструкції. Вони додають тексту емоційної виразності та образності, не порушуючи при цьому внутрішніх законів української граматики.

Understanding when and where to use these present active participles requires a strong sense of linguistic register. The acceptability of a participle often depends entirely on whether you are writing a medical textbook, reciting poetry, or chatting with a friend over coffee. In specialized scientific or technical literature, certain active participles are preserved as strict, standardized terminology. For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and clinical records might describe «лежачі хворі» (bedridden patients). In these highly formalized contexts, the need for a concise, single-word term overrides the general stylistic preference for descriptive clauses. However, this scientific tolerance does not translate to everyday colloquial speech. If you are describing a noisy situation in a park, saying «кричаща дитина» or «бігучий хлопчик» is completely unacceptable. These forms sound incredibly unnatural and foreign. Instead, conversational Ukrainian demands the descriptive relative clause: «дитина, яка кричить» or «хлопчик, що біжить». 

:::info
**Граматична підказка**
When in doubt, always default to a descriptive clause with «який» or «що». It is the safest, most natural, and most universally accepted way to express an ongoing action performed by a subject in modern Ukrainian.
:::

Furthermore, even among the suffixes themselves, there is a subtle hierarchy of naturalness. Participles formed with «-учий» or «-ючий» have integrated much more deeply into the core vocabulary of the language when describing permanent traits, often losing their verb-like qualities entirely to become true adjectives. They sound inherently Ukrainian when used correctly. On the other hand, attempting to force new formations with these suffixes to describe temporary actions will almost always trigger stylistic alarms, as they frequently turn out to be awkward bureaucratic calques that need immediate replacement.

<!-- INJECT_ACTIVITY: fill-in-present-formation -->
<!-- INJECT_ACTIVITY: match-up-definitions -->

## Активні дієприкметники минулого часу (-л-)

While present active participles are heavily restricted and often sound foreign in modern Ukrainian, past active participles are completely natural, highly productive, and stylistically neutral. You will encounter them constantly in both classical literature and everyday colloquial speech. These participles elegantly describe an object based on an action it has already independently completed. To form them, you must start with a perfective verb (дієслово доконаного виду), because the inherent meaning relies on the action being definitively finished. The morphological process is remarkably straightforward. You take the infinitive form of the perfective verb and isolate the stem by dropping the standard «-ти» ending. Then, you simply add the suffix «-л-» followed by the appropriate adjective ending. For example, if we take the verb «посивіти» (to turn grey), we drop the «-ти» to get the stem «посиві-». Then, we attach the suffix «-л-» and the masculine ending «-ий» to create the participle «посивілий» (grey-haired). Similarly, the verb «змарніти» (to become emaciated or to waste away) becomes «змарнілий». This simple addition of the «-л-» suffix allows you to concisely describe a noun's new state resulting from its own past action.

There is one important phonetic rule to remember when forming these past active participles, as Ukrainian heavily favors fluid pronunciation. Many perfective verbs in Ukrainian end in the suffix «-нути», which frequently denotes a single, sudden, or successfully completed action. According to standard morphological rules, when you form a past active participle from such verbs, the entire «-ну-» suffix must be dropped from the infinitive stem. This prevents the resulting word from sounding clumsy, overly long, or difficult to pronounce. Let us look at the verb «зів'янути» (to wilt). We do not say «зів'янутий» or «зів'янулий», as these forms violate phonetic norms. Instead, we drop the «-ну-» to get the simplified stem «зів'я-», add the suffix «-л-», and arrive at the elegant and correct form «зів'ялий». The exact same rule applies to verbs like «розквітнути» (to blossom) and «змерзнути» (to freeze). Dropping the «-ну-» gives us «розквітлий» and «змерзлий». For verbs without this suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) becomes «збанкрутілий», as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon is a fundamental feature of natural Ukrainian morphology. It is detailed extensively in standard reference materials, such as Oleksandr Avramenko's Grade 7 textbook. It ensures the language remains melodic and flows easily in spoken contexts.

Семантичне значення цих дієприкметників дуже чітке: вони завжди вказують на повністю завершену зміну стану. Предмет уже виконав дію в минулому, і тепер ми бачимо лише її результат. Наприклад, «пожовклий листок» — це листок, який уже закінчив процес зміни кольору і став жовтим. Це суттєво відрізняється від форми «жовтіючий», яка б означала листок, що змінює колір просто зараз. Українська мова любить точність, тому для опису результату дії ми завжди обираємо минулий час. Ще один яскравий приклад — слово «зниклий» (від дієслова «зникнути»). Ми використовуємо його, щоб описати людину чи предмет, яких уже немає на місці.

> *The semantic meaning of these participles is very clear: they always indicate a completely finished change of state. The object has already performed the action in the past, and now we only see its result. For example, «пожовклий листок» is a leaf that has already finished the process of changing color and has become yellow. This differs significantly from the form «жовтіючий», which would mean a leaf that is changing color right now. The Ukrainian language loves precision, so to describe the result of an action, we always choose the past tense. Another vivid example is the word «зниклий» (from the verb «зникнути»). We use it to describe a person or an object that is no longer in its place.*

Because past active participles function syntactically like adjectives, they must decline to match the noun they modify in gender, number, and case. Fortunately, their declension paradigm is predictable and requires no new memorization. They follow the exact same pattern as regular adjectives belonging to the hard group (тверда група), such as «добрий» or «новий». This means they take the standard endings across all seven Ukrainian cases. Let us examine the complete declension paradigm using the participle «зів'ялий» (wilted) across masculine, feminine, neuter, and plural forms.

| Відмінок (Case) | Чоловічий рід (m) | Жіночий рід (f) | Середній рід (n) | Множина (pl) |
| :--- | :--- | :--- | :--- | :--- |
| **Називний (N.)** | зів'ялий | зів'яла | зів'яле | зів'ялі |
| **Родовий (G.)** | зів'ялого | зів'ялої | зів'ялого | зів'ялих |
| **Давальний (D.)** | зів'ялому | зів'ялій | зів'ялому | зів'ялим |
| **Знахідний (A.)** | зів'ялий/ого | зів'ялу | зів'яле | зів'ялі/их |
| **Орудний (I.)** | зів'ялим | зів'ялою | зів'ялим | зів'ялими |
| **Місцевий (L.)** | (на) зів'ялому/ім | (на) зів'ялій | (на) зів'ялому/ім | (на) зів'ялих |

:::info
**Граматична підказка**
In the Accusative case (Знахідний відмінок) for masculine and plural forms, the ending depends on whether the noun is animate or inanimate. If you are describing a person, like «потерпілий» (a victim), use the Genitive ending («потерпілого»). For inanimate objects, like «опалий листок», use the Nominative ending («опалий»).
:::

Notice how the feminine form takes «-ої» in the Genitive case and «-ою» in the Instrumental case, behaving exactly like a standard hard-stem adjective. The neuter form mirrors the masculine in almost all oblique cases, differing primarily in the Nominative and Accusative. When you encounter plural participles like «почорнілі» or «опалі» (fallen), they will reliably take «-их» in the Genitive and Locative cases, and «-ими» in the Instrumental. By treating these participles simply as regular hard-group adjectives, you can seamlessly integrate them into any sentence structure without having to second-guess the endings.

<!-- INJECT_ACTIVITY: essay-response-nature -->

## Чого уникати: русизми у дієприкметниках

The Ukrainian language has its own unique path of development, which means its grammatical structure differs significantly from Russian. One of the most glaring markers of Russian influence—often referred to as Surzhyk—is the use of the suffixes **-вш-** and **-ш-** to form past active participles. Words like «сказавший» and «прийшовший» are completely alien to Ukrainian morphology, even though you might frequently hear them in casual, mixed speech. As noted in the standard school curriculum (e.g., O. Glazova, Grade 11, p. 72), these forms are a gross violation of the literary norm. They are direct calques from Russian that must be entirely eradicated from your speech. In Ukrainian, we do not use these suffixes to create participles under any circumstances. Recognizing and avoiding these unnatural forms is a crucial step in speaking authentic, decolonized Ukrainian. When you hear someone say «учень, зробивший завдання», it immediately signals a lack of proficiency in the literary language. True Ukrainian grammar relies on entirely different mechanisms to convey these past actions.

Since we cannot use forms like «зробивший», and even many present active participles like «читаючий» are considered unnatural, how do we express these ideas? The most common and natural strategy in Ukrainian is the descriptive clause, known as **описовий зворот**. Instead of trying to force a verb into an awkward adjective-like form, we simply use a relative pronoun—typically «який» or «що»—followed by a regular conjugated verb in the appropriate tense. For example, instead of the artificial «читаюча дівчина», a native speaker will naturally say «дівчина, яка читає». This structure is highly productive, elegant, and stylistically neutral, making it perfect for both everyday conversation and formal writing. If you want to say "the students who finished the test," you completely avoid the banned **-вш-** suffix and simply say «студенти, які закінчили тест». Replacing suspicious present active participles with an **описовий зворот** is always the safest, most authentic, and grammatically impeccable choice.

Another essential strategy for purifying your vocabulary involves replacing active participles with dedicated nouns or standard adjectives. Many words ending in **-учий** or **-ячий** have direct, proper noun equivalents in Ukrainian that sound much more professional. For instance, the calque «керуючий» must be replaced with the official professional title «керівник» (manager). Similarly, «завідуючий» is correctly translated and used as the noun «завідувач». We also frequently replace these participles with adjectives that carry a specific semantic nuance. A classic example is the word «діючий». While you might hear it often in Surzhyk, the correct Ukrainian term for "current" or "valid," such as in «діючий закон», is the adjective «чинний». Furthermore, pay close attention to words describing purpose versus an ongoing action. The participle «миючий» describes something that is actively washing right now, whereas the adjective «мийний» describes the intended purpose of an object. Therefore, "detergent" is never «миючий засіб», but rather «мийний засіб».

:::info
**Граматична підказка**
Whenever a specialized noun exists to denote a profession or role (like «керівник» or «завідувач»), the Ukrainian language will always prefer it over an active participle.
:::

Заміна неприродних дієприкметників на питомі українські слова робить ваше мовлення деколонізованим, живим та справді автентичним. Існує ціла група слів, які ми називаємо «хибними друзями». Це типові кальки, які дуже міцно вкорінилися в щоденному спілкуванні через тривалий вплив російської мови на український мовний простір. Наприклад, слово «слідуючий» ніколи не використовується для позначення порядку в черзі чи послідовності подій; єдиний правильний варіант — це прикметник «наступний». Так само рішуче уникайте слова «бажаючий». Якщо ви говорите про людину, яка має намір щось зробити, використовуйте чудове українське слово «охочий». Ще один поширений канцеляризм — це «лідируючий», який надзвичайно легко замінюється на прикметник «провідний». Свідома відмова від цих кальок та перехід на питому лексику є беззаперечною ознакою високої мовної культури.

> *Replacing unnatural participles with native Ukrainian words makes your speech decolonized, lively, and truly authentic. There is a whole group of words that we call "false friends." These are typical calques that have become very firmly rooted in daily communication due to the prolonged influence of the Russian language on the Ukrainian linguistic space. For example, the word «слідуючий» is never used to indicate order in a queue or a sequence of events; the only correct option is the adjective «наступний». Likewise, resolutely avoid the word «бажаючий». If you are talking about a person who intends to do something, use the wonderful Ukrainian word «охочий». Another common bureaucratic calque is «лідируючий», which is extremely easily replaced by the adjective «провідний». Consciously abandoning these calques and transitioning to native vocabulary is an undeniable sign of high linguistic culture.*

<!-- INJECT_ACTIVITY: error-correction-calques -->

## Дієприкметник у тексті

In documentaries, voice-over scripts often rely on active participles to create a vivid, flowing picture of the natural world. The narrator must describe ongoing actions and permanent characteristics of the environment simultaneously. However, to keep the Ukrainian language natural and avoid a heavy, bureaucratic tone, professional scriptwriters skillfully alternate between lexicalized active participles and descriptive clauses with the word «що». This rhythmic switching ensures the text remains poetic, dynamic, and grammatically impeccable.

> — **Оповідач:** Перед нами розгортаються Карпати. Квітучі луки ваблять своїм солодким ароматом, запрошуючи мандрівників. *(The Carpathians unfold before us. Blooming meadows entice with their sweet aroma, inviting travelers.)*
> — **Оповідач:** Зверніть увагу на оленя, що біжить крізь густий ранковий ліс. *(Pay attention to the deer running through the dense morning forest.)*
> — **Оповідач:** Його шлях пролягає туди, де спадає могутній ревучий водоспад. *(Its path lies where the mighty roaring waterfall cascades.)*
> — **Оповідач:** А високо в небі спокійно пливуть хмари, що мандрують над побілілими від снігу вершинами гір. *(And high in the sky calmly float clouds wandering above the snow-whitened mountain peaks.)*

Notice how the narrator uses «квітучі луки» (blooming meadows) and «ревучий водоспад» (roaring waterfall) as natural adjective-like participles. But when describing the animal in motion, the script switches to an active clause for «олень, що біжить» (a running deer). In Ukrainian, attempting to say «бігучий олень» would sound extremely unnatural and forced, whereas the descriptive clause paints a dynamic, living picture without violating the stylistic norms of the language.

Ukrainian classic literature offers the finest examples of how active participles — especially past tense forms with the suffix **-л-** — enhance the poetic imagery of the countryside. Writers use these forms to capture a state that has already been achieved, painting a still-life picture of nature settling into a new season or a new mood.

Читаючи твори видатних майстрів слова, таких як Михайло Коцюбинський або Михайло Стельмах, ми дуже часто натрапляємо на майстерне використання активних дієприкметників минулого часу. Вони допомагають авторам надзвичайно точно передати тонкі зміни в природі. Наприклад, Стельмах пише: «Солодким хлібом пахнуть стерні, і чуйно соняшник поверне пожовклу голову на схід». Слово «пожовклу» тут показує завершену дію: голова соняшника вже повністю змінила свій колір під впливом літнього сонця. Так само у Коцюбинського ми читаємо: «Стиха лущиться зерно з перестиглого колоса». Форма «перестиглого» підкреслює, що процес дозрівання вже остаточно закінчився, і природа готова віддати свої щедрі плоди. Ці дієприкметники настільки органічно вплітаються в текст, що роблять його мелодійним та виразним. Вони зовсім не обтяжують речення, як це часто роблять неприродні форми теперішнього часу, а навпаки — додають йому неперевершеної художньої глибини та глибокої емоційності. Письменники свідомо обирають саме ці форми, щоб створити ефект застиглої миті.

> *Reading the works of outstanding masters of the word, such as Mykhailo Kotsiubynsky or Mykhailo Stelmakh, we very often come across the masterful use of past active participles. They help the authors extremely accurately convey subtle changes in nature. For example, Stelmakh writes: "The stubble smells of sweet bread, and the sunflower sensitively turns its yellowed head to the east." The word "yellowed" here shows an absolutely completed action: the sunflower's head has already completely changed its color under the influence of the summer sun. Similarly, in Kotsiubynsky we read: "The grain quietly peels from the overripe ear." The form "overripe" emphasizes that the ripening process is finally finished, and nature is ready to yield its generous fruits. These participles weave into the text so organically that they make it melodic and expressive. They do not weigh down the sentence at all, as unnatural present tense forms often do, but on the contrary — they add unsurpassed artistic depth and deep emotionality to it. Writers consciously choose exactly these forms to create the effect of a frozen moment.*

The beauty of forms like «пожовклий» (yellowed) or «перестиглий» (overripe) lies in their ability to act purely as descriptive adjectives while carrying the full historical weight of the verb's action. They describe a permanent, observable state that resulted from a dynamic, transformative process, which is a hallmark of high-quality Ukrainian literary style.

The stylistic differences between natural Ukrainian and translated bureaucratic language become starkly apparent in technical or professional writing. Compare two versions of a formal business report to see how incorrect participle usage degrades the text.

Версія А (небажана): «Існуючий план показує, що домінуючий тренд на ринку вимагає термінових змін. Завідуючий відділом підкреслив, що оточуюче середовище є вкрай нестабільним».
Версія Б (правильна): «Наявний план показує, що панівний тренд на ринку вимагає термінових змін. Завідувач відділу підкреслив, що довкілля є вкрай нестабільним».

> *Version A (undesirable): "The existing plan shows that the dominating trend in the market requires urgent changes. The managing of the department emphasized that the surrounding environment is extremely unstable."*
> *Version B (correct): "The available plan shows that the prevailing trend in the market requires urgent changes. The head of the department emphasized that the environment is extremely unstable."*

Version A is heavily infected with Russian calques masquerading as active present participles. Words like «існуючий» (existing) and «домінуючий» (dominating) instantly reveal a lack of language proficiency and a heavy reliance on direct, word-for-word translation from other languages. Furthermore, the term «завідуючий» incorrectly treats a permanent professional title as an ongoing, temporary action, while the phrase «оточуюче середовище» is a famously clunky, unnatural construction.

Version B, on the other hand, demonstrates high linguistic culture and unquestionable professional competence. It completely replaces the clumsy participles with precise, native Ukrainian adjectives and nouns. We use «наявний» instead of the artificial «існуючий», and «панівний» instead of «домінуючий». The professional role is accurately named with the dedicated noun «завідувач», and the complex descriptive phrase is elegantly condensed into the single, beautiful native noun «довкілля» (environment). 

:::tip
**Did you know?**
In formal Ukrainian, switching from active present participles to dedicated nouns or adjectives is not just a stylistic preference — it is a strict requirement of the modern state standard for professional communication.
:::

When you write reports, emails, or academic papers, your choice of vocabulary strongly signals your command of the language. A native speaker reading Version A will immediately sense an artificial, translated tone. Version B flows naturally because it respects the fundamental principle of Ukrainian morphology: if a dedicated noun or adjective exists to describe a state or a role, it always overrides an active participle.

Understanding how to form and identify participles is only the first step; you must also know how to integrate them structurally into your sentences. Because participles answer the questions **який? яка? яке? які?**, they almost always function syntactically as attributes (означення). They modify a specific noun and agree with it completely in gender, number, and case.

Дієприкметник у реченні найчастіше виступає граматичним означенням і під час синтаксичного розбору підкреслюється хвилястою лінією. Він може стояти як безпосередньо перед іменником, так і відразу після нього. Якщо дієприкметник має при собі будь-які залежні слова, він утворює так званий дієприкметниковий зворот. Розглянемо класичний літературний приклад: «Гори, побілілі від снігу, виднілися вдалині». У цьому реченні головне слово — це іменник «гори». Активний дієприкметник минулого часу «побілілі» граматично узгоджується з ним у називному відмінку множини. Але він стоїть тут не сам: слова «від снігу» синтаксично залежать від дієприкметника, утворюючи цілу конструкцію, яка детально уточнює ознаку цих гір.

> *A participle in a sentence most often acts as a grammatical attribute and during syntactic parsing is underlined with a wavy line. It can stand either immediately before the noun or right after it. If a participle has any dependent words attached to it, it forms a so-called participial phrase. Take a classic literary example: "The mountains, whitened by the snow, were visible in the distance." In this sentence, the main word is the noun "mountains." The past active participle "whitened" grammatically agrees with it in the nominative case plural. But it does not stand alone here: the words "by the snow" syntactically depend on the participle, forming an entire construction that details the attribute of these mountains.*

When the participial phrase (дієприкметниковий зворот) comes after the noun it modifies, it is set off by commas in writing. This specific word order creates a beautifully structured, poetic sentence rhythm that is very often found in classic literature and formal writing, allowing writers to pack rich, descriptive information into a single, elegant sentence.

:::info
**Grammar box**
A **дієприкметниковий зворот** (participial phrase) is simply a participle along with any words that belong to it. We will explore the precise punctuation rules for these phrases in Module 59, but for now, remember that they offer a powerful way to pack rich, descriptive information into a single sentence.
:::

By observing active participles in context, you can truly see how they elevate the language. Whether you are reading a novel, analyzing a technical document, or watching a nature documentary, recognizing these forms allows you to appreciate the elegance and precision of authentic Ukrainian syntax.

<!-- INJECT_ACTIVITY: reading-comprehension-nature -->

## Підсумок

Дієприкметник — це форма, яка поєднує властивості дієслова та прикметника, виражаючи ознаку предмета за дією. У цьому модулі ми зосередилися на активних дієприкметниках — тих, що описують предмет, який сам виконує дію. Вони бувають теперішнього та минулого часу. Теперішній час утворюється за допомогою суфіксів **-уч- / -юч-** (перша дієвідміна) та **-ач- / -яч-** (друга дієвідміна). Минулий час утворюється від основи інфінітива неперехідних дієслів доконаного виду за допомогою суфікса **-л-**, причому суфікс **-ну-** зазвичай випадає (*зів'янути* → *зів'ялий*). Активні дієприкметники минулого часу є природними для української мови, тоді як форми теперішнього часу вимагають обережності.

> *A participle is a form that combines the properties of a verb and an adjective, expressing the attribute of an object by its action. In this module, we focused on active participles—those that describe an object that performs the action itself. They can be present and past tense. The present tense is formed using the suffixes **-уч- / -юч-** (first conjugation) and **-ач- / -яч-** (second conjugation). The past tense is formed from the infinitive stem of intransitive perfective verbs using the suffix **-л-**, and the suffix **-ну-** usually drops out (зів'янути → зів'ялий). Past active participles are absolutely natural for the Ukrainian language, while present tense forms require caution.*

When speaking and writing in Ukrainian, avoiding unnatural active participles is a strong indicator of your language proficiency. The legacy of Russian grammatical influence has left a habit of using calqued participle forms. To maintain the authenticity of your Ukrainian, you must apply a mental "Decolonization Checklist" before using an active participle of the present tense.

First, the suffixes for past active participles ending in *-вш-* and *-ш-* are strictly forbidden in modern standard Ukrainian. Words like *посинівший* or *сказавший* are severe errors and direct calques.

Second, be highly skeptical of forms ending in *-учий*, *-ючий*, *-ачий*, or *-ячий* when describing temporary actions. Instead of saying *діючий закон*, you must use the established adjective **чинний** (valid). Instead of *бажаючий*, use the noun **охочий** (willing person).

Finally, the most reliable strategy in Ukrainian is to replace problematic active participles with a subordinate clause starting with **який** (which) or **що** (that). A "reading student" is never *читаючий учень*, but always *учень, який читає*.

**Підсумкова таблиця: Утворення активних дієприкметників**

| Час | Основа | Суфікс | Приклад | Статус |
| :--- | :--- | :--- | :--- | :--- |
| **Теперішній** | I дієвідміна | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений (переважно сталі ознаки) |
| **Теперішній** | II дієвідміна | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений (переважно сталі ознаки) |
| **Минулий** | Інфінітив доконаного виду | **-л-** | *зникнути* → *зниклий* | Природний (поширений) |
| **Минулий** | Інфінітив із суфіксом -ну- | **-л-** (суфікс -ну- випадає) | *зів'янути* → *зів'ялий* | Природний (поширений) |

:::note
**Quick tip**
If you can replace an active participle with a normal adjective, a specific noun, or a simple subordinate clause without changing the meaning, you should always do it. Ukrainian prefers clear, descriptive phrasing over heavy, artificial participles.
:::

As we conclude this exploration of active participles, take a moment to evaluate your understanding. These forms are a bridge to advanced syntax, but they require a delicate touch. Ask yourself the following questions to ensure you have internalized the core concepts.

Чи відрізняю я дієприкметник від прикметника? Ви маєте розуміти, що прикметник позначає постійну ознаку, а дієприкметник — ознаку за дією. Чи правильно я утворюю минулий час? Пам'ятайте про зникнення суфікса «-ну-» при творенні слів на зразок «зів'ялий». Чи уникаю я русизмів на -учий? Ви повинні автоматично замінювати їх описовими зворотами зі словом «який» або питомими українськими словами.

> *Do I distinguish a participle from an adjective? You should understand that an adjective indicates a permanent attribute, while a participle indicates an attribute by action. Am I correctly forming the past tense? Remember the disappearance of the "-ну-" suffix when forming words like "зів'ялий". Am I avoiding Russianisms ending in -учий? You must automatically replace them with descriptive phrases using the word "який" or native Ukrainian words.*

In Module 58, we will explore passive participles. Unlike the active forms, passive participles are incredibly productive, completely natural, and absolutely essential for both everyday conversation and formal writing. You will see how the object receives the action, expressing the attribute of an object that has been acted upon, such as a read book (*прочитана книга*) or a built bridge (*збудований міст*). This opens up an entirely new dimension of Ukrainian sentence structure.

<!-- INJECT_ACTIVITY: match-up-term-definitions -->
<!-- INJECT_ACTIVITY: quiz-active-participles-review -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: participles-active
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

**Level: B1 (Module 65)**

**Instructions in Ukrainian.** All activity types appropriate.


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
