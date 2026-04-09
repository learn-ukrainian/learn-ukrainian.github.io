<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/comparison.yaml` file for module **54: Більше, краще, найкраще** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-form-the-comparative-from-the-base-adjective -->`
- `<!-- INJECT_ACTIVITY: true-false-identify-correct-and-incorrect-comparative-constructions-genitive-traps -->`
- `<!-- INJECT_ACTIVITY: match-up-match-adjective-to-its-superlative-form -->`
- `<!-- INJECT_ACTIVITY: quiz-suppletive-choice-choose-the-correct-suppletive-form -->`
- `<!-- INJECT_ACTIVITY: error-correction-comparison-find-and-fix-wrong-comparative-and-superlative-forms-double-comparison-russianisms -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the comparative from the base adjective
  items: 8
  type: fill-in
- focus: Choose the correct suppletive form (більший, кращий, гірший)
  items: 8
  type: quiz
- focus: Match adjective to its superlative form
  items: 8
  type: match-up
- focus: Identify correct and incorrect comparative constructions
  items: 8
  type: true-false
- focus: Find and fix wrong comparative and superlative forms (e.g., *більш кращий
    → кращий, *гарніший → кращий/гарніший)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- набагато (much, significantly)
- трохи (a little, slightly)
- значно (considerably)
- навпаки (on the contrary)
required:
- порівняння (comparison)
- більший (bigger)
- менший (smaller)
- кращий (better)
- гірший (worse)
- найкращий (the best)
- найбільший (the biggest)
- солодший (sweeter)
- цікавіший (more interesting)
- ніж (than)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вищий ступінь: порівнюємо два предмети

Сьогодні ми вчимося порівнювати два предмети. В українській мові ми використовуємо для цього **вищий ступінь порівняння** *(comparative degree)*. Але пам'ятайте одне дуже важливе правило. Ми можемо порівнювати тільки **якісні прикметники** *(qualitative adjectives)*. Це слова, які описують певну **якість** *(quality)*, що може бути більшою або меншою. Наприклад, ми можемо порівнювати **розмір** *(size)*, **швидкість** *(speed)*, температуру або **смак** *(taste)*. Ми не можемо сказати «більш дерев'яний» або «більш залізний». Але ми з радістю можемо сказати «більш солодкий» або «більш солоний». Це основа для правильного спілкування.

Дуже часто ми утворюємо вищий ступінь за допомогою короткого **суфікса -ш-** *(suffix -ш-)*. Ми просто додаємо цей суфікс до основи базового слова. Але тут є один маленький **фонетичний** *(phonetic)* секрет. Якщо прикметник має суфікси **-к-**, **-ок-** або **-ек-**, вони зазвичай **зникають** *(disappear)* перед додаванням нового суфікса. Це дуже часте явище в українській мові. Подивіться на ці типові приклади.
Слово **солодкий** *(sweet)* втрачає свій суфікс **-к-**. Воно стає новим словом **солодший** *(sweeter)*.
Слово **тонкий** *(thin)* також швидко втрачає **-к-**. Ми отримуємо зручне слово **тонший** *(thinner)*.
А слово **короткий** *(short)* перетворюється на **коротший** *(shorter)*.
Це проста форма порівняння. Вона звучить дуже **природно** *(naturally)*. Українці використовують її щодня.

Інший дуже популярний суфікс — це **-іш-**. Це найбільш **продуктивний** *(productive)* спосіб утворити вищий ступінь порівняння. Ми додаємо його до багатьох різних прикметників. Він дуже **зручний** *(convenient)* для вимови. Ось кілька типових і корисних прикладів.
Слово **цікавий** *(interesting)* легко стає словом **цікавіший** *(more interesting)*.
Слово **теплий** *(warm)* швидко перетворюється на **тепліший** *(warmer)*.
Ви також можете впевнено сказати **гарніший** *(nicer)* від слова **гарний** *(nice)*. Це абсолютно правильна регулярна **альтернатива** *(alternative)*.
Цікаво, що слово **швидкий** *(fast)* має дві можливі форми. Ви можете сказати **швидший** або **швидкіший** *(faster)*. Обидва варіанти правильні та зрозумілі. Вибирайте той суфікс, який вам зараз легше вимовляти.

Коли ми додаємо суфікс **-ш-**, дуже часто відбувається **чергування приголосних** *(consonant mutation)*. Це абсолютно природний фонетичний **процес** *(process)*. Звуки просто змінюються, щоб слово було набагато легше вимовляти. Є три головні правила, які вам треба запам'ятати.
Перше правило: звуки **г**, **ж**, **з** плюс суфікс **-ш-** завжди дають новий звук **жч**. Наприклад, слово **дорогий** *(expensive)* стає словом **дорожчий** *(more expensive)*. Слово **близький** *(close)* стає **ближчий** *(closer)*. А слово **дужий** *(strong)* стає **дужчий** *(stronger)*.
Друге правило: звук **с** плюс **-ш-** разом дають звук **щ**. Тому слово **високий** *(tall)* стає словом **вищий** *(taller)*.
Третє правило: звуки **ст** плюс **-ш-** також дають звук **щ**. Наприклад, слово **товстий** *(thick)* має дві правильні форми: **товстіший** або **товщий** *(thicker)*. Особливо слова «дорожчий» та «вищий» є дуже популярними у щоденних розмовах.

<!-- INJECT_ACTIVITY: fill-in-form-the-comparative-from-the-base-adjective -->

В українській мові також успішно існує **складена форма** *(compound form)* порівняння. Для неї ми використовуємо спеціальні слова **більш** *(more)* або **менш** *(less)*. Після них завжди йде звичайна форма прикметника. Ця форма часто звучить трохи більш **офіційно** *(formally)* або книжно. Ми зазвичай використовуємо її для тонких **нюансів** *(nuances)*. Також вона дуже потрібна для довгих або складних багатоскладових слів. Наприклад, ми часто кажемо **більш відомий** *(more famous)*. Або ми можемо сказати **менш популярний** *(less popular)*. Це дійсно дуже простий спосіб порівняння, але прості форми з суфіксами звучать більш природно.

Як правильно будувати цілі речення з порівнянням? В українській мові є дві правильні синтаксичні **конструкції** *(constructions)*. Вони мають абсолютно однакове значення, але зовсім різну граматику.
Перша поширена конструкція використовує слово **ніж** *(than)* та **називний відмінок** *(Nominative case)*. Наприклад: «Цей новий телефон дорожчий, ніж той». Зверніть увагу на обов'язкову кому перед словом «ніж».
Друга конструкція використовує прийменник **за** *(than)* та **знахідний відмінок** *(Accusative case)*. Наприклад: «Цей новий телефон дорожчий за той». Тут жодна кома не потрібна. Обидві форми дуже активно використовуються в розмовній мові. Ви можете сміливо вибирати ту конструкцію, яка вам зараз більше подобається.

Прочитайте цей короткий діалог у магазині електроніки. Він добре показує, як звичайні люди щодня порівнюють різні речі в реальному житті.
> — **Покупець:** Добрий день! Я зараз шукаю новий сучасний **смартфон** *(smartphone)*.
> — **Консультант:** Добрий день! Будь ласка, подивіться на ці дві популярні моделі.
> — **Покупець:** Цей екран **більший** *(bigger)*, але телефон також дуже дорогий.
> — **Консультант:** Так, ви маєте рацію. Але ця чорна модель **дешевша** *(cheaper)* за ту. Вона має трохи **менший** *(smaller)* екран.
> — **Покупець:** Розумію. Але мені дуже потрібен телефон, який працює швидше.
> — **Консультант:** Тоді перший варіант точно **кращий** *(better)* для вас. Він значно **потужніший** *(more powerful)*, ніж цей другий варіант.

<!-- INJECT_ACTIVITY: true-false-identify-correct-and-incorrect-comparative-constructions-genitive-traps -->


## Найвищий ступінь: хто найкращий?

Іноді нам потрібно сказати, що певний предмет має **найвищий ступінь** *(the highest degree)* конкретної якості. Це означає, що він просто **найкращий** *(the best)* серед усіх інших предметів у групі. В українській мові ми утворюємо **просту форму** *(simple form)* найвищого ступеня дуже легко і швидко. Ми беремо готову форму вищого ступеня і просто додаємо префікс **най-** *(the most)*. Це дуже важливе граматичне правило. Ми завжди використовуємо основу вищого ступеня, а не початкову форму прикметника. Наприклад, слово **солодший** *(sweeter)* миттєво стає словом **найсолодший** *(the sweetest)*. Слово **цікавіший** *(more interesting)* перетворюється на **найцікавіший** *(the most interesting)*. А популярне слово **дорожчий** *(more expensive)* стає словом **найдорожчий** *(the most expensive)*. Ви просто додаєте один маленький префікс до слова. Ця форма є найбільш природною, традиційною і частотною в українській мові. Ви будете постійно чути її кожного дня.

Також в українській мові успішно існує **складена форма** *(compound form)* найвищого ступеня. Для неї ми використовуємо спеціальні окремі слова **найбільш** *(the most)* або **найменш** *(the least)*. Після цих слів завжди йде звичайна початкова форма прикметника без жодних змін. Наприклад, ми часто кажемо **найбільш популярний** *(the most popular)* актор або **найменш відомий** *(the least famous)* письменник. Ця форма звучить трохи більш офіційно і формально. Її дуже часто використовують у телевізійних новинах, офіційних документах або для довгих наукових слів. Але у звичайних щоденних розмовах українці завжди частіше вибирають просту форму з префіксом **най-**.

Іноді ми хочемо зробити наш найвищий ступінь ще сильнішим і виразнішим. Для цього ми використовуємо спеціальні граматичні **підсилювачі** *(intensifiers)*. Ми просто додаємо короткі частки перед нашим стандартним префіксом **най-**. У нас логічно виходять подвійні префікси **якнай-** *(as ... as possible)* та **щонай-** *(the very ...)*. Вони успішно додають нове емоційне значення: «настільки сильно, наскільки це можливо» або «абсолютно». Наприклад, слово **швидкий** *(fast)* стає словом **якнайшвидший** *(as fast as possible)*. Ми часто кажемо: «Знайдіть якнайшвидший шлях додому». А відоме слово **кращий** *(better)* перетворюється на чудову форму **щонайкращий** *(the very best)*. Ви також можете впевнено сказати **якнайтепліший** *(as warm as possible)*. Ці красиві форми роблять вашу українську мову дуже природною, багатою та глибокою.

Тепер обов'язково поговоримо про одну дуже серйозну і поширену помилку. Багато людей помилково використовують слово **самий** *(the most)*, щоб утворити найвищий ступінь. Наприклад, вони часто кажуть «самий великий» або «самий новий телефон». Це велика лексична помилка і класичний **русизм** *(Russianism)* у нашій мові. Українська мова **ніколи** *(never)* не використовує слово «самий» для порівняння прикметників. Це правило є дуже строгим і принциповим. Замість цього чужого російського слова ми завжди використовуємо наш рідний префікс **най-**. Тому популярна фраза ❌ «самий кращий» є абсолютно неправильною і неприродною. Ви повинні завжди говорити тільки ✅ **найкращий**. Фраза ❌ «самий розумний студент» — це теж груба помилка. Правильний український варіант — це ✅ **найрозумніший** *(the smartest)*. Будь ласка, назавжди забудьте конструкцію зі словом «самий» і завжди обирайте правильні українські форми.

Давайте із задоволенням прочитаємо короткий пізнавальний текст про **українські рекорди** *(Ukrainian records)*. Він чудово показує, як ці форми працюють на реальній практиці. Україна — це надзвичайно велика та дуже цікава європейська країна. Вона має багато унікальних туристичних місць. **Найвища гора** *(the highest mountain)* в Україні — це знаменита Говерла. Вона гордо знаходиться у мальовничих Карпатах. **Найбільше місто** *(the biggest city)* — це наша велична столиця, красень Київ. Тут щодня живе і працює дуже багато людей. А в історичному центрі Києва є **найглибша станція** *(the deepest station)* метро. Вона відома і називається «Арсенальна». Це не тільки найглибша станція в усій Україні, але й у цілому світі. Як бачите, наш префікс **най-** чудово допомагає нам розповідати про найкращі та найцікавіші речі.

<!-- INJECT_ACTIVITY: match-up-match-adjective-to-its-superlative-form -->


## Особливі форми: більший, кращий, гірший

В українській мові є кілька важливих прикметників, які повністю змінюють свій корінь. Це **особливі форми** *(irregular forms)*, які треба добре запам'ятати. Слово **великий** *(big)* ніколи не стає «величіший». Воно змінюється на слово **більший** *(bigger)*. Найвищий ступінь — це **найбільший** *(the biggest)*. Це правило також працює для слова **малий** *(small)*. Його вищий ступінь — це **менший** *(smaller)*, а найвищий — **найменший** *(the smallest)*. Ви можете сказати: «Мій новий дім **більший**, ніж старий». Або: «Ця проблема значно **менша**, не хвилюйся». Ці базові форми є дуже важливим фундаментом вашого щоденного спілкування.

Тепер розглянемо особливі форми для якості. Базове слово **добрий** *(good)* або **гарний** *(good, nice)* має вищий ступінь **кращий** *(better)*. Найвищий ступінь — це популярне слово **найкращий** *(the best)*. Іноді українці використовують слово **ліпший** *(better)*. Це гарний синонім, але форма **кращий** є більш універсальною для рівня А2. Для антоніма **поганий** *(bad)* ми маємо форму **гірший** *(worse)*. Її найвищий ступінь — це **найгірший** *(the worst)*. Ці слова також повністю змінюють свій вигляд. Ми часто кажемо: «Сьогодні погода **гірша**, ніж учора». Або: «Це **найкращий** день у моєму житті!». Обов'язково вивчіть ці чотири важливі слова.

<!-- INJECT_ACTIVITY: quiz-suppletive-choice-choose-the-correct-suppletive-form -->

Далі ми маємо поговорити про **прислівники** *(adverbs)*. Прислівники, які утворені від якісних прикметників, також мають ступені порівняння. Вони працюють за такою ж простою логікою. Слово **добре** *(well)* стає словом **краще** *(better)*. Слово **погано** *(badly)* змінюється на **гірше** *(worse)*. Слово **багато** *(a lot)* має форму **більше** *(more)*. А слово **мало** *(a little)* перетворюється на **менше** *(less)*. Для звичайних прислівників ми використовуємо стандартний суфікс. Наприклад, слово **швидко** *(fast)* стає формою **швидше** *(faster)*. Ви можете легко порівнювати різні дії: «Він читає **швидше**, ніж я». Ці короткі слова роблять ваші розповіді більш динамічними.

Зараз ми обговоримо одну типову помилку. Це так зване **подвійне порівняння** *(double comparison)*. Ми ніколи не можемо поєднувати слово **більш** *(more)* та форму вищого ступеня на -ший. Наприклад, фраза ❌ «більш кращий» — це велика помилка. Слово **кращий** вже означає «better». Якщо ви додаєте слово «більш», виходить «more better», що є абсолютно неправильним. Те ж саме стосується найвищого ступеня. Фраза ❌ «найбільш найкращий» є логічно некоректною. Ви повинні обрати тільки один спосіб порівняння. Ви можете сказати складену форму ✅ **більш гарний**. Або ви можете використати просту форму ✅ **кращий**. Обидва варіанти є правильними.

Давайте прочитаємо короткий діалог про вибір ресторану. Двоє друзів обговорюють, де краще пообідати сьогодні. Зверніть увагу на особливі форми.
> — **Марко:** Привіт! Підемо в нове кафе чи у старий ресторан? *(Hi! Shall we go to the new cafe or the old restaurant?)*
> — **Оксана:** Я думаю, що старий ресторан **кращий**. Там їжа значно смачніша. *(I think the old restaurant is better. The food there is much tastier.)*
> — **Марко:** Це правда, але ціни там **більші**. *(That's true, but the prices there are bigger.)*
> — **Оксана:** Можливо, але для мене якість — це **найкращий** аргумент. *(Maybe, but for me, quality is the best argument.)*
> — **Марко:** Погоджуюсь. Це справді **найкращий** варіант. *(I agree. This is indeed the best option.)*

<!-- INJECT_ACTIVITY: error-correction-comparison-find-and-fix-wrong-comparative-and-superlative-forms-double-comparison-russianisms -->


## Порівняння у житті

Іноді нам потрібно показати, наскільки велика різниця між предметами чи діями. Для цього ми використовуємо спеціальні слова, які підсилюють значення. Найпопулярніші з них — це **набагато** *(much)*, **значно** *(significantly)* та **трохи** *(a bit)*. Вони завжди стоять перед формою вищого ступеня. Ви можете просто сказати: «Ця квартира більша». Але якщо різниця справді дуже велика, ви кажете: «Ця квартира набагато більша». Слово «значно» має абсолютно такий самий зміст, але воно звучить трохи офіційніше. Наприклад: «Новий робочий проєкт значно **цікавіший** *(more interesting)*». Якщо ж різниця мінімальна, ми використовуємо слово «трохи». Наприклад: «Мій молодший брат трохи менший, ніж я». Іноді в неформальній розмові українці кажуть слово **куди** *(way)*. Фраза «куди краще» означає «набагато краще». Ці короткі слова роблять ваше мовлення точним і дуже природним.

Давайте подивимося, як ми використовуємо ці форми щодня. Прочитайте діалог двох колег. Вони планують спільну літню відпустку і активно порівнюють два популярні українські міста. Зверніть увагу на слова-підсилювачі.

> — **Олена:** Куди ми поїдемо відпочивати влітку? До Львова чи до Одеси? *(Where will we go to rest in the summer? To Lviv or to Odesa?)*
> — **Павло:** Я думаю, що Львів **старіший** *(older)* і значно цікавіший. *(I think Lviv is older and significantly more interesting.)*
> — **Олена:** Так, це правда, але Одеса **тепліша** *(warmer)*. Там є Чорне море. *(Yes, that's true, but Odesa is warmer. There is the Black Sea there.)*
> — **Павло:** Згоден. Але дорога до Одеси значно **довша** *(longer)*. *(I agree. But the road to Odesa is significantly longer.)*
> — **Олена:** І квитки на нічний поїзд до Одеси трохи **дорожчі** *(more expensive)*. *(And tickets for the night train to Odesa are a bit more expensive.)*
> — **Павло:** Тоді Львів — це точно найкращий варіант для нас зараз. *(Then Lviv is definitely the best option for us now.)*

Тепер прочитайте коротку розповідь. Автор порівнює своє життя зараз і в минулому. Зверніть увагу на форми прикметників і прислівників. Вони допомагають описати життєві зміни.

«Мій ідеальний день зараз набагато **спокійніший** *(calmer)*, ніж раніше. Три роки тому я жив у Києві. Це найбільше місто в Україні. Життя там було значно швидше і дуже стресове. Раніше я прокидався **пізніше** *(later)*, бо часто працював вночі. Мій старий офіс був більший. Але дорога туди була найгіршою частиною дня.

Зараз я живу в Тернополі. Це місто менше, але воно куди **комфортніше** *(more comfortable)* для мене. Я прокидаюся **раніше** *(earlier)* і маю вільний час для ранкової кави. Моя нова квартира трохи менша за стару. Проте вона набагато **світліша** *(brighter)* і тепліша. Найкраще в моєму новому житті — це довга вечірня прогулянка в парку. Тут повітря **чистіше** *(cleaner)*, а люди навколо гуляють **повільніше** *(slower)*. Я думаю, що такі зміни — це завжди на краще.»


## Підсумок

Ось і все! Тепер ви знаєте, як порівнювати різні предмети, людей та дії українською мовою. Повторімо три головні правила цього уроку. *(That's it! Now you know how to compare different objects, people, and actions in Ukrainian. Let's review the three main rules of this lesson.)*

По-перше, прості форми вищого ступеня мають спеціальні суфікси **-ший** або **-іший** *(comparative suffixes)*. Для найвищого ступеня ми завжди додаємо префікс **най-** *(superlative prefix)* до простої форми.

По-друге, обов'язково пам'ятайте про зміну приголосних звуків *(consonant changes)*. Наприклад, звук «г» часто змінюється на «жч» (дорогий — дорожчий). А звук «с» змінюється на «щ» (високий — вищий).

По-третє, треба запам'ятати чотири дуже важливі особливі слова. Це **більший** *(bigger)*, **менший** *(smaller)*, **кращий** *(better)* та **гірший** *(worse)*. Їхні унікальні форми треба просто знати напам'ять.

Перевірте себе *(Check yourself)*:
1. Як сказати "the most interesting" одним словом?
2. Чому ми ніколи не кажемо «самий великий»? Яка українська форма є правильною?
3. Як граматично порівняти два предмети за допомогою слова **за** *(than)*? (Наприклад, порівняйте каву і чай).

Якщо ви знаєте відповіді на ці запитання, ви готові до наступної теми. Ви — **найкращі** *(the best)*!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: comparison
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

**Level: A2 (Module 54/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


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
