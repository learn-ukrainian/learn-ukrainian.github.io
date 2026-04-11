<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-nominative-accusative.yaml` file for module **32: Багато людей, багато речей** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-nom-plural -->`
- `<!-- INJECT_ACTIVITY: sort-animate-inanimate -->`
- `<!-- INJECT_ACTIVITY: quiz-acc-plural-choice -->`
- `<!-- INJECT_ACTIVITY: error-correction-plural -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the Nominative plural from given singular nouns across all declension
    classes
  items: 8
  type: fill-in
- focus: Sort plural nouns into animate vs. inanimate, then predict their Accusative
    form
  items: 8
  type: group-sort
- focus: Choose the correct Accusative plural form (animate = Gen.Pl., inanimate =
    Nom.Pl.) in sentences
  items: 8
  type: quiz
- focus: Find and fix wrong plural noun endings in Nominative and Accusative (e.g.,
    *дітей грають → діти грають, *бачу студенти → студентів)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відміна (declension class)
- чергування (alternation)
- предмет (object, item)
- група (group)
required:
- множина (plural)
- називний відмінок (nominative case)
- знахідний відмінок (accusative case)
- живий (animate)
- неживий (inanimate)
- закінчення (ending (grammar))
- люди (people)
- діти (children)
- речі (things)
- очі (eyes)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Множина називного відмінка (Nominative Plural)

Сьогодні теплий вихідний день, і велика сім’я гуляє в зоопарку. Вони дивляться на різних тварин і птахів.
> — **Мама:** Діти, подивіться туди! Там спокійно сплять великі **леви** *(lions)*.
> — **Син:** Ого, які вони красиві та сильні! А хто там швидко стрибає?
> — **Тато:** Це веселі **мавпи** *(monkeys)*. Вони дуже люблять активно гратися.
> — **Донька:** Я бачу високі зелені дерева. А біля дерев стоять **жирафи** *(giraffes)*.
> — **Мама:** Так, це справжні жирафи. Вони зараз їдять свіже листя.
> — **Син:** А де живуть птахи? Я дуже люблю **пінгвінів** *(penguins)*! Хочу їх побачити.
> — **Тато:** Пінгвіни живуть там, де холодна вода. Ми зараз ідемо саме до них.
> — **Донька:** Чудово! Я дуже хочу побачити маленьких і смішних пінгвінів.

Ми часто говоримо про предмети або людей у множині. In Ukrainian, changing a noun from singular to plural depends heavily on its gender and its declension class, known as **відміна** *(declension)*. Усі українські іменники мають чотири відміни. You already know that these four classes group nouns by their endings and genders. To form the Nominative plural correctly, we use this system as our roadmap. Кожна відміна має свої правила та закінчення. The endings will also change depending on whether the final consonant of the stem is hard, soft, or mixed. Давайте подивимося на правила для кожної відміни.

Перша відміна — це слова жіночого, чоловічого або спільного роду. Вони завжди закінчуються на «-а» або «-я». The plural endings for this class are very straightforward and depend on the stem. Якщо слово має тверду основу, ми додаємо закінчення «-и». For example, **сестра** *(sister)* becomes **сестри** *(sisters)*, **мама** *(mom)* becomes **мами** *(moms)*, and **книжка** *(book)* becomes **книжки** *(books)*. Якщо слово має м'яку або мішану основу, ми використовуємо закінчення «-і» або «-ї». This makes pronunciation much smoother. Так, **земля** *(land)* becomes **землі** *(lands)*, **суддя** *(judge)* becomes **судді** *(judges)*, and **пісня** *(song)* becomes **пісні** *(songs)*.

Друга відміна є найбільшою. Сюди належить багато слів чоловічого та середнього роду. Let's look at the masculine nouns first. Для слів чоловічого роду з твердою основою стандартне закінчення множини — це «-и». Наприклад, **стіл** *(table)* is **столи** *(tables)*, **завод** *(factory)* is **заводи** *(factories)*, and **телефон** *(phone)* is **телефони** *(phones)*. Якщо основа м'яка або мішана, закінчення змінюється на «-і» або «-ї». Тому **кінь** *(horse)* changes to **коні** *(horses)*, **плащ** *(cloak)* changes to **плащі** *(cloaks)*, and **герой** *(hero)* becomes **герої** *(heroes)*. A very important feature of this group is consonant alternation. Деякі популярні слова змінюють останній приголосний перед закінченням «-і». The most common example you must know is **друг** *(friend)*, which changes to **друзі** *(friends)* in the plural. Another common one is **рік** *(year)*, which becomes **роки** *(years)*.

Тепер подивимося на слова середнього роду другої відміни. Neuter nouns form their plurals differently than masculine nouns in the same class. Замість закінчень «-и» та «-і», слова середнього роду зазвичай отримують закінчення «-а» або «-я». Якщо слово в однині закінчується на «-о», у множині воно матиме закінчення «-а». Наприклад, велике **місто** *(city)* changes to **міста** *(cities)*, **село** *(village)* becomes **села** *(villages)*, and **вікно** *(window)* is **вікна** *(windows)*. If the neuter noun ends in «-е» or «-я» in the singular, it takes the plural ending «-я». Тому **поле** *(field)* becomes **поля** *(fields)*, **море** *(sea)* becomes **моря** *(seas)*, and **обличчя** *(face)* is simply **обличчя** *(faces)* in plural as well.

Третя відміна — це слова жіночого роду, які закінчуються на приголосний звук, а також слово «мати». This class is very consistent and easy to remember. Усі ці слова в називному відмінку множини мають закінчення «-і». Наприклад, темна **ніч** *(night)* becomes **ночі** *(nights)*, **річ** *(thing)* becomes **речі** *(things)*, **подорож** *(journey)* is **подорожі** *(journeys)*, and **сіль** *(salt)* is **солі** *(salts)*. Слово **мати** *(mother)* має особливу форму множини — **матері** *(mothers)*.

Четверта відміна також дуже цікава. Вона об’єднує слова середнього роду, які часто позначають малих тварин або дітей. When forming the plural, these nouns reveal a hidden suffix «-ат-» or «-ят-» before the ending «-а». Наприклад, маленьке **курча** *(chick)* becomes **курчата** *(chicks)*. Так само **теля** *(calf)* changes to **телята** *(calves)*, **кошеня** *(kitten)* becomes **кошенята** *(kittens)*, and **лоша** *(foal)* is **лошата** *(foals)*. Ці слова часто можна почути в селі або в зоопарку.

Деякі українські іменники мають унікальні форми множини. These are common irregular forms that you must memorize as complete lexical units, because they do not follow the standard declension rules. Найважливіші слова — це **людина** *(person)* та **дитина** *(child)*. У множині вони повністю змінюють форму: «людина» стає **люди** *(people)*, а «дитина» стає **діти** *(children)*. Також є слова, які позначають парні частини тіла. Вони зберегли стародавні форми множини. Наприклад, **око** *(eye)* стає **очі** *(eyes)*, **вухо** *(ear)* стає **вуха** *(ears)*, а **плече** *(shoulder)* стає **плечі** *(shoulders)*. Це дуже важливі слова для щоденного спілкування.

<!-- INJECT_ACTIVITY: fill-in-nom-plural -->

## Знахідний відмінок множини: Живе чи неживе? (Accusative Plural: Animate vs. Inanimate)

Тепер ми знаємо, як утворювати називний відмінок множини. Це базова форма для підмета. Але що робити, коли ці слова є прямим додатком у реченні? Ми використовуємо знахідний відмінок дуже часто. Цей відмінок показує об'єкт дії. The Accusative plural has a golden rule that you must memorize. Its form depends entirely on whether the noun is animate, like people and animals, or inanimate, like objects and concepts. For all inanimate nouns, the Accusative plural is exactly the same as the Nominative plural. For all animate nouns, the Accusative plural is exactly the same as the Genitive plural. In the singular, this animate and inanimate split only applied to masculine nouns. In the plural, this rule is absolute and applies to all nouns across all genders and declension classes.

Почнемо з простих неживих предметів. У цьому випадку граматика працює на вас. Якщо предмет неживий, вам не потрібно вчити нове закінчення. Ви просто використовуєте форму називного відмінка множини. Я бачу нові **столи** *(tables)* у цій кімнаті. Вона часто купує цікаві **книжки** *(books)*. Ми дуже любимо ці великі **міста** *(cities)*. Вони будують сучасні **заводи** *(factories)* біля річки. Наші студенти читають довгі **тексти** *(texts)* на уроці. Зверніть увагу, як ці слова діють як прямий додаток у реченні. Це дуже просте і зручне правило для повсякденного спілкування. Because these nouns are not alive, their Accusative form is perfectly identical to their Nominative form.

А тепер поговоримо про живих істот. Це всі люди, тварини, птахи та риби. When the direct object is animate, the Accusative plural borrows its entire form from the Genitive plural. This means you will see completely different endings compared to the subject form. For many masculine nouns, you will add the ending «-ів» or «-їв». For many feminine and neuter nouns, you will often use a zero-ending, which sometimes causes a new vowel to appear inside the word. Я щодня бачу **студентів** *(students)* біля нашого університету. Ми вчора зустріли моїх **сестер** *(sisters)* у центральному парку. Він кожного ранку годує **птахів** *(birds)* біля дому. Олег добре знає цих **лікарів** *(doctors)*. Моя сусідка дуже любить своїх **котів** *(cats)*. Слово «студентів» має типове закінчення «-ів» для чоловічого роду. Слово «сестер» має нульове закінчення, де з'явилася літера «е».

This grammatical rule creates a very common trap for English speakers. In English, we say "I see the tables" and "I see the students" using the exact same plural pattern. Because of this structural similarity, it is highly tempting to say «*Я бачу студенти» in Ukrainian. Це дуже типова помилка. You must actively split the concepts of living and non-living things in your mind. Because "students" are alive, they require the Genitive-matching form. You must say «Я бачу студентів». Ця різниця є дуже важливим маркером природної української мови. Завжди пам'ятайте про це правило, коли говорите про людей!

Давайте уважно подивимося на українські дієслова, які часто вимагають знахідного відмінка. Є спеціальні перехідні дієслова, які ми використовуємо кожного дня. Вони автоматично вимагають цього правила для знахідного відмінка. Вам варто активно практикувати ці популярні дієслова:

* Дієслово **бачити** *(to see)*: Я бачу високі дерева і маленьких птахів.
* Дієслово **знати** *(to know)*: Вона добре знає ці правила і цих людей.
* Дієслово **любити** *(to love)*: Ми любимо гори і своїх розумних собак.
* Дієслово **зустрічати** *(to meet)*: Вони часто зустрічають своїх колег біля метро.
* Дієслово **шукати** *(to look for)*: Він зараз шукає свої ключі та старих друзів.

Найкращий спосіб тренуватися — це будувати змішані контрастні речення. Вони чітко показують різницю між підметом і додатком. На столі лежать нові **підручники** *(textbooks)*. Тут слово «підручники» є підметом у реченні. Але я бачу в аудиторії тільки студентів. Тут слово «студентів» є прямим додатком. Старі **книги** *(books)* стоять на високій полиці. Я беру ці старі книги і йду читати. Мої найкращі **друзі** *(friends)* чекають мене на вулиці. Я дуже радий сьогодні бачити своїх друзів. In these paired examples, you can clearly see how inanimate nouns stay the exact same whether they perform the action or receive the action. However, the animate nouns change their form completely.

<!-- INJECT_ACTIVITY: sort-animate-inanimate -->
<!-- INJECT_ACTIVITY: quiz-acc-plural-choice -->

## Називний чи знахідний? Визначаємо за контекстом (Nominative or Accusative?)

Українська мова має дуже логічну та прозору структуру для кожного речення. Коли ми говоримо про різні речі або людей, ми обов'язково повинні розуміти їхню роль. Who or what is performing the action in the sentence? This is your subject, and it always takes the Nominative case without any exceptions. It answers the basic questions «хто?» or «що?». Але дуже часто наші предмети або люди отримують дію від іншого суб'єкта. What is being seen, read, bought, or built? This is your direct object, and it always takes the Accusative case. It directly answers the questions «кого?» or «що?». Ми успішно використовуємо цей граматичний тест кожного дня у розмовах. Він чудово допомагає нам швидко зрозуміти, який саме відмінок потрібен у конкретному реченні. Якщо розумні **студенти** *(students)* уважно читають текст, слово «студенти» — це називний відмінок. Якщо ми бачимо цих студентів в аудиторії, слово «студентів» — це вже знахідний відмінок.

Тут ми з вами маємо одну надзвичайно цікаву граматичну загадку. Багато українських слів виглядають однаково у називному та знахідному відмінках множини. Це правило стосується всіх неживих предметів. The only way to tell the difference is by carefully looking at the word order and analyzing the core meaning of the verb. Let's look at the simple word **машини** *(cars)*. Якщо ми кажемо «Машини стоять біля нашого будинку», слово «машини» самостійно виконує дію. Тому це чистий називний відмінок. Якщо ми кажемо «Я щоранку бачу нові машини», дія переходить безпосередньо на предмети. Це вже знахідний відмінок, хоча візуальна форма слова зовсім не змінилася. Це правило чудово працює для слів типу **книжки** *(books)*, **телефони** *(phones)* або широкі **поля** *(fields)*. Контекст речення — це завжди наша найкраща граматична підказка.

Давайте уважно подивимося, як ці два відмінки працюють разом у реальному повсякденному житті. Візьмемо для прикладу дуже просте і зрозуміле речення: «Студенти читають нові книжки». Тут живі люди активно виконують дію, а неживі предмети її отримують. Слово «студенти» стоїть у називному відмінку множини. Слово «книжки» логічно стоїть у знахідному відмінку. Це класична і дуже правильна українська структура. Але українська мова дозволяє нам вільно грати зі словами. We can completely swap the semantic roles in the sentence to see how the meaning and the grammar change. Уявіть таке метафоричне речення: «Книжки вчать цих студентів». Тепер наші предмети стали головними суб'єктами дії. Тому слово «книжки» перейшло у називний відмінок. А от слово «студентів» тепер пасивно отримує цю дію. It is an animate noun, so its Accusative form must match the Genitive case exactly.

Найкраще тренувати ці граматичні правила у жвавих місцях, де завжди є багато людей і предметів. Звичайний український міський ринок ідеально підходить для такої розмовної практики.
> — **Олена:** Дивись, який сьогодні шумний ринок! Тут працюють хороші **продавці** *(sellers)*.
> — **Максим:** Так, і тут постійно ходять різні **покупці** *(buyers)*. Я якраз бачу знайомих продавців біля входу.
> — **Олена:** Вони зараз продають свіжі **овочі** *(vegetables)* та солодкі **фрукти** *(fruits)*.
> — **Максим:** Я хочу купити ці красиві овочі на вечерю. Але тут досить високі **ціни** *(prices)*.
> — **Олена:** Ціни завжди швидко ростуть восени. Давай запитаємо тих людей про фрукти.
> — **Максим:** Добре, я знаю цих людей, вони часто роблять приємні знижки.

У цьому діалозі ми бачимо, як називний і знахідний відмінки множини природно змінюють один одного.

Знахідний відмінок у множині також дуже часто працює разом зі спеціальними прийменниками. Certain prepositions always strictly demand the Accusative case when they indicate a direction, a duration of time, or the specific topic of a conversation. Прийменник **через** *(through, across)* показує активний рух: «Ми довго їдемо через високі **гори** *(mountains)*». Прийменник **на** *(onto, for)* часто показує час: «Вони планують поїздку на наступні **вихідні** *(weekend)*». Прийменник **про** *(about)* показує головну тему розмови: «Мої друзі говорять про нові українські **фільми** *(movies)*». You must constantly remember that after these specific prepositions, the plural noun is always in the Accusative case. Навіть для живих людей ми кажемо: «Ми сьогодні читаємо статтю про молодих українських студентів».

Зараз ми разом прочитаємо невеликий текст про звичайний день у нашому університеті. Під час читання спробуйте самостійно знайти всі іменники у множині. Світлі просторі **аудиторії** *(classrooms)* щоранку чекають на студентів. Молоді амбітні **викладачі** *(teachers)* ретельно готують складні **завдання** *(tasks)*. Вони акуратно кладуть нові **маркери** *(markers)* на великі дерев'яні столи. Студенти швидко відкривають свої чисті **зошити** *(notebooks)* і уважно пишуть довгі **речення** *(sentences)*. Викладачі бачать розумних студентів і щиро радіють. У цьому тексті слова «аудиторії» та «викладачі» є головними підметами у чистому називному відмінку. Вони самі виконують дію. Слова «маркери» та «зошити» — це прямі додатки у знахідному відмінку, хоча їхня форма нагадує називний. Слово «студентів» тут чудово показує нам класичний знахідний відмінок для живих істот.

<!-- INJECT_ACTIVITY: error-correction-plural -->

## Підсумок

Сьогодні ми зробили великий крок уперед. Ми вивчили, як працює **множина** *(plural)* для різних слів. Тепер ви можете вільно говорити про багато предметів. Ви також вмієте описувати великі **групи** *(groups)* людей. Давайте швидко перевіримо ваші знання. Дайте відповіді на ці короткі **запитання** *(questions)*.

- Яке **закінчення** *(ending)* мають іменники першої відміни в називному відмінку множини? Вони зазвичай мають закінчення «-и» після твердих приголосних або «-і» після м'яких.
- Яка головна **різниця** *(difference)* між знахідним відмінком для живих істот і неістот? Для живих істот форма завжди збігається з родовим відмінком. А для неістот ця форма повністю збігається з називним відмінком.
- Як правильно перекласти англійську фразу "I see children"? Ми кажемо: «Я бачу дітей». Це наш прямий **додаток** *(object)* у реченні.
- Чи змінюються назви неживих предметів у знахідному відмінку множини порівняно з називним? Ні, ці форми завжди залишаються однаковими.
- Назвіть правильну множину для слів «людина», «дитина», «око». Це дуже важливі **винятки** *(exceptions)*: «люди», «діти», «очі».

Ви чудово попрацювали сьогодні. Ці граматичні правила дуже часто зустрічаються в реальному житті. Тому продовжуйте активно практикувати їх щодня.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-nominative-accusative
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

**Level: A2 (Module 32/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
