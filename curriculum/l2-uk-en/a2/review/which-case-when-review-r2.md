## Linguistic Scan
No linguistic errors found.

## Exercise Check
Marker inventory: only one marker is present, `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`.

Issues:
- The plan expects four activity slots/types (`quiz`, `group-sort`, `fill-in`, `true-false`), but the module contains only one marker total.
- The markers are not spread through the module; they are fully clustered at the end of the only written section.
- The sole marker is a poor fit for its location: the plan’s true/false focus explicitly mentions contrasts like `на роботу` vs `на роботі`, but the module never reaches the preposition section where that contrast should be taught.
- No inline DSL exercises are present, so there is no exercise logic to validate beyond marker placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 3/10 | The module stops after `## Дієслово вирішує: Який відмінок після дієслова? (~600 words)` and `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`. Searches on the provided content returned `## Прийменник вирішує: 0`, `## Особливі випадки: 0`, `## Алгоритм вибору відмінка: 0`, so three planned sections and their plan points are missing. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, surzhyk, calques, paronym errors, wrong case forms, or forbidden Russian characters were found in the provided prose. The supplied VESUM note says all checked words exist, and spot checks for debatable forms like `напряму`, `прем'єром`, `керує`, `потребує` also passed. |
| 3. Pedagogical quality | 5/10 | The written section does give multiple examples for verb-governed cases, e.g. `Я читаю книгу. Ми шукаємо ключі.` and `Я допомагаю сестрі. Ми щиро дякуємо вчителям.` But the promised systematic decision process from the plan is not taught because the algorithm section is absent, and there is no distributed practice after each major concept. |
| 4. Vocabulary coverage | 4/10 | Some required words are used naturally, e.g. `відмінок`, `прийменник`, `дієслово`, `думати`, `боятися`, `користуватися`. But required plan vocabulary is missing from the prose: searches returned `напрямок: 0`, `місце: 0`, `характеристика: 0`. |
| 5. Exercise quality | 2/10 | Only one marker exists: `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`. The plan requires four activity types, and the lone true/false marker comes before the module teaches the key location/direction contrasts named in the plan. |
| 6. Engagement & tone | 9/10 | The opening classroom frame is concrete and usable: `Сьогодні ми граємо в граматичних детективів. Ми читаємо українську газету...` The teacher voice is mostly warm and focused on the grammar task rather than corporate/gamified fluff. |
| 7. Structural integrity | 2/10 | The pipeline word count is 732, far below the 2000-word target. Structurally, only one H2 section is present, while the plan specifies four core sections. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian grammar on its own terms and makes no decolonizing/cultural errors. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue has named speakers and a real instructional situation: `Президент зустрівся з прем'єром. Для журналістів підготували зал`. It is short, but it is still more natural than a purely transactional drill. |

## Findings
- [PLAN ADHERENCE] [SEVERITY: critical]  
  Location: The module ends after `## Дієслово вирішує: Який відмінок після дієслова? (~600 words)` and `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`  
  Issue: Three planned sections are missing entirely: `Прийменник вирішує`, `Особливі випадки`, and `Алгоритм вибору відмінка`. That also removes core plan points such as `на + Acc.` vs `на + Loc.`, `у/в + Acc.` vs `у/в + Loc.`, `по + Loc.`, `з/із + Gen./Instr.`, `за + Acc./Instr.`, time expressions, locative characteristics, years, and the decision process.  
  Fix: Insert the three missing sections after the first activity marker, covering the missing preposition rules, special uses, and the step-by-step algorithm.

- [STRUCTURAL INTEGRITY] [SEVERITY: critical]  
  Location: `**PIPELINE NOTE — Word count: 732 words**`  
  Issue: The module is far below the 2000-word target. This is not a minor shortfall; most of the planned lesson content is absent.  
  Fix: Add the missing sections in full so the module reaches the planned scope and clears the word target.

- [VOCABULARY COVERAGE] [SEVERITY: major]  
  Location: Whole module; searches on the provided content returned `напрямок: 0`, `місце: 0`, `характеристика: 0`  
  Issue: Required vocabulary from the plan is missing from the prose, even though these concepts are central to the omitted sections.  
  Fix: Add those required words explicitly and naturally in the new preposition/special-use sections.

- [EXERCISE QUALITY] [SEVERITY: major]  
  Location: `<!-- INJECT_ACTIVITY: true-false-case-pairs -->`  
  Issue: There is only one marker total, so the plan’s `quiz`, `group-sort`, and `fill-in` activities are missing. The existing true/false marker is also misplaced, because the module has not yet taught the preposition contrasts that the plan says this activity should test.  
  Fix: Change the current marker to a quiz marker for verb-governed cases, then add `group-sort`, `fill-in`, and `true-false` markers after the later sections where those topics are actually taught.

## Verdict: REVISE
Multiple critical findings block shipment: three planned sections are missing, the module is only 732 words against a 2000-word target, and the activity flow is incomplete and mispositioned.

