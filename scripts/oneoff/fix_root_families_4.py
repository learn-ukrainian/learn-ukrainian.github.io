import re

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix transliteration issue (imperfective)
text = text.replace(" (imperfective)", "")
text = text.replace(" (perfective)", "")

# Fix Complexity Sentence
text = text.replace(
    "Тепер, коли ви розумієте механіку «великої четвірки» коренів, ви можете застосувати цю систему до будь-якого нового кореня, який ви зустрінете.",
    "Тепер ви розумієте механіку великої четвірки коренів. Ви можете використати цю систему для нових слів."
)

with open('curriculum/l2-uk-en/a2/root-families-i.md', 'w', encoding='utf-8') as f:
    f.write(text)
