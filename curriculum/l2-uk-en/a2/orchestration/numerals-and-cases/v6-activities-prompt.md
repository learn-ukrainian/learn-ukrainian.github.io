<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/numerals-and-cases.yaml` file for module **55: Числа у відмінках** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-ordinals -->`
- `<!-- INJECT_ACTIVITY: match-up-numeral-meanings -->`
- `<!-- INJECT_ACTIVITY: group-sort-agreement -->`
- `<!-- INJECT_ACTIVITY: quiz-noun-selection -->`
- `<!-- INJECT_ACTIVITY: fill-in-decline-ordinal-numerals-in-context-of-dates-and-addresses -->`
- `<!-- INJECT_ACTIVITY: match-up-match-numeral-expressions-to-their-correct-form -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Decline ordinal numerals in context (dates, addresses)
  items: 8
  type: fill-in
- focus: Choose the correct noun form after a numeral (Nom.Pl. vs Gen.Pl.)
  items: 8
  type: quiz
- focus: Sort numerals by which noun case they require (Nom.Sg., Nom.Pl., Gen.Pl.)
  items: 8
  type: group-sort
- focus: Match numeral expressions to their correct Ukrainian form
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- обидва (both, m.)
- обидві (both, f.)
- десяток (a ten, a dozen)
- пів (half)
required:
- числівник (numeral)
- порядковий (ordinal)
- кількісний (cardinal)
- перший (first)
- третій (third)
- один (one)
- скільки (how many)
- кілограм (kilogram)
- коштувати (to cost)
- вік (age)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Порядкові числівники: -ий та -ій (Ordinal Numerals: -ий and -ій)

Ми часто рахуємо різні предмети. Наприклад, ми кажемо: **один квиток** (one ticket), **два квитки** (two tickets), **три квитки** (three tickets). Це кількісні числівники (cardinal numerals). Вони просто показують загальну кількість предметів.
Але іноді нам важливо знати порядок предметів або людей у черзі. Для цього ми використовуємо **порядкові числівники** (ordinal numerals). Вони відповідають на питання «який?» (which one?), «яка?», «яке?» або «котрий?» (which in order?).
Порядкові числівники працюють як звичайні прикметники (adjectives). Вони мають рід (gender), число (number) та відмінок (case). Вони завжди узгоджуються з іменником, який стоїть поруч.
Порівняйте ці дві ситуації. Ми маємо **два квитки** (two tickets). Але я хочу взяти саме **другий квиток** (the second ticket). Кількісний числівник «два» просто рахує квитки. А порядковий числівник «другий» описує конкретний квиток.

Більшість порядкових числівників мають тверде закінчення **-ий** (hard ending -ий). Вони відмінюються (decline) як звичайні тверді прикметники, наприклад, слово «новий» (new).
Ось найчастіші порядкові числівники з твердим закінченням:
- **перший** (first)
- **другий** (second)
- **четвертий** (fourth)
- **п'ятий** (fifth)
- **десятий** (tenth)

Давайте подивимося, як змінюється числівник «п'ятий» у чоловічому роді (masculine singular). Він має такі ж закінчення, як прикметник:
- Називний (Nominative): **п'ятий поверх** (fifth floor)
- Родовий (Genitive): від **п'ятого поверху** (from the fifth floor)
- Давальний (Dative): по **п'ятому поверху** (along the fifth floor)
- Знахідний (Accusative): через **п'ятий поверх** (through the fifth floor)
- Орудний (Instrumental): перед **п'ятим поверхом** (in front of the fifth floor)
- Місцевий (Locative): на **п'ятому** / **п'ятім поверсі** (on the fifth floor)

Як бачите, це знайомі вам правила. Якщо ви знаєте закінчення прикметників, ви вже вмієте відмінювати ці числівники.

Існує також м'який тип відмінювання (soft declension pattern). Головний числівник у цій групі — це **третій** (third). Він має закінчення **-ій**, тому відмінюється як м'який прикметник, наприклад «синій» (blue).
Коли ми змінюємо слово «третій», ми використовуємо м'який знак, щоб зберегти правильний звук. Ось як це виглядає у чоловічому роді:
- Називний (Nominative): **третій поверх** (third floor)
- Родовий (Genitive): від **третього поверху** (from the third floor)
- Давальний (Dative): по **третьому поверху** (along the third floor)
- Знахідний (Accusative): через **третій поверх** (through the third floor)
- Орудний (Instrumental): перед **третім поверхом** (in front of the third floor)
- Місцевий (Locative): на **третьому** / **третім поверсі** (on the third floor)

Зауважте, що слово «перший» історично мало інші форми. Але сьогодні на рівні А2 ми вважаємо його звичайним твердим прикметником.

Порядкові числівники також постійно змінюють закінчення для жіночого та середнього роду. Вони повністю копіюють поведінку прикметників у реченні. Жіночий рід (feminine) зазвичай має закінчення **-а** або **-я**. Середній рід (neuter) має закінчення **-е** або **-є**. Усі слова у множині (plural) завжди мають закінчення **-і**.
Подивіться на ці дуже прості приклади узгодження:
- Чоловічий рід: **перший поверх** (1st floor), **другий урок** (2nd lesson).
- Жіночий рід: **перша зупинка** (1st stop), **друга вправа** (2nd exercise).
- Середній рід: **перше вікно** (1st window), **друге місто** (2nd city).
- Множина: **перші дні** (first days), **другі місця** (second places).

Пам'ятайте, що м'який числівник «третій» (third) у жіночому роді має форму **третя** (third, f.). А в середньому роді він має форму **третє** (third, n.). Множина буде **треті** (third, pl.).

Ми дуже часто використовуємо порядкові числівники для дат (dates). В українській мові є одне залізне правило. Коли ми називаємо число місяця, порядковий числівник завжди стоїть у Родовому відмінку (Genitive case). Слово «місяць» або його назва також стоїть у Родовому відмінку.
Чому так відбувається? Тому що ми скорочуємо фразу. Повна фраза звучить як «день двадцять першого числа березня» (the day of the twenty-first date of March).
Ось кілька дуже корисних прикладів:
- Коли твій день народження? **Двадцять першого березня** (March 21st).
- Ми зустрінемося **десятого квітня** (April 10th).
- Новий рік починається **першого січня** (January 1st).
- Свято буде **третього травня** (May 3rd).

Запам'ятайте закінчення **-ого** для всіх дат у чоловічому та середньому роді. Воно допоможе вам правильно планувати зустрічі.

<!-- INJECT_ACTIVITY: fill-in-ordinals -->


## Один/одна/одне у відмінках (One in All Cases)

Числівник **один** (one) — це дуже особливе і важливе слово. Він зовсім не працює так, як інші числа. Він дуже схожий на звичайний твердий прикметник. Тому він змінюється для всіх трьох родів (genders). Він також має різні форми для всіх семи відмінків (cases). В українській мові ми завжди узгоджуємо це слово з іменником (noun). Наприклад, для чоловічого роду ми кажемо **один великий будинок** (one big house). Для жіночого роду ми використовуємо форму **одна нова машина** (one new car). А для середнього роду нам потрібне слово **одне зелене дерево** (one green tree). Іноді ми навіть маємо форму множини (plural) — **одні люди** (some people). Це дуже логічна граматична система. Якщо ви вже знаєте прикметники, вам буде дуже легко.

Давайте спочатку подивимося на чоловічий та середній рід (masculine and neuter). Вони мають однакові форми майже у всіх непрямих відмінках. Вам треба запам'ятати кілька ключових слів. У Родовому відмінку (Genitive) це завжди буде **одного** (of one). У Давальному (Dative) ми кажемо **одному** (to one). Орудний відмінок (Instrumental) має форму **одним** (with one). Місцевий відмінок (Locative) — це **на одному** (on one) або коротко **на однім**. Знахідний відмінок (Accusative) для чоловічого роду залежить від істоти (animacy). Якщо предмет неживий (inanimate), форма не змінюється. Ми просто кажемо **бачу один стіл** (I see one table). Якщо це жива істота (animate), ми беремо форму Родового відмінка. Тоді ми кажемо **бачу одного хлопця** (I see one boy). Для середнього роду це завжди просто **одне**.

Тепер перейдемо до жіночого роду (feminine). Початкова форма тут — це **одна**. Вона також повністю змінює свої закінчення у реченні. Родовий відмінок має відразу дві правильні форми: **однієї** або коротше **одної** (of one). Давальний відмінок — це форма **одній** (to one). Знахідний відмінок дуже простий і логічний, ми використовуємо слово **одну** (one, acc.). Орудний відмінок також має два популярні варіанти: **однією** або **одною** (with one). Місцевий відмінок збігається з Давальним, тому ми кажемо **на одній** (on one). Ці форми постійно звучать у реальних розмовах. Наприклад, ми дуже часто використовуємо фразу **з однієї сторони** (from one side). Або ви можете сказати: «я зараз живу в одній кімнаті» (I am living in one room now).

Цікаво, що українське слово «один» не завжди означає просто математичне число. Це унікальне слово має багато інших корисних значень (meanings). Дуже часто воно означає «сам» (alone). Наприклад: «Сьогодні **я тут один**» (Today I am here alone), або «вона залишилася одна» (she stayed alone). Інколи ми використовуємо його, щоб сказати «якийсь» (a certain / some). Ви можете почути таку цікаву фразу: «**Один чоловік сказав** мені правду» (A certain man told me the truth). Також це слово часто може означати «той самий» (the same). Наприклад, ми кажемо: «**Ми з одного міста**» (We are from the same city). Або «вони щодня працюють в одному офісі» (They work in the same office every day). Ви будете чути ці фрази постійно.

<!-- INJECT_ACTIVITY: match-up-numeral-meanings -->


## Скільки чого? Числівник + іменник (How Many? Numeral + Noun Agreement)

Як ми рахуємо предмети в українській мові? Це дуже цікава граматична система. У нас є три головні групи чисел. Кожна група вимагає свій відмінок для іменника. Перша група — це число **один** (one). Вона працює з Називним відмінком однини (Nominative Singular). Друга група — це числа **два, три, чотири** (two, three, four). Після них ми використовуємо **Називний відмінок множини** (Nominative Plural). Це дуже важливе правило. Українська мова тут має власну давню логіку. Ми кажемо **два столи** (two tables) або **три крісла** (three armchairs). Ми ніколи не використовуємо Родовий відмінок однини (Genitive Singular) після цих чисел. Третя група — це числа від п'яти до двадцяти. Вони вимагають Родового відмінка множини (Genitive Plural). Якщо ви запам'ятаєте ці три правила, ви зможете правильно рахувати будь-які предмети.

Давайте подивимося на другу групу уважніше. Це числа два, три та чотири. Тут є один важливий нюанс для числа «два». Воно має дві форми. Для чоловічого та середнього роду ми кажемо **два** (two, m./n.). Наприклад: **два брати** (two brothers), **два вікна** (two windows). Для жіночого роду ми маємо спеціальну форму **дві** (two, f.). Ми кажемо **дві сестри** (two sisters) або **дві стіни** (two walls). Це дуже красива граматична особливість. А от числа **три** (three) та **чотири** (four) не змінюються. Вони однакові для всіх родів. Ми просто додаємо іменник у Називному відмінку множини: **три дні** (three days), **чотири машини** (four cars). Вам просто треба знати базову форму множини.

Тепер перейдемо до третьої великої групи. Це числа від п'яти до двадцяти. У цій групі правило завжди однакове. Ми повинні використовувати **Родовий відмінок множини** (Genitive Plural). Якщо ви бачите число **п'ять** (five), іменник змінює свою форму. Ми кажемо **п'ять студентів** (five students). Якщо ми маємо число **десять** (ten), ми кажемо **десять гривень** (ten hryvnias). Для числа **вісім** (eight) ми використовуємо фразу **вісім годин** (eight hours). Це правило працює стабільно і допомагає нам щодня. Зверніть увагу на спеціальні слова. Деякі іменники мають унікальні форми у множині. Наприклад, слово **людина** (person) перетворюється на **людей** (people). Ми кажемо **шість людей** (six people). Слово **дитина** (child) стає словом **дітей** (children). Ми кажемо **сім дітей** (seven children).

Що робити, коли ми маємо великі або складені числа? Наприклад, двадцять один або сорок п'ять? В українській мові діє правило останньої цифри. Тільки останнє слово у числі вирішує, який відмінок нам потрібен. Наприклад, число **двадцять один** (twenty-one) закінчується на «один». Тому ми використовуємо правило першої групи. Ми кажемо **двадцять один студент** (twenty-one students). Число **тридцять три** (thirty-three) закінчується на «три». Значить, це друга група. Ми кажемо **тридцять три студенти** (thirty-three students) у Називному відмінку множини. А число **сорок сім** (forty-seven) закінчується на «сім». Це вже третя група. Ми повинні сказати **сорок сім студентів** (forty-seven students). Це правило завжди працює для всіх великих чисел. Спробуйте самі побудувати кілька таких фраз усно.

Ми також часто використовуємо слова, які позначають кількість без точних цифр. Наприклад, ми часто питаємо **скільки?** (how many? / how much?). Або ми використовуємо такі корисні слова, як **багато** (many / much) та **мало** (few / little). Також ми часто кажемо **кілька** або **декілька** (several). Всі ці слова працюють як числа від п'яти до двадцяти. Вони завжди вимагають Родового відмінка множини для предметів, які ми можемо порахувати. Тому ми кажемо **багато запитань** (many questions). Ми можемо сказати **мало проблем** (few problems). Або ми скажемо **кілька днів** (several days) та **декілька друзів** (several friends). Коли ми йдемо на базар чи в магазин, ці слова стають нашими найкращими помічниками. Це дуже полегшує вивчення нових тем.

Нарешті, ми маємо поговорити про винятки та спеціальні слова. Найпопулярніші з них — це **пів** (half) та **півтора** (one and a half). Ці цікаві слова ніколи не відмінюються. Вони взагалі не змінюють свою форму. Але вони вимагають після себе **Родового відмінка однини** (Genitive Singular). Це дуже важливо запам'ятати. Наприклад, ми кажемо **півтора кілограма** (one and a half kilograms). Ми також кажемо **півтора місяця** (one and a half months). Для жіночого роду ми маємо спеціальну форму **півтори** (one and a half, f.). Ми дуже часто використовуємо її для часу. Наприклад, ми кажемо **півтори години** (one and a half hours). Це дуже типова українська фраза. Тепер ви знаєте всі секрети українських числівників.

<!-- INJECT_ACTIVITY: group-sort-agreement -->
<!-- INJECT_ACTIVITY: quiz-noun-selection -->


## Числа навколо нас (Numbers Around Us)

Подивіться, як числа працюють у реальному житті. Уявіть ситуацію на ринку. Вчитель та учні організовують спортивне свято і купують інвентар.
> — **Вчитель:** Добрий день! Скільки **коштують** *(cost)* ці **три м'ячі** *(three balls)*?
> — **Продавець:** Доброго дня! Вони коштують **п'ятсот гривень** *(five hundred hryvnias)*.
> — **Учень:** Це дуже дорого! А скільки коштує **один м'яч** *(one ball)*?
> — **Продавець:** Один м'яч коштує **двісті гривень** *(two hundred hryvnias)*. Якщо берете три, буде дешевше.
> — **Вчитель:** Добре. Дайте, будь ласка, **п'ять м'ячів** *(five balls)* і **два насоси** *(two pumps)*.
> — **Продавець:** З вас **тисяча двісті гривень** *(one thousand two hundred hryvnias)*.
> — **Вчитель:** Ось, тримайте. Дякую!

Зверніть увагу, як змінюється слово «м'яч». Ми кажемо «один м'яч» у Називному відмінку однини. Потім ми кажемо «три м'ячі» у Називному відмінку множини. Нарешті, ми кажемо «п'ять м'ячів» у Родовому відмінку множини. Слово «гривня» також змінюється: «двісті гривень», «п'ятсот гривень». Це правило узгодження в дії.

Числа також дуже важливі для адрес і телефонів. В Україні ми використовуємо спеціальну ієрархію для адреси. Спочатку ми називаємо **вулицю** *(street)*. Потім ми називаємо **будинок** *(building)*. Нарешті, ми називаємо **квартиру** *(apartment)*. Наприклад: «вулиця Хрещатик, будинок двадцять два, квартира п'ять». Іноді вулиці мають номери замість імен. У такому випадку ми використовуємо порядкові числівники. Наприклад: «**П'ята лінія**» *(Fifth Line)* або «**Перша вулиця**» *(First Street)*. Номери телефонів також легко читати. Ми зазвичай читаємо їх по одній цифрі або групами по дві.
> — **Максим:** Який твій номер телефону?
> — **Олена:** Мій номер — **нуль дев'яносто шість** *(zero ninety-six)*, **чотириста двадцять** *(four hundred twenty)*, **п'ятнадцять** *(fifteen)*, **вісімдесят один** *(eighty-one)*.

Для телефонів і адрес ми використовуємо звичайні кількісні числівники. Вам просто треба знати базові числа.

Як ми говоримо про **вік** *(age)* українською мовою? Ми використовуємо займенник у Давальному відмінку. Найпопулярніша фраза — «**мені ... років**» *(I am ... years old)*. Але слово **рік** *(year)* має спеціальний цикл узгодження. Якщо число закінчується на один, ми використовуємо форму однини: «Мені **двадцять один рік**» *(I am twenty-one years old)*. Якщо число закінчується на два, три або чотири, ми використовуємо форму множини: «Моєму брату **двадцять два роки**» *(My brother is twenty-two years old)*. Для чисел від п'яти до дев'яти, а також для нуля, ми використовуємо Родовий відмінок множини: «Моїй мамі **п'ятдесят п'ять років**» *(My mom is fifty-five years old)*. Ми також часто використовуємо числа для часу. Пам'ятайте, що для годин потрібні порядкові числівники у Місцевому відмінку. Ми кажемо «**о третій годині**» *(at three o'clock)* або «**о десятій ранку**» *(at ten in the morning)*.

Давайте попрактикуємо читання дат. Коли ми говоримо про дати, порядковий числівник має бути в Родовому відмінку. Прочитайте цей короткий текст про українські свята.
В Україні є багато важливих свят. Найголовніше свято — це День Незалежності. Ми святкуємо його **двадцять четвертого серпня** *(on the twenty-fourth of August)*. Ще одне важливе свято — це День Конституції. Воно відзначається **двадцять восьмого червня** *(on the twenty-eighth of June)*. Звісно, всі люди дуже люблять Новий рік. Ми святкуємо Новий рік **першого січня** *(on the first of January)*. Також ми маємо Різдво. Тепер Україна святкує Різдво **двадцять п'ятого грудня** *(on the twenty-fifth of December)*.

Зверніть увагу, що всі дати закінчуються на «-го»: першого, двадцять п'ятого. Це вказує на день, коли щось відбувається. Назва місяця також стоїть у Родовому відмінку: серпня, червня, січня, грудня. 

<!-- INJECT_ACTIVITY: fill-in-decline-ordinal-numerals-in-context-of-dates-and-addresses -->
<!-- INJECT_ACTIVITY: match-up-match-numeral-expressions-to-their-correct-form -->


## Підсумок

Сьогодні ми вивчили багато нових правил про **числівники** *(numerals)*. Пам'ятайте, що **порядкові числівники** *(ordinal numerals)* мають дві групи. Більшість закінчується на твердий звук: «**п'ятий**» *(fifth)*, «**десятий**» *(tenth)*. Але слово «**третій**» *(third)* має м'який звук. Тому ми кажемо «**третього**» *(of the third)*, а не «третого». Слово «**перший**» *(first)* має твердий звук і відмінюється стандартно.

Також ми вивчили дуже важливий **цикл узгодження** *(agreement cycle)*. Це правило «один-два-п'ять». Після числа один ми використовуємо Називний відмінок однини. Наприклад: «один брат». Після чисел два, три і чотири потрібен Називний відмінок множини: «два брати». А після чисел від п'яти до двадцяти ми використовуємо Родовий відмінок множини: «п'ять братів». Це базовий ритм української мови.

Тепер перевірте себе. Дайте відповіді на ці чотири питання:
1. Як сказати "May 5th" українською мовою?
2. Яка форма іменника стоїть після слова «три»?
3. Чим відрізняється слово «третій» від слова «перший»?
4. Як правильно перекласти фразу "from one city"?

Якщо ви знаєте відповіді, ви чудово засвоїли цю складну тему!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: numerals-and-cases
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

**Level: A2 (Module 55/60) — ELEMENTARY**

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

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
