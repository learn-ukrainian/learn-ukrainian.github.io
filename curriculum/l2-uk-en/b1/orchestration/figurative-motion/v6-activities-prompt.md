<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/figurative-motion.yaml` file for module **31: Час іде, дощ іде** (b1).

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

- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: group-sort -->`
- `<!-- INJECT_ACTIVITY: fill-in -->`
- `<!-- INJECT_ACTIVITY: error-correction -->`
- `<!-- INJECT_ACTIVITY: free-write -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify whether a motion verb is used literally or figuratively in a sentence
  items: 12
  type: quiz
- focus: Complete Ukrainian figurative expressions with the correct motion verb
  items: 12
  type: fill-in
- focus: Match figurative motion expressions with their meanings
  items: 12
  type: match-up
- focus: 'Sort motion verb uses: literal / figurative — time / weather / abstract'
  items: 12
  type: group-sort
- focus: Fix English calques and Russicisms in figurative motion expressions
  items: 12
  type: error-correction
- focus: Write a paragraph about your week using at least 5 figurative motion expressions
  items: 12
  type: free-write


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- 'злетіти (to soar — figurative: prices soar)'
- водити за ніс (to deceive — idiom)
- вийти (to turn out / result)
- підійти (to suit — figurative)
- дійти до висновку (to reach a conclusion)
- обійтися (to get by without)
- хмари пливуть (clouds drift)
- мурашки біжать (goosebumps)
- багатозначне слово (polysemous word)
- фразеологізм (phraseological unit / idiom)
required:
- переносне значення (figurative meaning)
- пряме значення (literal meaning)
- дощ іде (it's raining — figurative use of іти)
- час іде (time passes)
- час летить (time flies)
- справи йдуть (things are going — about progress)
- мова йде про (it's about / the topic is)
- 'йтися (impersonal — to be about: йдеться про)'
- нести відповідальність (to bear responsibility)
- вести переговори (to conduct negotiations)
- вести себе (to behave)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслова руху в переносному значенні

В українській мові слова часто мають не одне, а кілька значень. Це явище називається **багатозначність** (polysemy), а саме слово — **багатозначне слово** (polysemous word). Коли ми вивчаємо нову лексику, ми зазвичай запам'ятовуємо **пряме значення** (literal meaning). Наприклад, пряме значення дієслова руху «іти» — це переміщатися за допомогою ніг (to move on foot). Ми кажемо: «Хлопчик іде до школи» (The boy is walking to school) або «Жінка іде на роботу» (The woman is walking to work). Це фізична дія, яку ми можемо легко побачити та виміряти. Але мова — це гнучка система. З часом люди починають використовувати знайомі слова для опису інших явищ за подібністю ознак (by similarity of features). Так виникає **переносне значення** (figurative meaning). В українській мові дієслова руху надзвичайно часто вживаються в переносному значенні. Ми щодня кажемо: «**Дощ іде**» (It's raining) або «**Час іде**» (Time passes). Фізично дощ і час не мають ніг, вони не можуть крокувати (step). Але їхня дія нагадує нам безперервний рух. Розуміння переносного значення — це ключ до природної, справжньої української мови. Без нього мова звучить штучно (artificially) і занадто механічно. Тому ми повинні навчитися відчувати ці дієслова так, як їх відчувають носії мови (native speakers).

Українські школярі знайомляться з концепцією переносного значення ще в початкових класах на уроках лексикології (lexicology). У підручнику Олександра Авраменка для п'ятого класу є дуже показовий діалог (a very revealing dialogue). Уявіть ситуацію: старша сестра дивиться у вікно на темні хмари (dark clouds) і каже своєму маленькому брату: «Візьми парасольку, скоро піде дощ» (Take an umbrella, it will start raining soon). Брат, який ще тільки пізнає світ і сприймає слова буквально (literally), здивовано питає: «А хіба дощ має ноги, щоб ходити?» (But does rain have legs to walk?). Це дитяче запитання ідеально ілюструє суть переносного значення. Дитина знає пряме значення (рух ногами), але ще не розуміє переносного (процес падіння крапель). Переносне значення — це значення, перенесене з одних предметів чи явищ на інші за подібністю (transferred from some objects or phenomena to others based on similarity). Дощ не крокує, але його наближення і падіння ми уявляємо як рух до нас. Тому для українців дощ саме «іде», а не просто падає зверху вниз.

Коли ми аналізуємо лексичне значення слова (the lexical meaning of a word), ми бачимо, як первинне значення (primary meaning) — рух на ногах — розширюється і створює нові, вторинні значення (secondary meanings). Це розширення не є випадковим (random). Воно підпорядковується певній логіці мислення. В українській мові дієслова руху найчастіше вживаються переносно, коли йдеться про явища природи (natural phenomena) або плин часу. Ми виділяємо кілька основних категорій переносного руху. Перша категорія — це час: секунди, хвилини, дні та роки не стоять на місці, вони постійно рухаються вперед. Друга категорія — це погода: опади (precipitation) сприймаються як активні учасники дії. Третя категорія — це події та соціальні процеси (events and social processes): заходи (events), уроки, фільми також мають свій початок і кінець, тобто проходять певну дистанцію. Четверта категорія — це абстрактні відносини (abstract relations) та стани (states): наші думки, емоції та навіть слова можуть «рухатися» в розмові. Кожна з цих категорій використовує свою специфічну групу дієслів. Найбільший і найширший спектр (the widest spectrum) має дієслово «іти», але ми також будемо активно використовувати «летіти», «пливти», «бігти» та їхні префіксальні форми (prefixed forms).

> **Олена:** Дивись, які темні хмари збираються над деревами.
> **Марія:** Так, уже **дощ іде**! Відчуваєш перші краплі на обличчі? Треба відкривати парасольку.
> **Олена:** Відчуваю. Знаєш, я думала... Як же швидко **час іде**, правда? Здається, тільки вчора ми зустрічали весну, а вже кінець літа.
> **Марія:** Ой, і не кажи. Літо стрімко йде до кінця. Але осінь теж має свою красу. До речі, як **справи йдуть** на твоїй новій роботі?
> **Олена:** Усе йде за планом. Зараз **мова йде про** наше майбутнє, про новий великий проєкт у Європі. Сподіваюся, все вийде.

У цьому діалозі подруги не використовують дієслово «іти» для опису фізичного крокування. Жоден предмет не переміщається на ногах. Вони обговорюють погоду («дощ іде»), швидкість життя («час іде»), прогрес у кар'єрі («справи йдуть») та тему дискусії («мова йде про»). Це типова, природна розмова двох українців, яка повністю побудована на переносних значеннях.

## Iти / ходити: найширший спектр

Дієслово «іти» (та його недоконана пара «ходити») має найширший спектр переносних значень (the widest spectrum of figurative meanings) в українській мові. Почнемо з погодних явищ (weather phenomena). В українській картині світу опади не просто падають зверху вниз, вони активно діють і рухаються в просторі. Тому «іти» — це головне дієслово для опису опадів. Ми говоримо: «**Дощ іде**» (It is raining), «Сніг іде» (It is snowing), «Град іде» (It is hailing), «Дрібна мжичка іде» (A fine drizzle is falling). В англійській мові ви використовуєте дієслово "to fall" (падати) або безособову конструкцію "it is raining". Англомовні студенти часто роблять типову помилку (a typical mistake) і намагаються перекласти це дослівно: «*дощ падає*» (rain falls). Хоча в деяких західних регіонах України можна почути такий вислів як поетичну або діалектну форму, стандартна літературна норма (standard literary norm) вимагає використання дієслова руху. Українська погода «крокує» (walks). Наприклад: «Надворі йде сильний дощ, тому ми залишимося вдома» (It is raining heavily outside, so we will stay home). Або в минулому часі: «Вчора йшов сніг цілий день, і дороги замело» (It snowed all day yesterday, and the roads were covered).

Друга велика категорія — це плин часу (the passage of time). Час не стоїть на місці, він має свій ритм і постійний рух. Для опису цього неухильного, стабільного та нейтрального ритму ми використовуємо дієслово «іти». Це не швидкий біг і не повільне повзання, це нормальний хід подій (normal course of events). Ми часто говоримо: «**Час іде**» (Time passes), «Годинник іде» (The clock is ticking/running), «Роки йдуть» (Years go by), «Століття йдуть» (Centuries pass). Дієслово «іти» ідеально передає ідею безперервного (continuous) і незупинного (unstoppable) потоку часу. Наприклад, ви можете сказати: «Ідуть дні, тижні, місяці, а ситуація не змінюється» (Days, weeks, months pass, but the situation doesn't change). Або: «Рік іде за роком, і ми стаємо дорослішими» (Year goes after year, and we become older). У цих випадках «іти» означає просто «минати» (to pass). Коли ми дивимося на механічний годинник, ми бачимо, як рухаються його стрілки (hands). Цей рух механізму українці теж називають словом «іде»: «Мій новий годинник іде дуже точно» (My new watch runs very accurately).

Третя категорія охоплює різноманітні події та соціальні процеси (events and social processes). Усе, що має розклад (schedule), тривалість і певний сценарій, також «іде». Наприклад, коли ми говоримо про кінематограф, ми не кажемо, що фільм «показують» (хоча це можливо граматично). Найприродніше сказати: «Цей фільм іде в кінотеатрах» (This film is showing in cinemas). Так само ми описуємо навчальний процес: «Тихо, зараз урок іде!» (Quiet, the lesson is in progress!). Культурні заходи теж мають свій рух: «Концерт іде вже дві години» (The concert has been going on for two hours). Якщо у вашому будинку працюють будівельники, ви скажете: «У нас зараз ремонт іде» (We have renovations underway). В офіційному контексті ми часто чуємо: «Переговори йдуть складно» (Negotiations are proceeding with difficulty). І, звісно, дуже популярний вираз для опису загального прогресу — «**Справи йдуть**» (Things are going). «Як ідуть твої справи?» (How are your things going?) — «Дякую, мої **справи йдуть** чудово» (Thanks, my things are going great). Дієслово «іти» тут показує, що процес триває, він є активним і розвивається в часі, на відміну від статичного дієслова «відбуватися» (to occur).

У сфері абстрактної логіки (abstract logic) та ідіом дієслово «іти» відіграє ключову роль. Найважливіший вираз, який ви повинні запам'ятати для дискусій — це «**мова йде про**» (we are talking about / the topic is). Наприклад: «У цій статті **мова йде про** нові реформи» (This article is about new reforms). Проте, зверніть увагу: хоча цей вираз дуже поширений, мовознавці часто називають його калькою (calque) з російської. Більш автентичною, питомо українською формою є безособове дієслово (impersonal verb) «**йтися**» — «**йдеться про**» (it concerns / it is about). Замість «мова йде про безпеку» краще сказати: «У документі **йдеться про** безпеку» (The document is about safety). Також дієслово «іти» утворює важливі сталі вирази (fixed expressions) для опису нашої поведінки в складних ситуаціях. Наприклад, «йти на компроміс» (to compromise): «Уряд пішов на компроміс із протестувальниками» (The government compromised with the protesters). Або «йти на ризик» (to take a risk): «Він пішов на великий ризик, коли відкрив цей бізнес» (He took a great risk when he opened this business). Ще один корисний вираз — «йти назустріч» (to meet halfway / accommodate): «Керівництво пішло нам назустріч і змінило графік» (The management accommodated us and changed the schedule).

Коли ми додаємо префікси (prefixes) до дієслова «іти», ми отримуємо нові, ще більш абстрактні переносні значення. Розглянемо найуживаніші з них. Дієслово «**вийти**» (to go out) у переносному значенні означає «дати результат» (to turn out / to result). Ми кажемо: «У мене **вийшов** гарний пиріг» (My pie turned out well) або «На жаль, нічого не вийшло» (Unfortunately, nothing worked out). Дієслово «**підійти**» (to approach) використовується, коли щось нам пасує або відповідає нашим потребам (suits or meets our needs): «Цей колір тобі дуже підходить» (This color really suits you) або «Такий варіант нам не підходить» (Such an option doesn't suit us). Дієслово «**дійти**» (to reach) часто вживається для опису ментального процесу (mental process): «Після довгих роздумів я **дійшов до висновку**, що це помилка» (After long reflections, I reached the conclusion that this is a mistake). А дієслово «**обійтися**» (to walk around) означає впоратися без чогось (to get by without something): «Ми обійдемося без вашої допомоги» (We will get by without your help). Ці префіксальні форми роблять нашу мову значно багатшою (significantly richer).

<!-- INJECT_ACTIVITY: match-up -->

## Летіти: швидкість

Дієслово «**летіти**» (to fly) у своєму прямому значенні описує рух птахів або літаків у повітрі. Але в переносному значенні воно стає головним інструментом для опису екстремальної швидкості (extreme speed) і стрімкого плину часу (rapid passage of time). Якщо час, який «іде» — це нормальний, спокійний ритм нашого життя, то час, який «летить» — це час, якого нам завжди не вистачає. Ми використовуємо цей вираз, коли ми дуже зайняті, щасливі або здивовані тим, як швидко минули події. Українці часто вигукують: «Як швидко **час летить**!» (How fast **time flies**!). Це універсальна емоційна реакція. Ми можемо сказати: «Мої вихідні просто пролетіли, я навіть не встиг відпочити» (My weekend just flew by, I didn't even have time to rest). Або: «**Дні летять** як одна мить» (Days fly by like a single moment). Коли ви зустрічаєте старого друга, якого давно не бачили, ви обов'язково скажете: «Боже, як летять роки! Твої діти вже такі дорослі» (God, how years fly! Your children are already so grown up). Дієслово «летіти» передає відчуття, що ми не можемо контролювати цей рух, він занадто швидкий для нас.

Окрім часу, «летіти» чудово описує швидке поширення інформації (rapid spread of information) або раптову зміну стану (sudden change of state). Уявіть, що сталася якась сенсаційна подія. Інформація про неї не просто поширюється, вона «летить». Ми кажемо: «Ця новина швидко облетіла все місто» (This news quickly spread around the whole city). Префікс «об-» тут показує, що інформація охопила всю територію, обігнувши її. Ще одне дуже важливе використання пов'язане з економікою та фінансами. Коли вартість товарів раптово і дуже сильно зростає, ми використовуємо дієслово «**злетіти**» (to take off / to soar). Префікс «з-» означає різкий рух знизу вгору. Наприклад: «Минулого місяця ціни на продукти стрімко **злетіли** вгору» (Last month, grocery prices skyrocketed). Або: «Вартість оренди квартир злетіла до небес» (The cost of renting apartments soared to the skies). Це набагато емоційніше і виразніше, ніж просто сказати «ціни виросли» (prices grew).

У розмовному стилі (colloquial style) дієслово «летіти» з різними префіксами часто використовується для опису швидких, іноді неприємних, соціальних ситуацій. Наприклад, дієслово «вилетіти» (to fly out) може означати втрату роботи або статусу через порушення правил. Якщо студент не склав іспити і його відрахували (expelled), ми кажемо: «Він вилетів з університету» (He flew out of the university). Якщо людину раптово звільнили з посади (fired from a position), це звучить так: «Він зі скандалом вилетів з роботи» (He flew out of work with a scandal). А якщо на вас раптово нападає сильна емоція або природна стихія, ви скажете: «Раптом налетів сильний вітер» (Suddenly a strong wind swooped in). Або якщо на вас хтось раптово почав кричати без причини: «Він налетів на мене з претензіями» (He swooped in on me with complaints). Ці розмовні форми додають мові динаміки (add dynamics to the language) і дуже часто зустрічаються в повсякденному спілкуванні (everyday communication). Розуміння цих префіксів допоможе вам швидше реагувати на несподівані зміни (unexpected changes) у розмові.

<!-- INJECT_ACTIVITY: quiz -->

## Пливти: плавність і повільність

Якщо «летіти» — це швидкість, то дієслово «пливти» (to swim / to drift) у переносному значенні — це абсолютна протилежність. Це плавність (smoothness), повільність (slowness), грація і відсутність різких рухів. У прямому значенні ми пливемо у воді. Вода створює опір (resistance), тому рух у ній завжди більш плавний. Українці переносять цю плавність на спостереження за природою. Коли ми дивимося в небо і бачимо, як повільно і беззвучно рухаються хмари, ми кажемо: «По небу **хмари пливуть**» (Clouds are drifting across the sky). Цей рух настільки спокійний, що нагадує рух човна (boat) по озеру. Так само ми можемо описати вечірній пейзаж: «Яскравий місяць повільно пливе між зірками» (A bright moon slowly drifts among the stars). А якщо вранці над річкою збирається густа димка (thick mist), ми опишемо це так: «Білий туман пливе над водою» (White fog drifts over the water). В усіх цих поетичних образах (poetic images) дієслово «пливти» підкреслює гармонію природи. Милуватися тим, як по небу повільно пливуть хмари, можна годинами. Цей рух не має чіткої цілі, він є частиною великого природного циклу (great natural cycle).

Ця ідея плавного потоку (smooth flow) чудово підходить для опису абстрактних ідей — наших думок (thoughts) та звуків. Коли людина мріє (dreams) або глибоко замислилася (is deeply in thought), її думки не стрибають, вони переходять одна в одну дуже м'яко. Ми кажемо: «Мої думки повільно пливуть» (My thoughts are slowly drifting). Так само ми сприймаємо гарну музику. Звуки можуть обволікати (envelop) нас, створюючи єдиний потік: «У залі тихо пливе чарівна мелодія» (A magical melody quietly flows in the hall). Дуже цікаво порівняти сприйняття часу. Ми вже знаємо вираз «час летить» (time flies — fast, stressful). Але коли ми відпочиваємо біля моря, нікуди не поспішаємо і насолоджуємося моментом, ми скажемо інакше: «Тут час повільно пливе» (Here time drifts slowly). Обидва вирази описують плин часу, але вони мають абсолютно протилежні емоційні конотації (opposite emotional connotations). «Летіти» — це стрімкість і брак часу, а «пливти» — це тривалість, спокій і мрійливість (dreaminess). Коли ви використовуєте дієслово «пливти» в контексті часу, ви ніби зупиняєте мить і дозволяєте собі просто спостерігати за тим, як життя розгортається перед вами (unfolds before you). Це дуже корисне слово для опису медитативних станів (meditative states) або спогадів (memories).

<!-- INJECT_ACTIVITY: group-sort -->

## Бігти, їхати, нести та інші

Дієслово «бігти» (to run) у переносному значенні займає золоту середину (golden middle) між нормальним ритмом «іти» та екстремальною швидкістю «летіти». Воно передає ідею поспіху (hurrying) та інтенсивної зайнятості. Ми можемо сказати: «Час біжить так непомітно, що я не встигаю закінчити проєкт» (Time runs so imperceptibly that I don't have time to finish the project). Тут час не просто минає, він ніби тікає від нас. Крім того, «бігти» дуже часто описує рух рідини (liquids) та фізичні відчуття на тілі. Українці кажуть: «Чиста вода швидко біжить у гірській річці» (Clean water runs quickly in the mountain river). А якщо ви відчуваєте раптовий страх (fear), хвилювання або холод, ваше тіло реагує специфічно. Українською мовою цей стан описується прекрасною ідіомою: «У мене аж **мурашки біжать** по шкірі» (I even have goosebumps — literally 'ants are running' — on my skin). Це дуже яскравий образ: маленькі мурахи (ants), які швидко пересуваються вашим тілом.

Дієслово «їхати» (to go by vehicle) рідше використовується в літературних переносних значеннях, але воно надзвичайно популярне в сучасному молодіжному сленгу (modern youth slang) та розмовній мові. Найвідоміший розмовний вираз — «дах їде» (the roof is going), що означає «божеволіти» (to go crazy) або втрачати контроль над думками від стресу чи втоми (fatigue). Ви можете почути: «Після десяти годин роботи за комп'ютером у мене вже просто дах їде!» (After ten hours of working at the computer, my roof is simply going / I'm going crazy!). Інший цікавий розмовний варіант — «їхати на чомусь» (to ride on something), що означає бути надзвичайно зацикленим (obsessed) або сфокусованим на якійсь одній ідеї: «Він зовсім поїхав на здоровому харчуванні» (He is completely obsessed with healthy eating). Молодь також любить використовувати вираз «поїхати» в значенні втрати адекватності (loss of adequacy): «Він зовсім поїхав зі своїми теоріями змов» (He completely lost it with his conspiracy theories). Хоча ці вирази не варто використовувати в офіційному есе (formal essay) або на діловій зустрічі (business meeting), їх розуміння критично важливе для перегляду сучасних українських серіалів (modern Ukrainian series) або спілкування в соціальних мережах (social networks).

Дієслова «нести» (to carry) та «вести» (to lead) і їхні неозначені пари «носити» та «водити» створюють багато офіційних, ділових виразів. Наприклад, у юриспруденції (jurisprudence) та бізнесі ми використовуємо вираз «**нести відповідальність**» (to bear responsibility): «Кожен працівник несе відповідальність за свою роботу» (Every employee bears responsibility for their work). Або «носити ім'я» (to bear a name): «Ця красива центральна вулиця носить ім'я Тараса Шевченка» (This beautiful central street bears the name of Taras Shevchenko). Що стосується «вести», то це стандартне слово для організації процесів. Дипломати та політики повинні «**вести переговори**» (to conduct negotiations). Учитель у школі часто каже учням: «Вам треба добре **вести себе** на уроці!» (You need to behave well in class!). Ще одна цікава ідіома — «**водити за ніс**» (to deceive / lead by the nose), що означає обманювати людину (to deceive a person): «Цей продавець довго водив нас за ніс, перш ніж ми зрозуміли його хитрощі» (This seller led us by the nose for a long time before we realized his tricks).

:::caution
Вираз «**вести себе**» (to behave) є дуже поширеним у розмовній мові, але авторитетні мовознавці (linguists) вважають його калькою з російського «вести себя». Більш природним і правильним українським словом є дієслово «**поводитися**» (to behave). Тому замість «веди себе добре» краще і грамотніше сказати «поводься добре».
:::

Префіксальні форми (prefixed forms) цих дієслів також дуже корисні для висловлення абстрактних ідей. Дієслово «донести» (to carry up to) часто використовується в значенні «пояснити», «передати інформацію» (to convey an idea): «Спікер намагався донести свою головну думку до аудиторії» (The speaker tried to convey his main idea to the audience). Дієслово «принести» (to bring) може стосуватися не лише речей, а й абстрактних концептів: «Ця блискуча перемога принесла йому великий успіх та популярність» (This brilliant victory brought him great success and popularity). А дієслово «провести» (to lead through) стало стандартним терміном для організації різних подій: «Наш університет планує провести важливий науковий захід наступного тижня» (Our university plans to hold an important scientific event next week). Усі ці форми показують, як фізична дія — переміщення об'єкта або ведення людини — трансформується у вплив на абстрактні процеси та події в суспільстві.

<!-- INJECT_ACTIVITY: fill-in -->

## Українські вирази vs англійські кальки

Коли ви починаєте говорити українською мовою, ваш мозок автоматично намагається перекласти структури з вашої рідної англійської. Це природний процес, але він призводить до появи кальок (calques) — дослівних перекладів (literal translations), які граматично можливі, але стилістично неприродні. Найбільш класичний приклад такої кальки — це фраза «*дощ падає*» (rain falls). Як ми вже обговорювали раніше, в українській мові погодні явища є активними суб'єктами (active subjects), які мають свій власний рух. Вони не підкоряються простому закону гравітації (law of gravity), вони «крокують» землею. Тому ми завжди маємо казати «**дощ іде**», «сніг іде». Звичайно, ви можете почути вислів «падає сніг» у віршах (poems) або в західних регіонах України, де є певний вплив інших мов, але літературний стандарт вимагає дієслова «іти». Те саме стосується часу. Англомовний студент може сказати «*час пробігає*» (time runs by) або «*час минає швидко*», намагаючись скопіювати англійські конструкції. Проте найприроднішими варіантами залишаються наші дієслова руху в чистій формі: «**час іде**» (нейтрально), «**час летить**» (дуже швидко), «час біжить» (із поспіхом). А коли ми говоримо про кіно, краще сказати «фільм іде» (the film is showing), а не «*фільм показують*» (the film is being shown). Завжди запитуйте себе: «Чи звучить це так, як сказала б моя українська бабуся?» (Always ask yourself: "Does this sound like my Ukrainian grandmother would say it?").

Окрім англійських кальок, українська мова століттями зазнавала потужного тиску з боку російської мови. Це призвело до появи багатьох русизмів (Russicisms) — виразів, які скопійовані з російської. Однією з найчастіших помилок є використання виразу «*діло йде*» або «*справи є добре*» (the latter is an English calque "things are good"). В українській мові ми використовуємо красивий і природний вираз «**справи йдуть**» (things are going). Ми кажемо: «Мої справи йдуть чудово» (My things are going great). Ще одна величезна проблема — це вираз «**мова йде про**». Ви часто будете чути його на вулиці, по телевізору і навіть читати в газетах. Однак авторитетні мовознавці (authoritative linguists), такі як Борис Антоненко-Давидович, наголошують, що це пряма калька з російського виразу «речь идет о». Справжня українська мова має для цього елегантне і коротке безособове дієслово «**йтися**». Тому замість конструкції «У цій книзі мова йде про історію України» (In this book the topic is the history of Ukraine), інтелігентна людина скаже: «У цій книзі **йдеться про** історію України» (This book is about the history of Ukraine). Використання форми «йдеться» — це маркер вашої високої мовної культури та глибокого розуміння природи українського слова.

Чому українська мова так активно використовує саме дієслова руху для абстрактних понять? Відповідь лежить у культурній логіці (cultural logic) та світогляді (worldview) нашого народу. Для українців навколишній світ — природа, час, абстрактні явища — ніколи не був просто статичною декорацією (static background). Світ завжди сприймався як живий організм (living organism), який дихає, діє і рухається разом із людиною. Час не просто існує, він — активний учасник нашого життя, він «іде» або «летить» поруч із нами. Дощ — це не просто вода, що падає з неба під впливом фізики, це гість (guest), який «приходить» на наші поля, щоб дати їм життя. Коли ми кажемо «справи йдуть», ми підсвідомо (subconsciously) наділяємо наші соціальні процеси енергією руху (energy of movement). Використання цих переносних дієслів руху — це не просто граматичне правило (grammar rule). Це спосіб думати українською (a way to think in Ukrainian). Коли ви перестаєте перекладати слова у своїй голові і починаєте бачити, як хмари «пливуть», а ціни «злітають», ви робите величезний крок до справжнього мовного занурення (linguistic immersion). Ви починаєте бачити світ очима українців.

<!-- INJECT_ACTIVITY: error-correction -->

## Підсумок: буквальне і переносне

Ми завершуємо наше дослідження (exploration) переносного всесвіту дієслів руху. Ви побачили, як базові слова, що означають фізичне переміщення, трансформуються в потужні інструменти для опису часу, природи та людських емоцій. Давайте підсумуємо цей спектр у короткій таблиці:

| Дієслово руху | Пряме значення (Literal) | Переносне значення (Figurative) | Приклади |
|---|---|---|---|
| **іти** | Рухатися на ногах (to walk) | Погода, нейтральний час, заходи | Дощ іде, час іде, урок іде |
| **летіти** | Рухатися в повітрі (to fly) | Висока швидкість, стрімкий час | Час летить, ціни злетіли |
| **пливти** | Рухатися у воді (to swim/drift) | Плавність, повільність, думки | Хмари пливуть, мелодія пливе |
| **бігти** | Швидко пересуватися (to run) | Поспіх, рух рідини, відчуття | Вода біжить, мурашки біжать |
| **нести** | Тримати в руках (to carry) | Відповідальність, імена, статус | Нести відповідальність |
| **вести** | Спрямовувати когось (to lead) | Організація процесів, поведінка | Вести переговори |

Знання цих **фразеологізмів** (phraseological units) та переносних значень робить вашу українську живою, динамічною та природною. Ви більше не звучите як машина, що перекладає словник (dictionary), ви звучите як людина, що відчуває пульс мови (pulse of the language). Кожен із цих виразів — це маленьке вікно в український спосіб мислення (a small window into the Ukrainian way of thinking). 

Тепер час перевірити ваші знання (time to check your knowledge). Спробуйте відповісти на ці запитання без підглядання в текст:
1. Як правильно сказати "It's raining" українською мовою без використання кальки з англійської?
2. Яке дієслово найкраще описує дуже швидкий, непомітний біг часу, коли ви чимось сильно захоплені?
3. У чому полягає емоційна та смислова різниця між виразами «час летить» і «час пливе»?
4. Яке українське слово краще використати замість русизму «вести себе»?
5. Як сказати "The book is about history" використовуючи правильне безособове дієслово?

У наступному модулі (M36) на нас чекає «Подорож Україною». Ми об'єднаємо ці переносні форми з буквальними дієсловами руху, щоб навчитися розповідати захопливі історії про подорожі нашими прекрасними містами та горами.

<!-- INJECT_ACTIVITY: free-write -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: figurative-motion
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

**Level: B1 (Module 31)**

**Instructions in Ukrainian.** All activity types appropriate.


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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
