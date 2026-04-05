<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 33: Скільки? (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-033
level: A2
sequence: 33
slug: plural-genitive
version: '1.0'
title: Скільки?
subtitle: Родовий відмінок множини — найскладніший відмінок
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can form the Genitive plural for I відміна nouns, applying the zero 
    ending correctly and inserting fleeting vowels where needed (сестер, 
    книжок).
  - Learner can form the Genitive plural for II відміна nouns using the correct 
    ending (-ів/-їв for most masculine, zero ending for most neuter, -ей for 
    soft-stem masculine).
  - Learner can use quantity expressions (скільки, багато, мало, кілька, 
    декілька, numerals 5+) with the Genitive plural correctly.
  - Learner can produce short utterances about quantities in everyday contexts 
    (shopping, describing a room, talking about family).
dialogue_situations:
  - setting: 'School cafeteria inventory — counting remaining items: Скільки тарілок
      (f, plates)? Двадцять. Виделок (f, forks)? П''ятнадцять. Ложок (f, spoons)?
      Десять. Склянок (f, glasses)? Немає склянок!'
    speakers:
      - Завідувач їдальні (cafeteria manager)
      - Помічник
    motivation: 'Genitive plural: тарілка→тарілок, виделка→виделок, склянка→склянок'
content_outline:
  - section: 'Чому родовий множини такий складний? (Why Is the Genitive Plural So
      Hard?)'
    words: 400
    points:
      - 'Overview: Gen.Pl. has THREE possible endings — zero (нульове закінчення),
        -ів/-їв, -ей — plus fleeting vowels. No single rule covers all nouns.'
      - 'Why it matters: Gen.Pl. appears after numbers 5+, after багато/мало/кілька/скільки,
        and in many prepositional phrases. It is the most common plural case.'
      - 'Strategy: learn by відміна and gender, with the most frequent words first.'
  - section: 'I відміна: нульове закінчення (First Declension: Zero Ending)'
    words: 500
    points:
      - 'Most I відміна nouns (feminine -а/-я) take zero ending: книга → книг, зірка
        → зірок, вишня → вишень.'
      - 'Fleeting vowels appear when consonant clusters form: сестра → сестер, земля
        → земель, пісня → пісень, казка → казок.'
      - 'Exceptions with -ів or -ей: суддя → суддів, сім''я → сімей, стаття → статей.'
      - 'Drill: form Gen.Pl. for common I відміна nouns with and without fleeting
        vowels.'
  - section: 'II відміна: -ів, нульове, -ей (Second Declension: Three Patterns)'
    words: 600
    points:
      - 'Masculine hard stems: -ів (столів, братів, учнів, днів).'
      - 'Masculine soft stems: -ів or -ей (учителів, but гостей, коней).'
      - 'Neuter -о: zero ending, often with fleeting vowels (вікон, слів, but міст
        — no fleeting vowel).'
      - 'Neuter -е/-я: -ів/-їв (морів, подвір''їв) or zero (сердець, яєць).'
      - 'The -ин/-їн suffix disappears: громадянин → громадян, киянин → киян.'
  - section: 'Скільки чого? Кількість у житті (How Much of What? Quantity in Daily
      Life)'
    words: 500
    points:
      - 'Pattern: скільки/багато/мало/кілька/декілька + Gen.Pl. — Скільки студентів?
        Багато книжок. Мало грошей. Кілька друзів.'
      - 'Numbers 5+ take Gen.Pl.: п''ять яблук, десять студентів, двадцять гривень.'
      - 'Contrast with 2-4 (Nom.Pl.): два студенти vs. п''ять студентів; три книжки
        vs. сім книжок.'
      - 'Dialogues: at a store asking for quantities, describing what is in a room,
        talking about family members.'
vocabulary_hints:
  required:
    - родовий відмінок (genitive case)
    - нульове закінчення (zero ending)
    - кількість (quantity, amount)
    - багато (a lot, many)
    - мало (few, little)
    - кілька (a few, several)
    - декілька (a few, several)
    - скільки (how many, how much)
    - гроші (money)
    - гривня (hryvnia)
  recommended:
    - вставний голосний (fleeting vowel)
    - виняток (exception)
    - десяток (a dozen, ten-unit)
