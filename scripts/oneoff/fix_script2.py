with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "r") as f:
    text = f.read()

text = text.replace("«**Дайте** мені чорну каву, будь ласка.»", "«**Дайте** чорну каву, будь ласка.»")
text = text.replace("«**Дай** мені твій телефон.»", "«**Дай** твій телефон.»")
text = text.replace("**Будь ласка**, дайте мені меню.", "**Будь ласка**, дайте меню.")
text = text.replace("Дайте мені, **будь ласка**, меню.", "Дайте, **будь ласка**, меню.")
text = text.replace("Дайте мені меню, **будь ласка**.", "Дайте меню, **будь ласка**.")
text = text.replace("1. Вам потрібно: ваш найкращий друг читає статтю.", "1. Ваш найкращий друг читає статтю.")
text = text.replace("Це ваші найважливіші базові практичні навички", "Це ваші найважливіші практичні навички")

with open("curriculum/l2-uk-en/a1/imperative-and-requests.md", "w") as f:
    f.write(text)
