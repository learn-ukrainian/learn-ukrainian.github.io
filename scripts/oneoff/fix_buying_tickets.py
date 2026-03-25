import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: "Мені, будь ласка"
text = text.replace('or «Мені, будь ласка» (To me, please)', 'or «Я хочу» (I want)')

# Fix 2: Replace complex translations with simple ones
old_1 = 'Розуміння географії та інфраструктури України — це перший крок до будь-якої успішної подорожі. Країна величезна, тому внутрішні подорожі — це серйозна логістична подія, а не просто швидка поїздка.'
new_1 = 'Географія України дуже цікава. Це велика країна. Внутрішні подорожі — це велика подія. Вони займають багато часу.'
text = text.replace(old_1, new_1)

old_2 = 'Кожне велике українське місто має специфічну інфраструктуру для транспорту. Термінологія для цих місць точна, і знати, куди саме йти, вкрай важливо, щоб випадково не пропустити свій рейс. Дуже поширена помилка для тих, хто вивчає мову, — прибути не на ту станцію.'
new_2 = 'Кожне місто має свою інфраструктуру. Вокзали мають точні назви. Ви маєте знати правильну назву. Туристи часто роблять помилки.'
text = text.replace(old_2, new_2)

old_3 = 'Тепер, коли ми точно визначили наш пункт призначення та обраний вид транспорту, ми повинні успішно здійснити фінансову операцію. Купівля квитка вимагає точного вказування кількості, напрямку поїздки, формату та бажаного класу комфорту.'
new_3 = 'Ми знаємо наш маршрут. Тепер ми купуємо квитки. Касир хоче знати деталі. Ви говорите кількість і напрямок.'
text = text.replace(old_3, new_3)

old_4 = 'Фізичне місце, де ви купуєте традиційні паперові квитки в будівлі вокзалу, називається **ка́са** (ticket office). Історично купівля квитка означала терпляче стояння в довгій, повільній черзі біля каси. Однак сучасні пасажирські перевезення в Україні дуже цифровізовані. Сьогодні переважна більшість місцевих жителів використовує **електро́нний квито́к** (electronic ticket), збережений на їхніх мобільних пристроях.'
new_4 = 'Ви купуєте квитки тут. Це місце — **ка́са** (ticket office). Раніше люди стояли в довгих чергах. Сьогодні українці люблять цифрові технології. Вони часто мають **електро́нний квито́к** (electronic ticket) у смартфоні.'
text = text.replace(old_4, new_4)

old_5 = 'Ваш квиток надійно заброньовано, і ви нарешті прибули на вокзал. У цьому розділі наведено необхідний словниковий запас, щоб орієнтуватися у фізичній інфраструктурі вокзалу, знаходити своє місце та розуміти глибокі культурні ритуали самої поїздки.'
new_5 = 'Ви маєте квиток. Ви прибули на вокзал. Тут ми вивчаємо нові слова. Ви шукаєте платформу і вагон. Ви також вивчаєте культурні традиції поїзда.'
text = text.replace(old_5, new_5)

# More translations to boost immersion (Translating English to Simple Ukrainian)
# Intro
old_intro = 'Traveling across the vast landscapes of Ukraine is a fundamental part of experiencing the country. Whether you want to admire the historic architecture of Lviv, feel the sea breeze in Odesa, or hike the trails in the Carpathians, you absolutely need to know how to move between regions. In this lesson, we will learn how to navigate busy transport hubs, choose your ideal vehicle, and confidently state your destination at the ticket office.'
new_intro = 'Подорожі Україною — це дуже цікавий досвід. Ви можете дивитися архітектуру міста Львів. Ви можете відчувати море біля міста Одеса. Ви можете гуляти в горах. Ви маєте знати транспортні слова. У цьому уроці ми вивчаємо вокзали. Ми також вибираємо транспорт. Ми купуємо квитки.'
text = text.replace(old_intro, new_intro)

# Section: Напрямок руху: правило «до»
old_dir = 'When you purchase a ticket, read a schedule board, or explain your itinerary to a friend, you must express direction. You need to articulate exactly where you are going. In Ukrainian, when we indicate travel toward a specific city or town, we utilize the preposition **до** (to/until) followed by the Genitive case form of the city name.'
new_dir = 'Ви купуєте квиток. Ви читаєте розклад. Ви говорите напрямок поїздки. В українській мові ми використовуємо прийменник **до** (to). Ми також використовуємо родовий відмінок.'
text = text.replace(old_dir, new_dir)

old_dir_2 = 'At the beginner A1 level, you do not need to memorize the entire complex grammatical system of the Genitive case. Instead, pedagogically treat these extremely common destinations as fixed lexical chunks. Generally, most city names ending in a hard consonant simply add an "-а", while those ending in "-а" change their ending to "-и".'
new_dir_2 = 'На рівні А1 вам не треба вчити всі правила. Просто запам\'ятайте ці слова як блоки. Назви міст на приголосний додають "-а". Назви на "-а" змінюють кінець на "-и".'
text = text.replace(old_dir_2, new_dir_2)

# Section: Орієнтація на вокзалі: платформи та вагони
old_plat = 'Major transport hubs can be intensely overwhelming, with dozens of active tracks and multiple long trains arriving simultaneously. You must precisely know how to ask for your departure location. The word for a single train carriage is **ваго́н**. You will regularly utilize the Prepositional case to ask about location: «на платформі», «у вагоні».'
new_plat = 'Великі вокзали можуть лякати. Там є багато колій і поїздів. Ви маєте знати місце відправлення. Одне слово для частини поїзда — це **ваго́н**. Ми використовуємо місцевий відмінок: «на платформі», «у вагоні».'
text = text.replace(old_plat, new_plat)

# Section: Вибір і розташування місця
old_seat = 'Your physical ticket or digital screen will clearly indicate your specific **мі́сце** (seat/place). In the specific context of night trains, this word refers to a flat sleeping bed. Passengers hold strong, established preferences regarding where they sleep, and the location determines certain rigid etiquette rules.'
new_seat = 'Ваш квиток має конкретне **мі́сце** (seat/place). У нічному поїзді це місце для сну. Пасажири мають свої улюблені місця. Місце також має свої правила.'
text = text.replace(old_seat, new_seat)

# Section: Контроль часу
old_time = 'Precise time management is critical in the railway ecosystem. You will encounter the word **розкла́д** (schedule) constantly on glowing digital boards and large printed tables. To inquire about timing, we rely on very precise question structures.'
new_time = 'Контроль часу дуже важливий. Ви часто бачите слово **розкла́д** (schedule) на вокзалі. Ми використовуємо точні питання для часу.'
text = text.replace(old_time, new_time)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'w', encoding='utf-8') as f:
    f.write(text)

