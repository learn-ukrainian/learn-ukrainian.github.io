<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/because-and-although.yaml` file for module **47: Тому що, бо, хоча** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-cause-clauses -->`
- `<!-- INJECT_ACTIVITY: match-up-cause-concession -->`
- `<!-- INJECT_ACTIVITY: unjumble-complex-sentences -->`
- `<!-- INJECT_ACTIVITY: quiz-cause-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-conjunctions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct conjunction (тому що, бо, хоча, але) to complete sentences
  items: 8
  type: quiz
- focus: Complete compound sentences by adding the missing clause after the conjunction
  items: 8
  type: fill-in
- focus: Match two halves of sentences — причина with наслідок, допуст with результат
  items: 8
  type: match-up
- focus: Sort conjunctions into причина (тому що, бо) vs. допуст (хоча) vs. протиставлення
    (але, проте, однак)
  items: 8
  type: group-sort
- focus: Reorder words to form correct compound sentences with тому що, бо, and хоча
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- допуст (concession)
- зате (but then, on the other hand)
- навпаки (on the contrary)
- незважаючи на (despite)
required:
- тому що (because)
- бо (because — colloquial)
- хоча (although, even though)
- але (but)
- проте (however, yet)
- однак (however)
- причина (reason, cause)
- сполучник (conjunction)
- складне речення (complex sentence)
- тому (therefore, that is why)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ та діалог

> — **Студент 1:** Привіт. Я сьогодні не піду в університет, **бо** *(because)* дуже втомився після роботи. Я працював до пізньої ночі.
> — **Студент 2:** Привіт. Але тобі обов'язково треба йти сьогодні. Ти що, забув про наш розклад?
> — **Студент 1:** А що там сьогодні таке? Чому я маю йти на цю пару?
> — **Студент 2:** Тобі треба бути там, **тому що** *(because)* завтра буде дуже важлива **контрольна** *(test)* з історії.
> — **Студент 1:** Ох, я зовсім забув про неї. Але я так хочу спати зараз.
> — **Студент 2:** Розумію тебе. Слухай, **хоча** *(although)* я теж дуже втомився, я все одно піду. Ця **лекція** *(lecture)* буде дуже корисна.
> — **Студент 1:** Добре, ти маєш рацію. Я зараз вип'ю велику чашку кави і теж піду на заняття.

Прості речення — це добре для початку, але на рівні А2 цього вже замало. Вам треба вміти будувати довгі та складні речення. Ви маєте пояснювати свої дії та думки. Для цього вам потрібна **причина** *(reason)* та **допуст** *(concession)*. Ці маленькі слова роблять вашу мову дуже живою та природною. Сьогодні ми навчимося з'єднувати різні ідеї в одне ціле. Ми будемо активно використовувати сполучники «тому що», «бо» та «хоча».

## Чому? Тому що... / Бо... (Why? Because...)

Ми часто запитуємо людей про різні речі. Ми хочемо знати причини подій та дій. Для цього ми використовуємо слово **чому** *(why)*. Коли ми відповідаємо, ми називаємо **причину** *(cause, reason)*. В українській мові є два головні слова для цього. Це слова «тому що» та «бо». Обидва слова означають одне і те саме. Вони з'єднують дві ідеї в одне логічне речення. Наприклад, ви можете сказати: «Я вдома, бо сьогодні дощ». Або ви можете сказати: «Я вдома, тому що сьогодні дощ». Це дуже проста і корисна граматика. In English, you generally use one main word for this purpose: "because". В українській мові ми маємо вибір. Ви можете вільно обрати те слово, яке вам більше подобається.

Яка різниця між цими словами? Усе залежить від вашої ситуації та стилю спілкування. The word «бо» is the workhorse of spoken Ukrainian. Воно дуже коротке, швидке та максимально пряме. Українці постійно використовують «бо» у щоденному спілкуванні з друзями. Наприклад: «Я поспішаю, бо запізнююся на роботу». Ви дуже часто будете чути «бо» на вулиці або в кафе. The phrase «тому що» is the neutral, universal choice. Ця фраза ідеально підходить і для розмови, і для письма. Вона завжди звучить трохи серйозніше та офіційніше. Наприклад, у книзі ви прочитаєте: «Земля прекрасна, тому що на ній живуть люди». Отже, для швидкої розмови сміливо обирайте «бо». Для тексту чи офіційної бесіди беріть «тому що».

Ці два слова мають дещо різні граматичні правила. У складному реченні вони стоять у різних місцях. The conjunction «бо» is strictly a connector that sits between two clauses. Ви ніколи не можете почати нове речення зі слова «бо». Воно завжди йде тільки після головної інформації. On the other hand, the phrase «тому що» is more flexible. Вона може спокійно стояти всередині вашого складного речення. Вона також може починати нове речення. Ми робимо так, коли даємо пряму відповідь на запитання. Подивіться на цей короткий діалог:

> — **Олена:** Чому ти не прийшов учора?
> — **Марко:** Тому що я був дуже зайнятий.

You cannot start a new sentence with «бо» to answer a direct question. Це звучить дуже неприродно для українців. Для першого слова у вашій відповіді ми завжди беремо «тому що».

Зараз ми поговоримо про одну дуже типову помилку. English speakers often fall into the "Because-What" trap. Англійське слово "because" студенти часто перекладають як «тому що». Вони бачать там слово «що» і думають, що воно завжди потрібне. Тому вони часто помиляються і кажуть «бо що». Це велика проблема. Слово «бо» є повністю самостійним сполучником. Ніколи не додавайте маленьке «що» до «бо». Це **калька** *(calque)*, якої немає в українській мові. Правильно казати: «Я вчу мову, бо мені це подобається». Неправильно казати: «Я вчу мову, бо що мені це подобається». Запам'ятайте це просте правило назавжди. Слово «бо» чудово працює без сторонньої допомоги.

Тепер час подивитися на українську пунктуацію. Це надзвичайно важлива тема для правильного письма. У складному реченні ми маємо дві різні частини. Ці частини треба візуально розділяти. В українській мові **кома** *(comma)* працює як надійний прикордонник між двома ідеями. The comma is the strict border guard between the main clause and the cause clause. Ви повинні завжди ставити кому перед словами «тому що» та «бо». Це обов'язкове граматичне правило нашого синтаксису. Давайте подивимося на кілька гарних прикладів. «Вона вивчає українську мову, бо хоче розуміти своїх друзів». «Ми не пішли гуляти, тому що надворі був дощ». «Студенти уважно слухають, бо викладач розповідає цікаву історію». Зверніть увагу на коми у цих реченнях. Англійська мова часто зовсім не вимагає коми перед причиною. Але українська мова завжди вимагає коми перед цими важливими сполучниками.

Як ми створюємо такі складні речення на практиці? Це дуже схоже на просту математику. Ми беремо два окремі факти і робимо з них один сильний аргумент. Уявіть, що у вас є перший факт: «Петро винайшов вулик». **Вулик** *(beehive)* — це спеціальний дерев'яний будинок для бджіл. Потім у вас є другий факт: «Він — відомий **бджоляр** *(beekeeper)*». Тепер ми хочемо пояснити причину його великої популярності. Ми просто з'єднуємо ці два факти разом. Результат буде такий: «Петро — найвідоміший бджоляр, тому що він винайшов вулик». Ми щойно перетворили два короткі речення на одне велике інформативне речення. Це робить вашу розповідь набагато цікавішою та багатшою. Ви можете легко робити так з будь-якими фактами у житті. Головне — знайти правильний логічний зв'язок між ними.

Також варто пам'ятати про правильну інтонацію. У причинових реченнях голос робить легкий рух угору (↗) перед сполучниками «тому що» або «бо», щоб показати, що далі буде пояснення. А вже в кінці підрядної частини голос спокійно падає вниз (↘). Наприклад: «Я не прийшов (↗), тому що був зайнятий (↘)». Це робить вашу мову дуже природною.

<!-- INJECT_ACTIVITY: fill-in-cause-clauses -->

## Хоча... (Although...)

У нашому житті часто трапляються різні великі перешкоди. Іноді ми маємо серйозну проблему, але все одно робимо свою роботу. Це називається **допуст** *(concession)*. У таких ситуаціях ми використовуємо дуже корисне слово: **хоча** *(although / even though)*. Concessive clauses introduce a fact that should logically prevent the main action, but the main action happens anyway. Це показує вашу внутрішню силу або несподіваний результат. Наприклад, на вулиці зараз дуже погана погода. Логічно просто залишитися вдома і пити гарячий чай. Але ми маємо зовсім інші великі плани. Подивіться на цей короткий студентський діалог:

> — **Максим:** Чому ти тут? Ти ж хворієш. *(Why are you here? You are sick.)*
> — **Оксана:** Я прийшла на лекцію, хоча почуваюся погано. *(I came to the lecture, although I feel bad.)*

Зверніть увагу на **контраст** *(contrast)* між поганою ситуацією та дією. Сполучник «хоча» допомагає нам будувати такі цікаві речення. Ви можете також сміливо використовувати коротку форму: **хоч** *(even though)*. Ці два слова однакові за значенням.

На відміну від слова «бо», сполучник «хоча» є дуже гнучким інструментом. Від нього може легко починатися ваше нове складне речення. Згадайте наше старе граматичне правило про кому. Ми завжди повинні візуально відокремлювати дві частини складного речення. Якщо частина зі словом «хоча» стоїть на початку, ми обов'язково ставимо кому. Ось гарний приклад з української класичної літератури: «Хоча було тільки **надвечір’я** *(early evening)*, **присмерки** *(twilight)* вже згусли». But you can also flip the grammatical structure completely. The dependent clause with "хоча" can comfortably sit in the second half of your sentence. У такому випадку ми просто ставимо кому прямо перед сполучником «хоча». Наприклад: «Я сьогодні дуже багато вчуся, хоча дуже втомився». Обидва ці варіанти звучать максимально природно і правильно. Вибирайте той варіант структури, який вам більше подобається під час розмови.

Ви вже напевно добре знаєте популярне українське слово **але** *(but)*. Students often wonder when to use "але" and when to use "хоча", since both words show contrast. Звичайне «але» показує дуже просте **протиставлення** *(opposition)* двох рівних фактів. Наприклад: «Він зараз втомлений, але він активно працює». Це просто дві різні звичайні життєві ситуації. А ось наше нове слово «хоча» додає значно більше емоцій. Воно завжди показує велике **зусилля** *(effort)* або подолання серйозної перешкоди. Коли ви кажете: «Хоча він втомлений, він працює», ви підкреслюєте його силу. Це звучить набагато сильніше, цікавіше і багатше. The conjunction "хоча" makes one clause grammatically dependent on the other, creating a sense of an obstacle being actively overcome. Слово «але» просто нейтрально з'єднує дві незалежні ідеї. Тому для драматичних історій завжди краще брати сполучник «хоча».

В українській мові історично існує ще одна цікава граматична традиція. When you start your complex sentence with a "хоча" clause, you can add an extra conjunction to the main clause. Ми досить часто додаємо коротке слово «а» або слово «але» у другу частину. Це робить ваш фінальний контраст ще більш яскравим і емоційним. Наприклад: «Хоч і тепло ще, а осінь вже підходить **крадькома** *(stealthily)*». Зверніть увагу, що ми маємо відразу два сполучники в одному реченні. Англійською мовою така конструкція звучить як велика помилка. Але українською мовою це нормальна літературна практика. You do not have to use this expressive double structure every time you speak. Однак ви часто будете бачити її в хорошій українській літературі. Ви також будете постійно чути її в живій щоденній розмові. Ця маленька деталь додає вашій мові автентичного українського колориту.

Нарешті, давайте трохи поговоримо про правильну інтонацію у таких реченнях. Your voice needs to accurately guide the listener through the emotional contrast. Коли ви починаєте речення зі слова «хоча», ваш голос повинен іти вгору (↗). The rising intonation clearly signals to your conversation partner that they need to wait for a twist. Ви ніби загадково кажете їм: «Увага, зараз буде сюрприз!». А потім, коли ви говорите головну частину речення, ваш голос іде різко вниз (↘). The falling tone comfortably delivers the final unexpected result. Давайте зараз потренуємо це разом на одному красивому поетичному прикладі. Будь ласка, прочитайте це коротке складне речення вголос у своїй кімнаті: «Хоч земля вся укрита **снігами** *(snows)* ↗, моє серце в **цвіту** *(bloom)* ↘». Ви відчуваєте цю неймовірно красиву музику нашої рідної мови? Правильна українська інтонація гарантовано робить вас справжнім майстром спілкування.

<!-- INJECT_ACTIVITY: match-up-cause-concession -->
<!-- INJECT_ACTIVITY: unjumble-complex-sentences -->

## Складносурядне речення: і, та, але (Compound Sentences)

На рівні А1 ви вже добре вивчили базові **сполучники** *(conjunctions)*: «і», «та», «але». Ви часто і успішно використовували їх щодня. Ви брали їх, щоб просто з'єднати два слова або дві короткі фрази. Наприклад: «хліб і молоко», «великий, але дорогий» або «швидко та смачно». Тепер ми переходимо до наступного дуже важливого етапу.  Ми будемо разом будувати великі **складносурядні речення** *(compound sentences)*. Це такі речення, де дві рівні частини спокійно працюють разом. Сполучники «і» та «та» мають однакове базове значення. Українці часто чергують їх у своїй щоденній розмові. We use "та" as a perfect synonym for "і" simply to avoid repeating the same sound too often. Наприклад, ми кажемо: «Я купив хліб і молоко, та ще взяв твердий сир». Це звучить дуже природно і мелодійно.

Що означають «рівні частини» в українській граматиці? Уявіть собі два окремі, самостійні прості речення. Кожне з них має свій власний суб'єкт і свою власну дію. Наприклад, перше речення: «Я ввечері прийшов додому». І друге окреме речення: «Ми разом смачно **повечеряли** *(had dinner)*». Compound sentences build a simple bridge between two ideas of equal importance and weight. Ми з'єднуємо їх так: «Я ввечері прийшов додому, і ми разом смачно повечеряли». Обидві ці частини можуть спокійно існувати окремо одна від одної. Згадайте наші попередні нові сполучники «тому що» або «хоча». Вони завжди створюють логічну залежність: одна частина є головною, а інша — залежною. A clause starting with "because" cannot logically stand alone as a complete thought. Але у складносурядному реченні зі словами «і» чи «але» всі частини є рівноправними незалежними партнерами. Ніхто нікому не підпорядковується.

Ви вже чудово знаєте і активно використовуєте популярне слово «але». Воно завжди прекрасно працює для простого **протиставлення** *(opposition)* у розмові. Наприклад: «Сергій хотів піти в кіно, але він не мав вільного часу». Проте на рівні А2 настав час розширити ваш активний словниковий запас. Українська мова має два чудові і красиві синоніми: **проте** *(however / yet)* та **однак** *(however)*. These words function exactly like "але", but they elevate your speech to a much more sophisticated, mature level. Ви будете часто бачити їх у новинах, книгах та статтях. Давайте уважно порівняємо дві схожі фрази. Перша: «Сергій хотів піти в кіно, але він не мав вільного часу». А тепер друга: «Сергій хотів піти в кіно, проте він не мав вільного часу». Значення залишається однаковим, але другий варіант звучить набагато елегантніше і професійніше. Сміливо використовуйте «проте» та «однак» у ваших розмовах.

Тепер давайте детально поговоримо про важливі правила української **пунктуації** *(punctuation)*. In Ukrainian, comma placement depends entirely on the specific grammatical structures you are connecting. Коли сполучники «і» або «та» з'єднують лише два слова, ми кому не ставимо. Наприклад, ми пишемо: «брат і сестра» або «сніг та дощ». Але граматична ситуація кардинально змінюється, коли ми будуємо велике складне речення. If "і" or "та" connect two completely independent clauses, a comma is strictly mandatory before the conjunction. Ми завжди повинні писати: «Світило яскраве сонце, і маленькі пташки весело співали». Тут ми маємо дві різні дії і два різні суб'єкти. Правила для слів «але», «проте» та «однак» є ще простішими. You must always, without any exception, put a comma before words expressing direct contrast. Ми завжди пишемо: «Я багато працював, однак я нічого не встиг». Це залізне правило української граматики.

Ці маленькі сполучні слова роблять вашу українську мову живою та логічно зв'язною. Вони активно працюють як гнучка **сполучна тканина** *(connective tissue)* між вашими ідеями. Уявіть собі ситуацію, що ви розповідаєте другу про свій робочий день. Ви можете говорити короткими, дуже сухими фактами. «Він сьогодні багато працював. Він дуже сильно втомився. Він успішно закінчив свій новий **проєкт** *(project)*». Це звучить трохи як автоматичний робот, чи не так? Coordinating conjunctions allow you to seamlessly weave these isolated facts into a smooth, natural narrative flow. Давайте спробуємо гарно об'єднати ці три окремі думки. Ми скажемо так: «Він багато працював і сильно втомився, проте успішно закінчив проєкт». Тепер це вже справжня, красива і жива історія. Ваша розповідь стала динамічною, емоційною і дійсно цікавою для вашого слухача.

Насамкінець, зверніть особливу увагу на правильну мелодію таких речень. We previously discussed the dramatic rise-and-fall intonation of complex sentences that use the word "хоча". Складносурядні речення завжди звучать набагато спокійніше, рівніше і стабільніше. Тому що наші частини є рівноправними, ми використовуємо **рівну інтонацію** *(even intonation)*. Зазвичай обидві незалежні частини речення мають дуже схожий спокійний рух голосу вниз (↘). The falling intonation clearly marks the successful completion of each independent thought within the larger sentence. Ви ніби ставите невидиму крапку своїм голосом після кожної ідеї. Давайте зараз прочитаємо цей простий приклад разом. «Ми пішли в чудовий зелений парк (↘), і ми там довго гуляли (↘)». Ваша інтонація відразу показує вашу впевненість і емоційну стабільність. Завжди тренуйте цю спокійну мелодію, коли ви самостійно читаєте українські тексти вголос.

<!-- INJECT_ACTIVITY: quiz-cause-choice -->
<!-- INJECT_ACTIVITY: group-sort-conjunctions -->

## Підсумок

Сьогодні ми вивчили дуже важливі слова для вашого щоденного спілкування. Вони допомагають будувати складні, логічні та красиві речення. Давайте коротко повторимо наші головні правила.

По-перше, ми використовуємо **сполучники причини** *(causal conjunctions)* «тому що» та «бо». Вони завжди відповідають на питання «Чому?». Наприклад: «Я вивчаю українську мову, тому що я хочу жити в Києві». Це ваш основний інструмент для пояснення.

По-друге, ми тепер знаємо **сполучник допусту** *(concessive conjunction)* «хоча». Він показує цікавий контраст або несподіваний результат. Він відповідає на питання «Незважаючи на що?». Наприклад: «Хоча я дуже втомився, я читаю нову книгу». 

По-третє, ми вміємо з'єднувати дві незалежні ідеї. Для цього ми беремо слова «і», «та», «але», «проте» або «однак». Завжди пам'ятайте про обов'язкові коми перед цими словами у великих складних реченнях!

Тепер час для невеликої самоперевірки. Спробуйте дати повні відповіді на два прості запитання. Чому ви зараз вивчаєте українську мову? Що ви зазвичай робите ввечері, хоча ви дуже втомилися після роботи? Спробуйте сказати це вголос або напишіть ці відповіді для себе. З цими маленькими словами ваша українська розповідь стає набагато багатшою і природнішою!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: because-and-although
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

**Level: A2 (Module 47/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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
