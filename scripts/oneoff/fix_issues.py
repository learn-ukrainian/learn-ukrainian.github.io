import re

file_path = "curriculum/l2-uk-en/a1/likes-and-preferences.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
    
# Fix 1 & 2: ~line 7-8
content = content.replace("* **Мені подо́бається ка́ва.** — I like coffee.", "* **Я люблю́ ка́ву.** — I like coffee.")
content = content.replace("* **Мені подо́бається чита́ти.** — I like to read.", "* **Я люблю́ чита́ти.** — I like to read.")

# Fix 3, 4, 5: ~line 26-28
content = content.replace("* **Мені подо́бається ціка́вий фільм.** — I like an interesting film.", "* **Я люблю́ ціка́вий фільм.** — I like an interesting film.")
content = content.replace("* **Мені подо́баються ці кві́ти.** — I like these flowers.", "* **Я люблю́ ці кві́ти.** — I like these flowers.")
content = content.replace("* **Йому подо́баються нові́ книжки́.** — He likes new books.", "* **Він лю́бить нові́ книжки́.** — He likes new books.")

# Fix 6: ~line 51
content = content.replace("When you say **мені подо́бається**, you are describing", "When you say **\"I like\"**, you are describing")

# Fix 7, 8: ~line 53-55
content = content.replace("* **Мені подо́бається ця кни́га.** — I find this book appealing.", "* **Я люблю́ цю кни́гу.** — I find this book appealing.")
content = content.replace("* **Мені подо́бається смачни́й борщ.** — I like tasty borscht.", "* **Я люблю́ смачни́й борщ.** — I like tasty borscht.")

# Fix 9: ~line 90
content = content.replace("* **Мені подо́бається ка́ва.** — I like coffee.", "* **Я люблю́ ка́ву.** — I like coffee.") # this replaces the second instance too

# Fix 10, 11: ~line 100-101
content = content.replace("* **А вам?** — And you? (formal/plural)", "* **А ви?** — And you? (formal/plural)")
content = content.replace("* **Тобі подо́бається му́зика?** — Do you like music?", "* **Ти лю́биш му́зику?** — Do you like music?")

# Fix 12, 13, 14: ~line 107-109
content = content.replace("> — **Приві́т! Тобі подо́бається цей чай?**", "> — **Приві́т! Ти лю́биш цей чай?**")
content = content.replace("> — **Так, смачни́й чай. А тобі?**", "> — **Так, смачни́й чай. А ти?**")
content = content.replace("> — **Мені теж. Я дуже люблю́ чай.**", "> — **Я теж. Я дуже люблю́ чай.**")

# Fix 15: ~line 124
content = content.replace("* **Мені подо́бається суп.** — I find the soup appealing.", "* **Я люблю́ суп.** — I find the soup appealing.")

# Write back
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacements done.")
