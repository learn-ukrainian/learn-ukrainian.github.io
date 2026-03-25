import re

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('## Вступ (Introduction)', '## Вступ')
text = text.replace('## Презентація: Дієслова та відмінювання (Presentation: Verbs and Declension)', '## Презентація: Дієслова та відмінювання')
text = text.replace('## Соціокультурний контекст: Фемінітиви та IT (Sociocultural Context: Femininitives and IT)', '## Соціокультурний контекст: Фемінітиви та IT')
text = text.replace('## Практика та запобігання помилкам (Practice and Error Prevention)', '## Практика та запобігання помилкам')
text = text.replace('## Діалоги та кар\'єрні плани (Dialogues and Career Plans)', '## Діалоги та кар\'єрні плани')
text = text.replace('# Підсумок (Summary)', '# Підсумок')

# I will also add a huge dialogue or table to boost immersion.
immersion_block = """

> **🎬 Діалог: Ким ви хочете стати? (Dialogue: What do you want to become?)**
> 
> — Привіт! Я чув, ти змінив роботу? (Hi! I heard you changed your job?)
> — Так! Раніше я працював інженером, але зараз я хочу стати програмістом. (Yes! Previously I worked as an engineer, but now I want to become a programmer.)
> — Це чудово! А твоя сестра? Вона працює вчителькою? (That's wonderful! And your sister? Does she work as a teacher?)
> — Вона була вчителькою минулого року. Тепер вона стала директоркою школи. (She was a teacher last year. Now she became the director of the school.)
> — Ого! Це велика зміна статусу. (Wow! That is a big change of status.)
> — Так, вона дуже багато працює. А ким ти мрієш стати? (Yes, she works very hard. And what do you dream of becoming?)
> — Я хочу стати лікарем. Я багато вчуся для цього. (I want to become a doctor. I study a lot for this.)

> **💡 Додаткові приклади (Additional examples)**
> 
> * **Він працює економістом у банку.** (He works as an economist in a bank.)
> * **Вона раніше була журналісткою, а тепер працює менеджеркою.** (She previously was a journalist, and now works as a manager.)
> * **Вони хочуть стати хорошими спеціалістами.** (They want to become good specialists.)
> * **В Україні багато людей працюють айтівцями.** (In Ukraine many people work as IT professionals.)
> * **Ми були студентами, а стали експертами.** (We were students, and became experts.)
> * **Мій друг буде директором.** (My friend will be a director.)

"""

text = text.replace('## Вступ', immersion_block + '\n## Вступ')

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'w', encoding='utf-8') as f:
    f.write(text)

