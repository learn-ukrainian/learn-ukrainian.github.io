<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/imperative-complete.yaml` file for module **44: Хай він прочитає!** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-3rd-person-imperative -->`
- `<!-- INJECT_ACTIVITY: unjumble-1st-person-plural -->`
- `<!-- INJECT_ACTIVITY: match-up-vocative-wishes -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the correct imperative — 3rd person with хай/нехай or 1st plural with
    -мо — from given infinitives
  items: 8
  type: fill-in
- focus: Choose the correct aspect (imperfective or perfective) for imperatives in
    various situations (general advice vs. specific command)
  items: 8
  type: quiz
- focus: Match Vocative + imperative + Instrumental combinations to create correct
    wishes (Оленко + будь + щасливою)
  items: 8
  type: match-up
- focus: Reorder words to form correct imperative sentences — commands, suggestions
    with -мо, and wishes with Vocative + будь + Instrumental
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спокійний (calm)
- уважний (attentive)
- живи (live — imperative)
- здійснитися (to come true)
- мрія (dream)
required:
- хай (let — particle for 3rd person imperative)
- нехай (let — formal variant)
- наказовий спосіб (imperative mood)
- побажання (wish, blessing)
- кличний відмінок (Vocative case)
- будь / будьте (be — imperative of бути)
- щасливий / щасливою (happy / happy — Instr.f.)
- здоровий / здоровими (healthy / healthy — Instr.pl.)
- ходімо (let's go)
- давайте (let's — suggestion particle)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ: На кухні з шеф-кухарем (~120 words)

> — **Шеф-кухар:** Усім добрий вечір! *(Good evening everyone!)* Сьогодні ми готуємо смачний український борщ. *(Today we are cooking delicious Ukrainian borscht.)* Друзі, **почнімо** *(let's start)*! Оксано, **наріжте** *(cut)* цибулю.
> — **Оксана:** Добре, шефе. Я вже ріжу. *(Okay, chef. I am already cutting.)*
> — **Шеф-кухар:** Чудово. Тепер чекаємо на бульйон. *(Great. Now we wait for the broth.)* **Хай** *(let)* вода закипить швидше. А ви, Максиме, робіть засмажку. *(And you, Maksym, make the sauté.)*
> — **Максим:** Я додав томатну пасту. Що далі? *(I added tomato paste. What next?)*
> — **Шеф-кухар:** **Нехай** *(let)* соус настоїться десять хвилин. Це дуже важливо для гарного смаку. *(This is very important for good taste.)* Потім ми все змішаємо. *(Then we will mix everything.)* **Помішаймо** *(let's stir)* разом! Оксано, **будь уважною** *(be attentive)*, ніж дуже гострий.
> — **Оксана:** Дякую, я обережна. *(Thank you, I am careful.)*
> — **Шеф-кухар:** Усі молодці! *(Everyone is doing great!)* **Хай** наш борщ буде найсмачнішим! *(May our borscht be the most delicious!)*


## Хай і нехай: Наказ для третіх осіб

Зазвичай ми звертаємося прямо до людини, з якою ми спілкуємося. Ми кажемо: «**Скажи** *(tell)* йому!», «**Зробіть** *(do)* це!», «**Слухай** *(listen)* уважно!». Ми використовуємо форми для «ти» або «ви». Але іноді нам потрібен наказ або побажання для іншої людини. Ми хочемо сказати про «нього», «неї» або «них». When we want to give an indirect command or express a wish for a third party, we use the third-person imperative. В українській мові ми використовуємо спеціальні слова для цього. Ми кажемо: «Хай він скаже!». Це дуже популярна конструкція в розмовній мові. We do not change the verb itself, but rather add a specific particle before it to show our intent. This is a very common structure in daily conversations and formal writing.

Як ми утворюємо цей наказ? Це дуже просто. Ми беремо слово «хай» або «нехай» і додаємо дієслово у формі третьої особи. To form the third-person imperative, use the particle "хай" or "нехай" followed by the verb in the third-person present or future tense. Слово «хай» ми часто використовуємо щодня, коли говоримо з друзями. Воно коротке і зручне. Слово «нехай» — це більш офіційний, літературний варіант. Ви часто бачите його в книгах або офіційних документах. Вони означають абсолютно одне і те ж. The verb after "хай" or "нехай" is always in its normal third-person form (he/she/it/they). You only need to know the regular present or future tense conjugation, and you can easily create these commands.

Наприклад:
* «Хай він **читає** *(reads)*».
* «Нехай вона **знає** *(knows)*».
* «Хай вони **прийдуть** *(will come)*».

Коли ми використовуємо ці слова? Вони мають кілька важливих функцій у нашому житті. По-перше, це **дозвіл** *(permission)*. Наприклад, ви не проти, щоб людина щось зробила.
«Хай він **іде** *(goes)*, я не проти».

По-друге, це непрямий **наказ** *(command)*. Ви кажете одній людині передати наказ іншій людині. Це дуже корисно на роботі або в школі.
«Нехай вони **зачекають** *(wait)* у коридорі».

По-третє, це **побажання** *(wishes)* або тости. Це дуже важлива частина української культури. Ми часто бажаємо щось хороше іншим людям на свята.
«Хай вам **щастить**!» *(good luck to you!)*.
«Нехай **здійсняться** *(come true)* ваші **мрії** *(dreams)*!».

In all these cases, the grammatical structure is completely identical. The particle does the work of turning a regular statement of fact into a command, a permission, or a warm wish. This makes it a very flexible tool.

Дієслово завжди залежить від суб'єкта. Якщо ми говоримо про одну людину, дієслово має форму однини. Якщо ми говоримо про багатьох людей, дієслово має форму множини. The verb must always agree with the subject in number, just like in any regular sentence.

Наприклад, ми говоримо про одну **дитину** *(child)*:
«Хай дитина **грається** *(plays)*».

Але якщо ми говоримо про багатьох дітей, ми обов'язково змінюємо форму дієслова:
«Хай **діти** *(children)* граються на вулиці».
«Нехай **батьки** *(parents)* **відпочинуть** *(rest)* вдома».

This rule is strict and very logical. You cannot use a singular verb with a plural subject after these imperative particles. If the subject changes to plural, the verb must also change.

Ми можемо використовувати дієслова **недоконаного** *(imperfective)* або **доконаного** *(perfective)* виду. Це дуже сильно змінює нюанс нашого наказу. "Хай" with an imperfective verb in the present tense describes an ongoing, repeated, or general action. "Хай" with a perfective verb in the future tense implies a specific, completed result that we urgently want to happen.

Порівняйте ці речення:
* «Хай він **пише** *(writes)* **щодня** *(every day)*». Це недоконаний вид, регулярна дія.
* «Хай він **напише** *(will write)* цей лист сьогодні». Це доконаний вид, ми хочемо конкретний результат.
* «Нехай вона **читає** *(reads)* цю книгу довго».
* «Хай вона **прочитає** *(will read)* цей текст зараз».

This aspect distinction helps you be extremely precise about what kind of action you are commanding or wishing for. It shows whether you care about the process or the final result.

<!-- INJECT_ACTIVITY: fill-in-3rd-person-imperative -->


## Читаймо! Ходімо! Перша особа множини

Коли ми хочемо щось робити разом з іншими людьми, ми використовуємо спеціальну форму. We use the first-person plural imperative to invite others to act with us. Це точний граматичний еквівалент англійського «Let's...». Щоб утворити цю форму, ми беремо дієслово для другої особи однини. Потім ми просто додаємо суфікс **-мо**. The grammatical formation is wonderfully simple: just take the familiar "you" command form and attach the "-мо" suffix to the end. Наприклад: дієслово «**читати**» *(to read)* має форму «**читай**» *(read)*. Ми додаємо суфікс і маємо «**читаймо**» *(let's read)*. Дієслово «**робити**» *(to do)* має форму «**роби**» *(do)*. Разом це буде «**робімо**» *(let's do)*. А дієслово «**бути**» *(to be)* має форму «**будь**» *(be)*, тому ми кажемо «**будьмо**» *(let's be)*. Це дуже красива, формальна і природна українська конструкція. This is the authentic, elegant way to suggest a shared action or activity in the Ukrainian language.

У щоденному житті ми дуже часто використовуємо ці короткі слова. The absolute most common form you will hear every day is «**ходімо**!» *(let's go!)*. На жаль, на вулицях люди іноді кажуть «**пішли**» *(we went)*, коли кличуть друзів кудись іти. Але це помилка, бо «пішли» — це форма минулого часу, а не наказ. But "пішли" is grammatically the past tense, making it a colloquial error when used for an invitation. Завжди кажіть правильно: «Ходімо в кіно!» або «Ходімо додому!». Ось ще кілька дуже корисних фраз для щоденного спілкування на роботі чи вдома: «**Починаймо**!» *(Let's start!)*. «**Поговорімо** про це пізніше» *(Let's talk about it later)*. «**Зробімо** це важке завдання!» *(Let's do this hard task!)*. «**Поїдьмо** на море влітку!» *(Let's go to the sea in summer!)*. Ці слова роблять вашу мову дуже живою та природною.

Тепер ми обов'язково маємо поговорити про одну важливу проблему — це використання слова «**давайте**» *(let's)*. In the Russian language, it is the standard rule to say "Let's + infinitive verb" to form a group command. Через тривалий історичний вплив багато людей в Україні теж кажуть: «Давайте читати» або «Давайте працювати». Але в літературній українській мові це велика помилка і типова **калька** *(calque)*. You must explicitly avoid using "давайте" with an infinitive verb in Ukrainian. Правильно казати тільки автентичні українські форми з суфіксом: «Читаймо!» або «**Працюймо**!» *(Let's work!)*. Однак, є один допустимий компромісний варіант у повсякденній розмовній мові. However, in casual, everyday speech, you might hear "давайте" followed by the normal future tense form, like «Давайте **поїдемо**» *(Let's go)* або «Давайте купимо». This is considered a softer, slightly more colloquial suggestion. Але пам'ятайте, що найкращий, найчистіший і найправильніший варіант — це завжди український суфікс «-мо».

Вид дієслова також дуже важливий для цих спільних наказів і пропозицій. Aspect also matters deeply when we invite people to do things together. **Недоконаний вид** *(imperfective aspect)* означає загальну, регулярну дію або постійний процес. «Працюймо разом щодня!». «Читаймо хороші українські книги!». «**Співаймо** *(let's sing)* українські пісні кожного свята!». **Доконаний вид** *(perfective aspect)* означає один конкретний результат або одну швидку мету. «Зробімо цей важливий **проєкт** *(project)* сьогодні!». «**Купімо** *(let's buy)* ці квитки зараз!». «**Напишімо** *(let's write)* цей короткий лист!».

Ось невелика таблиця найпопулярніших щоденних дієслів у цій корисній формі. Here is a helpful summary table of common verbs in the first-person plural imperative form for your reference:
*   «**Пити**» *(to drink)* ➡️ «**Пиймо**!» *(Let's drink!)*
*   «**Іти**» *(to go on foot)* ➡️ «Ходімо!» *(Let's go!)*
*   «**Брати**» *(to take)* ➡️ «**Берімо**!» *(Let's take!)*
*   «**Дивитися**» *(to watch)* ➡️ «**Дивімося**!» *(Let's watch!)*

<!-- INJECT_ACTIVITY: unjumble-1st-person-plural -->


## Кличний + наказовий + орудний: Побажання (~550 words)

В українській мові є дуже красива і важлива конструкція для **побажання** *(wish, blessing)*. We often use a specific rhythmic pattern for wishes, greetings, and blessings. Ми поєднуємо **кличний відмінок** *(Vocative case)*, **наказовий спосіб** *(imperative mood)* та орудний відмінок. This powerful grammatical combination uses the Vocative case to address the person directly. It uses the imperative mood to command the state. Finally, it uses the Instrumental case to define exactly what that state is. Наприклад: «**Мамо** *(Mom)*, **будь** *(be)* **щасливою** *(happy)*!». You are literally commanding someone to exist in a specific, positive state of being. Це звучить дуже тепло, емоційно і природно. Ми активно використовуємо цю граматичну форму на всі свята і кожного дня. Зрозуміти цю логіку означає зрозуміти українську душу. 

Щоб побажання звучало щиро і поважно, ми завжди маємо правильно кликати людину. The direct address must always be strictly in the Vocative case for the wish to sound natural. Згадаймо базові форми для популярних імен та родичів. Let's quickly review the basic Vocative forms for names and family members. Іменник жіночого роду «**Олена**» *(Olena)* має теплу форму «**Оленко**» *(Olenko)*. Слово «**тато**» *(dad)* змінюється на форму «**тату**» *(tatu)*. Слово «**друг**» *(friend)* має відому форму «**друже**» *(druzhe)*. А форма множини для слова «**друзі**» *(friends)* або «**колеги**» *(colleagues)* завжди залишається такою ж. У кличному відмінку ми просто кажемо: «друзі», «колеги». Коли ми кажемо «Оленко, будь щасливою» або «Тату, будь здоровим», ми показуємо нашу велику повагу. Using the standard Nominative case here sounds unnatural and slightly rude in Ukrainian.

Після дієслова «будь» або «**будьте**» *(be)* ми використовуємо прикметники саме в орудному відмінку. The Instrumental case answers the question "to be what or to be who?". Для чоловічого роду ми маємо закінчення «-им». Наприклад: «будь **здоровим**» *(healthy)*, «будь **спокійним**» *(calm)*. Для жіночого роду ми використовуємо гарне закінчення «-ою». Наприклад: «будь щасливою», «будь здоровою». У множині або для ввічливої форми на «ви» ми завжди додаємо закінчення «-ими». For plural groups or polite, formal addresses, we use the ending "-ими". Ми радісно кажемо: «Друзі, будьте **успішними** *(successful)*!». Або ми можемо сказати дітям: «**Діти** *(children)*, будьте **уважними** *(attentive)*!». Ця граматична структура робить ваші слова ідеальними. It shows that you are actively wishing them a continuous state of success or health.

Ці щирі побажання — це не просто граматика. Це дуже важлива частина української культури та глибоких традицій. These phrases and structures are essential social tools in Ukraine. Ми часто говоримо їх на дні народження або під час теплих зустрічей. We use them during birthdays, national holidays, or regular social gatherings. Традиційний український святковий тост звучить дуже коротко і сильно: «Будьмо!». It is a powerful one-word toast that literally means "Let us be". Інша дуже популярна щоденна фраза — це «Будьте здорові!». Люди часто кажуть це, коли хтось чхає, або коли гості йдуть додому. Також ми часто кажемо: «**Живи** *(live)* довго!». Notice that in this specific, fixed phrase "Будьте здорові", we often use the Nominative plural instead of the Instrumental. It is a frozen historical idiom. Але для нових, персональних побажань ми завжди беремо орудний відмінок.

Ми також можемо поєднувати частку «**хай**» *(let)* з кличним відмінком. We can also combine the particle "хай" with Vocative addresses to create indirect blessings. У таких реченнях дія часто спрямована на людину. Тому ми додаємо займенники у давальному відмінку. We use the Dative case pronouns "тобі" or "вам" to show exactly who receives the positive action. Наприклад: «Друже, хай тобі **щастить** *(to be lucky)*!». This translates beautifully as: "May luck happen to you, my friend!". Інший дуже гарний і популярний приклад для свята: «Діти, **нехай** *(let)* **здійсняться** *(come true)* всі ваші **мрії** *(dreams)*!». Тут ми кличемо дітей. А потім ми використовуємо форму третьої особи для слова «мрії». These elegant combinations make your Ukrainian sound native, warm, and deeply respectful in any situation.

<!-- INJECT_ACTIVITY: match-up-vocative-wishes -->


## Вид дієслова в наказовому способі

Ми знаємо, що українські дієслова мають два види: недоконаний і доконаний. We know that Ukrainian verbs have two aspects: imperfective and perfective. Ця різниця дуже важлива, коли ми використовуємо наказовий спосіб. This difference is very important when we use the imperative mood. Дієслова недоконаного виду показують процес або регулярну дію. Imperfective verbs show a process or a habitual action. Тому ми використовуємо їх для загальних порад. Therefore, we use them for general advice. Наприклад, ми кажемо: «**Читай** *(read)* більше!». Також ми використовуємо їх для постійних дій. We also use them for constant actions: «**Пишіть** *(write)* коментарі щодня!». Ще одна важлива функція — це ввічливі запрошення. Another important function is polite invitations. Коли приходять гості, ми привітно кажемо: «**Сідайте** *(sit down)*, будь ласка» або «**Проходьте** *(come in)*». Using the imperfective aspect for invitations makes the command sound softer, like a welcoming suggestion rather than a strict order.

Дієслова доконаного виду мають іншу мету. Perfective verbs have a different purpose. Ми використовуємо їх, коли нам потрібен конкретний результат. We use them when we need a specific result. Perfective imperatives are used for specific, direct commands where a clear outcome is expected. Наприклад, вчитель каже студенту: «**Прочитай** *(read through)* цю статтю!». Це означає, що текст треба прочитати до кінця. This means the text must be read to the end. Або друг може сказати вам: «**Напиши** *(write)* мені СМС!». Він хоче отримати одне повідомлення. He wants to receive one message. Якщо в кімнаті холодно, ми просимо: «**Закрий** *(close)* вікно!». Це разова дія, яка дає швидкий результат. This is a one-time action that gives a quick result.

Коли ми хочемо заборонити щось робити, ми використовуємо слово «не». When we want to forbid doing something, we use the word "не". Загальне правило дуже просте: завжди використовуйте дієслова недоконаного виду для заборон. The general rule is very simple: always use imperfective verbs for prohibitions. Мама каже сину: «Не **відкривай** *(open)* вікно!». Подруга радить: «Не пиши йому!». We use the imperfective aspect here because we want the person to completely avoid the process. The action should never start. Чи можемо ми використовувати доконаний вид після слова «не»? Can we use the perfective aspect after the word "не"? Так, але це буває рідко. Yes, but this is rare. Using the perfective with "не" acts as a sharp warning against an accidental result. Ми кричимо дитині: «Не **впади** *(fall)*!». Ми попереджаємо про раптову небезпеку. We are warning about a sudden danger.

Давайте підсумуємо різницю між двома видами у наказах. Let's summarize the difference between the two aspects in commands. The choice between imperfective and perfective depends on the context. Are you talking about "always" and "in general", or about "now" and "this specific thing"? 

| Недоконаний вид (Imperfective) | Доконаний вид (Perfective) |
| :--- | :--- |
| **Пиши!** *(Keep writing!)* | **Напиши!** *(Get it written!)* |
| Процес або регулярна дія. | Конкретний результат або разова дія. |
| Process or habitual action. | Specific result or one-time action. |
| Загальна порада. | Чіткий наказ. |
| General advice. | Clear command. |
| Ввічливе запрошення. | Термінова вимога. |
| Polite invitation. | Urgent request. |
| Заборона (з часткою «не»). | Попередження (з часткою «не»). |
| Prohibition (with the particle "не"). | Warning (with the particle "не"). |

Ми кажемо: «Читай українські книги щодня». We say: "Read Ukrainian books every day". Це корисна звичка. This is a useful habit. Але ми кажемо: «Прочитай цей текст зараз». But we say: "Read this text now". Це вже конкретне завдання. This is a specific task.

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->


## Підсумок

Отже, сьогодні ми вивчили багато нових корисних правил. Наказовий спосіб в українській мові — це не тільки наказ для слова «ти». The imperative mood isn't just for the second person. Ми використовуємо українські частки **«хай»** або **«нехай»** *(let)* для інших людей. Або ми додаємо коротке закінчення **«-мо»** *(let's)*, коли ми хочемо щось робити разом. Також ми тепер знаємо золоте правило для щирих українських побажань. Remember the golden rule for wishes: Address the person in the Vocative case + use "Be" in the Imperative + put the State in the Instrumental case. Наприклад: «**Оленко** *(Olenka)*, **будь** *(be)* завжди **щасливою** *(happy)*!».

Тепер **перевірімо** *(let's check)* ваші нові знання. Ask yourself these three questions to see your progress:

1. Can I tell someone "let's go" together without using a Russianism?
Я точно пам'ятаю, що треба казати «**ходімо**» *(let's go)*, а не «пішли»?
2. Do I know how to wish a friend luck using the particle "хай"?
Я можу сміливо сказати другові: «**Хай** тобі завжди **щастить** *(good luck)*!»?
3. Can I form kind wishes with the verb "to be" correctly?
Я добре розумію, чому ми кажемо «будь **здоровим** *(healthy)*», а не просто «будь здоровий»?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: imperative-complete
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

**Level: A2 (Module 44/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
