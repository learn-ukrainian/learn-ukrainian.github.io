import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-i-things.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1
content = content.replace(
    "> Знахідний відмінок — це двигун ваших речень. Він показує, куди спрямована дія, дозволяючи вам взаємодіяти зі світом. Без нього ваші слова залишаються ізольованими об'єктами; з ним ви починаєте будувати справжні живі історії.\n>\n> The accusative case is the engine of your sentences. It shows where an action is directed, allowing you to interact with the world around you. Without it, your words remain isolated objects; with it, you begin to build real, living stories.",
    "> Знахідний відмінок — це двигун ваших речень. Він показує напрямок дії. Ви активно взаємодієте з навколишнім світом. Ваші слова без цього відмінка просто залишаються ізольованими об'єктами. Цей відмінок дуже ефективно будує справжні живі історії.\n>\n> The accusative case is the engine of your sentences. It shows the direction of the action. You actively interact with the surrounding world. Your words without this case simply remain isolated objects. This case very effectively builds real living stories."
)

# 3
content = content.replace(
    "Українська мова працює зовсім інакше. Ми використовуємо спеціальні закінчення слів. Ці закінчення показують роль кожного слова. Це дає нам неймовірну гнучкість речень.\nEnglish has a very strict word order. Ukrainian works completely differently. We use special word endings. These endings show the role of each word. This gives us incredible sentence flexibility.",
    "Українська мова працює зовсім інакше. Ми використовуємо спеціальні закінчення слів. Ці закінчення показують роль кожного слова. Ми маємо неймовірну гнучкість речень.\nEnglish has a very strict word order. Ukrainian works completely differently. We use special word endings. These endings show the role of each word. We have incredible sentence flexibility."
)

# 4
content = content.replace(
    "Слова середнього роду закінчуються на літери «о» або «е». Вони ніколи не змінюються у знахідному відмінку. Ця стабільність дає нам можливість трохи розслабитися. Ми можемо безпечно використовувати їхню словникову форму.\nNeuter words end in the letters \"o\" or \"e\". They never change in the accusative case. This stability gives us an opportunity to relax a bit. We can safely use their dictionary form.",
    "Слова середнього роду закінчуються на літери «о» або «е». Вони ніколи не змінюються у знахідному відмінку. Через цю стабільність ми можемо трохи розслабитися. Ми можемо безпечно використовувати їхню словникову форму.\nNeuter words end in the letters \"o\" or \"e\". They never change in the accusative case. Because of this stability we can relax a bit. We can safely use their dictionary form."
)

# 5
content = content.replace(
    "### Дієслова-тригери: Хто керує відмінком?\nДеякі дієслова автоматично вимагають знахідного відмінка. Ми називаємо такі слова дієсловами-тригерами. Вони показують пряму фізичну або розумову дію. Коли ви чуєте ці слова, готуйтеся швидко змінювати закінчення.\nSome verbs automatically require the accusative case. We call such words trigger verbs. They show direct physical or mental action. When you hear these words, prepare to quickly change the endings.",
    "### Слова-тригери: Хто керує відмінком?\nДеякі слова автоматично вимагають знахідного відмінка. Ми називаємо такі слова тригерами. Вони показують пряму фізичну або розумову дію. Ви чуєте ці слова. Тоді ви готуєтеся швидко змінювати закінчення.\nSome words automatically require the accusative case. We call such words triggers. They show direct physical or mental action. You hear these words. Then you prepare to quickly change the endings."
)

# 6
content = content.replace(
    "Дієслово «бачити» — це ваш головний інструмент візуального сприйняття. Кожного разу, коли ви розплющуєте очі, ви створюєте об'єкти дії.",
    "Слово «бачити» — це головний інструмент візуального сприйняття. Ви розплющуєте очі і одразу створюєте об'єкти дії."
)
content = content.replace(
    "The verb \"to see\" is your main tool of visual perception. Every time you open your eyes, you create objects of action.",
    "The word \"to see\" is the main tool of visual perception. You open your eyes and immediately create objects of action."
)

