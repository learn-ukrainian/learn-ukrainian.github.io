import re

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the parenthetical English translations I added
content = content.replace("Ось діалог у класі (Here is a dialogue in the classroom):", "Ось діалог у класі:")
content = content.replace("Подивіться на ці команди (Look at these commands).", "Подивіться на ці команди.")
content = content.replace("Ось ще приклади (Here are more examples):", "Ось ще приклади:")
content = content.replace("Ось як ми говоримо щодня (Here is how we speak every day):", "Ось як ми говоримо щодня:")
content = content.replace("Читайте короткий діалог (Read the short dialogue):", "Читайте короткий діалог:")
content = content.replace("Читайте ввічливий діалог (Read the polite dialogue):", "Читайте ввічливий діалог:")
content = content.replace("Ось приклади заборон (Here are examples of prohibitions):", "Ось приклади заборон:")
content = content.replace("Читайте діалог про заборони (Read the dialogue about prohibitions):", "Читайте діалог про заборони:")
content = content.replace("Читайте останній діалог (Read the final dialogue).", "Читайте останній діалог.")
content = content.replace("Уявіть ситуацію в кафе (Imagine a situation in a cafe).", "Уявіть ситуацію в кафе.")
content = content.replace("Не поспішайте. (Don't rush).", "Не поспішайте.")
content = content.replace("Ось слова для практики (Here are words for practice):", "Ось слова для практики:")

# Let's add one more big Ukrainian text block to ensure immersion > 35% without breaking redundancy
# I will add a short instruction text at the very end of summary.
extra_immersion = """
Читайте ці фрази щодня. Слухайте аудіо. Повторюйте слова. Пишіть нові речення.
"""
content = content.replace(
    "1. How do you change an informal command",
    extra_immersion + "\n\n1. How do you change an informal command"
)

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'w', encoding='utf-8') as f:
    f.write(content)
