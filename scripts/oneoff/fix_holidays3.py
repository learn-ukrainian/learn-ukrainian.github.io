with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "r") as f:
    text = f.read()

text = text.replace("Бажати — це те, що ви хочете дати людині емоційно.", "Бажати — це ваші добрі емоції для іншої людини.")
text = text.replace("**Бажати** is expressing what good things you want to give the person emotionally.", "**Бажати** is your good emotions for another person.")

with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "w") as f:
    f.write(text)
