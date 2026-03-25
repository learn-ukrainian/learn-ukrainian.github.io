import re

with open("curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml", "r") as f:
    text = f.read()

text = text.replace("options: [Добрий, Добре, Добра]", "options: [Добрий, Добре, Добра, Добру]")
text = text.replace("options: [справи, справа, справ]", "options: [справи, справа, справ, справу]")
text = text.replace("options: [побачення, побачень, побачити]", "options: [побачення, побачень, побачити, бачити]")
text = text.replace("options: [Дякую, Дякуємо, Дякувати]", "options: [Дякую, Дякуємо, Дякувати, Дякує]")
text = text.replace("options: [ласка, ласки, ласко]", "options: [ласка, ласки, ласко, ласку]")
text = text.replace("options: [ранок, ранку, ранком]", "options: [ранок, ранку, ранком, ранці]")

with open("curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml", "w") as f:
    f.write(text)
