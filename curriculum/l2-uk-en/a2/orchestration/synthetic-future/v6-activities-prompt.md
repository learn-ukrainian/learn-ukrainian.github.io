<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/synthetic-future.yaml` file for module **41: Я напишу!** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-choose-between-simple-and-compound-future-forms-based-on-context -->`
- `<!-- INJECT_ACTIVITY: group-sort-future-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-compound-future -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: unjumble-future-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences with the correct future form (synthetic perfective or
    analytical imperfective) based on context
  items: 8
  type: fill-in
- focus: Identify whether a future sentence uses synthetic or analytical future and
    explain the aspect choice
  items: 8
  type: quiz
- focus: Sort verb forms into two groups — synthetic future (perfective) and analytical
    future (imperfective)
  items: 8
  type: group-sort
- focus: Reorder words to form correct future tense sentences using both synthetic
    (напишу) and analytical (буду писати) forms
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- приїхати (to arrive — pf.)
- обіцяти (to promise)
- планувати (to plan)
- прибирати / прибрати (to clean up — impf./pf.)
required:
- майбутній час (future tense)
- простий (simple, synthetic)
- складений (compound, analytical)
- сказати / скажу (to say/tell — pf. future)
- написати / напишу (to write — pf. future)
- зробити / зроблю (to do — pf. future)
- буду (I will — auxiliary)
- прочитати (to read through — pf.)
- подзвонити (to call — pf.)
- купити (to buy — pf.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Два майбутніх часи (Two Futures in Ukrainian)

В англійській мові є лише один майбутній час. In English, there is only one future tense. English uses the word "will" to talk about any future action. В українській мові ми маємо два майбутніх часи. In Ukrainian, we have two future tenses. Your choice of tense depends strictly on the verbal aspect. Ми обираємо між завершеним результатом та тривалим процесом. We must decide if the action is a single finished event or a repeated habit. Це правило не залежить від формального чи неформального стилю. This rule does not depend on formal or informal style. This choice is purely about how the action unfolds in reality. Ukrainian grammar forces us to be specific about our intentions. Ви повинні одразу думати про мету вашої дії. You must immediately think about the goal of your action.

Перший варіант — це **простий майбутній час**. The first option is the simple future tense. We form this tense using perfective verbs. Дієслова **доконаного виду** не мають справжнього теперішнього часу. Verbs of the perfective aspect do not have a real present tense. Think about it logically: a completed action cannot be happening right now. Якщо дія повністю завершена, вона не може тривати зараз. If an action is completely finished, it cannot last right now. Because perfective verbs cannot logically exist in the present, their present-tense forms automatically point to the future. They look exactly like present tense verbs, but they carry a future meaning. Наприклад, ми беремо дієслово «писати». For example, we take the verb to write. У теперішньому часі ми кажемо: «Я **пишу** листа». In the present tense, we say: "I am writing a letter". This means you are doing the action right now. Але дієслово «написати» має доконаний вид. But the verb to write with the prefix "на-" has the perfective aspect. Форма «я **напишу** листа» означає завершену дію в майбутньому. The form "I will write a letter" means a completed action in the future. It means you will finish the letter completely.

Другий варіант — це **складений майбутній час**. The second option is the compound future tense. We use this specific form with verbs of the imperfective aspect. Цей час показує тривалу або регулярну дію в майбутньому. This tense shows a continuous or regular action in the future. To build it, we need the auxiliary verb **бути** in its future forms. The verb "to be" helps us create this structure. До цього слова ми додаємо інфінітив дієслова **недоконаного виду**. To this word we add the infinitive of the imperfective aspect verb. For example, we combine "буду" and the infinitive "писати". Ми кажемо: «Завтра я **буду писати** листа». We say: "Tomorrow I will be writing a letter". This means the process will happen, but we do not guarantee the final completion. Можливо, я не закінчу цей довгий текст. Maybe I will not finish this long text. Ця форма також ідеально підходить для регулярних дій. This form is also ideally suited for regular actions. Кожного вечора я **буду читати** книгу. Every evening I will read a book. The grammatical structure is always the verb "бути" plus the dictionary form of the main verb.

Давайте коротко порівняємо ці дві форми. Let's briefly compare these two forms. The simple future promises a clear result and a logical completion. Форма «я **напишу**» гарантує результат. The form "I will write" guarantees a result. The compound future focuses entirely on duration and repetition. Форма «я **буду писати**» показує лише активний процес. The form "I will be writing" shows only an active process. Choosing the wrong tense can change the meaning of your promise. Якщо ви кажете «я **зроблю**», люди чекають на результат. If you say "I will do", people wait for a result. If you say "я **буду робити**", you only promise to spend time on the task. Обидва часи дуже потрібні для щоденного спілкування українською мовою. Both tenses are very necessary for daily communication in the Ukrainian language.

<!-- INJECT_ACTIVITY: fill-in-choose-between-simple-and-compound-future-forms-based-on-context -->


## Простий майбутній час (Perfective/Synthetic Future)

The simple future tense uses perfective verbs. Ми завжди використовуємо дієслова **доконаного виду** *(perfective aspect)*. To build this tense, we take a perfective verb and conjugate it exactly like a present-tense verb. Ми просто додаємо звичайні закінчення теперішнього часу. *(We simply add normal present-tense endings.)* Most perfective verbs are just imperfective verbs with a specific prefix added to the beginning. Наприклад, ми беремо популярний префікс **про-** і дієслово **читати** *(to read)*. *(For example, we take the popular prefix pro- and the verb to read.)* Разом ми отримуємо нове дієслово **прочитати** *(to read completely)*. This new verb belongs to the first conjugation. Ми відмінюємо його так: **я прочитаю** *(I will read)*, **ти прочитаєш** *(you will read)*, **він прочитає** *(he will read)*. У множині ми кажемо: **ми прочитаємо** *(we will read)*, **ви прочитаєте** *(you will read)*, **вони прочитають** *(they will read)*. The endings are absolutely identical to the present tense, but the prefix automatically makes the meaning future.

The second conjugation follows the exact same structural logic. Ми беремо префікс і додаємо його до базової основи. *(We take a prefix and add it to the base stem.)* However, you must remember the specific consonant shifts that happen in the first person singular. Ці чергування приголосних звуків дуже важливі тут. *(These consonant sound shifts are very important here.)* For example, the consonant **б** changes to the cluster **бл**. Дієслово **зробити** *(to do completely)* має форму **я зроблю** *(I will do)*. Інші форми залишаються нормальними: **ти зробиш** *(you will do)*, **він зробить** *(he will do)*, **ми зробимо** *(we will do)*, **ви зробите** *(you will do)*, **вони зроблять** *(they will do)*. Another common shift is **т** to **ч**. Від дієслова **побачити** *(to see)* ми легко утворюємо форму **я побачу** *(I will see)*. You will also frequently see the shift from **д** to **дж** in verbs like **порадити** *(to advise)*, which becomes **я пораджу** *(I will advise)*.

Some perfective verbs are absolutely essential for daily communication and simple transactions. Це головні дієслова для вашого щоденного виживання. *(These are the main verbs for your daily survival.)* You will use them constantly to make firm promises or state clear decisions. Якщо ви хочете щось сказати, ви кажете: «Я **скажу**» *(I will say)*. Якщо ви плануєте покупку в магазині, ви кажете: «Я **куплю**» *(I will buy)*. Notice that the verb **купити** *(to buy)* also features the consonant shift in the first person. Для розмови по телефону ми використовуємо дієслово **подзвонити** *(to call)*. Ви кажете своїм друзям: «Я **подзвоню** вам завтра» *(I will call you tomorrow)*. Якщо ви відправляєте важливе повідомлення, ви кажете: «Я **надішлю** довгий емейл» *(I will send a long email)*.

Motion verbs use specific prefixes to clearly show your concrete future travel plans. Дієслова руху дуже часто мають префікси **по-** або **при-**. *(Motion verbs very often have the prefixes po- or pry-.)* The prefix "по-" shows the active start of a trip or movement away from your current location. Якщо ви плануєте подорож машиною, ви кажете: «Я **поїду**» *(I will leave/go by vehicle)*. Якщо ви йдете кудись пішки, ви кажете: «Я **піду**» *(I will go by foot)*. The prefix "при-" always shows successful arrival at a destination. Якщо ви говорите про точний час, ви кажете: «Я **приїду** о сьомій годині» *(I will arrive at seven o'clock)*. Ці короткі слова ідеально підходять для планування маршруту. *(These short words are perfectly suited for planning a route.)*

Let's see how friends use these concrete promises when planning a relaxing evening together. Вони зараз планують спільну смачну вечерю. *(They are now planning a joint tasty dinner.)*

> — **Анна:** Що ми будемо робити сьогодні ввечері? *(What will we do tonight?)*
> — **Максим:** Я **куплю** червоне вино і свіжі фрукти. *(I will buy red wine and fresh fruits.)*
> — **Анна:** Дуже добре, а я **зроблю** великий салат. *(Very good, and I will make a large salad.)*
> — **Анна:** Також я **замовлю** гарячу піцу для нас. *(Also I will order a hot pizza for us.)*
> — **Максим:** Чудово! А потім ми **подивимося** цікавий фільм. *(Great! And then we will watch an interesting movie.)*

<!-- INJECT_ACTIVITY: group-sort-future-forms -->


## Складений майбутній час (Imperfective/Analytical Future)

Зараз ми вивчимо інший спосіб говорити про майбутнє. *(Now we will learn another way to talk about the future.)* Це складений майбутній час. *(This is the compound future tense.)* English uses progressive forms to show an ongoing action in the future. Ukrainian uses a similar structure exclusively for imperfective verbs. Ця граматична конструкція показує тривалий процес. *(This grammatical structure shows a continuous process.)* You build it with a helper verb and an infinitive. Ось повна парадигма допоміжного дієслова **бути** *(to be)*. *(Here is the full paradigm of the helper verb to be.)* Зверніть увагу на закінчення. *(Pay attention to the endings.)* **Я буду** *(I will be)*, **ти будеш** *(you will be)*, **він буде** *(he will be)*, **вона буде** *(she will be)*, **ми будемо** *(we will be)*, **ви будете** *(you will be)*, **вони будуть** *(they will be)*. After this helper verb, you must always place an imperfective infinitive. Дієслово після слова «бути» ніколи не змінює свою форму. *(The verb after the word "to be" never changes its form.)* Ви кажете: «Я буду **працювати**» *(I will be working)*. Ви також кажете: «Вона буде **читати**» *(She will be reading)*. The helper verb changes to match the person, but the main action verb stays in the infinitive form.

Ми використовуємо цю граматичну форму для опису тривалих дій. *(We use this grammatical form to describe continuous actions.)* The compound future tense is perfect when you want to emphasize the duration of a process. Ви фокусуєте увагу на самому процесі, а не на конкретному результаті. *(You focus attention on the process itself, and not on a specific result.)* If an action will take a long time, you must use the imperfective aspect. Наприклад, ви кажете: «Завтра я буду **працювати** весь день» *(Tomorrow I will be working all day)*. У цьому реченні важливий сам неперервний процес роботи. *(In this sentence, the continuous process of work itself is important.)* Інший популярний приклад: «Я буду **читати** книгу ввечері» *(I will be reading a book in the evening)*. Тут ви не обіцяєте прочитати всю книгу повністю до кінця. *(Here you do not promise to read the whole book completely to the end.)* Ви просто описуєте свій стан. *(You simply describe your state.)* The continuous process of reading will comfortably occupy your free evening.

Також ми регулярно використовуємо цей час для повторюваних дій. *(Also we regularly use this tense for repeated actions.)* When an action will happen repeatedly or habitually in the future, the compound form is strictly required. Слова-маркери дуже часто допомагають зрозуміти цю щоденну ситуацію. *(Marker words very often help to understand this daily situation.)* The repetition makes the action an imperfective process by definition, requiring the helper verb. Ви часто побачите слова **щодня** *(every day)*, **часто** *(often)* або **завжди** *(always)*. *(You will often see the words every day, often or always.)* Ці короткі слова завжди показують рутину. *(These short words always show a routine.)* Ви кажете: «Я буду **дзвонити** тобі щодня» *(I will be calling you every day)*. Це чітко означає, що дія буде повторюватися багато разів. *(This clearly means that the action will be repeated many times.)* Ви також можете сказати своїм друзям: «Ми будемо часто **зустрічатися**» *(We will be meeting often)*.

Тут студенти дуже часто роблять серйозну граматичну помилку. *(Here students very often make a serious grammatical error.)* You must never combine the conjugated helper verb with a perfective infinitive. Це жахливий гібрид, який зовсім не існує в українській мові. *(This is a terrible hybrid that does not exist in the Ukrainian language at all.)* Форма «я буду написати» є абсолютно неправильною. *(The form "I will write" is absolutely incorrect.)* Ukrainian explicitly separates the idea of process and the idea of a finished result. Якщо ви хочете показати фінальний результат, ви завжди використовуєте просту форму: «Я **напишу** довгий емейл» *(I will write a long email)*. Тут важлива дія має чіткий кінець. *(Here the important action has a clear end.)* Якщо ви хочете показати процес, ви використовуєте складену форму: «Я **буду писати** емейл» *(I will be writing an email)*. Цей активний процес триває певний час. *(This active process lasts a certain time.)* You cannot mix these two distinct temporal concepts together.

Давайте уважно подивимося, як друзі обговорюють свої нові звички. *(Let's carefully see how friends discuss their new habits.)* Вони серйозно говорять про свої амбітні плани на наступний рік. *(They are seriously talking about their ambitious plans for the next year.)* Вони обговорюють корисні речі, які скоро стануть їхньою новою рутиною. *(They are discussing useful things that will soon become their new routine.)*
> — **Марта:** Що ти будеш **робити** в новому році? *(What will you be doing in the new year?)*
> — **Олег:** Я буду щодня **бігати** у великому парку. *(I will be running in the large park every day.)*
> — **Марта:** Це дуже корисна щоденна звичка для здоров'я. *(This is a very useful daily habit for health.)*
> — **Олег:** А також я буду **вчити** українську кожну суботу. *(And also I will be studying Ukrainian every Saturday.)*
> — **Марта:** Чудово, я буду **допомагати** тобі з домашнім завданням. *(Great, I will be helping you with homework.)*
> — **Олег:** Дякую, ми будемо регулярно **практикувати** мову разом. *(Thank you, we will be practicing the language regularly together.)*

<!-- INJECT_ACTIVITY: fill-in-compound-future -->


## Як обрати вид для майбутнього (Choosing Aspect for the Future)

We now have two tools for the future. Are you focusing on the final result, or the ongoing process? Ваш вибір завжди залежить від головної мети. *(Your choice always depends on the main goal.)* Порівняйте ці два різні речення. *(Compare these two different sentences.)* «Я **прочитаю** *(will finish reading)* цю статтю» *(I will finish reading this article)* означає, що ви закінчите дію. *(means that you will finish the action.)* Але речення «Я **буду читати** *(will be reading)* цю статтю» *(But the sentence «I will be reading this article»)* означає тільки активний процес. *(means only an active process.)* Ви кажете «я **напишу**» *(I will write)*, коли хочете закінчити текст. *(You say «I will write» when you want to finish the text.)* Але ви кажете «я **буду писати**» *(I will be writing)*, коли описуєте свою роботу. *(But you say «I will be writing» when you describe your work.)*

Деякі слова дуже допомагають обрати правильний вид. *(Some words help a lot to choose the correct aspect.)* When an action is a short, completed event, we use the simple future. Для доконаного виду ми часто використовуємо слова **скоро** *(soon)* або **за хвилину** *(in a minute)*. *(For the perfective aspect we often use the words soon or in a minute.)* Слово **враз** *(suddenly)* також показує швидку дію. *(The word suddenly also shows a fast action.)* Conversely, if you emphasize duration, you need the compound future. Це слова **довго** *(for a long time)* або **цілий вечір** *(the whole evening)*. *(These are the words for a long time or the whole evening.)* Для регулярних дій допомагають слова **часто** *(often)* та **завжди** *(always)*. *(For regular actions the words often and always help.)*

There is a very important difference between English and Ukrainian grammar in conditional sentences. Ви часто будете використовувати слова **якщо** *(if)* та **коли** *(when)*. *(You will often use the words if and when.)* In English, you use the present tense after "if" or "when" for future events. In Ukrainian, both parts of the sentence must be in the future tense. Якщо подія буде в майбутньому, ми використовуємо майбутній час двічі. *(If the event will be in the future, we use the future tense twice.)* Подивіться на це речення. *(Look at this sentence.)* «Якщо ти **прийдеш** *(will come)*, ми **будемо пити** *(will be drinking)* чай». *(If you come, we will be drinking tea.)* Обидва дієслова показують майбутній час. *(Both verbs show the future tense.)* Ви також можете сказати: «Коли я **приїду** *(will arrive)*, я **подзвоню** *(will call)* тобі». *(You can also say: When I arrive, I will call you.)* Ніколи не використовуйте теперішній час після слова «якщо» для майбутнього! *(Never use the present tense after the word "if" for the future!)*

Давайте подивимося, як друзі планують свої вихідні. *(Let's see how friends plan their weekend.)* Процеси та результати тут дуже зрозумілі. *(Processes and results are very clear here.)*
> — **Анна:** Що ти будеш **робити** завтра? *(What will you be doing tomorrow?)*
> — **Марко:** Вранці я буду **прибирати** квартиру. *(In the morning I will be cleaning the apartment.)* О другій годині я **подзвоню** тобі, і ми **підемо** в кіно. *(At two o'clock I will call you, and we will go to the cinema.)*
> — **Анна:** Чудово! Я **куплю** квитки заздалегідь. *(Great! I will buy the tickets in advance.)*
> — **Марко:** Добре, якщо ти **купиш** квитки, я **куплю** попкорн. *(Good, if you buy the tickets, I will buy the popcorn.)*

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->
<!-- INJECT_ACTIVITY: unjumble-future-sentences -->


## Підсумок

Let's review the two ways to talk about the future in Ukrainian. Усе залежить від виду дієслова. *(Everything depends on the verb aspect.)*

*   **Простий майбутній час** *(Simple future tense)*: We use the **доконаний вид** *(perfective aspect)*. You add present tense endings to the perfective verb. Цей час показує результат або одну коротку дію. *(This tense shows a result or one short action.)* Наприклад: «Я **напишу**» *(For example: I will write)*.
*   **Складений майбутній час** *(Compound future tense)*: We use the **недоконаний вид** *(imperfective aspect)*. You combine the conjugated word **буду** *(I will be)* with an imperfective infinitive. Цей час показує довгий процес або регулярну дію. *(This tense shows a long process or a regular action.)* Наприклад: «Я **буду писати**» *(For example: I will be writing)*.

Now, answer these three questions to check your knowledge. Дайте відповіді на ці запитання. *(Answer these questions.)*

1. How do you say «I will call» as a single, completed act?
2. Why is the phrase «я буду написати» grammatically wrong?
3. Which future form do you use with the word **щодня** *(every day)*?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: synthetic-future
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

**Level: A2 (Module 41/60) — ELEMENTARY**

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
