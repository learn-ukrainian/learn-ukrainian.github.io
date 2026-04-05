<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-genitive.yaml` file for module **33: Скільки?** (a2).

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

- focus: Form the Genitive plural from given nouns (mixed відміни), inserting fleeting
    vowels where needed
  items: 8
  type: fill-in
- focus: Choose the correct Gen.Pl. form in quantity expressions (багато ___, п'ять
    ___)
  items: 8
  type: quiz
- focus: Match singular nouns with their correct Genitive plural forms
  items: 8
  type: match-up
- focus: Judge whether a given Gen.Pl. form is correct or incorrect (common errors
    like книгів instead of книг)
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- вставний голосний (fleeting vowel)
- виняток (exception)
- десяток (a dozen, ten-unit)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому родовий множини такий складний?

Українська мова має сім відмінків. Родовий відмінок множини — це справжнє випробування для студентів. Називний відмінок множини дуже простий і зрозумілий. Ми просто додаємо закінчення **-и** *(ending -y)* або **-і** *(ending -i)*. Наприклад, ми кажемо «столи», «книги», «дні». Але **родовий відмінок** *(genitive case)* працює зовсім інакше. The Genitive plural is often considered the "final boss" of Ukrainian noun declension. It is the most unpredictable case in the plural form. Instead of learning one simple rule, you must master three completely different grammatical patterns. These patterns include the ending **-ів** *(ending -iv)*, the ending **-ей** *(ending -ey)*, and the **нульове закінчення** *(zero ending)*. In addition to these unpredictable endings, words often change their internal vowels to maintain a nice rhythm. Це робить цей відмінок найскладнішим правилом.

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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-genitive
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

**Level: A2 (Module 33/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

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
