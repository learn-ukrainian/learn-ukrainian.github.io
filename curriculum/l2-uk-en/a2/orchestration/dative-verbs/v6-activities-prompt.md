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

(No injection markers found in prose. All activities will go to workbook.)

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

Давальний відмінок — це відмінок комунікації та дії для іншої людини *(the Dative case is the case of communication and action for another person)*. Уявіть, що ви даєте комусь свою енергію, час або важливу інформацію *(Imagine that you give someone your energy, time, or important information)*. Learners often associate the Dative case exclusively with the preposition "to," such as giving a gift "to" a friend. However, many common Ukrainian verbs trigger this case directly because the action itself is inherently directed at a recipient or beneficiary. When you learn a new verb, always pay attention to the case it requires.

В українській мові є дуже важливі дієслова, які завжди вимагають давального відмінка *(In the Ukrainian language, there are very important verbs that always require the Dative case)*. Найпопулярніші з них — це **допомагати** *(to help)* та **дякувати** *(to thank)*. In English, these verbs take a direct object (you simply help *someone*, or you thank *someone*). In Ukrainian, the logic is different: you help *to* someone and you express gratitude *to* someone. The person receiving the help or the thanks is the recipient of your good action, so they must be in the Dative case.

Давайте згадаємо закінчення давального відмінка для іменників, щоб правильно будувати речення *(Let's recall the Dative case endings for nouns to build sentences correctly)*. Чоловічий рід часто має довгі закінчення **-ові** або **-еві** *(Masculine gender often has the long endings -ovi or -evi)*. Наприклад: брат — **братові** *(to a brother)*, вчитель — **вчителеві** *(to a teacher)*, друг — **другові** *(to a friend)*. Жіночий рід зазвичай має закінчення **-і** або **-ї** *(Feminine gender usually has the ending -i or -ji)*. Наприклад: бабуся — **бабусі** *(to a grandma)*, мама — **мамі** *(to a mom)*, колега — **колезі** *(to a colleague)*. Ось приклади *(Here are examples)*: «Я допомагаю мамі готувати вечерю» *(I help mom cook dinner)*. «Син завжди щиро дякує батькові» *(The son always sincerely thanks the father)*.

Дієслова **дзвонити** *(to call, to phone)* та **відповідати** *(to answer)* також вимагають давального відмінка, коли ми говоримо про людей *(The verbs to call and to answer also require the Dative case when we talk about people)*. Я дзвоню **другові** *(I call a friend)*, але я дзвоню **в офіс** *(I call the office - Accusative for direction)*. Вона дзвонить **мамі** кожного вечора *(She calls mom every evening)*. Я відповідаю **студентові** на уроці *(I answer the student in class)*, але я відповідаю **на питання** в тесті *(I answer the question on the test)*. The Dative case is strictly used for the *person* on the other end of the line or the person you are having a conversation with.

Ми також використовуємо давальний відмінок, коли даємо комусь поради або коли хтось нам заважає *(We also use the Dative case when we give advice to someone or when someone bothers us)*. Дієслово **радити** *(to advise)* дуже корисне в діалогах *(The verb to advise is very useful in dialogues)*: «Я раджу **тобі** прочитати цю нову українську книгу» *(I advise you to read this new Ukrainian book)*. Дієслово **заважати** *(to bother, to disturb)* часто звучить у негативних наказах *(The verb to bother often sounds in negative commands)*: «Будь ласка, не заважай **мені** працювати!» *(Please, don't bother me while I work!)*.

Щоб швидко і правильно використовувати ці дієслова, вам треба добре знати особові займенники *(To use these verbs quickly and correctly, you need to know the personal pronouns well)*. Ось повний список для вашої практики в давальному відмінку *(Here is the complete list for your practice in the Dative case)*:
* я → **мені** *(to me)*: Моя сестра завжди допомагає мені.
* ти → **тобі** *(to you)*: Я щиро дякую тобі за все.
* він → **йому** *(to him)*: Ми дзвонимо йому кожен день.
* вона → **їй** *(to her)*: Лікар радить їй більше відпочивати.
* ми → **нам** *(to us)*: Цей гучний шум заважає нам спати.
* ви → **вам** *(to you, pl/formal)*: Наші студенти відповідають вам.
* вони → **їм** *(to them)*: Волонтери активно допомагають їм.

> — **Волонтер:** Добрий день! Я зараз допомагаю **бабусі** нести важкі сумки додому *(Good day! I am currently helping grandma carry heavy bags home)*.
> — **Координатор:** Дуже добре! А де зараз наш новий волонтер Тарас? *(Very good! And where is our new volunteer Taras now?)*
> — **Волонтер:** Він дзвонить своєму **другові**, щоб знайти велику машину *(He is calling his friend to find a large car)*.
> — **Координатор:** Зрозуміло. А хто сьогодні допомагає **Олені** на складі? *(Understood. And who is helping Olena in the warehouse today?)*
> — **Волонтер:** Ніхто. Але я раджу **сусідці** не заважати **їй** працювати *(No one. But I advise the neighbor not to bother her working)*.
> — **Координатор:** Це правильне рішення. Ми завжди раді допомогти **людям** у нашому місті! *(That is the right decision. We are always glad to help people in our city!)*
> — **Волонтер:** Так, і вони часто дуже тепло дякують **нам** *(Yes, and they often thank us very warmly)*.

<!-- INJECT_ACTIVITY: fill-in, complete sentences with the correct dative form after verbs like дякувати, допомагати, and дзвонити -->


## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative) (~550 words total)

В українській мові ми часто говоримо про наші інтереси *(In the Ukrainian language, we often talk about our interests)*. Дієслово **подобатися** *(to be pleasing to, to like)* має дуже незвичну граматику *(The verb to like has very unusual grammar)*. The syntax of this verb is completely reversed compared to English. The person who "likes" something is NOT the grammatical subject. Instead, this person is the experiencer and must be in the Dative case. The thing that is liked is actually the grammatical subject in the Nominative case, and it controls the verb. Ми кажемо: «**Мені** подобається ця нова **книга**» *(To me, this new book is pleasing / I like this new book)*. «**Тобі** подобається цей **чай**» *(To you, this tea is pleasing / You like this tea)*.

Дієслово завжди має форму третьої особи *(The verb always has the third-person form)*. Because the verb agrees with the thing being liked, we only use two present tense forms. We use the singular form when the object is singular, and the plural form when the objects are plural. Ми використовуємо форму однини **подобається** *(is pleasing)* для одного предмета *(We use the singular form for one object)*. Наприклад: «Мені подобається чорна **кава**» *(I like black coffee)*. Ми використовуємо форму множини **подобаються** *(are pleasing)* для багатьох предметів *(We use the plural form for many objects)*. Наприклад: «Їй подобаються старі **фільми**» *(She likes old movies)* або «Нам подобаються українські **пісні**» *(We like Ukrainian songs)*. It is critical to remember that the verb NEVER agrees with the Dative pronoun. The form only changes based on whether the liked object is singular or plural. «Вам подобається це **місто**?» *(Do you like this city?)*. «Вам подобаються ці **вулиці**?» *(Do you like these streets?)*.

У минулому часі це дієслово працює дуже цікаво *(In the past tense, this verb works very interestingly)*. The past tense forms must agree in gender and number with the Nominative subject, not the Dative person. Є чотири форми для минулого часу *(There are four forms for the past tense)*. Чоловічий рід — **подобався** *(was pleasing, masc)*. Жіночий рід — **подобалася** *(was pleasing, fem)*. Середній рід — **подобалося** *(was pleasing, neut)*. Множина — **подобалися** *(were pleasing, pl)*. «Мені подобалася та стара **пісня**» *(I liked that old song - feminine agreement)*. «Тобі подобався той новий **фільм**?» *(Did you like that new movie? - masculine agreement)*. «Йому подобалося те велике місто» *(He liked that big city - neuter agreement)*. «Нам подобалися ті цікаві **книжки**» *(We liked those interesting books - plural agreement)*.

Багато іноземців роблять одну типову граматичну помилку *(Many foreigners make one typical grammatical mistake)*. Вони часто кажуть: «Я подобаю цю книгу» *(They often say: "I please this book")*. This is a direct translation from English, but it sounds absurd. If you use the Nominative pronoun for yourself, it means that YOU are the subject doing the pleasing. Отже, ця фраза має зовсім інший сенс *(So, this phrase has a completely different meaning)*. It actually means that someone likes you! Якщо ви хочете сказати про свої інтереси, ви завжди повинні почати речення з давального відмінка *(If you want to talk about your interests, you must always start the sentence with the Dative case)*. Ми кажемо: «Мені подобається» *(We say: "To me it is pleasing")*.

Ми можемо легко додати емоції в наші речення *(We can easily add emotions to our sentences)*. Для цього ми використовуємо спеціальні прислівники *(For this, we use special adverbs)*. Слово **дуже** *(very much)* робить емоцію сильною *(The word very much makes the emotion strong)*: «Нам дуже подобаються ці високі **гори**» *(We like these high mountains very much)*. Слово **більше** *(more)* показує різницю *(The word more shows a difference)*: «Йому більше подобається теплий чай» *(He likes warm tea more)*. Фраза **зовсім не** *(not at all)* показує сильну негативну реакцію *(The phrase not at all shows a strong negative reaction)*: «Мені зовсім не подобається ця холодна **погода**» *(I do not like this cold weather at all)*.

<!-- INJECT_ACTIVITY: match-up, focus on matching подобатися sentences to their English equivalents, highlighting the reversed subject mapping -->


## Скільки тобі років? Вік у давальному відмінку (Age in the Dative)

В українській мові ми говоримо про вік інакше *(In the Ukrainian language we talk about age differently)*. In English, you "are" a certain age. In some other languages, you "have" years. Українці не використовують дієслово «мати» або «бути» для віку *(Ukrainians do not use the verb "to have" or "to be" for age)*. Замість цього роки «належать» людині *(Instead, the years "belong" to a person)*. Тому ми завжди використовуємо давальний відмінок *(That is why we always use the Dative case)*. Формула дуже проста *(The formula is very simple)*. Спочатку йде людина в давальному відмінку *(First comes the person in the Dative case)*. Потім ми додаємо число *(Then we add the number)*. В кінці ми кажемо слово «**рік**» *(At the end we say the word "year")*. Наприклад: «Мені двадцять **років**» *(I am twenty years old)*. 

Це слово має три різні форми *(This word has three different forms)*. Цей вибір залежить від останньої цифри числа *(This choice depends on the last digit of the number)*. You must pay attention to the grammar of numbers. Якщо число закінчується на один, ми кажемо рік *(If the number ends in one, we say year)*. Наприклад: «Двадцять один рік» *(Twenty-one years)*. Якщо число закінчується на два, три або чотири, ми використовуємо форму **роки** *(If the number ends in two, three, or four, we use the form years)*. Наприклад: «Двадцять два роки» *(Twenty-two years)*. Для всіх інших чисел ми кажемо років *(For all other numbers we say years)*. Це стосується чисел від п'яти до двадцяти *(This applies to numbers from five to twenty)*. Це також стосується всіх круглих десятків *(This also applies to all round tens)*. Наприклад: «Тридцять років» *(Thirty years)* або «п’ятнадцять років» *(fifteen years)*.

Щоб запитати про вік, ми використовуємо спеціальну фразу *(To ask about age, we use a special phrase)*. Ми кажемо: «**Скільки** тобі років?» *(How old are you?)*. Слово «скільки» означає «як багато» *(The word "how many" means "how much")*. Ви можете запитати про вік інших людей *(You can ask about the age of other people)*. Для цього просто змініть особу в давальному відмінку *(For this, simply change the person in the Dative case)*. Наприклад: «Скільки **дідусеві** років?» *(How old is grandfather?)*. Або ви можете запитати: «Скільки їй років?» *(Or you can ask: "How old is she?")*. У розмовній мові українці часто не кажуть слово «років» *(In spoken language, Ukrainians often do not say the word "years")*. Відповідь може бути дуже короткою *(The answer can be very short)*. Хтось може сказати: «Мені двадцять» *(Someone can say: "I am twenty")*. Або: «Йому п'ятдесят» *(Or: "He is fifty")*. Це звучить природно і просто *(This sounds natural and simple)*.

Давайте подивимося на конкретні приклади з родиною *(Let's look at specific examples with family)*. Пам'ятайте, що всі люди стоять у давальному відмінку *(Remember that all people stand in the Dative case)*. Ми кажемо: «Дідусеві вісімдесят років» *(Grandfather is eighty years old)*. Ми також кажемо: «**Дитині** три роки» *(The child is three years old)*. Або ми кажемо: «**Сестрі** двадцять п'ять» *(The sister is twenty-five)*.

> — **Олена:** Скільки **братові** років? *(How old is the brother?)*
> — **Марк:** Йому двадцять один рік. *(He is twenty-one years old.)*

Що робити, якщо ми говоримо про минулий час? *(What to do if we talk about the past tense?)* Sometimes you need to ask "How old were you?" in the past tense. Для минулого часу ми додаємо слово **було** *(For the past tense we add the word "was")*. Це дієслово завжди залишається нейтральним *(This verb always stays neutral)*. Воно ніколи не змінює свою форму *(It never changes its form)*. Ми запитуємо: «Скільки тобі було років?» *(How old were you?)*.

> — **Олена:** Скільки тобі було років тоді? *(How old were you then?)*
> — **Марк:** Мені було десять років. *(I was ten years old.)*

<!-- INJECT_ACTIVITY: true-false, focus on judging whether age expressions use correct dative forms for nouns/pronouns and correct number agreement (рік/роки/років) -->


## Давальний чи знахідний? Порівняння (Dative vs. Accusative)

Як ми знаємо, українські дієслова вимагають різних відмінків *(As we know, Ukrainian verbs require different cases)*. Найчастіше ми вибираємо між знахідним і давальним відмінками *(Most often we choose between the accusative and dative cases)*. Знахідний відмінок показує прямий об'єкт дії *(The accusative case shows the direct object of an action)*. This means you are doing something directly TO a person or a thing. They are the target of your action. Давальний відмінок показує непрямий об'єкт *(The dative case shows the indirect object)*. This means you are doing something FOR or TO a person as a recipient or a listener. Вони отримують вашу дію, допомогу або слова *(They receive your action, help, or words)*. The action is directed towards them, but they are not the direct target.

Давайте порівняємо ці два відмінки на практиці *(Let's compare these two cases in practice)*. Подивіться на два схожі речення *(Look at two similar sentences)*. Ми кажемо: «Я бачу маму» *(We say: "I see mom")*. Тут ми використовуємо знахідний відмінок *(Here we use the accusative case)*. The verb "to see" requires a direct target. Але ми кажемо: «Я допомагаю мамі» *(But we say: "I help mom")*. Тут ми використовуємо давальний відмінок *(Here we use the dative case)*. The verb "to help" is directed to a recipient. Дієслова **бачити** *(to see)*, **знати** *(to know)*, **любити** *(to love)*, та **чекати** *(to wait)* вимагають знахідного відмінка *(The verbs to see, to know, to love, and to wait require the accusative case)*. Дієслова **допомагати** *(to help)*, **радити** *(to advise)*, **дякувати** *(to thank)*, та **дзвонити** *(to call)* вимагають давального відмінка *(The verbs to help, to advise, to thank, and to call require the dative case)*.

Деякі дієслова можуть використовувати обидва відмінки одночасно *(Some verbs can use both cases simultaneously)*. Ми можемо давати щось комусь *(We can give something to someone)*. Це дієслова **давати** *(to give)*, **казати** *(to say)*, та **показувати** *(to show)*. Річ завжди стоїть у знахідному відмінку *(The thing always stands in the accusative case)*. Людина завжди стоїть у давальному відмінку *(The person always stands in the dative case)*. Наприклад: «Я даю яблуко братові» *(For example: "I give an apple to the brother")*. Слово «яблуко» — це знахідний відмінок *(The word "apple" is the accusative case)*. Слово «братові» — це давальний відмінок *(The word "to the brother" is the dative case)*. Інший приклад: «Він показує книжку сестрі» *(Another example: "He shows a book to the sister")*. The book is the direct object in the Accusative case, and the sister is the recipient in the Dative case.

Займенники також мають різні форми для цих відмінків *(Pronouns also have different forms for these cases)*. Для знахідного відмінка ми використовуємо такі форми: **мене** *(me)*, **тебе** *(you)*, **його** *(him)*, **її** *(her)*, **нас** *(us)*, **вас** *(you)*, та **їх** *(them)*. Наприклад: «Ти бачиш мене» *(For example: "You see me")*. Для давального відмінка форми інші: **мені** *(to me)*, **тобі** *(to you)*, **йому** *(to him)*, **їй** *(to her)*, **нам** *(to us)*, **вам** *(to you)*, та **їм** *(to them)*. Наприклад: «Ти допомагаєш мені» *(For example: "You help me")*. Here is a simple decision strategy tip. When you want to use a pronoun, ask yourself a question. Is this person a direct target? Якщо так, використовуйте знахідний відмінок *(If yes, use the accusative case)*. Is this person a listener or a recipient? Якщо так, використовуйте давальний відмінок *(If yes, use the dative case)*.

<!-- INJECT_ACTIVITY: quiz, focus on choosing between dative and accusative for the underlined noun or pronoun in sentences like "Він бачить (подругу/подрузі)" or "Він дзвонить (подрузі/подругу)." -->


## Підсумок

У цьому модулі ми вивчили давальний відмінок *(In this module we learned the dative case)*. You now know that some Ukrainian verbs require the dative case for the person receiving the action. Ми також навчилися говорити про вік та речі, які нам подобаються *(We also learned to talk about age and things we like)*.

Ось головні дієслова цього модуля *(Here are the main verbs of this module)*:
* **допомагати** *(to help)*
* **дякувати** *(to thank)*
* **дзвонити** *(to call)*
* **радити** *(to advise)*
* **заважати** *(to bother)*
* **відповідати** *(to answer)*
* **подобатися** *(to like)*

Пам’ятайте, що дієслово «подобатися» має незвичну структуру *(Remember that the verb "to like" has an unusual structure)*. The person who likes something is in the dative case, and the thing they like is the grammatical subject. Також ми використовуємо давальний відмінок, коли говоримо про вік *(Also we use the dative case when we talk about age)*. Наприклад: «Моєму братові двадцять років» *(For example: "My brother is twenty years old")*.

Перевірте себе *(Check yourself)*. Дайте відповіді на ці запитання *(Answer these questions)*:
* Як сказати "I help my brother" українською?
* Яка форма слова «рік» потрібна для числа 22?
* Чому ми кажемо «Мені подобаються книги», а не «Мені подобається книги»?
* Який відмінок ми використовуємо для віку?

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
