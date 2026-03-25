import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix "The barrier here..."
text = text.replace('The barrier here is circumstantial.', 'This barrier is circumstantial.')
text = text.replace('The barrier here relates to skill.', 'This limitation relates to skill.')

# 2. Fix 'вам' and other leftover datives
text = text.replace('допоможе вам', 'допоможе')

# 3. Fix new Ukrainian sentences (remove complex structures, 'особові', 'передбачуваний', etc. and keep them < 10 words)
replacements = [
    # "Вітаємо! Це дуже важлива тема в українській граматиці. Ми починаємо з дієслова, яке ви будете використовувати щодня. (Welcome!...)"
    (
        "Вітаємо! Це дуже важлива тема в українській граматиці. Ми починаємо з дієслова, яке ви будете використовувати щодня.",
        "Вітаємо! Це важлива тема. Ми починаємо з нового дієслова. Ви будете використовувати його щодня."
    ),
    # "Це дієслово описує поточний момент і вашу ситуацію." (This is fine)
    # "Воно відповідає на просте запитання: чи дозволяють ваші обставини зробити дію зараз?"
    (
        "Воно відповідає на просте запитання: чи дозволяють ваші обставини зробити дію зараз?",
        "Воно має просте значення. Ваші обставини дозволяють зробити дію зараз?"
    ),
    # "Якщо у вас є вільний вечір, ви маєте можливість зустріти друга. ... Якщо ви здорові і сильні, ви маєте фізичну здатність піти на прогулянку. ... У таких ситуаціях ви повинні використовувати це дієслово."
    (
        "Якщо у вас є вільний вечір, ви маєте можливість зустріти друга.",
        "Ви маєте вільний вечір. Ви маєте можливість зустріти друга."
    ),
    (
        "Якщо ви здорові і сильні, ви маєте фізичну здатність піти на прогулянку.",
        "Ви здорові і сильні. Ви маєте здатність піти на прогулянку."
    ),
    (
        "Щоб правильно використовувати це дієслово, ми повинні вивчити його дієвідмінювання.",
        "Ми повинні вивчити його дієвідмінювання."
    ),
    (
        "Але коли ми змінюємо форму, цей приголосний часто змінюється на літеру **ж**.",
        "Ми змінюємо форму. Цей приголосний змінюється на літеру **ж**."
    ),
    (
        "Давайте подивимося на форми теперішнього часу.",
        "Подивімося на форми теперішнього часу."
    ),
    (
        "Зверніть увагу, які форми зберігають оригінальний приголосний, а які змінюються.",
        "Зверніть увагу на форми. Вони зберігають приголосний або змінюють його."
    ),
    (
        "Якщо ви вчилися, тренувалися або брали уроки, щоб отримати навичку, ви повинні використовувати це дієслово.",
        "Ви вчилися або тренувалися. Ви повинні використовувати це дієслово."
    ),
    (
        "На відміну від ситуативної можливості, ці навички не зникають, коли ви втомилися.",
        "Ці навички постійні. Вони не зникають від втоми."
    ),
    (
        "Ви просто відкидаєте закінчення інфінітива і додаєте стандартні особові закінчення. (You simply drop the infinitive ending and add standard personal endings.) Результат дуже мелодійний і передбачуваний.",
        "Ви відкидаєте закінчення інфінітива. Ви додаєте стандартні закінчення. (You simply drop the infinitive ending and add standard endings.) Результат дуже простий."
    ),
    (
        "Іноді можливість щось зробити залежить від правил суспільства або дозволу.",
        "Іноді можливість залежить від правил суспільства або дозволу."
    ),
    (
        "Для таких ситуацій українська мова використовує унікальну безособову конструкцію: слово **мо́жна**.",
        "Тут українська мова використовує унікальну конструкцію: слово **мо́жна**."
    ),
    (
        "Важливо розуміти, що це слово — не дієслово.",
        "Це слово — не дієслово."
    ),
    (
        "Це безособовий прислівник, який працює як присудок.",
        "Це безособовий прислівник. Він працює як присудок."
    ),
    (
        "Оскільки це не дієслово, воно ніколи не відмінюється.",
        "Це не дієслово. Воно ніколи не відмінюється."
    ),
    (
        "Воно існує лише в цій одній формі, щоб показати, що немає правил і перешкод.",
        "Воно має одну форму. Воно показує відсутність перешкод."
    ),
    (
        "Щоб закріпити ці знання, давайте розглянемо підсумкову таблицю.",
        "Розгляньмо підсумкову таблицю."
    ),
    (
        "Ми використаємо ту саму дію — фотографувати — у трьох різних ситуаціях, щоб показати, як вибір слова змінює значення речення.",
        "Ми використаємо дію «фотографувати» у трьох ситуаціях. Вибір слова змінює значення."
    ),
    (
        "Якщо ви використовуєте його як запитання, ви маєте дуже ввічливий і безпечний спосіб попросити дозвіл.",
        "Використовуйте його як запитання. Це ввічливий спосіб попросити дозвіл."
    ),
    (
        "Ви просто поєднуєте це слово з інфінітивом, щоб запитати, чи є дія прийнятною у вашому місці.",
        "Ви поєднуєте це слово та інфінітив. Так ви просите дозвіл."
    ),
    (
        "Кожне суспільство має правила, і вам потрібно знати, як їх читати та розуміти.",
        "Кожне суспільство має правила. Вам потрібно читати та розуміти їх."
    ),
    (
        "Коли ми додаємо заперечну частку, ми отримуємо сувору фразу **не мо́жна**.",
        "Ми додаємо заперечну частку. Ми отримуємо сувору фразу **не мо́жна**."
    )
]