# 7
content = content.replace(
    "Дієслово «мати» показує ваше особисте володіння чимось. Це дуже сильне та часте слово. В українській мові ми використовуємо його для абстрактних речей також.",
    "Слово «мати» показує ваше особисте володіння чимось. Це дуже сильне та часте слово. Ми використовуємо це слово для абстрактних речей також."
)
content = content.replace(
    "The verb \"to have\" shows your personal possession of something. It is a very strong and frequent word. In the Ukrainian language, we use it for abstract things too.",
    "The word \"to have\" shows your personal possession of something. It is a very strong and frequent word. We use this word for abstract things too."
)

# 8
content = content.replace(
    "Це дієслово описує дуже конкретну фізичну дію.",
    "Це слово описує дуже конкретну фізичну дію."
)
content = content.replace(
    "This verb describes a very concrete physical action.",
    "This word describes a very concrete physical action."
)

# 9
content = content.replace(
    "Ваш мозок завжди активно шукає найпростіший шлях. Коли ви вчите нове слово, мозок зберігає його як фіксовану картинку. Він хоче використовувати цю ж картинку абсолютно всюди.",
    "Ваш мозок завжди активно шукає найпростіший шлях. Ви вчите нове слово. Мозок зберігає його як фіксовану картинку. Він хоче використовувати цю ж картинку абсолютно всюди."
)
content = content.replace(
    "Your brain always actively looks for the easiest path. When you learn a new word, the brain saves it as a fixed picture. It wants to use this same picture absolutely everywhere.",
    "Your brain always actively looks for the easiest path. You learn a new word. The brain saves it as a fixed picture. It wants to use this same picture absolutely everywhere."
)

# 10
content = content.replace(
    "Вивчення окремих ізольованих слів часто займає надто багато часу. Набагато ефективніше вивчати цілі сталі словосполучення разом. Це блоки слів, які дуже природно існують разом. Вони допомагають вам говорити набагато швидше.\nLearning individual isolated words often takes too much time. It is much more effective to study entire fixed collocations together. These are blocks of words that very naturally exist together. They help you speak much faster.",
    "Вивчення окремих ізольованих слів часто займає надто багато часу. Набагато ефективніше вивчати цілі сталі словосполучення разом. Це великі блоки слів. Вони дуже природно існують разом. Так ви можете говорити набагато швидше.\nLearning individual isolated words often takes too much time. It is much more effective to study entire fixed collocations together. These are large blocks of words. They very naturally exist together. This way you can speak much faster."
)

# 11
content = content.replace(
    "> Коли ви вчите нове дієслово, одразу вчіть його зі своїм об'єктом. Не вчіть просто порознє «брати».",
    "> Ви вчите нове слово. Завжди одразу вчіть його зі своїм об'єктом. Не вчіть просто порознє «брати»."
)
content = content.replace(
    "> When you learn a new verb, immediately learn it with its object. Do not just learn an empty \"to take\".",
    "> You learn a new word. Always immediately learn it with its object. Do not just learn an empty \"to take\"."
)

# 12
content = content.replace(
    "Щоб завжди говорити правильно, вам потрібен надійний автоматичний рефлекс. Ви не повинні довго думати про граматичні правила під час жвавої розмови. Ви повинні просто інтуїтивно відчувати правильну граматичну форму. Ми досягаємо цього через постійне багаторазове повторення.\nTo always speak correctly, you need a reliable automatic reflex. You should not think long about grammatical rules during a lively conversation. You should simply intuitively feel the correct grammatical form. We achieve this through constant multiple repetition.",
    "Ви хочете завжди говорити правильно. Ви повинні мати надійний автоматичний рефлекс. Ви не повинні довго думати про граматику під час розмови. Ви повинні просто інтуїтивно відчувати правильну граматичну форму. Ми досягаємо цього через постійне багаторазове повторення.\nYou want to always speak correctly. You must have a reliable automatic reflex. You should not think long about grammar during a conversation. You should simply intuitively feel the correct grammatical form. We achieve this through constant multiple repetition."
)

