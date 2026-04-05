<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-adjectives-pronouns.yaml` file for module **13: Мого друга, цієї книги** (a2).

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

- `<!-- INJECT_ACTIVITY: genitive-adjectives-fill -->`
- `<!-- INJECT_ACTIVITY: possessive-pronouns-quiz -->`
- `<!-- INJECT_ACTIVITY: genitive-phrases-match -->`
- `<!-- INJECT_ACTIVITY: demonstrative-adjective-noun-fill -->`
- `<!-- INJECT_ACTIVITY: genitive-phrases-correction -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the adjective and noun into the correct Genitive form
  items: 8
  type: fill-in
- focus: Choose the correct possessive pronoun form (мого vs. моєї etc.)
  items: 8
  type: quiz
- focus: Match Nominative noun phrases to their Genitive equivalents
  items: 8
  type: match-up
- focus: Build complete Genitive phrases with demonstrative + adjective + noun
  items: 8
  type: fill-in
- focus: Find and fix adjective-noun agreement errors in Genitive phrases (e.g., *нової
    друга → нового друга, *цієї будинку → цього будинку)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- молодий (young)
- старший (older, elder)
- дівчина (girl, young woman)
- олівець (pencil)
required:
- прикметник (adjective)
- займенник (pronoun)
- присвійний (possessive)
- вказівний (demonstrative)
- узгодження (agreement (grammatical))
- дозвіл (permission)
- підручник (textbook)
- документ (document)
- вчителька (female teacher)
- важливий (important)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Який? Якого? Прикметники в родовому (Which? Whose? Adjectives in the Genitive)

