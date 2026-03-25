with open('curriculum/l2-uk-en/a1/prohibitions-and-signs.md', 'r') as f:
    text = f.read()

text = text.replace('Вам не потрібно змінювати форму', 'Ви не маєте змінювати форму')
text = text.replace('Коли вам треба перейти дорогу, шукайте', 'Для переходу дороги шукайте')
text = text.replace('Вам потрібна «зупи́нка».', 'Ви шукаєте «зупинку».')
text = text.replace('вам часто потрібно', 'ви часто маєте')

text = text.replace('описує все, що пов\'язано з пішоходами.', 'описує речі для пішоходів.')
text = text.replace('Уявіть, що ви бачите', 'Уявіть: ви бачите')
text = text.replace('Пам\'ятайте, що публічні знаки', 'Пам\'ятайте: публічні знаки')

with open('curriculum/l2-uk-en/a1/prohibitions-and-signs.md', 'w') as f:
    f.write(text)
