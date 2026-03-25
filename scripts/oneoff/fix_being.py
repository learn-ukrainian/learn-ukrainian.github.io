import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1 & 2
content = content.replace(
    "In this module, we will explore exactly how to build these functional descriptions and avoid the common traps that give away non-native speakers.",
    "Mastering this structure allows you to build accurate functional descriptions and avoid the common traps that give away non-native speakers."
)

# Fix 3 & 4
content = content.replace("айті́шник", "айтіве́ць")
content = content.replace("айті́шниця", "айті́вка")
content = content.replace("айті́шницею", "айті́вкою")

# Fix 5
content = content.replace(
    "- **Вона́ — ме́неджерка.** — She is a manager.\n- **Вона́ ста́ла ме́неджеркою.** — She became a manager.",
    "- **Він — ме́неджер.** — He is a manager.\n- **Він став ме́неджером.** — He became a manager."
)

# Fix 6
content = content.replace(
    "— Чудо́во. Нам потрі́бна хоро́ша спеціалі́стка.",
    "— Чудо́во. Ми шука́ємо хоро́шу спеціалі́стку."
)

# Fix 7
content = content.replace(
    "- **Він працю́є дире́ктором.** — He works as a director.\n- **Вона́ ста́ла дире́кторкою.** — She became a director.",
    "- **Він працю́є дире́ктором.** — He works as a director.\n- **Він став дире́ктором.** — He became a director."
)

# Fix 8 & 9
content = content.replace(
    "- **Ти — юри́стка. → Ти була́ юри́сткою.** — You are a lawyer. → You were a lawyer.\n- **Вона́ — вчи́телька. → Вона́ була́ вчи́телькою.** — She is a teacher. → She was a teacher.",
    "- **Ти — юри́ст. → Ти був юри́стом.** — You are a lawyer. → You were a lawyer.\n- **Він — вчи́тель. → Він був вчи́телем.** — He is a teacher. → He was a teacher."
)

# Fix 10
content = content.replace(
    "- **Він ста́не хоро́шим лі́карем.** — He will become a good doctor.",
    "- **Він ста́не лі́карем.** — He will become a doctor."
)

# Fix 11
content = content.replace("<!-- adapted from: Grade", "<!-- Source: Grade")
content = content.replace("<!-- adapted from: State Standard", "<!-- Source: State Standard")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
