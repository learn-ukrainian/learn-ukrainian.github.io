import re

file_path = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/a1-final-exam.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 'мові' (Dative case flag)
content = content.replace("Порядок слів в українській мові гнучкий.", "Порядок слів тут гнучкий.")
content = content.replace("Word order in the Ukrainian language is flexible.", "Word order here is flexible.")

# 2. 'нам' (Dative case flag)
content = content.replace("Знахідний відмінок показує нам прямий об'єкт.", "Знахідний відмінок показує прямий об'єкт.")

# 3. 'вам' (Dative case flag)
content = content.replace("Бажаємо вам неймовірних успіхів на цьому фінальному тесті.", "Бажаємо успіхів на цьому фінальному тесті.")

# 4. 'з прийменником' (Instrumental case flag)
content = content.replace("Цей відмінок завжди використовується з прийменником.", "Цей відмінок завжди має прийменник.")
content = content.replace("This case is always used with a preposition.", "This case always has a preposition.")

# 5. 'настав' (Perfective aspect flag)
content = content.replace("Тепер настав час спокійно перевірити", "Тепер час спокійно перевірити")

# 6. 'займенник' (Metalanguage term flag)
content = content.replace("| Займенник (Pronoun) |", "| Хто (Who)           |")

# 7. Redundancy: "Their conjugated endings feature the distinct vowels "и" or "ї"."
content = content.replace("Their conjugated endings feature the distinct vowels \"и\" or \"ї\".", "They use the vowels \"и\" or \"ї\" instead.")

# 8. Immersion fix: replace English paragraphs with Bilingual ones
rep1 = """The final assessment is structured to evaluate your practical communication skills comprehensively. We want to see exactly how you use the language in real life. The exam includes multiple distinct sections. First, you will demonstrate your understanding of fundamental grammar and core vocabulary. Then, you will complete reading comprehension tasks based on cultural texts. After that, we will check your listening skills using authentic audio recordings. Every part of the test is meticulously designed to be fair, transparent, and supportive. There are no trick questions here. The goal is to let you showcase your newly acquired abilities."""

rep1_bil = """Фінальний тест структурований, щоб комплексно оцінити ваші комунікативні навички. Ми хочемо бачити, як ви використовуєте мову в житті. Екзамен має кілька різних секцій. Спочатку ви покажете розуміння базової граматики та словника. Потім ви виконаєте завдання на читання. Після цього ми перевіримо навички аудіювання за допомогою аудіо записів. Кожна частина тесту розроблена справедливо. Тут немає питань із підступом. Мета — показати ваші нові здібності.
*(The final assessment is structured to evaluate your practical communication skills comprehensively. We want to see exactly how you use the language in real life. The exam includes multiple distinct sections. First, you will demonstrate your understanding of fundamental grammar and core vocabulary. Then, you will complete reading comprehension tasks based on cultural texts. After that, we will check your listening skills using authentic audio recordings. Every part of the test is meticulously designed to be fair, transparent, and supportive. There are no trick questions here. The goal is to let you showcase your newly acquired abilities.)*"""

content = content.replace(rep1, rep1_bil)

rep2 = """During the assessment, you will experience a carefully balanced language environment. To ensure you completely understand what to do, all task instructions are provided in English. This strategic scaffolding reduces unnecessary stress and cognitive load. However, the reading passages and listening audio tracks will be entirely in Ukrainian. This tests your true immersion and real-time comprehension. Do not worry if you do not immediately recognize every single word. Focus on grasping the main idea and use context clues to find the correct answer. You already possess the tools needed to decode meaning from unfamiliar texts."""

rep2_bil = """Під час оцінювання ви відчуєте збалансоване мовне середовище. Щоб гарантувати повне розуміння, всі інструкції надаються англійською мовою. Ця стратегічна підтримка зменшує стрес. Однак тексти для читання та аудіо треки будуть повністю українською. Це перевіряє ваше справжнє занурення. Не хвилюйтеся, якщо ви не відразу впізнаєте кожне слово. Зосередьтеся на головній ідеї. Ви вже маєте інструменти для розуміння текстів.
*(During the assessment, you will experience a carefully balanced language environment. To ensure you completely understand what to do, all task instructions are provided in English. This strategic scaffolding reduces unnecessary stress and cognitive load. However, the reading passages and listening audio tracks will be entirely in Ukrainian. This tests your true immersion and real-time comprehension. Do not worry if you do not immediately recognize every single word. Focus on grasping the main idea and use context clues to find the correct answer. You already possess the tools needed to decode meaning from unfamiliar texts.)*"""

