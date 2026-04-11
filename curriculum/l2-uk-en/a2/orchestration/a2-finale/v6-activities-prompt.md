<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-finale.yaml` file for module **69: Фінал A2** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-situations -->`
- `<!-- INJECT_ACTIVITY: fill-in-dialogues -->`
- `<!-- INJECT_ACTIVITY: quiz-integrated-grammar -->`
- `<!-- INJECT_ACTIVITY: error-correction-a2 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete dialogues in real-world Ukrainian city situations
  items: 8
  type: fill-in
- focus: Choose the correct grammar form in integrated context (mixed cases, aspect)
  items: 8
  type: quiz
- focus: Match situations to appropriate Ukrainian phrases and expressions
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences covering module topics
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- маршрутка (minibus)
- прогулянка (walk, stroll)
- дізнатися (to find out, to learn)
- готовий (ready)
required:
- прибуття (arrival)
- вокзал (train station)
- квиток (ticket)
- ринок (market)
- замовити (to order)
- порадити (to recommend)
- будівля (building)
- враження (impression)
- підсумок (summary)
- вітаємо (congratulations)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Ранок: прибуття та орієнтація (Morning: Arrival and Orientation)

Уявіть цю яскраву ситуацію. Ранкове сонце світить прямо в очі. Ваш швидкісний потяг прибуває на платформу. Ви виходите з вагона і глибоко вдихаєте свіже повітря. Ось вона — довгоочікувана мить. Я у Львові! Я на головному вокзалі! Навколо вас дуже багато людей, усі кудись поспішають зі своїми валізами. Ви чуєте гучні оголошення, бачите величні старі будівлі. **Прибуття** (arrival) — це завжди початок нової, цікавої пригоди. Перше практичне завдання — знайти правильний транспорт. **Вокзал** (train station) у Львові дуже великий і красивий. Де зупинка? Як найкраще доїхати до історичного центру?

Ви бачите невеликий кіоск біля виходу. Вам потрібно купити **квиток** (ticket). Це ідеальна ситуація для знахідного відмінка (Accusative case). Ви будете чекати на трамвай.

> **Турист:** Добрий ранок! Дайте, будь ласка, один квиток на трамвай. *(Good morning! Give me, please, one ticket for the tram.)*
> **Касирка:** Добрий ранок. Вісімнадцять гривень, будь ласка. *(Good morning. Eighteen hryvnias, please.)*
> **Турист:** Ось, візьміть. А де тут зупинка? *(Here, take it. And where is the stop here?)*
> **Касирка:** Зупинка прямо, біля головного входу. Ви будете чекати на трамвай номер дев'ять. *(The stop is straight ahead, near the main entrance. You will wait for tram number nine.)*
> **Турист:** Дуже дякую! *(Thank you very much!)*
> **Касирка:** Прошу. Щасливої дороги! *(You are welcome. Have a good trip!)*

:::tip
In Ukrainian, we use the Locative case to show where someone is (**на вокзалі**, **у Львові**), but we use the Accusative case to show the direction of movement or waiting (**чекати на трамвай**).
:::

Великі українські міста мають зручні та різні види транспорту. Ви можете обрати трамвай, тролейбус, великий автобус або комфортне таксі. Також в Україні дуже популярна **маршрутка** (minibus). Вона зазвичай їздить швидко і часто зупиняється на невеликих зупинках. Який транспорт ви обираєте сьогодні? Ви можете швидко їхати до центру на таксі. Ви можете повільно їхати на трамваї і дивитися у вікно. Або, якщо ви маєте час, ви можете просто йти пішки. Це найкращий спосіб побачити нове місце.

Ви приїхали до центру. Ви швидко знаходите свій готель. Час для реєстрації на рецепції. Тут ми часто використовуємо родовий відмінок (Genitive case) для заперечення або приналежності.

> **Турист:** Добрий день! У мене є бронювання на ім'я Джон Сміт. *(Good day! I have a reservation under the name John Smith.)*
> **Адміністратор:** Добрий день, пане Джоне. Дайте, будь ласка, ваш паспорт. *(Good day, Mr. John. Give me, please, your passport.)*
> **Турист:** Ось мій паспорт. У вас є вільні кімнати на третьому поверсі? *(Here is my passport. Do you have free rooms on the third floor?)*
> **Адміністратор:** На жаль, немає вільних номерів на третьому. Але є чудова кімната на другому. *(Unfortunately, there are no free rooms on the third. But there is a wonderful room on the second.)*
> **Турист:** Добре, я беру. О котрій годині сніданок? *(Good, I will take it. At what time is breakfast?)*
> **Адміністратор:** Сніданок о восьмій ранку. Ось ваш ключ. *(Breakfast is at eight in the morning. Here is your key.)*

Львів — це справді особливе, атмосферне місто. Воно має унікальну архітектуру та багату історію. Під час прогулянки ви обов'язково побачите тут прекрасні старі австрійські будинки та традиційні, дуже красиві українські церкви. Вузькі вулиці завжди запрошують туристів до нових і несподіваних відкриттів. Попереду на вас чекає довга **прогулянка** (walk) старовинним містом. А пізно ввечері обов'язково буде тепла зустріч з хорошими друзями. Ви швидко залишаєте важкі речі в кімнаті, берете фотоапарат і йдете на вулицю. Це чудове місто вже чекає на вас!

<!-- INJECT_ACTIVITY: match-up-situations -->

## День: ринок, кав'ярня, прогулянка (Day: Market, Cafe, Walk)

Ви повільно йдете до історичного центру міста. Перед вами несподівано з'являється славетна Площа Ринок. Це справжнє серце старого Львова. Цей центральний майдан дуже старовинний, неймовірно гарний і завжди багатолюдний. Навколо голосно грають вуличні музиканти, усміхнені туристи роблять яскраві фотографії. Зовсім недалеко від площі є традиційний відкритий **ринок** (market). Ви вирішуєте піти туди, щоб подивитися на місцеве життя та купити свіжі продукти.

На базарі завжди багато свіжих продуктів і гучних веселих розмов. Тут ви можете чудово тренувати числівники та родовий відмінок множини. 

> **Турист:** Добрий день! Які гарні яблука! Скільки вони коштують? *(Good day! What beautiful apples! How much do they cost?)*
> **Продавчиня:** Добрий день! Сорок гривень за кілограм. Вони дуже солодкі. *(Good day! Forty hryvnias per kilogram. They are very sweet.)*
> **Турист:** Дайте мені, будь ласка, два кілограми яблук і п'ять помідорів. *(Give me, please, two kilograms of apples and five tomatoes.)*
> **Продавчиня:** Звичайно. Щось ще? У нас є дуже свіжий сир. *(Of course. Anything else? We have very fresh cheese.)*
> **Турист:** Ці жовті яблука солодші, ніж ті червоні? *(Are these yellow apples sweeter than those red ones?)*
> **Продавчиня:** Так, ці найкращі. А цей сир дорожчий, але дуже смачний. *(Yes, these are the best. And this cheese is more expensive, but very tasty.)*
> **Турист:** Дякую, я візьму тільки фрукти та овочі. *(Thank you, I will take only fruits and vegetables.)*

:::caution
Remember the numeral rules! Numbers 2, 3, and 4 require the nominative plural (**два кілограми**). Numbers 5 and above require the genitive plural (**п'ять помідорів**). This is a very common place for mistakes!
:::

Після галасливого базару приходить ідеальний час трохи відпочити. Ви йдете у традиційний затишний львівський заклад. Львівська кава — це справжня міська легенда. Українці дуже часто обговорюють свої гастрономічні смаки, активно використовуючи орудний відмінок для інгредієнтів. Хтось любить пити міцну каву з холодним молоком. Хтось обирає гарячий чай з лимоном або просто каву без цукру. Я віддаю перевагу чорній каві. Фраза віддавати перевагу означає вибирати щось як краще або смачніше для себе.

Ви сідаєте за маленький дерев'яний столик біля великого вікна. Підходить ввічливий офіціант. Час **замовити** (to order) смачний обід. Тут дуже важливо пам'ятати про вид дієслова.

> **Офіціант:** Добрий день. Ви вже обрали? Що будете замовляти? *(Good day. Have you already chosen? What will you order?)*
> **Турист:** Добрий день. Я хочу замовити традиційний обід. Що ви можете **порадити** (to recommend)? *(Good day. I want to order a traditional lunch. What can you recommend?)*
> **Офіціант:** Що порадити? Наші вареники з картоплею просто чудові. Або візьміть український борщ. *(What to recommend? Our dumplings with potatoes are simply wonderful. Or take Ukrainian borscht.)*
> **Турист:** Добре, я візьму борщ і фруктовий компот. *(Good, I will take borscht and fruit kompot.)*

Через десять хвилин:
> **Турист:** Перепрошую, я замовляв борщ, а ви принесли грибний суп. *(Excuse me, I ordered (imp) borscht, but you brought (perf) mushroom soup.)*
> **Офіціант:** Ой, вибачте! Я зараз усе швидко виправлю. *(Oh, excuse me! I will fix everything quickly now.)*

Після дуже смачного та ситного обіду ви знову продовжуєте гуляти містом. Раптом ви бачите високу і красиву вежу. Це дуже стара і монументальна **будівля** (building). Ви дуже хочете **дізнатися** (to find out, to learn) більше цікавої історії про це місце. Ви запитуєте місцевого жителя, використовуючи минулий час доконаного виду. "Перепрошую, хто збудував цю унікальну церкву?" або "Скажіть, будь ласка, коли відкрили цей прекрасний театр?" Місцеві люди завжди радо відповідають на такі запитання туристів.

<!-- INJECT_ACTIVITY: fill-in-dialogues -->

## Вечір: друзі, розмови, плани (Evening: Friends, Conversations, Plans)

Настає тихий вечір. Місто повільно запалює свої теплі ліхтарі. Це ідеальний час для зустрічі з українськими друзями. Ви заходите в невеликий атмосферний паб. Атмосфера навколо дуже розслаблена та приємна. Ви радісно вітаєтеся, активно використовуючи кличний відмінок, щоб показати свою повагу та дружнє ставлення. "Привіт, друже!", "Добрий вечір, пане Юрію!", "Радий тебе бачити, Оксано!".

Ви сідаєте разом за великий стіл і замовляєте смачні напої. Тепер прийшов час детально розповісти про ваш довгий день. Це найкращий момент, щоб показати, як добре ви знаєте вид дієслова. Ми завжди використовуємо недоконаний вид для тривалих процесів і доконаний для завершених результатів.

> **Юрій:** Як пройшов твій день? Що ти робив сьогодні у місті? *(How did your day pass? What were you doing today in the city?)*
> **Турист:** Мій день був просто чудовий! Сьогодні я багато гуляв і бачив багато старих пам'ятників. *(My day was simply wonderful! Today I walked a lot and saw many old monuments.)*
> **Оксана:** Ти купив щось цікаве на місцевому ринку? *(Did you buy something interesting at the local market?)*
> **Турист:** Так! Я довго вибирав різні подарунки, але нарешті купив гарний сувенір для мами. А потім я дуже смачно пообідав. *(Yes! I was choosing different gifts for a long time, but finally bought a beautiful souvenir for mom. And then I had a very tasty lunch.)*

:::note
Verb aspect is your best friend when telling stories. Use the imperfective aspect to set the scene or describe a process (**гуляв**, **бачив**, **вибирав**). Use the perfective aspect for the main events and finalized results (**купив**, **пообідав**).
:::

Друзі активно запитують про ваші **враження** (impression). Під час такої довгої, щирої розмови ви можете вільно ділитися своїми особистими думками. Використовуйте корисні фрази "на мою думку" або "мені здається". Ви порівнюєте величний Львів зі своїм рідним містом. Використовуйте родовий відмінок для правильного порівняння. "На мою думку, Львів набагато старіший за моє місто. Але моє місто трохи більше за Львів." Друзі захоплено розповідають цікаві факти про давні українські традиції. "Я дізнався багато нового про свято Івана Купала! Це дуже незвичайно," — кажете ви.

Вечір швидко продовжується. Ви починаєте серйозно обговорювати спільні плани на завтра і на ваше майбутнє навчання. Тут ви природно використовуєте майбутній час.

> **Оксана:** Що ми будемо робити завтра? Які у нас спільні плани? *(What will we be doing tomorrow? What are our shared plans?)*
> **Турист:** Завтра зранку ми будемо довго гуляти у зеленому парку. А потім я поїду високо в Карпати. *(Tomorrow morning we will be walking for a long time in the green park. And then I will go high into the Carpathians.)*
> **Юрій:** Це справді чудова ідея! Але обов'язково пам'ятай: якщо буде гарна сонячна погода, ми зможемо піднятися на велику гору. *(This is truly a wonderful idea! But definitely remember: if there is good sunny weather, we will be able to climb a large mountain.)*
> **Турист:** Я дуже сильно хочу побачити Карпатські гори. А також я хочу успішно продовжити вивчати українську мову. Якщо я вивчу всі ці нові слова, я буду вільно говорити! *(I very much want to see the Carpathian mountains. And also I want to successfully continue studying the Ukrainian language. If I learn all these new words, I will speak absolutely fluently!)*

Ваш довгий і дуже насичений день у Львові нарешті закінчується. Ви трохи втомилися, але ви внутрішньо дуже щасливі. Настав пізній час прощатися з друзями. Ви щиро посміхаєтеся і говорите стандартні теплі формули прощання: "На добраніч!", "До завтра!", "Було надзвичайно приємно побачитися!". Ви повільно повертаєтеся у свій тихий готель, повністю задоволені своїм чудовим українським днем.

<!-- INJECT_ACTIVITY: quiz-integrated-grammar -->
<!-- INJECT_ACTIVITY: error-correction-a2 -->

## Підсумок: від A2 до B1 (Summary: From A2 to B1)

Зупиніться на одну коротку мить і подивіться на свій величезний навчальний прогрес. Цей фінальний модуль — це ваш великий і важливий **підсумок** (summary) усього рівня A2. Подумайте, що ви тепер можете самостійно робити? Спробуйте впевнено сказати ці прості твердження вголос. "Я можу самостійно замовити улюблену їжу в місцевому ресторані." "Я можу без проблем купити квиток на швидкісний потяг чи міський автобус." "Я можу детально розповісти про своє минуле, правильно використовуючи минулий час." "Я чудово розумію логічну різницю між доконаним та недоконаним видами дієслів." "Я можу легко запитати правильну дорогу на незнайомій вулиці." Це не просто суха теорія чи граматичні правила. Це ваші реальні, практичні комунікативні навички. Згідно з європейськими мовними стандартами CEFR, базовий рівень A2 означає, що ви можете ефективно та швидко спілкуватися в простих, звичних життєвих ситуаціях. Ви успішно досягли цієї дуже важливої мети!

Попереду на вас чекає наступний, ще більш цікавий крок — середній рівень B1. Що саме зміниться у вашому щоденному навчанні? По-перше, буде набагато більше української мови безпосередньо в граматичних інструкціях та детальних поясненнях. Англійська мова поступово, але впевнено зникне з ваших регулярних уроків. По-друге, навчальні тексти стануть значно довшими і трохи складнішими. Ви будете постійно читати справжні цікаві історії, біографії відомих людей та актуальні новини. По-третє, з'явиться нова, значно більш детальна та глибока граматика. Ми будемо активно вивчати дієслова руху з різними корисними префіксами (наприклад, "приїхати", "вийти", "перейти", "обійти"). Також ми почнемо поступово вивчати українські дієприкметники. Але зовсім не хвилюйтеся! Ваш міцний базовий граматичний міст уже дуже надійно побудований. Ви чудово знаєте всі сім відмінків, ви добре розумієте час і складний вид дієслова. Тепер ви будете тільки збагачувати та красиво прикрашати свою українську мову.

Успішне завершення початкового рівня A2 — це справді величезне особисте досягнення. Українська мова — це надзвичайно красива, але об'єктивно складна слов'янська мова. Ви так багато і наполегливо працювали, ви сумлінно виконали сотні практичних вправ, ви вивчили дуже багато нових корисних слів і складних граматичних правил. Ви можете щиро пишатися собою сьогодні. Ви вже повністю **готовий** (ready) турист і чудовий, впевнений співрозмовник. Ви можете самостійно і спокійно вирішувати щоденні життєві ситуації в Україні. **Вітаємо** (congratulations)! Ви повністю готові до нових захопливих мовних викликів. Побачимося на цікавому та глибокому рівні B1!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-finale
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

**Level: A2 (Module 69/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