activity_hints:
  - type: fill-in
    focus: Form the Genitive plural from given nouns (mixed відміни), inserting 
      fleeting vowels where needed
    items: 8
  - type: quiz
    focus: Choose the correct Gen.Pl. form in quantity expressions (багато ___, 
      п'ять ___)
    items: 8
  - type: match-up
    focus: Match singular nouns with their correct Genitive plural forms
    items: 8
  - type: true-false
    focus: Judge whether a given Gen.Pl. form is correct or incorrect (common 
      errors like книгів instead of книг)
    items: 8
references:
  - title: Літвінова Grade 6, с. 160
    notes: Gen.Pl. endings for II відміна with full table and exercises
  - title: Заболотний Grade 6, §62
    notes: Gen.Pl. of I відміна — zero ending, fleeting vowels, exceptions
  - title: "ULP: Genitive Plural"
    url: "https://www.ukrainianlessons.com/genitive-case/"
    notes: Practical examples of Gen.Pl. in everyday speech

</plan_content>

## Generated Content

<generated_module_content>
## Чому родовий множини такий складний?

Українська мова має сім відмінків. Родовий відмінок множини — це справжнє випробування для студентів. Називний відмінок множини дуже простий і зрозумілий. Ми просто додаємо закінчення **-и** *(ending -y)* або **-і** *(ending -i)*. Наприклад, ми кажемо «столи», «книги», «дні». Але **родовий відмінок** *(genitive case)* працює зовсім інакше. The Genitive plural is often considered the hardest part of Ukrainian noun declension. It is the most unpredictable case in the plural form. Instead of learning one simple rule, you must master three completely different grammatical patterns. These patterns include the ending **-ів** *(ending -iv)*, the ending **-ей** *(ending -ey)*, and the **нульове закінчення** *(zero ending)*. In addition to these unpredictable endings, words often change their internal vowels to maintain a nice rhythm. Це робить цей відмінок найскладнішим правилом.

Без цього відмінка неможливо говорити українською. Ми використовуємо його кожного дня у магазині, на роботі або вдома. You must use the Genitive plural when you count objects starting from five to infinity. Наприклад, ми кажемо «п'ять **гривень**» *(five hryvnias)* або «десять **студентів**» *(ten students)*. Він також потрібен для слів, які означають **кількість** *(quantity)*. Це такі популярні слова, як **багато** *(a lot, many)*, **мало** *(few, little)*, **кілька** *(a few, several)* та **декілька** *(a few, several)*. Ми часто кажемо «багато **друзів**» *(many friends)* або «мало **грошей**» *(little money)*. Цей відмінок описує відсутність предмета або людини. Коли ми використовуємо слово «**немає**» *(there is no / are no)*, ми завжди пишемо родовий відмінок. Наприклад: «немає **квитків**» *(there are no tickets)*. Тому дуже важливо знати ці складні форми.

Як правильно обрати закінчення для нового слова? The logic behind the Genitive plural endings depends on two main factors. First, you need to know the grammatical gender of the noun you want to use. Second, you must determine its declension group, which is called **відміна** *(declension)*. Different declensions prefer completely different endings in the plural form. Жіночий рід найчастіше обирає нульове закінчення. Чоловічий рід зазвичай має довге закінчення -ів. Середній рід також часто отримує нульове закінчення, як і жіночий рід. Але українська мова має багато **винятків** *(exceptions)*. You will find that some masculine nouns behave identically to feminine nouns, and vice versa. Іноді вам доведеться просто запам'ятовувати унікальні форми для популярних слів.

Фонетика також грає дуже важливу роль у цьому процесі. The choice between the endings -ів and -ей often depends on the final consonant of the word's stem. Words with "hard" consonants usually take the ending -ів, while words with "soft" consonants sometimes take -ей. Найцікавіший процес відбувається, коли слово має нульове закінчення. When a word loses its final vowel, you might get a cluster of crowded, difficult consonants at the end. Ukrainian phonetics strongly dislikes unpronounceable consonant clusters. Тому мова автоматично додає **вставний голосний** *(fleeting vowel)* між цими приголосними. Це робить слово гарним і зручним для вимови. Наприклад, слово «**школа**» *(school)* втрачає своє закінчення «-а». Ми не можемо сказати «школ», тому що це важко. Тому ми кажемо «**шкіл**» *(of schools)*, де з'являється новий звук «і».

## I відміна: нульове закінчення

Перша відміна — це іменники переважно жіночого роду, які мають закінчення -а або -я. Коли ми утворюємо родовий відмінок множини, ці слова зазвичай втрачають своє закінчення. Ми називаємо це граматичне явище **нульове закінчення** *(zero ending)*. The primary rule for these nouns is very logical and surprisingly simple: you just drop the final vowel completely. Це популярне правило, яке ви будете використовувати дуже часто. Наприклад, слово «**газета**» *(newspaper)* перетворюється на форму «**газет**» *(of newspapers)*. Слово «**книга**» *(book)* стає короткою формою «**книг**» *(of books)*. А слово «**хмара**» *(cloud)* швидко стає формою «**хмар**» *(of clouds)*. If a feminine noun ends in -я, it usually indicates that the preceding consonant is soft. When you drop this final -я, you must always preserve that phonetic softness. Тому ми пишемо м'який знак у кінці таких нових слів. Наприклад, слово «**диня**» *(melon)* завжди стає формою «**динь**» *(of melons)*. Це базове правило для першої відміни, яке дуже легко запам'ятати.

Але українська фонетика не любить, коли багато приголосних стоять разом. Коли слово втрачає останню літеру -а або -я, може з'явитися важка комбінація приголосних звуків. We call this a difficult consonant cluster. To solve this pronunciation problem, the Ukrainian language automatically inserts a new letter inside the root of the word. Ми називаємо це цікаве рішення **вставний голосний** *(fleeting vowel)*. The language usually inserts the letter -о- between two hard consonants to make the word easier to say. Наприклад, слово «**казка**» *(fairy tale)* стає формою «**казок**» *(of fairy tales)*. Ми ніколи не кажемо «казк», тому що це важко і незручно. Так само слово «**сумка**» *(bag)* перетворюється на зручну форму «**сумок**» *(of bags)*. If the surrounding consonants are soft, hissing, or contain the letter 'й', the language inserts the letter -е- instead. Наприклад, слово «**сестра**» *(sister)* стає дуже красивим словом «**сестер**» *(of sisters)*. А слово «**земля**» *(land, earth)* перетворюється на «**земель**» *(of lands)*. Це правило робить українську мову такою приємною для наших вух.

Деякі іменники жіночого роду мають м'яку основу перед своїм закінченням -я. Many feminine nouns ending in -я with a soft stem follow a special but predictable pattern. Наприклад, слово «**пісня**» *(song)* стає красивим словом «**пісень**» *(of songs)*. Тут також добре працює вставний голосний, тому нове слово звучить м'яко. Але є слова, які мають подвійну приголосну перед останньою літерою -я. Nouns that end with a double consonant plus -я take the specific ending -ей instead of the zero ending. Наприклад, слово «**стаття**» *(article)* стає цікавим словом «**статей**» *(of articles)*. Ми також повинні розрізняти жіночий та справжній чоловічий рід. Наприклад, відоме слово «**суддя**» *(judge)* також належить до нашої першої відміни. Але це слово чоловічого роду, тому воно має інші граматичні правила. Воно отримує типове чоловіче закінчення, а не наше нульове закінчення. Називний відмінок — це «суддя», а родовий відмінок множини — це «**суддів**» *(of judges)*. Це дуже важлива різниця для щоденних розмов.

Українська мова має деякі слова, які працюють як справжні **винятки** *(exceptions)*. Some very common feminine nouns absolutely refuse to use the zero ending, even though they belong to the first declension. Замість цього вони отримують довге закінчення -ей, яке зазвичай належить іншим граматичним групам. Наприклад, важливе слово «**сім'я**» *(family)* перетворюється на популярну форму «**сімей**» *(of families)*. Так само маленька «**миша**» *(mouse)* у родовому відмінку множини стає словом «**мишей**» *(of mice)*. Why do these surprising exceptions exist in our grammar? These are incredibly high-frequency words with ancient historical roots. The language preserved these irregular forms simply because people used them every single day for centuries. Тому вам не потрібно шукати тут логічне або просте правило. Ви повинні просто завчити ці популярні винятки напам'ять.

<!-- INJECT_ACTIVITY: match-up, Match singular Nom. nouns (I відміна) with their correct Genitive plural forms (e.g., книжка -> книжок, дочка -> дочок) -->
<!-- INJECT_ACTIVITY: fill-in, Form the Genitive plural for I відміна nouns, focusing on inserting the correct fleeting vowel (-о- or -е-) -->

## II відміна: -ів, нульове, -ей

Друга відміна має три різні закінчення для родового відмінка множини. Найпопулярніше закінчення для слів чоловічого роду — це довге закінчення **-ів**. Це базовий стандарт для іменників, які закінчуються на твердий приголосний. This is the absolute default rule for the vast majority of hard-stem masculine nouns. Наприклад, звичайне слово «**стіл**» *(table)* перетворюється на форму «**столів**» *(of tables)*. Сучасне слово «**комп'ютер**» *(computer)* легко стає словом «**комп'ютерів**» *(of computers)*. Це просте правило також чудово працює для людей. Слово «**брат**» *(brother)* має форму «**братів**» *(of brothers)*. А популярне слово «**студент**» *(student)* стає формою «**студентів**» *(of students)*. If you see a standard masculine noun ending in a hard consonant, just add -ів. Це найбезпечніший вибір для родового відмінка множини. Слово «**парк**» *(park)* стає словом «**парків**» *(of parks)*, а високий «**будинок**» *(building)* перетворюється на багато «**будинків**» *(of buildings)*.

Слова чоловічого роду з м'якою основою мають інший характер. Вони часто закінчуються на м'який знак або літеру -й. Ці слова зазвичай отримують м'яке закінчення **-ів** або **-їв**. Наприклад, слово «**учень**» *(pupil)* стає формою «**учнів**» *(of pupils)*. Слово «**водій**» *(driver)* перетворюється на красиву форму «**водіїв**» *(of drivers)*. Але є дуже важлива історична група слів. Certain masculine nouns with soft or hissing stems prefer the special ending -ей. Наприклад, слово «**гість**» *(guest)* у множині має дуже популярну форму «**гостей**» *(of guests)*. Слово «**кінь**» *(horse)* стає красивим словом «**коней**» *(of horses)*. Також ми маємо дуже важливе щоденне слово «**гроші**» *(money)*. Although "гроші" is always a plural word, its Genitive form is actually "грошей" *(of money)*. Це слово потрібно запам'ятати дуже добре, тому що ми використовуємо його постійно.

Тепер ми можемо поговорити про слова середнього роду. Іменники середнього роду із типовим закінченням -о працюють дуже цікаво. These nouns behave exactly like the feminine nouns from the first declension. Вони просто мають нульове закінчення у родовому відмінку множини. Наприклад, добре відоме слово «**слово**» *(word)* перетворюється на коротку форму «**слів**» *(of words)*. Солодке «**яблуко**» *(apple)* стає формою «**яблук**» *(of apples)*. Іноді тут також з'являється наш старий друг — вставний голосний. The fleeting vowel -о- or -е- often jumps in to break up difficult consonant clusters. Наприклад, слово «**вікно**» *(window)* має важку форму «вікн». Тому воно перетворюється на легку форму «**вікон**» *(of windows)*. We must clearly distinguish between neuter and masculine genders here. Чоловіче слово «телефон» має довгу форму «телефонів». Але середнє слово «**місто**» *(city)* має коротку форму «**міст**» *(of cities)*.

Іменники середнього роду із закінченням -е або -я мають м'яку основу. Ці слова можуть вільно обирати різні граматичні шляхи. Вони можуть отримувати стандартне чоловіче закінчення -ів або -їв. Наприклад, велике «**море**» *(sea)* стає довгою формою «**морів**» *(of seas)*. А сільське «**подвір'я**» *(yard)* стає красивим словом «**подвір'їв**» *(of yards)*. Але інші популярні слова середнього роду обирають нульове закінчення. A good rule of thumb is to look at double consonants. Якщо слово має подвійну приголосну перед останньою літерою, воно часто втрачає останню літеру. Наприклад, слово «**обличчя**» *(face)* стає короткою формою «**облич**» *(of faces)*. Важливе слово «**знання**» *(knowledge)* перетворюється на форму «**знань**» *(of knowledge)*. Це робить такі слова коротшими і легшими для швидкої розмови.

Українська мова має дуже цікаву спеціальну групу слів для людей. Вони позначають національність, походження або соціальний статус. Ці слова завжди закінчуються на типовий суфікс **-ин** в однині. Many common nouns use this historical suffix to indicate a person belonging to a larger group. Наприклад, місцевий житель міста Києва — це «**киянин**» *(Kyivan)*. Офіційний громадянин України — це «**громадянин**» *(citizen)*. А людина з Татарстану — це «**татарин**» *(Tatar)*. When these specific words form the Genitive plural, the entire -ин suffix mysteriously disappears from the word. Замість довгого закінчення вони раптово отримують нульове закінчення. Тому ми кажемо багато «**киян**» *(of Kyivans)*, мільйони «**громадян**» *(of citizens)* та багато «**татар**» *(of Tatars)*. Це правило стосується багатьох національностей та регіонів. 

Найважливіші слова в нашій мові часто є найбільш неправильними. Extremely high-frequency words often change their roots or endings unpredictably in the Genitive plural. Найкращий і найвідоміший приклад — це слово «**людина**» *(person)*. У родовому відмінку множини воно стає зовсім іншим словом «**людей**» *(of people)*. Маленька «**дитина**» *(child)* також повністю змінює свій корінь і перетворюється на популярну форму «**дітей**» *(of children)*. Деякі частини тіла також зберегли дуже давні історичні форми. Наприклад, наше ліве або праве «**око**» *(eye)* у множині завжди стає красивим словом «**очей**» *(of eyes)*. А слово «**вухо**» *(ear)* перетворюється на коротку і дивну форму «**вух**» *(of ears)*. Ці слова абсолютно не підкоряються стандартним правилам граматики. Їх потрібно просто запам'ятати і використовувати щодня під час розмов.

<!-- INJECT_ACTIVITY: true-false, Judge whether a given Gen.Pl. form is correct or incorrect (e.g., "братей" vs "братів", "містов" vs "міст"), 8 items -->

## Скільки чого? Кількість у житті

> — **Завідувач їдальні:** Добрий ранок. Давай перевіримо наш посуд. Скільки у нас «**тарілок**» *(of plates)* на кухні?
> — **Помічник:** У нас є «**двадцять**» *(twenty)* тарілок.
> — **Завідувач їдальні:** Добре. А скільки «**виделок**» *(of forks)*?
> — **Помічник:** Я бачу лише «**п'ять**» *(five)* виделок на столі.
> — **Завідувач їдальні:** Це дуже «**мало**» *(few)*! Нам потрібно більше. А скільки «**ложок**» *(of spoons)*?
> — **Помічник:** У нас є «**десять**» *(ten)* ложок.
> — **Завідувач їдальні:** Зрозуміло. А скільки чистих «**склянок**» *(of glasses)* стоїть там?
> — **Помічник:** Ой, у нас зовсім немає склянок! Усі склянки брудні.
> — **Завідувач їдальні:** Нам потрібно «**багато**» *(a lot)* чистого посуду просто зараз!
> — **Помічник:** Я зараз швидко все помию.

Ми постійно говоримо про кількість предметів, людей або продуктів. In Ukrainian, words that express quantity always demand a specific grammatical case. Слова «**скільки**» *(how many)*, «багато», «мало», «**кілька**» *(a few)* або «**декілька**» *(several)* вимагають родового відмінка множини. These quantity words are like magnets that pull the following noun into the Genitive plural. Наприклад, ми часто кажемо: «У мене багато друзів». Або ми можемо сказати: «На столі лежить кілька книжок». Якщо ви запитуєте ціну, ви кажете: «Скільки грошей це коштує?». The quantity word comes first, and the plural noun immediately follows it in its modified Genitive form. Це головне правило для розмов про будь-яку кількість у повсякденному житті.

Найцікавіша ситуація виникає, коли ми використовуємо точні цифри. There is a very important "Number Switch" rule in Ukrainian grammar. Після цифр «**два**» *(two)*, «**три**» *(three)* або «**чотири**» *(four)* ми використовуємо звичайний називний відмінок множини. Наприклад, ми кажемо «два столи» або «три книжки». But the moment you reach the number five, the grammar completely changes. Після цифри «п'ять» і для всіх більших чисел ми завжди використовуємо родовий відмінок множини. Тому ми говоримо «п'ять столів» або «десять книжок». Це дуже помітно, коли ми рахуємо «**гроші**» *(money)*. Ми кажемо «три гривні», але «десять гривень». Цей перехід від двох до п'яти — основа української математики.

Родовий відмінок множини також критично важливий для опису відсутності чогось. We already know that the word "немає" always requires the Genitive case. Це правило чудово працює і для множини. Якщо ви хочете купити квитки, але їх уже продали, касир скаже: «Вибачте, немає місць». Якщо у вас порожній гаманець, ви кажете: «У мене зараз немає грошей». This case is also widely used for general descriptions of spaces or groups. Наприклад, ви можете описувати кімнату: «У цій кімнаті немає вікон, але тут багато столів». Або ви розповідаєте про родину: «У брата немає дітей, але є багато собак». Ми використовуємо цю граматичну конструкцію щодня.

Давайте подивимося, як ці правила працюють разом на місцевому ринку під час покупок:

> — **Покупець:** Добрий день. Дайте мені, будь ласка, десять яблук і два кілограми помідорів.
> — **Продавець:** Прошу, ось ваші красиві яблука. Щось ще бажаєте купити?
> — **Покупець:** Так, дайте ще три огірки.
> — **Продавець:** Добре. З вас сьогодні рівно «**п'ятдесят**» *(fifty)* гривень, будь ласка.
> — **Покупець:** Ось мої гроші, дякую вам.

<!-- INJECT_ACTIVITY: quiz, Choose the correct Gen.Pl. form in quantity expressions (e.g., багато (студент/студенти/студентів)), 8 items -->

## Підсумок

Родовий відмінок множини — це дійсно найскладніша тема. The Genitive plural is truly the most difficult topic. But it relies on three main «**стовпи**» *(pillars)*. Перший стовп — це «**нульове закінчення**» *(zero ending)*. Воно працює для більшості слів жіночого та середнього роду. Наприклад, ми кажемо багато «**книг**» *(of books)* або кілька «**вікон**» *(of windows)*. Другий стовп — це закінчення «-ів» або «-їв». We use this ending for most masculine words and some soft neuter words. Ми купуємо п'ять «**столів**» *(of tables)* або бачимо багато «**морів**» *(of seas)*. Третій стовп — це закінчення «-ей». Це закінчення мають специфічні слова та часті винятки. Ми чекаємо багато «**гостей**» *(of guests)* або не спимо п'ять «**ночей**» *(of nights)*.

Тепер перевірте себе:
* Чи можете ви утворити родовий відмінок множини для слова «**сестра**» *(sister)*? Правильно, це «**сестер**» *(of sisters)*.
* Чи знаєте ви правильне закінчення для слова «**гість**» *(guest)*? Так, це закінчення «-ей».
* Що відбувається після слова «багато»? Наступне слово завжди стоїть у родовому відмінку множини.
* А який відмінок ми використовуємо після цифри «**сім**» *(seven)*? Ми також використовуємо родовий відмінок множини!

**Deterministic word count: 2582 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 616 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Києва — NOT IN VESUM
  ✗ Татарстану — NOT IN VESUM
  ✗ братей — NOT IN VESUM
  ✗ вікн — NOT IN VESUM
  ✗ казк — NOT IN VESUM
  ✗ містов — NOT IN VESUM
  ✗ школ — NOT IN VESUM

All 616 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
