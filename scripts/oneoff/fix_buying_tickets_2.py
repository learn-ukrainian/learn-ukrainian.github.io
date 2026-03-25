import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Підкажіть, коли поїзд прибуває в гори?', 'Коли поїзд прибуває в гори?')
text = text.replace('В українській мові ми використовуємо прийменник', 'Тут ми використовуємо прийменник')
text = text.replace('Сьогодні українці люблять цифрові технології.', 'Сьогодні українці часто використовують смартфони.')
text = text.replace('На рівні А1 вам не треба вчити всі правила.', 'На рівні А1 студенти не вчать всі правила.')

# Robotic
text = text.replace('Ви можете дивитися архітектуру міста Львів. Ви можете відчувати море біля міста Одеса. Ви можете гуляти в горах.', 'Там є красива архітектура міста Львів. Також є море біля міста Одеса. Люди люблять гуляти в горах.')

# Translate Summary
old_summary = '''Mastering travel vocabulary unlocks the entire geography of the country. In this comprehensive lesson, you successfully acquired the essential terms to legally purchase a ticket, orient yourself within massive stations, and appreciate the unique cultural nuances of Ukrainian railways. You now clearly understand that a **вокза́л** is dedicated specifically to trains, whereas an **автовокза́л** serves buses. You learned the strict grammatical necessity of asking for **оди́н квито́к** with the correct masculine agreement and to accurately express your final destination utilizing the preposition **до** instead of the erroneous «в». You can confidently choose between the quiet privacy of a **купе́** and the engaging social atmosphere of a **плацка́рт**, explicitly request a convenient **ни́жнє мі́сце**, and actively participate in the tradition of ordering tea served in an iconic metal **підстака́нник**. Most importantly, you are fully prepared to present an **електро́нний квито́к** on a modern smartphone application, seamlessly blending deep historical tradition with contemporary digital convenience. Щасливої доро́ги!'''

new_summary = '''Знати слова для подорожей — це дуже важливо. На цьому уроці ми вивчили багато нових слів. Ми знаємо, як купувати квиток. Ми знаємо, як шукати поїзд. Ми розуміємо культуру українських подорожей.
Слово **вокза́л** — це місце для поїздів. Слово **автовокза́л** — це місце для автобусів.
Тепер ми знаємо граматику. Ми просимо **оди́н квито́к** (masculine form). Ми використовуємо прийменник **до** для напрямку. Ми не використовуємо прийменник «в».
Ми розуміємо різницю між класами поїзда. Ми можемо вибрати приватне **купе́**. Або ми можемо вибрати соціальний **плацка́рт**. Ми знаємо, як просити зручне **ни́жнє мі́сце**.
Також ми знаємо про чай. Ми можемо пити чай. Провідник приносить чай у традиційному металевому стакані. Цей стакан називається **підстака́нник**.
Сьогодні всі використовують технології. Тому ми знаємо про **електро́нний квито́к**. Його легко показати на смартфоні.
Щасливої доро́ги! (Have a safe trip!)'''

text = text.replace(old_summary, new_summary)

# Translate Culture 1
old_cult_1 = '''> [!culture] **The Rhythmic Soundtrack of the Journey**
> The soft, rhythmic metallic clinking of a small spoon against the glass wall inside a «підстаканник», perfectly synchronized with the heavy rocking of the train, is the definitive sensory experience of travel in Ukraine. Ordering this tea from the «провідник» is not merely about quenching thirst; this ritual acts as a vital psychological threshold that marks the official beginning of the relaxation phase of your long journey.'''

new_cult_1 = '''> [!culture] **Звуки подорожі (Sounds of the journey)**
> Звук ложки у склянці — це класичний звук поїзда. Металевий **підстаканник** робить цей звук особливим. Цей звук і рух поїзда — це справжній український досвід. Ви замовляєте чай у провідника. Це не просто напій. Цей ритуал означає початок відпочинку. Ваша довга подорож починається.'''

text = text.replace(old_cult_1, new_cult_1)

# Translate Culture 2
old_cult_2 = '''> [!culture] **The Rich Sociology of Platzkart**
> Do not let the open, unshielded architecture of a «плацкарт» intimidate you. This space serves as a deeply authentic, vibrant cultural environment rather than just a cheap ticket option. Passengers quickly change into comfortable domestic clothes, generously share homemade food like roasted chicken, boiled eggs, and thick sandwiches, and engage in long, philosophical conversations with complete strangers. This experience represents a highly communal journey that effectively highlights the open, egalitarian nature of Ukrainian society.'''

new_cult_2 = '''> [!culture] **Соціологія плацкарта (Sociology of Platzkart)**
> Відкритий **плацкарт** — це не страшно. Це дуже автентичне культурне місце. Це не просто дешевий квиток. Пасажири одягають зручний домашній одяг. Вони діляться домашньою їжею. Наприклад, вони їдять курку, яйця та бутерброди. Вони довго говорять з іншими людьми. Це дуже соціальна подорож. Вона показує відкритий характер українців.'''

text = text.replace(old_cult_2, new_cult_2)

# Fix sub clause
text = text.replace('Підкажіть, коли поїзд прибуває в гори?', 'Коли поїзд прибуває в гори?')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md', 'w', encoding='utf-8') as f:
    f.write(text)

