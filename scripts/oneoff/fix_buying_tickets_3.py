import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Tip
old_tip = '''> [!tip] **Taxis and Station Terminology**
> If you enter a local taxi and simply say «на вокзал» (to the station), the driver will automatically, without question, take you directly to the railway station. If your purchased ticket is actually for a bus, you must be explicit and clearly state «на автовокзал». This simple vocabulary distinction saves many foreign travelers from missing their scheduled departures.'''
new_tip = '''> [!tip] **Таксі та вокзали (Taxis and stations)**
> Ви сідаєте в таксі. Ви говорите: «на вокзал». Водій автоматично їде на залізничну станцію. Водій не має питань. Але ваш квиток може бути на автобус. Тоді ви маєте сказати: «на автовокзал». Це дуже важливе правило. Воно допомагає туристам встигнути на рейс.'''
text = text.replace(old_tip, new_tip)

# Warning In/Into
old_warn1 = '''> [!warning] **The "In/Into" Translation Trap**
> English speakers instinctively want to translate the concept of "traveling to" using the preposition «в» (in/into) because they logically conceptualize entering the physical city limits. This mental translation results in phrases like «Я їду в Львів», which immediately sound unnatural to a native ear. Always use «до» for geographical destinations: «Я їду до Львова». This represents the natural, correct Ukrainian grammatical pattern for movement toward a location.'''
new_warn1 = '''> [!warning] **Правило прийменників (The rule of prepositions)**
> Англомовні люди часто роблять помилку. Вони хочуть перекласти "traveling to" словом «в». Наприклад, вони кажуть: «Я їду в Львів». Це звучить дуже неприродно для українців. Ви завжди маєте використовувати слово «до» для міст. Правильна фраза: «Я їду до Львова». Це природна і правильна українська граматика для напрямку.'''
text = text.replace(old_warn1, new_warn1)

# Warning Gender
old_warn2 = '''> [!warning] **Gender Agreement Alert**
> Because language learners frequently memorize «одна» (one, feminine) first as a default counting word, they often mistakenly say «одна квиток» at the counter. This is a highly noticeable grammatical error because «квиток» is decidedly masculine. Train your ear to always link these two specific words together naturally: «оди́н квито́к». Never use the feminine numerical form here.'''
new_warn2 = '''> [!warning] **Увага на рід (Gender alert)**
> Студенти часто вчать слово «одна» першим. Тому вони часто говорять касиру: «одна квиток». Це дуже помітна помилка. Слово «квиток» — це чоловічий рід. Ви маєте тренувати свій слух. Завжди використовуйте правильну форму разом: «оди́н квито́к». Ніколи не використовуйте жіночий рід тут.'''
text = text.replace(old_warn2, new_warn2)

# Fact Digital
old_fact = '''> [!fact] **The Rapid Digital Transformation**
> Ukraine boasts one of the most rapid and successful adoptions of digital public services anywhere in Europe. The massive societal shift from queueing nervously at a traditional «каса» to instantly generating an «електронний квиток» completely transformed the travel experience. Traditional paper tickets are now primarily purchased only by elderly passengers who prefer cash transactions, or they are kept as physical paper souvenirs by visiting tourists.'''
new_fact = '''> [!fact] **Цифрова революція (Digital transformation)**
> Україна має дуже швидкий цифровий розвиток. Раніше всі стояли в довгих чергах біля каси. Тепер люди генерують **електро́нний квито́к** дуже швидко. Це повністю змінило досвід подорожей. Сьогодні паперові квитки купують дуже рідко. Їх купують старі люди, які люблять готівку. Або туристи купують їх як сувеніри.'''
text = text.replace(old_fact, new_fact)

# Observe Etiquette
old_obs = '''> [!observe] **The Strict Etiquette of the Berths**
> The unwritten social contract of the train dictates specific behavior regarding seats. If you successfully occupy a «нижнє місце», it is considered mandatory politeness to gracefully allow the passenger occupying the «верхнє місце» to sit on the edge of your bed during daylight hours. They absolutely need this access to eat their meals at the shared table or simply to socialize. The lower space is treated as shared community territory until it is officially time to sleep.'''
new_obs = '''> [!observe] **Етикет місць (The etiquette of berths)**
> Поїзд має свій соціальний етикет. Ви маєте **ни́жнє мі́сце**. Вдень ви маєте дозволити пасажиру зверху сидіти на вашому ліжку. Це правило ввічливості. Пасажир зверху хоче їсти за спільним столом. Або він просто хоче говорити з людьми. Нижнє місце — це спільна територія вдень. Вночі це ваше приватне місце для сну.'''
text = text.replace(old_obs, new_obs)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'w', encoding='utf-8') as f:
    f.write(text)

