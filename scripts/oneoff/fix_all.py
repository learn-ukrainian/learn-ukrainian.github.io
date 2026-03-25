import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

# Revert English in headers
content = content.replace("## Вступ (Introduction)", "## Вступ")
content = content.replace("## Презентація: Дієслова та відмінювання (Presentation: Verbs and Conjugation)", "## Презентація: Дієслова та відмінювання")
content = content.replace("## Соціокультурний контекст: Фемінітиви та IT (Sociocultural Context: Femininitives and IT)", "## Соціокультурний контекст: Фемінітиви та IT")
content = content.replace("## Практика та запобігання помилкам (Practice and Error Prevention)", "## Практика та запобігання помилкам")
content = content.replace("## Діалоги та кар'єрні плани (Dialogues and Career Plans)", "## Діалоги та кар'єрні плани")
content = content.replace("# Підсумок (Summary)", "# Підсумок")

# Revert inline English
content = content.replace("Найпоширеніша помилка (The most common mistake) English speakers make", "The most common mistake English speakers make")
content = content.replace("Because English uses «to be» with the basic noun form (базова форма)", "Because English uses «to be» with the basic noun form")
content = content.replace("Уявіть, що ви одягаєте уніформу. (Think of it like putting on a uniform.)", "Think of it like putting on a uniform.")
content = content.replace("Це головне правило (This is the core logic) behind the State Standard rule", "This is the core logic behind the State Standard rule")

# Fix complexity errors properly by ensuring we match exactly
content = re.sub(r"Мій найкр́ащий друг рані́ше працюва́в юри́стом, але́ він за́вжди мрі́яв бу́ти лі́карем\.", "Мій найкр́ащий друг рані́ше працюва́в юри́стом. Але́ він за́вжди мрі́яв бу́ти лі́карем.", content)
content = re.sub(r"Ми́ вважа́ємо, що́ ніко́ли не́ пі́зно ста́ти ти́м, ки́м ти́ хо́чеш бу́ти!", "Ми́ вважа́ємо так. Ніко́ли не́ пі́зно змінити профе́сію!", content)
content = re.sub(r"Я́ працювала́ журналі́сткою п'я́ть рокі́в, але́ по́тім я́ зрозумі́ла, що́ хо́чу працюва́ти в бі́знесі\.", "Я́ працювала́ журналі́сткою п'я́ть рокі́в. По́тім я́ зрозумі́ла, що́ хо́чу працюва́ти в бі́знесі.", content)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
