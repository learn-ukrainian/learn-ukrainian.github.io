import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/a1-final-exam.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix `вам`
content = content.replace("Це допоможе вам не запізнитися на поїзд.", "Це допоможе не запізнитися на поїзд.")

# Fix `Щоб у` and robotic structure "ви маєте"
content = content.replace("Щоб успішно подорожувати Україною, ви маєте використовувати свої мовні навички.", "Успішна подорож Україною вимагає ваших мовних навичок.")
content = content.replace("Ви маєте використовувати числа для розуміння цін на ринку.", "Використовуйте числа для розуміння цін на ринку.")
content = content.replace("Ви маєте знати правильні маршрути автобусів.", "Добре знати правильні маршрути автобусів.")
content = content.replace("Також ви маєте купувати квитки на вокзалі.", "Також ви купуєте квитки на вокзалі.")
content = content.replace("Ви маєте вміти запитувати час.", "Вміння запитати час — це дуже важливо.")
content = content.replace("Ви маєте розуміти ці важливі слова для правильного читання.", "Розуміння цих слів дуже важливе для правильного читання.")

# Fix remaining "ви маєте" or "Ви маєте"
content = content.replace("ви маєте використовувати Знахідний відмінок", "використовуйте Знахідний відмінок")
content = content.replace("ви маєте розказати про себе", "ви розказуєте про себе")
content = content.replace("ви маєте замовити їжу", "ви замовляєте їжу")

# Add bilingual translations for immersion boost
rep16 = """Immersive language learning is deeply and inextricably connected to exploring local culture and geography. In this final exam, your comprehensive reading tasks will be beautifully framed around a thematic journey across Ukraine. You will conceptually travel from the bustling historical capital in the center to the vibrant cultural hub in the west. This engaging thematic narrative effortlessly integrates practical vocabulary from many different conceptual topics. You will need to actively use vocabulary related directly to public transport, traditional food, and everyday daily life. As you read these curated texts, vividly imagine yourself walking down these ancient cobblestone streets and interacting warmly with the local people. This rich context makes the language come brilliantly alive."""
rep16_bil = """Вивчення мови глибоко пов'язане з місцевою культурою та географією. У цьому фінальному тесті ваші завдання на читання — це тематична подорож Україною. Ви будете віртуально подорожувати від історичної столиці в центрі до культурного центру на заході. Ця цікава історія інтегрує практичний словник. Ви будете активно використовувати нові слова. Вони стосуються транспорту, їжі та щоденного життя. Коли ви читаєте ці тексти, уявляйте себе на цих старовинних вулицях. Ви говорите з місцевими людьми. Цей багатий контекст робить мову дуже живою.
*(Immersive language learning is deeply and inextricably connected to exploring local culture and geography. In this final exam, your comprehensive reading tasks will be beautifully framed around a thematic journey across Ukraine. You will conceptually travel from the bustling historical capital in the center to the vibrant cultural hub in the west. This engaging thematic narrative effortlessly integrates practical vocabulary from many different conceptual topics. You will need to actively use vocabulary related directly to public transport, traditional food, and everyday daily life. As you read these curated texts, vividly imagine yourself walking down these ancient cobblestone streets and interacting warmly with the local people. This rich context makes the language come brilliantly alive.)*"""
content = content.replace(rep16, rep16_bil)

rep17 = """This module marks the culmination of your A1 journey. You have reviewed the fundamental building blocks of the Ukrainian language, explored the rich cultural landscapes of Kyiv and Lviv, and practiced essential communicative scenarios. You now know how to navigate verb classes, agree adjectives with nouns, and employ correct noun cases for location and motion."""
rep17_bil = """Цей модуль — це кінець вашої подорожі А1. Ви повторили базові елементи української мови. Ви досліджували багаті культурні ландшафти Києва та Львова. Ви практикували важливі комунікативні ситуації. Тепер ви знаєте класи дієслів. Ви знаєте узгодження слів. Ви використовуєте правильні відмінки для місця та руху.
*(This module marks the culmination of your A1 journey. You have reviewed the fundamental building blocks of the Ukrainian language, explored the rich cultural landscapes of Kyiv and Lviv, and practiced essential communicative scenarios. You now know how to navigate verb classes, agree adjectives with nouns, and employ correct noun cases for location and motion.)*"""
content = content.replace(rep17, rep17_bil)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done part 5.")