content = content.replace(rep2, rep2_bil)

rep3 = """Your overall performance is evaluated based on your ability to communicate effectively and clearly. We absolutely do not expect absolute perfection at the A1 level. Your **оцінка** (grade) reflects how well you can convey your message and understand others in a conversational context. If you make a **помилка** (mistake) during the test, do not panic or feel discouraged. Mistakes are a natural, inevitable, and necessary part of the language learning process. They clearly show us what we need to practice more in the future. Our primary goal as Patient Supportive Tutors is to celebrate what you do **правильно** (correctly)."""

rep3_bil = """Ваш результат оцінюється на основі вашої здатності ефективно спілкуватися. Ми абсолютно не очікуємо досконалості на рівні A1. Ваша **оцінка** відображає, наскільки добре ви можете передати своє повідомлення. Якщо ви робите **помилку** під час тесту, не панікуйте. Помилки — це природна і необхідна частина процесу навчання. Вони чітко показують нам, що потрібно більше практикувати в майбутньому. Наша головна мета — святкувати те, що ви робите **правильно**.
*(Your overall performance is evaluated based on your ability to communicate effectively and clearly. We absolutely do not expect absolute perfection at the A1 level. Your **оцінка** (grade) reflects how well you can convey your message and understand others in a conversational context. If you make a **помилка** (mistake) during the test, do not panic or feel discouraged. Mistakes are a natural, inevitable, and necessary part of the language learning process. They clearly show us what we need to practice more in the future. Our primary goal as Patient Supportive Tutors is to celebrate what you do **правильно** (correctly).)*"""

content = content.replace(rep3, rep3_bil)

rep4 = """Before you begin the test, take a deep, calming breath. You have practiced these specific concepts many times throughout the previous modules. Read each question slowly and methodically. When you need to **слухати** (listen) to the audio recordings, focus on identifying familiar verbs and nouns. When you need to **писати** (write), remember the basic spelling rules and sound patterns. Trust your trained intuition and try not to second-guess your very first answers. You are fully prepared, equipped, and ready for this rewarding challenge."""

rep4_bil = """Перед початком тесту зробіть глибокий вдих. Ви багато разів практикували ці концепції. Читайте кожне запитання повільно. Коли вам потрібно **слухати** аудіо, зосередьтеся на знайомих дієсловах та іменниках. Коли вам потрібно **писати**, згадайте базові правила. Довіряйте своїй інтуїції і намагайтеся не сумніватися у своїх перших відповідях. Ви повністю готові до цього виклику.
*(Before you begin the test, take a deep, calming breath. You have practiced these specific concepts many times throughout the previous modules. Read each question slowly and methodically. When you need to **слухати** (listen) to the audio recordings, focus on identifying familiar verbs and nouns. When you need to **писати** (write), remember the basic spelling rules and sound patterns. Trust your trained intuition and try not to second-guess your very first answers. You are fully prepared, equipped, and ready for this rewarding challenge.)*"""

content = content.replace(rep4, rep4_bil)

rep5 = """In Ukrainian, nouns change their endings depending on their specific grammatical role in the sentence. This morphological system is beautiful and highly logical. The Nominative case is always the subject of the sentence. It tells us clearly who or what is performing the main action. You will always find this exact form when you look up a word in the dictionary. When you want to call someone's name or address them directly, you must use the Vocative case. This essential feature makes your speech polite, natural, and culturally authentic."""

rep5_bil = """Іменники змінюють свої закінчення залежно від граматичної ролі в реченні. Ця морфологічна система дуже красива і логічна. Називний відмінок — це завжди суб'єкт речення. Він чітко говорить, хто або що виконує дію. Ви завжди знайдете цю форму в словнику. Коли ви хочете покликати когось, ви маєте використовувати Кличний відмінок. Це робить вашу мову ввічливою.
*(In Ukrainian, nouns change their endings depending on their specific grammatical role in the sentence. This morphological system is beautiful and highly logical. The Nominative case is always the subject of the sentence. It tells us clearly who or what is performing the main action. You will always find this exact form when you look up a word in the dictionary. When you want to call someone's name or address them directly, you must use the Vocative case. This essential feature makes your speech polite, natural, and culturally authentic.)*"""

content = content.replace(rep5, rep5_bil)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done applying fixes.")
