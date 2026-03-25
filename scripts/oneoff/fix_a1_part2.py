import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/a1-final-exam.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix grammatical issues introduced or missed
content = content.replace("Вони чітко показують нам, що потрібно більше практикувати в майбутньому.", "Вони чітко показують нові завдання для практики.")
content = content.replace("Коли вам потрібно слухати аудіо, зосередьтеся на знайомих дієсловах та іменниках.", "Слухайте аудіо уважно. Зосередьтеся на знайомих дієсловах та іменниках.")
content = content.replace("Коли вам потрібно **слухати** аудіо, зосередьтеся на знайомих дієсловах та іменниках.", "Уважно **слухайте** аудіо. Зосередьтеся на знайомих дієсловах та іменниках.")
content = content.replace("Коли вам потрібно **писати**, згадайте базові правила.", "Під час письма згадайте базові правила.")
content = content.replace("Коли вам потрібно писати, згадайте базові правила.", "Під час письма згадайте базові правила.")

content = content.replace("Перед початком тесту зробіть глибокий вдих.", "До початку тесту зробіть глибокий вдих.")
content = content.replace("Фінальний тест структурований, щоб комплексно оцінити ваші комунікативні навички.", "Цей фінальний тест комплексно оцінює ваші комунікативні навички.")
content = content.replace("Ми хочемо бачити, як ви використовуєте мову в житті.", "Ми хочемо бачити ваші навички в реальному житті.")

content = content.replace("Щоб гарантувати повне розуміння, всі інструкції надаються англійською мовою.", "Усі інструкції надаються англійською мовою для повного розуміння.")
content = content.replace("Якщо ви робите **помилку** під час тесту, не панікуйте.", "Робити **помилку** під час тесту — це абсолютно нормально.")
content = content.replace("Не хвилюйтеся, якщо ви не відразу впізнаєте кожне слово.", "Не хвилюйтеся про незнайомі нові слова.")
content = content.replace("в словнику", "у словнику")

content = content.replace("Ваша **оцінка** відображає, наскільки добре ви можете передати своє повідомлення.", "Ваша **оцінка** показує ваш рівень комунікації.")

# Add more bilingual replacements to boost immersion from 25.9% to 35%
rep6 = """In Ukrainian, grammatical harmony and structural agreement are fundamental principles. An adjective cannot exist independently; it must perfectly mirror the noun it describes. This strict rule means that the gender (masculine, feminine, or neuter), the number (singular or plural), and the case of the adjective must perfectly match the corresponding noun. Failing to match these elements creates sentences that sound disjointed to native speakers."""
rep6_bil = """Граматична гармонія та узгодження — це дуже фундаментальні принципи. Прикметник не може існувати самостійно. Він має точно відображати іменник. Це правило означає єдність форми. Рід, число та відмінок прикметника повинні відповідати іменнику. Ці елементи створюють дуже правильні красиві речення.
*(In Ukrainian, grammatical harmony and structural agreement are fundamental principles. An adjective cannot exist independently; it must perfectly mirror the noun it describes. This strict rule means that the gender (masculine, feminine, or neuter), the number (singular or plural), and the case of the adjective must perfectly match the corresponding noun. Failing to match these elements creates sentences that sound disjointed to native speakers.)*"""
content = content.replace(rep6, rep6_bil)

rep7 = """Verbs are the active engine of every single sentence. In the present tense, Ukrainian verbs are categorized into two main conjugation patterns: Class I and Class II. Class I verbs typically end in "-ати" or "-яти" in their infinitive dictionary form. Their endings have the vowels "е" or "є". Class II verbs usually end in "-ити" or "-іти". They use the vowels "и" or "ї" instead. Let's thoroughly compare them."""
rep7_bil = """Дієслова — це активний двигун кожного речення. У теперішньому часі українські дієслова мають два основні класи. Дієслова першого класу зазвичай мають форму на "-ати" або "-яти". Їхні закінчення мають дуже характерні голосні "е" або "є". Дієслова другого класу зазвичай мають форму на "-ити" або "-іти". Вони використовують інші голосні "и" або "ї". Давайте уважно порівняємо їх.
*(Verbs are the active engine of every single sentence. In the present tense, Ukrainian verbs are categorized into two main conjugation patterns: Class I and Class II. Class I verbs typically end in "-ати" or "-яти" in their infinitive dictionary form. Their endings have the vowels "е" or "є". Class II verbs usually end in "-ити" or "-іти". They use the vowels "и" or "ї" instead. Let's thoroughly compare them.)*"""
content = content.replace(rep7, rep7_bil)

rep8 = """Kyiv is not just the modern administrative center; it is the true historical heart of Ukraine. Founded deep in the 5th century, it is recognized as one of the oldest and most historically significant cities in Eastern Europe. Its deep historical status makes it an endlessly fascinating place to explore linguistically. The sprawling city is defined by its stunning geography, particularly the wide and majestic Dnipro River that gracefully divides the city into the right and left banks. When you read assessment texts about Kyiv, pay close attention to the cultural symbols. The blooming **кашта́н** (chestnut tree) is the iconic, beloved symbol of Kyiv. Every May, the city dramatically transforms into a magnificent sea of white and pink chestnut blossoms."""
rep8_bil = """Київ — це не просто сучасний адміністративний центр. Це справжнє історичне серце України. Він має статус одного з найстаріших міст Східної Європи. Його глибока історія робить його цікавим місцем. Велике місто має дуже красиву географію. Широка і велична річка Дніпро розділяє місто на правий і лівий береги. Коли ви читаєте тексти про Київ, звертайте увагу на культурні символи. Квітучий **каштан** — це улюблений символ Києва. Кожного травня місто має багато білих і рожевих квітів.
*(Kyiv is not just the modern administrative center; it is the true historical heart of Ukraine. Founded deep in the 5th century, it is recognized as one of the oldest and most historically significant cities in Eastern Europe. Its deep historical status makes it an endlessly fascinating place to explore linguistically. The sprawling city is defined by its stunning geography, particularly the wide and majestic Dnipro River that gracefully divides the city into the right and left banks. When you read assessment texts about Kyiv, pay close attention to the cultural symbols. The blooming **кашта́н** (chestnut tree) is the iconic, beloved symbol of Kyiv. Every May, the city dramatically transforms into a magnificent sea of white and pink chestnut blossoms.)*"""
content = content.replace(rep8, rep8_bil)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done part 2.")
