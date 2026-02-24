import re

md_path = "curriculum/l2-uk-en/a2/a2-final-exam.md"
with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace headers
text = text.replace("## Вступ: Огляд іспиту (Overview / Огляд)", "## Вступ: Огляд іспиту")
text = text.replace("## Навичка 1: Майстерність відмінків (Case System Mastery)", "## Навичка 1: Майстерність відмінків")
text = text.replace("## Навичка 2: Вид дієслова — Процес чи результат? (Verb Aspect)", "## Навичка 2: Вид дієслова — Процес чи результат?")
text = text.replace("## Навичка 3: Навігація до екзаменаційного центру (Navigation)", "## Навичка 3: Навігація до екзаменаційного центру")
text = text.replace("## Інтеграційне завдання: Культура іспитів (Integration Challenge)", "## Інтеграційне завдання: Культура іспитів")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(text)
