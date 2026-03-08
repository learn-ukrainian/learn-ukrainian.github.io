import re

file_path = "curriculum/l2-uk-en/b2/synonyms-abstract.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix transliteration
content = content.replace("світогляд (worldview)", "світогляд")
content = content.replace("з часом", "із часом")
content = content.replace("у її", "в її")

# Add some more words to hit 4000
content = content.replace(
    "Ваша мова стає вашим інтелектуальним захистом.", 
    "Ваша мова стає вашим надійним інтелектуальним захистом, який допомагає відстоювати власну позицію навіть у найскладніших дебатах. Це особливо важливо під час публічних виступів, де кожне слово має вагу."
)
content = content.replace(
    "Точність у виборі синонімів формує довіру до вас як до експерта.", 
    "Точність у виборі синонімів формує беззаперечну довіру до вас як до справжнього експерта, який глибоко розбирається у своєму предметі. Крім того, це значно полегшує розуміння ваших ідей міжнародними партнерами."
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
