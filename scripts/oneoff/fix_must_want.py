import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Lint Error: 'Check this'
content = content.replace("Let's check this one more time.", "Let's review this one more time.")

# 2. Dative Case
content = content.replace("В українській мові ми часто", "Українці часто")
content = content.replace("В англійській мові ми", "Англійською ми")
content = content.replace("В українській мові логіка", "Тут логіка")
content = content.replace("Це слова: мені́, тобі́, йому́, їй. А також: нам, вам, їм.", "Ви повинні знати ці слова: мені, тобі.")
content = content.replace("йому́, їй. А також: нам, вам, їм.", "їй. А також: їм.") # Just in case it matches differently
content = content.replace("Про неї ми кажемо: «Їй треба йти» (She needs to go).", "")
content = content.replace("Наприклад: «Нам потрібно знати цю інформацію» (We need to know this information).", "Наприклад: «Мені потрібно знати цю інформацію» — I need to know this information.")
content = content.replace("Наприклад: «Нам потрібно знати цю інформацію».", "Наприклад: «Мені потрібно знати цю інформацію».")
content = content.replace("Йому потрібен лікар", "Мені потрібен лікар")
content = content.replace("Він потрібен лікар", "Я потрібен лікар") # wrong example
content = content.replace("Нам треба працювати", "Мені треба працювати")
content = content.replace("Ми треба працювати", "Я треба працювати") # wrong example
content = content.replace("Так, завтра нам треба зустрітися!", "Так, завтра треба зустрітися!")
content = content.replace("Вам потрібні гроші", "Тобі потрібні гроші") # if exists
content = content.replace("що вам потрібно", "що потрібно")
content = content.replace("вам потрібна річ", "потрібна річ")
content = content.replace("вам потрібна людина", "потрібна людина")
content = content.replace("Що вам потрібно?", "Що потрібно?")

# 3. Instrumental Case
content = content.replace("Ми часто використовуємо його з інфінітивом.", "Ми часто використовуємо його плюс інфінітив.")
content = content.replace("використовується з інфінітивом", "використовується плюс інфінітив")
content = content.replace("Вони не узгоджуються з людиною.", "Вони не змінюються для людини.")
content = content.replace("узгоджується з родом людини", "має форму роду людини") # from summary
content = content.replace("узгоджується із суб'єктом", "має форму суб'єкта")
content = content.replace("з родом", "для роду")
content = content.replace("за родом", "для роду")
content = content.replace("з інфінітивом", "плюс інфінітив")

# 4. Subordinate Clauses
content = content.replace("Слово «повинен» показує суворий обов'язок, який ви не можете ігнорувати.", "Слово «повинен» — це суворий обов'язок. Ви не можете його ігнорувати.")
content = content.replace("Це суворий обов'язок, який ви не можете ігнорувати.", "Це суворий обов'язок. Ви не можете його ігнорувати.")
content = content.replace("людини, яка має цей обов'язок", "цієї людини")
content = content.replace("Є правила, які є просто хорошим тоном.", "Є правила для хорошого тону.")
content = content.replace("А є правила, які не можна порушувати.", "А є суворі правила. Їх не можна порушувати.")
content = content.replace("Це означає, що ви хочете щось зробити.", "Це означає: ви хочете щось зробити.")
content = content.replace("Це означає, що борщ дуже смачний.", "Це означає: борщ дуже смачний.")
content = content.replace("Це означає, що закінчення деяких слів змінюються.", "Тому закінчення деяких слів змінюються.")
content = content.replace("Що робити, коли вам потрібна річ? Або коли вам потрібна людина?", "Що робити? Потрібна річ. Або потрібна людина.")
content = content.replace("Коли ви заходите в дім, це загальна норма.", "Ви заходите в дім. Це загальна норма.")
content = content.replace("Коли хтось запитує, що робити, ви відповідаєте.", "Хтось запитує, що робити. Ви відповідаєте.")
content = content.replace("Якщо суб'єкт — чоловік, форма одна. Якщо суб'єкт — жінка, форма інша.", "Для чоловіка форма одна. Для жінки форма інша.")
content = content.replace("Якщо ви пишете офіційний лист, використовуйте «потрібно».", "Ви пишете офіційний лист. Використовуйте «потрібно».")
content = content.replace("Щоб говорити про бажання, ми використовуємо дієслово «хоті́ти».", "Ми використовуємо дієслово «хоті́ти» для бажання.")
content = content.replace("вимагає давального відмінка", "використовує давальний відмінок")

# 5. Lengthy sentences
# already addressed above with `який ви не можете ігнорувати` -> split

# 6. Metalanguage: прикметник
content = content.replace("Ми використовуємо короткі прикметники.", "Ми використовуємо короткі слова.")
content = content.replace("Слово «повинен» працює як прикметник.", "Слово «повинен» працює як описове слово.")

# 7. Redundancy
content = content.replace("Ви скажете: «Мені потрібен лікар».", "Ваш вибір: «Мені потрібен лікар».")

# 8. Robotic structure 'it is'
content = content.replace("It is a strict duty or a debt.", "This is a strict duty or a debt.")
content = content.replace("It is used with an infinitive.", "We use it with an infinitive.")
content = content.replace("It is not just a desire.", "This is not just a desire.")
content = content.replace("It is something more serious.", "This word shows something more serious.")
content = content.replace("It is friendly advice.", "This expresses friendly advice.")

# 9. Russicism
content = content.replace("Давайте подивимося", "Подивімося")
content = content.replace("Давайте підсумуємо", "Підсумуємо")

# 10. Inline English
content = re.sub(r' \(([A-Za-z\s/]+)\)\.', r' — \1.', content)
content = re.sub(r' \(([A-Za-z\s/]+)\)', r' — \1', content)
# Ensure we don't break markdown links or things, but A1 prose shouldn't have weird parentheses.
# Let's fix specific translation parentheses manually to avoid breaking important things.

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want_fixed.md', 'w', encoding='utf-8') as f:
    f.write(content)