> — **Власник:** Добрий день! Я шукаю свого нового телефона. *(Good day! I am looking for my new phone.)*
> — **Працівник:** Якого телефона? У нас сьогодні дуже багато знайдених телефонів. *(Which phone? We have a lot of found phones today.)*
> — **Власник:** Великого чорного телефона. *(A big black phone.)*
> — **Працівник:** Зрозуміло. А я шукаю власника цієї червоної парасольки. Це не ваша? *(Understood. And I am looking for the owner of this red umbrella. Is it not yours?)*
> — **Власник:** Ні, у мене взагалі немає червоної парасольки. *(No, I don't have a red umbrella at all.)*

When an adjective modifies a noun in the Genitive case, the adjective must also take a Genitive ending. This strict matching process is called **узгодження** (agreement).

Читаємо українською:
**Який** телефон? *(Which phone? — Nominative)*
**Якого** телефона? *(Which phone? — Genitive)*
**Яка** сумка? *(Which bag? — Nominative)*
**Якої** сумки? *(Which bag? — Genitive)*

Masculine and neuter adjectives ending in a hard consonant take the **-ого** ending. Drop the final letter(s) of the dictionary form and add the new ending.

:::note Закінчення -ого (Ending -ого)
*   **новий** → нового *(new)*
*   **старий** → старого *(old)*
*   **велике** → великого *(big)*
*   **молодий** → молодого *(young)*
:::

Читаємо українською:
У мене немає нового підручника. *(I do not have a new textbook.)*
Ми живемо біля старого міського парку. *(We live near the old city park.)*
Він довго шукає великого чорного кота. *(He is looking for a big black cat for a long time.)*
Це зошит нашого молодого вчителя. *(This is the notebook of our young teacher.)*
Тут поблизу немає чистого озера. *(There is no clean lake nearby here.)*

Masculine and neuter adjectives with soft stems take the **-ього** ending. The soft sign (`ь`) preserves the softness of the stem consonant.

:::note Закінчення -ього (Ending -ього)
*   **синій** → синього *(blue)*
*   **літній** → літнього *(summer)*
*   **вчорашнє** → вчорашнього *(yesterday's)*
*   **вечірній** → вечірнього *(evening)*
:::

Читаємо українською:
Я сьогодні не маю синього олівця. *(I don't have a blue pencil today.)*
Ми всі чекаємо літнього теплого сонця. *(We are all waiting for the warm summer sun.)*
Вона зовсім не пам'ятає вчорашнього дня. *(She doesn't remember yesterday at all.)*
Біля синього моря завжди дуже гарно. *(It is always very beautiful near the blue sea.)*
У нас на жаль немає вечірнього квитка. *(Unfortunately, we do not have an evening ticket.)*

Feminine adjectives with a hard stem take the **-ої** ending.

:::note Закінчення -ої (Ending -ої)
*   **нова** → нової *(new)*
*   **велика** → великої *(big)*
*   **гарна** → гарної *(beautiful)*
*   **молода** → молодої *(young)*
:::

Читаємо українською:
У мене зараз немає нової цікавої книги. *(I do not have a new interesting book right now.)*
Вони довго стоять біля великої школи. *(They are standing near the big school for a long time.)*
Це старе фото дуже гарної дівчини. *(This is an old photo of a very beautiful girl.)*
Я ніколи не бачив цієї молодої жінки. *(I have never seen this young woman.)*
Ми швидко вийшли з нової машини. *(We quickly got out of the new car.)*

> — **Олег:** У тебе є синя ручка? *(Do you have a blue pen?)*
> — **Марія:** У мене немає нової ручки, тільки стара. *(I don't have a new pen, only an old one.)*
> — **Олег:** Добре, дай мені стару. А ти не бачив великої лінійки? *(Good, give me the old one. And haven't you seen a big ruler?)*
> — **Марія:** Ні, я ніде не бачила великої лінійки. *(No, I haven't seen a big ruler anywhere.)*

Feminine adjectives with a soft stem take the **-ьої** ending, using the soft sign to maintain correct pronunciation.

:::note Закінчення -ьої (Ending -ьої)
*   **синя** → синьої *(blue)*
*   **вечірня** → вечірньої *(evening)*
*   **літня** → літньої *(summer)*
*   **рання** → ранньої *(early)*
:::

Читаємо українською:
Вона прийшла на свято без синьої сукні. *(She arrived at the holiday without the blue dress.)*
Ми вчора чекали гостей до пізньої ночі. *(We waited for guests until late at night yesterday.)*
Тут на ринку ще немає ранньої полуниці. *(There is no early strawberry here at the market yet.)*
Я купив дорогий квиток для вечірньої вистави. *(I bought an expensive ticket for the evening performance.)*
Він ніколи не любить сильної літньої спеки. *(He never likes strong summer heat.)*

Both the adjective and the noun must be in the Genitive case when following prepositions that require it (such as **без**, **біля**, **до**).

Читаємо українською:
Мій молодший брат прийшов додому без великого олівця. *(My younger brother came home without a big pencil.)*
Іноземні туристи стоять біля старої дерев'яної церкви. *(Foreign tourists are standing near the old wooden church.)*
Ми довго їхали автомобілем до синього моря. *(We were driving by car to the blue sea for a long time.)*
Без доброго старого друга буває дуже сумно. *(Without a good old friend, it can be very sad.)*
Малі діти зараз граються біля високого дерева. *(Small children are playing near the tall tree now.)*
Вона успішно доїхала до нової станції метро. *(She successfully reached the new metro station.)*
Студент не може добре вчитися без розумної книги. *(The student cannot study well without a smart book.)*
Наш собака спокійно спить біля теплого каміна. *(Our dog is sleeping calmly near the warm fireplace.)*

> — **Анна:** Ти зараз йдеш до нового великого магазину? *(Are you going to the new big store now?)*
> — **Віктор:** Ні, я йду до старої аптеки. *(No, I am going to the old pharmacy.)*
> — **Анна:** Купи мені мінеральної води, будь ласка. Я не можу жити без чистої води. *(Buy me mineral water, please. I cannot live without clean water.)*
> — **Віктор:** Добре. Я буду біля великого міського парку через годину. *(Okay. I will be near the big city park in an hour.)*

<!-- INJECT_ACTIVITY: genitive-adjectives-fill -->

## Мого, твого, нашого: присвійні займенники (Мого, твого, нашого: Possessive Pronouns)

> — **Павло:** Де зараз собака мого брата? *(Where is my brother's dog now?)*
> — **Олена:** Він бігає біля твого паркану. *(It is running near your fence.)*

Possessive pronouns change their form in the Genitive case. For masculine and neuter nouns, singular possessive pronouns use endings similar to adjectives: **мій** *(my)* becomes **мого**, and **твій** *(your - singular/informal)* becomes **твого**. Plural forms are **наш** *(our)* → **нашого**, and **ваш** *(your - plural/formal)* → **вашого**.

:::note Називний → Родовий (Nominative → Genitive)
* **мій брат** → немає **мого брата** *(my brother → there is no my brother)*
* **твій лист** → без **твого листа** *(your letter → without your letter)*
* **наш дім** → біля **нашого дому** *(our house → near our house)*
* **ваш офіс** → навпроти **вашого офісу** *(your office → opposite your office)*
:::

Читаємо українською:
Це дуже гарне фото з мого нового офісу. *(This is a very beautiful photo from my new office.)*
Ми не можемо працювати без твого комп'ютера. *(We cannot work without your computer.)*
Туристи стоять біля нашого великого готелю. *(The tourists are standing near our big hotel.)*
Я ніколи не бачив вашого старшого брата. *(I have never seen your older brother.)*

For feminine nouns in the Genitive case, the pronouns **моя** *(my)* and **твоя** *(your)* change to **моєї** and **твоєї**. The pronouns **наша** *(our)* and **ваша** *(your)* change to **нашої** and **вашої**.

:::tip Жіночий рід (Feminine gender)
* **моя мама** → для **моєї мами** *(my mom → for my mom)*
* **твоя сестра** → від **твоєї сестри** *(your sister → from your sister)*
* **наша вчителька** → без **нашої вчительки** *(our teacher → without our teacher)*
* **ваша подруга** → біля **вашої подруги** *(your friend → near your friend)*
:::

Читаємо українською:
Це дуже гарний подарунок для моєї мами. *(This is a very beautiful gift for my mom.)*
Вона прийшла до школи без твоєї книги. *(She came to school without your book.)*
Малі діти чекають біля нашої нової машини. *(The small children are waiting near our new car.)*
Ми отримали довгого листа від вашої вчительки. *(We received a long letter from your teacher.)*
Ми не можемо увійти туди без вашого дозволу. *(We cannot enter there without your permission.)*

> — **Катерина:** Ти взяв зошит твоєї сестри? *(Did you take your sister's notebook?)*
> — **Антон:** Ні, я взяв ручку моєї вчительки. *(No, I took my teacher's pen.)*

Third-person possessive pronouns **його** *(his/its)* and **її** *(her)* are completely static. They do not change their endings to match the case, gender, or number of the noun they describe.

:::note Незмінні займенники (Unchanging pronouns)
* **його брат** → від **його брата** *(his brother → from his brother)*
* **її сестра** → біля **її сестри** *(her sister → near her sister)*
* **його місто** → до **його міста** *(his city → to his city)*
:::

Читаємо українською:
Я йду додому від його старшого брата. *(I am going home from his older brother.)*
Кіт спокійно спить біля її маленької сестри. *(The cat is sleeping calmly near her little sister.)*
Ми довго їхали до його рідного міста. *(We drove to his hometown for a long time.)*
Сьогодні в магазині немає її улюбленої піци. *(There is no her favorite pizza in the store today.)*

> — **Олег:** Ти знаєш його нового друга? *(Do you know his new friend?)*
> — **Ірина:** Ні, я ніколи не бачила його друга. *(No, I have never seen his friend.)*
> — **Олег:** А де ключі від її квартири? *(And where are the keys from her apartment?)*
> — **Ірина:** Вони лежать біля її сумки. *(They are lying near her bag.)*

The word **їхній** *(their)* acts like a soft-stem adjective. It declines and agrees fully with the noun. For masculine and neuter nouns, it becomes **їхнього**. For feminine nouns, it becomes **їхньої**. 

:::tip Займенник «їхній» (The pronoun «їхній»)
* **їхній син** *(m)* → немає **їхнього сина** *(their son → there is no their son)*
* **їхня школа** *(f)* → до **їхньої школи** *(their school → to their school)*
* **їхнє село** *(n)* → з **їхнього села** *(their village → from their village)*
:::

Читаємо українською:
Я ще не бачив їхнього нового будинку. *(I have not seen their new house yet.)*
Моя сестра працює біля їхньої школи. *(My sister works near their school.)*
Тут більше немає їхнього старого автомобіля. *(Their old car is no longer here.)*
Ми довго стояли біля їхньої нової роботи. *(We stood near their new job for a long time.)*

Combine possessive pronouns with common prepositions that require the Genitive case: **з** *(from)*, **для** *(for)*, **без** *(without)*, **від** *(from a person)*, and **біля** *(near)*. Every modifier and noun in the phrase must take the Genitive form.

Читаємо українською:
Новий студент приїхав з мого рідного міста. *(The new student arrived from my hometown.)*
Це дуже гарні квіти для твоєї сестри. *(These are very beautiful flowers for your sister.)*
Цей важливий документ прийшов від нашого брата. *(This important document came from our brother.)*
Маленька дитина грається біля їхнього великого будинку. *(A small child is playing near their big house.)*
Я буду працювати тут і без її дозволу. *(I will work here even without her permission.)*

> — **Марія:** Звідки приїхав цей молодий турист? *(Where did this young tourist come from?)*
> — **Олександр:** Він приїхав з мого міста. *(He came from my city.)*
> — **Марія:** Це подарунок для твоєї мами? *(Is this a gift for your mom?)*
> — **Олександр:** Так, це новий телефон для моєї мами. *(Yes, this is a new phone for my mom.)*
> — **Марія:** Ми можемо увійти без вашого дозволу? *(Can we enter without your permission?)*
> — **Олександр:** Ні, ви не можете увійти без мого дозволу. *(No, you cannot enter without my permission.)*

<!-- INJECT_ACTIVITY: possessive-pronouns-quiz -->
<!-- INJECT_ACTIVITY: genitive-phrases-match -->

## Цього, того: вказівні займенники та повні фрази (Цього, того: Demonstratives and Full Phrases)

> — **Віктор:** Що ти знаєш про того чоловіка? *(What do you know about that man?)*
> — **Марія:** Я нічого не знаю про того чоловіка, але я знаю цього хлопця. *(I know nothing about that man, but I know this guy.)*
> — **Віктор:** Ти взяла ключі від цього автомобіля? *(Did you take the keys from this car?)*
> — **Марія:** Ні, я взяла ключі від того старого будинку. *(No, I took the keys from that old house.)*

Demonstrative pronouns change their form in the Genitive case. For masculine and neuter nouns, **цей** *(this)* becomes **цього** *(of this)*, and **той** *(that)* becomes **того** *(of that)*. 

Читаємо українською:
Я нічого не їв після цього дня. *(I have eaten nothing since this day.)*
Ми чекали біля того будинку. *(We waited near that house.)*
Що ти хочеш від того чоловіка? *(What do you want from that man?)*
У цього студента немає словника. *(This student does not have a dictionary.)*
Я не бачу того великого озера. *(I do not see that big lake.)*

For feminine nouns, **ця** *(this)* becomes **цієї** *(of this)*. **Та** *(that)* becomes **тієї** *(of that)*. 

Читаємо українською:
Він отримав листа від цієї дівчини. *(He received a letter from this girl.)*
Навпроти тієї школи є великий парк. *(There is a big park opposite that school.)*
Я не можу працювати без цієї книги. *(I cannot work without this book.)*
Ми довго стояли біля тієї старої церкви. *(We stood near that old church for a long time.)*
У цієї молодої жінки є двоє дітей. *(This young woman has two children.)*

> — **Анна:** Ти знаєш цю нову студентку? *(Do you know this new student?)*
> — **Богдан:** Так, я отримав зошит від цієї студентки. *(Yes, I received a notebook from this student.)*
> — **Анна:** А хто живе біля тієї річки? *(And who lives near that river?)*
> — **Богдан:** Там живе мій брат. *(My brother lives there.)*

When combining multiple descriptive words, the standard word order is: Demonstrative Pronoun + Possessive Pronoun + Adjective + Noun. Every single word in the chain must obey **узгодження** (agreement) in gender, number, and case.

:::tip Порядок слів (Word order)
Вказівний + Присвійний + Прикметник + Іменник
*(Demonstrative + Possessive + Adjective + Noun)*
**Біля цього мого нового будинку.** *(Near this my new house.)*
**Для тієї вашої старої проблеми.** *(For that your old problem.)*
:::

Читаємо українською:
Я приїхав з того мого рідного міста. *(I arrived from that hometown of mine.)*
Ми працюємо без цього вашого нового плану. *(We are working without this new plan of yours.)*
Вона не хоче жити біля тієї нашої гучної вулиці. *(She does not want to live near that loud street of ours.)*
У цього твого старшого брата є машина? *(Does this older brother of yours have a car?)*
Це подарунок для тієї моєї найкращої подруги. *(This is a gift for that best friend of mine.)*

> — **Олена:** Чий це телефон лежить на столі? *(Whose phone is this lying on the table?)*
> — **Дмитро:** Це телефон того нашого нового менеджера. *(This is the phone of that new manager of ours.)*
> — **Олена:** А ці важливі документи? *(And these important documents?)*
> — **Дмитро:** Вони для цієї моєї важливої зустрічі. *(They are for this important meeting of mine.)*

Always verify the gender of the core noun. You cannot say *«від нової друга»* because **друг** *(friend)* is masculine, so it requires the masculine adjective ending (від нового друга). Soft-stem adjectives require a soft sign before the Genitive ending. You cannot write *«синого моря»* — the correct form is **синього моря** *(of the blue sea)*.

Читаємо українською:
Він не має чорного олівця. *(He does not have a black pencil.)*
У нас немає синього паперу. *(We do not have blue paper.)*
Вона прийшла без мого доброго друга. *(She came without my good friend.)*
Я не бачив цієї вчорашньої газети. *(I did not see this yesterday's newspaper.)*
Ми не можемо працювати без ранкового чаю. *(We cannot work without morning tea.)*
Вони живуть біля того великого літнього саду. *(They live near that big summer garden.)*

Build phrases step by step. Start with the Nominative noun, put it into the Genitive case, and then add modifiers one by one.

:::note Крок за кроком (Step by step)
1. **автомобіль** *(masculine noun)*
2. немає **автомобіля** *(Genitive case)*
3. старого **автомобіля** *(add Genitive adjective)*
4. мого старого **автомобіля** *(add Genitive possessive)*
5. цього мого старого **автомобіля** *(add Genitive demonstrative)*
6. біля цього мого старого **автомобіля** *(add preposition)*
:::

Читаємо українською:
Книга → без книги → без цікавої книги → без тієї цікавої книги. *(Book → without a book → without an interesting book → without that interesting book.)*
Місто → з міста → з великого міста → з того нашого великого міста. *(City → from a city → from a big city → from that big city of ours.)*
Студент → від студента → від нового студента → від цього їхнього нового студента. *(Student → from a student → from a new student → from this new student of theirs.)*

> — **Катерина:** Для кого ці квіти? *(For whom are these flowers?)*
> — **Андрій:** Це подарунок для тієї моєї нової сусідки. *(This is a gift for that new neighbor of mine.)*
> — **Катерина:** А цей торт? *(And this cake?)*
> — **Андрій:** А торт ми купили для цього нашого маленького сина. *(And we bought the cake for this little son of ours.)*

<!-- INJECT_ACTIVITY: demonstrative-adjective-noun-fill -->
<!-- INJECT_ACTIVITY: genitive-phrases-correction -->

## Підсумок (Summary)

Genitive phrases require full **узгодження** (agreement) across all modifiers. Adjectives take **-ого** / **-ього** or **-ої** / **-ьої**. Demonstratives become **цього** / **того** and **цієї** / **тієї**. Possessives agree with the noun, but **його** *(his)* and **її** *(her)* never change. 

Читаємо українською:
У мене немає цього нового словника. *(I do not have this new dictionary.)*
Ми гуляємо біля того великого парку. *(We are walking near that big park.)*
Він прийшов без своєї старшої сестри. *(He came without his older sister.)*
Вона купила квиток для нашого доброго друга. *(She bought a ticket for our good friend.)*
Це речі того їхнього нового студента. *(These are the things of that new student of theirs.)*

:::note Самоперевірка (Self-check)
1. Як змінюється прикметник чоловічого роду в родовому відмінку? *(Masculine adjective Genitive ending?)*
— Він має закінчення **-ого** або **-ього**. *(Ending -ого or -ього.)*
2. Яка форма займенника «ця» у родовому відмінку? *(Form of "ця" in Genitive?)*
— Правильна форма — **цієї**. *(Form цієї.)*
3. Чи змінюються займенники «його» та «її», коли вони означають володіння? *(Do possessives "його" and "її" change?)*
— Ні, вони завжди залишаються незмінними. *(No, they always remain unchanged.)*
4. Який порядок слів у фразі «біля цієї моєї великої хати»? *(What is the word order in this phrase?)*
— Прийменник, вказівний займенник, присвійний займенник, прикметник, іменник. *(Preposition, demonstrative, possessive, adjective, noun.)*
:::

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-adjectives-pronouns
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

**Level: A2 (Module 13/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю


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