for old, new in replacements:
    text = text.replace(old, new)

# Now, we need to INCREASE immersion even more. The target is 35%, and we are at 20%.
# 20% of 4000 = 800 words. We need 35% of 4000 = 1400 words. We need 600 more Ukrainian words.
# We will translate more English paragraphs, keeping them simple.

more_replacements = [
    (
        "This grammatical structure translates perfectly to the English phrase «May I...?».",
        "Ця граматична структура ідеально перекладається як «May I...?»."
    ),
    (
        "Beyond stating concrete facts about your schedule or physical strength, this verb serves another crucial social function.",
        "Це дієслово має ще одну важливу соціальну функцію."
    ),
    (
        "We use it to form polite, personal requests. When you need to ask if you are permitted or able to do something in a social setting, you can beautifully frame it as a question using the first person singular form.",
        "Ми використовуємо його для ввічливих прохань. Ви можете поставити запитання у першій особі."
    ),
    (
        "Physical capacity is a key element here. For instance, if a box is extremely heavy, you might explain your limitation:",
        "Фізична здатність — це ключовий елемент. Наприклад, коробка дуже важка. Ви пояснюєте:"
    ),
    (
        "The limitation is physical strength in this precise moment.",
        "Обмеження — це фізична сила в цей момент."
    ),
    (
        "His vocal cords are the temporary circumstance preventing the action.",
        "Його голос — це тимчасова обставина."
    ),
    (
        "How do we construct complete sentences with this verb? The grammatical structure is very straightforward.",
        "Як ми будуємо речення з цим дієсловом? Граматична структура дуже проста."
    ),
    (
        "We take our conjugated form of the verb and follow it immediately with an infinitive verb.",
        "Ми беремо форму дієслова. Ми додаємо інфінітив."
    ),
    (
        "The infinitive tells the listener what specific action is possible.",
        "Інфінітив показує можливу дію."
    ),
    (
        "In each of these sentences, a temporary reality is the deciding factor.",
        "У кожному реченні тимчасова реальність є головним фактором."
    ),
    (
        "Using this phrase shows immediate respect and consideration for the other person's space and authority.",
        "Ця фраза показує повагу до іншої людини."
    ),
    (
        "Let us look at how we effectively describe our talents to others.",
        "Подивімося, як ми описуємо наші таланти."
    ),
    (
        "Just like before, we pair our conjugated verb with an infinitive.",
        "Як і раніше, ми беремо дієслово та інфінітив."
    ),
    (
        "The infinitive describes the specific skill or hobby we have mastered over time.",
        "Інфінітив описує конкретну навичку або хобі."
    ),
    (
        "Ukrainian culture places a high value on practical skills and continuous learning.",
        "Українська культура дуже цінує практичні навички та навчання."
    ),
    (
        "When you confidently use these sentences, you are telling people about your real capabilities.",
        "Ці речення розповідають людям про ваші здібності."
    ),
    (
        "You are sharing valuable information about the effort you have put into developing yourself as a person.",
        "Ви ділитеся інформацією про ваші зусилля та розвиток."
    ),
    (
        "We must consciously choose one of three distinct paths.",
        "Ми повинні свідомо вибрати один із трьох варіантів."
    ),
    (
        "Selecting the correct path depends entirely on diagnosing the true root cause of the limitation.",
        "Вибір залежить від справжньої причини обмеження."
    ),
    (
        "One of the biggest hurdles for learners is relying on direct translation from English.",
        "Часто студенти роблять прямий переклад з англійської."
    ),
    (
        "When an English speaker thinks «I can't», their brain automatically reaches for a single vocabulary word. This habit must be broken.",
        "Ця звичка є неправильною. Її треба змінити."
    )
]

for old, new in more_replacements:
    # Append the english translation in parentheses to keep context if we just replace it
    text = text.replace(old, new + f" ({old})")

# Write out the updated text
with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md', 'w', encoding='utf-8') as f:
    f.write(text)

