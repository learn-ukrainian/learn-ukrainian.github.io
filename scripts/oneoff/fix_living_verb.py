import re

file_path = "curriculum/l2-uk-en/a1/the-living-verb-i.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1
content = content.replace("| **Я слухаю музику.** | I listen to music. |", "| **Я слухаю радіо.** | I listen to the radio. |")

# Fix 2
content = content.replace("| **Мій друг також вивчає мову.** | My friend also studies the language. |", "| **Мій друг також вивчає текст.** | My friend also studies the text. |")

# Fix 3
content = content.replace("> **Іван:** Привіт, Анно! Ні, я зараз не працюю. Я відпочиваю. Я слухаю музику і читаю журнал.", "> **Іван:** Привіт, Анно! Ні, я зараз не працюю. Я відпочиваю. Я слухаю радіо і читаю журнал.")

# Fix 4, 5, 6
content = content.replace("> **Іван:** Так, я читаю новини про Україну. Я багато читаю. А ти? Що ти робиш сьогодні? Ти граєш на гітарі?", "> **Іван:** Так, я читаю новини. Я багато читаю. А ти? Що ти робиш сьогодні? Ти багато граєш?")

# Fix 7
content = content.replace("> **Анна:** Ні, я не граю сьогодні. Я вивчаю українську мову. Я читаю текст і пишу нові слова. Я вже багато знаю і розумію.", "> **Анна:** Ні, я не граю сьогодні. Я багато вивчаю. Я читаю текст і пишу нові слова. Я вже багато знаю і розумію.")

# Fix 8
content = content.replace("> **Іван:** Ти молодець! Ти гарно пишеш і добре розумієш. Твій брат також вивчає мову?", "> **Іван:** Ти молодець! Ти гарно пишеш і добре розумієш. Твій брат також вивчає текст?")

# Fix 9
content = content.replace("> **Анна:** Так, мій брат вивчає мову. Він зараз слухає подкаст і думає про граматику. Ми працюємо дуже багато.", "> **Анна:** Так, мій брат вивчає текст. Він зараз слухає подкаст і думає про це. Ми працюємо дуже багато.")

# Fix 10
content = content.replace("> **Анна:** Вони також працюють. Вони читають, пишуть і слухають. Ми всі вивчаємо мову.", "> **Анна:** Вони також працюють. Вони читають, пишуть і слухають. Ми всі вивчаємо текст.")

# Fix 11
content = content.replace("> **Анна:** Добре, Іване. Бувай!\n> **Іван:** Бувай, Анно!", "> **Анна:** Добре, Іване.\n> **Іван:** Добре, Анно!")

# Fix 12
content = content.replace("> 🌍 **Культура (Culture): Птицю пізнати по пір'ю...**", "> 🌍 **Культура (Culture): Мова — це важливо**")

# Fix 13 (Engagement box)
tip_box = """> [!tip] Професійна порада (Pro Tip)
> Dropping the pronoun when the context is clear makes your Ukrainian sound much more natural and fluent. Don't be afraid to just say the verb!

"""
content = content.replace("Next, let's tackle \"Pronoun Overuse.\"", tip_box + "Next, let's tackle \"Pronoun Overuse.\"")

# Fix 14 (Split section)
content = content.replace("### Міні-розповідь (Mini-Story)", "## Розповіді (Stories)\n\n### Міні-розповідь (Mini-Story)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixes applied.")
