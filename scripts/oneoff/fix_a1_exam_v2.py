import re

with open('curriculum/l2-uk-en/a1/a1-final-exam.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix intro 1
old_intro1 = """Ласкаво просимо до фінального етапу вашої подорожі рівнем А1! Ви неймовірно багато працювали, приділяючи години уваги, щоб досягти цього важливого моменту. Щоб зменшити хвилювання та створити комфортне середовище, граматичні пояснення залишаться англійською. Але всі тексти для читання, практичні приклади та діалоги будуть повністю українською. Цей підхід гарантує, що ви розумієте завдання, водночас перевіряючи ваші навички читання та розуміння."""
new_intro1 = "Вітаємо на фінальному іспиті рівня А1! Ви дуже багато працювали. Ви готові. Граматичні пояснення будуть англійською мовою. Тексти, приклади та діалоги будуть українською мовою. Ви добре знаєте цю граматику. Ви добре читаєте і розумієте тексти."
text = text.replace(old_intro1, new_intro1)

# 2. Fix intro 2
old_intro2 = """Ви готові! Чудова робота! Згадайте свій найперший модуль. Ви починали з вивчення кирилиці, нових звуків та простих слів. Сьогодні ви успішно використовуєте відмінки, відмінюєте дієслова та будуєте змістовні речення. Ви можете ввічливо вітатися, замовляти їжу в ресторані, користуватися транспортом і розповідати про свій день. Цей фінальний іспит просто підтверджує те, що ви вже знаєте і практикуєте щодня. Зробіть глибокий вдих і визнайте свій успіх. Ви побудували міцний і постійний фундамент в українській мові."""
new_intro2 = "Ви готові! Чудова робота! Згадайте перший модуль. Ви вчили букви і звуки. Сьогодні ви знаєте відмінки. Ви добре відмінюєте дієслова. Ви вітаєте людей на вулиці. Ви замовляєте їжу в кафе. Ви говорите про свій день. Цей іспит дуже простий. Він перевіряє ваші знання. Ви маєте чудовий фундамент."
text = text.replace(old_intro2, new_intro2)

# 3. Fix psych
old_psych = """Вивчення мови — це марафон, а не спринт. На рівні А1 головна мета — це не абсолютна граматична досконалість, а ефективна та впевнена комунікація. Якщо ви випадково використовуєте неправильне закінчення, але бариста повністю розуміє ваше замовлення, це велика перемога. Цей іспит створений, щоб показати, що ви вже вмієте робити, а не карати за помилки. Ваша **оцінка** — це об'єктивне вимірювання ваших практичних навичок. Ви можете зрозуміти розклад поїздів? Чи легко вам запитати дорогу на вулиці? Ви готові описати свій ранок? Якщо ви робите це **правильно** більшість часу, ви успішно досягли цілей рівня А1."""
new_psych = "Вивчення мови — це довгий шлях. На рівні А1 головна мета — комунікація. Ви маєте розуміти людей. Люди мають розуміти вас. Іноді ми робимо помилки. Це нормально. Ваша оцінка показує ваші навички. Ви розумієте розклад поїздів? Ви можете запитати дорогу? Ви можете описати ранок? Ви робите це дуже добре. Ви досягли цілей рівня А1."
text = text.replace(old_psych, new_psych)

# 4. Fix outro
old_outro = """Ви прочитали та зрозуміли автентичні тексти про Київ та Львів. Ви можете впевнено та правильно відмінювати базові дієслова обох класів. Ви можете швидко формулювати та правильно відповідати на практичні щоденні запитання. Ви більше не є абсолютним новачком. Ви — впевнений мовець, який розуміє українську мову.

Пишайтеся своїм великим словниковим запасом. Коли ви слухаєте носіїв мови, ви завжди розпізнаєте знайомі слова, граматичні структури та розумієте загальний зміст. Продовжуйте слухати українську музику, читати прості культурні тексти та практикувати свої навички спілкування за кожної нагоди. Ми дуже пишаємося вашою відданістю та неймовірним успіхом."""

new_outro = """Ви читали тексти про Київ та Львів. Ви вмієте правильно відмінювати дієслова. Ви швидко відповідаєте на запитання. Ви більше не новачок. Ви добре розумієте українську мову.

Ви знаєте багато слів. Ви розумієте носіїв мови. Ви розпізнаєте знайомі слова і граматику. Слухайте українську музику. Читайте прості тексти. Говоріть українською часто. Ми пишаємося вашим успіхом."""
text = text.replace(old_outro, new_outro)

# 5. Fix summary
old_summary = """Цей фінальний модуль повторення об'єднує граматику та словник рівня А1. Ви повторили відмінки: називний, кличний, знахідний, місцевий. Ви закріпили розуміння дієслів першого та другого класу. Ви також практикували синтаксис і формування запитань. Через культурні тексти про Київ та Львів ви використовували ці правила в реальних контекстах: транспорт, їжа та щоденна рутина. Тепер ви повністю готові до фінального тесту і переходу на рівень А2. Ваша праця дає чудові результати. Успіхів на іспиті!"""

new_summary = """Цей модуль повторює граматику та словник А1. Ми повторили називний, кличний, знахідний та місцевий відмінки. Ми повторили дієслова першого та другого класу. Ми практикували прості запитання. Ми читали тексти про місто Київ та місто Львів. Ми говорили про транспорт, їжу та ранок. Тепер ви готові до тесту. Ви готові до рівня А2. Ваша праця дає чудові результати. Успіхів на іспиті!"""
text = text.replace(old_summary, new_summary)


# 6. More translations to hit 35% immersion
# Let's replace some English grammar explanations with very simple Ukrainian ones.
text = text.replace(
    "The Nominative case is the absolute foundation of the language; it is the dictionary form of any given noun. It directly answers the core questions **хто?** (who?) or **що?** (what?). We use the Nominative case to designate the grammatical subject of a sentence. The subject is the active person, concept, or thing performing the action of the verb. Every single noun you learn initially starts in this fundamental case.",
    "Називний відмінок — це основа. Це словникова форма іменника. Він відповідає на питання **хто?** або **що?**. Ми використовуємо називний відмінок для підмета. Підмет робить дію в реченні. Кожне нове слово має цю форму."
)

text = text.replace(
    "When you need to address someone directly, Ukrainian utilizes a highly specific and culturally vital form called the Vocative case. This case has no associated questions because it does not describe an action or an object; it is purely functional. It is used to call out to people, address them by their name, or use their professional title. Actively using the Vocative case demonstrates a high level of cultural competence, respect, and politeness.",
    "Ми використовуємо кличний відмінок для звертання. Цей відмінок не має питань. Він не описує дію чи об'єкт. Він має іншу функцію. Ми використовуємо його, щоб кликати людей. Ми поважаємо людей. Кличний відмінок показує вашу повагу."
)

text = text.replace(
    "The Accusative case is absolutely crucial for everyday basic communication and survival. It explicitly marks the direct object of a sentence — the specific thing or person directly receiving the action of a transitive verb. It specifically answers the direct questions **кого?** (whom?) or **що?** (what?). Whenever you read a book, buy a ticket, or drink a coffee, that object must take the Accusative case.",
    "Знахідний відмінок дуже важливий для комунікації. Він позначає прямий об'єкт у реченні. Об'єкт приймає дію. Знахідний відмінок відповідає на питання **кого?** або **що?**. Ви читаєте книгу, купуєте квиток або п'єте каву. Це все знахідний відмінок."
)

text = text.replace(
    "To accurately describe exactly where something or someone is located, we consistently employ the Locative case. It directly answers the spatial question **де?** (where?). A defining feature of this case is that it is strictly and always used with a preposition, most commonly **в/у** (in, inside) or **на** (on, at a surface/event).",
    "Місцевий відмінок описує локацію. Він відповідає на питання **де?**. Ми завжди використовуємо цей відмінок з прийменниками. Найчастіше це прийменники **в / у** та **на**."
)

text = text.replace(
    "Ukrainian naturally employs a highly flexible Subject-Verb-Object (SVO) word order. While native speakers frequently move words around to create specific emotional or logical emphasis, adhering to the SVO structure remains your safest, most reliable baseline. We easily form general questions (yes/no questions) by simply raising our vocal intonation at the very end of the sentence, occasionally adding the interrogative particle **чи** at the beginning for formal clarity.",
    "Українська мова має гнучкий порядок слів. Але структура Підмет-Присудок-Додаток є найкращою для вас. Ми легко формуємо загальні питання. Ми просто змінюємо інтонацію в кінці речення. Ми також можемо додати частку **чи** на початку."
)

with open('curriculum/l2-uk-en/a1/a1-final-exam.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Second pass done.")
