<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/which-case-when.yaml` file for module **36: Компас відмінків** (a2).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Given a sentence with a blank, choose the correct case form based on the
    governing verb or preposition
  items: 8
  type: quiz
- focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., Loc.)
  items: 8
  type: group-sort
- focus: Complete sentences with the correct noun form — mixed cases triggered by
    different prepositions and verbs, including time expressions (у четвер), characteristics
    (у червоному светрі), and path (по кімнаті)
  items: 8
  type: fill-in
- focus: Judge whether the case used in a sentence is correct or incorrect, including
    tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- алгоритм (algorithm)
- контекст (context)
- керувати (to manage, drive)
- майбутнє (future)
required:
- відмінок (grammatical case)
- прийменник (preposition)
- дієслово (verb)
- напрямок (direction)
- місце (place, location)
- час (time)
- характеристика (characteristic, description)
- думати (to think)
- боятися (to be afraid)
- користуватися (to use)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслово вирішує: Який відмінок після дієслова?

Уявіть, що у вас є надійний граматичний компас *(grammatical compass)*. Цей компас допомагає швидко обрати правильний відмінок *(case)*. Відмінки в українській мові ніколи не бувають випадковими. У реченні майже завжди є головне слово, яке вимагає конкретного відмінка для інших слів. Це граматичне явище лінгвісти називають керування *(government)*. Найчастіше таким потужним тригером є саме дієслово *(verb)*. Наприклад, дієслово «бачити» *(to see)* завжди вимагає питання «кого? що?». Тому ми правильно кажемо «бачу нову книгу» *(I see a new book)*, а не просто «книга».

Найбільша група дієслів завжди вимагає Знахідного відмінка *(Accusative case)*. Це перехідні дієслова *(transitive verbs)*, які означають пряму дію, спрямовану на конкретний об'єкт. Ви вже дуже добре знаєте ці популярні дієслова: «любити» *(to love)*, «знати» *(to know)*, «читати» *(to read)*, «купити» *(to buy)*, «шукати» *(to look for)*. Після них ми завжди ставимо питання «кого? що?».
Жіночий рід *(feminine gender)* тут змінює закінчення «-а» на «-у», а «-я» на «-ю». Наприклад: «Я дуже люблю сучасну Україну» *(I love modern Ukraine very much)*. «Ми зараз читаємо цікаву статтю» *(We are reading an interesting article now)*.
Чоловічий рід *(masculine gender)* має два різні варіанти. Для неістот *(inanimate objects)* базова форма зовсім не змінюється. Наприклад: «Я читаю довгий текст» *(I am reading a long text)*. «Ми активно шукаємо старий парк» *(We are actively looking for an old park)*. Але для істот *(animate objects)* закінчення обов'язково змінюється на «-а» або «-я». Наприклад: «Я сьогодні бачу старшого брата» *(I see an older brother today)*. «Вона добре знає цього лікаря» *(She knows this doctor well)*.

Інша дуже важлива група дієслів вимагає використання Давального відмінка *(Dative case)*. Це дієслова, які зазвичай означають передачу інформації, допомогу або ставлення до конкретної людини. До цієї групи належать дієслова «допомагати» *(to help)*, «телефонувати» *(to call)*, «дякувати» *(to thank)*, «радити» *(to advise)*, «заважати» *(to disturb)*. Після них ми завжди ставимо питання «кому? чому?».
Зверніть особливу увагу на типові закінчення. Чоловічий рід найчастіше отримує довгі закінчення «-ові» або «-еві». Наприклад: «Я часто телефоную своєму найкращому другові» *(I often call my best friend)*. «Студент щиро дякує новому вчителю» *(A student sincerely thanks a new teacher)*. Жіночий рід зазвичай має просте закінчення «-і». Наприклад: «Він щодня допомагає молодшій сестрі» *(He helps a younger sister every day)*. «Ми завжди дякуємо нашій мамі» *(We always thank our mom)*. Пам'ятайте, що в українській мові ми дякуємо комусь, а не когось. Тому ми завжди кажемо «дякую вам» *(thank you)*, а не «дякую вас».

Деякі цікаві дієслова обов'язково вимагають Орудного відмінка *(Instrumental case)*. Зазвичай це дієслова, які означають ваш інтерес, використання якогось інструмента або професійне управління. Це дуже популярні дієслова: «цікавитися» *(to be interested in)*, «користуватися» *(to use)*, «займатися» *(to be engaged in)*, «керувати» *(to manage/drive)*. Після них ми завжди ставимо питання «ким? чим?».
Наприклад, якщо ви використовуєте певний предмет як інструмент, ви кажете: «Він користується новим дорогим комп'ютером» *(He uses a new expensive computer)*. Якщо ви маєте серйозне хобі або інтерес, ви скажете: «Вона глибоко цікавиться українською історією» *(She is deeply interested in Ukrainian history)* або «Мій старший брат професійно займається спортом» *(My older brother professionally does sports)*. Якщо людина має високу керівну посаду, ми кажемо: «Директор успішно керує великою компанією» *(A director successfully manages a large company)*.

Родовий відмінок *(Genitive case)* також має свої особливі дієслова-тригери. Найчастіший і найважливіший тригер — це слово «немає» *(there is no)*. Після слова «немає» завжди стоїть Родовий відмінок і питання «кого? чого?». Наприклад: «На жаль, у мене зараз немає вільного часу» *(Unfortunately, I have no free time now)*. «У нас поки що немає великих грошей» *(We do not have big money yet)*.
Також Родовий відмінок потрібен після дієслів страху та сильної потреби. Це дієслова «боятися» *(to be afraid of)* та «потребувати» *(to need/require)*. Наприклад: «Маленька дитина дуже боїться великого сусідського собаки» *(A small child is very afraid of a big neighborhood dog)*. «Цей складний проєкт негайно потребує нашої професійної допомоги» *(This complex project urgently requires our professional help)*.

> — **Вчитель:** Добрий день, друзі! *(Good day, friends!)*
> — **Олена:** Добрий день! *(Good day!)*
> — **Вчитель:** Давайте сьогодні пограємо в справжніх граматичних детективів. *(Let's play true grammar detectives today.)* Я зараз читаю свіжу газету: «Президент зустрівся з новим прем'єром». *(I am reading a fresh newspaper now: "The president met with the new premier".)* Який відмінок ми тут бачимо і чому? *(What case do we see here and why?)*
> — **Олена:** Слово «прем'єром» — це Орудний відмінок. *(The word "premier" is Instrumental case.)* Головний тригер тут — це дієслово «зустрітися з». *(The main trigger here is the verb "to meet with".)*
> — **Вчитель:** Чудово! *(Excellent!)* Ви дуже уважний детектив! *(You are a very attentive detective!)*

<!-- INJECT_ACTIVITY: quiz, Choose the correct case form based on the governing verb, 8 items -->


## Прийменник вирішує: Один прийменник — різні відмінки

Часто один прийменник може вимагати різних відмінків. Найвідоміший приклад — це прийменники «в/у» та «на». Вони працюють як перемикачі між напрямком та місцем. In English, you use "to" or "into" for direction and "in/at" for location. In Ukrainian, we use the same preposition, but we change the case. Якщо ми говоримо про напрямок, ми ставимо питання «куди?». У цьому випадку ми використовуємо Знахідний відмінок *(Accusative case)*. Наприклад: «Я йду на пошту» *(I am going to the post office)*. «Він швидко поклав телефон у чорну сумку» *(He quickly put a phone into a black bag)*. Це активна дія, яка має конкретну ціль. Але якщо ми говоримо про постійне місце, ми ставимо питання «де?». Тоді ми обов'язково використовуємо Місцевий відмінок *(Locative case)*. Порівняйте ситуацію: «Я зараз працюю на пошті» *(I am working at the post office now)*. «Його новий телефон лежить у чорній сумці» *(His new phone is lying in a black bag)*. Це статична позиція, де немає жодного руху. Запам'ятайте дуже просте і важливе правило: активний рух — це Знахідний відмінок, а статика — це Місцевий відмінок.

Ще один дуже цікавий прийменник — це «з». Цей короткий прийменник також має дві абсолютно різні функції. Перша функція — це рух із якогось місця назовні. У цьому значенні прийменник «з» завжди вимагає Родового відмінка *(Genitive case)*. Наприклад: «Моя сестра щойно приїхала з Одеси» *(My sister just arrived from Odesa)*. «Студент швидко вийшов з аудиторії» *(A student went quickly out of the classroom)*. Друга функція — це спільна дія. Тут прийменник «з» вимагає Орудного відмінка *(Instrumental case)*. Наприклад: «Він пішов у кіно з найкращим другом» *(He went to the cinema with a best friend)*. «Я щоранку люблю пити каву з теплим молоком» *(I like to drink coffee with warm milk every morning)*. Для кращого звучання ми часто використовуємо варіант «із» замість «з». Наприклад: «смачний хліб із маслом» *(tasty bread with butter)* або «довгий лист із Києва» *(a long letter from Kyiv)*.

Прийменник «за» також ефективно працює з двома відмінками: Знахідним та Орудним. Ми використовуємо Знахідний відмінок, коли говоримо про обмін, ціну або причину. Наприклад: «Я хочу сам заплатити за каву» *(I want to pay for a coffee myself)*. Дуже популярна фраза «дякую за» також завжди вимагає Знахідного відмінка. Ми часто кажемо: «Дякую вам за швидку допомогу» *(Thank you for the quick help)*. «Дякую за вашу чудову роботу» *(Thank you for your excellent work)*. Але якщо ми говоримо про фізичне місце позаду чогось, ми використовуємо Орудний відмінок. Наприклад: «Моя велика родина сидить за святковим столом» *(My large family is sitting at a festive table)*. «Маленький собака весело біжить за старим автобусом» *(A small dog is happily running after an old bus)*. Це завжди позиція позаду іншого об'єкта.

Окремо треба сказати про важливий прийменник «по». Він дуже часто використовується з Місцевим відмінком. Це означає рух по поверхні або всередині великого простору. In English, you might use "around", "along", or "across" for this concept. Наприклад, якщо ви гуляєте без конкретної цілі у центрі, ви скажете: «Я люблю гуляти по старому місту» *(I like to walk around an old city)*. Якщо спортсмен активно тренується, він каже: «Я щодня бігаю по великому стадіону» *(I run around a big stadium every day)*. Туристи часто кажуть таку фразу своїм друзям: «Ми дуже хочемо подорожувати по цілому світу» *(We really want to travel around the whole world)*. Прийменник «по» показує, що ваша дія вільно охоплює весь цей простір, а не лише одну пряму лінію.

<!-- INJECT_ACTIVITY: group-sort, Sort prepositions by which case(s) they govern (Acc., Gen., Instr., Loc.), 8 items -->


## Особливі випадки: Час, характеристика, шлях

Час — це дуже важливий елемент у нашій мові. Для днів тижня ми завжди використовуємо **Знахідний відмінок** *(Accusative case)* з прийменниками «у» або «в». Наприклад, ми кажемо: «Я працюю у середу» *(I work on Wednesday)* або «Ми відпочиваємо у п'ятницю» *(We rest on Friday)*. Зверніть увагу, що для днів тижня ми не використовуємо **Місцевий відмінок** *(Locative case)*. When you want to say "next" or "last" regarding a specific time period, you must use the Genitive case without any prepositions. Це дуже важливе правило. Ми кажемо: «**наступного тижня**» *(next week)*, «**минулого місяця**» *(last month)*, «**наступного року**» *(next year)*. Це **виняток** *(exception)*, який треба добре запам'ятати. If you talk about a specific year, you use the Locative case. Наприклад: «Я народився у дві тисячі першому році» *(I was born in two thousand and one)*. «Мій старший брат закінчив університет у минулому році» *(My older brother finished university last year)*. Отже, дні тижня — це Знахідний відмінок, а конкретні роки — Місцевий відмінок. Фрази зі словами «наступний» та «минулий» — це **Родовий відмінок** *(Genitive case)*.

Тепер поговоримо про те, як ми описуємо людей та їхній одяг. Коли ми хочемо сказати, що людина носить певний одяг, ми використовуємо Місцевий відмінок з прийменником «у» або «в». This is a very common pattern for physical descriptions. Ми кажемо: «Ця красива жінка **у синій сукні** *(in a blue dress)* — моя старша сестра». «Той чоловік **у капелюсі** *(in a hat)* — мій новий сусід». «Маленький хлопець **у червоному светрі** *(in a red sweater)* дуже швидко біжить по вулиці». This pattern specifically describes the clothing that a person is wearing. Do not confuse this with describing where an object is located. Якщо ви кажете «на жінці» *(on the woman)*, це означає фізичну локацію на її тілі. Наприклад: «На жінці сидить маленький зелений жук» *(A small green bug is sitting on the woman)*. Але якщо ми описуємо стиль людини, ми завжди говоримо «у сукні», «**в окулярах**» *(in glasses)*, «**у пальті**» *(in a coat)*.

Місцевий відмінок також чудово працює, коли ми говоримо про абстрактний час. Sometimes we treat periods of life or states of being as if they are physical places. Ми кажемо: «**У дитинстві** *(In childhood)* я дуже любив грати на великій вулиці». «**У майбутньому** *(In the future)* я хочу стати хорошим лікарем». Це абстрактний простір, де відбувається дія. Також ми використовуємо Місцевий відмінок для опису абстрактного стану. Наприклад: «Моя мама зараз **у відпустці** *(on vacation)*». Ми також можемо сказати: «Вона зараз **у декреті**» *(She is on maternity leave right now)*. «Його батько довго був у дуже тривалому відрядженні» *(His father was on a very long business trip for a long time)*. Це означає, що людина перебуває у певному тривалому процесі.

Ми вже говорили про прийменник «по» і Місцевий відмінок. Але давайте розглянемо це важливе правило детальніше. Ця комбінація часто показує активний рух, який охоплює велику поверхню. This is the extended movement pattern. Ми використовуємо його зі специфічними дієсловами руху. Наприклад: «Маленький човен повільно **пливе по річці** *(is swimming along the river)*». «Великі білі птахи красиво **літають по небу** *(are flying across the sky)*». «Ми любимо влітку їздити по українських селах» *(We like to drive through Ukrainian villages in summer)*. This construction highlights the medium or the surface where the movement happens. Коли ми їдемо по дорозі, ми використовуємо весь простір цієї дороги *(When we drive on the road, we use the entire space of this road)*. Ви не просто йдете вперед, ви активно взаємодієте з усім простором. Тому ми часто кажемо: «Діти весело **бігають по кімнаті** *(are running around the room)*». «Ми довго гуляли по великому зимовому лісу» *(We walked around the large winter forest for a long time)*. Це показує велику свободу просторового руху.

<!-- INJECT_ACTIVITY: fill-in, Focus: Complete sentences with correct noun forms (mixed cases: time, clothing, path), 8 items -->


## Алгоритм вибору відмінка

Як швидко обрати правильний відмінок у реченні? Це дуже простий і логічний процес. The decision process for finding the correct case follows a strict order of priority. Ми використовуємо простий **алгоритм** *(algorithm)*, який має три кроки.

Крок перший: шукаємо прийменник. Prepositions always have the highest priority and completely overrule the verb. Якщо ви бачите прийменник, ви повинні обрати відмінок, який він вимагає. Наприклад, після слова «без» завжди йде Родовий відмінок. «Я п'ю каву без цукру».

Крок другий: якщо прийменника немає, ми дивимося на дієслово. Each specific verb commands a specific case for its direct or indirect object. Якщо ви бачите дієслово «допомагати», ви автоматично використовуєте Давальний відмінок. «Син допомагає мамі».

Крок третій: якщо ви досі не знаєте правильний відмінок, поставте граматичне питання. Ask the grammatical question to the noun to reveal its role in the sentence. Питання «Кого?» або «Що?» — це Знахідний відмінок. Питання «Кому?» або «Чому?» — це Давальний відмінок. Питання «Ким?» або «Чим?» — це Орудний відмінок.

| Крок | Дія | Результат |
|---|---|---|
| 1 | Є прийменник? | Прийменник обирає відмінок. |
| 2 | Немає прийменника? | Дієслово обирає відмінок. |
| 3 | Сумніваєтеся? | Поставте граматичне питання. |

Студенти часто роблять однакові граматичні помилки, коли вивчають відмінки. English speakers often map English prepositions directly to Ukrainian cases, which causes problems. Запам'ятайте, що англійська фраза «think about» українською звучить як «**думати про**» *(to think about)*. Після цього прийменника ми завжди використовуємо Знахідний відмінок, а не Місцевий. Ми кажемо: «Я часто думаю про тебе», а не «Я думаю про тобі».

Друга велика проблема — це дієслово «допомагати». English speakers want to use a direct object here because of the English translation. Але українське дієслово «допомагати» завжди вимагає Давального відмінка. Ми кажемо «Я допомагаю своєму брату», а не «Я допомагаю свого брата».

Також будьте обережні з прийменниками простору. Remember the difference between dynamic direction and static location. Коли ви активно йдете кудись, ви кажете: «Я йду в магазин». Це **напрямок** *(direction)* і Знахідний відмінок. Але коли ви вже там, ви кажете: «Я в магазині». Це статичне **місце** *(location)* і Місцевий відмінок.

Студенти читають новий український текст на уроці граматики.
> — **Марк:** Ірино, я не розумію одне речення. *(Iryna, I do not understand one sentence.)*
> — **Ірина:** Яке речення ти не розумієш, Марку? *(Which sentence do you not understand, Mark?)*
> — **Марк:** Чому тут написано «у понеділок»? *(Why is it written "on Monday" here?)*
> — **Ірина:** Це Знахідний відмінок, він показує час. *(This is the Accusative case, it shows time.)*
> — **Марк:** Але прийменник «у» — це Місцевий відмінок. *(But the preposition "у" is the Locative case.)*
> — **Ірина:** Ні, дні тижня ми завжди пишемо у Знахідному відмінку. *(No, we always write days of the week in the Accusative case.)*
> — **Марк:** Дякую, я тепер усе зрозумів. *(Thank you, I understood everything now.)*
> — **Ірина:** А ти пам'ятаєш фразу «цікавитися музикою»? *(And do you remember the phrase "to be interested in music"?)*
> — **Марк:** Так, дієслово «цікавитися» завжди вимагає Орудного відмінка. *(Yes, the verb "to be interested" always requires the Instrumental case.)*
> — **Ірина:** Правильно, ти дуже добре знаєш граматику. *(Correct, you know grammar very well.)*

<!-- INJECT_ACTIVITY: true-false, Focus: Judge whether the case used in a sentence is correct (includes tricky Acc/Loc pairs), 8 items -->


## Підсумок

Кожен український іменник має свого «боса» — це дієслово або прийменник. Every Ukrainian noun depends on a "boss" — either a verb or a preposition. Саме вони завжди вирішують, який відмінок ви повинні використовувати. Якщо ви бачите прийменник, він головний. The preposition always dictates the case. Наприклад, після прийменника «без» завжди стоїть Родовий відмінок. Якщо прийменника немає, ви дивитеся на дієслово. The verb determines the case of its object. Наприклад, дієслово «бачити» вимагає Знахідного відмінка, а дієслово «допомагати» — Давального відмінка. Якщо ви сумніваєтеся, просто поставте граматичне питання. The correct question will reveal the necessary case.

Перевірте себе та дайте відповіді на ці запитання:
1. Який відмінок ми вживаємо після дієслова «дякувати»? (Відповідь: Давальний відмінок).
2. Коли ми використовуємо прийменник «на» плюс Знахідний відмінок? (Відповідь: Коли це напрямок, і ми відповідаємо на питання «куди?»).
3. Як правильно сказати: «у понеділок» чи «в понеділку»? (Відповідь: «У понеділок» — це Знахідний відмінок для днів тижня).
4. Який відмінок ми використовуємо, коли описуємо одяг людини? (Відповідь: Місцевий відмінок із прийменником «у/в»).

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: which-case-when
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 36/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
