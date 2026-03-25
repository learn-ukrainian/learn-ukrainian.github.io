import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

# Fix complexity errors
content = content.replace("Мій найкращий друг раніше працював юристом, але він завжди мріяв бути лікарем.", "Мій найкращий друг раніше працював юристом. Але він завжди мріяв бути лікарем.")
content = content.replace("Ми вважаємо, що ніколи не пізно стати тим, ким ти хочеш бути!", "Ми вважаємо, що ніколи не пізно змінити професію.")
content = content.replace("Я працювала журналісткою п'ять років, але потім я зрозуміла, що хочу працювати в бізнесі.", "Я працювала журналісткою п'ять років. Потім я зрозуміла, що хочу працювати в бізнесі.")

# Add more translation phrases to paragraphs as requested by "Add short Ukrainian phrases with (translations) in existing paragraphs"
# Paragraph: The most common mistake English speakers make is the «Nominative Trap.»
content = content.replace(
    "The most common mistake English speakers make is the «Nominative Trap.»",
    "Найпоширеніша помилка (The most common mistake) English speakers make is the «Nominative Trap.»"
)
content = content.replace(
    "Because English uses «to be» with the basic noun form",
    "Because English uses «to be» with the basic noun form (базова форма)"
)
content = content.replace(
    "Think of it like putting on a uniform.",
    "Уявіть, що ви одягаєте уніформу. (Think of it like putting on a uniform.)"
)
content = content.replace(
    "This is the core logic behind the State Standard rule",
    "Це головне правило (This is the core logic) behind the State Standard rule"
)

# Replace Headers
content = content.replace("## Вступ", "## Вступ (Introduction)")
content = content.replace("## Презентація: Дієслова та відмінювання", "## Презентація: Дієслова та відмінювання (Presentation: Verbs and Conjugation)")
content = content.replace("## Соціокультурний контекст: Фемінітиви та IT", "## Соціокультурний контекст: Фемінітиви та IT (Sociocultural Context: Femininitives and IT)")
content = content.replace("## Практика та запобігання помилкам", "## Практика та запобігання помилкам (Practice and Error Prevention)")
content = content.replace("## Діалоги та кар'єрні плани", "## Діалоги та кар'єрні плани (Dialogues and Career Plans)")
content = content.replace("# Підсумок\n", "# Підсумок (Summary)\n")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
