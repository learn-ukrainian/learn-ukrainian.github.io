import re

with open('curriculum/l2-uk-en/a1/weather-and-nature.md', 'r') as f:
    text = f.read()

# Fix 1
text = text.replace('На ву́лиці си́льний ві́тер.', 'Сього́дні си́льний ві́тер.')
text = text.replace('(There is a strong wind outside.)', '(There is a strong wind today.)')

# Fix 2
text = text.replace('forecast, or **прогно́з пого́ди**.', 'forecast, or **прогно́з**.')

# Fix 3
text = text.replace('На не́бі вели́ка хма́ра і си́льний ві́тер.', 'Вели́ка хма́ра і си́льний ві́тер.')
text = text.replace('There is a big cloud in the sky and a strong wind.', 'A big cloud and a strong wind.')

# Fix 4
text = text.replace('Ки́їв', 'Киї́в')

# Fix 5
text = text.replace('Те́пло', 'Тепло́')
text = text.replace('те́пло', 'тепло́')

# Fix 6
text = text.replace('Спеко́тно', 'Спекотно')
text = text.replace('спеко́тно', 'спекотно')

# Fix 7
text = text.replace('Во́сени', 'Восени́')
text = text.replace('во́сени', 'восени́')

# Fix 8
text = text.replace('Сві́тить', 'Світи́ть')
text = text.replace('сві́тить', 'світи́ть')

# Fix 9
text = text.replace('рі́чки', 'річки́')

# Fix 10
text = text.replace('Яка́', 'Яка')

# Fix 11
callout = "> [!tip]\n> Always remember to drop the dummy subject \"it\" when talking about weather in Ukrainian!\n"
if "> [!tip]" not in text:
    text = text.replace('# Підсумок', callout + '\n# Підсумок')

with open('curriculum/l2-uk-en/a1/weather-and-nature.md', 'w') as f:
    f.write(text)
