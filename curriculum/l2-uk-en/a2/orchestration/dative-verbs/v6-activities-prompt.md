<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-verbs.yaml` file for module **21: Допомагати, дякувати, дзвонити** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-focus-completing-sentences-with-correct-dative-noun-pronoun-forms-after-help-thank-call -->`
- `<!-- INJECT_ACTIVITY: match-up-focus-matching-ukrainian-sentences-to-english-i-like-equivalents-to-cement-the-subject-object-shift -->`
- `<!-- INJECT_ACTIVITY: true-false-focus-judging-the-correctness-of-age-expressions-dative-form-correct-year-noun-agreement -->`
- `<!-- INJECT_ACTIVITY: quiz-focus-choosing-between-dative-and-accusative-for-the-noun-pronoun-after-specific-verbs-e-g -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences with the correct dative form after dative-governing verbs
  items: 8
  type: fill-in
- focus: Choose dative vs. accusative for the underlined noun/pronoun (допомагати
    мам_ vs. бачити мам_)
  items: 8
  type: quiz
- focus: Match подобатися sentences to their English equivalents (reversed subject
    mapping)
  items: 8
  type: match-up
- focus: Judge whether age expressions use correct dative forms and number agreement
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- довіряти (to trust)
- вибачати (to forgive)
- посміхатися (to smile (at someone))
- співчувати (to sympathize (with someone))
- заздрити (to envy)
required:
- допомагати (to help)
- дякувати (to thank)
- дзвонити (to call, to phone)
- радити (to advise)
- заважати (to bother, to disturb)
- подобатися (to be pleasing to, to like (reversed syntax))
- відповідати (to answer (someone))
- рік (year)
- роки (years (2-4))
- років (years (5+))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслова з давальним відмінком (Verbs That Take the Dative)

Ці дієслова вимагають особливої уваги. *(These verbs require special attention.)*
In English, when you help someone, thank someone, or call someone, the person is usually the direct object. You simply say "I help him" or "She thanks the teacher."
В українській мові граматична логіка цих дієслів зовсім інша. *(In the Ukrainian language, the grammatical logic of these verbs is completely different.)*
Ці дієслова показують дію, яка має конкретного отримувача. *(These verbs show an action that has a specific recipient.)*
Because the action is indirect, the person receiving the help or thanks must be in the Dative case (**давальний відмінок**).
Ми завжди ставимо питання: **кому?** *(to whom?)* або **чому?** *(to what?)*.
Ви даєте вашу допомогу або ваші слова іншій людині. *(You give your help or your words to another person.)*

Давайте детально розглянемо дієслово **допомагати** *(to help)*.
Я дуже часто допомагаю своїй великій родині. *(I very often help my large family.)*
When we use this verb, the family members receiving the help must take Dative endings.
Наприклад, я щодня допомагаю **мамі** *(mom)* та молодшій **сестрі** *(sister)*.
Моя донька допомагає **бабусі** готувати вечерю. *(My daughter helps grandma cook dinner.)*
For masculine nouns, we strongly prefer the endings **-ові** or **-еві** when talking about people. This makes it instantly clear that the person is the recipient in the Dative case.
Я з радістю допомагаю **татові** *(dad)*.
Мій малий син допомагає старшому **братові** *(brother)* робити уроки.
Він завжди допомагає своєму найкращому **другові** *(friend)*.
Ці закінчення роблять вашу українську мову дуже природною і правильною. *(These endings make your Ukrainian language very natural and correct.)*

Тепер поговоримо про дієслово **дякувати** *(to thank)*.
Це надзвичайно важливе слово для ввічливого спілкування. *(This is an extremely important word for polite communication.)*
Граматика тут дуже специфічна. *(The grammar here is very specific.)*
A common mistake for learners familiar with Russian is to use the Accusative case (like the Russian word «благодарить»). The phrase «дякую вас» is completely incorrect in Ukrainian; it is a direct grammatical translation from Russian.
В українській мові ми завжди кажемо «дякую **вам**» *(thank you [plural/formal])* або «дякую **тобі**» *(thank you [singular/informal])*.
Ми щиро дякуємо головному **лікарю** *(the doctor)*.
Я дуже дякую **вчителеві** *(the teacher)* за його щоденну допомогу.
Ми голосно дякуємо **друзям** *(friends)* за чудовий подарунок.
Завжди пам'ятайте це просте правило. *(Always remember this simple rule.)*

Ще два дуже важливі дієслова щоденного вжитку — це **дзвонити** *(to call)* та **телефонувати** *(to phone)*.
Ці дієслова також показують прямий напрямок дії до конкретної людини. *(These verbs also show a direct direction of action to a specific person.)*
Я дуже часто дзвоню моїй найкращій **подрузі** *(female friend)* Марії.
Він майже щодня телефонує **Андрієві** *(Andriy)*.
In English, you might say "I make a call to someone," using a preposition. In Ukrainian, you do not use the preposition **до** *(to)* with these verbs for people.
Моя мама щовечора дзвонить старшому **синові** *(son)*.
Подзвони **їй** *(her)* завтра вранці, будь ласка.
Давальний відмінок сам показує напрямок вашого дзвінка. *(The Dative case itself shows the direction of your call.)*

Є ще кілька дуже корисних дієслів, які працюють саме за цим правилом: **радити** *(to advise)*, **заважати** *(to bother, to disturb)*, та **відповідати** *(to answer)*.
Я **раджу тобі** *(I advise you)* обов'язково подивитися цей новий фільм.
Вибачте, я зараз не **заважаю вам** *(am I bothering you)*?
Хороший учень завжди правильно **відповідає вчителеві** *(answers the teacher)*.
Ми часто використовуємо ці дієслова для ввічливих прохань. *(We often use these verbs for polite requests.)*
Будь ласка, не **заважай мені** *(do not bother me)* працювати над проектом.
Завжди швидко **відповідай мамі** *(answer mom)*, коли вона щось питає.
Інші корисні дієслова з давальним відмінком: **довіряти** *(to trust)*, **вибачати** *(to forgive)*, **посміхатися** *(to smile)*, **співчувати** *(to sympathize)*, та **заздрити** *(to envy)*. Я **довіряю другові** *(I trust my friend)*. Вона щиро **посміхається дитині** *(she smiles at the child)*.


Прочитайте цей короткий текст про допомогу. *(Read this short text about helping.)*
Сьогодні важливий День волонтера в нашому місті. *(Today is an important Volunteer Day in our city.)*

> — **Волонтер:** Олено, я зараз **допомагаю сусідці** *(I help the neighbor)* прибирати великий парк. Тобі потрібна допомога?
> — **Олена:** Ні, я вже все зробила. Але я **раджу тобі** *(I advise you)* трохи відпочити.
> — **Волонтер:** Добре, тоді я **дзвоню другові** *(I call the friend)* Івану. Він має принести воду.
> — **Іван:** Привіт! Я вже тут. Тримай свіжу воду та смачну їжу.
> — **Волонтер:** Я щиро **дякую тобі** *(I thank you)* за цю велику допомогу!

<!-- INJECT_ACTIVITY: fill-in-focus-completing-sentences-with-correct-dative-noun-pronoun-forms-after-help-thank-call -->

## Мені подобається: Давальний відмінок особи (The Experiencer Dative with подобатися)

Зараз ми вивчимо одне з найпопулярніших слів. *(Now we will learn one of the most popular words.)* Це дієслово **подобатися** *(to like, to be pleasing)*. Ця граматична конструкція працює не так, як в англійській мові. In English, when you say "I like the book", the word "I" is the active subject, and the book is the direct object. In Ukrainian, the logic is completely reversed. Ми кажемо «Мені подобається книжка». У цьому реченні слово «книжка» — це головний підмет у називному відмінку. *(In this sentence, the word "book" is the main subject in the nominative case.)* А слово «мені» стоїть у давальному відмінку. *(And the word "to me" is in the dative case.)* Literally, this Ukrainian sentence means "The book is pleasing to me." Дія йде від предмета до людини. *(The action goes from the object to the person.)* Тому людина завжди має форму давального відмінка. *(That is why the person always takes the form of the dative case.)*

Форма дієслова залежить тільки від предмета. *(The form of the verb depends only on the object.)* Вона не залежить від людини, якій подобається цей предмет. *(It does not depend on the person who likes this object.)* Якщо предмет один, ми використовуємо форму однини **подобається**. Мені подобається цей гарячий **чай** *(tea)*. Тобі подобається нова **квартира** *(apartment)*. Якщо предметів багато, ми беремо форму множини **подобаються**. Мені подобаються ці красиві **квіти** *(flowers)*. Йому подобаються старі **фільми** *(movies)*. The English translation remains "I like" or "you like", but the Ukrainian verb ending physically changes to match the plural subjects «квіти» or «фільми». Це дуже важливе правило. *(This is a very important rule.)*

Ми дуже часто використовуємо різні особові займенники з цим дієсловом. *(We very often use various personal pronouns with this verb.)* Ви вже знаєте форму «мені подобається» *(I like)*. Якщо ви запитуєте друга, ви кажете «**тобі** подобається» *(you like [singular/informal])* або «тобі подобаються». Для третьої особи ми кажемо «**йому** подобається» *(he likes)* та «**їй** подобається» *(she likes)*. У множині ми маємо форму «**нам** подобається» *(we like)*. Якщо ви говорите з учителем або групою людей, використовуйте форму «**вам** подобається» *(you like [plural/formal])*. Для інших людей є форма «**їм** подобається» *(they like)*. Їм подобається гуляти в парку. *(They like to walk in the park.)* Нам подобаються ці смачні яблука. *(We like these tasty apples.)*

У минулому часі правило працює так само. *(In the past tense, the rule works the same way.)* Дієслово змінює свою форму і показує рід предмета, який стоїть у називному відмінку. *(The verb changes its form and shows the gender of the object, which is in the nominative case.)* Якщо предмет чоловічого роду, ми кажемо «мені **подобався**». Мені подобався цей довгий фільм. *(I liked this long movie.)* Для жіночого роду потрібна форма «мені **подобалася**». Тобі подобалася ця чорна **кава** *(coffee)*. Якщо підмет середнього роду, використовуйте закінчення «-о»: «мені **подобалося**». Йому подобалося солодке **морозиво** *(ice cream)*. У множині форма завжди однакова: «мені **подобалися**». Нам подобалися ті цікаві книги. *(We liked those interesting books.)* The verb strictly mirrors the gender of the thing being liked, never the experiencer.

Якщо ви хочете зробити заперечення, просто поставте частку **не** *(not)* перед дієсловом. *(If you want to make a negation, just put the particle "не" before the verb.)* Мені не подобається ця гучна музика. *(I do not like this loud music.)* Їй не подобався той старий ресторан. *(She did not like that old restaurant.)* Запитувати про смаки також дуже просто. *(Asking about tastes is also very simple.)* Тобі не подобається ця нова пісня? *(Do you not like this new song?)* Що вам подобається в Україні? *(What do you like in Ukraine?)* Мені дуже подобається вивчати українську мову. *(I really like studying the Ukrainian language.)* А що подобається тобі? *(And what do you like?)*

<!-- INJECT_ACTIVITY: match-up-focus-matching-ukrainian-sentences-to-english-i-like-equivalents-to-cement-the-subject-object-shift -->

## Скільки тобі років? Вік у давальному відмінку (Age in the Dative)

Говорити про свій **вік** *(age)* українською мовою дуже легко, якщо ви пам'ятаєте попереднє правило. *(Talking about your age in Ukrainian is very easy if you remember the previous rule.)* In English, you "are" a certain age, using the verb "to be" with the subject. В українській мові ми використовуємо іншу логіку. *(In the Ukrainian language, we use a different logic.)* Age is treated as a fact or an experience that happens *to* someone. Тому людина завжди стоїть у давальному відмінку. *(That is why the person always stands in the dative case.)* The pattern is simple and strict: [Person in Dative] + [Number] + [Word for "year"]. Наприклад, ми кажемо: «Мені двадцять років». *(For example, we say: "To me twenty years".)* Дідусеві вісімдесят років. *(Grandpa is eighty years old.)* The verb "to be" is completely omitted in the present tense, making the structure very concise and direct.

The most complex part of stating your age is choosing the correct form for the word "year". В українській мові є три різні форми цього слова. *(In the Ukrainian language, there are three different forms of this word.)* The choice depends entirely on the last digit of the number you are using.

1. Форма **рік** *(year)* використовується для чисел, які закінчуються на 1, але не 11.
2. Форма **роки** *(years)* потрібна для чисел, які закінчуються на 2, 3, або 4, але не 12, 13, 14.
3. Форма **років** *(years [Genitive plural])* використовується для всіх інших чисел: 5, 6, 7, 8, 9, 0, а також для групи від 11 до 19.

| Число (Number) | Форма (Form) | Приклад (Example) |
| :--- | :--- | :--- |
| 1, 21, 31... | рік | Моєму братові двадцять один рік. *(My brother is 21 years old.)* |
| 2, 3, 4, 22, 23, 24... | роки | Моїй сестрі двадцять два роки. *(My sister is 22 years old.)* |
| 5-20, 25-30, 35-40... | років | Моїй мамі п'ятдесят років. *(My mom is 50 years old.)* |

Щоб запитати про вік, ми використовуємо слово **скільки** *(how many)*. *(To ask about age, we use the word "how many".)* Після слова «скільки» іменник завжди стоїть у родовому відмінку множини. *(After the word "how many", the noun always stands in the genitive case plural.)* That is why the question always uses the form «років», regardless of what the actual age might be. Людина, про яку ми запитуємо, залишається в давальному відмінку. *(The person about whom we are asking remains in the dative case.)* Скільки тобі років? *(How old are you?)* Скільки йому років? *(How old is he?)* Скільки років вашому синові? *(How old is your son?)* The structure of the question perfectly mirrors the structure of the answer you expect.

Подивімося, як люди говорять про вік у реальному житті. *(Let's see how people talk about age in real life.)*

> — **Олена:** Привіт, Антоне! Скільки років твоєму татові? *(Hi, Anton! How old is your dad?)*
> — **Антон:** Йому п'ятдесят два роки. А твоїй мамі? *(He is fifty-two years old. And your mom?)*
> — **Олена:** Їй сорок дев'ять років. *(She is forty-nine years old.)*
> — **Антон:** А скільки років твоїй бабусі? *(And how old is your grandma?)*
> — **Олена:** Моїй бабусі сімдесят один рік. *(My grandma is seventy-one years old.)*

Як бачите, ми часто запитуємо про вік родичів або друзів. *(As you can see, we often ask about the age of relatives or friends.)* Головне — пам'ятати про правильний відмінок для людини та правильну форму слова. *(The main thing is to remember about the correct case for the person and the correct form of the word.)*

<!-- INJECT_ACTIVITY: true-false-focus-judging-the-correctness-of-age-expressions-dative-form-correct-year-noun-agreement -->

## Давальний чи знахідний? Порівняння (Dative vs. Accusative with Verbs)

Ми вже добре знаємо два важливі відмінки: знахідний і давальний. *(We already know well two important cases: accusative and dative.)* Коли саме ми використовуємо кожен з них? *(When exactly do we use each of them?)* It all depends on the internal logic of the action and the specific verb you choose. Знахідний відмінок завжди показує пряму дію на об'єкт. *(The accusative case always shows a direct action on an object.)* Think of it as a direct hit on a target. Ви бачите людину, ви добре знаєте мову, ви любите музику. *(You see a person, you know a language well, you love music.)* Наприклад, ми кажемо «я бачу маму». *(For example, we say "I see mom".)* Давальний відмінок має зовсім іншу логіку. *(The dative case has a completely different logic.)* Він показує отримувача дії. *(It shows the recipient of the action.)* Think of it as a hand-off, a transfer, or a delivery. Ви даєте щось людині, ви допомагаєте комусь. *(You give something to a person, you help someone.)* Наприклад, ми говоримо «я допомагаю мамі» або «я дякую вчителеві». *(For example, we say "I help mom" or "I thank the teacher".)* Дія йде до людини, а не прямо на неї. *(The action goes to the person, and not directly on them.)*

Уважно подивімося на ці відмінки разом. *(Let's look carefully at these cases together.)* Пряме порівняння допомагає зрозуміти різницю набагато краще. *(A direct comparison helps to understand the difference much better.)* Завжди звертайте увагу на закінчення слів. *(Always pay attention to the endings of words.)*
«Я люблю маму». *(I love mom.)* Це знахідний відмінок, пряма дія. *(This is the accusative case, direct action.)*
«Я допомагаю мамі». *(I help mom.)* Це давальний відмінок, дія йде до людини. *(This is the dative case, the action goes to the person.)*
Ви бачите, як змінюється слово «мама»? *(Do you see how the word "mom" changes?)* Вона має закінчення «-у» у знахідному відмінку, і «-і» у давальному. *(It has the ending "-u" in the accusative case, and "-i" in the dative.)*
Ось ще кілька корисних прикладів. *(Here are a few more useful examples.)*
«Я бачу друга». *(I see a friend.)* Це знахідний відмінок. *(This is the accusative case.)*
«Я дзвоню другові». *(I call a friend.)* Це вже давальний відмінок. *(This is already the dative case.)*
«Ми чекаємо подругу». *(We wait for a friend.)* Знахідний відмінок. *(Accusative case.)*
«Ми дякуємо подрузі». *(We thank the friend.)* Давальний відмінок. *(Dative case.)*

Деякі дієслова можуть використовувати обидва відмінки одночасно. *(Some verbs can use both cases simultaneously.)* Найкращі приклади — це слова **давати** *(to give)* та **розповідати** *(to tell)*. *(The best examples are the words "to give" and "to tell".)* Структура таких речень є дуже логічною. *(The structure of such sentences is very logical.)* Спочатку йде дієслово, потім людина у давальному відмінку, а потім річ у знахідному. *(First goes the verb, then the person in the dative case, and then the thing in the accusative.)* Формула така: дієслово + кому? + що? *(The formula is this: verb + to whom? + what?)*
Я даю мамі квіти. *(I give mom flowers.)* Кому я даю? Мамі. *(To whom do I give? To mom.)* Що я даю? Квіти. *(What do I give? Flowers.)*
Він розповідає нам історію. *(He tells us a story.)* Кому він розповідає? Нам. *(To whom does he tell? To us.)* Що він розповідає? Історію. *(What does he tell? A story.)*
Вони купують синові подарунок. *(They buy a present for the son.)* Такі речення дають багато інформації одразу. *(Such sentences give a lot of information at once.)*

Як обрати правильний відмінок під час розмови? *(How to choose the correct case during a conversation?)* There is a simple strategic rule. Якщо людина є отримувачем вашої дії, використовуйте давальний відмінок. *(If the person is the recipient of your action, use the dative case.)* Communication, help, or gifts always travel to a destination. Якщо людина є об'єктом дії, використовуйте знахідний відмінок. *(If the person is the object of the action, use the accusative case.)* Seeing, liking, or waiting are direct actions on an object.
Цікавий приклад — це дієслова зі значенням «кликати». *(An interesting example is verbs with the meaning 'to call/summon'.)*
Слово **дзвонити** *(to call by phone)* вимагає давального відмінка. *(The word "to call by phone" requires the dative case.)* Я дзвоню братові. *(I call my brother.)* Це комунікація, яка йде до нього. *(This is communication that goes to him.)*
Але слово **кликати** *(to call/summon)* вимагає знахідного відмінка. *(But the word "to call/summon" requires the accusative case.)* Я кличу брата. *(I call my brother.)* Це пряма дія безпосередньо на нього. *(This is a direct action directly on him.)*

<!-- INJECT_ACTIVITY: quiz-focus-choosing-between-dative-and-accusative-for-the-noun-pronoun-after-specific-verbs-e-g -->

## Підсумок

Ми вивчили дуже важливу тему сьогодні. *(We learned a very important topic today.)* Давальний відмінок має три головні ролі у таких реченнях. *(The dative case has three main roles in such sentences.)*

По-перше, дієслова **допомагати** *(to help)*, **дякувати** *(to thank)* та **дзвонити** *(to call)* вимагають форми «кому?». *(First, the verbs "to help", "to thank", and "to call" require the "to whom?" form.)* Дія йде до людини. *(The action goes to the person.)*

По-друге, дієслово **подобатися** *(to like)* має зворотну структуру. *(Second, the verb "to like" has a reverse structure.)* Людина стоїть у давальному відмінку, а річ — у називному. *(The person is in the dative case, and the thing is in the nominative.)*

По-третє, ми використовуємо давальний відмінок для віку. *(Third, we use the dative case for age.)*

Перевірте свої знання: *(Check your knowledge:)*

- Як правильно сказати: «дякую тебе» чи «дякую тобі»? *(How to say it correctly: "thank you [acc.]" or "thank you [dat.]"?)* Правильно: «дякую тобі». *(Correct: "thank you [dat.]".)*
- Яку форму має дієслово «подобатися», якщо мені подобаються книги? *(What form does the verb "to like" have if I like books?)* Множина: «подобаються». *(Plural: "they are pleasing".)*
- Яку форму слова **рік** *(year)* ми вживаємо для числа 22? *(Which form of the word "year" do we use for the number 22?)* Форма: «двадцять два роки». *(Form: "twenty-two years".)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-verbs
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

**Level: A2 (Module 21/60) — ELEMENTARY**

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
