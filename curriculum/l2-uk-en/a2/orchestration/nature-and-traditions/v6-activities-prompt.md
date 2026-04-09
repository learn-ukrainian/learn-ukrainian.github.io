<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/nature-and-traditions.yaml` file for module **60: Пори року і свята** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-seasons-match-seasonal-vocabulary-and-activities -->`
- `<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->`
- `<!-- INJECT_ACTIVITY: fill-in-grammar-seasons -->`
- `<!-- INJECT_ACTIVITY: true-false-culture -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match seasonal vocabulary and activities to the correct season
  items: 8
  type: match-up
- focus: Identify which holiday a tradition belongs to
  items: 8
  type: quiz
- focus: Complete sentences about weather and seasons with correct grammar forms
  items: 8
  type: fill-in
- focus: Verify facts about Ukrainian holiday traditions
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кутя (kutia — Christmas ritual dish)
- колядка (Christmas carol)
- вінок (wreath)
- мороз (frost)
- розквітати (to blossom)
required:
- пора року (season)
- весна (spring)
- літо (summer)
- осінь (autumn)
- зима (winter)
- погода (weather)
- свято (holiday)
- Різдво (Christmas)
- Великдень (Easter)
- традиція (tradition)
- писанка (decorated Easter egg)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чотири пори року (The Four Seasons)

Українська природа дуже красива та різноманітна. В Україні є чотири різні **пори року** *(seasons)*. Це зелена **весна** *(spring)*, тепле **літо** *(summer)*, золота **осінь** *(autumn)* і сніжна **зима** *(winter)*. Вони завжди йдуть одна за одною. Кожна пора року має свій характер. Ми часто хочемо сказати «in summer» або «in winter». Але ми не використовуємо прийменники «у» або «в» з іменником. Це дуже поширена граматична помилка. Українці кажуть інакше: **навесні** *(in spring)*, **влітку** *(in summer)*, **восени** *(in autumn)* та **взимку** *(in winter)*. Наприклад, ми говоримо: «Я дуже люблю відпочивати влітку». Ніколи не кажіть «у літі», тому що це звучить неприродно. Запам'ятайте ці чотири важливі слова, щоб розмовляти правильно.

Після довгої та холодної зими завжди приходить весна. Навесні природа повільно прокидається. Світить яскраве сонце, і на вулиці з кожним днем **стає тепліше** *(it gets warmer)*. У парках і лісах **все розквітає** *(everything blossoms)*: зелені дерева, великі кущі та перші квіти. З теплих країв **птахи повертаються** *(birds return)* додому. Після весни починається літо. Влітку часто буває дуже **спекотно** *(hot)*. Це улюблений час для багатьох українців. Літо — це найкращий **час відпочивати** *(time to rest)*. Люди часто їдуть на природу, до річки або до моря. Там вони можуть засмагати на сонці та **купатися** *(to swim)* у теплій воді. Літня погода буває різна. День може бути **сонячний** *(sunny)*, іноді — **хмарний** *(cloudy)* або навіть **вітряний** *(windy)*. Але зазвичай влітку завжди тепло і дуже приємно.

Після спекотного літа настає красива золота осінь. Восени дні стають коротшими, а ночі — довшими. На вулиці вже досить **прохолодно** *(chilly)*. Жовте, червоне та коричневе **листя падає** *(leaves fall)* з дерев на мокру землю. Восени небо часто буває сіре, і **часто дощить** *(it rains often)*. Тому люди одягають теплі куртки, пальта та беруть парасольки. Після осені приходить біла зима. Взимку вся природа спить. Часто **йде сніг** *(it snows)*, і вся земля стає **біла** *(white)* і чиста. На вулиці справжній **мороз** *(frost)*. У таку погоду ми часто кажемо: «Сьогодні **на вулиці морозно** *(it is frosty outside)*». Або ми просто кажемо: «**Мені холодно** *(I am cold)*». Але взимку також дуже весело. Діти можуть грати в сніжки або безпечно кататися на ковзанці.

Усі пори року дуже різні, і ми можемо їх легко порівнювати. Для цього ми використовуємо українські прикметники вищого ступеня. Наприклад, ми знаємо, що **літо тепліше за весну** *(summer is warmer than spring)*. Осінь холодніша за літо, але це ідеальна пора для гарячого чаю. **Зима — найхолодніша пора року** *(winter is the coldest season of the year)*. Якщо ми говоримо про українську погоду, ми також бачимо велику різницю. **Восени більше дощів, ніж влітку** *(in autumn there is more rain than in summer)*. Сонце світить набагато менше. **Взимку дні коротші** *(in winter the days are shorter)*, а ночі стають найдовшими у році. Але кожна людина має свою власну улюблену пору року.

Давайте послухаємо коротку розмову двох друзів про їхні улюблені сезони. Вони використовують фрази «мені подобається» та «тому що».

> — **Олена:** Привіт, Максиме! Скажи, яка твоя улюблена пора року? *(Hi, Maksym! Tell me, what is your favorite season?)*
> — **Максим:** Привіт, Олено! Я обожнюю літо, тому що можна поїхати до моря. *(Hi, Olena! I adore summer because one can go to the sea.)*
> — **Олена:** А мені найбільше подобається золота осінь. *(And I like golden autumn the most.)*
> — **Максим:** Цікаво. А чому ти так любиш осінь? *(Interesting. And why do you like autumn so much?)*
> — **Олена:** Тому що я люблю гуляти в парку, коли тихо падає жовте листя. *(Because I like to walk in the park when yellow leaves fall quietly.)*

<!-- INJECT_ACTIVITY: match-up-seasons-match-seasonal-vocabulary-and-activities -->


## Українські свята: від Різдва до Купала (Ukrainian Holidays)

Українці дуже люблять свої національні традиції. Зимові свята — це особливий і магічний час для кожної української родини. Раніше багато українців святкували **Різдво** *(Christmas)* сьомого січня. Але зараз ми повертаємося до своїх справжніх історичних традицій. Тому сучасна Україна святкує Різдво разом з усім вільним світом — двадцять п'ятого грудня. Це дуже важливий крок для нашої культури. Велике свято починається ввечері двадцять четвертого грудня. Цей тихий сімейний вечір називається **Святий Вечір** *(Holy Supper)*. Уся родина сідає за стіл, коли на темному небі з'являється перша зірка. На святковому столі обов'язково є **дванадцять страв** *(12 dishes)*. Головна страва — це солодка **кутя** *(kutia - sweet grain dish)*. У кімнаті також стоїть **дідух** *(didukh - wheat sheaf)*. Це традиційний сніп пшениці, який символізує предків та хороший майбутній урожай. Дідух — це наш давній український символ. Але зима — це не тільки Різдво. Шостого грудня до українських дітей приходить **Святий Миколай** *(Saint Nicholas)*. Він приносить слухняним дітям довгоочікувані подарунки.

Навесні вся природа прокидається, і приходить велике весняне свято — **Великдень** *(Easter)*. Це найголовніше християнське свято в Україні. Традиційно **на Великдень** *(for Easter)* українці йдуть до церкви. Там вони святять спеціальні продукти у великому святковому кошику. Головний символ цього весняного свята — це красиві **писанки** *(decorated eggs)*. Писанки мають дуже складні, цікаві та унікальні візерунки. Кожен регіон України має свої особливі кольори та символи для писанок. Також українські жінки печуть солодкий традиційний хліб, який називається **паска** *(Easter bread)*. На Великдень люди не кажуть одне одному звичайне «Добрий день». Вони вітаються спеціальними словами: «Христос воскрес!» *(Christ is risen!)*. А інші люди радісно відповідають: «Воістину воскрес!» *(Truly He is risen!)*. Це дуже світле, тепле і радісне свято для всіх людей.

Влітку українці також мають багато цікавих і давніх традицій. Найвідоміше літнє народне свято — це **Івана Купала** *(Ivan Kupala Day)*. Ми святкуємо його в теплу ніч на сьоме липня. Це дуже старе свято, яке тісно пов'язане з природою, водою та магічним вогнем. Молоді дівчата йдуть у поле і плетуть красивий **вінок** *(wreath)* з літніх квітів. Потім вони пускають ці зелені вінки на воду в річку. Ввечері українська молодь збирається разом, співає народні пісні та стрибає через велике **вогнище** *(bonfire)*. Люди здавна вірять, що вогонь очищає людину. Також існує популярна легенда про **цвіт папороті** *(fern flower)*. Кажуть, що ця магічна квітка цвіте тільки одну коротку ніч у році. Хто її знайде, той завжди буде багатий і щасливий. Наприкінці літа ми маємо найважливіше державне свято. Двадцять четвертого серпня ми гордо святкуємо **День Незалежності** *(Independence Day)* України.

Восени ми також маємо дуже важливі національні дати. Першого жовтня Україна святкує **День захисників і захисниць України** *(Day of Defenders of Ukraine)*. У цей осінній день ми щиро дякуємо всім сміливим героям, які захищають нашу рідну країну. Ця дата обрана зовсім не випадково. Історично першого жовтня українські козаки завжди святкували велике свято — **Покрова** *(Intercession)*. Козаки глибоко вірили, що Свята Покрова надійно захищає їх у важкому бою. Сьогодні ми з гордістю продовжуємо цю славну традицію. Для нас надзвичайно важливо **шанувати традиції** *(to honor traditions)* наших мудрих предків. Українці дуже люблять збиратися разом у такі дні. Ми завжди намагаємося **святкувати разом** *(to celebrate together)*, тому що це робить нашу націю сильнішою. Кожне свято — це важлива частина нашої великої історії.

Щоб правильно говорити про всі ці свята, нам треба знати, як українці називають дати. Це дуже просте і логічне граматичне правило. Ми використовуємо порядковий числівник у середньому роді та назву місяця. Назва місяця завжди стоїть у родовому відмінку *(Genitive case)*. Наприклад, ми правильно кажемо «перше вересня», «двадцять п'яте грудня», «сьоме січня». Зверніть увагу: ми обов'язково кажемо «двадцять п'яте», а не «двадцять п'ять». Якщо ми хочемо відповісти на питання «коли?», ми змінюємо перше слово. Ми ставимо всю фразу в родовий відмінок. Прийменник тут зовсім не потрібен. Наприклад: «Коли День Незалежності? — Двадцять четвертого серпня». «Коли Покрова? — Першого жовтня». «Коли приходить Святий Миколай? — Шостого грудня». Запам'ятайте цю дуже просту формулу: Порядковий числівник (Родовий відмінок) + Місяць (Родовий відмінок). Це нове правило допоможе вам правильно говорити про свої дні народження та ваші улюблені свята.

<!-- INJECT_ACTIVITY: quiz-holiday-traditions -->


## Що ми робимо у кожну пору року? (Seasonal Activities)

Кожна пора року має свої особливі і дуже цікаві заняття. Навесні українська природа швидко прокидається після довгої зими, і люди проводять багато часу на вулиці. Українці дуже люблять **садити квіти** *(to plant flowers)* та **працювати в саду** *(to work in the garden)* біля свого дому. Це ідеальний час, щоб зробити свій двір красивим і зеленим. Влітку в Україні зазвичай дуже тепло і сонячно кожного дня. Це найкращий сезон, щоб **подорожувати** *(to travel)* або їздити на Чорне море. Багато людей люблять плавати в чистій воді і **засмагати** *(to sunbathe)* на гарячому пляжі. Восени світлі дні стають набагато коротшими, а погода часто буває прохолодною. Але українці мають дуже популярне осіннє хобі. Ми дуже любимо **збирати гриби та ягоди** *(to pick mushrooms and berries)*. На вихідних ми часто їдемо в ліс, щоб збирати гриби разом із сім'єю. Це неймовірно цікаво і дуже корисно для нашого здоров'я.

Взимку українська природа спокійно відпочиває під холодним білим снігом. Але зимові місяці також пропонують нам багато чудових активностей. Українці дуже люблять **кататися на лижах** *(to ski)* у високих Карпатських горах. У великому місті діти і дорослі часто хочуть **піти на ковзанку** *(to go to the ice rink)* на вихідних. Це завжди дуже веселе та енергійне заняття для всієї родини. Але взимку часто буває дуже холодно і вітряно. **Коли** *(when)* на вулиці сильний **мороз** *(frost)*, люди значно менше гуляють у парках. Коли на вулиці мороз, я люблю пити теплий чай вдома. У такі дні ми читаємо цікаві книги, дивимося старі фільми та проводимо час із сім'єю. Цей приємний контраст між активним літом і дуже спокійною зимою робить наш рік по-справжньому гармонійним.

Щоб розповідати про ці пори року та наші свята, нам потрібні види дієслова. Це **недоконаний вид** *(Imperfective aspect)* і **доконаний вид** *(Perfective aspect)*. Ми завжди використовуємо недоконаний вид для довгих і регулярних процесів. Наприклад, ми кажемо: «**Сніг падав** *(Snow was falling)* цілий день». Це довга дія в минулому, яка ще не має фінального результату. Але коли ми говоримо про конкретний результат дії, ми беремо доконаний вид. Ми кажемо: «Сніг нарешті **розтанув** *(melted)*». Ми часто використовуємо ці дві важливі форми, коли описуємо нашу підготовку до великих свят. Порівняйте ці дві прості фрази. «Ми **готували** *(were preparing)* кутю три години» — це дуже довгий процес напередодні Різдва. А фраза «Ми **приготували** *(have prepared)* смачну вечерю» показує фінальний результат нашої важкої роботи.

Тепер давайте поєднаємо різну погоду і наші регулярні дії в одному реченні. Ми можемо легко використовувати слова **тому що** *(because)*, щоб логічно пояснити причину. Наприклад: «Минулого літа ми часто ходили до річки, тому що було дуже спекотно». Щоб розповісти про свої регулярні дії, ми беремо спеціальні слова. Це корисні прислівники **зазвичай** *(usually)*, **завжди** *(always)* та **іноді** *(sometimes)*. Взимку ми зазвичай святкуємо Різдво вдома з рідними людьми. Навесні ми іноді їздимо в гори, щоб дихати свіжим повітрям. Влітку ми завжди відпочиваємо біля води і багато плаваємо. А восени ми зазвичай збираємо багатий врожай у своєму саду. Такі короткі слова дуже допомагають нам говорити природно, красиво і граматично правильно. 

<!-- INJECT_ACTIVITY: fill-in-grammar-seasons -->


## Мої традиції (My Traditions)

Тепер давайте прочитаємо цікаву історію. Це розповідь українського підлітка про його сімейне свято.

«Моє найулюбленіше зимове свято — це **Різдво** *(Christmas)*. Ми завжди святкуємо його вдома. Наша велика родина збирається разом кожного року. **Спочатку** *(First)* ми довго **готуємо вечерю** *(prepare dinner)*. Моя мама і бабуся роблять дванадцять різних страв. Найголовніша страва на нашому столі — це солодка кутя з медом. **Потім** *(Then)* ми чекаємо, коли на небі з'явиться перша зірка. Вона показує, що свято вже почалося. Коли зірка вже світить, ми нарешті починаємо вечеряти. Але перед вечерею у нас завжди є традиційна **молитва** *(prayer)*. Ми всі дякуємо за цей рік і просимо миру. Після смачної вечері починається найкращий час для нас, дітей. Ми **співаємо колядки** *(sing carols)* і радіємо цьому світлому святу. Наші батьки дають нам чудові **подарунки** *(gifts)*. Ця тепла **родинна вечеря** *(family dinner)* завжди дарує мені багато радості і спокою. Я просто обожнюю цю магічну зимову атмосферу».

А як ви святкуєте ваші свята? У кожної людини є свої улюблені традиції. Щоб розказати про них, ми можемо використовувати такі фрази: «**У моїй країні ми святкуємо** *(In my country we celebrate)*...» або «**Моя улюблена традиція — це** *(My favorite tradition is)*...». Наприклад, ви можете сказати: «У моїй країні ми святкуємо Новий рік на вулиці». Або ви можете розповісти: «Моя улюблена традиція — це робити великий **подарунок для сестри** *(gift for sister)*». Коли ми говоримо про компанію людей, ми використовуємо орудний відмінок. Наприклад, дуже весело **святкувати з друзями** *(to celebrate with friends)* або вечеряти з батьками. Деякі люди люблять гучні вечірки, а інші обирають тихий вечір. Які традиції має ваша сім'я? Ви зазвичай готуєте багато їжі чи замовляєте піцу? Ви любите танцювати всю ніч чи спати? Розкажіть про це своїм друзям.

Українські свята мають дуже глибокий сенс. Вони показують багату історію і культуру народу. Ці давні традиції об'єднують людей різних поколінь. Коли українці співають старі пісні, вони відчувають свій міцний зв'язок з минулим. Це допомагає їм краще розуміти себе. Щоб сказати про свої бажання або мрії, ми використовуємо слова **б** або **би** *(would)*. Це спеціальні форми умовного способу. Наприклад, ви можете сказати: «**Я хотів би** *(I would like)* побачити, як люди **плетуть вінки** *(weave wreaths)* на Купала». Якщо говорить жінка, вона скаже: «**Я хотіла б** *(I would like)* почути українські колядки на Різдво». А **які українські традиції ви хотіли б спробувати** *(what Ukrainian traditions would you like to try)*? Ви хотіли б зробити писанку на Великдень? Або ви б хотіли стрибати через велике вогнище? Кожна традиція — це унікальний досвід.

<!-- INJECT_ACTIVITY: true-false-culture -->


## Підсумок

Ось і все! Сьогодні ми вивчили багато нових і важливих слів. Тепер ви знаєте назви всіх чотирьох пір року. Це **зима** *(winter)*, **весна** *(spring)*, **літо** *(summer)* та **осінь** *(autumn)*. Ви також пам'ятаєте всі дванадцять місяців.

Ми навчилися правильно говорити про час. Пам'ятайте важливу різницю. Слово **зима** — це іменник. А слово **взимку** *(in winter)* — це прислівник. Щоб сказати «in spring», ми кажемо **навесні** *(in spring)*, а не «у весні».

Тепер ви вмієте правильно називати дати. Наприклад: «Сьогодні **перше вересня** *(September first)*». Але якщо це день події: «Свято буде **першого вересня** *(on September first)*». 

Ми також говорили про головні українські свята. Ви знаєте про магічне **Різдво** *(Christmas)* та світлий **Великдень** *(Easter)*. Ви також читали про літнє свято **Івана Купала** *(Ivan Kupala Day)*.

Час перевірити ваші знання. Спробуйте відповісти на ці три питання:
1. Як сказати "in spring" українською мовою?
2. Коли ми святкуємо **День Незалежності** *(Independence Day)*?
3. Що таке **писанка** *(decorated Easter egg)* і коли ми її робимо?

Ви чудово попрацювали сьогодні. До зустрічі у наступному модулі!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: nature-and-traditions
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

**Level: A2 (Module 60/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