<fixes>
- find: "<!-- INJECT_ACTIVITY: true-false-case-pairs -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-verb-governed-cases -->"
- insert_after: "<!-- INJECT_ACTIVITY: quiz-verb-governed-cases -->"
  content: |
    
    ## Прийменник вирішує: Один прийменник — різні відмінки (The Preposition Decides: One Preposition, Different Cases)
    
    Дуже часто саме **прийменник** підказує, який відмінок потрібен. Але тут важливо дивитися не лише на саме слово, а й на **контекст**: чи ми говоримо про **напрямок**, чи про **місце**; про рух, чи про перебування.
    
    Один із найважливіших прикладів для рівня A2 — це «на». Коли є рух до цілі, ми вживаємо знахідний відмінок: Я йду **на роботу**. Ми ставимо чашку **на стіл**. Студенти прийшли **на лекцію**. Тут «на» показує напрямок: куди?
    
    Якщо ж руху немає і ми описуємо місце, вживаємо місцевий відмінок: Я вже **на роботі**. Книга лежить **на столі**. Студенти сидять **на лекції**. Отже, одна й та сама форма прийменника не означає один і той самий відмінок: усе вирішує значення.
    
    > *Very often it is the preposition itself that tells you which case to use. But here you must look at context too: are we talking about direction or location; movement or being somewhere? One of the most important A2 examples is `на`. With movement toward a goal, use the accusative: `Я йду на роботу`. With location, use the locative: `Я на роботі`.* 
    
    Те саме бачимо з прийменниками «у/в». Коли хтось кудись вирушає, потрібен знахідний: Я йду **в магазин**. Вона заходить **у кімнату**. Ми сідаємо **в автобус**. Але коли людина або предмет уже перебуває в певному місці, потрібен місцевий: Я **в магазині**. Вона чекає **у кімнаті**. Ми розмовляємо **в автобусі**.
    
    Прийменники «у/в» також часто виражають **час**. Для днів тижня в українській мові звично вживати знахідний: **у середу**, **у четвер**, **у п'ятницю**. Наприклад: У четвер ми пишемо тест. У середу я працюю з дому. У п'ятницю вони їдуть до бабусі. Тут легко побачити зв'язок між часом і питанням коли?
    
    Місцевий відмінок після «у/в» часто вживається для років і часових контекстів: **у 2014 році**, **у двадцять першому столітті**, **у дитинстві**. Ми кажемо: У 2014 році він жив у Львові. У дитинстві вона любила малювати. У двадцять першому столітті люди багато спілкуються онлайн.
    
    > *The same contrast works with `у/в`: accusative for direction (`в магазин`, `у кімнату`, `в автобус`) and locative for location (`в магазині`, `у кімнаті`, `в автобусі`). These prepositions also appear in time expressions: accusative for days (`у четвер`) and locative for years or periods (`у 2014 році`, `у дитинстві`).*
    
    Ще один дуже корисний прийменник — «по». У цьому модулі нас цікавить уживання з місцевим відмінком, коли ми говоримо про шлях, поверхню або маршрут руху: ходити **по вулиці**, бігати **по кімнаті**, гуляти **по парку**, їздити **по місту**, подорожувати **по Україні**. Тут ідея не в точці призначення, а в русі всередині певного простору.
    
    З прийменником «з/із» треба розрізняти два значення. Якщо ми говоримо «звідки?», уживаємо родовий: вийти **з дому**, приїхати **з Києва**, взяти книжку **зі столу**. Якщо ж говоримо «з ким?» або «з чим?», уживаємо орудний: піти **з другом**, говорити **з учителем**, кава **з молоком**. Значення тут повністю змінює відмінок.
    
    Подібно працює і «за». Коли ми говоримо про плату, причину подяки або обмін, уживаємо знахідний: дякувати **за допомогу**, платити **за квитки**, боротися **за місце** в команді. Але коли йдеться про положення «позаду» або про рух слідом, уживаємо орудний: сидіти **за столом**, стояти **за будинком**, бігти **за автобусом**.
    
    Хороша звичка для учня — не запам'ятовувати прийменник окремо, а вчити коротку пару: **на роботу / на роботі**, **в магазин / в магазині**, **з дому / з другом**, **за допомогу / за столом**. Так ви одразу бачите і форму, і значення.
    
    <!-- INJECT_ACTIVITY: group-sort-prepositions-by-case -->
    
    ## Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics, Path)
    
    Тепер подивімося на кілька вживань, які особливо часто збивають з пантелику. Формально вони прості, але в живому мовленні їх легко переплутати, якщо думати лише про переклад.
    
    Почнімо з часу. Для назв днів тижня після «у/в» ми вже бачили знахідний: **у середу**, **у четвер**, **у п'ятницю**. Так само знахідний часто з'являється в словосполученнях на кшталт: **цю неділю** я відпочиваю, **цей вечір** ми проводимо вдома. Але поруч із цим в українській мові є інший шаблон: **наступного тижня**, **минулого року**, **цього місяця**. Тут уживається родовий, і це треба просто впізнавати як окрему часову модель.
    
    Наприклад: Цю неділю ми їдемо в село. Наступного тижня у мене екзамен. Минулого року вони жили в Одесі. У четвер я телефоную сестрі, а в п'ятницю зустрічаюся з друзями. Такі пари корисно вивчати разом, щоб відчути, який відмінок запускає кожен часовий вираз.
    
    > *Time expressions are not all built the same way. Ukrainian uses the accusative for day names like `у четвер` and often for phrases like `цю неділю`, but it uses the genitive in patterns like `наступного тижня` or `минулого року`.*
    
    Інший важливий випадок — це **характеристика** людини через одяг або зовнішню ознаку. У такому значенні часто вживаємо «у/в» + місцевий відмінок: хлопець **у червоному светрі**, дівчина **в окулярах**, жінка **у білому пальті**, чоловік **у темному піджаку**. Тут ми не говоримо, де людина перебуває. Ми даємо їй опис, тобто характеристику.
    
    Порівняйте: Хлопець **у кімнаті** читає книжку. Хлопець **у червоному светрі** читає книжку. У першому реченні `у кімнаті` відповідає на питання де? і називає місце. У другому `у червоному светрі` не називає місце, а описує зовнішній вигляд людини. Форма схожа, але функція інша.
    
    Місцевий також часто вживається для ширшого часового тла: **у 2014 році**, **у дитинстві**, **у двадцять першому столітті**. Це не конкретний день, а період або рамка, у межах якої щось відбувається. Наприклад: У дитинстві я боявся темряви. У 2014 році вони переїхали до Києва. У двадцять першому столітті цифрові навички дуже важливі.
    
    Ще одна модель із місцевим — це шлях після «по». Ми кажемо: діти бігають **по кімнаті**, туристи гуляють **по парку**, автобус їздить **по місту**, мандрівники подорожують **по Україні**. Цей шаблон передає рух усередині певного простору, а не рух до однієї кінцевої точки.
    
    Якщо ви вагаєтеся, подумайте так: чи це місце призначення, чи простір руху; чи це адреса, чи опис; чи це окремий день, чи ширший часовий період. Таке запитання швидко повертає вас до правильної форми.
    
    <!-- INJECT_ACTIVITY: fill-in-mixed-case-triggers -->
    
    ## Алгоритм вибору відмінка (The Case Selection Algorithm)
    
    Тепер зберімо все в один **алгоритм**, щоб ви могли не вгадувати форму, а свідомо її обирати.
    
    Крок 1: подивіться, чи є в реченні прийменник. Якщо є, починайте саме з нього. Наприклад, у фразі `на роботі` саме прийменник `на` разом зі значенням місця підказує місцевий відмінок. У фразі `за допомогу` прийменник `за` у значенні причини або плати запускає знахідний.
    
    Крок 2: якщо прийменника немає, знайдіть дієслово. Саме дієслово часто керує формою іменника. `Допомагати` вимагає давального: допомагати **сусідові**. `Користуватися` вимагає орудного: користуватися **словником**. `Боятися` вимагає родового: боятися **собак**. `Бачити` вимагає знахідного: бачити **будинок**.
    
    Крок 3: якщо ви все ще не впевнені, поставте відмінкове питання. Кого? Що? Кому? Чому? Ким? Чим? На кому? На чому? Питання не замінює правила, але добре допомагає перевірити себе після того, як ви знайшли дієслово або прийменник.
    
    > *Now we turn everything into one decision process. Step 1: look for a preposition. Step 2: if there is no preposition, find the governing verb. Step 3: if you are still unsure, test the noun with the case question. This gives you a repeatable method instead of guesswork.*
    
    Спробуймо пройти алгоритм на кількох прикладах.
    
    1. Я йду ___ магазин. Є прийменник `в`. Значення — напрямок, а не місце. Отже, потрібен знахідний: `в магазин`.
    2. Я працюю ___ магазині. Є прийменник `в`. Значення — місце. Отже, потрібен місцевий: `в магазині`.
    3. Я дякую ___ сестрі. Прийменника немає. Дієслово `дякувати` керує давальним. Отже, `сестрі`.
    4. Ми користуємося ___ словником. Прийменника немає. Дієслово `користуватися` керує орудним. Отже, `словником`.
    5. У четвер ми говоримо ___ майбутнє. Є прийменник `про`, а він вимагає знахідного. Отже, `про майбутнє`.
    
    Найпоширеніші помилки в цьому модулі такі:
    - плутати `на роботу` і `на роботі`;
    - плутати `в кімнату` і `в кімнаті`;
    - після `допомагати` ставити знахідний замість давального;
    - забувати, що `думати` тут уживається з `про` + знахідний;
    - бачити форму з `у/в` і автоматично думати тільки про місце, хоча інколи це час або характеристика.
    
    Якщо коротко, логіка така: **прийменник → значення → відмінок**. Якщо прийменника немає, тоді **дієслово → відмінок**. А вже після цього ми добираємо правильне закінчення. Саме так працює компас відмінків у повсякденному мовленні.
    
    <!-- INJECT_ACTIVITY: true-false-case-pairs -->
</fixes>