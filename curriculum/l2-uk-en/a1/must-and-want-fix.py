import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'r') as f:
    text = f.read()

# 1. Remove Dative pronouns
text = re.sub(r'Мені́ тре́ба', 'Тре́ба', text)
text = re.sub(r'мені́ тре́ба', 'тре́ба', text)
text = re.sub(r'Тобі́ тре́ба', 'Тре́ба', text)
text = re.sub(r'тобі́ тре́ба', 'тре́ба', text)
text = re.sub(r'Йому́ тре́ба', 'Тре́ба', text)
text = re.sub(r'йому́ тре́ба', 'тре́ба', text)
text = re.sub(r'Їй тре́ба', 'Тре́ба', text)
text = re.sub(r'їй тре́ба', 'тре́ба', text)
text = re.sub(r'Нам тре́ба', 'Тре́ба', text)
text = re.sub(r'нам тре́ба', 'тре́ба', text)
text = re.sub(r'Вам тре́ба', 'Тре́ба', text)
text = re.sub(r'вам тре́ба', 'тре́ба', text)
text = re.sub(r'Їм тре́ба', 'Тре́ба', text)
text = re.sub(r'їм тре́ба', 'тре́ба', text)

text = re.sub(r'Мені́ потрі́бн', 'Потрі́бн', text)
text = re.sub(r'Йому́ потрі́бн', 'Потрі́бн', text)
text = re.sub(r'Нам потрі́бн', 'Потрі́бн', text)
text = re.sub(r'Їй потрі́бн', 'Потрі́бн', text)
text = re.sub(r'Вам потрі́бн', 'Потрі́бн', text)

# 2. Fix robotic structure "It is..."
text = text.replace('It is necessary to work.', 'Working is necessary.')
text = text.replace('It is always necessary to sleep.', 'Sleeping is always necessary.')
text = text.replace('It is necessary to wait here.', 'Waiting here is required.')
text = text.replace('It is necessary to go now.', 'Going now is essential.')
text = text.replace('It is necessary to read the text.', 'Reading the text is required.')
text = text.replace('It is needed to wait carefully here.', 'Waiting carefully here is required.')

# 3. Remove inline English
text = text.replace('Сценарій: Працюва́ти (To work)', 'Сценарій: Працюва́ти')
text = text.replace('Діалог 1: Плани на вечір (Evening plans)', 'Діалог 1: Плани на вечір')
text = text.replace('Діалог 2: Допомога на вулиці (Help on the street)', 'Діалог 2: Допомога на вулиці')

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/must-and-want.md', 'w') as f:
    f.write(text)