# 13
content = content.replace(
    "Давайте ще раз попрактикуємо цей плавний перехід від пасивної ідеї до активної дії.",
    "Давайте ще раз попрактикуємо цей плавний перехід від ідеї до дії."
)
content = content.replace(
    "Let's practice again this smooth transition from passive idea to active action.",
    "Let's practice again this smooth transition from idea to action."
)

# 14
content = content.replace(
    "В абсолютно кожному українському супермаркеті ви обов'язково почуєте одне стандартне питання. Кожен касир завжди неодмінно вас запитає: «Пакет потрібен?»",
    "У кожному українському супермаркеті ви почуєте одне стандартне питання. Кожен касир завжди неодмінно запитає: «Пакет потрібен?»"
)
content = content.replace(
    "In absolutely every Ukrainian supermarket you will definitely hear one standard question. Every cashier will always inevitably ask you: \"Do you need a bag?\"",
    "In every Ukrainian supermarket you will hear one standard question. Every cashier will always inevitably ask: \"Do you need a bag?\""
)

# 15
content = content.replace(
    "Слово «пакет» — це звичайний іменник чоловічого роду.",
    "Слово «пакет» — це типове слово чоловічого роду."
)
content = content.replace(
    "The word \"bag\" is a regular masculine noun.",
    "The word \"bag\" is a typical word of the masculine gender."
)

# 16
content = content.replace(
    "**Касир:** Добрий вечір. Пакет потрібен вам сьогодні? (Good evening. Do you need a bag today?)",
    "**Касир:** Добрий вечір. Ви берете пакет сьогодні? (Good evening. Are you taking a bag today?)"
)

# 17
content = content.replace(
    "> В давній українській культурі свіжий хліб має дуже особливе, майже сакральне значення.",
    "> У давній українській культурі свіжий хліб має дуже особливе значення."
)
content = content.replace(
    "> In ancient Ukrainian culture fresh bread has a very special, almost sacred meaning.",
    "> In ancient Ukrainian culture fresh bread has a very special meaning."
)

# 18
content = content.replace(
    "Спочатку мені категорично потрібен свіжий хліб.",
    "Спочатку я категорично хочу свіжий хліб."
)
content = content.replace(
    "First I categorically need fresh bread.",
    "First I categorically want fresh bread."
)

# 19
content = content.replace(
    "Ми детально навчилися працювати зі складним знахідним відмінком для звичайних неістот.",
    "Ми навчилися працювати зі знахідним відмінком для звичайних неістот."
)
content = content.replace(
    "We detailedly learned to work with the complex accusative case for regular inanimate objects.",
    "We learned to work with the accusative case for regular inanimate objects."
)

# Add extra examples for immersion
content = content.replace(
    "Я бачу гарне вікно поруч.\nI see a beautiful window nearby.",
    "Я бачу гарне вікно поруч. Я бачу новий комп'ютер.\nI see a beautiful window nearby. I see a new computer."
)

content = content.replace(
    "Тут є новий **паке́т**. Я беру новий **пакет**.\nHere is a new bag. I take a new bag.",
    "Тут є новий **паке́т**. Я беру новий **пакет**.\nHere is a new bag. I take a new bag.\n\nТут лежить старий **зо́шит**. Я бачу старий **зошит**.\nHere lies an old notebook. I see an old notebook."
)

content = content.replace(
    "Я чую твій тихий голос.\nI hear your quiet voice.",
    "Я чую твій тихий голос. Я чую цей звук.\nI hear your quiet voice. I hear this sound."
)

content = content.replace(
    "Я хочу новий телефон сьогодні.\nI want a new phone today.",
    "Я хочу новий телефон сьогодні. Я хочу цей зошит.\nI want a new phone today. I want this notebook."
)

# Remove 'дієслово' instances
content = content.replace("дієслово «бачити»", "слово «бачити»")
content = content.replace("Дієслово «бачити»", "Слово «бачити»")
content = content.replace("дієслово «мати»", "слово «мати»")
content = content.replace("Дієслово «мати»", "Слово «мати»")
content = content.replace("Це дієслово описує", "Це слово описує")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement complete.")
