
md_path = "curriculum/l2-uk-en/a2/a2-final-exam.md"
with open(md_path, encoding="utf-8") as f:
    text = f.read()

# 1. Transliteration
text = text.replace("Знахідний відмінок (Accusative)", "Знахідний відмінок")
text = text.replace("давальний відмінок (Dative)", "давальний відмінок")
text = text.replace("відмінок (Accusative)", "відмінок")
text = text.replace("викладачу (Dative)", "викладачу")
text = text.replace("питання (Accusative)", "питання")
text = text.replace("родовий відмінок (Genitive)", "родовий відмінок")
text = text.replace("орудного відмінка (Instrumental)", "орудного відмінка")
text = text.replace("орудний відмінок (Instrumental)", "орудний відмінок")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(text)
